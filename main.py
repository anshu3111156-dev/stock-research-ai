import json
import os
import time
import threading
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv, find_dotenv

from src.data import get_stock_data, clean_data, analyse_history
from src.signals import basic_signal
from src.llm import generate_stock_brief, generate_portfolio_brief
from src.utils import format_percent, format_ratio

load_dotenv(find_dotenv())

OUTPUT_FOLDER = "portfolio_report"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ── FINANCIAL GLOSSARY ────────────────────

FINANCIAL_GLOSSARY = {
    "P/E Ratio (Price to Earnings)": "How much investors are paying for every ₹1 of company profit. Lower can mean cheaper, but check the sector average.",
    "P/B Ratio (Price to Book)":     "Compares stock price to the company's net assets. Below 1 means trading cheaper than its assets are worth.",
    "EPS (Earnings Per Share)":      "Profit earned per single share. Higher is better — shows the company is actually making money.",
    "ROE (Return on Equity)":        "How efficiently the company uses shareholder money to generate profit. Above 15% is generally considered good.",
    "Debt to Equity":                "How much debt the company carries vs shareholder funds. Very high levels mean more financial risk.",
    "Profit Margin":                 "What percentage of revenue actually becomes profit after all costs. Higher margin = more efficient business.",
    "Revenue Growth (YoY)":          "How much the company's sales grew compared to last year. Consistent growth above 10% is healthy.",
    "Earnings Growth (YoY)":         "How much the company's profits grew compared to last year. Should ideally grow faster than revenue.",
    "52-Week High/Low":              "The highest and lowest price the stock traded at in the past year. Useful to see where current price sits.",
    "Moving Average (MA50/MA200)":   "Average price over last 50 or 200 days. Price above MA200 generally signals positive long-term trend.",
    "Volatility":                    "How much the stock price moves daily on average. Higher volatility means higher risk and reward potential.",
    "Market Cap":                    "Total market value of the company. Large cap above ₹20,000 Crore, mid cap ₹5,000-20,000, small cap below.",
}

# ── PRINT FUNCTIONS ───────────────────────

def print_glossary():
    print("\n" + "="*55)
    print("  📖 FINANCIAL TERMS GLOSSARY")
    print("="*55)
    for term, definition in FINANCIAL_GLOSSARY.items():
        print(f"\n  {term}")
        print(f"  → {definition}")
    print("\n" + "="*55)

def print_stock_brief(brief, history):
    print("\n" + "="*55)
    print(f"  {brief['company_name'].upper()}")
    print(f"  Sector: {brief['sector']}")
    print("="*55)
    print("\n📌 ANALYST SUMMARY")
    print(brief['analyst_summary'])
    print("\n💰 VALUATION COMMENTARY")
    print(brief['valuation_commentary'])
    print("\n📊 FINANCIAL HEALTH")
    print(brief['financial_health'])
    print("\n📈 GROWTH OUTLOOK")
    print(brief['growth_outlook'])
    print("\n⚠️  RISK FLAGS")
    for i, risk in enumerate(brief['risk_flags'], 1):
        print(f"  {i}. {risk}")
    print("\n👤 INVESTOR PROFILE")
    print(brief['investor_profile'])
    print("\n🔍 WATCH OUT FOR")
    print(brief['watch_out_for'])
    print("\n📰 NEWS CONTEXT")
    print(brief.get('news_context', 'No recent news available.'))
    print("\n📋 KEY METRICS")
    for key, value in brief['key_metrics'].items():
        print(f"  {key.replace('_',' ').title():<20} {value}")
    if history:
        print("\n📉 PRICE HISTORY (1 YEAR)")
        print(f"  52-Week High:   ₹{history['high_52w']:,.2f}")
        print(f"  52-Week Low:    ₹{history['low_52w']:,.2f}")
        print(f"  Avg Price:      ₹{history['avg_price']:,.2f}")
        print(f"  Volatility:     {history['volatility']}% daily")
        print(f"  50-Day MA:      ₹{history['ma50']:,.2f}  — {history['ma50_signal']}")
        print(f"  200-Day MA:     ₹{history['ma200']:,.2f} — {history['ma200_signal']}")
    print("="*55)

