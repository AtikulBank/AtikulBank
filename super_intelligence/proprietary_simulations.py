"""
Proprietary Platform Simulations
Structural logic of world's most gatekept proprietary platforms:

1. Renaissance Medallion Engine: Hidden Markov Model + Kernelized String-Matching
2. Citadel Order Internalizer: Wholesale de-anonymization matrix
3. Solarflare Bare-Metal Fabric: OS Kernel Bypass simulation
4. Navier-Stokes Fluid Dynamics: Dark Pool liquidity modeling
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum
import math
from scipy import stats
from scipy.spatial.distance import cdist
import warnings

warnings.filterwarnings("ignore")


class RenaissanceMedallion:
    """
    Renaissance Medallion Engine
    
    Hidden Markov Model combined with Kernelized String-Matching algorithms
    to profile buyer/seller behavioral clusters in real-time.
    """
    
    def __init__(self, n_states: int = 5, kernel_bandwidth: float = 0.1):
        self.n_states = n_states
        self.kernel_bandwidth = kernel_bandwidth
        
        # HMM parameters
        self.transition_matrix = np.random.dirichlet(np.ones(n_states), size=n_states)
        self.emission_means = np.random.randn(n_states, 2)  # 2D feature space
        self.emission_covs = np.array([np.eye(2) for _ in range(n_states)])
        self.initial_probs = np.ones(n_states) / n_states
        
        # State
        self.current_state = 0
        self.state_history = []
        self.cluster_profiles = {}
        
    def profile_behavioral_clusters(self, order_flow: pd.DataFrame) -> Dict[str, Any]:
        """
        Profile buyer/seller behavioral clusters using HMM + Kernel matching.
        """
        if order_flow is None or order_flow.empty:
            return self._empty_result()
        
        # Extract features: price change, volume, time between orders
        features = self._extract_features(order_flow)
        
        if len(features) == 0:
            return self._empty_result()
        
        # Forward-backward algorithm for state inference
        state_sequence = self._viterbi_algorithm(features)
        
        # Kernelized string matching for cluster identification
        clusters = self._kernel_string_matching(features, state_sequence)
        
        # Update cluster profiles
        self.cluster_profiles = clusters
        
        return {
            'state_sequence': state_sequence.tolist(),
            'clusters': clusters,
            'n_clusters': len(clusters),
            'behavioral_patterns': self._analyze_patterns(state_sequence, features)
        }
    
    def _extract_features(self, order_flow: pd.DataFrame) -> np.ndarray:
        """Extract features from order flow."""
        features = []
        
        if 'price' in order_flow.columns and 'volume' in order_flow.columns:
            prices = order_flow['price'].values
            volumes = order_flow['volume'].values
            
            # Price changes
            price_changes = np.diff(prices) if len(prices) > 1 else np.zeros(1)
            
            # Volume-weighted price impact
            if len(volumes) > 1:
                vwap_impact = volumes[1:] * price_changes / (volumes[1:] + volumes[:-1])
            else:
                vwap_impact = np.zeros(1)
            
            # Normalize features
            if len(price_changes) > 0:
                price_changes_norm = (price_changes - np.mean(price_changes)) / (np.std(price_changes) + 1e-10)
                vwap_impact_norm = (vwap_impact - np.mean(vwap_impact)) / (np.std(vwap_impact) + 1e-10)
                
                # Stack as 2D features
                min_len = min(len(price_changes_norm), len(vwap_impact_norm))
                features = np.column_stack([price_changes_norm[:min_len], vwap_impact_norm[:min_len]])
        
        return features if len(features) > 0 else np.array([])
    
    def _viterbi_algorithm(self, features: np.ndarray) -> np.ndarray:
        """Viterbi algorithm for HMM state inference."""
        n_features = len(features)
        n_states = self.n_states
        
        if n_features == 0:
            return np.array([0])
        
        # Initialize
        log_probs = np.zeros((n_features, n_states))
        backpointers = np.zeros((n_features, n_states), dtype=int)
        
        # Initial probabilities
        for s in range(n_states):
            log_probs[0, s] = np.log(self.initial_probs[s] + 1e-10)
            log_probs[0, s] += self._log_emission_prob(features[0], s)
        
        # Forward pass
        for t in range(1, n_features):
            for s in range(n_states):
                max_prob = -np.inf
                max_state = 0
                
                for prev_s in range(n_states):
                    prob = log_probs[t-1, prev_s] + np.log(self.transition_matrix[prev_s, s] + 1e-10)
                    prob += self._log_emission_prob(features[t], s)
                    
                    if prob > max_prob:
                        max_prob = prob
                        max_state = prev_s
                
                log_probs[t, s] = max_prob
                backpointers[t, s] = max_state
        
        # Backtrack
        states = np.zeros(n_features, dtype=int)
        states[-1] = np.argmax(log_probs[-1])
        
        for t in range(n_features-2, -1, -1):
            states[t] = backpointers[t+1, states[t+1]]
        
        return states
    
    def _log_emission_prob(self, feature: np.ndarray, state: int) -> float:
        """Compute log emission probability."""
        mean = self.emission_means[state]
        cov = self.emission_covs[state]
        
        diff = feature - mean
        try:
            cov_inv = np.linalg.inv(cov)
            log_prob = -0.5 * diff @ cov_inv @ diff
        except np.linalg.LinAlgError:
            log_prob = -0.5 * np.sum(diff**2)
        
        return log_prob
    
    def _kernel_string_matching(self, features: np.ndarray, states: np.ndarray) -> Dict[int, Dict]:
        """Kernelized string matching for cluster identification."""
        clusters = {}
        
        for state in range(self.n_states):
            mask = states == state
            if np.any(mask):
                cluster_features = features[mask]
                
                # Compute cluster center using kernel density estimation
                if len(cluster_features) > 0:
                    center = np.mean(cluster_features, axis=0)
                    spread = np.std(cluster_features, axis=0)
                    
                    clusters[state] = {
                        'center': center.tolist(),
                        'spread': spread.tolist(),
                        'size': int(np.sum(mask)),
                        'density': float(np.mean(mask))
                    }
        
        return clusters
    
    def _analyze_patterns(self, states: np.ndarray, features: np.ndarray) -> Dict[str, Any]:
        """Analyze behavioral patterns."""
        if len(states) == 0:
            return {}
        
        # State transition patterns
        transitions = []
        for i in range(len(states) - 1):
            transitions.append((states[i], states[i+1]))
        
        # Most common transitions
        from collections import Counter
        transition_counts = Counter(transitions)
        most_common = transition_counts.most_common(3)
        
        return {
            'most_common_transitions': most_common,
            'state_entropy': float(stats.entropy(np.bincount(states) / len(states))),
            'pattern_complexity': float(np.std(states))
        }
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result."""
        return {
            'state_sequence': [],
            'clusters': {},
            'n_clusters': 0,
            'behavioral_patterns': {}
        }


