# PROTOCOL — ShapeWalk vs Dump vs Embedding RAG top-k (locked)

Locked **before** outcomes. Do not retune $k$, the embedder, $\widehat{\mathcal{A}}$ coefficients, the equal-quality gate, or the PASS band after seeing live numbers.

This is a **protocol + harness scaffold**. Authoritative $\widehat{\mathcal{A}}$ / PASS numbers do **not** exist until the first locked run is written under explicit `WRITE=1`. This note is not a Result. It is **not** a MemNet SemVer $a$/$b$ claim.

## Parent lock

The lexical three-arm bake-off remains **authoritative** for ShapeWalk vs Dump vs **lexical** RAG:

- Protocol: [`../shapewalk-vs-rag/PROTOCOL.md`](../shapewalk-vs-rag/PROTOCOL.md)
- Record: [`../shapewalk-vs-rag/results.summary.json`](../shapewalk-vs-rag/results.summary.json) (**PASS**; $n_{\mathrm{triple}}=83$; mean $\Delta_{\mathrm{RAG}}\approx 211.57$; mean $\Delta_{\mathrm{dump}}\approx 3108.59$)

Do **not** overwrite that summary. Do **not** retune $a,b,c,d$, $k=12$, or the lexical Jaccard arm. Lexical RAG is **not** required in this live loop; it may be cited as a prior contrast only.

This protocol adds a **new arm**: Embedding RAG top-$k$ on the **same** candidate bag and cue surface as lexical RAG.

## Stratum

- Graphs: `experiments/p1-hr/` (Sage author-blind **ACCEPT after regen**; $n=200$)
- Package pin: `memnet-llm==0.19.5` preferred (package pin only; **no SemVer $a$ or $b$ claim**). `memnet-llm==0.19.4` is acceptable if the installed version is recorded on the run payload
- Task: harder evidence-versus-noise, **same as** `experiments/p1-llm-hard/` and the lexical bake-off: no `KEY=` / `key:` markers; list evidence, ignore noise; alphabetical, comma-separated
- LLM (live, not this scaffold's verdict): OpenRouter `openai/gpt-4o-mini`, $T=0$ greedy primary. $T>0$ later optional — **not this protocol version**
- Inventory $S$ fixed per graph (same manifold for all arms in this protocol)

## Arms (this protocol)

1. **ShapeWalk.** MemNet `pin_map` / bounded Shape offer + admission. Same spirit as p1-llm-hard / lexical bake-off: cue kind `HUB`, locators `[("slug", hub_slug)]`, `depth=k=2`, `max_rows=M=12`, `active_only=True`. Caller admits the offered Shape rows (node rows only; skip `EDG`/`LAW`). **Live** arm uses `PinMapComposer.compose`. A BFS $k$-hop cap-$M$ stand-in in the dry harness is **not** the paper walk. Do **not** put embedding vectors on the `pin_map` wire.

2. **Dump.** Dump inventory observables into $W$ (P1 dump baseline; keep for continuity). Bench fixture: serialise **all** observable session nodes (kind + payload / codebook locators). Cap is **not** applied. Not a product dump of $S$ and not `rag_query`.

3. **Embedding RAG top-$k$ (new).** No ShapeWalk. Same candidate bag as lexical: observables only — `kind` + `slug` + `title`. **Never** `hid`, store keys, or nickname `id` / `nick` in features, embed texts, scores, or sort keys. Query text = hub `kind` + hub `slug` + hub `title` (same cue surface as lexical). Each candidate is embedded as `"{kind} {slug} {title}"`. Score = **cosine similarity** of embedding vectors. Admit **top-$k$** in score order (order is physical). Ties: higher cosine first, then lexicographic `slug`.

### Preregistered embedder

$$
\texttt{sentence-transformers/all-MiniLM-L6-v2}
$$

Local weights; deterministic given those weights. **No OpenAI (or other) embed API in v1.**

### Preregistered $k$

$$
k_{\mathrm{RAG}} = M_{\mathrm{walk}} = 12
$$

Equal-cap comparison with ShapeWalk's hard `max_rows`. Same $k$ as the lexical arm (unchanged). Dump remains uncapped.

## Shared measurement (Â)

Same estimator as P1 / p1-llm-hard / lexical bake-off — **not retuned**:

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

Among **equal-quality pairs** (ShapeWalk and Embedding RAG both equal-quality on the same session), ShapeWalk has **lower mean** $\widehat{\mathcal{A}}$ than Embedding RAG. Report paired mean $\Delta$ and 95% bootstrap CIs ($B=10\,000$, seed $42$), same style as the lexical pairwise dump contrast.

- $\Delta_{\mathrm{embed}}=\widehat{\mathcal{A}}_{\mathrm{embed}}-\widehat{\mathcal{A}}_{\mathrm{walk}}$

**PASS** (pairs) iff all of:

- $n_{\mathrm{pair}}\ge n_{\mathrm{pair\_min}}=30$
- mean $\Delta_{\mathrm{embed}}>0$ and 95% CI excludes $0$
- coefficients not retuned; scorer is full-gold evidence + `noise_leak` gate

**FAIL** if Embedding RAG has equal or lower mean $\widehat{\mathcal{A}}$ at equal quality (mean $\Delta\le 0$ or CI includes $0$), or if $n_{\mathrm{pair}}<30$.

**Secondary (not a rescue of a pair FAIL):** pairwise equal-quality vs Dump (walk+Dump), same CI style as the lexical pairwise dump contrast. Report it; do not treat dump pairwise PASS as the primary claim if the embed pair fails the $n$ gate or the $\Delta_{\mathrm{embed}}$ band.

Lexical RAG is **not** in the live loop and is **not** a PASS/FAIL input here.

## Firewalls

- No `hid` in embed features, embed texts, scores, or admission order
- Nickname `id` / `nick` off the wire for scoring and for $W$ identity
- Embedder features are observables-only (`kind` + `slug` + `title`)
- Embedding vectors stay in the Embedding RAG arm; **do not** put vectors on the `pin_map` wire
- No $m$ / $p$ / $\lambda$ / momentum on `pin_map`
- No same-run coefficient fit
- Embedding RAG is a bench load operator, not a MemNet verb (`rag_query` is not added)
- Dump remains a bench fixture
- No OpenAI embed API in v1

## What this is NOT

- Not a SemVer claim
- Not a proof that embeddings always lose
- Not a retune or overwrite of the lexical PASS record
- Not a replacement of p1-llm-hard ShapeWalk-vs-dump numbers
- Not a live LLM verdict in this scaffold commit
- Not a requirement to re-run lexical Jaccard in this loop

## Still later (not this protocol version)

- Embedding $T>0$ band (sibling later; this $T=0$ embed PASS is unchanged)
- Lexical $T>0$ band — **started** (does not overwrite this embed PASS): [`../shapewalk-vs-rag-tgt0/`](../shapewalk-vs-rag-tgt0/)
- KEY-extraction variant
- Other embedders / embed APIs
