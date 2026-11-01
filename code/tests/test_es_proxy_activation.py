"""Proxy award changes activation amplitude, never duration or bid headroom."""
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from tests.test_es_synthetic_market_core import make_qh, make_input
from tests.test_es_perfect_v1 import daily
from src.es_synthetic_market.core import solve_joint
from src.es_synthetic_market.perfect import PerfectEngine


class ProxyActivationTests(unittest.TestCase):
    def solve(self, rate, basis='proxy_awarded', baseline=0, up=40, down=20):
        q=replace(make_qh('q',datetime(2025,1,1,12,tzinfo=timezone.utc),
            alpha_up=.4,alpha_down=.2,cap_up=10,cap_down=5,act_up=100,act_down=-50),
            afrr_award_rate_up=rate,afrr_award_rate_down=rate,activation_capacity_basis=basis)
        inp=replace(make_input((q,),(0,),contracts_both=False),e_initial_mwh=100,
            charge_mw=50,grid_import_mw=50)
        r=solve_joint(inp,'D',fixed_spot_mw={inp.contracts[0].contract_id:(max(baseline,0),max(-baseline,0))},
            fixed_reserve_mw={'q':(up,down)},terminal_hard=False,enforce_annual_efc=False,daily_efc_limit=2.)
        return inp,r

    def test_half_award_cash_soc_efc_and_unchanged_duration(self):
        inp,r=self.solve(.5)
        self.assertTrue(r.feasible,r.message)
        # Capacity 250 EUR; up activation 2 MWh x 100, down .5 MWh x -50.
        self.assertAlmostEqual(r.objective_gross_eur,425.)
        trace=r.soc_trace_mwh['seg-a']
        self.assertAlmostEqual(trace[0],100+.5*.92)
        self.assertAlmostEqual(trace[1],100+.5*.92-2/.92)
        self.assertAlmostEqual(r.residuals['annual_efc_used_2025'],(.5*.92+2/.92)/360)
        self.assertEqual(r.reserve_up_mw['q'],40)

    def test_zero_award_no_activation_but_full_bid_headroom(self):
        _,r=self.solve(0)
        self.assertTrue(r.feasible,r.message)
        self.assertAlmostEqual(r.objective_gross_eur,0)
        self.assertTrue(all(abs(v-100)<1e-7 for v in r.soc_trace_mwh['seg-a']))
        _,bad=self.solve(0,baseline=80,up=40,down=0)
        self.assertFalse(bad.feasible)

    def test_unit_award_matches_legacy(self):
        _,a=self.solve(1)
        _,b=self.solve(1,'full_bid')
        self.assertEqual(a.objective_gross_eur,b.objective_gross_eur)
        self.assertEqual(a.soc_trace_mwh,b.soc_trace_mwh)

    def test_fractional_award_and_cross_zero(self):
        _,r=self.solve(.333,baseline=-10,up=100,down=40)
        self.assertTrue(r.feasible,r.message)
        # Down: -23.32 MW for .05h; up: +23.3 MW for .1h; idle: -10 MW for .1h.
        expected=100+23.32*.05*.92-23.3*.1/.92+10*.1*.92
        self.assertAlmostEqual(r.soc_trace_mwh['seg-a'][-1],expected)

    def test_rolling_cash_physics_restore_and_mode_identity(self):
        inp,end=daily(days=3)
        inp=replace(inp,qhs=tuple(replace(q,alpha_up=.2,alpha_down=.1,
            afrr_award_rate_up=.5,afrr_award_rate_down=.25,
            afrr_activation_price_up_eur_per_mwh=100,afrr_activation_price_down_eur_per_mwh=-10) for q in inp.qhs))
        settings=dict(execution_end=end,daily_efc_limit=2.,activation_capacity_basis='proxy_awarded',
            time_limit_seconds=10,history_mode='delta',capacity_award_sensitivity=True)
        e=PerfectEngine(inp,**settings)
        self.assertTrue(e.step(),e.failure)
        cp=e.checkpoint()
        r=PerfectEngine.restore(inp,cp,**settings)
        with self.assertRaises(ValueError):
            PerfectEngine.restore(inp,cp,**dict(settings,activation_capacity_basis='full_bid'))
        e.run();r.run()
        self.assertIsNone(e.failure);self.assertIsNone(r.failure)
        self.assertEqual(e._ledger.total_cash_eur,r._ledger.total_cash_eur)
        self.assertAlmostEqual(e._soc,10,places=5)
        self.assertEqual(e.report()['activation_capacity_basis'],'proxy_awarded')

    def test_invalid_basis(self):
        with self.assertRaises(ValueError): self.solve(.5,'bad')
