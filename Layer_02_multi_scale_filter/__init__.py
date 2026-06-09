"""
LAYER 2: MULTI-SCALE FILTER
Ensemble Kalman (50), Particle Filter (1000), Unscented KF, Extended KF,
Adaptive KF, Wavelet Denoising, EMD (3 IMFs), Savitzky-Golay
"""

from .multi_scale_filter import MultiScaleFilter

__all__ = ["MultiScaleFilter"]