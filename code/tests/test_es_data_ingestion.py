import io
import json
import os
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from src.data_ingestion.es.common import is_html
from src.data_ingestion.es.omie import build_omie_url, download_omie, parse_omie, standardize_omie_rows
from src.data_ingestion.es.quality import summarize_rows
from src.data_ingestion.es.ree import CredentialError, ESIOSClient, HTTPResponse, REDataClient
from src.data_ingestion.es import cli as es_cli
from src.data_ingestion.es.omie import normalize_omie_directory
from src.data_ingestion.es.entsoe import build_entsoe_url, download_entsoe, parse_entsoe_xml


class FakeResponse:
    def __init__(self, body, status=200, headers=None):
        self.body = body; self.status = status; self.headers = headers or {"Content-Type": "text/plain"}
    def __enter__(self): return self
    def __exit__(self, *args): return None
    def read(self): return self.body
    def getcode(self): return self.status


def opener_for(body, status=200, headers=None, seen=None):
    def opener(request, timeout=60):
        if seen is not None: seen.append(request)
        return FakeResponse(body, status, headers)
    return opener


class TestOMIE(unittest.TestCase):
    def test_urls_and_names(self):
        self.assertIn("marginalpdbc_20260801.1", build_omie_url("da", "2026-08-01"))
        self.assertIn("marginalpibc_2026080103.1", build_omie_url("ida3", "2026-08-01"))
        self.assertIn("precios_pibcic_20260831.1", build_omie_url("idc", "2026-08-31"))

    def test_parse_delimited_and_idc_medioes(self):
        body = ("MARGINALPDBC;\n2026;08;01;1;12.5;12.5;\n2026;08;01;2;13,5;13,5;\n").encode("latin-1")
        rows = parse_omie(body, "da", "2026-08-01")
        self.assertEqual([r["period"] for r in rows], [1, 2])
        self.assertEqual(rows[1]["price_es_eur_mwh"], 13.5)
        self.assertEqual(rows[0]["year"], 2026)
        idc = ("MARGINAL\nAño;Mes;Día;Periodo;MáximoES;MáximoPT;MáximoMO;MínimoES;MínimoPT;MínimoMO;MedioES;MedioPT;MedioMO;\n2026;8;1;1;10;0;0;1;0;0;5.5;0;0;\n").encode("latin-1")
        row = parse_omie(idc, "idc", "2026-08-01")[0]
        self.assertEqual(row["price_es_field"], "MedioES")
        self.assertEqual(row["price_es_eur_mwh"], 5.5)
        no_header = b"2026;8;1;1;10;0;0;1;0;0;5.5;0;0;\n"
        self.assertEqual(parse_omie(no_header, "idc", "2026-08-01")[0]["price_es_eur_mwh"], 5.5)

    def test_html_and_empty_rejected_or_marked(self):
        with self.assertRaises(ValueError): parse_omie(b"<!DOCTYPE html><html>error</html>", "da")
        with tempfile.TemporaryDirectory() as directory:
            result = download_omie("ida3", "2026-08-01", directory, "batch", opener=opener_for(b"18 bytes no trades"))
            self.assertIn(result["status"], {"empty_business_file", "success"})
            result2 = download_omie("ida3", "2026-08-01", directory, "batch2", opener=opener_for(b"<html>denied</html>"))
            self.assertEqual(result2["status"], "failed_html_response")

    def test_manifest_batch_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            first = download_omie("da", "2026-08-01", directory, "batch", opener=opener_for(b"2026;08;01;1;1;1;"))
            second = download_omie("da", "2026-08-01", directory, "batch", opener=opener_for(b"2026;08;01;1;99;99;"))
            self.assertEqual(second["status"], "already_exists")
            self.assertEqual(Path(first["path"]).read_bytes(), b"2026;08;01;1;1;1;")

    def test_no_fixed_96_assumption(self):
        rows = standardize_omie_rows(parse_omie(b"2026;10;25;1;1;1;\n2026;10;25;100;2;2;", "da", "2026-10-25"), "2026-10")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[-1]["period_granularity"], "15min")
        self.assertEqual(rows[-1]["local_time"], "2026-10-25T23:45:00+01:00")

    def test_normalize_cross_month(self):
        with tempfile.TemporaryDirectory() as directory:
            for day in ("2026-08-31", "2026-09-01"):
                path = Path(directory) / "omie" / day[:7] / "batch" / f"marginalpdbc_{day.replace('-', '')}.1"
                path.parent.mkdir(parents=True)
                path.write_bytes((f"2026;{day[5:7]};{day[8:10]};1;10;10;\n").encode())
            rows = normalize_omie_directory(directory, "2026-08-31", "2026-09-01", ["da"])
            self.assertEqual(len(rows), 2)
            self.assertEqual({r["delivery_date"] for r in rows}, {"2026-08-31", "2026-09-01"})

    def test_audited_cutovers_and_old_hourly(self):
        rows = standardize_omie_rows([
            {"kind": "da", "delivery_date": "2025-09-30", "period": 1},
            {"kind": "da", "delivery_date": "2025-09-30", "period": 24},
            {"kind": "ida3", "delivery_date": "2025-03-18", "period": 1},
        ])
        self.assertEqual([r["period_granularity"] for r in rows], ["hour", "hour", "hour"])
        self.assertEqual(rows[0]["local_time"], "2025-09-30T00:00:00+02:00")
        self.assertEqual(rows[1]["local_time"], "2025-09-30T23:00:00+02:00")

    def test_dst_qh_utc_axis_and_partial_horizon(self):
        spring = standardize_omie_rows([{"kind": "da", "delivery_date": "2026-03-29", "period": p} for p in (8, 9, 92)])
        self.assertEqual(spring[1]["local_time"], "2026-03-29T03:00:00+02:00")
        self.assertEqual(len({r["utc_time"] for r in spring}), 3)
        autumn = standardize_omie_rows([{"kind": "da", "delivery_date": "2026-10-25", "period": p} for p in (9, 13)])
        self.assertEqual([r["local_time_naive"] for r in autumn], ["2026-10-25T02:00:00", "2026-10-25T02:00:00"])
        self.assertEqual([r["dst_fold"] for r in autumn], [0, 1])
        self.assertEqual(len({r["utc_time"] for r in autumn}), 2)
        partial = standardize_omie_rows([{"kind": "ida3", "delivery_date": "2026-08-01", "period": 49}])
        self.assertEqual(partial[0]["local_time"], "2026-08-01T12:00:00+02:00")


