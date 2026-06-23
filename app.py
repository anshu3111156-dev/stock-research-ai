import os
import re
import time
import streamlit as st
import plotly.graph_objects as go
from dotenv import load_dotenv

load_dotenv()

# ── SECRETS ───────────────────────────────────────────────────────────────────
try:
    for key in ["GROQ_API_KEY", "NEWS_API_KEY"]:
        if key in st.secrets and key not in os.environ:
            os.environ[key] = st.secrets[key]
except Exception as e:
    print(f"[WARN] Could not load secrets: {e}")

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Clariva — Equity Research",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── SIMPLE STRING HELPERS (English only) ─────────────────────────────────────
STRINGS = {
    "hero_title":     "Smart research for",
    "hero_highlight": "every investor.",
    "hero_sub":       "AI-powered equity analysis from NSE, BSE, NYSE and 25+ global exchanges",
    "level_prompt":   "Tell us your investing experience so we can tailor the analysis for you",
    "search_title":   "Search any company",
    "search_sub":     "Type a company name or browse by exchange below",
    "analyse_btn":    "Analyse",
    "back_btn":       "← Back to Search",
    "change_level":   "↩ Change Level",
    "glossary_btn":   "📚 Glossary",
    "glossary_title": "📚 Financial Terms Glossary",
    "glossary_search":"Search a term — e.g. P/E Ratio, ROE, Market Cap...",
    "popular":        "POPULAR STOCKS",
    "how_it_works":   "HOW IT WORKS",
    "key_metrics":    "KEY METRICS",
    "price_history":  "PRICE HISTORY — 1 YEAR",
    "signals":        "SIGNALS DETECTED",
    "ai_brief":       "AI RESEARCH BRIEF",
    "analyst_summary":"📌 Analyst Summary",
    "valuation":      "💰 Valuation",
    "growth":         "📈 Growth Outlook",
    "risks":          "⚠️ Risk Flags",
    "health":         "💪 Financial Health",
    "profile":        "👤 Investor Profile",
    "watch":          "🔍 Watch Out For",
    "news":           "📰 Latest News & Market Context",
    "annual":         "📋 Annual Report Insights",
    "beginner_guide": "WHAT DO THESE NUMBERS MEAN?",
    "beginner_title": "📖 Simple Guide — What You Just Read",
    "not_advice":     "Not financial advice",
    "fetching":       "Fetching live market data...",
    "generating":     "Generating AI research brief...",
    "footer":         "StockAI · by Anshika Singh · Electronics Engineering, Banasthali Vidyapith · Powered by yfinance · Groq · RAG · Not financial advice",
    "tailored":       "Analysis tailored to your experience level",
    "nav_tag":        "Groq · yfinance · RAG",
    "level_i_am":     "I'm a",
    "or_ticker":      "Or enter a ticker manually (e.g. RELIANCE.NS / TSLA)",
    "invalid_ticker": "Invalid ticker. Use only letters, numbers, dots and hyphens.",
    "not_found":      "Company not found — enter ticker manually below",
    "session_limit":  "You have reached the session request limit. Please refresh the page.",
    "rate_wait":      "Please wait {secs}s before the next request.",
    "busy":           "⚠️ Market data service is busy. Please wait 2 minutes and try again.",
    "ai_warn":        "⚠️ AI brief unavailable. Showing data view.",
    "fetch_error":    "⚠️ Could not fetch data for {name}. Check the ticker and try again.",
}

def t(key, **kwargs):
    s = STRINGS.get(key, key)
    return s.format(**kwargs) if kwargs else s


# ── LEVEL-AWARE EXPLAINER HELPERS ─────────────────────────────────────────────
# These control how much of the Technical Indicators / Peer Comparison /
# Correlation sections render at each level, and inject a plain-language
# explainer line for lower levels — without removing the underlying data,
# per the "show but simplify" requirement for Beginner.

def is_beginner(level: str) -> bool:
    return "Beginner" in level or "🌱" in level

def is_learner(level: str) -> bool:
    return "Learner" in level or "📈" in level

def is_expert(level: str) -> bool:
    return "Expert" in level or "🏦" in level

def level_rank(level: str) -> int:
    """0=Beginner, 1=Learner, 2=Intermediate, 3=Expert — for 'show N items' gating."""
    if is_beginner(level):
        return 0
    if is_learner(level):
        return 1
    if is_expert(level):
        return 3
    return 2  # Intermediate / unrecognised default

# Max number of extended-metric chips, peer-table rows-of-detail, etc. shown
# per level. Beginner sees the simplest, most essential subset; Expert sees
# everything. This is intentionally a count cap, not a content swap — same
# underlying data source, fewer items surfaced at lower levels.
MAX_EXTENDED_METRICS = {0: 2, 1: 3, 2: 5, 3: 99}
MAX_SIGNALS_SHOWN     = {0: 4, 1: 6, 2: 10, 3: 99}
MAX_PEER_COLUMNS      = {0: 3, 1: 4, 2: 5, 3: 5}  # company,P/E,P/B capped lowest; full table for higher levels

PLAIN_EXPLAINERS = {
    "technical": {
        0: ("These are technical indicators traders use to study price patterns. "
            "You don't need to understand the formulas — just know that they describe what the "
            "price has been doing recently, not what it will do next."),
        1: ("RSI, MACD and Bollinger Bands describe recent price momentum and how stretched the "
            "price is versus its recent range. They're descriptive, not predictive."),
        2: ("Standard momentum/volatility indicators (RSI, MACD, Bollinger Bands), shown here as "
            "descriptive context on recent price action."),
        3: ("Textbook technical readings (RSI-14, MACD, Bollinger Bands) for recent price action."),
    },
    "peers": {
        0: ("This compares the company to a few similar companies in the same industry. "
            "A number only means something next to others like it — e.g. a P/E of 30 sounds high, "
            "but might be normal for that industry."),
        1: ("Comparing key ratios against a few close industry peers gives context — "
            "the same number can mean different things in different sectors."),
        2: ("Ratios for this stock vs its closest listed peers, for relative valuation context."),
        3: ("Peer set ratios (P/E, P/B, ROE, margin, market cap) for relative valuation benchmarking."),
    },
    "correlation": {
        0: ("This shows how closely this stock's price moves track the overall market. "
            "A high number means it usually goes up and down WITH the market; a low number means "
            "it moves more on its own."),
        1: ("Correlation and beta describe how this stock's moves have related to the broader "
            "market index recently — useful context, not a forecast."),
        2: ("Correlation, beta estimate, and annualised volatility vs the relevant benchmark index."),
        3: ("Trailing correlation/beta vs benchmark, with annualised volatility — descriptive co-movement only."),
    },
}

def plain_explainer(section: str, level: str) -> str:
    rank = level_rank(level)
    return PLAIN_EXPLAINERS.get(section, {}).get(rank, "")


# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

*, *::before, *::after {
    box-sizing: border-box;
    font-family: 'Inter', -apple-system, sans-serif;
}

#MainMenu, footer, header, .stDeployButton,
div[data-testid="stDecoration"],
[data-testid="stSidebar"] { display: none !important; }

.stApp {
    background-color: #1a1f2e !important;
    color: #e2e8f0 !important;
}
section[data-testid="stMain"] > div { padding-top: 0 !important; }
.main .block-container {
    background-color: #1a1f2e !important;
    padding: 0 2rem 2rem 2rem !important;
    max-width: 1300px !important;
}

