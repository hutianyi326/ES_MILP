"""Four independent synthetic optimisations and non-feedback diagnostics."""
from dataclasses import asdict
from datetime import timedelta
from hashlib import sha256
from pathlib import Path
import json
from importlib.metadata import version

from .core import HISTORICAL_CONDITIONAL_PREFIX, SYNTHETIC_MARKET_PREFIX, solve_joint, _required_madrid_timezone
from .rolling import solve_rolling
from .diagnostics import build_frozen_snapshot, replay_pressure, _contact, _violation, _recovery

TOL = 1e-5


def fingerprint(value):
    return sha256(json.dumps(value, sort_keys=True, default=str,
                             separators=(",", ":")).encode()).hexdigest()


def _physical(inp, base, up, down, order):
    """Independent entire-order replay; no optimisation or settlement."""
    used = {y: 0. for y in inp.effective_annual_efc_budget}
    states = {}; operation = []; errors = []; soc = inp.e_initial_mwh
    segments = {}; max_lower = max_upper = max_power = 0.
    first_contact = {"lower":None,"upper":None}
    first_violation = {"lower":None,"upper":None}
    for i, q in enumerate(inp.qhs):
        if i == 0 or inp.qhs[i - 1].segment_id != q.segment_id:
            soc = inp.e_initial_mwh
            segments[q.segment_id] = dict(start_utc=q.start_utc.isoformat(), recovery=None)
        states[q.qh_id] = {"soc_mwh": soc, "prior_efc_by_year": dict(used)}
        b, u, d = base[q.qh_id], up[q.qh_id], down[q.qh_id]
        export = min(inp.discharge_mw, inp.grid_export_mw)
        charge = min(inp.charge_mw, inp.grid_import_mw)
        if b + u > export + TOL or b - d < -charge - TOL:
            errors.append("reserve_headroom:" + q.qh_id)
        max_power = max(max_power,b+u-export,-charge-(b-d))
        phases = [("up", q.alpha_up, b + u), ("down", q.alpha_down, b - d)]
        if order == "D": phases.reverse()
        phases.append(("idle", 1 - (q.alpha_up + q.alpha_down), b))
        local_minutes = 0.
        for phase, fraction, power in phases:
            if fraction == 0: continue
            start = soc
            dc = -power * .25 * fraction * inp.eta_charge if power < 0 else -power * .25 * fraction / inp.eta_discharge
            soc += dc
            phase_start = q.start_utc + timedelta(minutes=local_minutes)
            duration = 15*fraction
            for name,bound in (("lower",inp.e_min_mwh),("upper",inp.e_max_mwh)):
                moment = _contact(start,soc,bound,0.,duration)
                if moment is not None and first_contact[name] is None:
                    first_contact[name] = dict(qh_id=q.qh_id,phase=phase,
                        utc=(phase_start+timedelta(minutes=moment)).isoformat())
            for name,moment in _violation(start,soc,inp.e_min_mwh,inp.e_max_mwh,0.,duration).items():
                if moment is not None and first_violation[name] is None:
                    first_violation[name] = dict(qh_id=q.qh_id,phase=phase,
                        utc=(phase_start+timedelta(minutes=moment)).isoformat())
            max_lower = max(max_lower,inp.e_min_mwh-soc)
            max_upper = max(max_upper,soc-inp.e_max_mwh)
            max_power = max(max_power,power-export,-charge-power)
            efc = abs(dc) / inp.cycle_denominator_mwh
            used[q.madrid_year] += efc
            operation.append(dict(qh_id=q.qh_id, phase=phase, hours=.25 * fraction,
                power_mw=power, start_soc_mwh=start, end_soc_mwh=soc, efc=efc,
                madrid_year=q.madrid_year,start_utc=phase_start.isoformat(),
                end_utc=(phase_start+timedelta(minutes=duration)).isoformat()))
            local_minutes += duration
            if soc < inp.e_min_mwh - TOL or soc > inp.e_max_mwh + TOL:
                errors.append("soc:" + q.qh_id + ":" + phase)
            if power > export + TOL or power < -charge - TOL:
                errors.append("power:" + q.qh_id + ":" + phase)
        if i == len(inp.qhs) - 1 or inp.qhs[i + 1].segment_id != q.segment_id:
            if abs(soc - inp.e_terminal_mwh) > TOL: errors.append("terminal:" + q.segment_id)
            segments[q.segment_id].update(end_utc=q.end_utc.isoformat(),final_soc_mwh=soc,
                recovery=_recovery(soc,inp.e_min_mwh,inp.e_max_mwh,charge,export,inp.eta_charge,inp.eta_discharge))
    for year, amount in used.items():
        if amount > inp.effective_annual_efc_budget[year] + TOL:
            errors.append("annual_efc:" + str(year))
    return dict(status="FAIL" if errors else "PASS", errors=errors,
                states=states, operation=operation, efc_by_year=used,
                first_boundary_contact=first_contact,first_violation_onset=first_violation,
                max_lower_violation_mwh=max_lower,max_upper_violation_mwh=max_upper,
                max_power_violation_mw=max_power,
                efc_budget_shortfall_by_year={y:max(0.,v-inp.effective_annual_efc_budget[y]) for y,v in used.items()},
                segments=segments,recovery_basis="segment-end to safe bounds only; hypothetical free power; no trade or feedback")


