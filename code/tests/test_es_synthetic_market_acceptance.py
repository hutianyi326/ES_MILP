"""Independent integration regressions; entirely artificial prices/events."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from types import SimpleNamespace
from unittest.mock import patch
import unittest
import numpy as np
from tests.test_es_synthetic_market_core import make_qh, make_input
from src.es_synthetic_market import ContractInput, FixedCommitment, SyntheticMarketInput, solve_joint

UTC = timezone.utc


class TestMarketAcceptance(unittest.TestCase):
    def test_complete_dst_day_equals_one_day_and_partial_day_fraction(self):
        tz = ZoneInfo("Europe/Madrid")
        for year, month, day, hours in ((2025,3,30,23),(2025,10,26,25),(2026,3,29,23),(2026,10,25,25),(2024,2,29,24)):
            local = datetime(year, month, day, tzinfo=tz)
            start = local.astimezone(UTC)
            end = (local + timedelta(days=1)).astimezone(UTC)
            self.assertEqual((end-start).total_seconds()/3600, hours)
            qhs = tuple(make_qh(str(i),start+timedelta(minutes=15*i),year=year) for i in range(hours*4))
            inp = SyntheticMarketInput(qhs,(),annual_efc_budget={year:600}, input_id="ES_SYNTHETIC_MARKET_DST")
            self.assertAlmostEqual(inp.effective_annual_efc_budget[year],600/(366 if year==2024 else 365),places=10)
            half = replace(inp, qhs=qhs[:2])
            self.assertAlmostEqual(half.effective_annual_efc_budget[year],600*0.5/hours/(366 if year==2024 else 365),places=10)

    def test_distinct_delivery_periods_never_sum_their_mw(self):
        base = datetime(2025,1,1,tzinfo=UTC)
        qhs = tuple(make_qh(str(i),base+timedelta(minutes=15*i)) for i in range(10))
        contracts = tuple(ContractInput(str(i),"DA",base,base,qhs[i].start_utc,qhs[i].end_utc,50,{str(i):1}) for i in (8,9))
        inp = SyntheticMarketInput(qhs,contracts,annual_efc_budget={2025:600},e_initial_mwh=60,eta_charge=1,eta_discharge=1,input_id="ES_SYNTHETIC_MARKET_INDEPENDENT_PERIODS")
        r = solve_joint(inp)
        self.assertTrue(r.feasible)
        self.assertAlmostEqual(r.qh_baseline_mw["8"],100)
        self.assertAlmostEqual(r.qh_baseline_mw["9"],100)

    def test_prefix_limits_are_per_timestamp_and_include_fixed_baseline(self):
        base = datetime(2025,1,1,tzinfo=UTC)
        qhs = tuple(make_qh(str(i),base+timedelta(minutes=15*i)) for i in range(4))
        q = qhs[-1]
        contracts = tuple(ContractInput(str(i),"DA" if i<2 else "IDA",base,base+timedelta(minutes=i+1),q.start_utc,q.end_utc,100 if i<2 else 0,{q.qh_id:1}) for i in range(4))
        inp = SyntheticMarketInput(qhs,contracts,annual_efc_budget={2025:600},reserve_limit_up_mw=0,reserve_limit_down_mw=0,input_id="ES_SYNTHETIC_MARKET_PREFIX")
        r = solve_joint(inp)
        self.assertTrue(r.feasible)
        self.assertAlmostEqual(r.objective_gross_eur,2500,places=5)
        r_fixed = solve_joint(replace(inp,fixed_commitments=(FixedCommitment("3",baseline_mw=90),)))
        self.assertTrue(r_fixed.feasible)
        self.assertAlmostEqual(r_fixed.objective_gross_eur,250,places=5)

    def test_closed_gates_zero_and_injected_afrr_order_rejected(self):
        base = datetime(2025,1,1,tzinfo=UTC)
        q = replace(make_qh("q",base,cap_up=2,cap_down=3),afrr_gate_close_utc=base-timedelta(hours=1),afrr_result_release_utc=base)
        inp = SyntheticMarketInput((q,),(),annual_efc_budget={2025:600},input_id="ES_SYNTHETIC_MARKET_GATE")
        r = solve_joint(inp)
        self.assertAlmostEqual(r.objective_gross_eur,0)
        # Closed reserve gates are constants in the compact formulation; the
        # remaining vector is charge, discharge, operation mode and SOC.
        fake = SimpleNamespace(success=True,status=0,message="tampered",x=np.array([100.,0,0,10]),fun=-200.,mip_gap=0.,mip_dual_bound=-200.)
        with patch("scipy.optimize.milp",return_value=fake):
            with self.assertRaises(AssertionError):
                solve_joint(inp)
        contract = ContractInput("closed","DA",base-timedelta(hours=1),base,base,q.end_utc,-100,{"q":1})
        r2 = solve_joint(replace(inp,contracts=(contract,)))
        self.assertEqual(r2.contract_trades[0]["buy_mw"],0)
        self.assertEqual(r2.contract_trades[0]["sell_mw"],0)

    def test_hour_contract_output_reconstructs_cash_without_duplicate_sum(self):
        base = datetime(2025,1,1,tzinfo=UTC)
        qhs = tuple(make_qh(str(i),base+timedelta(minutes=15*i)) for i in range(4))
        weights={q.qh_id:1 for q in qhs}
        contracts=tuple(ContractInput(m,m,base,base,base,base+timedelta(hours=1),p,weights) for m,p in (("DA",50),("IDA",0)))
        inp=SyntheticMarketInput(qhs,contracts,annual_efc_budget={2025:600},input_id="ES_SYNTHETIC_MARKET_HOUR")
        r=solve_joint(inp)
        self.assertAlmostEqual(r.objective_gross_eur,5000)
        self.assertEqual(len(r.contract_trades),2)
        self.assertAlmostEqual(sum(t["cash_eur"] for t in r.contract_trades),r.objective_gross_eur)
        self.assertAlmostEqual(sum(r.cash_breakdown_eur.values()),r.objective_gross_eur)
        self.assertAlmostEqual(r.contract_trades[0]["sell_mwh"],100)

    def test_year_boundary_preserves_soc(self):
        base=datetime(2025,12,31,22,15,tzinfo=UTC)
        qhs=tuple(make_qh(str(i),base+timedelta(minutes=15*i),year=2025 if i<3 else 2026) for i in range(6))
        inp=SyntheticMarketInput(qhs,(),fixed_commitments=(FixedCommitment("2",baseline_mw=-2),FixedCommitment("3",baseline_mw=1.6928)),annual_efc_budget={2025:600,2026:600},input_id="ES_SYNTHETIC_MARKET_CROSS_YEAR")
        r=solve_joint(inp)
        self.assertTrue(r.feasible)
        self.assertAlmostEqual(r.soc_trace_mwh["seg-a"][2],10.46)
        self.assertAlmostEqual(r.soc_trace_mwh["seg-a"][3],10)

if __name__ == "__main__":
    unittest.main()
