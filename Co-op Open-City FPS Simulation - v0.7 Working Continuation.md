# Co-op Open-City FPS Simulation — v0.7 Working Continuation

**Version:** 0.7.0-draft.17
**Status:** The crew deployment opportunity-cost proof is sealed. No successor city scope is authorized by this continuation.
**Opened:** 2026-08-26  
**Frozen base:** [Co-op Open-City FPS Simulation Contract — v0.6.0](Persistent%20City%20Simulation%20-%20Initial%20Systems%20Note.md)

## Record boundary

The v0.6.0 contract is frozen as the record of the first-principles city model. Do not revise it retrospectively. New decisions, refinements, tests, and implementation-facing specifications belong in this continuation and receive their own versioned changelog entries.

## Inherited baseline

This continuation inherits the v0.6.0 contract, including these established laws:

- The authoritative city record holds causal truth; player intelligence is incomplete and cannot rewrite it.
- City state changes through agents or processes taking valid, resource-constrained actions through the area graph, gates, and thresholds.
- Event fronts are player-readable projections of agent or process commitments, never independent scripted causes.
- The crew bubble materializes the same causal world at high first-person fidelity, then compresses durable results back into the city record.
- The city advances only while at least one player is deployed.

## Continuation scope

Translate the frozen laws into the smallest proof kernel before expanding the city. The immediate target remains:

- three connected areas;
- two competing factions;
- police or a public-service agent;
- one fire process; and
- one crew commitment that occupies player attention.

The kernel must prove determinism, inspectability, valid causal propagation, and faithful materialization without any direct front-stage rule.

The frozen first scenario is specified in [Three-Area Causal Proof Kernel — v0.1.0](Three-Area%20Causal%20Proof%20Kernel%20-%20Draft.md). It is the sole implementation target for this phase.

The corrected reference implementation and passing evidence are recorded in [Proof Kernel Implementation Evidence — v0.1.1](Proof%20Kernel%20Implementation%20Evidence%20-%20v0.1.1.md). The earlier v0.1.0 candidate record is superseded.

The real first-person embodiment of those sealed records is recorded in [Unreal Materialization Proof Evidence — v0.1.0](Unreal%20Materialization%20Proof%20Evidence%20-%20v0.1.0.md). The Unreal project is `CityMaterializationProof/`; it has no strategic-simulation authority.

The bridge-access round trip is specified in [v0.1.1](Bridge%20Access%20Persistence%20Round-Trip%20Proof%20-%20Draft.md), with its reviewed original retained as [v0.1.0](Bridge%20Access%20Persistence%20Round-Trip%20Proof%20-%20v0.1.0.md). Its final implementation and passing evidence are recorded in [Bridge Access Persistence Round-Trip Evidence — v0.1.1](Bridge%20Access%20Persistence%20Round-Trip%20Evidence%20-%20v0.1.1.md); the original [evidence v0.1.0](Bridge%20Access%20Persistence%20Round-Trip%20Evidence%20-%20v0.1.0.md) remains inspectable.

The frozen [Bridge Access Traversal Contention Proof — v0.1.0](Bridge%20Access%20Traversal%20Contention%20Proof%20-%20Draft.md) has a retained original execution witness in [v0.1.0](Bridge%20Access%20Traversal%20Contention%20Proof%20Evidence%20-%20v0.1.0.md) and its final provenance-corrected evidence in [v0.1.1](Bridge%20Access%20Traversal%20Contention%20Proof%20Evidence%20-%20v0.1.1.md). It establishes only the documented contention semantics.

The sealed [Crew Deployment Opportunity-Cost Proof — v0.1.0](Crew%20Deployment%20Opportunity-Cost%20Proof%20-%20Draft.md) and its [evidence](Crew%20Deployment%20Opportunity-Cost%20Proof%20Evidence%20-%20v0.1.0.md) establish one shared deployment commitment, exact B/C physical evidence contracts, and the B/C/D opportunity-cost branches. They authorize no successor city scope.

