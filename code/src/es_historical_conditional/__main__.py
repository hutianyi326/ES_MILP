import argparse
from datetime import datetime, date, time, timedelta, timezone
from pathlib import Path
import json
from .adapter import load_raw,scenario,complete_contracts,model_input,evidence_payload,save_new,MADRID,dependency_hashes
from .runner import economic_trial

SCENARIOS=('ts_start__cap_old','ts_start__cap_new','ts_end__cap_old','ts_end__cap_new')
MODES=('rolling2','rolling7','joint_full')
ORDERS=('U','D')
# Empirical planning estimate from the audited eight-day rolling2 delta JSONs
# in rolling2_8day_20260921_v1 (768 QHs, eight result files).  It is a disk
# capacity estimate only and never enters optimization or settlement.
ROLLING2_DELTA_BYTES_PER_QH_ESTIMATE=23065.316731770832
COMMON_INPUT_BYTES_PER_QH_ESTIMATE=3167.459543

def validate_request(start_date,end_date,out,root):
    if not date(2025,1,1)<=start_date<end_date<=date(2026,9,1):
        raise ValueError('outside authorized 2025-01-01 to 2026-09-01 exclusive bounds')
    allowed=(root.parent/'output').resolve()
    if not out.is_relative_to(allowed) or out==allowed:raise ValueError('new named output below outputs/es_historical_conditional required')
    if out.exists():raise FileExistsError('output already exists; use a new version')

def _rolling_window_count(inp):
    count=0;by_segment={}
    for qh in inp.qhs:by_segment.setdefault(qh.segment_id,[]).append(qh)
    for rows in by_segment.values():
        index=0
        while index<len(rows):
            start=rows[index].start_utc
            midnight=start.astimezone(MADRID).replace(hour=0,minute=0,second=0,microsecond=0)
            execute_end=min((midnight+timedelta(days=1)).astimezone(timezone.utc),rows[-1].end_utc)
            advanced=sum(q.end_utc<=execute_end for q in rows[index:])
            if advanced<=0:raise AssertionError('rolling coverage does not advance')
            index+=advanced;count+=1
    return count

def _input_configuration(inp):
    return dict(qh_count=len(inp.qhs),contract_count=len(inp.contracts),
        segment_count=len({q.segment_id for q in inp.qhs}),
        battery={k:getattr(inp,k) for k in ('charge_mw','discharge_mw','grid_import_mw','grid_export_mw',
            'e_min_mwh','e_max_mwh','e_initial_mwh','e_terminal_mwh','eta_charge','eta_discharge',
            'reserve_limit_up_mw','reserve_limit_down_mw')},
        cycle_denominator_mwh=inp.cycle_denominator_mwh,
        annual_efc_budget=dict(inp.annual_efc_budget),effective_annual_efc_budget=inp.effective_annual_efc_budget,
        rolling_execution_windows=_rolling_window_count(inp),input_id=inp.input_id,
        data_scope=inp.data_scope,research_provenance=inp.research_provenance)

def build_preflight(*,args,bundle,cases,summary):
    inputs={name:_input_configuration(model_input(bundle,cases[name])) for name in args.scenarios}
    matrix=[dict(scenario=s,mode=m,order=o,planning_days={'rolling2':2,'rolling7':7}.get(m))
        for s in args.scenarios for m in args.modes for o in args.orders]
    rolling_calls=sum(inputs[r['scenario']]['rolling_execution_windows'] for r in matrix if r['mode'].startswith('rolling'))
    rolling2_qh=sum(inputs[r['scenario']]['qh_count'] for r in matrix if r['mode']=='rolling2')
    evidence_qh=sum(inputs[s]['qh_count'] for s in args.scenarios)
    size_estimate_applicable=set(args.modes)=={'rolling2'} and args.history_mode=='delta'
    result_bytes=round(rolling2_qh*ROLLING2_DELTA_BYTES_PER_QH_ESTIMATE) if size_estimate_applicable else None
    evidence_bytes=round(evidence_qh*COMMON_INPUT_BYTES_PER_QH_ESTIMATE)
    segments=cases[args.scenarios[0]]['manifest']['segments']
    return dict(schema='ES_HISTORICAL_CONDITIONAL_PREFLIGHT_V1',economic_solve_requested=args.run_economic,
        economic_solve_started_when_written=False,
        scope='historical_conditional',formal_approved=False,perfect_information_override=True,
        period=[args.start,args.end_exclusive],timezone='Europe/Madrid',resolution_minutes=15,
        coverage=dict(target_qh=len(bundle.grid),common_qh=next(iter(summary['coverage'].values()))['common_qh'],
            source_files=len(bundle.sources),rejected_files=len(bundle.rejected),
            common_start_utc=segments[0]['start_utc'],common_end_exclusive_utc=segments[-1]['end_exclusive_utc'],
            common_segments=segments,common_mask_basis=list(SCENARIOS),scenarios=summary['coverage']),
        selection=dict(scenarios=list(args.scenarios),modes=list(args.modes),orders=list(args.orders),run_matrix=matrix,
            defaults=dict(modes=['rolling2'],orders=['U','D'],scenarios=list(SCENARIOS))),inputs=inputs,
        solver=dict(time_limit_seconds=args.time_limit,mip_rel_gap=args.gap,history_mode=args.history_mode,
            presolve=args.presolve,
            engine='scipy.optimize.milp / bundled HiGHS',experimental_a1_a3=False),
        settlement=dict(label='conditional gross; not certified historical upper bound',fees='not_included',
            degradation_cash='not_included',spot_markets=['DA','IDA'],reserve=['aFRR capacity','aFRR activation'],
            only_executed_day_enters_cash_and_efc=True),
        output_plan=dict(directory=str(Path(args.output).resolve()),overwrite=False,result_files=len(matrix),
            rolling_solver_calls=rolling_calls,joint_solver_calls=sum(r['mode']=='joint_full' for r in matrix),
            rolling_history=args.history_mode,checkpoint_api_available=True,checkpoint_persistence=False,
            resume_from_disk=False,checkpoint_schema='ES_SYNTHETIC_ROLLING_V1',
            estimated_rolling2_result_json_bytes=result_bytes,
            estimated_common_input_json_bytes=evidence_bytes,
            estimated_total_json_bytes=(result_bytes+evidence_bytes if result_bytes is not None else None),
            size_estimate_basis='linear QH extrapolation from rolling2_8day_20260921_v1; planning only'),
        code_hashes=dependency_hashes())

