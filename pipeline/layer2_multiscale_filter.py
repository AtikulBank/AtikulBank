"""
LAYER 2: MULTI-SCALE FILTER
Ensemble Kalman (50) | Particle Filter (1000) | Unscented KF | Extended KF |
Adaptive KF | Wavelet Denoising | EMD (3 IMFs) | Savitzky-Golay

Multi-resolution signal filtering for noise removal and trend extraction.
Produces a denoised, filtered price signal for downstream analysis.
"""
from __future__ import annotations

import math
from typing import List, Tuple, Optional
from collections import deque

import numpy as np

from pipeline import FilteredSignals


# ── Kalman Filter Core ──────────────────────────────────────────────

class KalmanFilterCore:
    """Generic linear Kalman filter."""

    def __init__(self, dim_state: int = 2, dim_obs: int = 1):
        self.dim_state = dim_state
        self.dim_obs = dim_obs
        self.x = np.zeros(dim_state)              # state estimate
        self.P = np.eye(dim_state) * 10.0         # covariance
        self.Q = np.eye(dim_state) * 0.01         # process noise
        self.R = np.eye(dim_obs) * 0.1            # measurement noise
        self.F = np.eye(dim_state)                # transition
        self.H = np.zeros((dim_obs, dim_state))   # observation
        self.H[0, 0] = 1.0                        # observe position
        self.K = np.zeros((dim_state, dim_obs))   # gain

    def predict(self, dt: float = 1.0) -> np.ndarray:
        self.F[0, 1] = dt  # position += velocity * dt
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        return self.x.copy()

    def update(self, z: float) -> np.ndarray:
        z_arr = np.array([z])
        y = z_arr - self.H @ self.x
        S = self.H @ self.P @ self.H.T + self.R
        self.K = self.P @ self.H.T @ np.linalg.inv(S)
        self.x = self.x + self.K @ y
        I = np.eye(self.dim_state)
        self.P = (I - self.K @ self.H) @ self.P
        return self.x.copy()

    def filter(self, z: float, dt: float = 1.0) -> float:
        self.predict(dt)
        self.update(z)
        return float(self.x[0])


# ── Ensemble Kalman Filter (EnKF) ──────────────────────────────────

class EnsembleKalmanFilter:
    """
    Ensemble Kalman Filter with N_ensemble members.
    Better handles nonlinear dynamics than standard KF.
    """

    def __init__(self, n_ensemble: int = 50, dim_state: int = 2):
        self.N = n_ensemble
        self.dim = dim_state
        self.X = np.random.randn(n_ensemble, dim_state)  # ensemble matrix
        self.Q = np.eye(dim_state) * 0.01
        self.R = np.eye(1) * 0.1
        self.H = np.zeros((1, dim_state))
        self.H[0, 0] = 1.0

    def predict(self, dt: float = 1.0) -> None:
        """Ensemble prediction step with process noise."""
        for i in range(self.N):
            # Linear state transition: pos += vel * dt
            self.X[i, 0] += self.X[i, 1] * dt
            # Add process noise
            self.X[i] += np.random.multivariate_normal(np.zeros(self.dim), self.Q)

    def update(self, z: float) -> float:
        """Ensemble update step. Returns mean estimate."""
        z_vec = np.full(self.N, z)

        # Ensemble mean
        x_mean = np.mean(self.X, axis=0)
        z_mean = np.mean(self.H @ self.X.T, axis=1)

        # Perturb observations
        z_pert = z_vec + np.random.randn(self.N) * np.sqrt(self.R[0, 0])

        # Cross-covariance
        X_anom = self.X - x_mean
        Z_anom = (self.H @ self.X.T).T - z_mean

        P_xz = (X_anom.T @ Z_anom) / (self.N - 1)
        P_zz = (Z_anom.T @ Z_anom) / (self.N - 1) + self.R

        # Kalman gain
        K = P_xz @ np.linalg.inv(P_zz)

        # Update each ensemble member
        for i in range(self.N):
            y = z_pert[i] - (self.H @ self.X[i])
            self.X[i] += (K @ y).flatten()

        return float(np.mean(self.X[:, 0]))


# ── Particle Filter ─────────────────────────────────────────────────

