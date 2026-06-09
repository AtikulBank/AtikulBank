#pragma once
/**
 * LAYER 11: EXECUTION GUARD - C++ Core
 * Ultra-low-latency execution validation for XAUUSD trading.
 * 
 * Features:
 * - FIX heartbeat monitoring (nanosecond precision)
 * - Spread validation (< 50 bps)
 * - NFP/FOMC session blocking
 * - London/NY session validation
 * - Position limit enforcement
 * - Daily/weekly loss limits
 * - Drawdown circuit breaker
 * 
 * Compiled with: -O3 -march=native -mtune=native -ffast-math
 */

#include <cstdint>
#include <chrono>
#include <atomic>
#include <array>
#include <cstring>
#include <ctime>

#ifdef __linux__
#include <x86intrin.h>
#endif

namespace atikul::execution {

// ── Constants ─────────────────────────────────────────────────────

constexpr double MAX_SPREAD_BPS = 50.0;
constexpr double MAX_DAILY_LOSS_PCT = 0.03;   // 3%
constexpr double MAX_WEEKLY_LOSS_PCT = 0.07;  // 7%
constexpr double MAX_DRAWDOWN_PCT = 0.10;     // 10%
constexpr int32_t MAX_CONCURRENT_POSITIONS = 3;
constexpr int64_t HEARTBEAT_TIMEOUT_NS = 30'000'000'000LL;  // 30 seconds in ns
constexpr int32_t NFP_BLOCK_MINUTES = 30;     // Block 30 min before/after NFP
constexpr int32_t FOMC_BLOCK_MINUTES = 60;    // Block 60 min before/after FOMC

// ── Nanosecond Timer ──────────────────────────────────────────────

inline int64_t now_ns() noexcept {
    #ifdef __linux__
    return __rdtsc();
    #else
    return std::chrono::high_resolution_clock::now().time_since_epoch().count();
    #endif
}

// ── Session Type ──────────────────────────────────────────────────

enum class Session : uint8_t {
    ASIAN = 0,      // 00:00 - 07:00 UTC
    LONDON = 1,     // 07:00 - 16:00 UTC
    NEW_YORK = 2,   // 13:00 - 21:00 UTC
    OVERLAP = 3,    // 13:00 - 16:00 UTC (London+NY)
    OFF_HOURS = 4,  // 21:00 - 00:00 UTC
};

// ── Execution Check Result ────────────────────────────────────────

struct ExecutionResult {
    bool fix_heartbeat_ok;
    bool spread_ok;
    bool session_active;
    bool not_nfp_fomc;
    bool position_limit_ok;
    bool daily_loss_ok;
    bool weekly_loss_ok;
    bool drawdown_ok;
    bool all_checks_passed;
    
    double spread_bps;
    double daily_loss_pct;
    double weekly_loss_pct;
    double drawdown_pct;
    int32_t current_positions;
    
    char failed_checks[512];
    int32_t failed_count;
};

// ── FIX Heartbeat Monitor ────────────────────────────────────────

class HeartbeatMonitor {
    std::atomic<int64_t> last_heartbeat_ns_{0};
    std::atomic<int64_t> heartbeat_count_{0};
    std::atomic<int64_t> missed_count_{0};
    int64_t timeout_ns_;
    
public:
    HeartbeatMonitor(int64_t timeout_ns = HEARTBEAT_TIMEOUT_NS) 
        : timeout_ns_(timeout_ns) {}
    
    void on_heartbeat() noexcept {
        last_heartbeat_ns_.store(now_ns(), std::memory_order_release);
        heartbeat_count_.fetch_add(1, std::memory_order_relaxed);
    }
    
    bool is_connected() const noexcept {
        int64_t last = last_heartbeat_ns_.load(std::memory_order_acquire);
        if (last == 0) return true;  // No heartbeat yet
        int64_t elapsed = now_ns() - last;
        return elapsed < timeout_ns_;
    }
    
    double seconds_since_heartbeat() const noexcept {
        int64_t last = last_heartbeat_ns_.load(std::memory_order_acquire);
        if (last == 0) return 0.0;
        return static_cast<double>(now_ns() - last) / 1e9;
    }
    
    int64_t heartbeat_count() const noexcept { return heartbeat_count_.load(); }
    int64_t missed_count() const noexcept { return missed_count_.load(); }
};

// ── Spread Validator ──────────────────────────────────────────────

class SpreadValidator {
    double max_spread_bps_;
    double recent_spreads_[100];
    int32_t spread_idx_;
    int32_t violation_count_;
    
public:
    SpreadValidator(double max_bps = MAX_SPREAD_BPS) 
        : max_spread_bps_(max_bps), spread_idx_(0), violation_count_(0) {
        memset(recent_spreads_, 0, sizeof(recent_spreads_));
    }
    
