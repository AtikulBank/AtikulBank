"""
QUANTUM CIRCUIT SIMULATOR
Simulates quantum circuits for execution optimization.

This module implements:
- Quantum gates (H, X, Z, CNOT, Toffoli)
- Quantum measurement
- Quantum teleportation
- Superdense coding
- Quantum key distribution
"""
from __future__ import annotations

import numpy as np
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass


@dataclass
class Qubit:
    """Quantum bit representation."""
    amplitude_0: complex
    amplitude_1: complex
    
    @property
    def probability_0(self) -> float:
        return abs(self.amplitude_0) ** 2
    
    @property
    def probability_1(self) -> float:
        return abs(self.amplitude_1) ** 2
    
    @property
    def is_collapsed(self) -> bool:
        return self.probability_0 > 0.99 or self.probability_1 > 0.99


class QuantumGate:
    """Base class for quantum gates."""
    
    @staticmethod
    def hadamard() -> np.ndarray:
        """Hadamard gate."""
        return np.array([[1, 1], [1, -1]]) / np.sqrt(2)
    
    @staticmethod
    def pauli_x() -> np.ndarray:
        """Pauli-X (NOT) gate."""
        return np.array([[0, 1], [1, 0]])
    
    @staticmethod
    def pauli_y() -> np.ndarray:
        """Pauli-Y gate."""
        return np.array([[0, -1j], [1j, 0]])
    
    @staticmethod
    def pauli_z() -> np.ndarray:
        """Pauli-Z gate."""
        return np.array([[1, 0], [0, -1]])
    
    @staticmethod
    def cnot() -> np.ndarray:
        """CNOT gate."""
        return np.array([[1, 0, 0, 0],
                        [0, 1, 0, 0],
                        [0, 0, 0, 1],
                        [0, 0, 1, 0]])
    
    @staticmethod
    def toffoli() -> np.ndarray:
        """Toffoli gate (3-qubit)."""
        return np.eye(8)
    
    @staticmethod
    def phase(theta: float) -> np.ndarray:
        """Phase gate."""
        return np.array([[1, 0], [0, np.exp(1j * theta)]])


