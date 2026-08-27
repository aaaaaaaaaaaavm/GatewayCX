"""Scenario input and deterministic result output."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .model import MODEL_VERSION, Scenario, simulate


def load_scenario(path: Path) -> Scenario:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: scenario root must be an object")
    return Scenario.from_dict(data)


def run_scenario_file(path: Path) -> dict[str, Any]:
    result = simulate(load_scenario(path))
    result["source"] = path.as_posix()
    return result


def run_directory(scenarios_dir: Path) -> dict[str, Any]:
    paths = sorted(scenarios_dir.glob("S*.json"))
    if not paths:
        raise ValueError(f"no S*.json scenarios found in {scenarios_dir}")
    results = [run_scenario_file(path) for path in paths]
    ids = [result["scenario_id"] for result in results]
    if len(ids) != len(set(ids)):
        raise ValueError("scenario ids must be unique")
    return {
        "record": "GatewayCX deterministic baseline",
        "evidence_class": "MODEL",
        "model_version": MODEL_VERSION,
        "result_count": len(results),
        "results": results,
    }


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(data, indent=2, sort_keys=True) + "\n"
    path.write_text(rendered, encoding="utf-8")

