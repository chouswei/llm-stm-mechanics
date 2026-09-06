#!/usr/bin/env python3
"""ShapeWalk vs Dump vs RAG lexical top-k — T>0 band (p1-tgt0 stack).

Lock: experiments/shapewalk-vs-rag-tgt0/PROTOCOL.md (preregistered; do not retune).
Parent T=0 lock: experiments/shapewalk-vs-rag/results.summary.json (do not overwrite).
p1-tgt0 sibling: experiments/p1-tgt0/ (two-arm dump contrast; do not overwrite).

Authoritative Â / PASS numbers do not exist until a locked live run is written
under SHAPEWALK_VS_RAG_TGT0_WRITE=1. Default live writes results.live.json only.

W builders are imported from experiments/shapewalk-vs-rag/run_shapewalk_vs_rag.py
(same k, Jaccard, pin_map, dump). T=0.8 and n_seeds=20 are locked to p1-tgt0.

Per seed: full-gold score_llm + noise_leak (p1-llm-hard).
Per arm: score_mean, noise_leak_any; Â uses ℓ = 1 − score_mean.

Full live generate load: 200 sessions × 3 arms × 20 seeds = 12_000 calls.
Use --limit for smoke. That is not a protocol verdict.

Env:
  OPENROUTER_API_KEY                required for a live generate (never commit)
  OPENROUTER_BASE_URL               default https://openrouter.ai/api/v1
  P1_LLM_MODEL                      default openai/gpt-4o-mini
  SHAPEWALK_VS_RAG_TGT0_WRITE        if 1, also write results.summary.json after a
                                    real live run (do not set from a different
                                    model / package / T / n_seeds / scorer)
  SHAPEWALK_VS_RAG_TGT0_DRY         if 1, W-stats only (not a paper verdict)

No secrets in this file. No MemNet SemVer claim. Not an OM theorem.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEX_DIR = HERE.parent / "shapewalk-vs-rag"
P1_TGT0_DIR = HERE.parent / "p1-tgt0"
PARENT_SUMMARY = LEX_DIR / "results.summary.json"
P1_TGT0_SUMMARY = P1_TGT0_DIR / "results.summary.json"
SUMMARY_PATH = HERE / "results.summary.json"
LIVE_PATH = HERE / "results.live.json"

sys.path.insert(0, str(LEX_DIR))
sys.path.insert(0, str(P1_TGT0_DIR))

import run_p1_tgt0 as tgt0  # noqa: E402
import run_shapewalk_vs_rag as lex  # noqa: E402

# --- Preregistered protocol constants (FIXED; match PROTOCOL.md / p1-tgt0) ---
MEMNET_PACKAGE = "memnet-llm==0.19.5"
MEMNET_PACKAGE_OK = ("0.19.5", "0.19.4")
K_HOP = lex.K_HOP
M_WALK = lex.M_WALK
RAG_K = lex.RAG_K
CUE_KIND = lex.CUE_KIND
COEF_A = lex.COEF_A
COEF_B = lex.COEF_B
COEF_C = lex.COEF_C
COEF_D = lex.COEF_D
N_SESSIONS = lex.N_SESSIONS
N_TRIPLE_MIN = lex.N_TRIPLE_MIN
BOOTSTRAP_B = lex.BOOTSTRAP_B
BOOTSTRAP_SEED = lex.BOOTSTRAP_SEED
DEFAULT_BASE = lex.DEFAULT_BASE
DEFAULT_MODEL = lex.DEFAULT_MODEL
TEMPERATURE = tgt0.TEMPERATURE  # 0.8
N_SEEDS = tgt0.N_SEEDS  # 20
MAX_TOKENS = lex.MAX_TOKENS
HTTP_RETRIES = lex.HTTP_RETRIES
N_GENERATE_FULL = N_SESSIONS * 3 * N_SEEDS  # 12_000

SCHEMA_PATH = lex.SCHEMA_PATH


def score_mean(scores: list[float]) -> float:
    return tgt0.score_mean(scores)


def noise_leak_any(preds: list[set[str]]) -> bool:
    return tgt0.noise_leak_any(preds)


def equal_quality_primary(mean_score: float, leak_any: bool) -> bool:
    return tgt0.equal_quality_primary(mean_score, leak_any)


def locked_block() -> dict:
    block = lex.locked_block()
    block["memnet_package"] = MEMNET_PACKAGE
    block["temperature"] = TEMPERATURE
    block["n_seeds"] = N_SEEDS
    block["scorer"] = "score_mean of full_gold_evidence"
    block["equal_quality"] = "score_mean==1.0 AND NOT noise_leak_any"
    block["ell_task"] = "1-score_mean"
    block["t0_parent"] = "experiments/shapewalk-vs-rag/"
    block["p1_tgt0_sibling"] = "experiments/p1-tgt0/"
    block["n_generate_full"] = N_GENERATE_FULL
    block["stochasticity"] = "path measure; measurement band; not OM theorem"
    block["semver_claim"] = False
    return block


def write_flag_set() -> bool:
    return os.environ.get("SHAPEWALK_VS_RAG_TGT0_WRITE", "").strip() in {
        "1",
        "true",
        "TRUE",
        "yes",
    }


def evaluate_arm_tgt0(graph: lex.GraphObs, w: list[lex.NodeObs], pred_texts: list[str]) -> dict:
    """Aggregate n_seeds generates on a fixed W (p1-tgt0 scoring)."""
    gold_ev = lex.full_gold_evidence(graph.session_i, list(graph.gold_slugs))
    tokens = sum(lex.node_tokens(n.title, n.slug) for n in w)
    seed_rows: list[dict] = []
    scores: list[float] = []
    preds: list[set[str]] = []
    for i, text in enumerate(pred_texts):
        pred = lex.parse_pred_values(text)
        score = lex.score_llm_full_gold_evidence(pred, gold_ev)
        leak = lex.noise_leak(pred)
        scores.append(score)
        preds.append(pred)
        seed_rows.append(
            {
                "seed": i,
                "score_llm": score,
                "noise_leak": leak,
                "pred": sorted(pred),
            }
        )
    mean = score_mean(scores)
    leak_any = noise_leak_any(preds)
    ahat = lex.action_estimate(w_size=len(w), tokens=tokens, score=mean)
    gold = lex.gold_in_w(graph, w)
    return {
        "w_size": len(w),
        "tokens": tokens,
        "n_gold_in_w": len(gold),
        "gold_in_w": gold,
        "score_mean": mean,
        "noise_leak_any": leak_any,
        "n_seeds": len(pred_texts),
        "A_hat": ahat,
        "equal_quality": equal_quality_primary(mean, leak_any),
        "w_slugs": [n.slug for n in w],
        "seeds": seed_rows,
    }


def compact_arm(row: dict) -> dict:
    return {
        "w_size": row["w_size"],
        "n_gold_in_w": row["n_gold_in_w"],
        "score_mean": row["score_mean"],
        "noise_leak_any": row["noise_leak_any"],
        "A_hat": row["A_hat"],
        "equal_quality": row["equal_quality"],
        "tokens": row["tokens"],
        "n_seeds": row["n_seeds"],
    }


def primary_verdict(n_triple: int, rag_stats: dict, dump_stats: dict) -> tuple[str, str]:
    if n_triple < N_TRIPLE_MIN:
        return (
            "FAIL",
            f"n_triple={n_triple} < n_triple_min={N_TRIPLE_MIN}. Pairwise equal-quality "
            "is secondary and does not rescue a triple FAIL.",
        )
    rag_mean = rag_stats.get("mean")
    dump_mean = dump_stats.get("mean")
    rag_ok = (
        rag_mean is not None
        and float(rag_mean) > 0.0
        and lex.ci_excludes_zero_positive(rag_stats.get("ci95") or [None, None])
    )
    dump_ok = (
        dump_mean is not None
        and float(dump_mean) > 0.0
        and lex.ci_excludes_zero_positive(dump_stats.get("ci95") or [None, None])
    )
    if rag_ok and dump_ok:
        return (
            "PASS",
            "Equal-quality triples (score_mean==1.0 AND NOT noise_leak_any): "
            "mean Δ_RAG>0 and CI excludes 0; mean Δ_dump>0 and CI excludes 0; "
            f"n_triple>={N_TRIPLE_MIN}; T={TEMPERATURE}; n_seeds={N_SEEDS}; "
            "coefficients not retuned; scorer is full-gold evidence + "
            "noise_leak_any gate.",
        )
    bits = []
    if not rag_ok:
        bits.append(
            f"Δ_RAG mean={rag_mean} ci={rag_stats.get('ci95')} "
            "(need mean>0 and CI excluding 0)"
        )
    if not dump_ok:
        bits.append(
            f"Δ_dump mean={dump_mean} ci={dump_stats.get('ci95')} "
            "(need mean>0 and CI excluding 0)"
        )
    return "FAIL", "; ".join(bits)


def check_scorer() -> int:
    """Lexical RAG/firewall checks plus T>0 score_mean / noise_leak_any gates."""
    rc = lex.check_scorer()
    if rc != 0:
        return rc

    assert TEMPERATURE == 0.8, TEMPERATURE
    assert N_SEEDS == 20, N_SEEDS
    assert tgt0.TEMPERATURE == TEMPERATURE
    assert tgt0.N_SEEDS == N_SEEDS
    assert RAG_K == 12 and RAG_K == M_WALK
    assert COEF_A == 1.0 and COEF_B == 1.0 and COEF_C == 0.0 and COEF_D == 10.0
    assert N_TRIPLE_MIN == 30
    assert BOOTSTRAP_B == 10_000 and BOOTSTRAP_SEED == 42
    assert N_GENERATE_FULL == 12_000

    session_i = 170
    gold_slugs = [
        "hub-s0170",
        "usr-s0170-g0",
        "usr-s0170-g1",
        "usr-s0170-g2",
        "usr-s0170-g3",
    ]
    gold = lex.full_gold_evidence(session_i, gold_slugs)
    walk_resident = {lex.evidence_value(session_i, "hub-s0170")}
    walk_noise = {lex.noise_value(session_i, "decoy-s0170")}
    dump_pred = set(gold)

    seeds_perfect = [1.0] * N_SEEDS
    seeds_mixed = [1.0] * (N_SEEDS - 1) + [0.8]
    assert abs(score_mean(seeds_perfect) - 1.0) < 1e-12
    assert score_mean(seeds_mixed) < 1.0
    assert not noise_leak_any([walk_resident] * N_SEEDS)
    assert noise_leak_any(
        [walk_resident] * (N_SEEDS - 1) + [walk_resident | walk_noise]
    )
    assert equal_quality_primary(score_mean(seeds_perfect), False)
    assert not equal_quality_primary(score_mean(seeds_mixed), False)
    assert not equal_quality_primary(1.0, True)

    hub = lex.NodeObs("HUB", "hub-s0000", "Star hub s0000")
    decoy = lex.NodeObs("NOISE", "zzzz-noise", "unrelated blob")
    graph = lex.GraphObs(
        session_i=0,
        family="check",
        hub_slug="hub-s0000",
        gold_slugs=("hub-s0000",),
        nodes=(hub, decoy),
        edges=(),
        raw={},
    )
    perfect_texts = [lex.evidence_value(0, "hub-s0000")] * N_SEEDS
    leaked_texts = perfect_texts[:-1] + [lex.noise_value(0, "zzzz-noise")]
    walk_w = [hub]
    ok_arm = evaluate_arm_tgt0(graph, walk_w, perfect_texts)
    assert ok_arm["equal_quality"]
    assert abs(ok_arm["score_mean"] - 1.0) < 1e-12
    assert not ok_arm["noise_leak_any"]
    assert abs(ok_arm["A_hat"] - lex.action_estimate(w_size=1, tokens=lex.node_tokens(hub.title, hub.slug), score=1.0)) < 1e-12

    leak_arm = evaluate_arm_tgt0(graph, walk_w, leaked_texts)
    assert not leak_arm["equal_quality"]
    assert leak_arm["noise_leak_any"]

    mixed_pred = [lex.evidence_value(0, "hub-s0000")] * (N_SEEDS - 1) + ["nope"]
    mixed_arm = evaluate_arm_tgt0(graph, walk_w, mixed_pred)
    assert mixed_arm["score_mean"] < 1.0
    assert not mixed_arm["equal_quality"]

    empty = lex.bootstrap_ci([])
    v_fail, _ = primary_verdict(0, empty, empty)
    assert v_fail == "FAIL"
    pos = lex.bootstrap_ci([10.0] * 40)
    v_pass, _ = primary_verdict(40, pos, pos)
    assert v_pass == "PASS"
    v_n, _ = primary_verdict(10, pos, pos)
    assert v_n == "FAIL"

    assert PARENT_SUMMARY != SUMMARY_PATH
    assert P1_TGT0_SUMMARY != SUMMARY_PATH
    assert write_flag_set() is False or os.environ.get(
        "SHAPEWALK_VS_RAG_TGT0_WRITE", ""
    ).strip() in {"1", "true", "TRUE", "yes"}

    print(
        f"T>0 band: T={TEMPERATURE} n_seeds={N_SEEDS} "
        f"(locked to p1-tgt0); Â uses ℓ=1−score_mean"
    )
    print("primary gate: score_mean==1.0 AND NOT noise_leak_any (all three arms)")
    print(f"full live generate load: {N_GENERATE_FULL} calls; use --limit for smoke")
    print("parent T=0 summary is never written from this driver")
    print("check-scorer: ok")
    return 0


def run_dry(*, limit: int | None) -> int:
    graphs = lex.load_p1_hr_graphs(limit=limit)
    if not graphs:
        print(f"No p1-hr specs under {lex.P1_HR_SPECS}", file=sys.stderr)
        return 1
    arms = {
        "shapewalk_dry_standin": lex.build_w_shapewalk_dry_standin,
        "dump": lex.build_w_dump,
        "rag": lex.build_w_rag,
    }
    payload: dict = {
        "dry_run": True,
        "live_driver_shipped": True,
        "note": (
            "Not a paper verdict. ShapeWalk here is BFS k-hop cap-M, not "
            "pin_map. RAG lexical top-k is the real v1 scorer. T>0 generate "
            "is not run in --dry. See PROTOCOL.md."
        ),
        "locked": locked_block(),
        "n_graphs": len(graphs),
        "arms": {},
        "parent_summary_untouched": str(PARENT_SUMMARY),
    }
    print(
        "DRY (not a paper verdict). "
        f"n={len(graphs)} p1-hr specs. RAG k={RAG_K}. "
        f"T={TEMPERATURE} n_seeds={N_SEEDS} generate skipped. "
        "ShapeWalk = BFS stand-in, not pin_map."
    )
    for name, builder in arms.items():
        rows = [lex.w_stats_row(g, builder(g)) for g in graphs]
        summary = lex.summarise_arm(rows)
        payload["arms"][name] = {"summary": summary}
        print(
            f"  {name}: mean|W|={summary['mean_w']:.4f} "
            f"mean gold∩W={summary['mean_gold_in_w']:.4f} "
            f"mean gold coverage in W={summary['mean_gold_coverage_in_w']:.4f}"
        )
    LIVE_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {LIVE_PATH} (dry). Did not write {SUMMARY_PATH}.")
    print(f"Did not write parent {PARENT_SUMMARY}.")
    return 0


def _chat_complete(
    base: str, key: str, model: str, prompt: str, *, seed: int
) -> str:
    url = base.rstrip("/") + "/chat/completions"
    body = json.dumps(
        {
            "model": model,
            "temperature": TEMPERATURE,
            "max_tokens": MAX_TOKENS,
            "seed": seed,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    last_err: Exception | None = None
    for attempt in range(HTTP_RETRIES):
        req = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/chouswei/llm-stm-mechanics",
                "X-Title": "llm-stm-mechanics shapewalk-vs-rag-tgt0",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            choices = payload.get("choices") or []
            if not choices:
                raise RuntimeError(f"OpenRouter empty choices: {payload!r}"[:500])
            msg = (choices[0].get("message") or {}).get("content") or ""
            return str(msg)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:800]
            last_err = RuntimeError(f"OpenRouter HTTP {exc.code}: {detail}")
            if exc.code in {429, 500, 502, 503} and attempt + 1 < HTTP_RETRIES:
                time.sleep(2 ** attempt)
                continue
            raise last_err from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_err = exc
            if attempt + 1 < HTTP_RETRIES:
                time.sleep(2 ** attempt)
                continue
            raise
    raise last_err or RuntimeError("OpenRouter call failed")


def generate_seeds(prompt: str, key: str, base: str, model: str) -> list[str]:
    return [
        _chat_complete(base, key, model, prompt, seed=i) for i in range(N_SEEDS)
    ]


def _memnet_ok(version: str) -> bool:
    return any(version.startswith(v) for v in MEMNET_PACKAGE_OK)


def run_live(*, limit: int | None, key: str, base: str, model: str) -> int:
    graphs = lex.load_p1_hr_graphs(limit=limit)
    if not graphs:
        print(f"No p1-hr specs under {lex.P1_HR_SPECS}", file=sys.stderr)
        return 1
    if not SCHEMA_PATH.is_file():
        print(f"Missing schema {SCHEMA_PATH}", file=sys.stderr)
        return 1

    t0 = time.time()
    eng = lex.Engine()
    memnet_version = str(eng.memnet_version)
    if not _memnet_ok(memnet_version):
        print(
            f"warning: installed memnet {memnet_version} is not the protocol "
            f"pin {MEMNET_PACKAGE} (0.19.4 acceptable if recorded)",
            file=sys.stderr,
        )
    elif not memnet_version.startswith("0.19.5"):
        print(
            f"warning: installed memnet {memnet_version}; protocol prefers "
            f"{MEMNET_PACKAGE}",
            file=sys.stderr,
        )

    n_planned = len(graphs) * 3 * N_SEEDS
    sessions: list[dict] = []
    n_error = 0
    arm_names = ("shapewalk", "dump", "rag")

    print(
        f"LIVE three-arm OpenRouter generate (T>0). n={len(graphs)} "
        f"model={model} T={TEMPERATURE} n_seeds={N_SEEDS} "
        f"pin_map M={M_WALK} k={K_HOP} RAG k={RAG_K} memnet={memnet_version}. "
        f"Planned generate calls={n_planned} "
        f"(full protocol {N_GENERATE_FULL}). Not a paper summary unless "
        "SHAPEWALK_VS_RAG_TGT0_WRITE=1 after this locked run. "
        "Does not write the T=0 lexical summary."
    )

    for graph in graphs:
        try:
            ws = lex.live_w_for_session(eng, graph)
            arm_rows: dict[str, dict] = {}
            for name in arm_names:
                w = ws[name]
                prompt = lex.build_prompt(graph.session_i, w, graph.gold_slugs)
                texts = generate_seeds(prompt, key, base, model)
                arm_rows[name] = evaluate_arm_tgt0(graph, w, texts)
            a_walk = arm_rows["shapewalk"]["A_hat"]
            row = {
                "session_i": graph.session_i,
                "family": graph.family,
                "hub_slug": graph.hub_slug,
                "n_gold": len(graph.gold_slugs),
                "shapewalk": arm_rows["shapewalk"],
                "dump": arm_rows["dump"],
                "rag": arm_rows["rag"],
                "delta_rag": arm_rows["rag"]["A_hat"] - a_walk,
                "delta_dump": arm_rows["dump"]["A_hat"] - a_walk,
                "triple_equal_quality": all(
                    arm_rows[n]["equal_quality"] for n in arm_names
                ),
                "ok": True,
                "error": None,
            }
        except Exception as exc:  # noqa: BLE001
            n_error += 1
            row = {
                "session_i": graph.session_i,
                "family": graph.family,
                "ok": False,
                "error": f"{type(exc).__name__}: {exc}",
                "triple_equal_quality": False,
            }
        sessions.append(row)
        if row.get("ok"):
            sw, du, rg = row["shapewalk"], row["dump"], row["rag"]
            print(
                f"session {graph.session_i:04d} "
                f"walk |W|={sw['w_size']} gold∩W={sw['n_gold_in_w']} "
                f"score_mean={sw['score_mean']:.3f} leak_any={int(sw['noise_leak_any'])} "
                f"Â={sw['A_hat']:.2f} | "
                f"dump |W|={du['w_size']} gold∩W={du['n_gold_in_w']} "
                f"score_mean={du['score_mean']:.3f} leak_any={int(du['noise_leak_any'])} "
                f"Â={du['A_hat']:.2f} | "
                f"rag |W|={rg['w_size']} gold∩W={rg['n_gold_in_w']} "
                f"score_mean={rg['score_mean']:.3f} leak_any={int(rg['noise_leak_any'])} "
                f"Â={rg['A_hat']:.2f} triple={int(row['triple_equal_quality'])}",
                flush=True,
            )
        else:
            print(
                f"session {graph.session_i:04d} FAIL {row.get('error')}",
                flush=True,
            )

    ok_rows = [s for s in sessions if s.get("ok")]
    triples = [s for s in ok_rows if s.get("triple_equal_quality")]
    pair_rag = [
        s
        for s in ok_rows
        if s["shapewalk"]["equal_quality"] and s["rag"]["equal_quality"]
    ]
    pair_dump = [
        s
        for s in ok_rows
        if s["shapewalk"]["equal_quality"] and s["dump"]["equal_quality"]
    ]

    stats_triple_rag = lex.bootstrap_ci([s["delta_rag"] for s in triples])
    stats_triple_dump = lex.bootstrap_ci([s["delta_dump"] for s in triples])
    stats_pair_rag = lex.bootstrap_ci([s["delta_rag"] for s in pair_rag])
    stats_pair_dump = lex.bootstrap_ci([s["delta_dump"] for s in pair_dump])
    n_triple = len(triples)
    verdict, reason = primary_verdict(n_triple, stats_triple_rag, stats_triple_dump)

    n_leak = 0
    for s in ok_rows:
        if any(s[n]["noise_leak_any"] for n in arm_names):
            n_leak += 1

    elapsed = time.time() - t0
    write_summary = write_flag_set()
    payload = {
        "dry_run": False,
        "live_driver_shipped": True,
        "authoritative_summary": write_summary,
        "note": (
            "Live three-arm T>0 generate. results.summary.json is written only if "
            "SHAPEWALK_VS_RAG_TGT0_WRITE=1. This file is not a SemVer claim and "
            "does not overwrite the T=0 lexical PASS or p1-tgt0."
            if write_summary
            else (
                "Live three-arm T>0 generate wrote results.live.json only. "
                "Not an authoritative summary. Do not invent PASS for the "
                "paper without WRITE=1 after this locked protocol run."
            )
        ),
        "locked": locked_block(),
        "llm": {
            "provider": "OpenRouter",
            "model": model,
            "base": base,
            "temperature": TEMPERATURE,
            "n_seeds": N_SEEDS,
            "decoding": "T=0.8 n_seeds=20 (p1-tgt0 measurement band)",
        },
        "memnet_llm_version": memnet_version,
        "n_sessions": len(graphs),
        "n_ok": len(ok_rows),
        "n_error": n_error,
        "n_triple": n_triple,
        "n_pair_walk_rag": len(pair_rag),
        "n_pair_walk_dump": len(pair_dump),
        "n_noise_leak": n_leak,
        "n_generate_planned": n_planned,
        "stats_triple": {
            "delta_rag": stats_triple_rag,
            "delta_dump": stats_triple_dump,
        },
        "stats_pairwise_walk_rag": stats_pair_rag,
        "stats_pairwise_walk_dump": stats_pair_dump,
        "verdict": verdict,
        "verdict_reason": reason,
        "elapsed_s": elapsed,
        "call_counts": eng.calls,
        "parent_summary_untouched": str(PARENT_SUMMARY),
        "sessions": sessions,
    }
    LIVE_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        f"n_triple={n_triple} Δ_RAG mean={stats_triple_rag['mean']} "
        f"CI={stats_triple_rag['ci95']} Δ_dump mean={stats_triple_dump['mean']} "
        f"CI={stats_triple_dump['ci95']} verdict={verdict}"
    )
    print(f"Wrote {LIVE_PATH}.")

    if write_summary:
        summary = {
            "stratum": "shapewalk-vs-dump-vs-rag-lexical-topk-tgt0",
            "protocol": "experiments/shapewalk-vs-rag-tgt0/PROTOCOL.md",
            "honesty": (
                "graphs: Sage author-blind ACCEPT after regen "
                "(experiments/p1-blind/SAGE_SIGNOFF.md); not a SemVer a/b claim; "
                "measurement band not OM theorem"
            ),
            "memnet_llm_version": memnet_version,
            "coefficient_lock": {
                "a": COEF_A,
                "b": COEF_B,
                "c": COEF_C,
                "d": COEF_D,
                "d_empty_W": "|W|",
                "tokens": "sum(len(title)+len(slug))",
                "ell_task": "1-score_mean",
                "locked_before_outcomes": True,
                "retuned": False,
            },
            "llm": payload["llm"],
            "protocol_lock": payload["locked"],
            "n_sessions": len(graphs),
            "n_ok": len(ok_rows),
            "n_error": n_error,
            "n_triple": n_triple,
            "n_triple_min": N_TRIPLE_MIN,
            "n_pair_walk_rag": len(pair_rag),
            "n_pair_walk_dump": len(pair_dump),
            "n_noise_leak": n_leak,
            "stats_triple": payload["stats_triple"],
            "stats_pairwise_walk_rag": stats_pair_rag,
            "stats_pairwise_walk_dump": stats_pair_dump,
            "elapsed_s": elapsed,
            "verdict": verdict,
            "verdict_reason": reason,
            "parent_t0": "experiments/shapewalk-vs-rag/results.summary.json",
            "p1_tgt0": "experiments/p1-tgt0/results.summary.json",
            "sessions": [
                {
                    "session_i": s["session_i"],
                    "family": s.get("family"),
                    "ok": s.get("ok"),
                    "triple_equal_quality": s.get("triple_equal_quality"),
                    "delta_rag": s.get("delta_rag"),
                    "delta_dump": s.get("delta_dump"),
                    "shapewalk": compact_arm(s["shapewalk"]) if s.get("ok") else None,
                    "dump": compact_arm(s["dump"]) if s.get("ok") else None,
                    "rag": compact_arm(s["rag"]) if s.get("ok") else None,
                    "error": s.get("error"),
                }
                for s in sessions
            ],
            "harness": "experiments/shapewalk-vs-rag-tgt0/run_shapewalk_vs_rag_tgt0.py",
            "T_gt_0": True,
        }
        SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {SUMMARY_PATH} (SHAPEWALK_VS_RAG_TGT0_WRITE=1).")
        print(f"Did not write parent {PARENT_SUMMARY}.")
    else:
        print(
            f"Did not write {SUMMARY_PATH} "
            "(set SHAPEWALK_VS_RAG_TGT0_WRITE=1 after a locked run)."
        )

    print(reason)
    return 0 if n_error == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-scorer",
        action="store_true",
        help="Run T=0 lexical checks plus T>0 score_mean / noise_leak_any (no API).",
    )
    parser.add_argument(
        "--dry",
        action="store_true",
        help="Build W for three arms from p1-hr JSON; print |W| / gold∩W; no LLM.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional cap on number of p1-hr graphs (dry or live smoke).",
    )
    args = parser.parse_args()
    if args.check_scorer or os.environ.get("SHAPEWALK_VS_RAG_TGT0_CHECK", "").strip() in {
        "1",
        "true",
        "TRUE",
        "yes",
    }:
        return check_scorer()

    dry = args.dry or os.environ.get("SHAPEWALK_VS_RAG_TGT0_DRY", "").strip() in {
        "1",
        "true",
        "TRUE",
        "yes",
    }
    if dry:
        return run_dry(limit=args.limit)

    key = (os.environ.get("OPENROUTER_API_KEY") or "").strip() or None
    if not key:
        print(
            "OPENROUTER_API_KEY missing. Export it (never commit), "
            "or run --check-scorer / --dry.\n"
            "Live driver is shipped: with a key this script runs the full "
            f"{N_SESSIONS}-session three-arm generate at T={TEMPERATURE} with "
            f"n_seeds={N_SEEDS} ({N_GENERATE_FULL} generate calls). "
            "Use --limit for smoke. No results.summary.json unless "
            "SHAPEWALK_VS_RAG_TGT0_WRITE=1 after a locked run. "
            "Never writes experiments/shapewalk-vs-rag/results.summary.json. "
            "PROTOCOL.md is the lock.",
            file=sys.stderr,
        )
        return 2

    base = os.environ.get("OPENROUTER_BASE_URL", DEFAULT_BASE).strip() or DEFAULT_BASE
    model = os.environ.get("P1_LLM_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    return run_live(limit=args.limit, key=key, base=base, model=model)


if __name__ == "__main__":
    sys.exit(main())
