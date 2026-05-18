# Stock Research AI

An AI-powered stock research tool that fetches live financial data from global exchanges, pulls real-time news headlines, and generates structured equity research briefs using Groq's Llama 3.3 model. Built for retail investors who want clear, jargon-free analysis of any listed company.

---

## Features

- Live stock data from NSE, BSE, and NYSE via yfinance
- Real-time news headlines fetched per stock using NewsAPI
- Rule-based signal logic across 8+ financial metrics — P/E, ROE, debt, margins, momentum
- AI-generated analyst briefs in structured JSON using Groq's Llama 3.3
- Portfolio-level analysis — sector concentration, risk flags, best and worst performers
- Financial glossary explaining every metric in plain English
- Mid-run STOP support using threading — halts cleanly between stocks
- All reports saved as JSON, TXT, and CSV in an organised output folder

---

## Project Structure

```
stock-research-ai/
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

Python · yfinance · Groq API · Llama 3.3 · NewsAPI · Pandas · Threading · python-dotenv

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

Run
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

Built by Anshika Singh · Electronics Engineering · Banasthali Vidyapith
