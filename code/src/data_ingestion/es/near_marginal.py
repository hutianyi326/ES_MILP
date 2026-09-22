"""Conditional near-marginal stack and setter calibration for Spain.

This module intentionally keeps the current OMIE unit list as a conditional
crosswalk.  It is therefore a diagnostic calibration, not historical ground
truth.  All calculations use the 2025-01-01--2025-03-18 evening window that
has an OMIE multi-label price-setting label and cleaned UOF matched sell rows.
"""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
UOF_PATH = ROOT / "data/processed/ES/omie_uof_sell_matched_20250101_20250318_evening.csv"
PRICE_PATH = ROOT / "data/processed/ES/omie_spot_20250101_20250318.csv"
SETTER_PATH = ROOT / "data/processed/ES/official_setter_20250101_20250318.csv"
CROSSWALK_PATH = ROOT / "data/processed/ES/omie_uof_technology_crosswalk_candidate_20260904.csv"
DETAIL_PATH = ROOT / "data/processed/ES/omie_near_marginal_20250101_20250318_evening.csv"
HOURLY_PATH = ROOT / "data/processed/ES/omie_near_marginal_hourly_20250101_20250318_evening.csv"
METRICS_PATH = ROOT / "data/processed/ES/omie_near_marginal_calibration_20250101_20250318_evening.csv"

CROSSWALK_VERSION = "current_OMIE_LIST_20260904_CONDITIONAL"
RELATIVE_WINDOWS = (("relative_90", 0.90), ("relative_925", 0.925), ("relative_95", 0.95), ("relative_975", 0.975))
ABSOLUTE_WINDOW = ("absolute_5", 5.0)
SHARE_THRESHOLDS = (0.0, 0.05, 0.10, 0.20, 0.30)
COMMON_TECHS = ("CCGT", "Hydro", "PumpedHydro", "Wind", "SolarPV", "RenewCogRes", "Nuclear", "Coal", "Other")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _float(value: str | None) -> float:
    try:
        return float(value or "")
    except (TypeError, ValueError):
        return math.nan


def _canonical_technology(value: str | None) -> str:
    """Align current-list labels with the coarser official setter labels.

    The official monthly setter table has an ``Other`` bucket and does not
    expose separate labels for solar thermal, storage or other thermal units.
    These are retained in the detail output but collapsed only for the
    precision/recall evaluation.
    """

    value = (value or "").strip()
    if not value:
        return "unmapped"
    if value in {"OtherThermal", "SolarThermal", "Storage"}:
        return "Other"
    return value if value in COMMON_TECHS else "Other"


