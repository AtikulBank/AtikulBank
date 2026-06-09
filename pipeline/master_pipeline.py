"""
MASTER PIPELINE ORCHESTRATOR
Connects all 15 layers into a complete trading pipeline.

Layer 0:  Hardware Guard
Layer 1:  Signal Integrity
Layer 2:  Multi-Scale Filter
Layer 3:  168 Filter Engine
Layer 4:  Manipulation Shield
Layer 5:  Dimensional Compression
Layer 6:  ML Inference (30 models)
Layer 7:  RL Agents (10 agents)
Layer 8:  Bayesian Ensemble
Layer 9:  Confidence Gate
Layer 10: Risk Engine
Layer 11: Execution Guard
Layer 12: FIX Execution
Layer 13: Position Lifecycle
Layer 14: Self Learning
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

from pipeline import (
    TickData, ValidatedTick, FilteredSignals, FilterVector168,
    SignalDirection, ManipulationVerdict, CompressedVector,
    MLPrediction, MLPredictionMatrix, RLAgentVote, RLEnsemble,
    BayesianFusion, GateResult, ConfidenceWall, RiskParameters,
    ExecutionCheck, FIXOrder, PositionState, LayerTimings,
)

# Import all layers
from Layer_00_hardware_guard.hardware_guard import HardwareGuard
from Layer_01_signal_integrity.signal_integrity import SignalIntegrity
from Layer_02_multi_scale_filter.multi_scale_filter import MultiScaleFilter
from Layer_03_168_filter_engine.filter_engine import FilterEngine
from Layer_04_manipulation_shield.manipulation_shield import ManipulationShield
from Layer_05_dimensional_compression.dimensional_compression import DimensionalCompression
from Layer_06_ml_inference.ml_inference import MLInference
from Layer_07_rl_agents.rl_agents import RLAgents
from Layer_08_bayesian_ensemble.bayesian_ensemble import BayesianEnsemble
from Layer_10_risk_engine.risk_engine import RiskEngine
from Layer_11_execution_guard.execution_guard import ExecutionGuard
from Layer_12_fix_execution.fix_execution import FIXExecution
from Layer_13_position_lifecycle.position_lifecycle import PositionLifecycle
from Layer_14_self_learning.self_learning import SelfLearning


@dataclass
class PipelineConfig:
    """Master pipeline configuration."""
    symbol: str = "XAUUSD"
    enable_all_layers: bool = True
    max_latency_ms: float = 100.0
    min_confidence: float = 0.6
    enable_self_learning: bool = True
    enable_position_management: bool = True


@dataclass
class PipelineResult:
    """Complete pipeline result."""
    # Input
    tick: TickData = field(default_factory=TickData)
    timestamp: float = 0.0
    
    # Layer outputs
    validated_tick: Optional[ValidatedTick] = None
    filtered_signals: Optional[FilteredSignals] = None
    filter_vector: Optional[FilterVector168] = None
    manipulation_verdict: Optional[ManipulationVerdict] = None
    compressed_vector: Optional[CompressedVector] = None
    ml_predictions: Optional[MLPredictionMatrix] = None
    rl_ensemble: Optional[RLEnsemble] = None
    bayesian_fusion: Optional[BayesianFusion] = None
    confidence_wall: Optional[ConfidenceWall] = None
    risk_parameters: Optional[RiskParameters] = None
    execution_check: Optional[ExecutionCheck] = None
    
    # Decision
    final_signal: SignalDirection = SignalDirection.HOLD
    final_confidence: float = 0.0
    should_trade: bool = False
    
    # Order
    order: Optional[FIXOrder] = None
    position: Optional[PositionState] = None
    
    # Timing
    timings: LayerTimings = field(default_factory=LayerTimings)
    total_latency_ms: float = 0.0
    
    # Learning
    learning_result: Optional[Dict] = None


class MasterPipeline:
    """
    MASTER PIPELINE ORCHESTRATOR
    Connects all 15 layers into a complete trading pipeline.
    """
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        
        # Initialize all layers
        self.hardware_guard = HardwareGuard()
        self.signal_integrity = SignalIntegrity()
        self.multi_scale_filter = MultiScaleFilter()
        self.filter_engine = FilterEngine()
        self.manipulation_shield = ManipulationShield()
        self.dimensional_compression = DimensionalCompression()
        self.ml_inference = MLInference()
        self.rl_agents = RLAgents()
        self.bayesian_ensemble = BayesianEnsemble()
        self.risk_engine = RiskEngine()
        self.execution_guard = ExecutionGuard()
        self.fix_execution = FIXExecution()
        self.position_lifecycle = PositionLifecycle()
        self.self_learning = SelfLearning()
        
        # State
        self._tick_count = 0
        self._last_tick_time = 0.0
        self._pipeline_start_time = time.time()
        
        # Performance tracking
        self._latencies: List[float] = []
        self._signals: List[SignalDirection] = []
        self._trades_executed: int = 0
        
        # Initialize hardware
        self.hardware_guard.initialize()
    
    def process_tick(self, tick: TickData) -> PipelineResult:
        """
        Process a single tick through the complete pipeline.
        
        Returns PipelineResult with all layer outputs and final decision.
        """
        pipeline_start = time.time()
        self._tick_count += 1
        
        result = PipelineResult(
            tick=tick,
            timestamp=pipeline_start,
        )
        
        timings = LayerTimings()
        
        try:
            # Layer 0: Hardware Guard
            t0 = time.time()
            self.hardware_guard.on_tick_start()
            timings.l0_hardware_ns = int((time.time() - t0) * 1e9)
            
            # Layer 1: Signal Integrity
            t1 = time.time()
            result.validated_tick = self.signal_integrity.validate_tick(tick)
            if not result.validated_tick.is_valid:
                result.final_signal = SignalDirection.HOLD
                result.should_trade = False
                timings.l1_integrity_ns = int((time.time() - t1) * 1e9)
                timings.total_ns = int((time.time() - pipeline_start) * 1e9)
                result.timings = timings
                result.total_latency_ms = timings.total_ns / 1e6
                return result
            timings.l1_integrity_ns = int((time.time() - t1) * 1e9)
            
            # Layer 2: Multi-Scale Filter
            t2 = time.time()
            result.filtered_signals = self.multi_scale_filter.filter_tick(
                tick.last_price if tick.last_price > 0 else (tick.bid + tick.ask) / 2
            )
            timings.l2_filter_ns = int((time.time() - t2) * 1e9)
            
            # Layer 3: 168 Filter Engine
            t3 = time.time()
            result.filter_vector = self.filter_engine.compute_filters(
                result.filtered_signals
            )
            timings.l3_168filter_ns = int((time.time() - t3) * 1e9)
            
            # Layer 4: Manipulation Shield
            t4 = time.time()
            result.manipulation_verdict = self.manipulation_shield.check(
                tick, result.filter_vector
            )
            if result.manipulation_verdict.is_manipulated:
                result.final_signal = SignalDirection.HOLD
                result.should_trade = False
                timings.l4_manipulation_ns = int((time.time() - t4) * 1e9)
                timings.total_ns = int((time.time() - pipeline_start) * 1e9)
                result.timings = timings
                result.total_latency_ms = timings.total_ns / 1e6
                return result
            timings.l4_manipulation_ns = int((time.time() - t4) * 1e9)
            
            # Layer 5: Dimensional Compression
            t5 = time.time()
            result.compressed_vector = self.dimensional_compression.compress(
                result.filter_vector
            )
            timings.l5_compress_ns = int((time.time() - t5) * 1e9)
            
            # Layer 6: ML Inference
            t6 = time.time()
            result.ml_predictions = self.ml_inference.predict(
                result.compressed_vector
            )
            timings.l6_ml_inference_ns = int((time.time() - t6) * 1e9)
            
            # Layer 7: RL Agents
            t7 = time.time()
            result.rl_ensemble = self.rl_agents.vote(
                result.filter_vector, result.ml_predictions
            )
            timings.l7_rl_agents_ns = int((time.time() - t7) * 1e9)
            
            # Layer 8: Bayesian Ensemble
            t8 = time.time()
            result.bayesian_fusion = self.bayesian_ensemble.fuse(
                result.ml_predictions, result.rl_ensemble
            )
            timings.l8_bayesian_ns = int((time.time() - t8) * 1e9)
            
            # Layer 9: Confidence Gate
            t9 = time.time()
            result.confidence_wall = self._check_confidence_gate(
                result.bayesian_fusion, result.filter_vector
            )
            timings.l9_gate_wall_ns = int((time.time() - t9) * 1e9)
            
            # Layer 10: Risk Engine
            t10 = time.time()
            result.risk_parameters = self.risk_engine.calculate_risk(
                result.bayesian_fusion, result.filter_vector
            )
            timings.l10_risk_ns = int((time.time() - t10) * 1e9)
            
            # Layer 11: Execution Guard
            t11 = time.time()
            result.execution_check = self.execution_guard.check(
                bid=tick.bid,
                ask=tick.ask,
                utc_now=datetime.now(timezone.utc),
            )
            timings.l11_guard_ns = int((time.time() - t11) * 1e9)
            
            # Make final decision
            result.final_signal = result.bayesian_fusion.final_signal
            result.final_confidence = result.bayesian_fusion.final_confidence
            
            # Check if we should trade
            result.should_trade = self._should_trade(result)
            
            # Layer 12: FIX Execution (if trading)
            if result.should_trade:
                t12 = time.time()
                result.order = self._create_order(result)
                timings.l12_execution_ns = int((time.time() - t12) * 1e9)
                
                # Layer 13: Position Lifecycle
                if self.config.enable_position_management:
                    t13 = time.time()
                    result.position = self._manage_position(result)
                    timings.l13_lifecycle_ns = int((time.time() - t13) * 1e9)
            
            # Layer 14: Self Learning
            if self.config.enable_self_learning:
                t14 = time.time()
                result.learning_result = self._update_learning(result)
                timings.l14_learning_ns = int((time.time() - t14) * 1e9)
            
            # Calculate total timing
            timings.total_ns = int((time.time() - pipeline_start) * 1e9)
            result.timings = timings
            result.total_latency_ms = timings.total_ns / 1e6
            
            # Track performance
            self._latencies.append(result.total_latency_ms)
            self._signals.append(result.final_signal)
            
            if result.should_trade:
                self._trades_executed += 1
            
            return result
            
        except Exception as e:
            # Error handling
            result.final_signal = SignalDirection.HOLD
            result.should_trade = False
            timings.total_ns = int((time.time() - pipeline_start) * 1e9)
            result.timings = timings
            result.total_latency_ms = timings.total_ns / 1e6
            return result
    
    def _check_confidence_gate(
        self,
        fusion: BayesianFusion,
        filter_vector: FilterVector168,
    ) -> ConfidenceWall:
        """Layer 9: Check confidence gate."""
        gates = []
        
        # Gate 1: Minimum confidence
        gate1 = GateResult(
            gate_id=1,
            name="minimum_confidence",
            value=fusion.final_confidence,
            threshold=self.config.min_confidence,
            passed=fusion.final_confidence >= self.config.min_confidence,
        )
        gates.append(gate1)
        
        # Gate 2: Agreement between ML and RL
        ml_signal = 1 if fusion.ml_weight > 0.5 else -1
        rl_signal = 1 if fusion.rl_weight > 0.5 else -1
        agreement = (ml_signal == rl_signal)
        gate2 = GateResult(
            gate_id=2,
            name="ml_rl_agreement",
            value=1.0 if agreement else 0.0,
            threshold=0.5,
            passed=agreement,
        )
        gates.append(gate2)
        
        # Gate 3: Filter vector stability
        stability = abs(fusion.final_confidence - 0.5) * 2
        gate3 = GateResult(
            gate_id=3,
            name="signal_stability",
            value=stability,
            threshold=0.3,
            passed=stability >= 0.3,
        )
        gates.append(gate3)
        
        # Check if all gates passed
        all_passed = all(g.passed for g in gates)
        failed_gates = [g.name for g in gates if not g.passed]
        
        return ConfidenceWall(
            gates=gates,
            all_passed=all_passed,
            failed_gates=failed_gates,
        )
    
    def _should_trade(self, result: PipelineResult) -> bool:
        """Determine if we should trade."""
        # Check all conditions
        conditions = [
            result.validated_tick is not None and result.validated_tick.is_valid,
            result.manipulation_verdict is not None and not result.manipulation_verdict.is_manipulated,
            result.confidence_wall is not None and result.confidence_wall.all_passed,
            result.execution_check is not None and result.execution_check.all_checks_passed,
            result.risk_parameters is not None and not result.risk_parameters.halt_triggered,
            result.final_signal != SignalDirection.HOLD,
            result.final_confidence >= self.config.min_confidence,
        ]
        
        return all(conditions)
    
    def _create_order(self, result: PipelineResult) -> FIXOrder:
        """Create FIX order."""
        risk = result.risk_parameters
        
        # Calculate order quantity
        quantity = risk.position_size if risk else 0.01
        
        # Create order
        order = self.fix_execution.create_order(
            symbol=self.config.symbol,
            side=OrderSide.BUY if result.final_signal == SignalDirection.BUY else OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=quantity,
        )
        
        return order
    
    def _manage_position(self, result: PipelineResult) -> Optional[PositionState]:
        """Manage position lifecycle."""
        if not result.order:
            return None
        
        # Open position
        position = self.position_lifecycle.open_position(
            symbol=self.config.symbol,
            side=PositionSide.LONG if result.final_signal == SignalDirection.BUY else PositionSide.SHORT,
            entry_price=result.tick.last_price or (result.tick.bid + result.tick.ask) / 2,
            quantity=result.order.quantity,
            stop_loss=result.risk_parameters.stop_loss if result.risk_parameters else 0,
            take_profit_1=result.risk_parameters.take_profit_1 if result.risk_parameters else 0,
            take_profit_2=result.risk_parameters.take_profit_2 if result.risk_parameters else 0,
            take_profit_3=result.risk_parameters.take_profit_3 if result.risk_parameters else 0,
        )
        
        return position
    
    def _update_learning(self, result: PipelineResult) -> Dict:
        """Update self-learning system."""
        # Create trade outcome for learning
        outcome = TradeOutcome(
            trade_id=f"TRADE{int(time.time())}",
            timestamp=time.time(),
            symbol=self.config.symbol,
            side="BUY" if result.final_signal == SignalDirection.BUY else "SELL",
            entry_price=result.tick.last_price or (result.tick.bid + result.tick.ask) / 2,
            exit_price=0,
            quantity=result.order.quantity if result.order else 0,
            pnl=0,
            pnl_pct=0,
            duration_seconds=0,
            features=result.compressed_vector.pca_components[:10] if result.compressed_vector else {},
            prediction=result.final_confidence,
            confidence=result.final_confidence,
        )
        
        return self.self_learning.record_trade(outcome)
    
    @property
    def stats(self) -> Dict:
        """Get pipeline statistics."""
        return {
            "tick_count": self._tick_count,
            "uptime_seconds": time.time() - self._pipeline_start_time,
            "avg_latency_ms": sum(self._latencies) / max(len(self._latencies), 1),
            "max_latency_ms": max(self._latencies) if self._latencies else 0,
            "trades_executed": self._trades_executed,
            "signal_distribution": {
                "BUY": self._signals.count(SignalDirection.BUY),
                "SELL": self._signals.count(SignalDirection.SELL),
                "HOLD": self._signals.count(SignalDirection.HOLD),
            },
            "layer_stats": {
                "hardware_guard": self.hardware_guard.stats,
                "signal_integrity": self.signal_integrity.stats,
                "filter_engine": self.filter_engine.stats,
                "manipulation_shield": self.manipulation_shield.stats,
                "ml_inference": self.ml_inference.stats,
                "rl_agents": self.rl_agents.stats,
                "execution_guard": self.execution_guard.stats,
                "position_lifecycle": self.position_lifecycle.stats,
                "self_learning": self.self_learning.stats,
            },
        }