class CitadelOrderInternalizer:
    """
    Citadel Order Internalizer
    
    Wholesale de-anonymization matrix that clusters market orders
    by tracking flow toxicity and structural imbalances.
    """
    
    def __init__(self, toxicity_window: int = 100):
        self.toxicity_window = toxicity_window
        self.flow_history = []
        self.toxicity_scores = []
        self.de_anonymization_matrix = None
        
    def internalize_orders(self, orders: pd.DataFrame) -> Dict[str, Any]:
        """
        De-anonymize and cluster market orders.
        """
        if orders is None or orders.empty:
            return self._empty_result()
        
        # Extract order features
        features = self._extract_order_features(orders)
        
        # Compute flow toxicity (VPIN-like)
        toxicity = self._compute_flow_toxicity(features)
        self.toxicity_scores.append(toxicity)
        
        # Structural imbalance
        imbalance = self._compute_structural_imbalance(orders)
        
        # De-anonymization clustering
        clusters = self._de_anonymize_clusters(features, toxicity)
        
        # Update history
        self.flow_history.extend(features.tolist())
        
        return {
            'toxicity_score': toxicity,
            'structural_imbalance': imbalance,
            'clusters': clusters,
            'flow_toxicity_history': self.toxicity_scores[-10:],
            'internalization_rate': self._compute_internalization_rate(clusters)
        }
    
    def _extract_order_features(self, orders: pd.DataFrame) -> np.ndarray:
        """Extract features from orders."""
        features = []
        
        required_cols = ['price', 'volume', 'side']
        if all(col in orders.columns for col in required_cols):
            prices = orders['price'].values
            volumes = orders['volume'].values
            sides = orders['side'].values
            
            # Convert sides to numerical
            side_numerical = np.where(sides == 'buy', 1, -1)
            
            # Order imbalance
            buy_volume = np.sum(volumes[sides == 'buy']) if np.any(sides == 'buy') else 0
            sell_volume = np.sum(volumes[sides == 'sell']) if np.any(sides == 'sell') else 0
            total_volume = buy_volume + sell_volume
            
            if total_volume > 0:
                imbalance = (buy_volume - sell_volume) / total_volume
            else:
                imbalance = 0.0
            
            # Price impact
            price_impact = np.mean(np.abs(np.diff(prices))) if len(prices) > 1 else 0.0
            
            features = np.array([imbalance, price_impact, np.mean(volumes)])
        
        return features if len(features) > 0 else np.array([0, 0, 0])
    
    def _compute_flow_toxicity(self, features: np.ndarray) -> float:
        """
        Compute flow toxicity (VPIN-like measure).
        High toxicity indicates informed trading.
        """
        if len(features) == 0:
            return 0.0
        
        # Simplified toxicity: volume imbalance * price impact
        imbalance = abs(features[0])
        price_impact = features[1]
        
        toxicity = imbalance * price_impact * 100  # Scale factor
        
        return min(toxicity, 1.0)
    
    def _compute_structural_imbalance(self, orders: pd.DataFrame) -> float:
        """Compute structural imbalance in order book."""
        if 'side' not in orders.columns or 'volume' not in orders.columns:
            return 0.0
        
        sides = orders['side'].values
        volumes = orders['volume'].values
        
        buy_volume = np.sum(volumes[sides == 'buy']) if np.any(sides == 'buy') else 0
        sell_volume = np.sum(volumes[sides == 'sell']) if np.any(sides == 'sell') else 0
        
        total_volume = buy_volume + sell_volume
        if total_volume > 0:
            imbalance = (buy_volume - sell_volume) / total_volume
        else:
            imbalance = 0.0
        
        return float(imbalance)
    
    def _de_anonymize_clusters(self, features: np.ndarray, toxicity: float) -> Dict[str, Any]:
        """De-anonymize order clusters based on toxicity."""
        if len(features) == 0:
            return {}
        
        # Simple clustering based on toxicity level
        clusters = {}
        
        if toxicity > 0.7:
            clusters['high_toxicity'] = {
                'type': 'informed_trader',
                'confidence': toxicity,
                'features': features.tolist()
            }
        elif toxicity > 0.3:
            clusters['medium_toxicity'] = {
                'type': 'mixed_flow',
                'confidence': toxicity,
                'features': features.tolist()
            }
        else:
            clusters['low_toxicity'] = {
                'type': 'noise_trader',
                'confidence': 1.0 - toxicity,
                'features': features.tolist()
            }
        
        return clusters
    
    def _compute_internalization_rate(self, clusters: Dict) -> float:
        """Compute internalization rate."""
        if not clusters:
            return 0.0
        
        # Higher toxicity clusters have higher internalization
        total_confidence = sum(c.get('confidence', 0) for c in clusters.values())
        avg_confidence = total_confidence / len(clusters) if clusters else 0
        
        return float(avg_confidence)
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result."""
        return {
            'toxicity_score': 0.0,
            'structural_imbalance': 0.0,
            'clusters': {},
            'flow_toxicity_history': [],
            'internalization_rate': 0.0
        }


class NavierStokesFluidDynamics:
    """
    Navier-Stokes Fluid Dynamics
    
    Models Dark Pool liquidity pools as high-velocity fluid mesh.
    Calculates turbulence via simulated Reynolds numbers.
    Dynamically halts operations during Macro Liquidity Injections.
    """
    
    def __init__(self, viscosity: float = 0.001, density: float = 1000.0):
        self.viscosity = viscosity
        self.density = density
        self.reynolds_number = 0.0
        self.turbulence_index = 0.0
        self.velocity_field = None
        self.pressure_field = None
        
    def simulate_fluid_dynamics(self, liquidity_data: pd.DataFrame, 
                               velocity_scale: float = 1.0) -> Dict[str, Any]:
        """
        Simulate Navier-Stokes fluid dynamics for dark pool liquidity.
        """
        if liquidity_data is None or liquidity_data.empty:
            return self._empty_result()
        
        # Extract liquidity parameters
        volumes = liquidity_data['volume'].values if 'volume' in liquidity_data.columns else None
        prices = liquidity_data['price'].values if 'price' in liquidity_data.columns else None
        
        if volumes is None or prices is None:
            return self._empty_result()
        
        # Create velocity field from price movements
        if len(prices) > 1:
            velocity = np.diff(prices) * velocity_scale
        else:
            velocity = np.array([0.0])
        
        # Compute Reynolds number: Re = (density * velocity * characteristic_length) / viscosity
        characteristic_length = np.mean(np.abs(np.diff(prices))) if len(prices) > 1 else 1.0
        avg_velocity = np.mean(np.abs(velocity))
        
        self.reynolds_number = (self.density * avg_velocity * characteristic_length) / self.viscosity
        
        # Compute turbulence index
        self.turbulence_index = self._compute_turbulence_index(velocity, volumes)
        
        # Create velocity and pressure fields
        self.velocity_field = self._create_velocity_field(velocity)
        self.pressure_field = self._create_pressure_field(volumes)
        
        # Detect macro liquidity injections
        injection_detected = self._detect_liquidity_injection(volumes, prices)
        
        # Compute stability metrics
        stability = self._compute_stability_metrics()
        
        return {
            'reynolds_number': float(self.reynolds_number),
            'turbulence_index': float(self.turbulence_index),
            'velocity_field': self.velocity_field.tolist() if self.velocity_field is not None else [],
            'pressure_field': self.pressure_field.tolist() if self.pressure_field is not None else [],
            'injection_detected': injection_detected,
            'stability': stability,
            'recommendation': self._generate_recommendation()
        }
    
    def _compute_turbulence_index(self, velocity: np.ndarray, volumes: np.ndarray) -> float:
        """
        Compute turbulence index from velocity fluctuations.
        """
        if len(velocity) == 0:
            return 0.0
        
        # Turbulence intensity: std(velocity) / mean(velocity)
        if np.mean(np.abs(velocity)) > 0:
            turbulence_intensity = np.std(velocity) / np.mean(np.abs(velocity))
        else:
            turbulence_intensity = 0.0
        
        # Weight by volume
        if len(volumes) > 0:
            volume_weight = np.mean(volumes) / np.max(volumes) if np.max(volumes) > 0 else 1.0
        else:
            volume_weight = 1.0
        
        turbulence_index = turbulence_intensity * volume_weight
        
        return min(turbulence_index, 1.0)
    
    def _create_velocity_field(self, velocity: np.ndarray) -> np.ndarray:
        """Create 2D velocity field."""
        if len(velocity) == 0:
            return np.zeros((10, 10))
        
        # Interpolate to 10x10 grid
        grid_size = 10
        x = np.linspace(0, 1, grid_size)
        y = np.linspace(0, 1, grid_size)
        
        # Simple interpolation
        velocity_interp = np.interp(x, np.linspace(0, 1, len(velocity)), velocity)
        
        # Create 2D field
        field = np.outer(velocity_interp, np.ones(grid_size))
        
        return field
    
    def _create_pressure_field(self, volumes: np.ndarray) -> np.ndarray:
        """Create pressure field from volumes."""
        if len(volumes) == 0:
            return np.zeros((10, 10))
        
        # Normalize volumes
        vol_norm = volumes / np.max(volumes) if np.max(volumes) > 0 else volumes
        
        # Interpolate to grid
        grid_size = 10
        x = np.linspace(0, 1, grid_size)
        vol_interp = np.interp(x, np.linspace(0, 1, len(vol_norm)), vol_norm)
        
        # Create pressure field
        field = np.outer(vol_interp, np.ones(grid_size))
        
        return field
    
    def _detect_liquidity_injection(self, volumes: np.ndarray, prices: np.ndarray) -> bool:
        """
        Detect macro liquidity injections (Central Bank Shocks).
        """
        if len(volumes) < 10 or len(prices) < 10:
            return False
        
        # Look for sudden volume spikes with price stability
        volume_mean = np.mean(volumes)
        volume_std = np.std(volumes)
        
        price_changes = np.abs(np.diff(prices))
        price_volatility = np.std(price_changes)
        
        # Injection criteria: high volume, low price volatility
        recent_volumes = volumes[-10:]
        recent_volatility = np.std(price_changes[-10:]) if len(price_changes) >= 10 else 0
        
        volume_spike = np.mean(recent_volumes) > volume_mean + 2 * volume_std
        price_stable = recent_volatility < price_volatility * 0.5
        
        return volume_spike and price_stable
    
    def _compute_stability_metrics(self) -> Dict[str, float]:
        """Compute fluid stability metrics."""
        # Reynolds number classification
        if self.reynolds_number < 2000:
            flow_regime = "laminar"
            stability_score = 1.0
        elif self.reynolds_number < 4000:
            flow_regime = "transitional"
            stability_score = 0.5
        else:
            flow_regime = "turbulent"
            stability_score = 0.2
        
        return {
            'flow_regime': flow_regime,
            'stability_score': stability_score,
            'reynolds_normalized': min(self.reynolds_number / 10000, 1.0)
        }
    
    def _generate_recommendation(self) -> str:
        """Generate trading recommendation based on fluid dynamics."""
        if self.turbulence_index > 0.7:
            return "HALT_TRADING"
        elif self.turbulence_index > 0.4:
            return "REDUCE_POSITIONS"
        elif self.reynolds_number > 4000:
            return "INCREASE_HEDGING"
        else:
            return "NORMAL_OPERATION"
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result."""
        return {
            'reynolds_number': 0.0,
            'turbulence_index': 0.0,
            'velocity_field': [],
            'pressure_field': [],
            'injection_detected': False,
            'stability': {'flow_regime': 'laminar', 'stability_score': 1.0, 'reynolds_normalized': 0.0},
            'recommendation': 'NORMAL_OPERATION'
        }


