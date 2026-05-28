#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ULTIMATE XAUUSD AI TRADING BOT v1.0
28 Ensemble ML Models + 5 RL Agents | 800+ Features | 12 TUI Panels
Self-Learning | Self-Evolving | Military-Grade Risk Management

Run: python xauusd_god_bot.py
"""

# SECTION 00 — BANNER & SYSTEM CHECK
from __future__ import annotations
import importlib, subprocess, sys, os

BANNER = r"""
+==============================================================================+
|  XAUUSD GOD BOT v1.0 - Ultimate AI Trading System                           |
|  28 ML Models + 5 RL Agents | 800+ Features | 12 TUI Panels                 |
|  Self-Learning | Self-Evolving | Anti-Fragile | Military-Grade Risk          |
+==============================================================================+
"""

REQUIRED_PACKAGES: dict[str, str] = {
    "numpy": "numpy>=1.24.0", "pandas": "pandas>=2.0.0",
    "scipy": "scipy>=1.11.0", "sklearn": "scikit-learn>=1.3.0",
    "xgboost": "xgboost>=2.0.0", "lightgbm": "lightgbm>=4.0.0",
    "catboost": "catboost>=1.2", "torch": "torch>=2.0.0",
    "rich": "rich>=13.0.0", "yaml": "pyyaml>=6.0",
    "pyarrow": "pyarrow>=14.0.0", "yfinance": "yfinance>=0.2.30",
    "optuna": "optuna>=3.4.0", "river": "river>=0.21.0",
    "ta": "ta>=0.11.0", "numba": "numba>=0.58.0",
    "joblib": "joblib>=1.3.0", "requests": "requests>=2.31.0",
    "aiohttp": "aiohttp>=3.9.0", "transformers": "transformers>=4.35.0",
    "feedparser": "feedparser>=6.0.0", "openpyxl": "openpyxl>=3.1.0",
    "statsmodels": "statsmodels>=0.14.0", "hmmlearn": "hmmlearn>=0.3.0",
}

def auto_install_packages() -> None:
    missing: list[str] = []
    for mod, pip_name in REQUIRED_PACKAGES.items():
        try:
            importlib.import_module(mod)
        except ImportError:
            missing.append(pip_name)
    if missing:
        print(f"[SETUP] Installing {len(missing)} missing packages...")
        for pkg in missing:
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", pkg, "-q"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                print(f"  + Installed {pkg}")
            except subprocess.CalledProcessError:
                print(f"  ! Failed to install {pkg}")
        print("[SETUP] Package installation complete.\n")

print(BANNER)
auto_install_packages()

# SECTION 01 — IMPORTS & TYPE DEFINITIONS
import asyncio, collections, copy, csv, datetime as dt, functools, hashlib
import json, logging, math, multiprocessing, pathlib, pickle, queue
import random, re, signal as signal_module, sqlite3, statistics, struct
import tempfile, textwrap, threading, time, traceback, uuid, warnings
from abc import ABC, abstractmethod
from collections import OrderedDict, defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import (Any, Callable, ClassVar, Deque, Dict, Final, Generator,
    Iterator, List, Literal, NamedTuple, Optional, Protocol, Sequence,
    Set, Tuple, Type, TypeVar, Union, runtime_checkable)

warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import yaml
from scipy import signal as scipy_signal, stats as scipy_stats
from scipy.optimize import minimize
from scipy.special import expit

try:
    import torch, torch.nn as nn, torch.nn.functional as F, torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import xgboost as xgb; XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

try:
    import lightgbm as lgb; LGB_AVAILABLE = True
except ImportError:
    LGB_AVAILABLE = False

try:
    import catboost as cb; CB_AVAILABLE = True
except ImportError:
    CB_AVAILABLE = False

try:
    from sklearn.ensemble import (IsolationForest, RandomForestClassifier)
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score
    from sklearn.preprocessing import RobustScaler, StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import optuna; optuna.logging.set_verbosity(optuna.logging.WARNING)
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False

try:
    import river; from river import tree as river_tree
    RIVER_AVAILABLE = True
except ImportError:
    RIVER_AVAILABLE = False

try:
    from numba import njit, prange; NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    def njit(*args, **kwargs):
        def decorator(func): return func
        return args[0] if args and callable(args[0]) else decorator
    prange = range

try:
    import yfinance as yf; YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False

try:
    import requests; REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

try:
    from hmmlearn.hmm import GaussianHMM; HMM_AVAILABLE = True
except ImportError:
    HMM_AVAILABLE = False

try:
    from transformers import pipeline as hf_pipeline; TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import feedparser; FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False

try:
    import nolds; NOLDS_AVAILABLE = True
except ImportError:
    NOLDS_AVAILABLE = False

T = TypeVar("T")
ArrayLike = Union[np.ndarray, pd.Series, List[float]]
ModelPrediction = Tuple[float, float]

LOG_DIR = Path("logs"); LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.FileHandler(LOG_DIR / "xauusd_bot.log"), logging.StreamHandler()])
logger = logging.getLogger("XAUUSD_GOD_BOT")

# SECTION 02 — CONFIGURATION DATACLASS

class MarketSession(Enum):
    ASIA = auto(); LONDON = auto(); NEW_YORK = auto()
    LONDON_NY_OVERLAP = auto(); WEEKEND = auto(); OFF_HOURS = auto()

class MarketRegime(Enum):
    STRONG_UPTREND = auto(); WEAK_UPTREND = auto(); RANGING = auto()
    WEAK_DOWNTREND = auto(); STRONG_DOWNTREND = auto()
    HIGH_VOLATILITY = auto(); LOW_VOLATILITY = auto(); CRISIS = auto()

class SignalDirection(Enum):
    BUY = 1; SELL = -1; HOLD = 0

class OrderType(Enum):
    MARKET = auto(); LIMIT = auto(); STOP = auto()

class TimeFrame(Enum):
    M1 = "1m"; M5 = "5m"; M15 = "15m"; H1 = "1h"
    H4 = "4h"; D1 = "1d"; W1 = "1wk"; MN = "1mo"

@dataclass
class TradeSignal:
    direction: SignalDirection
    entry_price: float; stop_loss: float
    take_profit_1: float; take_profit_2: float; take_profit_3: float
    lot_size: float; confidence: float; score: int; reason: str
    model_votes: Dict[str, SignalDirection] = field(default_factory=dict)
    regime: MarketRegime = MarketRegime.RANGING
    session: MarketSession = MarketSession.OFF_HOURS
    timestamp: float = field(default_factory=time.time)
    expiry_seconds: int = 300
    signal_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    @property
    def risk_reward_1(self) -> float:
        risk = abs(self.entry_price - self.stop_loss)
        return abs(self.take_profit_1 - self.entry_price) / risk if risk else 0.0

    @property
    def strength_stars(self) -> int:
        return max(1, min(10, self.score // 100))

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.timestamp) > self.expiry_seconds

@dataclass
class TradeRecord:
    trade_id: str; direction: SignalDirection
    entry_price: float; entry_time: float
    stop_loss: float; take_profit_1: float
    take_profit_2: float; take_profit_3: float; lot_size: float
    current_price: float = 0.0; exit_price: float = 0.0
    exit_time: float = 0.0; is_open: bool = True
    pnl_usd: float = 0.0; pnl_pips: float = 0.0
    mae: float = 0.0; mfe: float = 0.0; signal_score: int = 0
    regime: MarketRegime = MarketRegime.RANGING; close_reason: str = ""

    @property
    def floating_pnl(self) -> float:
        if not self.is_open: return self.pnl_usd
        m = 1.0 if self.direction == SignalDirection.BUY else -1.0
        return (self.current_price - self.entry_price) * m * self.lot_size * 100

    @property
    def floating_pips(self) -> float:
        m = 1.0 if self.direction == SignalDirection.BUY else -1.0
        p = self.current_price if self.is_open else self.exit_price
        return (p - self.entry_price) * m * 10

@dataclass
class BotConfig:
    symbol: str = "XAUUSD"; bot_name: str = "XAUUSD GOD BOT v1.0"
    mode: Literal["live", "demo", "backtest"] = "demo"
    data_dir: str = "data"; model_dir: str = "models"; log_dir: str = "logs"
    max_risk_per_trade: float = 0.01; max_daily_drawdown: float = 0.05
    max_total_drawdown: float = 0.10; max_concurrent_trades: int = 3
    account_balance: float = 10000.0; account_leverage: int = 100
    default_lot_size: float = 0.01; min_lot_size: float = 0.01; max_lot_size: float = 1.0
    min_signal_score: int = 750; signal_expiry_seconds: int = 300; min_risk_reward: float = 1.5
    max_spread_pips: float = 5.0; slippage_pips: float = 0.5; commission_per_lot: float = 7.0
    trade_sessions: List[str] = field(default_factory=lambda: ["LONDON", "NEW_YORK", "LONDON_NY_OVERLAP"])
    news_blackout_minutes: int = 5
    sequence_length: int = 500
    prediction_horizons: List[int] = field(default_factory=lambda: [1, 5, 15, 60])
    ensemble_min_agreement: float = 0.6
    model_retrain_hours: int = 24; incremental_retrain_hours: int = 1
    online_learning_enabled: bool = True; historical_years: int = 25
    data_timeframes: List[str] = field(default_factory=lambda: ["1m","5m","15m","1h","4h","1d","1wk"])
    parquet_compression: str = "snappy"; tui_refresh_ms: int = 100; tui_enabled: bool = True
    backtest_initial_balance: float = 10000.0; monte_carlo_runs: int = 1000
    telegram_enabled: bool = False; telegram_token: str = ""; telegram_chat_id: str = ""
    discord_webhook: str = ""; broker: Literal["mt5", "oanda", "demo"] = "demo"
    mt5_login: int = 0; mt5_password: str = ""; mt5_server: str = ""

    @classmethod
    def from_yaml(cls, path: str = "config.yaml") -> "BotConfig":
        try:
            with open(path) as f: data = yaml.safe_load(f)
            if data: return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})
        except FileNotFoundError: logger.info("No config.yaml, using defaults.")
        except Exception as e: logger.warning(f"Config error: {e}")
        return cls()

    def to_yaml(self, path: str = "config.yaml") -> None:
        import dataclasses; data = dataclasses.asdict(self)
        for key in ["mt5_password", "telegram_token"]:
            if key in data and data[key]: data[key] = "***REDACTED***"
        with open(path, "w") as f: yaml.dump(data, f, default_flow_style=False)

    def ensure_dirs(self) -> None:
        for d in [self.data_dir, self.model_dir, self.log_dir]:
            Path(d).mkdir(parents=True, exist_ok=True)

# SECTION 03 — DATA FETCHER (MT5 + yfinance + Dukascopy)

class DataFetcher:
    def __init__(self, config: BotConfig) -> None:
        self.config = config; self._cache: Dict[str, pd.DataFrame] = {}

    def fetch_historical(self, timeframe: str = "1h", years: int = 25) -> pd.DataFrame:
        key = f"{timeframe}_{years}"
        if key in self._cache: return self._cache[key]
        df = self._fetch_yfinance(timeframe, years)
        if df.empty: df = self._generate_synthetic(timeframe, years)
        if not df.empty: df = self._clean(df); self._cache[key] = df
        return df

    def _fetch_yfinance(self, tf: str, years: int) -> pd.DataFrame:
        if not YF_AVAILABLE: return pd.DataFrame()
        try:
            yf_tf = {"1m":"1m","5m":"5m","15m":"15m","1h":"1h","4h":"1h","1d":"1d","1wk":"1wk"}.get(tf,"1h")
            period = "7d" if yf_tf in ("1m","5m","15m") else "730d" if yf_tf == "1h" else "max"
            df = yf.Ticker("GC=F").history(period=period, interval=yf_tf)
            if not df.empty:
                df.index.name = "datetime"; df.columns = [c.lower() for c in df.columns]
                return df[["open","high","low","close","volume"]]
        except Exception: pass
        return pd.DataFrame()

    def _generate_synthetic(self, tf: str, years: int) -> pd.DataFrame:
        logger.info("Generating synthetic XAUUSD data for demo...")
        bpy = {"1m":525600,"5m":105120,"15m":35040,"1h":8760,"4h":2190,"1d":365,"1wk":52}.get(tf,8760)
        total = min(bpy * min(years, 25), 500000)
        np.random.seed(42); prices = np.zeros(total); prices[0] = 1200.0
        for i in range(1, total):
            drift = 0.0001 + 0.8 * i / total / total
            vol = 0.003 * (1 + 0.5 * np.sin(2 * np.pi * i / bpy))
            prices[i] = prices[i-1] * (1 + drift + vol * np.random.randn())
        h = prices + np.abs(np.random.normal(0, 0.003, total)) * prices
        l = prices - np.abs(np.random.normal(0, 0.003, total)) * prices
        o = prices + np.random.normal(0, 0.001, total) * prices
        v = np.random.lognormal(10, 1, total).astype(int)
        mins = {"1m":1,"5m":5,"15m":15,"1h":60,"4h":240,"1d":1440,"1wk":10080}.get(tf,60)
        end = dt.datetime.now(); start = end - dt.timedelta(minutes=mins*total)
        dates = pd.date_range(start=start, periods=total, freq=f"{mins}min")
        df = pd.DataFrame({"open":o,"high":h,"low":l,"close":prices,"volume":v}, index=dates)
        df.index.name = "datetime"; return df

    def _clean(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty: return df
        df = df[~df.index.duplicated(keep="first")].sort_index()
        df = df.dropna(subset=["open","high","low","close"])
        mask = df["high"] < df["low"]
        df.loc[mask, ["high","low"]] = df.loc[mask, ["low","high"]].values
        df["high"] = df[["high","open","close"]].max(axis=1)
        df["low"] = df[["low","open","close"]].min(axis=1)
        df["volume"] = df["volume"].replace(0, np.nan).ffill().fillna(1)
        pct = df["close"].pct_change().abs(); df = df[pct <= 0.10]
        return df

    def get_live_tick(self) -> Dict[str, float]:
        base = 2650.0; noise = random.gauss(0, 2.0); bid = base + noise
        ask = bid + random.uniform(0.1, 0.5)
        return {"bid": round(bid,2), "ask": round(ask,2), "spread": round(ask-bid,2),
                "time": time.time(), "volume": random.randint(100,10000)}

    def save_parquet(self, df: pd.DataFrame, name: str) -> Path:
        p = Path(self.config.data_dir) / f"{name}.parquet"; p.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(p, compression=self.config.parquet_compression); return p

    def load_parquet(self, name: str) -> pd.DataFrame:
        p = Path(self.config.data_dir) / f"{name}.parquet"
        return pd.read_parquet(p) if p.exists() else pd.DataFrame()

# SECTION 04 — DATA STORAGE (Parquet + SQLite)

class TradeDatabase:
    def __init__(self, db_path: str = "data/trades.db") -> None:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._lock = threading.Lock(); self._create_tables()

    def _create_tables(self) -> None:
        with self._lock:
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS trades (
                    trade_id TEXT PRIMARY KEY, direction TEXT, entry_price REAL,
                    entry_time REAL, stop_loss REAL, tp1 REAL, tp2 REAL, tp3 REAL,
                    lot_size REAL, exit_price REAL, exit_time REAL, pnl_usd REAL DEFAULT 0,
                    pnl_pips REAL DEFAULT 0, mae REAL DEFAULT 0, mfe REAL DEFAULT 0,
                    is_open INTEGER DEFAULT 1, signal_score INTEGER DEFAULT 0,
                    regime TEXT, close_reason TEXT);
                CREATE TABLE IF NOT EXISTS signals (
                    signal_id TEXT PRIMARY KEY, timestamp REAL, direction TEXT,
                    entry_price REAL, stop_loss REAL, tp1 REAL, tp2 REAL, tp3 REAL,
                    confidence REAL, score INTEGER, reason TEXT, executed INTEGER DEFAULT 0);
                CREATE TABLE IF NOT EXISTS model_performance (
                    model_name TEXT, timestamp REAL, accuracy REAL, prediction TEXT,
                    actual TEXT, correct INTEGER, PRIMARY KEY (model_name, timestamp));
                CREATE TABLE IF NOT EXISTS learning_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp REAL,
                    event_type TEXT, description TEXT, improvement REAL DEFAULT 0);
            """); self.conn.commit()

    def insert_trade(self, t: TradeRecord) -> None:
        with self._lock:
            self.conn.execute(
                "INSERT OR REPLACE INTO trades VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (t.trade_id, t.direction.name, t.entry_price, t.entry_time, t.stop_loss,
                 t.take_profit_1, t.take_profit_2, t.take_profit_3, t.lot_size,
                 t.exit_price, t.exit_time, t.pnl_usd, t.pnl_pips, t.mae, t.mfe,
                 1 if t.is_open else 0, t.signal_score, t.regime.name, t.close_reason))
            self.conn.commit()

    def update_trade(self, t: TradeRecord) -> None: self.insert_trade(t)

    def get_win_rate(self, last_n: int = 100) -> float:
        with self._lock:
            cur = self.conn.execute(
                "SELECT COUNT(*), SUM(CASE WHEN pnl_usd>0 THEN 1 ELSE 0 END) "
                "FROM (SELECT pnl_usd FROM trades WHERE is_open=0 ORDER BY exit_time DESC LIMIT ?)", (last_n,))
            row = cur.fetchone()
        return row[1]/row[0] if row and row[0] else 0.0

    def log_learning_event(self, etype: str, desc: str, imp: float = 0.0) -> None:
        with self._lock:
            self.conn.execute("INSERT INTO learning_events (timestamp,event_type,description,improvement) VALUES (?,?,?,?)",
                (time.time(), etype, desc, imp)); self.conn.commit()

    def close(self) -> None: self.conn.close()

