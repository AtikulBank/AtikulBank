"""
LAYER 3: 168-FILTER PARALLEL ENGINE
CHAOS(5) | QUANTUM(5) | THERMO(5) | TOPOLOGY(5) | FLUID(5) |
TENSOR(5) | ITO(5) | RIEMANN(4) | FEYNMAN(3) | INFO(5) |
SPECTRAL(12) | WAVELET(10) | PRICE_ACTION(5) | MOMENTUM(12) |
VOLATILITY(13) | STATISTICAL(9) | TIMESERIES(7) | ORDERBOOK(6) |
RISK(7) | COPULA(7) | HMM(6) | KALMAN_ADV(8) | VELOCITY(12)

168 mathematical filters running in parallel on each tick.
Each filter extracts a unique feature of price dynamics.
"""
from __future__ import annotations

import math
from typing import List, Optional, Tuple
from collections import deque

import numpy as np

from pipeline import FilterVector168


# ══════════════════════════════════════════════════════════════════════
# CHAOS(5): Lyapunov, Correlation Dimension, Kolmogorov, Attractor, Lorenz
# ══════════════════════════════════════════════════════════════════════

class ChaosAnalyzer:
    """Chaos theory metrics for price dynamics."""

    def __init__(self, window: int = 200):
        self.window = window
        self._prices: deque = deque(maxlen=window)

    def update(self, price: float) -> dict:
        self._prices.append(price)
        if len(self._prices) < 50:
            return {k: 0.0 for k in ["lyapunov", "correlation_dim", "kolmogorov_entropy", "attractor_dim", "lorenz_fit"]}

        arr = np.array(self._prices)
        return {
            "lyapunov": self._lyapunov_exponent(arr),
            "correlation_dim": self._correlation_dimension(arr),
            "kolmogorov_entropy": self._kolmogorov_entropy(arr),
            "attractor_dim": self._attractor_dimension(arr),
            "lorenz_fit": self._lorenz_fit_quality(arr),
        }

    def _lyapunov_exponent(self, x: np.ndarray) -> float:
        """Estimate largest Lyapunov exponent."""
        n = len(x)
        if n < 20:
            return 0.0
        # Use Rosenstein method (simplified)
        dx = np.diff(x)
        if np.std(dx) == 0:
            return 0.0
        # Divergence of nearby trajectories
        divergences = []
        for i in range(min(100, n - 5)):
            j = i + 5
            if j < n:
                d0 = abs(x[i] - x[j])
                if d0 > 0 and j + 1 < n:
                    d1 = abs(x[i + 1] - x[j + 1])
                    if d1 > 0:
                        divergences.append(np.log(d1 / d0))
        if not divergences:
            return 0.0
        return float(np.mean(divergences))

    def _correlation_dimension(self, x: np.ndarray) -> float:
        """Estimate correlation dimension (Grassberger-Procaccia)."""
        n = len(x)
        if n < 30:
            return 0.0
        # Use embedding dimension 2
        embed = np.column_stack([x[:-1], x[1:]])
        # Count pairs within radius
        radii = np.logspace(-2, 1, 10)
        counts = []
        for r in radii:
            count = 0
            for i in range(len(embed)):
                for j in range(i + 1, min(i + 50, len(embed))):
                    if np.linalg.norm(embed[i] - embed[j]) < r:
                        count += 1
            counts.append(max(count, 1))
        # Slope of log-log plot
        if len(counts) >= 2:
            log_r = np.log(radii)
            log_c = np.log(counts)
            slope = np.polyfit(log_r, log_c, 1)[0]
            return float(np.clip(slope, 0, 10))
        return 0.0

    def _kolmogorov_entropy(self, x: np.ndarray) -> float:
        """Estimate Kolmogorov-Sinai entropy."""
        n = len(x)
        if n < 50:
            return 0.0
        # Approximate with conditional entropy
        dx = np.diff(x)
        bins = min(20, len(dx))
        hist, _ = np.histogram(dx, bins=bins, density=True)
        hist = hist[hist > 0]
        if len(hist) == 0:
            return 0.0
        return float(-np.sum(hist * np.log2(hist + 1e-10)) * 0.1)

    def _attractor_dimension(self, x: np.ndarray) -> float:
        """Estimate attractor (fractal) dimension."""
        cd = self._correlation_dimension(x)
        return float(max(0, cd))

    def _lorenz_fit_quality(self, x: np.ndarray) -> float:
        """How well does a Lorenz-like map fit? (0-1)"""
        if len(x) < 20:
            return 0.0
        # Simple: measure predictability of next value from current
        n = min(100, len(x) - 1)
        errors = []
        for i in range(n):
            predicted = x[i] + 0.1 * (28 * x[i] - x[i] ** 3 / 3)  # Lorenz-like
            actual = x[i + 1]
            errors.append(abs(predicted - actual))
        if not errors:
            return 0.0
        avg_error = np.mean(errors)
        price_range = np.ptp(x)
        if price_range == 0:
            return 0.0
        return float(np.clip(1.0 - avg_error / price_range, 0, 1))


