"""
LAYER 10: RISK ENGINE - BUILD SETUP
Cython + C++ compilation for AWS C7g optimization
"""

from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np

# AWS C7g (Graviton3) compiler flags
AWS_C7G_FLAGS = [
    '-march=native',
    '-O3',
    '-ffast-math',
    '-funroll-loops',
    '-fvectorize',
    '-DARM_NEON',
    '-pthread',
]

# Fallback for non-ARM systems
X86_FLAGS = [
    '-march=native',
    '-O3',
    '-ffast-math',
    '-funroll-loops',
    '-mavx2',
    '-mfma',
    '-pthread',
]

import platform
if platform.machine() == 'aarch64':
    COMPILER_FLAGS = AWS_C7G_FLAGS
else:
    COMPILER_FLAGS = X86_FLAGS

ext_modules = [
    Extension(
        name="risk_wrapper",
        sources=[
            "cython/risk_wrapper.pyx",
            "cpp/risk_core.cpp",
        ],
        include_dirs=[np.get_include(), "cpp/"],
        language="c++",
        extra_compile_args=COMPILER_FLAGS + ['-std=c++17'],
        extra_link_args=['-pthread'],
        define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
    )
]

setup(
    name="risk_engine",
    version="1.0.0",
    description="High-performance risk engine with C++ backend",
    author="AtikulBank",
    author_email="dev@atikulbank.com",
    packages=["cython"],
    ext_modules=cythonize(
        ext_modules,
        compiler_directives={
            'language_level': 3,
            'boundscheck': False,
            'wraparound': False,
            'cdivision': True,
        }
    ),
    python_requires=">=3.8",
    install_requires=["numpy>=1.20", "cython>=0.29"],
)