"""
LAYER 8: BAYESIAN ENSEMBLE - BUILD SETUP
Cython + C++ compilation for AWS C7g optimization
"""

from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np

# AWS C7g (Graviton3) compiler flags
# ARM64 architecture with NEON SIMD support
AWS_C7G_FLAGS = [
    '-march=native',           # Optimize for current CPU
    '-O3',                     # Maximum optimization
    '-ffast-math',             # Fast math operations
    '-funroll-loops',          # Loop unrolling
    '-fvectorize',             # Auto-vectorization
    '-DARM_NEON',              # Enable NEON SIMD
    '-pthread',                # Threading support
]

# Fallback for non-ARM systems
X86_FLAGS = [
    '-march=native',
    '-O3',
    '-ffast-math',
    '-funroll-loops',
    '-mavx2',                  # AVX2 SIMD (x86)
    '-mfma',                   # FMA instructions
    '-pthread',
]

# Determine platform-specific flags
import platform
if platform.machine() == 'aarch64':
    COMPILER_FLAGS = AWS_C7G_FLAGS
else:
    COMPILER_FLAGS = X86_FLAGS

# Define Cython extension
ext_modules = [
    Extension(
        name="bayesian_wrapper",
        sources=[
            "cython/bayesian_wrapper.pyx",
            "cpp/bayesian_core.cpp",
        ],
        include_dirs=[
            np.get_include(),
            "cpp/",
        ],
        language="c++",
        extra_compile_args=COMPILER_FLAGS + [
            '-std=c++17',
        ],
        extra_link_args=[
            '-pthread',
        ],
        define_macros=[
            ("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION"),
        ],
    )
]

setup(
    name="bayesian_ensemble",
    version="1.0.0",
    description="High-performance Bayesian ensemble with C++ backend",
    long_description=open("README.md").read() if __import__("os").path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    author="AtikulBank",
    author_email="dev@atikulbank.com",
    url="https://github.com/atikulbank/trading-bot",
    packages=["cython"],
    ext_modules=cythonize(
        ext_modules,
        compiler_directives={
            'language_level': 3,
            'boundscheck': False,
            'wraparound': False,
            'cdivision': True,
            'nonecheck': False,
            'initializedcheck': False,
        }
    ),
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20",
        "cython>=0.29",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Cython",
        "Programming Language :: C++",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
)