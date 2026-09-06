#!/usr/bin/env python3
"""ShapeWalk vs Dump vs RAG lexical top-k — protocol + harness scaffold.

Lock: experiments/shapewalk-vs-rag/PROTOCOL.md (preregistered; no Result here).
Authoritative Â / PASS numbers do not exist until a locked live run. This
script does not write results.summary.json unless SHAPEWALK_VS_RAG_WRITE=1.

Three W builders:
  shapewalk — live: MemNet pin_map (same spirit as p1-llm-hard walk).
              dry: BFS k-hop cap-M stand-in (NOT pin_map; labelled).
  dump      — all observable nodes from the graph spec (P1 dump fixture).
  rag       — lexical token-Jaccard top-k; deterministic; no embeddings.

Scorer copied (minimal) from experiments/p1-llm-hard/: full-gold evidence
recall + noise_leak gate. Do not change p1-llm-hard.

Env:
  OPENROUTER_API_KEY           required for a live generate (never commit)
  OPENROUTER_BASE_URL          default https://openrouter.ai/api/v1
  P1_LLM_MODEL                 default openai/gpt-4o-mini
  SHAPEWALK_VS_RAG_WRITE       if 1, allow writing results.summary.json
  SHAPEWALK_VS_RAG_DRY         if 1, W-stats only (not a paper verdict)

No secrets in this file. No MemNet SemVer claim.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
P1_HR_SPECS = HERE.parent / "p1-hr" / "graphs" / "specs"
SUMMARY_PATH = HERE / "results.summary.json"
LIVE_PATH = HERE / "results.live.json"

# --- Preregistered protocol constants (FIXED; match PROTOCOL.md) ---
MEMNET_PACKAGE = "memnet-llm==0.19.4"
K_HOP = 2
M_WALK = 12
RAG_K = M_WALK  # equal-cap; not mean |W|_walk ≈ 9.13
CUE_KIND = "HUB"
COEF_A = 1.0
COEF_B = 1.0
COEF_C = 0.0
COEF_D = 10.0
N_SESSIONS = 200
N_TRIPLE_MIN = 30
BOOTSTRAP_B = 10_000
BOOTSTRAP_SEED = 42
DEFAULT_BASE = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-4o-mini"
TEMPERATURE = 0.0

TOKEN_RE = re.compile(r"[EN]\d+-[A-Za-z0-9._-]+")
LEX_TOKEN_RE = re.compile(r"[a-z0-9]+")

TASK_INSTRUCTION = (
    "The working set below is the only material you may use. "
    "Lines tagged evidence: hold values you must list. "
    "Lines tagged noise: must be ignored. "
    "There are no KEY= or key: markers. "
    "List every evidence value, alphabetical, comma-separated. "
    "Output only those values, nothing else. "
    "Do not invent values that are not tagged evidence."
)


@dataclass(frozen=True)
class NodeObs:
    """Observable node fields only. nick/hid must never enter RAG features."""

    kind: str
    slug: str
    title: str


@dataclass(frozen=True)
class GraphObs:
    session_i: int
    family: str
    hub_slug: str
    gold_slugs: tuple[str, ...]
    nodes: tuple[NodeObs, ...]
    edges: tuple[tuple[str, str], ...]  # undirected hop graph (src, dst)

    def hub(self) -> NodeObs:
        for n in self.nodes:
            if n.slug == self.hub_slug:
                return n
        raise KeyError(self.hub_slug)


# --- Scorer (minimal copy of p1-llm-hard; do not import/break that file) ---


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


def action_estimate(*, w_size: int, tokens: int, score: float) -> float:
    """Â stand-in: d(∅,W)=|W|; conceptual d remains Lev (37). Coeffs locked."""
    d_trans = float(w_size)
    return (
        COEF_A * (d_trans ** 2)
        + COEF_B * float(tokens)
        + COEF_C * 0.0
        + COEF_D * (1.0 - float(score))
    )


def node_tokens(title: str, slug: str) -> int:
    return len(title) + len(slug)


# --- RAG lexical top-k (real, deterministic) ---


def lex_tokens(*parts: str) -> frozenset[str]:
    """Alphanumeric tokens, lowercased. Never pass nick/hid here."""
    blob = " ".join(parts)
    return frozenset(LEX_TOKEN_RE.findall(blob.lower()))


def token_jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def cue_tokens(hub: NodeObs) -> frozenset[str]:
    """RelativeSeed cue: kind + slug + title. Observables only."""
    return lex_tokens(hub.kind, hub.slug, hub.title)


def candidate_tokens(node: NodeObs) -> frozenset[str]:
    return lex_tokens(node.kind, node.slug, node.title)


def rag_score(hub: NodeObs, node: NodeObs) -> float:
    return token_jaccard(cue_tokens(hub), candidate_tokens(node))


def build_w_rag(graph: GraphObs, *, k: int = RAG_K) -> list[NodeObs]:
    """Admit top-k by Jaccard; score order is physical W order."""
    hub = graph.hub()
    ranked = sorted(
        graph.nodes,
        key=lambda n: (-rag_score(hub, n), n.slug),
    )
    return list(ranked[:k])


def build_w_dump(graph: GraphObs) -> list[NodeObs]:
    """Uncapped dump of observable nodes (spec order)."""
    return list(graph.nodes)


def build_w_shapewalk_dry_standin(graph: GraphObs) -> list[NodeObs]:
    """BFS k-hop from hub, cap M. NOT pin_map. Dry only."""
    adj: dict[str, set[str]] = {n.slug: set() for n in graph.nodes}
    for src, dst in graph.edges:
        if src in adj and dst in adj:
            adj[src].add(dst)
            adj[dst].add(src)
    by_slug = {n.slug: n for n in graph.nodes}
    order: list[NodeObs] = []
    seen = {graph.hub_slug}
    q = [graph.hub_slug]
    hops = {graph.hub_slug: 0}
    for u in q:
        if hops[u] > K_HOP:
            continue
        node = by_slug.get(u)
        if node is not None:
            order.append(node)
            if len(order) >= M_WALK:
                return order
        if hops[u] == K_HOP:
            continue
        for v in sorted(adj.get(u, ())):
            if v not in seen:
                seen.add(v)
                hops[v] = hops[u] + 1
                q.append(v)
    return order[:M_WALK]


def gold_in_w(graph: GraphObs, w: list[NodeObs]) -> list[str]:
    slugs = {n.slug for n in w}
    return [g for g in graph.gold_slugs if g in slugs]


def load_graph_json(path: Path) -> GraphObs:
    raw = json.loads(path.read_text(encoding="utf-8"))
    nodes = tuple(
        NodeObs(
            kind=str(n["kind"]),
            slug=str(n["slug"]),
            title=str(n["title"]),
        )
        for n in raw["nodes"]
    )
    edges = tuple(
        (str(e["src_slug"]), str(e["dst_slug"])) for e in raw.get("edges", [])
    )
    return GraphObs(
        session_i=int(raw["session_i"]),
        family=str(raw.get("family", "")),
        hub_slug=str(raw["hub_slug"]),
        gold_slugs=tuple(str(s) for s in raw["gold_slugs"]),
        nodes=nodes,
        edges=edges,
    )


def load_p1_hr_graphs(*, limit: int | None = None) -> list[GraphObs]:
    paths = sorted(P1_HR_SPECS.glob("g*.json"))
    graphs = [load_graph_json(p) for p in paths]
    graphs.sort(key=lambda g: g.session_i)
    if limit is not None:
        graphs = graphs[:limit]
    return graphs


def w_stats_row(graph: GraphObs, w: list[NodeObs]) -> dict:
    gold = gold_in_w(graph, w)
    n_gold = len(graph.gold_slugs)
    tokens = sum(node_tokens(n.title, n.slug) for n in w)
    coverage = (len(gold) / n_gold) if n_gold else 1.0
    return {
        "session_i": graph.session_i,
        "w_size": len(w),
        "tokens": tokens,
        "n_gold": n_gold,
        "n_gold_in_w": len(gold),
        "gold_coverage_in_w": coverage,
        "w_slugs": [n.slug for n in w],
    }


def summarise_arm(rows: list[dict]) -> dict:
    n = len(rows)
    if not n:
        return {"n": 0}
    return {
        "n": n,
        "mean_w": sum(r["w_size"] for r in rows) / n,
        "mean_gold_in_w": sum(r["n_gold_in_w"] for r in rows) / n,
        "mean_gold_coverage_in_w": sum(r["gold_coverage_in_w"] for r in rows) / n,
        "mean_tokens": sum(r["tokens"] for r in rows) / n,
    }


def check_scorer() -> int:
    """p1-llm-hard session 170 identity + RAG firewall / determinism."""
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

    # RAG: nick must not affect rank; order deterministic; k cap.
    hub = NodeObs("HUB", "hub-s0000", "Star hub s0000")
    decoy = NodeObs("NOISE", "zzzz-noise", "unrelated blob")
    near = NodeObs("SPOKE", "spoke-s0000-n00", "Spoke s0000 #00")
    twin_b = NodeObs("LEAF", "aaa-s0000", "Star hub s0000")
    twin_a = NodeObs("LEAF", "bbb-s0000", "Star hub s0000")
    graph = GraphObs(
        session_i=0,
        family="check",
        hub_slug="hub-s0000",
        gold_slugs=("hub-s0000",),
        nodes=(hub, decoy, near, twin_b, twin_a),
        edges=(),
    )
    w = build_w_rag(graph, k=3)
    assert len(w) == 3
    # Hub Jaccard vs itself is 1; next, twins share title tokens; slug tie-break.
    assert w[0].slug == "hub-s0000"
    twin_slugs = {w[1].slug, w[2].slug}
    assert twin_slugs == {"aaa-s0000", "bbb-s0000"}, twin_slugs
    assert w[1].slug < w[2].slug  # lexicographic slug after equal Jaccard
    w2 = build_w_rag(graph, k=3)
    assert [n.slug for n in w] == [n.slug for n in w2]

    poisoned = GraphObs(
        session_i=0,
        family="check",
        hub_slug="hub-s0000",
        gold_slugs=("hub-s0000",),
        nodes=(
            hub,
            NodeObs("NOISE", "hid-leak", "zzzz"),
        ),
        edges=(),
    )
    # Features are kind/slug/title only; a slug containing "hid" is still an
    # observable locator (not the hid field). Nickname is not on NodeObs.
    assert not hasattr(NodeObs, "nick")
    scored = rag_score(hub, poisoned.nodes[1])
    assert isinstance(scored, float)

    a = lex_tokens("HUB", "hub-s0000")
    b = lex_tokens("HUB", "hub-s0000")
    assert abs(token_jaccard(a, b) - 1.0) < 1e-12
    c = lex_tokens("NOISE", "zzzz")
    assert token_jaccard(a, c) < 1.0

    dump_w = build_w_dump(graph)
    assert len(dump_w) == len(graph.nodes)

    print("HARD session 170: walk score_llm=0.20 (1/5) if only resident evidence")
    print("dump score_llm=1.00; noise_leak if any N… in pred")
    print("equal_quality requires score_llm==1.0 AND no noise_leak")
    print(f"RAG k={RAG_K} == M_walk={M_WALK}; token Jaccard; nick off NodeObs")
    print("check-scorer: ok")
    return 0


def run_dry(*, limit: int | None) -> int:
    graphs = load_p1_hr_graphs(limit=limit)
    if not graphs:
        print(f"No p1-hr specs under {P1_HR_SPECS}", file=sys.stderr)
        return 1
    arms = {
        "shapewalk_dry_standin": build_w_shapewalk_dry_standin,
        "dump": build_w_dump,
        "rag": build_w_rag,
    }
    payload: dict = {
        "dry_run": True,
        "note": (
            "Not a paper verdict. ShapeWalk here is BFS k-hop cap-M, not "
            "pin_map. RAG lexical top-k is the real v1 scorer. See PROTOCOL.md."
        ),
        "locked": {
            "memnet_package": MEMNET_PACKAGE,
            "k_hop": K_HOP,
            "M_walk": M_WALK,
            "rag_k": RAG_K,
            "cue_kind": CUE_KIND,
            "coef": {"a": COEF_A, "b": COEF_B, "c": COEF_C, "d": COEF_D},
            "d_empty_W": "|W|",
            "conceptual_d": "Lev (37)",
            "n_triple_min": N_TRIPLE_MIN,
            "bootstrap_B": BOOTSTRAP_B,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "temperature": TEMPERATURE,
            "model": DEFAULT_MODEL,
            "retuned": False,
        },
        "n_graphs": len(graphs),
        "arms": {},
    }
    print(
        "DRY (not a paper verdict). "
        f"n={len(graphs)} p1-hr specs. RAG k={RAG_K}. "
        "ShapeWalk = BFS stand-in, not pin_map."
    )
    for name, builder in arms.items():
        rows = [w_stats_row(g, builder(g)) for g in graphs]
        summary = summarise_arm(rows)
        payload["arms"][name] = {"summary": summary}
        print(
            f"  {name}: mean|W|={summary['mean_w']:.4f} "
            f"mean gold∩W={summary['mean_gold_in_w']:.4f} "
            f"mean gold coverage in W={summary['mean_gold_coverage_in_w']:.4f}"
        )
    LIVE_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {LIVE_PATH} (dry). Did not write {SUMMARY_PATH}.")
    return 0


def maybe_refuse_summary_write() -> None:
    write = os.environ.get("SHAPEWALK_VS_RAG_WRITE", "").strip() in {
        "1",
        "true",
        "TRUE",
        "yes",
    }
    if write:
        print(
            "SHAPEWALK_VS_RAG_WRITE=1 is set, but this scaffold has no locked "
            "live verdict to write. Refusing to create results.summary.json.",
            file=sys.stderr,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-scorer",
        action="store_true",
        help="Run evidence-vs-noise scorer + RAG determinism checks (no API).",
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
        help="Optional cap on number of p1-hr graphs (dry only).",
    )
    args = parser.parse_args()
    if args.check_scorer or os.environ.get("SHAPEWALK_VS_RAG_CHECK", "").strip() in {
        "1",
        "true",
        "TRUE",
        "yes",
    }:
        return check_scorer()

    dry = args.dry or os.environ.get("SHAPEWALK_VS_RAG_DRY", "").strip() in {
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
            "No results.summary.json in this scaffold; PROTOCOL.md is the lock. "
            "Live three-arm LLM generate is not shipped as a 200-session driver.",
            file=sys.stderr,
        )
        maybe_refuse_summary_write()
        return 2

    maybe_refuse_summary_write()
    print(
        "Live OpenRouter three-arm generate is not shipped as a full "
        "200-session driver in this scaffold. Install "
        f"{MEMNET_PACKAGE}, reuse experiments/p1-hr graphs, "
        f"pin_map M={M_WALK} k={K_HOP} vs dump vs RAG lexical top-k={RAG_K}, "
        f"model={os.environ.get('P1_LLM_MODEL', DEFAULT_MODEL)}, "
        f"T={TEMPERATURE}, score_llm=full_gold_evidence, no KEY= markers. "
        "Do not commit the API key. Do not invent results.summary.json."
    )
    LIVE_PATH.write_text(
        json.dumps(
            {
                "live_driver_shipped": False,
                "note": (
                    "Not a paper verdict. Run --dry for W stats; PROTOCOL.md "
                    "for the lock. results.summary.json must come from a "
                    "locked live run with WRITE=1 after the driver exists."
                ),
                "model": os.environ.get("P1_LLM_MODEL", DEFAULT_MODEL),
                "temperature": TEMPERATURE,
                "rag_k": RAG_K,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {LIVE_PATH}. Did not write {SUMMARY_PATH}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
