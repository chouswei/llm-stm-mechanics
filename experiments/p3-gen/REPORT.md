# STM Prediction 3 — generation half (OpenRouter, $T=0$)

After-generate comparison on isomorphic CREATE-order / nickname permutations. Graph and cue match the before-generate harness in [`../p3/`](../p3/). **$T=0$ is the predeclared primary band.** $T>0$ was not run on this $0.19.3$ split; the CANONICAL band later closed in [`../p3-tgt0/`](../p3-tgt0/).

**Not a MemNet SemVer $a$ or $b$ claim.** Nickname-off-wire is product honesty $c$ (MemNet PR #148 / `memnet-llm` 0.19.4). Post-fix confirmation: [`../p3-gen-0194/`](../p3-gen-0194/).

## Verdict

| Condition | Verdict | mismatches / 120 |
|-----------|---------|------------------|
| RAW (`pin_map` as emitted, nickname `id` may be present) | **FAIL** | 30/120 |
| CANONICAL (strip `id`/`hid` from `pin_map` text; preserve order) | **PASS** | 0/120 |
| $T>0$ CANONICAL | later **PASS** on $0.19.4$ | skipped here; closed in [`../p3-tgt0/`](../p3-tgt0/) |

- `raw_id_wire_diff_events=120`
- `canon_text_diff_events=0`
- `hid_leaks=0`
- `build_fail=0`
- `nickname_on_wire_failure_mode=True`

Discarded: local `sshleifer/tiny-gpt2` partials — not part of this verdict.

## Stack

- MemNet `0.19.3` @ `eff05dc8` (after PR #147)
- LLM: OpenRouter `openai/gpt-4o-mini`, base `https://openrouter.ai/api/v1`
- Protocol: `n_sessions=8`, `n_perms=15` (120 comparisons), $M=12$, $k=2$, cue kind `HUB`
- Decoding: $T=0$ greedy, `max_tokens=256`
- Task: list DOC `slug` fields in order, comma-separated
- `DROP_KEYS={id,hid}` for the CANONICAL wire only

Elapsed ~360s. Product-API call counts (one session per orig or perm):

| call | count |
|------|-------|
| `open_session` | 128 |
| `MutateGate.apply` | 128 |
| `PinMapComposer.compose` | 128 |
| `close_session` | 128 |

$8\times(1+15)=128$. Operators remain 2: mutate and `pin_map`. No `rag_query`.

## Claim under test

Hidden-id / nickname permutations must not change generate outputs once *labels* are canonicalised. Admission order is physical and is not sorted away. After #147, before-generate order already matches; this half asks whether the *generate* still depends on names that are not identity.

## Pass/fail against the claim

**RAW FAIL.** Every one of the 120 comparisons had a different RAW `pin_map` string (`raw_id_wire_diff_events=120`) because optional nickname `id` is still on the wire even though ranking no longer uses it. On that wire, 30/120 orig-vs-perm answers disagreed.

**CANONICAL PASS.** Stripping `id`/`hid` while keeping row order made `pin_map` text identical across permutations (`canon_text_diff_events=0`) and answers matched 0/120 mismatches.

**Interpretation.** After #147, the remaining gauge leak *for generation* is nickname `id` on the `pin_map` wire, not ranking/order. That is an honesty / wire-shape issue. Closing it in the product is MemNet PR #148 (`memnet-llm` 0.19.4, honesty $c$); this paper does not cut SemVer $a$ or $b$.

## Example mismatch pattern

On CANONICAL, the same DOC slugs and titles appear in the same order for orig and perm (as in the before-generate [`../p3/REPORT.md`](../p3/REPORT.md) match example). RAW answers can drop a slug when nickname ids reshuffle across isomorphic CREATE-order permutations, even though the observable DOC rows are the same sequence.

Illustrative RAW fragment (session 0 style; ids are nicknames, not identity):

```
(:DOC {id: 'nick-doc-s00-n00', slug: 'doc-s00-n00', title: 'Document s00 #0'})
...
(:DOC {id: 'nick-doc-s00-n06', slug: 'doc-s00-n06', title: 'Document s00 #6'})
```

vs a permutation that keeps slug/title order but permutes `id`. CANONICAL drops those `id` fields and the generate matches. Full per-call `results.json` is optional and is not shipped (size).

## How to re-run

See [`README.md`](README.md). Requires `OPENROUTER_API_KEY` in the environment (never commit it). `P3_GEN_DRY=1` runs the MemNet pin_map / wire-diff half only.
