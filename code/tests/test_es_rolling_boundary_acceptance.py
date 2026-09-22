"""Extra no-network boundary acceptance, without changing market assumptions."""
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from zoneinfo import ZoneInfo
import unittest
from src.es_synthetic_market import SyntheticMarketInput, solve_rolling
from tests.test_es_synthetic_market_core import make_qh,make_contract
from tests.test_es_synthetic_market_rolling import fixture

TZ=ZoneInfo('Europe/Madrid');UTC=timezone.utc

class TestRollingBoundaryAcceptance(unittest.TestCase):
    def test_autumn_25_hour_day_is_executed_once(self):
        start=datetime(2025,10,25,23,45,tzinfo=TZ)
        end=datetime(2025,10,27,0,15,tzinfo=TZ)
        n=int((end.astimezone(UTC)-start.astimezone(UTC)).total_seconds()/900)
        result=solve_rolling(fixture(start,n))
        self.assertTrue(result.success,result.failure)
        self.assertEqual([len(w.executed_qh_ids) for w in result.windows],[1,100,1])
        ids=[q for w in result.windows for q in w.executed_qh_ids]
        self.assertEqual(len(set(ids)),102)

    def test_gap_resets_soc_not_shared_annual_budget(self):
        starts=[datetime(2025,1,1,0,tzinfo=TZ),datetime(2025,1,1,3,tzinfo=TZ)]
        qhs=tuple(make_qh(f'{s}-{i}',start.astimezone(UTC)+timedelta(minutes=15*i),segment=str(s))
            for s,start in enumerate(starts) for i in range(2))
        contracts=tuple(make_contract(q,'DA',0 if i%2==0 else 100) for i,q in enumerate(qhs))
        inp=SyntheticMarketInput(qhs,contracts,annual_efc_budget={2025:.02},
            input_id='ES_SYNTHETIC_MARKET_GAP_ACCEPTANCE')
        result=solve_rolling(inp)
        self.assertTrue(result.success,result.failure)
        self.assertEqual(len(result.windows),2)
        self.assertAlmostEqual(result.windows[0].end_execution_soc_mwh,10)
        self.assertAlmostEqual(result.windows[1].start_soc_mwh,10)
        a,b=(w.efc_used_by_year[2025] for w in result.windows)
        self.assertGreater(a,0)
        self.assertAlmostEqual(a,.02,places=7)
        self.assertAlmostEqual(b-a,0,places=7)
        self.assertGreaterEqual(b+1e-9,a)
        self.assertLessEqual(b,inp.effective_annual_efc_budget[2025]+1e-6)

if __name__=='__main__':unittest.main()
