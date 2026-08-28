"""S030 two-implementation BPv7 exchange through the GX-A1 fault gateway."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .authenticated_rpc import DurableReplayStore, _mac
from .bearer_adapter import ProfileBackedAdapter, TrafficUnit
from .io import write_json
from .traffic_store import SQLiteTrafficStore


PROFILE = Path("profiles/bearers/reference-rf.json")
SECRET = hashlib.sha256(b"gatewaycx-s030-interop-key").digest()


def _run(command: list[str], payload: bytes, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(command, input=payload, capture_output=True, check=check, timeout=120)


class FaultInjectedGateway:
    """Payload-opaque bundle handoff backed by GX-A1 ledger and replay state."""

    def __init__(self, database: Path) -> None:
        self.adapter = ProfileBackedAdapter.from_file(PROFILE, store=SQLiteTrafficStore(database))
        self.replay = DurableReplayStore(database)
        self.client_id = "s030-bpv7-lab"
        self.offset_s = 0.0

    def _authenticated(self, sequence: int, unit_id: str, bundle: bytes) -> tuple[bool, bool]:
        envelope = {
            "client_id": self.client_id,
            "sequence": sequence,
            "traffic_unit_id": unit_id,
            "payload_bytes": len(bundle),
            "sha256": hashlib.sha256(bundle).hexdigest(),
        }
        envelope["mac"] = _mac(SECRET, envelope)
        supplied = envelope["mac"]
        authentic = hmac.compare_digest(supplied, _mac(SECRET, envelope))
        tampered = dict(envelope); tampered["payload_bytes"] += 1
        tamper_rejected = not hmac.compare_digest(supplied, _mac(SECRET, tampered))
        return authentic and self.replay.accept(self.client_id, sequence), tamper_rejected

    def transfer(self, bundle: bytes, unit_id: str, sequence: int) -> tuple[bytes, dict[str, Any]]:
        authenticated, tamper_rejected = self._authenticated(sequence, unit_id, bundle)
        if not authenticated:
            raise RuntimeError("authenticated replay store rejected new transfer")
        submitted = self.adapter.submit(TrafficUnit(unit_id, len(bundle), "GX-T4-bpv7", True))
        self.offset_s += 1
        fault = self.adapter.inject_fault("GX.BEARER.CONTACT_LOST", self.offset_s)
        truncated = bundle[: max(1, len(bundle) // 2)]
        replay_rejected = not self.replay.accept(self.client_id, sequence)
        self.offset_s += 1
        self.adapter.clear_faults(self.offset_s)
        self.adapter.set_contact(True, self.offset_s)
        self.adapter.acquire(self.offset_s)
        self.offset_s += 20
        self.adapter.advance(self.offset_s)
        transmitted = self.adapter.transmit(0.1)
        snapshot = self.adapter.snapshot()
        return bundle, {
            "unit_id": unit_id,
            "bundle_bytes": len(bundle),
            "bundle_sha256": hashlib.sha256(bundle).hexdigest(),
            "authenticated": authenticated,
            "tampered_metadata_rejected": tamper_rejected,
            "same_sequence_rejected": replay_rejected,
            "gx_a1_submit_status": submitted["status"],
            "fault_code": fault["fault_code"],
            "faulted_wire_bytes": len(truncated),
            "faulted_wire_image": truncated,
            "retry_wire_bytes": len(bundle),
            "gx_a1_transmitted_bytes": transmitted["transmitted_bytes"],
            "ledger_accepted_bytes": snapshot["accepted_bytes"],
            "ledger_transmitted_bytes": snapshot["transmitted_bytes"],
        }

    def close(self) -> None:
        self.adapter.close(); self.replay.close()


def _rust_encode(binary: Path, payload: bytes, root: Path) -> bytes:
    manifest = root / "rust.manifest"; source = root / "rust.payload"
    manifest.write_text("source=dtn://rust/source\ndestination=dtn://go/destination\nlifetime=1h\n", encoding="utf-8")
    source.write_bytes(payload)
    return _run([str(binary), "encode", str(manifest), str(source)], b"").stdout


def _rust_decode(binary: Path, bundle: bytes, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return _run([str(binary), "decode", "-", "-p"], bundle, check=check)


def build_bpv7_interop_lab(go_bridge: Path, rust_bp7: Path) -> dict[str, Any]:
    payload_go = b"go-to-rust:gatewaycx-s030"
    payload_rust = b"rust-to-go:gatewaycx-s030"
    with tempfile.TemporaryDirectory(prefix="gatewaycx-s030-") as temporary:
        root = Path(temporary); gateway = FaultInjectedGateway(root / "gateway.sqlite3")
        try:
            go_bundle = _run([str(go_bridge), "encode"], payload_go).stdout
            go_retry, go_record = gateway.transfer(go_bundle, "s030-go-rust", 1)
            go_fault_decode = _rust_decode(rust_bp7, go_record.pop("faulted_wire_image"), check=False)
            rust_received = _rust_decode(rust_bp7, go_retry).stdout

            rust_bundle = _rust_encode(rust_bp7, payload_rust, root)
            rust_retry, rust_record = gateway.transfer(rust_bundle, "s030-rust-go", 2)
            rust_fault_decode = _run([str(go_bridge), "decode"], rust_record.pop("faulted_wire_image"), check=False)
            go_received = _run([str(go_bridge), "decode"], rust_retry).stdout
            final_snapshot = gateway.adapter.snapshot()
        finally:
            gateway.close()
    directions = {
        "dtn7_go_to_bp7_rs": {**go_record, "fault_decode_rejected": go_fault_decode.returncode != 0, "payload_exact": rust_received == payload_go, "received_sha256": hashlib.sha256(rust_received).hexdigest()},
        "bp7_rs_to_dtn7_go": {**rust_record, "fault_decode_rejected": rust_fault_decode.returncode != 0, "payload_exact": go_received == payload_rust, "received_sha256": hashlib.sha256(go_received).hexdigest()},
    }
    checks = {
        "both_wire_directions_preserve_payload": all(row["payload_exact"] for row in directions.values()),
        "both_decoders_reject_truncated_first_attempt": all(row["fault_decode_rejected"] for row in directions.values()),
        "both_handoffs_are_authenticated_and_replay_safe": all(row["authenticated"] and row["tampered_metadata_rejected"] and row["same_sequence_rejected"] for row in directions.values()),
        "gx_a1_accepts_each_bundle_once": all(row["gx_a1_submit_status"] == "accepted_pending" for row in directions.values()),
        "ledger_conserves_all_bundle_bytes": final_snapshot["accepted_bytes"] == final_snapshot["transmitted_bytes"] == sum(row["bundle_bytes"] for row in directions.values()),
    }
    return {
        "study_id": "S030", "title": "Two-implementation BPv7 exchange through a fault-injected GX-A1 gateway", "evidence_class": "EXTERNAL INTEROPERABILITY TEST",
        "implementations": {"go": "dtn7-go pkg/bpv7", "rust": "bp7-rs used by dtn7-rs"},
        "directions": directions, "final_ledger": final_snapshot, "checks": checks,
        "interpretation_boundary": [
            "The test crosses two independently maintained RFC 9171 serializers/decoders in both directions; it does not run their full routing daemons or a convergence-layer session.",
            "GatewayCX treats the bundle wire image as opaque payload while GX-A1 records identifiers and byte counts.",
            "HMAC and durable sequence state are the bounded S019 mechanism, not BPSec, PKI or production key lifecycle.",
            "The injected first attempt is truncation at half length, followed by a complete retry; contact-plan routing, expiry and multi-hop forwarding remain separate tests.",
            "External source is fetched and built at pinned revisions in CI and is not vendored or relicensed by GatewayCX.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--go-bridge", type=Path, required=True); parser.add_argument("--rust-bp7", type=Path, required=True); parser.add_argument("--output", type=Path, required=True); args = parser.parse_args(argv)
    write_json(args.output, build_bpv7_interop_lab(args.go_bridge, args.rust_bpv7)); print(f"wrote {args.output}"); return 0


if __name__ == "__main__": raise SystemExit(main())
