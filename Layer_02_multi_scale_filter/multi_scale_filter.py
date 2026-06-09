"""
LAYER 2: MULTI-SCALE FILTER
Implements multiple filtering algorithms for noise removal
"""

import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from scipy import signal as scipy_signal
from scipy.ndimage import uniform_filter1d
import pywt


@dataclass
class FilterState:
    """State of a filter"""
    estimate: float = 0.0
    velocity: float = 0.0
    acceleration: float = 0.0
    jerk: float = 0.0
    uncertainty: float = 1.0
    innovation: float = 0.0
    gain: float = 0.0


class KalmanFilter:
    """Standard Kalman Filter"""
    
    def __init__(self, dt: float = 1.0, process_noise: float = 0.01, measurement_noise: float = 0.1):
        self.dt = dt
        self.Q = np.array([[dt**4/4, dt**3/2], [dt**3/2, dt**2]]) * process_noise
        self.R = np.array([[measurement_noise]])
        self.x = np.zeros(2)  # [position, velocity]
        self.P = np.eye(2) * 1.0
        self.H = np.array([[1.0, 0.0]])
        
    def predict(self) -> np.ndarray:
        F = np.array([[1, self.dt], [0, 1]])
        self.x = F @ self.x
        self.P = F @ self.P @ F.T + self.Q
        return self.x.copy()
    
    def update(self, z: float) -> np.ndarray:
        y = z - self.H @ self.x
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T / S[0, 0]
        self.x = self.x + K.flatten() * y
        self.P = (np.eye(2) - K @ self.H) @ self.P
        return self.x.copy()
    
    def get_state(self) -> FilterState:
        return FilterState(
            estimate=float(self.x[0]),
            velocity=float(self.x[1]),
            uncertainty=float(np.sqrt(self.P[0, 0])),
            gain=float(self.P[0, 0] / (self.P[0, 0] + self.R[0, 0]))
        )


class EnsembleKalmanFilter:
    """Ensemble Kalman Filter with N particles"""
    
    def __init__(self, n_ensemble: int = 50, dt: float = 1.0):
        self.n_ensemble = n_ensemble
        self.dt = dt
        self.ensemble = np.random.randn(n_ensemble, 2) * 0.1
        self.measurement_noise = 0.1
        
    def predict(self) -> np.ndarray:
        F = np.array([[1, self.dt], [0, 1]])
        for i in range(self.n_ensemble):
            self.ensemble[i] = F @ self.ensemble[i] + np.random.randn(2) * 0.01
        return np.mean(self.ensemble, axis=0)
    
    def update(self, z: float) -> np.ndarray:
        H = np.array([1.0, 0.0])
        
        # Calculate ensemble mean and perturbations
        mean = np.mean(self.ensemble, axis=0)
        perturbations = self.ensemble - mean
        
        # Innovation
        innovations = z - self.ensemble @ H
        
        # Innovation covariance
        S = np.var(innovations) + self.measurement_noise
        
        # Kalman gain
        K = np.cov(self.ensemble.T) @ H / S
        
        # Update ensemble
        for i in range(self.n_ensemble):
            self.ensemble[i] += K * (innovations[i] + np.random.randn() * self.measurement_noise)
        
        return np.mean(self.ensemble, axis=0)


class ParticleFilter:
    """Particle Filter with N particles"""
    
    def __init__(self, n_particles: int = 1000, dt: float = 1.0):
        self.n_particles = n_particles
        self.dt = dt
        self.particles = np.random.randn(n_particles, 2) * 0.1
        self.weights = np.ones(n_particles) / n_particles
        self.measurement_noise = 0.1
        
    def predict(self) -> np.ndarray:
        # Add process noise
        noise = np.random.randn(self.n_particles, 2) * 0.01
        self.particles[:, 0] += self.particles[:, 1] * self.dt + noise[:, 0]
        self.particles[:, 1] += noise[:, 1]
        return np.average(self.particles, weights=self.weights, axis=0)
    
    def update(self, z: float) -> np.ndarray:
        # Calculate likelihoods
        distances = np.abs(self.particles[:, 0] - z)
        likelihoods = np.exp(-distances**2 / (2 * self.measurement_noise**2))
        
        # Update weights
        self.weights *= likelihoods
        self.weights /= np.sum(self.weights) + 1e-10
        
        # Resample if effective sample size is low
        ess = 1.0 / np.sum(self.weights**2)
        if ess < self.n_particles / 2:
            self._resample()
        
        return np.average(self.particles, weights=self.weights, axis=0)
    
    def _resample(self) -> None:
        """Stratified resampling"""
        indices = np.zeros(self.n_particles, dtype=int)
        positions = (np.arange(self.n_particles) + np.random.random()) / self.n_particles
        
        cumsum = np.cumsum(self.weights)
        i, j = 0, 0
        while i < self.n_particles:
            if positions[i] < cumsum[j]:
                indices[i] = j
                i += 1
            else:
                j += 1
        
        self.particles = self.particles[indices]
        self.weights = np.ones(self.n_particles) / self.n_particles


