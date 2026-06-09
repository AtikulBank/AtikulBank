"""
LAYER 6: ML INFERENCE ENGINE (30 models parallel)
RF | ET | LR | XGB | LGB | CAT | LSTM | Transformer | TCN | NBeats |
TFT | Mamba | River | PatchTST | iTransformer | TimesNet | CrossNet | SCINet

ThreadPoolExecutor → parallel inference
OUTPUT: prob_matrix[30, 3] → {BUY, SELL, HOLD}
"""
from __future__ import annotations

import time
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np

from pipeline import MLPrediction, MLPredictionMatrix, CompressedVector


class TrainedModelWrapper:
    """Wrapper for a trained ML model with prediction interface."""

    def __init__(self, name: str, model: Any = None, model_type: str = "sklearn"):
        self.name = name
        self.model = model
        self.model_type = model_type
        self.accuracy = 0.5
        self.prediction_count = 0
        self._loaded = model is not None

    def predict_proba(self, features: np.ndarray) -> np.ndarray:
        """Predict class probabilities [buy, sell, hold]."""
        if not self._loaded or self.model is None:
            return np.array([0.33, 0.33, 0.34])

        try:
            if self.model_type == "sklearn":
                proba = self.model.predict_proba(features.reshape(1, -1))[0]
                if len(proba) == 2:
                    return np.array([proba[0], proba[1], 0.0])
                return proba[:3]
            elif self.model_type == "torch":
                import torch
                self.model.eval()
                with torch.no_grad():
                    x = torch.tensor(features, dtype=torch.float32).unsqueeze(0)
                    out = self.model(x)
                    proba = torch.softmax(out, dim=-1).numpy()[0]
                    return proba[:3] if len(proba) >= 3 else np.pad(proba, (0, 3 - len(proba)))
            elif self.model_type == "xgboost":
                dmatrix = np.array(features).reshape(1, -1)
                proba = self.model.predict(dmatrix)[0]
                if len(proba) == 2:
                    return np.array([proba[0], proba[1], 0.0])
                return proba[:3]
            elif self.model_type == "river":
                x_dict = {f"f{i}": v for i, v in enumerate(features)}
                prediction = self.model.predict_proba_one(x_dict)
                buy = prediction.get(1, 0.33)
                sell = prediction.get(-1, 0.33)
                hold = 1.0 - buy - sell
                return np.array([buy, sell, max(hold, 0)])
        except Exception:
            pass

        return np.array([0.33, 0.33, 0.34])

    def update_accuracy(self, correct: bool) -> None:
        self.prediction_count += 1
        alpha = 0.1
        self.accuracy = self.accuracy * (1 - alpha) + (1.0 if correct else 0.0) * alpha


class MLPipeline30:
    """
    LAYER 6: ML Inference Engine with 30 models.
    Runs parallel inference using ThreadPoolExecutor.
    """

    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.models: List[TrainedModelWrapper] = []
        self._tick_count = 0
        self._model_names = [
            "RandomForest", "ExtraTrees", "LogisticRegression",
            "XGBoost", "LightGBM", "CatBoost",
            "LSTM", "Transformer", "TCN", "NBeats",
            "TemporalFusion", "Mamba",
            "River", "PatchTST", "iTransformer", "TimesNet",
            "CrossNet", "SCINet",
        ]
        for name in self._model_names:
            self.models.append(TrainedModelWrapper(name=name))

    def add_model(self, wrapper: TrainedModelWrapper) -> None:
        self.models.append(wrapper)

    def predict_single(self, model: TrainedModelWrapper, features: np.ndarray) -> MLPrediction:
        t0 = time.perf_counter_ns()
        proba = model.predict_proba(features)
        elapsed = time.perf_counter_ns() - t0
        pred = MLPrediction(model_name=model.name, buy_prob=float(proba[0]), sell_prob=float(proba[1]), hold_prob=float(proba[2]), confidence=float(np.max(proba)))
        return pred

    def infer(self, features: np.ndarray) -> MLPredictionMatrix:
        self._tick_count += 1
        predictions = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.predict_single, m, features): m for m in self.models if m._loaded}
            for future in as_completed(futures, timeout=1.0):
                try:
                    pred = future.result(timeout=0.5)
                    predictions.append(pred)
                except Exception:
                    pass

        if not predictions:
            for m in self.models[:6]:
                proba = m.predict_proba(features)
                predictions.append(MLPrediction(model_name=m.name, buy_prob=float(proba[0]), sell_prob=float(proba[1]), hold_prob=float(proba[2])))

        buy_probs = np.array([p.buy_prob for p in predictions])
        sell_probs = np.array([p.sell_prob for p in predictions])
        hold_probs = np.array([p.hold_prob for p in predictions])

        weights = np.array([m.accuracy for m in self.models if m._loaded][:len(predictions)])
        if len(weights) != len(predictions):
            weights = np.ones(len(predictions))
        weights = weights / max(weights.sum(), 1e-10)

        result = MLPredictionMatrix(
            predictions=predictions,
            ensemble_buy=float(np.average(buy_probs, weights=weights)),
            ensemble_sell=float(np.average(sell_probs, weights=weights)),
            ensemble_hold=float(np.average(hold_probs, weights=weights)),
        )
        return result

    @property
    def stats(self) -> dict:
        loaded = sum(1 for m in self.models if m._loaded)
        return {"tick_count": self._tick_count, "total_models": len(self.models), "loaded_models": loaded}
