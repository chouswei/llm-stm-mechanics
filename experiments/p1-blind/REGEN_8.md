# Eight AUTO_DUMP regenerations (`asymmetric-spoke`)

During the Sage author-blind pass, eight graphs in family `asymmetric-spoke` failed AUTO_DUMP: the $k\le 2$ neighbourhood of the legal HUB seed was gold-only, so a dump-vs-walk contrast in that ball was vacuous.

**Fix (same family, same gold set):** add a non-gold decoy at hop 1 (`doc-sNNNN-decoy`, edge `contains` / `h1-decoy`).

Sage re-check after regen: **ACCEPT 8/8**.

These session indices are graph identities in [`../p1-hr/`](../p1-hr/), not blind pack IDs. They are the eight family members whose gold set occupies the whole $k\le 2$ ball (`n_gold=4`: hub + light + `hvy0` + `hvy1`). The three family members with `n_gold=3` already had a non-gold node (`hvy1`) in that ball and were not regenerated.

| session_i | spec | gold slugs (unchanged) |
|-----------|------|------------------------|
| 14 | `g0014.json` | hub, light, hvy0, hvy1 |
| 29 | `g0029.json` | hub, light, hvy0, hvy1 |
| 59 | `g0059.json` | hub, light, hvy0, hvy1 |
| 74 | `g0074.json` | hub, light, hvy0, hvy1 |
| 89 | `g0089.json` | hub, light, hvy0, hvy1 |
| 119 | `g0119.json` | hub, light, hvy0, hvy1 |
| 134 | `g0134.json` | hub, light, hvy0, hvy1 |
| 149 | `g0149.json` | hub, light, hvy0, hvy1 |

Not regenerated (`n_gold=3`): 44, 104, 164.

Builder lock: [`../p1-hr/graphs/builders.py`](../p1-hr/graphs/builders.py) `build_asymmetric_spoke` inserts the hop-1 decoy when `len(gold) >= 4`.
