"""
StockAI — Flask backend
Replaces streamlit with a proper web server.
Run: python app.py   (or gunicorn app:app)
"""

import os, re, time, json
from functools import lru_cache
from flask import Flask, request, jsonify, render_template, session
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "stockai-dev-secret-change-in-prod")

# ── RATE LIMITING (per session) ───────────────────────────────────────────────
COOLDOWN = 20
MAX_REQ  = 15

def rate_ok(sess):
    now     = time.time()
    elapsed = now - sess.get("last_request_time", 0)
    if elapsed < COOLDOWN:
        return False, int(COOLDOWN - elapsed)
    if sess.get("request_count", 0) >= MAX_REQ:
        return False, -1  # -1 = session limit
    return True, 0

# ── DATA HELPERS ──────────────────────────────────────────────────────────────
def sanitise_ticker(raw: str):
    cleaned = re.sub(r'[^A-Z0-9.\-&]', '', raw.upper().strip())[:15]
    if not cleaned:
        return None
    if not re.match(r'^[A-Z0-9&\-]{1,12}(\.[A-Z]{1,3})?$', cleaned):
        return None
    return cleaned

# Cache stock data for 5 minutes
_stock_cache = {}
_cache_times = {}

def cached_stock_data(ticker: str) -> dict:
    now = time.time()
    if ticker in _stock_cache and (now - _cache_times.get(ticker, 0)) < 300:
        return _stock_cache[ticker]
    try:
        from src.data import get_stock_data, clean_data
        data = clean_data(get_stock_data(ticker))
        _stock_cache[ticker] = data
        _cache_times[ticker] = now
        return data
    except Exception as e:
        raise RuntimeError(str(e))

# ── STRIP PRICE CACHE ─────────────────────────────────────────────────────────
_strip_cache      = []
_strip_cache_time = 0

STRIP_TICKERS = {
    "RELIANCE": "RELIANCE.NS",
    "TCS":      "TCS.NS",
    "INFY":     "INFY.NS",
    "HDFC BK":  "HDFCBANK.NS",
    "NIFTY50":  "^NSEI",
    "SENSEX":   "^BSESN",
    "NVIDIA":   "NVDA",
    "APPLE":    "AAPL",
    "TESLA":    "TSLA",
}

def fetch_strip_prices():
    global _strip_cache, _strip_cache_time
    if time.time() - _strip_cache_time < 45:
        return _strip_cache
    import yfinance as yf
    results = []
    for label, sym in STRIP_TICKERS.items():
        try:
            hist = yf.Ticker(sym).history(period="5d", interval="1d")
            if hist is None or hist.empty or "Close" not in hist.columns:
                continue
            closes = hist["Close"].dropna()
            if len(closes) < 2:
                continue
            prev = float(closes.iloc[-2])
            curr = float(closes.iloc[-1])
            if prev == 0:
                continue
            chg = ((curr - prev) / prev) * 100
            is_index = sym.startswith("^")
            is_in    = sym.endswith((".NS", ".BO"))
            cur = "" if is_index else ("₹" if is_in else "$")
            results.append({
                "label": label,
                "price": f"{cur}{curr:,.2f}" if cur else f"{curr:,.0f}",
                "chg":   round(chg, 2),
            })
        except Exception:
            continue
    _strip_cache      = results
    _strip_cache_time = time.time()
    return results

# ── VECTORSTORE ───────────────────────────────────────────────────────────────
_vs = None
def get_vectorstore():
    global _vs
    if _vs is None and os.path.exists("data/faiss_index"):
        try:
            from src.rag import load_faiss_index
            _vs = load_faiss_index()
        except Exception:
            pass
    return _vs

# ═══════════════════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/strip")
def api_strip():
    try:
        return jsonify(fetch_strip_prices())
    except Exception:
        return jsonify([])

@app.route("/api/search")
def api_search():
    from data_constants import ALL_COMPANIES
    q = request.args.get("q", "").lower().strip()
    if len(q) < 2:
        return jsonify([])
    matches = [
        {"name": n, "ticker": tk}
        for n, tk in ALL_COMPANIES.items()
        if q in n.lower()
    ]
    return jsonify(matches[:10])

