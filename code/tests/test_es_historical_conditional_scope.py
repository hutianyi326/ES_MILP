"""Scope and provenance gates for the historical-conditional core path.

These tests do not read raw data or run a historical revenue calculation.
They only prove that a conditional input/result cannot be labelled synthetic.
"""

from datetime import datetime, timedelta, timezone
import unittest

from src.es_synthetic_market.core import QHInput, SyntheticMarketInput
from src.es_synthetic_market.integration import run_four_combinations
from src.es_synthetic_market.rolling import RollingEngine


UTC = timezone.utc


def _qh():
    start = datetime(2025, 1, 2, tzinfo=UTC)
    return QHInput(
        qh_id="conditional-q0",
        start_utc=start,
        end_utc=start + timedelta(minutes=15),
        segment_id="segment-a",
        madrid_year=2025,
        alpha_up=0.0,
        alpha_down=0.0,
        afrr_gate_close_utc=start,
        afrr_result_release_utc=start,
    )


def _conditional(**kwargs):
    values = dict(
        qhs=(_qh(),),
        contracts=(),
        annual_efc_budget={2025: 600.0},
        input_id="ES_HISTORICAL_CONDITIONAL_TEST",
        data_scope="historical_conditional",
        research_provenance="manifest-sha256:test",
    )
    values.update(kwargs)
    return SyntheticMarketInput(**values)


class TestHistoricalConditionalScope(unittest.TestCase):
    def test_synthetic_default_is_unchanged(self):
        inp = SyntheticMarketInput(
            qhs=(_qh(),), contracts=(), annual_efc_budget={2025: 600.0},
            input_id="ES_SYNTHETIC_MARKET_TEST",
        )
        self.assertEqual(inp.data_scope, "synthetic")
        self.assertEqual(inp.research_provenance, "")

    def test_conditional_requires_namespace_and_provenance(self):
        inp = _conditional()
        self.assertEqual(inp.data_scope, "historical_conditional")
        self.assertEqual(inp.research_provenance, "manifest-sha256:test")
        with self.assertRaises(ValueError):
            _conditional(research_provenance="")
        with self.assertRaises(ValueError):
            _conditional(input_id="ES_SYNTHETIC_MARKET_NOT_CONDITIONAL")

    def test_conditional_rolling_window_preserves_scope(self):
        inp = _conditional()
        engine = RollingEngine(inp, run_id="ES_HISTORICAL_CONDITIONAL_ROLLING_U", order_mode="U")
        win, _, _, _ = engine._window_input(inp.qhs, inp.qhs[0].start_utc, inp.qhs[-1].end_utc)
        self.assertEqual(win.data_scope, "historical_conditional")
        self.assertEqual(win.research_provenance, inp.research_provenance)
        self.assertTrue(win.input_id.startswith("ES_HISTORICAL_CONDITIONAL_"))

    def test_integration_rejects_synthetic_run_label_for_conditional_input(self):
        with self.assertRaises(ValueError):
            run_four_combinations(_conditional(), run_id="ES_SYNTHETIC_C")


if __name__ == "__main__":
    unittest.main()
