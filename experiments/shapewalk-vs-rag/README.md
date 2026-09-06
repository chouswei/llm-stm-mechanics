# ShapeWalk vs Dump vs RAG top-k (bake-off scaffold)

Protocol + harness for a three-arm comparison on the p1-hr $n=200$ graphs: **ShapeWalk** (`pin_map`), **Dump** (P1 continuity), and **RAG lexical top-$k$** (no graph walk). Task and scorer match [`../p1-llm-hard/`](../p1-llm-hard/) (evidence vs noise; full-gold evidence + `noise_leak` gate). Coefficients $a=1,b=1,c=0,d=10$ — **not retuned**.

**Lock:** [`PROTOCOL.md`](PROTOCOL.md) is authoritative. Do not retune $k$, Jaccard, $\widehat{\mathcal{A}}$ coeffs, or the PASS band after seeing outcomes.

**Authoritative numbers:** TBD until the first locked live run. This directory ships **no** `results.summary.json`. Do not invent a PASS.

## Stack

- `memnet-llm==0.19.4` (package pin; no SemVer $a$/$b$ claim)
- Graphs: [`../p1-hr/`](../p1-hr/) (Sage author-blind ACCEPT after regen)
- LLM (live only): OpenRouter `openai/gpt-4o-mini`, $T=0$
- $k_{\mathrm{RAG}}=M_{\mathrm{walk}}=12$ (see PROTOCOL)

## Re-run

No keys are stored in this repo. Export `OPENROUTER_API_KEY` in the environment only. Never commit it.

Scorer + RAG determinism self-check (no API, no MemNet):

```bash
python3 experiments/shapewalk-vs-rag/run_shapewalk_vs_rag.py --check-scorer
```

Dry mode builds $W$ for each arm from p1-hr graph JSON (no LLM). ShapeWalk in dry mode is a **BFS $k$-hop cap-$M$ stand-in**, not `pin_map`. RAG lexical top-$k$ is real and deterministic. Prints $|W|$ / $\mathrm{gold}\cap W$ stats. Not a paper verdict.

```bash
python3 experiments/shapewalk-vs-rag/run_shapewalk_vs_rag.py --dry
# optional: --limit 20
```

Live LLM (needs `OPENROUTER_API_KEY`; full three-arm generate is not shipped as a 200-session driver in this scaffold):

```bash
python3 -m venv .venv
.venv/bin/pip install "memnet-llm==0.19.4"
export OPENROUTER_API_KEY=  # your key; never commit it
.venv/bin/python experiments/shapewalk-vs-rag/run_shapewalk_vs_rag.py
```

Live writes [`results.live.json`](results.live.json) by default. It does **not** overwrite `results.summary.json` unless `WRITE=1` (env `SHAPEWALK_VS_RAG_WRITE=1`). Do not set `WRITE=1` from a different model, package, or scorer.

Optional env: `OPENROUTER_BASE_URL` (default `https://openrouter.ai/api/v1`), `P1_LLM_MODEL` (default `openai/gpt-4o-mini`).

## What this is not

Not SemVer. Not embedding-RAG. Not a proof RAG is always worse. Not a replacement of [`../p1-llm-hard/results.summary.json`](../p1-llm-hard/results.summary.json).
