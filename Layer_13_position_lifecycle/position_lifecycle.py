"""
LAYER 13: POSITION LIFECYCLE MANAGER
Manages position from opening to closing with full tracking.

Features:
- Position opening with entry tracking
- Real-time P&L calculation
- Trailing stop implementation
- Take profit levels (TP1, TP2, TP3)
- Break-even stop movement
- Partial close support
- Position sizing based on risk
- Multi-position management
- Emergency close functionality
- Performance analytics

Position States:
- OPENING: Order submitted, waiting for fill
- OPEN: Position active
- CLOSING: Close order submitted
- CLOSED: Position closed
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics


class PositionSide(Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class PositionState(Enum):
    OPENING = "OPENING"
    OPEN = "OPEN"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"


@dataclass
class Position:
    """Position tracking data."""
    position_id: str
    symbol: str
    side: PositionSide
    state: PositionState = PositionState.OPENING
    
    # Entry
    entry_price: float = 0.0
    entry_time: float = 0.0
    quantity: float = 0.0
    
    # Current
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0
    
    # Stop Loss
    stop_loss: float = 0.0
    original_stop_loss: float = 0.0
    trailing_stop_active: bool = False
    trailing_stop_distance: float = 0.0
    trailing_stop_high: float = 0.0
    trailing_stop_low: float = float('inf')
    
    # Take Profit
    take_profit_1: float = 0.0
    take_profit_2: float = 0.0
    take_profit_3: float = 0.0
    tp1_hit: bool = False
    tp2_hit: bool = False
    tp3_hit: bool = False
    
    # Break-even
    break_even_enabled: bool = False
    break_even_trigger: float = 0.0
    break_even_offset: float = 0.0
    break_even_moved: bool = False
    
    # Partial close
    original_quantity: float = 0.0
    closed_quantity: float = 0.0
    
    # Exit
    exit_price: float = 0.0
    exit_time: float = 0.0
    exit_reason: str = ""
    realized_pnl: float = 0.0
    commission: float = 0.0
    slippage: float = 0.0
    
    # Metadata
    magic_number: int = 0
    comment: str = ""
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class PositionConfig:
    """Position management configuration."""
    max_positions: int = 3
    risk_per_trade_pct: float = 1.0  # Risk 1% per trade
    max_risk_total_pct: float = 3.0  # Max 3% total risk
    default_sl_atr_multiplier: float = 2.0
    default_tp_atr_multiplier: float = 3.0
    trailing_stop_activation_pct: float = 1.0  # Activate at 1% profit
    trailing_stop_distance_pct: float = 0.5  # Trail by 0.5%
    break_even_trigger_pct: float = 0.5  # Move to BE at 0.5%
    break_even_offset_pips: float = 5.0  # BE + 5 pips


class PositionLifecycle:
    """
    LAYER 13: Position Lifecycle Manager
    Manages positions from opening to closing.
    """
    
    def __init__(self, config: Optional[PositionConfig] = None):
        self.config = config or PositionConfig()
        
        # Position tracking
        self._positions: Dict[str, Position] = {}
        self._closed_positions: List[Position] = []
        self._position_counter = 0
        
        # Account state
        self._equity = 10000.0
        self._balance = 10000.0
        self._free_margin = 10000.0
        
        # Statistics
        self._total_trades = 0
        self._winning_trades = 0
        self._losing_trades = 0
        self._total_pnl = 0.0
        self._max_drawdown = 0.0
        self._peak_equity = 10000.0
        
        # Performance tracking
        self._daily_pnl: List[float] = []
        self._weekly_pnl: List[float] = []
        self._monthly_pnl: List[float] = []
    
    def generate_position_id(self) -> str:
        """Generate unique position ID."""
        self._position_counter += 1
        return f"POS{int(time.time())}{self._position_counter:06d}"
    
    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        symbol: str = "XAUUSD",
    ) -> float:
        """Calculate position size based on risk management."""
        # Risk amount in dollars
        risk_amount = self._equity * (self.config.risk_per_trade_pct / 100)
        
        # Risk per unit
        risk_per_unit = abs(entry_price - stop_loss)
        
        if risk_per_unit <= 0:
            return 0.0
        
        # Calculate size
        size = risk_amount / risk_per_unit
        
        # Round to lot size (0.01 for forex)
        size = round(size, 2)
        
        # Ensure minimum
        size = max(size, 0.01)
        
        return size
    
    def open_position(
        self,
        symbol: str,
        side: PositionSide,
        entry_price: float,
        quantity: float,
        stop_loss: float,
        take_profit_1: float = 0.0,
        take_profit_2: float = 0.0,
        take_profit_3: float = 0.0,
        magic_number: int = 0,
        comment: str = "",
    ) -> Position:
        """Open a new position."""
        # Check max positions
        open_count = len([p for p in self._positions.values() if p.state == PositionState.OPEN])
        if open_count >= self.config.max_positions:
            raise ValueError(f"Max positions ({self.config.max_positions}) reached")
        
        # Create position
        position = Position(
            position_id=self.generate_position_id(),
            symbol=symbol,
            side=side,
            state=PositionState.OPEN,
            entry_price=entry_price,
            entry_time=time.time(),
            quantity=quantity,
            original_quantity=quantity,
            current_price=entry_price,
            stop_loss=stop_loss,
            original_stop_loss=stop_loss,
            take_profit_1=take_profit_1,
            take_profit_2=take_profit_2,
            take_profit_3=take_profit_3,
            magic_number=magic_number,
            comment=comment,
        )
        
        self._positions[position.position_id] = position
        return position
    
    def update_price(self, position_id: str, current_price: float) -> Optional[Position]:
        """Update position with current price."""
        position = self._positions.get(position_id)
        if not position or position.state != PositionState.OPEN:
            return None
        
        position.current_price = current_price
        
        # Calculate P&L
        if position.side == PositionSide.LONG:
            position.unrealized_pnl = (current_price - position.entry_price) * position.quantity
        else:
            position.unrealized_pnl = (position.entry_price - current_price) * position.quantity
        
        position.unrealized_pnl_pct = (position.unrealized_pnl / self._equity) * 100
        
        # Update trailing stop
        self._update_trailing_stop(position, current_price)
        
        # Check break-even
        self._check_break_even(position, current_price)
        
        # Check take profits
        self._check_take_profits(position, current_price)
        
        # Check stop loss
        self._check_stop_loss(position, current_price)
        
        return position
    
    def _update_trailing_stop(self, position: Position, current_price: float) -> None:
        """Update trailing stop if enabled."""
        if not self.config.trailing_stop_activation_pct:
            return
        
        # Calculate profit percentage
        if position.side == PositionSide.LONG:
            profit_pct = ((current_price - position.entry_price) / position.entry_price) * 100
            position.trailing_stop_high = max(position.trailing_stop_high, current_price)
        else:
            profit_pct = ((position.entry_price - current_price) / position.entry_price) * 100
            position.trailing_stop_low = min(position.trailing_stop_low, current_price)
        
        # Activate trailing stop
        if not position.trailing_stop_active and profit_pct >= self.config.trailing_stop_activation_pct:
            position.trailing_stop_active = True
            position.trailing_stop_distance = current_price * (self.config.trailing_stop_distance_pct / 100)
        
        # Update trailing stop
        if position.trailing_stop_active:
            if position.side == PositionSide.LONG:
                new_stop = position.trailing_stop_high - position.trailing_stop_distance
                if new_stop > position.stop_loss:
                    position.stop_loss = new_stop
            else:
                new_stop = position.trailing_stop_low + position.trailing_stop_distance
                if new_stop < position.stop_loss:
                    position.stop_loss = new_stop
    
    def _check_break_even(self, position: Position, current_price: float) -> None:
        """Check if stop should move to break-even."""
        if not self.config.break_even_trigger_pct or position.break_even_moved:
            return
        
        # Calculate profit percentage
        if position.side == PositionSide.LONG:
            profit_pct = ((current_price - position.entry_price) / position.entry_price) * 100
        else:
            profit_pct = ((position.entry_price - current_price) / position.entry_price) * 100
        
        # Move to break-even
        if profit_pct >= self.config.break_even_trigger_pct:
            if position.side == PositionSide.LONG:
                new_stop = position.entry_price + (position.break_even_offset * 0.0001 * position.entry_price)
            else:
                new_stop = position.entry_price - (position.break_even_offset * 0.0001 * position.entry_price)
            
            if not position.trailing_stop_active or new_stop > position.stop_loss:
                position.stop_loss = new_stop
                position.break_even_moved = True
    
    def _check_take_profits(self, position: Position, current_price: float) -> None:
        """Check if take profit levels are hit."""
        if position.side == PositionSide.LONG:
            if not position.tp1_hit and position.take_profit_1 > 0 and current_price >= position.take_profit_1:
                position.tp1_hit = True
                self._partial_close(position, 0.33, "TP1")
            
            if not position.tp2_hit and position.take_profit_2 > 0 and current_price >= position.take_profit_2:
                position.tp2_hit = True
                self._partial_close(position, 0.5, "TP2")
            
            if not position.tp3_hit and position.take_profit_3 > 0 and current_price >= position.take_profit_3:
                position.tp3_hit = True
                self._close_position(position, current_price, "TP3")
        else:
            if not position.tp1_hit and position.take_profit_1 > 0 and current_price <= position.take_profit_1:
                position.tp1_hit = True
                self._partial_close(position, 0.33, "TP1")
            
            if not position.tp2_hit and position.take_profit_2 > 0 and current_price <= position.take_profit_2:
                position.tp2_hit = True
                self._partial_close(position, 0.5, "TP2")
            
            if not position.tp3_hit and position.take_profit_3 > 0 and current_price <= position.take_profit_3:
                position.tp3_hit = True
                self._close_position(position, current_price, "TP3")
    
    def _check_stop_loss(self, position: Position, current_price: float) -> None:
        """Check if stop loss is hit."""
        if position.side == PositionSide.LONG:
            if current_price <= position.stop_loss:
                self._close_position(position, position.stop_loss, "SL")
        else:
            if current_price >= position.stop_loss:
                self._close_position(position, position.stop_loss, "SL")
    
    def _partial_close(self, position: Position, fraction: float, reason: str) -> None:
        """Partially close position."""
        close_qty = position.quantity * fraction
        close_qty = round(close_qty, 2)
        
        if close_qty >= 0.01:
            position.quantity -= close_qty
            position.closed_quantity += close_qty
            
            # Calculate realized P&L for closed portion
            if position.side == PositionSide.LONG:
                pnl = (position.current_price - position.entry_price) * close_qty
            else:
                pnl = (position.entry_price - position.current_price) * close_qty
            
            position.realized_pnl += pnl
            self._total_pnl += pnl
            self._equity += pnl
    
    def _close_position(self, position: Position, exit_price: float, reason: str) -> None:
        """Close position completely."""
        position.state = PositionState.CLOSED
        position.exit_price = exit_price
        position.exit_time = time.time()
        position.exit_reason = reason
        
        # Calculate final P&L
        if position.side == PositionSide.LONG:
            pnl = (exit_price - position.entry_price) * position.quantity
        else:
            pnl = (position.entry_price - exit_price) * position.quantity
        
        position.realized_pnl += pnl
        position.unrealized_pnl = 0
        
        # Update statistics
        self._total_trades += 1
        self._total_pnl += position.realized_pnl
        self._equity += pnl
        
        if position.realized_pnl >= 0:
            self._winning_trades += 1
        else:
            self._losing_trades += 1
        
        # Update drawdown
        if self._equity > self._peak_equity:
            self._peak_equity = self._equity
        
        drawdown = (self._peak_equity - self._equity) / self._peak_equity
        if drawdown > self._max_drawdown:
            self._max_drawdown = drawdown
        
        # Move to closed positions
        self._closed_positions.append(position)
        del self._positions[position.position_id]
    
    def close_position(self, position_id: str, exit_price: float, reason: str = "MANUAL") -> Optional[Position]:
        """Manually close a position."""
        position = self._positions.get(position_id)
        if not position or position.state != PositionState.OPEN:
            return None
        
        self._close_position(position, exit_price, reason)
        return position
    
    def emergency_close_all(self, current_price: float, reason: str = "EMERGENCY") -> List[Position]:
        """Emergency close all positions."""
        closed = []
        for position_id in list(self._positions.keys()):
            position = self._positions.get(position_id)
            if position and position.state == PositionState.OPEN:
                self._close_position(position, current_price, reason)
                closed.append(position)
        return closed
    
    def modify_stop_loss(self, position_id: str, new_stop: float) -> bool:
        """Modify stop loss level."""
        position = self._positions.get(position_id)
        if not position or position.state != PositionState.OPEN:
            return False
        
        position.stop_loss = new_stop
        return True
    
    def modify_take_profit(self, position_id: str, tp1: float = 0, tp2: float = 0, tp3: float = 0) -> bool:
        """Modify take profit levels."""
        position = self._positions.get(position_id)
        if not position or position.state != PositionState.OPEN:
            return False
        
        if tp1 > 0:
            position.take_profit_1 = tp1
        if tp2 > 0:
            position.take_profit_2 = tp2
        if tp3 > 0:
            position.take_profit_3 = tp3
        
        return True
    
    @property
    def open_positions(self) -> List[Position]:
        """Get all open positions."""
        return [p for p in self._positions.values() if p.state == PositionState.OPEN]
    
    @property
    def open_count(self) -> int:
        """Get count of open positions."""
        return len(self.open_positions)
    
    @property
    def total_unrealized_pnl(self) -> float:
        """Get total unrealized P&L."""
        return sum(p.unrealized_pnl for p in self.open_positions)
    
    @property
    def total_realized_pnl(self) -> float:
        """Get total realized P&L."""
        return self._total_pnl
    
    @property
    def win_rate(self) -> float:
        """Get win rate percentage."""
        if self._total_trades == 0:
            return 0.0
        return (self._winning_trades / self._total_trades) * 100
    
    @property
    def profit_factor(self) -> float:
        """Get profit factor."""
        wins = sum(p.realized_pnl for p in self._closed_positions if p.realized_pnl > 0)
        losses = abs(sum(p.realized_pnl for p in self._closed_positions if p.realized_pnl < 0))
        if losses == 0:
            return float('inf') if wins > 0 else 0.0
        return wins / losses
    
    @property
    def sharpe_ratio(self) -> float:
        """Calculate Sharpe ratio (simplified)."""
        if len(self._closed_positions) < 2:
            return 0.0
        
        returns = [p.realized_pnl / self._equity for p in self._closed_positions]
        if not returns:
            return 0.0
        
        avg_return = statistics.mean(returns)
        std_return = statistics.stdev(returns) if len(returns) > 1 else 1.0
        
        if std_return == 0:
            return 0.0
        
        # Annualized (assuming 252 trading days)
        return (avg_return / std_return) * (252 ** 0.5)
    
    @property
    def stats(self) -> Dict:
        """Get comprehensive statistics."""
        return {
            "equity": self._equity,
            "balance": self._balance,
            "open_positions": self.open_count,
            "total_unrealized_pnl": self.total_unrealized_pnl,
            "total_realized_pnl": self._total_pnl,
            "total_trades": self._total_trades,
            "winning_trades": self._winning_trades,
            "losing_trades": self._losing_trades,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self._max_drawdown * 100,
            "peak_equity": self._peak_equity,
        }
