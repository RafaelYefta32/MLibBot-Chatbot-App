import json
from pathlib import Path

import faiss
import numpy as np
import joblib
from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

from utils.rag_pipeline import build_prompt, call_groq
from utils.intent import predict_intent, predict_intent_proba


BASE_DIR = Path(__file__).resolve().parent
VECTOR_DIR = BASE_DIR / "vectorstore"

INDOBERT_MODEL_NAME = "LazarusNLP/all-indobert-base-v4"

bm25 = joblib.load(VECTOR_DIR / "bm25.pkl")

# faiss_tfidf_index = faiss.read_index(str(VECTOR_DIR / "faiss_tfidf.index"))

indo_embeddings = np.load(VECTOR_DIR / "indo_embeddings.npy")
faiss_indo_index = faiss.read_index(str(VECTOR_DIR / "faiss_indo.index"))
embed_model = SentenceTransformer(INDOBERT_MODEL_NAME)

with open(VECTOR_DIR / "docs.json", encoding="utf-8") as f:
    DOCS = json.load(f)

app = FastAPI()

class IntentRequest(BaseModel):
    message: str

@app.post("/test/intent")
def test_intent(req: IntentRequest):
    label = predict_intent(req.message)
    proba = predict_intent_proba(req.message)
    return {
        "message": req.message,
        "intent": label,
        "proba": proba
    }

class ChatRequest(BaseModel):
    message: str
    top_k: int = 4
    # "bm25", "faiss', "hybrid"
    method: str = "hybrid"

def retrieve_bm25(query: str, top_k: int):
    """Retrieval pakai BM25 (lexical)."""
    tokens = query.lower().split()
    scores = bm25.get_scores(tokens)
    idxs = np.argsort(scores)[::-1][:top_k]

    results = []
    for i in idxs:
        doc = DOCS[int(i)]
        results.append(
            {
                "text": doc["text"],
                "source": doc["source"],
                "source_id": doc["source_id"],
                "score": float(scores[i]),
            }
        )
    return results


def retrieve_faiss(query: str, top_k: int):
    """
    Retrieval utama: IndoBERT + FAISS (semantic search).
    """
    q_emb = embed_model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype(np.float32)

    scores, idxs = faiss_indo_index.search(q_emb, top_k)
    scores = scores[0]
    idxs = idxs[0]

    results = []
    for score, i in zip(scores, idxs):
        doc = DOCS[int(i)]
        results.append(
            {
                "text": doc["text"],
                "source": doc["source"],
                "source_id": doc["source_id"],
                "score": float(score),
            }
        )
    return results


def retrieve_hybrid(query: str, top_k: int, alpha: float = 0.5):
    # alpha = bobot BM25 (0.5 50% BM25, 50% IndoBERT)
    # --- skor BM25 untuk semua dokumen ---
    tokens = query.lower().split()
    bm25_scores = bm25.get_scores(tokens)  # shape (n_docs,)

    q_emb = embed_model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype(np.float32)[0]  # (dim,)

    faiss_scores = indo_embeddings @ q_emb  # cosine similarity per dokumen

    def norm(x):
        x = np.array(x, dtype=np.float32)
        x_min = float(x.min())
        x_max = float(x.max())
        if x_max - x_min < 1e-9:
            return np.zeros_like(x)
        return (x - x_min) / (x_max - x_min)

    bm25_n = norm(bm25_scores)
    faiss_n = norm(faiss_scores)

    hybrid = alpha * bm25_n + (1.0 - alpha) * faiss_n

    idxs = np.argsort(hybrid)[::-1][:top_k]

    results = []
    for i in idxs:
        doc = DOCS[int(i)]
        results.append(
            {
                "text": doc["text"],
                "source": doc["source"],
                "source_id": doc["source_id"],
                "score_bm25": float(bm25_scores[i]),
                "score_faiss": float(faiss_scores[i]),
                "score_hybrid": float(hybrid[i]),
            }
        )
    return results


@app.get("/health")
def health():
    return {
        "status": "ok",
        "vector_db": "bm25 + indoBERT+faiss",
        "docs_count": len(DOCS),
    }


@app.post("/test/retrieve")
def test_retrieve(req: ChatRequest):
    if req.method == "bm25":
        hits = retrieve_bm25(req.message, req.top_k)
    elif req.method == "faiss":
        hits = retrieve_faiss(req.message, req.top_k)
    else:  # "hybrid"
        hits = retrieve_hybrid(req.message, req.top_k)
    return {"query": req.message, "results": hits}


@app.post("/test/compare")
def test_compare(req: ChatRequest):
    bm25_hits = retrieve_bm25(req.message, req.top_k)
    faiss_hits = retrieve_faiss(req.message, req.top_k)      # IndoBERT
    hybrid_hits = retrieve_hybrid(req.message, req.top_k)

    return {
        "query": req.message,
        "bm25": bm25_hits,
        "faiss_indobert": faiss_hits,
        "hybrid": hybrid_hits,
    }


@app.post("/chat")
def chat(req: ChatRequest):
    # minimal 8 konteks
    effective_k = max(req.top_k, 8)

    if req.method == "bm25":
        contexts = retrieve_bm25(req.message, effective_k)
    elif req.method == "faiss":
        contexts = retrieve_faiss(req.message, effective_k)
    else:  # hybrid
        contexts = retrieve_hybrid(req.message, effective_k)

    prompt = build_prompt(req.message, contexts)
    answer = call_groq(prompt)

    return {"answer": answer, "sources": contexts}
