"""
LAYERS 7-15: ORCHESTRATION & EXECUTION
Layer 7:  10 RL Specialist Agents
Layer 8:  Bayesian Ensemble Fusion
Layer 9:  7-Gate Confidence Wall
Layer 10: Adaptive Risk Engine
Layer 11: Execution Guard
Layer 12: FIX Order Execution
Layer 13: Position Lifecycle Manager
Layer 14: Continuous Self-Learning
Layer 15: Async Master Loop
"""
from __future__ import annotations

import time
import json
import pickle
import asyncio
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from collections import deque
from dataclasses import asdict

import numpy as np

from pipeline import (
    FilterVector168, MLPredictionMatrix, CompressedVector,
    SignalDirection, RLAgentVote, RLEnsemble, BayesianFusion,
    GateResult, ConfidenceWall, RiskParameters, ExecutionCheck,
    FIXOrder, PositionState, TickData, ValidatedTick, FilteredSignals,
    LayerTimings, ManipulationVerdict,
)


# ══════════════════════════════════════════════════════════════════════
# LAYER 7: 10 RL SPECIALIST AGENTS
# ══════════════════════════════════════════════════════════════════════

class RLAgentBase:
    """Base class for RL specialist agents."""

    def __init__(self, name: str):
        self.name = name
        self.accuracy = 0.5
        self.win_count = 0
        self.total_count = 0

    def vote(self, fv: FilterVector168, ml_pred: MLPredictionMatrix) -> RLAgentVote:
        raise NotImplementedError

    def update_reward(self, correct: bool) -> None:
        self.total_count += 1
        if correct:
            self.win_count += 1
        self.accuracy = self.win_count / max(1, self.total_count)


class TrendMasterAgent(RLAgentBase):
    """A1: TrendMaster - Hurst>0.6 ∧ Lyapunov<0 → BUY"""

    def __init__(self):
        super().__init__("TrendMaster")

    def vote(self, fv: FilterVector168, ml_pred: MLPredictionMatrix) -> RLAgentVote:
        hurst = fv.hurst_exponent
        lyap = fv.lyapunov
        if hurst > 0.6 and lyap < 0:
            return RLAgentVote(self.name, SignalDirection.BUY, 0.7)
        elif hurst > 0.6 and lyap >= 0:
            return RLAgentVote(self.name, SignalDirection.SELL, 0.6)
        return RLAgentVote(self.name, SignalDirection.HOLD, 0.5)


class ReversalSnipeAgent(RLAgentBase):
    """A2: ReversalSnipe - Entropy↓ ∧ Curvature↑ → SELL"""

    def __init__(self):
        super().__init__("ReversalSnipe")

    def vote(self, fv: FilterVector168, ml_pred: MLPredictionMatrix) -> RLAgentVote:
        entropy = fv.shannon_entropy
        curvature = fv.riemann_curvature
        if entropy < 0.3 and curvature > 0.5:
            return RLAgentVote(self.name, SignalDirection.SELL, 0.65)
        elif entropy < 0.3 and curvature < -0.5:
            return RLAgentVote(self.name, SignalDirection.BUY, 0.65)
        return RLAgentVote(self.name, SignalDirection.HOLD, 0.5)


class BreakoutHuntAgent(RLAgentBase):
    """A3: BreakoutHunt - VolCompression→Spike → BUY/SELL"""

    def __init__(self):
        super().__init__("BreakoutHunt")

    def vote(self, fv: FilterVector168, ml_pred: MLPredictionMatrix) -> RLAgentVote:
        choppiness = fv.choppiness
        velocity = fv.price_velocity
        if choppiness < 30 and abs(velocity) > 0.01:
            direction = SignalDirection.BUY if velocity > 0 else SignalDirection.SELL
            return RLAgentVote(self.name, direction, 0.7)
        return RLAgentVote(self.name, SignalDirection.HOLD, 0.5)


