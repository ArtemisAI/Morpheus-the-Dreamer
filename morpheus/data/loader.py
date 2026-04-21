"""Load training pairs from a claude-mem SQLite database."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from morpheus.data.schema import Observation, Pair


# Query mirrors the spec's pseudocode. The `morpheus_training_pairs` table is
# created by the pair-mining job (not implemented in scaffolding).
_PAIR_QUERY = """
SELECT
    tp.bucket_key,
    p.id, p.type, p.content, p.concepts, p.files_read, p.created_at_epoch,
    n.id, n.type, n.content, n.concepts, n.files_read, n.created_at_epoch
FROM morpheus_training_pairs AS tp
JOIN observations AS p ON p.id = tp.pos_obs_id
JOIN observations AS n ON n.id = tp.neg_obs_id
"""


def _row_to_obs(
    id_: str, type_: str, content: str, concepts: str, files_read: str, epoch: int,
) -> Observation:
    import json

    return Observation(
        id=id_,
        type=type_,  # type: ignore[arg-type]
        content=content,
        concepts=json.loads(concepts or "[]"),
        files_read=json.loads(files_read or "[]"),
        created_at_epoch=epoch,
    )


def load_pairs_from_sqlite(path: str | Path) -> list[Pair]:
    """Return all (pos, neg) pairs from the claude-mem DB.

    Reads the `morpheus_training_pairs` table. Raises FileNotFoundError if
    the DB does not exist; returns [] if the table is absent.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    con = sqlite3.connect(str(p))
    try:
        try:
            rows = con.execute(_PAIR_QUERY).fetchall()
        except sqlite3.OperationalError:
            return []
    finally:
        con.close()

    out: list[Pair] = []
    for r in rows:
        bucket = r[0]
        pos = _row_to_obs(*r[1:7])
        neg = _row_to_obs(*r[7:13])
        out.append(Pair(bucket_id=bucket, positive=pos, negative=neg))
    return out
