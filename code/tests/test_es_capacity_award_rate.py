"""Capacity-revenue proxy and source-calendar regression checks."""
import unittest
from copy import deepcopy
from dataclasses import replace
from datetime import date, datetime, timezone
from contextlib import redirect_stderr
from io import StringIO
import math
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch

from project.prepare_es_afrr_award_rates import day_grid, ratio
from project.compare_es_capacity_award_sensitivity import comparison_normalizer
from project.resume_es_capacity_award_rate import resume_settings
from project.run_es_perfect_v1 import apply_posthoc_capacity_rates,main as run_main
from tests.test_es_perfect_v1 import daily
from tests.test_es_synthetic_market_core import make_input, make_qh
from src.es_synthetic_market.core import FixedCommitment, solve_joint
from src.es_synthetic_market.perfect import PerfectEngine


class AwardRateTests(unittest.TestCase):
    def test_source_ratio_and_dst(self):
        self.assertEqual(ratio(2000, 1000), (0.5, 0.5, 'valid'))
        self.assertEqual(ratio(2000, 0), (0.0, 0.0, 'zero_allocated'))
        self.assertEqual(ratio(0, 0), (None, None, 'zero_market'))
        self.assertEqual(ratio(1000, 1100), (1.1, None, 'allocated_exceeds_offer'))
        self.assertEqual(len(day_grid(date(2025, 3, 30))), 92)
        self.assertEqual(len(day_grid(date(2025, 10, 26))), 100)
        self.assertEqual(len(set(day_grid(date(2025, 10, 26)))), 100)

    def test_capacity_objective_cash_and_missing_direction(self):
        q = make_qh('q', datetime(2025, 1, 1, tzinfo=timezone.utc), cap_up=10, cap_down=10)
        base = solve_joint(make_input((q,), (0,), contracts_both=False), 'D')
        all_awarded = solve_joint(make_input((replace(q, afrr_award_rate_up=1.0,
                                                   afrr_award_rate_down=1.0),), (0,),
                                             contracts_both=False), 'D')
        self.assertEqual(base.reserve_up_mw, all_awarded.reserve_up_mw)
        self.assertEqual(base.reserve_down_mw, all_awarded.reserve_down_mw)
        self.assertAlmostEqual(base.objective_gross_eur, all_awarded.objective_gross_eur)
        half = replace(q, afrr_award_rate_up=0.5, afrr_award_rate_down=0.25)
        sensitive = solve_joint(make_input((half,), (0,), contracts_both=False), 'D')
        self.assertTrue(base.feasible and sensitive.feasible)
        self.assertAlmostEqual(base.reserve_up_mw['q'], sensitive.reserve_up_mw['q'])
        self.assertAlmostEqual(base.reserve_down_mw['q'], sensitive.reserve_down_mw['q'])
        self.assertAlmostEqual(sensitive.cash_breakdown_eur['capacity'],
            5 * sensitive.reserve_up_mw['q'] + 2.5 * sensitive.reserve_down_mw['q'])
        self.assertAlmostEqual(sensitive.objective_gross_eur, sensitive.cash_breakdown_eur['capacity'])
        missing = replace(q, afrr_award_rate_up=None, afrr_award_rate_down=0)
        skipped = solve_joint(make_input((missing,), (0,), contracts_both=False), 'D')
        self.assertTrue(skipped.feasible)
        self.assertEqual((skipped.reserve_up_mw['q'], skipped.reserve_down_mw['q']), (0, 0))

    def test_frozen_reserve_uses_same_effective_price(self):
        q = replace(make_qh('q', datetime(2025, 1, 1, tzinfo=timezone.utc), cap_up=10),
                    afrr_award_rate_up=0.5)
        inp = make_input((q,), (0,), contracts_both=False)
        result = solve_joint(inp, 'D', fixed_reserve_mw={'q': (40, 0)})
        self.assertTrue(result.feasible, result.message)
        self.assertAlmostEqual(result.objective_gross_eur, 200)
        self.assertAlmostEqual(result.cash_breakdown_eur['capacity'], 200)
        carried = make_input((q,), (0,), contracts_both=False,
                             fixed=(FixedCommitment('q', reserve_up_mw=40),))
        carried_result = solve_joint(carried, 'D')
        self.assertTrue(carried_result.feasible, carried_result.message)
        self.assertAlmostEqual(carried_result.cash_breakdown_eur['fixed'], 200)
        self.assertAlmostEqual(carried_result.objective_gross_eur,
            sum(carried_result.cash_breakdown_eur.values()))

    def test_rolling_ledger_and_checkpoint_use_proxy(self):
        inp, end = daily()
        qhs = tuple(replace(q, afrr_capacity_price_up_eur_per_mw_qh=30,
                            afrr_award_rate_up=0.5) for q in inp.qhs)
        inp = replace(inp, qhs=qhs)
        engine = PerfectEngine(inp, execution_end=end, capacity_award_sensitivity=True,
                               time_limit_seconds=10, history_mode='delta')
        self.assertTrue(engine.step(), engine.failure)
        self.assertTrue(engine.step(), engine.failure)
        positive = [e for e in engine._ledger.snapshot()
                    if e['settlement_type'] == 'aFRR_capacity' and e['direction'] == 'up'
                    and e['quantity'] > 0]
        self.assertTrue(positive)
        self.assertTrue(all(abs(e['cash_eur'] - e['quantity'] * 15) < 1e-5 for e in positive))
        cp = engine.checkpoint()
        restored = PerfectEngine.restore(inp, cp, execution_end=end,
            capacity_award_sensitivity=True, time_limit_seconds=10, history_mode='delta')
        self.assertEqual(restored._ledger.total_cash_eur, engine._ledger.total_cash_eur)
        with self.assertRaisesRegex(ValueError, 'checkpoint integrity/input/configuration mismatch'):
            PerfectEngine.restore(inp, cp, execution_end=end,
                capacity_award_sensitivity=False, time_limit_seconds=10, history_mode='delta')

    def test_resume_settings_supports_new_modes_and_legacy_checkpoint(self):
        self.assertEqual(resume_settings(dict(capacity_award_mode='optimize',
            run_id='ES_HISTORICAL_CONDITIONAL_PERFECT_V1_CAP_RATE_OPT')),
            ('optimize','ES_HISTORICAL_CONDITIONAL_PERFECT_V1_CAP_RATE_OPT',True))
        self.assertEqual(resume_settings(dict(capacity_award_mode='posthoc',
            run_id='ES_HISTORICAL_CONDITIONAL_PERFECT_V1_CAP_RATE_POSTHOC')),
            ('posthoc','ES_HISTORICAL_CONDITIONAL_PERFECT_V1_CAP_RATE_POSTHOC',False))
        self.assertEqual(resume_settings(dict(award_rate_source={'sha256':'legacy'})),
            ('optimize','ES_HISTORICAL_CONDITIONAL_PERFECT_V1_CAP_RATE',True))

    def test_comparison_rejects_posthoc_as_reoptimized_and_uses_real_power(self):
        base=dict(capacity_award_mode='full_fill')
        inp=dict(discharge_mw=200.)
        with self.assertRaisesRegex(ValueError,'must use capacity_award_mode=optimize'):
            comparison_normalizer(base,dict(capacity_award_mode='posthoc'),inp,inp)
        self.assertEqual(comparison_normalizer(base,dict(capacity_award_mode='optimize'),inp,inp),
                         (200.,200000.))

    def test_cli_requires_rate_file_only_for_sensitivity_modes(self):
        with TemporaryDirectory() as tmp:
            output=Path(tmp)/'run'
            cases=(
                (['--start','2025-01-01','--end','2025-01-02','--output',str(output),
                  '--capacity-award-mode','optimize'],),
                (['--start','2025-01-01','--end','2025-01-02','--output',str(output),
                  '--award-rate-file','rates.csv.gz'],),
            )
            for (arguments,) in cases:
                with self.subTest(arguments=arguments),patch('sys.argv',['run_es_perfect_v1.py',*arguments]),\
                     redirect_stderr(StringIO()),self.assertRaises(SystemExit) as error:
                    run_main()
                self.assertEqual(error.exception.code,2)
                self.assertFalse(output.exists())

    def test_posthoc_adjusts_capacity_only_reconciles_and_rejects_reapplication(self):
        inp,end=daily(days=3)
        inp=replace(inp,qhs=tuple(replace(q,afrr_capacity_price_up_eur_per_mw_qh=100.,
                                         afrr_capacity_price_down_eur_per_mw_qh=100.)
                                   for q in inp.qhs))
        engine=PerfectEngine(inp,execution_end=end,time_limit_seconds=10,history_mode='delta')
        engine.run()
        self.assertIsNone(engine.failure,engine.failure)
        orders_before=deepcopy(engine._orders)
        reserves_before=deepcopy(engine._reserves)
        checkpoint_before=engine.checkpoint()
        ledger=engine._ledger.snapshot()
        report=engine.report()
        raw_capacity=sum(e['cash_eur'] for e in ledger if e['settlement_type']=='aFRR_capacity')
        factors={(q.qh_id,direction):dict(rate=rate) for q in inp.qhs
                 for direction,rate in (('up',0.5),('down',0.25))}
        apply_posthoc_capacity_rates(report,ledger,factors,inp.discharge_mw)
        adjusted_capacity=sum(e['cash_eur'] for e in ledger if e['settlement_type']=='aFRR_capacity')
        expected_capacity=sum(e['unadjusted_cash_eur']*factors[(e['object_id'],e['direction'])]['rate']
                              for e in ledger if e['settlement_type']=='aFRR_capacity')
        self.assertAlmostEqual(adjusted_capacity,expected_capacity)
        self.assertNotAlmostEqual(adjusted_capacity,raw_capacity)
        report_cash=sum(sum(month['cash_eur'].values()) for month in report['months'].values()
                        if month['cash_eur'] is not None)
        self.assertTrue(math.isclose(report_cash,sum(e['cash_eur'] for e in ledger),rel_tol=1e-9,abs_tol=1e-6))
        self.assertEqual(engine._orders,orders_before)
        self.assertEqual(engine._reserves,reserves_before)
        self.assertEqual(engine.checkpoint(),checkpoint_before)
        self.assertIn('checkpoint retains full_fill solver state',report['cash_basis'])
        cash_after_first=deepcopy([e['cash_eur'] for e in ledger])
        with self.assertRaisesRegex(ValueError,'already been applied'):
            apply_posthoc_capacity_rates(report,ledger,factors,inp.discharge_mw)
        self.assertEqual([e['cash_eur'] for e in ledger],cash_after_first)


if __name__ == '__main__':
    unittest.main()
