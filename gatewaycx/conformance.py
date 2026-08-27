"""GX-B1 bearer-profile semantic checks with no third-party runtime dependency."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


REQUIRED_TELEMETRY = {
    "link_state",
    "tx_rate_mbps",
    "rx_rate_mbps",
    "queue_bytes",
    "next_contact_utc",
    "fault_codes",
}
MEDIA = {"optical", "rf", "hybrid", "other"}
REGIONS = {"earth", "cislunar", "lunar_orbit", "lunar_surface"}
AVAILABILITY_MODES = {"continuous", "scheduled", "opportunistic"}
EVIDENCE_LEVELS = {"assumed", "marketed", "specified", "demonstrated", "qualified"}


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _uri(value: Any) -> bool:
    return isinstance(value, str) and bool(urlparse(value).scheme)


def validate_bearer_profile(profile: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {
        "schema_version", "bearer_id", "media", "endpoints", "performance",
        "availability", "queue", "security", "telemetry", "evidence",
    }
    missing = sorted(required - profile.keys())
    if missing:
        errors.append(f"missing top-level fields: {missing}")
        return errors
    if profile["schema_version"] != "0.1":
        errors.append("schema_version must be '0.1'")
    if not isinstance(profile["bearer_id"], str) or not re.fullmatch(
        r"[a-z0-9][a-z0-9._-]{2,63}", profile["bearer_id"]
    ):
        errors.append("bearer_id does not match the portable identifier profile")
    if profile["media"] not in MEDIA:
        errors.append(f"media must be one of {sorted(MEDIA)}")

    endpoints = profile["endpoints"]
    if not isinstance(endpoints, list) or len(endpoints) != 2:
        errors.append("endpoints must contain exactly two endpoint objects")
    else:
        for index, endpoint in enumerate(endpoints):
            if not isinstance(endpoint, dict) or not endpoint.get("node_id"):
                errors.append(f"endpoints[{index}] requires node_id")
            if not isinstance(endpoint, dict) or endpoint.get("region") not in REGIONS:
                errors.append(f"endpoints[{index}].region is invalid")
        if endpoints[0].get("node_id") == endpoints[1].get("node_id"):
            errors.append("endpoint node_id values must differ")

    performance = profile["performance"]
    performance_fields = (
        "forward_capacity_mbps", "return_capacity_mbps", "one_way_latency_min_ms",
        "one_way_latency_max_ms", "acquisition_max_s", "maximum_traffic_unit_bytes",
    )
    if not isinstance(performance, dict):
        errors.append("performance must be an object")
    else:
        numeric_performance = True
        for field in performance_fields:
            if field not in performance or not _is_number(performance[field]):
                errors.append(f"performance.{field} must be numeric")
                numeric_performance = False
        if numeric_performance:
            if performance["forward_capacity_mbps"] <= 0 or performance["return_capacity_mbps"] <= 0:
                errors.append("forward and return capacity must be greater than zero")
            if performance["one_way_latency_min_ms"] < 0:
                errors.append("minimum latency must be non-negative")
            if performance["one_way_latency_max_ms"] < performance["one_way_latency_min_ms"]:
                errors.append("maximum latency must be greater than or equal to minimum latency")
            if performance["acquisition_max_s"] < 0:
                errors.append("acquisition time must be non-negative")
            if performance["maximum_traffic_unit_bytes"] < 256:
                errors.append("maximum traffic unit must be at least 256 bytes")

    availability = profile["availability"]
    if not isinstance(availability, dict) or availability.get("mode") not in AVAILABILITY_MODES:
        errors.append("availability.mode is invalid")
    else:
        if availability["mode"] == "scheduled" and not _uri(availability.get("contact_plan_uri")):
            errors.append("scheduled availability requires contact_plan_uri")
        if not isinstance(availability.get("weather_sensitive"), bool):
            errors.append("availability.weather_sensitive must be boolean")
        horizon = availability.get("prediction_horizon_s")
        if not isinstance(horizon, int) or isinstance(horizon, bool) or horizon < 0:
            errors.append("availability.prediction_horizon_s must be a non-negative integer")

    queue = profile["queue"]
    if not isinstance(queue, dict):
        errors.append("queue must be an object")
    else:
        deferred = queue.get("deferred_delivery")
        durable = queue.get("durable_bytes")
        if not isinstance(deferred, bool):
            errors.append("queue.deferred_delivery must be boolean")
        if not isinstance(durable, int) or isinstance(durable, bool) or durable < 0:
            errors.append("queue.durable_bytes must be a non-negative integer")
        if queue.get("backpressure") not in {"reject", "queue", "best_effort_drop"}:
            errors.append("queue.backpressure is invalid")
        if deferred is True and durable == 0:
            errors.append("deferred delivery requires non-zero durable_bytes")
        if deferred is True and queue.get("backpressure") != "queue":
            errors.append("deferred delivery requires queue backpressure")

    security = profile["security"]
    if not isinstance(security, dict):
        errors.append("security must be an object")
    else:
        treatment = security.get("payload_treatment")
        if treatment not in {"transparent", "terminated", "transformed"}:
            errors.append("security.payload_treatment is invalid")
        if not security.get("management_authentication"):
            errors.append("security.management_authentication is required")
        if treatment in {"terminated", "transformed"} and not security.get(
            "termination_disclosure"
        ):
            errors.append("non-transparent payload treatment requires termination_disclosure")

    telemetry = profile["telemetry"]
    if not isinstance(telemetry, dict):
        errors.append("telemetry must be an object")
    else:
        capabilities = telemetry.get("capabilities")
        if not isinstance(capabilities, list):
            errors.append("telemetry.capabilities must be an array")
        else:
            absent = sorted(REQUIRED_TELEMETRY - set(capabilities))
            if absent:
                errors.append(f"required telemetry capabilities absent: {absent}")
        freshness = telemetry.get("freshness_max_s")
        if not isinstance(freshness, int) or isinstance(freshness, bool) or freshness < 1:
            errors.append("telemetry.freshness_max_s must be a positive integer")

    evidence = profile["evidence"]
    if not isinstance(evidence, dict) or evidence.get("level") not in EVIDENCE_LEVELS:
        errors.append("evidence.level is invalid")
    else:
        if not _uri(evidence.get("source_uri")):
            errors.append("evidence.source_uri must be an absolute URI")
        try:
            date.fromisoformat(evidence.get("as_of", ""))
        except (TypeError, ValueError):
            errors.append("evidence.as_of must be an ISO date")
        if not isinstance(evidence.get("conditions"), list):
            errors.append("evidence.conditions must be an array")
        if evidence["level"] == "qualified" and not _uri(evidence.get("conformance_report_uri")):
            errors.append("qualified evidence requires conformance_report_uri")
    return errors


def validate_file(path: Path) -> list[str]:
    try:
        profile = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read JSON: {exc}"]
    if not isinstance(profile, dict):
        return ["profile root must be an object"]
    return validate_bearer_profile(profile)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profiles", type=Path, nargs="+")
    args = parser.parse_args(argv)
    failed = False
    for path in args.profiles:
        errors = validate_file(path)
        if errors:
            failed = True
            print(f"{path}: failed")
            for error in errors:
                print(f"- {error}")
        else:
            print(f"{path}: passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
