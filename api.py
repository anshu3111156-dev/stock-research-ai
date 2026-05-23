import os
import yfinance as yf
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from src.data import get_stock_data, clean_data, analyse_history
from src.signals import basic_signal
from src.llm import generate_stock_brief, generate_portfolio_brief
from src.rag import load_faiss_index

load_dotenv()

app = FastAPI(title="Stock Research AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── LOAD RAG VECTORSTORE ONCE AT STARTUP ──

vectorstore = None
FAISS_INDEX_PATH = "data/faiss_index"

@app.on_event("startup")
def load_rag():
    global vectorstore
    if os.path.exists(FAISS_INDEX_PATH):
        try:
            print("Loading annual report index...")
            vectorstore = load_faiss_index()
            print("Annual report index loaded.")
        except Exception as e:
            print(f"Could not load RAG index: {e}")

# ── REQUEST MODELS ────────────────────────

class ResearchRequest(BaseModel):
    ticker: str

class PortfolioRequest(BaseModel):
    tickers: list[str]

# ── ENDPOINTS ─────────────────────────────

@app.get("/")
def root():
    return {"message": "Stock Research AI is running."}

@app.get("/health")
def health():
    return {"status": "ok", "rag_loaded": vectorstore is not None}

@app.post("/research")
def get_research(request: ResearchRequest):
    ticker = request.ticker.strip().upper()

    try:
        # Step 1 — fetch live data
        raw_data = get_stock_data(ticker)
        data     = clean_data(raw_data)
        signals  = basic_signal(data)
        history  = analyse_history(ticker)

        # Step 2 — fetch real price history for chart
        stock      = yf.Ticker(ticker)
        price_hist = stock.history(period="1y")
        price_data = {
            "dates":  price_hist.index.strftime("%Y-%m-%d").tolist(),
            "closes": price_hist["Close"].round(2).tolist(),
        }

        # Step 3 — generate AI brief with RAG
        brief = generate_stock_brief(data, signals, ticker, vectorstore)

        return {
            "ticker":     ticker,
            "brief":      brief,
            "history":    history,
            "signals":    signals,
            "price_data": price_data,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/portfolio")
def get_portfolio(request: PortfolioRequest):
    all_stock_data = []

    for ticker in request.tickers:
        ticker = ticker.strip().upper()
        try:
            data    = clean_data(get_stock_data(ticker))
            signals = basic_signal(data)
            history = analyse_history(ticker)
            brief   = generate_stock_brief(data, signals, ticker, vectorstore)

            all_stock_data.append({
                "ticker":  ticker,
                "data":    data,
                "signals": signals,
                "brief":   brief,
                "history": history,
            })
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            continue

    if not all_stock_data:
        raise HTTPException(status_code=400, detail="No valid tickers provided.")

    portfolio_brief = generate_portfolio_brief(all_stock_data)

    return {
        "stocks":          all_stock_data,
        "portfolio_brief": portfolio_brief,
    }

@app.post("/ask")
def ask_annual_report(request: dict):
    question = request.get("question", "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required.")
    if vectorstore is None:
        raise HTTPException(status_code=503, detail="Annual report index not loaded.")

    from src.rag import ask_annual_report as rag_ask
    answer = rag_ask(question, vectorstore)
    return {"question": question, "answer": answer}