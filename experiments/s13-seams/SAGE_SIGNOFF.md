# Sage sign-off — §13 seam locks (#23–#26)

**Date:** 2026-09-04  
**Reviewer:** Sage  
**Block:** ACCEPT-with-nits

Conceptual locks only. No silent overclaims. Discrete Dirac / port-Hamiltonian, Onsager–Machlup for `pin_map`+sampler, a production $p$ estimator, continuous gauge-as-theorem, the metric on $W$, and inspectability remain open. No MemNet SemVer.

## Verdict table

| PR | Seam | Verdict | Nit |
|----|------|---------|-----|
| [#23](https://github.com/chouswei/llm-stm-mechanics/pull/23) | Legendre ($p_{\mathrm{mech}}\equiv p_{\mathrm{adj}}$) | ACCEPT | Prefer named $p$ in §6.1 display prose |
| [#24](https://github.com/chouswei/llm-stm-mechanics/pull/24) | Update (discrete EL vs port-Hamiltonian) | ACCEPT | Eviction = discrete dissipative force, schematic until Dirac; $R$ in (10) is the continuous forgetting account |
| [#25](https://github.com/chouswei/llm-stm-mechanics/pull/25) | Stochasticity (drift vs path measure; OM candidate) | ACCEPT | — |
| [#26](https://github.com/chouswei/llm-stm-mechanics/pull/26) | Markov (conditional on inventory) | ACCEPT | Optional hypothesis cue in §14 next to "claimed Markov" |

## Nits (applied in the follow-up record)

1. **Legendre.** Prefer $p_{\mathrm{adj}}$ or $p_{\mathrm{mech}}$ explicitly in §6.1 display prose. Reserve a bare $p$ for sentences that invoke the §13 Legendre seam lock, and for (14)–(15) where $p$ is already the costate by definition. Do not collapse the seam for a skimmer.
2. **Update.** On the hard window, eviction is carried as a discrete dissipative force in the forced/dissipative discrete EL sense (schematic until a discrete Dirac / discrete port-Hamiltonian step exists). Continuous resistive $R$ in (10) remains the continuous forgetting account, not a second competing discrete eviction channel.
3. **Markov (thin, optional).** Next to "claimed Markov" in §14, a light hypothesis cue so skimmers do not treat the claim as established.

## Stay open

- Discrete Dirac / discrete port-Hamiltonian step
- Onsager–Machlup for composed `pin_map` + sampler
- Production $p$ estimator
- Continuous gauge-as-theorem
- Metric on $W$
- Inspectability of learned control

## Tighten next (not this record unless a trivial pointer)

- Metric on $W$
- $W$-only Markov falsification run
- Inspectability
