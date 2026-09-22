"""Executable P0 boundary / ledger / energy acceptance fixtures."""
import json
import unittest
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from unittest.mock import patch
from zoneinfo import ZoneInfo
from tests.test_es_synthetic_market_rolling import fixture
from tests.test_es_synthetic_market_core import make_qh,make_contract,make_input
from src.es_synthetic_market.perfect import PerfectEngine
from src.es_synthetic_market.core import solve_joint

TZ=ZoneInfo('Europe/Madrid');UTC=timezone.utc

def daily(days=3,start=None):
    start=start or datetime(2025,1,1,tzinfo=TZ)
    end=start+timedelta(days=days)
    count=int((end.astimezone(UTC)-start.astimezone(UTC)).total_seconds()/900)
    inp=fixture(start,count,lambda i: -5 if i%96<48 else 20,True)
    cs=[];qs=[]
    for q,c in zip(inp.qhs,inp.contracts):
        midnight=q.start_utc.astimezone(TZ).replace(hour=0,minute=0)
        gate=(midnight-timedelta(hours=12)).astimezone(UTC)
        cs.append(replace(c,gate_close_utc=gate,result_release_utc=gate+timedelta(minutes=45)))
        qs.append(replace(q,afrr_gate_close_utc=gate+timedelta(hours=4),
            afrr_result_release_utc=gate+timedelta(hours=4,minutes=30),afrr_capacity_price_up_eur_per_mw_qh=.1))
    return replace(inp,qhs=tuple(qs),contracts=tuple(cs)), (end-timedelta(days=1)).astimezone(UTC)

