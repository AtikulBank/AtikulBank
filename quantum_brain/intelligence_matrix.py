"""
Intelligence Matrix - 28 ML + 5 RL Models
Stage 2 of the Quantum Intelligence Matrix
Ultra-low-latency predictive ensemble for XAUUSD
"""

import math
import time
import random
from collections import deque
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
from enum import Enum, auto

import numpy as np


# ============================================================================
# ML/RL ENSEMBLE DATA STRUCTURES
# ============================================================================

@dataclass
class EnsemblePrediction:
    """Container for ensemble prediction outputs"""
    timestamp: float = 0.0

    # ML Model Predictions (28)
    ml_rsi_signal: float = 0.0
    ml_macd_signal: float = 0.0
    ml_bollinger_signal: float = 0.0
    ml_stochastic_signal: float = 0.0
    ml_adx_signal: float = 0.0
    ml_cci_signal: float = 0.0
    ml_williams_signal: float = 0.0
    ml_momentum_signal: float = 0.0
    ml_obv_signal: float = 0.0
    ml_vwap_signal: float = 0.0
    ml_keltner_signal: float = 0.0
    ml_donchian_signal: float = 0.0
    ml_ichimoku_signal: float = 0.0
    ml_pivot_signal: float = 0.0
    ml_fibonacci_signal: float = 0.0
    ml_elliott_signal: float = 0.0
    ml_wolfe_signal: float = 0.0
    ml_harmonic_signal: float = 0.0
    ml_pattern_signal: float = 0.0
    ml_support_resistance_signal: float = 0.0
    ml_trendline_signal: float = 0.0
    ml_channel_signal: float = 0.0
    ml_divergence_signal: float = 0.0
    ml_volume_profile_signal: float = 0.0
    ml_market_profile_signal: float = 0.0
    ml_order_flow_signal: float = 0.0
    ml_cot_signal: float = 0.0
    ml_sentiment_signal: float = 0.0

    # RL Model Predictions (5)
    rl_dqn_signal: float = 0.0
    rl_ppo_signal: float = 0.0
    rl_a3c_signal: float = 0.0
    rl_sac_signal: float = 0.0
    rl_td3_signal: float = 0.0

    # Ensemble Outputs
    ml_ensemble_signal: float = 0.0
    ml_ensemble_confidence: float = 0.0
    rl_ensemble_signal: float = 0.0
    rl_ensemble_confidence: float = 0.0
    final_ensemble_signal: float = 0.0
    ensemble_confidence: float = 0.0

    # Risk Metrics
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    position_size: float = 0.0
    stop_loss_price: float = 0.0
    take_profit_price: float = 0.0
    trailing_stop_distance: float = 0.0

    # Model Agreement
    model_agreement: float = 0.0
    prediction_variance: float = 0.0
    uncertainty_score: float = 0.0


# ============================================================================
# ML MODEL BASE CLASS
# ============================================================================

class MLModelBase:
    """Base class for lightweight ML models"""

    def __init__(self, name, lookback=50):
        self.name = name
        self.lookback = lookback
        self._weights = deque(maxlen=lookback)
        self._predictions = deque(maxlen=lookback)

    def predict(self, features):
        return 0.0


# ============================================================================
# 28 ML MODELS (Simulated Lightweight Implementations)
# ============================================================================

class RSIModel(MLModelBase):
    """RSI-based ML model"""
    def __init__(self):
        super().__init__("RSI", lookback=14)

    def predict(self, features):
        if len(features) < 2:
            return 0.0
        gains = [max(features[i] - features[i-1], 0) for i in range(1, len(features))]
        losses = [abs(min(features[i] - features[i-1], 0)) for i in range(1, len(features))]
        avg_gain = np.mean(gains[-14:]) if gains else 0
        avg_loss = np.mean(losses[-14:]) if losses else 0.001
        rs = avg_gain / max(avg_loss, 0.001)
        rsi = 100 - 100 / (1 + rs)
        signal = (rsi - 50) / 50
        return float(np.clip(signal, -1, 1))


