"""Read-only audit for the Spain perfect-information aFRR candidate mask.

This script does not call an API and never changes files under data/raw/ES.
It reads the already preserved JSON responses for indicators 632, 633, 680
and 681, constructs the accepted local-time window with zoneinfo, and writes
an auditable JSON summary beside this script.

The alpha calculation is explicitly conditional: the public API label for
680/681 is ``Energía`` but the public indicator-to-settlement/MWh crosswalk is
not closed.  The script therefore does not certify units, fill sparse values,
or authorize a production MILP input.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


UTC = dt.timezone.utc
MADRID = ZoneInfo("Europe/Madrid")
QH = dt.timedelta(minutes=15)
INDICATORS = (632, 633, 680, 681)
PENINSULA_GEO_ID = 8741
PENINSULA_GEO_NAME = "Península"
LOCAL_START = dt.datetime(2025, 1, 1, 0, 0, tzinfo=MADRID)
LOCAL_END_EXCLUSIVE = dt.datetime(2026, 9, 1, 0, 0, tzinfo=MADRID)
REJECTION_KEYS = (
    "json_parse_error",
    "indicator_id_mismatch",
    "indicator_id_missing",
    "row_not_object",
    "datetime_missing",
    "datetime_parse_error",
    "naive_datetime_rejected",
    "non_qh_timestamp_rejected",
    "geo_missing_or_not_peninsula",
    "value_parse_error",
    "nonfinite_value_rejected",
    "out_of_window_qh",
)


def iso(value: dt.datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def expected_utc_quarters() -> list[dt.datetime]:
    """Generate valid quarter starts from local window endpoints.

    The endpoint conversion is timezone-aware.  Stepping in UTC avoids
    inventing nonexistent local quarters during spring DST transitions and
    retains both real quarters during autumn transitions.
    """

    start = LOCAL_START.astimezone(UTC)
    end = LOCAL_END_EXCLUSIVE.astimezone(UTC)
    result: list[dt.datetime] = []
    current = start
    while current < end:
        result.append(current)
        current += QH
    return result


def parse_response(
    path: Path,
    expected_indicator_id: int,
    expected: set[dt.datetime],
) -> tuple[dict[str, Any], list[tuple[dt.datetime, float]], Counter[str], str, int]:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    stats: Counter[str] = Counter()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        stats["json_parse_error"] += 1
        return {}, [], stats, digest, len(raw)
    indicator = payload.get("indicator")
    if not isinstance(indicator, dict):
        stats["json_parse_error"] += 1
        return {}, [], stats, digest, len(raw)
    indicator_id = indicator.get("id")
    if indicator_id is None:
        stats["indicator_id_missing"] += 1
        return indicator, [], stats, digest, len(raw)
    try:
        indicator_id = int(indicator_id)
    except (TypeError, ValueError):
        stats["indicator_id_mismatch"] += 1
        return indicator, [], stats, digest, len(raw)
    if indicator_id != expected_indicator_id:
        stats["indicator_id_mismatch"] += 1
        return indicator, [], stats, digest, len(raw)

    rows: list[tuple[dt.datetime, float]] = []
    for item in indicator.get("values", []):
        if not isinstance(item, dict):
            stats["row_not_object"] += 1
            continue
        raw_datetime = item.get("datetime_utc")
        if not raw_datetime:
            stats["datetime_missing"] += 1
            continue
        try:
            timestamp = dt.datetime.fromisoformat(str(raw_datetime).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            stats["datetime_parse_error"] += 1
            continue
        if timestamp.tzinfo is None:
            stats["naive_datetime_rejected"] += 1
            continue
        timestamp = timestamp.astimezone(UTC)
        if timestamp.minute not in (0, 15, 30, 45) or timestamp.second != 0 or timestamp.microsecond != 0:
            stats["non_qh_timestamp_rejected"] += 1
            continue
        if item.get("geo_id") != PENINSULA_GEO_ID or item.get("geo_name") != PENINSULA_GEO_NAME:
            stats["geo_missing_or_not_peninsula"] += 1
            continue
        try:
            value = float(item["value"])
        except (KeyError, TypeError, ValueError):
            stats["value_parse_error"] += 1
            continue
        if not math.isfinite(value):
            stats["nonfinite_value_rejected"] += 1
            continue
        if timestamp not in expected:
            stats["out_of_window_qh"] += 1
            continue
        rows.append((timestamp, value))
    return indicator, rows, stats, digest, len(raw)


def load_series(project_root: Path, expected: set[dt.datetime]) -> tuple[
    dict[int, dict[dt.datetime, set[float]]],
    dict[int, dict[str, Any]],
    dict[int, Counter[dt.datetime]],
]:
    root = project_root / "data" / "raw" / "ES" / "esios"
    series: dict[int, dict[dt.datetime, set[float]]] = {indicator: defaultdict(set) for indicator in INDICATORS}
    occurrences: dict[int, Counter[dt.datetime]] = {indicator: Counter() for indicator in INDICATORS}
    file_meta: dict[int, dict[str, Any]] = {
        indicator: {
            "glob_pattern": f"data/raw/ES/esios/**/fetch_{indicator}.json",
            "scope_note": "Only files matching this exact fetch_ID.json pattern are read; other raw naming patterns are outside this audit.",
            "files_read": 0,
            "files_with_values": 0,
            "files_empty": 0,
            "paths": [],
            "sha256_by_file": {},
            "rejected_record_counts": Counter({key: 0 for key in REJECTION_KEYS}),
            "files": [],
        }
        for indicator in INDICATORS
    }

    for indicator in INDICATORS:
        for path in sorted(root.rglob(f"fetch_{indicator}.json")):
            file_meta[indicator]["files_read"] += 1
            relative_path = str(path.relative_to(project_root))
            file_meta[indicator]["paths"].append(relative_path)
            metadata, rows, parse_stats, digest, byte_count = parse_response(path, indicator, expected)
            file_meta[indicator]["sha256_by_file"][relative_path] = digest
            for key, count in parse_stats.items():
                file_meta[indicator]["rejected_record_counts"][key] += count
            file_meta[indicator]["files"].append(
                {
                    "path": relative_path,
                    "sha256": digest,
                    "bytes": byte_count,
                    "rejected_record_counts": dict(parse_stats),
                }
            )
            if rows:
                file_meta[indicator]["files_with_values"] += 1
            else:
                file_meta[indicator]["files_empty"] += 1
            for timestamp, value in rows:
                occurrences[indicator][timestamp] += 1
                series[indicator][timestamp].add(value)
            file_meta[indicator].setdefault("metadata_samples", []).append(
                {
                    "name": metadata.get("name"),
                    "step_type": metadata.get("step_type"),
                    "magnitud": [x.get("name") for x in metadata.get("magnitud", [])],
                    "tiempo": [x.get("name") for x in metadata.get("tiempo", [])],
                    "geos": [x.get("geo_name") for x in metadata.get("geos", [])],
                }
            )
    for indicator in INDICATORS:
        file_meta[indicator]["rejected_record_counts"] = dict(file_meta[indicator]["rejected_record_counts"])
    return series, file_meta, occurrences


def non_conflicting_value(series: dict[dt.datetime, set[float]], timestamp: dt.datetime) -> float | None:
    values = series.get(timestamp)
    if not values or len(values) != 1:
        return None
    return next(iter(values))


def runs_from_timestamps(timestamps: set[dt.datetime]) -> list[dict[str, Any]]:
    if not timestamps:
        return []
    ordered = sorted(timestamps)
    runs: list[dict[str, Any]] = []
    start = previous = ordered[0]
    for timestamp in ordered[1:]:
        if timestamp - previous == QH:
            previous = timestamp
            continue
        end_exclusive = previous + QH
        runs.append(
            {
                "start_utc": iso(start),
                "end_exclusive_utc": iso(end_exclusive),
                "start_madrid": start.astimezone(MADRID).isoformat(),
                "end_exclusive_madrid": end_exclusive.astimezone(MADRID).isoformat(),
                "qh_count": int((end_exclusive - start).total_seconds() / QH.total_seconds()),
                "duration_hours_utc": (end_exclusive - start).total_seconds() / 3600,
            }
        )
        start = previous = timestamp
    end_exclusive = previous + QH
    runs.append(
        {
            "start_utc": iso(start),
            "end_exclusive_utc": iso(end_exclusive),
            "start_madrid": start.astimezone(MADRID).isoformat(),
            "end_exclusive_madrid": end_exclusive.astimezone(MADRID).isoformat(),
            "qh_count": int((end_exclusive - start).total_seconds() / QH.total_seconds()),
            "duration_hours_utc": (end_exclusive - start).total_seconds() / 3600,
        }
    )
    return runs


def build_evidence(project_root: Path) -> dict[str, Any]:
    expected_list = expected_utc_quarters()
    expected = set(expected_list)
    series, file_meta, occurrences = load_series(project_root, expected)

    common = set.intersection(*(set(series[indicator]) for indicator in INDICATORS))
    common_no_conflicts = {
        timestamp
        for timestamp in common
        if all(len(series[indicator][timestamp]) == 1 for indicator in INDICATORS)
    }

    conditional_mappable: set[dt.datetime] = set()
    invalid_rows: list[dict[str, Any]] = []
    reason_counts: Counter[str] = Counter()
    alpha_up: list[float] = []
    alpha_down: list[float] = []

    for timestamp in sorted(common_no_conflicts):
        r_up, r_down, e_up, e_down = (non_conflicting_value(series[indicator], timestamp) for indicator in INDICATORS)
        if any(value is None or not math.isfinite(value) for value in (r_up, r_down, e_up, e_down)):
            reason_counts["nonfinite_or_missing"] += 1
            continue
        reasons: list[str] = []
        if r_up <= 0:
            reasons.append("zero_or_negative_up_reserve_denominator")
        if r_down <= 0:
            reasons.append("zero_or_negative_down_reserve_denominator")
        a_up = e_up / (r_up * 0.25) if r_up > 0 else None
        a_down = e_down / (r_down * 0.25) if r_down > 0 else None
        if a_up is not None:
            alpha_up.append(a_up)
        if a_down is not None:
            alpha_down.append(a_down)
        if a_up is None or a_down is None:
            reasons.append("undefined_alpha")
        else:
            if a_up < 0 or a_down < 0:
                reasons.append("negative_alpha")
            if a_up + a_down > 1:
                reasons.append("alpha_sum_gt_1")
        if reasons:
            for reason in reasons:
                reason_counts[reason] += 1
            invalid_rows.append(
                {
                    "timestamp_utc": iso(timestamp),
                    "timestamp_madrid": timestamp.astimezone(MADRID).isoformat(),
                    "r_up_632": r_up,
                    "r_down_633": r_down,
                    "e_up_680": e_up,
                    "e_down_681": e_down,
                    "alpha_up": a_up,
                    "alpha_down": a_down,
                    "reasons": reasons,
                }
            )
            continue
        conditional_mappable.add(timestamp)

    # Conflicting duplicate values are never silently merged.  They are
    # excluded from the candidate mask and reported separately.
    conflict_counts = {
        str(indicator): sum(1 for values in series[indicator].values() if len(values) > 1)
        for indicator in INDICATORS
    }
    candidate_runs = runs_from_timestamps(conditional_mappable)

    by_year: dict[str, int] = defaultdict(int)
    by_day: Counter[str] = Counter()
    for timestamp in expected_list:
        local = timestamp.astimezone(MADRID)
        by_year[str(local.year)] += 1
        by_day[local.date().isoformat()] += 1

    dst_days = {
        date: count for date, count in sorted(by_day.items()) if count != 96
    }

    return {
        "audit": {
            "name": "spain_perfect_information_aFRR_candidate_audit",
            "audit_date": "2026-09-20",
            "script": "countries/ES/audit_pi_candidate_20260920.py",
            "read_only": True,
            "credentials_used": False,
            "raw_overwritten": False,
        },
        "window": {
            "zone": "Europe/Madrid",
            "local_start_inclusive": LOCAL_START.isoformat(),
            "local_end_exclusive": LOCAL_END_EXCLUSIVE.isoformat(),
            "utc_start_inclusive": iso(LOCAL_START.astimezone(UTC)),
            "utc_end_exclusive": iso(LOCAL_END_EXCLUSIVE.astimezone(UTC)),
            "expected_qh_count": len(expected_list),
            "expected_qh_by_local_year": dict(sorted(by_year.items())),
            "dst_local_dates_with_non_96_qh": dst_days,
            "primary_key": "datetime_utc",
        },
        "indicators": [
            {"id": indicator, "role": role}
            for indicator, role in (
                (632, "up_reserve_power_candidate_denominator"),
                (633, "down_reserve_power_candidate_denominator"),
                (680, "up_activated_energy_candidate_numerator"),
                (681, "down_activated_energy_candidate_numerator"),
            )
        ],
        "raw_inventory": {
            str(indicator): file_meta[indicator] for indicator in INDICATORS
        },
        "coverage": {
            "unique_explicit_points": {str(indicator): len(series[indicator]) for indicator in INDICATORS},
            "duplicate_timestamp_points": {
                str(indicator): sum(1 for count in occurrences[indicator].values() if count > 1)
                for indicator in INDICATORS
            },
            "duplicate_value_conflicts": conflict_counts,
            "four_indicator_explicit_intersection": len(common),
            "four_indicator_nonconflicting_intersection": len(common_no_conflicts),
        },
        "conditional_mapping": {
            "status": "conditional_only_unit_and_public_settlement_crosswalk_unresolved",
            "formula_up": "E680_MWh / (R632_MW * 0.25_h)",
            "formula_down": "E681_MWh / (R633_MW * 0.25_h)",
            "no_fill_or_clip": True,
            "conditional_mappable_qh": len(conditional_mappable),
            "invalid_qh": len(invalid_rows),
            "invalid_reason_counts": dict(sorted(reason_counts.items())),
            "alpha_up_range_observed": [min(alpha_up), max(alpha_up)] if alpha_up else None,
            "alpha_down_range_observed": [min(alpha_down), max(alpha_down)] if alpha_down else None,
            "invalid_rows": invalid_rows,
        },
        "candidate_continuous_runs": {
            "definition": [
                "four explicit indicator points at the same UTC QH",
                "adjacent timestamps exactly 15 minutes apart",
                "finite, nonconflicting values and positive denominators",
                "conditional alpha values nonnegative and alpha_up + alpha_down <= 1",
                "no step expansion, forward-fill, interpolation, clipping, or normalization",
            ],
            "minimum_qh_count": 1,
            "note": "Seven days is a rolling optimization window, not a data acceptance threshold; short runs are retained and may use a shortened final window.",
            "count": len(candidate_runs),
            "runs": candidate_runs,
        },
        "market_status_policy": {
            "confirmed_cancelled_session": "not_tradable; exclude as market-status event, not as an unexplained missing price",
            "unknown_empty_or_unclassified": "exclude from the joint input mask and split the continuous interval",
            "final_price_revision_in_perfect_information_mode": "allowed as ex-post settlement input, with original publication/update metadata preserved",
        },
        "unresolved": [
            "Official public crosswalk and direct MWh/unit evidence for API indicators 680/681 to ESECS/ESECB or an equivalent settlement field.",
            "Whether 680/681 aggregate energy includes QHs with no matching 632/633 capacity allocation, non-capacity participants, or cross-border/PICASSO components.",
            "Whether datetime_utc denotes the start or end of the represented QH energy interval, including any boundary treatment.",
            "Joint alignment with all market price inputs and applicable market-regime/contract boundaries.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("audit_pi_candidate_20260920_evidence.json"),
        help="output JSON path; only this derived evidence file is written",
    )
    args = parser.parse_args()
    project_root = Path(__file__).resolve().parents[2]
    evidence = build_evidence(project_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "expected_qh_count": evidence["window"]["expected_qh_count"],
        "common_qh": evidence["coverage"]["four_indicator_nonconflicting_intersection"],
        "conditional_mappable_qh": evidence["conditional_mapping"]["conditional_mappable_qh"],
        "candidate_runs": evidence["candidate_continuous_runs"]["count"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
