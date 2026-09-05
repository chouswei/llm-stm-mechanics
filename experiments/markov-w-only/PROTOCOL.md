# PROTOCOL — W-only Markov falsification (locked)

Locked **before** outcomes. Do not retune the band, match rule, or admission rules after seeing mismatch rates.

This is a fail-able **W-only** test on a declared MemNet goldfish harness with a working positive control. It is **not** a proof that $\sigma=(W,p)$ is Markov, and **not** an empirical closure of soft-KV / tool-state / LLM-dialogue hidden history. Alt histories are equivalent-cue (same Shape family), not deep divergent dialogue summaries.

The live driver lived off-repo. This note records the locked design; it is not a re-run script.

## Stratum

- Structural MemNet goldfish; **no LLM generate**
- Package: `memnet-llm` $0.19.4$ (package pin only; **no SemVer $a$ or $b$ claim**)
- $n=200$ post-regen p1-hr graphs
- Inventory $S$ fixed per graph (same manifold for Walk and Alt)
- Measured state $\sigma=$ ordered observable hard-window $W$ only (no $p$ estimator)

## Match on ordered observable $W$

Match Walk vs Alt at turn $t$ on the **ordered observable** working set: kind plus observable payload / codebook locators; never `hid`, store keys, or nickname `id`.

Alt is an **equivalent slug-locator cue without kind** (same Shape family). This is not a deep divergent dialogue-summary history.

Gate: $n_{\mathrm{matched}}\ge n_{\mathrm{matched\_min}}=30$. This run: $n_{\mathrm{matched}}=200$.

## Main vs positive control

**Main (Markov-honest admission).** Admit from $(W,\mathrm{offer})$ only. Compare $\mathrm{offer}_{t+1}$ / $W_{t+1}$ across matched Walk vs Alt. Falsify W-only Markov on this harness if the mismatch rate exceeds the predeclared band.

**Positive control (hidden path-label admission).** Hide a path-label in admission so information outside recorded $W$ can steer the next offer. This arm **must FAIL** (mismatch above the band) for the harness to be valid. If the positive control also matches, the test cannot see hidden history and is invalid.

## Band

Predeclared band $\le 0.05$:

- Main **PASS** (not falsified) iff mismatch rate $\le 0.05$
- Positive control **FAIL as required** iff mismatch rate $> 0.05$ $\to$ `HARNESS_VALID`
- Final claim `NOT_FALSIFIED` only if main PASSes and the harness is valid

## Still not this protocol

- No $p$ in $\sigma$
- No soft attention / KV mass
- No tool-caller policy state
- No LLM-dialogue hidden history
- No deep divergent Alt summaries
