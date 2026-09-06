# ShapeWalk vs Dump vs Embedding RAG top-k

Protocol + **live three-arm OpenRouter driver** on the p1-hr $n=200$ graphs: **ShapeWalk** (`PinMapComposer.compose` / `pin_map`), **Dump** (P1 continuity), and **Embedding RAG top-$k$** (MiniLM cosine; no graph walk). Lexical Jaccard RAG is **not** in this live loop; the parent lock is [`../shapewalk-vs-rag/`](../shapewalk-vs-rag/) (**PASS**; do not overwrite).

Task and scorer match [`../p1-llm-hard/`](../p1-llm-hard/) (evidence vs noise; full-gold evidence + `noise_leak` gate). Coefficients $a=1,b=1,c=0,d=10$ — **not retuned**. $k=12$ is the same cap as lexical; the lexical Jaccard definition is unchanged.

**Lock:** [`PROTOCOL.md`](PROTOCOL.md) is authoritative. Do not retune $k$, the MiniLM embedder, $\widehat{\mathcal{A}}$ coeffs, or the PASS band after seeing outcomes.

**Authoritative numbers:** [`results.summary.json`](results.summary.json) / [`REPORT.md`](REPORT.md). Do not overwrite them from a different model, package, embedder, or scorer. A live re-run writes [`results.live.json`](results.live.json) by default. Do **not** treat `results.live.json` as the paper record unless `SHAPEWALK_VS_RAG_EMBED_WRITE=1` after a locked protocol run.

## Stack

- `memnet-llm==0.19.5` preferred (`0.19.4` OK if noted on the run payload; package pin; no SemVer $a$/$b$ claim)
- `sentence-transformers` (local `all-MiniLM-L6-v2`; no OpenAI embed API in v1)
- Graphs: [`../p1-hr/`](../p1-hr/) (Sage author-blind ACCEPT after regen)
- LLM (live only): OpenRouter `openai/gpt-4o-mini`, $T=0$ — generate only
- $k_{\mathrm{RAG}}=M_{\mathrm{walk}}=12$ (see PROTOCOL)

## Re-run

No keys are stored in this repo. Export `OPENROUTER_API_KEY` in the environment only. Never commit it.

Scorer + cosine rank + (if MiniLM is installed) embed determinism on a tiny fixture (no API):

```bash
python3 experiments/shapewalk-vs-rag-embed/run_shapewalk_vs_rag_embed.py --check-scorer
```

Dry mode builds $W$ for each arm from p1-hr graph JSON (no LLM). ShapeWalk in dry mode is a **BFS $k$-hop cap-$M$ stand-in**, not `pin_map`. Embedding RAG uses **real MiniLM** when `sentence-transformers` is installed; otherwise the script prints a clear skip and does not pretend to have embed $W$-stats.

```bash
python3 -m venv .venv
.venv/bin/pip install sentence-transformers
python3 experiments/shapewalk-vs-rag-embed/run_shapewalk_vs_rag_embed.py --dry
# optional: --limit 20
```

Live three-arm generate (needs `OPENROUTER_API_KEY` and MiniLM; default is the full $n=200$ protocol). OpenRouter is used for **generate only**, not embeddings:

```bash
python3 -m venv .venv
.venv/bin/pip install "memnet-llm==0.19.5" sentence-transformers
export OPENROUTER_API_KEY=  # your key; never commit it
.venv/bin/python experiments/shapewalk-vs-rag-embed/run_shapewalk_vs_rag_embed.py
# optional smoke: --limit 2  (not a protocol verdict)
```

ShapeWalk **live** uses real `PinMapComposer.compose` (cue kind `HUB`, locators `[("slug", hub_slug)]`, `depth=2`, `max_rows=12`, `active_only=True`; admit node rows only). Dump serialises all observable session nodes (uncapped). Embedding RAG stays local MiniLM cosine top-$k=12$ with **no** `hid` / nick in embed texts and **no** vectors on `pin_map`.

Per session the driver records $|W|$, $\mathrm{gold}\cap W$, `score_llm`, `noise_leak`, and $\widehat{\mathcal{A}}$ for each arm. Summary fields: $n_{\mathrm{pair}}$ (walk+embed equal-quality), mean $\Delta_{\mathrm{embed}}$, bootstrap CI ($B=10000$, seed $42$), secondary walk+Dump pairwise, PASS/FAIL per PROTOCOL.

Live writes [`results.live.json`](results.live.json) by default. It does **not** write `results.summary.json` unless `SHAPEWALK_VS_RAG_EMBED_WRITE=1`. Do not set `WRITE=1` from a different model, package, embedder, or scorer.

Optional env: `OPENROUTER_BASE_URL` (default `https://openrouter.ai/api/v1`), `P1_LLM_MODEL` (default `openai/gpt-4o-mini`).

## What this is not

Not SemVer. Not a proof embeddings always lose. Not a retune of [`../shapewalk-vs-rag/results.summary.json`](../shapewalk-vs-rag/results.summary.json). Not a replacement of [`../p1-llm-hard/results.summary.json`](../p1-llm-hard/results.summary.json). Primary claim is equal-quality **pairs** (ShapeWalk + Embedding RAG), not dump rescue, not lexical triples.
