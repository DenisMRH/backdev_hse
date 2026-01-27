import pickle
import numpy as np
from pathlib import Path
from typing import Tuple

_model = None

class ModelNotLoadedError(RuntimeError):
    pass

def load_ml_model(path: str = "model.pkl"):
    global _model
    model_path = Path(path)
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found at {model_path}")
    
    with open(model_path, "rb") as f:
        _model = pickle.load(f)

def get_prediction(features: list[float]) -> Tuple[bool, float]:
    global _model
    if _model is None:
        raise ModelNotLoadedError("Model is not loaded")
    
    np_features = np.array(features).reshape(1, -1)
    
    prediction = _model.predict(np_features)
    probabilities = _model.predict_proba(np_features)
    
    is_violation = bool(prediction[0])
    probability = float(probabilities[0][1])
    
    return is_violation, probability
