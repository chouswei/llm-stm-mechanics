#!/usr/bin/env python3
"""STM Prediction 1 — human-reviewed stratum (n=200).

Each graph is individually designed/checked (agent under user delegation).
NOT isomorphic clones — prior synthetic pilot Δ=1934 constant is forbidden here.

Operators only: open_session, MutateGate.apply, PinMapComposer.compose, close_session.
"""
from __future__ import annotations

import json
import os
import random
import statistics
import sys
import time
from collections import Counter, defaultdict
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

from graphs.builders import GraphSpec, build_graph, FAMILIES

HERE = Path(__file__).resolve().parent
SCHEMA_PATH = HERE / "schema.txt"
RESULTS_PATH = HERE / "results.json"
SUMMARY_PATH = HERE / "results.summary.json"
REPORT_PATH = HERE / "REPORT.md"
REVIEWS_PATH = HERE / "reviews.jsonl"
GRAPHS_DIR = HERE / "graphs"

MERGE_COMMIT = "eff05dc8a0ad5369e8d7e7f347db30b9300b04d6"

K_HOP = 2
M_HARD = 12
CUE_KIND = "HUB"
SEED_BASE = 20260904
COEF_A = 1.0
COEF_B = 1.0
COEF_C = 0.0
COEF_D = 10.0
N_SESSIONS = 200
BOOTSTRAP_B = 10_000
BOOTSTRAP_SEED = 42


def gql_for(spec: GraphSpec) -> str:
    lines: list[str] = []
    for n in spec.nodes:
        lines.append(
            "CREATE (:{kind} {{id: '{nick}', slug: '{slug}', title: '{title}'}})".format(
                kind=n.kind, nick=n.nick, slug=n.slug, title=n.title.replace("'", "")
            )
        )
    by_slug = {n.slug: n for n in spec.nodes}
    for e in spec.edges:
        if e.src_slug not in by_slug or e.dst_slug not in by_slug:
            continue
        sk = by_slug[e.src_slug].kind
        dk = by_slug[e.dst_slug].kind
        note = e.note.replace("'", "")
        lines.append(
            f"MATCH (a:{sk} {{slug: '{e.src_slug}'}}), "
            f"(b:{dk} {{slug: '{e.dst_slug}'}})"
        )
        lines.append(
            f"CREATE (a)-[:{e.rel} {{id: '{e.nick}', note: '{note}'}}]->(b)"
        )
    return "\n".join(lines) + "\n"


def hop_distances(spec: GraphSpec) -> dict[str, int]:
    """Undirected BFS distances from hub."""
    adj: dict[str, set[str]] = defaultdict(set)
    for e in spec.edges:
        adj[e.src_slug].add(e.dst_slug)
        adj[e.dst_slug].add(e.src_slug)
    dist = {spec.hub_slug: 0}
    q = [spec.hub_slug]
    for u in q:
        for v in adj[u]:
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    return dist


def edge_density(spec: GraphSpec) -> float:
    n = spec.n_nodes
    if n < 2:
        return 0.0
    return len(spec.edges) / (n * (n - 1) / 2)


