"""Scenario-at-a-time CLI retains exactly the old common-mask evidence."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
from tests.test_es_historical_conditional_adapter import fixture
from src.es_historical_conditional.adapter import four_scenarios,evidence_payload
from src.es_historical_conditional.__main__ import main

class TestStreamingScenarioCLI(unittest.TestCase):
    def test_evidence_matches_four_scenario_builder(self):
        root=Path(__file__).resolve().parents[1]
        b=fixture();expected=four_scenarios(b,common=True)
        with TemporaryDirectory(dir=root/'outputs/es_historical_conditional') as tmp:
            out=Path(tmp)/'qa'
            argv=['conditional','--start','2025-01-02','--end-exclusive','2025-01-03','--output',str(out)]
            with patch('sys.argv',argv),patch('src.es_historical_conditional.__main__.load_raw',return_value=b),patch('builtins.print'):
                main()
            for key,case in expected.items():
                actual=json.loads((out/('__'.join(key)+'_common_input.json')).read_text(encoding='utf-8'))
                wanted=json.loads(json.dumps(evidence_payload(b,case),default=str))
                self.assertEqual(actual,wanted)

    def test_preflight_only_defaults_to_rolling2_and_never_solves(self):
        root=Path(__file__).resolve().parents[1];b=fixture()
        with TemporaryDirectory(dir=root/'outputs/es_historical_conditional') as tmp:
            out=Path(tmp)/'preflight'
            argv=['conditional','--start','2025-01-02','--end-exclusive','2025-01-03',
                  '--output',str(out),'--preflight-only']
            with patch('sys.argv',argv),patch('src.es_historical_conditional.__main__.load_raw',return_value=b),\
                 patch('src.es_historical_conditional.__main__.economic_trial') as solve,patch('builtins.print'):
                main()
            solve.assert_not_called()
            preflight=json.loads((out/'preflight.json').read_text(encoding='utf-8'))
            self.assertEqual(preflight['selection']['modes'],['rolling2'])
            self.assertEqual(preflight['selection']['orders'],['U','D'])
            self.assertEqual(len(preflight['selection']['run_matrix']),8)
            self.assertFalse(preflight['solver']['experimental_a1_a3'])
            self.assertFalse(preflight['economic_solve_requested'])
            self.assertFalse(preflight['economic_solve_started_when_written'])
            self.assertFalse(preflight['output_plan']['checkpoint_persistence'])
            self.assertFalse(preflight['output_plan']['resume_from_disk'])
            self.assertEqual({p.name for p in out.iterdir()},{'preflight.json','summary.json'})

if __name__=='__main__':unittest.main()
