"""
Configuration Manager for cTrader FIX Engine
Loads credentials from .env file - ZERO hardcoded passwords
"""

from .loader import FixConfig, load_config