class ParticleFilter:
    """
    Sequential Monte Carlo particle filter.
    Handles highly nonlinear/non-Gaussian dynamics.
    """

    def __init__(self, n_particles: int = 1000, dim: int = 2):
        self.N = n_particles
        self.dim = dim
        self.particles = np.random.randn(n_particles, dim) * 10
        self.weights = np.ones(n_particles) / n_particles
        self.obs_noise_std = 0.5

    def predict(self, dt: float = 1.0) -> None:
        """Propagate particles through dynamics + noise."""
        # Simple random walk + velocity
        self.particles[:, 0] += self.particles[:, 1] * dt
        self.particles[:, 1] += np.random.randn(self.N) * 0.1
        # Add process noise
        self.particles += np.random.randn(self.N, self.dim) * 0.5

    def update(self, z: float) -> float:
        """Update weights based on observation likelihood."""
        # Innovation
        innov = z - self.particles[:, 0]

        # Likelihood (Gaussian)
        log_lik = -0.5 * (innov / self.obs_noise_std) ** 2
        log_lik -= np.max(log_lik)  # numerical stability
        lik = np.exp(log_lik)

        # Update weights
        self.weights *= lik
        w_sum = np.sum(self.weights)
        if w_sum > 0:
            self.weights /= w_sum
        else:
            self.weights = np.ones(self.N) / self.N

        # Resample if effective sample size is low
        ess = 1.0 / np.sum(self.weights ** 2)
        if ess < self.N / 2:
            self._resample()

        return float(np.average(self.particles[:, 0], weights=self.weights))

    def _resample(self) -> None:
        """Systematic resampling."""
        indices = np.random.choice(self.N, self.N, p=self.weights)
        self.particles = self.particles[indices].copy()
        self.weights = np.ones(self.N) / self.N

    @property
    def effective_sample_size(self) -> float:
        return 1.0 / np.sum(self.weights ** 2)


# ── Unscented Kalman Filter (UKF) ──────────────────────────────────

class UnscentedKalmanFilter:
    """
    Unscented Kalman Filter using sigma points.
    Better than EKF for highly nonlinear systems.
    """

    def __init__(self, dim_state: int = 2, alpha: float = 0.1, beta: float = 2.0, kappa: float = 0.0):
        self.dim = dim_state
        self.n_sigma = 2 * dim_state + 1
        self.alpha = alpha
        self.beta = beta
        self.kappa = kappa
        self.x = np.zeros(dim_state)
        self.P = np.eye(dim_state) * 10.0
        self.Q = np.eye(dim_state) * 0.01
        self.R = np.eye(1) * 0.1

        # Compute weights
        lam = alpha ** 2 * (dim_state + kappa) - dim_state
        self.Wm = np.full(self.n_sigma, 0.5 / (dim_state + lam))
        self.Wm[0] = lam / (dim_state + lam)
        self.Wc = self.Wm.copy()
        self.Wc[0] += (1 - alpha ** 2 + beta)

    def _sigma_points(self) -> np.ndarray:
        """Generate sigma points from state and covariance."""
        lam = self.alpha ** 2 * (self.dim + self.kappa) - self.dim
        L = np.linalg.cholesky((self.dim + lam) * self.P)
        sigmas = np.zeros((self.n_sigma, self.dim))
        sigmas[0] = self.x
        for i in range(self.dim):
            sigmas[i + 1] = self.x + L[:, i]
            sigmas[self.dim + i + 1] = self.x - L[:, i]
        return sigmas

    def predict(self, dt: float = 1.0) -> None:
        sigmas = self._sigma_points()
        # Propagate: pos += vel * dt
        for s in sigmas:
            s[0] += s[1] * dt
        self.x = np.average(sigmas, axis=0, weights=self.Wm)
        P_pred = np.zeros_like(self.P)
        for i, s in enumerate(sigmas):
            diff = s - self.x
            P_pred += self.Wc[i] * np.outer(diff, diff)
        self.P = P_pred + self.Q

    def update(self, z: float) -> float:
        sigmas = self._sigma_points()
        z_sigmas = sigmas[:, 0]  # observe position
        z_pred = np.average(z_sigmas, weights=self.Wm)
        Pzz = 0.0
        Pxz = np.zeros((self.dim, 1))
        for i, s in enumerate(sigmas):
            diff_z = z_sigmas[i] - z_pred
            Pzz += self.Wc[i] * diff_z ** 2
            diff_x = s - self.x
            Pxz += self.Wc[i] * np.outer(diff_x, diff_z)
        Pzz += self.R[0, 0]
        K = (Pxz / Pzz).reshape(-1, 1)
        self.x += (K.flatten() * (z - z_pred))
        self.P -= K @ K.T * Pzz
        return float(self.x[0])


