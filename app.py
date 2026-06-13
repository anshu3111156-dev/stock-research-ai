import os
import re
import time
import streamlit as st
import plotly.graph_objects as go
from dotenv import load_dotenv

load_dotenv()

# ── load streamlit secrets for deployment ─
try:
    for key in ["GROQ_API_KEY", "NEWS_API_KEY"]:
        if key in st.secrets:
            os.environ[key] = st.secrets[key]
except Exception:
    pass

# ── PAGE CONFIG ───────────────────────────

st.set_page_config(
    page_title="Stock Research AI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── CUSTOM CSS ────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * { font-family: 'Inter', sans-serif; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}

    .stApp {
        background-color: #0f0f0f;
        color: #ffffff;
    }

    /* ── NAVBAR ── */
    .navbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 32px;
        background: #0f0f0f;
        border-bottom: 1px solid #1e1e1e;
        margin-bottom: 0px;
    }
    .navbar-logo {
        font-size: 20px;
        font-weight: 700;
        color: #00d4aa;
        letter-spacing: -0.5px;
    }
    .navbar-tag {
        font-size: 11px;
        color: #555;
        margin-top: 2px;
    }

    /* ── HERO ── */
    .hero {
        text-align: center;
        padding: 60px 20px 40px 20px;
    }
    .hero-title {
        font-size: 48px;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -1px;
        margin-bottom: 12px;
        line-height: 1.1;
    }
    .hero-title span {
        color: #00d4aa;
    }
    .hero-subtitle {
        font-size: 16px;
        color: #888;
        margin-bottom: 40px;
    }

    /* ── SEARCH ── */
    .search-container {
        max-width: 600px;
        margin: 0 auto;
        position: relative;
    }
    .stTextInput input {
        background: #1a1a1a !important;
        border: 1px solid #2a2a2a !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        font-size: 16px !important;
        padding: 16px 20px !important;
        height: 56px !important;
    }
    .stTextInput input:focus {
        border-color: #00d4aa !important;
        box-shadow: 0 0 0 2px rgba(0, 212, 170, 0.1) !important;
    }
    .stTextInput input::placeholder {
        color: #555 !important;
    }

    /* ── KNOWLEDGE CARDS ── */
    .level-card {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s ease;
        margin: 8px 0;
    }
    .level-card:hover {
        border-color: #00d4aa;
        background: #1e2a28;
    }
    .level-card.selected {
        border-color: #00d4aa;
        background: #0d2420;
    }
    .level-icon {
        font-size: 32px;
        margin-bottom: 8px;
    }
    .level-title {
        font-size: 15px;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 4px;
    }
    .level-desc {
        font-size: 12px;
        color: #666;
    }

    /* ── METRIC CARDS ── */
    .metric-card {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 12px;
        padding: 20px;
        margin: 6px 0;
    }
    .metric-label {
        font-size: 11px;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 24px;
        font-weight: 700;
        color: #ffffff;
    }
    .metric-value.positive { color: #00d4aa; }
    .metric-value.negative { color: #ff4b4b; }

    /* ── SECTION CARDS ── */
    .section-card {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 12px;
        padding: 24px;
        margin: 8px 0;
    }
    .section-title {
        font-size: 12px;
        font-weight: 600;
        color: #00d4aa;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 12px;
    }
    .section-text {
        font-size: 14px;
        color: #cccccc;
        line-height: 1.7;
    }

    /* ── RISK TAGS ── */
    .risk-tag {
        background: rgba(255,75,75,0.1);
        border: 1px solid rgba(255,75,75,0.3);
        border-radius: 6px;
        padding: 6px 12px;
        margin: 4px;
        display: inline-block;
        color: #ff4b4b;
        font-size: 12px;
    }
    .signal-good {
        background: rgba(0,212,170,0.1);
        border: 1px solid rgba(0,212,170,0.3);
        border-radius: 6px;
        padding: 6px 12px;
        margin: 4px;
        display: inline-block;
        color: #00d4aa;
        font-size: 12px;
    }
    .signal-warn {
        background: rgba(255,165,0,0.1);
        border: 1px solid rgba(255,165,0,0.3);
        border-radius: 6px;
        padding: 6px 12px;
        margin: 4px;
        display: inline-block;
        color: #ffa500;
        font-size: 12px;
    }

    /* ── NEWS BOX ── */
    .news-card {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-left: 3px solid #ffa500;
        border-radius: 12px;
        padding: 20px;
        margin: 8px 0;
    }

    /* ── RAG BOX ── */
    .rag-card {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-left: 3px solid #7c3aed;
        border-radius: 12px;
        padding: 20px;
        margin: 8px 0;
    }

    /* ── DIVIDER ── */
    .custom-divider {
        border: none;
        border-top: 1px solid #1e1e1e;
        margin: 24px 0;
    }

    /* ── BUTTONS ── */
    .stButton button {
        background: #00d4aa !important;
        color: #0f0f0f !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        padding: 10px 24px !important;
        transition: all 0.2s ease !important;
    }
    .stButton button:hover {
        background: #00b894 !important;
        transform: translateY(-1px) !important;
    }

    /* ── SUGGESTION LIST ── */
    .suggestion-item {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 8px;
        padding: 10px 16px;
        margin: 4px 0;
        cursor: pointer;
        font-size: 14px;
        color: #cccccc;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .suggestion-ticker {
        color: #00d4aa;
        font-size: 12px;
        font-weight: 600;
    }

    /* ── COMPANY HEADER ── */
    .company-header {
        background: linear-gradient(135deg, #1a1a1a 0%, #1e2a28 100%);
        border: 1px solid #2a2a2a;
        border-radius: 16px;
        padding: 28px;
        margin: 16px 0;
    }
    .company-name {
        font-size: 28px;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 4px;
    }
    .company-meta {
        font-size: 13px;
        color: #666;
    }
    .price-display {
        font-size: 36px;
        font-weight: 700;
        color: #ffffff;
    }
    .price-change-pos {
        font-size: 16px;
        color: #00d4aa;
        font-weight: 600;
    }
    .price-change-neg {
        font-size: 16px;
        color: #ff4b4b;
        font-weight: 600;
    }

    /* ── GLOSSARY BOX ── */
    .glossary-term {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 10px;
        padding: 16px;
        margin: 6px 0;
    }
    .glossary-word {
        font-size: 14px;
        font-weight: 600;
        color: #00d4aa;
        margin-bottom: 4px;
    }
    .glossary-def {
        font-size: 13px;
        color: #999;
        line-height: 1.5;
    }

    /* ── LEVEL BADGE ── */
    .level-badge {
        display: inline-block;
        background: rgba(0,212,170,0.1);
        border: 1px solid rgba(0,212,170,0.3);
        border-radius: 20px;
        padding: 4px 12px;
        font-size: 12px;
        color: #00d4aa;
        font-weight: 600;
    }

    /* ── SPINNER OVERRIDE ── */
    .stSpinner > div {
        border-top-color: #00d4aa !important;
    }

    /* ── SELECTBOX ── */
    .stSelectbox select {
        background: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #2a2a2a !important;
        border-radius: 8px !important;
    }

    /* hide streamlit elements */
    .stDeployButton {display: none;}
    div[data-testid="stDecoration"] {display: none;}
</style>
""", unsafe_allow_html=True)

# ── COMPANY DATABASE ──────────────────────

ALL_COMPANIES = {
    # NSE India
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
    # BSE
    "Tata Power": "TATAPOWER.BO",
    "Suzlon Energy": "SUZLON.BO",
    "YES Bank": "YESBANK.BO",
    "Vodafone Idea": "IDEA.BO",
    "BHEL": "BHEL.BO",
    "SAIL": "SAIL.BO",
    "Bank of Baroda": "BANKBARODA.BO",
    "PNB": "PNB.BO",
    "IDFC First Bank": "IDFCFIRSTB.BO",
    # NYSE / NASDAQ
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
        "style": "Explain every term. Use very simple language. No jargon at all."
    },
    "📈 Learner": {
        "desc": "Know the basics",
        "detail": "Understand what stocks are, learning more",
        "style": "Use simple language. Explain complex terms briefly."
    },
    "💼 Intermediate": {
        "desc": "Invest regularly",
        "detail": "Comfortable with P/E, ROE, basic analysis",
        "style": "Use standard financial language. Focus on insights over definitions."
    },
    "🏦 Expert": {
        "desc": "Professional or experienced",
        "detail": "Deep market knowledge, technical analysis",
        "style": "Use professional financial language. Provide technical depth. Skip basic explanations."
    },
}

GLOSSARY = {
    "P/E Ratio": "Price to Earnings — how much you pay for every ₹1 of profit. Lower = potentially cheaper.",
    "P/B Ratio": "Price to Book — compares price to net assets. Below 1 means trading cheaper than assets.",
    "EPS": "Earnings Per Share — profit per single share. Higher is better.",
    "ROE": "Return on Equity — how well company uses your money to generate profit. Above 15% is good.",
    "Debt to Equity": "How much debt vs shareholder funds. Very high = more financial risk.",
    "Profit Margin": "% of revenue that becomes profit. Higher = more efficient business.",
    "Revenue Growth": "How much sales grew vs last year. Above 10% is healthy.",
    "Market Cap": "Total market value. Large cap >₹20,000 Cr, mid cap ₹5,000-20,000 Cr.",
    "52 Week High": "Highest price in the last year.",
    "52 Week Low": "Lowest price in the last year.",
    "Moving Average": "Average price over a period. MA50 = last 50 days. Price above MA200 = positive trend.",
    "Volatility": "How much price moves daily. Higher = more risk and potential reward.",
    "Dividend Yield": "Annual dividend as % of stock price. Income for investors.",
    "Bull Market": "Rising market where prices are going up.",
    "Bear Market": "Falling market where prices are going down.",
    "SEBI": "Securities and Exchange Board of India — regulates Indian stock markets.",
    "NSE": "National Stock Exchange — India's largest stock exchange.",
    "BSE": "Bombay Stock Exchange — oldest stock exchange in Asia.",
    "NASDAQ": "US tech-heavy stock exchange. Home to Apple, Microsoft, NVIDIA.",
    "NYSE": "New York Stock Exchange — largest stock exchange in the world.",
}

# ── SESSION STATE ─────────────────────────

if 'knowledge_level' not in st.session_state:
    st.session_state.knowledge_level = None
if 'request_count' not in st.session_state:
    st.session_state.request_count = 0
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = ""
if 'current_page' not in st.session_state:
    st.session_state.current_page = "home"

# ── LOAD RESOURCES ────────────────────────

@st.cache_resource
def load_vectorstore():
    FAISS_INDEX_PATH = "data/faiss_index"
    if os.path.exists(FAISS_INDEX_PATH):
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

def sanitise_ticker(ticker):
    return re.sub(r'[^A-Z0-9.\-&]', '', ticker.upper())[:20]

vectorstore = load_vectorstore()

# ── NAVBAR ────────────────────────────────

st.markdown("""
<div class="navbar">
    <div>
        <div class="navbar-logo">📈 StockAI</div>
        <div class="navbar-tag">Powered by Groq · yfinance · RAG</div>
    </div>
    <div style="color:#555; font-size:12px;">Not financial advice</div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# PAGE 1 — KNOWLEDGE LEVEL SELECTOR
# ══════════════════════════════════════════

if st.session_state.knowledge_level is None:

    st.markdown("""
    <div class="hero">
        <div class="hero-title">Research any stock.<br><span>Understand it instantly.</span></div>
        <div class="hero-subtitle">AI-powered equity research for every type of investor</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='text-align:center; color:#888; font-size:14px; margin-bottom:24px;'>First, tell us about your investing experience</div>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    for col, (level, info) in zip(
        [col1, col2, col3, col4],
        KNOWLEDGE_LEVELS.items()
    ):
        with col:
            st.markdown(f"""
            <div class="level-card">
                <div class="level-icon">{level.split()[0]}</div>
                <div class="level-title">{level.split(' ', 1)[1]}</div>
                <div class="level-desc">{info['detail']}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Select", key=f"level_{level}", use_container_width=True):
                st.session_state.knowledge_level = level
                st.rerun()

    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align:center; color:#444; font-size:12px; padding:20px;'>
        Stock Research AI analyses live financial data from NSE, BSE, NYSE and 25+ global exchanges
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════
# PAGE 2 — MAIN APP
# ══════════════════════════════════════════

else:
    level_info = KNOWLEDGE_LEVELS[st.session_state.knowledge_level]

    # ── TOP BAR ───────────────────────────
    top1, top2, top3 = st.columns([6, 2, 2])
    with top1:
        st.markdown(f"""
        <div style='padding:8px 0;'>
            <span class='level-badge'>{st.session_state.knowledge_level}</span>
            <span style='color:#444; font-size:12px; margin-left:8px;'>
                Analysis tailored to your level
            </span>
        </div>
        """, unsafe_allow_html=True)
    with top2:
        if st.button("📚 Glossary", use_container_width=True):
            st.session_state.current_page = (
                "glossary" if st.session_state.current_page != "glossary" else "home"
            )
    with top3:
        if st.button("↩ Change Level", use_container_width=True):
            st.session_state.knowledge_level = None
            st.rerun()

    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

    # ── GLOSSARY PAGE ─────────────────────
    if st.session_state.current_page == "glossary":
        st.markdown("<div style='font-size:22px; font-weight:700; color:#fff; margin-bottom:16px;'>📚 Financial Terms Glossary</div>", unsafe_allow_html=True)
        search_term = st.text_input("Search a term", placeholder="e.g. P/E Ratio, ROE, Market Cap...")
        for term, definition in GLOSSARY.items():
            if not search_term or search_term.lower() in term.lower():
                st.markdown(f"""
                <div class="glossary-term">
                    <div class="glossary-word">{term}</div>
                    <div class="glossary-def">{definition}</div>
                </div>
                """, unsafe_allow_html=True)

    # ── MAIN SEARCH PAGE ──────────────────
    else:
        # search bar
        st.markdown("""
        <div style='text-align:center; font-size:28px; font-weight:700;
             color:#fff; margin:20px 0 8px 0; letter-spacing:-0.5px;'>
            Search any company
        </div>
        <div style='text-align:center; color:#555; font-size:14px; margin-bottom:24px;'>
            Type a company name — suggestions will appear
        </div>
        """, unsafe_allow_html=True)

        search_col = st.columns([1, 4, 1])[1]
        with search_col:
            search_query = st.text_input(
                "",
                placeholder="🔍  Search company — e.g. Reliance, Apple, HDFC...",
                label_visibility="collapsed"
            )

        # autocomplete suggestions
        if search_query and len(search_query) >= 2:
            matches = {
                name: ticker
                for name, ticker in ALL_COMPANIES.items()
                if search_query.lower() in name.lower()
            }

            if matches:
                st.markdown("<div style='max-width:600px; margin:0 auto;'>", unsafe_allow_html=True)
                for name, ticker in list(matches.items())[:6]:
                    col_s1, col_s2 = st.columns([5, 1])
                    with col_s1:
                        st.markdown(f"""
                        <div class="suggestion-item">
                            <span>{name}</span>
                            <span class="suggestion-ticker">{ticker}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_s2:
                        if st.button("Analyse →", key=f"select_{ticker}"):
                            st.session_state.selected_ticker = ticker
                            st.session_state.current_page = "analysis"
                            st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style='text-align:center; color:#555; font-size:13px; margin:8px 0;'>
                    Company not in list — enter ticker manually below
                </div>
                """, unsafe_allow_html=True)
                manual_col = st.columns([1, 4, 1])[1]
                with manual_col:
                    manual = st.text_input(
                        "",
                        placeholder="Enter ticker manually e.g. RELIANCE.NS / TSLA",
                        label_visibility="collapsed",
                        key="manual_ticker"
                    )
                    if manual and st.button("Analyse Manual Ticker →", use_container_width=True):
                        st.session_state.selected_ticker = sanitise_ticker(manual)
                        st.session_state.current_page = "analysis"
                        st.rerun()

        # popular stocks
        if not search_query:
            st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)
            st.markdown("<div style='text-align:center; color:#555; font-size:13px; margin-bottom:16px;'>POPULAR STOCKS</div>", unsafe_allow_html=True)

            popular = {
                "Reliance Industries": "RELIANCE.NS",
                "HDFC Bank": "HDFCBANK.NS",
                "Infosys": "INFY.NS",
                "Tata Motors": "TATAMOTORS.NS",
                "Tesla": "TSLA",
                "NVIDIA": "NVDA",
                "Apple": "AAPL",
                "Zomato": "ZOMATO.NS",
            }

            cols = st.columns(4)
            for i, (name, ticker) in enumerate(popular.items()):
                with cols[i % 4]:
                    if st.button(f"{name}", key=f"pop_{ticker}", use_container_width=True):
                        st.session_state.selected_ticker = ticker
                        st.session_state.current_page = "analysis"
                        st.rerun()

        # ── ANALYSIS PAGE ──────────────────
        if st.session_state.current_page == "analysis" and st.session_state.selected_ticker:

            ticker = st.session_state.selected_ticker

            # back button
            if st.button("← Back to Search"):
                st.session_state.current_page = "home"
                st.session_state.selected_ticker = ""
                st.rerun()

            st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

            # rate limit check
            if st.session_state.request_count >= 10:
                st.error("⚠️ You have reached 10 requests this session. Please refresh the page.")
                st.stop()

            with st.spinner("Fetching live data..."):
                try:
                    import yfinance as yf
                    from src.data import analyse_history
                    from src.signals import basic_signal
                    from src.utils import get_currency_symbol

                    data    = cached_stock_data(ticker)
                    signals = basic_signal(data)
                    history = analyse_history(ticker)
                    currency = get_currency_symbol(ticker)

                    stock      = yf.Ticker(ticker)
                    price_hist = stock.history(period="1y")
                    price_data = {
                        "dates":  price_hist.index.strftime("%Y-%m-%d").tolist(),
                        "closes": price_hist["Close"].round(2).tolist(),
                    }

                except Exception as e:
                    if "too many requests" in str(e).lower():
                        st.error("⚠️ Market data service is busy. Please wait 2 minutes and try again.")
                    else:
                        st.error(f"Error fetching data: {str(e)}")
                    st.stop()

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
                        st.error(f"Error generating brief: {str(e)}")
                    st.stop()

            # ── COMPANY HEADER ────────────────

            price_val = brief['key_metrics'].get('price', 'N/A')
            ret_val   = brief['key_metrics'].get('one_year_return', 'N/A')

            try:
                ret_float = float(str(ret_val).replace('%','').replace('+',''))
                ret_class = "price-change-pos" if ret_float >= 0 else "price-change-neg"
                ret_arrow = "▲" if ret_float >= 0 else "▼"
            except Exception:
                ret_class = "price-change-pos"
                ret_arrow = ""

            st.markdown(f"""
            <div class="company-header">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div>
                        <div class="company-name">{brief['company_name']}</div>
                        <div class="company-meta">
                            {brief['sector']} &nbsp;·&nbsp; {ticker}
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <div class="price-display">{price_val}</div>
                        <div class="{ret_class}">{ret_arrow} {ret_val} (1Y)</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── KEY METRICS ROW ───────────────

            st.markdown("<div style='font-size:11px; color:#555; text-transform:uppercase; letter-spacing:1px; margin:16px 0 8px;'>KEY METRICS</div>", unsafe_allow_html=True)

            m = brief['key_metrics']
            mc1, mc2, mc3, mc4, mc5, mc6 = st.columns(6)

            metrics_display = [
                ("P/E Ratio", m.get('pe_ratio', 'N/A')),
                ("P/B Ratio", m.get('pb_ratio', 'N/A')),
                ("Profit Margin", m.get('profit_margin', 'N/A')),
                ("ROE", m.get('roe', 'N/A')),
                ("Debt / Equity", m.get('debt_to_equity', 'N/A')),
                ("Revenue Growth", m.get('revenue_growth', 'N/A')),
            ]

            for col, (label, value) in zip(
                [mc1, mc2, mc3, mc4, mc5, mc6],
                metrics_display
            ):
                with col:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">{label}</div>
                        <div class="metric-value">{value}</div>
                    </div>
                    """, unsafe_allow_html=True)

            # ── PRICE CHART ───────────────────

            if price_data and price_data.get("dates"):
                st.markdown("<div style='font-size:11px; color:#555; text-transform:uppercase; letter-spacing:1px; margin:20px 0 8px;'>PRICE HISTORY — 1 YEAR</div>", unsafe_allow_html=True)

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=price_data["dates"],
                    y=price_data["closes"],
                    mode="lines",
                    name="Price",
                    line=dict(color="#00d4aa", width=2),
                    fill="tozeroy",
                    fillcolor="rgba(0, 212, 170, 0.04)"
                ))

                if history:
                    fig.add_trace(go.Scatter(
                        x=price_data["dates"][-50:],
                        y=[history['ma50']] * min(50, len(price_data["dates"])),
                        mode="lines",
                        name=f"MA50 {currency}{history['ma50']:,.0f}",
                        line=dict(color="#ffa500", width=1, dash="dash")
                    ))
                    fig.add_trace(go.Scatter(
                        x=price_data["dates"],
                        y=[history['ma200']] * len(price_data["dates"]),
                        mode="lines",
                        name=f"MA200 {currency}{history['ma200']:,.0f}",
                        line=dict(color="#ff4b4b", width=1, dash="dash")
                    ))

                fig.update_layout(
                    paper_bgcolor="#1a1a1a",
                    plot_bgcolor="#1a1a1a",
                    font_color="#888",
                    height=350,
                    margin=dict(l=20, r=20, t=20, b=20),
                    xaxis=dict(
                        gridcolor="#222",
                        showgrid=True,
                        zeroline=False
                    ),
                    yaxis=dict(
                        gridcolor="#222",
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
                        font=dict(size=11),
                        bgcolor="rgba(0,0,0,0)"
                    )
                )
                st.plotly_chart(fig, use_container_width=True)

                if history:
                    hc1, hc2, hc3, hc4 = st.columns(4)
                    hc1.metric("52W High",  f"{currency}{history['high_52w']:,.2f}")
                    hc2.metric("52W Low",   f"{currency}{history['low_52w']:,.2f}")
                    hc3.metric("Avg Price", f"{currency}{history['avg_price']:,.2f}")
                    hc4.metric("Volatility",f"{history['volatility']}% daily")

            st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

            # ── SIGNALS ───────────────────────

            st.markdown("<div style='font-size:11px; color:#555; text-transform:uppercase; letter-spacing:1px; margin:0 0 8px;'>SIGNALS DETECTED</div>", unsafe_allow_html=True)
            signals_html = ""
            for s in signals:
                if "WARNING" in s:
                    signals_html += f'<span class="risk-tag">⚠ {s}</span> '
                elif "STRONG" in s or "HIGH ROE" in s:
                    signals_html += f'<span class="signal-good">✅ {s}</span> '
                else:
                    signals_html += f'<span class="signal-warn">ℹ {s}</span> '
            st.markdown(f'<div class="section-card">{signals_html}</div>', unsafe_allow_html=True)

            st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

            # ── AI ANALYSIS ───────────────────

            st.markdown("<div style='font-size:11px; color:#555; text-transform:uppercase; letter-spacing:1px; margin:0 0 8px;'>AI RESEARCH BRIEF</div>", unsafe_allow_html=True)

            left, right = st.columns(2)

            with left:
                st.markdown(f"""
                <div class="section-card">
                    <div class="section-title">📌 Analyst Summary</div>
                    <div class="section-text">{brief["analyst_summary"]}</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="section-card">
                    <div class="section-title">💰 Valuation</div>
                    <div class="section-text">{brief["valuation_commentary"]}</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="section-card">
                    <div class="section-title">📈 Growth Outlook</div>
                    <div class="section-text">{brief["growth_outlook"]}</div>
                </div>
                """, unsafe_allow_html=True)

                risks_html = "".join([
                    f'<span class="risk-tag">⚠ {r}</span>'
                    for r in brief.get('risk_flags', [])
                ])
                st.markdown(f"""
                <div class="section-card">
                    <div class="section-title">⚠️ Risk Flags</div>
                    <div>{risks_html}</div>
                </div>
                """, unsafe_allow_html=True)

            with right:
                st.markdown(f"""
                <div class="section-card">
                    <div class="section-title">💪 Financial Health</div>
                    <div class="section-text">{brief["financial_health"]}</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="section-card">
                    <div class="section-title">👤 Investor Profile</div>
                    <div class="section-text">{brief["investor_profile"]}</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="section-card">
                    <div class="section-title">🔍 Watch Out For</div>
                    <div class="section-text">{brief["watch_out_for"]}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

            # ── NEWS ──────────────────────────

            st.markdown(f"""
            <div class="news-card">
                <div class="section-title">📰 Latest News & Market Context</div>
                <div class="section-text">{brief.get("news_context", "No recent news available.")}</div>
            </div>
            """, unsafe_allow_html=True)

            # ── ANNUAL REPORT ─────────────────

            if vectorstore and brief.get("annual_report_insights"):
                st.markdown(f"""
                <div class="rag-card">
                    <div class="section-title">📋 Annual Report Insights</div>
                    <div class="section-text">{brief.get("annual_report_insights")}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

            # ── BEGINNER EXPLAINER ────────────

            if "Beginner" in st.session_state.knowledge_level:
                st.markdown("<div style='font-size:11px; color:#555; text-transform:uppercase; letter-spacing:1px; margin:0 0 8px;'>WHAT DO THESE NUMBERS MEAN?</div>", unsafe_allow_html=True)
                st.markdown("""
                <div class="section-card">
                    <div class="section-title">📖 Quick Guide for Beginners</div>
                    <div class="section-text">
                        <b>P/E Ratio</b> — Think of it as how expensive the stock is vs how much money the company makes. Lower is generally better.<br><br>
                        <b>ROE</b> — Imagine you gave the company ₹100. ROE tells you how much profit they made with it. 15% means they made ₹15 profit on your ₹100.<br><br>
                        <b>Debt/Equity</b> — How much the company has borrowed compared to what it owns. Very high debt can be risky.<br><br>
                        <b>Profit Margin</b> — If revenue is ₹100, a 10% margin means ₹10 is actual profit. Higher is better.<br><br>
                        <b>1Y Return</b> — If you had bought this stock a year ago, this is how much you would have gained or lost.
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # ── FOOTER ────────────────────────────
    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align:center; color:#333; font-size:12px; padding:16px;'>
        Stock Research AI — by Anshika Singh &nbsp;·&nbsp;
        Electronics Engineering · Banasthali Vidyapith &nbsp;·&nbsp;
        Not financial advice
    </div>
    """, unsafe_allow_html=True)