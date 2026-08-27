"""Deterministic RF/optical handover replay inspired by multipath and torque fill."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DURATION_S = 180.0
STEP_S = 0.5
OPTICAL_CAPACITY_MBPS = 500.0
RF_CAPACITY_MBPS = 20.0
OPTICAL_OUTAGE_START_S = 60.0
OPTICAL_RETURN_S = 120.0
OPTICAL_REACQUISITION_S = 15.0
RF_COLD_ACQUISITION_S = 20.0
WARM_SWITCH_S = 0.5
RF_KEEPALIVE_MBPS = 0.1
TRAFFIC = (
    {"name": "control", "offered_mbps": 0.5, "deferred": False},
    {"name": "interactive", "offered_mbps": 2.0, "deferred": False},
    {"name": "bulk", "offered_mbps": 100.0, "deferred": True},
)


def _bytes_for_rate(rate_mbps: float) -> int:
    return round(rate_mbps * 1_000_000 * STEP_S / 8)


def _active_paths(policy: str, time_s: float) -> dict[str, float]:
    optical_active = time_s < OPTICAL_OUTAGE_START_S or time_s >= (
        OPTICAL_RETURN_S + OPTICAL_REACQUISITION_S
    )
    if policy == "cold_failover":
        rf_active = (
            time_s >= OPTICAL_OUTAGE_START_S + RF_COLD_ACQUISITION_S
            and time_s < OPTICAL_RETURN_S + OPTICAL_REACQUISITION_S
        )
        return {
            "optical": OPTICAL_CAPACITY_MBPS if optical_active else 0.0,
            "rf": RF_CAPACITY_MBPS if rf_active else 0.0,
        }
    if policy == "warm_standby":
        rf_active = time_s >= OPTICAL_OUTAGE_START_S + WARM_SWITCH_S and not optical_active
        return {
            "optical": OPTICAL_CAPACITY_MBPS if optical_active else 0.0,
            "rf": RF_CAPACITY_MBPS if rf_active else 0.0,
        }
    if policy == "split_continuity":
        return {
            "optical": OPTICAL_CAPACITY_MBPS if optical_active else 0.0,
            "rf": RF_CAPACITY_MBPS,
        }
    raise ValueError(f"unknown policy {policy}")


def replay(policy: str) -> dict[str, Any]:
    offered = {item["name"]: 0 for item in TRAFFIC}
    delivered = {item["name"]: 0 for item in TRAFFIC}
    rejected = {item["name"]: 0 for item in TRAFFIC}
    queued = {item["name"]: 0 for item in TRAFFIC}
    max_queued = {item["name"]: 0 for item in TRAFFIC}
    interruption = {item["name"]: 0.0 for item in TRAFFIC if not item["deferred"]}
    max_interruption = interruption.copy()
    keepalive_bytes = 0
    path_active_seconds = {"optical": 0.0, "rf": 0.0}

    steps = round(DURATION_S / STEP_S)
    for step in range(steps):
        time_s = step * STEP_S
        paths = _active_paths(policy, time_s)
        for path, capacity in paths.items():
            if capacity > 0:
                path_active_seconds[path] += STEP_S

        if policy == "warm_standby" and paths["optical"] > 0:
            keepalive_bytes += _bytes_for_rate(RF_KEEPALIVE_MBPS)

        fresh = {item["name"]: _bytes_for_rate(item["offered_mbps"]) for item in TRAFFIC}
        for name, value in fresh.items():
            offered[name] += value

        allocations = {item["name"]: 0 for item in TRAFFIC}
        if policy == "split_continuity":
            rf_bytes = _bytes_for_rate(paths["rf"])
            for name in ("control", "interactive"):
                sent = min(fresh[name], rf_bytes)
                allocations[name] += sent
                rf_bytes -= sent
            bulk_capacity = rf_bytes + _bytes_for_rate(paths["optical"])
            allocations["bulk"] = min(fresh["bulk"] + queued["bulk"], bulk_capacity)
        else:
            total_capacity = _bytes_for_rate(paths["optical"] + paths["rf"])
            for item in TRAFFIC:
                name = item["name"]
                demand = fresh[name] + (queued[name] if item["deferred"] else 0)
                sent = min(demand, total_capacity)
                allocations[name] = sent
                total_capacity -= sent

        for item in TRAFFIC:
            name = item["name"]
            delivered[name] += allocations[name]
            if item["deferred"]:
                queued[name] = max(0, queued[name] + fresh[name] - allocations[name])
                max_queued[name] = max(max_queued[name], queued[name])
            else:
                missing = fresh[name] - allocations[name]
                rejected[name] += missing
                if missing:
                    interruption[name] += STEP_S
                    max_interruption[name] = max(max_interruption[name], interruption[name])
                else:
                    interruption[name] = 0.0

    return {
        "policy": policy,
        "offered_bytes": offered,
        "delivered_bytes": delivered,
        "rejected_bytes": rejected,
        "queued_at_end_bytes": queued,
        "maximum_queued_bytes": max_queued,
        "maximum_continuous_interruption_s": max_interruption,
        "rf_keepalive_bytes": keepalive_bytes,
        "path_active_seconds": path_active_seconds,
    }


def build_handover_study() -> dict[str, Any]:
    policies = [replay(name) for name in ("cold_failover", "warm_standby", "split_continuity")]
    return {
        "study_id": "S010",
        "title": "RF continuity around optical handover",
        "evidence_class": "MODEL",
        "inputs": {
            "duration_s": DURATION_S,
            "step_s": STEP_S,
            "optical_capacity_mbps": OPTICAL_CAPACITY_MBPS,
            "rf_capacity_mbps": RF_CAPACITY_MBPS,
            "optical_outage_start_s": OPTICAL_OUTAGE_START_S,
            "optical_return_s": OPTICAL_RETURN_S,
            "optical_reacquisition_s": OPTICAL_REACQUISITION_S,
            "rf_cold_acquisition_s": RF_COLD_ACQUISITION_S,
            "warm_switch_s": WARM_SWITCH_S,
            "rf_keepalive_mbps": RF_KEEPALIVE_MBPS,
            "traffic": list(TRAFFIC),
        },
        "policies": policies,
        "interpretation_boundary": [
            "All capacities, traffic rates and event times are synthetic assumptions.",
            "The optical and RF paths are assumed independent; shared failure domains are omitted.",
            "The model allocates byte budgets, not packets, congestion windows or RF spectrum.",
            "Warm standby consumes keepalive capacity but no terminal power is modelled.",
            "Multipath transport support and end-to-end session migration are not implemented.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/S010_handover.json"))
    args = parser.parse_args(argv)
    rendered = json.dumps(build_handover_study(), indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
