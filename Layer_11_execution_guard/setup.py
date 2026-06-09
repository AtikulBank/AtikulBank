"""
Build system for Layer 11 Execution Guard Cython extension.
Compiles C++ core with Cython wrapper for ultra-low-latency execution checks.
"""
from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np

extensions = [
    Extension(
        "Layer_11_execution_guard.cython.execution_wrapper",
        ["Layer_11_execution_guard/cython/execution_wrapper.pyx"],
        include_dirs=[
            np.get_include(),
            "Layer_11_execution_guard/cpp",
        ],
        language="c++",
        extra_compile_args=[
            "-O3",
            "-march=native",
            "-mtune=native",
            "-ffast-math",
            "-std=c++17",
            "-DNPY_NO_DEPRECATED_API=NPY_1_7_API_VERSION",
        ],
        extra_link_args=[
            "-std=c++17",
        ],
    ),
]

setup(
    name="layer11-execution-guard",
    version="1.0.0",
    description="Layer 11: Ultra-low-latency Execution Guard with C++ core",
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            "language_level": 3,
            "boundscheck": False,
            "wraparound": False,
            "cdivision": True,
            "initializedcheck": False,
            "nonecheck": False,
            "overflowcheck": False,
        },
    ),
    include_dirs=[np.get_include()],
)
