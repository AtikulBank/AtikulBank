"""
Setup script for cTrader HFT Engine
Compiles Cython extensions for ultra-low-latency performance
"""

from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np

# Compiler directives for maximum performance
compiler_directives = {
    'language_level': 3,
    'boundscheck': False,
    'wraparound': False,
    'cdivision': True,
    'nonecheck': False,
    'overflowcheck': False,
    'initializedcheck': False,
}

# Define Cython extensions
extensions = [
    Extension(
        name="ctrader_hft_engine.core.network.hft_socket",
        sources=["ctrader_hft_engine/core/network/hft_socket.pyx"],
        include_dirs=[np.get_include()],
        extra_compile_args=["-O3", "-march=native", "-mtune=native"],
        extra_link_args=["-O3"],
    ),
    Extension(
        name="ctrader_hft_engine.core.fix.fix_encoder",
        sources=["ctrader_hft_engine/core/fix/fix_encoder.pyx"],
        include_dirs=[np.get_include()],
        extra_compile_args=["-O3", "-march=native", "-mtune=native"],
        extra_link_args=["-O3"],
    ),
    Extension(
        name="ctrader_hft_engine.core.fix.fix_decoder",
        sources=["ctrader_hft_engine/core/fix/fix_decoder.pyx"],
        include_dirs=[np.get_include()],
        extra_compile_args=["-O3", "-march=native", "-mtune=native"],
        extra_link_args=["-O3"],
    ),
]

setup(
    name="ctrader_hft_engine",
    version="1.0.0",
    description="Ultra-Low-Latency Cython HFT Engine for cTrader FIX API",
    long_description=open("README.md").read() if __file__ else "",
    long_description_content_type="text/markdown",
    author="HFT Architecture Team",
    packages=[
        "ctrader_hft_engine",
        "ctrader_hft_engine.core",
        "ctrader_hft_engine.core.network",
        "ctrader_hft_engine.core.fix",
        "ctrader_hft_engine.utils",
        "ctrader_hft_engine.config",
    ],
    ext_modules=cythonize(
        extensions,
        compiler_directives=compiler_directives,
        nthreads=4,
    ),
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.21.0",
        "cython>=0.29.0",
    ],
    zip_safe=False,
)