# Canonical Occupancy Transition Proof Evidence

**Version:** 0.1.0
**Status:** Passed and sealed.
**Specification:** [Canonical Occupancy Transition Proof — v0.1.0](Canonical%20Occupancy%20Transition%20Proof%20-%20Draft.md)
**Payload schema:** `CanonicalOccupancyTransitionPayload.v1`
**Simulation identity:** `0.7.0-draft.65`
**Parent continuation:** [Co-op Open-City FPS Simulation — v0.7 Working Continuation](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)

## Claim tested

> **One canonically identified subject can leave one settled canonical site,
> enter one exact resource-owning canonical transition over canonical time,
> and settle at the other endpoint only through a later record-relative
> canonical completion boundary—without navigation, interpolation, Unreal, or
> representation state acquiring occupancy or completion authority.**

The proof is canonical-only. It does not claim physical traversal.

## Exact fixture

```text
R0 @ t0/00
occupancy = at_site(topology_site_0002)
commitment = planned
reservation = available
        ↓ Bstart bound to H0
Rtransit @ t0/30
occupancy = in_transition(occupancy_transition_0001)
commitment = active
reservation = reserved by exact transition
        ↓ fresh Bcomplete bound to Htransit
Rfinal @ t1/00
occupancy = at_site(topology_site_0001)
commitment = succeeded
reservation = released
        ↓
none
```

The blocked root uses the same transition definition and resolver path:

```text
R0_blocked
route access = blocked
        ↓ ordinary complete start-gate evaluation
Rblocked
occupancy unchanged at site_0002
commitment = failed(reason = failed_gate)
reservation never acquired
completion work absent
```

## Canonical checkpoint identities

```yaml
R0: b31e7ad0993e288ba80f50fb1960da5c67bad9bcc7cc39bf0ec0ebeeaad57dc8
R0_blocked: 55b9c7f1a0840b6618d96e99c7f4d0f754815622ee4f51ea1873425ab9164005
Rtransit: 2640fe567b343e2229f875c9cf2d081f41aaaec2a3834e81e2efb3f9caa5da19
Rfinal: 3a00d32115af74950923ac3362a8459d0e08043d45abbe91bcc573e27103db34
Rblocked: 5b69846d05255dd364790bfb7f277fe4a2b878318589eef359266d035e7514d9
```

Every successor contains only its predecessor hash and exact boundary witness.
No canonical record contains its own hash or a competing transaction header.

## Spatial and resource observations

The sealed Phase-1 topology R0 artifact was independently rebound by exact
SHA-256:

```text
5e57c04875cfaead69f4cd6aaffeee2f788a2c1f5a820a56fb7083f8f7e861ed
```

The available occupancy root carries that byte-identical spatial-topology
projection. The blocked root differs only in its route-access fact and truthful
genesis. Open and blocked transition-definition projections are byte-identical.

The singular occupancy tagged union produced exactly three lawful physical
relations:

```text
at_site(site_0002)
in_transition(transition_0001)
at_site(site_0001)
```

`in_transition` placed the subject at neither endpoint and created no route
occupancy, progress, geometry, segment, or arrival fact. The detached
inspection projection remained outside canonical serialization.

The fixture-local reservation lifecycle closed exactly:

```text
available → reserved_by(transition_0001) → available
```

The blocked branch never acquired it.

## Record-relative chronology

Completion was absent from R0 unresolved work. Accepted start privately built
and fully validated Rtransit, published it atomically, then terminated the
start context. Only a fresh scheduler query of published Rtransit's
`future_causal_state.unresolved_work` produced Bcomplete.

The source audit found:

- exactly one public `next_consequential_boundary(record)`;
- exactly one public `resolve_next_due(canonical_record, record_bound_boundary)`;
- no scheduler read of commitment completion time, genesis, historical
  `created_work`, cache, or trace;
- no resolver read of navigation, transform, coordinate, progress, arrival,
  Unreal, policy, or resolution-local state;
- completion-work construction confined to accepted-start schedule/provenance;
- no retained boundary, itinerary, provisional record, or local cache authority;
- no randomness and no successor self-hash.

## Resolution-policy equivalence

Two materially different local histories were replayed:

```text
BOUNDARY JUMP
R0 → start → Rtransit → completion → Rfinal

DENSE INSPECTION
R0 → local inspection → start → Rtransit
   → local inspection → completion → Rfinal
```

They are byte-identical at R0, both record-bound boundaries, Rtransit, Rfinal,
ledger, ancestry, reservations, future schedules, and terminal disposition.
Only the exact non-authoritative inspection trace differs.

## Failure and atomicity evidence

All **41/41** declared adversarial families are mechanically witnessed. They
cover exact schema/type identity, singular occupancy, topology relation,
record-bound capabilities, time equality, lifecycle coherence, resource
closure, schedule-copy non-authority, representation exclusion, and source
isolation.

All **30/30** exact private construction fault points reject before publication.
At every provisional write, the source bytes/hash and scheduler result remain
unchanged; no successor, ledger append, cache, global state, or provisional
authority escapes.

Blocked route access remains the sole demonstrated ordinary failed-gate
transaction. Malformed occupancy, reservation, topology, schedule, identity,
or capability state rejects diagnostically without canonical history.

## Verification

- Complete Python regression suite: **215/215 passing**.
- Focused occupancy-transition suite: **20/20 passing**.
- Deterministic artifacts: **19/19 regenerated**.
- Adversarial families: **41/41 passing**.
- Private fault points: **30/30 passing**.
- Self-excluding release package: **33/33 verified**.

Run the release verifier:

```sh
cd "/Users/boandersson/Desktop/Games/THE_CITY"
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/thecity_pycache \
  python3 proof_kernel/verify_canonical_occupancy_transition_release.py verify
```

## Boundary

This proves one canonical subject, two sites, one unordered route, one ordered
transition intent, one reservation, two strictly ordered boundaries, one
blocked control, and two local execution policies.

It does not prove Unreal occupancy materialization, physical traversal,
navigation, interpolation, coordinates, distance, speed, derived travel time,
route occupancy/capacity, interruption/rerouting, multiple subjects,
contention, external input, randomness, simultaneous physical domains,
networking, streaming, World Partition, production topology, or Phase 3.

## Changelog

### 0.1.0 — 2026-08-27

- Sealed the bounded canonical occupancy transition proof.
- Recorded singular occupancy, exact reservation lifecycle, Rtransit
  publication before record-relative completion rediscovery, blocked ordinary
  failure, dense/jump equivalence, replay, 41 adversarial families, 30 private
  fault points, source audit, and self-excluding release verification.
