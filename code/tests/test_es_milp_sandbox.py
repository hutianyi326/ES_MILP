"""Synthetic-only tests for the battery MILP foundation.

These tests do not use raw market files, API credentials, or historical
activation.  They are deliberately small enough to inspect by hand.
"""

import unittest

import numpy as np

from src.es_milp_sandbox import BatteryMILPInput, solve_battery_milp
from src.es_milp_sandbox.battery import audit_solution


class TestSyntheticBatteryMILP(unittest.TestCase):
    def test_small_arbitrage_and_efficiency(self):
        case = BatteryMILPInput(
            energy_price=(10.0, 100.0), dt_hours=1.0,
            e_initial_mwh=100.0, e_terminal_mwh=100.0,
            eta_charge=0.92, eta_discharge=0.92, input_id="ES_SYNTHETIC_TEST_ARBITRAGE",
        )
        result = solve_battery_milp(case)
        self.assertTrue(result.success, result.message)
        # The low-price period charges and the high-price period discharges.
        # The 10--190 MWh band limits charging to 90/0.92 MW in one hour.
        self.assertAlmostEqual(result.charge_mw[0], 90.0 / 0.92, places=5)
        self.assertAlmostEqual(result.discharge_mw[1], 82.8, places=5)
        self.assertAlmostEqual(result.soc_end_mwh[-1], 100.0, places=5)
        self.assertAlmostEqual(result.objective_eur, 7301.7391304348, places=4)
        self._assert_clean(result)

    def test_negative_price_prefers_charging_without_terminal_target(self):
        case = BatteryMILPInput(
            energy_price=(-20.0,), dt_hours=1.0,
            e_initial_mwh=100.0, e_terminal_mwh=None, input_id="ES_SYNTHETIC_TEST_NEGATIVE",
        )
        result = solve_battery_milp(case)
        self.assertTrue(result.success, result.message)
        self.assertAlmostEqual(result.charge_mw[0], 90.0 / 0.92, places=5)
        self.assertAlmostEqual(result.discharge_mw[0], 0.0, places=5)
        self.assertAlmostEqual(result.soc_end_mwh[0], 190.0, places=5)
        self.assertAlmostEqual(result.objective_eur, 1956.5217391304, places=4)
        self._assert_clean(result)

    def test_soc_power_and_mutual_exclusion(self):
        case = BatteryMILPInput(
            energy_price=(50.0, -50.0, 50.0), dt_hours=0.25,
            e_initial_mwh=100.0, e_terminal_mwh=100.0,
            charge_mw=100.0, discharge_mw=100.0, input_id="ES_SYNTHETIC_TEST_PHYSICS",
        )
        result = solve_battery_milp(case)
        self.assertTrue(result.success, result.message)
        self.assertTrue(np.all(result.soc_end_mwh >= 10.0 - 1e-6))
        self.assertTrue(np.all(result.soc_end_mwh <= 190.0 + 1e-6))
        self.assertTrue(np.all(result.charge_mw <= 100.0 + 1e-6))
        self.assertTrue(np.all(result.discharge_mw <= 100.0 + 1e-6))
        self.assertTrue(np.all((result.charge_mw <= 1e-6) | (result.discharge_mw <= 1e-6)))
        self._assert_clean(result)

    def test_dc_throughput_cycle_budget_is_hard_limit(self):
        # 0.25 EFC means 90 MWh DC throughput for the fixed 10--190 MWh band.
        case = BatteryMILPInput(
            energy_price=(0.0, 100.0), dt_hours=1.0,
            e_initial_mwh=100.0, e_terminal_mwh=100.0,
            cycle_budget=0.25, input_id="ES_SYNTHETIC_TEST_CYCLE",
        )
        result = solve_battery_milp(case)
        self.assertTrue(result.success, result.message)
        self.assertLessEqual(result.residuals["cycle_throughput_mwh"], 90.0 + 1e-6)
        # Returning to the same SOC makes DC charge and discharge throughput
        # equal; the budget therefore caps charge below the 100 MW limit.
        self.assertLess(result.charge_mw[0], 100.0 - 1e-4)
        self.assertAlmostEqual(result.residuals["cycle_throughput_mwh"], 90.0, places=4)
        self._assert_clean(result)

    def test_non_synthetic_and_nonfinite_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            BatteryMILPInput(energy_price=(1.0,), input_id="HISTORICAL_MARKET_DATA")
        with self.assertRaises(ValueError):
            BatteryMILPInput(energy_price=(float("nan"),), input_id="ES_SYNTHETIC_TEST_BAD")
        with self.assertRaises(ValueError):
            BatteryMILPInput(energy_price=(1.0,), charge_mw=float("inf"), input_id="ES_SYNTHETIC_TEST_BAD")
        with self.assertRaises(ValueError):
            BatteryMILPInput(energy_price=(1.0,), eta_charge=0.0, input_id="ES_SYNTHETIC_TEST_BAD")

    @staticmethod
    def _assert_clean(result):
        for key in (
            "soc_recursion_abs_max", "charge_power_violation_max",
            "discharge_power_violation_max", "soc_bound_violation_max",
            "cycle_throughput_violation_max", "binary_integrality_abs_max",
            "terminal_soc_abs_max", "objective_cash_consistency_abs",
        ):
            assert result.residuals[key] <= 1e-6, (key, result.residuals)

    def test_tampered_solution_is_rejected_by_independent_audit(self):
        case = BatteryMILPInput(
            energy_price=(10.0,), dt_hours=1.0,
            e_initial_mwh=100.0, e_terminal_mwh=100.0,
            input_id="ES_SYNTHETIC_TEST_AUDIT",
        )
        faults = (
            # Negative charging power, with a matching SOC equation, is invalid.
            ((-1.0,), (0.0,), (0.0,), (99.08,)),
            # The physical recursion can hold while the fixed terminal SOC fails.
            ((1.0,), (0.0,), (0.0,), (100.92,)),
            # Raw binary values are never allowed to be fractional or outside [0, 1].
            ((0.0,), (0.0,), (1.5,), (100.0,)),
            # NaN in either a power or SOC array is rejected before residual math.
            ((float("nan"),), (0.0,), (0.0,), (100.0,)),
            ((0.0,), (0.0,), (0.0,), (float("nan"),)),
        )
        for charge, discharge, mode, soc in faults:
            with self.subTest(fault=(charge, discharge, mode, soc)):
                with self.assertRaises((AssertionError, ValueError)):
                    audit_solution(case, charge, discharge, mode, soc)

        with self.assertRaises(ValueError):
            audit_solution(case, (0.0,), (0.0,), (0.0,), (100.0,), tolerance=0.0)
        with self.assertRaises(ValueError):
            audit_solution(case, (0.0,), (0.0,), (0.0,), (100.0,), tolerance=float("nan"))


if __name__ == "__main__":
    unittest.main()