# ── Extended Kalman Filter (EKF) ───────────────────────────────────

class ExtendedKalmanFilter:
    """Extended Kalman Filter with linearized Jacobians."""

    def __init__(self, dim_state: int = 2):
        self.dim = dim_state
        self.x = np.zeros(dim_state)
        self.P = np.eye(dim_state) * 10.0
        self.Q = np.eye(dim_state) * 0.01
        self.R = np.eye(1) * 0.1

    def predict(self, dt: float = 1.0) -> None:
        # State transition: pos += vel * dt
        F = np.eye(self.dim)
        F[0, 1] = dt
        self.x = F @ self.x
        self.P = F @ self.P @ F.T + self.Q

    def update(self, z: float) -> float:
        # Observation: z = pos + noise
        H = np.zeros((1, self.dim))
        H[0, 0] = 1.0
        y = z - H @ self.x
        S = H @ self.P @ H.T + self.R
        K = self.P @ H.T / S[0, 0]
        self.x = self.x + K.flatten() * y[0]
        I = np.eye(self.dim)
        self.P = (I - K @ H) @ self.P
        return float(self.x[0])


# ── Adaptive Kalman Filter ──────────────────────────────────────────

class AdaptiveKalmanFilter:
    """
    Kalman filter with adaptive noise estimation.
    Uses innovation sequence to estimate R online.
    """

    def __init__(self, dim_state: int = 2, window: int = 50):
        self.kf = KalmanFilterCore(dim_state=dim_state)
        self.window = window
        self._innovations: deque = deque(maxlen=window)

    def filter(self, z: float, dt: float = 1.0) -> float:
        # Predict
        self.kf.predict(dt)

        # Innovation
        innovation = z - self.kf.H @ self.kf.x
        self._innovations.append(float(innovation[0]))

        # Adapt R from innovation statistics
        if len(self._innovations) >= 10:
            inn_arr = np.array(self._innovations)
            estimated_R = np.var(inn_arr)
            self.kf.R[0, 0] = max(estimated_R, 1e-6)

        # Update
        self.kf.update(z)
        return float(self.kf.x[0])

    @property
    def estimated_R(self) -> float:
        return float(self.kf.R[0, 0])


# ── Wavelet Denoising ──────────────────────────────────────────────

class WaveletDenoising:
    """
    Wavelet thresholding denoising.
    Uses Haar wavelet decomposition with soft thresholding.
    """

    def __init__(self, levels: int = 3, threshold_sigma: float = 1.5):
        self.levels = levels
        self.threshold_sigma = threshold_sigma

    def denoise(self, signal: np.ndarray) -> np.ndarray:
        """Denoise signal using wavelet thresholding."""
        if len(signal) < 4:
            return signal.copy()

        # Simple Haar-like decomposition
        s = signal.copy().astype(np.float64)
        coeffs = []

        for _ in range(self.levels):
            n = len(s)
            if n < 2:
                break
            # Pad if odd
            if n % 2 == 1:
                s = np.append(s, s[-1])
                n += 1
            approx = (s[0::2] + s[1::2]) / 2.0
            detail = (s[0::2] - s[1::2]) / 2.0
            coeffs.append(detail)
            s = approx

        # Threshold details
        for i in range(len(coeffs)):
            detail = coeffs[i]
            sigma = np.median(np.abs(detail)) / 0.6745
            threshold = self.threshold_sigma * sigma
            coeffs[i] = np.sign(detail) * np.maximum(np.abs(detail) - threshold, 0)

        # Reconstruct
        for i in range(len(coeffs) - 1, -1, -1):
            detail = coeffs[i]
            n = len(detail)
            s = np.zeros(2 * n)
            s[0::2] = s[:n] + detail
            s[1::2] = s[:n] - detail

        # Match original length
        return s[:len(signal)]

    def extract_features(self, signal: np.ndarray) -> dict:
        """Extract wavelet features from signal."""
        denoised = self.denoise(signal)
        residual = signal - denoised
        return {
            "wavelet_energy": float(np.sum(denoised ** 2)),
            "noise_energy": float(np.sum(residual ** 2)),
            "snr": float(np.sum(denoised ** 2) / max(1e-10, np.sum(residual ** 2))),
            "regularity": float(np.std(np.diff(denoised))),
        }


