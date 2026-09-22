"""Synthetic multi-local-day optimization, one-local-day execution.

Only committed execution enters cash/EFC. Failed windows change no state.
Checkpoints are JSON serializable; no historical reader/API is provided.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta, timezone
from copy import deepcopy
from hashlib import sha256
import json
from importlib.metadata import version
from .core import (
    HISTORICAL_CONDITIONAL_PREFIX,
    SYNTHETIC_MARKET_PREFIX,
    SyntheticMarketInput,
    solve_joint,
    _required_madrid_timezone,
)
from .ledger import LedgerEntry, SettlementLedger

UTC=timezone.utc
TOL=1e-5

def _hash(value):
    return sha256(json.dumps(value,sort_keys=True,default=str,separators=(",", ":")).encode()).hexdigest()

def _midnight(value):
    return value.astimezone(_required_madrid_timezone()).replace(hour=0,minute=0,second=0,microsecond=0)

@dataclass(frozen=True)
class RollingOrder:
    contract_id: str
    sell_mw: float
    buy_mw: float
    status: str
    submitted_at: str
    result_release_utc: str

@dataclass(frozen=True)
class FrozenReserve:
    qh_id: str
    up_mw: float
    down_mw: float
    status: str
    submitted_at: str
    result_release_utc: str

@dataclass(frozen=True)
class RollingWindowResult:
    start_utc: str
    window_end_utc: str
    execute_end_utc: str
    planned_qh_ids: tuple[str,...]
    executed_qh_ids: tuple[str,...]
    start_soc_mwh: float
    end_execution_soc_mwh: float
    gross_eur: float
    salvage_eur: float
    objective_eur: float
    upper_bound_eur: float | None
    absolute_gap_eur: float | None
    relative_gap: float | None
    raw_solver_gap: float | None
    proven_optimal: bool
    execution_cash_eur: float
    efc_used_by_year: dict
    order_snapshot: dict
    order_snapshot_hash: str
    ledger_digest: str
    operation: tuple[dict,...]
    trade_bound_canonicalization_max_mw: float = 0.0
    snapshot_mode: str = "full"
    ledger_delta: tuple[dict,...] = ()
    previous_ledger_digest: str = ""

    def as_dict(self): return asdict(self)

@dataclass(frozen=True)
class RollingRunResult:
    run_id: str
    path: str
    success: bool
    failure: str | None
    windows: tuple[RollingWindowResult,...]
    ledger: SettlementLedger
    final_orders: tuple[RollingOrder,...]
    final_reserves: tuple[FrozenReserve,...]
    input_hash: str
    configuration_hash: str
    data_scope: str = "synthetic"
    research_provenance: str = ""
    history_mode: str = "full"
    planning_days: int = 2

    @property
    def execution_cash_eur(self):
        return self.ledger.total_cash_eur if self.success else None

    def as_dict(self, *, include_ledger=True):
        out=dict(run_id=self.run_id,path=self.path,success=self.success,failure=self.failure,
            execution_cash_eur=self.execution_cash_eur,
            diagnostic_cash_before_failure_eur=None if self.success else self.ledger.total_cash_eur,
            windows=[w.as_dict() for w in self.windows],
            final_orders=[asdict(o) for o in self.final_orders],final_reserves=[asdict(o) for o in self.final_reserves],
            input_hash=self.input_hash,configuration_hash=self.configuration_hash,
            weight_kind="fixed_order_no_probability",design_version="2026-09-20-draft-4",
            environment={p:version(p) for p in ("numpy","scipy","tzdata")},fees="not_included",
            scope="synthetic_only" if self.data_scope == "synthetic" else "historical_conditional",
            data_scope=self.data_scope,research_provenance=self.research_provenance,
            history_mode=self.history_mode,planning_days=self.planning_days,
            ledger_digest_kind="sha256_delta_chain" if self.history_mode=="delta" else "sha256_full_snapshot")
        if include_ledger:
            out['cash_ledger']=self.ledger.snapshot()
        elif self.history_mode=="delta":
            out['cash_ledger_reference']=dict(kind='reconstruct_from_window_ledger_delta',
                rows=sum(len(w.ledger_delta) for w in self.windows),
                chain_head=self.windows[-1].ledger_digest if self.windows else '')
        else:
            raise ValueError('only delta history can omit the duplicate ledger')
        return out

class RollingEngine:
    def __init__(self, inp: SyntheticMarketInput, *, run_id="ES_SYNTHETIC_ROLLING",
                 order_mode="U", time_limit_seconds=60., mip_rel_gap=1e-4, history_mode="full",
                 planning_days=2, presolve=False):
        if not isinstance(presolve, bool):
            raise ValueError("presolve must be boolean")
        if history_mode not in {"full","delta"}:
            raise ValueError("unknown rolling history mode")
        self.history_mode=history_mode
        if order_mode not in {"U","D"}:
            raise ValueError("fixed U/D order required")
        if isinstance(planning_days,bool) or not isinstance(planning_days,int) or planning_days < 1:
            raise ValueError("planning_days must be a positive integer")
        # Existing synthetic run IDs use the broader ES_SYNTHETIC_ namespace
        # (for example ES_SYNTHETIC_ROLLING); preserve that compatibility while
        # keeping input IDs stricter in core.py.
        prefix = "ES_SYNTHETIC_" if inp.data_scope == "synthetic" else HISTORICAL_CONDITIONAL_PREFIX
        if not run_id.startswith(prefix):
            raise ValueError(f"{inp.data_scope} run ID must start with {prefix}")
        if inp.fixed_commitments:
            raise ValueError("rolling starts without historical commitments; use checkpoint for continuation")
        if inp.e_initial_mwh != 10 or inp.e_terminal_mwh != 10:
            raise ValueError("rolling independent segments start/end at 10 MWh")
        for a,b in zip(inp.qhs,inp.qhs[1:]):
            if a.segment_id != b.segment_id and a.end_utc == b.start_utc:
                raise ValueError("only genuine gaps may reset SOC")
        self.inp=deepcopy(inp)
        self.run_id=run_id;self.order_mode=order_mode;self.planning_days=planning_days
        self.path=f"rolling{planning_days}-"+order_mode
        self.time_limit_seconds=time_limit_seconds;self.mip_rel_gap=mip_rel_gap
        self.presolve=presolve
        self.input_hash=_hash(asdict(inp))
        self.configuration_hash=_hash(dict(run_id=run_id,order=order_mode,time_limit=time_limit_seconds,gap=mip_rel_gap,presolve=presolve,design="draft-4",tzdata=version("tzdata")))
        # Preserve the legacy seven-day configuration hash.  The production
        # two-day strategy receives its own hash so old rolling7 checkpoints
        # cannot be restored into a default rolling2 run.
        if planning_days!=7:
            self.configuration_hash=_hash(dict(legacy=self.configuration_hash,planning_days=planning_days))
        if history_mode!="full":
            self.configuration_hash=_hash(dict(legacy=self.configuration_hash,history_mode=history_mode))
        self._qh_contract_indices={q.qh_id:[] for q in self.inp.qhs}
        self._segment_contract_indices={q.segment_id:[] for q in self.inp.qhs}
        self._segment_rows={};self._segment_positions={}
        qmap=self.inp.qh_by_id
        for q in self.inp.qhs:
            rows=self._segment_rows.setdefault(q.segment_id,[])
            self._segment_positions[q.qh_id]=len(rows);rows.append(q)
        for j,c in enumerate(self.inp.contracts):
            segments=set()
            for key,weight in c.qh_weights.items():
                if weight>0:
                    self._qh_contract_indices[key].append(j);segments.add(qmap[key].segment_id)
            for seg in segments:self._segment_contract_indices[seg].append(j)
        self._budget=inp.effective_annual_efc_budget
        self._used={y:0. for y in self._budget}
        self._soc=10.;self._index=0
        self._orders={};self._reserves={};self._ledger=SettlementLedger();self._windows=[]
        self.failure=None

    def _window_input(self, qhs, start, end):
        ids={q.qh_id for q in qhs};contracts=[];frozen={}
        candidates=sorted({j for q in qhs for j in self._qh_contract_indices[q.qh_id]})
        for j in candidates:
            c=self.inp.contracts[j]
            if c.delivery_end_utc <= start or c.delivery_start_utc >= end: continue
            old=self._orders.get(c.contract_id)
            mapped={k:v for k,v in c.qh_weights.items() if k in ids and v>0}
            if not mapped: continue
            if old is None:
                if c.delivery_start_utc < start or c.delivery_end_utc > end or set(k for k,v in c.qh_weights.items() if v>0)-ids:
                    continue  # Do not truncate new contracts to make them eligible.
                contracts.append(c)
            else:
                if c.delivery_end_utc > end and max(old.sell_mw,old.buy_mw)>TOL:
                    raise ValueError("existing commitment extends beyond window; cannot truncate")
                if c.delivery_end_utc > end: continue
                contracts.append(replace(c,delivery_start_utc=max(start,c.delivery_start_utc),qh_weights=mapped))
                frozen[c.contract_id]=(old.sell_mw,old.buy_mw)
        years={q.madrid_year for q in qhs}
        remaining={y:max(0.,self._budget[y]-self._used[y]) for y in years}
        win=replace(self.inp,qhs=tuple(qhs),contracts=tuple(contracts),fixed_commitments=(),
            annual_efc_budget={y:self._budget[y] for y in years},e_initial_mwh=self._soc,input_id=self.inp.input_id+"_WINDOW")
        fr={q.qh_id:(self._reserves[q.qh_id].up_mw,self._reserves[q.qh_id].down_mw) for q in qhs if q.qh_id in self._reserves}
        return win,frozen,fr,remaining

    def _salvage_coefficient(self, win, final):
        if final: return 0.
        tz=_required_madrid_timezone();last=win.qhs[-1].start_utc.astimezone(tz).date()
        numerator=denominator=0.
        quotes_by_qh={q.qh_id:[] for q in win.qhs}
        for c in win.contracts:
            if c.market=="DA":
                for key,weight in c.qh_weights.items():
                    if weight>0:quotes_by_qh[key].append(c)
        for q in win.qhs:
            if q.start_utc.astimezone(tz).date()!=last: continue
            quotes=quotes_by_qh[q.qh_id]
            if len(quotes)!=1:
                raise ValueError("terminal value requires exactly one DA reference price for each last-day QH")
            numerator+=quotes[0].price_eur_per_mwh*q.duration_hours;denominator+=q.duration_hours
        return .92*max(numerator/denominator,0.)

    @staticmethod
    def _status(nonzero, release, now):
        return ("awarded" if release<=now else "pending") if nonzero else "not_submitted"

    def _step(self):
        q0=self.inp.qhs[self._index]
        segment=self._segment_rows[q0.segment_id][self._segment_positions[q0.qh_id]:]
        start=q0.start_utc
        end=min((_midnight(start)+timedelta(days=self.planning_days)).astimezone(UTC),segment[-1].end_utc)
        execute_end=min((_midnight(start)+timedelta(days=1)).astimezone(UTC),segment[-1].end_utc)
        qhs=[q for q in segment if q.end_utc<=end];executed=[q for q in qhs if q.end_utc<=execute_end]
        win,frozen,frozen_reserve,remaining=self._window_input(qhs,start,end)
        final=end==segment[-1].end_utc;coefficient=self._salvage_coefficient(win,final)
        result=solve_joint(win,self.order_mode,time_limit_seconds=self.time_limit_seconds,mip_rel_gap=self.mip_rel_gap,
            presolve=self.presolve,
            terminal_hard=final,salvage_price_eur_per_mwh=coefficient,terminal_reference_mwh=10,
            fixed_spot_mw=frozen,fixed_reserve_mw=frozen_reserve,remaining_annual_efc=remaining,
            experimental_a1_a3=False)
        if not result.feasible: raise ValueError("window has no audited feasible solution: "+result.message)
        orders=dict(self._orders);reserves=dict(self._reserves);ledger=self._ledger.fork();used=dict(self._used)
        changed_spot=set();changed_reserve=set()
        trades={t["contract_id"]:t for t in result.contract_trades}
        segment_ids={q.qh_id for q in segment}
        for j in self._segment_contract_indices[q0.segment_id]:
            c=self.inp.contracts[j]
            if c.contract_id in orders or c.delivery_end_utc<=start or c.gate_close_utc>=execute_end: continue
            if not segment_ids.intersection(c.qh_weights): continue
            t=trades.get(c.contract_id)
            sell,buy=(float(t["sell_mw"]),float(t["buy_mw"])) if t and c.gate_close_utc>=start else (0.,0.)
            orders[c.contract_id]=RollingOrder(c.contract_id,sell,buy,self._status(max(sell,buy)>TOL,c.result_release_utc,execute_end),c.gate_close_utc.isoformat(),c.result_release_utc.isoformat())
            changed_spot.add(c.contract_id)
        for q in segment:
            if q.qh_id in reserves or q.afrr_gate_close_utc>=execute_end: continue
            up,down=(result.reserve_up_mw[q.qh_id],result.reserve_down_mw[q.qh_id]) if q.qh_id in result.reserve_up_mw and q.afrr_gate_close_utc>=start else (0.,0.)
            reserves[q.qh_id]=FrozenReserve(q.qh_id,up,down,self._status(max(up,down)>TOL,q.afrr_result_release_utc,execute_end),q.afrr_gate_close_utc.isoformat(),q.afrr_result_release_utc.isoformat())
            changed_reserve.add(q.qh_id)
        for key,o in list(orders.items()):
            if o.status=="pending" and datetime.fromisoformat(o.result_release_utc)<=execute_end:
                orders[key]=replace(o,status="awarded");changed_spot.add(key)
        for key,o in list(reserves.items()):
            if o.status=="pending" and datetime.fromisoformat(o.result_release_utc)<=execute_end:
                reserves[key]=replace(o,status="awarded");changed_reserve.add(key)
        e=self._soc;operation=[];trace_index=0;before=ledger.total_cash_eur;expected_cash=0.
        for q in executed:
            day=q.start_utc.astimezone(_required_madrid_timezone()).date().isoformat();baseline=0.
            for j in self._qh_contract_indices[q.qh_id]:
                c=self.inp.contracts[j]
                weight=float(c.qh_weights.get(q.qh_id,0))
                if not weight: continue
                o=orders.get(c.contract_id)
                if o is None: raise AssertionError("executed spot position was not frozen")
                baseline+=weight*(o.sell_mw-o.buy_mw)
                for direction,mw in (("sell",o.sell_mw),("buy",o.buy_mw)):
                    ledger.settle_energy(run_id=self.run_id,path=self.path,market=c.market,contract_id=c.contract_id,
                        direction=direction,quantity_mw=mw*weight,price_eur_per_mwh=c.price_eur_per_mwh,
                        qh_id=q.qh_id,hours=q.duration_hours,execution_day=day,fixed=c.contract_id in frozen)
                    expected_cash+=(1 if direction=="sell" else -1)*mw*weight*c.price_eur_per_mwh*q.duration_hours
            r=reserves[q.qh_id]
            if abs(baseline-result.qh_baseline_mw[q.qh_id])>TOL or abs(r.up_mw-result.reserve_up_mw[q.qh_id])>TOL or abs(r.down_mw-result.reserve_down_mw[q.qh_id])>TOL:
                raise AssertionError("executed commitments differ from optimized positions")
            for direction,mw,alpha,cap,act in (("up",r.up_mw,q.alpha_up,q.afrr_capacity_price_up_eur_per_mw_qh,q.afrr_activation_price_up_eur_per_mwh),("down",r.down_mw,q.alpha_down,q.afrr_capacity_price_down_eur_per_mw_qh,q.afrr_activation_price_down_eur_per_mwh)):
                common=dict(run_id=self.run_id,path=self.path,qh_id=q.qh_id,direction=direction,execution_day=day,fixed=q.qh_id in frozen_reserve)
                ledger.settle_capacity(**common,capacity_mw=mw,price_eur_per_mw_period=cap)
                ledger.settle_activation(**common,activation_mwh=mw*q.duration_hours*alpha,price_eur_per_mwh=act)
                expected_cash+=mw*cap+mw*q.duration_hours*alpha*act
            phases=[("up",q.alpha_up,baseline+r.up_mw),("down",q.alpha_down,baseline-r.down_mw)]
            if self.order_mode=="D": phases.reverse()
            phases.append(("idle",1-(q.alpha_up+q.alpha_down),baseline))
            for phase,fraction,power in phases:
                if fraction==0: continue
                h=q.duration_hours*fraction;ch=max(-power,0.);dis=max(power,0.);prior=e
                e+=self.inp.eta_charge*ch*h-dis*h/self.inp.eta_discharge
                efc=(self.inp.eta_charge*ch*h+dis*h/self.inp.eta_discharge)/self.inp.cycle_denominator_mwh
                used[q.madrid_year]+=efc
                if e<self.inp.e_min_mwh-TOL or e>self.inp.e_max_mwh+TOL or abs(e-result.soc_trace_mwh[q.segment_id][trace_index])>TOL:
                    raise AssertionError("independent executed SOC audit failed")
                operation.append(dict(qh_id=q.qh_id,phase=phase,hours=h,power_mw=power,start_soc_mwh=prior,end_soc_mwh=e,efc=efc,madrid_year=q.madrid_year))
                trace_index+=1
        if any(used[y]>self._budget[y]+TOL for y in used): raise AssertionError("executed annual EFC budget exceeded")
        cash=ledger.total_cash_eur-before
        if abs(cash-expected_cash)>TOL: raise AssertionError("independent executed cash audit failed")
        if execute_end==segment[-1].end_utc and abs(e-10)>TOL: raise AssertionError("segment terminal SOC is not 10")
        if self.history_mode=="delta":
            snapshot=dict(previous_snapshot_hash=self._windows[-1].order_snapshot_hash if self._windows else "",
                spot=[asdict(orders[k]) for k in sorted(changed_spot)],
                reserve=[asdict(reserves[k]) for k in sorted(changed_reserve)])
            ledger_delta=ledger.delta_snapshot()
            previous_ledger=self._windows[-1].ledger_digest if self._windows else ""
            ledger_digest=_hash(dict(previous=previous_ledger,entries=ledger_delta))
        else:
            snapshot=dict(spot=[asdict(orders[k]) for k in sorted(orders)],reserve=[asdict(reserves[k]) for k in sorted(reserves)])
            ledger_delta=();previous_ledger="";ledger_digest=ledger.digest()
        window=RollingWindowResult(start.isoformat(),end.isoformat(),execute_end.isoformat(),tuple(q.qh_id for q in qhs),
            tuple(q.qh_id for q in executed),self._soc,e,result.objective_gross_eur,result.salvage_eur,result.objective_eur,
            result.profit_upper_bound_eur,result.absolute_gap_eur,result.relative_gap,result.raw_solver_gap,result.proven_optimal,
            cash,dict(used),snapshot,_hash(snapshot),ledger_digest,tuple(operation),
            float(result.residuals.get("trade_bound_canonicalization_max_mw",0.0)),
            self.history_mode,ledger_delta,previous_ledger)
        self._ledger.commit(ledger)
        self._orders,self._reserves,self._used=orders,reserves,used
        self._soc=10. if execute_end==segment[-1].end_utc else e
        self._index+=len(executed);self._windows.append(window)

    def step(self):
        if self.failure is not None or self._index==len(self.inp.qhs): return False
        try: self._step()
        except (ValueError,AssertionError) as exc:
            self.failure=str(exc);return False
        return True

    def run(self):
        while self.step(): pass
        return RollingRunResult(self.run_id,self.path,self.failure is None,self.failure,tuple(self._windows),
            self._ledger.clone(),tuple(self._orders.values()),tuple(self._reserves.values()),self.input_hash,self.configuration_hash,
            self.inp.data_scope,self.inp.research_provenance,self.history_mode,self.planning_days)

    def checkpoint(self):
        state=dict(schema="ES_SYNTHETIC_ROLLING_V1",input_hash=self.input_hash,configuration_hash=self.configuration_hash,
            index=self._index,soc=self._soc,used=self._used,orders=[asdict(o) for o in self._orders.values()],
            reserves=[asdict(o) for o in self._reserves.values()],ledger=self._ledger.snapshot(),
            windows=[w.as_dict() for w in self._windows],failure=self.failure,history_mode=self.history_mode,
            planning_days=self.planning_days)
        state=json.loads(json.dumps(state,sort_keys=True))
        return dict(state=state,state_hash=_hash(state))

    @classmethod
    def restore(cls, inp, checkpoint, **kwargs):
        engine=cls(inp,**kwargs);s=checkpoint["state"]
        if _hash(s)!=checkpoint["state_hash"] or s["input_hash"]!=engine.input_hash or s["configuration_hash"]!=engine.configuration_hash:
            raise ValueError("checkpoint integrity/input/configuration mismatch")
        engine._index=s["index"];engine._soc=s["soc"];engine._used={int(k):v for k,v in s["used"].items()}
        engine._orders={o["contract_id"]:RollingOrder(**o) for o in s["orders"]}
        engine._reserves={o["qh_id"]:FrozenReserve(**o) for o in s["reserves"]}
        for row in s["ledger"]: engine._ledger.record(LedgerEntry(**{k:v for k,v in row.items() if k!="key"}))
        engine._windows=[RollingWindowResult(**w) for w in s["windows"]];engine.failure=s["failure"]
        if s.get("history_mode","full")!=engine.history_mode:
            raise ValueError("checkpoint history mode mismatch")
        if s.get("planning_days",7)!=engine.planning_days:
            raise ValueError("checkpoint planning horizon mismatch")
        if engine.history_mode=="delta":
            spot,reserve=verify_order_history(engine._windows)
            if spot!={k:asdict(v) for k,v in engine._orders.items()} or reserve!={k:asdict(v) for k,v in engine._reserves.items()}:
                raise ValueError("checkpoint orders differ from delta history")
            verify_ledger_history(engine._windows,engine._ledger)
        return engine


def verify_order_history(windows):
    """O(total updates) hash-chain verification and final state reconstruction."""
    spot={};reserve={};previous=""
    for w in windows:
        if _hash(w.order_snapshot)!=w.order_snapshot_hash:
            raise ValueError("order snapshot hash mismatch")
        if w.snapshot_mode=="delta":
            if w.order_snapshot.get("previous_snapshot_hash")!=previous:
                raise ValueError("order snapshot chain mismatch")
        elif w.snapshot_mode=="full":spot={};reserve={}
        else:raise ValueError("unknown snapshot encoding")
        for name,target,key,quantities in (("spot",spot,"contract_id",("sell_mw","buy_mw")),
                                            ("reserve",reserve,"qh_id",("up_mw","down_mw"))):
            for row in w.order_snapshot[name]:
                old=target.get(row[key])
                if old and any(old[k]!=row[k] for k in quantities):
                    raise ValueError("frozen quantity changed in history")
                target[row[key]]=dict(row)
        previous=w.order_snapshot_hash
    return spot,reserve


def verify_ledger_history(windows,ledger):
    """Check delta chain and reconcile every entry with the final full ledger."""
    expected={e.key:e for e in ledger.entries};seen=set();previous=""
    for w in windows:
        if w.snapshot_mode!="delta":raise ValueError("delta ledger history required")
        if w.previous_ledger_digest!=previous or _hash(dict(previous=previous,entries=w.ledger_delta))!=w.ledger_digest:
            raise ValueError("ledger chain mismatch")
        for row in w.ledger_delta:
            entry=LedgerEntry(**{k:v for k,v in row.items() if k!="key"})
            if tuple(row["key"])!=entry.key or entry.key in seen or expected.get(entry.key)!=entry:
                raise ValueError("ledger delta does not match unique final entry")
            seen.add(entry.key)
        previous=w.ledger_digest
    if seen!=set(expected):raise ValueError("ledger history incomplete")
    return previous

def solve_rolling(inp, **kwargs):
    return RollingEngine(inp,**kwargs).run()
