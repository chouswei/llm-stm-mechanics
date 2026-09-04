#!/usr/bin/env python3
"""STM Prediction 3 — rename invariance / gauge anomaly (post PR #147 re-run).

Product operators only: session lifecycle + mutate (Commit) + query pin-map (Recall).
No LLM generate, T=0, exact match. Installed from MemNet merge commit eff05dc8
(PR #147: ranking by kind + observable payload, excludes hid and nickname id).
"""

from __future__ import annotations

import json
import os
import random
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

os.environ.setdefault("MEMNET_TEST_INLINE", "1")
os.environ.setdefault("MEMNET_SERVE_INTERNAL", "1")
# No live Neo4j / InvenTree / Pi / droplet.
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

N_SESSIONS = int(__import__('os').environ.get('P3_N_SESSIONS', '20'))
N_PERMS = int(__import__('os').environ.get('P3_N_PERMS', '100'))
K_HOP = 2
M_LIMIT = 12  # hard LIMIT; do not raise to "make it pass"
N_DOC = 7
N_USR = 4
N_TSK = 4
# 1 hub + 7 doc + 4 usr + 4 tsk = 16 nodes (order can move; M=12 bites)

# Codebook cue: kind + locator on unique observable slug (not hid, not nickname).
CUE_KIND = "HUB"
SEED_BASE = 20260903  # frozen

