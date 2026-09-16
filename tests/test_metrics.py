import unittest

from physai_bench.io import ValidationError, validate_dataset
from physai_bench.metrics import evaluate, parse_label


def item(item_id: str, answer: str = "C", episode: str = "episode-1") -> dict:
    return {
        "id": item_id,
        "instruction": "Choose the best action.",
        "context": {
            "mission": "Test mission",
            "physical_state": {},
            "observations": [],
            "tool_history": [],
            "a2a_interactions": [],
            "network_conditions": {},
        },
        "candidates": [
            {"label": label, "action": label, "description": label}
            for label in ("A", "B", "C", "D")
        ],
        "answer": answer,
        "rationale": "Test rationale.",
        "metadata": {
            "source_episode": episode,
            "source_turn": 1,
            "target_turn": 2,
            "action_category": "navigation_and_planning",
            "difficulty": "test",
            "physical_factors": [],
            "network_factors": [],
            "generator": "unit-test",
            "schema_version": "1.0",
        },
    }


class ParseLabelTests(unittest.TestCase):
    def test_accepts_single_label(self) -> None:
        self.assertEqual(parse_label(" c "), "C")

    def test_rejects_explanation(self) -> None:
        self.assertIsNone(parse_label("Answer: C"))


class EvaluateTests(unittest.TestCase):
    def test_failures_count_as_incorrect(self) -> None:
        dataset = [item("one"), item("two", episode="episode-2")]
        predictions = [{"id": "one", "prediction": "C", "inference_success": True}]
        report = evaluate(dataset, predictions, resamples=100, seed=7)
        self.assertEqual(report["items"], 2)
        self.assertEqual(report["correct"], 1)
        self.assertEqual(report["accuracy"], 0.5)
        self.assertEqual(report["parse_success_rate"], 0.5)
        self.assertEqual(report["inference_success_rate"], 0.5)

    def test_unknown_prediction_id_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            evaluate([item("one")], [{"id": "other", "prediction": "C"}])

    def test_invalid_candidate_order_is_rejected(self) -> None:
        dataset = [item("one")]
        dataset[0]["candidates"].reverse()
        with self.assertRaises(ValidationError):
            validate_dataset(dataset)


if __name__ == "__main__":
    unittest.main()

