"""
LAYER 5: DIMENSIONAL COMPRESSION
Reduces 168 features to compressed representation
"""

import numpy as np
from typing import Dict, Any, Optional, Tuple
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from dataclasses import dataclass


@dataclass
class CompressionResult:
    """Result of dimensional compression"""
    compressed_vector: np.ndarray = None
    original_size: int = 0
    compressed_size: int = 0
    variance_explained: float = 0.0
    reconstruction_error: float = 0.0


class DimensionalCompression:
    """
    Layer 5: Dimensional Compression
    Reduces 168 features to compressed representation using PCA and optional autoencoder
    """
    
    def __init__(
        self,
        target_variance: float = 0.95,
        max_components: int = 50,
        use_autoencoder: bool = False
    ):
        """
        Initialize Dimensional Compression
        
        Args:
            target_variance: Target variance to explain (default: 95%)
            max_components: Maximum number of PCA components
            use_autoencoder: Whether to use autoencoder for compression
        """
        self.target_variance = target_variance
        self.max_components = max_components
        self.use_autoencoder = use_autoencoder
        
        # PCA for dimensionality reduction
        self.pca = PCA(n_components=max_components)
        
        # StandardScaler for normalization
        self.scaler = StandardScaler()
        
        # Optional autoencoder
        self.autoencoder = None
        if use_autoencoder:
            self.autoencoder = MLPRegressor(
                hidden_layer_sizes=(100, 50, 20, 50, 100),
                activation='relu',
                max_iter=1000,
                random_state=42
            )
        
        # State
        self._is_fitted = False
        self._n_components = max_components
        
    def fit(self, features: np.ndarray) -> None:
        """
        Fit compression model on training data
        
        Args:
            features: Training features of shape (n_samples, 168)
        """
        if features.shape[1] != 168:
            raise ValueError(f"Expected 168 features, got {features.shape[1]}")
        
        # Fit scaler
        features_scaled = self.scaler.fit_transform(features)
        
        # Fit PCA
        self.pca.fit(features_scaled)
        
        # Determine number of components for target variance
        cumulative_variance = np.cumsum(self.pca.explained_variance_ratio_)
        self._n_components = np.searchsorted(cumulative_variance, self.target_variance) + 1
        self._n_components = min(self._n_components, self.max_components)
        
        # Refit PCA with optimal number of components
        self.pca.n_components = self._n_components
        self.pca.fit(features_scaled)
        
        # Fit autoencoder if enabled
        if self.use_autoencoder and self.autoencoder is not None:
            # Autoencoder input = PCA compressed
            pca_compressed = self.pca.transform(features_scaled)
            self.autoencoder.fit(pca_compressed, pca_compressed)
        
        self._is_fitted = True
        
    def compress(self, features: np.ndarray) -> CompressionResult:
        """
        Compress features
        
        Args:
            features: Input features of shape (n_samples, 168) or (168,)
            
        Returns:
            CompressionResult with compressed vector
        """
        if not self._is_fitted:
            raise RuntimeError("Model not fitted. Call fit() first.")
        
        # Handle single sample
        if features.ndim == 1:
            features = features.reshape(1, -1)
        
        # Ensure 168 features
        if features.shape[1] != 168:
            # Pad or truncate to 168
            if features.shape[1] < 168:
                features = np.pad(features, ((0, 0), (0, 168 - features.shape[1])))
            else:
                features = features[:, :168]
        
        # Scale features
        features_scaled = self.scaler.transform(features)
        
        # PCA compression
        pca_compressed = self.pca.transform(features_scaled)
        
        # Optional autoencoder compression
        if self.use_autoencoder and self.autoencoder is not None:
            compressed = self.autoencoder.predict(pca_compressed)
        else:
            compressed = pca_compressed
        
        # Calculate reconstruction error
        pca_reconstructed = self.pca.inverse_transform(pca_compressed)
        reconstruction_error = np.mean((features_scaled - pca_reconstructed) ** 2)
        
        # Variance explained
        variance_explained = np.sum(self.pca.explained_variance_ratio_)
        
        return CompressionResult(
            compressed_vector=compressed.flatten(),
            original_size=168,
            compressed_size=compressed.shape[1] if compressed.ndim > 1 else compressed.shape[0],
            variance_explained=variance_explained,
            reconstruction_error=reconstruction_error
        )
    
    def decompress(self, compressed: np.ndarray) -> np.ndarray:
        """
        Decompress features back to original space
        
        Args:
            compressed: Compressed features
            
        Returns:
            Reconstructed features of shape (n_samples, 168)
        """
        if not self._is_fitted:
            raise RuntimeError("Model not fitted. Call fit() first.")
        
        # Handle single sample
        if compressed.ndim == 1:
            compressed = compressed.reshape(1, -1)
        
        # Optional autoencoder decompression
        if self.use_autoencoder and self.autoencoder is not None:
            pca_compressed = self.autoencoder.predict(compressed)
        else:
            pca_compressed = compressed
        
        # PCA decompression
        features_scaled = self.pca.inverse_transform(pca_compressed)
        
        # Inverse scale
        features = self.scaler.inverse_transform(features_scaled)
        
        return features
    
    def get_info(self) -> Dict[str, Any]:
        """Get compression information"""
        return {
            "is_fitted": self._is_fitted,
            "n_components": self._n_components,
            "target_variance": self.target_variance,
            "max_components": self.max_components,
            "use_autoencoder": self.use_autoencoder,
            "variance_explained": float(np.sum(self.pca.explained_variance_ratio_)) if self._is_fitted else 0.0,
            "compression_ratio": 168 / self._n_components if self._n_components > 0 else 1.0
        }