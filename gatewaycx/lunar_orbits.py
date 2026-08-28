"""S022 two-body envelope for lunar relay-shell and synchronous-orbit intuition."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

from .io import write_json


MOON_RADIUS_KM = 1_737.4
MOON_GM_KM3_S2 = 4_902.800066
MOON_SIDEREAL_PERIOD_DAYS = 27.321661
EARTH_MOON_SEMIMAJOR_KM = 384_400.0
EARTH_TO_MOON_MASS_RATIO = 81.30056
LIGHT_SPEED_KM_S = 299_792.458
SHELL_ALTITUDES_KM = (100.0, 1_000.0, 5_000.0, 8_000.0)


def circular_period_s(radius_km: float) -> float:
    if radius_km <= MOON_RADIUS_KM:
        raise ValueError("orbital radius must be above the reference lunar surface")
    return 2 * math.pi * math.sqrt(radius_km**3 / MOON_GM_KM3_S2)


def synchronous_radius_km(period_days: float = MOON_SIDEREAL_PERIOD_DAYS) -> float:
    if period_days <= 0:
        raise ValueError("period must be positive")
    period_s = period_days * 86_400
    return (MOON_GM_KM3_S2 * period_s**2 / (4 * math.pi**2)) ** (1 / 3)


def approximate_hill_radius_km() -> float:
    moon_to_earth_mass_ratio = 1 / EARTH_TO_MOON_MASS_RATIO
    return EARTH_MOON_SEMIMAJOR_KM * (moon_to_earth_mass_ratio / 3) ** (1 / 3)


def shell(altitude_km: float) -> dict[str, Any]:
    radius_km = MOON_RADIUS_KM + altitude_km
    horizon_angle_rad = math.acos(MOON_RADIUS_KM / radius_km)
    horizon_slant_km = math.sqrt(radius_km**2 - MOON_RADIUS_KM**2)
    return {
        "altitude_km": altitude_km,
        "orbital_period_h": round(circular_period_s(radius_km) / 3_600, 6),
        "surface_horizon_half_angle_deg": round(math.degrees(horizon_angle_rad), 6),
        "ideal_equatorial_satellites_min": math.ceil(math.pi / horizon_angle_rad),
        "horizon_slant_range_km": round(horizon_slant_km, 6),
        "horizon_one_way_light_time_ms": round(
            horizon_slant_km / LIGHT_SPEED_KM_S * 1_000, 6
        ),
    }


def build_lunar_orbit_envelope() -> dict[str, Any]:
    synchronous_radius = synchronous_radius_km()
    hill_radius = approximate_hill_radius_km()
    shells = [shell(altitude) for altitude in SHELL_ALTITUDES_KM]
    sync_altitude = synchronous_radius - MOON_RADIUS_KM
    checks = {
        "one_hundred_km_period_is_about_two_hours": 1.9
        < shells[0]["orbital_period_h"]
        < 2.1,
        "eight_thousand_km_period_is_about_one_earth_day": 23.0
        < shells[-1]["orbital_period_h"]
        < 25.0,
        "earth_day_orbit_is_not_lunar_stationary": abs(
            shells[-1]["orbital_period_h"] - MOON_SIDEREAL_PERIOD_DAYS * 24
        )
        > 600,
        "moon_synchronous_radius_exceeds_approximate_hill_radius": synchronous_radius
        > hill_radius,
        "higher_shell_reduces_ideal_equatorial_count": shells[-1][
            "ideal_equatorial_satellites_min"
        ]
        < shells[0]["ideal_equatorial_satellites_min"],
        "higher_shell_increases_surface_slant_range": shells[-1]["horizon_slant_range_km"]
        > shells[0]["horizon_slant_range_km"],
        "every_shell_remains_inside_approximate_hill_radius": all(
            MOON_RADIUS_KM + item["altitude_km"] < hill_radius for item in shells
        ),
    }
    return {
        "study_id": "S022",
        "title": "Lunar relay-shell and synchronous-orbit envelope",
        "evidence_class": "DERIVATION",
        "inputs": {
            "moon_radius_km": MOON_RADIUS_KM,
            "moon_gm_km3_s2": MOON_GM_KM3_S2,
            "moon_sidereal_period_days": MOON_SIDEREAL_PERIOD_DAYS,
            "earth_moon_semimajor_km": EARTH_MOON_SEMIMAJOR_KM,
            "earth_to_moon_mass_ratio": EARTH_TO_MOON_MASS_RATIO,
            "light_speed_km_s": LIGHT_SPEED_KM_S,
            "shell_altitudes_km": list(SHELL_ALTITUDES_KM),
        },
        "synchronous_case": {
            "two_body_synchronous_radius_km": round(synchronous_radius, 6),
            "two_body_synchronous_altitude_km": round(sync_altitude, 6),
            "approximate_hill_radius_km": round(hill_radius, 6),
            "synchronous_to_hill_ratio": round(synchronous_radius / hill_radius, 6),
            "inside_approximate_hill_sphere": synchronous_radius < hill_radius,
        },
        "relay_shells": shells,
        "checks": checks,
        "interpretation_boundary": [
            "The lunar stationary analogy requires a period equal to the Moon's sidereal rotation, not a 24-hour Earth day.",
            "The two-body synchronous radius lies beyond this study's approximate lunar Hill radius, so a simple circular lunar-GSO architecture is rejected as a baseline.",
            "Hill radius is an approximate stability screen, not a trajectory propagation or proof that every orbit inside it is stable.",
            "The satellite-count metric covers an ideal equatorial great circle to zero-degree elevation with no overlap; it is not global surface coverage and excludes poles, terrain, occultation, inclination, outages and capacity.",
            "Real cislunar relays may use elliptical, frozen, resonant, Lagrange-region or other multi-body trajectories that this two-body shell model does not evaluate.",
            "The shell comparison is an architecture envelope, not a constellation selection, link budget or mission design.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/S022_lunar_orbits.json"))
    args = parser.parse_args(argv)
    write_json(args.output, build_lunar_orbit_envelope())
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
