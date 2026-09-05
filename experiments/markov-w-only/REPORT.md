# W-only Markov falsification — structural MemNet goldfish

**Date:** 2026-09-05  
**Verdict:** `NOT_FALSIFIED` (PASS) — W-only Markov **not rejected** on this stratum  
**Harness:** `HARNESS_VALID`

Full harness lived off-repo. Locked design: [`PROTOCOL.md`](PROTOCOL.md). Counts: [`results.summary.json`](results.summary.json). No per-graph `results.json` dump is shipped.

## Honesty

- This is **not** a proof that $\sigma=(W,p)$ is Markov, and **not** an empirical closure of soft-KV / tool-state / LLM-dialogue hidden history.
- It is a fail-able W-only test on a declared MemNet goldfish harness with a working positive control.
- Alt histories were equivalent-cue (same Shape family), not deep divergent dialogue summaries.
- Protocol was locked before outcomes.
- Package pin `memnet-llm` $0.19.4$ is not a SemVer $a$ or $b$ claim.

## Counts (do not invent)

| Field | Value |
|-------|--------|
| Package | `memnet-llm` $0.19.4$ |
| Stratum | structural MemNet goldfish; no LLM generate |
| Graphs | $n=200$ post-regen p1-hr |
| Match | Alt via equivalent slug-locator cue without kind |
| $n_{\mathrm{matched}}$ | $200$ ($\ge n_{\mathrm{matched\_min}}=30$) |
| $\sigma$ | ordered observable hard-window $W$ only (no $p$ estimator) |
| Band | $\le 0.05$ |
| Main (Markov-honest admission) | mismatch_rate $=0.0$ $\to$ PASS (not falsified) |
| Positive control (hidden path-label admission) | mismatch_rate $=1.0$ $\to$ FAIL as required |
| Harness validity | `HARNESS_VALID` |
| Final | `NOT_FALSIFIED` (PASS) |

Main admission is Markov in $(W,\mathrm{offer})$: mismatch rate on $\mathrm{offer}_{t+1}$ / $W_{t+1}$ is $0$. The positive control hid a path-label in admission and mismatched on every matched pair, so the harness can see hidden history when it is present.

## Still open

$p$ estimator; soft attention / KV; real divergent histories (dialogue summaries, tool state). Record only that W-only Markov was not rejected on this declared goldfish harness.
