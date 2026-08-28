"""S024 time-sampled lunar relay ephemeris, contact, capacity and failure study."""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .io import write_json
from .lunar_orbits import MOON_GM_KM3_S2, MOON_RADIUS_KM, MOON_SIDEREAL_PERIOD_DAYS


STEP_S = 600
DURATION_S = 48 * 3600
MIN_ELEVATION_DEG = 10.0
ISL_LIMIT_KM = 14_000.0


@dataclass(frozen=True)
class Orbit:
    name: str
    altitude_km: float
    inclination_deg: float
    raan_deg: float
    phase_deg: float


SITES = {
    "south_pole": (0.0, -90.0),
    "far_side_equator": (180.0, 0.0),
    "near_side_equator": (0.0, 0.0),
}


def _dot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _sub(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return tuple(x - y for x, y in zip(a, b))  # type: ignore[return-value]


def _norm(a: tuple[float, float, float]) -> float:
    return math.sqrt(_dot(a, a))


def _site(longitude_deg: float, latitude_deg: float) -> tuple[float, float, float]:
    lon, lat = map(math.radians, (longitude_deg, latitude_deg))
    return (
        MOON_RADIUS_KM * math.cos(lat) * math.cos(lon),
        MOON_RADIUS_KM * math.cos(lat) * math.sin(lon),
        MOON_RADIUS_KM * math.sin(lat),
    )


def position(orbit: Orbit, elapsed_s: float) -> tuple[float, float, float]:
    """Propagate a circular Kepler orbit and rotate it into the Moon-fixed frame."""
    radius = MOON_RADIUS_KM + orbit.altitude_km
    mean_motion = math.sqrt(MOON_GM_KM3_S2 / radius**3)
    argument = math.radians(orbit.phase_deg) + mean_motion * elapsed_s
    inc, raan = map(math.radians, (orbit.inclination_deg, orbit.raan_deg))
    x_orbit, y_orbit = radius * math.cos(argument), radius * math.sin(argument)
    x = math.cos(raan) * x_orbit - math.sin(raan) * math.cos(inc) * y_orbit
    y = math.sin(raan) * x_orbit + math.cos(raan) * math.cos(inc) * y_orbit
    z = math.sin(inc) * y_orbit
    lunar_rotation = 2 * math.pi * elapsed_s / (MOON_SIDEREAL_PERIOD_DAYS * 86400)
    return (
        math.cos(lunar_rotation) * x + math.sin(lunar_rotation) * y,
        -math.sin(lunar_rotation) * x + math.cos(lunar_rotation) * y,
        z,
    )


def elevation_deg(site: tuple[float, float, float], satellite: tuple[float, float, float]) -> float:
    line = _sub(satellite, site)
    return math.degrees(math.asin(_dot(line, site) / (_norm(line) * _norm(site))))


def _segment_clears_moon(a: tuple[float, float, float], b: tuple[float, float, float]) -> bool:
    delta = _sub(b, a)
    fraction = max(0.0, min(1.0, -_dot(a, delta) / _dot(delta, delta)))
    closest = tuple(a[i] + fraction * delta[i] for i in range(3))
    return _norm(closest) > MOON_RADIUS_KM


def _earth_visible(satellite: tuple[float, float, float]) -> bool:
    # Earth is approximated as infinitely far on the +X Moon-fixed axis.
    if satellite[0] >= 0:
        return True
    return math.hypot(satellite[1], satellite[2]) > MOON_RADIUS_KM


def _reachable(start: int, earth_nodes: set[int], graph: dict[int, set[int]]) -> bool:
    pending, seen = [start], set()
    while pending:
        node = pending.pop()
        if node in earth_nodes:
            return True
        if node in seen:
            continue
        seen.add(node)
        pending.extend(graph[node] - seen)
    return False


def constellation(name: str, count: int, altitude_km: float, inclination_deg: float) -> tuple[Orbit, ...]:
    planes = 2 if count >= 6 else 1
    return tuple(
        Orbit(
            f"{name}-{index + 1}",
            altitude_km,
            inclination_deg if index % 2 == 0 else 180 - inclination_deg,
            360 * (index % planes) / planes,
            360 * (index // planes) / math.ceil(count / planes),
        )
        for index in range(count)
    )


def _summarise(samples: list[dict[str, float | bool]]) -> dict[str, Any]:
    available = [bool(row["available"]) for row in samples]
    runs, current = [], 0
    for state in available + [True]:
        if not state:
            current += STEP_S
        elif current:
            runs.append(current)
            current = 0
    return {
        "availability_fraction": round(sum(available) / len(available), 6),
        "maximum_blackout_s": max(runs, default=0),
        "delivered_terabits": round(sum(float(row["capacity_mbps"]) * STEP_S / 1e6 for row in samples), 6),
        "mean_visible_access_nodes": round(sum(float(row["visible_nodes"]) for row in samples) / len(samples), 6),
    }


def evaluate(orbits: tuple[Orbit, ...], failed_name: str | None = None) -> dict[str, Any]:
    site_rows: dict[str, list[dict[str, float | bool]]] = {name: [] for name in SITES}
    for elapsed in range(0, DURATION_S, STEP_S):
        active = [(orbit, position(orbit, elapsed)) for orbit in orbits if orbit.name != failed_name]
        earth_nodes = {i for i, (_, pos) in enumerate(active) if _earth_visible(pos)}
        graph = {i: set() for i in range(len(active))}
        for i in range(len(active)):
            for j in range(i + 1, len(active)):
                distance = _norm(_sub(active[i][1], active[j][1]))
                if distance <= ISL_LIMIT_KM and _segment_clears_moon(active[i][1], active[j][1]):
                    graph[i].add(j)
                    graph[j].add(i)
        weather_blocks_optical = (elapsed // 3600) % 8 in (0, 1)
        trunk_mbps = 50.0 if weather_blocks_optical else 500.0
        for site_name, coordinates in SITES.items():
            site = _site(*coordinates)
            visible = [i for i, (_, pos) in enumerate(active) if elevation_deg(site, pos) >= MIN_ELEVATION_DEG]
            routed = any(_reachable(i, earth_nodes, graph) for i in visible)
            site_rows[site_name].append({
                "available": routed,
                "visible_nodes": float(len(visible)),
                "capacity_mbps": min(100.0, trunk_mbps) if routed else 0.0,
            })
    return {name: _summarise(rows) for name, rows in site_rows.items()}


def build_ephemeris_study() -> dict[str, Any]:
    candidates = {
        "low_polar_8": constellation("lp", 8, 100.0, 88.0),
        "medium_inclined_8": constellation("mi", 8, 5_000.0, 70.0),
        "medium_inclined_12": constellation("mi12", 12, 5_000.0, 70.0),
    }
    cases = []
    for name, orbits in candidates.items():
        nominal = evaluate(orbits)
        single_failure = evaluate(orbits, orbits[0].name)
        cases.append({
            "constellation": name,
            "satellite_count": len(orbits),
            "orbit_elements": [orbit.__dict__ for orbit in orbits],
            "nominal": nominal,
            "single_satellite_failure": {"failed": orbits[0].name, "sites": single_failure},
        })
    checks = {
        "all_sites_and_failures_are_time_sampled": all(
            set(case["nominal"]) == set(SITES) and set(case["single_satellite_failure"]["sites"]) == set(SITES)
            for case in cases
        ),
        "more_medium_satellites_improve_worst_nominal_availability": min(
            row["availability_fraction"] for row in cases[2]["nominal"].values()
        ) >= min(row["availability_fraction"] for row in cases[1]["nominal"].values()),
        "failure_never_increases_delivered_capacity": all(
            case["single_satellite_failure"]["sites"][site]["delivered_terabits"] <= case["nominal"][site]["delivered_terabits"]
            for case in cases for site in SITES
        ),
        "far_side_requires_relay_path": any(
            case["nominal"]["far_side_equator"]["availability_fraction"] > 0 for case in cases
        ),
    }
    return {
        "study_id": "S024",
        "title": "Time-sampled lunar relay ephemeris, contact, capacity and failure envelope",
        "evidence_class": "SIMULATION",
        "inputs": {
            "duration_s": DURATION_S,
            "step_s": STEP_S,
            "minimum_elevation_deg": MIN_ELEVATION_DEG,
            "isl_limit_km": ISL_LIMIT_KM,
            "access_capacity_mbps": 100.0,
            "optical_earth_trunk_mbps": 500.0,
            "rf_fallback_mbps": 50.0,
            "weather_pattern": "two hours optical unavailable in each deterministic eight-hour block",
        },
        "cases": cases,
        "checks": checks,
        "interpretation_boundary": [
            "Positions are propagated circular two-body ephemerides sampled in a rotating Moon-fixed frame; this is not SPICE, n-body or flight-dynamics propagation.",
            "Earth is approximated as infinitely far on the Moon-fixed +X axis; lunar libration and Earth-station geometry are excluded.",
            "Terrain, antenna patterns, link acquisition time, interference, station diversity, queueing and protocol overhead are excluded.",
            "The deterministic weather pattern and capacities are sensitivity inputs, not forecasts or terminal specifications.",
            "The model compares candidate classes and failures; it does not select a production constellation.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/S024_ephemeris.json"))
    args = parser.parse_args(argv)
    write_json(args.output, build_ephemeris_study())
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
