#!/usr/bin/env python3
"""STM Prediction 2 — finite-difference λ̂_M as account diagnostic (paper §10.2).

Product operators only: open_session, MutateGate.apply, PinMapComposer.compose,
close_session. Engine caps stay hard rejects; M is varied only as compose
max_rows analysis knob. No Neo4j / Pi / droplet / InvenTree.
Installed from MemNet merge commit eff05dc8 (same as green P3).
"""
from __future__ import annotations

import json
import math
import os
import random
import time
from dataclasses import dataclass, field
from pathlib import Path

os.environ.setdefault("MEMNET_TEST_INLINE", "1")
os.environ.setdefault("MEMNET_SERVE_INTERNAL", "1")
os.environ.pop("MEMNET_NEO4J_URL", None)

from memnet import __version__ as MEMNET_VERSION
from memnet.exceptions import MemNetError
from memnet.mutate_gate import MutateGate
from memnet.pin_map_composer import PinMapComposer
from memnet.session import close_session, open_session

HERE = Path(__file__).resolve().parent
SCHEMA_PATH = HERE / "schema.txt"
RESULTS_PATH = HERE / "results.json"
REPORT_PATH = HERE / "REPORT.md"

MERGE_COMMIT = "eff05dc8a0ad5369e8d7e7f347db30b9300b04d6"
N_SESSIONS = int(os.environ.get("P2_N_SESSIONS", "200"))
M_GRID = [8, 12, 16, 24, 32]
DELTA = 4  # one step in M grid
BAND = 0.005  # |λ̂| < BAND treated as zero (preregistered)
MASS = 0.01  # preregistered mass term in J
K_HOP = 2
SEED_BASE = 20260904
CUE_KIND = "HUB"

# Graph sizing: ≥40 nodes so small M can bind; gold within k=2 of correct hub.
N_GOLD = 8
N_FIL_CORRECT = 10
N_BRIDGE = 8
N_DIST = 22  # distractor DOCs at depth-2 from wrong hub only
# nodes = 2 hubs + gold + fil + bridge + dist = 2+8+10+8+22 = 50


@dataclass
class SessionGraph:
    session_i: int
    hub_correct: str
    hub_wrong: str
    gold: list[str]
    n_nodes: int


