"""
LAYER 11 EXECUTION GUARD - COMPREHENSIVE TESTS
Tests for all 7 mathematical formulas and quantum components.
"""
import pytest
import numpy as np
from datetime import datetime, timezone
from Layer_11_execution_guard.execution_guard import ExecutionGuard, ExecutionGuardConfig
from Layer_11_execution_guard.quantum.quantum_engine import (
    QuantumRandomNumberGenerator,
    QuantumAnnealing,
    QuantumErrorCorrection,
    QuantumSuperposition,
    QuantumEntanglement,
    QuantumWalk,
    QuantumExecutionEngine,
)
from Layer_11_execution_guard.quantum.quantum_circuit import (
    QuantumCircuitSimulator,
    QuantumExecutionOptimizer,
)


class TestFormula1_FIXHeartbeat:
    """Test FIX heartbeat < 30s."""
    
    def test_heartbeat_within_timeout(self):
        config = ExecutionGuardConfig()
        guard = ExecutionGuard(config)
        guard.on_heartbeat()
        
        result = guard.check(
            bid=2350.0,
            ask=2350.5,
            utc_now=datetime(2025, 6, 9, 14, 30, tzinfo=timezone.utc)
        )
        assert result.fix_heartbeat_ok == True
    
    def test_heartbeat_expired(self):
        config = ExecutionGuardConfig(heartbeat_timeout_s=0.001)
        guard = ExecutionGuard(config)
        guard.on_heartbeat()
        
        import time
        time.sleep(0.01)
        
        result = guard.check(
            bid=2350.0,
            ask=2350.5,
            utc_now=datetime(2025, 6, 9, 14, 30, tzinfo=timezone.utc)
        )
        assert result.fix_heartbeat_ok == False


class TestFormula2_SpreadATR:
    """Test Spread < ATR × 0.10."""
    
    def test_spread_within_atr(self):
        config = ExecutionGuardConfig()
        guard = ExecutionGuard(config)
        
        result = guard.check(
            bid=2350.0,
            ask=2350.5,
            utc_now=datetime(2025, 6, 9, 14, 30, tzinfo=timezone.utc)
        )
        assert result.spread_ok == True
    
    def test_spread_exceeds_atr(self):
        config = ExecutionGuardConfig()
        guard = ExecutionGuard(config)
        
        result = guard.check(
            bid=2350.0,
            ask=2355.0,
            utc_now=datetime(2025, 6, 9, 14, 30, tzinfo=timezone.utc)
        )
        assert result.spread_ok == False


class TestFormula3_NFPBlock:
    """Test Not within ±5min NFP/FOMC."""
    
    def test_nfp_blocked(self):
        config = ExecutionGuardConfig()
        guard = ExecutionGuard(config)
        
        result = guard.check(
            bid=2350.0,
            ask=2350.5,
            utc_now=datetime(2025, 1, 10, 13, 30, tzinfo=timezone.utc)
        )
        assert result.not_nfp_fomc == False
    
    def test_nfp_outside_block(self):
        config = ExecutionGuardConfig()
        guard = ExecutionGuard(config)
        
        result = guard.check(
            bid=2350.0,
            ask=2350.5,
            utc_now=datetime(2025, 1, 10, 13, 24, tzinfo=timezone.utc)
        )
        assert result.not_nfp_fomc == True


class TestFormula4_Session:
    """Test Session: London 07-16 UTC OR NY 13-21 UTC."""
    
    def test_london_session(self):
        config = ExecutionGuardConfig()
        guard = ExecutionGuard(config)
        
        result = guard.check(
            bid=2350.0,
            ask=2350.5,
            utc_now=datetime(2025, 6, 9, 10, 30, tzinfo=timezone.utc)
        )
        assert result.session_active == True
    
    def test_ny_session(self):
        config = ExecutionGuardConfig()
        guard = ExecutionGuard(config)
        
        result = guard.check(
            bid=2350.0,
            ask=2350.5,
            utc_now=datetime(2025, 6, 9, 17, 30, tzinfo=timezone.utc)
        )
        assert result.session_active == True
    
    def test_off_hours(self):
        config = ExecutionGuardConfig()
        guard = ExecutionGuard(config)
        
        result = guard.check(
            bid=2350.0,
            ask=2350.5,
            utc_now=datetime(2025, 6, 9, 3, 30, tzinfo=timezone.utc)
        )
        assert result.session_active == False


class TestFormula5_Positions:
    """Test Positions < 3."""
    
    def test_positions_within_limit(self):
        config = ExecutionGuardConfig()
        guard = ExecutionGuard(config)
        
        guard.on_position_open()
        guard.on_position_open()
        
        result = guard.check(
            bid=2350.0,
            ask=2350.5,
            utc_now=datetime(2025, 6, 9, 14, 30, tzinfo=timezone.utc)
        )
        assert result.position_limit_ok == True
    
    def test_positions_exceeds_limit(self):
        config = ExecutionGuardConfig()
        guard = ExecutionGuard(config)
        
        guard.on_position_open()
        guard.on_position_open()
        guard.on_position_open()
        
        result = guard.check(
            bid=2350.0,
            ask=2350.5,
            utc_now=datetime(2025, 6, 9, 14, 30, tzinfo=timezone.utc)
        )
        assert result.position_limit_ok == False


