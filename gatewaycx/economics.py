"""S027 cost per delivered and retained bit sensitivity model."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from .io import write_json


SECONDS_YEAR = 365.25 * 86400


def annualised_capex(capex_usd: float, years: int, discount_rate: float) -> float:
    factor = discount_rate * (1 + discount_rate) ** years / ((1 + discount_rate) ** years - 1)
    return capex_usd * factor


def case(utilisation: float, optical_availability: float) -> dict[str, Any]:
    capex_usd, annual_opex_usd = 900_000_000.0, 85_000_000.0
    annual_cost = annualised_capex(capex_usd, 10, 0.08) + annual_opex_usd
    optical_bps, rf_bps = 1e9, 100e6
    offered_bps = optical_bps * utilisation
    available_bps = optical_bps * optical_availability + rf_bps * (1 - optical_availability)
    delivered_bps = min(offered_bps, available_bps) * 0.88
    delivered_bits = delivered_bps * SECONDS_YEAR
    retained_bits = 2e15 * 8 * 3  # 2 PB, three protected copies.
    storage_annual_usd = annualised_capex(120_000_000.0, 7, 0.08) + 12_000_000.0
    return {
        "utilisation": utilisation, "optical_availability": optical_availability,
        "delivered_bits_year": round(delivered_bits),
        "cost_per_delivered_bit_usd": annual_cost / delivered_bits,
        "retained_bits": retained_bits,
        "cost_per_retained_bit_year_usd": storage_annual_usd / retained_bits,
        "annual_network_cost_usd": round(annual_cost, 2), "annual_storage_cost_usd": round(storage_annual_usd, 2),
    }


def build_economics_study() -> dict[str, Any]:
    cases = [case(utilisation, availability) for utilisation in (0.1, 0.4, 0.8) for availability in (0.7, 0.9, 0.99)]
    low, high = case(0.1, 0.9), case(0.8, 0.9)
    checks = {
        "every_case_has_delivered_and_retained_bit_cost": all(row["cost_per_delivered_bit_usd"] > 0 and row["cost_per_retained_bit_year_usd"] > 0 for row in cases),
        "utilisation_spreads_fixed_cost": high["cost_per_delivered_bit_usd"] < low["cost_per_delivered_bit_usd"],
        "rf_fallback_keeps_available_capacity_nonzero": all(row["delivered_bits_year"] > 0 for row in cases),
    }
    return {
        "study_id": "S027", "title": "Cost per delivered and retained bit sensitivity", "evidence_class": "MODEL", "cases": cases, "checks": checks,
        "input_contract": {"network_capex_usd": 900_000_000, "annual_opex_usd": 85_000_000, "economic_life_years": 10, "discount_rate": 0.08, "optical_capacity_bps": 1_000_000_000, "rf_fallback_bps": 100_000_000, "delivery_efficiency": 0.88, "retained_storage_pb": 2, "protected_copies": 3},
        "interpretation_boundary": [
            "All cost, utilisation, availability and demand inputs are synthetic architecture sensitivities, not supplier quotes, financing terms or a market forecast.",
            "Cost per delivered bit annualises a shared network and excludes price discrimination, taxes, spectrum, insurance, launch schedule risk and demand growth.",
            "Cost per retained bit-year covers a synthetic protected storage pool; it is not a customer price and does not include the full data-centre mass model.",
            "The model is executable so real partner, terminal and launch inputs can replace assumptions without changing the accounting equation.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--output", type=Path, default=Path("results/S027_economics.json")); args = parser.parse_args(argv)
    write_json(args.output, build_economics_study()); print(f"wrote {args.output}"); return 0


if __name__ == "__main__": raise SystemExit(main())