# ── Empirical Mode Decomposition (EMD) ─────────────────────────────

class EmpiricalModeDecomposition:
    """
    Simplified EMD that extracts Intrinsic Mode Functions (IMFs).
    Uses sifting process to decompose signal.
    """

    def __init__(self, max_imfs: int = 3, max_siftings: int = 10):
        self.max_imfs = max_imfs
        self.max_siftings = max_siftings

    def decompose(self, signal: np.ndarray) -> List[np.ndarray]:
        """Decompose signal into IMFs."""
        residual = signal.copy().astype(np.float64)
        imfs = []

        for _ in range(self.max_imfs):
            if len(residual) < 4:
                break

            imf = residual.copy()
            for _ in range(self.max_siftings):
                # Find extrema
                peaks = np.where((imf[1:-1] > imf[:-2]) & (imf[1:-1] > imf[2:]))[0] + 1
                troughs = np.where((imf[1:-1] < imf[:-2]) & (imf[1:-1] < imf[2:]))[0] + 1

                if len(peaks) < 2 or len(troughs) < 2:
                    break

                # Interpolate envelopes
                idx_peaks = np.concatenate(([0], peaks, [len(imf)-1]))
                vals_peaks = np.concatenate(([imf[0]], imf[peaks], [imf[-1]]))
                upper = np.interp(np.arange(len(imf)), idx_peaks, vals_peaks)

                idx_troughs = np.concatenate(([0], troughs, [len(imf)-1]))
                vals_troughs = np.concatenate(([imf[0]], imf[troughs], [imf[-1]]))
                lower = np.interp(np.arange(len(imf)), idx_troughs, vals_troughs)

                mean_env = (upper + lower) / 2.0
                imf = imf - mean_env

                # Check sifting criterion
                if np.std(np.diff(np.sign(np.diff(imf)))) < 1.0:
                    break

            imfs.append(imf)
            residual = residual - imf

        if len(residual) > 0 and np.any(residual != 0):
            imfs.append(residual)

        return imfs

    def extract_features(self, signal: np.ndarray) -> dict:
        """Extract EMD features."""
        imfs = self.decompose(signal)
        features = {}
        for i, imf in enumerate(imfs[:self.max_imfs]):
            features[f"imf{i+1}_energy"] = float(np.sum(imf ** 2))
            features[f"imf{i+1}_mean"] = float(np.mean(np.abs(imf)))
            features[f"imf{i+1}_std"] = float(np.std(imf))
        features["n_imfs"] = len(imfs)
        return features


# ── Savitzky-Golay Filter ──────────────────────────────────────────

