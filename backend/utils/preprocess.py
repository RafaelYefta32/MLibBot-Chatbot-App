import re
import unicodedata
from typing import List

# buang karakter kontrol aneh
re_ctrl = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

# samakan variasi unicode yang sering muncul di PDF
map_punct = {
    "\u2018": "'", "\u2019": "'", "\u201A": "'",
    "\u201C": '"', "\u201D": '"', "\u201E": '"',
    "\u2013": "-", "\u2014": "-", "\u2212": "-",
    "\u00A0": " ",  # non-breaking space
}

# token BM25: huruf/angka (cukup robust utk Indo + ISBN + angka)
re_token_bm25 = re.compile(r"[0-9A-Za-zÀ-ÖØ-öø-ÿ]+")

def _normalize_unicode(text: str) -> str:
    # NFKC: normalisasi bentuk unicode (fullwidth, dsb)
    return unicodedata.normalize("NFKC", text)

def _replace_punct(text: str) -> str:
    for k, v in map_punct.items():
        text = text.replace(k, v)
    return text

def _fix_pdf_hyphenation(text: str) -> str:
    """
    Perbaiki pemenggalan kata:
    'perpu-\nstakaan' -> 'perpustakaan'
    """
    return re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)

def _cleanup_base(text: str) -> str:
    if not text:
        return ""

    text = str(text)
    text = _normalize_unicode(text)
    text = _replace_punct(text)

    # samain newline
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _fix_pdf_hyphenation(text)

    # buang kontrol
    text = re_ctrl.sub(" ", text)

    # rapihin whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text

def clean_text(text: str) -> str:
    """
    Cleaning untuk dokumen (PDF/Excel) & text umum.
    Tidak lower-case (nama orang, judul, dsb).
    """
    return _cleanup_base(text)

def clean_query(text: str) -> str:
    """
    - lower
    - rapihin huruf berulang panjang
    - normalisasi istilah umum
    """
    t = _cleanup_base(text).lower()

    # "lamaaa": "lamaa"
    t = re.sub(r"([a-zA-Z])\1{2,}", r"\1\1", t)

    # normalisasi istilah umum
    replacements = {
    # perpustakaan
    "perpus": "perpustakaan",
    "perpust": "perpustakaan",
    "perpustakaan maranatha": "perpustakaan universitas kristen maranatha",
    "ukm": "universitas kristen maranatha", 
    "marnat": "Universitas Kristen Maranatha",
    "e-journal": "ejournal",
    "e journal": "ejournal",
    "ejurnal": "ejournal",
    "e-jurnal": "ejournal",
    "e-resource": "eresource",
    "e resource": "eresource",
    "e-resources": "eresource",
    "e-book": "ebook",
    "e book": "ebook",
    "ebook": "ebook",
    "e-books": "ebook",
    "ta": "tugas akhir",
    "t.a": "tugas akhir",
    "skripsi": "skripsi",
    "thesis": "tesis",
    "booking": "pemesanan",
    "reservasi": "pemesanan",
    "reserve": "pemesanan",
    "pinjem": "pinjam",
    "minjem": "pinjam",
    "ngembaliin": "mengembalikan",
    "balikin": "mengembalikan",
    "perpanjang": "perpanjangan",
    "renew": "perpanjangan",
    "extend": "perpanjangan",
    "wa": "whatsapp",
    "w/a": "whatsapp",
    "whats app": "whatsapp",
    "ig": "instagram",
    "insta": "instagram",
    "telp": "telepon",
    "no hp": "nomor hp",
    "hp": "handphone",
    "telat": "terlambat",
    "denda": "denda",
    }

    for k, v in replacements.items():
        t = re.sub(rf"\b{re.escape(k)}\b", v, t)

    return t

def tokenize_bm25(text: str) -> List[str]:
    t = clean_query(text)
    return re_token_bm25.findall(t)