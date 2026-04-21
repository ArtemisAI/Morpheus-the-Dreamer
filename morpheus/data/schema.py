"""Core dataclasses: Observation, RetentionEvent, Pair.

Fields mirror the v0 spec's data-pipeline table. Stdlib-only (no pydantic) to
keep the scaffold's install surface at `python + numpy`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

# Matches `observations.type` enum referenced in the v0 spec. Exact names are
# claude-mem's concern; we keep them as opaque strings here.
ObservationType = Literal[
    "fact", "decision", "preference", "task", "error", "other",
]

# `observation_feedback.signal_type` — label space for v0.
RetentionSignal = Literal[
    "retained",        # retained_in_context  -> positive
    "superseded",      # negative
    "merged",          # merged_into          -> negative
    "consolidated",    # consolidated_into    -> neutral, dropped from training
]


@dataclass
class Observation:
    """One atomic memory chunk written by the claude-mem extractor."""

    id: str
    type: ObservationType
    content: str
    concepts: list[str] = field(default_factory=list)
    files_read: list[str] = field(default_factory=list)
    created_at_epoch: int = 0
    # Optional: precomputed embedding self-similarity (dot with project centroid).
    embedding_self_similarity: float = 0.0
    times_retrieved: int = 0
    project_local: bool = False


@dataclass
class RetentionEvent:
    """Label attached to an observation by the compiler/feedback pipeline."""

    observation_id: str
    signal: RetentionSignal
    created_at_epoch: int = 0


@dataclass
class Pair:
    """A DPO-style preference pair drawn from the same bucket_key.

    `positive` retained in context; `negative` was superseded/merged.
    `bucket_id` is the anchor-state hash from morpheus-rl-design §4 (GiGPO-style).
    """

    bucket_id: str
    positive: Observation
    negative: Observation
    metadata: dict = field(default_factory=dict)
