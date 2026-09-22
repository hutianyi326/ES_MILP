"""Fetch the eSIOS inputs needed for the conditional Spain spot merge.

The key is read into memory from the user-authorized key file and is never
written to a raw response, manifest, quality report or processed CSV.
"""

from __future__ import annotations

import argparse
import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

from .common import retrieval_batch_id
from .esios_batch import CSV_FIELDS, _extract_rows, month_windows, read_ree_key
from .ree import ESIOSClient


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def run(api_key_file: str | Path, start: date, end: date, raw_root: str | Path = "data/raw/ES", processed_root: str | Path = "data/processed/ES", workers: int = 3) -> dict[str, object]:
    api_key = read_ree_key(api_key_file)
    batch = retrieval_batch_id()
    raw_root = Path(raw_root)
    processed_root = Path(processed_root)
    jobs = []
    for period, request_start, request_end in month_windows(start, end):
        jobs.extend((period, dataset, indicator_id, request_start, request_end, time_agg) for dataset, indicator_id, time_agg in (
            ("demand_real", "1293", "average"),
            ("imbalance", "763", None),
            ("imbalance", "764", None),
        ))

    def fetch(job):
        period, dataset, indicator_id, request_start, request_end, time_agg = job
        client = ESIOSClient(api_key=api_key, timeout=90.0)
        params = {"start_date": request_start, "end_date": request_end, "time_trunc": "fifteen_minutes"}
        if time_agg:
            params["time_agg"] = time_agg
        url = client.build_indicator_url(indicator_id, **params)
        response, payload = client.fetch_indicator(indicator_id, **params)
        raw_path = raw_root / "esios" / period / batch / f"fetch_{indicator_id}.json"
        meta = client.save_response(response, raw_path, url, params)
        rows, parsed = _extract_rows(payload if response.status < 400 else None, dataset, period, request_start, request_end, time_agg, str(raw_path), str(meta.get("sha256", "")))
        return {
            "period": period,
            "dataset": dataset,
            "indicator_id": indicator_id,
            "http_status": response.status,
            "values": len(rows),
            "raw_path": str(raw_path),
            "raw_sha256": meta.get("sha256", ""),
            "indicator_name": parsed.get("indicator_name"),
            "rows": rows,
        }

    results = []
    rows_by_dataset: dict[str, list[dict[str, object]]] = {"demand_real": [], "imbalance": []}
    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        futures = [executor.submit(fetch, job) for job in jobs]
        for future in as_completed(futures):
            result = future.result()
            rows = result.pop("rows")
            results.append(result)
            rows_by_dataset[result["dataset"]].extend(rows)

    for dataset, rows in rows_by_dataset.items():
        rows.sort(key=lambda row: (str(row.get("datetime_utc", "")), str(row.get("indicator_id", ""))))
        if rows:
            _write_rows(processed_root / f"esios_{dataset}_{start:%Y%m%d}_{end:%Y%m%d}_{batch}.csv", rows)

    quality = {
        "retrieved_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "timezone": "Europe/Madrid",
        "batch": batch,
        "request_count": len(results),
        "http_status_counts": {str(status): sum(item["http_status"] == status for item in results) for status in sorted({item["http_status"] for item in results})},
        "rows_by_dataset": {dataset: len(rows) for dataset, rows in rows_by_dataset.items()},
        "requests": sorted(results, key=lambda item: (item["period"], item["dataset"], item["indicator_id"])),
    }
    quality_path = processed_root / f"esios_quality_{start:%Y%m%d}_{end:%Y%m%d}_{batch}.json"
    quality_path.parent.mkdir(parents=True, exist_ok=True)
    quality_path.write_text(json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8")
    return quality


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="esios-targeted-fetch")
    parser.add_argument("--api-key-file", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--raw-root", default="data/raw/ES")
    parser.add_argument("--processed-root", default="data/processed/ES")
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args(argv)
    quality = run(Path(args.api_key_file), date.fromisoformat(args.start), date.fromisoformat(args.end), args.raw_root, args.processed_root, args.workers)
    print(json.dumps({key: value for key, value in quality.items() if key != "requests"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
