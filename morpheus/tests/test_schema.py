"""Tests for morpheus.data.schema dataclasses."""

from __future__ import annotations

import unittest

from morpheus.data.schema import Observation, Pair, RetentionEvent


class TestSchema(unittest.TestCase):
    def test_observation_defaults(self) -> None:
        o = Observation(id="x", type="fact", content="hi")
        self.assertEqual(o.concepts, [])
        self.assertEqual(o.files_read, [])
        self.assertFalse(o.project_local)

    def test_retention_event_signal(self) -> None:
        e = RetentionEvent(observation_id="x", signal="retained")
        self.assertEqual(e.signal, "retained")

    def test_pair_roundtrip(self) -> None:
        a = Observation(id="p", type="fact", content="good")
        b = Observation(id="n", type="fact", content="bad")
        p = Pair(bucket_id="b0", positive=a, negative=b, metadata={"k": 1})
        self.assertIs(p.positive, a)
        self.assertIs(p.negative, b)
        self.assertEqual(p.metadata["k"], 1)


if __name__ == "__main__":
    unittest.main()
