# Data format

PhysAI-Bench uses newline-delimited JSON (JSONL): one benchmark instance per line. The authoritative machine-readable definition is [schema.json](schema.json).

## Core fields

| Field | Meaning |
|---|---|
| `id` | Stable canonical instance identifier |
| `instruction` | Decision-making question shown to the model |
| `context` | Only information visible before the target decision |
| `candidates` | Exactly four actions labeled A-D |
| `answer` | Trace-derived reference label |
| `rationale` | Explanation based only on visible context |
| `metadata` | Episode, turn, category, factor, generator, and schema provenance |

The reference action is trace-derived. It is the action executed in the source mission and is not claimed to be the only theoretically valid or globally optimal choice.

## Leakage controls

When constructing or releasing data:

- truncate the episode immediately before the target action;
- keep context and distractor generation blind to the executed action;
- add the trace-derived action only during independent validation and assembly;
- reject semantically equivalent alternatives;
- exclude development and demonstration source episodes from held-out evaluation;
- lock held-out item identifiers, episode identifiers, the sampling seed, and dataset fingerprint before model evaluation.

## Prediction format

Each prediction file is also JSONL:

```json
{"id": "physai-bench-example-0001", "prediction": "C", "latency_s": 0.42, "inference_success": true}
```

`prediction` must be exactly one of `A`, `B`, `C`, or `D` after trimming whitespace. Missing, malformed, and failed predictions count as incorrect.

The sample instance is illustrative and mirrors the example in the paper; it is not part of any official evaluation split.

