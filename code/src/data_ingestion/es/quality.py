"""Quality summaries shared by CLI outputs and offline validation."""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


def summarize_rows(rows: Iterable[dict[str, Any]], timestamp_fields: tuple[str, ...] = ("utc_time", "datetime_utc", "timestamp_utc", "datetime", "timestamp", "local_time")) -> dict[str, Any]:
    data = list(rows)
    timestamps: list[str] = []
    for row in data:
        for key in timestamp_fields:
            value = row.get(key)
            if value:
                timestamps.append(str(value)); break
    # Keys are dataset-specific.  A period shared by DA and IDC is not a
    # duplicate, and technologies may legitimately share a timestamp.
    omie_keys = [(
        row.get("source"), row.get("kind"), row.get("delivery_date"), row.get("period")
    ) for row in data if row.get("kind") and row.get("delivery_date") and row.get("period") is not None]
    redata_keys = [(
        row.get("technology"), row.get("datetime_utc") or row.get("source_datetime")
    ) for row in data if row.get("technology") and (row.get("datetime_utc") or row.get("source_datetime"))]
    generic_keys = [(row.get("datetime_utc") or row.get("timestamp") or row.get("local_time_naive"),) for row in data if not row.get("kind") and not row.get("technology") and (row.get("datetime_utc") or row.get("timestamp") or row.get("local_time_naive"))]
    dup_count = sum(len(keys) - len(set(keys)) for keys in (omie_keys, redata_keys, generic_keys))
    missing = {}
    if data:
        for key in data[0]:
            missing[key] = sum(row.get(key) in (None, "") for row in data)
    return {"records": len(data), "first_timestamp": min(timestamps) if timestamps else None, "last_timestamp": max(timestamps) if timestamps else None, "duplicate_count": dup_count, "missing_by_field": missing}


def write_quality_report(path: str | Path, sections: dict[str, Any], title: str = "ES data download quality") -> None:
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# {title}", "", f"Generated at: {datetime.now().astimezone().isoformat()}", "", "This report separates source facts from checks and unresolved questions.", ""]
    for name, value in sections.items():
        lines.extend([f"## {name}", ""])
        if isinstance(value, dict):
            for key, item in value.items():
                lines.append(f"- **{key}**: {item}")
        elif isinstance(value, list):
            lines.extend(f"- {item}" for item in value)
        else:
            lines.append(str(value))
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def summarize_omie_downloads(raw_root: str | Path, start: str, end: str, kinds: list[str]) -> dict[str, Any]:
    """Summarize the newest immutable manifest record per product/day."""
    from datetime import date, timedelta
    begin, finish = date.fromisoformat(start), date.fromisoformat(end)
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for manifest in (Path(raw_root) / "omie").rglob("manifest.json") if (Path(raw_root) / "omie").exists() else []:
        try:
            records = json.loads(manifest.read_text(encoding="utf-8")).get("records", [])
        except (ValueError, OSError):
            continue
        for record in records:
            try: delivery = date.fromisoformat(str(record.get("delivery_date")))
            except (TypeError, ValueError): continue
            kind = str(record.get("kind"))
            if kind not in kinds or delivery < begin or delivery > finish: continue
            key = (kind, delivery.isoformat())
            old = latest.get(key)
            if old is None or str(record.get("retrieved_at", "")) >= str(old.get("retrieved_at", "")):
                latest[key] = record
    expected_days = (finish - begin).days + 1
    result: dict[str, Any] = {"requested": expected_days * len(kinds), "by_kind": {}, "latest_records": len(latest)}
    for kind in kinds:
        records = [latest[(kind, d)] for d in ((begin + timedelta(days=i)).isoformat() for i in range(expected_days)) if (kind, d) in latest]
        counts = {"requested": expected_days, "success": 0, "empty_business_file": 0, "failed": 0, "failed_html_response": 0, "already_exists": 0, "bytes": 0}
        for record in records:
            status = str(record.get("status", "failed")); counts[status] = counts.get(status, 0) + 1; counts["bytes"] += int(record.get("bytes") or 0)
        result["by_kind"][kind] = counts
    return result
