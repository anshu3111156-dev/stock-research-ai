def basic_signal(data):
    signals = []

    if data['pe'] != "N/A":
        pe = float(data['pe'])
        sector = str(data['sector'])
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

    if data['revenue_growth'] != "N/A":
        rg = float(data['revenue_growth'])
        if rg > 0.20:        signals.append("STRONG revenue growth (>20% YoY)")
        elif rg > 0.10:      signals.append("HEALTHY revenue growth (10-20% YoY)")
        elif 0 < rg <= 0.10: signals.append("SLOW revenue growth (<10% YoY)")
        elif rg < 0:         signals.append("WARNING — revenue shrinking YoY")

    if data['earnings_growth'] != "N/A":
        eg = float(data['earnings_growth'])
        if eg < -0.20:  signals.append("WARNING — earnings fell >20% YoY")
        elif eg > 0.25: signals.append("STRONG earnings growth (>25% YoY)")

    if data['profit_margin'] != "N/A":
        pm = float(data['profit_margin'])
        if pm < 0:      signals.append("WARNING — loss-making company")
        elif pm < 0.05: signals.append("THIN profit margins (<5%)")
        elif pm > 0.20: signals.append("STRONG profit margins (>20%)")

    if data['roe'] != "N/A":
        roe = float(data['roe'])
        if roe > 0.20:   signals.append("HIGH ROE (>20%) — efficiently using shareholder capital")
        elif roe < 0.08: signals.append("LOW ROE (<8%) — not generating enough return on equity")

    if data['debt_to_equity'] != "N/A":
        de = float(data['debt_to_equity'])
        if "Financial" not in str(data['sector']):
            if de > 150:  signals.append("VERY HIGH debt-to-equity — significant financial risk")
            elif de > 80: signals.append("ELEVATED debt-to-equity — monitor debt levels")
            elif de < 10: signals.append("VERY LOW debt — strong balance sheet")

    if data['price_change_1y'] != "N/A":
        pc = float(data['price_change_1y'])
        if pc > 50:    signals.append("VERY STRONG momentum — up >50% in last year")
        elif pc > 25:  signals.append("STRONG momentum — up >25% in last year")
        elif pc < -30: signals.append("WARNING — stock down >30% in last year")
        elif pc < -15: signals.append("WEAK momentum — down >15% in last year")

    if data['pb_ratio'] != "N/A":
        pb = float(data['pb_ratio'])
        if pb < 1:    signals.append("TRADING BELOW BOOK VALUE — bargain or value trap")
        elif pb > 20: signals.append("HIGH P/B — market pricing in strong intangible value")

    if not signals:
        signals.append("No strong signals — stock appears fairly valued")

    return signals