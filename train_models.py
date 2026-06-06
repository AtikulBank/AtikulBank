import pandas as pd
import numpy as np
import os, joblib
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

XAUUSD_PATH = r"C:\Users\Its Rakib\Downloads\2026.6.6XAUUSD-M1-No Session.csv"
EURAUD_PATH = r"C:\Users\Its Rakib\Downloads\2026.6.6EURAUD-M1-No Session.csv"
SAVE_DIR = "trained_models"
os.makedirs(SAVE_DIR, exist_ok=True)

def load_data(path):
    print(f"Loading {path}...")
    df = pd.read_csv(path, low_memory=False)
    df.columns = df.columns.str.strip()
    print(f"Loaded {len(df)} rows")
    return df

def make_features(df):
    df = df.copy()
    df['mid'] = (df['Bid'] + df['Ask']) / 2
    df['spread'] = df['Ask'] - df['Bid']
    df['return1'] = df['mid'].pct_change()
    df['return5'] = df['mid'].pct_change(5)
    df['return10'] = df['mid'].pct_change(10)
    df['momentum'] = df['mid'] - df['mid'].shift(10)
    # RSI
    delta = df['mid'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    df['rsi'] = 100 - (100 / (1 + gain / (loss + 1e-9)))
    # MACD
    ema12 = df['mid'].ewm(span=12).mean()
    ema26 = df['mid'].ewm(span=26).mean()
    df['macd'] = ema12 - ema26
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    # Bollinger
    sma20 = df['mid'].rolling(20).mean()
    std20 = df['mid'].rolling(20).std()
    df['bb_upper'] = sma20 + 2*std20
    df['bb_lower'] = sma20 - 2*std20
    df['bb_width'] = df['bb_upper'] - df['bb_lower']
    # ATR
    df['atr'] = df['spread'].rolling(14).mean()
    # Label
    future = df['mid'].shift(-10)
    df['label'] = 0
    df.loc[(future - df['mid']) / df['mid'] > 0.0005, 'label'] = 1
    df.loc[(future - df['mid']) / df['mid'] < -0.0005, 'label'] = -1
    df = df.dropna()
    # Use last 500k rows for speed
    if len(df) > 500000:
        df = df.tail(500000)
    return df

def train(df, name):
    features = ['return1','return5','return10','momentum','rsi','macd','macd_signal','bb_width','atr','spread']
    X = df[features].values
    y = df['label'].values
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)
    models = {
        'RandomForest': RandomForestClassifier(n_estimators=100, n_jobs=-1, random_state=42),
        'GradientBoosting': GradientBoostingClassifier(n_estimators=100, random_state=42),
        'LogisticRegression': LogisticRegression(max_iter=1000, random_state=42),
    }
    for mname, model in models.items():
        print(f"  Training {mname}...")
        model.fit(X_train, y_train)
        acc = accuracy_score(y_test, model.predict(X_test))
        print(f"  {mname} Accuracy: {acc:.2%}")
        joblib.dump({'model': model, 'scaler': scaler}, f"{SAVE_DIR}/{name}_{mname}.joblib")
        print(f"  Saved: {SAVE_DIR}/{name}_{mname}.joblib")

print("="*50)
print("TRAINING XAUUSD MODELS")
print("="*50)
df_x = load_data(XAUUSD_PATH)
df_x = make_features(df_x)
train(df_x, "XAUUSD")

print("="*50)
print("TRAINING EURAUD MODELS")
print("="*50)
df_e = load_data(EURAUD_PATH)
df_e = make_features(df_e)
train(df_e, "EURAUD")

print("\nAll models saved to trained_models/")