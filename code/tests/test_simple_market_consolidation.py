"""Consolidation must preserve source resolution, nulls, zones and DST days."""
import unittest
from datetime import date
from project.consolidate_simple_market_data import activation_arrays, bounds, gap_runs, put_interval, ES


def xml_series(points, duplicate=False):
    series=f'''<TimeSeries><businessType>A96</businessType><standard_MarketProduct.marketProductType>A01</standard_MarketProduct.marketProductType><currency_Unit.name>EUR</currency_Unit.name><price_Measure_Unit.name>MWH</price_Measure_Unit.name><flowDirection.direction>A01</flowDirection.direction><curveType>A03</curveType><Period><timeInterval><start>2025-12-31T23:00Z</start><end>2025-12-31T23:00:24Z</end></timeInterval><resolution>PT4S</resolution>{points}</Period></TimeSeries>'''
    return f'<Balancing_MarketDocument><type>A84</type><process.processType>A67</process.processType><area_Domain.mRID>{ES}</area_Domain.mRID>{series}{series if duplicate else ""}</Balancing_MarketDocument>'.encode()


class ConsolidationTests(unittest.TestCase):
    def test_dst_day_lengths(self):
        for day,expected in [(date(2025,10,26),90000),(date(2026,3,29),82800),(date(2026,10,25),90000),(date(2026,1,1),86400)]:
            a,b=bounds(day)
            self.assertEqual((b-a).total_seconds(),expected)

    def test_hourly_price_mapping_is_labelled_not_invented_quarter_prices(self):
        grid={'da':{}};start=int(bounds(date(2025,6,1))[0].timestamp())
        put_interval(grid,'da',start,start+3600,0.,'source','PT60M')
        self.assertEqual(len(grid['da']),4)
        self.assertTrue(all(v==[0.,'source','PT60M'] for v in grid['da'].values()))

    def test_off_grid_source_rejected(self):
        with self.assertRaises(ValueError):
            put_interval({'da':{}},'da',1,901,4,'source','PT15M')

    def test_a03_explicit_null_resets_and_zero_is_valid(self):
        points='<Point><position>1</position><activation_Price.amount>0</activation_Price.amount><imbalance_Price.category>A08</imbalance_Price.category></Point><Point><position>3</position></Point><Point><position>5</position><activation_Price.amount>10</activation_Price.amount><imbalance_Price.category>A08</imbalance_Price.category></Point>'
        values,seen=activation_arrays(xml_series(points),date(2026,1,1))
        self.assertEqual(values['up'][:7],[0,0,None,None,10,10,None])
        self.assertEqual(seen['up'][:7],[True]*6+[False])
        self.assertFalse(any(seen['down']))

    def test_overlapping_activation_rejected(self):
        points='<Point><position>1</position><activation_Price.amount>1</activation_Price.amount><imbalance_Price.category>A08</imbalance_Price.category></Point>'
        with self.assertRaises(ValueError):
            activation_arrays(xml_series(points,True),date(2026,1,1))

    def test_gap_classification_distinguishes_source_null_and_no_report(self):
        runs=list(gap_runs([0,None,None,None,2],[True,True,True,False,True],100))
        self.assertEqual(runs,[(104,112,'source_explicit_null'),(112,116,'source_unreported')])


if __name__=='__main__':
    unittest.main()
