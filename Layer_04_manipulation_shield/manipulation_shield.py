"""
LAYER 4: MANIPULATION SHIELD
Detects and rejects manipulated or fake data
"""

import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from sklearn.ensemble import IsolationForest
from collections import deque


@dataclass
class ManipulationResult:
    """Result of manipulation detection"""
    is_manipulated: bool = False
    anomaly_score: float = 0.0
    vpin: float = 0.0
    lee_ready_direction: int = 0  # -1: sell, 0: neutral, 1: buy
    stop_hunt_detected: bool = False
    fake_breakout_detected: bool = False
    spread_manipulation_detected: bool = False
    rejection_reason: str = ""


class ManipulationShield:
    """
    Layer 4: Manipulation Shield
    Detects and rejects manipulated or fake data
    """
    
    def __init__(
        self,
        vpin_threshold: float = 0.7,
        contamination: float = 0.1,
        window_size: int = 1000
    ):
        """
        Initialize Manipulation Shield
        
        Args:
            vpin_threshold: VPIN threshold for rejection
            contamination: Expected contamination ratio for IsolationForest
            window_size: Window size for rolling calculations
        """
        self.vpin_threshold = vpin_threshold
        self.contamination = contamination
        self.window_size = window_size
        
        # Isolation Forest for anomaly detection
        self.isolation_forest = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        
        # State tracking
        self._feature_buffer: deque = deque(maxlen=window_size)
        self._price_buffer: deque = deque(maxlen=window_size)
        self._volume_buffer: deque = deque(maxlen=window_size)
        self._spread_buffer: deque = deque(maxlen=window_size)
        self._is_fitted = False
        self._rejection_count = 0
        self._total_count = 0
        
    def detect(
        self,
        features: np.ndarray,
        price: float,
        volume: float,
        bid: float,
        ask: float
    ) -> ManipulationResult:
        """
        Detect manipulation in tick data
        
        Args:
            features: Feature vector (168 features)
            price: Current price
            volume: Current volume
            bid: Current bid
            ask: Current ask
            
        Returns:
            ManipulationResult with detection results
        """
        self._total_count += 1
        result = ManipulationResult()
        
        # Update buffers
        self._feature_buffer.append(features)
        self._price_buffer.append(price)
        self._volume_buffer.append(volume)
        spread = ask - bid
        self._spread_buffer.append(spread)
        
        # Fit Isolation Forest if enough data
        if len(self._feature_buffer) >= 100 and not self._is_fitted:
            self._fit_isolation_forest()
        
        # Check 1: IsolationForest anomaly detection
        if self._is_fitted and len(features) > 0:
            anomaly_score = self._check_anomaly(features)
            result.anomaly_score = anomaly_score
            if anomaly_score < -0.1:
                result.is_manipulated = True
                result.rejection_reason = "IsolationForest anomaly"
                self._rejection_count += 1
                return result
        
        # Check 2: VPIN (Volume-synchronized Probability of Informed Trading)
        vpin = self._compute_vpin()
        result.vpin = vpin
        if vpin > self.vpin_threshold:
            result.is_manipulated = True
            result.rejection_reason = f"VPIN {vpin:.3f} > {self.vpin_threshold}"
            self._rejection_count += 1
            return result
        
        # Check 3: Lee-Ready direction classifier
        lee_ready_dir = self._lee_ready_classifier(price, bid, ask)
        result.lee_ready_direction = lee_ready_dir
        
        # Check 4: Stop-hunt pattern detection
        stop_hunt = self._detect_stop_hunt()
        result.stop_hunt_detected = stop_hunt
        if stop_hunt:
            result.is_manipulated = True
            result.rejection_reason = "Stop-hunt pattern detected"
            self._rejection_count += 1
            return result
        
        # Check 5: Fake breakout validation
        fake_breakout = self._detect_fake_breakout()
        result.fake_breakout_detected = fake_breakout
        if fake_breakout:
            result.is_manipulated = True
            result.rejection_reason = "Fake breakout detected"
            self._rejection_count += 1
            return result
        
        # Check 6: Spread manipulation sensor
        spread_manip = self._detect_spread_manipulation()
        result.spread_manipulation_detected = spread_manip
        if spread_manip:
            result.is_manipulated = True
            result.rejection_reason = "Spread manipulation detected"
            self._rejection_count += 1
            return result
        
        return result
    
    def _fit_isolation_forest(self) -> None:
        """Fit Isolation Forest on buffered features"""
        if len(self._feature_buffer) < 100:
            return
        
        try:
            X = np.array(list(self._feature_buffer))
            # Handle NaN/Inf
            X = np.nan_to_num(X, nan=0.0, posinf=1e10, neginf=-1e10)
            self.isolation_forest.fit(X)
            self._is_fitted = True
        except Exception as e:
            print(f"[MANIPULATION SHIELD] IsolationForest fit failed: {e}")
    
    def _check_anomaly(self, features: np.ndarray) -> float:
        """Check if features are anomalous"""
        try:
            X = features.reshape(1, -1)
            X = np.nan_to_num(X, nan=0.0, posinf=1e10, neginf=-1e10)
            score = self.isolation_forest.score_samples(X)[0]
            return float(score)
        except Exception:
            return 0.0
    
    def _compute_vpin(self) -> float:
        """
        Compute VPIN (Volume-synchronized Probability of Informed Trading)
        
        Returns:
            VPIN value between 0 and 1
        """
        if len(self._volume_buffer) < 100:
            return 0.0
        
        volumes = np.array(self._volume_buffer)
        prices = np.array(self._price_buffer)
        
        # Classify trades as buyer-initiated or seller-initiated
        classifications = []
        for i in range(1, len(prices)):
            if prices[i] > prices[i-1]:
                classifications.append(1)  # Buyer-initiated
            elif prices[i] < prices[i-1]:
                classifications.append(-1)  # Seller-initiated
            else:
                classifications.append(0)  # Neutral
        
        classifications = np.array(classifications)
        
        # Compute VPIN
        n_buckets = 10
        bucket_size = len(volumes) // n_buckets
        
        if bucket_size == 0:
            return 0.0
        
        vpin_values = []
        for i in range(n_buckets):
            start = i * bucket_size
            end = start + bucket_size
            
            bucket_volumes = volumes[start:end]
            bucket_classifications = classifications[start:end]
            
            total_volume = np.sum(bucket_volumes)
            if total_volume == 0:
                continue
            
            # Buy volume and sell volume
            buy_volume = np.sum(bucket_volumes[bucket_classifications == 1])
            sell_volume = np.sum(bucket_volumes[bucket_classifications == -1])
            
            # VPIN for this bucket
            vpin_bucket = abs(buy_volume - sell_volume) / total_volume
            vpin_values.append(vpin_bucket)
        
        return float(np.mean(vpin_values)) if vpin_values else 0.0
    
    def _lee_ready_classifier(self, price: float, bid: float, ask: float) -> int:
        """
        Lee-Ready algorithm for trade classification
        
        Args:
            price: Trade price
            bid: Bid price
            ask: Ask price
            
        Returns:
            -1 for sell, 0 for neutral, 1 for buy
        """
        if bid <= 0 or ask <= 0:
            return 0
        
        mid = (bid + ask) / 2
        spread = ask - bid
        
        # Rule 1: If price is above midpoint, classify as buy
        if price > mid + spread * 0.1:
            return 1
        # Rule 2: If price is below midpoint, classify as sell
        elif price < mid - spread * 0.1:
            return -1
        # Rule 3: If price is at midpoint, use tick rule
        else:
            if len(self._price_buffer) >= 2:
                prev_price = self._price_buffer[-2]
                if price > prev_price:
                    return 1
                elif price < prev_price:
                    return -1
            return 0
    
    def _detect_stop_hunt(self) -> bool:
        """
        Detect stop-hunt pattern
        
        Returns:
            True if stop-hunt detected
        """
        if len(self._price_buffer) < 20:
            return False
        
        prices = np.array(self._price_buffer)
        
        # Look for sharp move followed by reversal
        recent = prices[-20:]
        max_price = np.max(recent)
        min_price = np.min(recent)
        current = prices[-1]
        
        # Check if price spiked and then reversed
        if len(prices) >= 3:
            # Spike up then down
            if (prices[-3] < max_price * 0.99 and 
                prices[-2] > max_price * 0.99 and 
                prices[-1] < prices[-2] * 0.99):
                return True
            
            # Spike down then up
            if (prices[-3] > min_price * 1.01 and 
                prices[-2] < min_price * 1.01 and 
                prices[-1] > prices[-2] * 1.01):
                return True
        
        return False
    
    def _detect_fake_breakout(self) -> bool:
        """
        Detect fake breakout pattern
        
        Returns:
            True if fake breakout detected
        """
        if len(self._price_buffer) < 50:
            return False
        
        prices = np.array(self._price_buffer)
        
        # Calculate support and resistance
        recent = prices[-50:]
        support = np.percentile(recent, 10)
        resistance = np.percentile(recent, 90)
        
        current = prices[-1]
        
        # Check for breakout that fails
        if len(prices) >= 3:
            # Breakout above resistance that fails
            if (prices[-2] > resistance and 
                prices[-1] < resistance and 
                prices[-3] < resistance):
                return True
            
            # Breakout below support that fails
            if (prices[-2] < support and 
                prices[-1] > support and 
                prices[-3] > support):
                return True
        
        return False
    
    def _detect_spread_manipulation(self) -> bool:
        """
        Detect spread manipulation
        
        Returns:
            True if spread manipulation detected
        """
        if len(self._spread_buffer) < 100:
            return False
        
        spreads = np.array(self._spread_buffer)
        
        # Check for abnormal spread expansion
        recent_spread = spreads[-10:]
        historical_spread = spreads[:-10]
        
        if len(historical_spread) == 0:
            return False
        
        recent_mean = np.mean(recent_spread)
        historical_mean = np.mean(historical_spread)
        historical_std = np.std(historical_spread)
        
        # If recent spread is significantly larger than historical
        if recent_mean > historical_mean + 3 * historical_std:
            return True
        
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get manipulation detection statistics"""
        rejection_rate = self._rejection_count / self._total_count if self._total_count > 0 else 0.0
        
        return {
            "total_checks": self._total_count,
            "rejections": self._rejection_count,
            "rejection_rate": rejection_rate,
            "is_fitted": self._is_fitted,
            "buffer_size": len(self._feature_buffer)
        }
    
    def reset(self) -> None:
        """Reset manipulation shield state"""
        self._feature_buffer.clear()
        self._price_buffer.clear()
        self._volume_buffer.clear()
        self._spread_buffer.clear()
        self._is_fitted = False
        self._rejection_count = 0
        self._total_count = 0