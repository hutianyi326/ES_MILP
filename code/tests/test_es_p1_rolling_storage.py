"""Economic/physical invariance and transactional compact-history checks."""
from dataclasses import asdict,replace
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from copy import deepcopy
import json
import unittest
from unittest.mock import patch
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
import random
from src.es_synthetic_market.ledger import SettlementLedger,LedgerEntry
from src.es_synthetic_market.rolling import RollingEngine,_hash,verify_order_history,verify_ledger_history
from src.es_synthetic_market.core import solve_joint
from tests.test_es_synthetic_market_rolling import fixture

TZ=ZoneInfo('Europe/Madrid')

def entry(i,cash=1):
    return LedgerEntry('r','p','aFRR_capacity',str(i),'up',1,cash,1,cash,'2025-01-01')

class TestLedgerTransaction(unittest.TestCase):
    def test_cancellation_accuracy_survives_fork_commit_clone(self):
        a=SettlementLedger();a.record(entry(0,1e16));a.record(entry(1,1))
        b=a.fork();b.record(entry(2,-1e16))
        self.assertEqual(b.total_cash_eur,1.)
        a.commit(b)
        self.assertEqual(a.total_cash_eur,sum(e.cash_eur for e in a.entries))
        self.assertEqual(a.clone().total_cash_eur,1.)
        randomizer=random.Random(19);many=SettlementLedger()
        for i in range(2000):many.record(entry(i,randomizer.uniform(-1e6,1e6)))
        self.assertEqual(many.total_cash_eur,sum(e.cash_eur for e in many.entries))

    def test_isolated_commit_and_immutable_clone(self):
        a=SettlementLedger();a.record(entry(0));b=a.fork();b.record(entry(1,3))
        self.assertEqual(a.total_cash_eur,1);self.assertEqual(b.total_cash_eur,4)
        self.assertEqual(len(b.delta_snapshot()),1)
        a.commit(b);self.assertEqual(a.total_cash_eur,4)
        with self.assertRaises(ValueError):a.commit(b)
        c=a.clone();c.record(entry(2));self.assertEqual(len(a.entries),2)
        self.assertEqual(c.entries[0],a.entries[0])

    def test_duplicate_conflict_and_stale_parent(self):
        a=SettlementLedger();a.record(entry(0));b=a.fork()
        b.record(replace(entry(0),fixed=True));self.assertEqual(len(b.delta_snapshot()),0)
        with self.assertRaises(ValueError):b.record(entry(0,3))
        a.record(entry(2))
        with self.assertRaises(ValueError):b.record(entry(3))
        with self.assertRaises(ValueError):a.commit(b)

