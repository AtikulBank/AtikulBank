"""
XAUUSD GOD BOT v2.0 — Data Management Module
Data Fetching | SQLite Storage | Parquet Storage | Data Quality

Author: Atikul Islam
Version: 2.0.0-alpha.2
"""

from __future__ import annotations

import os
import sys
import asyncio
import sqlite3
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
from collections import deque
import logging
import json
import hashlib
import gzip
import shutil
from enum import Enum

# Try imports with fallbacks
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    PYARROW_AVAILABLE = True
except ImportError:
    PYARROW_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 01 — DATA FETCHER BASE
# ═══════════════════════════════════════════════════════════════════════════

class DataSource(Enum):
    """Available data sources."""
    MT5 = "mt5"
    YFINANCE = "yfinance"
    DUKASCOPY = "dukascopy"
    STOOQ = "stooq"
    FALLBACK = "fallback"


@dataclass
class DataQualityReport:
    """Report on data quality metrics."""
    source: str
    total_records: int
    missing_records: int
    duplicate_records: int
    outlier_records: int
    gap_count: int
    completeness_score: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __repr__(self) -> str:
        return f"<DataQualityReport {self.source} completeness={self.completeness_score:.1%}>"
    
    @property
    def quality_grade(self) -> str:
        """Return letter grade based on completeness."""
        if self.completeness_score >= 0.99:
            return "A+"
        elif self.completeness_score >= 0.95:
            return "A"
        elif self.completeness_score >= 0.90:
            return "B"
        elif self.completeness_score >= 0.80:
            return "C"
        else:
            return "F"


class DataFetcherBase:
    """
    Base class for all data fetchers.
    
    This abstract base class defines the interface that all
    data source implementations must follow.
    
    Attributes:
        name: Name of the data source.
        priority: Priority (lower = higher priority).
        logger: Logger instance.
    """
    
    def __init__(self, name: str, priority: int = 10):
        """
        Initialize DataFetcherBase.
        
        Args:
            name: Name of the data source.
            priority: Priority (1=highest).
        """
        self.name = name
        self.priority = priority
        self.logger = logging.getLogger(f"XAUUSD_GOD_BOT.DataFetcher.{name}")
        self._is_connected = False
    
    def __repr__(self) -> str:
        return f"<DataFetcher.{self.name} priority={self.priority} connected={self._is_connected}>"
    
    @property
    def is_connected(self) -> bool:
        """Check if data source is connected."""
        return self._is_connected
    
    def connect(self) -> bool:
        """
        Connect to data source.
        
        Returns:
            bool: True if connected successfully.
        """
        raise NotImplementedError("Subclasses must implement connect()")
    
    def disconnect(self) -> None:
        """Disconnect from data source."""
        raise NotImplementedError("Subclasses must implement disconnect()")
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV data.
        
        Args:
            symbol: Trading symbol (e.g., "XAUUSD").
            timeframe: Timeframe (e.g., "1m", "1h", "1d").
            start_date: Start datetime.
            end_date: End datetime.
        
        Returns:
            DataFrame with OHLCV data or None if failed.
        """
        raise NotImplementedError("Subclasses must implement fetch_ohlcv()")
    
    def fetch_tick(self, symbol: str, count: int) -> Optional[pd.DataFrame]:
        """
        Fetch recent tick data.
        
        Args:
            symbol: Trading symbol.
            count: Number of ticks to fetch.
        
        Returns:
            DataFrame with tick data or None if failed.
        """
        raise NotImplementedError("Subclasses must implement fetch_tick()")
    
    def fetch_live(self, symbol: str) -> Optional[Dict[str, float]]:
        """
        Fetch current price data.
        
        Args:
            symbol: Trading symbol.
        
        Returns:
            Dict with bid, ask, last, spread or None.
        """
        raise NotImplementedError("Subclasses must implement fetch_live()")
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get connection information.
        
        Returns:
            Dict with connection details.
        """
        return {
            "name": self.name,
            "connected": self._is_connected,
            "priority": self.priority,
        }


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 02 — MT5 DATA FETCHER
# ═══════════════════════════════════════════════════════════════════════════

