# P3 generation half — rename invariance after generate

OpenRouter `openai/gpt-4o-mini` at $T=0$ (greedy, `max_tokens=256`). Graph construction matches [`../p3/`](../p3/) (CREATE-order / nickname isomorphism). Conditions:

- **RAW** — actual `pin_map` text (may include nickname `id`)
- **CANONICAL** — strip `id`/`hid` from `pin_map` text, preserve row order (`DROP_KEYS={id,hid}`)

Task: list DOC `slug` fields in emitted order, comma-separated.

This is **not** a MemNet SemVer $a$ or $b$ claim. Nickname-off-wire is product honesty $c$ (MemNet PR #148 / `memnet-llm` 0.19.4); the post-fix confirmation is [`../p3-gen-0194/`](../p3-gen-0194/).

## Reported verdict (2026-09-04)

Authoritative numbers are in [`results.summary.json`](results.summary.json) / [`REPORT.md`](REPORT.md). Do not treat a local dry-run as the paper result.

| Condition | Verdict |
|-----------|---------|
| RAW | FAIL — mismatches 30/120 |
| CANONICAL | PASS — mismatches 0/120 |
| $T>0$ CANONICAL | later PASS on 0.19.4 (see [`../p3-tgt0/`](../p3-tgt0/); skipped on this $T=0$ split) |

Discarded: local `sshleifer/tiny-gpt2` partials — not part of the verdict.

## Re-run (requires your key)

No keys are stored in this repo. Export `OPENROUTER_API_KEY` in the environment only.

```bash
python3 -m venv .venv
.venv/bin/pip install "git+https://github.com/chouswei/MemNet.git@eff05dc8a0ad5369e8d7e7f347db30b9300b04d6"
export OPENROUTER_API_KEY=  # your key; never commit it
.venv/bin/python experiments/p3-gen/run_p3_gen.py
```

Wire-diff / pin_map half without calling the LLM:

```bash
P3_GEN_DRY=1 .venv/bin/python experiments/p3-gen/run_p3_gen.py
```

Optional env: `OPENROUTER_BASE_URL` (default `https://openrouter.ai/api/v1`), `P3_GEN_MODEL` (default `openai/gpt-4o-mini`), `P3_N_SESSIONS` (default 8), `P3_N_PERMS` (default 15).
