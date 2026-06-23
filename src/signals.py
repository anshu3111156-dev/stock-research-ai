def _f(value):
    """Safely coerce to float, return None on failure or N/A."""
    if value == "N/A" or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def basic_signal(data):
    signals = []

    pe = _f(data.get('pe'))
    if pe is not None:
        sector = str(data.get('sector', ''))
        if "Financial" in sector or "Bank" in sector:
            if pe < 8:    signals.append("LOW P/E for a bank — possibly undervalued")
            elif pe > 20: signals.append("HIGH P/E for a bank — unusual, check NPA levels")
        elif "Technology" in sector:
            if pe < 15:   signals.append("LOW P/E for a tech company — possibly undervalued or declining")
            elif pe > 50: signals.append("HIGH P/E — priced for very high growth, verify earnings")
        elif "Consumer" in sector:
            if pe < 25:   signals.append("LOW P/E for consumer sector — possibly undervalued")
            elif pe > 80: signals.append("VERY HIGH P/E — market pricing in significant growth")
        else:
            if pe < 12:   signals.append("LOW P/E — possibly undervalued, check why")
            elif pe > 45: signals.append("HIGH P/E — priced for high growth or overvalued")

    rg = _f(data.get('revenue_growth'))
    if rg is not None:
        if rg > 0.20:        signals.append("STRONG revenue growth (>20% YoY)")
        elif rg > 0.10:      signals.append("HEALTHY revenue growth (10-20% YoY)")
        elif 0 < rg <= 0.10: signals.append("SLOW revenue growth (<10% YoY)")
        elif rg < 0:         signals.append("WARNING — revenue shrinking YoY")

    eg = _f(data.get('earnings_growth'))
    if eg is not None:
        if eg < -0.20:  signals.append("WARNING — earnings fell >20% YoY")
        elif eg > 0.25: signals.append("STRONG earnings growth (>25% YoY)")

    pm = _f(data.get('profit_margin'))
    if pm is not None:
        if pm < 0:      signals.append("WARNING — loss-making company")
        elif pm < 0.05: signals.append("THIN profit margins (<5%)")
        elif pm > 0.20: signals.append("STRONG profit margins (>20%)")

    roe = _f(data.get('roe'))
    if roe is not None:
        if roe > 0.20:   signals.append("HIGH ROE (>20%) — efficiently using shareholder capital")
        elif roe < 0.08: signals.append("LOW ROE (<8%) — not generating enough return on equity")

    de = _f(data.get('debt_to_equity'))
    if de is not None and "Financial" not in str(data.get('sector', '')):
        if de > 150:  signals.append("VERY HIGH debt-to-equity — significant financial risk")
        elif de > 80: signals.append("ELEVATED debt-to-equity — monitor debt levels")
        elif de < 10: signals.append("VERY LOW debt — strong balance sheet")

    pc = _f(data.get('price_change_1y'))
    if pc is not None:
        if pc > 50:    signals.append("VERY STRONG momentum — up >50% in last year")
        elif pc > 25:  signals.append("STRONG momentum — up >25% in last year")
        elif pc < -30: signals.append("WARNING — stock down >30% in last year")
        elif pc < -15: signals.append("WEAK momentum — down >15% in last year")

    pb = _f(data.get('pb_ratio'))
    if pb is not None:
        if pb < 1:    signals.append("TRADING BELOW BOOK VALUE — bargain or value trap")
        elif pb > 20: signals.append("HIGH P/B — market pricing in strong intangible value")

    rec = str(data.get('recommendation', '')).lower()
    if rec in ("buy", "strong_buy", "strongbuy"):
        signals.append("ANALYST CONSENSUS: BUY")

    dy = _f(data.get('dividend_yield'))
    if dy is not None:
        if dy > 0.04:
            signals.append("HIGH dividend yield (>4%)")
        elif dy > 0:
            signals.append("Pays dividend")

    if not signals:
        signals.append("No strong signals — stock appears fairly valued")

    return signals