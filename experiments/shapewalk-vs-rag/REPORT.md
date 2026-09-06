# ShapeWalk vs Dump vs RAG top-k — locked live record

**Verdict: PASS**

Authoritative numbers: [`results.summary.json`](results.summary.json). Protocol lock: [`PROTOCOL.md`](PROTOCOL.md). Do not overwrite from a different model, package, or scorer. Not a MemNet SemVer $a$/$b$ claim.

## Stack

- `memnet-llm==0.19.4`
- Graphs: `experiments/p1-hr/` (Sage author-blind **ACCEPT after regen**; $n=200$)
- LLM: OpenRouter `openai/gpt-4o-mini`, $T=0$
- Arms: ShapeWalk (`PinMapComposer.compose`, $k=2$, $M=12$), Dump (uncapped), RAG lexical Jaccard top-$k=12$
- Coefficients $a=1,b=1,c=0,d=10$ — **not retuned**
- Scorer: full-gold evidence + `noise_leak` gate (same as p1-llm-hard)

## Primary claim (equal-quality triples)

$n_{\mathrm{triple}}=83$ (min $30$).

| Contrast | mean $\Delta$ | 95% CI | $n$ |
|----------|---------------|--------|-----|
| $\widehat{\mathcal{A}}_{\mathrm{RAG}}-\widehat{\mathcal{A}}_{\mathrm{walk}}$ | 211.566265 | [184.662651, 236.746988] | 83 |
| $\widehat{\mathcal{A}}_{\mathrm{dump}}-\widehat{\mathcal{A}}_{\mathrm{walk}}$ | 3108.590361 | [2886.518072, 3335.228916] | 83 |

Both CIs exclude $0$; mean $\Delta>0$ → ShapeWalk lower action at matched quality. Bootstrap $B=10000$, seed $42$.

**PASS** under PROTOCOL: $n_{\mathrm{triple}}\ge 30$; both contrasts positive with CI excluding $0$; coeffs/scorer unchanged.

## Secondary (pairwise; not a rescue)

| Pair | mean $\Delta$ | 95% CI | $n$ |
|------|---------------|--------|-----|
| walk+RAG equal-quality | 211.566265 | [184.662651, 236.746988] | 83 |
| walk+Dump equal-quality | 2936.352941 | [2784.141176, 3091.500000] | 170 |

Note: $n_{\mathrm{pair\_walk\_rag}}=83$ equals $n_{\mathrm{triple}}$ on this run (every walk+RAG equal-quality row was also dump-perfect).

## Run hygiene

- $n_{\mathrm{ok}}=200$, $n_{\mathrm{error}}=0$, $n_{\mathrm{noise\_leak}}=0$
- elapsed $\approx 788.8$ s
- call counts: `{"open_session": 200, "MutateGate.apply": 200, "PinMapComposer.compose": 200, "close_session": 200}`

## What this is not

Not embedding-RAG. Not a proof RAG is always worse. Not a replacement of [`../p1-llm-hard/results.summary.json`](../p1-llm-hard/results.summary.json). Not SemVer.
