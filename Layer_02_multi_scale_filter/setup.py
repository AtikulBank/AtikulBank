"""
Setup script for building Cython extensions for Layer 2
"""

from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np

# Define C++ extension
extensions = [
    Extension(
        "filter_wrapper",
        sources=[
            "cython/filter_wrapper.pyx",
            "cpp/kalman_filters.cpp"
        ],
        include_dirs=[
            np.get_include(),
            "cpp"
        ],
        language="c++",
        extra_compile_args=[
            "-O3",                    # Maximum optimization
            "-march=native",          # Optimize for current CPU
            "-mtune=native",          # Tune for current CPU
            "-ffast-math",            # Fast math operations
            "-funroll-loops",         # Unroll loops
            "-finline-functions",     # Inline functions
            "-DNDEBUG",               # Disable debug assertions
            "-std=c++17",             # C++17 standard
            "-fopenmp"                # OpenMP for parallel processing
        ],
        extra_link_args=[
            "-O3",
            "-fopenmp"
        ],
        define_macros=[
            ("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")
        ]
    )
]

setup(
    name="filter_wrapper",
    version="1.0.0",
    description="Ultra-high performance multi-scale filter engine",
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            'language_level': 3,
            'boundscheck': False,
            'wraparound': False,
            'cdivision': True,
            'initializedcheck': False,
            'nonecheck': False,
            'overflowcheck': False,
            'embedsignature': True,
            'cdivision_warnings': False,
            'annotation_typing': False,
            'autotestdict': False
        }
    ),
    include_dirs=[np.get_include()],
    python_requires=">=3.7",
    install_requires=[
        "numpy>=1.20.0",
        "Cython>=0.29.0"
    ]
)