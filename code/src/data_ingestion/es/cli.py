"""Command line interface for ES-DATA-01.

Examples (run from repository root)::

    python -m src.data_ingestion.es.cli omie --start 2026-08-01 --end 2026-08-31
    python -m src.data_ingestion.es.cli redata --start 2026-08-01T00:00 --end 2026-08-01T23:59
    python -m src.data_ingestion.es.cli esios metadata 682
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from .common import json_dump, retrieval_batch_id
from .omie import download_omie, normalize_omie_directory, parse_omie, standardize_omie_rows, write_standardized_csv
from .ree import CredentialError, ESIOSClient, REDataClient
from .entsoe import SPAIN_EIC, download_entsoe, parse_entsoe_xml
from .quality import summarize_omie_downloads, summarize_rows, write_quality_report


def _dates(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="es-data")
    sub = parser.add_subparsers(dest="command", required=True)
    omie = sub.add_parser("omie", help="download and parse OMIE files")
    omie.add_argument("--start", required=True); omie.add_argument("--end", required=True)
    omie.add_argument("--kind", choices=["da", "ida1", "ida2", "ida3", "idc", "all"], default="all")
    omie.add_argument("--raw-root", default="data/raw/ES"); omie.add_argument("--processed-root", default="data/processed/ES"); omie.add_argument("--quality-output", help="optional quality report path"); omie.add_argument("--skip-download", action="store_true", help="normalize already downloaded immutable responses")
    redata = sub.add_parser("redata", help="fetch no-token REData JSON")
    redata.add_argument("--start", required=True); redata.add_argument("--end", required=True); redata.add_argument("--raw-root", default="data/raw/ES"); redata.add_argument("--processed-root", default="data/processed/ES"); redata.add_argument("--time-trunc", default="hour", choices=["hour", "day", "month", "year"])
    entsoe = sub.add_parser("entsoe", help="fetch ENTSO-E A75 actual generation")
    entsoe.add_argument("--start", required=True); entsoe.add_argument("--end", required=True); entsoe.add_argument("--domain", default=SPAIN_EIC); entsoe.add_argument("--resolution"); entsoe.add_argument("--psr-type"); entsoe.add_argument("--raw-root", default="data/raw/ES"); entsoe.add_argument("--processed-root", default="data/processed/ES")
    esios = sub.add_parser("esios", help="authenticated eSIOS metadata/fetch/discovery")
    esios.add_argument("action", choices=["metadata", "fetch", "discover"]); esios.add_argument("value", nargs="?"); esios.add_argument("--start"); esios.add_argument("--end"); esios.add_argument("--time-trunc", default=None); esios.add_argument("--time-agg", default=None); esios.add_argument("--raw-root", default="data/raw/ES")
    args = parser.parse_args(argv)
    if args.command == "omie":
        start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)
        kinds = ["da", "ida1", "ida2", "ida3", "idc"] if args.kind == "all" else [args.kind]
        batch = retrieval_batch_id(); all_rows = []
        if args.skip_download:
            all_rows = normalize_omie_directory(args.raw_root, start, end, kinds)
        else:
            for current in _dates(start, end):
                for kind in kinds:
                    record = download_omie(kind, current, args.raw_root, batch)
                    if record["status"] not in {"success", "empty_business_file", "already_exists"}:
                        continue
                    path = Path(record["path"])
                    try:
                        rows = standardize_omie_rows(parse_omie(path, kind, current.isoformat()), current.isoformat())
                        all_rows.extend(rows)
                    except ValueError as exc:
                        record["parse_error"] = str(exc)
        out = Path(args.processed_root) / f"omie_spot_{start:%Y%m%d}_{end:%Y%m%d}.csv"
        write_standardized_csv(all_rows, out)
        quality_path = Path(args.quality_output) if args.quality_output else Path(args.processed_root) / f"omie_quality_{start:%Y%m%d}_{end:%Y%m%d}.md"
        write_quality_report(quality_path, {"records": summarize_rows(all_rows), "download": summarize_omie_downloads(args.raw_root, start.isoformat(), end.isoformat(), kinds) | {"batch": batch}, "granularity_by_kind": {kind: {"rows": sum(1 for row in all_rows if row.get("kind") == kind), "period_min": min((int(row["period"]) for row in all_rows if row.get("kind") == kind and row.get("period") is not None), default=None), "period_max": max((int(row["period"]) for row in all_rows if row.get("kind") == kind and row.get("period") is not None), default=None), "null_price": sum(row.get("price_es_eur_mwh") is None for row in all_rows if row.get("kind") == kind), "null_utc": sum(row.get("utc_time") in (None, "") for row in all_rows if row.get("kind") == kind)} for kind in kinds}})
        print(json.dumps({"batch": batch, "records": len(all_rows), "output": str(out)}, ensure_ascii=False)); return 0
    if args.command == "redata":
        client = REDataClient(); response, payload = client.fetch(start_date=args.start, end_date=args.end, time_trunc=args.time_trunc)
        batch = retrieval_batch_id(); period = args.start[:7]
        path = Path(args.raw_root) / "redata" / period / batch / "generacion_estructura-generacion.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists(): path.write_bytes(response.body)
        meta = {"source": "redata", "url": client.build_url("generacion", "estructura-generacion", args.start, args.end, args.time_trunc), "http_status": response.status, "bytes": len(response.body), "batch": batch, "retrieved_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()}
        json_dump(path.with_suffix(".meta.json"), meta)
        if response.status >= 400 or payload is None:
            print(json.dumps({"status": "failed", "http_status": response.status, "records": 0, "path": str(path)})); return 1
        records = client.records(payload)
        standardized = client.standardize_rows(records, args.start[:7], args.time_trunc, derive_average_mw=False)
        processed = Path(args.processed_root) / f"redata_{args.start[:10]}_{args.end[:10]}_{args.time_trunc}.csv"
        write_standardized_csv(standardized, processed)
        print(json.dumps({"batch": batch, "http_status": response.status, "records": len(records), "path": str(path), "processed": str(processed)})); return 0 if response.status < 400 else 1
    if args.command == "entsoe":
        try:
            record = download_entsoe(args.start, args.end, raw_root=args.raw_root, domain=args.domain, resolution=args.resolution, psr_type=args.psr_type)
        except CredentialError as exc:
            print(json.dumps({"status": "skipped", "reason": str(exc)}, ensure_ascii=False)); return 2
        rows = []
        if record["status"] in {"success", "already_exists"}:
            try: rows = parse_entsoe_xml(Path(record["path"]))
            except (ValueError, OSError): rows = []
        processed = None
        if record["status"] in {"success", "already_exists"}:
            processed = Path(args.processed_root) / f"entsoe_a75_{args.start[:10]}_{args.end[:10]}.csv"
            write_standardized_csv(rows, processed)
        print(json.dumps({"status": record["status"], "http_status": record["http_status"], "records": len(rows), "path": record["path"], "processed": str(processed) if processed else None}, ensure_ascii=False)); return 0 if record["status"] in {"success", "already_exists", "empty_business_file"} else 1
    client = ESIOSClient()
    if not args.value:
        print(json.dumps({"status": "failed", "reason": "an indicator ID or discovery text is required"}, ensure_ascii=False)); return 2
    if args.action == "fetch" and (not args.start or not args.end):
        print(json.dumps({"status": "failed", "reason": "--start and --end are required for fetch"}, ensure_ascii=False)); return 2
    try:
        if args.action == "discover":
            response, payload = client.search_indicators(args.value)
            request_url = f"{client.base_url}/indicators?{urllib.parse.urlencode({'text': args.value, 'locale': 'es'})}"
            request_params = {"text": args.value, "locale": "es"}
        elif args.action == "metadata":
            response, payload = client.metadata(args.value)
            request_url = client.build_indicator_url(args.value)
            request_params = {"locale": "es"}
        else:
            response, payload = client.fetch_indicator(args.value, start_date=args.start, end_date=args.end, time_trunc=args.time_trunc, time_agg=args.time_agg)
            request_url = client.build_indicator_url(args.value, start_date=args.start, end_date=args.end, time_trunc=args.time_trunc, time_agg=args.time_agg)
            request_params = {k: v for k, v in {"start_date": args.start, "end_date": args.end, "time_trunc": args.time_trunc, "time_agg": args.time_agg}.items() if v is not None}
    except CredentialError as exc:
        print(json.dumps({"status": "skipped", "reason": str(exc)}, ensure_ascii=False)); return 2
    period = (args.start[:7] if args.start else datetime.now(timezone.utc).strftime("%Y-%m"))
    batch = retrieval_batch_id()
    safe_value = re.sub(r"[^A-Za-z0-9_.-]+", "_", args.value)[:120]
    path = Path(args.raw_root) / "esios" / period / batch / f"{args.action}_{safe_value}.json"
    meta = client.save_response(response, path, request_url, request_params)
    parsed = payload is not None
    record_count = 0
    if isinstance(payload, dict):
        for key in ("values", "data", "indicators", "archives"):
            value = payload.get(key)
            if isinstance(value, list): record_count += len(value)
    status = "success" if response.status < 400 and parsed else ("failed_json" if response.status < 400 else "failed")
    print(json.dumps({"status": status, "http_status": response.status, "records": record_count, "path": str(path), "sha256": meta["sha256"]}, ensure_ascii=False)); return 0 if status == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
