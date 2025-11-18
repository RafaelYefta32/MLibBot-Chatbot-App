import pdfplumber
import pandas as pd

def load_pdf(path: str):
    """Ekstrak teks dari PDF per halaman."""
    texts = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            texts.append({"text": text, "source": "pdf", "source_id": f"page_{i+1}"})
    return texts


def load_excel(path: str):
    """Load katalog buku dari Excel."""
    df = pd.read_excel(path)

    rows = []
    for idx, row in df.iterrows():
        combined = " | ".join([str(x) for x in row.tolist()])
        rows.append({
            "text": combined,
            "source": "excel",
            "source_id": f"row_{idx+1}"
        })

    return rows
