# Experiments (P1 / P1-HR / P1-LLM / P1-LLM-hard / P1-tgt0 / P1-blind / P2 / P3 / P3-gen / P3-gen-0194 / P3-tgt0)

Harnesses for the thesis §10 predictions. P1, P2, and P3 before-generate are in-process MemNet goldfish only (no LLM generate). P1 LLM-answer quality (`p1-llm/`, harder evidence-versus-noise `p1-llm-hard/`) and P3 generation half (`p3-gen/`, post-fix record `p3-gen-0194/`) call an OpenRouter chat API at $T=0$; P1 $T>0$ harder (`p1-tgt0/`) and P3 $T>0$ CANONICAL (`p3-tgt0/`) are the temperature bands on the same stack. That is the exception, not a change to the synthetic strata.

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

# P1-LLM-hard — evidence vs noise (no KEY= markers; T=0)
# Authoritative numbers: experiments/p1-llm-hard/results.summary.json
# Harder than KEY-extraction; keep p1-llm/. T>0 closed in p1-tgt0/.
.venv/bin/python experiments/p1-llm-hard/run_p1_llm_hard.py --check-scorer
# export OPENROUTER_API_KEY=
# .venv/bin/python experiments/p1-llm-hard/run_p1_llm_hard.py

# P1-tgt0 — T>0 harder evidence-vs-noise (T=0.8, n_seeds=20)
# Authoritative numbers: experiments/p1-tgt0/results.summary.json
# Live 200×20 driver lived off-repo; this script is the scorer lock.
.venv/bin/python experiments/p1-tgt0/run_p1_tgt0.py --check-scorer

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

# P3-tgt0 — T>0 CANONICAL band on memnet-llm 0.19.4 (OpenRouter; needs OPENROUTER_API_KEY)
# Authoritative numbers: experiments/p3-tgt0/results.summary.json
# Do not overwrite that summary from a different model or package.
# .venv/bin/pip install "memnet-llm==0.19.4"
# .venv/bin/python experiments/p3-tgt0/run_p3_tgt0.py
```

## Reported scoreboard (2026-09-04)

| Pred | Verdict | Notes |
|------|---------|-------|
| P1 synthetic | PASS (structural) | n=500; constant Δ=1934 (clone stratum) |
| P1-HR | PASS | n=200; Sage author-blind ACCEPT after regen; 17 families; n_both_perfect=170; mean Δ≈2930.59, CI [2778.71, 3084.10] (gold presence, post-regen) |
| P1-LLM | PASS | full-gold KEY-extraction; n=170 equal-quality; same post-regen Δ/CI; T=0 gpt-4o-mini; KEY T>0 not run. Invalid gold∩W 200/200 must not be cited |
| P1-LLM-hard | PASS | evidence vs noise (no KEY=); n=161 equal-quality; n_noise_leak=0; mean Δ≈2940.65, CI [2782.09, 3098.31]; T=0 gpt-4o-mini |
| P1-tgt0 | PASS | T>0 harder evidence vs noise; T=0.8; n_seeds=20; n=160 strict equal-quality; mean Δ≈2939.12; CI [2779.9875, 3096.9]; n_noise_leak=0; relaxed n=161 secondary only |
| P2 | PASS (account diagnostic) | truncation / no-false-positive strong; AUROC vs \|W\| only marginal |
| P3 before-generate | PASS after MemNet #147 | pre-#147: FAIL (order) — see `p3/PRE147.md` |
| P3 generation half ($T=0$) | 0.19.3: RAW FAIL 30/120 / CANONICAL PASS 0/120; 0.19.4: both PASS 0/120 | #148 honesty c confirmation; no SemVer $a$/$b$ claim |
| P3 generation half ($T>0$ CANONICAL) | PASS | 0.19.4; T=0.8; N_SAMPLES_DIST=5; DIST_MATCH_BAND=0.05; n_pairs=120; mean/min exact-match rate 1.0; same-run T=0 RAW/CANONICAL PASS 0/120 |

Full per-session dumps are truncated in `*.summary.json`; re-run the scripts for complete artifacts.
