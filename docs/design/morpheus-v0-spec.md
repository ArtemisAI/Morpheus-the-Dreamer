# Morpheus v0 Spec

## The one-sentence problem

Given a chronological stream of claude-mem observations and which ones the compiler later chose to inject into a downstream agent's context, **learn a scoring function that predicts retention probability, so retrieval ranks by learned utility instead of uniform decay**.

## v0 hypothesis (falsifiable, 2 weeks)

> A DPO-trained Qwen2.5-3B-Instruct classifier, trained on ~10k (retained_obs, dropped_obs) pairs mined from existing `observation_feedback` history, beats the current `relevance_score × 1.0` baseline on next-session `retained_in_context` rate by ≥10 percentage points on held-out sessions.

If this is false in 2 weeks, we ditch the ML approach and ship the tabular weight-table from `morpheus-rl-design.md` instead.

## System boundary — what v0 does NOT do

1. **No online learning.** Nightly batch only. No gradient updates during serving.
2. **No memory overwrite / merge / consolidation action.** The policy only scores existing observations; the compiler still decides what to inject.
3. **No per-project or per-user policies.** Single global model.
4. **No neural summarizer / consolidation digest generation.** That stays prompt-driven (as in `morpheus-architecture.md` Phase C).
5. **No multi-turn credit assignment across sessions.** Each (obs, outcome) pair is i.i.d. in v0.

---

## v0 data pipeline

### Input: claude-mem session transcripts

From `claude-mem` SQLite (`observations` + `observation_feedback` tables, schema at migration ≥24):

| Field | Source | Use |
|---|---|---|
| `observations.id` | PK | Join key |
| `observations.type` | enum (6) | Feature |
| `observations.content` | text | Main input |
| `observations.concepts` | JSON array | Feature |
| `observations.files_read` | JSON array | Feature |
| `observations.created_at_epoch` | int | Age feature |
| `observation_feedback.signal_type` | enum | **Label** |
| `observation_feedback.created_at_epoch` | int | Ordering |

### Chunking — pick ONE

**Decision: one observation = one training example.** Observations are already atomic units written by the extractor. Don't re-chunk.

*Rejected: MemAgent-style fixed-token chunking. We have structured rows, not a long document.*

### Action space

**Binary {retain, drop} per observation.** No edit, merge, or reorder in v0.

### Reward — pick ONE

**Decision: binary terminal retention.**
```
r(obs) = 1  if any retained_in_context feedback exists for obs
r(obs) = 0  if only superseded/merged_into signals exist
r(obs) = discarded from training if only consolidated_into (neutral)
```

Justification (3 sentences): (1) MemSearcher and MemAgent both show terminal binary rewards suffice to train keep/drop — we don't need StepSearch's IG because we have no gold docs. (2) `retained_in_context` is the *only* signal with a clean "agent found this useful" semantics; the others are noisy. (3) Binary labels map cleanly to DPO preference pairs, letting us skip a critic entirely.

### Storage

**SQLite.** Reuse the existing `claude-mem` DB. Add one table `morpheus_training_pairs` with cols `(pos_obs_id, neg_obs_id, bucket_key, created_epoch)`. Pairs within the same bucket only; DPO wants comparable items.

*Rejected: JSONL. Losing transactional semantics with the upstream DB is not worth the serialization savings.*

---

## v0 policy architecture

### Base model

**Qwen2.5-3B-Instruct.** Justification: MemSearcher shows 3B beats 7B baselines on the memory-management task family (avg EM 43.8 vs. 38.5); fits comfortably on one 24GB GPU with LoRA; Qwen tokenizer handles our code-heavy content well.

### Feature extraction — memory chunk as input

Serialize each observation as:
```
<obs type="{type}" age_days="{days}" concepts="{top3}" files="{top2_prefixes}">
{content}
</obs>
```
One string per obs, truncated to 512 tokens. No embeddings — the model reads raw text.

### Output head

**Generative (DPO).** Model emits a single token `<keep>` or `<drop>`; DPO loss on preference pairs. No classifier head bolted on — keeps the training loop identical to standard DPO pipelines (TRL library).

*Rejected: classifier head. Adds a custom training path; harder to iterate. DPO on next-token `<keep>/<drop>` gives a score via logits if needed.*

---

## v0 training loop

### Pseudocode (≤40 lines)

