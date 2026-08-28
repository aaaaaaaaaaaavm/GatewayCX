"""S015 integrated RF/optical, durable-object and GX-O1 event replay."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .diagnostics import make_event, validate_trace
from .handover import (
    DURATION_S,
    OPTICAL_CAPACITY_MBPS,
    OPTICAL_OUTAGE_START_S,
    OPTICAL_REACQUISITION_S,
    OPTICAL_RETURN_S,
    RF_CAPACITY_MBPS,
    RF_KEEPALIVE_MBPS,
    STEP_S,
    WARM_SWITCH_S,
    replay as handover_replay,
)
from .model import SPEED_OF_LIGHT_KM_S


DISTANCE_KM = 384_400.0
OBJECT_ADMISSION_S = 50.0
OBJECT_BYTES = 1_000_000_000
REMOTE_PROCESSING_S = 0.020
CONTROL_MBPS = 0.5
INTERACTIVE_MBPS = 2.0


def _rate_bytes(rate_mbps: float) -> int:
    return round(rate_mbps * 1_000_000 * STEP_S / 8)


def _active_bearer(time_s: float) -> tuple[str | None, float]:
    optical_recovered_s = OPTICAL_RETURN_S + OPTICAL_REACQUISITION_S
    if time_s < OPTICAL_OUTAGE_START_S or time_s >= optical_recovered_s:
        return "gx-reference-optical", OPTICAL_CAPACITY_MBPS
    if time_s >= OPTICAL_OUTAGE_START_S + WARM_SWITCH_S:
        return "gx-reference-rf", RF_CAPACITY_MBPS
    return None, 0.0


def _freeze(
    bearer_id: str,
    link_state: str,
    capacity_mbps: float,
    queue_bytes: int,
) -> dict[str, Any]:
    return {
        "bearer_id": bearer_id,
        "link_state": link_state,
        "tx_rate_mbps": capacity_mbps,
        "queue_bytes": queue_bytes,
        "missing_bytes": queue_bytes,
    }


def build_integrated_replay() -> dict[str, Any]:
    queue_bytes = 0
    maximum_queue_bytes = 0
    object_delivered_bytes = 0
    object_path_bytes = {"gx-reference-optical": 0, "gx-reference-rf": 0}
    offered = {"control": 0, "interactive": 0}
    delivered = {"control": 0, "interactive": 0}
    rejected = {"control": 0, "interactive": 0}
    keepalive_bytes = 0
    events: list[dict[str, Any]] = []
    object_last_byte_transmitted_s: float | None = None

    for step in range(round(DURATION_S / STEP_S)):
        time_s = step * STEP_S
        bearer_id, capacity_mbps = _active_bearer(time_s)
        if capacity_mbps == OPTICAL_CAPACITY_MBPS:
            keepalive_bytes += _rate_bytes(RF_KEEPALIVE_MBPS)

        if time_s == OBJECT_ADMISSION_S:
            queue_bytes = OBJECT_BYTES
            maximum_queue_bytes = OBJECT_BYTES
            events.append(
                make_event(
                    "evt-001", round(time_s * 1_000), "durable-ingress", "lunar_surface",
                    "delivery_status", "info", "GX.QUEUE.ACCEPTED_PENDING",
                    "submitted", "accepted_pending",
                    _freeze("gx-reference-optical", "available", OPTICAL_CAPACITY_MBPS, queue_bytes),
                )
            )

        if time_s == OPTICAL_OUTAGE_START_S:
            events.append(
                make_event(
                    "evt-002", round(time_s * 1_000), "bearer-adapter", "lunar_surface",
                    "fault_asserted", "error", "GX.BEARER.CONTACT_LOST",
                    "optical_available", "unavailable",
                    _freeze("gx-reference-optical", "unavailable", 0.0, queue_bytes),
                )
            )
        if time_s == OPTICAL_OUTAGE_START_S + WARM_SWITCH_S:
            events.append(
                make_event(
                    "evt-003", round(time_s * 1_000), "bearer-adapter", "lunar_surface",
                    "fault_cleared", "warning", "GX.BEARER.FALLBACK_ACTIVE",
                    "unavailable", "degraded_rf",
                    _freeze("gx-reference-rf", "degraded", RF_CAPACITY_MBPS, queue_bytes),
                )
            )
        if time_s == OPTICAL_RETURN_S + OPTICAL_REACQUISITION_S:
            events.append(
                make_event(
                    "evt-004", round(time_s * 1_000), "bearer-adapter", "lunar_surface",
                    "state_transition", "info", "GX.BEARER.PREFERRED_RESTORED",
                    "degraded_rf", "optical_available",
                    _freeze("gx-reference-optical", "available", OPTICAL_CAPACITY_MBPS, queue_bytes),
                )
            )

        fresh = {
            "control": _rate_bytes(CONTROL_MBPS),
            "interactive": _rate_bytes(INTERACTIVE_MBPS),
        }
        capacity_bytes = _rate_bytes(capacity_mbps)
        for traffic_class in ("control", "interactive"):
            offered[traffic_class] += fresh[traffic_class]
            sent = min(fresh[traffic_class], capacity_bytes)
            delivered[traffic_class] += sent
            rejected[traffic_class] += fresh[traffic_class] - sent
            capacity_bytes -= sent

        if queue_bytes and capacity_bytes:
            sent = min(queue_bytes, capacity_bytes)
            queue_bytes -= sent
            object_delivered_bytes += sent
            if bearer_id is None:
                raise AssertionError("bytes cannot be allocated without an active bearer")
            object_path_bytes[bearer_id] += sent
            if queue_bytes == 0:
                object_last_byte_transmitted_s = time_s + STEP_S

    if object_last_byte_transmitted_s is None:
        raise AssertionError("object did not drain during the replay")
    one_way_s = DISTANCE_KM / SPEED_OF_LIGHT_KM_S
    adapter_delivery_s = object_last_byte_transmitted_s + one_way_s
    remote_completion_s = adapter_delivery_s + REMOTE_PROCESSING_S
    events.extend(
        [
            make_event(
                "evt-005", round(adapter_delivery_s * 1_000), "delivery-adapter", "earth",
                "delivery_status", "info", "GX.DELIVERY.ADAPTER_DELIVERED",
                "accepted_pending", "bp_delivered",
                _freeze("gx-reference-optical", "available", OPTICAL_CAPACITY_MBPS, 0),
            ),
            make_event(
                "evt-006", round(remote_completion_s * 1_000), "application-receipt", "earth",
                "delivery_status", "info", "GX.DELIVERY.REMOTE_COMPLETED",
                "bp_delivered", "remote_completed",
                _freeze("gx-reference-optical", "available", OPTICAL_CAPACITY_MBPS, 0),
            ),
        ]
    )
    events.sort(key=lambda item: item["observed_offset_ms"])
    trace = {
        "profile_id": "GX-O1",
        "schema_version": "0.1",
        "trace_id": "gx-s015-integrated-001",
        "time_basis": "synthetic_replay_offset",
        "traffic_unit": {
            "traffic_unit_id": "urn:gatewaycx:synthetic:s015-object-001",
            "traffic_class": "GX-T3-operational",
            "payload_bytes": OBJECT_BYTES,
            "payload_content_recorded": False,
        },
        "events": events,
        "interpretation_boundary": [
            "The trace is generated from a byte-budget replay and contains no observed telemetry.",
            "Adapter delivery and remote completion remain separate acknowledgement states.",
        ],
    }
    trace_errors = validate_trace(trace)
    if trace_errors:
        raise AssertionError(f"integrated GX-O1 trace failed validation: {trace_errors}")

    s010_warm = handover_replay("warm_standby")
    return {
        "study_id": "S015",
        "title": "Integrated warm-handover durable-delivery replay",
        "evidence_class": "MODEL + TEST",
        "inputs": {
            "duration_s": DURATION_S,
            "step_s": STEP_S,
            "distance_km": DISTANCE_KM,
            "object_admission_s": OBJECT_ADMISSION_S,
            "object_bytes": OBJECT_BYTES,
            "optical_capacity_mbps": OPTICAL_CAPACITY_MBPS,
            "rf_capacity_mbps": RF_CAPACITY_MBPS,
            "optical_outage_start_s": OPTICAL_OUTAGE_START_S,
            "rf_warm_switch_s": WARM_SWITCH_S,
            "optical_return_s": OPTICAL_RETURN_S,
            "optical_reacquisition_s": OPTICAL_REACQUISITION_S,
            "control_mbps": CONTROL_MBPS,
            "interactive_mbps": INTERACTIVE_MBPS,
        },
        "continuity": {
            "offered_bytes": offered,
            "delivered_bytes": delivered,
            "rejected_bytes": rejected,
            "maximum_interruption_s": WARM_SWITCH_S,
            "rf_keepalive_bytes": keepalive_bytes,
        },
        "durable_object": {
            "accepted_bytes": OBJECT_BYTES,
            "delivered_bytes": object_delivered_bytes,
            "queued_at_end_bytes": queue_bytes,
            "maximum_queue_bytes": maximum_queue_bytes,
            "retransmitted_bytes": 0,
            "bytes_by_bearer": object_path_bytes,
            "last_byte_transmitted_s": round(object_last_byte_transmitted_s, 6),
            "adapter_delivery_s": round(adapter_delivery_s, 6),
            "remote_completion_s": round(remote_completion_s, 6),
        },
        "gx_o1_trace": trace,
        "composition_checks": {
            "control_rejection_matches_s010_warm": (
                rejected["control"] == s010_warm["rejected_bytes"]["control"]
            ),
            "interactive_rejection_matches_s010_warm": (
                rejected["interactive"] == s010_warm["rejected_bytes"]["interactive"]
            ),
            "rf_keepalive_matches_s010_warm": keepalive_bytes == s010_warm["rf_keepalive_bytes"],
            "durable_conservation": OBJECT_BYTES == object_delivered_bytes + queue_bytes,
            "diagnostic_trace_conforms_gx_o1": not trace_errors,
            "application_plaintext_recorded": False,
        },
        "interpretation_boundary": [
            "All traffic, capacities and event times are synthetic assumptions inherited from S010 or declared here.",
            "The replay allocates byte budgets, not packets, congestion windows, BP bundles or radio resources.",
            "RF and optical failure domains are assumed independent and terminal power is not modelled.",
            "Zero retransmission follows from the persistent object ledger assumption; no protocol implements it here.",
            "The GX-O1 events are generated evidence, not observed provider telemetry.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/S015_integrated_replay.json"))
    args = parser.parse_args(argv)
    rendered = json.dumps(build_integrated_replay(), indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