def print_portfolio_brief(brief):
    print("\n" + "="*55)
    print("  PORTFOLIO ANALYSIS")
    print("="*55)
    print("\n📁 PORTFOLIO SUMMARY")
    print(brief['portfolio_summary'])
    print("\n🏢 SECTOR CONCENTRATION")
    print(brief['sector_concentration'])
    print("\n💪 OVERALL HEALTH")
    print(brief['overall_health'])
    print("\n⚠️  PORTFOLIO RISKS")
    for i, risk in enumerate(brief['portfolio_risks'], 1):
        print(f"  {i}. {risk}")
    print("\n🏆 BEST PERFORMING STOCK")
    print(f"  {brief['best_performing_stock']}")
    print("\n🔴 WEAKEST STOCK")
    print(f"  {brief['weakest_stock']}")
    print("\n💡 PORTFOLIO OBSERVATIONS")
    print(brief['portfolio_advice'])
    print("\n🔍 WATCH OUT FOR")
    print(brief['watch_out_for'])
    print("="*55)

# ── SAVE FUNCTIONS ────────────────────────

def save_stock_report(ticker, brief, signals, history):
    json_path = os.path.join(OUTPUT_FOLDER, f"{ticker.replace('.','_')}.json")
    txt_path  = os.path.join(OUTPUT_FOLDER, f"{ticker.replace('.','_')}.txt")

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(brief, f, indent=2, ensure_ascii=False)

    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(f"STOCK REPORT — {brief['company_name']}\n")
        f.write(f"Generated: {datetime.now().strftime('%d %b %Y %I:%M %p')}\n")
        f.write("="*55 + "\n\n")
        f.write(f"ANALYST SUMMARY\n{brief['analyst_summary']}\n\n")
        f.write(f"VALUATION\n{brief['valuation_commentary']}\n\n")
        f.write(f"FINANCIAL HEALTH\n{brief['financial_health']}\n\n")
        f.write(f"GROWTH OUTLOOK\n{brief['growth_outlook']}\n\n")
        f.write("RISK FLAGS\n")
        for i, r in enumerate(brief['risk_flags'], 1):
            f.write(f"  {i}. {r}\n")
        f.write(f"\nINVESTOR PROFILE\n{brief['investor_profile']}\n\n")
        f.write(f"WATCH OUT FOR\n{brief['watch_out_for']}\n\n")
        f.write(f"NEWS CONTEXT\n{brief.get('news_context', 'No recent news available.')}\n\n")
        if history:
            f.write("PRICE HISTORY\n")
            f.write(f"  52-Week High: ₹{history['high_52w']:,.2f}\n")
            f.write(f"  52-Week Low:  ₹{history['low_52w']:,.2f}\n")
            f.write(f"  Volatility:   {history['volatility']}%\n")
            f.write(f"  Signals: {', '.join(signals)}\n")

    print(f"  Saved → {json_path}")
    print(f"  Saved → {txt_path}")

def save_portfolio_report(brief, tickers):
    path = os.path.join(OUTPUT_FOLDER, "portfolio_summary.txt")
    with open(path, 'w', encoding='utf-8') as f:
        f.write("PORTFOLIO ANALYSIS REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%d %b %Y %I:%M %p')}\n")
        f.write(f"Stocks: {', '.join(tickers)}\n")
        f.write("="*55 + "\n\n")
        f.write(f"PORTFOLIO SUMMARY\n{brief['portfolio_summary']}\n\n")
        f.write(f"SECTOR CONCENTRATION\n{brief['sector_concentration']}\n\n")
        f.write(f"OVERALL HEALTH\n{brief['overall_health']}\n\n")
        f.write("PORTFOLIO RISKS\n")
        for i, r in enumerate(brief['portfolio_risks'], 1):
            f.write(f"  {i}. {r}\n")
        f.write(f"\nBEST STOCK: {brief['best_performing_stock']}\n")
        f.write(f"WEAKEST STOCK: {brief['weakest_stock']}\n\n")
        f.write(f"OBSERVATIONS\n{brief['portfolio_advice']}\n\n")
        f.write(f"WATCH OUT FOR\n{brief['watch_out_for']}\n")
    print(f"  Portfolio report saved → {path}")

