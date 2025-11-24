import re

def clean_text(text: str) -> str:
    if not text:
        return ""
    # buang karakter kontrol aneh
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
    # normalisasi spasi
    text = re.sub(r"\s+", " ", text)
    return text.strip()
