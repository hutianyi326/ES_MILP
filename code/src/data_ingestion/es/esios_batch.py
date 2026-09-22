"""Batch downloader and long-form normalizer for authenticated REE eSIOS data.

The batch job deliberately keeps the API key in memory only.  Raw responses are
stored without request headers, while processed CSVs retain the source period,
local/UTC timestamps, geo, magnitude and update metadata needed for audit.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import time as sleep_time
from calendar import monthrange
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, time
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .common import retrieval_batch_id
from .ree import ESIOSClient, HTTPResponse


INDICATORS: dict[str, tuple[str, ...]] = {
    "demand_real": ("1293",),
    "afrr": ("630", "631", "632", "633", "634", "2130", "680", "681", "682", "683"),
    "imbalance": ("763", "764"),
    "p48_generation": tuple(str(i) for i in range(71, 95)),
}

INDICATOR_TO_DATASET = {indicator_id: dataset for dataset, ids in INDICATORS.items() for indicator_id in ids}

CSV_FIELDS = [
    "indicator_id",
    "indicator_name",
    "dataset",
    "magnitud",
    "step_type",
    "time_name",
    "geo_id",
    "geo_name",
    "value",
    "datetime_local",
    "datetime_utc",
    "tz_time",
    "values_updated_at",
    "source_period",
    "request_start",
    "request_end",
    "time_trunc",
    "time_agg",
    "raw_path",
    "raw_sha256",
]


def read_ree_key(path: str | Path) -> str:
    """Read only the value immediately following the ``## REE APIKey`` heading."""

    lines = Path(path).read_text(encoding="utf-8").splitlines()
    heading = re.compile(r"^\s*##\s*REE\s*API\s*Key\s*$", re.IGNORECASE)
    index = next((i for i, line in enumerate(lines) if heading.match(line)), -1)
    if index < 0:
        raise ValueError("REE API key heading not found")
    candidate = ""
    for line in lines[index + 1 :]:
        text = line.strip()
        if not text or re.match(r"^#+\s*key\s*:", text, re.IGNORECASE):
            continue
        candidate = text.strip("`\"'")
        break
    candidate = re.sub(r"^Bearer\s+", "", candidate, flags=re.IGNORECASE).strip()
    if not candidate:
        raise ValueError("REE API key value is empty")
    return candidate


def month_windows(start: date, end: date, tz_name: str = "Europe/Madrid") -> list[tuple[str, str, str]]:
    """Return (period, ISO start, ISO end) windows with local DST offsets."""

    tz = ZoneInfo(tz_name)
    current = date(start.year, start.month, 1)
    windows: list[tuple[str, str, str]] = []
    while current <= end:
        month_end = date(current.year, current.month, monthrange(current.year, current.month)[1])
        left = max(start, current)
        right = min(end, month_end)
        if left <= right:
            start_dt = datetime.combine(left, time.min, tzinfo=tz)
            end_dt = datetime.combine(right, time(23, 59, 59), tzinfo=tz)
            windows.append((current.strftime("%Y-%m"), start_dt.isoformat(), end_dt.isoformat()))
        current = date(current.year + (current.month == 12), 1 if current.month == 12 else current.month + 1, 1)
    return windows


def _names(value: Any) -> str:
    if isinstance(value, list):
        return "|".join(str(item.get("name", "")) if isinstance(item, dict) else str(item) for item in value)
    if isinstance(value, dict):
        return str(value.get("name", ""))
    return str(value or "")


