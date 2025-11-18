# backend/main.py

from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from utils.rag_pipeline import build_prompt, call_ollama
from pathlib import Path

# ======================================================
# KONFIGURASI PATH
# ======================================================

BASE_DIR = Path(__file__).resolve().parent
VECTOR_DIR = BASE_DIR / "vectorstore"
COLLECTION = "mlibbot"

# ======================================================
# LOAD QDRANT LOCAL
# ======================================================

client = QdrantClient(path=str(VECTOR_DIR))

# ======================================================
# LOAD EMBEDDING MODEL
# ======================================================

EMBED = SentenceTransformer("all-MiniLM-L6-v2")

# ======================================================
# FASTAPI INIT
# ======================================================

app = FastAPI()

# ======================================================
# REQUEST BODY
# ======================================================

class ChatRequest(BaseModel):
    message: str
    top_k: int = 4


# ======================================================
# ENDPOINT CHATBOT RAG
# ======================================================

@app.post("/chat")
def chat(req: ChatRequest):
    # 1. embedding
    q = EMBED.encode(req.message).tolist()

    # 2. retrieve dokumen
    hits = client.search(
        collection_name=COLLECTION,
        query_vector=q,
        limit=req.top_k
    )

    contexts = [
        {
            "text": h.payload.get("text"),
            "source": h.payload.get("source"),
            "source_id": h.payload.get("source_id")
        }
        for h in hits
    ]

    # 3. build prompt RAG
    prompt = build_prompt(req.message, contexts)

    # 4. LLM (qwen2.5:0.5b)
    answer = call_ollama(prompt)

    return {
        "answer": answer,
        "sources": contexts
    }


# ======================================================
# ENDPOINT HEALTH TESTING
# ======================================================

@app.get("/health")
def health():
    return {"status": "ok", "vector_db": "qdrant", "llm": "qwen2.5:0.5b"}


# ======================================================
# ENDPOINT PENGUJIAN
# ======================================================

@app.post("/test/embed")
def test_embed(req: ChatRequest):
    vec = EMBED.encode(req.message).tolist()
    return {"embedding_first_10": vec[:10]}


@app.post("/test/retrieve")
def test_retrieve(req: ChatRequest):
    q = EMBED.encode(req.message).tolist()

    hits = client.search(
        collection_name=COLLECTION,
        query_vector=q,
        limit=req.top_k
    )

    return {
        "query": req.message,
        "results": [
            {
                "text": h.payload.get("text")[:300],
                "source": h.payload.get("source"),
                "source_id": h.payload.get("source_id")
            }
            for h in hits
        ]
    }


@app.post("/test/rag")
def test_rag(req: ChatRequest):
    q = EMBED.encode(req.message).tolist()

    hits = client.search(
        collection_name=COLLECTION,
        query_vector=q,
        limit=req.top_k
    )

    contexts = [
        {
            "text": h.payload.get("text"),
            "source": h.payload.get("source"),
            "source_id": h.payload.get("source_id")
        }
        for h in hits
    ]

    prompt = build_prompt(req.message, contexts)
    answer = call_ollama(prompt)

    return {
        "query": req.message,
        "prompt": prompt,
        "answer": answer,
        "sources": contexts
    }


@app.get("/test/ask")
def test_ask(q: str, top_k: int = 4):
    emb = EMBED.encode([q]).tolist()[0]

    hits = client.search(
        collection_name=COLLECTION,
        query_vector=emb,
        limit=top_k
    )

    contexts = [
        {
            "text": h.payload.get("text"),
            "source": h.payload.get("source"),
            "source_id": h.payload.get("source_id")
        }
        for h in hits
    ]

    prompt = build_prompt(q, contexts)
    answer = call_ollama(prompt)

    return {"answer": answer, "sources": contexts}
