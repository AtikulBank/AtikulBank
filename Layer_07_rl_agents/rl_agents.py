"""
LAYER 7: 10 RL SPECIALIST AGENTS
Reinforcement Learning agents for different market regimes
"""

import numpy as np
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class AgentAction:
    """Action from an RL agent"""
    agent_name: str
    action: int  # -1: sell, 0: hold, 1: buy
    confidence: float  # 0 to 1
    regime: str = "unknown"


@dataclass
class RLResult:
    """Result from RL agent manager"""
    agent_actions: List[AgentAction] = field(default_factory=list)
    regime: str = "unknown"
    regime_confidence: float = 0.0
    best_agent: str = ""
    consensus_action: int = 0
    consensus_confidence: float = 0.0


class RLAgentManager:
    """
    Layer 7: 10 RL Specialist Agents
    Each agent specializes in different market conditions
    """
    
    def __init__(self):
        """Initialize RL Agent Manager"""
        
        # Define 10 specialist agents
        self.agents = {
            "TrendMaster": {
                "condition": lambda f: f.get("hurst", 0.5) > 0.6 and f.get("lyapunov", 0) < 0,
                "regime": "TREND"
            },
            "ReversalSniper": {
                "condition": lambda f: f.get("entropy_rate", 0.5) < 0.3 and f.get("accel", 0) > 0,
                "regime": "REVERSAL"
            },
            "BreakoutHunter": {
                "condition": lambda f: f.get("vol_cluster", 0) > 0.5 and f.get("real_vol", 0) > 0.02,
                "regime": "BREAKOUT"
            },
            "Scalper": {
                "condition": lambda f: f.get("vel_reversal", 0) > 0.3 and f.get("kinetic_e", 0) > 0.01,
                "regime": "SCALP"
            },
            "MacroGuard": {
                "condition": lambda f: f.get("path_var", 0) < 0.1,
                "regime": "MACRO"
            },
            "ChaosFilter": {
                "condition": lambda f: f.get("lyapunov", 0) > 0.5,
                "regime": "CHAOS"
            },
            "TopoAgent": {
                "condition": lambda f: f.get("persist_h1", 0) > 0.5,
                "regime": "TOPOLOGY"
            },
            "FluidAgent": {
                "condition": lambda f: f.get("reynolds", 0) > 2300,
                "regime": "FLUID"
            },
            "QuantumAgent": {
                "condition": lambda f: f.get("q_annealing", 0) < -0.5,
                "regime": "QUANTUM"
            },
            "EntropyAgent": {
                "condition": lambda f: f.get("free_energy", 0) < 0,
                "regime": "ENTROPY"
            }
        }
        
        # Agent performance tracking
        self.agent_performance: Dict[str, Dict[str, float]] = {
            name: {"wins": 0, "losses": 0, "total": 0}
            for name in self.agents
        }
        
        # Current regime
        self.current_regime = "unknown"
        self.regime_history: List[str] = []
        
    def select_agent(self, features: Dict[str, float]) -> AgentAction:
        """
        Select the best agent based on current market conditions
        
        Args:
            features: Current market features
            
        Returns:
            AgentAction from the selected agent
        """
        # Determine current regime
        regime = self._detect_regime(features)
        self.current_regime = regime
        self.regime_history.append(regime)
        
        # Find matching agent
        best_agent = None
        best_confidence = 0.0
        
        for name, config in self.agents.items():
            try:
                if config["condition"](features):
                    # Calculate confidence based on feature strength
                    confidence = self._calculate_confidence(name, features)
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_agent = name
            except Exception:
                continue
        
        # Default to first agent if no match
        if best_agent is None:
            best_agent = list(self.agents.keys())[0]
            best_confidence = 0.3
        
        # Get agent action
        action = self._get_agent_action(best_agent, features)
        
        return AgentAction(
            agent_name=best_agent,
            action=action,
            confidence=best_confidence,
            regime=regime
        )
    
    def _detect_regime(self, features: Dict[str, float]) -> str:
        """Detect current market regime"""
        # Check each agent's condition
        for name, config in self.agents.items():
            try:
                if config["condition"](features):
                    return config["regime"]
            except Exception:
                continue
        
        return "UNKNOWN"
    
    def _calculate_confidence(self, agent_name: str, features: Dict[str, float]) -> float:
        """Calculate confidence for an agent"""
        perf = self.agent_performance.get(agent_name, {"wins": 0, "losses": 0, "total": 0})
        
        if perf["total"] == 0:
            return 0.5  # Default confidence
        
        win_rate = perf["wins"] / perf["total"]
        
        # Adjust based on regime matching
        regime_match = 1.0 if self.agents[agent_name]["regime"] == self.current_regime else 0.5
        
        return float(win_rate * regime_match)
    
    def _get_agent_action(self, agent_name: str, features: Dict[str, float]) -> int:
        """Get action from a specific agent"""
        # Simplified action logic based on agent type
        agent_config = self.agents.get(agent_name, {})
        regime = agent_config.get("regime", "UNKNOWN")
        
        # Get price momentum
        velocity = features.get("velocity", 0)
        price_vel = features.get("price_vel", 0)
        
        # Different action logic based on regime
        if regime == "TREND":
            return 1 if velocity > 0 else -1
        elif regime == "REVERSAL":
            return -1 if velocity > 0 else 1
        elif regime == "BREAKOUT":
            return 1 if features.get("real_vol", 0) > 0.02 else 0
        elif regime == "SCALP":
            return 1 if price_vel > 0 else -1
        elif regime == "CHAOS":
            return 0  # Hold in chaos
        else:
            return 0  # Default hold
    
    def update_performance(self, agent_name: str, won: bool) -> None:
        """Update agent performance after trade"""
        if agent_name in self.agent_performance:
            self.agent_performance[agent_name]["total"] += 1
            if won:
                self.agent_performance[agent_name]["wins"] += 1
            else:
                self.agent_performance[agent_name]["losses"] += 1
    
    def get_regime_stats(self) -> Dict[str, Any]:
        """Get regime statistics"""
        if not self.regime_history:
            return {"current_regime": "unknown", "regime_counts": {}}
        
        # Count regime occurrences
        regime_counts = {}
        for regime in self.regime_history:
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
        
        return {
            "current_regime": self.current_regime,
            "regime_counts": regime_counts,
            "total_ticks": len(self.regime_history)
        }