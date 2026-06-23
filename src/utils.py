def get_currency_symbol(ticker):
    ticker = str(ticker).upper()

    suffix_map = {
        ".NS": "₹", ".BO": "₹",
        ".L": "£",
        ".PA": "€", ".NX": "€", ".DE": "€", ".F": "€", ".AS": "€",
        ".MC": "€", ".MI": "€", ".BR": "€", ".VI": "€", ".LS": "€",
        ".HE": "€", ".AT": "€",
        ".SW": "CHF ",
        ".T": "¥",
        ".SS": "¥", ".SZ": "¥",
        ".HK": "HK$",
        ".AX": "A$",
        ".TO": "C$", ".V": "C$",
        ".SA": "R$",
        ".KS": "₩", ".KQ": "₩",
        ".SI": "S$",
        ".ST": "kr ", ".OL": "kr ", ".CO": "kr ",
        ".MX": "MX$",
        ".JO": "R",
        ".SR": "﷼",
        ".AD": "AED ", ".DU": "AED ",
        ".NZ": "NZ$",
        ".BK": "฿",
        ".KL": "RM",
        ".JK": "Rp",
        ".TW": "NT$",
        ".TA": "₪",
        ".IS": "₺",
        ".ME": "₽",
    }
    for suffix, symbol in suffix_map.items():
        if ticker.endswith(suffix):
            return symbol
    return "$"


def format_number(value, ticker=""):
    """Big numbers (revenue, market cap, FCF) in local-currency-appropriate units."""
    if value == "N/A" or value is None:
        return "N/A"
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "N/A"
    symbol = get_currency_symbol(ticker)
    if symbol == "₹":
        return f"₹{value / 1e7:,.2f} Crore"
    if abs(value) >= 1e9:
        return f"{symbol}{value / 1e9:,.2f} Billion"
    if abs(value) >= 1e6:
        return f"{symbol}{value / 1e6:,.2f} Million"
    return f"{symbol}{value:,.2f}"


def format_price(value, ticker=""):
    if value == "N/A" or value is None:
        return "N/A"
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "N/A"
    symbol = get_currency_symbol(ticker)
    return f"{symbol}{value:,.2f}"


def format_ratio(value):
    if value == "N/A" or value is None:
        return "N/A"
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return "N/A"


def format_percent(value):
    """Expects a fraction (0.12 -> 12.00%). Caps absurd values as a data-quality guard."""
    if value == "N/A" or value is None:
        return "N/A"
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "N/A"
    result = value * 100
    if abs(result) > 1000:
        return "N/A (data error)"
    return f"{result:.2f}%"


def build_stock_prompt(data, signals, ticker=""):
    signals_text = "\n".join([f"- {s}" for s in signals]) if signals else "- None detected"
    return f"""
Analyse this stock and return a JSON research brief.

Company: {data.get('name', 'N/A')}
Sector: {data.get('sector', 'N/A')}
Industry: {data.get('industry', 'N/A')}

--- PRICE & VALUATION ---
Latest Price:          {format_price(data.get('price'), ticker)}
P/E Ratio:             {format_ratio(data.get('pe'))}
Forward P/E:           {format_ratio(data.get('forward_pe'))}
P/B Ratio:             {format_ratio(data.get('pb_ratio'))}
EV/EBITDA:             {format_ratio(data.get('ev_to_ebitda'))}
EPS:                   {format_price(data.get('eps'), ticker)}
Dividend Yield:        {format_percent(data.get('dividend_yield'))}
1-Year Price Change:   {format_ratio(data.get('price_change_1y'))}%
Beta:                  {format_ratio(data.get('beta'))}
Analyst Target Price:  {format_price(data.get('target_price'), ticker)}
Analyst Recommendation:{data.get('recommendation', 'N/A')}

--- FINANCIALS ---
Total Revenue:         {format_number(data.get('revenue'), ticker)}
Market Cap:            {format_number(data.get('market_cap'), ticker)}
Free Cash Flow:        {format_number(data.get('free_cashflow'), ticker)}
Revenue Growth (YoY):  {format_percent(data.get('revenue_growth'))}
Earnings Growth (YoY): {format_percent(data.get('earnings_growth'))}

--- PROFITABILITY & RISK ---
Profit Margin:         {format_percent(data.get('profit_margin'))}
Return on Equity:      {format_percent(data.get('roe'))}
Debt to Equity:        {format_ratio(data.get('debt_to_equity'))}

--- SIGNALS DETECTED ---
{signals_text}

--- ABOUT ---
{data.get('summary', 'N/A')}
""".strip()