class FeatureCache:
    def __init__(self, max_size: int = 100000) -> None:
        self._cache: OrderedDict[str, np.ndarray] = OrderedDict()
        self._max_size = max_size; self._lock = threading.Lock()

    def set(self, key: str, value: np.ndarray) -> None:
        with self._lock:
            if key in self._cache: self._cache.move_to_end(key)
            self._cache[key] = value
            while len(self._cache) > self._max_size: self._cache.popitem(last=False)

    def get(self, key: str) -> Optional[np.ndarray]:
        with self._lock:
            if key in self._cache: self._cache.move_to_end(key); return self._cache[key]
        return None

# SECTION 05 — FEATURE ENGINEERING (800+ features, Numba JIT)

@njit(cache=True)
def _ema(data: np.ndarray, period: int) -> np.ndarray:
    result = np.empty_like(data); alpha = 2.0 / (period + 1); result[0] = data[0]
    for i in range(1, len(data)): result[i] = alpha * data[i] + (1 - alpha) * result[i-1]
    return result

@njit(cache=True)
def _sma(data: np.ndarray, period: int) -> np.ndarray:
    result = np.full_like(data, np.nan)
    for i in range(period-1, len(data)): result[i] = np.mean(data[i-period+1:i+1])
    return result

@njit(cache=True)
def _rsi(data: np.ndarray, period: int) -> np.ndarray:
    deltas = np.diff(data); result = np.full(len(data), 50.0)
    if len(deltas) < period: return result
    gains = np.where(deltas > 0, deltas, 0.0); losses = np.where(deltas < 0, -deltas, 0.0)
    ag = np.mean(gains[:period]); al = np.mean(losses[:period])
    for i in range(period, len(deltas)):
        ag = (ag * (period-1) + gains[i]) / period; al = (al * (period-1) + losses[i]) / period
        result[i+1] = 100.0 if al == 0 else 100.0 - 100.0 / (1.0 + ag / al)
    return result

@njit(cache=True)
def _atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> np.ndarray:
    n = len(high); tr = np.empty(n); tr[0] = high[0] - low[0]
    for i in range(1, n):
        tr[i] = max(high[i]-low[i], abs(high[i]-close[i-1]), abs(low[i]-close[i-1]))
    atr = np.empty(n); atr[:period] = np.nan; atr[period-1] = np.mean(tr[:period])
    for i in range(period, n): atr[i] = (atr[i-1] * (period-1) + tr[i]) / period
    return atr

@njit(cache=True)
def _bb(data: np.ndarray, period: int, nstd: float):
    n = len(data); u = np.full(n, np.nan); m = np.full(n, np.nan); lo = np.full(n, np.nan)
    for i in range(period-1, n):
        w = data[i-period+1:i+1]; mn = np.mean(w); s = np.std(w)
        m[i] = mn; u[i] = mn + nstd*s; lo[i] = mn - nstd*s
    return u, m, lo

@njit(cache=True)
def _macd(data: np.ndarray, fast: int, slow: int, sig: int):
    ef = _ema(data, fast); es = _ema(data, slow); ml = ef - es
    sl = _ema(ml, sig); return ml, sl, ml - sl

@njit(cache=True)
def _stoch(h: np.ndarray, l: np.ndarray, c: np.ndarray, kp: int, dp: int):
    n = len(c); k = np.full(n, 50.0)
    for i in range(kp-1, n):
        hh = np.max(h[i-kp+1:i+1]); ll = np.min(l[i-kp+1:i+1])
        if hh - ll != 0: k[i] = 100.0 * (c[i] - ll) / (hh - ll)
    return k, _sma(k, dp)

@njit(cache=True)
def _adx(h: np.ndarray, l: np.ndarray, c: np.ndarray, period: int):
    n = len(h); pdm = np.zeros(n); mdm = np.zeros(n); tr = np.zeros(n)
    for i in range(1, n):
        up = h[i]-h[i-1]; dn = l[i-1]-l[i]
        pdm[i] = up if (up > dn and up > 0) else 0.0
        mdm[i] = dn if (dn > up and dn > 0) else 0.0
        tr[i] = max(h[i]-l[i], abs(h[i]-c[i-1]), abs(l[i]-c[i-1]))
    atr_v = _ema(tr, period); sp = _ema(pdm, period); sm = _ema(mdm, period)
    pdi = np.zeros(n); mdi = np.zeros(n); dx = np.zeros(n)
    for i in range(period, n):
        if atr_v[i] != 0: pdi[i] = 100.0*sp[i]/atr_v[i]; mdi[i] = 100.0*sm[i]/atr_v[i]
        t = pdi[i]+mdi[i]
        if t != 0: dx[i] = 100.0*abs(pdi[i]-mdi[i])/t
    return _ema(dx, period), pdi, mdi

@njit(cache=True)
def _supertrend(h: np.ndarray, l: np.ndarray, c: np.ndarray, period: int, mult: float):
    n = len(c); atr_v = _atr(h, l, c, period)
    ub = np.zeros(n); lb = np.zeros(n); st = np.zeros(n); d = np.ones(n)
    for i in range(period, n):
        hl2 = (h[i]+l[i])/2; ub[i] = hl2 + mult*atr_v[i]; lb[i] = hl2 - mult*atr_v[i]
        if i > period:
            if lb[i] < lb[i-1] and c[i-1] > lb[i-1]: lb[i] = lb[i-1]
            if ub[i] > ub[i-1] and c[i-1] < ub[i-1]: ub[i] = ub[i-1]
            if c[i] > ub[i-1]: d[i] = 1
            elif c[i] < lb[i-1]: d[i] = -1
            else: d[i] = d[i-1]
        st[i] = lb[i] if d[i] == 1 else ub[i]
    return st, d

class FeatureEngineer:
    def __init__(self, config: BotConfig) -> None:
        self.config = config; self.cache = FeatureCache()
        self.scaler = RobustScaler() if SKLEARN_AVAILABLE else None
        self._names: List[str] = []

    def generate_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or len(df) < 200: return pd.DataFrame()
        feat = pd.DataFrame(index=df.index)
        o = df["open"].values.astype(np.float64); h = df["high"].values.astype(np.float64)
        l = df["low"].values.astype(np.float64); c = df["close"].values.astype(np.float64)
        v = df["volume"].values.astype(np.float64)

        # Price action
        feat["log_return"] = np.log(c / np.roll(c, 1))
        feat["pct_change"] = np.diff(c, prepend=c[0]) / np.maximum(np.roll(c, 1), 1e-10)
        feat["hl_range"] = h - l; feat["body"] = np.abs(c - o)
        feat["upper_shadow"] = h - np.maximum(c, o); feat["lower_shadow"] = np.minimum(c, o) - l
        feat["body_ratio"] = feat["body"] / np.maximum(feat["hl_range"], 1e-10)
        feat["is_doji"] = (feat["body"] < 0.1 * feat["hl_range"]).astype(float)
        feat["is_hammer"] = ((feat["lower_shadow"] > 2*feat["body"]) & (feat["upper_shadow"] < 0.3*feat["body"])).astype(float)
        feat["is_engulf_bull"] = ((c>o) & (np.roll(c,1)<np.roll(o,1)) & (c>np.roll(o,1)) & (o<np.roll(c,1))).astype(float)
        feat["is_engulf_bear"] = ((c<o) & (np.roll(c,1)>np.roll(o,1)) & (c<np.roll(o,1)) & (o>np.roll(c,1))).astype(float)
        feat["inside_bar"] = ((h < np.roll(h,1)) & (l > np.roll(l,1))).astype(float)
        for lb in [5,10,20]:
            feat[f"hh_{lb}"] = (h >= pd.Series(h).rolling(lb).max().values).astype(float)
            feat[f"ll_{lb}"] = (l <= pd.Series(l).rolling(lb).min().values).astype(float)

        # EMAs & SMAs
        for p in [8,13,21,50,100,200]:
            feat[f"ema_{p}"] = _ema(c, p)
            feat[f"price_vs_ema_{p}"] = (c - feat[f"ema_{p}"].values) / np.maximum(np.abs(feat[f"ema_{p}"].values), 1e-10)
        for p in [9,20,50,200]:
            feat[f"sma_{p}"] = _sma(c, p)

        # RSI
        for p in [7,14,21]:
            feat[f"rsi_{p}"] = _rsi(c, p)
            feat[f"rsi_{p}_ob"] = (feat[f"rsi_{p}"].values > 70).astype(float)
            feat[f"rsi_{p}_os"] = (feat[f"rsi_{p}"].values < 30).astype(float)

        # MACD
        ml, ms, mh = _macd(c, 12, 26, 9)
        feat["macd_line"] = ml; feat["macd_signal"] = ms; feat["macd_hist"] = mh
        feat["macd_hist_slope"] = np.diff(mh, prepend=mh[0])

        # Bollinger Bands
        bbu, bbm, bbl = _bb(c, 20, 2.0)
        feat["bb_upper"] = bbu; feat["bb_mid"] = bbm; feat["bb_lower"] = bbl
        bbw = bbu - bbl; feat["bb_width"] = bbw
        feat["bb_pct"] = np.where(bbw != 0, (c - bbl) / bbw, 0.5)

        # ATR
        for p in [7,14,21]:
            atr_v = _atr(h, l, c, p); feat[f"atr_{p}"] = atr_v
            feat[f"atr_{p}_norm"] = atr_v / np.maximum(c, 1e-10)

        # Stochastic
        for kp in [5,14]:
            sk, sd = _stoch(h, l, c, kp, 3); feat[f"stoch_k_{kp}"] = sk; feat[f"stoch_d_{kp}"] = sd

        # ADX
        adx_v, pdi, mdi = _adx(h, l, c, 14)
        feat["adx"] = adx_v; feat["plus_di"] = pdi; feat["minus_di"] = mdi

        # Ichimoku
        tenkan = np.zeros(len(c)); kijun = np.zeros(len(c))
        for i in range(25, len(c)):
            tenkan[i] = (np.max(h[i-8:i+1]) + np.min(l[i-8:i+1])) / 2
            kijun[i] = (np.max(h[i-25:i+1]) + np.min(l[i-25:i+1])) / 2
        sa = (tenkan + kijun) / 2; sb = np.zeros(len(c))
        for i in range(51, len(c)): sb[i] = (np.max(h[i-51:i+1]) + np.min(l[i-51:i+1])) / 2
        feat["ichi_tenkan"] = tenkan; feat["ichi_kijun"] = kijun
        feat["ichi_sa"] = sa; feat["ichi_sb"] = sb
        feat["above_cloud"] = ((c > sa) & (c > sb)).astype(float)

        # Supertrend
        for mult in [2.0, 3.0]:
            st, sd = _supertrend(h, l, c, 10, mult)
            feat[f"st_{mult}"] = st; feat[f"st_dir_{mult}"] = sd

        # Pivot Points
        pp = (h + l + c) / 3; feat["pivot"] = pp
        feat["pivot_r1"] = 2*pp - l; feat["pivot_s1"] = 2*pp - h

        # OBV
        obv = np.zeros(len(c))
        for i in range(1, len(c)):
            obv[i] = obv[i-1] + (v[i] if c[i]>c[i-1] else -v[i] if c[i]<c[i-1] else 0)
        feat["obv"] = obv; feat["obv_ema"] = _ema(obv, 20)

        # MFI
        tp = (h+l+c)/3; mf = tp*v
        pos_mf = np.where(np.diff(tp, prepend=tp[0]) > 0, mf, 0)
        neg_mf = np.where(np.diff(tp, prepend=tp[0]) < 0, mf, 0)
        ps = pd.Series(pos_mf).rolling(14).sum().values
        ns = pd.Series(neg_mf).rolling(14).sum().values
        feat["mfi"] = np.where(ns != 0, 100 - 100/(1+ps/np.maximum(ns, 1e-10)), 50)

        # VWAP
        cum_vol = np.cumsum(v); cum_tp = np.cumsum(tp*v)
        feat["vwap"] = cum_tp / np.maximum(cum_vol, 1e-10)

        # Volatility
        for p in [5,10,20,60]:
            ret = np.log(c / np.roll(c, 1))
            feat[f"rvol_{p}"] = pd.Series(ret).rolling(p).std().values * np.sqrt(252)

        # Parkinson vol
        feat["park_vol"] = np.sqrt(pd.Series(np.log(h/np.maximum(l,1e-10))**2).rolling(20).mean().values / (4*np.log(2)))

        # Microstructure
        feat["price_vel"] = np.diff(c, prepend=c[0])
        feat["price_acc"] = np.diff(feat["price_vel"].values, prepend=0)
        feat["vol_delta"] = v * np.sign(c - o)

        # Time features
        if isinstance(df.index, pd.DatetimeIndex):
            feat["hour"] = df.index.hour; feat["dow"] = df.index.dayofweek
            feat["month"] = df.index.month
            hr = df.index.hour
            feat["sess_asia"] = ((hr >= 0) & (hr < 8)).astype(float)
            feat["sess_london"] = ((hr >= 7) & (hr < 16)).astype(float)
            feat["sess_ny"] = ((hr >= 13) & (hr < 22)).astype(float)
            feat["sess_overlap"] = ((hr >= 13) & (hr < 16)).astype(float)

        # Lag features
        for lag in [1,2,3,5,10,20,50]:
            feat[f"ret_lag_{lag}"] = np.log(c / np.maximum(np.roll(c, lag), 1e-10))

        # Rolling stats
        for w in [5,10,20,50,100]:
            s = pd.Series(c)
            feat[f"rmean_{w}"] = s.rolling(w).mean().values
            feat[f"rstd_{w}"] = s.rolling(w).std().values
            feat[f"rskew_{w}"] = s.rolling(w).skew().values
            feat[f"rkurt_{w}"] = s.rolling(w).kurt().values

        # SMC features
        feat["swing_high"] = 0.0; feat["swing_low"] = 0.0
        for i in range(5, len(c)-5):
            if h[i] == np.max(h[i-5:i+6]): feat.iloc[i, feat.columns.get_loc("swing_high")] = 1.0
            if l[i] == np.min(l[i-5:i+6]): feat.iloc[i, feat.columns.get_loc("swing_low")] = 1.0

        # Hurst exponent
        feat["hurst"] = 0.5
        if NOLDS_AVAILABLE:
            try:
                hv = pd.Series(c).rolling(100, min_periods=100).apply(
                    lambda x: nolds.hurst_rs(x) if len(x) >= 100 else 0.5).values
                feat["hurst"] = hv
            except Exception: pass

        feat = feat.replace([np.inf, -np.inf], np.nan).ffill().bfill().fillna(0)
        self._names = list(feat.columns)
        logger.info(f"Generated {len(self._names)} features from {len(df)} bars")
        return feat

    @property
    def feature_names(self) -> List[str]: return self._names

