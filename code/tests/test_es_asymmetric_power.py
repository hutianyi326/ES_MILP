"""Check asymmetric power and full cross-zero reserve at known operating points."""
import unittest
from dataclasses import replace
from datetime import datetime, timezone

from tests.test_es_synthetic_market_core import make_input, make_qh
from src.es_synthetic_market.core import solve_joint


class AsymmetricPowerTests(unittest.TestCase):
    def solve(self, baseline, up, down, alpha_up=0, alpha_down=0, cap=150):
        q = make_qh('q', datetime(2025, 1, 1, tzinfo=timezone.utc),
                    alpha_up=alpha_up, alpha_down=alpha_down)
        inp = replace(make_input((q,), (0,), contracts_both=False),
                      charge_mw=50, discharge_mw=100, grid_import_mw=50,
                      grid_export_mw=100, reserve_limit_up_mw=cap,
                      reserve_limit_down_mw=cap, e_initial_mwh=100)
        spot = (max(baseline, 0), max(-baseline, 0))
        return solve_joint(inp, 'D', fixed_spot_mw={inp.contracts[0].contract_id: spot},
                           fixed_reserve_mw={'q': (up, down)}, terminal_hard=False,
                           remaining_annual_efc={2025: 10}, reserve_headroom_from_gct=True)

    def test_cross_zero_up_and_down_full_activation(self):
        for args in ((-50, 150, 0, 1, 0), (100, 0, 150, 0, 1)):
            with self.subTest(args=args):
                result = self.solve(*args)
                self.assertTrue(result.feasible, result.message)
        self.assertFalse(self.solve(-50, 150, 0, 1, 0, cap=100).feasible)

    def test_unavailable_headroom_is_rejected(self):
        for args in ((-50, 0, 1), (100, 1, 0), (0, 0, 51), (0, 101, 0)):
            with self.subTest(args=args):
                self.assertFalse(self.solve(*args).feasible)

    def test_new_reserve_above_100_is_solved_and_returned(self):
        q = make_qh('q', datetime(2025, 1, 1, tzinfo=timezone.utc), cap_up=10)
        inp = replace(make_input((q,), (0,), contracts_both=False),
                      charge_mw=50, grid_import_mw=50, reserve_limit_up_mw=150,
                      reserve_limit_down_mw=150, e_initial_mwh=100)
        result = solve_joint(inp, 'D', fixed_spot_mw={inp.contracts[0].contract_id:(0, 50)},
                             terminal_hard=False, remaining_annual_efc={2025:10},
                             reserve_headroom_from_gct=True)
        self.assertTrue(result.feasible, result.message)
        self.assertAlmostEqual(result.reserve_up_mw['q'], 150)


if __name__ == '__main__':
    unittest.main()
