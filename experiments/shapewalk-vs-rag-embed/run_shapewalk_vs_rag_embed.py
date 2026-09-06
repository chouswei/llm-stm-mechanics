#!/usr/bin/env python3
"""ShapeWalk vs Dump vs Embedding RAG top-k — live three-arm OpenRouter driver.

Lock: experiments/shapewalk-vs-rag-embed/PROTOCOL.md (preregistered; do not retune).
Parent lock: experiments/shapewalk-vs-rag/ (lexical PASS; do not overwrite).
Authoritative Â / PASS numbers do not exist until a locked live run is written
under SHAPEWALK_VS_RAG_EMBED_WRITE=1. Default live writes results.live.json only.

Three W builders (lexical Jaccard is NOT in this live loop):
  shapewalk — live: MemNet PinMapComposer.compose / pin_map (not BFS).
              dry: BFS k-hop cap-M stand-in (NOT pin_map; labelled).
  dump      — live: all observable session nodes (P1 dump fixture; uncapped).
              dry: all observable nodes from the graph spec.
  embed_rag — MiniLM cosine top-k; local sentence-transformers; no embed API;
              no hid/nick in embed texts; vectors never on pin_map.

Scorer copied (minimal) from experiments/p1-llm-hard/: full-gold evidence
recall + noise_leak gate. Do not change p1-llm-hard.

Env:
  OPENROUTER_API_KEY                required for a live generate (never commit)
  OPENROUTER_BASE_URL               default https://openrouter.ai/api/v1
  P1_LLM_MODEL                      default openai/gpt-4o-mini
  SHAPEWALK_VS_RAG_EMBED_WRITE      if 1, also write results.summary.json after
                                    a real live run (do not set from a different
                                    model / package / embedder / scorer)
  SHAPEWALK_VS_RAG_EMBED_DRY        if 1, W-stats only (not a paper verdict)

No secrets in this file. No MemNet SemVer claim.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import statistics
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
P1_HR_DIR = HERE.parent / "p1-hr"
P1_HR_SPECS = P1_HR_DIR / "graphs" / "specs"
SCHEMA_PATH = P1_HR_DIR / "schema.txt"
SUMMARY_PATH = HERE / "results.summary.json"
LIVE_PATH = HERE / "results.live.json"

# --- Preregistered protocol constants (FIXED; match PROTOCOL.md) ---
MEMNET_PACKAGE = "memnet-llm==0.19.5"
MEMNET_PACKAGE_OK = ("0.19.5", "0.19.4")
K_HOP = 2
M_WALK = 12
RAG_K = M_WALK  # equal-cap; same k as lexical; do not retune lexical Jaccard
CUE_KIND = "HUB"
EMBEDDER_ID = "sentence-transformers/all-MiniLM-L6-v2"
COEF_A = 1.0
COEF_B = 1.0
COEF_C = 0.0
COEF_D = 10.0
N_SESSIONS = 200
N_PAIR_MIN = 30
BOOTSTRAP_B = 10_000
BOOTSTRAP_SEED = 42
DEFAULT_BASE = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-4o-mini"
TEMPERATURE = 0.0
MAX_TOKENS = 256
HTTP_RETRIES = 6

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

_MINILM_MODEL = None


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
    raw: dict[str, Any]

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


# --- Embedding RAG top-k (local MiniLM; no vectors on pin_map) ---


def observable_embed_text(node: NodeObs) -> str:
    """kind + slug + title only. Never hid / nick / store keys."""
    return f"{node.kind} {node.slug} {node.title}"


def cosine_similarity(u: list[float], v: list[float]) -> float:
    if len(u) != len(v):
        raise ValueError("cosine_similarity: vector length mismatch")
    nu = math.sqrt(sum(x * x for x in u))
    nv = math.sqrt(sum(x * x for x in v))
    if nu == 0.0 or nv == 0.0:
        return 0.0
    return sum(a * b for a, b in zip(u, v)) / (nu * nv)


def rank_by_cosine(
    nodes: tuple[NodeObs, ...] | list[NodeObs],
    scores: list[float],
    *,
    k: int,
) -> list[NodeObs]:
    """Admit top-k: higher cosine first, then lexicographic slug."""
    if len(nodes) != len(scores):
        raise ValueError("rank_by_cosine: nodes/scores length mismatch")
    ranked = sorted(zip(scores, nodes), key=lambda t: (-t[0], t[1].slug))
    return [n for _s, n in ranked[:k]]


def embedder_available() -> bool:
    try:
        import sentence_transformers  # noqa: F401
    except ImportError:
        return False
    return True


def skip_minilm_message() -> str:
    return (
        "SKIP: sentence-transformers is not installed; cannot run MiniLM "
        f"Embedding RAG ({EMBEDDER_ID}). "
        "Install with: pip install sentence-transformers"
    )


def get_minilm():
    """Load preregistered MiniLM once. Vectors stay in this arm, not pin_map."""
    global _MINILM_MODEL
    if _MINILM_MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(skip_minilm_message()) from exc
        _MINILM_MODEL = SentenceTransformer(EMBEDDER_ID)
    return _MINILM_MODEL


def encode_texts(texts: list[str]) -> list[list[float]]:
    model = get_minilm()
    vecs = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return [list(map(float, row)) for row in vecs]


def embed_scores(hub: NodeObs, nodes: tuple[NodeObs, ...] | list[NodeObs]) -> list[float]:
    texts = [observable_embed_text(hub)] + [observable_embed_text(n) for n in nodes]
    vecs = encode_texts(texts)
    query = vecs[0]
    return [cosine_similarity(query, vecs[i + 1]) for i in range(len(nodes))]


def build_w_embed_rag(graph: GraphObs, *, k: int = RAG_K) -> list[NodeObs]:
    """Admit top-k by MiniLM cosine; score order is physical W order."""
    hub = graph.hub()
    scores = embed_scores(hub, graph.nodes)
    return rank_by_cosine(graph.nodes, scores, k=k)


def build_w_dump(graph: GraphObs) -> list[NodeObs]:
    """Uncapped dump of observable nodes (spec order). Dry / JSON fixture."""
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
        raw=raw,
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


def locked_block() -> dict:
    return {
        "memnet_package": MEMNET_PACKAGE,
        "memnet_package_ok": list(MEMNET_PACKAGE_OK),
        "k_hop": K_HOP,
        "M_walk": M_WALK,
        "rag_k": RAG_K,
        "cue_kind": CUE_KIND,
        "embedder": EMBEDDER_ID,
        "embed_api": None,
        "lexical_jaccard_in_live_loop": False,
        "parent_lexical_protocol": "experiments/shapewalk-vs-rag/PROTOCOL.md",
        "coef": {"a": COEF_A, "b": COEF_B, "c": COEF_C, "d": COEF_D},
        "d_empty_W": "|W|",
        "conceptual_d": "Lev (37)",
        "n_pair_min": N_PAIR_MIN,
        "bootstrap_B": BOOTSTRAP_B,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "temperature": TEMPERATURE,
        "model": DEFAULT_MODEL,
        "scorer": "full_gold_evidence",
        "equal_quality": "score_llm==1.0 AND no noise_leak",
        "retuned": False,
        "semver_claim": False,
        "vectors_on_pin_map": False,
    }


def format_working_set(session_i: int, w: list[NodeObs], gold_slugs: tuple[str, ...]) -> str:
    """Prompt-only evidence/noise tags. Observables only (no nick/hid)."""
    gold = set(gold_slugs)
    lines: list[str] = []
    for n in w:
        title = n.title.replace("'", "")
        if n.slug in gold:
            tag = f"evidence: '{evidence_value(session_i, n.slug)}'"
        else:
            tag = f"noise: '{noise_value(session_i, n.slug)}'"
        lines.append(f"(:{n.kind} {{slug: '{n.slug}', title: '{title}'}}) {tag}")
    return "\n".join(lines)


def build_prompt(session_i: int, w: list[NodeObs], gold_slugs: tuple[str, ...]) -> str:
    body = format_working_set(session_i, w, gold_slugs)
    return f"{TASK_INSTRUCTION}\n\nworking set:\n{body}"


def evaluate_arm(graph: GraphObs, w: list[NodeObs], pred_text: str) -> dict:
    gold_ev = full_gold_evidence(graph.session_i, list(graph.gold_slugs))
    pred = parse_pred_values(pred_text)
    score = score_llm_full_gold_evidence(pred, gold_ev)
    leak = noise_leak(pred)
    tokens = sum(node_tokens(n.title, n.slug) for n in w)
    ahat = action_estimate(w_size=len(w), tokens=tokens, score=score)
    gold = gold_in_w(graph, w)
    return {
        "w_size": len(w),
        "tokens": tokens,
        "n_gold_in_w": len(gold),
        "gold_in_w": gold,
        "score_llm": score,
        "noise_leak": leak,
        "A_hat": ahat,
        "equal_quality": equal_quality(score, pred),
        "pred": sorted(pred),
        "w_slugs": [n.slug for n in w],
    }


def bootstrap_ci(
    deltas: list[float], n_boot: int = BOOTSTRAP_B, seed: int = BOOTSTRAP_SEED
) -> dict:
    if not deltas:
        return {"mean": None, "median": None, "ci95": [None, None], "n": 0, "n_bootstrap": n_boot}
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


def ci_excludes_zero_positive(ci: list) -> bool:
    lo, hi = ci[0], ci[1]
    if lo is None or hi is None:
        return False
    return float(lo) > 0.0


def primary_verdict(n_pair: int, embed_stats: dict) -> tuple[str, str]:
    if n_pair < N_PAIR_MIN:
        return (
            "FAIL",
            f"n_pair={n_pair} < n_pair_min={N_PAIR_MIN}. Dump pairwise "
            "is secondary and does not rescue an embed-pair FAIL.",
        )
    embed_mean = embed_stats.get("mean")
    embed_ok = (
        embed_mean is not None
        and float(embed_mean) > 0.0
        and ci_excludes_zero_positive(embed_stats.get("ci95") or [None, None])
    )
    if embed_ok:
        return (
            "PASS",
            "Equal-quality pairs (ShapeWalk + EmbedRAG): mean Δ_embed>0 and "
            "CI excludes 0; n_pair>="
            f"{N_PAIR_MIN}; coefficients not retuned; scorer is full-gold "
            "evidence + noise_leak gate. Not a proof embeddings always lose.",
        )
    return (
        "FAIL",
        f"Δ_embed mean={embed_mean} ci={embed_stats.get('ci95')} "
        "(need mean>0 and CI excluding 0)",
    )


def write_flag_set() -> bool:
    return os.environ.get("SHAPEWALK_VS_RAG_EMBED_WRITE", "").strip() in {
        "1",
        "true",
        "TRUE",
        "yes",
    }


def _tiny_rank_fixture() -> GraphObs:
    hub = NodeObs("HUB", "hub-s0000", "Star hub s0000")
    decoy = NodeObs("NOISE", "zzzz-noise", "unrelated blob")
    twin_b = NodeObs("LEAF", "aaa-s0000", "Star hub s0000")
    twin_a = NodeObs("LEAF", "bbb-s0000", "Star hub s0000")
    return GraphObs(
        session_i=0,
        family="check",
        hub_slug="hub-s0000",
        gold_slugs=("hub-s0000",),
        nodes=(hub, decoy, twin_b, twin_a),
        edges=(),
        raw={},
    )


def check_scorer() -> int:
    """p1-llm-hard session 170 identity + embed rank / firewall / determinism."""
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

    # Embed rank: higher cosine, then lex slug. Tiny fixture, synthetic vectors.
    graph = _tiny_rank_fixture()
    nodes = graph.nodes
    # Identical query/candidate text for hub → cosine 1; twins share title with
    # hub so get equal mid scores; decoy lowest. Equal-score twins: slug order.
    syn = [1.0, 0.10, 0.80, 0.80]
    w = rank_by_cosine(nodes, syn, k=3)
    assert len(w) == 3
    assert w[0].slug == "hub-s0000"
    assert w[1].slug == "aaa-s0000"
    assert w[2].slug == "bbb-s0000"
    w2 = rank_by_cosine(nodes, syn, k=3)
    assert [n.slug for n in w] == [n.slug for n in w2]

    assert not hasattr(NodeObs, "nick")
    for n in nodes:
        blob = observable_embed_text(n)
        assert "hid" not in blob.split()
        assert "nick" not in blob.split()

    u = [1.0, 0.0]
    v = [1.0, 0.0]
    assert abs(cosine_similarity(u, v) - 1.0) < 1e-12
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) < 1e-12
    assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0

    dump_w = build_w_dump(graph)
    assert len(dump_w) == len(graph.nodes)

    prompt = build_prompt(0, [graph.hub(), nodes[1]], ("hub-s0000",))
    assert "evidence: 'E0-hub-s0000'" in prompt
    assert "noise: 'N0-zzzz-noise'" in prompt
    body = format_working_set(0, [graph.hub(), nodes[1]], ("hub-s0000",))
    assert "KEY=" not in body
    assert "key:" not in body
    assert "nick" not in prompt

    empty = bootstrap_ci([])
    assert empty["n"] == 0
    assert empty["mean"] is None
    v_fail, _ = primary_verdict(0, empty)
    assert v_fail == "FAIL"
    pos = bootstrap_ci([10.0] * 40)
    v_pass, _ = primary_verdict(40, pos)
    assert v_pass == "PASS"
    v_n, _ = primary_verdict(10, pos)
    assert v_n == "FAIL"

    print("HARD session 170: walk score_llm=0.20 (1/5) if only resident evidence")
    print("dump score_llm=1.00; noise_leak if any N… in pred")
    print("equal_quality requires score_llm==1.0 AND no noise_leak")
    print(
        f"Embed RAG k={RAG_K} == M_walk={M_WALK}; cosine; "
        f"embedder={EMBEDDER_ID}; nick off NodeObs; no vectors on pin_map"
    )

    if embedder_available():
        w_live = build_w_embed_rag(graph, k=3)
        w_again = build_w_embed_rag(graph, k=3)
        assert [n.slug for n in w_live] == [n.slug for n in w_again], (
            [n.slug for n in w_live],
            [n.slug for n in w_again],
        )
        assert w_live[0].slug == "hub-s0000"
        print("MiniLM tiny-fixture rank: deterministic (two encodes match)")
    else:
        print(skip_minilm_message() + " (synthetic cosine rank still checked)")

    print("check-scorer: ok")
    return 0


def run_dry(*, limit: int | None) -> int:
    graphs = load_p1_hr_graphs(limit=limit)
    if not graphs:
        print(f"No p1-hr specs under {P1_HR_SPECS}", file=sys.stderr)
        return 1
    has_embed = embedder_available()
    payload: dict = {
        "dry_run": True,
        "live_driver_shipped": True,
        "note": (
            "Not a paper verdict. ShapeWalk here is BFS k-hop cap-M, not "
            "pin_map. Embedding RAG uses real MiniLM when installed. "
            "See PROTOCOL.md."
        ),
        "locked": locked_block(),
        "n_graphs": len(graphs),
        "minilm_installed": has_embed,
        "arms": {},
    }
    print(
        "DRY (not a paper verdict). "
        f"n={len(graphs)} p1-hr specs. RAG k={RAG_K}. "
        "ShapeWalk = BFS stand-in, not pin_map."
    )
    arms: dict = {
        "shapewalk_dry_standin": build_w_shapewalk_dry_standin,
        "dump": build_w_dump,
    }
    if has_embed:
        arms["embed_rag"] = build_w_embed_rag
    else:
        print(skip_minilm_message(), file=sys.stderr)
        payload["embed_rag_skipped"] = skip_minilm_message()

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


def gql_from_raw(raw: dict) -> str:
    """P1-hr mutate fixture: CREATE/MATCH by observable slug, never hid."""
    lines: list[str] = []
    nodes = raw["nodes"]
    for n in nodes:
        title = str(n["title"]).replace("'", "")
        nick = str(n.get("nick") or f"nick-{n['slug']}").replace("'", "")
        lines.append(
            "CREATE (:{kind} {{id: '{nick}', slug: '{slug}', title: '{title}'}})".format(
                kind=n["kind"], nick=nick, slug=n["slug"], title=title
            )
        )
    by_slug = {n["slug"]: n for n in nodes}
    for e in raw.get("edges", []):
        src = e["src_slug"]
        dst = e["dst_slug"]
        if src not in by_slug or dst not in by_slug:
            continue
        sk = by_slug[src]["kind"]
        dk = by_slug[dst]["kind"]
        note = str(e.get("note", "")).replace("'", "")
        nick = str(e.get("nick") or f"nick-e-{src}-{dst}").replace("'", "")
        rel = e["rel"]
        lines.append(
            f"MATCH (a:{sk} {{slug: '{src}'}}), "
            f"(b:{dk} {{slug: '{dst}'}})"
        )
        lines.append(
            f"CREATE (a)-[:{rel} {{id: '{nick}', note: '{note}'}}]->(b)"
        )
    return "\n".join(lines) + "\n"


def _configure_memnet_env() -> None:
    os.environ.setdefault("MEMNET_TEST_INLINE", "1")
    os.environ.setdefault("MEMNET_SERVE_INTERNAL", "1")
    os.environ.pop("MEMNET_NEO4J_URL", None)
    os.environ.pop("MEMNET_AGENSGRAPH_URL", None)


def _import_memnet():
    _configure_memnet_env()
    try:
        from memnet import __version__ as MEMNET_VERSION
        from memnet.exceptions import MemNetError
        from memnet.mutate_gate import MutateGate
        from memnet.pin_map_composer import PinMapComposer
        from memnet.session import close_session, open_session
    except ImportError as exc:
        raise RuntimeError(
            f"memnet is required for live ShapeWalk. Install {MEMNET_PACKAGE} "
            f"(or memnet-llm==0.19.4 and record the version)."
        ) from exc
    return MEMNET_VERSION, MemNetError, MutateGate, PinMapComposer, close_session, open_session


class Engine:
    """Product Python API: open, mutate, pin_map, close. Same as p1-hr."""

    def __init__(self) -> None:
        (
            self.memnet_version,
            self.MemNetError,
            self._MutateGate,
            self._PinMapComposer,
            self._close_session,
            self._open_session,
        ) = _import_memnet()
        self.calls = {
            "open_session": 0,
            "MutateGate.apply": 0,
            "PinMapComposer.compose": 0,
            "close_session": 0,
        }

    def open(self):
        self.calls["open_session"] += 1
        return self._open_session(map_file=str(SCHEMA_PATH), ttl_minutes=60)

    def mutate(self, ss, gql: str) -> None:
        self.calls["MutateGate.apply"] += 1
        lines = [ln for ln in gql.splitlines() if ln.strip()]
        self._MutateGate(ss).apply(lines, mode="mutate")

    def pin_map(self, ss, hub_slug: str):
        self.calls["PinMapComposer.compose"] += 1
        rows, text = self._PinMapComposer(ss).compose(
            anchor=None,
            kind=CUE_KIND,
            locators=[("slug", hub_slug)],
            depth=K_HOP,
            max_rows=M_WALK,
            active_only=True,
            require_anchor=False,
        )
        return rows, text or ""

    def close(self, ss) -> None:
        self.calls["close_session"] += 1
        self._close_session(ss.session_id)


def admitted_from_rows(rows) -> list[NodeObs]:
    """Caller admits offered Shape rows (node rows only; skip EDG/LAW)."""
    out: list[NodeObs] = []
    for r in rows:
        if r.tag == "EDG" or getattr(r, "kind", None) == "edge":
            continue
        if r.tag == "LAW":
            continue
        slug = str(r.fields.get("slug", ""))
        title = str(r.fields.get("title", ""))
        if not slug:
            continue
        out.append(NodeObs(kind=str(r.tag), slug=slug, title=title))
    return out


def dump_from_session(ss) -> list[NodeObs]:
    """Uncapped bench dump of observable session nodes (not a product dump)."""
    out: list[NodeObs] = []
    for r in ss.store.list_records(active_only=True):
        if r.tag == "EDG":
            continue
        slug = str(r.fields.get("slug", ""))
        title = str(r.fields.get("title", ""))
        if not slug:
            continue
        out.append(NodeObs(kind=str(r.tag), slug=slug, title=title))
    return out


def live_w_for_session(eng: Engine, graph: GraphObs) -> dict[str, list[NodeObs]]:
    """One MemNet session: pin_map ShapeWalk + dump; Embed RAG from JSON observables."""
    ss = eng.open()
    try:
        eng.mutate(ss, gql_from_raw(graph.raw))
        rows, _text = eng.pin_map(ss, graph.hub_slug)
        walk = admitted_from_rows(rows)
        dump = dump_from_session(ss)
        embed_rag = build_w_embed_rag(graph)
        return {"shapewalk": walk, "dump": dump, "embed_rag": embed_rag}
    finally:
        try:
            eng.close(ss)
        except Exception:
            pass


def _chat_complete(base: str, key: str, model: str, prompt: str) -> str:
    url = base.rstrip("/") + "/chat/completions"
    body = json.dumps(
        {
            "model": model,
            "temperature": TEMPERATURE,
            "max_tokens": MAX_TOKENS,
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
                "X-Title": "llm-stm-mechanics shapewalk-vs-rag-embed",
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


def generate(prompt: str, key: str, base: str, model: str) -> str:
    return _chat_complete(base, key, model, prompt)


def compact_arm(row: dict) -> dict:
    return {
        "w_size": row["w_size"],
        "n_gold_in_w": row["n_gold_in_w"],
        "score_llm": row["score_llm"],
        "noise_leak": row["noise_leak"],
        "A_hat": row["A_hat"],
        "equal_quality": row["equal_quality"],
        "tokens": row["tokens"],
    }


def run_live(*, limit: int | None, key: str, base: str, model: str) -> int:
    if not embedder_available():
        print(skip_minilm_message(), file=sys.stderr)
        return 2
    graphs = load_p1_hr_graphs(limit=limit)
    if not graphs:
        print(f"No p1-hr specs under {P1_HR_SPECS}", file=sys.stderr)
        return 1
    if not SCHEMA_PATH.is_file():
        print(f"Missing schema {SCHEMA_PATH}", file=sys.stderr)
        return 1

    t0 = time.time()
    eng = Engine()
    memnet_version = str(eng.memnet_version)
    if not any(memnet_version.startswith(p) for p in MEMNET_PACKAGE_OK):
        print(
            f"warning: installed memnet {memnet_version} is not "
            f"{MEMNET_PACKAGE} or 0.19.4",
            file=sys.stderr,
        )

    sessions: list[dict] = []
    n_error = 0
    arm_names = ("shapewalk", "dump", "embed_rag")

    print(
        f"LIVE three-arm OpenRouter generate. n={len(graphs)} "
        f"model={model} T={TEMPERATURE} pin_map M={M_WALK} k={K_HOP} "
        f"Embed RAG k={RAG_K} embedder={EMBEDDER_ID} memnet={memnet_version}. "
        "OpenRouter is generate-only. Not a paper summary unless "
        "SHAPEWALK_VS_RAG_EMBED_WRITE=1 after this locked run."
    )

    for graph in graphs:
        try:
            ws = live_w_for_session(eng, graph)
            arm_rows: dict[str, dict] = {}
            for name in arm_names:
                w = ws[name]
                prompt = build_prompt(graph.session_i, w, graph.gold_slugs)
                text = generate(prompt, key, base, model)
                arm_rows[name] = evaluate_arm(graph, w, text)
            a_walk = arm_rows["shapewalk"]["A_hat"]
            row = {
                "session_i": graph.session_i,
                "family": graph.family,
                "hub_slug": graph.hub_slug,
                "n_gold": len(graph.gold_slugs),
                "shapewalk": arm_rows["shapewalk"],
                "dump": arm_rows["dump"],
                "embed_rag": arm_rows["embed_rag"],
                "delta_embed": arm_rows["embed_rag"]["A_hat"] - a_walk,
                "delta_dump": arm_rows["dump"]["A_hat"] - a_walk,
                "pair_equal_quality": (
                    arm_rows["shapewalk"]["equal_quality"]
                    and arm_rows["embed_rag"]["equal_quality"]
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
                "pair_equal_quality": False,
            }
        sessions.append(row)
        if row.get("ok"):
            sw, du, em = row["shapewalk"], row["dump"], row["embed_rag"]
            print(
                f"session {graph.session_i:04d} "
                f"walk |W|={sw['w_size']} gold∩W={sw['n_gold_in_w']} "
                f"score={sw['score_llm']:.3f} leak={int(sw['noise_leak'])} "
                f"Â={sw['A_hat']:.2f} | "
                f"dump |W|={du['w_size']} gold∩W={du['n_gold_in_w']} "
                f"score={du['score_llm']:.3f} leak={int(du['noise_leak'])} "
                f"Â={du['A_hat']:.2f} | "
                f"embed |W|={em['w_size']} gold∩W={em['n_gold_in_w']} "
                f"score={em['score_llm']:.3f} leak={int(em['noise_leak'])} "
                f"Â={em['A_hat']:.2f} pair={int(row['pair_equal_quality'])}",
                flush=True,
            )
        else:
            print(
                f"session {graph.session_i:04d} FAIL {row.get('error')}",
                flush=True,
            )

    ok_rows = [s for s in sessions if s.get("ok")]
    pairs = [s for s in ok_rows if s.get("pair_equal_quality")]
    pair_dump = [
        s
        for s in ok_rows
        if s["shapewalk"]["equal_quality"] and s["dump"]["equal_quality"]
    ]

    stats_pair_embed = bootstrap_ci([s["delta_embed"] for s in pairs])
    stats_pair_dump = bootstrap_ci([s["delta_dump"] for s in pair_dump])
    n_pair = len(pairs)
    verdict, reason = primary_verdict(n_pair, stats_pair_embed)

    n_leak = 0
    for s in ok_rows:
        if any(s[n]["noise_leak"] for n in arm_names):
            n_leak += 1

    elapsed = time.time() - t0
    write_summary = write_flag_set()
    payload = {
        "dry_run": False,
        "live_driver_shipped": True,
        "authoritative_summary": write_summary,
        "note": (
            "Live three-arm generate. results.summary.json is written only if "
            "SHAPEWALK_VS_RAG_EMBED_WRITE=1. This file is not a SemVer claim."
            if write_summary
            else (
                "Live three-arm generate wrote results.live.json only. "
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
            "decoding": "greedy T=0 (predeclared primary band)",
            "use": "generate only; embeddings are local MiniLM",
        },
        "embedder": EMBEDDER_ID,
        "memnet_llm_version": memnet_version,
        "n_sessions": len(graphs),
        "n_ok": len(ok_rows),
        "n_error": n_error,
        "n_pair": n_pair,
        "n_pair_walk_embed": n_pair,
        "n_pair_walk_dump": len(pair_dump),
        "n_noise_leak": n_leak,
        "stats_pairwise_walk_embed": stats_pair_embed,
        "stats_pairwise_walk_dump": stats_pair_dump,
        "verdict": verdict,
        "verdict_reason": reason,
        "elapsed_s": elapsed,
        "call_counts": eng.calls,
        "sessions": sessions,
    }
    LIVE_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        f"n_pair={n_pair} Δ_embed mean={stats_pair_embed['mean']} "
        f"CI={stats_pair_embed['ci95']} Δ_dump mean={stats_pair_dump['mean']} "
        f"CI={stats_pair_dump['ci95']} verdict={verdict}"
    )
    print(f"Wrote {LIVE_PATH}.")

    if write_summary:
        summary = {
            "stratum": "shapewalk-vs-dump-vs-rag-embed-topk",
            "protocol": "experiments/shapewalk-vs-rag-embed/PROTOCOL.md",
            "parent_lexical": "experiments/shapewalk-vs-rag/results.summary.json",
            "honesty": (
                "graphs: Sage author-blind ACCEPT after regen "
                "(experiments/p1-blind/SAGE_SIGNOFF.md); not a SemVer a/b claim"
            ),
            "memnet_llm_version": memnet_version,
            "embedder": EMBEDDER_ID,
            "coefficient_lock": {
                "a": COEF_A,
                "b": COEF_B,
                "c": COEF_C,
                "d": COEF_D,
                "d_empty_W": "|W|",
                "tokens": "sum(len(title)+len(slug))",
                "ell_task": "1-score_llm",
                "locked_before_outcomes": True,
                "retuned": False,
            },
            "llm": payload["llm"],
            "protocol_lock": payload["locked"],
            "n_sessions": len(graphs),
            "n_ok": len(ok_rows),
            "n_error": n_error,
            "n_pair": n_pair,
            "n_pair_min": N_PAIR_MIN,
            "n_pair_walk_embed": n_pair,
            "n_pair_walk_dump": len(pair_dump),
            "n_noise_leak": n_leak,
            "stats_pairwise_walk_embed": stats_pair_embed,
            "stats_pairwise_walk_dump": stats_pair_dump,
            "elapsed_s": elapsed,
            "verdict": verdict,
            "verdict_reason": reason,
            "sessions": [
                {
                    "session_i": s["session_i"],
                    "family": s.get("family"),
                    "ok": s.get("ok"),
                    "pair_equal_quality": s.get("pair_equal_quality"),
                    "delta_embed": s.get("delta_embed"),
                    "delta_dump": s.get("delta_dump"),
                    "shapewalk": compact_arm(s["shapewalk"]) if s.get("ok") else None,
                    "dump": compact_arm(s["dump"]) if s.get("ok") else None,
                    "embed_rag": compact_arm(s["embed_rag"]) if s.get("ok") else None,
                    "error": s.get("error"),
                }
                for s in sessions
            ],
            "harness": "experiments/shapewalk-vs-rag-embed/run_shapewalk_vs_rag_embed.py",
            "T_gt_0": "OPEN",
        }
        SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {SUMMARY_PATH} (SHAPEWALK_VS_RAG_EMBED_WRITE=1).")
    else:
        print(
            f"Did not write {SUMMARY_PATH} "
            "(set SHAPEWALK_VS_RAG_EMBED_WRITE=1 after a locked run)."
        )

    print(reason)
    return 0 if n_error == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-scorer",
        action="store_true",
        help="Run evidence-vs-noise scorer + embed rank checks (no API).",
    )
    parser.add_argument(
        "--dry",
        action="store_true",
        help="Build W for arms from p1-hr JSON; MiniLM if installed; no LLM.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional cap on number of p1-hr graphs (dry or live smoke).",
    )
    args = parser.parse_args()
    if args.check_scorer or os.environ.get("SHAPEWALK_VS_RAG_EMBED_CHECK", "").strip() in {
        "1",
        "true",
        "TRUE",
        "yes",
    }:
        return check_scorer()

    dry = args.dry or os.environ.get("SHAPEWALK_VS_RAG_EMBED_DRY", "").strip() in {
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
            "200-session three-arm generate (pin_map ShapeWalk, dump, "
            f"Embedding RAG MiniLM top-k={RAG_K}). No results.summary.json unless "
            "SHAPEWALK_VS_RAG_EMBED_WRITE=1 after a locked run. PROTOCOL.md is the lock.",
            file=sys.stderr,
        )
        return 2

    base = os.environ.get("OPENROUTER_BASE_URL", DEFAULT_BASE).strip() or DEFAULT_BASE
    model = os.environ.get("P1_LLM_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    return run_live(limit=args.limit, key=key, base=base, model=model)


if __name__ == "__main__":
    sys.exit(main())
