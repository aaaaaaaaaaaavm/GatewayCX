"""S025 class-based RF/optical link budgets and fallback sensitivities."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

from .io import write_json


C_M_S = 299_792_458.0
PLANCK_J_S = 6.62607015e-34


RF_CLASSES = (
    {"name": "surface_s_band", "frequency_ghz": 2.25, "range_km": 2_000.0, "tx_power_dbw": 10.0, "tx_gain_dbi": 8.0, "rx_gt_db_k": -1.0, "loss_db": 3.0, "rate_mbps": 1.0, "required_ebn0_db": 4.0},
    {"name": "dwe_ka_band", "frequency_ghz": 32.0, "range_km": 384_400.0, "tx_power_dbw": 20.0, "tx_gain_dbi": 45.0, "rx_gt_db_k": 35.0, "loss_db": 4.0, "rate_mbps": 100.0, "required_ebn0_db": 5.0},
)


OPTICAL_CLASSES = (
    {"name": "lunar_crosslink", "range_km": 10_000.0, "wavelength_nm": 1550.0, "tx_power_w": 2.0, "tx_aperture_m": 0.08, "rx_aperture_m": 0.20, "efficiency": 0.25, "divergence_urad": 25.0, "rate_mbps": 500.0, "required_photons_per_bit": 100.0},
    {"name": "lunar_earth_trunk", "range_km": 384_400.0, "wavelength_nm": 1550.0, "tx_power_w": 5.0, "tx_aperture_m": 0.20, "rx_aperture_m": 1.0, "efficiency": 0.20, "divergence_urad": 20.0, "rate_mbps": 1_000.0, "required_photons_per_bit": 100.0},
)


def rf_budget(profile: dict[str, float | str], extra_loss_db: float = 0.0) -> dict[str, Any]:
    frequency_hz = float(profile["frequency_ghz"]) * 1e9
    range_m = float(profile["range_km"]) * 1e3
    fspl_db = 20 * math.log10(4 * math.pi * range_m * frequency_hz / C_M_S)
    cn0_db_hz = (float(profile["tx_power_dbw"]) + float(profile["tx_gain_dbi"]) +
                 float(profile["rx_gt_db_k"]) - fspl_db - float(profile["loss_db"]) -
                 extra_loss_db + 228.6)
    ebn0_db = cn0_db_hz - 10 * math.log10(float(profile["rate_mbps"]) * 1e6)
    return {
        "free_space_path_loss_db": round(fspl_db, 6),
        "cn0_db_hz": round(cn0_db_hz, 6),
        "ebn0_db": round(ebn0_db, 6),
        "margin_db": round(ebn0_db - float(profile["required_ebn0_db"]), 6),
        "extra_loss_db": extra_loss_db,
    }


def optical_budget(profile: dict[str, float | str], pointing_error_urad: float) -> dict[str, Any]:
    wavelength = float(profile["wavelength_nm"]) * 1e-9
    range_m = float(profile["range_km"]) * 1e3
    divergence = float(profile["divergence_urad"]) * 1e-6
    spot_radius = divergence * range_m
    capture = min(1.0, (float(profile["rx_aperture_m"]) / (2 * spot_radius)) ** 2)
    pointing_ratio = pointing_error_urad / float(profile["divergence_urad"])
    pointing_factor = math.exp(-2 * pointing_ratio**2)
    received_w = float(profile["tx_power_w"]) * float(profile["efficiency"]) * capture * pointing_factor
    photon_energy = PLANCK_J_S * C_M_S / wavelength
    photons_per_bit = received_w / photon_energy / (float(profile["rate_mbps"]) * 1e6)
    return {
        "spot_radius_m": round(spot_radius, 6),
        "capture_fraction": round(capture, 12),
        "pointing_loss_db": round(-10 * math.log10(pointing_factor), 6),
        "received_power_w": received_w,
        "photons_per_bit": round(photons_per_bit, 6),
        "margin_db": round(10 * math.log10(photons_per_bit / float(profile["required_photons_per_bit"])), 6),
        "pointing_error_urad": pointing_error_urad,
    }


def acquisition_yield(
    acquisition_s: float,
    contact_s: float = 600.0,
    optical_rate_mbps: float = 1_000.0,
    rf_fallback_mbps: float = 100.0,
    optical_availability: float = 0.9,
) -> dict[str, Any]:
    """Bound contact yield after terminal acquisition, with RF during optical outage."""
    usable_s = max(0.0, contact_s - acquisition_s)
    hybrid_mbits = usable_s * (
        optical_rate_mbps * optical_availability
        + rf_fallback_mbps * (1.0 - optical_availability)
    )
    return {
        "contact_s": contact_s,
        "acquisition_s": acquisition_s,
        "usable_s": usable_s,
        "usable_contact_fraction": round(usable_s / contact_s, 6),
        "hybrid_contact_yield_mbits": round(hybrid_mbits, 6),
    }


def build_link_budget_study() -> dict[str, Any]:
    rf_cases = []
    for profile in RF_CLASSES:
        rf_cases.append({
            "class": profile["name"], "profile": profile,
            "clear": rf_budget(profile),
            "degraded": rf_budget(profile, 6.0),
        })
    optical_cases = []
    for profile in OPTICAL_CLASSES:
        optical_cases.append({
            "class": profile["name"], "profile": profile,
            "pointing_sensitivity": [optical_budget(profile, error) for error in (0.0, 5.0, 10.0, 20.0)],
        })
    weather = [
        {"optical_availability": availability, "optical_mbps": 1000.0 * availability, "rf_fallback_mbps": 100.0, "hybrid_average_mbps": 1000.0 * availability + 100.0 * (1 - availability)}
        for availability in (0.5, 0.8, 0.95, 0.99)
    ]
    acquisition = [acquisition_yield(seconds) for seconds in (5.0, 20.0, 60.0, 180.0)]
    checks = {
        "rf_degradation_reduces_margin_by_six_db": all(round(row["clear"]["margin_db"] - row["degraded"]["margin_db"], 6) == 6.0 for row in rf_cases),
        "optical_pointing_error_reduces_margin": all(row["pointing_sensitivity"][0]["margin_db"] > row["pointing_sensitivity"][-1]["margin_db"] for row in optical_cases),
        "rf_fallback_preserves_nonzero_weather_blocked_service": all(row["hybrid_average_mbps"] > row["optical_mbps"] for row in weather),
        "higher_optical_availability_increases_hybrid_capacity": all(a["hybrid_average_mbps"] < b["hybrid_average_mbps"] for a, b in zip(weather, weather[1:])),
        "longer_acquisition_reduces_contact_yield": all(a["hybrid_contact_yield_mbits"] > b["hybrid_contact_yield_mbits"] for a, b in zip(acquisition, acquisition[1:])),
        "rf_fallback_preserves_acquired_contact_yield": all(row["hybrid_contact_yield_mbits"] > 0 for row in acquisition),
    }
    return {
        "study_id": "S025", "title": "Class-based RF and optical link-budget sensitivity", "evidence_class": "DERIVATION + MODEL",
        "rf_classes": rf_cases, "optical_classes": optical_cases, "weather_and_fallback": weather,
        "acquisition_and_fallback": acquisition, "checks": checks,
        "interpretation_boundary": [
            "Every terminal parameter is a declared architecture class, not vendor data or measured performance.",
            "RF uses free-space loss and a simplified C/N0-to-Eb/N0 budget; coding implementation loss, interference, polarisation dynamics and regulatory constraints require separate inputs.",
            "Optical capture uses a far-field spot approximation and Gaussian pointing penalty; acquisition is a declared elapsed-time sensitivity, not a terminal-control simulation.",
            "Atmospheric turbulence, scintillation and cloud correlation are not resolved.",
            "A positive paper margin is not availability, acquisition success, hardware qualification or a service guarantee.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/S025_link_budgets.json"))
    args = parser.parse_args(argv); write_json(args.output, build_link_budget_study()); print(f"wrote {args.output}"); return 0


if __name__ == "__main__": raise SystemExit(main())
