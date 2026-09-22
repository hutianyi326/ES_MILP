"""Synthetic-only tests for the Spain DA/IDA/aFRR joint core.

No raw files, credentials, network calls, or historical data are used here.
"""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from src.es_synthetic_market import (
    ContractInput,
    FixedCommitment,
    QHInput,
    SyntheticMarketInput,
    solve_joint,
    solve_joint_both_orders,
)


UTC = timezone.utc


def make_qh(
    qh_id: str,
    start: datetime,
    *,
    segment: str = "seg-a",
    year: int = 2025,
    alpha_up: float = 0.0,
    alpha_down: float = 0.0,
    cap_up: float = 0.0,
    cap_down: float = 0.0,
    act_up: float = 0.0,
    act_down: float = 0.0,
) -> QHInput:
    return QHInput(
        qh_id=qh_id,
        start_utc=start,
        end_utc=start + timedelta(minutes=15),
        segment_id=segment,
        madrid_year=year,
        alpha_up=alpha_up,
        alpha_down=alpha_down,
        afrr_capacity_price_up_eur_per_mw_qh=cap_up,
        afrr_capacity_price_down_eur_per_mw_qh=cap_down,
        afrr_activation_price_up_eur_per_mwh=act_up,
        afrr_activation_price_down_eur_per_mwh=act_down,
        afrr_gate_close_utc=start,
        afrr_result_release_utc=start,
    )


def make_contract(qh: QHInput, market: str, price: float, suffix: str = "") -> ContractInput:
    return ContractInput(
        contract_id=f"{market}-{qh.qh_id}{suffix}",
        market=market,
        gate_close_utc=qh.start_utc,
        result_release_utc=qh.start_utc,
        delivery_start_utc=qh.start_utc,
        delivery_end_utc=qh.end_utc,
        price_eur_per_mwh=price,
        qh_weights={qh.qh_id: 1.0},
    )


def make_input(qhs, prices, *, fixed=(), budget=600.0, contracts_both=True):
    contracts = []
    for qh, price in zip(qhs, prices):
        contracts.append(make_contract(qh, "DA", price))
        if contracts_both:
            contracts.append(make_contract(qh, "IDA", price, suffix="-IDA"))
    return SyntheticMarketInput(
        qhs=tuple(qhs),
        contracts=tuple(contracts),
        fixed_commitments=tuple(fixed),
        annual_efc_budget={2025: budget},
        input_id="ES_SYNTHETIC_MARKET_TEST",
    )


