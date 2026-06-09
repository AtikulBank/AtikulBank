"""
Build system for Cython extensions and C++ components.
Compiles:
  - fix_pipeline/fix_decoder.pyx → fix_decoder.so
  - fix_pipeline/network_layer.pyx → network_layer.so
  - csrc/latency_monitor.cpp → latency_monitor.so
"""
from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np

# Cython extensions
cython_extensions = [
    Extension(
        "fix_pipeline.fix_decoder",
        ["fix_pipeline/fix_decoder.pyx"],
        include_dirs=[np.get_include()],
        extra_compile_args=["-O3", "-march=native", "-mtune=native"],
        language="c",
    ),
    Extension(
        "fix_pipeline.network_layer",
        ["fix_pipeline/network_layer.pyx"],
        include_dirs=[np.get_include()],
        extra_compile_args=["-O3", "-march=native", "-mtune=native"],
        language="c",
    ),
]

setup(
    name="atikulbank-pipeline",
    version="1.0.0",
    description="World #1 Master Pipeline - Renaissance + Citadel + Two Sigma + DE Shaw Hybrid",
    author="AtikulBank",
    python_requires=">=3.9",
    ext_modules=cythonize(
        cython_extensions,
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
    install_requires=[
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "scipy>=1.11.0",
        "scikit-learn>=1.3.0",
        "xgboost>=2.0.0",
        "lightgbm>=4.0.0",
        "catboost>=1.2",
        "torch>=2.0.0",
        "rich>=13.0.0",
    ],
    extras_require={
        "dev": ["pytest", "pytest-asyncio", "mypy"],
    },
)