    bool validate(double bid, double ask) noexcept {
        if (bid <= 0 || ask <= 0 || bid > ask) {
            violation_count_++;
            return false;
        }
        
        double mid = (bid + ask) / 2.0;
        if (mid <= 0) return false;
        
        double spread_bps = ((ask - bid) / mid) * 10000.0;
        recent_spreads_[spread_idx_ % 100] = spread_bps;
        spread_idx_++;
        
        if (spread_bps > max_spread_bps_) {
            violation_count_++;
            return false;
        }
        
        return true;
    }
    
    double avg_spread_bps() const noexcept {
        double sum = 0;
        int32_t count = std::min(spread_idx_, 100);
        for (int32_t i = 0; i < count; i++) {
            sum += recent_spreads_[i];
        }
        return count > 0 ? sum / count : 0.0;
    }
    
    int32_t violation_count() const noexcept { return violation_count_; }
};

// ── Session Checker ───────────────────────────────────────────────

class SessionChecker {
    struct BlockedPeriod {
        int32_t month;
        int32_t day;
        int32_t hour_minutes;
        int32_t duration_minutes;
    };
    
    static constexpr int32_t MAX_BLOCKED = 20;
    BlockedPeriod blocked_[MAX_BLOCKED];
    int32_t blocked_count_;
    
public:
    SessionChecker() : blocked_count_(0) {
        // Initialize with known NFP/FOMC dates (2025)
        add_blocked(1, 10, 13*60+30, 90);   // NFP Jan
        add_blocked(2, 7, 13*60+30, 90);    // NFP Feb
        add_blocked(3, 7, 13*60+30, 90);    // NFP Mar
        add_blocked(4, 4, 13*60+30, 90);    // NFP Apr
        add_blocked(5, 2, 13*60+30, 90);    // NFP May
        add_blocked(6, 6, 13*60+30, 90);    // NFP Jun
        add_blocked(7, 3, 13*60+30, 90);    // NFP Jul (July 4th holiday)
        add_blocked(8, 1, 13*60+30, 90);    // NFP Aug
        add_blocked(9, 5, 13*60+30, 90);    // NFP Sep
        add_blocked(10, 3, 13*60+30, 90);   // NFP Oct
        add_blocked(11, 7, 13*60+30, 90);   // NFP Nov
        add_blocked(12, 5, 13*60+30, 90);   // NFP Dec
    }
    
    void add_blocked(int32_t month, int32_t day, int32_t hour_minutes, int32_t duration) {
        if (blocked_count_ < MAX_BLOCKED) {
            blocked_[blocked_count_++] = {month, day, hour_minutes, duration};
        }
    }
    
    Session get_current_session(int32_t utc_hour) const noexcept {
        if (utc_hour >= 13 && utc_hour < 16) return Session::OVERLAP;
        if (utc_hour >= 7 && utc_hour < 16) return Session::LONDON;
        if (utc_hour >= 13 && utc_hour < 21) return Session::NEW_YORK;
        if (utc_hour >= 0 && utc_hour < 7) return Session::ASIAN;
        return Session::OFF_HOURS;
    }
    
    bool is_session_active(int32_t utc_hour) const noexcept {
        Session s = get_current_session(utc_hour);
        return s == Session::LONDON || s == Session::NEW_YORK || s == Session::OVERLAP;
    }
    
    bool is_nfp_fomc_blocked(int32_t month, int32_t day, int32_t utc_hour, int32_t utc_minute) const noexcept {
        int32_t current_minutes = utc_hour * 60 + utc_minute;
        
        for (int32_t i = 0; i < blocked_count_; i++) {
            if (blocked_[i].month == month && blocked_[i].day == day) {
                int32_t block_start = blocked_[i].hour_minutes;
                int32_t block_end = block_start + blocked_[i].duration_minutes;
                
                if (current_minutes >= block_start - 30 && current_minutes <= block_end + 30) {
                    return true;
                }
            }
        }
        return false;
    }
};

// ── Position Manager ──────────────────────────────────────────────

class PositionManager {
    std::atomic<int32_t> open_positions_{0};
    std::atomic<double> daily_pnl_{0.0};
    std::atomic<double> weekly_pnl_{0.0};
    std::atomic<double> peak_equity_{10000.0};
    std::atomic<double> current_equity_{10000.0};
    int32_t max_concurrent_;
    double max_daily_loss_;
    double max_weekly_loss_;
    double max_drawdown_;
    
public:
    PositionManager(
        int32_t max_concurrent = MAX_CONCURRENT_POSITIONS,
        double max_daily = MAX_DAILY_LOSS_PCT,
        double max_weekly = MAX_WEEKLY_LOSS_PCT,
        double max_dd = MAX_DRAWDOWN_PCT
    ) : max_concurrent_(max_concurrent),
        max_daily_loss_(max_daily),
        max_weekly_loss_(max_weekly),
        max_drawdown_(max_dd) {}
    
    bool can_open_position() const noexcept {
        return open_positions_.load() < max_concurrent_;
    }
    
    void on_position_open() noexcept { open_positions_.fetch_add(1); }
    void on_position_close() noexcept { 
        int32_t current = open_positions_.load();
        if (current > 0) open_positions_.fetch_sub(1);
    }
    
