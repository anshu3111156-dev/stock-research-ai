import json
import os
from groq import Groq
from dotenv import load_dotenv
from src.utils import build_stock_prompt
from src.data import get_company_news

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ── FALLBACK MODEL CHAIN ──────────────────
# If one model is rate limited, automatically tries the next
MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it"
]

def call_groq_with_fallback(messages, max_tokens=1000):
    last_error = None
    for model in MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
                max_tokens=max_tokens
            )
            return response
        except Exception as e:
            if "rate_limit" in str(e).lower() or "429" in str(e):
                last_error = e
                continue
            raise e
    raise Exception(
        "All AI models are currently at capacity. Please try again in 30 minutes."
    )

# ── SYSTEM PROMPTS ────────────────────────

def get_stock_system_prompt(lang="English"):
    language_rule = (
        "Write all text in Hindi (Devanagari script). "
        "Keep financial terms like P/E, ROE, EPS in English but explain them in Hindi."
        if lang == "हिंदी"
        else "Write all responses in clear simple English."
    )

    return f"""
You are an equity research analyst writing briefs for retail investors.
{language_rule}

YOUR RULES:
1. Never give buy, sell, or hold recommendations.
2. Use correct currency for the stock exchange:
   Indian stocks (NSE/BSE) — use ₹ and Crore/Lakh Crore.
   US stocks (NYSE/NASDAQ) — use $ and Billion/Million.
   UK stocks (LSE) — use £ and Billion/Million.
   European stocks — use € and Billion/Million.
   Match currency to the exchange the stock is listed on.
3. Use simple language. Avoid jargon. If you must use a term explain it in brackets.
4. Be honest about data gaps — if a metric is N/A say so clearly.
5. Always flag risks clearly. Never be overly optimistic.
6. Keep language neutral and factual.
7. Write as if explaining to an educated first-time investor aged 25-35.
8. Respond with ONLY a valid JSON object. No extra text, no markdown, no backticks.
9. Debt context — D/E below 50 is LOW for most non-financial companies.
   Only flag debt as high if D/E is above 100.
10. In key_metrics always use the correct currency symbol for the exchange.
    Never use ₹ for US, UK or European stocks.
11. The stock exchange is clear from the company data. Use it to determine currency.

OUTPUT FORMAT — exactly these keys:
{{
  "company_name": "string",
  "sector": "string",
  "analyst_summary": "2 sentence plain English overview under 50 words",
  "valuation_commentary": "2-3 sentences on P/E, P/B, EPS",
  "financial_health": "3-4 sentences on revenue, margins, ROE, debt",
  "growth_outlook": "2-3 sentences on revenue and earnings growth",
  "risk_flags": ["risk 1", "risk 2", "risk 3"],
  "investor_profile": "1-2 sentences on what type of investor this suits",
  "key_metrics": {{
    "price": "string — correct currency for this exchange",
    "pe_ratio": "string",
    "pb_ratio": "string",
    "profit_margin": "string",
    "roe": "string",
    "debt_to_equity": "string",
    "revenue_growth": "string",
    "one_year_return": "string — percentage only"
  }},
  "watch_out_for": "1-2 sentences on most important thing to monitor",
  "news_context": "2-3 sentences on recent news and what it means for the stock",
  "annual_report_insights": "3-4 sentences of key insights from annual report covering strategy, risks and outlook"
}}
"""

PORTFOLIO_SYSTEM_PROMPT = """
You are a portfolio analyst writing for retail investors.

YOUR RULES:
1. Never give buy, sell, or hold recommendations.
2. Use correct currency for each stock's exchange.
3. Use simple English. Avoid jargon.
4. Be honest about risks. Never be overly optimistic.
5. Respond with ONLY a valid JSON object. No extra text, no markdown, no backticks.

OUTPUT FORMAT — exactly these keys:
{
  "portfolio_summary": "3-4 sentences describing the portfolio as a whole",
  "sector_concentration": "2-3 sentences on diversification",
  "overall_health": "2-3 sentences on combined financial health",
  "portfolio_risks": ["risk 1", "risk 2", "risk 3"],
  "best_performing_stock": "stock name and why it stands out",
  "weakest_stock": "stock name and what concerns exist",
  "portfolio_advice": "2-3 sentences of general observations",
  "watch_out_for": "2 sentences on most important thing to monitor"
}
"""

# ── JSON PARSER ───────────────────────────

def parse_json(raw):
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())

# ── GENERATE STOCK BRIEF ──────────────────

def generate_stock_brief(data, signals, ticker, vectorstore=None, lang="English"):
    prompt = build_stock_prompt(data, signals, ticker)

    # add news headlines
    headlines = get_company_news(ticker)
    if headlines and headlines != ["Could not fetch news."]:
        news_text = "\n".join(f"- {h}" for h in headlines)
        prompt += f"""

RECENT NEWS HEADLINES (last 5):
{news_text}

Use these headlines to fill the news_context field.
Comment on what this news means for the stock.
"""
    else:
        prompt += "\n\nnews_context: No recent news available."

    # add RAG insights from annual report if available
    if vectorstore is not None:
        try:
            rag_questions = [
                "What is the company strategy and future outlook?",
                "What are the key risks mentioned by management?",
                "What are the capital expenditure and growth plans?",
            ]
            rag_context = ""
            for q in rag_questions:
                results = vectorstore.similarity_search(q, k=2)
                for doc in results:
                    page = doc.metadata.get('page', '?')
                    rag_context += f"\n[Page {page}] {doc.page_content}\n"

            prompt += f"""

INSIGHTS FROM COMPANY ANNUAL REPORT:
{rag_context}

Use these annual report insights to fill the annual_report_insights field.
Summarise key strategic points, risks and outlook in simple English.
"""
        except Exception:
            prompt += "\n\nannual_report_insights: Annual report data not available."
    else:
        prompt += "\n\nannual_report_insights: Annual report not loaded for this stock."

    system_prompt = get_stock_system_prompt(lang)

    response = call_groq_with_fallback(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": prompt}
        ],
        max_tokens=1000
    )
    return parse_json(response.choices[0].message.content)

# ── GENERATE PORTFOLIO BRIEF ──────────────

def generate_portfolio_brief(all_stock_data, lang="English"):
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
Analyse this portfolio of stocks and return a JSON portfolio brief.

PORTFOLIO HOLDINGS:
{portfolio_text}

Total stocks: {len(all_stock_data)}
Sectors represented: {', '.join(set([
    i['data']['sector']
    for i in all_stock_data
    if i['data']['sector'] != 'N/A'
]))}
"""

    response = call_groq_with_fallback(
        messages=[
            {"role": "system", "content": PORTFOLIO_SYSTEM_PROMPT},
            {"role": "user",   "content": prompt}
        ],
        max_tokens=1000
    )
    return parse_json(response.choices[0].message.content)