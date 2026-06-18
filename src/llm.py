import re
import json
import os
import time
import logging

from groq import Groq
from dotenv import load_dotenv
from src.utils import build_stock_prompt, format_percent, format_ratio
from src.data import get_company_news

load_dotenv()

logger = logging.getLogger(__name__)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ── FALLBACK MODEL CHAIN ──────────────────────────────────────────────────────
MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
]

_RETRY_KEYWORDS = [
    "rate_limit", "429", "503", "capacity", "timeout",
    "overloaded", "service unavailable", "too many requests",
]


def call_groq_with_fallback(messages: list, max_tokens: int = 1800) -> object:
    last_error = None
    for model in MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
                max_tokens=max_tokens,
            )
            return response
        except Exception as e:
            err_str = str(e).lower()
            if any(kw in err_str for kw in _RETRY_KEYWORDS):
                last_error = e
                time.sleep(2)
                continue
            raise e
    raise Exception(
        "All AI models are currently at capacity. Please try again in 30 minutes."
    ) from last_error


# ── JSON PARSER ───────────────────────────────────────────────────────────────
def parse_json(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```\s*$', '', raw)
    raw = raw.strip()
    start = raw.find('{')
    end   = raw.rfind('}')
    if start != -1 and end != -1 and end > start:
        raw = raw[start:end + 1]
    return json.loads(raw)


# ── LEVEL-AWARE SYSTEM PROMPTS ────────────────────────────────────────────────
# Each level produces genuinely different content — not just tone but structure,
# vocabulary, depth, and what is explained vs assumed.

def _get_system_prompt(level: str, lang: str = "English") -> str:
    language_rule = (
        "Write all text values in Hindi (Devanagari script). "
        "Keep financial terms like P/E, ROE, EPS in English but explain them in Hindi. "
        "All JSON keys must remain in English."
        if lang == "हिंदी"
        else "Write all responses in English."
    )

    currency_rule = """Currency rules — follow exactly:
- Indian stocks (.NS / .BO suffix) → use ₹ and Crore / Lakh Crore
- US stocks (no suffix, NYSE/NASDAQ) → use $ and Billion / Million
- UK stocks (.L) → use £ and Billion
- European stocks (.PA .DE .MI etc.) → use € and Billion
- Never mix currencies. Use the exchange to determine which currency."""

    base_rules = f"""{language_rule}

{currency_rule}

ALWAYS:
- Never give buy, sell, or hold recommendations.
- Be honest about data gaps. If a metric is N/A say so.
- Debt/Equity below 50 is LOW for most non-financial companies. Only flag debt as high if D/E > 80. Banks are leveraged by design.
- Respond with ONLY a valid JSON object. No markdown. No backticks. No text outside the JSON."""

    output_format = """
OUTPUT FORMAT — return exactly these keys:
{
  "company_name": "string",
  "sector": "string",
  "traffic_light": "GREEN or YELLOW or RED",
  "traffic_light_reason": "one plain sentence explaining the signal",
  "analyst_summary": "string",
  "valuation_commentary": "string",
  "financial_health": "string",
  "growth_outlook": "string",
  "risk_flags": ["risk 1", "risk 2", "risk 3", "risk 4"],
  "investor_profile": "string",
  "key_metrics": {
    "price": "string with currency",
    "pe_ratio": "string",
    "pb_ratio": "string",
    "profit_margin": "string as %",
    "roe": "string as %",
    "debt_to_equity": "string",
    "revenue_growth": "string as %",
    "one_year_return": "string as % with + or - sign"
  },
  "watch_out_for": "string",
  "news_context": "string",
  "annual_report_insights": "string"
}"""

    # ── BEGINNER ──────────────────────────────────────────────────────────────
    if "Beginner" in level or "🌱" in level:
        return f"""You are explaining a stock to someone who has never invested before. They are a 22-year-old who just started earning and wants to understand if a company is doing well.

{base_rules}

BEGINNER WRITING RULES — every single one is mandatory:
1. Never use a financial term without explaining it in simple brackets immediately after. Example: "P/E ratio (how much you are paying for every ₹1 the company earns)".
2. Write like you are explaining to a curious friend, not writing a report. Use "the company", "they", "it" — not corporate language.
3. analyst_summary must be 80-100 words. Start with what the company actually does in one sentence. Then explain if it is doing well or not. No jargon.
4. valuation_commentary: Explain P/E simply. Say whether the stock seems cheap or expensive in plain words. Always give context: "A P/E of 25 means you are paying ₹25 for every ₹1 of profit the company makes."
5. financial_health: Use simple comparisons. "The company earns more than it spends" or "It has borrowed a lot — imagine taking a big loan to run your business."
6. growth_outlook: Is the company growing? By how much? Make it feel real. "Revenue grew 18% — that means they sold 18% more than last year."
7. risk_flags: Each flag must be a full plain-English sentence. Not "High debt" — instead: "The company has borrowed a large amount of money, which means it has to pay back loans even when times are tough."
8. investor_profile: Say in one sentence who this is good for and one sentence warning about risk. No jargon.
9. watch_out_for: One thing, explained simply, that even a non-investor can understand.
10. traffic_light: Set to GREEN, YELLOW, or RED based on overall health. traffic_light_reason must be one simple sentence a beginner can understand.
11. news_context: Explain the news like you are telling a friend what happened. What does it mean for the company?

{output_format}"""

    # ── LEARNER ───────────────────────────────────────────────────────────────
    elif "Learner" in level or "📈" in level:
        return f"""You are writing a stock brief for someone who understands what stocks are and knows basic terms like P/E and revenue, but is still building their knowledge.

{base_rules}

LEARNER WRITING RULES:
1. You can use financial terms but always add brief context the first time. Example: "P/E of 24 — roughly in line with sector average for consumer companies."
2. analyst_summary: 70-80 words. Cover what the company does, current performance, and one key thing to know. Moderate depth.
3. valuation_commentary: Mention P/E, P/B. Add sector context — is this ratio high or normal for this type of company?
4. financial_health: Cover revenue, margin, ROE and debt. One sentence of context per metric. Not too deep.
5. growth_outlook: Give growth rates with interpretation. "Revenue growth of 15% is healthy but slowing from last year's 22%."
6. risk_flags: Short specific sentences. Can use some financial terms but explain them briefly. Example: "Debt/Equity of 120 is elevated — the company is more leveraged than most peers."
7. investor_profile: 2 sentences. Who suits this stock — growth, value, or income investors?
8. watch_out_for: One or two things with brief explanation of why they matter.
9. Do NOT set traffic_light or traffic_light_reason — set both to "N/A".
10. news_context: Brief interpretation of the news and what it signals.

{output_format}"""

    # ── INTERMEDIATE ──────────────────────────────────────────────────────────
    elif "Intermediate" in level or "💼" in level:
        return f"""You are writing a stock brief for an investor who invests regularly and is comfortable with standard financial analysis. They understand P/E, ROE, margins, and sector comparisons.

{base_rules}

INTERMEDIATE WRITING RULES:
1. Use standard financial language without explanation. P/E, ROE, D/E, EV/EBITDA, FCF — no need to define these.
2. analyst_summary: 60-70 words. Business overview, current market position, and one key thesis point. Concise and information-dense.
3. valuation_commentary: Compare P/E and P/B to sector averages. Mention forward P/E if available. Comment on whether the stock is cheap, fair or expensive vs peers.
4. financial_health: Cover gross margin, operating margin, ROE, FCF, and D/E. Note trends — improving or deteriorating?
5. growth_outlook: Revenue CAGR context, earnings trajectory, margin expansion or compression. Any catalyst or headwind.
6. risk_flags: Specific, data-driven risks. Reference actual numbers. "Operating margin compressed 200bps YoY" not "margins are low".
7. investor_profile: One precise sentence. What return profile does this suit — value, growth, GARP, dividend?
8. watch_out_for: Two specific things. Reference metrics or events — "watch for Q3 margin guidance given rising input costs."
9. Do NOT set traffic_light or traffic_light_reason — set both to "N/A".
10. news_context: What does the news mean for earnings or valuation? No hand-holding.

{output_format}"""

    # ── EXPERT ────────────────────────────────────────────────────────────────
    else:  # Expert / 🏦
        return f"""You are writing a professional equity research note for an experienced investor or analyst. They have deep market knowledge and expect technical precision.

{base_rules}

EXPERT WRITING RULES:
1. Write like a sell-side research note. Dense, precise, no hand-holding.
2. analyst_summary: 50-60 words maximum. Thesis-first: lead with the key investment consideration, not company description.
3. valuation_commentary: Reference EV/EBITDA, P/FCF, PEG alongside P/E and P/B. Comment on premium or discount to historical averages and sector peers. Is the current multiple justified by the growth profile?
4. financial_health: Cover EBITDA margins, FCF conversion, ROCE, interest coverage, and net debt/EBITDA. Flag any deterioration in capital allocation quality.
5. growth_outlook: Discuss revenue drivers, margin levers, and earnings quality. Note any divergence between reported earnings and FCF. Mention any cyclical or structural tailwinds/headwinds.
6. risk_flags: Four technical risks with data references. Include valuation risk, execution risk, macro sensitivity, and any balance sheet concern. Be specific: cite actual numbers.
7. investor_profile: One sentence. Frame it as a portfolio context — "suitable for growth-at-reasonable-price mandates with 18-24 month horizon."
8. watch_out_for: Two items. Focus on earnings quality signals, covenant triggers, or macro sensitivity. Reference specific metrics to track.
9. Do NOT set traffic_light or traffic_light_reason — set both to "N/A".
10. news_context: Assess the news through a valuation and earnings impact lens. What is the market likely to reprice?

{output_format}"""


# ── PORTFOLIO SYSTEM PROMPT ───────────────────────────────────────────────────
_PORTFOLIO_SYSTEM_PROMPT = """You are a portfolio analyst writing for retail investors.

RULES:
1. Never give buy, sell, or hold recommendations.
2. Use correct currency for each stock based on its exchange.
3. Use plain English. Explain any financial terms briefly in brackets.
4. Be honest about risks. Do not be overly optimistic.
5. Respond with ONLY a valid JSON object. No markdown. No backticks. No text outside the JSON.

OUTPUT FORMAT:
{
  "portfolio_summary": "3-4 sentences describing the portfolio as a whole",
  "sector_concentration": "2-3 sentences on diversification",
  "overall_health": "2-3 sentences on combined financial health",
  "portfolio_risks": ["risk 1", "risk 2", "risk 3"],
  "best_performing_stock": "stock name and why it stands out",
  "weakest_stock": "stock name and specific concerns",
  "portfolio_advice": "2-3 sentences of general observations",
  "watch_out_for": "2 sentences on the most important thing to monitor"
}"""


# ── FALLBACK BRIEF ────────────────────────────────────────────────────────────
def _fallback_brief(data: dict, signals: list, ticker: str) -> dict:
    from src.utils import get_currency_symbol, format_price
    currency = get_currency_symbol(ticker)
    price    = data.get("price")

    risk_flags = [s.replace("WARNING — ", "") for s in signals if "WARNING" in s]
    if not risk_flags:
        risk_flags = ["AI analysis unavailable — review signals manually"]

    return {
        "company_name":   data.get("name") or ticker,
        "sector":         data.get("sector") or "N/A",
        "traffic_light":  "N/A",
        "traffic_light_reason": "AI unavailable",
        "analyst_summary": (
            "Live AI analysis is temporarily unavailable. "
            "Key data from yfinance is shown below — please review the metrics and signals."
        ),
        "valuation_commentary": (
            f"P/E: {format_ratio(data.get('pe'))}  |  "
            f"P/B: {format_ratio(data.get('pb_ratio'))}  |  "
            f"EPS: {format_price(data.get('eps'), ticker)}."
        ),
        "financial_health": (
            f"ROE: {format_percent(data.get('roe'))}  |  "
            f"Profit Margin: {format_percent(data.get('profit_margin'))}  |  "
            f"Debt/Equity: {format_ratio(data.get('debt_to_equity'))}."
        ),
        "growth_outlook": (
            f"Revenue growth: {format_percent(data.get('revenue_growth'))}  |  "
            f"Earnings growth: {format_percent(data.get('earnings_growth'))}."
        ),
        "risk_flags":       risk_flags,
        "investor_profile": "Unable to generate — AI service unavailable.",
        "watch_out_for":    "Monitor the signals flagged above.",
        "news_context":     "News analysis unavailable during AI outage.",
        "annual_report_insights": None,
        "key_metrics": {
            "price":          format_price(price, ticker),
            "pe_ratio":       format_ratio(data.get("pe")),
            "pb_ratio":       format_ratio(data.get("pb_ratio")),
            "profit_margin":  format_percent(data.get("profit_margin")),
            "roe":            format_percent(data.get("roe")),
            "debt_to_equity": format_ratio(data.get("debt_to_equity")),
            "revenue_growth": format_percent(data.get("revenue_growth")),
            "one_year_return": (
                f"{data.get('price_change_1y'):+.2f}%"
                if data.get("price_change_1y") not in (None, "N/A")
                else "N/A"
            ),
        },
    }


# ── GENERATE STOCK BRIEF ──────────────────────────────────────────────────────
def generate_stock_brief(
    data:       dict,
    signals:    list,
    ticker:     str,
    vectorstore = None,
    lang:       str = "English",
    level:      str = "💼 Intermediate",
) -> dict:
    prompt = build_stock_prompt(data, signals, ticker)

    # News
    headlines = get_company_news(ticker)
    useful    = [h for h in headlines if not h.startswith(
        ("Could not", "News", "No recent", "NEWS_API", "news unavailable")
    )]
    if useful:
        news_text  = "\n".join(f"- {h}" for h in useful)
        prompt    += f"\n\nRECENT NEWS HEADLINES:\n{news_text}\nUse these to fill the news_context field."
    else:
        prompt    += "\n\nnews_context: No recent news available for this stock."

    # RAG
    if vectorstore is not None:
        try:
            rag_questions = [
                "What is the company strategy and future outlook?",
                "What are the key risks mentioned by management?",
                "What are the capital expenditure and growth plans?",
            ]
            seen   = set()
            chunks = []
            for q in rag_questions:
                results = vectorstore.similarity_search(q, k=2)
                for doc in results:
                    content = doc.page_content.strip()
                    if content not in seen:
                        seen.add(content)
                        page = doc.metadata.get("page", "?")
                        chunks.append(f"[Page {page}] {content}")
            if chunks:
                prompt += f"\n\nANNUAL REPORT INSIGHTS:\n" + "\n".join(chunks)
            else:
                prompt += "\n\nannual_report_insights: Annual report not loaded for this stock."
        except Exception:
            prompt += "\n\nannual_report_insights: Annual report data not available."
    else:
        prompt += "\n\nannual_report_insights: Annual report not loaded for this stock."

    system_prompt = _get_system_prompt(level, lang)

    try:
        response = call_groq_with_fallback(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": prompt},
            ],
            max_tokens=1800,
        )
        raw    = response.choices[0].message.content
        result = parse_json(raw)
        # Ensure traffic_light keys always exist
        result.setdefault("traffic_light", "N/A")
        result.setdefault("traffic_light_reason", "N/A")
        return result

    except json.JSONDecodeError as e:
        logger.warning("JSON parse failed: %s", e)
        return _fallback_brief(data, signals, ticker)
    except Exception as e:
        logger.warning("Groq call failed: %s", e)
        return _fallback_brief(data, signals, ticker)


# ── PORTFOLIO BRIEF ───────────────────────────────────────────────────────────
def generate_portfolio_brief(all_stock_data: list, lang: str = "English") -> dict:
    portfolio_text = ""
    sectors = set()
    for item in all_stock_data:
        d      = item["data"]
        sector = d.get("sector", "N/A") or "N/A"
        if sector != "N/A":
            sectors.add(sector)
        portfolio_text += (
            f"\nStock: {d.get('name', 'N/A')}"
            f"\nSector: {sector}"
            f"\n1-Year Return: {d.get('price_change_1y', 'N/A')}%"
            f"\nRevenue Growth: {format_percent(d.get('revenue_growth'))}"
            f"\nProfit Margin: {format_percent(d.get('profit_margin'))}"
            f"\nDebt to Equity: {format_ratio(d.get('debt_to_equity'))}"
            f"\nSignals: {', '.join(item.get('signals', []))}"
            "\n---"
        )
    prompt = (
        f"Analyse this portfolio of {len(all_stock_data)} stocks.\n\n"
        f"HOLDINGS:\n{portfolio_text}\n\n"
        f"Sectors: {', '.join(sectors) if sectors else 'N/A'}"
    )
    try:
        response = call_groq_with_fallback(
            messages=[
                {"role": "system", "content": _PORTFOLIO_SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            max_tokens=1800,
        )
        return parse_json(response.choices[0].message.content)
    except Exception:
        return {
            "portfolio_summary":     "Portfolio analysis temporarily unavailable.",
            "sector_concentration":  "N/A",
            "overall_health":        "N/A",
            "portfolio_risks":       ["AI service unavailable"],
            "best_performing_stock": "N/A",
            "weakest_stock":         "N/A",
            "portfolio_advice":      "Please try again in a few minutes.",
            "watch_out_for":         "N/A",
        }