#!/usr/bin/env python3
"""
SCAN ALL MATHEMATICAL MODELS - Deep Analysis
=============================================
List all models and their working status
"""

import numpy as np
import sys
sys.path.insert(0, '.')

def scan_models():
    """Scan all mathematical models in the bot."""
    print("="*80)
    print("  DEEP SCAN OF ALL MATHEMATICAL MODELS")
    print("="*80)
    
    # Import the bot
    try:
        from xauusd_god_bot import (
            LSTMModel, TransformerModel, TCNModel, WaveNetModel,
            XGBoostModel, LightGBMModel, RandomForestModel, CatBoostModel,
            PPOAgent, MetaLearner, AnomalyDetectorModel, OnlineLearningModel,
            NBeatsModel, MambaModel, LiquidNNModel, NeuralODEModel, DiffusionModel
        )
        from xauusd_god_bot import BotConfig
        print("✅ Successfully imported all models")
    except Exception as e:
        print(f"❌ Import error: {e}")
        return
    
    # Create config
    config = BotConfig()
    
    # List of all models
    models = [
        ("LSTM", LSTMModel),
        ("Transformer", TransformerModel),
        ("TCN", TCNModel),
        ("WaveNet", WaveNetModel),
        ("XGBoost", XGBoostModel),
        ("LightGBM", LightGBMModel),
        ("RandomForest", RandomForestModel),
        ("CatBoost", CatBoostModel),
        ("PPOAgent", PPOAgent),
        ("MetaLearner", MetaLearner),
        ("AnomalyDetector", AnomalyDetectorModel),
        ("OnlineLearning", OnlineLearningModel),
        ("NBeats", NBeatsModel),
        ("Mamba", MambaModel),
        ("LiquidNN", LiquidNNModel),
        ("NeuralODE", NeuralODEModel),
        ("Diffusion", DiffusionModel),
    ]
    
    print("\n" + "="*80)
    print("  MODEL STATUS")
    print("="*80)
    
    working_models = []
    fake_models = []
    
    for name, ModelClass in models:
        try:
            # Create model instance
            if name in ["LSTM", "GRU", "Transformer", "TCN", "WaveNet"]:
                model = ModelClass(config, input_size=50)
            else:
                model = ModelClass(config)
            
            # Test prediction with random data
            X = np.random.randn(50)
            direction, confidence = model.predict(X)
            
            # Check if model is real or fake
            # Real models should have varying predictions
            X2 = np.random.randn(50) * 2  # Different input
            dir2, conf2 = model.predict(X2)
            
            # Check if predictions are the same (fake) or different (real)
            is_same = abs(direction - dir2) < 0.01 and abs(confidence - conf2) < 0.01
            
            if is_same:
                status = "❌ FAKE (Same output for different inputs)"
                fake_models.append(name)
            else:
                status = "✅ REAL (Different outputs for different inputs)"
                working_models.append(name)
            
            print(f"\n{name}:")
            print(f"  Status: {status}")
            print(f"  Prediction 1: direction={direction:.4f}, confidence={confidence:.4f}")
            print(f"  Prediction 2: direction={dir2:.4f}, confidence={conf2:.4f}")
            
        except Exception as e:
            print(f"\n{name}: ❌ ERROR - {e}")
            fake_models.append(name)
    
    # Summary
    print("\n" + "="*80)
    print("  SUMMARY")
    print("="*80)
    print(f"\n✅ Working Models ({len(working_models)}):")
    for m in working_models:
        print(f"  - {m}")
    
    print(f"\n❌ Fake Models ({len(fake_models)}):")
    for m in fake_models:
        print(f"  - {m}")
    
    print(f"\nTotal: {len(models)} models")
    print(f"Working: {len(working_models)} ({len(working_models)/len(models)*100:.1f}%)")
    print(f"Fake: {len(fake_models)} ({len(fake_models)/len(models)*100:.1f}%)")
    
    return working_models, fake_models


if __name__ == "__main__":
    scan_models()
