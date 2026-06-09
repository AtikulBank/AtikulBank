/**
 * LAYER 5: DIMENSIONAL COMPRESSION - C++ IMPLEMENTATION
 * High-performance dimensionality reduction with AWS C7g optimization
 */

#include "compression_core.h"
#include <cmath>
#include <cstring>
#include <algorithm>

namespace compression {

// ============================================================================
// PCA Compressor
// ============================================================================

PCACompressor::PCACompressor(int n_components, double variance_threshold)
    : n_components_(n_components), variance_threshold_(variance_threshold), variance_explained_(0.0) {}

void PCACompressor::center_data(const double* X, int n_samples, double* X_centered) const {
    // Compute mean
    std::vector<double> mean(n_features_, 0.0);
    for (int i = 0; i < n_samples; i++) {
        for (int j = 0; j < n_features_; j++) {
            mean[j] += X[i * n_features_ + j];
        }
    }
    for (int j = 0; j < n_features_; j++) {
        mean[j] /= n_samples;
    }
    
    // Center data
    for (int i = 0; i < n_samples; i++) {
        for (int j = 0; j < n_features_; j++) {
            X_centered[i * n_features_ + j] = X[i * n_features_ + j] - mean[j];
        }
    }
}

void PCACompressor::compute_covariance(const double* X_centered, int n_samples, int n_features, double* cov) const {
    // Cov = (1/(n-1)) * X^T * X
    double scale = 1.0 / (n_samples - 1);
    
    for (int i = 0; i < n_features; i++) {
        for (int j = i; j < n_features; j++) {
            double sum = 0.0;
            for (int k = 0; k < n_samples; k++) {
                sum += X_centered[k * n_features + i] * X_centered[k * n_features + j];
            }
            cov[i * n_features + j] = sum * scale;
            cov[j * n_features + i] = cov[i * n_features + j];  // Symmetric
        }
    }
}

void PCACompressor::compute_eigenvectors(double* cov, int n, double* eigenvalues, double* eigenvectors) const {
    // Initialize eigenvectors as identity
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            eigenvectors[i * n + j] = (i == j) ? 1.0 : 0.0;
        }
    }
    
    // Jacobi eigenvalue algorithm
    for (int iter = 0; iter < 100; iter++) {
        // Find largest off-diagonal element
        int p = 0, q = 1;
        double max_val = std::abs(cov[0 * n + 1]);
        
        for (int i = 0; i < n; i++) {
            for (int j = i + 1; j < n; j++) {
                if (std::abs(cov[i * n + j]) > max_val) {
                    max_val = std::abs(cov[i * n + j]);
                    p = i;
                    q = j;
                }
            }
        }
        
        if (max_val < 1e-10) break;  // Converged
        
        // Compute rotation angle
        double theta = 0.5 * std::atan2(2 * cov[p * n + q], cov[p * n + p] - cov[q * n + q]);
        double c = std::cos(theta);
        double s = std::sin(theta);
        
        // Apply rotation to covariance matrix
        for (int i = 0; i < n; i++) {
            double vip = cov[i * n + p];
            double viq = cov[i * n + q];
            cov[i * n + p] = c * vip + s * viq;
            cov[i * n + q] = -s * vip + c * viq;
        }
        
        for (int j = 0; j < n; j++) {
            double vpj = cov[p * n + j];
            double vqj = cov[q * n + j];
            cov[p * n + j] = c * vpj + s * vqj;
            cov[q * n + j] = -s * vpj + c * vqj;
        }
        
        // Update eigenvectors
        for (int i = 0; i < n; i++) {
            double vip = eigenvectors[i * n + p];
            double viq = eigenvectors[i * n + q];
            eigenvectors[i * n + p] = c * vip + s * viq;
            eigenvectors[i * n + q] = -s * vip + c * viq;
        }
    }
    
    // Extract eigenvalues
    for (int i = 0; i < n; i++) {
        eigenvalues[i] = cov[i * n + i];
    }
}

