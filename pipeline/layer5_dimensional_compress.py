"""
LAYER 5: DIMENSIONAL COMPRESSION
float32[168] → PCA(95% variance) | StandardScaler | Autoencoder bottleneck

Compresses 168-dimensional filter vector to lower dimensions for ML inference.
"""
from __future__ import annotations

import numpy as np
from typing import List, Optional, Tuple
from collections import deque

from pipeline import FilterVector168, CompressedVector


class StandardScaler:
    """Online standard scaler with running statistics."""

    def __init__(self, n_features: int = 168):
        self.n = n_features
        self._count = 0
        self._mean = np.zeros(n_features)
        self._M2 = np.zeros(n_features)
        self._initialized = False

    def partial_fit(self, x: np.ndarray) -> None:
        if not self._initialized or len(x) != self.n:
            self.n = len(x)
            self._mean = np.zeros(self.n)
            self._M2 = np.zeros(self.n)
            self._initialized = True
        self._count += 1
        delta = x - self._mean
        self._mean += delta / self._count
        delta2 = x - self._mean
        self._M2 += delta * delta2

    def transform(self, x: np.ndarray) -> np.ndarray:
        if self._count < 2:
            return x
        var = self._M2 / (self._count - 1)
        std = np.sqrt(var)
        std[std == 0] = 1.0
        return (x - self._mean) / std

    @property
    def fitted(self) -> bool:
        return self._count >= 2


class PCACompressor:
    """Incremental PCA via power iteration."""

    def __init__(self, n_components: int = 30, variance_target: float = 0.95):
        self.n_components = n_components
        self.variance_target = variance_target
        self._components: Optional[np.ndarray] = None
        self._mean: Optional[np.ndarray] = None
        self._explained_ratio: Optional[np.ndarray] = None
        self._fitted = False
        self._buffer: list = []
        self._buffer_size = 500

    def partial_fit(self, x: np.ndarray) -> None:
        self._buffer.append(x)
        if len(self._buffer) >= self._buffer_size:
            self._fit_buffer()

    def _fit_buffer(self) -> None:
        if len(self._buffer) < 10:
            return
        X = np.array(self._buffer)
        self._mean = np.mean(X, axis=0)
        X_centered = X - self._mean
        cov = np.cov(X_centered.T)
        eigenvalues, eigenvectors = np.linalg.eigh(cov)
        idx = np.argsort(eigenvalues)[::-1]
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]
        total_var = np.sum(eigenvalues)
        if total_var > 0:
            self._explained_ratio = eigenvalues / total_var
        cumulative = np.cumsum(self._explained_ratio)
        n_keep = np.searchsorted(cumulative, self.variance_target) + 1
        n_keep = min(n_keep, self.n_components, len(eigenvalues))
        self._components = eigenvectors[:, :n_keep].T
        self._fitted = True
        self._buffer = []

    def transform(self, x: np.ndarray) -> np.ndarray:
        if not self._fitted or self._components is None or self._mean is None:
            return x[:self.n_components] if len(x) > self.n_components else x
        centered = x - self._mean
        return self._components @ centered

    @property
    def n_kept(self) -> int:
        return self._components.shape[0] if self._components is not None else 0


class AutoencoderBottleneck:
    """Simple linear autoencoder for additional compression."""

    def __init__(self, input_dim: int = 30, bottleneck_dim: int = 15):
        self.input_dim = input_dim
        self.bottleneck_dim = bottleneck_dim
        scale = np.sqrt(2.0 / input_dim)
        self.W_enc = np.random.randn(input_dim, bottleneck_dim) * scale
        self.W_dec = np.random.randn(bottleneck_dim, input_dim) * scale
        self.b_enc = np.zeros(bottleneck_dim)
        self.b_dec = np.zeros(input_dim)
        self.lr = 0.001

    def encode(self, x: np.ndarray) -> np.ndarray:
        return np.maximum(0, x @ self.W_enc + self.b_enc)

    def decode(self, z: np.ndarray) -> np.ndarray:
        return z @ self.W_dec + self.b_dec

    def forward(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        z = self.encode(x)
        x_hat = self.decode(z)
        return z, x_hat

    def update(self, x: np.ndarray) -> float:
        z, x_hat = self.forward(x)
        loss = np.mean((x - x_hat) ** 2)
        grad_out = 2 * (x_hat - x) / len(x)
        grad_dec = np.outer(z, grad_out)
        grad_b_dec = grad_out
        grad_z = grad_out @ self.W_dec.T
        grad_enc_mask = (z > 0).astype(float)
        grad_enc = np.outer(x, grad_z * grad_enc_mask)
        grad_b_enc = grad_z * grad_enc_mask
        self.W_enc -= self.lr * grad_enc
        self.b_enc -= self.lr * grad_b_enc
        self.W_dec -= self.lr * grad_dec
        self.b_dec -= self.lr * grad_b_dec
        return float(loss)


class DimensionalCompressor:
    """
    LAYER 5: Dimensional Compression
    Compresses 168 → PCA components → Autoencoder bottleneck.
    """

    def __init__(self, pca_components: int = 30, ae_bottleneck: int = 15, variance_target: float = 0.95):
        self.scaler = StandardScaler(n_features=168)
        self.pca = PCACompressor(n_components=pca_components, variance_target=variance_target)
        self.autoencoder = AutoencoderBottleneck(input_dim=pca_components, bottleneck_dim=ae_bottleneck)
        self._count = 0
        self._input_dim = None

    def compress(self, fv: FilterVector168) -> CompressedVector:
        arr = np.array(fv.to_array(), dtype=np.float32)
        self._count += 1
        self.scaler.partial_fit(arr)
        self.pca.partial_fit(arr)
        if self.pca._fitted:
            scaled = self.scaler.transform(arr)
            pca_result = self.pca.transform(scaled)
            self.autoencoder.update(pca_result)
        else:
            self.autoencoder.update(arr[:30] if len(arr) > 30 else arr)

        cv = CompressedVector()
        if self.scaler._count > 1:
            scaled = self.scaler.transform(arr)
            if self.pca._fitted:
                pca_result = self.pca.transform(scaled)
                cv.pca_components = pca_result.tolist()
                cv.n_components = len(pca_result)
                cv.variance_explained = float(np.sum(self.pca._explained_ratio[:self.pca.n_kept])) if self.pca._explained_ratio is not None else 0.0
                ae_result = self.autoencoder.encode(pca_result)
                cv.autoencoder_bottleneck = ae_result.tolist()
            else:
                cv.pca_components = scaled[:30].tolist()
                cv.n_components = min(30, len(scaled))
        return cv

    @property
    def stats(self) -> dict:
        return {"count": self._count, "pca_n": self.pca.n_kept, "pca_fitted": self.pca._fitted, "scaler_fitted": self.scaler.fitted}
