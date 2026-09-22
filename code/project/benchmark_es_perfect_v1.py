"""Compare legacy two-day/v5 EFC policy against a completed P0 sample.

This is a boundary-policy comparison, not a claim of identical feasible sets.
The formal-day input and budget are taken from the P0 sample without its tail.
"""
import argparse
from dataclasses import replace
from datetime import datetime
import json
from pathlib import Path
import sys
from time import perf_counter
from unittest.mock import patch

CODE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(CODE))
from project.run_es_full_ts_start_cap_old_d_20260921 import input_from_saved_configuration,apply_terminal_efc_reserve
from src.es_synthetic_market.rolling import RollingEngine
from src.es_synthetic_market import _baseline_core

class V5SampleEngine(RollingEngine):
    def _window_input(self,qhs,start,end):
        win,fr,rr,remaining=super()._window_input(qhs,start,end,
            soc_override=min(self.inp.e_max_mwh,max(self.inp.e_min_mwh,self._soc)))
        segment=self._segment_rows[qhs[0].segment_id]
        reserve=(self.inp.e_max_mwh-self.inp.e_terminal_mwh)/(self.inp.eta_discharge*self.inp.cycle_denominator_mwh)
        remaining,_=apply_terminal_efc_reserve(remaining,terminal_year=segment[-1].madrid_year,
            planning_reaches_segment_end=qhs[-1].end_utc==segment[-1].end_utc,reserve_efc=reserve)
        return win,fr,rr,{y:max(0.,v-1e-6) for y,v in remaining.items()}

def main():
    p=argparse.ArgumentParser();p.add_argument('--sample',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();new=json.loads((a.sample/'summary.json').read_text(encoding='utf-8'))
    manifest=json.loads((a.sample/'manifest.json').read_text(encoding='utf-8'));end=datetime.fromisoformat(manifest['formal_end'])
    inp=input_from_saved_configuration(json.loads((a.sample/'solver_input.json').read_text(encoding='utf-8')))
    qs=tuple(q for q in inp.qhs if q.end_utc<=end);ids={q.qh_id for q in qs}
    if any(not r['valid'] for r in json.loads((a.sample/'input_evidence.json').read_text(encoding='utf-8'))['rows'] if datetime.fromisoformat(r['qh_id'])<end):
        raise ValueError('comparison requires complete formal input; legacy gap semantics differ')
    inp=replace(inp,qhs=qs,contracts=tuple(c for c in inp.contracts if set(c.qh_weights)<=ids),
        annual_efc_budget={y:v for y,v in inp.annual_efc_budget.items() if y in {q.madrid_year for q in qs}})
    solver_times=[];original=_baseline_core.solve_joint;canonical=_baseline_core._canonical_trade_mw
    def timed(*args,**kwargs):
        r=original(*args,**kwargs);solver_times.append(r.residuals.get('solver_seconds',0.));return r
    def bounded(x):return canonical(min(100.,max(0.,x)) if -1e-5<=x<=100+1e-5 else x)
    engine=V5SampleEngine(inp,run_id='ES_HISTORICAL_CONDITIONAL_LEGACY_8D',order_mode='D',history_mode='delta',time_limit_seconds=30)
    start=perf_counter()
    with patch.object(_baseline_core,'solve_joint',timed),patch.object(_baseline_core,'_canonical_trade_mw',bounded):result=engine.run()
    wall=perf_counter()-start
    payload=dict(label='same_formal_input_budget_different_boundary_and_GCT_policy',formal_qh=len(qs),
        legacy=dict(success=result.success,failure=result.failure,cash_eur=result.execution_cash_eur,solver_seconds=sum(solver_times),wall_seconds=wall),
        perfect=new,limitations=['single run, not repeated performance distribution',
            'P0 has extra tail, GCT headroom and T terminal; legacy truncates final planning window',
            'same prepared initial closed markets and formal budget; not archived full-range result'])
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload,ensure_ascii=False))

if __name__=='__main__':main()
