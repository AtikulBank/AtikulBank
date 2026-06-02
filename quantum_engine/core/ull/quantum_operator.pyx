# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True

import numpy as np
cimport numpy as cnp

cpdef double calculate_quantum_uncertainty_limit(cnp.float64_t[:] price_ticks, double reynolds_factor):
    cdef int i
    cdef int length = price_ticks.shape[0]
    cdef double quantum_friction = 0.0
    cdef double delta = 0.0
    
    for i in range(1, length):
        delta = price_ticks[i] - price_ticks[i-1]
        quantum_friction += (delta * reynolds_factor) / (2.718281828459 + abs(delta))
    return quantum_friction