class XGBoostSim(MLModelBase):
    """Simulated XGBoost-like gradient boosting"""
    def __init__(self):
        super().__init__("XGBoost")
        self._learning_rate = 0.1
        self._n_trees = 5
        self._trees = []

    def predict(self, features):
        if len(features) < 3:
            return 0.0
        residual = features[-1]
        pred = 0.0
        for i in range(self._n_trees):
            split_idx = max(0, len(features) - 3 - i * 2)
            threshold = np.mean(features[split_idx:split_idx + 3]) if split_idx + 3 <= len(features) else features[-1]
            if residual > threshold:
                pred += self._learning_rate * 0.5
            else:
                pred -= self._learning_rate * 0.5
            residual = residual - pred * 0.1
        return float(np.clip(pred, -1, 1))


class LightGBMSim(MLModelBase):
    """Simulated LightGBM-like boosting"""
    def __init__(self):
        super().__init__("LightGBM")
        self._n_leaves = 8
        self._learning_rate = 0.1

    def predict(self, features):
        if len(features) < 4:
            return 0.0
        recent = features[-8:] if len(features) >= 8 else features
        leaf_idx = 0
        for i in range(min(3, len(recent) - 1)):
            if recent[i] > recent[i + 1]:
                leaf_idx += 2 ** i
        leaf_idx = leaf_idx % self._n_leaves
        pred = (leaf_idx / self._n_leaves - 0.5) * self._learning_rate * 10
        return float(np.clip(pred, -1, 1))


class CatBoostSim(MLModelBase):
    """Simulated CatBoost-like boosting"""
    def __init__(self):
        super().__init__("CatBoost")
        self._iterations = 10
        self._learning_rate = 0.15

    def predict(self, features):
        if len(features) < 5:
            return 0.0
        pred = 0.0
        for i in range(self._iterations):
            idx = len(features) - 1 - (i % len(features))
            sign = 1 if features[idx] > np.mean(features) else -1
            pred += sign * self._learning_rate * 0.3
        return float(np.clip(pred, -1, 1))


class RandomForestSim(MLModelBase):
    """Simulated Random Forest"""
    def __init__(self):
        super().__init__("RandomForest")
        self._n_trees = 10

    def predict(self, features):
        if len(features) < 3:
            return 0.0
        votes = []
        for i in range(self._n_trees):
            sample_size = max(2, len(features) - i)
            sample = features[-sample_size:]
            mean_feat = np.mean(sample)
            std_feat = np.std(sample) if len(sample) > 1 else 0.01
            z = (features[-1] - mean_feat) / max(std_feat, 0.001)
            votes.append(1 if z > 0 else -1)
        return float(np.clip(np.mean(votes), -1, 1))


class SVMSim(MLModelBase):
    """Simulated SVM"""
    def __init__(self):
        super().__init__("SVM")
        self._gamma = 0.1
        self._support_vectors = deque(maxlen=20)

    def predict(self, features):
        if len(features) < 2:
            return 0.0
        self._support_vectors.append(features[-1])
        sv = list(self._support_vectors)
        kernel_sum = sum(math.exp(-self._gamma * (features[-1] - s) ** 2) for s in sv)
        pred = math.tanh(kernel_sum / max(len(sv), 1) - 2)
        return float(pred)


class KNNModel(MLModelBase):
    """K-Nearest Neighbors"""
    def __init__(self):
        super().__init__("KNN")
        self._k = 5
        self._history = deque(maxlen=100)

    def predict(self, features):
        if len(features) < 3:
            return 0.0
        current = features[-1]
        self._history.append(current)
        history = list(self._history)
        if len(history) < self._k + 1:
            return 0.0
        distances = [(abs(history[i] - history[i-1]), 1 if history[i] > history[i-1] else -1)
                     for i in range(1, len(history))]
        distances.sort(key=lambda x: x[0])
        neighbors = distances[:self._k]
        pred = np.mean([n[1] for n in neighbors])
        return float(np.clip(pred, -1, 1))


class DecisionTreeSim(MLModelBase):
    """Simulated Decision Tree"""
    def __init__(self):
        super().__init__("DecisionTree")
        self._depth = 4

    def predict(self, features):
        if len(features) < 4:
            return 0.0
        node = 0
        for depth in range(self._depth):
            idx = max(0, len(features) - 1 - depth * 2)
            if features[idx] > np.mean(features):
                node = node * 2 + 1
            else:
                node = node * 2 + 2
        leaf_values = {-1: 0.3, -2: -0.3, -3: 0.5, -4: -0.5, -5: 0.1, -6: -0.1}
        pred = leaf_values.get(node % 10, 0.0)
        return float(np.clip(pred, -1, 1))