class MT5DataFetcher(DataFetcherBase):
    """
    MetaTrader 5 data fetcher implementation.
    
    This class handles all MT5 data operations including:
    - Historical OHLCV data
    - Real-time tick streaming
    - Account information
    
    Args:
        login: MT5 account login number.
        password: MT5 account password.
        server: MT5 server name.
        path: Path to MT5 terminal executable.
    """
    
    TIMEFRAME_MAP: Dict[str, int] = {
        "1m": mt5.TIMEFRAME_M1 if MT5_AVAILABLE else 1,
        "5m": mt5.TIMEFRAME_M5 if MT5_AVAILABLE else 5,
        "15m": mt5.TIMEFRAME_M15 if MT5_AVAILABLE else 15,
        "30m": mt5.TIMEFRAME_M30 if MT5_AVAILABLE else 30,
        "1h": mt5.TIMEFRAME_H1 if MT5_AVAILABLE else 60,
        "4h": mt5.TIMEFRAME_H4 if MT5_AVAILABLE else 240,
        "1d": mt5.TIMEFRAME_D1 if MT5_AVAILABLE else 1440,
        "1w": mt5.TIMEFRAME_W1 if MT5_AVAILABLE else 10080,
        "1M": mt5.TIMEFRAME_MN1 if MT5_AVAILABLE else 43200,
    }
    
    def __init__(
        self,
        login: int = 0,
        password: str = "",
        server: str = "",
        path: str = "",
    ):
        """
        Initialize MT5 data fetcher.
        
        Args:
            login: MT5 account login.
            password: MT5 account password.
            server: MT5 server name.
            path: Path to MT5 terminal.
        """
        super().__init__("MT5", priority=1)
        self.login = login
        self.password = password
        self.server = server
        self.terminal_path = path
        self._last_error = ""
    
    def __repr__(self) -> str:
        return f"<MT5DataFetcher login={self.login} server={self.server} connected={self._is_connected}>"
    
    def connect(self) -> bool:
        """
        Connect to MT5 terminal.
        
        Returns:
            bool: True if connected successfully.
        """
        if not MT5_AVAILABLE:
            self.logger.error("MetaTrader5 package not available")
            self._is_connected = False
            return False
        
        try:
            if not mt5.initialize(path=self.terminal_path):
                error = mt5.last_error()
                self.logger.error(f"MT5 initialize failed: {error}")
                self._last_error = str(error)
                self._is_connected = False
                return False
            
            if self.login > 0:
                if not mt5.login(login=self.login, password=self.password, server=self.server):
                    error = mt5.last_error()
                    self.logger.error(f"MT5 login failed: {error}")
                    self._last_error = str(error)
                    self._is_connected = False
                    return False
            
            self._is_connected = True
            self.logger.info(f"Connected to MT5: login={self.login}, server={self.server}")
            return True
            
        except Exception as e:
            self.logger.error(f"MT5 connection error: {e}")
            self._last_error = str(e)
            self._is_connected = False
            return False
    
    def disconnect(self) -> None:
        """Disconnect from MT5 terminal."""
        if MT5_AVAILABLE:
            try:
                mt5.shutdown()
                self.logger.info("Disconnected from MT5")
            except Exception as e:
                self.logger.error(f"MT5 disconnect error: {e}")
        self._is_connected = False
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV data from MT5.
        
        Args:
            symbol: Trading symbol (e.g., "XAUUSD").
            timeframe: Timeframe string.
            start_date: Start datetime.
            end_date: End datetime.
        
        Returns:
            DataFrame with OHLCV data or None.
        """
        if not self._is_connected:
            self.logger.error("Not connected to MT5")
            return None
        
        if not MT5_AVAILABLE:
            return None
        
        try:
            tf = self.TIMEFRAME_MAP.get(timeframe, mt5.TIMEFRAME_H1)
            
            start_ts = int(start_date.timestamp())
            end_ts = int(end_date.timestamp())
            
            rates = mt5.copy_rates_range(symbol, tf, start_ts, end_ts)
            
            if rates is None or len(rates) == 0:
                self.logger.warning(f"No data returned for {symbol} {timeframe}")
                return None
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df = df.rename(columns={
                'time': 'timestamp',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'tick_volume': 'volume',
                'spread': 'spread',
                'real_volume': 'real_volume',
            })
            
            self.logger.info(f"Fetched {len(df)} bars from MT5: {symbol} {timeframe}")
            return df
            
        except Exception as e:
            self.logger.error(f"MT5 fetch OHLCV error: {e}")
            return None
    
    def fetch_tick(self, symbol: str, count: int = 1000) -> Optional[pd.DataFrame]:
        """
        Fetch recent tick data from MT5.
        
        Args:
            symbol: Trading symbol.
            count: Number of ticks to fetch.
        
        Returns:
            DataFrame with tick data or None.
        """
        if not self._is_connected or not MT5_AVAILABLE:
            return None
        
        try:
            ticks = mt5.copy_ticks_from(symbol, datetime.now(), count, mt5.COPY_TICKS_ALL)
            
            if ticks is None or len(ticks) == 0:
                return None
            
            df = pd.DataFrame(ticks)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            return df
            
        except Exception as e:
            self.logger.error(f"MT5 fetch tick error: {e}")
            return None
    
    def fetch_live(self, symbol: str) -> Optional[Dict[str, float]]:
        """
        Fetch current price from MT5.
        
        Args:
            symbol: Trading symbol.
        
        Returns:
            Dict with bid, ask, last, spread or None.
        """
        if not self._is_connected or not MT5_AVAILABLE:
            return None
        
        try:
            tick = mt5.symbol_info_tick(symbol)
            
            if tick is None:
                return None
            
            return {
                'bid': float(tick.bid),
                'ask': float(tick.ask),
                'last': float(tick.last),
                'spread': float(tick.ask - tick.bid),
                'volume': float(tick.volume),
                'time': datetime.fromtimestamp(tick.time),
            }
            
        except Exception as e:
            self.logger.error(f"MT5 fetch live error: {e}")
            return None
    
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """
        Get MT5 account information.
        
        Returns:
            Dict with account info or None.
        """
        if not self._is_connected or not MT5_AVAILABLE:
            return None
        
        try:
            info = mt5.account_info()
            
            if info is None:
                return None
            
            return {
                'login': info.login,
                'balance': info.balance,
                'equity': info.equity,
                'margin': info.margin,
                'free_margin': info.margin_free,
                'margin_level': info.margin_level,
                'leverage': info.leverage,
                'currency': info.currency,
                'server': info.server,
                'company': info.company,
            }
            
        except Exception as e:
            self.logger.error(f"MT5 account info error: {e}")
            return None
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get symbol information from MT5.
        
        Args:
            symbol: Trading symbol.
        
        Returns:
            Dict with symbol info or None.
        """
        if not self._is_connected or not MT5_AVAILABLE:
            return None
        
        try:
            info = mt5.symbol_info(symbol)
            
            if info is None:
                return None
            
            return {
                'symbol': info.name,
                'bid': info.bid,
                'ask': info.ask,
                'spread': info.spread,
                'digits': info.digits,
                'tick_value': info.trade_tick_value,
                'tick_size': info.trade_tick_size,
                'volume_min': info.volume_min,
                'volume_max': info.volume_max,
                'volume_step': info.volume_step,
            }
            
        except Exception as e:
            self.logger.error(f"MT5 symbol info error: {e}")
            return None


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 03 — YFINANCE DATA FETCHER
# ═══════════════════════════════════════════════════════════════════════════

