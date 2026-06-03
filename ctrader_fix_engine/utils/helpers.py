"""
Utility Helper Functions
"""

import uuid
import time
from datetime import datetime, timezone


def generate_cl_ord_id(prefix: str = "ORD") -> str:
    """
    Generate unique client order ID
    
    Args:
        prefix: Optional prefix for the order ID
        
    Returns:
        Unique order ID string
    """
    timestamp = int(time.time() * 1000)  # Milliseconds
    unique_id = uuid.uuid4().hex[:8].upper()
    return f"{prefix}-{timestamp}-{unique_id}"


def format_price(price: float, decimals: int = 5) -> str:
    """
    Format price with specified decimal places
    
    Args:
        price: Price value
        decimals: Number of decimal places
        
    Returns:
        Formatted price string
    """
    return f"{price:.{decimals}f}"


def format_quantity(quantity: float) -> str:
    """
    Format quantity with appropriate precision
    
    Args:
        quantity: Quantity value
        
    Returns:
        Formatted quantity string
    """
    if quantity == int(quantity):
        return str(int(quantity))
    return f"{quantity:.5f}"


def get_utc_timestamp() -> str:
    """
    Get current UTC timestamp in FIX format
    
    Returns:
        Timestamp string (YYYYMMDD-HH:MM:SS.mmm)
    """
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H:%M:%S.%f")[:-3]


def validate_symbol(symbol: str) -> bool:
    """
    Validate trading symbol format
    
    Args:
        symbol: Symbol to validate
        
    Returns:
        True if valid
    """
    # Basic validation: letters only, reasonable length
    return symbol.isalpha() and 3 <= len(symbol) <= 20


def calculate_pip_value(symbol: str, pip_size: float = 0.0001) -> float:
    """
    Calculate pip value for a symbol
    
    Args:
        symbol: Trading symbol
        pip_size: Size of one pip
        
    Returns:
        Pip value
    """
    # Default pip sizes for common symbols
    pip_sizes = {
        "EURUSD": 0.0001,
        "GBPUSD": 0.0001,
        "USDJPY": 0.01,
        "XAUUSD": 0.01,
        "XAGUSD": 0.001,
    }
    
    return pip_sizes.get(symbol.upper(), pip_size)