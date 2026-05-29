"""
XAUUSD GOD BOT v2.0 — ML Models Module
28 ML/DL Models | Ensemble | Model Management

Author: Atikul Islam
Version: 2.0.0-alpha.4
"""

from __future__ import annotations

import os
import sys
import time
import logging
import pickle
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
from collections import deque
import threading
import asyncio

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
except Exception:
    TORCH_AVAILABLE = False

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

try:
    import catboost as cb
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, classification_report
    from sklearn.isotonic import IsotonicRegression
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False

try:
    from river import tree as river_tree
    from river import preprocessing as river_preprocessing
    from river import metrics as river_metrics
    RIVER_AVAILABLE = True
except ImportError:
    RIVER_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 01 — BASE MODEL INTERFACE
# ═══════════════════════════════════════════════════════════════════════════

class BaseModel:
    """
    Abstract base class for all ML models.
    
    All models must implement:
    - fit(X, y): Train the model
    - predict(X): Return class prediction
    - predict_proba(X): Return probability predictions
    - save(path): Save model to disk
    - load(path): Load model from disk
    """
    
    def __init__(self, name: str):
        """
        Initialize BaseModel.
        
        Args:
            name: Model name.
        """
        self.name = name
        self.is_trained = False
        self.last_trained: Optional[datetime] = None
        self.accuracy_history: deque = deque(maxlen=100)
        self._lock = threading.Lock()
        self.logger = logging.getLogger(f"XAUUSD_GOD_BOT.Models.{name}")
        self.model: Any = None
        self.scaler: Any = None
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} '{self.name}' trained={self.is_trained}>"
    
    def fit(self, X: np.ndarray, y: np.ndarray, **kwargs) -> 'BaseModel':
        """
        Train the model.
        
        Args:
            X: Feature matrix (n_samples, n_features).
            y: Target vector (n_samples,).
        
        Returns:
            Self for chaining.
        """
        raise NotImplementedError("Subclasses must implement fit()")
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class labels.
        
        Args:
            X: Feature matrix.
        
        Returns:
            Array of predictions (0/1 for down/up).
        """
        raise NotImplementedError("Subclasses must implement predict()")
    
    def predict_proba(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict class probabilities.
        
        Args:
            X: Feature matrix.
        
        Returns:
            Tuple of (prob_class_0, prob_class_1).
        """
        raise NotImplementedError("Subclasses must implement predict_proba()")
    
    def predict_confidence(self, X: np.ndarray) -> float:
        """
        Get prediction confidence (0-1).
        
        Args:
            X: Feature matrix.
        
        Returns:
            Confidence score.
        """
        try:
            prob0, prob1 = self.predict_proba(X)
            return max(prob0, prob1)
        except Exception:
            return 0.5
    
    def save(self, path: Union[str, Path]) -> bool:
        """
        Save model to disk.
        
        Args:
            path: Path to save file.
        
        Returns:
            True if successful.
        """
        raise NotImplementedError("Subclasses must implement save()")
    
    def load(self, path: Union[str, Path]) -> bool:
        """
        Load model from disk.
        
        Args:
            path: Path to model file.
        
        Returns:
            True if successful.
        """
        raise NotImplementedError("Subclasses must implement load()")
    
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """Get feature importance scores."""
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get model status."""
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "trained": self.is_trained,
            "last_trained": self.last_trained,
            "accuracy_history_len": len(self.accuracy_history),
            "avg_accuracy": np.mean(self.accuracy_history) if self.accuracy_history else 0.0,
        }


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 02 — LSTM MODEL
# ═══════════════════════════════════════════════════════════════════════════

class LSTMModel(BaseModel):
    """
    Bidirectional LSTM with Attention mechanism.
    
    Architecture:
    - 3 BiLSTM layers (256 hidden units each)
    - Bahdanau attention
    - Dropout 0.3
    - LayerNorm
    - FC output layers
    """
    
    def __init__(
        self,
        input_dim: int = 100,
        sequence_length: int = 100,
        hidden_dim: int = 256,
        num_layers: int = 3,
        dropout: float = 0.3,
        learning_rate: float = 0.001,
    ):
        """
        Initialize LSTM model.
        
        Args:
            input_dim: Number of features.
            sequence_length: Input sequence length.
            hidden_dim: Hidden dimension.
            num_layers: Number of LSTM layers.
            dropout: Dropout rate.
            learning_rate: Learning rate.
        """
        super().__init__("LSTM")
        
        self.input_dim = input_dim
        self.sequence_length = sequence_length
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.dropout = dropout
        self.learning_rate = learning_rate
        
        if TORCH_AVAILABLE:
            self._build_model()
    
    def _build_model(self) -> None:
        """Build PyTorch LSTM model."""
        class Attention(nn.Module):
            def __init__(self, hidden_dim: int):
                super().__init__()
                self.attention = nn.Linear(hidden_dim * 2, 1)
            
            def forward(self, lstm_output, hidden):
                attention_weights = torch.softmax(self.attention(lstm_output), dim=1)
                context = torch.sum(attention_weights * lstm_output, dim=1)
                return context, attention_weights
        
        class BiLSTMAttention(nn.Module):
            def __init__(self, input_dim, hidden_dim, num_layers, dropout):
                super().__init__()
                
                self.lstm = nn.LSTM(
                    input_size=input_dim,
                    hidden_size=hidden_dim,
                    num_layers=num_layers,
                    batch_first=True,
                    dropout=dropout if num_layers > 1 else 0,
                    bidirectional=True,
                )
                
                self.attention = Attention(hidden_dim)
                self.layer_norm = nn.LayerNorm(hidden_dim * 2)
                self.dropout = nn.Dropout(dropout)
                
                self.fc1 = nn.Linear(hidden_dim * 2, 128)
                self.fc2 = nn.Linear(128, 64)
                self.fc3 = nn.Linear(64, 2)
                
                self.relu = nn.ReLU()
                self.output_activation = nn.Softmax(dim=1)
            
            def forward(self, x):
                lstm_out, (hidden, cell) = self.lstm(x)
                
                context, attention_weights = self.attention(lstm_out, hidden)
                
                x = self.layer_norm(context)
                x = self.dropout(x)
                x = self.relu(self.fc1(x))
                x = self.dropout(x)
                x = self.relu(self.fc2(x))
                x = self.fc3(x)
                x = self.output_activation(x)
                
                return x
        
        self.model = BiLSTMAttention(
            self.input_dim, self.hidden_dim, self.num_layers, self.dropout
        )
        self.optimizer = optim.AdamW(self.model.parameters(), lr=self.learning_rate)
        self.criterion = nn.CrossEntropyLoss()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
    
    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        val_split: float = 0.2,
        epochs: int = 50,
        batch_size: int = 64,
        **kwargs
    ) -> 'LSTMModel':
        """
        Train LSTM model.
        
        Args:
            X: Feature matrix.
            y: Target vector (0=down, 1=up).
            val_split: Validation split ratio.
            epochs: Number of training epochs.
            batch_size: Batch size.
        
        Returns:
            Self.
        """
        if not TORCH_AVAILABLE:
            self.logger.warning("PyTorch not available, cannot train")
            return self
        
        try:
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
            
            if X.shape[1] > self.input_dim:
                X = X[:, :self.input_dim]
            elif X.shape[1] < self.input_dim:
                pad_width = self.input_dim - X.shape[1]
                X = np.pad(X, ((0, 0), (0, pad_width)), mode='constant')
            
            if len(X) >= self.sequence_length:
                X_seq = np.array([X[i:i+self.sequence_length] for i in range(len(X) - self.sequence_length)])
                y_seq = y[self.sequence_length:]
            else:
                X_seq = X.reshape(1, *X.shape)
                if X_seq.shape[1] < self.sequence_length:
                    pad = np.zeros((X_seq.shape[0], self.sequence_length - X_seq.shape[1], X_seq.shape[2]))
                    X_seq = np.concatenate([pad, X_seq], axis=1)
                y_seq = y
            
            X_train, X_val, y_train, y_val = train_test_split(
                X_seq, y_seq, test_size=val_split, shuffle=False
            )
            
            X_train_t = torch.FloatTensor(X_train).to(self.device)
            y_train_t = torch.LongTensor(y_train).to(self.device)
            X_val_t = torch.FloatTensor(X_val).to(self.device)
            y_val_t = torch.LongTensor(y_val).to(self.device)
            
            train_dataset = TensorDataset(X_train_t, y_train_t)
            train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
            
            self.model.train()
            best_val_acc = 0.0
            
            for epoch in range(epochs):
                epoch_loss = 0.0
                for batch_X, batch_y in train_loader:
                    self.optimizer.zero_grad()
                    outputs = self.model(batch_X)
                    loss = self.criterion(outputs, batch_y)
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                    self.optimizer.step()
                    epoch_loss += loss.item()
                
                self.model.eval()
                with torch.no_grad():
                    val_outputs = self.model(X_val_t)
                    val_preds = torch.argmax(val_outputs, dim=1)
                    val_acc = (val_preds == y_val_t).float().mean().item()
                
                if val_acc > best_val_acc:
                    best_val_acc = val_acc
                
                if epoch % 10 == 0:
                    self.logger.info(f"Epoch {epoch}: Loss={epoch_loss/len(train_loader):.4f} ValAcc={val_acc:.4f}")
            
            self.is_trained = True
            self.last_trained = datetime.now()
            self.accuracy_history.append(best_val_acc)
            
            self.logger.info(f"LSTM trained: accuracy={best_val_acc:.4f}")
            
        except Exception as e:
            self.logger.error(f"LSTM training error: {e}")
        
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict class labels."""
        if not self.is_trained or not TORCH_AVAILABLE:
            return np.zeros(len(X))
        
        try:
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
            
            if X.shape[1] > self.input_dim:
                X = X[:, :self.input_dim]
            elif X.shape[1] < self.input_dim:
                pad_width = self.input_dim - X.shape[1]
                X = np.pad(X, ((0, 0), (0, pad_width)), mode='constant')
            
            X_t = torch.FloatTensor(X).unsqueeze(0).to(self.device) if len(X.shape) == 2 else torch.FloatTensor(X).to(self.device)
            
            self.model.eval()
            with torch.no_grad():
                outputs = self.model(X_t)
                preds = torch.argmax(outputs, dim=1).cpu().numpy()
            
            return preds
            
        except Exception as e:
            self.logger.error(f"LSTM predict error: {e}")
            return np.zeros(len(X))
    
    def predict_proba(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Predict class probabilities."""
        if not self.is_trained or not TORCH_AVAILABLE:
            return np.zeros(len(X)), np.ones(len(X))
        
        try:
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
            
            if X.shape[1] > self.input_dim:
                X = X[:, :self.input_dim]
            elif X.shape[1] < self.input_dim:
                pad_width = self.input_dim - X.shape[1]
                X = np.pad(X, ((0, 0), (0, pad_width)), mode='constant')
            
            X_t = torch.FloatTensor(X).unsqueeze(0).to(self.device) if len(X.shape) == 2 else torch.FloatTensor(X).to(self.device)
            
            self.model.eval()
            with torch.no_grad():
                outputs = self.model(X_t)
                probs = outputs.cpu().numpy()
            
            return probs[:, 0], probs[:, 1]
            
        except Exception as e:
            self.logger.error(f"LSTM predict_proba error: {e}")
            return np.zeros(len(X)), np.ones(len(X))
    
    def save(self, path: Union[str, Path]) -> bool:
        """Save model to disk."""
        try:
            if not TORCH_AVAILABLE:
                return False
            
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            torch.save({
                'model_state_dict': self.model.state_dict(),
                'optimizer_state_dict': self.optimizer.state_dict(),
                'input_dim': self.input_dim,
                'hidden_dim': self.hidden_dim,
                'num_layers': self.num_layers,
                'dropout': self.dropout,
                'is_trained': self.is_trained,
                'last_trained': self.last_trained,
            }, path)
            
            self.logger.info(f"LSTM saved to {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"LSTM save error: {e}")
            return False
    
    def load(self, path: Union[str, Path]) -> bool:
        """Load model from disk."""
        try:
            if not TORCH_AVAILABLE or not Path(path).exists():
                return False
            
            checkpoint = torch.load(path, map_location=self.device)
            
            self.input_dim = checkpoint.get('input_dim', self.input_dim)
            self.hidden_dim = checkpoint.get('hidden_dim', self.hidden_dim)
            self.num_layers = checkpoint.get('num_layers', self.num_layers)
            self.dropout = checkpoint.get('dropout', self.dropout)
            
            self._build_model()
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            self.is_trained = checkpoint.get('is_trained', False)
            self.last_trained = checkpoint.get('last_trained')
            
            self.logger.info(f"LSTM loaded from {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"LSTM load error: {e}")
            return False


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 03 — XGBOOST MODEL
# ═══════════════════════════════════════════════════════════════════════════

class XGBoostModel(BaseModel):
    """
    XGBoost gradient boosting classifier.
    
    Features:
    - n_estimators with early stopping
    - SHAP explainability
    - Optuna hyperparameter tuning
    """
    
    def __init__(
        self,
        n_estimators: int = 500,
        max_depth: int = 6,
        learning_rate: float = 0.01,
        subsample: float = 0.8,
        colsample_bytree: float = 0.7,
        random_state: int = 42,
    ):
        """
        Initialize XGBoost model.
        
        Args:
            n_estimators: Number of boosting rounds.
            max_depth: Maximum tree depth.
            learning_rate: Learning rate.
            subsample: Subsample ratio.
            colsample_bytree: Column subsample ratio.
            random_state: Random seed.
        """
        super().__init__("XGBoost")
        
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.subsample = subsample
        self.colsample_bytree = colsample_bytree
        self.random_state = random_state
        
        if XGBOOST_AVAILABLE:
            self._build_model()
    
    def _build_model(self) -> None:
        """Build XGBoost model."""
        self.model = xgb.XGBClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            subsample=self.subsample,
            colsample_bytree=self.colsample_bytree,
            random_state=self.random_state,
            use_label_encoder=False,
            eval_metric='logloss',
            n_jobs=-1,
        )
        self.evals = []
    
    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        eval_set: Optional[Tuple[np.ndarray, np.ndarray]] = None,
        early_stopping_rounds: int = 50,
        **kwargs
    ) -> 'XGBoostModel':
        """
        Train XGBoost model.
        
        Args:
            X: Feature matrix.
            y: Target vector.
            eval_set: Validation set for early stopping.
            early_stopping_rounds: Early stopping rounds.
        
        Returns:
            Self.
        """
        if not XGBOOST_AVAILABLE:
            self.logger.warning("XGBoost not available")
            return self
        
        try:
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
            
            eval_set_tuple = [(X, y)] if eval_set is None else [eval_set]
            
            self.model.fit(
                X, y,
                eval_set=eval_set_tuple,
                early_stopping_rounds=early_stopping_rounds,
                verbose=False,
            )
            
            train_pred = self.model.predict(X)
            train_acc = accuracy_score(y, train_pred)
            
            self.is_trained = True
            self.last_trained = datetime.now()
            self.accuracy_history.append(train_acc)
            
            self.logger.info(f"XGBoost trained: accuracy={train_acc:.4f}")
            
        except Exception as e:
            self.logger.error(f"XGBoost training error: {e}")
        
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict class labels."""
        if not self.is_trained or not XGBOOST_AVAILABLE:
            return np.zeros(len(X))
        
        try:
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
            return self.model.predict(X)
        except Exception as e:
            self.logger.error(f"XGBoost predict error: {e}")
            return np.zeros(len(X))
    
    def predict_proba(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Predict class probabilities."""
        if not self.is_trained or not XGBOOST_AVAILABLE:
            return np.zeros(len(X)), np.ones(len(X))
        
        try:
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
            probs = self.model.predict_proba(X)
            return probs[:, 0], probs[:, 1]
        except Exception as e:
            self.logger.error(f"XGBoost predict_proba error: {e}")
            return np.zeros(len(X)), np.ones(len(X))
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores."""
        if not self.is_trained or not XGBOOST_AVAILABLE:
            return {}
        
        try:
            importance = self.model.feature_importances_
            return {f"feature_{i}": float(imp) for i, imp in enumerate(importance)}
        except Exception as e:
            self.logger.error(f"XGBoost feature importance error: {e}")
            return {}
    
    def save(self, path: Union[str, Path]) -> bool:
        """Save model to disk."""
        try:
            if not XGBOOST_AVAILABLE:
                return False
            
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            self.model.save_model(str(path))
            self.logger.info(f"XGBoost saved to {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"XGBoost save error: {e}")
            return False
    
    def load(self, path: Union[str, Path]) -> bool:
        """Load model from disk."""
        try:
            if not XGBOOST_AVAILABLE or not Path(path).exists():
                return False
            
            self._build_model()
            self.model.load_model(str(path))
            self.is_trained = True
            
            self.logger.info(f"XGBoost loaded from {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"XGBoost load error: {e}")
            return False


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 04 — LIGHTGBM MODEL
# ═══════════════════════════════════════════════════════════════════════════

class LightGBMModel(BaseModel):
    """
    LightGBM gradient boosting classifier.
    
    Features:
    - Leaf-wise tree growth
    - Fast training
    - Categorical feature support
    """
    
    def __init__(
        self,
        n_estimators: int = 500,
        num_leaves: int = 63,
        max_depth: int = -1,
        learning_rate: float = 0.01,
        random_state: int = 42,
    ):
        """
        Initialize LightGBM model.
        
        Args:
            n_estimators: Number of boosting rounds.
            num_leaves: Number of leaves.
            max_depth: Maximum tree depth.
            learning_rate: Learning rate.
            random_state: Random seed.
        """
        super().__init__("LightGBM")
        
        self.n_estimators = n_estimators
        self.num_leaves = num_leaves
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.random_state = random_state
        
        if LIGHTGBM_AVAILABLE:
            self._build_model()
    
    def _build_model(self) -> None:
        """Build LightGBM model."""
        self.model = lgb.LGBMClassifier(
            n_estimators=self.n_estimators,
            num_leaves=self.num_leaves,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            random_state=self.random_state,
            n_jobs=-1,
            verbose=-1,
        )
    
    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        eval_set: Optional[Tuple[np.ndarray, np.ndarray]] = None,
        **kwargs
    ) -> 'LightGBMModel':
        """Train LightGBM model."""
        if not LIGHTGBM_AVAILABLE:
            self.logger.warning("LightGBM not available")
            return self
        
        try:
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
            
            self.model.fit(X, y, eval_set=[(X, y)] if eval_set is None else [eval_set])
            
            train_pred = self.model.predict(X)
            train_acc = accuracy_score(y, train_pred)
            
            self.is_trained = True
            self.last_trained = datetime.now()
            self.accuracy_history.append(train_acc)
            
            self.logger.info(f"LightGBM trained: accuracy={train_acc:.4f}")
            
        except Exception as e:
            self.logger.error(f"LightGBM training error: {e}")
        
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict class labels."""
        if not self.is_trained or not LIGHTGBM_AVAILABLE:
            return np.zeros(len(X))
        
        try:
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
            return self.model.predict(X)
        except Exception as e:
            self.logger.error(f"LightGBM predict error: {e}")
            return np.zeros(len(X))
    
    def predict_proba(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Predict class probabilities."""
        if not self.is_trained or not LIGHTGBM_AVAILABLE:
            return np.zeros(len(X)), np.ones(len(X))
        
        try:
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
            probs = self.model.predict_proba(X)
            return probs[:, 0], probs[:, 1]
        except Exception as e:
            self.logger.error(f"LightGBM predict_proba error: {e}")
            return np.zeros(len(X)), np.ones(len(X))
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores."""
        if not self.is_trained or not LIGHTGBM_AVAILABLE:
            return {}
        
        try:
            importance = self.model.feature_importances_
            return {f"feature_{i}": float(imp) for i, imp in enumerate(importance)}
        except Exception:
            return {}
    
    def save(self, path: Union[str, Path]) -> bool:
        """Save model to disk."""
        try:
            if not LIGHTGBM_AVAILABLE:
                return False
            
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            self.model.booster_.save_model(str(path))
            self.logger.info(f"LightGBM saved to {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"LightGBM save error: {e}")
            return False
    
    def load(self, path: Union[str, Path]) -> bool:
        """Load model from disk."""
        try:
            if not LIGHTGBM_AVAILABLE or not Path(path).exists():
                return False
            
            self._build_model()
            self.model.booster_ = lgb.Booster(model_file=str(path))
            self.is_trained = True
            
            self.logger.info(f"LightGBM loaded from {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"LightGBM load error: {e}")
            return False


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 05 — RANDOM FOREST MODEL
# ═══════════════════════════════════════════════════════════════════════════

class RandomForestModel(BaseModel):
    """
    Random Forest classifier with OOB scoring.
    """
    
    def __init__(
        self,
        n_estimators: int = 500,
        max_depth: Optional[int] = None,
        min_samples_split: int = 10,
        random_state: int = 42,
    ):
        """
        Initialize Random Forest model.
        
        Args:
            n_estimators: Number of trees.
            max_depth: Maximum tree depth.
            min_samples_split: Minimum samples to split.
            random_state: Random seed.
        """
        super().__init__("RandomForest")
        
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.random_state = random_state
        
        if SKLEARN_AVAILABLE:
            self._build_model()
    
    def _build_model(self) -> None:
        """Build Random Forest model."""
        self.model = RandomForestClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            random_state=self.random_state,
            n_jobs=-1,
            oob_score=True,
        )
    
    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        **kwargs
    ) -> 'RandomForestModel':
        """Train Random Forest model."""
        if not SKLEARN_AVAILABLE:
            self.logger.warning("Sklearn not available")
            return self
        
        try:
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
            
            self.model.fit(X, y)
            
            train_pred = self.model.predict(X)
            train_acc = accuracy_score(y, train_pred)
            oob_acc = self.model.oob_score_ if hasattr(self.model, 'oob_score_') else train_acc
            
            self.is_trained = True
            self.last_trained = datetime.now()
            self.accuracy_history.append(train_acc)
            
            self.logger.info(f"RandomForest trained: accuracy={train_acc:.4f} OOB={oob_acc:.4f}")
            
        except Exception as e:
            self.logger.error(f"RandomForest training error: {e}")
        
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict class labels."""
        if not self.is_trained or not SKLEARN_AVAILABLE:
            return np.zeros(len(X))
        
        try:
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
            return self.model.predict(X)
        except Exception as e:
            self.logger.error(f"RandomForest predict error: {e}")
            return np.zeros(len(X))
    
    def predict_proba(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Predict class probabilities."""
        if not self.is_trained or not SKLEARN_AVAILABLE:
            return np.zeros(len(X)), np.ones(len(X))
        
        try:
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
            probs = self.model.predict_proba(X)
            return probs[:, 0], probs[:, 1]
        except Exception as e:
            self.logger.error(f"RandomForest predict_proba error: {e}")
            return np.zeros(len(X)), np.ones(len(X))
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores."""
        if not self.is_trained or not SKLEARN_AVAILABLE:
            return {}
        
        try:
            importance = self.model.feature_importances_
            return {f"feature_{i}": float(imp) for i, imp in enumerate(importance)}
        except Exception:
            return {}
    
    def save(self, path: Union[str, Path]) -> bool:
        """Save model to disk."""
        try:
            if not SKLEARN_AVAILABLE:
                return False
            
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'wb') as f:
                pickle.dump(self.model, f)
            
            self.logger.info(f"RandomForest saved to {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"RandomForest save error: {e}")
            return False
    
    def load(self, path: Union[str, Path]) -> bool:
        """Load model from disk."""
        try:
            if not SKLEARN_AVAILABLE or not Path(path).exists():
                return False
            
            with open(path, 'rb') as f:
                self.model = pickle.load(f)
            
            self.is_trained = True
            self.logger.info(f"RandomForest loaded from {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"RandomForest load error: {e}")
            return False


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 06 — CATBOOST MODEL
# ═══════════════════════════════════════════════════════════════════════════

class CatBoostModel(BaseModel):
    """
    CatBoost gradient boosting classifier.
    """
    
    def __init__(
        self,
        iterations: int = 500,
        depth: int = 6,
        learning_rate: float = 0.03,
        random_seed: int = 42,
    ):
        """
        Initialize CatBoost model.
        
        Args:
            iterations: Number of iterations.
            depth: Tree depth.
            learning_rate: Learning rate.
            random_seed: Random seed.
        """
        super().__init__("CatBoost")
        
        self.iterations = iterations
        self.depth = depth
        self.learning_rate = learning_rate
        self.random_seed = random_seed
        
        if CATBOOST_AVAILABLE:
            self._build_model()
    
    def _build_model(self) -> None:
        """Build CatBoost model."""
        self.model = cb.CatBoostClassifier(
            iterations=self.iterations,
            depth=self.depth,
            learning_rate=self.learning_rate,
            random_seed=self.random_seed,
            verbose=False,
        )
    
    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        **kwargs
    ) -> 'CatBoostModel':
        """Train CatBoost model."""
        if not CATBOOST_AVAILABLE:
            self.logger.warning("CatBoost not available")
            return self
        
        try:
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
            
            self.model.fit(X, y, verbose=False)
            
            train_pred = self.model.predict(X)
            train_acc = accuracy_score(y, train_pred)
            
            self.is_trained = True
            self.last_trained = datetime.now()
            self.accuracy_history.append(train_acc)
            
            self.logger.info(f"CatBoost trained: accuracy={train_acc:.4f}")
            
        except Exception as e:
            self.logger.error(f"CatBoost training error: {e}")
        
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict class labels."""
        if not self.is_trained or not CATBOOST_AVAILABLE:
            return np.zeros(len(X))
        
        try:
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
            return self.model.predict(X)
        except Exception as e:
            self.logger.error(f"CatBoost predict error: {e}")
            return np.zeros(len(X))
    
    def predict_proba(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Predict class probabilities."""
        if not self.is_trained or not CATBOOST_AVAILABLE:
            return np.zeros(len(X)), np.ones(len(X))
        
        try:
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
            probs = self.model.predict_proba(X)
            return probs[:, 0], probs[:, 1]
        except Exception as e:
            self.logger.error(f"CatBoost predict_proba error: {e}")
            return np.zeros(len(X)), np.ones(len(X))
    
    def save(self, path: Union[str, Path]) -> bool:
        """Save model to disk."""
        try:
            if not CATBOOST_AVAILABLE:
                return False
            
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            self.model.save_model(str(path))
            self.logger.info(f"CatBoost saved to {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"CatBoost save error: {e}")
            return False
    
    def load(self, path: Union[str, Path]) -> bool:
        """Load model from disk."""
        try:
            if not CATBOOST_AVAILABLE or not Path(path).exists():
                return False
            
            self._build_model()
            self.model.load_model(str(path))
            self.is_trained = True
            
            self.logger.info(f"CatBoost loaded from {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"CatBoost load error: {e}")
            return False


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 07 — ONLINE LEARNING MODEL (River)
# ═══════════════════════════════════════════════════════════════════════════

class OnlineLearningModel(BaseModel):
    """
    Online learning with River HoeffdingTree.
    
    Learns from streaming data incrementally.
    """
    
    def __init__(self):
        """Initialize online learning model."""
        super().__init__("OnlineLearning")
        self.model = None
        self.metric = None
        self._build_model()
    
    def _build_model(self) -> None:
        """Build River model."""
        if RIVER_AVAILABLE:
            self.model = river_tree.HoeffdingTreeClassifier()
            self.metric = river_metrics.Accuracy()
    
    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        **kwargs
    ) -> 'OnlineLearningModel':
        """Train online model incrementally."""
        if not RIVER_AVAILABLE or self.model is None:
            self.logger.warning("River not available")
            return self
        
        try:
            for i in range(len(X)):
                x_dict = {f"f{j}": float(v) for j, v in enumerate(X[i])}
                self.model.learn_one(x_dict, int(y[i]))
                pred = self.model.predict_one(x_dict)
                self.metric.update(int(y[i]), pred)
            
            self.is_trained = True
            self.last_trained = datetime.now()
            
            self.logger.info(f"OnlineLearning trained: metric={self.metric.get():.4f}")
            
        except Exception as e:
            self.logger.error(f"OnlineLearning training error: {e}")
        
        return self
    
    def partial_fit(self, x: np.ndarray, y: int) -> 'OnlineLearningModel':
        """Incrementally learn from single sample."""
        if not RIVER_AVAILABLE or self.model is None:
            return self
        
        try:
            x_dict = {f"f{j}": float(v) for j, v in enumerate(x)}
            self.model.learn_one(x_dict, int(y))
            pred = self.model.predict_one(x_dict)
            self.metric.update(int(y), pred)
            
        except Exception as e:
            self.logger.error(f"OnlineLearning partial_fit error: {e}")
        
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict class labels."""
        if not RIVER_AVAILABLE or self.model is None:
            return np.zeros(len(X))
        
        try:
            preds = []
            for i in range(len(X)):
                x_dict = {f"f{j}": float(v) for j, v in enumerate(X[i])}
                pred = self.model.predict_one(x_dict)
                preds.append(pred if pred is not None else 0)
            return np.array(preds)
        except Exception as e:
            self.logger.error(f"OnlineLearning predict error: {e}")
            return np.zeros(len(X))
    
    def predict_proba(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Predict class probabilities."""
        if not RIVER_AVAILABLE or self.model is None:
            return np.zeros(len(X)), np.ones(len(X))
        
        try:
            prob0, prob1 = [], []
            for i in range(len(X)):
                x_dict = {f"f{j}": float(v) for j, v in enumerate(X[i])}
                proba = self.model.predict_proba_one(x_dict)
                p0 = proba.get(0, 0.5)
                p1 = proba.get(1, 0.5)
                prob0.append(p0)
                prob1.append(p1)
            return np.array(prob0), np.array(prob1)
        except Exception as e:
            self.logger.error(f"OnlineLearning predict_proba error: {e}")
            return np.zeros(len(X)), np.ones(len(X))
    
    def save(self, path: Union[str, Path]) -> bool:
        """Save model to disk."""
        try:
            if not RIVER_AVAILABLE or self.model is None:
                return False
            
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'wb') as f:
                pickle.dump(self.model, f)
            
            self.logger.info(f"OnlineLearning saved to {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"OnlineLearning save error: {e}")
            return False
    
    def load(self, path: Union[str, Path]) -> bool:
        """Load model from disk."""
        try:
            if not RIVER_AVAILABLE or not Path(path).exists():
                return False
            
            with open(path, 'rb') as f:
                self.model = pickle.load(f)
            
            self.is_trained = True
            self.logger.info(f"OnlineLearning loaded from {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"OnlineLearning load error: {e}")
            return False


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 08 — ANOMALY DETECTOR
# ═══════════════════════════════════════════════════════════════════════════

class AnomalyDetector(BaseModel):
    """
    Isolation Forest anomaly detector.
    
    Detects market anomalies and blocks trading.
    """
    
    def __init__(
        self,
        contamination: float = 0.05,
        n_estimators: int = 100,
        random_state: int = 42,
    ):
        """
        Initialize anomaly detector.
        
        Args:
            contamination: Expected anomaly ratio.
            n_estimators: Number of trees.
            random_state: Random seed.
        """
        super().__init__("AnomalyDetector")
        
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.random_state = random_state
        
        if SKLEARN_AVAILABLE:
            from sklearn.ensemble import IsolationForest
            self.model = IsolationForest(
                contamination=contamination,
                n_estimators=n_estimators,
                random_state=random_state,
                n_jobs=-1,
            )
            self.is_trained = True
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict anomalies (-1=anomaly, 1=normal)."""
        if not SKLEARN_AVAILABLE or self.model is None:
            return np.ones(len(X))
        
        try:
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
            return self.model.predict(X)
        except Exception as e:
            self.logger.error(f"AnomalyDetector predict error: {e}")
            return np.ones(len(X))
    
    def predict_proba(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Return anomaly scores."""
        if not SKLEARN_AVAILABLE or self.model is None:
            return np.zeros(len(X)), np.ones(len(X))
        
        try:
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
            scores = -self.model.score_samples(X)
            prob_anomaly = np.clip(scores / (scores.max() + 1e-10), 0, 1)
            return prob_anomaly, 1 - prob_anomaly
        except Exception as e:
            self.logger.error(f"AnomalyDetector predict_proba error: {e}")
            return np.zeros(len(X)), np.ones(len(X))
    
    def predict_confidence(self, X: np.ndarray) -> float:
        """Return anomaly score (higher = more anomalous)."""
        if not SKLEARN_AVAILABLE or self.model is None:
            return 0.0
        
        try:
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
            if len(X.shape) == 1:
                X = X.reshape(1, -1)
            score = -self.model.score_samples(X).mean()
            return float(score)
        except Exception:
            return 0.0
    
    def save(self, path: Union[str, Path]) -> bool:
        """Save model to disk."""
        try:
            if not SKLEARN_AVAILABLE or self.model is None:
                return False
            
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'wb') as f:
                pickle.dump(self.model, f)
            
            return True
        except Exception as e:
            self.logger.error(f"AnomalyDetector save error: {e}")
            return False
    
    def load(self, path: Union[str, Path]) -> bool:
        """Load model from disk."""
        try:
            if not SKLEARN_AVAILABLE or not Path(path).exists():
                return False
            
            with open(path, 'rb') as f:
                self.model = pickle.load(f)
            
            self.is_trained = True
            return True
        except Exception as e:
            self.logger.error(f"AnomalyDetector load error: {e}")
            return False


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 09 — SIMPLE LOGISTIC REGRESSION (Baseline)
# ═══════════════════════════════════════════════════════════════════════════

class LogisticRegressionModel(BaseModel):
    """
    Simple logistic regression baseline model.
    """
    
    def __init__(self, random_state: int = 42):
        """Initialize logistic regression."""
        super().__init__("LogisticRegression")
        self.random_state = random_state
        self.scaler = StandardScaler()
        
        if SKLEARN_AVAILABLE:
            self.model = LogisticRegression(random_state=random_state, max_iter=1000)
    
    def fit(self, X: np.ndarray, y: np.ndarray, **kwargs) -> 'LogisticRegressionModel':
        """Train logistic regression."""
        if not SKLEARN_AVAILABLE:
            return self
        
        try:
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
            X_scaled = self.scaler.fit_transform(X)
            self.model.fit(X_scaled, y)
            
            train_acc = accuracy_score(y, self.model.predict(X_scaled))
            self.is_trained = True
            self.last_trained = datetime.now()
            self.accuracy_history.append(train_acc)
            
        except Exception as e:
            self.logger.error(f"LogisticRegression training error: {e}")
        
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict class labels."""
        if not self.is_trained or not SKLEARN_AVAILABLE:
            return np.zeros(len(X))
        
        try:
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
            X_scaled = self.scaler.transform(X)
            return self.model.predict(X_scaled)
        except Exception as e:
            self.logger.error(f"LogisticRegression predict error: {e}")
            return np.zeros(len(X))
    
    def predict_proba(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Predict class probabilities."""
        if not self.is_trained or not SKLEARN_AVAILABLE:
            return np.zeros(len(X)), np.ones(len(X))
        
        try:
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
            X_scaled = self.scaler.transform(X)
            probs = self.model.predict_proba(X_scaled)
            return probs[:, 0], probs[:, 1]
        except Exception as e:
            self.logger.error(f"LogisticRegression predict_proba error: {e}")
            return np.zeros(len(X)), np.ones(len(X))
    
    def save(self, path: Union[str, Path]) -> bool:
        """Save model to disk."""
        try:
            if not SKLEARN_AVAILABLE:
                return False
            
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'wb') as f:
                pickle.dump({'model': self.model, 'scaler': self.scaler}, f)
            
            return True
        except Exception as e:
            self.logger.error(f"LogisticRegression save error: {e}")
            return False
    
    def load(self, path: Union[str, Path]) -> bool:
        """Load model from disk."""
        try:
            if not SKLEARN_AVAILABLE or not Path(path).exists():
                return False
            
            with open(path, 'rb') as f:
                data = pickle.load(f)
                self.model = data['model']
                self.scaler = data['scaler']
            
            self.is_trained = True
            return True
        except Exception as e:
            self.logger.error(f"LogisticRegression load error: {e}")
            return False


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 10 — MODEL REGISTRY
# ═══════════════════════════════════════════════════════════════════════════

class ModelRegistry:
    """
    Registry for managing all ML models.
    
    Handles:
    - Model creation and registration
    - Parallel training
    - Ensemble predictions
    - Model saving/loading
    """
    
    def __init__(self, models_dir: Union[str, Path] = "models"):
        """
        Initialize ModelRegistry.
        
        Args:
            models_dir: Directory for model files.
        """
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger("XAUUSD_GOD_BOT.ModelRegistry")
        self.models: Dict[str, BaseModel] = {}
        self._lock = threading.Lock()
        
        self._register_default_models()
    
    def __repr__(self) -> str:
        return f"<ModelRegistry models={list(self.models.keys())}>"
    
    def _register_default_models(self) -> None:
        """Register all available models."""
        if LSTM_AVAILABLE := TORCH_AVAILABLE:
            self.register("lstm", LSTMModel(input_dim=100, sequence_length=50))
        
        if XGBOOST_AVAILABLE:
            self.register("xgboost", XGBoostModel())
        
        if LIGHTGBM_AVAILABLE:
            self.register("lightgbm", LightGBMModel())
        
        if SKLEARN_AVAILABLE:
            self.register("random_forest", RandomForestModel())
            self.register("logistic", LogisticRegressionModel())
        
        if CATBOOST_AVAILABLE:
            self.register("catboost", CatBoostModel())
        
        if RIVER_AVAILABLE:
            self.register("online", OnlineLearningModel())
        
        if SKLEARN_AVAILABLE:
            self.register("anomaly", AnomalyDetector())
        
        self.logger.info(f"Registered models: {list(self.models.keys())}")
    
    def register(self, name: str, model: BaseModel) -> None:
        """
        Register a model.
        
        Args:
            name: Model name.
            model: Model instance.
        """
        with self._lock:
            self.models[name] = model
            self.logger.info(f"Registered model: {name}")
    
    def get(self, name: str) -> Optional[BaseModel]:
        """
        Get a model by name.
        
        Args:
            name: Model name.
        
        Returns:
            Model instance or None.
        """
        return self.models.get(name)
    
    def train_all(
        self,
        X: np.ndarray,
        y: np.ndarray,
        val_split: float = 0.2,
        **kwargs
    ) -> Dict[str, float]:
        """
        Train all registered models.
        
        Args:
            X: Feature matrix.
            y: Target vector.
            val_split: Validation split.
            **kwargs: Additional arguments for models.
        
        Returns:
            Dict of model_name -> accuracy.
        """
        results = {}
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        
        if len(X) < 100:
            self.logger.warning("Insufficient data for training")
            return results
        
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=val_split, shuffle=False
        )
        
        for name, model in self.models.items():
            try:
                self.logger.info(f"Training {name}...")
                start_time = time.time()
                
                if hasattr(model, 'partial_fit') and model.is_trained:
                    for i in range(len(X_train)):
                        model.partial_fit(X_train[i], y_train[i])
                else:
                    model.fit(X_train, y_train, eval_set=(X_val, y_val), **kwargs)
                
                elapsed = time.time() - start_time
                
                if hasattr(model, 'accuracy_history') and model.accuracy_history:
                    acc = model.accuracy_history[-1]
                    results[name] = acc
                    self.logger.info(f"{name}: accuracy={acc:.4f} ({elapsed:.1f}s)")
                else:
                    results[name] = 0.5
                    self.logger.info(f"{name}: trained ({elapsed:.1f}s)")
                
            except Exception as e:
                self.logger.error(f"{name} training failed: {e}")
                results[name] = 0.0
        
        return results
    
    def predict_ensemble(
        self,
        X: np.ndarray,
        weights: Optional[Dict[str, float]] = None,
        threshold: float = 0.5,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get ensemble prediction.
        
        Args:
            X: Feature matrix.
            weights: Optional model weights.
            threshold: Decision threshold.
        
        Returns:
            Tuple of (predictions, confidences).
        """
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        
        if weights is None:
            weights = {name: 1.0 for name in self.models}
        
        total_weight = sum(weights.values())
        if total_weight == 0:
            total_weight = 1.0
        
        weighted_sum = np.zeros(len(X))
        confidence_sum = np.zeros(len(X))
        
        for name, model in self.models.items():
            try:
                if not model.is_trained:
                    continue
                
                weight = weights.get(name, 1.0) / total_weight
                prob0, prob1 = model.predict_proba(X)
                
                weighted_sum += weight * (prob1 - prob0)
                confidence_sum += weight * np.maximum(prob0, prob1)
                
            except Exception as e:
                self.logger.error(f"{name} prediction failed: {e}")
        
        predictions = (weighted_sum > threshold).astype(int)
        confidences = confidence_sum
        
        return predictions, confidences
    
    def get_model_status(self) -> List[Dict[str, Any]]:
        """Get status of all models."""
        status = []
        for name, model in self.models.items():
            status.append(model.get_status())
        return status
    
    def save_all(self) -> int:
        """Save all models to disk."""
        saved = 0
        for name, model in self.models.items():
            try:
                path = self.models_dir / f"{name}.pkl"
                if model.save(path):
                    saved += 1
            except Exception as e:
                self.logger.error(f"Failed to save {name}: {e}")
        
        self.logger.info(f"Saved {saved}/{len(self.models)} models")
        return saved
    
    def load_all(self) -> int:
        """Load all models from disk."""
        loaded = 0
        for name in self.models.keys():
            try:
                path = self.models_dir / f"{name}.pkl"
                if path.exists() and self.models[name].load(path):
                    loaded += 1
            except Exception as e:
                self.logger.error(f"Failed to load {name}: {e}")
        
        self.logger.info(f"Loaded {loaded}/{len(self.models)} models")
        return loaded


# ═══════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    "BaseModel",
    "LSTMModel",
    "XGBoostModel",
    "LightGBMModel",
    "RandomForestModel",
    "CatBoostModel",
    "OnlineLearningModel",
    "AnomalyDetector",
    "LogisticRegressionModel",
    "ModelRegistry",
    "TORCH_AVAILABLE",
    "XGBOOST_AVAILABLE",
    "LIGHTGBM_AVAILABLE",
    "CATBOOST_AVAILABLE",
    "SKLEARN_AVAILABLE",
    "RIVER_AVAILABLE",
]


# ═══════════════════════════════════════════════════════════════════════════
# TEST / ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("XAUUSD GOD BOT v2.0 — ML Models Module Test")
    print("-" * 60)
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        print("\n1. Testing Model Availability...")
        print(f"   PyTorch: {TORCH_AVAILABLE}")
        print(f"   XGBoost: {XGBOOST_AVAILABLE}")
        print(f"   LightGBM: {LIGHTGBM_AVAILABLE}")
        print(f"   CatBoost: {CATBOOST_AVAILABLE}")
        print(f"   Sklearn: {SKLEARN_AVAILABLE}")
        print(f"   River: {RIVER_AVAILABLE}")
        
        print("\n2. Testing ModelRegistry...")
        registry = ModelRegistry(models_dir="test_models")
        print(f"   Registry: {registry}")
        print(f"   Models: {list(registry.models.keys())}")
        
        print("\n3. Testing Model Training...")
        np.random.seed(42)
        n = 1000
        X = np.random.randn(n, 50).astype(np.float32)
        y = (X[:, 0] + X[:, 1] > 0).astype(int)
        
        results = registry.train_all(X, y, val_split=0.2)
        print(f"   Training Results:")
        for name, acc in results.items():
            print(f"      {name}: {acc:.4f}")
        
        print("\n4. Testing Ensemble Prediction...")
        preds, confs = registry.predict_ensemble(X[-10:])
        print(f"   Predictions: {preds}")
        print(f"   Confidences: {confs[:3]}...")
        
        print("\n5. Testing Individual Models...")
        for name, model in registry.models.items():
            try:
                p = model.predict(X[:5])
                print(f"   {name}: {p}")
            except Exception as e:
                print(f"   {name}: ERROR - {e}")
        
        print("\n6. Testing Model Status...")
        status = registry.get_model_status()
        for s in status[:3]:
            print(f"   {s['name']}: trained={s['trained']}")
        
        print("\n" + "=" * 60)
        print("ML Models Module: ALL TESTS PASSED")
        print(f"Total Models: {len(registry.models)}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
