#!/usr/bin/env python3
"""
BACKTEST & OPTIMIZATION - Find 50/50 Win Rate Strategy
Like Renaissance Technologies Medallion Fund approach
"""

import sys
import time
import numpy as np
import pandas as pd
from typing import List, Tuple, Dict
from dataclasses import dataclass
from enum import Enum

class SignalDirection(Enum):
    BUY = 1
    SELL = -1
    NEUTRAL = 0

@dataclass
class TradeResult:
    entry_price: float
    exit_price: float
    direction: SignalDirection
    sl: float
    tp1: float
    pnl_pips: float
    pnl_usd: float
    win: bool
    exit_reason: str

class MedallionStyleBacktester:
    """
    Renaissance Technologies Medallion Fund style backtesting.
    Focus on:
    1. High frequency trading with small edges
    2. Multiple uncorrelated signals
    3. Dynamic position sizing
    4. Strict risk management
    """
    
    def __init__(self, initial_balance: float = 10000.0):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.peak_balance = initial_balance
        self.trades: List[TradeResult] = []
        self.max_drawdown = 0.0
        
        # Medallion-style parameters
        self.max_risk_per_trade = 0.005  # 0.5% risk per trade (aggressive)
        self.max_daily_trades = 100  # High frequency
        self.min_sharpe = 1.5  # Minimum Sharpe ratio
        self.lookback_period = 20  # For signal generation
        
    def calculate_atr(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate Average True Range."""
        if len(prices) < period + 1:
            return np.std(prices) * 0.1
        
        # Simple ATR using close prices
        returns = np.diff(prices[-period-1:])
        atr = np.mean(np.abs(returns))
        
        return atr if atr > 0 else np.std(prices) * 0.1
    
    def calculate_support_resistance(self, prices: np.ndarray) -> Tuple[float, float]:
        """Calculate support and resistance levels."""
        if len(prices) < 20:
            return prices[-1] * 0.99, prices[-1] * 1.01
        
        # Use rolling min/max for support/resistance
        window = min(20, len(prices))
        support = np.min(prices[-window:])
        resistance = np.max(prices[-window:])
        
        # Adjust based on recent price action
        recent_prices = prices[-10:]
        if np.mean(np.diff(recent_prices)) > 0:  # Uptrend
            support = np.min(recent_prices[-5:])
            resistance = np.max(prices[-window:]) * 1.001
        else:  # Downtrend
            support = np.min(prices[-window:]) * 0.999
            resistance = np.max(recent_prices[-5:])
        
        return support, resistance
    
    def generate_signal(self, prices: np.ndarray, index: int) -> Tuple[SignalDirection, float, float]:
        """
        Generate trading signal using multiple uncorrelated factors.
        Returns: (direction, confidence, sl_distance)
        """
        if index < self.lookback_period:
            return SignalDirection.NEUTRAL, 0.0, 0.0
        
        lookback = prices[index-self.lookback_period:index+1]
        
        # Factor 1: Mean Reversion
        mean_price = np.mean(lookback)
        current_price = prices[index]
        z_score = (current_price - mean_price) / (np.std(lookback) + 1e-10)
        
        # Factor 2: Momentum
        short_momentum = (prices[index] - prices[index-5]) / prices[index-5] if index >= 5 else 0
        long_momentum = (prices[index] - prices[index-20]) / prices[index-20] if index >= 20 else 0
        
        # Factor 3: Volatility
        volatility = np.std(np.diff(lookback[-10:])) if len(lookback) >= 10 else np.std(lookback)
        vol_regime = "HIGH" if volatility > np.std(prices[-50:]) * 1.2 else "LOW" if volatility < np.std(prices[-50:]) * 0.8 else "NORMAL"
        
        # Factor 4: Price Pattern
        recent_high = np.max(lookback[-5:])
        recent_low = np.min(lookback[-5:])
        price_position = (current_price - recent_low) / (recent_high - recent_low + 1e-10)
        
        # Factor 5: RSI-like momentum
        gains = np.maximum(np.diff(lookback[-14:]), 0)
        losses = np.maximum(-np.diff(lookback[-14:]), 0)
        avg_gain = np.mean(gains) if len(gains) > 0 else 0
        avg_loss = np.mean(losses) if len(losses) > 0 else 0
        rs = avg_gain / (avg_loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        # Combine signals (Medallion-style: multiple independent signals)
        signal_score = 0.0
        confidence_factors = []
        
        # Mean Reversion Signal (contrarian) - MORE AGGRESSIVE
        if z_score > 1.5:
            signal_score -= 0.4  # Overbought -> SELL
            confidence_factors.append(0.75)
        elif z_score < -1.5:
            signal_score += 0.4  # Oversold -> BUY
            confidence_factors.append(0.75)
        
        # Momentum Signal (trend following) - MORE AGGRESSIVE
        if short_momentum > 0.001 and long_momentum > 0:
            signal_score += 0.35  # Strong uptrend
            confidence_factors.append(0.70)
        elif short_momentum < -0.001 and long_momentum < 0:
            signal_score -= 0.35  # Strong downtrend
            confidence_factors.append(0.70)
        
        # RSI Signal - NEW
        if rsi > 70:
            signal_score -= 0.3  # Overbought
            confidence_factors.append(0.65)
        elif rsi < 30:
            signal_score += 0.3  # Oversold
            confidence_factors.append(0.65)
        
        # Volatility Breakout Signal - ADJUSTED
        if vol_regime == "HIGH" and price_position > 0.7:
            signal_score += 0.25  # Breakout in high volatility
            confidence_factors.append(0.65)
        elif vol_regime == "LOW" and price_position < 0.3:
            signal_score -= 0.25  # Breakdown in low volatility
            confidence_factors.append(0.65)
        
        # Price Position Signal - ADJUSTED
        if price_position > 0.85:
            signal_score -= 0.2  # Near high -> potential reversal
            confidence_factors.append(0.60)
        elif price_position < 0.15:
            signal_score += 0.2  # Near low -> potential bounce
            confidence_factors.append(0.60)
        
        # Determine direction
        if abs(signal_score) < 0.1:
            direction = SignalDirection.NEUTRAL
        elif signal_score > 0:
            direction = SignalDirection.BUY
        else:
            direction = SignalDirection.SELL
        
        # Calculate confidence (average of factors)
        confidence = np.mean(confidence_factors) if confidence_factors else 0.5
        
        # Calculate SL distance based on ATR - WIDER for higher win rate
        atr = self.calculate_atr(prices[:index+1])
        sl_distance = atr * 3.0 if vol_regime == "NORMAL" else atr * 3.5 if vol_regime == "HIGH" else atr * 2.5
        
        return direction, confidence, sl_distance
    
    def calculate_position_size(self, sl_distance: float) -> float:
        """Calculate position size using fixed fractional method."""
        risk_amount = self.balance * self.max_risk_per_trade
        # XAUUSD: 1 lot = 100 oz, pip value = $1 per 0.01 lot per pip
        # For simplicity: lot_size = risk_amount / (sl_distance * 100)
        lot_size = risk_amount / (sl_distance * 100 + 1e-10)
        return round(max(0.01, min(lot_size, 1.0)), 2)
    
    def simulate_trade(self, entry_price: float, direction: SignalDirection, 
                       sl_distance: float, prices: np.ndarray, index: int) -> TradeResult:
        """Simulate a trade with SL/TP management."""
        lot_size = self.calculate_position_size(sl_distance)
        
        # Use 1.05R target for highest win rate (like Medallion)
        # TP closer = higher win rate but lower reward
        tp_multiplier = 1.05
        
        if direction == SignalDirection.BUY:
            sl = entry_price - sl_distance
            tp1 = entry_price + sl_distance * tp_multiplier
        else:
            sl = entry_price + sl_distance
            tp1 = entry_price - sl_distance * tp_multiplier
        
        # Simulate price movement for next 20 bars
        max_bars = min(20, len(prices) - index - 1)
        exit_price = entry_price
        exit_reason = "TIME_EXIT"
        
        # Trailing stop variables
        trailing_sl = sl
        trailing_activation = 0.5  # Activate at 50% of TP distance
        
        for i in range(1, max_bars + 1):
            current_price = prices[index + i]
            
            if direction == SignalDirection.BUY:
                # Update trailing stop
                if current_price > entry_price + sl_distance * trailing_activation:
                    new_trailing = current_price - sl_distance * 0.8
                    trailing_sl = max(trailing_sl, new_trailing)
                
                # Check trailing SL first
                if current_price <= trailing_sl:
                    exit_price = max(trailing_sl, current_price)
                    exit_reason = "TRAILING_SL"
                    break
                # Check TP
                if current_price >= tp1:
                    exit_price = tp1
                    exit_reason = "TP_HIT"
                    break
            else:  # SELL
                # Update trailing stop
                if current_price < entry_price - sl_distance * trailing_activation:
                    new_trailing = current_price + sl_distance * 0.8
                    trailing_sl = min(trailing_sl, new_trailing)
                
                # Check trailing SL first
                if current_price >= trailing_sl:
                    exit_price = min(trailing_sl, current_price)
                    exit_reason = "TRAILING_SL"
                    break
                # Check TP
                if current_price <= tp1:
                    exit_price = tp1
                    exit_reason = "TP_HIT"
                    break
        
        # Calculate PnL
        if direction == SignalDirection.BUY:
            pnl_pips = (exit_price - entry_price) * 10  # XAUUSD: 1 pip = $0.1
        else:
            pnl_pips = (entry_price - exit_price) * 10
        
        pnl_usd = pnl_pips * lot_size * 10  # PnL in USD
        
        win = pnl_usd > 0
        
        return TradeResult(
            entry_price=entry_price,
            exit_price=exit_price,
            direction=direction,
            sl=sl,
            tp1=tp1,
            pnl_pips=pnl_pips,
            pnl_usd=pnl_usd,
            win=win,
            exit_reason=exit_reason
        )
    
    def run_backtest(self, prices: np.ndarray) -> Dict:
        """Run backtest on price data."""
        print("="*80)
        print("  MEDALLION STYLE BACKTEST - Target: 50/50 Win Rate")
        print("="*80)
        
        self.balance = self.initial_balance
        self.peak_balance = self.initial_balance
        self.trades = []
        
        # Track daily stats
        daily_trades = 0
        daily_pnl = 0.0
        
        for i in range(self.lookback_period, len(prices) - 1):
            # Reset daily stats
            if i % 100 == 0:
                daily_trades = 0
                daily_pnl = 0.0
            
            # Skip if too many daily trades
            if daily_trades >= self.max_daily_trades:
                continue
            
            # Generate signal
            direction, confidence, sl_distance = self.generate_signal(prices, i)
            
            # Only trade if confidence is high enough
            if confidence < 0.45:
                continue
            
            # Check drawdown limit
            dd = (self.peak_balance - self.balance) / self.peak_balance
            if dd > 0.10:  # 10% max drawdown
                continue
            
            # Simulate trade
            trade = self.simulate_trade(prices[i], direction, sl_distance, prices, i)
            self.trades.append(trade)
            
            # Update balance
            self.balance += trade.pnl_usd
            self.peak_balance = max(self.peak_balance, self.balance)
            daily_trades += 1
            daily_pnl += trade.pnl_usd
            
            # Track max drawdown
            current_dd = (self.peak_balance - self.balance) / self.peak_balance
            self.max_drawdown = max(self.max_drawdown, current_dd)
        
        return self._calculate_stats()
    
    def _calculate_stats(self) -> Dict:
        """Calculate backtest statistics."""
        if not self.trades:
            return {"error": "No trades"}
        
        wins = sum(1 for t in self.trades if t.win)
        losses = len(self.trades) - wins
        win_rate = wins / len(self.trades) if self.trades else 0
        
        total_pnl = sum(t.pnl_usd for t in self.trades)
        avg_pnl = total_pnl / len(self.trades)
        
        winning_trades = [t for t in self.trades if t.win]
        losing_trades = [t for t in self.trades if not t.win]
        
        avg_win = np.mean([t.pnl_usd for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl_usd for t in losing_trades]) if losing_trades else 0
        
        # Profit factor
        gross_profit = sum(t.pnl_usd for t in winning_trades)
        gross_loss = abs(sum(t.pnl_usd for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Sharpe ratio (simplified)
        returns = [t.pnl_usd / self.initial_balance for t in self.trades]
        sharpe = np.mean(returns) / (np.std(returns) + 1e-10) * np.sqrt(252)
        
        # Expectancy
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * abs(avg_loss))
        
        return {
            "total_trades": len(self.trades),
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "avg_pnl_per_trade": avg_pnl,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor,
            "sharpe_ratio": sharpe,
            "max_drawdown": self.max_drawdown,
            "expectancy": expectancy,
            "final_balance": self.balance,
            "return_pct": (self.balance - self.initial_balance) / self.initial_balance * 100
        }
    
    def print_results(self, stats: Dict):
        """Print backtest results."""
        print("\n" + "="*80)
        print("  BACKTEST RESULTS")
        print("="*80)
        
        print(f"\n  Total Trades: {stats['total_trades']}")
        print(f"  Wins: {stats['wins']} ({stats['win_rate']*100:.1f}%)")
        print(f"  Losses: {stats['losses']}")
        
        print(f"\n  Total PnL: ${stats['total_pnl']:+,.2f}")
        print(f"  Average PnL: ${stats['avg_pnl_per_trade']:+,.2f}")
        print(f"  Average Win: ${stats['avg_win']:+,.2f}")
        print(f"  Average Loss: ${stats['avg_loss']:+,.2f}")
        
        print(f"\n  Profit Factor: {stats['profit_factor']:.2f}")
        print(f"  Sharpe Ratio: {stats['sharpe_ratio']:.2f}")
        print(f"  Max Drawdown: {stats['max_drawdown']*100:.2f}%")
        print(f"  Expectancy: ${stats['expectancy']:+,.2f}")
        
        print(f"\n  Final Balance: ${stats['final_balance']:,.2f}")
        print(f"  Return: {stats['return_pct']:+.2f}%")
        
        # Check if we achieved 50/50
        if stats['win_rate'] >= 0.50:
            print("\n  ✅ ACHIEVED 50/50 WIN RATE!")
        else:
            print(f"\n  ❌ Current win rate: {stats['win_rate']*100:.1f}% (need 50%)")
        
        # Exit reason analysis
        tp_hits = sum(1 for t in self.trades if t.exit_reason == "TP_HIT")
        sl_hits = sum(1 for t in self.trades if t.exit_reason == "SL_HIT")
        time_exits = sum(1 for t in self.trades if t.exit_reason == "TIME_EXIT")
        
        print(f"\n  Exit Reasons:")
        print(f"    TP Hits: {tp_hits} ({tp_hits/len(self.trades)*100:.1f}%)")
        print(f"    SL Hits: {sl_hits} ({sl_hits/len(self.trades)*100:.1f}%)")
        print(f"    Time Exits: {time_exits} ({time_exits/len(self.trades)*100:.1f}%)")

def main():
    """Run backtest with synthetic data."""
    print("Generating realistic XAUUSD price data...")
    
    # Generate realistic XAUUSD price data
    np.random.seed(42)
    n_bars = 2000
    base_price = 2350.0
    
    # Create realistic price series with trends, ranges, and breakouts
    returns = np.random.randn(n_bars) * 0.0008
    # Add realistic patterns
    returns[100:300] += 0.0003  # Uptrend
    returns[300:500] -= 0.0005  # Downtrend
    returns[500:700] += np.random.randn(200) * 0.001  # Volatile recovery
    returns[700:900] += 0.0002  # Mild uptrend
    returns[900:1100] -= 0.0004  # Downtrend
    returns[1100:1300] += np.random.randn(200) * 0.0015  # High volatility
    returns[1300:1500] += 0.0006  # Strong uptrend
    returns[1500:1700] -= 0.0003  # Pullback
    returns[1700:2000] += np.random.randn(300) * 0.002  # Very volatile
    
    prices = base_price * np.exp(np.cumsum(returns))
    
    print(f"Price range: ${prices.min():.2f} - ${prices.max():.2f}")
    print(f"Total bars: {n_bars}")
    
    # Run backtest
    bt = MedallionStyleBacktester(initial_balance=10000.0)
    stats = bt.run_backtest(prices)
    bt.print_results(stats)
    
    return 0 if stats.get('win_rate', 0) >= 0.50 else 1

if __name__ == "__main__":
    sys.exit(main())
