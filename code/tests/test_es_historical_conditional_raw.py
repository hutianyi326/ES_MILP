import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime,date,timedelta
import unittest
from src.es_historical_conditional.adapter import load_raw,MADRID,save_new,dependency_hashes
from src.es_historical_conditional.__main__ import validate_request

class RawTests(unittest.TestCase):
    def test_metadata_accept_and_fail_closed(self):
        for defect in (None,'http','sha','unit','direction','resolution'):
            with self.subTest(defect=defect),TemporaryDirectory() as tmp:
                root=Path(tmp);p=root/'data/raw/ES/esios/test/fetch_632.json';p.parent.mkdir(parents=True)
                payload={'indicator':{'id':632,'name':'Asignación reserva a '+('bajar' if defect=='direction' else 'subir'),
                    'magnitud':[{'name':'bad' if defect=='unit' else 'Potencia'}],
                    'tiempo':[{'id':4 if defect=='resolution' else 218}],
                    'values':[{'datetime_utc':'2024-12-31T23:00:00Z','geo_id':8741,'geo_name':'Península','value':100}]}}
                raw=json.dumps(payload).encode();p.write_bytes(raw)
                meta={'http_status':500 if defect=='http' else 200,'sha256':'bad' if defect=='sha' else hashlib.sha256(raw).hexdigest()}
                p.with_suffix('.json.meta.json').write_text(json.dumps(meta),encoding='utf-8')
                b=load_raw(root,datetime(2025,1,1,tzinfo=MADRID),datetime(2025,1,2,tzinfo=MADRID))
                self.assertEqual(bool(b.values[632]),defect is None)
                self.assertEqual(p.read_bytes(),raw)

    def test_cli_authorized_bounds_and_output_protection(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);out=(root/'outputs/es_historical_conditional/v1').resolve()
            validate_request(date(2025,1,1),date(2026,9,1),out,root)
            for a,b in [(date(2024,12,31),date(2025,1,2)),(date(2025,1,1),date(2026,9,2)),(date(2025,1,1),date(2025,1,1))]:
                with self.assertRaises(ValueError):validate_request(a,b,out,root)
            with self.assertRaises(ValueError):validate_request(date(2025,1,1),date(2025,1,2),root,root)
            out.mkdir(parents=True)
            with self.assertRaises(FileExistsError):validate_request(date(2025,1,1),date(2025,1,2),out,root)
            save_new(out/'x.json',{'value':1})
            with self.assertRaises(FileExistsError):save_new(out/'x.json',{'value':2})
            self.assertEqual(json.loads((out/'x.json').read_text())['value'],1)

    def test_dependency_fingerprints_include_parsers(self):
        h=dependency_hashes()
        for p in ('countries/ES/audit_pi_candidate_20260920.py','project/es_joint_gate_audit_20260920.py','src/data_ingestion/es/omie.py'):
            self.assertIn(p,h);self.assertEqual(len(h[p]),64)

if __name__=='__main__':unittest.main()
