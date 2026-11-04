"""Price screening, settlement signs, interval semantics and non-MILP cash checks."""
import unittest
from datetime import datetime, timezone
from project.calculate_simple_entsoe_day import activation, da_search, expand, linear_percentile


class SimpleDayTests(unittest.TestCase):
    def test_quantile_valuation_changes_value_without_changing_activation_trigger(self):
        dn = activation(60, 100, 2, 1, 0, 50, False, restoration_price=120)
        self.assertAlmostEqual(dn['da_restoration_cash_eur'], 50/900*.92**2*120)
        up = activation(350, 100, 2, 1, 200, 50, True, restoration_price=70)
        self.assertAlmostEqual(up['da_restoration_cash_eur'], -50/900/.92**2*70)
        # Using P75 for valuation must not create an activation absent at the same-QH DA.
        no_dn = activation(110, 100, 2, 1, 0, 50, False, restoration_price=120)
        self.assertEqual(no_dn['energy_mwh'], 0)

    def test_linear_percentiles_include_all_slots_and_interpolate(self):
        self.assertEqual(linear_percentile([40, 10, 30, 20], .25), 17.5)
        self.assertEqual(linear_percentile([40, 10, 30, 20], .75), 32.5)
        self.assertEqual(linear_percentile([0, 0, 0, 100], .75), 25)
        for values in ([], [1, None], [float('nan')]):
            with self.assertRaises(ValueError):
                linear_percentile(values, .25)

    def test_dn_resale_value_uses_both_efficiencies(self):
        r = activation(26.54, 112.01, 1.61, 1, 0, 50, False)
        self.assertAlmostEqual(r['da_restoration_energy_mwh'], (50/900)*.92**2)
        self.assertAlmostEqual(r['da_restoration_cash_eur'], (50/900)*.92**2*112.01)
        self.assertAlmostEqual(r['efficiency_adjusted_reference_eur'], r['cash_eur']+r['da_restoration_cash_eur'])

    def test_up_replenishment_cost_divides_by_both_efficiencies(self):
        r = activation(350, 100, 2, 1, 200, 50, True)
        self.assertAlmostEqual(r['da_restoration_energy_mwh'], (50/900)/.92**2)
        self.assertAlmostEqual(r['da_restoration_cash_eur'], -(50/900)/.92**2*100)
        self.assertAlmostEqual(r['efficiency_adjusted_reference_eur'], r['cash_eur']+r['da_restoration_cash_eur'])

    def test_capacity_and_spread_are_strict_and_capacity_gates_activation(self):
        self.assertEqual(activation(300, 100, 1, 1, 100, 50, True)['energy_mwh'], 0)
        self.assertEqual(activation(300, 100, 2, 1, 200, 50, True)['energy_mwh'], 0)
        self.assertAlmostEqual(activation(301, 100, 2, 1, 200, 50, True)['energy_mwh'], 50/900)

    def test_down_is_expenditure_and_negative_price_is_income(self):
        self.assertAlmostEqual(activation(60, 100, 2, 1, 0, 50, False)['cash_eur'], -60*50/900)
        self.assertGreater(activation(-1, 100, 2, 1, 0, 50, False)['cash_eur'], 0)

    def test_null_price_is_not_a_zero_price(self):
        self.assertFalse(activation(None, 100, 2, 1, 0, 50, False)['price_available'])
        self.assertTrue(activation(0, 100, 2, 1, 0, 50, False)['price_available'])
        self.assertGreater(activation(0, 100, 2, 1, 0, 50, False)['energy_mwh'], 0)

    def test_compressed_intervals_expand_and_null_resets(self):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        rows = [dict(start='2026-01-01T00:00:00+00:00', end='2026-01-01T00:00:08+00:00', point={'price': '2'}),
                dict(start='2026-01-01T00:00:08+00:00', end='2026-01-01T00:00:16+00:00', point={})]
        self.assertEqual(expand(rows, start, 4, 4, 'price'), [2, 2, None, None])
        with self.assertRaises(ValueError):
            expand(rows+rows[:1], start, 4, 4, 'price')

    def test_da_respects_energy_order_efficiency_and_reconciles_cash(self):
        prices = [10]*12+[100]*12
        r = da_search(prices, 50, 100)
        ch, dis = r['charge_mwh_ac'], r['discharge_mwh_ac']
        self.assertAlmostEqual(sum(ch)*.92, 100)
        self.assertAlmostEqual(sum(dis)/.92, 100)
        self.assertLess(max(i for i, v in enumerate(ch) if v), min(i for i, v in enumerate(dis) if v))
        self.assertAlmostEqual(r['profit_eur'], sum(p*(d-c) for p, d, c in zip(prices, dis, ch)))
        self.assertAlmostEqual(r['profit_eur'], 9200-1000/.92)

    def test_da_can_choose_no_trade_and_rejects_missing_data(self):
        self.assertEqual(da_search([100]*96, 50, 100)['profit_eur'], 0)
        with self.assertRaises(ValueError):
            da_search([100, None], 50, 100)
