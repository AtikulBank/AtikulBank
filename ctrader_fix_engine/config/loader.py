"""
FIX Configuration Loader
Secure credential management via .env files
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class FixConfig:
    """Immutable FIX connection configuration"""
    host: str
    port: int
    sender_comp_id: str
    target_comp_id: str
    sender_sub_id: str
    password: str
    heartbeat_interval: int = 30
    reconnect_interval: int = 5
    max_reconnect_attempts: int = 10
    buffer_size: int = 65536
    timeout: float = 30.0

    def __post_init__(self):
        if not self.host:
            raise ValueError("FIX_HOST is required")
        if not self.sender_comp_id:
            raise ValueError("SENDER_COMP_ID is required")
        if not self.target_comp_id:
            raise ValueError("TARGET_COMP_ID is required")
        if not self.password:
            raise ValueError("FIX_PASSWORD is required")


def load_config(env_file: Optional[str] = None) -> FixConfig:
    """
    Load FIX configuration from environment variables or .env file
    
    Args:
        env_file: Path to .env file. If None, looks for .env in current directory
        
    Returns:
        FixConfig with all required parameters
        
    Raises:
        FileNotFoundError: If .env file not found
        ValueError: If required environment variables are missing
    """
    # Load .env file if provided or exists
    if env_file:
        _load_dotenv(Path(env_file))
    else:
        env_path = Path(".env")
        if env_path.exists():
            _load_dotenv(env_path)
        else:
            # Try to find .env in parent directories
            for parent in Path(".").resolve().parents:
                parent_env = parent / ".env"
                if parent_env.exists():
                    _load_dotenv(parent_env)
                    break

    # Required variables
    required_vars = {
        "FIX_HOST": "host",
        "FIX_PORT": "port",
        "SENDER_COMP_ID": "sender_comp_id",
        "TARGET_COMP_ID": "target_comp_id",
        "SENDER_SUB_ID": "sender_sub_id",
        "FIX_PASSWORD": "password",
    }

    config_dict = {}
    
    for env_var, field_name in required_vars.items():
        value = os.getenv(env_var)
        if value is None:
            raise ValueError(f"Missing required environment variable: {env_var}")
        
        # Convert port to int
        if field_name == "port":
            try:
                value = int(value)
            except ValueError:
                raise ValueError(f"FIX_PORT must be an integer, got: {value}")
        
        config_dict[field_name] = value

    # Optional variables with defaults
    optional_vars = {
        "FIX_HEARTBEAT_INTERVAL": ("heartbeat_interval", int),
        "FIX_RECONNECT_INTERVAL": ("reconnect_interval", int),
        "FIX_MAX_RECONNECT_ATTEMPTS": ("max_reconnect_attempts", int),
        "FIX_BUFFER_SIZE": ("buffer_size", int),
        "FIX_TIMEOUT": ("timeout", float),
    }

    for env_var, (field_name, converter) in optional_vars.items():
        value = os.getenv(env_var)
        if value is not None:
            try:
                config_dict[field_name] = converter(value)
            except ValueError:
                raise ValueError(f"{env_var} must be {converter.__name__}, got: {value}")

    return FixConfig(**config_dict)


def _load_dotenv(path: Path) -> None:
    """Load .env file into environment variables (simplified implementation)"""
    if not path.exists():
        raise FileNotFoundError(f".env file not found: {path}")

    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
            
            # Parse key=value pairs
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                
                # Only set if not already set (respect existing env vars)
                if key not in os.environ:
                    os.environ[key] = value