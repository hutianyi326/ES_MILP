import copy
import csv
import io
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

from project.build_es_result_presentation import (
    MARKETS, MADRID, aggregate, build, _annual_data, _chart_svg, _fmt,
    _hourly_csv, _monthly_csv, _money_table, _rolling_12m, _shares, _validate_baseline,
)


def row(t, value=1., settled=True, efc=0.1):
    return dict(qh_id=t.isoformat(), time=t.isoformat(), status='valid' if settled else 'assumed_idle',
                cash={m: value if m == 'DA' else 0. for m in MARKETS} if settled else None, efc=efc)


def fixture(path, mode='full_fill', settled=True, blocked=0):
    path.mkdir()
    start=datetime(2025,1,1,tzinfo=MADRID); end=start+timedelta(hours=1)
    config=dict(charge_mw=100.,discharge_mw=100.,e_min_mwh=10.,e_max_mwh=190.,
                e_initial_mwh=10.,e_terminal_mwh=10.,eta_charge=.92,eta_discharge=.92,
                reserve_limit_up_mw=100.,reserve_limit_down_mw=100.,grid_import_mw=100.,grid_export_mw=100.,data_scope='historical_conditional')
    manifest=dict(mode='perfect_history_v1',scenario='ts_start/cap_old/D',capacity_award_mode=mode,
                  formal_start=start.isoformat(),formal_end=end.isoformat(),input_end=(end+timedelta(days=1)).isoformat())
    rows=[row(start+timedelta(minutes=15*i), -0.00001, settled, 0.3) for i in range(4)]
    # The observation QH has large cash and must never reach formal statistics.
    rows.append(row(end,999999.))
    objects={'manifest.json':manifest,'summary.json':dict(success=True,annual_budget={'2025':2.},quality={'blocked_qh':blocked}),
             'solver_input.json':config,'result.json':dict(rows=rows,months={}), 'cash_ledger.json':[]}
    for name,value in objects.items():
        (path/name).write_text(json.dumps(value,indent=2),encoding='utf-8')
    return dict(manifest=manifest,summary=objects['summary.json'],config=config,start=start,end=end,mode=mode)


