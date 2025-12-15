import json
from pathlib import Path
import faiss 
import numpy as np
import joblib
from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from utils.rag_pipeline import build_prompt, call_groq
from utils.intent import predict_intent_conf
from utils.preprocess import clean_query, tokenize_bm25

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

class ChatRequest(BaseModel):
    message: str
    top_k: int = 4
    # "bm25", "faiss', "hybrid"
    method: str = "hybrid"

def retrieve_bm25(query: str, top_k: int):
    tokens = tokenize_bm25(query)
    scores = bm25.get_scores(tokens)
    idxs = np.argsort(scores)[::-1][:top_k]

    results = []
    for i in idxs:
        doc = docs[int(i)]
        results.append({
            "text": doc["text"],
            "source": doc["source"],
            "source_id": doc["source_id"],
            "score": float(scores[i]),
        })
    return results

def retrieve_faiss(query: str, top_k: int):
    q = clean_query(query)
    q_emb = embed_model.encode(
        [q],
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype(np.float32)

    scores, idxs = faiss_indo_index.search(q_emb, top_k)
    scores = scores[0]
    idxs = idxs[0]

    results = []
    for score, i in zip(scores, idxs):
        doc = docs[int(i)]
        results.append({
            "text": doc["text"],
            "source": doc["source"],
            "source_id": doc["source_id"],
            "score": float(score),
        })
    return results

# # hybrid faiss search 
def retrieve_hybrid(query: str, top_k: int, alpha: float = 0.5, pool_mul: int = 10, pool_min: int = 50):
    pool = max(top_k * pool_mul, pool_min)

    # BM25 scores untuk docs
    tokens = tokenize_bm25(query)
    bm25_scores_all = bm25.get_scores(tokens)  # panjang = len(docs)
    bm25_top_idxs = np.argsort(bm25_scores_all)[::-1][:pool]

    # FAISS search (semantic) untuk top pool
    q = clean_query(query)
    q_emb = embed_model.encode([q], convert_to_numpy=True, normalize_embeddings=True).astype(np.float32)

    faiss_scores, faiss_idxs = faiss_indo_index.search(q_emb, pool)
    faiss_scores = faiss_scores[0]
    faiss_idxs = faiss_idxs[0]
    default_faiss = float(faiss_scores.min()) if len(faiss_scores) else 0.0

    # map: idx -> score
    faiss_score_map = {int(i): float(s) for i, s in zip(faiss_idxs, faiss_scores) if int(i) >= 0}
    # union kandidat
    candidate_idxs = list(set(map(int, bm25_top_idxs)) | set(faiss_score_map.keys()))
    # ambil skor untuk kandidat aja
    bm25_cand = np.array([float(bm25_scores_all[i]) for i in candidate_idxs], dtype=np.float32)
    faiss_cand = np.array([float(faiss_score_map.get(i, default_faiss)) for i in candidate_idxs], dtype=np.float32)
    # normalisasi
    def norm(x: np.ndarray) -> np.ndarray:
        x_min = float(x.min()) if len(x) else 0.0
        x_max = float(x.max()) if len(x) else 0.0
        if x_max - x_min < 1e-9:
            return np.zeros_like(x)
        return (x - x_min) / (x_max - x_min)

    bm25_n = norm(bm25_cand)
    faiss_n = norm(faiss_cand)

    hybrid = alpha * bm25_n + (1.0 - alpha) * faiss_n

    # sort kandidat berdasarkan hybrid desc, ambil top_k
    order = np.argsort(hybrid)[::-1][:top_k]

    results = []
    for rank_pos in order:
        i = candidate_idxs[int(rank_pos)]
        doc = docs[i]
        results.append({
            "text": doc.get("text"),
            "source": doc.get("source"),
            "source_id": doc.get("source_id"),
            "score_bm25": float(bm25_scores_all[i]),
            "score_faiss": float(faiss_score_map.get(i, default_faiss)),
            "score_hybrid": float(hybrid[int(rank_pos)]),
        })
    return results

@app.get("/")
def root():
    return {
        "message": "MLibBot API nih brow",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
def health():
    return {
        "status": "ok",
        "vector_db": "bm25 + indoBERT+faiss",
        "docs_count": len(docs),
    }

@app.post("/test/intent")
def test_intent(req: IntentRequest):
    label, score, percent, proba = predict_intent_conf(req.message)
    return {
        "message": req.message,
        "intent": label,
        "confidence": score,          # 0-1
        "confidence_percent": percent, # 0-100
        "proba": proba
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

@app.post("/test/prompt")
def test_prompt(req: ChatRequest):
    # ambil contexts sesuai method
    if req.method == "bm25":
        contexts = retrieve_bm25(req.message, req.top_k)
    elif req.method == "faiss":
        contexts = retrieve_faiss(req.message, req.top_k)
    else:
        contexts = retrieve_hybrid(req.message, req.top_k)

    prompt = build_prompt(req.message, contexts)
    return {"query": req.message, "method": req.method, "prompt": prompt, "contexts": contexts}


@app.post("/chat")
def chat(req: ChatRequest):
    label, score, percent, proba = predict_intent_conf(req.message)

    if req.method == "bm25":
        contexts = retrieve_bm25(req.message, req.top_k)
    elif req.method == "faiss":
        contexts = retrieve_faiss(req.message, req.top_k)
    else:  # hybrid
        contexts = retrieve_hybrid(req.message, req.top_k)

    prompt = build_prompt(req.message, contexts)
    answer = call_groq(prompt)

    return {
        "answer": answer,
        "method": req.method,            
        "top_k_requested": req.top_k,
        "intent": {
            "label": label,
            "confidence": score,              # 0-1
            "confidence_percent": percent,    # 0-100
            "proba": proba
        },
        "sources": contexts
    }