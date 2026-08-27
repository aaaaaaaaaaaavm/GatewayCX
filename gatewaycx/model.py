"""Deterministic first-order service-path model for GatewayCX.

This module keeps propagation, processing and serialization as separate terms. It does not model
transport congestion control, packet loss, shared-link contention or orbital contacts. Those
omissions are intentional and recorded in docs/PROVENANCE.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SPEED_OF_LIGHT_KM_S = 299_792.458
MODEL_VERSION = "0.1.0"
PATH_KINDS = {"local", "cislunar"}
DELIVERY_MODES = {"continuous", "deferred", "local-only"}


class ScenarioError(ValueError):
    """Raised when a scenario would make the model ambiguous or physically invalid."""


def _nonnegative_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ScenarioError(f"{field} must be a number")
    number = float(value)
    if number < 0:
        raise ScenarioError(f"{field} must be non-negative")
    return number


@dataclass(frozen=True)
class Path:
    name: str
    kind: str
    distance_km: float
    one_way_processing_ms: float
    capacity_mbps: float
    available: bool

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> "Path":
        kind = str(data.get("kind", ""))
        if kind not in PATH_KINDS:
            raise ScenarioError(f"path {name}: kind must be one of {sorted(PATH_KINDS)}")
        distance = _nonnegative_number(data.get("distance_km"), f"path {name}.distance_km")
        processing = _nonnegative_number(
            data.get("one_way_processing_ms", 0),
            f"path {name}.one_way_processing_ms",
        )
        capacity = _nonnegative_number(data.get("capacity_mbps"), f"path {name}.capacity_mbps")
        if capacity == 0:
            raise ScenarioError(f"path {name}.capacity_mbps must be greater than zero")
        available = data.get("available")
        if not isinstance(available, bool):
            raise ScenarioError(f"path {name}.available must be true or false")
        return cls(name, kind, distance, processing, capacity, available)

    @property
    def propagation_one_way_s(self) -> float:
        return self.distance_km / SPEED_OF_LIGHT_KM_S

    @property
    def processing_one_way_s(self) -> float:
        return self.one_way_processing_ms / 1_000.0

    @property
    def round_trip_s(self) -> float:
        return 2.0 * (self.propagation_one_way_s + self.processing_one_way_s)

    def serialization_s(self, transfer_bytes: int) -> float:
        return transfer_bytes * 8.0 / (self.capacity_mbps * 1_000_000.0)


@dataclass(frozen=True)
class Operation:
    name: str
    phase: int
    path: str
    sequential_round_trips: float
    transfer_bytes: int
    delivery_mode: str
    required_for_user_completion: bool

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Operation":
        name = str(data.get("name", "")).strip()
        if not name:
            raise ScenarioError("operation.name must not be empty")
        phase_value = data.get("phase")
        if isinstance(phase_value, bool) or not isinstance(phase_value, int) or phase_value < 0:
            raise ScenarioError(f"operation {name}.phase must be a non-negative integer")
        path = str(data.get("path", "")).strip()
        round_trips = _nonnegative_number(
            data.get("sequential_round_trips", 0),
            f"operation {name}.sequential_round_trips",
        )
        transfer_value = data.get("transfer_bytes", 0)
        if isinstance(transfer_value, bool) or not isinstance(transfer_value, int) or transfer_value < 0:
            raise ScenarioError(f"operation {name}.transfer_bytes must be a non-negative integer")
        delivery_mode = str(data.get("delivery_mode", ""))
        if delivery_mode not in DELIVERY_MODES:
            raise ScenarioError(
                f"operation {name}.delivery_mode must be one of {sorted(DELIVERY_MODES)}"
            )
        required = data.get("required_for_user_completion")
        if not isinstance(required, bool):
            raise ScenarioError(
                f"operation {name}.required_for_user_completion must be true or false"
            )
        return cls(
            name,
            phase_value,
            path,
            round_trips,
            transfer_value,
            delivery_mode,
            required,
        )


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    title: str
    evidence_class: str
    description: str
    paths: dict[str, Path]
    operations: tuple[Operation, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Scenario":
        scenario_id = str(data.get("id", "")).strip()
        title = str(data.get("title", "")).strip()
        if not scenario_id or not title:
            raise ScenarioError("scenario id and title must not be empty")
        evidence_class = str(data.get("evidence_class", "")).strip()
        if evidence_class != "MODEL":
            raise ScenarioError("baseline executable scenarios must declare evidence_class MODEL")
        raw_paths = data.get("paths")
        if not isinstance(raw_paths, dict) or not raw_paths:
            raise ScenarioError("scenario.paths must be a non-empty object")
        paths = {name: Path.from_dict(name, value) for name, value in raw_paths.items()}
        raw_operations = data.get("operations")
        if not isinstance(raw_operations, list) or not raw_operations:
            raise ScenarioError("scenario.operations must be a non-empty array")
        operations = tuple(Operation.from_dict(item) for item in raw_operations)
        names = [item.name for item in operations]
        if len(names) != len(set(names)):
            raise ScenarioError("operation names must be unique within a scenario")
        if not any(item.required_for_user_completion for item in operations):
            raise ScenarioError("a scenario must have at least one operation required for completion")
        missing_paths = sorted({item.path for item in operations} - set(paths))
        if missing_paths:
            raise ScenarioError(f"operations reference unknown paths: {missing_paths}")
        for item in operations:
            if item.delivery_mode == "local-only" and paths[item.path].kind != "local":
                raise ScenarioError(
                    f"operation {item.name}: local-only delivery cannot use a cislunar path"
                )
        return cls(
            scenario_id,
            title,
            evidence_class,
            str(data.get("description", "")).strip(),
            paths,
            operations,
        )


def _rounded(value: float) -> float:
    return round(value, 9)


def simulate(scenario: Scenario) -> dict[str, Any]:
    """Execute one deterministic scenario and return a JSON-serialisable evidence record."""

    operation_results: list[dict[str, Any]] = []
    phase_durations: dict[int, list[float]] = {}
    completed_backbone_bytes = 0
    queued_backbone_bytes = 0

    for operation in scenario.operations:
        path = scenario.paths[operation.path]
        if path.available:
            duration = (
                operation.sequential_round_trips * path.round_trip_s
                + path.serialization_s(operation.transfer_bytes)
            )
            status = "completed"
            reason = None
            phase_durations.setdefault(operation.phase, []).append(duration)
            if path.kind == "cislunar":
                completed_backbone_bytes += operation.transfer_bytes
        elif operation.delivery_mode == "deferred":
            duration = 0.0
            status = "queued"
            reason = "path unavailable; deferred delivery accepted"
            if path.kind == "cislunar":
                queued_backbone_bytes += operation.transfer_bytes
        else:
            duration = 0.0
            status = "failed"
            reason = "path unavailable and delivery is not deferred"

        operation_results.append(
            {
                "name": operation.name,
                "phase": operation.phase,
                "path": operation.path,
                "path_kind": path.kind,
                "delivery_mode": operation.delivery_mode,
                "required_for_user_completion": operation.required_for_user_completion,
                "sequential_round_trips": operation.sequential_round_trips,
                "transfer_bytes": operation.transfer_bytes,
                "status": status,
                "duration_s": _rounded(duration),
                "reason": reason,
            }
        )

    required_statuses = [
        result["status"]
        for result in operation_results
        if result["required_for_user_completion"]
    ]
    status_counts = {
        state: sum(result["status"] == state for result in operation_results)
        for state in ("completed", "queued", "failed")
    }
    elapsed_s = sum(max(values) for _, values in sorted(phase_durations.items()) if values)

    return {
        "scenario_id": scenario.scenario_id,
        "title": scenario.title,
        "evidence_class": scenario.evidence_class,
        "model_version": MODEL_VERSION,
        "user_transaction_complete": all(state == "completed" for state in required_statuses),
        "elapsed_s": _rounded(elapsed_s),
        "completed_backbone_bytes": completed_backbone_bytes,
        "queued_backbone_bytes": queued_backbone_bytes,
        "status_counts": status_counts,
        "paths": {
            name: {
                "kind": path.kind,
                "available": path.available,
                "distance_km": path.distance_km,
                "capacity_mbps": path.capacity_mbps,
                "propagation_one_way_s": _rounded(path.propagation_one_way_s),
                "processing_one_way_s": _rounded(path.processing_one_way_s),
                "round_trip_s": _rounded(path.round_trip_s),
            }
            for name, path in sorted(scenario.paths.items())
        },
        "operations": operation_results,
    }