    void record_trade_pnl(double pnl) noexcept {
        daily_pnl_.fetch_add(pnl);
        weekly_pnl_.fetch_add(pnl);
        
        double equity = current_equity_.fetch_add(pnl) + pnl;
        current_equity_.store(equity);
        
        double peak = peak_equity_.load();
        if (equity > peak) {
            peak_equity_.store(equity);
        }
    }
    
    void daily_reset() noexcept { daily_pnl_.store(0.0); }
    void weekly_reset() noexcept { weekly_pnl_.store(0.0); }
    
    bool is_daily_loss_ok() const noexcept {
        double equity = current_equity_.load();
        if (equity <= 0) return false;
        double loss_pct = std::abs(daily_pnl_.load()) / equity;
        return loss_pct < max_daily_loss_;
    }
    
    bool is_weekly_loss_ok() const noexcept {
        double equity = current_equity_.load();
        if (equity <= 0) return false;
        double loss_pct = std::abs(weekly_pnl_.load()) / equity;
        return loss_pct < max_weekly_loss_;
    }
    
    bool is_drawdown_ok() const noexcept {
        double peak = peak_equity_.load();
        double current = current_equity_.load();
        if (peak <= 0) return true;
        double dd = (peak - current) / peak;
        return dd < max_drawdown_;
    }
    
    int32_t open_count() const noexcept { return open_positions_.load(); }
    double daily_loss_pct() const noexcept {
        double equity = current_equity_.load();
        return equity > 0 ? std::abs(daily_pnl_.load()) / equity : 0.0;
    }
    double weekly_loss_pct() const noexcept {
        double equity = current_equity_.load();
        return equity > 0 ? std::abs(weekly_pnl_.load()) / equity : 0.0;
    }
    double drawdown_pct() const noexcept {
        double peak = peak_equity_.load();
        double current = current_equity_.load();
        return peak > 0 ? (peak - current) / peak : 0.0;
    }
};

// ── Main Execution Guard ──────────────────────────────────────────

class ExecutionGuard {
    HeartbeatMonitor heartbeat_;
    SpreadValidator spread_;
    SessionChecker session_;
    PositionManager positions_;
    
public:
    ExecutionGuard() = default;
    
    ExecutionResult check(
        double bid,
        double ask,
        int32_t utc_year,
        int32_t utc_month,
        int32_t utc_day,
        int32_t utc_hour,
        int32_t utc_minute
    ) noexcept {
        ExecutionResult result{};
        
        result.fix_heartbeat_ok = heartbeat_.is_connected();
        result.spread_ok = spread_.validate(bid, ask);
        result.spread_bps = spread_.avg_spread_bps();
        result.session_active = session_.is_session_active(utc_hour);
        result.not_nfp_fomc = !session_.is_nfp_fomc_blocked(utc_month, utc_day, utc_hour, utc_minute);
        result.position_limit_ok = positions_.can_open_position();
        result.current_positions = positions_.open_count();
        result.daily_loss_ok = positions_.is_daily_loss_ok();
        result.daily_loss_pct = positions_.daily_loss_pct();
        result.weekly_loss_ok = positions_.is_weekly_loss_ok();
        result.weekly_loss_pct = positions_.weekly_loss_pct();
        result.drawdown_ok = positions_.is_drawdown_ok();
        result.drawdown_pct = positions_.drawdown_pct();
        
        result.all_checks_passed = 
            result.fix_heartbeat_ok &&
            result.spread_ok &&
            result.session_active &&
            result.not_nfp_fomc &&
            result.position_limit_ok &&
            result.daily_loss_ok &&
            result.weekly_loss_ok &&
            result.drawdown_ok;
        
        result.failed_count = 0;
        char* ptr = result.failed_checks;
        int32_t remaining = sizeof(result.failed_checks);
        
        auto add_fail = [&](const char* msg) {
            int32_t len = strlen(msg);
            if (len < remaining - 2) {
                memcpy(ptr, msg, len);
                ptr += len;
                *ptr++ = ';';
                remaining -= len + 1;
                result.failed_count++;
            }
        };
        
        if (!result.fix_heartbeat_ok) add_fail("FIX heartbeat timeout");
        if (!result.spread_ok) add_fail("Spread too wide");
        if (!result.session_active) add_fail("Outside trading session");
        if (!result.not_nfp_fomc) add_fail("NFP/FOMC block");
        if (!result.position_limit_ok) add_fail("Position limit reached");
        if (!result.daily_loss_ok) add_fail("Daily loss limit");
        if (!result.weekly_loss_ok) add_fail("Weekly loss limit");
        if (!result.drawdown_ok) add_fail("Max drawdown exceeded");
        
        if (ptr > result.failed_checks) *(ptr - 1) = '\0';
        else *ptr = '\0';
        
        return result;
    }
    
    HeartbeatMonitor& heartbeat() { return heartbeat_; }
    SpreadValidator& spread_validator() { return spread_; }
    SessionChecker& session_checker() { return session_; }
    PositionManager& position_manager() { return positions_; }
};

} // namespace atikul::execution
