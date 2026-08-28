#!/usr/bin/env python3
"""Standalone GX-A1 RF adapter example with no GatewayCX runtime imports.

The file intentionally uses only the Python standard library.  It provides a
second implementation of the authenticated JSONL binding for interoperability
tests; it is not supplier code, a modem driver or a production daemon.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import socket
import sqlite3
from pathlib import Path
from typing import Any


RPC_VERSION = "GX-A1-JSONL-HMAC/0.1"
API_VERSION = "GX-A1/0.1"
MAX_REQUEST_BYTES = 1_000_000


def canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign(secret: bytes, value: dict[str, Any]) -> str:
    unsigned = {key: item for key, item in value.items() if key != "mac"}
    return hmac.new(secret, canonical(unsigned), hashlib.sha256).hexdigest()


class StandaloneRFAdapter:
    def __init__(self, profile_path: Path, database: Path) -> None:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        required = {"schema_version", "bearer_id", "media", "performance", "queue"}
        if not isinstance(profile, dict) or not required.issubset(profile):
            raise ValueError("profile lacks standalone adapter fields")
        if profile["media"] != "rf":
            raise ValueError("standalone example accepts an RF profile only")
        self.profile = profile
        self.database = sqlite3.connect(database, isolation_level=None)
        self.database.row_factory = sqlite3.Row
        self.database.execute("PRAGMA journal_mode=WAL")
        self.database.execute("PRAGMA synchronous=FULL")
        self.database.execute(
            """
            CREATE TABLE IF NOT EXISTS standalone_units (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                traffic_unit_id TEXT NOT NULL UNIQUE,
                payload_bytes INTEGER NOT NULL,
                traffic_class TEXT NOT NULL,
                deferred INTEGER NOT NULL,
                remaining_bytes INTEGER NOT NULL,
                transmitted_bytes INTEGER NOT NULL,
                CHECK (payload_bytes > 0),
                CHECK (remaining_bytes + transmitted_bytes = payload_bytes)
            )
            """
        )
        self.database.execute(
            """
            CREATE TABLE IF NOT EXISTS standalone_clients (
                client_id TEXT PRIMARY KEY,
                last_sequence INTEGER NOT NULL
            )
            """
        )
        self.offset_s = 0.0
        self.contact = False
        self.link_state = "unavailable"
        self.ready_at_s: float | None = None
        self.link_epoch = 0

    def envelope(self, operation: str, status: str, **fields: Any) -> dict[str, Any]:
        return {
            "api_version": API_VERSION,
            "bearer_id": self.profile["bearer_id"],
            "operation": operation,
            "status": status,
            "observed_offset_s": round(self.offset_s, 6),
            **fields,
        }

    def ledger(self) -> dict[str, int]:
        row = self.database.execute(
            """
            SELECT COALESCE(SUM(payload_bytes), 0),
                   COALESCE(SUM(transmitted_bytes), 0),
                   COALESCE(SUM(remaining_bytes), 0), COUNT(*)
            FROM standalone_units
            """
        ).fetchone()
        return {
            "accepted_bytes": int(row[0]),
            "transmitted_bytes": int(row[1]),
            "queue_bytes": int(row[2]),
            "traffic_units": int(row[3]),
        }

    def accept_sequence(self, client_id: str, sequence: int) -> bool:
        self.database.execute("BEGIN IMMEDIATE")
        try:
            row = self.database.execute(
                "SELECT last_sequence FROM standalone_clients WHERE client_id = ?",
                (client_id,),
            ).fetchone()
            if row is not None and sequence <= int(row[0]):
                self.database.execute("COMMIT")
                return False
            self.database.execute(
                """
                INSERT INTO standalone_clients (client_id, last_sequence) VALUES (?, ?)
                ON CONFLICT(client_id) DO UPDATE SET last_sequence = excluded.last_sequence
                """,
                (client_id, sequence),
            )
            self.database.execute("COMMIT")
            return True
        except BaseException:
            self.database.execute("ROLLBACK")
            raise

    def dispatch(self, operation: Any, arguments: Any) -> dict[str, Any]:
        if not isinstance(arguments, dict):
            raise ValueError("arguments_must_be_object")
        if operation == "capabilities":
            return self.envelope(
                operation,
                "ok",
                profile=self.profile,
                operations=[
                    "capabilities",
                    "snapshot",
                    "submit",
                    "set_contact",
                    "acquire",
                    "advance",
                    "transmit",
                ],
                reference_persistence_scope="standalone_sqlite_file",
                implementation_id="gatewaycx-standalone-rf-example/0.1",
            )
        if operation == "snapshot":
            ledger = self.ledger()
            performance = self.profile["performance"]
            return self.envelope(
                operation,
                "ok",
                link_state=self.link_state,
                tx_rate_mbps=(
                    performance["forward_capacity_mbps"]
                    if self.link_state == "ready"
                    else 0.0
                ),
                rx_rate_mbps=(
                    performance["return_capacity_mbps"]
                    if self.link_state == "ready"
                    else 0.0
                ),
                queue_bytes=ledger["queue_bytes"],
                accepted_bytes=ledger["accepted_bytes"],
                transmitted_bytes=ledger["transmitted_bytes"],
                next_contact_utc=None,
                fault_codes=[],
                link_epoch=self.link_epoch,
                reference_persistence_scope="standalone_sqlite_file",
            )
        if operation == "submit":
            identity = str(arguments["traffic_unit_id"])
            size = int(arguments["payload_bytes"])
            traffic_class = str(arguments["traffic_class"])
            deferred = bool(arguments.get("deferred", True))
            maximum = int(self.profile["performance"]["maximum_traffic_unit_bytes"])
            if not identity or size <= 0 or not traffic_class:
                return self.envelope(operation, "rejected", reason="invalid_metadata")
            if size > maximum:
                return self.envelope(operation, "rejected", reason="traffic_unit_too_large")
            if self.link_state != "ready" and not (
                deferred and self.profile["queue"]["deferred_delivery"]
            ):
                return self.envelope(operation, "rejected", reason="link_unavailable")
            self.database.execute("BEGIN IMMEDIATE")
            try:
                existing = self.database.execute(
                    """
                    SELECT payload_bytes, traffic_class, deferred FROM standalone_units
                    WHERE traffic_unit_id = ?
                    """,
                    (identity,),
                ).fetchone()
                if existing is not None:
                    same = (
                        int(existing[0]) == size
                        and str(existing[1]) == traffic_class
                        and bool(existing[2]) == deferred
                    )
                    self.database.execute("COMMIT")
                    return self.envelope(
                        operation, "duplicate_known" if same else "duplicate_conflict"
                    )
                queued = self.ledger()["queue_bytes"]
                if queued + size > int(self.profile["queue"]["durable_bytes"]):
                    self.database.execute("COMMIT")
                    return self.envelope(operation, "rejected", reason="durable_queue_full")
                self.database.execute(
                    """
                    INSERT INTO standalone_units (
                        traffic_unit_id, payload_bytes, traffic_class, deferred,
                        remaining_bytes, transmitted_bytes
                    ) VALUES (?, ?, ?, ?, ?, 0)
                    """,
                    (identity, size, traffic_class, int(deferred), size),
                )
                self.database.execute("COMMIT")
            except BaseException:
                self.database.execute("ROLLBACK")
                raise
            return self.envelope(
                operation,
                "accepted_pending",
                traffic_unit_id=identity,
                accepted_bytes=size,
                queue_bytes=self.ledger()["queue_bytes"],
            )
        if operation == "set_contact":
            self.offset_s = max(self.offset_s, float(arguments["offset_s"]))
            self.contact = bool(arguments["available"])
            if not self.contact:
                self.link_state = "unavailable"
                self.ready_at_s = None
            return self.envelope(
                operation, "ok", contact_available=self.contact, link_state=self.link_state
            )
        if operation == "acquire":
            self.offset_s = max(self.offset_s, float(arguments["offset_s"]))
            if not self.contact:
                return self.envelope(operation, "rejected", reason="contact_unavailable")
            self.link_state = "acquiring"
            self.ready_at_s = self.offset_s + float(
                self.profile["performance"]["acquisition_max_s"]
            )
            return self.envelope(
                operation, "accepted", link_state=self.link_state, ready_at_s=self.ready_at_s
            )
        if operation == "advance":
            self.offset_s = max(self.offset_s, float(arguments["offset_s"]))
            transitioned = bool(
                self.link_state == "acquiring"
                and self.ready_at_s is not None
                and self.offset_s >= self.ready_at_s
                and self.contact
            )
            if transitioned:
                self.link_state = "ready"
                self.ready_at_s = None
                self.link_epoch += 1
            return self.envelope(
                operation, "ok", link_state=self.link_state, transitioned=transitioned
            )
        if operation == "transmit":
            duration = float(arguments["duration_s"])
            if duration <= 0:
                raise ValueError("invalid_duration")
            if self.link_state != "ready":
                self.offset_s += duration
                return self.envelope(
                    operation, "blocked", reason="link_not_ready", transmitted_bytes=0
                )
            budget = int(
                float(self.profile["performance"]["forward_capacity_mbps"])
                * 1_000_000
                * duration
                / 8
            )
            transmitted = 0
            self.database.execute("BEGIN IMMEDIATE")
            try:
                rows = self.database.execute(
                    """
                    SELECT sequence, remaining_bytes FROM standalone_units
                    WHERE remaining_bytes > 0 ORDER BY sequence
                    """
                ).fetchall()
                for row in rows:
                    sent = min(int(row[1]), budget - transmitted)
                    if sent <= 0:
                        break
                    self.database.execute(
                        """
                        UPDATE standalone_units
                        SET remaining_bytes = remaining_bytes - ?,
                            transmitted_bytes = transmitted_bytes + ?
                        WHERE sequence = ?
                        """,
                        (sent, sent, row[0]),
                    )
                    transmitted += sent
                self.database.execute("COMMIT")
            except BaseException:
                self.database.execute("ROLLBACK")
                raise
            self.offset_s += duration
            return self.envelope(
                operation,
                "ok",
                transmitted_bytes=transmitted,
                queue_bytes=self.ledger()["queue_bytes"],
                fragments=[],
            )
        raise ValueError("unknown_operation")

    def close(self) -> None:
        self.database.close()


class Server:
    def __init__(
        self,
        adapter: StandaloneRFAdapter,
        client_id: str,
        secret: bytes,
        port_file: Path,
    ) -> None:
        self.adapter = adapter
        self.client_id = client_id
        self.secret = secret
        self.port_file = port_file
        self.stop = False

    def response(self, request: Any) -> dict[str, Any]:
        if not isinstance(request, dict):
            return {"rpc_version": RPC_VERSION, "ok": False, "error": "invalid_request"}
        request_id = request.get("request_id")
        sequence = request.get("sequence")
        base = {
            "rpc_version": RPC_VERSION,
            "request_id": request_id,
            "sequence": sequence,
            "ok": False,
        }
        if (
            request.get("rpc_version") != RPC_VERSION
            or request.get("client_id") != self.client_id
            or isinstance(sequence, bool)
            or not isinstance(sequence, int)
            or sequence <= 0
        ):
            return {**base, "error": "invalid_envelope"}
        supplied = request.get("mac")
        if not isinstance(supplied, str) or not hmac.compare_digest(
            supplied, sign(self.secret, request)
        ):
            return {**base, "error": "authentication_failed"}
        if not self.adapter.accept_sequence(self.client_id, sequence):
            result = {**base, "error": "replayed_sequence"}
            result["mac"] = sign(self.secret, result)
            return result
        operation = request.get("operation")
        if operation == "shutdown":
            self.stop = True
            payload = {"operation": "shutdown", "status": "accepted"}
        else:
            try:
                payload = self.adapter.dispatch(operation, request.get("arguments", {}))
            except (KeyError, TypeError, ValueError) as exc:
                result = {**base, "error": "invalid_operation", "detail": str(exc)}
                result["mac"] = sign(self.secret, result)
                return result
        result = {**base, "ok": True, "result": payload}
        result["mac"] = sign(self.secret, result)
        return result

    def serve(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind(("127.0.0.1", 0))
            self.port_file.write_text(
                f"127.0.0.1:{listener.getsockname()[1]}\n", encoding="utf-8"
            )
            listener.listen(8)
            while not self.stop:
                connection, _ = listener.accept()
                with connection:
                    received = bytearray()
                    while len(received) <= MAX_REQUEST_BYTES and b"\n" not in received:
                        chunk = connection.recv(65_536)
                        if not chunk:
                            break
                        received.extend(chunk)
                    try:
                        request = json.loads(received.split(b"\n", 1)[0].decode("utf-8"))
                        result = self.response(request)
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        result = {
                            "rpc_version": RPC_VERSION,
                            "request_id": None,
                            "sequence": None,
                            "ok": False,
                            "error": "invalid_json",
                        }
                    connection.sendall(canonical(result) + b"\n")
        self.port_file.unlink(missing_ok=True)
        self.adapter.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--port-file", type=Path, required=True)
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--secret-file", type=Path, required=True)
    args = parser.parse_args()
    encoded = args.secret_file.read_text(encoding="ascii").strip()
    if len(encoded) != 64:
        parser.error("secret file must contain 64 hexadecimal digits")
    secret = bytes.fromhex(encoded)
    Server(
        StandaloneRFAdapter(args.profile, args.database),
        args.client_id,
        secret,
        args.port_file,
    ).serve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
