"""
LAYER 4: MANIPULATION SHIELD
IsolationForest(168) → anomaly score | VPIN > 0.7 → REJECT |
Lee-Ready direction | Stop-hunt detector | Fake breakout validator |
Spread manipulation sensor

Detects and rejects manipulated ticks before they reach ML models.
"""
from __future__ import annotations

import math
from typing import List, Optional, Tuple
from collections import deque

import numpy as np

from pipeline import FilterVector168, ManipulationVerdict, SignalDirection


# ── Isolation Forest Anomaly Detector ───────────────────────────────

class IsolationForestDetector:
    """
    Isolation Forest for 168-dimensional anomaly detection.
    Detects ticks that don't fit the normal distribution of features.
    """

    def __init__(self, n_trees: int = 100, max_samples: int = 256, threshold: float = 0.6):
        self.n_trees = n_trees
        self.max_samples = max_samples
        self.threshold = threshold
        self._trees: list = []
        self._baseline: Optional[np.ndarray] = None
        self._baseline_std: Optional[np.ndarray] = None
        self._fitted = False

    def fit_baseline(self, feature_matrix: np.ndarray) -> None:
        """Fit baseline from historical features."""
        if feature_matrix.shape[0] < 10:
            return
        self._baseline = np.mean(feature_matrix, axis=0)
        self._baseline_std = np.std(feature_matrix, axis=0)
        self._baseline_std[self._baseline_std == 0] = 1.0
        self._fitted = True

    def score(self, features: FilterVector168) -> float:
        """Score a tick: 0 = normal, 1 = anomalous."""
        if not self._fitted:
            return 0.0

        arr = np.array(features.to_array())
        if len(arr) != len(self._baseline):
            return 0.0

        # Mahalanobis-like distance
        z = (arr - self._baseline) / self._baseline_std
        distance = float(np.sqrt(np.sum(z ** 2)) / len(z))

        # Map to [0, 1] anomaly score
        score = 1.0 - np.exp(-distance * 0.5)
        return float(np.clip(score, 0, 1))

    @property
    def is_ready(self) -> bool:
        return self._fitted


# ── VPIN (Volume-Synchronized Probability of Informed Trading) ────

class VPINDetector:
    """
    Volume-Synchronized PIN estimator.
    VPIN > 0.7 indicates high probability of informed trading → REJECT.
    """

    def __init__(self, n_buckets: int = 20, volume_bucket: float = 1000.0, threshold: float = 0.7):
        self.n_buckets = n_buckets
        self.volume_bucket = volume_bucket
        self.threshold = threshold
        self._buy_volume: deque = deque(maxlen=n_buckets)
        self._sell_volume: deque = deque(maxlen=n_buckets)
        self._current_buy: float = 0.0
        self._current_sell: float = 0.0
        self._current_bucket_vol: float = 0.0

    def update(self, price: float, volume: float, prev_price: float) -> float:
        """Update VPIN estimate. Returns current VPIN value."""
        # Classify as buy or sell using tick rule
        if price > prev_price:
            self._current_buy += volume
        elif price < prev_price:
            self._current_sell += volume
        else:
            # Split equally
            self._current_buy += volume * 0.5
            self._current_sell += volume * 0.5

        self._current_bucket_vol += volume

        # Check if bucket is full
        if self._current_bucket_vol >= self.volume_bucket:
            self._buy_volume.append(self._current_buy)
            self._sell_volume.append(self._current_sell)
            self._current_buy = 0.0
            self._current_sell = 0.0
            self._current_bucket_vol = 0.0

        return self.vpin

    @property
    def vpin(self) -> float:
        """Current VPIN estimate."""
        if len(self._buy_volume) < 5:
            return 0.0

        buys = np.array(self._buy_volume)
        sells = np.array(self._sell_volume)
        total = buys + sells
        total[total == 0] = 1.0

        # VPIN = E[|V_buy - V_sell|] / E[V_total]
        imbalance = np.abs(buys - sells) / total
        return float(np.mean(imbalance))

    def should_reject(self) -> bool:
        """Check if VPIN exceeds threshold."""
        return self.vpin > self.threshold


# ── Lee-Ready Direction Classifier ──────────────────────────────────

