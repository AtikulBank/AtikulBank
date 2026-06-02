import numpy as np

def compute_navier_stokes_turbulence(order_flow_velocity, viscosity_theta):
    U = np.array(order_flow_velocity, dtype=np.float64)
    reynolds_state = np.max(np.abs(U)) / (viscosity_theta + 1e-9)
    energy_dissipation = np.sum(U**2) * reynolds_state
    singularity_blowup = True if energy_dissipation > 10**5 else False
    return {
        "reynolds_state": reynolds_state,
        "energy_dissipation": energy_dissipation,
        "singularity_detected": singularity_blowup
    }
