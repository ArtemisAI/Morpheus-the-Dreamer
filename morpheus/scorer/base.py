"""Abstract Scorer interface: score(Observation) -> float."""

from __future__ import annotations

from abc import ABC, abstractmethod

from morpheus.data.schema import Observation


class Scorer(ABC):
    """A retention scorer. Higher score = more likely to be retained."""

    @abstractmethod
    def score(self, obs: Observation) -> float:
        """Return a real-valued retention score for `obs`."""

    def score_batch(self, obss: list[Observation]) -> list[float]:
        """Default batch implementation; subclasses may override for speed."""
        return [self.score(o) for o in obss]
