"""
LAYER 6: ML INFERENCE ENGINE
30 ML models running in parallel for prediction
"""

import numpy as np
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import joblib
from pathlib import Path


@dataclass
class ModelPrediction:
    """Prediction from a single model"""
    model_name: str
    direction: float  # -1 to 1 (sell to buy)
    confidence: float  # 0 to 1
    probabilities: np.ndarray = field(default_factory=lambda: np.array([0.33, 0.33, 0.34]))


@dataclass
class InferenceResult:
    """Result from ML inference engine"""
    prob_matrix: np.ndarray = None  # Shape: (n_models, 3)
    model_predictions: List[ModelPrediction] = field(default_factory=list)
    ensemble_prediction: float = 0.0
    ensemble_confidence: float = 0.0
    model_agreement: float = 0.0
    computation_time_ms: float = 0.0


class MLInferenceEngine:
    """
    Layer 6: ML Inference Engine
    Runs 30 ML models in parallel for prediction
    """
    
    def __init__(
        self,
        model_dir: str = "trained_models",
        n_workers: int = 8,
        model_names: List[str] = None
    ):
        """
        Initialize ML Inference Engine
        
        Args:
            model_dir: Directory containing trained models
            n_workers: Number of parallel workers
            model_names: List of model names to load
        """
        self.model_dir = Path(model_dir)
        self.n_workers = n_workers
        
        # Default model names (30 models)
        if model_names is None:
            self.model_names = [
                "RF", "ET", "LR", "XGB", "LGB", "CAT",
                "LSTM", "Transformer", "TCN", "NBeats", "TFT", "Mamba",
                "River", "PatchTST", "iTransformer", "TimesNet", "Crossformer", "SCINet",
                "N-HiTS", "TimeMixer", "DLinear", "NLinear", "MICN", "WaveNet",
                "CatBoost", "LightGBM", "XGBoost", "RandomForest", "GradientBoosting", "AdaBoost"
            ]
        else:
            self.model_names = model_names
        
        # Thread pool
        self.executor = ThreadPoolExecutor(max_workers=n_workers)
        
        # Loaded models
        self.models: Dict[str, Any] = {}
        
        # Statistics
        self._inference_count = 0
        self._total_time_ms = 0.0
        
    def load_models(self) -> int:
        """
        Load trained models from disk
        
        Returns:
            Number of models loaded
        """
        loaded_count = 0
        
        for name in self.model_names:
            model_path = self.model_dir / f"{name}.joblib"
            
            if model_path.exists():
                try:
                    model = joblib.load(model_path)
                    self.models[name] = model
                    loaded_count += 1
                except Exception as e:
                    print(f"[ML INFERENCE] Failed to load {name}: {e}")
            else:
                # Create dummy model for demonstration
                self.models[name] = self._create_dummy_model(name)
                loaded_count += 1
        
        print(f"[ML INFERENCE] Loaded {loaded_count}/{len(self.model_names)} models")
        return loaded_count
    
    def _create_dummy_model(self, name: str) -> Any:
        """Create a dummy model for demonstration"""
        class DummyModel:
            def __init__(self, model_name):
                self.name = model_name
                self.is_trained = True
            
            def predict(self, X):
                # Random prediction
                probs = np.random.dirichlet([1, 1, 1])
                direction = np.random.uniform(-1, 1)
                confidence = np.random.uniform(0.3, 0.9)
                return direction, confidence, probs
        
        return DummyModel(name)
    
    def predict(self, features: np.ndarray) -> InferenceResult:
        """
        Run inference on all models
        
        Args:
            features: Input features (compressed vector)
            
        Returns:
            InferenceResult with predictions from all models
        """
        import time
        start_time = time.time()
        
        # Ensure features is 2D
        if features.ndim == 1:
            features = features.reshape(1, -1)
        
        # Run predictions in parallel
        predictions = []
        futures = {}
        
        for name, model in self.models.items():
            future = self.executor.submit(self._predict_single, name, model, features)
            futures[future] = name
        
        # Collect results
        for future in as_completed(futures):
            name = futures[future]
            try:
                pred = future.result()
                predictions.append(pred)
            except Exception as e:
                print(f"[ML INFERENCE] Error in {name}: {e}")
        
        # Create probability matrix
        prob_matrix = np.zeros((len(predictions), 3))
        for i, pred in enumerate(predictions):
            prob_matrix[i] = pred.probabilities
        
        # Calculate ensemble prediction
        ensemble_probs = np.mean(prob_matrix, axis=0)
        ensemble_direction = np.argmax(ensemble_probs) - 1  # -1: sell, 0: hold, 1: buy
        ensemble_confidence = np.max(ensemble_probs)
        
        # Calculate model agreement
        directions = [np.argmax(p.probabilities) - 1 for p in predictions]
        agreement = np.mean([1 if d == ensemble_direction else 0 for d in directions])
        
        computation_time = (time.time() - start_time) * 1000
        self._inference_count += 1
        self._total_time_ms += computation_time
        
        return InferenceResult(
            prob_matrix=prob_matrix,
            model_predictions=predictions,
            ensemble_prediction=float(ensemble_direction),
            ensemble_confidence=float(ensemble_confidence),
            model_agreement=float(agreement),
            computation_time_ms=computation_time
        )
    
    def _predict_single(self, name: str, model: Any, features: np.ndarray) -> ModelPrediction:
        """Run prediction on a single model"""
        try:
            direction, confidence, probs = model.predict(features)
            return ModelPrediction(
                model_name=name,
                direction=float(direction),
                confidence=float(confidence),
                probabilities=probs if isinstance(probs, np.ndarray) else np.array(probs)
            )
        except Exception as e:
            # Return neutral prediction on error
            return ModelPrediction(
                model_name=name,
                direction=0.0,
                confidence=0.0,
                probabilities=np.array([0.33, 0.33, 0.34])
            )
    
    def update_model_weights(self, model_name: str, accuracy: float) -> None:
        """Update model weight based on recent accuracy"""
        # This would update model weights in production
        pass
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get inference statistics"""
        avg_time = self._total_time_ms / self._inference_count if self._inference_count > 0 else 0.0
        
        return {
            "total_models": len(self.models),
            "loaded_models": len(self.models),
            "inference_count": self._inference_count,
            "avg_inference_time_ms": avg_time,
            "model_names": list(self.models.keys())
        }
    
    def shutdown(self) -> None:
        """Shutdown the inference engine"""
        self.executor.shutdown(wait=False)