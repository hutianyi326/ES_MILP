"""Synthetic-only joint DA/IDA/aFRR MILP.

The implementation follows ``model/es_perfect_information_design_20260920.md``
draft 4. Optional frozen-order, remaining-budget and terminal-value arguments
are the window kernel used by rolling.py; default calls remain full-joint.
It has no real-data reader or post-hoc pressure report.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from calendar import isleap
from importlib.metadata import PackageNotFoundError, version as package_version
from math import isfinite
from typing import Mapping, Sequence
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import numpy as np


SYNTHETIC_MARKET_PREFIX = "ES_SYNTHETIC_MARKET_"
HISTORICAL_CONDITIONAL_PREFIX = "ES_HISTORICAL_CONDITIONAL_"
DATA_SCOPES = {"synthetic", "historical_conditional"}
_TOL = 1e-9
REQUIRED_TZDATA_VERSION = "2026.4"


def _canonical_trade_mw(value: float) -> float:
    """Remove <=1e-9 MW solver overflow at 0/100, not input-data clipping."""
    value = float(value)
    if not isfinite(value) or value < -_TOL or value > 100.0 + _TOL:
        raise ValueError("solver trade materially outside [0,100] MW")
    return min(100.0, max(0.0, value))


def _canonical_net_trade_mw(value: float) -> float:
    """Remove <=1e-9 MW solver overflow at the signed contract bounds."""
    value = float(value)
    if not isfinite(value) or value < -100.0 - _TOL or value > 100.0 + _TOL:
        raise ValueError("solver net trade materially outside [-100,100] MW")
    return min(100.0, max(-100.0, value))


def _finite(value: float, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _utc_datetime(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _required_madrid_timezone() -> ZoneInfo:
    """Enforce the reproducible synthetic Madrid/DST environment gate."""

    try:
        installed = package_version("tzdata")
    except PackageNotFoundError as exc:
        raise ValueError("tzdata==2026.4 is required; refusing a silent UTC fallback") from exc
    if installed != REQUIRED_TZDATA_VERSION:
        raise ValueError(f"tzdata=={REQUIRED_TZDATA_VERSION} is required, found {installed}")
    try:
        return ZoneInfo("Europe/Madrid")
    except ZoneInfoNotFoundError as exc:
        raise ValueError("Europe/Madrid is unavailable; refusing a silent UTC fallback") from exc


@dataclass(frozen=True)
class QHInput:
    """One synthetic 15-minute delivery period.

    ``madrid_year`` is explicit so this synthetic core does not silently
    infer a local year from UTC.  Real Spain input will require the separate
    Europe/Madrid/tzdata ingestion gate.
    """

    qh_id: str
    start_utc: datetime
    end_utc: datetime
    segment_id: str
    madrid_year: int
    alpha_up: float
    alpha_down: float
    afrr_capacity_price_up_eur_per_mw_qh: float = 0.0
    afrr_capacity_price_down_eur_per_mw_qh: float = 0.0
    afrr_activation_price_up_eur_per_mwh: float = 0.0
    afrr_activation_price_down_eur_per_mwh: float = 0.0
    afrr_gate_close_utc: datetime | None = None
    afrr_result_release_utc: datetime | None = None

    def __post_init__(self) -> None:
        if not self.qh_id or not self.segment_id:
            raise ValueError("qh_id and segment_id must be non-empty")
        start = _utc_datetime(self.start_utc, "start_utc")
        end = _utc_datetime(self.end_utc, "end_utc")
        if end <= start or abs((end - start).total_seconds() / 3600.0 - 0.25) > _TOL:
            raise ValueError("synthetic QH must be exactly 15 minutes")
        if start.minute % 15 or start.second or start.microsecond:
            raise ValueError("QH must start on the UTC quarter-hour grid")
        if not isinstance(self.madrid_year, int) or self.madrid_year < 2000:
            raise ValueError("madrid_year must be an integer year")
        a_up = _finite(self.alpha_up, "alpha_up")
        a_down = _finite(self.alpha_down, "alpha_down")
        if a_up < 0 or a_down < 0 or a_up > 1 or a_down > 1 or a_up + a_down > 1:
            raise ValueError("activation strengths must be in [0,1] and sum to at most 1")
        for name in (
            "afrr_capacity_price_up_eur_per_mw_qh",
            "afrr_capacity_price_down_eur_per_mw_qh",
            "afrr_activation_price_up_eur_per_mwh",
            "afrr_activation_price_down_eur_per_mwh",
        ):
            _finite(getattr(self, name), name)
        if (self.afrr_gate_close_utc is None) != (self.afrr_result_release_utc is None):
            raise ValueError("aFRR gate and result events must be supplied together")
        if self.afrr_gate_close_utc is not None:
            gate = _utc_datetime(self.afrr_gate_close_utc, "afrr_gate_close_utc")
            result = _utc_datetime(self.afrr_result_release_utc, "afrr_result_release_utc")
            if not (gate <= result <= start):
                raise ValueError("require aFRR gate_close <= result_release <= delivery_start")
            object.__setattr__(self, "afrr_gate_close_utc", gate)
            object.__setattr__(self, "afrr_result_release_utc", result)

        object.__setattr__(self, "start_utc", start)
        object.__setattr__(self, "end_utc", end)
        object.__setattr__(self, "alpha_up", a_up)
        object.__setattr__(self, "alpha_down", a_down)

    @property
    def duration_hours(self) -> float:
        return 0.25


@dataclass(frozen=True)
class ContractInput:
    """One synthetic DA or IDA contract mapped to one or more QHs."""

    contract_id: str
    market: str
    gate_close_utc: datetime
    result_release_utc: datetime
    delivery_start_utc: datetime
    delivery_end_utc: datetime
    price_eur_per_mwh: float
    qh_weights: Mapping[str, float]

    def __post_init__(self) -> None:
        if not self.contract_id:
            raise ValueError("contract_id must be non-empty")
        if self.market not in {"DA", "IDA"}:
            raise ValueError("market must be DA or IDA")
        gate = _utc_datetime(self.gate_close_utc, "gate_close_utc")
        result = _utc_datetime(self.result_release_utc, "result_release_utc")
        delivery_start = _utc_datetime(self.delivery_start_utc, "delivery_start_utc")
        delivery_end = _utc_datetime(self.delivery_end_utc, "delivery_end_utc")
        if not (gate <= result <= delivery_start < delivery_end):
            raise ValueError("require gate_close <= result_release <= delivery_start < delivery_end")
        _finite(self.price_eur_per_mwh, "price_eur_per_mwh")
        if not self.qh_weights:
            raise ValueError("qh_weights must not be empty")
        for qh_id, weight in self.qh_weights.items():
            if not isinstance(qh_id, str) or not qh_id:
                raise ValueError("qh_weights keys must be non-empty strings")
            weight = _finite(weight, f"qh_weights[{qh_id}]")
            if weight < 0 or weight > 1:
                raise ValueError("qh weights must be in [0,1]")
        object.__setattr__(self, "gate_close_utc", gate)
        object.__setattr__(self, "result_release_utc", result)
        object.__setattr__(self, "delivery_start_utc", delivery_start)
        object.__setattr__(self, "delivery_end_utc", delivery_end)


@dataclass(frozen=True)
class FixedCommitment:
    """Already frozen synthetic commitment carried into a joint solve."""

    qh_id: str
    baseline_mw: float = 0.0
    reserve_up_mw: float = 0.0
    reserve_down_mw: float = 0.0
    fixed_energy_cash_eur: float = 0.0
    status: str = "awarded"

    def __post_init__(self) -> None:
        if not self.qh_id:
            raise ValueError("fixed commitment qh_id must be non-empty")
        for name in ("baseline_mw", "reserve_up_mw", "reserve_down_mw", "fixed_energy_cash_eur"):
            _finite(getattr(self, name), name)
        if abs(self.baseline_mw) > 100 + _TOL:
            raise ValueError("fixed baseline must be within +/-100 MW")
        if self.reserve_up_mw < 0 or self.reserve_down_mw < 0:
            raise ValueError("fixed reserves must be non-negative")
        if self.reserve_up_mw > 100 + _TOL or self.reserve_down_mw > 100 + _TOL:
            raise ValueError("fixed reserves are capped at 100 MW per direction")
        if self.status not in {"awarded", "pending"}:
            raise ValueError("fixed commitment status must be awarded or pending")


@dataclass(frozen=True)
class SyntheticMarketInput:
    """Validated input for the full-joint core.

    The default remains the historical synthetic development scope.  The
    explicitly labelled conditional scope is accepted only with its own
    input-id namespace and a provenance marker; this prevents a real-data
    adapter from silently masquerading as a synthetic regression fixture.
    """

    qhs: tuple[QHInput, ...]
    contracts: tuple[ContractInput, ...]
    fixed_commitments: tuple[FixedCommitment, ...] = ()
    annual_efc_budget: Mapping[int, float] = field(default_factory=dict)
    charge_mw: float = 100.0
    discharge_mw: float = 100.0
    grid_import_mw: float = 100.0
    grid_export_mw: float = 100.0
    e_min_mwh: float = 10.0
    e_max_mwh: float = 190.0
    e_initial_mwh: float = 10.0
    e_terminal_mwh: float = 10.0
    eta_charge: float = 0.92
    eta_discharge: float = 0.92
    reserve_limit_up_mw: float = 100.0
    reserve_limit_down_mw: float = 100.0
    input_id: str = ""
    data_scope: str = "synthetic"
    research_provenance: str = ""

    def __post_init__(self) -> None:
        madrid_tz = _required_madrid_timezone()
        if self.data_scope not in DATA_SCOPES:
            raise ValueError("data_scope must be synthetic or historical_conditional")
        if self.data_scope == "synthetic":
            if not self.input_id.startswith(SYNTHETIC_MARKET_PREFIX):
                raise ValueError("synthetic market input_id must start with ES_SYNTHETIC_MARKET_")
        else:
            if not self.input_id.startswith(HISTORICAL_CONDITIONAL_PREFIX):
                raise ValueError("historical_conditional input_id must start with ES_HISTORICAL_CONDITIONAL_")
            if not isinstance(self.research_provenance, str) or not self.research_provenance.strip():
                raise ValueError("historical_conditional input requires research_provenance")
        if not self.qhs:
            raise ValueError("qhs must not be empty")
        qh_ids = [q.qh_id for q in self.qhs]
        if len(set(qh_ids)) != len(qh_ids):
            raise ValueError("qh_id values must be unique")
        if list(self.qhs) != sorted(self.qhs, key=lambda q: q.start_utc):
            raise ValueError("qhs must be supplied in global chronological order")
        by_segment: dict[str, list[QHInput]] = {}
        for qh in self.qhs:
            if qh.afrr_gate_close_utc is None or qh.afrr_result_release_utc is None:
                raise ValueError("each synthetic QH must carry aFRR gate/result events")
            if qh.start_utc.astimezone(madrid_tz).year != qh.madrid_year:
                raise ValueError(f"qh {qh.qh_id} madrid_year does not match Europe/Madrid")
            by_segment.setdefault(qh.segment_id, []).append(qh)
        all_by_time = sorted(self.qhs, key=lambda q: q.start_utc)
        for previous, current in zip(all_by_time, all_by_time[1:]):
            if current.start_utc < previous.end_utc:
                raise ValueError("QH delivery intervals must not overlap globally")
        for segment, rows in by_segment.items():
            for previous, current in zip(rows, rows[1:]):
                if current.start_utc <= previous.start_utc or current.start_utc != previous.end_utc:
                    raise ValueError(f"segment {segment} must be contiguous; gaps belong in another segment")
        segment_start = {segment: rows[0].start_utc for segment, rows in by_segment.items()}
        contract_ids = [c.contract_id for c in self.contracts]
        if len(set(contract_ids)) != len(contract_ids):
            raise ValueError("contract_id values must be unique")
        qh_map = {q.qh_id: q for q in self.qhs}
        qh_id_set = set(qh_map)
        for contract in self.contracts:
            unknown = set(contract.qh_weights) - qh_id_set
            if unknown:
                raise ValueError(f"contract {contract.contract_id} maps unknown QHs: {sorted(unknown)}")
            mapped_qhs = [qh_map[qid] for qid, weight in contract.qh_weights.items() if float(weight) > 0]
            if any(q.start_utc < contract.delivery_start_utc or q.end_utc > contract.delivery_end_utc for q in mapped_qhs):
                raise ValueError(f"contract {contract.contract_id} maps outside its delivery interval")
            if len({q.segment_id for q in mapped_qhs}) > 1:
                raise ValueError(f"contract {contract.contract_id} cannot cross synthetic segments or gaps")
            mapped_hours = sum(qh_map[qid].duration_hours * float(weight) for qid, weight in contract.qh_weights.items())
            contract_hours = (contract.delivery_end_utc - contract.delivery_start_utc).total_seconds() / 3600.0
            if abs(mapped_hours - contract_hours) > 1e-8:
                raise ValueError(f"contract {contract.contract_id} QH mapping does not conserve duration")
        fixed_ids = [f.qh_id for f in self.fixed_commitments]
        if len(fixed_ids) != len(set(fixed_ids)):
            raise ValueError("one fixed commitment record is required per QH")
        if set(fixed_ids) - qh_id_set:
            raise ValueError("fixed commitment references unknown QH")
        for commitment in self.fixed_commitments:
            if commitment.reserve_up_mw > self.reserve_limit_up_mw + _TOL or commitment.reserve_down_mw > self.reserve_limit_down_mw + _TOL:
                raise ValueError("fixed reserve exceeds the configured per-direction limit")
        for name in (
            "charge_mw", "discharge_mw", "grid_import_mw", "grid_export_mw",
            "e_min_mwh", "e_max_mwh", "e_initial_mwh", "e_terminal_mwh",
            "eta_charge", "eta_discharge", "reserve_limit_up_mw", "reserve_limit_down_mw",
        ):
            _finite(getattr(self, name), name)
        if min(self.charge_mw, self.discharge_mw, self.grid_import_mw, self.grid_export_mw) < 0:
            raise ValueError("power limits must be non-negative")
        if not (0 <= self.e_min_mwh < self.e_max_mwh):
            raise ValueError("require 0 <= e_min_mwh < e_max_mwh")
        if not (self.e_min_mwh <= self.e_initial_mwh <= self.e_max_mwh):
            raise ValueError("initial energy must be within bounds")
        if not (self.e_min_mwh <= self.e_terminal_mwh <= self.e_max_mwh):
            raise ValueError("terminal energy must be within bounds")
        if not (0 < self.eta_charge <= 1 and 0 < self.eta_discharge <= 1):
            raise ValueError("efficiencies must be in (0,1]")
        if self.reserve_limit_up_mw < 0 or self.reserve_limit_down_mw < 0:
            raise ValueError("reserve limits must be non-negative")
        years = {q.madrid_year for q in self.qhs}
        for year in years:
            if year not in self.annual_efc_budget:
                raise ValueError(f"missing annual EFC budget for synthetic year {year}")
            budget = _finite(self.annual_efc_budget[year], f"annual_efc_budget[{year}]")
            if budget < 0 or budget > 600 + _TOL:
                raise ValueError("annual EFC budgets must be in [0,600]; coverage-derived or tighter test budgets only")
        if set(self.annual_efc_budget) - years:
            raise ValueError("annual budget contains a year with no QH")

    @property
    def qh_by_id(self) -> dict[str, QHInput]:
        return {q.qh_id: q for q in self.qhs}

    @property
    def fixed_by_qh(self) -> dict[str, FixedCommitment]:
        return {f.qh_id: f for f in self.fixed_commitments}

    @property
    def cycle_denominator_mwh(self) -> float:
        return 2.0 * (self.e_max_mwh - self.e_min_mwh)

    @property
    def coverage_derived_efc_budget(self) -> dict[int, float]:
        """Sum valid/actual duration per Madrid day, then prorate 600 EFC."""
        madrid_tz = _required_madrid_timezone()
        by_day: dict[object, float] = {}
        for q in self.qhs:
            day = q.start_utc.astimezone(madrid_tz).date()
            by_day[day] = by_day.get(day, 0.0) + q.duration_hours
        covered: dict[int, float] = {q.madrid_year: 0.0 for q in self.qhs}
        for day, valid_hours in by_day.items():
            start = datetime(day.year, day.month, day.day, tzinfo=madrid_tz)
            actual_hours = ((start + timedelta(days=1)).astimezone(timezone.utc)
                            - start.astimezone(timezone.utc)).total_seconds() / 3600.0
            covered[day.year] += 600.0 * (valid_hours / actual_hours) / (366 if isleap(day.year) else 365)
        return covered

    @property
    def effective_annual_efc_budget(self) -> dict[int, float]:
        """The tighter of the user cap and covered-local-time cap."""

        coverage = self.coverage_derived_efc_budget
        return {year: min(float(self.annual_efc_budget[year]), coverage[year]) for year in coverage}

    def new_order_allowed(self, event_time: datetime, segment_id: str) -> bool:
        """Whether a new order event is inside the modeled segment boundary."""

        segment_start = min(q.start_utc for q in self.qhs if q.segment_id == segment_id)
        return event_time >= segment_start


@dataclass(frozen=True)
class SyntheticMarketResult:
    order_mode: str
    success: bool
    status: int
    message: str
    objective_gross_eur: float | None
    solver_objective_min_eur: float | None
    qh_baseline_mw: Mapping[str, float]
    reserve_up_mw: Mapping[str, float]
    reserve_down_mw: Mapping[str, float]
    soc_trace_mwh: Mapping[str, tuple[float, ...]]
    qh_power_trace_mw: Mapping[str, tuple[float, ...]]
    cash_breakdown_eur: Mapping[str, float]
    residuals: Mapping[str, float]
    absolute_gap_eur: float | None
    relative_gap: float | None
    raw_solver_gap: float | None
    input_id: str
    feasible: bool = False
    proven_optimal: bool = False
    contract_trades: tuple[Mapping[str, object], ...] = ()
    profit_upper_bound_eur: float | None = None
    salvage_eur: float = 0.0
    objective_eur: float | None = None
    data_scope: str = "synthetic"
    research_provenance: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "order_mode": self.order_mode,
            "success": self.success,
            "status": self.status,
            "message": self.message,
            "objective_gross_eur": self.objective_gross_eur,
            "solver_objective_min_eur": self.solver_objective_min_eur,
            "qh_baseline_mw": dict(self.qh_baseline_mw),
            "reserve_up_mw": dict(self.reserve_up_mw),
            "reserve_down_mw": dict(self.reserve_down_mw),
            "soc_trace_mwh": {key: list(value) for key, value in self.soc_trace_mwh.items()},
            "qh_power_trace_mw": {key: list(value) for key, value in self.qh_power_trace_mw.items()},
            "cash_breakdown_eur": dict(self.cash_breakdown_eur),
            "residuals": dict(self.residuals),
            "absolute_gap_eur": self.absolute_gap_eur,
            "relative_gap": self.relative_gap,
            "raw_solver_gap": self.raw_solver_gap,
            "input_id": self.input_id,
            "feasible": self.feasible,
            "proven_optimal": self.proven_optimal,
            "contract_trades": [dict(row) for row in self.contract_trades],
            "profit_upper_bound_eur": self.profit_upper_bound_eur,
            "salvage_eur": self.salvage_eur,
            "objective_eur": self.objective_eur,
            "data_scope": self.data_scope,
            "research_provenance": self.research_provenance,
        }


@dataclass(frozen=True)
class _Step:
    qh_index: int
    qh_id: str
    phase: str
    duration_hours: float


def _build_steps(inp: SyntheticMarketInput, order_mode: str) -> list[_Step]:
    if order_mode not in {"U", "D"}:
        raise ValueError("order_mode must be U or D")
    steps: list[_Step] = []
    for i, qh in enumerate(inp.qhs):
        phases = (
            (("up", qh.alpha_up), ("down", qh.alpha_down), ("idle", 1 - (qh.alpha_up + qh.alpha_down)))
            if order_mode == "U" else
            (("down", qh.alpha_down), ("up", qh.alpha_up), ("idle", 1 - (qh.alpha_up + qh.alpha_down)))
        )
        for phase, fraction in phases:
            if fraction == 0.0:
                continue
            steps.append(_Step(i, qh.qh_id, phase, 0.25 * fraction))
    if not steps:
        raise ValueError("at least one positive-duration synthetic substep is required")
    return steps


def _fixed_cash_total(inp: SyntheticMarketInput) -> float:
    """Cash already attached to frozen commitments, counted once."""

    total = sum(f.fixed_energy_cash_eur for f in inp.fixed_commitments)
    fixed = inp.fixed_by_qh
    for qh in inp.qhs:
        commitment = fixed.get(qh.qh_id)
        if commitment is None:
            continue
        total += qh.afrr_capacity_price_up_eur_per_mw_qh * commitment.reserve_up_mw
        total += qh.afrr_capacity_price_down_eur_per_mw_qh * commitment.reserve_down_mw
        total += qh.afrr_activation_price_up_eur_per_mwh * commitment.reserve_up_mw * 0.25 * qh.alpha_up
        total += qh.afrr_activation_price_down_eur_per_mwh * commitment.reserve_down_mw * 0.25 * qh.alpha_down
    return float(total)


def solve_joint(
    inp: SyntheticMarketInput,
    order_mode: str = "U",
    *,
    time_limit_seconds: float = 60.0,
    mip_rel_gap: float = 1e-4,
    presolve: bool = False,
    terminal_hard: bool = True,
    salvage_price_eur_per_mwh: float = 0.0,
    terminal_reference_mwh: float | None = None,
    fixed_spot_mw: Mapping[str, tuple[float, float]] | None = None,
    fixed_reserve_mw: Mapping[str, tuple[float, float]] | None = None,
    remaining_annual_efc: Mapping[int, float] | None = None,
) -> SyntheticMarketResult:
    """Solve one full-joint synthetic order path with SciPy/HiGHS.

    This function is deliberately synthetic-only and has no file or network
    input.  It returns both the modeled gross objective and independent audit
    residuals.  Rolling execution and real event persistence are later work.
    """

    if not isfinite(float(time_limit_seconds)) or time_limit_seconds <= 0:
        raise ValueError("time_limit_seconds must be positive and finite")
    if not isfinite(float(mip_rel_gap)) or mip_rel_gap < 0:
        raise ValueError("mip_rel_gap must be non-negative and finite")
    if not isinstance(presolve, bool):
        raise ValueError("presolve must be boolean")
    if not isinstance(terminal_hard, bool):
        raise ValueError("terminal_hard must be boolean")
    if not isfinite(float(salvage_price_eur_per_mwh)) or salvage_price_eur_per_mwh < 0:
        raise ValueError("salvage_price_eur_per_mwh must be finite and non-negative")
    terminal_reference = inp.e_terminal_mwh if terminal_reference_mwh is None else float(terminal_reference_mwh)
    if not inp.e_min_mwh <= terminal_reference <= inp.e_max_mwh:
        raise ValueError("terminal_reference_mwh must be within energy bounds")
    steps = _build_steps(inp, order_mode)
    qhs = inp.qhs
    contracts = inp.contracts
    # Local indexes keep the public immutable input free of mutable caches.
    qh_map = inp.qh_by_id
    qh_index = {q.qh_id: i for i, q in enumerate(qhs)}
    segment_start: dict[str, datetime] = {}
    for qh in qhs:
        segment_start.setdefault(qh.segment_id, qh.start_utc)
    fixed = inp.fixed_by_qh
    fixed_for_qh = {qh.qh_id: fixed.get(qh.qh_id, FixedCommitment(qh.qh_id)) for qh in qhs}
    frozen_spot = dict(fixed_spot_mw or {})
    frozen_reserve = dict(fixed_reserve_mw or {})
    budget_limits = dict(inp.effective_annual_efc_budget if remaining_annual_efc is None else remaining_annual_efc)
    if set(budget_limits) != {q.madrid_year for q in qhs}:
        raise ValueError("remaining annual budget years must match the window")
    if any(not isfinite(float(v)) or not 0 <= v <= 600 for v in budget_limits.values()):
        raise ValueError("remaining annual budget must be finite in [0,600]")
    if set(frozen_spot) - {c.contract_id for c in contracts} or set(frozen_reserve) - {q.qh_id for q in qhs}:
        raise ValueError("frozen order outside modeled window")
    for key, pair in list(frozen_spot.items()) + list(frozen_reserve.items()):
        if len(pair) != 2 or any(not isfinite(float(v)) or not 0 <= v <= 100 for v in pair):
            raise ValueError("invalid frozen order MW")
    if any(s > 1e-7 and b > 1e-7 for s,b in frozen_spot.values()):
        raise ValueError("frozen spot order cannot buy and sell simultaneously")
    try:
        from scipy.optimize import Bounds, LinearConstraint, milp
        from scipy.sparse import lil_matrix
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("SciPy is required; use the project .venv-es-milp environment") from exc

    # Logical market quantities may be constants or compact solver variables.
    # A contract's old (sell,buy,mode) projection is exactly one signed net MW
    # quantity in [-100,100].  Positive is sell and negative is buy.
    n_contracts = len(contracts)
    n_qh = len(qhs)
    n_steps = len(steps)
    contract_segments: list[set[str]] = []
    contract_events_by_qh: dict[str, dict[datetime, list[tuple[int, float]]]] = {
        q.qh_id: {} for q in qhs
    }
    contract_cash_coeff = np.zeros(n_contracts)
    for j, contract in enumerate(contracts):
        mapped_segments: set[str] = set()
        for qh_id, weight in contract.qh_weights.items():
            if float(weight) <= 0:
                continue
            mapped_segments.add(qh_map[qh_id].segment_id)
            contract_cash_coeff[j] += contract.price_eur_per_mwh * qh_map[qh_id].duration_hours * float(weight)
            contract_events_by_qh[qh_id].setdefault(contract.result_release_utc, []).append((j, float(weight)))
        contract_segments.append(mapped_segments)

    lower_list: list[float] = []
    upper_list: list[float] = []
    objective_list: list[float] = []
    integrality_list: list[int] = []

    def allocate(lo: float, hi: float, coefficient: float = 0.0, integer: bool = False) -> int:
        index = len(lower_list)
        lower_list.append(float(lo))
        upper_list.append(float(hi))
        objective_list.append(float(coefficient))
        integrality_list.append(1 if integer else 0)
        return index

    net_index = np.full(n_contracts, -1, dtype=int)
    net_fixed = np.zeros(n_contracts)
    frozen_sell = np.zeros(n_contracts)
    frozen_buy = np.zeros(n_contracts)
    objective_offset = 0.0
    forced_infeasible = False
    for j, contract in enumerate(contracts):
        mapped_segments = contract_segments[j]
        eligible = len(mapped_segments) == 1 and contract.gate_close_utc >= segment_start[next(iter(mapped_segments))]
        if contract.contract_id in frozen_spot:
            frozen_sell[j], frozen_buy[j] = map(float, frozen_spot[contract.contract_id])
            net_fixed[j] = frozen_sell[j] - frozen_buy[j]
            objective_offset += -contract_cash_coeff[j] * net_fixed[j]
            # The old binary mode made every exactly simultaneous fixed pair
            # infeasible, including pairs below the input validation tolerance.
            forced_infeasible |= frozen_sell[j] > 0.0 and frozen_buy[j] > 0.0
        elif eligible:
            net_index[j] = allocate(-100.0, 100.0, -contract_cash_coeff[j])

    reserve_up_coeff = np.array([
        -(qh.afrr_capacity_price_up_eur_per_mw_qh + qh.afrr_activation_price_up_eur_per_mwh * 0.25 * qh.alpha_up)
        for qh in qhs
    ])
    reserve_down_coeff = np.array([
        -(qh.afrr_capacity_price_down_eur_per_mw_qh + qh.afrr_activation_price_down_eur_per_mwh * 0.25 * qh.alpha_down)
        for qh in qhs
    ])
    reserve_up_index = np.full(n_qh, -1, dtype=int)
    reserve_down_index = np.full(n_qh, -1, dtype=int)
    reserve_up_fixed = np.zeros(n_qh)
    reserve_down_fixed = np.zeros(n_qh)
    reserve_up_limit = np.zeros(n_qh)
    reserve_down_limit = np.zeros(n_qh)
    for i, qh in enumerate(qhs):
        fc = fixed_for_qh[qh.qh_id]
        reserve_up_limit[i] = inp.reserve_limit_up_mw - fc.reserve_up_mw
        reserve_down_limit[i] = inp.reserve_limit_down_mw - fc.reserve_down_mw
        eligible = qh.qh_id in frozen_reserve or qh.afrr_gate_close_utc >= segment_start[qh.segment_id]
        if qh.qh_id in frozen_reserve:
            up_value, down_value = map(float, frozen_reserve[qh.qh_id])
            up_valid = 0.0 <= up_value <= reserve_up_limit[i] and up_value == round(up_value)
            down_valid = 0.0 <= down_value <= reserve_down_limit[i] and down_value == round(down_value)
            if up_valid:
                reserve_up_fixed[i] = up_value
                objective_offset += reserve_up_coeff[i] * up_value
            else:
                reserve_up_index[i] = allocate(up_value, up_value, reserve_up_coeff[i], integer=True)
            if down_valid:
                reserve_down_fixed[i] = down_value
                objective_offset += reserve_down_coeff[i] * down_value
            else:
                reserve_down_index[i] = allocate(down_value, down_value, reserve_down_coeff[i], integer=True)
        elif eligible:
            if reserve_up_limit[i] < 0.0:
                forced_infeasible = True
            elif reserve_up_limit[i] > 0.0:
                reserve_up_index[i] = allocate(0.0, reserve_up_limit[i], reserve_up_coeff[i], integer=True)
            if reserve_down_limit[i] < 0.0:
                forced_infeasible = True
            elif reserve_down_limit[i] > 0.0:
                reserve_down_index[i] = allocate(0.0, reserve_down_limit[i], reserve_down_coeff[i], integer=True)

    # Physical power can never exceed the corresponding grid direction, so
    # these bounds are at least as tight as the nameplate bounds.  Keep the
    # physical variable structure unchanged in this net-contract revision.
    charge_bound = min(inp.charge_mw, inp.grid_import_mw)
    discharge_bound = min(inp.discharge_mw, inp.grid_export_mw)
    charge_index = np.full(n_steps, -1, dtype=int)
    discharge_index = np.full(n_steps, -1, dtype=int)
    operation_mode_index = np.full(n_steps, -1, dtype=int)
    soc_index = np.full(n_steps, -1, dtype=int)
    for s in range(n_steps):
        charge_index[s] = allocate(0.0, charge_bound)
        discharge_index[s] = allocate(0.0, discharge_bound)
        operation_mode_index[s] = allocate(0.0, 1.0, integer=True)
        soc_index[s] = allocate(inp.e_min_mwh, inp.e_max_mwh)

    step_indices_by_segment: dict[str, list[int]] = {}
    for s, step in enumerate(steps):
        step_indices_by_segment.setdefault(qhs[step.qh_index].segment_id, []).append(s)
    terminal_steps = [indices[-1] for indices in step_indices_by_segment.values()]
    if not terminal_hard and salvage_price_eur_per_mwh:
        for last_step in terminal_steps:
            objective_list[int(soc_index[last_step])] -= float(salvage_price_eur_per_mwh)

    # Eliminated fixed decisions must remain in HiGHS' objective.  A single
    # fixed-one anchor preserves the old objective value, relative-gap
    # denominator, and minimization-side dual-bound scale exactly.
    if objective_offset != 0.0:
        allocate(1.0, 1.0, objective_offset)

    nvar = len(lower_list)
    objective = np.asarray(objective_list, dtype=float)
    lower = np.asarray(lower_list, dtype=float)
    upper = np.asarray(upper_list, dtype=float)
    integrality = np.asarray(integrality_list, dtype=int)

    rows: list[tuple[dict[int, float], float, float]] = []

    def add(row: Mapping[int, float], lo: float, hi: float) -> None:
        rows.append((dict(row), float(lo), float(hi)))

    def add_logical(terms: Sequence[tuple[int, float, float]], lo: float, hi: float) -> None:
        row: dict[int, float] = {}
        constant = 0.0
        for index, fixed_value, coefficient in terms:
            if index >= 0:
                row[index] = row.get(index, 0.0) + coefficient
            else:
                constant += coefficient * fixed_value
        add(row, lo - constant, hi - constant)

    if forced_infeasible:
        add({}, 1.0, 0.0)

    # Contract-to-QH baseline coefficient map, in logical net-MW space.
    qh_market_terms: dict[str, list[tuple[int, float]]] = {q.qh_id: [] for q in qhs}
    for j, contract in enumerate(contracts):
        for qh_id, weight in contract.qh_weights.items():
            qh_market_terms[qh_id].append((j, float(weight)))

    # Each delivery QH has its own cumulative MW position. Simultaneous
    # results form one node; contract IDs never create artificial chronology.
    for qh in qhs:
        fixed_base = fixed_for_qh[qh.qh_id].baseline_mw
        cumulative_terms: list[tuple[int, float, float]] = []
        event_times = sorted(contract_events_by_qh[qh.qh_id])
        for event_time in event_times:
            for j, weight in contract_events_by_qh[qh.qh_id][event_time]:
                cumulative_terms.append((int(net_index[j]), float(net_fixed[j]), weight))
            add_logical(cumulative_terms, -100.0 - fixed_base, 100.0 - fixed_base)

    # Baseline, QH reserve headroom, and per-step physical power equations.
    for i, qh in enumerate(qhs):
        fc = fixed_for_qh[qh.qh_id]
        base_terms = [
            (int(net_index[j]), float(net_fixed[j]), coefficient)
            for j, coefficient in qh_market_terms[qh.qh_id]
        ]
        add_logical(
            base_terms + [(int(reserve_up_index[i]), float(reserve_up_fixed[i]), 1.0)],
            -np.inf,
            inp.grid_export_mw - fc.baseline_mw - fc.reserve_up_mw,
        )
        add_logical(
            [(index, value, -coefficient) for index, value, coefficient in base_terms]
            + [(int(reserve_down_index[i]), float(reserve_down_fixed[i]), 1.0)],
            -np.inf,
            inp.grid_import_mw + fc.baseline_mw - fc.reserve_down_mw,
        )
        # Invalid fixed integer reserves remain fixed integer variables so
        # HiGHS returns infeasible exactly as under the old formulation.
        if reserve_up_index[i] >= 0 and lower[reserve_up_index[i]] == upper[reserve_up_index[i]]:
            add({int(reserve_up_index[i]): 1.0}, -np.inf, reserve_up_limit[i])
        if reserve_down_index[i] >= 0 and lower[reserve_down_index[i]] == upper[reserve_down_index[i]]:
            add({int(reserve_down_index[i]): 1.0}, -np.inf, reserve_down_limit[i])

    for s, step in enumerate(steps):
        if operation_mode_index[s] >= 0:
            add({int(charge_index[s]): 1.0, int(operation_mode_index[s]): charge_bound}, -np.inf, charge_bound)
            add({int(discharge_index[s]): 1.0, int(operation_mode_index[s]): -discharge_bound}, -np.inf, 0.0)
        qh = qhs[step.qh_index]
        fc = fixed_for_qh[qh.qh_id]
        power_terms = [
            (int(discharge_index[s]), 0.0, 1.0),
            (int(charge_index[s]), 0.0, -1.0),
        ] + [
            (int(net_index[j]), float(net_fixed[j]), -coefficient)
            for j, coefficient in qh_market_terms[qh.qh_id]
        ]
        if step.phase == "up":
            power_terms.append((int(reserve_up_index[step.qh_index]), float(reserve_up_fixed[step.qh_index]), -1.0))
            rhs = fc.baseline_mw + fc.reserve_up_mw
        elif step.phase == "down":
            power_terms.append((int(reserve_down_index[step.qh_index]), float(reserve_down_fixed[step.qh_index]), 1.0))
            rhs = fc.baseline_mw - fc.reserve_down_mw
        else:
            rhs = fc.baseline_mw
        add_logical(power_terms, rhs, rhs)

    # SOC recursion and segment boundary conditions.
    previous_step_by_segment: dict[str, int | None] = {}
    for s, step in enumerate(steps):
        qh = qhs[step.qh_index]
        soc_terms = [
            (int(soc_index[s]), 0.0, 1.0),
            (int(charge_index[s]), 0.0, -inp.eta_charge * step.duration_hours),
            (int(discharge_index[s]), 0.0, step.duration_hours / inp.eta_discharge),
        ]
        previous = previous_step_by_segment.get(qh.segment_id)
        if previous is None:
            add_logical(soc_terms, inp.e_initial_mwh, inp.e_initial_mwh)
        else:
            soc_terms.append((int(soc_index[previous]), 0.0, -1.0))
            add_logical(soc_terms, 0.0, 0.0)
        previous_step_by_segment[qh.segment_id] = s
    if terminal_hard:
        for last_step in terminal_steps:
            add({int(soc_index[last_step]): 1.0}, inp.e_terminal_mwh, inp.e_terminal_mwh)

    # Annual DC-throughput budget shared across all segments in a year.  The
    # effective limit is additionally capped by the fraction of the local
    # Madrid year actually covered by the synthetic input.
    for year, budget in budget_limits.items():
        row: dict[int, float] = {}
        for s, step in enumerate(steps):
            if inp.qhs[step.qh_index].madrid_year == year:
                if charge_index[s] >= 0:
                    row[int(charge_index[s])] = row.get(int(charge_index[s]), 0.0) + inp.eta_charge * step.duration_hours / inp.cycle_denominator_mwh
                if discharge_index[s] >= 0:
                    row[int(discharge_index[s])] = row.get(int(discharge_index[s]), 0.0) + step.duration_hours / inp.eta_discharge / inp.cycle_denominator_mwh
        add(row, -np.inf, float(budget))

    matrix = lil_matrix((len(rows), nvar), dtype=float)
    row_lb = np.empty(len(rows)); row_ub = np.empty(len(rows))
    for r, (entries, lo, hi) in enumerate(rows):
        for column, value in entries.items():
            matrix[r, column] = value
        row_lb[r] = lo; row_ub[r] = hi
    result = milp(
        c=objective,
        integrality=integrality,
        bounds=Bounds(lower, upper),
        constraints=LinearConstraint(matrix.tocsr(), row_lb, row_ub),
        options={
            "presolve": bool(presolve),
            "time_limit": float(time_limit_seconds),
            "mip_rel_gap": float(mip_rel_gap),
        },
    )
    fixed_cash = _fixed_cash_total(inp)
    if result.x is None:
        return SyntheticMarketResult(
            order_mode=order_mode, success=False, status=int(result.status), message=str(result.message),
            objective_gross_eur=None, solver_objective_min_eur=None, qh_baseline_mw={}, reserve_up_mw={},
            reserve_down_mw={}, soc_trace_mwh={}, qh_power_trace_mw={}, cash_breakdown_eur={}, residuals={},
            absolute_gap_eur=None, relative_gap=None, raw_solver_gap=None, input_id=inp.input_id,
            feasible=False, proven_optimal=False,
            data_scope=inp.data_scope, research_provenance=inp.research_provenance,
        )

    # A solver may return a tiny overflow at an exact trade bound.
    # Canonicalize only this numerical overflow before cash/audit/persistence.
    # Never change raw prices, activation ratios, or a materially invalid trade.
    x = result.x.copy()
    trade_bound_adjustment = 0.0
    for idx in net_index[net_index >= 0]:
        old = float(x[idx])
        x[idx] = _canonical_net_trade_mw(old)
        trade_bound_adjustment = max(trade_bound_adjustment, abs(old-x[idx]))
    for idx in np.concatenate((reserve_up_index[reserve_up_index >= 0], reserve_down_index[reserve_down_index >= 0])):
        old = float(x[idx])
        x[idx] = _canonical_trade_mw(old)
        trade_bound_adjustment = max(trade_bound_adjustment, abs(old-x[idx]))

    def logical_values(indices: np.ndarray, fixed_values: np.ndarray) -> np.ndarray:
        return np.array([
            float(x[index]) if index >= 0 else float(fixed_values[i])
            for i, index in enumerate(indices)
        ])

    net_values = logical_values(net_index, net_fixed)
    reserve_up_values = logical_values(reserve_up_index, reserve_up_fixed)
    reserve_down_values = logical_values(reserve_down_index, reserve_down_fixed)
    sell_values = np.maximum(net_values, 0.0)
    buy_values = np.maximum(-net_values, 0.0)
    for j, contract in enumerate(contracts):
        if contract.contract_id in frozen_spot:
            sell_values[j] = frozen_sell[j]
            buy_values[j] = frozen_buy[j]

    baseline_out: dict[str, float] = {}
    up_out: dict[str, float] = {}
    down_out: dict[str, float] = {}
    cash_energy = 0.0
    cash_energy_by_market = {"DA": 0.0, "IDA": 0.0}
    for j, contract in enumerate(contracts):
        contract_cash = contract.price_eur_per_mwh * net_values[j] * sum(
            qh_map[qid].duration_hours * float(weight) for qid, weight in contract.qh_weights.items()
        )
        cash_energy += contract_cash
        cash_energy_by_market[contract.market] += contract_cash
    for qh_i, qh in enumerate(qhs):
        base = fixed_for_qh[qh.qh_id].baseline_mw + sum(coef * net_values[j] for j, coef in qh_market_terms[qh.qh_id])
        baseline_out[qh.qh_id] = float(base)
        up_out[qh.qh_id] = float(fixed_for_qh[qh.qh_id].reserve_up_mw + reserve_up_values[qh_i])
        down_out[qh.qh_id] = float(fixed_for_qh[qh.qh_id].reserve_down_mw + reserve_down_values[qh_i])
    cap_cash = sum(qh.afrr_capacity_price_up_eur_per_mw_qh * up_out[qh.qh_id] + qh.afrr_capacity_price_down_eur_per_mw_qh * down_out[qh.qh_id] for qh in qhs)
    act_cash = sum(
        qh.afrr_activation_price_up_eur_per_mwh * up_out[qh.qh_id] * 0.25 * qh.alpha_up
        + qh.afrr_activation_price_down_eur_per_mwh * down_out[qh.qh_id] * 0.25 * qh.alpha_down
        for qh in qhs
    )
    gross = cash_energy + cap_cash + act_cash + sum(f.fixed_energy_cash_eur for f in inp.fixed_commitments)
    salvage = 0.0
    if not terminal_hard and salvage_price_eur_per_mwh:
        salvage = float(salvage_price_eur_per_mwh) * sum(float(x[soc_index[last]]) - terminal_reference for last in terminal_steps)
    objective_value = gross + salvage
    soc_by_segment: dict[str, list[float]] = {}
    power_by_qh: dict[str, list[float]] = {}
    for s, step in enumerate(steps):
        soc_by_segment.setdefault(qhs[step.qh_index].segment_id, []).append(float(x[soc_index[s]]))
        power_by_qh.setdefault(step.qh_id, []).append(float(x[discharge_index[s]] - x[charge_index[s]]))

    # Rebuild the former logical layout for the independent algebra audit.
    # The audit remains intentionally formulation-independent and continues to
    # verify buy/sell mutual exclusion, original cash, and all physical rules.
    legacy_cursor = 0
    sell = np.arange(legacy_cursor, legacy_cursor + n_contracts); legacy_cursor += n_contracts
    buy = np.arange(legacy_cursor, legacy_cursor + n_contracts); legacy_cursor += n_contracts
    contract_mode = np.arange(legacy_cursor, legacy_cursor + n_contracts); legacy_cursor += n_contracts
    reserve_up = np.arange(legacy_cursor, legacy_cursor + n_qh); legacy_cursor += n_qh
    reserve_down = np.arange(legacy_cursor, legacy_cursor + n_qh); legacy_cursor += n_qh
    charge = np.arange(legacy_cursor, legacy_cursor + n_steps); legacy_cursor += n_steps
    discharge = np.arange(legacy_cursor, legacy_cursor + n_steps); legacy_cursor += n_steps
    operation_mode = np.arange(legacy_cursor, legacy_cursor + n_steps); legacy_cursor += n_steps
    soc = np.arange(legacy_cursor, legacy_cursor + n_steps); legacy_cursor += n_steps
    audit_x = np.zeros(legacy_cursor)
    audit_x[sell] = sell_values
    audit_x[buy] = buy_values
    audit_x[contract_mode] = (buy_values > 0.0).astype(float)
    audit_x[reserve_up] = reserve_up_values
    audit_x[reserve_down] = reserve_down_values
    audit_x[charge] = x[charge_index]
    audit_x[discharge] = x[discharge_index]
    audit_x[operation_mode] = x[operation_mode_index]
    audit_x[soc] = x[soc_index]
    audit_qh_market_terms: dict[str, list[tuple[int, float]]] = {qh.qh_id: [] for qh in qhs}
    for qh_id, terms in qh_market_terms.items():
        for j, coefficient in terms:
            audit_qh_market_terms[qh_id].append((int(sell[j]), coefficient))
            audit_qh_market_terms[qh_id].append((int(buy[j]), -coefficient))
    residuals = _audit_solution(inp, order_mode, audit_x, steps, audit_qh_market_terms, sell, buy, contract_mode, reserve_up, reserve_down, charge, discharge, operation_mode, soc, baseline_out, up_out, down_out, gross, float(result.fun), terminal_hard=terminal_hard, objective_value=objective_value, objective_constant=(0.0 if terminal_hard else float(salvage_price_eur_per_mwh) * terminal_reference * len(terminal_steps)), frozen_spot=frozen_spot, frozen_reserve=frozen_reserve, budget_limits=budget_limits)
    ax = matrix.tocsr() @ x
    residuals["all_variable_bounds_max"] = float(max(0.0, np.max(lower-x), np.max(x-upper)))
    residuals["all_linear_rows_max"] = float(max(0.0, np.max(row_lb-ax), np.max(ax-row_ub)))
    integers = x[integrality != 0]
    residuals["all_integer_variables_max"] = float(np.max(np.abs(integers-np.rint(integers)), initial=0.0))
    residuals["trade_bound_canonicalization_max_mw"] = trade_bound_adjustment
    if max(residuals[k] for k in ("all_variable_bounds_max", "all_linear_rows_max", "all_integer_variables_max")) > 1e-5:
        raise AssertionError("synthetic solver vector fails complete algebraic feasibility audit")
    # HiGHS reports a minimization-side mip gap.  Convert only the numeric bounds if available.
    raw_gap = float(getattr(result, "mip_gap", 0.0)) if getattr(result, "mip_gap", None) is not None else None
    dual = getattr(result, "mip_dual_bound", None)
    absolute_gap = None
    relative_gap = None
    profit_upper = None
    if dual is not None and isfinite(float(dual)):
        objective_constant = 0.0 if terminal_hard else float(salvage_price_eur_per_mwh) * terminal_reference * len(terminal_steps)
        profit_upper = fixed_cash - float(dual) - objective_constant
        absolute_gap = float(profit_upper - objective_value)
        relative_gap = absolute_gap / max(1.0, abs(objective_value))
    fixed_energy_cash = sum(f.fixed_energy_cash_eur for f in inp.fixed_commitments)
    fixed_reserve_cash = fixed_cash - fixed_energy_cash
    cap_new_cash = cap_cash - sum(
        qh.afrr_capacity_price_up_eur_per_mw_qh * fixed_for_qh[qh.qh_id].reserve_up_mw
        + qh.afrr_capacity_price_down_eur_per_mw_qh * fixed_for_qh[qh.qh_id].reserve_down_mw
        for qh in qhs
    )
    act_new_cash = act_cash - sum(
        qh.afrr_activation_price_up_eur_per_mwh * fixed_for_qh[qh.qh_id].reserve_up_mw * 0.25 * qh.alpha_up
        + qh.afrr_activation_price_down_eur_per_mwh * fixed_for_qh[qh.qh_id].reserve_down_mw * 0.25 * qh.alpha_down
        for qh in qhs
    )
    return SyntheticMarketResult(
        order_mode,
        True,
        int(result.status),
        str(result.message),
        gross,
        float(result.fun),
        baseline_out,
        up_out,
        down_out,
        {k: tuple(v) for k, v in soc_by_segment.items()},
        {k: tuple(v) for k, v in power_by_qh.items()},
        {
            "DA_energy": cash_energy_by_market["DA"],
            "IDA_energy": cash_energy_by_market["IDA"],
            "capacity": cap_new_cash,
            "activation": act_new_cash,
            "fixed": fixed_energy_cash + fixed_reserve_cash,
        },
        residuals,
        absolute_gap,
        relative_gap,
        raw_gap,
        inp.input_id,
        feasible=True,
        proven_optimal=bool(result.success and int(result.status) == 0),
        profit_upper_bound_eur=profit_upper,
        contract_trades=tuple({
            "contract_id": c.contract_id, "market": c.market,
            "gate_close_utc": c.gate_close_utc.isoformat(),
            "result_release_utc": c.result_release_utc.isoformat(),
            "delivery_start_utc": c.delivery_start_utc.isoformat(),
            "delivery_end_utc": c.delivery_end_utc.isoformat(),
            "sell_mw": float(sell_values[j]), "buy_mw": float(buy_values[j]),
            "sell_mwh": float(sell_values[j]) * (c.delivery_end_utc-c.delivery_start_utc).total_seconds()/3600,
            "buy_mwh": float(buy_values[j]) * (c.delivery_end_utc-c.delivery_start_utc).total_seconds()/3600,
            "cash_eur": c.price_eur_per_mwh * net_values[j] * (c.delivery_end_utc-c.delivery_start_utc).total_seconds()/3600,
        } for j, c in enumerate(contracts)),
        salvage_eur=salvage,
        objective_eur=objective_value,
        data_scope=inp.data_scope,
        research_provenance=inp.research_provenance,
    )


def solve_joint_both_orders(inp: SyntheticMarketInput, **kwargs: float) -> dict[str, SyntheticMarketResult]:
    """Run the two fixed-order joint cases independently."""

    return {"U": solve_joint(inp, "U", **kwargs), "D": solve_joint(inp, "D", **kwargs)}


def _audit_solution(
    inp: SyntheticMarketInput,
    order_mode: str,
    x: np.ndarray,
    steps: Sequence[_Step],
    qh_market_terms: Mapping[str, Sequence[tuple[int, float]]],
    sell: np.ndarray,
    buy: np.ndarray,
    contract_mode: np.ndarray,
    reserve_up: np.ndarray,
    reserve_down: np.ndarray,
    charge: np.ndarray,
    discharge: np.ndarray,
    operation_mode: np.ndarray,
    soc: np.ndarray,
    baseline_out: Mapping[str, float],
    up_out: Mapping[str, float],
    down_out: Mapping[str, float],
    gross: float,
    solver_fun: float,
    *,
    terminal_hard: bool = True,
    objective_value: float | None = None,
    objective_constant: float = 0.0,
    frozen_spot: Mapping[str, tuple[float, float]] | None = None,
    frozen_reserve: Mapping[str, tuple[float, float]] | None = None,
    budget_limits: Mapping[int, float] | None = None,
) -> dict[str, float]:
    if not np.all(np.isfinite(x)):
        raise AssertionError("solver vector contains non-finite values")
    qh_map = inp.qh_by_id
    qh_index = {qh.qh_id: i for i, qh in enumerate(inp.qhs)}
    segment_start: dict[str, datetime] = {}
    for qh in inp.qhs:
        segment_start.setdefault(qh.segment_id, qh.start_utc)
    fixed_by_qh = inp.fixed_by_qh
    fixed_for_qh = {
        qh.qh_id: fixed_by_qh.get(qh.qh_id, FixedCommitment(qh.qh_id))
        for qh in inp.qhs
    }
    contracts_by_qh: dict[str, list[tuple[int, float, datetime]]] = {
        qh.qh_id: [] for qh in inp.qhs
    }
    event_times_by_qh: dict[str, set[datetime]] = {qh.qh_id: set() for qh in inp.qhs}
    contract_segments: list[set[str]] = []
    for j, contract in enumerate(inp.contracts):
        mapped_segments: set[str] = set()
        for qh_id, weight in contract.qh_weights.items():
            if float(weight) <= 0:
                continue
            mapped_segments.add(qh_map[qh_id].segment_id)
            weight_f = float(weight)
            contracts_by_qh[qh_id].append((j, weight_f, contract.result_release_utc))
            event_times_by_qh[qh_id].add(contract.result_release_utc)
        contract_segments.append(mapped_segments)
    frozen_spot = frozen_spot or {}
    frozen_reserve = frozen_reserve or {}
    power_violation = 0.0
    power_equation_violation = 0.0
    charge_violation = 0.0
    discharge_violation = 0.0
    contract_bound_violation = 0.0
    contract_mode_integrality = 0.0
    contract_mode_violation = 0.0
    contract_gate_violation = 0.0
    for idx in range(len(sell)):
        sell_value = float(x[sell[idx]])
        buy_value = float(x[buy[idx]])
        mode_value = float(x[contract_mode[idx]])
        contract_bound_violation = max(contract_bound_violation, -sell_value, -buy_value, sell_value - 100.0, buy_value - 100.0)
        contract_mode_integrality = max(contract_mode_integrality, abs(mode_value - round(mode_value)))
        contract_mode_violation = max(contract_mode_violation, sell_value - 100.0 * (1.0 - mode_value), buy_value - 100.0 * mode_value)
        mapped_segments = contract_segments[idx]
        if inp.contracts[idx].contract_id not in frozen_spot and len(mapped_segments) == 1 and inp.contracts[idx].gate_close_utc < segment_start[next(iter(mapped_segments))]:
            contract_gate_violation = max(contract_gate_violation, sell_value, buy_value)
    result_node_position_violation = 0.0
    for qh in inp.qhs:
        mapped_contracts = contracts_by_qh[qh.qh_id]
        times = sorted(event_times_by_qh[qh.qh_id])
        for event_time in times:
            position = fixed_for_qh[qh.qh_id].baseline_mw
            # Keep original contract order to preserve floating-point audit
            # behavior while avoiding a full contracts scan for each QH.
            for j, weight, result_release in mapped_contracts:
                if result_release <= event_time:
                    position += weight * (float(x[sell[j]]) - float(x[buy[j]]))
            result_node_position_violation = max(result_node_position_violation, abs(position)-100.0)
    reserve_violation = 0.0
    reserve_bound_violation = 0.0
    reserve_integrality = 0.0
    for qh_id, base in baseline_out.items():
        qh_i = qh_index[qh_id]
        fc = fixed_for_qh[qh_id]
        reserve_bound_violation = max(
            reserve_bound_violation,
            -float(x[reserve_up[qh_i]]),
            float(x[reserve_up[qh_i]]) - (inp.reserve_limit_up_mw - fc.reserve_up_mw),
            -float(x[reserve_down[qh_i]]),
            float(x[reserve_down[qh_i]]) - (inp.reserve_limit_down_mw - fc.reserve_down_mw),
        )
        reserve_integrality = max(
            reserve_integrality,
            abs(float(x[reserve_up[qh_i]]) - round(float(x[reserve_up[qh_i]]))),
            abs(float(x[reserve_down[qh_i]]) - round(float(x[reserve_down[qh_i]]))),
        )
        qh = inp.qhs[qh_i]
        if qh_id not in frozen_reserve and qh.afrr_gate_close_utc < segment_start[qh.segment_id]:
            reserve_bound_violation = max(reserve_bound_violation, float(x[reserve_up[qh_i]]), float(x[reserve_down[qh_i]]))
        power_violation = max(power_violation, max(base - inp.grid_export_mw, -inp.grid_import_mw - base, 0.0))
        reserve_violation = max(reserve_violation, up_out[qh_id] - inp.reserve_limit_up_mw, down_out[qh_id] - inp.reserve_limit_down_mw)
        power_violation = max(power_violation, base + up_out[qh_id] - inp.grid_export_mw, -inp.grid_import_mw - (base - down_out[qh_id]))
    previous_by_segment: dict[str, float] = {}
    soc_violation = 0.0
    throughput_by_year: dict[int, float] = {}
    for idx, step in enumerate(steps):
        qh = qh_map[step.qh_id]
        mode_value = float(x[operation_mode[idx]])
        charge_value = float(x[charge[idx]])
        discharge_value = float(x[discharge[idx]])
        charge_violation = max(charge_violation, -charge_value, charge_value - inp.charge_mw * (1.0 - mode_value))
        discharge_violation = max(discharge_violation, -discharge_value, discharge_value - inp.discharge_mw * mode_value)
        if step.phase == "up":
            expected_power = baseline_out[step.qh_id] + up_out[step.qh_id]
        elif step.phase == "down":
            expected_power = baseline_out[step.qh_id] - down_out[step.qh_id]
        else:
            expected_power = baseline_out[step.qh_id]
        power_equation_violation = max(power_equation_violation, abs(discharge_value - charge_value - expected_power))
        current = float(x[soc[idx]])
        previous = previous_by_segment.get(qh.segment_id, inp.e_initial_mwh)
        expected = previous + inp.eta_charge * charge_value * step.duration_hours - discharge_value * step.duration_hours / inp.eta_discharge
        soc_violation = max(soc_violation, abs(current - expected), inp.e_min_mwh - current, current - inp.e_max_mwh)
        throughput_by_year[qh.madrid_year] = throughput_by_year.get(qh.madrid_year, 0.0) + (inp.eta_charge * float(x[charge[idx]]) * step.duration_hours + float(x[discharge[idx]]) * step.duration_hours / inp.eta_discharge) / inp.cycle_denominator_mwh
        previous_by_segment[qh.segment_id] = current
    terminal_violation = 0.0
    if terminal_hard:
        for segment, terminal in previous_by_segment.items():
            terminal_violation = max(terminal_violation, abs(terminal - inp.e_terminal_mwh))
    objective_target = gross if objective_value is None else objective_value
    objective_consistency = abs((-solver_fun) + _fixed_cash_total(inp) - objective_target - objective_constant)
    independent_energy = 0.0
    for contract_index, contract in enumerate(inp.contracts):
        mapped_hours = sum(qh_map[qid].duration_hours * float(weight) for qid, weight in contract.qh_weights.items())
        independent_energy += contract.price_eur_per_mwh * (float(x[sell[contract_index]]) - float(x[buy[contract_index]])) * mapped_hours
    independent_capacity = sum(
        qh.afrr_capacity_price_up_eur_per_mw_qh * up_out[qh.qh_id]
        + qh.afrr_capacity_price_down_eur_per_mw_qh * down_out[qh.qh_id]
        for qh in inp.qhs
    )
    independent_activation = sum(
        qh.afrr_activation_price_up_eur_per_mwh * up_out[qh.qh_id] * 0.25 * qh.alpha_up
        + qh.afrr_activation_price_down_eur_per_mwh * down_out[qh.qh_id] * 0.25 * qh.alpha_down
        for qh in inp.qhs
    )
    independent_cash = independent_energy + independent_capacity + independent_activation + _fixed_cash_total(inp) - sum(
        qh.afrr_capacity_price_up_eur_per_mw_qh * fc.reserve_up_mw
        + qh.afrr_capacity_price_down_eur_per_mw_qh * fc.reserve_down_mw
        + qh.afrr_activation_price_up_eur_per_mwh * fc.reserve_up_mw * 0.25 * qh.alpha_up
        + qh.afrr_activation_price_down_eur_per_mwh * fc.reserve_down_mw * 0.25 * qh.alpha_down
        for qh in inp.qhs
        for fc in [fixed_for_qh[qh.qh_id]]
    )
    integrality = 0.0
    for idx in list(reserve_up) + list(reserve_down) + list(operation_mode):
        integrality = max(integrality, abs(float(x[idx]) - round(float(x[idx]))))
    budget_violation = 0.0
    effective_budget = inp.effective_annual_efc_budget if budget_limits is None else budget_limits
    for year, used in throughput_by_year.items():
        budget_violation = max(budget_violation, used - float(effective_budget[year]))
    residuals = {
        "soc_recursion_abs_max": float(max(soc_violation, 0.0)),
        "power_headroom_violation_max": float(max(power_violation, 0.0)),
        "power_equation_abs_max": float(max(power_equation_violation, 0.0)),
        "charge_power_violation_max": float(max(charge_violation, 0.0)),
        "discharge_power_violation_max": float(max(discharge_violation, 0.0)),
        "contract_bound_violation_max": float(max(contract_bound_violation, 0.0)),
        "contract_mode_violation_max": float(max(contract_mode_violation, 0.0)),
        "contract_gate_violation_max": float(max(contract_gate_violation, 0.0)),
        "contract_mode_integer_abs_max": float(contract_mode_integrality),
        "result_node_spot_position_violation_max": float(max(result_node_position_violation, 0.0)),
        "reserve_limit_violation_max": float(max(reserve_violation, 0.0)),
        "reserve_bound_violation_max": float(max(reserve_bound_violation, 0.0)),
        "reserve_integer_abs_max": float(reserve_integrality),
        "terminal_soc_abs_max": float(max(terminal_violation, 0.0)),
        "annual_efc_violation_max": float(max(budget_violation, 0.0)),
        "binary_integer_abs_max": float(integrality),
        "objective_cash_consistency_abs": float(objective_consistency),
        "independent_cash_rebuild_abs": float(abs(gross - independent_cash)),
    }
    for year, used in throughput_by_year.items():
        residuals[f"annual_efc_used_{year}"] = float(used)
        residuals[f"annual_efc_budget_effective_{year}"] = float(effective_budget[year])
    check_values = [
        value
        for key, value in residuals.items()
        if not key.startswith("annual_efc_used_") and not key.startswith("annual_efc_budget_effective_")
    ]
    if max(check_values, default=0.0) > 1e-5:
        raise AssertionError(f"independent synthetic market audit failed: {residuals}")
    return residuals