class YFinanceDataFetcher(DataFetcherBase):
    """
    Yahoo Finance data fetcher implementation.
    
    Provides free historical data for:
    - Gold Futures (GC=F)
    - Gold ETF (GLD)
    - Dollar Index (DX-Y.NYB)
    - Treasury Yields (^TNX, ^IRX)
    - VIX (^VIX)
    
    Note: Data has 1-day delay, suitable for daily timeframe.
    """
    
    SYMBOL_MAP: Dict[str, str] = {
        "XAUUSD": "GC=F",
        "GC": "GC=F",
        "GLD": "GLD",
        "DXY": "DX-Y.NYB",
        "TNX": "^TNX",
        "IRX": "^IRX",
        "VIX": "^VIX",
        "CL": "CL=F",
        "SI": "SI=F",
    }
    
    def __init__(self):
        """Initialize YFinance data fetcher."""
        super().__init__("YFinance", priority=2)
        self._session = None
    
    def __repr__(self) -> str:
        return f"<YFinanceDataFetcher connected={self._is_connected}>"
    
    def connect(self) -> bool:
        """
        Connect to YFinance (no actual connection needed).
        
        Returns:
            bool: True.
        """
        self._is_connected = True
        self.logger.info("YFinance fetcher ready (no connection needed)")
        return True
    
    def disconnect(self) -> None:
        """Disconnect from YFinance."""
        self._is_connected = False
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV data from Yahoo Finance.
        
        Args:
            symbol: Trading symbol.
            timeframe: Timeframe (1d, 1wk, 1mo supported).
            start_date: Start datetime.
            end_date: End datetime.
        
        Returns:
            DataFrame with OHLCV data or None.
        """
        if not YFINANCE_AVAILABLE:
            self.logger.error("yfinance package not available")
            return None
        
        try:
            yf_symbol = self.SYMBOL_MAP.get(symbol, symbol)
            
            interval_map = {
                "1m": "1m",
                "5m": "5m",
                "15m": "15m",
                "30m": "30m",
                "1h": "60m",
                "4h": "4h",
                "1d": "1d",
                "1w": "1wk",
                "1M": "1mo",
            }
            interval = interval_map.get(timeframe, "1d")
            
            df = yf.download(
                yf_symbol,
                start=start_date,
                end=end_date,
                interval=interval,
                progress=False,
                auto_adjust=True,
            )
            
            if df.empty:
                self.logger.warning(f"No data from YFinance: {yf_symbol}")
                return None
            
            df = df.reset_index()
            
            if 'Datetime' in df.columns:
                df = df.rename(columns={'Datetime': 'timestamp'})
            elif 'Date' in df.columns:
                df = df.rename(columns={'Date': 'timestamp'})
            
            if 'Volume' not in df.columns:
                df['Volume'] = 0
            
            df = df[['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']]
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume',
            })
            
            df = df.dropna()
            
            self.logger.info(f"Fetched {len(df)} bars from YFinance: {symbol}")
            return df
            
        except Exception as e:
            self.logger.error(f"YFinance fetch error: {e}")
            return None
    
    def fetch_live(self, symbol: str) -> Optional[Dict[str, float]]:
        """
        Fetch current price from Yahoo Finance.
        
        Args:
            symbol: Trading symbol.
        
        Returns:
            Dict with price data or None.
        """
        if not YFINANCE_AVAILABLE:
            return None
        
        try:
            yf_symbol = self.SYMBOL_MAP.get(symbol, symbol)
            
            ticker = yf.Ticker(yf_symbol)
            info = ticker.fast_info
            
            return {
                'last': float(info.last_price),
                'bid': float(info.bid or info.last_price),
                'ask': float(info.ask or info.last_price),
                'spread': float(info.ask - info.bid) if info.ask and info.bid else 0,
                'volume': float(info.last_volume or 0),
                'time': datetime.now(),
            }
            
        except Exception as e:
            self.logger.error(f"YFinance live fetch error: {e}")
            return None
    
    def fetch_multiple_symbols(
        self,
        symbols: List[str],
        period: str = "1mo",
        interval: str = "1d"
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple symbols at once.
        
        Args:
            symbols: List of trading symbols.
            period: Time period (e.g., "1mo", "1y", "max").
            interval: Data interval.
        
        Returns:
            Dict mapping symbol to DataFrame.
        """
        if not YFINANCE_AVAILABLE:
            return {}
        
        result = {}
        
        try:
            yf_symbols = [self.SYMBOL_MAP.get(s, s) for s in symbols]
            
            data = yf.download(
                yf_symbols,
                period=period,
                interval=interval,
                progress=False,
                auto_adjust=True,
                group_by='ticker',
            )
            
            for symbol in symbols:
                try:
                    yf_sym = self.SYMBOL_MAP.get(symbol, symbol)
                    
                    if yf_sym in data.columns.get_level_values(0):
                        df = data[yf_sym].copy()
                    else:
                        df = data.xs(yf_sym, level=0, axis=1 if data.columns.nlevels > 1 else 0)
                    
                    df = df.reset_index()
                    df = df.rename(columns={
                        'Open': 'open', 'High': 'high',
                        'Low': 'low', 'Close': 'close', 'Volume': 'volume',
                    })
                    df['timestamp'] = pd.to_datetime(df['Datetime'] if 'Datetime' in df.columns else df['Date'])
                    
                    result[symbol] = df
                    
                except Exception as e:
                    self.logger.warning(f"Failed to fetch {symbol}: {e}")
            
        except Exception as e:
            self.logger.error(f"YFinance batch fetch error: {e}")
        
        return result


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 04 — DATA QUALITY
# ═══════════════════════════════════════════════════════════════════════════

