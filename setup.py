"""
Quantum Trading Machine - Build Script
Compiles all Cython extensions for maximum performance
"""

from setuptools import setup, Extension
from Cython.Build import cythonize

# Compiler directives for maximum performance
compiler_directives = {
    'language_level': 3,
    'boundscheck': False,

    'cdivision': True,
    'nonecheck': False,
    'overflowcheck': False,
    'initializedcheck': False,
}

# Define Cython extensions
extensions = [
    # Quantum Brain


    # FIX Pipeline
    Extension(
        "fix_pipeline.network_layer",
        sources=["fix_pipeline/network_layer.pyx"],
        extra_compile_args=["-O3", "-march=native", "-mtune=native"],
    ),
    Extension(
        "fix_pipeline.order_encoder",
        sources=["fix_pipeline/order_encoder.pyx"],
        extra_compile_args=["-O3", "-march=native", "-mtune=native"],
    ),
    Extension(
        "fix_pipeline.fix_decoder",
        sources=["fix_pipeline/fix_decoder.pyx"],
        extra_compile_args=["-O3", "-march=native", "-mtune=native"],
    ),
]

# Setup configuration
setup(
    name="quantum-trading-machine",
    version="2.0.0",
    author="Quantum HFT Engine",
    description="Institutional Quantum Trading Engine - Pure Cython + Raw C-Sockets",
    long_description=open("README.md").read() if __name__ == "__main__" else "",
    long_description_content_type="text/markdown",
    packages=["quantum_brain", "fix_pipeline"],
    package_dir={"quantum_brain": "quantum_brain", "fix_pipeline": "fix_pipeline"},
    ext_modules=cythonize(
        extensions,
        compiler_directives=compiler_directives,
        annotate=False,
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