def print_comparison_table(all_stock_data):
    rows = []
    for item in all_stock_data:
        d = item['data']
        rows.append({
            "Company":     d['name'],
            "Price":       d['price'],
            "PE":          d['pe'],
            "PB":          d['pb_ratio'],
            "Rev Growth":  d['revenue_growth'],
            "Margin":      d['profit_margin'],
            "ROE":         d['roe'],
            "D/E":         d['debt_to_equity'],
            "1Y Return %": d['price_change_1y'],
        })
    df = pd.DataFrame(rows).set_index("Company").round(2)
    csv_path = os.path.join(OUTPUT_FOLDER, "comparison_table.csv")
    df.to_csv(csv_path)
    print("\n" + "="*55)
    print("  STOCK COMPARISON TABLE")
    print("="*55)
    print(df.to_string())
    print(f"\n  Saved → {csv_path}")

# ── MAIN ──────────────────────────────────

print("\n" + "="*55)
print("  STOCK RESEARCH AI — by Anshika Singh")
print("  Powered by yfinance + Groq (Llama 3.3)")
print("="*55)

print("\nEnter NSE stock tickers one by one.")
print("Examples: RELIANCE.NS  INFY.NS  HDFCBANK.NS")
print("Type DONE when finished.\n")

tickers = []
while True:
    ticker = input("Enter ticker: ").strip().upper()
    if ticker == "DONE":
        if len(tickers) == 0:
            print("Please enter at least one ticker.")
            continue
        break
    if ticker:
        tickers.append(ticker)
        print(f"  Added {ticker}. Enter next or type DONE.")

print(f"\nAnalysing {len(tickers)} stock(s)...\n")

stop_flag = threading.Event()

def listen_for_stop():
    while not stop_flag.is_set():
        user_input = input()
        if user_input.strip().upper() == "STOP":
            print("\n  ⛔ STOP received — finishing current stock then halting...")
            stop_flag.set()
            break

listener_thread = threading.Thread(target=listen_for_stop, daemon=True)
listener_thread.start()

print("  (Type STOP and press Enter anytime to halt)\n")

all_stock_data = []

for ticker in tickers:
    if stop_flag.is_set():
        print(f"  Skipping {ticker} — stopped by user.")
        continue

    print(f"\n{'─'*55}")
    print(f"  Processing: {ticker}")
    print('─'*55)

    try:
        if stop_flag.is_set(): raise InterruptedError
        data    = clean_data(get_stock_data(ticker))
        signals = basic_signal(data)

        if stop_flag.is_set(): raise InterruptedError
        history = analyse_history(ticker)

        if stop_flag.is_set(): raise InterruptedError
        print("  Fetching news & generating AI brief...")
        brief = generate_stock_brief(data, signals, ticker)

        if stop_flag.is_set(): raise InterruptedError
        print_stock_brief(brief, history)
        save_stock_report(ticker, brief, signals, history)

        all_stock_data.append({
            "ticker":  ticker,
            "data":    data,
            "signals": signals,
            "brief":   brief,
            "history": history
        })

        if len(tickers) > 1 and not stop_flag.is_set():
            time.sleep(2)

    except InterruptedError:
        print(f"  ⛔ {ticker} interrupted — partial data not saved.")
    except json.JSONDecodeError:
        print(f"  JSON parsing failed for {ticker}")
    except Exception as e:
        print(f"  Error processing {ticker}: {e}")

stop_flag.set()

if len(all_stock_data) > 1:
    print_comparison_table(all_stock_data)

# print glossary once after all stocks
print_glossary()

if len(all_stock_data) >= 1:
    print("\n\nGenerating portfolio analysis...")
    try:
        portfolio_brief = generate_portfolio_brief(all_stock_data)
        print_portfolio_brief(portfolio_brief)
        save_portfolio_report(portfolio_brief, tickers)
    except Exception as e:
        print(f"  Portfolio analysis failed: {e}")

print(f"\nAll files saved in: {OUTPUT_FOLDER}/")
print("Done.\n")