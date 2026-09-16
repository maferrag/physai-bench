# Contributing

Thank you for helping improve PhysAI-Bench.

## Before opening a change

- Keep benchmark identifiers and source-episode metadata stable.
- Do not move examples across development, demonstration, and held-out splits.
- Do not expose held-out labels in prompts, logs, or public model outputs.
- Record the dataset fingerprint and random seed whenever a split is generated.
- Add or update tests when changing parsing, scoring, or validation behavior.

## Local checks

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
physai-bench validate data/samples/example.jsonl
physai-bench evaluate --dataset data/samples/example.jsonl --predictions data/samples/predictions.jsonl
```

Please use focused pull requests and explain any effect on benchmark comparability or previously reported scores.

