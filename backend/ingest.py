import json
from pathlib import Path
import numpy as np
import pandas as pd
import pdfplumber
import faiss 
from rank_bm25 import BM25Okapi 
import joblib
from sentence_transformers import SentenceTransformer
from utils.preprocess import clean_text, tokenize_bm25
from utils.splitter import chunk_text

base = Path(__file__).resolve().parent
data = base / "data"
vector_dir = base / "vectorstore"
vector_dir.mkdir(exist_ok=True)

catalog = data / "hasil_catalog_v4_blank_generated.xlsx"
pdf_path = data / "data_operasional_mlibbot_perpustakaan_maranatha_v1.pdf"

indobert_model = "LazarusNLP/all-indobert-base-v4"

def load_docs():
    docs = []
    # 1) katalog Excel
    df = pd.read_excel(catalog)
    df.columns = [c.lower().strip() for c in df.columns]

    for i, row in df.iterrows():
        # pake id asli
        raw_id = str(row.get("id", "")).strip()
        parent_id = f"cat_{raw_id}" if raw_id else f"row_{i+1}"

        title = str(row.get("title", "")).strip()
        authors = str(row.get("authors", "")).strip()
        year = str(row.get("year", "")).strip()
        isbn = str(row.get("isbn", "")).strip()
        publisher = str(row.get("publisher", "")).strip()
        language = str(row.get("language", "")).strip()
        location = str(row.get("location", "")).strip()
        availability = str(row.get("availability", "")).strip()
        detail_url = str(row.get("detail_url", "")).strip()
        thumbnail_url = str(row.get("thumbnail_url", "")).strip()
        keyword = str(row.get("keyword", "")).strip()
        synopsis = str(row.get("synopsis", "")).strip()

        # doc meta (1 buku = 1 doc)
        meta_text = clean_text(
            f"Judul: {title}\n"
            f"Penulis: {authors}\n"
            f"Tahun: {year}\n"
            f"ISBN: {isbn}\n"
            f"Penerbit: {publisher}\n"
            f"Bahasa: {language}\n"
            f"Lokasi: {location}\n"
            f"Status: {availability}\n"
            f"Kata kunci: {keyword}\n"
        )
        docs.append({
            "text": meta_text,
            "source": "catalog",
            "doc_kind": "catalog_meta",
            "source_id": parent_id,
            "parent_id": parent_id,
            "title": title,
            "authors": authors,
            "year": year,
            "isbn": isbn,
            "publisher": publisher,
            "language": language,
            "location": location,
            "availability": availability,
            "detail_url": detail_url,
            "thumbnail_url": thumbnail_url,
            "keyword": keyword,
        })

        # doc sinopsis di-chunk (1 buku bisa banyak doc)
        syn_clean = clean_text(synopsis)
        syn_chunks = chunk_text(syn_clean, chunk_size=200, overlap=50)

        for si, ch in enumerate(syn_chunks):
            syn_text = clean_text(
                f"Judul: {title}\n"
                f"Penulis: {authors}\n"
                f"Tahun: {year}\n"
                f"ISBN: {isbn}\n"
                f"Lokasi: {location}\n"
                f"Status: {availability}\n"
                f"Kata kunci: {keyword}\n"
                f"Sinopsis: {ch}\n"
            )
            docs.append({
                "text": syn_text,
                "source": "catalog",
                "doc_kind": "catalog_synopsis",
                "source_id": f"{parent_id}_s{si}",

                # link ke parent
                "parent_id": parent_id,
                "title": title,
                "authors": authors,
                "year": year,
                "isbn": isbn,
                "location": location,
                "availability": availability,
                "detail_url": detail_url,
                "thumbnail_url": thumbnail_url,
                "keyword": keyword,
            })

    # 2) PDF operasional
    with pdfplumber.open(pdf_path) as pdf_obj:
        for p, page in enumerate(pdf_obj.pages):
            raw = clean_text(page.extract_text() or "")
            chunks = chunk_text(raw, 200, 50)
            for ci, ch in enumerate(chunks):
                docs.append(
                    {
                        "text": ch,
                        "source": "pdf",
                        "doc_kind": "pdf_chunk",
                        "source_id": f"p{p+1}_c{ci}",
                    }
                )
    return docs

def main():
    docs = load_docs()
    print(f"[INFO] Total dokumen: {len(docs)}")

    texts = [d["text"] for d in docs]

    print("[INFO] Bangun index BM25...")
    tokens = [tokenize_bm25(t) for t in texts]
    bm25 = BM25Okapi(tokens)
    joblib.dump(bm25, vector_dir / "bm25.pkl")

    print("[INFO] Bangun embedding IndoBERT...")
    model = SentenceTransformer(indobert_model)

    indo_embeddings = model.encode(
        texts,
        batch_size=16,
        convert_to_numpy=True,
        show_progress_bar=True,
        normalize_embeddings=True,
    ).astype(np.float32)

    np.save(vector_dir / "indo_embeddings.npy", indo_embeddings)

    print("[INFO] Bangun index FAISS IndoBERT...")
    dim_indo = indo_embeddings.shape[1]
    faiss_indo_index = faiss.IndexFlatIP(dim_indo)
    faiss_indo_index.add(indo_embeddings)
    faiss.write_index(faiss_indo_index, str(vector_dir / "faiss_indo.index"))

    with open(vector_dir / "docs.json", "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)

    print("[INFO] Ingest selesai. BM25 dan IndoBERT+FAISS siap dipakai.")

if __name__ == "__main__":
    main()