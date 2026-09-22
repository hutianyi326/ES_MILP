"""Independent integration acceptance regressions for synthetic C delivery."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch
import unittest

from tests.test_es_synthetic_market_rolling import fixture, TZ
from src.es_synthetic_market import RollingEngine, solve_rolling
from src.es_synthetic_market.diagnostics import DiagnosticQH, DiagnosticSnapshot, replay_pressure
from src.es_synthetic_market.diagnostics import build_frozen_snapshot
from src.es_synthetic_market.integration import run_four_combinations, _physical


def dq(index=0, baseline=0., up=20., down=20., au=.2, ad=.4):
    start = datetime(2025, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=15 * index)
    return DiagnosticQH(str(index), start, start + timedelta(minutes=15),
                        "a", 2025, baseline, up, down, au, ad)


class TestCPressureAnchors(unittest.TestCase):
    def test_missing_budget_and_wrong_year_rejected(self):
        q = dq()
        with self.assertRaises(ValueError): DiagnosticSnapshot(q, 100., q.start_utc)
        with self.assertRaises(ValueError): replace(q, madrid_year=2024)

    def test_year_cycle_shortfall_fails_and_single_direction_alternation_not_run(self):
        q = dq(up=20., down=0., au=1., ad=0.)
        out = replay_pressure(DiagnosticSnapshot(q, 100., q.start_utc,
             prior_efc_by_year={2025:.9}, efc_budget_by_year={2025:.9})).paths
        self.assertFalse(out["main"].feasible)
        self.assertGreater(out["main"].efc_budget_shortfall_by_year[2025], 0.)
        self.assertEqual(out["down_then_up"].status, "NOT_RUN")
        self.assertEqual(out["down_then_up"].records, ())

    def test_tail_year_boundary_and_zero_alpha_headroom(self):
        a = replace(dq(up=0., down=0., au=0., ad=0.),
                    start_utc=datetime(2025,12,31,22,45,tzinfo=timezone.utc),
                    end_utc=datetime(2025,12,31,23,0,tzinfo=timezone.utc))
        b = replace(dq(1, baseline=20., up=0., down=0., au=0., ad=0.),
                    start_utc=a.end_utc, end_utc=a.end_utc+timedelta(minutes=15), madrid_year=2026)
        out = replay_pressure(DiagnosticSnapshot(a, 100., a.start_utc, (b,),
            efc_budget_by_year={2025:0.,2026:1.})).paths["main"]
        self.assertEqual(out.efc_used_by_year[2025], 0.)
        self.assertAlmostEqual(out.efc_used_by_year[2026],5/.92/360)
        q = dq(baseline=90.,up=20.,down=0.,au=0.,ad=0.)
        out = replay_pressure(DiagnosticSnapshot(q,100.,q.start_utc,
            efc_budget_by_year={2025:600.})).paths["none"]
        self.assertFalse(out.power_feasible)
        self.assertEqual(out.max_power_violation_mw,10.)

    def test_low_soc_hand_calculated_contact_and_no_clipping(self):
        q = dq()
        snap = DiagnosticSnapshot(q, 11., q.start_utc, efc_budget_by_year={2025: 600.})
        out = replay_pressure(snap).paths["main"]
        self.assertAlmostEqual(out.min_raw_soc_mwh, 11 - 1 / .92)
        self.assertAlmostEqual(out.first_boundary_contact["lower"], 2.76)
        self.assertAlmostEqual(out.first_violation_onset["lower"], 2.76)
        self.assertFalse(out.feasible)
        self.assertAlmostEqual(out.final_soc_mwh, 11 - 1 / .92 + 2 * .92)

    def test_upper_soc_alternate_order_contact(self):
        q = dq()
        snap = DiagnosticSnapshot(q, 189., q.start_utc, efc_budget_by_year={2025: 600.})
        out = replay_pressure(snap, order_mode="D").paths["main"]
        self.assertAlmostEqual(out.max_raw_soc_mwh, 190.84)
        self.assertAlmostEqual(out.first_violation_onset["upper"], 60 / (20 * .92))
        self.assertFalse(out.feasible)

    def test_no_activation_pulse_safe_but_nonzero_alpha_tail_fails(self):
        a = dq(up=0., down=0., au=0., ad=0.)
        b = dq(1, up=20., down=0., au=1., ad=0.)
        c = dq(2, up=0., down=0., au=0., ad=0.)
        snap = DiagnosticSnapshot(a, 11., a.start_utc, (b, c),
                                  efc_budget_by_year={2025: 600.})
        out = replay_pressure(snap).paths["none"]
        self.assertAlmostEqual(out.records[0]["soc_end_mwh"], 11.)
        self.assertAlmostEqual(out.final_soc_mwh, 11 - 5 / .92)
        self.assertEqual(out.validation_minutes, 45.)
        self.assertAlmostEqual(out.first_violation_onset["lower"], 17.76)
        self.assertEqual(out.records[-1]["end_utc"], c.end_utc.isoformat())
        self.assertFalse(out.feasible)
        self.assertAlmostEqual(out.recovery["needed_dc_mwh"], 5 / .92 - 1)
        self.assertAlmostEqual(out.recovery["ideal_minute"], (5 / .92 - 1) / 92 * 60)

    def test_invalid_tiny_alpha_is_rejected_not_normalized(self):
        for au, ad in ((-.00000000001, 0.), (.5, .50000000001)):
            with self.assertRaises(ValueError):
                dq(au=au, ad=ad)

    def test_tiny_positive_activation_retains_time_and_energy(self):
        q = dq(up=100., down=0., au=1e-10, ad=0.)
        out = replay_pressure(DiagnosticSnapshot(q, 100., q.start_utc,
                              efc_budget_by_year={2025: 600.})).paths["main"]
        self.assertEqual(len(out.records), 2)
        self.assertAlmostEqual(out.validation_minutes, 15.)
        self.assertGreater(out.dc_throughput_mwh, 0.)


class TestCIntegrationBoundaries(unittest.TestCase):
    def test_duplicate_unknown_incomplete_mismatched_orders_rejected(self):
        inp=fixture(datetime(2025,1,1,tzinfo=TZ),1)
        cid=inp.contracts[0].contract_id
        spot=dict(contract_id=cid,sell_mw=20.,buy_mw=0.,status="awarded")
        reserve=dict(qh_id="0",up_mw=20.,down_mw=0.,status="awarded")
        for kind,row,idfield in (("spot",spot,"contract_id"),("reserve",reserve,"qh_id")):
            missing=dict(row);missing.pop("sell_mw" if kind=="spot" else "up_mw")
            bad_cases=([row,row], [dict(row,**{idfield:"unknown"})], [missing], {"wrong":row})
            for rows in bad_cases:
                with self.subTest(kind=kind,rows=rows), self.assertRaises(ValueError):
                    build_frozen_snapshot(inp.qhs,inp.contracts,rows if kind=="spot" else [],
                        rows if kind=="reserve" else [],0,initial_soc_mwh=11.,efc_budget_by_year={2025:600.})

    def test_offsetting_gross_orders_change_order_fingerprint(self):
        inp=fixture(datetime(2025,1,1,tzinfo=TZ),1)
        c1=inp.contracts[0];c2=replace(c1,contract_id="offset",market="IDA")
        def snapshot(amount):
            return build_frozen_snapshot(inp.qhs,(c1,c2),[
                dict(contract_id=c1.contract_id,sell_mw=amount,buy_mw=0.,status="awarded"),
                dict(contract_id=c2.contract_id,sell_mw=0.,buy_mw=amount,status="awarded")],
                [],0,initial_soc_mwh=11.,efc_budget_by_year={2025:600.})
        a,b=snapshot(10.),snapshot(20.)
        self.assertEqual(a.qh.baseline_mw,b.qh.baseline_mw)
        self.assertNotEqual(a.source_order_hash,b.source_order_hash)
        self.assertEqual(len(a.visible_orders["spot"]),2)

    def test_other_order_report_contains_intraperiod_risk_metrics(self):
        inp=fixture(datetime(2025,1,1,tzinfo=TZ),1)
        inp=replace(inp,qhs=(replace(inp.qhs[0],alpha_up=.2,alpha_down=.4),),
                    e_initial_mwh=11.,e_terminal_mwh=11.-1/.92+2*.92)
        out=_physical(inp,{"0":0.},{"0":20.},{"0":20.},"U")
        self.assertAlmostEqual(out["max_lower_violation_mwh"],1/.92-1.)
        self.assertIsNotNone(out["first_violation_onset"]["lower"])
        self.assertIn("recovery",out["segments"][inp.qhs[0].segment_id])
        self.assertIn("efc_budget_shortfall_by_year",out)

    def test_four_combinations_stress_failure_preserves_main_cash(self):
        inp = fixture(datetime(2025,1,1,23,45,tzinfo=TZ),2,reserve=True)
        inp = replace(inp,qhs=tuple(replace(q,afrr_capacity_price_up_eur_per_mw_qh=10.,
                       afrr_capacity_price_down_eur_per_mw_qh=10.) for q in inp.qhs))
        out = run_four_combinations(inp)
        self.assertEqual(set(out["combinations"]),{"joint_full-U","joint_full-D","rolling7-U","rolling7-D"})
        for r in out["combinations"].values():
            self.assertEqual(r["main_status"],"PASS",r.get("main_audit"))
            self.assertGreater(r["valid_gross_eur"],0.)
            self.assertEqual(r["diagnostic_isolation"],"PASS")
            self.assertEqual(len(r["pressure"]),2)
            self.assertTrue(any(p["status"]=="FAIL" for snap in r["pressure"] for p in snap["paths"].values()))
            self.assertFalse(r["pressure_cash_included"])

    def test_snapshot_keeps_pending_tail_and_excludes_later_rescue(self):
        inp = fixture(datetime(2025,1,1,tzinfo=TZ),3)
        q = inp.qhs
        contracts = (replace(inp.contracts[2],contract_id="pending",gate_close_utc=q[0].start_utc,
                            result_release_utc=q[2].start_utc),
                     replace(inp.contracts[1],contract_id="rescue",gate_close_utc=q[0].start_utc+timedelta(seconds=1)))
        orders = [dict(contract_id="pending",sell_mw=20.,buy_mw=0.,status="pending"),
                  dict(contract_id="rescue",sell_mw=0.,buy_mw=100.,status="awarded")]
        snap = build_frozen_snapshot(q,contracts,orders,[],0,initial_soc_mwh=11.,efc_budget_by_year={2025:600.})
        self.assertEqual(len(snap.tail),2)
        self.assertEqual(snap.tail[0].baseline_mw,0.)
        self.assertEqual(snap.tail[1].baseline_mw,20.)
        self.assertFalse(replay_pressure(snap).paths["none"].feasible)
        orders[0]["sell_mw"] = 21.
        changed = build_frozen_snapshot(q,contracts,orders,[],0,initial_soc_mwh=11.,efc_budget_by_year={2025:600.})
        self.assertNotEqual(snap.source_order_hash,changed.source_order_hash)

    def test_later_window_failure_keeps_prior_state_but_invalidates_total(self):
        inp = fixture(datetime(2025, 1, 1, 23, 45, tzinfo=TZ), 2,
                      lambda i: 10 if i == 0 else 100)
        engine = RollingEngine(inp)
        self.assertTrue(engine.step(), engine.failure)
        before = engine.checkpoint()["state"]
        with patch("src.es_synthetic_market.rolling.solve_joint",
                   return_value=SimpleNamespace(feasible=False, message="C injected failure")):
            result = engine.run()
        self.assertFalse(result.success)
        self.assertIsNone(result.execution_cash_eur)
        self.assertEqual(len(result.windows), 1)
        after = engine.checkpoint()["state"]
        for key in ("soc", "index", "used", "orders", "reserves", "ledger", "windows"):
            self.assertEqual(before[key], after[key], key)

    def test_real_gap_resets_soc_without_reissuing_annual_budget(self):
        a = fixture(datetime(2025, 1, 1, 23, 30, tzinfo=TZ), 2,
                    lambda i: 0 if i == 0 else 1000)
        b = fixture(datetime(2025, 1, 3, 23, 30, tzinfo=TZ), 2,
                    lambda i: 0 if i == 0 else 100)
        bq = tuple(replace(q, qh_id="b" + q.qh_id, segment_id="segment-b") for q in b.qhs)
        bc = tuple(replace(c, contract_id="b" + c.contract_id,
                           qh_weights={"b" + k: v for k, v in c.qh_weights.items()})
                   for c in b.contracts)
        inp = replace(a, qhs=a.qhs + bq, contracts=a.contracts + bc)
        result = solve_rolling(inp)
        self.assertTrue(result.success, result.failure)
        self.assertEqual(len(result.windows), 2)
        self.assertAlmostEqual(result.windows[0].end_execution_soc_mwh, 10)
        self.assertAlmostEqual(result.windows[1].start_soc_mwh, 10)
        used = result.windows[-1].efc_used_by_year[2025]
        self.assertLessEqual(used, inp.effective_annual_efc_budget[2025] + 1e-6)
        self.assertGreater(result.windows[0].efc_used_by_year[2025], 0)

    def test_day_eight_early_gate_order_is_not_truncated_into_window(self):
        inp = fixture(datetime(2025, 1, 1, tzinfo=TZ), 8 * 96)
        contracts = list(inp.contracts)
        contracts[-1] = replace(contracts[-1], gate_close_utc=inp.qhs[0].start_utc,
                                result_release_utc=inp.qhs[0].start_utc,
                                price_eur_per_mwh=1e6)
        engine = RollingEngine(replace(inp, contracts=tuple(contracts)))
        self.assertTrue(engine.step(), engine.failure)
        order = next(o for o in engine._windows[0].order_snapshot["spot"]
                     if o["contract_id"] == contracts[-1].contract_id)
        self.assertEqual(order["status"], "not_submitted")
        self.assertEqual(order["sell_mw"], 0)
        self.assertEqual(order["buy_mw"], 0)


if __name__ == "__main__":
    unittest.main()
