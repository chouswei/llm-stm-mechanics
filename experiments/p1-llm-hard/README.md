# P1 LLM-answer quality — harder stratum (evidence vs noise)

Record of Prediction 1 on the p1-hr $n=200$ graphs with an LLM generate at $T=0$. Graphs: Sage author-blind **ACCEPT after regen**. Harder than closed KEY-extraction ([`../p1-llm/`](../p1-llm/)): no `KEY=` / `key:` markers; prompt-only evidence and noise tags; list evidence, ignore noise.

Post-regen primary: $n=161$ both-perfect (score $1.0$ and no noise leak), mean $\Delta\approx 2940.65$, 95% CI $[2782.09, 3098.31]$. $n_{\mathrm{noise\_leak}}=0$.

**Authoritative numbers:** [`results.summary.json`](results.summary.json) / [`REPORT.md`](REPORT.md). Do not overwrite them from a different model, package, or scorer. Do not replace the KEY-extraction record.

## Scorer

$$
\mathrm{score\_llm} = \lvert\mathrm{pred}\cap\mathrm{full\_gold\_evidence}\rvert / \lvert\mathrm{full\_gold\_evidence}\rvert
$$

`full_gold_evidence` = `E{session_i}-{slug}` for **all** `graph.gold_slugs`. Not $\mathrm{gold}\cap W$.

Prompt-only evidence tags are still restricted to $\mathrm{gold}\cap W$. Noise tags `N{session_i}-{slug}` mark non-gold in $W$. `noise_leak` if any `N…` appears in `pred`. Equal-quality gate: both $\mathrm{score\_llm}=1.0$ **and** no noise leak.

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
.venv/bin/python experiments/p1-llm-hard/run_p1_llm_hard.py
```

Live re-runs write `results.live.json` by default. They do **not** overwrite `results.summary.json` unless `P1_LLM_HARD_WRITE=1`.

Scorer self-check (no API, no MemNet):

```bash
python3 experiments/p1-llm-hard/run_p1_llm_hard.py --check-scorer
```

Optional env: `OPENROUTER_BASE_URL` (default `https://openrouter.ai/api/v1`), `P1_LLM_MODEL` (default `openai/gpt-4o-mini`). $T>0$ on this harder task is [`../p1-tgt0/`](../p1-tgt0/). KEY-extraction $T>0$ was not run.
