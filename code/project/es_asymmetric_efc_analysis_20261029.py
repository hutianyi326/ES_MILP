"""Export monthly actual EFC and first dates exceeding 99% of annual budgets."""
import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from build_es_result_presentation import _read_rows

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/asymmetric_50_100_20261029'
RUNS={'baseline_100_100':'capacity_award_rate_full_accelerated_20260923',
      'asymmetric_cap100':'asymmetric_50_100_cap100_resume_20261029',
      'asymmetric_cap150':'asymmetric_50_100_cap150_resume_20261029'}
TZ=ZoneInfo('Europe/Madrid')

def main():
    data={}; dates={}
    for name,folder in RUNS.items():
        run=ROOT/'output'/folder
        summary=json.loads((run/'summary.json').read_text(encoding='utf-8'))
        if not summary['success']: raise ValueError(f'unsuccessful run {name}')
        budgets={int(y):v for y,v in summary['annual_budget'].items()}
        used=defaultdict(float); monthly=defaultdict(float); dates[name]={}
        for row in _read_rows(run/'result.json'):
            t=datetime.fromisoformat(row['time']).astimezone(TZ)
            if t.year not in budgets: continue
            value=float(row.get('efc') or 0)
            used[t.year]+=value; monthly[t.strftime('%Y-%m')]+=value
            if used[t.year]>=0.99*budgets[t.year] and str(t.year) not in dates[name]:
                dates[name][str(t.year)]=t.isoformat()
        for year,total in used.items():
            if abs(total-summary['annual_used'][str(year)])>1e-5:
                raise ValueError(f'EFC total does not reconcile {name} {year}')
        data[name]=monthly
    with (OUT/'monthly_efc.csv').open('x',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['month',*RUNS])
        for month in sorted(set().union(*(set(v) for v in data.values()))):
            writer.writerow([month,*(data[n].get(month,0) for n in RUNS)])
    (OUT/'efc_99_percent_dates.json').write_text(json.dumps(dates,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dates,ensure_ascii=False))

if __name__=='__main__':main()
