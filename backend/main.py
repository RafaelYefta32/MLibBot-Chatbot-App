import os
from dotenv import load_dotenv
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List
from bson import ObjectId

import faiss 
import numpy as np
import joblib
from sentence_transformers import SentenceTransformer

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from jose import JWTError, jwt

from utils.rag_pipeline import build_prompt, call_groq
from utils.intent import predict_intent_conf
from utils.preprocess import clean_query, tokenize_bm25

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "mlibbot_db")
SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise ValueError("No SECRET_KEY set for application")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

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

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]
users_collection = db["users"]
chat_sessions_collection = db["chat_sessions"]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserRegister(BaseModel):
    fullName: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    fullName: str
    email: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class UserUpdate(BaseModel):
    fullName: str
    email: EmailStr

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str

class IntentRequest(BaseModel):
    message: str

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    top_k: int = 4
    # "bm25", "faiss', "hybrid"
    method: str = "hybrid"

class ChatMessageModel(BaseModel):
    role: str
    content: str
    timestamp: datetime

class CreateSessionRequest(BaseModel):
    title: Optional[str] = None

class SessionResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int

class SessionDetailResponse(BaseModel):
    id: str
    title: str
    messages: List[dict]
    created_at: datetime
    updated_at: datetime

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user_id(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
    except JWTError:
        return None
    
    user = await users_collection.find_one({"email": email})
    return str(user["_id"]) if user else None

@app.post("/auth/register", response_model=UserResponse)
async def register(user: UserRegister):
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user.password)
    
    new_user = {
        "fullName": user.fullName,
        "email": user.email,
        "password": hashed_password,
        "created_at": datetime.utcnow()
    }
    result = await users_collection.insert_one(new_user)
    
    return {
        "id": str(result.inserted_id),
        "fullName": new_user["fullName"],
        "email": new_user["email"]
    }

@app.post("/auth/login", response_model=Token)
async def login(user: UserLogin):
    db_user = await users_collection.find_one({"email": user.email})
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    if not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    access_token = create_access_token(data={"sub": db_user["email"]})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(db_user["_id"]),
            "fullName": db_user["fullName"],
            "email": db_user["email"]
        }
    }

@app.put("/auth/profile", response_model=UserResponse)
async def update_profile(
    user_data: UserUpdate, 
    user_id: str = Depends(get_current_user_id)
):
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    existing_user = await users_collection.find_one({
        "email": user_data.email, 
        "_id": {"$ne": ObjectId(user_id)} 
    })
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already in use by another account")

    await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"fullName": user_data.fullName, "email": user_data.email}}
    )

    return {
        "id": user_id,
        "fullName": user_data.fullName,
        "email": user_data.email
    }

@app.put("/auth/password")
async def update_password(
    pwd_data: PasswordUpdate, 
    user_id: str = Depends(get_current_user_id)
):
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_db = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user_db:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(pwd_data.current_password, user_db["password"]):
        raise HTTPException(status_code=400, detail="Incorrect current password")

    new_hashed_password = get_password_hash(pwd_data.new_password)
    
    await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"password": new_hashed_password}}
    )

    return {"message": "Password updated successfully"}

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await users_collection.find_one({"email": email})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
        
    return {
        "id": str(user["_id"]),
        "fullName": user["fullName"],
        "email": user["email"]
    }

@app.post("/chat/sessions", response_model=SessionResponse)
async def create_chat_session(
    req: CreateSessionRequest,
    user_id: str = Depends(get_current_user_id)
):
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    now = datetime.utcnow()
    new_session = {
        "user_id": user_id,
        "title": req.title or "Percakapan Baru",
        "messages": [],
        "created_at": now,
        "updated_at": now
    }
    
    result = await chat_sessions_collection.insert_one(new_session)
    
    return {
        "id": str(result.inserted_id),
        "title": new_session["title"],
        "created_at": new_session["created_at"],
        "updated_at": new_session["updated_at"],
        "message_count": 0
    }

@app.get("/chat/sessions", response_model=List[SessionResponse])
async def list_chat_sessions(user_id: str = Depends(get_current_user_id)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    sessions = await chat_sessions_collection.find(
        {"user_id": user_id}
    ).sort("updated_at", -1).to_list(100)
    
    return [
        {
            "id": str(s["_id"]),
            "title": s["title"],
            "created_at": s["created_at"],
            "updated_at": s["updated_at"],
            "message_count": len(s.get("messages", []))
        }
        for s in sessions
    ]

@app.get("/chat/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_chat_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id)
):
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    session = await chat_sessions_collection.find_one({
        "_id": ObjectId(session_id),
        "user_id": user_id
    })
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "id": str(session["_id"]),
        "title": session["title"],
        "messages": session.get("messages", []),
        "created_at": session["created_at"],
        "updated_at": session["updated_at"]
    }

