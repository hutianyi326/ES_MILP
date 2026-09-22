import unittest
from collections import defaultdict
from datetime import datetime,timedelta
from src.es_historical_conditional.adapter import (
    RawBundle,IDS,KINDS,QH,MADRID,UTC,grid_between,budget,complete_contracts,
    scenario,four_scenarios,model_input,nominal,CANCEL,digest)

def fixture(day=datetime(2025,1,2,tzinfo=MADRID),n=4):
    a=day.astimezone(UTC); grid={a+i*QH for i in range(n)}
    vals={i:defaultdict(set) for i in IDS};refs={i:defaultdict(list) for i in IDS}
    for t in grid|{a+n*QH}:
        for i in IDS:
            vals[i][t]={100. if i in (632,633) else 2. if i in (680,681) else 30.}
            refs[i][t]=[0]
    spots={k:defaultdict(set) for k in KINDS};cs={}
    for k in KINDS:
        slots=tuple(sorted(grid))
        if k=='ida3' and a.astimezone(MADRID).hour<12:continue
        cs[k]=dict(kind=k,day=day.date(),slots=slots,prices={50.},source_ids=[0])
        for t in grid:spots[k][t]={50.}
    return RawBundle(grid,vals,refs,cs,spots,[{'path':'fixture','sha256':'fixture'}],[])

class AdapterTests(unittest.TestCase):
    def test_shift_energy_and_price_not_capacity(self):
        b=fixture(); t=min(b.grid)
        b.values[680][t+QH]={4.};b.values[682][t+QH]={99.}
        s=scenario(b,'ts_start','cap_old');e=scenario(b,'ts_end','cap_old')
        self.assertEqual(s['series'][t]['alpha_up'],.08)
        self.assertEqual(e['series'][t]['alpha_up'],.16)
        self.assertEqual(e['series'][t]['values'][682],99.)
        self.assertEqual(e['series'][t]['values'][632],100.)
        self.assertEqual(e['series'][t]['provenance']['680']['raw_timestamp'],(t+QH).isoformat().replace('+00:00','Z'))

    def test_negative_price_and_capacity_direction(self):
        b=fixture();t=min(b.grid)
        b.values[2130][t]={12.};b.values[634][t]={5.};b.values[683][t]={-30.}
        inp=model_input(b,scenario(b,'ts_start','cap_old'));q=inp.qhs[0]
        self.assertEqual(q.afrr_capacity_price_up_eur_per_mw_qh*20,240)
        self.assertEqual(q.afrr_capacity_price_down_eur_per_mw_qh,5)
        self.assertEqual(q.afrr_activation_price_down_eur_per_mwh,30)
        self.assertEqual(inp.data_scope,'historical_conditional')
        self.assertFalse(inp.input_id.startswith('ES_SYNTHETIC_'))

    def test_strict_alpha_no_clipping(self):
        for iid,value in [(632,0),(633,-1),(680,-1),(680,25),(681,26)]:
            b=fixture();b.values[iid][min(b.grid)]={value}
            self.assertEqual(len(scenario(b,'ts_start','cap_old')['series']),0)

    def test_positive_tiny_alpha_preserved(self):
        b=fixture();t=min(b.grid);b.values[680][t]={1e-14}
        self.assertGreater(scenario(b,'ts_start','cap_old')['series'][t]['alpha_up'],0)

    def test_conflict_rejects_not_latest(self):
        b=fixture();b.values[682][min(b.grid)]={1.,2.}
        self.assertFalse(scenario(b,'ts_start','cap_old')['series'])

    def test_cancel_only_removes_that_session(self):
        b=fixture(datetime(2025,4,20,tzinfo=MADRID))
        self.assertIn(('ida1','2025-04-20'),CANCEL)
        b.spot['ida1'].clear();b.contracts.pop('ida1')
        self.assertEqual(len(scenario(b,'ts_start','cap_old')['series']),4)
        b.spot['ida2'].clear()
        self.assertFalse(scenario(b,'ts_start','cap_old')['series'])

    def test_contract_closure_iterates(self):
        p=set(range(6));cs={'a':{'slots':(0,1,2)},'b':{'slots':(2,3,4)},'c':{'slots':(4,5,6)}}
        self.assertEqual(complete_contracts(p,cs),set())

    def test_common_masks_closed_and_separate_hashes(self):
        b=fixture(n=8)
        # Two complete independent hours per market.
        for k in list(b.contracts):
            base=b.contracts.pop(k)
            for j in (0,4):b.contracts[k+str(j)]={**base,'slots':base['slots'][j:j+4]}
        b.values[680].pop(max(b.grid)+QH)
        own=four_scenarios(b); common=four_scenarios(b,common=True)
        self.assertEqual(len(own[('ts_start','cap_old')]['series']),8)
        self.assertEqual({len(c['series']) for c in common.values()},{4})
        self.assertEqual(len({c['manifest_hash'] for c in common.values()}),4)

    def test_dst_day_budget_and_half_day(self):
        for day in (datetime(2025,3,30,tzinfo=MADRID),datetime(2025,10,26,tzinfo=MADRID)):
            g=grid_between(day,day+timedelta(days=1))
            self.assertIn(len(g),(92,100));self.assertAlmostEqual(budget(g)[2025],600/365)
            self.assertAlmostEqual(budget(sorted(g)[:len(g)//2])[2025],300/365)

    def test_year_and_gap_shared_budget(self):
        a=datetime(2025,1,2,tzinfo=MADRID);b=datetime(2025,2,2,tzinfo=MADRID)
        p=grid_between(a,a+timedelta(days=1))|grid_between(b,b+timedelta(days=1))
        self.assertAlmostEqual(budget(p)[2025],1200/365)

    def test_nominal_dst_and_gate(self):
        b=fixture();s=model_input(b,scenario(b,'ts_start','cap_old'))
        n=model_input(b,scenario(b,'ts_start','cap_new'))
        self.assertEqual(n.qhs[0].afrr_gate_close_utc-s.qhs[0].afrr_gate_close_utc,timedelta(hours=1))
        self.assertFalse(s.new_order_allowed(s.qhs[0].afrr_gate_close_utc,'S0'))
        self.assertEqual(n.qhs[0].afrr_gate_close_utc.astimezone(MADRID).day,1)

if __name__=='__main__':unittest.main()