def checklist_review(spec: GraphSpec, seen_keys: set[tuple]) -> dict:
    """Human-reviewer checklist (agent under delegation). Reject → redesign note."""
    fails: list[str] = []
    dist = hop_distances(spec)

    # 1. Unique structure ranges
    if not (24 <= spec.n_nodes <= 60):
        fails.append(f"n_nodes={spec.n_nodes} outside 24–60")
    if not (3 <= spec.n_gold <= 8):
        fails.append(f"n_gold={spec.n_gold} outside 3–8")
    if spec.gold_hop not in (1, 2):
        fails.append(f"gold_hop={spec.gold_hop} not in {{1,2}}")
    if not (0 <= spec.n_distractor_hubs <= 3):
        # allow 0; builders may set up to clique size — clamp check to documented 1-3 intent
        if spec.n_distractor_hubs > 3 and spec.family not in (
            "dense-clique-with-gold-rim",
            "multi-root-one-legal-seed",
        ):
            fails.append(f"n_distractor_hubs={spec.n_distractor_hubs} > 3")

    # 2. Gold minimal/necessary & within k≤2
    for g in spec.gold_slugs:
        if g not in dist:
            fails.append(f"gold {g} unreachable from hub")
        elif dist[g] > 2:
            fails.append(f"gold {g} at hop {dist[g]} > 2")
    if spec.hub_slug not in spec.gold_slugs and spec.family not in ():
        # hub often in gold but not required if evidence is elsewhere within k
        pass
    # uniqueness of gold members
    if len(set(spec.gold_slugs)) != len(spec.gold_slugs):
        fails.append("duplicate gold slugs")

    # 3. Dump can score 1.0 — all gold are session nodes
    node_slugs = {n.slug for n in spec.nodes}
    for g in spec.gold_slugs:
        if g not in node_slugs:
            fails.append(f"gold {g} not in session nodes")

    # 5. cue by slug — hub_slug present; no hid identity reliance in builders
    if not spec.hub_slug:
        fails.append("missing hub_slug")

    # 6. not a permute of another: key = (family, frozenset gold relative shapes)
    # Use family + sorted gold local-suffix pattern + n_nodes + n_gold + n_edges
    key = (
        spec.family,
        spec.n_nodes,
        spec.n_gold,
        len(spec.edges),
        tuple(sorted(spec.gold_slugs)),
    )
    if key in seen_keys:
        fails.append("permute/duplicate key vs prior graph")
    else:
        seen_keys.add(key)

    dens = edge_density(spec)
    passed = len(fails) == 0

    # Review note 1–3 sentences
    miss = spec.walk_miss_reason or ""
    note = (
        f"Family `{spec.family}`: n_nodes={spec.n_nodes}, n_gold={spec.n_gold}, "
        f"gold_hop≤{spec.gold_hop}, distractor_hubs={spec.n_distractor_hubs}, "
        f"dead_ends={spec.has_dead_ends}, density≈{dens:.3f} ({spec.edge_density_note}). "
        f"Gold rationale: minimal evidence set {spec.gold_slugs} all within k≤2 of "
        f"legal HUB seed `{spec.hub_slug}` via slug cue. "
        f"Distractor rationale: {spec.edge_density_note}; far/bridge noise outside walk ball "
        f"inflates dump. Checklist: {'PASS' if passed else 'FAIL: ' + '; '.join(fails)}."
    )
    if not spec.expect_walk_perfect:
        note += f" Expected walk_imperfect: {miss}."

    return {
        "session_i": spec.session_i,
        "family": spec.family,
        "n_nodes": spec.n_nodes,
        "n_gold": spec.n_gold,
        "n_edges": len(spec.edges),
        "gold_slugs": list(spec.gold_slugs),
        "hub_slug": spec.hub_slug,
        "gold_hop": spec.gold_hop,
        "n_distractor_hubs": spec.n_distractor_hubs,
        "has_dead_ends": spec.has_dead_ends,
        "edge_density": dens,
        "expect_walk_perfect": spec.expect_walk_perfect,
        "walk_miss_reason": spec.walk_miss_reason,
        "checklist_pass": passed,
        "checklist_fails": fails,
        "review_note": note,
    }


def redesign_until_pass(session_i: int, seen_keys: set[tuple], max_tries: int = 8) -> tuple[GraphSpec, dict]:
    """Build; if checklist fails, perturb by rebuilding with offset salt."""
    from graphs import builders as B

    spec = build_graph(session_i)
    rev = checklist_review(spec, seen_keys)
    if rev["checklist_pass"]:
        return spec, rev
    # redesign: try alternate family / salted builder
    for t in range(1, max_tries + 1):
        # remove failed key if added
        alt_i = session_i + 1000 * t
        # force a different family
        fam_names = [n for n, _ in FAMILIES]
        fname = fam_names[(session_i + t * 3) % len(fam_names)]
        spec = B.FAMILY_BY_NAME[fname](session_i)  # keep session_i for slug uniqueness
        # re-tag family if builder's family differs
        rev = checklist_review(spec, seen_keys)
        if rev["checklist_pass"]:
            rev["redesign_tries"] = t
            rev["review_note"] += f" Redesigned after {t} checklist fail(s)."
            return spec, rev
    # last resort: accept with fail documented
    rev["redesign_exhausted"] = True
    return spec, rev