def _extract_rows(payload: dict[str, Any] | None, dataset: str, source_period: str, request_start: str, request_end: str, time_agg: str | None, raw_path: str, raw_sha256: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    indicator = payload.get("indicator") if isinstance(payload, dict) else None
    if not isinstance(indicator, dict):
        return [], {"indicator_id": None, "indicator_name": None, "values": 0, "reason": "missing_indicator"}
    indicator_id = str(indicator.get("id", ""))
    name = str(indicator.get("name", ""))
    magnitude = _names(indicator.get("magnitud"))
    time_name = _names(indicator.get("tiempo"))
    rows: list[dict[str, Any]] = []
    values = indicator.get("values") if isinstance(indicator.get("values"), list) else []
    for point in values:
        if not isinstance(point, dict):
            continue
        rows.append({
            "indicator_id": indicator_id,
            "indicator_name": name,
            "dataset": dataset,
            "magnitud": magnitude,
            "step_type": indicator.get("step_type", ""),
            "time_name": time_name,
            "geo_id": point.get("geo_id", ""),
            "geo_name": point.get("geo_name", ""),
            "value": point.get("value", ""),
            "datetime_local": point.get("datetime", ""),
            "datetime_utc": point.get("datetime_utc", ""),
            "tz_time": point.get("tz_time", ""),
            "values_updated_at": indicator.get("values_updated_at", ""),
            "source_period": source_period,
            "request_start": request_start,
            "request_end": request_end,
            "time_trunc": "fifteen_minutes",
            "time_agg": time_agg or "",
            "raw_path": raw_path,
            "raw_sha256": raw_sha256,
        })
    return rows, {"indicator_id": indicator_id, "indicator_name": name, "values": len(rows), "magnitud": magnitude, "time_name": time_name}


def run_batch(api_key_file: str | Path, start: date, end: date, raw_root: str | Path = "data/raw/ES", processed_root: str | Path = "data/processed/ES", tz_name: str = "Europe/Madrid", pause_seconds: float = 0.0, workers: int = 4) -> dict[str, Any]:
    key = read_ree_key(api_key_file)
    batch = retrieval_batch_id()
    raw_root_path = Path(raw_root)
    processed_root_path = Path(processed_root)
    windows = month_windows(start, end, tz_name)
    stats: list[dict[str, Any]] = []
    output_paths = {dataset: processed_root_path / f"esios_{dataset}_{start:%Y%m%d}_{end:%Y%m%d}_{batch}.csv" for dataset in INDICATORS}
    writers: dict[str, tuple[Any, csv.DictWriter]] = {}
    jobs = [(period, dataset, indicator_id, request_start, request_end, "average" if indicator_id == "1293" else None) for period, request_start, request_end in windows for dataset, ids in INDICATORS.items() for indicator_id in ids]

    def fetch_job(job: tuple[str, str, str, str, str, str | None]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        period, dataset, indicator_id, request_start, request_end, time_agg = job
        client = ESIOSClient(api_key=key, timeout=90.0)
        params = {"start_date": request_start, "end_date": request_end, "time_trunc": "fifteen_minutes"}
        if time_agg:
            params["time_agg"] = time_agg
        url = client.build_indicator_url(indicator_id, **params)
        response: HTTPResponse | None = None
        last_status: int | None = None
        payload: dict[str, Any] | None = None
        error = ""
        for attempt in range(3):
            try:
                response, payload = client.fetch_indicator(indicator_id, **params)
                last_status = response.status
                if response.status not in {429, 500, 502, 503, 504}:
                    break
                sleep_time.sleep(2 ** attempt)
            except Exception as exc:  # pragma: no cover - network dependent
                error = f"{type(exc).__name__}: {exc}"
                sleep_time.sleep(2 ** attempt)
        raw_path = raw_root_path / "esios" / period / batch / f"fetch_{indicator_id}.json"
        if response is None:
            response = HTTPResponse(last_status or 0, {}, b"")
        meta = client.save_response(response, raw_path, url, params)
        rows, parsed_stats = _extract_rows(payload if last_status and last_status < 400 else None, dataset, period, request_start, request_end, time_agg, str(raw_path), str(meta.get("sha256", "")))
        result = {"period": period, "dataset": dataset, "indicator_id": indicator_id, "http_status": last_status or 0, "values": len(rows), "raw_path": str(raw_path), "raw_sha256": meta.get("sha256"), "error": error, "indicator_name": parsed_stats.get("indicator_name")}
        if pause_seconds:
            sleep_time.sleep(pause_seconds)
        return result, rows

    try:
        with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
            futures = [executor.submit(fetch_job, job) for job in jobs]
            total = len(futures)
            for completed, future in enumerate(as_completed(futures), 1):
                result, rows = future.result()
                stats.append(result)
                if rows:
                    handle_writer = writers.get(result["dataset"])
                    if handle_writer is None:
                        output_paths[result["dataset"]].parent.mkdir(parents=True, exist_ok=True)
                        handle = output_paths[result["dataset"]].open("w", encoding="utf-8", newline="")
                        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
                        writer.writeheader()
                        writers[result["dataset"]] = (handle, writer)
                    writers[result["dataset"]][1].writerows(rows)
                if completed == 1 or completed % 10 == 0 or completed == total:
                    print(json.dumps({"progress": completed, "total": total, "period": result["period"], "dataset": result["dataset"], "indicator_id": result["indicator_id"], "http_status": result["http_status"], "values": result["values"]}, ensure_ascii=False), flush=True)
    finally:
        for handle, _writer in writers.values():
            handle.close()

    quality = {
        "retrieved_at": datetime.now().astimezone().isoformat(),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "timezone": tz_name,
        "batch": batch,
        "request_count": len(stats),
        "http_status_counts": {str(status): sum(item["http_status"] == status for item in stats) for status in sorted({item["http_status"] for item in stats})},
        "rows_by_dataset": {dataset: sum(item["values"] for item in stats if item["dataset"] == dataset) for dataset in INDICATORS},
        "zero_value_requests": [item for item in stats if item["values"] == 0],
        "outputs": {dataset: str(path) for dataset, path in output_paths.items() if path.exists()},
    }
    quality_path = processed_root_path / f"esios_quality_{start:%Y%m%d}_{end:%Y%m%d}_{batch}.json"
    quality_path.parent.mkdir(parents=True, exist_ok=True)
    quality_path.write_text(json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8")
    return quality


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="esios-batch")
    parser.add_argument("--api-key-file", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--raw-root", default="data/raw/ES")
    parser.add_argument("--processed-root", default="data/processed/ES")
    parser.add_argument("--timezone", default="Europe/Madrid")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args(argv)
    quality = run_batch(Path(args.api_key_file), date.fromisoformat(args.start), date.fromisoformat(args.end), args.raw_root, args.processed_root, args.timezone, workers=args.workers)
    print(json.dumps({"status": "success", "batch": quality["batch"], "request_count": quality["request_count"], "rows_by_dataset": quality["rows_by_dataset"], "quality": str(Path(args.processed_root) / f"esios_quality_{args.start.replace('-', '')}_{args.end.replace('-', '')}_{quality['batch']}.json")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