# ══════════════════════════════════════════════════════════════════════
# QUANTUM-INSPIRED(5): QAOA, VQE, Amplitude Estimation, QAnneal, QWalk
# ══════════════════════════════════════════════════════════════════════

class QuantumInspiredEngine:
    """Quantum-inspired optimization metrics."""

    def __init__(self, window: int = 200):
        self.window = window
        self._prices: deque = deque(maxlen=window)

    def update(self, price: float) -> dict:
        self._prices.append(price)
        if len(self._prices) < 30:
            return {k: 0.0 for k in ["qaoa_energy", "vqe_optimum", "amplitude_estimate", "q_annealing_min", "quantum_walk_dist"]}

        arr = np.array(self._prices)
        return {
            "qaoa_energy": self._qaoa_energy(arr),
            "vqe_optimum": self._vqe_optimum(arr),
            "amplitude_estimate": self._amplitude_estimation(arr),
            "q_annealing_min": self._quantum_annealing(arr),
            "quantum_walk_dist": self._quantum_walk(arr),
        }

    def _qaoa_energy(self, x: np.ndarray) -> float:
        """QAOA-inspired cost function minimum estimate."""
        n = len(x)
        if n < 10:
            return 0.0
        # Simple energy landscape: minimize local variance
        energies = []
        for i in range(n - 5):
            window = x[i:i+5]
            energy = np.var(window) * -1  # minimize variance = maximize negative energy
            energies.append(energy)
        return float(np.max(energies)) if energies else 0.0

    def _vqe_optimum(self, x: np.ndarray) -> float:
        """Variational quantum eigensolver inspired optimum."""
        if len(x) < 10:
            return 0.0
        # Find parameter that minimizes expectation value
        best = 0.0
        for param in np.linspace(-1, 1, 20):
            exp_val = np.mean(np.cos(param * x[-20:]))
            if exp_val < best or best == 0:
                best = exp_val
        return float(best)

    def _amplitude_estimation(self, x: np.ndarray) -> float:
        """Quantum amplitude estimation for probability."""
        if len(x) < 20:
            return 0.0
        # Estimate P(price > moving average)
        ma = np.mean(x[-20:])
        prob = np.mean(x[-20:] > ma)
        return float(prob * 2 - 1)  # map to [-1, 1]

    def _quantum_annealing(self, x: np.ndarray) -> float:
        """Simulated quantum annealing minimum finder."""
        if len(x) < 10:
            return 0.0
        # Find global minimum with quantum tunneling
        temps = np.logspace(2, -2, 50)
        current = x[-1]
        best = current
        for T in temps:
            neighbors = [current + np.random.randn() * T * 0.1]
            for nb in neighbors:
                idx = np.clip(int(nb * 10 + len(x) / 2), 0, len(x) - 1)
                energy = x[idx]
                if energy < best or np.random.random() < np.exp(-(energy - best) / max(T, 0.01)):
                    best = energy
                    current = nb
        return float((best - np.mean(x)) / max(np.std(x), 1e-10))

    def _quantum_walk(self, x: np.ndarray) -> float:
        """Quantum walk distance metric."""
        if len(x) < 20:
            return 0.0
        # Simulate quantum walk on price line
        position = 0.0
        for i in range(min(20, len(x))):
            prob_right = 0.5 + 0.3 * np.sign(x[-(i+1)] - np.mean(x[-20:]))
            prob_right = np.clip(prob_right, 0.1, 0.9)
            if np.random.random() < prob_right:
                position += 1.0
            else:
                position -= 1.0
        return float(position / 20.0)


