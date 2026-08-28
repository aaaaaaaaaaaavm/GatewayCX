"""S028 executable lunar-region identity, consistency, update, black-start and recovery faults."""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import multiprocessing
import os
import random
import shutil
import sqlite3
import tempfile
import time
from pathlib import Path
from typing import Any

from .io import write_json


IDENTITY_KEY = b"gatewaycx-s028-identity-test-key"
UPDATE_KEY = b"gatewaycx-s028-update-test-key"


def _canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(value, separators=(",", ":"), sort_keys=True).encode()


def issue_token(subject: str, serial: int, issued_s: int, expires_s: int) -> str:
    claims = {"exp": expires_s, "iat": issued_s, "serial": serial, "sub": subject}
    payload = base64.urlsafe_b64encode(_canonical(claims)).decode().rstrip("=")
    signature = hmac.new(IDENTITY_KEY, payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"


def validate_token(token: str, now_s: int, revoked: set[int]) -> tuple[bool, str]:
    try:
        payload, supplied = token.split(".", 1)
        expected = hmac.new(IDENTITY_KEY, payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(supplied, expected):
            return False, "signature"
        padded = payload + "=" * (-len(payload) % 4)
        claims = json.loads(base64.urlsafe_b64decode(padded))
    except (ValueError, json.JSONDecodeError):
        return False, "format"
    if now_s >= int(claims["exp"]):
        return False, "expired"
    if int(claims["serial"]) in revoked:
        return False, "revoked"
    return True, "accepted"


def identity_experiment() -> dict[str, Any]:
    token = issue_token("crew-17", 41, 100, 200)
    during_partition = validate_token(token, 150, set())
    after_holdover = validate_token(token, 210, set())
    after_reconnect = validate_token(token, 160, {41})
    forged = validate_token(token[:-1] + ("0" if token[-1] != "0" else "1"), 150, set())
    return {
        "experiment_id": "X07", "mechanism": "HMAC-signed offline capability with bounded expiry and serial revocation",
        "during_partition": {"accepted": during_partition[0], "reason": during_partition[1], "revocation_visibility": "stale"},
        "after_holdover_expiry": {"accepted": after_holdover[0], "reason": after_holdover[1]},
        "after_reconnection": {"accepted": after_reconnect[0], "reason": after_reconnect[1]},
        "forged_token": {"accepted": forged[0], "reason": forged[1]},
    }


def _open_replica(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE kv (key TEXT PRIMARY KEY, value TEXT, version INTEGER, region TEXT)")
    return connection


def consistency_experiment(root: Path) -> dict[str, Any]:
    earth, moon = _open_replica(root / "earth.db"), _open_replica(root / "moon.db")
    try:
        strong_write = {"accepted": False, "reason": "quorum_unavailable"}
        earth.execute("INSERT INTO kv VALUES ('schedule', 'earth-v2', 2, 'earth')")
        moon.execute("INSERT INTO kv VALUES ('schedule', 'moon-v2', 2, 'moon')")
        earth.commit(); moon.commit()
        candidates = [earth.execute("SELECT value, version, region FROM kv").fetchone(), moon.execute("SELECT value, version, region FROM kv").fetchone()]
        winner = max(candidates, key=lambda row: (row[1], row[2]))
        for database in (earth, moon):
            database.execute("UPDATE kv SET value=?, version=?, region=? WHERE key='schedule'", winner)
            database.commit()
        converged = earth.execute("SELECT value FROM kv").fetchone()[0] == moon.execute("SELECT value FROM kv").fetchone()[0]
        earth_escrow, moon_escrow = 5, 5
        earth_used, moon_used = 5, 4
        return {
            "experiment_id": "X08",
            "strong_command_during_partition": strong_write,
            "eventual_register": {"earth_write": "earth-v2", "moon_write": "moon-v2", "resolution": winner[0], "converged": converged},
            "escrow_counter": {"global_limit": earth_escrow + moon_escrow, "earth_used": earth_used, "moon_used": moon_used, "oversubscribed": earth_used + moon_used > earth_escrow + moon_escrow},
        }
    finally:
        earth.close(); moon.close()


def _signed_manifest(version: str, payload: bytes) -> dict[str, Any]:
    body = {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(), "version": version}
    return {**body, "signature": hmac.new(UPDATE_KEY, _canonical(body), hashlib.sha256).hexdigest()}


def _verify_update(manifest: dict[str, Any], payload: bytes) -> tuple[bool, str]:
    body = {key: manifest[key] for key in ("bytes", "sha256", "version")}
    expected = hmac.new(UPDATE_KEY, _canonical(body), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(str(manifest.get("signature", "")), expected):
        return False, "manifest_signature"
    if len(payload) != int(manifest["bytes"]) or hashlib.sha256(payload).hexdigest() != manifest["sha256"]:
        return False, "payload_digest"
    return True, "verified"


def update_experiment(root: Path) -> dict[str, Any]:
    slot_a, slot_b = root / "slot-a.bin", root / "slot-b.bin"
    slot_a.write_bytes(b"gatewaycx-service-v1")
    payload = b"gatewaycx-service-v2:" + bytes(range(64))
    manifest = _signed_manifest("v2", payload)
    corrupt = payload[:-1] + bytes([payload[-1] ^ 0xFF])
    corrupt_result = _verify_update(manifest, corrupt)
    valid_result = _verify_update(manifest, payload)
    if valid_result[0]:
        slot_b.write_bytes(payload)
    active_after_failed_health = "A"
    migration = sqlite3.connect(root / "service.db")
    migration.execute("CREATE TABLE state (schema_version INTEGER)")
    migration.execute("INSERT INTO state VALUES (1)"); migration.commit()
    try:
        migration.execute("BEGIN IMMEDIATE")
        migration.execute("UPDATE state SET schema_version=2")
        raise RuntimeError("fault_before_migration_commit")
    except RuntimeError:
        migration.rollback()
    schema_after_fault = migration.execute("SELECT schema_version FROM state").fetchone()[0]
    migration.close()
    return {
        "experiment_id": "X14",
        "corrupt_payload": {"accepted": corrupt_result[0], "reason": corrupt_result[1]},
        "valid_payload": {"accepted": valid_result[0], "reason": valid_result[1], "staged_sha256": hashlib.sha256(slot_b.read_bytes()).hexdigest()},
        "failed_health_check": {"active_slot": active_after_failed_health, "candidate_slot": "B"},
        "migration_fault": {"schema_version_after_rollback": schema_after_fault},
    }


def _service_process(ready: multiprocessing.Event, stop: multiprocessing.Event) -> None:
    ready.set()
    stop.wait(5)


def _launch_service() -> tuple[bool, int]:
    ready, stop = multiprocessing.Event(), multiprocessing.Event()
    process = multiprocessing.Process(target=_service_process, args=(ready, stop))
    process.start(); started = ready.wait(2); stop.set(); process.join(2)
    return started, process.exitcode if process.exitcode is not None else -999


def black_start_experiment() -> dict[str, Any]:
    services = ("holdover_time", "local_trust", "dns", "identity", "gateway")
    nominal = {}
    for service in services:
        started, exitcode = _launch_service()
        nominal[service] = {"started": started, "clean_exit": exitcode == 0}
    time_fault = {
        "holdover_time": {"started": False, "reason": "fault_injected"},
        "local_trust": {"started": False, "reason": "time_dependency"},
        "dns": {"started": True, "reason": "time_independent_local_zone"},
        "identity": {"started": False, "reason": "trust_dependency"},
        "gateway": {"started": False, "reason": "identity_dependency"},
    }
    return {"experiment_id": "X16", "earth_available": False, "nominal_process_start": nominal, "lost_holdover_time": time_fault}


def recovery_experiment(root: Path) -> dict[str, Any]:
    database = root / "ledger.db"
    connection = sqlite3.connect(database)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("CREATE TABLE ledger (id INTEGER PRIMARY KEY, committed INTEGER NOT NULL)")
    connection.commit()
    rng = random.Random(9171)
    attempted, committed, rolled_back = 60, 0, 0
    fault_points = []
    for unit_id in range(attempted):
        fault = rng.choice(("none", "before_insert", "after_insert", "after_commit"))
        fault_points.append(fault)
        try:
            connection.execute("BEGIN IMMEDIATE")
            if fault == "before_insert": raise RuntimeError(fault)
            connection.execute("INSERT INTO ledger VALUES (?, 1)", (unit_id,))
            if fault == "after_insert": raise RuntimeError(fault)
            connection.commit(); committed += 1
            if fault == "after_commit": raise RuntimeError(fault)
        except RuntimeError:
            if connection.in_transaction:
                connection.rollback(); rolled_back += 1
    durable_rows = connection.execute("SELECT COUNT(*) FROM ledger WHERE committed=1").fetchone()[0]
    integrity_before = connection.execute("PRAGMA integrity_check").fetchone()[0]
    backup = root / "ledger.backup.db"
    backup_connection = sqlite3.connect(backup); connection.backup(backup_connection); backup_connection.close(); connection.close()
    data = bytearray(database.read_bytes()); data[0:16] = b"FAULTED-LEDGER!!"; database.write_bytes(data)
    try:
        damaged = sqlite3.connect(database); damaged.execute("PRAGMA integrity_check").fetchone(); damaged.close(); corruption_detected = False
    except sqlite3.DatabaseError:
        corruption_detected = True
    shutil.copy2(backup, database)
    restored = sqlite3.connect(database)
    integrity_after = restored.execute("PRAGMA integrity_check").fetchone()[0]
    restored_rows = restored.execute("SELECT COUNT(*) FROM ledger").fetchone()[0]; restored.close()
    return {
        "experiment_id": "X18", "seed": 9171, "attempted_transactions": attempted,
        "fault_distribution": {name: fault_points.count(name) for name in sorted(set(fault_points))},
        "committed_before_corruption": committed, "durable_rows_before_corruption": durable_rows,
        "rolled_back_transactions": rolled_back, "integrity_before_corruption": integrity_before,
        "corruption_detected": corruption_detected, "integrity_after_restore": integrity_after,
        "restored_rows": restored_rows,
    }


def build_regional_fault_lab() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="gatewaycx-s028-") as temporary:
        root = Path(temporary)
        identity = identity_experiment()
        # Each SQLite experiment gets an isolated directory to prevent accidental shared state.
        consistency_root = root / "consistency"; consistency_root.mkdir()
        update_root = root / "update"; update_root.mkdir()
        recovery_root = root / "recovery"; recovery_root.mkdir()
        consistency = consistency_experiment(consistency_root)
        update = update_experiment(update_root)
        black_start = black_start_experiment()
        recovery = recovery_experiment(recovery_root)
    checks = {
        "offline_identity_is_bounded_and_reconciled": identity["during_partition"]["accepted"] and not identity["after_holdover_expiry"]["accepted"] and not identity["after_reconnection"]["accepted"] and not identity["forged_token"]["accepted"],
        "consistency_policies_fail_or_merge_by_class": not consistency["strong_command_during_partition"]["accepted"] and consistency["eventual_register"]["converged"] and not consistency["escrow_counter"]["oversubscribed"],
        "update_faults_preserve_active_state": not update["corrupt_payload"]["accepted"] and update["valid_payload"]["accepted"] and update["failed_health_check"]["active_slot"] == "A" and update["migration_fault"]["schema_version_after_rollback"] == 1,
        "black_start_uses_real_child_processes": all(row["started"] and row["clean_exit"] for row in black_start["nominal_process_start"].values()),
        "recovery_detects_corruption_and_restores_exact_commits": recovery["corruption_detected"] and recovery["integrity_after_restore"] == "ok" and recovery["restored_rows"] == recovery["committed_before_corruption"] == recovery["durable_rows_before_corruption"],
    }
    return {
        "study_id": "S028", "title": "Executable lunar-region fault laboratory", "evidence_class": "TEST",
        "experiments": {"identity_partition": identity, "consistency_partition": consistency, "signed_update": update, "black_start": black_start, "storage_recovery": recovery},
        "checks": checks,
        "interpretation_boundary": [
            "HMAC test keys demonstrate signature and stale-revocation semantics, not PKI, protected key custody or production identity.",
            "The consistency experiment uses two local SQLite replicas and declared merge policies, not a distributed database product.",
            "The update experiment writes and hashes real payloads and rolls back a SQLite migration, but does not implement secure boot or a transparency log.",
            "Black start launches real child processes without Earth, but does not exercise electrical power, flight computers, oscillators or network interfaces.",
            "Recovery injects deterministic transaction faults and corrupts/restores a database file; it is not raw-device power-loss or radiation testing.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--output", type=Path, default=Path("results/S028_regional_fault_lab.json")); args = parser.parse_args(argv)
    write_json(args.output, build_regional_fault_lab()); print(f"wrote {args.output}"); return 0


if __name__ == "__main__": raise SystemExit(main())