def main():
    p=argparse.ArgumentParser(description='Conditional historical QA; annual economic trial defaults to rolling2')
    p.add_argument('--start',required=True);p.add_argument('--end-exclusive',required=True)
    p.add_argument('--output',required=True);p.add_argument('--run-economic',action='store_true')
    p.add_argument('--preflight-only',action='store_true',help='write compact machine-readable configuration without economic solves')
    p.add_argument('--modes',nargs='+',choices=MODES,default=['rolling2'])
    p.add_argument('--orders',nargs='+',choices=ORDERS,default=['U','D'])
    p.add_argument('--scenarios',nargs='+',choices=SCENARIOS,default=list(SCENARIOS))
    p.add_argument('--time-limit',type=float,default=30);p.add_argument('--gap',type=float,default=1e-4)
    p.add_argument('--history-mode',choices=('delta','full'),default='delta')
    p.add_argument('--presolve',dest='presolve',action='store_true',default=False,
                   help='enable HiGHS presolve (default off: presolve collapses this model and needs more nodes)')
    a=p.parse_args();root=Path(__file__).resolve().parents[2]
    if a.preflight_only and a.run_economic:raise ValueError('--preflight-only cannot be combined with --run-economic')
    if len(set(a.modes))!=len(a.modes) or len(set(a.orders))!=len(a.orders) or len(set(a.scenarios))!=len(a.scenarios):
        raise ValueError('duplicate mode/order/scenario selection')
    start=datetime.combine(date.fromisoformat(a.start),time(),tzinfo=MADRID)
    end=datetime.combine(date.fromisoformat(a.end_exclusive),time(),tzinfo=MADRID)
    out=Path(a.output).resolve();validate_request(start.date(),end.date(),out,root);out.mkdir(parents=True,exist_ok=False)
    b=load_raw(root.parent/'input',start,end);native_manifests={};masks=[]
    keys=[(t,c) for t in ('ts_start','ts_end') for c in ('cap_old','cap_new')]
    for key in keys:
        native=scenario(b,*key);native_manifests[key]=native['manifest'];masks.append(set(native['series']))
    common_points=complete_contracts(set.intersection(*masks),b.contracts)
    summary=dict(scope='historical_conditional',formal_approved=False,period=[a.start,a.end_exclusive],
        target_qh=len(b.grid),source_files=len(b.sources),rejected_files=len(b.rejected),code_hashes=dependency_hashes(),
        selection=dict(scenarios=list(a.scenarios),modes=list(a.modes),orders=list(a.orders)),coverage={},results=[],pressure_status='NOT_RUN')
    cases={}
    for key in keys:
        case=scenario(b,*key,restrict=common_points);name='__'.join(key);native=native_manifests[key]
        series_keys=set(case['series'])
        summary['coverage'][name]=dict(own_qh=native['selected_qh'],common_qh=len(series_keys),
            native_budget=native['annual_efc_budget'],common_budget=case['manifest']['annual_efc_budget'],
            segments=len(case['manifest']['segments']),contracts=sum(set(c['slots'])<=series_keys for c in b.contracts.values()))
        if name in a.scenarios:cases[name]=case
    save_new(out/'preflight.json',build_preflight(args=a,bundle=b,cases=cases,summary=summary))
    if a.preflight_only:
        save_new(out/'summary.json',summary);print(json.dumps({'output':str(out),'runs':0}),flush=True);return
    for name in a.scenarios:
        key=tuple(name.split('__'));case=cases[name]
        save_new(out/(name+'_own_manifest.json'),native_manifests[key])
        save_new(out/(name+'_common_input.json'),evidence_payload(b,case))
        if not a.run_economic:continue
        inp=model_input(b,case)
        for mode in a.modes:
            for order in a.orders:
                rid='ES_HISTORICAL_CONDITIONAL_'+name+'__'+mode+'__'+order
                result=economic_trial(inp,rid,mode,order,a.time_limit,a.gap,history_mode=a.history_mode,presolve=a.presolve)
                save_new(out/(rid+'.json'),result)
                row=dict(scenario=name,mode=mode,order=order,status=result['status'],gross_eur=result['valid_gross_eur'])
                summary['results'].append(row);print(json.dumps(row),flush=True)
    save_new(out/'summary.json',summary)
    print(json.dumps({'output':str(out),'coverage':summary['coverage'],'runs':len(summary['results'])}),flush=True)

if __name__=='__main__':main()
