"""Deterministic 70/15/15 split over pairs, grouped by bucket_id when possible."""

from __future__ import annotations

import random

from morpheus.data.schema import Pair


def split_sessions(
    pairs: list[Pair], seed: int = 0, ratios: tuple[float, float, float] = (0.7, 0.15, 0.15),
) -> tuple[list[Pair], list[Pair], list[Pair]]:
    """Return (train, val, test) partitions of `pairs`.

    Uses a deterministic shuffle keyed by `seed`. In v0 this is a naive
    random split; session-level grouping is left for when we have real data.
    """
    assert abs(sum(ratios) - 1.0) < 1e-6, "ratios must sum to 1"
    rng = random.Random(seed)
    shuffled = pairs[:]
    rng.shuffle(shuffled)
    n = len(shuffled)
    n_train = int(n * ratios[0])
    n_val = int(n * ratios[1])
    train = shuffled[:n_train]
    val = shuffled[n_train : n_train + n_val]
    test = shuffled[n_train + n_val :]
    return train, val, test
