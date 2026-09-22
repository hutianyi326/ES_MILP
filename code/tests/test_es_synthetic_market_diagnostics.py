"""C-stage synthetic pressure diagnostics."""
from datetime import datetime, timedelta, timezone
import unittest

from src.es_synthetic_market.diagnostics import (
    DiagnosticQH, DiagnosticSnapshot, build_frozen_snapshot,
    make_snapshot, replay_pressure, run_fixed_order_comparison,
)

UTC = timezone.utc


def qh(i, *, alpha_up=.2, alpha_down=.2, baseline=0., up=20., down=20., committed=True):
    start = datetime(2025, 1, 1, tzinfo=UTC) + timedelta(minutes=15*i)
    if not committed: baseline = up = down = 0.
    return DiagnosticQH(str(i), start, start + timedelta(minutes=15), "s", 2025,
                       baseline, up, down, alpha_up, alpha_down, committed)


class TestDiagnostics(unittest.TestCase):
    def test_six_paths_keep_raw_soc_and_recovery(self):
        snap = DiagnosticSnapshot(qh(0, baseline=0., up=100., down=0.), 11., qh(0).start_utc, efc_budget_by_year={2025:600.})
        result = replay_pressure(snap)
        self.assertEqual(set(result.paths), {"none", "only_up", "only_down", "up_then_down", "down_then_up", "main"})
        self.assertFalse(result.paths["only_up"].feasible)
        self.assertGreater(result.paths["only_up"].max_lower_violation_mwh, 0)
        self.assertGreater(result.paths["only_up"].recovery["needed_dc_mwh"], 0)
        self.assertEqual(result.paths["only_up"].pulse_minutes, 15.)

    def test_tail_uses_main_alpha_and_does_not_clip(self):
        first = qh(0, baseline=0., up=100., down=0.)
        tail = qh(1, alpha_up=1., alpha_down=0., baseline=100., up=0., down=0.)
        snap = DiagnosticSnapshot(first, 11., first.start_utc, (tail,), efc_budget_by_year={2025:600.})
        result = replay_pressure(snap)
        only = result.paths["only_up"]
        self.assertEqual(only.validation_minutes, 30.)
        self.assertGreater(only.max_lower_violation_mwh, 0)
        self.assertLess(only.final_soc_mwh, 10.)
        self.assertEqual(len(only.records), 2)

    def test_u_and_d_are_same_fixed_orders(self):
        snap = DiagnosticSnapshot(qh(0), 100., qh(0).start_utc, efc_budget_by_year={2025:600.})
        comparison = run_fixed_order_comparison(snap)
        self.assertTrue(comparison["same_fixed_orders"])
        self.assertFalse(comparison["pressure_feedback"])
        self.assertNotEqual(comparison["up_then_down"]["paths"]["main"]["order_mode"], comparison["down_then_up"]["paths"]["main"]["order_mode"])

    def test_gate_equality_includes_pending_and_later_gate_excludes(self):
        class Obj:
            def __init__(self, **kwargs): self.__dict__.update(kwargs)
        start = datetime(2025, 1, 1, tzinfo=UTC)
        q0 = Obj(qh_id="0", start_utc=start, end_utc=start+timedelta(minutes=15), segment_id="s", madrid_year=2025, alpha_up=0., alpha_down=0., afrr_gate_close_utc=start)
        q1 = Obj(qh_id="1", start_utc=start+timedelta(minutes=15), end_utc=start+timedelta(minutes=30), segment_id="s", madrid_year=2025, alpha_up=0., alpha_down=0., afrr_gate_close_utc=start+timedelta(seconds=1))
        c0 = Obj(contract_id="c0", gate_close_utc=start, qh_weights={"0": 1.})
        c1 = Obj(contract_id="c1", gate_close_utc=start+timedelta(seconds=1), qh_weights={"1": 1.})
        orders = {"c0": Obj(contract_id="c0", sell_mw=20., buy_mw=0., status="pending"), "c1": Obj(contract_id="c1", sell_mw=99., buy_mw=0., status="awarded")}
        snap = build_frozen_snapshot([q0, q1], [c0, c1], orders, {}, 0, initial_soc_mwh=100., efc_budget_by_year={2025:600.})
        self.assertEqual(snap.qh.baseline_mw, 20.)
        self.assertEqual(snap.tail, ())
        self.assertTrue(snap.source_order_hash)

    def test_physical_gap_is_rejected(self):
        first = qh(0)
        gap = qh(1, committed=False)
        later = qh(2, committed=True)
        later = DiagnosticQH(later.qh_id, later.start_utc + timedelta(minutes=15), later.end_utc + timedelta(minutes=15), later.segment_id, later.madrid_year, later.baseline_mw, later.reserve_up_mw, later.reserve_down_mw, later.alpha_up, later.alpha_down, later.committed)
        with self.assertRaises(ValueError):
            make_snapshot((first, gap, later), 0, initial_soc_mwh=100., submitted_qh_ids={"0", "2"})


if __name__ == "__main__":
    unittest.main()
