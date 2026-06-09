"""
LAYER 0: HARDWARE GUARD
Ensures optimal hardware conditions for low-latency trading
"""

import os
import time
import psutil
import numpy as np
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class HardwareMetrics:
    """Hardware metrics dataclass"""
    latency_ns: int = 0
    clock_offset_ns: int = 0
    memory_allocated_mb: float = 0.0
    cpu_affinity_set: bool = False
    cpu_freq_mhz: float = 0.0
    memory_available_mb: float = 0.0
    is_realtime: bool = False


class HardwareGuard:
    """
    Layer 0: Hardware Guard
    Ensures optimal hardware conditions for low-latency trading
    """
    
    def __init__(self, target_latency_ns: int = 1_000_000) -> None:
        """
        Initialize Hardware Guard
        
        Args:
            target_latency_ns: Target latency in nanoseconds (default: 1ms = 1,000,000 ns)
        """
        self.target_latency_ns = target_latency_ns
        self.metrics = HardwareMetrics()
        self._memory_buffer: Optional[np.ndarray] = None
        self._initialized = False
        
    def initialize(self) -> bool:
        """
        Initialize hardware guard
        
        Returns:
            True if initialization successful
        """
        try:
            # Pre-allocate memory buffer (10MB)
            self._memory_buffer = np.zeros(10 * 1024 * 1024 // 8, dtype=np.float64)
            self.metrics.memory_allocated_mb = self._memory_buffer.nbytes / (1024 * 1024)
            
            # Set CPU affinity to first core (if available)
            try:
                p = psutil.Process()
                p.cpu_affinity([0])
                self.metrics.cpu_affinity_set = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self.metrics.cpu_affinity_set = False
            
            # Get CPU frequency
            try:
                freq = psutil.cpu_freq()
                if freq:
                    self.metrics.cpu_freq_mhz = freq.current
            except Exception:
                pass
            
            # Get available memory
            mem = psutil.virtual_memory()
            self.metrics.memory_available_mb = mem.available / (1024 * 1024)
            
            # Check if running with realtime priority
            self.metrics.is_realtime = self._check_realtime_priority()
            
            # Measure latency
            self.metrics.latency_ns = self._measure_latency()
            
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"[HARDWARE GUARD] Initialization failed: {e}")
            return False
    
    def _measure_latency(self, iterations: int = 1000) -> int:
        """
        Measure tick-to-tick latency
        
        Args:
            iterations: Number of iterations to average
            
        Returns:
            Average latency in nanoseconds
        """
        latencies = []
        
        for _ in range(iterations):
            start = time.perf_counter_ns()
            # Simulate minimal work
            _ = time.perf_counter_ns()
            end = time.perf_counter_ns()
            latencies.append(end - start)
        
        return int(np.mean(latencies))
    
    def _check_realtime_priority(self) -> bool:
        """Check if process has realtime priority"""
        try:
            p = psutil.Process()
            # Check if nice value is negative (realtime on Linux)
            return p.nice() < 0
        except Exception:
            return False
    
    def set_realtime_priority(self) -> bool:
        """
        Set process to realtime priority
        
        Returns:
            True if successful
        """
        try:
            p = psutil.Process()
            # Set nice value to -20 (highest priority on Linux)
            p.nice(-20)
            self.metrics.is_realtime = True
            return True
        except Exception as e:
            print(f"[HARDWARE GUARD] Could not set realtime priority: {e}")
            return False
    
    def sync_clock(self) -> float:
        """
        Sync system clock (simplified - would use PTP/GPS in production)
        
        Returns:
            Clock offset in nanoseconds
        """
        # In production, this would sync with PTP/GPS
        # For now, we just measure the offset
        t1 = time.time_ns()
        t2 = time.time_ns()
        self.metrics.clock_offset_ns = t2 - t1
        return self.metrics.clock_offset_ns
    
    def validate(self) -> Dict[str, Any]:
        """
        Validate hardware conditions
        
        Returns:
            Dictionary with validation results
        """
        if not self._initialized:
            self.initialize()
        
        # Re-measure latency
        self.metrics.latency_ns = self._measure_latency()
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "latency_ns": self.metrics.latency_ns,
            "latency_ms": self.metrics.latency_ns / 1_000_000,
            "latency_ok": self.metrics.latency_ns <= self.target_latency_ns,
            "clock_offset_ns": self.metrics.clock_offset_ns,
            "memory_allocated_mb": self.metrics.memory_allocated_mb,
            "memory_available_mb": self.metrics.memory_available_mb,
            "cpu_affinity_set": self.metrics.cpu_affinity_set,
            "cpu_freq_mhz": self.metrics.cpu_freq_mhz,
            "is_realtime": self.metrics.is_realtime,
            "all_ok": (
                self.metrics.latency_ns <= self.target_latency_ns and
                self.metrics.memory_available_mb > 100  # At least 100MB available
            )
        }
        
        return results
    
    def get_metrics(self) -> HardwareMetrics:
        """Get current hardware metrics"""
        return self.metrics
    
    def cleanup(self) -> None:
        """Cleanup resources"""
        self._memory_buffer = None
        self._initialized = False