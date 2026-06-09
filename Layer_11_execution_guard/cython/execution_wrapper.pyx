# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True
"""
LAYER 11: EXECUTION GUARD - Cython Wrapper
Python-C++ bridge for ultra-low-latency execution validation.
"""

from libc.stdint cimport int32_t, int64_t
from libcpp cimport bool
from libc.string cimport memcpy

cdef extern from "../cpp/execution_core.h" namespace "atikul::execution":
    cdef enum Session:
        ASIAN = 0
        LONDON = 1
        NEW_YORK = 2
        OVERLAP = 3
        OFF_HOURS = 4
    
    cdef struct ExecutionResult:
        bool fix_heartbeat_ok
        bool spread_ok
        bool session_active
        bool not_nfp_fomc
        bool position_limit_ok
        bool daily_loss_ok
        bool weekly_loss_ok
        bool drawdown_ok
        bool all_checks_passed
        double spread_bps
        double daily_loss_pct
        double weekly_loss_pct
        double drawdown_pct
        int32_t current_positions
        char failed_checks[512]
        int32_t failed_count
    
    cdef cppclass HeartbeatMonitor:
        HeartbeatMonitor(int64_t timeout_ns)
        void on_heartbeat() noexcept
        bool is_connected() noexcept
        double seconds_since_heartbeat() noexcept
        int64_t heartbeat_count() noexcept
    
    cdef cppclass SpreadValidator:
        SpreadValidator(double max_bps)
        bool validate(double bid, double ask) noexcept
        double avg_spread_bps() noexcept
        int32_t violation_count() noexcept
    
    cdef cppclass SessionChecker:
        SessionChecker()
        Session get_current_session(int32_t utc_hour) noexcept
        bool is_session_active(int32_t utc_hour) noexcept
        bool is_nfp_fomc_blocked(int32_t month, int32_t day, int32_t hour, int32_t minute) noexcept
    
    cdef cppclass PositionManager:
        PositionManager(int32_t max_concurrent, double max_daily, double max_weekly, double max_dd)
        bool can_open_position() noexcept
        void on_position_open() noexcept
        void on_position_close() noexcept
        void record_trade_pnl(double pnl) noexcept
        void daily_reset() noexcept
        void weekly_reset() noexcept
        int32_t open_count() noexcept
        double daily_loss_pct() noexcept
        double weekly_loss_pct() noexcept
        double drawdown_pct() noexcept
    
    cdef cppclass ExecutionGuard:
        ExecutionGuard()
        ExecutionResult check(double bid, double ask, int32_t year, int32_t month, int32_t day, int32_t hour, int32_t minute) noexcept
        HeartbeatMonitor& heartbeat()
        SpreadValidator& spread_validator()
        SessionChecker& session_checker()
        PositionManager& position_manager()


cdef class PyExecutionGuard:
    """Python wrapper for C++ ExecutionGuard."""
    cdef ExecutionGuard* _guard
    
    def __cinit__(self):
        self._guard = new ExecutionGuard()
    
    def __dealloc__(self):
        if self._guard != NULL:
            del self._guard
    
    def on_heartbeat(self):
        """Notify that FIX heartbeat received."""
        self._guard.heartbeat().on_heartbeat()
    
    def is_connected(self):
        """Check if FIX connection is alive."""
        return self._guard.heartbeat().is_connected()
    
    def seconds_since_heartbeat(self):
        """Seconds since last heartbeat."""
        return self._guard.heartbeat().seconds_since_heartbeat()
    
    def heartbeat_count(self):
        """Total heartbeats received."""
        return self._guard.heartbeat().heartbeat_count()
    
    def check(self, double bid, double ask, int year, int month, int day, int hour, int minute):
        """
        Run all execution checks.
        Returns dict with check results.
        """
        cdef ExecutionResult result = self._guard.check(
            bid, ask, year, month, day, hour, minute
        )
        
        failed = result.failed_checks[:result.failed_checks.index(b'\x00') if b'\x00' in result.failed_checks else len(result.failed_checks)]
        
        return {
            'fix_heartbeat_ok': result.fix_heartbeat_ok,
            'spread_ok': result.spread_ok,
            'session_active': result.session_active,
            'not_nfp_fomc': result.not_nfp_fomc,
            'position_limit_ok': result.position_limit_ok,
            'daily_loss_ok': result.daily_loss_ok,
            'weekly_loss_ok': result.weekly_loss_ok,
            'drawdown_ok': result.drawdown_ok,
            'all_checks_passed': result.all_checks_passed,
            'spread_bps': result.spread_bps,
            'daily_loss_pct': result.daily_loss_pct,
            'weekly_loss_pct': result.weekly_loss_pct,
            'drawdown_pct': result.drawdown_pct,
            'current_positions': result.current_positions,
            'failed_checks': failed.decode('utf-8', errors='ignore'),
            'failed_count': result.failed_count,
        }
    
    def on_position_open(self):
        """Record position open."""
        self._guard.position_manager().on_position_open()
    
    def on_position_close(self):
        """Record position close."""
        self._guard.position_manager().on_position_close()
    
    def record_trade_pnl(self, double pnl):
        """Record trade P&L."""
        self._guard.position_manager().record_trade_pnl(pnl)
    
    def daily_reset(self):
        """Reset daily P&L."""
        self._guard.position_manager().daily_reset()
    
    def weekly_reset(self):
        """Reset weekly P&L."""
        self._guard.position_manager().weekly_reset()
    
    @property
    def open_positions(self):
        return self._guard.position_manager().open_count()
    
    @property
    def daily_loss_pct(self):
        return self._guard.position_manager().daily_loss_pct()
    
    @property
    def weekly_loss_pct(self):
        return self._guard.position_manager().weekly_loss_pct()
    
    @property
    def drawdown_pct(self):
        return self._guard.position_manager().drawdown_pct()
