"""Period aggregation regression against the original scalar 4s calculator."""
import unittest

from project.calculate_simple_entsoe_day import activation, da_search
from project.calculate_simple_market_period import daily_case, exposures


class SimplePeriodTests(unittest.TestCase):
    def test_screened_exposure_matches_scalar_original(self):
        prices = [None, 0, -50, 100, 300, 300.01, 900, -500]
        for up in [True, False]:
            for cap in [1, 1.01]:
                exp = exposures(prices, 100, cap, up=up)
                scalar = [activation(p,100,cap,1,200 if up else 0,1,up) for p in prices]
                self.assertEqual(exp['valid_points'], 7)
                self.assertEqual(exp['active_points'], sum(r['energy_mwh']>0 for r in scalar))
                self.assertAlmostEqual(exp['energy_per_mw'], sum(r['energy_mwh'] for r in scalar))
                self.assertAlmostEqual(exp['cash_per_mw'], sum(r['cash_eur'] for r in scalar))

    def test_da_linear_scaling_preserves_allocation_results(self):
        prices = [40]*8+[-50]*8+[500]*8+[10]*8+[700]*8
        full = da_search(prices,100,200)
        for share in [.5, .8, 1]:
            direct = da_search(prices,100*share,200*share)
            self.assertAlmostEqual(direct['profit_eur'], full['profit_eur']*share)
            self.assertEqual(direct['charge_start_index'], full['charge_start_index'])
            self.assertEqual(direct['discharge_start_index'], full['discharge_start_index'])
            self.assertEqual(direct['depth'], full['depth'])

    def test_missing_is_distinct_from_real_zero_price(self):
        nulls = exposures([None],100,2,up=False)
        zeros = exposures([0],100,2,up=False)
        self.assertEqual(nulls['valid_points'],0)
        self.assertEqual(nulls['active_points'],0)
        self.assertEqual(zeros['valid_points'],1)
        self.assertEqual(zeros['active_points'],1)
        self.assertEqual(zeros['cash_per_mw'],0)
        self.assertGreater(zeros['energy_per_mw'],0)

    def test_cost_sign_when_p25_negative_and_sell_value_negative(self):
        d = dict(date='2025-06-01', month='2025-06', da_sales_full_eur=100,
            da_purchases_full_eur=-20,capacity_up_per_mw=10,capacity_down_per_mw=15,
            up_cash_per_mw=20,down_cash_per_mw=-10,up_energy_per_mw=1,down_energy_per_mw=2,
            da_buy_full_mwh=10,da_sell_full_mwh=8,da_p25=-5,da_p75=-1,
            expected_points=21600,up_valid_points=0,down_valid_points=21600,
            up_active_points=0,down_active_points=1)
        half = daily_case(d,'50% DA',.5)
        self.assertGreater(half['up_replenishment_cost_eur'],0)
        self.assertLess(half['down_resale_value_eur'],0)
        self.assertAlmostEqual(half['up_replenishment_cost_eur'],50/.92**2*5)
        self.assertAlmostEqual(half['total_with_value_eur'],sum(half[k] for k in
            ['da_net_eur','capacity_total_eur','activation_cash_eur','down_resale_value_eur','up_replenishment_cost_eur']))
        pure = daily_case(d,'100% DA',1)
        for key in ['capacity_total_eur','activation_cash_eur','down_resale_value_eur','up_replenishment_cost_eur']:
            self.assertEqual(pure[key],0)


if __name__ == '__main__':
    unittest.main()
