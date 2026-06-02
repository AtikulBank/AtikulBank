"""
Configuration module for cTrader HFT Engine
Loads credentials from environment variables securely
"""
import os
from typing import Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class FIXConfig:
    """FIX API Configuration from environment variables"""
    FIX_HOST: str
    FIX_PORT: int
    SENDER_COMP_ID: str
    TARGET_COMP_ID: str
    SENDER_SUB_ID: str
    FIX_PASSWORD: str
    
    @classmethod
    def from_environment(cls) -> 'FIXConfig':
        """Load configuration from environment variables"""
        return cls(
            FIX_HOST=os.environ.get('FIX_HOST', ''),
            FIX_PORT=int(os.environ.get('FIX_PORT', '0')),
            SENDER_COMP_ID=os.environ.get('SENDER_COMP_ID', ''),
            TARGET_COMP_ID=os.environ.get('TARGET_COMP_ID', ''),
            SENDER_SUB_ID=os.environ.get('SENDER_SUB_ID', ''),
            FIX_PASSWORD=os.environ.get('FIX_PASSWORD', '')
        )
    
    def validate(self) -> bool:
        """Validate that all required fields are present"""
        return all([
            self.FIX_HOST,
            self.FIX_PORT > 0,
            self.SENDER_COMP_ID,
            self.TARGET_COMP_ID,
            self.SENDER_SUB_ID,
            self.FIX_PASSWORD
        ])

def load_env_file(env_path: str = '.env') -> None:
    """Load environment variables from .env file"""
    path = Path(env_path)
    if not path.exists():
        print(f"[CONFIG] No .env file found at {env_path}")
        return
    
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                os.environ[key] = value

def get_fix_config() -> FIXConfig:
    """Get FIX configuration from environment"""
    # Try to load .env file first
    load_env_file()
    
    config = FIXConfig.from_environment()
    
    if not config.validate():
        print("[CONFIG] Warning: Some FIX configuration values are missing")
        print("[CONFIG] Please set the following environment variables:")
        print("  - FIX_HOST")
        print("  - FIX_PORT")
        print("  - SENDER_COMP_ID")
        print("  - TARGET_COMP_ID")
        print("  - SENDER_SUB_ID")
        print("  - FIX_PASSWORD")
    
    return config