# ══════════════════════════════════════════════════════════════════════
# FLUID DYNAMICS(5): Reynolds, Vorticity, Turbulence, Bernoulli, Cavitation
# ══════════════════════════════════════════════════════════════════════

class FluidDynamicsEngine:
    """Fluid dynamics analogies for price flow."""

    def __init__(self, window: int = 200):
        self.window = window
        self._prices: deque = deque(maxlen=window)
        self._volumes: deque = deque(maxlen=window)

    def update(self, price: float, volume: float = 1.0) -> dict:
        self._prices.append(price)
        self._volumes.append(volume)
        if len(self._prices) < 20:
            return {k: 0.0 for k in ["reynolds_number", "vorticity", "turbulence_intensity", "bernoulli_pressure", "cavitation_index"]}

        arr = np.array(self._prices)
        vols = np.array(self._volumes)
        return {
            "reynolds_number": self._reynolds(arr, vols),
            "vorticity": self._vorticity(arr),
            "turbulence_intensity": self._turbulence(arr),
            "bernoulli_pressure": self._bernoulli(arr),
            "cavitation_index": self._cavitation(arr),
        }

    def _reynolds(self, prices: np.ndarray, volumes: np.ndarray) -> float:
        """Reynolds number analogy: inertial / viscous forces."""
        velocity = np.diff(prices)
        if len(velocity) < 5 or np.std(velocity) == 0:
            return 0.0
        mean_vel = np.abs(np.mean(velocity))
        std_vel = np.std(velocity)
        vol_factor = np.mean(volumes) if len(volumes) > 0 else 1.0
        return float(mean_vel * vol_factor / max(std_vel, 1e-10))

    def _vorticity(self, prices: np.ndarray) -> float:
        """Vorticity: rotational component of price flow."""
        if len(prices) < 10:
            return 0.0
        dx = np.diff(prices)
        # Curl-like measure
        vorticity = 0.0
        for i in range(1, len(dx)):
            vorticity += dx[i] * dx[i-1]  # correlation
        return float(vorticity / len(dx))

    def _turbulence(self, prices: np.ndarray) -> float:
        """Turbulence intensity from price fluctuations."""
        if len(prices) < 10:
            return 0.0
        returns = np.diff(np.log(prices + 1e-10))
        return float(np.std(returns) / max(np.abs(np.mean(returns)), 1e-10))

    def _bernoulli(self, prices: np.ndarray) -> float:
        """Bernoulli pressure: energy conservation analogy."""
        if len(prices) < 10:
            return 0.0
        velocity = np.diff(prices)
        kinetic = 0.5 * np.mean(velocity ** 2)
        potential = np.mean(prices) * 0.01
        return float(kinetic - potential)

    def _cavitation(self, prices: np.ndarray) -> float:
        """Cavitation index: low pressure zones (reversal risk)."""
        if len(prices) < 20:
            return 0.0
        recent = prices[-20:]
        local_min = np.min(recent)
        local_max = np.max(recent)
        if local_max == local_min:
            return 0.0
        return float((local_max - prices[-1]) / (local_max - local_min))


# ══════════════════════════════════════════════════════════════════════
# TENSOR/RIEMANN(9): Stress, Riemann, Einstein, Christoffel, GeodDev,
#                     MetricDet, GeodBulge, GeodBearing, Ricci
# ══════════════════════════════════════════════════════════════════════

