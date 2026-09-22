"""Run and time the authorized full-range Spain conditional MILP scenario.

The production model is imported from the desktop ``pkg_patched`` package,
while immutable raw inputs and all outputs remain under the project root.
"""
from __future__ import annotations

import argparse
import ctypes
from collections import Counter
from datetime import date, datetime, time
import json
from math import isfinite
from pathlib import Path
import shutil
import sys
from time import perf_counter
from types import SimpleNamespace

PATCHED = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PATCHED))
sys.path.insert(1, str(ROOT))

import scipy.optimize

from src.es_historical_conditional.__main__ import build_preflight
from src.es_historical_conditional.adapter import (
    MADRID,
    complete_contracts,
    evidence_payload,
    load_raw,
    model_input,
    save_new,
    scenario,
)
from src.es_historical_conditional.runner import economic_trial
import src.es_synthetic_market.rolling as rolling_module
from src.es_synthetic_market.core import ContractInput, QHInput, SyntheticMarketInput
import src.es_synthetic_market.core as core_module
import src.es_synthetic_market._baseline_core as baseline_core_module

START = "2025-01-01"
END_EXCLUSIVE = "2026-09-01"
SCENARIO = "ts_start__cap_old"
RUN_ID = "ES_HISTORICAL_CONDITIONAL_ts_start__cap_old__rolling2__D"
TIME_LIMIT = 30.0
GAP = 1e-4
ANNUAL_EFC_NUMERICAL_MARGIN = 1e-6


def apply_terminal_efc_reserve(
    remaining: dict[int, float], *, terminal_year: int,
    planning_reaches_segment_end: bool, reserve_efc: float,
) -> tuple[dict[int, float], float]:
    """Reduce only a non-final window's available EFC; never alter the annual budget."""
    adjusted = dict(remaining)
    withheld = 0.0
    if not planning_reaches_segment_end and terminal_year in adjusted:
        before = adjusted[terminal_year]
        adjusted[terminal_year] = max(0.0, before - reserve_efc)
        withheld = before - adjusted[terminal_year]
    return adjusted, withheld


class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong),
        ("PageFaultCount", ctypes.c_ulong),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t),
    ]


def memory_info() -> dict:
    counters = PROCESS_MEMORY_COUNTERS_EX()
    counters.cb = ctypes.sizeof(counters)
    get_process = ctypes.windll.kernel32.GetCurrentProcess
    get_process.restype = ctypes.c_void_p
    handle = get_process()
    get_memory = ctypes.windll.kernel32.K32GetProcessMemoryInfo
    get_memory.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong]
    get_memory.restype = ctypes.c_int
    ok = get_memory(
        handle, ctypes.byref(counters), counters.cb
    )
    if not ok:
        return {}
    return {
        "working_set_bytes": int(counters.WorkingSetSize),
        "peak_working_set_bytes": int(counters.PeakWorkingSetSize),
        "private_bytes": int(counters.PrivateUsage),
        "peak_pagefile_bytes": int(counters.PeakPagefileUsage),
    }


