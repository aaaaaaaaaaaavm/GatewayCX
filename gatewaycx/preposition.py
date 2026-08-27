"""Bounded predictive prepositioning study with explicit forecast error cost."""

from __future__ import annotations

import argparse
import itertools
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


EARTH_MOON_RTT_S = 2.564440764
CACHE_BUDGET_BYTES = 900_000_000
UNUSED_COST_S_PER_100_MB = 0.75


@dataclass(frozen=True)
class Content:
    content_id: str
    size_bytes: int
    requests_if_needed: int
    actual_requested: bool
    essential: bool
    popularity_probability: float
    calibrated_probability: float
    overconfident_probability: float


CONTENTS = (
    Content("emergency_maps", 180_000_000, 8, True, True, 0.97, 0.98, 0.99),
    Content("medical_reference", 120_000_000, 6, True, True, 0.95, 0.97, 0.99),
    Content("software_patch", 250_000_000, 4, True, False, 0.65, 0.80, 0.70),
    Content("crew_training", 200_000_000, 3, True, False, 0.60, 0.70, 0.45),
    Content("entertainment_bundle", 450_000_000, 5, False, False, 0.40, 0.10, 0.98),
    Content("science_catalog", 300_000_000, 2, False, False, 0.35, 0.25, 0.85),
    Content("family_messages", 100_000_000, 6, True, False, 0.75, 0.65, 0.60),
    Content("earth_news", 150_000_000, 3, False, False, 0.45, 0.30, 0.75),
)


def _forecast(content: Content, policy: str) -> float:
    if policy == "essential_only":
        return 0.0
    if policy == "popularity_only":
        return content.popularity_probability
    if policy == "calibrated_forecast":
        return content.calibrated_probability
    if policy == "overconfident_forecast":
        return content.overconfident_probability
    if policy == "oracle":
        return float(content.actual_requested)
    raise ValueError(f"unknown policy: {policy}")


def _expected_utility(content: Content, probability: float) -> float:
    expected_avoided_delay = probability * content.requests_if_needed * EARTH_MOON_RTT_S
    unused_cost = (
        (1.0 - probability)
        * (content.size_bytes / 100_000_000)
        * UNUSED_COST_S_PER_100_MB
    )
    return expected_avoided_delay - unused_cost


def _select(policy: str) -> tuple[Content, ...]:
    essential = tuple(item for item in CONTENTS if item.essential)
    optional = tuple(item for item in CONTENTS if not item.essential)
    if sum(item.size_bytes for item in essential) > CACHE_BUDGET_BYTES:
        raise ValueError("essential reservation exceeds the cache budget")
    if policy == "essential_only":
        return essential

    feasible: list[tuple[float, int, tuple[str, ...], tuple[Content, ...]]] = []
    for count in range(len(optional) + 1):
        for subset in itertools.combinations(optional, count):
            selected = essential + subset
            total_bytes = sum(item.size_bytes for item in selected)
            if total_bytes > CACHE_BUDGET_BYTES:
                continue
            utility = sum(_expected_utility(item, _forecast(item, policy)) for item in subset)
            if utility < 0:
                continue
            feasible.append(
                (
                    round(utility, 12),
                    -total_bytes,
                    tuple(item.content_id for item in subset),
                    selected,
                )
            )
    return max(feasible, key=lambda item: (item[0], item[1], item[2]))[3]


def _evaluate(policy: str) -> dict[str, Any]:
    selected = _select(policy)
    prefetched_bytes = sum(item.size_bytes for item in selected)
    useful = tuple(item for item in selected if item.actual_requested)
    wasted = tuple(item for item in selected if not item.actual_requested)
    essential_bytes = sum(item.size_bytes for item in selected if item.essential)
    brier_score = None
    if policy != "essential_only":
        probabilities = [_forecast(item, policy) for item in CONTENTS]
        outcomes = [float(item.actual_requested) for item in CONTENTS]
        brier_score = sum(
            (probability - outcome) ** 2
            for probability, outcome in zip(probabilities, outcomes, strict=True)
        ) / len(CONTENTS)
    avoided_requests = sum(item.requests_if_needed for item in useful)
    return {
        "policy": policy,
        "selected_ids": [item.content_id for item in selected],
        "prefetched_bytes": prefetched_bytes,
        "essential_reserved_bytes": essential_bytes,
        "optional_prefetched_bytes": prefetched_bytes - essential_bytes,
        "useful_prefetched_bytes": sum(item.size_bytes for item in useful),
        "wasted_prefetched_bytes": sum(item.size_bytes for item in wasted),
        "useful_byte_fraction": round(sum(item.size_bytes for item in useful) / prefetched_bytes, 6),
        "avoided_remote_requests": avoided_requests,
        "avoided_round_trip_seconds": round(avoided_requests * EARTH_MOON_RTT_S, 6),
        "forecast_brier_score": None if brier_score is None else round(brier_score, 6),
    }


def build_preposition_study() -> dict[str, Any]:
    policies = (
        "essential_only",
        "popularity_only",
        "calibrated_forecast",
        "overconfident_forecast",
        "oracle",
    )
    evaluations = {policy: _evaluate(policy) for policy in policies}
    return {
        "study_id": "S012",
        "title": "Predictive prepositioning with forecast error cost",
        "evidence_class": "MODEL",
        "inputs": {
            "earth_moon_round_trip_s": EARTH_MOON_RTT_S,
            "cache_budget_bytes": CACHE_BUDGET_BYTES,
            "unused_cost_s_per_100_mb": UNUSED_COST_S_PER_100_MB,
            "contents": [asdict(item) for item in CONTENTS],
        },
        "decision_boundary": {
            "predictor_output": "request probability per immutable object",
            "deterministic_authority": "essential reservation plus exhaustive capacity-constrained selection",
            "rule": "a predictor cannot evict essential content or exceed the declared cache budget",
        },
        "policies": evaluations,
        "comparison": {
            "calibrated_minus_popularity_useful_bytes": (
                evaluations["calibrated_forecast"]["useful_prefetched_bytes"]
                - evaluations["popularity_only"]["useful_prefetched_bytes"]
            ),
            "overconfident_minus_popularity_wasted_bytes": (
                evaluations["overconfident_forecast"]["wasted_prefetched_bytes"]
                - evaluations["popularity_only"]["wasted_prefetched_bytes"]
            ),
            "calibrated_matches_oracle_selection": (
                evaluations["calibrated_forecast"]["selected_ids"]
                == evaluations["oracle"]["selected_ids"]
            ),
            "learned_policy_admission_result": "not established",
        },
        "interpretation_boundary": [
            "Content sizes, probabilities, outcomes and request counts are synthetic assumptions.",
            "The calibrated label describes an input forecast; one realised batch cannot establish calibration.",
            "No neural network is trained or executed; the model defines the contract a future predictor must satisfy.",
            "The oracle uses outcomes unavailable at decision time and is only an upper-bound comparator.",
            "Avoided round trips value latency; prefetching moves traffic earlier and does not make bytes free.",
            "The model omits expiry, privacy, encryption, cache churn, multicast and contact uncertainty.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/S012_prepositioning.json"))
    args = parser.parse_args(argv)
    rendered = json.dumps(build_preposition_study(), indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
