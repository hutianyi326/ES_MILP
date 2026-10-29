"""Run the three authorized daily-only EFC scenarios with immutable outputs."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
SCENARIOS={'baseline_100_100':(100,100),'asymmetric_cap100':(50,100),'asymmetric_cap150':(50,150)}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--start',default='2026-01-01')
    p.add_argument('--end',default='2026-09-01')
    p.add_argument('--workers',type=int,default=3)
    args=p.parse_args()
    base=args.output.resolve();base.mkdir(parents=True,exist_ok=False)
    def run(name,powers):
        charge,reserve=powers
        prep=base/(name+'_input');out=base/name
        command=[sys.executable,str(ROOT/'code/project/run_es_perfect_v1.py'),
            '--start',args.start,'--end',args.end,'--output',str(prep),'--preflight-only',
            '--daily-efc-limit','2','--capacity-award-mode','optimize',
            '--award-rate-file',str(ROOT/'input/processed/ES/afrr_capacity_award_rate_202501_202608.csv.gz'),
            '--charge-mw',str(charge),'--grid-import-mw',str(charge),
            '--discharge-mw','100','--grid-export-mw','100',
            '--reserve-limit-up-mw',str(reserve),'--reserve-limit-down-mw',str(reserve)]
        with (base/(name+'.log')).open('x',encoding='utf-8') as log:
            subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
            subprocess.run([sys.executable,str(ROOT/'code/project/resume_es_capacity_award_rate.py'),
                '--source',str(prep),'--output',str(out),'--fresh','--checkpoint-every','30'],
                cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
        summary=json.loads((out/'summary.json').read_text(encoding='utf-8'))
        if not summary['success']:raise RuntimeError(f'{name}: {summary["failure"]}')
        print(json.dumps(dict(scenario=name,success=True,annual_used=summary['annual_used']),ensure_ascii=False),flush=True)
        return name
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(lambda item:run(*item),SCENARIOS.items()))


if __name__=='__main__':main()
