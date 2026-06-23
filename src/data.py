import yfinance as yf
import requests
import os

# ── EXTENDED NAME MAP FOR NEWS SEARCH ─────────────────────
# Used by get_company_news to query NewsAPI with a clean company name
# instead of a raw ticker symbol. Falls back to ticker prefix if missing.
NEWS_NAME_MAP = {
    "RELIANCE.NS": "Reliance Industries", "TCS.NS": "Tata Consultancy Services",
    "INFY.NS": "Infosys", "HDFCBANK.NS": "HDFC Bank", "ICICIBANK.NS": "ICICI Bank",
    "SBIN.NS": "State Bank of India", "WIPRO.NS": "Wipro", "HCLTECH.NS": "HCL Technologies",
    "BAJFINANCE.NS": "Bajaj Finance", "BHARTIARTL.NS": "Bharti Airtel",
    "ASIANPAINT.NS": "Asian Paints", "MARUTI.NS": "Maruti Suzuki", "TATAMOTORS.NS": "Tata Motors",
    "SUNPHARMA.NS": "Sun Pharma", "ITC.NS": "ITC", "KOTAKBANK.NS": "Kotak Mahindra Bank",
    "AXISBANK.NS": "Axis Bank", "LT.NS": "Larsen Toubro", "TITAN.NS": "Titan Company",
    "NESTLEIND.NS": "Nestle India", "ZOMATO.NS": "Zomato", "PAYTM.NS": "Paytm",
    "NYKAA.NS": "Nykaa", "IRCTC.NS": "IRCTC", "ADANIENT.NS": "Adani Enterprises",
    "ADANIPORTS.NS": "Adani Ports", "POWERGRID.NS": "Power Grid", "NTPC.NS": "NTPC",
    "ONGC.NS": "ONGC", "COALINDIA.NS": "Coal India", "TATASTEEL.NS": "Tata Steel",
    "JSWSTEEL.NS": "JSW Steel", "HINDALCO.NS": "Hindalco", "ULTRACEMCO.NS": "UltraTech Cement",
    "DIVISLAB.NS": "Divi's Laboratories", "DRREDDY.NS": "Dr Reddy's", "CIPLA.NS": "Cipla",
    "EICHERMOT.NS": "Eicher Motors", "HEROMOTOCO.NS": "Hero MotoCorp", "BAJAJ-AUTO.NS": "Bajaj Auto",
    "TECHM.NS": "Tech Mahindra", "M&M.NS": "Mahindra Mahindra", "INDUSINDBK.NS": "IndusInd Bank",
    "TATACONSUM.NS": "Tata Consumer Products", "PIDILITIND.NS": "Pidilite Industries",
    "HAVELLS.NS": "Havells India", "VOLTAS.NS": "Voltas", "GRASIM.NS": "Grasim Industries",
    "TATAPOWER.BO": "Tata Power", "SUZLON.BO": "Suzlon Energy", "YESBANK.BO": "Yes Bank",
    "IDEA.BO": "Vodafone Idea", "BHEL.BO": "BHEL", "SAIL.BO": "SAIL",
    "BANKBARODA.BO": "Bank of Baroda", "PNB.BO": "Punjab National Bank",
    "IDFCFIRSTB.BO": "IDFC First Bank",
    "AAPL": "Apple", "MSFT": "Microsoft", "AMZN": "Amazon", "GOOGL": "Google",
    "META": "Meta", "TSLA": "Tesla", "NVDA": "Nvidia", "JPM": "JPMorgan Chase",
    "JNJ": "Johnson Johnson", "V": "Visa", "MA": "Mastercard", "PG": "Procter Gamble",
    "WMT": "Walmart", "DIS": "Disney", "NFLX": "Netflix", "GS": "Goldman Sachs",
    "BLK": "BlackRock", "XOM": "ExxonMobil", "KO": "Coca Cola", "NKE": "Nike",
    "MCD": "McDonald's", "AMD": "AMD", "CRM": "Salesforce", "ADBE": "Adobe",
    "PYPL": "PayPal", "UBER": "Uber", "ABNB": "Airbnb", "PLTR": "Palantir",
    "BRK-B": "Berkshire Hathaway", "INTC": "Intel", "SPOT": "Spotify", "SNOW": "Snowflake",
}


