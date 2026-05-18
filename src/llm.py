import json
import os
from groq import Groq
from dotenv import load_dotenv
from src.utils import build_stock_prompt
from src.data import get_company_news

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

STOCK_SYSTEM_PROMPT = """
You are a SEBI-registered equity research analyst at a reputed Indian brokerage firm.
You write research briefs strictly for retail investors in India.

YOUR RULES:
1. Never give buy, sell, or hold recommendations.
2. Always use Indian units — Crore and Lakh Crore. Never say billion or million.
3. Use simple English. Avoid jargon. If you must use a term, explain it in brackets.
4. Be honest about data gaps — if a metric is N/A, say so clearly.
5. Always flag risks clearly. Never paint an overly optimistic picture.
6. Keep language neutral and factual.
7. Write as if explaining to an educated first-time investor aged 25-35.
8. Respond with ONLY a valid JSON object. No extra text, no markdown, no backticks.
9. IMPORTANT — use sector context for debt: a D/E below 50 is LOW for most Indian
   non-financial companies. Only flag debt as high if D/E is above 100.

OUTPUT FORMAT — exactly these keys:
{
  "company_name": "string",
  "sector": "string",
  "analyst_summary": "2 sentence plain English overview under 50 words",
  "valuation_commentary": "2-3 sentences on P/E, P/B, EPS",
  "financial_health": "3-4 sentences on revenue, margins, ROE, debt",
  "growth_outlook": "2-3 sentences on revenue and earnings growth",
  "risk_flags": ["risk 1", "risk 2", "risk 3"],
  "investor_profile": "1-2 sentences on what type of investor this suits",
  "key_metrics": {
    "price": "string",
    "pe_ratio": "string",
    "pb_ratio": "string",
    "profit_margin": "string",
    "roe": "string",
    "debt_to_equity": "string",
    "revenue_growth": "string",
    "one_year_return": "string"
  },
  "watch_out_for": "1-2 sentences on most important thing to monitor",
  "news_context": "2-3 sentences commenting on the recent news headlines and what they mean for the stock"
}
"""

PORTFOLIO_SYSTEM_PROMPT = """
You are a SEBI-registered portfolio analyst at a reputed Indian brokerage firm.
You analyse a collection of stocks as a whole portfolio for retail investors in India.

YOUR RULES:
1. Never give buy, sell, or hold recommendations.
2. Always use Indian units — Crore and Lakh Crore. Never say billion or million.
3. Use simple English. Avoid jargon.
4. Be honest about risks. Never be overly optimistic.
5. Respond with ONLY a valid JSON object. No extra text, no markdown, no backticks.

OUTPUT FORMAT — exactly these keys:
{
  "portfolio_summary": "3-4 sentences describing the portfolio as a whole",
  "sector_concentration": "2-3 sentences on diversification",
  "overall_health": "2-3 sentences on combined financial health",
  "portfolio_risks": ["risk 1", "risk 2", "risk 3"],
  "best_performing_stock": "stock name and why",
  "weakest_stock": "stock name and concerns",
  "portfolio_advice": "2-3 sentences of general observations",
  "watch_out_for": "2 sentences on most important thing to monitor"
}
"""

def parse_json(raw):
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())

def generate_stock_brief(data, signals, ticker):
    prompt = build_stock_prompt(data, signals)

    # Fetch news and append to prompt
    headlines = get_company_news(ticker)
    if headlines and headlines != ["Could not fetch news."]:
        news_text = "\n".join(f"- {h}" for h in headlines)
        prompt += f"""

RECENT NEWS HEADLINES (last 5):
{news_text}

Use these headlines to add a news_context field in your JSON response.
Comment on what this news means for the stock — opportunities or concerns.
"""
    else:
        prompt += "\n\nnews_context: No recent news available."

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": STOCK_SYSTEM_PROMPT},
            {"role": "user",   "content": prompt}
        ],
        temperature=0.3,
        max_tokens=1500
    )
    return parse_json(response.choices[0].message.content)

def generate_portfolio_brief(all_stock_data):
    from src.utils import format_percent, format_ratio
    portfolio_text = ""
    for item in all_stock_data:
        d = item['data']
        portfolio_text += f"""
Stock: {d['name']}
Sector: {d['sector']}
1-Year Return: {d['price_change_1y']}%
Revenue Growth: {format_percent(d['revenue_growth'])}
Profit Margin: {format_percent(d['profit_margin'])}
Debt to Equity: {format_ratio(d['debt_to_equity'])}
Signals: {', '.join(item['signals'])}
---"""

    prompt = f"""
Analyse this portfolio of Indian stocks and return a JSON portfolio brief.

PORTFOLIO HOLDINGS:
{portfolio_text}

Total stocks: {len(all_stock_data)}
Sectors represented: {', '.join(set([i['data']['sector'] for i in all_stock_data if i['data']['sector'] != 'N/A']))}
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": PORTFOLIO_SYSTEM_PROMPT},
            {"role": "user",   "content": prompt}
        ],
        temperature=0.3,
        max_tokens=1500
    )
    return parse_json(response.choices[0].message.content)