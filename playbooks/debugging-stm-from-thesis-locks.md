# Debugging STM from thesis locks

**Source:** `thesis/analytical-mechanics-of-llm-stm.md` in [llm-stm-mechanics](https://github.com/chouswei/llm-stm-mechanics)  
**Status:** operational debugging checklist derived from locked §13 seams. Pair with [`playbooks/agent-harness-from-thesis-locks.md`](agent-harness-from-thesis-locks.md): harness = how to wire; this = how to triage when a task fails. Not a MemNet SemVer claim. Honesty $c$ / wire leaks are **symptoms**, not version cuts.

Use this when an LLM agent with session memory (MemNet ShapeWalk or any inventory $S$ + working set $W$) fails a task. Do **not** put $m$, $p$, momentum, coverage, $\lambda$, or stickiness on `pin_map` as product fields — analysis / diagnostics only.

---

## 0. First question

Is the failure in **proposal**, **admission**, **eviction**, **integrate** (LLM), or **Commit**?

Force that split **before** tweaking $M$ / window / rankers. Collapsing the three control surfaces plus generate plus inventory write is how you debug the wrong object.

| Surface | Question |
|---------|----------|
| **Proposal** | Was gold in the offer $\tilde{X}$ (ordered observables)? |
| **Admission** | Was gold in the offer but missing from $W$? |
| **Eviction** | Did gold enter $W$ then leave? |
| **Integrate** | $W$ held gold; generate still wrong ($T$, seed, model)? |
| **Commit** | Unexpected $\Delta$ on $S$ (impulse), not a retrieval miss? |

Cue / experimenter $u$ sits **before** proposal. Wrong codebook tokens look like proposal failure until you check harness §2.5.

---

## 1. Decision tree

Work top-down. Stop at the first FAIL that blocks later steps.

### 1. Logs exist? (inspectability)

If proposal / admission / eviction are **not** separately logged → **stop**. Fix logging. You cannot debug collapsed scores.

Fail-able: auditor cannot tell which surface moved → FAIL inspectability. A global ranker may only propose.

### 2. Gauge / identity leak? (gauge / P3, symmetries besides renaming)

Hid, store key, or nickname `id` in ranking features, metric, or offer order?

- Isomorphic rename changes offer or answer → **gauge anomaly** (P3 class). Physical Shape lives in quotient $W/G$; metric (37) is observables-only, order-sensitive.
- Nickname `id` on the `pin_map` wire → honesty-$c$ / wire-leak **symptom** (RAW vs CANONICAL split). Off the wire.
- Sorting by hid to “clean” tests → gauge anomaly, not hygiene.
- Do **not** enlarge $G$ to wash out admission order (order is not a symmetry). Inventory automorphisms that preserve observables are **candidates**, not a license to merge-by-name.

**Fix:** observables-only order; nickname off wire; hid-permutation must leave observable offer unchanged.

### 3. Cap biting? (KKT / $\hat\lambda_M$)

Estimate / account $\hat\lambda_M$ (finite-difference shadow price). Account diagnostic, not a buyable knob.

- Task fails **and** $\hat\lambda_M>0$ → Shape pressing the cap. Relax $M$ / hops **or** rethink Shape.
- Task fails **and** slack ($\hat\lambda_M\approx 0$, gold already fits) → **wrong cue / wrong Shape**, not “buy more $M$”.
- Cap-violation rate under learned policies must be **0** at the engine. Softening hard caps inside Recall is not a debug fix (inspectability).

### 4. Cue / control wrong? (user-input placement)

User input / experimenter $u$: is the cue **codebook tokens**?

Wrong placement (user text dumped as $S$; merge-by-name; collapsed surfaces) — see harness §2.5.

Three legal placements (may stack): cue / control $u$; admitted mass in $W$; discrete impulse $F^\pm$. Not dump-$S$ by default. Log `cue_q` / `control_u` and placement.

A cue-basis change is canonical for control **only if** the observable trajectory law is preserved; else it is a different programme (symmetries besides renaming).

### 5. Admission vs offer mismatch? (three surfaces / update)

- Offer good, $W$ missing gold → **admission** policy (caller did not admit the Shape).
- Offer missing gold → **proposal / cue**, not admission.
- $\tilde{X}_t\subseteq W_t$ only if the **whole** Shape is admitted.

Native update is forced discrete EL on the turn lattice, not “run continuous $R$ on the hard window.” Do not invent a second discrete eviction channel while triaging admission.

### 6. Eviction / stickiness? (measuring $m$, dissipation circularity)

Gold entered then vanished → **eviction** or low stickiness.

- $m$ / $M(W)$ is **analysis** (displacement protocol: intervention needed to knock an item out of $W$ with task and model fixed). Do **not** invent a stickiness field on the wire.
- Critical eviction weights: **preregistered only**. Structural dissipation (bytes, Lev of eviction under metric (37)) is non-circular; task-weighted needs freeze then held-out.
- Do not retune “critical” after seeing which policy won.

### 7. Temperature? (stochasticity)

- $T=0$: drift statements OK (fixed seed for ties).
- $T>0$: object is a **path measure**. Fix $T$ or average seeds / predeclared band.
- Single lucky seed ≠ closure. Onsager–Machlup is a **candidate** for continuous surrogates, not a theorem for categorical token noise — do not “fix stochasticity” by citing OM.

### 8. Markov / hidden state? (Markov, Legendre)

Matched $W$ + $u$ but **divergent futures** → hidden history (tool/caller state, undeclared UI, soft KV, RNG beyond protocol).

- Enlarge $\sigma$ or retract the Markov claim **for that harness**.
- Inventory $S$ unequal with equal $W$ = different manifold, not a Markov fail.
- Engine does not emit $p$. $W$-only is stronger / easier to falsify. If you put $p$ in $\sigma$, name $p_{\mathrm{mech}}$ vs $p_{\mathrm{adj}}$ (Legendre lock); never a `momentum` field on `pin_map`.

Positive control that **should** mismatch (hidden path-label) is required to trust a Markov harness — see §3.

### 9. Commit impulse? (update)

Unexpected inventory change → Commit $\Delta$. STM bug may be **Commit policy**, not retrieval.

Commit is a gated impulse on $S$, not a third retrieval verb. Log `commit?` (observables only).

### 10. Score circularity? (dissipation circularity)

Celebrating $\widehat{\mathcal{A}}$ after same-run fit of critical weights / $a,b,c,d$ → **invalid**. Freeze then held-out.

Do not bake the benchmark into $L$ / $R$ and call it a win.

---

## 2. Symptom → likely surface

| Symptom | Check | Likely surface | Lock cited |
|---------|-------|----------------|------------|
| Cannot tell why $W$ changed | Separate proposal / admission / eviction lines? | Logging (stop) | inspectability |
| Rename / nickname changes offer or answer | Hid / `id` in features or wire; hid-perm | Proposal ranking / wire | gauge/P3; symmetries besides renaming |
| Hid-sort “fixes” tests | Order washed out? | Test hygiene / proposal | metric (37); gauge |
| Task fail, gold truncated, relaxing $M$ helps | $\hat\lambda_M>0$ | Cap / Shape size | KKT / $\hat\lambda_M$ |
| Task fail, gold already fits | Slack; cue codebook | Cue / Shape, not $M$ | user-input; inspectability |
| User text in $S$ without Commit | Placement | Cue vs dump-$S$ | user-input placement |
| Merge-by-name / “the user said X” | Identity-by-name | Commit / find | gauge; symmetries besides renaming |
| Offer has gold; $W$ does not | Admission policy / order | Admission | three surfaces; update |
| Offer lacks gold | Cue tokens vs ranker | Proposal / cue | inspectability; user-input |
| Gold in $W$ then gone | Eviction log; displacement probe | Eviction | measuring $m$; dissipation circularity |
| Invented stickiness / $\lambda$ / $m$ on `pin_map` | Wire fields | Product leak (not a fix) | measuring $m$; Legendre firewall |
| Generate wrong despite gold in $W$ | $T$, seed, model | Integrate | stochasticity |
| Same $W$+$u$, different futures | Hidden tool/UI/KV | $\sigma$ incomplete | Markov; Legendre if claiming $p$ |
| $S$ changed, retrieval looks “wrong” | `commit?` | Commit $\Delta$ | update |
| $\widehat{\mathcal{A}}$ win after fitting $c$ on same run | Freeze date vs eval | Scoring, not STM | dissipation circularity |
| Honesty $c$ / RAW vs CANONICAL split | `id`/`hid` on offer wire | Wire leak symptom | gauge/P3 |

---

## 3. Positive controls (sanity)

- **Hid permutation must not change** the observable offer if the harness is honest (P3 / gauge). FAIL = identity leak.
- **A control that should mismatch** (e.g. hidden path-label in admission) is required for a Markov harness to be valid. If that control also matches, the test cannot see hidden state.
- **Cap-violation rate = 0** under learned policies at the engine. Any bypass → inspectability FAIL, not a ranking tweak.
- **Matched $W$+$u$** (Markov): futures agree within the predeclared band; else enlarge $\sigma$ or retract.
- **Displacement probe for $m$** (optional, analysis): forced removal with task/model fixed. Off-wire; do not ship $M(W)$ on `pin_map`.

---

## 4. What not to do when debugging

- Dump $S$ / `rag_query` as “more memory”
- Soften hard caps inside the engine
- Sort by hid to clean tests
- Collapse three surfaces into one ranker score
- Fit $m$ / critical weights / $a,b,c,d$ on the same run you celebrate
- Put $m$, $p$, momentum, coverage, $\lambda$, stickiness on `pin_map`
- Treat honesty $c$ / wire leaks as a SemVer $a$/$b$ claim
- Identify $p_{\mathrm{mech}}\equiv p_{\mathrm{adj}}$ without the Legendre conditions, then “debug momentum”
- Wash out admission order as if it were gauge
- Merge nodes by nickname because an automorphism *might* exist

---

## 5. Minimal debug log checklist

Start from harness §11. Enough to replay which surface moved and to run gauge / Markov / cap diagnostics.

```
turn_t
  cue_q / control_u          # codebook tokens; user placement: cue / W-span / F±
  proposal: ordered observable ids (+ payloads), caps (k,M,…), rejects
  admission: ordered W ids, policy name
  eviction: removed ids, policy name
  integrate: model, T, seed(s)
  commit?: delta summary (observables only)
  scores?: ell_task, tokens, critical_evictions (if preregistered)
```

**Debug-specific (optional, analysis — not product fields on `pin_map`):**

- $\hat\lambda_M$ account (finite-difference; slack vs biting)
- gauge perm result (hid-isomorph: offer/answer same? RAW vs CANONICAL wire)
- matched-$W$ pair ids (Markov: pair key, next-offer / next-$W$ mismatch)
- cap_violation? (engine reject count; must be 0 under learned $u$)
- displacement probe ids (measuring $m$; off-wire)

Never log hid as a ranking feature. Observable identities only in the metric (37).

---

## 6. Pointers

- Thesis: `thesis/analytical-mechanics-of-llm-stm.md`  
- Pair: [`playbooks/agent-harness-from-thesis-locks.md`](agent-harness-from-thesis-locks.md) (wire); this file (triage)  
- §13 seam locks: metric (37), Markov, Legendre, update, stochasticity, gauge/P3 (chart ≠ theorem), inspectability, dissipation circularity, measuring $m$, symmetries besides renaming, user-input placement (harness §2.5)  
- Empirical: `experiments/` (P1/P2/P3, `markov-w-only/`, `s13-seams/`)
