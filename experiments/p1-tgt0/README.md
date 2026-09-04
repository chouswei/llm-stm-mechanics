# P1 LLM-answer quality — $T>0$ band (harder evidence vs noise)

Paper §10.1 temperature condition. Same harder evidence-versus-noise task as [`../p1-llm-hard/`](../p1-llm-hard/) (not KEY-extraction). Coefficients locked, **not retuned**.

- LLM: OpenRouter `openai/gpt-4o-mini`, $T=0.8$, $n_{\mathrm{seeds}}=20$
- Primary: both $\mathrm{score\_mean}=1.0$ and no $\mathrm{noise\_leak\_any}$; $n=160$; mean $\Delta\approx 2939.12$; $95\%$ CI $[2779.9875, 3096.9]$
- Relaxed secondary only: $n=161$; mean $\Delta\approx 2940.64$
- $n_{\mathrm{noise\_leak}}=0$

**Authoritative numbers:** [`results.summary.json`](results.summary.json) / [`REPORT.md`](REPORT.md). Do not overwrite them from a different model, package, or scorer. Do not replace the $T=0$ harder record or the KEY-extraction record.

## Scorer

Per seed, $\mathrm{score\_llm}$ is full-gold evidence recall (same as `p1-llm-hard`). Per condition, $\mathrm{score\_mean}$ is the mean over $20$ seeds; $\mathrm{noise\_leak\_any}$ if any seed leaks an $N\ldots$ token. $\widehat{\mathcal{A}}$ uses $\ell=1-\mathrm{score\_mean}$.

## Stack

- `memnet-llm==0.19.4`
- Graphs: [`../p1-hr/`](../p1-hr/)
- LLM: OpenRouter `openai/gpt-4o-mini`, $T=0.8$, $n_{\mathrm{seeds}}=20$
- Coefficients $a=1,b=1,c=0,d=10$ — **not retuned**

## Re-run (requires your key)

The live $200$-session $\times$ $20$-seed driver is **not** shipped here (that harness lived off-repo for the paper run). This directory's `run_p1_tgt0.py` is the protocol note and scorer lock. Authoritative counts stay in `results.summary.json`.

No keys are stored in this repo. Export `OPENROUTER_API_KEY` in the environment only.

```bash
python3 experiments/p1-tgt0/run_p1_tgt0.py --check-scorer
```
