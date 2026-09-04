#!/usr/bin/env python3
"""STM Prediction 1 — bounded ShapeWalk vs RAG-style dump (action at equal quality).

Paper §10.1 (post-Sage). Synthetic-stratum pilot (not human-reviewed 200).

Operators only: open_session, MutateGate.apply, PinMapComposer.compose, close_session.
Dump condition is a bench fixture (serialise observables → admit large ranked list into
synthetic W). Not a MemNet product verb; no rag_query.
"""

from __future__ import annotations

import json
import os
import random
import statistics
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

os.environ.setdefault("MEMNET_TEST_INLINE", "1")
os.environ.setdefault("MEMNET_SERVE_INTERNAL", "1")
os.environ.pop("MEMNET_NEO4J_URL", None)
os.environ.pop("MEMNET_AGENSGRAPH_URL", None)

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

# --- Preregistered protocol constants (FIXED before seeing outcomes) ---
K_HOP = 2
M_HARD = 12  # hard max_rows for ShapeWalk; do NOT raise
CUE_KIND = "HUB"
SEED_BASE = 20260904

# Action estimator coefficients — LOCKED before run (write in REPORT first).
COEF_A = 1.0  # a: transition distance weight
COEF_B = 1.0  # b: tokens_admitted weight
COEF_C = 0.0  # c: critical_evictions (none in single-turn)
COEF_D = 10.0  # d: task loss weight
# d(empty, W) := |W|  (cardinality of admitted set from empty)
# tokens_admitted := sum(len(title)+len(slug)) over admitted nodes
# ℓ_task := 1 - score

N_CORE_DOC = 5
N_CORE_TSK = 2
N_CORE_USR = 2
N_NOISE = 24  # outside k=2 ball → dump-heavy, walk-invisible
# node count = 1 HUB + 5 DOC + 2 TSK + 2 USR + 1 BRIDGE + 24 NOISE = 35 ≥ 16

DEFAULT_N = 500
FALLBACK_N = 200
WALL_BUDGET_S = 30 * 60
BOOTSTRAP_B = 10_000
BOOTSTRAP_SEED = 42


@dataclass
class NodeSpec:
    kind: str
    slug: str
    title: str
    nick: str


@dataclass
class EdgeSpec:
    src_slug: str
    dst_slug: str
    rel: str
    note: str
    nick: str


@dataclass
class GraphSpec:
    session_i: int
    hub_slug: str
    nodes: list[NodeSpec]
    edges: list[EdgeSpec]
    gold_slugs: list[str]  # minimal gold evidence (observables, within k≤2)


