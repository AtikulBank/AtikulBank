"""
LAYER 0: HARDWARE GUARD
Latency check < 1ms, Clock sync (GPS/PTP), Memory pre-allocated, CPU affinity locked
"""

from .hardware_guard import HardwareGuard

__all__ = ["HardwareGuard"]