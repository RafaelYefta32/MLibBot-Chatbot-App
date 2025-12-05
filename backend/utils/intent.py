from pathlib import Path
import re
import joblib

from .preprocess import clean_text  

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "model"  

INTENT_MODEL_PATH = MODEL_DIR / "intent_model_logreg_tfidf.pkl"

intent_pipeline = joblib.load(INTENT_MODEL_PATH)

def _preprocess_intent(text: str) -> str:
    text = clean_text(text)

    if not isinstance(text, str):
        text = str(text)

    text = text.lower()
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    text = re.sub(r"[^0-9a-zA-ZÀ-ÿ\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def predict_intent(text: str) -> str:
    s = _preprocess_intent(text)
    return intent_pipeline.predict([s])[0]


def predict_intent_proba(text: str):
    s = _preprocess_intent(text)
    proba = intent_pipeline.predict_proba([s])[0]
    labels = intent_pipeline.classes_
    return dict(zip(labels, proba))