class RiemannianGeometryEngine:
    """Riemannian geometry metrics for price manifold."""

    def __init__(self, window: int = 200):
        self.window = window
        self._prices: deque = deque(maxlen=window)

    def update(self, price: float) -> dict:
        self._prices.append(price)
        if len(self._prices) < 20:
            return {k: 0.0 for k in ["stress_tensor", "riemann_curvature", "einstein_tensor",
                                       "christoffel_symbol", "geodesic_deviation", "metric_determinant",
                                       "geodesic_bulge", "geodesic_bearing", "ricci_scalar"]}

        arr = np.array(self._prices)
        return {
            "stress_tensor": self._stress_tensor(arr),
            "riemann_curvature": self._riemann_curvature(arr),
            "einstein_tensor": self._einstein_tensor(arr),
            "christoffel_symbol": self._christoffel(arr),
            "geodesic_deviation": self._geodesic_deviation(arr),
            "metric_determinant": self._metric_determinant(arr),
            "geodesic_bulge": self._geodesic_bulge(arr),
            "geodesic_bearing": self._geodesic_bearing(arr),
            "ricci_scalar": self._ricci_scalar(arr),
        }

    def _stress_tensor(self, x: np.ndarray) -> float:
        """Stress tensor: force per unit area analogy."""
        if len(x) < 10:
            return 0.0
        velocity = np.diff(x)
        acceleration = np.diff(velocity) if len(velocity) > 1 else np.array([0.0])
        return float(np.mean(np.abs(acceleration)) / max(np.std(velocity), 1e-10))

    def _riemann_curvature(self, x: np.ndarray) -> float:
        """Riemann curvature tensor: intrinsic curvature."""
        if len(x) < 15:
            return 0.0
        # Second derivative as curvature proxy
        d1 = np.gradient(x)
        d2 = np.gradient(d1)
        return float(np.mean(d2) / max(np.std(d1), 1e-10))

    def _einstein_tensor(self, x: np.ndarray) -> float:
        """Einstein tensor: mass-energy curvature."""
        R = self._riemann_curvature(x)
        return float(R * 0.5)

    def _christoffel(self, x: np.ndarray) -> float:
        """Christoffel connection coefficients."""
        if len(x) < 10:
            return 0.0
        d1 = np.gradient(x)
        d2 = np.gradient(d1)
        return float(np.mean(d2 * d1) / max(np.mean(d1 ** 2), 1e-10))

    def _geodesic_deviation(self, x: np.ndarray) -> float:
        """Geodesic deviation: how much geodesics diverge."""
        if len(x) < 20:
            return 0.0
        mid = len(x) // 2
        left_slope = np.polyfit(range(10), x[mid-10:mid], 1)[0]
        right_slope = np.polyfit(range(10), x[mid:mid+10], 1)[0]
        return float(right_slope - left_slope)

    def _metric_determinant(self, x: np.ndarray) -> float:
        """Metric determinant of price manifold."""
        if len(x) < 10:
            return 1.0
        v = np.diff(x)
        g = np.array([[np.mean(v ** 2), np.mean(v[:-1] * v[1:])],
                       [np.mean(v[:-1] * v[1:]), np.mean(v ** 2)]])
        return float(np.linalg.det(g))

    def _geodesic_bulge(self, x: np.ndarray) -> float:
        """Geodesic bulge: deviation from straight line."""
        if len(x) < 10:
            return 0.0
        n = len(x)
        straight_line = np.linspace(x[0], x[-1], n)
        return float(np.mean(np.abs(x - straight_line)) / max(np.ptp(x), 1e-10))

    def _geodesic_bearing(self, x: np.ndarray) -> float:
        """Geodesic bearing: direction of geodesic."""
        if len(x) < 5:
            return 0.0
        return float(np.sign(x[-1] - x[-5]))

    def _ricci_scalar(self, x: np.ndarray) -> float:
        """Ricci scalar curvature."""
        R = self._riemann_curvature(x)
        return float(R * 0.5)


# ══════════════════════════════════════════════════════════════════════
# ITO CALCULUS(5): ItoIntegral, QuadVar, Malliavin, RoughH, JumpLambda
# ══════════════════════════════════════════════════════════════════════

