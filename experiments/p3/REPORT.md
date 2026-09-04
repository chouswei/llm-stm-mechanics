# STM Prediction 3 — rename invariance / gauge anomaly

Cheap half: **before generation**. No LLM generate. No temperature. Exact pin_map / Shape comparison.

**Verdict:** `PASS`

## Claim

Hidden-id permutations produce no change in offered Shapes once *labels* are canonicalised by observable identity. Admission order is PHYSICAL and must NOT be canonicalised away. If hid-sort changes row order (and therefore W), that IS a gauge anomaly.

PASS only if both `label_anomaly` and `order_anomaly` are zero. FAIL if any label_anomaly. FAIL (order) if only order_anomaly.

## memnet-llm version and API actually called

- **memnet-llm:** `0.19.3` (installed from GitHub merge commit, import `memnet`)
- **memnet.__file__:** `/workspace/p3-hid-post147/.venv/lib/python3.13/site-packages/memnet/__init__.py`
- **merge commit:** `eff05dc8a0ad5369e8d7e7f347db30b9300b04d6` (PR #147)
- **observable_rank present:** `True` (exports: `RANK_EXCLUDE_KEYS`, `edge_rank_key`, `node_rank_key`, `observable_payload`, `ranked`, `record_rank_key`)
- **observable_rank module:** `/workspace/p3-hid-post147/.venv/lib/python3.13/site-packages/memnet/observable_rank.py`
- **Binding:** `in-process Python product API (CLI-equivalent; goldfish, no Neo4j)`
- **Operators (count=2):** pin_map (query pin-map), mutate
- **CLI argv:**
  - `memnet session open --map-file`
  - `memnet mutate --stdin`
  - `memnet query pin-map --kind --locator --depth --max-rows`
  - `memnet session close`
- **Python names:** `memnet.session.open_session`, `memnet.mutate_gate.MutateGate.apply`, `memnet.pin_map_composer.PinMapComposer.compose`, `memnet.session.close_session`
- **Not used:** `add`, `rag_query`, `Layer`, `query find`, `query neighbors`
- **Call counts:** `{"open_session": 2020, "MutateGate.apply": 2020, "PinMapComposer.compose": 2020, "close_session": 2020}`

## Protocol parameters

- n_sessions = **20**
- n_perms = **100** (plus one original per session)
- M (hard LIMIT `--max-rows`) = **12** — not raised
- k ( `--depth`) = **2**
- cue tokens: `--kind HUB` + `codebook field locator slug=hub-sXX (unique HUB seed)`
- nodes per session = **16** (HUB + 7 DOC + 4 USR + 4 TSK)
- RNG seed base = `20260903`
- Predeclared equivalence band: **exact match (T=0, no GPU). No wiggle.**

## How hid was permuted

hid is **not** on the pin_map wire.

hid is GraphElement handle (Record.hid, exclude=True, _elN), off pin_map wire. Operational permutation = shuffled CREATE order (allocator new_hid) plus bijection on optional nickname property id. MATCH/cue use observable slug, never hid/id.

Canonicalisation: node: (kind, payload minus id/hid); edge: (src_obs, rel_type, rel_payload minus id/hid, dst_obs). Emitted sequence is NOT sorted.

## Counts

| metric | count |
|---|---|
| n_compare (session × perm) | 2000 |
| label_match | 2000 |
| label_anomaly | 0 |
| order_match | 2000 |
| order_anomaly | 0 |
| build_fail | 0 |
| shapes with `_el` hid leak in pin_map | 0 |

## Pass/fail against the claim

**PASS**

Both label sets and emitted sequences matched exactly on every permutation.

## Concrete example

No anomaly (both counters zero). One orig vs perm match:

- kind: `match`
- session_i=0 perm_i=1
- orig session `mn_31738f81` vs perm session `mn_c28bb3b3`
- cue: `--kind HUB --locator slug=hub-s00`
- orig_n=12 perm_n=12

Original emitted canonical order:

```
(:DOC {slug=doc-s00-n00, title=Document s00 #0})
(:DOC {slug=doc-s00-n01, title=Document s00 #1})
(:DOC {slug=doc-s00-n02, title=Document s00 #2})
(:DOC {slug=doc-s00-n03, title=Document s00 #3})
(:DOC {slug=doc-s00-n04, title=Document s00 #4})
(:DOC {slug=doc-s00-n05, title=Document s00 #5})
(:DOC {slug=doc-s00-n06, title=Document s00 #6})
(:HUB {slug=hub-s00, title=Hub s00 root})
(:TSK {slug=tsk-s00-n00, title=Task s00 #0})
(:TSK {slug=tsk-s00-n01, title=Task s00 #1})
(:TSK {slug=tsk-s00-n02, title=Task s00 #2})
(:TSK {slug=tsk-s00-n03, title=Task s00 #3})
```

Permutation emitted canonical order (not sorted):

```
(:DOC {slug=doc-s00-n00, title=Document s00 #0})
(:DOC {slug=doc-s00-n01, title=Document s00 #1})
(:DOC {slug=doc-s00-n02, title=Document s00 #2})
(:DOC {slug=doc-s00-n03, title=Document s00 #3})
(:DOC {slug=doc-s00-n04, title=Document s00 #4})
(:DOC {slug=doc-s00-n05, title=Document s00 #5})
(:DOC {slug=doc-s00-n06, title=Document s00 #6})
(:HUB {slug=hub-s00, title=Hub s00 root})
(:TSK {slug=tsk-s00-n00, title=Task s00 #0})
(:TSK {slug=tsk-s00-n01, title=Task s00 #1})
(:TSK {slug=tsk-s00-n02, title=Task s00 #2})
(:TSK {slug=tsk-s00-n03, title=Task s00 #3})
```

Original raw pin_map:

```
(:DOC {id: 'nick-doc-s00-n00', slug: 'doc-s00-n00', title: 'Document s00 #0'})
(:DOC {id: 'nick-doc-s00-n01', slug: 'doc-s00-n01', title: 'Document s00 #1'})
(:DOC {id: 'nick-doc-s00-n02', slug: 'doc-s00-n02', title: 'Document s00 #2'})
(:DOC {id: 'nick-doc-s00-n03', slug: 'doc-s00-n03', title: 'Document s00 #3'})
(:DOC {id: 'nick-doc-s00-n04', slug: 'doc-s00-n04', title: 'Document s00 #4'})
(:DOC {id: 'nick-doc-s00-n05', slug: 'doc-s00-n05', title: 'Document s00 #5'})
(:DOC {id: 'nick-doc-s00-n06', slug: 'doc-s00-n06', title: 'Document s00 #6'})
(:HUB {id: 'nick-hub-s00', slug: 'hub-s00', title: 'Hub s00 root'})
(:TSK {id: 'nick-tsk-s00-n00', slug: 'tsk-s00-n00', title: 'Task s00 #0'})
(:TSK {id: 'nick-tsk-s00-n01', slug: 'tsk-s00-n01', title: 'Task s00 #1'})
(:TSK {id: 'nick-tsk-s00-n02', slug: 'tsk-s00-n02', title: 'Task s00 #2'})
(:TSK {id: 'nick-tsk-s00-n03', slug: 'tsk-s00-n03', title: 'Task s00 #3'})
```

Permutation raw pin_map:

```
(:DOC {id: 'nick-doc-s00-n00', slug: 'doc-s00-n00', title: 'Document s00 #0'})
(:DOC {id: 'nick-tsk-s00-n00', slug: 'doc-s00-n01', title: 'Document s00 #1'})
(:DOC {id: 'nick-usr-s00-n01', slug: 'doc-s00-n02', title: 'Document s00 #2'})
(:DOC {id: 'nick-doc-s00-n04', slug: 'doc-s00-n03', title: 'Document s00 #3'})
(:DOC {id: 'nick-usr-s00-n03', slug: 'doc-s00-n04', title: 'Document s00 #4'})
(:DOC {id: 'nick-hub-s00', slug: 'doc-s00-n05', title: 'Document s00 #5'})
(:DOC {id: 'nick-doc-s00-n01', slug: 'doc-s00-n06', title: 'Document s00 #6'})
(:HUB {id: 'nick-tsk-s00-n01', slug: 'hub-s00', title: 'Hub s00 root'})
(:TSK {id: 'nick-doc-s00-n03', slug: 'tsk-s00-n00', title: 'Task s00 #0'})
(:TSK {id: 'nick-doc-s00-n05', slug: 'tsk-s00-n01', title: 'Task s00 #1'})
(:TSK {id: 'nick-tsk-s00-n03', slug: 'tsk-s00-n02', title: 'Task s00 #2'})
(:TSK {id: 'nick-doc-s00-n02', slug: 'tsk-s00-n03', title: 'Task s00 #3'})
```

## Per-session summary

| session | hub slug | orig rows | label_anomaly | order_anomaly | both_match |
|---|---|---|---|---|---|
| 00 | `hub-s00` | 12 | 0 | 0 | 100 |
| 01 | `hub-s01` | 12 | 0 | 0 | 100 |
| 02 | `hub-s02` | 12 | 0 | 0 | 100 |
| 03 | `hub-s03` | 12 | 0 | 0 | 100 |
| 04 | `hub-s04` | 12 | 0 | 0 | 100 |
| 05 | `hub-s05` | 12 | 0 | 0 | 100 |
| 06 | `hub-s06` | 12 | 0 | 0 | 100 |
| 07 | `hub-s07` | 12 | 0 | 0 | 100 |
| 08 | `hub-s08` | 12 | 0 | 0 | 100 |
| 09 | `hub-s09` | 12 | 0 | 0 | 100 |
| 10 | `hub-s10` | 12 | 0 | 0 | 100 |
| 11 | `hub-s11` | 12 | 0 | 0 | 100 |
| 12 | `hub-s12` | 12 | 0 | 0 | 100 |
| 13 | `hub-s13` | 12 | 0 | 0 | 100 |
| 14 | `hub-s14` | 12 | 0 | 0 | 100 |
| 15 | `hub-s15` | 12 | 0 | 0 | 100 |
| 16 | `hub-s16` | 12 | 0 | 0 | 100 |
| 17 | `hub-s17` | 12 | 0 | 0 | 100 |
| 18 | `hub-s18` | 12 | 0 | 0 | 100 |
| 19 | `hub-s19` | 12 | 0 | 0 | 100 |

## Package test `tests/test_pin_map_observable_rank.py`

- present: `True` (fetched from merge commit; not shipped in the wheel)
- path: `/workspace/p3-hid-post147/pkg_tests/test_pin_map_observable_rank.py`
- result: `3 passed` in 2.70s
  - `test_rank_key_excludes_hid_and_nickname_id` PASSED
  - `test_isomorphic_create_shuffle_same_pin_map_sequence` PASSED
  - `test_find_seed_order_follows_observables_not_hid` PASSED

## Comparison to prior pilot (pre-PR #147)

Prior on `pypi memnet-llm==0.19.3 pre-PR#147`: label_match 2000/2000, order_anomaly 2000/2000, verdict `FAIL (order)`.

This re-run (merge `eff05dc8a0ad5369e8d7e7f347db30b9300b04d6`): label_match 2000/2000, order_anomaly 0/2000, verdict `PASS`.

Order anomalies went from 2000/2000 to 0/2000 after ranking by kind + observable payload (excluding hid and nickname id).

## Files written

- schema: `/workspace/p3-hid-post147/schema.txt`
- runner: `/workspace/p3-hid-post147/run_p3.py`
- results: `/workspace/p3-hid-post147/results.json`
- report: `/workspace/p3-hid-post147/REPORT.md`
- venv: `/workspace/p3-hid-post147/.venv`

## How to re-run

```bash
/workspace/p3-hid-post147/.venv/bin/pip install 'git+https://github.com/chouswei/MemNet.git@eff05dc8a0ad5369e8d7e7f347db30b9300b04d6'
/workspace/p3-hid-post147/.venv/bin/python /workspace/p3-hid-post147/run_p3.py
```

In-process only (`MEMNET_TEST_INLINE=1`). Does not clone git, does not merge, does not touch InvenTree / Pi / droplet / live Neo4j.

Elapsed: 607.63 s (UTC run clock; user zone Asia/Taipei).