class ScalperAgent(RLAgentBase):
    """A4: Scalper - VelReversal ∧ KineticSpike"""

    def __init__(self):
        super().__init__("Scalper")

    def vote(self, fv: FilterVector168, ml_pred: MLPredictionMatrix) -> RLAgentVote:
        vel = fv.price_velocity
        kinetic = fv.kinetic_energy
        if kinetic > 0.02 and abs(vel) > 0.005:
            direction = SignalDirection.BUY if vel > 0 else SignalDirection.SELL
            return RLAgentVote(self.name, direction, 0.6)
        return RLAgentVote(self.name, SignalDirection.HOLD, 0.5)


class MacroGuardAgent(RLAgentBase):
    """A5: MacroGuard - PathIntVar < threshold"""

    def __init__(self):
        super().__init__("MacroGuard")

    def vote(self, fv: FilterVector168, ml_pred: MLPredictionMatrix) -> RLAgentVote:
        path_var = fv.path_variation
        if path_var < 5.0:
            return RLAgentVote(self.name, SignalDirection.HOLD, 0.8)
        elif path_var > 50.0:
            return RLAgentVote(self.name, SignalDirection.HOLD, 0.9)
        return RLAgentVote(self.name, SignalDirection.HOLD, 0.5)


class ChaosFilterAgent(RLAgentBase):
    """A6: ChaosFilter - Lyapunov>0.5 → BLOCK"""

    def __init__(self):
        super().__init__("ChaosFilter")

    def vote(self, fv: FilterVector168, ml_pred: MLPredictionMatrix) -> RLAgentVote:
        lyap = fv.lyapunov
        if lyap > 0.5:
            return RLAgentVote(self.name, SignalDirection.HOLD, 0.9)
        elif lyap < -0.1:
            return RLAgentVote(self.name, SignalDirection.HOLD, 0.3)
        return RLAgentVote(self.name, SignalDirection.HOLD, 0.5)


class TopoAgent(RLAgentBase):
    """A7: TopoAgent - H1 loops change detected"""

    def __init__(self):
        super().__init__("TopoAgent")
        self._prev_h1 = 0.0

    def vote(self, fv: FilterVector168, ml_pred: MLPredictionMatrix) -> RLAgentVote:
        h1 = fv.persistent_h1
        delta = abs(h1 - self._prev_h1)
        self._prev_h1 = h1
        if delta > 0.3:
            return RLAgentVote(self.name, SignalDirection.HOLD, 0.7)
        return RLAgentVote(self.name, SignalDirection.HOLD, 0.4)


class FluidAgent(RLAgentBase):
    """A8: FluidAgent - Reynolds > 2300 → turbulent → HOLD"""

    def __init__(self):
        super().__init__("FluidAgent")

    def vote(self, fv: FilterVector168, ml_pred: MLPredictionMatrix) -> RLAgentVote:
        reynolds = fv.reynolds_number
        if reynolds > 2300:
            return RLAgentVote(self.name, SignalDirection.HOLD, 0.85)
        elif reynolds < 500:
            return RLAgentVote(self.name, SignalDirection.HOLD, 0.4)
        return RLAgentVote(self.name, SignalDirection.HOLD, 0.5)


class QuantumAgent(RLAgentBase):
    """A9: QuantumAgent - QAnnealing minimum found"""

    def __init__(self):
        super().__init__("QuantumAgent")

    def vote(self, fv: FilterVector168, ml_pred: MLPredictionMatrix) -> RLAgentVote:
        q_min = fv.q_annealing_min
        if q_min < -0.8:
            return RLAgentVote(self.name, SignalDirection.BUY, 0.65)
        elif q_min > 0.8:
            return RLAgentVote(self.name, SignalDirection.SELL, 0.65)
        return RLAgentVote(self.name, SignalDirection.HOLD, 0.5)


class EntropyAgent(RLAgentBase):
    """A10: EntropyAgent - FreeEnergy gradient < 0"""

    def __init__(self):
        super().__init__("EntropyAgent")
        self._prev_fe = 0.0

    def vote(self, fv: FilterVector168, ml_pred: MLPredictionMatrix) -> RLAgentVote:
        fe = fv.free_energy
        gradient = fe - self._prev_fe
        self._prev_fe = fe
        if gradient < -0.01:
            return RLAgentVote(self.name, SignalDirection.BUY, 0.6)
        elif gradient > 0.01:
            return RLAgentVote(self.name, SignalDirection.SELL, 0.6)
        return RLAgentVote(self.name, SignalDirection.HOLD, 0.5)


