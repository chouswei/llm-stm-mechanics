# ShapeWalk vs Dump vs RAG top-k — $T>0$ band

Protocol + **live three-arm OpenRouter driver** on the p1-hr $n=200$ graphs, same arms as [`../shapewalk-vs-rag/`](../shapewalk-vs-rag/) (ShapeWalk `pin_map`, Dump, lexical Jaccard top-$k=12$), scored on the [`../p1-tgt0/`](../p1-tgt0/) temperature band: $T=0.8$, $n_{\mathrm{seeds}}=20$, $\mathrm{score\_mean}$, $\mathrm{noise\_leak\_any}$.

**Parent $T=0$ lock:** [`../shapewalk-vs-rag/results.summary.json`](../shapewalk-vs-rag/results.summary.json) (**PASS**; $n_{\mathrm{triple}}=83$). Do **not** overwrite it. Do not retune $k$, Jaccard, or $a,b,c,d$.

**Lock:** [`PROTOCOL.md`](PROTOCOL.md) is authoritative. Authoritative $\widehat{\mathcal{A}}$ / PASS numbers do **not** exist in this directory until a locked live run is written under `SHAPEWALK_VS_RAG_TGT0_WRITE=1`. There is **no** fabricated `results.summary.json` in the scaffold.

A live re-run writes [`results.live.json`](results.live.json) by default.

## Stack

- `memnet-llm==0.19.5` preferred (`0.19.4` OK if noted on the run payload; package pin; no SemVer $a$/$b$ claim)
- Graphs: [`../p1-hr/`](../p1-hr/) (Sage author-blind ACCEPT after regen)
- LLM (live only): OpenRouter `openai/gpt-4o-mini`, $T=0.8$, $n_{\mathrm{seeds}}=20$ per (session, arm) — **same as** `p1-tgt0`
- $k_{\mathrm{RAG}}=M_{\mathrm{walk}}=12$ (lexical PROTOCOL; not retuned)
- $W$ builders: imported from [`../shapewalk-vs-rag/run_shapewalk_vs_rag.py`](../shapewalk-vs-rag/run_shapewalk_vs_rag.py)

## Cost

Full protocol: $200\times 3\times 20$ = **12 000** generate calls (plus retries). Use `--limit` for smoke. That smoke is **not** a protocol verdict.

## Re-run

No keys are stored in this repo. Export `OPENROUTER_API_KEY` in the environment only. Never commit it.

Scorer + RAG determinism + $T>0$ gates (no API; lexical $W$ checks reused):

```bash
python3 experiments/shapewalk-vs-rag-tgt0/run_shapewalk_vs_rag_tgt0.py --check-scorer
```

Dry mode builds $W$ for each arm from p1-hr graph JSON (no LLM). ShapeWalk in dry mode is a **BFS $k$-hop cap-$M$ stand-in**, not `pin_map`. RAG lexical top-$k$ is real and deterministic. Prints $|W|$ / $\mathrm{gold}\cap W$ stats. Not a paper verdict.

```bash
python3 experiments/shapewalk-vs-rag-tgt0/run_shapewalk_vs_rag_tgt0.py --dry
# optional: --limit 20
```

Live three-arm generate (needs `OPENROUTER_API_KEY`; default is the full $n=200$ protocol, $20$ seeds per arm):

```bash
python3 -m venv .venv
.venv/bin/pip install "memnet-llm==0.19.5"
export OPENROUTER_API_KEY=  # your key; never commit it
.venv/bin/python experiments/shapewalk-vs-rag-tgt0/run_shapewalk_vs_rag_tgt0.py
# optional smoke: --limit 1  (60 generate calls; not a protocol verdict)
```

ShapeWalk **live** uses real `PinMapComposer.compose` (cue kind `HUB`, locators `[("slug", hub_slug)]`, `depth=2`, `max_rows=12`, `active_only=True`; admit node rows only). Dump serialises all observable session nodes (uncapped). RAG stays deterministic token-Jaccard top-$k=12$ with **no** `hid` in features or sort keys. $W$ is built once per session; the $20$ seeds are generate draws on that $W$.

Per seed the driver records full-gold `score_llm` and `noise_leak`. Per arm: `score_mean`, `noise_leak_any`, and $\widehat{\mathcal{A}}$ with $\ell=1-\mathrm{score\_mean}$. Summary fields: $n_{\mathrm{triple}}$, mean $\Delta_{\mathrm{RAG}}$ / $\Delta_{\mathrm{dump}}$, bootstrap CIs ($B=10000$, seed $42$), PASS/FAIL per PROTOCOL.

Live writes [`results.live.json`](results.live.json) by default. It does **not** write `results.summary.json` unless `SHAPEWALK_VS_RAG_TGT0_WRITE=1`. Do not set `WRITE=1` from a different model, package, temperature, seed count, or scorer. This driver **never** writes the parent $T=0$ summary.

Optional env: `OPENROUTER_BASE_URL` (default `https://openrouter.ai/api/v1`), `P1_LLM_MODEL` (default `openai/gpt-4o-mini`).

## What this is not

Not SemVer. Not a replacement of the $T=0$ lexical PASS. Not a replacement of [`../p1-tgt0/results.summary.json`](../p1-tgt0/results.summary.json). Not embedding $T>0$ (still later). Not an OM theorem. Primary claim is equal-quality **triples** under $\mathrm{score\_mean}=1.0$ and no $\mathrm{noise\_leak\_any}$, not pairwise rescue.
