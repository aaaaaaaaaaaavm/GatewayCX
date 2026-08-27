"""Dependency and fault-injection model for lunar network islanding and black start."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ESSENTIAL_SERVICES = (
    "holdover_time",
    "local_trust_root",
    "local_name_root",
    "local_identity_verifier",
    "local_route_controller",
    "durable_queue",
    "operations_api",
)

ISLANDABLE_DEPENDENCIES = {
    "holdover_time": (),
    "local_trust_root": (),
    "local_name_root": ("holdover_time",),
    "local_identity_verifier": ("holdover_time", "local_trust_root"),
    "local_route_controller": ("holdover_time",),
    "durable_queue": ("local_route_controller",),
    "operations_api": ("local_name_root", "local_identity_verifier", "durable_queue"),
}

EARTH_COUPLED_DEPENDENCIES = {
    **ISLANDABLE_DEPENDENCIES,
    "local_name_root": ("earth_dns",),
    "local_identity_verifier": ("holdover_time", "earth_identity"),
    "local_route_controller": ("holdover_time", "earth_contact_control"),
}

EARTH_SERVICES = ("earth_dns", "earth_identity", "earth_contact_control")


def _start(
    dependencies: dict[str, tuple[str, ...]],
    available_external: set[str],
    failed_local: set[str] | None = None,
) -> dict[str, Any]:
    failed = failed_local or set()
    running = set(available_external)
    stages: list[list[str]] = []
    while True:
        ready = sorted(
            service
            for service, required in dependencies.items()
            if service not in running
            and service not in failed
            and all(dependency in running for dependency in required)
        )
        if not ready:
            break
        stages.append(ready)
        running.update(ready)
    started = [service for service in ESSENTIAL_SERVICES if service in running]
    blocked = {
        service: [dependency for dependency in dependencies[service] if dependency not in running]
        for service in ESSENTIAL_SERVICES
        if service not in running and service not in failed
    }
    return {
        "stages": stages,
        "started_essential": started,
        "started_essential_count": len(started),
        "failed_local": sorted(failed),
        "blocked": blocked,
    }


def build_black_start_study() -> dict[str, Any]:
    no_earth: set[str] = set()
    earth_up = set(EARTH_SERVICES)
    earth_coupled_partition = _start(EARTH_COUPLED_DEPENDENCIES, no_earth)
    earth_coupled_recovery = _start(EARTH_COUPLED_DEPENDENCIES, earth_up)
    islandable_partition = _start(ISLANDABLE_DEPENDENCIES, no_earth)
    fault_injection = {
        failed: _start(ISLANDABLE_DEPENDENCIES, no_earth, {failed})
        for failed in ESSENTIAL_SERVICES
    }
    ranked_faults = sorted(
        (
            {
                "failed_service": failed,
                "remaining_essential_count": result["started_essential_count"],
                "blocked_or_failed_count": len(ESSENTIAL_SERVICES) - result["started_essential_count"],
            }
            for failed, result in fault_injection.items()
        ),
        key=lambda item: (item["remaining_essential_count"], item["failed_service"]),
    )
    return {
        "study_id": "S013",
        "title": "Lunar network islanding and black-start dependency model",
        "evidence_class": "MODEL",
        "inputs": {
            "essential_services": list(ESSENTIAL_SERVICES),
            "earth_services": list(EARTH_SERVICES),
            "islandable_dependencies": {
                service: list(required)
                for service, required in ISLANDABLE_DEPENDENCIES.items()
            },
            "earth_coupled_dependencies": {
                service: list(required)
                for service, required in EARTH_COUPLED_DEPENDENCIES.items()
            },
        },
        "scenarios": {
            "earth_coupled_during_partition": earth_coupled_partition,
            "earth_coupled_after_earth_recovery": earth_coupled_recovery,
            "islandable_during_partition": islandable_partition,
        },
        "single_local_faults": fault_injection,
        "fault_ranking": ranked_faults,
        "interpretation_boundary": [
            "The graph models logical start dependencies, not electrical power or hardware boot.",
            "A running node means dependencies are present; it does not prove correctness, security or capacity.",
            "Service names and dependency edges are architecture assumptions for fault discovery.",
            "Holdover duration, clock error, trust freshness and key compromise are not modelled.",
            "Single faults do not cover correlated failure, Byzantine behaviour or recovery ordering after state divergence.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/S013_black_start.json"))
    args = parser.parse_args(argv)
    rendered = json.dumps(build_black_start_study(), indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