@app.route("/api/analyse", methods=["POST"])
def api_analyse():
    body   = request.get_json(force=True)
    ticker = body.get("ticker", "").strip()
    level  = body.get("level", "💼 Intermediate")

    # Sanitise
    clean = sanitise_ticker(ticker)
    if not clean:
        return jsonify({"error": "invalid_ticker"}), 400

    # Rate limit
    ok, wait = rate_ok(session)
    if not ok:
        if wait == -1:
            return jsonify({"error": "session_limit"}), 429
        return jsonify({"error": "rate_limit", "wait": wait}), 429

    try:
        import yfinance as yf
        from src.data    import analyse_history
        from src.signals import basic_signal
        from src.utils   import get_currency_symbol

        data     = cached_stock_data(clean)
        signals  = basic_signal(data)
        history  = analyse_history(clean, price_hist=data.get("_price_hist"))
        currency = get_currency_symbol(clean) or "₹"

        price_hist = data.get("_price_hist")
        if price_hist is None or (hasattr(price_hist, "empty") and price_hist.empty):
            price_hist = yf.Ticker(clean).history(period="1y")

        price_data = {}
        if price_hist is not None and not price_hist.empty:
            price_data = {
                "dates":  price_hist.index.strftime("%Y-%m-%d").tolist(),
                "closes": price_hist["Close"].round(2).tolist(),
            }

    except Exception as e:
        err = str(e).lower()
        if "too many requests" in err or "rate" in err:
            return jsonify({"error": "busy"}), 503
        return jsonify({"error": "fetch_error", "detail": str(e)}), 500

    # AI brief
    vectorstore = get_vectorstore()
    try:
        from src.llm import generate_stock_brief
        brief = generate_stock_brief(data, signals, clean, vectorstore, lang="English", level=level)
        session["request_count"]    = session.get("request_count", 0) + 1
        session["last_request_time"] = time.time()
    except Exception:
        try:
            from src.llm import _fallback_brief
            brief = _fallback_brief(data, signals, clean, level=level)
        except Exception:
            brief = {
                "company_name": clean, "sector": "N/A",
                "key_metrics": {}, "traffic_light": "YELLOW",
                "traffic_light_reason": "Could not generate AI brief.",
                "analyst_summary": "N/A", "valuation_commentary": "N/A",
                "growth_outlook": "N/A", "risk_flags": [],
                "financial_health": "N/A", "investor_profile": "N/A",
                "watch_out_for": "N/A", "news_context": "N/A",
                "annual_report_insights": None,
            }

    # Technical indicators
    tech = {}
    try:
        from src.analytics import technical_snapshot
        tech = technical_snapshot(price_hist)
    except Exception:
        pass

    # Peer comparison
    peer_data = {}
    try:
        from src.analytics import fetch_peer_metrics
        peer_data = fetch_peer_metrics(clean)
    except Exception:
        pass

    # Historical financials
    fin_trend = {}
    try:
        from src.analytics import fetch_historical_financials
        fin_trend = fetch_historical_financials(clean)
    except Exception:
        pass

    # Correlation & volatility
    corr_data = {}
    try:
        from src.analytics import correlation_volatility
        corr_data = correlation_volatility(clean, price_hist=price_hist)
    except Exception:
        pass

    # Extended metrics
    ext_metrics = []
    try:
        from src.utils import format_number, format_price as fp
        if data.get("forward_pe")     not in (None, "N/A"): ext_metrics.append(("Forward P/E",    f"{float(data['forward_pe']):.1f}x"))
        if data.get("target_price")   not in (None, "N/A"): ext_metrics.append(("Analyst Target", fp(data["target_price"], clean)))
        if data.get("ev_to_ebitda")   not in (None, "N/A"): ext_metrics.append(("EV/EBITDA",      f"{float(data['ev_to_ebitda']):.1f}x"))
        if data.get("beta")           not in (None, "N/A"): ext_metrics.append(("Beta",            f"{float(data['beta']):.2f}"))
        if data.get("free_cashflow")  not in (None, "N/A"): ext_metrics.append(("Free Cash Flow",  format_number(data["free_cashflow"], clean)))
        if data.get("recommendation") not in (None, "N/A"): ext_metrics.append(("Analyst View",    str(data["recommendation"]).upper()))
    except Exception:
        pass

    # History stats
    history_stats = {}
    if history:
        history_stats = {
            "high_52w":   history.get("high_52w"),
            "low_52w":    history.get("low_52w"),
            "avg_price":  history.get("avg_price"),
            "volatility": history.get("volatility"),
            "ma50":       history.get("ma50"),
            "ma200":      history.get("ma200"),
        }

    return jsonify({
        "brief":        brief,
        "signals":      signals,
        "price_data":   price_data,
        "history":      history_stats,
        "currency":     currency,
        "tech":         tech,
        "peers":        peer_data,
        "fin_trend":    fin_trend,
        "corr":         corr_data,
        "ext_metrics":  ext_metrics,
        "has_rag":      vectorstore is not None,
    })

