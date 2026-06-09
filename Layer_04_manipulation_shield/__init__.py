"""
LAYER 4: MANIPULATION SHIELD
IsolationForest(168) → anomaly score
VPIN > 0.7 → REJECT
Lee-Ready direction classifier
Stop-hunt pattern detector
Fake breakout validator
Spread manipulation sensor
"""

from .manipulation_shield import ManipulationShield

__all__ = ["ManipulationShield"]