# PROTOCOL — ShapeWalk vs Dump vs lexical RAG top-k, $T>0$ band (locked)

Locked **before** outcomes. Do not retune $k$, the lexical Jaccard scorer, $\widehat{\mathcal{A}}$ coefficients, the equal-quality gate, $T$, $n_{\mathrm{seeds}}$, or the PASS band after seeing live numbers.

This is a **protocol + harness scaffold**. Authoritative $\widehat{\mathcal{A}}$ / PASS numbers do **not** exist until the first locked run is written under explicit `WRITE=1`. This note is not a Result. It is **not** a MemNet SemVer $a$/$b$ claim.

## Parent lock (T=0 lexical)

The $T=0$ lexical three-arm bake-off remains **authoritative** for the greedy band:

- Protocol: [`../shapewalk-vs-rag/PROTOCOL.md`](../shapewalk-vs-rag/PROTOCOL.md)
- Record: [`../shapewalk-vs-rag/results.summary.json`](../shapewalk-vs-rag/results.summary.json) (**PASS**; $n_{\mathrm{triple}}=83$)

Do **not** overwrite that summary. Do **not** retune $a,b,c,d$, $k=12$, or the lexical Jaccard arm.

This protocol is the **$T>0$ measurement band** on the **same arms**. It is **not** a replacement of that PASS, and **not** a replacement of [`../p1-tgt0/`](../p1-tgt0/) (ShapeWalk vs dump only).

## Stratum

