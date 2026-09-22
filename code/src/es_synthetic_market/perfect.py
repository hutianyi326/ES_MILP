"""P0 perfect-history rolling mode. Nullable evidence never enters the MILP.

GCT reserve checks, full fill, and idle gap bridges are modelling assumptions.
Legacy RollingEngine and the archived v5 entry point remain reproducible.
"""
import json
from dataclasses import asdict, replace
from datetime import timedelta
from math import isfinite
from time import perf_counter

from .rolling import RollingEngine, _hash, _midnight, UTC, TOL
from .core import _required_madrid_timezone


class PerfectEngine(RollingEngine):
    def __init__(self, inp, *, execution_end, inactive=(), evidence=None, budget_manifest=None,
                 run_id="ES_SYNTHETIC_PERFECT_V1", order_mode="D", **kwargs):
        if execution_end.tzinfo is None:
            raise ValueError("aware execution_end required")
        self.execution_end=execution_end.astimezone(UTC)
        self.inactive=frozenset(inactive)
        self.evidence=evidence or {}
        self.budget_manifest=budget_manifest or {}
        if kwargs.get("planning_days",2)!=2:
            raise ValueError("perfect_history_v1 requires two local days")
        qhs=inp.qhs
        if not qhs[0].start_utc < self.execution_end or self.execution_end != _midnight(self.execution_end).astimezone(UTC):
            raise ValueError("execution_end must be a later local midnight")
        if qhs[0].start_utc != _midnight(qhs[0].start_utc).astimezone(UTC):
            raise ValueError("execution must start at local midnight")
        required_end=(_midnight(self.execution_end)+timedelta(days=1)).astimezone(UTC)
        if qhs[-1].end_utc != required_end:
            raise ValueError("input grid must include exactly one extra local day")
        if any(a.end_utc!=b.start_utc for a,b in zip(qhs,qhs[1:])):
            raise ValueError("nullable grid must be filled before constructing PerfectEngine")
        if self.inactive-set(inp.qh_by_id):
            raise ValueError("unknown inactive QH")
        # Gap coefficients are harmless finite sentinels, only behind zero bounds.
        # Original nulls remain in evidence; never overwrite raw files.
        qhs=tuple(replace(q,segment_id="continuous",**(dict(alpha_up=0.,alpha_down=0.,
            afrr_capacity_price_up_eur_per_mw_qh=0.,afrr_capacity_price_down_eur_per_mw_qh=0.,
            afrr_activation_price_up_eur_per_mwh=0.,afrr_activation_price_down_eur_per_mwh=0.)
            if q.qh_id in self.inactive else {})) for q in qhs)
        inp=replace(inp,qhs=qhs)
        super().__init__(inp,run_id=run_id,order_mode=order_mode,**kwargs)
        # Explicit global budgets, not the coverage cap of a sliced window.
        self._budget={int(y):float(v) for y,v in inp.annual_efc_budget.items()}
        self._used={y:0. for y in self._budget}
        self.configuration_hash=_hash(dict(base=self.configuration_hash,mode="perfect_history_v1",
            end=self.execution_end,mask=sorted(self.inactive),evidence=_hash(self.evidence),
            budgets=self.budget_manifest,assumptions=["full_fill_gct_headroom","gap_idle_zero_self_discharge"]))
        self._budget_audit={}
        self._last_result=None

    def _window_input(self,qhs,start,end):
        if not isfinite(self._soc) or not self.inp.e_min_mwh-TOL<=self._soc<=self.inp.e_max_mwh+TOL:
            raise ValueError("unknown_state")
        # Clamp a copy for v5-scale boundary noise, leaving failed state untouched.
        soc=min(self.inp.e_max_mwh,max(self.inp.e_min_mwh,self._soc))
        win,frozen,fr,remaining=super()._window_input(qhs,start,end,soc_override=soc)
        win=replace(win,e_initial_mwh=soc)
        for c in win.contracts:
            bad=bool({k for k,v in c.qh_weights.items() if v>0}&self.inactive)
            if bad:
                if max(frozen.get(c.contract_id,(0.,0.)))>TOL:
                    raise ValueError("unresolved_commitment:"+c.contract_id)
                frozen[c.contract_id]=(0.,0.)
            elif c.gate_close_utc<start and c.contract_id not in frozen:
                frozen[c.contract_id]=(0.,0.)
        for q in qhs:
            if q.qh_id in self.inactive:
                if max(fr.get(q.qh_id,(0.,0.)))>TOL:
                    raise ValueError("unresolved_commitment:"+q.qh_id)
                fr[q.qh_id]=(0.,0.)
            elif q.afrr_gate_close_utc<start and q.qh_id not in fr:
                fr[q.qh_id]=(0.,0.)
        # Confirm we can represent every order whose GCT will occur today.
        boundary=min((_midnight(start)+timedelta(days=1)).astimezone(UTC),self.execution_end)
        modeled={c.contract_id for c in win.contracts}
        for c in self.inp.contracts:
            if start<=c.gate_close_utc<boundary and c.delivery_end_utc>start and c.contract_id not in modeled:
                raise ValueError("future_commitment_outside_window:"+c.contract_id)
        terminal_year=(self.execution_end-timedelta(microseconds=1)).astimezone(_required_madrid_timezone()).year
        reserve=(self.inp.e_max_mwh-self.inp.e_terminal_mwh)/(self.inp.eta_discharge*self.inp.cycle_denominator_mwh)
        self._budget_audit={}
        for y in remaining:
            available=max(0.,self._budget[y]-self._used[y])
            withheld=min(available,reserve) if y==terminal_year and end<self.execution_end else 0.
            remaining[y]=max(0.,available-withheld-1e-6)
            self._budget_audit[y]=dict(budget=self._budget[y],used_before=self._used[y],available=available,
                withheld=withheld,numerical_margin=1e-6,solver_limit=remaining[y])
        return win,frozen,fr,remaining

    def _p0_solver_options(self,win):
        targets={q.qh_id:self.inp.e_terminal_mwh for q in win.qhs if q.end_utc==self.execution_end}
        return dict(reserve_headroom_from_gct=True,terminal_soc_at=targets)

    def _solve_window(self,win,order_mode,**options):
        from . import rolling
        from .core import SyntheticMarketResult
        # A missing execution day alone never reaches this shortcut. All future
        # window slots must be masked, and every frozen commitment verified zero.
        if not all(q.qh_id in self.inactive for q in win.qhs):
            return rolling.solve_joint(win,order_mode,**options)
        pairs=list(options['fixed_spot_mw'].values())+list(options['fixed_reserve_mw'].values())
        if any(max(pair)>TOL for pair in pairs):
            raise ValueError('unresolved_commitment')
        if any(abs(win.e_initial_mwh-target)>TOL for target in options['terminal_soc_at'].values()):
            raise ValueError('infeasible_terminal_with_gap')
        zero={q.qh_id:0. for q in win.qhs}
        trades=tuple(dict(contract_id=c.contract_id,sell_mw=0.,buy_mw=0.) for c in win.contracts)
        constants={c.contract_id:dict(column=-1,constant=0.) for c in win.contracts}
        reserves={q.qh_id:dict(column=-1,constant=0.) for q in win.qhs}
        return self._zero_result(win,order_mode,zero,trades,constants,reserves)

    @staticmethod
    def _zero_result(win,order_mode,zero,trades,constants,reserves):
        from .core import SyntheticMarketResult
        return SyntheticMarketResult(order_mode=order_mode,success=True,status=0,message='fixed_path_validated_skip',
            objective_gross_eur=0.,solver_objective_min_eur=0.,qh_baseline_mw=zero,reserve_up_mw=zero,
            reserve_down_mw=zero,soc_trace_mwh={'continuous':tuple(win.e_initial_mwh for q in win.qhs)},
            qh_power_trace_mw={q.qh_id:(0.,) for q in win.qhs},cash_breakdown_eur={},
            residuals=dict(solver_seconds=0.,model_columns=0,model_rows=0,model_nonzeros=0,model_integers=0,
                eliminated_objective_constant_min=0.,solver_variable_objective_min=0.,fixed_path_validated_skip=1),
            absolute_gap_eur=0.,relative_gap=0.,raw_solver_gap=0.,input_id=win.input_id,feasible=True,
            proven_optimal=True,profit_upper_bound_eur=0.,contract_trades=trades,salvage_eur=0.,objective_eur=0.,
            solver_mapping=dict(contracts=constants,reserve_up=reserves,reserve_down=reserves,objective_constant_min=0.))

    def _salvage_coefficient(self,win,final):
        last=win.qhs[-1].start_utc.astimezone(_required_madrid_timezone()).date()
        quotes=[]
        for q in win.qhs:
            if q.qh_id in self.inactive or q.start_utc.astimezone(_required_madrid_timezone()).date()!=last:
                continue
            cs=[c for c in win.contracts if c.market=="DA" and c.qh_weights.get(q.qh_id,0)>0]
            if len(cs)==1:
                quotes.append(cs[0].price_eur_per_mwh)
        return .92*max(sum(quotes)/len(quotes),0.) if quotes else 0.

    def _audit_candidate(self,win,result,window,orders,reserves,frozen,fr,remaining):
        """Independent public-output audit, before the transactional commit."""
        trades={t['contract_id']:t for t in result.contract_trades}
        events=[];restored=[];gross=0.;variable_cash=0.;constant_cash=0.
        for c in win.contracts:
            t=trades[c.contract_id];net=t['sell_mw']-t['buy_mw']
            pair=frozen.get(c.contract_id)
            if pair is not None and abs(net-(pair[0]-pair[1]))>TOL:
                raise AssertionError("eliminated contract restoration failed")
            cash=c.price_eur_per_mwh*net*sum(c.qh_weights.values())*.25
            gross+=cash
            if pair is not None or c.gate_close_utc<win.qhs[0].start_utc: constant_cash+=cash
            else: variable_cash+=cash
            restored.append(dict(contract_id=c.contract_id,net_mw=net,eliminated=pair is not None or c.gate_close_utc<win.qhs[0].start_utc,
                weights=dict(c.qh_weights),cash_eur=cash))
        for q in win.qhs:
            up=result.reserve_up_mw[q.qh_id];down=result.reserve_down_mw[q.qh_id]
            if q.qh_id in fr and max(abs(up-fr[q.qh_id][0]),abs(down-fr[q.qh_id][1]))>TOL:
                raise AssertionError("eliminated reserve restoration failed")
            cash=up*(q.afrr_capacity_price_up_eur_per_mw_qh+q.alpha_up*.25*q.afrr_activation_price_up_eur_per_mwh)
            cash+=down*(q.afrr_capacity_price_down_eur_per_mw_qh+q.alpha_down*.25*q.afrr_activation_price_down_eur_per_mwh)
            gross+=cash
            if q.qh_id in fr or q.afrr_gate_close_utc<win.qhs[0].start_utc: constant_cash+=cash
            else: variable_cash+=cash
            cs=[c for c in win.contracts if c.qh_weights.get(q.qh_id,0)>0]
            nodes=sorted({q.afrr_gate_close_utc}|{c.result_release_utc for c in cs if c.result_release_utc>=q.afrr_gate_close_utc})
            for node in nodes:
                base=sum(c.qh_weights[q.qh_id]*(trades[c.contract_id]['sell_mw']-trades[c.contract_id]['buy_mw'])
                         for c in cs if c.result_release_utc<=node)
                su=win.grid_export_mw-base-up;sd=win.grid_import_mw+base-down
                if min(su,sd)<-TOL: raise AssertionError("independent GCT headroom failed")
                events.append(dict(qh_id=q.qh_id,event=node.isoformat(),baseline=base,up=up,down=down,slack_up=su,slack_down=sd))
        if abs(gross-result.objective_gross_eur)>TOL:
            raise AssertionError("independent gross reconstruction failed")
        if abs(constant_cash+result.residuals['eliminated_objective_constant_min'])>TOL:
            raise AssertionError("eliminated objective constant failed")
        # Min objective contains the variable salvage term; reference offset is separate.
        coeff=self._salvage_coefficient(win,False)
        rebuilt=-result.residuals['solver_variable_objective_min']+constant_cash-coeff*10
        if abs(rebuilt-result.objective_eur)>TOL:
            raise AssertionError("independent objective reconstruction failed")
        if abs(gross+result.salvage_eur-result.objective_eur)>TOL:
            raise AssertionError("salvage cash separation failed")
        frozen_rows=[]
        for c in self.inp.contracts:
            if c.contract_id not in orders: continue
            o=orders[c.contract_id]
            if c.contract_id in self._orders:
                old=self._orders[c.contract_id]
                if (o.sell_mw,o.buy_mw)!=(old.sell_mw,old.buy_mw):raise AssertionError("frozen spot changed")
                continue
            reason="initial_closed_zero" if c.gate_close_utc<self.inp.qhs[0].start_utc else (
                "gap_disabled" if set(c.qh_weights)&self.inactive else "optimized")
            frozen_rows.append(dict(key=[self.run_id,self.path,c.contract_id,"net"],instrument_id=c.contract_id,
                market=c.market,session=c.contract_id,delivery_start=c.delivery_start_utc.isoformat(),
                delivery_end=c.delivery_end_utc.isoformat(),weights=dict(c.qh_weights),gct=c.gate_close_utc.isoformat(),
                release=c.result_release_utc.isoformat(),freeze_at=max(c.gate_close_utc,self.inp.qhs[0].start_utc).isoformat(),
                mw=o.sell_mw-o.buy_mw,reason=reason,status=o.status,window=window.start_utc,input_hash=self.input_hash))
        for q in self.inp.qhs:
            if q.qh_id not in reserves:continue
            r=reserves[q.qh_id]
            if q.qh_id in self._reserves:
                old=self._reserves[q.qh_id]
                if (r.up_mw,r.down_mw)!=(old.up_mw,old.down_mw):raise AssertionError("frozen reserve changed")
                continue
            for direction,mw in (("up",r.up_mw),("down",r.down_mw)):
                frozen_rows.append(dict(key=[self.run_id,self.path,q.qh_id,direction],instrument_id=q.qh_id,
                    market="aFRR",direction=direction,delivery_start=q.start_utc.isoformat(),delivery_end=q.end_utc.isoformat(),
                    gct=q.afrr_gate_close_utc.isoformat(),release=q.afrr_result_release_utc.isoformat(),
                    freeze_at=max(q.afrr_gate_close_utc,self.inp.qhs[0].start_utc).isoformat(),mw=mw,
                    reason="initial_closed_zero" if q.afrr_gate_close_utc<self.inp.qhs[0].start_utc else ("gap_disabled" if q.qh_id in self.inactive else "optimized"),
                    status=r.status,window=window.start_utc,input_hash=self.input_hash))
        self._last_result=result
        prior=self._windows[-1].order_snapshot_hash if self._windows else ''
        return dict(events=events,restored_contracts=restored,frozen_delta=frozen_rows,solver_mapping=dict(result.solver_mapping),
            frozen_before_hash=prior,frozen_after_hash=window.order_snapshot_hash,
            checkpoint_id=_hash(dict(input=self.input_hash,config=self.configuration_hash,window=window.start_utc,orders=window.order_snapshot_hash,ledger=window.ledger_digest)),
            frozen_reserves={k:list(v) for k,v in fr.items()},budget=dict(self._budget_audit),
            model=dict(result.residuals),gross_reconstructed=gross,variable_cash=variable_cash,constant_cash=constant_cash,
            lookahead_complete=not any(q.qh_id in self.inactive for q in win.qhs),
            headroom_assumption="stage1_full_fill_from_gct",salvage_coefficient=coeff)

    def report(self):
        """Materialize null results for gaps/blocked windows; never fake zero cash."""
        qmap=self.inp.qh_by_id;cash={};ops={};efcs={}
        for w in self._windows:
            for qid in w.executed_qh_ids:cash[qid]={k:0. for k in ('DA','ID','cap_up','cap_down','act_up','act_down')}
            for op in w.operation:
                ops[op['qh_id']]=op
                efcs[op['qh_id']]=efcs.get(op['qh_id'],0.)+op['efc']
        for row in self._ledger.snapshot():
            typ=row['settlement_type'];direction=row['direction']
            energy=typ in ('DA_energy','IDA_energy')
            qid=json.loads(row['object_id'])[1] if energy else row['object_id']
            if qid not in cash:continue
            key=('DA' if typ=='DA_energy' else 'ID') if energy else ('cap_' if typ=='aFRR_capacity' else 'act_')+direction
            cash[qid][key]+=row['cash_eur']
        rows=[]
        for q in self.inp.qhs:
            if q.start_utc>=self.execution_end:break
            executed=q.qh_id in cash
            valid=executed and q.qh_id not in self.inactive
            status='valid' if valid else ('assumed_idle' if executed else 'not_solved_due_to_unknown_state')
            rows.append(dict(qh_id=q.qh_id,time=q.start_utc.isoformat(),status=status,
                cash=cash[q.qh_id] if valid else None,soc=ops.get(q.qh_id,{}).get('end_soc_mwh'),
                efc=efcs.get(q.qh_id,0.) if executed else None))
        months={}
        for row in rows:
            month=qmap[row['qh_id']].start_utc.astimezone(_required_madrid_timezone()).strftime('%Y-%m')
            m=months.setdefault(month,dict(total_qh=0,valid_qh=0,cash_eur={k:0. for k in ('DA','ID','cap_up','cap_down','act_up','act_down')}))
            m['total_qh']+=1
            if row['cash'] is not None:
                m['valid_qh']+=1
                for k,v in row['cash'].items():m['cash_eur'][k]+=v
        for m in months.values():
            m['coverage']=m['valid_qh']/m['total_qh']
            m['cash_keur_per_mw']={k:v/(1000*self.inp.discharge_mw) for k,v in m['cash_eur'].items()} if m['valid_qh'] and self.inp.discharge_mw else None
            if not m['valid_qh']:m['cash_eur']=None
        formal_ids={r['qh_id'] for r in rows}
        evidence_rows=[r for r in self.evidence.get('rows',[]) if r['qh_id'] in formal_ids]
        raw_complete=sum(all(v is not None and isfinite(v) for v in r.get('raw_values',{}).values())
                         and all(v is not None and isfinite(v) for v in r.get('spot',{}).values()) for r in evidence_rows)
        quality=dict(formal_qh=len(rows),raw_field_complete_qh=raw_complete if evidence_rows else None,
            raw_field_coverage=raw_complete/len(rows) if evidence_rows else None,
            enabled_input_coverage=sum(qid not in self.inactive for qid in formal_ids)/len(rows),
            settlement_coverage=sum(r['cash'] is not None for r in rows)/len(rows),
            assumed_idle_hours=.25*sum(r['status']=='assumed_idle' for r in rows),
            blocked_qh=sum(r['status']=='not_solved_due_to_unknown_state' for r in rows),
            disabled_contract_count=sum(bool({k for k,v in c.qh_weights.items() if v>0}&self.inactive) for c in self.inp.contracts),
            disabled_contract_count_scope='entire_input_including_lookahead',
            incomplete_lookahead_windows=sum(not w.audit['lookahead_complete'] for w in self._windows))
        return dict(mode='perfect_history_v1',success=self.failure is None,failure=self.failure,
            formal_end=self.execution_end.isoformat(),input_hash=self.input_hash,configuration_hash=self.configuration_hash,
            assumptions=['perfect_prices_alpha_full_fill','reserve_headroom_from_gct','gap_idle_zero_self_discharge'],
            budgets=self.budget_manifest,annual_budget=self._budget,annual_used=self._used,
            rows=rows,months=months,quality=quality,coverage=quality['settlement_coverage'],
            solver_seconds=sum(w.audit['model']['solver_seconds'] for w in self._windows),
            windows=[w.as_dict() for w in self._windows],gaps=self.evidence)
