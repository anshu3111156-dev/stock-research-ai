"""
Live ticker strip data fetcher.
Called by app.py with st_autorefresh to get fresh prices every 60 seconds.
Returns a list of dicts with name, price, change_pct, direction.
"""
import yfinance as yf

# All tickers shown in the strip — name displayed, ticker fetched
STRIP_STOCKS = [
    ("RELIANCE",    "RELIANCE.NS"),
    ("TCS",         "TCS.NS"),
    ("HDFCBANK",    "HDFCBANK.NS"),
    ("INFY",        "INFY.NS"),
    ("ICICIBANK",   "ICICIBANK.NS"),
    ("BHARTIARTL",  "BHARTIARTL.NS"),
    ("TATAMOTORS",  "TATAMOTORS.NS"),
    ("ZOMATO",      "ZOMATO.NS"),
    ("WIPRO",       "WIPRO.NS"),
    ("BAJFINANCE",  "BAJFINANCE.NS"),
    ("ADANIENT",    "ADANIENT.NS"),
    ("ITC",         "ITC.NS"),
    ("SBIN",        "SBIN.NS"),
    ("AXISBANK",    "AXISBANK.NS"),
    ("TITAN",       "TITAN.NS"),
    ("AAPL",        "AAPL"),
    ("MSFT",        "MSFT"),
    ("NVDA",        "NVDA"),
    ("TSLA",        "TSLA"),
    ("GOOGL",       "GOOGL"),
    ("META",        "META"),
    ("AMZN",        "AMZN"),
]


def fetch_strip_data() -> list[dict]:
    """
    Fetch latest price and % change for all strip tickers.
    Uses yf.download (batch) for speed — single API call for all tickers.
    Falls back gracefully: if a ticker fails, it is skipped.
    Returns list of dicts: {name, price, change_pct, up}
    """
    results = []
    tickers_list = [t for _, t in STRIP_STOCKS]
    name_map     = {t: n for n, t in STRIP_STOCKS}

    try:
        # Batch download last 2 days so we can compute daily change
        raw = yf.download(
            tickers_list,
            period="2d",
            interval="1d",
            group_by="ticker",
            auto_adjust=True,
            progress=False,
            threads=True,
        )

        for ticker in tickers_list:
            try:
                # For multiple tickers, raw is MultiIndex; for one ticker it's flat
                if len(tickers_list) > 1:
                    closes = raw[ticker]["Close"].dropna()
                else:
                    closes = raw["Close"].dropna()

                if len(closes) < 1:
                    continue

                price   = float(closes.iloc[-1])
                prev    = float(closes.iloc[-2]) if len(closes) >= 2 else price
                chg_pct = ((price - prev) / prev * 100) if prev else 0.0

                # Currency prefix
                if ticker.endswith(".NS") or ticker.endswith(".BO"):
                    price_str = f"₹{price:,.2f}"
                else:
                    price_str = f"${price:,.2f}"

                results.append({
                    "name":       name_map.get(ticker, ticker),
                    "price":      price_str,
                    "change_pct": f"{chg_pct:+.2f}%",
                    "up":         chg_pct >= 0,
                })
            except Exception:
                continue

    except Exception:
        # Total failure — return empty so app doesn't crash
        pass

    return results


def build_strip_html(stocks: list[dict]) -> str:
    """
    Build the scrolling ticker strip HTML + CSS.
    Uses a pure CSS marquee animation — no JS required.
    Doubles the content so the scroll loops seamlessly.
    """
    if not stocks:
        # Fallback static strip if data fetch failed
        stocks = [
            {"name": "RELIANCE", "price": "—",    "change_pct": "—",     "up": True},
            {"name": "TCS",      "price": "—",    "change_pct": "—",     "up": True},
            {"name": "NVDA",     "price": "—",    "change_pct": "—",     "up": True},
            {"name": "AAPL",     "price": "—",    "change_pct": "—",     "up": False},
        ]

    def item_html(s):
        colour  = "#16a34a" if s["up"] else "#dc2626"
        arrow   = "▲" if s["up"] else "▼"
        return (
            f'<span style="display:inline-flex;align-items:center;gap:8px;'
            f'margin-right:40px;white-space:nowrap;">'
            f'<span style="color:#d1d5db;font-weight:600;font-size:12px;">{s["name"]}</span>'
            f'<span style="color:#9ca3af;font-size:12px;">{s["price"]}</span>'
            f'<span style="color:{colour};font-size:12px;font-weight:600;">'
            f'{arrow} {s["change_pct"]}</span>'
            f'</span>'
        )

    # Build one pass of items, then duplicate for seamless loop
    inner = "".join(item_html(s) for s in stocks)
    track = inner + inner   # duplicate for seamless loop

    return f"""
<style>
.ticker-wrap {{
    background: #111827;
    border-bottom: 1px solid #1f2937;
    overflow: hidden;
    width: 100%;
    height: 36px;
    display: flex;
    align-items: center;
    position: relative;
}}
.ticker-track {{
    display: inline-flex;
    align-items: center;
    white-space: nowrap;
    animation: ticker-scroll 60s linear infinite;
    padding-left: 100%;
}}
.ticker-wrap:hover .ticker-track {{
    animation-play-state: paused;
}}
@keyframes ticker-scroll {{
    0%   {{ transform: translateX(0); }}
    100% {{ transform: translateX(-50%); }}
}}
</style>
<div class="ticker-wrap">
    <div class="ticker-track">{track}</div>
</div>
"""