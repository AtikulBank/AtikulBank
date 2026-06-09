"""
LAYER 8: BAYESIAN ENSEMBLE FUSION
ML weights = softmax(recent_accuracy[30])
RL weights = softmax(recent_win_rate[10])
BMA posterior ∝ P(data|model) × P(model)
"""

from .bayesian_ensemble import BayesianEnsemble

__all__ = ["BayesianEnsemble"]