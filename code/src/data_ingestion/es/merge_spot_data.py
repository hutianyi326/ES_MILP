"""Merge the conditional NM sample with Combined and REE eSIOS inputs.

The output is deliberately hourly because the NM calibration window is hourly.
The Combined workbook and eSIOS sources are quarter-hourly; continuous values
are averaged over the four quarter-hours and counts are retained for audit.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
NM_PATH = ROOT / "data/processed/ES/omie_near_marginal_hourly_20250101_20250318_evening.csv"
COMBINED_PATH = ROOT / "data/raw/ES/Spain_Combined_Data.xlsx"
PROCESSED_ROOT = ROOT / "data/processed/ES"
MERGED_PATH = PROCESSED_ROOT / "es_spot_nm_combined_20250101_20250318_evening.csv"
QUALITY_PATH = PROCESSED_ROOT / "es_spot_nm_combined_quality_20250101_20250318_evening.json"


COMBINED_RENAME = {
    "Date (GMT+1)": "local_datetime_naive",
    "Hydro pumped storage consumption": "pumped_storage_consumption_mw",
    "Battery Consumption": "battery_consumption_mw",
    "Cross border electricity trading": "cross_border_trading_mw",
    "Nuclear": "nuclear_output_mw",
    "Hydro Run-of-River": "hydro_run_of_river_mw",
    "Biomass": "biomass_output_mw",
    "Fossil hard coal": "coal_output_mw",
    "Fossil oil": "oil_output_mw",
    "Fossil gas": "gas_output_mw",
    "Hydro water reservoir": "hydro_reservoir_output_mw",
    "Hydro pumped storage": "pumped_hydro_output_mw",
    "Battery": "battery_output_mw",
    "Others": "other_output_mw",
    "Other renewables": "other_renewables_output_mw",
    "Waste": "waste_output_mw",
    "Wind onshore": "wind_output_mw",
    "Solar": "solar_output_mw",
    "Load": "load_mw",
    "Day Ahead Auction (ES)": "combined_da_price_eur_mwh",
    "Analysis Month": "analysis_month",
    "Analysis Hour": "analysis_hour",
}


def _latest(pattern: str) -> Path | None:
    candidates = sorted(PROCESSED_ROOT.glob(pattern), key=lambda path: path.stat().st_mtime)
    return candidates[-1] if candidates else None


def _load_combined() -> tuple[pd.DataFrame, dict[str, object]]:
    raw = pd.read_excel(COMBINED_PATH, sheet_name="Combined", header=None)
    headers = [str(value).strip() if not pd.isna(value) else f"unnamed_{idx}" for idx, value in enumerate(raw.iloc[0])]
    frame = raw.iloc[2:].copy()
    frame.columns = headers
    frame = frame.rename(columns=COMBINED_RENAME)
    frame["local_datetime_naive"] = pd.to_datetime(frame["local_datetime_naive"], errors="coerce")
    frame = frame[frame["local_datetime_naive"].notna()].copy()
    frame["delivery_date"] = frame["local_datetime_naive"].dt.strftime("%Y-%m-%d")
    frame["hour"] = frame["local_datetime_naive"].dt.hour + 1
    frame = frame[(frame["delivery_date"] >= "2025-01-01") & (frame["delivery_date"] <= "2025-03-18") & frame["hour"].between(20, 23)].copy()
    numeric_columns = [column for column in COMBINED_RENAME.values() if column not in {"local_datetime_naive", "analysis_month", "analysis_hour"}]
    for column in numeric_columns:
        if column in frame:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    aggregation = {column: "mean" for column in numeric_columns if column in frame}
    grouped = frame.groupby(["delivery_date", "hour"], as_index=False).agg(aggregation)
    counts = frame.groupby(["delivery_date", "hour"], as_index=False).size().rename(columns={"size": "quarter_hour_count"})
    price_range = frame.groupby(["delivery_date", "hour"], as_index=False)["combined_da_price_eur_mwh"].agg(combined_price_min="min", combined_price_max="max")
    grouped = grouped.merge(counts, on=["delivery_date", "hour"], how="left").merge(price_range, on=["delivery_date", "hour"], how="left")
    grouped["combined_price_consistent"] = (grouped["combined_price_max"] - grouped["combined_price_min"]).abs() <= 1e-9
    grouped["hydro_conventional_output_mw"] = grouped["hydro_run_of_river_mw"].fillna(0) + grouped["hydro_reservoir_output_mw"].fillna(0)
    grouped["hydro_output_mw"] = grouped["hydro_conventional_output_mw"].fillna(0) + grouped["pumped_hydro_output_mw"].fillna(0)
    # Combined labels the gas column as Fossil gas; using it as CCGT is a
    # transparent research proxy and not an official unit-level technology map.
    grouped["ccgt_output_mw_proxy"] = grouped["gas_output_mw"]
    grouped["rl_dom_mw"] = grouped["load_mw"] - grouped["wind_output_mw"] - grouped["solar_output_mw"]
    # The Combined series is negative during the known midday export window
    # and positive during the evening import window.  Convert its apparent
    # net-import sign convention to an explicit net-export field while
    # retaining the original source column unchanged.
    grouped["net_export_mw"] = -grouped["cross_border_trading_mw"]
    grouped["rl_adj_mw"] = grouped["rl_dom_mw"] + grouped["net_export_mw"]
    return grouped, {"source": str(COMBINED_PATH), "raw_rows_in_window": int(len(frame)), "hourly_rows": int(len(grouped)), "quarter_hour_count_distribution": {str(key): int(value) for key, value in frame.groupby(["delivery_date", "hour"]).size().value_counts().sort_index().items()}}


def _load_esios(path: Path | None, dataset: str) -> tuple[pd.DataFrame, dict[str, object]]:
    if path is None or not path.exists():
        return pd.DataFrame(columns=["delivery_date", "hour"]), {"path": None, "rows": 0, "status": "missing"}
    frame = pd.read_csv(path)
    frame["datetime_local_parsed"] = pd.to_datetime(frame["datetime_local"], errors="coerce")
    frame = frame[frame["datetime_local_parsed"].notna()].copy()
    frame["delivery_date"] = frame["datetime_local_parsed"].dt.strftime("%Y-%m-%d")
    frame["hour"] = frame["datetime_local_parsed"].dt.hour + 1
    frame = frame[(frame["delivery_date"] >= "2025-01-01") & (frame["delivery_date"] <= "2025-03-18") & frame["hour"].between(20, 23)].copy()
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    if dataset == "demand_real":
        grouped = frame.groupby(["delivery_date", "hour"], as_index=False).agg(
            ree_demand_real_mw=("value", "mean"),
            esios_demand_qh_count=("value", "count"),
            ree_demand_updated_at=("values_updated_at", "first"),
        )
    else:
        grouped = frame.pivot_table(index=["delivery_date", "hour"], columns="indicator_id", values="value", aggfunc="mean").reset_index()
        grouped = grouped.rename(columns={"763": "imbalance_up_price_eur_mwh", "764": "imbalance_down_price_eur_mwh", 763: "imbalance_up_price_eur_mwh", 764: "imbalance_down_price_eur_mwh"})
        for column in ("imbalance_up_price_eur_mwh", "imbalance_down_price_eur_mwh"):
            if column not in grouped:
                grouped[column] = pd.NA
        counts = frame.pivot_table(index=["delivery_date", "hour"], columns="indicator_id", values="value", aggfunc="count").reset_index()
        counts = counts.rename(columns={"763": "esios_imbalance_up_qh_count", "764": "esios_imbalance_down_qh_count", 763: "esios_imbalance_up_qh_count", 764: "esios_imbalance_down_qh_count"})
        for column in ("esios_imbalance_up_qh_count", "esios_imbalance_down_qh_count"):
            if column not in counts:
                counts[column] = 0
        grouped = grouped.merge(counts, on=["delivery_date", "hour"], how="left")
    return grouped, {"path": str(path), "rows": int(len(frame)), "hourly_rows": int(len(grouped)), "status": "loaded"}


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8")


def run() -> dict[str, object]:
    nm = pd.read_csv(NM_PATH)
    nm["delivery_date"] = nm["delivery_date"].astype(str)
    nm["hour"] = pd.to_numeric(nm["hour"], errors="coerce").astype("Int64")
    combined, combined_quality = _load_combined()
    demand_path = _latest("esios_demand_real_20250101_20250318_*.csv")
    imbalance_path = _latest("esios_imbalance_20250101_20250318_*.csv")
    demand, demand_quality = _load_esios(demand_path, "demand_real")
    imbalance, imbalance_quality = _load_esios(imbalance_path, "imbalance")

    merged = nm.merge(combined, on=["delivery_date", "hour"], how="left", validate="one_to_one", suffixes=("", "_combined"))
    merged = merged.merge(demand, on=["delivery_date", "hour"], how="left", validate="one_to_one")
    merged = merged.merge(imbalance, on=["delivery_date", "hour"], how="left", validate="one_to_one")
    merged["da_price_difference_nm_vs_combined_eur_mwh"] = merged["price_eur_mwh"] - merged["combined_da_price_eur_mwh"]
    merged["data_date_timezone"] = "Europe/Madrid"
    merged["combined_resolution"] = "15min_source_aggregated_to_hour"
    merged["combined_price_source"] = "user_provided_Energy_Chart_export_cleaned_15min"
    merged["combined_price_aggregation_note"] = "user_note_possible_average_of_prior_5min_values_not_independently_verified"
    merged["esios_resolution"] = "requested_15min_aggregated_to_hour"
    merged["esios_demand_native_resolution"] = "5min_metadata_Cinco_minutos"
    merged["esios_imbalance_native_resolution"] = "15min_metadata_Quince_minutos"
    # Battery Consumption is blank in the supplied Combined source window.
    # Keep that raw-derived column unchanged and expose a separate research
    # field for the user's no-installed-battery assumption.
    merged["battery_consumption_research_mw"] = merged["battery_consumption_mw"].fillna(0.0)
    merged["battery_consumption_research_assumption"] = "source_blank_assumed_zero_no_storage_installed"
    merged["crosswalk_version"] = merged["crosswalk_version"].fillna("current_OMIE_LIST_20260904_CONDITIONAL")
    merged["merge_status"] = "conditional_diagnostic"
    merged["imbalance_source_status"] = "REE_eSIOS_loaded" if not imbalance.empty else "missing"
    # Keep the key columns first and make the remaining schema deterministic.
    key_columns = ["delivery_date", "hour", "delivery_hour", "local_datetime", "price_eur_mwh", "price_regime", "official_setter_labels", "nm_total_mw", "nm_mapped_mw", "nm_unmapped_mw", "crosswalk_coverage"]
    remaining = [column for column in merged.columns if column not in key_columns]
    merged = merged[key_columns + remaining]
    _write_csv(MERGED_PATH, merged)

    numeric_fields = [column for column in merged.columns if column.endswith("_mw") or column.endswith("_eur_mwh") or column.endswith("_output_mw") or column.endswith("_count")]
    missing = {column: int(merged[column].isna().sum()) for column in numeric_fields if column in merged and merged[column].isna().sum()}
    quality = {
        "status": "conditional_diagnostic",
        "timezone": "Europe/Madrid",
        "join_key": ["delivery_date", "hour"],
        "merged_rows": int(len(merged)),
        "unique_join_keys": int(merged[["delivery_date", "hour"]].drop_duplicates().shape[0]),
        "missing_numeric_fields": missing,
        "price_difference_max_abs": float(merged["da_price_difference_nm_vs_combined_eur_mwh"].abs().max()) if len(merged) else None,
        "price_difference_mismatch_count_gt_0_001": int((merged["da_price_difference_nm_vs_combined_eur_mwh"].abs() > 0.001).sum()),
        "combined": combined_quality,
        "demand_real": demand_quality,
        "imbalance": imbalance_quality,
        "outputs": {"merged": str(MERGED_PATH), "quality": str(QUALITY_PATH)},
        "assumptions": {
            "gas_as_ccgt_proxy": True,
            "positive_cross_border_is_import": True,
            "negative_cross_border_is_export": True,
            "cross_border_sign_basis": "midday_Combined_negative_and_REE_P48_import_export_sign_sample",
            "hourly_mean_for_15min_inputs": True,
            "battery_consumption_blank_assumed_zero_research_field": True,
            "current_crosswalk_is_conditional": True,
        },
        "combined_price_provenance": {
            "source": "user_provided_Energy_Chart_export",
            "source_resolution": "cleaned_15min",
            "user_note": "possibly_direct_average_of_prior_5min_values",
            "independently_verified": False,
            "use_as_nm_price_basis": False,
        },
        "resolution_audit": {
            "demand_real_native_metadata": "Cinco minutos",
            "demand_real_api_request": "fifteen_minutes with time_agg=average",
            "demand_real_observed_counts": "288/day at five_minutes; 96/day at fifteen_minutes",
            "imbalance_native_metadata": "Quince minutos",
            "hourly_merge": "arithmetic_mean_of_four_15min_values",
        },
    }
    QUALITY_PATH.write_text(json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8")
    return quality


def main() -> int:
    parser = argparse.ArgumentParser(prog="merge-es-spot-data")
    parser.parse_args()
    quality = run()
    print(json.dumps({key: value for key, value in quality.items() if key not in {"missing_numeric_fields", "combined", "demand_real", "imbalance"}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