/* ── NAVBAR ── */
.tt-navbar {
    background: #151a27;
    border-bottom: 1px solid #2d3548;
    padding: 0 32px;
    height: 58px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 0 -2rem 0 -2rem;
}
.tt-logo {
    font-size: 20px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.3px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.tt-logo-dot {
    width: 9px; height: 9px;
    background: #ff8c00;
    border-radius: 50%;
    display: inline-block;
}
.tt-nav-right { display: flex; align-items: center; gap: 16px; }
.tt-nav-tag { font-size: 12px; color: #475569; }
.tt-not-advice {
    font-size: 10px; color: #475569;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 4px;
    padding: 3px 8px;
}

/* ── TICKER STRIP ── */
.tt-strip {
    background: #111827;
    border-bottom: 1px solid #2d3548;
    padding: 9px 0;
    margin: 0 -2rem 0 -2rem;
    overflow: hidden;
    white-space: nowrap;
}
.tt-strip-inner {
    display: inline-flex;
    gap: 0;
    animation: marquee 40s linear infinite;
}
.tt-strip:hover .tt-strip-inner { animation-play-state: paused; }
@keyframes marquee {
    0%   { transform: translateX(0); }
    100% { transform: translateX(-50%); }
}
.tt-strip-item {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 0 28px;
    border-right: 1px solid #2d3548;
    font-size: 12px;
}
.tt-strip-name  { color: #94a3b8; font-weight: 600; letter-spacing: 0.3px; }
.tt-strip-price { color: #ffffff; font-weight: 700; }
.tt-strip-up    { color: #22c55e; font-weight: 600; }
.tt-strip-down  { color: #ef4444; font-weight: 600; }

/* ── HERO ── */
.tt-hero {
    text-align: center;
    padding: 60px 20px 44px;
}
.tt-hero-title {
    font-size: 46px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -1.8px;
    line-height: 1.1;
    margin-bottom: 6px;
}
.tt-hero-accent { color: #ff8c00; }
.tt-hero-sub {
    font-size: 15px;
    color: #64748b;
    margin-top: 12px;
}

/* ── LEVEL CARDS ── */
.tt-level-card {
    background: #222836;
    border: 1.5px solid #2d3548;
    border-radius: 14px;
    padding: 26px 16px;
    text-align: center;
    transition: all 0.18s ease;
    min-height: 160px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}
.tt-level-card:hover {
    border-color: #ff8c00;
    background: #252d3e;
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(255,140,0,0.08);
}
.tt-level-icon { font-size: 28px; margin-bottom: 10px; }
.tt-level-name { font-size: 14px; font-weight: 700; color: #ffffff; margin-bottom: 4px; }
.tt-level-desc { font-size: 11px; color: #64748b; line-height: 1.4; }

/* ── SECTION LABEL ── */
.tt-section-label {
    font-size: 11px;
    font-weight: 700;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 1.4px;
    margin: 26px 0 12px;
}

/* ── CARDS ── */
.tt-card {
    background: #222836;
    border: 1px solid #2d3548;
    border-radius: 12px;
    padding: 20px 22px;
    margin: 6px 0;
}
.tt-card-title {
    font-size: 10px;
    font-weight: 700;
    color: #ff8c00;
    text-transform: uppercase;
    letter-spacing: 1.1px;
    margin-bottom: 12px;
}
.tt-card-text {
    font-size: 13px;
    color: #94a3b8;
    line-height: 1.8;
}

/* ── METRIC CARDS ── */
.tt-metric {
    background: #222836;
    border: 1px solid #2d3548;
    border-radius: 10px;
    padding: 16px 18px;
    margin: 4px 0;
}
.tt-metric-label {
    font-size: 10px;
    font-weight: 600;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.9px;
    margin-bottom: 7px;
}
.tt-metric-value { font-size: 20px; font-weight: 700; color: #ffffff; }

/* ── COMPANY HEADER ── */
.tt-company-header {
    background: #222836;
    border: 1px solid #2d3548;
    border-radius: 14px;
    padding: 26px 30px;
    margin: 16px 0 20px;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 16px;
}
.tt-company-name { font-size: 26px; font-weight: 800; color: #ffffff; letter-spacing: -0.5px; margin-bottom: 4px; }
.tt-company-meta { font-size: 12px; color: #64748b; }
.tt-price { font-size: 32px; font-weight: 700; color: #ffffff; text-align: right; }
.tt-return-up   { font-size: 14px; font-weight: 600; color: #22c55e; }
.tt-return-down { font-size: 14px; font-weight: 600; color: #ef4444; }

/* ── TRAFFIC LIGHT ── */
.tl-green {
    background: rgba(34,197,94,0.06);
    border: 1.5px solid rgba(34,197,94,0.2);
    border-left: 4px solid #22c55e;
    border-radius: 10px;
    padding: 14px 18px;
    margin: 0 0 16px;
    display: flex; align-items: center; gap: 12px;
}
.tl-yellow {
    background: rgba(255,140,0,0.06);
    border: 1.5px solid rgba(255,140,0,0.2);
    border-left: 4px solid #ff8c00;
    border-radius: 10px;
    padding: 14px 18px;
    margin: 0 0 16px;
    display: flex; align-items: center; gap: 12px;
}
.tl-red {
    background: rgba(239,68,68,0.06);
    border: 1.5px solid rgba(239,68,68,0.2);
    border-left: 4px solid #ef4444;
    border-radius: 10px;
    padding: 14px 18px;
    margin: 0 0 16px;
    display: flex; align-items: center; gap: 12px;
}
.tl-dot-green  { width:13px;height:13px;border-radius:50%;background:#22c55e;flex-shrink:0; }
.tl-dot-yellow { width:13px;height:13px;border-radius:50%;background:#ff8c00;flex-shrink:0; }
.tl-dot-red    { width:13px;height:13px;border-radius:50%;background:#ef4444;flex-shrink:0; }
.tl-text { font-size: 13px; color: #e2e8f0; font-weight: 500; }

/* ── SIGNAL CHIPS ── */
.chip-red   { display:inline-flex;align-items:center;background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.25);color:#ef4444;border-radius:20px;padding:5px 12px;font-size:12px;font-weight:500;margin:3px;gap:5px; }
.chip-green { display:inline-flex;align-items:center;background:rgba(34,197,94,0.08);border:1px solid rgba(34,197,94,0.25);color:#22c55e;border-radius:20px;padding:5px 12px;font-size:12px;font-weight:500;margin:3px;gap:5px; }
.chip-amber { display:inline-flex;align-items:center;background:rgba(255,140,0,0.08);border:1px solid rgba(255,140,0,0.25);color:#ff8c00;border-radius:20px;padding:5px 12px;font-size:12px;font-weight:500;margin:3px;gap:5px; }

/* ── RISK TAGS ── */
.risk-pill { display:inline-block;background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.25);color:#ef4444;border-radius:8px;padding:6px 12px;font-size:12px;margin:4px;line-height:1.5; }

/* ── NEWS / RAG ── */
.tt-news-card { background:#222836;border:1px solid #2d3548;border-left:3px solid #ff8c00;border-radius:12px;padding:20px 22px;margin:6px 0; }
.tt-rag-card  { background:#222836;border:1px solid #2d3548;border-left:3px solid #6366f1;border-radius:12px;padding:20px 22px;margin:6px 0; }

/* ── BEGINNER ── */
.tt-beginner { background:linear-gradient(135deg,#1c2a1e 0%,#222836 100%);border:1px solid rgba(34,197,94,0.2);border-radius:12px;padding:20px 22px;margin:6px 0; }

/* ── SUGGESTION ROWS ── */
.tt-suggestion { background:#222836;border:1px solid #2d3548;border-radius:8px;padding:12px 16px;margin:4px 0;display:flex;justify-content:space-between;align-items:center;transition:border-color 0.15s; }
.tt-suggestion:hover { border-color:#ff8c00;background:#252d3e; }
.tt-sug-name   { font-size:14px;color:#e2e8f0;font-weight:500; }
.tt-sug-ticker { font-size:11px;color:#ff8c00;font-weight:600;background:rgba(255,140,0,0.1);padding:3px 8px;border-radius:4px; }

/* ── BADGE ── */
.tt-badge { display:inline-flex;align-items:center;background:rgba(255,140,0,0.1);border:1px solid rgba(255,140,0,0.3);color:#ff8c00;border-radius:20px;padding:4px 12px;font-size:12px;font-weight:600;gap:5px; }

/* ── GLOSSARY ── */
.tt-gloss-card { background:#222836;border:1px solid #2d3548;border-radius:10px;padding:16px 18px;margin:6px 0; }
.tt-gloss-word { font-size:13px;font-weight:700;color:#ff8c00;margin-bottom:4px; }
.tt-gloss-def  { font-size:12px;color:#64748b;line-height:1.6; }

/* ── TERMINAL / DATA-DENSE PANELS ── */
.tt-panel {
    background:#1c2230;
    border:1px solid #2d3548;
    border-radius:10px;
    padding:16px 18px;
    margin:6px 0;
}
.tt-panel-head {
    display:flex; justify-content:space-between; align-items:center;
    margin-bottom:12px;
}
.tt-panel-title {
    font-size:10.5px; font-weight:700; color:#ff8c00;
    text-transform:uppercase; letter-spacing:1.1px;
}
.tt-panel-sub { font-size:10.5px; color:#475569; font-family:'JetBrains Mono','Consolas',monospace; }

/* Monospace numeric readouts, terminal-style */
.tt-mono { font-family:'JetBrains Mono','Consolas',monospace; }
.tt-num-grid {
    display:grid; grid-template-columns:repeat(auto-fit,minmax(110px,1fr));
    gap:1px; background:#2d3548; border-radius:8px; overflow:hidden;
}
.tt-num-cell {
    background:#1c2230; padding:12px 14px;
}
.tt-num-label { font-size:9.5px; color:#475569; text-transform:uppercase; letter-spacing:0.8px; margin-bottom:5px; }
.tt-num-value { font-size:16px; font-weight:700; color:#ffffff; font-family:'JetBrains Mono','Consolas',monospace; }
.tt-num-tag   { font-size:10px; margin-top:4px; font-weight:600; }
.tt-tag-good  { color:#22c55e; }
.tt-tag-warn  { color:#ff8c00; }
.tt-tag-bad   { color:#ef4444; }
.tt-tag-neutral { color:#64748b; }

/* Data table — peer comparison etc */
.tt-table { width:100%; border-collapse:collapse; font-size:12.5px; }
.tt-table th {
    text-align:right; padding:9px 12px;
    color:#475569; font-weight:600; font-size:10px;
    text-transform:uppercase; letter-spacing:0.6px;
    border-bottom:1px solid #2d3548;
}
.tt-table th:first-child, .tt-table td:first-child { text-align:left; }
.tt-table td {
    text-align:right; padding:10px 12px;
    color:#cbd5e1; font-family:'JetBrains Mono','Consolas',monospace;
    border-bottom:1px solid #232a3a;
}
.tt-table tr.tt-subject-row td {
    background:rgba(255,140,0,0.06);
    color:#ffffff; font-weight:700;
}
.tt-table tr.tt-subject-row td:first-child { border-left:2px solid #ff8c00; }

/* Disclaimer / methodology note */
.tt-disclaimer {
    background:rgba(99,102,241,0.05);
    border:1px solid rgba(99,102,241,0.18);
    border-radius:8px;
    padding:10px 14px;
    margin:10px 0 4px;
    font-size:11.5px;
    color:#8b93a8;
    line-height:1.55;
    display:flex; gap:8px; align-items:flex-start;
}
.tt-disclaimer-icon { flex-shrink:0; font-size:13px; }

/* Plain-language explainer for lower levels — visually distinct from the
   methodology disclaimer (green-tinted = "here's what this means", vs the
   indigo disclaimer above = "here's the methodology caveat") */
.tt-plain-explain {
    background:rgba(34,197,94,0.05);
    border:1px solid rgba(34,197,94,0.18);
    border-radius:8px;
    padding:10px 14px;
    margin:10px 0 4px;
    font-size:12px;
    color:#a8d8b9;
    line-height:1.6;
    display:flex; gap:8px; align-items:flex-start;
}
.tt-plain-explain-icon { flex-shrink:0; font-size:13px; }

/* Tab-style sub-navigation within analysis page */
.tt-subtabs { display:flex; gap:4px; margin:18px 0 4px; flex-wrap:wrap; }

/* ── DIVIDER ── */
.tt-divider { border:none;border-top:1px solid #2d3548;margin:24px 0; }

/* ── INPUTS ── */
.stTextInput input {
    background:#222836 !important;
    border:1.5px solid #2d3548 !important;
    border-radius:10px !important;
    color:#ffffff !important;
    font-size:14px !important;
    padding:13px 18px !important;
}
.stTextInput input:focus { border-color:#ff8c00 !important; box-shadow:0 0 0 3px rgba(255,140,0,0.08) !important; }
.stTextInput input::placeholder { color:#475569 !important; }

/* Selectbox */
div[data-baseweb="select"] > div { background:#222836 !important;border:1.5px solid #2d3548 !important;border-radius:10px !important;color:#ffffff !important; }
div[data-baseweb="popover"] { background:#222836 !important;border:1px solid #2d3548 !important; }

/* ── BUTTONS ── */
.stButton button {
    background:#222836 !important;
    color:#94a3b8 !important;
    border:1px solid #2d3548 !important;
    border-radius:8px !important;
    font-size:13px !important;
    font-weight:500 !important;
    transition:all 0.15s !important;
}
.stButton button:hover { border-color:#ff8c00 !important;color:#ff8c00 !important;background:#252d3e !important; }

.primary-cta button {
    background:#ff8c00 !important;
    color:#ffffff !important;
    border:none !important;
    font-weight:700 !important;
    font-size:14px !important;
}
.primary-cta button:hover { background:#e67e00 !important; }

/* Spinner */
.stSpinner > div { border-top-color:#ff8c00 !important; }

/* Plotly */
.js-plotly-plot { border-radius:12px;overflow:hidden; }

/* Streamlit metric */
[data-testid="stMetricValue"] { color:#ffffff !important;font-size:18px !important;font-weight:700 !important; }
[data-testid="stMetricLabel"] { color:#475569 !important;font-size:11px !important; }
</style>
""", unsafe_allow_html=True)

# ── COMPANY DATABASE ──────────────────────────────────────────────────────────
COMPANIES_BY_EXCHANGE = {
    "🇮🇳 NSE — National Stock Exchange": {
        "Reliance Industries":       "RELIANCE.NS",
        "Tata Consultancy Services": "TCS.NS",
        "Infosys":                   "INFY.NS",
        "HDFC Bank":                 "HDFCBANK.NS",
        "ICICI Bank":                "ICICIBANK.NS",
        "State Bank of India":       "SBIN.NS",
        "Wipro":                     "WIPRO.NS",
        "HCL Technologies":          "HCLTECH.NS",
        "Bajaj Finance":             "BAJFINANCE.NS",
        "Bharti Airtel":             "BHARTIARTL.NS",
        "Asian Paints":              "ASIANPAINT.NS",
        "Maruti Suzuki":             "MARUTI.NS",
        "Tata Motors":               "TATAMOTORS.NS",
        "Sun Pharmaceutical":        "SUNPHARMA.NS",
        "ITC":                       "ITC.NS",
        "Kotak Mahindra Bank":       "KOTAKBANK.NS",
        "Axis Bank":                 "AXISBANK.NS",
        "Larsen & Toubro":           "LT.NS",
        "Titan Company":             "TITAN.NS",
        "Nestle India":              "NESTLEIND.NS",
        "Zomato":                    "ZOMATO.NS",
        "Paytm":                     "PAYTM.NS",
        "Nykaa":                     "NYKAA.NS",
        "IRCTC":                     "IRCTC.NS",
        "Adani Enterprises":         "ADANIENT.NS",
        "Adani Ports":               "ADANIPORTS.NS",
        "Power Grid":                "POWERGRID.NS",
        "NTPC":                      "NTPC.NS",
        "ONGC":                      "ONGC.NS",
        "Coal India":                "COALINDIA.NS",
        "Tata Steel":                "TATASTEEL.NS",
        "JSW Steel":                 "JSWSTEEL.NS",
        "Hindalco":                  "HINDALCO.NS",
        "UltraTech Cement":          "ULTRACEMCO.NS",
        "Divi's Laboratories":       "DIVISLAB.NS",
        "Dr Reddy's Laboratories":   "DRREDDY.NS",
        "Cipla":                     "CIPLA.NS",
        "Eicher Motors":             "EICHERMOT.NS",
        "Hero MotoCorp":             "HEROMOTOCO.NS",
        "Bajaj Auto":                "BAJAJ-AUTO.NS",
        "Tech Mahindra":             "TECHM.NS",
        "Mahindra & Mahindra":       "M&M.NS",
        "IndusInd Bank":             "INDUSINDBK.NS",
        "Tata Consumer Products":    "TATACONSUM.NS",
        "Pidilite Industries":       "PIDILITIND.NS",
        "Havells India":             "HAVELLS.NS",
        "Voltas":                    "VOLTAS.NS",
        "Grasim Industries":         "GRASIM.NS",
    },
    "🇮🇳 BSE — Bombay Stock Exchange": {
        "Tata Power":           "TATAPOWER.BO",
        "Suzlon Energy":        "SUZLON.BO",
        "YES Bank":             "YESBANK.BO",
        "Vodafone Idea":        "IDEA.BO",
        "BHEL":                 "BHEL.BO",
        "SAIL":                 "SAIL.BO",
        "Bank of Baroda":       "BANKBARODA.BO",
        "Punjab National Bank": "PNB.BO",
        "IDFC First Bank":      "IDFCFIRSTB.BO",
    },
    "🇺🇸 NYSE / NASDAQ": {
        "Apple":              "AAPL",
        "Microsoft":          "MSFT",
        "Amazon":             "AMZN",
        "Alphabet (Google)":  "GOOGL",
        "Meta (Facebook)":    "META",
        "Tesla":              "TSLA",
        "NVIDIA":             "NVDA",
        "JPMorgan Chase":     "JPM",
        "Johnson & Johnson":  "JNJ",
        "Visa":               "V",
        "Mastercard":         "MA",
        "Procter & Gamble":   "PG",
        "Walmart":            "WMT",
        "Disney":             "DIS",
        "Netflix":            "NFLX",
        "Goldman Sachs":      "GS",
        "BlackRock":          "BLK",
        "ExxonMobil":         "XOM",
        "Coca Cola":          "KO",
        "Nike":               "NKE",
        "McDonald's":         "MCD",
        "AMD":                "AMD",
        "Salesforce":         "CRM",
        "Adobe":              "ADBE",
        "PayPal":             "PYPL",
        "Uber":               "UBER",
        "Airbnb":             "ABNB",
        "Palantir":           "PLTR",
        "Berkshire Hathaway": "BRK-B",
        "Intel":              "INTC",
        "Spotify":            "SPOT",
        "Snowflake":          "SNOW",
    },
}

ALL_COMPANIES = {
    name: ticker
    for ex in COMPANIES_BY_EXCHANGE.values()
    for name, ticker in ex.items()
}

KNOWLEDGE_LEVELS = {
    "🌱 Beginner":     {"detail": "Never invested before or just getting started"},
    "📈 Learner":      {"detail": "Know the basics, still learning"},
    "💼 Intermediate": {"detail": "Comfortable with P/E, ROE and basic analysis"},
    "🏦 Expert":       {"detail": "Deep market knowledge, technical analysis"},
}

GLOSSARY = {
    "P/E Ratio":        "Price to Earnings — how much you pay for every ₹1 of profit. Lower = potentially cheaper.",
    "Forward P/E":      "Expected P/E based on next year's estimated earnings. Lower than trailing P/E = earnings expected to grow.",
    "P/B Ratio":        "Price to Book — stock price vs net assets. Below 1 means trading below book value.",
    "EPS":              "Earnings Per Share — company profit divided by number of shares. Higher is better.",
    "EV/EBITDA":        "Enterprise Value to EBITDA — accounts for debt in valuation. Popular for comparing companies.",
    "ROE":              "Return on Equity — profit generated per rupee of shareholder money. Above 15% is generally good.",
    "ROA":              "Return on Assets — how efficiently all assets are used to generate profit.",
    "Debt to Equity":   "How much the company has borrowed vs what shareholders own. D/E below 50% is generally low.",
    "Profit Margin":    "% of revenue that becomes profit. Higher = more efficient business model.",
    "Gross Margin":     "Revenue minus cost of goods sold, as a %. High gross margin = strong pricing power.",
    "Operating Margin": "Profit after operating costs. Shows how efficient the core business is.",
    "Free Cash Flow":   "Cash left after all expenses and investments. Positive FCF = real cash being generated.",
    "Current Ratio":    "Current assets / current liabilities. Above 1 = can pay short-term obligations.",
    "Beta":             "How much the stock moves vs the market. Beta 1.5 = 50% more volatile than Nifty/S&P 500.",
    "Revenue Growth":   "How much sales grew year-on-year. Above 10% is healthy for most sectors.",
    "Market Cap":       "Total value of all shares. Large cap >₹20,000 Cr, mid cap ₹5,000–20,000 Cr.",
    "52 Week High/Low": "Highest and lowest price in the past year. Useful for understanding price range.",
    "Moving Average":   "Average price over a period. MA50 = last 50 days. Price above MA200 = positive trend.",
    "Volatility":       "How much the price moves daily. Higher = more risk and potential reward.",
    "Dividend Yield":   "Annual dividend as % of stock price. Good for income-seeking investors.",
    "Bull Market":      "Rising market — prices going up over a sustained period.",
    "Bear Market":      "Falling market — prices going down over a sustained period.",
    "NSE":              "National Stock Exchange — India's largest exchange by trading volume.",
    "BSE":              "Bombay Stock Exchange — oldest exchange in Asia.",
    "SEBI":             "Securities and Exchange Board of India — regulates Indian markets.",
    "FII":              "Foreign Institutional Investors — large foreign funds investing in Indian markets.",
    "DII":              "Domestic Institutional Investors — Indian mutual funds and insurance companies.",
}

POPULAR = {
    "Reliance Industries": "RELIANCE.NS",
    "HDFC Bank":           "HDFCBANK.NS",
    "Infosys":             "INFY.NS",
    "Tata Motors":         "TATAMOTORS.NS",
    "Tesla":               "TSLA",
    "NVIDIA":              "NVDA",
    "Apple":               "AAPL",
    "Zomato":              "ZOMATO.NS",
}

# Tickers shown in the strip
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

# ── SESSION STATE ─────────────────────────────────────────────────────────────
for k, v in {
    "knowledge_level":       None,
    "request_count":         0,
    "last_request_time":     0.0,
    "selected_ticker":       "",
    "selected_company_name": "",
    "current_page":          "home",
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── HELPERS ───────────────────────────────────────────────────────────────────
@st.cache_resource
def load_vectorstore():
    if os.path.exists("data/faiss_index"):
        try:
            from src.rag import load_faiss_index
            return load_faiss_index()
        except Exception:
            return None
    return None

@st.cache_data(ttl=300, show_spinner=False)
def cached_stock_data(ticker: str) -> dict:
    from src.data import get_stock_data, clean_data
    return clean_data(get_stock_data(ticker))

def sanitise_ticker(raw: str):
    cleaned = re.sub(r'[^A-Z0-9.\-&]', '', raw.upper().strip())[:15]
    if not cleaned:
        return None
    if not re.match(r'^[A-Z0-9&\-]{1,12}(\.[A-Z]{1,3})?$', cleaned):
        return None
    return cleaned

COOLDOWN = 20
MAX_REQ  = 15

def rate_ok() -> bool:
    elapsed = time.time() - st.session_state.last_request_time
    if elapsed < COOLDOWN:
        st.warning(t("rate_wait", secs=int(COOLDOWN - elapsed)))
        return False
    if st.session_state.request_count >= MAX_REQ:
        st.error(t("session_limit"))
        return False
    return True

# ── LIVE TICKER STRIP ─────────────────────────────────────────────────────────
@st.cache_data(ttl=45, show_spinner=False)
def fetch_strip_prices() -> list[dict]:
    """
    Fetch latest prices for strip tickers.

    Uses individual yf.Ticker().history() calls instead of a single batch
    yf.download() — batch calls covering a mixed set of equities + indices
    are more prone to outright failing on shared/cloud IPs (Yahoo rate-limits
    these harder), and a single failure in a batch call can take the whole
    strip down. Per-ticker calls let partial failures degrade gracefully
    instead of blanking the entire strip.
    """
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
                "chg":   chg,
            })
        except Exception:
            continue

    return results

def build_strip_html(items: list[dict]) -> str:
    if not items:
        return ""
    inner = ""
    for it in items:
        chg    = it["chg"]
        cls    = "tt-strip-up" if chg >= 0 else "tt-strip-down"
        arrow  = "▲" if chg >= 0 else "▼"
        inner += (
            f'<span class="tt-strip-item">'
            f'<span class="tt-strip-name">{it["label"]}</span>'
            f'<span class="tt-strip-price">{it["price"]}</span>'
            f'<span class="{cls}">{arrow} {abs(chg):.2f}%</span>'
            f'</span>'
        )
    # duplicate for seamless loop
    doubled = inner + inner
    return f'<div class="tt-strip"><div class="tt-strip-inner">{doubled}</div></div>'

vectorstore = load_vectorstore()

# ── NAVBAR ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="tt-navbar">
    <div class="tt-logo">
        <span class="tt-logo-dot"></span>
        Clariva
    </div>
    <div class="tt-nav-right">
        <span class="tt-nav-tag">{t('nav_tag')}</span>
        <span class="tt-not-advice">{t('not_advice')}</span>
    </div>
</div>""", unsafe_allow_html=True)

# ── TICKER STRIP ──────────────────────────────────────────────────────────────
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=45_000, limit=None, key="ticker_refresh")
except ImportError:
    pass

strip_data = fetch_strip_prices()
if strip_data:
    st.markdown(build_strip_html(strip_data), unsafe_allow_html=True)
else:
    st.markdown(
        '<div class="tt-strip"><div class="tt-strip-inner">'
        '<span class="tt-strip-item">'
        '<span class="tt-strip-name" style="color:#475569;">'
        'Market data temporarily unavailable — refreshing automatically'
        '</span></span></div></div>',
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# PAGE A — KNOWLEDGE LEVEL SELECTOR
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.knowledge_level is None:

    st.markdown(f"""
    <div class="tt-hero">
        <div class="tt-hero-title">
            {t('hero_title')}<br>
            <span class="tt-hero-accent">{t('hero_highlight')}</span>
        </div>
        <div class="tt-hero-sub">{t('hero_sub')}</div>
    </div>""", unsafe_allow_html=True)

    st.markdown(
        f"<div style='text-align:center;font-size:14px;color:#475569;font-weight:500;"
        f"margin-bottom:24px;'>{t('level_prompt')}</div>",
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    for col, (level, info) in zip([c1, c2, c3, c4], KNOWLEDGE_LEVELS.items()):
        with col:
            icon  = level.split()[0]
            label = level.split(' ', 1)[1]
            st.markdown(f"""
            <div class="tt-level-card">
                <div class="tt-level-icon">{icon}</div>
                <div class="tt-level-name">{label}</div>
                <div class="tt-level-desc">{info['detail']}</div>
            </div>""", unsafe_allow_html=True)
            if st.button(f"{t('level_i_am')} {label}", key=f"lvl_{level}", use_container_width=True):
                st.session_state.knowledge_level = level
                st.rerun()

    st.markdown("<hr class='tt-divider'>", unsafe_allow_html=True)
    st.markdown(
        "<div style='text-align:center;color:#2d3548;font-size:12px;padding:14px;'>"
        "Trusted analysis · Live market data · Not financial advice</div>",
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# PAGE B — MAIN APP
# ══════════════════════════════════════════════════════════════════════════════
else:
    level = st.session_state.knowledge_level

    # ── TOP BAR ───────────────────────────────────────────────────────────────
    tb1, tb2, tb3 = st.columns([5, 2, 2])
    with tb1:
        st.markdown(
            f"<div style='padding:12px 0 8px;'><span class='tt-badge'>{level}</span>"
            f"<span style='color:#475569;font-size:12px;margin-left:10px;'>{t('tailored')}</span></div>",
            unsafe_allow_html=True,
        )
    with tb2:
        if st.button(t("glossary_btn"), use_container_width=True, key="gloss_btn"):
            st.session_state.current_page = (
                "glossary" if st.session_state.current_page != "glossary" else "home"
            )
    with tb3:
        if st.button(t("change_level"), use_container_width=True, key="chg_lvl"):
            st.session_state.knowledge_level = None
            st.session_state.current_page    = "home"
            st.rerun()

    st.markdown("<hr class='tt-divider'>", unsafe_allow_html=True)

    # ── GLOSSARY ──────────────────────────────────────────────────────────────
    if st.session_state.current_page == "glossary":
        st.markdown(
            f"<div style='font-size:22px;font-weight:800;color:#fff;"
            f"letter-spacing:-0.5px;margin-bottom:20px;'>{t('glossary_title')}</div>",
            unsafe_allow_html=True,
        )
        q = st.text_input("", placeholder=t("glossary_search"),
                          label_visibility="collapsed", key="gloss_q")
        for term, defn in GLOSSARY.items():
            if not q or q.lower() in term.lower() or q.lower() in defn.lower():
                st.markdown(f"""
                <div class="tt-gloss-card">
                    <div class="tt-gloss-word">{term}</div>
                    <div class="tt-gloss-def">{defn}</div>
                </div>""", unsafe_allow_html=True)

    # ── SEARCH / HOME ─────────────────────────────────────────────────────────
    elif st.session_state.current_page in ("home", "search"):

        st.markdown(f"""
        <div style='text-align:center;margin:32px 0 8px;'>
            <div style='font-size:28px;font-weight:800;color:#fff;
                 letter-spacing:-0.6px;margin-bottom:8px;'>{t('search_title')}</div>
            <div style='font-size:14px;color:#475569;'>{t('search_sub')}</div>
        </div>""", unsafe_allow_html=True)

        _, mid, _ = st.columns([1, 4, 1])
        with mid:
            query = st.text_input(
                "", placeholder="🔍  Search — Reliance, Apple, HDFC Bank, Tesla...",
                label_visibility="collapsed", key="main_search",
            )

            st.markdown(
                "<div style='text-align:center;color:#475569;font-size:12px;"
                "margin:14px 0 6px;'>— or browse by exchange —</div>",
                unsafe_allow_html=True,
            )
            exc_options = ["— Select exchange —"] + list(COMPANIES_BY_EXCHANGE.keys())
            sel_exc = st.selectbox("", exc_options, label_visibility="collapsed", key="exc_sel")

            if sel_exc != "— Select exchange —":
                cos    = COMPANIES_BY_EXCHANGE[sel_exc]
                co_opts = ["— Choose a company —"] + list(cos.keys())
                sel_co  = st.selectbox("", co_opts, label_visibility="collapsed", key="co_sel")
                if sel_co not in ("— Choose a company —", ""):
                    ticker = cos[sel_co]
                    st.caption(f"Symbol: `{ticker}`")
                    st.markdown('<div class="primary-cta">', unsafe_allow_html=True)
                    if st.button(f"📊 {t('analyse_btn')}: {sel_co}", use_container_width=True, key="analyse_exchange"):
                        if rate_ok():
                            st.session_state.selected_ticker       = ticker
                            st.session_state.selected_company_name = sel_co
                            st.session_state.current_page          = "analysis"
                            st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown(
                    f"<div style='color:#475569;font-size:12px;margin:10px 0 4px;'>{t('or_ticker')}</div>",
                    unsafe_allow_html=True,
                )
                manual = st.text_input(
                    "", placeholder="e.g. RELIANCE.NS / TSLA / AAPL",
                    label_visibility="collapsed", key="manual_t",
                )
                if manual:
                    clean = sanitise_ticker(manual)
                    if clean is None:
                        st.error(t("invalid_ticker"))
                    else:
                        st.markdown('<div class="primary-cta">', unsafe_allow_html=True)
                        if st.button(f"📊 {t('analyse_btn')}: {clean}", use_container_width=True, key="manual_go"):
                            if rate_ok():
                                st.session_state.selected_ticker       = clean
                                st.session_state.selected_company_name = clean
                                st.session_state.current_page          = "analysis"
                                st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

        # Live search suggestions
        if query and len(query) >= 2:
            matches = {n: tk for n, tk in ALL_COMPANIES.items() if query.lower() in n.lower()}
            _, mc, _ = st.columns([1, 4, 1])
            with mc:
                if matches:
                    for name, tkr in list(matches.items())[:8]:
                        s1, s2 = st.columns([5, 1])
                        with s1:
                            st.markdown(f"""
                            <div class="tt-suggestion">
                                <span class="tt-sug-name">{name}</span>
                                <span class="tt-sug-ticker">{tkr}</span>
                            </div>""", unsafe_allow_html=True)
                        with s2:
                            if st.button("→", key=f"sq_{tkr}"):
                                if rate_ok():
                                    st.session_state.selected_ticker       = tkr
                                    st.session_state.selected_company_name = name
                                    st.session_state.current_page          = "analysis"
                                    st.rerun()
                else:
                    st.markdown(
                        f"<div style='text-align:center;color:#475569;font-size:13px;"
                        f"padding:12px;'>{t('not_found')}</div>",
                        unsafe_allow_html=True,
                    )

        # Popular stocks
        if not query:
            st.markdown("<hr class='tt-divider'>", unsafe_allow_html=True)
            st.markdown(f"<div class='tt-section-label'>{t('popular')}</div>", unsafe_allow_html=True)
            pc = st.columns(4)
            for i, (name, tkr) in enumerate(POPULAR.items()):
                with pc[i % 4]:
                    if st.button(name, key=f"pop_{tkr}", use_container_width=True):
                        if rate_ok():
                            st.session_state.selected_ticker       = tkr
                            st.session_state.selected_company_name = name
                            st.session_state.current_page          = "analysis"
                            st.rerun()

            # How it works
            st.markdown("<hr class='tt-divider'>", unsafe_allow_html=True)
            st.markdown(f"<div class='tt-section-label'>{t('how_it_works')}</div>", unsafe_allow_html=True)
            hw1, hw2, hw3, hw4 = st.columns(4)
            for col, icon, title, desc in [
                (hw1, "🔍", "Search",      "Type any company from NSE, BSE or NYSE"),
                (hw2, "📊", "Live Data",   "Real-time financial data via yfinance"),
                (hw3, "🤖", "AI Analysis", "Groq's Llama 3 writes a personalised brief"),
                (hw4, "📋", "Your Report", "Valuation, health, risks and news in one view"),
            ]:
                with col:
                    st.markdown(f"""
                    <div class="tt-card" style="text-align:center;">
                        <div style="font-size:28px;margin-bottom:10px;">{icon}</div>
                        <div style="font-size:13px;font-weight:700;color:#fff;margin-bottom:6px;">{title}</div>
                        <div style="font-size:12px;color:#64748b;line-height:1.55;">{desc}</div>
                    </div>""", unsafe_allow_html=True)

    # ── ANALYSIS PAGE ─────────────────────────────────────────────────────────
    if st.session_state.current_page == "analysis" and st.session_state.selected_ticker:

        ticker       = st.session_state.selected_ticker
        company_name = st.session_state.get("selected_company_name", ticker)

        if st.button(t("back_btn"), key="back"):
            st.session_state.current_page          = "home"
            st.session_state.selected_ticker       = ""
            st.session_state.selected_company_name = ""
            st.rerun()

        st.markdown("<hr class='tt-divider'>", unsafe_allow_html=True)

        # Fetch data
        with st.spinner(t("fetching")):
            try:
                import yfinance as yf
                from src.data    import analyse_history
                from src.signals import basic_signal
                from src.utils   import get_currency_symbol

                data     = cached_stock_data(ticker)
                signals  = basic_signal(data)
                history  = analyse_history(ticker, price_hist=data.get("_price_hist"))
                currency = get_currency_symbol(ticker) or "₹"

                price_hist = data.get("_price_hist")
                if price_hist is None or (hasattr(price_hist, "empty") and price_hist.empty):
                    price_hist = yf.Ticker(ticker).history(period="1y")

                price_data = {}
                if price_hist is not None and not price_hist.empty:
                    price_data = {
                        "dates":  price_hist.index.strftime("%Y-%m-%d").tolist(),
                        "closes": price_hist["Close"].round(2).tolist(),
                    }
            except Exception as e:
                err = str(e).lower()
                if "too many requests" in err or "rate" in err:
                    st.error(t("busy"))
                else:
                    st.error(t("fetch_error", name=company_name))
                st.stop()

        # Generate AI brief — level now flows into BOTH the AI prompt depth
        # (handled inside generate_stock_brief / src/llm.py's LEVEL_CONFIG)
        # AND the no-AI fallback path below, so the level promise holds
        # even when Groq is unavailable.
        with st.spinner(t("generating")):
            try:
                from src.llm import generate_stock_brief
                brief = generate_stock_brief(
                    data, signals, ticker, vectorstore,
                    lang="English", level=level,
                )
                st.session_state.request_count    += 1
                st.session_state.last_request_time = time.time()
            except Exception:
                st.warning(t("ai_warn"))
                try:
                    from src.llm import _fallback_brief
                    brief = _fallback_brief(data, signals, ticker, level=level)
                except Exception:
                    brief = {
                        "company_name": company_name, "sector": "N/A",
                        "key_metrics": {}, "traffic_light": "YELLOW",
                        "traffic_light_reason": "Could not generate AI brief.",
                        "analyst_summary": "N/A", "valuation_commentary": "N/A",
                        "growth_outlook": "N/A", "risk_flags": [],
                        "financial_health": "N/A", "investor_profile": "N/A",
                        "watch_out_for": "N/A", "news_context": "N/A",
                        "annual_report_insights": None,
                    }

        # ── COMPANY HEADER ────────────────────────────────────────────────────
        price_val = brief["key_metrics"].get("price", "N/A")
        ret_val   = brief["key_metrics"].get("one_year_return", "N/A")
        try:
            ret_f     = float(str(ret_val).replace("%", "").replace("+", ""))
            ret_cls   = "tt-return-up" if ret_f >= 0 else "tt-return-down"
            ret_arrow = "▲" if ret_f >= 0 else "▼"
        except Exception:
            ret_cls   = "tt-return-up"
            ret_arrow = ""

        st.markdown(f"""
        <div class="tt-company-header">
            <div>
                <div class="tt-company-name">{brief.get('company_name') or company_name}</div>
                <div class="tt-company-meta">
                    {brief.get('sector','N/A')} &nbsp;·&nbsp;
                    <span style='color:#ff8c00;font-family:monospace;font-size:11px;'>{ticker}</span>
                </div>
            </div>
            <div>
                <div class="tt-price">{price_val}</div>
                <div class="{ret_cls}">{ret_arrow} {ret_val}
                    &nbsp;<span style='font-weight:400;color:#475569;font-size:12px;'>1Y return</span>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        # ── TRAFFIC LIGHT (Beginner only) ─────────────────────────────────────
        if is_beginner(level):
            tl     = str(brief.get("traffic_light", "")).upper()
            tl_why = brief.get("traffic_light_reason", "")
            if tl == "GREEN":
                st.markdown(f'<div class="tl-green"><div class="tl-dot-green"></div><div class="tl-text">🟢 <b>Looks stable</b> — {tl_why}</div></div>', unsafe_allow_html=True)
            elif tl == "RED":
                st.markdown(f'<div class="tl-red"><div class="tl-dot-red"></div><div class="tl-text">🔴 <b>Concerning signals</b> — {tl_why}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="tl-yellow"><div class="tl-dot-yellow"></div><div class="tl-text">🟡 <b>Mixed signals</b> — {tl_why}</div></div>', unsafe_allow_html=True)

        # ── KEY METRICS ───────────────────────────────────────────────────────
        st.markdown(f"<div class='tt-section-label'>{t('key_metrics')}</div>", unsafe_allow_html=True)
        m  = brief["key_metrics"]
        mc = st.columns(6)
        for col, (label, val) in zip(mc, [
            ("P/E Ratio",      m.get("pe_ratio",      "N/A")),
            ("P/B Ratio",      m.get("pb_ratio",      "N/A")),
            ("Profit Margin",  m.get("profit_margin", "N/A")),
            ("ROE",            m.get("roe",           "N/A")),
            ("Debt / Equity",  m.get("debt_to_equity","N/A")),
            ("Revenue Growth", m.get("revenue_growth","N/A")),
        ]):
            with col:
                st.markdown(f"""
                <div class="tt-metric">
                    <div class="tt-metric-label">{label}</div>
                    <div class="tt-metric-value">{val}</div>
                </div>""", unsafe_allow_html=True)

        # Extended metrics row — count capped per level (Beginner sees the
        # 2 most essential, Expert sees all available). Same data source,
        # fewer items surfaced at lower levels, per the "different depth of
        # content" requirement.
        try:
            from src.utils import format_number, format_price as fp
            ext = []
            if data.get("forward_pe")     not in (None, "N/A"): ext.append(("Forward P/E",   f"{float(data['forward_pe']):.1f}x"))
            if data.get("target_price")   not in (None, "N/A"): ext.append(("Analyst Target", fp(data["target_price"], ticker)))
            if data.get("ev_to_ebitda")   not in (None, "N/A"): ext.append(("EV/EBITDA",     f"{float(data['ev_to_ebitda']):.1f}x"))
            if data.get("beta")           not in (None, "N/A"): ext.append(("Beta",           f"{float(data['beta']):.2f}"))
            if data.get("free_cashflow")  not in (None, "N/A"): ext.append(("Free Cash Flow", format_number(data["free_cashflow"], ticker)))
            if data.get("recommendation") not in (None, "N/A"): ext.append(("Analyst View",   str(data["recommendation"]).upper()))

            cap = MAX_EXTENDED_METRICS.get(level_rank(level), 99)
            ext = ext[:cap]

            if ext:
                ecols = st.columns(len(ext))
                for col, (lbl, v) in zip(ecols, ext):
                    with col:
                        st.markdown(f"""
                        <div class="tt-metric">
                            <div class="tt-metric-label">{lbl}</div>
                            <div class="tt-metric-value" style="font-size:16px;">{v}</div>
                        </div>""", unsafe_allow_html=True)
        except Exception:
            pass

        # ── PRICE CHART ───────────────────────────────────────────────────────
        if price_data and price_data.get("dates"):
            st.markdown(f"<div class='tt-section-label'>{t('price_history')}</div>", unsafe_allow_html=True)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=price_data["dates"], y=price_data["closes"],
                mode="lines", name="Price",
                line=dict(color="#ff8c00", width=2),
                fill="tozeroy", fillcolor="rgba(255,140,0,0.05)",
            ))
            # MA50/MA200 overlays are genuinely useful at every level (they're
            # visual, not jargon-heavy), but we only label them with raw
            # "MA50"/"MA200" for Learner+ — Beginner gets a plain label.
            if history:
                n = len(price_data["dates"])
                ma50_label  = "MA50"  if not is_beginner(level) else "50-day average"
                ma200_label = "MA200" if not is_beginner(level) else "200-day average"
                fig.add_trace(go.Scatter(
                    x=price_data["dates"][-50:],
                    y=[history["ma50"]] * min(50, n),
                    mode="lines", name=ma50_label,
                    line=dict(color="#6366f1", width=1.5, dash="dash"),
                ))
                fig.add_trace(go.Scatter(
                    x=price_data["dates"],
                    y=[history["ma200"]] * n,
                    mode="lines", name=ma200_label,
                    line=dict(color="#ef4444", width=1.5, dash="dash"),
                ))
            fig.update_layout(
                paper_bgcolor="#222836", plot_bgcolor="#222836",
                font=dict(color="#94a3b8", size=11),
                height=340,
                margin=dict(l=12, r=12, t=12, b=12),
                xaxis=dict(gridcolor="#2d3548", showgrid=True, zeroline=False),
                yaxis=dict(gridcolor="#2d3548", showgrid=True, zeroline=False, tickprefix=currency),
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02,
                            xanchor="right", x=1, bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
            )
            st.plotly_chart(fig, use_container_width=True)

            if history:
                h1, h2, h3, h4 = st.columns(4)
                h1.metric("52W High",   f"{currency}{history['high_52w']:,.2f}")
                h2.metric("52W Low",    f"{currency}{history['low_52w']:,.2f}")
                h3.metric("Avg Price",  f"{currency}{history['avg_price']:,.2f}")
                h4.metric("Volatility", f"{history['volatility']}% daily")

        st.markdown("<hr class='tt-divider'>", unsafe_allow_html=True)

        # ── TECHNICAL INDICATORS ─────────────────────────────────────────────
        # Visible at every level (per spec: show but simplify for Beginner),
        # with a level-appropriate plain-language explainer line swapped in
        # above the methodology disclaimer.
        try:
            from src.analytics import technical_snapshot
            tech = technical_snapshot(price_hist)
        except Exception:
            tech = {}

        if tech:
            st.markdown("<div class='tt-section-label'>TECHNICAL INDICATORS</div>", unsafe_allow_html=True)

            st.markdown(
                f"<div class='tt-plain-explain'><span class='tt-plain-explain-icon'>💡</span>"
                f"<span>{plain_explainer('technical', level)}</span></div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div class='tt-disclaimer'><span class='tt-disclaimer-icon'>ℹ️</span>"
                "<span>These describe <b>past</b> price action using standard textbook formulas. "
                "There is no reliable evidence that technical indicators predict future returns — "
                "treat these as context, not signals to act on.</span></div>",
                unsafe_allow_html=True,
            )

            tone_class = {"good": "tt-tag-good", "warn": "tt-tag-warn", "bad": "tt-tag-bad", "neutral": "tt-tag-neutral"}
            cells = []
            if "rsi" in tech:
                r = tech["rsi"]
                rsi_label = r["label"] if not is_beginner(level) else (
                    "Price has risen a lot recently" if r["tone"] == "warn" and r["value"] >= 70 else
                    "Price has fallen a lot recently" if r["tone"] == "warn" else
                    "Nothing extreme either way"
                )
                cells.append(("RSI (14)", f"{r['value']}", rsi_label, tone_class.get(r["tone"], "tt-tag-neutral")))
            if "macd" in tech:
                mc_ = tech["macd"]
                macd_label = mc_["label"] if not is_beginner(level) else (
                    "Momentum leaning positive" if mc_["tone"] == "good" else "Momentum leaning negative"
                )
                cells.append(("MACD", f"{mc_['macd']}", macd_label, tone_class.get(mc_["tone"], "tt-tag-neutral")))
            # Signal line / histogram detail: Learner and above only — for
            # Beginner this is one level of detail too deep per the spec.
            if "macd" in tech and not is_beginner(level):
                mc_ = tech["macd"]
                cells.append(("Signal Line", f"{mc_['signal']}", f"Histogram {mc_['histogram']:+.2f}", "tt-tag-neutral"))
            if "bollinger" in tech:
                bb_ = tech["bollinger"]
                bb_label = bb_["label"] if not is_beginner(level) else (
                    "Price is near the top of its recent range" if bb_["tone"] == "warn" and "upper" in bb_["label"].lower() else
                    "Price is near the bottom of its recent range" if bb_["tone"] == "warn" else
                    "Price is in the middle of its recent range"
                )
                cells.append((f"Price Range ({currency})" if is_beginner(level) else f"Bollinger ({currency})",
                              f"{bb_['lower']:.0f} — {bb_['upper']:.0f}",
                              bb_label, tone_class.get(bb_["tone"], "tt-tag-neutral")))

            grid_html = "<div class='tt-num-grid'>"
            for label, value, tag, tone_cls in cells:
                grid_html += (
                    f"<div class='tt-num-cell'>"
                    f"<div class='tt-num-label'>{label}</div>"
                    f"<div class='tt-num-value'>{value}</div>"
                    f"<div class='tt-num-tag {tone_cls}'>{tag}</div>"
                    f"</div>"
                )
            grid_html += "</div>"
            st.markdown(f"<div class='tt-panel'>{grid_html}</div>", unsafe_allow_html=True)

            st.markdown("<hr class='tt-divider'>", unsafe_allow_html=True)

        # ── PEER / SECTOR COMPARISON ─────────────────────────────────────────
        try:
            from src.analytics import fetch_peer_metrics
            peer_data = fetch_peer_metrics(ticker)
        except Exception:
            peer_data = {}

        if peer_data and peer_data.get("rows"):
            st.markdown("<div class='tt-section-label'>PEER COMPARISON</div>", unsafe_allow_html=True)

            st.markdown(
                f"<div class='tt-plain-explain'><span class='tt-plain-explain-icon'>💡</span>"
                f"<span>{plain_explainer('peers', level)}</span></div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div class='tt-disclaimer'><span class='tt-disclaimer-icon'>ℹ️</span>"
                "<span>Ratios fetched live for this stock and its closest listed peers. "
                "Useful for relative context — a high P/E only means something next to similar companies.</span></div>",
                unsafe_allow_html=True,
            )

            # Column count capped per level: Beginner sees Company/P/E/P/B
            # only; higher levels see the full set including ROE, Margin,
            # Market Cap.
            peer_col_cap = MAX_PEER_COLUMNS.get(level_rank(level), 5)
            all_columns  = ["Company", "P/E", "P/B", "ROE", "Margin", "Mkt Cap"]
            shown_columns = all_columns[:peer_col_cap]

            rows_html = ""
            for row in peer_data["rows"]:
                cls = "tt-subject-row" if row["is_subject"] else ""
                pe_v     = f"{row['pe']}x" if row["pe"] is not None else "—"
                pb_v     = f"{row['pb']}x" if row["pb"] is not None else "—"
                roe_v    = f"{row['roe']}%" if row["roe"] is not None else "—"
                margin_v = f"{row['margin']}%" if row["margin"] is not None else "—"
                mcap_v   = "—"
                if row["mcap"]:
                    mc_val = row["mcap"]
                    if mc_val >= 1e12:
                        mcap_v = f"{mc_val/1e12:.2f}T"
                    elif mc_val >= 1e9:
                        mcap_v = f"{mc_val/1e9:.1f}B"
                    else:
                        mcap_v = f"{mc_val/1e6:.0f}M"

                all_cells = [row['name'], pe_v, pb_v, roe_v, margin_v, mcap_v]
                shown_cells = all_cells[:peer_col_cap]
                cells_html = "".join(f"<td>{c}</td>" for c in shown_cells)
                rows_html += f"<tr class='{cls}'>{cells_html}</tr>"

            header_html = "".join(f"<th>{c}</th>" for c in shown_columns)
            table_html = f"""
            <div class="tt-panel">
                <table class="tt-table">
                    <thead><tr>{header_html}</tr></thead>
                    <tbody>{rows_html}</tbody>
                </table>
            </div>"""
            st.markdown(table_html, unsafe_allow_html=True)

            st.markdown("<hr class='tt-divider'>", unsafe_allow_html=True)

        # ── HISTORICAL FINANCIALS TREND ──────────────────────────────────────
        # Shown for Learner and above only — for a complete Beginner, a
        # multi-year revenue/net-income trend chart adds more confusion than
        # value at this stage (it's the one section gated off entirely,
        # since it's pure historical-statement reading rather than a
        # "current snapshot" like the others).
        if not is_beginner(level):
            try:
                from src.analytics import fetch_historical_financials
                fin_trend = fetch_historical_financials(ticker)
            except Exception:
                fin_trend = {}

            if fin_trend and fin_trend.get("years"):
                st.markdown("<div class='tt-section-label'>HISTORICAL FINANCIALS</div>", unsafe_allow_html=True)
                st.markdown(
                    "<div class='tt-disclaimer'><span class='tt-disclaimer-icon'>ℹ️</span>"
                    "<span>Annual figures as reported, most recent years available. "
                    "Shows trend direction only — not adjusted for one-off items or accounting changes.</span></div>",
                    unsafe_allow_html=True,
                )

                fin_fig = go.Figure()
                years = fin_trend["years"]
                if fin_trend.get("revenue"):
                    fin_fig.add_trace(go.Bar(
                        x=years, y=fin_trend["revenue"], name="Revenue",
                        marker_color="#6366f1", opacity=0.85,
                    ))
                if fin_trend.get("net_income"):
                    fin_fig.add_trace(go.Bar(
                        x=years, y=fin_trend["net_income"], name="Net Income",
                        marker_color="#ff8c00", opacity=0.85,
                    ))
                fin_fig.update_layout(
                    barmode="group",
                    paper_bgcolor="#222836", plot_bgcolor="#222836",
                    font=dict(color="#94a3b8", size=11),
                    height=300,
                    margin=dict(l=12, r=12, t=12, b=12),
                    xaxis=dict(gridcolor="#2d3548", showgrid=False),
                    yaxis=dict(gridcolor="#2d3548", showgrid=True, zeroline=False),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02,
                                xanchor="right", x=1, bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
                )
                st.plotly_chart(fin_fig, use_container_width=True)

                # Net margin trend cells: Intermediate+ only — Learner gets
                # the chart but not this extra derived-metric row.
                if fin_trend.get("net_margin") and not is_learner(level):
                    margin_cells = "".join(
                        f"<div class='tt-num-cell'><div class='tt-num-label'>{y} margin</div>"
                        f"<div class='tt-num-value' style='font-size:14px;'>{m}%</div></div>"
                        for y, m in zip(years, fin_trend["net_margin"]) if m is not None
                    )
                    st.markdown(f"<div class='tt-num-grid'>{margin_cells}</div>", unsafe_allow_html=True)

                st.markdown("<hr class='tt-divider'>", unsafe_allow_html=True)
        else:
            # Beginner notice explaining why this section is condensed —
            # keeps the promise transparent rather than silently vanishing.
            st.markdown(
                "<div class='tt-plain-explain'><span class='tt-plain-explain-icon'>💡</span>"
                "<span>We've kept multi-year financial statement trends out of the Beginner view to "
                "avoid overload — switch to Learner or above (via 'Change Level' up top) to see "
                "revenue and profit history charts.</span></div>",
                unsafe_allow_html=True,
            )

        # ── CORRELATION & VOLATILITY VS INDEX ────────────────────────────────
        try:
            from src.analytics import correlation_volatility
            corr_data = correlation_volatility(ticker, price_hist=price_hist)
        except Exception:
            corr_data = {}

        if corr_data:
            st.markdown("<div class='tt-section-label'>CORRELATION & VOLATILITY</div>", unsafe_allow_html=True)

            st.markdown(
                f"<div class='tt-plain-explain'><span class='tt-plain-explain-icon'>💡</span>"
                f"<span>{plain_explainer('correlation', level)}</span></div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div class='tt-disclaimer'><span class='tt-disclaimer-icon'>ℹ️</span>"
                f"<span>Measures how this stock's daily moves have related to the "
                f"{corr_data['benchmark_name']} over the past year. Past co-movement, not a forecast.</span></div>",
                unsafe_allow_html=True,
            )

            beta_label = "Beta (est.)" if not is_beginner(level) else "Market sensitivity"
            cv_cells = [
                ("Correlation", f"{corr_data['correlation']:.2f}", corr_data["correlation_label"], "tt-tag-neutral"),
                (beta_label, f"{corr_data['beta_estimate']:.2f}" if corr_data.get("beta_estimate") is not None else "—",
                 "vs " + corr_data["benchmark_name"], "tt-tag-neutral"),
                ("Stock Volatility", f"{corr_data['stock_volatility']}%", "annualised", "tt-tag-warn" if corr_data["stock_volatility"] > corr_data["bench_volatility"] else "tt-tag-good"),
            ]
            # Benchmark-volatility comparison cell: Learner+ only — for
            # Beginner, three cells (correlation/beta/own-volatility) is
            # the right amount; a 4th comparison cell is one too many.
            if not is_beginner(level):
                cv_cells.append(
                    (f"{corr_data['benchmark_name']} Volatility", f"{corr_data['bench_volatility']}%", "annualised", "tt-tag-neutral")
                )

            grid2 = "<div class='tt-num-grid'>"
            for label, value, tag, tone_cls in cv_cells:
                grid2 += (
                    f"<div class='tt-num-cell'>"
                    f"<div class='tt-num-label'>{label}</div>"
                    f"<div class='tt-num-value'>{value}</div>"
                    f"<div class='tt-num-tag {tone_cls}'>{tag}</div>"
                    f"</div>"
                )
            grid2 += "</div>"
            st.markdown(f"<div class='tt-panel'>{grid2}</div>", unsafe_allow_html=True)

            st.markdown("<hr class='tt-divider'>", unsafe_allow_html=True)

        # ── SIGNALS ───────────────────────────────────────────────────────────
        # Count capped per level — Beginner sees the most decisive few
        # signals only, Expert sees everything the rule engine produced.
        st.markdown(f"<div class='tt-section-label'>{t('signals')}</div>", unsafe_allow_html=True)

        sig_cap = MAX_SIGNALS_SHOWN.get(level_rank(level), 99)
        # Prioritise WARNING signals first so capping never hides a risk
        # in favour of a neutral/positive one.
        warning_sigs = [s for s in signals if "WARNING" in s]
        other_sigs   = [s for s in signals if "WARNING" not in s]
        shown_signals = (warning_sigs + other_sigs)[:sig_cap]

        sig_html = ""
        for s in shown_signals:
            if "WARNING" in s:
                sig_html += f'<span class="chip-red">⚠ {s}</span>'
            elif any(k in s for k in ("STRONG", "HIGH ROE", "VERY LOW debt",
                                       "ANALYST CONSENSUS: BUY", "Pays dividend", "HIGH dividend")):
                sig_html += f'<span class="chip-green">✓ {s}</span>'
            else:
                sig_html += f'<span class="chip-amber">ℹ {s}</span>'
        if len(signals) > sig_cap:
            sig_html += f'<span class="chip-amber">+{len(signals) - sig_cap} more (raise your level to see all)</span>'
        st.markdown(f'<div class="tt-card" style="padding:16px;">{sig_html}</div>', unsafe_allow_html=True)

        st.markdown("<hr class='tt-divider'>", unsafe_allow_html=True)

        # ── AI BRIEF ──────────────────────────────────────────────────────────
        st.markdown(f"<div class='tt-section-label'>{t('ai_brief')}</div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='tt-disclaimer'><span class='tt-disclaimer-icon'>🤖</span>"
            "<span>Generated by an LLM from the data above. It can summarise fundamentals and "
            "phrase them clearly — it has no special ability to forecast price moves, and isn't "
            "a buy/sell recommendation.</span></div>",
            unsafe_allow_html=True,
        )

        left, right = st.columns(2)
        with left:
            for card_t, key in [
                (t("analyst_summary"), "analyst_summary"),
                (t("valuation"),       "valuation_commentary"),
                (t("growth"),          "growth_outlook"),
            ]:
                st.markdown(f"""
                <div class="tt-card">
                    <div class="tt-card-title">{card_t}</div>
                    <div class="tt-card-text">{brief.get(key,'N/A')}</div>
                </div>""", unsafe_allow_html=True)

            risks      = brief.get("risk_flags", [])
            risks_html = "".join(f'<span class="risk-pill">⚠ {r}</span>' for r in risks) if risks else \
                         '<span style="color:#475569;font-size:13px;">No specific risks flagged.</span>'
            st.markdown(f"""
            <div class="tt-card">
                <div class="tt-card-title">{t('risks')}</div>
                <div>{risks_html}</div>
            </div>""", unsafe_allow_html=True)

        with right:
            for card_t, key in [
                (t("health"),  "financial_health"),
                (t("profile"), "investor_profile"),
                (t("watch"),   "watch_out_for"),
            ]:
                st.markdown(f"""
                <div class="tt-card">
                    <div class="tt-card-title">{card_t}</div>
                    <div class="tt-card-text">{brief.get(key,'N/A')}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<hr class='tt-divider'>", unsafe_allow_html=True)

        # ── NEWS ──────────────────────────────────────────────────────────────
        st.markdown(f"""
        <div class="tt-news-card">
            <div class="tt-card-title">{t('news')}</div>
            <div class="tt-card-text">{brief.get('news_context','No recent news available.')}</div>
        </div>""", unsafe_allow_html=True)

        # ── ANNUAL REPORT ─────────────────────────────────────────────────────
        ari = brief.get("annual_report_insights")
        if vectorstore and ari and "not loaded" not in str(ari).lower():
            st.markdown(f"""
            <div class="tt-rag-card">
                <div class="tt-card-title">{t('annual')}</div>
                <div class="tt-card-text">{ari}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<hr class='tt-divider'>", unsafe_allow_html=True)

        # ── BEGINNER EXPLAINER ────────────────────────────────────────────────
        if is_beginner(level):
            st.markdown(f"<div class='tt-section-label'>{t('beginner_guide')}</div>", unsafe_allow_html=True)
            rows = [
                ("P/E Ratio",      "How much you pay for every ₹1 of company profit. Lower is generally cheaper."),
                ("ROE",            "If you gave ₹100, ROE shows how much profit the company made. 15% = ₹15 on your ₹100."),
                ("Debt/Equity",    "How much the company borrowed vs what it owns. Very high debt can be risky."),
                ("Profit Margin",  "Of every ₹100 in sales, how much is actual profit. Higher is better."),
                ("Revenue Growth", "How much sales grew vs last year. 15% growth means they sold 15% more."),
                ("1Y Return",      "If you had bought one year ago, this is what you would have gained or lost."),
            ]
            rows_html = "".join(
                f'<div style="margin-bottom:12px;">'
                f'<span style="font-size:13px;font-weight:700;color:#ffffff;">{term}</span>'
                f' — <span style="font-size:13px;color:#94a3b8;line-height:1.6;">{defn}</span></div>'
                for term, defn in rows
            )
            st.markdown(f"""
            <div class="tt-beginner">
                <div class="tt-card-title">{t('beginner_title')}</div>
                {rows_html}
            </div>""", unsafe_allow_html=True)

    # ── FOOTER ────────────────────────────────────────────────────────────────
    st.markdown("<hr class='tt-divider'>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='text-align:center;color:#2d3548;font-size:11px;padding:14px;'>{t('footer')}</div>",
        unsafe_allow_html=True,
    )