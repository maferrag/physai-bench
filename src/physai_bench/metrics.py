"""Strict PhysAI-Bench scoring and source-episode bootstrap intervals."""

from __future__ import annotations

import random
from collections import defaultdict
from statistics import fmean
from typing import Any

from .io import LABELS, ValidationError


def parse_label(value: Any) -> str | None:
    """Parse the paper's strict one-label response format."""
    if not isinstance(value, str):
        return None
    label = value.strip().upper()
    return label if label in LABELS and len(label) == 1 else None


def _prediction_map(predictions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    mapped: dict[str, dict[str, Any]] = {}
    for prediction in predictions:
        item_id = prediction.get("id")
        if not isinstance(item_id, str) or not item_id:
            raise ValidationError("every prediction must have a non-empty string id")
        if item_id in mapped:
            raise ValidationError(f"duplicate prediction id {item_id!r}")
        mapped[item_id] = prediction
    return mapped


def cluster_bootstrap_interval(
    outcomes: list[tuple[str, int]],
    *,
    confidence: float = 0.95,
    resamples: int = 2_000,
    seed: int = 42,
) -> tuple[float, float]:
    """Bootstrap accuracy by resampling complete source episodes."""
    if not outcomes:
        return (0.0, 0.0)
    clusters: dict[str, list[int]] = defaultdict(list)
    for episode_id, correct in outcomes:
        clusters[episode_id].append(correct)
    cluster_ids = sorted(clusters)
    if len(cluster_ids) == 1:
        accuracy = fmean(clusters[cluster_ids[0]])
        return (accuracy, accuracy)

    rng = random.Random(seed)
    samples: list[float] = []
    for _ in range(resamples):
        selected = [rng.choice(cluster_ids) for _ in cluster_ids]
        values = [value for cluster_id in selected for value in clusters[cluster_id]]
        samples.append(fmean(values))
    samples.sort()
    tail = (1.0 - confidence) / 2.0
    low_index = max(0, int(tail * (resamples - 1)))
    high_index = min(resamples - 1, int((1.0 - tail) * (resamples - 1)))
    return (samples[low_index], samples[high_index])


def evaluate(
    dataset: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
    *,
    resamples: int = 2_000,
    seed: int = 42,
) -> dict[str, Any]:
    """Score one prediction per benchmark item with failures counted as incorrect."""
    prediction_by_id = _prediction_map(predictions)
    dataset_ids = {item["id"] for item in dataset}
    unknown_ids = sorted(set(prediction_by_id) - dataset_ids)
    if unknown_ids:
        preview = ", ".join(repr(item_id) for item_id in unknown_ids[:3])
        raise ValidationError(f"predictions contain unknown ids: {preview}")

    correct_count = 0
    parse_success_count = 0
    inference_success_count = 0
    latencies: list[float] = []
    outcomes: list[tuple[str, int]] = []
    categories: dict[str, list[int]] = defaultdict(list)

    for item in dataset:
        prediction = prediction_by_id.get(item["id"], {})
        inference_success = bool(prediction.get("inference_success", bool(prediction)))
        parsed = parse_label(prediction.get("prediction")) if inference_success else None
        correct = int(parsed == item["answer"])
        correct_count += correct
        parse_success_count += int(parsed is not None)
        inference_success_count += int(inference_success)

        latency = prediction.get("latency_s")
        if inference_success and isinstance(latency, (int, float)) and latency >= 0:
            latencies.append(float(latency))

        metadata = item["metadata"]
        episode_id = str(metadata["source_episode"])
        category = str(metadata["action_category"])
        outcomes.append((episode_id, correct))
        categories[category].append(correct)

    count = len(dataset)
    accuracy = correct_count / count
    ci_low, ci_high = cluster_bootstrap_interval(
        outcomes, resamples=resamples, seed=seed
    )
    return {
        "items": count,
        "predictions_received": len(prediction_by_id),
        "correct": correct_count,
        "accuracy": accuracy,
        "accuracy_percent": round(100.0 * accuracy, 4),
        "cluster_bootstrap_95_ci": [ci_low, ci_high],
        "cluster_bootstrap_95_ci_percent": [
            round(100.0 * ci_low, 4),
            round(100.0 * ci_high, 4),
        ],
        "parse_success_rate": parse_success_count / count,
        "inference_success_rate": inference_success_count / count,
        "mean_latency_s": fmean(latencies) if latencies else None,
        "category_accuracy": {
            category: fmean(values) for category, values in sorted(categories.items())
        },
        "bootstrap": {
            "unit": "source_episode",
            "resamples": resamples,
            "seed": seed,
        },
    }

