"""Run P0 ts_start/cap_old/D with nullable input evidence and one tail day.

Example: --start 2025-01-01 --end 2025-01-09 (end exclusive).
No API calls, no previous-day input requirement, no overwrite of existing output.
"""
import argparse
from dataclasses import asdict,replace
from datetime import datetime,timedelta
import json
from pathlib import Path
import sys
from time import perf_counter

CODE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(CODE))
from src.es_historical_conditional.adapter import load_raw,MADRID,digest
from src.es_historical_conditional.perfect import prepare,load_award_rates
from src.es_synthetic_market.perfect import PerfectEngine


def apply_posthoc_capacity_rates(report, ledger, award_rates, discharge_mw):
    """Apply award-rate proxies to capacity cash only, leaving all decisions intact."""
    if any(entry.get('sensitivity_cash_label')=='posthoc_capacity_revenue_proxy'
           for entry in ledger if entry['settlement_type']=='aFRR_capacity'):
        raise ValueError('post-hoc capacity rates have already been applied to this ledger')
    capacity_cash={}
    for entry in ledger:
        if entry['settlement_type']!='aFRR_capacity':
            continue
        key=(entry['object_id'],entry['direction'])
        observation=award_rates.get(key)
        quantity=float(entry['quantity'])
        if observation is None or observation['rate'] is None:
            if abs(quantity)>1e-8:
                raise ValueError(f'nonzero capacity position lacks a valid post-hoc rate: {key}')
            rate=0.0
        else:
            rate=float(observation['rate'])
        raw_cash=float(entry['cash_eur'])
        raw_price=float(entry['unit_price_eur'])
        entry['unadjusted_cash_eur']=raw_cash
        entry['full_fill_unit_price_eur']=raw_price
        entry['award_rate_proxy']=observation['rate'] if observation else None
        entry['cash_eur']=raw_cash*rate
        entry['unit_price_eur']=raw_price*rate
        entry['sensitivity_cash_label']='posthoc_capacity_revenue_proxy'
        capacity_cash.setdefault(entry['object_id'],{})['cap_'+entry['direction']]=entry['cash_eur']

    for row in report['rows']:
        if row['cash'] is None:
            continue
        row['cash']['cap_up']=capacity_cash.get(row['qh_id'],{}).get('cap_up',0.0)
        row['cash']['cap_down']=capacity_cash.get(row['qh_id'],{}).get('cap_down',0.0)
    months={key:{k:0.0 for k in ('DA','ID','cap_up','cap_down','act_up','act_down')}
            for key in report['months']}
    month_valid={key:0 for key in report['months']}
    for row in report['rows']:
        if row['cash'] is None:
            continue
        month=datetime.fromisoformat(row['time']).astimezone(MADRID).strftime('%Y-%m')
        month_valid[month]+=1
        for key,value in row['cash'].items():
            months[month][key]+=float(value)
    for month,values in months.items():
        if month_valid[month]==0:
            report['months'][month]['cash_eur']=None
            report['months'][month]['cash_keur_per_mw']=None
            continue
        report['months'][month]['cash_eur']=values
        report['months'][month]['cash_keur_per_mw']={key:value/(1000*discharge_mw)
                                                      for key,value in values.items()}
    report['capacity_award_mode']='posthoc'
    report['cash_basis']='capacity_cash_posthoc_proxy; checkpoint retains full_fill solver state'
    report['assumptions'].append('capacity_award_rate_proxy_posthoc_capacity_revenue_only')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--start',required=True,help='first formal local date')
    p.add_argument('--end',required=True,help='formal end local date, exclusive')
    p.add_argument('--input',type=Path,default=CODE.parent/'input')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--budget-json',type=Path,help='explicit formal year:value map; not tail budgets')
    p.add_argument('--time-limit',type=float,default=30.)
    p.add_argument('--preflight-only',action='store_true')
    p.add_argument('--checkpoint-every',type=int,default=1,help='save cumulative checkpoint every N windows')
    p.add_argument('--capacity-award-mode',choices=('full_fill','optimize','posthoc'),default='full_fill',
        help='full_fill: ignore award rates; optimize: include rates in MILP objective; posthoc: haircut capacity cash after V1 decisions')
    p.add_argument('--award-rate-file',type=Path,help='required for optimize/posthoc; QH/direction CSV.GZ')
    args=p.parse_args()
    if args.capacity_award_mode!='full_fill' and not args.award_rate_file:
        p.error('--award-rate-file is required for optimize and posthoc modes')
    if args.capacity_award_mode=='full_fill' and args.award_rate_file:
        p.error('--award-rate-file requires --capacity-award-mode optimize or posthoc')
    if args.checkpoint_every<1:p.error('checkpoint-every must be positive')
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
    award_rates=load_award_rates(args.award_rate_file) if args.award_rate_file else None
    preparation_rates=award_rates if args.capacity_award_mode in ('optimize','posthoc') else None
    inp,mask,evidence,budgets=prepare(bundle,end,formal_budget=explicit,
        budget_source=('explicit:'+digest(explicit)) if explicit is not None else 'formal_valid_mask',
        award_rates=preparation_rates)
    if args.capacity_award_mode=='posthoc':
        # Solve exactly the full-fill V1 problem; retain rates as separate audit evidence.
        inp=replace(inp,qhs=tuple(replace(q,afrr_award_rate_up=1.0,afrr_award_rate_down=1.0) for q in inp.qhs))
        save_award_evidence=[row for row in evidence['rows']
                             if 'award_rate_up' in row or 'award_rate_down' in row]
    else:
        save_award_evidence=None
    run_id='ES_HISTORICAL_CONDITIONAL_PERFECT_V1'+('_CAP_RATE_OPT' if args.capacity_award_mode=='optimize' else '_CAP_RATE_POSTHOC' if args.capacity_award_mode=='posthoc' else '')
    save('input_evidence.json',evidence)
    save('solver_input.json',asdict(inp))
    if save_award_evidence is not None:
        save('award_rate_evidence.json',save_award_evidence)
    save('manifest.json',dict(mode='perfect_history_v1',scenario='ts_start/cap_old/D'+('/capacity_award_rate_proxy_'+args.capacity_award_mode if award_rates is not None else ''),
        capacity_award_mode=args.capacity_award_mode,run_id=run_id,
        checkpoint_cash_basis='full_fill_solver_state_before_posthoc' if args.capacity_award_mode=='posthoc' else 'solver_settlement',
        formal_start=start,formal_end=end,input_end=end+timedelta(days=1),budgets=budgets,
        award_rate_source=dict(path=str(args.award_rate_file),sha256=__import__('hashlib').sha256(args.award_rate_file.read_bytes()).hexdigest()) if args.award_rate_file else None,
        input_hash=digest(asdict(inp)),source_files=bundle.sources,rejected=bundle.rejected,
        code_hashes={str(f.relative_to(CODE)):__import__('hashlib').sha256(f.read_bytes()).hexdigest()
                     for folder in ('src/es_synthetic_market','src/es_historical_conditional') for f in (CODE/folder).glob('*.py')},
        preparation_seconds=perf_counter()-started))
    if args.preflight_only:
        print(json.dumps(dict(status='preflight_complete',qh=len(inp.qhs),gaps=len(mask),budgets=budgets),default=str))
        return
    engine=PerfectEngine(inp,execution_end=end,inactive=mask,evidence=evidence,budget_manifest=budgets,
        capacity_award_sensitivity=args.capacity_award_mode=='optimize',
        run_id=run_id,
        history_mode='delta',time_limit_seconds=args.time_limit)
    solve_started=perf_counter()
    # Each successful commit can be resumed with PerfectEngine.restore; no failed candidate is written as a committed state.
    while engine.step():
        n=len(engine._windows)
        if n%args.checkpoint_every==0:
            save(f'checkpoint_{n:04d}.json',engine.checkpoint())
        w=engine._windows[-1]
        print(json.dumps(dict(window=n,start=str(w.start_utc),soc=engine._soc,
            solver_seconds=w.audit['model']['solver_seconds'],elapsed=perf_counter()-started)),flush=True)
    report=engine.report();report['execution_wall_seconds']=perf_counter()-solve_started
    report['total_wall_seconds']=perf_counter()-started
    report['capacity_award_mode']=args.capacity_award_mode
    report['cash_basis']='solver_settlement' if args.capacity_award_mode!='posthoc' else 'capacity_cash_posthoc_proxy; checkpoint retains full_fill solver state'
    ledger=engine._ledger.snapshot()
    if args.capacity_award_mode=='posthoc':
        apply_posthoc_capacity_rates(report,ledger,award_rates,inp.discharge_mw)
    save('result.json',report)
    save('cash_ledger.json',ledger)
    save('final_checkpoint.json',engine.checkpoint())
    frozen=[r for w in engine._windows for r in w.audit['frozen_delta']]
    save('frozen_ledger.json',frozen)
    summary={k:report[k] for k in ('mode','success','failure','annual_budget','annual_used','coverage','quality',
                                 'solver_seconds','execution_wall_seconds','total_wall_seconds','months')}
    summary['capacity_award_mode']=args.capacity_award_mode
    summary['cash_basis']=report['cash_basis']
    save('summary.json',summary)
    print(json.dumps(summary,ensure_ascii=False))

if __name__=='__main__':main()