```python
# Offline. Runs nightly.
import sqlite3, torch
from trl import DPOTrainer, DPOConfig
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL = "Qwen/Qwen2.5-3B-Instruct"
DB    = "/var/claude-mem/brain.db"
LR, BATCH, KL_BETA, EPOCHS = 1e-6, 32, 0.1, 1

def load_pairs(db):
    con = sqlite3.connect(db)
    rows = con.execute("""
      SELECT p.content, n.content
      FROM morpheus_training_pairs tp
      JOIN observations p ON p.id = tp.pos_obs_id
      JOIN observations n ON n.id = tp.neg_obs_id
    """).fetchall()
    return [{"prompt": "Keep this observation?\n",
             "chosen":   f"<obs>{p}</obs> <keep>",
             "rejected": f"<obs>{n}</obs> <keep>"} for p, n in rows]

tok   = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.bfloat16)
ref   = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.bfloat16)
data  = load_pairs(DB)

cfg = DPOConfig(
    learning_rate=LR, per_device_train_batch_size=BATCH,
    num_train_epochs=EPOCHS, beta=KL_BETA,
    max_length=1024, max_prompt_length=64,
    loss_type="sigmoid",          # standard DPO
    gradient_checkpointing=True, bf16=True,
    output_dir="./ckpt/morpheus-v0",
)
DPOTrainer(model=model, ref_model=ref, args=cfg,
           train_dataset=data, tokenizer=tok).train()
```

### Exact hyperparameters

| Param | Value | Source |
|---|---|---|
| Base model | Qwen2.5-3B-Instruct | MemSearcher 2511.02805 |
| LoRA rank | 16, alpha 32, dropout 0.05, target `q,k,v,o` | standard |
| Learning rate | 1e-6 | MemAgent + MemSearcher both |
| Train batch | 32 (per-device), accumulate to 256 effective | MemSearcher |
| Epochs | 1 | MemSearcher |
| DPO β | 0.1 | TRL default; tune in ablation |
| Max seq | 1024 | MemSearcher memory cap |
| Precision | bf16 + gradient checkpointing | fits 24GB |
| Preference pairs per update | ~10k | rough target |

### Trajectory sampling

Not applicable — we sample pairs from historical `observation_feedback`, no rollouts. One mined pair = one positive (`retained_in_context`) and one negative (`superseded` or `merged_into`) observation, drawn from the **same bucket_key** (see `morpheus-rl-design.md` §4) to ensure comparability.

---

## v0 evaluation

### Success metric

**`retained_in_context` rate on held-out sessions improves by ≥10pp over baseline.** Held-out = most recent 10% of sessions, time-sorted. Baseline = current `relevance_score × 1.0` ranking.

If <10pp: v0 fails; ship the tabular baseline instead.

### Ablations (3 knobs)

1. **Model scale:** 0.5B vs. 3B vs. 7B Qwen2.5-Instruct. Tests whether 3B is the right capacity.
2. **Pair mining source:** same-bucket only vs. cross-bucket. Tests whether bucket-keyed comparison is the load-bearing piece (as GiGPO 2505.10978 suggests).
3. **Reward signal:** binary retained-only vs. binary with `superseded` as explicit negative. Tests whether the supersession signal is actually informative (§10 q1 of the RL design doc).

---

## v0 file layout

```
morpheus/
├── README.md
├── pyproject.toml
├── configs/
│   └── v0.yaml                   # all hyperparams above
├── src/morpheus/
│   ├── data.py                   # mine pairs from claude-mem DB
│   ├── bucket.py                 # bucket_key from morpheus-rl-design §4
│   ├── train.py                  # DPO loop (pseudocode above)
│   ├── serve.py                  # score(obs) → logit, writes policy_weights
│   └── eval.py                   # held-out retained_in_context uplift
└── tests/
    └── test_bucket.py            # bucket hashing stability
```

10 files total. No frameworks beyond `trl`, `transformers`, `sqlite3`.

---

## Disagreement with `morpheus-rl-design.md`

**We disagree on two points, mildly, and one, strongly.**

1. *(Mild)* The tabular `weight = 1.0 + k·(μ−μ_global)/(1+sample_count/50)` is fine as a **fallback**, not as the primary approach. It can't generalize across buckets with zero samples, which is most of them on a new project. v0 should train a model; keep the table as the cold-start prior.

2. *(Mild)* Clamping to `[0.5, 1.5]` is arbitrary and prevents the policy from ever strongly filtering. A model output passed through sigmoid naturally lives in (0,1); no clamp needed.

3. *(Strong)* **§3's four-signal reward with `superseded = −0.3`, `merged = −0.1` is under-motivated.** The literature (MemSearcher, MemAgent, MEM1) consistently uses binary or near-binary terminal rewards. The `-0.3 / -0.1` ratio is a guess. **v0 uses binary retention and treats `superseded`/`merged` uniformly as negatives**, then ablates (see Ablation 3) to see if the distinction matters. If it does, we fit the coefficients from data, not from prior belief.

Everything else in the design doc — the bucket_key definition, nightly cadence, feature-flag gating, multiplicative serving blend — we keep as-is.
