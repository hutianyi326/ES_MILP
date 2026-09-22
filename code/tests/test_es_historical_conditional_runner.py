import unittest
from dataclasses import replace
from datetime import datetime
from tests.test_es_synthetic_market_rolling import fixture as rolling_fixture,TZ
from src.es_synthetic_market.rolling import RollingEngine
from src.es_historical_conditional.adapter import model_input,scenario
from src.es_historical_conditional.runner import rebuild_ledger,economic_trial
from tests.test_es_historical_conditional_adapter import fixture

class RunnerTests(unittest.TestCase):
    def test_nonzero_cross_midnight_all_four(self):
        inp=rolling_fixture(datetime(2025,1,1,23,45,tzinfo=TZ),4,lambda i:(-50,0,100,0)[i],True)
        inp=replace(inp,input_id='ES_HISTORICAL_CONDITIONAL_FIXTURE',data_scope='historical_conditional',research_provenance='synthetic-fixture-only')
        for mode in ('joint_full','rolling7','rolling2'):
            for order in ('U','D'):
                r=economic_trial(inp,'ES_HISTORICAL_CONDITIONAL_FIXTURE',mode,order,5)
                self.assertEqual(r['status'],'CONDITIONAL_PASS')
                self.assertGreater(r['valid_gross_eur'],0)
                self.assertAlmostEqual(r['cash_residual_eur'],0)
                self.assertEqual(len(r['input_configuration_hash']),64)
                self.assertEqual(r['solver_configuration']['time_limit_seconds'],5)
                self.assertEqual(r['solver_configuration']['planning_days'],
                    {'joint_full':None,'rolling7':7,'rolling2':2}[mode])

    def test_explicit_rolling_mode_and_planning_days_must_match(self):
        inp=rolling_fixture(datetime(2025,1,1,23,45,tzinfo=TZ),4)
        inp=replace(inp,input_id='ES_HISTORICAL_CONDITIONAL_FIXTURE',data_scope='historical_conditional',research_provenance='synthetic-fixture-only')
        with self.assertRaises(ValueError):
            economic_trial(inp,'ES_HISTORICAL_CONDITIONAL_FIXTURE','rolling2','U',5,planning_days=7)

    def test_default_trial_is_rolling2_u_with_experiment_disabled(self):
        inp=rolling_fixture(datetime(2025,1,1,23,45,tzinfo=TZ),4)
        inp=replace(inp,input_id='ES_HISTORICAL_CONDITIONAL_FIXTURE',data_scope='historical_conditional',research_provenance='synthetic-fixture-only')
        r=economic_trial(inp,'ES_HISTORICAL_CONDITIONAL_FIXTURE',time_limit=5)
        self.assertEqual((r['mode'],r['order']),('rolling2','U'))
        self.assertEqual(r['solver_configuration']['planning_days'],2)
        self.assertFalse(r['solver_configuration']['experimental_a1_a3'])

    def test_eight_local_days_window_and_scope(self):
        inp=rolling_fixture(datetime(2025,1,1,tzinfo=TZ),8*96,lambda i:10 if i%96<48 else 100)
        inp=replace(inp,input_id='ES_HISTORICAL_CONDITIONAL_8D',data_scope='historical_conditional',research_provenance='synthetic-fixture-only')
        eng=RollingEngine(inp,run_id='ES_HISTORICAL_CONDITIONAL_8D',time_limit_seconds=5)
        self.assertTrue(eng.step(),eng.failure)
        self.assertEqual(len(eng._windows[0].planned_qh_ids),2*96)
        self.assertEqual(len(eng._windows[0].executed_qh_ids),96)
        self.assertGreater(eng._windows[0].execution_cash_eur,0)

    def test_cash_anchor(self):
        b=fixture();inp=model_input(b,scenario(b,'ts_start','cap_old'))
        up={q.qh_id:20. for q in inp.qhs};down={q.qh_id:10. for q in inp.qhs}
        led=rebuild_ledger(inp,[],up,down,'ES_HISTORICAL_CONDITIONAL_TEST','test')
        # 4 QHs: capacity (20+10)*30, activation (20-10)*.25*.08*30.
        self.assertAlmostEqual(led.total_cash_eur,4*(900+6))
        self.assertEqual(len(led.entries),16)

    def test_no_past_gate_solve_and_labels(self):
        inp=model_input(fixture(),scenario(fixture(),'ts_start','cap_old'))
        for mode in ('joint_full','rolling7'):
            r=economic_trial(inp,'ES_HISTORICAL_CONDITIONAL_TEST',mode,'U',5)
            self.assertEqual(r['status'],'CONDITIONAL_PASS')
            self.assertAlmostEqual(r['valid_gross_eur'],0.)
            self.assertEqual(r['pressure_status'],'NOT_RUN')
            self.assertEqual(r['source_result']['data_scope'],'historical_conditional')

if __name__=='__main__':unittest.main()