class UnscentedKalmanFilter:
    """Unscented Kalman Filter"""
    
    def __init__(self, dt: float = 1.0, alpha: float = 0.001, beta: float = 2.0, kappa: float = 0.0):
        self.dt = dt
        self.alpha = alpha
        self.beta = beta
        self.kappa = kappa
        self.n = 2  # State dimension
        
        # Calculate sigma points weights
        lam = alpha**2 * (self.n + kappa) - self.n
        self.Wm = np.full(2 * self.n + 1, 0.5 / (self.n + lam))
        self.Wm[0] = lam / (self.n + lam)
        self.Wc = self.Wm.copy()
        self.Wc[0] += 1 - alpha**2 + beta
        
        self.x = np.zeros(self.n)
        self.P = np.eye(self.n)
        self.Q = np.eye(self.n) * 0.01
        self.R = np.array([[0.1]])
        
    def _sigma_points(self) -> np.ndarray:
        """Generate sigma points"""
        sqrt_P = np.linalg.cholesky(self.P)
        lam = self.alpha**2 * (self.n + self.kappa) - self.n
        
        sigma = np.zeros((2 * self.n + 1, self.n))
        sigma[0] = self.x
        for i in range(self.n):
            sigma[i + 1] = self.x + np.sqrt(self.n + lam) * sqrt_P[:, i]
            sigma[self.n + i + 1] = self.x - np.sqrt(self.n + lam) * sqrt_P[:, i]
        
        return sigma
    
    def _f(self, x: np.ndarray) -> np.ndarray:
        """State transition function"""
        F = np.array([[1, self.dt], [0, 1]])
        return F @ x
    
    def _h(self, x: np.ndarray) -> float:
        """Measurement function"""
        return x[0]
    
    def predict(self) -> np.ndarray:
        sigma = self._sigma_points()
        sigma_pred = np.array([self._f(s) for s in sigma])
        
        self.x = np.sum(self.Wm[:, None] * sigma_pred, axis=0)
        self.P = self.Q.copy()
        for i in range(2 * self.n + 1):
            diff = sigma_pred[i] - self.x
            self.P += self.Wc[i] * np.outer(diff, diff)
        
        return self.x.copy()
    
    def update(self, z: float) -> np.ndarray:
        sigma = self._sigma_points()
        sigma_pred = np.array([self._f(s) for s in sigma])
        
        # Predicted measurement
        z_pred = np.array([self._h(s) for s in sigma_pred])
        z_mean = np.sum(self.Wm * z_pred)
        
        # Innovation covariance
        Pzz = self.R.copy()
        for i in range(2 * self.n + 1):
            Pzz += self.Wc[i] * (z_pred[i] - z_mean)**2
        
        # Cross covariance
        Pxz = np.zeros((self.n, 1))
        for i in range(2 * self.n + 1):
            Pxz += self.Wc[i] * np.outer(sigma_pred[i] - self.x, z_pred[i] - z_mean)
        
        # Kalman gain
        K = Pxz / Pzz[0, 0]
        
        # Update state
        self.x += K.flatten() * (z - z_mean)
        self.P -= K @ Pzz @ K.T
        
        return self.x.copy()


class ExtendedKalmanFilter:
    """Extended Kalman Filter"""
    
    def __init__(self, dt: float = 1.0):
        self.dt = dt
        self.x = np.zeros(2)
        self.P = np.eye(2)
        self.Q = np.eye(2) * 0.01
        self.R = np.array([[0.1]])
        
    def _f(self, x: np.ndarray) -> np.ndarray:
        """Nonlinear state transition"""
        return np.array([x[0] + x[1] * self.dt, x[1]])
    
    def _F(self, x: np.ndarray) -> np.ndarray:
        """Jacobian of state transition"""
        return np.array([[1, self.dt], [0, 1]])
    
    def _h(self, x: np.ndarray) -> float:
        """Nonlinear measurement"""
        return x[0]
    
    def _H(self, x: np.ndarray) -> np.ndarray:
        """Jacobian of measurement"""
        return np.array([[1, 0]])
    
    def predict(self) -> np.ndarray:
        self.x = self._f(self.x)
        F = self._F(self.x)
        self.P = F @ self.P @ F.T + self.Q
        return self.x.copy()
    
    def update(self, z: float) -> np.ndarray:
        H = self._H(self.x)
        y = z - self._h(self.x)
        S = H @ self.P @ H.T + self.R
        K = self.P @ H.T / S[0, 0]
        self.x += K.flatten() * y
        self.P = (np.eye(2) - K @ H) @ self.P
        return self.x.copy()