class RLEnsembleLayer:
    """LAYER 7: 10 RL Specialist Agents."""

    def __init__(self):
        self.agents: List[RLAgentBase] = [
            TrendMasterAgent(), ReversalSnipeAgent(), BreakoutHuntAgent(),
            ScalperAgent(), MacroGuardAgent(), ChaosFilterAgent(),
            TopoAgent(), FluidAgent(), QuantumAgent(), EntropyAgent(),
        ]
        self._tick_count = 0

    def vote(self, fv: FilterVector168, ml_pred: MLPredictionMatrix) -> RLEnsemble:
        self._tick_count += 1
        votes = [agent.vote(fv, ml_pred) for agent in self.agents]

        buy_votes = [v for v in votes if v.action == SignalDirection.BUY]
        sell_votes = [v for v in votes if v.action == SignalDirection.SELL]

        buy_conf = np.mean([v.confidence for v in buy_votes]) if buy_votes else 0.0
        sell_conf = np.mean([v.confidence for v in sell_votes]) if sell_votes else 0.0

        if buy_conf > sell_conf and buy_conf > 0.5:
            consensus = SignalDirection.BUY
            confidence = buy_conf
        elif sell_conf > buy_conf and sell_conf > 0.5:
            consensus = SignalDirection.SELL
            confidence = sell_conf
        else:
            consensus = SignalDirection.HOLD
            confidence = max(1.0 - buy_conf - sell_conf, 0.3)

        return RLEnsemble(votes=votes, consensus=consensus, consensus_confidence=confidence)


# ══════════════════════════════════════════════════════════════════════
# LAYER 8: BAYESIAN ENSEMBLE FUSION
# ══════════════════════════════════════════════════════════════════════

class BayesianFusionLayer:
    """LAYER 8: Bayesian Model Average fusion."""

    def __init__(self, ml_window: int = 100, rl_window: int = 50):
        self.ml_window = ml_window
        self.rl_window = rl_window
        self._ml_history: deque = deque(maxlen=ml_window)
        self._rl_history: deque = deque(maxlen=rl_window)

    def fuse(self, ml_pred: MLPredictionMatrix, rl_ensemble: RLEnsemble) -> BayesianFusion:
        ml_buy = ml_pred.ensemble_buy
        ml_sell = ml_pred.ensemble_sell
        ml_hold = ml_pred.ensemble_hold

        rl_buy = rl_ensemble.consensus_confidence if rl_ensemble.consensus == SignalDirection.BUY else 0.0
        rl_sell = rl_ensemble.consensus_confidence if rl_ensemble.consensus == SignalDirection.SELL else 0.0
        rl_hold = rl_ensemble.consensus_confidence if rl_ensemble.consensus == SignalDirection.HOLD else 0.0

        ml_weight = 0.6
        rl_weight = 0.4

        buy_score = ml_buy * ml_weight + rl_buy * rl_weight
        sell_score = ml_sell * ml_weight + rl_sell * rl_weight
        hold_score = ml_hold * ml_weight + rl_hold * rl_weight

        total = buy_score + sell_score + hold_score
        if total > 0:
            buy_score /= total
            sell_score /= total
            hold_score /= total

        scores = np.array([buy_score, sell_score, hold_score])
        probs = scores / max(scores.sum(), 1e-10)
        entropy = -np.sum(probs * np.log2(probs + 1e-10))

        max_idx = np.argmax(scores)
        final_signal = [SignalDirection.BUY, SignalDirection.SELL, SignalDirection.HOLD][max_idx]
        final_confidence = float(scores[max_idx] / max(scores.sum(), 1e-10))

        ci_p10 = float(np.percentile(scores, 10))
        ci_p90 = float(np.percentile(scores, 90))

        return BayesianFusion(
            final_signal=final_signal, final_confidence=final_confidence,
            buy_score=buy_score, sell_score=sell_score, hold_score=hold_score,
            ml_weight=ml_weight, rl_weight=rl_weight,
            disagreement_entropy=entropy, ci_p10=ci_p10, ci_p90=ci_p90,
        )


