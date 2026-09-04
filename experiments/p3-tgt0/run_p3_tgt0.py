#!/usr/bin/env python3
"""STM Prediction 3 — T>0 CANONICAL distributional generation band.

memnet-llm 0.19.4. LLM via OpenRouter OpenAI-compatible API.
T=0 greedy remains the predeclared primary exact-match band.
T>0 CANONICAL uses N_SAMPLES_DIST draws and DIST_MATCH_BAND.
No secrets in this file.

Paper numbers live in results.summary.json (2026-09-04). A live re-run
writes results.json and must not overwrite the paper summary.

Env:
  OPENROUTER_API_KEY    required unless P3_GEN_DRY=1
  OPENROUTER_BASE_URL   default https://openrouter.ai/api/v1
  P3_GEN_MODEL          default openai/gpt-4o-mini
  P3_N_SESSIONS         default 8
  P3_N_PERMS            default 15
  P3_TGT0_TEMP          default 0.8
  P3_N_SAMPLES_DIST     default 5
  P3_DIST_MATCH_BAND    default 0.05
  P3_GEN_DRY            if 1, skip LLM; still count wire diffs
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

os.environ.setdefault("MEMNET_TEST_INLINE", "1")
os.environ.setdefault("MEMNET_SERVE_INTERNAL", "1")
os.environ.pop("MEMNET_NEO4J_URL", None)

HERE = Path(__file__).resolve().parent
P3_GEN_DIR = HERE.parent / "p3-gen"
P3_DIR = HERE.parent / "p3"
sys.path.insert(0, str(P3_GEN_DIR))
sys.path.insert(0, str(P3_DIR))

from run_p3 import (  # noqa: E402
    CUE_KIND,
    Engine,
    K_HOP,
    M_LIMIT,
    build_base_graph,
    capture_shape,
    permute_graph,
)
from run_p3_gen import (  # noqa: E402
    DROP_KEYS,
    MAX_TOKENS,
    TASK_INSTRUCTION,
    canonicalize_pin_map_text,
    parse_doc_slugs,
)

SCHEMA_PATH = P3_GEN_DIR / "schema.txt"
RESULTS_PATH = HERE / "results.json"

N_SESSIONS = int(os.environ.get("P3_N_SESSIONS", "8"))
N_PERMS = int(os.environ.get("P3_N_PERMS", "15"))
TGT0_TEMP = float(os.environ.get("P3_TGT0_TEMP", "0.8"))
N_SAMPLES_DIST = int(os.environ.get("P3_N_SAMPLES_DIST", "5"))
DIST_MATCH_BAND = float(os.environ.get("P3_DIST_MATCH_BAND", "0.05"))
MERGE_COMMIT = "1242c467bc9052360b4d61d754e944cc7ddf6cd9"

DEFAULT_BASE = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-4o-mini"


def _chat_complete(
    base: str, key: str, model: str, prompt: str, temperature: float
) -> str:
    url = base.rstrip("/") + "/chat/completions"
    body = json.dumps(
        {
            "model": model,
            "temperature": temperature,
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
            "X-Title": "llm-stm-mechanics P3-tgt0",
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


def generate(
    pin_map: str,
    dry: bool,
    key: str | None,
    base: str,
    model: str,
    temperature: float,
) -> str:
    if dry:
        return ",".join(parse_doc_slugs(pin_map))
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is unset (set it or P3_GEN_DRY=1)")
    return _chat_complete(base, key, model, pin_map, temperature)


def slug_key(text: str) -> tuple[str, ...]:
    return tuple(parse_doc_slugs(text))


def exact_match_rate(orig_keys: list[tuple[str, ...]], perm_keys: list[tuple[str, ...]]) -> float:
    """Histogram overlap (1 - total variation) over parsed slug-list keys."""
    n = len(orig_keys)
    if n == 0 or n != len(perm_keys):
        return 0.0
    co = Counter(orig_keys)
    cp = Counter(perm_keys)
    overlap = sum(min(co[k], cp[k]) for k in set(co) | set(cp))
    return overlap / n


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

    import run_p3 as p3mod

    p3mod.SCHEMA_PATH = SCHEMA_PATH

    eng = Engine()
    raw_mismatch = 0
    canon_mismatch = 0
    raw_id_wire_diff = 0
    canon_text_diff = 0
    hid_leaks = 0
    build_fail = 0
    pair_rates: list[float] = []
    api_calls = 0

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
        orig_raw_ans = generate(orig.raw, dry, key, base, model, 0.0)
        orig_canon_ans = generate(orig_canon, dry, key, base, model, 0.0)
        api_calls += 0 if dry else 2
        orig_raw_slugs = parse_doc_slugs(orig_raw_ans)
        orig_canon_slugs = parse_doc_slugs(orig_canon_ans)
        orig_dist = [
            slug_key(generate(orig_canon, dry, key, base, model, TGT0_TEMP))
            for _ in range(N_SAMPLES_DIST)
        ]
        api_calls += 0 if dry else N_SAMPLES_DIST

        for p in range(N_PERMS):
            perm = permute_graph(base_g, p + 1)
            got = capture_shape(eng, perm)
            if got.exit_code != 0 or not got.raw:
                build_fail += 1
                raw_mismatch += 1
                canon_mismatch += 1
                pair_rates.append(0.0)
                continue
            if got.hid_leak:
                hid_leaks += 1
            got_canon = canonicalize_pin_map_text(got.raw)
            if orig.raw != got.raw:
                raw_id_wire_diff += 1
            if orig_canon != got_canon:
                canon_text_diff += 1
            perm_raw_ans = generate(got.raw, dry, key, base, model, 0.0)
            perm_canon_ans = generate(got_canon, dry, key, base, model, 0.0)
            api_calls += 0 if dry else 2
            if orig_raw_slugs != parse_doc_slugs(perm_raw_ans):
                raw_mismatch += 1
            if orig_canon_slugs != parse_doc_slugs(perm_canon_ans):
                canon_mismatch += 1
            perm_dist = [
                slug_key(generate(got_canon, dry, key, base, model, TGT0_TEMP))
                for _ in range(N_SAMPLES_DIST)
            ]
            api_calls += 0 if dry else N_SAMPLES_DIST
            pair_rates.append(exact_match_rate(orig_dist, perm_dist))
        print(
            f"session {s:02d} raw_mm={raw_mismatch} canon_mm={canon_mismatch} "
            f"mean_emr={sum(pair_rates) / len(pair_rates) if pair_rates else 0:.3f} "
            f"elapsed={time.time() - t0:.1f}s",
            flush=True,
        )

    n_compare = N_SESSIONS * N_PERMS
    mean_emr = sum(pair_rates) / len(pair_rates) if pair_rates else 0.0
    min_emr = min(pair_rates) if pair_rates else 0.0
    tgt0_pass = (1.0 - mean_emr) <= DIST_MATCH_BAND and (1.0 - min_emr) <= DIST_MATCH_BAND
    raw_verdict = "FAIL" if raw_mismatch else "PASS"
    canon_verdict = "FAIL" if canon_mismatch else "PASS"
    tgt0_verdict = "PASS" if tgt0_pass else "FAIL"
    if dry:
        raw_verdict = "DRY (not a paper verdict)"
        canon_verdict = "DRY (not a paper verdict)"
        tgt0_verdict = "DRY (not a paper verdict)"

    results = {
        "memnet_llm_version": MEMNET_VERSION,
        "merge_commit": MERGE_COMMIT,
        "pr_ranking_fix": 147,
        "pr_nickname_off_wire": 148,
        "dry_run": dry,
        "semver_a_claim": False,
        "semver_b_claim": False,
        "llm": {
            "provider": "OpenRouter",
            "model": model,
            "base": base,
            "max_tokens": MAX_TOKENS,
            "skipped": dry,
        },
        "protocol": {
            "n_sessions": N_SESSIONS,
            "n_perms": N_PERMS,
            "n_pairs": n_compare,
            "M": M_LIMIT,
            "k": K_HOP,
            "cue_kind": CUE_KIND,
            "task": TASK_INSTRUCTION,
            "DROP_KEYS": sorted(DROP_KEYS),
            "T_gt_0": {
                "temperature": TGT0_TEMP,
                "N_SAMPLES_DIST": N_SAMPLES_DIST,
                "DIST_MATCH_BAND": DIST_MATCH_BAND,
            },
        },
        "verdicts": {
            "T0_RAW": {
                "verdict": raw_verdict,
                "mismatches": raw_mismatch,
                "n_compare": n_compare,
            },
            "T0_CANONICAL": {
                "verdict": canon_verdict,
                "mismatches": canon_mismatch,
                "n_compare": n_compare,
            },
            "T_gt_0_CANONICAL": {
                "verdict": tgt0_verdict,
                "mean_exact_match_rate": mean_emr,
                "min_exact_match_rate": min_emr,
                "n_pairs": len(pair_rates),
            },
        },
        "counts": {
            "raw_id_wire_diff_events": raw_id_wire_diff,
            "canon_text_diff_events": canon_text_diff,
            "hid_leaks": hid_leaks,
            "build_fail": build_fail,
        },
        "openrouter_calls": api_calls,
        "elapsed_s": round(time.time() - t0, 3),
        "paper_summary": str(HERE / "results.summary.json"),
        "note": (
            "Paper numbers are results.summary.json (OpenRouter gpt-4o-mini, 2026-09-04). "
            "This file is a re-run artifact. No secrets. No SemVer a or b claim."
        ),
    }
    RESULTS_PATH.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"verdicts": results["verdicts"], "counts": results["counts"]}, indent=2))
    if dry:
        return 0
    ok = (
        raw_mismatch == 0
        and canon_mismatch == 0
        and build_fail == 0
        and tgt0_pass
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
