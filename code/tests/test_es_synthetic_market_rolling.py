"""Synthetic B-stage integration tests, with explicit artificial event times."""
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from zoneinfo import ZoneInfo
from types import SimpleNamespace
from unittest.mock import patch
import json
import unittest
from tests.test_es_synthetic_market_core import make_qh,make_contract
from src.es_synthetic_market import SyntheticMarketInput,ContractInput,RollingEngine,solve_rolling

UTC=timezone.utc
TZ=ZoneInfo("Europe/Madrid")

def fixture(start, count, price=None, reserve=False):
    start=start.astimezone(UTC)
    qhs=tuple(make_qh(str(i),start+timedelta(minutes=15*i),year=(start+timedelta(minutes=15*i)).astimezone(TZ).year) for i in range(count))
    contracts=tuple(make_contract(q,"DA",price(i) if price else 0.) for i,q in enumerate(qhs))
    return SyntheticMarketInput(qhs,contracts,annual_efc_budget={q.madrid_year:600 for q in qhs},
        reserve_limit_up_mw=100 if reserve else 0,reserve_limit_down_mw=100 if reserve else 0,
        input_id="ES_SYNTHETIC_MARKET_ROLLING_TEST")

class TestRolling(unittest.TestCase):
    def test_planning_days_validation_default_hash_and_checkpoint_isolation(self):
        inp=fixture(datetime(2025,1,1,tzinfo=TZ),3*96)
        default=RollingEngine(inp);explicit=RollingEngine(inp,planning_days=2)
        self.assertEqual(default.path,'rolling2-U')
        self.assertEqual(default.configuration_hash,explicit.configuration_hash)
        seven=RollingEngine(inp,planning_days=7)
        self.assertEqual(seven.path,'rolling7-U')
        self.assertNotEqual(seven.configuration_hash,default.configuration_hash)
        checkpoint=default.checkpoint()
        with self.assertRaises(ValueError):RollingEngine.restore(inp,checkpoint,planning_days=7)
        for bad in (True,0,-1,2.5):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):RollingEngine(inp,planning_days=bad)

    def test_two_day_window_covers_execution_and_next_day_only(self):
        inp=fixture(datetime(2025,1,1,tzinfo=TZ),3*96,lambda i:1 if 96<=i<192 else 0)
        a=RollingEngine(inp,planning_days=2);self.assertTrue(a.step(),a.failure)
        first=a._windows[0]
        self.assertEqual(len(first.planned_qh_ids),2*96)
        self.assertEqual(len(first.executed_qh_ids),96)
        self.assertEqual(datetime.fromisoformat(first.window_end_utc).astimezone(TZ),datetime(2025,1,3,tzinfo=TZ))
        contracts=tuple(replace(c,price_eur_per_mwh=10000) if i>=192 else c for i,c in enumerate(inp.contracts))
        qhs=tuple(replace(q,alpha_up=.4,alpha_down=.3) if i>=192 else q for i,q in enumerate(inp.qhs))
        b=RollingEngine(replace(inp,contracts=contracts,qhs=qhs),planning_days=2);self.assertTrue(b.step(),b.failure)
        self.assertEqual(first.order_snapshot,b._windows[0].order_snapshot)
        self.assertAlmostEqual(first.end_execution_soc_mwh,b._windows[0].end_execution_soc_mwh)

    def test_two_day_dst_boundary_uses_local_midnights(self):
        start=datetime(2025,3,29,tzinfo=TZ)
        end=datetime(2025,4,1,tzinfo=TZ)
        count=int((end.astimezone(UTC)-start.astimezone(UTC)).total_seconds()/900)
        engine=RollingEngine(fixture(start,count),planning_days=2)
        self.assertTrue(engine.step(),engine.failure)
        first=engine._windows[0]
        self.assertEqual(len(first.executed_qh_ids),96)
        self.assertEqual(len(first.planned_qh_ids),96+92)
        self.assertEqual(datetime.fromisoformat(first.window_end_utc).astimezone(TZ),datetime(2025,3,31,tzinfo=TZ))

    def test_two_day_freezes_next_day_orders_and_carries_soc_and_efc(self):
        start=datetime(2025,1,1,tzinfo=TZ)
        inp=fixture(start,3*96,lambda i:(-20 if i%2==0 else 80),True)
        target_index=100;target=inp.qhs[target_index]
        qhs=list(inp.qhs)
        qhs[target_index]=replace(target,afrr_gate_close_utc=inp.qhs[0].start_utc,
            afrr_result_release_utc=target.start_utc,afrr_capacity_price_up_eur_per_mw_qh=2)
        contracts=list(inp.contracts)
        contracts[target_index]=replace(contracts[target_index],gate_close_utc=inp.qhs[0].start_utc,
            result_release_utc=target.start_utc,price_eur_per_mwh=-200)
        inp=replace(inp,qhs=tuple(qhs),contracts=tuple(contracts))
        engine=RollingEngine(inp,planning_days=2,history_mode='delta')
        self.assertTrue(engine.step(),engine.failure)
        spot_before=engine._orders[contracts[target_index].contract_id]
        reserve_before=engine._reserves[target.qh_id]
        self.assertEqual(spot_before.status,'pending')
        self.assertEqual(reserve_before.status,'pending')
        self.assertTrue(engine.step(),engine.failure)
        spot_after=engine._orders[contracts[target_index].contract_id]
        reserve_after=engine._reserves[target.qh_id]
        self.assertEqual((spot_before.sell_mw,spot_before.buy_mw),(spot_after.sell_mw,spot_after.buy_mw))
        self.assertEqual((reserve_before.up_mw,reserve_before.down_mw),(reserve_after.up_mw,reserve_after.down_mw))
        self.assertEqual(spot_after.status,'awarded')
        self.assertEqual(reserve_after.status,'awarded')
        self.assertAlmostEqual(engine._windows[1].start_soc_mwh,engine._windows[0].end_execution_soc_mwh)
        self.assertGreaterEqual(engine._windows[1].efc_used_by_year[2025]+1e-9,
            engine._windows[0].efc_used_by_year[2025])

    def test_window_optimizes_future_day_but_executes_only_first_prefix(self):
        inp=fixture(datetime(2025,1,1,23,45,tzinfo=TZ),2,lambda i:10 if i==0 else 100)
        engine=RollingEngine(inp)
        self.assertTrue(engine.step(),engine.failure)
        first=engine._windows[0]
        self.assertEqual(len(first.planned_qh_ids),2)
        self.assertEqual(len(first.executed_qh_ids),1)
        self.assertGreater(first.end_execution_soc_mwh,10)
        self.assertLess(first.execution_cash_eur,0)
        self.assertLess(first.efc_used_by_year[2025],inp.effective_annual_efc_budget[2025])
        result=engine.run()
        self.assertTrue(result.success,result.failure)
        self.assertEqual(len(result.windows),2)
        self.assertAlmostEqual(result.windows[-1].end_execution_soc_mwh,10)
        self.assertGreater(result.execution_cash_eur,0)

    def test_pending_future_spot_and_reserve_freeze_then_award(self):
        inp=fixture(datetime(2025,1,1,23,45,tzinfo=TZ),4,lambda i:(-50,0,100,0)[i],True)
        qhs=list(inp.qhs);target=qhs[2]
        release=target.start_utc-timedelta(minutes=5)
        qhs[2]=replace(target,afrr_gate_close_utc=qhs[0].start_utc,afrr_result_release_utc=release,
            afrr_capacity_price_up_eur_per_mw_qh=2,afrr_capacity_price_down_eur_per_mw_qh=3)
        contracts=list(inp.contracts)
        contracts[2]=replace(contracts[2],gate_close_utc=qhs[0].start_utc,result_release_utc=release)
        inp=replace(inp,qhs=tuple(qhs),contracts=tuple(contracts))
        result=solve_rolling(inp)
        self.assertTrue(result.success,result.failure)
        first=result.windows[0].order_snapshot
        initial=next(o for o in first["spot"] if o["contract_id"]==contracts[2].contract_id)
        final=next(o for o in result.final_orders if o.contract_id==contracts[2].contract_id)
        self.assertEqual(initial["status"],"pending")
        self.assertEqual(final.status,"awarded")
        self.assertGreater(initial["sell_mw"],0)
        self.assertAlmostEqual(initial["sell_mw"],final.sell_mw)
        res0=next(o for o in first["reserve"] if o["qh_id"]=="2")
        res1=next(o for o in result.final_reserves if o.qh_id=="2")
        self.assertEqual(res0["status"],"pending")
        self.assertEqual(res1.status,"awarded")
        self.assertEqual(res0["down_mw"],res1.down_mw)
        self.assertEqual(len(result.ledger.entries),len({e.key for e in result.ledger.entries}))
        self.assertAlmostEqual(sum(w.execution_cash_eur for w in result.windows),result.execution_cash_eur)

    def test_checkpoint_restart_and_run_replay_do_not_duplicate(self):
        inp=fixture(datetime(2025,1,1,23,45,tzinfo=TZ),5,lambda i:10 if i==0 else 100)
        a=RollingEngine(inp);self.assertTrue(a.step())
        checkpoint=json.loads(json.dumps(a.checkpoint()))
        b=RollingEngine.restore(inp,checkpoint)
        ra,rb=a.run(),b.run()
        self.assertTrue(ra.success,ra.failure)
        self.assertTrue(rb.success,rb.failure)
        self.assertAlmostEqual(ra.execution_cash_eur,rb.execution_cash_eur)
        self.assertEqual(ra.ledger.digest(),rb.ledger.digest())
        self.assertEqual(a.run().ledger.digest(),ra.ledger.digest())
        checkpoint["state"]["soc"]+=1
        with self.assertRaises(ValueError): RollingEngine.restore(inp,checkpoint)

    def test_failure_changes_no_committed_state_or_valid_profit(self):
        inp=fixture(datetime(2025,1,1,23,45,tzinfo=TZ),2)
        engine=RollingEngine(inp);before=engine.checkpoint()["state"]
        with patch("src.es_synthetic_market.rolling.solve_joint",return_value=SimpleNamespace(feasible=False,message="injected no solution")):
            result=engine.run()
        self.assertFalse(result.success)
        self.assertIsNone(result.execution_cash_eur)
        after=engine.checkpoint()["state"]
        for key in ("soc","index","used","orders","reserves","ledger","windows"):
            self.assertEqual(before[key],after[key])

    def test_hour_contract_crossing_midnight_has_one_mw_and_four_cash_shards(self):
        inp=fixture(datetime(2025,1,1,23,30,tzinfo=TZ),4)
        q=inp.qhs
        contracts=tuple(ContractInput(m,m,q[0].start_utc,q[0].start_utc,q[0].start_utc,q[-1].end_utc,p,{x.qh_id:1 for x in q}) for m,p in (("DA",50),("IDA",0)))
        result=solve_rolling(replace(inp,contracts=contracts))
        self.assertTrue(result.success,result.failure)
        self.assertAlmostEqual(result.execution_cash_eur,5000)
        paid=[e for e in result.ledger.entries if e.settlement_type=="DA_energy" and e.direction=="sell"]
        self.assertEqual(len(paid),4)
        self.assertTrue(all(abs(e.quantity-100)<1e-5 for e in paid))

    def test_dst_and_short_tail_execute_each_local_day_once(self):
        start=datetime(2025,3,29,12,tzinfo=TZ)
        end=datetime(2025,3,31,1,tzinfo=TZ)
        count=int((end.astimezone(UTC)-start.astimezone(UTC)).total_seconds()/900)
        result=solve_rolling(fixture(start,count))
        self.assertTrue(result.success,result.failure)
        self.assertEqual([len(w.executed_qh_ids) for w in result.windows],[48,92,4])
        ids=[q for w in result.windows for q in w.executed_qh_ids]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertEqual(len(ids),count)
        self.assertTrue(all(w.salvage_eur==0 for w in result.windows))

    def test_global_year_budget_not_recomputed_per_window_and_year_soc_continues(self):
        inp=fixture(datetime(2025,12,31,23,45,tzinfo=TZ),2,lambda i:0 if i==0 else 100)
        result=solve_rolling(inp)
        self.assertTrue(result.success,result.failure)
        self.assertGreater(result.windows[0].end_execution_soc_mwh,10)
        self.assertAlmostEqual(result.windows[1].start_soc_mwh,result.windows[0].end_execution_soc_mwh)
        for y,used in result.windows[-1].efc_used_by_year.items():
            self.assertLessEqual(used,inp.effective_annual_efc_budget[y]+1e-6)

    def test_actual_seven_day_window_and_day_eight_information_isolation(self):
        inp=fixture(datetime(2025,1,1,tzinfo=TZ),8*96,lambda i:1 if 6*96<=i<7*96 else 0)
        a=RollingEngine(inp,planning_days=7);self.assertTrue(a.step(),a.failure)
        self.assertEqual(len(a._windows[0].planned_qh_ids),7*96)
        self.assertEqual(len(a._windows[0].executed_qh_ids),96)
        contracts=tuple(replace(c,price_eur_per_mwh=10000) if i>=7*96 else c for i,c in enumerate(inp.contracts))
        qhs=tuple(replace(q,alpha_up=.4,alpha_down=.3) if i>=7*96 else q for i,q in enumerate(inp.qhs))
        b=RollingEngine(replace(inp,contracts=contracts,qhs=qhs),planning_days=7);self.assertTrue(b.step(),b.failure)
        self.assertEqual(a._windows[0].order_snapshot,b._windows[0].order_snapshot)
        self.assertAlmostEqual(a._windows[0].end_execution_soc_mwh,b._windows[0].end_execution_soc_mwh)
        w=a._windows[0]
        self.assertGreater(w.salvage_eur,0)
        self.assertAlmostEqual(w.objective_eur,w.gross_eur+w.salvage_eur)
        self.assertAlmostEqual(w.upper_bound_eur,w.objective_eur,places=4)
        self.assertLess(abs(w.absolute_gap_eur),1e-4)
        self.assertTrue(all(e.settlement_type!="terminal_value" for e in a._ledger.entries))
        self.assertAlmostEqual(a._used[2025],sum(row["efc"] for row in w.operation))

    def test_terminal_mean_is_clipped_after_averaging(self):
        inp=fixture(datetime(2025,1,1,tzinfo=TZ),8*96,lambda i:-10 if i%2 else 2)
        engine=RollingEngine(inp,planning_days=7)
        win,*_=engine._window_input(inp.qhs[:7*96],inp.qhs[0].start_utc,inp.qhs[7*96-1].end_utc)
        self.assertEqual(engine._salvage_coefficient(win,False),0)

if __name__=="__main__": unittest.main()