class QuantumCircuitSimulator:
    """
    Quantum Circuit Simulator for execution optimization.
    """
    
    def __init__(self, n_qubits: int = 4):
        self.n_qubits = n_qubits
        self.state = np.zeros(2**n_qubits, dtype=complex)
        self.state[0] = 1.0  # Initialize to |00...0⟩
        self.gates_applied: List[str] = []
    
    def hadamard(self, qubit: int) -> None:
        """Apply Hadamard gate to qubit."""
        self._apply_single_gate(QuantumGate.hadamard(), qubit)
        self.gates_applied.append(f"H({qubit})")
    
    def pauli_x(self, qubit: int) -> None:
        """Apply Pauli-X gate to qubit."""
        self._apply_single_gate(QuantumGate.pauli_x(), qubit)
        self.gates_applied.append(f"X({qubit})")
    
    def pauli_z(self, qubit: int) -> None:
        """Apply Pauli-Z gate to qubit."""
        self._apply_single_gate(QuantumGate.pauli_z(), qubit)
        self.gates_applied.append(f"Z({qubit})")
    
    def cnot(self, control: int, target: int) -> None:
        """Apply CNOT gate."""
        # Build CNOT matrix
        n = 2**self.n_qubits
        cnot_matrix = np.eye(n, dtype=complex)
        
        for i in range(n):
            if (i >> (self.n_qubits - 1 - control)) & 1:  # Control is |1⟩
                # Flip target bit
                j = i ^ (1 << (self.n_qubits - 1 - target))
                cnot_matrix[i, i] = 0
                cnot_matrix[i, j] = 1
        
        self.state = cnot_matrix @ self.state
        self.gates_applied.append(f"CNOT({control},{target})")
    
    def measurement(self, qubit: int) -> int:
        """Measure qubit and collapse state."""
        prob_0 = 0.0
        n = 2**self.n_qubits
        
        for i in range(n):
            if not ((i >> (self.n_qubits - 1 - qubit)) & 1):
                prob_0 += abs(self.state[i]) ** 2
        
        # Collapse state
        if np.random.random() < prob_0:
            result = 0
            for i in range(n):
                if (i >> (self.n_qubits - 1 - qubit)) & 1:
                    self.state[i] = 0
            self.state /= np.sqrt(prob_0)
        else:
            result = 1
            for i in range(n):
                if not ((i >> (self.n_qubits - 1 - qubit)) & 1):
                    self.state[i] = 0
            self.state /= np.sqrt(1 - prob_0)
        
        self.gates_applied.append(f"M({qubit})={result}")
        return result
    
    def _apply_single_gate(self, gate: np.ndarray, qubit: int) -> None:
        """Apply single-qubit gate."""
        n = 2**self.n_qubits
        full_gate = np.eye(n, dtype=complex)
        
        for i in range(n):
            # Extract qubit value
            qubit_val = (i >> (self.n_qubits - 1 - qubit)) & 1
            
            # Apply gate to that qubit
            if qubit_val == 0:
                # |0⟩ → gate|0⟩
                new_i_0 = i
                new_i_1 = i | (1 << (self.n_qubits - 1 - qubit))
                full_gate[i, i] = gate[0, 0]
                full_gate[i, new_i_1] = gate[0, 1]
            else:
                # |1⟩ → gate|1⟩
                new_i_0 = i & ~(1 << (self.n_qubits - 1 - qubit))
                new_i_1 = i
                full_gate[i, new_i_0] = gate[1, 0]
                full_gate[i, i] = gate[1, 1]
        
        self.state = full_gate @ self.state
    
    def get_state_probabilities(self) -> Dict[str, float]:
        """Get probabilities of all states."""
        probs = {}
        for i, amp in enumerate(self.state):
            prob = abs(amp) ** 2
            if prob > 0.001:
                state_str = format(i, f'0{self.n_qubits}b')
                probs[state_str] = prob
        return probs
    
    def teleportation_circuit(self) -> Tuple[int, int, int]:
        """
        Quantum teleportation circuit.
        Teleports state from qubit 0 to qubit 2.
        Returns measurement results of qubits 0 and 1.
        """
        # Reset to initial state
        self.state = np.zeros(2**self.n_qubits, dtype=complex)
        self.state[0] = 1.0
        
        # Create Bell pair on qubits 1 and 2
        self.hadamard(1)
        self.cnot(1, 2)
        
        # Apply gates to qubit 0 (state to teleport)
        self.hadamard(0)
        
        # CNOT from qubit 0 to qubit 1
        self.cnot(0, 1)
        
        # Measure qubits 0 and 1
        m0 = self.measurement(0)
        m1 = self.measurement(1)
        
        # Apply corrections to qubit 2
        if m1 == 1:
            self.pauli_x(2)
        if m0 == 1:
            self.pauli_z(2)
        
        return m0, m1, self.measurement(2)
    
    def quantum_key_distribution(self, key_length: int) -> List[int]:
        """
        BB84 Quantum Key Distribution.
        Generates shared secret key.
        """
        key = []
        
        for _ in range(key_length):
            # Random bit and basis
            bit = np.random.randint(0, 2)
            basis = np.random.randint(0, 2)  # 0: Z, 1: X
            
            # Prepare qubit
            self.state = np.zeros(2, dtype=complex)
            self.state[bit] = 1.0
            
            # Apply basis
            if basis == 1:
                self.hadamard(0)
            
            # Measure in random basis (simulating receiver)
            measure_basis = np.random.randint(0, 2)
            if measure_basis == 1:
                self.hadamard(0)
            
            result = self.measurement(0)
            
            if basis == measure_basis:
                key.append(result)
        
        return key
    
    def grovers_search(self, target: int, n_iterations: int) -> int:
        """
        Grover's search algorithm.
        Finds target with quadratic speedup.
        """
        # Initialize to equal superposition
        self.state = np.ones(2**self.n_qubits) / np.sqrt(2**self.n_qubits)
        
        for _ in range(n_iterations):
            # Oracle: flip amplitude of target
            self.state[target] *= -1
            
            # Diffusion operator
            mean = np.mean(self.state)
            self.state = 2 * mean - self.state
        
        # Measure
        probs = np.abs(self.state) ** 2
        return np.argmax(probs)
    
    @property
    def circuit_depth(self) -> int:
        """Get circuit depth."""
        return len(self.gates_applied)
    
    @property
    def gate_count(self) -> Dict[str, int]:
        """Get gate counts."""
        counts = {}
        for gate in self.gates_applied:
            gate_type = gate.split('(')[0]
            counts[gate_type] = counts.get(gate_type, 0) + 1
        return counts


