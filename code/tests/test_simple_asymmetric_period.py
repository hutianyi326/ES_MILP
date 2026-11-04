"""Asymmetric charge/discharge limits and chronological-search regression."""
import unittest
from project.calculate_simple_entsoe_day import da_search


class AsymmetricDayTests(unittest.TestCase):
    def test_symmetric_keyword_is_backward_compatible(self):
        prices=[60]*8+[-20]*8+[220]*8+[40]*8
        self.assertEqual(da_search(prices,50,100),da_search(prices,50,100,discharge_power=50))

    def test_asymmetric_power_efficiency_order_and_cash(self):
        prices=[10]*24+[100]*24
        r=da_search(prices,40,160,discharge_power=80)
        charge,dis=r['charge_mwh_ac'],r['discharge_mwh_ac']
        self.assertAlmostEqual(sum(charge),160/.92)
        self.assertAlmostEqual(sum(dis),160*.92)
        self.assertLessEqual(max(charge),10)
        self.assertLessEqual(max(dis),20)
        self.assertEqual(len([v for v in charge if v>0]),18)
        self.assertEqual(len([v for v in dis if v>0]),8)
        self.assertLess(max(i for i,v in enumerate(charge) if v),min(i for i,v in enumerate(dis) if v))
        self.assertAlmostEqual(r['profit_eur'],160*.92*100-160/.92*10)

    def test_slower_charge_reoptimizes_depth_and_profit(self):
        prices=[1000]*8+[-1000]*8+[1000]*8
        previous=da_search(prices,80,160,discharge_power=80)
        current=da_search(prices,40,160,discharge_power=80)
        self.assertLess(current['profit_eur'],previous['profit_eur'])
        self.assertLess(current['depth'],previous['depth'])

    def test_too_short_day_or_flat_price_can_choose_no_trade(self):
        self.assertEqual(da_search([100]*96,40,160,discharge_power=80)['profit_eur'],0)
        self.assertEqual(da_search([10],40,160,discharge_power=80)['profit_eur'],0)
        with self.assertRaises(ValueError):
            da_search([10,100],40,160,discharge_power=0)


if __name__=='__main__':
    unittest.main()
