#!/usr/bin/env python3
"""STM Prediction 1 — LLM-answer quality (FIXED full-gold scorer).

Paper numbers live in results.summary.json (2026-09-04). This script is the
protocol note + scorer lock. Live re-run needs OPENROUTER_API_KEY; it writes
results.live.json and does not overwrite the paper summary unless P1_LLM_WRITE=1.

INVALID prior: score against gold∩W (extraction fidelity) → false 200/200
LLM-perfect. MUST NOT be used as the claim.

FIXED:
  score_llm = |pred ∩ full_gold_keys| / |full_gold_keys|
  full_gold_keys = ALL graph.gold_slugs

Prompt-only KEY still uses gold∩W (keys actually resident in W).

Env:
  OPENROUTER_API_KEY   required for a live generate (never commit)
  OPENROUTER_BASE_URL  default https://openrouter.ai/api/v1
  P1_LLM_MODEL         default openai/gpt-4o-mini
  P1_LLM_WRITE         if 1, also write results.summary.json (do not do this
                       from a different model/scorer)
  P1_LLM_DRY           if 1, skip LLM (not a paper verdict)

No secrets in this file.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SUMMARY_PATH = HERE / "results.summary.json"
LIVE_PATH = HERE / "results.live.json"

DEFAULT_BASE = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-4o-mini"
TEMPERATURE = 0.0

TASK_INSTRUCTION = (
    "The working set below is the only evidence you may use. "
    "List the KEY slugs that appear in it, comma-separated. "
    "Output only those slugs, nothing else. "
    "Do not invent slugs that are not in the working set."
)


def score_llm_full_gold(pred: set[str], full_gold_keys: list[str]) -> float:
    """FIXED scorer: recall of pred against ALL gold slugs."""
    if not full_gold_keys:
        return 1.0
    gold = set(full_gold_keys)
    return len(pred & gold) / len(full_gold_keys)


def score_llm_INVALID_gold_cap_W(pred: set[str], gold_in_W: list[str]) -> float:
    """INVALID extraction-fidelity scorer. Do not use for the P1 claim."""
    if not gold_in_W:
        return 1.0
    return len(pred & set(gold_in_W)) / len(gold_in_W)


def parse_pred_slugs(text: str) -> set[str]:
    parts: list[str] = []
    for chunk in (text or "").replace("\n", ",").split(","):
        tok = chunk.strip().strip("`").strip("'").strip('"')
        if tok:
            parts.append(tok)
    return set(parts)


def check_scorer() -> int:
    """Session 170 identity + invalid-vs-fixed contrast. No API."""
    full_gold = [
        "hub-s0170",
        "usr-s0170-g0",
        "usr-s0170-g1",
        "usr-s0170-g2",
        "usr-s0170-g3",
    ]
    # Walk W is M-capped: only the hub gold key is resident.
    gold_in_walk_W = ["hub-s0170"]
    walk_pred = {"hub-s0170"}
    dump_pred = set(full_gold)

    walk_fixed = score_llm_full_gold(walk_pred, full_gold)
    dump_fixed = score_llm_full_gold(dump_pred, full_gold)
    walk_invalid = score_llm_INVALID_gold_cap_W(walk_pred, gold_in_walk_W)

    assert abs(walk_fixed - 0.20) < 1e-12, walk_fixed
    assert dump_fixed == 1.0, dump_fixed
    assert walk_invalid == 1.0, walk_invalid  # the false “perfect”

    # If every session extracted gold∩W perfectly, INVALID would report 200/200.
    print("FIXED session 170: walk score_llm=0.20 (1/5), dump=1.00")
    print("INVALID gold∩W on the same walk extract: 1.00 — NOT the claim")
    print("check-scorer: ok")
    return 0


def paper_summary_note() -> None:
    data = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    print(
        "Paper record (do not cite the invalid gold∩W 200/200 run):\n"
        f"  verdict={data['verdict']} n_both_perfect={data['n_both_perfect']}\n"
        f"  n_walk_imperfect_llm={data['n_walk_imperfect_llm']} "
        f"n_dump_imperfect_llm={data['n_dump_imperfect_llm']}\n"
        f"  mean Δ={data['stats_both_perfect']['mean']} "
        f"CI={data['stats_both_perfect']['ci95']}\n"
        f"  T>0={data['T_gt_0']}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-scorer",
        action="store_true",
        help="Run FIXED vs INVALID scorer checks (no API, no MemNet).",
    )
    args = parser.parse_args()
    if args.check_scorer or os.environ.get("P1_LLM_CHECK", "").strip() in {
        "1",
        "true",
        "TRUE",
        "yes",
    }:
        return check_scorer()

    dry = os.environ.get("P1_LLM_DRY", "").strip() in {"1", "true", "TRUE", "yes"}
    key = (os.environ.get("OPENROUTER_API_KEY") or "").strip() or None
    if not dry and not key:
        print(
            "OPENROUTER_API_KEY missing. Export it (never commit), "
            "or run --check-scorer / P1_LLM_DRY=1.\n"
            "Paper verdict is experiments/p1-llm/results.summary.json; "
            "a live re-run is not required to read the record.",
            file=sys.stderr,
        )
        paper_summary_note()
        return 2

    if dry:
        print(
            "P1_LLM_DRY=1: not a paper verdict. Scorer lock is full_gold. "
            "Invalid gold∩W 200/200 must not be cited."
        )
        paper_summary_note()
        check_scorer()
        LIVE_PATH.write_text(
            json.dumps(
                {
                    "dry_run": True,
                    "note": "Not a paper verdict. See results.summary.json.",
                    "scorer": "full_gold",
                    "invalid_prior": "gold∩W 200/200 MUST NOT be cited",
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
        f"T={TEMPERATURE}, FIXED score_llm=full_gold. "
        "Do not restore the gold∩W scorer. Do not commit the API key."
    )
    paper_summary_note()
    return 0


if __name__ == "__main__":
    sys.exit(main())
