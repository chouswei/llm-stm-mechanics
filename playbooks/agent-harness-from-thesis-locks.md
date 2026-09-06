# Agent harness playbook (from STM analytical-mechanics locks)

**Source:** `thesis/analytical-mechanics-of-llm-stm.md` in [llm-stm-mechanics](https://github.com/chouswei/llm-stm-mechanics)  
**Status:** operational checklist derived from locked §13 seams + §6–§10. Not a MemNet SemVer claim.

Use this when wiring an LLM agent that uses session memory (MemNet ShapeWalk or any inventory S + working set W). When a task fails, triage with [`playbooks/debugging-stm-from-thesis-locks.md`](debugging-stm-from-thesis-locks.md) (harness = how to wire; that = how to debug).

---

## 0. One-sentence model

Short-term memory is a **controlled trajectory** of the working set W, not a dump of inventory S. The LLM is the **integrator**. Steering chooses controls. Memory = **manifold + phase point**.

---

## 1. Roles (do not collapse)

| Role | Does | Does not |
|------|------|----------|
| **Integrator (LLM)** | Maps resident W → next tokens / tool calls | Hold S, pick L, invent store keys |
| **Steering (harness / experimenter)** | Chooses cue u, admission, eviction policy | Pretend the model “is” the memory |
| **Memory** | Inventory S (manifold) + phase point (W,p) | Emit p, coverage, λ, m on the wire |

If the same software component picks the next cue, log that as **experimenter**, not as integrator.

---

## 2. Turn loop (native update)

Per turn t:

1. **Cue → control** — map product cue q (codebook tokens) to analysis control u once at the boundary.
2. **Proposal** — offer Shape X̃_t (e.g. MemNet `pin_map`, bounded k, hard LIMIT M).
3. **Admission** — caller builds actual W_t from offer + instructions + dialogue + tools. X̃_t ⊆ W_t only if the whole Shape is admitted.
4. **Integrate** — LLM generates under W_t (drift at T=0; path measure at T>0 — fix T or average seeds).
5. **Eviction** — KV / window policy removes mass from W (discrete dissipative force on the hard window; continuous R is the forgetting *account*, not a second discrete channel).
6. **Commit (optional)** — gated Δ changes inventory S; impulse, not a third retrieval verb.

**Native mechanical update** is forced discrete Euler–Lagrange on the turn lattice, not “run continuous port-Hamiltonian on the hard window.”

---

## 2.5 User input

User input is **steering / experimenter**, not the integrator and not inventory S by default.

Three placements (may stack on one turn):

1. **As cue / control u** — human message (or a product cue derived from it) maps to u_t: what to propose, admit, commit. Same experimenter slot as an agent choosing the next `pin_map` cue. Log under `cue_q` / `control_u`.
2. **As admitted mass in W** — if user text is pasted into the window, it is part of ordered W_t (configuration), same as any other span. Not S unless gated Commit writes it.
3. **As discrete impulse / force** — corrections, user-triggered tool handoffs, “stop/redo” may enter as F± on the turn update without dumping S.

**Not:** a reason to collapse proposal / admission / eviction into one score; not identity-by-name on the graph (“the user said X” ≠ merge nodes by name).

**Log:** user turns → `cue_q` / `control_u`; if text entered the window → also admission (ordered observable / span ids); if Commit → `commit?` line.

**Temperature / Markov:** user text in W is part of measured σ; undeclared UI state (draft buffers, unsent edits) outside W is hidden history (Markov lock).

---

## 3. Three control surfaces (always log separately)

1. **Proposal** — what was offered (X̃, order preserved).
2. **Admission** — what entered W and in what order.
3. **Eviction** — what left W.

A global ranker may **only propose**. Collapsing all three into one opaque score fails the **inspectability** lock.

### Inspectability audit bar (learned argmax_u H_c)

Allowed as **harness / experimenter** work only (doctrine: no learned ranker inside Recall / RelativeSeed).

Required:

1. Emit chosen u (reconstructible from logs).
2. Hard caps stay hard (engine rejects; no soft-cap bypass inside Recall).
3. Rename-invariant features (no `hid` / store key / nickname `id` in ranker features).
4. Separate proposal / admission / eviction logs.
5. Not a MemNet verb; RelativeSeed never absorbs.

Fail-able checks (run when you claim inspectability): hid-feature permutation changes u → FAIL; engine cap-violation rate > 0 → FAIL; auditor cannot tell which surface moved → FAIL.

---

## 4. Gauge / identity (what not to key on)

- **Identity is the graph element**, not a name. Optional `id` is nickname only.
- **Physical Shape** lives in quotient W/G (global discrete rename of hids preserving observables).
- Continuous θ_t naming chart + π_a ≡ 0 is **pedagogy**, not a product theorem.
- **Admission order is physical** — do not sort by hid to “clean” tests.
- Metric on W: ordered sequence of **observable** identities; d = Lev (edit distance). No hid in the metric.

**Harness test:** isomorphic CREATE-order / nickname permutations → same observable offer sequence (P3 class). Fail = gauge anomaly.

---

## 5. Caps and diagnostics

- Window / hop / row / rate caps are **inequalities** → hard reject in the engine.
- λ̂_M (finite-difference shadow price) is an **account diagnostic**, not a buyable product knob.
- Positive λ̂_M when gold is truncated and relaxing M helps; should not fake-positive when gold already fits.

**Debug:** task fails + λ̂_M>0 → Shape pressing the cap. Task fails + slack → wrong cue / wrong Shape, not “buy more M.”

---

## 6. Markov boundary (what to put in state)

- Claim (hypothesis): active process Markov in measured σ given fixed inventory S.
- Intended σ=(W,p); engine does **not** emit p. W-only is stronger / easier to falsify.
- Inventory S is **not** STM state. Unequal S with equal W = different manifold, not a Markov fail.
- Hide nothing that affects the future outside σ: tool/caller bits, undeclared RNG, soft KV mass not in hard W.

**Structural check (already run on MemNet goldfish):** matched ordered W, same next cue, Markov admission → futures match; positive control with hidden path-label must mismatch (harness valid). Does **not** prove soft-KV / dialogue-summary Markovness.

---

## 7. Action / scoring (measurement model)

Operational estimator (conceptual form):

Â_d = Σ_t [ a·d(W_t,W_{t+1})² + b·tokens + c·critical_evictions + d·ℓ_task ]

Rules:

- Preregister a,b,c,d (and any stand-in for d, e.g. d(∅,W)=|W|) **before** held-out outcomes.
- Compare policies at **matched answer quality**, not “dump has more gold so loses.”
- **Critical evictions** = task-weighted stand-in → same preregister / freeze / held-out discipline (no same-run fit).
- Structural dissipation (bytes, Lev of eviction) is non-circular; task-weighted dissipation needs held-out weights.

---

## 8. Temperature

- T=0: drift statements OK (fixed seed for ties).
- T>0: object is a **path measure**; fix T or average seeds / use a predeclared distributional band.
- Onsager–Machlup is a **candidate** for continuous surrogates — not a theorem for categorical token noise. A derivation would be a large-deviation rate for composed offer+admission+sampler, or a discrete-admission $\to$ Langevin+OM limit on chart (7) (§13 stochasticity lock).

---

## 9. Handoff between agents

If a session is SSOT for shared working memory:

- Hand off the **session id** only.
- Peer re-pins via `pin_map` / cue — do **not** ship a graph dump as STM.
- Empty cue outline = census under hard LIMIT, not a neighbourhood dump of edges.

---

## 10. What not to ship (firewalls)

| Ban | Why |
|-----|-----|
| `rag_query` / dump-S as MemNet STM API | Snapshot benches ≠ product dump |
| `momentum` / coverage / λ / m on `pin_map` | Analysis-only |
| Learned ranker inside Recall / RelativeSeed absorb | Doctrine 9 |
| Identity-by-name / silent merge-by-LLM on find | Cue by name OK; merge is a Commit write |
| Softening hard caps inside the engine for “learning” | Caps stay hard |
| Same-run fit of critical-pin weights then celebrating Â | Circularity |

---

## 11. Minimal logging schema (per turn)

```
turn_t
  cue_q / control_u
  proposal: ordered observable ids (+ payloads), caps (k,M,…), rejects
  admission: ordered W ids, policy name
  eviction: removed ids, policy name
  integrate: model, T, seed(s)
  commit?: delta summary (observables only)
  scores?: ell_task, tokens, critical_evictions (if preregistered)
```

Enough to replay which surface moved and to run gauge / Markov / cap diagnostics.

- User input: always `cue_q` / `control_u`; plus admission (ordered observable / span ids) if text entered W; plus `commit?` if Commit wrote S. Record placement (cue / W-span / F±). Never dump-S by default.

---

## 12. Quick self-check (before calling it “done”)

- [ ] Three surfaces logged separately  
- [ ] User input placed as cue / W-span / F± (not dump-S; not collapsed surfaces)  
- [ ] No hid in ranker features or metric  
- [ ] Hard caps hard; λ̂ only as diagnostic  
- [ ] Coeffs / critical checklist frozen before held-out  
- [ ] T fixed or seeds averaged  
- [ ] Handoff = session id, not dump  
- [ ] Learned cue chooser (if any) passes inspectability bar  

---

## Pointers

- Thesis: `thesis/analytical-mechanics-of-llm-stm.md`  
- §13 seam locks: Legendre (+ analysis-only $p$ maps (35)–(36)), update rule (+ discrete Dirac requirements; structure not written), stochasticity (OM candidate / derivation bar), Markov (+ W-only empirical), metric (37), measuring $m$ (off-wire), symmetries besides renaming, inspectability, gauge chart ≠ theorem, dissipation circularity  
- Debug when a task fails: [`playbooks/debugging-stm-from-thesis-locks.md`](debugging-stm-from-thesis-locks.md)  
- Empirical harnesses: `experiments/` (P1/P2/P3, `markov-w-only/`, `s13-seams/`; ShapeWalk vs lexical RAG live driver: `experiments/shapewalk-vs-rag/`)
