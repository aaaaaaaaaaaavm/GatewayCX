"""Payload-blind traffic-unit ledgers for GatewayCX reference adapters."""

from __future__ import annotations

import sqlite3
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class StoredTrafficUnit:
    traffic_unit_id: str
    payload_bytes: int
    traffic_class: str
    deferred: bool


@dataclass
class _MemoryRow:
    unit: StoredTrafficUnit
    remaining_bytes: int
    transmitted_bytes: int = 0


class TrafficStore(Protocol):
    persistence_scope: str

    def snapshot(self) -> dict[str, int]: ...

    def accept(self, unit: StoredTrafficUnit, capacity_bytes: int) -> dict[str, Any]: ...

    def transmit(self, byte_budget: int) -> list[dict[str, Any]]: ...

    def close(self) -> None: ...


def _same_unit(row: Any, unit: StoredTrafficUnit) -> bool:
    return (
        row["payload_bytes"] == unit.payload_bytes
        and row["traffic_class"] == unit.traffic_class
        and bool(row["deferred"]) == unit.deferred
    )


def _accept_error(unit: StoredTrafficUnit, capacity_bytes: int) -> str | None:
    if not unit.traffic_unit_id:
        return "missing_traffic_unit_id"
    if unit.payload_bytes <= 0:
        return "invalid_payload_bytes"
    if not unit.traffic_class:
        return "missing_traffic_class"
    if capacity_bytes < 0:
        return "invalid_capacity_bytes"
    return None


class InMemoryTrafficStore:
    persistence_scope = "process_memory"

    def __init__(self) -> None:
        self._rows: deque[_MemoryRow] = deque()
        self._by_id: dict[str, _MemoryRow] = {}

    def snapshot(self) -> dict[str, int]:
        return {
            "accepted_bytes": sum(row.unit.payload_bytes for row in self._rows),
            "transmitted_bytes": sum(row.transmitted_bytes for row in self._rows),
            "queue_bytes": sum(row.remaining_bytes for row in self._rows),
            "traffic_units": len(self._rows),
            "pending_units": sum(row.remaining_bytes > 0 for row in self._rows),
        }

    def accept(self, unit: StoredTrafficUnit, capacity_bytes: int) -> dict[str, Any]:
        error = _accept_error(unit, capacity_bytes)
        if error is not None:
            return {"status": "rejected", "reason": error}
        existing = self._by_id.get(unit.traffic_unit_id)
        if existing is not None:
            same = (
                existing.unit.payload_bytes == unit.payload_bytes
                and existing.unit.traffic_class == unit.traffic_class
                and existing.unit.deferred == unit.deferred
            )
            return {"status": "duplicate_known" if same else "duplicate_conflict"}
        if self.snapshot()["queue_bytes"] + unit.payload_bytes > capacity_bytes:
            return {"status": "rejected", "reason": "durable_queue_full"}
        row = _MemoryRow(unit, unit.payload_bytes)
        self._rows.append(row)
        self._by_id[unit.traffic_unit_id] = row
        return {"status": "accepted_pending", "accepted_bytes": unit.payload_bytes}

    def transmit(self, byte_budget: int) -> list[dict[str, Any]]:
        if byte_budget < 0:
            raise ValueError("byte_budget must be non-negative")
        fragments: list[dict[str, Any]] = []
        for row in self._rows:
            if byte_budget == 0:
                break
            if row.remaining_bytes == 0:
                continue
            sent = min(row.remaining_bytes, byte_budget)
            row.remaining_bytes -= sent
            row.transmitted_bytes += sent
            byte_budget -= sent
            fragments.append(
                {
                    "traffic_unit_id": row.unit.traffic_unit_id,
                    "bytes": sent,
                    "complete": row.remaining_bytes == 0,
                }
            )
        return fragments

    def close(self) -> None:
        return None


