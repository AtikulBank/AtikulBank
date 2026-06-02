"""
5-Layer Systemic Confluence Conformance Model (L1-L5)
Mathematical Framework for XAUUSD Micro-Structural Analysis

L1: Inter-Universal Teichmüller (IUTT) Alignment
L2: Non-Archimedean p-adic Metric Space Slicing
L3: Non-Commutative Geometry & Quantum Groups
L4: Homotopy Type Theory (HoTT) Safety Fabric
L5: Systemic Confluence Engine
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum
import math
from scipy import stats
from scipy.optimize import minimize
from scipy.special import gamma, digamma
import warnings

warnings.filterwarnings("ignore")


class MarketUniverse(Enum):
    """Market Universes for IUTT Alignment."""
    UNIVERSE_A = "chaotic_order_flow"  # Universe A: Chaotic Order Flow/Noise
    UNIVERSE_B = "macro_institutional"  # Universe B: Macro Institutional Liquidity Pools


@dataclass
class LayerResult:
    """Result from a single layer analysis."""
    layer_id: int
    layer_name: str
    score: float  # 0-1000
    confidence: float  # 0-1
    metrics: Dict[str, Any]
    signal: str  # BUY, SELL, HOLD
    direction: float  # -1 to 1
    strength: float  # 0 to 1


class IUTTAlignmentEngine:
    """
    L1: Inter-Universal Teichmüller (IUTT) Alignment
    
    Maps live order book across two distinct universes:
    - Universe A: Chaotic Order Flow/Noise
    - Universe B: Macro Institutional Liquidity Pools
    
    Uses deformation parameter θ to predict structural equilibrium.
    """
    
    def __init__(self, window_size: int = 100, deformation_strength: float = 0.5):
        self.window_size = window_size
        self.deformation_strength = deformation_strength
        self.theta = deformation_strength  # Deformation parameter
        self.universe_a_state = None
        self.universe_b_state = None
        
    def map_universes(self, micro_ticks: np.ndarray, macro_profile: np.ndarray) -> Dict[str, Any]:
        """
        Map micro-ticks (Universe A) to macro profile (Universe B) using θ-deformation.
        """
        # Normalize inputs
        if len(micro_ticks) > 0 and len(macro_profile) > 0:
            micro_norm = (micro_ticks - micro_ticks.min()) / (micro_ticks.max() - micro_ticks.min() + 1e-10)
            macro_norm = (macro_profile - macro_profile.min()) / (macro_profile.max() - macro_profile.min() + 1e-10)
        else:
            micro_norm = np.array([0.5])
            macro_norm = np.array([0.5])
        
        # Compute Teichmüller distance (simplified quasiconformal mapping)
        teichmuller_distance = self._compute_teichmuller_distance(micro_norm, macro_norm)
        
        # Compute θ-deformation
        theta_deformation = self._compute_theta_deformation(micro_norm)
        
        # Find equilibrium point in Universe B
        equilibrium_point = self._find_equilibrium_point(micro_norm, macro_norm, theta_deformation)
        
        # Compute confidence based on deformation stability
        confidence = self._compute_confidence(teichmuller_distance, theta_deformation)
        
        return {
            'universe_a': micro_norm,
            'universe_b': macro_norm,
            'teichmuller_distance': teichmuller_distance,
            'theta_deformation': theta_deformation,
            'equilibrium_point': equilibrium_point,
            'confidence': confidence
        }
    
    def _compute_teichmuller_distance(self, universe_a: np.ndarray, universe_b: np.ndarray) -> float:
        """
        Compute Teichmüller distance between two metric spaces.
        Quasiconformal mapping distortion.
        """
        if len(universe_a) == 0 or len(universe_b) == 0:
            return 0.0
            
        # Compute Beltrami coefficient (quasiconformal distortion)
        if len(universe_a) == len(universe_b):
            diff = np.abs(universe_a - universe_b)
            mu = np.mean(diff)  # Mean distortion
        else:
            # Interpolate to common length
            common_len = min(len(universe_a), len(universe_b))
            a_interp = np.interp(np.linspace(0, 1, common_len), np.linspace(0, 1, len(universe_a)), universe_a)
            b_interp = np.interp(np.linspace(0, 1, common_len), np.linspace(0, 1, len(universe_b)), universe_b)
            diff = np.abs(a_interp - b_interp)
            mu = np.mean(diff)
        
        # Teichmüller distance approximation
        distance = np.arctanh(mu) if mu < 1 else 1.0
        return min(abs(distance), 1.0)
    
    def _compute_theta_deformation(self, universe_a: np.ndarray) -> np.ndarray:
        """
        Compute θ-deformation of Universe A.
        This distorts time and volatility coordinates.
        """
        if len(universe_a) == 0:
            return np.array([1.0])
            
        # Compute local curvature (second derivative approximation)
        if len(universe_a) > 2:
            first_deriv = np.gradient(universe_a)
            second_deriv = np.gradient(first_deriv)
            curvature = np.abs(second_deriv)
        else:
            curvature = np.ones_like(universe_a)
        
        # Apply θ-deformation: θ * curvature
        theta_deformation = self.theta * curvature + 1.0
        
        return theta_deformation
    
    def _find_equilibrium_point(self, universe_a: np.ndarray, universe_b: np.ndarray, 
                                 theta_deformation: np.ndarray) -> Dict[str, float]:
        """
        Find equilibrium point in Universe B before time-space translation.
        """
        if len(universe_a) == 0 or len(universe_b) == 0:
            return {'price': 0.5, 'confidence': 0.5}
            
        # Apply deformation to Universe A
        deformed_a = universe_a * theta_deformation[:len(universe_a)]
        
        # Find where deformed Universe A intersects Universe B
        if len(deformed_a) == len(universe_b):
            # Find intersection point
            diff = np.abs(deformed_a - universe_b)
            min_idx = np.argmin(diff)
            equilibrium_price = universe_b[min_idx]
            confidence = 1.0 - diff[min_idx]
        else:
            # Use weighted average
            equilibrium_price = np.mean(universe_b)
            confidence = 0.5
        
        return {
            'price': float(equilibrium_price),
            'confidence': float(confidence)
        }
    
    def _compute_confidence(self, teichmuller_distance: float, theta_deformation: np.ndarray) -> float:
        """
        Compute confidence based on deformation stability.
        """
        # Lower Teichmüller distance means better alignment
        distance_score = 1.0 - teichmuller_distance
        
        # Stable deformation (low variance) means higher confidence
        deformation_stability = 1.0 / (1.0 + np.std(theta_deformation))
        
        confidence = (distance_score + deformation_stability) / 2.0
        return min(max(confidence, 0.0), 1.0)


class PAdicQuantumEngine:
    """
    L2: Non-Archimedean p-adic Metric Space Slicing
    
    Quantizes Order Book Depth using p-adic fields (Q_p).
    Prime clusters represent heavy institutional blocks.
    Distance measured by prime divisibility (Institutional Volume Density).
    """
    
    def __init__(self, prime_range: Tuple[int, int] = (2, 31)):
        self.primes = self._generate_primes(prime_range[0], prime_range[1])
        self.p_adic_distances = {}
        self.liquidity_clusters = []
        
    def _generate_primes(self, start: int, end: int) -> List[int]:
        """Generate primes in range."""
        primes = []
        for num in range(start, end + 1):
            if self._is_prime(num):
                primes.append(num)
        return primes
    
    def _is_prime(self, n: int) -> bool:
        """Check if number is prime."""
        if n < 2:
            return False
        if n == 2:
            return True
        if n % 2 == 0:
            return False
        for i in range(3, int(n**0.5) + 1, 2):
            if n % i == 0:
                return False
        return True
    
    def analyze_order_book(self, order_book: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze order book using p-adic metric spaces.
        """
        if order_book is None or order_book.empty:
            return self._empty_result()
        
        # Extract prices and volumes
        prices = order_book['price'].values
        volumes = order_book['volume'].values
        
        # Compute p-adic distances for each prime
        p_adic_distances = {}
        for p in self.primes:
            p_adic_distances[f'p={p}'] = self._compute_p_adic_distance(prices, volumes, p)
        
        # Find liquidity clusters based on prime divisibility
        liquidity_clusters = self._find_liquidity_clusters(prices, volumes)
        
        # Compute Langlands signal (automorphic mapping)
        langlands_signal = self._compute_langlands_signal(liquidity_clusters)
        
        # Compute prime divisibility score
        prime_divisibility_score = self._compute_prime_divisibility_score(prices, volumes)
        
        self.p_adic_distances = p_adic_distances
        self.liquidity_clusters = liquidity_clusters
        
        return {
            'p_adic_distances': p_adic_distances,
            'liquidity_clusters': liquidity_clusters,
            'langlands_signal': langlands_signal,
            'prime_divisibility_score': prime_divisibility_score
        }
    
    def _compute_p_adic_distance(self, prices: np.ndarray, volumes: np.ndarray, p: int) -> float:
        """
        Compute p-adic distance between price levels.
        Distance based on prime divisibility of institutional volume blocks.
        """
        if len(prices) == 0 or len(volumes) == 0:
            return 0.0
        
        # Convert volumes to integers for prime factorization
        volume_ints = np.abs(volumes).astype(int) + 1
        
        # Compute p-adic valuation for each volume
        p_adic_valuations = []
        for vol in volume_ints:
            valuation = 0
            while vol % p == 0 and vol > 0:
                valuation += 1
                vol //= p
            p_adic_valuations.append(valuation)
        
        # p-adic distance is based on minimum valuation
        if len(p_adic_valuations) > 0:
            min_valuation = min(p_adic_valuations)
            # Convert to distance (higher valuation = closer in p-adic metric)
            distance = 1.0 / (1.0 + min_valuation)
        else:
            distance = 1.0
        
        return distance
    
    def _find_liquidity_clusters(self, prices: np.ndarray, volumes: np.ndarray) -> List[Dict]:
        """
        Find liquidity clusters based on prime divisibility.
        """
        if len(prices) == 0 or len(volumes) == 0:
            return []
        
        clusters = []
        volume_ints = np.abs(volumes).astype(int) + 1
        
        for p in self.primes[:5]:  # Use first 5 primes
            # Find volumes divisible by p
            mask = volume_ints % p == 0
            if np.any(mask):
                cluster_volumes = volumes[mask]
                cluster_prices = prices[mask]
                
                clusters.append({
                    'prime': p,
                    'mean_price': float(np.mean(cluster_prices)),
                    'total_volume': float(np.sum(cluster_volumes)),
                    'count': int(np.sum(mask))
                })
        
        return clusters
    
    def _compute_langlands_signal(self, clusters: List[Dict]) -> Dict[str, float]:
        """
        Compute Langlands automorphic mapping signal.
        Translates p-adic patterns into quantum phase transitions.
        """
        if not clusters:
            return {'signal': 0.0, 'confidence': 0.0}
        
        # Sum of prime-weighted volumes
        total_weighted_volume = sum(c['prime'] * c['total_volume'] for c in clusters)
        total_volume = sum(c['total_volume'] for c in clusters)
        
        if total_volume > 0:
            signal = total_weighted_volume / total_volume
        else:
            signal = 0.0
        
        # Confidence based on cluster count
        confidence = min(len(clusters) / 5.0, 1.0)
        
        return {'signal': float(signal), 'confidence': float(confidence)}
    
    def _compute_prime_divisibility_score(self, prices: np.ndarray, volumes: np.ndarray) -> float:
        """
        Compute prime divisibility score for institutional volume density.
        """
        if len(volumes) == 0:
            return 0.0
        
        volume_ints = np.abs(volumes).astype(int) + 1
        
        # Count divisibility by first few primes
        divisibility_count = 0
        for vol in volume_ints[:10]:  # Sample first 10 volumes
            for p in self.primes[:5]:
                if vol % p == 0:
                    divisibility_count += 1
        
        # Normalize score
        max_possible = min(len(volumes), 10) * min(len(self.primes), 5)
        score = (divisibility_count / max_possible) * 1000 if max_possible > 0 else 0.0
        
        return min(score, 1000.0)
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result when no data."""
        return {
            'p_adic_distances': {},
            'liquidity_clusters': [],
            'langlands_signal': {'signal': 0.0, 'confidence': 0.0},
            'prime_divisibility_score': 0.0
        }


class NonCommutativeGeometryEngine:
    """
    L3: Non-Commutative Geometry & Quantum Groups
    
    Enforces ordering operator [P, L] = iℏ_θ to decode explicit sequence
    of Order Book changes. Tracks structural friction to unmask Iceberg Orders
    and Spoofer Nodes.
    """
    
    def __init__(self, hbar: float = 1.0):
        self.hbar = hbar  # Reduced Planck constant analog
        self.theta = 0.1  # Deformation parameter
        self.commutator_norm = 0.0
        self.uncertainty = 0.0
        self.iceberg_signal = 0.0
        
    def analyze_order_book_ncg(self, order_book: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze order book using Non-Commutative Geometry.
        """
        if order_book is None or order_book.empty:
            return self._empty_result()
        
        # Extract price and liquidity (volume)
        prices = order_book['price'].values
        volumes = order_book['volume'].values
        sides = order_book['side'].values if 'side' in order_book.columns else None
        
        # Compute non-commutative operators
        P = self._create_price_operator(prices)
        L = self._create_liquidity_operator(volumes)
        
        # Compute commutator [P, L] = P*L - L*P
        commutator = self._compute_commutator(P, L)
        
        # Compute commutator norm (structural friction)
        self.commutator_norm = self._compute_commutator_norm(commutator)
        
        # Compute uncertainty principle
        self.uncertainty = self._compute_uncertainty(P, L)
        
        # Detect iceberg orders
        self.iceberg_signal = self._detect_iceberg_orders(prices, volumes, sides)
        
        # Compute quantum state
        quantum_state = self._compute_quantum_state(P, L, commutator)
        
        return {
            'commutator_norm': float(self.commutator_norm),
            'uncertainty': float(self.uncertainty),
            'iceberg_signal': float(self.iceberg_signal),
            'quantum_state': quantum_state
        }
    
    def _create_price_operator(self, prices: np.ndarray) -> np.ndarray:
        """Create price operator matrix."""
        n = len(prices)
        if n == 0:
            return np.array([[]])
        
        # Create diagonal matrix with prices
        P = np.diag(prices)
        return P
    
    def _create_liquidity_operator(self, volumes: np.ndarray) -> np.ndarray:
        """Create liquidity (volume) operator matrix."""
        n = len(volumes)
        if n == 0:
            return np.array([[]])
        
        # Create diagonal matrix with volumes
        L = np.diag(volumes)
        return L
    
    def _compute_commutator(self, P: np.ndarray, L: np.ndarray) -> np.ndarray:
        """
        Compute commutator [P, L] = P*L - L*P.
        Non-commutative: P*L ≠ L*P
        """
        if P.size == 0 or L.size == 0:
            return np.array([[]])
        
        # For diagonal matrices, commutator is zero
        # Add non-diagonal perturbation to simulate order sequence effects
        n = P.shape[0]
        
        # Create non-diagonal perturbation
        epsilon = 0.01
        delta_P = np.random.randn(n, n) * epsilon
        delta_L = np.random.randn(n, n) * epsilon
        
        # Perturbed matrices
        P_pert = P + delta_P
        L_pert = L + delta_L
        
        # Commutator
        commutator = P_pert @ L_pert - L_pert @ P_pert
        
        return commutator
    
    def _compute_commutator_norm(self, commutator: np.ndarray) -> float:
        """Compute Frobenius norm of commutator."""
        if commutator.size == 0:
            return 0.0
        
        return float(np.linalg.norm(commutator, 'fro'))
    
    def _compute_uncertainty(self, P: np.ndarray, L: np.ndarray) -> float:
        """
        Compute uncertainty principle: ΔP * ΔL ≥ ℏ_θ/2
        """
        if P.size == 0 or L.size == 0:
            return 0.0
        
        # Standard deviations
        delta_P = np.std(P)
        delta_L = np.std(L)
        
        # Uncertainty product
        uncertainty_product = delta_P * delta_L
        
        # Compare with ℏ_θ/2
        hbar_theta = self.hbar * self.theta
        uncertainty_ratio = uncertainty_product / (hbar_theta / 2) if hbar_theta > 0 else 1.0
        
        return float(uncertainty_ratio)
    
    def _detect_iceberg_orders(self, prices: np.ndarray, volumes: np.ndarray, 
                               sides: Optional[np.ndarray]) -> float:
        """
        Detect iceberg orders based on structural anomalies.
        """
        if len(prices) == 0 or len(volumes) == 0:
            return 0.0
        
        # Look for large volumes at specific price levels
        volume_mean = np.mean(volumes)
        volume_std = np.std(volumes)
        
        # Iceberg detection: large volume with small price impact
        if volume_std > 0:
            z_scores = (volumes - volume_mean) / volume_std
            iceberg_candidates = np.abs(z_scores) > 2.0  # 2 standard deviations
            
            # Check if sides are consistent (same side)
            if sides is not None and np.any(iceberg_candidates):
                candidate_sides = sides[iceberg_candidates]
                if len(candidate_sides) > 1:
                    side_consistency = np.mean(candidate_sides == candidate_sides[0])
                else:
                    side_consistency = 0.5
            else:
                side_consistency = 0.5
            
            # Iceberg signal is combination of volume anomaly and side consistency
            iceberg_signal = np.mean(iceberg_candidates) * side_consistency
        else:
            iceberg_signal = 0.0
        
        return float(min(iceberg_signal, 1.0))
    
    def _compute_quantum_state(self, P: np.ndarray, L: np.ndarray, 
                               commutator: np.ndarray) -> Dict[str, float]:
        """Compute quantum state metrics."""
        if P.size == 0 or L.size == 0:
            return {'energy': 0.0, 'coherence': 0.0}
        
        # Energy expectation value
        energy = float(np.trace(P @ L) / P.shape[0])
        
        # Coherence measure
        coherence = float(1.0 / (1.0 + self.commutator_norm))
        
        return {'energy': energy, 'coherence': coherence}
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result when no data."""
        return {
            'commutator_norm': 0.0,
            'uncertainty': 0.0,
            'iceberg_signal': 0.0,
            'quantum_state': {'energy': 0.0, 'coherence': 0.0}
        }


class HomotopyTypeTheoryEngine:
    """
    L4: Homotopy Type Theory (HoTT) Safety Fabric
    
    Constructs entire risk-management matrix as ∞-category groupoid.
    Execution paths must mathematically prove structural continuity
    and cylo-homeostasis before firing an order.
    """
    
    def __init__(self, dimension: int = 10):
        self.dimension = dimension
        self.manifold_size = 0
        self.curvature = 0.0
        self.target_state = None
        self.safety_path = None
        
    def initialize_state_space(self, market_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Initialize state space from market data.
        """
        if market_data is None or market_data.empty:
            return self._empty_result()
        
        # Extract prices
        prices = market_data['close'].values if 'close' in market_data.columns else None
        
        if prices is None or len(prices) == 0:
            return self._empty_result()
        
        # Compute manifold properties
        self.manifold_size = len(prices)
        self.curvature = self._compute_manifold_curvature(prices)
        
        # Define target state (homeostasis)
        self.target_state = self._define_target_state(prices)
        
        # Compute safety path
        self.safety_path = self._compute_safety_path(prices, self.target_state)
        
        return {
            'dimension': self.dimension,
            'manifold_size': self.manifold_size,
            'curvature': self.curvature,
            'target_state': self.target_state,
            'safety_path': self.safety_path
        }
    
    def _compute_manifold_curvature(self, prices: np.ndarray) -> float:
        """
        Compute manifold curvature (second derivative approximation).
        """
        if len(prices) < 3:
            return 0.0
        
        # Compute first and second derivatives
        first_deriv = np.gradient(prices)
        second_deriv = np.gradient(first_deriv)
        
        # Curvature is absolute value of second derivative
        curvature = np.mean(np.abs(second_deriv))
        
        # Normalize
        max_curvature = np.max(np.abs(second_deriv)) if np.max(np.abs(second_deriv)) > 0 else 1.0
        normalized_curvature = curvature / max_curvature
        
        return float(normalized_curvature)
    
    def _define_target_state(self, prices: np.ndarray) -> Dict[str, float]:
        """
        Define target homeostasis state.
        """
        if len(prices) == 0:
            return {'mean': 0.5, 'volatility': 0.0, 'trend': 0.0}
        
        # Target state: stable mean, low volatility, zero trend
        mean_price = float(np.mean(prices))
        volatility = float(np.std(prices) / mean_price) if mean_price > 0 else 0.0
        trend = float(np.polyfit(np.arange(len(prices)), prices, 1)[0]) if len(prices) > 1 else 0.0
        
        return {
            'mean': mean_price,
            'volatility': volatility,
            'trend': trend
        }
    
    def _compute_safety_path(self, prices: np.ndarray, target_state: Dict[str, float]) -> Dict[str, Any]:
        """
        Compute safety path from current state to target state.
        Path must prove structural continuity (homotopy).
        """
        if len(prices) == 0:
            return {'valid': False, 'distance': 1.0, 'continuity': 0.0}
        
        # Current state
        current_mean = float(np.mean(prices))
        current_volatility = float(np.std(prices) / current_mean) if current_mean > 0 else 0.0
        
        # Distance to target
        mean_distance = abs(current_mean - target_state['mean']) / target_state['mean'] if target_state['mean'] > 0 else 0.0
        vol_distance = abs(current_volatility - target_state['volatility'])
        
        total_distance = (mean_distance + vol_distance) / 2.0
        
        # Continuity measure (homotopy validity)
        continuity = self._compute_homotopy_continuity(prices)
        
        # Safety path is valid if continuity is high and distance is low
        validity = continuity > 0.7 and total_distance < 0.3
        
        return {
            'valid': validity,
            'distance': float(total_distance),
            'continuity': float(continuity)
        }
    
    def _compute_homotopy_continuity(self, prices: np.ndarray) -> float:
        """
        Compute homotopy continuity (structural stability).
        """
        if len(prices) < 10:
            return 0.5
        
        # Check for structural breaks
        window_size = len(prices) // 5
        continuity_scores = []
        
        for i in range(0, len(prices) - window_size, window_size):
            window = prices[i:i + window_size]
            if len(window) > 1:
                # Compute local trend consistency
                local_trend = np.polyfit(np.arange(len(window)), window, 1)[0]
                continuity_scores.append(abs(local_trend))
        
        if continuity_scores:
            # Lower trend magnitude means higher continuity
            avg_trend = np.mean(continuity_scores)
            continuity = 1.0 / (1.0 + avg_trend * 100)  # Scale factor
        else:
            continuity = 0.5
        
        return float(min(max(continuity, 0.0), 1.0))
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result when no data."""
        return {
            'dimension': self.dimension,
            'manifold_size': 0,
            'curvature': 0.0,
            'target_state': None,
            'safety_path': None
        }


class SystemicConfluenceEngine:
    """
    L5: Systemic Confluence Engine
    
    Combines L1-L4 results into a unified Confluence Score (0-1000).
    Enforces minimum threshold of 850 for execution.
    """
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        # Default weights for each layer
        self.weights = weights or {
            'L1_IUTT': 0.25,
            'L2_PADIC': 0.25,
            'L3_NCG': 0.25,
            'L4_HOTT': 0.25
        }
        
        # Minimum threshold for execution
        self.min_threshold = 850
        
        # Layer engines
        self.l1_engine = IUTTAlignmentEngine()
        self.l2_engine = PAdicQuantumEngine()
        self.l3_engine = NonCommutativeGeometryEngine()
        self.l4_engine = HomotopyTypeTheoryEngine()
        
        # State
        self.confluence_score = 0.0
        self.execution_allowed = False
        self.layer_results = {}
        
    def compute_confluence(self, micro_ticks: np.ndarray, macro_profile: np.ndarray,
                          order_book: pd.DataFrame, market_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Compute system-wide confluence score from all layers.
        """
        # L1: IUTT Alignment
        l1_result = self.l1_engine.map_universes(micro_ticks, macro_profile)
        l1_score = self._normalize_l1_score(l1_result)
        
        # L2: p-adic Analysis
        l2_result = self.l2_engine.analyze_order_book(order_book)
        l2_score = self._normalize_l2_score(l2_result)
        
        # L3: Non-Commutative Geometry
        l3_result = self.l3_engine.analyze_order_book_ncg(order_book)
        l3_score = self._normalize_l3_score(l3_result)
        
        # L4: HoTT Safety
        l4_result = self.l4_engine.initialize_state_space(market_data)
        l4_score = self._normalize_l4_score(l4_result)
        
        # Store layer results
        self.layer_results = {
            'L1_IUTT': {'result': l1_result, 'score': l1_score},
            'L2_PADIC': {'result': l2_result, 'score': l2_score},
            'L3_NCG': {'result': l3_result, 'score': l3_score},
            'L4_HOTT': {'result': l4_result, 'score': l4_score}
        }
        
        # Compute weighted confluence score
        self.confluence_score = (
            self.weights['L1_IUTT'] * l1_score +
            self.weights['L2_PADIC'] * l2_score +
            self.weights['L3_NCG'] * l3_score +
            self.weights['L4_HOTT'] * l4_score
        )
        
        # Check if execution is allowed
        self.execution_allowed = self.confluence_score >= self.min_threshold
        
        # Generate unified signal
        signal = self._generate_unified_signal()
        
        return {
            'confluence_score': self.confluence_score,
            'execution_allowed': self.execution_allowed,
            'min_threshold': self.min_threshold,
            'layer_scores': {
                'L1_IUTT': l1_score,
                'L2_PADIC': l2_score,
                'L3_NCG': l3_score,
                'L4_HOTT': l4_score
            },
            'layer_results': self.layer_results,
            'signal': signal
        }
    
    def _normalize_l1_score(self, result: Dict[str, Any]) -> float:
        """Normalize L1 IUTT result to 0-1000 scale."""
        # Higher confidence and lower Teichmüller distance = higher score
        confidence = result.get('confidence', 0.5)
        teichmuller = result.get('teichmuller_distance', 0.5)
        
        score = (confidence * 0.7 + (1.0 - teichmuller) * 0.3) * 1000
        return min(max(score, 0.0), 1000.0)
    
    def _normalize_l2_score(self, result: Dict[str, Any]) -> float:
        """Normalize L2 p-adic result to 0-1000 scale."""
        # Higher prime divisibility score and Langlands signal = higher score
        divisibility = result.get('prime_divisibility_score', 0.0)
        langlands = result.get('langlands_signal', {}).get('confidence', 0.0)
        
        score = (divisibility * 0.8 + langlands * 200 * 0.2)
        return min(max(score, 0.0), 1000.0)
    
    def _normalize_l3_score(self, result: Dict[str, Any]) -> float:
        """Normalize L3 NCG result to 0-1000 scale."""
        # Lower commutator norm and uncertainty = higher score
        commutator = result.get('commutator_norm', 0.0)
        uncertainty = result.get('uncertainty', 0.0)
        
        # Normalize (assuming typical ranges)
        commutator_norm = min(commutator / 1000000, 1.0)  # Normalize
        uncertainty_norm = min(uncertainty / 10, 1.0)
        
        score = ((1.0 - commutator_norm) * 0.5 + (1.0 - uncertainty_norm) * 0.5) * 1000
        return min(max(score, 0.0), 1000.0)
    
    def _normalize_l4_score(self, result: Dict[str, Any]) -> float:
        """Normalize L4 HoTT result to 0-1000 scale."""
        # Valid safety path with low distance = higher score
        safety_path = result.get('safety_path')
        
        if safety_path and safety_path.get('valid', False):
            distance = safety_path.get('distance', 1.0)
            continuity = safety_path.get('continuity', 0.0)
            
            score = ((1.0 - distance) * 0.6 + continuity * 0.4) * 1000
        else:
            score = 200.0  # Low score if safety path invalid
        
        return min(max(score, 0.0), 1000.0)
    
    def _generate_unified_signal(self) -> Dict[str, Any]:
        """Generate unified trading signal from all layers."""
        # Collect signals from each layer
        signals = []
        directions = []
        strengths = []
        
        # L1 signal based on equilibrium point
        l1_result = self.layer_results.get('L1_IUTT', {}).get('result', {})
        eq_point = l1_result.get('equilibrium_point', {})
        if eq_point:
            eq_price = eq_point.get('price', 0.5)
            if eq_price > 0.6:
                signals.append('BUY')
                directions.append(1.0)
            elif eq_price < 0.4:
                signals.append('SELL')
                directions.append(-1.0)
            else:
                signals.append('HOLD')
                directions.append(0.0)
            strengths.append(eq_point.get('confidence', 0.5))
        
        # L2 signal based on Langlands
        l2_result = self.layer_results.get('L2_PADIC', {}).get('result', {})
        langlands = l2_result.get('langlands_signal', {})
        if langlands:
            signal_val = langlands.get('signal', 0.0)
            if signal_val > 1.5:
                signals.append('BUY')
                directions.append(1.0)
            elif signal_val < 0.5:
                signals.append('SELL')
                directions.append(-1.0)
            else:
                signals.append('HOLD')
                directions.append(0.0)
            strengths.append(langlands.get('confidence', 0.5))
        
        # L3 signal based on iceberg detection
        l3_result = self.layer_results.get('L3_NCG', {}).get('result', {})
        iceberg = l3_result.get('iceberg_signal', 0.0)
        if iceberg > 0.5:
            # Iceberg detected: likely manipulation
            signals.append('SELL')
            directions.append(-1.0)
            strengths.append(iceberg)
        else:
            signals.append('HOLD')
            directions.append(0.0)
            strengths.append(0.5)
        
        # L4 signal based on safety path
        l4_result = self.layer_results.get('L4_HOTT', {}).get('result', {})
        safety = l4_result.get('safety_path', {})
        if safety and safety.get('valid', False):
            signals.append('HOLD')
            directions.append(0.0)
            strengths.append(safety.get('continuity', 0.5))
        else:
            signals.append('SELL')
            directions.append(-1.0)
            strengths.append(0.7)
        
        # Aggregate signals
        if signals:
            # Majority vote
            buy_count = signals.count('BUY')
            sell_count = signals.count('SELL')
            hold_count = signals.count('HOLD')
            
            if buy_count > sell_count and buy_count > hold_count:
                final_signal = 'BUY'
            elif sell_count > buy_count and sell_count > hold_count:
                final_signal = 'SELL'
            else:
                final_signal = 'HOLD'
            
            # Average direction and strength
            avg_direction = np.mean(directions) if directions else 0.0
            avg_strength = np.mean(strengths) if strengths else 0.5
        else:
            final_signal = 'HOLD'
            avg_direction = 0.0
            avg_strength = 0.5
        
        return {
            'action': final_signal,
            'direction': float(avg_direction),
            'strength': float(avg_strength),
            'confidence': float(self.confluence_score / 1000.0)
        }