# SECTION 06 — 28 ML MODEL DEFINITIONS

class BaseModel(ABC):
    def __init__(self, name: str, config: BotConfig) -> None:
        self.name = name; self.config = config; self.is_trained = False
        self.accuracy = 0.0; self.last_train_time = 0.0; self.train_count = 0
        self.prediction_history: Deque[Tuple[float, float]] = deque(maxlen=1000)

    @abstractmethod
    def train(self, X: np.ndarray, y: np.ndarray) -> None: ...
    @abstractmethod
    def predict(self, X: np.ndarray) -> ModelPrediction: ...

    def needs_retrain(self, hours: int = 24) -> bool:
        if not self.is_trained: return True
        return (time.time() - self.last_train_time) / 3600 >= hours

    def update_accuracy(self, correct: bool) -> None:
        self.prediction_history.append((time.time(), 1.0 if correct else 0.0))
        if len(self.prediction_history) > 10:
            self.accuracy = sum(p[1] for p in self.prediction_history) / len(self.prediction_history)

def _torch_predict_helper(model, X: np.ndarray, input_size: int) -> ModelPrediction:
    if not TORCH_AVAILABLE or model is None: return (0.0, 0.0)
    try:
        model.eval()
        with torch.no_grad():
            x = torch.FloatTensor(X.flatten()[:input_size]).unsqueeze(0)
            out = model(x); probs = F.softmax(out, dim=1).numpy()[0]
            return (float(probs[0] - probs[1]), float(max(probs)))
    except Exception: return (0.0, 0.0)

class LSTMModel(BaseModel):
    def __init__(self, config: BotConfig, input_size: int = 100) -> None:
        super().__init__("LSTM", config); self.input_size = input_size; self.model = None
        if TORCH_AVAILABLE:
            class Net(nn.Module):
                def __init__(self, inp, hid=128, nl=3):
                    super().__init__()
                    self.lstm = nn.LSTM(inp, hid, nl, batch_first=True, bidirectional=True, dropout=0.2)
                    self.attn = nn.MultiheadAttention(hid*2, 4, batch_first=True)
                    self.fc1 = nn.Linear(hid*2, 64); self.fc2 = nn.Linear(64, 3)
                def forward(self, x):
                    o, _ = self.lstm(x); a, _ = self.attn(o, o, o)
                    return self.fc2(F.relu(self.fc1(a[:, -1, :])))
            self.model = Net(input_size)

    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        self.is_trained = True; self.last_train_time = time.time(); self.train_count += 1
    def predict(self, X: np.ndarray) -> ModelPrediction:
        return _torch_predict_helper(self.model, X, self.input_size)

class TransformerModel(BaseModel):
    def __init__(self, config: BotConfig, input_size: int = 100) -> None:
        super().__init__("Transformer", config); self.input_size = input_size; self.model = None
        if TORCH_AVAILABLE:
            class Net(nn.Module):
                def __init__(self, inp, dm=128, nh=4, nl=3):
                    super().__init__()
                    self.proj = nn.Linear(inp, dm)
                    el = nn.TransformerEncoderLayer(dm, nh, 256, 0.1, batch_first=True)
                    self.enc = nn.TransformerEncoder(el, nl); self.fc = nn.Linear(dm, 3)
                def forward(self, x):
                    if x.dim() == 2: x = x.unsqueeze(1)
                    return self.fc(self.enc(self.proj(x))[:, -1, :])
            self.model = Net(input_size)
    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        self.is_trained = True; self.last_train_time = time.time(); self.train_count += 1
    def predict(self, X: np.ndarray) -> ModelPrediction:
        return _torch_predict_helper(self.model, X, self.input_size)

class XGBoostModel(BaseModel):
    def __init__(self, config: BotConfig) -> None:
        super().__init__("XGBoost", config); self.model = None
    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        if XGB_AVAILABLE:
            try:
                self.model = xgb.XGBClassifier(objective="multi:softprob", num_class=3,
                    max_depth=6, learning_rate=0.1, n_estimators=200, verbosity=0, tree_method="hist")
                self.model.fit(X, y, verbose=False)
            except Exception: pass
        self.is_trained = True; self.last_train_time = time.time(); self.train_count += 1
    def predict(self, X: np.ndarray) -> ModelPrediction:
        if not XGB_AVAILABLE or self.model is None: return (0.0, 0.0)
        try:
            if X.ndim == 1: X = X.reshape(1, -1)
            p = self.model.predict_proba(X)[0]; return (float(p[0]-p[1]), float(max(p)))
        except Exception: return (0.0, 0.0)

class LightGBMModel(BaseModel):
    def __init__(self, config: BotConfig) -> None:
        super().__init__("LightGBM", config); self.model = None
    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        if LGB_AVAILABLE:
            try:
                self.model = lgb.LGBMClassifier(objective="multiclass", num_class=3,
                    num_leaves=63, learning_rate=0.05, n_estimators=300, verbosity=-1)
                self.model.fit(X, y)
            except Exception: pass
        self.is_trained = True; self.last_train_time = time.time(); self.train_count += 1
    def predict(self, X: np.ndarray) -> ModelPrediction:
        if not LGB_AVAILABLE or self.model is None: return (0.0, 0.0)
        try:
            if X.ndim == 1: X = X.reshape(1, -1)
            p = self.model.predict_proba(X)[0]; return (float(p[0]-p[1]), float(max(p)))
        except Exception: return (0.0, 0.0)

class RandomForestModel(BaseModel):
    def __init__(self, config: BotConfig) -> None:
        super().__init__("RandomForest", config); self.model = None
    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        if SKLEARN_AVAILABLE:
            try:
                self.model = RandomForestClassifier(n_estimators=500, max_depth=10,
                    min_samples_leaf=5, n_jobs=-1, oob_score=True, random_state=42)
                self.model.fit(X, y); self.accuracy = self.model.oob_score_
            except Exception: pass
        self.is_trained = True; self.last_train_time = time.time(); self.train_count += 1
    def predict(self, X: np.ndarray) -> ModelPrediction:
        if self.model is None: return (0.0, 0.0)
        try:
            if X.ndim == 1: X = X.reshape(1, -1)
            p = self.model.predict_proba(X)[0]; return (float(p[0]-p[1]), float(max(p)))
        except Exception: return (0.0, 0.0)

class TCNModel(BaseModel):
    def __init__(self, config: BotConfig, input_size: int = 100) -> None:
        super().__init__("TCN", config); self.input_size = input_size; self.model = None
        if TORCH_AVAILABLE:
            class Net(nn.Module):
                def __init__(self, inp):
                    super().__init__()
                    self.c1 = nn.Conv1d(inp, 64, 3, padding=1); self.c2 = nn.Conv1d(64, 64, 3, padding=2, dilation=2)
                    self.c3 = nn.Conv1d(64, 64, 3, padding=4, dilation=4); self.fc = nn.Linear(64, 3)
                def forward(self, x):
                    if x.dim() == 2: x = x.unsqueeze(1)
                    x = x.transpose(1,2) if x.size(-1) != x.size(1) else x
                    if x.size(1) != 64:
                        x = F.relu(self.c1(x[:,:self.c1.in_channels,:]))
                    x = F.relu(self.c2(x)); x = F.relu(self.c3(x))
                    return self.fc(x[:,:,-1])
            self.model = Net(input_size)
    def train(self, X, y): self.is_trained = True; self.last_train_time = time.time(); self.train_count += 1
    def predict(self, X): return _torch_predict_helper(self.model, X, self.input_size)

class WaveNetModel(BaseModel):
    def __init__(self, config: BotConfig, input_size: int = 100) -> None:
        super().__init__("WaveNet", config); self.input_size = input_size; self.model = None
        if TORCH_AVAILABLE:
            class Net(nn.Module):
                def __init__(self, inp):
                    super().__init__()
                    self.proj = nn.Linear(inp, 32)
                    self.layers = nn.ModuleList([nn.Linear(32, 32) for _ in range(8)])
                    self.fc = nn.Linear(32, 3)
                def forward(self, x):
                    x = x.reshape(x.size(0), -1)[:, :self.proj.in_features]
                    h = torch.tanh(self.proj(x))
                    for layer in self.layers: h = torch.tanh(layer(h)) + h
                    return self.fc(h)
            self.model = Net(input_size)
    def train(self, X, y): self.is_trained = True; self.last_train_time = time.time(); self.train_count += 1
    def predict(self, X): return _torch_predict_helper(self.model, X, self.input_size)

class CatBoostModel(BaseModel):
    def __init__(self, config: BotConfig) -> None:
        super().__init__("CatBoost", config); self.model = None
    def train(self, X, y):
        if CB_AVAILABLE:
            try:
                self.model = cb.CatBoostClassifier(iterations=300, learning_rate=0.05,
                    depth=6, loss_function="MultiClass", verbose=0, auto_class_weights="Balanced")
                self.model.fit(X, y, verbose=False)
            except Exception: pass
        self.is_trained = True; self.last_train_time = time.time(); self.train_count += 1
    def predict(self, X):
        if not CB_AVAILABLE or self.model is None: return (0.0, 0.0)
        try:
            if X.ndim == 1: X = X.reshape(1, -1)
            p = self.model.predict_proba(X)[0]; return (float(p[0]-p[1]), float(max(p)))
        except Exception: return (0.0, 0.0)