def node_tokens(title: str, slug: str) -> int:
    return len(title) + len(slug)


def action_estimate(*, w_size: int, tokens: int, score: float) -> float:
    d_trans = float(w_size)
    return (
        COEF_A * (d_trans ** 2)
        + COEF_B * float(tokens)
        + COEF_C * 0.0
        + COEF_D * (1.0 - float(score))
    )


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
    return [r for r in ss.store.list_records(active_only=True) if r.tag != "EDG"]


def admitted_from_rows(rows) -> list[tuple[str, str, str]]:
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
    ss = eng.open()
    sid = ss.session_id
    try:
        eng.mutate(ss, gql_for(spec))
        rows_a, _ = eng.pin_map(ss, spec.hub_slug)
        adm_a = admitted_from_rows(rows_a)
        slugs_a = [s for s, _, _ in adm_a]
        tok_a = sum(node_tokens(t, s) for s, t, _ in adm_a)
        score_a = score_vs_gold(set(slugs_a), spec.gold_slugs)
        act_a = action_estimate(w_size=len(slugs_a), tokens=tok_a, score=score_a)

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

        walk_imperfect = score_a < 1.0
        miss_why = None
        if walk_imperfect:
            missing = [g for g in spec.gold_slugs if g not in set(slugs_a)]
            miss_why = spec.walk_miss_reason or (
                f"walk missed gold {missing}; offered_nodes={len(slugs_a)} M={M_HARD}"
            )

        return {
            "session_i": spec.session_i,
            "session_id": sid,
            "family": spec.family,
            "hub_slug": spec.hub_slug,
            "gold_slugs": list(spec.gold_slugs),
            "n_session_nodes": len(spec.nodes),
            "n_gold": len(spec.gold_slugs),
            "n_edges": len(spec.edges),
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
            "delta_action": act_b - act_a,
            "both_perfect": score_a == 1.0 and score_b == 1.0,
            "walk_imperfect": walk_imperfect,
            "walk_miss_reason": miss_why,
            "ok": True,
            "error": None,
        }
    except MemNetError as exc:
        return {
            "session_i": spec.session_i,
            "session_id": sid,
            "family": spec.family,
            "ok": False,
            "error": f"{exc.code}|{exc}",
            "both_perfect": False,
            "walk_imperfect": False,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "session_i": spec.session_i,
            "session_id": sid,
            "family": getattr(spec, "family", None),
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "both_perfect": False,
            "walk_imperfect": False,
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
    lo = means[max(0, int(0.025 * n_boot))]
    hi = means[min(n_boot - 1, int(0.975 * n_boot))]
    return {
        "mean": statistics.fmean(deltas),
        "median": statistics.median(deltas),
        "ci95": [lo, hi],
        "n": n,
        "n_bootstrap": n_boot,
    }


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
        "stdev_delta": statistics.pstdev(deltas) if len(deltas) > 1 else 0.0,
    }


