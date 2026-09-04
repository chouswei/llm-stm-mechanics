# P1 LLM-answer quality stratum (FIXED full-gold scorer)

Record of Prediction 1 on the p1-hr $n=200$ graphs with an LLM generate at $T=0$. Graphs: Sage author-blind **ACCEPT after regen**. Post-regen primary: $n=170$, mean $\Delta\approx 2930.59$, 95% CI $[2778.71, 3084.10]$.

**Authoritative numbers:** [`results.summary.json`](results.summary.json) / [`REPORT.md`](REPORT.md). Do not overwrite them from a different model, package, or scorer.

## Scorer (FIXED)

$$
\mathrm{score\_llm} = |\mathrm{pred} \cap \mathrm{full\_gold\_keys}| / |\mathrm{full\_gold\_keys}|
$$

`full_gold_keys` = **all** `graph.gold_slugs`. Not $\mathrm{gold}\cap W$.

Prompt-only KEY is still restricted to $\mathrm{gold}\cap W$ (the model is not asked for keys that are not in $W$). Quality is judged against the full gold set.

## Invalid prior (do not cite)

A previous run scored $\mathrm{pred}$ against $\mathrm{gold}\cap W$ (extraction fidelity) and reported $200/200$ LLM-perfect. That is **invalid**. This directory supersedes it.

## Stack

- `memnet-llm==0.19.4`
- Graphs: [`../p1-hr/`](../p1-hr/)
- LLM: OpenRouter `openai/gpt-4o-mini`, $T=0$
- Coefficients $a=1,b=1,c=0,d=10$ — **not retuned**

## Re-run (requires your key)

No keys are stored in this repo. Export `OPENROUTER_API_KEY` in the environment only.

```bash
python3 -m venv .venv
.venv/bin/pip install "memnet-llm==0.19.4"
export OPENROUTER_API_KEY=  # your key; never commit it
.venv/bin/python experiments/p1-llm/run_p1_llm.py
```

Live re-runs write `results.live.json` by default. They do **not** overwrite `results.summary.json` unless `P1_LLM_WRITE=1`.

Scorer self-check (no API, no MemNet):

```bash
python3 experiments/p1-llm/run_p1_llm.py --check-scorer
```

Optional env: `OPENROUTER_BASE_URL` (default `https://openrouter.ai/api/v1`), `P1_LLM_MODEL` (default `openai/gpt-4o-mini`). $T>0$ is not this script; it remains OPEN.
