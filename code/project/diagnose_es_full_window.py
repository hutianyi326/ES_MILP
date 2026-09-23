"""Reproduce failed full-range window from an immutable checkpoint."""
import json,sys,gc
from pathlib import Path
from datetime import datetime
from dataclasses import asdict
CODE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(CODE))
from project.run_es_full_ts_start_cap_old_d_20260921 import input_from_saved_configuration
from src.es_synthetic_market.perfect import PerfectEngine
from src.es_synthetic_market.core import solve_joint
ROOT=CODE.parent;RUN=ROOT/'output/perfect_v1_full_20260922';OUT=ROOT/'output/perfect_v1_full_diagnostic'
OUT.mkdir(exist_ok=True)
inp=input_from_saved_configuration(json.loads((RUN/'solver_input.json').read_text(encoding='utf-8')))
evidence=json.loads((RUN/'input_evidence.json').read_text(encoding='utf-8'))
for row in evidence['rows']:row['raw_values']={int(k):v for k,v in row['raw_values'].items()}
manifest=json.loads((RUN/'manifest.json').read_text(encoding='utf-8'))
cp=json.loads((RUN/'checkpoint_0300.json').read_text(encoding='utf-8'))
engine=PerfectEngine.restore(inp,cp,execution_end=datetime.fromisoformat(manifest['formal_end']),
    inactive=[r['qh_id'] for r in evidence['rows'] if not r['valid']],evidence=evidence,budget_manifest=manifest['budgets'],
    run_id='ES_HISTORICAL_CONDITIONAL_PERFECT_V1',history_mode='delta',time_limit_seconds=30.)
del cp;gc.collect()
original=engine._solve_window
def checked(win,order_mode,**options):
    result=original(win,order_mode,**options)
    if not result.feasible:
        payload=dict(window=asdict(win),options=options,start=str(win.qhs[0].start_utc),used=engine._used,soc=engine._soc)
        (OUT/'failed_window.json').write_text(json.dumps(payload,default=str,indent=2),encoding='utf-8')
        for name,changes in [('presolve',dict(presolve=True)),('loose_budget',dict(remaining_annual_efc={y:v+1e-5 for y,v in options['remaining_annual_efc'].items()}))]:
            alt=solve_joint(win,order_mode,**{**options,**changes})
            print(name,alt.feasible,alt.message,dict(alt.residuals),flush=True)
    return result
engine._solve_window=checked
while engine.step():print(len(engine._windows),engine._soc,engine._used,flush=True)
print('FAILED',engine.failure,flush=True)
