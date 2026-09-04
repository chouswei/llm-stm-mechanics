# P1 author-blind review (Sage)

Record of the **author-blind** review of the p1-hr $n=200$ graphs. Sage did not author the graphs.

**Stratum sign-off:** ACCEPT after regen. See [`SAGE_SIGNOFF.md`](SAGE_SIGNOFF.md).

Protocol (2026-09-04):

- Blinded packs
- No `expect_*` fields
- No prior reviews
- No $\widehat{\mathcal{A}}$ as quality evidence

The sealed pack-to-session map is **not shipped**. Do not invent it. Post-hoc reconstruction of pack IDs from this tree is not a blind review.

## Files

| File | Role |
|------|------|
| [`SAGE_SIGNOFF.md`](SAGE_SIGNOFF.md) | Stratum sign-off |
| [`REPORT.md`](REPORT.md) | Review report |
| [`REGEN_8.md`](REGEN_8.md) | Eight AUTO_DUMP regenerations |
| [`BLIND_REVIEWS.md`](BLIND_REVIEWS.md) | Summary of the blind pass (no pack secrets) |
| [`results.summary.json`](results.summary.json) | Reconstructed counts; no secrets |
| [`BLIND_MAP.md`](BLIND_MAP.md) | Sealed / omitted |

Graphs live in [`../p1-hr/`](../p1-hr/). The eight regenerated `asymmetric-spoke` specs are in that tree.
