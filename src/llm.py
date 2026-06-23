import json
import os
from groq import Groq
from dotenv import load_dotenv
from src.utils import build_stock_prompt
from src.data import get_company_news

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Optional per-ticker RAG — degrades gracefully if rag.py / reports aren't set up
try:
    from src.rag import load_index_for_ticker, has_report
    _RAG_AVAILABLE = True
except Exception:
    _RAG_AVAILABLE = False
    def has_report(ticker):  # noqa
        return False
    def load_index_for_ticker(ticker):  # noqa
        return None


LEVEL_INSTRUCTIONS = {
    "🌱 Beginner": (
        "Audience: complete beginner, never invested before. Use very simple words, "
        "explain every term in plain language inline, avoid jargon entirely. "
        "Keep sentences short. Assume zero prior finance knowledge."
    ),
    "📈 Learner": (
        "Audience: knows basic investing terms (P/E, market cap) but still learning. "
        "Use simple language but you may use standard terms without re-explaining every one."
    ),
    "💼 Intermediate": (
        "Audience: comfortable with P/E, ROE, debt ratios and basic fundamental analysis. "
        "Write at a standard retail-investor analyst level, no need to over-explain basics."
    ),
    "🏦 Expert": (
        "Audience: experienced investor with deep market knowledge. Be precise and concise, "
        "use proper financial terminology freely, focus on nuance over explanation."
    ),
}

LANG_INSTRUCTIONS = {
    "English": "Write the entire response in English.",
    "Hindi": "Write the entire response in Hindi (Devanagari script), keeping financial terms and numbers clear.",
}


STOCK_SYSTEM_PROMPT_TEMPLATE = """
You are a SEBI-registered equity research analyst at a reputed Indian brokerage firm.
You write research briefs strictly for retail investors.

YOUR RULES:
1. Never give buy, sell, or hold recommendations.
2. Always use Indian units (Crore, Lakh Crore) for Indian stocks; use Billion/Million for non-Indian stocks. Match whatever unit convention is already used in the data given to you.
3. {level_instruction}
4. {lang_instruction}
5. Be honest about data gaps — if a metric is N/A, say so clearly.
6. Always flag risks clearly. Never paint an overly optimistic picture.
7. Keep language neutral and factual.
8. Respond with ONLY a valid JSON object. No extra text, no markdown, no backticks.
9. IMPORTANT — use sector context for debt: a D/E below 50 is LOW for most non-financial companies. Only flag debt as high if D/E is above 100.
10. Set "traffic_light" to one of exactly: "GREEN", "YELLOW", "RED" based on overall financial health
    (GREEN = healthy fundamentals & low risk flags, YELLOW = mixed signals, RED = significant red flags like losses, very high debt, or sharp price decline).
    "traffic_light_reason" must be ONE short sentence explaining why.

OUTPUT FORMAT — exactly these keys:
{{
  "company_name": "string",
  "sector": "string",
  "traffic_light": "GREEN | YELLOW | RED",
  "traffic_light_reason": "1 short sentence",
  "analyst_summary": "2 sentence plain English overview under 50 words",
  "valuation_commentary": "2-3 sentences on P/E, P/B, EPS",
  "financial_health": "3-4 sentences on revenue, margins, ROE, debt",
  "growth_outlook": "2-3 sentences on revenue and earnings growth",
  "risk_flags": ["risk 1", "risk 2", "risk 3"],
  "investor_profile": "1-2 sentences on what type of investor this suits",
  "key_metrics": {{
    "price": "string",
    "pe_ratio": "string",
    "pb_ratio": "string",
    "profit_margin": "string",
    "roe": "string",
    "debt_to_equity": "string",
    "revenue_growth": "string",
    "one_year_return": "string"
  }},
  "watch_out_for": "1-2 sentences on most important thing to monitor",
  "news_context": "2-3 sentences commenting on the recent news headlines and what they mean for the stock",
  "annual_report_insights": "3-4 sentences of key insights from the company annual report covering strategy, risks and outlook, OR null if no annual report context was provided below"
}}
"""

PORTFOLIO_SYSTEM_PROMPT = """
You are a SEBI-registered portfolio analyst at a reputed Indian brokerage firm.
You analyse a collection of stocks as a whole portfolio for retail investors.

YOUR RULES:
1. Never give buy, sell, or hold recommendations.
2. Use simple English. Avoid jargon.
3. Be honest about risks. Never be overly optimistic.
4. Respond with ONLY a valid JSON object. No extra text, no markdown, no backticks.

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


def _rag_context_for_ticker(ticker: str) -> str | None:
    """Returns formatted annual-report context for a ticker, or None if unavailable."""
    if not _RAG_AVAILABLE or not has_report(ticker):
        return None
    try:
        vectorstore = load_index_for_ticker(ticker)
        if not vectorstore:
            return None
        questions = [
            "What is the company strategy and future outlook?",
            "What are the key risks mentioned by management?",
            "What are the capital expenditure and growth plans?",
        ]
        context = ""
        for q in questions:
            results = vectorstore.similarity_search(q, k=3)
            for doc in results:
                page = doc.metadata.get('page', '?')
                context += f"\n[Page {page}] {doc.page_content}\n"
        return context
    except Exception:
        return None


def generate_stock_brief(data, signals, ticker, vectorstore=None, lang="English", level="💼 Intermediate"):
    """
    vectorstore param kept for backward compatibility but ignored —
    the correct per-ticker RAG index (if any) is loaded internally based on ticker.
    """
    prompt = build_stock_prompt(data, signals, ticker)

    # News
    headlines = get_company_news(ticker)
    if headlines and headlines != ["Could not fetch news."]:
        news_text = "\n".join(f"- {h}" for h in headlines)
        prompt += f"""

