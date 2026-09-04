# Experiments (P1 / P1-HR / P1-LLM / P1-blind / P2 / P3 / P3-gen / P3-gen-0194)

Harnesses for the thesis §10 predictions. P1, P2, and P3 before-generate are in-process MemNet goldfish only (no LLM generate). P1 LLM-answer quality (`p1-llm/`) and P3 generation half (`p3-gen/`, post-fix record `p3-gen-0194/`) call an OpenRouter chat API at $T=0$; that is the exception, not a change to the synthetic strata.

## Stack

Install MemNet from the post-#147 commit used in P1/P2/P3 and the 0.19.3 generation split. For the 0.19.4 confirmation, install `memnet-llm==0.19.4` instead (see `p3-gen-0194/`).

```bash
python3 -m venv .venv
.venv/bin/pip install "git+https://github.com/chouswei/MemNet.git@eff05dc8a0ad5369e8d7e7f347db30b9300b04d6"
```

Seeds and locked coefficients are in each `run_*.py` / REPORT.

## Re-run

```bash
# P1 — ShapeWalk vs dump (synthetic pilot n=500; isomorphic — constant Δ)
.venv/bin/python experiments/p1/run_p1.py

# P1-HR — ShapeWalk vs dump on human-reviewed n=200 (diverse families)
# Sage author-blind ACCEPT after regen: experiments/p1-blind/
.venv/bin/python experiments/p1-hr/run_p1_hr.py

# P1-LLM — LLM-answer quality on p1-hr graphs (FIXED full-gold scorer; T=0)
# Authoritative numbers: experiments/p1-llm/results.summary.json
# Do NOT cite the invalid gold∩W 200/200 extraction-fidelity run.
# Needs OPENROUTER_API_KEY for a live re-run; never commit the key.
.venv/bin/python experiments/p1-llm/run_p1_llm.py --check-scorer
# export OPENROUTER_API_KEY=
# .venv/bin/python experiments/p1-llm/run_p1_llm.py

# P2 — M-cap lambda-hat diagnostic (eq 31)
.venv/bin/python experiments/p2/run_p2.py

# P3 — rename / order invariance (eq 19 law; before generate)
.venv/bin/python experiments/p3/run_p3.py

# P3-gen — generation half on 0.19.3 @ eff05dc8 (OpenRouter; needs OPENROUTER_API_KEY)
# Paper split is experiments/p3-gen/results.summary.json — do not overwrite it
# from a different model. Dry-run: P3_GEN_DRY=1 (wire diffs only).
export OPENROUTER_API_KEY=  # never commit
.venv/bin/python experiments/p3-gen/run_p3_gen.py

# P3-gen-0194 — same protocol on memnet-llm 0.19.4 (honesty c confirmation)
# Authoritative numbers: experiments/p3-gen-0194/results.summary.json
# Re-run uses experiments/p3-gen/run_p3_gen.py after pip install memnet-llm==0.19.4
```

## Reported scoreboard (2026-09-04)

| Pred | Verdict | Notes |
|------|---------|-------|
| P1 synthetic | PASS (structural) | n=500; constant Δ=1934 (clone stratum) |
| P1-HR | PASS | n=200; Sage author-blind ACCEPT after regen; 17 families; n_both_perfect=170; mean Δ≈2930.59, CI [2778.71, 3084.10] (gold presence, post-regen) |
| P1-LLM | PASS | full-gold scorer; n=170 equal-quality; same post-regen Δ/CI; T=0 gpt-4o-mini; T>0 OPEN. Invalid gold∩W 200/200 must not be cited |
| P2 | PASS (account diagnostic) | truncation / no-false-positive strong; AUROC vs \|W\| only marginal |
| P3 before-generate | PASS after MemNet #147 | pre-#147: FAIL (order) — see `p3/PRE147.md` |
| P3 generation half ($T=0$) | 0.19.3: RAW FAIL 30/120 / CANONICAL PASS 0/120; 0.19.4: both PASS 0/120 | #148 honesty c confirmation; $T>0$ OPEN; no SemVer $a$/$b$ claim |

Full per-session dumps are truncated in `*.summary.json`; re-run the scripts for complete artifacts.