void PCACompressor::select_components(double* eigenvalues, double* eigenvectors, int n) {
    // Sort eigenvalues in descending order
    std::vector<int> indices(n);
    std::iota(indices.begin(), indices.end(), 0);
    std::sort(indices.begin(), indices.end(), [&](int a, int b) {
        return eigenvalues[a] > eigenvalues[b];
    });
    
    // Compute cumulative variance
    double total_variance = 0.0;
    for (int i = 0; i < n; i++) {
        total_variance += std::max(0.0, eigenvalues[indices[i]]);
    }
    
    double cumulative = 0.0;
    n_components_ = 0;
    
    for (int i = 0; i < n && i < n_components_; i++) {
        cumulative += std::max(0.0, eigenvalues[indices[i]]);
        n_components_ = i + 1;
        
        if (cumulative / total_variance >= variance_threshold_) {
            break;
        }
    }
    
    variance_explained_ = cumulative / total_variance;
    
    // Store selected components
    components_.resize(n_features_ * n_components_);
    for (int i = 0; i < n_components_; i++) {
        for (int j = 0; j < n_features_; j++) {
            components_[j * n_components_ + i] = eigenvectors[j * n + indices[i]];
        }
    }
    
    eigenvalues_.resize(n_components_);
    for (int i = 0; i < n_components_; i++) {
        eigenvalues_[i] = eigenvalues[indices[i]];
    }
}

void PCACompressor::fit(const double* X, int n_samples, int n_features) {
    n_features_ = n_features;
    
    // Compute mean
    mean_.resize(n_features, 0.0);
    for (int i = 0; i < n_samples; i++) {
        for (int j = 0; j < n_features; j++) {
            mean_[j] += X[i * n_features + j];
        }
    }
    for (int j = 0; j < n_features; j++) {
        mean_[j] /= n_samples;
    }
    
    // Center data
    std::vector<double> X_centered(n_samples * n_features);
    center_data(X, n_samples, X_centered.data());
    
    // Compute covariance
    std::vector<double> cov(n_features * n_features);
    compute_covariance(X_centered.data(), n_samples, n_features, cov.data());
    
    // Compute eigenvectors
    std::vector<double> eigenvalues(n_features);
    std::vector<double> eigenvectors(n_features * n_features);
    compute_eigenvectors(cov.data(), n_features, eigenvalues.data(), eigenvectors.data());
    
    // Select components
    select_components(eigenvalues.data(), eigenvectors.data(), n_features);
}

void PCACompressor::transform(const double* x, double* z) const {
    // Center input
    std::vector<double> x_centered(n_features_);
    for (int j = 0; j < n_features_; j++) {
        x_centered[j] = x[j] - mean_[j];
    }
    
    // Project: z = x_centered * components
    for (int i = 0; i < n_components_; i++) {
        double sum = 0.0;
        for (int j = 0; j < n_features_; j++) {
            sum += x_centered[j] * components_[j * n_components_ + i];
        }
        z[i] = sum;
    }
}

void PCACompressor::inverse_transform(const double* z, double* x) const {
    // Reconstruct: x = z * components^T + mean
    for (int j = 0; j < n_features_; j++) {
        double sum = 0.0;
        for (int i = 0; i < n_components_; i++) {
            sum += z[i] * components_[j * n_components_ + i];
        }
        x[j] = sum + mean_[j];
    }
}

// ============================================================================
// SVD Compressor
// ============================================================================

SVDCompressor::SVDCompressor(int n_components) : n_components_(n_components) {}

void SVDCompressor::compute_svd(const double* X, int m, int n, double* U, double* S, double* Vt) const {
    // Simplified SVD using Golub-Reinsch algorithm
    // For production, use LAPACK's dgesvd
    
    // Compute X^T * X
    std::vector<double> XtX(n * n, 0.0);
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            double sum = 0.0;
            for (int k = 0; k < m; k++) {
                sum += X[k * n + i] * X[k * n + j];
            }
            XtX[i * n + j] = sum;
        }
    }
    
    // Compute eigenvectors of X^T * X (gives V and S^2)
    std::vector<double> eigenvalues(n);
    std::vector<double> eigenvectors(n * n);
    
    // Use Jacobi for symmetric matrix
    PCACompressor pca;
    pca.compute_eigenvectors(XtX.data(), n, eigenvalues.data(), eigenvectors.data());
    
    // Sort by eigenvalue
    std::vector<int> indices(n);
    std::iota(indices.begin(), indices.end(), 0);
    std::sort(indices.begin(), indices.end(), [&](int a, int b) {
        return eigenvalues[a] > eigenvalues[b];
    });
    
    // Store Vt (transpose of V)
    for (int i = 0; i < n; i++) {
        S[i] = std::sqrt(std::max(0.0, eigenvalues[indices[i]]));
        for (int j = 0; j < n; j++) {
            Vt[i * n + j] = eigenvectors[j * n + indices[i]];
        }
    }
    
    // Compute U = X * V * S^{-1}
    for (int i = 0; i < m; i++) {
        for (int j = 0; j < std::min(m, n); j++) {
            double sum = 0.0;
            for (int k = 0; k < n; k++) {
                sum += X[i * n + k] * Vt[j * n + k];
            }
            U[i * n + j] = (S[j] > 1e-10) ? sum / S[j] : 0.0;
        }
    }
}

