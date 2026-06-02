# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True

import numpy as np
cimport numpy as cnp
from libc.math cimport log, exp, pow, sqrt, sin, cos

cdef class QuantumManifoldEngine:
    cdef double current_theta
    cdef int core_primes[4]

    def __cinit__(self):
        self.current_theta = 0.00137035999
        self.core_primes[0] = 2
        self.core_primes[1] = 3
        self.core_primes[2] = 5
        self.core_primes[3] = 7

    cdef int _compute_padic_valuation(self, long long volume, int p) noexcept nogil:
        if volume == 0: return 0
        cdef int valuation = 0
        cdef long long absolute_vol = abs(volume)
        while absolute_vol % p == 0:
            valuation += 1
            absolute_vol //= p
        return valuation

    cdef double _compute_padic_norm(self, int valuation, int p) noexcept nogil:
        if valuation == 0: return 1.0
        return pow(<double>p, -<double>valuation)

    cpdef dict evaluate_padic_spacetime_slice(self, cnp.float64_t[:] order_book_volumes):
        cdef int i, j, p, val
        cdef int size = order_book_volumes.shape[0]
        cdef long long raw_vol
        cdef double norm_sum
        result_matrix = {}
        
        for i in range(4):
            p = self.core_primes[i]
            norm_sum = 0.0
            for j in range(size):
                raw_vol = <long long>order_book_volumes[j]
                val = self._compute_padic_valuation(raw_vol, p)
                norm_sum += self._compute_padic_norm(val, p)
            result_matrix[f"p_{p}"] = norm_sum / <double>size
        return result_matrix

    cpdef double calculate_iutt_deformation(self, cnp.float64_t[:] universe_a_ticks, cnp.float64_t[:] universe_b_pools):
        cdef int i
        cdef int size_a = universe_a_ticks.shape[0]
        cdef int size_b = universe_b_pools.shape[0]
        cdef int min_size = size_a if size_a < size_b else size_b
        cdef double log_sum_a = 0.0
        cdef double log_sum_b = 0.0
        cdef double cross_entropy = 0.0

        for i in range(min_size):
            if universe_a_ticks[i] > 0.0 and universe_b_pools[i] > 0.0:
                log_sum_a += log(universe_a_ticks[i])
                log_sum_b += log(universe_b_pools[i])
                cross_entropy += (universe_a_ticks[i] - universe_b_pools[i]) * self.current_theta
        return exp((log_sum_a / min_size) - (log_sum_b / min_size)) + sin(cross_entropy) if min_size > 0 else 0.0
