#!/usr/bin/env python3
"""
REALISTIC BOT - 70% Win Rate for Live Trading
==============================================
More realistic approach for consistent profits

Strategy:
- 70% win rate target
- More trades (higher frequency)
- Balanced TP/SL ratio
- Consistent profits over time
"""

import numpy as np
from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import time

class SignalDirection(Enum):
    BUY = 1
    SELL = -1
    NEUTRAL = 0

@dataclass
class RealisticTrade:
    entry_price: float
    direction: SignalDirection
    sl: float
    tp1: float
    tp2: float
    confidence: float
    lot_size: float
    risk_amount: float
    entry_time: float

class RealisticSystem:
    """
    Realistic Trading System for 70% Win Rate
    
    Designed for:
- Consistent profits
- More trades (higher frequency)
- Balanced risk/reward
- Sustainable performance
    """
    
    def __init__(self, account_balance: float = 10000.0):
        self.account_balance = account_balance
        self.max_risk_percent = 0.01  # 1% risk per trade (conservative)
        self.spread_points = 30  # XAUUSD typical spread (3.0 pips)
        self.slippage_points = 10  # Expected slippage
        
        # Trading parameters for 70% win rate
        self.tp_multiplier = 0.5  # Moderate TP (50% of ATR)
        self.sl_multiplier = 1.0  # Moderate SL (100% of ATR)
        self.min_momentum = 0.3  # Lower momentum requirement
        self.max_trades_per_day = 20
        
    def calculate_atr(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> float:
        """Calculate ATR from OHLC data."""
        if len(closes) < period + 1:
            return np.std(closes[-20:]) * 0.1
        
        tr = np.maximum(
            highs[-period:] - lows[-period:],
            np.maximum(
                np.abs(highs[-period:] - np.roll(closes, 1)[-period:]),
                np.abs(lows[-period:] - np.roll(closes, 1)[-period:])
            )
        )
        return np.mean(tr)
    
    def calculate_spread_cost(self, current_price: float) -> float:
        """Calculate spread cost in price."""
        return self.spread_points * 0.01
    
    def calculate_slippage(self) -> float:
        """Estimate slippage."""
        return self.slippage_points * 0.01
    
    def calculate_lot_size(self, sl_distance: float) -> float:
        """Calculate lot size based on risk management."""
        risk_amount = self.account_balance * self.max_risk_percent
        pip_value = 1.0
        sl_pips = sl_distance / 0.01
        
        if sl_pips == 0:
            return 0.01
        
        lot_size = risk_amount / (sl_pips * pip_value * 100)
        return max(0.01, min(lot_size, 1.0))
    
    def generate_signal(self, 
                       highs: np.ndarray, 
                       lows: np.ndarray, 
                       closes: np.ndarray,
                       volumes: np.ndarray) -> Optional[RealisticTrade]:
        """Generate trading signal for 70% win rate."""
        
        if len(closes) < 30:
            return None
        
        current_price = closes[-1]
        current_time = time.time()
        
        # Calculate ATR
        atr = self.calculate_atr(highs, lows, closes)
        if atr == 0:
            return None
        
        # Calculate TP and SL distances
        tp_distance = atr * self.tp_multiplier
        sl_distance = atr * self.sl_multiplier
        
        # Add spread and slippage to SL
        sl_distance += self.calculate_spread_cost(current_price) + self.calculate_slippage()
        
        # FILTER 1: Moderate momentum (price moved somewhat)
        recent_move = closes[-1] - closes[-3]
        if abs(recent_move) < atr * self.min_momentum:
            return None
        
        # FILTER 2: Direction consistency (2+ bars same direction)
        last_2_moves = np.diff(closes[-3:])
        if not (all(last_2_moves > 0) or all(last_2_moves < 0)):
            return None
        
        # FILTER 3: Volume check
        if len(volumes) >= 5:
            avg_volume = np.mean(volumes[-5:])
            current_volume = volumes[-1]
            if current_volume < avg_volume * 0.7:
                return None
        
        # FILTER 4: Price position
        recent_high = np.max(highs[-15:])
        recent_low = np.min(lows[-15:])
        price_range = recent_high - recent_low
        if price_range == 0:
            return None
        
        price_position = (current_price - recent_low) / price_range
        
        # FILTER 5: Simple trend direction
        if recent_move > 0:  # BUY signal
            direction = SignalDirection.BUY
        else:  # SELL signal
            direction = SignalDirection.SELL
        
        # FILTER 6: Trend strength
        trend_strength = abs(closes[-1] - closes[-5]) / atr
        if trend_strength < 0.5:
            return None
        
        # Calculate entry levels
        spread_cost = self.calculate_spread_cost(current_price)
        
        if direction == SignalDirection.BUY:
            entry = current_price + spread_cost
            sl = entry - sl_distance
            tp1 = entry + tp_distance
            tp2 = entry + tp_distance * 1.5
        else:  # SELL
            entry = current_price - spread_cost
            sl = entry + sl_distance
            tp1 = entry - tp_distance
            tp2 = entry - tp_distance * 1.5
        
        # Calculate lot size
        lot_size = self.calculate_lot_size(sl_distance)
        
        # Calculate risk
        risk_amount = self.account_balance * self.max_risk_percent
        
        # Confidence
        confidence = 0.7  # 70% confidence target
        
        return RealisticTrade(
            entry_price=entry,
            direction=direction,
            sl=sl,
            tp1=tp1,
            tp2=tp2,
            confidence=confidence,
            lot_size=lot_size,
            risk_amount=risk_amount,
            entry_time=current_time
        )
    
    def should_exit_trade(self, trade: RealisticTrade, current_price: float) -> Tuple[bool, str]:
        """Check if trade should be exited."""
        
        if trade.direction == SignalDirection.BUY:
            if current_price >= trade.tp1:
                return True, "TP_HIT"
            if current_price <= trade.sl:
                return True, "SL_HIT"
        else:
            if current_price <= trade.tp1:
                return True, "TP_HIT"
            if current_price >= trade.sl:
                return True, "SL_HIT"
        
        return False, ""
    
    def calculate_pnl(self, trade: RealisticTrade, exit_price: float) -> float:
        """Calculate PnL in USD."""
        if trade.direction == SignalDirection.BUY:
            pnl_pips = (exit_price - trade.entry_price) / 0.01
        else:
            pnl_pips = (trade.entry_price - exit_price) / 0.01
        
        pnl_usd = pnl_pips * trade.lot_size * 1.0
        
        return pnl_usd


def run_realistic_simulation():
    """Run realistic simulation for 70% win rate."""
    print("="*80)
    print("  REALISTIC BOT - 70% Win Rate Target")
    print("="*80)
    
    # Generate realistic XAUUSD OHLCV data
    np.random.seed(456)  # Different seed
    n_bars = 1000
    base_price = 2350.0
    
    # Create realistic price movements with trends and ranges
    returns = np.random.randn(n_bars) * 0.0004
    # Add various market conditions
    returns[50:200] += 0.0003  # Uptrend
    returns[200:350] -= 0.0002  # Downtrend
    returns[350:500] += 0.0002  # Uptrend
    returns[500:650] -= 0.0003  # Downtrend
    returns[650:800] += 0.0002  # Uptrend
    returns[800:1000] -= 0.0001  # Mild downtrend
    
    closes = base_price * np.exp(np.cumsum(returns))
    
    # Generate OHLC from close
    highs = closes + np.abs(np.random.randn(n_bars) * 0.8)
    lows = closes - np.abs(np.random.randn(n_bars) * 0.8)
    opens = np.roll(closes, 1)
    opens[0] = closes[0]
    
    # Generate volume
    volumes = np.random.randint(1000, 8000, n_bars)
    
    print(f"\nPrice range: ${closes.min():.2f} - ${closes.max():.2f}")
    print(f"Total bars: {n_bars}")
    print(f"Account Balance: $10,000")
    
    # Initialize system
    system = RealisticSystem(account_balance=10000.0)
    trades = []
    open_trade = None
    
    # Run simulation
    print("\nRunning realistic simulation...")
    
    for i in range(30, n_bars):
        current_price = closes[i]
        
        # Check if we have an open trade
        if open_trade is not None:
            should_exit, reason = system.should_exit_trade(open_trade, current_price)
            
            if should_exit:
                pnl = system.calculate_pnl(open_trade, current_price)
                trades.append({
                    'entry': open_trade.entry_price,
                    'exit': current_price,
                    'direction': open_trade.direction.name,
                    'pnl': pnl,
                    'win': pnl > 0,
                    'reason': reason,
                    'lot_size': open_trade.lot_size
                })
                
                win_status = "✅ WIN" if pnl > 0 else "❌ LOSS"
                print(f"  Trade {len(trades):3d}: {open_trade.direction.name:4s} @ {open_trade.entry_price:.2f} → {current_price:.2f} | PnL: ${pnl:+.2f} | {win_status} | {reason}")
                
                open_trade = None
        else:
            # Generate new signal
            trade = system.generate_signal(
                highs[:i+1], 
                lows[:i+1], 
                closes[:i+1],
                volumes[:i+1]
            )
            
            if trade is not None:
                open_trade = trade
    
    # Close any remaining open trade
    if open_trade is not None:
        current_price = closes[-1]
        pnl = system.calculate_pnl(open_trade, current_price)
        trades.append({
            'entry': open_trade.entry_price,
            'exit': current_price,
            'direction': open_trade.direction.name,
            'pnl': pnl,
            'win': pnl > 0,
            'reason': "END_OF_DATA",
            'lot_size': open_trade.lot_size
        })
    
    # Calculate results
    print("\n" + "="*80)
    print("  REALISTIC SIMULATION RESULTS")
    print("="*80)
    
    if trades:
        wins = sum(1 for t in trades if t['win'])
        losses = len(trades) - wins
        win_rate = wins / len(trades) if trades else 0
        
        total_pnl = sum(t['pnl'] for t in trades)
        avg_pnl = total_pnl / len(trades) if trades else 0
        
        print(f"\n  Total Trades: {len(trades)}")
        print(f"  Wins: {wins} ({win_rate*100:.1f}%)")
        print(f"  Losses: {losses} ({(1-win_rate)*100:.1f}%)")
        
        print(f"\n  Total PnL: ${total_pnl:+,.2f}")
        print(f"  Average PnL: ${avg_pnl:+,.2f}")
        
        # Exit reasons
        tp_hits = sum(1 for t in trades if t['reason'] == 'TP_HIT')
        sl_hits = sum(1 for t in trades if t['reason'] == 'SL_HIT')
        
        print(f"\n  Exit Reasons:")
        print(f"    TP Hits: {tp_hits} ({tp_hits/len(trades)*100:.1f}%)")
        print(f"    SL Hits: {sl_hits} ({sl_hits/len(trades)*100:.1f}%)")
        
        # Check if target achieved
        if win_rate >= 0.70:
            print(f"\n  🎯 TARGET ACHIEVED! {win_rate*100:.1f}% win rate (target: 70%)")
        else:
            print(f"\n  ❌ Current win rate: {win_rate*100:.1f}% (need 70%)")
        
        # Profit factor
        gross_profit = sum(t['pnl'] for t in trades if t['win'])
        gross_loss = abs(sum(t['pnl'] for t in trades if not t['win']))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        print(f"\n  Profit Factor: {profit_factor:.2f}")
        print(f"  Risk Analysis:")
        print(f"    Max Risk per Trade: 1% (${10000 * 0.01:.2f})")
        print(f"    Average Lot Size: {np.mean([t['lot_size'] for t in trades]):.2f}")
        
    else:
        print("\n  No trades generated")
    
    return trades


if __name__ == "__main__":
    trades = run_realistic_simulation()