class AdaptiveKalmanFilter:
    """Adaptive Kalman Filter with noise estimation"""
    
    def __init__(self, dt: float = 1.0, window: int = 50):
        self.dt = dt
        self.window = window
        self.x = np.zeros(2)
        self.P = np.eye(2)
        self.Q = np.eye(2) * 0.01
        self.R = np.array([[0.1]])
        self.H = np.array([[1.0, 0.0]])
        
        # Innovation history for noise estimation
        self.innovations = []
        
    def predict(self) -> np.ndarray:
        F = np.array([[1, self.dt], [0, 1]])
        self.x = F @ self.x
        self.P = F @ self.P @ F.T + self.Q
        return self.x.copy()
    
    def update(self, z: float) -> np.ndarray:
        y = z - self.H @ self.x
        self.innovations.append(float(y))
        
        # Adaptive noise estimation
        if len(self.innovations) > self.window:
            self.innovations = self.innovations[-self.window:]
            innovation_var = np.var(self.innovations)
            self.R = np.array([[innovation_var]])
        
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T / S[0, 0]
        self.x += K.flatten() * y
        self.P = (np.eye(2) - K @ self.H) @ self.P
        return self.x.copy()


class WaveletDenoiser:
    """Wavelet Denoising"""
    
    def __init__(self, wavelet: str = 'db4', level: int = 5):
        self.wavelet = wavelet
        self.level = level
        
    def denoise(self, data: np.ndarray) -> np.ndarray:
        """Apply wavelet denoising"""
        if len(data) < 2 ** self.level:
            return data
        
        # Decompose
        coeffs = pywt.wavedec(data, self.wavelet, level=self.level)
        
        # Threshold detail coefficients
        sigma = np.median(np.abs(coeffs[-1])) / 0.6745
        threshold = sigma * np.sqrt(2 * np.log(len(data)))
        
        denoised_coeffs = [coeffs[0]]  # Keep approximation coefficients
        for c in coeffs[1:]:
            denoised_coeffs.append(pywt.threshold(c, threshold, mode='soft'))
        
        # Reconstruct
        return pywt.waverec(denoised_coeffs, self.wavelet)[:len(data)]


class EMDDenoiser:
    """Empirical Mode Decomposition"""
    
    def __init__(self, n_imfs: int = 3):
        self.n_imfs = n_imfs
        
    def decompose(self, data: np.ndarray) -> List[np.ndarray]:
        """Simple EMD decomposition"""
        # Simplified EMD - in production use PyEMD
        imfs = []
        residual = data.copy()
        
        for _ in range(self.n_imfs):
            if len(residual) < 10:
                break
            
            # Simple sift
            t = np.arange(len(residual))
            mean_envelope = uniform_filter1d(residual, size=5)
            imf = residual - mean_envelope
            imfs.append(imf)
            residual = mean_envelope
        
        if len(residual) > 0:
            imfs.append(residual)
        
        return imfs
    
    def denoise(self, data: np.ndarray) -> np.ndarray:
        """Denoise using EMD"""
        imfs = self.decompose(data)
        # Sum first n_imfs
        return np.sum(imfs[:self.n_imfs], axis=0)


class SavitzkyGolayFilter:
    """Savitzky-Golay Filter"""
    
    def __init__(self, window_length: int = 11, polyorder: int = 3):
        self.window_length = window_length
        self.polyorder = polyorder
        
    def filter(self, data: np.ndarray) -> np.ndarray:
        """Apply Savitzky-Golay filter"""
        if len(data) < self.window_length:
            return data
        return scipy_signal.savgol_filter(data, self.window_length, self.polyorder)


