from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models
from utils.text_loader import load_pdf, load_excel
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

VECTOR_DIR = BASE_DIR / "vectorstore"
VECTOR_DIR.mkdir(exist_ok=True)

COLLECTION = "mlibbot"

print("Memuat model embedding...")
MODEL = SentenceTransformer("all-MiniLM-L6-v2")

print("Menghubungkan Qdrant local...")
client = QdrantClient(path=str(VECTOR_DIR))

print("Membaca data katalog...")
excel_docs = load_excel(DATA_DIR / "hasil_catalog_v1.xlsx")

print("Membaca data PDF operasional...")
pdf_docs = load_pdf(DATA_DIR / "data_operasional_mlibbot_perpustakaan_maranatha_v1.pdf")

docs = excel_docs + pdf_docs
print(f"Total dokumen: {len(docs)}")

# Hapus collection lama
client.recreate_collection(
    collection_name=COLLECTION,
    vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
)

print("Melakukan embedding dan upload ke Qdrant...")
for i, d in enumerate(docs):
    vec = MODEL.encode(d["text"]).tolist()

    client.upsert(
        collection_name=COLLECTION,
        points=[
            models.PointStruct(
                id=i,
                vector=vec,
                payload=d
            )
        ]
    )

print("Vectorstore berhasil dibuat!")
