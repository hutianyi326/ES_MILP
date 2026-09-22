"""Run P0 ts_start/cap_old/D with nullable input evidence and one tail day.

Example: --start 2025-01-01 --end 2025-01-09 (end exclusive).
No API calls, no previous-day input requirement, no overwrite of existing output.
"""
import argparse
from dataclasses import asdict
from datetime import datetime,timedelta
import json
from pathlib import Path
import sys
from time import perf_counter

CODE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(CODE))
from src.es_historical_conditional.adapter import load_raw,MADRID,digest
from src.es_historical_conditional.perfect import prepare
from src.es_synthetic_market.perfect import PerfectEngine


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--start',required=True,help='first formal local date')
    p.add_argument('--end',required=True,help='formal end local date, exclusive')
    p.add_argument('--input',type=Path,default=CODE.parent/'input')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--budget-json',type=Path,help='explicit formal year:value map; not tail budgets')
    p.add_argument('--time-limit',type=float,default=30.)
    p.add_argument('--preflight-only',action='store_true')
    args=p.parse_args()
    start=datetime.fromisoformat(args.start).replace(tzinfo=MADRID)
    end=datetime.fromisoformat(args.end).replace(tzinfo=MADRID)
    if start>=end:p.error('end must follow start')
    args.output.mkdir(parents=True,exist_ok=False)
    def save(name,obj):
        with (args.output/name).open('x',encoding='utf-8') as f:
            json.dump(obj,f,ensure_ascii=False,default=str,allow_nan=False,indent=2)
    started=perf_counter()
    bundle=load_raw(args.input,start,end+timedelta(days=1))
    explicit=None
    if args.budget_json:
        explicit={int(k):float(v) for k,v in json.loads(args.budget_json.read_text(encoding='utf-8')).items()}
    if explicit is None and args.start=='2025-01-01' and args.end=='2026-09-01':
        archived=CODE.parent/'output/full_range/final_report.json'
        if not archived.exists():
            raise ValueError('v5 comparison requires archived annual budgets or --budget-json')
        explicit={int(k):float(v) for k,v in json.loads(archived.read_text(encoding='utf-8'))['annual_efc_budget'].items()}
    inp,mask,evidence,budgets=prepare(bundle,end,formal_budget=explicit,
        budget_source=('explicit:'+digest(explicit)) if explicit is not None else 'formal_valid_mask')
    save('input_evidence.json',evidence)
    save('solver_input.json',asdict(inp))
    save('manifest.json',dict(mode='perfect_history_v1',scenario='ts_start/cap_old/D',
        formal_start=start,formal_end=end,input_end=end+timedelta(days=1),budgets=budgets,
        input_hash=digest(asdict(inp)),source_files=bundle.sources,rejected=bundle.rejected,
        code_hashes={str(f.relative_to(CODE)):__import__('hashlib').sha256(f.read_bytes()).hexdigest()
                     for folder in ('src/es_synthetic_market','src/es_historical_conditional') for f in (CODE/folder).glob('*.py')},
        preparation_seconds=perf_counter()-started))
    if args.preflight_only:
        print(json.dumps(dict(status='preflight_complete',qh=len(inp.qhs),gaps=len(mask),budgets=budgets),default=str))
        return
    engine=PerfectEngine(inp,execution_end=end,inactive=mask,evidence=evidence,budget_manifest=budgets,
        run_id='ES_HISTORICAL_CONDITIONAL_PERFECT_V1',history_mode='delta',time_limit_seconds=args.time_limit)
    solve_started=perf_counter()
    # Each successful commit can be resumed with PerfectEngine.restore; no failed candidate is written as a committed state.
    while engine.step():
        save(f'checkpoint_{len(engine._windows):04d}.json',engine.checkpoint())
    report=engine.report();report['execution_wall_seconds']=perf_counter()-solve_started
    report['total_wall_seconds']=perf_counter()-started
    save('result.json',report)
    save('cash_ledger.json',engine._ledger.snapshot())
    save('final_checkpoint.json',engine.checkpoint())
    frozen=[r for w in engine._windows for r in w.audit['frozen_delta']]
    save('frozen_ledger.json',frozen)
    summary={k:report[k] for k in ('mode','success','failure','annual_budget','annual_used','coverage','quality',
                                 'solver_seconds','execution_wall_seconds','total_wall_seconds','months')}
    save('summary.json',summary)
    print(json.dumps(summary,ensure_ascii=False))

if __name__=='__main__':main()
