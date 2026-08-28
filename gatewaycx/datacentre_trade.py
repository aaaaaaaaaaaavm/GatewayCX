"""S026 lunar data-centre power, thermal, radiation, mass and storage trade."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

from .io import write_json


STEFAN_BOLTZMANN = 5.670374419e-8
CONFIGURATIONS = (
    {"name": "surface_shielded", "compute_kw": 20.0, "storage_pb": 2.0, "network_kw": 3.0, "overhead_factor": 1.45, "radiator_k": 330.0, "radiator_emissivity": 0.88, "compute_kg_per_kw": 22.0, "storage_kg_per_pb": 180.0, "shielding_kg": 6_000.0, "radiation_factor": 0.20},
    {"name": "orbital_service_node", "compute_kw": 8.0, "storage_pb": 0.5, "network_kw": 2.0, "overhead_factor": 1.35, "radiator_k": 345.0, "radiator_emissivity": 0.88, "compute_kg_per_kw": 18.0, "storage_kg_per_pb": 150.0, "shielding_kg": 900.0, "radiation_factor": 1.0},
    {"name": "hybrid_surface_orbit", "compute_kw": 14.0, "storage_pb": 1.5, "network_kw": 4.0, "overhead_factor": 1.40, "radiator_k": 335.0, "radiator_emissivity": 0.88, "compute_kg_per_kw": 20.0, "storage_kg_per_pb": 170.0, "shielding_kg": 3_500.0, "radiation_factor": 0.45},
)


def evaluate(config: dict[str, float | str]) -> dict[str, Any]:
    it_kw = float(config["compute_kw"]) + float(config["network_kw"]) + 0.8 * float(config["storage_pb"])
    facility_kw = it_kw * float(config["overhead_factor"])
    heat_w = facility_kw * 1000
    radiator_flux = float(config["radiator_emissivity"]) * STEFAN_BOLTZMANN * (float(config["radiator_k"])**4 - 100.0**4)
    radiator_area = heat_w / radiator_flux
    radiator_kg = radiator_area * 8.0
    dry_mass = (float(config["compute_kw"]) * float(config["compute_kg_per_kw"]) +
                float(config["storage_pb"]) * float(config["storage_kg_per_pb"]) +
                float(config["shielding_kg"]) + radiator_kg)
    raw_upsets_year = 1000 * float(config["radiation_factor"])
    residual_upsets_year = raw_upsets_year * 1e-4  # ECC + scrubbing architecture target.
    storage_j_per_gb_year = facility_kw * 1000 * 365.25 * 86400 / (float(config["storage_pb"]) * 1e6)
    return {
        "it_power_kw": round(it_kw, 6), "facility_power_kw": round(facility_kw, 6),
        "radiator_area_m2": round(radiator_area, 6), "radiator_mass_kg": round(radiator_kg, 6),
        "estimated_dry_mass_kg": round(dry_mass, 6), "raw_upsets_per_year": raw_upsets_year,
        "residual_upsets_per_year_target": residual_upsets_year,
        "storage_energy_j_per_gb_year": round(storage_j_per_gb_year, 6),
    }


def build_datacentre_trade() -> dict[str, Any]:
    cases = [{"configuration": config["name"], "inputs": config, "outputs": evaluate(config)} for config in CONFIGURATIONS]
    checks = {
        "every_case_models_all_requested_domains": all(set(row["outputs"]) >= {"facility_power_kw", "radiator_area_m2", "estimated_dry_mass_kg", "residual_upsets_per_year_target", "storage_energy_j_per_gb_year"} for row in cases),
        "shielded_surface_has_lower_residual_upset_target_than_orbit": cases[0]["outputs"]["residual_upsets_per_year_target"] < cases[1]["outputs"]["residual_upsets_per_year_target"],
        "every_radiator_and_mass_is_positive": all(row["outputs"]["radiator_area_m2"] > 0 and row["outputs"]["estimated_dry_mass_kg"] > 0 for row in cases),
    }
    return {
        "study_id": "S026", "title": "Lunar regional data-centre physical trade", "evidence_class": "MODEL", "configurations": cases, "checks": checks,
        "interpretation_boundary": [
            "Inputs are architecture classes, not qualified components, launch quotes or a settlement demand forecast.",
            "Radiator sizing is steady-state black-body rejection to a 100 K sink and excludes view factors, dust, sunlight, deployment and fluid loops.",
            "Radiation figures are comparative upset-rate assumptions with an ECC/scrubbing target, not a radiation transport analysis or parts qualification.",
            "Mass includes compute, storage, radiator and a shielding allowance but excludes structure, power generation, batteries, cabling, spares, landing and maintenance.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--output", type=Path, default=Path("results/S026_datacentre_trade.json")); args = parser.parse_args(argv)
    write_json(args.output, build_datacentre_trade()); print(f"wrote {args.output}"); return 0


if __name__ == "__main__": raise SystemExit(main())
