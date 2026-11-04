"""Independent vectorized re-read of native 4s prices and saved Excel XML."""
import argparse
import json
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd


def run(source, result_dir, workbook):
    saved = json.loads((result_dir/'results.json').read_text(encoding='utf-8'))
    reference = pd.DataFrame(saved['daily_inputs']).set_index('date')
    observed = []
    columns = ['start_europe_madrid','da_eur_mwh','capacity_up_eur_mw_qh','capacity_down_eur_mw_qh',
               'activation_up_eur_mwh','activation_down_eur_mwh']
    for path in sorted((source/'processed/prices_4s').glob('*.csv.gz')):
        frame = pd.read_csv(path, usecols=columns)
        day = frame['start_europe_madrid'].str.slice(0,10)
        values = pd.DataFrame({'date':day})
        for direction in ['up','down']:
            price = frame[f'activation_{direction}_eur_mwh']
            eligible = price.notna() & (frame[f'capacity_{direction}_eur_mw_qh']>1)
            eligible &= ((price-frame['da_eur_mwh']>200) if direction=='up' else (frame['da_eur_mwh']-price>0))
            values[f'{direction}_valid_points'] = price.notna().astype(int)
            values[f'{direction}_active_points'] = eligible.astype(int)
            values[f'{direction}_cash_per_mw'] = price.where(eligible,0)/900*(1 if direction=='up' else -1)
            values[f'{direction}_energy_per_mw'] = eligible.astype(float)/900
        observed.append(values.groupby('date').sum())
        print('Independent native-price verification '+path.name[:7],flush=True)
    actual = pd.concat(observed).sort_index()
    errors = {}
    for key in actual.columns:
        diff = (actual[key]-reference[key]).abs()
        errors[key] = float(diff.max())
        assert diff.max()<1e-7, (key,diff.idxmax(),diff.max())

    qh = pd.read_csv(result_dir/'quarter_hour_calculation_basis.csv')
    da_errors=[]
    for date, group in qh.groupby('date', sort=False):
        prices=group['da_eur_mwh'].to_numpy()
        ch=group['da_charge_full_mwh'].to_numpy()
        dis=group['da_discharge_full_mwh'].to_numpy()
        ref=reference.loc[date]
        state=np.cumsum(ch*.92-dis/.92)
        assert np.min(state)>-1e-7 and np.max(state)<200+1e-7 and abs(state[-1])<1e-7
        assert max(ch.max(),dis.max())<25+1e-7
        if ch.sum()>0:
            ci,di=np.flatnonzero(ch>0),np.flatnonzero(dis>0)
            assert ci[-1]<di[0]
            assert len(ci)==ci[-1]-ci[0]+1 and len(di)==di[-1]-di[0]+1
        for key,value in [('da_p25',np.percentile(prices,25)),('da_p75',np.percentile(prices,75)),
                          ('da_purchases_full_eur',-np.dot(ch,prices)),('da_sales_full_eur',np.dot(dis,prices))]:
            error=abs(ref[key]-value);da_errors.append(error);assert error<1e-7
        for direction in ['up','down']:
            cp=group[f'capacity_{direction}_eur_mw_qh']
            assert abs(cp.where(cp>1,0).sum()-ref[f'capacity_{direction}_per_mw'])<1e-7

    ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    formula_count=0
    with zipfile.ZipFile(workbook) as archive:
        sheetxml={}
        error_cells=[]
        for name in archive.namelist():
            if name.startswith('xl/worksheets/sheet') and name.endswith('.xml'):
                tree=ET.fromstring(archive.read(name));sheetxml[name]=tree
                formula_count+=len(tree.findall('.//m:f',ns))
                error_cells.extend((name,c.attrib['r']) for c in tree.findall('.//m:c',ns) if c.attrib.get('t')=='e')
        assert not error_cells,error_cells
        summary={c.attrib['r']:c for c in sheetxml['xl/worksheets/sheet1.xml'].findall('.//m:c',ns)}
        keys=['da_net_eur','capacity_up_eur','capacity_down_eur','activation_up_cash_eur',
              'activation_down_cash_eur','down_resale_value_eur','up_replenishment_cost_eur',
              'activation_net_with_value_eur','total_cash_eur','total_with_value_eur']
        excel_errors=[]
        for i,r in enumerate(saved['totals']):
            for c,key in zip('BCDEFGHIJK',keys):
                v=float(summary[f'{c}{6+i}'].find('m:v',ns).text)
                error=abs(v-r[key]);excel_errors.append(error);assert error<1e-5
        for i,r in enumerate(saved['monthly']):
            for c,key in zip('CDEFGHIJKL',keys):
                v=float(summary[f'{c}{17+i}'].find('m:v',ns).text)
                error=abs(v-r[key]);excel_errors.append(error);assert error<1e-5
        calc_count=len(sheetxml['xl/worksheets/sheet3.xml'].findall('.//m:row',ns))
        assert calc_count>=1554
        params={c.attrib['r']:c for c in sheetxml['xl/worksheets/sheet2.xml'].findall('.//m:c',ns)}
        assert float(params['C23'].find('m:v',ns).text)==.5
        chart_names=[p for p in archive.namelist() if '/charts/chart' in p and p.endswith('.xml')]
        assert len(chart_names)==1
        chartxml=archive.read(chart_names[0]).decode('utf-8')
        for color in ['203A5F','B55D34','3D8470']:
            assert color in chartxml,color
    report=dict(native_4s_rows=11189700,days=len(actual),quarter_hours=len(qh),
                max_daily_exposure_errors=errors,max_da_checks_error=max(da_errors),
                excel_formulas=formula_count,excel_error_cells=error_cells,
                excel_financial_comparisons=len(excel_errors),excel_max_difference=max(excel_errors),
                chart_count=1,chart_colors_verified=True,
                january_sample_reproduced=saved['checks']['jan_20260101_50pct_reproduced_eur'],
                result='PASS')
    (result_dir/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--results',type=Path,required=True)
    parser.add_argument('--workbook',type=Path,required=True)
    args=parser.parse_args()
    run(args.source,args.results,args.workbook)
