"""
Tick Data Pipeline
Real-time processing of raw ticks for trend and price velocity analysis
Optimized for XAUUSD micro-structural market analysis
"""

import time
from collections import deque
from dataclasses import dataclass
from typing import Optional, List, Tuple
from enum import Enum, auto


class TrendDirection(Enum):
    """Trend direction"""
    STRONG_UP = auto()
    UP = auto()
    NEUTRAL = auto()
    DOWN = auto()
    STRONG_DOWN = auto()


@dataclass
class Tick:
    """Raw tick data"""
    timestamp: float
    bid: float
    ask: float
    volume: float = 0.0
    
    @property
    def mid(self) -> float:
        """Calculate mid price"""
        return (self.bid + self.ask) / 2.0
    
    @property
    def spread(self) -> float:
        """Calculate spread"""
        return self.ask - self.bid


@dataclass
class TickAnalysis:
    """Analysis result from tick processing"""
    timestamp: float
    mid_price: float
    trend: TrendDirection
    price_velocity: float  # Price change per second
    momentum: float        # Short-term momentum
    volatility: float      # Realized volatility
    spread: float          # Current spread
    volume: float          # Current volume
    imbalance: float       # Bid-Ask volume imbalance


class TickPipeline:
    """
    Real-time tick data pipeline for XAUUSD
    Processes raw ticks for trend and price velocity analysis
    """
    
    def __init__(self, 
                 lookback_period: int = 100,
                 velocity_window: float = 1.0,
                 momentum_window: float = 5.0):
        """
        Initialize tick pipeline
        
        Args:
            lookback_period: Number of ticks to keep in history
            velocity_window: Time window for velocity calculation (seconds)
            momentum_window: Time window for momentum calculation (seconds)
        """
        self._lookback_period = lookback_period
        self._velocity_window = velocity_window
        self._momentum_window = momentum_window
        
        # Tick history
        self._ticks: deque = deque(maxlen=lookback_period)
        self._timestamps: deque = deque(maxlen=lookback_period)
        
        # Running statistics
        self._last_tick: Optional[Tick] = None
        self._last_analysis: Optional[TickAnalysis] = None
        
        # Performance counters
        self._tick_count = 0
        self._start_time = time.time()
    
    def process_tick(self, tick: Tick) -> TickAnalysis:
        """
        Process a single tick and return analysis
        
        Args:
            tick: Raw tick data
            
        Returns:
            Analysis result
        """
        self._tick_count += 1
        
        # Store tick
        self._ticks.append(tick)
        self._timestamps.append(tick.timestamp)
        
        # Calculate analysis
        analysis = self._analyze_tick(tick)
        self._last_analysis = analysis
        self._last_tick = tick
        
        return analysis
    
    def process_bid_ask(self, timestamp: float, bid: float, 
                        ask: float, volume: float = 0.0) -> TickAnalysis:
        """
        Process bid/ask update
        
        Args:
            timestamp: Tick timestamp
            bid: Bid price
            ask: Ask price
            volume: Optional volume
            
        Returns:
            Analysis result
        """
        tick = Tick(
            timestamp=timestamp,
            bid=bid,
            ask=ask,
            volume=volume
        )
        return self.process_tick(tick)
    
    def _analyze_tick(self, tick: Tick) -> TickAnalysis:
        """Perform comprehensive tick analysis"""
        
        # Price velocity (change per second)
        velocity = self._calculate_velocity(tick)
        
        # Momentum
        momentum = self._calculate_momentum(tick)
        
        # Realized volatility
        volatility = self._calculate_volatility()
        
        # Trend detection
        trend = self._detect_trend(velocity, momentum)
        
        # Bid-Ask imbalance (simplified)
        imbalance = self._calculate_imbalance(tick)
        
        return TickAnalysis(
            timestamp=tick.timestamp,
            mid_price=tick.mid,
            trend=trend,
            price_velocity=velocity,
            momentum=momentum,
            volatility=volatility,
            spread=tick.spread,
            volume=tick.volume,
            imbalance=imbalance
        )
    
    def _calculate_velocity(self, current_tick: Tick) -> float:
        """
        Calculate price velocity (price change per second)
        Uses linear regression over recent ticks for robustness
        """
        if len(self._ticks) < 2:
            return 0.0
        
        # Find ticks within velocity window
        window_start = current_tick.timestamp - self._velocity_window
        recent_ticks = [
            t for t in self._ticks 
            if t.timestamp >= window_start
        ]
        
        if len(recent_ticks) < 2:
            return 0.0
        
        # Simple velocity: (current - oldest in window) / time
        oldest = recent_ticks[0]
        dt = current_tick.timestamp - oldest.timestamp
        
        if dt < 1e-6:  # Avoid division by zero
            return 0.0
        
        velocity = (current_tick.mid - oldest.mid) / dt
        
        return velocity
    
    def _calculate_momentum(self, current_tick: Tick) -> float:
        """
        Calculate short-term momentum
        Returns normalized momentum score [-1, 1]
        """
        if len(self._ticks) < 2:
            return 0.0
        
        # Find ticks within momentum window
        window_start = current_tick.timestamp - self._momentum_window
        recent_ticks = [
            t for t in self._ticks 
            if t.timestamp >= window_start
        ]
        
        if len(recent_ticks) < 2:
            return 0.0
        
        # Calculate momentum as weighted average of price changes
        momentum = 0.0
        total_weight = 0.0
        
        for i in range(1, len(recent_ticks)):
            dt = recent_ticks[i].timestamp - recent_ticks[i-1].timestamp
            if dt > 1e-6:
                price_change = recent_ticks[i].mid - recent_ticks[i-1].mid
                # Weight by recency
                weight = 1.0 / (1.0 + (current_tick.timestamp - recent_ticks[i].timestamp))
                momentum += price_change * weight
                total_weight += weight
        
        if total_weight > 0:
            momentum /= total_weight
        
        # Normalize to [-1, 1] range (assuming typical XAUUSD moves)
        normalized = max(-1.0, min(1.0, momentum / 10.0))
        
        return normalized
    
    def _calculate_volatility(self) -> float:
        """
        Calculate realized volatility (standard deviation of returns)
        """
        if len(self._ticks) < 10:
            return 0.0
        
        # Calculate returns
        returns = []
        for i in range(1, len(self._ticks)):
            if self._ticks[i-1].mid > 0:
                ret = (self._ticks[i].mid - self._ticks[i-1].mid) / self._ticks[i-1].mid
                returns.append(ret)
        
        if len(returns) < 2:
            return 0.0
        
        # Calculate standard deviation
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        
        return variance ** 0.5
    
    def _detect_trend(self, velocity: float, momentum: float) -> TrendDirection:
        """
        Detect trend direction using velocity and momentum
        """
        # Combine signals
        signal = 0.7 * velocity + 0.3 * momentum * 100  # Scale momentum
        
        # Thresholds for trend detection (based on XAUUSD characteristics)
        if signal > 0.5:
            return TrendDirection.STRONG_UP
        elif signal > 0.1:
            return TrendDirection.UP
        elif signal < -0.5:
            return TrendDirection.STRONG_DOWN
        elif signal < -0.1:
            return TrendDirection.DOWN
        else:
            return TrendDirection.NEUTRAL
    
    def _calculate_imbalance(self, tick: Tick) -> float:
        """
        Calculate bid-ask imbalance
        Positive = more buying pressure, Negative = more selling pressure
        """
        # Simplified imbalance based on position within spread
        if tick.spread < 1e-6:
            return 0.0
        
        # Position relative to bid/ask
        position = (tick.mid - tick.bid) / tick.spread
        
        # Convert to imbalance [-1, 1]
        imbalance = 2.0 * (position - 0.5)
        
        return imbalance
    
    def get_recent_ticks(self, n: int = 10) -> List[Tick]:
        """Get last n ticks"""
        return list(self._ticks)[-n:]
    
    def get_statistics(self) -> dict:
        """Get pipeline statistics"""
        elapsed = time.time() - self._start_time
        
        return {
            'tick_count': self._tick_count,
            'ticks_per_second': self._tick_count / max(elapsed, 0.001),
            'buffer_size': len(self._ticks),
            'buffer_capacity': self._ticks.maxlen
        }
    
    def reset(self):
        """Reset pipeline state"""
        self._ticks.clear()
        self._timestamps.clear()
        self._last_tick = None
        self._last_analysis = None
        self._tick_count = 0
        self._start_time = time.time()


