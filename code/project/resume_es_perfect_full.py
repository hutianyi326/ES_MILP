"""Resume the audited full run; retry infeasible numerical solves with presolve only."""
import json,sys,gc,shutil
import scipy.optimize
from pathlib import Path
from datetime import datetime,timezone
from dataclasses import replace
from time import perf_counter
CODE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(CODE))
from project.run_es_full_ts_start_cap_old_d_20260921 import input_from_saved_configuration
from src.es_synthetic_market.perfect import PerfectEngine
from src.es_synthetic_market import _baseline_core
ROOT=CODE.parent;SOURCE=ROOT/'output/perfect_v1_full_20260922';OUT=ROOT/'output/perfect_v1_full_completed_retry'
started=perf_counter();OUT.mkdir(exist_ok=False)
def save(name,obj,pretty=False):
    with (OUT/name).open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,default=str,allow_nan=False,indent=2 if pretty else None)
save('process_start.json',dict(start_utc=datetime.now(timezone.utc).isoformat(),scope='resume_process'))
for name in ('solver_input.json','input_evidence.json','manifest.json'):shutil.copy2(SOURCE/name,OUT/name)
inp=input_from_saved_configuration(json.loads((OUT/'solver_input.json').read_text(encoding='utf-8')))
evidence=json.loads((OUT/'input_evidence.json').read_text(encoding='utf-8'))
for row in evidence['rows']:row['raw_values']={int(k):v for k,v in row['raw_values'].items()}
manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
cp=json.loads((SOURCE/'final_checkpoint.json').read_text(encoding='utf-8'))
engine=PerfectEngine.restore(inp,cp,execution_end=datetime.fromisoformat(manifest['formal_end']),
    inactive=[r['qh_id'] for r in evidence['rows'] if not r['valid']],evidence=evidence,budget_manifest=manifest['budgets'],
    run_id='ES_HISTORICAL_CONDITIONAL_PERFECT_V1',history_mode='delta',time_limit_seconds=30.)
save('resume_provenance.json',dict(source=str(SOURCE),checkpoint_hash=cp['state_hash'],committed_windows=len(engine._windows),
    original_failure=engine.failure,retry_policy='status 2 only: same inputs/constraints/budget, presolve=True',core_unchanged=True))
del cp;gc.collect();engine.failure=None
calls=[];original_milp=scipy.optimize.milp
def timed(*args,**kwargs):
    t=perf_counter();r=original_milp(*args,**kwargs)
    calls.append(dict(seconds=perf_counter()-t,status=int(r.status),presolve=kwargs['options']['presolve']))
    return r
scipy.optimize.milp=timed
original=engine._solve_window;retries=[]
def checked(win,order_mode,**options):
    first=len(calls);result=original(win,order_mode,**options)
    if not result.feasible and result.status==2 and not options['presolve']:
        reason=result.message
        result=original(win,order_mode,**{**options,'presolve':True})
        record=dict(start=str(win.qhs[0].start_utc),first_message=reason,retry_feasible=result.feasible,retry_message=result.message,calls=calls[first:])
        retries.append(record);print(json.dumps(dict(retry=record)),flush=True)
        with (OUT/'retry_events.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(record)+'\n')
    if result.feasible:
        result=replace(result,residuals={**result.residuals,'solver_seconds':sum(c['seconds'] for c in calls[first:]),'presolve_retry':int(len(calls)-first>1)})
    return result
engine._solve_window=checked
solve_started=perf_counter()
while engine.step():
    w=engine._windows[-1]
    print(json.dumps(dict(window=len(engine._windows),start=w.start_utc,soc=engine._soc,solver_seconds=w.audit['model']['solver_seconds'],elapsed=perf_counter()-started)),flush=True)
report=engine.report();prior=json.loads((SOURCE/'summary.json').read_text(encoding='utf-8'))
report['execution_wall_seconds']=prior['execution_wall_seconds']+perf_counter()-solve_started
report['total_wall_seconds']=prior['total_wall_seconds']+perf_counter()-started
report['retry_events']=retries
save('result.json',report,True)
save('cash_ledger.json',engine._ledger.snapshot())
save('final_checkpoint.json',engine.checkpoint())
save('frozen_ledger.json',[r for w in engine._windows for r in w.audit['frozen_delta']])
summary={k:report[k] for k in ('mode','success','failure','annual_budget','annual_used','coverage','quality','solver_seconds','execution_wall_seconds','total_wall_seconds','months')}
summary['retry_count']=len(retries);summary['resume_wall_including_saves_seconds']=perf_counter()-started
save('summary.json',summary,True);save('solver_calls_resumed.json',calls,True)
print(json.dumps(summary,ensure_ascii=False),flush=True)
