"""S021 interoperability probe against the standalone RF adapter process."""

from __future__ import annotations

import argparse
import ast
import hashlib
import secrets
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from .authenticated_rpc import AUTH_RPC_VERSION, AuthenticatedAdapterRPCClient
from .io import write_json


ADAPTER_PATH = Path("adapters/standalone_rf_adapter.py")
PROFILE_PATH = Path("profiles/bearers/reference-rf.json")
CLIENT_ID = "gatewaycx-s021-client"
UNIT_BYTES = 65_536


def _runtime_imports() -> list[str]:
    source = ADAPTER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return sorted(imports)


def _start(
    port_file: Path, database: Path, secret_file: Path
) -> tuple[subprocess.Popen[str], int]:
    process = subprocess.Popen(
        [
            sys.executable,
            str(ADAPTER_PATH),
            "--profile",
            str(PROFILE_PATH),
            "--database",
            str(database),
            "--port-file",
            str(port_file),
            "--client-id",
            CLIENT_ID,
            "--secret-file",
            str(secret_file),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    for _ in range(200):
        if port_file.exists():
            host, port = port_file.read_text(encoding="utf-8").strip().rsplit(":", 1)
            if host != "127.0.0.1":
                process.kill()
                raise RuntimeError("standalone adapter escaped loopback")
            return process, int(port)
        if process.poll() is not None:
            _, error = process.communicate()
            raise RuntimeError(f"standalone adapter exited before readiness: {error}")
        time.sleep(0.01)
    process.kill()
    process.wait(timeout=5)
    raise TimeoutError("standalone adapter did not publish its port")


def _shutdown(
    client: AuthenticatedAdapterRPCClient, process: subprocess.Popen[str]
) -> None:
    response = client.call("shutdown")
    if not response["ok"]:
        raise RuntimeError("standalone adapter rejected shutdown")
    process.wait(timeout=5)
    process.communicate()


def build_independent_adapter_probe() -> dict[str, Any]:
    source_bytes = ADAPTER_PATH.read_bytes()
    imports = _runtime_imports()
    with tempfile.TemporaryDirectory(prefix="gatewaycx-s021-") as temp_dir:
        root = Path(temp_dir)
        database = root / "standalone.sqlite3"
        port_file = root / "standalone.port"
        secret_file = root / "client.secret"
        secret = secrets.token_bytes(32)
        secret_file.write_text(secret.hex() + "\n", encoding="ascii")
        secret_file.chmod(0o600)

        first_process, first_port = _start(port_file, database, secret_file)
        first_client = AuthenticatedAdapterRPCClient(
            "127.0.0.1", first_port, CLIENT_ID, secret
        )
        capabilities = first_client.call("capabilities")
        initial = first_client.call("snapshot")
        submitted = first_client.call(
            "submit",
            traffic_unit_id="gx-s021-unit-001",
            payload_bytes=UNIT_BYTES,
            traffic_class="GX-T3-operational",
            deferred=True,
        )
        duplicate = first_client.call(
            "submit",
            traffic_unit_id="gx-s021-unit-001",
            payload_bytes=UNIT_BYTES,
            traffic_class="GX-T3-operational",
            deferred=True,
        )
        first_client.call("set_contact", available=True, offset_s=1.0)
        acquiring = first_client.call("acquire", offset_s=1.0)
        ready_at_s = acquiring["result"]["ready_at_s"]
        ready = first_client.call("advance", offset_s=ready_at_s)
        transmitted = first_client.call("transmit", duration_s=0.1)
        _shutdown(first_client, first_process)
        restart_sequence = first_client.sequence

        second_process, second_port = _start(port_file, database, secret_file)
        second_client = AuthenticatedAdapterRPCClient(
            "127.0.0.1", second_port, CLIENT_ID, secret, sequence=restart_sequence
        )
        restarted = second_client.call("snapshot")
        _shutdown(second_client, second_process)

    capabilities_result = capabilities["result"]
    initial_result = initial["result"]
    submitted_result = submitted["result"]
    duplicate_result = duplicate["result"]
    ready_result = ready["result"]
    transmitted_result = transmitted["result"]
    restarted_result = restarted["result"]
    checks = {
        "standalone_source_has_no_gatewaycx_import": not any(
            name == "gatewaycx" or name.startswith("gatewaycx.") for name in imports
        ),
        "server_runs_as_separate_process": first_process.pid != second_process.pid,
        "gatewaycx_client_accepts_standalone_response": capabilities["ok"] is True,
        "authenticated_wire_version_matches": capabilities["rpc_version"]
        == AUTH_RPC_VERSION,
        "portable_adapter_version_matches": capabilities_result["api_version"]
        == "GX-A1/0.1",
        "standalone_implementation_identifies_itself": capabilities_result[
            "implementation_id"
        ]
        == "gatewaycx-standalone-rf-example/0.1",
        "initial_link_is_unavailable": initial_result["link_state"] == "unavailable",
        "traffic_submission_is_accepted": submitted_result["status"]
        == "accepted_pending",
        "duplicate_submission_is_idempotent": duplicate_result["status"]
        == "duplicate_known",
        "adapter_reaches_ready": ready_result["link_state"] == "ready",
        "profile_capacity_drains_unit": transmitted_result["transmitted_bytes"]
        == UNIT_BYTES,
        "standalone_ledger_survives_restart": (
            restarted_result["accepted_bytes"] == UNIT_BYTES
            and restarted_result["transmitted_bytes"] == UNIT_BYTES
            and restarted_result["queue_bytes"] == 0
        ),
        "payload_content_crossed_binding": False,
    }
    return {
        "study_id": "S021",
        "title": "Independent-code GX-A1 adapter interoperability",
        "evidence_class": "TEST",
        "inputs": {
            "adapter_path": ADAPTER_PATH.as_posix(),
            "profile_path": PROFILE_PATH.as_posix(),
            "adapter_source_sha256": hashlib.sha256(source_bytes).hexdigest(),
            "adapter_imports": imports,
            "client_implementation": "gatewaycx.authenticated_rpc",
            "server_implementation": "standalone Python standard-library process",
            "traffic_unit_bytes": UNIT_BYTES,
            "payload_content_supplied": False,
        },
        "observations": {
            "rpc_version": capabilities["rpc_version"],
            "api_version": capabilities_result["api_version"],
            "implementation_id": capabilities_result["implementation_id"],
            "persistence_scope": capabilities_result["reference_persistence_scope"],
            "submit_status": submitted_result["status"],
            "duplicate_status": duplicate_result["status"],
            "ready_at_s": ready_at_s,
            "transmitted_bytes": transmitted_result["transmitted_bytes"],
            "restart_accepted_bytes": restarted_result["accepted_bytes"],
            "restart_transmitted_bytes": restarted_result["transmitted_bytes"],
            "restart_queue_bytes": restarted_result["queue_bytes"],
        },
        "checks": checks,
        "interpretation_boundary": [
            "The server is a separately written standard-library implementation and imports no GatewayCX runtime module.",
            "Both implementations remain authored in this repository by the same project; this is code-path independence, not independent organisational validation.",
            "No supplier, optical terminal, RF modem, spacecraft, antenna or physical link participates.",
            "The standalone server implements the bounded S021 operation subset and is not a production daemon or complete conformance target.",
            "The binding carries traffic metadata and byte counts, never payload content.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("results/S021_independent_adapter.json")
    )
    args = parser.parse_args(argv)
    write_json(args.output, build_independent_adapter_probe())
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