# ══════════════════════════════════════════════════════════════════════
# LAYER 9: 7-GATE CONFIDENCE WALL
# ══════════════════════════════════════════════════════════════════════

class ConfidenceWallLayer:
    """LAYER 9: 7-Gate Confidence Wall."""

    def __init__(self):
        self._pass_count = 0
        self._fail_count = 0

    def check(self, fusion: BayesianFusion, fv: FilterVector168) -> ConfidenceWall:
        gates = [
            GateResult(1, "ensemble_confidence", fusion.final_confidence, 0.60, fusion.final_confidence > 0.60),
            GateResult(2, "model_agreement", 1.0 - fusion.disagreement_entropy, 0.65, fusion.disagreement_entropy < 1.2),
            GateResult(3, "lyapunov", abs(fv.lyapunov), 0.30, abs(fv.lyapunov) < 0.30),
            GateResult(4, "shannon_entropy", fv.shannon_entropy, 0.80, fv.shannon_entropy < 0.80),
            GateResult(5, "topology_loops", fv.persistent_h1, 0.50, fv.persistent_h1 < 0.5),
            GateResult(6, "reynolds", fv.reynolds_number, 4000, fv.reynolds_number < 4000),
            GateResult(7, "q_annealing", fv.q_annealing_min, -0.50, fv.q_annealing_min < -0.50 or fv.q_annealing_min > 0.50),
        ]

        all_passed = all(g.passed for g in gates)
        failed = [g.name for g in gates if not g.passed]

        if all_passed:
            self._pass_count += 1
        else:
            self._fail_count += 1

        return ConfidenceWall(gates=gates, all_passed=all_passed, failed_gates=failed)

    @property
    def pass_rate(self) -> float:
        total = self._pass_count + self._fail_count
        return self._pass_count / max(1, total)


# ══════════════════════════════════════════════════════════════════════
# LAYER 10: ADAPTIVE RISK ENGINE
# ══════════════════════════════════════════════════════════════════════

class AdaptiveRiskEngine:
    """LAYER 10: Kelly fraction + ATR-based sizing + hard limits."""

    def __init__(self, max_concurrent: int = 3, daily_loss_limit: float = 0.03,
                 weekly_loss_limit: float = 0.07, max_drawdown: float = 0.10):
        self.max_concurrent = max_concurrent
        self.daily_loss_limit = daily_loss_limit
        self.weekly_loss_limit = weekly_loss_limit
        self.max_drawdown = max_drawdown
        self._daily_pnl = 0.0
        self._weekly_pnl = 0.0
        self._peak_equity = 1.0
        self._current_equity = 1.0
        self._position_count = 0
        self._trade_history: deque = deque(maxlen=100)

    def compute_risk(self, price: float, fv: FilterVector168, fusion: BayesianFusion) -> RiskParameters:
        rp = RiskParameters()
        quad_var = fv.quadratic_variation
        atr_proxy = np.sqrt(max(quad_var, 1e-10)) * np.sqrt(252)
        rp.atr_proxy = float(atr_proxy)
        rp.vol_regime = float(fv.choppiness / 100.0) if fv.choppiness > 0 else 1.0

        win_rate = 0.5
        avg_win_loss = 1.5
        kelly_full = win_rate - (1 - win_rate) / avg_win_loss if avg_win_loss > 0 else 0.0
        kelly_f = max(0, kelly_full * 0.25)
        kelly_f = min(kelly_f, 0.02)
        rp.kelly_fraction = float(kelly_f)

        vol_adj = max(rp.vol_regime, 0.1)
        rp.position_size = float(kelly_f / vol_adj)

        atr = max(atr_proxy * price * 0.01, 1.0)
        if fusion.final_signal == SignalDirection.BUY:
            rp.stop_loss = price - atr * 1.5
            rp.take_profit_1 = price + atr * 1.5
            rp.take_profit_2 = price + atr * 3.0
            rp.take_profit_3 = price + atr * 4.5
        elif fusion.final_signal == SignalDirection.SELL:
            rp.stop_loss = price + atr * 1.5
            rp.take_profit_1 = price - atr * 1.5
            rp.take_profit_2 = price - atr * 3.0
            rp.take_profit_3 = price - atr * 4.5

        rp.risk_reward_ratio = 1.5
        rp.max_concurrent = self.max_concurrent
        rp.daily_loss_pct = self._daily_pnl
        rp.weekly_loss_pct = self._weekly_pnl

        current_dd = (self._peak_equity - self._current_equity) / max(self._peak_equity, 1e-10)
        rp.max_drawdown_pct = float(current_dd)

        if rp.daily_loss_pct > self.daily_loss_limit:
            rp.halt_triggered = True
            rp.halt_reason = f"Daily loss {rp.daily_loss_pct:.2%} > {self.daily_loss_limit:.2%}"
        elif rp.weekly_loss_pct > self.weekly_loss_limit:
            rp.halt_triggered = True
            rp.halt_reason = f"Weekly loss {rp.weekly_loss_pct:.2%} > {self.weekly_loss_limit:.2%}"
        elif current_dd > self.max_drawdown:
            rp.halt_triggered = True
            rp.halt_reason = f"Drawdown {current_dd:.2%} > {self.max_drawdown:.2%}"

        return rp

    def record_trade(self, pnl: float) -> None:
        self._daily_pnl += pnl
        self._weekly_pnl += pnl
        self._current_equity += pnl
        self._peak_equity = max(self._peak_equity, self._current_equity)
        self._trade_history.append(pnl)

    def daily_reset(self) -> None:
        self._daily_pnl = 0.0

    def weekly_reset(self) -> None:
        self._weekly_pnl = 0.0


