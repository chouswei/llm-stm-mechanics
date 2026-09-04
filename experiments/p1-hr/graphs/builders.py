"""Diverse topology-family builders for STM P1 human-reviewed stratum.

Each call produces a unique GraphSpec parameterized by session_i — not a
permute of a single template. Families intentionally vary n_nodes, n_gold,
gold hop depth, distractor hubs, density, and dead-end presence.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


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
    family: str
    hub_slug: str
    nodes: list[NodeSpec]
    edges: list[EdgeSpec]
    gold_slugs: list[str]
    gold_hop: int  # 1 or 2 (max hop of any gold from hub)
    n_distractor_hubs: int
    has_dead_ends: bool
    edge_density_note: str
    expect_walk_perfect: bool
    walk_miss_reason: str | None = None  # set when expect_walk_perfect=False
    review_hints: dict = field(default_factory=dict)

    @property
    def n_nodes(self) -> int:
        return len(self.nodes)

    @property
    def n_gold(self) -> int:
        return len(self.gold_slugs)

    @property
    def gold_slug_set(self) -> frozenset[str]:
        return frozenset(self.gold_slugs)


def _ss(i: int) -> str:
    return f"s{i:04d}"


def _node(kind: str, slug: str, title: str) -> NodeSpec:
    return NodeSpec(kind, slug, title, f"nick-{slug}")


def _edge(src: str, dst: str, rel: str, note: str) -> EdgeSpec:
    return EdgeSpec(src, dst, rel, note, f"nick-e-{note}-{src}-{dst}"[:80])


def _pad_noise(
    nodes: list[NodeSpec],
    edges: list[EdgeSpec],
    ss: str,
    target_n: int,
    attach_to: str,
    *,
    dead_end: bool = True,
    prefix: str = "noise",
) -> None:
    """Attach filler NOISE / LEAF nodes to reach target_n (or leave if already ≥)."""
    k = 0
    while len(nodes) < target_n:
        slug = f"{prefix}-{ss}-n{k:02d}"
        kind = "LEAF" if dead_end and (k % 3 == 0) else "NOISE"
        nodes.append(_node(kind, slug, f"{kind.title()} {ss} #{k}"))
        # Attach beyond k=2 when possible via a bridge, else to attach_to
        if dead_end and k % 2 == 0 and any(n.slug.startswith(f"bridge-{ss}") for n in nodes):
            bridge = f"bridge-{ss}"
            edges.append(_edge(bridge, slug, "links", f"{prefix}-{k}"))
        else:
            # Prefer attaching to a dedicated far anchor if present
            far = f"far-{ss}"
            if any(n.slug == far for n in nodes):
                edges.append(_edge(far, slug, "links", f"{prefix}-{k}"))
            else:
                edges.append(_edge(attach_to, slug, "links", f"{prefix}-{k}"))
        k += 1


def _ensure_far_branch(
    nodes: list[NodeSpec], edges: list[EdgeSpec], ss: str, via: str
) -> str:
    """Create hop-2 bridge then far anchor so dump has bulk outside walk ball."""
    bridge = f"bridge-{ss}"
    far = f"far-{ss}"
    if not any(n.slug == bridge for n in nodes):
        nodes.append(_node("BRIDGE", bridge, f"Bridge {ss}"))
        edges.append(_edge(via, bridge, "next", "to-bridge"))
    if not any(n.slug == far for n in nodes):
        nodes.append(_node("BRIDGE", far, f"Far anchor {ss}"))
        edges.append(_edge(bridge, far, "next", "to-far"))
    return far


# ---------- family builders ----------

def build_star(i: int) -> GraphSpec:
    ss = _ss(i)
    hub = f"hub-{ss}"
    # vary spoke count and gold size with i
    n_spokes = 8 + (i % 10)  # 8..17
    n_gold = 3 + (i % 5)  # 3..7 (hub + spokes)
    target_n = 28 + (i % 25)  # 28..52
    nodes = [_node("HUB", hub, f"Star hub {ss}")]
    edges: list[EdgeSpec] = []
    spokes = []
    for k in range(n_spokes):
        slug = f"spoke-{ss}-n{k:02d}"
        spokes.append(slug)
        nodes.append(_node("SPOKE", slug, f"Spoke {ss} #{k:02d}"))
        edges.append(_edge(hub, slug, "contains", f"spoke-{k}"))
    # dead-end stubs on some spokes
    has_de = True
    for k in range(2 + (i % 3)):
        de = f"dead-{ss}-n{k:02d}"
        nodes.append(_node("LEAF", de, f"Dead end {ss} #{k}"))
        edges.append(_edge(spokes[k % len(spokes)], de, "links", f"de-{k}"))
    gold = [hub] + spokes[: max(0, n_gold - 1)]
    # far noise for dump weight
    via = spokes[-1]
    _ensure_far_branch(nodes, edges, ss, via)
    _pad_noise(nodes, edges, ss, target_n, hub, dead_end=True)
    return GraphSpec(
        i, "star", hub, nodes, edges, gold, gold_hop=1,
        n_distractor_hubs=0, has_dead_ends=has_de,
        edge_density_note="low-star", expect_walk_perfect=True,
        review_hints={"spokes": n_spokes},
    )


def build_chain_of_hubs(i: int) -> GraphSpec:
    ss = _ss(i)
    n_chain = 3 + (i % 3)  # 3..5 hubs
    hub = f"hub-{ss}-h0"
    nodes: list[NodeSpec] = []
    edges: list[EdgeSpec] = []
    hubs = []
    for k in range(n_chain):
        slug = f"hub-{ss}-h{k}" if k else hub
        # only first is kind HUB for cue; others DIST (distractor hubs)
        kind = "HUB" if k == 0 else "DIST"
        hubs.append(slug)
        nodes.append(_node(kind, slug, f"Chain hub {ss} pos{k}"))
        if k > 0:
            edges.append(_edge(hubs[k - 1], slug, "next", f"chain-{k}"))
    # docs hanging off chain positions
    docs = []
    n_doc = 4 + (i % 4)
    for k in range(n_doc):
        slug = f"doc-{ss}-n{k:02d}"
        docs.append(slug)
        nodes.append(_node("DOC", slug, f"Chain doc {ss} #{k}"))
        edges.append(_edge(hubs[min(k, n_chain - 1)], slug, "documents", f"cd-{k}"))
    n_gold = 3 + (i % 4)
    # gold: legal hub + docs on first two hops
    gold = [hub] + docs[: n_gold - 1]
    gold_hop = 1 if all(
        any(e.src_slug == hub and e.dst_slug == g or e.dst_slug == hub and e.src_slug == g
            for e in edges) or g == hub
        for g in gold
    ) else 2
    # refine gold_hop
    gold_hop = 2 if n_chain >= 3 and any(g in hubs[2:] for g in gold) else (
        2 if any(g in docs[2:] for g in gold) else 1
    )
    # ensure gold within k=2: only take docs linked to hubs[0] or hubs[1]
    safe_docs = [d for d in docs if any(
        (e.src_slug in hubs[:2] and e.dst_slug == d) or (e.dst_slug in hubs[:2] and e.src_slug == d)
        for e in edges
    )]
    gold = [hub] + safe_docs[: n_gold - 1]
    if len(gold) < 3:
        gold = [hub] + docs[:2]
    target_n = 30 + (i % 28)
    _ensure_far_branch(nodes, edges, ss, hubs[-1])
    _pad_noise(nodes, edges, ss, target_n, hubs[-1])
    return GraphSpec(
        i, "chain-of-hubs", hub, nodes, edges, gold,
        gold_hop=2 if n_chain > 2 else 1,
        n_distractor_hubs=n_chain - 1, has_dead_ends=False,
        edge_density_note="chain-sparse", expect_walk_perfect=True,
    )


def build_diamond(i: int) -> GraphSpec:
    ss = _ss(i)
    hub = f"hub-{ss}"
    nodes = [_node("HUB", hub, f"Diamond root {ss}")]
    edges: list[EdgeSpec] = []
    # two parallel mid nodes then join
    left = f"doc-{ss}-left"
    right = f"doc-{ss}-right"
    join = f"tsk-{ss}-join"
    nodes += [
        _node("DOC", left, f"Left arm {ss}"),
        _node("DOC", right, f"Right arm {ss}"),
        _node("TSK", join, f"Join task {ss}"),
    ]
    edges += [
        _edge(hub, left, "next", "dl"),
        _edge(hub, right, "next", "dr"),
        _edge(left, join, "next", "lj"),
        _edge(right, join, "next", "rj"),
    ]
    # extra parallel arms for variety
    n_extra = 1 + (i % 3)
    extras = []
    for k in range(n_extra):
        a = f"doc-{ss}-arm{k}"
        extras.append(a)
        nodes.append(_node("DOC", a, f"Arm {ss} #{k}"))
        edges.append(_edge(hub, a, "next", f"arm-{k}"))
        edges.append(_edge(a, join, "next", f"armj-{k}"))
    n_gold = 3 + (i % 4)
    gold = [hub, left, right, join][:n_gold]
    if n_gold > 4:
        gold = [hub, left, right, join] + extras[: n_gold - 4]
    # dead ends off left
    has_de = (i % 2 == 0)
    if has_de:
        for k in range(2 + (i % 2)):
            de = f"dead-{ss}-n{k:02d}"
            nodes.append(_node("LEAF", de, f"Dead {ss} #{k}"))
            edges.append(_edge(left, de, "links", f"dde-{k}"))
    target_n = 26 + (i % 30)
    _ensure_far_branch(nodes, edges, ss, join)
    _pad_noise(nodes, edges, ss, target_n, join)
    return GraphSpec(
        i, "diamond", hub, nodes, edges, gold, gold_hop=2,
        n_distractor_hubs=0, has_dead_ends=has_de,
        edge_density_note="diamond-medium", expect_walk_perfect=True,
    )


def build_wide_shallow(i: int) -> GraphSpec:
    ss = _ss(i)
    hub = f"hub-{ss}"
    n_child = 6 + (i % 5)  # 6..10 keep M-feasible
    nodes = [_node("HUB", hub, f"Wide hub {ss}")]
    edges: list[EdgeSpec] = []
    kids = []
    for k in range(n_child):
        kind = "DOC" if k % 2 == 0 else "TSK"
        slug = f"{kind.lower()}-{ss}-n{k:02d}"
        kids.append(slug)
        nodes.append(_node(kind, slug, f"Wide child {ss} #{k:02d}"))
        edges.append(_edge(hub, slug, "contains", f"w-{k}"))
    n_gold = 4 + (i % 5)
    gold = [hub] + kids[: n_gold - 1]
    # distractor hub as sibling? attach a DIST hub under a child (hop2)
    n_dh = 1 + (i % 2)
    for k in range(n_dh):
        dh = f"dist-{ss}-h{k}"
        nodes.append(_node("DIST", dh, f"Distractor hub {ss} #{k}"))
        edges.append(_edge(kids[k % len(kids)], dh, "mentions", f"dh-{k}"))
    target_n = 32 + (i % 28)
    _ensure_far_branch(nodes, edges, ss, kids[-1])
    _pad_noise(nodes, edges, ss, target_n, kids[-1])
    # walk may be imperfect if too many kids (>11 non-seed in ball when counting hop2 dist)
    # kids are hop1; with n_child large, still ≤17 nodes at hop1 — if n_child+1+n_dh > 12, truncate
    n_in_ball_est = 1 + n_child + n_dh  # rough
    expect = n_in_ball_est <= 12 or set(gold).issubset(set([hub] + kids[:11]))
    # more carefully: ranked other nodes — DOC before DIST before TSK...
    # Keep expect True when gold are early DOCs
    return GraphSpec(
        i, "wide-shallow", hub, nodes, edges, gold, gold_hop=1,
        n_distractor_hubs=n_dh, has_dead_ends=False,
        edge_density_note="wide-shallow", expect_walk_perfect=True,
        walk_miss_reason=None,
    )


def build_deep_narrow(i: int) -> GraphSpec:
    ss = _ss(i)
    hub = f"hub-{ss}"
    nodes = [_node("HUB", hub, f"Deep root {ss}")]
    edges: list[EdgeSpec] = []
    # depth-2 spine: hub -> mid -> leaf_gold
    mid = f"doc-{ss}-mid"
    leaf = f"tsk-{ss}-leaf"
    nodes += [_node("DOC", mid, f"Mid {ss}"), _node("TSK", leaf, f"Deep leaf {ss}")]
    edges += [_edge(hub, mid, "next", "dn1"), _edge(mid, leaf, "next", "dn2")]
    # sparse side docs at hop1
    sides = []
    for k in range(2 + (i % 3)):
        slug = f"doc-{ss}-side{k}"
        sides.append(slug)
        nodes.append(_node("DOC", slug, f"Side {ss} #{k}"))
        edges.append(_edge(hub, slug, "contains", f"side-{k}"))
    n_gold = 3 + (i % 3)
    gold = [hub, mid, leaf] + sides[: max(0, n_gold - 3)]
    gold = gold[:n_gold]
    has_de = True
    for k in range(1 + (i % 4)):
        de = f"dead-{ss}-n{k:02d}"
        nodes.append(_node("LEAF", de, f"Dead stub {ss} #{k}"))
        edges.append(_edge(sides[k % len(sides)] if sides else mid, de, "links", f"de-{k}"))
    target_n = 24 + (i % 36)
    _ensure_far_branch(nodes, edges, ss, leaf)
    _pad_noise(nodes, edges, ss, target_n, leaf)
    return GraphSpec(
        i, "deep-narrow", hub, nodes, edges, gold, gold_hop=2,
        n_distractor_hubs=0, has_dead_ends=has_de,
        edge_density_note="deep-sparse", expect_walk_perfect=True,
    )


def build_multi_root(i: int) -> GraphSpec:
    ss = _ss(i)
    hub = f"hub-{ss}-legal"
    nodes = [_node("HUB", hub, f"Legal seed {ss}")]
    edges: list[EdgeSpec] = []
    # illegal roots (also HUB kind but different slug — cue targets legal only)
    n_other = 1 + (i % 3)
    for k in range(n_other):
        oh = f"hub-{ss}-other{k}"
        nodes.append(_node("HUB", oh, f"Illegal root {ss} #{k}"))
        # disconnect other roots from legal gold; attach their own trees
        for j in range(3):
            d = f"noise-{ss}-or{k}-{j}"
            nodes.append(_node("NOISE", d, f"Other-tree {ss} {k}.{j}"))
            edges.append(_edge(oh, d, "contains", f"or-{k}-{j}"))
    # legal gold under legal hub
    docs = []
    for k in range(4 + (i % 4)):
        slug = f"doc-{ss}-n{k:02d}"
        docs.append(slug)
        nodes.append(_node("DOC", slug, f"Legal doc {ss} #{k}"))
        edges.append(_edge(hub, slug, "documents", f"ld-{k}"))
    n_gold = 3 + (i % 4)
    gold = [hub] + docs[: n_gold - 1]
    target_n = 34 + (i % 26)
    _ensure_far_branch(nodes, edges, ss, docs[-1])
    _pad_noise(nodes, edges, ss, target_n, docs[-1])
    return GraphSpec(
        i, "multi-root-one-legal-seed", hub, nodes, edges, gold, gold_hop=1,
        n_distractor_hubs=n_other, has_dead_ends=False,
        edge_density_note="multi-root-partitioned", expect_walk_perfect=True,
    )


def build_noisy_sibling_hub(i: int) -> GraphSpec:
    ss = _ss(i)
    hub = f"hub-{ss}"
    sib = f"dist-{ss}-sib"
    nodes = [
        _node("HUB", hub, f"Legal hub {ss}"),
        _node("DIST", sib, f"Sibling distractor {ss}"),
    ]
    edges: list[EdgeSpec] = [_edge(hub, sib, "paired_with", "sib")]
    # gold under legal; noise under sibling
    docs = []
    for k in range(3 + (i % 5)):
        slug = f"doc-{ss}-n{k:02d}"
        docs.append(slug)
        nodes.append(_node("DOC", slug, f"Goldish doc {ss} #{k}"))
        edges.append(_edge(hub, slug, "documents", f"gd-{k}"))
    for k in range(6 + (i % 6)):
        slug = f"noise-{ss}-sib-{k:02d}"
        nodes.append(_node("NOISE", slug, f"Sib noise {ss} #{k}"))
        edges.append(_edge(sib, slug, "links", f"sn-{k}"))
    n_gold = 3 + (i % 4)
    gold = [hub] + docs[: n_gold - 1]
    # sibling noise is within k=2 via sib — can crowd the ball
    expect = True
    miss = None
    target_n = 36 + (i % 24)
    _ensure_far_branch(nodes, edges, ss, docs[-1] if docs else sib)
    # pad attached to far so not all in ball
    _pad_noise(nodes, edges, ss, target_n, sib, dead_end=True)
    return GraphSpec(
        i, "noisy-sibling-hub", hub, nodes, edges, gold, gold_hop=1,
        n_distractor_hubs=1, has_dead_ends=True,
        edge_density_note="sibling-asymmetric", expect_walk_perfect=expect,
        walk_miss_reason=miss,
    )


def build_sparse_evidence(i: int) -> GraphSpec:
    ss = _ss(i)
    hub = f"hub-{ss}"
    nodes = [_node("HUB", hub, f"Sparse hub {ss}")]
    edges: list[EdgeSpec] = []
    # very few edges; gold = hub + 2 docs
    d0 = f"doc-{ss}-a"
    d1 = f"doc-{ss}-b"
    t0 = f"tsk-{ss}-a"
    nodes += [
        _node("DOC", d0, f"Sparse A {ss}"),
        _node("DOC", d1, f"Sparse B {ss}"),
        _node("TSK", t0, f"Sparse task {ss}"),
    ]
    edges += [
        _edge(hub, d0, "documents", "sa"),
        _edge(hub, d1, "documents", "sb"),
        _edge(d0, t0, "mentions", "st"),
    ]
    n_gold = 3 + (i % 2)
    gold = [hub, d0, d1, t0][:n_gold]
    # many disconnected-looking far nodes via long chain
    target_n = 40 + (i % 20)
    _ensure_far_branch(nodes, edges, ss, d1)
    _pad_noise(nodes, edges, ss, target_n, hub, dead_end=True)
    return GraphSpec(
        i, "sparse-evidence", hub, nodes, edges, gold,
        gold_hop=2 if t0 in gold else 1,
        n_distractor_hubs=0, has_dead_ends=True,
        edge_density_note="very-sparse-core", expect_walk_perfect=True,
    )


def build_dense_clique_gold_rim(i: int) -> GraphSpec:
    ss = _ss(i)
    hub = f"hub-{ss}"
    nodes = [_node("HUB", hub, f"Clique rim hub {ss}")]
    edges: list[EdgeSpec] = []
    # dense clique of DIST nodes at hop1
    n_clique = 3 + (i % 2)  # 3..4 keep ball small
    clique = []
    for k in range(n_clique):
        slug = f"dist-{ss}-c{k}"
        clique.append(slug)
        nodes.append(_node("DIST", slug, f"Clique member {ss} #{k}"))
        edges.append(_edge(hub, slug, "contains", f"c-{k}"))
    for a in range(n_clique):
        for b in range(a + 1, n_clique):
            edges.append(_edge(clique[a], clique[b], "paired_with", f"p-{a}-{b}"))
    # gold on rim: DOC/TSK attached to hub, not in clique
    rim = []
    for k in range(3 + (i % 4)):
        kind = "DOC" if k % 2 == 0 else "TSK"
        slug = f"{kind.lower()}-{ss}-rim{k}"
        rim.append(slug)
        nodes.append(_node(kind, slug, f"Rim gold {ss} #{k}"))
        edges.append(_edge(hub, slug, "documents", f"rim-{k}"))
    n_gold = 3 + (i % 5)
    gold = [hub] + rim[: n_gold - 1]
    target_n = 30 + (i % 28)
    _ensure_far_branch(nodes, edges, ss, rim[-1] if rim else clique[-1])
    _pad_noise(nodes, edges, ss, target_n, clique[0])
    # clique + rim may exceed M
    return GraphSpec(
        i, "dense-clique-with-gold-rim", hub, nodes, edges, gold, gold_hop=1,
        n_distractor_hubs=min(3, n_clique), has_dead_ends=False,
        edge_density_note="clique-dense", expect_walk_perfect=True,
        walk_miss_reason=None,
    )


def build_broken_path_repair(i: int) -> GraphSpec:
    ss = _ss(i)
    hub = f"hub-{ss}"
    nodes = [_node("HUB", hub, f"Repair hub {ss}")]
    edges: list[EdgeSpec] = []
    # broken direct: hub -/-> target; repair via mid
    mid = f"doc-{ss}-repair"
    target = f"tsk-{ss}-target"
    decoy = f"doc-{ss}-decoy"
    nodes += [
        _node("DOC", mid, f"Repair mid {ss}"),
        _node("TSK", target, f"Repaired target {ss}"),
        _node("DOC", decoy, f"Decoy stub {ss}"),
    ]
    edges += [
        _edge(hub, mid, "next", "rep1"),
        _edge(mid, target, "next", "rep2"),
        _edge(hub, decoy, "contains", "decoy"),  # dead-ish branch
    ]
    extra = []
    for k in range(2 + (i % 4)):
        slug = f"doc-{ss}-x{k}"
        extra.append(slug)
        nodes.append(_node("DOC", slug, f"Extra {ss} #{k}"))
        edges.append(_edge(hub, slug, "contains", f"x-{k}"))
    n_gold = 3 + (i % 4)
    gold = [hub, mid, target] + extra[: max(0, n_gold - 3)]
    gold = gold[:n_gold]
    has_de = True
    de = f"dead-{ss}-0"
    nodes.append(_node("LEAF", de, f"Dead off decoy {ss}"))
    edges.append(_edge(decoy, de, "links", "de0"))
    target_n = 28 + (i % 30)
    _ensure_far_branch(nodes, edges, ss, decoy)
    _pad_noise(nodes, edges, ss, target_n, decoy)
    return GraphSpec(
        i, "broken-path-then-repair", hub, nodes, edges, gold, gold_hop=2,
        n_distractor_hubs=0, has_dead_ends=has_de,
        edge_density_note="repair-path", expect_walk_perfect=True,
    )


def build_hub_dead_ends(i: int) -> GraphSpec:
    ss = _ss(i)
    hub = f"hub-{ss}"
    nodes = [_node("HUB", hub, f"Dead-end hub {ss}")]
    edges: list[EdgeSpec] = []
    docs = []
    for k in range(5 + (i % 4)):
        slug = f"doc-{ss}-n{k:02d}"
        docs.append(slug)
        nodes.append(_node("DOC", slug, f"Core doc {ss} #{k}"))
        edges.append(_edge(hub, slug, "documents", f"hd-{k}"))
    n_de = 4 + (i % 5)
    for k in range(n_de):
        de = f"dead-{ss}-n{k:02d}"
        nodes.append(_node("LEAF", de, f"Dead branch {ss} #{k}"))
        edges.append(_edge(docs[k % len(docs)], de, "links", f"hde-{k}"))
    n_gold = 3 + (i % 5)
    gold = [hub] + docs[: n_gold - 1]
    target_n = 30 + (i % 28)
    _ensure_far_branch(nodes, edges, ss, docs[-1])
    _pad_noise(nodes, edges, ss, target_n, docs[0])
    return GraphSpec(
        i, "hub-with-dead-ends", hub, nodes, edges, gold, gold_hop=1,
        n_distractor_hubs=0, has_dead_ends=True,
        edge_density_note="dead-end-heavy", expect_walk_perfect=True,
    )


def build_fan_out_fan_in(i: int) -> GraphSpec:
    ss = _ss(i)
    hub = f"hub-{ss}"
    sink = f"tsk-{ss}-sink"
    nodes = [
        _node("HUB", hub, f"Fan hub {ss}"),
        _node("TSK", sink, f"Fan sink {ss}"),
    ]
    edges: list[EdgeSpec] = []
    mids = []
    n_mid = 4 + (i % 5)
    for k in range(n_mid):
        slug = f"doc-{ss}-m{k}"
        mids.append(slug)
        nodes.append(_node("DOC", slug, f"Fan mid {ss} #{k}"))
        edges.append(_edge(hub, slug, "produces", f"fo-{k}"))
        edges.append(_edge(slug, sink, "uses", f"fi-{k}"))
    n_gold = 3 + (i % 5)
    gold = [hub, sink] + mids[: n_gold - 2]
    gold = gold[:n_gold]
    target_n = 28 + (i % 30)
    _ensure_far_branch(nodes, edges, ss, sink)
    _pad_noise(nodes, edges, ss, target_n, sink)
    return GraphSpec(
        i, "fan-out-fan-in", hub, nodes, edges, gold, gold_hop=2,
        n_distractor_hubs=0, has_dead_ends=False,
        edge_density_note="fan-medium", expect_walk_perfect=True,
    )


def build_ladder(i: int) -> GraphSpec:
    ss = _ss(i)
    hub = f"hub-{ss}"
    nodes = [_node("HUB", hub, f"Ladder top {ss}")]
    edges: list[EdgeSpec] = []
    n_rung = 3 + (i % 3)
    left = [hub]
    right = []
    r0 = f"doc-{ss}-r0"
    right.append(r0)
    nodes.append(_node("DOC", r0, f"Ladder R0 {ss}"))
    edges.append(_edge(hub, r0, "links", "r0"))
    for k in range(1, n_rung):
        L = f"doc-{ss}-L{k}"
        R = f"doc-{ss}-R{k}"
        left.append(L)
        right.append(R)
        nodes.append(_node("DOC", L, f"Ladder L{k} {ss}"))
        nodes.append(_node("DOC", R, f"Ladder R{k} {ss}"))
        edges.append(_edge(left[k - 1], L, "next", f"ld-{k}"))
        edges.append(_edge(right[k - 1], R, "next", f"rd-{k}"))
        edges.append(_edge(L, R, "links", f"rung-{k}"))
    n_gold = 3 + (i % 4)
    # gold within k=2 of hub: hub, r0, L1, R1
    candidates = [hub, r0]
    if n_rung > 1:
        candidates += [left[1], right[1]]
    gold = candidates[:n_gold]
    while len(gold) < 3:
        gold.append(r0)
    target_n = 30 + (i % 28)
    _ensure_far_branch(nodes, edges, ss, left[-1])
    _pad_noise(nodes, edges, ss, target_n, left[-1])
    return GraphSpec(
        i, "ladder", hub, nodes, edges, gold, gold_hop=2,
        n_distractor_hubs=0, has_dead_ends=False,
        edge_density_note="ladder", expect_walk_perfect=True,
    )


def build_tree_gold_leaves(i: int) -> GraphSpec:
    ss = _ss(i)
    hub = f"hub-{ss}"
    nodes = [_node("HUB", hub, f"Tree root {ss}")]
    edges: list[EdgeSpec] = []
    mids = []
    for k in range(3 + (i % 3)):
        slug = f"doc-{ss}-m{k}"
        mids.append(slug)
        nodes.append(_node("DOC", slug, f"Tree mid {ss} #{k}"))
        edges.append(_edge(hub, slug, "contains", f"tm-{k}"))
    leaves = []
    for k, mid in enumerate(mids):
        for j in range(1 + (i + k) % 3):
            slug = f"tsk-{ss}-L{k}{j}"
            leaves.append(slug)
            nodes.append(_node("TSK", slug, f"Gold leaf {ss} {k}.{j}"))
            edges.append(_edge(mid, slug, "produces", f"tl-{k}-{j}"))
    n_gold = 3 + (i % 5)
    gold = [hub] + leaves[: n_gold - 1]
    if len(gold) < 3:
        gold = [hub, mids[0], leaves[0] if leaves else mids[0]]
    target_n = 32 + (i % 28)
    _ensure_far_branch(nodes, edges, ss, mids[-1])
    _pad_noise(nodes, edges, ss, target_n, mids[0])
    return GraphSpec(
        i, "tree-with-gold-leaves", hub, nodes, edges, gold, gold_hop=2,
        n_distractor_hubs=0, has_dead_ends=False,
        edge_density_note="tree", expect_walk_perfect=True,
    )


def build_asymmetric_spoke(i: int) -> GraphSpec:
    ss = _ss(i)
    hub = f"hub-{ss}"
    nodes = [_node("HUB", hub, f"Asym hub {ss}")]
    edges: list[EdgeSpec] = []
    # one heavy arm, one light arm
    heavy = []
    for k in range(6 + (i % 5)):
        slug = f"doc-{ss}-hvy{k}"
        heavy.append(slug)
        nodes.append(_node("DOC", slug, f"Heavy arm {ss} #{k}"))
        if k == 0:
            edges.append(_edge(hub, slug, "next", f"hv0"))
        else:
            edges.append(_edge(heavy[k - 1], slug, "next", f"hv{k}"))
    light = f"tsk-{ss}-light"
    nodes.append(_node("TSK", light, f"Light arm {ss}"))
    edges.append(_edge(hub, light, "mentions", "lt"))
    # gold: hub + light + first heavy (within k=2: heavy[0], heavy[1])
    n_gold = 3 + (i % 4)
    gold = [hub, light, heavy[0]]
    if n_gold > 3 and len(heavy) > 1:
        gold.append(heavy[1])
    gold = gold[:n_gold]
    # heavy chain beyond k=2 is dump-only
    target_n = 34 + (i % 26)
    _ensure_far_branch(nodes, edges, ss, heavy[-1])
    _pad_noise(nodes, edges, ss, target_n, heavy[-1])
    return GraphSpec(
        i, "asymmetric-spoke", hub, nodes, edges, gold, gold_hop=2,
        n_distractor_hubs=0, has_dead_ends=False,
        edge_density_note="asymmetric", expect_walk_perfect=True,
    )


def build_cap_bind_stress(i: int) -> GraphSpec:
    """Intentionally walk_imperfect: many hop-1 nodes; late-ranked USR gold."""
    ss = _ss(i)
    hub = f"hub-{ss}"
    nodes = [_node("HUB", hub, f"Cap-stress hub {ss}")]
    edges: list[EdgeSpec] = []
    # Many DOC distractors (rank before USR)
    for k in range(14):
        slug = f"doc-{ss}-fill{k:02d}"
        nodes.append(_node("DOC", slug, f"Fill doc {ss} #{k:02d}"))
        edges.append(_edge(hub, slug, "contains", f"fill-{k}"))
    # Gold includes late USR nodes
    usrs = []
    for k in range(4):
        slug = f"usr-{ss}-g{k}"
        usrs.append(slug)
        nodes.append(_node("USR", slug, f"Gold user {ss} #{k}"))
        edges.append(_edge(hub, slug, "owns", f"ug-{k}"))
    n_gold = 4 + (i % 4)  # 4..7
    gold = [hub] + usrs[: n_gold - 1]
    # ball has 1+14+4 = 19 nodes → M=12 truncates; USR ranks after DOC → miss
    target_n = 40 + (i % 20)
    _ensure_far_branch(nodes, edges, ss, f"doc-{ss}-fill00")
    _pad_noise(nodes, edges, ss, target_n, f"doc-{ss}-fill13")
    return GraphSpec(
        i, "cap-bind-stress", hub, nodes, edges, gold, gold_hop=1,
        n_distractor_hubs=0, has_dead_ends=False,
        edge_density_note="cap-stress-wide", expect_walk_perfect=False,
        walk_miss_reason="cap_binding: 14 DOC fillers rank before USR gold; M=12 truncates gold",
    )


def build_wrong_branch(i: int) -> GraphSpec:
    """Walk may miss: gold on less-preferred branch amid many ranked distractors."""
    ss = _ss(i)
    hub = f"hub-{ss}"
    nodes = [_node("HUB", hub, f"Branch hub {ss}")]
    edges: list[EdgeSpec] = []
    # Preferred-looking DOC branch (fills rank)
    for k in range(12):
        slug = f"doc-{ss}-pref{k:02d}"
        nodes.append(_node("DOC", slug, f"Pref branch {ss} #{k:02d}"))
        edges.append(_edge(hub, slug, "documents", f"pref-{k}"))
    # Gold on USR/TSK "wrong" (late rank) branch at hop 1-2
    bridge = f"bridge-{ss}-g"
    nodes.append(_node("BRIDGE", bridge, f"Gold bridge {ss}"))
    edges.append(_edge(hub, bridge, "links", "altb"))
    gnodes = []
    for k in range(5):
        slug = f"usr-{ss}-alt{k}"
        gnodes.append(slug)
        nodes.append(_node("USR", slug, f"Alt gold {ss} #{k}"))
        edges.append(_edge(bridge, slug, "owns", f"altg-{k}"))
    n_gold = 4 + (i % 3)
    gold = [hub] + gnodes[: n_gold - 1]
    # BRIDGE ranks early alphabetically actually — bridge + some USR may fit
    # With 12 DOC + bridge + hub = 14 already before USR → USR truncated
    target_n = 42 + (i % 18)
    far_via = f"doc-{ss}-pref11"
    _ensure_far_branch(nodes, edges, ss, far_via)
    _pad_noise(nodes, edges, ss, target_n, far_via)
    return GraphSpec(
        i, "wrong-branch-crowding", hub, nodes, edges, gold, gold_hop=2,
        n_distractor_hubs=0, has_dead_ends=False,
        edge_density_note="crowded-alt-branch", expect_walk_perfect=False,
        walk_miss_reason="wrong_branch/cap_binding: preferred DOC arm fills M=12 before alt-branch USR gold",
    )


FAMILIES: list[tuple[str, Callable[[int], GraphSpec]]] = [
    ("star", build_star),
    ("chain-of-hubs", build_chain_of_hubs),
    ("diamond", build_diamond),
    ("wide-shallow", build_wide_shallow),
    ("deep-narrow", build_deep_narrow),
    ("multi-root-one-legal-seed", build_multi_root),
    ("noisy-sibling-hub", build_noisy_sibling_hub),
    ("sparse-evidence", build_sparse_evidence),
    ("dense-clique-with-gold-rim", build_dense_clique_gold_rim),
    ("broken-path-then-repair", build_broken_path_repair),
    ("hub-with-dead-ends", build_hub_dead_ends),
    ("fan-out-fan-in", build_fan_out_fan_in),
    ("ladder", build_ladder),
    ("tree-with-gold-leaves", build_tree_gold_leaves),
    ("asymmetric-spoke", build_asymmetric_spoke),
    ("cap-bind-stress", build_cap_bind_stress),
    ("wrong-branch-crowding", build_wrong_branch),
]

FAMILY_BY_NAME = {n: fn for n, fn in FAMILIES}


def assign_family(session_i: int) -> str:
    """Mostly perfect families; ~30 dedicated walk_imperfect graphs."""
    perfect = [n for n, _ in FAMILIES if n not in (
        "cap-bind-stress", "wrong-branch-crowding"
    )]
    # indices 0..169: round-robin perfect-leaning families (includes wide/clique which usually pass)
    if session_i < 170:
        return perfect[session_i % len(perfect)]
    # 170..199 (30 graphs): dedicated imperfect stratum
    imperfect = ["cap-bind-stress", "wrong-branch-crowding"]
    return imperfect[(session_i - 170) % len(imperfect)]


def build_graph(session_i: int) -> GraphSpec:
    name = assign_family(session_i)
    fn = FAMILY_BY_NAME[name]
    spec = fn(session_i)
    # Clamp n_nodes into 24..60 by padding or (rare) note — builders target this.
    if spec.n_nodes < 24:
        _pad_noise(spec.nodes, spec.edges, _ss(session_i), 24, spec.hub_slug)
    if spec.n_nodes > 60:
        # trim trailing noise nodes/edges
        keep = {n.slug for n in spec.nodes[:60]}
        keep |= set(spec.gold_slugs) | {spec.hub_slug}
        spec.nodes = [n for n in spec.nodes if n.slug in keep][:60]
        keep = {n.slug for n in spec.nodes}
        spec.edges = [e for e in spec.edges if e.src_slug in keep and e.dst_slug in keep]
    # Clamp gold 3..8
    if len(spec.gold_slugs) < 3:
        extras = [n.slug for n in spec.nodes if n.slug not in spec.gold_slugs and n.kind != "NOISE"]
        spec.gold_slugs = list(spec.gold_slugs) + extras[: 3 - len(spec.gold_slugs)]
    if len(spec.gold_slugs) > 8:
        spec.gold_slugs = list(spec.gold_slugs)[:8]
    return spec