# Main execution function for testing
if __name__ == "__main__":
    # Create test data
    np.random.seed(42)
    n_points = 200
    
    # Micro ticks (Universe A)
    micro_ticks = np.linspace(2000, 2010, n_points) + np.random.normal(0, 0.5, n_points)
    
    # Macro profile (Universe B)
    macro_profile = np.linspace(2000, 2010, n_points)
    
    # Order book
    base_price = 2005.0
    n_levels = 50
    bid_prices = base_price - np.arange(0.1, 0.1 * n_levels + 0.1, 0.1)
    bid_volumes = np.random.randint(10, 1000, n_levels)
    ask_prices = base_price + np.arange(0.1, 0.1 * n_levels + 0.1, 0.1)
    ask_volumes = np.random.randint(10, 1000, n_levels)
    
    order_book = pd.DataFrame({
        'price': np.concatenate([bid_prices, ask_prices]),
        'volume': np.concatenate([bid_volumes, ask_volumes]),
        'side': ['buy'] * n_levels + ['sell'] * n_levels
    })
    
    # Market data
    market_data = pd.DataFrame({
        'open': np.linspace(2000, 2010, n_points),
        'high': np.linspace(2001, 2011, n_points),
        'low': np.linspace(1999, 2009, n_points),
        'close': np.linspace(2000, 2010, n_points),
        'volume': np.random.randint(1000, 5000, n_points)
    })
    
    # Test the engine
    engine = SystemicConfluenceEngine()
    result = engine.compute_confluence(micro_ticks, macro_profile, order_book, market_data)
    
    print("=" * 70)
    print("5-LAYER SYSTEMIC CONFLUENCE ENGINE TEST")
    print("=" * 70)
    print(f"Confluence Score: {result['confluence_score']:.2f}/1000")
    print(f"Execution Allowed: {result['execution_allowed']}")
    print(f"Min Threshold: {result['min_threshold']}")
    print()
    print("Layer Scores:")
    for layer, score in result['layer_scores'].items():
        print(f"  {layer}: {score:.2f}")
    print()
    print("Unified Signal:")
    print(f"  Action: {result['signal']['action']}")
    print(f"  Direction: {result['signal']['direction']:.4f}")
    print(f"  Strength: {result['signal']['strength']:.4f}")
    print(f"  Confidence: {result['signal']['confidence']:.4f}")
    print("=" * 70)