# STM Prediction 2 — M-cap multiplier detects a wrong Shape

Paper §10.2 (post-Sage). Cheap analysis half: no LLM generate.

**Verdict:** `PASS`

PASS: (a)(b)(c) hold; λ̂ beats raw |W| on AUROC/accuracy

## Claim

λ̂_M is an account diagnostic (finite-difference of preregistered J), not a KKT multiplier read off the engine. Engine caps stay hard rejects.

Prediction: λ̂_M becomes positive when the row cap is active and marginally relaxing M would improve the task objective. Wrongly centred / diffuse Shapes produce positive λ̂_M more often than correctly centred compact Shapes.

## memnet-llm version and API

- **memnet-llm:** `0.19.3`
- **memnet.__file__:** `/workspace/stm-p2/.venv/lib/python3.13/site-packages/memnet/__init__.py`
- **merge commit:** `eff05dc8a0ad5369e8d7e7f347db30b9300b04d6` (same as green P3)
- **Operators (count=4):** `open_session`, `MutateGate.apply`, `PinMapComposer.compose`, `close_session`
- **Call counts:** `{"open_session": 200, "MutateGate.apply": 200, "PinMapComposer.compose": 2000, "close_session": 200}`
- **Not used:** Neo4j, Pi, droplet, InvenTree, soft-buy M inside engine
- **Analysis knob:** compose `max_rows` M only; engine store caps remain hard rejects

## Preregistered protocol

- n_sessions = **200**
- M grid = `[8, 12, 16, 24, 32]`, δ = grid step (**4** for 8→12/12→16; **8** for 16→24/24→32; preregistered one-step FD), depth = **2**
- Equivalence band: |λ̂| < **0.005** treated as zero
- J(M) = `(1 - score) + 0.01*|W|, score=|gold∩W|/|gold|`
- λ̂_M = −(J(M+δ)−J(M))/δ with δ = M_next − M
- Cap active / truncated: gold ⊈ W(M). W(M) = admitted rows (admit all of X̃).
- CORRECT cue: kind=HUB + true hub slug (compact Shape). WRONG cue: kind=HUB + distractor hub (diffuse / off-centre).
- RNG seed base = `20260904`
- elapsed = **143.17s**

## Tests

### (a) Truncated + score improves ⇒ λ̂ > band

- n = 463, n_positive = 449, rate = **0.9697624190064795**, majority = **True**

### (b) Gold inside (slack) ⇒ λ̂ ≤ band

- n = 667, n_nonpositive = 667, rate = **1.0**, majority = **True**
- positive-with-slack rate = 0.0

### (c) WRONG positive-λ̂ rate > CORRECT (clear gap)

- CORRECT pos rate = **0.16625**
- WRONG pos rate = **0.395**
- gap = **0.22875**, clear gap = **True**
- per-M: `{"8": {"CORRECT_pos_rate": 0.665, "WRONG_pos_rate": 0.0}, "12": {"CORRECT_pos_rate": 0.0, "WRONG_pos_rate": 0.0}, "16": {"CORRECT_pos_rate": 0.0, "WRONG_pos_rate": 0.58}, "24": {"CORRECT_pos_rate": 0.0, "WRONG_pos_rate": 1.0}}`

### Null: λ̂ vs raw |W| for identifying wrong Shapes

- AUROC(λ̂) = **0.599359375**, AUROC(|W|) = **0.5**
- acc(positive λ̂ ⇒ wrong) = **0.614375**, acc(|W|≥median ⇒ wrong) = **0.5** (median_W=16.0)
- λ̂ better than |W| = **True**

## State clearly

**λ̂ is an account diagnostic** computed from the preregistered finite-difference of J over compose `max_rows`. **The engine still hard-rejects** on its store caps; this protocol does not soft-buy M inside the engine.

## Paths

- script: `/workspace/stm-p2/run_p2.py`
- results: `/workspace/stm-p2/results.json`
- report: `/workspace/stm-p2/REPORT.md`

