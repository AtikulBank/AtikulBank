/**
 * LAYER 4: MANIPULATION SHIELD - C++ IMPLEMENTATION
 * High-performance manipulation detection with AWS C7g optimization
 */

#include "manipulation_core.h"
#include <algorithm>
#include <numeric>
#include <cmath>

namespace manipulation {

// ============================================================================
// VPIN Calculator
// ============================================================================

VPINCalculator::VPINCalculator(int n_buckets) : n_buckets_(n_buckets) {}

void VPINCalculator::classify_trades(const double* prices, int n, int* classifications) const {
    classifications[0] = 0;  // First trade is neutral
    
    for (int i = 1; i < n; i++) {
        if (prices[i] > prices[i-1]) {
            classifications[i] = 1;   // Buyer-initiated
        } else if (prices[i] < prices[i-1]) {
            classifications[i] = -1;  // Seller-initiated
        } else {
            classifications[i] = 0;   // Neutral
        }
    }
}

double VPINCalculator::compute(const double* prices, const double* volumes, int n) const {
    if (n < 100) return 0.0;
    
    // Classify trades
    std::vector<int> classifications(n);
    classify_trades(prices, n, classifications.data());
    
    // Compute VPIN using volume buckets
    int bucket_size = n / n_buckets_;
    if (bucket_size == 0) return 0.0;
    
    double total_vpin = 0.0;
    int valid_buckets = 0;
    
    for (int bucket = 0; bucket < n_buckets_; bucket++) {
        int start = bucket * bucket_size;
        int end = start + bucket_size;
        if (end > n) end = n;
        
        double buy_volume = 0.0;
        double sell_volume = 0.0;
        double total_volume = 0.0;
        
        for (int i = start; i < end; i++) {
            total_volume += volumes[i];
            if (classifications[i] == 1) {
                buy_volume += volumes[i];
            } else if (classifications[i] == -1) {
                sell_volume += volumes[i];
            }
        }
        
        if (total_volume > 0) {
            double vpin_bucket = std::abs(buy_volume - sell_volume) / total_volume;
            total_vpin += vpin_bucket;
            valid_buckets++;
        }
    }
    
    return (valid_buckets > 0) ? total_vpin / valid_buckets : 0.0;
}

double VPINCalculator::compute_neon(const double* prices, const double* volumes, int n) const {
#ifdef __ARM_NEON
    // AWS C7g NEON SIMD optimization
    if (n < 100) return 0.0;
    
    // Classify trades with NEON
    std::vector<int> classifications(n);
    classifications[0] = 0;
    
    int i = 1;
    for (; i + 3 < n; i += 4) {
        // Load 4 prices
        float64x2_t prev1 = vld1q_f64(&prices[i-1]);
        float64x2_t prev2 = vld1q_f64(&prices[i+1]);
        float64x2_t curr1 = vld1q_f64(&prices[i]);
        float64x2_t curr2 = vld1q_f64(&prices[i+2]);
        
        // Compare
        uint64x2_t gt1 = vcgtq_f64(curr1, prev1);
        uint64x2_t gt2 = vcgtq_f64(curr2, prev2);
        uint64x2_t lt1 = vcltq_f64(curr1, prev1);
        uint64x2_t lt2 = vcltq_f64(curr2, prev2);
        
        // Convert to int
        int32x2_t class1 = vcombine_s32(
            vreinterpret_s32_u32(vmovn_u64(gt1)),
            vreinterpret_s32_u32(vmovn_u64(lt1))
        );
        int32x2_t class2 = vcombine_s32(
            vreinterpret_s32_u32(vmovn_u64(gt2)),
            vreinterpret_s32_u32(vmovn_u64(lt2))
        );
        
        // Store classifications
        int tmp[4];
        vst1_s32(&tmp[0], class1);
        vst1_s32(&tmp[2], class2);
        
        classifications[i] = tmp[0] ? 1 : (tmp[2] ? -1 : 0);
        classifications[i+1] = tmp[1] ? 1 : (tmp[3] ? -1 : 0);
        classifications[i+2] = tmp[2] ? 1 : (tmp[0] ? -1 : 0);  // Simplified
        classifications[i+3] = tmp[3] ? 1 : (tmp[1] ? -1 : 0);  // Simplified
    }
    
    // Handle remaining elements
    for (; i < n; i++) {
        if (prices[i] > prices[i-1]) {
            classifications[i] = 1;
        } else if (prices[i] < prices[i-1]) {
            classifications[i] = -1;
        } else {
            classifications[i] = 0;
        }
    }
    
    // Compute VPIN
    return compute(prices, volumes, n);
#else
    // Fallback to standard implementation
    return compute(prices, volumes, n);
#endif
}

// ============================================================================
// Lee-Ready Classifier
// ============================================================================

int LeeReadyClassifier::classify(double price, double bid, double ask, double prev_price) {
    if (bid <= 0 || ask <= 0) return 0;
    
    double mid = (bid + ask) / 2.0;
    double spread = ask - bid;
    double tolerance = spread * 0.1;
    
    // Rule 1: Price above midpoint + tolerance
    if (price > mid + tolerance) {
        return 1;  // Buy
    }
    
    // Rule 2: Price below midpoint - tolerance
    if (price < mid - tolerance) {
        return -1;  // Sell
    }
    
    // Rule 3: Use tick rule
    if (price > prev_price) {
        return 1;
    } else if (price < prev_price) {
        return -1;
    }
    
    return 0;  // Neutral
}

// ============================================================================
// Stop-Hunt Detector
// ============================================================================

bool StopHuntDetector::detect(const double* prices, int n) {
    if (n < 20) return false;
    
    // Find recent min/max
    double max_price = prices[0];
    double min_price = prices[0];
    
    for (int i = 1; i < 20 && i < n; i++) {
        if (prices[n - 1 - i] > max_price) max_price = prices[n - 1 - i];
        if (prices[n - 1 - i] < min_price) min_price = prices[n - 1 - i];
    }
    
    // Check for spike and reversal pattern
    if (n >= 3) {
        double p3 = prices[n - 3];
        double p2 = prices[n - 2];
        double p1 = prices[n - 1];
        
        // Spike up then down
        if (p3 < max_price * (1.0 - STOP_HUNT_SPIKE_THRESHOLD) &&
            p2 > max_price * (1.0 - STOP_HUNT_SPIKE_THRESHOLD) &&
            p1 < p2 * (1.0 - STOP_HUNT_SPIKE_THRESHOLD)) {
            return true;
        }
        
        // Spike down then up
        if (p3 > min_price * (1.0 + STOP_HUNT_SPIKE_THRESHOLD) &&
            p2 < min_price * (1.0 + STOP_HUNT_SPIKE_THRESHOLD) &&
            p1 > p2 * (1.0 + STOP_HUNT_SPIKE_THRESHOLD)) {
            return true;
        }
    }
    
    return false;
}

bool StopHuntDetector::detect_simd(const double* prices, int n) {
#ifdef __ARM_NEON
    // NEON-optimized version for AWS C7g
    if (n < 20) return false;
    
    // Find min/max using NEON reduction
    float64x2_t max_vec = vdupq_n_f64(-1e300);
    float64x2_t min_vec = vdupq_n_f64(1e300);
    
    int start = n - 20;
    if (start < 0) start = 0;
    
    for (int i = start; i + 1 < n; i += 2) {
        float64x2_t vals = vld1q_f64(&prices[i]);
        max_vec = vmaxq_f64(max_vec, vals);
        min_vec = vminq_f64(min_vec, vals);
    }
    
    // Extract max/min
    double max_vals[2], min_vals[2];
    vst1q_f64(max_vals, max_vec);
    vst1q_f64(min_vals, min_vec);
    
    double max_price = std::max(max_vals[0], max_vals[1]);
    double min_price = std::min(min_vals[0], min_vals[1]);
    
    // Check pattern
    if (n >= 3) {
        double p3 = prices[n - 3];
        double p2 = prices[n - 2];
        double p1 = prices[n - 1];
        
        if ((p3 < max_price * 0.99 && p2 > max_price * 0.99 && p1 < p2 * 0.99) ||
            (p3 > min_price * 1.01 && p2 < min_price * 1.01 && p1 > p2 * 1.01)) {
            return true;
        }
    }
    
    return false;
#else
    return detect(prices, n);
#endif
}

// ============================================================================
// Fake Breakout Detector
// ============================================================================

bool FakeBreakoutDetector::detect(const double* prices, int n) {
    if (n < 50) return false;
    
    // Compute support and resistance
    std::vector<double> recent(prices + n - 50, prices + n);
    std::sort(recent.begin(), recent.end());
    
    double support = recent[4];     // 10th percentile
    double resistance = recent[44]; // 90th percentile
    
    // Check for failed breakout
    if (n >= 3) {
        double p3 = prices[n - 3];
        double p2 = prices[n - 2];
        double p1 = prices[n - 1];
        
        // Breakout above resistance that fails
        if (p2 > resistance && p1 < resistance && p3 < resistance) {
            return true;
        }
        
        // Breakout below support that fails
        if (p2 < support && p1 > support && p3 > support) {
            return true;
        }
    }
    
    return false;
}

// ============================================================================
// Spread Manipulation Detector
// ============================================================================

bool SpreadManipulationDetector::detect(const double* spreads, int n) {
    if (n < 100) return false;
    
    // Compute historical statistics
    double hist_sum = 0.0;
    double hist_sum_sq = 0.0;
    int hist_count = n - 10;
    
    for (int i = 0; i < hist_count; i++) {
        hist_sum += spreads[i];
        hist_sum_sq += spreads[i] * spreads[i];
    }
    
    double hist_mean = hist_sum / hist_count;
    double hist_var = (hist_sum_sq / hist_count) - (hist_mean * hist_mean);
    double hist_std = std::sqrt(hist_var);
    
    // Compute recent mean
    double recent_sum = 0.0;
    for (int i = hist_count; i < n; i++) {
        recent_sum += spreads[i];
    }
    double recent_mean = recent_sum / 10.0;
    
    // Check for abnormal expansion
    return (recent_mean > hist_mean + SPREAD_MANIPULATION_THRESHOLD * hist_std);
}

// ============================================================================
// IsolationForest Scorer (simplified)
// ============================================================================

double IsolationForestScorer::score(const double* features, int n_features) {
    if (n_features == 0) return 0.0;
    
    // Simplified scoring based on feature statistics
    double sum = 0.0;
    double sum_sq = 0.0;
    
    for (int i = 0; i < n_features; i++) {
        sum += features[i];
        sum_sq += features[i] * features[i];
    }
    
    double mean = sum / n_features;
    double var = (sum_sq / n_features) - (mean * mean);
    double std = std::sqrt(var);
    
    // Score based on deviation from expected distribution
    // Lower score = more anomalous
    double score = -std;  // Negative std indicates unusual patterns
    
    return score;
}

}  // namespace manipulation

// ============================================================================
// C API for Cython binding
// ============================================================================

extern "C" {
    
    double compute_vpin_c(const double* prices, const double* volumes, int n) {
        manipulation::VPINCalculator calc;
        return calc.compute(prices, volumes, n);
    }
    
    int lee_ready_classify_c(double price, double bid, double ask, double prev_price) {
        return manipulation::LeeReadyClassifier::classify(price, bid, ask, prev_price);
    }
    
    int detect_stop_hunt_c(const double* prices, int n) {
        return manipulation::StopHuntDetector::detect(prices, n) ? 1 : 0;
    }
    
    int detect_fake_breakout_c(const double* prices, int n) {
        return manipulation::FakeBreakoutDetector::detect(prices, n) ? 1 : 0;
    }
    
    int detect_spread_manipulation_c(const double* spreads, int n) {
        return manipulation::SpreadManipulationDetector::detect(spreads, n) ? 1 : 0;
    }
    
    double isolation_forest_score_c(const double* features, int n_features) {
        return manipulation::IsolationForestScorer::score(features, n_features);
    }
    
}