import os
import re
import streamlit as st
import plotly.graph_objects as go
from dotenv import load_dotenv

load_dotenv()

# ── SECRETS ───────────────────────────────
try:
    for key in ["GROQ_API_KEY", "NEWS_API_KEY"]:
        if key in st.secrets:
            os.environ[key] = st.secrets[key]
except Exception:
    pass

# ── PAGE CONFIG ───────────────────────────
st.set_page_config(
    page_title="StockAI — Smart Equity Research",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── CSS ───────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

* { font-family: 'Inter', sans-serif; box-sizing: border-box; }

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
[data-testid="stSidebar"] {display: none;}
[data-testid="stDecoration"] {display: none;}
.stDeployButton {display: none;}

/* ── BASE ── */
.stApp {
    background-color: #1a1f2e;
    color: #ffffff;
}
section[data-testid="stMain"] > div {
    padding-top: 0px;
}
.block-container {
    padding: 0px 2rem 2rem 2rem !important;
    max-width: 1400px !important;
}

/* ── NAVBAR ── */
.tt-navbar {
    background: #151a27;
    border-bottom: 1px solid #2d3548;
    padding: 0 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 60px;
    margin: 0 -2rem 0 -2rem;
    position: sticky;
    top: 0;
    z-index: 999;
}
.tt-logo {
    font-size: 18px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.5px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.tt-logo-dot {
    width: 8px;
    height: 8px;
    background: #ff8c00;
    border-radius: 50%;
    display: inline-block;
}
.tt-nav-right {
    font-size: 12px;
    color: #64748b;
}

/* ── TICKER TAPE ── */
.tt-ticker {
    background: #151a27;
    border-bottom: 1px solid #2d3548;
    padding: 8px 32px;
    margin: 0 -2rem 0 -2rem;
    overflow: hidden;
    white-space: nowrap;
    font-size: 12px;
    color: #94a3b8;
}
.tt-ticker-item {
    display: inline-block;
    margin-right: 32px;
}
.tt-ticker-name { color: #94a3b8; font-weight: 500; }
.tt-ticker-price { color: #ffffff; font-weight: 600; margin: 0 4px; }
.tt-ticker-up { color: #22c55e; }
.tt-ticker-down { color: #ef4444; }

/* ── HERO ── */
.tt-hero {
    text-align: center;
    padding: 64px 20px 48px;
}
.tt-hero-title {
    font-size: 44px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -1.5px;
    line-height: 1.1;
    margin-bottom: 16px;
}
.tt-hero-accent { color: #ff8c00; }
.tt-hero-sub {
    font-size: 16px;
    color: #64748b;
    margin-bottom: 48px;
    font-weight: 400;
}

/* ── SEARCH ── */
.tt-search-wrap {
    max-width: 560px;
    margin: 0 auto 8px auto;
}
.stTextInput > div > div > input {
    background: #222836 !important;
    border: 1.5px solid #2d3548 !important;
    border-radius: 10px !important;
    color: #ffffff !important;
    font-size: 15px !important;
    padding: 14px 18px !important;
    height: 52px !important;
    transition: border-color 0.2s !important;
}
.stTextInput > div > div > input:focus {
    border-color: #ff8c00 !important;
    box-shadow: 0 0 0 3px rgba(255, 140, 0, 0.1) !important;
}
.stTextInput > div > div > input::placeholder {
    color: #475569 !important;
}

/* ── SUGGESTIONS ── */
.tt-suggestion {
    background: #222836;
    border: 1px solid #2d3548;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 4px 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: border-color 0.15s, background 0.15s;
}
.tt-suggestion:hover {
    border-color: #ff8c00;
    background: #2a2f40;
}
.tt-sug-name { font-size: 14px; color: #e2e8f0; font-weight: 500; }
.tt-sug-ticker {
    font-size: 11px;
    color: #ff8c00;
    font-weight: 600;
    background: rgba(255,140,0,0.1);
    padding: 3px 8px;
    border-radius: 4px;
}

/* ── KNOWLEDGE LEVEL CARDS ── */
.tt-level-card {
    background: #222836;
    border: 1.5px solid #2d3548;
    border-radius: 14px;
    padding: 24px 16px;
    text-align: center;
    transition: all 0.2s ease;
    height: 160px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}
.tt-level-card:hover {
    border-color: #ff8c00;
    background: #252d3e;
    transform: translateY(-2px);
}
.tt-level-icon { font-size: 28px; margin-bottom: 10px; }
.tt-level-title { font-size: 14px; font-weight: 700; color: #ffffff; margin-bottom: 4px; }
.tt-level-desc { font-size: 11px; color: #64748b; line-height: 1.4; }

/* ── SECTION LABEL ── */
.tt-section-label {
    font-size: 11px;
    font-weight: 600;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin: 24px 0 12px 0;
}

/* ── POPULAR PILL BUTTONS ── */
.stButton > button {
    background: #222836 !important;
    color: #94a3b8 !important;
    border: 1px solid #2d3548 !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 8px 16px !important;
    transition: all 0.15s !important;
    width: 100% !important;
}
.stButton > button:hover {
    border-color: #ff8c00 !important;
    color: #ff8c00 !important;
    background: #252d3e !important;
}

/* ── PRIMARY BUTTON ── */
.tt-primary-btn > button {
    background: #ff8c00 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}
.tt-primary-btn > button:hover {
    background: #e67e00 !important;
    color: #ffffff !important;
}

/* ── COMPANY HEADER ── */
.tt-company-header {
    background: #222836;
    border: 1px solid #2d3548;
    border-radius: 14px;
    padding: 28px 32px;
    margin: 16px 0 24px 0;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
}
.tt-company-name {
    font-size: 26px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.5px;
    margin-bottom: 4px;
}
.tt-company-meta { font-size: 13px; color: #64748b; }
.tt-price { font-size: 32px; font-weight: 700; color: #ffffff; }
.tt-return-up { font-size: 15px; color: #22c55e; font-weight: 600; }
.tt-return-down { font-size: 15px; color: #ef4444; font-weight: 600; }

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
    letter-spacing: 0.8px;
    margin-bottom: 6px;
}
.tt-metric-value {
    font-size: 20px;
    font-weight: 700;
    color: #ffffff;
}

/* ── ANALYSIS CARDS ── */
.tt-card {
    background: #222836;
    border: 1px solid #2d3548;
    border-radius: 12px;
    padding: 20px 22px;
    margin: 8px 0;
    height: 100%;
}
.tt-card-title {
    font-size: 10px;
    font-weight: 700;
    color: #ff8c00;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.tt-card-text {
    font-size: 13px;
    color: #94a3b8;
    line-height: 1.75;
}

/* ── RISK TAGS ── */
.tt-risk {
    display: inline-block;
    background: rgba(239,68,68,0.08);
    border: 1px solid rgba(239,68,68,0.25);
    color: #ef4444;
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 12px;
    margin: 3px;
}
.tt-signal-good {
    display: inline-block;
    background: rgba(34,197,94,0.08);
    border: 1px solid rgba(34,197,94,0.25);
    color: #22c55e;
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 12px;
    margin: 3px;
}
.tt-signal-warn {
    display: inline-block;
    background: rgba(255,140,0,0.08);
    border: 1px solid rgba(255,140,0,0.25);
    color: #ff8c00;
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 12px;
    margin: 3px;
}

/* ── NEWS CARD ── */
.tt-news {
    background: #222836;
    border: 1px solid #2d3548;
    border-left: 3px solid #ff8c00;
    border-radius: 12px;
    padding: 20px 22px;
    margin: 8px 0;
}

/* ── RAG CARD ── */
.tt-rag {
    background: #222836;
    border: 1px solid #2d3548;
    border-left: 3px solid #6366f1;
    border-radius: 12px;
    padding: 20px 22px;
    margin: 8px 0;
}

/* ── DIVIDER ── */
.tt-divider {
    border: none;
    border-top: 1px solid #2d3548;
    margin: 28px 0;
}

/* ── BADGE ── */
.tt-badge {
    display: inline-block;
    background: rgba(255,140,0,0.1);
    border: 1px solid rgba(255,140,0,0.3);
    color: #ff8c00;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 600;
}

/* ── GLOSSARY ── */
.tt-glossary-item {
    background: #222836;
    border: 1px solid #2d3548;
    border-radius: 10px;
    padding: 16px 18px;
    margin: 6px 0;
}
.tt-glossary-word {
    font-size: 13px;
    font-weight: 700;
    color: #ff8c00;
    margin-bottom: 4px;
}
.tt-glossary-def {
    font-size: 12px;
    color: #64748b;
    line-height: 1.6;
}

/* ── BEGINNER BOX ── */
.tt-beginner {
    background: linear-gradient(135deg, #1e2a1e 0%, #222836 100%);
    border: 1px solid rgba(34,197,94,0.2);
    border-radius: 12px;
    padding: 20px 22px;
    margin: 8px 0;
}

/* ── PLOTLY OVERRIDE ── */
.js-plotly-plot .plotly .modebar {
    background: transparent !important;
}

/* ── SPINNER ── */
.stSpinner > div { border-top-color: #ff8c00 !important; }

/* ── SELECTBOX ── */
div[data-baseweb="select"] > div {
    background: #222836 !important;
    border-color: #2d3548 !important;
    color: #ffffff !important;
}
</style>
""", unsafe_allow_html=True)

# ── COMPANY DATABASE ──────────────────────
ALL_COMPANIES = {
    "Reliance Industries": "RELIANCE.NS",
    "Tata Consultancy Services": "TCS.NS",
    "Infosys": "INFY.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "State Bank of India": "SBIN.NS",
    "Wipro": "WIPRO.NS",
    "HCL Technologies": "HCLTECH.NS",
    "Bajaj Finance": "BAJFINANCE.NS",
    "Bharti Airtel": "BHARTIARTL.NS",
    "Asian Paints": "ASIANPAINT.NS",
    "Maruti Suzuki": "MARUTI.NS",
    "Tata Motors": "TATAMOTORS.NS",
    "Sun Pharmaceutical": "SUNPHARMA.NS",
    "ITC": "ITC.NS",
    "Kotak Mahindra Bank": "KOTAKBANK.NS",
    "Axis Bank": "AXISBANK.NS",
    "Larsen & Toubro": "LT.NS",
    "Titan Company": "TITAN.NS",
    "Nestle India": "NESTLEIND.NS",
    "Zomato": "ZOMATO.NS",
    "Paytm": "PAYTM.NS",
    "Nykaa": "NYKAA.NS",
    "IRCTC": "IRCTC.NS",
    "Adani Enterprises": "ADANIENT.NS",
    "Adani Ports": "ADANIPORTS.NS",
    "Power Grid": "POWERGRID.NS",
    "NTPC": "NTPC.NS",
    "ONGC": "ONGC.NS",
    "Coal India": "COALINDIA.NS",
    "Tata Steel": "TATASTEEL.NS",
    "JSW Steel": "JSWSTEEL.NS",
    "Hindalco": "HINDALCO.NS",
    "UltraTech Cement": "ULTRACEMCO.NS",
    "Divis Laboratories": "DIVISLAB.NS",
    "Dr Reddys Laboratories": "DRREDDY.NS",
    "Cipla": "CIPLA.NS",
    "Eicher Motors": "EICHERMOT.NS",
    "Hero MotoCorp": "HEROMOTOCO.NS",
    "Bajaj Auto": "BAJAJ-AUTO.NS",
    "Tech Mahindra": "TECHM.NS",
    "Mahindra & Mahindra": "M&M.NS",
    "IndusInd Bank": "INDUSINDBK.NS",
    "Tata Consumer Products": "TATACONSUM.NS",
    "Pidilite Industries": "PIDILITIND.NS",
    "Havells India": "HAVELLS.NS",
    "Voltas": "VOLTAS.NS",
    "Grasim Industries": "GRASIM.NS",
    "Tata Power": "TATAPOWER.BO",
    "Suzlon Energy": "SUZLON.BO",
    "YES Bank": "YESBANK.BO",
    "Vodafone Idea": "IDEA.BO",
    "BHEL": "BHEL.BO",
    "SAIL": "SAIL.BO",
    "Bank of Baroda": "BANKBARODA.BO",
    "PNB": "PNB.BO",
    "IDFC First Bank": "IDFCFIRSTB.BO",
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Amazon": "AMZN",
    "Alphabet (Google)": "GOOGL",
    "Meta (Facebook)": "META",
    "Tesla": "TSLA",
    "NVIDIA": "NVDA",
    "JPMorgan Chase": "JPM",
    "Johnson & Johnson": "JNJ",
    "Visa": "V",
    "Mastercard": "MA",
    "Procter & Gamble": "PG",
    "Walmart": "WMT",
    "Disney": "DIS",
    "Netflix": "NFLX",
    "Goldman Sachs": "GS",
    "BlackRock": "BLK",
    "ExxonMobil": "XOM",
    "Coca Cola": "KO",
    "Nike": "NKE",
    "McDonald's": "MCD",
    "AMD": "AMD",
    "Salesforce": "CRM",
    "Adobe": "ADBE",
    "PayPal": "PYPL",
    "Uber": "UBER",
    "Airbnb": "ABNB",
    "Palantir": "PLTR",
    "Berkshire Hathaway": "BRK-B",
    "Intel": "INTC",
    "Spotify": "SPOT",
    "Snowflake": "SNOW",
}

KNOWLEDGE_LEVELS = {
    "🌱 Beginner": {
        "desc": "New to investing",
        "detail": "Never invested before or just getting started",
    },
    "📈 Learner": {
        "desc": "Know the basics",
        "detail": "Understand what stocks are, still learning",
    },
    "💼 Intermediate": {
        "desc": "Invest regularly",
        "detail": "Comfortable with P/E, ROE and basic analysis",
    },
    "🏦 Expert": {
        "desc": "Experienced investor",
        "detail": "Deep market knowledge, technical analysis",
    },
}

GLOSSARY = {
    "P/E Ratio": "Price to Earnings — how much you pay per ₹1 of profit. Lower generally means cheaper stock.",
    "P/B Ratio": "Price to Book — stock price vs net assets. Below 1 means trading cheaper than assets worth.",
    "EPS": "Earnings Per Share — profit made per single share. Higher is better.",
    "ROE": "Return on Equity — how well company uses your money to make profit. Above 15% is generally good.",
    "Debt to Equity": "How much debt vs shareholder funds. Very high debt means more financial risk.",
    "Profit Margin": "% of revenue that becomes profit. Higher margin means more efficient business.",
    "Revenue Growth": "How much sales grew vs last year. Consistent growth above 10% is healthy.",
    "Market Cap": "Total market value. Large cap above ₹20,000 Crore, mid cap ₹5,000-20,000 Crore.",
    "52 Week High/Low": "Highest and lowest price in the last year. Useful to see where stock currently sits.",
    "Moving Average MA50/MA200": "Average price over 50 or 200 days. Price above MA200 is a positive trend signal.",
    "Volatility": "How much price moves daily. Higher volatility means more risk and potential reward.",
    "Dividend Yield": "Annual dividend as % of stock price. Important for income-seeking investors.",
    "Bull Market": "Rising market — prices going up over a sustained period.",
    "Bear Market": "Falling market — prices going down over a sustained period.",
    "SEBI": "Securities and Exchange Board of India — the regulator of Indian stock markets.",
    "NSE": "National Stock Exchange — India's largest and most active stock exchange.",
    "BSE": "Bombay Stock Exchange — oldest stock exchange in Asia, based in Mumbai.",
    "NASDAQ": "US exchange focused on technology companies. Home to Apple, Microsoft, NVIDIA.",
    "NYSE": "New York Stock Exchange — largest stock exchange in the world by market cap.",
    "FII": "Foreign Institutional Investors — large foreign funds investing in Indian markets.",
    "DII": "Domestic Institutional Investors — Indian mutual funds and insurance companies.",
}

POPULAR = {
    "Reliance Industries": "RELIANCE.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "Infosys": "INFY.NS",
    "Tata Motors": "TATAMOTORS.NS",
    "Tesla": "TSLA",
    "NVIDIA": "NVDA",
    "Apple": "AAPL",
    "Zomato": "ZOMATO.NS",
}

# ── SESSION STATE ─────────────────────────
for key, default in {
    'knowledge_level': None,
    'request_count': 0,
    'selected_ticker': "",
    'current_page': "home",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── RESOURCES ─────────────────────────────
@st.cache_resource
def load_vectorstore():
    if os.path.exists("data/faiss_index"):
        try:
            from src.rag import load_faiss_index
            return load_faiss_index()
        except Exception:
            return None
    return None

@st.cache_data(ttl=300)
def cached_stock_data(ticker):
    from src.data import get_stock_data, clean_data
    return clean_data(get_stock_data(ticker))

def sanitise_ticker(t):
    return re.sub(r'[^A-Z0-9.\-&]', '', t.upper())[:20]

vectorstore = load_vectorstore()

# ── NAVBAR ────────────────────────────────
st.markdown("""
<div class="tt-navbar">
    <div class="tt-logo">
        <span class="tt-logo-dot"></span>
        StockAI
    </div>
    <div class="tt-nav-right">
        AI-Powered Equity Research &nbsp;·&nbsp; Not financial advice
    </div>
</div>
""", unsafe_allow_html=True)

# ── TICKER TAPE ───────────────────────────
st.markdown("""
<div class="tt-ticker">
    <span class="tt-ticker-item">
        <span class="tt-ticker-name">RELIANCE</span>
        <span class="tt-ticker-price">₹1,293</span>
        <span class="tt-ticker-up">▲ 2.38%</span>
    </span>
    <span class="tt-ticker-item">
        <span class="tt-ticker-name">TCS</span>
        <span class="tt-ticker-price">₹3,412</span>
        <span class="tt-ticker-up">▲ 1.24%</span>
    </span>
    <span class="tt-ticker-item">
        <span class="tt-ticker-name">INFY</span>
        <span class="tt-ticker-price">₹1,179</span>
        <span class="tt-ticker-down">▼ 0.45%</span>
    </span>
    <span class="tt-ticker-item">
        <span class="tt-ticker-name">HDFC BANK</span>
        <span class="tt-ticker-price">₹1,820</span>
        <span class="tt-ticker-up">▲ 1.02%</span>
    </span>
    <span class="tt-ticker-item">
        <span class="tt-ticker-name">TESLA</span>
        <span class="tt-ticker-price">$428</span>
        <span class="tt-ticker-up">▲ 3.21%</span>
    </span>
    <span class="tt-ticker-item">
        <span class="tt-ticker-name">NVIDIA</span>
        <span class="tt-ticker-price">$131</span>
        <span class="tt-ticker-up">▲ 4.15%</span>
    </span>
    <span class="tt-ticker-item">
        <span class="tt-ticker-name">NIFTY 50</span>
        <span class="tt-ticker-price">23,622</span>
        <span class="tt-ticker-up">▲ 1.99%</span>
    </span>
    <span class="tt-ticker-item">
        <span class="tt-ticker-name">SENSEX</span>
        <span class="tt-ticker-price">75,527</span>
        <span class="tt-ticker-up">▲ 2.30%</span>
    </span>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# KNOWLEDGE LEVEL PAGE
# ══════════════════════════════════════════
if st.session_state.knowledge_level is None:

    st.markdown("""
    <div class="tt-hero">
        <div class="tt-hero-title">
            Smart research for<br>
            <span class="tt-hero-accent">every investor</span>
        </div>
        <div class="tt-hero-sub">
            AI-powered equity analysis from NSE, BSE, NYSE and 25+ global exchanges
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='text-align:center; font-size:14px; color:#475569; margin-bottom:20px;'>
        Tell us your investing experience so we can tailor the analysis for you
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    for col, (level, info) in zip([c1, c2, c3, c4], KNOWLEDGE_LEVELS.items()):
        with col:
            icon = level.split()[0]
            name = level.split(' ', 1)[1]
            st.markdown(f"""
            <div class="tt-level-card">
                <div class="tt-level-icon">{icon}</div>
                <div class="tt-level-title">{name}</div>
                <div class="tt-level-desc">{info['detail']}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"I'm a {name}", key=f"lvl_{level}", use_container_width=True):
                st.session_state.knowledge_level = level
                st.rerun()

    st.markdown("<div class='tt-divider'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align:center; color:#2d3548; font-size:12px; padding:16px;'>
        Trusted analysis · Live market data · Not financial advice
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════
else:
    # ── TOP BAR ───────────────────────────
    tb1, tb2, tb3 = st.columns([5, 1, 1])
    with tb1:
        st.markdown(f"""
        <div style='padding:12px 0 8px 0;'>
            <span class='tt-badge'>{st.session_state.knowledge_level}</span>
            <span style='color:#475569; font-size:12px; margin-left:10px;'>
                Analysis tailored to your experience level
            </span>
        </div>
        """, unsafe_allow_html=True)
    with tb2:
        if st.button("📚 Glossary", use_container_width=True):
            st.session_state.current_page = (
                "glossary" if st.session_state.current_page != "glossary" else "home"
            )
    with tb3:
        if st.button("↩ Change Level", use_container_width=True):
            st.session_state.knowledge_level = None
            st.session_state.current_page = "home"
            st.rerun()

    st.markdown("<div class='tt-divider'></div>", unsafe_allow_html=True)

    # ── GLOSSARY ──────────────────────────
    if st.session_state.current_page == "glossary":
        st.markdown("""
        <div style='font-size:22px; font-weight:800; color:#fff;
             letter-spacing:-0.5px; margin-bottom:20px;'>
            📚 Financial Terms Glossary
        </div>
        """, unsafe_allow_html=True)

        g_search = st.text_input(
            "",
            placeholder="Search a term — e.g. P/E Ratio, ROE, Market Cap...",
            label_visibility="collapsed"
        )

        for term, definition in GLOSSARY.items():
            if not g_search or g_search.lower() in term.lower() or g_search.lower() in definition.lower():
                st.markdown(f"""
                <div class="tt-glossary-item">
                    <div class="tt-glossary-word">{term}</div>
                    <div class="tt-glossary-def">{definition}</div>
                </div>
                """, unsafe_allow_html=True)

    # ── SEARCH + HOME ─────────────────────
    else:
        # search
        st.markdown("""
        <div style='text-align:center; margin: 32px 0 8px 0;'>
            <div style='font-size:26px; font-weight:800; color:#fff;
                 letter-spacing:-0.5px; margin-bottom:8px;'>
                Search any company
            </div>
            <div style='font-size:14px; color:#475569;'>
                Type a company name to get AI-powered research instantly
            </div>
        </div>
        """, unsafe_allow_html=True)

        _, sc, _ = st.columns([1, 4, 1])
        with sc:
            query = st.text_input(
                "",
                placeholder="🔍  Search — Reliance, Apple, HDFC Bank...",
                label_visibility="collapsed",
                key="main_search"
            )

        # suggestions
        if query and len(query) >= 2:
            matches = {
                n: t for n, t in ALL_COMPANIES.items()
                if query.lower() in n.lower()
            }
            if matches:
                _, mc, _ = st.columns([1, 4, 1])
                with mc:
                    for name, ticker in list(matches.items())[:7]:
                        s1, s2 = st.columns([5, 1])
                        with s1:
                            st.markdown(f"""
                            <div class="tt-suggestion">
                                <span class="tt-sug-name">{name}</span>
                                <span class="tt-sug-ticker">{ticker}</span>
                            </div>
                            """, unsafe_allow_html=True)
                        with s2:
                            if st.button("→", key=f"s_{ticker}"):
                                st.session_state.selected_ticker = ticker
                                st.session_state.current_page = "analysis"
                                st.rerun()
            else:
                _, mc, _ = st.columns([1, 4, 1])
                with mc:
                    st.markdown("""
                    <div style='text-align:center; color:#475569;
                         font-size:13px; padding:12px;'>
                        Company not found — enter ticker manually
                    </div>
                    """, unsafe_allow_html=True)
                    manual = st.text_input(
                        "",
                        placeholder="e.g. RELIANCE.NS or TSLA",
                        label_visibility="collapsed",
                        key="manual_input"
                    )
                    if manual:
                        st.markdown('<div class="tt-primary-btn">', unsafe_allow_html=True)
                        if st.button("Analyse →", use_container_width=True, key="manual_btn"):
                            st.session_state.selected_ticker = sanitise_ticker(manual)
                            st.session_state.current_page = "analysis"
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

        # popular stocks
        if not query:
            st.markdown("<div class='tt-section-label'>POPULAR STOCKS</div>", unsafe_allow_html=True)
            cols = st.columns(4)
            for i, (name, ticker) in enumerate(POPULAR.items()):
                with cols[i % 4]:
                    if st.button(name, key=f"pop_{ticker}", use_container_width=True):
                        st.session_state.selected_ticker = ticker
                        st.session_state.current_page = "analysis"
                        st.rerun()

            st.markdown("<div class='tt-divider'></div>", unsafe_allow_html=True)
            st.markdown("<div class='tt-section-label'>HOW IT WORKS</div>", unsafe_allow_html=True)

            hw1, hw2, hw3, hw4 = st.columns(4)
            for col, icon, title, desc in [
                (hw1, "🔍", "Search", "Type any company name from NSE, BSE or NYSE"),
                (hw2, "📊", "Live Data", "We fetch real-time financial data instantly"),
                (hw3, "🤖", "AI Analysis", "Groq's Llama 3.3 generates a research brief"),
                (hw4, "📋", "Your Report", "Get valuation, health, risks and news context"),
            ]:
                with col:
                    st.markdown(f"""
                    <div class="tt-card" style='text-align:center;'>
                        <div style='font-size:28px; margin-bottom:10px;'>{icon}</div>
                        <div style='font-size:13px; font-weight:700;
                             color:#fff; margin-bottom:6px;'>{title}</div>
                        <div style='font-size:12px; color:#64748b;
                             line-height:1.5;'>{desc}</div>
                    </div>
                    """, unsafe_allow_html=True)

        # ── ANALYSIS ──────────────────────
        if st.session_state.current_page == "analysis" and st.session_state.selected_ticker:

            ticker = st.session_state.selected_ticker

            if st.button("← Back to Search", key="back_btn"):
                st.session_state.current_page = "home"
                st.session_state.selected_ticker = ""
                st.rerun()

            st.markdown("<div class='tt-divider'></div>", unsafe_allow_html=True)

            if st.session_state.request_count >= 10:
                st.error("⚠️ You have reached 10 requests this session. Please refresh the page.")
                st.stop()

            # fetch data
            with st.spinner("Fetching live market data..."):
                try:
                    import yfinance as yf
                    from src.data import analyse_history
                    from src.signals import basic_signal
                    from src.utils import get_currency_symbol

                    data     = cached_stock_data(ticker)
                    signals  = basic_signal(data)
                    history  = analyse_history(ticker)
                    currency = get_currency_symbol(ticker)

                    stock      = yf.Ticker(ticker)
                    price_hist = stock.history(period="1y")
                    price_data = {
                        "dates":  price_hist.index.strftime("%Y-%m-%d").tolist(),
                        "closes": price_hist["Close"].round(2).tolist(),
                    }

                except Exception as e:
                    if "too many requests" in str(e).lower():
                        st.error("⚠️ Market data is busy. Please wait 2 minutes and try again.")
                    else:
                        st.error(f"Error fetching data: {str(e)}")
                    st.stop()

            # generate brief
            with st.spinner("Generating AI research brief..."):
                try:
                    from src.llm import generate_stock_brief
                    brief = generate_stock_brief(
                        data, signals, ticker, vectorstore, "English"
                    )
                    st.session_state.request_count += 1
                except Exception as e:
                    if "rate_limit" in str(e).lower() or "429" in str(e) or "capacity" in str(e).lower():
                        st.error("⚠️ AI service is at capacity. Please try again in 30 minutes.")
                    else:
                        st.error(f"Error: {str(e)}")
                    st.stop()

            # ── COMPANY HEADER ────────────
            price_val = brief['key_metrics'].get('price', 'N/A')
            ret_val   = brief['key_metrics'].get('one_year_return', 'N/A')
            try:
                ret_f = float(str(ret_val).replace('%','').replace('+',''))
                ret_cls = "tt-return-up" if ret_f >= 0 else "tt-return-down"
                ret_arrow = "▲" if ret_f >= 0 else "▼"
            except Exception:
                ret_cls = "tt-return-up"
                ret_arrow = ""

            st.markdown(f"""
            <div class="tt-company-header">
                <div>
                    <div class="tt-company-name">{brief['company_name']}</div>
                    <div class="tt-company-meta">
                        {brief['sector']} &nbsp;·&nbsp;
                        <span style='color:#ff8c00;'>{ticker}</span>
                    </div>
                </div>
                <div style='text-align:right;'>
                    <div class="tt-price">{price_val}</div>
                    <div class="{ret_cls}">{ret_arrow} {ret_val} &nbsp;1Y Return</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── KEY METRICS ───────────────
            st.markdown("<div class='tt-section-label'>KEY METRICS</div>", unsafe_allow_html=True)

            m = brief['key_metrics']
            mc = st.columns(6)
            for col, label, key in zip(mc, [
                "P/E Ratio", "P/B Ratio", "Profit Margin",
                "ROE", "Debt / Equity", "Revenue Growth"
            ], [
                'pe_ratio', 'pb_ratio', 'profit_margin',
                'roe', 'debt_to_equity', 'revenue_growth'
            ]):
                with col:
                    st.markdown(f"""
                    <div class="tt-metric">
                        <div class="tt-metric-label">{label}</div>
                        <div class="tt-metric-value">{m.get(key, 'N/A')}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<div class='tt-divider'></div>", unsafe_allow_html=True)

            # ── PRICE CHART ───────────────
            if price_data and price_data.get("dates"):
                st.markdown("<div class='tt-section-label'>PRICE HISTORY — 1 YEAR</div>", unsafe_allow_html=True)

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=price_data["dates"],
                    y=price_data["closes"],
                    mode="lines",
                    name="Price",
                    line=dict(color="#ff8c00", width=2),
                    fill="tozeroy",
                    fillcolor="rgba(255,140,0,0.04)"
                ))
                if history:
                    fig.add_trace(go.Scatter(
                        x=price_data["dates"][-50:],
                        y=[history['ma50']] * min(50, len(price_data["dates"])),
                        mode="lines",
                        name=f"MA50",
                        line=dict(color="#6366f1", width=1.5, dash="dash")
                    ))
                    fig.add_trace(go.Scatter(
                        x=price_data["dates"],
                        y=[history['ma200']] * len(price_data["dates"]),
                        mode="lines",
                        name=f"MA200",
                        line=dict(color="#ef4444", width=1.5, dash="dash")
                    ))

                fig.update_layout(
                    paper_bgcolor="#222836",
                    plot_bgcolor="#222836",
                    font=dict(color="#94a3b8", size=11),
                    height=340,
                    margin=dict(l=16, r=16, t=16, b=16),
                    xaxis=dict(gridcolor="#2d3548", showgrid=True, zeroline=False),
                    yaxis=dict(
                        gridcolor="#2d3548",
                        showgrid=True,
                        zeroline=False,
                        tickprefix=currency
                    ),
                    hovermode="x unified",
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1,
                        bgcolor="rgba(0,0,0,0)",
                        font=dict(size=11)
                    )
                )
                st.plotly_chart(fig, use_container_width=True)

                if history:
                    hc = st.columns(4)
                    for col, label, val in zip(hc, [
                        "52W High", "52W Low", "Avg Price", "Daily Volatility"
                    ], [
                        f"{currency}{history['high_52w']:,.2f}",
                        f"{currency}{history['low_52w']:,.2f}",
                        f"{currency}{history['avg_price']:,.2f}",
                        f"{history['volatility']}%",
                    ]):
                        with col:
                            st.markdown(f"""
                            <div class="tt-metric">
                                <div class="tt-metric-label">{label}</div>
                                <div class="tt-metric-value">{val}</div>
                            </div>
                            """, unsafe_allow_html=True)

            st.markdown("<div class='tt-divider'></div>", unsafe_allow_html=True)

            # ── SIGNALS ───────────────────
            st.markdown("<div class='tt-section-label'>SIGNALS DETECTED</div>", unsafe_allow_html=True)
            sig_html = ""
            for s in signals:
                if "WARNING" in s:
                    sig_html += f'<span class="tt-risk">⚠ {s}</span> '
                elif "STRONG" in s or "HIGH ROE" in s or "LOW debt" in s.upper():
                    sig_html += f'<span class="tt-signal-good">✓ {s}</span> '
                else:
                    sig_html += f'<span class="tt-signal-warn">● {s}</span> '
            st.markdown(f'<div class="tt-card">{sig_html}</div>', unsafe_allow_html=True)

            st.markdown("<div class='tt-divider'></div>", unsafe_allow_html=True)

            # ── AI BRIEF ──────────────────
            st.markdown("<div class='tt-section-label'>AI RESEARCH BRIEF</div>", unsafe_allow_html=True)

            left, right = st.columns(2)
            with left:
                for title, key in [
                    ("📌 Analyst Summary", "analyst_summary"),
                    ("💰 Valuation", "valuation_commentary"),
                    ("📈 Growth Outlook", "growth_outlook"),
                ]:
                    st.markdown(f"""
                    <div class="tt-card">
                        <div class="tt-card-title">{title}</div>
                        <div class="tt-card-text">{brief.get(key, 'N/A')}</div>
                    </div>
                    """, unsafe_allow_html=True)

                risks_html = "".join([
                    f'<span class="tt-risk">⚠ {r}</span>'
                    for r in brief.get('risk_flags', [])
                ])
                st.markdown(f"""
                <div class="tt-card">
                    <div class="tt-card-title">⚠️ Risk Flags</div>
                    <div>{risks_html}</div>
                </div>
                """, unsafe_allow_html=True)

            with right:
                for title, key in [
                    ("💪 Financial Health", "financial_health"),
                    ("👤 Investor Profile", "investor_profile"),
                    ("🔍 Watch Out For", "watch_out_for"),
                ]:
                    st.markdown(f"""
                    <div class="tt-card">
                        <div class="tt-card-title">{title}</div>
                        <div class="tt-card-text">{brief.get(key, 'N/A')}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<div class='tt-divider'></div>", unsafe_allow_html=True)

            # ── NEWS ──────────────────────
            st.markdown(f"""
            <div class="tt-news">
                <div class="tt-card-title">📰 Latest News & Market Context</div>
                <div class="tt-card-text">
                    {brief.get("news_context", "No recent news available.")}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── ANNUAL REPORT ─────────────
            if vectorstore and brief.get("annual_report_insights"):
                st.markdown(f"""
                <div class="tt-rag">
                    <div class="tt-card-title">📋 Annual Report Insights</div>
                    <div class="tt-card-text">
                        {brief.get("annual_report_insights")}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # ── BEGINNER GUIDE ────────────
            if "Beginner" in st.session_state.knowledge_level:
                st.markdown("<div class='tt-divider'></div>", unsafe_allow_html=True)
                st.markdown("<div class='tt-section-label'>WHAT DO THESE NUMBERS MEAN?</div>", unsafe_allow_html=True)
                st.markdown("""
                <div class="tt-beginner">
                    <div class="tt-card-title">📖 Simple Guide — What You Just Read</div>
                    <div class="tt-card-text">
                        <b style='color:#ffffff;'>P/E Ratio</b> — Think of it as how expensive the stock is.
                        If P/E is 25, you're paying ₹25 for every ₹1 of profit the company makes.
                        Lower is generally better — but compare within the same sector.<br><br>
                        <b style='color:#ffffff;'>ROE (Return on Equity)</b> — If you gave the company ₹100,
                        ROE tells you how much profit they made. 15% ROE means ₹15 profit on your ₹100.
                        Above 15% is generally considered good.<br><br>
                        <b style='color:#ffffff;'>Debt/Equity</b> — How much the company has borrowed
                        vs what it owns. Very high debt can be risky if earnings fall.<br><br>
                        <b style='color:#ffffff;'>Profit Margin</b> — If revenue is ₹100 and margin is 10%,
                        ₹10 is actual profit. Higher is better — it means the business is efficient.<br><br>
                        <b style='color:#ffffff;'>1Y Return</b> — If you had bought this stock one year ago,
                        this is how much money you would have made or lost.
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # ── FOOTER ────────────────────────────
    st.markdown("<div class='tt-divider'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align:center; color:#2d3548; font-size:12px; padding:20px;'>
        StockAI — by Anshika Singh &nbsp;·&nbsp;
        Electronics Engineering · Banasthali Vidyapith &nbsp;·&nbsp;
        Powered by yfinance · Groq · RAG &nbsp;·&nbsp;
        <span style='color:#2d3548;'>Not financial advice</span>
    </div>
    """, unsafe_allow_html=True)