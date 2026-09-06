# PROTOCOL — ShapeWalk vs Dump vs RAG top-k (locked)

Locked **before** outcomes. Do not retune $k$, the lexical scorer, $\widehat{\mathcal{A}}$ coefficients, the equal-quality gate, or the PASS band after seeing live numbers.

This is a **protocol + harness scaffold**. Authoritative $\widehat{\mathcal{A}}$ / PASS numbers do **not** exist until the first locked run is written under explicit `WRITE=1`. This note is not a Result. It is **not** a MemNet SemVer $a$/$b$ claim.

Existing P1 (`p1/`, `p1-hr/`, `p1-llm/`, `p1-llm-hard/`) compares **ShapeWalk vs dump** on p1-hr graphs. This bake-off adds a third arm: a **RAG-style lexical top-$k$ retrieve** baseline with **no** graph walk and **no** `pin_map` Shape.

## Stratum

- Graphs: `experiments/p1-hr/` (Sage author-blind **ACCEPT after regen**; $n=200$)
- Package pin: `memnet-llm==0.19.4` (package pin only; **no SemVer $a$ or $b$ claim**)
- Task: harder evidence-versus-noise, **same as** `experiments/p1-llm-hard/`: no `KEY=` / `key:` markers; list evidence, ignore noise; alphabetical, comma-separated
- LLM (live, not this scaffold's verdict): OpenRouter `openai/gpt-4o-mini`, $T=0$ greedy primary. $T>0$ later optional — **not this protocol version**
- Inventory $S$ fixed per graph (same manifold for all three arms)

## Arms

1. **ShapeWalk.** MemNet `pin_map` / bounded Shape offer + admission. Same spirit as the p1-llm-hard walk arm: cue kind `HUB`, locators `[("slug", hub_slug)]`, `depth=k=2`, `max_rows=M=12`, `active_only=True`. Caller admits the offered Shape rows (node rows only; skip `EDG`/`LAW`). **Live** arm uses `PinMapComposer.compose`. A BFS $k$-hop cap-$M$ stand-in in the dry harness is **not** the paper walk.

2. **Dump.** Dump inventory observables into $W$ (P1 dump baseline; keep for continuity). Bench fixture: serialise **all** observable session nodes (kind + payload / codebook locators). Cap is **not** applied. Not a product dump of $S$ and not `rag_query`.

3. **RAG top-$k$.** No ShapeWalk. Build a bag of candidate spans/nodes from $S$ using **observables only**: `kind` + payload / codebook locators (`slug`, `title`). **Never** `hid`, store keys, or nickname `id` / `nick` in features or sort keys. Score each candidate by **lexical overlap** with the cue/query tokens (RelativeSeed cue: hub `kind` + hub `slug` + hub `title`). Primary overlap: **token Jaccard** on alphanumeric tokens, lowercased. Admit **top-$k$** by that score into $W$ in **score order** (order is physical). Ties: higher Jaccard first, then lexicographic `slug`. Deterministic; **no embedding API**.

### Preregistered $k$

$$
k_{\mathrm{RAG}} = M_{\mathrm{walk}} = 12
$$

Equal-cap comparison with ShapeWalk's hard `max_rows`. This is **not** a match to mean ShapeWalk $|W|$ (p1-hr full $n=200$ reports $\mathrm{mean}|W|_{\mathrm{walk}}\approx 9.13$). Dump remains uncapped.

## Shared measurement (Â)

Same estimator as P1 / p1-llm-hard — **not retuned**:

```
Â = a·d(∅,W)² + b·tokens + c·0 + d·(1 − score_llm)
a = 1.0, b = 1.0, c = 0.0, d = 10.0
d(empty, W) := |W|     # operational stand-in; conceptual d remains Lev (37)
tokens := Σ (len(title)+len(slug))
score_llm := |pred ∩ full_gold_evidence| / |full_gold_evidence|
full_gold_evidence := E{session_i}-{slug} for ALL graph.gold_slugs   # NOT gold∩W
noise_leak := any N… token in pred
equal quality := score_llm==1.0 AND no noise_leak  (per arm)
```

Prompt-only `evidence:` tags remain restricted to $\mathrm{gold}\cap W$. Noise tags `N{session_i}-{slug}` mark non-gold in $W$.

Single-turn from empty; $c=0$ (no critical evictions in this stratum).

## Primary claim

Among **equal-quality triples** (all three arms equal-quality on the same session), ShapeWalk has **lower mean** $\widehat{\mathcal{A}}$ than RAG and than Dump. Report paired mean $\Delta$ and 95% bootstrap CIs ($B=10\,000$, seed $42$), same style as p1-llm-hard.

- $\Delta_{\mathrm{RAG}}=\widehat{\mathcal{A}}_{\mathrm{RAG}}-\widehat{\mathcal{A}}_{\mathrm{walk}}$
- $\Delta_{\mathrm{dump}}=\widehat{\mathcal{A}}_{\mathrm{dump}}-\widehat{\mathcal{A}}_{\mathrm{walk}}$

**PASS** (triples) iff all of:

- $n_{\mathrm{triple}}\ge n_{\mathrm{triple\_min}}=30$
- mean $\Delta_{\mathrm{RAG}}>0$ and 95% CI excludes $0$
- mean $\Delta_{\mathrm{dump}}>0$ and 95% CI excludes $0$
- coefficients not retuned; scorer is full-gold evidence + `noise_leak` gate

**FAIL** if RAG or Dump has equal or lower mean $\widehat{\mathcal{A}}$ at equal quality (mean $\Delta\le 0$ or CI includes $0$), or if $n_{\mathrm{triple}}<30$.

**Secondary (not a rescue of a triple FAIL):** pairwise equal-quality vs ShapeWalk (walk+RAG; walk+Dump), same CI style. Report it; do not treat pairwise PASS as the primary claim if triples fail the $n$ gate.

## Firewalls

- No `hid` in RAG features, scores, or admission order
- Nickname `id` / `nick` off the wire for scoring and for $W$ identity
- No $m$ / $p$ / $\lambda$ / momentum on `pin_map`
- No same-run coefficient fit
- RAG is a bench load operator, not a MemNet verb (`rag_query` is not added)
- Dump remains a bench fixture

## What this is NOT

- Not a SemVer claim
- Not a proof that RAG is always worse
- Not embedding-RAG (lexical Jaccard only in v1)
- Not a replacement of p1-llm-hard ShapeWalk-vs-dump numbers
- Not a live LLM verdict in this scaffold commit

## Still later (not this protocol version)

- Embedding RAG arm — **started** (this lexical PASS record is unchanged): [`../shapewalk-vs-rag-embed/`](../shapewalk-vs-rag-embed/)
- $T>0$ band — **started** (this $T=0$ lexical PASS record is unchanged): [`../shapewalk-vs-rag-tgt0/`](../shapewalk-vs-rag-tgt0/)
- KEY-extraction variant