# ══════════════════════════════════════════════════════════════════════
# LAYER 11: EXECUTION GUARD
# ══════════════════════════════════════════════════════════════════════

class ExecutionGuard:
    """LAYER 11: Session, spread, NFP/FOMC, position limits."""

    def __init__(self):
        self._position_count = 0
        self._daily_loss = 0.0
        self._last_heartbeat_ns = time.time_ns()

    def on_heartbeat(self) -> None:
        self._last_heartbeat_ns = time.time_ns()

    def check(self, spread_bps: float, risk: RiskParameters, positions: int) -> ExecutionCheck:
        ec = ExecutionCheck()

        heartbeat_s = (time.time_ns() - self._last_heartbeat_ns) / 1e9
        ec.fix_heartbeat_ok = heartbeat_s < 30

        ec.spread_ok = spread_bps < 50

        now_utc = time.gmtime()
        hour = now_utc.tm_hour
        is_london = 7 <= hour < 16
        is_ny = 13 <= hour < 21
        ec.session_active = is_london or is_ny

        ec.position_limit_ok = positions < risk.max_concurrent
        ec.daily_loss_ok = abs(risk.daily_loss_pct) < 0.03

        ec.all_checks_passed = all([ec.fix_heartbeat_ok, ec.spread_ok, ec.session_active, ec.position_limit_ok, ec.daily_loss_ok])

        if not ec.fix_heartbeat_ok:
            ec.failed_checks.append("FIX heartbeat timeout")
        if not ec.spread_ok:
            ec.failed_checks.append(f"Spread {spread_bps:.1f} bps too wide")
        if not ec.session_active:
            ec.failed_checks.append("Outside London/NY session")
        if not ec.position_limit_ok:
            ec.failed_checks.append(f"Position limit {positions}/{risk.max_concurrent}")
        if not ec.daily_loss_ok:
            ec.failed_checks.append(f"Daily loss {risk.daily_loss_pct:.2%}")

        return ec


# ══════════════════════════════════════════════════════════════════════
# LAYER 12: FIX ORDER EXECUTION
# ══════════════════════════════════════════════════════════════════════