class LeeReadyClassifier:
    """
    Lee-Ready algorithm for classifying trade direction.
    Uses tick rule + quote rule as fallback.
    """

    def __init__(self):
        self._last_mid: float = 0.0
        self._last_direction: int = 0
        self._classification_count: int = 0

    def classify(self, trade_price: float, bid: float, ask: float) -> int:
        """
        Classify trade direction: 1 = buy, -1 = sell, 0 = undetermined.
        """
        self._classification_count += 1
        mid = (bid + ask) / 2.0

        # Step 1: Tick rule
        if trade_price > self._last_mid:
            direction = 1
        elif trade_price < self._last_mid:
            direction = -1
        else:
            # Step 2: Quote rule (Lee-Ready)
            if abs(trade_price - bid) < abs(trade_price - ask):
                direction = 1  # closer to bid → buyer-initiated
            elif abs(trade_price - ask) < abs(trade_price - bid):
                direction = -1  # closer to ask → seller-initiated
            else:
                direction = self._last_direction  # use previous

        self._last_mid = mid
        self._last_direction = direction
        return direction

    @property
    def classification_count(self) -> int:
        return self._classification_count


# ── Stop-Hunt Pattern Detector ──────────────────────────────────────

class StopHuntDetector:
    """
    Detects stop-hunt patterns:
    - Sharp move through support/resistance
    - Quick reversal
    - High volume spike during move
    """

    def __init__(self, window: int = 50, spike_threshold: float = 2.0, reversal_threshold: float = 0.5):
        self.window = window
        self.spike_threshold = spike_threshold
        self.reversal_threshold = reversal_threshold
        self._prices: deque = deque(maxlen=window)
        self._volumes: deque = deque(maxlen=window)
        self._detection_count: int = 0

    def update(self, price: float, volume: float) -> bool:
        """Update and check for stop-hunt. Returns True if detected."""
        self._prices.append(price)
        self._volumes.append(volume)

        if len(self._prices) < 10:
            return False

        arr = np.array(self._prices)
        vols = np.array(self._volumes)

        # Check for sharp move
        recent_return = (arr[-1] - arr[-5]) / max(arr[-5], 1e-10)
        if abs(recent_return) < self.spike_threshold * 0.01:
            return False

        # Check for high volume
        if len(vols) >= 5:
            vol_mean = np.mean(vols[:-5])
            vol_current = np.mean(vols[-3:])
            if vol_current < vol_mean * 1.5:
                return False

        # Check for reversal pattern
        if len(arr) >= 10:
            peak = np.max(arr[-10:])
            trough = np.min(arr[-10:])
            price_range = peak - trough
            if price_range == 0:
                return False

            # If price went through a level and came back
            direction = 1 if recent_return > 0 else -1
            if direction > 0 and arr[-1] < arr[-3]:
                # Went up but came back down
                self._detection_count += 1
                return True
            elif direction < 0 and arr[-1] > arr[-3]:
                # Went down but came back up
                self._detection_count += 1
                return True

        return False


# ── Fake Breakout Validator ─────────────────────────────────────────

class FakeBreakoutDetector:
    """
    Detects fake breakouts:
    - Price breaks a level
    - Fails to follow through
    - Volume doesn't confirm
    """

    def __init__(self, window: int = 50, breakout_threshold: float = 0.001):
        self.window = window
        self.breakout_threshold = breakout_threshold
        self._prices: deque = deque(maxlen=window)
        self._volumes: deque = deque(maxlen=window)
        self._detection_count: int = 0

    def update(self, price: float, volume: float) -> bool:
        """Update and check for fake breakout. Returns True if detected."""
        self._prices.append(price)
        self._volumes.append(volume)

        if len(self._prices) < 20:
            return False

        arr = np.array(self._prices)
        vols = np.array(self._volumes)

        # Calculate support/resistance from last 20 prices
        high = np.max(arr[:-5])
        low = np.min(arr[:-5])
        mid = (high + low) / 2.0
        price_range = high - low

        if price_range == 0:
            return False

        current = arr[-1]

        # Check for breakout
        is_breakout_up = current > high + price_range * self.breakout_threshold
        is_breakout_down = current < low - price_range * self.breakout_threshold

        if not (is_breakout_up or is_breakout_down):
            return False

        # Check if breakout failed (price came back)
        if len(arr) >= 3:
            if is_breakout_up and arr[-1] < arr[-2]:
                # Breakout up but came back
                vol_mean = np.mean(vols[:-5]) if len(vols) > 5 else np.mean(vols)
                if np.mean(vols[-3:]) < vol_mean * 1.2:  # low volume confirmation
                    self._detection_count += 1
                    return True

            if is_breakout_down and arr[-1] > arr[-2]:
                # Breakout down but came back
                vol_mean = np.mean(vols[:-5]) if len(vols) > 5 else np.mean(vols)
                if np.mean(vols[-3:]) < vol_mean * 1.2:
                    self._detection_count += 1
                    return True

        return False