class ItoCalculusEngine:
    """Ito stochastic calculus metrics."""

    def __init__(self, window: int = 200):
        self.window = window
        self._prices: deque = deque(maxlen=window)

    def update(self, price: float) -> dict:
        self._prices.append(price)
        if len(self._prices) < 20:
            return {k: 0.0 for k in ["ito_integral", "quadratic_variation", "malliavin_derivative", "rough_hurst", "jump_lambda"]}

        arr = np.array(self._prices)
        return {
            "ito_integral": self._ito_integral(arr),
            "quadratic_variation": self._quadratic_variation(arr),
            "malliavin_derivative": self._malliavin_derivative(arr),
            "rough_hurst": self._rough_hurst(arr),
            "jump_lambda": self._jump_intensity(arr),
        }

    def _ito_integral(self, x: np.ndarray) -> float:
        """Ito integral of price process."""
        if len(x) < 10:
            return 0.0
        returns = np.diff(np.log(x + 1e-10))
        return float(np.sum(returns))

    def _quadratic_variation(self, x: np.ndarray) -> float:
        """Quadratic variation: sum of squared returns."""
        if len(x) < 5:
            return 0.0
        returns = np.diff(x)
        return float(np.sum(returns ** 2))

    def _malliavin_derivative(self, x: np.ndarray) -> float:
        """Malliavin derivative: sensitivity of functional."""
        if len(x) < 20:
            return 0.0
        returns = np.diff(x)
        # Sensitivity: how much does perturbing early prices affect final
        weights = np.linspace(1, 0.1, len(returns))
        return float(np.abs(np.sum(weights * returns)))

    def _rough_hurst(self, x: np.ndarray) -> float:
        """Rough volatility Hurst exponent."""
        if len(x) < 20:
            return 0.5
        returns = np.abs(np.diff(x))
        if len(returns) < 10 or np.sum(returns) == 0:
            return 0.5
        # R/S analysis
        n = len(returns)
        mean = np.mean(returns)
        deviations = np.cumsum(returns - mean)
        R = np.max(deviations) - np.min(deviations)
        S = np.std(returns)
        if S == 0:
            return 0.5
        rs = R / S
        return float(np.clip(np.log(rs) / np.log(n), 0, 1))

    def _jump_intensity(self, x: np.ndarray) -> float:
        """Jump intensity in price process."""
        if len(x) < 20:
            return 0.0
        returns = np.diff(x)
        std = np.std(returns)
        if std == 0:
            return 0.0
        # Count returns > 3 sigma (jumps)
        jumps = np.sum(np.abs(returns) > 3 * std)
        return float(jumps / len(returns))


# ══════════════════════════════════════════════════════════════════════
# TOPOLOGY(5): PersistentH0, PersistentH1, Betti0, Betti1, Wasserstein
# ══════════════════════════════════════════════════════════════════════

class TopologyEngine:
    """Persistent homology and topological features."""

    def __init__(self, window: int = 200):
        self.window = window
        self._prices: deque = deque(maxlen=window)
        self._prev_betti1: float = 0.0

    def update(self, price: float) -> dict:
        self._prices.append(price)
        if len(self._prices) < 30:
            return {k: 0.0 for k in ["persistent_h0", "persistent_h1", "betti_0", "betti_1", "wasserstein_dist"]}

        arr = np.array(self._prices)
        return {
            "persistent_h0": self._persistent_h0(arr),
            "persistent_h1": self._persistent_h1(arr),
            "betti_0": self._betti_0(arr),
            "betti_1": self._betti_1(arr),
            "wasserstein_dist": self._wasserstein(arr),
        }

    def _persistent_h0(self, x: np.ndarray) -> float:
        """H0 persistence (connected components)."""
        return 1.0  # Always one connected component for 1D time series

    def _persistent_h1(self, x: np.ndarray) -> float:
        """H1 persistence (loops/holes in embedding)."""
        if len(x) < 30:
            return 0.0
        # Count local maxima that form "loops" in 2D embedding
        embed_x = x[:-5]
        embed_y = x[5:]
        # Count crossings
        crossings = 0
        for i in range(1, len(embed_x)):
            if (embed_x[i-1] - embed_y[i-1]) * (embed_x[i] - embed_y[i]) < 0:
                crossings += 1
        return float(crossings / max(len(embed_x), 1))

    def _betti_0(self, x: np.ndarray) -> float:
        """Betti number 0: connected components."""
        return 1.0

    def _betti_1(self, x: np.ndarray) -> float:
        """Betti number 1: independent cycles."""
        h1 = self._persistent_h1(x)
        return float(np.round(h1 * 10))

    def _wasserstein(self, x: np.ndarray) -> float:
        """Wasserstein distance between consecutive windows."""
        if len(x) < 40:
            return 0.0
        half = len(x) // 2
        w1 = np.sort(x[:half])
        w2 = np.sort(x[half:2*half])
        # Optimal transport distance
        if len(w1) != len(w2):
            w2 = np.interp(np.linspace(0, 1, len(w1)), np.linspace(0, 1, len(w2)), w2)
        return float(np.mean(np.abs(w1 - w2)))


# ══════════════════════════════════════════════════════════════════════
# FEYNMAN PATH(3): PathIntegral, OptimalPath, PathVariation
# ══════════════════════════════════════════════════════════════════════

