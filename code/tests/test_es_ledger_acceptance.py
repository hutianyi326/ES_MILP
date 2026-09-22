"""Main-thread hand calculations for synthetic settlement, no market data."""
from dataclasses import replace
import unittest
from src.es_synthetic_market.ledger import SettlementLedger


class TestLedgerAcceptance(unittest.TestCase):
    def energy(self, ledger, **overrides):
        args = dict(run_id="ES_SYNTHETIC_MARKET_LEDGER", path="U",market="DA",
                    contract_id="contract",direction="sell",quantity_mw=10,
                    price_eur_per_mwh=50,qh_id="q0",hours=.25,execution_day="2025-01-01")
        args.update(overrides)
        return ledger.settle_energy(**args)

    def test_four_cash_types_match_hand_calculation(self):
        ledger=SettlementLedger()
        self.energy(ledger)
        self.energy(ledger,market="IDA",contract_id="adjust",direction="buy",quantity_mw=4,price_eur_per_mwh=30)
        common=dict(run_id="ES_SYNTHETIC_MARKET_LEDGER",path="U",qh_id="q0",direction="down",quantity=20,execution_day="2025-01-01")
        # Capacity price is already EUR/MW/period: no additional 0.25.
        ledger.settle_afrr(**common,kind="capacity",unit_price_eur=2,hours=1)
        ledger.settle_afrr(**common,kind="activation",unit_price_eur=-30,hours=.25*.4)
        self.assertEqual(ledger.cash_by_type(),{"DA_energy":125.,"IDA_energy":-30.,"aFRR_capacity":40.,"aFRR_activation":-60.})
        self.assertEqual(ledger.total_cash_eur,75.)

    def test_hourly_contract_slices_settle_once(self):
        ledger=SettlementLedger()
        for i in range(4):
            entry=self.energy(ledger,qh_id=str(i))
            ledger.record(entry)
        self.assertEqual(len(ledger.entries),4)
        self.assertEqual(ledger.total_cash_eur,500.)
        self.assertEqual(len({e.key for e in ledger.entries}),4)
        before=ledger.digest()
        ledger.extend(ledger.entries)
        self.assertEqual(ledger.digest(),before)

    def test_conflicting_duplicate_fails_without_changing_cash(self):
        ledger=SettlementLedger()
        entry=self.energy(ledger)
        with self.assertRaises(ValueError):
            ledger.record(replace(entry,cash_eur=entry.cash_eur+1))
        self.assertEqual(ledger.total_cash_eur,125.)

    def test_negative_energy_price_preserves_buy_and_sell_cash_signs(self):
        ledger=SettlementLedger()
        self.energy(ledger,price_eur_per_mwh=-10,direction="buy")
        self.energy(ledger,price_eur_per_mwh=-10,direction="sell",contract_id="other")
        self.assertEqual([e.cash_eur for e in ledger.entries],[25.,-25.])
        self.assertEqual(ledger.total_cash_eur,0.)

    def test_nonfinite_quantities_are_rejected(self):
        for value in (float("nan"),float("inf"),float("-inf")):
            with self.assertRaises(ValueError):
                self.energy(SettlementLedger(),quantity_mw=value)

    def test_non_cash_terminal_value_is_rejected(self):
        entry=self.energy(SettlementLedger())
        with self.assertRaises(ValueError):
            SettlementLedger().record(replace(entry,settlement_type="terminal_value"))

    def test_direct_entry_cannot_invent_cash(self):
        entry=self.energy(SettlementLedger())
        with self.assertRaises(ValueError):
            SettlementLedger().record(replace(entry,cash_eur=999))

    def test_contract_and_qh_ids_have_no_delimiter_collision(self):
        ledger=SettlementLedger()
        self.energy(ledger,contract_id="a|b",qh_id="c")
        self.energy(ledger,contract_id="a",qh_id="b|c")
        self.assertEqual(len(ledger.entries),2)
        self.assertEqual(ledger.total_cash_eur,250)

    def test_digest_is_independent_of_insertion_order(self):
        a,b=SettlementLedger(),SettlementLedger()
        for q in ("1","2"):
            self.energy(a,qh_id=q)
        for q in ("2","1"):
            self.energy(b,qh_id=q)
        self.assertEqual(a.digest(),b.digest())

    def test_explicit_afrr_units_and_no_second_duration_conversion(self):
        ledger=SettlementLedger()
        common=dict(run_id="ES_SYNTHETIC_MARKET_LEDGER",path="U",qh_id="q",direction="down",execution_day="2025-01-01")
        capacity=ledger.settle_capacity(**common,capacity_mw=20,price_eur_per_mw_period=2)
        activation=ledger.settle_activation(**common,activation_mwh=2,price_eur_per_mwh=-30)
        self.assertEqual((capacity.quantity_unit,capacity.price_unit,capacity.cash_eur),("MW","EUR/MW/period",40))
        self.assertEqual((activation.quantity_unit,activation.price_unit,activation.cash_eur),("MWh","EUR/MWh",-60))
        with self.assertRaises(ValueError):
            ledger.settle_afrr(**common,kind="capacity",quantity=20,unit_price_eur=2,hours=.25)

    def test_becoming_fixed_does_not_repeat_or_alter_existing_settlement(self):
        ledger=SettlementLedger()
        entry=self.energy(ledger,fixed=False)
        replay=ledger.record(replace(entry,fixed=True))
        self.assertFalse(replay.fixed)
        self.assertEqual(len(ledger.entries),1)
        self.assertEqual(ledger.total_cash_eur,125)

    def test_wrong_unit_label_is_rejected(self):
        entry=self.energy(SettlementLedger())
        with self.assertRaises(ValueError):
            SettlementLedger().record(replace(entry,quantity_unit="MWh"))

if __name__ == "__main__":
    unittest.main()
