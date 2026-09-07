# ShapeWalk vs Dump vs RAG top-k — $T>0$ locked live record

**Verdict: PASS**

Authoritative numbers: [`results.summary.json`](results.summary.json). Protocol lock: [`PROTOCOL.md`](PROTOCOL.md). Parent $T=0$ lexical PASS unchanged: [`../shapewalk-vs-rag/results.summary.json`](../shapewalk-vs-rag/results.summary.json). Do not overwrite from a different model, package, temperature, seed count, or scorer. Not a MemNet SemVer $a$/$b$ claim.

## Stack

- `memnet-llm==0.19.5`
- Graphs: `experiments/p1-hr/` (Sage author-blind **ACCEPT after regen**; $n=200$)
- LLM: OpenRouter `openai/gpt-4o-mini`, $T=0.8$, $n_{\mathrm{seeds}}=20$ (same measurement band as `p1-tgt0`)
- Arms: ShapeWalk (`PinMapComposer.compose`, $k=2$, $M=12$), Dump (uncapped), RAG lexical Jaccard top-$k=12$
- Coefficients $a=1,b=1,c=0,d=10$ — **not retuned**. Operational empty-$W$ / bake-off $d=\lvert W\rvert$; conceptual $d$ remains Lev (37).
- Scorer: full-gold evidence + `noise_leak_any` gate (same as p1-tgt0); $\ell=1-\mathrm{score\_mean}$

## Primary claim (equal-quality triples)

$n_{\mathrm{triple}}=81$ (min $30$).

| Contrast | mean $\Delta$ | 95% CI | $n$ |
|----------|---------------|--------|-----|
| $\widehat{\mathcal{A}}_{\mathrm{RAG}}-\widehat{\mathcal{A}}_{\mathrm{walk}}$ | 211.654321 | [184.358025, 237.728395] | 81 |
| $\widehat{\mathcal{A}}_{\mathrm{dump}}-\widehat{\mathcal{A}}_{\mathrm{walk}}$ | 3098.098765 | [2869.925926, 3327.876543] | 81 |

Both CIs exclude $0$; mean $\Delta>0$ → ShapeWalk lower action at matched quality. Bootstrap $B=10000$, seed $42$.

**PASS** under PROTOCOL: $n_{\mathrm{triple}}\ge 30$; both contrasts positive with CI excluding $0$; coeffs/scorer/$T$/$n_{\mathrm{seeds}}$ unchanged.

## Secondary (pairwise; not a rescue)

| Pair | mean $\Delta$ | 95% CI | $n$ |
|------|---------------|--------|-----|
| walk+RAG equal-quality | 211.654321 | [184.358025, 237.728395] | 81 |
| walk+Dump equal-quality | 2928.609467 | [2772.804734, 3085.609467] | 169 |

Note: $n_{\mathrm{pair\_walk\_rag}}=81$ equals $n_{\mathrm{triple}}$ on this run (every walk+RAG equal-quality row was also dump-perfect).

## Run hygiene

- $n_{\mathrm{ok}}=200$, $n_{\mathrm{error}}=0$, $n_{\mathrm{noise\_leak}}=0$
- elapsed $\approx 14614.8$ s
- planned generate calls: $12000$ ($200\times 3\times 20$)
- call counts: `{"open_session": 200, "MutateGate.apply": 200, "PinMapComposer.compose": 200, "close_session": 200}`
- Parent $T=0$ summary and `p1-tgt0` summary were **not** written by this driver

## What this is not

Not a replacement of the $T=0$ lexical PASS. Not a replacement of [`../p1-tgt0/results.summary.json`](../p1-tgt0/results.summary.json). Not embedding $T>0$ (still later). Not SemVer. Not an OM / stochastic-mechanics theorem.
