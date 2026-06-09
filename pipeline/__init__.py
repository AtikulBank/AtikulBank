"""
WORLD #1 MASTER PIPELINE
Renaissance + Citadel + Two Sigma + DE Shaw HYBRID

Layer 0:  Hardware Guard        - Latency, CPU affinity, memory pool
Layer 1:  Signal Integrity      - Tick auth, monotonicity, sanity
Layer 2:  Multi-Scale Filter    - Ensemble KF, Particle Filter, UKF, EKF
Layer 3:  168-Filter Engine     - Chaos, Quantum, Thermo, Topology, Fluid, Tensor, Ito, Riemann, Feynman, Info, Spectral, Wavelet
Layer 4:  Manipulation Shield   - VPIN, stop-hunt, fake breakout
Layer 5:  Dimensional Compress  - PCA + Autoencoder
Layer 6:  ML Inference (30)     - RF, ET, LR, XGB, LGB, CAT, LSTM, Transformer, TCN, NBeats, TFT, Mamba, etc.
Layer 7:  10 RL Agents          - TrendMaster, ReversalSnipe, BreakoutHunt, Scalper, MacroGuard, ChaosFilter, TopoAgent, FluidAgent, QuantumAgent, EntropyAgent
Layer 8:  Bayesian Fusion       - BMA posterior, dynamic ensemble
Layer 9:  7-Gate Wall           - Confidence gates pass/fail
Layer 10: Adaptive Risk         - Kelly fraction, ATR, hard limits
Layer 11: Execution Guard       - Session, spread, NFP/FOMC
Layer 12: FIX Execution         - NewOrderSingle, OCA
Layer 13: Position Lifecycle    - TP→SL move, emergency close
Layer 14: Self-Learning         - River, ADWIN, batch retrain
Layer 15: Async Master Loop     - Async chain L0→L14
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple

# ── Layer Data Contracts ──────────────────────────────────────────────

@dataclass
class TickData:
    """Raw tick from cTrader FIX stream."""
    symbol: str = ""
    bid: float = 0.0
    ask: float = 0.0
    bid_size: float = 0.0
    ask_size: float = 0.0
    last_price: float = 0.0
    last_size: float = 0.0
    timestamp_ns: int = 0           # nanosecond epoch
    exchange_ts: str = ""
    msg_seq_num: int = 0


@dataclass
class ValidatedTick:
    """After Layer 1 signal integrity."""
    tick: TickData = field(default_factory=TickData)
    is_valid: bool = True
    rejection_reason: str = ""
    latency_ns: int = 0
    monotonic_ok: bool = True
    spread_bps: float = 0.0


@dataclass
class FilteredSignals:
    """After Layer 2 multi-scale filtering."""
    raw_price: float = 0.0
    kalman_ensemble: float = 0.0
    particle_mean: float = 0.0
    ukf_estimate: float = 0.0
    ekf_estimate: float = 0.0
    adaptive_kf: float = 0.0
    wavelet_denoised: float = 0.0
    emd_imfs: List[float] = field(default_factory=list)
    savgol_smoothed: float = 0.0
    ensemble_mean: float = 0.0


@dataclass
class FilterVector168:
    """After Layer 3: 168-filter parallel engine output."""
    # CHAOS(5)
    lyapunov: float = 0.0
    correlation_dim: float = 0.0
    kolmogorov_entropy: float = 0.0
    attractor_dim: float = 0.0
    lorenz_fit: float = 0.0
    # QUANTUM(5)
    qaoa_energy: float = 0.0
    vqe_optimum: float = 0.0
    amplitude_estimate: float = 0.0
    q_annealing_min: float = 0.0
    quantum_walk_dist: float = 0.0
    # THERMO(5)
    boltzmann_factor: float = 0.0
    entropy_transfer: float = 0.0
    mutual_information: float = 0.0
    free_energy: float = 0.0
    entropy_rate: float = 0.0
    # TOPOLOGY(5)
    persistent_h0: float = 0.0
    persistent_h1: float = 0.0
    betti_0: float = 0.0
    betti_1: float = 0.0
    wasserstein_dist: float = 0.0
    # FLUID(5)
    reynolds_number: float = 0.0
    vorticity: float = 0.0
    turbulence_intensity: float = 0.0
    bernoulli_pressure: float = 0.0
    cavitation_index: float = 0.0
    # TENSOR(5)
    stress_tensor: float = 0.0
    riemann_curvature: float = 0.0
    einstein_tensor: float = 0.0
    christoffel_symbol: float = 0.0
    geodesic_deviation: float = 0.0
    # ITO(5)
    ito_integral: float = 0.0
    quadratic_variation: float = 0.0
    malliavin_derivative: float = 0.0
    rough_hurst: float = 0.0
    jump_lambda: float = 0.0
    # RIEMANN(4)
    metric_determinant: float = 0.0
    geodesic_bulge: float = 0.0
    geodesic_bearing: float = 0.0
    ricci_scalar: float = 0.0
    # FEYNMAN(3)
    path_integral: float = 0.0
    optimal_path: float = 0.0
    path_variation: float = 0.0
    # INFO(5)
    shannon_entropy: float = 0.0
    kolmogorov_complexity: float = 0.0
    fisher_information: float = 0.0
    kl_divergence: float = 0.0
    algorithmic_mutual_info: float = 0.0
    # SPECTRAL(12)
    fft_dominant_freq: float = 0.0
    fft_spectral_centroid: float = 0.0
    fft_spectral_rolloff: float = 0.0
    fft_spectral_flatness: float = 0.0
    mesa_energy: float = 0.0
    hilbert_instantaneous_freq: float = 0.0
    hilbert_envelope: float = 0.0
    coherence_xy: float = 0.0
    coherence_slope: float = 0.0
    coherence_peak: float = 0.0
    spectral_entropy: float = 0.0
    spectral_contrast: float = 0.0
    # WAVELET(10)
    cwt_scale: float = 0.0
    cwt_energy: float = 0.0
    dwt_approx: float = 0.0
    dwt_detail: float = 0.0
    wavelet_entropy: float = 0.0
    wavelet_regularity: float = 0.0
    wavelet_leader: float = 0.0
    wtmm_max: float = 0.0
    wtmm_mean: float = 0.0
    wavelet_hurst: float = 0.0
    # PRICE_ACTION(5)
    candle_pattern: float = 0.0
    engulfing_signal: float = 0.0
    doji_signal: float = 0.0
    pin_bar: float = 0.0
    inside_bar: float = 0.0
    # MOMENTUM(12)
    rsi_14: float = 0.0
    macd_hist: float = 0.0
    stochastic_k: float = 0.0
    stochastic_d: float = 0.0
    cci_20: float = 0.0
    williams_r: float = 0.0
    roc_10: float = 0.0
    momentum_10: float = 0.0
    tsi: float = 0.0
    ultimate_osc: float = 0.0
    awesome_osc: float = 0.0
    trix: float = 0.0
    # VOLATILITY(13)
    atr_14: float = 0.0
    bollinger_upper: float = 0.0
    bollinger_lower: float = 0.0
    bollinger_width: float = 0.0
    historical_vol: float = 0.0
    garman_klass: float = 0.0
    parkinson: float = 0.0
    yang_zhang: float = 0.0
    keltner_upper: float = 0.0
    keltner_lower: float = 0.0
    donchian_upper: float = 0.0
    donchian_lower: float = 0.0
    choppiness: float = 0.0
    # STATISTICAL(9)
    skewness: float = 0.0
    kurtosis: float = 0.0
    jarque_bera: float = 0.0
    adf_statistic: float = 0.0
    hurst_exponent: float = 0.0
    autocorrelation_1: float = 0.0
    autocorrelation_5: float = 0.0
    heteroskedasticity: float = 0.0
    variance_ratio: float = 0.0
    # TIMESERIES(7)
    arima_forecast: float = 0.0
    var_forecast: float = 0.0
    cointegration: float = 0.0
    regime_state: float = 0.0
    trend_strength: float = 0.0
    seasonality: float = 0.0
    cycle_period: float = 0.0
    # ORDERBOOK(6)
    bid_ask_imbalance: float = 0.0
    depth_imbalance: float = 0.0
    order_flow_toxicity: float = 0.0
    cumulative_delta: float = 0.0
    large_order_ratio: float = 0.0
    book_pressure: float = 0.0
    # RISK(7)
    var_95: float = 0.0
    cvar_95: float = 0.0
    max_drawdown: float = 0.0
    tail_ratio: float = 0.0
    downside_vol: float = 0.0
    omega_ratio: float = 0.0
    sortino_ratio: float = 0.0
    # COPULA(7)
    gaussian_copula: float = 0.0
    Clayton_copula: float = 0.0
    Gumbel_copula: float = 0.0
    Frank_copula: float = 0.0
    tail_dependence_lower: float = 0.0
    tail_dependence_upper: float = 0.0
    copula_tau: float = 0.0
    # HMM(6)
    hmm_state: float = 0.0
    hmm_transition_prob: float = 0.0
    hmm_emission_prob: float = 0.0
    viterbi_path: float = 0.0
    baum_welch_likelihood: float = 0.0
    regime_confidence: float = 0.0
    # KALMAN_ADV(8)
    kalman_state: float = 0.0
    kalman_innovation: float = 0.0
    kalman_gain: float = 0.0
    kalman_residual: float = 0.0
    kalman_covariance: float = 0.0
    kalman_prediction_error: float = 0.0
    kalman_smoothing: float = 0.0
    kalman_filtered_trend: float = 0.0
    # VELOCITY(12)
    price_velocity: float = 0.0
    price_acceleration: float = 0.0
    price_jerk: float = 0.0
    bid_velocity: float = 0.0
    ask_velocity: float = 0.0
    spread_velocity: float = 0.0
    volume_velocity: float = 0.0
    momentum_velocity: float = 0.0
    kinetic_energy: float = 0.0
    directional_energy: float = 0.0
    reversal_velocity: float = 0.0
    velocity_sma_ratio: float = 0.0

    def to_array(self) -> list:
        """Convert all 168 filters to a flat list."""
        return [v for k, v in self.__dict__.items() if isinstance(v, (int, float))]

    @property
    def count(self) -> int:
        return sum(1 for v in self.__dict__.values() if isinstance(v, (int, float)))


class SignalDirection(Enum):
    BUY = auto()
    SELL = auto()
    HOLD = auto()


@dataclass
class ManipulationVerdict:
    """After Layer 4: manipulation shield."""
    is_manipulated: bool = False
    isolation_score: float = 0.0
    vpin: float = 0.0
    lee_ready_direction: int = 0
    stop_hunt_detected: bool = False
    fake_breakout: bool = False
    spread_manipulation: bool = False
    reason: str = ""


@dataclass
class CompressedVector:
    """After Layer 5: PCA + autoencoder compression."""
    pca_components: List[float] = field(default_factory=list)
    autoencoder_bottleneck: List[float] = field(default_factory=list)
    n_components: int = 0
    variance_explained: float = 0.0


@dataclass
class MLPrediction:
    """Single model prediction."""
    model_name: str = ""
    buy_prob: float = 0.0
    sell_prob: float = 0.0
    hold_prob: float = 0.0
    confidence: float = 0.0


@dataclass
class MLPredictionMatrix:
    """After Layer 6: 30-model inference."""
    predictions: List[MLPrediction] = field(default_factory=list)
    ensemble_buy: float = 0.0
    ensemble_sell: float = 0.0
    ensemble_hold: float = 0.0


@dataclass
class RLAgentVote:
    """Single RL agent vote."""
    agent_name: str = ""
    action: SignalDirection = SignalDirection.HOLD
    confidence: float = 0.0


@dataclass
class RLEnsemble:
    """After Layer 7: 10 RL agents."""
    votes: List[RLAgentVote] = field(default_factory=list)
    consensus: SignalDirection = SignalDirection.HOLD
    consensus_confidence: float = 0.0


@dataclass
class BayesianFusion:
    """After Layer 8: Bayesian ensemble fusion."""
    final_signal: SignalDirection = SignalDirection.HOLD
    final_confidence: float = 0.0
    buy_score: float = 0.0
    sell_score: float = 0.0
    hold_score: float = 0.0
    ml_weight: float = 0.0
    rl_weight: float = 0.0
    disagreement_entropy: float = 0.0
    ci_p10: float = 0.0
    ci_p90: float = 0.0


@dataclass
class GateResult:
    """Single gate pass/fail."""
    gate_id: int = 0
    name: str = ""
    value: float = 0.0
    threshold: float = 0.0
    passed: bool = False


@dataclass
class ConfidenceWall:
    """After Layer 9: 7-gate confidence wall."""
    gates: List[GateResult] = field(default_factory=list)
    all_passed: bool = False
    failed_gates: List[str] = field(default_factory=list)


@dataclass
class RiskParameters:
    """After Layer 10: adaptive risk engine."""
    kelly_fraction: float = 0.0
    atr_proxy: float = 0.0
    vol_regime: float = 0.0
    position_size: float = 0.0
    stop_loss: float = 0.0
    take_profit_1: float = 0.0
    take_profit_2: float = 0.0
    take_profit_3: float = 0.0
    risk_reward_ratio: float = 0.0
    max_concurrent: int = 3
    daily_loss_pct: float = 0.0
    weekly_loss_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    halt_triggered: bool = False
    halt_reason: str = ""


@dataclass
class ExecutionCheck:
    """After Layer 11: execution guard."""
    fix_heartbeat_ok: bool = True
    spread_ok: bool = True
    not_nfp_fomc: bool = True
    session_active: bool = True
    position_limit_ok: bool = True
    daily_loss_ok: bool = True
    all_checks_passed: bool = True
    failed_checks: List[str] = field(default_factory=list)


@dataclass
class FIXOrder:
    """After Layer 12: FIX order execution."""
    order_id: str = ""
    cl_ord_id: str = ""
    symbol: str = "XAUUSD"
    side: int = 0          # 1=BUY, 2=SELL
    order_qty: float = 0.0
    price: float = 0.0
    stop_loss: float = 0.0
    take_profit_1: float = 0.0
    take_profit_2: float = 0.0
    take_profit_3: float = 0.0
    magic_id: str = ""
    signal_hash: str = ""
    raw_fix: str = ""


@dataclass
class PositionState:
    """After Layer 13: position lifecycle."""
    order_id: str = ""
    entry_price: float = 0.0
    current_price: float = 0.0
    direction: SignalDirection = SignalDirection.HOLD
    current_sl: float = 0.0
    current_tp1: float = 0.0
    current_tp2: float = 0.0
    current_tp3: float = 0.0
    tp1_hit: bool = False
    tp2_hit: bool = False
    tp3_hit: bool = False
    pnl: float = 0.0
    pnl_pips: float = 0.0
    should_emergency_close: bool = False
    emergency_reason: str = ""


@dataclass
class LayerTimings:
    """Latency per layer in nanoseconds."""
    l0_hardware_ns: int = 0
    l1_integrity_ns: int = 0
    l2_filter_ns: int = 0
    l3_168filter_ns: int = 0
    l4_manipulation_ns: int = 0
    l5_compress_ns: int = 0
    l6_ml_inference_ns: int = 0
    l7_rl_agents_ns: int = 0
    l8_bayesian_ns: int = 0
    l9_gate_wall_ns: int = 0
    l10_risk_ns: int = 0
    l11_guard_ns: int = 0
    l12_execution_ns: int = 0
    l13_lifecycle_ns: int = 0
    l14_learning_ns: int = 0
    l15_loop_ns: int = 0
    total_ns: int = 0

    @property
    def total_ms(self) -> float:
        return self.total_ns / 1_000_000

    def to_dict(self) -> Dict[str, float]:
        return {k: v / 1_000_000 for k, v in self.__dict__.items()}  # ms


__all__ = [
    "TickData", "ValidatedTick", "FilteredSignals", "FilterVector168",
    "SignalDirection", "ManipulationVerdict", "CompressedVector",
    "MLPrediction", "MLPredictionMatrix", "RLAgentVote", "RLEnsemble",
    "BayesianFusion", "GateResult", "ConfidenceWall", "RiskParameters",
    "ExecutionCheck", "FIXOrder", "PositionState", "LayerTimings",
]