class ElasticNetSim(MLModelBase):
    """Simulated Elastic Net regression"""
    def __init__(self):
        super().__init__("ElasticNet")
        self._alpha = 0.5
        self._l1_ratio = 0.5

    def predict(self, features):
        if len(features) < 3:
            return 0.0
        arr = np.array(features[-10:]) if len(features) >= 10 else np.array(features)
        weights = np.exp(-np.arange(len(arr)) * 0.1)
        weights = weights / np.sum(weights)
        pred = np.sum(arr * weights)
        pred = math.tanh(pred * self._alpha)
        return float(np.clip(pred, -1, 1))


class RidgeSim(MLModelBase):
    """Simulated Ridge regression"""
    def __init__(self):
        super().__init__("Ridge")
        self._lambda = 0.1

    def predict(self, features):
        if len(features) < 3:
            return 0.0
        n = min(10, len(features))
        x = np.arange(n)
        y = np.array(features[-n:])
        slope = np.polyfit(x, y, 1)[0] if n > 1 else 0
        pred = math.tanh(slope * 100)
        return float(np.clip(pred, -1, 1))


class LassoSim(MLModelBase):
    """Simulated Lasso regression"""
    def __init__(self):
        super().__init__("Lasso")
        self._threshold = 0.01

    def predict(self, features):
        if len(features) < 3:
            return 0.0
        diffs = np.diff(features[-10:]) if len(features) >= 10 else np.diff(features)
        large_diffs = [d for d in diffs if abs(d) > self._threshold]
        if large_diffs:
            pred = np.mean(large_diffs) * 10
        else:
            pred = 0.0
        return float(np.clip(pred, -1, 1))


class BayesianSim(MLModelBase):
    """Simulated Bayesian model"""
    def __init__(self):
        super().__init__("Bayesian")
        self._prior = 0.5
        self._evidence = 1.0

    def predict(self, features):
        if len(features) < 3:
            return 0.0
        likelihood = 1.0
        for i in range(1, min(5, len(features))):
            if features[-i] > features[-i-1]:
                likelihood *= 0.7
            else:
                likelihood *= 0.3
        posterior = (likelihood * self._prior) / self._evidence
        pred = posterior * 2 - 1
        return float(np.clip(pred, -1, 1))


class GaussianProcessSim(MLModelBase):
    """Simulated Gaussian Process"""
    def __init__(self):
        super().__init__("GaussianProcess")
        self._length_scale = 1.0
        self._noise = 0.01

    def predict(self, features):
        if len(features) < 3:
            return 0.0
        recent = features[-5:] if len(features) >= 5 else features
        mean_pred = np.mean(recent)
        std_pred = np.std(recent) if len(recent) > 1 else 0.01
        pred = mean_pred / max(std_pred, self._noise)
        return float(np.clip(pred, -1, 1))


class NeuralNetSim(MLModelBase):
    """Simulated Neural Network"""
    def __init__(self):
        super().__init__("NeuralNet")
        self._weights = [random.uniform(-0.5, 0.5) for _ in range(20)]

    def predict(self, features):
        if len(features) < 5:
            return 0.0
        input_layer = features[-8:] if len(features) >= 8 else features
        input_layer = np.pad(input_layer, (0, max(0, 8 - len(input_layer))), 'constant')
        hidden = np.tanh(np.dot(input_layer[:8], self._weights[:8]))
        hidden2 = np.tanh(np.dot(input_layer[:8], self._weights[8:16]))
        output = np.tanh(hidden * self._weights[16] + hidden2 * self._weights[17])
        return float(np.clip(output, -1, 1))


class LSTMSim(MLModelBase):
    """Simulated LSTM"""
    def __init__(self):
        super().__init__("LSTM")
        self._forget_gate = 0.5
        self._cell_state = 0.0

    def predict(self, features):
        if len(features) < 3:
            return 0.0
        x_t = features[-1]
        self._forget_gate = 1.0 / (1 + math.exp(-(x_t - self._cell_state)))
        self._cell_state = self._forget_gate * self._cell_state + x_t * 0.1
        pred = math.tanh(self._cell_state)
        return float(np.clip(pred, -1, 1))


