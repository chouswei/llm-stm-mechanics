# Experiments (P1 / P2 / P3)

Synthetic-stratum harnesses for the thesis §10 predictions. No LLM generate. In-process MemNet goldfish only.

## Stack

Install MemNet from the post-#147 commit used in the reported runs:

```bash
python3 -m venv .venv
.venv/bin/pip install "git+https://github.com/chouswei/MemNet.git@eff05dc8a0ad5369e8d7e7f347db30b9300b04d6"
```

Seeds and locked coefficients are in each `run_*.py` / REPORT.

## Re-run

```bash
# P1 — ShapeWalk vs dump action (eq 30)
.venv/bin/python experiments/p1/run_p1.py

# P2 — M-cap lambda-hat diagnostic (eq 31)
.venv/bin/python experiments/p2/run_p2.py

# P3 — rename / order invariance (eq 19 law)
.venv/bin/python experiments/p3/run_p3.py
```

## Reported scoreboard (2026-09-04)

| Pred | Verdict | Notes |
|------|---------|-------|
| P1 | PASS (structural) | equal *gold-evidence presence*, not LLM answer quality; n=500 |
| P2 | PASS (account diagnostic) | truncation / no-false-positive strong; AUROC vs \|W\| only marginal |
| P3 before-generate | PASS after MemNet #147 | pre-#147: FAIL (order) — see `p3/PRE147.md` |
| P3 generation half | OPEN | not run |

Full per-session dumps are truncated in `*.summary.json`; re-run the scripts for complete artifacts.
