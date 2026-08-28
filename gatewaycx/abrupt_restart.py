"""S020 abrupt-process termination probe for the SQLite traffic ledger."""

from __future__ import annotations

import argparse
import json
import os
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from .io import write_json
from .traffic_store import SQLiteTrafficStore, StoredTrafficUnit


STABLE_UNIT = StoredTrafficUnit("gx-s020-stable", 65_536, "GX-T3-operational", True)
PRECOMMIT_UNIT = StoredTrafficUnit("gx-s020-uncommitted", 32_768, "GX-T3-operational", True)
POSTCOMMIT_UNIT = StoredTrafficUnit("gx-s020-committed", 16_384, "GX-T3-operational", True)
RECOVERY_UNIT = StoredTrafficUnit("gx-s020-recovery", 8_192, "GX-T2-network-control", True)
CAPACITY_BYTES = 1_000_000


def _insert(connection: sqlite3.Connection, unit: StoredTrafficUnit) -> None:
    connection.execute(
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


def _fault_worker(database: Path, ready_file: Path, phase: str) -> None:
    connection = sqlite3.connect(database, isolation_level=None)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=FULL")
    connection.execute("BEGIN IMMEDIATE")
    _insert(connection, PRECOMMIT_UNIT if phase == "before_commit" else POSTCOMMIT_UNIT)
    if phase == "after_commit":
        connection.execute("COMMIT")
    ready_file.write_text(json.dumps({"phase": phase, "pid": os.getpid()}), encoding="utf-8")
    while True:
        signal.pause()


def _kill_at_phase(database: Path, root: Path, phase: str) -> int:
    ready_file = root / f"{phase}.ready"
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "gatewaycx.abrupt_restart",
            "--worker",
            phase,
            "--database",
            str(database),
            "--ready-file",
            str(ready_file),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    for _ in range(500):
        if ready_file.exists():
            break
        if process.poll() is not None:
            _, error = process.communicate()
            raise RuntimeError(f"S020 worker exited before fault point: {error}")
        time.sleep(0.01)
    else:
        process.kill()
        process.wait(timeout=5)
        raise TimeoutError(f"S020 worker did not reach {phase}")
    worker_pid = process.pid
    process.kill()
    return_code = process.wait(timeout=5)
    process.communicate()
    if return_code >= 0:
        raise AssertionError("S020 worker was not terminated by a signal")
    return worker_pid


def _ids(database: Path) -> list[str]:
    with sqlite3.connect(database) as connection:
        return [
            str(row[0])
            for row in connection.execute(
                "SELECT traffic_unit_id FROM traffic_units ORDER BY sequence"
            )
        ]


def _integrity(database: Path) -> str:
    with sqlite3.connect(database) as connection:
        return str(connection.execute("PRAGMA integrity_check").fetchone()[0])


def build_abrupt_restart_study() -> dict[str, Any]:
    if os.name != "posix":
        raise RuntimeError("S020 requires POSIX signal termination")
    with tempfile.TemporaryDirectory(prefix="gatewaycx-s020-") as temp_dir:
        root = Path(temp_dir)
        database = root / "traffic-ledger.sqlite3"
        seed = SQLiteTrafficStore(database)
        stable_decision = seed.accept(STABLE_UNIT, CAPACITY_BYTES)
        stable_snapshot = seed.snapshot()
        seed.close()

        before_pid = _kill_at_phase(database, root, "before_commit")
        after_precommit_kill = SQLiteTrafficStore(database)
        precommit_snapshot = after_precommit_kill.snapshot()
        after_precommit_kill.close()
        precommit_ids = _ids(database)
        precommit_integrity = _integrity(database)

        after_pid = _kill_at_phase(database, root, "after_commit")
        after_postcommit_kill = SQLiteTrafficStore(database)
        postcommit_snapshot = after_postcommit_kill.snapshot()
        recovery_decision = after_postcommit_kill.accept(RECOVERY_UNIT, CAPACITY_BYTES)
        final_snapshot = after_postcommit_kill.snapshot()
        after_postcommit_kill.close()
        final_ids = _ids(database)
        postcommit_integrity = _integrity(database)

    checks = {
        "fault_workers_are_distinct_processes": before_pid != after_pid,
        "stable_unit_was_committed": stable_decision["status"] == "accepted_pending",
        "precommit_kill_preserves_stable_state": precommit_snapshot == stable_snapshot,
        "precommit_unit_is_rolled_back": PRECOMMIT_UNIT.traffic_unit_id not in precommit_ids,
        "integrity_after_precommit_kill": precommit_integrity == "ok",
        "postcommit_unit_survives_kill": POSTCOMMIT_UNIT.traffic_unit_id in final_ids,
        "postcommit_bytes_survive_kill": postcommit_snapshot["accepted_bytes"]
        == STABLE_UNIT.payload_bytes + POSTCOMMIT_UNIT.payload_bytes,
        "integrity_after_postcommit_kill": postcommit_integrity == "ok",
        "store_accepts_new_work_after_recovery": recovery_decision["status"]
        == "accepted_pending",
        "final_byte_ledger_is_conserved": final_snapshot["accepted_bytes"]
        == final_snapshot["transmitted_bytes"] + final_snapshot["queue_bytes"],
        "payload_content_was_supplied": False,
    }
    return {
        "study_id": "S020",
        "title": "Abrupt process termination at SQLite transaction boundaries",
        "evidence_class": "TEST",
        "inputs": {
            "termination": "SIGKILL via subprocess.kill",
            "journal_mode": "WAL",
            "synchronous_mode": "FULL",
            "fault_points": ["after insert before commit", "after commit before close"],
            "payload_content_supplied": False,
        },
        "observations": {
            "stable_snapshot": stable_snapshot,
            "after_precommit_kill": precommit_snapshot,
            "after_postcommit_kill": postcommit_snapshot,
            "final_snapshot": final_snapshot,
            "precommit_recovered_ids": precommit_ids,
            "final_recovered_ids": final_ids,
            "precommit_integrity_check": precommit_integrity,
            "postcommit_integrity_check": postcommit_integrity,
        },
        "checks": checks,
        "interpretation_boundary": [
            "The probe sends SIGKILL to a separate writer while a transaction is open and again after commit but before a clean close.",
            "The fault points are coordinated software boundaries, not arbitrary instruction, kernel, filesystem, device-cache or electrical power-loss points.",
            "A passing SQLite integrity check establishes recovery for these temporary local files only; it does not qualify storage media or a flight computer.",
            "The test stores traffic identifiers, classes and byte counts but no payload content.",
            "WAL and synchronous FULL are active configuration observations, not a guarantee against every storage failure mode.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=("before_commit", "after_commit"))
    parser.add_argument("--database", type=Path)
    parser.add_argument("--ready-file", type=Path)
    parser.add_argument("--output", type=Path, default=Path("results/S020_abrupt_restart.json"))
    args = parser.parse_args(argv)
    if args.worker:
        if args.database is None or args.ready_file is None:
            parser.error("--worker requires --database and --ready-file")
        _fault_worker(args.database, args.ready_file, args.worker)
        return 0
    write_json(args.output, build_abrupt_restart_study())
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
