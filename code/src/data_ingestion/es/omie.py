"""OMIE file URLs, immutable downloads, and tolerant fixed-width parsers."""

from __future__ import annotations

import csv
import io
import re
import urllib.parse
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from .common import is_html, iso_now, json_dump, parse_number, retrieval_batch_id, safe_write_bytes, sha256_bytes

OMIE_KIND_CONFIG = {
    "da": {"prefix": "marginalpdbc", "parents": "marginalpdbc", "dataset": "OMIE_DA_PRICE_ES", "lang": "en"},
    "ida1": {"prefix": "marginalpibc", "parents": "marginalpibc", "dataset": "OMIE_IDA1_PRICE_ES", "lang": "es", "session": "01"},
    "ida2": {"prefix": "marginalpibc", "parents": "marginalpibc", "dataset": "OMIE_IDA2_PRICE_ES", "lang": "es", "session": "02"},
    "ida3": {"prefix": "marginalpibc", "parents": "marginalpibc", "dataset": "OMIE_IDA3_PRICE_ES", "lang": "es", "session": "03"},
    "idc": {"prefix": "precios_pibcic", "parents": "precios_pibcic", "dataset": "OMIE_IDC_STATS_ES", "lang": "en"},
}


def _as_date(value: date | str) -> date:
    return value if isinstance(value, date) else date.fromisoformat(value)


def omie_filename(kind: str, delivery_date: date | str) -> str:
    if kind not in OMIE_KIND_CONFIG:
        raise ValueError(f"unsupported OMIE kind: {kind}")
    config = OMIE_KIND_CONFIG[kind]
    suffix = config.get("session", "")
    return f"{config['prefix']}_{_as_date(delivery_date):%Y%m%d}{suffix}.1"


def build_omie_url(kind: str, delivery_date: date | str, lang: str | None = None) -> str:
    config = OMIE_KIND_CONFIG.get(kind)
    if config is None:
        raise ValueError(f"unsupported OMIE kind: {kind}")
    filename = omie_filename(kind, delivery_date)
    language = lang or config["lang"]
    query = urllib.parse.urlencode({"filename": filename, "parents": config["parents"]})
    return f"https://www.omie.es/{language}/file-download?{query}"


