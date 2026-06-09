"""
LAYER 1: SIGNAL INTEGRITY
Tick authentication, Timestamp monotonicity, Price sanity bounds,
Bid-Ask spread validity, Volume spike detection, Exchange heartbeat verify
"""

from .signal_integrity import SignalIntegrity

__all__ = ["SignalIntegrity"]