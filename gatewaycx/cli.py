"""Command-line entry point for GatewayCX baseline studies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .audit import audit, format_audit
from .io import run_directory, run_scenario_file, write_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gatewaycx")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="run one scenario")
    run.add_argument("scenario", type=Path)

    run_all = subparsers.add_parser("run-all", help="run every committed baseline scenario")
    run_all.add_argument("--scenarios", type=Path, default=Path("scenarios"))
    run_all.add_argument("--output", type=Path, default=Path("results/baseline.json"))

    check = subparsers.add_parser("audit", help="check the engineering record for drift")
    check.add_argument("--root", type=Path, default=Path("."))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "run":
        print(json.dumps(run_scenario_file(args.scenario), indent=2, sort_keys=True))
        return 0
    if args.command == "audit":
        errors = audit(args.root.resolve())
        print(format_audit(errors))
        return 1 if errors else 0
    record = run_directory(args.scenarios)
    write_json(args.output, record)
    print(f"wrote {args.output} with {record['result_count']} model results")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