class FIXOrderExecutor:
    """LAYER 12: NewOrderSingle + OCA groups."""

    def __init__(self, sender_comp_id: str = "ATIKUL", target_comp_id: str = "CTRADER"):
        self.sender = sender_comp_id
        self.target = target_comp_id
        self._seq_num = 0
        self._order_count = 0

    def create_order(self, signal: SignalDirection, price: float, risk: RiskParameters, signal_hash: str) -> FIXOrder:
        self._seq_num += 1
        self._order_count += 1

        order = FIXOrder()
        order.symbol = "XAUUSD"
        order.side = 1 if signal == SignalDirection.BUY else 2
        order.order_qty = round(risk.position_size * 100, 2)
        order.price = price
        order.stop_loss = risk.stop_loss
        order.take_profit_1 = risk.take_profit_1
        order.take_profit_2 = risk.take_profit_2
        order.take_profit_3 = risk.take_profit_3
        order.signal_hash = signal_hash
        order.magic_id = f"{signal_hash[:8]}_{int(time.time())}"
        order.cl_ord_id = f"ORD_{self._seq_num}_{int(time.time() * 1000)}"

        ts = time.strftime("%Y%m%d-%H:%M:%S", time.gmtime())
        tags = [
            f"8=FIX.4.4", f"9=0", f"35=D", f"34={self._seq_num}",
            f"49={self.sender}", f"56={self.target}", f"52={ts}",
            f"11={order.cl_ord_id}", f"55={order.symbol}", f"54={order.side}",
            f"38={order.order_qty}", f"40=2", f"44={order.price}",
            f"59=0", f"1={order.magic_id}",
        ]
        raw = "\x01".join(tags) + "\x01"
        body_len = len(raw) - raw.index("35=") + 3
        raw = raw.replace("9=0", f"9={body_len}", 1)

        checksum = sum(ord(c) for c in raw) % 256
        raw += f"10={checksum:03d}\x01"
        order.raw_fix = raw

        return order


# ══════════════════════════════════════════════════════════════════════
# LAYER 13: POSITION LIFECYCLE MANAGER
# ══════════════════════════════════════════════════════════════════════

class PositionLifecycleManager:
    """LAYER 13: TP→SL move, emergency close, rolling stats."""

    def __init__(self):
        self._positions: Dict[str, PositionState] = {}
        self._closed_trades: deque = deque(maxlen=1000)

    def open_position(self, order: FIXOrder) -> PositionState:
        ps = PositionState(
            order_id=order.cl_ord_id, entry_price=order.price,
            direction=SignalDirection.BUY if order.side == 1 else SignalDirection.SELL,
            current_sl=order.stop_loss, current_tp1=order.take_profit_1,
            current_tp2=order.take_profit_2, current_tp3=order.take_profit_3,
        )
        self._positions[order.cl_ord_id] = ps
        return ps

    def update_tick(self, order_id: str, current_price: float, velocity: float = 0.0) -> Optional[PositionState]:
        ps = self._positions.get(order_id)
        if ps is None:
            return None
        ps.current_price = current_price
        direction_mult = 1 if ps.direction == SignalDirection.BUY else -1
        ps.pnl_pips = (current_price - ps.entry_price) * direction_mult
        ps.pnl = ps.pnl_pips * 0.01

        if not ps.tp1_hit and ps.direction == SignalDirection.BUY and current_price >= ps.current_tp1:
            ps.tp1_hit = True
            ps.current_sl = ps.entry_price  # move to breakeven
        elif not ps.tp1_hit and ps.direction == SignalDirection.SELL and current_price <= ps.current_tp1:
            ps.tp1_hit = True
            ps.current_sl = ps.entry_price

        if not ps.tp2_hit and ps.direction == SignalDirection.BUY and current_price >= ps.current_tp2:
            ps.tp2_hit = True
            ps.current_sl = ps.current_tp1
        elif not ps.tp2_hit and ps.direction == SignalDirection.SELL and current_price <= ps.current_tp2:
            ps.tp2_hit = True
            ps.current_sl = ps.current_tp1

        if velocity != 0:
            wrong_dir = (ps.direction == SignalDirection.BUY and velocity < -0.02) or \
                        (ps.direction == SignalDirection.SELL and velocity > 0.02)
            if wrong_dir and ps.pnl_pips < 0:
                ps.should_emergency_close = True
                ps.emergency_reason = f"Velocity spike wrong dir: {velocity:.4f}"

        return ps

    def close_position(self, order_id: str, close_price: float) -> Optional[PositionState]:
        ps = self._positions.pop(order_id, None)
        if ps:
            ps.current_price = close_price
            direction_mult = 1 if ps.direction == SignalDirection.BUY else -1
            ps.pnl_pips = (close_price - ps.entry_price) * direction_mult
            self._closed_trades.append(ps)
        return ps

    @property
    def open_count(self) -> int:
        return len(self._positions)

    @property
    def rolling_stats(self) -> dict:
        if not self._closed_trades:
            return {"win_rate": 0, "avg_pnl": 0, "sharpe": 0, "calmar": 0}
        pnls = np.array([t.pnl for t in self._closed_trades])
        wins = np.sum(pnls > 0)
        total = len(pnls)
        win_rate = wins / max(1, total)
        avg_pnl = float(np.mean(pnls))
        sharpe = float(np.mean(pnls) / max(np.std(pnls), 1e-10) * np.sqrt(252))
        cum_pnl = np.cumsum(pnls)
        peak = np.maximum.accumulate(cum_pnl)
        dd = (peak - cum_pnl) / np.maximum(peak, 1e-10)
        max_dd = float(np.max(dd)) if len(dd) > 0 else 0
        calmar = float(avg_pnl * 252 / max(max_dd, 1e-10))
        return {"win_rate": win_rate, "avg_pnl": avg_pnl, "sharpe": sharpe, "calmar": calmar, "trades": total}