def build_graph(session_i: int) -> GraphSpec:
    """Session with gold evidence inside k≤2 of HUB; bulk NOISE at hop≥3."""
    ss = f"s{session_i:04d}"
    hub_slug = f"hub-{ss}"
    nodes: list[NodeSpec] = [
        NodeSpec("HUB", hub_slug, f"Hub {ss} root", f"nick-{hub_slug}"),
    ]
    edges: list[EdgeSpec] = []
    docs: list[str] = []
    for i in range(N_CORE_DOC):
        slug = f"doc-{ss}-n{i:02d}"
        docs.append(slug)
        nodes.append(NodeSpec("DOC", slug, f"Document {ss} #{i}", f"nick-{slug}"))
        edges.append(
            EdgeSpec(slug, hub_slug, "documents", f"doc-{i}", f"nick-e-doc-{ss}-{i:02d}")
        )
    # DOC ring (keeps docs mutual 2-hop via hub already)
    for i in range(N_CORE_DOC):
        a, b = docs[i], docs[(i + 1) % N_CORE_DOC]
        edges.append(
            EdgeSpec(a, b, "next", f"ring-{i}", f"nick-e-ring-{ss}-{i:02d}")
        )
    tsks: list[str] = []
    for i in range(N_CORE_TSK):
        slug = f"tsk-{ss}-n{i:02d}"
        tsks.append(slug)
        nodes.append(NodeSpec("TSK", slug, f"Task {ss} #{i}", f"nick-{slug}"))
        edges.append(
            EdgeSpec(slug, hub_slug, "mentions", f"tsk-{i}", f"nick-e-tsk-{ss}-{i:02d}")
        )
    for i in range(N_CORE_USR):
        slug = f"usr-{ss}-n{i:02d}"
        nodes.append(NodeSpec("USR", slug, f"User {ss} #{i}", f"nick-{slug}"))
        edges.append(
            EdgeSpec(slug, docs[i % N_CORE_DOC], "owns", f"own-{i}", f"nick-e-own-{ss}-{i:02d}")
        )
    # Bridge at hop 2 (via last DOC), then NOISE at hop ≥3 — dump-only bulk.
    bridge_slug = f"bridge-{ss}"
    nodes.append(
        NodeSpec("BRIDGE", bridge_slug, f"Bridge {ss}", f"nick-{bridge_slug}")
    )
    edges.append(
        EdgeSpec(
            docs[-1],
            bridge_slug,
            "next",
            "to-bridge",
            f"nick-e-bridge-{ss}",
        )
    )
    for i in range(N_NOISE):
        slug = f"noise-{ss}-n{i:02d}"
        nodes.append(NodeSpec("NOISE", slug, f"Noise blob {ss} #{i}", f"nick-{slug}"))
        edges.append(
            EdgeSpec(
                bridge_slug,
                slug,
                "links",
                f"noise-{i}",
                f"nick-e-noise-{ss}-{i:02d}",
            )
        )
    # Minimal gold: HUB + first 3 DOCs + first TSK (all ≤1 hop of HUB).
    gold = [hub_slug, docs[0], docs[1], docs[2], tsks[0]]
    assert len(nodes) >= 16
    return GraphSpec(
        session_i=session_i,
        hub_slug=hub_slug,
        nodes=nodes,
        edges=edges,
        gold_slugs=gold,
    )


def gql_for(spec: GraphSpec) -> str:
    lines: list[str] = []
    for n in spec.nodes:
        lines.append(
            "CREATE (:{kind} {{id: '{nick}', slug: '{slug}', title: '{title}'}})".format(
                kind=n.kind, nick=n.nick, slug=n.slug, title=n.title
            )
        )
    by_slug = {n.slug: n for n in spec.nodes}
    for e in spec.edges:
        sk = by_slug[e.src_slug].kind
        dk = by_slug[e.dst_slug].kind
        lines.append(
            f"MATCH (a:{sk} {{slug: '{e.src_slug}'}}), "
            f"(b:{dk} {{slug: '{e.dst_slug}'}})"
        )
        lines.append(
            f"CREATE (a)-[:{e.rel} {{id: '{e.nick}', note: '{e.note}'}}]->(b)"
        )
    return "\n".join(lines) + "\n"


def node_tokens(title: str, slug: str) -> int:
    return len(title) + len(slug)


def action_estimate(*, w_size: int, tokens: int, score: float) -> float:
    """Â_d single-turn from empty. Coefficients locked above.
    d(empty,W)=|W|; term is a * d^2 as in the preregistered estimator.
    """
    d_trans = float(w_size)  # d(empty, W) = |W|
    crit_evict = 0.0
    ell = 1.0 - float(score)
    return (
        COEF_A * (d_trans ** 2)
        + COEF_B * float(tokens)
        + COEF_C * crit_evict
        + COEF_D * ell
    )


@dataclass
class LoadResult:
    condition: str
    score: float
    w_slugs: list[str]
    w_size: int
    tokens: int
    action: float
    n_offered_rows: int
    n_session_nodes: int


