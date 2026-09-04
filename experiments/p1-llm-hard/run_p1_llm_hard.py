#!/usr/bin/env python3
"""STM Prediction 1 — harder LLM-answer quality (evidence vs noise).

Paper numbers live in results.summary.json (2026-09-04). This script is the
protocol note + scorer lock. Live re-run needs OPENROUTER_API_KEY; it writes
results.live.json and does not overwrite the paper summary unless
P1_LLM_HARD_WRITE=1.

Harder than experiments/p1-llm/ (KEY-extraction):
  no KEY=/key: markers
  evidence: 'E{session_i}-{slug}' on gold ∩ W
  noise:    'N{session_i}-{slug}' on non-gold in W
  task: list every evidence value, ignore noise; alphabetical comma-separated
  score_llm = |pred ∩ full_gold_evidence| / |full_gold_evidence|
  full_gold_evidence from ALL graph.gold_slugs
  noise_leak if any N… in pred
  equal quality: score_llm==1.0 AND no noise_leak

Env:
  OPENROUTER_API_KEY     required for a live generate (never commit)
  OPENROUTER_BASE_URL    default https://openrouter.ai/api/v1
  P1_LLM_MODEL           default openai/gpt-4o-mini
  P1_LLM_HARD_WRITE      if 1, also write results.summary.json (do not do this
                         from a different model/scorer)
  P1_LLM_HARD_DRY        if 1, skip LLM (not a paper verdict)

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
TEMPERATURE = 0.0

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


def noise_leak(pred: set[str]) -> bool:
    return any(tok.startswith("N") for tok in pred)


def equal_quality(score: float, pred: set[str]) -> bool:
    return abs(score - 1.0) < 1e-12 and not noise_leak(pred)


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
    """Session 170 identity: M-capped walk cannot recover full gold evidence."""
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
    assert not equal_quality(walk_ok, walk_resident_evidence)
    assert equal_quality(dump_ok, dump_pred)
    assert not equal_quality(leaked, walk_resident_evidence | walk_noise)

    parsed = parse_pred_values(
        "E170-hub-s0170, N170-decoy-s0170, E170-usr-s0170-g0"
    )
    assert "E170-hub-s0170" in parsed
    assert "N170-decoy-s0170" in parsed
    assert noise_leak(parsed)

    print("HARD session 170: walk score_llm=0.20 (1/5) if only resident evidence")
    print("dump score_llm=1.00; noise_leak if any N… in pred")
    print("equal_quality requires score_llm==1.0 AND no noise_leak")
    print("check-scorer: ok")
    return 0


def paper_summary_note() -> None:
    data = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    print(
        "Paper record (harder evidence-vs-noise; keep KEY-extraction p1-llm):\n"
        f"  verdict={data['verdict']} n_both_perfect={data['n_both_perfect']}\n"
        f"  n_noise_leak={data['n_noise_leak']}\n"
        f"  n_walk_imperfect_llm={data['n_walk_imperfect_llm']} "
        f"n_dump_imperfect_llm={data['n_dump_imperfect_llm']}\n"
        f"  mean Δ={data['stats_both_perfect']['mean']} "
        f"CI={data['stats_both_perfect']['ci95']}\n"
        f"  elapsed_s={data['elapsed_s']} T>0={data['T_gt_0']}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-scorer",
        action="store_true",
        help="Run evidence-vs-noise scorer checks (no API, no MemNet).",
    )
    args = parser.parse_args()
    if args.check_scorer or os.environ.get("P1_LLM_HARD_CHECK", "").strip() in {
        "1",
        "true",
        "TRUE",
        "yes",
    }:
        return check_scorer()

    dry = os.environ.get("P1_LLM_HARD_DRY", "").strip() in {
        "1",
        "true",
        "TRUE",
        "yes",
    }
    key = (os.environ.get("OPENROUTER_API_KEY") or "").strip() or None
    if not dry and not key:
        print(
            "OPENROUTER_API_KEY missing. Export it (never commit), "
            "or run --check-scorer / P1_LLM_HARD_DRY=1.\n"
            "Paper verdict is experiments/p1-llm-hard/results.summary.json; "
            "a live re-run is not required to read the record.",
            file=sys.stderr,
        )
        paper_summary_note()
        return 2

    if dry:
        print(
            "P1_LLM_HARD_DRY=1: not a paper verdict. Scorer lock is "
            "full_gold_evidence with noise_leak gate. KEY-extraction p1-llm "
            "is a separate, kept result."
        )
        paper_summary_note()
        check_scorer()
        LIVE_PATH.write_text(
            json.dumps(
                {
                    "dry_run": True,
                    "note": "Not a paper verdict. See results.summary.json.",
                    "scorer": "full_gold_evidence",
                    "harder_than": "experiments/p1-llm/",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return 0

    print(
        "Live OpenRouter re-run is not shipped as a full 200-session driver "
        "in this record commit (authoritative counts are in "
        "results.summary.json). Install memnet-llm==0.19.4, reuse "
        "experiments/p1-hr graphs, pin_map M=12 k=2 vs dump fixture, "
        f"model={os.environ.get('P1_LLM_MODEL', DEFAULT_MODEL)}, "
        f"T={TEMPERATURE}, score_llm=full_gold_evidence, no KEY= markers, "
        "evidence/noise tags only. Do not commit the API key."
    )
    paper_summary_note()
    return 0


if __name__ == "__main__":
    sys.exit(main())