## Product framing

This proof track serves a 1–4 player co-op open-city FPS. The crew receives incomplete intelligence, chooses where to deploy from a persistent hub, and pays active-world time for travel and intervention. The core player pressure is: **what do we answer, what do we delay, and what do we allow to happen without us?**

The city is not a mission generator with scripted incidents. The FPS layer is the high-resolution embodiment of the causal city machine: players later enter the routes, control, damage, services, resources, significant people, and counter-operations that the shared city record has established.

## Player-to-city mutation boundary

Players do not use the off-screen agent planner; their immediate actions resolve through the first-person simulation. A player-caused outcome becomes durable city state only when it crosses the same causal boundary as any other mutation:

```text
physical player action
  → detected consequential outcome
  → persistence gate and evidence
  → canonical mutation with crew/player provenance
  → thresholds and downstream eligibility update
```

Non-consequential local detail may disappear when an area is compressed. Durable outcomes—such as a blocked route, destroyed resource, captured significant person, altered control, or changed access—must enter the authoritative record through the deterministic transaction and causal ledger. Players therefore affect the same city machine without being reduced to abstract planner agents.

## Commitment lifecycle contract

Every time-bearing action is an explicit commitment with a canonical identifier, owner, start time, state, resource reservations, gate-check schedule, and terminal disposition. Its allowed lifecycle is:

```text
planned → active → succeeded | failed | cancelled
```

Traversal commitments additionally record route, current segment, deterministic progress, and exact last valid location. Route gates are tested at defined entry boundaries; a later closure cannot retroactively invalidate a segment already entered. Effects such as defensive pressure must be owned by, scoped to, and expire with a named commitment unless they are intentionally promoted to durable city state.

Every terminal transition must release, consume, transfer, or transform all reserved resources and record that disposition in the causal ledger. Reproducible but stale reservations are a simulation defect.

## Deterministic mutation and ordering law

Each strategic decision time is a transaction boundary. No agent, process, or front may mutate the authoritative city record directly while deciding what to do.

At a strategic decision time, resolve work in this order:

1. Identify due commitments and processes from the canonical city record.
2. Create one immutable start-of-boundary snapshot. Agents derive their observations, beliefs, and feasible actions from this snapshot only.
3. Produce action proposals without changing city state.
4. Sort proposals by a canonical execution key: decision time, simulation phase, target scope, action-class priority, a seed-derived tie-break value, actor/process identifier, commitment identifier, and action identifier.
5. Revalidate and commit proposals one at a time against the working record in that canonical order. A proposal that has become invalid must record its failed gate or unavailable resource; it must not silently mutate state.
6. Apply derived state, threshold crossings, and downstream eligibility changes in a final canonical phase. New commitments become eligible at their recorded next decision time.

The same snapshot gives simultaneous actors the same information. The canonical commit order makes resource conflicts and gate races deterministic. The rule also prevents a runtime container's iteration order from becoming hidden city law.

## Replay equivalence

The proof kernel must satisfy this reproducibility condition:

```text
same canonical authoritative initial record
+ same seed and deterministic random-draw sequence
+ same ordered player/input sequence
+ same simulation version and rule set
────────────────────────────────────────────
= byte-equivalent canonical causal record
```

Semantic equivalence is acceptable only where byte identity is intentionally unavailable; it must compare the same authoritative facts, causal-ledger entries, scheduled commitments, and derived eligibility state. A canonical serializer and stable identifier ordering are therefore required for the byte-equivalence proof.

## Mutation provenance

Every attempted or committed consequential mutation must append an inspectable causal-ledger entry containing:

