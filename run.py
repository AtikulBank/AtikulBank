"""
AtikulBot - World #1 Master Pipeline Design
Renaissance + Citadel + Two Sigma + DE Shaw HYBRID

15-Layer Trading Bot with 168-Filter Parallel Engine
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Layer_15_master_loop import MasterLoop


async def main():
    """Main entry point"""
    print("=" * 60)
    print("  WORLD #1 MASTER PIPELINE DESIGN")
    print("  Renaissance + Citadel + Two Sigma + DE Shaw HYBRID")
    print("=" * 60)
    print()
    
    # Initialize master loop
    master = MasterLoop()
    
    try:
        # Start the bot
        await master.start()
    except KeyboardInterrupt:
        print("\n[MAIN] Interrupted by user")
    except Exception as e:
        print(f"\n[MAIN] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Stop the bot
        await master.stop()
        
        # Print statistics
        stats = master.get_statistics()
        print("\n" + "=" * 60)
        print("  SESSION STATISTICS")
        print("=" * 60)
        print(f"  Total Ticks: {stats['tick_count']}")
        print(f"  Uptime: {stats['uptime_seconds']:.1f} seconds")
        print(f"  Position Trades: {stats['position_lifecycle']['total_trades']}")
        print(f"  Win Rate: {stats['position_lifecycle']['win_rate']:.2%}")
        print(f"  Total P&L: ${stats['position_lifecycle']['total_pnl']:.2f}")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())