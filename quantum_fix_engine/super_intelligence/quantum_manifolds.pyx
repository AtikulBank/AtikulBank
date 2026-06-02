# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True

import numpy as np
cimport numpy as cnp
from libc.math cimport log, exp, pow, sin

cdef class QuantumManifoldEngine:
    cdef double current_theta
    cdef int core_primes[4]

    def __cinit__(self):
        self.current_theta = 0.00137035999
        self.core_primes[0] = 2
        self.core_primes[1] = 3

    cdef int _compute_padic_valuation(self, long long volume, int p) noexcept nogil:
        if volume == 0: return 0
        cdef int valuation = 0
        cdef long long absolute_vol = abs(volume)
        while absolute_vol % p == 0:
            valuation += 1
            absolute_vol //= p
        return valuation

    cpdef dict evaluate_padic_spacetime_slice(self, cnp.float64_t[:] order_book_volumes):
        cdef int i, j, p, val
        cdef int size = order_book_volumes.shape[0]
        cdef double norm_sum
        result_matrix = {}
        
        for i in range(2):
            p = self.core_primes[i]
            norm_sum = 0.0
            for j in range(size):
                val = self._compute_and_get_val(<long long>order_book_volumes[j], p)
                norm_sum += pow(<double>p, -<double>val) if val > 0 else 1.0
            result_matrix[f"p_{p}"] = norm_sum / <double>size
        return result_matrix

    cdef int _compute_and_get_val(self, long long vol, int p) noexcept nogil:
        return self._compute_padic_valuation(vol, p)

    cpdef double calculate_iutt_deformation(self, cnp.float64_t[:] ticks, cnp.float64_t[:] pools):
        cdef int i
        cdef int min_size = ticks.shape[0] if ticks.shape[0] < pools.shape[0] else pools.shape[0]
        cdef double cross_entropy = 0.0
        for i in range(min_size):
            cross_entropy += (ticks[i] - pools[i]) * self.current_theta
        return sin(cross_entropy)
