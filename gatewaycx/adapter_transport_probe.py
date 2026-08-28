"""S018 process-boundary probe for the GX-A1 JSON-lines Unix-socket binding."""

from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from .adapter_rpc import AdapterRPCClient, RPC_VERSION
from .io import write_json


PROFILE_PATH = Path("profiles/bearers/reference-rf.json")
UNIT_BYTES = 65_536


def _start_server(port_file: Path, database: Path) -> tuple[subprocess.Popen[str], int]:
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "gatewaycx.adapter_rpc",
            "--port-file",
            str(port_file),
            "--profile",
            str(PROFILE_PATH),
            "--database",
            str(database),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    for _ in range(100):
        if port_file.exists():
            address = port_file.read_text(encoding="utf-8").strip()
            host, port = address.rsplit(":", 1)
            if host != "127.0.0.1":
                process.terminate()
                raise RuntimeError("GX-A1 reference server escaped loopback")
            return process, int(port)
        if process.poll() is not None:
            _, error = process.communicate()
            raise RuntimeError(f"GX-A1 RPC server exited before readiness: {error}")
        time.sleep(0.01)
    process.terminate()
    raise TimeoutError("GX-A1 RPC server did not publish its port")


def _invalid_json(port: int) -> dict[str, Any]:
    with socket.create_connection(("127.0.0.1", port), timeout=5) as connection:
        connection.sendall(b"this is not json\n")
        response = bytearray()
        while b"\n" not in response:
            response.extend(connection.recv(65_536))
    parsed = json.loads(response.split(b"\n", 1)[0].decode("utf-8"))
    if not isinstance(parsed, dict):
        raise AssertionError("invalid-JSON response must be an object")
    return parsed


def _shutdown(client: AdapterRPCClient, process: subprocess.Popen[str]) -> None:
    client.call("shutdown")
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.terminate()
        process.wait(timeout=5)
    process.communicate()


def build_transport_probe() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="gatewaycx-s018-") as temp_dir:
        root = Path(temp_dir)
        port_file = root / "gx-a1.port"
        database = root / "traffic.sqlite3"
        first_process, first_port = _start_server(port_file, database)
        first_pid = first_process.pid
        first_client = AdapterRPCClient("127.0.0.1", first_port)
        capabilities = first_client.call("capabilities")
        initial = first_client.call("snapshot")
        submitted = first_client.call(
            "submit",
            traffic_unit_id="gx-s018-unit-001",
            payload_bytes=UNIT_BYTES,
            traffic_class="GX-T3-operational",
            deferred=True,
        )
        first_client.call("set_contact", available=True, offset_s=1.0)
        acquiring = first_client.call("acquire", offset_s=1.0)
        ready_at_s = acquiring["result"]["ready_at_s"]
        ready = first_client.call("advance", offset_s=ready_at_s)
        transmitted = first_client.call("transmit", duration_s=0.1)
        malformed = _invalid_json(first_port)
        alive_after_malformed = first_process.poll() is None
        _shutdown(first_client, first_process)

        second_process, second_port = _start_server(port_file, database)
        second_pid = second_process.pid
        second_client = AdapterRPCClient("127.0.0.1", second_port)
        restarted = second_client.call("snapshot")
        _shutdown(second_client, second_process)

    operation_result = capabilities["result"]
    initial_result = initial["result"]
    submitted_result = submitted["result"]
    ready_result = ready["result"]
    transmitted_result = transmitted["result"]
    restarted_result = restarted["result"]
    checks = {
        "separate_client_and_server_processes": first_pid != second_pid,
        "rpc_version_is_stable": capabilities["rpc_version"] == RPC_VERSION,
        "capabilities_cross_process_boundary": operation_result["operation"] == "capabilities",
        "initial_link_is_unavailable": initial_result["link_state"] == "unavailable",
        "submission_is_accepted_pending": submitted_result["status"] == "accepted_pending",
        "acquisition_reaches_ready": ready_result["link_state"] == "ready",
        "profile_capacity_drains_unit": transmitted_result["transmitted_bytes"] == UNIT_BYTES,
        "malformed_json_is_rejected": (
            malformed["ok"] is False and malformed["error"] == "invalid_json"
        ),
        "server_survives_malformed_request": alive_after_malformed,
        "binding_is_loopback_only": first_port > 0 and second_port > 0,
        "restart_resets_link_state": restarted_result["link_state"] == "unavailable",
        "restart_preserves_traffic_ledger": (
            restarted_result["accepted_bytes"] == UNIT_BYTES
            and restarted_result["transmitted_bytes"] == UNIT_BYTES
            and restarted_result["queue_bytes"] == 0
        ),
        "payload_content_crossed_rpc": False,
    }
    return {
        "study_id": "S018",
        "title": "GX-A1 local process-boundary transport",
        "evidence_class": "TEST",
        "inputs": {
            "profile_path": PROFILE_PATH.as_posix(),
            "traffic_unit_bytes": UNIT_BYTES,
            "transport": "TCP loopback",
            "framing": "one JSON line per connection",
            "bind_address": "127.0.0.1",
            "payload_content_supplied": False,
        },
        "first_server": {
            "persistence_scope": operation_result["reference_persistence_scope"],
            "submit_status": submitted_result["status"],
            "ready_at_s": ready_at_s,
            "transmitted_bytes": transmitted_result["transmitted_bytes"],
            "malformed_request_error": malformed["error"],
        },
        "second_server": {
            "link_state": restarted_result["link_state"],
            "accepted_bytes": restarted_result["accepted_bytes"],
            "transmitted_bytes": restarted_result["transmitted_bytes"],
            "queue_bytes": restarted_result["queue_bytes"],
        },
        "checks": checks,
        "interpretation_boundary": [
            "The binding is loopback TCP JSONL, not a deployed network protocol or supplier standard.",
            "Loopback limits reachability to the host but does not provide application authentication, authorisation, confidentiality or message integrity.",
            "Both server launches still use the GatewayCX reference adapter; no independent supplier implementation participates.",
            "The request carries traffic metadata only. It does not carry payload content, packets or BPv7 bundles.",
            "The server controls no terminal, modem, pointing system or physical link.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/S018_adapter_transport.json"))
    args = parser.parse_args(argv)
    write_json(args.output, build_transport_probe())
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
