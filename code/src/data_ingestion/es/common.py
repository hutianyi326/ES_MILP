"""Small dependency-free helpers used by the ES data collectors."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def retrieval_batch_id(now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    return now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def safe_write_bytes(path: Path, data: bytes) -> bool:
    """Write only when *path* does not exist; return whether a file was made."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return False
    # exclusive creation is important if two collectors run concurrently.
    with path.open("xb") as handle:
        handle.write(data)
    return True


def parse_number(value: str | None) -> float | None:
    if value is None:
        return None
    text = value.strip().replace("\xa0", "")
    if not text or text in {"-", "--", "NA", "N/A"}:
        return None
    # OMIE uses decimal point in current files; accept comma for old exports.
    text = text.replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def is_html(data: bytes) -> bool:
    head = data[:2048].lstrip().lower()
    return head.startswith((b"<!doctype html", b"<html", b"<head", b"<body")) or b"<html" in head


def redact_headers(headers: dict[str, str]) -> dict[str, str]:
    result = {}
    for key, value in headers.items():
        result[key] = "<redacted>" if key.lower() in {"x-api-key", "authorization", "cookie"} else value
    return result


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_iso_datetime(value: str, default_tz: str = "Europe/Madrid") -> tuple[str | None, str | None]:
    """Return (UTC ISO, offset) without requiring zoneinfo for basic offsets.

    Zoneinfo is used by callers when the source timestamp has no offset.  A
    source offset is never discarded, which is essential around DST folds.
    """
    text = value.strip()
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None, None
    if dt.tzinfo is None:
        return None, None
    offset = dt.strftime("%z")
    offset = offset[:3] + ":" + offset[3:] if len(offset) == 5 else offset
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"), offset


def flatten_values(value: Any) -> Iterable[dict[str, Any]]:
    """Yield value dictionaries from common JSON:API/eSIOS shapes."""
    if isinstance(value, dict):
        if isinstance(value.get("values"), list):
            for item in value["values"]:
                if isinstance(item, dict):
                    yield item
        for key in ("data", "included", "indicator"):
            child = value.get(key)
            if isinstance(child, list):
                for item in child:
                    yield from flatten_values(item)
            elif isinstance(child, dict):
                yield from flatten_values(child)
    elif isinstance(value, list):
        for item in value:
            yield from flatten_values(item)
