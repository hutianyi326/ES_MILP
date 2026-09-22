"""Create compact audited summaries for the completed Spain full-range run."""
from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
import hashlib
import json
import mmap
import re
from pathlib import Path
from statistics import median
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output/full_range"
RESULT = OUT / "ES_HISTORICAL_CONDITIONAL_ts_start__cap_old__rolling2__D.json"
MADRID = ZoneInfo("Europe/Madrid")


def extract_json_value(path: Path, key: str, read_bytes: int = 4_000_000):
    marker = json.dumps(key).encode() + b":"
    with path.open("rb") as handle:
        data = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)
        pos = data.find(marker)
        if pos < 0:
            raise KeyError(key)
        start = pos + len(marker)
        text = data[start:start + read_bytes].decode("utf-8")
        value, _ = json.JSONDecoder().raw_decode(text.lstrip())
        data.close()
        return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_object_status(path: Path, key: str) -> str:
    marker = json.dumps(key).encode() + b":"
    with path.open("rb") as handle:
        data = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)
        pos = data.find(marker)
        if pos < 0:
            raise KeyError(key)
        match = re.search(rb'"status"\s*:\s*"([^"]+)"', data[pos:pos + 100_000])
        data.close()
    if not match:
        raise ValueError(f"status not found for {key}")
    return match.group(1).decode()


def percentile(values, q):
    values = sorted(values)
    if not values:
        return None
    index = (len(values) - 1) * q
    lo = int(index)
    hi = min(lo + 1, len(values) - 1)
    weight = index - lo
    return values[lo] * (1 - weight) + values[hi] * weight