void SVDCompressor::fit(const double* X, int n_samples, int n_features) {
    n_features_ = n_features;
    
    // Compute mean
    mean_.resize(n_features, 0.0);
    for (int i = 0; i < n_samples; i++) {
        for (int j = 0; j < n_features; j++) {
            mean_[j] += X[i * n_features + j];
        }
    }
    for (int j = 0; j < n_features; j++) {
        mean_[j] /= n_samples;
    }
    
    // Center data
    std::vector<double> X_centered(n_samples * n_features);
    for (int i = 0; i < n_samples; i++) {
        for (int j = 0; j < n_features; j++) {
            X_centered[i * n_features + j] = X[i * n_features + j] - mean_[j];
        }
    }
    
    // Compute SVD
    U_.resize(n_samples * n_components_);
    S_.resize(n_components_);
    Vt_.resize(n_components_ * n_features);
    
    std::vector<double> U_full(n_samples * n_features);
    std::vector<double> S_full(n_features);
    std::vector<double> Vt_full(n_features * n_features);
    
    compute_svd(X_centered.data(), n_samples, n_features, U_full.data(), S_full.data(), Vt_full.data());
    
    // Keep only top components
    for (int i = 0; i < n_components_; i++) {
        S_[i] = S_full[i];
        for (int j = 0; j < n_features; j++) {
            Vt_[i * n_features + j] = Vt_full[i * n_features + j];
        }
    }
}

void SVDCompressor::transform(const double* x, double* z) const {
    // Center input
    std::vector<double> x_centered(n_features_);
    for (int j = 0; j < n_features_; j++) {
        x_centered[j] = x[j] - mean_[j];
    }
    
    // Project: z = x_centered * V * S^{-1}
    for (int i = 0; i < n_components_; i++) {
        double sum = 0.0;
        for (int j = 0; j < n_features_; j++) {
            sum += x_centered[j] * Vt_[i * n_features + j];
        }
        z[i] = (S_[i] > 1e-10) ? sum / S_[i] : 0.0;
    }
}

void SVDCompressor::inverse_transform(const double* z, double* x) const {
    // Reconstruct: x = z * S * V^T + mean
    for (int j = 0; j < n_features_; j++) {
        double sum = 0.0;
        for (int i = 0; i < n_components_; i++) {
            sum += z[i] * S_[i] * Vt_[i * n_features + j];
        }
        x[j] = sum + mean_[j];
    }
}

// ============================================================================
// Random Projector
// ============================================================================

RandomProjector::RandomProjector(int n_components, double epsilon)
    : n_components_(n_components), epsilon_(epsilon) {}

int RandomProjector::compute_optimal_dimensions(int n_samples, double epsilon) {
    // Johnson-Lindenstrauss lemma
    // k >= 8 * ln(n) / epsilon^2
    return static_cast<int>(std::ceil(8.0 * std::log(n_samples) / (epsilon * epsilon)));
}

void RandomProjector::generate_projection_matrix() {
    // Gaussian random projection
    projection_matrix_.resize(n_features_ * n_components_);
    
    // Simple pseudo-random number generator
    uint64_t seed = 42;
    auto next_random = [&seed]() -> double {
        seed = seed * 6364136223846793005ULL + 1442695040888963407ULL;
        return static_cast<double>(seed & 0xFFFFFFFF) / 0xFFFFFFFF;
    };
    
    for (int i = 0; i < n_features_ * n_components_; i++) {
        // Box-Muller transform for Gaussian
        double u1 = next_random();
        double u2 = next_random();
        projection_matrix_[i] = std::sqrt(-2.0 * std::log(u1 + 1e-10)) * std::cos(2.0 * M_PI * u2);
    }
    
    // Normalize columns
    for (int j = 0; j < n_components_; j++) {
        double norm = 0.0;
        for (int i = 0; i < n_features_; i++) {
            norm += projection_matrix_[i * n_components_ + j] * projection_matrix_[i * n_components_ + j];
        }
        norm = std::sqrt(norm);
        for (int i = 0; i < n_features_; i++) {
            projection_matrix_[i * n_components_ + j] /= norm;
        }
    }
}

void RandomProjector::init(int n_features) {
    n_features_ = n_features;
    generate_projection_matrix();
}

void RandomProjector::transform(const double* x, double* z) const {
    // z = x * R
    for (int j = 0; j < n_components_; j++) {
        double sum = 0.0;
        for (int i = 0; i < n_features_; i++) {
            sum += x[i] * projection_matrix_[i * n_components_ + j];
        }
        z[j] = sum;
    }
}

