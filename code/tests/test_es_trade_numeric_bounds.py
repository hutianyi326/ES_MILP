"""Persisted trades must be valid frozen inputs even with solver roundoff."""
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from scipy.optimize import milp as real_milp
from src.es_synthetic_market.core import _canonical_trade_mw
from src.es_synthetic_market import SyntheticMarketInput, RollingEngine
from tests.test_es_synthetic_market_core import make_qh, make_contract

class TestTradeNumericBounds(unittest.TestCase):
    def test_observed_eighth_day_roundoff(self):
        self.assertEqual(_canonical_trade_mw(-4.37990284725454e-14),0.0)
        self.assertEqual(_canonical_trade_mw(100.00000000000007),100.0)

    def test_valid_small_and_interior_trades_unchanged(self):
        for x in (0.,1e-14,1.25,99.99999999999,100.):
            self.assertEqual(_canonical_trade_mw(x),x)

    def test_material_overflow_and_nonfinite_rejected(self):
        for x in (-1e-6,100.000001,float('nan'),float('inf')):
            with self.assertRaises(ValueError):_canonical_trade_mw(x)

    def test_solver_exit_then_next_window_freeze(self):
        start=datetime(2025,1,1,22,45,tzinfo=timezone.utc)
        qhs=tuple(replace(make_qh(str(i),start+timedelta(minutes=15*i),cap_up=2,cap_down=3),
            afrr_gate_close_utc=start,afrr_result_release_utc=start) for i in range(2))
        contracts=tuple(replace(make_contract(q,m,p),gate_close_utc=start,result_release_utc=start)
            for q in qhs for m,p in [('DA',50),('IDA',0)])
        inp=SyntheticMarketInput(qhs,contracts,annual_efc_budget={2025:600},input_id='ES_SYNTHETIC_MARKET_BOUND_TEST')
        def noisy(**kwargs):
            result=real_milp(**kwargs)
            # Four signed contract entries, followed by two QH reserve pairs.
            for i in range(4):
                if result.x[i]==-100:result.x[i]=-100-7e-14
                elif result.x[i]==100:result.x[i]=100+7e-14
            for i in range(4,8):
                if result.x[i]==0:result.x[i]=-4e-14
                elif result.x[i]==100:result.x[i]=100+7e-14
            return result
        engine=RollingEngine(inp)
        with patch('scipy.optimize.milp',side_effect=noisy):
            self.assertTrue(engine.step(),engine.failure)
        result=engine.run()
        self.assertTrue(result.success,result.failure)
        self.assertEqual(len(result.windows),2)
        self.assertGreater(result.windows[0].trade_bound_canonicalization_max_mw,0)
        self.assertTrue(all(0<=o.sell_mw<=100 and 0<=o.buy_mw<=100 for o in result.final_orders))
        self.assertTrue(all(0<=o.up_mw<=100 and 0<=o.down_mw<=100 for o in result.final_reserves))

    def test_material_solver_overflow_submits_no_window(self):
        start=datetime(2025,1,1,tzinfo=timezone.utc)
        q=make_qh('q',start)
        inp=SyntheticMarketInput((q,),(make_contract(q,'DA',0),),annual_efc_budget={2025:600},
            input_id='ES_SYNTHETIC_MARKET_BOUND_BAD')
        def bad(**kwargs):
            result=real_milp(**kwargs);result.x[0]=-100.000001;return result
        engine=RollingEngine(inp);before=engine.checkpoint()['state']
        with patch('scipy.optimize.milp',side_effect=bad):result=engine.run()
        self.assertFalse(result.success)
        self.assertIsNone(result.execution_cash_eur)
        after=engine.checkpoint()['state']
        for k in ('index','soc','used','orders','reserves','ledger','windows'):
            self.assertEqual(before[k],after[k])

if __name__=='__main__':unittest.main()