class TestSyntheticMarketCore(unittest.TestCase):
    def test_full_joint_da_ida_arbitrage_and_cash_audit(self):
        base = datetime(2025, 1, 1, tzinfo=UTC)
        qhs = (make_qh("q0", base), make_qh("q1", base + timedelta(minutes=15)))
        result = solve_joint(make_input(qhs, (-10.0, 100.0)), "U")
        self.assertTrue(result.success, result.message)
        self.assertGreater(result.cash_breakdown_eur["DA_energy"] + result.cash_breakdown_eur["IDA_energy"], 0.0)
        self.assertAlmostEqual(
            result.objective_gross_eur,
            sum(result.cash_breakdown_eur[key] for key in ("DA_energy", "IDA_energy", "capacity", "activation", "fixed")),
            places=5,
        )
        self.assertNotIn("energy", result.cash_breakdown_eur)
        self.assertLessEqual(result.residuals["annual_efc_used_2025"], 600.0 + 1e-7)
        self.assertLessEqual(result.residuals["terminal_soc_abs_max"], 1e-6)

    def test_both_fixed_orders_are_separate_joint_solves(self):
        base = datetime(2025, 1, 1, tzinfo=UTC)
        qhs = (
            make_qh("q0", base, alpha_up=0.2, alpha_down=0.3, cap_up=5.0, cap_down=4.0, act_up=10.0, act_down=-3.0),
            make_qh("q1", base + timedelta(minutes=15), alpha_up=0.1, alpha_down=0.2, cap_up=5.0, cap_down=4.0, act_up=10.0, act_down=-3.0),
        )
        results = solve_joint_both_orders(make_input(qhs, (0.0, 0.0)))
        self.assertEqual(set(results), {"U", "D"})
        self.assertTrue(results["U"].success, results["U"].message)
        self.assertTrue(results["D"].success, results["D"].message)
        self.assertNotEqual(results["U"].order_mode, results["D"].order_mode)

    def test_activation_cash_and_actual_power_trace_are_present(self):
        base = datetime(2025, 1, 1, tzinfo=UTC)
        qhs = (
            make_qh("q0", base, alpha_up=0.5, alpha_down=0.0, cap_up=10.0, act_up=20.0),
            make_qh("q1", base + timedelta(minutes=15), alpha_up=0.0, alpha_down=0.5, cap_down=10.0, act_down=8.0),
        )
        result = solve_joint(make_input(qhs, (-20.0, 80.0)), "U")
        self.assertTrue(result.success, result.message)
        self.assertIn("activation", result.cash_breakdown_eur)
        self.assertEqual(len(result.qh_power_trace_mw["q0"]), 2)
        self.assertEqual(len(result.qh_power_trace_mw["q1"]), 2)

    def test_fixed_reserve_cash_is_counted_once_and_limits_are_per_direction(self):
        base = datetime(2025, 1, 1, tzinfo=UTC)
        qh = make_qh("q0", base, cap_up=2.0, cap_down=3.0)
        fixed = FixedCommitment("q0", baseline_mw=0.0, reserve_up_mw=30.0, reserve_down_mw=20.0, fixed_energy_cash_eur=7.0)
        result = solve_joint(make_input((qh,), (0.0,), fixed=(fixed,)), "U")
        self.assertTrue(result.success, result.message)
        self.assertLessEqual(result.reserve_up_mw["q0"], 100.0 + 1e-6)
        self.assertLessEqual(result.reserve_down_mw["q0"], 100.0 + 1e-6)
        self.assertGreaterEqual(result.cash_breakdown_eur["fixed"], 7.0)
        self.assertAlmostEqual(
            result.objective_gross_eur,
            sum(result.cash_breakdown_eur[key] for key in ("DA_energy", "IDA_energy", "capacity", "activation", "fixed")),
            places=5,
        )

    def test_cross_gap_segments_reset_soc_but_share_annual_budget(self):
        base = datetime(2025, 1, 1, tzinfo=UTC)
        qhs = (
            make_qh("a0", base, segment="a"), make_qh("a1", base + timedelta(minutes=15), segment="a"),
            make_qh("b0", base + timedelta(hours=1), segment="b"), make_qh("b1", base + timedelta(hours=1, minutes=15), segment="b"),
        )
        result = solve_joint(make_input(qhs, (-10.0, 100.0, -10.0, 100.0), budget=0.25), "U")
        self.assertTrue(result.success, result.message)
        self.assertEqual(set(result.soc_trace_mwh), {"a", "b"})
        self.assertLessEqual(result.residuals["annual_efc_used_2025"], 0.25 + 1e-6)

    def test_annual_budget_is_capped_by_covered_madrid_time(self):
        base = datetime(2025, 1, 1, tzinfo=UTC)
        qhs = (make_qh("q0", base), make_qh("q1", base + timedelta(minutes=15)))
        inp = make_input(qhs, (0.0, 0.0), budget=600.0)
        expected = 600.0 * 0.5 / 8760.0
        self.assertAlmostEqual(inp.coverage_derived_efc_budget[2025], expected, places=12)
        self.assertAlmostEqual(inp.effective_annual_efc_budget[2025], expected, places=12)

    def test_simultaneous_result_node_is_not_ordered_by_contract_id(self):
        base = datetime(2025, 1, 1, tzinfo=UTC)
        qh = make_qh("q0", base)
        contracts = tuple(
            ContractInput(
                contract_id=contract_id,
                market="DA",
                gate_close_utc=base,
                result_release_utc=base,
                delivery_start_utc=base,
                delivery_end_utc=qh.end_utc,
                price_eur_per_mwh=price,
                qh_weights={qh.qh_id: 1.0},
            )
            for contract_id, price in (("sell-a", 10.0), ("sell-b", 10.0), ("buy-c", -10.0), ("buy-d", -10.0))
        )
        inp = SyntheticMarketInput(
            qhs=(qh,), contracts=contracts, annual_efc_budget={2025: 600.0}, input_id="ES_SYNTHETIC_MARKET_RESULT_PREFIX"
        )
        result = solve_joint(inp, "U")
        self.assertTrue(result.success, result.message)
        self.assertLessEqual(abs(result.qh_baseline_mw["q0"]), 100.0 + 1e-6)
        self.assertLessEqual(result.residuals["result_node_spot_position_violation_max"], 1e-6)
        self.assertAlmostEqual(result.objective_gross_eur, 1000.0, places=5)

    def test_strict_input_gate_rejects_non_synthetic_and_unmappable_data(self):
        base = datetime(2025, 1, 1, tzinfo=UTC)
        qh = make_qh("q0", base)
        with self.assertRaises(ValueError):
            SyntheticMarketInput(qhs=(qh,), contracts=(make_contract(qh, "DA", 1.0),), annual_efc_budget={2025: 1.0}, input_id="HISTORICAL")
        with self.assertRaises(ValueError):
            make_qh("bad", base, alpha_up=0.8, alpha_down=0.3)
        bad_contract = ContractInput(
            contract_id="bad", market="DA", gate_close_utc=base - timedelta(hours=2),
            result_release_utc=base - timedelta(hours=1), delivery_start_utc=base,
            delivery_end_utc=base + timedelta(minutes=30), price_eur_per_mwh=1.0, qh_weights={"q0": 1.0},
        )
        with self.assertRaises(ValueError):
            SyntheticMarketInput(qhs=(qh,), contracts=(bad_contract,), annual_efc_budget={2025: 1.0}, input_id="ES_SYNTHETIC_MARKET_BAD")

    def test_contract_event_order_and_qh_duration_are_checked(self):
        base = datetime(2025, 1, 1, tzinfo=UTC)
        qh = make_qh("q0", base)
        with self.assertRaises(ValueError):
            ContractInput("bad", "DA", base, base - timedelta(minutes=1), base, qh.end_utc, 1.0, {"q0": 1.0})
        with self.assertRaises(ValueError):
            bad = ContractInput("bad2", "DA", base - timedelta(hours=2), base - timedelta(hours=1), base, base + timedelta(minutes=30), 1.0, {"q0": 1.0})
            SyntheticMarketInput(qhs=(qh,), contracts=(bad,), annual_efc_budget={2025: 1.0}, input_id="ES_SYNTHETIC_MARKET_BAD2")

    def test_qh_level_reserve_headroom_is_hard_even_when_alpha_is_zero(self):
        base = datetime(2025, 1, 1, tzinfo=UTC)
        qh = make_qh("q0", base, alpha_up=0.0, alpha_down=0.0)
        fixed = FixedCommitment("q0", baseline_mw=90.0, reserve_up_mw=20.0)
        inp = SyntheticMarketInput(qhs=(qh,), contracts=(), fixed_commitments=(fixed,), annual_efc_budget={2025: 600.0}, input_id="ES_SYNTHETIC_MARKET_HEADROOM")
        result = solve_joint(inp, "U")
        self.assertFalse(result.success)

    def test_down_activation_can_cross_zero_and_remains_a_physical_charge(self):
        base = datetime(2025, 1, 1, tzinfo=UTC)
        qh0 = make_qh("q0", base)
        qh1 = make_qh("q1", base + timedelta(minutes=15), alpha_down=1.0)
        qh2 = make_qh("q2", base + timedelta(minutes=30))
        contracts = ()
        fixed = (
            FixedCommitment("q0", baseline_mw=-20.0),
            FixedCommitment("q1", baseline_mw=10.0, reserve_down_mw=30.0),
            FixedCommitment("q2", baseline_mw=33.856),
        )
        inp = SyntheticMarketInput(qhs=(qh0, qh1, qh2), contracts=contracts, fixed_commitments=fixed, annual_efc_budget={2025: 600.0}, input_id="ES_SYNTHETIC_MARKET_CROSS_ZERO")
        result = solve_joint(inp, "U")
        self.assertTrue(result.success, result.message)
        self.assertAlmostEqual(result.qh_power_trace_mw["q1"][0], -20.0, places=5)

    def test_missing_afrr_event_and_oversized_budget_are_rejected(self):
        base = datetime(2025, 1, 1, tzinfo=UTC)
        qh = QHInput("q0", base, base + timedelta(minutes=15), "seg-a", 2025, 0.0, 0.0)
        contract = make_contract(qh, "DA", 0.0)
        with self.assertRaises(ValueError):
            SyntheticMarketInput(qhs=(qh,), contracts=(contract,), annual_efc_budget={2025: 1.0}, input_id="ES_SYNTHETIC_MARKET_NO_EVENT")
        qh_ok = make_qh("q0", base)
        with self.assertRaises(ValueError):
            SyntheticMarketInput(qhs=(qh_ok,), contracts=(make_contract(qh_ok, "DA", 0.0),), annual_efc_budget={2025: 600.1}, input_id="ES_SYNTHETIC_MARKET_BIG_BUDGET")

    def test_qh_reverse_order_is_rejected_instead_of_reordering_soc(self):
        base = datetime(2025, 1, 1, tzinfo=UTC)
        q0 = make_qh("q0", base)
        q1 = make_qh("q1", base + timedelta(minutes=15))
        with self.assertRaises(ValueError):
            SyntheticMarketInput(
                qhs=(q1, q0),
                contracts=(make_contract(q1, "DA", 0.0), make_contract(q0, "DA", 0.0)),
                annual_efc_budget={2025: 1.0},
                input_id="ES_SYNTHETIC_MARKET_REVERSE",
            )

    def test_independent_audit_rejects_negative_physics(self):
        base = datetime(2025, 1, 1, tzinfo=UTC)
        qh = make_qh("q0", base)
        inp = make_input((qh,), (0.0,), contracts_both=False)
        # One signed contract + two reserves + four physical variables.
        negative_physics = np.zeros(7)
        negative_physics[3] = -1.0
        negative_physics[4] = -1.0
        negative_physics[6] = 10.0
        fake_negative = SimpleNamespace(success=True, status=0, message="tampered", x=negative_physics, fun=0.0, mip_gap=0.0, mip_dual_bound=0.0)
        with patch("scipy.optimize.milp", return_value=fake_negative):
            with self.assertRaises(AssertionError):
                solve_joint(inp, "U")

    def test_feasible_time_limit_solution_is_reported_not_discarded(self):
        base = datetime(2025, 1, 1, tzinfo=UTC)
        qh = make_qh("q0", base)
        inp = SyntheticMarketInput(qhs=(qh,), contracts=(), annual_efc_budget={2025: 1.0}, input_id="ES_SYNTHETIC_MARKET_TIME_LIMIT")
        from scipy.optimize import milp as real_milp
        def feasible_time_limit(**kwargs):
            solved = real_milp(**kwargs)
            return SimpleNamespace(
                success=False, status=1, message="time limit", x=solved.x,
                fun=solved.fun, mip_gap=0.5, mip_dual_bound=solved.fun,
            )
        with patch("scipy.optimize.milp", side_effect=feasible_time_limit):
            result = solve_joint(inp, "U")
        self.assertTrue(result.success)
        self.assertTrue(result.feasible)
        self.assertFalse(result.proven_optimal)
        self.assertAlmostEqual(result.raw_solver_gap, 0.5)


if __name__ == "__main__":
    unittest.main()
