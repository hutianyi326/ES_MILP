import json
import tempfile
import unittest
from pathlib import Path

from project.build_es_result_presentation import (MARKETS, _expected_qh_for_day,
    _money_table, _nice_tick_step, _rolling_12m, _rolling_12m_svg,
    _rolling_12m_table, _rolling_v1_from_monthly_csv, aggregate, average_capacity)


class ResultPresentationTests(unittest.TestCase):
    def test_month_and_hour_aggregation_requires_complete_valid_hours(self):
        rows = []
        for minute in (0, 15, 30, 45):
            rows.append({
                'qh_id': f'qh-{minute}', 'time': f'2024-12-31T23:{minute:02d}:00+00:00',
                'status': 'valid', 'cash': {m: (250.0 if m == 'DA' else 0.0) for m in MARKETS},
                'efc': 0.25,
            })
        rows.append({'qh_id': 'missing', 'time': '2025-01-01T00:00:00+00:00',
                     'status': 'assumed_idle', 'cash': None, 'efc': 0.0})
        data = aggregate(rows, discharge_mw=100.0)
        self.assertEqual(data['monthly']['2025-01']['valid_qh'], 4)
        self.assertEqual(data['monthly']['2025-01']['total_qh'], 5)
        self.assertAlmostEqual(data['market_eur']['DA'], 1000.0)
        self.assertAlmostEqual(data['total_efc'], 1.0)
        self.assertEqual(len(data['complete_hours']), 1)
        self.assertAlmostEqual(data['hours'][0]['components']['DA'], 0.01)
        self.assertEqual(data['hours'][1]['count'], 0)
        self.assertAlmostEqual(data['monthly_hours']['2025-01'][0]['total_kEUR_per_MW'], 0.01)
        self.assertEqual(_expected_qh_for_day('2025-03-30'), 92)
        self.assertEqual(_expected_qh_for_day('2025-10-26'), 100)

    def test_average_capacity_nets_energy_and_converts_activation_to_mw(self):
        qh = '2025-01-01T00:00:00Z'
        ledger = [
            {'settlement_type': 'DA_energy', 'object_id': json.dumps(['da-id', qh]), 'direction': 'sell', 'quantity': 60},
            {'settlement_type': 'DA_energy', 'object_id': json.dumps(['da-buy', qh]), 'direction': 'buy', 'quantity': 100},
            {'settlement_type': 'IDA_energy', 'object_id': json.dumps(['id-1', qh]), 'direction': 'sell', 'quantity': 80},
            {'settlement_type': 'IDA_energy', 'object_id': json.dumps(['id-2', qh]), 'direction': 'buy', 'quantity': 30},
            {'settlement_type': 'aFRR_capacity', 'object_id': qh, 'direction': 'up', 'quantity': 30},
            {'settlement_type': 'aFRR_capacity', 'object_id': qh, 'direction': 'down', 'quantity': 20},
            {'settlement_type': 'aFRR_activation', 'object_id': qh, 'direction': 'up',
             'quantity': 2.5, 'quantity_unit': 'MWh', 'hours': 0.25},
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'ledger.json'
            path.write_text(json.dumps(ledger), encoding='utf-8')
            actual = average_capacity(path, {qh}, total_qh=2)
        self.assertAlmostEqual(actual['DA'], -20.0)
        self.assertAlmostEqual(actual['ID'], 25.0)
        self.assertAlmostEqual(actual['spot_net_da_id'], 5.0)
        self.assertAlmostEqual(actual['cap_up'], 15.0)
        self.assertAlmostEqual(actual['cap_down'], 10.0)
        self.assertAlmostEqual(actual['act_up'], 5.0)
        self.assertAlmostEqual(actual['act_down'], 0.0)

    def test_month_table_lists_all_months_and_annual_monthly_average(self):
        months = {
            '2025-01': {'cash_eur': {m: 1000.0 if m == 'DA' else 0.0 for m in MARKETS}},
            '2025-02': {'cash_eur': {m: 3000.0 if m == 'DA' else 0.0 for m in MARKETS}},
        }
        table = _money_table(months, 100.0, [2025], per_mw=False)
        self.assertIn('2025/01', table)
        self.assertIn('2025/02', table)
        self.assertIn('2025年月均（2个月）', table)
        self.assertIn('2025年合计', table)
        self.assertIn('**2.00**', table)

    def test_chart_tick_steps_use_clear_integer_intervals(self):
        self.assertEqual(_nice_tick_step(8250), 1000)
        self.assertEqual(_nice_tick_step(90), 10)
        self.assertEqual(_nice_tick_step(150), 20)

    def test_rolling_12_month_revenue_uses_consecutive_calendar_months(self):
        months = {}
        for index in range(13):
            year, month_index = divmod(2025 * 12 + index, 12)
            key = f'{year:04d}-{month_index + 1:02d}'
            months[key] = {'cash_eur': {m: (index + 1) * 1000.0 if m == 'DA' else 0.0
                                        for m in MARKETS}}
        rolling = _rolling_12m(months, discharge_mw=100.0)
        self.assertEqual(len(rolling), 2)
        self.assertEqual(rolling[0]['window_start'], '2025-01')
        self.assertEqual(rolling[0]['window_end'], '2025-12')
        self.assertAlmostEqual(rolling[0]['kEUR'], 78.0)
        self.assertAlmostEqual(rolling[0]['kEUR_per_MW'], 0.78)
        self.assertEqual(rolling[1]['window_start'], '2025-02')
        self.assertEqual(rolling[1]['window_end'], '2026-01')
        self.assertAlmostEqual(rolling[1]['kEUR'], 90.0)

    def test_v1_rolling_is_calendar_aligned_and_chart_table_show_both_scenarios(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'monthly.csv'
            path.write_text('month,v1_total_kEUR_per_MW\n' + ''.join(
                f'2025-{month:02d},1.00\n' for month in range(1, 13)), encoding='utf-8')
            v1 = _rolling_v1_from_monthly_csv(path)
            self.assertEqual(len(v1), 1)
            self.assertEqual(v1[0]['window_start'], '2025-01')
            self.assertAlmostEqual(v1[0]['kEUR_per_MW'], 12.0)
            current = [{'month': '2025-12', 'window_start': '2025-01',
                        'window_end': '2025-12', 'kEUR_per_MW': 10.0}]
            table = _rolling_12m_table(current, v1)
            self.assertIn('V1 100%中标', table)
            self.assertIn('| 2.00 |', table)
            svg = Path(directory) / 'chart.svg'
            _rolling_12m_svg(current, svg, v1)
            content = svg.read_text(encoding='utf-8')
            self.assertIn('#2878a5', content)
            self.assertIn('#e87522', content)
            self.assertIn('V1（100%中标）', content)


if __name__ == '__main__':
    unittest.main()
