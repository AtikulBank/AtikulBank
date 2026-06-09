# cython: boundscheck=False, wraparound=False, cdivision=True
# cython: language_level=3
# distutils: extra_compile_args = -march=native -O3 -ffast-math
# distutils: extra_link_args = -march=native

"""
LAYER 5: DIMENSIONAL COMPRESSION - CYTHON WRAPPER
High-performance dimensionality reduction with C++ backend

AWS C7g Optimizations:
- ARM64 NEON SIMD
- Branch prediction hints
- Cache-friendly memory access
"""

import numpy as np
cimport numpy as cnp
from libc.stdlib cimport malloc, free
from libc.string cimport memcpy

# Import numpy C API
cnp.import_array()

# C++ function declarations
cdef extern from "compression_core.h" namespace "compression":
    cdef cppclass PCACompressor:
        PCACompressor(int n_components, double variance_threshold)
        void fit(const double* X, int n_samples, int n_features)
        void transform(const double* x, double* z) const
        void inverse_transform(const double* z, double* x) const
        int get_n_components() const
        double get_variance_explained() const
    
    cdef cppclass SVDCompressor:
        SVDCompressor(int n_components)
        void fit(const double* X, int n_samples, int n_features)
        void transform(const double* x, double* z) const
        void inverse_transform(const double* z, double* x) const
    
    cdef cppclass RandomProjector:
        RandomProjector(int n_components, double epsilon)
        void init(int n_features)
        void transform(const double* x, double* z) const
        @staticmethod
        int compute_optimal_dimensions(int n_samples, double epsilon)

# C API declarations
cdef extern from "compression_core.cpp":
    void* pca_create(int n_components, double variance_threshold)
    void pca_fit(void* pca, const double* X, int n_samples, int n_features)
    void pca_transform(void* pca, const double* x, double* z)
    void pca_inverse_transform(void* pca, const double* z, double* x)
    int pca_get_n_components(void* pca)
    double pca_get_variance_explained(void* pca)
    void pca_destroy(void* pca)
    
    void* svd_create(int n_components)
    void svd_fit(void* svd, const double* X, int n_samples, int n_features)
    void svd_transform(void* svd, const double* x, double* z)
    void svd_inverse_transform(void* svd, const double* z, double* x)
    void svd_destroy(void* svd)
    
    void* random_projector_create(int n_components, double epsilon)
    void random_projector_init(void* rp, int n_features)
    void random_projector_transform(void* rp, const double* x, double* z)
    void random_projector_destroy(void* rp)


class PCACython:
    """
    High-performance PCA with C++ backend
    
    AWS C7g Optimized:
    - NEON SIMD for matrix operations
    - Cache-friendly memory layout
    - Branch prediction hints
    """
    
    def __init__(self, int n_components=50, double variance_threshold=0.95):
        self._pca = pca_create(n_components, variance_threshold)
        self._n_components = n_components
        self._is_fitted = False
    
    def __dealloc__(self):
        if self._pca != NULL:
            pca_destroy(self._pca)
    
    def fit(self, cnp.ndarray[double, ndim=2] X):
        """Fit PCA on training data"""
        cdef int n_samples = X.shape[0]
        cdef int n_features = X.shape[1]
        
        pca_fit(self._pca, &X[0, 0], n_samples, n_features)
        self._n_components = pca_get_n_components(self._pca)
        self._is_fitted = True
    
    def transform(self, cnp.ndarray[double, ndim=1] x):
        """Transform to reduced dimensions"""
        cdef cnp.ndarray[double, ndim=1] z = np.zeros(self._n_components)
        pca_transform(self._pca, &x[0], &z[0])
        return z
    
    def inverse_transform(self, cnp.ndarray[double, ndim=1] z):
        """Reconstruct to original space"""
        cdef cnp.ndarray[double, ndim=1] x = np.zeros(168)
        pca_inverse_transform(self._pca, &z[0], &x[0])
        return x
    
    @property
    def n_components(self):
        return self._n_components
    
    @property
    def variance_explained(self):
        return pca_get_variance_explained(self._pca)


