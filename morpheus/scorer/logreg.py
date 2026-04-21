"""LogRegScorer — 5-feature logistic regression, stdlib + numpy only.

This is the "ship early" baseline called out in open-question #10: if a
5-feature logreg matches Qwen2.5-3B within 2pp, we delete the GPU dep.
"""

from __future__ import annotations

import numpy as np

from morpheus.data.schema import Observation
from morpheus.features.extract import FEATURE_NAMES, extract_features
from morpheus.scorer.base import Scorer


class LogRegScorer(Scorer):
    """Sigmoid(w·x + b). `weights` has shape (5,); `bias` is scalar.

    Feature normalization is baked in via `feature_mean` / `feature_std` so
    that `score()` at serving time matches training-time conditioning.
    """

    def __init__(
        self,
        weights: np.ndarray,
        bias: float,
        feature_mean: np.ndarray,
        feature_std: np.ndarray,
    ) -> None:
        assert weights.shape == (len(FEATURE_NAMES),)
        assert feature_mean.shape == weights.shape
        assert feature_std.shape == weights.shape
        self.weights = weights.astype(np.float64)
        self.bias = float(bias)
        self.feature_mean = feature_mean.astype(np.float64)
        self.feature_std = feature_std.astype(np.float64)

    def _normalize(self, x: np.ndarray) -> np.ndarray:
        return (x - self.feature_mean) / np.where(self.feature_std == 0, 1.0, self.feature_std)

    def logit(self, obs: Observation) -> float:
        x = self._normalize(extract_features(obs))
        return float(np.dot(self.weights, x) + self.bias)

    def score(self, obs: Observation) -> float:
        z = self.logit(obs)
        # Numerically stable sigmoid.
        if z >= 0:
            e = np.exp(-z)
            return float(1.0 / (1.0 + e))
        e = np.exp(z)
        return float(e / (1.0 + e))
