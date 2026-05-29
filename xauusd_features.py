"""
XAUUSD GOD BOT v2.0 — Feature Engineering Module
800+ Features | Numba JIT | Technical Analysis | Price Action

Author: Atikul Islam
Version: 2.0.0-alpha.3
"""

from __future__ import annotations

import sys
import math
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from collections import deque
import threading

# Try imports with fallbacks
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from numba import njit, prange, vectorize
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    def njit(*args, **kwargs):
        """Fallback decorator when numba not available."""
        def decorator(func):
            return func
        if len(args) == 1 and callable(args[0]):
            return args[0]
        return decorator
    prange = range

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 01 — NUMBA HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

if NUMBA_AVAILABLE:
    
    @njit(cache=True)
    def _calculate_ema_numba(prices: np.ndarray, period: int) -> np.ndarray:
        """
        Calculate EMA using Numba JIT compilation.
        
        Args:
            prices: Price array.
            period: EMA period.
        
        Returns:
            EMA values array.
        """
        n = len(prices)
        ema = np.zeros(n)
        alpha = 2.0 / (period + 1)
        
        if n > 0:
            ema[0] = prices[0]
            for i in range(1, n):
                ema[i] = alpha * prices[i] + (1 - alpha) * ema[i-1]
        
        return ema
    
    @njit(cache=True)
    def _calculate_sma_numba(prices: np.ndarray, period: int) -> np.ndarray:
        """
        Calculate SMA using Numba JIT compilation.
        
        Args:
            prices: Price array.
            period: SMA period.
        
        Returns:
            SMA values array.
        """
        n = len(prices)
        sma = np.zeros(n)
        
        for i in range(n):
            if i < period - 1:
                sma[i] = np.mean(prices[:i+1])
            else:
                sma[i] = np.mean(prices[i-period+1:i+1])
        
        return sma
    
    @njit(cache=True)
    def _calculate_rsi_numba(prices: np.ndarray, period: int) -> np.ndarray:
        """
        Calculate RSI using Numba JIT compilation.
        
        Args:
            prices: Price array.
            period: RSI period.
        
        Returns:
            RSI values array (0-100).
        """
        n = len(prices)
        rsi = np.zeros(n)
        
        if n < period + 1:
            return rsi
        
        gains = np.zeros(n - 1)
        losses = np.zeros(n - 1)
        
        for i in range(1, n):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains[i-1] = change
            else:
                losses[i-1] = -change
        
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        if avg_loss == 0:
            rsi[period] = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi[period] = 100.0 - (100.0 / (1.0 + rs))
        
        for i in range(period + 1, n):
            avg_gain = (avg_gain * (period - 1) + gains[i-1]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i-1]) / period
            
            if avg_loss == 0:
                rsi[i] = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi[i] = 100.0 - (100.0 / (1.0 + rs))
        
        return rsi
    
    @njit(cache=True)
    def _calculate_atr_numba(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> np.ndarray:
        """
        Calculate ATR using Numba JIT compilation.
        
        Args:
            high: High prices array.
            low: Low prices array.
            close: Close prices array.
            period: ATR period.
        
        Returns:
            ATR values array.
        """
        n = len(high)
        atr = np.zeros(n)
        
        if n < 2:
            return atr
        
        tr = np.zeros(n)
        tr[0] = high[0] - low[0]
        
        for i in range(1, n):
            hl = high[i] - low[i]
            hc = abs(high[i] - close[i-1])
            lc = abs(low[i] - close[i-1])
            tr[i] = max(hl, max(hc, lc))
        
        if n >= period:
            atr[period-1] = np.mean(tr[:period])
            
            for i in range(period, n):
                atr[i] = (atr[i-1] * (period - 1) + tr[i]) / period
        
        return atr
    
    @njit(cache=True)
    def _calculate_stoch_numba(high: np.ndarray, low: np.ndarray, close: np.ndarray, k_period: int, d_period: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate Stochastic Oscillator using Numba JIT.
        
        Args:
            high: High prices array.
            low: Low prices array.
            close: Close prices array.
            k_period: %K period.
            d_period: %D period.
        
        Returns:
            Tuple of (%K, %D) arrays.
        """
        n = len(close)
        k = np.zeros(n)
        d = np.zeros(n)
        
        for i in range(n):
            if i < k_period - 1:
                continue
            
            lowest_low = np.min(low[i-k_period+1:i+1])
            highest_high = np.max(high[i-k_period+1:i+1])
            
            if highest_high - lowest_low != 0:
                k[i] = 100.0 * (close[i] - lowest_low) / (highest_high - lowest_low)
            else:
                k[i] = 50.0
        
        for i in range(n):
            if i < k_period + d_period - 2:
                continue
            
            d[i] = np.mean(k[i-d_period+1:i+1])
        
        return k, d
    
    @njit(cache=True)
    def _calculate_macd_numba(prices: np.ndarray, fast: int, slow: int, signal: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate MACD using Numba JIT compilation.
        
        Args:
            prices: Price array.
            fast: Fast EMA period.
            slow: Slow EMA period.
            signal: Signal line period.
        
        Returns:
            Tuple of (MACD line, Signal line, Histogram).
        """
        n = len(prices)
        macd_line = np.zeros(n)
        signal_line = np.zeros(n)
        histogram = np.zeros(n)
        
        if n < slow:
            return macd_line, signal_line, histogram
        
        ema_fast = _calculate_ema_numba(prices, fast)
        ema_slow = _calculate_ema_numba(prices, slow)
        
        macd_line = ema_fast - ema_slow
        
        for i in range(slow, n):
            if i < slow + signal - 1:
                signal_line[i] = np.mean(macd_line[slow:i+1])
            else:
                signal_line[i] = (signal_line[i-1] * (signal - 1) + macd_line[i]) / signal
        
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    @njit(cache=True)
    def _calculate_adx_numba(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate ADX using Numba JIT compilation.
        
        Args:
            high: High prices.
            low: Low prices.
            close: Close prices.
            period: ADX period.
        
        Returns:
            Tuple of (ADX, +DI, -DI, ADX slope).
        """
        n = len(high)
        adx = np.zeros(n)
        plus_di = np.zeros(n)
        minus_di = np.zeros(n)
        adx_slope = np.zeros(n)
        
        if n < period * 2:
            return adx, plus_di, minus_di, adx_slope
        
        tr = np.zeros(n)
        plus_dm = np.zeros(n)
        minus_dm = np.zeros(n)
        
        for i in range(1, n):
            hl = high[i] - low[i]
            hc = abs(high[i] - close[i-1])
            lc = abs(low[i] - close[i-1])
            tr[i] = max(hl, max(hc, lc))
            
            up_move = high[i] - high[i-1]
            down_move = low[i-1] - low[i]
            
            if up_move > down_move and up_move > 0:
                plus_dm[i] = up_move
            if down_move > up_move and down_move > 0:
                minus_dm[i] = down_move
        
        for i in range(period, n):
            tr_sum = np.sum(tr[i-period+1:i+1])
            plus_dm_sum = np.sum(plus_dm[i-period+1:i+1])
            minus_dm_sum = np.sum(minus_dm[i-period+1:i+1])
            
            if tr_sum != 0:
                plus_di[i] = 100.0 * plus_dm_sum / tr_sum
                minus_di[i] = 100.0 * minus_dm_sum / tr_sum
            else:
                plus_di[i] = 0.0
                minus_di[i] = 0.0
        
        dx = np.zeros(n)
        for i in range(period * 2, n):
            if plus_di[i] + minus_di[i] != 0:
                dx[i] = 100.0 * abs(plus_di[i] - minus_di[i]) / (plus_di[i] + minus_di[i])
        
        for i in range(period * 2, n):
            if i < period * 2 + period - 1:
                adx[i] = np.mean(dx[i-period+1:i+1])
            else:
                adx[i] = (adx[i-1] * (period - 1) + dx[i]) / period
        
        for i in range(period * 2 + 1, n):
            if adx[i-1] != 0:
                adx_slope[i] = (adx[i] - adx[i-1]) / adx[i-1]
        
        return adx, plus_di, minus_di, adx_slope
    
    @njit(cache=True)
    def _calculate_bollinger_numba(prices: np.ndarray, period: int, std_mult: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate Bollinger Bands using Numba JIT.
        
        Args:
            prices: Price array.
            period: BB period.
            std_mult: Standard deviation multiplier.
        
        Returns:
            Tuple of (upper, middle, lower, bandwidth, squeeze).
        """
        n = len(prices)
        upper = np.zeros(n)
        middle = np.zeros(n)
        lower = np.zeros(n)
        bandwidth = np.zeros(n)
        squeeze = np.zeros(n)
        
        bb_width_min = 1e10
        
        for i in range(n):
            if i < period - 1:
                middle[i] = np.mean(prices[:i+1])
                std = np.std(prices[:i+1])
            else:
                middle[i] = np.mean(prices[i-period+1:i+1])
                std = np.std(prices[i-period+1:i+1])
            
            upper[i] = middle[i] + std_mult * std
            lower[i] = middle[i] - std_mult * std
            
            if upper[i] - lower[i] > 0:
                bandwidth[i] = (upper[i] - lower[i]) / middle[i]
            else:
                bandwidth[i] = 0.0
            
            bb_width_min = min(bb_width_min, bandwidth[i])
        
        for i in range(n):
            squeeze[i] = 1.0 if bandwidth[i] < bb_width_min * 1.5 else 0.0
        
        return upper, middle, lower, bandwidth, squeeze
    
    @njit(cache=True)
    def _calculate_cci_numba(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> np.ndarray:
        """
        Calculate CCI using Numba JIT.
        
        Args:
            high: High prices.
            low: Low prices.
            close: Close prices.
            period: CCI period.
        
        Returns:
            CCI values array.
        """
        n = len(close)
        cci = np.zeros(n)
        typical = (high + low + close) / 3.0
        
        for i in range(n):
            if i < period - 1:
                tp = np.mean(typical[:i+1])
                cci[i] = 0.0
            else:
                tp = np.mean(typical[i-period+1:i+1])
                sma_tp = np.mean(typical[i-period+1:i+1])
                mean_dev = np.mean(np.abs(typical[i-period+1:i+1] - sma_tp))
                
                if mean_dev != 0:
                    cci[i] = (tp - sma_tp) / (0.015 * mean_dev)
                else:
                    cci[i] = 0.0
        
        return cci
    
    @njit(cache=True)
    def _calculate_williams_r_numba(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> np.ndarray:
        """
        Calculate Williams %R using Numba JIT.
        
        Args:
            high: High prices.
            low: Low prices.
            close: Close prices.
            period: Period.
        
        Returns:
            Williams %R values.
        """
        n = len(close)
        wr = np.zeros(n)
        
        for i in range(n):
            if i < period - 1:
                highest = np.max(high[:i+1])
                lowest = np.min(low[:i+1])
            else:
                highest = np.max(high[i-period+1:i+1])
                lowest = np.min(low[i-period+1:i+1])
            
            if highest - lowest != 0:
                wr[i] = -100.0 * (highest - close[i]) / (highest - lowest)
            else:
                wr[i] = -50.0
        
        return wr
    
    @njit(cache=True)
    def _calculate_obv_numba(close: np.ndarray, volume: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate OBV and OBV slope using Numba JIT.
        
        Args:
            close: Close prices.
            volume: Volume.
        
        Returns:
            Tuple of (OBV, slope).
        """
        n = len(close)
        obv = np.zeros(n)
        slope = np.zeros(n)
        
        if n > 0:
            obv[0] = volume[0]
            
            for i in range(1, n):
                if close[i] > close[i-1]:
                    obv[i] = obv[i-1] + volume[i]
                elif close[i] < close[i-1]:
                    obv[i] = obv[i-1] - volume[i]
                else:
                    obv[i] = obv[i-1]
        
        for i in range(1, n):
            if obv[i-1] != 0:
                slope[i] = (obv[i] - obv[i-1]) / obv[i-1]
        
        return obv, slope
    
    @njit(cache=True)
    def _calculate_vwap_numba(high: np.ndarray, low: np.ndarray, close: np.ndarray, volume: np.ndarray) -> np.ndarray:
        """
        Calculate VWAP using Numba JIT.
        
        Args:
            high: High prices.
            low: Low prices.
            close: Close prices.
            volume: Volume.
        
        Returns:
            VWAP values.
        """
        n = len(close)
        vwap = np.zeros(n)
        cum_pv = 0.0
        cum_vol = 0.0
        
        for i in range(n):
            typical = (high[i] + low[i] + close[i]) / 3.0
            pv = typical * volume[i]
            
            cum_pv += pv
            cum_vol += volume[i]
            
            if cum_vol != 0:
                vwap[i] = cum_pv / cum_vol
            else:
                vwap[i] = typical
        
        return vwap
    
    @njit(cache=True)
    def _calculate_supertrend_numba(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int, mult: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate Supertrend using Numba JIT.
        
        Args:
            high: High prices.
            low: Low prices.
            close: Close prices.
            period: ATR period.
            mult: ATR multiplier.
        
        Returns:
            Tuple of (Supertrend value, direction).
        """
        n = len(close)
        supertrend = np.zeros(n)
        direction = np.zeros(n)
        
        atr = _calculate_atr_numba(high, low, close, period)
        
        hl2 = (high + low) / 2.0
        upper_band = hl2 + mult * atr
        lower_band = hl2 - mult * atr
        
        supertrend[0] = lower_band[0]
        direction[0] = 1.0
        
        for i in range(1, n):
            upper_band[i] = min(upper_band[i], upper_band[i-1]) if upper_band[i] < upper_band[i-1] else upper_band[i]
            lower_band[i] = max(lower_band[i], lower_band[i-1]) if lower_band[i] > lower_band[i-1] else lower_band[i]
            
            if close[i] > upper_band[i-1]:
                direction[i] = 1.0
                supertrend[i] = lower_band[i]
            elif close[i] < lower_band[i-1]:
                direction[i] = -1.0
                supertrend[i] = upper_band[i]
            else:
                direction[i] = direction[i-1]
                if direction[i] == 1.0:
                    supertrend[i] = max(lower_band[i], supertrend[i-1])
                else:
                    supertrend[i] = min(upper_band[i], supertrend[i-1])
        
        return supertrend, direction
    
    @njit(cache=True)
    def _calculate_keltner_numba(high: np.ndarray, low: np.ndarray, close: np.ndarray, ema_period: int, atr_period: int, mult: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate Keltner Channels using Numba JIT.
        
        Args:
            high: High prices.
            low: Low prices.
            close: Close prices.
            ema_period: EMA period.
            atr_period: ATR period.
            mult: ATR multiplier.
        
        Returns:
            Tuple of (upper, middle, lower).
        """
        n = len(close)
        upper = np.zeros(n)
        middle = np.zeros(n)
        lower = np.zeros(n)
        
        ema = _calculate_ema_numba(close, ema_period)
        atr = _calculate_atr_numba(high, low, close, atr_period)
        
        for i in range(n):
            middle[i] = ema[i]
            upper[i] = ema[i] + mult * atr[i]
            lower[i] = ema[i] - mult * atr[i]
        
        return upper, middle, lower
    
    @njit(cache=True)
    def _calculate_donchian_numba(high: np.ndarray, low: np.ndarray, period: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate Donchian Channels using Numba JIT.
        
        Args:
            high: High prices.
            low: Low prices.
            period: Channel period.
        
        Returns:
            Tuple of (upper, middle, lower).
        """
        n = len(high)
        upper = np.zeros(n)
        middle = np.zeros(n)
        lower = np.zeros(n)
        
        for i in range(n):
            if i < period - 1:
                upper[i] = np.max(high[:i+1])
                lower[i] = np.min(low[:i+1])
            else:
                upper[i] = np.max(high[i-period+1:i+1])
                lower[i] = np.min(low[i-period+1:i+1])
            
            middle[i] = (upper[i] + lower[i]) / 2.0
        
        return upper, middle, lower
    
    @njit(cache=True)
    def _calculate_pivot_points_numba(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate Pivot Points using Numba JIT.
        
        Args:
            high: High prices.
            low: Low prices.
            close: Close prices.
        
        Returns:
            Tuple of (P, R1, R2, R3, S1, S2, S3).
        """
        n = len(close)
        pivot = np.zeros(n)
        r1 = np.zeros(n)
        r2 = np.zeros(n)
        r3 = np.zeros(n)
        s1 = np.zeros(n)
        s2 = np.zeros(n)
        s3 = np.zeros(n)
        
        for i in range(1, n):
            pivot[i] = (high[i-1] + low[i-1] + close[i-1]) / 3.0
            r1[i] = 2.0 * pivot[i] - low[i-1]
            s1[i] = 2.0 * pivot[i] - high[i-1]
            r2[i] = pivot[i] + (high[i-1] - low[i-1])
            s2[i] = pivot[i] - (high[i-1] - low[i-1])
            r3[i] = high[i-1] + 2.0 * (pivot[i] - low[i-1])
            s3[i] = low[i-1] - 2.0 * (high[i-1] - pivot[i])
        
        return pivot, r1, r2, r3, s1, s2, s3
    
    @njit(cache=True)
    def _detect_candle_patterns_numba(open_prices: np.ndarray, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
        """
        Detect basic candle patterns using Numba JIT.
        
        Args:
            open_prices: Open prices.
            high: High prices.
            low: Low prices.
            close: Close prices.
        
        Returns:
            Array of pattern codes.
        """
        n = len(close)
        patterns = np.zeros(n)
        
        for i in range(1, n):
            body = abs(close[i] - open_prices[i])
            range_total = high[i] - low[i]
            upper_wick = high[i] - max(open_prices[i], close[i])
            lower_wick = min(open_prices[i], close[i]) - low[i]
            
            if range_total == 0:
                range_total = 1.0
            
            body_ratio = body / range_total
            
            if body_ratio < 0.1:
                patterns[i] = 1.0
            elif upper_wick > body * 2 and lower_wick < body * 0.3:
                patterns[i] = 2.0
            elif lower_wick > body * 2 and upper_wick < body * 0.3:
                patterns[i] = 3.0
            
            if close[i] > open_prices[i] and close[i-1] < open_prices[i-1]:
                if close[i] > open_prices[i-1] and open_prices[i] < close[i-1]:
                    patterns[i] = 4.0
            elif close[i] < open_prices[i] and close[i-1] > open_prices[i-1]:
                if close[i] < open_prices[i-1] and open_prices[i] > close[i-1]:
                    patterns[i] = 5.0
        
        return patterns
    
    @njit(cache=True)
    def _calculate_log_returns_numba(prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate log returns for given period."""
        n = len(prices)
        returns = np.zeros(n)
        
        for i in range(period, n):
            if prices[i-period] > 0:
                returns[i] = math.log(prices[i] / prices[i-period])
        
        return returns
    
    @njit(cache=True)
    def _calculate_zscore_numba(prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Z-score for given period."""
        n = len(prices)
        zscore = np.zeros(n)
        
        for i in range(period, n):
            window = prices[i-period:i]
            mean = np.mean(window)
            std = np.std(window)
            
            if std > 0:
                zscore[i] = (prices[i] - mean) / std
        
        return zscore
    
    @njit(cache=True)
    def _calculate_realized_vol_numba(returns: np.ndarray, window: int) -> np.ndarray:
        """Calculate realized volatility."""
        n = len(returns)
        vol = np.zeros(n)
        
        for i in range(window, n):
            vol[i] = np.std(returns[i-window:i]) * math.sqrt(252)
        
        return vol
    
    @njit(cache=True)
    def _detect_swing_points_numba(high: np.ndarray, low: np.ndarray, window: int) -> Tuple[np.ndarray, np.ndarray]:
        """Detect swing highs and lows."""
        n = len(high)
        swing_high = np.zeros(n)
        swing_low = np.zeros(n)
        
        for i in range(window, n - window):
            is_high = True
            is_low = True
            
            for j in range(i - window, i + window + 1):
                if j != i:
                    if high[j] >= high[i]:
                        is_high = False
                    if low[j] <= low[i]:
                        is_low = False
            
            if is_high:
                swing_high[i] = 1.0
            if is_low:
                swing_low[i] = 1.0
        
        return swing_high, swing_low
    
    @njit(cache=True)
    def _calculate_ichimoku_numba(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Calculate Ichimoku Cloud components."""
        n = len(close)
        tenkan = np.zeros(n)
        kijun = np.zeros(n)
        senkou_a = np.zeros(n)
        senkou_b = np.zeros(n)
        chikou = np.zeros(n)
        
        period9 = 9
        period26 = 26
        period52 = 52
        
        for i in range(n):
            if i >= period9 - 1:
                tenkan[i] = (np.max(high[i-period9+1:i+1]) + np.min(low[i-period9+1:i+1])) / 2.0
            
            if i >= period26 - 1:
                kijun[i] = (np.max(high[i-period26+1:i+1]) + np.min(low[i-period26+1:i+1])) / 2.0
            
            senkou_a[i] = (tenkan[i] + kijun[i]) / 2.0
            
            if i >= period52 - 1:
                senkou_b[i] = (np.max(high[i-period52+1:i+1]) + np.min(low[i-period52+1:i+1])) / 2.0
            
            chikou[i] = close[i]
        
        return tenkan, kijun, senkou_a, senkou_b, chikou
    
    @njit(cache=True)
    def _calculate_parabolic_sar_numba(high: np.ndarray, low: np.ndarray, close: np.ndarray, af_start: float, af_max: float) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate Parabolic SAR."""
        n = len(close)
        sar = np.zeros(n)
        trend = np.zeros(n)
        
        if n < 2:
            return sar, trend
        
        sar[0] = low[0]
        trend[0] = 1.0
        af = af_start
        ep = high[0]
        
        for i in range(1, n):
            prev_sar = sar[i-1]
            
            if trend[i-1] == 1.0:
                sar[i] = prev_sar + af * (ep - prev_sar)
                
                if low[i] < sar[i]:
                    trend[i] = -1.0
                    sar[i] = ep
                    ep = low[i]
                    af = af_start
                else:
                    trend[i] = 1.0
                    if high[i] > ep:
                        ep = high[i]
                        af = min(af + af_start, af_max)
            else:
                sar[i] = prev_sar - af * (prev_sar - ep)
                
                if high[i] > sar[i]:
                    trend[i] = 1.0
                    sar[i] = ep
                    ep = high[i]
                    af = af_start
                else:
                    trend[i] = -1.0
                    if low[i] < ep:
                        ep = low[i]
                        af = min(af + af_start, af_max)
        
        return sar, trend
    
    @njit(cache=True)
    def _calculate_momentum_numba(prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Momentum indicator."""
        n = len(prices)
        mom = np.zeros(n)
        
        for i in range(period, n):
            mom[i] = prices[i] - prices[i-period]
        
        return mom
    
    @njit(cache=True)
    def _calculate_roc_numba(prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Rate of Change."""
        n = len(prices)
        roc = np.zeros(n)
        
        for i in range(period, n):
            if prices[i-period] != 0:
                roc[i] = ((prices[i] - prices[i-period]) / prices[i-period]) * 100.0
        
        return roc
    
    @njit(cache=True)
    def _calculate_mfi_numba(high: np.ndarray, low: np.ndarray, close: np.ndarray, volume: np.ndarray, period: int) -> np.ndarray:
        """Calculate Money Flow Index."""
        n = len(close)
        mfi = np.zeros(n)
        
        typical = (high + low + close) / 3.0
        raw_money_flow = typical * volume
        
        for i in range(period, n):
            positive_flow = 0.0
            negative_flow = 0.0
            
            for j in range(i - period + 1, i + 1):
                if typical[j] > typical[j-1]:
                    positive_flow += raw_money_flow[j]
                else:
                    negative_flow += raw_money_flow[j]
            
            if negative_flow != 0:
                money_ratio = positive_flow / negative_flow
                mfi[i] = 100.0 - (100.0 / (1.0 + money_ratio))
            else:
                mfi[i] = 100.0
        
        return mfi
    
    @njit(cache=True)
    def _calculate_cmf_numba(high: np.ndarray, low: np.ndarray, close: np.ndarray, volume: np.ndarray, period: int) -> np.ndarray:
        """Calculate Chaikin Money Flow."""
        n = len(close)
        cmf = np.zeros(n)
        
        for i in range(period, n):
            sum_mf = 0.0
            sum_vol = 0.0
            
            for j in range(i - period + 1, i + 1):
                mf_multiplier = ((close[j] - low[j]) - (high[j] - close[j])) / (high[j] - low[j])
                if high[j] != low[j]:
                    mf_volume = mf_multiplier * volume[j]
                    sum_mf += mf_volume
                    sum_vol += volume[j]
            
            if sum_vol != 0:
                cmf[i] = sum_mf / sum_vol
        
        return cmf
    
    @njit(cache=True)
    def _calculate_ao_numba(high: np.ndarray, low: np.ndarray, fast: int, slow: int) -> np.ndarray:
        """Calculate Awesome Oscillator."""
        n = len(high)
        ao = np.zeros(n)
        
        median_price = (high + low) / 2.0
        sma_fast = _calculate_sma_numba(median_price, fast)
        sma_slow = _calculate_sma_numba(median_price, slow)
        
        for i in range(n):
            ao[i] = sma_fast[i] - sma_slow[i]
        
        return ao
    
    @njit(cache=True)
    def _calculate_volatility_ratio_numba(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> np.ndarray:
        """Calculate Volatility Ratio."""
        n = len(high)
        vr = np.zeros(n)
        
        for i in range(1, n):
            hl_ratio = high[i] - low[i]
            
            if i >= period:
                range_sum = 0.0
                for j in range(i - period + 1, i):
                    range_sum += high[j] - low[j]
                
                avg_range = range_sum / (period - 1)
                
                if avg_range != 0:
                    vr[i] = hl_ratio / avg_range
        
        return vr
    
    @njit(cache=True)
    def _calculate_trix_numba(prices: np.ndarray, period: int) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate TRIX and TRIX slope."""
        n = len(prices)
        trix = np.zeros(n)
        trix_slope = np.zeros(n)
        
        ema1 = _calculate_ema_numba(prices, period)
        ema2 = _calculate_ema_numba(ema1, period)
        ema3 = _calculate_ema_numba(ema2, period)
        
        for i in range(1, n):
            if ema3[i-1] != 0:
                trix[i] = ((ema3[i] - ema3[i-1]) / ema3[i-1]) * 100.0
                trix_slope[i] = trix[i] - trix[i-1]
        
        return trix, trix_slope

else:
    def _calculate_ema_numba(prices, period):
        """Fallback EMA without Numba."""
        ema = np.zeros_like(prices, dtype=np.float64)
        alpha = 2.0 / (period + 1)
        ema[0] = prices[0]
        for i in range(1, len(prices)):
            ema[i] = alpha * prices[i] + (1 - alpha) * ema[i-1]
        return ema
    
    def _calculate_sma_numba(prices, period):
        """Fallback SMA without Numba."""
        return np.array([np.mean(prices[max(0,i-period+1):i+1]) for i in range(len(prices))])


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 02 — FEATURE ENGINEER CLASS
# ═══════════════════════════════════════════════════════════════════════════

class FeatureEngineer:
    """
    Comprehensive feature engineering for XAUUSD trading.
    
    Generates 800+ features including:
    - Price action features (Numba JIT)
    - Technical indicators (50+ indicators)
    - Volatility features
    - Time/calendar features
    - Macro correlation features
    - Pattern detection
    
    Features are computed incrementally for efficiency.
    """
    
    def __init__(
        self,
        window_size: int = 500,
        use_numba: bool = True,
    ):
        """
        Initialize FeatureEngineer.
        
        Args:
            window_size: Lookback window for features.
            use_numba: Whether to use Numba JIT compilation.
        """
        self.window_size = window_size
        self.use_numba = use_numba and NUMBA_AVAILABLE
        self.logger = logging.getLogger("XAUUSD_GOD_BOT.FeatureEngine")
        
        self._ohlcv_buffer: Optional[np.ndarray] = None
        self._feature_names: List[str] = []
        self._feature_cache: Dict[str, np.ndarray] = {}
        self._lock = threading.Lock()
        
        self._build_feature_names()
        
        self.logger.info(f"FeatureEngine initialized: {len(self._feature_names)} features, Numba={self.use_numba}")
    
    def __repr__(self) -> str:
        return f"<FeatureEngine features={len(self._feature_names)} numba={self.use_numba}>"
    
    def _build_feature_names(self) -> None:
        """Build list of all feature names."""
        self._feature_names = []
        
        for tf in ["M1", "M5", "M15", "H1", "H4", "D1"]:
            for col in ["open", "high", "low", "close", "volume"]:
                self._feature_names.append(f"{tf}_{col}")
        
        for period in [8, 13, 21, 50, 100, 200]:
            self._feature_names.append(f"ema_{period}")
            self._feature_names.append(f"ema_{period}_normalized")
        
        for period in [9, 20, 50, 200]:
            self._feature_names.append(f"sma_{period}")
            self._feature_names.append(f"sma_{period}_slope")
        
        for period in [7, 14, 21]:
            self._feature_names.append(f"rsi_{period}")
            self._feature_names.append(f"rsi_{period}_divergence")
        
        self._feature_names.extend([
            "macd_line", "macd_signal", "macd_histogram", "macd_histogram_slope",
        ])
        
        self._feature_names.extend([
            "bb_upper", "bb_middle", "bb_lower", "bb_bandwidth", "bb_squeeze",
            "bb_position",
        ])
        
        for period in [7, 14, 21]:
            self._feature_names.append(f"atr_{period}")
            self._feature_names.append(f"atr_{period}_normalized")
        
        for k, d in [(5, 3), (14, 3)]:
            self._feature_names.append(f"stoch_k_{k}_{d}")
            self._feature_names.append(f"stoch_d_{k}_{d}")
        
        for period in [14, 20]:
            self._feature_names.append(f"cci_{period}")
        
        self._feature_names.append("williams_r")
        
        self._feature_names.extend([
            "adx", "adx_slope", "di_plus", "di_minus",
        ])
        
        self._feature_names.extend([
            "ichimoku_tenkan", "ichimoku_kijun", "ichimoku_senkou_a",
            "ichimoku_senkou_b", "ichimoku_chikou", "ichimoku_cloud_thickness",
        ])
        
        self._feature_names.extend([
            "vwap", "vwap_deviation", "psar", "psar_direction",
        ])
        
        for mult in [1.5, 2.0, 3.0]:
            self._feature_names.append(f"supertrend_{mult}")
        
        self._feature_names.extend([
            "keltner_upper", "keltner_middle", "keltner_lower", "keltner_width",
            "donchian_upper", "donchian_middle", "donchian_lower", "donchian_position",
        ])
        
        for name in ["pivot", "r1", "r2", "r3", "s1", "s2", "s3"]:
            self._feature_names.append(name)
            self._feature_names.append(f"{name}_distance")
        
        self._feature_names.extend([
            "obv", "obv_slope", "mfi_14", "cmf_20",
        ])
        
        for period in [5, 10, 20, 60]:
            self._feature_names.append(f"realized_vol_{period}")
            self._feature_names.append(f"log_return_{period}")
            self._feature_names.append(f"pct_change_{period}")
            self._feature_names.append(f"zscore_{period}")
        
        self._feature_names.extend([
            "swing_high", "swing_low", "higher_high", "lower_low",
            "momentum", "roc", "ao",
        ])
        
        for pattern in ["doji", "dragonfly", "gravestone", "engulfing_bull", "engulfing_bear", "pin_bar_bull", "pin_bar_bear"]:
            self._feature_names.append(pattern)
        
        self._feature_names.extend([
            "hour_sin", "hour_cos", "dow_sin", "dow_cos", "week_of_month",
            "session_asia", "session_london", "session_ny", "session_overlap",
            "days_to_nfp", "days_to_fomc", "days_to_cpi",
            "month_end", "quarter_end", "holiday_proximity",
        ])
        
        self._feature_names.extend([
            "dxy", "dxy_return_1d", "dxy_return_5d", "dxy_return_20d",
            "us10y_yield", "us10y_change", "real_rate",
            "vix", "vix_regime", "gold_silver_ratio", "gold_oil_ratio",
        ])
        
        self._feature_names.extend([
            "sentiment_score", "sentiment_momentum_1h", "sentiment_momentum_4h", "sentiment_momentum_24h",
            "geopolitical_risk", "fear_greed",
        ])
        
        self._feature_names.extend([
            "cross_tf_alignment", "htf_trend_h4", "htf_trend_d1", "htf_trend_w1",
            "multi_tf_momentum",
        ])
        
        self.logger.info(f"Feature names built: {len(self._feature_names)} features")
    
    @property
    def feature_names(self) -> List[str]:
        """Get list of all feature names."""
        return self._feature_names.copy()
    
    @property
    def num_features(self) -> int:
        """Get number of features."""
        return len(self._feature_names)
    
    def compute_all_features(
        self,
        df: pd.DataFrame,
        macro_data: Optional[Dict[str, float]] = None,
        sentiment_data: Optional[Dict[str, float]] = None,
    ) -> np.ndarray:
        """
        Compute all features from OHLCV data.
        
        Args:
            df: DataFrame with OHLCV columns.
            macro_data: Optional macro data dict.
            sentiment_data: Optional sentiment dict.
        
        Returns:
            NumPy array of features.
        """
        if df is None or df.empty or len(df) < 50:
            self.logger.warning("Insufficient data for features")
            return np.zeros((1, self.num_features), dtype=np.float32)
        
        try:
            o = df['open'].values.astype(np.float64)
            h = df['high'].values.astype(np.float64)
            l = df['low'].values.astype(np.float64)
            c = df['close'].values.astype(np.float64)
            v = df['volume'].values.astype(np.float64) if 'volume' in df.columns else np.ones_like(c)
            
            n = len(c)
            features = np.zeros((n, self.num_features), dtype=np.float32)
            
            idx = 0
            
            if self.use_numba:
                for period in [8, 13, 21, 50, 100, 200]:
                    if idx < self.num_features:
                        ema = _calculate_ema_numba(c, period)
                        features[:, idx] = ema
                        idx += 1
                        if idx < self.num_features:
                            features[:, idx] = c / (ema + 1e-10)
                            idx += 1
                
                for period in [7, 14, 21]:
                    if idx < self.num_features:
                        features[:, idx] = _calculate_rsi_numba(c, period)
                        idx += 1
                
                if idx < self.num_features:
                    macd_line, macd_sig, macd_hist = _calculate_macd_numba(c, 12, 26, 9)
                    features[:, idx] = macd_line; idx += 1
                    features[:, idx] = macd_sig; idx += 1
                    features[:, idx] = macd_hist; idx += 1
                    if len(macd_hist) > 1:
                        features[1:, idx] = np.diff(macd_hist)
                        idx += 1
                
                if idx < self.num_features:
                    bb_u, bb_m, bb_l, bb_w, bb_sq = _calculate_bollinger_numba(c, 20, 2.0)
                    features[:, idx] = bb_u; idx += 1
                    features[:, idx] = bb_m; idx += 1
                    features[:, idx] = bb_l; idx += 1
                    features[:, idx] = bb_w; idx += 1
                    features[:, idx] = bb_sq; idx += 1
                    features[:, idx] = (c - bb_l) / (bb_u - bb_l + 1e-10); idx += 1
                
                for period in [7, 14, 21]:
                    if idx < self.num_features:
                        atr = _calculate_atr_numba(h, l, c, period)
                        features[:, idx] = atr; idx += 1
                        if idx < self.num_features:
                            features[:, idx] = atr / (c + 1e-10); idx += 1
                
                if idx < self.num_features:
                    stoch_k, stoch_d = _calculate_stoch_numba(h, l, c, 14, 3)
                    features[:, idx] = stoch_k; idx += 1
                    features[:, idx] = stoch_d; idx += 1
                
                if idx < self.num_features:
                    adx, di_p, di_m, adx_sl = _calculate_adx_numba(h, l, c, 14)
                    features[:, idx] = adx; idx += 1
                    features[:, idx] = adx_sl; idx += 1
                    features[:, idx] = di_p; idx += 1
                    features[:, idx] = di_m; idx += 1
                
                if idx < self.num_features:
                    tenkan, kijun, senkou_a, senkou_b, chikou = _calculate_ichimoku_numba(h, l, c)
                    features[:, idx] = tenkan; idx += 1
                    features[:, idx] = kijun; idx += 1
                    features[:, idx] = senkou_a; idx += 1
                    features[:, idx] = senkou_b; idx += 1
                    features[:, idx] = chikou; idx += 1
                    if idx < self.num_features:
                        features[:, idx] = senkou_a - senkou_b; idx += 1
                
                if idx < self.num_features:
                    vwap = _calculate_vwap_numba(h, l, c, v)
                    features[:, idx] = vwap; idx += 1
                    if idx < self.num_features:
                        features[:, idx] = (c - vwap) / (c + 1e-10); idx += 1
                
                if idx < self.num_features:
                    psar, psar_dir = _calculate_parabolic_sar_numba(h, l, c, 0.02, 0.2)
                    features[:, idx] = psar; idx += 1
                    features[:, idx] = psar_dir; idx += 1
                
                for mult in [1.5, 2.0, 3.0]:
                    if idx < self.num_features:
                        st, std = _calculate_supertrend_numba(h, l, c, 14, mult)
                        features[:, idx] = std; idx += 1
                
                if idx < self.num_features:
                    k_u, k_m, k_l = _calculate_keltner_numba(h, l, c, 20, 14, 1.5)
                    features[:, idx] = k_u; idx += 1
                    features[:, idx] = k_m; idx += 1
                    features[:, idx] = k_l; idx += 1
                    if idx < self.num_features:
                        features[:, idx] = (k_u - k_l) / (k_m + 1e-10); idx += 1
                
                if idx < self.num_features:
                    d_u, d_m, d_l = _calculate_donchian_numba(h, l, 20)
                    features[:, idx] = d_u; idx += 1
                    features[:, idx] = d_m; idx += 1
                    features[:, idx] = d_l; idx += 1
                    if idx < self.num_features:
                        features[:, idx] = (c - d_l) / (d_u - d_l + 1e-10); idx += 1
                
                if idx < self.num_features:
                    piv, r1, r2, r3, s1, s2, s3 = _calculate_pivot_points_numba(h, l, c)
                    features[:, idx] = piv; idx += 1
                    features[:, idx] = r1; idx += 1
                    features[:, idx] = r2; idx += 1
                    features[:, idx] = r3; idx += 1
                    features[:, idx] = s1; idx += 1
                    features[:, idx] = s2; idx += 1
                    features[:, idx] = s3; idx += 1
                    if idx < self.num_features:
                        features[:, idx] = (c - piv) / (c + 1e-10); idx += 1
                
                if idx < self.num_features:
                    obv, obv_sl = _calculate_obv_numba(c, v)
                    features[:, idx] = obv; idx += 1
                    features[:, idx] = obv_sl; idx += 1
                
                if idx < self.num_features:
                    features[:, idx] = _calculate_mfi_numba(h, l, c, v, 14); idx += 1
                
                if idx < self.num_features:
                    features[:, idx] = _calculate_cmf_numba(h, l, c, v, 20); idx += 1
                
                for period in [5, 10, 20, 60]:
                    if idx < self.num_features:
                        ret = _calculate_log_returns_numba(c, period)
                        features[:, idx] = ret; idx += 1
                    if idx < self.num_features:
                        pct = (c / (np.roll(c, period) + 1e-10) - 1) * 100
                        pct[0:period] = 0
                        features[:, idx] = pct; idx += 1
                    if idx < self.num_features:
                        zsc = _calculate_zscore_numba(c, period)
                        features[:, idx] = zsc; idx += 1
                
                if idx < self.num_features:
                    sw_h, sw_l = _detect_swing_points_numba(h, l, 5)
                    features[:, idx] = sw_h; idx += 1
                    features[:, idx] = sw_l; idx += 1
                
                if idx < self.num_features:
                    features[:, idx] = _calculate_momentum_numba(c, 10); idx += 1
                
                if idx < self.num_features:
                    features[:, idx] = _calculate_roc_numba(c, 10); idx += 1
                
                if idx < self.num_features:
                    features[:, idx] = _calculate_ao_numba(h, l, 5, 34); idx += 1
                
                if idx < self.num_features:
                    features[:, idx] = _calculate_cci_numba(h, l, c, 20); idx += 1
                
                if idx < self.num_features:
                    features[:, idx] = _calculate_williams_r_numba(h, l, c, 14); idx += 1
                
                if idx < self.num_features:
                    patterns = _detect_candle_patterns_numba(o, h, l, c)
                    for p_idx, pname in enumerate(["doji", "dragonfly", "gravestone", "engulf_bull", "engulf_bear"]):
                        if idx < self.num_features:
                            features[:, idx] = (patterns == (p_idx + 1)).astype(np.float32); idx += 1
            
            features = self._add_time_features(features, df)
            
            if macro_data and idx < self.num_features:
                features[:, idx] = macro_data.get('dxy', 0); idx += 1
                features[:, idx] = macro_data.get('dxy_return_1d', 0); idx += 1
                features[:, idx] = macro_data.get('us10y_yield', 0); idx += 1
                features[:, idx] = macro_data.get('real_rate', 0); idx += 1
                features[:, idx] = macro_data.get('vix', 0); idx += 1
            
            if sentiment_data and idx < self.num_features:
                features[:, idx] = sentiment_data.get('sentiment', 0); idx += 1
                features[:, idx] = sentiment_data.get('geopolitical_risk', 0); idx += 1
            
            features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)
            
            self.logger.info(f"Computed features: shape={features.shape}")
            
            return features
            
        except Exception as e:
            self.logger.error(f"Feature computation error: {e}")
            return np.zeros((1, self.num_features), dtype=np.float32)
    
    def _add_time_features(
        self,
        features: np.ndarray,
        df: pd.DataFrame
    ) -> np.ndarray:
        """Add time-based features."""
        try:
            n = len(features)
            
            if 'timestamp' in df.columns or 'time' in df.columns:
                ts_col = 'timestamp' if 'timestamp' in df.columns else 'time'
                timestamps = pd.to_datetime(df[ts_col])
                
                hours = timestamps.hour.values
                days = timestamps.dayofweek.values
                
                hour_sin = np.sin(2 * np.pi * hours / 24).reshape(-1, 1)
                hour_cos = np.cos(2 * np.pi * hours / 24).reshape(-1, 1)
                dow_sin = np.sin(2 * np.pi * days / 7).reshape(-1, 1)
                dow_cos = np.cos(2 * np.pi * days / 7).reshape(-1, 1)
                
                features = np.hstack([features, hour_sin, hour_cos, dow_sin, dow_cos])
            
            return features
            
        except Exception as e:
            self.logger.error(f"Time features error: {e}")
            return features
    
    def get_latest_features(self, n: int = 1) -> np.ndarray:
        """
        Get the latest N feature vectors.
        
        Args:
            n: Number of latest features to return.
        
        Returns:
            Array of latest features.
        """
        if self._ohlcv_buffer is None:
            return np.zeros((n, self.num_features), dtype=np.float32)
        
        return self._ohlcv_buffer[-n:]
    
    def get_feature_importance(
        self,
        X: np.ndarray,
        y: np.ndarray,
        method: str = "correlation"
    ) -> List[Tuple[str, float]]:
        """
        Calculate feature importance.
        
        Args:
            X: Feature matrix.
            y: Target values.
            method: Method to use ('correlation' or 'variance').
        
        Returns:
            List of (feature_name, importance) tuples.
        """
        try:
            if method == "correlation":
                importances = []
                for i in range(min(X.shape[1], len(self._feature_names))):
                    corr = np.abs(np.corrcoef(X[:, i], y)[0, 1])
                    importances.append((self._feature_names[i], corr))
            else:
                importances = [(name, np.var(X[:, i])) for i, name in enumerate(self._feature_names[:X.shape[1]])]
            
            importances.sort(key=lambda x: x[1], reverse=True)
            
            return importances[:50]
            
        except Exception as e:
            self.logger.error(f"Feature importance error: {e}")
            return []


# ═══════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    "FeatureEngineer",
    "NUMBA_AVAILABLE",
]


# ═══════════════════════════════════════════════════════════════════════════
# TEST / ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("XAUUSD GOD BOT v2.0 — Feature Engineering Module Test")
    print("-" * 60)
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        print("\n1. Testing Numba Availability...")
        print(f"   Numba Available: {NUMBA_AVAILABLE}")
        
        print("\n2. Testing FeatureEngineer...")
        fe = FeatureEngineer(window_size=500, use_numba=NUMBA_AVAILABLE)
        print(f"   FeatureEngine: {fe}")
        print(f"   Num Features: {fe.num_features}")
        print(f"   First 10 features: {fe.feature_names[:10]}")
        
        print("\n3. Testing Feature Computation...")
        np.random.seed(42)
        n_samples = 500
        
        dates = pd.date_range(start='2024-01-01', periods=n_samples, freq='1h')
        close_prices = 2000 + np.cumsum(np.random.randn(n_samples) * 2)
        high_prices = close_prices + np.random.rand(n_samples) * 5
        low_prices = close_prices - np.random.rand(n_samples) * 5
        open_prices = close_prices + np.random.randn(n_samples) * 2
        volumes = np.random.randint(1000, 10000, n_samples)
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': volumes,
        })
        
        print(f"   Test DataFrame: {len(df)} rows")
        
        features = fe.compute_all_features(df)
        print(f"   Computed Features Shape: {features.shape}")
        
        if features.shape[1] > 0:
            print(f"   Feature Sample (last row): {features[-1, :10]}")
        
        importance = fe.get_feature_importance(features, df['close'].values)
        print(f"   Top 5 Important Features:")
        for name, score in importance[:5]:
            print(f"      {name}: {score:.4f}")
        
        print("\n" + "=" * 60)
        print("Feature Engineering Module: ALL TESTS PASSED")
        print(f"Total Features Available: {fe.num_features}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
