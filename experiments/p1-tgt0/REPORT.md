# STM Prediction 1 — T>0 LLM-answer quality band (harder evidence vs noise)

Paper §10.1 temperature condition. Same harder evidence-vs-noise task as `p1-llm-hard` (NOT KEY-extraction). Coefficients locked (not retuned).

**Verdict (PRIMARY strict):** `PASS`
**Verdict (RELAXED secondary):** `PASS`

## Contrast: T=0 harder PASS vs this T>0 band

| | T=0 harder (`p1-llm-hard`) | **T>0 band (this run)** |
|---|---|---|
| Temperature | 0.0 (greedy) | **0.8** |
| Seeds / (graph, condition) | 1 | **20** |
| Equal-quality gate | score_llm==1.0 & no leak | score_mean==1.0 & no leak_any (strict) |
| n_both_perfect (strict) | 161 | **160** |
| mean Δ | 2940.645962732919 | **2939.11875** |
| 95% CI | [2782.086956521739, 3098.3105590062114] | **[2779.9875, 3096.9]** |
| Verdict | PASS | **PASS** |

T=0 harder stratum closed PASS (n_both_perfect=161). This run is the §10.1 temperature band at matched answer quality using score_mean over seeds.

## Claim

At equal *LLM answer quality* (strict: score_mean==1.0 and no noise_leak_any on both sides), bounded ShapeWalk has lower estimated action Â than a dump of the same observable material — under T>0 stochastic decoding.

## Coefficient lock (SAME as prior P1 — not retuned)

```
Â = a·|W|² + b·tokens + c·0 + d·(1 − score_mean)
a = 1.0, b = 1.0, c = 0.0, d = 10.0
d(empty, W) := |W|
tokens := Σ (len(title)+len(slug)) on admitted rows (fixed across seeds)
score_mean := mean_s score_llm_s ; score_llm_s := |pred_s ∩ full_gold_evidence| / |full_gold_evidence|
noise_leak_any := any_s (N… token in pred_s)
```

## MemNet / operators / LLM

- **memnet-llm:** `0.19.4`
- **merge commit:** `eff05dc8a0ad5369e8d7e7f347db30b9300b04d6`
- **LLM:** OpenRouter `openai/gpt-4o-mini` (T=0.8, n_seeds=20)
- **LLM base:** `https://openrouter.ai/api/v1`
- **Operators only:** `open_session`, `MutateGate.apply`, `PinMapComposer.compose`, `close_session`
- **Not used:** Neo4j / rag_query / product dump S
- **Call counts:** `{"open_session": 200, "MutateGate.apply": 200, "PinMapComposer.compose": 200, "close_session": 200}`
- **LLM calls:** `8001` (retries=0)

## Protocol

- n = **200** (reused post-regen p1-hr graphs)
- wall_time_s = **1343.25**
- temperature = **0.8**, n_seeds = **20**
- k (depth) = **2**, M (max_rows) = **12**
- cue: kind=`HUB` + locator `slug=<hub-slug>`
- Condition A: ShapeWalk pin_map; admit all offered rows as W
- Condition B: dump all observable session nodes (bench fixture)
- Prompt materialisation (prompt-only; no product identity mutate):
  - gold∩W → `evidence: 'E{session_i}-{slug}'`
  - non-gold in W → `noise: 'N{session_i}-{slug}'`
  - **no** `KEY=` / `key:`
- **score_llm denominator: FULL `graph.gold_slugs`**
- Per seed: score_llm_s; per condition: score_mean, noise_leak_any
- Â uses ell_task = 1 − score_mean; |W|/tokens from admitted W (same each seed)
- Primary: both score_mean==1.0 AND NOT noise_leak_any
- Relaxed secondary: both score_mean≥0.95 AND NOT noise_leak_any

## Results — both-perfect LLM stratum (PRIMARY strict)

- n_both_perfect = **160**
- n_noise_leak (either side, full ok set) = **0**
- n_walk_imperfect_llm = **39**
- n_dump_imperfect_llm = **9**
- mean Â walk = **342.1625**
- mean Â dump = **3281.28125**
- mean Δ (Â_dump − Â_walk) = **2939.11875**
- median Δ = **2847.0**
- 95% bootstrap CI = **[2779.9875, 3096.9]**
- stdev Δ = **1009.831720955743**

## Results — relaxed band (SECONDARY; not the strict claim)

- n_relaxed = **161**
- mean Δ = **2940.644409937888**
- median Δ = **2847.0**
- 95% bootstrap CI = **[2782.086956521739, 3098.3105590062114]**
- secondary verdict = **PASS**

## Pass/fail

**PRIMARY:** PASS — On both-perfect T>0 stricter stratum (n=160), mean Δ=2939.1188 > 0 and 95% CI [2779.9875, 3096.9000] excludes 0. Coefficients not retuned.

**RELAXED (secondary):** PASS — n=161, mean Δ=2940.6444, CI excludes 0.

## Notes

- Graphs: post-regen p1-hr specs.
- Coefficients locked identical to prior P1; not retuned after outcomes.
- Prompt-only materialisation; product identity not mutated.
- Seed count = 20; temperature = 0.8.
