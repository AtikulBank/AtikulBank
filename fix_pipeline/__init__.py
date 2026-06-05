"""
FIX Pipeline - High-Speed Routing
Direct connection to cTrader FIX gateway
"""

try:
    from .network_layer import TcpSocket, SocketError
except ImportError:
    from .network_layer import TcpSocket, SocketError

# Use pure Python encoder (Cython version has segfault issue)
from .fix_encoder_py import FixEncoder

from .fix_decoder import FixDecoder, MarketDataTick, ExecutionReport, FixMsgType
from .simulated_feed import SimulatedMarketFeed, MarketDataProvider

__all__ = [
    'TcpSocket', 'SocketError',
    'FixEncoder',
    'FixDecoder', 'MarketDataTick', 'ExecutionReport', 'FixMsgType',
    'SimulatedMarketFeed', 'MarketDataProvider',
]