def _request(url: str, timeout: float = 60.0, opener: Callable[..., Any] | None = None) -> tuple[int, dict[str, str], bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": "ES-DATA-01/1.0", "Accept": "*/*"})
    opener = opener or urllib.request.urlopen
    try:
        with opener(request, timeout=timeout) as response:
            return int(getattr(response, "status", response.getcode())), dict(response.headers), response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers or {}), exc.read()


def download_omie(kind: str, delivery_date: date | str, raw_root: str | Path = "data/raw/ES", retrieval_batch: str | None = None, opener: Callable[..., Any] | None = None) -> dict[str, Any]:
    """Download one file into ``source/period/batch`` and append a manifest.

    Existing files are never overwritten.  HTTP 200 HTML responses and the
    known 18-byte no-trade files are represented in the manifest rather than
    incorrectly treated as successful parsed datasets.
    """
    d = _as_date(delivery_date)
    batch = retrieval_batch or retrieval_batch_id()
    config = OMIE_KIND_CONFIG[kind]
    url = build_omie_url(kind, d)
    status, headers, body = _request(url, opener=opener)
    filename = omie_filename(kind, d)
    target = Path(raw_root) / "omie" / d.strftime("%Y-%m") / batch / filename
    record: dict[str, Any] = {"source": "omie", "dataset": config["dataset"], "kind": kind, "period": d.strftime("%Y-%m"), "delivery_date": d.isoformat(), "url": url, "retrieved_at": iso_now(), "http_status": status, "bytes": len(body), "sha256": sha256_bytes(body), "filename": filename, "path": str(target), "headers": {k: v for k, v in headers.items() if k.lower() not in {"set-cookie"}}, "status": "failed"}
    if status == 200 and body and not is_html(body):
        if safe_write_bytes(target, body):
            record["status"] = "empty_business_file" if _looks_empty_business(body) else "success"
        else:
            record["status"] = "already_exists"
    elif status == 200 and is_html(body):
        record["status"] = "failed_html_response"
    else:
        record["status"] = "failed"
    manifest = target.parent / "manifest.json"
    previous: list[dict[str, Any]] = []
    if manifest.exists():
        import json
        try:
            previous = json.loads(manifest.read_text(encoding="utf-8")).get("records", [])
        except (ValueError, OSError):
            previous = []
    previous.append(record)
    json_dump(manifest, {"schema": "ES-DATA-01/manifest-v1", "source": "omie", "retrieval_batch": batch, "records": previous})
    return record


def _looks_empty_business(body: bytes) -> bool:
    text = body.decode("latin-1", errors="replace")
    rows = [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith(("#", "//"))]
    return len(rows) <= 2 and len(body) <= 256


def _clean_line(line: str) -> str:
    return line.strip("\ufeff\r\n")


def _split(line: str) -> list[str]:
    # Current OMIE exports are fixed-width but releases also contain `;` and
    # whitespace variants.  Keep the original row and parse both safely.
    if ";" in line:
        return [x.strip() for x in line.split(";")]
    if "\t" in line:
        return [x.strip() for x in line.split("\t")]
    return re.split(r"\s+", line.strip())


def _header_map(lines: list[str]) -> dict[str, int]:
    for line in lines[:80]:
        parts = _split(line)
        lowered = [p.lower().replace(" ", "") for p in parts]
        if any("marginales" in x or "marginales" in x for x in lowered) or any("medioes" in x for x in lowered):
            return {p.lower().replace(" ", ""): i for i, p in enumerate(parts)}
    return {}


def parse_omie(source: bytes | str | Path, kind: str, delivery_date: str | None = None) -> list[dict[str, Any]]:
    """Parse an OMIE price file while preserving each raw line.

    Header labels are preferred.  Positional fallback follows the official
    common layout: year/month/day/period then Spanish and Portuguese price.
    No expected row count is imposed (DST and empty sessions are valid).
    """
    if isinstance(source, bytes):
        body = source
    else:
        body = Path(source).read_bytes()
    if is_html(body):
        raise ValueError("HTML response is not an OMIE business file")
    text = body.decode("latin-1", errors="replace")
    lines = [_clean_line(x) for x in text.splitlines()]
    labels = _header_map(lines)
    output: list[dict[str, Any]] = []
    for raw in lines:
        if not raw.strip() or raw.lstrip().startswith(("#", "//", "Fecha", "DATE", "MARGINAL", "PERIOD")):
            continue
        parts = _split(raw)
        if len(parts) < 4 or not any(ch.isdigit() for ch in parts[0]):
            continue
        # Skip metadata dates and separator lines by requiring a numeric period
        period_idx = labels.get("period", labels.get("periodo", 3))
        if period_idx >= len(parts) or parse_number(parts[period_idx]) is None:
            continue
        def get(*names: str, fallback: int | None = None) -> str | None:
            for name in names:
                idx = labels.get(name)
                if idx is not None and idx < len(parts):
                    return parts[idx]
            return parts[fallback] if fallback is not None and fallback < len(parts) else None
        period_text = get("period", "periodo", fallback=3)
        es_text = get("marginales", "marginales/esp", "marginales.es", "maximoes", "minimoes", "medioes", fallback=4)
        if kind == "idc":
            # PRECIOS_PIBCIC official no-header layout places MedioES in the
            # 11th field (zero-based index 10): Max/Min/VWAP for ES/PT/MO.
            es_text = get("medioes", "medi oes", fallback=10 if len(parts) > 10 else 4)
        row: dict[str, Any] = {"source": "OMIE", "kind": kind, "delivery_date": delivery_date, "period": int(float(period_text)) if period_text else None, "price_es_eur_mwh": parse_number(es_text), "raw_line": raw}
        row["price_es_field"] = "MedioES" if kind == "idc" else "MarginalES"
        # Retain common source components if present; do not invent a timestamp.
        for key, (aliases, fallback) in {"year": (("year", "ano", "año"), 0), "month": (("month", "mes"), 1), "day": (("day", "dia", "día"), 2)}.items():
            val = get(*aliases, fallback=fallback)
            row[key] = int(float(val)) if val and parse_number(val) is not None else None
        output.append(row)
    return output


def standardize_omie_rows(rows: list[dict[str, Any]], source_period: str | None = None) -> list[dict[str, Any]]:
    """Add explicit time fields where a source delivery date and period exist."""
    result = []
    for row in rows:
        item = dict(row)
        item["source_period"] = source_period or item.get("delivery_date")
        period = item.get("period")
        delivery = item.get("delivery_date")
        if delivery and period is not None and period >= 1:
            granularity = _omie_granularity(item.get("kind"), str(delivery))
            # Expand from local market-day midnight to UTC, then add the
            # source period.  This correctly skips the spring gap and emits
            # both autumn fold occurrences with unique UTC timestamps.
            try:
                from zoneinfo import ZoneInfo
                market_day = date.fromisoformat(str(delivery))
                zone = ZoneInfo("Europe/Madrid")
                local_midnight = datetime(market_day.year, market_day.month, market_day.day, tzinfo=zone)
                utc_start = local_midnight.astimezone(timezone.utc)
                step = timedelta(minutes=15 if granularity == "15min" else 60)
                utc_time = utc_start + step * (period - 1)
                local = utc_time.astimezone(zone)
                item["local_time_naive"] = local.replace(tzinfo=None).isoformat()
                item["local_time"] = local.isoformat()
                item["utc_time"] = utc_time.isoformat().replace("+00:00", "Z")
                offset = local.strftime("%z")
                item["utc_offset"] = offset[:3] + ":" + offset[3:]
                item["dst_fold"] = local.fold
            except Exception:
                item.update({"local_time_naive": None, "local_time": None, "utc_time": None, "utc_offset": None, "dst_fold": None})
            item["period_granularity"] = granularity
        else:
            item.update({"local_time_naive": None, "local_time": None, "utc_time": None, "utc_offset": None, "dst_fold": None})
            item["period_granularity"] = "source_period"
        result.append(item)
    return result


def _omie_granularity(kind: str | None, delivery_date: str) -> str:
    """Return the audited market granularity from the delivery-date cutovers."""
    try:
        d = date.fromisoformat(delivery_date)
    except ValueError:
        return "source_period"
    if kind == "da":
        return "15min" if d >= date(2025, 10, 1) else "hour"
    if kind in {"ida1", "ida2", "ida3", "idc"}:
        # Operation go-live was 2025-03-18; the first delivery day was
        # 2025-03-19, which is the date used for source-file classification.
        return "15min" if d >= date(2025, 3, 19) else "hour"
    return "source_period"


def write_standardized_csv(rows: list[dict[str, Any]], path: str | Path) -> None:
    if not rows:
        Path(path).write_text("", encoding="utf-8")
        return
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)


def normalize_omie_directory(raw_root: str | Path, start: date | str, end: date | str, kinds: list[str] | None = None) -> list[dict[str, Any]]:
    """Parse the newest immutable response for every requested source file."""
    raw_root = Path(raw_root)
    kinds = kinds or list(OMIE_KIND_CONFIG)
    # Index each calendar month separately.  A range may cross month/year
    # boundaries; indexing only start's month silently dropped those files.
    monthly: dict[str, dict[str, Path]] = {}
    def index_month(month: str) -> dict[str, Path]:
        if month in monthly:
            return monthly[month]
        root = raw_root / "omie" / month
        by_name: dict[str, Path] = {}
        # Most OMIE daily files use the historical ``.1`` revision suffix,
        # but corrected releases can use ``.2``, ``.3`` … (for example
        # marginalpdbc_20251030.3).  Keep all numeric revision files so a
        # later revision can repair an apparent missing ``.1`` file.
        for path in root.rglob("*") if root.exists() else []:
            if not path.is_file() or not (path.name.endswith(".1") or re.match(r"^marginalpdbc_\d{8}\.\d+$", path.name)):
                continue
            prior = by_name.get(path.name)
            if prior is None or path.stat().st_mtime > prior.stat().st_mtime:
                by_name[path.name] = path
        monthly[month] = by_name
        return by_name
    result: list[dict[str, Any]] = []
    for current in (_as_date(start) + timedelta(days=i) for i in range((_as_date(end) - _as_date(start)).days + 1)):
        for kind in kinds:
            name = omie_filename(kind, current)
            month_index = index_month(current.strftime("%Y-%m"))
            path = month_index.get(name)
            if path is None and kind == "da":
                # A corrected DA price may be published as
                # marginalpdbc_YYYYMMDD.2/.3 instead of replacing .1.
                prefix = f"marginalpdbc_{current:%Y%m%d}."
                revisions = [(int(candidate.name.rsplit(".", 1)[1]), candidate) for candidate in month_index.values() if candidate.name.startswith(prefix) and candidate.name.rsplit(".", 1)[1].isdigit()]
                if revisions:
                    path = max(revisions, key=lambda item: item[0])[1]
            if path is None:
                continue
            try:
                standardized = standardize_omie_rows(parse_omie(path, kind, current.isoformat()), current.isoformat())
                for item in standardized:
                    item["source_file"] = path.name
                    item["source_path"] = str(path)
                result.extend(standardized)
            except ValueError:
                continue
    return result
