# Analytical Mechanics of Short-Term Memory for Large Language Models

**Szu-Wei Chou**

**2026-09-03** (results §10 updated 2026-09-04)

> **Header note.** This is a research note accompanying MemNet (https://github.com/chouswei/MemNet). It is analysis. It is not a MemNet SemVer claim and changes no MemNet version.

---

## Abstract

Short-term memory in a large language model is not a store. It is a controlled trajectory. The tokens a model can use at turn $t$ come only from the working-set configuration $W_t$: what is actually resident in the context window and the KV cache. Everything else — weights, a corpus, a session graph $S$ — is inventory. This note argues that analytical mechanics is the right fundamental layer for the *mechanism* of short-term memory. $W_t$ is a phase point. The cue is a control $u$. The momentum $p$ is derived, not asserted. Usefulness is a property of the action $\mathcal{A} = \int L\,dt$ along a trajectory, not of a global ranker and not of a dump of $S$. Three roles separate cleanly and must not be collapsed: the LLM is the integrator, steering is the choice of Hamiltonian, force, or constraint, and memory is the manifold plus the phase point. Because the working set is discrete, we use discrete variational mechanics rather than pretending $W$ is smooth. Because eviction destroys information, we use a dissipative port-Hamiltonian form rather than claiming a symplectic flow. Because window length and row caps are inequalities, we use KKT multipliers, which turns a modelling nuisance into a diagnostic: the multiplier on a cap is strictly positive exactly when that cap is biting. Because the cue is a control, the natural setting is Pontryagin's maximum principle, in which $p$ is the costate and "the experimenter picks the next cue" is the maximisation step. The strongest result is a symmetry. Hidden identifiers are not observable and identity-by-name is not identity, so the offered Shape must be invariant under renaming. That is a gauge invariance. The physical working set is the class in the quotient $\mathcal{W}/G$; a hid-dependent trajectory is a gauge anomaly. A continuous naming chart is used later only as a pedagogical surrogate, not as the derivation of a Noether-I charge. Three predictions are stated with protocols that can fail. On a synthetic stratum they all passed after one product fix: a hid-ranking gauge anomaly in `pin_map` (MemNet PR #147) that Prediction 3 caught before generation. Human-reviewed graphs and LLM-generate strata remain open. Hilbert-space formalism is optional later, as a quantisation of this mechanics. It is never the store.

---

## Non-doctrine block

This thesis is analysis. It is not MemNet product doctrine. It changes no MemNet version — not a, not b, not c. Nine specific consequences, stated so they cannot be quietly dropped:

1. **Phase-space equivalence in research does not license a third operator.** It does not license a `rag_query` on the wire. Operator count stays 2: Recall and Commit.
2. $p$ is an analysis quantity. It is never a node property and is never emitted by `pin_map`. Emitting it would break identity-is-the-element and no-store-key.
3. $H$ is not a MemNet verb and not a scheduler. It describes why the agent picks a cue. It does not run anything.
4. **The manifold is implicit and is never emitted.** Do not materialise it, do not precompute it, and do not dump $S$ in order to "see" it.
5. **Multipliers are for analysis.** Engine caps stay hard rejects. A soft, buyable row cap $M$ is goldfish death.
6. $\mathcal{A}$ is an analysis integral over the agent's turns, not engine-retained state. There is no cross-turn trajectory store. That is exactly the stuffed-map failure that dropping prior pin maps exists to prevent.
7. **No engine-emitted coverage, $d$, $\lambda$, or $m$.** Schematic terms in $L_d$ are analysis. They are not `pin_map` fields. The ban is the same as for $p$.
8. **An experimental snapshot is not a dump-$S$ API.** Serialising observable material for a RAG bench is a protocol step. It is not a product dump of $S$ and not `rag_query`.
9. **No learned ranker inside Recall.** Approximating $\arg\max_u H_c$ is experimenter or harness work. It is not a MemNet verb and not a silent merge into RelativeSeed. RelativeSeed still never absorbs.

---

## 1 Introduction: the goldfish generate

The next generate is a goldfish. At turn $t$ the model emits tokens conditioned on one thing: the working-set configuration $W_t$, meaning the token and KV state actually resident in the context window. Weights are frozen inventory. A vector index is inventory. A session graph $S$ is inventory. None of it participates in the forward pass unless it has been loaded into $W_t$ first.

This is not a limitation to be argued away. It is the boundary condition that makes the problem well posed. It also kills the most common non-answer, which is to make the store bigger. A larger store does not change the goldfish. Dumping a long-term store into the window is not a mechanism; it is a resource decision that happens to have a mechanism-shaped hole where the mechanism should be. Position effects make this concrete: model performance depends on *where* in a long context the relevant evidence sits, not merely on whether it is present [11]. Presence is not usefulness.

So the question is not "how much can we store" but "which slice is loaded, and at what cost". That question has a shape. It is a state, a control, a cost, and constraints. That is analytical mechanics.

**The claim.** Analytical mechanics is the right fundamental layer for the mechanism of short-term memory in large language models. Configuration, velocity, derived momentum, a Lagrangian, a Hamiltonian, constraints with multipliers, and a variational principle over turns are sufficient to state what short-term memory *is* and to make predictions about it that can fail. Hilbert-space and quantum formalism is optional and later — a quantisation of this mechanics, taken up in §11. It is never the store.

**One caveat, stated early.** The LLM is a stochastic map. At temperature $T > 0$ the update from $W_t$ to $W_{t+1}$ is sampled, not determined, so the integrator is a Langevin-type stochastic integrator and not a symplectic one; deterministic statements below are statements about the drift, and every measurement protocol in §10 must either fix the temperature or average over seeds.

**Turn index.** Throughout, $t$ is a **turn index**, not wall-clock time. $t \to t+1$ is one agent turn. Wall-clock latency is a real engineering quantity and is not this variable.

## 2 Related work

**Analytical mechanics.** The standard treatments are Goldstein, Poole and Safko [1] and Landau and Lifshitz [2]. We use them for the ordinary machinery: generalised coordinates, the Legendre transform, canonical transformations, and constraint classification.

**Discrete variational mechanics.** The working set is discrete, so the correct reference frame is discrete mechanics rather than a smoothed analogy. Marsden and West [3] give discrete Lagrangians, discrete Euler-Lagrange equations, a discrete Noether theorem, and natural treatments of forces, dissipation and constraints. This is the load-bearing citation for §3.

**Dissipative and open systems.** A memory that forgets is not conservative. Port-Hamiltonian systems theory [4] supplies the resistive structure and the dissipation inequality that eviction needs.

**Optimal control.** Cue-as-control plus an action functional is optimal control, not bare classical mechanics. Pontryagin's maximum principle [5] gives the costate interpretation of $p$ and the control Hamiltonian. Inequality constraints are handled by the Karush-Kuhn-Tucker conditions [6][7], with the standard modern presentation and the shadow-price reading of multipliers in Boyd and Vandenberghe [8].

**Symmetry.** Noether [9] is the source for symmetry implies conservation. The case that applies here is a finite group $G$ acting globally: physical Shape lives in the quotient $\mathcal{W}/G$ (orbit equivalence). The second theorem's local gauge invariance is only what an optional continuous naming chart would look like; it is not the existing lock (§8).

**Geometric and quantum-inspired information retrieval.** There is a real literature that puts retrieval in Hilbert space: van Rijsbergen [10], the survey by Uprety, Gkoumas and Song [12], and Piwowarski, Frommholz, Lalmas and van Rijsbergen [13]. Operator representations of graph nodes exist too [14]. This work is relevant to §11 and is explicitly *not* the foundation used here. Quantum walks [17][18] appear only in §11. Quantum steering [19] appears only as a contrast: the steering in this paper is classical control, not the EPR-type phenomenon.

**Context loading and eviction.** Retrieval-augmented generation [16] is the canonical load operator. KV eviction has a growing literature; H2O [20] evicts by accumulated attention score, and SnapKV [21] selects prompt KV positions using an observation window at the end of the prompt. Position sensitivity in long contexts is documented by Liu et al. [11]. In the language of this paper, all of these are *controls on the same phase space*.

**Informal.** Karpathy's model-as-CPU / context-as-RAM analogy [15] is a useful piece of framing and is cited as informal commentary, not as a result. It gets the inventory-versus-resident distinction right and stops there; it has no dynamics, no cost functional, and no symmetry.

## 3 Analytical mechanics as the fundamental

### 3.1 The variational object

Let $\mathcal{W}$ denote the configuration manifold of admissible working sets. A trajectory is a sequence $W_0, W_1, \ldots, W_N$. In a continuous surrogate one writes

$$
\mathcal{A}[W,u] = \int_{0}^{N} L(W,\dot{W},u,t)\,dt.\qquad (1)
$$

The action is always $\mathcal{A}$, never $S$. The symbol $S$ is locked to the persistent session graph. A useful elementary Lagrangian is

$$
L(W,\dot{W},u,t)=\frac{1}{2}m\|\dot{W}\|^2-V(W;u,t)-C(W,u,t).\qquad (2)
$$

The kinetic term is not decoration. It defines persistence. The parameter $m$ is pin stickiness: large $m$ makes rapid working-set changes costly. The cue $u$ enters a time-dependent potential or a constraint. It is a control, not a coordinate. $C$ prices token load, unsupported material, redundancy, or task error.

Now derive momentum rather than naming one by intuition:

$$
p = \frac{\partial L}{\partial \dot{W}} = m\dot{W}.\qquad (3)
$$

Thus hold and inertia are represented by $m$. Momentum is the consequence $m\dot{W}$. It is not defined as "how hard a pin resists eviction". Such a verbal definition would assert the answer without giving a Lagrangian and would make $p$ a product field. Both are category errors.

Where the Legendre transform is regular, the Hamiltonian is

$$
H(W,p,u,t)=p\cdot\dot{W}-L=\frac{\|p\|^2}{2m}+V(W;u,t)+C(W,u,t).\qquad (4)
$$

This $H$ is an analysis function. It is not a MemNet verb and not a scheduler. It explains the selected deflection of $W$; it does not perform Recall or Commit.

**Peak\_L firewall.** MemNet has a product selector named `Peak_L`, a last-resort seed selector under RelativeSeed, not the default. In this paper $L$ is the Lagrangian. Product `Peak_L` is **not** $\arg\max L$.

### 3.2 No smooth-manifold fudge

A token is admitted or it is not. A graph row is returned or it is not. The native $W$ is discrete, while ordinary Hamilton's principle assumes a smooth manifold. Pretending otherwise would make every later equation cosmetic.

Use a discrete Lagrangian $L_d(W_k,W_{k+1};u_k)$, interpreted as an approximation to the action over one turn. The discrete action is

$$
\mathcal{A}_d = \sum_{k=0}^{N-1} L_d(W_k,W_{k+1};u_k).\qquad (5)
$$

Varying interior configurations with endpoints fixed gives the discrete Euler-Lagrange equation [3]:

$$
D_2 L_d(W_{k-1},W_k;u_{k-1})+D_1 L_d(W_k,W_{k+1};u_k)+F^-_k+F^+_k=0.\qquad (6)
$$

Here $D_1 L_d$ means the partial derivative of $L_d$ with respect to its *first* slot (the earlier configuration), and $D_2 L_d$ with respect to its *second* slot (the later configuration). They are not new operators; they are ordinary gradients with the two arguments of $L_d(W_k,W_{k+1})$ labelled. The $F_k^\pm$ terms are discrete external forces: steering, tool output, or a commit kick. Discrete Noether theory gives conservation laws for symmetries of $L_d$. Forced and constrained versions remain available. Dissipation can also be included. This is why discrete variational mechanics is not merely a patch; it is the native formulation.

There is an alternative when gradients are needed. Relax membership into continuous attention mass $a_i \ge 0$ on a simplex,

$$
\sum_i a_i = 1,\qquad (7)
$$

and define $W$ by its attention-density vector. The vertices recover hard admission. This relaxation can estimate gradients or solve an optimal control problem, but an implementation must round back to a discrete working set. The relaxed system is an instrument, not an excuse to claim the actual window is smooth.

### 3.3 Forgetting makes the system open

Pure Hamiltonian flow is symplectic and volume-preserving. Eviction is neither. It destroys recoverable state from the active working set. Therefore "$H$ generates the next step" plus "caps evict" is quietly inconsistent unless loss is modelled.

One option is a Rayleigh dissipation function,

$$
\mathcal{R}(\dot{W})=\frac{1}{2}\gamma\|\dot{W}\|^2,\qquad (8)
$$

which modifies the Euler-Lagrange equation to

$$
\frac{d}{dt}\frac{\partial L}{\partial\dot{W}}-\frac{\partial L}{\partial W}+\frac{\partial\mathcal{R}}{\partial\dot{W}}=F_u.\qquad (9)
$$

The better systems account is port-Hamiltonian [4]:

$$
\begin{bmatrix}\dot{W}\\ \dot{p}\end{bmatrix}=(J-R)\nabla H+Gu,\qquad J^{\top}=-J,\qquad R=R^{\top}\succeq 0.\qquad (10)
$$

Then

$$
\dot{H}=-\nabla H^{\top} R\nabla H+y^{\top}u\le y^{\top}u.\qquad (11)
$$

Read the symbols once. $\nabla H$ is the gradient of $H$ in the $(W,p)$ coordinates. The superscript $\top$ is transpose: $J^{\top}=-J$ says $J$ is skew-symmetric; $y^{\top}u$ is the ordinary scalar product of the co-port $y$ with the control $u$. The relation $R\succeq 0$ means $R$ is symmetric positive semidefinite — a matrix that can only dissipate, never create, energy. The inequality $\le$ in (11) is the dissipation inequality: stored energy cannot rise faster than the power injected through the port.

The skew structure $J$ accounts for conservative interchange. The resistive structure $R$ accounts for eviction, summarisation loss, and lossy KV compression. The port $(u,y)$ accounts for energy supplied by steering. This is the precise repair for the strongest physics objection to the model: a forgetting memory is an open dissipative system, not a closed Hamiltonian one.

## 4 Dictionary and naming

| Symbol or term | Meaning in this paper |
|---|---|
| $S$ | The persistent session graph: inventory, not the action and not the working set. |
| $\mathcal{A}=\int L\,dt$ | The action over agent turns. It is an analysis integral, not retained engine state. |
| $W_t$ | The LLM-side working-set configuration actually in the context window / KV cache at turn $t$. This is the phase point's configuration component. |
| $\dot{W}$ | Working-set change per turn; in the native discrete model, a finite difference or transition descriptor. |
| $\tilde{X}_t$ | The bounded MemNet `pin_map` artifact: the offered Shape that may populate or steer $W_t$. |
| $u$ | The cue as a control: a time-dependent potential, force input, or constraint pinning a submanifold. Never a coordinate. |
| $q$ | Reserved for the MemNet product cue, represented by codebook tokens. Product $q$ maps to analysis control $u$, once at the product boundary. |
| $p$ | Conjugate momentum, derived by $p=\partial L/\partial\dot{W}$. With the kinetic term above, $p=m\dot{W}$. |
| $L(W,\dot{W})$ | The Lagrangian: persistence cost minus controlled potential and task costs, with controls made explicit when needed. |
| $H(W,p)$ | The Legendre transform/control Hamiltonian, with $u$ explicit when needed. Not a product verb. |
| $\Delta$ | The gated Commit. It is an impulse that can change inventory $S$, not the session graph itself. |
| $t$ | Turn index, not wall clock. |
| store | The manifold of configurations on which $W$ can live, represented by inventory such as weights, a cabinet, a corpus, or session graph $S$. It is not the point $W$. |

**Uncommon operators, once.** $\setminus$ is set difference. $\mapsto$ means "is rewritten as." $\arg\max$ is the set of maximisers. $\nabla$ is gradient; $(\cdot)^{\top}$ is transpose; $R\succeq 0$ means positive semidefinite. $D_1,D_2$ are partials in the first and second slots of a two-argument discrete Lagrangian. A hat ($\widehat{\cdot}$) marks an estimator. $\chi_{\mathrm{invalid}}$ is a $0$/$+\infty$ barrier. These are standard analysis marks; none is a MemNet wire verb.

There are two levels in the word *store*. Concrete cabinets contain elements. Analytically, their addressable possibilities induce the manifold $\mathcal{W}$. The store is therefore the manifold on which a phase point may be selected, not the selected point itself. Memgraph and Neo4j can implement a cabinet. Neither is a theory of memory.

A **canonical transformation** changes coordinates while preserving the symplectic form. Here it means changing how the same inventory is addressed: for example, replacing one cue basis with another invertible cue basis while leaving observable load trajectories unchanged. A new cue basis is not a new memory if the physics is equivalent.

A **holonomic constraint** depends only on the current configuration, $g(W_t)=0$. "Keep the system instruction resident" can be modelled this way. A **path-dependent constraint** depends on history or reachability. Leftover identifiers do not teleport: one can pin only what one can cue along an admissible path. A claimed pin that cannot be reached by the current cue is not a point on the admissible submanifold.

The most important dictionary distinction is operational. $W_t$ is LLM-side. $\tilde{X}_t$ is the offered Shape. The relation $\tilde{X}_t\subseteq W_t$ holds only if the caller admits the whole Shape. Steering proposes $\tilde{X}$; the caller's admission decides $W$; eviction then acts on $W$. These are three distinct places control enters. Collapsing the first two hides one.

[^W-not-Q]: $W$ is not called $Q$ because $Q$ is already taken in MemNet for the `RelativeSeed` seed set; $|Q|>1$ is `CueConflict`.

## 5 The role of the LLM

The LLM is the integrator. It runs the equations of motion under whatever $H$ and constraints are set. It does not pick the Lagrangian. It does not hold, measure, or commit $S$. In an agent loop it may also pick the next cue — that is the experimenter, still not the memory.

This role statement is intentionally strict. A forward pass integrates one controlled step. Sampling supplies stochastic forcing. The prompt constructor, retriever, and KV policy establish the force and boundary conditions. The model then maps resident state to a distribution over outputs. Calling the model "the memory" confuses the transition rule with the state being transitioned.

The integrator may produce text that proposes a cue for the next turn. At that moment the same software component occupies a second *role*: experimenter. The distinction is causal, not organisational. The experimenter selects $u_t$; the integrator realises the stochastic transition conditional on $u_t$. Logging them separately is enough to test the distinction.

## 6 Steering as control

Steering is choosing $H$, a force, or a constraint that deflects $W$. ShapeWalk, RAG retrieval, a ranker, and KV eviction are different controls on the same phase space. Steering is not the generate and not the store. Quantum steering is a different technical concept [19]; none of its nonlocality is invoked here.

### 6.1 Optimal control, not bare mechanics

Let the controlled state obey

$$
\dot{W} = f(W,u,t)\qquad (12)
$$

or its discrete counterpart $W_{t+1}=F(W_t,u_t,\xi_t)$, where $\xi_t$ is sampling noise (the stochastic draw of the LLM). Let the objective be

$$
J[u] = \Phi(W_N) + \int_0^N \ell(W,u,t)\,dt.\qquad (13)
$$

Here $\Phi(W_N)$ is a terminal cost on the final working set, and $\ell(W,u,t)$ is the running cost per turn (token mass, task error, redundancy). Neither is a MemNet verb; both are analysis scalars chosen by the experimenter.

Pontryagin's control Hamiltonian is

$$
H_c(W,p,u,t)=p\cdot f(W,u,t)-\ell(W,u,t).\qquad (14)
$$

The necessary conditions are

$$
\dot{W}=\frac{\partial H_c}{\partial p},\qquad \dot{p}=-\frac{\partial H_c}{\partial W},\qquad u_t\in\arg\max_{u\in U}H_c(W_t,p_t,u,t).\qquad (15)
$$

The first two lines are the usual Hamilton equations for state and costate. The third uses $\arg\max$: $u_t$ is any control in the allowed set $U$ that *maximises* $H_c$ at the current $(W_t,p_t)$. If several maximisers exist, any one may be chosen; the set notation $\in\arg\max$ records that. That maximisation step *is* cue selection.

Here $p$ is the adjoint or costate $p_{\mathrm{adj}}$. Mechanical momentum $p_{\mathrm{mech}}=m\dot{W}$ lives in a different equation. This paper uses one letter $p$ as a convenience. The identification $p_{\mathrm{mech}}\equiv p_{\mathrm{adj}}$ is assumed, not shown; it holds only under Legendre regularity (§13). It is not permission to invent a `momentum` field. The maximum principle *is* the sentence "the experimenter picks the next cue." The LLM does not choose the cost functional. It integrates the next step after the experimenter or agent harness selects $u$.

### 6.2 Inequality caps and KKT diagnostics

Window length, hop radius, row cap $M$, and load-rate caps are inequalities. They are not plain equality constraints with ordinary Lagrange multipliers. Let

$$
g_M(W)=|W|-M\le 0.\qquad (16)
$$

The augmented cost uses a KKT multiplier $\lambda_M\ge0$. Necessary conditions include primal feasibility, dual feasibility, stationarity, and complementary slackness [6][7][8]:

$$
\lambda_M g_M(W)=0.\qquad (17)
$$

Therefore

$$
\lambda_M>0 \implies |W|=M.\qquad (18)
$$

Under regularity and an active optimum, a positive shadow price occurs precisely when relaxing the cap would improve the objective. This yields a measurable result: $\lambda_M>0$ exactly when the goldfish row cap is biting. The same applies to window length, hop radius, and rate caps. Estimate $\lambda_M$ by finite differences of optimal task loss around $M$, not by softening the engine reject. The engine cap remains hard.

### 6.3 Three control surfaces

Control enters at three places:

1. **Proposal:** a retrieval or walk offers $\tilde{X}_t$.
2. **Admission:** the caller constructs actual $W_t$ from the proposal, instructions, dialogue, and tool results.
3. **Eviction:** a KV policy removes elements or attention mass from $W_t$ after admission.

A global ranker controls proposal. It does not determine admission and cannot know the final eviction trajectory by itself. This is why a single relevance score cannot be the mechanism of STM.

**RAG firewall.** RAG is a legitimate object of study as a load operator. It is still not a sanctioned MemNet operator. Phase-space comparison does not add `rag_query` to the wire.

## 7 Memory as manifold and phase point

Memory is manifold plus phase point. The store — weights, cabinet, session graph $S$, corpus — is inventory. STM is $(W,p)$. Usefulness is a trajectory of $\mathcal{A}$, not a dump.

The configuration manifold collects admissible working sets. Its topology says which configurations can be reached from which others under legal controls. The phase point adds the derived tendency $p$, so two identical windows need not represent the same memory state if one is being held and one is being rapidly displaced. The distinction is analytical: no engine emits $p$.

This definition answers a practical question that static retrieval metrics evade. Suppose two systems expose the same evidence at turn 5. System A loaded a bounded neighbourhood at turns 2–5 and preserved task-relevant pins. System B repeatedly dumped large ranked lists and evicted the useful evidence twice. Their endpoint $W_5$ may match, but their action costs differ. STM quality is path-sensitive.

A phase-space diagram makes the separation explicit:

```mermaid
flowchart TD
    I["Inventory — weights, corpus, session graph S"] -->|"control u proposes"| X["Offered Shape X̃_t"]
    X -->|"caller admission"| W["Configuration W_t"]
    W -->|"derive p = m W-dot"| P["Phase point W_t, p_t"]
    P -->|"LLM stochastic integration"| Nxt["Next configuration W_t+1"]
    Nxt -->|"eviction / dissipation"| E["Bounded W_t+1"]
    Nxt -.->|"gated Commit Delta"| I
```

The diagram has no arrow from inventory directly to generation. Every usable item crosses the proposal and admission boundaries. Commit $\Delta$ points back to inventory because it changes $S$, not because $S$ is the action.

### 7.1 Locality and reachability

A store induces many possible coordinates. Only a small neighbourhood is reachable under a bounded cue. This makes graph topology mechanically relevant without turning the graph into the state. A $k$-hop control restricts admissible transitions; it does not claim the whole graph is resident.

Path dependence matters for stale ids. If an identifier remains in a caller but is no longer nameable from the current cue basis, it cannot be treated as an instantaneous holonomic pin. It requires a path through admissible cues or it is unavailable. "Leftover ids do not teleport" is thus a reachability condition.

### 7.2 Framework honesty

Analytical mechanics supplies the dynamics. An earlier quantum-measurement pass supplied a different discipline: no-cloning as "hand the session id, do not dump $S$," and `CueConflict` as "do not fake collapse." Analytical mechanics does not give those constraints for free. They remain interface and measurement commitments. This paper has not swapped frameworks and silently retained their conclusions; it states which framework contributes what.

## 8 Noether: rename invariance as gauge symmetry

This is the main result.

### 8.1 The symmetry already exists

A hidden identifier `hid` is not observable. Identity-by-name is not identity. Rename every hidden storage identifier by a bijection $\rho$, preserving incidence, observable payloads, and codebook-token relations. A correct `pin_map` output cannot change except for the corresponding unobservable relabelling. Formally, if $G$ is the group of such renamings and $g\in G$, then the discrete Lagrangian must satisfy

$$
L_d(gW_t,gW_{t+1};u_t)=L_d(W_t,W_{t+1};u_t).\qquad (19)
$$

The measurable Shape is an equivalence class $[\tilde{X}_t]$ under $G$, not a bag of cabinet keys. This is gauge invariance: multiple internal descriptions denote one physical working-set trajectory.

For a finite permutation group, invariance gives exact orbit equivalence rather than a differential Noether charge. That orbit equivalence on the quotient $\mathcal{W}/G$ is the theorem. What follows is a continuous pedagogical surrogate, not a derivation from the existing MemNet lock. The lock is a global bijection $\rho$ on hidden ids, applied once to the cabinet. Local turn-dependent renaming is a strictly larger group. Embed renaming in a continuous redundant naming chart only to show what a Noether-II constraint *would* look like. Let $\theta^a_t$ be coordinates that choose an internal naming gauge while observables $x_t$ encode incidence and payload. Write

$$
W_t=(x_t,\theta_t),\qquad (20)
$$

and require local gauge invariance under arbitrary turn-dependent shifts

$$
\theta_t^a \mapsto \theta_t^a + \epsilon_t^a.\qquad (21)
$$

The arrow $\mapsto$ means "is sent to": each naming coordinate $\theta_t^a$ may be shifted by an arbitrary $\epsilon_t^a$ at that turn. It is a rewrite rule for the chart, not a dynamical flow.

Because names are unobservable, the action cannot depend on $\theta^a$ or its velocity. The conjugate naming momentum is therefore

$$
\pi_a = \frac{\partial L}{\partial \dot\theta^a}=0.\qquad (22)
$$

Its evolution is

$$
\dot\pi_a = \frac{\partial L}{\partial \theta^a}=0.\qquad (23)
$$

In the surrogate, the vanishing gauge charge $\pi_a\equiv0$ is a constraint: no physical momentum flows in the hidden-name direction. It is a property of the continuous chart, not a conserved payload of the product. Ordinary global symmetries yield a possibly nonzero conserved charge. A local gauge symmetry yields a Noether identity and a constraint. The product lock is global and discrete; the local continuous story is pedagogy. Calling some arbitrary hash count "the conserved quantity" would be wrong. The rigorous result is that physical trajectories lie in the quotient $\mathcal{W}/G$.

### 8.2 Observable consequence

Let a load cost be

$$
C_{\mathrm{load}}(\tilde{X}_t,W_t).\qquad (24)
$$

Gauge invariance requires

$$
C_{\mathrm{load}}(g\tilde{X}_t,gW_t)=C_{\mathrm{load}}(\tilde{X}_t,W_t).\qquad (25)
$$

Then action, cap multipliers, and task metrics are all functions on the quotient space. Two isomorphic session graphs differing only in hidden names must produce the same distribution of admitted Shapes, the same estimated action, and the same task score, up to sampling error.

### 8.3 What breaks when symmetry breaks

If `hid` leaks into ranking, ordering, persistence, or the returned Shape, the potential becomes $V(W;u,\theta)$. Then

$$
\dot\pi_a=\frac{\partial L}{\partial\theta^a}\ne0.\qquad (26)
$$

The naming gauge exerts a fictitious force. Two relabelled but otherwise identical stores can follow different trajectories. The measured action becomes cabinet-dependent. Cache behaviour can change after a database migration that preserves all observable content. Worse, an emitted hidden key acquires apparent identity and can be replayed as if it were the element. That violates identity-is-the-element and no-store-key.

This gives a direct test. Generate isomorphic copies of a session graph under random hidden-id permutations. Fix cue codebook tokens, admission policy, model, and RNG seed. Canonicalise *labels*, not sequence: admission order in the window is physical [11]. If a hid-sort changes row order and therefore $W$, that is a gauge anomaly, not noise to be washed out. Any systematic difference is a gauge anomaly. The quotient has become an executable invariant test.

## 9 Instantiations: one phase space, different controls

The instantiations below repeat a crucial distinction because implementations tend to erase it: $W_t$ is LLM-side; $\tilde{X}_t$ is the offered Shape; $\tilde{X}_t\subseteq W_t$ only if the caller admits the whole Shape. Steering proposes $\tilde{X}$, caller admission decides $W$, and eviction then acts on $W$. These are three distinct control sites. Collapsing proposal and admission hides one.

### 9.1 MemNet ShapeWalk

This is a worked example using package `memnet-llm` 0.19.3. It is not the only physics and it is not a MemNet 1.0 claim.

Let the product cue $q_t$ be a finite sequence of codebook tokens. At the analysis boundary, map product $q_t$ to control $u_t$. Relative seed selection identifies a legal seed relative to the existing session. A bounded ShapeWalk explores at most $k$ hops and returns at most `LIMIT M` rows. The resulting bounded `pin_map` artifact is $\tilde{X}_t$.

A schematic discrete Lagrangian is

$$
L_d(W_t,W_{t+1};u_t)=\frac{m}{2}\,d(W_t,W_{t+1})^2-\alpha\,\mathrm{coverage}(W_{t+1},u_t)+\beta\,|W_{t+1}\setminus W_t|+\chi_{\mathrm{invalid}}.\qquad (27)
$$

Read (27) term by term. $d(W_t,W_{t+1})$ is a set-transition distance between consecutive working sets. The stickiness $m$ prices churn through the kinetic term. $\mathrm{coverage}(W_{t+1},u_t)$ is a scalar reward for how well the new set supports the cue — analysis only, never a `pin_map` field. The operator $\setminus$ is set difference: $W_{t+1}\setminus W_t$ is the set of elements newly admitted this turn, and $|W_{t+1}\setminus W_t|$ is their count. The symbol $\chi_{\mathrm{invalid}}$ is an indicator barrier: $0$ on legal transitions and $+\infty$ on hard-invalid ones (cap violations, unreachable pins), so illegal moves are simply not stationary points of $L_d$. The native discrete momentum is the discrete Legendre transform of $L_d$, not returned by the engine.

**Worked turn.** Assume the LLM is answering why a prior deployment failed. At turn 7, product cue $q_7$ contains codebook tokens for `deployment`, `rollback`, and a relative-session marker. The experimenter maps this to $u_7$. ShapeWalk starts from the legal RelativeSeed, walks up to $k=2$, and offers 18 rows under hard `LIMIT M=24`; this is $\tilde{X}_7$. The caller admits the 12 rows whose observable payload fits alongside system text and recent dialogue, so $\tilde{X}_7\nsubseteq W_7$ as an entire Shape. KV policy then removes two low-value old dialogue spans from $W_7$. The model integrates the resulting state and explains the rollback. If the output warrants durable change, gated Commit $\Delta_7$ writes a new observable relation to $S$. Commit is an impulse that changes the manifold's inventory for future turns. It is not a third retrieval operator.

The constraints are

$$
\mathrm{hop}(\tilde{X}_7)\le k,\qquad |\tilde{X}_7|\le M,\qquad \mathrm{rate}(W_7,W_8)\le r.\qquad (28)
$$

Plain language: $\mathrm{hop}(\tilde{X})$ is the farthest graph distance from the seed still present in the offered Shape; $|\tilde{X}|$ is the row count; $\mathrm{rate}(W_t,W_{t+1})$ is how fast the working set is allowed to change (for example $|W_{t+1}\setminus W_t|$). All three are $\le$ inequalities — hard caps, not soft targets.

Their KKT multipliers estimate which cap is active in the *optimal-control account*. Product behaviour remains hard reject. If the row-cap multiplier becomes positive and task loss rises, the diagnostic says the offered Shape is pressing against $M$. It does not say to make $M$ buyable.

Rename invariance is immediate: permuting all hidden ids while preserving observable relations must leave the canonicalised 18-row Shape unchanged. This is the §8 gauge test in product clothing.

### 9.2 RAG retrieval

RAG [16] is one load operator from a corpus into the window. A retriever maps query control $u_t$ to passages, giving an offered set $\tilde{X}_t^{\mathrm{RAG}}$. A prompt assembler admits some or all passages into $W_t$. The model then integrates. A large top-$K$ is not a larger memory; it is a stronger and usually more dissipative load impulse.

The relevant cost is not only retrieval relevance. It includes token mass, duplication, displacement of resident pins, and positional degradation:

$$
C_{\mathrm{RAG}}=c_{\mathrm{tok}}|\tilde{X}|+c_{\mathrm{dup}}D(\tilde{X})+c_{\mathrm{evict}}E(W_{t-1},W_t)+c_{\mathrm{task}}\ell_{\mathrm{task}}.\qquad (29)
$$

Each $c_{\cdot}$ is a nonnegative weight fixed by the experimenter. $|\tilde{X}|$ prices token mass; $D(\tilde{X})$ prices duplication inside the offer; $E(W_{t-1},W_t)$ prices how much resident material was displaced; $\ell_{\mathrm{task}}$ is the task loss (for example $1$ minus answer quality). None of these scalars is emitted by the engine.

The "lost in the middle" result [11] implies that equal evidence with equal inclusion can induce different task costs under different positions. Therefore global rank alone cannot determine $W$'s usefulness.

RAG is a legitimate experimental control. The RAG firewall still holds: it is not a sanctioned MemNet operator, and the phase-space account licenses no `rag_query` verb.

### 9.3 KV eviction: H2O, SnapKV, and cousins

KV eviction controls the third surface. H2O retains a balance of recent tokens and accumulated-attention heavy hitters [20]. SnapKV uses an observation window to select clustered prompt positions per attention head [21]. Both act by throwing mass out of $W$ when capacity binds.

Their action is dissipative. If a selected KV entry is gone, ordinary Hamiltonian inversion cannot recover it. In the port-Hamiltonian form, each policy changes the resistive structure $R$. A policy that removes task-irrelevant mass has low task-weighted dissipation; one that removes a critical pin has high task-weighted dissipation even if byte counts match.

This suggests a common benchmark across ShapeWalk, RAG, H2O, and SnapKV. Hold the model and task fixed. Instrument proposal, admission, and eviction separately. Measure transition distance, resident token mass, task loss, and estimated cap multipliers. They are then comparable controls on one phase space rather than unrelated product categories.

## 10 Falsifiable predictions

A dictionary can always be made to fit after the fact. A mechanism must rule out outcomes. The following predictions can fail.

### 10.1 Prediction 1: bounded local loading costs less action than a dump

**Claim.** For tasks whose required evidence lies within a bounded $k$-hop session neighbourhood, the same information loaded by bounded ShapeWalk will achieve equal task performance at lower measured action than a RAG-style dump of the available session material.

Define an operational discrete action estimator before seeing outcomes:

$$
\widehat{\mathcal{A}}_d=\sum_t\bigl[a\,d(W_t,W_{t+1})^2+b\,\mathrm{tokens\_admitted}_t+c\,\mathrm{critical\_evictions}_t+d\,\ell_{\mathrm{task},t}\bigr],\qquad (30)
$$

The hat on $\widehat{\mathcal{A}}_d$ marks an *estimator*: an operational stand-in for the true action, not the action itself. The coefficients $a,b,c,d$ are nonnegative and must be preregistered on a development set before the held-out comparison. $\mathrm{tokens\_admitted}$ counts newly loaded token mass; $\mathrm{critical\_evictions}$ counts removals of task-relevant pins; $\ell_{\mathrm{task}}$ is task loss. This is not claimed to be a universal Lagrangian. It is a measurement model.

**Protocol.** Build at least 500 synthetic and 200 human-reviewed session graphs. Each task has a known minimal evidence set within $k\le2$ hops of a legal RelativeSeed. Create two load conditions: (A) bounded ShapeWalk with fixed hard $M$, and (B) a semantic RAG operator allowed to retrieve from a serialised snapshot of the same observable material. That snapshot is a bench fixture. It is not a product dump of $S$ and not `rag_query`. Match model, prompt instructions, and total output budget. Compare at equal task quality; do not require matched final evidence coverage. A coverage-match plus a token-mass term in $\widehat{\mathcal{A}}_d$ would make the dump lose by construction. Log offered $\tilde{X}_t$, caller admissions, final $W_t$, KV evictions, answer score, and all random seeds. Run deterministic decoding and a temperature condition with at least 20 seeds. Compare $\widehat{\mathcal{A}}_d$ at matched answer quality using paired bootstrap confidence intervals.

**Failure condition.** If RAG dumps have equal or lower action at equal quality across the prespecified local-task stratum, the predicted advantage is false. If the result appears only after changing coefficients, it is also false for the preregistered estimator. A mixed result would narrow the claim to particular graph topologies rather than rescue it universally.

**Result (synthetic stratum, 2026-09-04).** PASS. MemNet @ `eff05dc8` (post PR #147). $n=500$ isomorphic-scale sessions; both conditions scored $1.0$ on all $500$ (gold evidence present). Coefficients locked before outcomes: $a=1$, $b=1$, $c=0$, $d=10$, with $d(\emptyset,W)=|W|$ in (30). Mean $\widehat{\mathcal{A}}$ walk $=422$, dump $=2356$, paired $\Delta=1934$; $95\%$ bootstrap CI $[1934,1934]$ excludes $0$. Dump admitted mean $|W|=35$ vs walk $|W|=11$. Caveat: $\Delta$ was constant across this regular synthetic family — a structural win, not a noisy human-task win. No LLM generate. Human-reviewed $200$ not run.

### 10.2 Prediction 2: the M-cap multiplier detects a wrong Shape

**Claim.** The finite-difference $\widehat{\lambda}_M$ is a diagnostic of the *account*, not a KKT multiplier read off the engine. Complementary slackness is exact only at an optimum of the control programme. The prediction is that this diagnostic becomes positive precisely when the row cap is active and marginally relaxing $M$ would improve the task objective. Wrongly centred or diffuse Shapes should produce positive $\widehat{\lambda}_M$ more often than correctly centred compact Shapes.

**Protocol.** For each task, run $M\in\{8,12,16,24,32\}$ while keeping all other caps fixed. Estimate

$$
\widehat{\lambda}_{M}=-\frac{J^{\ast}(M+\delta)-J^{\ast}(M)}{\delta}\qquad (31)
$$

Again the hat means estimator. $J^{\ast}(M)$ is the achieved task cost when the row cap is set to $M$; $\delta$ is a small positive step in $M$ (one grid step in the experiments). The fraction is an ordinary finite difference: how much $J^{\ast}$ falls when the cap is relaxed, with a minus sign so that improvement yields $\widehat\lambda_M>0$. It is a shadow-price analogue of the account, not a multiplier read out of the engine.

Use one-row or four-row finite differences and confidence intervals over model seeds. Label whether the gold minimal evidence set is truncated at each $M$. Independently perturb the cue to create a wrong Shape without changing the answer target. Test whether $\widehat{\lambda}_{M}>0$ predicts truncation and task improvement under cap relaxation.

**Failure condition.** The claim fails if $\widehat{\lambda}_{M}$ is routinely positive while the cap has slack, nonpositive when relaxing a binding cap improves the preregistered objective, or no better than raw row count at identifying wrong Shapes. Noise near zero should be handled with an equivalence band fixed in advance.

Complementary slackness is exact for the optimisation model under its regularity assumptions. An engine trace is not automatically an optimum. The protocol therefore tests the adequacy of the model as well as the product hypothesis.

**Result (synthetic stratum, 2026-09-04).** PASS as an *account* diagnostic. $n=200$ sessions, $M\in\{8,12,16,24,32\}$, $\delta$ one grid step, band $|\widehat\lambda|<0.005$, $J=(1-\mathrm{score})+0.01|W|$. When gold was truncated and score improved at $M+\delta$, $\widehat\lambda_M$ was positive in $449/463$ ($97\%$). When gold already lay inside $W$, $\widehat\lambda_M\le$ band in $667/667$ (never fake-positive with slack). Wrong cue vs correct: positive-$\widehat\lambda$ rate $0.395$ vs $0.166$ (gap $0.229$). Beat raw $|W|$ as a wrong-Shape detector (AUROC $0.599$ vs $0.5$). Engine caps remained hard rejects; $M$ was only the compose analysis knob. No LLM generate.

### 10.3 Prediction 3: rename invariance

**Claim.** Hidden-id permutations produce no change in offered Shapes, admitted working sets, cap multipliers, or output distributions, once *labels* are canonicalised. Admission order is physical and is not canonicalised away.

**Protocol.** For every test session create 100 isomorphic hidden-id permutations. Freeze observable fields, edge labels, cue codebook tokens, model, and random seeds. Canonicalise labels by observable identity. Do not sort or otherwise wash out row order: if hid-sort changes sequence and therefore $W$, that is a gauge anomaly [11]. Exact comparison before generation; distributional comparison after generation. At $T>0$ and under GPU noise, "reproducible" means outside a predeclared equivalence band. Exact-match without that band will false-positive.

**Failure condition.** Any reproducible dependence on hidden names is a gauge anomaly. There is no coefficient to tune. This is the sharpest test in the paper.

**Result (before-generate half, 2026-09-04).** The claim failed, then passed after a product honesty fix — exactly what a mechanism test is for.

1. **Pilot on PyPI `memnet-llm==0.19.3`:** FAIL (order). $20$ sessions $\times$ $100$ CREATE-order / nickname permutations $=2000$ comparisons. Label *sets* matched $2000/2000$ (`hid` never leaked onto the wire). Emitted *sequences* matched $0/2000$. Root cause: `pin_map` ranked by hidden `Record.hid` (`_elN`) in BFS / edge emit / shell cap. Admission order is physical [11]; sorting it away would have hidden the anomaly.
2. **Fix:** MemNet PR #147 — ranking by kind + observable payload; nickname `id` also excluded from the rank key. Same operators; not a usage-method $b$.
3. **Re-run on `master` @ `eff05dc8`:** PASS. Same $2000$ comparisons: label $2000/2000$, order $2000/2000$. Package regression `test_pin_map_observable_rank.py`: $3$ passed.

Generation half ($T>0$ distributional) not run; not needed to establish the pre-generate gauge law.

### 10.4 Scoreboard

| Prediction | Estimator | Stratum | Verdict |
|---|---|---|---|
| P1 local load vs dump | (30) | synthetic $n=500$, equal gold score | PASS |
| P2 $\widehat\lambda_M$ vs wrong Shape | (31) | synthetic $n=200$ | PASS |
| P3 rename / order invariance | (19) law | $2000$ perms; fail then fix then pass | PASS after #147 |

Scope lock: synthetic, in-process goldfish, no live cabinet, no LLM generate, no human-reviewed graphs. The three fail-able claims held on this stratum. That supports the variational account; it does not close §13.

## 11 Quantization later

Analytical mechanics comes first because the present mechanism already has configurations, controls, constraints, dissipation, and stochastic integration. If future evidence shows that noncommuting measurements, interference, or contextual probability add predictive power, quantisation has a disciplined path.

Start with observables $A(W,p)$ and $B(W,p)$ on phase space and their Poisson bracket,

$$
\{A,B\}=\frac{\partial A}{\partial W}\frac{\partial B}{\partial p}-\frac{\partial A}{\partial p}\frac{\partial B}{\partial W}.\qquad (32)
$$

Canonical quantisation replaces the bracket by a commutator,

$$
\{A,B\}\longrightarrow \frac{1}{i\hbar}[\hat A,\hat B].\qquad (33)
$$

That move may motivate Hilbert-space retrieval models [10][12][13], operator representations of local graph topology [14], or quantum-walk propagators [17][18]. It does not turn a graph database into a wavefunction, make a node id physical identity, or remove admission and eviction. A quantised model would still need an observable algebra, a state, a measurement rule, and a map back to actual $W_t$.

Complementarity and no-cloning may remain useful measurement disciplines. They are not derived here. Quantum walks may provide a later propagator over an already-defined configuration space. Hilbert space is optional later — a quantisation of this mechanics — never the store.

## 12 What this is not

This is not Hilbert IR presented as GQL semantics. Hilbert-space information retrieval is a mathematical framework for representation and measurement [10][12][13]; it does not make a graph query language quantum.

This is not a node `hid` or store key treated as identity. Hidden names are gauge. Observable identity is the element and its relations, not the cabinet address.

This is not raising $M$, enlarging the context window, or dumping $S$ and calling the result "more memory." Those moves alter a cap or load mass. They do not specify a good trajectory.

This is not a MemNet 1.0 claim. The worked package version is `memnet-llm` 0.19.3. The paper changes no version.

This is not a product switch to Memgraph or Neo4j. Those are cabinets: implementations of inventory that induces the manifold. Changing cabinets may be a canonical change of address or an engineering migration. It is not automatically a change in memory physics.

This is not a claim that the LLM stores or measures $S$. The LLM sees only admitted $W_t$. Nor is it a claim that a model-picked cue makes the model itself the memory; cue choice is the experimenter role.

This is not quantum steering. The term steering here means classical control of $W$, unlike the nonlocal quantum-information task formalised by Wiseman, Jones and Doherty [19].

This is not support from "quantum memory graph" marketing. Quantum Atomic RAG, QE-KGR, and QAOA-branded memory graphs are not cited as evidence.

## 13 Open questions

**What is the correct metric on working sets?** Set symmetric difference is easy but treats all resident material equally. Attention-weighted transport is richer but risks making the coordinate system model-specific. A useful metric should be rename-invariant, sensitive to admission order, and estimable without inspecting hidden store keys.

How should $m$ be measured? Pin stickiness could be estimated from the intervention needed to displace an item from $W$ while task and model remain fixed. It may be item-specific and state-dependent, giving a mass matrix rather than a scalar:

$$
T = \frac12 \dot{W}^\top M(W)\dot{W}.\qquad (34)
$$

Here $M(W)$ is a mass *matrix* (not the row cap $M$), and $\dot{W}^\top$ is the transpose of the velocity vector, so the product is the usual quadratic form $\sum_{ij}\dot W_i M_{ij}\dot W_j$. The matrix must live in analysis, not in `pin_map`.

**Where is the Markov boundary?** $(W,p)$ is intended to make the active process first-order, but stochastic decoding, tool state, and caller policy may leave hidden history. If trajectories with equal measured $(W,p)$ have systematically different futures under equal controls, the state is incomplete. That is another falsification route.

**How should discrete costates be interpreted?** Pontryagin costates and discrete Legendre momenta coincide only under specific regularity and discretisation choices. In mixed integer admission, the costate can be nonsmooth or set-valued. The paper's conceptual identification is strong; a production estimator needs a specific optimisation programme.

**Can dissipation be task-weighted without circularity?** Evicting a token matters because of future use, which is only partially observed. One route is to estimate counterfactual task loss after forced eviction. Another is to learn a dissipative metric on held-out tasks. Both risk overfitting the Lagrangian to the benchmark.

**Which symmetries besides renaming exist?** Cue-basis transformations may be canonical if they preserve observable trajectories. Order invariance is not generally a symmetry because long-context models are position-sensitive [11]. Session-graph automorphisms that preserve all codebook and payload observables are candidates for a larger gauge group.

**How much does stochasticity matter?** At nonzero temperature the relevant object is a path measure and the action may be an Onsager-Machlup-type functional rather than the deterministic $\mathcal{A}$. The Langevin sentence in §1 is not a full stochastic variational derivation. This is one of the framework's weakest current points.

**Can a learned control remain inspectable?** A ranker may approximate $\arg\max_u H_c$, but its chosen control should still be auditable against hard caps, rename invariance, and proposal/admission/eviction logs. Otherwise optimal-control notation only renames opacity.

**Which equation is the actual update?** §3.2 writes discrete Euler-Lagrange; §3.3 writes continuous port-Hamiltonian. They are stacked, not glued. There is no discrete Dirac or discrete port-Hamiltonian step in this paper. A physicist is entitled to ask which equation is the update rule.

**Is $p$ one object?** Mechanical $p_{\mathrm{mech}}=m\dot{W}$ and the Pontryagin costate $p_{\mathrm{adj}}$ live in different equations. One letter is a convenience. The identification is assumed, not shown.

**Is the continuous gauge chart a theorem?** The existing lock is a global discrete group $G$. The turn-dependent $\theta_t$ chart is a larger, continuous, local group used as pedagogy. The vanishing $\pi_a$ is a property of that surrogate. The theorem is the quotient $\mathcal{W}/G$.

## 14 Conclusion

The next LLM generate is a goldfish. Only $W_t$ is resident. The rest is inventory. Short-term memory is therefore not the session graph $S$, a corpus, weights, or a global ranking. It is the phase point $(W,p)$ moving on the manifold induced by that inventory.

The three roles are the spine. The LLM is the integrator. It runs the controlled, usually stochastic, equations and does not pick the Lagrangian, hold $S$, measure $S$, or commit $S$. Steering is choosing $H$, a force, or a constraint. ShapeWalk, RAG, rankers, and KV eviction are different controls on one phase space. **Memory = manifold + phase point.** Usefulness is a trajectory of $\mathcal{A}$, not a dump.

Taking the mechanics seriously repairs the loose parts. Discrete variational mechanics handles discrete $W$. A Rayleigh or port-Hamiltonian term handles forgetting. Momentum follows from $p=\partial L/\partial\dot{W}=m\dot{W}$; it is never asserted as a node property. KKT multipliers handle inequality caps and yield a cap-biting diagnostic. Pontryagin makes cue selection an optimal-control step and sharpens the experimenter role. Stochastic decoding makes the LLM a Langevin-type integrator.

Most importantly, analytical mechanics pays for itself through Noether. Hidden-name invariance is a gauge symmetry. Physical action lives on the quotient $\mathcal{W}/G$ because $L_d$ is $G$-invariant. A hidden-id-dependent trajectory is not merely ugly engineering; it is a gauge anomaly with a direct permutation test. The surrogate's $\pi\equiv0$ is a picture of that fact, not the reason.

The account can fail, and one run did: Prediction 3 failed on stock $0.19.3$ because `pin_map` ranked by hid. That is the point of a mechanism test. After ranking by observables (PR #147), P3 passed; P1 and P2 passed on the same synthetic stratum. The defensible result is now stronger than a dictionary: a variational account of the working set whose three fail-able claims held where tested, and whose lead symmetry already paid for a product fix. Human-reviewed graphs, LLM-generate strata, and the open items in §13 remain.

## Equation index

Paper form: each display equation ends with $\qquad (n)$. Display equations only.

- (1) action functional
- (2) elementary Lagrangian
- (3) derived momentum
- (4) Hamiltonian
- (5) discrete action
- (6) discrete Euler–Lagrange
- (7) simplex attention mass
- (8) Rayleigh dissipation
- (9) dissipative EL
- (10) port-Hamiltonian
- (11) dissipation inequality
- (12) controlled dynamics
- (13) control objective
- (14) control Hamiltonian
- (15) Pontryagin necessary conditions
- (16) row-cap inequality
- (17) complementary slackness
- (18) cap-biting implication
- (19) G-invariance of L_d
- (20) observable + naming chart
- (21) local naming shift (surrogate)
- (22) vanishing naming momentum (surrogate)
- (23) naming momentum evolution (surrogate)
- (24) load cost
- (25) gauge-invariant load cost
- (26) gauge anomaly force
- (27) ShapeWalk discrete Lagrangian
- (28) ShapeWalk hard caps
- (29) RAG load cost
- (30) operational action estimator
- (31) finite-difference shadow price
- (32) Poisson bracket
- (33) canonical quantisation map
- (34) state-dependent kinetic energy
## References

1. Herbert Goldstein, Charles P. Poole Jr., and John L. Safko. *Classical Mechanics*, 3rd ed. Addison-Wesley, 2002. https://books.google.com/books?id=EE-wQgAACAAJ
2. L. D. Landau and E. M. Lifshitz. *Mechanics*, 3rd ed., Vol. 1 of *Course of Theoretical Physics*. Butterworth-Heinemann, 1976. https://bibbase.org/network/publication/landau-lifshitz-mechanics-1976
3. J. E. Marsden and M. West. “Discrete mechanics and variational integrators.” *Acta Numerica* 10 (2001): 357–514. https://doi.org/10.1017/S096249290100006X
4. Arjan van der Schaft and Dimitri Jeltsema. *Port-Hamiltonian Systems Theory: An Introductory Overview*. *Foundations and Trends in Systems and Control* 1(2–3), 2014: 173–378. https://doi.org/10.1561/2600000002
5. L. S. Pontryagin, V. G. Boltyanskii, R. V. Gamkrelidze, and E. F. Mishchenko. *The Mathematical Theory of Optimal Processes*. Interscience Publishers, 1962. (Verified via the book-review record: R. Kaufman, *Canadian Mathematical Bulletin* 7(3), 1964, https://doi.org/10.1017/S0008439500032112)
6. William Karush. *Minima of Functions of Several Variables with Inequalities as Side Constraints*. Master's thesis, University of Chicago, 1939. https://catalog.lib.uchicago.edu/vufind/Record/4111654
7. H. W. Kuhn and A. W. Tucker. “Nonlinear Programming.” In *Proceedings of the Second Berkeley Symposium on Mathematical Statistics and Probability*, 1951, 481–492. https://projecteuclid.org/euclid.bsmsp/1200500249
8. Stephen Boyd and Lieven Vandenberghe. *Convex Optimization*. Cambridge University Press, 2004. https://stanford.edu/~boyd/cvxbook/
9. Emmy Noether. “Invariante Variationsprobleme.” *Nachrichten von der Gesellschaft der Wissenschaften zu Göttingen, Mathematisch-Physikalische Klasse* (1918): 235–257. https://eudml.org/doc/59024
10. C. J. van Rijsbergen. *The Geometry of Information Retrieval*. Cambridge University Press, 2004. https://doi.org/10.1017/CBO9780511543333
11. Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni, and Percy Liang. “Lost in the Middle: How Language Models Use Long Contexts.” *Transactions of the Association for Computational Linguistics* 12 (2024): 157–173. https://doi.org/10.1162/tacl_a_00638
12. Sagar Uprety, Dimitris Gkoumas, and Dawei Song. “A Survey of Quantum Theory Inspired Approaches to Information Retrieval.” *ACM Computing Surveys* 53(5), article 98, 2020. https://doi.org/10.1145/3402179
13. Benjamin Piwowarski, Ingo Frommholz, Mounia Lalmas, and Keith van Rijsbergen. “What Can Quantum Theory Bring to Information Retrieval?” In *Proceedings of the 19th ACM International Conference on Information and Knowledge Management*, 2010, 59–68. https://doi.org/10.1145/1871437.1871450
14. Andrew Vlasic and Salvador Aguinaga. “QuOp: A Quantum Operator Representation for Nodes.” arXiv:2407.14281, 2024. https://arxiv.org/abs/2407.14281
15. Andrej Karpathy. “LLMs … as the kernel process of a new Operating System.” Informal post, 28 September 2023. https://twitter.com/karpathy/status/1707437820045062561
16. Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Heinrich Küttler, Mike Lewis, Wen-tau Yih, Tim Rocktäschel, Sebastian Riedel, and Douwe Kiela. “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.” *Advances in Neural Information Processing Systems* 33, 2020. https://proceedings.nips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html
17. Y. Aharonov, L. Davidovich, and N. Zagury. “Quantum Random Walks.” *Physical Review A* 48 (1993): 1687–1690. https://doi.org/10.1103/PhysRevA.48.1687
18. Edward Farhi and Sam Gutmann. “Quantum Computation and Decision Trees.” *Physical Review A* 58 (1998): 915. https://doi.org/10.1103/PhysRevA.58.915
19. H. M. Wiseman, S. J. Jones, and A. C. Doherty. “Steering, Entanglement, Nonlocality, and the Einstein-Podolsky-Rosen Paradox.” *Physical Review Letters* 98 (2007): 140402. https://doi.org/10.1103/PhysRevLett.98.140402
20. Zhenyu Zhang, Ying Sheng, Tianyi Zhou, Tianlong Chen, Lianmin Zheng, Ruisi Cai, Zhao Song, Yuandong Tian, Christopher Ré, Clark Barrett, Zhangyang Wang, and Beidi Chen. “H2O: Heavy-Hitter Oracle for Efficient Generative Inference of Large Language Models.” *Advances in Neural Information Processing Systems* 36, 2023. https://proceedings.neurips.cc/paper_files/paper/2023/hash/6ceefa7b15572587b78ecfcebb2827f8-Abstract.html
21. Yuhong Li, Yingbing Huang, Bowen Yang, Bharat Venkitesh, Acyr Locatelli, Hanchen Ye, Tianle Cai, Patrick Lewis, and Deming Chen. “SnapKV: LLM Knows What You Are Looking for Before Generation.” *Advances in Neural Information Processing Systems* 37 (2024): 22947–22970. https://doi.org/10.52202/079017-0722