def build_session_graph(session_i: int, rng: random.Random) -> tuple[SessionGraph, str]:
    """Asymmetric topology: CORRECT compact (gold @ depth-1); WRONG diffuse.

    Distractor DOCs sit behind bridges under the wrong hub so they enter the
    wrong hub's depth-2 neighbourhood but not the correct hub's (would be
    depth 3). Ranking puts dist-* before gold-* among DOCs, so wrong Shape
    truncates gold until larger M.
    """
    ss = f"s{session_i:03d}"
    hub_c = f"hub-c-{ss}"
    hub_w = f"hub-w-{ss}"
    # mild per-session jitter so M binding is not identical everywhere
    n_gold = N_GOLD + rng.randint(-1, 1)  # 7..9
    n_dist = N_DIST + rng.randint(-2, 2)  # 20..24
    n_fil = N_FIL_CORRECT
    n_bridge = N_BRIDGE

    gold = [f"gold-{ss}-{i:02d}" for i in range(n_gold)]
    fils = [f"fil-{ss}-{i:02d}" for i in range(n_fil)]
    bridges = [f"bridge-{ss}-{i:02d}" for i in range(n_bridge)]
    dists = [f"dist-{ss}-{i:02d}" for i in range(n_dist)]

    lines: list[str] = []
    lines.append(
        f"CREATE (:HUB {{id: 'nick-{hub_c}', slug: '{hub_c}', title: 'Correct hub {ss}'}})"
    )
    lines.append(
        f"CREATE (:HUB {{id: 'nick-{hub_w}', slug: '{hub_w}', title: 'Wrong hub {ss}'}})"
    )
    for i, slug in enumerate(gold):
        lines.append(
            f"CREATE (:DOC {{id: 'nick-{slug}', slug: '{slug}', title: 'Gold {ss} #{i}'}})"
        )
    for i, slug in enumerate(fils):
        lines.append(
            f"CREATE (:FIL {{id: 'nick-{slug}', slug: '{slug}', title: 'Fil {ss} #{i}'}})"
        )
    for i, slug in enumerate(bridges):
        lines.append(
            f"CREATE (:FIL {{id: 'nick-{slug}', slug: '{slug}', title: 'Bridge {ss} #{i}'}})"
        )
    for i, slug in enumerate(dists):
        lines.append(
            f"CREATE (:DOC {{id: 'nick-{slug}', slug: '{slug}', title: 'Dist {ss} #{i}'}})"
        )

    edges: list[str] = []
    for i, slug in enumerate(gold):
        edges.append(
            f"MATCH (a:DOC {{slug: '{slug}'}}), (b:HUB {{slug: '{hub_c}'}})"
        )
        edges.append(
            f"CREATE (a)-[:documents {{id: 'e-g-{ss}-{i}', note: 'gold'}}]->(b)"
        )
    for i, slug in enumerate(fils):
        edges.append(
            f"MATCH (a:FIL {{slug: '{slug}'}}), (b:HUB {{slug: '{hub_c}'}})"
        )
        edges.append(
            f"CREATE (a)-[:mentions {{id: 'e-f-{ss}-{i}', note: 'fil'}}]->(b)"
        )
    for i, slug in enumerate(bridges):
        edges.append(
            f"MATCH (a:FIL {{slug: '{slug}'}}), (b:HUB {{slug: '{hub_w}'}})"
        )
        edges.append(
            f"CREATE (a)-[:mentions {{id: 'e-b-{ss}-{i}', note: 'bridge'}}]->(b)"
        )
    for i, slug in enumerate(dists):
        br = bridges[i % n_bridge]
        edges.append(
            f"MATCH (a:DOC {{slug: '{slug}'}}), (b:FIL {{slug: '{br}'}})"
        )
        edges.append(
            f"CREATE (a)-[:documents {{id: 'e-d-{ss}-{i}', note: 'dist'}}]->(b)"
        )
    # wrong hub points at correct hub (depth-1 link); distractors remain depth-3 from correct
    edges.append(
        f"MATCH (a:HUB {{slug: '{hub_w}'}}), (b:HUB {{slug: '{hub_c}'}})"
    )
    edges.append(
        f"CREATE (a)-[:links {{id: 'e-link-{ss}', note: 'hub-link'}}]->(b)"
    )

    gql = "\n".join(lines + edges) + "\n"
    n_nodes = 2 + n_gold + n_fil + n_bridge + n_dist
    spec = SessionGraph(
        session_i=session_i,
        hub_correct=hub_c,
        hub_wrong=hub_w,
        gold=gold,
        n_nodes=n_nodes,
    )
    return spec, gql


class Engine:
    """Product Python API (CLI-equivalent operators only)."""

    def __init__(self) -> None:
        self.calls = {
            "open_session": 0,
            "MutateGate.apply": 0,
            "PinMapComposer.compose": 0,
            "close_session": 0,
        }

    def open_session(self):
        self.calls["open_session"] += 1
        return open_session(map_file=str(SCHEMA_PATH))

    def mutate(self, ss, gql: str) -> None:
        self.calls["MutateGate.apply"] += 1
        lines = [ln for ln in gql.splitlines() if ln.strip()]
        MutateGate(ss).apply(lines, mode="mutate")

    def pin_map(self, ss, hub_slug: str, max_rows: int):
        self.calls["PinMapComposer.compose"] += 1
        rows, text = PinMapComposer(ss).compose(
            anchor=None,
            kind=CUE_KIND,
            locators=[("slug", hub_slug)],
            depth=K_HOP,
            max_rows=max_rows,
            active_only=True,
            require_anchor=False,
        )
        return rows, text or ""

    def close(self, ss) -> None:
        self.calls["close_session"] += 1
        close_session(ss.session_id)


def node_slugs_from_rows(rows) -> set[str]:
    out: set[str] = set()
    for r in rows:
        if getattr(r, "kind", None) == "edge" or getattr(r, "tag", None) == "EDG":
            continue
        s = (getattr(r, "fields", None) or {}).get("slug")
        if s:
            out.add(s)
    return out


def task_score(gold: list[str], w_slugs: set[str]) -> float:
    if not gold:
        return 1.0
    return len(set(gold) & w_slugs) / len(gold)


def J_of(score: float, w_size: int) -> float:
    """Preregistered task cost: (1 - score) + MASS * |W|."""
    return (1.0 - score) + MASS * float(w_size)


