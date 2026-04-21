"""Tests for morpheus.features.extract."""

from __future__ import annotations

import unittest

from morpheus.data.schema import Observation
from morpheus.features.extract import FEATURE_NAMES, extract_features


class TestFeatures(unittest.TestCase):
    def test_vector_length(self) -> None:
        o = Observation(id="x", type="fact", content="abc")
        v = extract_features(o, now_epoch=0)
        self.assertEqual(v.shape, (5,))
        self.assertEqual(len(FEATURE_NAMES), 5)

    def test_age_nonneg_and_length(self) -> None:
        o = Observation(id="x", type="fact", content="abcde", created_at_epoch=0)
        v = extract_features(o, now_epoch=86_400 * 3)  # 3 days later
        self.assertAlmostEqual(v[0], 3.0, places=4)
        self.assertEqual(v[1], 5.0)

    def test_booleans_and_scalars(self) -> None:
        o = Observation(
            id="x", type="fact", content="",
            embedding_self_similarity=0.7, times_retrieved=4, project_local=True,
        )
        v = extract_features(o, now_epoch=0)
        self.assertAlmostEqual(v[2], 0.7)
        self.assertEqual(v[3], 4.0)
        self.assertEqual(v[4], 1.0)


if __name__ == "__main__":
    unittest.main()
