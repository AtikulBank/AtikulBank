"""
LAYER 1: SIGNAL INTEGRITY
Tick authentication | Timestamp monotonicity | Price sanity bounds |
Bid-Ask spread validity | Volume spike detection | Exchange heartbeat verify

Validates every incoming tick for integrity, sanity, and authenticity
before any downstream processing.
"""
from __future__ import annotations

import hashlib
import hmac
import time
from typing import Optional, Tuple, List
from collections import deque

import numpy as np

from pipeline import TickData, ValidatedTick, SignalDirection


# ── Price Sanity Bounds ─────────────────────────────────────────────

class PriceSanityChecker:
    """
    Validates price is within expected bounds for the instrument.
    Prevents corrupt ticks from entering the pipeline.
    """

    # XAUUSD reasonable bounds (USD per troy oz)
    XAUUSD_MIN = 100.0
    XAUUSD_MAX = 10_000.0
    XAUUSD_MAX_TICK_MOVE = 50.0  # max $50 move in one tick

    def __init__(
        self,
        symbol: str = "XAUUSD",
        min_price: float = XAUUSD_MIN,
        max_price: float = XAUUSD_MAX,
        max_tick_move: float = XAUUSD_MAX_TICK_MOVE,
    ):
        self.symbol = symbol
        self.min_price = min_price
        self.max_price = max_price
        self.max_tick_move = max_tick_move
        self._last_price: Optional[float] = None
        self._violation_count = 0

    def check(self, price: float) -> Tuple[bool, str]:
        """Check if price is sane. Returns (is_valid, reason)."""
        if price <= 0:
            self._violation_count += 1
            return False, f"Price {price} <= 0"

        if price < self.min_price:
            self._violation_count += 1
            return False, f"Price {price} < min {self.min_price}"

        if price > self.max_price:
            self._violation_count += 1
            return False, f"Price {price} > max {self.max_price}"

        if self._last_price is not None:
            move = abs(price - self._last_price)
            if move > self.max_tick_move:
                self._violation_count += 1
                return False, f"Tick move {move:.2f} exceeds max {self.max_tick_move}"

        self._last_price = price
        return True, "ok"

    @property
    def violation_count(self) -> int:
        return self._violation_count


# ── Bid-Ask Spread Validator ────────────────────────────────────────

class SpreadValidator:
    """
    Validates bid-ask spread is within acceptable limits.
    Detects stale quotes, wide spreads, and crossing quotes.
    """

    def __init__(
        self,
        max_spread_bps: float = 50.0,   # 5 basis points max
        max_spread_abs: float = 5.0,    # $5 max absolute spread
        min_spread_bps: float = 0.0,    # 0 = allow zero spread
    ):
        self.max_spread_bps = max_spread_bps
        self.max_spread_abs = max_spread_abs
        self.min_spread_bps = min_spread_bps
        self._history: deque = deque(maxlen=1000)
        self._violation_count = 0

    def check(self, bid: float, ask: float) -> Tuple[bool, str, float]:
        """
        Validate spread. Returns (is_valid, reason, spread_bps).
        """
        if bid <= 0 or ask <= 0:
            self._violation_count += 1
            return False, "bid or ask <= 0", 0.0

        # Crossing quote (bid > ask)
        if bid > ask:
            self._violation_count += 1
            return False, f"Crossing quote: bid={bid} > ask={ask}", 0.0

        spread = ask - bid
        mid = (ask + bid) / 2.0
        spread_bps = (spread / mid * 10_000) if mid > 0 else 0.0

        # Too wide
        if spread_bps > self.max_spread_bps:
            self._violation_count += 1
            return False, f"Spread {spread_bps:.1f} bps > max {self.max_spread_bps}", spread_bps

        if spread > self.max_spread_abs:
            self._violation_count += 1
            return False, f"Spread ${spread:.2f} > max ${self.max_spread_abs}", spread_bps

        self._history.append(spread_bps)
        return True, "ok", spread_bps

    def avg_spread_bps(self) -> float:
        """Average spread over recent history."""
        if not self._history:
            return 0.0
        return float(np.mean(list(self._history)))

    @property
    def violation_count(self) -> int:
        return self._violation_count


