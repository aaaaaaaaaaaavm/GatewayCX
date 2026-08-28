"""S016 deterministic probe of the GX-A1 runtime bearer-adapter seam."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .bearer_adapter import ProfileBackedAdapter, TrafficUnit


PROFILE_PATHS = (
    Path("profiles/bearers/reference-optical.json"),
    Path("profiles/bearers/reference-rf.json"),
)
UNIT_BYTES = 65_536
UNIT_COUNT = 122
FIRST_TRANSMIT_WINDOW_S = 0.1
FAULT_CODE = "GX.BEARER.CONTACT_LOST"


def _signature(response: dict[str, Any]) -> list[str]:
    return sorted(response)


def _exercise(path: Path) -> dict[str, Any]:
    adapter = ProfileBackedAdapter.from_file(path)
    capabilities = adapter.capabilities()
    profile = capabilities["profile"]
    accepted = []
    for index in range(UNIT_COUNT):
        accepted.append(
            adapter.submit(
                TrafficUnit(
                    traffic_unit_id=f"{adapter.bearer_id}-unit-{index:03d}",
                    payload_bytes=UNIT_BYTES,
                    traffic_class="GX-T3-operational",
                )
            )
        )
    accepted_bytes = UNIT_BYTES * UNIT_COUNT
    duplicate = adapter.submit(
        TrafficUnit(
            traffic_unit_id=f"{adapter.bearer_id}-unit-000",
            payload_bytes=UNIT_BYTES,
            traffic_class="GX-T3-operational",
        )
    )
    oversize = adapter.submit(
        TrafficUnit(
            traffic_unit_id=f"{adapter.bearer_id}-oversize",
            payload_bytes=UNIT_BYTES + 1,
            traffic_class="GX-T3-operational",
        )
    )
    queued_before_contact = adapter.snapshot()

    contact = adapter.set_contact(True, 1.0)
    acquiring = adapter.acquire(1.0)
    ready_at_s = float(acquiring["ready_at_s"])
    ready = adapter.advance(ready_at_s)
    first_transmit = adapter.transmit(FIRST_TRANSMIT_WINDOW_S)
    expected_first_bytes = min(
        accepted_bytes,
        int(
            float(profile["performance"]["forward_capacity_mbps"])
            * 1_000_000
            * FIRST_TRANSMIT_WINDOW_S
            / 8
        ),
    )
    queue_before_fault = adapter.queue_bytes
    fault = adapter.inject_fault(FAULT_CODE, first_transmit["observed_offset_s"] + 0.1)
    fault_snapshot = adapter.snapshot()
    blocked = adapter.transmit(FIRST_TRANSMIT_WINDOW_S)
    queue_during_fault = adapter.queue_bytes

    clear = adapter.clear_faults(fault["observed_offset_s"] + 0.1)
    recovery_contact = adapter.set_contact(True, clear["observed_offset_s"])
    recovery_acquire = adapter.acquire(clear["observed_offset_s"])
    recovery_ready = adapter.advance(float(recovery_acquire["ready_at_s"]))
    recovery_windows = 0
    recovery_transmitted = 0
    last_transmit = first_transmit
    while adapter.queue_bytes:
        last_transmit = adapter.transmit(FIRST_TRANSMIT_WINDOW_S)
        recovery_transmitted += int(last_transmit["transmitted_bytes"])
        recovery_windows += 1
    final_snapshot = adapter.snapshot()

    operation_responses = {
        "capabilities": capabilities,
        "snapshot": queued_before_contact,
        "submit": accepted[0],
        "set_contact": contact,
        "acquire": acquiring,
        "advance": ready,
        "transmit": first_transmit,
        "inject_fault": fault,
        "clear_faults": clear,
    }
    signatures = {
        operation: _signature(response) for operation, response in operation_responses.items()
    }
    checks = {
        "all_units_accepted_pending": all(item["status"] == "accepted_pending" for item in accepted),
        "duplicate_not_requeued": duplicate["status"] == "duplicate_known",
        "oversize_rejected_at_mtu": (
            oversize["status"] == "rejected"
            and oversize["reason"] == "traffic_unit_too_large"
        ),
        "profile_acquisition_applied": (
            ready_at_s == 1.0 + float(profile["performance"]["acquisition_max_s"])
        ),
        "profile_capacity_applied": first_transmit["transmitted_bytes"] == expected_first_bytes,
        "fault_blocks_transmission": (
            blocked["status"] == "blocked" and blocked["transmitted_bytes"] == 0
        ),
        "queue_survives_fault": queue_before_fault == queue_during_fault,
        "recovery_requires_reacquisition": (
            recovery_contact["link_state"] == "unavailable"
            and recovery_acquire["status"] == "accepted"
            and recovery_ready["link_state"] == "ready"
        ),
        "byte_ledger_conserved": (
            accepted_bytes
            == final_snapshot["transmitted_bytes"] + final_snapshot["queue_bytes"]
        ),
        "queue_drained_after_recovery": final_snapshot["queue_bytes"] == 0,
    }
    return {
        "profile_path": path.as_posix(),
        "bearer_id": adapter.bearer_id,
        "media": profile["media"],
        "accepted_units": UNIT_COUNT,
        "accepted_bytes": accepted_bytes,
        "queued_before_contact_bytes": queued_before_contact["queue_bytes"],
        "acquisition_ready_at_s": ready_at_s,
        "first_window": {
            "duration_s": FIRST_TRANSMIT_WINDOW_S,
            "expected_bytes": expected_first_bytes,
            "transmitted_bytes": first_transmit["transmitted_bytes"],
            "queued_after_bytes": first_transmit["queue_bytes"],
        },
        "fault": {
            "code": FAULT_CODE,
            "link_state": fault_snapshot["link_state"],
            "queue_before_bytes": queue_before_fault,
            "queue_during_bytes": queue_during_fault,
            "blocked_transmitted_bytes": blocked["transmitted_bytes"],
        },
        "recovery": {
            "reacquired_at_s": recovery_ready["observed_offset_s"],
            "transmit_windows": recovery_windows,
            "transmitted_bytes": recovery_transmitted,
            "last_operation_offset_s": last_transmit["observed_offset_s"],
        },
        "final_ledger": {
            "accepted_bytes": final_snapshot["accepted_bytes"],
            "transmitted_bytes": final_snapshot["transmitted_bytes"],
            "queue_bytes": final_snapshot["queue_bytes"],
            "link_epoch": final_snapshot["link_epoch"],
        },
        "operation_signatures": signatures,
        "checks": checks,
    }


def build_adapter_probe(profile_paths: tuple[Path, ...] = PROFILE_PATHS) -> dict[str, Any]:
    adapters = [_exercise(path) for path in profile_paths]
    first_signatures = adapters[0]["operation_signatures"]
    return {
        "study_id": "S016",
        "title": "GX-A1 profile-backed bearer adapter probe",
        "evidence_class": "MODEL + TEST",
        "inputs": {
            "profile_paths": [path.as_posix() for path in profile_paths],
            "traffic_unit_bytes": UNIT_BYTES,
            "traffic_unit_count": UNIT_COUNT,
            "first_transmit_window_s": FIRST_TRANSMIT_WINDOW_S,
            "fault_code": FAULT_CODE,
            "payload_content_supplied": False,
        },
        "adapters": adapters,
        "cross_adapter_checks": {
            "same_operation_signatures": all(
                item["operation_signatures"] == first_signatures for item in adapters[1:]
            ),
            "all_adapter_checks_pass": all(
                all(item["checks"].values()) for item in adapters
            ),
            "both_media_families_exercised": {item["media"] for item in adapters}
            == {"optical", "rf"},
            "payload_content_recorded": False,
        },
        "interpretation_boundary": [
            "Both reference instances use one profile-backed Python implementation; this is interface parity, not independent multi-vendor interoperability.",
            "The GX-B1 capacities and acquisition ceilings are illustrative assumed inputs, not hardware measurements.",
            "Transmission is a byte-budget ledger with no waveform, pointing, packet, BPv7 or payload implementation.",
            "Fault injection is an in-process state transition; no physical link or provider control plane is connected.",
            "GX-A1/0.1 is an exploratory runtime seam and not a published standard.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/S016_adapter_probe.json"))
    args = parser.parse_args(argv)
    rendered = json.dumps(build_adapter_probe(), indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
