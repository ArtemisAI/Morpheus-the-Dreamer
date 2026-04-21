"""Synthetic pair generator for end-to-end smoke tests.

Generates pairs where the positive observation is (by construction) slightly
"better" on the 5 features used by `features.extract` — so a trained logreg
should beat random on the smoke test.
"""

from __future__ import annotations

import random
import time

from morpheus.data.schema import Observation, Pair


_TYPES = ("fact", "decision", "preference", "task", "error", "other")


def _make_obs(rng: random.Random, id_: str, good: bool, now: int) -> Observation:
    # Positives are younger, longer, more project-local, more retrieved.
    age_days = rng.randint(0, 20) if good else rng.randint(10, 90)
    length = rng.randint(200, 800) if good else rng.randint(20, 300)
    sim = rng.uniform(0.5, 0.95) if good else rng.uniform(0.0, 0.5)
    times = rng.randint(2, 10) if good else rng.randint(0, 3)
    local = good if rng.random() < 0.8 else (not good)

    return Observation(
        id=id_,
        type=rng.choice(_TYPES),  # type: ignore[arg-type]
        content="x" * length,
        concepts=[f"c{rng.randint(0, 20)}" for _ in range(rng.randint(0, 3))],
        files_read=[f"src/f{rng.randint(0, 5)}.py"],
        created_at_epoch=now - age_days * 86_400,
        embedding_self_similarity=sim,
        times_retrieved=times,
        project_local=local,
    )


def generate_synthetic_pairs(n: int = 100, seed: int = 0) -> list[Pair]:
    """Return `n` synthetic preference pairs with a learnable signal."""
    rng = random.Random(seed)
    now = int(time.time())
    pairs: list[Pair] = []
    for i in range(n):
        bucket = f"b{i % 10}"
        pos = _make_obs(rng, f"p{i}", good=True, now=now)
        neg = _make_obs(rng, f"n{i}", good=False, now=now)
        pairs.append(Pair(bucket_id=bucket, positive=pos, negative=neg,
                          metadata={"synthetic": True}))
    return pairs