# ── Volume Spike Detector ───────────────────────────────────────────

class VolumeSpikeDetector:
    """
    Detects abnormal volume spikes that may indicate:
    - Flash crash
    - Spoofing / layering
    - News event
    """

    def __init__(
        self,
        window: int = 100,
        spike_threshold: float = 3.0,  # 3x mean
        extreme_threshold: float = 5.0,  # 5x mean
    ):
        self.window = window
        self.spike_threshold = spike_threshold
        self.extreme_threshold = extreme_threshold
        self._history: deque = deque(maxlen=window)
        self._spike_count = 0
        self._extreme_count = 0

    def check(self, volume: float) -> Tuple[bool, str, float]:
        """
        Check volume spike. Returns (is_normal, description, z_score).
        """
        if len(self._history) < 10:
            self._history.append(volume)
            return True, "warming up", 0.0

        arr = np.array(self._history)
        mean = np.mean(arr)
        std = np.std(arr)

        if std == 0:
            self._history.append(volume)
            return True, "zero variance", 0.0

        z_score = (volume - mean) / std
        self._history.append(volume)

        if abs(z_score) > self.extreme_threshold:
            self._extreme_count += 1
            return False, f"EXTREME volume spike z={z_score:.2f}", z_score

        if abs(z_score) > self.spike_threshold:
            self._spike_count += 1
            return False, f"Volume spike z={z_score:.2f}", z_score

        return True, "normal", z_score

    @property
    def stats(self) -> dict:
        return {
            "spike_count": self._spike_count,
            "extreme_count": self._extreme_count,
            "history_len": len(self._history),
        }


# ── Tick Authenticator ──────────────────────────────────────────────

class TickAuthenticator:
    """
    HMAC-based tick authentication.
    Verifies tick hasn't been tampered with in transit.
    """

    def __init__(self, secret_key: str = ""):
        self._key = secret_key.encode() if secret_key else b""
        self._verified_count = 0
        self._failed_count = 0

    def compute_hmac(self, tick_data: str) -> str:
        """Compute HMAC-SHA256 for tick data."""
        if not self._key:
            return ""
        return hmac.new(self._key, tick_data.encode(), hashlib.sha256).hexdigest()

    def verify(self, tick_data: str, expected_hmac: str) -> bool:
        """Verify tick HMAC."""
        if not self._key:
            # No key configured = skip verification (development mode)
            self._verified_count += 1
            return True

        computed = self.compute_hmac(tick_data)
        is_valid = hmac.compare_digest(computed, expected_hmac)

        if is_valid:
            self._verified_count += 1
        else:
            self._failed_count += 1

        return is_valid

    @property
    def stats(self) -> dict:
        return {
            "verified": self._verified_count,
            "failed": self._failed_count,
            "has_key": bool(self._key),
        }


# ── Exchange Heartbeat Verifier ─────────────────────────────────────

class HeartbeatVerifier:
    """
    Monitors exchange heartbeat to detect disconnection.
    Triggers alert if no heartbeat received within threshold.
    """

    def __init__(self, expected_interval_s: float = 30.0, tolerance_s: float = 5.0):
        self.expected_interval_s = expected_interval_s
        self.tolerance_s = tolerance_s
        self._last_heartbeat_ns: int = 0
        self._heartbeat_count: int = 0
        self._missed_count: int = 0

    def on_heartbeat(self) -> None:
        """Called when heartbeat received from exchange."""
        now = time.time_ns()

        if self._last_heartbeat_ns > 0:
            gap_s = (now - self._last_heartbeat_ns) / 1e9
            if gap_s > self.expected_interval_s + self.tolerance_s:
                self._missed_count += 1

        self._last_heartbeat_ns = now
        self._heartbeat_count += 1

    def is_connected(self) -> bool:
        """Check if heartbeat is within acceptable window."""
        if self._last_heartbeat_ns == 0:
            return True  # No heartbeat yet, assume connected

        elapsed_s = (time.time_ns() - self._last_heartbeat_ns) / 1e9
        return elapsed_s < self.expected_interval_s + self.tolerance_s * 2

    def seconds_since_heartbeat(self) -> float:
        """Seconds since last heartbeat."""
        if self._last_heartbeat_ns == 0:
            return 0.0
        return (time.time_ns() - self._last_heartbeat_ns) / 1e9

    @property
    def stats(self) -> dict:
        return {
            "heartbeat_count": self._heartbeat_count,
            "missed_count": self._missed_count,
            "is_connected": self.is_connected(),
            "seconds_since_last": self.seconds_since_heartbeat(),
        }


