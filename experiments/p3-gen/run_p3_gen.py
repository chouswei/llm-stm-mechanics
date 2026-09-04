#!/usr/bin/env python3
"""STM Prediction 3 — generation half (rename invariance after generate).

MemNet @ eff05dc8 (PR #147). LLM via OpenRouter OpenAI-compatible API.
T=0 greedy is the predeclared primary band. No secrets in this file.

Conditions:
  RAW        — pin_map as emitted (nickname id may be on the wire)
  CANONICAL  — strip id/hid from pin_map text; preserve row order

Task: list DOC slug fields in order, comma-separated.
Compare orig vs isomorphic CREATE-order / nickname permutation answers.

Env:
  OPENROUTER_API_KEY   required unless P3_GEN_DRY=1
  OPENROUTER_BASE_URL  default https://openrouter.ai/api/v1
  P3_GEN_MODEL         default openai/gpt-4o-mini
  P3_N_SESSIONS        default 8
  P3_N_PERMS           default 15
  P3_GEN_DRY           if 1, skip LLM; still count wire diffs
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

os.environ.setdefault("MEMNET_TEST_INLINE", "1")
os.environ.setdefault("MEMNET_SERVE_INTERNAL", "1")
os.environ.pop("MEMNET_NEO4J_URL", None)

HERE = Path(__file__).resolve().parent
P3_DIR = HERE.parent / "p3"
sys.path.insert(0, str(P3_DIR))

from run_p3 import (  # noqa: E402
    CUE_KIND,
    Engine,
    HID_LEAK_RE,
    K_HOP,
    M_LIMIT,
    MERGE_COMMIT,
    PROP_RE,
    build_base_graph,
    capture_shape,
    permute_graph,
)

SCHEMA_PATH = HERE / "schema.txt"
RESULTS_PATH = HERE / "results.json"
REPORT_PATH = HERE / "REPORT.md"

N_SESSIONS = int(os.environ.get("P3_N_SESSIONS", "8"))
N_PERMS = int(os.environ.get("P3_N_PERMS", "15"))
DROP_KEYS = frozenset({"id", "hid"})
DOC_SLUG_RE = re.compile(r"doc-s\d+-n\d+")
BRACE_RE = re.compile(r"\{([^}]*)\}")

DEFAULT_BASE = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-4o-mini"
MAX_TOKENS = 256
TEMPERATURE = 0.0

TASK_INSTRUCTION = (
    "List the DOC slug fields in the order they appear in the pin_map, "
    "comma-separated. Output only the slugs, nothing else."
)


def canonicalize_pin_map_text(raw: str) -> str:
    """Strip id/hid properties; keep remaining keys and row order."""

    def _repl(match: re.Match[str]) -> str:
        kept: list[str] = []
        for key, val in PROP_RE.findall(match.group(1)):
            if key not in DROP_KEYS:
                kept.append(f"{key}: '{val}'")
        return "{" + ", ".join(kept) + "}"

    lines = [BRACE_RE.sub(_repl, line) for line in raw.splitlines()]
    text = "\n".join(lines)
    if raw.endswith("\n"):
        text += "\n"
    return text


def parse_doc_slugs(text: str) -> list[str]:
    return DOC_SLUG_RE.findall(text or "")


def _chat_complete(base: str, key: str, model: str, prompt: str) -> str:
    url = base.rstrip("/") + "/chat/completions"
    body = json.dumps(
        {
            "model": model,
            "temperature": TEMPERATURE,
            "max_tokens": MAX_TOKENS,
            "messages": [
                {
                    "role": "user",
                    "content": f"{TASK_INSTRUCTION}\n\npin_map:\n{prompt}",
                }
            ],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/chouswei/llm-stm-mechanics",
            "X-Title": "llm-stm-mechanics P3-gen",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:800]
        raise RuntimeError(f"OpenRouter HTTP {exc.code}: {detail}") from exc
    choices = payload.get("choices") or []
    if not choices:
        raise RuntimeError(f"OpenRouter empty choices: {payload!r}"[:500])
    msg = (choices[0].get("message") or {}).get("content") or ""
    return str(msg)


def generate(pin_map: str, dry: bool, key: str | None, base: str, model: str) -> str:
    if dry:
        return ",".join(parse_doc_slugs(pin_map))
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is unset (set it or P3_GEN_DRY=1)")
    return _chat_complete(base, key, model, pin_map)


def main() -> int:
    t0 = time.time()
    if "--dry-run" in sys.argv:
        os.environ["P3_GEN_DRY"] = "1"
    dry = os.environ.get("P3_GEN_DRY", "").strip() in {"1", "true", "TRUE", "yes"}
    key = os.environ.get("OPENROUTER_API_KEY") or None
    if key:
        key = key.strip() or None
    base = os.environ.get("OPENROUTER_BASE_URL", DEFAULT_BASE).strip() or DEFAULT_BASE
    model = os.environ.get("P3_GEN_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL

    if not dry and not key:
        print(
            "OPENROUTER_API_KEY missing. Export it, or run P3_GEN_DRY=1 "
            "for the pin_map / wire-diff half only.",
            file=sys.stderr,
        )
        return 2

    from memnet import __version__ as MEMNET_VERSION

    # Point Engine at this directory's schema (run_p3 binds SCHEMA_PATH at import).
    import run_p3 as p3mod

    p3mod.SCHEMA_PATH = SCHEMA_PATH

    eng = Engine()
    raw_mismatch = 0
    canon_mismatch = 0
    raw_id_wire_diff = 0
    canon_text_diff = 0
    hid_leaks = 0
    build_fail = 0
    examples: list[dict] = []

    for s in range(N_SESSIONS):
        base_g = build_base_graph(s)
        orig = capture_shape(eng, base_g)
        if orig.exit_code != 0 or not orig.raw:
            build_fail += 1
            print(f"session {s:02d} ORIG FAIL {orig.stderr[-200:]}", flush=True)
            continue
        if orig.hid_leak:
            hid_leaks += 1
        orig_canon = canonicalize_pin_map_text(orig.raw)
        orig_raw_ans = generate(orig.raw, dry, key, base, model)
        orig_canon_ans = generate(orig_canon, dry, key, base, model)
        orig_raw_slugs = parse_doc_slugs(orig_raw_ans)
        orig_canon_slugs = parse_doc_slugs(orig_canon_ans)

        for p in range(N_PERMS):
            perm = permute_graph(base_g, p + 1)
            got = capture_shape(eng, perm)
            if got.exit_code != 0 or not got.raw:
                build_fail += 1
                raw_mismatch += 1
                canon_mismatch += 1
                continue
            if got.hid_leak:
                hid_leaks += 1
            got_canon = canonicalize_pin_map_text(got.raw)
            if orig.raw != got.raw:
                raw_id_wire_diff += 1
            if orig_canon != got_canon:
                canon_text_diff += 1
            perm_raw_ans = generate(got.raw, dry, key, base, model)
            perm_canon_ans = generate(got_canon, dry, key, base, model)
            perm_raw_slugs = parse_doc_slugs(perm_raw_ans)
            perm_canon_slugs = parse_doc_slugs(perm_canon_ans)
            if orig_raw_slugs != perm_raw_slugs:
                raw_mismatch += 1
                if len(examples) < 5:
                    examples.append(
                        {
                            "kind": "raw_mismatch",
                            "session_i": s,
                            "perm_i": p + 1,
                            "orig_slugs": orig_raw_slugs,
                            "perm_slugs": perm_raw_slugs,
                            "orig_answer": orig_raw_ans,
                            "perm_answer": perm_raw_ans,
                        }
                    )
            if orig_canon_slugs != perm_canon_slugs:
                canon_mismatch += 1
                if len(examples) < 8:
                    examples.append(
                        {
                            "kind": "canon_mismatch",
                            "session_i": s,
                            "perm_i": p + 1,
                            "orig_slugs": orig_canon_slugs,
                            "perm_slugs": perm_canon_slugs,
                        }
                    )
        print(
            f"session {s:02d} raw_mm={raw_mismatch} canon_mm={canon_mismatch} "
            f"wire_raw={raw_id_wire_diff} wire_canon={canon_text_diff} "
            f"elapsed={time.time() - t0:.1f}s",
            flush=True,
        )

    n_compare = N_SESSIONS * N_PERMS
    # Paper verdict is the OpenRouter T=0 run in results.summary.json.
    # A live re-run reports its own counts; dry-run is not a verdict.
    raw_verdict = "FAIL" if raw_mismatch else "PASS"
    canon_verdict = "FAIL" if canon_mismatch else "PASS"
    if dry:
        raw_verdict = "DRY (not a paper verdict)"
        canon_verdict = "DRY (not a paper verdict)"

    results = {
        "memnet_llm_version": MEMNET_VERSION,
        "merge_commit": MERGE_COMMIT,
        "pr_ranking_fix": 147,
        "dry_run": dry,
        "semver_claim": False,
        "llm": {
            "provider": "OpenRouter",
            "model": model,
            "base": base,
            "temperature": TEMPERATURE,
            "max_tokens": MAX_TOKENS,
            "skipped": dry,
        },
        "protocol": {
            "n_sessions": N_SESSIONS,
            "n_perms": N_PERMS,
            "n_compare": n_compare,
            "M": M_LIMIT,
            "k": K_HOP,
            "cue_kind": CUE_KIND,
            "task": TASK_INSTRUCTION,
            "conditions": ["RAW", "CANONICAL"],
            "DROP_KEYS": sorted(DROP_KEYS),
        },
        "verdicts": {
            "RAW": {
                "verdict": raw_verdict,
                "mismatches": raw_mismatch,
                "n_compare": n_compare,
            },
            "CANONICAL": {
                "verdict": canon_verdict,
                "mismatches": canon_mismatch,
                "n_compare": n_compare,
            },
            "T_gt_0_CANONICAL": "OPEN",
        },
        "counts": {
            "raw_id_wire_diff_events": raw_id_wire_diff,
            "canon_text_diff_events": canon_text_diff,
            "hid_leaks": hid_leaks,
            "build_fail": build_fail,
        },
        "nickname_on_wire_failure_mode": raw_id_wire_diff == n_compare
        and canon_text_diff == 0,
        "api": {"call_counts": eng.calls},
        "examples": examples,
        "elapsed_s": round(time.time() - t0, 3),
        "paper_summary": str(HERE / "results.summary.json"),
        "note": (
            "Paper numbers are results.summary.json (OpenRouter gpt-4o-mini, 2026-09-04). "
            "This file is a re-run artifact. Discarded tiny-gpt2 partials are not a verdict. "
            "No SemVer product cut; nickname-off-wire is a separate MemNet PR."
        ),
    }
    RESULTS_PATH.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"verdicts": results["verdicts"], "counts": results["counts"]}, indent=2))
    return 0 if not dry and canon_mismatch == 0 and build_fail == 0 else (0 if dry else 1)


if __name__ == "__main__":
    raise SystemExit(main())
