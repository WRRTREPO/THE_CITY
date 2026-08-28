# THE_CITY Development Capacity and Progress Note

**Version:** 0.1.11
**Date:** 2026-08-27
**Status:** Recorded proof capacity only. This note grants no successor scope.
**Supersedes:** [v0.1.10](THE_CITY%20Development%20Capacity%20and%20Progress%20Note%20-%20v0.1.10.md)
**Governing record:** [Co-op Open-City FPS Simulation — v0.7 Working Continuation](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)

## Current position

THE_CITY has not proven a production city or physical movement system. It has
proven a bounded authority machine and now one explicit canonical occupancy
transition over the previously sealed two-site/one-route topology.

```text
canonical topology identity
        ↓
settled occupancy at site B
        ↓ canonical start boundary
exact in-transition relation + reservation
        ↓ fresh record-relative completion boundary
settled occupancy at site A + released reservation
```

Navigation, physical interpolation, Unreal Actors, coordinates, route
progress, and representation state do not own occupancy or completion.

## Inherited proven capacity

All capacity recorded in [v0.1.10](THE_CITY%20Development%20Capacity%20and%20Progress%20Note%20-%20v0.1.10.md)
remains proven only inside its sealed scopes:

- deterministic causal history and inspectable provenance;
- canonical-to-FPS materialization and FPS-evidence-to-canonical round trip;
- contention, deployment opportunity cost, live arrival, and historical finality;
- shared-state composition and bounded agent selection;
- resolution semantics, Causal-LOD equivalence, chronological rediscovery,
  external input interception, and same-clock successor semantics;
- integrated Unreal promotion/unload/repromotion;
- concurrent two-source external evidence arbitration; and
- canonical two-site/one-route spatial topology identity.

## New proven capacity

| Capacity | Proven boundary |
| --- | --- |
| Canonical occupancy transition — neutral fixture | One exact subject leaves `at_site(topology_site_0002)` through one R0-bound start, enters `in_transition(occupancy_transition_0001)` while one exact reservation is owned, then settles at `topology_site_0001` only after completion is freshly rediscovered from published Rtransit. A blocked route produces an ordinary failed gate with unchanged occupancy and no resource. Dense inspection and boundary jump match byte-identically at every checkpoint. |

The sealed evidence records:

```yaml
payload: CanonicalOccupancyTransitionPayload.v1
simulation_identity: 0.7.0-draft.65
canonical_records:
  - R0
  - R0_blocked
  - Rtransit
  - Rfinal
  - Rblocked
primary_boundaries: 2
blocked_control_boundaries: 1
canonical_subjects: 1
canonical_reservations: 1
local_execution_policies: 2
adversarial_families: 41
private_fault_points: 30
regression_checks: 215
focused_checks: 20
release_members: 33
```

## Progress record

```text
1.  CAUSAL HISTORY
2.  FPS MATERIALIZATION
3.  ROUND-TRIP PERSISTENCE
4.  TEMPORAL CONTENTION
5.  OPPORTUNITY COST
6.  LIVE ARRIVAL
7.  SHARED-STATE COMPOSITION
8.  BOUNDED AGENT SELECTION
9.  RESOLUTION SEMANTICS SUBSTRATE
10. CAUSAL-LOD EQUIVALENCE — NEUTRAL FIXTURE
11. RECORD-RELATIVE CHRONOLOGICAL RESOLUTION — NEUTRAL FIXTURE
12. EXTERNAL INPUT BOUNDARY — NEUTRAL FIXTURE
13. SAME-CLOCK SUCCESSOR SEMANTICS — NEUTRAL FIXTURE
14. INTEGRATED UNREAL PROMOTION → UNLOAD → REPROMOTION — NEUTRAL FIXTURE
15. CONCURRENT EXTERNAL EVIDENCE ARBITRATION — NEUTRAL FIXTURE
16. CANONICAL SPATIAL TOPOLOGY IDENTITY — NEUTRAL FIXTURE
17. CANONICAL OCCUPANCY TRANSITION — NEUTRAL FIXTURE
```

## Exact new operating envelope

```yaml
canonical_occupancy_transition:
  sites: 2 exact inherited site identities
  routes: 1 exact inherited unordered route relation
  subjects: 1
  occupancy_authority: 1 exact tagged union
  transitions: 1 ordered B-to-A fixture intent
  reservations: 1 subject-transition reservation
  consequential_boundaries: 2 strictly ordered
  blocked_control: 1 ordinary failed-gate transaction
  local_execution_histories: dense_inspection | boundary_jump
  unreal_processes: 0
  external_inputs: 0
  authoritative_random_draws: 0
```

## What `in_transition` now means

Within this sealed fixture only:

```text
in_transition(occupancy_transition_0001)
= settled-site occupancy is suspended
+ one exact active transition commitment owns one exact reservation
```

It does not mean route occupancy, a third place, coordinates, current segment,
progress, physical containment, route capacity use, or arrival.

## Not yet capacity

- Unreal occupancy materialization or physical traversal;
- navigation, animation, coordinates, interpolation, distance, speed, or
  derived travel time;
- route entry/exit, capacity, leases, traffic, congestion, collision, or
  production movement semantics;
- transition interruption, cancellation, rerouting, recovery, return, or
  mid-transition topology mutation;
- multiple subjects, occupancy contention, site exclusivity, split players,
  simultaneous physical domains, or Phase 3;
- live transport, networking, rollback, reconciliation, save/load, host
  migration, World Partition, streaming, population, or city scale;
- stochastic identity, generalized planners, production topology, or a
  generalized occupancy/movement resolver.

## Development rule

This seal closes Phase 2 only in the exact neutral canonical fixture. It does
not automatically select Phase 3. Any successor must identify one new risk,
freeze its authority and failure boundaries, and receive explicit scope.

## Changelog

### 0.1.11 — 2026-08-27

- Added the sealed Canonical Occupancy Transition Proof in its exact
  one-subject/two-site/one-route/one-reservation/two-boundary scope.
- Distinguished proven canonical occupancy transition from physical movement,
  traversal, navigation, representation, contention, simultaneous domains,
  networking, streaming, and production-scale occupancy systems.
