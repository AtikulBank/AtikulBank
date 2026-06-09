/**
 * LAYER 5: DIMENSIONAL COMPRESSION - C++ CORE
 * High-performance dimensionality reduction with AWS C7g optimization
 * 
 * Features:
 * - PCA (Principal Component Analysis)
 * - SVD (Singular Value Decomposition)
 * - Random Projection (Johnson-Lindenstrauss)
 * - Autoencoder inference
 * 
 * AWS C7g Optimizations:
 * - ARM64 NEON SIMD
 * - Branch prediction hints
 * - Cache-friendly data structures
 * - Lock-free computation
 */

#ifndef COMPRESSION_CORE_H
#define COMPRESSION_CORE_H

#include <cstdint>
#include <cstring>
#include <cmath>
#include <algorithm>
#include <vector>
#include <numeric>

// AWS C7g (Graviton3) specific intrinsics
#ifdef __ARM_NEON
#include <arm_neon.h>
#endif

#ifdef __AVX2__
#include <immintrin.h>
#endif

namespace compression {

// Configuration constants
constexpr double PCA_VARIANCE_THRESHOLD = 0.95;
constexpr int MAX_PCA_COMPONENTS = 50;
constexpr double RANDOM_PROJECTION_EPSILON = 0.1;

/**
 * PCA Compressor
 * Principal Component Analysis for dimensionality reduction
 */
class PCACompressor {
public:
    PCACompressor(int n_components = MAX_PCA_COMPONENTS, double variance_threshold = PCA_VARIANCE_THRESHOLD);
    ~PCACompressor() = default;
    
    /**
     * Fit PCA on training data
     * 
     * @param X Training data (n_samples x n_features)
     * @param n_samples Number of samples
     * @param n_features Number of features (168)
     */
    void fit(const double* X, int n_samples, int n_features);
    
    /**
     * Transform data to reduced dimensions
     * 
     * @param x Input features (n_features)
     * @param z Output compressed (n_components)
     */
    void transform(const double* x, double* z) const;
    
    /**
     * Inverse transform back to original space
     * 
     * @param z Compressed features (n_components)
     * @param x Output reconstructed (n_features)
     */
    void inverse_transform(const double* z, double* x) const;
    
    /**
     * Get number of components
     */
    int get_n_components() const { return n_components_; }
    
    /**
     * Get variance explained
     */
    double get_variance_explained() const { return variance_explained_; }

private:
    int n_components_;
    int n_features_;
    double variance_threshold_;
    double variance_explained_;
    
    std::vector<double> mean_;           // Feature means
    std::vector<double> components_;     // Principal components (n_features x n_components)
    std::vector<double> eigenvalues_;    // Eigenvalues
    
    /**
     * Center data (subtract mean)
     */
    void center_data(const double* X, int n_samples, double* X_centered) const;
    
    /**
     * Compute covariance matrix
     */
    void compute_covariance(const double* X_centered, int n_samples, int n_features, double* cov) const;
    
    /**
     * Compute eigenvectors using Jacobi iteration
     */
    void compute_eigenvectors(double* cov, int n, double* eigenvalues, double* eigenvectors) const;
    
    /**
     * Select components based on variance threshold
     */
    void select_components(double* eigenvalues, double* eigenvectors, int n);
};

/**
 * SVD Compressor
 * Singular Value Decomposition for dimensionality reduction
 */
class SVDCompressor {
public:
    SVDCompressor(int n_components = MAX_PCA_COMPONENTS);
    ~SVDCompressor() = default;
    
    /**
     * Fit SVD on training data
     */
    void fit(const double* X, int n_samples, int n_features);
    
    /**
     * Transform data
     */
    void transform(const double* x, double* z) const;
    
    /**
     * Inverse transform
     */
    void inverse_transform(const double* z, double* x) const;
    
    /**
     * Get singular values
     */
    const std::vector<double>& get_singular_values() const { return singular_values_; }

private:
    int n_components_;
    int n_features_;
    
    std::vector<double> U_;              // Left singular vectors
    std::vector<double> S_;              // Singular values
    std::vector<double> Vt_;             // Right singular vectors
    std::vector<double> mean_;           // Feature means
    
    /**
     * Compute SVD using Golub-Reinsch algorithm
     */
    void compute_svd(const double* X, int m, int n, double* U, double* S, double* Vt) const;
};

/**
 * Random Projector
 * Johnson-Lindenstrauss dimensionality reduction
 */
class RandomProjector {
public:
    RandomProjector(int n_components = 50, double epsilon = RANDOM_PROJECTION_EPSILON);
    ~RandomProjector() = default;
    
    /**
     * Initialize random projection matrix
     */
    void init(int n_features);
    
    /**
     * Transform data
     */
    void transform(const double* x, double* z) const;
    
    /**
     * Compute optimal dimensions for epsilon
     */
    static int compute_optimal_dimensions(int n_samples, double epsilon);

private:
    int n_components_;
    int n_features_;
    double epsilon_;
    
    std::vector<double> projection_matrix_;  // Random projection matrix
    
    /**
     * Generate Gaussian random matrix
     */
    void generate_projection_matrix();
};

/**
 * Autoencoder Inference (C++ backend for PyTorch model)
 */
class AutoencoderInference {
public:
    AutoencoderInference(int input_dim, int latent_dim);
    ~AutoencoderInference() = default;
    
    /**
     * Load weights from file
     */
    void load_weights(const char* encoder_path, const char* decoder_path);
    
    /**
     * Encode (compress)
     */
    void encode(const double* x, double* z) const;
    
    /**
     * Decode (decompress)
     */
    void decode(const double* z, double* x) const;

private:
    int input_dim_;
    int latent_dim_;
    
    // Encoder weights
    std::vector<double> W_encoder_;  // Weight matrix
    std::vector<double> b_encoder_;  // Bias vector
    
    // Decoder weights
    std::vector<double> W_decoder_;  // Weight matrix
    std::vector<double> b_decoder_;  // Bias vector
    
    /**
     * ReLU activation
     */
    static double relu(double x) { return x > 0 ? x : 0; }
    
    /**
     * Matrix-vector multiply
     */
    void matvec(const double* W, const double* x, double* y, int m, int n) const;
};

}  // namespace compression

#endif  // COMPRESSION_CORE_H