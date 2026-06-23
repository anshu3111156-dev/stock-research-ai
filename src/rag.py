import os
from groq import Groq
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

REPORTS_DIR = "data/reports"
INDEXES_DIR = "data/faiss_indexes"

# Maps ticker -> PDF filename (without .pdf)
TICKER_TO_REPORT = {
    "RELIANCE.NS":  "reliance_ns",
    "TCS.NS":       "tcs_ns",
    "INFY.NS":      "infy_ns",
    "HDFCBANK.NS":  "hdfcbank_ns",
    "WIPRO.NS":     "wipro_ns",
}

_embeddings = None  # cached embedding model, loaded once per process


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    return _embeddings


def load_and_chunk_pdf(pdf_path: str):
    loader = PyPDFLoader(pdf_path)
    pages  = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    return splitter.split_documents(pages)


def build_index_for_ticker(ticker: str):
    report_name = TICKER_TO_REPORT.get(ticker.upper())
    if not report_name:
        return None

    pdf_path   = os.path.join(REPORTS_DIR, f"{report_name}.pdf")
    index_path = os.path.join(INDEXES_DIR, report_name)

    if not os.path.exists(pdf_path):
        return None

    chunks      = load_and_chunk_pdf(pdf_path)
    embeddings  = get_embeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)

    os.makedirs(INDEXES_DIR, exist_ok=True)
    vectorstore.save_local(index_path)
    return vectorstore


def load_index_for_ticker(ticker: str):
    report_name = TICKER_TO_REPORT.get(ticker.upper())
    if not report_name:
        return None

    index_path = os.path.join(INDEXES_DIR, report_name)
    pdf_path   = os.path.join(REPORTS_DIR, f"{report_name}.pdf")

    if not os.path.exists(pdf_path):
        return None

    embeddings = get_embeddings()

    if os.path.exists(index_path):
        try:
            return FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
        except Exception:
            pass

    return build_index_for_ticker(ticker)


def build_all_indexes():
    for ticker in TICKER_TO_REPORT:
        print(f"Building index for {ticker}...")
        vs = build_index_for_ticker(ticker)
        print(f"  Done: {ticker}" if vs else f"  Skipped (no PDF found): {ticker}")


def has_report(ticker: str) -> bool:
    report_name = TICKER_TO_REPORT.get(ticker.upper())
    if not report_name:
        return False
    return os.path.exists(os.path.join(REPORTS_DIR, f"{report_name}.pdf"))


def ask_annual_report(question: str, vectorstore) -> str:
    results = vectorstore.similarity_search(question, k=8)
    context = ""
    for doc in results:
        page = doc.metadata.get('page', '?')
        context += f"\n[Page {page}]\n{doc.page_content}\n"

    prompt = f"""You are a senior equity research analyst helping a retail investor understand a company's annual report.

Answer the question below using ONLY the context provided. Use all relevant context, piece together info from multiple sections if needed.
Mention page numbers where you found information. Use simple English.
If the answer is not in the context, say so clearly.

CONTEXT FROM ANNUAL REPORT:
{context}

QUESTION: {question}

ANSWER:"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=800
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    build_all_indexes()