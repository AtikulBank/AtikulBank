# cython: boundscheck=False, wraparound=False, cdivision=True
# cython: language_level=3
# distutils: extra_compile_args = -march=native -O3 -ffast-math
# distutils: extra_link_args = -march=native

"""
LAYER 8: BAYESIAN ENSEMBLE - CYTHON WRAPPER
High-performance Bayesian inference with C++ backend

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
cdef extern from "bayesian_core.h" namespace "bayesian":
    cdef void softmax_neon(const double* logits, double* probs, int n)
    cdef void softmax_scalar(const double* logits, double* probs, int n)
    cdef void log_softmax(const double* logits, double* log_probs, int n)
    cdef void bma_compute(const double* model_probs, const double* model_weights,
                         double* ensemble_probs, int n_models, int n_classes)
    cdef void dirichlet_mean(const double* alpha, double* mean, int n)
    cdef void dirichlet_variance(const double* alpha, double* variance, int n)
    cdef void dirichlet_sample(const double* alpha, double* sample, int n)
    cdef void bayesian_update(const double* prior_alpha, const double* counts,
                             double* posterior_alpha, int n)
    
    cdef cppclass BayesianEnsembleManager:
        BayesianEnsembleManager(int n_ml_models, int n_rl_agents,
                               double ml_weight, double rl_weight)
        void fuse(const double* ml_probs, const double* rl_probs, double* ensemble_probs)
        void update_weights(const double* ml_accuracies, const double* rl_win_rates)
        double compute_uncertainty(const double* probs, int n_classes)
        const double* get_ml_weights()
        const double* get_rl_weights()

# C API declarations
cdef extern from "bayesian_core.cpp":
    void softmax_c(const double* logits, double* probs, int n)
    void log_softmax_c(const double* logits, double* log_probs, int n)
    void bma_compute_c(const double* model_probs, const double* model_weights,
                       double* ensemble_probs, int n_models, int n_classes)
    void dirichlet_mean_c(const double* alpha, double* mean, int n)
    void dirichlet_variance_c(const double* alpha, double* variance, int n)
    void dirichlet_sample_c(const double* alpha, double* sample, int n)
    void bayesian_update_c(const double* prior_alpha, const double* counts,
                           double* posterior_alpha, int n)
    void* bayesian_ensemble_create(int n_ml_models, int n_rl_agents,
                                   double ml_weight, double rl_weight)
    void bayesian_ensemble_fuse(void* manager, const double* ml_probs,
                                const double* rl_probs, double* ensemble_probs)
    void bayesian_ensemble_update_weights(void* manager, const double* ml_accuracies,
                                          const double* rl_win_rates)
    double bayesian_ensemble_compute_uncertainty(void* manager, const double* probs,
                                                 int n_classes)
    void bayesian_ensemble_destroy(void* manager)


def softmax(double[:] logits):
    """Compute softmax with NEON SIMD"""
    cdef int n = len(logits)
    cdef cnp.ndarray[double, ndim=1] probs = np.zeros(n)
    softmax_c(&logits[0], &probs[0], n)
    return probs


def log_softmax(double[:] logits):
    """Compute log-softmax for numerical stability"""
    cdef int n = len(logits)
    cdef cnp.ndarray[double, ndim=1] log_probs = np.zeros(n)
    log_softmax_c(&logits[0], &log_probs[0], n)
    return log_probs


def bma_compute(double[:] model_probs, double[:] model_weights, int n_models, int n_classes=3):
    """Compute Bayesian Model Averaging"""
    cdef cnp.ndarray[double, ndim=1] ensemble_probs = np.zeros(n_classes)
    bma_compute_c(&model_probs[0], &model_weights[0], &ensemble_probs[0], n_models, n_classes)
    return ensemble_probs


def dirichlet_mean(double[:] alpha):
    """Compute Dirichlet mean"""
    cdef int n = len(alpha)
    cdef cnp.ndarray[double, ndim=1] mean = np.zeros(n)
    dirichlet_mean_c(&alpha[0], &mean[0], n)
    return mean


def dirichlet_variance(double[:] alpha):
    """Compute Dirichlet variance"""
    cdef int n = len(alpha)
    cdef cnp.ndarray[double, ndim=1] variance = np.zeros(n)
    dirichlet_variance_c(&alpha[0], &variance[0], n)
    return variance


def dirichlet_sample(double[:] alpha):
    """Sample from Dirichlet distribution"""
    cdef int n = len(alpha)
    cdef cnp.ndarray[double, ndim=1] sample = np.zeros(n)
    dirichlet_sample_c(&alpha[0], &sample[0], n)
    return sample


def bayesian_update(double[:] prior_alpha, double[:] counts):
    """Bayesian updating with Dirichlet prior"""
    cdef int n = len(prior_alpha)
    cdef cnp.ndarray[double, ndim=1] posterior_alpha = np.zeros(n)
    bayesian_update_c(&prior_alpha[0], &counts[0], &posterior_alpha[0], n)
    return posterior_alpha


class BayesianEnsembleManagerCython:
    """
    High-performance Bayesian Ensemble with C++ backend
    
    Features:
    - Bayesian Model Averaging (BMA)
    - Dirichlet Prior/Posterior
    - Uncertainty quantification
    - Model weight updating
    
    AWS C7g Optimized:
    - NEON SIMD for softmax
    - Cache-friendly memory access
    """
    
    def __init__(self, int n_ml_models=30, int n_rl_agents=10,
                 double ml_weight=0.7, double rl_weight=0.3):
        """Initialize Bayesian Ensemble Manager"""
        self._manager = bayesian_ensemble_create(n_ml_models, n_rl_agents,
                                                 ml_weight, rl_weight)
        self._n_ml_models = n_ml_models
        self._n_rl_agents = n_rl_agents
    
    def __dealloc__(self):
        if self._manager != NULL:
            bayesian_ensemble_destroy(self._manager)
    
    def fuse(self, cnp.ndarray[double, ndim=2] ml_probs, cnp.ndarray[double, ndim=2] rl_probs):
        """Fuse ML and RL predictions using BMA"""
        cdef int n_ml = ml_probs.shape[0]
        cdef int n_rl = rl_probs.shape[0]
        cdef int n_classes = ml_probs.shape[1]
        
        cdef cnp.ndarray[double, ndim=1] ensemble_probs = np.zeros(n_classes)
        
        bayesian_ensemble_fuse(self._manager, &ml_probs[0, 0], &rl_probs[0, 0],
                              &ensemble_probs[0])
        
        return ensemble_probs
    
    def update_weights(self, cnp.ndarray[double, ndim=1] ml_accuracies,
                       cnp.ndarray[double, ndim=1] rl_win_rates):
        """Update model weights based on performance"""
        bayesian_ensemble_update_weights(self._manager, &ml_accuracies[0],
                                         &rl_win_rates[0])
    
    def compute_uncertainty(self, cnp.ndarray[double, ndim=1] probs):
        """Compute prediction uncertainty"""
        return bayesian_ensemble_compute_uncertainty(self._manager, &probs[0], len(probs))
    
    def get_ml_weights(self):
        """Get current ML weights"""
        cdef const double* weights = bayesian_ensemble_get_ml_weights(self._manager)
        cdef cnp.ndarray[double, ndim=1] result = np.zeros(self._n_ml_models)
        for i in range(self._n_ml_models):
            result[i] = weights[i]
        return result
    
    def get_rl_weights(self):
        """Get current RL weights"""
        cdef const double* weights = bayesian_ensemble_get_rl_weights(self._manager)
        cdef cnp.ndarray[double, ndim=1] result = np.zeros(self._n_rl_agents)
        for i in range(self._n_rl_agents):
            result[i] = weights[i]
        return result


class BayesianEnsembleCython:
    """
    Complete Bayesian Ensemble with Cython + C++ backend
    
    Features:
    - ML predictions (30 models)
    - RL predictions (10 agents)
    - Bayesian Model Averaging
    - Dirichlet prior/posterior
    - Uncertainty quantification
    
    AWS C7g Optimized:
    - NEON SIMD for softmax
    - Cache-friendly memory access
    - Thread pool for parallelism
    """
    
    def __init__(self,
                 int n_ml_models=30,
                 int n_rl_agents=10,
                 double ml_weight=0.7,
                 double rl_weight=0.3,
                 str backend='cython'):
        """
        Initialize Bayesian Ensemble
        
        Args:
            n_ml_models: Number of ML models
            n_rl_agents: Number of RL agents
            ml_weight: Weight for ML predictions
            rl_weight: Weight for RL predictions
            backend: 'cython' or 'python'
        """
        self._n_ml_models = n_ml_models
        self._n_rl_agents = n_rl_agents
        self._ml_weight = ml_weight
        self._rl_weight = rl_weight
        self._backend = backend
        
        if backend == 'cython':
            self._manager = BayesianEnsembleManagerCython(
                n_ml_models, n_rl_agents, ml_weight, rl_weight
            )
        
        # Model weights
        self._ml_weights = np.ones(n_ml_models) / n_ml_models
        self._rl_weights = np.ones(n_rl_agents) / n_rl_agents
        
        # Statistics
        self._fusion_count = 0
        self._total_uncertainty = 0.0
    
    def fuse(self, cnp.ndarray[double, ndim=2] ml_probs,
             cnp.ndarray[double, ndim=2] rl_probs):
        """
        Fuse ML and RL predictions
        
        Args:
            ml_probs: ML probability matrix (n_models, n_classes)
            rl_probs: RL probability matrix (n_agents, n_classes)
        
        Returns:
            Fused probabilities
        """
        if self._backend == 'cython':
            ensemble_probs = self._manager.fuse(ml_probs, rl_probs)
        else:
            # Python fallback: weighted average
            ml_weighted = np.average(ml_probs, axis=0, weights=self._ml_weights)
            rl_weighted = np.average(rl_probs, axis=0, weights=self._rl_weights)
            
            ml_w = self._ml_weight / (self._ml_weight + self._rl_weight)
            rl_w = self._rl_weight / (self._ml_weight + self._rl_weight)
            
            ensemble_probs = ml_w * ml_weighted + rl_w * rl_weighted
            
            # Apply softmax
            ensemble_probs = self._softmax(ensemble_probs / 1.0)
        
        # Compute uncertainty
        uncertainty = self.compute_uncertainty(ensemble_probs)
        self._fusion_count += 1
        self._total_uncertainty += uncertainty
        
        # Get final signal
        final_signal = int(np.argmax(ensemble_probs) - 1)  # -1, 0, 1
        final_confidence = float(np.max(ensemble_probs))
        
        return {
            'ensemble_probs': ensemble_probs.tolist(),
            'final_signal': final_signal,
            'final_confidence': final_confidence,
            'uncertainty': float(uncertainty),
            'ml_contribution': float(self._ml_weight * np.max(ml_probs)),
            'rl_contribution': float(self._rl_weight * np.max(rl_probs))
        }
    
    def update_weights(self, cnp.ndarray[double, ndim=1] ml_accuracies,
                       cnp.ndarray[double, ndim=1] rl_win_rates):
        """Update model weights based on performance"""
        if self._backend == 'cython':
            self._manager.update_weights(ml_accuracies, rl_win_rates)
            self._ml_weights = self._manager.get_ml_weights()
            self._rl_weights = self._manager.get_rl_weights()
        else:
            # Python fallback: softmax
            self._ml_weights = self._softmax(ml_accuracies / 1.0)
            self._rl_weights = self._softmax(rl_win_rates / 1.0)
    
    def compute_uncertainty(self, cnp.ndarray[double, ndim=1] probs):
        """Compute prediction uncertainty"""
        if self._backend == 'cython':
            return self._manager.compute_uncertainty(probs)
        else:
            # Python fallback: entropy
            entropy = -np.sum(probs * np.log(probs + 1e-10))
            max_entropy = np.log(len(probs))
            return entropy / max_entropy
    
    def _softmax(self, x):
        """Softmax with numerical stability"""
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum()
    
    def get_statistics(self):
        """Get ensemble statistics"""
        avg_uncertainty = self._total_uncertainty / self._fusion_count if self._fusion_count > 0 else 0.0
        
        return {
            'n_ml_models': self._n_ml_models,
            'n_rl_agents': self._n_rl_agents,
            'ml_weight': self._ml_weight,
            'rl_weight': self._rl_weight,
            'fusion_count': self._fusion_count,
            'avg_uncertainty': avg_uncertainty,
            'backend': self._backend
        }