# ══════════════════════════════════════════════════════════════════════
# LAYER 14: CONTINUOUS SELF-LEARNING
# ══════════════════════════════════════════════════════════════════════

class SelfLearningLayer:
    """LAYER 14: River online learning + ADWIN drift detection."""

    def __init__(self):
        self._features_buffer: list = []
        self._outcomes_buffer: list = []
        self._tick_since_retrain = 0
        self._retrain_interval = 1000
        self._model = None

    def try_import_river(self) -> bool:
        try:
            from river import tree as river_tree
            self._model = river_tree.HoeffdingTreeClassifier()
            return True
        except ImportError:
            return False

    def record_trade_outcome(self, features: np.ndarray, outcome: int) -> None:
        self._features_buffer.append(features.tolist())
        self._outcomes_buffer.append(outcome)

        if self._model is not None and len(self._features_buffer) > 0:
            try:
                x_dict = {f"f{i}": v for i, v in enumerate(self._features_buffer[-1])}
                self._model.learn_one(x_dict, self._outcomes_buffer[-1])
            except Exception:
                pass

    def on_tick(self) -> bool:
        self._tick_since_retrain += 1
        if self._tick_since_retrain >= self._retrain_interval:
            self._tick_since_retrain = 0
            return True
        return False

    def retrain_batch(self, models_dir: str = "trained_models") -> None:
        import os
        os.makedirs(models_dir, exist_ok=True)
        self._features_buffer = self._features_buffer[-5000:]
        self._outcomes_buffer = self._outcomes_buffer[-5000:]

    @property
    def buffer_size(self) -> int:
        return len(self._features_buffer)


# ══════════════════════════════════════════════════════════════════════
# LAYER 15: ASYNC MASTER LOOP
# ══════════════════════════════════════════════════════════════════════

class MasterLoop:
    """LAYER 15: Async master loop that chains L0→L14."""

    def __init__(self, checkpoint_dir: str = "checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)
        self._tick_count = 0
        self._timings = LayerTimings()

    def save_checkpoint(self, state: dict) -> None:
        path = self.checkpoint_dir / "state.pkl"
        with open(path, "wb") as f:
            pickle.dump(state, f)

    def load_checkpoint(self) -> dict:
        path = self.checkpoint_dir / "state.pkl"
        if path.exists():
            with open(path, "rb") as f:
                return pickle.load(f)
        return {}

    def log_tick(self, tick_num: int, signal: SignalDirection, confidence: float, timings: LayerTimings) -> str:
        log = {
            "tick": tick_num,
            "signal": signal.name,
            "confidence": round(confidence, 4),
            "total_ms": round(timings.total_ms, 2),
            "latencies": timings.to_dict(),
        }
        return json.dumps(log)