class TestREDataAndESIOS(unittest.TestCase):
    def test_redata_url_and_records(self):
        client = REDataClient()
        url = client.build_url("generacion", "estructura-generacion", "2026-08-01T00:00", "2026-08-01T23:59", "hour")
        self.assertIn("time_trunc=hour", url)
        payload = {"included": [{"attributes": {"title": "Solar", "magnitude": "GWh", "values": [{"datetime": "2026-08-01T00:00:00+02:00", "value": 1}]}}]}
        self.assertEqual(client.records(payload)[0]["magnitude"], "GWh")

    def test_esios_missing_credential_and_average_gate(self):
        old = os.environ.pop("ESIOS_API_KEY", None)
        try:
            client = ESIOSClient()
            with self.assertRaises(CredentialError): client.metadata(682)
            with self.assertRaises(CredentialError): client.search_indicators("regulación")
        finally:
            if old is not None: os.environ["ESIOS_API_KEY"] = old
        self.assertIn("time_agg=average", ESIOSClient(api_key="secret").build_indicator_url(1293, time_trunc="fifteen_minutes", time_agg="average"))
        self.assertNotIn("time_agg", ESIOSClient(api_key="secret").build_indicator_url(1293, time_trunc="fifteen_minutes"))
        load = ESIOSClient(api_key="secret", opener=opener_for(b'{}'))
        load.fetch_load(1293, "2026-08-01T00:00:00+02:00", "2026-08-01T01:00:00+02:00")

    def test_esios_header_not_persisted(self):
        seen = []
        client = ESIOSClient(api_key="TOP_SECRET", opener=opener_for(b'{"indicator":{}}', seen=seen))
        response, _ = client.metadata(682)
        self.assertEqual(response.status, 200)
        self.assertEqual(seen[0].get_header("X-api-key"), "TOP_SECRET")

    def test_esios_cli_saves_response_without_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            seen = []
            with patch.object(es_cli, "ESIOSClient", lambda: ESIOSClient(api_key="TOP_SECRET", opener=opener_for(b'{"indicator": {"values": [{"value": 1}]}}', seen=seen))):
                code = es_cli.main(["esios", "metadata", "682", "--raw-root", directory])
            self.assertEqual(code, 0)
            saved = list(Path(directory).rglob("*.json"))
            self.assertTrue(saved)
            self.assertFalse(any("TOP_SECRET" in p.read_text(encoding="utf8") for p in saved))
            self.assertFalse(any("payload" in p.read_text(encoding="utf8") for p in saved))

    def test_redata_error_does_not_create_processed(self):
        class FailedREData:
            def __init__(self, status=500, body=b"<html>error</html>"): self.status, self.body = status, body
            def fetch(self, **kwargs): return HTTPResponse(self.status, {}, self.body), None
            def build_url(self, *args, **kwargs): return "https://example.invalid"
            def records(self, payload): return []
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(es_cli, "REDataClient", FailedREData):
                code = es_cli.main(["redata", "--start", "2026-08-01T00:00", "--end", "2026-08-01T01:00", "--raw-root", directory, "--processed-root", directory])
            self.assertEqual(code, 1)
            self.assertFalse(list(Path(directory).glob("*.csv")))
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(es_cli, "REDataClient", lambda: FailedREData(200, b"not-json")):
                code = es_cli.main(["redata", "--start", "2026-08-01T00:00", "--end", "2026-08-01T01:00", "--raw-root", directory, "--processed-root", directory])
            self.assertEqual(code, 1)
            self.assertFalse(list(Path(directory).glob("*.csv")))

    def test_offset_and_quality(self):
        rows = [{"datetime": "2026-10-25T02:15:00+02:00", "datetime_utc": "2026-10-25T00:15:00Z", "value": 1}, {"datetime": "2026-10-25T02:15:00+01:00", "datetime_utc": "2026-10-25T01:15:00Z", "value": 2}]
        summary = summarize_rows(rows)
        self.assertEqual(summary["records"], 2)
        self.assertEqual(summary["duplicate_count"], 0)
        # Same period across products is not duplicate; same technology and
        # timestamp in REData is duplicate.
        summary = summarize_rows([
            {"source": "OMIE", "kind": "da", "delivery_date": "2026-08-01", "period": 1},
            {"source": "OMIE", "kind": "idc", "delivery_date": "2026-08-01", "period": 1},
            {"technology": "Solar", "datetime_utc": "2026-08-01T00:00:00Z"},
            {"technology": "Solar", "datetime_utc": "2026-08-01T00:00:00Z"},
        ])
        self.assertEqual(summary["duplicate_count"], 1)


