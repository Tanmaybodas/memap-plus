import os
from typing import Optional
from rapidfuzz import fuzz

_ENABLE_EMB = os.getenv("ENABLE_EMBEDDINGS", "false").lower() == "true"
_model = None

def _get_model():
    global _model
    if _model is not None:
        return _model
    if not _ENABLE_EMB:
        return None
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer('all-MiniLM-L6-v2')
        return _model
    except Exception:
        return None

def compare_usernames(u1: Optional[str], u2: Optional[str]) -> float:
    if not u1 or not u2:
        return 0.0
    return fuzz.ratio(u1.lower(), u2.lower()) / 100.0

def bio_similarity(bio1: Optional[str], bio2: Optional[str]) -> float:
    if not bio1 or not bio2:
        return 0.0
    model = _get_model()
    if model:
        try:
            from sentence_transformers import util
            emb1 = model.encode(bio1, convert_to_tensor=True)
            emb2 = model.encode(bio2, convert_to_tensor=True)
            score = float(util.cos_sim(emb1, emb2))
            # cos_sim may produce >1e-6 float noise; clamp 0..1
            return max(0.0, min(1.0, score))
        except Exception:
            pass
    # Fallback: fuzzy
    return fuzz.partial_ratio(bio1, bio2) / 100.0
