"""Formulation-size checks against the frozen pre-net-contract source."""

from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

import numpy as np

from src.es_synthetic_market import core as current

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "outputs/es_historical_conditional/net_contract_8day_20260920_v1/source_before/src/es_synthetic_market/core.py"
V2_SNAPSHOT = ROOT / "outputs/es_historical_conditional/eight_day_20260920_v2/source_snapshot/src/es_synthetic_market/core.py"
UTC = timezone.utc


def _load_snapshot(path=SNAPSHOT, module_name="es_p1_snapshot_core"):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load snapshot: {SNAPSHOT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _qh(module, start, qh_id, segment="S0", year=None):
    return module.QHInput(
        qh_id=qh_id, start_utc=start, end_utc=start + timedelta(minutes=15),
        segment_id=segment,
        madrid_year=start.astimezone(timezone(timedelta(hours=1))).year if year is None else year,
        alpha_up=0.2, alpha_down=0.1,
        afrr_gate_close_utc=start, afrr_result_release_utc=start,
    )


def _case(module, name):
    base = datetime(2025, 1, 1, tzinfo=UTC)
    if name == "da_ida_nodes":
        qhs = (_qh(module, base, "q0"), _qh(module, base + timedelta(minutes=15), "q1"))
        contracts = (
            module.ContractInput("DA-same", "DA", base, base, base, base + timedelta(minutes=15), 42.0, {"q0": 1.0}),
            module.ContractInput("IDA-same", "IDA", base, base, base, base + timedelta(minutes=15), 38.0, {"q0": 1.0}),
            module.ContractInput("DA-next-same", "DA", base, base, base + timedelta(minutes=15), base + timedelta(minutes=30), 36.0, {"q1": 1.0}),
            module.ContractInput("IDA-next", "IDA", base + timedelta(minutes=15), base + timedelta(minutes=15), base + timedelta(minutes=15), base + timedelta(minutes=30), 35.0, {"q1": 1.0}),
        )
        inp = module.SyntheticMarketInput(qhs=qhs, contracts=contracts, annual_efc_budget={2025: 600.0}, input_id="ES_SYNTHETIC_MARKET_P1_NODES")
        return inp, dict(order_mode="U")
    if name == "hourly_down":
        qhs = tuple(_qh(module, base + timedelta(minutes=15 * i), f"q{i}") for i in range(4))
        contract = module.ContractInput("IDA-hour", "IDA", base, base, base, base + timedelta(hours=1), 12.0, {f"q{i}": 1.0 for i in range(4)})
        inp = module.SyntheticMarketInput(qhs=qhs, contracts=(contract,), annual_efc_budget={2025: 600.0}, input_id="ES_SYNTHETIC_MARKET_P1_HOUR")
        return inp, dict(order_mode="D")
    if name == "segments_fixed_salvage":
        a0 = base
        b0 = base + timedelta(hours=1)
        qhs = (_qh(module, a0, "a0", "A"), _qh(module, a0 + timedelta(minutes=15), "a1", "A"), _qh(module, b0, "b0", "B"), _qh(module, b0 + timedelta(minutes=15), "b1", "B"))
        contracts = (
            module.ContractInput("DA-A", "DA", a0, a0, a0, a0 + timedelta(minutes=30), 20.0, {"a0": 1.0, "a1": 1.0}),
            module.ContractInput("IDA-B", "IDA", b0, b0, b0, b0 + timedelta(minutes=30), 25.0, {"b0": 1.0, "b1": 1.0}),
        )
        fixed = (module.FixedCommitment("a0", baseline_mw=10.0, reserve_up_mw=2.0),)
        inp = module.SyntheticMarketInput(qhs=qhs, contracts=contracts, fixed_commitments=fixed, annual_efc_budget={2025: 600.0}, e_initial_mwh=100.0, input_id="ES_SYNTHETIC_MARKET_P1_SEGMENTS")
        return inp, dict(order_mode="U", fixed_spot_mw={"DA-A": (5.0, 0.0)}, fixed_reserve_mw={"b0": (2.0, 1.0)}, terminal_hard=False, salvage_price_eur_per_mwh=4.0, terminal_reference_mwh=20.0)
    if name == "cross_year":
        start = datetime(2025, 12, 31, 22, 45, tzinfo=UTC)
        qhs = (_qh(module, start, "y0", "Y", 2025), _qh(module, start + timedelta(minutes=15), "y1", "Y", 2026))
        inp = module.SyntheticMarketInput(qhs=qhs, contracts=(), annual_efc_budget={2025: 600.0, 2026: 600.0}, input_id="ES_SYNTHETIC_MARKET_P1_YEAR")
        return inp, dict(order_mode="D")
    raise AssertionError(name)


def _capture(module, inp, options):
    captured = {}

    def capture_milp(**kwargs):
        constraints = kwargs["constraints"]
        captured["c"] = np.array(kwargs["c"], copy=True)
        captured["integrality"] = np.array(kwargs["integrality"], copy=True)
        captured["lb"] = np.array(kwargs["bounds"].lb, copy=True)
        captured["ub"] = np.array(kwargs["bounds"].ub, copy=True)
        captured["A"] = constraints.A.tocsr().copy()
        captured["row_lb"] = np.array(constraints.lb, copy=True)
        captured["row_ub"] = np.array(constraints.ub, copy=True)
        return SimpleNamespace(x=None, status=2, message="equivalence capture")

    with patch("scipy.optimize.milp", side_effect=capture_milp):
        module.solve_joint(inp, time_limit_seconds=10.0, mip_rel_gap=1e-6, **options)
    return captured


class P1IndexingEquivalenceTests(TestCase):
    def test_frozen_pre_net_source_still_matches_v2_matrix_exactly(self):
        before = _load_snapshot()
        v2 = _load_snapshot(V2_SNAPSHOT, "es_p1_v2_snapshot_core")
        for name in ("da_ida_nodes", "hourly_down", "segments_fixed_salvage", "cross_year"):
            before_inp, before_options = _case(before, name)
            v2_inp, v2_options = _case(v2, name)
            before_capture = _capture(before, before_inp, before_options)
            v2_capture = _capture(v2, v2_inp, v2_options)
            for key in ("c", "integrality", "lb", "ub", "row_lb", "row_ub"):
                np.testing.assert_array_equal(before_capture[key], v2_capture[key], err_msg=f"{name}:{key}")
            self.assertEqual(before_capture["A"].shape, v2_capture["A"].shape)
            np.testing.assert_array_equal(before_capture["A"].indptr, v2_capture["A"].indptr)
            np.testing.assert_array_equal(before_capture["A"].indices, v2_capture["A"].indices)
            np.testing.assert_array_equal(before_capture["A"].data, v2_capture["A"].data)

    def test_net_formulation_is_smaller_than_frozen_v2_source(self):
        snapshot = _load_snapshot()
        for name in ("da_ida_nodes", "hourly_down", "segments_fixed_salvage", "cross_year"):
            new_inp, options = _case(current, name)
            old_inp, old_options = _case(snapshot, name)
            new_capture = _capture(current, new_inp, options)
            old_capture = _capture(snapshot, old_inp, old_options)
            self.assertLessEqual(new_capture["A"].shape[0], old_capture["A"].shape[0], name)
            self.assertLessEqual(new_capture["A"].shape[1], old_capture["A"].shape[1], name)
            self.assertLessEqual(np.count_nonzero(new_capture["integrality"]), np.count_nonzero(old_capture["integrality"]), name)
            if len(new_inp.contracts):
                self.assertLess(new_capture["A"].shape[1], old_capture["A"].shape[1], name)
                self.assertLess(np.count_nonzero(new_capture["integrality"]), np.count_nonzero(old_capture["integrality"]), name)

    def test_small_cases_match_frozen_v2_optimum_and_bound(self):
        snapshot = _load_snapshot()
        for name in ("da_ida_nodes", "hourly_down", "segments_fixed_salvage", "cross_year"):
            with self.subTest(name=name):
                new_inp, options = _case(current, name)
                old_inp, old_options = _case(snapshot, name)
                new_result = current.solve_joint(
                    new_inp, time_limit_seconds=60.0, mip_rel_gap=1e-9, **options
                )
                old_result = snapshot.solve_joint(
                    old_inp, time_limit_seconds=60.0, mip_rel_gap=1e-9, **old_options
                )
                self.assertTrue(new_result.proven_optimal, new_result.message)
                self.assertTrue(old_result.proven_optimal, old_result.message)
                self.assertAlmostEqual(new_result.objective_eur, old_result.objective_eur, places=7)
                self.assertAlmostEqual(new_result.objective_gross_eur, old_result.objective_gross_eur, places=7)
                self.assertAlmostEqual(new_result.solver_objective_min_eur, old_result.solver_objective_min_eur, places=7)
                self.assertAlmostEqual(new_result.profit_upper_bound_eur, old_result.profit_upper_bound_eur, places=7)
