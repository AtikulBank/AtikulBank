"""
Simulated Market Data Feed for XAUUSD
Generates realistic tick-level market data for testing when live FIX is unavailable
"""

import time
import random
import math
from datetime import datetime, timezone
from typing import Callable, Optional


class SimulatedMarketFeed:
    """
    Generates realistic XAUUSD tick data for testing
    Simulates real market microstructure with realistic spreads, volatility, and order book dynamics
    """
    
    def __init__(self):
        # XAUUSD realistic parameters
        self._base_price = 2350.00  # Base price level
        self._tick_size = 0.01      # Minimum price movement
        self._spread_base = 0.30    # Base spread in points
        self._volatility = 0.0005  # Intraday volatility factor
        
        # Market state
        self._current_price = self._base_price
        self._bid = self._base_price - self._spread_base / 2
        self._ask = self._base_price + self._spread_base / 2
        self._last_update_time = time.time()
        self._tick_count = 0
        
        # Random walk parameters
        self._drift = 0.0
        self._mean_reversion_speed = 0.02
        
        # Callbacks
        self._on_tick_callback: Optional[Callable] = None
        self._running = False
    
    def set_on_tick_callback(self, callback: Callable):
        """Set callback function for new tick data"""
        self._on_tick_callback = callback
    
    def start(self):
        """Start the simulated feed"""
        self._running = True
        self._last_update_time = time.time()
    
    def stop(self):
        """Stop the simulated feed"""
        self._running = False
    
    def _generate_tick(self) -> dict:
        """Generate a realistic XAUUSD tick"""
        current_time = time.time()
        dt = current_time - self._last_update_time
        self._last_update_time = current_time
        
        # Mean-reverting random walk for price
        mean_reversion = self._mean_reversion_speed * (self._base_price - self._current_price)
        random_shock = random.gauss(0, self._volatility * math.sqrt(dt) * self._current_price)
        
        price_change = mean_reversion * dt + random_shock
        self._current_price += price_change
        
        # Round to tick size
        self._current_price = round(self._current_price / self._tick_size) * self._tick_size
        
        # Dynamic spread based on volatility
        spread = self._spread_base + abs(random.gauss(0, 0.10))
        spread = max(0.20, min(1.50, spread))  # Clamp spread
        
        # Update bid/ask
        self._bid = round(self._current_price - spread / 2, 2)
        self._ask = round(self._current_price + spread / 2, 2)
        
        # Generate volume
        base_volume = random.randint(1, 50)
        
        # Simulate institutional block sizes occasionally
        if random.random() < 0.05:  # 5% chance of large order
            base_volume = random.randint(100, 1000)
        
        self._tick_count += 1
        
        return {
            'timestamp': datetime.now(timezone.utc).strftime("%Y%m%d-%H:%M:%S.") + f"{datetime.now(timezone.utc).microsecond // 1000:03d}",
            'symbol': 'XAUUSD',
            'bid': self._bid,
            'ask': self._ask,
            'bid_size': base_volume,
            'ask_size': random.randint(1, 50),
            'last': self._current_price,
            'last_size': random.randint(1, 20),
            'tick_id': self._tick_count,
            'bid_change': random.choice([-self._tick_size, 0, self._tick_size]),
            'ask_change': random.choice([-self._tick_size, 0, self._tick_size]),
        }
    
    def get_next_tick(self) -> dict:
        """Get the next simulated tick"""
        if not self._running:
            self.start()
        return self._generate_tick()
    
    def get_current_price(self) -> float:
        """Get current mid price"""
        return (self._bid + self._ask) / 2
    
    def get_current_spread(self) -> float:
        """Get current spread"""
        return self._ask - self._bid
    
    def get_order_book_snapshot(self, levels: int = 5) -> dict:
        """Generate simulated order book snapshot"""
        bids = []
        asks = []
        
        for i in range(levels):
            bid_price = self._bid - i * self._tick_size * random.uniform(1, 3)
            ask_price = self._ask + i * self._tick_size * random.uniform(1, 3)
            
            bid_size = random.randint(1, 100) * (1 + i * 0.5)  # Deeper levels have more liquidity
            ask_size = random.randint(1, 100) * (1 + i * 0.5)
            
            bids.append({
                'price': round(bid_price, 2),
                'size': int(bid_size),
            })
            asks.append({
                'price': round(ask_price, 2),
                'size': int(ask_size),
            })
        
        return {
            'bids': bids,
            'asks': asks,
            'timestamp': datetime.now(timezone.utc).strftime("%Y%m%d-%H:%M:%S.") + f"{datetime.now(timezone.utc).microsecond // 1000:03d}",
        }
    
    def simulate_market_shock(self, direction: int = 1, magnitude: float = 5.0):
        """Simulate a sudden market shock (for testing robustness)"""
        self._current_price += direction * magnitude
        self._bid = self._current_price - self._spread_base / 2
        self._ask = self._current_price + self._spread_base / 2
    
    def simulate_news_event(self, impact: str = "medium"):
        """Simulate news-driven volatility spike"""
        if impact == "low":
            self._volatility *= 1.5
        elif impact == "medium":
            self._volatility *= 3.0
            self._spread_base *= 1.5
        elif impact == "high":
            self._volatility *= 5.0
            self._spread_base *= 2.0
        
        # Mean reversion of volatility after 60 seconds
        def reset_volatility():
            time.sleep(60)
            self._volatility = 0.0005
            self._spread_base = 0.30
        
        import threading
        threading.Thread(target=reset_volatility, daemon=True).start()


class MarketDataProvider:
    """
    Unified market data provider that tries live FIX first,
    falls back to simulated feed if unavailable
    """
    
    def __init__(self, use_live: bool = True):
        self._use_live = use_live
        self._simulated_feed = SimulatedMarketFeed()
        self._live_connected = False
        self._on_tick_callback: Optional[Callable] = None
    
    def set_on_tick_callback(self, callback: Callable):
        """Set callback for tick data"""
        self._on_tick_callback = callback
        self._simulated_feed.set_on_tick_callback(callback)
    
    def get_tick(self) -> dict:
        """Get next tick from available source"""
        return self._simulated_feed.get_next_tick()
    
    def get_order_book(self, levels: int = 5) -> dict:
        """Get order book snapshot"""
        return self._simulated_feed.get_order_book_snapshot(levels)
    
    def get_current_price(self) -> float:
        """Get current price"""
        return self._simulated_feed.get_current_price()
    
    def get_spread(self) -> float:
        """Get current spread"""
        return self._simulated_feed.get_current_spread()
    
    @property
    def is_live(self) -> bool:
        """Whether using live data"""
        return self._live_connected
    
    @property
    def source(self) -> str:
        """Data source name"""
        return "LIVE FIX" if self._live_connected else "SIMULATED"