class SQLiteTrafficStore:
    """SQLite-backed ledger containing traffic metadata and byte counts, never payload content."""

    persistence_scope = "sqlite_file"

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(path, isolation_level=None)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA synchronous=FULL")
        self._connection.execute("PRAGMA foreign_keys=ON")
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS traffic_units (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                traffic_unit_id TEXT NOT NULL UNIQUE,
                payload_bytes INTEGER NOT NULL CHECK (payload_bytes > 0),
                traffic_class TEXT NOT NULL,
                deferred INTEGER NOT NULL CHECK (deferred IN (0, 1)),
                remaining_bytes INTEGER NOT NULL CHECK (remaining_bytes >= 0),
                transmitted_bytes INTEGER NOT NULL CHECK (transmitted_bytes >= 0),
                CHECK (remaining_bytes + transmitted_bytes = payload_bytes)
            )
            """
        )

    def snapshot(self) -> dict[str, int]:
        row = self._connection.execute(
            """
            SELECT
                COALESCE(SUM(payload_bytes), 0) AS accepted_bytes,
                COALESCE(SUM(transmitted_bytes), 0) AS transmitted_bytes,
                COALESCE(SUM(remaining_bytes), 0) AS queue_bytes,
                COUNT(*) AS traffic_units,
                COALESCE(SUM(CASE WHEN remaining_bytes > 0 THEN 1 ELSE 0 END), 0)
                    AS pending_units
            FROM traffic_units
            """
        ).fetchone()
        return {key: int(row[key]) for key in row.keys()}

    def schema_columns(self) -> list[str]:
        return [
            str(row[1])
            for row in self._connection.execute("PRAGMA table_info(traffic_units)").fetchall()
        ]

    def database_settings(self) -> dict[str, str]:
        journal_mode = str(self._connection.execute("PRAGMA journal_mode").fetchone()[0]).upper()
        synchronous_value = int(self._connection.execute("PRAGMA synchronous").fetchone()[0])
        synchronous_names = {0: "OFF", 1: "NORMAL", 2: "FULL", 3: "EXTRA"}
        return {
            "journal_mode": journal_mode,
            "synchronous_mode": synchronous_names.get(
                synchronous_value, f"UNKNOWN_{synchronous_value}"
            ),
        }

    def accept(self, unit: StoredTrafficUnit, capacity_bytes: int) -> dict[str, Any]:
        error = _accept_error(unit, capacity_bytes)
        if error is not None:
            return {"status": "rejected", "reason": error}
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            existing = self._connection.execute(
                """
                SELECT payload_bytes, traffic_class, deferred
                FROM traffic_units WHERE traffic_unit_id = ?
                """,
                (unit.traffic_unit_id,),
            ).fetchone()
            if existing is not None:
                status = "duplicate_known" if _same_unit(existing, unit) else "duplicate_conflict"
                self._connection.execute("COMMIT")
                return {"status": status}
            queued = int(
                self._connection.execute(
                    "SELECT COALESCE(SUM(remaining_bytes), 0) FROM traffic_units"
                ).fetchone()[0]
            )
            if queued + unit.payload_bytes > capacity_bytes:
                self._connection.execute("COMMIT")
                return {"status": "rejected", "reason": "durable_queue_full"}
            self._connection.execute(
                """
                INSERT INTO traffic_units (
                    traffic_unit_id, payload_bytes, traffic_class, deferred,
                    remaining_bytes, transmitted_bytes
                ) VALUES (?, ?, ?, ?, ?, 0)
                """,
                (
                    unit.traffic_unit_id,
                    unit.payload_bytes,
                    unit.traffic_class,
                    int(unit.deferred),
                    unit.payload_bytes,
                ),
            )
            self._connection.execute("COMMIT")
            return {"status": "accepted_pending", "accepted_bytes": unit.payload_bytes}
        except BaseException:
            self._connection.execute("ROLLBACK")
            raise

    def transmit(self, byte_budget: int) -> list[dict[str, Any]]:
        if byte_budget < 0:
            raise ValueError("byte_budget must be non-negative")
        fragments: list[dict[str, Any]] = []
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            rows = self._connection.execute(
                """
                SELECT sequence, traffic_unit_id, remaining_bytes
                FROM traffic_units WHERE remaining_bytes > 0 ORDER BY sequence
                """
            ).fetchall()
            for row in rows:
                if byte_budget == 0:
                    break
                sent = min(int(row["remaining_bytes"]), byte_budget)
                remaining = int(row["remaining_bytes"]) - sent
                self._connection.execute(
                    """
                    UPDATE traffic_units
                    SET remaining_bytes = ?, transmitted_bytes = transmitted_bytes + ?
                    WHERE sequence = ?
                    """,
                    (remaining, sent, row["sequence"]),
                )
                byte_budget -= sent
                fragments.append(
                    {
                        "traffic_unit_id": row["traffic_unit_id"],
                        "bytes": sent,
                        "complete": remaining == 0,
                    }
                )
            self._connection.execute("COMMIT")
        except BaseException:
            self._connection.execute("ROLLBACK")
            raise
        return fragments

    def close(self) -> None:
        self._connection.close()
