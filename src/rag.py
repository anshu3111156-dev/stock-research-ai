import os
from groq import Groq
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

PDF_PATH         = "data/reliance_annual_report.pdf"
FAISS_INDEX_PATH = "data/faiss_index"

# ── STEP 1: LOAD + CHUNK ──────────────────

def load_and_chunk_pdf(pdf_path: str = PDF_PATH):
    print("  Loading PDF...")
    loader = PyPDFLoader(pdf_path)
    pages  = loader.load()
    print(f"  Total pages loaded: {len(pages)}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,      # bigger chunks = more context
        chunk_overlap=100     # more overlap = less info lost at edges
    )
    chunks = splitter.split_documents(pages)
    print(f"  Total chunks created: {len(chunks)}")
    return chunks

# ── STEP 2: EMBEDDINGS + FAISS ────────────

def build_faiss_index(chunks):
    print("\n  Loading embedding model...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    print("  Building FAISS index...")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(FAISS_INDEX_PATH)
    print(f"  FAISS index saved to: {FAISS_INDEX_PATH}")
    return vectorstore

def load_faiss_index():
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    vectorstore = FAISS.load_local(
        FAISS_INDEX_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )
    return vectorstore

def get_vectorstore(force_rebuild: bool = False):
    if not force_rebuild and os.path.exists(FAISS_INDEX_PATH):
        print("  Loading existing FAISS index...")
        return load_faiss_index()
    else:
        chunks = load_and_chunk_pdf()
        return build_faiss_index(chunks)

# ── STEP 3: RETRIEVE + ASK LLM ───────────

def ask_annual_report(question: str, vectorstore) -> str:
    # Fetch more chunks for better coverage
    results = vectorstore.similarity_search(question, k=8)

    # Build context from chunks with page numbers
    context = ""
    for i, doc in enumerate(results):
        page = doc.metadata.get('page', '?')
        context += f"\n[Page {page}]\n{doc.page_content}\n"

    prompt = f"""You are a senior equity research analyst helping a retail investor understand a company's annual report.

Your job is to answer the question below using the context provided from the annual report.

RULES:
1. Use ALL the context provided — piece together the answer from multiple sections if needed
2. If the exact answer is not present, give the closest relevant information you can find
3. Always mention page numbers where you found the information
4. Use simple English — explain like you're talking to a first time investor
5. If truly nothing relevant exists in the context, say so clearly

CONTEXT FROM ANNUAL REPORT:
{context}

QUESTION: {question}

ANSWER (be detailed and helpful):"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=800
    )
    return response.choices[0].message.content


# ── MAIN: INTERACTIVE Q&A ─────────────────

if __name__ == "__main__":
    print("\n" + "="*55)
    print("  ANNUAL REPORT Q&A — Reliance Industries")
    print("="*55)

    # Force rebuild with new better chunk settings
    vectorstore = get_vectorstore(force_rebuild=True)

    print("\n  FAISS index ready. Ask anything about the annual report.")
    print("  Type EXIT to quit.\n")

    while True:
        question = input("Your question: ").strip()
        if question.upper() == "EXIT":
            print("Bye!")
            break
        if not question:
            continue

        print("\n  Searching annual report...")
        answer = ask_annual_report(question, vectorstore)
        print("\n" + "="*55)
        print(answer)
        print("="*55 + "\n")