def _setter_labels(row: dict[str, str]) -> set[str]:
    labels = set()
    for label in (row.get("setter_labels") or "").split("|"):
        label = label.strip()
        if label in COMMON_TECHS:
            labels.add(label)
        elif label in {"ImportPortugal", "InternationalInterchange"}:
            # These labels cannot be represented by Spain generation UOF rows;
            # they remain in the source setter file but are outside this
            # generation-stack evaluation universe.
            continue
    return labels


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _choose_market_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Use MI when present, otherwise ES for a delivery hour.

    This follows the frozen baseline: MI is the coupled market curve and ES is
    used when the market is split.  PT and explicit interconnection rows are
    not included in the Spain generation stack.
    """

    mi = [row for row in rows if row.get("country_code") == "MI"]
    if mi:
        return mi
    return [row for row in rows if row.get("country_code") == "ES"]


def _bounds(window: str, parameter: float, price: float) -> tuple[float, float]:
    if window == "absolute_5":
        return price - parameter, price
    return parameter * price, price


def _metric(predicted: set[str], truth: set[str], technology: str) -> tuple[int, int, int, float, float, float]:
    pred = technology in predicted
    actual = technology in truth
    tp = int(pred and actual)
    fp = int(pred and not actual)
    fn = int((not pred) and actual)
    precision = tp / (tp + fp) if tp + fp else math.nan
    recall = tp / (tp + fn) if tp + fn else math.nan
    f1 = 2 * precision * recall / (precision + recall) if precision == precision and recall == recall and precision + recall else math.nan
    return tp, fp, fn, precision, recall, f1


def main() -> dict[str, object]:
    uof_rows = _read_csv(UOF_PATH)
    price_rows = _read_csv(PRICE_PATH)
    setter_rows = _read_csv(SETTER_PATH)
    crosswalk_rows = _read_csv(CROSSWALK_PATH)

    crosswalk = {row.get("unit_of_offer", ""): row for row in crosswalk_rows}
    prices: dict[tuple[str, int], float] = {}
    for row in price_rows:
        try:
            period = int(row.get("period", ""))
        except ValueError:
            continue
        if 20 <= period <= 23:
            prices[(row.get("delivery_date", ""), period)] = _float(row.get("price_es_eur_mwh"))

    setters: dict[tuple[str, int], dict[str, object]] = {}
    for row in setter_rows:
        try:
            hour = int(row.get("Hour", ""))
        except ValueError:
            continue
        if 20 <= hour <= 23:
            setters[(row.get("Date", ""), hour)] = {"labels": _setter_labels(row), "row": row}

    grouped: dict[tuple[str, int], list[dict[str, str]]] = defaultdict(list)
    for row in uof_rows:
        try:
            hour = int(row.get("Hour", ""))
        except ValueError:
            continue
        if 20 <= hour <= 23:
            grouped[(row.get("delivery_date", ""), hour)].append(row)

    keys = sorted(set(grouped) & set(prices) & set(setters))
    detail: list[dict[str, object]] = []
    hourly: list[dict[str, object]] = []
    # Stores predicted sets for the metric table: (window, share_basis,
    # threshold) -> list of (prediction, truth, date, hour, price).
    evaluations: dict[tuple[str, str, float], list[tuple[set[str], set[str], str, int, float]]] = defaultdict(list)

    for delivery_date, hour in keys:
        price = prices[(delivery_date, hour)]
        regime = "positive" if price > 0 else "zero" if price == 0 else "negative"
        selected = _choose_market_rows(grouped[(delivery_date, hour)])
        truth = setters[(delivery_date, hour)]["labels"]  # type: ignore[assignment]
        by_window: dict[str, dict[str, float]] = {}
        mapped_by_window: dict[str, float] = {}
        all_by_window: dict[str, float] = {}
        window_specs = list(RELATIVE_WINDOWS) + [ABSOLUTE_WINDOW]
        for window, parameter in window_specs:
            low, high = _bounds(window, parameter, price)
            by_technology: dict[str, float] = defaultdict(float)
            for row in selected:
                offer_price = _float(row.get("price_eur_mwh"))
                energy = _float(row.get("energy_mwh"))
                if not (offer_price == offer_price and energy == energy):
                    continue
                if low <= offer_price <= high:
                    raw_technology = (crosswalk.get(row.get("unit_of_offer", ""), {}).get("mapped_technology") or "").strip() or "unmapped"
                    canonical = _canonical_technology(raw_technology)
                    by_technology[raw_technology] += energy
            mapped_energy = sum(value for tech, value in by_technology.items() if tech != "unmapped")
            all_energy = sum(by_technology.values())
            by_window[window] = dict(by_technology)
            mapped_by_window[window] = mapped_energy
            all_by_window[window] = all_energy
            for raw_technology, nm_mw in sorted(by_technology.items()):
                detail.append(
                    {
                        "delivery_date": delivery_date,
                        "hour": hour,
                        "delivery_hour": hour - 1,
                        "price_eur_mwh": round(price, 6),
                        "price_regime": regime,
                        "window": window,
                        "window_parameter": parameter,
                        "lower_bound_eur_mwh": round(low, 6),
                        "upper_bound_eur_mwh": round(high, 6),
                        "raw_technology": raw_technology,
                        "evaluation_technology": _canonical_technology(raw_technology),
                        "nm_mw": round(nm_mw, 6),
                        "nmshare_all_selected": round(nm_mw / all_energy, 10) if all_energy else 0.0,
                        "nmshare_mapped_only": round(nm_mw / mapped_energy, 10) if mapped_energy and raw_technology != "unmapped" else 0.0,
                        "mapped_energy_mw": round(mapped_energy, 6),
                        "unmapped_energy_mw": round(by_technology.get("unmapped", 0.0), 6),
                        "nm_total_mw": round(all_energy, 6),
                        "crosswalk_version": CROSSWALK_VERSION,
                        "crosswalk_status": "conditional_current_list",
                    }
                )

        baseline = by_window["relative_95"]
        baseline_total = all_by_window["relative_95"]
        baseline_mapped = mapped_by_window["relative_95"]
        canonical_nm: dict[str, float] = defaultdict(float)
        for raw_technology, value in baseline.items():
            if raw_technology != "unmapped":
                canonical_nm[_canonical_technology(raw_technology)] += value
        primary_shares = {tech: (value / baseline_total if baseline_total else 0.0) for tech, value in canonical_nm.items()}
        mapped_shares = {tech: (value / baseline_mapped if baseline_mapped else 0.0) for tech, value in canonical_nm.items()}
        hourly_row: dict[str, object] = {
            "delivery_date": delivery_date,
            "hour": hour,
            "delivery_hour": hour - 1,
            "local_datetime": f"{delivery_date}T{hour - 1:02d}:00:00+01:00",
            "price_eur_mwh": round(price, 6),
            "price_regime": regime,
            "official_setter_labels": "|".join(sorted(truth)),
            "official_setter_count": len(truth),
            "nm_window": "relative_95",
            "nm_lower_bound_eur_mwh": round(0.95 * price, 6),
            "nm_total_mw": round(baseline_total, 6),
            "nm_mapped_mw": round(baseline_mapped, 6),
            "nm_unmapped_mw": round(baseline.get("unmapped", 0.0), 6),
            "crosswalk_coverage": round(baseline_mapped / baseline_total, 10) if baseline_total else 0.0,
            "crosswalk_version": CROSSWALK_VERSION,
        }
        for technology in COMMON_TECHS:
            hourly_row[f"{technology}_NM_MW"] = round(canonical_nm.get(technology, 0.0), 6)
            hourly_row[f"{technology}_NMShare_all"] = round(primary_shares.get(technology, 0.0), 10)
            hourly_row[f"{technology}_NMShare_mapped"] = round(mapped_shares.get(technology, 0.0), 10)
        hourly.append(hourly_row)

        for window, _parameter in list(RELATIVE_WINDOWS) + [ABSOLUTE_WINDOW]:
            raw = by_window[window]
            canonical: dict[str, float] = defaultdict(float)
            for raw_technology, value in raw.items():
                if raw_technology != "unmapped":
                    canonical[_canonical_technology(raw_technology)] += value
            total = all_by_window[window]
            mapped = mapped_by_window[window]
            for share_basis, denominator in (("all_selected", total), ("mapped_only", mapped)):
                shares = {tech: (value / denominator if denominator else 0.0) for tech, value in canonical.items()}
                for threshold in SHARE_THRESHOLDS:
                    predicted = {tech for tech, share in shares.items() if share > 0 and share >= threshold}
                    evaluations[(window, share_basis, threshold)].append((predicted, truth, delivery_date, hour, price))

    metric_rows: list[dict[str, object]] = []
    for (window, share_basis, threshold), observations in sorted(evaluations.items()):
        for technology in COMMON_TECHS:
            tps = fps = fns = 0
            for predicted, truth, _date, _hour, _price in observations:
                tp, fp, fn, _p, _r, _f1 = _metric(predicted, truth, technology)
                tps += tp; fps += fp; fns += fn
            precision = tps / (tps + fps) if tps + fps else math.nan
            recall = tps / (tps + fns) if tps + fns else math.nan
            f1 = 2 * precision * recall / (precision + recall) if precision == precision and recall == recall and precision + recall else math.nan
            metric_rows.append({
                "metric_family": "technology_multilabel",
                "window": window,
                "share_basis": share_basis,
                "share_threshold": threshold,
                "technology": technology,
                "observations": len(observations),
                "tp": tps,
                "fp": fps,
                "fn": fns,
                "precision": round(precision, 10) if precision == precision else "",
                "recall": round(recall, 10) if recall == recall else "",
                "f1": round(f1, 10) if f1 == f1 else "",
                "crosswalk_version": CROSSWALK_VERSION,
                "status": "conditional_diagnostic",
            })
        hits = sum(bool(predicted & truth) for predicted, truth, _date, _hour, _price in observations)
        rows_with_prediction = sum(bool(predicted) for predicted, _truth, _date, _hour, _price in observations)
        metric_rows.append({
            "metric_family": "multilabel_set_hit",
            "window": window,
            "share_basis": share_basis,
            "share_threshold": threshold,
            "technology": "predicted_set_nonempty_hit",
            "observations": len(observations),
            "hit_count": hits,
            "rows_with_prediction": rows_with_prediction,
            "hit_rate": round(hits / len(observations), 10) if observations else "",
            "crosswalk_version": CROSSWALK_VERSION,
            "status": "conditional_diagnostic",
        })

    # Separate top-1/top-2 rankings for the primary 95% window.
    for top_k in (1, 2):
        observations = []
        for delivery_date, hour in keys:
            price = prices[(delivery_date, hour)]
            selected = _choose_market_rows(grouped[(delivery_date, hour)])
            truth = setters[(delivery_date, hour)]["labels"]  # type: ignore[assignment]
            low, high = _bounds("relative_95", 0.95, price)
            canonical: dict[str, float] = defaultdict(float)
            for row in selected:
                op = _float(row.get("price_eur_mwh")); energy = _float(row.get("energy_mwh"))
                if op == op and energy == energy and low <= op <= high:
                    raw_technology = (crosswalk.get(row.get("unit_of_offer", ""), {}).get("mapped_technology") or "").strip()
                    if raw_technology:
                        canonical[_canonical_technology(raw_technology)] += energy
            ranked = [tech for tech, _value in sorted(canonical.items(), key=lambda item: (-item[1], item[0]))]
            predicted = set(ranked[:top_k])
            observations.append((predicted, truth))
        hit_count = sum(bool(predicted & truth) for predicted, truth in observations)
        metric_rows.append({
            "metric_family": "top_k_set_hit",
            "window": "relative_95",
            "share_basis": "all_selected",
            "share_threshold": "",
            "technology": f"top_{top_k}",
            "observations": len(observations),
            "top_k": top_k,
            "hit_count": hit_count,
            "hit_rate": round(hit_count / len(observations), 10) if observations else "",
            "crosswalk_version": CROSSWALK_VERSION,
            "status": "conditional_diagnostic",
        })

    _write_csv(DETAIL_PATH, detail)
    _write_csv(HOURLY_PATH, hourly)
    _write_csv(METRICS_PATH, metric_rows)
    return {
        "hours": len(keys),
        "detail_rows": len(detail),
        "hourly_rows": len(hourly),
        "metric_rows": len(metric_rows),
        "outputs": [str(DETAIL_PATH), str(HOURLY_PATH), str(METRICS_PATH)],
        "crosswalk_version": CROSSWALK_VERSION,
    }


if __name__ == "__main__":
    print(main())
