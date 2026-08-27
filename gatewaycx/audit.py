"""Cheap record-integrity checks for the GatewayCX engineering baseline."""

from __future__ import annotations

import json
import re
from pathlib import Path


SCENARIO_NAME = re.compile(r"^(S\d{3})_[a-z0-9_]+\.json$")
REQUIREMENT_ID = re.compile(r"\|\s*(GX-[A-Z]{3}-\d{3})\s*\|")
CLAIM_ID = re.compile(r"\|\s*(C\d{3})\s*\|")
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def _duplicates(items: list[str]) -> list[str]:
    return sorted({item for item in items if items.count(item) > 1})


def audit(root: Path) -> list[str]:
    errors: list[str] = []
    required_files = [
        "README.md",
        "ORIGIN.md",
        "VISION.md",
        "ROADMAP.md",
        "OPEN_PROBLEMS.md",
        "docs/REQUIREMENTS.md",
        "docs/CLAIM_LEDGER.md",
        "docs/PROVENANCE.md",
        "results/baseline.json",
    ]
    for relative in required_files:
        if not (root / relative).is_file():
            errors.append(f"missing required record: {relative}")

    scenario_ids: list[str] = []
    for path in sorted((root / "scenarios").glob("*.json")):
        match = SCENARIO_NAME.match(path.name)
        if not match:
            errors.append(f"scenario filename does not follow SNNN_name.json: {path.name}")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"cannot read {path.relative_to(root)}: {exc}")
            continue
        scenario_id = str(data.get("id", ""))
        scenario_ids.append(scenario_id)
        if scenario_id != match.group(1):
            errors.append(f"{path.name}: id {scenario_id!r} does not match filename")
        if data.get("evidence_class") != "MODEL":
            errors.append(f"{path.name}: executable baseline must declare MODEL evidence")
    if duplicates := _duplicates(scenario_ids):
        errors.append(f"duplicate scenario ids: {duplicates}")

    baseline_path = root / "results" / "baseline.json"
    if baseline_path.is_file():
        try:
            baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
            result_ids = [item["scenario_id"] for item in baseline.get("results", [])]
            if result_ids != scenario_ids:
                errors.append(
                    f"baseline scenario ids {result_ids} do not match inputs {scenario_ids}; regenerate"
                )
            if "generated_at" in baseline:
                errors.append("baseline contains a time-dependent generated_at field")
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
            errors.append(f"cannot inspect results/baseline.json: {exc}")

    registers = [
        (root / "docs" / "REQUIREMENTS.md", REQUIREMENT_ID, "requirement"),
        (root / "docs" / "CLAIM_LEDGER.md", CLAIM_ID, "claim"),
    ]
    for path, pattern, label in registers:
        if not path.is_file():
            continue
        ids = pattern.findall(path.read_text(encoding="utf-8"))
        if duplicates := _duplicates(ids):
            errors.append(f"duplicate {label} ids: {duplicates}")

    for markdown in sorted(root.rglob("*.md")):
        text = markdown.read_text(encoding="utf-8")
        for target in MARKDOWN_LINK.findall(text):
            clean = target.split("#", 1)[0].strip()
            if not clean or clean.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (markdown.parent / clean).resolve()
            if not resolved.exists():
                errors.append(
                    f"broken local link in {markdown.relative_to(root)}: {target}"
                )

    return errors


def format_audit(errors: list[str]) -> str:
    if not errors:
        return "record audit passed"
    return "record audit failed:\n" + "\n".join(f"- {error}" for error in errors)