@app.delete("/chat/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id)
):
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    result = await chat_sessions_collection.delete_one({
        "_id": ObjectId(session_id),
        "user_id": user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session deleted successfully"}

@app.put("/chat/sessions/{session_id}/title")
async def update_session_title(
    session_id: str,
    req: CreateSessionRequest,
    user_id: str = Depends(get_current_user_id)
):
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    result = await chat_sessions_collection.update_one(
        {"_id": ObjectId(session_id), "user_id": user_id},
        {"$set": {"title": req.title, "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Title updated successfully"}

def _dedupe_key(hit: dict) -> str:
    if hit.get("source") == "catalog":
        # satu buku = satu parent_id
        if hit.get("parent_id"):
            return str(hit["parent_id"])
        # fallback kalau parent_id kosong: potong s0/s1
        return str(hit.get("source_id", "")).split("_s")[0]

    # pdf: per chunk unik
    return f'{hit.get("source")}::{hit.get("source_id")}'

def dedupe(hits: list, top_k: int) -> list:
    seen = set()
    out = []
    for h in hits:
        key = _dedupe_key(h)
        if key in seen:
            continue
        seen.add(key)
        out.append(h)
        if len(out) >= top_k:
            break
    return out

def retrieve_bm25(query: str, top_k: int):
    pool = 16

    tokens = tokenize_bm25(query)
    scores = bm25.get_scores(tokens)
    idxs = np.argsort(scores)[::-1][:pool]  

    results = []
    for i in idxs:
        doc = docs[int(i)]
        results.append({
            "text": doc["text"],
            "source": doc["source"],
            "source_id": doc["source_id"],
            "parent_id": doc.get("parent_id"), 
            "score": float(scores[i]),
        })

    return dedupe(results, top_k)

def retrieve_faiss(query: str, top_k: int):
    pool = 16

    q = clean_query(query)
    q_emb = embed_model.encode([q], convert_to_numpy=True, normalize_embeddings=True).astype(np.float32)

    scores, idxs = faiss_indo_index.search(q_emb, pool) 
    scores = scores[0]
    idxs = idxs[0]

    results = []
    for score, i in zip(scores, idxs):
        if int(i) < 0:
            continue
        doc = docs[int(i)]
        results.append({
            "text": doc["text"],
            "source": doc["source"],
            "source_id": doc["source_id"],
            "parent_id": doc.get("parent_id"), 
            "score": float(score),
        })

    return dedupe(results, top_k)


# # hybrid faiss search 
def retrieve_hybrid(query: str, top_k: int, alpha: float = 0.5, pool_mul: int = 10, pool_min: int = 40):
    pool = max(top_k * pool_mul, pool_min)

    # BM25 scores untuk docs
    tokens = tokenize_bm25(query)
    bm25_scores_all = bm25.get_scores(tokens) 
    bm25_top_idxs = np.argsort(bm25_scores_all)[::-1][:pool]

    # FAISS search (semantic) untuk top pool
    q = clean_query(query)
    q_emb = embed_model.encode([q], convert_to_numpy=True, normalize_embeddings=True).astype(np.float32)

    faiss_scores, faiss_idxs = faiss_indo_index.search(q_emb, pool)
    faiss_scores = faiss_scores[0]
    faiss_idxs = faiss_idxs[0]
    default_faiss = float(faiss_scores.min()) if len(faiss_scores) else 0.0

    # map: idx - score
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

    order = np.argsort(hybrid)[::-1]

    results = []
    for rank_pos in order:
        i = candidate_idxs[int(rank_pos)]
        doc = docs[i]
        results.append({
            "text": doc.get("text"),
            "source": doc.get("source"),
            "source_id": doc.get("source_id"),
            "parent_id": doc.get("parent_id"),
            "score_bm25": float(bm25_scores_all[i]),
            "score_faiss": float(faiss_score_map.get(i, default_faiss)),
            "score_hybrid": float(hybrid[int(rank_pos)]),
        })
    return dedupe(results, top_k)

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
    faiss_hits = retrieve_faiss(req.message, req.top_k)
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
async def chat(req: ChatRequest):
    label, score, percent, proba = predict_intent_conf(req.message)

    if req.method == "bm25":
        contexts = retrieve_bm25(req.message, req.top_k)
    elif req.method == "faiss":
        contexts = retrieve_faiss(req.message, req.top_k)
    else:  # hybrid
        contexts = retrieve_hybrid(req.message, req.top_k)

    prompt = build_prompt(req.message, contexts)
    answer = call_groq(prompt)

    if req.session_id:
        now = datetime.utcnow()
        user_msg = {
            "role": "user",
            "content": req.message,
            "timestamp": now.isoformat()
        }
        bot_msg = {
            "role": "bot",
            "content": answer,
            "timestamp": now.isoformat(),
            "metadata": {
                "source": contexts[0].get("source") if contexts else None,
                "intent": label,
                "probability": percent,
                "score": contexts[0].get("score_hybrid") if contexts else None
            }
        }
        
        session = await chat_sessions_collection.find_one({"_id": ObjectId(req.session_id)})
        update_data = {
            "$push": {"messages": {"$each": [user_msg, bot_msg]}},
            "$set": {"updated_at": now}
        }
        
        if session and session.get("title") == "Percakapan Baru" and len(session.get("messages", [])) == 0:
            auto_title = req.message[:30] + ("..." if len(req.message) > 30 else "")
            update_data["$set"]["title"] = auto_title
        
        await chat_sessions_collection.update_one(
            {"_id": ObjectId(req.session_id)},
            update_data
        )

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