class MultiScaleFilter:
    """
    Layer 2: Multi-Scale Filter
    Combines multiple filtering algorithms for comprehensive noise removal
    """
    
    def __init__(self, dt: float = 1.0):
        self.dt = dt
        
        # Initialize all filters
        self.kalman = KalmanFilter(dt)
        self.ensemble_kalman = EnsembleKalmanFilter(n_ensemble=50, dt=dt)
        self.particle_filter = ParticleFilter(n_particles=1000, dt=dt)
        self.ukf = UnscentedKalmanFilter(dt)
        self.ekf = ExtendedKalmanFilter(dt)
        self.adaptive_kf = AdaptiveKalmanFilter(dt)
        self.wavelet = WaveletDenoiser()
        self.emd = EMDDenoiser(n_imfs=3)
        self.savitzky_golay = SavitzkyGolayFilter()
        
        # State
        self.price_buffer: List[float] = []
        self.max_buffer_size = 1000
        
    def filter_tick(self, price: float, timestamp: float) -> FilterState:
        """
        Filter a single tick through all filters
        
        Args:
            price: Raw price
            timestamp: Tick timestamp
            
        Returns:
            Combined filter state
        """
        # Add to buffer
        self.price_buffer.append(price)
        if len(self.price_buffer) > self.max_buffer_size:
            self.price_buffer.pop(0)
        
        # Apply each filter
        states = []
        
        # Kalman filters
        self.kalman.predict()
        states.append(self.kalman.update(price))
        
        self.ensemble_kalman.predict()
        states.append(self.ensemble_kalman.update(price))
        
        self.particle_filter.predict()
        states.append(self.particle_filter.update(price))
        
        self.ukf.predict()
        states.append(self.ukf.update(price))
        
        self.ekf.predict()
        states.append(self.ekf.update(price))
        
        self.adaptive_kf.predict()
        states.append(self.adaptive_kf.update(price))
        
        # Combine estimates
        estimates = np.array([s[0] for s in states])
        velocities = np.array([s[1] for s in states])
        
        # Return combined state
        return FilterState(
            estimate=float(np.median(estimates)),
            velocity=float(np.median(velocities)),
            uncertainty=float(np.std(estimates)),
            innovation=float(price - np.median(estimates)),
            gain=float(np.mean([0.5, 0.5, 0.5, 0.5, 0.5, 0.5]))
        )
    
    def filter_series(self, prices: np.ndarray, timestamps: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Filter a series of prices
        
        Args:
            prices: Array of prices
            timestamps: Array of timestamps
            
        Returns:
            Dictionary of filtered series
        """
        n = len(prices)
        
        # Apply filters
        kalman_est = np.zeros(n)
        ensemble_est = np.zeros(n)
        particle_est = np.zeros(n)
        ukf_est = np.zeros(n)
        ekf_est = np.zeros(n)
        adaptive_est = np.zeros(n)
        
        for i in range(n):
            self.kalman.predict()
            kalman_est[i] = self.kalman.update(prices[i])[0]
            
            self.ensemble_kalman.predict()
            ensemble_est[i] = self.ensemble_kalman.update(prices[i])[0]
            
            self.particle_filter.predict()
            particle_est[i] = self.particle_filter.update(prices[i])[0]
            
            self.ukf.predict()
            ukf_est[i] = self.ukf.update(prices[i])[0]
            
            self.ekf.predict()
            ekf_est[i] = self.ekf.update(prices[i])[0]
            
            self.adaptive_kf.predict()
            adaptive_est[i] = self.adaptive_kf.update(prices[i])[0]
        
        # Wavelet denoising
        wavelet_est = self.wavelet.denoise(prices)
        
        # EMD denoising
        emd_est = self.emd.denoise(prices)
        
        # Savitzky-Golay
        sg_est = self.savitzky_golay.filter(prices)
        
        # Combined estimate
        all_estimates = np.stack([
            kalman_est, ensemble_est, particle_est, ukf_est,
            ekf_est, adaptive_est, wavelet_est, emd_est, sg_est
        ], axis=0)
        
        combined = np.median(all_estimates, axis=0)
        
        return {
            "combined": combined,
            "kalman": kalman_est,
            "ensemble_kalman": ensemble_est,
            "particle": particle_est,
            "ukf": ukf_est,
            "ekf": ekf_est,
            "adaptive": adaptive_est,
            "wavelet": wavelet_est,
            "emd": emd_est,
            "savitzky_golay": sg_est
        }
    
    def get_state(self) -> Dict[str, Any]:
        """Get current filter states"""
        return {
            "kalman": self.kalman.get_state(),
            "buffer_size": len(self.price_buffer),
            "last_price": self.price_buffer[-1] if self.price_buffer else 0.0
        }