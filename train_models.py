#!/usr/bin/env python3
"""
XAUUSD Trading Bot - Model Training Script
Train ML Models and RL Agents with your CSV data
"""

import numpy as np
import pandas as pd
import joblib
import json
import time
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# STEP 1: LOAD CSV DATA
# ============================================================================

def load_csv(file_path):
    """Load CSV file with DateTime, Bid, Ask, Volume"""
    print(f"Loading: {file_path}")
    
    df = pd.read_csv(file_path)
    df.columns = [col.strip().lower() for col in df.columns]
    
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.set_index('datetime')
    
    for col in ['bid', 'ask', 'volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    if 'bid' in df.columns and 'ask' in df.columns:
        df['mid_price'] = (df['bid'] + df['ask']) / 2
        df['spread'] = df['ask'] - df['bid']
    
    print(f"  Loaded {len(df)} rows")
    return df

# ============================================================================
# STEP 2: FEATURE ENGINEERING
# ============================================================================

def engineer_features(df):
    """Create technical indicators"""
    features = pd.DataFrame(index=df.index)
    price = df['mid_price'] if 'mid_price' in df.columns else df.iloc[:, 0]
    
    features['return_1'] = price.pct_change(1)
    features['return_5'] = price.pct_change(5)
    features['return_10'] = price.pct_change(10)
    
    delta = price.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    features['rsi'] = 100 - (100 / (1 + gain / loss))
    
    ema12 = price.ewm(span=12).mean()
    ema26 = price.ewm(span=26).mean()
    features['macd'] = ema12 - ema26
    features['macd_signal'] = features['macd'].ewm(span=9).mean()
    
    sma20 = price.rolling(20).mean()
    std20 = price.rolling(20).std()
    features['bb_upper'] = sma20 + 2 * std20
    features['bb_lower'] = sma20 - 2 * std20
    features['bb_position'] = (price - features['bb_lower']) / (features['bb_upper'] - features['bb_lower'])
    
    if 'spread' in df.columns:
        features['spread'] = df['spread']
        features['spread_ma'] = df['spread'].rolling(20).mean()
    
    features['volatility'] = price.pct_change().rolling(20).std()
    features['sma_10'] = price.rolling(10).mean()
    features['sma_20'] = price.rolling(20).mean()
    features['ema_10'] = price.ewm(span=10).mean()
    features['price_sma10'] = price / features['sma_10']
    features['price_sma20'] = price / features['sma_20']
    features['momentum_5'] = price - price.shift(5)
    features['momentum_10'] = price - price.shift(10)
    
    return features.dropna()

# ============================================================================
# STEP 3: CREATE LABELS
# ============================================================================

def create_labels(price, forward_period=10):
    """Create labels: 1=BUY, 0=HOLD, -1=SELL"""
    future_return = price.shift(-forward_period) / price - 1
    labels = pd.Series(0, index=price.index)
    labels[future_return > 0.0005] = 1
    labels[future_return < -0.0005] = -1
    return labels.iloc[:-forward_period]

# ============================================================================
# STEP 4: TRAIN MODELS
# ============================================================================

def train_models(X, y):
    """Train ML Models"""
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score
    
    print("\n" + "="*60)
    print("  TRAINING ML MODELS")
    print("="*60)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"  Training: {len(X_train)} samples")
    print(f"  Testing: {len(X_test)} samples")
    
    models = {
        'RandomForest': RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
        'GradientBoosting': GradientBoostingClassifier(n_estimators=100, random_state=42),
        'LogisticRegression': LogisticRegression(max_iter=1000, random_state=42),
    }
    
    results = {}
    save_dir = Path('trained_models')
    save_dir.mkdir(exist_ok=True)
    
    for name, model in models.items():
        print(f"\n  Training {name}...")
        start = time.time()
        
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        accuracy = accuracy_score(y_test, y_pred)
        elapsed = time.time() - start
        
        results[name] = {'accuracy': accuracy, 'time': elapsed}
        joblib.dump(model, save_dir / f'ml_{name}.joblib')
        
        print(f"  {name}: Accuracy={accuracy:.4f}, Time={elapsed:.2f}s")
    
    return results

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("="*60)
    print("  XAUUSD TRADING BOT - MODEL TRAINING")
    print("="*60)
    
    XAUUSD_PATH = r"C:\QuantDataManager125\export\XAUUSD-M1-No Session.csv"
    EURAUD_PATH = r"C:\QuantDataManager125\export\EURAUD-M1-No Session.csv"
    
    print("\n  STEP 1: Loading Data...")
    xauusd_df = load_csv(XAUUSD_PATH)
    euraud_df = load_csv(EURAUD_PATH)
    
    print("\n  STEP 2: Engineering Features...")
    xauusd_features = engineer_features(xauusd_df)
    euraud_features = engineer_features(euraud_df)
    print(f"  XAUUSD: {len(xauusd_features.columns)} features")
    print(f"  EURAUD: {len(euraud_features.columns)} features")
    
    print("\n  STEP 3: Creating Labels...")
    xauusd_labels = create_labels(xauusd_df['mid_price'])
    euraud_labels = create_labels(euraud_df['mid_price'])
    
    X = np.vstack([xauusd_features.values, euraud_features.values])
    y = np.concatenate([xauusd_labels.values, euraud_labels.values])
    
    print(f"  Total: {len(X)} samples, {X.shape[1]} features")
    print(f"  BUY: {np.sum(y==1)}, HOLD: {np.sum(y==0)}, SELL: {np.sum(y==-1)}")
    
    results = train_models(X, y)
    
    save_dir = Path('trained_models')
    with open(save_dir / 'training_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "="*60)
    print("  TRAINING COMPLETE!")
    print("="*60)
    print("\n  Models saved to: trained_models/")
    for name, metrics in results.items():
        print(f"  {name}: {metrics['accuracy']:.4f}")

if __name__ == "__main__":
    main()