class TestCompactRolling(unittest.TestCase):
    def make_input(self):
        inp=fixture(datetime(2025,1,1,23,30,tzinfo=TZ),100,lambda i: 0 if i%2==0 else 100,True)
        # Pending orders cross a local midnight and later become awarded.
        q=inp.qhs[3];qs=list(inp.qhs)
        qs[3]=replace(q,afrr_gate_close_utc=inp.qhs[0].start_utc,
            afrr_result_release_utc=q.start_utc,afrr_capacity_price_up_eur_per_mw_qh=2)
        cs=list(inp.contracts);cs[3]=replace(cs[3],gate_close_utc=inp.qhs[0].start_utc)
        return replace(inp,qhs=tuple(qs),contracts=tuple(cs))

    def test_full_delta_economics_and_snapshots_equivalent(self):
        inp=self.make_input()
        full=RollingEngine(inp,history_mode='full').run()
        delta=RollingEngine(inp,history_mode='delta').run()
        self.assertTrue(full.success,full.failure);self.assertTrue(delta.success,delta.failure)
        self.assertEqual(full.execution_cash_eur,delta.execution_cash_eur)
        self.assertEqual(full.final_orders,delta.final_orders)
        self.assertEqual(full.final_reserves,delta.final_reserves)
        self.assertEqual(full.ledger.digest(),delta.ledger.digest())
        for a,b in zip(full.windows,delta.windows):
            for field in ('operation','start_soc_mwh','end_execution_soc_mwh','efc_used_by_year','execution_cash_eur'):
                self.assertEqual(getattr(a,field),getattr(b,field))
        spot,reserve=verify_order_history(delta.windows)
        self.assertEqual(spot,{o.contract_id:asdict(o) for o in delta.final_orders})
        self.assertEqual(reserve,{o.qh_id:asdict(o) for o in delta.final_reserves})
        verify_ledger_history(delta.windows,delta.ledger)
        compact=delta.as_dict(include_ledger=False)
        self.assertNotIn('cash_ledger',compact)
        self.assertEqual(compact['cash_ledger_reference']['rows'],len(delta.ledger.entries))
        self.assertEqual(compact['cash_ledger_reference']['chain_head'],delta.windows[-1].ledger_digest)
        with self.assertRaises(ValueError):full.as_dict(include_ledger=False)
        self.assertIn('cash_ledger',full.as_dict())
        self.assertIn('cash_ledger',delta.as_dict())
        reconstructed=SettlementLedger()
        persisted=json.loads(json.dumps(compact))
        for w in persisted['windows']:
            for row in w['ledger_delta']:
                reconstructed.record(LedgerEntry(**{k:v for k,v in row.items() if k!='key'}))
        self.assertTrue(any(e.fixed for e in delta.ledger.entries))
        self.assertEqual(reconstructed.snapshot(),delta.ledger.snapshot())
        delta_rows=sum(len(w.order_snapshot['spot'])+len(w.order_snapshot['reserve']) for w in delta.windows)
        full_rows=sum(len(w.order_snapshot['spot'])+len(w.order_snapshot['reserve']) for w in full.windows)
        self.assertLess(delta_rows,full_rows)

    def test_pre_optimization_rolling_matches_new_delta(self):
        path=Path(__file__).resolve().parents[1]/'outputs/es_historical_conditional/eight_day_20260920_v2/source_snapshot/src/es_synthetic_market/rolling.py'
        name='src.es_synthetic_market._pre_p1_rolling_test'
        spec=importlib.util.spec_from_file_location(name,path)
        old=importlib.util.module_from_spec(spec);sys.modules[name]=old;spec.loader.exec_module(old)
        inp=self.make_input()
        a=old.RollingEngine(inp).run();b=RollingEngine(inp,history_mode='delta',planning_days=7).run()
        self.assertTrue(a.success,a.failure);self.assertTrue(b.success,b.failure)
        self.assertEqual(a.ledger.snapshot(),b.ledger.snapshot())
        self.assertEqual([asdict(o) for o in a.final_orders],[asdict(o) for o in b.final_orders])
        self.assertEqual([asdict(o) for o in a.final_reserves],[asdict(o) for o in b.final_reserves])
        for x,y in zip(a.windows,b.windows):
            for key in ('operation','execution_cash_eur','efc_used_by_year','start_soc_mwh','end_execution_soc_mwh'):
                self.assertEqual(getattr(x,key),getattr(y,key))

    def test_checkpoint_restore_and_rehashed_tamper_rejected(self):
        inp=self.make_input();a=RollingEngine(inp,history_mode='delta')
        self.assertTrue(a.step(),a.failure)
        cp=json.loads(json.dumps(a.checkpoint()))
        b=RollingEngine.restore(inp,cp,history_mode='delta')
        self.assertEqual(a.run().ledger.digest(),b.run().ledger.digest())
        tamper=deepcopy(cp);tamper['state']['windows'][0]['order_snapshot']['previous_snapshot_hash']='bad'
        tamper['state_hash']=_hash(tamper['state'])
        with self.assertRaises(ValueError):RollingEngine.restore(inp,tamper,history_mode='delta')
        tamper=deepcopy(cp);tamper['state']['windows'][0]['ledger_delta'][0]['cash_eur']+=1
        tamper['state_hash']=_hash(tamper['state'])
        with self.assertRaises(ValueError):RollingEngine.restore(inp,tamper,history_mode='delta')

    def test_delta_mid_transaction_audit_failure_does_not_commit(self):
        engine=RollingEngine(self.make_input(),history_mode='delta')
        self.assertTrue(engine.step(),engine.failure)
        before=engine.checkpoint()['state']
        def invalid_trace(*args,**kwargs):
            result=solve_joint(*args,**kwargs)
            traces=dict(result.soc_trace_mwh);key=next(iter(traces))
            traces[key]=(traces[key][0]+1,)+tuple(traces[key][1:])
            return replace(result,soc_trace_mwh=traces)
        with patch('src.es_synthetic_market.rolling.solve_joint',side_effect=invalid_trace):
            self.assertFalse(engine.step())
        self.assertIn('SOC audit',engine.failure)
        after=engine.checkpoint()['state']
        for k in ('index','soc','used','orders','reserves','ledger','windows'):
            self.assertEqual(before[k],after[k])

    def test_empty_failed_delta_reference_is_explicit(self):
        engine=RollingEngine(self.make_input(),history_mode='delta')
        with patch('src.es_synthetic_market.rolling.solve_joint',return_value=SimpleNamespace(feasible=False,message='injected')):
            result=engine.run()
        obj=result.as_dict(include_ledger=False)
        self.assertFalse(obj['success'])
        self.assertIsNone(obj['execution_cash_eur'])
        self.assertEqual(obj['cash_ledger_reference'],dict(kind='reconstruct_from_window_ledger_delta',rows=0,chain_head=''))

if __name__=='__main__':unittest.main()