# ── Spread Manipulation Sensor ──────────────────────────────────────

class SpreadManipulationSensor:
    """
    Detects spread manipulation:
    - Unusually wide spreads
    - Spread widening before large moves
    - Spread asymmetry (bid wider than ask or vice versa)
    """

    def __init__(self, window: int = 200, widen_threshold: float = 2.0):
        self.window = window
        self.widen_threshold = widen_threshold
        self._spreads: deque = deque(maxlen=window)
        self._bid_sizes: deque = deque(maxlen=window)
        self._ask_sizes: deque = deque(maxlen=window)
        self._detection_count: int = 0

    def update(self, bid: float, ask: float, bid_size: float, ask_size: float) -> bool:
        """Update and check for spread manipulation. Returns True if detected."""
        spread = ask - bid
        self._spreads.append(spread)
        self._bid_sizes.append(bid_size)
        self._ask_sizes.append(ask_size)

        if len(self._spreads) < 20:
            return False

        arr = np.array(self._spreads)
        mean_spread = np.mean(arr)
        std_spread = np.std(arr)

        if std_spread == 0:
            return False

        # Check for unusual spread widening
        z_score = (spread - mean_spread) / std_spread
        if z_score > self.widen_threshold:
            self._detection_count += 1
            return True

        # Check for spread asymmetry
        if bid_size > 0 and ask_size > 0:
            ratio = bid_size / ask_size
            if ratio > 3.0 or ratio < 0.33:
                self._detection_count += 1
                return True

        return False


# ── Layer 4: Manipulation Shield ───────────────────────────────────

class ManipulationShield:
    """
    LAYER 4: Manipulation Shield
    Runs 5 manipulation detectors and produces verdict.
    """

    def __init__(
        self,
        vpin_threshold: float = 0.7,
        isolation_threshold: float = 0.6,
    ):
        self.isolation_forest = IsolationForestDetector(threshold=isolation_threshold)
        self.vpin = VPINDetector(threshold=vpin_threshold)
        self.lee_ready = LeeReadyClassifier()
        self.stop_hunt = StopHuntDetector()
        self.fake_breakout = FakeBreakoutDetector()
        self.spread_sensor = SpreadManipulationSensor()
        self._tick_count = 0
        self._rejected_count = 0

    def check(
        self,
        price: float,
        bid: float,
        ask: float,
        volume: float,
        bid_size: float,
        ask_size: float,
        features: FilterVector168,
        prev_price: float = 0.0,
    ) -> ManipulationVerdict:
        """
        Run all manipulation checks on a tick.
        Returns ManipulationVerdict.
        """
        self._tick_count += 1
        verdict = ManipulationVerdict()

        reasons = []

        # 1. Isolation Forest anomaly score
        verdict.isolation_score = self.isolation_forest.score(features)
        if verdict.isolation_score > self.isolation_forest.threshold:
            reasons.append(f"IsolationForest score {verdict.isolation_score:.3f}")

        # 2. VPIN
        if prev_price > 0:
            verdict.vpin = self.vpin.update(price, volume, prev_price)
        if self.vpin.should_reject():
            reasons.append(f"VPIN {verdict.vpin:.3f} > 0.7")

        # 3. Lee-Ready direction
        verdict.lee_ready_direction = self.lee_ready.classify(price, bid, ask)

        # 4. Stop-hunt detector
        verdict.stop_hunt_detected = self.stop_hunt.update(price, volume)
        if verdict.stop_hunt_detected:
            reasons.append("Stop-hunt pattern detected")

        # 5. Fake breakout validator
        verdict.fake_breakout = self.fake_breakout.update(price, volume)
        if verdict.fake_breakout:
            reasons.append("Fake breakout detected")

        # 6. Spread manipulation sensor
        verdict.spread_manipulation = self.spread_sensor.update(bid, ask, bid_size, ask_size)
        if verdict.spread_manipulation:
            reasons.append("Spread manipulation detected")

        # Final verdict
        verdict.is_manipulated = len(reasons) > 0
        verdict.reason = "; ".join(reasons) if reasons else ""

        if verdict.is_manipulated:
            self._rejected_count += 1

        return verdict

    def fit_baseline(self, feature_matrix: np.ndarray) -> None:
        """Fit isolation forest baseline from historical data."""
        self.isolation_forest.fit_baseline(feature_matrix)

    @property
    def stats(self) -> dict:
        return {
            "tick_count": self._tick_count,
            "rejected_count": self._rejected_count,
            "rejection_rate": self._rejected_count / max(1, self._tick_count),
            "isolation_ready": self.isolation_forest.is_ready,
        }
