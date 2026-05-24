def get_currency_symbol(ticker):
    ticker = str(ticker).upper()

    if ticker.endswith(".NS") or ticker.endswith(".BO"):
        return "₹"
    if ticker.endswith(".L"):
        return "£"
    if ticker.endswith(".PA") or ticker.endswith(".NX"):
        return "€"
    if ticker.endswith(".DE") or ticker.endswith(".F"):
        return "€"
    if ticker.endswith(".AS"):
        return "€"
    if ticker.endswith(".MC"):
        return "€"
    if ticker.endswith(".MI"):
        return "€"
    if ticker.endswith(".BR"):
        return "€"
    if ticker.endswith(".VI"):
        return "€"
    if ticker.endswith(".LS"):
        return "€"
    if ticker.endswith(".HE"):
        return "€"
    if ticker.endswith(".AT"):
        return "€"
    if ticker.endswith(".SW"):
        return "CHF "
    if ticker.endswith(".T"):
        return "¥"
    if ticker.endswith(".SS") or ticker.endswith(".SZ"):
        return "¥"
    if ticker.endswith(".HK"):
        return "HK$"
    if ticker.endswith(".AX"):
        return "A$"
    if ticker.endswith(".TO") or ticker.endswith(".V"):
        return "C$"
    if ticker.endswith(".SA"):
        return "R$"
    if ticker.endswith(".KS") or ticker.endswith(".KQ"):
        return "₩"
    if ticker.endswith(".SI"):
        return "S$"
    if ticker.endswith(".ST"):
        return "kr "
    if ticker.endswith(".OL"):
        return "kr "
    if ticker.endswith(".CO"):
        return "kr "
    if ticker.endswith(".MX"):
        return "MX$"
    if ticker.endswith(".JO"):
        return "R"
    if ticker.endswith(".SR"):
        return "﷼"
    if ticker.endswith(".AD") or ticker.endswith(".DU"):
        return "AED "
    if ticker.endswith(".NZ"):
        return "NZ$"
    if ticker.endswith(".BK"):
        return "฿"
    if ticker.endswith(".KL"):
        return "RM"
    if ticker.endswith(".JK"):
        return "Rp"
    if ticker.endswith(".TW"):
        return "NT$"
    if ticker.endswith(".TA"):
        return "₪"
    if ticker.endswith(".IS"):
        return "₺"
    if ticker.endswith(".ME"):
        return "₽"
    return "$"


def format_number(value, ticker=""):
    if value == "N/A" or value is None:
        return "N/A"
    symbol = get_currency_symbol(ticker)
    if symbol == "₹":
        return f"₹{value / 1e7:,.2f} Crore"
    return f"{symbol}{value / 1e9:,.2f} Billion"


def format_price(value, ticker=""):
    if value == "N/A" or value is None:
        return "N/A"
    symbol = get_currency_symbol(ticker)
    return f"{symbol}{value:,.2f}"


def format_ratio(value):
    if value == "N/A" or value is None:
        return "N/A"
    return f"{value:.2f}"


def format_percent(value):
    if value == "N/A" or value is None:
        return "N/A"
    result = value * 100
    if result > 20:
        return "N/A (data error)"
    return f"{result:.2f}%"


def build_stock_prompt(data, signals, ticker=""):
    signals_text = "\n".join([f"- {s}" for s in signals])
    return f"""
Analyse this stock and return a JSON research brief.

Company: {data['name']}
Sector: {data['sector']}
Industry: {data['industry']}

--- PRICE & VALUATION ---
Latest Price:          {format_price(data['price'], ticker)}
P/E Ratio:             {format_ratio(data['pe'])}
P/B Ratio:             {format_ratio(data['pb_ratio'])}
EPS:                   {format_price(data['eps'], ticker)}
Dividend Yield:        {format_percent(data['dividend_yield'])}
1-Year Price Change:   {format_ratio(data['price_change_1y'])}%

--- FINANCIALS ---
Total Revenue:         {format_number(data['revenue'], ticker)}
Market Cap:            {format_number(data['market_cap'], ticker)}
Revenue Growth (YoY):  {format_percent(data['revenue_growth'])}
Earnings Growth (YoY): {format_percent(data['earnings_growth'])}

--- PROFITABILITY & RISK ---
Profit Margin:         {format_percent(data['profit_margin'])}
Return on Equity:      {format_percent(data['roe'])}
Debt to Equity:        {format_ratio(data['debt_to_equity'])}

--- SIGNALS DETECTED ---
{signals_text}

--- ABOUT ---
{data['summary']}
""".strip()