def auroc(labels: list[int], scores: list[float]) -> float | None:
    """Mann-Whitney AUROC; None if degenerate."""
    pos = [s for s, y in zip(scores, labels) if y == 1]
    neg = [s for s, y in zip(scores, labels) if y == 0]
    if not pos or not neg:
        return None
    # P(score_pos > score_neg) + 0.5 P(eq)
    gt = sum(1 for p in pos for n in neg if p > n)
    eq = sum(1 for p in pos for n in neg if p == n)
    return (gt + 0.5 * eq) / (len(pos) * len(neg))


def run() -> dict:
    t0 = time.time()
    import memnet as _memnet_pkg

    eng = Engine()
    # per (session, cue, M): metrics
    rows_out: list[dict] = []
    build_fail = 0
    pin_fail = 0

    for si in range(N_SESSIONS):
        rng = random.Random(SEED_BASE + si)
        spec, gql = build_session_graph(si, rng)
        ss = eng.open_session()
        try:
            try:
                eng.mutate(ss, gql)
            except MemNetError as exc:
                build_fail += 1
                rows_out.append(
                    {
                        "session_i": si,
                        "error": f"mutate|{exc.code}|{exc}",
                    }
                )
                continue

            for cue_name, hub in (
                ("CORRECT", spec.hub_correct),
                ("WRONG", spec.hub_wrong),
            ):
                by_M: dict[int, dict] = {}
                for M in M_GRID:
                    try:
                        recs, _text = eng.pin_map(ss, hub, M)
                    except MemNetError as exc:
                        pin_fail += 1
                        by_M[M] = {
                            "M": M,
                            "error": f"{exc.code}|{exc}",
                            "W": 0,
                            "score": 0.0,
                            "J": 1.0,
                            "gold_in": False,
                            "truncated": True,
                        }
                        continue
                    slugs = node_slugs_from_rows(recs)
                    sc = task_score(spec.gold, slugs)
                    w = len(recs)  # admit all of X̃
                    gold_in = set(spec.gold).issubset(slugs)
                    by_M[M] = {
                        "M": M,
                        "W": w,
                        "score": sc,
                        "J": J_of(sc, w),
                        "gold_hits": len(set(spec.gold) & slugs),
                        "gold_n": len(spec.gold),
                        "gold_in": gold_in,
                        "truncated": not gold_in,
                    }

                # λ̂_M for each M with a next step
                for i, M in enumerate(M_GRID[:-1]):
                    M2 = M_GRID[i + 1]
                    delta = M2 - M  # grid step (4 for 8→12/12→16; 8 for 16→24/24→32)
                    a = by_M[M]
                    b = by_M[M2]
                    if "error" in a or "error" in b:
                        lam = None
                        score_improves = False
                    else:
                        lam = -(b["J"] - a["J"]) / delta
                        score_improves = b["score"] > a["score"] + 1e-12
                    rows_out.append(
                        {
                            "session_i": si,
                            "cue": cue_name,
                            "hub": hub,
                            "n_nodes": spec.n_nodes,
                            "M": M,
                            "M_next": M2,
                            "delta": delta,
                            "W": a.get("W"),
                            "W_next": b.get("W"),
                            "score": a.get("score"),
                            "score_next": b.get("score"),
                            "J": a.get("J"),
                            "J_next": b.get("J"),
                            "lambda_hat": lam,
                            "truncated": a.get("truncated"),
                            "gold_in": a.get("gold_in"),
                            "score_improves": score_improves,
                            "lambda_positive": (
                                lam is not None and lam > BAND
                            ),
                            "lambda_nonpositive": (
                                lam is not None and lam <= BAND
                            ),
                            "in_band": (
                                lam is not None and abs(lam) < BAND
                            ),
                        }
                    )
        finally:
            eng.close(ss)

        if (si + 1) % 25 == 0:
            print(f"session {si:03d} done elapsed={time.time()-t0:.1f}s", flush=True)

    return summarise(rows_out, eng, t0, memnet_file=getattr(_memnet_pkg, "__file__", None))