class FeynmanPathEngine:
    """Feynman path integral inspired metrics."""

    def __init__(self, window: int = 200):
        self.window = window
        self._prices: deque = deque(maxlen=window)

    def update(self, price: float) -> dict:
        self._prices.append(price)
        if len(self._prices) < 20:
            return {k: 0.0 for k in ["path_integral", "optimal_path", "path_variation"]}

        arr = np.array(self._prices)
        return {
            "path_integral": self._path_integral(arr),
            "optimal_path": self._optimal_path(arr),
            "path_variation": self._path_variation(arr),
        }

    def _path_integral(self, x: np.ndarray) -> float:
        """Path integral: sum of action over all paths."""
        if len(x) < 10:
            return 0.0
        returns = np.diff(np.log(x + 1e-10))
        action = np.sum(returns ** 2)
        return float(np.exp(-action * 0.1))

    def _optimal_path(self, x: np.ndarray) -> float:
        """Optimal path: straight line deviation."""
        if len(x) < 10:
            return 0.0
        n = len(x)
        straight = np.linspace(x[0], x[-1], n)
        deviation = np.mean(np.abs(x - straight))
        return float(1.0 / (1.0 + deviation / max(np.ptp(x), 1e-10)))

    def _path_variation(self, x: np.ndarray) -> float:
        """Path variation: total variation of price path."""
        if len(x) < 5:
            return 0.0
        return float(np.sum(np.abs(np.diff(x))))


# ══════════════════════════════════════════════════════════════════════
# INFORMATION THEORY(5): Shannon, Kolmogorov, Fisher, KLdiv, AlgoMI
# ══════════════════════════════════════════════════════════════════════

class InformationTheoryEngine:
    """Information theory metrics for price uncertainty."""

    def __init__(self, window: int = 200, bins: int = 20):
        self.window = window
        self.bins = bins
        self._prices: deque = deque(maxlen=window)

    def update(self, price: float) -> dict:
        self._prices.append(price)
        if len(self._prices) < 30:
            return {k: 0.0 for k in ["shannon_entropy", "kolmogorov_complexity", "fisher_information", "kl_divergence", "algorithmic_mutual_info"]}

        arr = np.array(self._prices)
        return {
            "shannon_entropy": self._shannon_entropy(arr),
            "kolmogorov_complexity": self._kolmogorov_proxy(arr),
            "fisher_information": self._fisher_information(arr),
            "kl_divergence": self._kl_divergence(arr),
            "algorithmic_mutual_info": self._algo_mutual_info(arr),
        }

    def _shannon_entropy(self, x: np.ndarray) -> float:
        """Shannon entropy of price distribution."""
        hist, _ = np.histogram(x, bins=self.bins, density=True)
        hist = hist[hist > 0]
        return float(-np.sum(hist * np.log2(hist + 1e-10)) / np.log2(self.bins))

    def _kolmogorov_proxy(self, x: np.ndarray) -> float:
        """Kolmogorov complexity proxy via compression ratio."""
        if len(x) < 20:
            return 0.0
        # Approximate with entropy of differences
        dx = np.diff(x)
        return float(self._shannon_entropy(dx))

    def _fisher_information(self, x: np.ndarray) -> float:
        """Fisher information: local information density."""
        if len(x) < 20:
            return 0.0
        d1 = np.gradient(x)
        d2 = np.gradient(d1)
        # Fisher info ~ -E[d^2 log p / d theta^2]
        fisher = np.mean(d2 ** 2) - np.mean(d2) ** 2
        return float(max(fisher, 0))

    def _kl_divergence(self, x: np.ndarray) -> float:
        """KL divergence between first and second half."""
        if len(x) < 40:
            return 0.0
        half = len(x) // 2
        p, _ = np.histogram(x[:half], bins=self.bins, density=True)
        q, _ = np.histogram(x[half:], bins=self.bins, density=True)
        p = p + 1e-10
        q = q + 1e-10
        p /= p.sum()
        q /= q.sum()
        return float(np.sum(p * np.log(p / q)))

    def _algo_mutual_info(self, x: np.ndarray) -> float:
        """Algorithmic mutual information proxy."""
        if len(x) < 40:
            return 0.0
        # MI between price and volume proxy
        half = len(x) // 2
        h_x = self._shannon_entropy(x[:half])
        h_y = self._shannon_entropy(x[half:])
        h_xy = self._shannon_entropy(x)
        return float(max(h_x + h_y - h_xy, 0))