- decision time, simulation phase, canonical execution sequence, and simulation version;
- actor or process identity, commitment identity, and action identity;
- snapshot reference plus the observed and believed inputs used for the decision;
- eligible action set, selected action, deterministic tie-break value, and any random-draw reference;
- resources reserved, consumed, transferred, or found unavailable;
- gates and thresholds evaluated, including their values and pass/fail result;
- the committed mutation or failed action result, with canonical pre-state and post-state references; and
- threshold crossings, derived effects, and downstream commitments or eligibility changes.

The ledger must allow a later inspection to reconstruct the complete causal chain without inferring intent from the final state alone.

## Changelog

### 0.7.0-draft.17 — 2026-08-26

- Implemented and sealed the crew deployment opportunity-cost proof: canonical deployment request and exclusivity, exact Unreal B/C evidence emission, autonomous fire/police/gang progression, deterministic B/C/D histories, and fresh final-record materialization.
- Proved that a single aircraft-bound crew spends one physical-evidence opportunity domain while active-world time advances unattended city processes.
- Preserved Unreal as proposal/materialization-only; the Python canonical transaction layer remains sole authority for deployment, durable mutations, and the causal ledger.
- No split-fireteam, intelligence, multiplayer, city-scale, or successor-system scope is authorized.

### 0.7.0-draft.16 — 2026-08-26

- Froze the crew deployment opportunity-cost proof: canonical deployment requests, one aircraft-bound crew commitment, exact B/C local evidence contracts, and a neutral D control branch.
- Fixed takeoff as the active-world-clock boundary; excluded split fireteams and intelligence variance.
- Historical freeze record. Implementation and evidence are recorded by draft.17; no city expansion is authorized.

### 0.7.0-draft.15 — 2026-08-26

- Corrected only the contention proof's cross-transaction provenance: `t1/15` now retains the t0 intermediate parent hash and a named scheduler-clock-advance derivation before revalidation.
- Corrected failed-entry resource provenance to record that no resource was acquired.
- Resealed the same contention behavior under new release identity; no traversal, ordering, authority, or city-law behavior changed.

### 0.7.0-draft.14 — 2026-08-26

- Implemented and passed the frozen bridge-access traversal contention proof: a captured Unreal crew proposal and a police E_AB entry resolve from one R0-bound canonical batch under either fixture ordering.
- Proved complete proposal authorization, lawful existing-lease traversal after later admission closure, a separately hashed t1/15 exit transaction, deterministic replay, and fresh Unreal materialization of both final records.
- Sealed the final artifact manifest and retained the explicit prohibition on city expansion or new systems.

### 0.7.0-draft.13 — 2026-08-26

- Froze Bridge Access Traversal Contention Proof v0.1.0 with exact simulation identity, batch-binding versus working-state hash semantics, and fixture-only ordering policy.
- Required complete physical-proposal authorization, a separate t1/15 exit transaction, adversarial rejection tests, full regressions, fresh materialization for both cases, and verifiable final artifact evidence.
- Authorized implementation only within the frozen contention-proof boundary; no adjacent city-system expansion is authorized.

### 0.7.0-draft.12 — 2026-08-26

- Prepared a specification-only proof for deterministic contention between a crew physical-consequence proposal and an already-due police E_AB entry proposal within one shared canonical decision boundary.
- Defined the candidate admission-versus-existing-lease clarification, destruction-first and entry-first cases, required intermediate evidence, and exact implementation boundary.
- No code, new city behavior, or implementation authority is established by this entry.

### 0.7.0-draft.11 — 2026-08-26

- Sealed the final rebuilt evidence set for the passed bridge-access round trip, including final source hashes, duplicate and replay artifact hashes, and fresh first-person rematerialization of the committed record.
- Retained v0.1.0 evidence as the original execution witness; the v0.1.1 evidence records only final visual/source hygiene, not new causal behavior or city law.

### 0.7.0-draft.10 — 2026-08-26

