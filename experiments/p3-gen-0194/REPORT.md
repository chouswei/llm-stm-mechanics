# STM Prediction 3 — generation half post-fix (`memnet-llm` 0.19.4)

Confirmation after [MemNet PR #148](https://github.com/chouswei/MemNet/pull/148) (nickname `id` off `pin_map` emit). Protocol matches [`../p3-gen/`](../p3-gen/). **$T=0$ is the predeclared primary band.** $T>0$ was not run.

**Product honesty $c$ confirmation, not a new prediction.** This note does not claim a MemNet SemVer $a$ or $b$ cut. Same usage method: cue $\to$ `pin_map` $\to$ mutate.

## Verdict

| Condition | Verdict | mismatches / 120 |
|-----------|---------|------------------|
| RAW (`pin_map` as emitted) | **PASS** | 0/120 (was FAIL 30/120 on 0.19.3 @ `eff05dc8`) |
| CANONICAL (strip `id`/`hid` from `pin_map` text; preserve order) | **PASS** | 0/120 |
| $T>0$ CANONICAL | **OPEN** | skipped (OpenRouter cost/latency) |

- `raw_id_wire_diff_events=0` (was 120)
- `canon_text_diff_events=0`
- `hid_leaks=0`
- `build_fail=0`
- `nickname_on_wire_failure_mode=false`

## Stack

- MemNet `0.19.4` (PR #148 merge `1242c467`; after PR #147 ranking fix)
- LLM: OpenRouter `openai/gpt-4o-mini`, base `https://openrouter.ai/api/v1`
- Protocol: `n_sessions=8`, `n_perms=15` (120 comparisons), $M=12$, $k=2$, cue kind `HUB`
- Decoding: $T=0$ greedy, `max_tokens=256`
- Task: list DOC `slug` fields in order, comma-separated
- `DROP_KEYS={id,hid}` for the CANONICAL wire only

Elapsed ~374s. Product-API call counts were not attached with the shipped summary; the protocol is $8\times(1+15)=128$ sessions (operators remain 2: mutate and `pin_map`; no `rag_query`).

## Pass/fail against the claim

**RAW PASS.** Nickname `id` is no longer on the `pin_map` wire, so isomorphic CREATE-order / nickname permutations no longer differ in RAW text (`raw_id_wire_diff_events=0`). Orig-vs-perm answers matched $0/120$.

**CANONICAL PASS.** Unchanged from 0.19.3: stripping `id`/`hid` while keeping row order yields identical text (`canon_text_diff_events=0`) and $0/120$ mismatches.

**Interpretation.** This confirms the 0.19.3 split: the remaining generation leak was nickname-on-wire, not ranking/order. #148 is honesty $c$ on the 0.19 line.

## How to re-run

See [`README.md`](README.md). Requires `OPENROUTER_API_KEY` in the environment (never commit it).
