"""
Quantum Brain - The Analytical Core
100+ Mathematical Filters + 100+ ML + 10+ RL Models
"""

from .mathematical_filters import QuantumMathEngine, QuantumMetrics
from .intelligence_matrix import IntelligenceMatrix, EnsemblePrediction
from .world_class_quantum_engine import WorldClassQuantumEngine
from .advanced_rl_agents import MathematicalFilterIntegration, EnhancedRLManager

# FIX 6: Connect comprehensive_ml_models
try:
    from .comprehensive_ml_models import (
        XGBoostEnsemble, LightGBMEnsemble, CatBoostEnsemble,
        BaseMLModel, ModelConfig, ModelMetrics, TrainingResult
    )
    COMPREHENSIVE_ML_AVAILABLE = True
except ImportError:
    COMPREHENSIVE_ML_AVAILABLE = False

__all__ = [
    'QuantumMathEngine', 'QuantumMetrics',
    'IntelligenceMatrix', 'EnsemblePrediction',
    'WorldClassQuantumEngine', 'MathematicalFilterIntegration', 'EnhancedRLManager',
]

if COMPREHENSIVE_ML_AVAILABLE:
    __all__.extend([
        'XGBoostEnsemble', 'LightGBMEnsemble', 'CatBoostEnsemble',
        'BaseMLModel', 'ModelConfig', 'ModelMetrics', 'TrainingResult',
    ])