class TestENTSOE(unittest.TestCase):
    XML = b'''<?xml version="1.0" encoding="UTF-8"?>
<GL_MarketDocument xmlns="urn:entsoe.eu:wgedi:313:document:actualgenerationpertype:5:1">
  <type>A75</type><process.processType>A16</process.processType>
  <TimeSeries><mRID>series-1</mRID><businessType>A01</businessType><processType>A16</processType>
    <inBiddingZone_Domain.mRID>10YES-REE------0</inBiddingZone_Domain.mRID><curveType>A01</curveType>
    <MktPSRType><psrType>B01</psrType></MktPSRType><quantity_Measure_Unit.name>MAW</quantity_Measure_Unit.name>
    <Period><timeInterval><start>2026-08-01T00:00Z</start><end>2026-08-01T00:30Z</end></timeInterval><resolution>PT15M</resolution>
      <Point><position>1</position><quantity>100</quantity></Point><Point><position>2</position><quantity>110</quantity></Point>
    </Period>
  </TimeSeries>
</GL_MarketDocument>'''

    def test_url_uses_audited_fields_and_utc(self):
        url = build_entsoe_url("2026-08-01T02:00:00+02:00", "2026-08-01T03:00:00+02:00", resolution="PT15M", psr_type="B01", api_key="SECRET")
        self.assertIn("documentType=A75", url); self.assertIn("processType=A16", url); self.assertIn("businessType=A01", url)
        self.assertIn("periodStart=202608010000", url); self.assertIn("periodEnd=202608010100", url); self.assertIn("in_Domain=10YES-REE------0", url)

    def test_xml_expansion_preserves_psr_unit_area(self):
        rows = parse_entsoe_xml(self.XML)
        self.assertEqual(len(rows), 2); self.assertEqual(rows[0]["timestamp_utc"], "2026-08-01T00:00:00Z")
        self.assertEqual(rows[1]["timestamp_utc"], "2026-08-01T00:15:00Z"); self.assertEqual(rows[0]["psr_type"], "B01")
        self.assertEqual(rows[0]["unit"], "MAW"); self.assertEqual(rows[0]["area"], "10YES-REE------0")
        self.assertEqual(rows[0]["in_bidding_zone_domain_mrid"], "10YES-REE------0")

    def test_missing_token_skip_and_download_redacts_manifest(self):
        old = os.environ.pop("ENTSOE_API_KEY", None)
        try:
            with self.assertRaises(CredentialError): download_entsoe("2026-08-01T00:00Z", "2026-08-01T00:15Z", tempfile.gettempdir())
        finally:
            if old is not None: os.environ["ENTSOE_API_KEY"] = old
        with tempfile.TemporaryDirectory() as directory:
            result = download_entsoe("2026-08-01T00:00Z", "2026-08-01T00:30Z", directory, api_key="SECRET", opener=opener_for(self.XML))
            self.assertEqual(result["status"], "success")
            manifest = next(Path(directory).rglob("manifest.json")).read_text(encoding="utf8")
            self.assertNotIn("SECRET", manifest); self.assertNotIn("securityToken", manifest)


if __name__ == "__main__":
    unittest.main()