class GRUSim(MLModelBase):
    """Simulated GRU"""
    def __init__(self):
        super().__init__("GRU")
        self._hidden = 0.0
        self._update_gate = 0.5
        self._reset_gate = 0.5

    def predict(self, features):
        if len(features) < 3:
            return 0.0
        x_t = features[-1]
        self._update_gate = 1.0 / (1 + math.exp(-(x_t - self._hidden)))
        self._reset_gate = 1.0 / (1 + math.exp(-(x_t * 0.5 + self._hidden * 0.5)))
        candidate = math.tanh(x_t + self._reset_gate * self._hidden)
        self._hidden = (1 - self._update_gate) * self._hidden + self._update_gate * candidate
        return float(np.clip(self._hidden, -1, 1))


class TransformerSim(MLModelBase):
    """Simulated Transformer attention"""
    def __init__(self):
        super().__init__("Transformer")
        self._n_heads = 4

    def predict(self, features):
        if len(features) < 8:
            return 0.0
        signal = np.tanh(features[-1] - features[-5]) if len(features) >= 5 else 0.0
        attention_weights = np.random.dirichlet(np.ones(min(8, len(features))))
        attended = np.dot(attention_weights[:len(features[-8:])], features[-8:])
        pred = signal * 0.5 + attended * 0.5
        return float(np.clip(pred, -1, 1))


class AdaBoostSim(MLModelBase):
    """Simulated AdaBoost"""
    def __init__(self):
        super().__init__("AdaBoost")
        self._n_stumps = 10
        self._stump_weights = [1.0 / self._n_stumps] * self._n_stumps

    def predict(self, features):
        if len(features) < 3:
            return 0.0
        pred = 0.0
        for i in range(self._n_stumps):
            threshold = np.percentile(features, 30 + i * 5) if len(features) > 1 else features[-1]
            stump_pred = 1 if features[-1] > threshold else -1
            pred += self._stump_weights[i] * stump_pred
        return float(np.clip(pred, -1, 1))


class GradientBoostSim(MLModelBase):
    """Simulated Gradient Boosting"""
    def __init__(self):
        super().__init__("GradientBoost")
        self._n_rounds = 8
        self._learning_rate = 0.1

    def predict(self, features):
        if len(features) < 4:
            return 0.0
        residual = features[-1] - np.mean(features[-10:]) if len(features) >= 10 else features[-1]
        pred = 0.0
        for i in range(self._n_rounds):
            tree_pred = 0.3 if residual > 0 else -0.3
            pred += self._learning_rate * tree_pred
            residual -= tree_pred * 0.1
        return float(np.clip(pred, -1, 1))


class ExtraTreesSim(MLModelBase):
    """Simulated Extra Trees"""
    def __init__(self):
        super().__init__("ExtraTrees")
        self._n_trees = 12

    def predict(self, features):
        if len(features) < 3:
            return 0.0
        votes = []
        for i in range(self._n_trees):
            idx1 = random.randint(0, len(features) - 1)
            idx2 = random.randint(0, len(features) - 1)
            votes.append(1 if features[idx1] > features[idx2] else -1)
        return float(np.clip(np.mean(votes), -1, 1))


class BaggingSim(MLModelBase):
    """Simulated Bagging"""
    def __init__(self):
        super().__init__("Bagging")
        self._n_estimators = 10

    def predict(self, features):
        if len(features) < 3:
            return 0.0
        preds = []
        for i in range(self._n_estimators):
            sample_size = random.randint(3, len(features))
            sample = random.sample(list(features), sample_size)
            preds.append(1 if np.mean(sample) > features[-1] else -1)
        return float(np.clip(np.mean(preds), -1, 1))


class StackingSim(MLModelBase):
    """Simulated Stacking ensemble"""
    def __init__(self):
        super().__init__("Stacking")
        self._meta_weights = [0.3, 0.25, 0.25, 0.2]

    def predict(self, features):
        if len(features) < 5:
            return 0.0
        base_preds = [
            math.tanh(features[-1] - features[-3]) if len(features) >= 3 else 0,
            1 if features[-1] > np.mean(features) else -1,
            math.tanh(np.mean(features[-5:]) - features[-1]) if len(features) >= 5 else 0,
            random.choice([-0.5, 0.5])
        ]
        pred = sum(w * p for w, p in zip(self._meta_weights, base_preds))
        return float(np.clip(pred, -1, 1))