@app.route("/api/companies")
def api_companies():
    from data_constants import COMPANIES_BY_EXCHANGE
    return jsonify(COMPANIES_BY_EXCHANGE)

# ── CHATBOT ───────────────────────────────────────────────────────────────────
CHAT_SYSTEM = """You are StockAI Assistant — a helpful, knowledgeable financial research chatbot
built into StockAI, an equity research platform.

You can help with:
- Questions about any specific stock currently being analysed (you'll receive live data as context)
- General investing concepts, financial metrics, market terminology
- How to read financial statements, ratios, signals
- Sector analysis, valuation frameworks, risk concepts
- Indian markets (NSE/BSE), US markets (NYSE/NASDAQ), and global exchanges

Rules:
- Always clarify you are NOT giving financial advice and cannot predict prices
- Be concise but informative — use bullet points for lists, plain language for Beginners
- If given stock context, use it to give specific, relevant answers
- Adapt your language to the user's knowledge level when told
- Never invent specific numbers — if you don't know a figure, say so

Knowledge level adjustments:
- Beginner: avoid jargon, use simple analogies, explain every term you use
- Learner: light explanations, assume basic knowledge of P/E, ROE etc.
- Intermediate: full financial terminology, no hand-holding
- Expert: technical depth, can discuss advanced metrics, options, macro
"""

@app.route("/api/chat", methods=["POST"])
def api_chat():
    body    = request.get_json(force=True)
    messages = body.get("messages", [])   # full conversation history
    context  = body.get("context", {})    # current stock data if on analysis page
    level    = body.get("level", "💼 Intermediate")

    if not messages:
        return jsonify({"error": "no_messages"}), 400

    # Build system prompt, injecting stock context if available
    system = CHAT_SYSTEM + f"\n\nUser knowledge level: {level}\n"
    if context.get("ticker"):
        m = context.get("key_metrics", {})
        system += f"""
Current stock being analysed:
- Company: {context.get('company_name', context['ticker'])}
- Ticker: {context['ticker']}
- Sector: {context.get('sector', 'N/A')}
- Price: {m.get('price', 'N/A')}
- P/E Ratio: {m.get('pe_ratio', 'N/A')}
- P/B Ratio: {m.get('pb_ratio', 'N/A')}
- ROE: {m.get('roe', 'N/A')}
- Profit Margin: {m.get('profit_margin', 'N/A')}
- Debt/Equity: {m.get('debt_to_equity', 'N/A')}
- Revenue Growth: {m.get('revenue_growth', 'N/A')}
- 1Y Return: {m.get('one_year_return', 'N/A')}
- Analyst Summary: {context.get('analyst_summary', 'N/A')}
- Risk Flags: {', '.join(context.get('risk_flags', [])) or 'None'}
- Traffic Light: {context.get('traffic_light', 'N/A')} — {context.get('traffic_light_reason', '')}

Use this data when answering questions about this stock.
"""

    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key:
        return jsonify({"error": "no_groq_key", "reply": "AI chat is unavailable — GROQ_API_KEY not configured."}), 503

    try:
        import groq as groq_lib
        client = groq_lib.Groq(api_key=groq_key)
        resp   = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "system", "content": system}] + messages,
            max_tokens=600,
            temperature=0.5,
        )
        reply = resp.choices[0].message.content.strip()
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e), "reply": "Sorry, I couldn't process that. Please try again."}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
