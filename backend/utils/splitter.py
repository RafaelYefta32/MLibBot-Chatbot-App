import re
from typing import List

def chunk_text(text: str, chunk_size: int = 200, overlap: int = 50) -> List[str]:
    text = re.sub(r"\s+", " ", text).strip()
    words = text.split(" ")
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i:i+chunk_size]
        chunks.append(" ".join(chunk))
        i += chunk_size - overlap
    return chunks
