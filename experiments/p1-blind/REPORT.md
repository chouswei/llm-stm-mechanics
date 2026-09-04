# STM Prediction 1 — author-blind review (Sage)

Paper §10.1. Graphs: [`../p1-hr/`](../p1-hr/) $n=200$.

**Stratum sign-off:** `ACCEPT after regen`

## Honesty

- Reviewer: Sage; author-blind; did not author graphs
- Protocol: blinded packs; no `expect_*`; no prior reviews; no $\widehat{\mathcal{A}}$ as quality evidence
- Sealed `blind_map` omitted (see [`BLIND_MAP.md`](BLIND_MAP.md))
- Do not cite $\widehat{\mathcal{A}}$ as a review quality score

## Checklist

- Objective blind checklist: **200/200 PASS**
- Agreement with original `checklist_pass`: **100%**

## Deep sample and regen

- Deep sample $n=34$: initially **33 OK**
- Eight `asymmetric-spoke` AUTO_DUMP fails ($k\le 2$ neighbourhood gold-only) listed, then regenerated with a non-gold decoy at hop 1 ([`REGEN_8.md`](REGEN_8.md))
- Sage re-check: **ACCEPT 8/8**

## Post-regen gold presence (PRIMARY)

`memnet-llm` **0.19.4**. Coefficients unchanged ($a=1$, $b=1$, $c=0$, $d=10$).

- $n_{\mathrm{both\_perfect}}=170$
- mean $\Delta\approx 2930.59$
- 95% CI **[2778.71, 3084.10]** (excludes 0)
- Verdict **PASS**

Pre-regen (same lock, 0.19.3 harness record): mean $\Delta\approx 2932.41$, CI $[2780.35, 3086.31]$. Full per-session dumps are not re-attached here.

## Post-regen P1 LLM (touched sessions merged)

Same primary: $n=170$ / $\Delta$ / CI. Full-gold KEY-extraction scorer. Still **PASS**. $T>0$ remains **OPEN**. See [`../p1-llm/`](../p1-llm/).

Harder evidence-versus-noise (no KEY markers): $n=161$ both-perfect, $n_{\mathrm{noise\_leak}}=0$, mean $\Delta\approx 2940.65$, CI $[2782.09, 3098.31]$. Still **PASS**. $T>0$ remains **OPEN**. See [`../p1-llm-hard/`](../p1-llm-hard/).
