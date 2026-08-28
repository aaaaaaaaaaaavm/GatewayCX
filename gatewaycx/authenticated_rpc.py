"""Authenticated local GX-A1 binding with durable replay rejection.

This is a bounded reference mechanism, not a production security protocol.  It
uses a pre-shared HMAC key to authenticate requests and responses, and stores
only the last accepted sequence number for each client in SQLite.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import re
import socket
import sqlite3
from pathlib import Path
from typing import Any

from .adapter_rpc import AdapterRPCServer, MAX_REQUEST_BYTES
from .bearer_adapter import ProfileBackedAdapter
from .traffic_store import SQLiteTrafficStore


AUTH_RPC_VERSION = "GX-A1-JSONL-HMAC/0.1"
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def _canonical_bytes(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _mac(secret: bytes, value: dict[str, Any]) -> str:
    unsigned = {key: item for key, item in value.items() if key != "mac"}
    return hmac.new(secret, _canonical_bytes(unsigned), hashlib.sha256).hexdigest()


def _valid_identifier(value: Any) -> bool:
    return isinstance(value, str) and _IDENTIFIER.fullmatch(value) is not None


def read_secret(path: Path) -> bytes:
    """Read a 256-bit pre-shared key represented by exactly 64 hexadecimal digits."""

    encoded = path.read_text(encoding="ascii").strip()
    if len(encoded) != 64:
        raise ValueError("secret file must contain exactly 64 hexadecimal digits")
    try:
        secret = bytes.fromhex(encoded)
    except ValueError as exc:
        raise ValueError("secret file must contain exactly 64 hexadecimal digits") from exc
    if len(secret) != 32:
        raise ValueError("secret must decode to 32 bytes")
    return secret


class DurableReplayStore:
    """Persist the highest authenticated sequence accepted for each client."""

    def __init__(self, path: Path) -> None:
        self._connection = sqlite3.connect(path, isolation_level=None)
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA synchronous=FULL")
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS rpc_client_sequences (
                client_id TEXT PRIMARY KEY,
                last_sequence INTEGER NOT NULL CHECK (last_sequence > 0)
            )
            """
        )

    def accept(self, client_id: str, sequence: int) -> bool:
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            row = self._connection.execute(
                "SELECT last_sequence FROM rpc_client_sequences WHERE client_id = ?",
                (client_id,),
            ).fetchone()
            if row is not None and sequence <= int(row[0]):
                self._connection.execute("COMMIT")
                return False
            self._connection.execute(
                """
                INSERT INTO rpc_client_sequences (client_id, last_sequence)
                VALUES (?, ?)
                ON CONFLICT(client_id) DO UPDATE SET last_sequence = excluded.last_sequence
                """,
                (client_id, sequence),
            )
            self._connection.execute("COMMIT")
            return True
        except BaseException:
            self._connection.execute("ROLLBACK")
            raise

    def last_sequence(self, client_id: str) -> int | None:
        row = self._connection.execute(
            "SELECT last_sequence FROM rpc_client_sequences WHERE client_id = ?",
            (client_id,),
        ).fetchone()
        return None if row is None else int(row[0])

    def close(self) -> None:
        self._connection.close()


