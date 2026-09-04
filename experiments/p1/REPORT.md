# STM Prediction 1 — bounded ShapeWalk vs dump (action at equal quality)

Paper §10.1 (post-Sage). **Synthetic-stratum pilot — not human-reviewed 200.**

**Verdict:** `PASS`

## Coefficient lock (FIXED before run)

Action estimator (single-turn load, W₀=∅, W₁=admitted set):

```
Â_d = a·d(W₀,W₁)² + b·tokens_admitted + c·critical_evictions + d·ℓ_task
# Practical single-turn form used:
Â   = a·|W|² + b·tokens + c·0 + d·(1 − score)
a = 1.0
b = 1.0
c = 0.0  # no eviction in single-turn
d = 10.0
d(empty, W) := |W|   (cardinality of admitted)
tokens_admitted := Σ (len(title)+len(slug)) over admitted nodes
ℓ_task := 1 − score
score := |gold ∩ W| / |gold|
```

Coefficients were locked before any outcome was inspected. FAIL if dump ≤ walk
on the both-perfect stratum, or if the result appears only after retuning.

## Claim

For tasks whose required evidence lies within a bounded k-hop session
neighbourhood, bounded ShapeWalk achieves equal task performance at lower
measured action than a RAG-style dump of the available session material.
Compare at **equal task quality**. Do NOT require matched final evidence coverage.

## MemNet / operators

- **memnet-llm:** `0.19.3`
- **memnet.__file__:** `/workspace/stm-p1/.venv/lib/python3.13/site-packages/memnet/__init__.py`
- **merge commit:** `eff05dc8a0ad5369e8d7e7f347db30b9300b04d6`
- **Operators only:** `open_session`, `MutateGate.apply`, `PinMapComposer.compose`, `close_session`
- **Not used:** `rag_query`, leftover `add`, `Layer`, Neo4j / Pi / droplet / InvenTree
- **Dump condition:** bench fixture — serialise observable session nodes and admit
  the full ranked list into synthetic W_B. Analysis of a load operator, **not** product soft-M.
- **Call counts:** `{"open_session": 500, "MutateGate.apply": 500, "PinMapComposer.compose": 500, "close_session": 500}`

## Protocol

- n_sessions = **500** (target 500 if wall <30 min; else 200 OK)
- wall_time_s = **294.96**
- scale_note: Projected 500 @ 0.579s/session ≈ 290s; keeping n=500.
- k (depth) = **2**
- M hard (ShapeWalk max_rows) = **12** — not raised
- cue: kind=`HUB` + locator `slug=<hub-slug>`
- nodes/session ≥16 (actual = 35)
- gold: minimal evidence set within k≤2 of HUB (hub + 3 DOC + 1 TSK)
- Condition A: ShapeWalk; **caller admits all of offered X̃** (synthetic)
- Condition B: dump ALL observable nodes in session snapshot (no cap)
- Equal quality stratum: both score == 1.0
- RNG seed base = `20260904`; bootstrap seed = `42`

## Results — both-perfect stratum (PRIMARY)

- n both-perfect = **500**
- mean Â walk = **422.0**
- mean Â dump = **2356.0**
- mean Δ (Â_dump − Â_walk) = **1934.0**
- median Δ = **1934.0**
- 95% bootstrap CI = **[1934.0, 1934.0]**

## Results — full set

- n_ok = **500**
- mean score walk = **1.0**
- mean score dump = **1.0**
- mean Â walk = **422.0**
- mean Â dump = **2356.0**
- mean Δ = **1934.0**
- median Δ = **1934.0**
- 95% bootstrap CI = **[1934.0, 1934.0]**

## Pass/fail against the claim

**PASS**

On both-perfect stratum (n=500), mean Δ=1934.0000 > 0 and 95% CI [1934.0000, 1934.0000] excludes 0 — dump costs more action at equal quality.

## Notes

- This is a **synthetic-stratum pilot**, not the human-reviewed 200 from the full protocol.
- No LLM generate; task quality is gold-evidence coverage of admitted W.
- Primary comparison is on pairs where both score==1 (equal quality).

