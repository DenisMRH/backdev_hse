import pickle
import numpy as np
from pathlib import Path
from typing import Tuple
from sklearn.linear_model import LogisticRegression


class ModelNotLoadedError(RuntimeError):
    pass

class ModelClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_model()
        return cls._instance

    def _load_model(self):
        model_path = "model.pkl"
        if not Path(model_path).exists():
            self._model = train_model()
            save_model(self._model, model_path)
        else:
            self._model = load_model(model_path)

    def predict(self, features):
        if self._model is None:
            raise ModelNotLoadedError("Model is not loaded")
        return self._model.predict(features)

    def predict_proba(self, features):
        if self._model is None:
            raise ModelNotLoadedError("Model is not loaded")
        return self._model.predict_proba(features)
        
            


def get_prediction(features: list[float]) -> Tuple[bool, float]:
    
    _model = ModelClient()
    
    np_features = np.array(features).reshape(1, -1)
    
    prediction = _model.predict(np_features)
    probabilities = _model.predict_proba(np_features)
    
    is_violation = bool(prediction[0])
    probability = float(probabilities[0][1])
    
    return is_violation, probability



def train_model():
    """Обучает простую модель на синтетических данных."""
    np.random.seed(42)
    # Признаки: [is_verified_seller, images_qty, description_length, category]
    X = np.random.rand(1000, 4)
    # Целевая переменная: 1 = нарушение, 0 = нет нарушения
    y = (X[:, 0] < 0.3) & (X[:, 1] < 0.2)
    y = y.astype(int)
    
    model = LogisticRegression()
    model.fit(X, y)
    return model

def save_model(model, path="model.pkl"):
    with open(path, "wb") as f:
        pickle.dump(model, f)

def load_model(path="model.pkl"):
    with open(path, "rb") as f:
        return pickle.load(f)
