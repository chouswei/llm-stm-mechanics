# STM Prediction 1 — harder LLM-answer quality (evidence vs noise)

Paper §10.1. Same human-reviewed $n=200$ graphs as [`../p1-hr/`](../p1-hr/). Sage author-blind **ACCEPT after regen**. **$T=0$ is the predeclared primary band.** $T>0$ was not run.

This stratum is **harder** than closed KEY-extraction ([`../p1-llm/`](../p1-llm/)). Keep that KEY result; do not replace it. This closes a harder discrimination task.

**Verdict:** `PASS`

## What is harder

- **No** `KEY=` / `key:` markers.
- Prompt-only `evidence: 'E{session_i}-{slug}'` on $\mathrm{gold}\cap W$.
- Prompt-only `noise: 'N{session_i}-{slug}'` on non-gold nodes in $W$.
- Task: list every evidence value, ignore noise; alphabetical, comma-separated.

## Coefficient lock (SAME as prior P1 — not retuned)

```
Â = a·|W|² + b·tokens + c·0 + d·(1 − score_llm)
a = 1.0, b = 1.0, c = 0.0, d = 10.0
d(empty, W) := |W|
tokens := Σ (len(title)+len(slug))
score_llm := |pred ∩ full_gold_evidence| / |full_gold_evidence|
full_gold_evidence := E{session_i}-{slug} for ALL graph.gold_slugs   # NOT gold∩W
noise_leak := any N… token in pred
equal quality := both score_llm==1.0 AND no noise_leak
```

GitHub math form: $\mathrm{score\_llm}=\lvert\mathrm{pred}\cap\mathrm{full\_gold\_evidence}\rvert/\lvert\mathrm{full\_gold\_evidence}\rvert$.

## Protocol

- Graphs: p1-hr $n=200$ (Sage author-blind **ACCEPT after regen**)
- **memnet-llm:** `0.19.4`
- LLM: OpenRouter `openai/gpt-4o-mini`, base `https://openrouter.ai/api/v1`, $T=0$ greedy
- Condition A: ShapeWalk `pin_map` ($M=12$, $k=2$, cue kind `HUB`)
- Condition B: dump all observable session nodes (bench fixture; not a product dump of $S$)
- Equal quality: both `score_llm == 1.0` on **full gold evidence** and **no** `noise_leak`
- $T>0$: **OPEN**

## Results — both-perfect stratum (PRIMARY; equal LLM quality; post-regen)

- n_both_perfect = **161** (both `score_llm==1.0` and no noise leak)
- n_noise_leak = **0**
- n_walk_imperfect_llm = **35**
- n_dump_imperfect_llm = **9**
- mean Δ (Â_dump − Â_walk) ≈ **2940.65**
- 95% bootstrap CI = **[2782.09, 3098.31]** (excludes 0)
- elapsed $\sim 674.8$s

The both-perfect slice is not the KEY-extraction $n=170$ set. Do not mix Δ with [`../p1-llm/`](../p1-llm/).

## Pass/fail

**PASS**

On both-perfect stratum ($n=161$), mean Δ≈2940.65 > 0 and 95% CI [2782.09, 3098.31] excludes 0 — dump costs more action at equal LLM-answer quality (full-gold evidence scorer; no noise leak). Coefficients not retuned. This closes a harder discrimination task than KEY-extraction.

## Honesty

- Sage author-blind **ACCEPT after regen** (graphs from p1-hr / p1-blind).
- KEY-extraction [`../p1-llm/`](../p1-llm/) remains the closed marker-assisted full-gold run.
- $T>0$ OPEN.
- No API keys in this repo.

## How to re-run

See [`README.md`](README.md). Requires `OPENROUTER_API_KEY` in the environment (never commit it). `--check-scorer` needs no key.
