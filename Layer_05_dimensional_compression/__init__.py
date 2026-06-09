"""
LAYER 5: DIMENSIONAL COMPRESSION
float32[168] → PCA(95% variance)
StandardScaler normalization
Autoencoder bottleneck (optional)
OUTPUT: compressed_vector[n_components]
"""

from .dimensional_compression import DimensionalCompression

__all__ = ["DimensionalCompression"]