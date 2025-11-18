# backend/utils/splitter.py
"""
Fungsi chunking sederhana: memecah teks panjang menjadi potongan
berukuran tertentu (by word) sehingga embedding lebih efektif.
"""
import re
from typing import List

def chunk_text(text: str, chunk_size: int = 250, overlap: int = 50) -> List[str]:
    """
    Split text into chunks of approx chunk_size words with overlap.
    """
    # normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    words = text.split(" ")
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i:i+chunk_size]
        chunks.append(" ".join(chunk))
        i += chunk_size - overlap
    return chunks
