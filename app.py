import os
import re
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
    pass  # running locally — keys loaded from .env instead

# ── PAGE CONFIG ───────────────────────────

st.set_page_config(
    page_title="Stock Research AI",
    page_icon="📈",
    layout="wide"
)

# ── CUSTOM CSS ────────────────────────────

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .section-header {
        color: #00d4aa;
        font-size: 15px;
        font-weight: 700;
        margin-top: 24px;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .insight-box {
        background: #1e2130;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        border: 1px solid #2d3250;
        line-height: 1.6;
    }
    .risk-tag {
        background: #ff4b4b22;
        border: 1px solid #ff4b4b;
        border-radius: 5px;
        padding: 5px 10px;
        margin: 3px;
        display: inline-block;
        color: #ff4b4b;
        font-size: 14px;
    }
    .news-box {
        background: #1a1f35;
        border-radius: 8px;
        padding: 15px;
        border-left: 4px solid #ffa500;
        margin: 10px 0;
        line-height: 1.6;
    }
    .rag-box {
        background: #1a1f35;
        border-radius: 8px;
        padding: 15px;
        border-left: 4px solid #7c3aed;
        margin: 10px 0;
        line-height: 1.6;
    }
    .signal-good {
        background: #00d4aa22;
        border: 1px solid #00d4aa;
        border-radius: 5px;
        padding: 5px 10px;
        margin: 3px;
        display: inline-block;
        color: #00d4aa;
        font-size: 13px;
    }
    .signal-warn {
        background: #ffa50022;
        border: 1px solid #ffa500;
        border-radius: 5px;
        padding: 5px 10px;
        margin: 3px;
        display: inline-block;
        color: #ffa500;
        font-size: 13px;
    }
    .signal-bad {
        background: #ff4b4b22;
        border: 1px solid #ff4b4b;
        border-radius: 5px;
        padding: 5px 10px;
        margin: 3px;
        display: inline-block;
        color: #ff4b4b;
        font-size: 13px;
    }
    [data-testid="metric-container"] {
        background: #1e2130;
        border: 1px solid #2d3250;
        border-radius: 10px;
        padding: 15px;
    }
    .stButton button {
        background: #00d4aa;
        color: #0e1117;
        border: none;
        border-radius: 8px;
        font-weight: bold;
    }
    .stButton button:hover {
        background: #00b894;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ── COMPANY LIST ──────────────────────────

NSE_COMPANIES = {
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
}

BSE_COMPANIES = {
    "Tata Power": "TATAPOWER.BO",
    "Suzlon Energy": "SUZLON.BO",
    "YES Bank": "YESBANK.BO",
    "Vodafone Idea": "IDEA.BO",
    "BHEL": "BHEL.BO",
    "SAIL": "SAIL.BO",
    "Bank of Baroda": "BANKBARODA.BO",
    "PNB": "PNB.BO",
    "Union Bank": "UNIONBANK.BO",
    "IDFC First Bank": "IDFCFIRSTB.BO",
}

NYSE_COMPANIES = {
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
    "IBM": "IBM",
    "AMD": "AMD",
    "Salesforce": "CRM",
    "Adobe": "ADBE",
    "PayPal": "PYPL",
    "Uber": "UBER",
    "Airbnb": "ABNB",
    "Palantir": "PLTR",
    "Berkshire Hathaway": "BRK-B",
}

ALL_COMPANIES = {**NSE_COMPANIES, **BSE_COMPANIES, **NYSE_COMPANIES}

# ── SESSION STATE ─────────────────────────

if 'request_count' not in st.session_state:
    st.session_state.request_count = 0

# ── LOAD RAG VECTORSTORE ──────────────────

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

vectorstore = load_vectorstore()

# ── CACHE STOCK DATA ──────────────────────

@st.cache_data(ttl=300)
def cached_stock_data(ticker):
    from src.data import get_stock_data, clean_data
    return clean_data(get_stock_data(ticker))

# ── INPUT SANITISER ───────────────────────

def sanitise_ticker(ticker):
    cleaned = re.sub(r'[^A-Z0-9.\-&]', '', ticker.upper())
    return cleaned[:20]

# ── HEADER ────────────────────────────────

st.title("📈 Stock Research AI")
st.markdown("*AI-powered equity research for retail investors — powered by yfinance, Groq & RAG*")
st.divider()

# ── SIDEBAR ───────────────────────────────

with st.sidebar:

    # language toggle
    lang = st.radio(
        "भाषा / Language",
        ["English", "हिंदी"],
        horizontal=True
    )

    st.divider()
    st.header("🔍 Search Stock")

    # exchange selector
    exchange = st.selectbox(
        "Exchange",
        ["All Exchanges", "NSE India", "BSE India", "NYSE / NASDAQ"]
    )

    # filter company list by exchange
    if exchange == "NSE India":
        company_list = sorted(NSE_COMPANIES.keys())
    elif exchange == "BSE India":
        company_list = sorted(BSE_COMPANIES.keys())
    elif exchange == "NYSE / NASDAQ":
        company_list = sorted(NYSE_COMPANIES.keys())
    else:
        company_list = sorted(ALL_COMPANIES.keys())

    # company dropdown
    selected_company = st.selectbox(
        "Select Company",
        [""] + company_list,
        format_func=lambda x: "Choose a company..." if x == "" else x
    )

    # manual ticker fallback
    manual_ticker = st.text_input(
        "Or enter ticker manually",
        placeholder="e.g. RELIANCE.NS / TSLA"
    ).strip().upper()

    # determine final ticker
    if manual_ticker:
        ticker = sanitise_ticker(manual_ticker)
    elif selected_company:
        ticker = ALL_COMPANIES.get(selected_company, "")
    else:
        ticker = ""

    if ticker:
        st.caption(f"Ticker: `{ticker}`")

    analyse_btn = st.button(
        "🚀 Analyse",
        use_container_width=True,
        type="primary",
        disabled=(ticker == "")
    )

    st.divider()

    if vectorstore:
        st.success("✅ Annual report loaded")
    else:
        st.info("ℹ️ Annual report not loaded")

    st.divider()
    st.caption("Not financial advice")
    st.caption("Built by Anshika Singh")
    st.caption("Electronics Engg · Banasthali Vidyapith")

# ── MAIN CONTENT ──────────────────────────

if analyse_btn and ticker:

    # session rate limit
    if st.session_state.request_count >= 10:
        st.error("⚠️ You have reached 10 requests this session. Please refresh the page to continue.")
        st.stop()

    with st.spinner(f"Fetching data for {ticker}..."):
        try:
            import yfinance as yf
            from src.data import analyse_history
            from src.signals import basic_signal
            from src.llm import generate_stock_brief
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
            if "too many requests" in str(e).lower() or "rate limited" in str(e).lower():
                st.error("⚠️ Market data service is busy. Please wait 2 minutes and try again.")
            else:
                st.error(f"Error fetching data: {str(e)}")
            st.stop()

    with st.spinner("Generating AI research brief..."):
        try:
            brief = generate_stock_brief(
                data, signals, ticker, vectorstore, lang
            )
            st.session_state.request_count += 1

        except Exception as e:
            if "rate_limit" in str(e).lower() or "429" in str(e) or "capacity" in str(e).lower():
                st.error("⚠️ AI service is at capacity. Please try again in 30 minutes.")
            else:
                st.error(f"Error generating brief: {str(e)}")
            st.stop()

    # ── COMPANY HEADER ────────────────────

    col1, col2 = st.columns([3, 1])
    with col1:
        st.header(f"🏢 {brief['company_name']}")
        st.markdown(f"**Sector:** {brief['sector']} &nbsp;|&nbsp; **Exchange:** {exchange} &nbsp;|&nbsp; **Ticker:** `{ticker}`")
    with col2:
        price = brief['key_metrics'].get('price', 'N/A')
        ret   = brief['key_metrics'].get('one_year_return', 'N/A')
        st.metric("Current Price (Live)", price, ret)

    st.divider()

    # ── KEY METRICS ───────────────────────

    st.markdown('<div class="section-header">📊 Key Metrics</div>', unsafe_allow_html=True)
    m = brief['key_metrics']
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("P/E Ratio",      m.get('pe_ratio', 'N/A'))
    c2.metric("P/B Ratio",      m.get('pb_ratio', 'N/A'))
    c3.metric("Profit Margin",  m.get('profit_margin', 'N/A'))
    c4.metric("ROE",            m.get('roe', 'N/A'))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Debt / Equity",   m.get('debt_to_equity', 'N/A'))
    c6.metric("Revenue Growth",  m.get('revenue_growth', 'N/A'))
    c7.metric("1Y Return",       m.get('one_year_return', 'N/A'))
    c8.metric("EPS",             m.get('price', 'N/A'))

    st.divider()

    # ── SIGNALS DETECTED ──────────────────

    st.markdown('<div class="section-header">🔔 Signals Detected</div>', unsafe_allow_html=True)
    signals_html = ""
    for s in signals:
        if "WARNING" in s:
            signals_html += f'<span class="signal-bad">⚠ {s}</span> '
        elif "STRONG" in s or "HIGH ROE" in s or "LOW debt" in s.upper():
            signals_html += f'<span class="signal-good">✅ {s}</span> '
        else:
            signals_html += f'<span class="signal-warn">ℹ {s}</span> '
    st.markdown(f'<div class="insight-box">{signals_html}</div>', unsafe_allow_html=True)

    st.divider()

    # ── PRICE CHART ───────────────────────

    if price_data and price_data.get("dates"):
        st.markdown('<div class="section-header">📉 Price History — 1 Year</div>', unsafe_allow_html=True)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=price_data["dates"],
            y=price_data["closes"],
            mode="lines",
            name="Price",
            line=dict(color="#00d4aa", width=2),
            fill="tozeroy",
            fillcolor="rgba(0, 212, 170, 0.05)"
        ))

        if history:
            fig.add_hline(
                y=history['ma50'],
                line_color="#ffa500",
                line_dash="dash",
                annotation_text=f"MA50 {currency}{history['ma50']:,.0f}",
                annotation_font_color="#ffa500"
            )
            fig.add_hline(
                y=history['ma200'],
                line_color="#ff4b4b",
                line_dash="dash",
                annotation_text=f"MA200 {currency}{history['ma200']:,.0f}",
                annotation_font_color="#ff4b4b"
            )

        fig.update_layout(
            paper_bgcolor="#0e1117",
            plot_bgcolor="#1e2130",
            font_color="white",
            height=400,
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis=dict(gridcolor="#2d3250", showgrid=True),
            yaxis=dict(gridcolor="#2d3250", showgrid=True, tickprefix=currency),
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)

        if history:
            h1, h2, h3, h4 = st.columns(4)
            h1.metric("52W High",   f"{currency}{history['high_52w']:,.2f}")
            h2.metric("52W Low",    f"{currency}{history['low_52w']:,.2f}")
            h3.metric("Avg Price",  f"{currency}{history['avg_price']:,.2f}")
            h4.metric("Volatility", f"{history['volatility']}% daily")

    st.divider()

    # ── TWO COLUMN LAYOUT ─────────────────

    left, right = st.columns(2)

    with left:
        st.markdown('<div class="section-header">📌 Analyst Summary</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="insight-box">{brief["analyst_summary"]}</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-header">💰 Valuation</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="insight-box">{brief["valuation_commentary"]}</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-header">📈 Growth Outlook</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="insight-box">{brief["growth_outlook"]}</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-header">⚠️ Risk Flags</div>', unsafe_allow_html=True)
        risks_html = "".join([f'<span class="risk-tag">⚠ {r}</span>' for r in brief.get('risk_flags', [])])
        st.markdown(f'<div class="insight-box">{risks_html}</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-header">💪 Financial Health</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="insight-box">{brief["financial_health"]}</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-header">👤 Investor Profile</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="insight-box">{brief["investor_profile"]}</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-header">🔍 Watch Out For</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="insight-box">{brief["watch_out_for"]}</div>', unsafe_allow_html=True)

    st.divider()

    # ── NEWS CONTEXT ──────────────────────

    st.markdown('<div class="section-header">📰 Latest News & Market Context</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="news-box">{brief.get("news_context", "No recent news available.")}</div>', unsafe_allow_html=True)

    # ── ANNUAL REPORT INSIGHTS ────────────

    if vectorstore and brief.get("annual_report_insights"):
        st.markdown('<div class="section-header">📋 Annual Report Insights</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="rag-box">{brief.get("annual_report_insights", "Not available.")}</div>', unsafe_allow_html=True)

    st.divider()

