"""Evaluation metrics: pairwise accuracy and retained-rate lift."""

from __future__ import annotations

from morpheus.data.schema import Pair
from morpheus.scorer.base import Scorer


def pairwise_accuracy(scorer: Scorer, pairs: list[Pair]) -> float:
    """Fraction of pairs where score(pos) > score(neg). Ties count 0.5."""
    if not pairs:
        return 0.0
    hits = 0.0
    for p in pairs:
        sp = scorer.score(p.positive)
        sn = scorer.score(p.negative)
        if sp > sn:
            hits += 1.0
        elif sp == sn:
            hits += 0.5
    return hits / len(pairs)


def retained_rate_lift(scorer: Scorer, baseline: Scorer, pairs: list[Pair]) -> float:
    """Pairwise-accuracy(scorer) minus pairwise-accuracy(baseline). In [-1, 1]."""
    return pairwise_accuracy(scorer, pairs) - pairwise_accuracy(baseline, pairs)