class PerfectTests(unittest.TestCase):
    def engine(self,inp,end,**kw):return PerfectEngine(inp,execution_end=end,time_limit_seconds=10,history_mode='delta',**kw)

    def test_g01_today_missing_still_freezes_tomorrow_and_restart(self):
        inp,end=daily();mask={q.qh_id for q in inp.qhs[:96]}
        e=self.engine(inp,end,inactive=mask)
        self.assertTrue(e.step(),e.failure)
        self.assertAlmostEqual(e._soc,10)
        self.assertIn(inp.contracts[100].contract_id,e._orders)
        self.assertTrue(any(o.sell_mw+o.buy_mw>0 for o in e._orders.values()))
        self.assertEqual(e._ledger.total_cash_eur,0)
        cp=json.loads(json.dumps(e.checkpoint()))
        r=PerfectEngine.restore(inp,cp,execution_end=end,inactive=mask,time_limit_seconds=10,history_mode='delta')
        e.run();r.run()
        self.assertIsNone(e.failure);self.assertIsNone(r.failure)
        self.assertEqual(e._orders,r._orders)
        self.assertAlmostEqual(e._ledger.total_cash_eur,r._ledger.total_cash_eur)
        report=e.report();self.assertIsNone(report['rows'][0]['cash'])
        self.assertEqual(report['quality']['assumed_idle_hours'],24.)
        self.assertEqual(report['quality']['settlement_coverage'],.5)
        self.assertAlmostEqual(report['rows'][191]['soc'],10,places=5)
        self.assertEqual(len(report['rows']),192)
        keys=[tuple(x['key']) for w in e._windows for x in w.audit['frozen_delta']]
        self.assertEqual(len(keys),len(set(keys)))

    def test_f01_initial_zero_ledger(self):
        inp,end=daily();e=self.engine(inp,end);self.assertTrue(e.step(),e.failure)
        rows=e._windows[0].audit['frozen_delta']
        zero=[r for r in rows if r['reason']=='initial_closed_zero']
        self.assertTrue(zero);self.assertTrue(all(r['mw']==0 for r in zero))

    def test_h01_gct_binds_before_release(self):
        q=make_qh('q',datetime(2025,1,1,tzinfo=UTC));start=q.start_utc
        q=replace(q,afrr_gate_close_utc=start-timedelta(hours=1),afrr_result_release_utc=start)
        c1=replace(make_contract(q,'DA',0),gate_close_utc=start-timedelta(hours=3),result_release_utc=start-timedelta(hours=2))
        c2=replace(make_contract(q,'IDA',0),gate_close_utc=start-timedelta(minutes=30),result_release_utc=start)
        inp=make_input((q,),(0,),contracts_both=False)
        inp=replace(inp,contracts=(c1,c2),e_initial_mwh=100)
        kw=dict(fixed_spot_mw={c1.contract_id:(80,0),c2.contract_id:(0,20)},fixed_reserve_mw={'q':(40,0)},terminal_hard=False,remaining_annual_efc={2025:1.})
        self.assertTrue(solve_joint(inp,'D',**kw).feasible)
        self.assertFalse(solve_joint(inp,'D',**kw,reserve_headroom_from_gct=True).feasible)

    def test_t01_internal_terminal_even_with_high_tail_prices(self):
        inp,end=daily()
        inp=replace(inp,contracts=tuple(replace(c,price_eur_per_mwh=1e3) if c.delivery_start_utc>=end else c for c in inp.contracts))
        e=self.engine(inp,end);e.run();self.assertIsNone(e.failure)
        self.assertAlmostEqual(e._soc,10,places=5)
        self.assertTrue(all(datetime.fromisoformat(w.execute_end_utc)<=end for w in e._windows))

    def test_f04_objective_constant_tampering_rejected(self):
        inp,end=daily();e=self.engine(inp,end);self.assertTrue(e.step(),e.failure)
        import src.es_synthetic_market.rolling as roll
        original=roll.solve_joint
        def corrupt(*a,**kw):
            r=original(*a,**kw)
            return replace(r,residuals={**r.residuals,'eliminated_objective_constant_min':999999})
        before=e.checkpoint()
        with patch.object(roll,'solve_joint',corrupt):self.assertFalse(e.step())
        after=e.checkpoint()
        for k in ('index','soc','used','orders','reserves','ledger','windows'):
            self.assertEqual(before['state'][k],after['state'][k])

    def test_e04_reserve_is_availability_not_consumption(self):
        inp,end=daily(days=4);e=self.engine(inp,end)
        e._budget={2025:10.};e._used={2025:2.}
        _,_,_,remaining=e._window_input(e.inp.qhs[:192],e.inp.qhs[0].start_utc,e.inp.qhs[191].end_utc)
        self.assertAlmostEqual(remaining[2025],7.456520739130435)
        self.assertEqual(e._used[2025],2.)
        _,_,_,remaining=e._window_input(e.inp.qhs[96:288],e.inp.qhs[96].start_utc,e.inp.qhs[287].end_utc)
        self.assertAlmostEqual(remaining[2025],7.999999)

    def test_g02_all_missing_has_null_cash_and_no_free_soc(self):
        inp,end=daily();e=self.engine(inp,end,inactive={q.qh_id for q in inp.qhs})
        with patch('src.es_synthetic_market.rolling.solve_joint',side_effect=AssertionError('must skip MILP')):e.run()
        self.assertIsNone(e.failure);self.assertAlmostEqual(e._soc,10)
        self.assertIsNone(e.report()['months']['2025-01']['cash_eur'])

    def test_g02_gap_terminal_conflict(self):
        inp,end=daily();e=self.engine(inp,end,inactive={q.qh_id for q in inp.qhs});e._soc=80
        self.assertFalse(e.step());self.assertEqual(e.failure,'infeasible_terminal_with_gap')
        self.assertEqual(e._soc,80)

    def test_review_soc_noise_clamps_before_validation_without_state_write(self):
        inp,end=daily();e=self.engine(inp,end)
        for val,expected in ((10-1e-8,10.),(190+1e-8,190.)):
            e._soc=val
            win,*_=e._window_input(e.inp.qhs[:192],e.inp.qhs[0].start_utc,e.inp.qhs[191].end_utc)
            self.assertEqual(win.e_initial_mwh,expected);self.assertEqual(e._soc,val)
        e._soc=10-1e-3
        self.assertFalse(e.step());self.assertEqual(e._soc,10-1e-3)

    def test_g03_hour_contract_disabled_whole(self):
        inp,end=daily();c=replace(inp.contracts[100],contract_id='hour',delivery_end_utc=inp.qhs[103].end_utc,
            qh_weights={q.qh_id:1. for q in inp.qhs[100:104]})
        inp=replace(inp,contracts=tuple(x for x in inp.contracts if x not in inp.contracts[100:104])+(c,))
        e=self.engine(inp,end,inactive={inp.qhs[101].qh_id});self.assertTrue(e.step(),e.failure)
        self.assertEqual(e._orders['hour'].sell_mw+e._orders['hour'].buy_mw,0)
        mapped=e._windows[0].audit['solver_mapping']['contracts']['hour']
        self.assertEqual(mapped,dict(column=-1,constant=0.))

    def test_e02_same_year_tail_competes_for_budget(self):
        q=make_qh('q',datetime(2025,1,1,tzinfo=UTC));r=replace(q,qh_id='r',start_utc=q.end_utc,end_utc=q.end_utc+timedelta(minutes=15))
        inp=replace(make_input((q,r),(0,0),contracts_both=False),e_initial_mwh=100)
        pairs={c.contract_id:(50.,0.) for c in inp.contracts}
        # Each QH consumes 12.5/.92/360 EFC; the second is an observed future QH.
        kw=dict(fixed_spot_mw=pairs,terminal_hard=False,reserve_headroom_from_gct=True)
        self.assertTrue(solve_joint(inp,'D',remaining_annual_efc={2025:.08},**kw).feasible)
        self.assertFalse(solve_joint(inp,'D',remaining_annual_efc={2025:.06},**kw).feasible)

    def test_g03_frozen_conflict_no_clearing(self):
        from src.es_synthetic_market.rolling import RollingOrder
        inp,end=daily();e=self.engine(inp,end,inactive={inp.qhs[100].qh_id})
        c=inp.contracts[100]
        e._orders[c.contract_id]=RollingOrder(c.contract_id,20,0,'pending',c.gate_close_utc.isoformat(),c.result_release_utc.isoformat())
        self.assertFalse(e.step());self.assertIn('unresolved_commitment',e.failure)
        self.assertEqual(e._orders[c.contract_id].sell_mw,20)

    def test_dst_grids(self):
        for start,count in ((datetime(2025,3,29,tzinfo=TZ),188),(datetime(2025,10,25,tzinfo=TZ),196)):
            inp,end=daily(start=start);e=self.engine(inp,end)
            self.assertTrue(e.step(),e.failure);self.assertEqual(len(e._windows[0].planned_qh_ids),count)

if __name__=='__main__':unittest.main()
