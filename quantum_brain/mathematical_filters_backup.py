"""
Quantum Mathematical Filters - 100+ Live Tick Filters
Stage 1 of the Quantum Intelligence Matrix
Ultra-low-latency mathematical transforms for XAUUSD micro-structural analysis
"""

import math
import time
from collections import deque
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from enum import Enum, auto
import numpy as np


# ============================================================================
# CORE DATA STRUCTURES
# ============================================================================

@dataclass
class QuantumMetrics:
    """Container for all quantum mathematical filter outputs"""
    timestamp: float = 0.0

    # Volatility Metrics (15+)
    realized_volatility: float = 0.0
    parkinson_volatility: float = 0.0
    garman_klass_volatility: float = 0.0
    rogers_satchell_volatility: float = 0.0
    yang_zhang_volatility: float = 0.0
    ewma_volatility: float = 0.0
    garch_volatility: float = 0.0
    range_based_vol: float = 0.0
    intraday_vol_ratio: float = 0.0
    tick_volatility: float = 0.0
    realized_kurtosis: float = 0.0
    realized_skewness: float = 0.0
    vol_of_vol: float = 0.0
    vol_regime: float = 0.0
    rough_volatility: float = 0.0

    # Velocity Metrics (15+)
    price_velocity: float = 0.0
    bid_velocity: float = 0.0
    ask_velocity: float = 0.0
    velocity_acceleration: float = 0.0
    jerk: float = 0.0
    velocity_mean_reversion: float = 0.0
    velocity_momentum: float = 0.0
    velocity_entropy: float = 0.0
    bid_ask_spread_velocity: float = 0.0
    micro_price_velocity: float = 0.0
    velocity_kalman: float = 0.0
    velocity_regression: float = 0.0
    velocity_wavelet: float = 0.0
    velocity_autocorrelation: float = 0.0
    velocity_trend: float = 0.0

    # Momentum Metrics (15+)
    rsi_7: float = 0.0
    rsi_14: float = 0.0
    rsi_21: float = 0.0
    macd_signal: float = 0.0
    stochastic_k: float = 0.0
    stochastic_d: float = 0.0
    cci: float = 0.0
    williams_r: float = 0.0
    rate_of_change: float = 0.0
    momentum_composite: float = 0.0
    z_score: float = 0.0
    percentile_rank: float = 0.0
    momentum_mean_reversion: float = 0.0
    momentum_breakout: float = 0.0
    hull_momentum: float = 0.0

    # Non-Commutative Metrics (10+)
    nc_position: float = 0.0
    nc_momentum: float = 0.0
    nc_volatility: float = 0.0
    nc_spread: float = 0.0
    nc_skew: float = 0.0
    nc_kurtosis: float = 0.0
    nc_entropy: float = 0.0
    nc_complexity: float = 0.0
    nc_order: float = 0.0
    nc_chaos: float = 0.0

    # Order Book Metrics (15+)
    bid_ask_spread: float = 0.0
    mid_price: float = 0.0
    micro_price: float = 0.0
    bid_depth_imbalance: float = 0.0
    volume_weighted_mid: float = 0.0
    price_impact: float = 0.0
    kyle_lambda: float = 0.0
    amihud_illiquidity: float = 0.0
    order_flow_imbalance: float = 0.0
    trade_intensity: float = 0.0
    volume_surprise: float = 0.0
    tick_direction: float = 0.0
    lee_ready_class: float = 0.0
    bid_ask_ratio: float = 0.0
    book_pressure: float = 0.0

    # Temporal Metrics (10+)
    time_of_day: float = 0.0
    session_phase: float = 0.0
    seconds_since_epoch: float = 0.0
    tick_frequency: float = 0.0
    time_regularity: float = 0.0
    temporal_momentum: float = 0.0
    time_weighted_return: float = 0.0
    session_volatility_ratio: float = 0.0
    time_dilation: float = 0.0
    temporal_entropy: float = 0.0

    # Composite Signals (20+)
    trend_signal: float = 0.0
    mean_reversion_signal: float = 0.0
    breakout_signal: float = 0.0
    volatility_signal: float = 0.0
    momentum_composite_signal: float = 0.0
    order_flow_signal: float = 0.0
    time_signal: float = 0.0
    regime_signal: float = 0.0
    risk_adjusted_signal: float = 0.0
    hurst_exponent: float = 0.0
    fractal_dimension: float = 0.0
    lyapunov_exponent: float = 0.0
    entropy_measures: float = 0.0
    information_ratio: float = 0.0
    sharpe_signal: float = 0.0
    sortino_signal: float = 0.0
    calmar_signal: float = 0.0
    omega_ratio: float = 0.0
    tail_risk: float = 0.0
    cohomology_class: float = 0.0


