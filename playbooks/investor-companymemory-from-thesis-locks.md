# Investor CompanyMemory surface map (from STM analytical-mechanics locks)

**Source:** `thesis/analytical-mechanics-of-llm-stm.md` in [llm-stm-mechanics](https://github.com/chouswei/llm-stm-mechanics)  
**Desk SSOT:** `docs/memnet-role.md` in [modelbasedPrj-ai-investor](https://github.com/chouswei/modelbasedPrj-ai-investor) — **ONE LINE:** MemNet owns the session; Neo4j owns the disk. Desk CompanyMemory is **not** on Bolt in this cut.  
**Status:** applications / surface map. Pair with [`playbooks/agent-harness-from-thesis-locks.md`](agent-harness-from-thesis-locks.md) (wire) and [`playbooks/debugging-stm-from-thesis-locks.md`](debugging-stm-from-thesis-locks.md) (triage). Not a MemNet SemVer claim. Not a desk code change. Inves owns the desk; this map lives in the thesis repo.

Use this when mapping STM locks onto **AI Investor CompanyMemory** (desk product). Do **not** invent desk APIs beyond `docs/memnet-role.md` and the locked facts below.

---

## 0. One-sentence model

Short-term memory is a **controlled trajectory** of admitted $W$ in analyse/chat, not a dump of the company session graph. The LLM **integrates** admitted $W$. CompanyMemory + harness **steer**. $S$ is the **company session inventory** (`COM_*`), not MemNet’s product identity and not Neo4j.

---

## 1. Roles (do not collapse)

Harness §1 still holds: LLM integrates admitted $W$; CompanyMemory + harness steer; $S$ is company-session inventory.

| Role | Is | Is not |
|------|----|--------|
| **CompanyMemory** | Desk **part**; company analytical memory **SSOT**; **client** of MemNet; one in-process company session per company (`companySessionId` / `COM_*`); Role D | MemNet product identity; Neo4j / Bolt in this cut; user `PersistentStore`; OHLCV |
| **EvidenceCentre Library** | Separate `evidenceSessionId`; Cataloguer writes Library **only** | Company session; fill-time CompanyMemory Commit |
| **OpenClaw** | InvestorApi only; claim ack carries `sessionId` + `companySessionId`; **pin_map-only** on company sessions | Bolt speaker; Library writer that `pin_map`s on the fill write path; EvidenceCentre client |
| **Integrator (LLM)** | Maps resident $W$ → memo / chat / tool calls | Hold $S$; pick $L$; invent store keys; merge-by-name |
| **Steering** | CompanyMemory + Host/AnalysisEngine choose cue, admission, eviction, gated Commit | Pretend the model “is” CompanyMemory |

Fill **MUST NOT** write the company session. Next **全日分析** hydrates CompanyMemory from Library (later Commit/hydrate — do not collapse Library write with company Commit).

NewsIngest / AnalysisEngine talk to CompanyMemory via existing `MemoryWrite` / `CompanySlice` ports (do not invent extra faces). Leftover `POST /api/crew/memory` is leftover, **not** a MemNet face.

---

## 2. Dictionary (thesis → desk)

| Thesis | Desk |
|--------|------|
| $S$ (inventory / manifold) | Company MemNet session graph for `COM_*` (+ snapshots). **NOT** user PersistentStore. **NOT** OHLCV. **NOT** Evidence Library session. |
| $W$ (working set) | Admitted `pin_map` Shape into analyse/chat context |
| $u$ / cue | RelativeSeed cue: typically anchor `COM_{ticker}_{exchange}`, codebook locators; depth / max_rows caps |
| Commit($\Delta$) | CompanyMemory gated GQL mutate (`CREATE` / `MERGE` / `MATCH…SET`). Leftover CLI `add` is **not** product Commit |
| Proposal | `pin_map` offer (shaped). Honesty $c$: nickname `id` **off wire** on 0.19.4; MemNet **0.19.5** `SHAPE_DROP_KEYS` drops `hid` / `_memnet_hid` / `elementId` on shaped emit. MemNet **MUST** highlight truncation on the wire when Shape is clipped; a truncation signal (or capped rows) means the extract is **incomplete** |
| Admission | What Host / AnalysisEngine actually pastes into the LLM window |
| Eviction | Caps / recycle / news keep caps (`AI_INVESTOR_MEMNET_KEEP_ENTS` etc.). Analysis of stickiness $m$ stays **off wire** |
| $F^\pm$ | Mission claim / Wanted hydrate / user chat corrections as **discrete impulses** — not dump-$S$ |
| Handoff | Deliver `companySessionId` (and mission session id where applicable); peer re-pins. Do **not** ship a graph dump |

Wire is **GQL**, not GraphQL. Layer-style hops may appear on **display**; mutate from CompanyMemory is GQL only.

---

## 3. Turn loop on 全日分析 (sketch)

Native update remains harness §2 (forced discrete EL on the turn lattice). Desk sketch:

1. **Cue → control** — instrument → `COM_*` anchor + `pin_map` params (depth / max_rows / who+bind).
2. **Proposal** — `pin_map` Shape from the **company** session (not Library, not cabinet dump).
3. **Admission** — merge Shape with fresh bars / news into $W$ for AnalysisEngine. $\tilde{X}\subseteq W$ only if the whole Shape is admitted.
4. **Integrate** — checklist / memo generate (Roles C + D as in `memnet-role.md`).
5. **Eviction** — window / keep caps (not a second retrieval verb; not “run continuous $R$ on the hard window”).
6. **Commit (optional)** — write findings / `FND` / `ENT` back via **CompanyMemory GQL only**. Impulse on $S$, not a third retrieval verb.

**Intra-tick:** Host may re-enter CompanyMemory after MemoryWrite so the next turn sees residue. That is still Commit then re-pin — not dump-$S$.

---

## 4. User / OpenClaw input (harness §2.5)

User input is **steering / experimenter**, not the integrator and not inventory $S$ by default.

Three legal placements (may stack):

1. **Cue / control $u$** — chat or mission text maps to what to propose / admit / commit (e.g. which `COM_*` to pin).
2. **Admitted mass in $W$** — pasted into analyse/chat window. Not $S$ unless gated CompanyMemory Commit writes it.
3. **Discrete impulse $F^\pm$** — mission claim, Wanted hydrate on 全日分析, user chat corrections. Not dump-$S$.

**Locked splits:**

- User chat / mission text → cue **or** admitted $W$ **or** $F^\pm$ — **not** automatic inventory.
- Wanted fill result → **Library only**. Hydration into CompanyMemory is a later Commit/hydrate step on 全日分析. Do **not** collapse Library write with company Commit.
- Fill **MUST NOT** `pin_map` on the fill write path as a Library writer.
- OpenClaw: InvestorApi only; claim ack carries `sessionId` + `companySessionId`; pin_map-only on **company** sessions; **MUST NOT** Bolt.
- “The user said $X$” ≠ merge nodes by name (identity is the graph element; nickname `id` is not merge key).

---

## 5. Firewalls

| Ban | Why |
|-----|-----|
| `rag_query` / dump-$S$ as STM API | Snapshot benches ≠ product dump; Host search stays outside MemNet |
| Layer mutate from CompanyMemory | GQL only (`CREATE` / `MERGE` / `MATCH…SET`); leftover CLI `add` ≠ Commit |
| Hid / nickname in ranking | Observables on wire; honesty $c$ / nickname `id` off wire on 0.19.4; **0.19.5** `SHAPE_DROP_KEYS` (`hid` / `_memnet_hid` / `elementId` dropped on shaped emit) |
| $m$ / $p$ / $\lambda$ / momentum on `pin_map` | Analysis-only (measuring $m$; Legendre) |
| Desk speaking Bolt; `liveNeo4jClaimed` true for CompanyMemory | MemNet = session; Neo4j = disk; **this cut does not put CompanyMemory on Neo4j** |
| Merge company session with Evidence Library session | Distinct `companySessionId` vs `evidenceSessionId` |
| Collapsed proposal / admission / eviction logs | Inspectability: three surfaces logged separately when debugging analyse misses |
| Federate MemNet over Desk REST / GraphQL as MemNet | Wire is GQL; leftover crew memory POST is not a face |
| Soften keep / row caps inside the engine “to remember more” | Caps stay hard; $\hat\lambda\_M$ is diagnostic |
| Hard-truncate a CompanyMemory extract so `FND` / checklist / fundamentals drop; call that window “complete” | Silent truncation of load-bearing kinds is a **harness bug**. Prefer **filter-out** (e.g. drop news) or **uncapped / high enough** `max_rows`. Honour the wire truncation highlight. Hard engine caps stay hard — fix cue / filter / scope, not soft $M$ |
| Paint “complete FND census” when `pin_map` signals truncation or rows were capped | Truncated Shape is **incomplete**. Re-cue / filter-out or raise compose $M$ / uncap and **re-pin**. Caps stay hard |

**MUST (CompanyMemory / company-session extracts).** Do **not** set `max_rows` (or any other compose window) so the offer can omit `FND`, checklist, or fundamentals. Prefer filter-out of non-load-bearing kinds (news is the usual drop) **or** an uncapped / high enough row budget that still holds those kinds. **MUST NOT** advertise a complete CompanyMemory extract under a window that can omit them. Admission and caps remain real; silent truncation that drops load-bearing kinds is not “the cap working as designed.” Engine caps stay hard rejects. The fix is cue / filter / scope, not softening $M$ inside Recall.

MemNet **MUST** highlight truncation on the wire when Shape is clipped. If `pin_map` emit signals truncation **or** rows were capped, treat the extract as **incomplete**: **MUST NOT** paint a “complete FND census.” Re-cue / filter-out (prefer filter-out) **or** raise compose $M$ / uncap and re-pin. Hard engine caps stay hard.

---

## 6. Inspectability / debug pointers

If **analyse misses a prior finding**, triage with [`playbooks/debugging-stm-from-thesis-locks.md`](debugging-stm-from-thesis-locks.md) **before** raising $M$ / keep caps / rankers. Split **proposal miss** (never in the offer) vs **truncated offer** (`max_rows` / window cut load-bearing kinds) vs **eviction** (entered $W$ then dropped).

Force the three surfaces (plus integrate / Commit):

1. **Proposal** — was the finding in the `pin_map` offer from the company session? If the offer is a hard truncate that dropped `FND` / checklist / fundamentals, **or** emit signals truncation / capped rows, that is a **truncated offer**, not a complete extract. Honour the wire highlight; re-cue / filter or raise compose $M$ / uncap and re-pin.
2. **Admission** — offered but not pasted into AnalysisEngine $W$?
3. **Eviction** — entered $W$ then dropped by window / keep / recycle (`AI_INVESTOR_MEMNET_KEEP_ENTS` etc.)?

Then: **cap biting** vs **wrong cue** (wrong `COM_*`, Library session instead of company session, empty census cue treated as neighbourhood dump). Gauge: nickname / hid leaks on the offer wire (honesty $c$). On MemNet **0.19.5**, shaped `pin_map` emit uses `SHAPE_DROP_KEYS` in `memnet.models` (`hid`, `_memnet_hid`, `elementId` dropped on shaped emit — mutate ack, shaped present, jsonl). Nickname `id` stays off **shaped read** (0.19.4). Do not invent extra drop keys. See MemNet [CHANGELOG 0.19.5](https://github.com/chouswei/MemNet/blob/main/CHANGELOG.md) and [`docs/operations/honesty-c-wire-audit.md`](https://github.com/chouswei/MemNet/blob/main/docs/operations/honesty-c-wire-audit.md).

Do **not** treat a Library-only fill as a CompanyMemory retrieval miss. Hydration has not Commit’d yet.

---

## 7. Handoff

If the company session is SSOT for shared company working memory:

- Hand off **`companySessionId`** (and mission `sessionId` where applicable).
- Peer re-pins via `pin_map` / cue. Do **not** ship a graph dump as STM.
- Empty cue outline = census under hard LIMIT, not a neighbourhood dump of edges.
- Do **not** bind mission `sessionId` to `companySessionId` or `evidenceSessionId`.

---

## 8. What this playbook does not do

- Change desk code in `modelbasedPrj-ai-investor` (Inves owns the desk).
- Claim Neo4j live / Bolt hydrate for CompanyMemory or EvidenceCentre.
- SemVer $a$/$b$ on MemNet (honesty $c$ is a wire-leak **symptom**, not a version cut). Truncation-on-wire is a harness MUST, not a SemVer claim here.
- Mint a truncation field name on `pin_map` (honour the emit signal / capped-row fact; do not invent a key in this playbook).
- Replace `docs/memnet-role.md` (that file remains desk SSOT).
- Put $m$, $p$, momentum, coverage, $\lambda$ on the product wire.

---

## 9. Quick self-check

- [ ] CompanyMemory named as desk part / MemNet **client**, not MemNet identity, not Neo4j  
- [ ] Library session ≠ company session; fill writes Library only  
- [ ] OpenClaw = InvestorApi; pin_map-only on company sessions; no Bolt; no fill-path `pin_map` as Library writer  
- [ ] $S$ = `COM_*` session (+ snapshots); not PersistentStore / OHLCV  
- [ ] Three surfaces logged separately on analyse misses  
- [ ] Commit = CompanyMemory GQL only  
- [ ] Handoff = session ids, not dump  
- [ ] No hid/nickname ranking; no $m$/$p$/$\lambda$ on `pin_map`  
- [ ] CompanyMemory `pin_map` on 0.19.5: `SHAPE_DROP_KEYS` hygiene (`hid` / `_memnet_hid` / `elementId` off shaped emit)  
- [ ] CompanyMemory extract: no truncating `max_rows` that can drop `FND` / checklist / fundamentals; filter-out or uncapped / high enough; never claim “complete” under that window  
- [ ] If `pin_map` signals truncation or rows were capped: extract incomplete; no “complete FND census”; re-cue / filter or raise compose $M$ / uncap and re-pin; caps stay hard  

---

## Pointers

- Thesis: `thesis/analytical-mechanics-of-llm-stm.md`  
- Wire: [`playbooks/agent-harness-from-thesis-locks.md`](agent-harness-from-thesis-locks.md)  
- Triage: [`playbooks/debugging-stm-from-thesis-locks.md`](debugging-stm-from-thesis-locks.md)  
- Desk SSOT: `docs/memnet-role.md` in [modelbasedPrj-ai-investor](https://github.com/chouswei/modelbasedPrj-ai-investor)  
- §13 seam locks used here: inspectability, gauge/P3 (nickname off wire; 0.19.5 `SHAPE_DROP_KEYS`), update (Commit impulse), user-input placement (harness §2.5), measuring $m$ (off-wire), Legendre firewall, KKT / $\hat\lambda\_M$ as diagnostic only  
- MemNet honesty $c$: [CHANGELOG 0.19.5](https://github.com/chouswei/MemNet/blob/main/CHANGELOG.md) (`SHAPE_DROP_KEYS`); [honesty-c wire audit](https://github.com/chouswei/MemNet/blob/main/docs/operations/honesty-c-wire-audit.md)  
