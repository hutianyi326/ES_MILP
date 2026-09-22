import unittest
from collections import defaultdict
from datetime import datetime,timedelta,timezone
from types import SimpleNamespace
from zoneinfo import ZoneInfo
from src.es_historical_conditional.perfect import prepare,events
from src.es_historical_conditional.adapter import IDS,KINDS,budget

TZ=ZoneInfo('Europe/Madrid');UTC=timezone.utc

def bundle(start,days=2):
    end=(start+timedelta(days=days)).astimezone(UTC);t=start.astimezone(UTC);grid=set()
    while t<end:grid.add(t);t+=timedelta(minutes=15)
    values={i:defaultdict(set) for i in IDS};spot={k:defaultdict(set) for k in KINDS};contracts={}
    for t in grid:
        for i in IDS:values[i][t]={100. if i in (632,633) else 0.}
        day=t.astimezone(TZ).date()
        for k in KINDS:
            if k=='ida3' and t.astimezone(TZ).hour<12:continue
            spot[k][t]={10.};cid=k+'-'+t.isoformat()
            contracts[cid]=dict(kind=k,day=day,slots=[t],prices={10.})
    return SimpleNamespace(grid=grid,values=values,spot=spot,contracts=contracts,sources=[])

class AdapterTests(unittest.TestCase):
    def test_first_day_closed_prices_not_required(self):
        start=datetime(2025,1,1,tzinfo=TZ);b=bundle(start)
        for t in b.grid:
            if t<(start+timedelta(days=1)).astimezone(UTC):
                for i in IDS:b.values[i][t]=set()
                for k in ('da','ida1','ida2'):b.spot[k][t]=set()
        inp,mask,ev,limits=prepare(b,start+timedelta(days=1))
        self.assertFalse(mask)
        self.assertEqual(len(inp.qhs),192)

    def test_e03_cross_year_budget_source_numeric_and_missing_rejected(self):
        start=datetime(2026,12,31,tzinfo=TZ);b=bundle(start)
        inp,mask,ev,limits=prepare(b,start+timedelta(days=1),formal_budget={2026:.2})
        self.assertEqual(inp.annual_efc_budget[2026],.2)
        self.assertAlmostEqual(inp.annual_efc_budget[2027],600/365)
        self.assertEqual(limits[2027]['kind'],'lookahead_only')
        with self.assertRaises(ValueError):prepare(b,start+timedelta(days=1),formal_budget={})

    def test_same_year_input_tail_does_not_increase_budget(self):
        start=datetime(2025,1,1,tzinfo=TZ)
        inp,*_=prepare(bundle(start),start+timedelta(days=1))
        self.assertAlmostEqual(inp.annual_efc_budget[2025],600/365)

    def test_e01_dst_day_budget_is_one_day(self):
        for start,count in ((datetime(2025,3,30,tzinfo=TZ),92),(datetime(2025,10,26,tzinfo=TZ),100)):
            b=bundle(start,1)
            self.assertEqual(len(b.grid),count);self.assertAlmostEqual(budget(b.grid)[2025],600/365)

    def test_null_tail_preserved_and_budget_not_inflated(self):
        start=datetime(2025,1,1,tzinfo=TZ);b=bundle(start)
        for t in b.grid:
            if t>=(start+timedelta(days=1)).astimezone(UTC):b.values[680][t]=set()
        inp,mask,ev,limits=prepare(b,start+timedelta(days=1))
        self.assertEqual(len(mask),96);self.assertEqual(ev['gaps'][0]['qh'],96)
        self.assertTrue(any(r['raw_values'][680] is None for r in ev['rows']))
        self.assertAlmostEqual(inp.annual_efc_budget[2025],600/365)