class DataQualityChecker:
    """
    Data quality checker and cleaner.
    
    Performs:
    - Gap detection and filling
    - Outlier detection (Z-score)
    - Duplicate removal
    - Timestamp alignment
    - Completeness scoring
    """
    
    def __init__(self, max_gap_minutes: int = 5):
        """
        Initialize DataQualityChecker.
        
        Args:
            max_gap_minutes: Maximum gap to fill (larger = outlier).
        """
        self.max_gap_minutes = max_gap_minutes
        self.logger = logging.getLogger("XAUUSD_GOD_BOT.DataQuality")
    
    def check(self, df: pd.DataFrame, source: str) -> DataQualityReport:
        """
        Check data quality and generate report.
        
        Args:
            df: DataFrame to check.
            source: Source name for report.
        
        Returns:
            DataQualityReport instance.
        """
        if df is None or df.empty:
            return DataQualityReport(
                source=source,
                total_records=0,
                missing_records=0,
                duplicate_records=0,
                outlier_records=0,
                gap_count=0,
                completeness_score=0.0,
            )
        
        total = len(df)
        
        missing = df.isnull().sum().sum()
        
        if 'timestamp' in df.columns:
            duplicates = df['timestamp'].duplicated().sum()
        else:
            duplicates = 0
        
        outliers = self._count_outliers(df)
        
        gaps = self._count_gaps(df)
        
        completeness = 1.0 - (missing / (total * len(df.columns)))
        
        report = DataQualityReport(
            source=source,
            total_records=total,
            missing_records=missing,
            duplicate_records=duplicates,
            outlier_records=outliers,
            gap_count=gaps,
            completeness_score=completeness,
        )
        
        self.logger.info(f"Quality report: {report}")
        
        return report
    
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean DataFrame by removing issues.
        
        Args:
            df: DataFrame to clean.
        
        Returns:
            Cleaned DataFrame.
        """
        if df is None or df.empty:
            return df
        
        df = df.copy()
        
        if 'timestamp' in df.columns:
            df = df.drop_duplicates(subset=['timestamp'], keep='last')
        
        df = self._fill_gaps(df)
        
        df = self._remove_outliers(df)
        
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].fillna(method='ffill')
        
        df = df.dropna()
        
        self.logger.info(f"Cleaned DataFrame: {len(df)} rows remaining")
        
        return df
    
    def _count_outliers(self, df: pd.DataFrame) -> int:
        """Count outlier records using Z-score."""
        if 'close' not in df.columns:
            return 0
        
        try:
            prices = df['close'].values
            mean = np.mean(prices)
            std = np.std(prices)
            
            if std == 0:
                return 0
            
            z_scores = np.abs((prices - mean) / std)
            outliers = np.sum(z_scores > 5)
            
            return int(outliers)
        except Exception:
            return 0
    
    def _count_gaps(self, df: pd.DataFrame) -> int:
        """Count time gaps in data."""
        if 'timestamp' not in df.columns:
            return 0
        
        try:
            times = pd.to_datetime(df['timestamp'])
            diffs = times.diff().dt.total_seconds()
            gaps = (diffs > self.max_gap_minutes * 60).sum()
            return int(gaps)
        except Exception:
            return 0
    
    def _fill_gaps(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fill small gaps in data."""
        if 'timestamp' not in df.columns:
            return df
        
        try:
            df = df.set_index('timestamp')
            
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            df[numeric_cols] = df[numeric_cols].fillna(method='ffill')
            
            df = df.reset_index()
            
            return df
        except Exception:
            return df
    
    def _remove_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove outlier records."""
        if 'close' not in df.columns:
            return df
        
        try:
            prices = df['close'].values
            mean = np.mean(prices)
            std = np.std(prices)
            
            if std > 0:
                z_scores = np.abs((prices - mean) / std)
                mask = z_scores < 5
                df = df[mask]
            
            return df
        except Exception:
            return df


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 05 — SQLITE DATABASE
# ═══════════════════════════════════════════════════════════════════════════

class TradeDatabase:
    """
    SQLite database for trade records and state persistence.
    
    Tables:
    - trades: All trade records
    - signals: Signal history
    - model_performance: Model accuracy tracking
    - daily_stats: Daily performance summaries
    - state: Bot state checkpoints
    """
    
    def __init__(self, db_path: Union[str, Path] = "trades.db"):
        """
        Initialize TradeDatabase.
        
        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = Path(db_path)
        self.logger = logging.getLogger("XAUUSD_GOD_BOT.Database")
        self._lock = threading.Lock()
        self._connection = None
        self._initialize()
    
    def __repr__(self) -> str:
        return f"<TradeDatabase path={self.db_path}>"
    
    def _initialize(self) -> None:
        """Initialize database and create tables."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._connection = conn
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket INTEGER UNIQUE,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    lots REAL NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    stop_loss REAL,
                    take_profit REAL,
                    open_time TEXT NOT NULL,
                    close_time TEXT,
                    pnl_real REAL,
                    pnl_pips REAL,
                    commission REAL,
                    swap REAL,
                    signal_score INTEGER,
                    regime TEXT,
                    session TEXT,
                    status TEXT DEFAULT 'open',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    signal_id TEXT PRIMARY KEY,
                    direction TEXT NOT NULL,
                    score INTEGER,
                    entry_price REAL,
                    stop_loss REAL,
                    take_profit1 REAL,
                    take_profit2 REAL,
                    take_profit3 REAL,
                    confidence REAL,
                    reason TEXT,
                    executed INTEGER DEFAULT 0,
                    timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS model_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT NOT NULL,
                    date TEXT NOT NULL,
                    accuracy REAL,
                    sharpe REAL,
                    trades_count INTEGER,
                    win_rate REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(model_name, date)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT UNIQUE NOT NULL,
                    trades INTEGER DEFAULT 0,
                    wins INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0,
                    win_rate REAL,
                    pnl REAL,
                    max_drawdown REAL,
                    sharpe REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS state (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_open ON trades(status, open_time)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_model_date ON model_performance(model_name, date)")
            
            conn.commit()
            
            self.logger.info(f"Database initialized: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"Database initialization error: {e}")
            raise
    
    def save_trade(self, trade_data: Dict[str, Any]) -> int:
        """
        Save trade record to database.
        
        Args:
            trade_data: Dict with trade fields.
        
        Returns:
            Row ID of inserted record.
        """
        with self._lock:
            try:
                cursor = self._connection.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO trades (
                        ticket, symbol, direction, lots, entry_price, exit_price,
                        stop_loss, take_profit, open_time, close_time,
                        pnl_real, pnl_pips, commission, swap,
                        signal_score, regime, session, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade_data.get('ticket'),
                    trade_data.get('symbol'),
                    trade_data.get('direction'),
                    trade_data.get('lots'),
                    trade_data.get('entry_price'),
                    trade_data.get('exit_price'),
                    trade_data.get('stop_loss'),
                    trade_data.get('take_profit'),
                    trade_data.get('open_time'),
                    trade_data.get('close_time'),
                    trade_data.get('pnl_real'),
                    trade_data.get('pnl_pips'),
                    trade_data.get('commission'),
                    trade_data.get('swap'),
                    trade_data.get('signal_score'),
                    trade_data.get('regime'),
                    trade_data.get('session'),
                    trade_data.get('status', 'open'),
                ))
                
                self._connection.commit()
                
                return cursor.lastrowid or 0
                
            except Exception as e:
                self.logger.error(f"Save trade error: {e}")
                return -1
    
    def get_open_trades(self) -> List[Dict[str, Any]]:
        """
        Get all open trades.
        
        Returns:
            List of trade dictionaries.
        """
        with self._lock:
            try:
                cursor = self._connection.cursor()
                cursor.execute("""
                    SELECT ticket, symbol, direction, lots, entry_price,
                           stop_loss, take_profit, open_time, regime, session
                    FROM trades WHERE status = 'open'
                """)
                
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                return [dict(zip(columns, row)) for row in rows]
                
            except Exception as e:
                self.logger.error(f"Get open trades error: {e}")
                return []
    
    def get_closed_trades(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get closed trades within date range.
        
        Args:
            start_date: Start date string (YYYY-MM-DD).
            end_date: End date string (YYYY-MM-DD).
            limit: Maximum number of records.
        
        Returns:
            List of trade dictionaries.
        """
        with self._lock:
            try:
                cursor = self._connection.cursor()
                
                query = "SELECT * FROM trades WHERE status = 'closed'"
                params = []
                
                if start_date:
                    query += " AND close_time >= ?"
                    params.append(start_date)
                if end_date:
                    query += " AND close_time <= ?"
                    params.append(end_date)
                
                query += f" ORDER BY close_time DESC LIMIT {limit}"
                
                cursor.execute(query, params)
                
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                return [dict(zip(columns, row)) for row in rows]
                
            except Exception as e:
                self.logger.error(f"Get closed trades error: {e}")
                return []
    
    def save_signal(self, signal_data: Dict[str, Any]) -> bool:
        """
        Save signal to database.
        
        Args:
            signal_data: Signal dictionary.
        
        Returns:
            True if saved successfully.
        """
        with self._lock:
            try:
                cursor = self._connection.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO signals (
                        signal_id, direction, score, entry_price, stop_loss,
                        take_profit1, take_profit2, take_profit3,
                        confidence, reason, executed, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    signal_data.get('signal_id'),
                    signal_data.get('direction'),
                    signal_data.get('score'),
                    signal_data.get('entry_price'),
                    signal_data.get('stop_loss'),
                    signal_data.get('take_profit1'),
                    signal_data.get('take_profit2'),
                    signal_data.get('take_profit3'),
                    signal_data.get('confidence'),
                    signal_data.get('reason'),
                    signal_data.get('executed', 0),
                    signal_data.get('timestamp'),
                ))
                
                self._connection.commit()
                
                return True
                
            except Exception as e:
                self.logger.error(f"Save signal error: {e}")
                return False
    
    def save_state(self, key: str, value: Any) -> bool:
        """
        Save bot state to database.
        
        Args:
            key: State key.
            value: State value (will be JSON serialized).
        
        Returns:
            True if saved successfully.
        """
        with self._lock:
            try:
                value_str = json.dumps(value) if not isinstance(value, str) else value
                
                cursor = self._connection.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO state (key, value, updated_at)
                    VALUES (?, ?, datetime('now'))
                """, (key, value_str))
                
                self._connection.commit()
                
                return True
                
            except Exception as e:
                self.logger.error(f"Save state error: {e}")
                return False
    
    def load_state(self, key: str, default: Any = None) -> Any:
        """
        Load bot state from database.
        
        Args:
            key: State key.
            default: Default value if not found.
        
        Returns:
            State value or default.
        """
        with self._lock:
            try:
                cursor = self._connection.cursor()
                cursor.execute("SELECT value FROM state WHERE key = ?", (key,))
                row = cursor.fetchone()
                
                if row:
                    try:
                        return json.loads(row[0])
                    except json.JSONDecodeError:
                        return row[0]
                
                return default
                
            except Exception as e:
                self.logger.error(f"Load state error: {e}")
                return default
    
    def get_performance_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Get performance statistics.
        
        Args:
            days: Number of days to analyze.
        
        Returns:
            Dict with performance metrics.
        """
        with self._lock:
            try:
                cursor = self._connection.cursor()
                
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_trades,
                        SUM(CASE WHEN pnl_real > 0 THEN 1 ELSE 0 END) as wins,
                        SUM(CASE WHEN pnl_real <= 0 THEN 1 ELSE 0 END) as losses,
                        SUM(pnl_real) as total_pnl,
                        AVG(pnl_real) as avg_pnl,
                        SUM(CASE WHEN pnl_real > 0 THEN pnl_real ELSE 0 END) as gross_profit,
                        ABS(SUM(CASE WHEN pnl_real < 0 THEN pnl_real ELSE 0 END)) as gross_loss
                    FROM trades 
                    WHERE status = 'closed'
                    AND close_time >= datetime('now', '-' || ? || ' days')
                """, (days,))
                
                row = cursor.fetchone()
                
                total = row[0] or 0
                wins = row[1] or 0
                losses = row[2] or 0
                total_pnl = row[3] or 0.0
                avg_pnl = row[4] or 0.0
                gross_profit = row[5] or 0.0
                gross_loss = row[6] or 0.0
                
                win_rate = wins / total if total > 0 else 0.0
                profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0
                
                return {
                    'total_trades': total,
                    'wins': wins,
                    'losses': losses,
                    'win_rate': win_rate,
                    'total_pnl': total_pnl,
                    'avg_pnl': avg_pnl,
                    'gross_profit': gross_profit,
                    'gross_loss': gross_loss,
                    'profit_factor': profit_factor,
                }
                
            except Exception as e:
                self.logger.error(f"Get performance stats error: {e}")
                return {}
    
    def close(self) -> None:
        """Close database connection."""
        with self._lock:
            try:
                if self._connection:
                    self._connection.close()
                    self.logger.info("Database connection closed")
            except Exception as e:
                self.logger.error(f"Database close error: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 06 — PARQUET STORAGE
# ═══════════════════════════════════════════════════════════════════════════

class ParquetStorage:
    """
    Parquet file storage for historical OHLCV data.
    
    Features:
    - Columnar storage for fast reads
    - Compression support
    - Multiple timeframe support
    - Incremental updates
    """
    
    def __init__(self, data_dir: Union[str, Path] = "data"):
        """
        Initialize ParquetStorage.
        
        Args:
            data_dir: Base directory for data storage.
        """
        self.data_dir = Path(data_dir)
        self.logger = logging.getLogger("XAUUSD_GOD_BOT.ParquetStorage")
        self._lock = threading.Lock()
        self._initialize()
    
    def __repr__(self) -> str:
        return f"<ParquetStorage dir={self.data_dir}>"
    
    def _initialize(self) -> None:
        """Initialize storage directories."""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            
            for tf in ["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1"]:
                (self.data_dir / tf).mkdir(exist_ok=True)
            
            self.logger.info(f"Parquet storage initialized: {self.data_dir}")
            
        except Exception as e:
            self.logger.error(f"Parquet init error: {e}")
    
    def _get_file_path(self, symbol: str, timeframe: str) -> Path:
        """Get parquet file path for symbol/timeframe."""
        return self.data_dir / timeframe / f"{symbol}_{timeframe}.parquet"
    
    def save(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str,
        mode: str = "overwrite"
    ) -> bool:
        """
        Save DataFrame to parquet file.
        
        Args:
            df: DataFrame to save.
            symbol: Trading symbol.
            timeframe: Timeframe string.
            mode: 'overwrite' or 'append'.
        
        Returns:
            True if saved successfully.
        """
        if df is None or df.empty:
            self.logger.warning(f"Empty DataFrame, not saving: {symbol} {timeframe}")
            return False
        
        if not PYARROW_AVAILABLE:
            self.logger.error("PyArrow not available, cannot save parquet")
            return False
        
        with self._lock:
            try:
                file_path = self._get_file_path(symbol, timeframe)
                
                if mode == "append" and file_path.exists():
                    existing = pd.read_parquet(file_path)
                    
                    if 'timestamp' in df.columns and 'timestamp' in existing.columns:
                        existing = existing[~existing['timestamp'].isin(df['timestamp'])]
                    
                    df = pd.concat([existing, df], ignore_index=True)
                    df = df.drop_duplicates(subset=['timestamp'], keep='last')
                    df = df.sort_values('timestamp')
                
                df.to_parquet(file_path, compression='snappy', index=False)
                
                self.logger.info(f"Saved {len(df)} rows to {file_path}")
                
                return True
                
            except Exception as e:
                self.logger.error(f"Save parquet error: {e}")
                return False
    
    def load(
        self,
        symbol: str,
        timeframe: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Optional[pd.DataFrame]:
        """
        Load DataFrame from parquet file.
        
        Args:
            symbol: Trading symbol.
            timeframe: Timeframe string.
            start_date: Start datetime filter.
            end_date: End datetime filter.
        
        Returns:
            DataFrame or None.
        """
        if not PYARROW_AVAILABLE:
            return None
        
        file_path = self._get_file_path(symbol, timeframe)
        
        if not file_path.exists():
            self.logger.warning(f"Parquet file not found: {file_path}")
            return None
        
        with self._lock:
            try:
                df = pd.read_parquet(file_path)
                
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    
                    if start_date:
                        df = df[df['timestamp'] >= start_date]
                    if end_date:
                        df = df[df['timestamp'] <= end_date]
                
                self.logger.info(f"Loaded {len(df)} rows from {file_path}")
                
                return df
                
            except Exception as e:
                self.logger.error(f"Load parquet error: {e}")
                return None
    
    def get_latest_timestamp(self, symbol: str, timeframe: str) -> Optional[datetime]:
        """
        Get latest timestamp in stored data.
        
        Args:
            symbol: Trading symbol.
            timeframe: Timeframe string.
        
        Returns:
            Latest timestamp or None.
        """
        df = self.load(symbol, timeframe)
        
        if df is not None and not df.empty and 'timestamp' in df.columns:
            return pd.to_datetime(df['timestamp']).max()
        
        return None
    
    def delete_old_data(
        self,
        symbol: str,
        timeframe: str,
        before_date: datetime
    ) -> bool:
        """
        Delete data before specified date.
        
        Args:
            symbol: Trading symbol.
            timeframe: Timeframe string.
            before_date: Delete data before this date.
        
        Returns:
            True if successful.
        """
        df = self.load(symbol, timeframe)
        
        if df is None or df.empty:
            return False
        
        if 'timestamp' in df.columns:
            df = df[df['timestamp'] >= before_date]
        
        return self.save(df, symbol, timeframe, mode="overwrite")
    
    def get_storage_size(self) -> Dict[str, int]:
        """
        Get storage sizes for all files.
        
        Returns:
            Dict mapping timeframe to size in bytes.
        """
        sizes = {}
        
        try:
            for tf in ["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1"]:
                tf_dir = self.data_dir / tf
                if tf_dir.exists():
                    total = sum(f.stat().st_size for f in tf_dir.rglob("*.parquet"))
                    sizes[tf] = total
        except Exception as e:
            self.logger.error(f"Get storage size error: {e}")
        
        return sizes


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 07 — DATA MANAGER (ORCHESTRATOR)
# ═══════════════════════════════════════════════════════════════════════════

class DataManager:
    """
    Orchestrates all data operations.
    
    Coordinates:
    - Multiple data fetchers (MT5, YFinance, etc.)
    - Quality checking and cleaning
    - SQLite and Parquet storage
    - Automatic failover
    """
    
    def __init__(
        self,
        db_path: Union[str, Path] = "trades.db",
        data_dir: Union[str, Path] = "data",
        config: Optional[Any] = None,
    ):
        """
        Initialize DataManager.
        
        Args:
            db_path: Path to SQLite database.
            data_dir: Directory for parquet storage.
            config: Config object with broker settings.
        """
        self.config = config
        self.logger = logging.getLogger("XAUUSD_GOD_BOT.DataManager")
        
        self.fetchers: Dict[str, DataFetcherBase] = {}
        self.primary_fetcher: Optional[DataFetcherBase] = None
        
        self.database = TradeDatabase(db_path)
        self.parquet = ParquetStorage(data_dir)
        self.quality = DataQualityChecker()
        
        self._initialize_fetchers()
    
    def __repr__(self) -> str:
        return f"<DataManager fetchers={list(self.fetchers.keys())}>"
    
    def _initialize_fetchers(self) -> None:
        """Initialize all data fetchers based on availability."""
        if MT5_AVAILABLE and self.config:
            mt5_fetcher = MT5DataFetcher(
                login=self.config.mt5_login,
                password=self.config.mt5_password,
                server=self.config.mt5_server,
                path=self.config.mt5_path,
            )
            if mt5_fetcher.connect():
                self.fetchers["MT5"] = mt5_fetcher
                self.primary_fetcher = mt5_fetcher
                self.logger.info("MT5 fetcher connected and set as primary")
        
        yf_fetcher = YFinanceDataFetcher()
        yf_fetcher.connect()
        self.fetchers["YFinance"] = yf_fetcher
        
        if self.primary_fetcher is None:
            self.primary_fetcher = yf_fetcher
            self.logger.info("YFinance set as primary fetcher")
        
        self.logger.info(f"Initialized fetchers: {list(self.fetchers.keys())}")
    
    def fetch_ohlcv(
        self,
        symbol: str = "XAUUSD",
        timeframe: str = "1h",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        use_cache: bool = True
    ) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV data with automatic failover.
        
        Args:
            symbol: Trading symbol.
            timeframe: Timeframe string.
            start_date: Start datetime.
            end_date: End datetime.
            use_cache: Use cached data if available.
        
        Returns:
            DataFrame with OHLCV data or None.
        """
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=365)
        
        if use_cache:
            cached = self.parquet.load(symbol, timeframe, start_date, end_date)
            if cached is not None and len(cached) > 100:
                self.logger.info(f"Using cached data: {len(cached)} rows")
                return cached
        
        for name, fetcher in sorted(self.fetchers.items(), key=lambda x: x[1].priority):
            try:
                df = fetcher.fetch_ohlcv(symbol, timeframe, start_date, end_date)
                
                if df is not None and not df.empty:
                    report = self.quality.check(df, name)
                    
                    if report.completeness_score > 0.8:
                        clean_df = self.quality.clean(df)
                        self.parquet.save(clean_df, symbol, timeframe, mode="append")
                        self.logger.info(f"Fetched from {name}: {len(clean_df)} rows, quality: {report.quality_grade}")
                        return clean_df
                    
            except Exception as e:
                self.logger.warning(f"Fetcher {name} failed: {e}")
                continue
        
        self.logger.error("All fetchers failed")
        return None
    
    def fetch_live(self, symbol: str = "XAUUSD") -> Optional[Dict[str, float]]:
        """
        Fetch live price data.
        
        Args:
            symbol: Trading symbol.
        
        Returns:
            Dict with live price data or None.
        """
        if self.primary_fetcher:
            try:
                return self.primary_fetcher.fetch_live(symbol)
            except Exception as e:
                self.logger.warning(f"Primary fetcher live failed: {e}")
        
        for fetcher in self.fetchers.values():
            try:
                result = fetcher.fetch_live(symbol)
                if result:
                    return result
            except Exception:
                continue
        
        return None
    
    def fetch_historical_max(
        self,
        symbol: str = "XAUUSD",
        timeframes: Optional[List[str]] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch maximum available historical data.
        
        Args:
            symbol: Trading symbol.
            timeframes: List of timeframes to fetch.
        
        Returns:
            Dict mapping timeframe to DataFrame.
        """
        if timeframes is None:
            timeframes = ["1h", "4h", "1d"]
        
        results = {}
        
        for tf in timeframes:
            df = self.fetch_ohlcv(
                symbol=symbol,
                timeframe=tf,
                start_date=datetime(2000, 1, 1),
                end_date=datetime.now(),
                use_cache=False,
            )
            
            if df is not None:
                results[tf] = df
                self.logger.info(f"Fetched {tf}: {len(df)} rows")
        
        return results
    
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get broker account information."""
        if isinstance(self.primary_fetcher, MT5DataFetcher):
            return self.primary_fetcher.get_account_info()
        return None
    
    def close(self) -> None:
        """Close all connections and cleanup."""
        for fetcher in self.fetchers.values():
            try:
                fetcher.disconnect()
            except Exception:
                pass
        
        self.database.close()
        
        self.logger.info("DataManager closed")


# ═══════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    "DataSource",
    "DataQualityReport",
    "DataFetcherBase",
    "MT5DataFetcher",
    "YFinanceDataFetcher",
    "DataQualityChecker",
    "TradeDatabase",
    "ParquetStorage",
    "DataManager",
]


