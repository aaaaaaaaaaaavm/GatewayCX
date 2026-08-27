"""Content-addressed transfer and A/B activation model for disrupted lunar updates."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CHUNK_BYTES = 10_000_000
FIRST_CONTACT_BYTES = 250_000_000


@dataclass(frozen=True)
class Layer:
    name: str
    generation: str
    size_bytes: int


CURRENT_LAYERS = (
    Layer("base_os", "2026.08", 600_000_000),
    Layer("runtime", "4.1", 200_000_000),
    Layer("application", "7.0", 150_000_000),
    Layer("configuration", "41", 50_000_000),
)
TARGET_LAYERS = (
    Layer("base_os", "2026.08", 600_000_000),
    Layer("runtime", "4.2", 220_000_000),
    Layer("application", "7.1", 160_000_000),
    Layer("configuration", "42", 50_000_000),
)


def _chunks(layer: Layer) -> list[dict[str, Any]]:
    if layer.size_bytes % CHUNK_BYTES:
        raise ValueError(f"{layer.name} size must be divisible by the study chunk size")
    chunks = []
    for index in range(layer.size_bytes // CHUNK_BYTES):
        identity = f"{layer.name}:{layer.generation}:{index}:{CHUNK_BYTES}".encode()
        chunks.append(
            {
                "digest": "sha256:" + hashlib.sha256(identity).hexdigest(),
                "size_bytes": CHUNK_BYTES,
                "layer": layer.name,
                "index": index,
            }
        )
    return chunks


def _manifest(version: str, layers: tuple[Layer, ...]) -> dict[str, Any]:
    descriptors = [chunk for layer in layers for chunk in _chunks(layer)]
    canonical = json.dumps(descriptors, sort_keys=True, separators=(",", ":")).encode()
    return {
        "version": version,
        "total_bytes": sum(item["size_bytes"] for item in descriptors),
        "descriptor_count": len(descriptors),
        "manifest_digest": "sha256:" + hashlib.sha256(canonical).hexdigest(),
        "descriptors": descriptors,
    }


def _activation_events(health_passes: bool) -> list[dict[str, str]]:
    events = [
        {"event": "start", "active_slot": "A", "active_version": "v1", "slot_b": "empty"},
        {"event": "first_contact_interrupted", "active_slot": "A", "active_version": "v1", "slot_b": "incomplete"},
        {"event": "missing_chunks_resumed", "active_slot": "A", "active_version": "v1", "slot_b": "complete"},
        {"event": "manifest_and_chunks_verified", "active_slot": "A", "active_version": "v1", "slot_b": "verified"},
        {"event": "slot_b_trial_boot", "active_slot": "B", "active_version": "v2-unconfirmed", "slot_b": "bootable"},
    ]
    if health_passes:
        events.append(
            {"event": "health_check_passed", "active_slot": "B", "active_version": "v2", "slot_b": "successful"}
        )
    else:
        events.extend(
            [
                {"event": "health_check_failed", "active_slot": "B", "active_version": "v2-unconfirmed", "slot_b": "unbootable"},
                {"event": "automatic_rollback", "active_slot": "A", "active_version": "v1", "slot_b": "unbootable"},
            ]
        )
    return events


def build_update_study() -> dict[str, Any]:
    current = _manifest("v1", CURRENT_LAYERS)
    target = _manifest("v2", TARGET_LAYERS)
    current_digests = {item["digest"] for item in current["descriptors"]}
    missing = [item for item in target["descriptors"] if item["digest"] not in current_digests]
    missing_bytes = sum(item["size_bytes"] for item in missing)
    first_contact_delivered = min(FIRST_CONTACT_BYTES, missing_bytes)
    second_contact_delivered = missing_bytes - first_contact_delivered
    target_bytes = target["total_bytes"]
    return {
        "study_id": "S011",
        "title": "Interruption-safe content-addressed A/B update",
        "evidence_class": "MODEL",
        "inputs": {
            "chunk_bytes": CHUNK_BYTES,
            "first_contact_bytes": FIRST_CONTACT_BYTES,
            "current_layers": [layer.__dict__ for layer in CURRENT_LAYERS],
            "target_layers": [layer.__dict__ for layer in TARGET_LAYERS],
        },
        "manifests": {
            "current": {key: value for key, value in current.items() if key != "descriptors"},
            "target": {key: value for key, value in target.items() if key != "descriptors"},
        },
        "content_addressed_transfer": {
            "reused_chunks": target["descriptor_count"] - len(missing),
            "missing_chunks": len(missing),
            "wire_bytes": missing_bytes,
            "first_contact_delivered_bytes": first_contact_delivered,
            "second_contact_resumed_bytes": second_contact_delivered,
            "bytes_retransmitted_after_interruption": 0,
        },
        "comparisons": {
            "monolithic_restart_wire_bytes": FIRST_CONTACT_BYTES + target_bytes,
            "monolithic_range_resume_wire_bytes": target_bytes,
            "content_addressed_wire_bytes": missing_bytes,
            "saved_vs_monolithic_restart_bytes": FIRST_CONTACT_BYTES + target_bytes - missing_bytes,
            "saved_vs_monolithic_range_resume_bytes": target_bytes - missing_bytes,
        },
        "activation": {
            "successful_update": _activation_events(True),
            "failed_health_check": _activation_events(False),
            "required_pre_activation_checks": [
                "trusted manifest signature",
                "manifest version monotonicity",
                "target hardware identity",
                "metadata freshness or approved holdover",
                "every chunk length and digest",
                "complete compatible bundle",
            ],
        },
        "interpretation_boundary": [
            "Layer sizes, versions and contact bytes are synthetic assumptions.",
            "Digests identify model descriptors; no gigabyte payloads are generated or transferred.",
            "The model does not implement Uptane, OCI distribution, signatures or secure boot.",
            "A/B slots do not make shared databases or incompatible schema changes rollback-safe.",
            "Chunk reuse depends on stable boundaries and is reduced by per-recipient encryption.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/S011_update_delivery.json"))
    args = parser.parse_args(argv)
    rendered = json.dumps(build_update_study(), indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