class TickAggregator:
    """
    Aggregates ticks into time-based bars
    Useful for higher timeframe analysis
    """
    
    def __init__(self, bar_interval: float = 1.0):
        """
        Initialize aggregator
        
        Args:
            bar_interval: Bar interval in seconds (e.g., 1.0 for 1-second bars)
        """
        self._bar_interval = bar_interval
        self._current_bar_start: Optional[float] = None
        self._bar_open: float = 0.0
        self._bar_high: float = 0.0
        self._bar_low: float = 0.0
        self._bar_close: float = 0.0
        self._bar_volume: float = 0.0
        self._tick_count: int = 0
    
    def add_tick(self, tick: Tick) -> Optional[dict]:
        """
        Add a tick and return completed bar if interval passed
        
        Returns:
            Completed bar dict or None
        """
        # Initialize or check interval
        if self._current_bar_start is None:
            self._start_new_bar(tick.timestamp, tick.mid, tick.volume)
            return None
        
        # Check if we've moved to next interval
        if tick.timestamp >= self._current_bar_start + self._bar_interval:
            # Complete current bar
            bar = self._get_bar()
            
            # Start new bar
            self._start_new_bar(tick.timestamp, tick.mid, tick.volume)
            
            return bar
        
        # Update current bar
        self._bar_high = max(self._bar_high, tick.mid)
        self._bar_low = min(self._bar_low, tick.mid)
        self._bar_close = tick.mid
        self._bar_volume += tick.volume
        self._tick_count += 1
        
        return None
    
    def _start_new_bar(self, timestamp: float, price: float, volume: float):
        """Start a new bar"""
        self._current_bar_start = timestamp
        self._bar_open = price
        self._bar_high = price
        self._bar_low = price
        self._bar_close = price
        self._bar_volume = volume
        self._tick_count = 1
    
    def _get_bar(self) -> dict:
        """Get completed bar as dictionary"""
        return {
            'timestamp': self._current_bar_start,
            'open': self._bar_open,
            'high': self._bar_high,
            'low': self._bar_low,
            'close': self._bar_close,
            'volume': self._bar_volume,
            'tick_count': self._tick_count
        }
    
    def get_current_bar(self) -> dict:
        """Get current incomplete bar"""
        if self._current_bar_start is None:
            return None
        
        return self._get_bar()
    
    def reset(self):
        """Reset aggregator state"""
        self._current_bar_start = None
        self._tick_count = 0
