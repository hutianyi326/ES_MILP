"""Post-hoc C-stage pressure diagnostics for the synthetic Spain model.

The functions in this module deliberately do not optimise, settle cash, or
modify a rolling run.  They replay a frozen position through the six required
15-minute paths and then continue with the main-path tail which was already
available at the snapshot time.  This keeps pressure results diagnostic only.

All power is signed on the AC side: positive means export/discharge and
negative means import/charge.  Raw SOC is retained when a path leaves the
10--190 MWh diagnostic interval; values are never clipped.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone, timedelta
from hashlib import sha256
import json
import math
from typing import Any, Iterable, Mapping, Sequence

from .core import _required_madrid_timezone

TOL = 1e-9
UTC = timezone.utc
PATHS = ("none", "only_up", "only_down", "up_then_down", "down_then_up", "main")
ORDERS = ("U", "D")


def _utc(v: Any) -> datetime:
    if isinstance(v, str):
        v = datetime.fromisoformat(v)
    if not isinstance(v, datetime) or v.tzinfo is None or v.utcoffset() is None:
        raise ValueError("diagnostic timestamp must be timezone-aware")
    return v.astimezone(UTC)


def _num(v: Any, name: str, *, nonnegative: bool = False) -> float:
    try:
        x = float(v)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(x) or (nonnegative and x < 0):
        raise ValueError(f"{name} must be finite" + (" and non-negative" if nonnegative else ""))
    return x


def _hash(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()


def _get(obj: Any, name: str, default: Any = None) -> Any:
    return obj.get(name, default) if isinstance(obj, Mapping) else getattr(obj, name, default)


@dataclass(frozen=True)
class DiagnosticQH:
    """A frozen main-path QH position used by the replay engine."""

    qh_id: str
    start_utc: datetime
    end_utc: datetime
    segment_id: str
    madrid_year: int
    baseline_mw: float
    reserve_up_mw: float
    reserve_down_mw: float
    alpha_up: float
    alpha_down: float
    committed: bool = True

    def __post_init__(self) -> None:
        if not self.qh_id or not self.segment_id:
            raise ValueError("qh_id and segment_id are required")
        start, end = _utc(self.start_utc), _utc(self.end_utc)
        if end <= start or abs((end - start).total_seconds() - 900) > 1e-6:
            raise ValueError("diagnostic QH must be exactly 15 minutes")
        for name in ("baseline_mw", "reserve_up_mw", "reserve_down_mw", "alpha_up", "alpha_down"):
            x = _num(getattr(self, name), name, nonnegative=name.startswith("reserve") or name.startswith("alpha"))
            object.__setattr__(self, name, x)
        if self.reserve_up_mw < 0 or self.reserve_down_mw < 0:
            raise ValueError("reserve MW must be non-negative")
        if not (0.0 <= self.alpha_up <= 1.0 and 0.0 <= self.alpha_down <= 1.0):
            raise ValueError("alpha values must lie in [0,1]")
        if self.alpha_up + self.alpha_down > 1.0:
            raise ValueError("alpha_up + alpha_down must be <= 1")
        madrid_year = _utc(self.start_utc).astimezone(_required_madrid_timezone()).year
        if int(self.madrid_year) != madrid_year:
            raise ValueError("madrid_year must match Europe/Madrid QH start")
        object.__setattr__(self, "start_utc", start)
        object.__setattr__(self, "end_utc", end)
        object.__setattr__(self, "madrid_year", madrid_year)
        if not self.committed and any(x != 0 for x in (self.baseline_mw, self.reserve_up_mw, self.reserve_down_mw)):
            raise ValueError("uncommitted QH must have zero positions")

    @property
    def duration_hours(self) -> float:
        return 0.25


@dataclass(frozen=True)
class DiagnosticSnapshot:
    """State known at one frozen QH start.

    ``tail`` contains only positions whose non-zero order/capacity was already
    submitted by ``asof_utc``.  A later opportunity is represented by omission,
    never by a fabricated zero-alpha or recharge action.
    """

    qh: DiagnosticQH
    initial_soc_mwh: float
    asof_utc: datetime
    tail: tuple[DiagnosticQH, ...] = ()
    prior_efc_by_year: Mapping[int, float] = field(default_factory=dict)
    efc_budget_by_year: Mapping[int, float] = field(default_factory=dict)
    source_order_hash: str = ""
    source_mode: str = "joint_full"
    visible_orders: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        initial = _num(self.initial_soc_mwh, "initial_soc_mwh")
        if not math.isfinite(initial):
            raise ValueError("initial SOC must be finite")
        asof = _utc(self.asof_utc)
        if asof != self.qh.start_utc:
            raise ValueError("snapshot asof must equal pulse start")
        ordered = tuple(self.tail)
        if ordered:
            previous = self.qh.end_utc
            for row in ordered:
                if row.segment_id != self.qh.segment_id:
                    raise ValueError("snapshot tail may not cross a segment gap")
                if row.start_utc != previous:
                    raise ValueError("snapshot tail must be contiguous; gaps are rejected")
                previous = row.end_utc
        object.__setattr__(self, "initial_soc_mwh", initial)
        object.__setattr__(self, "asof_utc", asof)
        object.__setattr__(self, "tail", ordered)
        budgets = {int(y): _num(v, "annual budget", nonnegative=True) for y, v in self.efc_budget_by_year.items()}
        prior = {int(y): _num(v, "prior EFC", nonnegative=True) for y, v in self.prior_efc_by_year.items()}
        if {q.madrid_year for q in (self.qh,) + ordered} - budgets.keys() or prior.keys() - budgets.keys():
            raise ValueError("explicit annual budget required for all snapshot and prior years")
        object.__setattr__(self, "efc_budget_by_year", budgets)
        object.__setattr__(self, "prior_efc_by_year", prior)


@dataclass(frozen=True)
class DiagnosticRecord:
    qh_id: str
    path: str
    phase: str
    start_utc: str
    end_utc: str
    duration_minutes: float
    power_mw: float
    soc_start_mwh: float
    soc_end_mwh: float
    dc_throughput_mwh: float
    efc: float


@dataclass(frozen=True)
class PressurePathResult:
    qh_id: str
    path: str
    order_mode: str
    pulse_minutes: float
    validation_minutes: float
    feasible: bool
    power_feasible: bool
    final_soc_mwh: float
    min_raw_soc_mwh: float
    max_raw_soc_mwh: float
    first_boundary_contact: Mapping[str, float | None]
    first_violation_onset: Mapping[str, float | None]
    max_lower_violation_mwh: float
    max_upper_violation_mwh: float
    max_power_violation_mw: float
    dc_throughput_mwh: float
    efc_used: float
    recovery: Mapping[str, float | None]
    records: tuple[Mapping[str, Any], ...]
    status: str = "PASS"
    efc_used_by_year: Mapping[int, float] = field(default_factory=dict)
    efc_budget_shortfall_by_year: Mapping[int, float] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PressureSnapshotResult:
    qh_id: str
    order_mode: str
    asof_utc: str
    source_mode: str
    source_order_hash: str
    fixed_commitment: Mapping[str, Any]
    paths: Mapping[str, PressurePathResult]

    def as_dict(self) -> dict[str, Any]:
        return {
            "qh_id": self.qh_id, "order_mode": self.order_mode,
            "asof_utc": self.asof_utc, "source_mode": self.source_mode,
            "source_order_hash": self.source_order_hash,
            "fixed_commitment": dict(self.fixed_commitment),
            "paths": {k: v.as_dict() for k, v in self.paths.items()},
        }


def make_qh_records(qhs: Iterable[Any], baseline: Mapping[str, float], reserve_up: Mapping[str, float], reserve_down: Mapping[str, float], *, committed: Mapping[str, bool] | None = None) -> tuple[DiagnosticQH, ...]:
    """Convert core ``QHInput`` objects plus frozen positions to diagnostics."""
    rows = []
    for q in qhs:
        qid = str(_get(q, "qh_id"))
        rows.append(DiagnosticQH(qid, _utc(_get(q, "start_utc")), _utc(_get(q, "end_utc")), str(_get(q, "segment_id")), int(_get(q, "madrid_year")), _num(baseline[qid], "baseline_mw"), _num(reserve_up[qid], "reserve_up_mw", nonnegative=True), _num(reserve_down[qid], "reserve_down_mw", nonnegative=True), _num(_get(q, "alpha_up"), "alpha_up"), _num(_get(q, "alpha_down"), "alpha_down"), True if committed is None else bool(committed[qid])))
    for a, b in zip(rows, rows[1:]):
        if a.end_utc > b.start_utc:
            raise ValueError("QH records overlap")
    return tuple(rows)


def _apply(soc: float, power: float, minutes: float, eta_c: float, eta_d: float) -> tuple[float, float, float]:
    h = minutes / 60.0
    if power >= 0:
        dc = power * h / eta_d
        return soc - dc, dc, dc
    dc = -power * h * eta_c
    return soc + dc, dc, dc


def _contact(start: float, end: float, bound: float, t: float, duration: float) -> float | None:
    if abs(start - bound) <= TOL:
        return t
    if abs(end - bound) <= TOL:
        return t + duration
    if (start - bound) * (end - bound) < 0:
        return t + duration * (bound - start) / (end - start)
    return None


def _violation(start: float, end: float, lower: float, upper: float, t: float, duration: float) -> dict[str, float | None]:
    out = {"lower": None, "upper": None}
    if start < lower - TOL:
        out["lower"] = t
    elif end < lower - TOL and start >= lower - TOL:
        out["lower"] = t + duration * max(0.0, min(1.0, (lower - start) / (end - start))) if end != start else t
    if start > upper + TOL:
        out["upper"] = t
    elif end > upper + TOL and start <= upper + TOL:
        out["upper"] = t + duration * max(0.0, min(1.0, (upper - start) / (end - start))) if end != start else t
    return out


def _phases(q: DiagnosticQH, path: str, order: str) -> list[tuple[str, float, float]]:
    if path == "none":
        return [("none", 15.0, q.baseline_mw)]
    if path == "only_up":
        return [("up", 15.0, q.baseline_mw + q.reserve_up_mw)]
    if path == "only_down":
        return [("down", 15.0, q.baseline_mw - q.reserve_down_mw)]
    if path in {"up_then_down", "down_then_up"}:
        if q.reserve_up_mw <= TOL or q.reserve_down_mw <= TOL:
            return []
        first = "up" if path == "up_then_down" else "down"
        return [(first, 7.5, q.baseline_mw + q.reserve_up_mw if first == "up" else q.baseline_mw - q.reserve_down_mw), ("down" if first == "up" else "up", 7.5, q.baseline_mw - q.reserve_down_mw if first == "up" else q.baseline_mw + q.reserve_up_mw)]
    if path != "main":
        raise ValueError(f"unknown pressure path {path}")
    first = ("up", q.alpha_up, q.baseline_mw + q.reserve_up_mw), ("down", q.alpha_down, q.baseline_mw - q.reserve_down_mw)
    if order == "D":
        first = (first[1], first[0])
    # Positive, even tiny, durations are retained.  The input validator has
    # already rejected negative residual idle time; no clipping is allowed.
    return [(kind, 15.0 * fraction, power) for kind, fraction, power in (*first, ("idle", 1.0 - (q.alpha_up + q.alpha_down), q.baseline_mw)) if fraction > 0.0]


def _recovery(soc: float, e_min: float, e_max: float, charge_limit: float, discharge_limit: float, eta_c: float, eta_d: float) -> dict[str, float | None]:
    if e_min <= soc <= e_max:
        return {"needed_dc_mwh": 0.0, "needed_ac_mwh": 0.0, "ideal_minute": 0.0, "direction": None}
    if soc < e_min:
        dc = e_min - soc
        # AC charging needed to put dc energy into the cell.
        return {"needed_dc_mwh": dc, "needed_ac_mwh": dc / eta_c, "ideal_minute": dc / (charge_limit * eta_c) * 60 if charge_limit > TOL else None, "direction": "charge"}
    dc = soc - e_max
    return {"needed_dc_mwh": dc, "needed_ac_mwh": dc * eta_d, "ideal_minute": dc / (discharge_limit / eta_d) * 60 if discharge_limit > TOL else None, "direction": "discharge"}


def replay_pressure(snapshot: DiagnosticSnapshot, *, order_mode: str = "U", eta_charge: float = .92, eta_discharge: float = .92, e_min_mwh: float = 10., e_max_mwh: float = 190., charge_limit_mw: float = 100., discharge_limit_mw: float = 100.) -> PressureSnapshotResult:
    """Replay six pressure paths for one frozen snapshot and its committed tail."""
    if order_mode not in ORDERS:
        raise ValueError("order_mode must be U or D")
    if not (0 < eta_charge <= 1 and 0 < eta_discharge <= 1):
        raise ValueError("efficiency must lie in (0,1]")
    for name, value in (("e_min", e_min_mwh), ("e_max", e_max_mwh), ("charge", charge_limit_mw), ("discharge", discharge_limit_mw)):
        _num(value, name, nonnegative=True)
    if e_min_mwh >= e_max_mwh:
        raise ValueError("energy bounds must be increasing")
    sequence = (snapshot.qh,) + tuple(snapshot.tail)
    outputs: dict[str, PressurePathResult] = {}
    for path in PATHS:
        soc = snapshot.initial_soc_mwh
        raw = [soc]; records: list[Mapping[str, Any]] = []
        contacts = {"lower": None, "upper": None}; violations = {"lower": None, "upper": None}
        max_lower = max(0., e_min_mwh-soc); max_upper = max(0., soc-e_max_mwh)
        max_power = throughput = 0.0; elapsed = 0.0; efc_by_year: dict[int, float] = {}
        for i, q in enumerate(sequence):
            phases = _phases(q, path, order_mode) if i == 0 else _phases(q, "main", order_mode)
            if path in {"up_then_down", "down_then_up"} and i == 0 and not phases:
                outputs[path] = PressurePathResult(snapshot.qh.qh_id, path, order_mode, 15., 0., False, False, snapshot.initial_soc_mwh, snapshot.initial_soc_mwh, snapshot.initial_soc_mwh, {"lower": None, "upper": None}, {"lower": None, "upper": None}, 0., 0., 0., 0., 0., _recovery(snapshot.initial_soc_mwh, e_min_mwh, e_max_mwh, charge_limit_mw, discharge_limit_mw, eta_charge, eta_discharge), tuple(), status="NOT_RUN")
                break
            max_power = max(max_power, q.baseline_mw + q.reserve_up_mw - discharge_limit_mw,
                            -charge_limit_mw - (q.baseline_mw - q.reserve_down_mw))
            local_offset = 0.0
            for phase, minutes, power in phases:
                if minutes <= 0.0: continue
                start = soc; soc, dc, _ = _apply(soc, power, minutes, eta_charge, eta_discharge)
                end = soc; raw.append(end); throughput += dc
                if contacts["lower"] is None: contacts["lower"] = _contact(start, end, e_min_mwh, elapsed, minutes)
                if contacts["upper"] is None: contacts["upper"] = _contact(start, end, e_max_mwh, elapsed, minutes)
                got = _violation(start, end, e_min_mwh, e_max_mwh, elapsed, minutes)
                for k in ("lower", "upper"):
                    if violations[k] is None: violations[k] = got[k]
                max_lower = max(max_lower, e_min_mwh - end); max_upper = max(max_upper, end - e_max_mwh)
                max_power = max(max_power, power - discharge_limit_mw, -charge_limit_mw - power, 0.0)
                # ``elapsed`` is validation time from the pulse start.  For a
                # tail QH use that QH's actual UTC start; this avoids a second
                # 15-minute offset when the pulse itself has ended.
                st = q.start_utc + timedelta(minutes=local_offset)
                en = st + timedelta(minutes=minutes)
                efc = dc / (2 * (e_max_mwh - e_min_mwh))
                efc_by_year[q.madrid_year] = efc_by_year.get(q.madrid_year, 0.0) + efc
                records.append(asdict(DiagnosticRecord(q.qh_id, path, phase, st.isoformat(), en.isoformat(), minutes, power, start, end, dc, efc)))
                local_offset += minutes
                elapsed += minutes
        if path in outputs and outputs[path].status == "NOT_RUN":
            continue
        shortfall = {y: max(0., snapshot.prior_efc_by_year.get(y, 0.) + efc_by_year.get(y, 0.) - budget)
                     for y, budget in snapshot.efc_budget_by_year.items()}
        feasible = max_lower <= TOL and max_upper <= TOL and max_power <= TOL and all(v <= TOL for v in shortfall.values())
        outputs[path] = PressurePathResult(snapshot.qh.qh_id, path, order_mode, 15., elapsed, feasible, max_power <= TOL, soc, min(raw), max(raw), contacts, violations, max(0., max_lower), max(0., max_upper), max_power, throughput, throughput / (2 * (e_max_mwh - e_min_mwh)), _recovery(soc, e_min_mwh, e_max_mwh, charge_limit_mw, discharge_limit_mw, eta_charge, eta_discharge), tuple(records), status=("PASS" if feasible else "FAIL"), efc_used_by_year=efc_by_year, efc_budget_shortfall_by_year=shortfall)
    return PressureSnapshotResult(snapshot.qh.qh_id, order_mode, snapshot.asof_utc.isoformat(), snapshot.source_mode, snapshot.source_order_hash, {"baseline_mw": snapshot.qh.baseline_mw, "reserve_up_mw": snapshot.qh.reserve_up_mw, "reserve_down_mw": snapshot.qh.reserve_down_mw, "tail_qh_ids": [q.qh_id for q in snapshot.tail], "tail_uses_main_alpha": True, "tail_has_new_orders": False, "visible_orders":dict(snapshot.visible_orders)}, outputs)


def make_snapshot(qhs: Sequence[DiagnosticQH], index: int, *, initial_soc_mwh: float, order_mode: str = "U", submitted_qh_ids: Iterable[str] | None = None, source_mode: str = "joint_full", source_order_hash: str = "", prior_efc_by_year: Mapping[int, float] | None = None, efc_budget_by_year: Mapping[int, float] | None = None) -> DiagnosticSnapshot:
    """Create a QH snapshot and filter the tail to already-submitted positions.

    ``submitted_qh_ids`` is intentionally explicit.  Callers must derive it
    from gate times; this function never assumes all future optimised orders
    were known at an earlier QH.
    """
    if not qhs or not (0 <= index < len(qhs)):
        raise ValueError("snapshot index outside QH sequence")
    q = qhs[index]
    allowed = set(submitted_qh_ids) if submitted_qh_ids is not None else {x.qh_id for x in qhs[index:] if x.committed}
    future = list(qhs[index + 1:])
    committed_positions = [i for i, x in enumerate(future) if x.qh_id in allowed and x.committed]
    last = max(committed_positions, default=-1)
    tail = []
    for i, x in enumerate(future):
        if i > last: break
        if x.segment_id != q.segment_id:
            raise ValueError("committed tail crosses a segment gap")
        if tail and tail[-1].end_utc != x.start_utc:
            raise ValueError("diagnostic tail has a time gap")
        tail.append(x if x.qh_id in allowed else replace(x, baseline_mw=0., reserve_up_mw=0., reserve_down_mw=0., committed=False))
    return DiagnosticSnapshot(q, initial_soc_mwh, q.start_utc, tuple(tail), prior_efc_by_year or {}, efc_budget_by_year or {}, source_order_hash, source_mode)


def _order_rows(rows, id_field, quantity_fields, known_ids):
    """Reject ambiguous/incomplete commitments before event-time filtering."""
    entries = rows.items() if isinstance(rows, Mapping) else ((_get(r, id_field), r) for r in rows)
    result = {}
    for key, row in entries:
        identifier = _get(row, id_field)
        if not isinstance(identifier, str) or key != identifier or identifier not in known_ids:
            raise ValueError("unknown or mismatched order identifier")
        if identifier in result:
            raise ValueError("duplicate order identifier")
        if _get(row, "status") not in {"pending", "awarded", "not_submitted"}:
            raise ValueError("unknown or missing order status")
        for name in quantity_fields:
            _num(_get(row, name), name, nonnegative=True)
        result[identifier] = row
    return result


def build_frozen_snapshot(qhs: Sequence[Any], contracts: Sequence[Any], spot_orders: Mapping[str, Any] | Sequence[Any], reserve_orders: Mapping[str, Any] | Sequence[Any], index: int, *, initial_soc_mwh: float, source_mode: str = "joint_full", prior_efc_by_year: Mapping[int, float] | None = None, efc_budget_by_year: Mapping[int, float] | None = None) -> DiagnosticSnapshot:
    """Build a snapshot from event-time orders, applying the gate exactly.

    An order is visible iff ``gate_close <= pulse_start``.  Equality is
    intentional.  A pending result with a later release remains a committed
    pending position; an order with a later gate, or a zero-volume
    ``not_submitted`` row, is excluded.  A later non-zero position after a
    missing QH is rejected instead of being silently pulled into the tail.
    """
    if not (0 <= index < len(qhs)):
        raise ValueError("snapshot index outside QH sequence")
    pulse = _utc(_get(qhs[index], "start_utc"))
    qids = [_get(q, "qh_id") for q in qhs]
    cids = [_get(c, "contract_id") for c in contracts]
    if len(set(qids)) != len(qids) or len(set(cids)) != len(cids):
        raise ValueError("duplicate QH or contract input identifier")
    spot_by_id = _order_rows(spot_orders, "contract_id", ("sell_mw", "buy_mw"), set(cids))
    reserve_by_qh = _order_rows(reserve_orders, "qh_id", ("up_mw", "down_mw"), set(qids))
    base: dict[str, float] = {str(_get(q, "qh_id")): 0.0 for q in qhs}
    rup: dict[str, float] = {str(_get(q, "qh_id")): 0.0 for q in qhs}
    rdn: dict[str, float] = {str(_get(q, "qh_id")): 0.0 for q in qhs}
    committed: dict[str, bool] = {k: False for k in base}
    visible_ids: list[str] = []
    provenance = {"spot":[], "reserve":[]}
    for c in contracts:
        cid = str(_get(c, "contract_id"))
        gate = _get(c, "gate_close_utc")
        if gate is None:
            raise ValueError("missing spot gate")
        if _utc(gate) > pulse:
            continue
        row = spot_by_id.get(cid)
        if row is None:
            continue
        submitted_at = _get(row, "submitted_at", None)
        if submitted_at is not None and _utc(submitted_at) > pulse:
            continue
        status_value = _get(row, "status", None)
        if status_value is None:
            raise ValueError("visible spot order must declare pending, awarded or not_submitted status")
        status = str(status_value)
        if status not in {"pending", "awarded", "not_submitted"}:
            raise ValueError("unknown spot status")
        sell = _num(_get(row, "sell_mw", 0.0), "sell_mw", nonnegative=True)
        buy = _num(_get(row, "buy_mw", 0.0), "buy_mw", nonnegative=True)
        if status == "not_submitted":
            if max(sell, buy) > TOL:
                raise ValueError("not_submitted order cannot carry non-zero volume")
            continue
        if max(sell, buy) <= TOL:
            continue
        visible_ids.append(cid)
        release = _get(c, "result_release_utc", _get(row, "result_release_utc"))
        provenance["spot"].append(dict(contract_id=cid, sell_mw=sell, buy_mw=buy,
            gate_close_utc=_utc(gate).isoformat(), submitted_at=_utc(submitted_at or gate).isoformat(),
            submission_basis="explicit" if submitted_at is not None else "model_gate_submission",
            result_release_utc=_utc(release).isoformat() if release is not None else None,
            status_asof=("pending" if _utc(release)>pulse else "awarded") if release is not None else status,
            qh_weights=dict(_get(c,"qh_weights"))))
        for qid, weight in (_get(c, "qh_weights", {}) or {}).items():
            weight = _num(weight, "contract weight", nonnegative=True)
            if weight > 0 and str(qid) not in base:
                raise ValueError("committed contract has unmapped delivery")
            if weight > 0:
                base[str(qid)] += float(weight) * (sell - buy)
                committed[str(qid)] = True
    for q in qhs:
        qid = str(_get(q, "qh_id")); row = reserve_by_qh.get(qid)
        gate = _get(q, "afrr_gate_close_utc")
        if gate is None:
            raise ValueError("missing reserve gate")
        if row is None or _utc(gate) > pulse:
            continue
        submitted_at = _get(row, "submitted_at", None)
        if submitted_at is not None and _utc(submitted_at) > pulse:
            continue
        status_value = _get(row, "status", None)
        if status_value is None:
            raise ValueError("visible reserve order must declare pending, awarded or not_submitted status")
        status = str(status_value)
        if status not in {"pending", "awarded", "not_submitted"}:
            raise ValueError("unknown reserve status")
        up = _num(_get(row, "up_mw", 0.0), "up_mw", nonnegative=True); down = _num(_get(row, "down_mw", 0.0), "down_mw", nonnegative=True)
        if status == "not_submitted":
            if max(up, down) > TOL: raise ValueError("not_submitted reserve cannot carry non-zero volume")
            continue
        if max(up, down) > TOL:
            rup[qid], rdn[qid], committed[qid] = up, down, True
            release = _get(q,"afrr_result_release_utc",_get(row,"result_release_utc"))
            provenance["reserve"].append(dict(qh_id=qid, up_mw=up, down_mw=down,
                gate_close_utc=_utc(gate).isoformat(), submitted_at=_utc(submitted_at or gate).isoformat(),
                submission_basis="explicit" if submitted_at is not None else "model_gate_submission",
                result_release_utc=_utc(release).isoformat() if release is not None else None,
                status_asof=("pending" if _utc(release)>pulse else "awarded") if release is not None else status))
    rows = make_qh_records(qhs, base, rup, rdn, committed=committed)
    # The current QH is always replayed, even when no position was frozen.  A
    # uncommitted intervening QHs retain zero positions and the original clock.
    tail_ids = {r.qh_id for r in rows[index + 1:] if r.committed}
    last_tail = max((i for i, r in enumerate(rows) if i > index and r.qh_id in tail_ids), default=index)
    tail: list[DiagnosticQH] = []
    for pos, r in enumerate(rows[index + 1:], start=index + 1):
        if r.segment_id != rows[index].segment_id:
            if any(x.segment_id == r.segment_id and x.qh_id in tail_ids for x in rows[pos:]):
                raise ValueError("committed tail crosses a segment gap")
            break
        if pos > last_tail: break
        if tail and tail[-1].end_utc != r.start_utc:
            raise ValueError("diagnostic tail has a time gap")
        if r.qh_id not in tail_ids:
            # This is an uncommitted but physically covered QH.  Keep it in
            # the validation clock with zero position and its original alpha.
            tail.append(r)
            continue
        tail.append(r)
    payload = {"pulse": pulse.isoformat(), "spot": sorted(visible_ids), "order_mode": source_mode,
               "qh": asdict(rows[index]), "tail": [asdict(r) for r in tail],
               "initial_soc_mwh": float(initial_soc_mwh), "prior_efc": prior_efc_by_year,
               "annual_budget": efc_budget_by_year, "orders":provenance}
    return DiagnosticSnapshot(rows[index], initial_soc_mwh, pulse, tuple(tail), prior_efc_by_year or {}, efc_budget_by_year or {}, _hash(payload), source_mode, provenance)


def run_pressure_suite(snapshots: Sequence[DiagnosticSnapshot], *, order_mode: str = "U", **kwargs: Any) -> dict[str, Any]:
    """Run every frozen snapshot; no result is fed back into optimisation."""
    if order_mode not in ORDERS: raise ValueError("order_mode must be U or D")
    rows = tuple(replay_pressure(s, order_mode=order_mode, **kwargs) for s in snapshots)
    return {"synthetic_only": True, "diagnostic_only": True, "pressure_feedback": False, "order_mode": order_mode, "fixed_order_no_probability": True, "paths": list(PATHS), "snapshot_count": len(rows), "input_hash": _hash([r.as_dict() for r in rows]), "snapshots": [r.as_dict() for r in rows]}


def run_fixed_order_comparison(snapshot: DiagnosticSnapshot, *, main_order: str = "U", **kwargs: Any) -> dict[str, Any]:
    """Replay the same fixed commitment under U and D; no re-optimisation."""
    if main_order not in ORDERS: raise ValueError("main_order must be U or D")
    u = replay_pressure(snapshot, order_mode="U", **kwargs).as_dict()
    d = replay_pressure(snapshot, order_mode="D", **kwargs).as_dict()
    return {"same_fixed_orders": True, "main_order": main_order, "up_then_down": u, "down_then_up": d, "pressure_feedback": False}


__all__ = ["DiagnosticQH", "DiagnosticSnapshot", "PressurePathResult", "PressureSnapshotResult", "PATHS", "make_qh_records", "make_snapshot", "build_frozen_snapshot", "replay_pressure", "run_pressure_suite", "run_fixed_order_comparison"]
