"""Read-only checks of the committed simple-model examples and result snapshots."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import posixpath
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[2]
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL='http://schemas.openxmlformats.org/officeDocument/2006/relationships'


def excel(path):
    with zipfile.ZipFile(path) as z:
        rels={r.attrib['Id']:r.attrib['Target'] for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        result={};errors=[];formulas=0
        for sh in ET.fromstring(z.read('xl/workbook.xml')).findall('s:sheets/s:sheet',NS):
            target=rels[sh.attrib['{'+REL+'}id']]
            part=target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join('xl',target))
            tree=ET.fromstring(z.read(part));values={}
            for c in tree.findall('.//s:c',NS):
                if c.attrib.get('t')=='e':errors.append((sh.attrib['name'],c.attrib['r']))
                f=c.find('s:f',NS);v=c.find('s:v',NS)
                formulas+=f is not None
                if v is not None and c.attrib.get('t','n')=='n':values[c.attrib['r']]=float(v.text)
            result[sh.attrib['name']]=values
        assert not errors,errors
        return result,formulas


def validate(release):
    manifest=json.loads((release/'delivery_manifest.json').read_text(encoding='utf-8'))
    for item in manifest:
        path=ROOT/item['path'];body=path.read_bytes()
        assert len(body)==item['bytes'] and hashlib.sha256(body).hexdigest()==item['sha256'],item['path']
    saved=json.loads((release/'benchmark_results.json').read_text(encoding='utf-8'))
    rows=list(csv.DictReader((release/'monthly_three_strategies.csv').open(encoding='utf-8-sig',newline='')))
    assert len(rows)==51
    comparisons=0
    for total in saved['symmetric_totals']:
        group=[r for r in rows if r['scenario']==total['scenario']]
        assert len(group)==17
        for key,value in total.items():
            if key.endswith('_eur'):
                assert abs(math.fsum(float(r[key]) for r in group)-value)<1e-5,key
                comparisons+=1
    asym=list(csv.DictReader((release/'monthly_asymmetric_80pct.csv').open(encoding='utf-8-sig',newline='')))
    assert len(asym)==17
    for key,value in saved['asymmetric_totals'].items():
        assert abs(math.fsum(float(r[key]) for r in asym)-value)<1e-5,key
        comparisons+=1
    monthly,monthly_formulas=excel(release/'artifacts/monthly_strategies_with_asymmetric.xlsx')
    assert abs(monthly['充50放100_80%现货']['M26']-saved['asymmetric_totals']['total_with_value_eur'])<1e-5
    assert abs(monthly['80%现货月度收益']['M24']-saved['symmetric_totals'][2]['total_with_value_eur'])<1e-5
    for i,total in enumerate(saved['symmetric_totals']):
        assert abs(monthly['月度收益'][f'K{6+i}']-total['total_with_value_eur'])<1e-5
    single,single_formulas=excel(release/'artifacts/sample_20260101_4s.xlsx')
    # Preserve the current saved allocation; the baseline was 50%, the saved sample is 80%.
    p=single['参数'];reference=saved['single_day_reference'];base=reference['configuration']['da_share'];share=p['B8']
    for cell,value in [('B6',100),('B7',200),('B10',.92),('B11',.92),('B16',1),('B17',1),('B18',200),('B19',0)]:
        assert abs(p[cell]-value)<1e-10,(cell,p[cell])
    expected=reference['da_profit_eur']*share/base+(reference['total_eur']-reference['da_profit_eur'])*(1-share)/(1-base)
    assert abs(single['汇总']['B17']-expected)<1e-5
    metrics=list(csv.DictReader((release/'monthly_asymmetric_da_metrics.csv').open(encoding='utf-8-sig',newline='')))
    assert len(metrics)==17
    assert abs(math.fsum(float(r['da_efc_160mwh']) for r in metrics)-517.94)<1e-8
    assert abs(math.fsum(float(r['project_efc_200mwh']) for r in metrics)-414.352)<1e-8
    report=dict(result='PASS',manifest_files_verified=len(manifest),monthly_financial_comparisons=comparisons,
        monthly_csv_rows=len(rows)+len(asym),monthly_workbook_sheets=list(monthly),
        monthly_workbook_formulas=monthly_formulas,sample_workbook_formulas=single_formulas,
        workbook_errors=0,da_metrics_months=len(metrics),sample_saved_da_share=share,sample_saved_total_eur=single['汇总']['B17'])
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__)
    p.add_argument('--release-dir',type=Path,default=ROOT/'reports/simple_model_release_20261104')
    p.add_argument('--write-report',action='store_true')
    a=p.parse_args();report=validate(a.release_dir)
    if a.write_report:
        with (a.release_dir/'release_checks.json').open('w',encoding='utf-8',newline='\n') as f:
            json.dump(report,f,ensure_ascii=False,indent=2)
    print(json.dumps(report,ensure_ascii=False,indent=2))
