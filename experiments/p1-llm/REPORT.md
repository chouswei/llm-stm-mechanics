# STM Prediction 1 — LLM-answer quality stratum (FIXED scorer)

Paper §10.1. Same human-reviewed $n=200$ graphs as [`../p1-hr/`](../p1-hr/). **$T=0$ is the predeclared primary band.** $T>0$ was not run.

**Verdict:** `PASS`

## Invalid prior scorer (do not cite)

An earlier LLM run scored $\mathrm{pred}$ against $\mathrm{gold}\cap W$ (extraction fidelity: did the model list the keys that were actually in $W$?). That run reported **200/200 LLM-perfect**. It is **INVALID**. It measures prompt extraction, not task quality against the full gold set. This directory records the **fixed** run that supersedes it. Do not cite 200/200 as the P1 LLM-quality claim.

## Coefficient lock (SAME as prior P1 — not retuned)

```
Â = a·|W|² + b·tokens + c·0 + d·(1 − score_llm)
a = 1.0, b = 1.0, c = 0.0, d = 10.0
d(empty, W) := |W|
tokens := Σ (len(title)+len(slug))
score_llm := |pred ∩ full_gold_keys| / |full_gold_keys|
full_gold_keys := ALL graph.gold_slugs   # NOT gold∩W
```

## Protocol

- Graphs: p1-hr $n=200$ (agent-reviewed under user delegation; **not author-blind**)
- **memnet-llm:** `0.19.4`
- LLM: OpenRouter `openai/gpt-4o-mini`, base `https://openrouter.ai/api/v1`, $T=0$ greedy
- Condition A: ShapeWalk `pin_map` ($M=12$, $k=2$, cue kind `HUB`)
- Condition B: dump all observable session nodes (bench fixture; not a product dump of $S$)
- Prompt-only KEY on $\mathrm{gold}\cap W$
- Equal quality: both `score_llm == 1.0` on **full gold**
- $T>0$: **OPEN**

## Results — both-perfect stratum (PRIMARY; equal LLM quality)

- n_both_perfect = **170** (both `score_llm==1.0` on full gold)
- n_walk_imperfect_llm = **30**
- n_dump_imperfect_llm = **0**
- mean Â walk = **338.99411764705883**
- mean Â dump = **3271.4058823529413**
- mean Δ (Â_dump − Â_walk) = **2932.4117647058824**
- median Δ = **2847.0** (same both-perfect Â as p1-hr gold-presence: $\ell_{\mathrm{task}}=0$ on both sides)
- 95% bootstrap CI = **[2780.3529411764707, 3086.3117647058825]** (excludes 0)
- stdev Δ = **1018.8145971623117**

On this equal-quality slice the action numbers match the p1-hr both-perfect gold-presence slice because the $d\cdot(1-\mathrm{score})$ term is zero for both conditions. The **score** itself is now LLM answer quality against full gold, not gold presence in $W$.

## Verification

Session **170** (`cap-bind-stress`, 5 gold slugs): walk `score_llm=0.20` ($1/5$) versus dump `1.00`. Walk $W$ is $M$-capped; only one gold key is resident, so the model cannot recover full gold. Dump $W$ contains all gold keys. This is exactly the case the invalid $\mathrm{gold}\cap W$ scorer would have called “perfect” if the model listed the single resident key.

## Pass/fail

**PASS**

On both-perfect stratum ($n=170$), mean Δ=2932.4118 > 0 and 95% CI [2780.3529, 3086.3118] excludes 0 — dump costs more action at equal LLM-answer quality (full-gold scorer). Coefficients not retuned.

## Honesty

- Not author-blind (graphs from p1-hr).
- $T>0$ OPEN.
- No API keys in this repo.

## How to re-run

See [`README.md`](README.md). Requires `OPENROUTER_API_KEY` in the environment (never commit it). `--check-scorer` needs no key.
