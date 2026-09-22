"""Equivalence and boundary tests for the compact signed-contract MILP."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from src.es_synthetic_market import ContractInput, FixedCommitment, SyntheticMarketInput, solve_joint
from tests.test_es_synthetic_market_core import make_contract, make_qh


UTC = timezone.utc


class TestNetContractFormulation(unittest.TestCase):
    def test_one_signed_contract_replaces_sell_buy_and_contract_binary(self):
        start = datetime(2025, 1, 1, tzinfo=UTC)
        qh = make_qh("q", start)
        inp = SyntheticMarketInput(
            (qh,), (make_contract(qh, "DA", 25.0),), annual_efc_budget={2025: 600.0},
            reserve_limit_up_mw=0.0, reserve_limit_down_mw=0.0,
            input_id="ES_SYNTHETIC_MARKET_NET_CAPTURE",
        )
        captured = {}

        def capture(**kwargs):
            captured.update(kwargs)
            return SimpleNamespace(x=None, status=2, message="capture")

        with patch("scipy.optimize.milp", side_effect=capture):
            result = solve_joint(inp)
        self.assertFalse(result.success)
        self.assertEqual(len(captured["c"]), 5)  # net + charge/discharge/mode/SOC
        self.assertEqual(captured["bounds"].lb[0], -100.0)
        self.assertEqual(captured["bounds"].ub[0], 100.0)
        self.assertEqual(np.count_nonzero(captured["integrality"]), 1)

    def test_negative_price_buy_and_positive_price_sell_reconstruct_public_orders(self):
        start = datetime(2025, 1, 1, tzinfo=UTC)
        q0 = make_qh("q0", start)
        q1 = make_qh("q1", start + timedelta(minutes=15))
        inp = SyntheticMarketInput(
            (q0, q1),
            (make_contract(q0, "DA", -100.0), make_contract(q1, "DA", 100.0)),
            annual_efc_budget={2025: 600.0}, eta_charge=1.0, eta_discharge=1.0,
            e_initial_mwh=60.0, e_terminal_mwh=60.0,
            reserve_limit_up_mw=0.0, reserve_limit_down_mw=0.0,
            input_id="ES_SYNTHETIC_MARKET_NET_NEGATIVE_PRICE",
        )
        result = solve_joint(inp)
        self.assertTrue(result.success, result.message)
        self.assertGreater(result.contract_trades[0]["buy_mw"], 0.0)
        self.assertEqual(result.contract_trades[0]["sell_mw"], 0.0)
        self.assertGreater(result.contract_trades[1]["sell_mw"], 0.0)
        self.assertEqual(result.contract_trades[1]["buy_mw"], 0.0)

    def test_fixed_objective_anchor_preserves_fun_dual_bound_and_public_trade(self):
        start = datetime(2025, 1, 1, tzinfo=UTC)
        qh = make_qh("q", start)
        contract = make_contract(qh, "DA", 20.0)
        inp = SyntheticMarketInput(
            (qh,), (contract,), annual_efc_budget={2025: 600.0},
            e_initial_mwh=20.0, reserve_limit_up_mw=0.0, reserve_limit_down_mw=0.0,
            input_id="ES_SYNTHETIC_MARKET_NET_OBJECTIVE_ANCHOR",
        )
        # Frozen 5 MW sell contributes -25 EUR to the old minimization target.
        from scipy.optimize import milp as real_milp
        captured = {}

        def return_fake(**kwargs):
            captured.update(kwargs)
            solved = real_milp(**kwargs)
            return SimpleNamespace(
                success=True, status=0, message="fixed anchor", x=solved.x,
                fun=-25.0, mip_gap=0.0, mip_dual_bound=-25.0,
            )

        with patch("scipy.optimize.milp", side_effect=return_fake):
            result = solve_joint(inp, terminal_hard=False, fixed_spot_mw={contract.contract_id: (5.0, 0.0)})
        fixed_columns = np.flatnonzero(captured["bounds"].lb == captured["bounds"].ub)
        self.assertIn(-25.0, captured["c"][fixed_columns])
        self.assertAlmostEqual(result.solver_objective_min_eur, -25.0)
        self.assertAlmostEqual(result.profit_upper_bound_eur, 25.0)
        self.assertAlmostEqual(result.absolute_gap_eur, 0.0)
        self.assertEqual(result.contract_trades[0]["sell_mw"], 5.0)
        self.assertEqual(result.contract_trades[0]["buy_mw"], 0.0)

    def test_fractional_frozen_integer_reserve_remains_infeasible(self):
        start = datetime(2025, 1, 1, tzinfo=UTC)
        qh = make_qh("q", start, cap_up=1.0)
        inp = SyntheticMarketInput(
            (qh,), (), annual_efc_budget={2025: 600.0},
            input_id="ES_SYNTHETIC_MARKET_NET_FRACTIONAL_RESERVE",
        )
        result = solve_joint(inp, fixed_reserve_mw={qh.qh_id: (0.5, 0.0)})
        self.assertFalse(result.success)
        self.assertFalse(result.feasible)

    def test_capacity_anchor_with_salvage_preserves_nonzero_dual_gap(self):
        start = datetime(2025, 1, 1, tzinfo=UTC)
        qh = make_qh("q", start, cap_up=5.0, cap_down=7.0)
        inp = SyntheticMarketInput(
            (qh,), (), annual_efc_budget={2025: 600.0}, e_initial_mwh=20.0,
            input_id="ES_SYNTHETIC_MARKET_NET_CAPACITY_ANCHOR",
        )
        # Frozen new capacity contributes -31 to the minimization target;
        # salvage contributes -80 at SOC=20.  A dual bound two EUR lower must
        # therefore restore a 33 EUR profit bound and a 2 EUR absolute gap.
        from scipy.optimize import milp as real_milp
        captured = {}

        def return_fake(**kwargs):
            captured.update(kwargs)
            solved = real_milp(**kwargs)
            return SimpleNamespace(
                success=False, status=1, message="time limit", x=solved.x,
                fun=-111.0, mip_gap=2.0 / 111.0, mip_dual_bound=-113.0,
            )

        with patch("scipy.optimize.milp", side_effect=return_fake):
            result = solve_joint(
                inp, terminal_hard=False, salvage_price_eur_per_mwh=4.0,
                terminal_reference_mwh=20.0, fixed_reserve_mw={qh.qh_id: (2.0, 3.0)},
                experimental_a1_a3=True,
            )
        fixed_columns = np.flatnonzero(captured["bounds"].lb == captured["bounds"].ub)
        # A1 also substitutes the fixed SOC, so the one objective anchor now
        # carries both the -31 capacity term and the -80 salvage term.
        self.assertIn(-111.0, captured["c"][fixed_columns])
        self.assertAlmostEqual(result.objective_gross_eur, 31.0)
        self.assertAlmostEqual(result.salvage_eur, 0.0)
        self.assertAlmostEqual(result.profit_upper_bound_eur, 33.0)
        self.assertAlmostEqual(result.absolute_gap_eur, 2.0)
        self.assertAlmostEqual(result.residuals["objective_cash_consistency_abs"], 0.0)

    def test_final_result_node_cap_survives_grid_limit_above_100(self):
        start = datetime(2025, 1, 1, tzinfo=UTC)
        qh = make_qh("q", start)
        contracts = tuple(
            ContractInput(
                f"DA-{i}", "DA", start, start, start, qh.end_utc, 100.0,
                {qh.qh_id: 1.0},
            )
            for i in range(3)
        )
        inp = SyntheticMarketInput(
            (qh,), contracts, fixed_commitments=(FixedCommitment("q", baseline_mw=-100.0),),
            annual_efc_budget={2025: 600.0}, charge_mw=200.0, discharge_mw=200.0,
            grid_export_mw=200.0, grid_import_mw=200.0,
            e_initial_mwh=190.0,
            reserve_limit_up_mw=0.0, reserve_limit_down_mw=0.0,
            input_id="ES_SYNTHETIC_MARKET_NET_RESULT_NODE_CAP",
        )
        # Override only this test window's prorated budget so the final event
        # position cap, rather than one-QH throughput coverage, binds at the
        # optimum.  Without that event row the profitable net position is 300.
        result = solve_joint(inp, terminal_hard=False, remaining_annual_efc={2025: 600.0})
        self.assertTrue(result.success, result.message)
        net = sum(row["sell_mw"] - row["buy_mw"] for row in result.contract_trades)
        self.assertAlmostEqual(net, 200.0, places=7)
        self.assertAlmostEqual(result.qh_baseline_mw["q"], 100.0, places=7)
        self.assertLessEqual(result.residuals["result_node_spot_position_violation_max"], 1e-7)

    def test_tolerance_only_negative_reserve_headroom_is_not_dropped(self):
        start = datetime(2025, 1, 1, tzinfo=UTC)
        qh = make_qh("q", start)
        inp = SyntheticMarketInput(
            (qh,), (), fixed_commitments=(FixedCommitment("q", reserve_up_mw=100.0 + 5e-10),),
            annual_efc_budget={2025: 600.0}, reserve_limit_up_mw=100.0,
            input_id="ES_SYNTHETIC_MARKET_NET_NEGATIVE_HEADROOM",
        )
        result = solve_joint(inp)
        self.assertFalse(result.success)


if __name__ == "__main__":
    unittest.main()