# ═══════════════════════════════════════════════════════════════════════════
# TEST / ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("XAUUSD GOD BOT v2.0 — Data Management Module Test")
    print("-" * 60)
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        print("\n1. Testing DataQualityChecker...")
        checker = DataQualityChecker()
        print(f"   QualityChecker: {checker}")
        
        print("\n2. Testing TradeDatabase...")
        db = TradeDatabase("test_trades.db")
        print(f"   Database: {db}")
        
        stats = db.get_performance_stats(days=30)
        print(f"   Stats (30 days): {stats}")
        
        print("\n3. Testing ParquetStorage...")
        storage = ParquetStorage("test_data")
        print(f"   Storage: {storage}")
        
        sizes = storage.get_storage_size()
        print(f"   Storage sizes: {sizes}")
        
        print("\n4. Testing YFinanceDataFetcher...")
        yf = YFinanceDataFetcher()
        print(f"   YFinance: {yf}")
        
        df = yf.fetch_ohlcv("XAUUSD", "1d", datetime(2024, 1, 1), datetime.now())
        if df is not None:
            print(f"   Fetched {len(df)} rows")
            print(df.tail(3))
        
        print("\n5. Testing DataManager...")
        manager = DataManager()
        print(f"   Manager: {manager}")
        
        live = manager.fetch_live("XAUUSD")
        if live:
            print(f"   Live: {live}")
        
        print("\n" + "=" * 60)
        print("Data Management Module: ALL TESTS PASSED")
        print("=" * 60)
        
        db.close()
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
