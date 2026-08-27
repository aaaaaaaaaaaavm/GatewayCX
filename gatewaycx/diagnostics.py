"""GX-O1 provider-neutral diagnostic event and flight-recorder profile."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


FAULT_CODES = {
    "GX.QUEUE.ACCEPTED_PENDING": {
        "category": "queue",
        "description": "A traffic unit was persisted locally and remains pending remote completion.",
        "terminal": False,
    },
    "GX.BEARER.CONTACT_LOST": {
        "category": "bearer",
        "description": "The selected bearer became unavailable during an active transfer.",
        "terminal": False,
    },
    "GX.BEARER.CONTACT_RESTORED": {
        "category": "bearer",
        "description": "The selected bearer returned to an available state.",
        "terminal": False,
    },
    "GX.DELIVERY.ADAPTER_DELIVERED": {
        "category": "delivery",
        "description": "The destination delivery adapter received the payload.",
        "terminal": False,
    },
    "GX.DELIVERY.REMOTE_COMPLETED": {
        "category": "delivery",
        "description": "The remote application returned an idempotency-bound processing receipt.",
        "terminal": True,
    },
    "GX.DELIVERY.EXPIRED": {
        "category": "delivery",
        "description": "The traffic unit lifetime ended without remote application completion.",
        "terminal": True,
    },
    "GX.STORAGE.DEPLETED": {
        "category": "storage",
        "description": "Durable storage could not retain another accepted traffic unit.",
        "terminal": False,
    },
    "GX.SECURITY.RECEIPT_INVALID": {
        "category": "security",
        "description": "A remote application receipt failed identity, integrity or binding checks.",
        "terminal": False,
    },
}

EVENT_TYPES = {"delivery_status", "fault_asserted", "fault_cleared"}
SEVERITIES = {"info", "warning", "error", "critical"}
REGIONS = {"earth", "cislunar", "lunar_orbit", "lunar_surface"}
DELIVERY_STAGES = {"accepted_pending": 1, "bp_delivered": 2, "remote_completed": 3}
FREEZE_FRAME_FIELDS = {
    "bearer_id",
    "link_state",
    "tx_rate_mbps",
    "queue_bytes",
    "missing_bytes",
}


def build_fault_registry() -> dict[str, Any]:
    return {
        "profile_id": "GX-O1",
        "schema_version": "0.1",
        "codes": [
            {"code": code, **definition}
            for code, definition in sorted(FAULT_CODES.items())
        ],
        "boundary": [
            "Codes identify portable event classes, not vendor root causes.",
            "Provider detail may be attached separately without changing the portable code.",
            "A terminal delivery state is not evidence of physical link or hardware qualification.",
        ],
    }


def _event(
    event_id: str,
    offset_ms: int,
    component: str,
    region: str,
    event_type: str,
    severity: str,
    fault_code: str,
    previous: str,
    current: str,
    freeze_frame: dict[str, Any],
) -> dict[str, Any]:
    return {
        "event_id": event_id,
        "observed_offset_ms": offset_ms,
        "source": {
            "node_id": f"gx-reference-{region.replace('_', '-')}",
            "region": region,
            "component": component,
        },
        "event_type": event_type,
        "severity": severity,
        "fault_code": fault_code,
        "state": {"previous": previous, "current": current},
        "freeze_frame": freeze_frame,
        "privacy": {
            "payload_plaintext_included": False,
            "user_identifier_included": False,
        },
    }


def build_reference_trace() -> dict[str, Any]:
    bearer_up = {
        "bearer_id": "gx-reference-optical",
        "link_state": "available",
        "tx_rate_mbps": 20.0,
        "queue_bytes": 10_000_000,
        "missing_bytes": 10_000_000,
    }
    return {
        "profile_id": "GX-O1",
        "schema_version": "0.1",
        "trace_id": "gx-s005-opaque-001",
        "time_basis": "synthetic_replay_offset",
        "traffic_unit": {
            "traffic_unit_id": "urn:gatewaycx:synthetic:s005-object-001",
            "traffic_class": "GX-T3-operational",
            "payload_bytes": 10_000_000,
            "payload_content_recorded": False,
        },
        "events": [
            _event(
                "evt-001", 20, "durable-ingress", "lunar_surface", "delivery_status",
                "info", "GX.QUEUE.ACCEPTED_PENDING", "submitted", "accepted_pending",
                bearer_up,
            ),
            _event(
                "evt-002", 1_600, "bearer-adapter", "lunar_surface", "fault_asserted",
                "error", "GX.BEARER.CONTACT_LOST", "available", "unavailable",
                {
                    **bearer_up,
                    "link_state": "unavailable",
                    "tx_rate_mbps": 0.0,
                    "queue_bytes": 6_000_000,
                    "missing_bytes": 6_000_000,
                },
            ),
            _event(
                "evt-003", 121_600, "bearer-adapter", "lunar_surface", "fault_cleared",
                "info", "GX.BEARER.CONTACT_RESTORED", "unavailable", "available",
                {
                    **bearer_up,
                    "queue_bytes": 6_000_000,
                    "missing_bytes": 6_000_000,
                },
            ),
            _event(
                "evt-004", 125_282, "delivery-adapter", "earth", "delivery_status",
                "info", "GX.DELIVERY.ADAPTER_DELIVERED", "accepted_pending", "bp_delivered",
                {
                    **bearer_up,
                    "queue_bytes": 0,
                    "missing_bytes": 0,
                },
            ),
            _event(
                "evt-005", 125_302, "application-receipt", "earth", "delivery_status",
                "info", "GX.DELIVERY.REMOTE_COMPLETED", "bp_delivered", "remote_completed",
                {
                    **bearer_up,
                    "queue_bytes": 0,
                    "missing_bytes": 0,
                },
            ),
        ],
        "interpretation_boundary": [
            "The trace is generated from S005 synthetic offsets and does not contain observed telemetry.",
            "Freeze-frame fields are the portable minimum, not a replacement for provider diagnostics.",
            "The trace identifier correlates events but contains no user or payload identity.",
        ],
    }


def validate_trace(trace: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {"profile_id", "schema_version", "trace_id", "time_basis", "traffic_unit", "events"}
    missing = sorted(required - trace.keys())
    if missing:
        return [f"missing top-level fields: {missing}"]
    if trace["profile_id"] != "GX-O1":
        errors.append("profile_id must be GX-O1")
    if trace["schema_version"] != "0.1":
        errors.append("schema_version must be 0.1")
    if not isinstance(trace["trace_id"], str) or not trace["trace_id"]:
        errors.append("trace_id must be a non-empty string")

    traffic = trace["traffic_unit"]
    if not isinstance(traffic, dict):
        errors.append("traffic_unit must be an object")
    else:
        if traffic.get("payload_content_recorded") is not False:
            errors.append("traffic_unit.payload_content_recorded must be false")
        payload_bytes = traffic.get("payload_bytes")
        if not isinstance(payload_bytes, int) or isinstance(payload_bytes, bool) or payload_bytes < 0:
            errors.append("traffic_unit.payload_bytes must be a non-negative integer")

    events = trace["events"]
    if not isinstance(events, list) or not events:
        errors.append("events must be a non-empty array")
        return errors
    seen_ids: set[str] = set()
    previous_offset = -1
    delivery_stage = 0
    for index, event in enumerate(events):
        prefix = f"events[{index}]"
        if not isinstance(event, dict):
            errors.append(f"{prefix} must be an object")
            continue
        event_id = event.get("event_id")
        if not isinstance(event_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,63}", event_id):
            errors.append(f"{prefix}.event_id is invalid")
        elif event_id in seen_ids:
            errors.append(f"{prefix}.event_id is duplicated")
        else:
            seen_ids.add(event_id)
        offset = event.get("observed_offset_ms")
        if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
            errors.append(f"{prefix}.observed_offset_ms must be a non-negative integer")
        elif offset <= previous_offset:
            errors.append(f"{prefix}.observed_offset_ms must increase monotonically")
        else:
            previous_offset = offset
        if event.get("event_type") not in EVENT_TYPES:
            errors.append(f"{prefix}.event_type is invalid")
        if event.get("severity") not in SEVERITIES:
            errors.append(f"{prefix}.severity is invalid")
        if event.get("fault_code") not in FAULT_CODES:
            errors.append(f"{prefix}.fault_code is not in the GX-O1 registry")
        source = event.get("source")
        if not isinstance(source, dict) or not source.get("node_id") or not source.get("component"):
            errors.append(f"{prefix}.source requires node_id and component")
        elif source.get("region") not in REGIONS:
            errors.append(f"{prefix}.source.region is invalid")
        freeze_frame = event.get("freeze_frame")
        if not isinstance(freeze_frame, dict):
            errors.append(f"{prefix}.freeze_frame must be an object")
        else:
            absent = sorted(FREEZE_FRAME_FIELDS - freeze_frame.keys())
            if absent:
                errors.append(f"{prefix}.freeze_frame fields absent: {absent}")
        privacy = event.get("privacy")
        if not isinstance(privacy, dict):
            errors.append(f"{prefix}.privacy must be an object")
        else:
            if privacy.get("payload_plaintext_included") is not False:
                errors.append(f"{prefix} must not include payload plaintext")
            if privacy.get("user_identifier_included") is not False:
                errors.append(f"{prefix} must not include a user identifier")
        if event.get("event_type") == "delivery_status":
            state = event.get("state")
            current = state.get("current") if isinstance(state, dict) else None
            stage = DELIVERY_STAGES.get(current)
            if stage is None:
                errors.append(f"{prefix}.state.current is not a delivery state")
            elif stage != delivery_stage + 1:
                errors.append(f"{prefix} collapses or reorders delivery acknowledgement states")
            else:
                delivery_stage = stage
        if event.get("event_type") == "fault_asserted" and event.get("severity") not in {
            "error", "critical"
        }:
            errors.append(f"{prefix} asserted faults require error or critical severity")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--trace-output",
        type=Path,
        default=Path("results/S014_diagnostic_trace.json"),
    )
    parser.add_argument(
        "--registry-output",
        type=Path,
        default=Path("profiles/diagnostics/gx-o1-fault-codes.json"),
    )
    parser.add_argument("--validate", type=Path)
    args = parser.parse_args(argv)
    if args.validate is not None:
        try:
            trace = json.loads(args.validate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"{args.validate}: cannot read JSON: {exc}")
            return 1
        errors = validate_trace(trace)
        if errors:
            print(f"{args.validate}: failed")
            for error in errors:
                print(f"- {error}")
            return 1
        print(f"{args.validate}: passed")
        return 0

    trace = build_reference_trace()
    errors = validate_trace(trace)
    if errors:
        raise RuntimeError(f"generated trace failed validation: {errors}")
    for path, value in (
        (args.trace_output, trace),
        (args.registry_output, build_fault_registry()),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