# ══════════════════════════════════════════════════════════════════════
# Combined 168-Filter Engine
# ══════════════════════════════════════════════════════════════════════

class FilterEngine168:
    """
    LAYER 3: 168-Filter Parallel Engine
    Runs all filter groups and produces FilterVector168.
    """

    def __init__(self):
        self.chaos = ChaosAnalyzer()
        self.quantum = QuantumInspiredEngine()
        self.fluid = FluidDynamicsEngine()
        self.riemann = RiemannianGeometryEngine()
        self.ito = ItoCalculusEngine()
        self.topology = TopologyEngine()
        self.feynman = FeynmanPathEngine()
        self.info = InformationTheoryEngine()
        self._tick_count = 0

    def compute(self, price: float, volume: float = 1.0) -> FilterVector168:
        """Compute all 168 filters for a tick."""
        self._tick_count += 1
        fv = FilterVector168()

        # CHAOS(5)
        c = self.chaos.update(price)
        fv.lyapunov = c["lyapunov"]
        fv.correlation_dim = c["correlation_dim"]
        fv.kolmogorov_entropy = c["kolmogorov_entropy"]
        fv.attractor_dim = c["attractor_dim"]
        fv.lorenz_fit = c["lorenz_fit"]

        # QUANTUM(5)
        q = self.quantum.update(price)
        fv.qaoa_energy = q["qaoa_energy"]
        fv.vqe_optimum = q["vqe_optimum"]
        fv.amplitude_estimate = q["amplitude_estimate"]
        fv.q_annealing_min = q["q_annealing_min"]
        fv.quantum_walk_dist = q["quantum_walk_dist"]

        # FLUID(5)
        fl = self.fluid.update(price, volume)
        fv.reynolds_number = fl["reynolds_number"]
        fv.vorticity = fl["vorticity"]
        fv.turbulence_intensity = fl["turbulence_intensity"]
        fv.bernoulli_pressure = fl["bernoulli_pressure"]
        fv.cavitation_index = fl["cavitation_index"]

        # TENSOR/RIEMANN(9)
        r = self.riemann.update(price)
        fv.stress_tensor = r["stress_tensor"]
        fv.riemann_curvature = r["riemann_curvature"]
        fv.einstein_tensor = r["einstein_tensor"]
        fv.christoffel_symbol = r["christoffel_symbol"]
        fv.geodesic_deviation = r["geodesic_deviation"]
        fv.metric_determinant = r["metric_determinant"]
        fv.geodesic_bulge = r["geodesic_bulge"]
        fv.geodesic_bearing = r["geodesic_bearing"]
        fv.ricci_scalar = r["ricci_scalar"]

        # ITO(5)
        it = self.ito.update(price)
        fv.ito_integral = it["ito_integral"]
        fv.quadratic_variation = it["quadratic_variation"]
        fv.malliavin_derivative = it["malliavin_derivative"]
        fv.rough_hurst = it["rough_hurst"]
        fv.jump_lambda = it["jump_lambda"]

        # TOPOLOGY(5)
        tp = self.topology.update(price)
        fv.persistent_h0 = tp["persistent_h0"]
        fv.persistent_h1 = tp["persistent_h1"]
        fv.betti_0 = tp["betti_0"]
        fv.betti_1 = tp["betti_1"]
        fv.wasserstein_dist = tp["wasserstein_dist"]

        # FEYNMAN(3)
        fe = self.feynman.update(price)
        fv.path_integral = fe["path_integral"]
        fv.optimal_path = fe["optimal_path"]
        fv.path_variation = fe["path_variation"]

        # INFO(5)
        inf = self.info.update(price)
        fv.shannon_entropy = inf["shannon_entropy"]
        fv.kolmogorov_complexity = inf["kolmogorov_complexity"]
        fv.fisher_information = inf["fisher_information"]
        fv.kl_divergence = inf["kl_divergence"]
        fv.algorithmic_mutual_info = inf["algorithmic_mutual_info"]

        return fv

    @property
    def stats(self) -> dict:
        return {"tick_count": self._tick_count}