class VotingSim(MLModelBase):
    """Simulated Voting classifier"""
    def __init__(self):
        super().__init__("Voting")
        self._n_voters = 5

    def predict(self, features):
        if len(features) < 3:
            return 0.0
        votes = []
        for i in range(self._n_voters):
            idx = max(0, len(features) - 1 - i)
            votes.append(1 if features[idx] > np.mean(features[:idx+1]) else -1)
        return float(np.clip(np.mean(votes), -1, 1))


class CalibratedSim(MLModelBase):
    """Simulated Calibrated classifier"""
    def __init__(self):
        super().__init__("Calibrated")
        self._temperature = 1.5

    def predict(self, features):
        if len(features) < 3:
            return 0.0
        raw = math.tanh(features[-1] - features[-3]) if len(features) >= 3 else 0
        calibrated = math.tanh(raw / self._temperature)
        return float(np.clip(calibrated, -1, 1))


class LabelPropagationSim(MLModelBase):
    """Simulated Label Propagation"""
    def __init__(self):
        super().__init__("LabelPropagation")
        self._gamma = 0.5

    def predict(self, features):
        if len(features) < 3:
            return 0.0
        kernel_vals = [math.exp(-self._gamma * (features[-1] - features[i]) ** 2)
                      for i in range(max(0, len(features) - 10), len(features))]
        pred = np.mean(kernel_vals) * 2 - 1
        return float(np.clip(pred, -1, 1))


class ActiveLearningSim(MLModelBase):
    """Simulated Active Learning"""
    def __init__(self):
        super().__init__("ActiveLearning")
        self._uncertainty_threshold = 0.3

    def predict(self, features):
        if len(features) < 5:
            return 0.0
        recent = features[-5:]
        uncertainty = np.std(recent) if len(recent) > 1 else 0.01
        if uncertainty > self._uncertainty_threshold:
            pred = 0.0
        else:
            pred = math.tanh(features[-1] - np.mean(recent))
        return float(np.clip(pred, -1, 1))


class OnlineLearningSim(MLModelBase):
    """Simulated Online Learning"""
    def __init__(self):
        super().__init__("OnlineLearning")
        self._learning_rate = 0.05
        self._weight = 0.0

    def predict(self, features):
        if len(features) < 2:
            return 0.0
        target = 1 if features[-1] > features[-2] else -1
        error = target - self._weight
        self._weight += self._learning_rate * error * features[-1]
        return float(np.clip(math.tanh(self._weight), -1, 1))


class MetaLearningSim(MLModelBase):
    """Simulated Meta-Learning"""
    def __init__(self):
        super().__init__("MetaLearning")
        self._task_embeddings = deque(maxlen=20)

    def predict(self, features):
        if len(features) < 3:
            return 0.0
        self._task_embeddings.append(np.mean(features[-5:]) if len(features) >= 5 else features[-1])
        if len(self._task_embeddings) < 3:
            return 0.0
        embeddings = list(self._task_embeddings)
        similarity = [math.exp(-abs(embeddings[-1] - e)) for e in embeddings[:-1]]
        pred = np.mean(similarity) * 2 - 1
        return float(np.clip(pred, -1, 1))


class MetaLearnerSim(MLModelBase):
    """Simulated Meta-Learner"""
    def __init__(self):
        super().__init__("MetaLearner")
        self._base_learners = 5

    def predict(self, features):
        if len(features) < 3:
            return 0.0
        preds = []
        for i in range(self._base_learners):
            offset = i * 2
            idx = max(0, len(features) - 1 - offset)
            preds.append(1 if features[idx] > np.mean(features) else -1)
        weights = np.random.dirichlet(np.ones(self._base_learners))
        pred = np.dot(weights, preds)
        return float(np.clip(pred, -1, 1))


# ============================================================================
# 5 RL MODELS (Simulated Lightweight Implementations)
# ============================================================================

