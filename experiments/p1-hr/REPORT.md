# STM Prediction 1 — human-reviewed stratum (ShapeWalk vs dump)

Paper §10.1 (post-Sage). **Human-reviewed n=200** (not the synthetic pilot).

**Verdict:** `PASS`

## Honesty

human-reviewed by agent under user delegation; not author-blind

## Coefficient lock (SAME as prior P1 — not retuned)

```
Â = a·|W|² + b·tokens + c·0 + d·(1 − score)
a = 1.0, b = 1.0, c = 0.0, d = 10.0
d(empty, W) := |W|
tokens := Σ (len(title)+len(slug))
score := |gold ∩ W| / |gold|
```

## MemNet / operators

- **memnet-llm:** `0.19.3`
- **memnet.__file__:** `/workspace/stm-p1-hr/.venv/lib/python3.13/site-packages/memnet/__init__.py`
- **merge commit:** `eff05dc8a0ad5369e8d7e7f347db30b9300b04d6`
- **Operators only:** `open_session`, `MutateGate.apply`, `PinMapComposer.compose`, `close_session`
- **Not used:** Neo4j / Pi / droplet / LLM generate / rag_query
- **Call counts:** `{"open_session": 200, "MutateGate.apply": 200, "PinMapComposer.compose": 200, "close_session": 200}`

## Protocol

- n = **200** human-reviewed session graphs
- wall_time_s = **138.43**
- k (depth) = **2**, M (max_rows) = **12**
- cue: kind=`HUB` + locator `slug=<hub-slug>`
- Condition A: ShapeWalk; admit all offered rows
- Condition B: Dump all observable session nodes (bench fixture)
- distinct topology families = **17**
- checklist passes = **200**/200

## Topology family histogram

- `cap-bind-stress`: 15
- `wrong-branch-crowding`: 15
- `chain-of-hubs`: 12
- `deep-narrow`: 12
- `diamond`: 12
- `star`: 12
- `wide-shallow`: 12
- `asymmetric-spoke`: 11
- `broken-path-then-repair`: 11
- `dense-clique-with-gold-rim`: 11
- `fan-out-fan-in`: 11
- `hub-with-dead-ends`: 11
- `ladder`: 11
- `multi-root-one-legal-seed`: 11
- `noisy-sibling-hub`: 11
- `sparse-evidence`: 11
- `tree-with-gold-leaves`: 11

## Results — both-perfect stratum (PRIMARY)

- n_both_perfect = **170**
- n_walk_imperfect = **30**
- mean Â walk = **338.99411764705883**
- mean Â dump = **3271.4058823529413**
- mean Δ (Â_dump − Â_walk) = **2932.4117647058824**
- median Δ = **2847.0**
- 95% bootstrap CI = **[2780.3529411764707, 3086.3117647058825]**
- stdev Δ = **1018.8145971623117**

## Results — full set

- n_ok = **200**
- mean score walk = **0.8821666666666667**
- mean score dump = **1.0**
- mean Â walk = **371.37333333333333**
- mean Â dump = **3415.145**
- mean Δ = **3043.771666666667**
- median Δ = **2924.5**
- 95% bootstrap CI = **[2906.6375, 3183.2525]**

## Walk-imperfect stratum

- count = **30** (target ≤20% → ≤40)
- reasons (top): {"cap_binding": 30}

## Pass/fail

**PASS**

On both-perfect stratum (n=170), mean Δ=2932.4118 > 0 and 95% CI [2780.3529, 3086.3118] excludes 0 — dump costs more action at equal quality. Coefficients not retuned.

## Notes

- Prior synthetic pilot (n=500) had constant Δ=1934 (isomorphic clones); this stratum forbids that.
- Reviews in `reviews.jsonl` (200 notes).
- Coefficients locked identical to prior P1; not retuned after outcomes.
