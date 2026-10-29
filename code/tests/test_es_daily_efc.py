"""Daily EFC: local-date limits, no banking, no annual cap, restart safety."""
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from tests.test_es_synthetic_market_core import make_input, make_qh
from tests.test_es_perfect_v1 import daily
from src.es_synthetic_market.core import solve_joint
from src.es_synthetic_market.perfect import PerfectEngine

TZ=ZoneInfo('Europe/Madrid')
UTC=timezone.utc


class DailyEfcTests(unittest.TestCase):
    def fixed_charge(self, local_times, limit):
        qhs=tuple(make_qh(str(i),t.astimezone(UTC)) for i,t in enumerate(local_times))
        inp=make_input(qhs,[0]*len(qhs),budget=0.,contracts_both=False)
        # 50 MW x .25h x .92 / 360 = .031944 EFC per QH.
        return solve_joint(inp,'D',fixed_spot_mw={c.contract_id:(0,50) for c in inp.contracts},
            fixed_reserve_mw={q.qh_id:(0,0) for q in qhs},terminal_hard=False,
            daily_efc_limit=limit,enforce_annual_efc=False)

    def test_madrid_midnight_not_utc_and_no_carry(self):
        # Same UTC date, different Madrid days: each gets its own allowance.
        t=datetime(2025,1,1,23,45,tzinfo=TZ)
        self.assertTrue(self.fixed_charge([t,t+timedelta(minutes=15)],.04).feasible)
        # Same local day: a .063889 total cannot borrow tomorrow's allowance.
        self.assertFalse(self.fixed_charge([t-timedelta(minutes=15),t],.04).feasible)

    def test_daily_cap_not_scaled_with_dst(self):
        for t in (datetime(2025,3,30,1,tzinfo=TZ),datetime(2025,10,26,1,tzinfo=TZ)):
            with self.subTest(t=t):
                self.assertFalse(self.fixed_charge([t,t+timedelta(minutes=15)],.04).feasible)

    def test_zero_cap_and_invalid_limits(self):
        t=datetime(2025,1,1,12,tzinfo=TZ)
        self.assertFalse(self.fixed_charge([t],0).feasible)
        for value in (-1,float('nan'),float('inf')):
            with self.assertRaises(ValueError):self.fixed_charge([t],value)

    def test_daily_only_can_exceed_legacy_zero_annual_budget(self):
        t=datetime(2025,1,1,12,tzinfo=TZ)
        r=self.fixed_charge([t],.04)
        self.assertTrue(r.feasible,r.message)
        self.assertGreater(r.residuals['annual_efc_used_2025'],0)
        self.assertLessEqual(r.residuals['daily_efc_violation_max'],1e-5)

    def test_activation_consumes_daily_allowance_without_baseline_energy(self):
        q=make_qh('q',datetime(2025,1,1,12,tzinfo=UTC),alpha_up=1.)
        inp=replace(make_input((q,),(0,),contracts_both=False),e_initial_mwh=100)
        options=dict(fixed_spot_mw={inp.contracts[0].contract_id:(0,0)},
            fixed_reserve_mw={'q':(50,0)},terminal_hard=False,enforce_annual_efc=False)
        # Activation physically exports 12.5 MWh; DC throughput is .03774 EFC.
        self.assertTrue(solve_joint(inp,'D',daily_efc_limit=.04,**options).feasible)
        self.assertFalse(solve_joint(inp,'D',daily_efc_limit=.03,**options).feasible)

    def test_rolling_restart_terminal_and_daily_execution(self):
        inp,end=daily(days=4)
        inp=replace(inp,annual_efc_budget={2025:0.})
        settings=dict(execution_end=end,daily_efc_limit=.2,history_mode='delta',time_limit_seconds=10)
        engine=PerfectEngine(inp,**settings)
        self.assertTrue(engine.step(),engine.failure)
        checkpoint=engine.checkpoint()
        with self.assertRaises(ValueError):
            PerfectEngine.restore(inp,checkpoint,**{**settings,'daily_efc_limit':.3})
        restored=PerfectEngine.restore(inp,checkpoint,**settings)
        engine.run();restored.run()
        self.assertIsNone(engine.failure)
        self.assertIsNone(restored.failure)
        self.assertEqual(engine.report()['daily_efc_used'],restored.report()['daily_efc_used'])
        self.assertGreater(engine._used[2025],0.)
        self.assertLessEqual(max(engine.report()['daily_efc_used'].values()),.2+1e-5)
        self.assertAlmostEqual(engine._soc,10.,places=5)
        self.assertIsNone(engine.report()['annual_budget'][2025])

    def test_both_days_in_planning_window_are_constrained(self):
        inp,end=daily(days=4)
        e=PerfectEngine(inp,execution_end=end,daily_efc_limit=.2,time_limit_seconds=10)
        self.assertTrue(e.step(),e.failure)
        r=e._last_result
        totals={}
        for q in e.inp.qhs[:192]:
            p=r.qh_baseline_mw[q.qh_id]
            # This fixture has zero activation, so baseline is physical power.
            d=q.start_utc.astimezone(TZ).date()
            totals[d]=totals.get(d,0)+(max(-p,0)*.92+max(p,0)/.92)*.25/360
        self.assertEqual(len(totals),2)
        self.assertLessEqual(max(totals.values()),.2+1e-5)


if __name__=='__main__':unittest.main()
