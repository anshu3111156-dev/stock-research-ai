import streamlit as st
import requests
import plotly.graph_objects as go

API_URL = "http://127.0.0.1:8000"

# ── PAGE CONFIG ───────────────────────────

st.set_page_config(
    page_title="Stock Research AI",
    page_icon="📈",
    layout="wide"
)

# ── CUSTOM CSS ────────────────────────────

st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .metric-card {
        background: #1e2130;
        border-radius: 10px;
        padding: 15px;
        margin: 5px;
        border-left: 4px solid #00d4aa;
    }
    .section-header {
        color: #00d4aa;
        font-size: 18px;
        font-weight: bold;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    .insight-box {
        background: #1e2130;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        border: 1px solid #2d3250;
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
    }
    .rag-box {
        background: #1a1f35;
        border-radius: 8px;
        padding: 15px;
        border-left: 4px solid #7c3aed;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ── HEADER ────────────────────────────────

st.title("📈 Stock Research AI")
st.markdown("*AI-powered equity research for Indian retail investors — powered by yfinance, Groq & RAG*")
st.divider()

# ── SIDEBAR ───────────────────────────────

with st.sidebar:
    st.header("🔍 Search Stock")
    ticker = st.text_input(
        "Enter NSE Ticker",
        placeholder="e.g. RELIANCE.NS",
        help="Enter any NSE stock ticker ending with .NS"
    ).strip().upper()

    analyse_btn = st.button("🚀 Analyse Stock", use_container_width=True, type="primary")

    st.divider()
    st.header("💬 Ask Annual Report")
    question = st.text_area(
        "Your question",
        placeholder="e.g. What is the green energy strategy?",
        height=100
    )
    ask_btn = st.button("🔎 Ask", use_container_width=True)

    st.divider()
    st.markdown("**Supported formats:**")
    st.markdown("RELIANCE.NS · TCS.NS · INFY.NS")
    st.markdown("HDFCBANK.NS · WIPRO.NS · SBIN.NS")

# ── MAIN CONTENT ──────────────────────────

if analyse_btn and ticker:
    with st.spinner(f"Fetching data and generating AI brief for {ticker}..."):
        try:
            response = requests.post(
                f"{API_URL}/research",
                json={"ticker": ticker},
                timeout=120
            )

            if response.status_code == 200:
                result     = response.json()
                brief      = result["brief"]
                history    = result["history"]
                signals    = result["signals"]
                price_data = result.get("price_data", {})

                # ── COMPANY HEADER ────────────────────

                col1, col2 = st.columns([3, 1])
                with col1:
                    st.header(f"🏢 {brief['company_name']}")
                    st.markdown(f"**Sector:** {brief['sector']}")
                with col2:
                    price = brief['key_metrics'].get('price', 'N/A')
                    ret   = brief['key_metrics'].get('one_year_return', 'N/A')
                    st.metric("Current Price", price, ret)

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
                c5.metric("Debt/Equity",    m.get('debt_to_equity', 'N/A'))
                c6.metric("Revenue Growth", m.get('revenue_growth', 'N/A'))
                c7.metric("1Y Return",      m.get('one_year_return', 'N/A'))
                c8.metric("Signals",        signals[0] if signals else "N/A")

                st.divider()

                # ── PRICE CHART ───────────────────────

                if price_data and price_data.get("dates"):
                    st.markdown('<div class="section-header">📉 Price History — 1 Year</div>', unsafe_allow_html=True)

                    fig = go.Figure()

                    # Real price line
                    fig.add_trace(go.Scatter(
                        x=price_data["dates"],
                        y=price_data["closes"],
                        mode="lines",
                        name="Price",
                        line=dict(color="#00d4aa", width=2),
                        fill="tozeroy",
                        fillcolor="rgba(0, 212, 170, 0.05)"
                    ))

                    # MA lines
                    if history:
                        fig.add_hline(
                            y=history['ma50'],
                            line_color="#ffa500",
                            line_dash="dash",
                            annotation_text=f"MA50 ₹{history['ma50']:,.0f}",
                            annotation_font_color="#ffa500"
                        )
                        fig.add_hline(
                            y=history['ma200'],
                            line_color="#ff4b4b",
                            line_dash="dash",
                            annotation_text=f"MA200 ₹{history['ma200']:,.0f}",
                            annotation_font_color="#ff4b4b"
                        )

                    fig.update_layout(
                        paper_bgcolor="#0e1117",
                        plot_bgcolor="#1e2130",
                        font_color="white",
                        height=400,
                        margin=dict(l=20, r=20, t=20, b=20),
                        xaxis=dict(gridcolor="#2d3250", showgrid=True),
                        yaxis=dict(gridcolor="#2d3250", showgrid=True, tickprefix="₹"),
                        legend=dict(bgcolor="#1e2130"),
                        hovermode="x unified"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # 52W stats below chart
                    if history:
                        h1, h2, h3, h4 = st.columns(4)
                        h1.metric("52W High",   f"₹{history['high_52w']:,.2f}")
                        h2.metric("52W Low",    f"₹{history['low_52w']:,.2f}")
                        h3.metric("Avg Price",  f"₹{history['avg_price']:,.2f}")
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

                st.markdown('<div class="section-header">📰 News Context</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="news-box">{brief.get("news_context", "No recent news available.")}</div>', unsafe_allow_html=True)

                # ── ANNUAL REPORT INSIGHTS ────────────

                st.markdown('<div class="section-header">📋 Annual Report Insights</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="rag-box">{brief.get("annual_report_insights", "Annual report not available for this stock.")}</div>', unsafe_allow_html=True)

            else:
                st.error(f"API Error: {response.json().get('detail', 'Unknown error')}")

        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to API. Make sure the FastAPI server is running: `python -m uvicorn api:app --reload`")
        except Exception as e:
            st.error(f"Error: {str(e)}")

elif analyse_btn and not ticker:
    st.warning("Please enter a stock ticker first.")

# ── ASK ANNUAL REPORT ─────────────────────

if ask_btn and question:
    with st.spinner("Searching annual report..."):
        try:
            response = requests.post(
                f"{API_URL}/ask",
                json={"question": question},
                timeout=60
            )
            if response.status_code == 200:
                answer = response.json().get("answer", "No answer found.")
                st.markdown('<div class="section-header">💬 Answer from Annual Report</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="rag-box">{answer}</div>', unsafe_allow_html=True)
            else:
                st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
        except Exception as e:
            st.error(f"Error: {str(e)}")

elif ask_btn and not question:
    st.warning("Please enter a question first.")

# ── FOOTER ────────────────────────────────

st.divider()
st.markdown(
    "<center><small>Stock Research AI — by Anshika Singh | "
    "Powered by yfinance + Groq (Llama 3.3) + RAG | "
    "Not financial advice</small></center>",
    unsafe_allow_html=True
)