from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np

extensions = [
    Extension("quantum_manifolds", ["../../super_intelligence/quantum_manifolds.pyx"]),
    Extension("fix_protocol", ["fix_protocol.pyx"])
]

setup(
    name="QuantumFIXEngine",
    ext_modules=cythonize(extensions, compiler_directives={'language_level': "3"}),
    include_dirs=[np.get_include()]
)
