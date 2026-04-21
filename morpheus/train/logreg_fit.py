"""Fit a LogRegScorer on preference pairs via pairwise logistic loss.

For each pair (pos, neg) with feature vectors x_p, x_n, minimize
    L = -log sigmoid(w·(x_p - x_n))  + (l2/2) * ||w||^2
via full-batch gradient descent. No sklearn; stdlib + numpy.
"""

from __future__ import annotations

import numpy as np

from morpheus.data.schema import Pair
from morpheus.features.extract import FEATURE_NAMES, extract_features
from morpheus.scorer.logreg import LogRegScorer


def _pair_features(pairs: list[Pair], now_epoch: int) -> tuple[np.ndarray, np.ndarray]:
    pos = np.stack([extract_features(p.positive, now_epoch) for p in pairs])
    neg = np.stack([extract_features(p.negative, now_epoch) for p in pairs])
    return pos, neg


def fit_logreg(
    pairs: list[Pair],
    *,
    lr: float = 0.1,
    l2: float = 1e-3,
    n_steps: int = 400,
    now_epoch: int | None = None,
    seed: int = 0,
) -> LogRegScorer:
    """Fit weights by pairwise-logistic gradient descent; return a LogRegScorer."""
    import time as _time

    if now_epoch is None:
        now_epoch = int(_time.time())
    if not pairs:
        raise ValueError("fit_logreg: empty pair list")

    pos, neg = _pair_features(pairs, now_epoch)
    all_x = np.vstack([pos, neg])
    mean = all_x.mean(axis=0)
    std = all_x.std(axis=0)
    std_safe = np.where(std == 0, 1.0, std)
    pos_n = (pos - mean) / std_safe
    neg_n = (neg - mean) / std_safe
    diff = pos_n - neg_n  # (N, D)

    rng = np.random.default_rng(seed)
    d = diff.shape[1]
    assert d == len(FEATURE_NAMES)
    w = rng.normal(scale=0.01, size=d)

    for _ in range(n_steps):
        z = diff @ w  # (N,)
        # sigmoid(-z) = 1 - sigmoid(z); gradient of -log sig(z) is -(1-sig(z)) * diff
        s = 1.0 / (1.0 + np.exp(-z))
        grad = -((1.0 - s)[:, None] * diff).mean(axis=0) + l2 * w
        w -= lr * grad

    return LogRegScorer(
        weights=w, bias=0.0, feature_mean=mean, feature_std=std_safe,
    )
