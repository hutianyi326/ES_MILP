"""ENTSO-E Transparency Platform A75 actual-generation collector.

Only the audited transport contract is encoded here.  Resolution, PSR type,
area type, units and returned series are read from each response; no BZN/CTA
or storage technology assumption is made.
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from .common import iso_now, is_html, json_dump, safe_write_bytes, sha256_bytes
from .ree import CredentialError, HTTPResponse

BASE_URL = "https://web-api.tp.entsoe.eu/api"
SPAIN_EIC = "10YES-REE------0"


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _text(parent: ET.Element, name: str) -> str | None:
    for child in list(parent):
        if _local(child.tag) == name:
            return (child.text or "").strip() or None
    return None


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.strip().replace("Z", "+00:00")).astimezone(timezone.utc)


def _resolution_step(resolution: str | None) -> timedelta | None:
    if not resolution:
        return None
    match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", resolution)
    if match:
        seconds = int(match.group(1) or 0) * 3600 + int(match.group(2) or 0) * 60 + int(match.group(3) or 0)
        return timedelta(seconds=seconds) if seconds else None
    match = re.fullmatch(r"P(?:(\d+)D)?", resolution)
    return timedelta(days=int(match.group(1))) if match and match.group(1) else None


def parse_entsoe_xml(source: bytes | str | Path) -> list[dict[str, Any]]:
    """Expand every A75 TimeSeries/Period/Point into UTC point records."""
    body = source if isinstance(source, bytes) else Path(source).read_bytes()
    if is_html(body):
        raise ValueError("HTML response is not an ENTSO-E XML business response")
    root = ET.fromstring(body)
    if _local(root.tag).lower() in {"error", "errors"}:
        raise ValueError("ENTSO-E error XML response")
    document_type = _text(root, "type") or _text(root, "documentType")
    process_type = _text(root, "processType") or _text(root, "process.processType")
    business_type = _text(root, "businessType")
    rows: list[dict[str, Any]] = []
    for series in root.iter():
        if _local(series.tag) != "TimeSeries":
            continue
        fields: dict[str, str | None] = {}
        for child in list(series):
            name = _local(child.tag)
            if name in {"mRID", "businessType", "processType", "process.processType", "product", "objectAggregation", "inBiddingZone_Domain", "outBiddingZone_Domain", "in_Domain", "out_Domain", "inBiddingZone_Domain.mRID", "outBiddingZone_Domain.mRID", "in_Domain.mRID", "out_Domain.mRID", "psrType", "curveType", "areaType", "resolution", "quantity_Measure_Unit.name", "energy_Measure_Unit.name"}:
                fields[name] = (child.text or "").strip() or None
            elif name == "MktPSRType":
                fields["psrType"] = _text(child, "psrType")
        series_id = fields.get("mRID")
        # Explicitly retain domain elements; never infer AreaType or a zone.
        area = (fields.get("inBiddingZone_Domain.mRID") or fields.get("in_Domain.mRID") or fields.get("outBiddingZone_Domain.mRID") or fields.get("out_Domain.mRID") or fields.get("inBiddingZone_Domain") or fields.get("in_Domain") or fields.get("outBiddingZone_Domain") or fields.get("out_Domain"))
        series_resolution = fields.get("resolution")
        series_psr = fields.get("psrType")
        for period in series.iter():
            if _local(period.tag) != "Period":
                continue
            interval = next((c for c in list(period) if _local(c.tag) == "timeInterval"), None)
            if interval is None:
                continue
            start_value = _text(interval, "start")
            end_value = _text(interval, "end")
            resolution = _text(period, "resolution") or series_resolution
            if start_value is None:
                continue
            start = _parse_time(start_value)
            end = _parse_time(end_value) if end_value else None
            step = _resolution_step(resolution)
            for point in list(period):
                if _local(point.tag) != "Point":
                    continue
                position_text = _text(point, "position")
                if position_text is None:
                    continue
                try:
                    position = int(position_text)
                except ValueError:
                    continue
                quantity = next((c.text for c in list(point) if _local(c.tag) in {"quantity", "energy_Quantity"}), None)
                timestamp = start + step * (position - 1) if step else None
                rows.append({
                    "timeseries_mrid": series_id,
                    "document_type": document_type,
                    "process_type": fields.get("processType") or process_type,
                    "business_type": fields.get("businessType") or business_type,
                    "curve_type": fields.get("curveType"),
                    "resolution": resolution,
                    "position": position,
                    "period_start_utc": start.isoformat().replace("+00:00", "Z"),
                    "period_end_utc": end.isoformat().replace("+00:00", "Z") if end else None,
                    "timestamp_utc": timestamp.isoformat().replace("+00:00", "Z") if timestamp else None,
                    "psr_type": series_psr,
                    "unit": fields.get("quantity_Measure_Unit.name") or fields.get("energy_Measure_Unit.name"),
                    "area": area,
                    "in_bidding_zone_domain": fields.get("inBiddingZone_Domain"),
                    "out_bidding_zone_domain": fields.get("outBiddingZone_Domain"),
                    "in_domain": fields.get("in_Domain"),
                    "out_domain": fields.get("out_Domain"),
                    "in_bidding_zone_domain_mrid": fields.get("inBiddingZone_Domain.mRID"),
                    "out_bidding_zone_domain_mrid": fields.get("outBiddingZone_Domain.mRID"),
                    "in_domain_mrid": fields.get("in_Domain.mRID"),
                    "out_domain_mrid": fields.get("out_Domain.mRID"),
                    "area_type": fields.get("areaType"),
                    "quantity": quantity.strip() if quantity else None,
                })
    return rows


def _utc_compact(value: str) -> str:
    text = value.strip()
    dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y%m%d%H%M")


def _safe_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    # Do not even retain the securityToken parameter name in persisted URLs;
    # the token is transport-only and a redacted key can still be misleading
    # in logs or copied into later requests.
    query = [(key, value) for key, value in query if key.lower() != "securitytoken"]
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urllib.parse.urlencode(query), parsed.fragment))


def build_entsoe_url(start: str, end: str, domain: str = SPAIN_EIC, resolution: str | None = None, psr_type: str | None = None, api_key: str | None = None) -> str:
    """Build an A75 URL; token inclusion is opt-in and always redacted by logs."""
    params: dict[str, str] = {"documentType": "A75", "processType": "A16", "businessType": "A01", "in_Domain": domain, "periodStart": _utc_compact(start), "periodEnd": _utc_compact(end)}
    if resolution:
        params["resolution"] = resolution
    if psr_type:
        params["psrType"] = psr_type
    if api_key:
        params["securityToken"] = api_key
    return f"{BASE_URL}?{urllib.parse.urlencode(params)}"


def _get(url: str, opener: Callable[..., Any] | None = None, timeout: float = 60.0) -> HTTPResponse:
    request = urllib.request.Request(url, headers={"Accept": "application/xml"}, method="GET")
    opener = opener or urllib.request.urlopen
    try:
        with opener(request, timeout=timeout) as response:
            return HTTPResponse(int(getattr(response, "status", response.getcode())), dict(response.headers), response.read())
    except urllib.error.HTTPError as exc:
        return HTTPResponse(exc.code, dict(exc.headers or {}), exc.read())


def download_entsoe(start: str, end: str, raw_root: str | Path = "data/raw/ES", domain: str = SPAIN_EIC, resolution: str | None = None, psr_type: str | None = None, api_key: str | None = None, opener: Callable[..., Any] | None = None, retrieval_batch: str | None = None) -> dict[str, Any]:
    key = api_key if api_key is not None else __import__("os").environ.get("ENTSOE_API_KEY")
    if not key or not key.strip():
        raise CredentialError("ENTSOE_API_KEY is missing; ENTSO-E request skipped")
    real_url = build_entsoe_url(start, end, domain, resolution, psr_type, key)
    safe_url = _safe_url(real_url)
    response = _get(real_url, opener=opener)
    batch = retrieval_batch or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    period = start[:7] if len(start) >= 7 else datetime.now(timezone.utc).strftime("%Y-%m")
    filename = f"a75_actual_generation_{_utc_compact(start)}_{_utc_compact(end)}.xml"
    target = Path(raw_root) / "entsoe" / period / batch / filename
    record: dict[str, Any] = {"source": "entsoe", "dataset": "ENTSOE_A75_ACTUAL_GENERATION", "document_type": "A75", "process_type": "A16", "business_type": "A01", "domain": domain, "period_start_utc": _utc_compact(start), "period_end_utc": _utc_compact(end), "resolution_requested": resolution, "psr_type_requested": psr_type, "url": safe_url, "retrieved_at": iso_now(), "http_status": response.status, "bytes": len(response.body), "sha256": sha256_bytes(response.body), "path": str(target), "status": "failed"}
    if response.status == 200 and response.body and not is_html(response.body):
        try:
            parsed_rows = parse_entsoe_xml(response.body)
        except (ET.ParseError, ValueError):
            parsed_rows = []
            record["status"] = "failed_payload"
        if record["status"] != "failed_payload":
            record["status"] = "success" if parsed_rows else "empty_business_file"
        if safe_write_bytes(target, response.body):
            pass
        else:
            record["status"] = "already_exists"
    elif response.status == 200 and is_html(response.body):
        record["status"] = "failed_html_response"
    else:
        record["status"] = "failed"
    manifest = target.parent / "manifest.json"
    previous: list[dict[str, Any]] = []
    if manifest.exists():
        try: previous = json.loads(manifest.read_text(encoding="utf-8")).get("records", [])
        except (ValueError, OSError): previous = []
    previous.append(record)
    json_dump(manifest, {"schema": "ES-DATA-01/entsoe-manifest-v1", "source": "entsoe", "retrieval_batch": batch, "records": previous})
    return record