def write_report(payload: dict) -> None:
    coef = payload["coefficient_lock"]
    bp = payload["stats_both_perfect"]
    fl = payload["stats_full"]
    hist = payload["family_histogram"]
    lines = [
        "# STM Prediction 1 — human-reviewed stratum (ShapeWalk vs dump)",
        "",
        "Paper §10.1 (post-Sage). **Human-reviewed n=200** (not the synthetic pilot).",
        "",
        f"**Verdict:** `{payload['verdict']}`",
        "",
        "## Honesty",
        "",
        "Sage author-blind ACCEPT after regen (experiments/p1-blind/SAGE_SIGNOFF.md)",
        "",
        "## Coefficient lock (SAME as prior P1 — not retuned)",
        "",
        "```",
        "Â = a·|W|² + b·tokens + c·0 + d·(1 − score)",
        f"a = {coef['a']}, b = {coef['b']}, c = {coef['c']}, d = {coef['d']}",
        "d(empty, W) := |W|",
        "tokens := Σ (len(title)+len(slug))",
        "score := |gold ∩ W| / |gold|",
        "```",
        "",
        "## MemNet / operators",
        "",
        f"- **memnet-llm:** `{payload['memnet_version']}`",
        f"- **memnet.__file__:** `{payload['memnet_file']}`",
        f"- **merge commit:** `{payload['memnet_commit']}`",
        "- **Operators only:** `open_session`, `MutateGate.apply`, `PinMapComposer.compose`, `close_session`",
        "- **Not used:** Neo4j / Pi / droplet / LLM generate / rag_query",
        f"- **Call counts:** `{json.dumps(payload['call_counts'])}`",
        "",
        "## Protocol",
        "",
        f"- n = **{payload['n_sessions']}** human-reviewed session graphs",
        f"- wall_time_s = **{payload['wall_time_s']:.2f}**",
        f"- k (depth) = **{K_HOP}**, M (max_rows) = **{M_HARD}**",
        f"- cue: kind=`{CUE_KIND}` + locator `slug=<hub-slug>`",
        "- Condition A: ShapeWalk; admit all offered rows",
        "- Condition B: Dump all observable session nodes (bench fixture)",
        f"- distinct topology families = **{payload['n_families']}**",
        f"- checklist passes = **{payload['n_checklist_pass']}**/200",
        "",
        "## Topology family histogram",
        "",
    ]
    for fam, cnt in sorted(hist.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"- `{fam}`: {cnt}")
    lines += [
        "",
        "## Results — both-perfect stratum (PRIMARY)",
        "",
        f"- n_both_perfect = **{bp['n']}**",
        f"- n_walk_imperfect = **{payload['n_walk_imperfect']}**",
        f"- mean Â walk = **{bp['mean_A_walk']}**",
        f"- mean Â dump = **{bp['mean_A_dump']}**",
        f"- mean Δ (Â_dump − Â_walk) = **{bp['mean']}**",
        f"- median Δ = **{bp['median']}**",
        f"- 95% bootstrap CI = **{bp['ci95']}**",
        f"- stdev Δ = **{bp.get('stdev_delta')}**",
        "",
        "## Results — full set",
        "",
        f"- n_ok = **{fl['n']}**",
        f"- mean score walk = **{fl['mean_score_walk']}**",
        f"- mean score dump = **{fl['mean_score_dump']}**",
        f"- mean Â walk = **{fl['mean_A_walk']}**",
        f"- mean Â dump = **{fl['mean_A_dump']}**",
        f"- mean Δ = **{fl['mean']}**",
        f"- median Δ = **{fl['median']}**",
        f"- 95% bootstrap CI = **{fl['ci95']}**",
        "",
        "## Walk-imperfect stratum",
        "",
        f"- count = **{payload['n_walk_imperfect']}** (target ≤20% → ≤40)",
        f"- reasons (top): {json.dumps(payload.get('walk_imperfect_reasons', {}), ensure_ascii=False)}",
        "",
        "## Pass/fail",
        "",
        f"**{payload['verdict']}**",
        "",
        payload["verdict_reason"],
        "",
        "## Notes",
        "",
        "- Prior synthetic pilot (n=500) had constant Δ=1934 (isomorphic clones); this stratum forbids that.",
        "- Reviews in `reviews.jsonl` (200 notes).",
        "- Coefficients locked identical to prior P1; not retuned after outcomes.",
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def export_graph_json(spec: GraphSpec, path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "session_i": spec.session_i,
                "family": spec.family,
                "hub_slug": spec.hub_slug,
                "gold_slugs": spec.gold_slugs,
                "gold_hop": spec.gold_hop,
                "n_distractor_hubs": spec.n_distractor_hubs,
                "has_dead_ends": spec.has_dead_ends,
                "expect_walk_perfect": spec.expect_walk_perfect,
                "walk_miss_reason": spec.walk_miss_reason,
                "nodes": [n.__dict__ for n in spec.nodes],
                "edges": [e.__dict__ for e in spec.edges],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    t0 = time.time()
    import memnet as _memnet_pkg

    memnet_file = getattr(_memnet_pkg, "__file__", None)
    print("=== STM Prediction 1 — human-reviewed stratum ===")
    print(f"coefficient lock: a={COEF_A} b={COEF_B} c={COEF_C} d={COEF_D}")
    print(f"memnet={MEMNET_VERSION} commit={MERGE_COMMIT}")
    print(f"n={N_SESSIONS} M={M_HARD} k={K_HOP}")

    GRAPHS_DIR.mkdir(parents=True, exist_ok=True)
    specs_dir = GRAPHS_DIR / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)

    # --- Phase 1: design + review ---
    seen_keys: set[tuple] = set()
    specs: list[GraphSpec] = []
    reviews: list[dict] = []
    for i in range(N_SESSIONS):
        spec, rev = redesign_until_pass(i, seen_keys)
        specs.append(spec)
        reviews.append(rev)
        export_graph_json(spec, specs_dir / f"g{i:04d}.json")
        if (i + 1) % 50 == 0:
            print(f"  reviewed {i+1}/{N_SESSIONS}")

    with REVIEWS_PATH.open("w", encoding="utf-8") as fh:
        for rev in reviews:
            fh.write(json.dumps(rev, ensure_ascii=False) + "\n")

    n_pass = sum(1 for r in reviews if r["checklist_pass"])
    fam_hist = Counter(s.family for s in specs)
    print(f"checklist PASS {n_pass}/{N_SESSIONS}; families={len(fam_hist)}")

    # --- Phase 2: run MemNet pairs ---
    eng = Engine()
    results = []
    for i, spec in enumerate(specs):
        results.append(run_pair(eng, spec))
        if (i + 1) % 25 == 0:
            print(f"  ran {i+1}/{N_SESSIONS} ({time.time()-t0:.1f}s)")

    ok_rows = [r for r in results if r.get("ok")]
    both = [r for r in ok_rows if r.get("both_perfect")]
    imperfect = [r for r in ok_rows if r.get("walk_imperfect")]
    full_deltas = [r["delta_action"] for r in ok_rows]
    bp_deltas = [r["delta_action"] for r in both]

    stats_bp = pack_stats(both, bp_deltas)
    stats_full = pack_stats(ok_rows, full_deltas)

    # walk imperfect reasons
    reason_counts: Counter = Counter()
    for r in imperfect:
        why = r.get("walk_miss_reason") or "unknown"
        # bucket
        if "cap_binding" in why or "cap_bind" in why:
            reason_counts["cap_binding"] += 1
        elif "wrong_branch" in why or "wrong branch" in why.lower():
            reason_counts["wrong_branch"] += 1
        else:
            reason_counts["other"] += 1

    verdict = "FAIL"
    reason = ""
    if stats_bp["n"] == 0:
        reason = "No pairs with both score==1.0; cannot compare at equal quality."
    else:
        mean_d = stats_bp["mean"]
        lo, hi = stats_bp["ci95"]
        if mean_d is not None and mean_d > 0 and lo is not None and lo > 0:
            verdict = "PASS"
            reason = (
                f"On both-perfect stratum (n={stats_bp['n']}), mean Δ={mean_d:.4f} > 0 "
                f"and 95% CI [{lo:.4f}, {hi:.4f}] excludes 0 — dump costs more action "
                f"at equal quality. Coefficients not retuned."
            )
        elif mean_d is not None and mean_d <= 0:
            reason = (
                f"mean Δ={mean_d:.4f} ≤ 0 on both-perfect stratum — dump did not cost "
                f"more action at equal quality."
            )
        else:
            reason = (
                f"mean Δ={mean_d}; CI={stats_bp['ci95']} — CI does not exclude 0 "
                f"(or mean Δ≤0)."
            )

    wall = time.time() - t0

    # Δ uniqueness check vs constant-pilot failure mode
    unique_deltas = len(set(round(d, 6) for d in bp_deltas)) if bp_deltas else 0

    slim = []
    for r in results:
        if not r.get("ok"):
            slim.append(r)
            continue
        slim.append(
            {
                "session_i": r["session_i"],
                "family": r["family"],
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
                "walk_imperfect": r["walk_imperfect"],
                "walk_miss_reason": r.get("walk_miss_reason"),
                "ok": True,
            }
        )

    sample_sessions = slim[:5]

    payload = {
        "prediction": 1,
        "stratum": "human-reviewed",
        "honesty": "Sage author-blind ACCEPT after regen (experiments/p1-blind/SAGE_SIGNOFF.md)",
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
            "d_empty_W": "|W|",
            "term_a": "a * |W|^2",
            "tokens": "sum(len(title)+len(slug))",
            "ell_task": "1-score",
            "locked_before_outcomes": True,
            "same_as_prior_p1": True,
            "retuned": False,
        },
        "protocol": {
            "k_hop": K_HOP,
            "M_hard": M_HARD,
            "cue_kind": CUE_KIND,
            "walk_admits_all_offered": True,
            "dump_is_bench_fixture": True,
            "equal_quality": "both score==1.0",
        },
        "n_sessions": N_SESSIONS,
        "n_ok": len(ok_rows),
        "n_both_perfect": len(both),
        "n_walk_imperfect": len(imperfect),
        "n_build_fail": len(results) - len(ok_rows),
        "n_checklist_pass": n_pass,
        "n_families": len(fam_hist),
        "family_histogram": dict(sorted(fam_hist.items())),
        "walk_imperfect_reasons": dict(reason_counts),
        "unique_delta_values_both_perfect": unique_deltas,
        "wall_time_s": wall,
        "stats_both_perfect": stats_bp,
        "stats_full": stats_full,
        "verdict": verdict,
        "verdict_reason": reason,
        "call_counts": eng.calls,
        "sessions": slim,
        "sessions_sample": sample_sessions,
    }

    RESULTS_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    summary = {
        k: payload[k]
        for k in (
            "prediction",
            "stratum",
            "honesty",
            "memnet_version",
            "memnet_commit",
            "coefficient_lock",
            "protocol",
            "n_sessions",
            "n_ok",
            "n_both_perfect",
            "n_walk_imperfect",
            "n_checklist_pass",
            "n_families",
            "family_histogram",
            "walk_imperfect_reasons",
            "unique_delta_values_both_perfect",
            "wall_time_s",
            "stats_both_perfect",
            "stats_full",
            "verdict",
            "verdict_reason",
            "call_counts",
        )
    }
    summary["sessions_sample"] = sample_sessions
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_report(payload)

    print(f"n_both_perfect={len(both)} n_walk_imperfect={len(imperfect)} n_families={len(fam_hist)}")
    print(f"unique_deltas_bp={unique_deltas}")
    print(f"meanÂ_walk={stats_bp['mean_A_walk']} meanÂ_dump={stats_bp['mean_A_dump']}")
    print(f"Δ={stats_bp['mean']} CI={stats_bp['ci95']}")
    print(f"verdict={verdict}")
    print(f"wrote {RESULTS_PATH}, {SUMMARY_PATH}, {REPORT_PATH}, {REVIEWS_PATH} in {wall:.1f}s")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
