"""Five hand-crafted features for the logreg baseline (Q10).

The v0 spec does not pin a feature list for the tabular baseline — it only
names candidates. We commit to:

    1. age_days                    (from observations.created_at_epoch)
    2. text_length                 (len(content) — cheap proxy for token_count)
    3. embedding_self_similarity   (precomputed, project-centroid dot)
    4. times_retrieved             (observation_feedback aggregate)
    5. project_local_bool          (bucket-key file-prefix match)

Rationale: covers recency, size, semantic fit, usage, and locality — the four
axes implied by the spec's "tabular fallback" and the bucket_key design.
"""

from __future__ import annotations

import time

import numpy as np

from morpheus.data.schema import Observation

FEATURE_NAMES: tuple[str, ...] = (
    "age_days",
    "text_length",
    "embedding_self_similarity",
    "times_retrieved",
    "project_local_bool",
)


def extract_features(obs: Observation, now_epoch: int | None = None) -> np.ndarray:
    """Return a length-5 float32 feature vector for `obs`."""
    if now_epoch is None:
        now_epoch = int(time.time())
    age_days = max(0.0, (now_epoch - obs.created_at_epoch) / 86_400.0)
    return np.array(
        [
            age_days,
            float(len(obs.content)),
            float(obs.embedding_self_similarity),
            float(obs.times_retrieved),
            1.0 if obs.project_local else 0.0,
        ],
        dtype=np.float64,
    )
