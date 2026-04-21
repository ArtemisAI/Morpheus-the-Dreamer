"""CLI entrypoint: `python -m morpheus smoke` and `python -m morpheus eval`."""

from __future__ import annotations

import argparse
import sys

from morpheus.data.synthetic import generate_synthetic_pairs
from morpheus.eval.holdout import split_sessions
from morpheus.eval.metrics import pairwise_accuracy, retained_rate_lift
from morpheus.scorer.random import RandomScorer
from morpheus.train.logreg_fit import fit_logreg


def _cmd_smoke(_args: argparse.Namespace) -> int:
    pairs = generate_synthetic_pairs(n=100, seed=0)
    train, val, test = split_sessions(pairs, seed=0)
    scorer = fit_logreg(train)
    baseline = RandomScorer(seed=0)
    acc = pairwise_accuracy(scorer, test)
    lift = retained_rate_lift(scorer, baseline, test)
    print(f"pairs: {len(pairs)} (train={len(train)} val={len(val)} test={len(test)})")
    print(f"scorer: LogRegScorer (5 features, pairwise-logistic fit)")
    print(f"baseline: RandomScorer(seed=0)")
    print(f"pairwise_accuracy(test): {acc:.3f}")
    print(f"retained_rate_lift vs random: {lift:+.3f}")
    return 0


def _cmd_eval(args: argparse.Namespace) -> int:
    # Placeholder: in v0 proper, loads from claude-mem SQLite via
    # morpheus.data.loader.load_pairs_from_sqlite(args.db).
    print(f"eval: db={args.db} (not implemented in scaffolding)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="morpheus")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("smoke", help="end-to-end synthetic smoke test")
    sp.set_defaults(func=_cmd_smoke)

    sp = sub.add_parser("eval", help="evaluate on a real claude-mem DB")
    sp.add_argument("--db", default="/var/claude-mem/brain.db")
    sp.set_defaults(func=_cmd_eval)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
