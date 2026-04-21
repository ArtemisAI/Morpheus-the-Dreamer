"""RandomScorer — sanity baseline; pairwise accuracy should hover near 0.5."""

from __future__ import annotations

import random

from morpheus.data.schema import Observation
from morpheus.scorer.base import Scorer


class RandomScorer(Scorer):
    """Returns a uniform random score in [0, 1). Deterministic given `seed`."""

    def __init__(self, seed: int = 0) -> None:
        self._rng = random.Random(seed)

    def score(self, obs: Observation) -> float:
        return self._rng.random()
