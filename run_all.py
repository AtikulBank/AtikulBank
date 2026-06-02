#!/usr/bin/env python3
"""
XAUUSD God Bot - One-Command Runner
Runs all components together in one command
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def print_banner():
    print("=" * 80)
    print("  XAUUSD GOD BOT - ONE COMMAND RUNNER")
    print("  All Systems Integrated | Single Command Execution")
    print("=" * 80)
    print()

def check_python_version():
    """Check Python version"""
    if sys.version_info < (3, 8):
        print(f"[ERROR] Python 3.8+ required. Current: {sys.version}")
        sys.exit(1)
    print(f"[✓] Python {sys.version_info.major}.{sys.version_info.minor}")

def check_required_packages():
    """Check and install required packages"""
    required = {
        'numpy': 'numpy',
        'pandas': 'pandas',
        'scipy': 'scipy',
        'sklearn': 'scikit-learn',
        'xgboost': 'xgboost',
        'lightgbm': 'lightgbm',
        'catboost': 'catboost',
        'torch': 'torch',
        'rich': 'rich',
        'yaml': 'pyyaml',
        'pyarrow': 'pyarrow',
        'yfinance': 'yfinance',
        'optuna': 'optuna',
        'river': 'river',
        'ta': 'ta',
        'numba': 'numba',
        'joblib': 'joblib',
        'requests': 'requests',
        'aiohttp': 'aiohttp',
        'transformers': 'transformers',
        'feedparser': 'feedparser',
        'openpyxl': 'openpyxl',
        'statsmodels': 'statsmodels',
        'hmmlearn': 'hmmlearn'
    }
    
    missing = []
    for mod, pip_name in required.items():
        try:
            importlib.import_module(mod)
        except ImportError:
            missing.append(pip_name)
    
    if missing:
        print(f"[!] Installing {len(missing)} missing packages...")
        for pkg in missing:
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", pkg, "-q"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print(f"  ✓ Installed {pkg}")
            except subprocess.CalledProcessError:
                print(f"  ✗ Failed to install {pkg}")
    else:
        print(f"[✓] All {len(required)} packages installed")
    
    return len(missing) == 0

def check_cython_extensions():
    """Check if Cython extensions are compiled"""
    cython_files = [
        "ctrader_hft_engine/core/network/hft_socket.cpython-*.so",
        "ctrader_hft_engine/core/fix/fix_encoder.cpython-*.so",
        "ctrader_hft_engine/core/fix/fix_decoder.cpython-*.so"
    ]
    
    all_compiled = True
    for pattern in cython_files:
        if not list(Path("ctrader_hft_engine").glob(pattern)):
            all_compiled = False
            break
    
    if all_compiled:
        print("[✓] Cython extensions compiled")
    else:
        print("[!] Cython extensions not found, building...")
        try:
            subprocess.check_call(
                [sys.executable, "setup.py", "build_ext", "--inplace"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print("[✓] Cython extensions built successfully")
        except subprocess.CalledProcessError as e:
            print(f"[!] Cython build failed: {e}")
            print("    Continuing with Python fallback...")
    
    return True

def check_config():
    """Check if configuration exists"""
    # Check for .env file
    if Path(".env").exists():
        print("[✓] .env file found")
        return True
    elif Path(".env.example").exists():
        print("[!] .env file not found")
        print("    Creating .env from .env.example...")
        try:
            import shutil
            shutil.copy(".env.example", ".env")
            print("    ✓ .env created (please edit with your credentials)")
            return False
        except Exception as e:
            print(f"    ✗ Failed to create .env: {e}")
            return False
    else:
        print("[!] No configuration files found")
        return False

def run_bot():
    """Run the XAUUSD God Bot"""
    print("\n" + "=" * 80)
    print("  STARTING XAUUSD GOD BOT")
    print("=" * 80 + "\n")
    
    try:
        # Import and run the bot
        from xauusd_god_bot import main
        import asyncio
        
        # Run the main function
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n[!] Bot stopped by user")
    except Exception as e:
        print(f"\n[ERROR] Bot failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def main():
    """Main runner function"""
    print_banner()
    
    # Step 1: Check Python version
    print("[STEP 1] Checking Python version...")
    check_python_version()
    print()
    
    # Step 2: Check packages
    print("[STEP 2] Checking packages...")
    packages_ok = check_required_packages()
    print()
    
    # Step 3: Check Cython extensions
    print("[STEP 3] Checking Cython extensions...")
    check_cython_extensions()
    print()
    
    # Step 4: Check configuration
    print("[STEP 4] Checking configuration...")
    config_ok = check_config()
    print()
    
    # Summary
    print("=" * 80)
    print("  SYSTEM CHECK COMPLETE")
    print("=" * 80)
    print(f"  Python: ✓")
    print(f"  Packages: {'✓' if packages_ok else '⚠'}")
    print(f"  Cython: ✓")
    print(f"  Config: {'✓' if config_ok else '⚠'}")
    print()
    
    if not config_ok:
        print("[!] Please configure .env file before running")
        print("    Edit .env with your cTrader FIX credentials")
        print()
        print("    Required variables:")
        print("      FIX_HOST")
        print("      FIX_PORT")
        print("      SENDER_COMP_ID")
        print("      TARGET_COMP_ID")
        print("      SENDER_SUB_ID")
        print("      FIX_PASSWORD")
        print()
        print("    Then run this script again.")
        return
    
    # Run the bot
    print("[STEP 5] Starting XAUUSD God Bot...")
    print()
    
    success = run_bot()
    
    if success:
        print("\n" + "=" * 80)
        print("  BOT EXECUTION COMPLETE")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("  BOT EXECUTION FAILED")
        print("=" * 80)

if __name__ == "__main__":
    main()