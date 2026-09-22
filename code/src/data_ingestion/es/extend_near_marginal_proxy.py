"""Conditionally extend the Spain near-marginal proxy after 2025-03-18.

The historical UO-to-technology crosswalk is still conditional.  This module
therefore produces explicitly labelled proxy outputs only; it never creates an
``Official_*_Setter`` field for the post-calibration period.

The extension is limited to the established evening window (local delivery
hours 19:00--22:00) and the currently available price-history horizon:
2025-03-19--2026-07-31.  It uses hourly DA prices through 2025-09-30 and
15-minute DA prices from 2025-10-01 onward.  UOF energy is converted to MW by
dividing by the interval duration (1 hour or 15 minutes).
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from .common import is_html, iso_now, json_dump, parse_number, retrieval_batch_id, safe_write_bytes, sha256_bytes
from .near_marginal import _canonical_technology
from .omie import normalize_omie_directory, omie_filename


ROOT = Path(__file__).resolve().parents[3]
RAW_ROOT = ROOT / "data/raw/ES"
PROCESSED_ROOT = ROOT / "data/processed/ES"
CROSSWALK_PATH = PROCESSED_ROOT / "omie_uof_technology_crosswalk_candidate_20260904.csv"

START = date(2025, 3, 19)
HOURLY_END = date(2025, 9, 30)
END = date(2026, 7, 31)
EVENING_HOURS = {19, 20, 21, 22}
CROSSWALK_VERSION = "current_OMIE_LIST_20260904_CONDITIONAL"
PROXY_STATUS = "conditional_proxy_crosswalk"

HOURLY_PATH = PROCESSED_ROOT / "omie_near_marginal_proxy_20250319_20250930_evening_hourly.csv"
QH_PATH = PROCESSED_ROOT / "omie_near_marginal_proxy_20251001_20260731_evening_15min.csv"
HOURLY_QUALITY_PATH = PROCESSED_ROOT / "omie_near_marginal_proxy_quality_20250319_20250930_evening.json"
QH_QUALITY_PATH = PROCESSED_ROOT / "omie_near_marginal_proxy_quality_20251001_20260731_evening.json"


def _month_windows(start: date, end: date) -> list[tuple[str, date, date]]:
    windows: list[tuple[str, date, date]] = []
    current = date(start.year, start.month, 1)
    while current <= end:
        next_month = date(current.year + (current.month == 12), 1 if current.month == 12 else current.month + 1, 1)
        window_start = max(start, current)
        window_end = min(end, next_month - timedelta(days=1))
        windows.append((current.strftime("%Y-%m"), window_start, window_end))
        current = next_month
    return windows


def _month_uof_url(month: str) -> str:
    compact = month.replace("-", "")
    query = urllib.parse.urlencode({"filename": f"curva_pbc_uof_{compact}.zip", "parents": "curva_pbc_uof"})
    return f"https://www.omie.es/index.php/en/file-download?{query}"


def _da_price_url(delivery_date: date) -> str:
    query = urllib.parse.urlencode({"filename": omie_filename("da", delivery_date), "parents": "marginalpdbc"})
    return f"https://www.omie.es/index.php/en/file-download?{query}"


def _get(url: str, timeout: float = 180.0) -> tuple[int, dict[str, str], bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": "ES-DATA-07/1.0", "Accept": "*/*"}, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return int(getattr(response, "status", response.getcode())), dict(response.headers), response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers or {}), exc.read()
    except urllib.error.URLError:
        # The managed runtime occasionally cannot resolve www.omie.es through
        # Python's resolver while the system curl resolver succeeds.  Retry
        # the same fixed official URL without changing the source or headers.
        import subprocess

        result = subprocess.run(
            ["curl.exe", "-L", "--fail", "--silent", "--show-error", "--retry", "2", "--max-time", str(int(timeout)), url],
            check=False,
            capture_output=True,
        )
        if result.returncode == 0:
            return 200, {}, result.stdout
        raise urllib.error.URLError(result.stderr.decode("utf-8", errors="replace").strip() or "curl download failed")


def _latest_raw_file(pattern: str) -> Path | None:
    paths = list(RAW_ROOT.glob(pattern))
    return max(paths, key=lambda path: path.stat().st_mtime) if paths else None


def _download_uof_month(month: str, batch: str) -> dict[str, Any]:
    filename = f"curva_pbc_uof_{month.replace('-', '')}.zip"
    existing = _latest_raw_file(f"omie/{month}/**/{filename}")
    if existing is not None:
        return {"month": month, "filename": filename, "url": _month_uof_url(month), "http_status": 200, "bytes": existing.stat().st_size, "sha256": sha256_bytes(existing.read_bytes()), "path": str(existing), "status": "existing"}
    url = _month_uof_url(month)
    target = RAW_ROOT / "omie" / month / batch / filename
    try:
        status, headers, body = _get(url)
        download_error = ""
    except urllib.error.URLError as exc:
        # Keep the run auditable when a future or withdrawn monthly package
        # is unavailable.  A missing package is a data-availability gap, not
        # a reason to discard the valid months already downloaded.
        status, headers, body = 0, {}, b""
        download_error = str(exc.reason if hasattr(exc, "reason") else exc)
    record: dict[str, Any] = {"source": "omie", "dataset": "OMIE_DA_UOF_CURVE_MONTHLY", "kind": "curva_pbc_uof", "period": month, "url": url, "retrieved_at": iso_now(), "http_status": status, "bytes": len(body), "sha256": sha256_bytes(body), "filename": filename, "path": str(target), "status": "failed"}
    if download_error:
        record["error"] = download_error
    if status == 200 and body and not is_html(body):
        target.parent.mkdir(parents=True, exist_ok=True)
        if safe_write_bytes(target, body):
            record["status"] = "success"
        else:
            record["status"] = "already_exists"
    elif status == 200 and is_html(body):
        record["status"] = "failed_html_response"
    manifest = target.parent / "manifest.json"
    json_dump(manifest, {"schema": "ES-DATA-07/uof-manifest-v1", "source": "omie", "retrieval_batch": batch, "records": [record]})
    return record


def _ensure_da_prices(start: date, end: date, batch: str) -> dict[str, Any]:
    requested = downloaded = skipped = failed = 0
    records: list[dict[str, Any]] = []
    current = start
    while current <= end:
        requested += 1
        filename = omie_filename("da", current)
        existing = _latest_raw_file(f"omie/{current:%Y-%m}/**/{filename}")
        if existing is not None:
            skipped += 1
        else:
            url = _da_price_url(current)
            status, headers, body = _get(url)
            target = RAW_ROOT / "omie" / current.strftime("%Y-%m") / batch / filename
            record: dict[str, Any] = {"source": "omie", "dataset": "OMIE_DA_PRICE_ES", "kind": "da", "period": current.strftime("%Y-%m"), "delivery_date": current.isoformat(), "url": url, "retrieved_at": iso_now(), "http_status": status, "bytes": len(body), "sha256": sha256_bytes(body), "filename": filename, "path": str(target), "status": "failed"}
            if status == 200 and body and not is_html(body):
                target.parent.mkdir(parents=True, exist_ok=True)
                record["status"] = "success" if safe_write_bytes(target, body) else "already_exists"
            elif status == 200 and is_html(body):
                record["status"] = "failed_html_response"
            manifest = target.parent / "manifest.json"
            json_dump(manifest, {"schema": "ES-DATA-07/price-manifest-v1", "source": "omie", "retrieval_batch": batch, "records": [record]})
            records.append(record)
            if record.get("status") in {"success", "already_exists"}:
                downloaded += 1
            else:
                failed += 1
        current += timedelta(days=1)
    return {"requested": requested, "downloaded": downloaded, "skipped_existing": skipped, "failed": failed, "records": records}


def _parse_uof_number(value: str | None) -> float | None:
    if value is None:
        return None
    parsed = parse_number(value)
    return float(parsed) if parsed is not None else None


def _market_scope(country: str) -> str:
    return {"MI": "Mibel", "ES": "España", "PT": "Portugal"}.get(country, country)


def _interval_minutes(delivery_date: date) -> int:
    return 60 if delivery_date < date(2025, 10, 1) else 15


def _local_datetime_for_period(delivery_date: date, period: int, interval_minutes: int) -> datetime:
    """Map OMIE period to Europe/Madrid using a UTC timeline for DST folds."""
    from zoneinfo import ZoneInfo

    zone = ZoneInfo("Europe/Madrid")
    midnight = datetime(delivery_date.year, delivery_date.month, delivery_date.day, tzinfo=zone)
    utc = midnight.astimezone(timezone.utc) + timedelta(minutes=interval_minutes * (period - 1))
    return utc.astimezone(zone)


def _parse_member_rows(zf: zipfile.ZipFile, member: str, price_lookup: dict[tuple[str, int], dict[str, Any]], crosswalk: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    """Stream one UOF day, flushing one period at a time."""
    rows: list[dict[str, Any]] = []
    with zf.open(member, "r") as raw:
        text = io.TextIOWrapper(raw, encoding="latin-1", errors="replace")
        bucket: list[dict[str, Any]] = []
        current_key: tuple[str, int] | None = None

        def flush() -> None:
            if not bucket:
                return
            key = (str(bucket[0]["delivery_date"]), int(bucket[0]["period"]))
            price_meta = price_lookup.get(key)
            if price_meta is None:
                bucket.clear()
                return
            mi_rows = [item for item in bucket if item["country_code"] == "MI"]
            selected = mi_rows if mi_rows else [item for item in bucket if item["country_code"] == "ES"]
            price = float(price_meta["price_eur_mwh"])
            interval_minutes = int(price_meta["interval_minutes"])
            regime = "positive" if price > 0 else "zero" if price == 0 else "negative"
            by_technology: dict[str, float] = defaultdict(float)
            mapped_mw = 0.0
            unmapped_mw = 0.0
            selected_count = 0
            selected_uos: set[str] = set()
            low = 0.95 * price
            high = price
            nm_defined = price > 0
            for item in selected:
                offer_price = item.get("price_eur_mwh")
                energy = item.get("energy_mwh")
                if offer_price is None or energy is None or not nm_defined or not (low <= offer_price <= high):
                    continue
                quantity_mw = energy * 60.0 / interval_minutes
                uo = str(item["unit_of_offer"])
                raw_technology = (crosswalk.get(uo, {}).get("mapped_technology") or "").strip() or "unmapped"
                tech = _canonical_technology(raw_technology)
                by_technology[tech] += quantity_mw
                if raw_technology == "unmapped":
                    unmapped_mw += quantity_mw
                else:
                    mapped_mw += quantity_mw
                selected_count += 1
                selected_uos.add(uo)
            total_mw = sum(by_technology.values())
            local = price_meta["local_datetime"]
            output: dict[str, Any] = {
                "delivery_date": key[0],
                "data_date": key[0],
                "period": key[1],
                "delivery_hour": local.hour,
                "local_datetime": local.isoformat(),
                "timezone": "Europe/Madrid",
                "period_granularity": price_meta["period_granularity"],
                "market_version": "DA_15MIN_MTU" if interval_minutes == 15 else "DA_HOURLY",
                "issued_at": "",
                "retrieved_at": price_meta.get("retrieved_at", ""),
                "price_eur_mwh": round(price, 6),
                "price_regime": regime,
                "proxy_status": PROXY_STATUS,
                "official_setter_labels": "",
                "nm_window": "relative_95" if nm_defined else "not_defined_nonpositive_price",
                "nm_lower_bound_eur_mwh": round(low, 6) if nm_defined else "",
                "nm_upper_bound_eur_mwh": round(high, 6) if nm_defined else "",
                "nm_total_mw": round(total_mw, 6),
                "nm_mapped_mw": round(mapped_mw, 6),
                "nm_unmapped_mw": round(unmapped_mw, 6),
                "crosswalk_coverage": round(mapped_mw / total_mw, 10) if total_mw else 0.0,
                "selected_offer_rows": selected_count,
                "selected_uo_count": len(selected_uos),
                "market_rows_used": "MI" if mi_rows else "ES",
                "price_source_file": price_meta["source_file"],
                "price_retrieved_at": price_meta.get("retrieved_at", ""),
                "price_source_path": price_meta.get("source_path", ""),
                "source_file": member,
                "uof_source_file": member,
                "crosswalk_version": CROSSWALK_VERSION,
            }
            for technology in ("CCGT", "Hydro", "PumpedHydro", "Wind", "SolarPV", "RenewCogRes", "Nuclear", "Coal", "Other"):
                value = by_technology.get(technology, 0.0)
                output[f"{technology}_NM_MW"] = round(value, 6)
                output[f"{technology}_NMShare_all"] = round(value / total_mw, 10) if total_mw else 0.0
            rows.append(output)
            bucket.clear()

        for raw_line in text:
            line = raw_line.strip().lstrip("\ufeff")
            if not line or line.startswith(("OMIE", "Hora;", "Fecha;")):
                continue
            parts = [part.strip() for part in line.split(";")]
            if len(parts) < 8:
                continue
            try:
                # Hourly UOF files use integer periods (1..24), while the
                # 15-minute files introduced for the 2025-10-01 MTU change
                # use labels such as H1Q1..H24Q4.  Normalize both forms to
                # the same 1..96 market-period index used by OMIE DA prices.
                period_text = parts[0].upper()
                if period_text.startswith("H") and "Q" in period_text:
                    hour_text, quarter_text = period_text[1:].split("Q", 1)
                    period = (int(hour_text) - 1) * 4 + int(quarter_text)
                else:
                    period = int(period_text)
                delivery_date = datetime.strptime(parts[1], "%d/%m/%Y").date()
            except (ValueError, TypeError):
                continue
            if not (START <= delivery_date <= END):
                continue
            interval_minutes = _interval_minutes(delivery_date)
            local = _local_datetime_for_period(delivery_date, period, interval_minutes)
            if local.hour not in EVENING_HOURS:
                continue
            key = (delivery_date.isoformat(), period)
            if current_key is not None and key != current_key:
                flush()
            current_key = key
            if parts[4] != "V" or parts[7] != "C":
                continue
            energy = _parse_uof_number(parts[5])
            offer_price = _parse_uof_number(parts[6])
            bucket.append({
                "delivery_date": delivery_date.isoformat(),
                "period": period,
                "country_code": parts[2],
                "unit_of_offer": parts[3],
                "offer_type": parts[4],
                "energy_mwh": energy,
                "price_eur_mwh": offer_price,
                "offered_or_cashed": parts[7],
            })
        flush()
    return rows


def _load_crosswalk() -> dict[str, dict[str, str]]:
    with CROSSWALK_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        return {row.get("unit_of_offer", ""): row for row in csv.DictReader(handle)}


def _uof_retrieved_at(package: Path) -> str:
    manifest = package.parent / "manifest.json"
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    for item in payload.get("records", []) or []:
        if item.get("filename") == package.name:
            return str(item.get("retrieved_at", ""))
    return ""


def _price_manifest_index() -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for manifest in RAW_ROOT.glob("omie/**/manifest.json"):
        try:
            payload = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for item in payload.get("records", []) or []:
            if item.get("kind") == "da" and item.get("filename"):
                prior = result.get(str(item["filename"]))
                if prior is None or str(item.get("retrieved_at", "")) > prior.get("retrieved_at", ""):
                    result[str(item["filename"])] = {
                        "retrieved_at": str(item.get("retrieved_at", "")),
                        "path": str(item.get("path", "")),
                    }
    return result


def _price_index(rows: Iterable[dict[str, Any]], manifest_index: dict[str, dict[str, str]]) -> dict[tuple[str, int], dict[str, Any]]:
    result: dict[tuple[str, int], dict[str, Any]] = {}
    for row in rows:
        try:
            delivery = str(row.get("delivery_date"))
            period = int(row.get("period"))
            price = float(row.get("price_es_eur_mwh"))
            local_text = str(row.get("local_time"))
            local = datetime.fromisoformat(local_text)
        except (TypeError, ValueError):
            continue
        if local.hour not in EVENING_HOURS:
            continue
        source_file = str(row.get("source_file") or f"marginalpdbc_{delivery.replace('-', '')}.1")
        manifest = manifest_index.get(source_file, {})
        result[(delivery, period)] = {
            "price_eur_mwh": price,
            "local_datetime": local,
            "period_granularity": row.get("period_granularity", "source_period"),
            "interval_minutes": 15 if row.get("period_granularity") == "15min" else 60,
            "source_file": source_file,
            "retrieved_at": manifest.get("retrieved_at", ""),
            "source_path": str(row.get("source_path") or manifest.get("path", "")),
        }
    return result


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _expected_periods(start: date, end: date) -> set[tuple[str, int]]:
    result: set[tuple[str, int]] = set()
    current = start
    while current <= end:
        interval = _interval_minutes(current)
        # Build expected keys from the local/UTC period mapping so DST days
        # retain 23/25-hour market-day behavior.
        for period in range(1, 101 if interval == 15 else 25):
            local = _local_datetime_for_period(current, period, interval)
            if local.date() != current or local.hour not in EVENING_HOURS:
                continue
            result.add((current.isoformat(), period))
        current += timedelta(days=1)
    return result


def run(start: date = START, hourly_end: date = HOURLY_END, end: date = END) -> dict[str, Any]:
    batch = retrieval_batch_id()
    # Price files from 2025-03-19 through 2025-06-30 were not previously in
    # raw; later price history already exists and is never overwritten.
    price_download = _ensure_da_prices(start, date(2025, 6, 30), batch)
    uof_downloads = [_download_uof_month(month, batch) for month, _window_start, _window_end in _month_windows(start, end)]
    normalized_prices = normalize_omie_directory(RAW_ROOT, start, end, kinds=["da"])
    prices = _price_index(normalized_prices, _price_manifest_index())
    crosswalk = _load_crosswalk()
    packages: dict[str, Path] = {}
    for month, _window_start, _window_end in _month_windows(start, end):
        package = _latest_raw_file(f"omie/{month}/**/curva_pbc_uof_{month.replace('-', '')}.zip")
        if package is not None:
            packages[month] = package

    rows: list[dict[str, Any]] = []
    for month in sorted(packages):
        package_retrieved_at = _uof_retrieved_at(packages[month])
        with zipfile.ZipFile(packages[month]) as zf:
            for member in sorted(zf.namelist()):
                if not member.lower().endswith(".1"):
                    continue
                member_rows = _parse_member_rows(zf, member, prices, crosswalk)
                for item in member_rows:
                    item["uof_source_zip"] = packages[month].name
                    item["uof_source_zip_path"] = str(packages[month])
                    item["uof_retrieved_at"] = package_retrieved_at
                rows.extend(member_rows)
    rows.sort(key=lambda row: (str(row["delivery_date"]), int(row["period"])))
    hourly_rows = [row for row in rows if start <= date.fromisoformat(str(row["delivery_date"])) <= hourly_end]
    qh_rows = [row for row in rows if date.fromisoformat(str(row["delivery_date"])) >= date(2025, 10, 1) and date.fromisoformat(str(row["delivery_date"])) <= end]
    _write_csv(HOURLY_PATH, hourly_rows)
    _write_csv(QH_PATH, qh_rows)

    def quality(output_path: Path, output_rows: list[dict[str, Any]], window_start: date, window_end: date) -> dict[str, Any]:
        expected = _expected_periods(window_start, window_end)
        observed = {(str(row["delivery_date"]), int(row["period"])) for row in output_rows}
        prices_observed = {(key[0], key[1]) for key in prices if window_start.isoformat() <= key[0] <= window_end.isoformat()}
        missing = expected - observed
        missing_by_month: dict[str, int] = defaultdict(int)
        for delivery, _period in missing:
            missing_by_month[delivery[:7]] += 1
        missing_dates = sorted({delivery for delivery, _period in missing})
        price_missing = expected - prices_observed
        return {
            "status": "conditional_proxy_extension" if not missing else "conditional_proxy_extension_partial",
            "proxy_status": PROXY_STATUS,
            "timezone": "Europe/Madrid",
            "window_start": window_start.isoformat(),
            "window_end": window_end.isoformat(),
            "evening_delivery_hours": sorted(EVENING_HOURS),
            "rows": len(output_rows),
            "unique_delivery_period_keys": len(observed),
            "expected_delivery_period_keys": len(expected),
            "missing_expected_keys": len(missing),
            "missing_expected_keys_by_month": dict(sorted(missing_by_month.items())),
            "missing_expected_dates": missing_dates,
            "price_keys_observed": len(prices_observed),
            "price_missing_expected_keys": len(price_missing),
            "rows_with_nm_selected": sum(float(row.get("nm_total_mw") or 0) > 0 for row in output_rows),
            "nonpositive_price_rows": sum(row.get("price_regime") in {"zero", "negative"} for row in output_rows),
            "market_rows_used": {market: sum(row.get("market_rows_used") == market for row in output_rows) for market in ("MI", "ES")},
            "output": str(output_path),
            "crosswalk_version": CROSSWALK_VERSION,
            "assumptions": {
                "relative_95_window": True,
                "uof_energy_to_mw": "divide_by_interval_hours",
                "crosswalk_is_conditional": True,
                "official_setter_not_generated_post_20250318": True,
                "source_price_basis": "OMIE_marginalpdbc",
            },
        }

    hourly_quality = quality(HOURLY_PATH, hourly_rows, start, hourly_end)
    qh_quality = quality(QH_PATH, qh_rows, date(2025, 10, 1), end)
    hourly_quality["downloads"] = {"price": price_download, "uof": uof_downloads}
    qh_quality["downloads"] = {"price": price_download, "uof": uof_downloads}
    json_dump(HOURLY_QUALITY_PATH, hourly_quality)
    json_dump(QH_QUALITY_PATH, qh_quality)
    return {"hourly": hourly_quality, "qh": qh_quality, "package_count": len(packages), "price_rows": len(normalized_prices)}


def main() -> int:
    parser = argparse.ArgumentParser(prog="extend-near-marginal-proxy")
    parser.add_argument("--start", default=START.isoformat())
    parser.add_argument("--hourly-end", default=HOURLY_END.isoformat())
    parser.add_argument("--end", default=END.isoformat())
    args = parser.parse_args()
    result = run(date.fromisoformat(args.start), date.fromisoformat(args.hourly_end), date.fromisoformat(args.end))
    print(json.dumps({"hourly": result["hourly"], "qh": result["qh"], "package_count": result["package_count"], "price_rows": result["price_rows"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