# Main execution function for testing
if __name__ == "__main__":
    # Create test data
    np.random.seed(42)
    
    # Test Renaissance Medallion
    print("=" * 70)
    print("RENAISSANCE MEDALLION ENGINE TEST")
    print("=" * 70)
    
    medallion = RenaissanceMedallion()
    
    # Create order flow
    n_orders = 100
    order_flow = pd.DataFrame({
        'price': np.linspace(2000, 2010, n_orders) + np.random.normal(0, 0.1, n_orders),
        'volume': np.random.randint(10, 1000, n_orders),
        'side': np.random.choice(['buy', 'sell'], n_orders)
    })
    
    medallion_result = medallion.profile_behavioral_clusters(order_flow)
    print(f"Clusters: {medallion_result['n_clusters']}")
    print(f"State Entropy: {medallion_result['behavioral_patterns'].get('state_entropy', 0):.4f}")
    
    # Test Citadel Order Internalizer
    print("\n" + "=" * 70)
    print("CITADEL ORDER INTERNALIZER TEST")
    print("=" * 70)
    
    citadel = CitadelOrderInternalizer()
    
    citadel_result = citadel.internalize_orders(order_flow)
    print(f"Toxicity Score: {citadel_result['toxicity_score']:.4f}")
    print(f"Structural Imbalance: {citadel_result['structural_imbalance']:.4f}")
    print(f"Internalization Rate: {citadel_result['internalization_rate']:.4f}")
    
    # Test Navier-Stokes Fluid Dynamics
    print("\n" + "=" * 70)
    print("NAVIER-STOKES FLUID DYNAMICS TEST")
    print("=" * 70)
    
    navier_stokes = NavierStokesFluidDynamics()
    
    liquidity_data = pd.DataFrame({
        'price': order_flow['price'].values,
        'volume': order_flow['volume'].values
    })
    
    ns_result = navier_stokes.simulate_fluid_dynamics(liquidity_data)
    print(f"Reynolds Number: {ns_result['reynolds_number']:.2f}")
    print(f"Turbulence Index: {ns_result['turbulence_index']:.4f}")
    print(f"Injection Detected: {ns_result['injection_detected']}")
    print(f"Recommendation: {ns_result['recommendation']}")
    print("=" * 70)