class AuthenticatedAdapterRPCServer:
    """One-request-per-connection HMAC-authenticated loopback binding."""

    def __init__(
        self,
        adapter: ProfileBackedAdapter,
        replay_store: DurableReplayStore,
        client_secrets: dict[str, bytes],
        host: str = "127.0.0.1",
        port: int = 0,
        port_file: Path | None = None,
    ) -> None:
        if host != "127.0.0.1":
            raise ValueError("authenticated reference binding is restricted to 127.0.0.1")
        if not client_secrets or any(not _valid_identifier(key) for key in client_secrets):
            raise ValueError("at least one valid client identifier is required")
        if any(len(secret) != 32 for secret in client_secrets.values()):
            raise ValueError("every HMAC secret must be 32 bytes")
        self.adapter = adapter
        self._dispatcher = AdapterRPCServer(adapter)
        self.replay_store = replay_store
        self.client_secrets = dict(client_secrets)
        self.host = host
        self.port = port
        self.port_file = port_file
        self._stop = False

    def _unsigned_error(
        self, error: str, request_id: str | None = None, sequence: int | None = None
    ) -> dict[str, Any]:
        return {
            "rpc_version": AUTH_RPC_VERSION,
            "request_id": request_id,
            "sequence": sequence,
            "ok": False,
            "error": error,
        }

    def dispatch(self, request: Any) -> dict[str, Any]:
        if not isinstance(request, dict):
            return self._unsigned_error("request_must_be_object")
        client_id = request.get("client_id")
        request_id = request.get("request_id")
        sequence = request.get("sequence")
        if request.get("rpc_version") != AUTH_RPC_VERSION:
            return self._unsigned_error("unsupported_rpc_version", request_id, sequence)
        if not _valid_identifier(client_id) or client_id not in self.client_secrets:
            return self._unsigned_error("unknown_client", request_id, sequence)
        if not _valid_identifier(request_id):
            return self._unsigned_error("invalid_request_id", None, sequence)
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence <= 0:
            return self._unsigned_error("invalid_sequence", request_id, None)
        supplied_mac = request.get("mac")
        if not isinstance(supplied_mac, str) or not hmac.compare_digest(
            supplied_mac, _mac(self.client_secrets[client_id], request)
        ):
            return self._unsigned_error("authentication_failed", request_id, sequence)
        if not self.replay_store.accept(client_id, sequence):
            response = self._unsigned_error("replayed_sequence", request_id, sequence)
        else:
            base_request = {
                "request_id": request_id,
                "operation": request.get("operation"),
                "arguments": request.get("arguments", {}),
            }
            base_response = self._dispatcher.dispatch(base_request)
            response = {
                **base_response,
                "rpc_version": AUTH_RPC_VERSION,
                "sequence": sequence,
            }
            if request.get("operation") == "shutdown" and response["ok"]:
                self._stop = True
        response["mac"] = _mac(self.client_secrets[client_id], response)
        return response

    def serve(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind((self.host, self.port))
            bound_host, bound_port = listener.getsockname()
            if self.port_file is not None:
                self.port_file.parent.mkdir(parents=True, exist_ok=True)
                self.port_file.write_text(f"{bound_host}:{bound_port}\n", encoding="utf-8")
            listener.listen(8)
            while not self._stop:
                connection, _ = listener.accept()
                with connection:
                    received = bytearray()
                    while len(received) <= MAX_REQUEST_BYTES:
                        chunk = connection.recv(65_536)
                        if not chunk:
                            break
                        received.extend(chunk)
                        if b"\n" in chunk:
                            break
                    if len(received) > MAX_REQUEST_BYTES:
                        response = self._unsigned_error("request_too_large")
                    else:
                        try:
                            request = json.loads(received.split(b"\n", 1)[0].decode("utf-8"))
                            response = self.dispatch(request)
                        except (UnicodeDecodeError, json.JSONDecodeError):
                            response = self._unsigned_error("invalid_json")
                    connection.sendall(_canonical_bytes(response) + b"\n")
        if self.port_file is not None:
            self.port_file.unlink(missing_ok=True)
        self.replay_store.close()
        self.adapter.close()


class AuthenticatedAdapterRPCClient:
    def __init__(
        self, host: str, port: int, client_id: str, secret: bytes, sequence: int = 0
    ) -> None:
        if not _valid_identifier(client_id) or len(secret) != 32 or sequence < 0:
            raise ValueError("invalid authenticated client configuration")
        self.host = host
        self.port = port
        self.client_id = client_id
        self.secret = secret
        self._sequence = sequence

    @property
    def sequence(self) -> int:
        return self._sequence

    def build_request(self, operation: str, **arguments: Any) -> dict[str, Any]:
        self._sequence += 1
        request = {
            "rpc_version": AUTH_RPC_VERSION,
            "client_id": self.client_id,
            "sequence": self._sequence,
            "request_id": f"{self.client_id}-{self._sequence:08d}",
            "operation": operation,
            "arguments": arguments,
        }
        request["mac"] = _mac(self.secret, request)
        return request

    def send(self, request: dict[str, Any]) -> dict[str, Any]:
        with socket.create_connection((self.host, self.port), timeout=5) as connection:
            connection.sendall(_canonical_bytes(request) + b"\n")
            response_bytes = bytearray()
            while b"\n" not in response_bytes:
                chunk = connection.recv(65_536)
                if not chunk:
                    break
                response_bytes.extend(chunk)
        response = json.loads(response_bytes.split(b"\n", 1)[0].decode("utf-8"))
        if response.get("request_id") != request.get("request_id"):
            raise RuntimeError("authenticated GX-A1 response request_id mismatch")
        supplied_mac = response.get("mac")
        if not isinstance(supplied_mac, str) or not hmac.compare_digest(
            supplied_mac, _mac(self.secret, response)
        ):
            raise RuntimeError("authenticated GX-A1 response MAC verification failed")
        return response

    def call(self, operation: str, **arguments: Any) -> dict[str, Any]:
        return self.send(self.build_request(operation, **arguments))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--port-file", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--secret-file", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.host != "127.0.0.1":
        parser.error("the authenticated reference binding is restricted to 127.0.0.1")
    try:
        secret = read_secret(args.secret_file)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    adapter = ProfileBackedAdapter.from_file(
        args.profile, store=SQLiteTrafficStore(args.database)
    )
    AuthenticatedAdapterRPCServer(
        adapter,
        DurableReplayStore(args.database),
        {args.client_id: secret},
        host=args.host,
        port=args.port,
        port_file=args.port_file,
    ).serve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
