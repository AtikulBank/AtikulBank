#!/usr/bin/env python3
"""Test bot initialization and training"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from xauusd_god_bot import BotConfig, XAUUSDGodBot, EnsembleOrchestrator
import numpy as np

# Create a minimal config
config = BotConfig()
config.mode = 'demo'
config.tui_enabled = False

# Create ensemble
ensemble = EnsembleOrchestrator(config)

# Generate dummy data
np.random.seed(42)
X = np.random.randn(1000, 100)  # 1000 samples, 100 features
y = np.random.randint(0, 3, 1000)  # 3 classes

print(f"Ensemble has {len(ensemble.models)} models, {len(ensemble.rl_agents)} RL agents")
print("Models:", list(ensemble.models.keys()))

# Try to train
print("\nTraining all models...")
ensemble.train_all(X, y)

# Check which models are trained
print("\nModel status:")
for name, model in ensemble.models.items():
    print(f"  {name}: is_trained={model.is_trained}, train_count={model.train_count}")

# Try to predict
print("\nTesting prediction...")
X_test = np.random.randn(1, 100)
direction, agreement, preds = ensemble.predict_ensemble(X_test)
print(f"Ensemble direction: {direction:.3f}, agreement: {agreement:.1%}")
print(f"Predictions count: {len(preds)}")