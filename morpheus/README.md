# morpheus/ — v0 scaffolding

Minimal Python package implementing the scaffold for the v0 spec
(`docs/design/morpheus-v0-spec.md`). **No training yet** — just the file
structure, dataclasses, a 5-feature logreg baseline, and a synthetic smoke
test that runs end-to-end.

## Install

Python 3.10+, numpy. No torch / transformers / sklearn.

```
pip install numpy
```

## Smoke test

```
python -m morpheus smoke
```

Generates 100 synthetic pairs, splits 70/15/15, fits a 5-feature logreg by
pairwise-logistic gradient descent, prints 5 lines, exits 0.

## Eval

```
python -m morpheus eval --db /path/to/brain.db
```

(Not implemented in scaffolding — stubs the SQLite loader call.)

## Layout

- `data/` — `schema.py` (Observation/RetentionEvent/Pair), `loader.py` (SQLite), `synthetic.py`.
- `features/extract.py` — 5-feature vector (age_days, text_length, embedding_self_similarity, times_retrieved, project_local_bool).
- `scorer/` — `base.Scorer`, `random.RandomScorer`, `logreg.LogRegScorer`, `dpo.DPOScorer` (raises; gated to v0.3).
- `train/logreg_fit.py` — stdlib+numpy GD on pairwise logistic loss.
- `eval/` — `metrics.py` (pairwise accuracy, retained-rate lift), `holdout.py`.
- `cli.py` / `__main__.py` — entrypoints.
- `tests/` — `unittest` suites.

## Deps

Runtime: `python>=3.10`, `numpy`. No sklearn (GD is ≤80 lines). DPO path
gated to v0.3 behind `torch`/`transformers`/`trl`.
