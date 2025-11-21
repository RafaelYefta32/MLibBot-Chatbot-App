import os
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from sentence_transformers import SentenceTransformer
import pdfplumber, pandas as pd
from pathlib import Path
from utils.splitter import chunk_text
from utils.preprocess import clean_text

os.environ["SENTENCE_TRANSFORMERS_HOME"] = "D:/model embedding"
BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
VECTOR = BASE / "vectorstore"
VECTOR.mkdir(exist_ok=True)

CATALOG = DATA / "hasil_catalog_v1.xlsx"
PDF = DATA / "data_operasional_mlibbot_perpustakaan_maranatha_v1.pdf"

EMBED = SentenceTransformer("intfloat/multilingual-e5-base") # model embedding

client = QdrantClient(path=str(VECTOR))  # local file-based storage

COLLECTION_NAME = "mlibbot"

def recreate_collection():
    if COLLECTION_NAME in client.get_collections().collections:
        client.delete_collection(COLLECTION_NAME)

    client.create_collection(
        COLLECTION_NAME,
        vectors_config=VectorParams(size=768, distance=Distance.COSINE)
    )

def ingest_catalog():
    df = pd.read_excel(CATALOG)
    df.columns = [c.lower().strip() for c in df.columns]
    docs = []

    for i, row in df.iterrows():
        text = clean_text(
            f"Judul: {row.get('title','')}\n,"
            f"Penulis: {row.get('authors','')}\n,"
            f"Tahun: {row.get('year','')}\n,"
            f"ISBN: {row.get('isbn','')}\n,"
            f"Penerbit: {row.get('publisher','')}\n,"
            f"Bahasa: {row.get('language','')},"
            f"Lokasi: {row.get('location','')},"
            f"Status: {row.get('availability','')},"
        )
        docs.append(("catalog_"+str(i), text, {"source":"catalog","source_id":str(i)}))
    return docs

def ingest_pdf():
    docs = []
    with pdfplumber.open(PDF) as pdf:
        for p, page in enumerate(pdf.pages):
            raw = clean_text(page.extract_text() or "")
            chunks = chunk_text(raw, 200, 50)
            for i, ch in enumerate(chunks):
                docs.append((f"pdf_{p}_{i}", ch, {"source":"pdf","source_id":f"p{p}_c{i}"}))
    return docs

def main():
    recreate_collection()
    all_docs = ingest_catalog() + ingest_pdf()

    vectors = []
    points = []

    for idx, (pid, text, meta) in enumerate(all_docs):
        emb = EMBED.encode(text).tolist()
        points.append(
            PointStruct(id=idx, vector=emb, payload={"text": text, **meta})
        )

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print("[OK] Ingest Qdrant selesai.")

if __name__ == "__main__":
    main()