class SVDCython:
    """
    High-performance SVD with C++ backend
    """
    
    def __init__(self, int n_components=50):
        self._svd = svd_create(n_components)
        self._n_components = n_components
        self._is_fitted = False
    
    def __dealloc__(self):
        if self._svd != NULL:
            svd_destroy(self._svd)
    
    def fit(self, cnp.ndarray[double, ndim=2] X):
        """Fit SVD on training data"""
        cdef int n_samples = X.shape[0]
        cdef int n_features = X.shape[1]
        
        svd_fit(self._svd, &X[0, 0], n_samples, n_features)
        self._is_fitted = True
    
    def transform(self, cnp.ndarray[double, ndim=1] x):
        """Transform to reduced dimensions"""
        cdef cnp.ndarray[double, ndim=1] z = np.zeros(self._n_components)
        svd_transform(self._svd, &x[0], &z[0])
        return z
    
    def inverse_transform(self, cnp.ndarray[double, ndim=1] z):
        """Reconstruct to original space"""
        cdef cnp.ndarray[double, ndim=1] x = np.zeros(168)
        svd_inverse_transform(self._svd, &z[0], &x[0])
        return x


class RandomProjectorCython:
    """
    High-performance Random Projection with C++ backend
    
    Johnson-Lindenstrauss dimensionality reduction
    """
    
    def __init__(self, int n_components=50, double epsilon=0.1):
        self._rp = random_projector_create(n_components, epsilon)
        self._n_components = n_components
        self._is_initialized = False
    
    def __dealloc__(self):
        if self._rp != NULL:
            random_projector_destroy(self._rp)
    
    def init(self, int n_features):
        """Initialize random projection matrix"""
        random_projector_init(self._rp, n_features)
        self._is_initialized = True
    
    def transform(self, cnp.ndarray[double, ndim=1] x):
        """Transform using random projection"""
        cdef cnp.ndarray[double, ndim=1] z = np.zeros(self._n_components)
        random_projector_transform(self._rp, &x[0], &z[0])
        return z
    
    @staticmethod
    def compute_optimal_dimensions(int n_samples, double epsilon):
        """Compute optimal dimensions for Johnson-Lindenstrauss"""
        return RandomProjector.compute_optimal_dimensions(n_samples, epsilon)


class DimensionalCompressionCython:
    """
    High-performance Dimensional Compression with C++ backend
    
    Features:
    - PCA compression
    - SVD compression
    - Random projection
    - Autoencoder (PyTorch backend)
    
    AWS C7g Optimized:
    - NEON SIMD for matrix operations
    - Cache-friendly memory layout
    - Branch prediction hints
    """
    
    def __init__(self, 
                 int target_components=50,
                 double variance_threshold=0.95,
                 str method='pca'):
        """
        Initialize Dimensional Compression
        
        Args:
            target_components: Target number of components
            variance_threshold: Target variance to explain
            method: 'pca', 'svd', or 'random_projection'
        """
        self._method = method
        self._target_components = target_components
        self._variance_threshold = variance_threshold
        self._is_fitted = False
        
        if method == 'pca':
            self._compressor = PCACython(target_components, variance_threshold)
        elif method == 'svd':
            self._compressor = SVDCython(target_components)
        elif method == 'random_projection':
            self._compressor = RandomProjectorCython(target_components)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def fit(self, cnp.ndarray[double, ndim=2] X):
        """
        Fit compression model on training data
        
        Args:
            X: Training data of shape (n_samples, 168)
        """
        if self._method == 'random_projection':
            self._compressor.init(X.shape[1])
        else:
            self._compressor.fit(X)
        
        self._is_fitted = True
    
    def compress(self, cnp.ndarray[double, ndim=1] features):
        """
        Compress features
        
        Args:
            features: Input features of shape (168,)
        
        Returns:
            Compressed features
        """
        if not self._is_fitted:
            raise RuntimeError("Model not fitted. Call fit() first.")
        
        return self._compressor.transform(features)
    
    def decompress(self, cnp.ndarray[double, ndim=1] compressed):
        """
        Decompress features
        
        Args:
            compressed: Compressed features
        
        Returns:
            Reconstructed features of shape (168,)
        """
        if not self._is_fitted:
            raise RuntimeError("Model not fitted. Call fit() first.")
        
        if self._method == 'random_projection':
            raise NotImplementedError("Random projection is not invertible")
        
        return self._compressor.inverse_transform(compressed)
    
    @property
    def n_components(self):
        if hasattr(self._compressor, 'n_components'):
            return self._compressor.n_components
        return self._target_components
    
    @property
    def variance_explained(self):
        if hasattr(self._compressor, 'variance_explained'):
            return self._compressor.variance_explained
        return 0.0