class BaselineTests(unittest.TestCase):
    def test_missing_rows_are_in_denominator_and_duplicate_rows_rejected(self):
        start=datetime(2025,1,1,tzinfo=MADRID)
        data=aggregate([row(start)],100,start,start+timedelta(hours=1))
        self.assertEqual((data['valid_qh'],data['total_qh'],data['missing_result_qh']),(1,4,3))
        self.assertFalse(data['complete_hours'])
        with self.assertRaises(ValueError):
            aggregate([row(start),row(start)],100)

    def test_missing_month_and_real_zero_are_distinct(self):
        a=datetime(2025,1,1,tzinfo=MADRID);b=datetime(2025,2,1,tzinfo=MADRID)
        data=aggregate([row(a,settled=False,efc=None),row(b,value=0.)],100)
        records=list(csv.DictReader(io.StringIO(_monthly_csv(data['monthly'],100))))
        self.assertEqual(records[0]['total_kEUR'],'')
        self.assertEqual(records[1]['total_kEUR'],'0.00')
        table=_money_table(data['monthly'],100,[2025],False)
        self.assertIn('2025年月均（1个月）',table)
        self.assertIn('| 2025/01 | —',table)
        self.assertNotIn('100.00%',_shares(data['monthly'])[0])

    def test_rolling_requires_valid_calendar_months(self):
        months={f'2025-{m:02d}':dict(cash_eur={'DA':1000.},valid_qh=50,total_qh=100,calendar_complete=True) for m in range(1,13)}
        valid=_rolling_12m(months,100)
        self.assertEqual(valid[0]['valid_qh'],600)
        self.assertEqual(valid[0]['total_qh'],1200)
        months['2025-01']['calendar_complete']=False
        self.assertEqual(_rolling_12m(months,100),[])
        months['2025-01']['calendar_complete']=True
        months['2025-02']['valid_qh']=0
        self.assertEqual(_rolling_12m(months,100),[])

    def test_dst_repeated_hour_and_missing_one_quarter(self):
        start=datetime(2025,10,26,0,tzinfo=timezone.utc)
        rows=[row(start+timedelta(minutes=15*i)) for i in range(8)]
        data=aggregate(rows,100)
        self.assertEqual(data['hours'][2]['count'],2)
        self.assertEqual(aggregate(rows[:-1],100)['hours'][2]['count'],1)
        records=list(csv.DictReader(io.StringIO(_hourly_csv(data['hours']))))
        self.assertEqual(records[0]['total_kEUR_per_MW'],'')

    def test_complete_days_and_leap_year_denominator(self):
        start=datetime(2024,2,29,tzinfo=MADRID);end=start+timedelta(days=1)
        data=aggregate([row(start+timedelta(minutes=15*i)) for i in range(96)],100,start,end)
        annual=_annual_data(dict(data=data,start=start,end=end))[2024]
        self.assertEqual((annual['complete_days'],annual['total_days'],annual['year_days']),(1,1,366))

    def test_invalid_cash_and_power_fail_before_silent_zero(self):
        r=row(datetime(2025,1,1,tzinfo=MADRID));r['cash'].pop('ID')
        with self.assertRaises(ValueError): aggregate([r],100)
        with self.assertRaises(ValueError): aggregate([],float('nan'))

    def test_axes_cover_negative_positive_data_with_ten_intervals(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'chart.svg'
            _chart_svg('t','u',['a'],[{'components':dict(DA=96,ID=-4,cap_up=0,cap_down=0,act_up=0,act_down=0)}],p)
            root=ET.parse(p).getroot();ns={'s':'http://www.w3.org/2000/svg'}
            ticks=[int(n.text) for n in root.findall('s:text',ns) if n.attrib.get('class')=='tick']
            self.assertEqual(len(ticks),11)
            self.assertLessEqual(ticks[0],-4);self.assertGreaterEqual(ticks[-1],96)
            self.assertEqual(len(set(b-a for a,b in zip(ticks,ticks[1:]))),1)

    def test_modes_metadata_and_outputs(self):
        for mode in ('full_fill','optimize','posthoc'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as d:
                root=Path(d);fixture(root/'run',mode)
                p=build(root/'run',root/'report'); text=p.read_text(encoding='utf-8')
                self.assertIn({'full_fill':'本情景未启用容量收入折减','optimize':'进入容量收入目标后重新优化','posthoc':'交易决策沿用原解'}[mode],text)
                self.assertNotIn('两条线',text)
                self.assertIn('不足12个合格连续自然月',text)
                self.assertIn('未记录',text)
                self.assertEqual(len(list(p.parent.glob('*.svg'))),9)
                self.assertEqual(len(list(p.parent.glob('*.csv'))),7)
                evidence=json.loads((p.parent/'report_manifest.json').read_text(encoding='utf-8'))
                self.assertAlmostEqual(evidence['total_eur'],-.00004)
                self.assertAlmostEqual(evidence['total_efc'],1.2)
                self.assertNotIn('-0.00',text)
                total_line=next(line for line in text.splitlines() if line.startswith('| 合计 |'))
                self.assertEqual(total_line.count('|'),5)
                with self.assertRaises(FileExistsError): build(root/'run',root/'report')

    def test_all_missing_report_preserves_null_and_grid(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);fixture(root/'run',settled=False,blocked=4)
            p=build(root/'run',root/'report')
            text=p.read_text(encoding='utf-8')
            self.assertIn('存在未知执行状态',text)
            self.assertIn('不可定义',text)
            heat=(p.parent/'monthly_hourly_heatmap_kEUR_per_MW.svg').read_text(encoding='utf-8')
            self.assertIn('2025/01',heat);self.assertIn('—',heat)
            self.assertIsNone(json.loads((p.parent/'report_manifest.json').read_text(encoding='utf-8'))['total_eur'])

    def test_baseline_rejects_capacity_budget_mode_and_interval_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);a=fixture(root/'a','optimize');b=fixture(root/'b')
            _validate_baseline(a,b)
            changes=[('config','e_max_mwh',390.),('config','grid_import_mw',1.),('config','grid_export_mw',1.),('manifest','input_end','2026-09-05T00:00:00+02:00'),('manifest','input_end',None),('summary','annual_budget',{'2025':99.}),('manifest','mode','other')]
            for group,key,val in changes:
                other=copy.deepcopy(b);other[group][key]=val
                with self.assertRaises(ValueError):_validate_baseline(a,other)
            other=copy.deepcopy(b);other['end']+=timedelta(days=1)
            with self.assertRaises(ValueError):_validate_baseline(a,other)
            with self.assertRaises(ValueError):build(root/'a',root/'out',root/'legacy.csv')

    def test_money_rounding_preserves_finite_values_and_negative_signs(self):
        self.assertEqual(_fmt(-.00001),'0.00')
        self.assertEqual(_fmt(-1.25),'-1.25')
        with self.assertRaises(ValueError):_fmt(float('inf'))


if __name__=='__main__':
    unittest.main()
