"""Dependency-free clients for REE eSIOS and REData APIs.

eSIOS calls intentionally fail clearly when ``ESIOS_API_KEY`` is absent.  No
file in the repository is considered a credential source.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .common import iso_now, json_dump, redact_headers, safe_write_bytes, sha256_bytes


class CredentialError(RuntimeError):
    """Raised when an authenticated eSIOS operation has no personal key."""


class HTTPResponse:
    def __init__(self, status: int, headers: dict[str, str], body: bytes):
        self.status, self.headers, self.body = status, headers, body


def _http_get(url: str, headers: dict[str, str] | None = None, timeout: float = 60.0, opener: Callable[..., Any] | None = None) -> HTTPResponse:
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    opener = opener or urllib.request.urlopen
    try:
        with opener(req, timeout=timeout) as resp:
            return HTTPResponse(int(getattr(resp, "status", resp.getcode())), dict(resp.headers), resp.read())
    except urllib.error.HTTPError as exc:
        return HTTPResponse(exc.code, dict(exc.headers or {}), exc.read())


class REDataClient:
    base_url = "https://apidatos.ree.es"

    def __init__(self, opener: Callable[..., Any] | None = None, timeout: float = 60.0):
        self.opener, self.timeout = opener, timeout

    def build_url(self, category: str, widget: str, start_date: str, end_date: str, time_trunc: str = "hour", **kwargs: str) -> str:
        if time_trunc not in {"hour", "day", "month", "year"}:
            raise ValueError("REData time_trunc must be hour, day, month, or year")
        params = {"start_date": start_date, "end_date": end_date, "time_trunc": time_trunc, **kwargs}
        return f"{self.base_url}/es/datos/{category}/{widget}?{urllib.parse.urlencode(params)}"

    def fetch(self, category: str = "generacion", widget: str = "estructura-generacion", start_date: str = "", end_date: str = "", time_trunc: str = "hour", **kwargs: str) -> tuple[HTTPResponse, dict[str, Any] | None]:
        if not start_date or not end_date:
            raise ValueError("start_date and end_date are required")
        url = self.build_url(category, widget, start_date, end_date, time_trunc, **kwargs)
        response = _http_get(url, {"Accept": "application/json"}, self.timeout, self.opener)
        try:
            parsed = json.loads(response.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            parsed = None
        return response, parsed

    @staticmethod
    def records(payload: dict[str, Any] | None) -> list[dict[str, Any]]:
        """Flatten REData JSON:API ``included[].attributes.values`` rows."""
        rows: list[dict[str, Any]] = []
        if not isinstance(payload, dict):
            return rows
        for item in payload.get("included", []) or []:
            if not isinstance(item, dict):
                continue
            attributes = item.get("attributes", item)
            if not isinstance(attributes, dict):
                continue
            title = attributes.get("title")
            magnitude = attributes.get("magnitude")
            status = attributes.get("status") or attributes.get("description")
            values = attributes.get("values", [])
            if isinstance(values, dict):
                values = [values]
            for point in values or []:
                if isinstance(point, dict):
                    row = dict(point)
                    row.update({"technology": title, "magnitude": magnitude, "status": status, "technology_type": attributes.get("type"), "composite": attributes.get("composite"), "last_update": attributes.get("last-update")})
                    rows.append(row)
        return rows

    @staticmethod
    def standardize_rows(rows: list[dict[str, Any]], source_period: str | None = None, time_trunc: str = "hour", derive_average_mw: bool = False) -> list[dict[str, Any]]:
        """Normalize REData values while keeping official energy values.

        ``derive_average_mw`` is deliberately opt-in and only succeeds for an
        hourly interval with a clearly energy-valued magnitude (GWh/MWh/kWh).
        A request's time truncation alone is not treated as proof of the unit.
        """
        result = []
        for row in rows:
            item = dict(row)
            item["source_period"] = source_period
            item["raw_value"] = row.get("value")
            item["raw_unit"] = row.get("magnitude")
            timestamp = row.get("datetime") or row.get("timestamp")
            if timestamp:
                from .common import parse_iso_datetime
                item["source_datetime"] = timestamp
                item["datetime_utc"], item["utc_offset"] = parse_iso_datetime(str(timestamp))
            else:
                item["source_datetime"] = None; item["datetime_utc"] = None; item["utc_offset"] = None
            unit = str(row.get("magnitude") or "").lower().replace(" ", "")
            converted = None
            gate_reason = "not_requested"
            if derive_average_mw:
                if time_trunc != "hour":
                    gate_reason = "requires_hour_interval"
                elif unit in {"gwh", "mwh", "kwh", "wh"} and isinstance(row.get("value"), (int, float)):
                    factors = {"gwh": 1000.0, "mwh": 1.0, "kwh": 0.001, "wh": 0.000001}
                    converted = float(row["value"]) * factors[unit]
                    gate_reason = "hourly_energy_to_average_mw"
                else:
                    gate_reason = "unit_not_verified_as_energy"
            item["average_mw"] = converted
            item["conversion_status"] = gate_reason
            result.append(item)
        return result


class ESIOSClient:
    base_url = "https://api.esios.ree.es"
    allowed_trunc = {"five_minutes", "ten_minutes", "fifteen_minutes", "hour", "day", "month", "year"}

    def __init__(self, api_key: str | None = None, opener: Callable[..., Any] | None = None, timeout: float = 60.0):
        # Deliberately only inspect explicit argument or environment variable.
        self.api_key = api_key if api_key is not None else os.environ.get("ESIOS_API_KEY")
        self.opener, self.timeout = opener, timeout

    @property
    def available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def _require_key(self) -> str:
        if not self.available:
            raise CredentialError("ESIOS_API_KEY is missing; eSIOS request skipped")
        return str(self.api_key)

    def _headers(self) -> dict[str, str]:
        return {"Accept": "application/json, application/vnd.esios-api-v1+json", "Content-Type": "application/json", "x-api-key": self._require_key()}

    def build_indicator_url(self, indicator_id: int | str, start_date: str | None = None, end_date: str | None = None, time_trunc: str | None = None, time_agg: str | None = None, locale: str = "es", **kwargs: str) -> str:
        if time_trunc is not None and time_trunc not in self.allowed_trunc:
            raise ValueError(f"unsupported eSIOS time_trunc: {time_trunc}")
        # Aggregation is only sent when explicitly requested.  In particular,
        # load callers must choose time_agg=average for QH aggregation.
        params: dict[str, str] = {"locale": locale}
        for key, value in (("start_date", start_date), ("end_date", end_date), ("time_trunc", time_trunc), ("time_agg", time_agg)):
            if value is not None:
                params[key] = value
        params.update(kwargs)
        return f"{self.base_url}/indicators/{urllib.parse.quote(str(indicator_id))}?{urllib.parse.urlencode(params)}"

    def fetch_indicator(self, indicator_id: int | str, **kwargs: str) -> tuple[HTTPResponse, dict[str, Any] | None]:
        url = self.build_indicator_url(indicator_id, **kwargs)
        response = _http_get(url, self._headers(), self.timeout, self.opener)
        try:
            payload = json.loads(response.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            payload = None
        return response, payload

    def fetch_load(self, indicator_id: int | str, start_date: str, end_date: str, time_trunc: str = "fifteen_minutes", time_agg: str | None = None, **kwargs: str) -> tuple[HTTPResponse, dict[str, Any] | None]:
        """Fetch a demand indicator with the mandated QH averaging rule."""
        if time_trunc == "fifteen_minutes":
            time_agg = "average"
        return self.fetch_indicator(indicator_id, start_date=start_date, end_date=end_date, time_trunc=time_trunc, time_agg=time_agg, **kwargs)

    def search_indicators(self, text: str, locale: str = "es") -> tuple[HTTPResponse, dict[str, Any] | None]:
        self._require_key()
        url = f"{self.base_url}/indicators?{urllib.parse.urlencode({'text': text, 'locale': locale})}"
        response = _http_get(url, self._headers(), self.timeout, self.opener)
        try:
            payload = json.loads(response.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            payload = None
        return response, payload

    def metadata(self, indicator_id: int | str) -> tuple[HTTPResponse, dict[str, Any] | None]:
        # Metadata uses same indicator route without date parameters.
        return self.fetch_indicator(indicator_id)

    def fetch_archive_list(self, start_date: str, end_date: str, date_type: str = "datos", locale: str = "es") -> tuple[HTTPResponse, dict[str, Any] | None]:
        self._require_key()
        if date_type not in {"datos", "publicacion"}:
            raise ValueError("date_type must be datos or publicacion")
        params = urllib.parse.urlencode({"start_date": start_date, "end_date": end_date, "date_type": date_type, "locale": locale})
        response = _http_get(f"{self.base_url}/archives?{params}", self._headers(), self.timeout, self.opener)
        try:
            payload = json.loads(response.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            payload = None
        return response, payload

    def save_response(self, response: HTTPResponse, path: str | Path, url: str | None = None, request_params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Save a non-secret response and metadata; request headers never persist."""
        path = Path(path)
        created = safe_write_bytes(path, response.body)
        # Request headers (especially x-api-key) and all credentials are
        # intentionally absent.  Response headers are not required for the
        # audit contract and are omitted to avoid accidentally persisting a
        # server-set credential/cookie.
        meta = {"source": "esios", "url": url, "request_params": request_params or {}, "retrieved_at": iso_now(), "http_status": response.status, "bytes": len(response.body), "sha256": sha256_bytes(response.body), "saved": created}
        json_dump(path.with_suffix(path.suffix + ".meta.json"), meta)
        return meta