def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    info  = stock.info or {}

    try:
        price = stock.fast_info.get("lastPrice")
    except Exception:
        price = None
    if price is None:
        price = info.get("currentPrice") or info.get("regularMarketPrice")

    # Fetch 1y history once and reuse for both price_change_1y and downstream chart/analytics
    try:
        history = stock.history(period="1y")
    except Exception:
        history = None

    change_pct = None
    if history is not None and not history.empty and len(history) >= 2:
        try:
            change_pct = ((history['Close'].iloc[-1] - history['Close'].iloc[0]) / history['Close'].iloc[0]) * 100
        except Exception:
            change_pct = None

    return {
        "name":            info.get("longName") or info.get("shortName"),
        "price":           price,
        "pe":              info.get("trailingPE"),
        "forward_pe":      info.get("forwardPE"),
        "ev_to_ebitda":    info.get("enterpriseToEbitda"),
        "eps":             info.get("trailingEps"),
        "revenue":         info.get("totalRevenue"),
        "market_cap":      info.get("marketCap"),
        "free_cashflow":   info.get("freeCashflow"),
        "beta":            info.get("beta"),
        "target_price":    info.get("targetMeanPrice"),
        "recommendation":  info.get("recommendationKey"),
        "price_change_1y": round(change_pct, 2) if change_pct is not None else None,
        "profit_margin":   info.get("profitMargins"),
        "roe":             info.get("returnOnEquity"),
        "debt_to_equity":  info.get("debtToEquity"),
        "pb_ratio":        info.get("priceToBook"),
        "dividend_yield":  info.get("dividendYield"),
        "earnings_growth": info.get("earningsGrowth"),
        "revenue_growth":  info.get("revenueGrowth"),
        "sector":          info.get("sector"),
        "industry":        info.get("industry"),
        "summary":         info.get("longBusinessSummary"),
        "_price_hist":     history,   # internal — reused by app.py to avoid a second yfinance call
    }


def clean_data(data):
    """N/A-fill everything except the internal _price_hist DataFrame, which must stay as-is."""
    cleaned = {}
    for k, v in data.items():
        if k == "_price_hist":
            cleaned[k] = v
            continue
        cleaned[k] = "N/A" if v is None else v
    return cleaned


def analyse_history(ticker, price_hist=None):
    """
    Computes 1-year price stats and moving averages.
    Accepts an optional pre-fetched price_hist DataFrame (from get_stock_data)
    to avoid hitting yfinance twice for the same ticker in one request.
    """
    try:
        history = price_hist
        if history is None or history.empty:
            history = yf.Ticker(ticker).history(period="1y")
        if history is None or history.empty:
            return None

        history = history.copy()
        history['Daily_Return'] = history['Close'].pct_change()
        history['MA50']  = history['Close'].rolling(window=50).mean()
        history['MA200'] = history['Close'].rolling(window=200).mean()

        latest_price = history['Close'].iloc[-1]
        latest_ma50  = history['MA50'].iloc[-1]
        latest_ma200 = history['MA200'].iloc[-1]

        # MA50/200 can be NaN if history is shorter than the window
        ma50_val  = float(latest_ma50)  if latest_ma50  == latest_ma50  else float(latest_price)
        ma200_val = float(latest_ma200) if latest_ma200 == latest_ma200 else float(latest_price)

        return {
            "high_52w":     round(history['Close'].max(), 2),
            "low_52w":      round(history['Close'].min(), 2),
            "avg_price":    round(history['Close'].mean(), 2),
            "avg_volume":   round(history['Volume'].mean(), 0),
            "volatility":   round(history['Daily_Return'].std() * 100, 2) if history['Daily_Return'].std() == history['Daily_Return'].std() else 0.0,
            "ma50":         round(ma50_val, 2),
            "ma200":        round(ma200_val, 2),
            "ma50_signal":  "ABOVE" if latest_price > ma50_val  else "BELOW",
            "ma200_signal": "ABOVE" if latest_price > ma200_val else "BELOW",
        }
    except Exception:
        return None


def get_company_news(ticker: str) -> list[str]:
    company = NEWS_NAME_MAP.get(ticker.upper(), ticker.split(".")[0])
    api_key = os.getenv("NEWS_API_KEY")

    if not api_key:
        return ["Could not fetch news."]

    url = (
        f"https://newsapi.org/v2/everything"
        f"?q={company}&language=en&pageSize=5&sortBy=publishedAt"
        f"&apiKey={api_key}"
    )

    try:
        response = requests.get(url, timeout=5)
        articles = response.json().get("articles", [])
        headlines = [a["title"] for a in articles[:5]]
        return headlines if headlines else ["Could not fetch news."]
    except Exception:
        return ["Could not fetch news."]