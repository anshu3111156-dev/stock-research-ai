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
    page_title="StockAI — Equity Research",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── i18n ──────────────────────────────────────────────────────────────────────
STRINGS = {
    "en": {
        "hero_title":     "Smart research for",
        "hero_highlight": "every investor.",
        "hero_sub":       "AI-powered equity analysis from NSE, BSE, NYSE and 25+ global exchanges",
        "level_prompt":   "Tell us your investing experience so we can tailor the analysis for you",
        "search_title":   "Search any company",
        "search_sub":     "Type a company name or select from the exchange list below",
        "exchange_label": "Exchange",
        "company_label":  "Company",
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
        "ai_busy":        "⚠️ AI service is at capacity. Please try again in 30 minutes.",
        "fetch_error":    "⚠️ Could not fetch data for {name}. Check the ticker and try again.",
        "ai_warn":        "⚠️ AI brief unavailable. Showing data view.",
    },
    "hi": {
        "hero_title":     "हर निवेशक के लिए",
        "hero_highlight": "स्मार्ट रिसर्च।",
        "hero_sub":       "NSE, BSE, NYSE और 25+ ग्लोबल एक्सचेंज से AI-संचालित इक्विटी विश्लेषण",
        "level_prompt":   "अपना निवेश अनुभव बताएं ताकि हम विश्लेषण आपके अनुसार बना सकें",
        "search_title":   "कोई भी कंपनी खोजें",
        "search_sub":     "कंपनी का नाम टाइप करें या नीचे से एक्सचेंज चुनें",
        "exchange_label": "एक्सचेंज",
        "company_label":  "कंपनी",
        "analyse_btn":    "विश्लेषण",
        "back_btn":       "← खोज पर वापस",
        "change_level":   "↩ स्तर बदलें",
        "glossary_btn":   "📚 शब्दावली",
        "glossary_title": "📚 वित्तीय शब्दावली",
        "glossary_search":"शब्द खोजें...",
        "popular":        "लोकप्रिय स्टॉक्स",
        "how_it_works":   "यह कैसे काम करता है",
        "key_metrics":    "मुख्य आंकड़े",
        "price_history":  "मूल्य इतिहास — 1 वर्ष",
        "signals":        "संकेत",
        "ai_brief":       "AI रिसर्च सारांश",
        "analyst_summary":"📌 विश्लेषक सारांश",
        "valuation":      "💰 मूल्यांकन",
        "growth":         "📈 विकास दृष्टिकोण",
        "risks":          "⚠️ जोखिम",
        "health":         "💪 वित्तीय स्वास्थ्य",
        "profile":        "👤 निवेशक प्रोफ़ाइल",
        "watch":          "🔍 ध्यान रखें",
        "news":           "📰 ताज़ा समाचार",
        "annual":         "📋 वार्षिक रिपोर्ट",
        "beginner_guide": "इन संख्याओं का मतलब क्या है?",
        "beginner_title": "📖 सरल गाइड",
        "not_advice":     "वित्तीय सलाह नहीं",
        "fetching":       "लाइव डेटा प्राप्त हो रहा है...",
        "generating":     "AI रिसर्च तैयार हो रही है...",
        "footer":         "StockAI · Anshika Singh द्वारा · वित्तीय सलाह नहीं",
        "tailored":       "आपके स्तर के अनुसार विश्लेषण",
        "nav_tag":        "Groq · yfinance · RAG",
        "level_i_am":     "मैं हूँ",
        "or_ticker":      "या टिकर मैन्युअल दर्ज करें (जैसे RELIANCE.NS / TSLA)",
        "invalid_ticker": "अमान्य टिकर। केवल अक्षर, संख्याएं, बिंदु और हाइफन उपयोग करें।",
        "not_found":      "कंपनी नहीं मिली — नीचे टिकर दर्ज करें",
        "session_limit":  "सत्र सीमा समाप्त। कृपया पेज रिफ्रेश करें।",
        "rate_wait":      "अगली रिक्वेस्ट के लिए {secs}s प्रतीक्षा करें।",
        "busy":           "⚠️ मार्केट डेटा व्यस्त है। 2 मिनट बाद पुनः प्रयास करें।",
        "ai_busy":        "⚠️ AI सेवा व्यस्त है। 30 मिनट बाद पुनः प्रयास करें।",
        "fetch_error":    "⚠️ {name} का डेटा नहीं मिला। टिकर जांचें।",
        "ai_warn":        "⚠️ AI सारांश उपलब्ध नहीं। डेटा दृश्य दिखाया जा रहा है।",
    },
}

