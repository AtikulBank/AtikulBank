"""
Cybernetic Homeostasis Loop

Real-time monitoring and adaptive control system.
Maintains system stability through feedback loops.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum
import time
from collections import deque
import warnings

warnings.filterwarnings("ignore")


class SystemState(Enum):
    """System states for homeostasis control."""
    NORMAL = "normal"
    STRESSED = "stressed"
    CRITICAL = "critical"
    RECOVERING = "recovering"


class AlertLevel(Enum):
    """Alert levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class SystemMetrics:
    """System performance metrics."""
    timestamp: float
    cpu_usage: float
    memory_usage: float
    latency_ns: float
    throughput: float
    error_rate: float
    confluence_score: float
    turbulence_index: float


class CyberneticHomeostasisLoop:
    """
    Cybernetic Homeostasis Loop
    
    Maintains system stability through feedback loops.
    Dynamically adjusts parameters based on real-time conditions.
    """
    
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        
        # System state
        self.system_state = SystemState.NORMAL
        self.alert_level = AlertLevel.INFO
        
        # Historical metrics
        self.metrics_history = deque(maxlen=window_size)
        self.alert_history = deque(maxlen=window_size)
        
        # Control parameters
        self.target_confluence = 850.0
        self.max_turbulence = 0.7
        self.max_latency_ns = 1000.0
        
        # Adaptive parameters
        self.adaptive_params = {
            'confluence_threshold': 850.0,
            'turbulence_limit': 0.7,
            'latency_limit': 1000.0,
            'error_rate_limit': 0.01
        }
        
        # Homeostasis gains
        self.gains = {
            'proportional': 1.0,
            'integral': 0.1,
            'derivative': 0.05
        }
        
        # Error history for integral term
        self.error_history = deque(maxlen=100)
        
        # Performance metrics
        self.performance = {
            'stability_score': 1.0,
            'recovery_count': 0,
            'emergency_count': 0,
            'avg_recovery_time': 0.0
        }
        
    def update_metrics(self, metrics: SystemMetrics) -> Dict[str, Any]:
        """
        Update system metrics and compute homeostasis response.
        """
        # Store metrics
        self.metrics_history.append(metrics)
        
        # Compute system health
        health = self._compute_system_health(metrics)
        
        # Determine system state
        new_state = self._determine_system_state(health)
        
        # Generate alerts if needed
        alerts = self._generate_alerts(metrics, health)
        
        # Compute adaptive adjustments
        adjustments = self._compute_adaptive_adjustments(health)
        
        # Update system state
        if new_state != self.system_state:
            self._handle_state_transition(self.system_state, new_state)
            self.system_state = new_state
        
        # Update performance metrics
        self._update_performance_metrics()
        
        return {
            'health': health,
            'system_state': self.system_state.value,
            'alert_level': self.alert_level.value,
            'alerts': alerts,
            'adjustments': adjustments,
            'performance': self.performance.copy()
        }
    
    def _compute_system_health(self, metrics: SystemMetrics) -> float:
        """
        Compute overall system health score (0-1).
        """
        health_scores = []
        
        # Confluence score health
        confluence_health = min(metrics.confluence_score / 1000.0, 1.0)
        health_scores.append(confluence_health)
        
        # Latency health (lower is better)
        latency_health = max(0, 1.0 - metrics.latency_ns / 10000.0)
        health_scores.append(latency_health)
        
        # Error rate health (lower is better)
        error_health = max(0, 1.0 - metrics.error_rate * 100)
        health_scores.append(error_health)
        
        # Turbulence health (lower is better)
        turbulence_health = max(0, 1.0 - metrics.turbulence_index)
        health_scores.append(turbulence_health)
        
        # Weighted average
        weights = [0.4, 0.3, 0.2, 0.1]
        health = sum(w * s for w, s in zip(weights, health_scores))
        
        return min(max(health, 0.0), 1.0)
    
    def _determine_system_state(self, health: float) -> SystemState:
        """Determine system state based on health."""
        if health > 0.8:
            return SystemState.NORMAL
        elif health > 0.5:
            return SystemState.STRESSED
        elif health > 0.2:
            return SystemState.CRITICAL
        else:
            return SystemState.RECOVERING
    
    def _generate_alerts(self, metrics: SystemMetrics, health: float) -> List[Dict]:
        """Generate alerts based on metrics."""
        alerts = []
        
        # Confluence score alert
        if metrics.confluence_score < self.adaptive_params['confluence_threshold']:
            alerts.append({
                'level': AlertLevel.WARNING.value,
                'message': f"Confluence score {metrics.confluence_score:.2f} below threshold",
                'metric': 'confluence_score',
                'value': metrics.confluence_score,
                'threshold': self.adaptive_params['confluence_threshold']
            })
        
        # Latency alert
        if metrics.latency_ns > self.adaptive_params['latency_limit']:
            alerts.append({
                'level': AlertLevel.CRITICAL.value,
                'message': f"Latency {metrics.latency_ns:.2f} ns exceeds limit",
                'metric': 'latency_ns',
                'value': metrics.latency_ns,
                'threshold': self.adaptive_params['latency_limit']
            })
        
        # Turbulence alert
        if metrics.turbulence_index > self.adaptive_params['turbulence_limit']:
            alerts.append({
                'level': AlertLevel.WARNING.value,
                'message': f"Turbulence index {metrics.turbulence_index:.4f} exceeds limit",
                'metric': 'turbulence_index',
                'value': metrics.turbulence_index,
                'threshold': self.adaptive_params['turbulence_limit']
            })
        
        # Error rate alert
        if metrics.error_rate > self.adaptive_params['error_rate_limit']:
            alerts.append({
                'level': AlertLevel.CRITICAL.value,
                'message': f"Error rate {metrics.error_rate:.4f} exceeds limit",
                'metric': 'error_rate',
                'value': metrics.error_rate,
                'threshold': self.adaptive_params['error_rate_limit']
            })
        
        # Store alerts
        for alert in alerts:
            self.alert_history.append(alert)
        
        # Update alert level
        if alerts:
            max_level = max(alert['level'] for alert in alerts)
            self.alert_level = AlertLevel(max_level)
        
        return alerts
    
    def _compute_adaptive_adjustments(self, health: float) -> Dict[str, float]:
        """
        Compute adaptive parameter adjustments using PID control.
        """
        # Error from target health
        error = 1.0 - health
        self.error_history.append(error)
        
        # PID terms
        proportional = error * self.gains['proportional']
        
        # Integral term
        if len(self.error_history) > 0:
            integral = np.mean(list(self.error_history)) * self.gains['integral']
        else:
            integral = 0.0
        
        # Derivative term
        if len(self.error_history) > 1:
            derivative = (error - list(self.error_history)[-2]) * self.gains['derivative']
        else:
            derivative = 0.0
        
        # Total adjustment
        adjustment = proportional + integral + derivative
        
        # Adjust parameters based on health
        adjustments = {
            'confluence_threshold': max(700, min(900, self.target_confluence - adjustment * 100)),
            'turbulence_limit': max(0.3, min(0.9, self.max_turbulence + adjustment * 0.1)),
            'latency_limit': max(500, min(2000, self.max_latency_ns - adjustment * 200)),
            'error_rate_limit': max(0.001, min(0.1, 0.01 + adjustment * 0.01))
        }
        
        # Update adaptive parameters
        self.adaptive_params.update(adjustments)
        
        return adjustments
    
    def _handle_state_transition(self, old_state: SystemState, new_state: SystemState):
        """Handle system state transitions."""
        if new_state == SystemState.RECOVERING:
            self.performance['recovery_count'] += 1
        
        if new_state == SystemState.CRITICAL:
            self.performance['emergency_count'] += 1
    
    def _update_performance_metrics(self):
        """Update performance metrics."""
        if len(self.metrics_history) > 0:
            # Compute stability score
            recent_health = []
            for metrics in list(self.metrics_history)[-100:]:
                health = self._compute_system_health(metrics)
                recent_health.append(health)
            
            self.performance['stability_score'] = np.mean(recent_health)
    
    def get_recommendation(self) -> Dict[str, Any]:
        """Get homeostasis recommendation."""
        if self.system_state == SystemState.NORMAL:
            return {
                'action': 'CONTINUE',
                'confidence': 0.9,
                'reason': 'System operating normally'
            }
        elif self.system_state == SystemState.STRESSED:
            return {
                'action': 'REDUCE_LOAD',
                'confidence': 0.7,
                'reason': 'System under stress'
            }
        elif self.system_state == SystemState.CRITICAL:
            return {
                'action': 'HALT_TRADING',
                'confidence': 0.95,
                'reason': 'System in critical state'
            }
        else:  # RECOVERING
            return {
                'action': 'GRADUAL_RECOVERY',
                'confidence': 0.6,
                'reason': 'System recovering from critical state'
            }
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for TUI dashboard."""
        return {
            'system_state': self.system_state.value,
            'alert_level': self.alert_level.value,
            'stability_score': self.performance['stability_score'],
            'recovery_count': self.performance['recovery_count'],
            'emergency_count': self.performance['emergency_count'],
            'adaptive_params': self.adaptive_params.copy(),
            'recent_alerts': list(self.alert_history)[-5:],
            'recommendation': self.get_recommendation()
        }


# Main execution function for testing
if __name__ == "__main__":
    print("=" * 70)
    print("CYBERNETIC HOMEOSTASIS LOOP TEST")
    print("=" * 70)
    
    # Create homeostasis loop
    homeostasis = CyberneticHomeostasisLoop()
    
    # Simulate system metrics
    np.random.seed(42)
    n_updates = 100
    
    for i in range(n_updates):
        # Create random metrics
        metrics = SystemMetrics(
            timestamp=time.time(),
            cpu_usage=np.random.uniform(0.3, 0.9),
            memory_usage=np.random.uniform(0.4, 0.8),
            latency_ns=np.random.uniform(100, 2000),
            throughput=np.random.uniform(1000, 5000),
            error_rate=np.random.uniform(0, 0.05),
            confluence_score=np.random.uniform(600, 950),
            turbulence_index=np.random.uniform(0, 0.9)
        )
        
        # Update homeostasis
        result = homeostasis.update_metrics(metrics)
    
    # Get final dashboard data
    dashboard = homeostasis.get_dashboard_data()
    
    print(f"\nFinal System State: {dashboard['system_state']}")
    print(f"Alert Level: {dashboard['alert_level']}")
    print(f"Stability Score: {dashboard['stability_score']:.4f}")
    print(f"Recovery Count: {dashboard['recovery_count']}")
    print(f"Emergency Count: {dashboard['emergency_count']}")
    
    print(f"\nRecommendation: {dashboard['recommendation']['action']}")
    print(f"Reason: {dashboard['recommendation']['reason']}")
    
    print(f"\nAdaptive Parameters:")
    for param, value in dashboard['adaptive_params'].items():
        print(f"  {param}: {value:.4f}")
    
    print("\n" + "=" * 70)
    print("HOMEOSTASIS TEST COMPLETED SUCCESSFULLY")
    print("=" * 70)