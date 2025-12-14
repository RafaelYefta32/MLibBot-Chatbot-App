from pathlib import Path
import re
import joblib
from .preprocess import clean_text  

base = Path(__file__).resolve().parent.parent
model_dir = base / "model"  
intent_model = "logreg_tfidf"  #"logreg_tfidf", "logreg_indobert"
model_file_mapping = {
    "logreg_tfidf": "intent_model_logreg_tfidf.pkl",
    "logreg_indobert": "intent_model_logreg_indobert.pkl",
}
if intent_model not in model_file_mapping:
    raise ValueError(f"Unknown INTENT MODEL NAME: {intent_model}")
intent_model_path = model_dir / model_file_mapping[intent_model]
intent_pipeline = joblib.load(intent_model_path)

def _preprocess_intent(text: str) -> str:
    text = clean_text(text)
    if not isinstance(text, str):
        text = str(text)

    text = text.lower()
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    text = re.sub(r"[^0-9a-zA-ZÀ-ÿ\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def predict_intent_proba(text: str):
    s = _preprocess_intent(text)
    proba = intent_pipeline.predict_proba([s])[0]
    labels = intent_pipeline.classes_
    return {lbl: float(p) for lbl, p in zip(labels, proba)}

def predict_intent_conf(text: str):
    proba_dict = predict_intent_proba(text)
    best_label = max(proba_dict, key=proba_dict.get)
    best_score = float(proba_dict[best_label])
    best_percent = round(best_score * 100, 1)
    return best_label, best_score, best_percent, proba_dict