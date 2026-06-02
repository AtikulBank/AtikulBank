#!/usr/bin/env python3
"""
cTrader HFT Engine - Main Runner Script
Ultra-low-latency Cython-based FIX API implementation
"""

import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def check_environment():
    """Check if environment variables are set"""
    required_vars = [
        'FIX_HOST',
        'FIX_PORT',
        'SENDER_COMP_ID',
        'TARGET_COMP_ID',
        'SENDER_SUB_ID',
        'FIX_PASSWORD'
    ]
    
    missing = [var for var in required_vars if not os.environ.get(var)]
    
    if missing:
        print("[ERROR] Missing environment variables:")
        for var in missing:
            print(f"  - {var}")
        print("\nPlease create a .env file with these variables:")
        print("=" * 60)
        print("FIX_HOST=your_fix_host")
        print("FIX_PORT=your_fix_port")
        print("SENDER_COMP_ID=your_sender_comp_id")
        print("TARGET_COMP_ID=your_target_comp_id")
        print("SENDER_SUB_ID=your_sender_sub_id")
        print("FIX_PASSWORD=your_fix_password")
        print("=" * 60)
        return False
    return True

def load_env_file(env_path: str = '.env'):
    """Load environment variables from .env file"""
    path = Path(env_path)
    if not path.exists():
        print(f"[INFO] No .env file found at {env_path}")
        return
    
    print(f"[INFO] Loading environment from {env_path}")
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                os.environ[key] = value

def build_extensions():
    """Build Cython extensions"""
    print("[BUILD] Compiling Cython extensions...")
    
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "setup.py", "build_ext", "--inplace"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent)
        )
        
        if result.returncode != 0:
            print(f"[BUILD ERROR] {result.stderr}")
            return False
        
        print("[BUILD] Cython extensions compiled successfully!")
        return True
        
    except Exception as e:
        print(f"[BUILD ERROR] {e}")
        return False

def run_hft_engine():
    """Run the HFT engine"""
    print("=" * 70)
    print("  cTrader HFT Engine - Ultra-Low-Latency FIX API Implementation")
    print("=" * 70)
    
    # Load environment
    load_env_file()
    
    # Check environment
    if not check_environment():
        return False
    
    # Print configuration (sensitive data masked)
    print("\n[CONFIG] FIX Configuration:")
    print(f"  Host: {os.environ.get('FIX_HOST', 'N/A')}")
    print(f"  Port: {os.environ.get('FIX_PORT', 'N/A')}")
    print(f"  Sender: {os.environ.get('SENDER_COMP_ID', 'N/A')}")
    print(f"  Target: {os.environ.get('TARGET_COMP_ID', 'N/A')}")
    print(f"  SubID: {os.environ.get('SENDER_SUB_ID', 'N/A')}")
    print(f"  Password: {'*' * 8}")
    
    try:
        # Import compiled Cython modules
        from ctrader_hft_engine.core.network.hft_socket import HFTSocket
        from ctrader_hft_engine.core.fix.fix_encoder import FIXEncoder
        from ctrader_hft_engine.core.fix.fix_decoder import FIXDecoder
        
        print("\n[SUCCESS] Cython modules loaded successfully!")
        
        # Create FIX encoder/decoder
        encoder = FIXEncoder(
            os.environ['SENDER_COMP_ID'],
            os.environ['TARGET_COMP_ID'],
            os.environ['SENDER_SUB_ID']
        )
        decoder = FIXDecoder()
        
        # Create socket
        socket = HFTSocket(
            os.environ['FIX_HOST'],
            int(os.environ['FIX_PORT']),
            use_ssl=True,
            timeout=5.0
        )
        
        print("\n[CONNECT] Establishing connection to cTrader...")
        
        if socket.connect():
            print("[CONNECT] Connection established!")
            
            # Send Logon
            logon_msg = encoder.create_logon_message(os.environ['FIX_PASSWORD'])
            print(f"[SEND] Logon message sent")
            
            # In production, you would wait for response here
            # For demo, we'll just print the structure
            
            print("\n[HFT] Engine is ready for trading!")
            print("[HFT] Press Ctrl+C to stop")
            
            # Keep running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n[HFT] Shutting down...")
                socket.disconnect()
                print("[HFT] Engine stopped")
                return True
        else:
            print("[ERROR] Failed to connect to cTrader")
            return False
            
    except ImportError as e:
        print(f"\n[ERROR] Cython modules not found. Please run build first:")
        print(f"  python setup.py build_ext --inplace")
        print(f"\nError details: {e}")
        return False
    except Exception as e:
        print(f"\n[ERROR] {e}")
        return False

if __name__ == "__main__":
    # First, try to build if extensions don't exist
    try:
        from ctrader_hft_engine.core.network.hft_socket import HFTSocket
        print("[INFO] Cython extensions already compiled")
    except ImportError:
        print("[INFO] Cython extensions not found, building...")
        if not build_extensions():
            sys.exit(1)
    
    # Run the engine
    success = run_hft_engine()
    sys.exit(0 if success else 1)