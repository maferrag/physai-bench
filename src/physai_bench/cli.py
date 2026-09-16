"""Command-line interface for PhysAI-Bench."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .io import ValidationError, clean_records, load_jsonl, validate_dataset
from .metrics import evaluate


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="physai-bench")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="validate benchmark JSONL")
    validate_parser.add_argument("dataset", type=Path)

    evaluate_parser = subparsers.add_parser("evaluate", help="score model predictions")
    evaluate_parser.add_argument("--dataset", required=True, type=Path)
    evaluate_parser.add_argument("--predictions", required=True, type=Path)
    evaluate_parser.add_argument("--output", type=Path)
    evaluate_parser.add_argument("--bootstrap-resamples", type=int, default=2_000)
    evaluate_parser.add_argument("--seed", type=int, default=42)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "validate":
            dataset = load_jsonl(args.dataset)
            validate_dataset(dataset)
            print(f"Valid: {len(dataset)} benchmark instance(s)")
            return 0

        dataset = load_jsonl(args.dataset)
        validate_dataset(dataset)
        predictions = clean_records(load_jsonl(args.predictions))
        report = evaluate(
            clean_records(dataset),
            predictions,
            resamples=args.bootstrap_resamples,
            seed=args.seed,
        )
        rendered = json.dumps(report, indent=2, sort_keys=True)
        if args.output:
            args.output.write_text(rendered + "\n", encoding="utf-8")
        print(rendered)
        return 0
    except (OSError, ValidationError) as exc:
        print(f"Error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

