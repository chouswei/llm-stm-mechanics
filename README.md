# Analytical Mechanics of Short-Term Memory for Large Language Models

Research note by **Szu-Wei Chou**, dated **2026-09-03**, accompanying [MemNet](https://github.com/chouswei/MemNet). Read the paper at [`thesis/analytical-mechanics-of-llm-stm.md`](thesis/analytical-mechanics-of-llm-stm.md).

Short-term memory is modelled as a controlled trajectory of the LLM-side working set $W_t$, not as a dump of persistent inventory such as a session graph. The note argues for discrete, dissipative analytical mechanics with Pontryagin control, KKT cap diagnostics, and a Noether gauge invariant under hidden-identifier renaming; Hilbert-space formalism is optional later as a quantisation, never the store. This is analysis only: it is not MemNet product doctrine, makes no SemVer claim, and changes no MemNet version.
