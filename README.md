```markdown
# 📈 Stock Research AI

🔗 **Live Demo:** https://stock-research-ai-bjktsdzcadpaqgwxj4njfd.streamlit.app

An AI-powered stock research tool that fetches live financial data from 30+ global exchanges, pulls real-time news headlines, and generates structured equity research briefs using Groq's Llama 3.3 model. Built for retail investors who want clear, jargon-free analysis of any listed company worldwide.

---

## Features

- Live stock data from NSE, BSE, NYSE, NASDAQ, LSE, and 25+ more exchanges via yfinance
- Auto-detects currency — ₹ for Indian stocks, $ for US, £ for UK, € for Europe, and more
- Real-time news headlines fetched per stock using NewsAPI
- Rule-based signal logic across 8+ financial metrics — P/E, ROE, debt, margins, momentum
- AI-generated analyst briefs in structured JSON using Groq's Llama 3.3
- Portfolio-level analysis — sector concentration, risk flags, best and worst performers
- Interactive price chart with 50-day and 200-day moving averages
- Financial glossary explaining every metric in plain English
- Streamlit web interface — no terminal needed
- All reports saved as JSON, TXT, and CSV in an organised output folder

---

## Project Structure

```
stock-research-ai/
├── app.py               
├── main.py              
├── requirements.txt     
├── .env                 
└── src/
    ├── data.py          
    ├── signals.py       
    ├── llm.py           
    └── utils.py         
```

---

## Tech Stack

Python · Streamlit · Plotly · yfinance · Groq API · Llama 3.3 · NewsAPI · Pandas · Threading · python-dotenv

---

## Setup

Clone the repository
```
git clone https://github.com/anshu3111156-dev/stock-research-ai.git
cd stock-research-ai
```

Install dependencies
```
pip install -r requirements.txt
```

Create a `.env` file in the root folder
```
GROQ_API_KEY=your-groq-key-here
NEWS_API_KEY=your-newsapi-key-here
```

Free Groq key — console.groq.com
Free NewsAPI key — newsapi.org

Run the web app
```
python -m streamlit run app.py
```

Or run the terminal version
```
python main.py
```

---

## Supported Exchanges

| Exchange | Example Tickers |
|---|---|
| NSE India | RELIANCE.NS · INFY.NS · HDFCBANK.NS · TATAMOTORS.NS |
| BSE India | WIPRO.BO · ZOMATO.BO |
| NYSE / NASDAQ | TSLA · NVDA · MSFT · BLK |
| London (LSE) | SHEL.L · HSBA.L |
| Germany (XETRA) | SAP.DE · BMW.DE |
| Japan (TSE) | 7203.T · 6758.T |
| Hong Kong | 0700.HK · 9988.HK |
| Australia | BHP.AX · CBA.AX |

---

## Output

Each run generates the following inside `portfolio_report/`

```
TICKER.json              structured AI brief
TICKER.txt               readable report with all sections
comparison_table.csv     side by side metrics for all stocks
portfolio_summary.txt    combined portfolio level analysis
```

---

*Built by Anshika Singh · Electronics Engineering · Banasthali Vidyapith*
*Not financial advice*
```
