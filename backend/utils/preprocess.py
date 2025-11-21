# backend/utils/preprocess.py

import re

def clean_text(text: str) -> str:
    if not text:
        return ""
    # Buang karakter kontrol aneh
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
    # Normalize multiple spaces
    text = re.sub(r"\s+", " ", text)
    return text.strip()
