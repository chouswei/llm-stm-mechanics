# ShapeWalk vs Dump vs Embedding RAG top-k — locked live record

**Verdict: PASS**

Authoritative numbers: [`results.summary.json`](results.summary.json). Protocol lock: [`PROTOCOL.md`](PROTOCOL.md). Parent lexical PASS unchanged: [`../shapewalk-vs-rag/results.summary.json`](../shapewalk-vs-rag/results.summary.json). Do not overwrite from a different model, package, embedder, or scorer. Not a MemNet SemVer $a$/$b$ claim.

## Stack

- `memnet-llm==0.19.5`
- Embedder: `sentence-transformers/all-MiniLM-L6-v2` (local cosine; generate-only OpenRouter)
- Graphs: `experiments/p1-hr/` (Sage author-blind **ACCEPT after regen**; $n=200$)
- LLM: OpenRouter `openai/gpt-4o-mini`, $T=0$
- Arms: ShapeWalk (`PinMapComposer.compose`, $k=2$, $M=12$), Dump (uncapped), Embedding RAG cosine top-$k=12$
- Coefficients $a=1,b=1,c=0,d=10$ — **not retuned**
- Scorer: full-gold evidence + `noise_leak` gate (same as p1-llm-hard)

## Primary claim (equal-quality walk+embed pairs)

$n_{\mathrm{pair}}=88$ (min $30$).

| Contrast | mean $\Delta$ | 95% CI | $n$ |
|----------|---------------|--------|-----|
| $\widehat{\mathcal{A}}_{\mathrm{embed}}-\widehat{\mathcal{A}}_{\mathrm{walk}}$ | 210.943182 | [183.340909, 237.693182] | 88 |

Mean $\Delta>0$ and CI excludes $0$ → ShapeWalk lower action at matched quality. Bootstrap $B=10000$, seed $42$.

**PASS** under PROTOCOL: $n_{\mathrm{pair}}\ge 30$; walk+embed contrast positive with CI excluding $0$; coeffs/scorer/embedder unchanged.

## Secondary (pairwise walk+Dump; not a rescue)

| Pair | mean $\Delta$ | 95% CI | $n$ |
|------|---------------|--------|-----|
| walk+Dump equal-quality | 2936.352941 | [2784.141176, 3091.5] | 170 |

Primary claim is equal-quality **pairs** (ShapeWalk + Embedding RAG), not dump rescue and not lexical triples.

## Run hygiene

- $n_{\mathrm{ok}}=200$, $n_{\mathrm{error}}=0$, $n_{\mathrm{noise\_leak}}=0$
- elapsed $\approx 857.5$ s
- call counts: `{"open_session": 200, "MutateGate.apply": 200, "PinMapComposer.compose": 200, "close_session": 200}`

## What this is not

Not a proof embeddings always lose. Not a replacement of the lexical PASS. Not SemVer. Not OpenAI-embed RAG. Not a replacement of [`../p1-llm-hard/results.summary.json`](../p1-llm-hard/results.summary.json).
