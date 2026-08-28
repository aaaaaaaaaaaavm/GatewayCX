"""S023 synthetic ground-network separation and optical-ISL bottleneck envelope."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .io import write_json


@dataclass(frozen=True)
class Demand:
    domain: str
    archetype: str
    service_units: float


DEMANDS = (
    Demand("deep_space", "distant_probe_return", 18.0),
    Demand("deep_space", "space_observatory_return", 20.0),
    Demand("deep_space", "solar_probe_return", 16.0),
    Demand("deep_space", "other_deep_space", 26.0),
    Demand("lunar", "crew_command_and_safety", 15.0),
    Demand("lunar", "lunar_science_return", 20.0),
    Demand("lunar", "settlement_internet_transit", 25.0),
)
SHARED_DEEP_SPACE_CAPACITY = 100.0
DEDICATED_LUNAR_CAPACITY = 70.0


def proportional_service(demands: tuple[Demand, ...], capacity: float) -> dict[str, Any]:
    offered = sum(item.service_units for item in demands)
    fraction = min(1.0, capacity / offered) if offered else 1.0
    rows = [
        {
            **asdict(item),
            "served_units": round(item.service_units * fraction, 6),
            "backlog_units": round(item.service_units * (1 - fraction), 6),
        }
        for item in demands
    ]
    served = sum(item["served_units"] for item in rows)
    return {
        "capacity_units": capacity,
        "offered_units": offered,
        "served_units": round(served, 6),
        "backlog_units": round(offered - served, 6),
        "utilisation": round(served / capacity, 6),
        "allocation_rule": "proportional synthetic service-unit allocation",
        "demands": rows,
    }


def pipeline(name: str, **stages: float) -> dict[str, Any]:
    limiting_stage = min(stages, key=stages.get)
    return {
        "name": name,
        "stage_capacity_units": stages,
        "delivered_units": min(stages.values()),
        "limiting_stage": limiting_stage,
    }


def _domain_served(case: dict[str, Any], domain: str) -> float:
    return round(
        sum(row["served_units"] for row in case["demands"] if row["domain"] == domain),
        6,
    )


def build_ground_offload_envelope() -> dict[str, Any]:
    deep = tuple(item for item in DEMANDS if item.domain == "deep_space")
    lunar = tuple(item for item in DEMANDS if item.domain == "lunar")
    shared = proportional_service(DEMANDS, SHARED_DEEP_SPACE_CAPACITY)
    separated_deep = proportional_service(deep, SHARED_DEEP_SPACE_CAPACITY)
    separated_lunar = proportional_service(lunar, DEDICATED_LUNAR_CAPACITY)
    shared_deep_served = _domain_served(shared, "deep_space")
    lunar_offered = sum(item.service_units for item in lunar)
    optical_isls_only = pipeline(
        "optical_isls_without_earth_egress",
        lunar_ingress=80.0,
        optical_inter_satellite=120.0,
        earth_trunk=0.0,
        ground_gateway=70.0,
    )
    trunk_limited = pipeline(
        "high_capacity_isls_with_constrained_earth_trunk",
        lunar_ingress=80.0,
        optical_inter_satellite=120.0,
        earth_trunk=50.0,
        ground_gateway=70.0,
    )
    balanced = pipeline(
        "isls_with_scaled_optical_rf_earth_egress",
        lunar_ingress=80.0,
        optical_inter_satellite=120.0,
        earth_trunk=100.0,
        ground_gateway=70.0,
    )
    checks = {
        "shared_case_is_oversubscribed": shared["backlog_units"] > 0,
        "separation_removes_lunar_demand_from_deep_space_pool": lunar_offered == 60.0,
        "deep_space_pool_clears_synthetic_demand_after_separation": separated_deep[
            "backlog_units"
        ]
        == 0,
        "lunar_pool_clears_synthetic_demand": separated_lunar["backlog_units"] == 0,
        "separation_increases_deep_space_service": separated_deep["served_units"]
        > shared_deep_served,
        "optical_isls_alone_do_not_create_earth_delivery": optical_isls_only[
            "delivered_units"
        ]
        == 0,
        "earth_trunk_limits_high_capacity_isls": trunk_limited["limiting_stage"]
        == "earth_trunk",
        "scaling_earth_trunk_moves_bottleneck_to_ground_gateway": balanced[
            "limiting_stage"
        ]
        == "ground_gateway",
    }
    return {
        "study_id": "S023",
        "title": "Deep-space protection and lunar ground-network offload envelope",
        "evidence_class": "MODEL",
        "inputs": {
            "demands": [asdict(item) for item in DEMANDS],
            "shared_deep_space_capacity_units": SHARED_DEEP_SPACE_CAPACITY,
            "dedicated_lunar_capacity_units": DEDICATED_LUNAR_CAPACITY,
            "unit_meaning": "synthetic scheduled-service unit; not an antenna-hour, byte or mission request",
        },
        "shared_pool": {
            **shared,
            "deep_space_served_units": shared_deep_served,
            "lunar_served_units": _domain_served(shared, "lunar"),
        },
        "separated_pools": {
            "deep_space": separated_deep,
            "lunar": separated_lunar,
            "lunar_units_removed_from_deep_space_pool": lunar_offered,
            "deep_space_service_gain_units": round(
                separated_deep["served_units"] - shared_deep_served, 6
            ),
        },
        "relay_pipeline_cases": [optical_isls_only, trunk_limited, balanced],
        "checks": checks,
        "interpretation_boundary": [
            "Every demand and capacity value is synthetic and dimensionless; none represents Voyager, JWST, Parker Solar Probe, Artemis, DSN or a provider schedule.",
            "The model demonstrates load separation, not actual antenna scheduling, mission priority, visibility or cost.",
            "A lunar relay network protects deep-space capacity by avoiding new lunar demand on that pool; it does not relay or replace support for distant missions by itself.",
            "Optical inter-satellite links redistribute traffic inside the relay network but deliver nothing to Earth without an Earth-facing trunk and compatible ground gateway.",
            "RF and optical egress, geographical ground diversity, weather, custody, storage and terrestrial backhaul must be sized as one pipeline.",
            "Actual DSN offload requires NASA and partner schedule data, mission constraints, regulatory authority and independently operated near-space capacity.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/S023_ground_offload.json"))
    args = parser.parse_args(argv)
    write_json(args.output, build_ground_offload_envelope())
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
