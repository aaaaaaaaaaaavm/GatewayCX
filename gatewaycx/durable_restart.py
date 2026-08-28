"""S017 cross-process restart probe for the payload-blind SQLite traffic ledger."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from .bearer_adapter import ProfileBackedAdapter, TrafficUnit
from .io import write_json
from .traffic_store import SQLiteTrafficStore


PROFILE_PATH = Path("profiles/bearers/reference-rf.json")
UNIT_BYTES = 65_536
UNIT_COUNT = 122
TRANSMIT_WINDOW_S = 0.1


def _unit(index: int, size: int = UNIT_BYTES) -> TrafficUnit:
    return TrafficUnit(
        traffic_unit_id=f"gx-s017-unit-{index:03d}",
        payload_bytes=size,
        traffic_class="GX-T3-operational",
    )


def _ready(adapter: ProfileBackedAdapter, offset_s: float) -> dict[str, Any]:
    adapter.set_contact(True, offset_s)
    acquiring = adapter.acquire(offset_s)
    return adapter.advance(float(acquiring["ready_at_s"]))


def _seed_worker(database: Path) -> dict[str, Any]:
    store = SQLiteTrafficStore(database)
    adapter = ProfileBackedAdapter.from_file(PROFILE_PATH, store=store)
    decisions = [adapter.submit(_unit(index)) for index in range(UNIT_COUNT)]
    before = adapter.snapshot()
    _ready(adapter, 1.0)
    transmitted = adapter.transmit(TRANSMIT_WINDOW_S)
    after = adapter.snapshot()
    adapter.close()
    return {
        "worker_pid": os.getpid(),
        "persistence_scope": before["reference_persistence_scope"],
        "accepted_units": sum(item["status"] == "accepted_pending" for item in decisions),
        "before_transmit": {
            "accepted_bytes": before["accepted_bytes"],
            "transmitted_bytes": before["transmitted_bytes"],
            "queue_bytes": before["queue_bytes"],
        },
        "first_transmit": {
            "transmitted_bytes": transmitted["transmitted_bytes"],
            "queue_bytes": transmitted["queue_bytes"],
        },
        "before_exit": {
            "accepted_bytes": after["accepted_bytes"],
            "transmitted_bytes": after["transmitted_bytes"],
            "queue_bytes": after["queue_bytes"],
        },
    }


def _recover_worker(database: Path) -> dict[str, Any]:
    store = SQLiteTrafficStore(database)
    adapter = ProfileBackedAdapter.from_file(PROFILE_PATH, store=store)
    after_restart = adapter.snapshot()
    duplicate = adapter.submit(_unit(0))
    conflict = adapter.submit(_unit(0, size=UNIT_BYTES - 1))
    ready = _ready(adapter, 1.0)
    windows = 0
    while adapter.queue_bytes:
        adapter.transmit(TRANSMIT_WINDOW_S)
        windows += 1
    final = adapter.snapshot()
    adapter.close()
    return {
        "worker_pid": os.getpid(),
        "after_restart": {
            "accepted_bytes": after_restart["accepted_bytes"],
            "transmitted_bytes": after_restart["transmitted_bytes"],
            "queue_bytes": after_restart["queue_bytes"],
            "persistence_scope": after_restart["reference_persistence_scope"],
        },
        "duplicate_status": duplicate["status"],
        "conflicting_duplicate_status": conflict["status"],
        "reacquired_at_s": ready["observed_offset_s"],
        "recovery_transmit_windows": windows,
        "final": {
            "accepted_bytes": final["accepted_bytes"],
            "transmitted_bytes": final["transmitted_bytes"],
            "queue_bytes": final["queue_bytes"],
        },
    }


def _run_worker(role: str, database: Path, report: Path) -> dict[str, Any]:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "gatewaycx.durable_restart",
            "--worker",
            role,
            "--database",
            str(database),
            "--report",
            str(report),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(report.read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise AssertionError("worker report root must be an object")
    return result


def build_durable_restart_study() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="gatewaycx-s017-") as temp_dir:
        root = Path(temp_dir)
        database = root / "traffic-ledger.sqlite3"
        seed = _run_worker("seed", database, root / "seed.json")
        recover = _run_worker("recover", database, root / "recover.json")
        final_store = SQLiteTrafficStore(database)
        final_reopen = final_store.snapshot()
        columns = final_store.schema_columns()
        database_settings = final_store.database_settings()
        final_store.close()

    seed_pid = seed.pop("worker_pid")
    recover_pid = recover.pop("worker_pid")
    accepted_bytes = UNIT_BYTES * UNIT_COUNT
    checks = {
        "workers_are_distinct_processes": seed_pid != recover_pid,
        "all_units_accepted_before_restart": seed["accepted_units"] == UNIT_COUNT,
        "first_window_uses_rf_profile_capacity": (
            seed["first_transmit"]["transmitted_bytes"] == 1_250_000
        ),
        "restart_preserves_accepted_bytes": (
            recover["after_restart"]["accepted_bytes"]
            == seed["before_exit"]["accepted_bytes"]
            == accepted_bytes
        ),
        "restart_preserves_transmitted_bytes": (
            recover["after_restart"]["transmitted_bytes"]
            == seed["before_exit"]["transmitted_bytes"]
        ),
        "restart_preserves_queue_bytes": (
            recover["after_restart"]["queue_bytes"] == seed["before_exit"]["queue_bytes"]
        ),
        "matching_duplicate_is_idempotent": recover["duplicate_status"] == "duplicate_known",
        "conflicting_duplicate_is_rejected": (
            recover["conflicting_duplicate_status"] == "duplicate_conflict"
        ),
        "final_byte_ledger_conserved": (
            recover["final"]["accepted_bytes"]
            == recover["final"]["transmitted_bytes"] + recover["final"]["queue_bytes"]
        ),
        "queue_drained_after_recovery": recover["final"]["queue_bytes"] == 0,
        "second_reopen_preserves_final_ledger": final_reopen == {
            **recover["final"],
            "traffic_units": UNIT_COUNT,
            "pending_units": 0,
        },
        "schema_contains_no_payload_content_column": {
            "payload", "payload_content", "payload_blob", "payload_plaintext"
        }.isdisjoint(columns),
        "configured_sqlite_modes_are_active": database_settings
        == {"journal_mode": "WAL", "synchronous_mode": "FULL"},
    }
    return {
        "study_id": "S017",
        "title": "Cross-process durable traffic-ledger restart",
        "evidence_class": "TEST",
        "inputs": {
            "profile_path": PROFILE_PATH.as_posix(),
            "traffic_unit_bytes": UNIT_BYTES,
            "traffic_unit_count": UNIT_COUNT,
            "accepted_bytes": accepted_bytes,
            "transmit_window_s": TRANSMIT_WINDOW_S,
            "payload_content_supplied": False,
            "sqlite_synchronous_mode": "FULL",
            "sqlite_journal_mode": "WAL",
        },
        "seed_process": seed,
        "recovery_process": recover,
        "final_reopen": final_reopen,
        "database_settings": database_settings,
        "checks": checks,
        "interpretation_boundary": [
            "The probe starts separate seed and recovery Python processes over one temporary SQLite file.",
            "SQLite persistence is real software behaviour here, but abrupt power loss, storage corruption and hardware durability are not tested.",
            "The ledger stores identifiers, traffic classes and byte counts; it does not store or transmit payload content.",
            "A transmitted byte count is adapter-ledger progress, not BPv7 delivery or remote application completion.",
            "The RF profile capacity remains an illustrative assumed input and no modem or link is connected.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=("seed", "recover"))
    parser.add_argument("--database", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--output", type=Path, default=Path("results/S017_durable_restart.json"))
    args = parser.parse_args(argv)
    if args.worker:
        if args.database is None or args.report is None:
            parser.error("--worker requires --database and --report")
        result = (
            _seed_worker(args.database)
            if args.worker == "seed"
            else _recover_worker(args.database)
        )
        write_json(args.report, result)
        return 0
    write_json(args.output, build_durable_restart_study())
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
