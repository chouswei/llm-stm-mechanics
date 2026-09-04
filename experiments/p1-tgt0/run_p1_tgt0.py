#!/usr/bin/env python3
"""STM Prediction 1 — T>0 harder LLM-answer quality (evidence vs noise).

Paper numbers live in results.summary.json (2026-09-04). This script is the
protocol note + scorer lock. The live 200-session × 20-seed driver lived
off-repo for the paper run; a full driver is not shipped here.

Same harder task as experiments/p1-llm-hard/ (NOT KEY-extraction):
  no KEY=/key: markers
  evidence: 'E{session_i}-{slug}' on gold ∩ W
  noise:    'N{session_i}-{slug}' on non-gold in W
  score_llm_s = |pred_s ∩ full_gold_evidence| / |full_gold_evidence|
  score_mean = mean over n_seeds of score_llm_s
  noise_leak_any if any seed leaks an N… token
  primary equal quality: score_mean==1.0 AND NOT noise_leak_any
  T=0.8, n_seeds=20

Env:
  OPENROUTER_API_KEY     required for a live generate (never commit)
  OPENROUTER_BASE_URL    default https://openrouter.ai/api/v1
  P1_LLM_MODEL           default openai/gpt-4o-mini
  P1_TGT0_DRY            if 1, skip LLM (not a paper verdict)

No secrets in this file.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SUMMARY_PATH = HERE / "results.summary.json"
LIVE_PATH = HERE / "results.live.json"

DEFAULT_BASE = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-4o-mini"
TEMPERATURE = 0.8
N_SEEDS = 20

TOKEN_RE = re.compile(r"[EN]\d+-[A-Za-z0-9._-]+")

TASK_INSTRUCTION = (
    "The working set below is the only material you may use. "
    "Lines tagged evidence: hold values you must list. "
    "Lines tagged noise: must be ignored. "
    "There are no KEY= or key: markers. "
    "List every evidence value, alphabetical, comma-separated. "
    "Output only those values, nothing else. "
    "Do not invent values that are not tagged evidence."
)


def evidence_value(session_i: int, slug: str) -> str:
    return f"E{session_i}-{slug}"


def noise_value(session_i: int, slug: str) -> str:
    return f"N{session_i}-{slug}"


def full_gold_evidence(session_i: int, gold_slugs: list[str]) -> list[str]:
    return [evidence_value(session_i, slug) for slug in gold_slugs]


def score_llm_full_gold_evidence(pred: set[str], gold_evidence: list[str]) -> float:
    """Recall of pred against ALL gold evidence tags (not gold∩W)."""
    if not gold_evidence:
        return 1.0
    gold = set(gold_evidence)
    return len(pred & gold) / len(gold_evidence)


def score_mean(scores: list[float]) -> float:
    if not scores:
        return 1.0
    return sum(scores) / len(scores)


def noise_leak(pred: set[str]) -> bool:
    return any(tok.startswith("N") for tok in pred)


def noise_leak_any(preds: list[set[str]]) -> bool:
    return any(noise_leak(pred) for pred in preds)


def equal_quality_primary(mean_score: float, leak_any: bool) -> bool:
    return abs(mean_score - 1.0) < 1e-12 and not leak_any


def parse_pred_values(text: str) -> set[str]:
    found = set(TOKEN_RE.findall(text or ""))
    if found:
        return found
    parts: list[str] = []
    for chunk in (text or "").replace("\n", ",").split(","):
        tok = chunk.strip().strip("`").strip("'").strip('"')
        if tok:
            parts.append(tok)
    return set(parts)


def check_scorer() -> int:
    """Session 170 identity plus T>0 score_mean / noise_leak_any gates."""
    session_i = 170
    gold_slugs = [
        "hub-s0170",
        "usr-s0170-g0",
        "usr-s0170-g1",
        "usr-s0170-g2",
        "usr-s0170-g3",
    ]
    gold = full_gold_evidence(session_i, gold_slugs)
    walk_resident_evidence = {evidence_value(session_i, "hub-s0170")}
    walk_noise = {noise_value(session_i, "decoy-s0170")}
    dump_pred = set(gold)

    walk_ok = score_llm_full_gold_evidence(walk_resident_evidence, gold)
    dump_ok = score_llm_full_gold_evidence(dump_pred, gold)
    leaked = score_llm_full_gold_evidence(
        walk_resident_evidence | walk_noise, gold
    )

    assert abs(walk_ok - 0.20) < 1e-12, walk_ok
    assert dump_ok == 1.0, dump_ok
    assert abs(leaked - 0.20) < 1e-12, leaked
    assert not noise_leak(walk_resident_evidence)
    assert not noise_leak(dump_pred)
    assert noise_leak(walk_resident_evidence | walk_noise)

    seeds_perfect = [1.0] * N_SEEDS
    seeds_mixed = [1.0] * (N_SEEDS - 1) + [0.8]
    assert abs(score_mean(seeds_perfect) - 1.0) < 1e-12
    assert score_mean(seeds_mixed) < 1.0
    assert not noise_leak_any([walk_resident_evidence] * N_SEEDS)
    assert noise_leak_any(
        [walk_resident_evidence] * (N_SEEDS - 1)
        + [walk_resident_evidence | walk_noise]
    )
    assert equal_quality_primary(score_mean(seeds_perfect), False)
    assert not equal_quality_primary(score_mean(seeds_mixed), False)
    assert not equal_quality_primary(1.0, True)

    parsed = parse_pred_values(
        "E170-hub-s0170, N170-decoy-s0170, E170-usr-s0170-g0"
    )
    assert "E170-hub-s0170" in parsed
    assert "N170-decoy-s0170" in parsed
    assert noise_leak(parsed)

    print("T>0 HARD: T=0.8 n_seeds=20; score_mean over seeds")
    print("primary gate: score_mean==1.0 AND NOT noise_leak_any")
    print("check-scorer: ok")
    return 0


def paper_summary_note() -> None:
    data = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    stats = data["stats_both_perfect_llm"]
    print(
        "Paper record (T>0 harder evidence-vs-noise; keep p1-llm-hard T=0):\n"
        f"  verdict_primary={data['verdict_primary']} "
        f"n_both_perfect={data['n_both_perfect']}\n"
        f"  n_relaxed={data['n_relaxed']} "
        f"verdict_relaxed={data['verdict_relaxed_secondary']}\n"
        f"  n_noise_leak={data['n_noise_leak']}\n"
        f"  n_walk_imperfect_llm={data['n_walk_imperfect_llm']} "
        f"n_dump_imperfect_llm={data['n_dump_imperfect_llm']}\n"
        f"  mean Δ={stats['mean_delta']} CI={stats['ci95']}\n"
        f"  wall_time_s={data['wall_time_s']} "
        f"T={data['protocol']['temperature']} n_seeds={data['protocol']['n_seeds']}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-scorer",
        action="store_true",
        help="Run evidence-vs-noise T>0 scorer checks (no API, no MemNet).",
    )
    args = parser.parse_args()
    if args.check_scorer or os.environ.get("P1_TGT0_CHECK", "").strip() in {
        "1",
        "true",
        "TRUE",
        "yes",
    }:
        return check_scorer()

    dry = os.environ.get("P1_TGT0_DRY", "").strip() in {
        "1",
        "true",
        "TRUE",
        "yes",
    }
    key = (os.environ.get("OPENROUTER_API_KEY") or "").strip() or None
    if not dry and not key:
        print(
            "OPENROUTER_API_KEY missing. Export it (never commit), "
            "or run --check-scorer / P1_TGT0_DRY=1.\n"
            "Paper verdict is experiments/p1-tgt0/results.summary.json; "
            "a live re-run is not required to read the record. "
            "The 200-session × 20-seed harness lived off-repo for this run.",
            file=sys.stderr,
        )
        paper_summary_note()
        return 2

    if dry:
        print(
            "P1_TGT0_DRY=1: not a paper verdict. Scorer lock is "
            "score_mean over n_seeds=20 of full_gold_evidence with "
            "noise_leak_any gate. T=0 harder p1-llm-hard is a separate, "
            "kept result."
        )
        paper_summary_note()
        check_scorer()
        LIVE_PATH.write_text(
            json.dumps(
                {
                    "dry_run": True,
                    "note": "Not a paper verdict. See results.summary.json.",
                    "scorer": "score_mean of full_gold_evidence",
                    "temperature": TEMPERATURE,
                    "n_seeds": N_SEEDS,
                    "t0_sibling": "experiments/p1-llm-hard/",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return 0

    print(
        "Live OpenRouter re-run is not shipped as a full 200-session × "
        "20-seed driver in this record commit (authoritative counts are in "
        "results.summary.json; the paper harness lived off-repo). Install "
        "memnet-llm==0.19.4, reuse experiments/p1-hr graphs, pin_map M=12 "
        f"k=2 vs dump fixture, model={os.environ.get('P1_LLM_MODEL', DEFAULT_MODEL)}, "
        f"T={TEMPERATURE}, n_seeds={N_SEEDS}, score_mean=mean of "
        "full_gold_evidence, no KEY= markers, evidence/noise tags only. "
        "Do not commit the API key."
    )
    paper_summary_note()
    return 0


if __name__ == "__main__":
    sys.exit(main())