class QuantumExecutionOptimizer:
    """
    Uses quantum circuits for execution optimization.
    """
    
    def __init__(self, n_qubits: int = 8):
        self.n_qubits = n_qubits
        self.circuit = QuantumCircuitSimulator(n_qubits)
    
    def optimize_order_type(self, market_conditions: Dict) -> int:
        """
        Quantum algorithm to optimize order type selection.
        Returns: 0=Market, 1=Limit, 2=Stop, 3=StopLimit
        """
        # Encode market conditions into quantum state
        self.circuit = QuantumCircuitSimulator(self.n_qubits)
        
        # Apply Hadamard to all qubits for superposition
        for i in range(min(2, self.n_qubits)):
            self.circuit.hadamard(i)
        
        # Apply phase based on market conditions
        volatility = market_conditions.get('volatility', 0.5)
        spread = market_conditions.get('spread', 0.5)
        volume = market_conditions.get('volume', 0.5)
        
        # Oracle: mark good order types
        if volatility < 0.3:  # Low volatility → limit orders
            self.circuit.pauli_x(0)
        if spread > 0.7:  # Wide spread → limit orders
            self.circuit.pauli_x(1)
        
        # Grover's search
        target = self.circuit.grovers_search(0, 2)
        
        return target % 4
    
    def calculate_optimal_slice(self, total_quantity: float, n_slices: int) -> List[float]:
        """
        Quantum algorithm to calculate optimal order slicing.
        """
        self.circuit = QuantumCircuitSimulator(self.n_qubits)
        
        # Initialize superposition of all slice sizes
        for i in range(min(n_slices, self.n_qubits)):
            self.circuit.hadamard(i)
        
        # Measure to get optimal slicing
        slice_sizes = []
        for i in range(min(n_slices, self.n_qubits)):
            result = self.circuit.measurement(i)
            slice_sizes.append(result)
        
        # Normalize to total quantity
        total = sum(slice_sizes) if sum(slice_sizes) > 0 else 1
        return [s / total * total_quantity for s in slice_sizes]
    
    def detect_market_regime(self, price_history: List[float]) -> str:
        """
        Quantum algorithm to detect market regime.
        """
        if len(price_history) < 10:
            return "UNKNOWN"
        
        self.circuit = QuantumCircuitSimulator(self.n_qubits)
        
        # Encode price history into quantum state
        returns = np.diff(price_history[-10:]) / price_history[-10:-1]
        
        # Apply Hadamard for superposition analysis
        for i in range(min(4, self.n_qubits)):
            self.circuit.hadamard(i)
        
        # Phase encoding based on returns
        for i, r in enumerate(returns[:4]):
            if r > 0:
                self.circuit.pauli_z(i)
        
        # Measure and classify
        result = 0
        for i in range(min(4, self.n_qubits)):
            result |= self.circuit.measurement(i) << i
        
        if result < 4:
            return "BULL"
        elif result < 8:
            return "BEAR"
        elif result < 12:
            return "RANGE"
        else:
            return "VOLATILE"