class SavitzkyGolayFilter:
    """
    Savitzky-Golay smoothing filter.
    Fits local polynomials to preserve peaks and valleys.
    """

    def __init__(self, window: int = 11, polyorder: int = 3):
        self.window = window
        self.polyorder = polyorder

    def smooth(self, signal: np.ndarray) -> np.ndarray:
        """Apply Savitzky-Golay smoothing."""
        if len(signal) < self.window:
            return signal.copy()

        # Compute SG coefficients (simplified)
        half_w = self.window // 2
        x = np.arange(-half_w, half_w + 1, dtype=np.float64)
        A = np.column_stack([x ** k for k in range(self.polyorder + 1)])
        coeffs = np.linalg.lstsq(A, np.eye(self.window), rcond=None)[0]

        # Apply filter
        result = np.zeros_like(signal, dtype=np.float64)
        for i in range(half_w, len(signal) - half_w):
            window_data = signal[i - half_w:i + half_w + 1]
            result[i] = np.dot(coeffs[:, half_w], window_data)

        # Pad edges
        result[:half_w] = signal[:half_w]
        result[-half_w:] = signal[-half_w:]

        return result

    def extract_features(self, signal: np.ndarray) -> dict:
        """Extract SG features."""
        smoothed = self.smooth(signal)
        residual = signal - smoothed
        first_deriv = np.gradient(smoothed)
        second_deriv = np.gradient(first_deriv)
        return {
            "sg_smoothed_mean": float(np.mean(smoothed)),
            "sg_smoothed_std": float(np.std(smoothed)),
            "sg_noise_energy": float(np.sum(residual ** 2)),
            "sg_first_deriv_mean": float(np.mean(first_deriv)),
            "sg_second_deriv_mean": float(np.mean(second_deriv)),
        }


# ── Layer 2: Multi-Scale Filter ────────────────────────────────────

class MultiScaleFilter:
    """
    LAYER 2: Multi-Scale Filter
    Runs 8 parallel filters and produces ensemble output.
    """

    def __init__(
        self,
        ensembles_kf: int = 50,
        n_particles: int = 1000,
    ):
        # Kalman family
        self.ensemble_kf = EnsembleKalmanFilter(n_ensemble=ensembles_kf)
        self.particle_filter = ParticleFilter(n_particles=n_particles)
        self.ukf = UnscentedKalmanFilter()
        self.ekf = ExtendedKalmanFilter()
        self.adaptive_kf = AdaptiveKalmanFilter()

        # Smoothing family
        self.wavelet = WaveletDenoising(levels=3)
        self.emd = EmpiricalModeDecomposition(max_imfs=3)
        self.savgol = SavitzkyGolayFilter(window=11, polyorder=3)

        # Price history for batch filters
        self._price_history: deque = deque(maxlen=500)
        self._filtered_count = 0

    def filter_tick(self, price: float, dt: float = 1.0) -> FilteredSignals:
        """
        Run all 8 filters on a new tick.
        Returns FilteredSignals with all filter outputs.
        """
        self._price_history.append(price)
        self._filtered_count += 1

        result = FilteredSignals(raw_price=price)

        # 1. Ensemble Kalman
        self.ensemble_kf.predict(dt)
        result.kalman_ensemble = self.ensemble_kf.update(price)

        # 2. Particle Filter
        self.particle_filter.predict(dt)
        result.particle_mean = self.particle_filter.update(price)

        # 3. UKF
        self.ukf.predict(dt)
        result.ukf_estimate = self.ukf.update(price)

        # 4. EKF
        self.ekf.predict(dt)
        result.ekf_estimate = self.ekf.update(price)

        # 5. Adaptive KF
        result.adaptive_kf = self.adaptive_kf.filter(price, dt)

        # Batch filters (need history)
        if len(self._price_history) >= 20:
            hist = np.array(self._price_history)

            # 6. Wavelet denoising
            denoised = self.wavelet.denoise(hist)
            result.wavelet_denoised = float(denoised[-1])

            # 7. EMD
            imfs = self.emd.decompose(hist)
            result.emd_imfs = [float(imf[-1]) for imf in imfs[:3]]

            # 8. Savitzky-Golay
            smoothed = self.savgol.smooth(hist)
            result.savgol_smoothed = float(smoothed[-1])

        # Ensemble mean of all filters
        estimates = [
            result.kalman_ensemble,
            result.particle_mean,
            result.ukf_estimate,
            result.ekf_estimate,
            result.adaptive_kf,
        ]
        if result.wavelet_denoised != 0:
            estimates.append(result.wavelet_denoised)
        if result.savgol_smoothed != 0:
            estimates.append(result.savgol_smoothed)

        result.ensemble_mean = float(np.mean(estimates))

        return result

    @property
    def stats(self) -> dict:
        return {
            "filtered_count": self._filtered_count,
            "history_length": len(self._price_history),
            "particle_ess": self.particle_filter.effective_sample_size,
            "adaptive_R": self.adaptive_kf.estimated_R,
        }
