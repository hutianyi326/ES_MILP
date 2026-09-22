"""Descriptive mechanism analysis for the conditional near-marginal proxy.

The output is intentionally an ex-post, conditional diagnostic.  It joins the
extended proxy to REE eSIOS demand, P48 scheduled generation and imbalance
prices where the time resolutions match.  It does not infer an official setter,
unit-level price setter or causal effect.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
PROCESSED = ROOT / "data/processed/ES"
PROXY_HOURLY = PROCESSED / "omie_near_marginal_proxy_20250319_20250930_evening_hourly.csv"
PROXY_QH = PROCESSED / "omie_near_marginal_proxy_20251001_20260731_evening_15min.csv"
DEMAND = PROCESSED / "esios_demand_real_20250701_20260731_20260904T231550Z.csv"
P48 = PROCESSED / "esios_p48_generation_20250701_20260731_20260904T231550Z.csv"
IMBALANCE = PROCESSED / "esios_imbalance_20250701_20260731_20260904T231550Z.csv"

OUT_HOURLY = PROCESSED / "es_proxy_mechanism_hourly_20250701_20250930_evening.csv"
OUT_QH = PROCESSED / "es_proxy_mechanism_qh_20251001_20260731_evening.csv"
OUT_SUMMARY = PROCESSED / "es_proxy_mechanism_summary_20250701_20260731.json"

CROSSWALK_VERSION = "current_OMIE_LIST_20260904_CONDITIONAL"
P48_INTERVAL_HOURS = 0.25
P48_TECHNOLOGY = {
    71: "hydro_scheduled_mw",
    72: "hydro_scheduled_mw",
    73: "pumped_hydro_scheduled_mw",
    74: "nuclear_scheduled_mw",
    77: "coal_scheduled_mw",
    78: "coal_scheduled_mw",
    79: "ccgt_scheduled_mw",
    80: "other_thermal_scheduled_mw",
    81: "other_thermal_scheduled_mw",
    82: "wind_scheduled_mw",
    83: "wind_scheduled_mw",
    84: "solar_scheduled_mw",
    85: "solar_scheduled_mw",
    86: "other_renewable_scheduled_mw",
    87: "other_thermal_scheduled_mw",
    88: "other_thermal_scheduled_mw",
    90: "other_renewable_scheduled_mw",
    91: "other_renewable_scheduled_mw",
    92: "other_renewable_scheduled_mw",
    93: "other_renewable_scheduled_mw",
    94: "other_renewable_scheduled_mw",
}
IMBALANCE_COLUMNS = {763: "imbalance_up_eur_mwh", 764: "imbalance_down_eur_mwh"}


def _local_key(values: pd.Series) -> pd.Series:
    """Use local wall-clock time as the join key (target hours are unambiguous)."""

    return values.astype(str).str.slice(0, 19)


def _read_proxy(path: Path, resolution: str) -> pd.DataFrame:
    usecols = [
        "delivery_date",
        "local_datetime",
        "period_granularity",
        "price_eur_mwh",
        "price_regime",
        "proxy_status",
        "nm_total_mw",
        "nm_mapped_mw",
        "nm_unmapped_mw",
        "crosswalk_coverage",
        "market_rows_used",
        "crosswalk_version",
        "CCGT_NM_MW",
        "CCGT_NMShare_all",
        "Hydro_NM_MW",
        "Hydro_NMShare_all",
        "PumpedHydro_NM_MW",
        "PumpedHydro_NMShare_all",
        "Other_NM_MW",
        "Other_NMShare_all",
    ]
    frame = pd.read_csv(path, usecols=usecols)
    frame["local_key"] = _local_key(frame["local_datetime"])
    frame["resolution"] = resolution
    frame["price_eur_mwh"] = pd.to_numeric(frame["price_eur_mwh"], errors="coerce")
    frame["delivery_date"] = frame["delivery_date"].astype(str)
    frame["hour"] = pd.to_datetime(frame["local_key"], errors="coerce").dt.hour
    return frame[frame["hour"].between(19, 22)].copy()


def _read_esios(path: Path, usecols: list[str], indicator_filter: set[int] | None = None) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    for chunk in pd.read_csv(path, usecols=usecols, chunksize=200_000):
        if indicator_filter is not None and "indicator_id" in chunk:
            ids = pd.to_numeric(chunk["indicator_id"], errors="coerce")
            chunk = chunk[ids.isin(indicator_filter)]
        if chunk.empty:
            continue
        chunk["local_key"] = _local_key(chunk["datetime_local"])
        chunk["hour"] = pd.to_datetime(chunk["local_key"], errors="coerce").dt.hour
        chunk = chunk[chunk["hour"].between(19, 22)].copy()
        if not chunk.empty:
            chunk["value"] = pd.to_numeric(chunk["value"], errors="coerce")
            parts.append(chunk)
    if not parts:
        return pd.DataFrame(columns=[*usecols, "local_key", "hour"])
    return pd.concat(parts, ignore_index=True)


def _environment() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    demand = _read_esios(DEMAND, ["datetime_local", "value"])
    demand = demand.groupby("local_key", as_index=False)["value"].mean().rename(columns={"value": "load_mw"})

    p48 = _read_esios(P48, ["indicator_id", "datetime_local", "value"], set(P48_TECHNOLOGY))
    if not p48.empty:
        # eSIOS marks P48 as Energía at a 15-minute interval.  Preserve the
        # source meaning and convert MWh per interval to average MW before
        # summing technologies: MW = MWh / 0.25 h.
        p48["value"] = p48["value"] / P48_INTERVAL_HOURS
        p48["indicator_id"] = pd.to_numeric(p48["indicator_id"], errors="coerce").astype("Int64")
        p48["technology_column"] = p48["indicator_id"].map(P48_TECHNOLOGY)
        p48 = p48.dropna(subset=["technology_column"])
        p48_qh = p48.groupby(["local_key", "technology_column"], as_index=False)["value"].sum()
        p48_qh = p48_qh.pivot(index="local_key", columns="technology_column", values="value").reset_index()
        p48_qh.columns.name = None
    else:
        p48_qh = pd.DataFrame(columns=["local_key"])

    imbalance = _read_esios(IMBALANCE, ["indicator_id", "datetime_local", "value"], set(IMBALANCE_COLUMNS))
    if not imbalance.empty:
        imbalance["indicator_id"] = pd.to_numeric(imbalance["indicator_id"], errors="coerce").astype("Int64")
        imbalance["imbalance_column"] = imbalance["indicator_id"].map(IMBALANCE_COLUMNS)
        imbalance = imbalance.dropna(subset=["imbalance_column"])
        imbalance = imbalance.groupby(["local_key", "imbalance_column"], as_index=False)["value"].mean()
        imbalance = imbalance.pivot(index="local_key", columns="imbalance_column", values="value").reset_index()
        imbalance.columns.name = None
    else:
        imbalance = pd.DataFrame(columns=["local_key"])
    return demand, p48_qh, imbalance


def _join(proxy: pd.DataFrame, demand: pd.DataFrame, p48: pd.DataFrame, imbalance: pd.DataFrame) -> pd.DataFrame:
    merged = proxy.merge(demand, on="local_key", how="left")
    merged = merged.merge(p48, on="local_key", how="left")
    merged = merged.merge(imbalance, on="local_key", how="left")
    for col in [
        "wind_scheduled_mw",
        "solar_scheduled_mw",
        "ccgt_scheduled_mw",
        "hydro_scheduled_mw",
        "pumped_hydro_scheduled_mw",
    ]:
        if col not in merged:
            merged[col] = math.nan
    merged["residual_load_proxy_mw"] = merged["load_mw"] - merged["wind_scheduled_mw"] - merged["solar_scheduled_mw"]
    nm_cols = {
        "CCGT_NMShare_all": "CCGT",
        "Hydro_NMShare_all": "Hydro",
        "PumpedHydro_NMShare_all": "PumpedHydro",
        "Other_NMShare_all": "Other",
    }
    merged["dominant_proxy_technology"] = merged[list(nm_cols)].rename(columns=nm_cols).idxmax(axis=1)
    merged["analysis_status"] = "conditional_proxy_mechanism_analysis"
    merged["p48_source_unit"] = "MWh_per_15min"
    merged["p48_power_conversion"] = "value / 0.25 h -> average MW"
    return merged


def _hour_key(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    # The hourly proxy stores an explicit ``:00:00`` timestamp, while the
    # first 13 characters of the quarter-hour key stop at the hour.  Restore
    # the suffix so the environment join is exact.
    out["hour_key"] = out["local_key"].str.slice(0, 13) + ":00:00"
    return out


def _numeric_summary(frame: pd.DataFrame) -> dict[str, object]:
    numeric = [
        "price_eur_mwh",
        "CCGT_NMShare_all",
        "Hydro_NMShare_all",
        "PumpedHydro_NMShare_all",
        "Other_NMShare_all",
        "nm_total_mw",
        "crosswalk_coverage",
        "load_mw",
        "residual_load_proxy_mw",
        "ccgt_scheduled_mw",
        "hydro_scheduled_mw",
        "pumped_hydro_scheduled_mw",
        "wind_scheduled_mw",
        "solar_scheduled_mw",
        "imbalance_up_eur_mwh",
        "imbalance_down_eur_mwh",
    ]
    present = [col for col in numeric if col in frame]
    corr: dict[str, float | None] = {}
    for col in present:
        if col == "price_eur_mwh":
            continue
        pair = frame[["price_eur_mwh", col]].dropna()
        corr[col] = float(pair["price_eur_mwh"].corr(pair[col])) if len(pair) >= 3 else None
    means = {col: float(frame[col].mean()) if frame[col].notna().any() else None for col in present}
    monthly = frame.assign(month=frame["delivery_date"].str.slice(0, 7)).groupby("month", dropna=False)[present].mean(numeric_only=True).reset_index()
    monthly_records = []
    for row in monthly.to_dict(orient="records"):
        monthly_records.append({key: (None if pd.isna(value) else float(value) if isinstance(value, (int, float)) else value) for key, value in row.items()})
    dominant = frame.groupby("dominant_proxy_technology", dropna=False)[["price_eur_mwh", "load_mw", "residual_load_proxy_mw"]].mean(numeric_only=True).reset_index()
    dominant_records = []
    for row in dominant.to_dict(orient="records"):
        dominant_records.append({key: (None if pd.isna(value) else float(value) if isinstance(value, (int, float)) else value) for key, value in row.items()})
    return {
        "rows": int(len(frame)),
        "date_min": str(frame["delivery_date"].min()) if len(frame) else None,
        "date_max": str(frame["delivery_date"].max()) if len(frame) else None,
        "coverage": {col: int(frame[col].notna().sum()) for col in ["load_mw", "residual_load_proxy_mw", "ccgt_scheduled_mw", "imbalance_up_eur_mwh", "imbalance_down_eur_mwh"] if col in frame},
        "mean": means,
        "price_correlation": corr,
        "monthly_mean": monthly_records,
        "dominant_proxy_mean": dominant_records,
    }


def main() -> dict[str, object]:
    proxy_hourly = _read_proxy(PROXY_HOURLY, "hourly")
    proxy_qh = _read_proxy(PROXY_QH, "15min")
    demand, p48, imbalance = _environment()
    qh = _join(proxy_qh, demand, p48, imbalance)
    qh = qh[(qh["delivery_date"] >= "2025-10-01") & (qh["delivery_date"] <= "2026-07-31")].copy()

    # For the hourly segment, average the 15-minute environment inputs by local hour.
    env_qh = demand.merge(p48, on="local_key", how="outer").merge(imbalance, on="local_key", how="outer")
    env_qh = _hour_key(env_qh)
    env_hourly = env_qh.groupby("hour_key", as_index=False).mean(numeric_only=True)
    env_hourly = env_hourly.rename(columns={"hour_key": "local_key"})
    hourly = _join(proxy_hourly, env_hourly, pd.DataFrame(columns=["local_key"]), pd.DataFrame(columns=["local_key"]))
    hourly = hourly[(hourly["delivery_date"] >= "2025-07-01") & (hourly["delivery_date"] <= "2025-09-30")].copy()

    OUT_QH.parent.mkdir(parents=True, exist_ok=True)
    qh.to_csv(OUT_QH, index=False, encoding="utf-8")
    hourly.to_csv(OUT_HOURLY, index=False, encoding="utf-8")
    summary = {
        "status": "conditional_proxy_mechanism_analysis",
        "crosswalk_version": CROSSWALK_VERSION,
        "scope": "ex_post_descriptive_association_not_causal_and_not_official_setter",
        "proxy_hourly": _numeric_summary(hourly),
        "proxy_qh": _numeric_summary(qh),
        "source_notes": {
            "demand": "REE eSIOS indicator 1293, API fifteen_minutes average of native five-minute values",
            "generation": "REE eSIOS P48 scheduled generation; source magnitude Energía (MWh per 15-minute interval), converted to average MW by dividing by 0.25 h; not measured actual generation",
            "imbalance": "REE eSIOS indicators 763/764, EUR/MWh",
            "cross_border": "not included in this extension join because a continuous full-period P48 cross-border file was not available in the current processed inputs",
            "missing_proxy": "2026-06-08 through 2026-07-31 remain pending UOF release and are not interpolated",
        },
        "unit_conversion": {
            "p48_source_magnitude": "Energía",
            "p48_source_interval": "15 minutes",
            "p48_source_unit": "MWh per interval",
            "p48_output_unit": "average MW",
            "p48_conversion": "MWh / 0.25 h",
        },
    }
    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"hourly_rows": len(hourly), "qh_rows": len(qh), "summary": str(OUT_SUMMARY)}


if __name__ == "__main__":
    print(main())
