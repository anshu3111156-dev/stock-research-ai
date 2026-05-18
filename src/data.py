import yfinance as yf
import requests
import os

def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    info  = stock.info

    try:
        price = stock.fast_info.get("lastPrice")
    except Exception:
        price = None

    try:
        history = stock.history(period="1y")
        if len(history) >= 2:
            change_pct = ((history['Close'].iloc[-1] - history['Close'].iloc[0]) / history['Close'].iloc[0]) * 100
        else:
            change_pct = None
    except Exception:
        change_pct = None

    return {
        "name":            info.get("longName"),
        "price":           price,
        "pe":              info.get("trailingPE"),
        "eps":             info.get("trailingEps"),
        "revenue":         info.get("totalRevenue"),
        "market_cap":      info.get("marketCap"),
        "price_change_1y": round(change_pct, 2) if change_pct else None,
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
    }


def clean_data(data):
    return {k: ("N/A" if v is None else v) for k, v in data.items()}


def analyse_history(ticker):
    try:
        history = yf.Ticker(ticker).history(period="1y")
        if history.empty:
            return None

        history['Daily_Return'] = history['Close'].pct_change()
        history['MA50']  = history['Close'].rolling(window=50).mean()
        history['MA200'] = history['Close'].rolling(window=200).mean()

        latest_price = history['Close'].iloc[-1]
        latest_ma50  = history['MA50'].iloc[-1]
        latest_ma200 = history['MA200'].iloc[-1]

        return {
            "high_52w":     round(history['Close'].max(), 2),
            "low_52w":      round(history['Close'].min(), 2),
            "avg_price":    round(history['Close'].mean(), 2),
            "avg_volume":   round(history['Volume'].mean(), 0),
            "volatility":   round(history['Daily_Return'].std() * 100, 2),
            "ma50":         round(latest_ma50, 2),
            "ma200":        round(latest_ma200, 2),
            "ma50_signal":  "ABOVE" if latest_price > latest_ma50  else "BELOW",
            "ma200_signal": "ABOVE" if latest_price > latest_ma200 else "BELOW",
        }
    except Exception:
        return None


def get_company_news(ticker: str) -> list[str]:
    name_map = {
        "RELIANCE.NS": "Reliance Industries",
        "TCS.NS":      "TCS Tata Consultancy",
        "INFY.NS":     "Infosys",
        "HDFCBANK.NS": "HDFC Bank",
        "WIPRO.NS":    "Wipro",
    }

    company = name_map.get(ticker.upper(), ticker.split(".")[0])
    api_key = os.getenv("NEWS_API_KEY")

    url = (
        f"https://newsapi.org/v2/everything"
        f"?q={company}&language=en&pageSize=5&sortBy=publishedAt"
        f"&apiKey={api_key}"
    )

    try:
        response = requests.get(url, timeout=5)
        articles = response.json().get("articles", [])
        headlines = [a["title"] for a in articles[:5]]
        return headlines
    except Exception:
        return ["Could not fetch news."]