- Implemented the frozen bridge-access persistence round trip exactly: Unreal emits an evidence proposal; the canonical Python transaction layer validates all gates, commits or rejects atomically, and produces the only authoritative record.
- Proved accepted physical destruction, stale/duplicate rejection without record mutation, byte-equivalent canonical replay, original-process destruction, and fresh Unreal rematerialization from the committed record alone.
- Added a narrow authority audit that verifies Unreal proposal code cannot write a committed record or causal ledger.
- No new city-law behavior is established by this entry.

### 0.7.0-draft.9 — 2026-08-26

- Revised the frozen bridge-access proof to use record-relative optimistic concurrency (`proposal.source_record_hash == transaction.pre_state_hash`) rather than a fixture-named hash rule.
- Required all side-effect-free validation gates to be evaluated and ledgered before commit eligibility is decided, so stale and duplicate protections are independently inspectable.
- Preserved the original 0.1.0 specification as a historical record; no implementation or new city-law behavior is established by this entry.

### 0.7.0-draft.8 — 2026-08-26

- Froze the bridge-access persistence round-trip proof specification: a physical destruction proposal must be validated and committed only by the canonical transaction layer, then survive fresh rematerialization from the resulting record.
- Defined accepted and rejected proposal paths, provenance, idempotency, and the prohibition on Unreal mutating city state directly.
- No implementation or new city-law behavior is established by this entry.

### 0.7.0-draft.7 — 2026-08-26

- Authorized and completed `CityMaterializationProof`, a UE 5.8 first-person record-materialization proof for the frozen Ash Crossing primary and counterfactual records.
- Verified a collision floor at the proof map's zero elevation, deterministic player placement, and physical distinctions between the two authoritative records.
- Recorded the source hashes, successful build, causal-kernel regression result, and both runtime observations in the Unreal materialization evidence record.
- No new city-law behavior is established by this entry.

### 0.7.0-draft.6 — 2026-08-26

- Corrected the reference kernel's future-edge gating, mid-route terminal cleanup, believed-input provenance, and failed-dispatch state.
- Recorded eight passing conformance checks and superseded the earlier nonconformant candidate evidence.
- No new city-law behavior is established by this entry.

### 0.7.0-draft.5 — 2026-08-26

- Implemented the frozen Ash Crossing proof kernel as a dependency-free deterministic reference simulation.
- Recorded passing primary-run, counterfactual, traversal, cleanup, replay, provenance, and materialization evidence.
- No new city-law behavior is established by this entry.

### 0.7.0-draft.4 — 2026-08-26

- Established explicit commitment lifecycle, traversal, scoped-effect expiry, and terminal resource-disposition requirements.
- Marked the corrected three-area proof-kernel specification as frozen and ready for implementation.
- No new city-law behavior is established by this entry.

### 0.7.0-draft.3 — 2026-08-26

- Added the complete three-area causal proof-kernel specification as the sole implementation target for this phase.
- No new city-law behavior is established by this entry.

### 0.7.0-draft.2 — 2026-08-26

- Added non-normative product framing: the causal city machine is the game; the FPS layer embodies it locally.
- Defined the player-to-city mutation boundary for durable physical outcomes.
- No new city-law behavior is established by this entry.

### 0.7.0-draft.1 — 2026-08-26

- Established the deterministic mutation and ordering law for the proof kernel.
- Established replay-equivalence and per-mutation provenance as acceptance requirements.
- No new city-law behavior is established by this entry.

### 0.7.0-draft.0 — 2026-08-26

- Opened the working continuation from the frozen v0.6.0 record.
- No new simulation behavior is established by this entry.

## Next working unit

The frozen three-area kernel has passed its primary run, counterfactual, replay-equivalence record, causal ledger, materialization projection, real first-person materialization, and one complete physical-to-canonical-to-physical persistence round trip.

The crew deployment opportunity-cost proof has passed and is sealed. No successor scope follows from it automatically.

Do not revise the frozen kernel or add map scale, additional city systems, or scripted front outcomes without a new user-directed scope decision. The proven round trip is one consequence, not authority to expand city scope.