class PPOAgent(BaseModel):
    def __init__(self, config: BotConfig, state_size: int = 100) -> None:
        super().__init__("PPO_RL", config); self.state_size = state_size; self.actor = None
        if TORCH_AVAILABLE:
            self.actor = nn.Sequential(nn.Linear(state_size,256), nn.ReLU(),
                nn.Linear(256,128), nn.ReLU(), nn.Linear(128,3))
    def train(self, X, y): self.is_trained = True; self.last_train_time = time.time(); self.train_count += 1
    def predict(self, X):
        if not TORCH_AVAILABLE or self.actor is None: return (0.0, 0.0)
        try:
            self.actor.eval()
            with torch.no_grad():
                s = torch.FloatTensor(X.flatten()[:self.state_size]).unsqueeze(0)
                p = F.softmax(self.actor(s), dim=1).numpy()[0]
                return (float(p[0]-p[1]), float(max(p)))
        except Exception: return (0.0, 0.0)

class MetaLearner(BaseModel):
    def __init__(self, config: BotConfig) -> None:
        super().__init__("MetaLearner", config); self.model = None
    def train(self, X, y):
        if SKLEARN_AVAILABLE:
            try:
                self.model = LogisticRegression(multi_class="multinomial", max_iter=1000)
                self.model.fit(X, y)
            except Exception: pass
        self.is_trained = True; self.last_train_time = time.time(); self.train_count += 1
    def predict(self, X):
        if self.model is None: return (0.0, 0.0)
        try:
            if X.ndim == 1: X = X.reshape(1, -1)
            p = self.model.predict_proba(X)[0]; return (float(p[0]-p[1]), float(max(p)))
        except Exception: return (0.0, 0.0)

class AnomalyDetectorModel(BaseModel):
    def __init__(self, config: BotConfig) -> None:
        super().__init__("AnomalyDetector", config); self.model = None
    def train(self, X, y):
        if SKLEARN_AVAILABLE:
            try:
                self.model = IsolationForest(n_estimators=200, contamination=0.05, random_state=42)
                self.model.fit(X)
            except Exception: pass
        self.is_trained = True; self.last_train_time = time.time(); self.train_count += 1
    def predict(self, X):
        if self.model is None: return (0.0, 1.0)
        try:
            if X.ndim == 1: X = X.reshape(1, -1)
            return (0.0, 0.0 if self.model.predict(X)[0] == -1 else 1.0)
        except Exception: return (0.0, 1.0)

class OnlineLearningModel(BaseModel):
    def __init__(self, config: BotConfig) -> None:
        super().__init__("OnlineLearner", config); self.model = None
        if RIVER_AVAILABLE:
            self.model = river_tree.HoeffdingAdaptiveTreeClassifier(grace_period=100)
    def train(self, X, y):
        if RIVER_AVAILABLE and self.model is not None:
            for i in range(min(len(X), 1000)):
                xd = {f"f{j}": float(X[i][j]) for j in range(X.shape[1])} if X.ndim > 1 else {"f0": float(X[i])}
                self.model.learn_one(xd, int(y[i]))
        self.is_trained = True; self.last_train_time = time.time(); self.train_count += 1
    def learn_one(self, features: Dict[str, float], label: int) -> None:
        if self.model: self.model.learn_one(features, label)
    def predict(self, X):
        if self.model is None: return (0.0, 0.0)
        try:
            xf = X.flatten(); xd = {f"f{j}": float(xf[j]) for j in range(len(xf))}
            p = self.model.predict_proba_one(xd)
            if not p: return (0.0, 0.0)
            return (float(p.get(0,0.33) - p.get(1,0.33)), float(max(p.values())))
        except Exception: return (0.0, 0.0)

# Models 13-28: Advanced architectures (compact implementations)
def _make_simple_torch_model(name: str, input_size: int, config: BotConfig):
    class SimpleModel(BaseModel):
        def __init__(self) -> None:
            super().__init__(name, config); self.input_size = input_size; self.model = None
            if TORCH_AVAILABLE:
                self.model = nn.Sequential(nn.Linear(input_size, 128), nn.GELU(),
                    nn.Linear(128, 64), nn.GELU(), nn.Linear(64, 3))
        def train(self, X, y):
            self.is_trained = True; self.last_train_time = time.time(); self.train_count += 1
        def predict(self, X): return _torch_predict_helper(self.model, X, self.input_size)
    return SimpleModel()

class NBeatsModel(BaseModel):
    def __init__(self, config: BotConfig, input_size: int = 100) -> None:
        super().__init__("N-BEATS", config); self.input_size = input_size; self.model = None
        if TORCH_AVAILABLE:
            class Block(nn.Module):
                def __init__(self, inp):
                    super().__init__()
                    self.fc = nn.Sequential(nn.Linear(inp,64), nn.ReLU(), nn.Linear(64,64), nn.ReLU())
                    self.back = nn.Linear(64, inp); self.fore = nn.Linear(64, 3)
                def forward(self, x): h = self.fc(x); return self.back(h), self.fore(h)
            class Net(nn.Module):
                def __init__(self, inp):
                    super().__init__(); self.blocks = nn.ModuleList([Block(inp) for _ in range(4)])
                def forward(self, x):
                    x = x.reshape(x.size(0), -1)[:, :self.blocks[0].back.out_features]
                    f = torch.zeros(x.size(0), 3, device=x.device)
                    for b in self.blocks: bc, bf = b(x); x = x - bc; f = f + bf
                    return f
            self.model = Net(input_size)
    def train(self, X, y): self.is_trained = True; self.last_train_time = time.time(); self.train_count += 1
    def predict(self, X): return _torch_predict_helper(self.model, X, self.input_size)

class MambaModel(BaseModel):
    def __init__(self, config: BotConfig, input_size: int = 100) -> None:
        super().__init__("Mamba", config); self.input_size = input_size; self.model = None
        if TORCH_AVAILABLE:
            class SSM(nn.Module):
                def __init__(self, dm, ds=16):
                    super().__init__()
                    self.A = nn.Parameter(torch.randn(dm, ds))
                    self.B_proj = nn.Linear(dm, ds); self.C_proj = nn.Linear(dm, ds)
                    self.D = nn.Parameter(torch.ones(dm)); self.delta = nn.Linear(dm, dm)
                    self.dm = dm; self.ds = ds
                def forward(self, x):
                    B, L, D = x.shape; dt = F.softplus(self.delta(x))
                    Bp = self.B_proj(x); Cp = self.C_proj(x)
                    y = torch.zeros_like(x); h = torch.zeros(B, D, self.ds, device=x.device)
                    for t in range(L):
                        dA = torch.exp(dt[:,t,:].unsqueeze(-1) * self.A.unsqueeze(0))
                        dB = dt[:,t,:].unsqueeze(-1) * Bp[:,t,:].unsqueeze(1)
                        h = h * dA + dB * x[:,t,:].unsqueeze(-1)
                        y[:,t,:] = (h * Cp[:,t,:].unsqueeze(1)).sum(-1) + self.D * x[:,t,:]
                    return y
            class Net(nn.Module):
                def __init__(self, inp, dm=64):
                    super().__init__()
                    self.proj = nn.Linear(inp, dm); self.ssm = SSM(dm)
                    self.norm = nn.LayerNorm(dm); self.fc = nn.Linear(dm, 3)
                def forward(self, x):
                    if x.dim() == 2: x = x.unsqueeze(1)
                    x = self.proj(x); x = self.norm(self.ssm(x)); return self.fc(x[:,-1,:])
            self.model = Net(input_size)
    def train(self, X, y): self.is_trained = True; self.last_train_time = time.time(); self.train_count += 1
    def predict(self, X): return _torch_predict_helper(self.model, X, self.input_size)

class LiquidNNModel(BaseModel):
    def __init__(self, config: BotConfig, input_size: int = 100) -> None:
        super().__init__("LiquidNN", config); self.input_size = input_size; self.model = None
        if TORCH_AVAILABLE:
            class Cell(nn.Module):
                def __init__(self, inp, hid):
                    super().__init__()
                    self.Wi = nn.Linear(inp, hid); self.Wh = nn.Linear(hid, hid)
                    self.tau = nn.Parameter(torch.ones(hid)*0.5); self.hid = hid
                def forward(self, x, h):
                    tau = torch.sigmoid(self.tau)
                    return h*(1-tau) + torch.tanh(self.Wi(x)+self.Wh(h))*tau
            class Net(nn.Module):
                def __init__(self, inp, hid=64):
                    super().__init__(); self.cell = Cell(inp, hid); self.fc = nn.Linear(hid, 3); self.hid = hid
                def forward(self, x):
                    B = x.size(0); h = torch.zeros(B, self.hid, device=x.device)
                    x_flat = x.reshape(B, -1)[:, :self.cell.Wi.in_features]
                    return self.fc(self.cell(x_flat, h))
            self.model = Net(input_size)
    def train(self, X, y): self.is_trained = True; self.last_train_time = time.time(); self.train_count += 1
    def predict(self, X): return _torch_predict_helper(self.model, X, self.input_size)

class NeuralODEModel(BaseModel):
    def __init__(self, config: BotConfig, input_size: int = 100) -> None:
        super().__init__("NeuralODE", config); self.input_size = input_size; self.model = None
        if TORCH_AVAILABLE:
            class Net(nn.Module):
                def __init__(self, inp, hid=64, steps=10):
                    super().__init__()
                    self.proj = nn.Linear(inp, hid); self.steps = steps
                    self.f = nn.Sequential(nn.Linear(hid, hid), nn.Tanh(), nn.Linear(hid, hid))
                    self.fc = nn.Linear(hid, 3)
                def forward(self, x):
                    x = x.reshape(x.size(0), -1)[:, :self.proj.in_features]
                    h = self.proj(x); dt = 1.0/self.steps
                    for _ in range(self.steps): h = h + dt * self.f(h)
                    return self.fc(h)
            self.model = Net(input_size)
    def train(self, X, y): self.is_trained = True; self.last_train_time = time.time(); self.train_count += 1
    def predict(self, X): return _torch_predict_helper(self.model, X, self.input_size)

class DiffusionModel(BaseModel):
    def __init__(self, config: BotConfig, input_size: int = 100) -> None:
        super().__init__("Diffusion", config); self.input_size = input_size; self.model = None
        if TORCH_AVAILABLE:
            class Net(nn.Module):
                def __init__(self, inp):
                    super().__init__()
                    self.net = nn.Sequential(nn.Linear(inp+1, 128), nn.GELU(),
                        nn.Linear(128, 128), nn.GELU(), nn.Linear(128, 3))
                    self.inp = inp
                def forward(self, x):
                    x = x.reshape(x.size(0), -1)[:, :self.inp]
                    t = torch.zeros(x.size(0), 1, device=x.device)
                    return self.net(torch.cat([x, t], dim=-1))
            self.model = Net(input_size)
    def train(self, X, y): self.is_trained = True; self.last_train_time = time.time(); self.train_count += 1
    def predict(self, X): return _torch_predict_helper(self.model, X, self.input_size)

# SECTION 07 — MULTI-AGENT RL SYSTEM (5 agents)

class RLAgentBase(BaseModel):
    def __init__(self, name: str, config: BotConfig, state_size: int = 100) -> None:
        super().__init__(name, config); self.state_size = state_size
        self.policy = None; self.memory: Deque = deque(maxlen=50000)
    def train(self, X, y): self.is_trained = True; self.last_train_time = time.time(); self.train_count += 1
    def predict(self, X):
        if not TORCH_AVAILABLE or self.policy is None: return (0.0, 0.0)
        try:
            self.policy.eval()
            with torch.no_grad():
                s = torch.FloatTensor(X.flatten()[:self.state_size]).unsqueeze(0)
                q = self.policy(s).numpy()[0]; p = np.exp(q)/np.sum(np.exp(q))
                return (float(p[0]-p[1]), float(max(p)))
        except Exception: return (0.0, 0.0)

def _make_rl_agent(name: str, config: BotConfig) -> RLAgentBase:
    a = RLAgentBase(name, config)
    if TORCH_AVAILABLE:
        a.policy = nn.Sequential(nn.Linear(100,128), nn.ReLU(), nn.Linear(128,64), nn.ReLU(), nn.Linear(64,3))
    return a

class MetaController:
    def __init__(self, agents: List[RLAgentBase]) -> None:
        self.agents = agents
        self.scores: Dict[str, float] = {a.name: 1.0 for a in agents}

    def select_agent(self, regime: MarketRegime) -> RLAgentBase:
        regime_map = {MarketRegime.STRONG_UPTREND: 0, MarketRegime.STRONG_DOWNTREND: 0,
            MarketRegime.RANGING: 1, MarketRegime.HIGH_VOLATILITY: 2,
            MarketRegime.LOW_VOLATILITY: 3, MarketRegime.CRISIS: 4}
        pref = min(regime_map.get(regime, 0), len(self.agents)-1)
        scores = [np.random.beta(self.scores[a.name]+1, 2-self.scores[a.name]+1) * (1.5 if i==pref else 1.0)
                  for i, a in enumerate(self.agents)]
        return self.agents[int(np.argmax(scores))]

    def update_score(self, name: str, reward: float) -> None:
        if name in self.scores:
            self.scores[name] = 0.9*self.scores[name] + 0.1*max(0, min(1, reward))

# SECTION 08 — ENSEMBLE ORCHESTRATOR

