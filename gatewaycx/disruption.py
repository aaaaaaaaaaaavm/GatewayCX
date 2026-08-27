"""S005 semantic replay for native IP and durable delivery across an outage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .model import SPEED_OF_LIGHT_KM_S


DISTANCE_KM = 384_400.0
CAPACITY_MBPS = 20.0
OBJECT_BYTES = 10_000_000
BYTES_BEFORE_OUTAGE = 4_000_000
OUTAGE_S = 120.0
LOCAL_ACCEPTANCE_S = 0.020
REMOTE_PROCESSING_S = 0.020
NATIVE_RECONNECT_ROUND_TRIPS = 3


def _round(value: float) -> float:
    return round(value, 6)


def _serialization_s(byte_count: int) -> float:
    return byte_count * 8.0 / (CAPACITY_MBPS * 1_000_000.0)


def _native_https_retry() -> dict[str, Any]:
    one_way_s = DISTANCE_KM / SPEED_OF_LIGHT_KM_S
    round_trip_s = 2.0 * one_way_s
    partial_s = _serialization_s(BYTES_BEFORE_OUTAGE)
    reconnect_s = NATIVE_RECONNECT_ROUND_TRIPS * round_trip_s
    retry_transfer_s = _serialization_s(OBJECT_BYTES)
    completed_s = partial_s + OUTAGE_S + reconnect_s + retry_transfer_s
    return {
        "mode": "native_https_retry",
        "client_contract": "ordinary end-to-end HTTPS",
        "delivery_contract": "synchronous; retry belongs to the application or user",
        "events": [
            {"at_s": 0.0, "event": "https_request_started", "user_state": "waiting"},
            {
                "at_s": _round(partial_s),
                "event": "path_lost_after_partial_transfer",
                "user_state": "failed_or_timed_out",
            },
            {
                "at_s": _round(partial_s + OUTAGE_S),
                "event": "path_restored",
                "user_state": "retry_required",
            },
            {
                "at_s": _round(completed_s),
                "event": "retry_http_response_received",
                "user_state": "remote_completion_known",
            },
        ],
        "traffic": {
            "wire_bytes": BYTES_BEFORE_OUTAGE + OBJECT_BYTES,
            "retransmitted_bytes": BYTES_BEFORE_OUTAGE,
            "durable_bytes_retained_across_outage": 0,
        },
        "timing": {
            "completion_s": _round(completed_s),
            "reconnect_round_trips": NATIVE_RECONNECT_ROUND_TRIPS,
        },
        "acknowledgement": {
            "local_durable_acceptance": False,
            "transport_ack_means_remote_application_processed": False,
            "final_http_response_is_application_defined_completion": True,
        },
        "security": {
            "application_tls_endpoints": ["lunar_client", "earth_service"],
            "gateway_can_read_application_plaintext": False,
            "payload_object_encryption_required": False,
        },
        "mutation_retry": {
            "outcome_after_lost_response": "unknown",
            "duplicate_effect_possible_without_idempotency_key": True,
            "exactly_once_claimed": False,
        },
    }


def _durable_mode(mode: str, opaque_payload: bool) -> dict[str, Any]:
    one_way_s = DISTANCE_KM / SPEED_OF_LIGHT_KM_S
    partial_s = _serialization_s(BYTES_BEFORE_OUTAGE)
    remaining_s = _serialization_s(OBJECT_BYTES - BYTES_BEFORE_OUTAGE)
    adapter_delivery_s = partial_s + OUTAGE_S + remaining_s + one_way_s
    processed_s = adapter_delivery_s + REMOTE_PROCESSING_S
    if opaque_payload:
        client_contract = "delay-aware object submission over ordinary local HTTPS"
        tls_endpoints = ["lunar_client", "lunar_ingress"]
        gateway_plaintext = False
        payload_encryption = True
        security_boundary = "application object remains encrypted across storage and DTN forwarding"
    else:
        client_contract = "service-owner terminating HTTPS proxy with explicit pending response"
        tls_endpoints = ["lunar_client", "lunar_proxy"]
        gateway_plaintext = True
        payload_encryption = False
        security_boundary = "TLS terminates at the approved lunar proxy; a new protected leg begins"
    return {
        "mode": mode,
        "client_contract": client_contract,
        "delivery_contract": "durable local acceptance followed by asynchronous remote completion",
        "events": [
            {
                "at_s": LOCAL_ACCEPTANCE_S,
                "event": "object_persisted_and_accepted",
                "user_state": "accepted_pending",
            },
            {
                "at_s": _round(partial_s),
                "event": "path_lost_with_chunk_ledger_persisted",
                "user_state": "accepted_pending",
            },
            {
                "at_s": _round(partial_s + OUTAGE_S),
                "event": "path_restored_and_missing_chunks_resumed",
                "user_state": "accepted_pending",
            },
            {
                "at_s": _round(adapter_delivery_s),
                "event": "bp_payload_delivered_to_remote_adapter",
                "user_state": "delivered_not_yet_processed",
            },
            {
                "at_s": _round(processed_s),
                "event": "remote_application_receipt_recorded",
                "user_state": "remote_completion_known",
            },
        ],
        "traffic": {
            "wire_bytes": OBJECT_BYTES,
            "retransmitted_bytes": 0,
            "durable_bytes_retained_across_outage": BYTES_BEFORE_OUTAGE,
        },
        "timing": {
            "local_acceptance_s": LOCAL_ACCEPTANCE_S,
            "remote_completion_s": _round(processed_s),
        },
        "acknowledgement": {
            "local_durable_acceptance": True,
            "local_acceptance_means_remote_completion": False,
            "bp_delivery_report_means_remote_application_processed": False,
            "application_receipt_required_for_remote_completion": True,
            "status_reports_assumed_always_available": False,
        },
        "security": {
            "application_tls_endpoints": tls_endpoints,
            "gateway_can_read_application_plaintext": gateway_plaintext,
            "payload_object_encryption_required": payload_encryption,
            "boundary": security_boundary,
            "bpsec_role": "candidate integrity/confidentiality protection between BP security endpoints",
        },
        "mutation_retry": {
            "idempotency_key_required": True,
            "duplicate_transport_delivery_possible": True,
            "duplicate_application_effect_suppressed_by_model": True,
            "exactly_once_claimed": False,
        },
    }


def build_disruption_study() -> dict[str, Any]:
    native = _native_https_retry()
    proxy = _durable_mode("terminating_deferred_proxy", opaque_payload=False)
    opaque = _durable_mode("opaque_deferred_object", opaque_payload=True)
    return {
        "study_id": "S005",
        "title": "IP/DTN interruption and recovery semantics",
        "evidence_class": "MODEL",
        "inputs": {
            "distance_km": DISTANCE_KM,
            "capacity_mbps": CAPACITY_MBPS,
            "object_bytes": OBJECT_BYTES,
            "bytes_before_outage": BYTES_BEFORE_OUTAGE,
            "outage_s": OUTAGE_S,
            "local_acceptance_s": LOCAL_ACCEPTANCE_S,
            "remote_processing_s": REMOTE_PROCESSING_S,
            "native_reconnect_round_trips": NATIVE_RECONNECT_ROUND_TRIPS,
            "chunk_ledger_assumption": "receiver inventory survives the outage",
        },
        "modes": {
            "native_https_retry": native,
            "terminating_deferred_proxy": proxy,
            "opaque_deferred_object": opaque,
        },
        "comparison": {
            "native_minus_durable_wire_bytes": (
                native["traffic"]["wire_bytes"] - opaque["traffic"]["wire_bytes"]
            ),
            "native_minus_durable_remote_completion_s": _round(
                native["timing"]["completion_s"] - opaque["timing"]["remote_completion_s"]
            ),
            "ordinary_https_preserves_application_tls_end_to_end": True,
            "terminating_proxy_preserves_application_tls_end_to_end": False,
            "opaque_object_preserves_payload_confidentiality_from_application_to_application": True,
        },
        "semantic_contract": {
            "accepted_pending": "persisted locally under a declared retention policy",
            "bp_delivered": "payload delivered to the destination BP application agent/adapter",
            "remote_completed": "remote application returned an idempotency-bound receipt",
            "failed": "not accepted durably and no remote completion is asserted",
            "expired": "accepted object reached its lifetime without remote completion",
        },
        "rejected_claims": [
            "An arbitrary synchronous HTTPS connection survives an indefinite partition transparently.",
            "A transport acknowledgement proves that the remote application processed a request.",
            "A BP delivery status report proves that the remote application processed a payload.",
            "BPv7 provides native BPv6-style custody transfer semantics.",
            "Deduplication and idempotency provide exactly-once execution.",
            "A terminating proxy preserves the original end-to-end TLS boundary.",
        ],
        "interpretation_boundary": [
            "The replay is deterministic and does not execute TCP, TLS, BPv7 or BPSec software.",
            "The 4 MB receiver chunk ledger is an application/object-layer assumption, not a BPv7 guarantee.",
            "The reconnect cost is a declared three-RTT approximation and not a packet trace.",
            "Status-report loss, bundle expiration, storage depletion and route selection are not simulated.",
            "Opaque payload confidentiality requires application-managed object encryption and key distribution.",
            "Remote processing receipts and idempotency semantics are application contracts outside BPv7.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/S005_disruption.json"))
    args = parser.parse_args(argv)
    rendered = json.dumps(build_disruption_study(), indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
