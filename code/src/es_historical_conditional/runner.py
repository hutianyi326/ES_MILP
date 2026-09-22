"""Conditional economic trial with independent cash/physical replay; C not run."""
from dataclasses import asdict
from importlib.metadata import version
import platform
from src.es_synthetic_market.core import solve_joint
from src.es_synthetic_market.rolling import solve_rolling
from src.es_synthetic_market.integration import _physical
from src.es_synthetic_market.ledger import SettlementLedger
from .adapter import MADRID,digest,dependency_hashes

def rebuild_ledger(inp,spots,up,down,run_id,path):
    ledger=SettlementLedger(); byid={r['contract_id']:r for r in spots}
    qh_by_id=inp.qh_by_id
    for c in inp.contracts:
        if c.contract_id not in byid:continue
        r=byid[c.contract_id]
        for qid,w in c.qh_weights.items():
            day=str(qh_by_id[qid].start_utc.astimezone(MADRID).date())
            for direction in ('sell','buy'):
                ledger.settle_energy(run_id=run_id,path=path,market=c.market,contract_id=c.contract_id,
                    direction=direction,quantity_mw=float(r[direction+'_mw'])*w,
                    price_eur_per_mwh=c.price_eur_per_mwh,qh_id=qid,hours=.25,execution_day=day)
    for q in inp.qhs:
        for d,r,alpha,pc,pe in [('up',up[q.qh_id],q.alpha_up,q.afrr_capacity_price_up_eur_per_mw_qh,q.afrr_activation_price_up_eur_per_mwh),
                               ('down',down[q.qh_id],q.alpha_down,q.afrr_capacity_price_down_eur_per_mw_qh,q.afrr_activation_price_down_eur_per_mwh)]:
            common=dict(run_id=run_id,path=path,qh_id=q.qh_id,direction=d,execution_day=str(q.start_utc.astimezone(MADRID).date()))
            ledger.settle_capacity(**common,capacity_mw=r,price_eur_per_mw_period=pc)
            ledger.settle_activation(**common,activation_mwh=r*.25*alpha,price_eur_per_mwh=pe)
    return ledger

def economic_trial(inp,run_id,mode='rolling2',order='U',time_limit=30.,gap=1e-4,history_mode='delta',planning_days=None,presolve=False):
    if inp.data_scope!='historical_conditional' or not run_id.startswith('ES_HISTORICAL_CONDITIONAL_'):
        raise ValueError('explicit conditional trial required')
    if mode not in ('joint_full','rolling7','rolling2') or order not in ('U','D'):raise ValueError('unknown mode/order')
    if history_mode not in ('full','delta'):raise ValueError('unknown history mode')
    if not isinstance(presolve,bool):raise ValueError('presolve must be boolean')
    expected_days={'rolling7':7,'rolling2':2}.get(mode)
    if planning_days is None:planning_days=expected_days
    if planning_days!=expected_days:
        raise ValueError('planning_days must match the explicit rolling mode')
    if inp.fixed_commitments:raise ValueError('trial supports no initial commitments')
    path=mode+'-'+order
    if mode=='joint_full':
        result=solve_joint(inp,order,time_limit_seconds=time_limit,mip_rel_gap=gap,presolve=presolve,
            experimental_a1_a3=False)
        feasible=result.feasible;cash=result.objective_gross_eur;spots=result.contract_trades
        base=dict(result.qh_baseline_mw);up=dict(result.reserve_up_mw);down=dict(result.reserve_down_mw)
    else:
        result=solve_rolling(inp,run_id=run_id,order_mode=order,time_limit_seconds=time_limit,mip_rel_gap=gap,
            history_mode=history_mode,planning_days=planning_days,presolve=presolve)
        feasible=result.success;cash=result.execution_cash_eur;spots=[asdict(x) for x in result.final_orders]
        byid={r['contract_id']:r for r in spots};rs={r.qh_id:r for r in result.final_reserves}
        qh_by_id=inp.qh_by_id
        contracts_by_qh={qid:[] for qid in qh_by_id}
        for c in inp.contracts:
            for qid,weight in c.qh_weights.items():
                if c.contract_id in byid:
                    contracts_by_qh[qid].append((c,weight))
        base={q.qh_id:sum(weight*(byid[c.contract_id]['sell_mw']-byid[c.contract_id]['buy_mw']) for c,weight in contracts_by_qh[q.qh_id]) for q in inp.qhs}
        up={q.qh_id:rs[q.qh_id].up_mw if q.qh_id in rs else 0. for q in inp.qhs}
        down={q.qh_id:rs[q.qh_id].down_mw if q.qh_id in rs else 0. for q in inp.qhs}
    out=dict(run_id=run_id,mode=mode,order=order,input_scope=inp.data_scope,
             research_provenance=inp.research_provenance,conditional_backtest=True,
             perfect_information_override=True,formal_approved=False,
             source_result=(result.as_dict(include_ledger=False) if mode.startswith('rolling') and history_mode=='delta'
                            else result.as_dict()),status='FAIL',valid_gross_eur=None,
             pressure_status='NOT_RUN',revenue_label='conditional gross; not certified historical upper bound')
    input_config=asdict(inp)
    solver_config=dict(mode=mode,order=order,history_mode=history_mode,time_limit_seconds=time_limit,mip_rel_gap=gap,
                       planning_days=planning_days,presolve=presolve,
                       experimental_a1_a3=False,
                       python=platform.python_version(),versions={p:version(p) for p in ('numpy','scipy','tzdata')},
                       solver='scipy.optimize.milp / bundled HiGHS')
    out.update(input_configuration=input_config,input_configuration_hash=digest(input_config),
               solver_configuration=solver_config,solver_configuration_hash=digest(solver_config),
               dependency_hashes=dependency_hashes())
    if not feasible:return out
    main=_physical(inp,base,up,down,order)
    ledger=rebuild_ledger(inp,spots,up,down,run_id,path)
    residual=ledger.total_cash_eur-cash
    out.update(main_audit=main,cash_ledger=ledger.snapshot(),cash_breakdown=ledger.cash_by_type(),cash_residual_eur=residual,
        same_orders_other_order=_physical(inp,base,up,down,'D' if order=='U' else 'U'))
    if main['status']=='PASS' and abs(residual)<=1e-5:
        out.update(status='CONDITIONAL_PASS',valid_gross_eur=cash)
    return out