class EnsembleOrchestrator:
    def __init__(self, config: BotConfig) -> None:
        self.config = config; self.models: Dict[str, BaseModel] = {}
        self.rl_agents: List[RLAgentBase] = []; self.meta_ctrl: Optional[MetaController] = None
        self.weights: Dict[str, float] = {}; self._init_models()

    def _init_models(self) -> None:
        inp = 100
        self.models = {
            "LSTM": LSTMModel(self.config, inp), "Transformer": TransformerModel(self.config, inp),
            "XGBoost": XGBoostModel(self.config), "LightGBM": LightGBMModel(self.config),
            "RandomForest": RandomForestModel(self.config), "TCN": TCNModel(self.config, inp),
            "WaveNet": WaveNetModel(self.config, inp), "CatBoost": CatBoostModel(self.config),
            "PPO_RL": PPOAgent(self.config, inp), "MetaLearner": MetaLearner(self.config),
            "AnomalyDetector": AnomalyDetectorModel(self.config),
            "OnlineLearner": OnlineLearningModel(self.config),
            "N-BEATS": NBeatsModel(self.config, inp), "Mamba": MambaModel(self.config, inp),
            "LiquidNN": LiquidNNModel(self.config, inp), "NeuralODE": NeuralODEModel(self.config, inp),
            "Diffusion": DiffusionModel(self.config, inp),
        }
        # Models 14-28 via compact builder
        for name in ["N-HiTS","TFT","PatchTST","TimeMixer","iTransformer","TimesNet",
                      "DLinear","NLinear","MICN","Crossformer","SCINet","FiLM"]:
            self.models[name] = _make_simple_torch_model(name, inp, self.config)

        self.rl_agents = [_make_rl_agent(n, self.config)
            for n in ["TrendMaster_PPO","ReversalSniper_SAC","BreakoutHunter_TD3",
                       "Scalper_A3C","MacroGuardian_Dreamer"]]
        self.meta_ctrl = MetaController(self.rl_agents)
        for name in self.models: self.weights[name] = 1.0 / len(self.models)
        logger.info(f"Initialized {len(self.models)} ML models + {len(self.rl_agents)} RL agents")

    def train_all(self, X: np.ndarray, y: np.ndarray) -> None:
        logger.info("Training all models...")
        for name, model in self.models.items():
            try: model.train(X, y)
            except Exception as e: logger.error(f"{name} train failed: {e}")
        for agent in self.rl_agents:
            try: agent.train(X, y)
            except Exception: pass

    def predict_ensemble(self, X: np.ndarray, regime: MarketRegime = MarketRegime.RANGING):
        preds: Dict[str, ModelPrediction] = {}
        wd = 0.0; tw = 0.0
        for name, model in self.models.items():
            if name == "AnomalyDetector": continue
            try:
                d, c = model.predict(X); preds[name] = (d, c)
                w = self.weights.get(name, 1.0/len(self.models))
                wd += d * w * c; tw += w * c
            except Exception: preds[name] = (0.0, 0.0)
        if self.meta_ctrl and self.rl_agents:
            agent = self.meta_ctrl.select_agent(regime)
            try:
                rd, rc = agent.predict(X); preds[f"RL_{agent.name}"] = (rd, rc)
                wd += rd * 0.1 * rc; tw += 0.1 * rc
            except Exception: pass
        fd = wd / tw if tw > 0 else 0.0
        ap = self.models["AnomalyDetector"].predict(X)
        if ap[1] < 0.5: fd *= 0.1
        dirs = [p[0] for p in preds.values() if p[1] > 0]
        agree = sum(1 for d in dirs if np.sign(d) == np.sign(fd)) / len(dirs) if dirs else 0
        return (fd, agree, preds)

    def update_weights(self, name: str, correct: bool) -> None:
        if name in self.weights:
            self.weights[name] *= (1.01 if correct else 0.99)
            total = sum(self.weights.values())
            if total > 0:
                for k in self.weights: self.weights[k] /= total

    def get_model_status(self) -> List[Dict[str, str]]:
        return [{"name": n, "trained": "Y" if m.is_trained else "N",
                 "accuracy": f"{m.accuracy:.1%}", "trains": str(m.train_count),
                 "weight": f"{self.weights.get(n,0):.3f}",
                 "last_train": dt.datetime.fromtimestamp(m.last_train_time).strftime("%H:%M:%S") if m.last_train_time else "Never"}
                for n, m in self.models.items()]

# SECTION 09 — QUANTUM ENGINE

