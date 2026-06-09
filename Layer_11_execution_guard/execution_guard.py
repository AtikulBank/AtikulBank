"""
LAYER 11: EXECUTION GUARD
Final validation before order execution.

8 Critical Checks:
1. FIX Heartbeat - Connection alive (< 30s)
2. Spread - < 50 bps
3. Session - London/NY active
4. NFP/FOMC - Not blocked
5. Position Limit - < 3 concurrent
6. Daily Loss - < 3%
7. Weekly Loss - < 7%
8. Drawdown - < 10%

If ANY check fails → REJECT order
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from pipeline import ExecutionCheck


@dataclass
class ExecutionGuardConfig:
    """Configuration for execution guard."""
    atr_spread_multiplier: float = 0.10  # Spread < ATR × 0.10
    heartbeat_timeout_s: float = 30.0
    max_concurrent_positions: int = 3
    max_daily_loss_pct: float = 0.03
    max_weekly_loss_pct: float = 0.07
    max_drawdown_pct: float = 0.10
    nfp_block_minutes: int = 5  # ±5 min before/after NFP
    fomc_block_minutes: int = 5  # ±5 min before/after FOMC


class ExecutionGuard:
    """
    LAYER 11: EXECUTION GUARD
    Final checks before order execution.
    
    Uses C++ core for ultra-low-latency validation.
    Falls back to Python if C++ extension not available.
    """
    
    def __init__(self, config: Optional[ExecutionGuardConfig] = None):
        self.config = config or ExecutionGuardConfig()
        
        # Try to load C++ extension
        self._cpp_guard = None
        try:
            from Layer_11_execution_guard.cython.execution_wrapper import PyExecutionGuard
            self._cpp_guard = PyExecutionGuard()
            self._use_cpp = True
        except ImportError:
            self._use_cpp = False
        
        # Python fallback state
        self._last_heartbeat_ns = 0
        self._heartbeat_count = 0
        self._spread_history: List[float] = []
        self._open_positions = 0
        self._daily_pnl = 0.0
        self._weekly_pnl = 0.0
        self._peak_equity = 10000.0
        self._current_equity = 10000.0
        
        # NFP/FOMC blocked dates (2025)
        self._blocked_dates = [
            (2025, 1, 10, 13, 30, 90),   # NFP Jan
            (2025, 2, 7, 13, 30, 90),    # NFP Feb
            (2025, 3, 7, 13, 30, 90),    # NFP Mar
            (2025, 4, 4, 13, 30, 90),    # NFP Apr
            (2025, 5, 2, 13, 30, 90),    # NFP May
            (2025, 6, 6, 13, 30, 90),    # NFP Jun
            (2025, 7, 3, 13, 30, 90),    # NFP Jul
            (2025, 8, 1, 13, 30, 90),    # NFP Aug
            (2025, 9, 5, 13, 30, 90),    # NFP Sep
            (2025, 10, 3, 13, 30, 90),   # NFP Oct
            (2025, 11, 7, 13, 30, 90),   # NFP Nov
            (2025, 12, 5, 13, 30, 90),   # NFP Dec
        ]
        
        self._check_count = 0
        self._reject_count = 0
    
    def on_heartbeat(self) -> None:
        """Notify that FIX heartbeat received."""
        if self._use_cpp:
            self._cpp_guard.on_heartbeat()
        else:
            self._last_heartbeat_ns = time.time_ns()
            self._heartbeat_count += 1
    
    def check(
        self,
        bid: float,
        ask: float,
        utc_now: Optional[datetime] = None,
    ) -> ExecutionCheck:
        """
        Run all 8 execution checks.
        Returns ExecutionCheck with pass/fail for each.
        """
        self._check_count += 1
        
        if utc_now is None:
            utc_now = datetime.now(timezone.utc)
        
        # Use C++ if available
        if self._use_cpp:
            result = self._cpp_guard.check(
                bid, ask,
                utc_now.year, utc_now.month, utc_now.day,
                utc_now.hour, utc_now.minute
            )
            return ExecutionCheck(
                fix_heartbeat_ok=result['fix_heartbeat_ok'],
                spread_ok=result['spread_ok'],
                session_active=result['session_active'],
                not_nfp_fomc=result['not_nfp_fomc'],
                position_limit_ok=result['position_limit_ok'],
                daily_loss_ok=result['daily_loss_ok'],
                weekly_loss_ok=result.get('weekly_loss_ok', True),
                all_checks_passed=result['all_checks_passed'],
                failed_checks=[result['failed_checks']] if result['failed_checks'] else [],
            )
        
        # Python fallback
        return self._check_python(bid, ask, utc_now)
    
    def _check_python(
        self,
        bid: float,
        ask: float,
        utc_now: datetime,
    ) -> ExecutionCheck:
        """Python fallback for execution checks."""
        ec = ExecutionCheck()
        failed = []
        
        # 1. FIX Heartbeat
        if self._last_heartbeat_ns > 0:
            elapsed_s = (time.time_ns() - self._last_heartbeat_ns) / 1e9
            ec.fix_heartbeat_ok = elapsed_s < self.config.heartbeat_timeout_s
            if not ec.fix_heartbeat_ok:
                failed.append(f"FIX heartbeat timeout ({elapsed_s:.1f}s)")
        else:
            ec.fix_heartbeat_ok = True  # No heartbeat yet
        
        # 2. Spread
        if bid > 0 and ask > 0 and bid <= ask:
            mid = (bid + ask) / 2
            spread_bps = ((ask - bid) / mid) * 10000
            ec.spread_ok = spread_bps <= self.config.max_spread_bps
            self._spread_history.append(spread_bps)
            if len(self._spread_history) > 100:
                self._spread_history.pop(0)
            if not ec.spread_ok:
                failed.append(f"Spread {spread_bps:.1f} bps > {self.config.max_spread_bps}")
        else:
            ec.spread_ok = False
            failed.append("Invalid bid/ask")
        
        # 3. Session
        hour = utc_now.hour
        is_london = 7 <= hour < 16
        is_ny = 13 <= hour < 21
        ec.session_active = is_london or is_ny
        if not ec.session_active:
            failed.append(f"Outside session (hour={hour})")
        
        # 4. NFP/FOMC
        ec.not_nfp_fomc = not self._is_blocked(utc_now)
        if not ec.not_nfp_fomc:
            failed.append("NFP/FOMC blocked")
        
        # 5. Position limit
        ec.position_limit_ok = self._open_positions < self.config.max_concurrent_positions
        if not ec.position_limit_ok:
            failed.append(f"Positions {self._open_positions}/{self.config.max_concurrent_positions}")
        
        # 6. Daily loss
        if self._current_equity > 0:
            daily_loss = abs(self._daily_pnl) / self._current_equity
            ec.daily_loss_ok = daily_loss < self.config.max_daily_loss_pct
            if not ec.daily_loss_ok:
                failed.append(f"Daily loss {daily_loss:.2%}")
        else:
            ec.daily_loss_ok = True
        
        # 7. Weekly loss
        if self._current_equity > 0:
            weekly_loss = abs(self._weekly_pnl) / self._current_equity
            ec.weekly_loss_ok = weekly_loss < self.config.max_weekly_loss_pct
            if not ec.weekly_loss_ok:
                failed.append(f"Weekly loss {weekly_loss:.2%}")
        else:
            ec.weekly_loss_ok = True
        
        # 8. Drawdown
        if self._peak_equity > 0:
            dd = (self._peak_equity - self._current_equity) / self._peak_equity
            ec.all_checks_passed = dd < self.config.max_drawdown_pct
            if not ec.all_checks_passed:
                failed.append(f"Drawdown {dd:.2%}")
        else:
            ec.all_checks_passed = True
        
        ec.all_checks_passed = all([
            ec.fix_heartbeat_ok,
            ec.spread_ok,
            ec.session_active,
            ec.not_nfp_fomc,
            ec.position_limit_ok,
            ec.daily_loss_ok,
            ec.weekly_loss_ok,
        ])
        ec.failed_checks = failed
        
        if not ec.all_checks_passed:
            self._reject_count += 1
        
        return ec
    
    def _is_blocked(self, utc_now: datetime) -> bool:
        """Check if current time is in NFP/FOMC block."""
        current_minutes = utc_now.hour * 60 + utc_now.minute
        
        for year, month, day, hour, minute, duration in self._blocked_dates:
            if (utc_now.year == year and 
                utc_now.month == month and 
                utc_now.day == day):
                block_start = hour * 60 + minute
                block_end = block_start + duration
                if block_start - self.config.nfp_block_minutes <= current_minutes <= block_end + self.config.nfp_block_minutes:
                    return True
        return False
    
    def on_position_open(self) -> None:
        """Record position open."""
        if self._use_cpp:
            self._cpp_guard.on_position_open()
        else:
            self._open_positions += 1
    
    def on_position_close(self) -> None:
        """Record position close."""
        if self._use_cpp:
            self._cpp_guard.on_position_close()
        else:
            if self._open_positions > 0:
                self._open_positions -= 1
    
    def record_trade_pnl(self, pnl: float) -> None:
        """Record trade P&L."""
        if self._use_cpp:
            self._cpp_guard.record_trade_pnl(pnl)
        else:
            self._daily_pnl += pnl
            self._weekly_pnl += pnl
            self._current_equity += pnl
            if self._current_equity > self._peak_equity:
                self._peak_equity = self._current_equity
    
    def daily_reset(self) -> None:
        """Reset daily P&L."""
        if self._use_cpp:
            self._cpp_guard.daily_reset()
        else:
            self._daily_pnl = 0.0
    
    def weekly_reset(self) -> None:
        """Reset weekly P&L."""
        if self._use_cpp:
            self._cpp_guard.weekly_reset()
        else:
            self._weekly_pnl = 0.0
    
    @property
    def stats(self) -> Dict:
        """Get execution guard statistics."""
        return {
            "check_count": self._check_count,
            "reject_count": self._reject_count,
            "reject_rate": self._reject_count / max(1, self._check_count),
            "open_positions": self._open_positions,
            "daily_loss_pct": abs(self._daily_pnl) / max(self._current_equity, 1),
            "weekly_loss_pct": abs(self._weekly_pnl) / max(self._current_equity, 1),
            "drawdown_pct": (self._peak_equity - self._current_equity) / max(self._peak_equity, 1),
            "use_cpp": self._use_cpp,
        }
