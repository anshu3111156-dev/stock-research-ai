def format_number(value):
    if value == "N/A" or value is None: return "N/A"
    return f"₹{value / 1e7:,.2f} Crore"

def format_price(value):
    if value == "N/A" or value is None: return "N/A"
    return f"₹{value:,.2f}"

def format_ratio(value):
    if value == "N/A" or value is None: return "N/A"
    return f"{value:.2f}"

def format_percent(value):
    if value == "N/A" or value is None: return "N/A"
    result = value * 100
    if result > 20: return "N/A (data error)"
    return f"{result:.2f}%"

def build_stock_prompt(data, signals):
    from src.utils import format_price, format_ratio, format_number, format_percent
    signals_text = "\n".join([f"- {s}" for s in signals])
    return f"""
Analyse this Indian stock and return a JSON research brief.

Company: {data['name']}
Sector: {data['sector']}
Industry: {data['industry']}

--- PRICE & VALUATION ---
Latest Price:          {format_price(data['price'])}
P/E Ratio:             {format_ratio(data['pe'])}
P/B Ratio:             {format_ratio(data['pb_ratio'])}
EPS:                   {format_price(data['eps'])}
Dividend Yield:        {format_percent(data['dividend_yield'])}
1-Year Price Change:   {format_ratio(data['price_change_1y'])}%

--- FINANCIALS ---
Total Revenue:         {format_number(data['revenue'])}
Market Cap:            {format_number(data['market_cap'])}
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