# Morpheus v0 — Open Questions

Ranked by value/cost. Answer in this order.

---

### 1. Do we have ≥10k (pos, neg) pairs with same bucket_key in the existing claude-mem DB?

**Why:** If the answer is no, v0 is dead on arrival — DPO needs paired preferences. We'd pivot to cross-bucket pairs or synthetic augmentation.

**Cheapest experiment:** One SQLite query against a real brain.db: `SELECT bucket_key, COUNT(*) FROM observations WHERE id IN (retained_ids) GROUP BY bucket_key HAVING COUNT >= 5`, same for negatives. Join and count intersection. 20 minutes.

---

### 2. Does binary retained/not-retained give a learnable signal, or is it too noisy?

**Why:** If the model can't fit the training set at all, v0 is a dead algorithm — pivot to the tabular baseline immediately.

**Cheapest experiment:** Train on 1k pairs for 100 steps, check train loss decreases monotonically. If not, diagnose with a linear probe on hand-crafted features (age, type, has-files-read). 2 hours.

---

### 3. Is Qwen2.5-3B actually better than a 0.5B model for this task?

**Why:** 0.5B inference is ~6x cheaper; if accuracy is comparable, we save serving cost forever.

**Cheapest experiment:** Run Ablation 1 from the v0 spec with 0.5B vs. 3B on identical data, same LoRA config. 1 GPU-day.

---

### 4. Does the bucket_key's file-prefix component generalize, or does it overfit per-project?

**Why:** `morpheus-rl-design.md` §10 q3 — if a single heavy project biases weights, global policy fails on new projects.

**Cheapest experiment:** Train on all-projects-except-one, evaluate held-out project's retention uplift. Repeat for 3 projects. 1 day.

---

### 5. Is `superseded` actually a negative signal, or is it orthogonal to retention quality?

**Why:** `morpheus-rl-design.md` §3 assigns `superseded = −0.3` by intuition. If it's noise, we should drop it from training and save half our labeling budget.

**Cheapest experiment:** Ablation 3 from v0 spec: train with retained-only negatives vs. retained + superseded negatives; compare held-out retention uplift. 1 GPU-day.

---

### 6. Does serving-time inference latency (Qwen2.5-3B scoring N observations) fit within the compiler's budget?

**Why:** If scoring adds >100ms per compile, users will disable the feature.

**Cheapest experiment:** Benchmark `model.forward` on batches of 64 × 512-token obs with int8 quantization, one 24GB GPU. Target: p95 ≤ 50ms. 2 hours.

---

### 7. Should the score be *multiplicative* with `relevance_score`, or *replace* it?

**Why:** The design doc assumes multiplicative. If the model's logits are well-calibrated, replacement is simpler and removes a confounder when debugging ranking regressions.

**Cheapest experiment:** Offline replay of last 30 days' retrievals: rank by `relevance × model`, by `model` alone, by `relevance` alone; compare NDCG@10 against actual retention labels. 3 hours.

---

### 8. How fast does the policy stale — weekly or monthly?

**Why:** Determines retraining cadence. Weekly = 4× the infra cost of monthly.

**Cheapest experiment:** Train on day-0 through day-N data, evaluate on day-N+7 vs. day-N+30. Plot retention uplift vs. staleness window. Can do with existing historical data, no new training runs. 1 day.

---

### 9. Is `retained_in_context` itself a biased teacher — does training on it just reproduce the current compiler's mistakes?

**Why:** Circular reward (§8 of RL design doc). If the compiler injects observation X, the model learns X is good, compiler keeps injecting X — feedback loop.

**Cheapest experiment:** Hand-label 200 retrieved observations as "actually useful" / "not" by reading the downstream agent's response. Correlate model score with human label. If r<0.3, we need a different teacher (LLM-as-judge). 1 day of human labeling.

---

### 10. Is v0 even needed, or does a 5-feature logistic regression match it?

**Why:** If a logreg on `(type, age, concept_popularity, file_prefix_popularity, token_count)` gets within 2pp of Qwen-3B, ship the logreg and delete the GPU dependency.

**Cheapest experiment:** scikit-learn logreg on the same pair dataset; compare held-out retention uplift vs. the v0 model. 2 hours. **Run this before Q3.**