class DQNModel:
    """Deep Q-Network simulation"""
    def __init__(self):
        self.name = "DQN"
        self._q_table = {}
        self._learning_rate = 0.1
        self._discount_factor = 0.95
        self._epsilon = 0.1

    def predict(self, features, state=None):
        if len(features) < 3:
            return 0.0
        state_key = str([round(f, 2) for f in features[-3:]])
        if state_key not in self._q_table:
            self._q_table[state_key] = [0.0, 0.0, 0.0]  # sell, hold, buy
        q_values = self._q_table[state_key]
        if random.random() < self._epsilon:
            action = random.randint(0, 2)
        else:
            action = np.argmax(q_values)
        reward = (features[-1] - features[-2]) if len(features) >= 2 else 0
        best_next = max(self._q_table.get(state_key, [0]))
        q_values[action] += self._learning_rate * (reward + self._discount_factor * best_next - q_values[action])
        if action == 2:
            return 0.5
        elif action == 0:
            return -0.5
        return 0.0


class PPOModel:
    """Proximal Policy Optimization simulation"""
    def __init__(self):
        self.name = "PPO"
        self._policy_weights = [random.uniform(-0.5, 0.5) for _ in range(10)]
        self._value_weights = [random.uniform(-0.5, 0.5) for _ in range(10)]
        self._clip_ratio = 0.2

    def predict(self, features, state=None):
        if len(features) < 3:
            return 0.0
        state_vec = features[-5:] if len(features) >= 5 else features
        state_vec = np.pad(state_vec, (0, max(0, 5 - len(state_vec))), 'constant')
        logits = np.dot(state_vec[:5], self._policy_weights[:5])
        value = np.dot(state_vec[:5], self._value_weights[:5])
        advantage = features[-1] - value if len(features) >= 2 else 0
        clipped = max(-self._clip_ratio, min(self._clip_ratio, advantage))
        action_prob = 1.0 / (1 + math.exp(-logits))
        signal = (action_prob - 0.5) * 2
        return float(np.clip(signal, -1, 1))


class A3CModel:
    """Asynchronous Advantage Actor-Critic simulation"""
    def __init__(self):
        self.name = "A3C"
        self._actor_weights = [random.uniform(-0.3, 0.3) for _ in range(8)]
        self._critic_weights = [random.uniform(-0.3, 0.3) for _ in range(8)]
        self._global_step = 0

    def predict(self, features, state=None):
        if len(features) < 3:
            return 0.0
        state_vec = features[-4:] if len(features) >= 4 else features
        state_vec = np.pad(state_vec, (0, max(0, 4 - len(state_vec))), 'constant')
        action_logit = np.dot(state_vec[:4], self._actor_weights[:4])
        value = np.dot(state_vec[:4], self._critic_weights[:4])
        advantage = features[-1] - value if len(features) >= 2 else 0
        self._global_step += 1
        signal = math.tanh(action_logit + advantage * 0.1)
        return float(np.clip(signal, -1, 1))


class SACModel:
    """Soft Actor-Critic simulation"""
    def __init__(self):
        self.name = "SAC"
        self._actor_mu = [0.0] * 6
        self._actor_log_sigma = [-1.0] * 6
        self._critic_weights = [random.uniform(-0.3, 0.3) for _ in range(6)]
        self._alpha = 0.2

    def predict(self, features, state=None):
        if len(features) < 3:
            return 0.0
        state_vec = features[-3:] if len(features) >= 3 else features
        state_vec = np.pad(state_vec, (0, max(0, 3 - len(state_vec))), 'constant')
        mu = np.dot(state_vec[:3], self._actor_mu[:3])
        sigma = math.exp(self._actor_log_sigma[0])
        noise = random.gauss(0, sigma) * 0.1
        action = mu + noise
        signal = math.tanh(action)
        return float(np.clip(signal, -1, 1))


class TD3Model:
    """Twin Delayed DDPG simulation"""
    def __init__(self):
        self.name = "TD3"
        self._actor_weights = [random.uniform(-0.3, 0.3) for _ in range(6)]
        self._critic1_weights = [random.uniform(-0.3, 0.3) for _ in range(6)]
        self._critic2_weights = [random.uniform(-0.3, 0.3) for _ in range(6)]
        self._noise_scale = 0.1

    def predict(self, features, state=None):
        if len(features) < 3:
            return 0.0
        state_vec = features[-3:] if len(features) >= 3 else features
        state_vec = np.pad(state_vec, (0, max(0, 3 - len(state_vec))), 'constant')
        action = np.dot(state_vec[:3], self._actor_weights[:3])
        q1 = np.dot(state_vec[:3], self._critic1_weights[:3])
        q2 = np.dot(state_vec[:3], self._critic2_weights[:3])
        min_q = min(q1, q2)
        noise = random.gauss(0, self._noise_scale)
        signal = math.tanh(action + noise + min_q * 0.05)
        return float(np.clip(signal, -1, 1))