SID_RE = re.compile(r"(mn_[0-9a-f]+)")
PROP_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*:\s*'((?:\\'|[^'])*)'")
NODE_RE = re.compile(r"^\(:([A-Za-z_][A-Za-z0-9_]*)\s*(\{.*\})?\)$")
EDGE_RE = re.compile(
    r"^\(:([A-Za-z_][A-Za-z0-9_]*)\s*(\{.*\})?\)"
    r"-\[:([A-Za-z_][A-Za-z0-9_]*)\s*(\{.*\})?\]->"
    r"\(:([A-Za-z_][A-Za-z0-9_]*)\s*(\{.*\})?\)$"
)
HID_LEAK_RE = re.compile(r"_el\d+")

# Nickname/hid/id are not identity. Strip from canonical labels.
DROP_KEYS = frozenset({"id", "hid"})


def _parse_props(blob: str | None) -> dict[str, str]:
    if not blob:
        return {}
    return {k: v.replace("\\'", "'") for k, v in PROP_RE.findall(blob)}


def _obs_node(kind: str, props: dict[str, str]) -> tuple:
    """Observable identity: kind + payload minus nickname/hid."""
    payload = tuple(sorted((k, v) for k, v in props.items() if k not in DROP_KEYS))
    return ("node", kind, payload)


def _obs_edge(
    src_kind: str,
    src_props: dict[str, str],
    rel: str,
    rel_props: dict[str, str],
    dst_kind: str,
    dst_props: dict[str, str],
) -> tuple:
    src = _obs_node(src_kind, src_props)
    dst = _obs_node(dst_kind, dst_props)
    rprops = tuple(sorted((k, v) for k, v in rel_props.items() if k not in DROP_KEYS))
    return ("edge", src, rel, rprops, dst)


def canonical_row(line: str) -> tuple | None:
    s = line.strip()
    if not s or s.startswith("#") or s.startswith("@"):
        return None
    m = EDGE_RE.match(s)
    if m:
        return _obs_edge(
            m.group(1),
            _parse_props(m.group(2)),
            m.group(3),
            _parse_props(m.group(4)),
            m.group(5),
            _parse_props(m.group(6)),
        )
    m = NODE_RE.match(s)
    if m:
        return _obs_node(m.group(1), _parse_props(m.group(2)))
    return ("raw", s)


def fmt_label(lab: tuple) -> str:
    if lab[0] == "node":
        _, kind, payload = lab
        props = ", ".join(f"{k}={v}" for k, v in payload)
        return f"(:{kind} {{{props}}})"
    if lab[0] == "edge":
        _, src, rel, rprops, dst = lab
        rp = "" if not rprops else " {" + ", ".join(f"{k}={v}" for k, v in rprops) + "}"
        return f"{fmt_label(src)}-[:{rel}{rp}]->{fmt_label(dst)}"
    return str(lab)


@dataclass
class GraphSpec:
    session_i: int
    hub_slug: str
    hub_title: str
    nodes: list[dict]  # kind, slug, title, nick
    edges: list[dict]  # src_slug, dst_slug, rel, note, nick


def build_base_graph(session_i: int) -> GraphSpec:
    ss = f"s{session_i:02d}"
    hub_slug = f"hub-{ss}"
    nodes = [
        {
            "kind": "HUB",
            "slug": hub_slug,
            "title": f"Hub {ss} root",
            "nick": f"nick-{hub_slug}",
        }
    ]
    edges: list[dict] = []
    docs = []
    for i in range(N_DOC):
        slug = f"doc-{ss}-n{i:02d}"
        docs.append(slug)
        nodes.append(
            {
                "kind": "DOC",
                "slug": slug,
                "title": f"Document {ss} #{i}",
                "nick": f"nick-{slug}",
            }
        )
        edges.append(
            {
                "src_slug": slug,
                "dst_slug": hub_slug,
                "rel": "documents",
                "note": f"doc-{i}",
                "nick": f"nick-e-doc-{ss}-{i:02d}",
            }
        )
    for i, a, b in ((i, docs[i], docs[(i + 1) % N_DOC]) for i in range(N_DOC)):
        edges.append(
            {
                "src_slug": a,
                "dst_slug": b,
                "rel": "next",
                "note": f"ring-{i}",
                "nick": f"nick-e-ring-{ss}-{i:02d}",
            }
        )
    for i in range(N_USR):
        slug = f"usr-{ss}-n{i:02d}"
        nodes.append(
            {
                "kind": "USR",
                "slug": slug,
                "title": f"User {ss} #{i}",
                "nick": f"nick-{slug}",
            }
        )
        edges.append(
            {
                "src_slug": slug,
                "dst_slug": docs[i % N_DOC],
                "rel": "owns",
                "note": f"own-{i}",
                "nick": f"nick-e-own-{ss}-{i:02d}",
            }
        )
    for i in range(N_TSK):
        slug = f"tsk-{ss}-n{i:02d}"
        nodes.append(
            {
                "kind": "TSK",
                "slug": slug,
                "title": f"Task {ss} #{i}",
                "nick": f"nick-{slug}",
            }
        )
        edges.append(
            {
                "src_slug": slug,
                "dst_slug": hub_slug,
                "rel": "mentions",
                "note": f"tsk-{i}",
                "nick": f"nick-e-tsk-{ss}-{i:02d}",
            }
        )
    return GraphSpec(
        session_i=session_i,
        hub_slug=hub_slug,
        hub_title=f"Hub {ss} root",
        nodes=nodes,
        edges=edges,
    )


def permute_graph(base: GraphSpec, perm_i: int) -> GraphSpec:
    """Isomorphism: bijection on nicknames + shuffled CREATE order (operational hid perm)."""
    rng = random.Random(SEED_BASE + 10_000 * base.session_i + perm_i)
    nodes = [dict(n) for n in base.nodes]
    edges = [dict(e) for e in base.edges]
    nicks_n = [n["nick"] for n in nodes]
    nicks_e = [e["nick"] for e in edges]
    rng.shuffle(nicks_n)
    rng.shuffle(nicks_e)
    for n, nick in zip(nodes, nicks_n):
        n["nick"] = nick
    for e, nick in zip(edges, nicks_e):
        e["nick"] = nick
    rng.shuffle(nodes)
    rng.shuffle(edges)
    return GraphSpec(
        session_i=base.session_i,
        hub_slug=base.hub_slug,
        hub_title=base.hub_title,
        nodes=nodes,
        edges=edges,
    )


def gql_for(spec: GraphSpec) -> str:
    lines: list[str] = []
    for n in spec.nodes:
        lines.append(
            "CREATE (:{kind} {{id: '{nick}', slug: '{slug}', title: '{title}'}})".format(
                **n
            )
        )
    for e in spec.edges:
        src_kind = next(n["kind"] for n in spec.nodes if n["slug"] == e["src_slug"])
        dst_kind = next(n["kind"] for n in spec.nodes if n["slug"] == e["dst_slug"])
        # MATCH by observable slug, never by hid/nickname.
        lines.append(
            f"MATCH (a:{src_kind} {{slug: '{e['src_slug']}'}}), "
            f"(b:{dst_kind} {{slug: '{e['dst_slug']}'}})"
        )
        lines.append(
            f"CREATE (a)-[:{e['rel']} {{id: '{e['nick']}', note: '{e['note']}'}}]->(b)"
        )
    return "\n".join(lines) + "\n"


class Engine:
    """Product Python API (same functions the CLI wraps)."""

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

    def pin_map(self, ss, hub_slug: str) -> str:
        self.calls["PinMapComposer.compose"] += 1
        _rows, text = PinMapComposer(ss).compose(
            anchor=None,
            kind=CUE_KIND,
            locators=[("slug", hub_slug)],
            depth=K_HOP,
            max_rows=M_LIMIT,
            active_only=True,
            require_anchor=False,
        )
        return text or ""

    def close(self, ss) -> None:
        self.calls["close_session"] += 1
        close_session(ss.session_id)


@dataclass
class Shape:
    sid: str
    raw: str
    lines: list[str]
    labels: list[tuple]
    hid_leak: bool
    exit_code: int
    stderr: str


def capture_shape(eng: Engine, spec: GraphSpec) -> Shape:
    ss = eng.open_session()
    sid = ss.session_id
    try:
        try:
            eng.mutate(ss, gql_for(spec))
        except MemNetError as exc:
            return Shape(
                sid=sid,
                raw="",
                lines=[],
                labels=[],
                hid_leak=False,
                exit_code=1,
                stderr=f"{exc.code}|{exc}",
            )
        try:
            raw = eng.pin_map(ss, spec.hub_slug)
        except MemNetError as exc:
            return Shape(
                sid=sid,
                raw="",
                lines=[],
                labels=[],
                hid_leak=False,
                exit_code=1,
                stderr=f"{exc.code}|{exc}",
            )
        lines = [ln for ln in raw.splitlines() if ln.strip()]
        labels = []
        for ln in lines:
            lab = canonical_row(ln)
            if lab is not None:
                labels.append(lab)
        hid_leak = bool(HID_LEAK_RE.search(raw))
        return Shape(
            sid=sid,
            raw=raw,
            lines=lines,
            labels=labels,
            hid_leak=hid_leak,
            exit_code=0,
            stderr="",
        )
    finally:
        eng.close(ss)


MERGE_COMMIT = "eff05dc8a0ad5369e8d7e7f347db30b9300b04d6"
PRIOR_PILOT = {
    "source": "pypi memnet-llm==0.19.3 pre-PR#147",
    "label_match": 2000,
    "label_anomaly": 0,
    "order_match": 0,
    "order_anomaly": 2000,
    "n_compare": 2000,
    "verdict": "FAIL (order)",
}


def _observable_rank_present() -> dict:
    info: dict = {"module_importable": False, "module_file": None, "exports": [], "error": None}
    try:
        import memnet.observable_rank as orank
        info["module_importable"] = True
        info["module_file"] = getattr(orank, "__file__", None)
        info["exports"] = sorted(
            n for n in dir(orank) if n in {
                "node_rank_key", "edge_rank_key", "record_rank_key",
                "observable_payload", "ranked", "RANK_EXCLUDE_KEYS",
            }
        )
    except Exception as exc:  # noqa: BLE001
        info["error"] = f"{type(exc).__name__}: {exc}"
    return info


def main() -> int:
    t0 = time.time()
    import memnet as _memnet_pkg
    memnet_file = getattr(_memnet_pkg, "__file__", None)
    obs_rank = _observable_rank_present()
    print(f"memnet version={MEMNET_VERSION} file={memnet_file}")
    print(f"observable_rank present={obs_rank['module_importable']} exports={obs_rank['exports']}")
    print(f"merge_commit={MERGE_COMMIT}")
    eng = Engine()
    label_match = 0
    label_anomaly = 0
    order_match = 0
    order_anomaly = 0
    build_fail = 0
    hid_leaks = 0
    examples: list[dict] = []
    match_examples: list[dict] = []
    per_session: list[dict] = []

    for s in range(N_SESSIONS):
        base = build_base_graph(s)
        orig = capture_shape(eng, base)
        if orig.exit_code != 0 or not orig.labels:
            build_fail += 1
            per_session.append(
                {
                    "session_i": s,
                    "hub_slug": base.hub_slug,
                    "orig_sid": orig.sid,
                    "orig_fail": orig.stderr[-500:],
                    "orig_n_labels": len(orig.labels),
                }
            )
            print(f"session {s:02d} ORIG FAIL exit={orig.exit_code} labels={len(orig.labels)}")
            continue
        if orig.hid_leak:
            hid_leaks += 1
        s_label_a = 0
        s_order_a = 0
        s_ok = 0
        for p in range(N_PERMS):
            perm = permute_graph(base, p + 1)
            got = capture_shape(eng, perm)
            if got.exit_code != 0:
                build_fail += 1
                label_anomaly += 1
                order_anomaly += 1
                s_label_a += 1
                s_order_a += 1
                if len(examples) < 5:
                    examples.append(
                        {
                            "kind": "build_fail",
                            "session_i": s,
                            "perm_i": p + 1,
                            "orig_sid": orig.sid,
                            "perm_sid": got.sid,
                            "stderr": got.stderr[-800:],
                        }
                    )
                continue
            if got.hid_leak:
                hid_leaks += 1
            set_o = set(orig.labels)
            set_p = set(got.labels)
            lab_ok = set_o == set_p
            ord_ok = orig.labels == got.labels
            if lab_ok:
                label_match += 1
            else:
                label_anomaly += 1
                s_label_a += 1
            if ord_ok:
                order_match += 1
            else:
                order_anomaly += 1
                s_order_a += 1
            if lab_ok and ord_ok:
                s_ok += 1
                if len(match_examples) < 2:
                    match_examples.append(
                        {
                            "kind": "match",
                            "session_i": s,
                            "perm_i": p + 1,
                            "orig_sid": orig.sid,
                            "perm_sid": got.sid,
                            "hub_slug": base.hub_slug,
                            "cue": f"--kind {CUE_KIND} --locator slug={base.hub_slug}",
                            "orig_n": len(orig.labels),
                            "perm_n": len(got.labels),
                            "orig_canonical_order": [fmt_label(x) for x in orig.labels],
                            "perm_canonical_order": [fmt_label(x) for x in got.labels],
                            "orig_raw": orig.raw,
                            "perm_raw": got.raw,
                        }
                    )
            if (not lab_ok or not ord_ok) and len(examples) < 5:
                only_o = sorted(fmt_label(x) for x in (set_o - set_p))
                only_p = sorted(fmt_label(x) for x in (set_p - set_o))
                examples.append(
                    {
                        "kind": (
                            "label_and_order"
                            if (not lab_ok and not ord_ok)
                            else ("label_only" if not lab_ok else "order_only")
                        ),
                        "session_i": s,
                        "perm_i": p + 1,
                        "orig_sid": orig.sid,
                        "perm_sid": got.sid,
                        "hub_slug": base.hub_slug,
                        "cue": f"--kind {CUE_KIND} --locator slug={base.hub_slug}",
                        "orig_n": len(orig.labels),
                        "perm_n": len(got.labels),
                        "orig_canonical_order": [fmt_label(x) for x in orig.labels],
                        "perm_canonical_order": [fmt_label(x) for x in got.labels],
                        "only_in_orig": only_o,
                        "only_in_perm": only_p,
                        "orig_raw": orig.raw,
                        "perm_raw": got.raw,
                        "orig_hid_leak": orig.hid_leak,
                        "perm_hid_leak": got.hid_leak,
                    }
                )
        per_session.append(
            {
                "session_i": s,
                "hub_slug": base.hub_slug,
                "orig_sid": orig.sid,
                "orig_n_labels": len(orig.labels),
                "orig_hid_leak": orig.hid_leak,
                "n_perms": N_PERMS,
                "label_anomaly": s_label_a,
                "order_anomaly": s_order_a,
                "both_match": s_ok,
            }
        )
        elapsed = time.time() - t0
        print(
            f"session {s:02d} orig_rows={len(orig.labels)} "
            f"label_a={s_label_a} order_a={s_order_a} both_match={s_ok} "
            f"elapsed={elapsed:.1f}s",
            flush=True,
        )

    n_compare = label_match + label_anomaly
    verdict = "PASS" if (label_anomaly == 0 and order_anomaly == 0) else (
        "FAIL" if label_anomaly else "FAIL (order)"
    )
    # FAIL if any label_anomaly; FAIL (order) if only order_anomaly; PASS only if both zero.
    if label_anomaly:
        verdict = "FAIL"
    elif order_anomaly:
        verdict = "FAIL (order)"
    else:
        verdict = "PASS"

    results = {
        "memnet_llm_version": MEMNET_VERSION,
        "memnet_file": memnet_file,
        "merge_commit": MERGE_COMMIT,
        "pr": 147,
        "observable_rank": obs_rank,
        "prior_pilot": PRIOR_PILOT,
        "api": {
            "binding": "in-process Python product API (CLI-equivalent; goldfish, no Neo4j)",
            "cli": [
                "session open --map-file",
                "mutate --stdin",
                "query pin-map --kind --locator --depth --max-rows",
                "session close",
            ],
            "python_names": [
                "memnet.session.open_session",
                "memnet.mutate_gate.MutateGate.apply",
                "memnet.pin_map_composer.PinMapComposer.compose",
                "memnet.session.close_session",
            ],
            "operator_count": 2,
            "operators": ["pin_map (query pin-map)", "mutate"],
            "not_used": ["add", "rag_query", "Layer", "query find", "query neighbors"],
            "call_counts": eng.calls,
        },
        "protocol": {
            "n_sessions": N_SESSIONS,
            "n_perms": N_PERMS,
            "M": M_LIMIT,
            "k": K_HOP,
            "cue_kind": CUE_KIND,
            "cue_tokens": "codebook field locator slug=hub-sXX (unique HUB seed)",
            "n_nodes": 1 + N_DOC + N_USR + N_TSK,
            "n_doc": N_DOC,
            "n_usr": N_USR,
            "n_tsk": N_TSK,
            "seed": SEED_BASE,
            "temperature": 0,
            "gpu": False,
            "equivalence_band": "exact match (T=0, no GPU). No wiggle.",
            "hid_on_wire": False,
            "isomorphism": (
                "hid is GraphElement handle (Record.hid, exclude=True, _elN), "
                "off pin_map wire. Operational permutation = shuffled CREATE order "
                "(allocator new_hid) plus bijection on optional nickname property id. "
                "MATCH/cue use observable slug, never hid/id."
            ),
            "canonicalisation": (
                "node: (kind, payload minus id/hid); "
                "edge: (src_obs, rel_type, rel_payload minus id/hid, dst_obs). "
                "Emitted sequence is NOT sorted."
            ),
        },
        "counts": {
            "n_compare": n_compare,
            "label_match": label_match,
            "label_anomaly": label_anomaly,
            "order_match": order_match,
            "order_anomaly": order_anomaly,
            "build_fail": build_fail,
            "hid_leak_shapes": hid_leaks,
        },
        "verdict": verdict,
        "per_session": per_session,
        "examples": examples,
        "match_examples": match_examples,
        "elapsed_s": round(time.time() - t0, 3),
        "files": {
            "schema": str(SCHEMA_PATH),
            "runner": str(HERE / "run_p3.py"),
            "results": str(RESULTS_PATH),
            "report": str(REPORT_PATH),
        },
    }
    RESULTS_PATH.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    write_report(results)
    print(json.dumps({"verdict": verdict, "counts": results["counts"]}, indent=2))
    return 0 if verdict == "PASS" else 1


def write_report(r: dict) -> None:
    c = r["counts"]
    p = r["protocol"]
    api = r["api"]
    ex = r["examples"]
    lines: list[str] = []
    lines.append("# STM Prediction 3 — rename invariance / gauge anomaly")
    lines.append("")
    lines.append("Cheap half: **before generation**. No LLM generate. No temperature. Exact pin_map / Shape comparison.")
    lines.append("")
    lines.append(f"**Verdict:** `{r['verdict']}`")
    lines.append("")
    lines.append("## Claim")
    lines.append("")
    lines.append(
        "Hidden-id permutations produce no change in offered Shapes once *labels* are "
        "canonicalised by observable identity. Admission order is PHYSICAL and must NOT "
        "be canonicalised away. If hid-sort changes row order (and therefore W), that IS "
        "a gauge anomaly."
    )
    lines.append("")
    lines.append("PASS only if both `label_anomaly` and `order_anomaly` are zero. "
                 "FAIL if any label_anomaly. FAIL (order) if only order_anomaly.")
    lines.append("")
    lines.append("## memnet-llm version and API actually called")
    lines.append("")
    lines.append(f"- **memnet-llm:** `{r['memnet_llm_version']}` (installed from GitHub merge commit, import `memnet`)")
    lines.append(f"- **memnet.__file__:** `{r.get('memnet_file')}`")
    lines.append(f"- **merge commit:** `{r.get('merge_commit')}` (PR #{r.get('pr')})")
    orinfo = r.get('observable_rank') or {}
    lines.append(
        f"- **observable_rank present:** `{orinfo.get('module_importable')}` "
        f"(exports: {', '.join('`' + x + '`' for x in (orinfo.get('exports') or []))})"
    )
    if orinfo.get('module_file'):
        lines.append(f"- **observable_rank module:** `{orinfo.get('module_file')}`")
    lines.append(f"- **Binding:** `{api['binding']}`")
    lines.append(f"- **Operators (count=2):** {', '.join(api['operators'])}")
    lines.append("- **CLI argv:**")
    for x in api["cli"]:
        lines.append(f"  - `memnet {x}`")
    lines.append("- **Python names:** " + ", ".join(f"`{x}`" for x in api["python_names"]))
    lines.append("- **Not used:** " + ", ".join(f"`{x}`" for x in api["not_used"]))
    lines.append(f"- **Call counts:** `{json.dumps(api['call_counts'])}`")
    lines.append("")
    lines.append("## Protocol parameters")
    lines.append("")
    lines.append(f"- n_sessions = **{p['n_sessions']}**")
    lines.append(f"- n_perms = **{p['n_perms']}** (plus one original per session)")
    lines.append(f"- M (hard LIMIT `--max-rows`) = **{p['M']}** — not raised")
    lines.append(f"- k ( `--depth`) = **{p['k']}**")
    lines.append(f"- cue tokens: `--kind {p['cue_kind']}` + `{p['cue_tokens']}`")
    lines.append(f"- nodes per session = **{p['n_nodes']}** (HUB + {p['n_doc']} DOC + {p['n_usr']} USR + {p['n_tsk']} TSK)")
    lines.append(f"- RNG seed base = `{p['seed']}`")
    lines.append(f"- Predeclared equivalence band: **{p['equivalence_band']}**")
    lines.append("")
    lines.append("## How hid was permuted")
    lines.append("")
    lines.append(p["hid_on_wire"] and "hid was on the wire." or "hid is **not** on the pin_map wire.")
    lines.append("")
    lines.append(p["isomorphism"])
    lines.append("")
    lines.append("Canonicalisation: " + p["canonicalisation"])
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    lines.append("| metric | count |")
    lines.append("|---|---|")
    lines.append(f"| n_compare (session × perm) | {c['n_compare']} |")
    lines.append(f"| label_match | {c['label_match']} |")
    lines.append(f"| label_anomaly | {c['label_anomaly']} |")
    lines.append(f"| order_match | {c['order_match']} |")
    lines.append(f"| order_anomaly | {c['order_anomaly']} |")
    lines.append(f"| build_fail | {c['build_fail']} |")
    lines.append(f"| shapes with `_el` hid leak in pin_map | {c['hid_leak_shapes']} |")
    lines.append("")
    lines.append("## Pass/fail against the claim")
    lines.append("")
    lines.append(f"**{r['verdict']}**")
    lines.append("")
    if c["label_anomaly"]:
        lines.append(
            "Label sets of canonical observables differed under isomorphic hid/nickname "
            "permutations. That is a gauge anomaly: the offered Shape depends on hidden "
            "names (or on hid-ordered truncation under hard LIMIT M)."
        )
    elif c["order_anomaly"]:
        lines.append(
            "Canonical label *sets* matched, but emitted *sequences* did not. Admission "
            "order is physical (Lost in the Middle). hid-sort changing row order is a "
            "gauge anomaly per the paper."
        )
    else:
        lines.append(
            "Both label sets and emitted sequences matched exactly on every permutation."
        )
    lines.append("")
    lines.append("## Concrete example")
    lines.append("")
    match_ex = r.get("match_examples") or []
    e = None
    if not ex and match_ex:
        lines.append("No anomaly (both counters zero). One orig vs perm match:")
        lines.append("")
        e = match_ex[0]
    elif not ex:
        lines.append("No anomaly example (both counters zero).")
    else:
        e = ex[0]
    if e is not None:
        lines.append(f"- kind: `{e.get('kind')}`")
        lines.append(f"- session_i={e.get('session_i')} perm_i={e.get('perm_i')}")
        lines.append(f"- orig session `{e.get('orig_sid')}` vs perm session `{e.get('perm_sid')}`")
        lines.append(f"- cue: `{e.get('cue')}`")
        lines.append(f"- orig_n={e.get('orig_n')} perm_n={e.get('perm_n')}")
        if e.get("only_in_orig") or e.get("only_in_perm"):
            lines.append("- set difference (canonical labels):")
            lines.append("  - only_in_orig:")
            for x in (e.get("only_in_orig") or [])[:12]:
                lines.append(f"    - `{x}`")
            lines.append("  - only_in_perm:")
            for x in (e.get("only_in_perm") or [])[:12]:
                lines.append(f"    - `{x}`")
        lines.append("")
        lines.append("Original emitted canonical order:")
        lines.append("")
        lines.append("```")
        for x in (e.get("orig_canonical_order") or []):
            lines.append(x)
        lines.append("```")
        lines.append("")
        lines.append("Permutation emitted canonical order (not sorted):")
        lines.append("")
        lines.append("```")
        for x in (e.get("perm_canonical_order") or []):
            lines.append(x)
        lines.append("```")
        lines.append("")
        lines.append("Original raw pin_map:")
        lines.append("")
        lines.append("```")
        lines.append((e.get("orig_raw") or "").rstrip())
        lines.append("```")
        lines.append("")
        lines.append("Permutation raw pin_map:")
        lines.append("")
        lines.append("```")
        lines.append((e.get("perm_raw") or "").rstrip())
        lines.append("```")
        if e.get("kind") == "build_fail":
            lines.append("")
            lines.append("Build/mutate/pin_map failure stderr:")
            lines.append("```")
            lines.append(e.get("stderr") or "")
            lines.append("```")
    lines.append("")
    lines.append("## Per-session summary")
    lines.append("")
    lines.append("| session | hub slug | orig rows | label_anomaly | order_anomaly | both_match |")
    lines.append("|---|---|---|---|---|---|")
    for s in r["per_session"]:
        lines.append(
            f"| {s['session_i']:02d} | `{s.get('hub_slug','')}` | {s.get('orig_n_labels')} | "
            f"{s.get('label_anomaly', 'FAIL')} | {s.get('order_anomaly', 'FAIL')} | {s.get('both_match', 0)} |"
        )
    lines.append("")
    prior = r.get("prior_pilot") or {}
    lines.append("## Comparison to prior pilot (pre-PR #147)")
    lines.append("")
    lines.append(
        f"Prior on `{prior.get('source')}`: "
        f"label_match {prior.get('label_match')}/{prior.get('n_compare')}, "
        f"order_anomaly {prior.get('order_anomaly')}/{prior.get('n_compare')}, "
        f"verdict `{prior.get('verdict')}`."
    )
    lines.append("")
    lines.append(
        f"This re-run (merge `{r.get('merge_commit')}`): "
        f"label_match {c['label_match']}/{c['n_compare']}, "
        f"order_anomaly {c['order_anomaly']}/{c['n_compare']}, "
        f"verdict `{r['verdict']}`."
    )
    lines.append("")
    if c["order_anomaly"] == 0 and c["label_anomaly"] == 0 and prior.get("order_anomaly"):
        lines.append(
            "Order anomalies went from 2000/2000 to 0/2000 after ranking by kind + "
            "observable payload (excluding hid and nickname id)."
        )
    lines.append("")
    if r.get("package_test"):
        pt = r["package_test"]
        lines.append("## Package test `tests/test_pin_map_observable_rank.py`")
        lines.append("")
        lines.append(f"- present: `{pt.get('present')}`")
        lines.append(f"- result: `{pt.get('result')}`")
        if pt.get("detail"):
            lines.append("")
            lines.append("```")
            lines.append(pt["detail"].rstrip())
            lines.append("```")
        lines.append("")
    lines.append("## Files written")
    lines.append("")
    for k, v in r["files"].items():
        lines.append(f"- {k}: `{v}`")
    lines.append(f"- venv: `{HERE / '.venv'}`")
    lines.append("")
    lines.append("## How to re-run")
    lines.append("")
    lines.append("```bash")
    lines.append(
        f"{HERE / '.venv' / 'bin' / 'pip'} install "
        f"'git+https://github.com/chouswei/MemNet.git@{MERGE_COMMIT}'"
    )
    lines.append(f"{HERE / '.venv' / 'bin' / 'python'} {HERE / 'run_p3.py'}")
    lines.append("```")
    lines.append("")
    lines.append("In-process only (`MEMNET_TEST_INLINE=1`). Does not clone git, does not merge, "
                 "does not touch InvenTree / Pi / droplet / live Neo4j.")
    lines.append("")
    lines.append(f"Elapsed: {r['elapsed_s']} s (UTC run clock; user zone Asia/Taipei).")
    lines.append("")
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