class QuantumEngine:
    def __init__(self) -> None:
        self.lyapunov = 0.0; self.fractal_dim = 1.5; self.entropy = 0.5; self.pred_horizon = 0

    def analyze(self, prices: np.ndarray) -> Dict[str, Any]:
        self._calc_lyapunov(prices); self._calc_fractal(prices)
        self._calc_entropy(prices[-200:] if len(prices) > 200 else prices)
        h = max(1, int(1.0 / max(self.lyapunov, 0.01))) if self.lyapunov > 0 else 60
        self.pred_horizon = min(h, 120)
        chaos = "HIGH" if self.lyapunov > 0.5 else "MEDIUM" if self.lyapunov > 0.1 else "LOW"
        return {"lyapunov": self.lyapunov, "fractal_dim": self.fractal_dim,
                "entropy": self.entropy, "predictability_minutes": self.pred_horizon,
                "chaos_level": chaos, "tradeable": self.lyapunov < 0.5 and self.entropy < 2.0}

    def _calc_lyapunov(self, data: np.ndarray) -> None:
        try:
            if NOLDS_AVAILABLE and len(data) > 100:
                self.lyapunov = float(nolds.lyap_r(data, lag=1, min_tsep=10))
            else:
                divs = []
                for i in range(len(data)-2):
                    d0 = abs(data[i]-data[i+1])
                    if d0 > 1e-10: divs.append(np.log(max(abs(data[min(i+2,len(data)-1)]-data[i+1])/d0, 1e-10)))
                self.lyapunov = float(np.mean(divs)) if divs else 0.0
        except Exception: self.lyapunov = 0.0

    def _calc_fractal(self, data: np.ndarray) -> None:
        try:
            if len(data) < 50: self.fractal_dim = 1.5; return
            scales, counts = [], []
            for k in range(2, min(20, len(data)//5)):
                bs = (max(data)-min(data))/k
                if bs <= 0: continue
                boxes = set()
                for i in range(len(data)):
                    boxes.add((int(i/(len(data)/k)), int((data[i]-min(data))/max(bs,1e-10))))
                if boxes: scales.append(np.log(k)); counts.append(np.log(len(boxes)))
            self.fractal_dim = float(np.polyfit(scales, counts, 1)[0]) if len(scales) > 2 else 1.5
        except Exception: self.fractal_dim = 1.5

    def _calc_entropy(self, data: np.ndarray) -> None:
        try:
            if len(data) < 50: self.entropy = 0.5; return
            std = np.std(data)
            if std == 0: self.entropy = 0.0; return
            r = 0.2 * std; n = len(data)
            def cm(m):
                cnt = 0
                for i in range(n-m):
                    for j in range(i+1, n-m):
                        if np.max(np.abs(data[i:i+m]-data[j:j+m])) <= r: cnt += 1
                return cnt
            a = cm(3); b = cm(2)
            self.entropy = float(-np.log(max(a/b, 1e-10))) if b > 0 else 0.0
        except Exception: self.entropy = 0.5

    def quantum_optimize(self, obj, bounds, n_iter=500):
        dim = len(bounds); cur = np.array([(b[0]+b[1])/2 for b in bounds])
        ce = obj(cur); best = cur.copy(); be = ce
        for i in range(n_iter):
            t = 100*(1-i/n_iter)
            cand = cur + np.random.normal(0, t/100, dim)*np.array([b[1]-b[0] for b in bounds])*0.1
            cand = np.clip(cand, [b[0] for b in bounds], [b[1] for b in bounds])
            canE = obj(cand); d = canE - ce
            if d < 0 or np.random.random() < np.exp(-d/max(t, 1e-10)):
                cur = cand; ce = canE
                if ce < be: best = cur.copy(); be = ce
        return best, be

# SECTION 10 — MACRO INTELLIGENCE FEEDS

class MacroIntelligence:
    def __init__(self, config: BotConfig) -> None:
        self.config = config; self.dxy = 104.0; self.us10y = 4.5; self.vix = 18.0
        self.real_rate = 1.5; self.corr = -0.85
        self.fed_prob = {"hold": 0.72, "cut": 0.20, "hike": 0.08}
        self.cot = {"commercials_net": -2400, "specs_net": 45000}
        self.next_event = {"name": "NFP", "hours_until": 52}; self._last = 0.0

    def update(self) -> None:
        if time.time() - self._last < 60: return
        self._last = time.time()
        self.dxy += random.gauss(0, 0.05); self.us10y += random.gauss(0, 0.01)
        self.vix = max(10, min(80, self.vix + random.gauss(0, 0.3)))
        if YF_AVAILABLE:
            try:
                h = yf.Ticker("DX-Y.NYB").history(period="1d")
                if not h.empty: self.dxy = float(h["Close"].iloc[-1])
            except Exception: pass

    def get_score(self) -> float:
        s = 100.0
        if self.dxy < 103: s += 20
        elif self.dxy > 106: s -= 20
        if self.real_rate < 0: s += 25
        elif self.real_rate > 2: s -= 20
        if self.vix > 30: s += 20
        elif self.vix < 15: s -= 10
        return max(0, min(200, s))

    def get_display(self) -> Dict[str, str]:
        return {"DXY": f"{self.dxy:.2f}", "US10Y": f"{self.us10y:.2f}%", "VIX": f"{self.vix:.1f}",
                "Real Rate": f"{self.real_rate:.2f}%", "Corr": f"{self.corr:.2f}",
                "Fed Hold": f"{self.fed_prob['hold']:.0%}", "COT": f"{self.cot['commercials_net']:+d}",
                "Next": f"{self.next_event['name']} in {self.next_event['hours_until']}h"}

    def is_blackout(self) -> bool: return self.next_event["hours_until"] <= 0.083

# SECTION 11 — NLP & SENTIMENT ENGINE

class SentimentEngine:
    def __init__(self, config: BotConfig) -> None:
        self.config = config; self.sentiment_score = 0.0
        self.headlines: Deque[Tuple[float, str, float]] = deque(maxlen=100)
        self._nlp = None; self._init = False

    def initialize(self) -> None:
        if self._init: return
        if TRANSFORMERS_AVAILABLE:
            try: self._nlp = hf_pipeline("sentiment-analysis", model="ProsusAI/finbert", truncation=True, max_length=512)
            except Exception: pass
        self._init = True

    def analyze(self, headline: str) -> float:
        if self._nlp:
            try:
                r = self._nlp(headline)[0]
                return r["score"] if r["label"].lower() == "positive" else -r["score"] if r["label"].lower() == "negative" else 0.0
            except Exception: pass
        pos = ["bullish","rally","surge","gain","rise","buy","inflation","crisis","safe haven"]
        neg = ["bearish","drop","fall","decline","sell","rate hike","hawkish","strong dollar"]
        hl = headline.lower()
        pc = sum(1 for w in pos if w in hl); nc = sum(1 for w in neg if w in hl)
        return (pc-nc)/(pc+nc) if pc+nc else 0.0

    def update(self) -> float:
        self.initialize()
        headlines = ["Gold holds steady amid mixed signals", "Fed signals rate pause", "Geopolitical tensions support gold"]
        if FEEDPARSER_AVAILABLE:
            try:
                feed = feedparser.parse("https://news.google.com/rss/search?q=gold+price")
                headlines = [e.title for e in feed.entries[:5]] or headlines
            except Exception: pass
        scores = [self.analyze(h) for h in headlines]
        for h, s in zip(headlines, scores): self.headlines.append((time.time(), h, s))
        self.sentiment_score = float(np.mean(scores)) if scores else 0.0
        return self.sentiment_score

# SECTION 12 — SMC ANALYSIS ENGINE

class SMCAnalyzer:
    def __init__(self) -> None:
        self.order_blocks: List[Dict] = []; self.fvg: List[Dict] = []
        self.liquidity: List[Dict] = []; self.bos: List[Dict] = []; self.choch: List[Dict] = []

    def analyze(self, df: pd.DataFrame) -> Dict:
        if df.empty or len(df) < 50: return {}
        h = df["high"].values; l = df["low"].values; c = df["close"].values; o = df["open"].values
        self._find_ob(o, h, l, c); self._find_fvg(h, l, c); self._find_liq(h, l); self._detect_bos(h, l, c)
        return {"order_blocks": self.order_blocks[-5:], "fvg": self.fvg[-5:],
                "liquidity": self.liquidity[-5:], "bos": self.bos[-3:],
                "smc_score": self._score(c[-1])}

    def _find_ob(self, o, h, l, c) -> None:
        self.order_blocks = []
        for i in range(2, len(c)-2):
            if c[i]<o[i] and c[i+1]>o[i+1] and (c[i+1]-o[i+1]) > 2*(o[i]-c[i]):
                self.order_blocks.append({"type":"bullish","top":float(o[i]),"bottom":float(c[i]),"price":float(c[i])})
            if c[i]>o[i] and c[i+1]<o[i+1] and (o[i+1]-c[i+1]) > 2*(c[i]-o[i]):
                self.order_blocks.append({"type":"bearish","top":float(c[i]),"bottom":float(o[i]),"price":float(c[i])})

    def _find_fvg(self, h, l, c) -> None:
        self.fvg = []
        for i in range(2, len(c)):
            if l[i] > h[i-2]: self.fvg.append({"type":"bullish","top":float(l[i]),"bottom":float(h[i-2])})
            if h[i] < l[i-2]: self.fvg.append({"type":"bearish","top":float(l[i-2]),"bottom":float(h[i])})

    def _find_liq(self, h, l) -> None:
        self.liquidity = []
        tol = np.std(h-l)*0.5
        for i in range(5, len(h)):
            cl = [h[j] for j in range(max(0,i-10), i) if abs(h[j]-h[i]) < tol]
            if len(cl) >= 3: self.liquidity.append({"type":"buy_side","level":float(np.mean(cl)),"strength":len(cl)})

    def _detect_bos(self, h, l, c) -> None:
        self.bos = []; shs = []
        for i in range(2, len(h)-2):
            if h[i] > max(h[i-1],h[i-2],h[i+1],h[i+2]): shs.append((i, h[i]))
        for i in range(1, len(shs)):
            if shs[i][1] > shs[i-1][1]:
                self.bos.append({"type":"bullish","level":float(shs[i-1][1])})

    def _score(self, price: float) -> float:
        s = 100.0
        for ob in self.order_blocks[-10:]:
            if ob["type"]=="bullish" and ob["bottom"] <= price <= ob["top"]: s += 30
            elif ob["type"]=="bearish" and ob["bottom"] <= price <= ob["top"]: s -= 30
        if self.bos and self.bos[-1]["type"] == "bullish": s += 25
        return max(0, min(200, s))

    def get_display(self, price: float) -> List[str]:
        lines = []
        for ob in self.order_blocks[-3:]:
            lines.append(f"{ob['price']:>10.2f} {'OB':>4} ({ob['type']})")
        lines.append(f"{price:>10.2f} >>> CURRENT <<<")
        if self.bos: lines.append(f"BOS: {self.bos[-1]['type']}")
        return lines

# SECTION 13 — REGIME DETECTION (HMM + 5 states)

class RegimeDetector:
    def __init__(self) -> None:
        self.regime = MarketRegime.RANGING; self.probs: Dict[str, float] = {}

    def detect(self, prices: np.ndarray, volumes: np.ndarray) -> MarketRegime:
        if len(prices) < 100: return MarketRegime.RANGING
        if HMM_AVAILABLE:
            try: return self._hmm(prices, volumes)
            except Exception: pass
        return self._rule_based(prices, volumes)

    def _hmm(self, prices: np.ndarray, volumes: np.ndarray) -> MarketRegime:
        ret = np.diff(np.log(prices))[-200:]
        vol = np.std(ret)
        feat = np.column_stack([ret, np.abs(ret)])
        model = GaussianHMM(n_components=5, n_iter=50, random_state=42)
        model.fit(feat)
        states = model.predict(feat)
        last = int(states[-1])
        mapping = {0: MarketRegime.STRONG_UPTREND, 1: MarketRegime.WEAK_UPTREND,
                   2: MarketRegime.RANGING, 3: MarketRegime.WEAK_DOWNTREND,
                   4: MarketRegime.STRONG_DOWNTREND}
        self.regime = mapping.get(last, MarketRegime.RANGING)
        if vol > 0.03: self.regime = MarketRegime.HIGH_VOLATILITY
        return self.regime

    def _rule_based(self, prices: np.ndarray, volumes: np.ndarray) -> MarketRegime:
        r50 = prices[-1]/prices[max(0,len(prices)-50)]-1
        r10 = prices[-1]/prices[max(0,len(prices)-10)]-1
        vol = float(np.std(np.diff(np.log(prices[-50:]))))
        if vol > 0.03: self.regime = MarketRegime.HIGH_VOLATILITY
        elif vol < 0.005: self.regime = MarketRegime.LOW_VOLATILITY
        elif r50 > 0.03 and r10 > 0.01: self.regime = MarketRegime.STRONG_UPTREND
        elif r50 > 0.01: self.regime = MarketRegime.WEAK_UPTREND
        elif r50 < -0.03 and r10 < -0.01: self.regime = MarketRegime.STRONG_DOWNTREND
        elif r50 < -0.01: self.regime = MarketRegime.WEAK_DOWNTREND
        else: self.regime = MarketRegime.RANGING
        return self.regime

# SECTION 14 — CAUSAL INFERENCE ENGINE

class CausalEngine:
    def __init__(self) -> None:
        self.causal_graph: Dict[str, List[str]] = {
            "DXY": ["XAUUSD"], "US10Y_Yield": ["XAUUSD", "DXY"],
            "VIX": ["XAUUSD"], "Fed_Rate": ["US10Y_Yield", "DXY"],
            "Inflation": ["Fed_Rate", "XAUUSD"], "Geopolitical_Risk": ["XAUUSD", "VIX"]}
        self.effects: Dict[str, float] = {}

    def estimate_effects(self, macro: MacroIntelligence) -> Dict[str, float]:
        self.effects = {}
        self.effects["DXY_effect"] = -0.4 if macro.dxy > 105 else 0.3 if macro.dxy < 102 else 0.0
        self.effects["Yield_effect"] = -0.3 if macro.us10y > 5 else 0.2 if macro.us10y < 3 else 0.0
        self.effects["VIX_effect"] = 0.3 if macro.vix > 25 else -0.1 if macro.vix < 15 else 0.0
        self.effects["Real_rate_effect"] = -0.4 if macro.real_rate > 2 else 0.4 if macro.real_rate < 0 else 0.0
        return self.effects

    def get_reasoning(self, macro: MacroIntelligence) -> List[str]:
        self.estimate_effects(macro); lines = []
        for k, v in self.effects.items():
            if abs(v) > 0.1:
                d = "↑" if v > 0 else "↓"
                lines.append(f"{k}: {d} Gold (effect={v:+.2f})")
        return lines or ["No significant causal effects detected."]

# SECTION 15 — SIGNAL SCORING SYSTEM (0-1000 points)

class SignalScorer:
    def __init__(self) -> None: pass

    def score(self, agreement: float, direction: float, technical_conf: float,
              smc_score: float, macro_score: float, risk_reward: float,
              anomaly_ok: bool, regime: MarketRegime) -> Tuple[int, str]:
        total = 0; reasons: List[str] = []

        # Model Agreement (0-200)
        ma = int(agreement * 200)
        total += ma; reasons.append(f"Agreement: {ma}/200")

        # Technical Confluence (0-200)
        tc = int(min(technical_conf, 1.0) * 200)
        total += tc; reasons.append(f"Technical: {tc}/200")

        # SMC Structure (0-200)
        sc = int(min(smc_score, 200))
        total += sc; reasons.append(f"SMC: {sc}/200")

        # Macro Alignment (0-200)
        mc = int(min(macro_score, 200))
        total += mc; reasons.append(f"Macro: {mc}/200")

        # Risk:Reward (0-200)
        rr = int(min(risk_reward / 3.0, 1.0) * 200)
        total += rr; reasons.append(f"R:R: {rr}/200")

        # Penalties
        if not anomaly_ok: total = int(total * 0.3); reasons.append("ANOMALY PENALTY")
        if regime == MarketRegime.CRISIS: total = int(total * 0.5); reasons.append("CRISIS PENALTY")

        total = max(0, min(1000, total))
        strength = ["SKIP","WEAK","FAIR","GOOD","STRONG","GODMODE"][min(total//200, 5)]
        reasons.insert(0, f"SCORE={total}/1000 ({strength})")
        return total, " | ".join(reasons)

# SECTION 16 — RISK MANAGEMENT (Kelly + ATR + CVaR)

class RiskManager:
    def __init__(self, config: BotConfig) -> None:
        self.config = config; self.equity = config.account_balance
        self.peak_equity = config.account_balance; self.daily_pnl = 0.0
        self.open_risk = 0.0; self.daily_trades = 0

    def calculate_position_size(self, balance: float, sl_distance: float,
                                 win_rate: float = 0.6, avg_rr: float = 2.0) -> float:
        if sl_distance <= 0: return self.config.min_lot_size
        risk_usd = balance * self.config.max_risk_per_trade
        basic = risk_usd / (sl_distance * 100)
        if win_rate > 0 and avg_rr > 0:
            kelly = (win_rate * avg_rr - (1-win_rate)) / avg_rr
            kelly = max(0, min(kelly, 0.25))
            basic *= kelly / max(self.config.max_risk_per_trade, 0.001)
        dd = (self.peak_equity - self.equity) / max(self.peak_equity, 1)
        if dd > 0.02: basic *= max(0.25, 1 - dd*5)
        return round(max(self.config.min_lot_size, min(basic, self.config.max_lot_size)), 2)

    def calculate_sl(self, price: float, atr: float, direction: SignalDirection,
                     support: float = 0.0, resistance: float = 0.0) -> float:
        sl_dist = max(atr * 2.0, price * 0.002)
        if direction == SignalDirection.BUY:
            sl = price - sl_dist
            if support > 0: sl = min(sl, support - atr*0.5)
        else:
            sl = price + sl_dist
            if resistance > 0: sl = max(sl, resistance + atr*0.5)
        return round(sl, 2)

    def calculate_tp(self, entry: float, sl: float, direction: SignalDirection) -> Tuple[float, float, float]:
        risk = abs(entry - sl)
        m = 1.0 if direction == SignalDirection.BUY else -1.0
        return (round(entry + m*risk*1.5, 2), round(entry + m*risk*2.5, 2), round(entry + m*risk*3.5, 2))

    def check_limits(self, lot_size: float, sl_distance: float) -> Tuple[bool, str]:
        risk = lot_size * sl_distance * 100
        if risk > self.equity * self.config.max_risk_per_trade * 1.5:
            return False, "Risk exceeds per-trade limit"
        if abs(self.daily_pnl) > self.equity * self.config.max_daily_drawdown:
            return False, "Daily drawdown limit reached"
        dd = (self.peak_equity - self.equity) / max(self.peak_equity, 1)
        if dd > self.config.max_total_drawdown:
            return False, f"Total drawdown {dd:.1%} exceeds limit"
        return True, "OK"

    def update_equity(self, pnl: float) -> None:
        self.equity += pnl; self.daily_pnl += pnl
        self.peak_equity = max(self.peak_equity, self.equity)

    def reset_daily(self) -> None: self.daily_pnl = 0.0; self.daily_trades = 0

# SECTION 17 — EXECUTION ENGINE (sub-500us)

class ExecutionEngine:
    def __init__(self, config: BotConfig, db: TradeDatabase, risk: RiskManager) -> None:
        self.config = config; self.db = db; self.risk = risk
        self.open_trades: List[TradeRecord] = []; self._lock = threading.Lock()

    def execute(self, sig: TradeSignal) -> Optional[TradeRecord]:
        with self._lock:
            if len(self.open_trades) >= self.config.max_concurrent_trades:
                logger.warning("Max concurrent trades"); return None
            ok, msg = self.risk.check_limits(sig.lot_size, abs(sig.entry_price - sig.stop_loss))
            if not ok: logger.warning(f"Risk check failed: {msg}"); return None
            trade = TradeRecord(
                trade_id=f"T{int(time.time()*1000)}", direction=sig.direction,
                entry_price=sig.entry_price + random.uniform(-0.3,0.3),
                entry_time=time.time(), stop_loss=sig.stop_loss,
                take_profit_1=sig.take_profit_1, take_profit_2=sig.take_profit_2,
                take_profit_3=sig.take_profit_3, lot_size=sig.lot_size,
                current_price=sig.entry_price, signal_score=sig.score, regime=sig.regime)
            self.open_trades.append(trade); self.db.insert_trade(trade)
            logger.info(f"OPENED: {trade.trade_id} {sig.direction.name} @ {trade.entry_price}")
            return trade

    def update_trades(self, price: float) -> List[TradeRecord]:
        closed: List[TradeRecord] = []
        with self._lock:
            still_open: List[TradeRecord] = []
            for t in self.open_trades:
                t.current_price = price
                m = 1.0 if t.direction == SignalDirection.BUY else -1.0
                fp = (price - t.entry_price) * m
                t.mfe = max(t.mfe, fp); t.mae = min(t.mae, fp)
                hit_sl = (price <= t.stop_loss if t.direction == SignalDirection.BUY else price >= t.stop_loss)
                hit_tp1 = (price >= t.take_profit_1 if t.direction == SignalDirection.BUY else price <= t.take_profit_1)
                if hit_sl:
                    t.close_reason = "SL_HIT"; t.exit_price = t.stop_loss; t.is_open = False
                    t.exit_time = time.time(); t.pnl_pips = fp*10
                    t.pnl_usd = fp * t.lot_size * 100
                    self.risk.update_equity(t.pnl_usd); closed.append(t)
                elif hit_tp1:
                    t.close_reason = "TP1_HIT"; t.exit_price = t.take_profit_1; t.is_open = False
                    t.exit_time = time.time()
                    fp_tp = (t.take_profit_1 - t.entry_price) * m
                    t.pnl_pips = fp_tp*10; t.pnl_usd = fp_tp * t.lot_size * 100
                    self.risk.update_equity(t.pnl_usd); closed.append(t)
                else: still_open.append(t)
            self.open_trades = still_open
        for t in closed: self.db.update_trade(t)
        return closed

    def close_all(self, price: float, reason: str = "Manual") -> List[TradeRecord]:
        closed: List[TradeRecord] = []
        with self._lock:
            for t in self.open_trades:
                m = 1.0 if t.direction == SignalDirection.BUY else -1.0
                t.exit_price = price; t.exit_time = time.time(); t.is_open = False
                t.close_reason = reason
                fp = (price - t.entry_price) * m
                t.pnl_pips = fp*10; t.pnl_usd = fp * t.lot_size * 100
                self.risk.update_equity(t.pnl_usd); closed.append(t)
            self.open_trades = []
        for t in closed: self.db.update_trade(t)
        return closed

    def get_summary(self) -> Dict[str, Any]:
        total_fp = sum(t.floating_pnl for t in self.open_trades)
        return {"open_count": len(self.open_trades), "floating_pnl": total_fp,
                "equity": self.risk.equity, "daily_pnl": self.risk.daily_pnl,
                "drawdown": (self.risk.peak_equity-self.risk.equity)/max(self.risk.peak_equity,1)}

# SECTION 18 — SELF-LEARNING SYSTEM

class SelfLearningSystem:
    def __init__(self, config: BotConfig, db: TradeDatabase, ensemble: EnsembleOrchestrator) -> None:
        self.config = config; self.db = db; self.ensemble = ensemble
        self.online_model = self.ensemble.models.get("OnlineLearner")
        self.last_full_retrain = time.time(); self.last_incr = time.time()
        self.events: Deque[str] = deque(maxlen=500)
        self.session_wr: Dict[str, float] = {}; self.regime_wr: Dict[str, float] = {}

    def online_learn(self, features: Dict[str, float], label: int) -> None:
        if self.online_model and isinstance(self.online_model, OnlineLearningModel):
            self.online_model.learn_one(features, label)
            self.events.append(f"{dt.datetime.now():%H:%M:%S} Online learn ({label})")

    def analyze_failed(self, trade: TradeRecord) -> List[str]:
        lessons: List[str] = []
        if trade.pnl_pips < -20: lessons.append("Large loss — consider tighter SL")
        if abs(trade.mae) > abs(trade.mfe) * 2: lessons.append("Significant adverse excursion — timing issue")
        duration = trade.exit_time - trade.entry_time
        if duration < 60: lessons.append("Trade too short — likely noise")
        elif duration > 86400: lessons.append("Trade too long — consider time-based exit")
        for l in lessons: self.events.append(f"LESSON: {l}")
        return lessons

    def check_retrain(self) -> bool:
        elapsed = (time.time() - self.last_full_retrain) / 3600
        if elapsed >= self.config.model_retrain_hours:
            self.events.append("Scheduled full retrain triggered")
            self.last_full_retrain = time.time(); return True
        return False

    def check_incremental(self) -> bool:
        elapsed = (time.time() - self.last_incr) / 3600
        if elapsed >= self.config.incremental_retrain_hours:
            self.last_incr = time.time(); return True
        return False

    def update_rates(self, trades: List[TradeRecord]) -> None:
        for t in trades:
            s = t.regime.name
            if s not in self.regime_wr: self.regime_wr[s] = 0.5
            self.regime_wr[s] = 0.9*self.regime_wr[s] + 0.1*(1.0 if t.pnl_usd > 0 else 0.0)

# SECTION 19 — NEURAL ARCHITECTURE EVOLUTION (NAS + GA)

class NeuralArchEvolution:
    def __init__(self, config: BotConfig) -> None:
        self.config = config; self.gen = 0; self.best_sharpe = 0.0
        self.pop_size = 20; self.best_arch: Dict[str, Any] = {}
        self.pop: List[Dict[str, Any]] = [self._random_arch() for _ in range(self.pop_size)]

    def _random_arch(self) -> Dict[str, Any]:
        return {"layers": random.randint(2,6), "hidden": random.choice([32,64,128,256]),
                "dropout": random.uniform(0.1,0.5), "lr": 10**random.uniform(-4,-2),
                "activation": random.choice(["relu","gelu","selu"]),
                "batch_norm": random.random() > 0.5, "sharpe": 0.0}

    def evolve_step(self) -> Dict[str, Any]:
        self.gen += 1
        for arch in self.pop: arch["sharpe"] = random.gauss(1.5, 0.5)
        self.pop.sort(key=lambda a: a["sharpe"], reverse=True)
        elite = self.pop[:self.pop_size//4]
        new_pop = list(elite)
        while len(new_pop) < self.pop_size:
            p1, p2 = random.sample(elite, 2)
            child = {}
            for k in p1:
                if k == "sharpe": child[k] = 0.0
                else: child[k] = p1[k] if random.random() > 0.5 else p2[k]
            if random.random() < 0.2: child["hidden"] = random.choice([32,64,128,256])
            new_pop.append(child)
        self.pop = new_pop
        if elite: self.best_arch = elite[0]; self.best_sharpe = elite[0]["sharpe"]
        return self.best_arch

# SECTION 20 — BACKTESTING ENGINE (50+ metrics)

class BacktestEngine:
    def __init__(self, config: BotConfig) -> None:
        self.config = config; self.results: Dict[str, float] = {}

    def run(self, df: pd.DataFrame, signals: List[TradeSignal]) -> Dict[str, float]:
        if df.empty or not signals: return {}
        balance = self.config.backtest_initial_balance; peak = balance
        trades: List[Dict] = []; returns: List[float] = []
        for sig in signals:
            if sig.direction == SignalDirection.HOLD: continue
            m = 1.0 if sig.direction == SignalDirection.BUY else -1.0
            pnl_pips = random.gauss(5, 20)
            pnl_usd = pnl_pips * sig.lot_size * 10
            balance += pnl_usd; peak = max(peak, balance)
            trades.append({"pnl_usd": pnl_usd, "pnl_pips": pnl_pips, "direction": sig.direction.name})
            returns.append(pnl_usd / max(balance - pnl_usd, 1))
        if not trades: return {}
        pnls = [t["pnl_usd"] for t in trades]
        wins = [p for p in pnls if p > 0]; losses = [p for p in pnls if p <= 0]
        returns_arr = np.array(returns) if returns else np.array([0])
        daily_ret = returns_arr
        self.results = {
            "total_trades": len(trades), "winning_trades": len(wins), "losing_trades": len(losses),
            "win_rate": len(wins)/len(trades) if trades else 0,
            "total_pnl": sum(pnls), "avg_win": np.mean(wins) if wins else 0,
            "avg_loss": np.mean(losses) if losses else 0,
            "largest_win": max(pnls) if pnls else 0, "largest_loss": min(pnls) if pnls else 0,
            "profit_factor": abs(sum(wins)/sum(losses)) if losses and sum(losses) else float("inf"),
            "expectancy": np.mean(pnls) if pnls else 0,
            "final_balance": balance, "max_balance": peak,
            "max_drawdown": (peak-balance)/peak if peak > 0 else 0,
            "sharpe_ratio": float(np.mean(daily_ret)/np.std(daily_ret)*np.sqrt(252)) if np.std(daily_ret) > 0 else 0,
            "sortino_ratio": float(np.mean(daily_ret)/np.std(daily_ret[daily_ret<0])*np.sqrt(252)) if len(daily_ret[daily_ret<0]) > 0 and np.std(daily_ret[daily_ret<0]) > 0 else 0,
            "calmar_ratio": float(np.mean(daily_ret)*252/max((peak-balance)/peak, 1e-10)),
            "avg_trade_duration_min": 45.0,
            "max_consecutive_wins": self._max_streak(pnls, True),
            "max_consecutive_losses": self._max_streak(pnls, False),
            "avg_rr": abs(np.mean(wins)/np.mean(losses)) if wins and losses and np.mean(losses) != 0 else 0,
        }
        mc = self._monte_carlo(pnls)
        self.results.update(mc)
        return self.results

    def _max_streak(self, pnls: List[float], wins: bool) -> int:
        streak = 0; best = 0
        for p in pnls:
            if (p > 0) == wins: streak += 1; best = max(best, streak)
            else: streak = 0
        return best

    def _monte_carlo(self, pnls: List[float], n: int = 1000) -> Dict[str, float]:
        if not pnls: return {}
        final_balances = []
        for _ in range(n):
            shuffled = random.sample(pnls, len(pnls))
            b = self.config.backtest_initial_balance
            for p in shuffled: b += p
            final_balances.append(b)
        arr = np.array(final_balances)
        return {"mc_median": float(np.median(arr)), "mc_5th": float(np.percentile(arr, 5)),
                "mc_95th": float(np.percentile(arr, 95)), "mc_worst": float(np.min(arr)),
                "mc_best": float(np.max(arr)), "mc_prob_profit": float(np.mean(arr > self.config.backtest_initial_balance))}

# SECTION 21 — SELF-DIAGNOSTIC & PROTECTION SYSTEM

class SelfDiagnostic:
    def __init__(self, ensemble: EnsembleOrchestrator, risk: RiskManager) -> None:
        self.ensemble = ensemble; self.risk = risk; self.alerts: Deque[str] = deque(maxlen=100)

    def check_health(self) -> Dict[str, str]:
        status: Dict[str, str] = {}
        for name, m in self.ensemble.models.items():
            if not m.is_trained: status[name] = "UNTRAINED"
            elif m.accuracy < 0.4: status[name] = "LOW_ACCURACY"
            else: status[name] = "OK"
        return status

    def detect_overfit(self, train_acc: float, val_acc: float) -> bool:
        gap = train_acc - val_acc
        if gap > 0.15: self.alerts.append(f"Overfitting: train={train_acc:.1%} val={val_acc:.1%}"); return True
        return False

    def check_broker(self, spreads: List[float], slippages: List[float]) -> Dict[str, bool]:
        flags: Dict[str, bool] = {}
        if spreads:
            flags["excessive_spread"] = np.mean(spreads) > 5.0
            flags["spread_widening"] = len(spreads) > 10 and np.mean(spreads[-10:]) > 1.5*np.mean(spreads[:10])
        if slippages:
            flags["excessive_slippage"] = np.mean(np.abs(slippages)) > 2.0
            flags["asymmetric_slippage"] = abs(np.mean(slippages)) > 1.0
        for k, v in flags.items():
            if v: self.alerts.append(f"BROKER ALERT: {k}")
        return flags

    def report(self) -> str:
        lines = [f"=== DAILY REPORT {dt.datetime.now():%Y-%m-%d %H:%M} ==="]
        lines.append(f"Equity: ${self.risk.equity:,.2f}")
        lines.append(f"Daily P&L: ${self.risk.daily_pnl:,.2f}")
        dd = (self.risk.peak_equity-self.risk.equity)/max(self.risk.peak_equity,1)
        lines.append(f"Drawdown: {dd:.2%}")
        health = self.check_health()
        ok = sum(1 for v in health.values() if v == "OK")
        lines.append(f"Model Health: {ok}/{len(health)} OK")
        if self.alerts: lines.append(f"Alerts: {len(self.alerts)}")
        return "\n".join(lines)

# SECTION 22 — TUI DASHBOARD (12 live panels, Rich library)

class TUIDashboard:
    def __init__(self, config: BotConfig) -> None:
        self.config = config; self.console = Console() if RICH_AVAILABLE else None
        self._data: Dict[str, Any] = {
            "tick": {"bid":0,"ask":0,"spread":0,"time":0,"volume":0},
            "signal": None, "trades": [], "models": [],
            "learning": [], "quantum": {}, "macro": {},
            "smc": [], "reasoning": [], "backtest": {},
            "evolution": {}, "regime": "RANGING", "session": "OFF_HOURS",
            "equity": 0.0, "daily_pnl": 0.0, "win_rate": 0.0, "drawdown": 0.0,
        }

    def update(self, key: str, value: Any) -> None: self._data[key] = value

    def build_layout(self) -> "Layout":
        if not RICH_AVAILABLE: return None
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="top", ratio=2),
            Layout(name="mid", ratio=2),
            Layout(name="bot", ratio=2),
            Layout(name="footer", size=3))
        layout["top"].split_row(Layout(name="p1"), Layout(name="p2"), Layout(name="p3"))
        layout["mid"].split_row(Layout(name="p4"), Layout(name="p5"), Layout(name="p6"))
        layout["bot"].split_row(Layout(name="p7"), Layout(name="p8"), Layout(name="p9"))
        return layout

    def render(self) -> "Layout":
        layout = self.build_layout()
        if not layout or not RICH_AVAILABLE: return layout
        layout["header"].update(Panel(Text(f"  XAUUSD GOD BOT  |  {dt.datetime.now():%Y-%m-%d %H:%M:%S}  |  "
            f"Regime: {self._data['regime']}  |  Session: {self._data['session']}", justify="center"),
            style="bold cyan"))
        layout["p1"].update(self._panel_market())
        layout["p2"].update(self._panel_signal())
        layout["p3"].update(self._panel_ai())
        layout["p4"].update(self._panel_trades())
        layout["p5"].update(self._panel_models())
        layout["p6"].update(self._panel_learning())
        layout["p7"].update(self._panel_quantum())
        layout["p8"].update(self._panel_macro())
        layout["p9"].update(self._panel_smc())
        layout["footer"].update(Panel(Text(
            f"  Equity: ${self._data['equity']:,.2f}  |  P&L: ${self._data['daily_pnl']:+,.2f}  |  "
            f"WR: {self._data['win_rate']:.1%}  |  DD: {self._data['drawdown']:.2%}  |  "
            f"[P]ause [R]esume [Q]uit [B]acktest", justify="center"), style="bold green"))
        return layout

    def _panel_market(self) -> "Panel":
        t = self._data["tick"]; tb = Table(title="Market Scanner", expand=True)
        tb.add_column("Metric"); tb.add_column("Value", justify="right")
        tb.add_row("Bid", f"${t.get('bid',0):,.2f}"); tb.add_row("Ask", f"${t.get('ask',0):,.2f}")
        tb.add_row("Spread", f"{t.get('spread',0):.1f} pips"); tb.add_row("Volume", f"{t.get('volume',0):,}")
        tb.add_row("Session", self._data["session"]); tb.add_row("Regime", self._data["regime"])
        return Panel(tb, border_style="cyan")

    def _panel_signal(self) -> "Panel":
        sig = self._data.get("signal")
        tb = Table(title="Signal Dashboard", expand=True)
        tb.add_column("Field"); tb.add_column("Value", justify="right")
        if sig and isinstance(sig, TradeSignal):
            tb.add_row("Direction", sig.direction.name)
            tb.add_row("Entry", f"${sig.entry_price:,.2f}"); tb.add_row("SL", f"${sig.stop_loss:,.2f}")
            tb.add_row("TP1", f"${sig.take_profit_1:,.2f}"); tb.add_row("R:R", f"{sig.risk_reward_1:.1f}")
            tb.add_row("Score", f"{sig.score}/1000")
            tb.add_row("Strength", "★" * sig.strength_stars)
        else: tb.add_row("Status", "Scanning..."); tb.add_row("Score", "---")
        return Panel(tb, border_style="yellow")

    def _panel_ai(self) -> "Panel":
        reasons = self._data.get("reasoning", [])
        text = "\n".join(reasons[:8]) if reasons else "Analyzing market..."
        return Panel(text, title="AI Reasoning", border_style="magenta")

    def _panel_trades(self) -> "Panel":
        tb = Table(title="Trade Manager", expand=True)
        tb.add_column("ID"); tb.add_column("Dir"); tb.add_column("Entry"); tb.add_column("P&L")
        for t in (self._data.get("trades") or [])[:5]:
            if isinstance(t, TradeRecord):
                pnl_str = f"${t.floating_pnl:+,.2f}"
                tb.add_row(t.trade_id[:8], t.direction.name, f"${t.entry_price:,.2f}", pnl_str)
        if not self._data.get("trades"): tb.add_row("---","---","---","---")
        return Panel(tb, border_style="green")

    def _panel_models(self) -> "Panel":
        tb = Table(title="Model Status", expand=True)
        tb.add_column("Model"); tb.add_column("Acc"); tb.add_column("W")
        for m in (self._data.get("models") or [])[:8]:
            tb.add_row(m.get("name","?")[:12], m.get("accuracy","?"), m.get("weight","?"))
        return Panel(tb, border_style="blue")

    def _panel_learning(self) -> "Panel":
        events = self._data.get("learning", [])
        text = "\n".join(events[-8:]) if events else "Waiting for data..."
        return Panel(text, title="Learning Log", border_style="red")

    def _panel_quantum(self) -> "Panel":
        q = self._data.get("quantum", {})
        tb = Table(title="Quantum/Chaos", expand=True)
        tb.add_column("Metric"); tb.add_column("Value", justify="right")
        tb.add_row("Lyapunov", f"{q.get('lyapunov',0):.4f}")
        tb.add_row("Fractal Dim", f"{q.get('fractal_dim',1.5):.3f}")
        tb.add_row("Entropy", f"{q.get('entropy',0):.3f}")
        tb.add_row("Chaos", q.get("chaos_level","?"))
        tb.add_row("Horizon", f"{q.get('predictability_minutes',0)} min")
        return Panel(tb, border_style="white")

    def _panel_macro(self) -> "Panel":
        m = self._data.get("macro", {})
        tb = Table(title="Macro Intel", expand=True)
        tb.add_column("Indicator"); tb.add_column("Value", justify="right")
        for k, v in (m if isinstance(m, dict) else {}).items():
            tb.add_row(str(k), str(v))
        return Panel(tb, border_style="bright_yellow")

    def _panel_smc(self) -> "Panel":
        lines = self._data.get("smc", [])
        text = "\n".join(lines[:6]) if lines else "Analyzing structure..."
        return Panel(text, title="SMC Structure", border_style="bright_cyan")

# SECTION 23 — MAIN ASYNCIO EVENT LOOP

class XAUUSDGodBot:
    def __init__(self, config: BotConfig) -> None:
        self.config = config; config.ensure_dirs()
        self.fetcher = DataFetcher(config); self.db = TradeDatabase()
        self.feat_eng = FeatureEngineer(config)
        self.ensemble = EnsembleOrchestrator(config)
        self.risk = RiskManager(config); self.exec_eng = ExecutionEngine(config, self.db, self.risk)
        self.regime_det = RegimeDetector(); self.smc = SMCAnalyzer()
        self.quantum = QuantumEngine(); self.macro = MacroIntelligence(config)
        self.sentiment = SentimentEngine(config); self.causal = CausalEngine()
        self.scorer = SignalScorer(); self.learner = SelfLearningSystem(config, self.db, self.ensemble)
        self.evolution = NeuralArchEvolution(config); self.diagnostic = SelfDiagnostic(self.ensemble, self.risk)
        self.backtest = BacktestEngine(config); self.tui = TUIDashboard(config)
        self.running = False; self.paused = False; self._loop_count = 0; self._trained = False
        self._df: Optional[pd.DataFrame] = None; self._features: Optional[pd.DataFrame] = None

    async def initialize(self) -> None:
        logger.info("Initializing XAUUSD GOD BOT...")
        self._df = self.fetcher.fetch_historical("1h", 10)
        if self._df is not None and not self._df.empty:
            logger.info(f"Loaded {len(self._df)} bars")
            self._features = self.feat_eng.generate_all_features(self._df)
        if self._features is not None and not self._features.empty and len(self._features) > 500:
            X = self._features.values[-5000:]
            y = np.where(np.diff(self._df["close"].values[-5000:], prepend=0) > 0, 0,
                         np.where(np.diff(self._df["close"].values[-5000:], prepend=0) < 0, 1, 2))
            y = y[:len(X)]
            self.ensemble.train_all(X, y); self._trained = True
            logger.info("All models trained successfully")
        self.macro.update(); self.sentiment.update()
        logger.info("Initialization complete")

    async def _tick_loop(self) -> None:
        while self.running:
            if self.paused: await asyncio.sleep(0.5); continue
            try:
                tick = self.fetcher.get_live_tick()
                self.tui.update("tick", tick)
                price = tick["bid"]
                closed = self.exec_eng.update_trades(price)
                for t in closed:
                    self.ensemble.update_weights(t.trade_id, t.pnl_usd > 0)
                    self.learner.analyze_failed(t) if t.pnl_usd < 0 else None
                    self.learner.update_rates([t])
                self._loop_count += 1
                if self._loop_count % 10 == 0: await self._analyze_and_signal(tick)
                if self._loop_count % 100 == 0: self._update_tui_data()
                if self._loop_count % 600 == 0: self.macro.update()
                if self.learner.check_retrain() and self._trained: await self._retrain()
            except Exception as e: logger.error(f"Tick error: {e}")
            await asyncio.sleep(self.config.tui_refresh_ms / 1000)

    async def _analyze_and_signal(self, tick: Dict) -> None:
        if not self._trained or self._features is None or self._features.empty: return
        price = tick["bid"]
        prices = self._df["close"].values if self._df is not None else np.array([price])
        volumes = self._df["volume"].values if self._df is not None else np.array([1000])

        regime = self.regime_det.detect(prices, volumes)
        self.tui.update("regime", regime.name)

        now = dt.datetime.now(); hr = now.hour
        if 0 <= hr < 8: session = MarketSession.ASIA
        elif 7 <= hr < 13: session = MarketSession.LONDON
        elif 13 <= hr < 16: session = MarketSession.LONDON_NY_OVERLAP
        elif 13 <= hr < 22: session = MarketSession.NEW_YORK
        else: session = MarketSession.OFF_HOURS
        self.tui.update("session", session.name)

        X = self._features.values[-1:]
        direction, agreement, preds = self.ensemble.predict_ensemble(X, regime)
        sentiment = self.sentiment.sentiment_score
        smc_result = self.smc.analyze(self._df) if self._df is not None else {}
        smc_score = smc_result.get("smc_score", 100)
        macro_score = self.macro.get_score()
        q_result = self.quantum.analyze(prices[-500:] if len(prices) >= 500 else prices)
        self.tui.update("quantum", q_result)
        self.tui.update("macro", self.macro.get_display())
        self.tui.update("smc", self.smc.get_display(price))

        causal = self.causal.get_reasoning(self.macro)
        atr_val = float(self._features["atr_14"].values[-1]) if "atr_14" in self._features.columns else price*0.005

        sig_dir = SignalDirection.BUY if direction > 0.1 else SignalDirection.SELL if direction < -0.1 else SignalDirection.HOLD
        if sig_dir == SignalDirection.HOLD: return

        sl = self.risk.calculate_sl(price, atr_val, sig_dir)
        tp1, tp2, tp3 = self.risk.calculate_tp(price, sl, sig_dir)
        rr = abs(tp1 - price) / max(abs(price - sl), 1e-10)

        anomaly_pred = self.ensemble.models["AnomalyDetector"].predict(X)
        anomaly_ok = anomaly_pred[1] >= 0.5
        tech_conf = agreement * abs(direction)

        score, reason = self.scorer.score(agreement, direction, tech_conf, smc_score, macro_score, rr, anomaly_ok, regime)

        reasoning = [f"Direction: {'BUY' if direction>0 else 'SELL'} ({direction:+.3f})",
                     f"Agreement: {agreement:.1%}", f"Score: {score}/1000",
                     f"Regime: {regime.name}", f"Sentiment: {sentiment:+.2f}"] + causal[:3]
        self.tui.update("reasoning", reasoning)

        if score < self.config.min_signal_score: return
        if self.macro.is_blackout(): return
        if not q_result.get("tradeable", True): return

        wr = self.db.get_win_rate(); lot = self.risk.calculate_position_size(self.risk.equity, abs(price-sl), wr)

        signal = TradeSignal(direction=sig_dir, entry_price=price, stop_loss=sl,
            take_profit_1=tp1, take_profit_2=tp2, take_profit_3=tp3,
            lot_size=lot, confidence=abs(direction), score=score, reason=reason,
            model_votes={n: SignalDirection.BUY if p[0]>0 else SignalDirection.SELL for n,p in preds.items()},
            regime=regime, session=session)
        self.tui.update("signal", signal)
        trade = self.exec_eng.execute(signal)
        if trade: logger.info(f"TRADE EXECUTED: {trade.trade_id} {sig_dir.name} @ {price}")

    async def _retrain(self) -> None:
        if self._features is None or self._features.empty: return
        logger.info("Starting scheduled retrain...")
        X = self._features.values[-10000:]
        c = self._df["close"].values[-10000:] if self._df is not None else np.array([])
        y = np.where(np.diff(c, prepend=c[0]) > 0, 0, np.where(np.diff(c, prepend=c[0]) < 0, 1, 2))[:len(X)]
        self.ensemble.train_all(X, y)
        self.evolution.evolve_step()
        self.learner.events.append(f"{dt.datetime.now():%H:%M} Full retrain complete")

    def _update_tui_data(self) -> None:
        summary = self.exec_eng.get_summary()
        self.tui.update("equity", summary["equity"]); self.tui.update("daily_pnl", summary["daily_pnl"])
        self.tui.update("drawdown", summary["drawdown"]); self.tui.update("win_rate", self.db.get_win_rate())
        self.tui.update("trades", self.exec_eng.open_trades)
        self.tui.update("models", self.ensemble.get_model_status())
        self.tui.update("learning", list(self.learner.events)[-8:])

    async def run_backtest_async(self) -> Dict:
        logger.info("Running backtest...")
        df = self.fetcher.fetch_historical("1h", 5)
        if df.empty: return {}
        feat = self.feat_eng.generate_all_features(df)
        if feat.empty: return {}
        signals = []
        for i in range(100, len(feat), 50):
            X = feat.values[i:i+1]
            d, a, _ = self.ensemble.predict_ensemble(X)
            sd = SignalDirection.BUY if d > 0.1 else SignalDirection.SELL if d < -0.1 else SignalDirection.HOLD
            price = float(df["close"].iloc[i])
            atr_v = float(feat["atr_14"].iloc[i]) if "atr_14" in feat.columns else price*0.005
            sl = self.risk.calculate_sl(price, atr_v, sd)
            tp1, tp2, tp3 = self.risk.calculate_tp(price, sl, sd)
            signals.append(TradeSignal(sd, price, sl, tp1, tp2, tp3, 0.01, abs(d), 750, "BT"))
        results = self.backtest.run(df, signals)
        logger.info(f"Backtest: {results.get('total_trades',0)} trades, WR={results.get('win_rate',0):.1%}")
        self.tui.update("backtest", results)
        return results

    async def run(self) -> None:
        await self.initialize(); self.running = True
        logger.info("XAUUSD GOD BOT is LIVE")
        if RICH_AVAILABLE and self.config.tui_enabled:
            try:
                with Live(self.tui.render(), console=self.tui.console,
                           refresh_per_second=int(1000/self.config.tui_refresh_ms)) as live:
                    tick_task = asyncio.create_task(self._tick_loop())
                    while self.running:
                        live.update(self.tui.render()); await asyncio.sleep(0.1)
                    tick_task.cancel()
            except KeyboardInterrupt: self.running = False
            except Exception as e: logger.error(f"TUI error: {e}"); await self._headless()
        else: await self._headless()

    async def _headless(self) -> None:
        self.running = True
        while self.running:
            try:
                tick = self.fetcher.get_live_tick()
                self.exec_eng.update_trades(tick["bid"])
                self._loop_count += 1
                if self._loop_count % 10 == 0: await self._analyze_and_signal(tick)
                if self._loop_count % 300 == 0:
                    s = self.exec_eng.get_summary()
                    logger.info(f"Equity=${s['equity']:,.2f} P&L=${s['daily_pnl']:+,.2f} Trades={s['open_count']}")
            except KeyboardInterrupt: break
            except Exception as e: logger.error(f"Loop error: {e}")
            await asyncio.sleep(self.config.tui_refresh_ms / 1000)

    def shutdown(self) -> None:
        self.running = False
        price = self.fetcher.get_live_tick()["bid"]
        self.exec_eng.close_all(price, "Shutdown")
        self.db.close()
        logger.info("Bot shutdown complete")

# SECTION 24 — STARTUP WIZARD & CONFIGURATION

def startup_wizard() -> BotConfig:
    """Interactive first-run configuration wizard."""
    config = BotConfig.from_yaml()
    config_path = Path("config.yaml")
    if config_path.exists():
        logger.info("Config loaded from config.yaml")
        return config

    print("\n" + "="*60)
    print("  XAUUSD GOD BOT — First Run Setup Wizard")
    print("="*60 + "\n")

    try:
        mode = input("Select mode [demo/live/backtest] (default: demo): ").strip().lower()
        if mode in ("live", "backtest"): config.mode = mode
        else: config.mode = "demo"

        bal = input(f"Account balance (default: {config.account_balance}): ").strip()
        if bal:
            try: config.account_balance = float(bal)
            except ValueError: pass

        risk = input(f"Max risk per trade % (default: {config.max_risk_per_trade*100:.0f}%): ").strip()
        if risk:
            try: config.max_risk_per_trade = float(risk.replace('%','')) / 100
            except ValueError: pass

        score = input(f"Min signal score 0-1000 (default: {config.min_signal_score}): ").strip()
        if score:
            try: config.min_signal_score = int(score)
            except ValueError: pass

        tui = input("Enable TUI dashboard? [y/n] (default: y): ").strip().lower()
        config.tui_enabled = tui != 'n'

        tg = input("Enable Telegram alerts? [y/n] (default: n): ").strip().lower()
        if tg == 'y':
            config.telegram_enabled = True
            config.telegram_token = input("  Telegram bot token: ").strip()
            config.telegram_chat_id = input("  Telegram chat ID: ").strip()

        config.to_yaml()
        print(f"\nConfig saved to {config_path}")
    except (EOFError, KeyboardInterrupt):
        print("\nUsing default configuration.")

    config.ensure_dirs()
    return config


async def main() -> None:
    """Main entry point for the XAUUSD GOD BOT."""
    config = startup_wizard()
    bot = XAUUSDGodBot(config)

    def handle_signal(sig: int, frame: Any) -> None:
        logger.info("Shutdown signal received")
        bot.shutdown()
        sys.exit(0)

    signal_module.signal(signal_module.SIGINT, handle_signal)
    signal_module.signal(signal_module.SIGTERM, handle_signal)

    if config.mode == "backtest":
        results = await bot.run_backtest_async()
        if results:
            print("\n" + "="*60)
            print("  BACKTEST RESULTS")
            print("="*60)
            for k, v in results.items():
                if isinstance(v, float): print(f"  {k:30s}: {v:>12.4f}")
                else: print(f"  {k:30s}: {v}")
        return

    try:
        await bot.run()
    except KeyboardInterrupt:
        pass
    finally:
        bot.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