// ============================================================================
// Autoencoder Inference
// ============================================================================

AutoencoderInference::AutoencoderInference(int input_dim, int latent_dim)
    : input_dim_(input_dim), latent_dim_(latent_dim) {
    W_encoder_.resize(latent_dim * input_dim);
    b_encoder_.resize(latent_dim);
    W_decoder_.resize(input_dim * latent_dim);
    b_decoder_.resize(input_dim);
}

void AutoencoderInference::matvec(const double* W, const double* x, double* y, int m, int n) const {
    for (int i = 0; i < m; i++) {
        double sum = 0.0;
        for (int j = 0; j < n; j++) {
            sum += W[i * n + j] * x[j];
        }
        y[i] = sum;
    }
}

void AutoencoderInference::encode(const double* x, double* z) const {
    // z = relu(W_encoder * x + b_encoder)
    std::vector<double> h(latent_dim_);
    matvec(W_encoder_.data(), x, h.data(), latent_dim_, input_dim_);
    
    for (int i = 0; i < latent_dim_; i++) {
        z[i] = relu(h[i] + b_encoder_[i]);
    }
}

void AutoencoderInference::decode(const double* z, double* x) const {
    // x = W_decoder * z + b_decoder
    matvec(W_decoder_.data(), z, x, input_dim_, latent_dim_);
    for (int i = 0; i < input_dim_; i++) {
        x[i] += b_decoder_[i];
    }
}

void AutoencoderInference::load_weights(const char* encoder_path, const char* decoder_path) {
    // Load weights from binary files
    FILE* f;
    
    f = fopen(encoder_path, "rb");
    if (f) {
        fread(W_encoder_.data(), sizeof(double), W_encoder_.size(), f);
        fread(b_encoder_.data(), sizeof(double), b_encoder_.size(), f);
        fclose(f);
    }
    
    f = fopen(decoder_path, "rb");
    if (f) {
        fread(W_decoder_.data(), sizeof(double), W_decoder_.size(), f);
        fread(b_decoder_.data(), sizeof(double), b_decoder_.size(), f);
        fclose(f);
    }
}

}  // namespace compression

// ============================================================================
// C API for Cython binding
// ============================================================================

extern "C" {
    
    void* pca_create(int n_components, double variance_threshold) {
        return new compression::PCACompressor(n_components, variance_threshold);
    }
    
    void pca_fit(void* pca, const double* X, int n_samples, int n_features) {
        static_cast<compression::PCACompressor*>(pca)->fit(X, n_samples, n_features);
    }
    
    void pca_transform(void* pca, const double* x, double* z) {
        static_cast<compression::PCACompressor*>(pca)->transform(x, z);
    }
    
    void pca_inverse_transform(void* pca, const double* z, double* x) {
        static_cast<compression::PCACompressor*>(pca)->inverse_transform(z, x);
    }
    
    int pca_get_n_components(void* pca) {
        return static_cast<compression::PCACompressor*>(pca)->get_n_components();
    }
    
    double pca_get_variance_explained(void* pca) {
        return static_cast<compression::PCACompressor*>(pca)->get_variance_explained();
    }
    
    void pca_destroy(void* pca) {
        delete static_cast<compression::PCACompressor*>(pca);
    }
    
    void* svd_create(int n_components) {
        return new compression::SVDCompressor(n_components);
    }
    
    void svd_fit(void* svd, const double* X, int n_samples, int n_features) {
        static_cast<compression::SVDCompressor*>(svd)->fit(X, n_samples, n_features);
    }
    
    void svd_transform(void* svd, const double* x, double* z) {
        static_cast<compression::SVDCompressor*>(svd)->transform(x, z);
    }
    
    void svd_inverse_transform(void* svd, const double* z, double* x) {
        static_cast<compression::SVDCompressor*>(svd)->inverse_transform(z, x);
    }
    
    void svd_destroy(void* svd) {
        delete static_cast<compression::SVDCompressor*>(svd);
    }
    
    void* random_projector_create(int n_components, double epsilon) {
        return new compression::RandomProjector(n_components, epsilon);
    }
    
    void random_projector_init(void* rp, int n_features) {
        static_cast<compression::RandomProjector*>(rp)->init(n_features);
    }
    
    void random_projector_transform(void* rp, const double* x, double* z) {
        static_cast<compression::RandomProjector*>(rp)->transform(x, z);
    }
    
    void random_projector_destroy(void* rp) {
        delete static_cast<compression::RandomProjector*>(rp);
    }
    
}