#pragma once
/**
 * C++ Ultra-Low-Latency Monitor
 * Nanosecond-precision tick timing with CPU cycle counting.
 * Compiled with: -O3 -march=native -mtune=native
 */

#include <cstdint>
#include <chrono>
#include <atomic>
#include <array>
#include <cstring>

#ifdef __linux__
#include <x86intrin.h>
#include <sched.h>
#include <sys/mman.h>
#endif

namespace atikul {

// ── Nanosecond Timer (uses RDTSC on x86) ─────────────────────────

class NanosecondTimer {
public:
    static inline uint64_t now_ns() noexcept {
        #ifdef __linux__
        return __rdtsc();  // CPU cycle counter
        #else
        return static_cast<uint64_t>(
            std::chrono::high_resolution_clock::now().time_since_epoch().count()
        );
        #endif
    }

    static inline uint64_t elapsed_ns(uint64_t start) noexcept {
        return now_ns() - start;
    }
};

// ── Per-Layer Latency Tracker ─────────────────────────────────────

class LatencyTracker {
    static constexpr size_t MAX_LAYERS = 16;
    static constexpr size_t WINDOW = 1024;

    struct LayerData {
        std::array<uint64_t, WINDOW> samples{};
        std::atomic<size_t> index{0};
        std::atomic<uint64_t> total{0};
        std::atomic<uint64_t> count{0};
    };

    std::array<LayerData, MAX_LAYERS> layers_;
    std::array<uint64_t, MAX_LAYERS> start_times_{};

public:
    void start(size_t layer_id) noexcept {
        if (layer_id < MAX_LAYERS) {
            start_times_[layer_id] = NanosecondTimer::now_ns();
        }
    }

    void stop(size_t layer_id) noexcept {
        if (layer_id < MAX_LAYERS) {
            uint64_t elapsed = NanosecondTimer::elapsed_ns(start_times_[layer_id]);
            auto& data = layers_[layer_id];
            size_t idx = data.index.fetch_add(1) % WINDOW;
            data.samples[idx] = elapsed;
            data.total.fetch_add(elapsed);
            data.count.fetch_add(1);
        }
    }

    double mean_ns(size_t layer_id) const noexcept {
        if (layer_id >= MAX_LAYERS) return 0.0;
        auto& data = layers_[layer_id];
        uint64_t c = data.count.load();
        return c > 0 ? static_cast<double>(data.total.load()) / c : 0.0;
    }

    double mean_ms(size_t layer_id) const noexcept {
        return mean_ns(layer_id) / 1'000'000.0;
    }
};

// ── CPU Affinity (Linux) ──────────────────────────────────────────

inline bool pin_to_core(int core_id) noexcept {
    #ifdef __linux__
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(core_id, &cpuset);
    return sched_setaffinity(0, sizeof(cpu_set_t), &cpuset) == 0;
    #else
    return false;
    #endif
}

// ── Memory Prefetch Helper ────────────────────────────────────────

inline void prefetch(const void* addr) noexcept {
    #ifdef __GNUC__
    __builtin_prefetch(addr, 0, 3);
    #endif
}

// ── Cache Line Size (for false sharing avoidance) ─────────────────

constexpr size_t CACHE_LINE_SIZE = 64;

template<typename T>
struct alignas(CACHE_LINE_SIZE) PaddedValue {
    T value;
    char padding[CACHE_LINE_SIZE - sizeof(T) % CACHE_LINE_SIZE];
};

} // namespace atikul
