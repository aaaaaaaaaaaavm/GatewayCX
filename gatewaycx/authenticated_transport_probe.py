"""S019 authenticated GX-A1 process-boundary and replay-rejection probe."""

from __future__ import annotations

import argparse
import json
import secrets
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from .authenticated_rpc import AUTH_RPC_VERSION, AuthenticatedAdapterRPCClient
from .io import write_json


PROFILE_PATH = Path("profiles/bearers/reference-rf.json")
CLIENT_ID = "gatewaycx-s019-probe"
UNIT_BYTES = 32_768


def _start_server(
    port_file: Path, database: Path, secret_file: Path
) -> tuple[subprocess.Popen[str], int]:
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "gatewaycx.authenticated_rpc",
            "--port-file",
            str(port_file),
            "--profile",
            str(PROFILE_PATH),
            "--database",
            str(database),
            "--client-id",
            CLIENT_ID,
            "--secret-file",
            str(secret_file),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    for _ in range(100):
        if port_file.exists():
            host, port = port_file.read_text(encoding="utf-8").strip().rsplit(":", 1)
            if host != "127.0.0.1":
                process.terminate()
                raise RuntimeError("authenticated GX-A1 server escaped loopback")
            return process, int(port)
        if process.poll() is not None:
            _, error = process.communicate()
            raise RuntimeError(f"authenticated GX-A1 server exited before readiness: {error}")
        time.sleep(0.01)
    process.terminate()
    raise TimeoutError("authenticated GX-A1 server did not publish its port")


def _shutdown(
    client: AuthenticatedAdapterRPCClient, process: subprocess.Popen[str]
) -> None:
    client.call("shutdown")
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.terminate()
        process.wait(timeout=5)
    process.communicate()


def _send_unverified(port: int, request: dict[str, Any]) -> dict[str, Any]:
    """Return an error envelope whose MAC is intentionally expected not to verify."""

    with socket.create_connection(("127.0.0.1", port), timeout=5) as connection:
        connection.sendall(
            (json.dumps(request, sort_keys=True, separators=(",", ":")) + "\n").encode(
                "utf-8"
            )
        )
        response = bytearray()
        while b"\n" not in response:
            chunk = connection.recv(65_536)
            if not chunk:
                break
            response.extend(chunk)
    parsed = json.loads(response.split(b"\n", 1)[0].decode("utf-8"))
    if not isinstance(parsed, dict):
        raise AssertionError("authentication error response must be an object")
    return parsed


def build_authenticated_transport_probe() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="gatewaycx-s019-") as temp_dir:
        root = Path(temp_dir)
        port_file = root / "gx-a1-auth.port"
        database = root / "traffic.sqlite3"
        secret_file = root / "client.secret"
        secret = secrets.token_bytes(32)
        wrong_secret = secrets.token_bytes(32)
        secret_file.write_text(secret.hex() + "\n", encoding="ascii")
        secret_file.chmod(0o600)

        first_process, first_port = _start_server(port_file, database, secret_file)
        client = AuthenticatedAdapterRPCClient(
            "127.0.0.1", first_port, CLIENT_ID, secret
        )
        capabilities = client.call("capabilities")
        submitted = client.call(
            "submit",
            traffic_unit_id="gx-s019-unit-001",
            payload_bytes=UNIT_BYTES,
            traffic_class="GX-T2-network-control",
            deferred=True,
        )

        replay_request = client.build_request("snapshot")
        first_snapshot = client.send(replay_request)
        replay_same_process = client.send(replay_request)

        tampered_request = client.build_request("snapshot")
        tampered_request["operation"] = "clear_faults"
        tampered = _send_unverified(first_port, tampered_request)

        wrong_client = AuthenticatedAdapterRPCClient(
            "127.0.0.1", first_port, CLIENT_ID, wrong_secret, sequence=client._sequence
        )
        wrong_key_request = wrong_client.build_request("snapshot")
        wrong_key = _send_unverified(first_port, wrong_key_request)
        last_accepted_sequence = replay_request["sequence"]
        _shutdown(client, first_process)
        restart_sequence = client.sequence

        second_process, second_port = _start_server(port_file, database, secret_file)
        restarted_client = AuthenticatedAdapterRPCClient(
            "127.0.0.1", second_port, CLIENT_ID, secret, sequence=restart_sequence
        )
        replay_after_restart = restarted_client.send(replay_request)
        post_restart = restarted_client.call("snapshot")
        _shutdown(restarted_client, second_process)

        with sqlite3.connect(database) as connection:
            database_columns = {
                row[1]
                for row in connection.execute("PRAGMA table_info(rpc_client_sequences)")
            }

    checks = {
        "valid_request_is_authenticated": capabilities["ok"] is True,
        "response_is_authenticated": isinstance(capabilities.get("mac"), str),
        "traffic_submission_is_accepted": submitted["result"]["status"]
        == "accepted_pending",
        "same_process_replay_is_rejected": replay_same_process.get("error")
        == "replayed_sequence",
        "tampered_request_is_rejected": tampered.get("error")
        == "authentication_failed",
        "wrong_key_is_rejected": wrong_key.get("error") == "authentication_failed",
        "restart_replay_is_rejected": replay_after_restart.get("error")
        == "replayed_sequence",
        "next_sequence_after_restart_is_accepted": post_restart["ok"] is True,
        "traffic_ledger_survives_restart": post_restart["result"]["accepted_bytes"]
        == UNIT_BYTES,
        "replay_store_contains_no_secret_column": "secret" not in database_columns,
        "payload_content_crossed_rpc": False,
    }
    return {
        "study_id": "S019",
        "title": "Authenticated GX-A1 binding and durable replay rejection",
        "evidence_class": "TEST",
        "inputs": {
            "rpc_version": AUTH_RPC_VERSION,
            "authentication": "HMAC-SHA256 with 256-bit pre-shared key",
            "ordering": "strictly increasing per-client integer sequence",
            "replay_state": "SQLite last accepted sequence",
            "transport": "TCP loopback JSONL",
            "payload_content_supplied": False,
        },
        "observations": {
            "accepted_sequence_before_restart": last_accepted_sequence,
            "same_process_replay_error": replay_same_process["error"],
            "restart_replay_error": replay_after_restart["error"],
            "tampered_request_error": tampered["error"],
            "wrong_key_error": wrong_key["error"],
            "accepted_bytes_after_restart": post_restart["result"]["accepted_bytes"],
            "replay_store_columns": sorted(database_columns),
        },
        "checks": checks,
        "interpretation_boundary": [
            "HMAC possession authenticates this reference client and detects request or response modification; it does not provide confidentiality.",
            "The pre-shared-key mechanism is not a PKI, key-rotation system, hardware root of trust or flight security design.",
            "A valid sequence is consumed before operation dispatch. A lost response therefore requires operation-specific reconciliation; only traffic submission has an explicit idempotency key here.",
            "Replay state survives a clean process restart, not abrupt power loss or corrupted storage.",
            "Both endpoints remain GatewayCX reference software on one host; no supplier adapter, terminal or physical link participates.",
            "Secrets, message authentication codes, process identifiers and ephemeral ports are excluded from the committed result.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("results/S019_authenticated_transport.json")
    )
    args = parser.parse_args(argv)
    write_json(args.output, build_authenticated_transport_probe())
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
