import json
from pathlib import Path
import numpy as np
import pandas as pd
import pdfplumber
import faiss 
from rank_bm25 import BM25Okapi 
import joblib
from sentence_transformers import SentenceTransformer
from utils.preprocess import clean_text
from utils.splitter import chunk_text

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
VECTOR_DIR = BASE / "vectorstore"
VECTOR_DIR.mkdir(exist_ok=True)

CATALOG = DATA / "hasil_catalog_v2.xlsx"
PDF = DATA / "data_operasional_mlibbot_perpustakaan_maranatha_v1.pdf"

INDOBERT_MODEL_NAME = "LazarusNLP/all-indobert-base-v4"

def load_docs():
    docs = []

    # 1) katalog Excel
    df = pd.read_excel(CATALOG)
    df.columns = [c.lower().strip() for c in df.columns]

    for i, row in df.iterrows():
        text = clean_text(
            f"Judul: {row.get('title','')}\n"
            f"Penulis: {row.get('authors','')}\n"
            f"Tahun: {row.get('year','')}\n"
            f"ISBN: {row.get('isbn','')}\n"
            f"Penerbit: {row.get('publisher','')}\n"
            f"Bahasa: {row.get('language','')}\n"
            f"Lokasi: {row.get('location','')}\n"
            f"Status: {row.get('availability','')}\n"
        )
        docs.append(
            {"text": text, "source": "catalog", "source_id": f"row_{i+1}"}
        )

    # 2) PDF operasional
    with pdfplumber.open(PDF) as pdf:
        for p, page in enumerate(pdf.pages):
            raw = clean_text(page.extract_text() or "")
            chunks = chunk_text(raw, 200, 50)
            for ci, ch in enumerate(chunks):
                docs.append(
                    {
                        "text": ch,
                        "source": "pdf",
                        "source_id": f"p{p+1}_c{ci}",
                    }
                )

    return docs

def tokenize(text: str):
    return text.lower().split()

def main():
    docs = load_docs()
    print(f"[INFO] Total dokumen: {len(docs)}")

    texts = [d["text"] for d in docs]
    tokens = [tokenize(t) for t in texts]

    print("[INFO] Bangun index BM25...")
    bm25 = BM25Okapi(tokens)
    joblib.dump(bm25, VECTOR_DIR / "bm25.pkl")

    print("[INFO] Bangun embedding IndoBERT...")
    model = SentenceTransformer(INDOBERT_MODEL_NAME)

    indo_embeddings = model.encode(
        texts,
        batch_size=16,
        convert_to_numpy=True,
        show_progress_bar=True,
        normalize_embeddings=True,  # L2-normalized
    ).astype(np.float32)

    np.save(VECTOR_DIR / "indo_embeddings.npy", indo_embeddings)

    print("[INFO] Bangun index FAISS IndoBERT...")
    dim_indo = indo_embeddings.shape[1]
    faiss_indo_index = faiss.IndexFlatIP(dim_indo)
    faiss_indo_index.add(indo_embeddings)
    faiss.write_index(faiss_indo_index, str(VECTOR_DIR / "faiss_indo.index"))

    with open(VECTOR_DIR / "docs.json", "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)

    print("[INFO] Ingest selesai. BM25 dan IndoBERT+FAISS siap dipakai.")

if __name__ == "__main__":
    main()