- Graphs: `experiments/p1-hr/` (Sage author-blind **ACCEPT after regen**; $n=200$)
- Package pin: `memnet-llm==0.19.5` preferred (package pin only; **no SemVer $a$ or $b$ claim**). `memnet-llm==0.19.4` is acceptable if the installed version is recorded on the run payload
- Task: harder evidence-versus-noise, **same as** `experiments/p1-llm-hard/` and the $T=0$ lexical bake-off: no `KEY=` / `key:` markers; list evidence, ignore noise; alphabetical, comma-separated
- LLM (live, not this scaffold's verdict): OpenRouter `openai/gpt-4o-mini`
- **Temperature band (match [`../p1-tgt0/`](../p1-tgt0/)):** $T=0.8$; $n_{\mathrm{seeds}}=20$ per (session, arm)
- Inventory $S$ fixed per graph (same manifold for all three arms)

## Arms

**Same as the $T=0$ lexical PROTOCOL.** No retune of $k$, Jaccard, or $a,b,c,d$.

1. **ShapeWalk.** MemNet `pin_map` / bounded Shape offer + admission. Cue kind `HUB`, locators `[("slug", hub_slug)]`, `depth=k=2`, `max_rows=M=12`, `active_only=True`. Caller admits the offered Shape rows (node rows only; skip `EDG`/`LAW`). **Live** arm uses `PinMapComposer.compose`. A BFS $k$-hop cap-$M$ stand-in in the dry harness is **not** the paper walk.

2. **Dump.** Dump inventory observables into $W$ (P1 dump baseline; keep for continuity). Bench fixture: serialise **all** observable session nodes (kind + payload / codebook locators). Cap is **not** applied. Not a product dump of $S$ and not `rag_query`.

3. **RAG top-$k$.** No ShapeWalk. Candidate bag from $S$ using **observables only**: `kind` + payload / codebook locators (`slug`, `title`). **Never** `hid`, store keys, or nickname `id` / `nick` in features or sort keys. Score each candidate by **token Jaccard** on alphanumeric tokens, lowercased, against the cue (hub `kind` + hub `slug` + hub `title`). Admit **top-$k$** by that score into $W$ in **score order**. Ties: higher Jaccard first, then lexicographic `slug`. Deterministic; **no embedding API**.

### Preregistered $k$ (unchanged)

$$
k_{\mathrm{RAG}} = M_{\mathrm{walk}} = 12
$$

Dump remains uncapped.

## Shared measurement (Â)

Per **seed**, $\mathrm{score\_llm}$ and $\mathrm{noise\_leak}$ are the same as `p1-llm-hard` / `p1-tgt0`:

```
score_llm_s := |pred_s ∩ full_gold_evidence| / |full_gold_evidence|
full_gold_evidence := E{session_i}-{slug} for ALL graph.gold_slugs   # NOT gold∩W
noise_leak_s := any N… token in pred_s
```

Per **arm** (mean over $n_{\mathrm{seeds}}=20$), match `p1-tgt0`:

```
score_mean := mean over 20 seeds of score_llm_s
noise_leak_any := any seed leaks an N… token
Â = a·d(∅,W)² + b·tokens + c·0 + d·(1 − score_mean)
a = 1.0, b = 1.0, c = 0.0, d = 10.0
d(empty, W) := |W|     # operational stand-in; conceptual d remains Lev (37)
tokens := Σ (len(title)+len(slug))   # from admitted W; same each seed
```

**Equal-quality (strict, primary):** $\mathrm{score\_mean}=1.0$ **AND NOT** $\mathrm{noise\_leak\_any}$ (all three arms on the same session for triples).

Prompt-only `evidence:` tags remain restricted to $\mathrm{gold}\cap W$. Noise tags `N{session_i}-{slug}` mark non-gold in $W$.

Single-turn from empty; $c=0$ (no critical evictions in this stratum). $|W|$ and tokens are properties of admitted $W$, not of the LLM draw.

## Primary claim

Among **equal-quality triples** (all three arms equal-quality on the same session under the **strict** $T>0$ gate), ShapeWalk has **lower mean** $\widehat{\mathcal{A}}$ than RAG and than Dump. Report paired mean $\Delta$ and 95% bootstrap CIs ($B=10\,000$, seed $42$), same style as p1-llm-hard / $T=0$ lexical.

- $\Delta_{\mathrm{RAG}}=\widehat{\mathcal{A}}_{\mathrm{RAG}}-\widehat{\mathcal{A}}_{\mathrm{walk}}$
- $\Delta_{\mathrm{dump}}=\widehat{\mathcal{A}}_{\mathrm{dump}}-\widehat{\mathcal{A}}_{\mathrm{walk}}$

**PASS** (triples) iff all of:

- $n_{\mathrm{triple}}\ge n_{\mathrm{triple\_min}}=30$
- mean $\Delta_{\mathrm{RAG}}>0$ and 95% CI excludes $0$
- mean $\Delta_{\mathrm{dump}}>0$ and 95% CI excludes $0$
- coefficients not retuned; scorer is full-gold evidence + `noise_leak_any` gate; $T=0.8$, $n_{\mathrm{seeds}}=20$

**FAIL** if RAG or Dump has equal or lower mean $\widehat{\mathcal{A}}$ at equal quality (mean $\Delta\le 0$ or CI includes $0$), or if $n_{\mathrm{triple}}<30$.

**Secondary (not a rescue of a triple FAIL):** pairwise equal-quality vs ShapeWalk (walk+RAG; walk+Dump), same CI style. Report it; do not treat pairwise PASS as the primary claim if triples fail the $n$ gate.

## Stochasticity lock

At $T>0$ the object is a **path measure**, not a single curve (thesis §13 stochasticity seam). This band is **measurement**: fix $T=0.8$ and average $n_{\mathrm{seeds}}=20$ of full-gold $\mathrm{score\_llm}$ (same discipline as `p1-tgt0`). It does **not** close an OM theorem, a stochastic variational derivation, or a SemVer $a$/$b$ claim.

## Firewalls

- No `hid` in RAG features, scores, or admission order
- Nickname `id` / `nick` off the wire for scoring and for $W$ identity
- No $m$ / $p$ / $\lambda$ / momentum on `pin_map`
- No same-run coefficient fit
- RAG is a bench load operator, not a MemNet verb (`rag_query` is not added)
- Dump remains a bench fixture
- Do not overwrite [`../shapewalk-vs-rag/results.summary.json`](../shapewalk-vs-rag/results.summary.json)
- Do not overwrite [`../p1-tgt0/results.summary.json`](../p1-tgt0/results.summary.json)

## Cost (full live)

Full protocol generate load: $n=200$ sessions $\times$ $3$ arms $\times$ $n_{\mathrm{seeds}}=20$ = **$12\,000$** OpenRouter generate calls (plus retries). Use `--limit` for smoke. That count is **not** a paper verdict.

## What this is NOT

- Not a SemVer claim
- Not a replacement of the $T=0$ lexical PASS
- Not a replacement of `p1-tgt0` (two-arm dump contrast)
- Not embedding-RAG; **embedding $T>0$ stays still-later** (sibling later)
- Not a proof that RAG is always worse
- Not an OM / stochastic-mechanics theorem
- Not a live LLM verdict in this scaffold commit

## Still later (not this protocol version)

- Embedding RAG $T>0$ band (sibling later; do not start here)
- KEY-extraction variant
