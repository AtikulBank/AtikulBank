"""
LAYER 14: CONTINUOUS SELF-LEARNING
Online learning and model adaptation for trading.

Features:
- Online learning with River library
- Concept drift detection (ADWIN, Page-Hinkley)
- Feature importance tracking
- Model performance monitoring
- Automatic retraining triggers
- Ensemble weight adaptation
- Market regime detection
- Adaptive strategy switching

Learning Modes:
- ONLINE: Continuous learning with each trade
- BATCH: Periodic batch retraining
- ADAPTIVE: Switch based on market conditions
"""
from __future__ import annotations

import time
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import statistics


class LearningMode(Enum):
    ONLINE = "ONLINE"
    BATCH = "BATCH"
    ADAPTIVE = "ADAPTIVE"


class DriftDetector(Enum):
    ADWIN = "ADWIN"
    PAGE_HINKLEY = "PAGE_HINKLEY"
    DDM = "DDM"


@dataclass
class TradeOutcome:
    """Trade outcome for learning."""
    trade_id: str
    timestamp: float
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_pct: float
    duration_seconds: float
    features: Dict[str, float]
    prediction: float
    confidence: float
    market_regime: str = ""
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class ModelPerformance:
    """Model performance metrics."""
    model_name: str
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    sharpe: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    avg_pnl: float = 0.0
    max_drawdown: float = 0.0
    last_updated: float = 0.0


@dataclass
class DriftAlert:
    """Concept drift alert."""
    detector: DriftDetector
    drift_magnitude: float
    confidence: float
    timestamp: float
    features_affected: List[str]
    recommendation: str