def prepare(out: Path):
    if out.exists():
        raise FileExistsError(f"output already exists: {out}")
    allowed = (ROOT / "output").resolve()
    out = out.resolve()
    if not out.is_relative_to(allowed) or out == allowed:
        raise ValueError("output must be a new directory below output")
    out.mkdir(parents=True, exist_ok=False)
    started = perf_counter()
    start = datetime.combine(date.fromisoformat(START), time(), tzinfo=MADRID)
    end = datetime.combine(date.fromisoformat(END_EXCLUSIVE), time(), tzinfo=MADRID)
    bundle = load_raw(ROOT / "input", start, end)
    keys = [(t, c) for t in ("ts_start", "ts_end") for c in ("cap_old", "cap_new")]
    native = {key: scenario(bundle, *key) for key in keys}
    common = complete_contracts(
        set.intersection(*(set(case["series"]) for case in native.values())), bundle.contracts
    )
    selected = scenario(bundle, "ts_start", "cap_old", restrict=common)
    summary = {
        "scope": "historical_conditional",
        "formal_approved": False,
        "period": [START, END_EXCLUSIVE],
        "target_qh": len(bundle.grid),
        "source_files": len(bundle.sources),
        "rejected_files": len(bundle.rejected),
        "selection": {"scenarios": [SCENARIO], "modes": ["rolling2"], "orders": ["D"]},
        "coverage": {},
        "results": [],
        "pressure_status": "NOT_RUN",
    }
    for key, case in native.items():
        restricted = scenario(bundle, *key, restrict=common)
        name = "__".join(key)
        summary["coverage"][name] = {
            "own_qh": case["manifest"]["selected_qh"],
            "common_qh": len(restricted["series"]),
            "native_budget": case["manifest"]["annual_efc_budget"],
            "common_budget": restricted["manifest"]["annual_efc_budget"],
            "segments": len(restricted["manifest"]["segments"]),
            "contracts": sum(set(c["slots"]) <= set(restricted["series"]) for c in bundle.contracts.values()),
        }
    args = SimpleNamespace(
        scenarios=[SCENARIO], modes=["rolling2"], orders=["D"],
        history_mode="delta", run_economic=True, time_limit=TIME_LIMIT,
        gap=GAP, presolve=False, start=START, end_exclusive=END_EXCLUSIVE,
        output=str(out),
    )
    preflight = build_preflight(args=args, bundle=bundle, cases={SCENARIO: selected}, summary=summary)
    preflight["coverage"]["common_mask_basis"] = ["__".join(k) for k in keys]
    preflight["selection"]["capacity_timetable_note"] = (
        "cap_old selected as the single representative scenario; its 16:00/16:30 historical "
        "switch remains a modelling assumption and the switch date is not evidenced"
    )
    preflight["preparation_wall_seconds"] = perf_counter() - started
    preflight["resource_after_preparation"] = memory_info()
    preflight["disk_free_bytes_after_preparation"] = shutil.disk_usage(out).free
    return bundle, native, selected, summary, preflight


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def input_from_saved_configuration(config: dict) -> SyntheticMarketInput:
    qhs = []
    for row in config.pop("qhs"):
        for key in ("start_utc", "end_utc", "afrr_gate_close_utc", "afrr_result_release_utc"):
            row[key] = _dt(row[key])
        qhs.append(QHInput(**row))
    contracts = []
    for row in config.pop("contracts"):
        for key in ("gate_close_utc", "result_release_utc", "delivery_start_utc", "delivery_end_utc"):
            row[key] = _dt(row[key])
        contracts.append(ContractInput(**row))
    config["annual_efc_budget"] = {int(k): v for k, v in config["annual_efc_budget"].items()}
    config["fixed_commitments"] = tuple(config["fixed_commitments"])
    return SyntheticMarketInput(qhs=tuple(qhs), contracts=tuple(contracts), **config)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--reuse-input-result")
    ns = parser.parse_args()
    out = Path(ns.output)
    total_started = perf_counter()
    if ns.reuse_input_result:
        source_result_path = Path(ns.reuse_input_result).resolve()
        if out.exists():
            raise FileExistsError(f"output already exists: {out}")
        allowed = (ROOT / "output").resolve()
        out = out.resolve()
        if not out.is_relative_to(allowed) or out == allowed:
            raise ValueError("output must be a new directory below output")
        out.mkdir(parents=True, exist_ok=False)
        with source_result_path.open(encoding="utf-8") as handle:
            source_result = json.load(handle)
        inp = input_from_saved_configuration(source_result["input_configuration"])
        source_dir = source_result_path.parent
        preflight = json.loads((source_dir / "preflight.json").read_text(encoding="utf-8"))
        preflight["output_plan"]["directory"] = str(out)
        preflight["reused_exact_input_configuration_from"] = str(source_result_path)
        preflight["input_reuse_reason"] = (
            "retry after a 3.6e-14 MWh rolling-boundary floating-point validation failure"
        )
        save_new(out / "preflight.json", preflight)
        shutil.copy2(source_dir / f"{SCENARIO}_own_manifest.json", out / f"{SCENARIO}_own_manifest.json")
        shutil.copy2(source_dir / f"{SCENARIO}_common_input.json", out / f"{SCENARIO}_common_input.json")
        old_summary = json.loads((source_dir / "summary.json").read_text(encoding="utf-8"))
        summary = {k: old_summary[k] for k in (
            "scope", "formal_approved", "period", "target_qh", "source_files",
            "rejected_files", "selection", "coverage"
        )}
        summary.update(results=[], pressure_status="NOT_RUN",
                       reused_exact_input_configuration_from=str(source_result_path))
    else:
        bundle, native, selected, summary, preflight = prepare(out)
        save_new(out / "preflight.json", preflight)
    if ns.preflight_only:
        summary["preflight_only"] = True
        summary["total_wall_seconds"] = perf_counter() - total_started
        save_new(out / "summary.json", summary)
        print(json.dumps({"phase": "preflight", "output": str(out), "coverage": preflight["coverage"]}))
        return

    if not ns.reuse_input_result:
        save_new(out / f"{SCENARIO}_own_manifest.json", native[("ts_start", "cap_old")]["manifest"])
        save_new(out / f"{SCENARIO}_common_input.json", evidence_payload(bundle, selected))
        inp = model_input(bundle, selected)

    original_milp = scipy.optimize.milp
    original_window_input = rolling_module.RollingEngine._window_input
    original_core_canonical_trade = core_module._canonical_trade_mw
    original_baseline_canonical_trade = baseline_core_module._canonical_trade_mw
    calls: list[dict] = []
    numerical_soc_clamps: list[dict] = []
    terminal_reserve_applications: list[dict] = []
    reserve_bound_canonicalizations: list[dict] = []
    active_reserve_labels: list[dict] = []
    active_reserve_label_index = 0
    terminal_efc_reserve = max(
        0.0,
        (inp.e_max_mwh - inp.e_terminal_mwh)
        / (inp.eta_discharge * inp.cycle_denominator_mwh),
    )

    def stable_window_input(engine, *args, **kwargs):
        """Canonicalize solver-scale boundary noise before strict input validation."""
        nonlocal active_reserve_labels, active_reserve_label_index
        before = engine._soc
        if engine.inp.e_min_mwh - 1e-5 <= before < engine.inp.e_min_mwh:
            engine._soc = engine.inp.e_min_mwh
        elif engine.inp.e_max_mwh < before <= engine.inp.e_max_mwh + 1e-5:
            engine._soc = engine.inp.e_max_mwh
        if engine._soc != before:
            numerical_soc_clamps.append({
                "qh_id": engine.inp.qhs[engine._index].qh_id,
                "before_mwh": before,
                "after_mwh": engine._soc,
                "absolute_adjustment_mwh": abs(engine._soc - before),
            })
        window_input = original_window_input(engine, *args, **kwargs)
        win, frozen, frozen_reserve, remaining = window_input
        active_reserve_labels = (
            [{"direction": "up", "qh_id": q.qh_id} for q in win.qhs if q.qh_id not in frozen_reserve]
            + [{"direction": "down", "qh_id": q.qh_id} for q in win.qhs if q.qh_id not in frozen_reserve]
        )
        active_reserve_label_index = 0
        qhs = args[0]
        segment = engine._segment_rows[qhs[0].segment_id]
        planning_reaches_segment_end = qhs[-1].end_utc == segment[-1].end_utc
        terminal_year = segment[-1].madrid_year
        before = remaining.get(terminal_year)
        remaining, withheld = apply_terminal_efc_reserve(
            remaining, terminal_year=terminal_year,
            planning_reaches_segment_end=planning_reaches_segment_end,
            reserve_efc=terminal_efc_reserve,
        )
        # Keep fixed commitments from landing exactly on the next window's
        # annual-budget boundary.  This only reduces available EFC.
        remaining = {
            year: max(0.0, value - ANNUAL_EFC_NUMERICAL_MARGIN)
            for year, value in remaining.items()
        }
        if withheld:
            terminal_reserve_applications.append({
                "window_start_qh_id": qhs[0].qh_id,
                "segment_id": qhs[0].segment_id,
                "terminal_year": terminal_year,
                "remaining_before_efc": before,
                "remaining_after_efc": remaining[terminal_year],
                "withheld_efc": withheld,
            })
        return win, frozen, frozen_reserve, remaining

    def tolerant_canonical_trade(value):
        nonlocal active_reserve_label_index
        value = float(value)
        label = (active_reserve_labels[active_reserve_label_index]
                 if active_reserve_label_index < len(active_reserve_labels)
                 else {"direction": "unknown", "qh_id": None})
        active_reserve_label_index += 1
        if not isfinite(value) or value < -1e-5 or value > 100.0 + 1e-5:
            raise ValueError("solver trade materially outside [0,100] MW")
        adjusted = min(100.0, max(0.0, value))
        if adjusted != value:
            reserve_bound_canonicalizations.append({
                "solver_call_number": len(calls),
                **label,
                "original_mw": value,
                "adjusted_mw": adjusted,
                "absolute_adjustment_mw": abs(adjusted - value),
            })
        return adjusted

    def timed_milp(*args, **kwargs):
        call_number = len(calls) + 1
        started = perf_counter()
        result = original_milp(*args, **kwargs)
        elapsed = perf_counter() - started
        row = {
            "call_number": call_number,
            "solver_seconds": elapsed,
            "success": bool(result.success),
            "status_code": int(result.status),
            "message": str(result.message),
            "mip_gap": None if getattr(result, "mip_gap", None) is None else float(result.mip_gap),
            "mip_node_count": None if getattr(result, "mip_node_count", None) is None else int(result.mip_node_count),
            "objective_minimization": None if result.fun is None else float(result.fun),
            "resource_after_call": memory_info(),
        }
        calls.append(row)
        if call_number == 1 or call_number % 25 == 0:
            print(json.dumps({"progress_solver_calls": call_number, "last_solver_seconds": elapsed,
                              "last_gap": row["mip_gap"]}), flush=True)
        return result

    scipy.optimize.milp = timed_milp
    rolling_module.RollingEngine._window_input = stable_window_input
    core_module._canonical_trade_mw = tolerant_canonical_trade
    baseline_core_module._canonical_trade_mw = tolerant_canonical_trade
    trial_started = perf_counter()
    try:
        result = economic_trial(
            inp, RUN_ID, "rolling2", "D", TIME_LIMIT, GAP,
            history_mode="delta", presolve=False,
        )
    finally:
        trial_wall = perf_counter() - trial_started
        scipy.optimize.milp = original_milp
        rolling_module.RollingEngine._window_input = original_window_input
        core_module._canonical_trade_mw = original_core_canonical_trade
        baseline_core_module._canonical_trade_mw = original_baseline_canonical_trade

    result_path = out / f"{RUN_ID}.json"
    save_started = perf_counter()
    save_new(result_path, result)
    result_save_wall = perf_counter() - save_started
    windows = result["source_result"]["windows"]
    if len(calls) != len(windows):
        raise AssertionError(f"solver call/window mismatch: {len(calls)} != {len(windows)}")
    window_rows = []
    for call, window in zip(calls, windows):
        window_rows.append({
            **call,
            "start_utc": window["start_utc"],
            "window_end_utc": window["window_end_utc"],
            "execute_end_utc": window["execute_end_utc"],
            "executed_qh": len(window["executed_qh_ids"]),
            "planned_qh": len(window["planned_qh_ids"]),
            "execution_cash_eur": window["execution_cash_eur"],
            "objective_eur": window["objective_eur"],
            "upper_bound_eur": window["upper_bound_eur"],
            "absolute_gap_eur": window["absolute_gap_eur"],
            "relative_gap": window["relative_gap"],
            "raw_solver_gap": window["raw_solver_gap"],
            "proven_optimal": window["proven_optimal"],
        })
    gap_values = [w["relative_gap"] for w in windows if w["relative_gap"] is not None]
    status_counts = Counter(call["status_code"] for call in calls)
    timing = {
        "schema": "ES_FULL_TS_START_CAP_OLD_D_TIMING_V1",
        "period_local": [START, END_EXCLUSIVE],
        "scenario": SCENARIO,
        "mode": "rolling2",
        "order": "D",
        "solver_configuration": result["solver_configuration"],
        "solver_calls": len(calls),
        "solver_status_code_counts": {str(k): v for k, v in sorted(status_counts.items())},
        "pure_solver_seconds": sum(c["solver_seconds"] for c in calls),
        "economic_trial_wall_seconds": trial_wall,
        "result_save_wall_seconds": result_save_wall,
        "total_wall_seconds": perf_counter() - total_started,
        "peak_working_set_bytes": memory_info().get("peak_working_set_bytes"),
        "disk_free_bytes_at_end": shutil.disk_usage(out).free,
        "window_relative_gap_max": max(gap_values, default=None),
        "window_relative_gap_mean": sum(gap_values) / len(gap_values) if gap_values else None,
        "proven_optimal_windows": sum(w["proven_optimal"] for w in windows),
        "numerical_soc_clamps": numerical_soc_clamps,
        "numerical_soc_clamp_count": len(numerical_soc_clamps),
        "numerical_soc_clamp_max_mwh": max(
            (r["absolute_adjustment_mwh"] for r in numerical_soc_clamps), default=0.0
        ),
        "terminal_efc_reserve_policy": {
            "enabled": True,
            "reserve_efc": terminal_efc_reserve,
            "formula": "(e_max_mwh - e_terminal_mwh) / (eta_discharge * cycle_denominator_mwh)",
            "rule": "withhold worst-case EFC to return from e_max to e_terminal until the planning window reaches the segment end",
            "does_not_change_annual_budget": True,
            "does_not_change_objective_physics_or_settlement": True,
            "annual_efc_numerical_margin": ANNUAL_EFC_NUMERICAL_MARGIN,
            "numerical_margin_only_reduces_available_efc": True,
            "affected_window_count": len(terminal_reserve_applications),
            "applications": terminal_reserve_applications,
        },
        "reserve_bound_canonicalization": {
            "allowed_interval_mw": [-1e-5, 100.00001],
            "rule": "clip only solver-scale reserve values below 0 to 0 or above 100 to 100; fail outside interval",
            "count": len(reserve_bound_canonicalizations),
            "max_adjustment_mw": max(
                (r["absolute_adjustment_mw"] for r in reserve_bound_canonicalizations), default=0.0
            ),
            "records": reserve_bound_canonicalizations,
        },
        "windows": window_rows,
    }
    save_new(out / "solver_timing.json", timing)
    summary["results"].append({
        "scenario": SCENARIO, "mode": "rolling2", "order": "D",
        "status": result["status"], "gross_eur": result["valid_gross_eur"],
    })
    summary.update({
        "pressure_status": "MEASURED",
        "solver_calls": len(calls),
        "pure_solver_seconds": timing["pure_solver_seconds"],
        "economic_trial_wall_seconds": trial_wall,
        "total_wall_seconds": timing["total_wall_seconds"],
        "peak_working_set_bytes": timing["peak_working_set_bytes"],
        "result_file_bytes": result_path.stat().st_size,
        "window_status_code_counts": timing["solver_status_code_counts"],
        "window_relative_gap_max": timing["window_relative_gap_max"],
        "window_relative_gap_mean": timing["window_relative_gap_mean"],
        "proven_optimal_windows": timing["proven_optimal_windows"],
        "failed_windows": sum(not c["success"] for c in calls),
        "numerical_soc_clamp_count": timing["numerical_soc_clamp_count"],
        "numerical_soc_clamp_max_mwh": timing["numerical_soc_clamp_max_mwh"],
        "terminal_efc_reserve_policy": timing["terminal_efc_reserve_policy"],
        "reserve_bound_canonicalization_count": timing["reserve_bound_canonicalization"]["count"],
        "reserve_bound_canonicalization_max_mw": timing["reserve_bound_canonicalization"]["max_adjustment_mw"],
    })
    save_new(out / "summary.json", summary)
    print(json.dumps({"phase": "complete", "output": str(out), "summary": summary}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