# ============================================================================
# QUANTUM MATHEMATICAL ENGINE
# ============================================================================

class QuantumMathEngine:
    """
    100+ Quantum Mathematical Filters for XAUUSD
    Processes raw tick streams into comprehensive mathematical metrics
    """

    def __init__(self, lookback: int = 500, price_scale: float = 10000.0):
        self._lookback = lookback
        self._price_scale = price_scale
        self._bid_history = deque(maxlen=lookback)
        self._ask_history = deque(maxlen=lookback)
        self._mid_history = deque(maxlen=lookback)
        self._volume_history = deque(maxlen=lookback)
        self._timestamp_history = deque(maxlen=lookback)
        self._return_history = deque(maxlen=lookback)
        self._tick_count = 0
        self._start_time = time.time()
        self._last_mid = 0.0
        self._last_bid = 0.0
        self._last_ask = 0.0
        self._last_timestamp = 0.0
        self._ewma_vol = 0.0
        self._ewma_velocity = 0.0
        self._ewma_momentum = 0.0
        self._alpha_ewma = 0.1
        self._vol_regime = 0.0
        self._mom_regime = 0.0

    def process_tick(self, timestamp: float, bid: float, ask: float, volume: float):
        """Process single tick through all 100+ mathematical filters"""
        self._tick_count += 1
        mid = (bid + ask) / 2.0
        metrics = QuantumMetrics(timestamp=timestamp)

        # Update history buffers
        self._bid_history.append(bid)
        self._ask_history.append(ask)
        self._mid_history.append(mid)
        self._volume_history.append(volume)
        self._timestamp_history.append(timestamp)

        # Calculate return if we have history
        if self._last_mid > 0 and len(self._mid_history) >= 2:
            ret = (mid - self._last_mid) / self._last_mid
            self._return_history.append(ret)

        # Update running stats
        self._last_mid = mid
        self._last_bid = bid
        self._last_ask = ask
        self._last_timestamp = timestamp

        # Execute all filter stages
        self._compute_volatility_metrics(metrics, mid, bid, ask)
        self._compute_velocity_metrics(metrics, timestamp, mid, bid, ask)
        self._compute_momentum_metrics(metrics, mid)
        self._compute_non_commutative_metrics(metrics, mid, bid, ask)
        self._compute_order_book_metrics(metrics, bid, ask, volume)
        self._compute_temporal_metrics(metrics)
        self._compute_composite_signals(metrics)

        return metrics

    def _compute_volatility_metrics(self, m: QuantumMetrics, mid: float,
                                     bid: float, ask: float):
        """Compute all volatility metrics"""
        returns = list(self._return_history)
        n = len(returns)
        if n < 5:
            return

        # 1. Realized Volatility
        arr = np.array(returns[-min(n, 100):])
        m.realized_volatility = float(np.std(arr) * math.sqrt(252 * 28800))

        # 2. Parkinson Volatility
        if len(self._mid_history) >= 2:
            mids = list(self._mid_history)
            high_low = max(mids[-min(n, 100):]) - min(mids[-min(n, 100):])
            m.parkinson_volatility = float(high_low / (2.0 * math.sqrt(2.0 / math.pi)))

        # 3. Garman-Klass Volatility
        mids_arr = np.array(list(self._mid_history)[-min(n, 100):])
        if len(mids_arr) > 1:
            log_ret = np.diff(np.log(mids_arr))
            m.garman_klass_volatility = float(np.std(log_ret) * math.sqrt(252 * 28800))

        # 4. Rogers-Satchell Volatility
        if n >= 2:
            rs_sum = 0.0
            for i in range(max(0, n-50), n):
                h = max(self._mid_history) if self._mid_history else mid
                l = min(self._mid_history) if self._mid_history else mid
                c = returns[i]
                o = returns[i-1] if i > 0 else 0
                rs_sum += (h - c) * (h - o) + (l - c) * (l - o)
            m.rogers_satchell_volatility = float(math.sqrt(rs_sum / min(n, 50)))

        # 5. Yang-Zhang Volatility
        m.yang_zhang_volatility = float(
            0.34 * m.rogers_satchell_volatility +
            0.33 * m.garman_klass_volatility +
            0.33 * m.realized_volatility
        ) if m.realized_volatility > 0 else 0.0

        # 6. EWMA Volatility
        self._ewma_vol = self._alpha_ewma * abs(returns[-1]) + (1 - self._alpha_ewma) * self._ewma_vol
        m.ewma_volatility = float(self._ewma_vol * math.sqrt(252 * 28800))

        # 7. GARCH-like Volatility
        alpha, beta = 0.1, 0.85
        garch_var = alpha * returns[-1]**2 + beta * m.ewma_volatility**2 / (252 * 28800)
        m.garch_volatility = float(math.sqrt(garch_var * 252 * 28800))

        # 8. Range-based Volatility
        if len(self._mid_history) >= 5:
            highs = list(self._mid_history)[-5:]
            m.range_based_vol = float((max(highs) - min(highs)) / mid)

        # 9. Intraday Vol Ratio
        m.intraday_vol_ratio = float(m.realized_volatility / max(m.ewma_volatility, 1e-10))

        # 10. Tick Volatility
        if len(self._mid_history) >= 10:
            ticks = list(self._mid_history)[-10:]
            m.tick_volatility = float(np.std(np.diff(ticks)) / mid)

        # 11. Realized Kurtosis
        if n >= 20:
            arr_20 = np.array(returns[-20:])
            mean_r = np.mean(arr_20)
            std_r = np.std(arr_20)
            if std_r > 0:
                m.realized_kurtosis = float(np.mean(((arr_20 - mean_r) / std_r) ** 4))

        # 12. Realized Skewness
        if n >= 20:
            arr_20 = np.array(returns[-20:])
            mean_r = np.mean(arr_20)
            std_r = np.std(arr_20)
            if std_r > 0:
                m.realized_skewness = float(np.mean(((arr_20 - mean_r) / std_r) ** 3))

        # 13. Vol of Vol
        if n >= 50:
            vol_window = []
            for i in range(max(0, n-50), n-10, 10):
                vol_window.append(np.std(returns[i:i+10]))
            if vol_window:
                m.vol_of_vol = float(np.std(vol_window))

        # 14. Vol Regime
        if m.realized_volatility > 0:
            self._vol_regime = 0.9 * self._vol_regime + 0.1 * (m.realized_volatility / max(m.ewma_volatility, 1e-10))
            m.vol_regime = float(self._vol_regime)

        # 15. Rough Volatility (simplified)
        if n >= 30:
            m.rough_volatility = float(
                np.mean([abs(returns[i] - returns[i-1]) for i in range(max(1, n-30), n)]) * math.sqrt(252 * 28800)
            )

    def _estimate_hurst(self, returns_list: list) -> float:
        """Estimate Hurst exponent using R/S analysis"""
        n = len(returns_list)
        if n < 20:
            return 0.5
        max_k = min(n // 2, 100)
        rs_list = []
        for k in range(10, max_k + 1, 5):
            rs_vals = []
            for start in range(0, n - k, k):
                subset = returns_list[start:start + k]
                mean_r = np.mean(subset)
                cumdev = np.cumsum(subset - mean_r)
                R = max(cumdev) - min(cumdev)
                S = np.std(subset)
                if S > 0:
                    rs_vals.append(R / S)
            if rs_vals:
                rs_list.append((math.log(k), math.log(np.mean(rs_vals))))
        if len(rs_list) < 3:
            return 0.5
        x = np.array([r[0] for r in rs_list])
        y = np.array([r[1] for r in rs_list])
        if np.std(x) > 0:
            slope = np.polyfit(x, y, 1)[0]
            return float(np.clip(slope, 0.0, 1.0))
        return 0.5

    def _compute_velocity_metrics(self, m: QuantumMetrics, timestamp: float,
                                   mid: float, bid: float, ask: float):
        """Compute all velocity metrics"""
        if self._last_timestamp <= 0 or self._last_mid <= 0:
            return

        dt = timestamp - self._last_timestamp
        if dt <= 0:
            return

        # 1. Price Velocity
        velocity = (mid - self._last_mid) / dt
        m.price_velocity = float(velocity)

        # 2. Bid Velocity
        m.bid_velocity = float((bid - self._last_bid) / dt)

        # 3. Ask Velocity
        m.ask_velocity = float((ask - self._last_ask) / dt)

        # 4. Velocity Acceleration
        self._ewma_velocity = 0.5 * velocity + 0.5 * self._ewma_velocity
        m.velocity_acceleration = float((velocity - self._ewma_velocity) / max(dt, 1e-10))

        # 5. Jerk (acceleration change)
        m.jerk = float(m.velocity_acceleration / max(dt, 1e-10))

        # 6. Velocity Mean Reversion
        if len(self._mid_history) >= 20:
            vels = []
            mids = list(self._mid_history)
            for i in range(1, min(20, len(mids))):
                vels.append((mids[-i] - mids[-i-1]) / max(dt, 1e-10))
            if vels:
                m.velocity_mean_reversion = float(-np.mean(vels) * 0.1)

        # 7. Velocity Momentum
        m.velocity_momentum = float(np.sign(m.price_velocity) * abs(m.velocity_acceleration))

        # 8. Velocity Entropy
        m.velocity_entropy = float(abs(m.price_velocity) * math.log(1 + abs(m.price_velocity)))

        # 9. Bid-Ask Spread Velocity
        if self._last_bid > 0 and self._last_ask > 0:
            spread_now = ask - bid
            spread_prev = self._last_ask - self._last_bid
            m.bid_ask_spread_velocity = float((spread_now - spread_prev) / dt)

        # 10. Micro Price Velocity
        depth_imbalance = (bid - mid) / max(ask - mid, 1e-10) if ask > mid else 0.5
        micro_price = bid + (ask - bid) * depth_imbalance
        m.micro_price_velocity = float((micro_price - self._last_mid) / dt)

        # 11. Velocity Kalman (simplified)
        kalman_gain = 0.3
        predicted = self._ewma_velocity
        m.velocity_kalman = float(predicted + kalman_gain * (velocity - predicted))

        # 12. Velocity Regression
        if len(self._mid_history) >= 10:
            recent_mids = list(self._mid_history)[-10:]
            x = np.arange(len(recent_mids))
            if len(x) > 1:
                slope = np.polyfit(x, recent_mids, 1)[0]
                m.velocity_regression = float(slope)

        # 13. Velocity Wavelet (simplified)
        if len(self._mid_history) >= 16:
            recent = np.array(list(self._mid_history)[-16:])
            coeffs = np.abs(np.fft.fft(recent - np.mean(recent)))[:8]
            m.velocity_wavelet = float(np.sum(coeffs[1:4]) / max(np.sum(coeffs), 1e-10))

        # 14. Velocity Autocorrelation
        if len(self._return_history) >= 20:
            rets = list(self._return_history)[-20:]
            if np.std(rets) > 0:
                arr = np.array(rets)
                autocorr = np.corrcoef(arr[:-1], arr[1:])[0, 1]
                m.velocity_autocorrelation = float(autocorr if not np.isnan(autocorr) else 0.0)

        # 15. Velocity Trend
        if len(self._mid_history) >= 5:
            recent = list(self._mid_history)[-5:]
            m.velocity_trend = float((recent[-1] - recent[0]) / max(recent[0], 1e-10))

    def _compute_momentum_metrics(self, m: QuantumMetrics, mid: float):
        """Compute all momentum metrics"""
        returns = list(self._return_history)
        n = len(returns)
        if n < 7:
            return

        # 1-3. RSI variants
        for period, name in [(7, 'rsi_7'), (14, 'rsi_14'), (21, 'rsi_21')]:
            if n >= period:
                gains = [max(r, 0) for r in returns[-period:]]
                losses = [abs(min(r, 0)) for r in returns[-period:]]
                avg_gain = np.mean(gains)
                avg_loss = np.mean(losses)
                rs = avg_gain / max(avg_loss, 1e-10)
                setattr(m, name, float(100 - 100 / (1 + rs)))

        # 4. MACD Signal
        if n >= 26:
            fast = np.mean(returns[-12:])
            slow = np.mean(returns[-26:])
            m.macd_signal = float(np.sign(fast - slow) * min(abs(fast - slow) * 100, 1.0))

        # 5-6. Stochastic
        if n >= 14:
            period_returns = returns[-14:]
            low = min(period_returns)
            high = max(period_returns)
            rng = high - low
            if rng > 0:
                m.stochastic_k = float((returns[-1] - low) / rng * 100)
                m.stochastic_d = float(np.mean([m.stochastic_k]))

        # 7. CCI
        if n >= 20:
            tp = np.mean(returns[-20:])
            mad = np.mean(np.abs(np.array(returns[-20:]) - tp))
            if mad > 0:
                m.cci = float((returns[-1] - tp) / (0.015 * mad))

        # 8. Williams %R
        if n >= 14:
            period_returns = returns[-14:]
            high = max(period_returns)
            low = min(period_returns)
            rng = high - low
            if rng > 0:
                m.williams_r = float((high - returns[-1]) / rng * -100)

        # 9. Rate of Change
        if n >= 10:
            m.rate_of_change = float((returns[-1] - returns[-10]) / max(abs(returns[-10]), 1e-10) * 100)

        # 10. Momentum Composite
        m.momentum_composite = float(
            (m.rsi_14 - 50) / 50 * 0.3 +
            m.macd_signal * 0.3 +
            (m.stochastic_k - 50) / 50 * 0.2 +
            m.rate_of_change / 100 * 0.2
        )

        # 11. Z-Score
        if n >= 20:
            arr = np.array(returns[-20:])
            mean_r = np.mean(arr)
            std_r = np.std(arr)
            if std_r > 0:
                m.z_score = float((returns[-1] - mean_r) / std_r)

        # 12. Percentile Rank
        if n >= 20:
            arr = np.array(returns[-20:])
            m.percentile_rank = float(np.sum(arr < returns[-1]) / len(arr) * 100)

        # 13. Momentum Mean Reversion
        m.momentum_mean_reversion = float(-m.z_score * 0.3)

        # 14. Momentum Breakout
        if n >= 20:
            recent = returns[-20:]
            m.momentum_breakout = float(1.0 if returns[-1] > max(recent) else (-1.0 if returns[-1] < min(recent) else 0.0))

        # 15. Hull Moving Average Momentum
        if n >= 20:
            hma_10 = np.mean(returns[-10:])
            hma_20 = np.mean(returns[-20:])
            hma_sqrt = np.mean(returns[-int(math.sqrt(20)):])
            hull = 2 * hma_10 - hma_20
            m.hull_momentum = float(hull - hma_sqrt)

    def _compute_non_commutative_metrics(self, m: QuantumMetrics, mid: float,
                                          bid: float, ask: float):
        """Compute non-commutative geometry metrics for order book dynamics"""
        # 1. NC Position (theta parameter)
        m.nc_position = float((mid - bid) / max(ask - bid, 1e-10))

        # 2. NC Momentum
        returns = list(self._return_history)
        n = len(returns)
        if n >= 5:
            m.nc_momentum = float(np.mean(returns[-5:]))

        # 3. NC Volatility
        if n >= 10:
            m.nc_volatility = float(np.std(returns[-10:]))

        # 4. NC Spread
        m.nc_spread = float((ask - bid) / mid)

        # 5. NC Skew
        if n >= 10:
            arr = np.array(returns[-10:])
            m.nc_skew = float(np.mean(((arr - np.mean(arr)) / max(np.std(arr), 1e-10)) ** 3))

        # 6. NC Kurtosis
        if n >= 10:
            arr = np.array(returns[-10:])
            m.nc_kurtosis = float(np.mean(((arr - np.mean(arr)) / max(np.std(arr), 1e-10)) ** 4) - 3)

        # 7. NC Entropy
        if n >= 10:
            arr = np.array(returns[-10:])
            hist, _ = np.histogram(arr, bins=5)
            probs = hist / max(np.sum(hist), 1)
            probs = probs[probs > 0]
            m.nc_entropy = float(-np.sum(probs * np.log2(probs)))

        # 8. NC Complexity
        m.nc_complexity = float(abs(m.nc_skew) + abs(m.nc_kurtosis) + m.nc_entropy)

        # 9. NC Order
        if n >= 10:
            arr = np.array(returns[-10:])
            m.nc_order = float(1.0 - min(1.0, m.nc_entropy / math.log2(5)))

        # 10. NC Chaos
        m.nc_chaos = float(m.nc_volatility * m.nc_complexity)

    def _compute_order_book_metrics(self, m: QuantumMetrics, bid: float,
                                     ask: float, volume: float):
        """Compute order book and microstructure metrics"""
        # 1. Bid-Ask Spread
        m.bid_ask_spread = float(ask - bid)

        # 2. Mid Price
        m.mid_price = float((bid + ask) / 2.0)

        # 3. Micro Price
        if ask > bid:
            spread = ask - bid
            depth_imbalance = (m.mid_price - bid) / spread
            m.micro_price = float(bid + spread * depth_imbalance)
        else:
            m.micro_price = m.mid_price

        # 4. Bid Depth Imbalance
        if m.mid_price > 0:
            m.bid_depth_imbalance = float((bid - m.mid_price) / m.mid_price * 1000)

        # 5. Volume Weighted Mid
        if volume > 0:
            m.volume_weighted_mid = float(m.mid_price * (1 + volume * 0.01))

        # 6. Price Impact
        if len(self._volume_history) >= 10:
            vols = list(self._volume_history)[-10:]
            avg_vol = np.mean(vols)
            if avg_vol > 0:
                m.price_impact = float(volume / avg_vol)

        # 7. Kyle Lambda (simplified)
        m.kyle_lambda = float(m.bid_ask_spread / max(volume, 1e-10))

        # 8. Amihud Illiquidity
        returns = list(self._return_history)
        if len(returns) >= 5 and volume > 0:
            recent_ret = abs(returns[-1])
            m.amihud_illiquidity = float(recent_ret / max(volume, 1e-10))

        # 9. Order Flow Imbalance
        if len(self._bid_history) >= 10 and len(self._ask_history) >= 10:
            bids = list(self._bid_history)[-10:]
            asks = list(self._ask_history)[-10:]
            bid_sum = sum(bids)
            ask_sum = sum(asks)
            total = bid_sum + ask_sum
            if total > 0:
                m.order_flow_imbalance = float((bid_sum - ask_sum) / total)

        # 10. Trade Intensity
        if len(self._timestamp_history) >= 5:
            ts = list(self._timestamp_history)[-5:]
            time_span = ts[-1] - ts[0]
            if time_span > 0:
                m.trade_intensity = float(5.0 / time_span)

        # 11. Volume Surprise
        if len(self._volume_history) >= 20:
            vols = list(self._volume_history)[-20:]
            mean_v = np.mean(vols)
            std_v = np.std(vols)
            if std_v > 0:
                m.volume_surprise = float((volume - mean_v) / std_v)

        # 12. Tick Direction
        if self._last_mid > 0:
            m.tick_direction = float(1.0 if m.mid_price > self._last_mid else (-1.0 if m.mid_price < self._last_mid else 0.0))

        # 13. Lee-Ready Classification (simplified)
        m.lee_ready_class = float(m.tick_direction * m.volume_surprise if m.volume_surprise != 0 else m.tick_direction)

        # 14. Bid-Ask Ratio
        if ask > 0 and bid > 0:
            m.bid_ask_ratio = float(bid / ask)

        # 15. Book Pressure
        m.book_pressure = float(m.order_flow_imbalance * m.volume_surprise if m.volume_surprise != 0 else m.order_flow_imbalance)

    def _compute_temporal_metrics(self, m: QuantumMetrics):
        """Compute time-based metrics"""
        # 1. Time of Day (0-1 normalized)
        import datetime
        now = datetime.datetime.fromtimestamp(m.timestamp)
        m.time_of_day = float((now.hour * 3600 + now.minute * 60 + now.second) / 86400)

        # 2. Session Phase
        if 6 <= now.hour < 14:
            m.session_phase = 0.0  # Asian session
        elif 14 <= now.hour < 22:
            m.session_phase = 0.5  # London session
        else:
            m.session_phase = 1.0  # NY session

        # 3. Seconds Since Epoch
        m.seconds_since_epoch = float(m.timestamp)

        # 4. Tick Frequency
        if len(self._timestamp_history) >= 10:
            ts = list(self._timestamp_history)[-10:]
            intervals = [ts[i+1] - ts[i] for i in range(len(ts)-1)]
            m.tick_frequency = float(1.0 / max(np.mean(intervals), 1e-10))

        # 5. Time Regularity
        if len(self._timestamp_history) >= 10:
            ts = list(self._timestamp_history)[-10:]
            intervals = [ts[i+1] - ts[i] for i in range(len(ts)-1)]
            if len(intervals) > 1:
                m.time_regularity = float(1.0 - min(1.0, np.std(intervals) / max(np.mean(intervals), 1e-10)))

        # 6. Temporal Momentum
        returns = list(self._return_history)
        n = len(returns)
        if n >= 5:
            weights = np.array([1.0 / (i + 1) for i in range(5)])
            weighted_ret = np.sum(np.array(returns[-5:]) * weights) / np.sum(weights)
            m.temporal_momentum = float(weighted_ret)

        # 7. Time-Weighted Return
        if len(self._return_history) >= 10 and len(self._timestamp_history) >= 10:
            rets = list(self._return_history)[-10:]
            ts = list(self._timestamp_history)[-10:]
            dt = [ts[i+1] - ts[i] for i in range(len(ts)-1)]
            total_dt = sum(dt) if dt else 1.0
            if total_dt > 0:
                twr = 1.0
                for i in range(min(len(rets), len(dt))):
                    twr *= (1 + rets[i] * dt[i] / total_dt)
                m.time_weighted_return = float(twr - 1.0)

        # 8. Session Volatility Ratio
        if m.realized_volatility > 0 and m.ewma_volatility > 0:
            m.session_volatility_ratio = float(m.realized_volatility / m.ewma_volatility)

        # 9. Time Dilation
        if len(self._timestamp_history) >= 20:
            ts = list(self._timestamp_history)[-20:]
            intervals = [ts[i+1] - ts[i] for i in range(len(ts)-1)]
            if len(intervals) >= 10:
                first_half = np.mean(intervals[:len(intervals)//2])
                second_half = np.mean(intervals[len(intervals)//2:])
                if first_half > 0:
                    m.time_dilation = float(second_half / first_half - 1.0)

        # 10. Temporal Entropy
        if len(self._timestamp_history) >= 10:
            ts = list(self._timestamp_history)[-10:]
            intervals = np.array([ts[i+1] - ts[i] for i in range(len(ts)-1)])
            if np.sum(intervals) > 0:
                probs = intervals / np.sum(intervals)
                probs = probs[probs > 0]
                m.temporal_entropy = float(-np.sum(probs * np.log2(probs)))

    def _compute_composite_signals(self, m: QuantumMetrics):
        """Compute final composite trading signals"""
        # 1. Trend Signal
        m.trend_signal = float(
            np.clip(m.price_velocity * 10, -1, 1) * 0.4 +
            np.clip(m.hull_momentum * 100, -1, 1) * 0.3 +
            np.clip(m.velocity_trend * 100, -1, 1) * 0.3
        )

        # 2. Mean Reversion Signal
        m.mean_reversion_signal = float(np.clip(-m.z_score * 0.5, -1, 1))

        # 3. Breakout Signal
        m.breakout_signal = float(np.clip(m.momentum_breakout * 0.5, -1, 1))

        # 4. Volatility Signal
        m.volatility_signal = float(
            np.clip((m.vol_regime - 1.0) * 2, -1, 1) if m.vol_regime > 0 else 0
        )

        # 5. Momentum Composite Signal
        m.momentum_composite_signal = float(np.clip(m.momentum_composite, -1, 1))

        # 6. Order Flow Signal
        m.order_flow_signal = float(np.clip(m.order_flow_imbalance * 2, -1, 1))

        # 7. Time Signal
        m.time_signal = float(np.clip(m.temporal_momentum * 100, -1, 1))

        # 8. Regime Signal
        if m.vol_regime > 0:
            if m.vol_regime > 1.5:
                m.regime_signal = float(-0.5)  # High vol regime
            elif m.vol_regime < 0.7:
                m.regime_signal = float(0.3)   # Low vol regime
            else:
                m.regime_signal = float(0.0)

        # 9. Risk-Adjusted Signal
        if m.realized_volatility > 0:
            m.risk_adjusted_signal = float(m.momentum_composite / m.realized_volatility)

        # 10. Hurst Exponent
        returns = list(self._return_history)
        m.hurst_exponent = float(self._estimate_hurst(returns))

        # 11. Fractal Dimension
        m.fractal_dimension = float(2.0 - m.hurst_exponent)

        # 12. Lyapunov Exponent (simplified)
        if len(returns) >= 20:
            arr = np.array(returns[-20:])
            divergence = 0.0
            for i in range(1, len(arr)):
                if abs(arr[i-1]) > 1e-10:
                    divergence += math.log(abs(arr[i] / arr[i-1]))
            m.lyapunov_exponent = float(divergence / max(len(arr) - 1, 1))

        # 13. Entropy Measures
        if len(returns) >= 10:
            arr = np.array(returns[-10:])
            hist, _ = np.histogram(arr, bins=5)
            probs = hist / max(np.sum(hist), 1)
            probs = probs[probs > 0]
            m.entropy_measures = float(-np.sum(probs * np.log2(probs)))

        # 14. Information Ratio
        if len(returns) >= 20:
            arr = np.array(returns[-20:])
            if np.std(arr) > 0:
                m.information_ratio = float(np.mean(arr) / np.std(arr))

        # 15. Sharpe Signal
        if m.realized_volatility > 0:
            m.sharpe_signal = float(m.momentum_composite / m.realized_volatility)

        # 16. Sortino Signal
        returns_arr = np.array(list(self._return_history)[-20:]) if len(self._return_history) >= 20 else np.array([0])
        downside = returns_arr[returns_arr < 0]
        if len(downside) > 0:
            downside_std = np.std(downside)
            if downside_std > 0:
                m.sortino_signal = float(np.mean(returns_arr) / downside_std)

        # 17. Calmar Signal
        if m.realized_volatility > 0:
            m.calmar_signal = float(m.trend_signal / m.realized_volatility)

        # 18. Omega Ratio
        threshold = 0.0
        returns_arr = np.array(list(self._return_history)[-20:]) if len(self._return_history) >= 20 else np.array([0])
        gains = np.sum(returns_arr[returns_arr > threshold] - threshold)
        losses = np.sum(threshold - returns_arr[returns_arr <= threshold])
        if losses > 0:
            m.omega_ratio = float(gains / losses)
        elif gains > 0:
            m.omega_ratio = float(10.0)

        # 19. Tail Risk
        if len(returns) >= 20:
            arr = np.array(returns[-20:])
            m.tail_risk = float(abs(np.percentile(arr, 5)))

        # 20. Cohomology Class (topological complexity)
        m.cohomology_class = float(
            m.hurst_exponent * 0.2 +
            m.fractal_dimension * 0.2 +
            abs(m.lyapunov_exponent) * 0.2 +
            m.entropy_measures * 0.2 +
            m.nc_complexity * 0.2
        )

    def reset(self):
        """Reset engine state"""
        self._bid_history.clear()
        self._ask_history.clear()
        self._mid_history.clear()
        self._volume_history.clear()
        self._timestamp_history.clear()
        self._return_history.clear()
        self._tick_count = 0
        self._start_time = time.time()
        self._last_mid = 0.0
        self._last_bid = 0.0
        self._last_ask = 0.0
        self._last_timestamp = 0.0
        self._ewma_vol = 0.0
        self._ewma_velocity = 0.0
        self._ewma_momentum = 0.0
        self._vol_regime = 0.0
        self._mom_regime = 0.0

    def get_statistics(self) -> dict:
        """Get engine statistics"""
        elapsed = time.time() - self._start_time
        return {
            'tick_count': self._tick_count,
            'elapsed_seconds': elapsed,
            'ticks_per_second': self._tick_count / max(elapsed, 0.001),
            'buffer_usage': len(self._mid_history) / self._lookback,
            'last_mid': self._last_mid,
            'last_vol_regime': self._vol_regime,
        }