elif analyse_btn and not ticker:
    st.warning("Please select a company or enter a ticker first.")

else:
    # ── LANDING STATE ─────────────────────
    st.markdown("### How to use")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**Step 1**\nSelect exchange and company from the sidebar dropdown")
    with col2:
        st.info("**Step 2**\nChoose English or Hindi and click Analyse")
    with col3:
        st.info("**Step 3**\nRead the full AI research brief with chart, news and signals")

    st.divider()

    st.markdown("### Popular stocks to try")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**🇮🇳 NSE India**")
        st.code("Reliance Industries\nHDFC Bank\nInfosys\nTata Motors")
    with c2:
        st.markdown("**🇺🇸 NYSE / NASDAQ**")
        st.code("Apple\nTesla\nNVIDIA\nMicrosoft")
    with c3:
        st.markdown("**📊 BSE India**")
        st.code("YES Bank\nTata Power\nBHEL\nSUZLON")

    st.divider()
    st.markdown("*Built by Anshika Singh — Electronics Engineering, Banasthali Vidyapith*")

# ── FOOTER ────────────────────────────────

st.divider()
st.markdown(
    "<center><small>Stock Research AI — by Anshika Singh | "
    "Powered by yfinance + Groq (Llama 3.3) | "
    "Not financial advice</small></center>",
    unsafe_allow_html=True
)