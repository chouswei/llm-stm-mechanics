# STM Prediction 3 — $T>0$ CANONICAL generation band (`memnet-llm` 0.19.4)

Distributional after-generate check on isomorphic CREATE-order / nickname permutations with **identical canonical `pin_map`**. Protocol matches [`../p3-gen/`](../p3-gen/) for graph, cue, and CANONICAL strip (`DROP_KEYS=\{id,hid\}`; preserve row order). **$T=0$ remains the predeclared primary exact-match band.** This record closes the predeclared $T>0$ CANONICAL band only.

**Product honesty $c$ stack, not a new prediction.** Same usage method: cue $\to$ `pin_map` $\to$ mutate. This note does not claim a MemNet SemVer $a$ or $b$ cut.

Authoritative numbers: [`results.summary.json`](results.summary.json).

## Verdict (2026-09-04)

| Condition | Verdict | Detail |
|-----------|---------|--------|
| $T=0$ RAW | **PASS** | mismatches $0/120$; `raw_id_wire_diff_events=0` |
| $T=0$ CANONICAL | **PASS** | mismatches $0/120$ |
| $T>0$ CANONICAL | **PASS** | $T=0.8$; $N_{\mathrm{SAMPLES\_DIST}}=5$; $\mathrm{DIST\_MATCH\_BAND}=0.05$; $n_{\mathrm{pairs}}=120$; $\mathrm{mean\_exact\_match\_rate}=1.0$; $\mathrm{min\_exact\_match\_rate}=1.0$ |

PASS criterion for $T>0$: $(1-\mathrm{mean})\le 0.05$ and $(1-\mathrm{min})\le 0.05$. Both sides $0.0$.

- $n_{\mathrm{pairs}}=120$ ($8$ sessions $\times$ $15$ perms)
- `canon_text_diff_events=0`, `hid_leaks=0`, `build_fail=0`
- Elapsed $\sim 1249.7$s; $\sim 897$ OpenRouter calls

## Stack

- MemNet `0.19.4` (PR #148 merge `1242c467`; after PR #147 ranking fix)
- LLM: OpenRouter `openai/gpt-4o-mini`, base `https://openrouter.ai/api/v1`
- Protocol: $n_{\mathrm{sessions}}=8$, $n_{\mathrm{perms}}=15$, $M=12$, $k=2$, cue kind `HUB`
- Decoding: $T=0$ greedy and $T=0.8$ with $5$ samples per CANONICAL prompt
- Task: list DOC `slug` fields in order, comma-separated
- `DROP_KEYS={id,hid}` for the CANONICAL wire

## Pass/fail against the claim

**$T=0$ RAW/CANONICAL PASS.** Same honesty $c$ confirmation as [`../p3-gen-0194/`](../p3-gen-0194/): orig-vs-perm answers matched $0/120$ on both wires; nickname `id` is not a RAW leak (`raw_id_wire_diff_events=0`).

**$T>0$ CANONICAL PASS.** On the predeclared band, every orig/perm pair with identical canonical `pin_map` had exact-match rate $1.0$ (mean and min). Exact-match without a band would still false-positive under GPU noise; this run used $\mathrm{DIST\_MATCH\_BAND}=0.05$ and sat at $0$ residual.

**Not closed.** P1 LLM-answer quality at $T>0$ remains OPEN. This is not a SemVer $a$ or $b$ claim.

## How to re-run

See [`README.md`](README.md). Requires `OPENROUTER_API_KEY` in the environment (never commit it). Do not overwrite [`results.summary.json`](results.summary.json) from a different model or package.
