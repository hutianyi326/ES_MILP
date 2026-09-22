"""Correctness anchors for A1 physical substitution, A2 rows and A3 bounds."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import unittest
from unittest.mock import patch

import numpy as np
from scipy.optimize import milp as real_milp
from src.es_synthetic_market import ContractInput, FixedCommitment, SyntheticMarketInput, solve_joint
from src.es_synthetic_market import _baseline_core
from src.es_synthetic_market.core import _interval_add, _interval_scale
from tests.test_es_synthetic_market_core import make_contract, make_qh


UTC = timezone.utc


class A1A3OptimizationTests(unittest.TestCase):
    def test_default_dispatch_preserves_frozen_before_layout_and_behavior(self):
        start = datetime(2025, 1, 1, tzinfo=UTC)
        qh = make_qh("q", start)
        contract = make_contract(qh, "DA", 20.0)
        inp = SyntheticMarketInput(
            (qh,), (contract,), annual_efc_budget={2025: 600.0},
            reserve_limit_up_mw=0.0, reserve_limit_down_mw=0.0,
            input_id="ES_SYNTHETIC_MARKET_A1_A3_DEFAULT_OFF",
        )
        captured = []

        def measured(**kwargs):
            captured.append({
                "c": np.asarray(kwargs["c"]).copy(),
                "integrality": np.asarray(kwargs["integrality"]).copy(),
                "lb": np.asarray(kwargs["bounds"].lb).copy(),
                "ub": np.asarray(kwargs["bounds"].ub).copy(),
                "a": kwargs["constraints"].A.tocsr().copy(),
                "row_lb": np.asarray(kwargs["constraints"].lb).copy(),
                "row_ub": np.asarray(kwargs["constraints"].ub).copy(),
            })
            return real_milp(**kwargs)

        with patch("scipy.optimize.milp", side_effect=measured):
            default = solve_joint(inp)
        with patch("scipy.optimize.milp", side_effect=measured):
            frozen_before = _baseline_core.solve_joint(inp)
        self.assertTrue(default.success, default.message)
        self.assertEqual(default.input_id, frozen_before.input_id)
        self.assertAlmostEqual(default.objective_eur, frozen_before.objective_eur)
        self.assertEqual(default.residuals["experimental_a1_a3_enabled"], 0)
        for key in (
            "optimization_fixed_physical_steps",
            "optimization_event_rows_intermediate_interval_deleted",
            "optimization_net_contract_bounds_tightened",
        ):
            self.assertEqual(default.residuals[key], 0)
        left, right = captured
        for key in ("c", "integrality", "lb", "ub", "row_lb", "row_ub"):
            np.testing.assert_array_equal(left[key], right[key])
        self.assertEqual(left["a"].shape, right["a"].shape)
        self.assertEqual(left["a"].nnz, right["a"].nnz)
        self.assertEqual((left["a"] != right["a"]).nnz, 0)

    def test_directed_interval_encloses_large_cancellation(self):
        interval = (0.0, 0.0)
        exact = Decimal(0)
        for value in (1e16, 1.0, -1e16, 0.1, -0.1):
            interval = _interval_add(interval, _interval_scale((value, value), 1.0))
            exact += Decimal.from_float(value)
        self.assertLessEqual(Decimal.from_float(interval[0]), exact)
        self.assertGreaterEqual(Decimal.from_float(interval[1]), exact)

    def test_reviewer_near_boundary_counterexample_keeps_feasible_quantity(self):
        start = datetime(2025, 1, 1, tzinfo=UTC)
        qh = make_qh("q", start)
        frozen = make_contract(qh, "DA", 0.0, "-tiny")
        variable = make_contract(qh, "IDA", 0.0, "-variable")
        inp = SyntheticMarketInput(
            (qh,), (frozen, variable),
            fixed_commitments=(FixedCommitment(qh.qh_id, baseline_mw=100.0),),
            annual_efc_budget={2025: 600.0}, e_initial_mwh=100.0,
            e_max_mwh=200.0, reserve_limit_up_mw=0.0, reserve_limit_down_mw=0.0,
            input_id="ES_SYNTHETIC_MARKET_A3_REVIEWER_BOUNDARY",
        )
        captured = {}
        def measured(**kwargs):
            captured.update(kwargs)
            return real_milp(**kwargs)
        with patch("scipy.optimize.milp", side_effect=measured):
            result = solve_joint(
                inp, terminal_hard=False, remaining_annual_efc={2025: 600.0},
                fixed_spot_mw={frozen.contract_id: (1e-14, 0.0)},
                experimental_a1_a3=True,
            )
        self.assertTrue(result.success, result.message)
        # Mathematical feasibility requires x=-1e-14.  The old propagation
        # rounded the candidate upper bound to -1.421e-14 and excluded it.
        self.assertGreaterEqual(float(captured["bounds"].ub[0]), -1e-14)
        self.assertFalse(any(lo > hi for lo, hi in zip(captured["bounds"].lb, captured["bounds"].ub)))

    def test_multi_contract_boundary_accumulation_does_not_false_delete_intermediate_event(self):
        start = datetime(2025, 1, 1, tzinfo=UTC)
        q0 = make_qh("q0", start)
        q1 = make_qh("q1", start + timedelta(minutes=15))
        early = tuple(ContractInput(
            f"DA-{i}", "DA", start, start, q1.start_utc, q1.end_utc, 0.0,
            {q1.qh_id: 1.0},
        ) for i in range(3))
        final = ContractInput(
            "IDA-final", "IDA", start, q1.start_utc, q1.start_utc, q1.end_utc,
            0.0, {q1.qh_id: 1.0},
        )
        inp = SyntheticMarketInput(
            (q0, q1), early + (final,), annual_efc_budget={2025: 600.0},
            e_initial_mwh=100.0, e_max_mwh=200.0,
            reserve_limit_up_mw=0.0, reserve_limit_down_mw=0.0,
            input_id="ES_SYNTHETIC_MARKET_A2_MULTI_BOUNDARY",
        )
        frozen = {contract.contract_id: (100.0 / 3.0, 0.0) for contract in early}
        result = solve_joint(
            inp, terminal_hard=False, remaining_annual_efc={2025: 600.0},
            fixed_spot_mw=frozen,
            experimental_a1_a3=True,
        )
        self.assertTrue(result.success, result.message)
        self.assertEqual(result.residuals["optimization_event_rows_total"], 2)
        self.assertEqual(result.residuals["optimization_event_rows_intermediate_kept"], 1)
        self.assertEqual(result.residuals["optimization_event_rows_intermediate_interval_deleted"], 0)
        self.assertEqual(result.residuals["optimization_event_rows_final_kept"], 1)

    def test_fixed_negative_price_reverse_hedge_reconstructs_cash_and_eliminates_physics(self):
        start = datetime(2025, 1, 1, tzinfo=UTC)
        qh = make_qh("q", start)
        da = make_contract(qh, "DA", -50.0)
        ida = make_contract(qh, "IDA", 100.0)
        inp = SyntheticMarketInput(
            (qh,), (da, ida), annual_efc_budget={2025: 600.0},
            reserve_limit_up_mw=0.0, reserve_limit_down_mw=0.0,
            input_id="ES_SYNTHETIC_MARKET_A1_FIXED_HEDGE",
        )
        result = solve_joint(
            inp,
            fixed_spot_mw={da.contract_id: (0.0, 40.0), ida.contract_id: (40.0, 0.0)},
            experimental_a1_a3=True,
        )
        self.assertTrue(result.success, result.message)
        self.assertAlmostEqual(result.objective_gross_eur, 1500.0)
        self.assertEqual(result.qh_power_trace_mw[qh.qh_id], (0.0,))
        self.assertEqual(result.soc_trace_mwh[qh.segment_id], (10.0,))
        self.assertEqual(result.residuals["optimization_fixed_physical_steps"], 1)
        self.assertEqual(result.residuals["optimization_charge_variables_eliminated"], 1)
        self.assertEqual(result.residuals["optimization_discharge_variables_eliminated"], 1)
        self.assertEqual(result.residuals["optimization_direction_binaries_eliminated"], 1)
        self.assertEqual(result.residuals["optimization_soc_variables_eliminated"], 1)
        self.assertEqual(result.residuals["optimization_event_rows_final_kept"], 1)
        self.assertAlmostEqual(result.residuals["independent_cash_rebuild_abs"], 0.0)

    def test_contiguous_fixed_interval_preserves_efficiency_terminal_and_efc(self):
        start = datetime(2025, 1, 1, tzinfo=UTC)
        q0 = make_qh("q0", start)
        q1 = make_qh("q1", start + timedelta(minutes=15))
        discharge = 10.0 * 0.25 * 0.92 * 0.92 / 0.25
        inp = SyntheticMarketInput(
            (q0, q1), (),
            fixed_commitments=(
                FixedCommitment(q0.qh_id, baseline_mw=-10.0),
                FixedCommitment(q1.qh_id, baseline_mw=discharge),
            ),
            annual_efc_budget={2025: 600.0},
            reserve_limit_up_mw=0.0, reserve_limit_down_mw=0.0,
            input_id="ES_SYNTHETIC_MARKET_A1_FIXED_INTERVAL",
        )
        result = solve_joint(inp, experimental_a1_a3=True)
        self.assertTrue(result.success, result.message)
        self.assertEqual(result.residuals["optimization_fixed_physical_steps"], 2)
        self.assertEqual(result.residuals["optimization_soc_variables_eliminated"], 2)
        self.assertAlmostEqual(result.soc_trace_mwh[q0.segment_id][0], 12.3, places=9)
        self.assertAlmostEqual(result.soc_trace_mwh[q0.segment_id][1], 10.0, places=9)
        self.assertAlmostEqual(result.residuals["terminal_soc_abs_max"], 0.0, places=10)
        self.assertAlmostEqual(result.residuals["annual_efc_violation_max"], 0.0)

    def test_intermediate_event_row_deleted_only_after_bound_proof_and_final_kept(self):
        start = datetime(2025, 1, 1, tzinfo=UTC)
        q0 = make_qh("q0", start)
        q1 = make_qh("q1", start + timedelta(minutes=15))
        first = ContractInput(
            "DA-q1", "DA", start, start, q1.start_utc, q1.end_utc, 5.0,
            {q1.qh_id: 1.0},
        )
        final = ContractInput(
            "IDA-q1", "IDA", start, q1.start_utc, q1.start_utc, q1.end_utc, 10.0,
            {q1.qh_id: 1.0},
        )
        inp = SyntheticMarketInput(
            (q0, q1), (first, final),
            fixed_commitments=(FixedCommitment(q1.qh_id, baseline_mw=50.0),),
            annual_efc_budget={2025: 600.0},
            charge_mw=200.0, discharge_mw=200.0,
            grid_import_mw=200.0, grid_export_mw=200.0,
            e_initial_mwh=100.0, e_terminal_mwh=100.0, e_max_mwh=200.0,
            reserve_limit_up_mw=0.0, reserve_limit_down_mw=0.0,
            input_id="ES_SYNTHETIC_MARKET_A2_EVENT_PROOF",
        )
        result = solve_joint(
            inp, terminal_hard=False, remaining_annual_efc={2025: 600.0},
            fixed_spot_mw={first.contract_id: (40.0, 0.0)},
            experimental_a1_a3=True,
        )
        self.assertTrue(result.success, result.message)
        self.assertGreaterEqual(result.residuals["optimization_net_contract_bounds_tightened"], 1)
        self.assertEqual(result.residuals["optimization_event_rows_total"], 2)
        self.assertEqual(result.residuals["optimization_event_rows_intermediate_interval_deleted"], 1)
        self.assertEqual(result.residuals["optimization_event_rows_final_kept"], 1)
        self.assertLessEqual(abs(result.qh_baseline_mw[q1.qh_id]), 100.0 + 1e-8)

    def test_reserve_and_direction_bounds_use_reachable_qh_interval(self):
        start = datetime(2025, 1, 1, tzinfo=UTC)
        qh = make_qh("q", start, alpha_up=1.0, cap_up=10.0)
        inp = SyntheticMarketInput(
            (qh,), (), fixed_commitments=(FixedCommitment(qh.qh_id, baseline_mw=80.0),),
            annual_efc_budget={2025: 600.0}, e_initial_mwh=100.0,
            e_max_mwh=200.0, grid_export_mw=100.0,
            reserve_limit_up_mw=100.0, reserve_limit_down_mw=0.0,
            input_id="ES_SYNTHETIC_MARKET_A3_RESERVE_BOUND",
        )
        result = solve_joint(
            inp, terminal_hard=False, remaining_annual_efc={2025: 600.0},
            experimental_a1_a3=True,
        )
        self.assertTrue(result.success, result.message)
        self.assertAlmostEqual(result.reserve_up_mw[qh.qh_id], 20.0)
        self.assertEqual(result.residuals["optimization_reserve_bounds_tightened"], 1)
        self.assertGreaterEqual(result.residuals["optimization_physical_bounds_tightened"], 1)
        self.assertAlmostEqual(result.residuals["all_linear_rows_max"], 0.0, places=8)


if __name__ == "__main__":
    unittest.main()