def run_four_combinations(inp, *, run_id="ES_SYNTHETIC_C", time_limit_seconds=60., mip_rel_gap=1e-6):
    """Run all four combinations without selecting a winning order.

    Only the accepted no-initial-commitment synthetic boundary is supported.
    Each QH pressure starts from its actual main state and as-of commitments.
    """
    # Keep the established synthetic run namespace (ES_SYNTHETIC_C,
    # ES_SYNTHETIC_ROLLING_...) while using a dedicated conditional namespace.
    expected_prefix = "ES_SYNTHETIC_" if inp.data_scope == "synthetic" else HISTORICAL_CONDITIONAL_PREFIX
    if not run_id.startswith(expected_prefix):
        raise ValueError(f"explicit {inp.data_scope} run ID required")
    if inp.fixed_commitments or inp.e_initial_mwh != 10 or inp.e_terminal_mwh != 10:
        raise ValueError("four-combination boundary requires no initial commitments and segment endpoints 10 MWh")
    _required_madrid_timezone()
    input_hash = fingerprint(asdict(inp))
    config = dict(time_limit_seconds=time_limit_seconds, mip_rel_gap=mip_rel_gap,
                  design_version="2026-09-20-draft-4", tzdata=version("tzdata"))
    design = Path(__file__).resolve().parents[2] / "model" / "es_perfect_information_design_20260920.md"
    # src/es_synthetic_market -> repository is parents[2].
    metadata = dict(run_id=run_id, input_hash=input_hash, configuration_hash=fingerprint(config),
                    design_hash=sha256(design.read_bytes()).hexdigest(), **config,
                    weight_kind="fixed_order_no_probability",
                    scope="synthetic_only" if inp.data_scope == "synthetic" else "historical_conditional",
                    data_scope=inp.data_scope, research_provenance=inp.research_provenance,
                    pressure_feedback=False, pressure_cash_included=False,
                    assumptions=["perfect information within respective horizon", "ideal full acceptance",
                        "no initial historical commitments", "user SOC bounds, not statutory SOC",
                        "gross cash excludes fees and degradation", "gate equality before QH delivery"],
                    coverage=[dict(qh_id=q.qh_id, start=q.start_utc.isoformat(),
                        end=q.end_utc.isoformat(), segment=q.segment_id) for q in inp.qhs])
    combinations = {}
    for mode in ("joint_full", "rolling7"):
        for order in ("U", "D"):
            key = mode + "-" + order
            if mode == "joint_full":
                result = solve_joint(inp, order, time_limit_seconds=time_limit_seconds, mip_rel_gap=mip_rel_gap)
                source = result.as_dict(); feasible = result.feasible
                cash = result.objective_gross_eur if feasible else None
                spots = [dict(r, status="awarded", submitted_at=r["gate_close_utc"]) for r in result.contract_trades]
                reserves = [dict(qh_id=q.qh_id, up_mw=result.reserve_up_mw.get(q.qh_id, 0.),
                    down_mw=result.reserve_down_mw.get(q.qh_id, 0.), status="awarded",
                    submitted_at=q.afrr_gate_close_utc.isoformat()) for q in inp.qhs]
                base = dict(result.qh_baseline_mw); up = dict(result.reserve_up_mw); down = dict(result.reserve_down_mw)
            else:
                result = solve_rolling(inp, run_id=run_id + "_" + order, order_mode=order,
                    time_limit_seconds=time_limit_seconds, mip_rel_gap=mip_rel_gap, planning_days=7)
                source = result.as_dict(); feasible = result.success; cash = result.execution_cash_eur
                spots = [asdict(x) for x in result.final_orders]
                reserves = [asdict(x) for x in result.final_reserves]
                by_contract = {x["contract_id"]: x for x in spots}
                by_qh = {x["qh_id"]: x for x in reserves}
                base = {q.qh_id: sum(c.qh_weights.get(q.qh_id, 0.) *
                    (by_contract[c.contract_id]["sell_mw"] - by_contract[c.contract_id]["buy_mw"])
                    for c in inp.contracts if c.contract_id in by_contract) for q in inp.qhs}
                up = {q.qh_id: by_qh.get(q.qh_id, {}).get("up_mw", 0.) for q in inp.qhs}
                down = {q.qh_id: by_qh.get(q.qh_id, {}).get("down_mw", 0.) for q in inp.qhs}
            report = dict(**metadata, mode=mode, order=order, source_result=source,
                          main_status="FAIL", valid_gross_eur=None, diagnostic_status="NOT_RUN")
            combinations[key] = report
            if not feasible: continue
            main = _physical(inp, base, up, down, order)
            if mode == "rolling7":
                executed = [r for w in result.windows for r in w.operation]
                if len(executed) != len(main["operation"]) or any(
                    a["qh_id"] != b["qh_id"] or a["phase"] != b["phase"] or
                    any(abs(a[k] - b[k]) > TOL for k in ("power_mw", "start_soc_mwh", "end_soc_mwh", "efc"))
                    for a, b in zip(executed, main["operation"])):
                    main["status"] = "FAIL"; main["errors"].append("rolling_execution_replay_mismatch")
            else:
                for segment, trace in result.soc_trace_mwh.items():
                    ids = {q.qh_id for q in inp.qhs if q.segment_id == segment}
                    expected = [r["end_soc_mwh"] for r in main["operation"] if r["qh_id"] in ids]
                    if len(trace) != len(expected) or any(abs(a-b)>TOL for a,b in zip(trace, expected)):
                        main["status"] = "FAIL"; main["errors"].append("joint_soc_replay_mismatch")
            report["main_audit"] = main; report["main_status"] = main["status"]
            if main["status"] != "PASS": continue
            report["valid_gross_eur"] = cash
            opposite = "D" if order == "U" else "U"
            report["same_orders_other_order"] = dict(order=opposite, reoptimised=False,
                **_physical(inp, base, up, down, opposite))
            before = fingerprint(source)
            pressure = []
            for i, q in enumerate(inp.qhs):
                state = main["states"][q.qh_id]
                snapshot = build_frozen_snapshot(inp.qhs, inp.contracts, spots, reserves, i,
                    initial_soc_mwh=state["soc_mwh"], source_mode=mode,
                    prior_efc_by_year=state["prior_efc_by_year"],
                    efc_budget_by_year=inp.effective_annual_efc_budget)
                pressure.append(replay_pressure(snapshot, order_mode=order,
                    eta_charge=inp.eta_charge, eta_discharge=inp.eta_discharge,
                    e_min_mwh=inp.e_min_mwh, e_max_mwh=inp.e_max_mwh,
                    charge_limit_mw=min(inp.charge_mw, inp.grid_import_mw),
                    discharge_limit_mw=min(inp.discharge_mw, inp.grid_export_mw)).as_dict())
            if fingerprint(source) != before or fingerprint(asdict(inp)) != input_hash:
                raise AssertionError("diagnostic mutated main result or input")
            report.update(pressure=pressure, diagnostic_status="COMPLETED",
                          diagnostic_isolation="PASS", revenue_interpretation="conditional_on_main_order_and_alpha")
    return dict(**metadata, combinations=combinations)
