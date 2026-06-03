"""
cTrader FIX 4.4 Engine - Build Script
Compiles Cython extensions for maximum performance
"""

from setuptools import setup, Extension
from Cython.Build import cythonize

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
        "ctrader_fix_engine.network.socket",
        sources=["ctrader_fix_engine/network/socket.pyx"],
        extra_compile_args=["-O3", "-march=native", "-mtune=native"],
    ),
    Extension(
        "ctrader_fix_engine.protocol.encoder",
        sources=["ctrader_fix_engine/protocol/encoder.pyx"],
        extra_compile_args=["-O3", "-march=native", "-mtune=native"],
    ),
    Extension(
        "ctrader_fix_engine.protocol.decoder",
        sources=["ctrader_fix_engine/protocol/decoder.pyx"],
        extra_compile_args=["-O3", "-march=native", "-mtune=native"],
    ),
]

# Setup configuration
setup(
    name="ctrader-fix-engine",
    version="1.0.0",
    author="cTrader HFT Engine",
    description="cTrader FIX 4.4 High-Frequency Trading Engine",
    long_description=open("README.md").read() if __name__ == "__main__" else "",
    long_description_content_type="text/markdown",
    packages=["ctrader_fix_engine"],
    package_dir={"ctrader_fix_engine": "ctrader_fix_engine"},
    ext_modules=cythonize(
        extensions,
        compiler_directives=compiler_directives,
        annotate=False,  # Set to True to generate HTML annotation
    ),
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Cython",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
)