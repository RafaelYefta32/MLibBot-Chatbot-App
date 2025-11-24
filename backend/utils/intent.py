from pathlib import Path
import joblib
from .preprocess import clean_text   

BASE_DIR = Path(__file__).resolve().parent.parent
VECTOR_DIR = BASE_DIR / "vectorstore"

INTENT_MODEL_PATH = VECTOR_DIR / "intent_model_logreg.pkl"  

intent_pipeline = joblib.load(INTENT_MODEL_PATH)

def predict_intent(text: str) -> str:
    cleaned = clean_text(text)
    return intent_pipeline.predict([cleaned])[0]

def predict_intent_proba(text: str):
    cleaned = clean_text(text)
    proba = intent_pipeline.predict_proba([cleaned])[0]
    labels = intent_pipeline.classes_
    return dict(zip(labels, proba))