class Engine:
    def __init__(self) -> None:
        self.calls = {
            "open_session": 0,
            "MutateGate.apply": 0,
            "PinMapComposer.compose": 0,
            "close_session": 0,
        }

    def open(self):
        self.calls["open_session"] += 1
        return open_session(map_file=str(SCHEMA_PATH), ttl_minutes=60)

    def mutate(self, ss, gql: str) -> None:
        self.calls["MutateGate.apply"] += 1
        lines = [ln for ln in gql.splitlines() if ln.strip()]
        MutateGate(ss).apply(lines, mode="mutate")

    def pin_map(self, ss, hub_slug: str):
        self.calls["PinMapComposer.compose"] += 1
        rows, text = PinMapComposer(ss).compose(
            anchor=None,
            kind=CUE_KIND,
            locators=[("slug", hub_slug)],
            depth=K_HOP,
            max_rows=M_HARD,
            active_only=True,
            require_anchor=False,
        )
        return rows, text or ""

    def close(self, ss) -> None:
        self.calls["close_session"] += 1
        close_session(ss.session_id)


def observable_nodes(ss) -> list:
    """Bench-fixture serialisation of session observables (not a product dump)."""
    return [r for r in ss.store.list_records(active_only=True) if r.tag != "EDG"]


def admitted_from_rows(rows) -> list[tuple[str, str, str]]:
    """Return list of (slug, title, kind) for node rows; skip edges/laws."""
    out = []
    for r in rows:
        if r.tag == "EDG" or getattr(r, "kind", None) == "edge":
            continue
        if r.tag == "LAW":
            continue
        slug = str(r.fields.get("slug", ""))
        title = str(r.fields.get("title", ""))
        if not slug:
            continue
        out.append((slug, title, r.tag))
    return out


def score_vs_gold(admitted_slugs: set[str], gold: list[str]) -> float:
    if not gold:
        return 1.0
    hit = sum(1 for g in gold if g in admitted_slugs)
    return hit / len(gold)


def run_pair(eng: Engine, spec: GraphSpec) -> dict:
    """One session: ShapeWalk (A) and Dump (B) at equal-quality comparison setup."""
    ss = eng.open()
    sid = ss.session_id
    try:
        eng.mutate(ss, gql_for(spec))
        # --- Condition A: ShapeWalk ---
        rows_a, _text_a = eng.pin_map(ss, spec.hub_slug)
        # Caller admits ALL of offered X̃ for this synthetic case (documented).
        adm_a = admitted_from_rows(rows_a)
        slugs_a = [s for s, _, _ in adm_a]
        tok_a = sum(node_tokens(t, s) for s, t, _ in adm_a)
        score_a = score_vs_gold(set(slugs_a), spec.gold_slugs)
        act_a = action_estimate(w_size=len(slugs_a), tokens=tok_a, score=score_a)

        # --- Condition B: Dump fixture (NOT a MemNet operator) ---
        # Serialise ALL observable nodes in the session snapshot; admit full list.
        # Cap is NOT applied — dump is allowed to be heavier.
        all_nodes = observable_nodes(ss)
        adm_b = []
        for r in all_nodes:
            slug = str(r.fields.get("slug", ""))
            title = str(r.fields.get("title", ""))
            if slug:
                adm_b.append((slug, title, r.tag))
        slugs_b = [s for s, _, _ in adm_b]
        tok_b = sum(node_tokens(t, s) for s, t, _ in adm_b)
        score_b = score_vs_gold(set(slugs_b), spec.gold_slugs)
        act_b = action_estimate(w_size=len(slugs_b), tokens=tok_b, score=score_b)

        return {
            "session_i": spec.session_i,
            "session_id": sid,
            "hub_slug": spec.hub_slug,
            "gold_slugs": list(spec.gold_slugs),
            "n_session_nodes": len(spec.nodes),
            "n_gold": len(spec.gold_slugs),
            "walk": {
                "score": score_a,
                "w_size": len(slugs_a),
                "tokens": tok_a,
                "action": act_a,
                "n_offered_rows": len(rows_a),
                "w_slugs": slugs_a,
            },
            "dump": {
                "score": score_b,
                "w_size": len(slugs_b),
                "tokens": tok_b,
                "action": act_b,
                "n_offered_rows": len(slugs_b),
                "w_slugs": slugs_b,
            },
            "delta_action": act_b - act_a,  # Â_dump − Â_walk
            "both_perfect": score_a == 1.0 and score_b == 1.0,
            "ok": True,
            "error": None,
        }
    except MemNetError as exc:
        return {
            "session_i": spec.session_i,
            "session_id": sid,
            "ok": False,
            "error": f"{exc.code}|{exc}",
            "both_perfect": False,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "session_i": spec.session_i,
            "session_id": sid,
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "both_perfect": False,
        }
    finally:
        try:
            eng.close(ss)
        except Exception:
            pass