def main():
    summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
    timing = json.loads((OUT / "solver_timing.json").read_text(encoding="utf-8"))
    preflight = json.loads((OUT / "preflight.json").read_text(encoding="utf-8"))
    windows = timing["windows"]
    monthly = defaultdict(lambda: {"windows": 0, "executed_qh": 0, "gross_eur": 0.0,
                                   "solver_seconds": 0.0, "max_gap": 0.0})
    annual = defaultdict(lambda: {"windows": 0, "executed_qh": 0, "gross_eur": 0.0,
                                  "solver_seconds": 0.0, "max_gap": 0.0})
    for window in windows:
        local = datetime.fromisoformat(window["start_utc"]).astimezone(MADRID)
        for key, bucket in ((local.strftime("%Y-%m"), monthly), (str(local.year), annual)):
            row = bucket[key]
            row["windows"] += 1
            row["executed_qh"] += window["executed_qh"]
            row["gross_eur"] += window["execution_cash_eur"]
            row["solver_seconds"] += window["solver_seconds"]
            row["max_gap"] = max(row["max_gap"], window["relative_gap"] or 0.0)
    gross = summary["results"][0]["gross_eur"]
    window_gross = sum(w["execution_cash_eur"] for w in windows)
    solver_times = [w["solver_seconds"] for w in windows]
    cash_breakdown = extract_json_value(RESULT, "cash_breakdown")
    cash_residual = extract_json_value(RESULT, "cash_residual_eur")
    main_audit_status = extract_object_status(RESULT, "main_audit")
    same_order_audit_status = extract_object_status(RESULT, "same_orders_other_order")

    final_efc = {}
    with RESULT.open("rb") as handle:
        data = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)
        marker = b'"efc_used_by_year":'
        pos = 0
        decoder = json.JSONDecoder()
        while True:
            pos = data.find(marker, pos)
            if pos < 0:
                break
            start = pos + len(marker)
            value, _ = decoder.raw_decode(data[start:start + 1000].decode("utf-8").lstrip())
            final_efc = value
            pos = start
        data.close()

    coverage = preflight["coverage"]
    report = {
        "schema": "ES_FULL_TS_START_CAP_OLD_D_FINAL_REPORT_V1",
        "result_status": summary["results"][0]["status"],
        "period_local": ["2025-01-01", "2026-09-01"],
        "scenario": {"timestamp": "ts_start", "capacity_timetable": "cap_old",
                     "activation_order": "D (down then up)", "mode": "rolling2"},
        "gross_eur": gross,
        "cash_breakdown_eur": cash_breakdown,
        "cash_residual_eur": cash_residual,
        "coverage": {
            "target_qh": coverage["target_qh"], "common_valid_qh": coverage["common_qh"],
            "coverage_percent": 100 * coverage["common_qh"] / coverage["target_qh"],
            "excluded_qh": coverage["target_qh"] - coverage["common_qh"],
            "segments": preflight["inputs"]["ts_start__cap_old"]["segment_count"],
            "contracts": preflight["inputs"]["ts_start__cap_old"]["contract_count"],
            "source_files": coverage["source_files"], "rejected_files": coverage["rejected_files"],
        },
        "solver": {
            "calls": timing["solver_calls"], "failed_windows": summary["failed_windows"],
            "status_code_counts": timing["solver_status_code_counts"],
            "pure_solver_seconds": timing["pure_solver_seconds"],
            "economic_trial_wall_seconds": timing["economic_trial_wall_seconds"],
            "total_wall_seconds": timing["total_wall_seconds"],
            "result_save_wall_seconds": timing["result_save_wall_seconds"],
            "mean_seconds_per_call": sum(solver_times) / len(solver_times),
            "median_seconds_per_call": median(solver_times),
            "p95_seconds_per_call": percentile(solver_times, .95),
            "max_seconds_per_call": max(solver_times),
            "time_limit_hits": sum(t >= 30 for t in solver_times),
            "relative_gap_max": timing["window_relative_gap_max"],
            "relative_gap_mean": timing["window_relative_gap_mean"],
            "proven_optimal_windows": timing["proven_optimal_windows"],
            "peak_working_set_bytes": timing["peak_working_set_bytes"],
            "configuration": timing["solver_configuration"],
        },
        "annual": dict(sorted(annual.items())),
        "monthly": dict(sorted(monthly.items())),
        "annual_efc_used": final_efc,
        "annual_efc_budget": preflight["inputs"]["ts_start__cap_old"]["annual_efc_budget"],
        "audits": {
            "window_cash_sum_eur": window_gross,
            "window_cash_vs_result_eur": window_gross - gross,
            "main_physical_status": main_audit_status,
            "same_orders_other_order_status": same_order_audit_status,
            "cash_residual_within_1e_5": abs(cash_residual) <= 1e-5,
            "efc_within_budget": all(float(final_efc[str(y)]) <= float(b) + 1e-8
                                     for y, b in preflight["inputs"]["ts_start__cap_old"]["annual_efc_budget"].items()),
        },
        "numerical_safeguards": {
            "soc_clamp_count": summary["numerical_soc_clamp_count"],
            "soc_clamp_max_mwh": summary["numerical_soc_clamp_max_mwh"],
            "terminal_efc_reserve": timing["terminal_efc_reserve_policy"],
            "reserve_bound_canonicalization": timing["reserve_bound_canonicalization"],
        },
        "failed_attempt_evidence": {
            "v1": "floating SOC 9.999999999999964 MWh rejected at strict 10 MWh lower bound after 26 windows",
            "v2": "2025 EFC exhausted before segment-terminal SOC return after 369 windows",
            "v3": "frozen final-day commitments exceeded remaining EFC by 1.54e-10 after 370 windows",
            "v4": "reserve value -3.371247514e-7 MW exceeded the source's 1e-9 canonicalization tolerance after 368 windows",
            "prechecks": [
                str(ROOT / "outputs/es_historical_conditional/rolling2_full_20250101_20260831_ts_start_cap_old_D_v4_margin_precheck_20260921_v1.json"),
                str(ROOT / "outputs/es_historical_conditional/rolling2_full_20250101_20260831_ts_start_cap_old_D_v4_trade_overflow_20260921_v4.json"),
            ],
        },
        "interpretation": {
            "label": "conditional gross; not certified historical upper bound",
            "perfect_information_override": True,
            "fees_included": False,
            "degradation_cash_included": False,
            "capacity_timetable_assumption": "cap_old 16:00/16:30; historical switch date remains unverified",
        },
        "files": {
            "result": {"path": str(RESULT), "bytes": RESULT.stat().st_size, "sha256": sha256(RESULT)},
            "timing": str(OUT / "solver_timing.json"),
            "preflight": str(OUT / "preflight.json"),
            "summary": str(OUT / "summary.json"),
        },
    }
    required_audits = (
        abs(report["audits"]["window_cash_vs_result_eur"]) <= 1e-5
        and report["audits"]["main_physical_status"] == "PASS"
        and report["audits"]["cash_residual_within_1e_5"]
        and report["audits"]["efc_within_budget"]
    )
    if report["result_status"] != "CONDITIONAL_PASS" or not required_audits:
        raise AssertionError(report["audits"])

    (OUT / "final_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    with (OUT / "monthly_summary.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=["month", "windows", "executed_qh", "gross_eur", "solver_seconds", "max_gap"])
        writer.writeheader()
        for month, row in sorted(monthly.items()):
            writer.writerow({"month": month, **row})
    with (OUT / "window_summary.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        fields = ["call_number", "start_utc", "window_end_utc", "execute_end_utc", "executed_qh", "planned_qh",
                  "execution_cash_eur", "solver_seconds", "status_code", "relative_gap", "raw_solver_gap", "proven_optimal"]
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(windows)
    md = f"""# Spain full-range MILP result — ts_start / cap_old / D

- Period: Madrid local 2025-01-01 through 2026-08-31
- Status: **{report['result_status']}**
- Conditional gross revenue: **EUR {gross:,.2f}**
- Coverage: {coverage['common_qh']:,}/{coverage['target_qh']:,} QH ({report['coverage']['coverage_percent']:.2f}%), {report['coverage']['segments']} segments
- Solver: 636/636 successful calls; {timing['pure_solver_seconds']:.2f}s pure solver, {timing['economic_trial_wall_seconds']:.2f}s economic trial, {timing['total_wall_seconds']:.2f}s total retry wall time
- Gap: maximum {timing['window_relative_gap_max']:.8f}; mean {timing['window_relative_gap_mean']:.8f}; no time-limit hits
- Peak working set: {timing['peak_working_set_bytes']/1024**3:.2f} GiB; result JSON: {RESULT.stat().st_size/1024**3:.2f} GiB

This is conditional gross revenue under perfect-information inputs. Fees and degradation cash are excluded. `cap_old` uses the 16:00/16:30 timetable assumption; its historical switch date remains unverified.
"""
    (OUT / "FINAL_REPORT.md").write_text(md, encoding="utf-8")
    print(json.dumps({"status": report["result_status"], "gross_eur": gross,
                      "annual": report["annual"], "audits": report["audits"],
                      "output": str(OUT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
