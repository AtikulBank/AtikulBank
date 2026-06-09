"""
LAYER 1: SIGNAL INTEGRITY
Validates incoming tick data for authenticity and sanity
"""

import time
import hashlib
import numpy as np
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque


@dataclass
class TickData:
    """Raw tick data from cTrader"""
    bid: float = 0.0
    ask: float = 0.0
    volume: float = 0.0
    timestamp: float = 0.0
    symbol: str = ""
    source: str = ""


@dataclass
class ValidationResult:
    """Result of signal validation"""
    is_valid: bool = True
    rejection_reason: str = ""
    timestamp: float = 0.0
    tick_hash: str = ""


class SignalIntegrity:
    """
    Layer 1: Signal Integrity
    Validates incoming tick data for authenticity and sanity
    """
    
    def __init__(
        self,
        max_spread_pct: float = 0.01,  # 1% max spread
        min_price: float = 100.0,  # Minimum valid price (XAUUSD)
        max_price: float = 5000.0,  # Maximum valid price
        min_volume: float = 0.0,
        max_volume_spike: float = 100.0,  # 100x average volume
        heartbeat_timeout_s: float = 30.0
    ) -> None:
        """
        Initialize Signal Integrity
        
        Args:
            max_spread_pct: Maximum allowed spread as percentage of mid price
            min_price: Minimum valid price
            max_price: Maximum valid price
            min_volume: Minimum valid volume
            max_volume_spike: Maximum volume spike multiplier
            heartbeat_timeout_s: Heartbeat timeout in seconds
        """
        self.max_spread_pct = max_spread_pct
        self.min_price = min_price
        self.max_price = max_price
        self.min_volume = min_volume
        self.max_volume_spike = max_volume_spike
        self.heartbeat_timeout_s = heartbeat_timeout_s
        
        # State tracking
        self._last_timestamp: float = 0.0
        self._last_heartbeat: float = time.time()
        self._volume_history: deque = deque(maxlen=1000)
        self._price_history: deque = deque(maxlen=1000)
        self._rejected_count: int = 0
        self._total_count: int = 0
        
    def validate_tick(self, tick: TickData) -> ValidationResult:
        """
        Validate a single tick
        
        Args:
            tick: Raw tick data
            
        Returns:
            ValidationResult with validation status
        """
        self._total_count += 1
        result = ValidationResult(
            is_valid=True,
            timestamp=time.time(),
            tick_hash=self._hash_tick(tick)
        )
        
        # Check 1: Price sanity bounds
        if not self._check_price_bounds(tick):
            result.is_valid = False
            result.rejection_reason = "Price out of bounds"
            self._rejected_count += 1
            return result
        
        # Check 2: Bid-Ask spread validity
        if not self._check_spread_validity(tick):
            result.is_valid = False
            result.rejection_reason = "Spread too large"
            self._rejected_count += 1
            return result
        
        # Check 3: Timestamp monotonicity
        if not self._check_timestamp_monotonicity(tick):
            result.is_valid = False
            result.rejection_reason = "Timestamp not monotonic"
            self._rejected_count += 1
            return result
        
        # Check 4: Volume spike detection
        if not self._check_volume_spike(tick):
            result.is_valid = False
            result.rejection_reason = "Volume spike detected"
            self._rejected_count += 1
            return result
        
        # Check 5: Exchange heartbeat verify
        if not self._check_heartbeat():
            result.is_valid = False
            result.rejection_reason = "Heartbeat timeout"
            self._rejected_count += 1
            return result
        
        # Update state
        self._last_timestamp = tick.timestamp
        self._price_history.append((tick.bid + tick.ask) / 2)
        self._volume_history.append(tick.volume)
        
        return result
    
    def _hash_tick(self, tick: TickData) -> str:
        """Generate unique hash for tick"""
        data = f"{tick.bid}:{tick.ask}:{tick.volume}:{tick.timestamp}"
        return hashlib.md5(data.encode()).hexdigest()[:16]
    
    def _check_price_bounds(self, tick: TickData) -> bool:
        """Check if price is within valid bounds"""
        mid = (tick.bid + tick.ask) / 2
        return self.min_price <= mid <= self.max_price
    
    def _check_spread_validity(self, tick: TickData) -> bool:
        """Check if spread is within valid bounds"""
        if tick.bid <= 0 or tick.ask <= 0:
            return False
        
        spread = tick.ask - tick.bid
        mid = (tick.bid + tick.ask) / 2
        spread_pct = spread / mid if mid > 0 else float('inf')
        
        return spread_pct <= self.max_spread_pct
    
    def _check_timestamp_monotonicity(self, tick: TickData) -> bool:
        """Check if timestamp is monotonically increasing"""
        if tick.timestamp <= self._last_timestamp:
            return False
        return True
    
    def _check_volume_spike(self, tick: TickData) -> bool:
        """Check for volume spikes"""
        if tick.volume < self.min_volume:
            return False
        
        if len(self._volume_history) < 10:
            return True  # Not enough history
        
        avg_volume = np.mean(self._volume_history)
        if avg_volume <= 0:
            return True
        
        volume_ratio = tick.volume / avg_volume
        return volume_ratio <= self.max_volume_spike
    
    def _check_heartbeat(self) -> bool:
        """Check if heartbeat is within timeout"""
        current_time = time.time()
        time_since_heartbeat = current_time - self._last_heartbeat
        return time_since_heartbeat <= self.heartbeat_timeout_s
    
    def update_heartbeat(self) -> None:
        """Update heartbeat timestamp"""
        self._last_heartbeat = time.time()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        rejection_rate = self._rejected_count / self._total_count if self._total_count > 0 else 0.0
        
        return {
            "total_ticks": self._total_count,
            "rejected_ticks": self._rejected_count,
            "rejection_rate": rejection_rate,
            "valid_rate": 1.0 - rejection_rate,
            "avg_volume": np.mean(self._volume_history) if self._volume_history else 0.0,
            "avg_price": np.mean(self._price_history) if self._price_history else 0.0,
            "last_timestamp": self._last_timestamp
        }
    
    def reset(self) -> None:
        """Reset validation state"""
        self._last_timestamp = 0.0
        self._last_heartbeat = time.time()
        self._volume_history.clear()
        self._price_history.clear()
        self._rejected_count = 0
        self._total_count = 0