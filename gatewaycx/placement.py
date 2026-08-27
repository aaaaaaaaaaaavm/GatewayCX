"""Exhaustive service-placement trade study for a bounded lunar regional Internet case."""

from __future__ import annotations

import argparse
import itertools
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


SITES = ("earth", "lunar_orbit", "lunar_surface")
SITE_RTT_S = {"earth": 2.564440764, "lunar_orbit": 0.12, "lunar_surface": 0.02}
SITE_BUDGETS = {
    "lunar_orbit": {"storage_gb": 25.0, "compute_units": 5},
    "lunar_surface": {"storage_gb": 100.0, "compute_units": 7},
}


@dataclass(frozen=True)
class Service:
    name: str
    replica_storage_gb: float
    compute_units: int
    requests_per_hour: int
    request_bytes: int
    response_bytes: int
    sequential_round_trips: int
    replication_bytes_per_hour: int
    essential_during_partition: bool


SERVICES = (
    Service("dns", 0.1, 1, 10_000, 100, 300, 1, 1_000_000, True),
    Service("identity", 5.0, 2, 1_000, 2_000, 5_000, 2, 50_000_000, True),
    Service("operations_api", 20.0, 4, 5_000, 2_000, 50_000, 2, 500_000_000, True),
    Service("static_content", 80.0, 2, 500, 1_000, 5_000_000, 1, 5_000_000_000, False),
    Service("science_archive", 15.0, 2, 20, 5_000, 500_000_000, 1, 100_000_000_000, False),
)


def _evaluate(placements: tuple[str, ...]) -> dict[str, Any] | None:
    usage = {
        site: {"storage_gb": 0.0, "compute_units": 0}
        for site in SITE_BUDGETS
    }
    for service, site in zip(SERVICES, placements, strict=True):
        if site in SITE_BUDGETS:
            usage[site]["storage_gb"] += service.replica_storage_gb
            usage[site]["compute_units"] += service.compute_units
    for site, budget in SITE_BUDGETS.items():
        if usage[site]["storage_gb"] > budget["storage_gb"]:
            return None
        if usage[site]["compute_units"] > budget["compute_units"]:
            return None

    latency_seconds_per_hour = 0.0
    cislunar_bytes_per_hour = 0
    essential_available = 0
    for service, site in zip(SERVICES, placements, strict=True):
        latency_seconds_per_hour += (
            service.requests_per_hour * service.sequential_round_trips * SITE_RTT_S[site]
        )
        if site == "earth":
            cislunar_bytes_per_hour += service.requests_per_hour * (
                service.request_bytes + service.response_bytes
            )
        else:
            cislunar_bytes_per_hour += service.replication_bytes_per_hour
            if service.essential_during_partition:
                essential_available += 1

    return {
        "placements": {
            service.name: site for service, site in zip(SERVICES, placements, strict=True)
        },
        "resource_use": {
            site: {
                "storage_gb": round(values["storage_gb"], 3),
                "compute_units": values["compute_units"],
            }
            for site, values in usage.items()
        },
        "interactive_delay_seconds_per_hour": round(latency_seconds_per_hour, 6),
        "cislunar_bytes_per_hour": cislunar_bytes_per_hour,
        "essential_services_available_during_partition": essential_available,
    }


def _sort_key(plan: dict[str, Any]) -> tuple[Any, ...]:
    return (
        plan["cislunar_bytes_per_hour"],
        plan["interactive_delay_seconds_per_hour"],
        tuple(plan["placements"].values()),
    )


def _pareto(plans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    frontier = []
    for candidate in plans:
        dominated = any(
            other["cislunar_bytes_per_hour"] <= candidate["cislunar_bytes_per_hour"]
            and other["interactive_delay_seconds_per_hour"]
            <= candidate["interactive_delay_seconds_per_hour"]
            and (
                other["cislunar_bytes_per_hour"] < candidate["cislunar_bytes_per_hour"]
                or other["interactive_delay_seconds_per_hour"]
                < candidate["interactive_delay_seconds_per_hour"]
            )
            for other in plans
            if other is not candidate
        )
        if not dominated:
            frontier.append(candidate)
    return sorted(frontier, key=_sort_key)


def build_placement_study() -> dict[str, Any]:
    evaluated = [
        plan
        for placements in itertools.product(SITES, repeat=len(SERVICES))
        if (plan := _evaluate(placements)) is not None
    ]
    required_essential = sum(service.essential_during_partition for service in SERVICES)
    resilient = [
        plan
        for plan in evaluated
        if plan["essential_services_available_during_partition"] == required_essential
    ]
    frontier = _pareto(resilient)
    earth_central = _evaluate(tuple("earth" for _ in SERVICES))
    assert earth_central is not None
    minimum_backbone = min(resilient, key=_sort_key)
    minimum_latency = min(
        resilient,
        key=lambda item: (
            item["interactive_delay_seconds_per_hour"],
            item["cislunar_bytes_per_hour"],
            tuple(item["placements"].values()),
        ),
    )
    return {
        "study_id": "S007",
        "title": "Constrained lunar service placement",
        "evidence_class": "MODEL",
        "inputs": {
            "sites": {site: {"round_trip_s": SITE_RTT_S[site]} for site in SITES},
            "lunar_site_budgets": SITE_BUDGETS,
            "services": [asdict(service) for service in SERVICES],
        },
        "search": {
            "candidate_combinations": len(SITES) ** len(SERVICES),
            "resource_feasible_combinations": len(evaluated),
            "partition_resilient_combinations": len(resilient),
            "pareto_frontier_size": len(frontier),
        },
        "earth_central_baseline": earth_central,
        "minimum_backbone_plan": minimum_backbone,
        "minimum_latency_plan": minimum_latency,
        "resilient_pareto_frontier": frontier,
        "interpretation_boundary": [
            "Demand, storage, compute, update and local-delay values are study assumptions.",
            "Storage and compute units do not constitute a lunar data-centre feasibility model.",
            "Cislunar bytes count user transfers for Earth placement or replica updates for lunar placement.",
            "The model omits consistency protocols, replica fan-out, failures, power and thermal limits.",
            "No weighted score selects a preferred plan; the Pareto frontier preserves the trade-off.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/S007_service_placement.json"))
    args = parser.parse_args(argv)
    rendered = json.dumps(build_placement_study(), indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