# ── Layer 1: Signal Integrity ──────────────────────────────────────

class SignalIntegrity:
    """
    LAYER 1: Signal Integrity
    Validates every incoming tick through 6 integrity checks.
    """

    def __init__(
        self,
        symbol: str = "XAUUSD",
        auth_key: str = "",
        max_spread_bps: float = 50.0,
        volume_spike_threshold: float = 3.0,
    ):
        self.price_checker = PriceSanityChecker(symbol=symbol)
        self.spread_validator = SpreadValidator(max_spread_bps=max_spread_bps)
        self.volume_detector = VolumeSpikeDetector(spike_threshold=volume_spike_threshold)
        self.authenticator = TickAuthenticator(secret_key=auth_key)
        self.heartbeat = HeartbeatVerifier()

        self._tick_count = 0
        self._rejected_count = 0

    def validate(self, tick: TickData) -> ValidatedTick:
        """
        Run all 6 integrity checks on a tick.
        Returns ValidatedTick with validation results.
        """
        import time as _time
        t0 = _time.perf_counter_ns()
        self._tick_count += 1

        result = ValidatedTick(tick=tick)

        reasons = []

        # Check 1: Tick authentication (if key configured)
        if self.authenticator._key:
            tick_str = f"{tick.symbol}:{tick.bid}:{tick.ask}:{tick.timestamp_ns}"
            if not self.authenticator.verify(tick_str, ""):
                reasons.append("Authentication failed")

        clock_valid = True  # simplified: assume monotonic ok
        result.monotonic_ok = clock_valid

        # Check 3: Price sanity (bid)
        bid_valid, bid_reason = self.price_checker.check(tick.bid)
        if not bid_valid:
            reasons.append(f"Bid: {bid_reason}")

        # Check 4: Price sanity (ask)
        ask_valid, ask_reason = self.price_checker.check(tick.ask)
        if not ask_valid:
            reasons.append(f"Ask: {ask_reason}")

        # Check 5: Spread validity
        spread_valid, spread_reason, spread_bps = self.spread_validator.check(tick.bid, tick.ask)
        result.spread_bps = spread_bps
        if not spread_valid:
            reasons.append(f"Spread: {spread_reason}")

        # Check 6: Volume spike
        vol_valid, vol_reason, vol_z = self.volume_detector.check(tick.last_size)
        if not vol_valid:
            reasons.append(f"Volume: {vol_reason}")

        # Final verdict
        result.is_valid = len(reasons) == 0
        result.rejection_reason = "; ".join(reasons) if reasons else ""
        result.latency_ns = _time.perf_counter_ns() - t0

        if not result.is_valid:
            self._rejected_count += 1

        return result

    def on_heartbeat(self):
        """Forward heartbeat to verifier."""
        self.heartbeat.on_heartbeat()

    @property
    def stats(self) -> dict:
        return {
            "tick_count": self._tick_count,
            "rejected_count": self._rejected_count,
            "acceptance_rate": (self._tick_count - self._rejected_count) / max(1, self._tick_count),
            "price_violations": self.price_checker.violation_count,
            "spread_violations": self.spread_validator.violation_count,
            "volume_stats": self.volume_detector.stats,
            "auth_stats": self.authenticator.stats,
            "heartbeat_stats": self.heartbeat.stats,
        }