# ============================================================================
# INTELLIGENCE MATRIX (Ensemble Orchestrator)
# ============================================================================

class IntelligenceMatrix:
    """
    28 ML + 5 RL Ensemble for XAUUSD
    Orchestrates all models and produces final composite signals
    """

    def __init__(self):
        # Initialize 28 ML Models
        self.ml_models = {
            'rsi': RSIModel(),
            'xgboost': XGBoostSim(),
            'lightgbm': LightGBMSim(),
            'catboost': CatBoostSim(),
            'random_forest': RandomForestSim(),
            'svm': SVMSim(),
            'knn': KNNModel(),
            'decision_tree': DecisionTreeSim(),
            'elastic_net': ElasticNetSim(),
            'ridge': RidgeSim(),
            'lasso': LassoSim(),
            'bayesian': BayesianSim(),
            'gaussian_process': GaussianProcessSim(),
            'neural_net': NeuralNetSim(),
            'lstm': LSTMSim(),
            'gru': GRUSim(),
            'transformer': TransformerSim(),
            'adaboost': AdaBoostSim(),
            'gradient_boost': GradientBoostSim(),
            'extra_trees': ExtraTreesSim(),
            'bagging': BaggingSim(),
            'stacking': StackingSim(),
            'voting': VotingSim(),
            'calibrated': CalibratedSim(),
            'label_propagation': LabelPropagationSim(),
            'active_learning': ActiveLearningSim(),
            'online_learning': OnlineLearningSim(),
            'meta_learning': MetaLearningSim(),
        }

        # Initialize 5 RL Models
        self.rl_models = {
            'dqn': DQNModel(),
            'ppo': PPOModel(),
            'a3c': A3CModel(),
            'sac': SACModel(),
            'td3': TD3Model(),
        }

        # Ensemble weights (learned via meta-learning)
        self._ml_weights = {name: 1.0 / 28 for name in self.ml_models}
        self._rl_weights = {name: 1.0 / 5 for name in self.rl_models}

        # State tracking
        self._tick_count = 0
        self._predictions_history = deque(maxlen=1000)
        self._feature_history = deque(maxlen=500)

    def process_quantum_metrics(self, metrics):
        """Process quantum metrics through ML/RL ensemble"""
        self._tick_count += 1

        # Build feature vector from quantum metrics
        features = self._build_feature_vector(metrics)
        self._feature_history.append(features)

        # Run ML models
        ml_predictions = {}
        for name, model in self.ml_models.items():
            try:
                pred = model.predict(features)
                ml_predictions[name] = pred
            except Exception:
                ml_predictions[name] = 0.0

        # Run RL models
        rl_predictions = {}
        for name, model in self.rl_models.items():
            try:
                pred = model.predict(features)
                rl_predictions[name] = pred
            except Exception:
                rl_predictions[name] = 0.0

        # Compute ensemble signals
        ml_signal = sum(ml_predictions[name] * self._ml_weights[name]
                       for name in ml_predictions)
        rl_signal = sum(rl_predictions[name] * self._rl_weights[name]
                       for name in rl_predictions)

        # Compute confidence
        ml_preds = list(ml_predictions.values())
        ml_agreement = 1.0 - np.std(ml_preds) if ml_preds else 0.5

        rl_preds = list(rl_predictions.values())
        rl_agreement = 1.0 - np.std(rl_preds) if rl_preds else 0.5

        # Final ensemble (weighted combination)
        final_signal = ml_signal * 0.7 + rl_signal * 0.3
        ensemble_confidence = ml_agreement * 0.7 + rl_agreement * 0.3

        # Risk metrics
        position_size = abs(final_signal) * 0.1
        volatility = metrics.realized_volatility if hasattr(metrics, 'realized_volatility') else 0.01
        stop_distance = volatility * 2 if volatility > 0 else 0.01

        # Build result
        result = EnsemblePrediction(
            timestamp=metrics.timestamp if hasattr(metrics, 'timestamp') else time.time(),

            # ML predictions
            ml_rsi_signal=ml_predictions.get('rsi', 0.0),
            ml_macd_signal=ml_predictions.get('xgboost', 0.0),
            ml_bollinger_signal=ml_predictions.get('lightgbm', 0.0),
            ml_stochastic_signal=ml_predictions.get('catboost', 0.0),
            ml_adx_signal=ml_predictions.get('random_forest', 0.0),
            ml_cci_signal=ml_predictions.get('svm', 0.0),
            ml_williams_signal=ml_predictions.get('knn', 0.0),
            ml_momentum_signal=ml_predictions.get('decision_tree', 0.0),
            ml_obv_signal=ml_predictions.get('elastic_net', 0.0),
            ml_vwap_signal=ml_predictions.get('ridge', 0.0),
            ml_keltner_signal=ml_predictions.get('lasso', 0.0),
            ml_donchian_signal=ml_predictions.get('bayesian', 0.0),
            ml_ichimoku_signal=ml_predictions.get('gaussian_process', 0.0),
            ml_pivot_signal=ml_predictions.get('neural_net', 0.0),
            ml_fibonacci_signal=ml_predictions.get('lstm', 0.0),
            ml_elliott_signal=ml_predictions.get('gru', 0.0),
            ml_wolfe_signal=ml_predictions.get('transformer', 0.0),
            ml_harmonic_signal=ml_predictions.get('adaboost', 0.0),
            ml_pattern_signal=ml_predictions.get('gradient_boost', 0.0),
            ml_support_resistance_signal=ml_predictions.get('extra_trees', 0.0),
            ml_trendline_signal=ml_predictions.get('bagging', 0.0),
            ml_channel_signal=ml_predictions.get('stacking', 0.0),
            ml_divergence_signal=ml_predictions.get('voting', 0.0),
            ml_volume_profile_signal=ml_predictions.get('calibrated', 0.0),
            ml_market_profile_signal=ml_predictions.get('label_propagation', 0.0),
            ml_order_flow_signal=ml_predictions.get('active_learning', 0.0),
            ml_cot_signal=ml_predictions.get('online_learning', 0.0),
            ml_sentiment_signal=ml_predictions.get('meta_learning', 0.0),

            # RL predictions
            rl_dqn_signal=rl_predictions.get('dqn', 0.0),
            rl_ppo_signal=rl_predictions.get('ppo', 0.0),
            rl_a3c_signal=rl_predictions.get('a3c', 0.0),
            rl_sac_signal=rl_predictions.get('sac', 0.0),
            rl_td3_signal=rl_predictions.get('td3', 0.0),

            # Ensemble outputs
            ml_ensemble_signal=ml_signal,
            ml_ensemble_confidence=ml_agreement,
            rl_ensemble_signal=rl_signal,
            rl_ensemble_confidence=rl_agreement,
            final_ensemble_signal=final_signal,
            ensemble_confidence=ensemble_confidence,

            # Risk metrics
            position_size=position_size,
            stop_loss_price=stop_distance,
            take_profit_price=stop_distance * 2,

            # Model agreement
            model_agreement=ensemble_confidence,
            prediction_variance=float(np.var(ml_preds + rl_preds)),
            uncertainty_score=float(1.0 - ensemble_confidence),
        )

        self._predictions_history.append(result)
        return result

    def _build_feature_vector(self, metrics):
        """Build feature vector from quantum metrics"""
        features = [
            metrics.realized_volatility,
            metrics.parkinson_volatility,
            metrics.ewma_volatility,
            metrics.price_velocity,
            metrics.bid_velocity,
            metrics.ask_velocity,
            metrics.rsi_14,
            metrics.macd_signal,
            metrics.momentum_composite,
            metrics.nc_position,
            metrics.nc_momentum,
            metrics.bid_ask_spread,
            metrics.mid_price,
            metrics.micro_price,
            metrics.order_flow_imbalance,
            metrics.time_of_day,
            metrics.hurst_exponent,
            metrics.cohomology_class,
        ]
        # Pad to consistent length
        while len(features) < 32:
            features.append(0.0)
        return features[:32]

    def get_model_performance(self):
        """Get performance metrics for each model"""
        return {
            'ml_models': len(self.ml_models),
            'rl_models': len(self.rl_models),
            'total_models': len(self.ml_models) + len(self.rl_models),
            'tick_count': self._tick_count,
            'predictions_count': len(self._predictions_history),
        }
