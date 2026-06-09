#!/usr/bin/env python3
"""
Script to show the current bot configuration
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the bot config
try:
    from xauusd_god_bot import BotConfig
    
    def show_config():
        print("=" * 60)
        print("  XAUUSD GOD BOT - Current Configuration")
        print("=" * 60)
        
        # Create default config
        config = BotConfig()
        
        print(f"\n🤖 Bot Design/Modes:")
        print(f"  • Bot Name: {config.bot_name}")
        print(f"  • Symbol: {config.symbol}")
        print(f"  • Current Mode: {config.mode}")
        print(f"  • TUI Dashboard: {'✅ Enabled' if config.tui_enabled else '❌ Disabled'}")
        
        print(f"\n📊 Trading Settings:")
        print(f"  • Account Balance: ${config.account_balance:,.2f}")
        print(f"  • Leverage: {config.account_leverage}x")
        print(f"  • Max Risk per Trade: {config.max_risk_per_trade*100:.1f}%")
        print(f"  • Max Daily Drawdown: {config.max_daily_drawdown*100:.1f}%")
        print(f"  • Max Signal Score: {config.min_signal_score}/1000")
        
        print(f"\n🎨 TUI Dashboard Design (12 Panels):")
        print(f"  • Panel 1 (p1): Market Scanner - Cyan border")
        print(f"  • Panel 2 (p2): Signal Dashboard - Yellow border")
        print(f"  • Panel 3 (p3): AI Reasoning - Magenta border")
        print(f"  • Panel 4 (p4): Trade Manager - Green border")
        print(f"  • Panel 5 (p5): Model Performance - Blue border")
        print(f"  • Panel 6 (p6): Learning Log - Red border")
        print(f"  • Panel 7 (p7): Quantum Analysis - White border")
        print(f"  • Panel 8 (p8): Macro Economics - Bright Yellow border")
        print(f"  • Panel 9 (p9): SMC Structure - Bright Cyan border")
        
        print(f"\n🔒 Locked Configuration:")
        print(f"  • No config.yaml file found")
        print(f"  • Using default settings")
        print(f"  • Bot will run startup wizard on first run")
        
        print(f"\n💡 Available Modes:")
        print(f"  • demo: Paper trading (default)")
        print(f"  • live: Real trading with MetaTrader 5")
        print(f"  • backtest: Historical testing")
        
        print(f"\n🚀 To run the bot:")
        print(f"  python xauusd_god_bot.py")
        print(f"  python xauusd_god_bot.py --mode backtest")
        print(f"  python xauusd_god_bot.py --mode live")
        
        print("=" * 60)
    
    if __name__ == "__main__":
        show_config()
        
except ImportError as e:
    print(f"Error importing bot config: {e}")
    print("Please run this script from the project directory.")