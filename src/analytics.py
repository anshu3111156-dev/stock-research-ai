"""
src/analytics.py
─────────────────────────────────────────────────────────────────────────
Descriptive market analytics for StockAI.

IMPORTANT — scope and intent:
This module computes standard, well-known descriptive statistics
(technical indicators, peer ratios, historical trend data, correlation
and volatility measures). It does NOT predict future prices, generate
buy/sell signals framed as recommendations, or claim any forecasting
edge. Technical indicators here are presented as "what the data shows
about the past", consistent with the fact that there is no reliable
academic or practical evidence that such indicators predict future
returns out-of-sample. Any "signal" language in this module describes
a textbook definition being met (e.g. "RSI > 70 = textbook overbought
zone"), not a prediction of what the price will do next.

All functions are defensive: yfinance data is frequently incomplete,
delayed, or missing fields (especially for smaller NSE/BSE tickers),
so every function degrades gracefully and returns partial results
with N/A placeholders rather than raising.
"""

from __future__ import annotations

import math
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf


# ═══════════════════════════════════════════════════════════════════════
# TECHNICAL INDICATORS
# ═══════════════════════════════════════════════════════════════════════

def compute_rsi(closes: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index (Wilder's smoothing).

    Edge cases handled explicitly:
    - avg_loss == 0 (no down days in the window) -> RSI = 100, not NaN.
    - avg_gain == 0 (no up days in the window)    -> RSI = 0.
    - both zero (flat price)                       -> RSI = 50 (neutral).
    """
    delta = closes.diff()
    gain  = delta.clip(lower=0)
    loss  = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    # Round away floating point noise (e.g. -0.0) before comparing to zero
    avg_gain_r = avg_gain.round(10)
    avg_loss_r = avg_loss.round(10)

    rs  = avg_gain / avg_loss_r.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))

    rsi = rsi.where(avg_loss_r != 0, 100.0)               # no losses -> RSI 100
    rsi = rsi.where(~((avg_loss_r == 0) & (avg_gain_r == 0)), 50.0)  # flat -> RSI 50
    rsi = rsi.where(avg_gain_r != 0, 0.0)                  # no gains -> RSI 0
    rsi = rsi.where(~((avg_loss_r == 0) & (avg_gain_r == 0)), 50.0)  # re-apply flat case last

    return rsi.fillna(50)


def compute_macd(closes: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """MACD line, signal line, and histogram."""
    ema_fast   = closes.ewm(span=fast, adjust=False).mean()
    ema_slow   = closes.ewm(span=slow, adjust=False).mean()
    macd_line  = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram  = macd_line - signal_line
    return {
        "macd":      macd_line,
        "signal":    signal_line,
        "histogram": histogram,
    }


def compute_bollinger(closes: pd.Series, period: int = 20, num_std: float = 2.0) -> dict:
    """Bollinger Bands: middle (SMA), upper, lower."""
    mid   = closes.rolling(window=period, min_periods=period).mean()
    std   = closes.rolling(window=period, min_periods=period).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    return {"mid": mid, "upper": upper, "lower": lower}


def technical_snapshot(price_hist: pd.DataFrame) -> dict:
    """
    Returns a dict of current technical indicator readings plus their
    textbook interpretation labels (descriptive, not predictive).
    Returns {} if there isn't enough price history.
    """
    if price_hist is None or price_hist.empty or "Close" not in price_hist.columns:
        return {}

    closes = price_hist["Close"].dropna()
    if len(closes) < 30:
        return {}

    out: dict = {}

    # RSI
    try:
        rsi_series   = compute_rsi(closes)
        rsi_val      = float(rsi_series.iloc[-1])
        if rsi_val >= 70:
            rsi_label, rsi_tone = "Overbought zone (textbook)", "warn"
        elif rsi_val <= 30:
            rsi_label, rsi_tone = "Oversold zone (textbook)", "warn"
        else:
            rsi_label, rsi_tone = "Neutral range", "neutral"
        out["rsi"] = {"value": round(rsi_val, 1), "label": rsi_label, "tone": rsi_tone, "series": rsi_series}
    except Exception:
        pass

    # MACD
    try:
        macd        = compute_macd(closes)
        macd_val    = float(macd["macd"].iloc[-1])
        signal_val  = float(macd["signal"].iloc[-1])
        hist_val    = float(macd["histogram"].iloc[-1])
        crossover   = "Bullish crossover (MACD > signal)" if macd_val > signal_val else "Bearish crossover (MACD < signal)"
        out["macd"] = {
            "macd": round(macd_val, 2), "signal": round(signal_val, 2),
            "histogram": round(hist_val, 2), "label": crossover,
            "tone": "good" if macd_val > signal_val else "warn",
            "series": macd,
        }
    except Exception:
        pass

    # Bollinger Bands
    try:
        bb       = compute_bollinger(closes)
        last_close = float(closes.iloc[-1])
        upper      = float(bb["upper"].iloc[-1])
        lower      = float(bb["lower"].iloc[-1])
        mid        = float(bb["mid"].iloc[-1])
        if last_close >= upper:
            bb_label, bb_tone = "Trading at/above upper band", "warn"
        elif last_close <= lower:
            bb_label, bb_tone = "Trading at/below lower band", "warn"
        else:
            band_width = upper - lower
            pos_pct = ((last_close - lower) / band_width * 100) if band_width else 50
            bb_label, bb_tone = f"{pos_pct:.0f}% of band range", "neutral"
        out["bollinger"] = {
            "upper": round(upper, 2), "mid": round(mid, 2), "lower": round(lower, 2),
            "label": bb_label, "tone": bb_tone, "series": bb,
        }
    except Exception:
        pass

    return out


# ═══════════════════════════════════════════════════════════════════════
# PEER / SECTOR COMPARISON
# ═══════════════════════════════════════════════════════════════════════

# Curated peer sets per ticker — keeps peer comparison fast and relevant
# instead of guessing a whole sector universe via API calls.
PEER_MAP: dict[str, list[str]] = {
    # NSE — IT
    "TCS.NS": ["INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS"],
    "INFY.NS": ["TCS.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS"],
    "WIPRO.NS": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "TECHM.NS"],
    "HCLTECH.NS": ["TCS.NS", "INFY.NS", "WIPRO.NS", "TECHM.NS"],
    "TECHM.NS": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS"],
    # NSE — Banking
    "HDFCBANK.NS": ["ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS"],
    "ICICIBANK.NS": ["HDFCBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS"],
    "SBIN.NS": ["HDFCBANK.NS", "ICICIBANK.NS", "KOTAKBANK.NS", "AXISBANK.NS"],
    "KOTAKBANK.NS": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS"],
    "AXISBANK.NS": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS"],
    "INDUSINDBK.NS": ["HDFCBANK.NS", "ICICIBANK.NS", "AXISBANK.NS"],
    # NSE — Auto
    "TATAMOTORS.NS": ["MARUTI.NS", "M&M.NS", "EICHERMOT.NS", "BAJAJ-AUTO.NS"],
    "MARUTI.NS": ["TATAMOTORS.NS", "M&M.NS", "HEROMOTOCO.NS"],
    "M&M.NS": ["TATAMOTORS.NS", "MARUTI.NS", "EICHERMOT.NS"],
    "EICHERMOT.NS": ["HEROMOTOCO.NS", "BAJAJ-AUTO.NS", "TVSMOTOR.NS"],
    "HEROMOTOCO.NS": ["BAJAJ-AUTO.NS", "EICHERMOT.NS"],
    "BAJAJ-AUTO.NS": ["HEROMOTOCO.NS", "EICHERMOT.NS"],
    # NSE — Pharma
    "SUNPHARMA.NS": ["DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS"],
    "DRREDDY.NS": ["SUNPHARMA.NS", "CIPLA.NS", "DIVISLAB.NS"],
    "CIPLA.NS": ["SUNPHARMA.NS", "DRREDDY.NS", "DIVISLAB.NS"],
    "DIVISLAB.NS": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS"],
    # NSE — Metals
    "TATASTEEL.NS": ["JSWSTEEL.NS", "HINDALCO.NS", "SAIL.BO"],
    "JSWSTEEL.NS": ["TATASTEEL.NS", "HINDALCO.NS", "SAIL.BO"],
    "HINDALCO.NS": ["TATASTEEL.NS", "JSWSTEEL.NS"],
    # NSE — Telecom / Energy / FMCG / Conglomerates
    "BHARTIARTL.NS": ["IDEA.BO"],
    "RELIANCE.NS": ["ONGC.NS", "NTPC.NS"],
    "ITC.NS": ["NESTLEIND.NS", "TATACONSUM.NS"],
    "NESTLEIND.NS": ["ITC.NS", "TATACONSUM.NS"],
    "TATACONSUM.NS": ["ITC.NS", "NESTLEIND.NS"],
    "ASIANPAINT.NS": ["PIDILITIND.NS", "HAVELLS.NS"],
    # US — Big Tech
    "AAPL": ["MSFT", "GOOGL", "META", "AMZN"],
    "MSFT": ["AAPL", "GOOGL", "META", "AMZN"],
    "GOOGL": ["AAPL", "MSFT", "META", "AMZN"],
    "META": ["GOOGL", "AAPL", "MSFT"],
    "AMZN": ["AAPL", "MSFT", "GOOGL"],
    "NVDA": ["AMD", "INTC"],
    "AMD": ["NVDA", "INTC"],
    "INTC": ["NVDA", "AMD"],
    # US — Finance/payments
    "JPM": ["GS", "BLK"],
    "GS": ["JPM", "BLK"],
    "V": ["MA", "PYPL"],
    "MA": ["V", "PYPL"],
    "PYPL": ["V", "MA"],
    # US — Consumer/retail
    "WMT": ["PG", "KO"],
    "KO": ["PG", "WMT"],
    "NKE": ["MCD", "DIS"],
    # US — Streaming/platforms
    "NFLX": ["DIS", "SPOT"],
    "UBER": ["ABNB"],
    "ABNB": ["UBER"],
    "CRM": ["ADBE", "SNOW"],
    "ADBE": ["CRM", "SNOW"],
    "SNOW": ["CRM", "ADBE"],
    "PLTR": ["SNOW"],
}


def get_peers(ticker: str, max_peers: int = 4) -> list[str]:
    return PEER_MAP.get(ticker.upper(), [])[:max_peers]


def fetch_peer_metrics(ticker: str, max_peers: int = 4) -> dict:
    """
    Pulls valuation/quality metrics for a stock and its curated peer set.
    Returns {'rows': [...], 'metric_keys': [...]} or {} on failure.
    Each row: {ticker, name, pe, pb, roe, margin, mcap, is_subject}
    """
    peers = get_peers(ticker, max_peers)
    if not peers:
        return {}

    symbols = [ticker] + peers
    rows = []
    for sym in symbols:
        try:
            info = yf.Ticker(sym).info or {}
            pe   = info.get("trailingPE")
            pb   = info.get("priceToBook")
            roe  = info.get("returnOnEquity")
            margin = info.get("profitMargins")
            mcap = info.get("marketCap")
            name = info.get("shortName") or sym

            rows.append({
                "ticker": sym,
                "name": name,
                "pe": round(pe, 1) if isinstance(pe, (int, float)) else None,
                "pb": round(pb, 1) if isinstance(pb, (int, float)) else None,
                "roe": round(roe * 100, 1) if isinstance(roe, (int, float)) else None,
                "margin": round(margin * 100, 1) if isinstance(margin, (int, float)) else None,
                "mcap": mcap,
                "is_subject": sym.upper() == ticker.upper(),
            })
        except Exception:
            continue

    if not rows:
        return {}

    return {"rows": rows, "peer_count": len(rows) - 1}


# ═══════════════════════════════════════════════════════════════════════
# HISTORICAL FINANCIALS (multi-year trend)
# ═══════════════════════════════════════════════════════════════════════

def fetch_historical_financials(ticker: str) -> dict:
    """
    Pulls up to 4 years of annual revenue, net income, and EPS from
    yfinance's income statement. Returns {} if unavailable (common for
    smaller/foreign tickers where yfinance financials are sparse).
    """
    try:
        tk = yf.Ticker(ticker)
        fin = tk.financials  # annual income statement, columns = periods (most recent first)
        if fin is None or fin.empty:
            return {}

        years = [str(c.year) if hasattr(c, "year") else str(c) for c in fin.columns]

        def _row(label_options):
            for lbl in label_options:
                if lbl in fin.index:
                    return fin.loc[lbl]
            return None

        revenue    = _row(["Total Revenue", "TotalRevenue"])
        net_income = _row(["Net Income", "NetIncome", "Net Income Common Stockholders"])

        if revenue is None and net_income is None:
            return {}

        # Order oldest → newest for left-to-right chart reading, cap at 4 years
        years_rev = list(zip(years, revenue.tolist())) if revenue is not None else []
        years_ni  = list(zip(years, net_income.tolist())) if net_income is not None else []

        years_rev = years_rev[:4][::-1]
        years_ni  = years_ni[:4][::-1]

        result = {
            "years":      [y for y, _ in years_rev] if years_rev else [y for y, _ in years_ni],
            "revenue":    [v for _, v in years_rev] if years_rev else None,
            "net_income": [v for _, v in years_ni] if years_ni else None,
        }

        # Margin trend, if both available and same length
        if result["revenue"] and result["net_income"] and len(result["revenue"]) == len(result["net_income"]):
            result["net_margin"] = [
                round((ni / rev) * 100, 1) if rev else None
                for rev, ni in zip(result["revenue"], result["net_income"])
            ]

        return result
    except Exception:
        return {}


# ═══════════════════════════════════════════════════════════════════════
# CORRELATION & VOLATILITY VS INDEX
# ═══════════════════════════════════════════════════════════════════════

def _benchmark_for_ticker(ticker: str) -> tuple[str, str]:
    """Pick a sensible index benchmark based on ticker suffix."""
    t = ticker.upper()
    if t.endswith(".NS") or t.endswith(".BO"):
        return "^NSEI", "Nifty 50"
    return "^GSPC", "S&P 500"


def correlation_volatility(ticker: str, price_hist: Optional[pd.DataFrame] = None) -> dict:
    """
    Computes correlation of daily returns with a relevant benchmark index,
    plus annualised volatility for both, over the trailing ~1 year.
    Returns {} if data is insufficient.
    """
    try:
        bench_symbol, bench_name = _benchmark_for_ticker(ticker)

        if price_hist is None or price_hist.empty:
            price_hist = yf.Ticker(ticker).history(period="1y")
        if price_hist is None or price_hist.empty or "Close" not in price_hist.columns:
            return {}

        bench_hist = yf.Ticker(bench_symbol).history(period="1y")
        if bench_hist is None or bench_hist.empty:
            return {}

        stock_close = price_hist["Close"].dropna()
        bench_close = bench_hist["Close"].dropna()

        stock_ret = stock_close.pct_change().dropna()
        bench_ret = bench_close.pct_change().dropna()

        # Align by date index
        df = pd.DataFrame({"stock": stock_ret, "bench": bench_ret}).dropna()
        if len(df) < 30:
            return {}

        corr = df["stock"].corr(df["bench"])

        stock_vol_annual = df["stock"].std() * math.sqrt(252) * 100
        bench_vol_annual = df["bench"].std() * math.sqrt(252) * 100

        # Simple beta estimate (covariance / variance) — descriptive only
        cov = df["stock"].cov(df["bench"])
        var = df["bench"].var()
        beta_est = cov / var if var else None

        if corr >= 0.7:
            corr_label = "Strongly moves with the market"
        elif corr >= 0.4:
            corr_label = "Moderately moves with the market"
        elif corr >= 0.1:
            corr_label = "Weakly linked to the market"
        else:
            corr_label = "Largely independent of market moves"

        return {
            "benchmark_name":   bench_name,
            "correlation":      round(float(corr), 2),
            "correlation_label": corr_label,
            "stock_volatility": round(float(stock_vol_annual), 1),
            "bench_volatility": round(float(bench_vol_annual), 1),
            "beta_estimate":    round(float(beta_est), 2) if beta_est is not None else None,
            "stock_series":     stock_close,
            "bench_series":     bench_close,
        }
    except Exception:
        return {}