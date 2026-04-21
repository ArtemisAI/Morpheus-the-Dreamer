"""Tests for LogRegScorer + fit_logreg + metrics on synthetic data."""

from __future__ import annotations

import unittest

from morpheus.data.synthetic import generate_synthetic_pairs
from morpheus.eval.holdout import split_sessions
from morpheus.eval.metrics import pairwise_accuracy
from morpheus.scorer.dpo import DPOScorer
from morpheus.scorer.random import RandomScorer
from morpheus.train.logreg_fit import fit_logreg


class TestLogReg(unittest.TestCase):
    def test_fit_beats_random_on_synthetic(self) -> None:
        pairs = generate_synthetic_pairs(n=200, seed=1)
        train, _val, test = split_sessions(pairs, seed=1)
        scorer = fit_logreg(train)
        rand = RandomScorer(seed=1)
        acc_fit = pairwise_accuracy(scorer, test)
        acc_rand = pairwise_accuracy(rand, test)
        self.assertGreater(acc_fit, 0.8)
        self.assertGreater(acc_fit - acc_rand, 0.1)

    def test_split_ratios(self) -> None:
        pairs = generate_synthetic_pairs(n=100, seed=2)
        tr, va, te = split_sessions(pairs, seed=2)
        self.assertEqual(len(tr) + len(va) + len(te), 100)
        self.assertEqual(len(tr), 70)

    def test_dpo_stub_raises(self) -> None:
        with self.assertRaises(NotImplementedError):
            DPOScorer()


if __name__ == "__main__":
    unittest.main()
