"""Deterministic Earth–Moon capacity, window and outage-buffer envelope."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from .model import SPEED_OF_LIGHT_KM_S


MILES_TO_KM = 1.609344
DISTANCE_CASES = (
    ("closest_cited", 225_309 * MILES_TO_KM),
    ("mean", 384_400.0),
    ("farthest_cited", 251_903 * MILES_TO_KM),
)
CAPACITY_CASES = (
    (20.0, "LLCD demonstrated uplink maximum"),
    (100.0, "GatewayCX comparison rate"),
    (622.0, "LLCD demonstrated downlink maximum"),
    (1_000.0, "GatewayCX comparison rate"),
)
WINDOW_BYTES = (1 * 2**20, 16 * 2**20, 64 * 2**20, 256 * 2**20)
OUTAGE_SECONDS = (600, 3_600, 86_400)
ADMITTED_RATES_MBPS = (10.0, 100.0, 622.0)


def _rounded(value: float) -> float:
    return round(value, 6)


def build_capacity_envelope() -> dict[str, Any]:
    paths: list[dict[str, Any]] = []
    for distance_name, distance_km in DISTANCE_CASES:
        one_way_s = distance_km / SPEED_OF_LIGHT_KM_S
        round_trip_s = 2 * one_way_s
        rates: list[dict[str, Any]] = []
        for capacity_mbps, basis in CAPACITY_CASES:
            bdp_bytes = capacity_mbps * 1_000_000 * round_trip_s / 8
            rates.append(
                {
                    "capacity_mbps": capacity_mbps,
                    "basis": basis,
                    "bandwidth_delay_product_bytes": math.ceil(bdp_bytes),
                    "bandwidth_delay_product_megabytes": _rounded(bdp_bytes / 1_000_000),
                    "minimum_full_rate_window_bytes": math.ceil(bdp_bytes),
                    "one_gib_serialization_s": _rounded(2**30 * 8 / (capacity_mbps * 1_000_000)),
                    "window_limited_throughput_mbps": {
                        str(window): _rounded(
                            min(capacity_mbps, window * 8 / round_trip_s / 1_000_000)
                        )
                        for window in WINDOW_BYTES
                    },
                }
            )
        paths.append(
            {
                "distance_case": distance_name,
                "distance_km": _rounded(distance_km),
                "one_way_light_time_s": _rounded(one_way_s),
                "round_trip_light_time_s": _rounded(round_trip_s),
                "rates": rates,
            }
        )

    outage_buffers = []
    for admitted_rate_mbps in ADMITTED_RATES_MBPS:
        outage_buffers.append(
            {
                "admitted_rate_mbps": admitted_rate_mbps,
                "required_bytes": {
                    str(seconds): math.ceil(admitted_rate_mbps * 1_000_000 * seconds / 8)
                    for seconds in OUTAGE_SECONDS
                },
            }
        )

    return {
        "study_id": "S006",
        "title": "Earth–Moon bandwidth-delay and outage-buffer envelope",
        "evidence_class": "DERIVATION",
        "inputs": {
            "speed_of_light_km_s": SPEED_OF_LIGHT_KM_S,
            "distance_source": "NASA Space Place cited closest/farthest miles; NASA mean km",
            "window_bytes": list(WINDOW_BYTES),
            "outage_seconds": list(OUTAGE_SECONDS),
        },
        "paths": paths,
        "outage_buffers": outage_buffers,
        "interpretation_boundary": [
            "The LLCD rates are historical demonstration rates, not an operational service offer.",
            "Bandwidth-delay product is necessary in-flight state, not a complete transport design.",
            "The outage calculation assumes admitted traffic continues at a constant stated rate.",
            "Protocol overhead, loss, congestion, contacts and relay processing are excluded.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/S006_capacity_envelope.json"))
    args = parser.parse_args(argv)
    rendered = json.dumps(build_capacity_envelope(), indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
