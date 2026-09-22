"""Synthetic fixed-order activation-path diagnostics.

No historical data, prices or API credentials are used here.  The tests keep
the fixed orders identical and assert the deliberately raw, unclipped paths.
"""

import math
import unittest

from src.es_milp_sandbox.order_diagnostic import (
    FixedOrderDiagnosticInput,
    diagnose_fixed_order,
)


class TestFixedOrderDiagnostic(unittest.TestCase):
    def _case(self, **overrides):
        values = dict(
            baseline_mw=0.0,
            reserve_up_mw=20.0,
            reserve_down_mw=20.0,
            a_up=0.2,
            a_down=0.4,
            initial_soc_mwh=100.0,
            input_id="ES_SYNTHETIC_ORDER_TEST",
        )
        values.update(overrides)
        return FixedOrderDiagnosticInput(**values)

    def test_low_soc_first_touch_and_violation_are_reported_without_clipping(self):
        result = diagnose_fixed_order(self._case(initial_soc_mwh=11.0))
        up_first = result["orders"]["up_then_down"]
        down_first = result["orders"]["down_then_up"]
        self.assertFalse(up_first["energy"]["feasible"])
        self.assertAlmostEqual(up_first["energy"]["first_boundary_contact_minute"]["lower"], 2.76, places=8)
        self.assertAlmostEqual(up_first["energy"]["violation_onset_boundary_minute"]["lower"], 2.76, places=8)
        self.assertLess(up_first["energy"]["min_raw_soc_mwh"], 10.0)
        self.assertTrue(down_first["energy"]["feasible"])
        self.assertAlmostEqual(up_first["energy"]["terminal_soc_mwh"], 11.75304347826087, places=8)
        self.assertAlmostEqual(down_first["energy"]["terminal_soc_mwh"], 11.75304347826087, places=8)

    def test_upper_boundary_down_first_and_up_first_safe(self):
        result = diagnose_fixed_order(self._case(initial_soc_mwh=189.0))
        down_first = result["orders"]["down_then_up"]
        up_first = result["orders"]["up_then_down"]
        self.assertFalse(down_first["energy"]["feasible"])
        self.assertAlmostEqual(down_first["energy"]["first_boundary_contact_minute"]["upper"], 3.260869565217391, places=8)
        self.assertGreater(down_first["energy"]["max_raw_soc_mwh"], 190.0)
        self.assertTrue(up_first["energy"]["feasible"])

    def test_boundary_equal_is_feasible(self):
        lower_case = self._case(
            initial_soc_mwh=10.0 + 100.0 * 0.25 / 0.92,
            baseline_mw=100.0, reserve_up_mw=0.0, reserve_down_mw=0.0,
            a_up=0.0, a_down=0.0, input_id="ES_SYNTHETIC_ORDER_TEST_TOUCH_LOWER",
        )
        upper_case = self._case(
            initial_soc_mwh=190.0 - 100.0 * 0.25 * 0.92,
            baseline_mw=-100.0, reserve_up_mw=0.0, reserve_down_mw=0.0,
            a_up=0.0, a_down=0.0, input_id="ES_SYNTHETIC_ORDER_TEST_TOUCH_UPPER",
        )
        for case, bound_name, expected_time in ((lower_case, "lower", 15.0), (upper_case, "upper", 15.0)):
            result = diagnose_fixed_order(case)
            for order in result["orders"].values():
                self.assertTrue(order["energy"]["feasible"])
                self.assertAlmostEqual(order["energy"]["first_boundary_contact_minute"][bound_name], expected_time, places=10)
                self.assertIsNone(order["energy"]["violation_onset_boundary_minute"][bound_name])

    def test_down_activation_can_still_be_discharging(self):
        result = diagnose_fixed_order(self._case(baseline_mw=50.0))
        for order in result["orders"].values():
            powers = [segment["actual_power_mw"] for segment in order["segments"]]
            self.assertEqual(powers, [70.0, 30.0, 50.0] if order["order"] == "up_then_down" else [30.0, 70.0, 50.0])
            self.assertTrue(all(power > 0 for power in powers))
            self.assertAlmostEqual(order["dc_throughput_mwh"], 12.5, places=8)
            self.assertAlmostEqual(order["energy"]["terminal_soc_mwh"], 87.5, places=8)

    def test_cross_zero_uses_actual_power_sign_and_efficiency(self):
        result = diagnose_fixed_order(self._case(baseline_mw=10.0, reserve_down_mw=30.0))
        for order in result["orders"].values():
            kinds = {segment["kind"]: segment for segment in order["segments"]}
            self.assertAlmostEqual(kinds["down"]["actual_power_mw"], -20.0)
            self.assertAlmostEqual(order["dc_throughput_mwh"], 4.557391304347826, places=8)
            self.assertAlmostEqual(order["energy"]["terminal_soc_mwh"], 99.12260869565218, places=8)

    def test_zero_and_one_sided_activation(self):
        zero = diagnose_fixed_order(self._case(reserve_up_mw=20.0, reserve_down_mw=30.0, a_up=0.0, a_down=0.0))
        self.assertEqual(len(zero["orders"]["up_then_down"]["segments"]), 1)
        self.assertEqual(zero["orders"]["up_then_down"]["segments"][0]["kind"], "idle")
        one = diagnose_fixed_order(self._case(a_up=1.0, a_down=0.0))
        self.assertEqual([s["kind"] for s in one["orders"]["up_then_down"]["segments"]], ["up"])
        self.assertAlmostEqual(one["orders"]["up_then_down"]["segments"][0]["duration_minute"], 15.0)

    def test_full_quarter_activation_has_no_negative_idle_segment(self):
        result = diagnose_fixed_order(self._case(a_up=0.8, a_down=0.2))
        for order in result["orders"].values():
            expected = ["up", "down"] if order["order"] == "up_then_down" else ["down", "up"]
            self.assertEqual([segment["kind"] for segment in order["segments"]], expected)
            self.assertTrue(all(segment["duration_minute"] >= 0.0 for segment in order["segments"]))
            self.assertAlmostEqual(sum(segment["duration_minute"] for segment in order["segments"]), 15.0, places=12)
            self.assertAlmostEqual(order["relative_activation"][0]["idle_duration_minute"], 0.0, places=12)

    def test_reserve_headroom_is_checked_even_when_activation_is_zero(self):
        result = diagnose_fixed_order(self._case(baseline_mw=90.0, reserve_up_mw=20.0, reserve_down_mw=0.0, a_up=0.0, a_down=0.0))
        for order in result["orders"].values():
            self.assertFalse(order["reserve_position"]["feasible"])
            self.assertFalse(order["reserve_position"]["quarter_hours"][0]["up_position_feasible"])
            self.assertTrue(order["power"]["feasible"])

    def test_100_mw_headroom_boundary_is_feasible(self):
        result = diagnose_fixed_order(self._case(baseline_mw=90.0, reserve_up_mw=10.0, reserve_down_mw=0.0, a_up=0.0, a_down=0.0))
        for order in result["orders"].values():
            self.assertTrue(order["reserve_position"]["feasible"])

    def test_two_quarter_hours_carry_soc_without_reset(self):
        result = diagnose_fixed_order(self._case(
            baseline_mw=(0.0, 0.0), reserve_up_mw=(20.0, 20.0), reserve_down_mw=(20.0, 20.0),
            a_up=(0.2, 0.2), a_down=(0.4, 0.4), input_id="ES_SYNTHETIC_ORDER_TEST_TWO_QH",
        ))
        for order in result["orders"].values():
            self.assertEqual(len(order["energy"]["raw_soc_trace_mwh"]), 7)
            records = order["segments"]
            self.assertAlmostEqual(records[3]["soc_start_mwh"], records[2]["soc_end_mwh"], places=12)
            self.assertAlmostEqual(records[3]["soc_start_mwh"], 100.75304347826087, places=8)
            self.assertAlmostEqual(order["energy"]["raw_soc_trace_mwh"][3], 100.75304347826087, places=8)
            self.assertAlmostEqual(order["energy"]["raw_soc_trace_mwh"][6], 101.50608695652174, places=8)
        self.assertTrue(result["comparison"]["terminal_soc_and_dc_throughput_invariant"])

    def test_rejects_nonfinite_invalid_ranges_and_non_synthetic_labels(self):
        invalid = (
            dict(a_up=1.0, a_down=0.1),
            dict(a_up=-0.1),
            dict(a_down=1.1),
            dict(reserve_up_mw=-1.0),
            dict(baseline_mw=math.nan),
            dict(a_up=math.inf),
            dict(input_id="HISTORICAL_ORDER_INPUT"),
            dict(qh_hours=1.0),
        )
        for overrides in invalid:
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    self._case(**overrides)


if __name__ == "__main__":
    unittest.main()
