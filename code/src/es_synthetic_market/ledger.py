"""Small, idempotent settlement ledger for the synthetic rolling model.

The ledger deliberately has no file, API, or market-rule adapter.  It only
records already frozen synthetic positions.  A ledger key contains the run,
path, settlement type, contract/QH shard and direction, so re-running a
window cannot charge the same delivery twice.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json
from math import isfinite
from typing import Iterable


@dataclass(frozen=True)
class LedgerEntry:
    run_id: str
    path: str
    settlement_type: str
    object_id: str
    direction: str
    quantity: float
    unit_price_eur: float
    hours: float
    cash_eur: float
    execution_day: str
    fixed: bool = False
    quantity_unit: str = ""
    price_unit: str = ""

    @property
    def key(self) -> tuple[str, str, str, str, str]:
        return (self.run_id, self.path, self.settlement_type, self.object_id, self.direction)

    def __post_init__(self) -> None:
        if not all(isinstance(v, str) and v for v in (self.run_id, self.path, self.settlement_type, self.object_id, self.direction, self.execution_day)):
            raise ValueError("ledger identifiers must be non-empty strings")
        for name in ("quantity", "unit_price_eur", "hours", "cash_eur"):
            value = float(getattr(self, name))
            if not isfinite(value):
                raise ValueError(f"{name} must be finite")
            object.__setattr__(self, name, value)
        if self.quantity < 0 or self.hours < 0:
            raise ValueError("ledger quantity and hours must be non-negative")
        if self.settlement_type not in {"DA_energy", "IDA_energy", "aFRR_capacity", "aFRR_activation"}:
            raise ValueError("unsupported cash settlement type")
        if self.settlement_type in {"DA_energy", "IDA_energy"}:
            if self.direction not in {"sell", "buy"}:
                raise ValueError("energy ledger direction must be sell or buy")
            expected = (1.0 if self.direction == "sell" else -1.0) * self.quantity * self.unit_price_eur * self.hours
            units = ("MW", "EUR/MWh")
        elif self.settlement_type == "aFRR_capacity":
            if self.direction not in {"up", "down"}:
                raise ValueError("aFRR ledger direction must be up or down")
            if self.hours != 1:
                raise ValueError("capacity standard price is EUR/MW/period; multiplier must be 1")
            expected = self.quantity * self.unit_price_eur
            units = ("MW", "EUR/MW/period")
        else:
            if self.direction not in {"up", "down"}:
                raise ValueError("aFRR ledger direction must be up or down")
            if self.hours != 1:
                raise ValueError("canonical activation quantity is MWh; multiplier must be 1")
            expected = self.quantity * self.unit_price_eur
            units = ("MWh", "EUR/MWh")
        if self.quantity_unit not in {"", units[0]} or self.price_unit not in {"", units[1]}:
            raise ValueError("ledger unit mismatch")
        object.__setattr__(self, "quantity_unit", units[0])
        object.__setattr__(self, "price_unit", units[1])
        if abs(float(self.cash_eur) - expected) > 1e-7:
            raise ValueError("ledger cash must be derived from typed quantity/price fields")


class SettlementLedger:
    """Idempotent, market-separated cash ledger.

    ``record`` is intentionally strict: the same key may be replayed only
    with the identical entry.  A different value under an existing key is a
    duplicate/conflicting settlement and raises instead of silently adding
    cash.
    """

    def __init__(self) -> None:
        self._entries: dict[tuple[str, str, str, str, str], LedgerEntry] = {}
        self._total = 0.0
        self._compensation = 0.0
        self._revision = 0
        self._parent = None
        self._parent_revision = None

    def _check_parent(self):
        if self._parent is not None and self._parent._revision != self._parent_revision:
            raise ValueError("stale ledger transaction")

    def fork(self):
        """O(1) isolated append transaction over immutable existing entries."""
        self._check_parent()
        if self._parent is not None:
            raise ValueError("nested ledger transactions are not supported")
        child=SettlementLedger()
        child._parent=self;child._parent_revision=self._revision;child._total=self._total
        child._compensation=self._compensation
        return child

    def clone(self):
        """Detached container; frozen scalar-only LedgerEntry objects can be shared."""
        self._check_parent()
        result=SettlementLedger()
        result._entries={e.key:e for e in self.entries}
        result._total=self._total;result._compensation=self._compensation;result._revision=len(result._entries)
        return result

    def commit(self, child):
        """Commit only a fresh direct transaction, after the window passed audits."""
        if child._parent is not self:
            raise ValueError("ledger transaction belongs to another parent")
        child._check_parent()
        # Every child entry was validated by record; no parent mutation occurred.
        if any(k in self._entries for k in child._entries):
            raise ValueError("conflicting ledger transaction")
        self._entries.update(child._entries)
        self._total=child._total;self._compensation=child._compensation;self._revision+=1

    def delta_snapshot(self):
        self._check_parent()
        return tuple(asdict(e) | {"key":e.key} for e in self._entries.values())

    def record(self, entry: LedgerEntry) -> LedgerEntry:
        self._check_parent()
        old = self._entries.get(entry.key)
        if old is None and self._parent is not None:
            old = self._parent._entries.get(entry.key)
        if old is not None:
            if replace(old, fixed=entry.fixed) != entry:
                raise ValueError(f"conflicting duplicate ledger key: {entry.key}")
            # Keep first-settlement provenance when a new order becomes fixed.
            return old
        self._entries[entry.key] = entry
        # Preserve accurate float summation when large positive/negative cash
        # nearly cancels; do not trade numerical stability for an O(1) total.
        value=entry.cash_eur;combined=self._total+value
        if abs(self._total)>=abs(value):
            self._compensation += (self._total-combined)+value
        else:
            self._compensation += (value-combined)+self._total
        self._total=combined
        self._revision += 1
        return entry

    def settle_energy(
        self,
        *,
        run_id: str,
        path: str,
        market: str,
        contract_id: str,
        direction: str,
        quantity_mw: float,
        price_eur_per_mwh: float,
        qh_id: str,
        hours: float,
        execution_day: str,
        fixed: bool = False,
    ) -> LedgerEntry:
        if market not in {"DA", "IDA"}:
            raise ValueError("energy market must be DA or IDA")
        if direction not in {"sell", "buy"}:
            raise ValueError("energy direction must be sell or buy")
        # A contract delivered over multiple execution days is explicitly
        # sharded by QH.  The shard is part of object_id and cannot be charged
        # again when a later rolling window is replayed.
        # JSON is a structural encoding: delimiter characters in either ID
        # cannot create an ``a|b/c`` versus ``a/b|c`` collision.
        object_id = json.dumps([str(contract_id), str(qh_id)], ensure_ascii=False, separators=(",", ":"))
        sign = 1.0 if direction == "sell" else -1.0
        entry = LedgerEntry(
            run_id, path, f"{market}_energy", object_id, direction,
            float(quantity_mw), float(price_eur_per_mwh), float(hours),
            sign * float(quantity_mw) * float(price_eur_per_mwh) * float(hours),
            execution_day, fixed,
        )
        return self.record(entry)

    def settle_afrr(
        self,
        *,
        run_id: str,
        path: str,
        qh_id: str,
        direction: str,
        kind: str,
        quantity: float,
        unit_price_eur: float,
        hours: float,
        execution_day: str,
        fixed: bool = False,
    ) -> LedgerEntry:
        """Compatibility: capacity MW/per-period price requires hours=1;
        activation MW * hours in [0,.25] is converted once to canonical MWh.
        Prefer the explicit-unit methods below in new callers.
        """
        common=dict(run_id=run_id,path=path,qh_id=qh_id,direction=direction,execution_day=execution_day,fixed=fixed)
        if not isfinite(float(quantity)) or float(quantity) < 0:
            raise ValueError("aFRR quantity must be finite and non-negative")
        if kind == "capacity":
            if hours != 1:
                raise ValueError("capacity is already normalized per period; hours must be 1")
            return self.settle_capacity(**common,capacity_mw=quantity,price_eur_per_mw_period=unit_price_eur)
        if kind == "activation":
            if not isfinite(float(hours)) or not 0 <= hours <= .25:
                raise ValueError("activation hours must be in [0,.25]")
            return self.settle_activation(**common,activation_mwh=float(quantity)*float(hours),price_eur_per_mwh=unit_price_eur)
        raise ValueError("aFRR kind must be capacity or activation")

    def settle_capacity(self, *, run_id: str, path: str, qh_id: str,
                        direction: str, capacity_mw: float,
                        price_eur_per_mw_period: float, execution_day: str,
                        fixed: bool = False) -> LedgerEntry:
        return self.record(LedgerEntry(run_id,path,"aFRR_capacity",qh_id,direction,
            capacity_mw,price_eur_per_mw_period,1,
            float(capacity_mw)*float(price_eur_per_mw_period),execution_day,fixed))

    def settle_activation(self, *, run_id: str, path: str, qh_id: str,
                          direction: str, activation_mwh: float,
                          price_eur_per_mwh: float, execution_day: str,
                          fixed: bool = False) -> LedgerEntry:
        return self.record(LedgerEntry(run_id,path,"aFRR_activation",qh_id,direction,
            activation_mwh,price_eur_per_mwh,1,
            float(activation_mwh)*float(price_eur_per_mwh),execution_day,fixed))

    @property
    def entries(self) -> tuple[LedgerEntry, ...]:
        self._check_parent()
        prefix=() if self._parent is None else self._parent.entries
        return prefix+tuple(self._entries.values())

    @property
    def total_cash_eur(self) -> float:
        self._check_parent()
        return self._total+self._compensation if isfinite(self._total) else self._total

    def cash_by_type(self) -> dict[str, float]:
        out: dict[str, float] = {}
        for entry in self.entries:
            out[entry.settlement_type] = out.get(entry.settlement_type, 0.0) + entry.cash_eur
        return out

    def snapshot(self) -> tuple[dict[str, object], ...]:
        return tuple(asdict(entry) | {"key": entry.key} for entry in self.entries)

    def digest(self) -> str:
        rows = sorted(self.snapshot(), key=lambda row: tuple(row["key"]))
        payload = json.dumps(rows, sort_keys=True, separators=(",", ":"), default=str).encode()
        return sha256(payload).hexdigest()

    def extend(self, entries: Iterable[LedgerEntry]) -> None:
        for entry in entries:
            self.record(entry)


__all__ = ["LedgerEntry", "SettlementLedger"]