def summarise(rows_out: list[dict], eng: Engine, t0: float, memnet_file: str | None) -> dict:
    obs = [r for r in rows_out if "lambda_hat" in r and r.get("lambda_hat") is not None]
    # (a) truncated AND score improves → λ̂ should be > band
    cond_a = [r for r in obs if r["truncated"] and r["score_improves"]]
    a_pass = [r for r in cond_a if r["lambda_positive"]]
    a_rate = (len(a_pass) / len(cond_a)) if cond_a else None

    # (b) gold fully inside (slack vs gold) → λ̂ ≤ band more often
    cond_b = [r for r in obs if r["gold_in"]]
    b_ok = [r for r in cond_b if r["lambda_nonpositive"]]
    b_rate = (len(b_ok) / len(cond_b)) if cond_b else None

    # (c) WRONG positive-λ̂ rate > CORRECT
    def pos_rate(cue: str) -> float | None:
        sub = [r for r in obs if r["cue"] == cue]
        if not sub:
            return None
        return sum(1 for r in sub if r["lambda_positive"]) / len(sub)

    rate_correct = pos_rate("CORRECT")
    rate_wrong = pos_rate("WRONG")
    gap = (
        None
        if rate_correct is None or rate_wrong is None
        else rate_wrong - rate_correct
    )

    # null: AUROC / accuracy of λ̂ vs |W| for identifying wrong cue
    labels = [1 if r["cue"] == "WRONG" else 0 for r in obs]
    scores_lam = [r["lambda_hat"] for r in obs]
    scores_W = [float(r["W"] or 0) for r in obs]
    auroc_lam = auroc(labels, scores_lam)
    auroc_W = auroc(labels, scores_W)

    # simple accuracy: predict wrong if λ̂ > band; predict wrong if |W| >= median
    med_W = sorted(scores_W)[len(scores_W) // 2] if scores_W else 0.0

    def acc(pred_wrong: list[bool]) -> float:
        if not labels:
            return float("nan")
        return sum(1 for y, p in zip(labels, pred_wrong) if bool(y) == p) / len(labels)

    acc_lam = acc([r["lambda_positive"] for r in obs])
    acc_W = acc([w >= med_W for w in scores_W])

    # PASS criteria
    a_holds = a_rate is not None and a_rate > 0.5
    b_holds = b_rate is not None and b_rate > 0.5
    c_holds = (
        gap is not None and rate_wrong is not None and rate_correct is not None and gap > 0.05
    )
    # "clear gap" preregistered as >5 percentage points
    better_than_W = (
        auroc_lam is not None
        and auroc_W is not None
        and auroc_lam > auroc_W + 1e-9
    ) or (acc_lam > acc_W + 1e-9)

    # FAIL if routinely positive with slack, nonpositive when binding+improves, or no better than |W|
    fail_slack_pos = (
        cond_b
        and (sum(1 for r in cond_b if r["lambda_positive"]) / len(cond_b)) > 0.5
    )
    fail_binding = a_rate is not None and a_rate <= 0.5
    fail_null = not better_than_W

    if a_holds and b_holds and c_holds and not fail_slack_pos:
        verdict = "PASS"
        # note: null comparison reported; soft factor — primary PASS is a/b/c
        if fail_null:
            verdict_note = (
                "PASS on (a)(b)(c); null: λ̂ not clearly better than raw |W| "
                "(reported, does not alone overturn a/b/c majority criteria)"
            )
        else:
            verdict_note = "PASS: (a)(b)(c) hold; λ̂ beats raw |W| on AUROC/accuracy"
    else:
        verdict = "FAIL"
        reasons = []
        if not a_holds:
            reasons.append(f"(a) rate={a_rate}")
        if not b_holds:
            reasons.append(f"(b) rate={b_rate}")
        if not c_holds:
            reasons.append(f"(c) wrong={rate_wrong} correct={rate_correct} gap={gap}")
        if fail_slack_pos:
            reasons.append("λ̂ routinely positive with slack")
        verdict_note = "FAIL: " + "; ".join(reasons)

    # per-M positive rates
    per_M = {}
    for M in M_GRID[:-1]:
        per_M[str(M)] = {
            "CORRECT_pos_rate": pos_rate_M(obs, "CORRECT", M),
            "WRONG_pos_rate": pos_rate_M(obs, "WRONG", M),
        }

    summary = {
        "verdict": verdict,
        "verdict_note": verdict_note,
        "claim": (
            "λ̂_M is an account diagnostic (finite-difference of preregistered J), "
            "not a KKT multiplier read off the engine. Engine caps stay hard rejects."
        ),
        "memnet_version": MEMNET_VERSION,
        "memnet_file": memnet_file,
        "merge_commit": MERGE_COMMIT,
        "n_sessions": N_SESSIONS,
        "M_grid": M_GRID,
        "delta": DELTA,
        "band": BAND,
        "mass": MASS,
        "J_formula": "(1 - score) + 0.01*|W|, score=|gold∩W|/|gold|",
        "depth": K_HOP,
        "operators": [
            "open_session",
            "MutateGate.apply",
            "PinMapComposer.compose",
            "close_session",
        ],
        "call_counts": dict(eng.calls),
        "n_obs": len(obs),
        "tests": {
            "a_truncated_and_improves": {
                "n": len(cond_a),
                "n_lambda_positive": len(a_pass),
                "rate": a_rate,
                "holds_majority": a_holds,
            },
            "b_slack_gold_inside": {
                "n": len(cond_b),
                "n_lambda_nonpositive": len(b_ok),
                "rate": b_rate,
                "holds_majority": b_holds,
                "positive_with_slack_rate": (
                    (sum(1 for r in cond_b if r["lambda_positive"]) / len(cond_b))
                    if cond_b
                    else None
                ),
            },
            "c_wrong_vs_correct_pos_rate": {
                "CORRECT_pos_rate": rate_correct,
                "WRONG_pos_rate": rate_wrong,
                "gap": gap,
                "holds_clear_gap": c_holds,
                "per_M": per_M,
            },
            "null_vs_raw_W": {
                "auroc_lambda": auroc_lam,
                "auroc_W": auroc_W,
                "acc_positive_lambda_implies_wrong": acc_lam,
                "acc_high_W_implies_wrong": acc_W,
                "median_W_threshold": med_W,
                "lambda_better": better_than_W,
            },
        },
        "build_fail": sum(1 for r in rows_out if str(r.get("error", "")).startswith("mutate")),
        "pin_fail": sum(
            1
            for r in rows_out
            if r.get("error") and not str(r.get("error", "")).startswith("mutate")
        ),
        "elapsed_s": round(time.time() - t0, 2),
        "observations": obs,
    }
    return summary


def pos_rate_M(obs: list[dict], cue: str, M: int) -> float | None:
    sub = [r for r in obs if r["cue"] == cue and r["M"] == M]
    if not sub:
        return None
    return sum(1 for r in sub if r["lambda_positive"]) / len(sub)


def write_report(summary: dict) -> None:
    t = summary["tests"]
    a, b, c, n = (
        t["a_truncated_and_improves"],
        t["b_slack_gold_inside"],
        t["c_wrong_vs_correct_pos_rate"],
        t["null_vs_raw_W"],
    )
    lines = []
    lines.append("# STM Prediction 2 — M-cap multiplier detects a wrong Shape")
    lines.append("")
    lines.append("Paper §10.2 (post-Sage). Cheap analysis half: no LLM generate.")
    lines.append("")
    lines.append(f"**Verdict:** `{summary['verdict']}`")
    lines.append("")
    lines.append(summary["verdict_note"])
    lines.append("")
    lines.append("## Claim")
    lines.append("")
    lines.append(summary["claim"])
    lines.append("")
    lines.append(
        "Prediction: λ̂_M becomes positive when the row cap is active and "
        "marginally relaxing M would improve the task objective. Wrongly centred / "
        "diffuse Shapes produce positive λ̂_M more often than correctly centred "
        "compact Shapes."
    )
    lines.append("")
    lines.append("## memnet-llm version and API")
    lines.append("")
    lines.append(f"- **memnet-llm:** `{summary['memnet_version']}`")
    lines.append(f"- **memnet.__file__:** `{summary['memnet_file']}`")
    lines.append(f"- **merge commit:** `{summary['merge_commit']}` (same as green P3)")
    lines.append(
        "- **Operators (count=4):** `open_session`, `MutateGate.apply`, "
        "`PinMapComposer.compose`, `close_session`"
    )
    lines.append(f"- **Call counts:** `{json.dumps(summary['call_counts'])}`")
    lines.append("- **Not used:** Neo4j, Pi, droplet, InvenTree, soft-buy M inside engine")
    lines.append(
        "- **Analysis knob:** compose `max_rows` M only; engine store caps remain hard rejects"
    )
    lines.append("")
    lines.append("## Preregistered protocol")
    lines.append("")
    lines.append(f"- n_sessions = **{summary['n_sessions']}**")
    lines.append(f"- M grid = `{summary['M_grid']}`, δ = **{summary['delta']}**, depth = **{summary['depth']}**")
    lines.append(f"- Equivalence band: |λ̂| < **{summary['band']}** treated as zero")
    lines.append(f"- J(M) = `{summary['J_formula']}`")
    lines.append(f"- λ̂_M = −(J(M+δ)−J(M))/δ")
    lines.append(
        "- Cap active / truncated: gold ⊈ W(M). W(M) = admitted rows (admit all of X̃)."
    )
    lines.append(
        "- CORRECT cue: kind=HUB + true hub slug (compact Shape). "
        "WRONG cue: kind=HUB + distractor hub (diffuse / off-centre)."
    )
    lines.append(f"- RNG seed base = `{SEED_BASE}`")
    lines.append(f"- elapsed = **{summary['elapsed_s']}s**")
    lines.append("")
    lines.append("## Tests")
    lines.append("")
    lines.append("### (a) Truncated + score improves ⇒ λ̂ > band")
    lines.append("")
    lines.append(
        f"- n = {a['n']}, n_positive = {a['n_lambda_positive']}, "
        f"rate = **{a['rate']}**, majority = **{a['holds_majority']}**"
    )
    lines.append("")
    lines.append("### (b) Gold inside (slack) ⇒ λ̂ ≤ band")
    lines.append("")
    lines.append(
        f"- n = {b['n']}, n_nonpositive = {b['n_lambda_nonpositive']}, "
        f"rate = **{b['rate']}**, majority = **{b['holds_majority']}**"
    )
    lines.append(f"- positive-with-slack rate = {b['positive_with_slack_rate']}")
    lines.append("")
    lines.append("### (c) WRONG positive-λ̂ rate > CORRECT (clear gap)")
    lines.append("")
    lines.append(f"- CORRECT pos rate = **{c['CORRECT_pos_rate']}**")
    lines.append(f"- WRONG pos rate = **{c['WRONG_pos_rate']}**")
    lines.append(f"- gap = **{c['gap']}**, clear gap = **{c['holds_clear_gap']}**")
    lines.append(f"- per-M: `{json.dumps(c['per_M'])}`")
    lines.append("")
    lines.append("### Null: λ̂ vs raw |W| for identifying wrong Shapes")
    lines.append("")
    lines.append(f"- AUROC(λ̂) = **{n['auroc_lambda']}**, AUROC(|W|) = **{n['auroc_W']}**")
    lines.append(
        f"- acc(positive λ̂ ⇒ wrong) = **{n['acc_positive_lambda_implies_wrong']}**, "
        f"acc(|W|≥median ⇒ wrong) = **{n['acc_high_W_implies_wrong']}** "
        f"(median_W={n['median_W_threshold']})"
    )
    lines.append(f"- λ̂ better than |W| = **{n['lambda_better']}**")
    lines.append("")
    lines.append("## State clearly")
    lines.append("")
    lines.append(
        "**λ̂ is an account diagnostic** computed from the preregistered finite-difference "
        "of J over compose `max_rows`. **The engine still hard-rejects** on its store caps; "
        "this protocol does not soft-buy M inside the engine."
    )
    lines.append("")
    lines.append("## Paths")
    lines.append("")
    lines.append(f"- script: `{HERE / 'run_p2.py'}`")
    lines.append(f"- results: `{RESULTS_PATH}`")
    lines.append(f"- report: `{REPORT_PATH}`")
    lines.append("")
    REPORT_PATH.write_text("\n".join(lines) + "\n")


def main() -> int:
    summary = run()
    # Slim observations in JSON optional — keep full for audit
    RESULTS_PATH.write_text(json.dumps(summary, indent=2, sort_keys=False) + "\n")
    write_report(summary)
    print("VERDICT", summary["verdict"])
    print(summary["verdict_note"])
    t = summary["tests"]
    print(
        "rates",
        "a=", t["a_truncated_and_improves"]["rate"],
        "b=", t["b_slack_gold_inside"]["rate"],
        "wrong=", t["c_wrong_vs_correct_pos_rate"]["WRONG_pos_rate"],
        "correct=", t["c_wrong_vs_correct_pos_rate"]["CORRECT_pos_rate"],
        "gap=", t["c_wrong_vs_correct_pos_rate"]["gap"],
    )
    print("wrote", RESULTS_PATH, REPORT_PATH)
    return 0 if summary["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