class SelfLearning:
    """
    LAYER 14: Continuous Self-Learning
    Online learning and model adaptation.
    """
    
    def __init__(
        self,
        learning_mode: LearningMode = LearningMode.ADAPTIVE,
        drift_detector: DriftDetector = DriftDetector.ADWIN,
        window_size: int = 1000,
        retrain_threshold: float = 0.1,
    ):
        self.learning_mode = learning_mode
        self.drift_detector = drift_detector
        self.window_size = window_size
        self.retrain_threshold = retrain_threshold
        
        # Trade history for learning
        self._trade_history: deque = deque(maxlen=window_size * 10)
        self._recent_outcomes: deque = deque(maxlen=window_size)
        
        # Model tracking
        self._models: Dict[str, ModelPerformance] = {}
        self._ensemble_weights: Dict[str, float] = {}
        
        # Drift detection
        self._drift_scores: deque = deque(maxlen=window_size)
        self._drift_alerts: List[DriftAlert] = []
        self._page_hinkley_sum = 0.0
        self._page_hinkley_count = 0
        self._page_hinkley_mean = 0.0
        
        # Feature importance
        self._feature_importance: Dict[str, float] = {}
        self._feature_history: deque = deque(maxlen=window_size)
        
        # Market regime
        self._regime_history: deque = deque(maxlen=100)
        self._current_regime = "UNKNOWN"
        
        # Retraining
        self._last_retrain_time = 0.0
        self._retrain_count = 0
        self._retrain_interval = 3600  # 1 hour default
        
        # Statistics
        self._total_predictions = 0
        self._correct_predictions = 0
        self._learning_events = 0
        
        # Performance tracking
        self._daily_performance: Dict[str, List[float]] = {}
    
    def record_trade(self, outcome: TradeOutcome) -> Dict:
        """Record trade outcome for learning."""
        self._trade_history.append(outcome)
        self._recent_outcomes.append(outcome)
        
        # Update model performance
        self._update_model_performance(outcome)
        
        # Update feature importance
        self._update_feature_importance(outcome)
        
        # Check for drift
        drift_alert = self._check_drift(outcome)
        
        # Update ensemble weights
        self._update_ensemble_weights()
        
        # Check if retraining needed
        retrain_needed = self._check_retrain_trigger()
        
        self._learning_events += 1
        
        return {
            "trade_recorded": True,
            "drift_alert": drift_alert,
            "retrain_needed": retrain_needed,
            "current_regime": self._current_regime,
            "ensemble_weights": self._ensemble_weights.copy(),
        }
    
    def predict(
        self,
        features: Dict[str, float],
        model_weights: Optional[Dict[str, float]] = None,
    ) -> Tuple[float, float]:
        """
        Make prediction using ensemble.
        Returns (prediction, confidence).
        """
        self._total_predictions += 1
        
        # Use provided weights or ensemble weights
        weights = model_weights or self._ensemble_weights
        
        if not weights:
            return 0.5, 0.5  # Default: neutral prediction
        
        # Simple weighted average (in real impl, would use actual models)
        prediction = 0.0
        total_weight = 0.0
        
        for model_name, weight in weights.items():
            # Simulate model prediction based on features
            model_pred = self._simulate_model_prediction(model_name, features)
            prediction += model_pred * weight
            total_weight += weight
        
        if total_weight > 0:
            prediction /= total_weight
        
        # Calculate confidence based on agreement
        confidence = self._calculate_confidence(features, weights)
        
        return prediction, confidence
    
    def _simulate_model_prediction(self, model_name: str, features: Dict[str, float]) -> float:
        """Simulate model prediction (placeholder for real models)."""
        # Simple feature-based prediction
        if "momentum" in features:
            momentum = features.get("momentum", 0)
            return 0.5 + (momentum * 0.1)
        elif "volatility" in features:
            vol = features.get("volatility", 0)
            return 0.5 - (vol * 0.05)
        return 0.5
    
    def _calculate_confidence(self, features: Dict[str, float], weights: Dict[str, float]) -> float:
        """Calculate prediction confidence."""
        # Base confidence from ensemble agreement
        if len(weights) < 2:
            return 0.5
        
        # Simulate model predictions
        predictions = []
        for model_name in weights:
            pred = self._simulate_model_prediction(model_name, features)
            predictions.append(pred)
        
        if not predictions:
            return 0.5
        
        # Confidence from prediction variance
        variance = statistics.variance(predictions) if len(predictions) > 1 else 0
        confidence = max(0.3, 1.0 - variance * 2)
        
        return min(confidence, 0.95)
    
    def _update_model_performance(self, outcome: TradeOutcome) -> None:
        """Update model performance metrics."""
        model_name = outcome.tags.get("model", "ensemble")
        
        if model_name not in self._models:
            self._models[model_name] = ModelPerformance(model_name=model_name)
        
        perf = self._models[model_name]
        perf.total_trades += 1
        
        # Update win rate
        if outcome.pnl >= 0:
            perf.win_rate = ((perf.win_rate * (perf.total_trades - 1)) + 1) / perf.total_trades
        else:
            perf.win_rate = (perf.win_rate * (perf.total_trades - 1)) / perf.total_trades
        
        # Update avg P&L
        perf.avg_pnl = ((perf.avg_pnl * (perf.total_trades - 1)) + outcome.pnl) / perf.total_trades
        
        # Update accuracy (correct direction prediction)
        predicted_direction = 1 if outcome.prediction > 0.5 else -1
        actual_direction = 1 if outcome.pnl >= 0 else -1
        
        if predicted_direction == actual_direction:
            self._correct_predictions += 1
            perf.accuracy = self._correct_predictions / self._total_predictions
        
        perf.last_updated = time.time()
    
    def _update_feature_importance(self, outcome: TradeOutcome) -> None:
        """Update feature importance based on trade outcome."""
        abs_pnl = abs(outcome.pnl)
        
        for feature_name, feature_value in outcome.features.items():
            if feature_name not in self._feature_importance:
                self._feature_importance[feature_name] = 0.0
            
            # Weight by P&L magnitude
            importance_delta = abs_pnl * abs(feature_value) * 0.01
            self._feature_importance[feature_name] += importance_delta
        
        # Normalize
        total = sum(self._feature_importance.values())
        if total > 0:
            for key in self._feature_importance:
                self._feature_importance[key] /= total
    
    def _check_drift(self, outcome: TradeOutcome) -> Optional[DriftAlert]:
        """Check for concept drift."""
        # Add to drift scores
        self._drift_scores.append(outcome.pnl)
        
        if len(self._drift_scores) < 100:
            return None
        
        # Page-Hinkley drift detection
        if self.drift_detector == DriftDetector.PAGE_HINKLEY:
            return self._page_hinkley_detect(outcome)
        
        # ADWIN-like drift detection
        elif self.drift_detector == DriftDetector.ADWIN:
            return self._adwin_detect(outcome)
        
        return None
    
    def _page_hinkley_detect(self, outcome: TradeOutcome) -> Optional[DriftAlert]:
        """Page-Hinkley drift detection."""
        self._page_hinkley_count += 1
        self._page_hinkley_mean = (self._page_hinkley_mean * (self._page_hinkley_count - 1) + outcome.pnl) / self._page_hinkley_count
        self._page_hinkley_sum += outcome.pnl - self._page_hinkley_mean - 0.005  # delta = 0.005
        
        # Check for drift
        if self._page_hinkley_sum > 50:  # threshold
            alert = DriftAlert(
                detector=DriftDetector.PAGE_HINKLEY,
                drift_magnitude=self._page_hinkley_sum,
                confidence=0.8,
                timestamp=time.time(),
                features_affected=list(self._feature_importance.keys())[:5],
                recommendation="Consider retraining models",
            )
            self._drift_alerts.append(alert)
            self._page_hinkley_sum = 0
            return alert
        
        return None
    
    def _adwin_detect(self, outcome: TradeOutcome) -> Optional[DriftAlert]:
        """ADWIN-like drift detection."""
        scores = list(self._drift_scores)
        n = len(scores)
        
        if n < 100:
            return None
        
        # Split window
        split = n // 2
        window1 = scores[:split]
        window2 = scores[split:]
        
        mean1 = statistics.mean(window1)
        mean2 = statistics.mean(window2)
        
        # Calculate drift magnitude
        drift = abs(mean2 - mean1)
        
        if drift > 0.5:  # threshold
            alert = DriftAlert(
                detector=DriftDetector.ADWIN,
                drift_magnitude=drift,
                confidence=min(drift / 2, 0.95),
                timestamp=time.time(),
                features_affected=list(self._feature_importance.keys())[:5],
                recommendation="Market regime change detected",
            )
            self._drift_alerts.append(alert)
            return alert
        
        return None
    
    def _update_ensemble_weights(self) -> None:
        """Update ensemble weights based on performance."""
        if not self._models:
            return
        
        # Calculate weights based on performance
        total_score = 0
        scores = {}
        
        for name, perf in self._models.items():
            # Composite score: accuracy * win_rate * (1 - max_drawdown)
            score = perf.accuracy * perf.win_rate * (1 - perf.max_drawdown)
            scores[name] = max(score, 0.01)  # Minimum weight
            total_score += scores[name]
        
        # Normalize weights
        if total_score > 0:
            for name in scores:
                self._ensemble_weights[name] = scores[name] / total_score
    
    def _check_retrain_trigger(self) -> bool:
        """Check if retraining is needed."""
        current_time = time.time()
        
        # Time-based retraining
        if current_time - self._last_retrain_time > self._retrain_interval:
            return True
        
        # Performance-based retraining
        if self._total_predictions > 100:
            accuracy = self._correct_predictions / self._total_predictions
            if accuracy < (1 - self.retrain_threshold):
                return True
        
        # Drift-based retraining
        if len(self._drift_alerts) > 0:
            recent_alert = self._drift_alerts[-1]
            if recent_alert.drift_magnitude > 1.0:
                return True
        
        return False
    
    def trigger_retrain(self) -> Dict:
        """Trigger model retraining."""
        self._last_retrain_time = time.time()
        self._retrain_count += 1
        
        # Reset drift alerts
        self._drift_alerts.clear()
        
        return {
            "retrain_triggered": True,
            "retrain_count": self._retrain_count,
            "timestamp": self._last_retrain_time,
            "reason": "Scheduled or performance-based retrain",
        }
    
    def detect_market_regime(self, features: Dict[str, float]) -> str:
        """Detect current market regime."""
        # Simple regime detection based on volatility and trend
        volatility = features.get("volatility", 0)
        trend = features.get("trend", 0)
        volume = features.get("volume", 0)
        
        if volatility > 0.02:
            regime = "HIGH_VOLATILITY"
        elif abs(trend) > 0.01:
            regime = "TRENDING" if trend > 0 else "REVERSAL"
        elif volume > 1.5:
            regime = "HIGH_VOLUME"
        else:
            regime = "RANGING"
        
        self._current_regime = regime
        self._regime_history.append(regime)
        
        return regime
    
    def get_top_features(self, n: int = 10) -> List[Tuple[str, float]]:
        """Get top N most important features."""
        sorted_features = sorted(
            self._feature_importance.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        return sorted_features[:n]
    
    @property
    def stats(self) -> Dict:
        """Get learning statistics."""
        return {
            "learning_mode": self.learning_mode.value,
            "total_trades": len(self._trade_history),
            "total_predictions": self._total_predictions,
            "accuracy": self._correct_predictions / max(self._total_predictions, 1),
            "learning_events": self._learning_events,
            "retrain_count": self._retrain_count,
            "drift_alerts": len(self._drift_alerts),
            "current_regime": self._current_regime,
            "ensemble_weights": self._ensemble_weights.copy(),
            "top_features": self.get_top_features(5),
            "model_count": len(self._models),
        }