class TestFormula6_DailyLoss:
    """Test Daily loss < 3%."""
    
    def test_daily_loss_within_limit(self):
        config = ExecutionGuardConfig()
        guard = ExecutionGuard(config)
        
        guard.record_trade_pnl(100.0)
        
        result = guard.check(
            bid=2350.0,
            ask=2350.5,
            utc_now=datetime(2025, 6, 9, 14, 30, tzinfo=timezone.utc)
        )
        assert result.daily_loss_ok == True
    
    def test_daily_loss_exceeds_limit(self):
        config = ExecutionGuardConfig()
        guard = ExecutionGuard(config)
        
        guard.record_trade_pnl(-400.0)
        
        result = guard.check(
            bid=2350.0,
            ask=2350.5,
            utc_now=datetime(2025, 6, 9, 14, 30, tzinfo=timezone.utc)
        )
        assert result.daily_loss_ok == False


class TestQuantumEngine:
    """Test quantum components."""
    
    def test_qrng(self):
        qrng = QuantumRandomNumberGenerator()
        
        for _ in range(100):
            r = qrng.quantum_random()
            assert 0 <= r < 1
    
    def test_quantum_annealing(self):
        annealer = QuantumAnnealing()
        
        prices = [2350.0, 2351.0, 2352.0, 2349.0, 2348.0]
        volumes = [100, 150, 120, 110, 130]
        
        result = annealer.anneal(prices, volumes, 10.0, 100)
        
        assert result.optimal_price > 0
        assert 0 <= result.confidence <= 1
    
    def test_quantum_error_correction(self):
        qec = QuantumErrorCorrection()
        
        original = 2350.0
        encoded = qec.encode(original)
        
        assert len(encoded) == 3
        
        decoded, error_rate = qec.decode(encoded)
        
        assert abs(decoded - original) < 0.1
        assert error_rate > 0.9
    
    def test_quantum_superposition(self):
        qs = QuantumSuperposition()
        
        current = 2350.0
        candidates = [2351.0, 2349.0, 2352.0, 2348.0]
        
        optimal, probs = qs.superpose(current, candidates)
        
        assert optimal in candidates
        assert len(probs) == 4
    
    def test_quantum_entanglement(self):
        qe = QuantumEntanglement()
        
        series1 = [2350.0, 2351.0, 2352.0, 2353.0]
        series2 = [100.0, 110.0, 120.0, 130.0]
        
        corr, entropy = qe.entangle(series1, series2)
        
        assert -1 <= corr <= 1
        assert entropy >= 0
    
    def test_quantum_walk(self):
        qw = QuantumWalk(50)
        
        start_price = 2350.0
        bids = [2349.0, 2348.0, 2347.0]
        asks = [2351.0, 2352.0, 2353.0]
        
        pred_price, confidence = qw.walk(start_price, bids, asks)
        
        assert pred_price > 0
        assert 0 <= confidence <= 1


class TestQuantumCircuit:
    """Test quantum circuit simulator."""
    
    def test_hadamard_gate(self):
        circuit = QuantumCircuitSimulator(2)
        circuit.hadamard(0)
        
        probs = circuit.get_state_probabilities()
        
        assert len(probs) == 4
        assert abs(sum(probs.values()) - 1.0) < 0.01
    
    def test_cnot_gate(self):
        circuit = QuantumCircuitSimulator(2)
        circuit.pauli_x(0)  # Set qubit 0 to |1⟩
        circuit.cnot(0, 1)  # CNOT: flip qubit 1
        
        probs = circuit.get_state_probabilities()
        
        # Should be in state |11⟩
        assert probs.get('11', 0) > 0.9
    
    def test_measurement(self):
        circuit = QuantumCircuitSimulator(1)
        circuit.hadamard(0)
        
        result = circuit.measurement(0)
        
        assert result in [0, 1]
    
    def test_grovers_search(self):
        circuit = QuantumCircuitSimulator(3)
        
        target = 5
        result = circuit.grovers_search(target, 3)
        
        assert result == target


class TestQuantumExecutionOptimizer:
    """Test quantum execution optimizer."""
    
    def test_optimize_order_type(self):
        optimizer = QuantumExecutionOptimizer()
        
        conditions = {
            'volatility': 0.2,
            'spread': 0.3,
            'volume': 0.7,
        }
        
        order_type = optimizer.optimize_order_type(conditions)
        
        assert 0 <= order_type <= 3
    
    def test_calculate_optimal_slice(self):
        optimizer = QuantumExecutionOptimizer()
        
        slices = optimizer.calculate_optimal_slice(100.0, 5)
        
        assert len(slices) == 5
        assert abs(sum(slices) - 100.0) < 0.01
    
    def test_detect_market_regime(self):
        optimizer = QuantumExecutionOptimizer()
        
        prices = [2350 + i for i in range(20)]
        
        regime = optimizer.detect_market_regime(prices)
        
        assert regime in ["BULL", "BEAR", "RANGE", "VOLATILE", "UNKNOWN"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
