import json
from pathlib import Path
import faiss 
import numpy as np
import joblib
from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from utils.rag_pipeline import build_prompt, call_groq
from utils.intent import predict_intent, predict_intent_proba #, predict_intent_conf

base = Path(__file__).resolve().parent
vector_dir = base / "vectorstore"
indobert_model = "LazarusNLP/all-indobert-base-v4"
bm25 = joblib.load(vector_dir / "bm25.pkl")
indo_embeddings = np.load(vector_dir / "indo_embeddings.npy")
faiss_indo_index = faiss.read_index(str(vector_dir / "faiss_indo.index"))
embed_model = SentenceTransformer(indobert_model)

with open(vector_dir / "docs.json", encoding="utf-8") as f:
    docs = json.load(f)

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

# baru
# def test_intent(req: IntentRequest):
#     label, score, proba = predict_intent_conf(req.message)
#     threshold = 0.6
#     if score >= threshold:
#         effective_intent = label
#         low_confidence = False
#     else:
#         effective_intent = "lainnya"
#         low_confidence = True

#     return {
#         "message": req.message,
#         "raw_intent": label,
#         "effective_intent": effective_intent,
#         "confidence": score,
#         "threshold": threshold,
#         "low_confidence": low_confidence,
#         "proba": proba,
#     }

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
        doc = docs[int(i)]
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
        doc = docs[int(i)]
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
        doc = docs[int(i)]
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
        "docs_count": len(docs),
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
