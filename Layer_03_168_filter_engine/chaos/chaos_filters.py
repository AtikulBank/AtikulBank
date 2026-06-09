"""
CHAOS FILTERS (5)
Lyapunov exponent, Correlation dimension, Kolmogorov-Sinai entropy,
Strange attractor dimension, Lorenz fit
"""

import numpy as np
from typing import Dict, Any


class ChaosFilters:
    """
    Chaos theory based filters for market analysis
    """
    
    def compute(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        Compute all chaos filters
        
        Args:
            data: Dictionary containing prices, volumes, timestamps
            
        Returns:
            Dictionary of chaos features
        """
        prices = data.get("prices", np.array([]))
        
        if len(prices) < 100:
            return self._default_features()
        
        features = {}
        
        # F122: Lyapunov exponent
        features["lyapunov"] = self._compute_lyapunov(prices)
        
        # F123: Correlation dimension
        features["corr_dim"] = self._compute_correlation_dimension(prices)
        
        # F124: Kolmogorov-Sinai entropy
        features["ks_entropy"] = self._compute_ks_entropy(prices)
        
        # F125: Strange attractor dimension
        features["strange_attractor"] = self._compute_strange_attractor(prices)
        
        # F126: Lorenz fit
        features["lorenz_fit"] = self._compute_lorenz_fit(prices)
        
        return features
    
    def _compute_lyapunov(self, prices: np.ndarray, lag: int = 1) -> float:
        """
        Compute maximum Lyapunov exponent
        
        Args:
            prices: Price series
            lag: Time lag
            
        Returns:
            Lyapunov exponent
        """
        n = len(prices)
        if n < 100:
            return 0.0
        
        # Compute divergence of nearby trajectories
        divs = []
        for i in range(n - 2 * lag):
            d0 = abs(prices[i] - prices[i + lag])
            if d0 > 1e-10:
                d1 = abs(prices[i + lag] - prices[i + 2 * lag])
                if d1 > 1e-10:
                    divs.append(np.log(d1 / d0))
        
        return float(np.mean(divs)) if divs else 0.0
    
    def _compute_correlation_dimension(self, prices: np.ndarray, m: int = 2, tau: int = 1) -> float:
        """
        Compute correlation dimension using Grassberger-Procaccia algorithm
        
        Args:
            prices: Price series
            m: Embedding dimension
            tau: Time delay
            
        Returns:
            Correlation dimension
        """
        n = len(prices)
        if n < 100:
            return 1.5
        
        # Create embedding vectors
        vectors = []
        for i in range(n - (m - 1) * tau):
            vec = [prices[i + j * tau] for j in range(m)]
            vectors.append(vec)
        
        vectors = np.array(vectors)
        N = len(vectors)
        
        # Compute distances
        distances = []
        for i in range(N):
            for j in range(i + 1, min(N, i + 100)):  # Limit for efficiency
                dist = np.linalg.norm(vectors[i] - vectors[j])
                if dist > 0:
                    distances.append(dist)
        
        if not distances:
            return 1.5
        
        # Compute correlation integral at different scales
        r_values = np.logspace(-2, 0, 10) * np.std(distances)
        C_r = []
        
        for r in r_values:
            count = sum(1 for d in distances if d < r)
            C_r.append(count / len(distances))
        
        # Fit power law
        log_r = np.log(r_values)
        log_C = np.log(np.array(C_r) + 1e-10)
        
        # Linear fit
        coeffs = np.polyfit(log_r, log_C, 1)
        return float(coeffs[0])
    
    def _compute_ks_entropy(self, prices: np.ndarray, bins: int = 10) -> float:
        """
        Compute Kolmogorov-Sinai entropy
        
        Args:
            prices: Price series
            bins: Number of bins for histogram
            
        Returns:
            KS entropy
        """
        n = len(prices)
        if n < 100:
            return 0.5
        
        # Normalize prices
        normalized = (prices - np.mean(prices)) / (np.std(prices) + 1e-10)
        
        # Create symbolic sequence
        hist, _ = np.histogram(normalized, bins=bins)
        probs = hist / np.sum(hist)
        
        # Remove zero probabilities
        probs = probs[probs > 0]
        
        # Compute entropy
        entropy = -np.sum(probs * np.log2(probs))
        
        # Normalize
        max_entropy = np.log2(bins)
        return float(entropy / max_entropy) if max_entropy > 0 else 0.5
    
    def _compute_strange_attractor(self, prices: np.ndarray, m: int = 3, tau: int = 5) -> float:
        """
        Compute strange attractor dimension
        
        Args:
            prices: Price series
            m: Embedding dimension
            tau: Time delay
            
        Returns:
            Strange attractor dimension
        """
        n = len(prices)
        if n < 100:
            return 2.0
        
        # Create embedding
        vectors = []
        for i in range(n - (m - 1) * tau):
            vec = [prices[i + j * tau] for j in range(m)]
            vectors.append(vec)
        
        vectors = np.array(vectors)
        
        # Compute box-counting dimension
        scales = np.logspace(0.5, 2, 10)
        counts = []
        
        for scale in scales:
            # Box counting
            boxes = set()
            for vec in vectors:
                box = tuple((vec / scale).astype(int))
                boxes.add(box)
            counts.append(len(boxes))
        
        # Fit power law
        log_scales = np.log(scales)
        log_counts = np.log(np.array(counts) + 1)
        
        coeffs = np.polyfit(log_scales, log_counts, 1)
        return float(-coeffs[0])
    
    def _compute_lorenz_fit(self, prices: np.ndarray) -> float:
        """
        Compute Lorenz system fit quality
        
        Args:
            prices: Price series
            
        Returns:
            Lorenz fit quality (0-1)
        """
        n = len(prices)
        if n < 100:
            return 0.5
        
        # Normalize prices
        normalized = (prices - np.mean(prices)) / (np.std(prices) + 1e-10)
        
        # Simple Lorenz-like model: dx/dt = sigma*(y-x), dy/dt = x*(rho-z)-y, dz/dt = x*y - beta*z
        # Use simplified version for fitting
        sigma, rho, beta = 10.0, 28.0, 8.0/3.0
        dt = 0.01
        
        # Simulate Lorenz system
        x, y, z = normalized[0], 0.0, 0.0
        lorenz_x = [x]
        
        for i in range(min(n-1, 1000)):
            dx = sigma * (y - x) * dt
            dy = (x * (rho - z) - y) * dt
            dz = (x * y - beta * z) * dt
            x += dx
            y += dy
            z += dz
            lorenz_x.append(x)
        
        # Compare with actual prices
        lorenz_x = np.array(lorenz_x[:n])
        correlation = np.corrcoef(normalized[:len(lorenz_x)], lorenz_x)[0, 1]
        
        return float(abs(correlation)) if not np.isnan(correlation) else 0.5
    
    def _default_features(self) -> Dict[str, float]:
        """Return default features when data is insufficient"""
        return {
            "lyapunov": 0.0,
            "corr_dim": 1.5,
            "ks_entropy": 0.5,
            "strange_attractor": 2.0,
            "lorenz_fit": 0.5
        }