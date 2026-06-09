"""
Build system for Layer 11 Execution Guard with Quantum modules.
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
    version="2.0.0",
    description="Layer 11: Ultra-low-latency Execution Guard with Quantum modules",
    author="AtikulBank",
    author_email="dev@atikulbank.com",
    url="https://github.com/AtikulBank/AtikulBank",
    packages=[
        "Layer_11_execution_guard",
        "Layer_11_execution_guard.quantum",
    ],
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
    install_requires=[
        "numpy>=1.21.0",
        "scipy>=1.7.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