def bootstrap_ci(deltas: list[float], n_boot: int = BOOTSTRAP_B, seed: int = BOOTSTRAP_SEED):
    if not deltas:
        return {"mean": None, "median": None, "ci95": [None, None], "n": 0}
    rng = random.Random(seed)
    n = len(deltas)
    means = []
    for _ in range(n_boot):
        sample = [deltas[rng.randrange(n)] for _ in range(n)]
        means.append(statistics.fmean(sample))
    means.sort()
    lo = means[int(0.025 * n_boot)]
    hi = means[int(0.975 * n_boot)]
    # percentile via index; clamp
    lo = means[max(0, int(0.025 * n_boot))]
    hi = means[min(n_boot - 1, int(0.975 * n_boot))]
    return {
        "mean": statistics.fmean(deltas),
        "median": statistics.median(deltas),
        "ci95": [lo, hi],
        "n": n,
        "n_bootstrap": n_boot,
    }


def write_report(payload: dict) -> None:
    coef = payload["coefficient_lock"]
    stats_bp = payload["stats_both_perfect"]
    stats_full = payload["stats_full"]
    verdict = payload["verdict"]
    lines = []
    lines.append("# STM Prediction 1 — bounded ShapeWalk vs dump (action at equal quality)")
    lines.append("")
    lines.append("Paper §10.1 (post-Sage). **Synthetic-stratum pilot — not human-reviewed 200.**")
    lines.append("")
    lines.append(f"**Verdict:** `{verdict}`")
    lines.append("")
    lines.append("## Coefficient lock (FIXED before run)")
    lines.append("")
    lines.append("Action estimator (single-turn load, W₀=∅, W₁=admitted set):")
    lines.append("")
    lines.append("```")
    lines.append("Â_d = a·d(W₀,W₁)² + b·tokens_admitted + c·critical_evictions + d·ℓ_task")
    lines.append("# Practical single-turn form used:")
    lines.append("Â   = a·|W|² + b·tokens + c·0 + d·(1 − score)")
    lines.append(f"a = {coef['a']}")
    lines.append(f"b = {coef['b']}")
    lines.append(f"c = {coef['c']}  # no eviction in single-turn")
    lines.append(f"d = {coef['d']}")
    lines.append("d(empty, W) := |W|   (cardinality of admitted)")
    lines.append("tokens_admitted := Σ (len(title)+len(slug)) over admitted nodes")
    lines.append("ℓ_task := 1 − score")
    lines.append("score := |gold ∩ W| / |gold|")
    lines.append("```")
    lines.append("")
    lines.append("Coefficients were locked before any outcome was inspected. FAIL if dump ≤ walk")
    lines.append("on the both-perfect stratum, or if the result appears only after retuning.")
    lines.append("")
    lines.append("## Claim")
    lines.append("")
    lines.append("For tasks whose required evidence lies within a bounded k-hop session")
    lines.append("neighbourhood, bounded ShapeWalk achieves equal task performance at lower")
    lines.append("measured action than a RAG-style dump of the available session material.")
    lines.append("Compare at **equal task quality**. Do NOT require matched final evidence coverage.")
    lines.append("")
    lines.append("## MemNet / operators")
    lines.append("")
    lines.append(f"- **memnet-llm:** `{payload['memnet_version']}`")
    lines.append(f"- **memnet.__file__:** `{payload['memnet_file']}`")
    lines.append(f"- **merge commit:** `{payload['memnet_commit']}`")
    lines.append("- **Operators only:** `open_session`, `MutateGate.apply`, `PinMapComposer.compose`, `close_session`")
    lines.append("- **Not used:** `rag_query`, leftover `add`, `Layer`, Neo4j / Pi / droplet / InvenTree")
    lines.append("- **Dump condition:** bench fixture — serialise observable session nodes and admit")
    lines.append("  the full ranked list into synthetic W_B. Analysis of a load operator, **not** product soft-M.")
    lines.append(f"- **Call counts:** `{json.dumps(payload['call_counts'])}`")
    lines.append("")
    lines.append("## Protocol")
    lines.append("")
    lines.append(f"- n_sessions = **{payload['n_sessions']}**"
                 f" (target 500 if wall <30 min; else 200 OK)")
    lines.append(f"- wall_time_s = **{payload['wall_time_s']:.2f}**")
    lines.append(f"- scale_note: {payload['scale_note']}")
    lines.append(f"- k (depth) = **{K_HOP}**")
    lines.append(f"- M hard (ShapeWalk max_rows) = **{M_HARD}** — not raised")
    lines.append(f"- cue: kind=`{CUE_KIND}` + locator `slug=<hub-slug>`")
    lines.append(f"- nodes/session ≥16 (actual = {payload['nodes_per_session']})")
    lines.append("- gold: minimal evidence set within k≤2 of HUB (hub + 3 DOC + 1 TSK)")
    lines.append("- Condition A: ShapeWalk; **caller admits all of offered X̃** (synthetic)")
    lines.append("- Condition B: dump ALL observable nodes in session snapshot (no cap)")
    lines.append("- Equal quality stratum: both score == 1.0")
    lines.append(f"- RNG seed base = `{SEED_BASE}`; bootstrap seed = `{BOOTSTRAP_SEED}`")
    lines.append("")
    lines.append("## Results — both-perfect stratum (PRIMARY)")
    lines.append("")
    bp = stats_bp
    lines.append(f"- n both-perfect = **{bp['n']}**")
    lines.append(f"- mean Â walk = **{bp['mean_A_walk']}**")
    lines.append(f"- mean Â dump = **{bp['mean_A_dump']}**")
    lines.append(f"- mean Δ (Â_dump − Â_walk) = **{bp['mean']}**")
    lines.append(f"- median Δ = **{bp['median']}**")
    lines.append(f"- 95% bootstrap CI = **{bp['ci95']}**")
    lines.append("")
    lines.append("## Results — full set")
    lines.append("")
    fl = stats_full
    lines.append(f"- n_ok = **{fl['n']}**")
    lines.append(f"- mean score walk = **{fl['mean_score_walk']}**")
    lines.append(f"- mean score dump = **{fl['mean_score_dump']}**")
    lines.append(f"- mean Â walk = **{fl['mean_A_walk']}**")
    lines.append(f"- mean Â dump = **{fl['mean_A_dump']}**")
    lines.append(f"- mean Δ = **{fl['mean']}**")
    lines.append(f"- median Δ = **{fl['median']}**")
    lines.append(f"- 95% bootstrap CI = **{fl['ci95']}**")
    lines.append("")
    lines.append("## Pass/fail against the claim")
    lines.append("")
    lines.append(f"**{verdict}**")
    lines.append("")
    lines.append(payload["verdict_reason"])
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- This is a **synthetic-stratum pilot**, not the human-reviewed 200 from the full protocol.")
    lines.append("- No LLM generate; task quality is gold-evidence coverage of admitted W.")
    lines.append("- Primary comparison is on pairs where both score==1 (equal quality).")
    lines.append("")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    t0 = time.time()
    import memnet as _memnet_pkg

    memnet_file = getattr(_memnet_pkg, "__file__", None)
    print("=== STM Prediction 1 ===")
    print(f"coefficient lock: a={COEF_A} b={COEF_B} c={COEF_C} d={COEF_D}")
    print(f"memnet version={MEMNET_VERSION} file={memnet_file}")
    print(f"merge_commit={MERGE_COMMIT}")
    print(f"M_HARD={M_HARD} K_HOP={K_HOP}")

    # Decide N: try 500; if a pilot of 20 projects >30min, fall back to 200.
    target_n = int(os.environ.get("P1_N_SESSIONS", str(DEFAULT_N)))
    eng = Engine()

    # Timing pilot
    pilot_n = min(20, target_n)
    pilot_rows = []
    for i in range(pilot_n):
        pilot_rows.append(run_pair(eng, build_graph(i)))
    pilot_dt = time.time() - t0
    per = pilot_dt / max(1, pilot_n)
    projected_500 = per * DEFAULT_N
    if target_n >= DEFAULT_N and projected_500 > WALL_BUDGET_S:
        n_sessions = FALLBACK_N
        scale_note = (
            f"Projected {DEFAULT_N} @ {per:.3f}s/session ≈ {projected_500:.0f}s > 30min; "
            f"using n={FALLBACK_N}."
        )
    else:
        n_sessions = target_n
        scale_note = (
            f"Projected {n_sessions} @ {per:.3f}s/session ≈ {per * n_sessions:.0f}s; "
            f"keeping n={n_sessions}."
        )
    print(scale_note)

    results = list(pilot_rows)
    for i in range(pilot_n, n_sessions):
        results.append(run_pair(eng, build_graph(i)))
        if (i + 1) % 50 == 0:
            print(f"  … {i+1}/{n_sessions} sessions ({time.time()-t0:.1f}s)")

    ok_rows = [r for r in results if r.get("ok")]
    both = [r for r in ok_rows if r.get("both_perfect")]
    full_deltas = [r["delta_action"] for r in ok_rows]
    bp_deltas = [r["delta_action"] for r in both]

    def pack_stats(rows, deltas):
        if not rows:
            return {
                "n": 0,
                "mean": None,
                "median": None,
                "ci95": [None, None],
                "mean_A_walk": None,
                "mean_A_dump": None,
                "mean_score_walk": None,
                "mean_score_dump": None,
                "n_bootstrap": BOOTSTRAP_B,
            }
        ci = bootstrap_ci(deltas)
        return {
            **ci,
            "mean_A_walk": statistics.fmean(r["walk"]["action"] for r in rows),
            "mean_A_dump": statistics.fmean(r["dump"]["action"] for r in rows),
            "mean_score_walk": statistics.fmean(r["walk"]["score"] for r in rows),
            "mean_score_dump": statistics.fmean(r["dump"]["score"] for r in rows),
            "mean_w_walk": statistics.fmean(r["walk"]["w_size"] for r in rows),
            "mean_w_dump": statistics.fmean(r["dump"]["w_size"] for r in rows),
            "mean_tok_walk": statistics.fmean(r["walk"]["tokens"] for r in rows),
            "mean_tok_dump": statistics.fmean(r["dump"]["tokens"] for r in rows),
        }

    stats_bp = pack_stats(both, bp_deltas)
    stats_full = pack_stats(ok_rows, full_deltas)

    # PASS if mean Δ>0 and CI excludes 0 on both-perfect stratum
    verdict = "FAIL"
    reason = ""
    if stats_bp["n"] == 0:
        verdict = "FAIL"
        reason = "No pairs with both score==1.0; cannot compare at equal quality."
    else:
        mean_d = stats_bp["mean"]
        lo, hi = stats_bp["ci95"]
        if mean_d is not None and mean_d > 0 and lo is not None and lo > 0:
            verdict = "PASS"
            reason = (
                f"On both-perfect stratum (n={stats_bp['n']}), mean Δ={mean_d:.4f} > 0 "
                f"and 95% CI [{lo:.4f}, {hi:.4f}] excludes 0 — dump costs more action "
                f"at equal quality."
            )
        elif mean_d is not None and mean_d <= 0:
            verdict = "FAIL"
            reason = (
                f"mean Δ={mean_d:.4f} ≤ 0 on both-perfect stratum — dump did not cost "
                f"more action at equal quality."
            )
        else:
            verdict = "FAIL"
            reason = (
                f"mean Δ={mean_d}; CI={stats_bp['ci95']} — CI does not exclude 0 "
                f"(or mean Δ≤0)."
            )

    wall = time.time() - t0
    # sample one pair for results
    sample = both[0] if both else (ok_rows[0] if ok_rows else None)
    # shrink per-session for json: drop full slug lists except sample
    slim = []
    for r in results:
        if not r.get("ok"):
            slim.append(r)
            continue
        slim.append(
            {
                "session_i": r["session_i"],
                "hub_slug": r["hub_slug"],
                "n_session_nodes": r["n_session_nodes"],
                "n_gold": r["n_gold"],
                "walk": {
                    k: r["walk"][k]
                    for k in ("score", "w_size", "tokens", "action", "n_offered_rows")
                },
                "dump": {
                    k: r["dump"][k]
                    for k in ("score", "w_size", "tokens", "action", "n_offered_rows")
                },
                "delta_action": r["delta_action"],
                "both_perfect": r["both_perfect"],
                "ok": True,
            }
        )

    payload = {
        "prediction": 1,
        "claim": (
            "bounded ShapeWalk equal quality at lower action than RAG-style dump "
            "for k-hop-local evidence tasks"
        ),
        "memnet_version": MEMNET_VERSION,
        "memnet_file": memnet_file,
        "memnet_commit": MERGE_COMMIT,
        "coefficient_lock": {
            "a": COEF_A,
            "b": COEF_B,
            "c": COEF_C,
            "d": COEF_D,
            "d_empty_W": "|W|", "term_a": "a * |W|^2",
            "tokens": "sum(len(title)+len(slug))",
            "ell_task": "1-score",
            "locked_before_outcomes": True,
        },
        "protocol": {
            "k_hop": K_HOP,
            "M_hard": M_HARD,
            "cue_kind": CUE_KIND,
            "walk_admits_all_offered": True,
            "dump_is_bench_fixture": True,
            "dump_cap_applied": False,
            "equal_quality": "both score==1.0",
            "no_matched_coverage_requirement": True,
        },
        "n_sessions": n_sessions,
        "n_ok": len(ok_rows),
        "n_both_perfect": len(both),
        "n_build_fail": len(results) - len(ok_rows),
        "nodes_per_session": len(build_graph(0).nodes),
        "scale_note": scale_note,
        "wall_time_s": wall,
        "stats_both_perfect": stats_bp,
        "stats_full": stats_full,
        "verdict": verdict,
        "verdict_reason": reason,
        "call_counts": eng.calls,
        "sample_pair": (
            {
                "session_i": sample["session_i"],
                "gold_slugs": sample["gold_slugs"],
                "walk": sample["walk"],
                "dump": {
                    k: sample["dump"][k]
                    for k in ("score", "w_size", "tokens", "action", "n_offered_rows")
                },
                "delta_action": sample["delta_action"],
            }
            if sample
            else None
        ),
        "sessions": slim,
        "note": "synthetic-stratum pilot not human-reviewed 200",
    }

    RESULTS_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_report(payload)

    print(f"n_sessions={n_sessions} n_both_perfect={len(both)} n_ok={len(ok_rows)}")
    print(f"meanÂ_walk={stats_bp['mean_A_walk']} meanÂ_dump={stats_bp['mean_A_dump']}")
    print(f"Δ={stats_bp['mean']} CI={stats_bp['ci95']}")
    print(f"verdict={verdict}")
    print(f"wrote {RESULTS_PATH} and {REPORT_PATH} in {wall:.1f}s")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
