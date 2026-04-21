"""DPOScorer — deferred to v0.3 (needs torch + transformers + trl).

See docs/design/morpheus-v0-spec.md § "v0 policy architecture" for the full
spec. This stub exists so the `scorer` package's shape matches the v0 target.
"""

from __future__ import annotations

from morpheus.data.schema import Observation
from morpheus.scorer.base import Scorer


class DPOScorer(Scorer):
    """Qwen2.5-3B-Instruct + DPO on <keep>/<drop> next-token logits.

    Gated to v0.3: requires torch, transformers, trl, and a GPU. The
    scaffolding intentionally does not import these.
    """

    def __init__(self, *_args, **_kwargs) -> None:
        raise NotImplementedError(
            "DPOScorer is v0.3 — needs torch/transformers/trl. "
            "See docs/design/morpheus-v0-spec.md §'v0 policy architecture'."
        )

    def score(self, obs: Observation) -> float:  # pragma: no cover
        raise NotImplementedError("v0.3")