def t(key, **kwargs):
    lang = st.session_state.get("lang", "en")
    s = STRINGS.get(lang, STRINGS["en"]).get(key, key)
    return s.format(**kwargs) if kwargs else s

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Noto+Sans+Devanagari:wght@400;500;600;700&display=swap');

*, *::before, *::after {
    box-sizing: border-box;
    font-family: 'Inter', 'Noto Sans Devanagari', -apple-system, sans-serif;
}

/* ── RESET STREAMLIT ── */
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
    position: sticky;
    top: 0;
    z-index: 999;
}
.tt-logo {
    font-size: 18px;
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
    font-weight: 400;
}

/* ── LEVEL CARDS ── */
.tt-level-card {
    background: #222836;
    border: 1.5px solid #2d3548;
    border-radius: 14px;
    padding: 26px 16px;
    text-align: center;
    transition: all 0.18s ease;
    cursor: pointer;
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
    display: flex;
    align-items: center;
    gap: 6px;
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
.tt-metric-value {
    font-size: 20px;
    font-weight: 700;
    color: #ffffff;
}

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
.tt-company-name {
    font-size: 26px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.5px;
    margin-bottom: 4px;
}
.tt-company-meta { font-size: 12px; color: #64748b; }
.tt-price { font-size: 32px; font-weight: 700; color: #ffffff; text-align: right; }
.tt-return-up   { font-size: 14px; font-weight: 600; color: #22c55e; }
.tt-return-down { font-size: 14px; font-weight: 600; color: #ef4444; }

/* ── TRAFFIC LIGHT (Beginner) ── */
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
.tl-dot-green  { width: 13px; height: 13px; border-radius: 50%; background: #22c55e; flex-shrink: 0; }
.tl-dot-yellow { width: 13px; height: 13px; border-radius: 50%; background: #ff8c00; flex-shrink: 0; }
.tl-dot-red    { width: 13px; height: 13px; border-radius: 50%; background: #ef4444; flex-shrink: 0; }
.tl-text { font-size: 13px; color: #e2e8f0; font-weight: 500; }

/* ── SIGNAL CHIPS ── */
.chip-red {
    display: inline-flex; align-items: center;
    background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.25);
    color: #ef4444; border-radius: 20px;
    padding: 5px 12px; font-size: 12px; font-weight: 500; margin: 3px; gap: 5px;
}
.chip-green {
    display: inline-flex; align-items: center;
    background: rgba(34,197,94,0.08); border: 1px solid rgba(34,197,94,0.25);
    color: #22c55e; border-radius: 20px;
    padding: 5px 12px; font-size: 12px; font-weight: 500; margin: 3px; gap: 5px;
}
.chip-amber {
    display: inline-flex; align-items: center;
    background: rgba(255,140,0,0.08); border: 1px solid rgba(255,140,0,0.25);
    color: #ff8c00; border-radius: 20px;
    padding: 5px 12px; font-size: 12px; font-weight: 500; margin: 3px; gap: 5px;
}

/* ── RISK TAGS ── */
.risk-pill {
    display: inline-block;
    background: rgba(239,68,68,0.08);
    border: 1px solid rgba(239,68,68,0.25);
    color: #ef4444;
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 12px;
    margin: 4px;
    line-height: 1.5;
}

/* ── NEWS / RAG CARDS ── */
.tt-news-card {
    background: #222836;
    border: 1px solid #2d3548;
    border-left: 3px solid #ff8c00;
    border-radius: 12px;
    padding: 20px 22px;
    margin: 6px 0;
}
.tt-rag-card {
    background: #222836;
    border: 1px solid #2d3548;
    border-left: 3px solid #6366f1;
    border-radius: 12px;
    padding: 20px 22px;
    margin: 6px 0;
}

/* ── BEGINNER BOX ── */
.tt-beginner {
    background: linear-gradient(135deg, #1c2a1e 0%, #222836 100%);
    border: 1px solid rgba(34,197,94,0.2);
    border-radius: 12px;
    padding: 20px 22px;
    margin: 6px 0;
}

/* ── SUGGESTION ITEMS ── */
.tt-suggestion {
    background: #222836;
    border: 1px solid #2d3548;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 4px 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: border-color 0.15s;
}
.tt-suggestion:hover { border-color: #ff8c00; background: #252d3e; }
.tt-sug-name   { font-size: 14px; color: #e2e8f0; font-weight: 500; }
.tt-sug-ticker {
    font-size: 11px; color: #ff8c00; font-weight: 600;
    background: rgba(255,140,0,0.1); padding: 3px 8px; border-radius: 4px;
}

/* ── BADGE ── */
.tt-badge {
    display: inline-flex; align-items: center;
    background: rgba(255,140,0,0.1);
    border: 1px solid rgba(255,140,0,0.3);
    color: #ff8c00; border-radius: 20px;
    padding: 4px 12px; font-size: 12px; font-weight: 600; gap: 5px;
}

/* ── GLOSSARY ── */
.tt-gloss-card {
    background: #222836;
    border: 1px solid #2d3548;
    border-radius: 10px;
    padding: 16px 18px;
    margin: 6px 0;
}
.tt-gloss-word { font-size: 13px; font-weight: 700; color: #ff8c00; margin-bottom: 4px; }
.tt-gloss-def  { font-size: 12px; color: #64748b; line-height: 1.6; }

/* ── DIVIDER ── */
.tt-divider { border: none; border-top: 1px solid #2d3548; margin: 24px 0; }

/* ── INPUTS ── */
.stTextInput input {
    background: #222836 !important;
    border: 1.5px solid #2d3548 !important;
    border-radius: 10px !important;
    color: #ffffff !important;
    font-size: 14px !important;
    padding: 13px 18px !important;
}
.stTextInput input:focus {
    border-color: #ff8c00 !important;
    box-shadow: 0 0 0 3px rgba(255,140,0,0.08) !important;
}
.stTextInput input::placeholder { color: #475569 !important; }

/* Selectbox */
div[data-baseweb="select"] > div {
    background: #222836 !important;
    border: 1.5px solid #2d3548 !important;
    border-radius: 10px !important;
    color: #ffffff !important;
}
div[data-baseweb="popover"] { background: #222836 !important; border: 1px solid #2d3548 !important; }

/* ── BUTTONS (global default) ── */
.stButton button {
    background: #222836 !important;
    color: #94a3b8 !important;
    border: 1px solid #2d3548 !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    transition: all 0.15s !important;
}
.stButton button:hover {
    border-color: #ff8c00 !important;
    color: #ff8c00 !important;
    background: #252d3e !important;
}

/* Primary CTA */
div[data-testid="column"] .stButton.primary-btn button,
.primary-cta button {
    background: #ff8c00 !important;
    color: #ffffff !important;
    border: none !important;
    font-weight: 700 !important;
}
.primary-cta button:hover {
    background: #e67e00 !important;
    color: #ffffff !important;
}

/* Spinner */
.stSpinner > div { border-top-color: #ff8c00 !important; }

/* Plotly chart */
.js-plotly-plot { border-radius: 12px; overflow: hidden; }

/* Streamlit metric labels */
[data-testid="stMetricValue"] { color: #ffffff !important; font-size: 18px !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"] { color: #475569 !important; font-size: 11px !important; }
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
    "Promoter Holding": "% held by founders/promoters. Higher = management aligned with shareholders.",
    "NPA":              "Non-Performing Asset — loans where repayment has stopped. High NPA = bad sign for banks.",
    "EBITDA":           "Earnings before interest, tax, depreciation and amortisation. Measures operating profit.",
    "PEG Ratio":        "P/E ratio divided by earnings growth. Below 1 = potentially undervalued for its growth rate.",
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

# ── SESSION STATE ─────────────────────────────────────────────────────────────
for k, v in {
    "knowledge_level":       None,
    "lang":                  "en",
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

COOLDOWN    = 20
MAX_REQ     = 15

def rate_ok() -> bool:
    elapsed = time.time() - st.session_state.last_request_time
    if elapsed < COOLDOWN:
        st.warning(t("rate_wait", secs=int(COOLDOWN - elapsed)))
        return False
    if st.session_state.request_count >= MAX_REQ:
        st.error(t("session_limit"))
        return False
    return True

vectorstore = load_vectorstore()

# ── NAVBAR ────────────────────────────────────────────────────────────────────
lang_btn = "🇮🇳 हिंदी" if st.session_state.lang == "en" else "🇬🇧 English"
nb1, nb2 = st.columns([9, 1])
with nb1:
    st.markdown(f"""
    <div class="tt-navbar">
        <div class="tt-logo">
            <span class="tt-logo-dot"></span>
            StockAI
        </div>
        <div class="tt-nav-right">
            <span class="tt-nav-tag">{t('nav_tag')}</span>
            <span class="tt-not-advice">{t('not_advice')}</span>
        </div>
    </div>""", unsafe_allow_html=True)
with nb2:
    st.markdown("<div style='margin-top:10px;'>", unsafe_allow_html=True)
    if st.button(lang_btn, key="lang_toggle"):
        st.session_state.lang = "hi" if st.session_state.lang == "en" else "en"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ── TICKER STRIP — live auto-refreshing ───────────────────────────────────────
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=60_000, limit=None, key="ticker_refresh")
except ImportError:
    pass

try:
    from src.ticker_strip import fetch_strip_data, build_strip_html

    @st.cache_data(ttl=55, show_spinner=False)
    def get_strip_data():
        return fetch_strip_data()

    strip_stocks = get_strip_data()
    st.markdown(build_strip_html(strip_stocks), unsafe_allow_html=True)
except Exception:
    # Fallback static strip if module not available
    st.markdown("""
    <div style="background:#151a27;border-bottom:1px solid #2d3548;padding:8px 32px;
                margin:0 -2rem 0 -2rem;overflow:hidden;white-space:nowrap;
                font-size:12px;color:#94a3b8;">
        <span style="margin-right:32px;">
            <span style="font-weight:500;">RELIANCE</span>
            <span style="color:#ffffff;font-weight:600;margin:0 4px;">₹—</span>
        </span>
        <span style="margin-right:32px;">
            <span style="font-weight:500;">TCS</span>
            <span style="color:#ffffff;font-weight:600;margin:0 4px;">₹—</span>
        </span>
        <span style="margin-right:32px;">
            <span style="font-weight:500;">NIFTY 50</span>
            <span style="color:#ffffff;font-weight:600;margin:0 4px;">—</span>
        </span>
        <span style="margin-right:32px;">
            <span style="font-weight:500;">SENSEX</span>
            <span style="color:#ffffff;font-weight:600;margin:0 4px;">—</span>
        </span>
        <span style="margin-right:32px;">
            <span style="font-weight:500;">NVIDIA</span>
            <span style="color:#ffffff;font-weight:600;margin:0 4px;">$—</span>
        </span>
    </div>""", unsafe_allow_html=True)

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
            # ── Live search box
            query = st.text_input(
                "", placeholder="🔍  Search — Reliance, Apple, HDFC Bank, Tesla...",
                label_visibility="collapsed", key="main_search",
            )

            # ── Exchange + company selector
            st.markdown(
                "<div style='text-align:center;color:#475569;font-size:12px;"
                "margin:14px 0 6px;'>— or browse by exchange —</div>",
                unsafe_allow_html=True,
            )
            exc_options = ["— Select exchange —"] + list(COMPANIES_BY_EXCHANGE.keys())
            sel_exc = st.selectbox("", exc_options, label_visibility="collapsed", key="exc_sel")

            if sel_exc != "— Select exchange —":
                cos       = COMPANIES_BY_EXCHANGE[sel_exc]
                co_opts   = ["— Choose a company —"] + list(cos.keys())
                sel_co    = st.selectbox("", co_opts, label_visibility="collapsed", key="co_sel")
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
                # Manual ticker entry (shown only when no exchange selected)
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

        # ── Live search suggestions
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

        # ── Popular stocks
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

            # ── How it works
            st.markdown("<hr class='tt-divider'>", unsafe_allow_html=True)
            st.markdown(f"<div class='tt-section-label'>{t('how_it_works')}</div>", unsafe_allow_html=True)
            hw1, hw2, hw3, hw4 = st.columns(4)
            for col, icon, title, desc in [
                (hw1, "🔍", "Search", "Type any company name from NSE, BSE or NYSE"),
                (hw2, "📊", "Live Data", "Real-time financial data fetched instantly via yfinance"),
                (hw3, "🤖", "AI Analysis", "Groq's Llama 3 generates a personalised research brief"),
                (hw4, "📋", "Your Report", "Valuation, financial health, risks and news — in one view"),
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

        # Generate AI brief
        with st.spinner(t("generating")):
            try:
                from src.llm import generate_stock_brief
                lang_str = "हिंदी" if st.session_state.lang == "hi" else "English"
                brief    = generate_stock_brief(
                    data, signals, ticker, vectorstore,
                    lang=lang_str, level=level,
                )
                st.session_state.request_count    += 1
                st.session_state.last_request_time = time.time()
            except Exception:
                st.warning(t("ai_warn"))
                try:
                    from src.llm import _fallback_brief
                    brief = _fallback_brief(data, signals, ticker)
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
        if "Beginner" in level or "🌱" in level:
            tl     = str(brief.get("traffic_light", "")).upper()
            tl_why = brief.get("traffic_light_reason", "")
            if tl == "GREEN":
                st.markdown(f'<div class="tl-green"><div class="tl-dot-green"></div>'
                            f'<div class="tl-text">🟢 <b>Looks stable</b> — {tl_why}</div></div>',
                            unsafe_allow_html=True)
            elif tl == "RED":
                st.markdown(f'<div class="tl-red"><div class="tl-dot-red"></div>'
                            f'<div class="tl-text">🔴 <b>Concerning signals</b> — {tl_why}</div></div>',
                            unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="tl-yellow"><div class="tl-dot-yellow"></div>'
                            f'<div class="tl-text">🟡 <b>Mixed signals</b> — {tl_why}</div></div>',
                            unsafe_allow_html=True)

        # ── KEY METRICS ───────────────────────────────────────────────────────
        st.markdown(f"<div class='tt-section-label'>{t('key_metrics')}</div>", unsafe_allow_html=True)
        m = brief["key_metrics"]
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

        # Extended metrics row (Expert/Intermediate)
        try:
            from src.utils import format_number, format_price as fp
            ext = []
            if data.get("forward_pe")     not in (None, "N/A"): ext.append(("Forward P/E",   f"{float(data['forward_pe']):.1f}x"))
            if data.get("ev_to_ebitda")   not in (None, "N/A"): ext.append(("EV/EBITDA",     f"{float(data['ev_to_ebitda']):.1f}x"))
            if data.get("free_cashflow")  not in (None, "N/A"): ext.append(("Free Cash Flow", format_number(data["free_cashflow"], ticker)))
            if data.get("beta")           not in (None, "N/A"): ext.append(("Beta",           f"{float(data['beta']):.2f}"))
            if data.get("target_price")   not in (None, "N/A"): ext.append(("Analyst Target", fp(data["target_price"], ticker)))
            if data.get("recommendation") not in (None, "N/A"): ext.append(("Analyst View",   str(data["recommendation"]).upper()))
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
            if history:
                n = len(price_data["dates"])
                fig.add_trace(go.Scatter(
                    x=price_data["dates"][-50:],
                    y=[history["ma50"]] * min(50, n),
                    mode="lines", name="MA50",
                    line=dict(color="#6366f1", width=1.5, dash="dash"),
                ))
                fig.add_trace(go.Scatter(
                    x=price_data["dates"],
                    y=[history["ma200"]] * n,
                    mode="lines", name="MA200",
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
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1, bgcolor="rgba(0,0,0,0)",
                    font=dict(size=11),
                ),
            )
            st.plotly_chart(fig, use_container_width=True)

            if history:
                h1, h2, h3, h4 = st.columns(4)
                h1.metric("52W High",   f"{currency}{history['high_52w']:,.2f}")
                h2.metric("52W Low",    f"{currency}{history['low_52w']:,.2f}")
                h3.metric("Avg Price",  f"{currency}{history['avg_price']:,.2f}")
                h4.metric("Volatility", f"{history['volatility']}% daily")

        st.markdown("<hr class='tt-divider'>", unsafe_allow_html=True)

        # ── SIGNALS ───────────────────────────────────────────────────────────
        st.markdown(f"<div class='tt-section-label'>{t('signals')}</div>", unsafe_allow_html=True)
        sig_html = ""
        for s in signals:
            if "WARNING" in s:
                sig_html += f'<span class="chip-red">⚠ {s}</span>'
            elif any(k in s for k in ("STRONG", "HIGH ROE", "VERY LOW debt", "ANALYST CONSENSUS: BUY",
                                       "Pays dividend", "HIGH dividend")):
                sig_html += f'<span class="chip-green">✓ {s}</span>'
            else:
                sig_html += f'<span class="chip-amber">ℹ {s}</span>'
        st.markdown(f'<div class="tt-card" style="padding:16px;">{sig_html}</div>', unsafe_allow_html=True)

        st.markdown("<hr class='tt-divider'>", unsafe_allow_html=True)

        # ── AI BRIEF ──────────────────────────────────────────────────────────
        st.markdown(f"<div class='tt-section-label'>{t('ai_brief')}</div>", unsafe_allow_html=True)

        left, right = st.columns(2)
        with left:
            st.markdown(f"""
            <div class="tt-card">
                <div class="tt-card-title">{t('analyst_summary')}</div>
                <div class="tt-card-text">{brief.get('analyst_summary','N/A')}</div>
            </div>""", unsafe_allow_html=True)

            st.markdown(f"""
            <div class="tt-card">
                <div class="tt-card-title">{t('valuation')}</div>
                <div class="tt-card-text">{brief.get('valuation_commentary','N/A')}</div>
            </div>""", unsafe_allow_html=True)

            st.markdown(f"""
            <div class="tt-card">
                <div class="tt-card-title">{t('growth')}</div>
                <div class="tt-card-text">{brief.get('growth_outlook','N/A')}</div>
            </div>""", unsafe_allow_html=True)

            risks     = brief.get("risk_flags", [])
            risks_html = "".join(f'<span class="risk-pill">⚠ {r}</span>' for r in risks) if risks else \
                         '<span style="color:#475569;font-size:13px;">No specific risks flagged.</span>'
            st.markdown(f"""
            <div class="tt-card">
                <div class="tt-card-title">{t('risks')}</div>
                <div>{risks_html}</div>
            </div>""", unsafe_allow_html=True)

        with right:
            st.markdown(f"""
            <div class="tt-card">
                <div class="tt-card-title">{t('health')}</div>
                <div class="tt-card-text">{brief.get('financial_health','N/A')}</div>
            </div>""", unsafe_allow_html=True)

            st.markdown(f"""
            <div class="tt-card">
                <div class="tt-card-title">{t('profile')}</div>
                <div class="tt-card-text">{brief.get('investor_profile','N/A')}</div>
            </div>""", unsafe_allow_html=True)

            st.markdown(f"""
            <div class="tt-card">
                <div class="tt-card-title">{t('watch')}</div>
                <div class="tt-card-text">{brief.get('watch_out_for','N/A')}</div>
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
        if "Beginner" in level or "🌱" in level:
            st.markdown(f"<div class='tt-section-label'>{t('beginner_guide')}</div>", unsafe_allow_html=True)
            if st.session_state.lang == "hi":
                rows = [
                    ("P/E Ratio",      "कंपनी की कमाई के लिए आप कितना पैसा दे रहे हैं। कम = संभवतः सस्ता।"),
                    ("ROE",            "आपके ₹100 पर कंपनी ने कितना मुनाफा कमाया। 15% मतलब ₹100 पर ₹15 मुनाफा।"),
                    ("Debt/Equity",    "कंपनी ने कितना कर्ज लिया है। ज्यादा कर्ज = ज्यादा जोखिम।"),
                    ("Profit Margin",  "₹100 की बिक्री में से असल मुनाफा कितना। ज्यादा = बेहतर।"),
                    ("Revenue Growth", "पिछले साल की तुलना में बिक्री कितनी बढ़ी।"),
                    ("1Y Return",      "अगर आपने 1 साल पहले खरीदा होता तो कितना फायदा/नुकसान होता।"),
                ]
            else:
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