RECENT NEWS HEADLINES (last 5):
{news_text}

Use these headlines to fill the news_context field. Comment on what this news means for the stock.
"""
    else:
        prompt += "\n\n(No recent news available — set news_context to a short note saying so.)"

    # RAG (per-ticker)
    rag_context = _rag_context_for_ticker(ticker)
    if rag_context:
        prompt += f"""

INSIGHTS FROM COMPANY ANNUAL REPORT:
{rag_context}

Use these annual report insights to fill the annual_report_insights field. Summarise key strategic points, risks and outlook in simple English.
"""
    else:
        prompt += "\n\n(No annual report on file for this company — set annual_report_insights to null.)"

    system_prompt = STOCK_SYSTEM_PROMPT_TEMPLATE.format(
        level_instruction=LEVEL_INSTRUCTIONS.get(level, LEVEL_INSTRUCTIONS["💼 Intermediate"]),
        lang_instruction=LANG_INSTRUCTIONS.get(lang, LANG_INSTRUCTIONS["English"]),
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": prompt}
        ],
        temperature=0.3,
        max_tokens=2000
    )
    return parse_json(response.choices[0].message.content)


def _fallback_brief(data, signals, ticker):
    """
    Used by app.py when the LLM call fails (rate limit, API error, bad JSON).
    Returns a minimal but structurally complete brief built only from raw data,
    so the UI doesn't crash — it just shows less commentary.
    """
    from src.utils import format_price, format_ratio, format_percent

    name = data.get("name") or ticker
    pe   = format_ratio(data.get("pe"))
    pb   = format_ratio(data.get("pb_ratio"))
    pm   = format_percent(data.get("profit_margin"))
    roe  = format_percent(data.get("roe"))
    de   = format_ratio(data.get("debt_to_equity"))
    rg   = format_percent(data.get("revenue_growth"))
    ret  = format_ratio(data.get("price_change_1y"))
    price = format_price(data.get("price"), ticker)

    has_warning = any("WARNING" in s for s in signals)
    traffic_light = "RED" if has_warning else "YELLOW"

    return {
        "company_name": name,
        "sector": data.get("sector", "N/A"),
        "traffic_light": traffic_light,
        "traffic_light_reason": "AI commentary unavailable — based on raw signals only.",
        "analyst_summary": f"{name} data loaded from live market feed. AI commentary is temporarily unavailable; raw metrics and signals are shown below.",
        "valuation_commentary": f"P/E: {pe}, P/B: {pb}. Compare against sector peers for context.",
        "financial_health": f"Profit margin: {pm}, ROE: {roe}, Debt/Equity: {de}.",
        "growth_outlook": f"Revenue growth (YoY): {rg}.",
        "risk_flags": [s for s in signals if "WARNING" in s] or ["No AI risk analysis available right now."],
        "investor_profile": "N/A — AI commentary unavailable.",
        "key_metrics": {
            "price": price,
            "pe_ratio": pe,
            "pb_ratio": pb,
            "profit_margin": pm,
            "roe": roe,
            "debt_to_equity": de,
            "revenue_growth": rg,
            "one_year_return": f"{ret}%" if ret != "N/A" else "N/A",
        },
        "watch_out_for": "AI brief unavailable — please retry shortly.",
        "news_context": "N/A — AI commentary unavailable.",
        "annual_report_insights": None,
    }


def generate_portfolio_brief(all_stock_data):
    from src.utils import format_percent, format_ratio
    portfolio_text = ""
    for item in all_stock_data:
        d = item['data']
        portfolio_text += f"""
Stock: {d.get('name', 'N/A')}
Sector: {d.get('sector', 'N/A')}
1-Year Return: {d.get('price_change_1y', 'N/A')}%
Revenue Growth: {format_percent(d.get('revenue_growth'))}
Profit Margin: {format_percent(d.get('profit_margin'))}
Debt to Equity: {format_ratio(d.get('debt_to_equity'))}
Signals: {', '.join(item['signals'])}
---"""

    prompt = f"""
Analyse this portfolio of stocks and return a JSON portfolio brief.

PORTFOLIO HOLDINGS:
{portfolio_text}

Total stocks: {len(all_stock_data)}
Sectors represented: {', '.join(set([i['data'].get('sector', 'N/A') for i in all_stock_data if i['data'].get('sector') not in (None, 'N/A')]))}
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