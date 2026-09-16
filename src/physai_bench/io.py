"""JSONL loading and benchmark record validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


LABELS = ("A", "B", "C", "D")
REQUIRED_CONTEXT_FIELDS = (
    "mission",
    "physical_state",
    "observations",
    "tool_history",
    "a2a_interactions",
    "network_conditions",
)
REQUIRED_METADATA_FIELDS = (
    "source_episode",
    "source_turn",
    "target_turn",
    "action_category",
    "difficulty",
    "physical_factors",
    "network_factors",
    "generator",
    "schema_version",
)


class ValidationError(ValueError):
    """Raised when a JSONL record violates the benchmark contract."""


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Load JSON objects from a UTF-8 JSONL file."""
    records: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValidationError(f"{path}:{line_number}: invalid JSON: {exc.msg}") from exc
            if not isinstance(value, dict):
                raise ValidationError(f"{path}:{line_number}: expected a JSON object")
            value["__line__"] = line_number
            records.append(value)
    return records


def _require(record: dict[str, Any], fields: Iterable[str], location: str) -> None:
    missing = [field for field in fields if field not in record]
    if missing:
        raise ValidationError(f"{location}: missing fields: {', '.join(missing)}")


def validate_instance(record: dict[str, Any], *, location: str = "record") -> None:
    """Validate the semantic constraints needed by the evaluator."""
    _require(
        record,
        ("id", "instruction", "context", "candidates", "answer", "rationale", "metadata"),
        location,
    )
    if not isinstance(record["id"], str) or not record["id"].strip():
        raise ValidationError(f"{location}: id must be a non-empty string")
    if not isinstance(record["instruction"], str) or not record["instruction"].strip():
        raise ValidationError(f"{location}: instruction must be a non-empty string")
    if not isinstance(record["context"], dict):
        raise ValidationError(f"{location}: context must be an object")
    _require(record["context"], REQUIRED_CONTEXT_FIELDS, f"{location}.context")

    candidates = record["candidates"]
    if not isinstance(candidates, list) or len(candidates) != 4:
        raise ValidationError(f"{location}: candidates must contain exactly four actions")
    candidate_labels: list[str] = []
    for index, candidate in enumerate(candidates):
        candidate_location = f"{location}.candidates[{index}]"
        if not isinstance(candidate, dict):
            raise ValidationError(f"{candidate_location}: expected an object")
        _require(candidate, ("label", "action", "description"), candidate_location)
        candidate_labels.append(candidate["label"])
    if tuple(candidate_labels) != LABELS:
        raise ValidationError(f"{location}: candidate labels must appear exactly once in A-D order")
    if record["answer"] not in LABELS:
        raise ValidationError(f"{location}: answer must be one of A, B, C, or D")

    if not isinstance(record["metadata"], dict):
        raise ValidationError(f"{location}: metadata must be an object")
    _require(record["metadata"], REQUIRED_METADATA_FIELDS, f"{location}.metadata")
    if record["metadata"]["schema_version"] != "1.0":
        raise ValidationError(f"{location}: unsupported schema_version")


def validate_dataset(records: list[dict[str, Any]]) -> None:
    """Validate every instance and reject duplicate identifiers."""
    if not records:
        raise ValidationError("dataset is empty")
    seen: set[str] = set()
    for record in records:
        line_number = record.get("__line__", "?")
        validate_instance(record, location=f"line {line_number}")
        item_id = record["id"]
        if item_id in seen:
            raise ValidationError(f"line {line_number}: duplicate id {item_id!r}")
        seen.add(item_id)


def clean_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove loader-only bookkeeping before further processing."""
    return [{key: value for key, value in record.items() if key != "__line__"} for record in records]

