"""
FIX Engine - Core Trading Logic
Manages FIX session lifecycle and order flow
"""

from .session import FixSession
from .pipeline import TickPipeline, TickAggregator, Tick, TickAnalysis, TrendDirection