# STM Prediction 1 — human-reviewed stratum (ShapeWalk vs dump)

Paper §10.1. **Human-reviewed n=200** (not the synthetic pilot). Sage author-blind **ACCEPT after regen**.

**Verdict:** `PASS`

## Honesty

Sage author-blind ACCEPT after regen. Reviewer did not author graphs. Protocol and sign-off: [`../p1-blind/SAGE_SIGNOFF.md`](../p1-blind/SAGE_SIGNOFF.md). Eight `asymmetric-spoke` graphs regenerated (non-gold hop-1 decoy) after AUTO_DUMP; see [`../p1-blind/REGEN_8.md`](../p1-blind/REGEN_8.md).

## Coefficient lock (SAME as prior P1 — not retuned)

```
Â = a·|W|² + b·tokens + c·0 + d·(1 − score)
a = 1.0, b = 1.0, c = 0.0, d = 10.0
d(empty, W) := |W|
tokens := Σ (len(title)+len(slug))
score := |gold ∩ W| / |gold|
```

## MemNet / operators

- **Post-regen gold-presence re-run:** `memnet-llm` `0.19.4` (coefficients unchanged)
- **Original harness record:** `memnet-llm` `0.19.3` @ `eff05dc8a0ad5369e8d7e7f347db30b9300b04d6`
- **Operators only:** `open_session`, `MutateGate.apply`, `PinMapComposer.compose`, `close_session`
- **Not used:** Neo4j / Pi / droplet / LLM generate / rag_query

## Protocol

- n = **200** human-reviewed session graphs
- k (depth) = **2**, M (max_rows) = **12**
- cue: kind=`HUB` + locator `slug=<hub-slug>`
- Condition A: ShapeWalk; admit all offered rows
- Condition B: Dump all observable session nodes (bench fixture)
- distinct topology families = **17**
- checklist passes = **200**/200 (blind checklist also 200/200; 100% agreement)

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

## Results — both-perfect stratum (PRIMARY, post-regen)

Authoritative post-regen (`memnet-llm` 0.19.4; reconstructed; full per-session dump not re-attached):

- n_both_perfect = **170**
- n_walk_imperfect = **30**
- mean Δ (Â_dump − Â_walk) ≈ **2930.59**
- 95% bootstrap CI = **[2778.71, 3084.10]** (excludes 0)

Pre-regen (same lock; 0.19.3 record, before the eight hop-1 decoys): mean Δ = 2932.4118; CI [2780.3529, 3086.3118]; mean Â walk = 338.9941; mean Â dump = 3271.4059; median Δ = 2847.0. Do not mix those Â means with the post-regen Δ.

## Walk-imperfect stratum

- count = **30** (target ≤20% → ≤40)
- reasons (top): {"cap_binding": 30}

## Pass/fail

**PASS**

On both-perfect stratum (n=170), post-regen mean Δ≈2930.59 > 0 and 95% CI [2778.71, 3084.10] excludes 0 — dump costs more action at equal quality. Coefficients not retuned.

## Notes

- Prior synthetic pilot (n=500) had constant Δ=1934 (isomorphic clones); this stratum forbids that.
- Authoring notes in `reviews.jsonl` are not the blind pack reviews.
- Coefficients locked identical to prior P1; not retuned after outcomes.
