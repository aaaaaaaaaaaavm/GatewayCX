"""Deterministic contact-capacity admission comparison for GatewayCX traffic classes."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TrafficDemand:
    traffic_class: str
    name: str
    offered_bytes: int
    deferred_allowed: bool


TRAFFIC = (
    TrafficDemand("GX-T0", "crew_safety", 500_000_000, False),
    TrafficDemand("GX-T1", "command_control_navigation", 1_000_000_000, False),
    TrafficDemand("GX-T2", "crew_interactive", 4_000_000_000, False),
    TrafficDemand("GX-T3", "settlement_operations", 10_000_000_000, True),
    TrafficDemand("GX-T4", "science_return", 30_000_000_000, True),
    TrafficDemand("GX-T5", "background_replication", 100_000_000_000, True),
)

CLASS_ORDER = tuple(item.traffic_class for item in TRAFFIC)
MINIMUM_SHARES = {
    "GX-T0": 0.25,
    "GX-T1": 0.20,
    "GX-T2": 0.15,
    "GX-T3": 0.15,
    "GX-T4": 0.20,
    "GX-T5": 0.05,
}
CONTACT_CASES = {
    "nominal_optical_plus_rf": (
        {"bearer": "optical", "capacity_mbps": 500.0, "duration_s": 600},
        {"bearer": "rf", "capacity_mbps": 100.0, "duration_s": 600},
    ),
    "rf_fallback_only": (
        {"bearer": "optical", "capacity_mbps": 0.0, "duration_s": 600},
        {"bearer": "rf", "capacity_mbps": 100.0, "duration_s": 600},
    ),
}


def _capacity_bytes(contacts: tuple[dict[str, Any], ...]) -> int:
    return int(sum(item["capacity_mbps"] * 1_000_000 * item["duration_s"] / 8 for item in contacts))


def _finish(delivered: dict[str, int], capacity_bytes: int) -> dict[str, Any]:
    rows = []
    for demand in TRAFFIC:
        sent = delivered[demand.traffic_class]
        remainder = demand.offered_bytes - sent
        rows.append(
            {
                **asdict(demand),
                "delivered_bytes": sent,
                "queued_bytes": remainder if demand.deferred_allowed else 0,
                "rejected_bytes": remainder if not demand.deferred_allowed else 0,
                "status": (
                    "delivered"
                    if remainder == 0
                    else "partially_delivered_and_queued"
                    if demand.deferred_allowed and sent > 0
                    else "queued"
                    if demand.deferred_allowed
                    else "partially_delivered_and_rejected"
                    if sent > 0
                    else "rejected"
                ),
            }
        )
    used = sum(delivered.values())
    return {
        "capacity_bytes": capacity_bytes,
        "delivered_bytes": used,
        "unused_bytes": capacity_bytes - used,
        "queued_bytes": sum(item["queued_bytes"] for item in rows),
        "rejected_bytes": sum(item["rejected_bytes"] for item in rows),
        "classes": rows,
    }


def strict_priority(capacity_bytes: int) -> dict[str, Any]:
    remaining = capacity_bytes
    delivered: dict[str, int] = {}
    for demand in TRAFFIC:
        sent = min(demand.offered_bytes, remaining)
        delivered[demand.traffic_class] = sent
        remaining -= sent
    return _finish(delivered, capacity_bytes)


def bounded_priority(capacity_bytes: int) -> dict[str, Any]:
    delivered = {traffic_class: 0 for traffic_class in CLASS_ORDER}
    # First pass protects a declared floor for every active class.
    for demand in TRAFFIC:
        floor = int(capacity_bytes * MINIMUM_SHARES[demand.traffic_class])
        delivered[demand.traffic_class] = min(demand.offered_bytes, floor)
    # Unused floors are borrowed in priority order; no class loses its first-pass allocation.
    remaining = capacity_bytes - sum(delivered.values())
    for demand in TRAFFIC:
        outstanding = demand.offered_bytes - delivered[demand.traffic_class]
        extra = min(outstanding, remaining)
        delivered[demand.traffic_class] += extra
        remaining -= extra
    return _finish(delivered, capacity_bytes)


def build_admission_study() -> dict[str, Any]:
    cases = {}
    for name, contacts in CONTACT_CASES.items():
        capacity = _capacity_bytes(contacts)
        cases[name] = {
            "contacts": list(contacts),
            "strict_priority": strict_priority(capacity),
            "bounded_priority": bounded_priority(capacity),
        }
    return {
        "study_id": "S009",
        "title": "Contact-aware admission and anti-starvation comparison",
        "evidence_class": "MODEL",
        "inputs": {
            "traffic": [asdict(item) for item in TRAFFIC],
            "bounded_priority_minimum_shares": MINIMUM_SHARES,
        },
        "cases": cases,
        "interpretation_boundary": [
            "Traffic volumes, contacts, capacities and minimum shares are synthetic assumptions.",
            "This is byte-budget admission, not antenna, orbital or packet scheduling.",
            "Rejected interactive bytes represent unmet service, not silent loss.",
            "Queued bytes require the durable storage declared by the active bearer and gateway.",
            "Safety classes and shares require hazard analysis before any operational use.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/S009_admission.json"))
    args = parser.parse_args(argv)
    rendered = json.dumps(build_admission_study(), indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
