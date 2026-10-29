"""Compare three completed historical rolling runs on their common valid QHs."""
import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from build_es_result_presentation import _read_rows, _top_level_scalars

ROOT = Path(__file__).resolve().parents[2]
RUNS = {
    'baseline_100_100': ROOT/'output/capacity_award_rate_full_accelerated_20260923',
    'asymmetric_cap100': ROOT/'output/asymmetric_50_100_cap100_resume_20261029',
    'asymmetric_cap150': ROOT/'output/asymmetric_50_100_cap150_resume_20261029',
}
OUT = ROOT/'reports/asymmetric_50_100_20261029'
KEYS = ('DA','ID','cap_up','cap_down','act_up','act_down')
FIELDS = {'charge_mw','discharge_mw','grid_import_mw','grid_export_mw','e_min_mwh',
          'e_max_mwh','e_initial_mwh','e_terminal_mwh','eta_charge','eta_discharge',
          'reserve_limit_up_mw','reserve_limit_down_mw'}
TZ = ZoneInfo('Europe/Madrid')


def file_hash(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    inputs, summaries, rows, manifests = {}, {}, {}, {}
    for name, path in RUNS.items():
        summaries[name] = json.loads((path/'summary.json').read_text(encoding='utf-8'))
        manifests[name] = json.loads((path/'manifest.json').read_text(encoding='utf-8'))
        if not summaries[name]['success'] or summaries[name]['failure']:
            raise ValueError(f'run did not complete successfully: {name}')
        inputs[name] = _top_level_scalars(path/'solver_input.json', FIELDS)
        items = _read_rows(path/'result.json')
        rows[name] = {row['qh_id']: row for row in items if row['cash'] is not None}
        if len(rows[name]) != len([r for r in items if r['cash'] is not None]):
            raise ValueError(f'duplicate valid QH: {name}')
        if len(rows[name]) != sum(m['valid_qh'] for m in summaries[name]['months'].values()):
            raise ValueError(f'valid QH count mismatch: {name}')
    for name in RUNS:
        if summaries[name]['annual_budget'] != summaries['baseline_100_100']['annual_budget']:
            raise ValueError('budget mismatch')
        for key in ('formal_start','formal_end','input_end'):
            if manifests[name][key] != manifests['baseline_100_100'][key]:
                raise ValueError(f'time range mismatch: {name}: {key}')
        if manifests[name]['award_rate_source']['sha256'] != manifests['baseline_100_100']['award_rate_source']['sha256']:
            raise ValueError('award rate input mismatch')
        for key in FIELDS-{'charge_mw','grid_import_mw','reserve_limit_up_mw','reserve_limit_down_mw'}:
            if inputs[name][key] != inputs['baseline_100_100'][key]:
                raise ValueError(f'common configuration mismatch: {name}: {key}')
    for name, charge, grid, reserve in (('baseline_100_100',100,100,100),
                                       ('asymmetric_cap100',50,50,100),
                                       ('asymmetric_cap150',50,50,150)):
        config=inputs[name]
        assert (config['charge_mw'],config['grid_import_mw'],config['reserve_limit_up_mw'],
                config['reserve_limit_down_mw']) == (charge,grid,reserve,reserve)
    common=set.intersection(*(set(v) for v in rows.values()))
    evidence_hashes={name:file_hash(path/'input_evidence.json')
                     for name,path in RUNS.items()}
    if len(set(evidence_hashes.values())) != 1:
        raise ValueError('historical input evidence differs')
    allsets={n:len(v) for n,v in rows.items()}
    monthly=defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    counts=defaultdict(int)
    for q in sorted(common):
        month=datetime.fromisoformat(rows['baseline_100_100'][q]['time']).astimezone(TZ).strftime('%Y-%m')
        counts[month]+=1
        for name in RUNS:
            for key in KEYS:
                monthly[month][name][key]+=float(rows[name][q]['cash'][key])/100000
    OUT.mkdir(parents=True,exist_ok=False)
    with (OUT/'monthly_common_qh.csv').open('x',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f); writer.writerow(['month','valid_qh','scenario',*KEYS,'total_keur_per_mw'])
        for month in sorted(monthly):
            for name in RUNS:
                vals=[monthly[month][name][k] for k in KEYS]
                writer.writerow([month,counts[month],name,*vals,sum(vals)])
    totals={name:{k:sum(monthly[m][name][k] for m in monthly) for k in KEYS} for name in RUNS}
    for name in RUNS:
        if set(rows[name]) == common:
            summary_total=sum(sum(m['cash_eur'].values()) for m in summaries[name]['months'].values() if m['cash_eur'])/100000
            if abs(sum(totals[name].values())-summary_total) > 1e-7:
                raise ValueError(f'cash total mismatch: {name}')
    evidence={'inputs':inputs,'valid_qh_by_run':allsets,'common_valid_qh':len(common),
              'all_valid_sets_equal':all(set(v)==common for v in rows.values()),
              'common_cash_keur_per_mw':totals,
              'input_evidence_sha256':evidence_hashes,
              'budget':summaries['baseline_100_100']['annual_budget'],
              'annual_used':{n:summaries[n]['annual_used'] for n in RUNS},
              'solver_seconds':{n:summaries[n]['solver_seconds'] for n in RUNS},
              'total_wall_seconds':{n:summaries[n]['total_wall_seconds'] for n in RUNS},
              'run_directories':{n:str(p) for n,p in RUNS.items()},
              'award_sources':{n:manifests[n].get('award_rate_source') for n in RUNS}}
    (OUT/'comparison_evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(evidence,ensure_ascii=False,indent=2))

if __name__ == '__main__': main()
