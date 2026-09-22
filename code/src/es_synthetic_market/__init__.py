"""Synthetic-only Spain DA/IDA/aFRR joint MILP core.

This package deliberately accepts only explicitly synthetic inputs.  It is a
development core for the approved design; it does not read historical files,
call APIs, or represent a production settlement adapter.
"""

from .core import (
    ContractInput,
    FixedCommitment,
    QHInput,
    SyntheticMarketInput,
    SyntheticMarketResult,
    solve_joint,
    solve_joint_both_orders,
)
from .ledger import LedgerEntry, SettlementLedger
from .rolling import FrozenReserve, RollingEngine, RollingOrder, RollingRunResult, RollingWindowResult, solve_rolling

__all__ = [
    "ContractInput",
    "FixedCommitment",
    "QHInput",
    "SyntheticMarketInput",
    "SyntheticMarketResult",
    "solve_joint",
    "solve_joint_both_orders",
    "LedgerEntry",
    "SettlementLedger",
    "FrozenReserve",
    "RollingEngine",
    "RollingOrder",
    "RollingRunResult",
    "RollingWindowResult",
    "solve_rolling",
]
