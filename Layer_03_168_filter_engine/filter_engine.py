"""
LAYER 3: 168-FILTER PARALLEL ENGINE
Main engine that coordinates all 15 filter groups
"""

import numpy as np
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Import all filter groups
from .chaos import ChaosFilters
from .quantum import QuantumFilters
from .thermo import ThermoFilters
from .topology import TopologyFilters
from .fluid import FluidFilters
from .tensor import TensorFilters
from .ito import ItoFilters
from .riemann import RiemannFilters
from .feynman import FeynmanFilters
from .info import InfoFilters
from .spectral import SpectralFilters
from .wavelet import WaveletFilters
from .price_action import PriceActionFilters
from .momentum import MomentumFilters
from .volatility import VolatilityFilters
from .statistical import StatisticalFilters
from .timeseries import TimeSeriesFilters
from .orderbook import OrderBookFilters
from .risk import RiskFilters
from .copula import CopulaFilters
from .hmm import HMMFilters
from .kalman_adv import KalmanAdvFilters
from .velocity import VelocityFilters


@dataclass
class FilterOutput:
    """Output from a filter group"""
    group_name: str
    features: Dict[str, float] = field(default_factory=dict)
    computation_time_ms: float = 0.0
    is_valid: bool = True


class FilterEngine:
    """
    Layer 3: 168-Filter Parallel Engine
    Coordinates all 15 filter groups for comprehensive market analysis
    """
    
    def __init__(self, n_workers: int = 8):
        """
        Initialize Filter Engine
        
        Args:
            n_workers: Number of parallel workers
        """
        self.n_workers = n_workers
        
        # Initialize all filter groups
        self.filters = {
            "chaos": ChaosFilters(),
            "quantum": QuantumFilters(),
            "thermo": ThermoFilters(),
            "topology": TopologyFilters(),
            "fluid": FluidFilters(),
            "tensor": TensorFilters(),
            "ito": ItoFilters(),
            "riemann": RiemannFilters(),
            "feynman": FeynmanFilters(),
            "info": InfoFilters(),
            "spectral": SpectralFilters(),
            "wavelet": WaveletFilters(),
            "price_action": PriceActionFilters(),
            "momentum": MomentumFilters(),
            "volatility": VolatilityFilters(),
            "statistical": StatisticalFilters(),
            "timeseries": TimeSeriesFilters(),
            "orderbook": OrderBookFilters(),
            "risk": RiskFilters(),
            "copula": CopulaFilters(),
            "hmm": HMMFilters(),
            "kalman_adv": KalmanAdvFilters(),
            "velocity": VelocityFilters()
        }
        
        # Thread pool for parallel execution
        self.executor = ThreadPoolExecutor(max_workers=n_workers)
        
        # Statistics
        self.total_filters = 168
        self.last_computation_time = 0.0
        
    def compute_all(
        self,
        prices: np.ndarray,
        volumes: np.ndarray,
        timestamps: np.ndarray,
        bid: float = 0.0,
        ask: float = 0.0
    ) -> Dict[str, Any]:
        """
        Compute all 168 filters
        
        Args:
            prices: Array of historical prices
            volumes: Array of historical volumes
            timestamps: Array of timestamps
            bid: Current bid price
            ask: Current ask price
            
        Returns:
            Dictionary with all filter outputs
        """
        start_time = time.time()
        
        # Prepare data for each filter group
        data = {
            "prices": prices,
            "volumes": volumes,
            "timestamps": timestamps,
            "bid": bid,
            "ask": ask,
            "mid": (bid + ask) / 2 if bid and ask else prices[-1] if len(prices) > 0 else 0.0,
            "spread": ask - bid if bid and ask else 0.0
        }
        
        # Compute filters in parallel
        outputs = {}
        futures = {}
        
        for name, filter_group in self.filters.items():
            future = self.executor.submit(self._compute_filter_group, name, filter_group, data)
            futures[future] = name
        
        # Collect results
        for future in as_completed(futures):
            name = futures[future]
            try:
                output = future.result()
                outputs[name] = output
            except Exception as e:
                print(f"[FILTER ENGINE] Error in {name}: {e}")
                outputs[name] = FilterOutput(
                    group_name=name,
                    features={},
                    computation_time_ms=0.0,
                    is_valid=False
                )
        
        # Calculate total computation time
        self.last_computation_time = (time.time() - start_time) * 1000
        
        # Flatten all features
        all_features = {}
        for name, output in outputs.items():
            for key, value in output.features.items():
                all_features[f"{name}_{key}"] = value
        
        return {
            "features": all_features,
            "feature_count": len(all_features),
            "computation_time_ms": self.last_computation_time,
            "group_outputs": {name: output.features for name, output in outputs.items()},
            "valid_groups": sum(1 for output in outputs.values() if output.is_valid)
        }
    
    def _compute_filter_group(
        self,
        name: str,
        filter_group: Any,
        data: Dict[str, Any]
    ) -> FilterOutput:
        """
        Compute a single filter group
        
        Args:
            name: Filter group name
            filter_group: Filter group instance
            data: Input data
            
        Returns:
            FilterOutput with computed features
        """
        start_time = time.time()
        
        try:
            features = filter_group.compute(data)
            computation_time = (time.time() - start_time) * 1000
            
            return FilterOutput(
                group_name=name,
                features=features,
                computation_time_ms=computation_time,
                is_valid=True
            )
        except Exception as e:
            return FilterOutput(
                group_name=name,
                features={},
                computation_time_ms=0.0,
                is_valid=False
            )
    
    def get_feature_vector(self, filter_outputs: Dict[str, Any]) -> np.ndarray:
        """
        Convert filter outputs to feature vector
        
        Args:
            filter_outputs: Output from compute_all
            
        Returns:
            Feature vector of shape (168,)
        """
        features = filter_outputs.get("features", {})
        
        # Create ordered feature vector
        feature_names = sorted(features.keys())
        feature_vector = np.array([features[name] for name in feature_names])
        
        # Pad or truncate to 168
        if len(feature_vector) < 168:
            feature_vector = np.pad(feature_vector, (0, 168 - len(feature_vector)))
        elif len(feature_vector) > 168:
            feature_vector = feature_vector[:168]
        
        return feature_vector
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics"""
        return {
            "total_filters": self.total_filters,
            "n_workers": self.n_workers,
            "last_computation_time_ms": self.last_computation_time,
            "filter_groups": list(self.filters.keys())
        }
    
    def shutdown(self) -> None:
        """Shutdown the filter engine"""
        self.executor.shutdown(wait=False)