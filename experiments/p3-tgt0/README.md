# P3 generation — $T>0$ CANONICAL band (`memnet-llm` 0.19.4)

OpenRouter `openai/gpt-4o-mini`. $T=0$ greedy RAW/CANONICAL plus $T=0.8$ CANONICAL distributional check.

- $N_{\mathrm{SAMPLES\_DIST}}=5$
- $\mathrm{DIST\_MATCH\_BAND}=0.05$
- $n_{\mathrm{pairs}}=120$ ($8$ sessions $\times$ $15$ perms, identical canonical `pin_map`)

Authoritative numbers: [`results.summary.json`](results.summary.json) / [`REPORT.md`](REPORT.md).

This directory records the **$T>0$ CANONICAL close** on that band after [MemNet PR #148](https://github.com/chouswei/MemNet/pull/148). It is not a new prediction and not a SemVer $a$ or $b$ claim. P1 $T>0$ remains OPEN.

## Re-run (requires your key)

No keys are stored in this repo. Export `OPENROUTER_API_KEY` in the environment only. Do not overwrite this directory's `results.summary.json` from a different model or package.

```bash
python3 -m venv .venv
.venv/bin/pip install "memnet-llm==0.19.4"
# or: .venv/bin/pip install "git+https://github.com/chouswei/MemNet.git@1242c467bc9052360b4d61d754e944cc7ddf6cd9"
export OPENROUTER_API_KEY=  # your key; never commit it
.venv/bin/python experiments/p3-tgt0/run_p3_tgt0.py
```

Optional env: `OPENROUTER_BASE_URL` (default `https://openrouter.ai/api/v1`), `P3_GEN_MODEL` (default `openai/gpt-4o-mini`), `P3_N_SESSIONS` (default 8), `P3_N_PERMS` (default 15), `P3_TGT0_TEMP` (default 0.8), `P3_N_SAMPLES_DIST` (default 5), `P3_DIST_MATCH_BAND` (default 0.05). Dry-run: `P3_GEN_DRY=1` (wire diffs only; not a paper verdict).
