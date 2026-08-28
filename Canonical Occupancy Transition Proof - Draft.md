# Canonical Occupancy Transition Proof

**Version:** 0.1.0
**Status:** Frozen specification; bounded canonical implementation authorized
**Selected:** 2026-08-27
**Parent continuation:** [Co-op Open-City FPS Simulation — v0.7 Working Continuation](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)
**Latest sealed predecessor:** [Canonical Spatial Topology Identity Proof — v0.1.0](Canonical%20Spatial%20Topology%20Identity%20Proof%20Evidence%20-%20v0.1.0.md)
**External program framing:** `The PROBLEM to solve v1.1 — Causal Continuity Under Distribution`, SHA-256 `de080c065006ccaf5899cca12c98a3f10a72a62176a265204b04521f9031aa07`; non-authoritative and not a repository release member
**Frozen payload schema:** `CanonicalOccupancyTransitionPayload.v1`
**Frozen simulation identity:** `0.7.0-draft.65`

## Question

> **Can one canonically identified subject leave settled occupancy at one
> canonical site, remain authoritatively in one exact transition over
> canonical time, and later settle at the other endpoint of one canonical
> route without navigation, physical interpolation, conceptual labels, or
> representation state acquiring authority over canonical occupancy or
> completion?**

The intended bounded chain is:

```text
R0 @ t0/00
subject settled at canonical site B
transition planned
        ↓
discover start @ t0/30 from R0
        ↓
ordinary topology + occupancy gates pass
reserve the subject's transition reservation
        ↓
Rtransit @ t0/30
subject canonically in transition
completion work now exists
        ↓
discard every R0-bound scheduler product
rediscover completion from Rtransit
        ↓
complete @ t1/00 without nav/interpolation input
release the reservation
        ↓
Rfinal @ t1/00
subject settled at canonical site A
```

This proof establishes a canonical occupancy-transition lifecycle. It does not
establish physical traversal, travel simulation, animation, route progress,
distance, speed, pathfinding, or arrival detection.

## Program position

The Phase 1 dependency is sealed:

```text
CONCEPTUAL GEOGRAPHY
        ≠
CANONICAL TOPOLOGY
        ≠
PHYSICAL REPRESENTATION
```

Phase 2 adds only this relation:

```text
CANONICAL SUBJECT
        ↓ singular tagged occupancy
AT CANONICAL SITE
        ↓ record-bound transition commitment
IN CANONICAL TRANSITION
        ↓ later record-bound completion
AT CANONICAL SITE
```

The named external thesis charter supplies only the Phase 2 dependency
objective. Its embedded current-state snapshot is historical and superseded by
the governing continuation. It grants no runtime authority and is not a release
member. The governing continuation and this reviewed proof contract remain the
repository authority.

## Novelty boundary

This is not the repository's first fixture-local location change. Earlier
kernel and contention proofs moved a police fixture through authored route and
lease semantics. This proof asks a different, narrower modern-machine
question:

> Can the exact Phase 1 topology identity law be extended under a new payload
> identity with one singular, referentially valid canonical occupancy state
> and one record-relative transition lifecycle?

It does not generalize earlier `location`, segment, traversal, or lease fields.
It does not claim that the Phase 2 genesis record is a child of a Phase 1
record. It reuses the sealed proof-local topology ID values under a new exact
payload and simulation identity.

The freeze/implementation oracle must mechanically extract
`current_causal_state.spatial_topology` from the sealed predecessor artifact
`proof_kernel/CanonicalSpatialTopologyIdentityProofRecords/canonical_topology_R0.json`
and require canonical-JSON byte identity with the available topology in this
proof's R0. For `R0_blocked`, the site identities, route identity, endpoint
semantics, and endpoint pair must match that predecessor projection exactly;
only the explicitly declared access fact differs. This detached comparison is
release evidence, not runtime ancestry or a second topology authority.

Deployment destination and clock-derived physical access are not occupancy.
Area ownership and control are not occupancy. Actor transform and collision
containment are not occupancy.

## Scope

```yaml
proof_scope:
  canonical_sites: 2
  canonical_routes: 1
  canonical_subjects: 1
  occupancy_transition_commitments: 1
  primary_boundaries: 2
  blocked_control_boundaries: 1
  canonical_resources: 1 fixture-local subject-transition reservation
  authoritative_random_draws: none
  external_inputs: none
  unreal_processes: none
  implementation_authority: bounded_canonical_only
```

The proof is canonical-only. Phase 1's real UE evidence remains predecessor
evidence for representation separation; this proof does not reopen its adapter
or create an occupancy materializer.

## Governing laws

### One singular authoritative occupancy

Exactly one canonical field owns the subject's current occupancy:

```yaml
canonical_occupancy:
  topology_occupant_0001:
    kind: at_site
    site_id: topology_site_0002
```

or:

```yaml
canonical_occupancy:
  topology_occupant_0001:
    kind: in_transition
    transition_id: occupancy_transition_0001
```

This is an exact tagged union.

```text
kind = at_site
→ exact keys: kind, site_id

kind = in_transition
→ exact keys: kind, transition_id
```

No canonical `subject.location`, `site.occupants`, coordinate, transform,
progress, current segment, or second occupancy index may coexist with this
relation. A detached site-to-subject projection may be computed for inspection,
but it is not authoritative input and is never persisted inside the envelope.

### Occupancy is settled location or exact transition identity

For this proof:

```text
canonical occupancy
= exactly one subject's authoritative spatial relation
= at one canonical site OR in one exact canonical transition
```

It does not mean:

```text
coordinates
physical containment
Actor transform
navigation position
route progress
ownership or control
site capacity
```

`in_transition` is not missing authority or an unknown-location error. It
asserts only that settled-site occupancy is suspended under the exact
referenced active transition commitment. It asserts no canonical place, route
occupancy, route-capacity use, geometric position, segment, progress, or
physical containment. The subject is canonically at neither endpoint while
this tag is active.

```text
commitment.route_id
    = transition eligibility and provenance reference

commitment.route_id
    ≠ current occupancy container
```

If a detached inspection projection is produced, its result is exact:

```yaml
at_site_topology_site_0002:
  site_projection:
    topology_site_0001: []
    topology_site_0002:
      - topology_occupant_0001
  detached_transition_relation: null

at_site_topology_site_0001:
  site_projection:
    topology_site_0001:
      - topology_occupant_0001
    topology_site_0002: []
  detached_transition_relation: null

in_transition_occupancy_transition_0001:
  site_projection:
    topology_site_0001: []
    topology_site_0002: []
  detached_transition_relation:
    topology_occupant_0001: occupancy_transition_0001
```

This projection is never serialized into canonical authority and cannot place
the subject at the origin, destination, both endpoints, or the route.

### Route relation and transition intent are different laws

The route remains the unordered Phase 1 relation:

```yaml
endpoint_semantics: unordered_pair_fixture_only
endpoint_site_ids:
  - topology_site_0001
  - topology_site_0002
```

The transition intent is ordered:

```yaml
origin_site_id: topology_site_0002
destination_site_id: topology_site_0001
```

The reverse lexical orientation is deliberate. Only a copy of
`[origin_site_id, destination_site_id]` is normalized to compare with the
stored route pair. Origin and destination are never reordered or rewritten.

Therefore:

```text
route storage order
≠ route direction
≠ transition intent order
```

This fixture demonstrates one B-to-A transition. It does not establish
production directionality or generalized bidirectionality.

### Completion belongs to canonical time

The transition has two explicit consequential boundaries:

```text
start:      t0/30, phase 10
completion: t1/00, phase 10
```

The payload admits exactly the ordered fixture time tokens
`t0/00 < t0/30 < t1/00`. This is an exhaustive proof-local ordering table, not
a generalized clock parser or calendar law.

The completion time is an exact proof-fixture schedule, not a distance-,
speed-, navigation-, animation-, or travel-cost calculation.

The canonical scheduler alone discovers completion from `Rtransit`.
Resolution-local inspection may occur between the boundaries, or nothing may
execute there. Neither history may create a canonical clock mutation, progress
fact, arrival fact, gate result, ledger entry, or completion capability.

### Record-relative continuation

The start boundary is bound to `H0 = canonical_hash(R0)`. It becomes stale when
`Rtransit` commits, even though it created the later work.

Completion is absent from R0. Only the committed `Rtransit` schedule may make
it discoverable:

```text
resolve start from R0
→ publish Rtransit
→ discard prior boundary authority
→ next_consequential_boundary(Rtransit)
→ completion boundary bound to Htransit
```

There is no precomputed itinerary.

R0 carries the commitment's declared `canonical_completion_time` as canonical
schedule-definition input, but it is not independently discoverable scheduling
authority: it is not a due-work member, boundary, or capability. Accepted start
resolution must read that exact value when it writes completion work into
`Rtransit.future_causal_state.unresolved_work`; only the committed work then
becomes discoverable scheduling authority.

The scheduler has exactly one authoritative read surface:

```text
next_consequential_boundary(record)
    reads record.future_causal_state.unresolved_work only
```

“Only” governs discovery of candidate work. The scheduler still validates the
canonical clock lower bound and hashes the complete queried record to bind the
boundary capability; neither operation may create or resurrect work.

It must never discover work from:

```text
commitment canonical_start_time or canonical_completion_time
fixture_genesis or initial_work_projection
historical ledger schedule_effect or created_work
resolution-local trace or cache
resolver-local candidate state
retained start context or itinerary
```

Those canonical duplicates are definition or provenance consistency witnesses.
They must agree where the schema requires, but none may repair, repopulate, or
substitute for `unresolved_work`.

The start publication barrier is exact:

```text
resolve_next_due(R0, Bstart)
    → construct candidate Rtransit privately
    → validate the complete candidate
    → hash the complete candidate and atomically publish Rtransit only
    → Bstart loses authority because the canonical record identity changed
    → terminate the start-resolution context

next_consequential_boundary(Rtransit)
    → independently discover Bcomplete bound to Htransit
```

The start resolver may not return `(Rtransit, Bcomplete)`, return an itinerary,
call scheduler discovery on an unpublished candidate, or retain a reusable
completion object. A private candidate has no published canonical authority
and cannot be a scheduler source.

### Time-field equality and non-repair

Every duplicated time representation is a consistency witness, not an
alternate clock authority:

```text
R0 commitment.canonical_start_time
    = R0 start work.decision_time
    = discovered start boundary.decision_time

accepted start creates completion work where:
Rtransit completion work.decision_time
    = commitment.canonical_completion_time

every successor canonical_clock
    = its resolved boundary.decision_time
```

A mismatch is a structural rejection before mutation. The scheduler may not
repair the commitment from work, repair work from the commitment, or choose
one representation as a hidden priority source.

### Reservation and terminal disposition

The proof contains one fixture-local exclusive subject-transition reservation:

```yaml
occupancy_transition_reservations:
  occupancy_reservation_topology_occupant_0001:
    occupant_id: topology_occupant_0001
    state: available
    owner_transition_id: null
```

Successful start reserves it for `occupancy_transition_0001`. Successful
completion releases it. A blocked start acquires nothing. Every terminal path
records one exact disposition:

```text
success → release_subject_transition_reservation
failed start → no_resource_acquired
```

This is not a route lease, site capacity, deployment reservation, movement
system, or generalized exclusivity model.

`fixture_genesis.initial_transition_reservation` is immutable provenance only;
it is never read as current allocation or gate authority. The current
`occupancy_transition_reservations` registry alone owns present reservation
state. `commitment.resources_owned` is the commitment-side consistency index
that must agree with that registry; it is not an alternate resource registry.

### Commitment owner and lifecycle refinement

The subject owns its own transition commitment in this neutral fixture. There
is no second agent, planner, driver, vehicle, or representation owner:

```yaml
owner_occupant_id: topology_occupant_0001
```

The exact serialized fixture transitions align with the governing commitment
law:

```text
planned → active → succeeded
planned → failed (terminal_reason = failed_gate)
```

`cancelled` remains a lawful governing terminal class but is outside this
fixture. An `active → failed` path is likewise not demonstrated here.
`failed_gate` is not a competing lifecycle state; it is the exact terminal
reason recorded when this fixture reaches `failed` directly from `planned`
through the blocked-route gate:

```yaml
state: failed
terminal_reason: failed_gate
```

For `planned`, `active`, and `succeeded`, `terminal_reason` is `null`. This
refinement cannot be changed without a new payload and simulation identity.

### Exhaustive lifecycle coherence matrix

The exact payload validator admits only these cross-field combinations. Every
other mixture rejects before boundary discovery or canonical mutation.

| Record | Occupancy | Commitment | Reservation | Clock | Exact unresolved work |
|---|---|---|---|---|---|
| `R0` / `R0_blocked` | `at_site(topology_site_0002)` | `planned`, no resources, reason/disposition `null` | available, owner `null` | `t0/00` | start only at `t0/30`, phase 10 |
| `Rtransit` | `in_transition(occupancy_transition_0001)` | `active`, owns exact reservation, reason/disposition `null` | reserved by exact transition | `t0/30` | completion only at `t1/00`, phase 10 |
| `Rfinal` | `at_site(topology_site_0001)` | `succeeded`, no resources, reason `null`, disposition `release_subject_transition_reservation` | available, owner `null` | `t1/00` | none |
| `Rblocked` | `at_site(topology_site_0002)` | `failed`, no resources, reason `failed_gate`, disposition `no_resource_acquired` | available, owner `null` | `t0/30` | none |

The validator also requires these exact identity couplings:

```text
canonical_occupancy key
    = commitment.owner_occupant_id
    = reservation.occupant_id

reservation table key
    = the sole member of commitment.resources_owned when active

reservation.owner_transition_id
    = occupancy.transition_id
    = commitment table key
    when and only when the commitment is active

reservation available
    ⇔ owner_transition_id is null
       and resources_owned is empty
```

The blocked root differs from the open root only in route access and truthful
genesis access. It otherwise occupies the same matrix row.

## Exact identity value spaces

The frozen payload admits only these proof-local values:

```yaml
CanonicalSiteId.v1:
  - topology_site_0001
  - topology_site_0002

CanonicalRouteId.v1:
  - topology_route_0001

CanonicalOccupantId.v1:
  - topology_occupant_0001

CanonicalOccupancyTransitionId.v1:
  - occupancy_transition_0001

CanonicalOccupancyReservationId.v1:
  - occupancy_reservation_topology_occupant_0001

CanonicalOccupancyWorkId.v1:
  - t0/30/occupancy/occupancy_transition_0001.start
  - t1/00/occupancy/occupancy_transition_0001.complete
```

These types are disjoint even where strings are structurally similar. A site
ID cannot be used as a subject, route, transition, resource, process, or work
ID. Display labels, conceptual-map identities, Unreal Actor names, navigation
IDs, level IDs, transforms, streaming cells, and coordinates are outside every
canonical value space.

## Frozen record identity

Every record in this proof uses:

```yaml
identity:
  record_schema: CanonicalResolutionEnvelope.v1
  payload_schema: CanonicalOccupancyTransitionPayload.v1
  scenario_id: canonical-occupancy-transition-v1
  scenario_version: 0.1.0
  simulation_version: 0.7.0-draft.65
  seed: canonical-occupancy-transition-v1/0001
```

This identity is frozen for the bounded implementation. A changed
authoritative field, ordering law, gate, or lifecycle rule requires a new
payload/simulation identity and a separately reviewed freeze before
implementation.

## Exact R0 shape

R0 is a new fixture genesis, not a Phase 1 successor.

The stored JSON root contains exactly `identity`, `current_causal_state`,
`future_causal_state`, and `causal_provenance`. There is no serialized
`canonical_envelope` wrapper.

```yaml
identity:
  record_schema: CanonicalResolutionEnvelope.v1
  payload_schema: CanonicalOccupancyTransitionPayload.v1
  scenario_id: canonical-occupancy-transition-v1
  scenario_version: 0.1.0
  simulation_version: 0.7.0-draft.65
  seed: canonical-occupancy-transition-v1/0001

current_causal_state:
  spatial_topology:
    sites:
      topology_site_0001: null
      topology_site_0002: null
    routes:
      topology_route_0001:
        endpoint_semantics: unordered_pair_fixture_only
        endpoint_site_ids:
          - topology_site_0001
          - topology_site_0002
        access_state: available

  canonical_occupancy:
    topology_occupant_0001:
      kind: at_site
      site_id: topology_site_0002

  occupancy_transition_commitments:
    occupancy_transition_0001:
      owner_occupant_id: topology_occupant_0001
      origin_site_id: topology_site_0002
      destination_site_id: topology_site_0001
      route_id: topology_route_0001
      canonical_start_time: t0/30
      canonical_completion_time: t1/00
      state: planned
      resources_owned: []
      terminal_reason: null
      terminal_resource_disposition: null

  occupancy_transition_reservations:
    occupancy_reservation_topology_occupant_0001:
      occupant_id: topology_occupant_0001
      state: available
      owner_transition_id: null

future_causal_state:
  canonical_clock: t0/00
  unresolved_work:
    - work_id: t0/30/occupancy/occupancy_transition_0001.start
      decision_time: t0/30
      simulation_phase: 10
      transition_id: occupancy_transition_0001
      action: start

causal_provenance:
  fixture_genesis:
    genesis_schema: CanonicalOccupancyTransitionFixtureGenesis.v1
    source: frozen_initial_fixture
    initial_topology:
      sites:
        topology_site_0001: null
        topology_site_0002: null
      routes:
        topology_route_0001:
          endpoint_semantics: unordered_pair_fixture_only
          endpoint_site_ids:
            - topology_site_0001
            - topology_site_0002
          access_state: available
    initial_occupancy:
      topology_occupant_0001:
        kind: at_site
        site_id: topology_site_0002
    initial_transition_definition:
      occupancy_transition_0001:
        owner_occupant_id: topology_occupant_0001
        origin_site_id: topology_site_0002
        destination_site_id: topology_site_0001
        route_id: topology_route_0001
        canonical_start_time: t0/30
        canonical_completion_time: t1/00
        state: planned
        resources_owned: []
        terminal_reason: null
        terminal_resource_disposition: null
    initial_transition_reservation:
      occupancy_reservation_topology_occupant_0001:
        occupant_id: topology_occupant_0001
        state: available
        owner_transition_id: null
    initial_work_projection:
      work_id: t0/30/occupancy/occupancy_transition_0001.start
      decision_time: t0/30
      simulation_phase: 10
      transition_id: occupancy_transition_0001
      action: start
  authoritative_causal_ledger: []
  canonical_ancestry: null
```

The exact stored JSON uses UTF-8, no BOM, one terminal LF, sorted object keys,
compact separators, `ensure_ascii = true`, strict JSON literals,
duplicate-member rejection, and `allow_nan = false`. Canonical identity is
`SHA-256(canonical_json(the exact four-key root object))`.

## Blocked-control R0

`R0_blocked` uses the same identity, topology IDs, transition definition,
occupancy, reservation, work, and rules. Its only gate-relevant current-state
difference is:

```yaml
spatial_topology:
  routes:
    topology_route_0001:
      access_state: blocked
```

Its genesis truthfully records blocked initial access. No branch selector,
expected outcome, alternate resolver, or scenario-specific priority enters the
canonical record.

`R0` and `R0_blocked` are two independently supplied, exact sealed fixture
roots. They share payload identity and deterministic seed because neither
randomness nor a seed-selected generator constructs them. The seed does not
uniquely identify genesis state. The harness may select one of the two named
root artifacts as an explicit test input, but it may not derive, toggle, or
rewrite one root from the other through a hidden variant flag. Their complete
transition-definition projections must hash byte-identically. The projection
is exactly the canonical JSON of
`current_causal_state.occupancy_transition_commitments.occupancy_transition_0001`;
route access and genesis metadata are outside that projection.

## Scheduler interfaces

The scheduler interface remains:

```text
next_consequential_boundary(canonical_record)
→ earliest unresolved (decision_time, simulation_phase)
→ complete work_id-ordered due set
→ record-bound boundary capability
```

The exact boundary schema is:

```yaml
boundary_schema: CanonicalOccupancyTransitionBoundary.v1
source_record_hash: CanonicalRecordHash.v1 of the exact queried record
decision_time: t0/30 | t1/00
simulation_phase: 10
due_work_ids:
  - exact sole work ID whose decision_time and action match this boundary
```

The fixture contains exactly one member at each demonstrated boundary. This
does not generalize multi-member batching.

The exact scheduler oracle is:

| Canonical record | Required result |
|---|---|
| `R0` | start at `t0/30`, phase 10, due set `[...start]`, source `H0` |
| `Rtransit` | completion at `t1/00`, phase 10, due set `[...complete]`, source `Htransit` |
| `Rfinal` | `none` |
| `R0_blocked` | start at `t0/30`, phase 10, due set `[...start]`, source `H0_blocked` |
| `Rblocked` | `none` |

These rows are also negative authority witnesses:

```text
R0 contains canonical_completion_time
    → completion is not discoverable

Rfinal retains commitment definition and historical start-ledger created_work
    → consumed completion does not reappear

Rblocked retains commitment definition
    → rejected start creates no completion eligibility
```

Dense-inspection and boundary-jump witnesses must return byte-identical
boundary objects at every matching canonical checkpoint, not merely identical
terminal records.

The only resolution entry point is:

```text
resolve_next_due(canonical_record, record_bound_boundary)
```

It accepts no navigation result, transform, coordinate, progress sample,
arrival flag, local clock, resolution trace, or representation state. Start,
ordinary gate failure, and completion are action members of this one declared
canonical path; there is no alternate arrival or completion API.

## Structural binding versus ordinary revalidation

Before any ordinary gate is evaluated, the validator must establish:

```yaml
structural_binding:
  - exact payload, identity, and lifecycle-matrix row
  - exact type-disjoint owner, site, route, transition, reservation, and work IDs
  - distinct origin and destination
  - referenced route and endpoint sites exist
  - normalize_copy([origin, destination]) == stored route endpoint pair
  - work action, transition ID, time, phase, and boundary source all agree
  - duplicated commitment/work/boundary times satisfy the equality law
  - topology is byte-identical to the selected exact root topology projection
    except for the selected root's frozen available-or-blocked access fact
```

Failure here is diagnostic-only structural rejection: no successor and no
canonical ledger entry.

The start transaction then revalidates the ordinary current-state gates:

```yaml
ordinary_start_gates:
  - commitment.state == planned
  - occupant occupancy == {kind: at_site, site_id: origin_site_id}
  - route.access_state == available
  - exact subject transition reservation.state == available
```

All ordinary gates are evaluated without short-circuiting. In the admitted
fixture value space, only route access may differ between two structurally
valid start roots. Blocked access therefore reaches one ordinary canonical
`failed` transaction with reason `failed_gate`; malformed identity, topology,
timing, occupancy, reservation, or schedule combinations do not.

## Start transaction

From available R0, start revalidates all ordinary facts from the exact R0
pre-state:

```yaml
ordinary_start_gates:
  - commitment.state == planned
  - occupant occupancy == {kind: at_site, site_id: topology_site_0002}
  - route.access_state == available
  - exact subject transition reservation.state == available
```

All gates are evaluated without short-circuiting after structural record and
boundary validation succeeds.

On acceptance, one atomic successor performs all of these changes:

```yaml
occupancy:
  prior:
    kind: at_site
    site_id: topology_site_0002
  successor:
    kind: in_transition
    transition_id: occupancy_transition_0001

commitment:
  state: active
  resources_owned:
    - occupancy_reservation_topology_occupant_0001
  terminal_reason: null
  terminal_resource_disposition: null

transition_reservation:
  state: reserved
  owner_transition_id: occupancy_transition_0001

schedule:
  consume: t0/30/occupancy/occupancy_transition_0001.start
  create: t1/00/occupancy/occupancy_transition_0001.complete

clock: t0/30
provenance: append exact start ledger entry
ancestry: parent H0
```

No canonical progress field or intermediate physical location is created.

## Rtransit

The exact authoritative state after start contains:

```yaml
canonical_occupancy:
  topology_occupant_0001:
    kind: in_transition
    transition_id: occupancy_transition_0001

occupancy_transition_commitments:
  occupancy_transition_0001:
    owner_occupant_id: topology_occupant_0001
    origin_site_id: topology_site_0002
    destination_site_id: topology_site_0001
    route_id: topology_route_0001
    canonical_start_time: t0/30
    canonical_completion_time: t1/00
    state: active
    resources_owned:
      - occupancy_reservation_topology_occupant_0001
    terminal_reason: null
    terminal_resource_disposition: null

occupancy_transition_reservations:
  occupancy_reservation_topology_occupant_0001:
    occupant_id: topology_occupant_0001
    state: reserved
    owner_transition_id: occupancy_transition_0001

future_causal_state:
  canonical_clock: t0/30
  unresolved_work:
    - work_id: t1/00/occupancy/occupancy_transition_0001.complete
      decision_time: t1/00
      simulation_phase: 10
      transition_id: occupancy_transition_0001
      action: complete
```

Topology remains byte-identical to R0. Completion work was not present in R0.

## Completion transaction

Completion is discovered only from `Rtransit` and revalidates:

```yaml
completion_gates:
  - commitment.state == active
  - canonical occupancy == {kind: in_transition, transition_id: occupancy_transition_0001}
  - transition reservation.state == reserved
  - transition reservation.owner_transition_id == occupancy_transition_0001
  - commitment.resources_owned == [occupancy_reservation_topology_occupant_0001]
```

Route access is a start-admission fact in this fixture. No route fact changes
between start and completion. Mid-transition route closure and its disposition
are explicitly outside scope.

On acceptance, one atomic successor performs:

```yaml
occupancy:
  prior:
    kind: in_transition
    transition_id: occupancy_transition_0001
  successor:
    kind: at_site
    site_id: topology_site_0001

commitment:
  state: succeeded
  resources_owned: []
  terminal_reason: null
  terminal_resource_disposition: release_subject_transition_reservation

transition_reservation:
  state: available
  owner_transition_id: null

schedule: consume completion; create nothing
clock: t1/00
provenance: append exact completion ledger entry
ancestry: parent Htransit
```

`next_consequential_boundary(Rfinal)` returns `none`.

## Rfinal

The complete primary terminal current/future projections are:

```yaml
canonical_occupancy:
  topology_occupant_0001:
    kind: at_site
    site_id: topology_site_0001

occupancy_transition_commitments:
  occupancy_transition_0001:
    owner_occupant_id: topology_occupant_0001
    origin_site_id: topology_site_0002
    destination_site_id: topology_site_0001
    route_id: topology_route_0001
    canonical_start_time: t0/30
    canonical_completion_time: t1/00
    state: succeeded
    resources_owned: []
    terminal_reason: null
    terminal_resource_disposition: release_subject_transition_reservation

occupancy_transition_reservations:
  occupancy_reservation_topology_occupant_0001:
    occupant_id: topology_occupant_0001
    state: available
    owner_transition_id: null

future_causal_state:
  canonical_clock: t1/00
  unresolved_work: []
```

Identity, available topology, fixture genesis, prior start ledger, exact
completion ledger, and immediate ancestry follow the exact checkpoint
construction and provenance laws below.

## Blocked ordinary failure

The blocked record is structurally valid and reaches canonical resolution.
Every start gate is evaluated. Only ordinary route access fails.

One atomic `Rblocked` successor must:

```yaml
canonical_occupancy:
  topology_occupant_0001:
    kind: at_site
    site_id: topology_site_0002

occupancy_transition_commitments:
  occupancy_transition_0001:
    owner_occupant_id: topology_occupant_0001
    origin_site_id: topology_site_0002
    destination_site_id: topology_site_0001
    route_id: topology_route_0001
    canonical_start_time: t0/30
    canonical_completion_time: t1/00
    state: failed
    resources_owned: []
    terminal_reason: failed_gate
    terminal_resource_disposition: no_resource_acquired

occupancy_transition_reservations:
  occupancy_reservation_topology_occupant_0001:
    occupant_id: topology_occupant_0001
    state: available
    owner_transition_id: null

future_causal_state:
  canonical_clock: t0/30
  unresolved_work: []
```

It appends ordinary canonical provenance and ancestry. It does not create
completion work. A blocked gate is not a structural rejection.

## Exact checkpoint construction law

Successor shapes are exhaustive transformations, not partial examples:

```text
Rtransit
  = exact deep copy of R0
  + only the accepted-start changes enumerated above
  + exact start ledger append
  + canonical_ancestry bound to H0

Rfinal
  = exact deep copy of Rtransit
  + only the completion changes enumerated above
  + exact completion ledger append
  + canonical_ancestry rebound to Htransit

Rblocked
  = exact deep copy of R0_blocked
  + only the failed-start changes enumerated above
  + exact blocked ledger append
  + canonical_ancestry bound to H0_blocked
```

In every successor, `identity` and `fixture_genesis` remain byte-identical to
their selected root. Primary topology remains the exact available topology at
R0, Rtransit, and Rfinal. Control topology remains the exact blocked topology
at R0_blocked and Rblocked. Any active or terminal primary record with changed
site identity, route identity, endpoints, endpoint semantics, or access state
is structurally invalid. Mid-transition topology mutation is excluded, not an
alternate completion outcome.

The complete legal records are therefore determined by the exact root, the
exhaustive lifecycle matrix, the enumerated transaction delta, and the exact
ledger/ancestry schemas below. No omitted field may be defaulted, inferred
from local state, or retained from a different checkpoint.

## Local execution-policy witnesses

Two non-authoritative execution histories must produce byte-identical primary
checkpoints:

```text
BOUNDARY JUMP
R0 → query Bstart → start → publish Rtransit
   → query Bcomplete from Rtransit → completion → Rfinal

DENSE INSPECTION
R0 → inspection_before_start_0001 → query Bstart → start
   → publish Rtransit → inspection_between_boundaries_0001
   → query Bcomplete from Rtransit → completion → Rfinal
```

The dense witness contains exactly two non-authoritative records, each with
exactly these keys:

```yaml
trace_schema: CanonicalOccupancyResolutionLocalInspection.v1
inspection_id: inspection_before_start_0001 | inspection_between_boundaries_0001
source_record_hash: H0 | Htransit
```

The boundary-jump witness contains zero local inspection records. Local
inspection records may contain only the exact diagnostic identity and
canonical source hash above. They may not contain or calculate
authoritative progress, position, arrival, gate results, resource disposition,
future schedule, or a reusable boundary capability.

In both histories, the completion query occurs only after Rtransit publication.
Dense inspection may delay that query but may not precompute or cache its
result.

The canonical oracle requires byte identity at R0, Rtransit, and Rfinal,
including hashes, complete ledgers, ancestry, resources, and future schedule.

## Provenance

There is one canonical ledger representation. No separate transaction header
owns competing authority.

The start entry must record:

- exact R0 pre-state hash and R0-bound boundary;
- ordered origin and destination intent;
- observed singular at-site occupancy;
- observed route ID, normalized endpoint comparison, and access state;
- every gate and result;
- acquired subject-transition reservation;
- occupancy, commitment, reservation, clock, and schedule mutations; and
- successor commitment state `active` with resource effect
  `reserve_subject_transition_reservation`.

The completion entry must record:

- exact Rtransit pre-state hash and Rtransit-bound boundary;
- observed active commitment, in-transition relation, reservation, and owned
  resource;
- every completion gate and result;
- the occupancy settlement at the destination;
- resource release, commitment terminalization, clock, and work consumption;
  and
- terminal disposition `release_subject_transition_reservation`.

The blocked entry must record:

- exact blocked-R0 pre-state hash and boundary;
- the complete start-gate observations, including blocked access;
- no occupancy mutation;
- no resource acquisition;
- commitment terminalization to `failed` with reason `failed_gate`; and
- terminal disposition `no_resource_acquired`.

Every canonical ledger entry has exactly this field contract:

```yaml
ledger_schema: CanonicalOccupancyTransitionLedgerEntry.v1
transaction_id: t0/30/phase_10/occupancy_transition_0001.start |
  t1/00/phase_10/occupancy_transition_0001.complete
ledger_sequence: 1 | 2
resolver_path_id: canonical_occupancy_transition.resolve_next_due.v1
canonical_execution_sequence: 0
simulation_version: 0.7.0-draft.65
owner_occupant_id: topology_occupant_0001
transition_id: occupancy_transition_0001
work_id: t0/30/occupancy/occupancy_transition_0001.start |
  t1/00/occupancy/occupancy_transition_0001.complete
action: start | complete
decision_time: t0/30 | t1/00
simulation_phase: 10
canonical_pre_state_hash: CanonicalRecordHash.v1 of the exact source record
source_boundary: CanonicalOccupancyTransitionBoundary.v1 bound to that hash
due_work_ids:
  - same exact value as work_id
snapshot_reference: same exact value as canonical_pre_state_hash
belief_inputs: not_applicable
eligible_action_set:
  - same exact value as work_id
selected_action: same exact value as work_id
deterministic_tie_break: none
random_draw_reference: none
threshold_evaluations: []
structural_validation: passed
transition_observation:
  origin_site_id: topology_site_0002
  destination_site_id: topology_site_0001
  route_id: topology_route_0001
  stored_endpoint_site_ids:
    - topology_site_0001
    - topology_site_0002
  normalized_transition_site_ids:
    - topology_site_0001
    - topology_site_0002
reservation_id: occupancy_reservation_topology_occupant_0001
gate_observations: exact start-or-completion array below, selected by action
result: started | failed_gate | completed
state_effects: exact result-specific projection below
resource_effect: reserve_subject_transition_reservation | no_resource_acquired |
  release_subject_transition_reservation
downstream_eligibility_effect: completion_work_created | none
schedule_effect:
  consumed_work_id: same exact value as work_id
  created_work: exact completion-work object below | null
```

Only `result: started` admits this exact non-null `created_work`; both terminal
results require `created_work: null`. `started` requires
`downstream_eligibility_effect: completion_work_created`; `failed_gate` and
`completed` require `downstream_eligibility_effect: none`:

```yaml
work_id: t1/00/occupancy/occupancy_transition_0001.complete
decision_time: t1/00
simulation_phase: 10
transition_id: occupancy_transition_0001
action: complete
```

The start observation order is exact:

```yaml
- gate_id: commitment_planned
  path: /current_causal_state/occupancy_transition_commitments/occupancy_transition_0001/state
  observed: planned
  required: planned
  passed: true
- gate_id: occupant_at_origin
  path: /current_causal_state/canonical_occupancy/topology_occupant_0001
  observed: {kind: at_site, site_id: topology_site_0002}
  required: {kind: at_site, site_id: topology_site_0002}
  passed: true
- gate_id: route_access_available
  path: /current_causal_state/spatial_topology/routes/topology_route_0001/access_state
  observed: available | blocked
  required: available
  passed: true | false
- gate_id: reservation_available
  path: /current_causal_state/occupancy_transition_reservations/occupancy_reservation_topology_occupant_0001/state
  observed: available
  required: available
  passed: true
```

The completion observation order is exact:

```yaml
- gate_id: commitment_active
  path: /current_causal_state/occupancy_transition_commitments/occupancy_transition_0001/state
  observed: active
  required: active
  passed: true
- gate_id: occupancy_in_exact_transition
  path: /current_causal_state/canonical_occupancy/topology_occupant_0001
  observed: {kind: in_transition, transition_id: occupancy_transition_0001}
  required: {kind: in_transition, transition_id: occupancy_transition_0001}
  passed: true
- gate_id: reservation_reserved
  path: /current_causal_state/occupancy_transition_reservations/occupancy_reservation_topology_occupant_0001/state
  observed: reserved
  required: reserved
  passed: true
- gate_id: reservation_owned_by_transition
  path: /current_causal_state/occupancy_transition_reservations/occupancy_reservation_topology_occupant_0001/owner_transition_id
  observed: occupancy_transition_0001
  required: occupancy_transition_0001
  passed: true
- gate_id: commitment_owns_exact_reservation
  path: /current_causal_state/occupancy_transition_commitments/occupancy_transition_0001/resources_owned
  observed: [occupancy_reservation_topology_occupant_0001]
  required: [occupancy_reservation_topology_occupant_0001]
  passed: true
```

The only legal `state_effects` projections are:

```yaml
started:
  occupancy: at_site_origin_to_in_transition
  commitment: planned_to_active
  reservation: available_to_reserved
  clock: t0/00_to_t0/30

failed_gate:
  occupancy: unchanged_at_origin
  commitment: planned_to_failed
  terminal_reason: failed_gate
  reservation: unchanged_available
  clock: t0/00_to_t0/30

completed:
  occupancy: in_transition_to_at_site_destination
  commitment: active_to_succeeded
  reservation: reserved_to_available
  clock: t0/30_to_t1/00
```

Each successor has exactly one canonical ancestry object:

```yaml
canonical_ancestry:
  ancestry_schema: CanonicalOccupancyTransitionAncestry.v1
  parent_record_hash: H0 | H0_blocked | Htransit
  boundary_derivation:
    method: next_consequential_boundary
    source_record_hash: same exact value as parent_record_hash
    decision_time: t0/30 | t1/00, as selected work requires
    simulation_phase: 10
    due_work_ids:
      - exact selected work_id
  ledger_sequence_after_commit: 1 | 2
```

`Rtransit` and `Rblocked` contain one ledger entry with ledger sequence 1. `Rfinal`
contains the byte-identical start entry followed by the completion entry with
ledger sequence 2. The ancestry object names only the immediate predecessor; the
ordered ledger carries accumulated causal history. There is no separately
canonical transaction header.

Successor hashes are computed externally only after complete successor
construction. No canonical record may contain its own hash.

## Failure atomicity

Structural validation and record-bound capability validation occur before
canonical mutation.

```text
invalid record / malformed work / stale or crossing boundary
→ reject
→ no successor
→ no canonical ledger append
→ source record byte-identical
```

Ordinary gate failure is different:

```text
valid blocked record + valid boundary
→ canonical resolution
→ ordinary `failed` successor with reason `failed_gate`
→ due work consumed
→ provenance appended
```

Successor construction is private until the complete envelope, ledger,
ancestry, schedule, resource state, and occupancy tagged union validate. Fault
injection after any provisional mutation but before publication must produce no
canonical successor. No partial record may expose the subject at both sites,
at neither site without an in-transition identity, active without its
reservation, or terminal while retaining its reservation.

### Exact diagnostic precedence

The implementation must apply these stages in order. A later stage may not
repair, reinterpret, or replace a failure from an earlier stage:

```yaml
diagnostic_precedence:
  1_stored_bytes:
    disposition: occupancy_transition_rejected.serialization
    covers: UTF-8, BOM, terminal-LF, duplicate-member, finite-number, and canonical-JSON checks
  2_canonical_record:
    disposition: occupancy_transition_rejected.invalid_canonical_record
    covers: exact identity, schema, topology, occupancy, lifecycle, resource, schedule, ledger, and ancestry validation
  3_record_bound_capability:
    ordered_precedence:
      - if the validated source record has no unresolved boundary: occupancy_transition_rejected.no_due_work
      - if the supplied capability is not an object with the exact five boundary keys: occupancy_transition_rejected.boundary_shape_mismatch
      - if its source_record_hash differs from the exact supplied record hash: occupancy_transition_rejected.boundary_source_mismatch
      - if any remaining field differs from the freshly discovered complete boundary: occupancy_transition_rejected.boundary_shape_mismatch
    covers: exact queried-record binding and complete due-boundary equality
  4_ordinary_gates:
    disposition: canonical result started | failed_gate | completed
    covers: complete non-short-circuited action-specific gate observations
  5_private_construction:
    disposition: private candidate only; no authority may escape
    covers: exhaustive provisional writes under the test-only fault seam
  6_complete_successor_validation:
    disposition: occupancy_transition_rejected.invalid_canonical_record
    covers: exhaustive successor validation before the singular publication point
  7_post_validation_prepublication_fault_seam:
    disposition: occupancy_transition_rejected.injected_private_construction_fault
    covers: the exact final branch-specific fault point after validation and before publication
  8_atomic_publication:
    disposition: return the one complete canonical successor
    covers: the sole point at which successor authority may escape
```

Malformed resolution-local traces use
`occupancy_transition_rejected.invalid_resolution_local_trace`. Attempts to
derive authority from local, retained, unpublished, navigation, or
representation state use `occupancy_transition_rejected.local_authority` or
`occupancy_transition_rejected.unpublished_candidate` as applicable. These
are diagnostic dispositions only and never canonical ledger values.

The exact private fault-injection points are:

```yaml
accepted_start:
  - start_after_occupancy
  - start_after_commitment_state
  - start_after_resources_owned
  - start_after_reservation_state
  - start_after_reservation_owner
  - start_after_start_work_consumed
  - start_after_completion_work_created
  - start_after_clock
  - start_after_ledger
  - start_after_ancestry
  - start_after_complete_validation_before_publication

completion:
  - completion_after_occupancy
  - completion_after_commitment_state
  - completion_after_resources_cleared
  - completion_after_terminal_disposition
  - completion_after_reservation_state
  - completion_after_reservation_owner_cleared
  - completion_after_work_consumed
  - completion_after_clock
  - completion_after_ledger
  - completion_after_ancestry
  - completion_after_complete_validation_before_publication

blocked_start:
  - blocked_after_commitment_state
  - blocked_after_terminal_reason
  - blocked_after_terminal_disposition
  - blocked_after_work_consumed
  - blocked_after_clock
  - blocked_after_ledger
  - blocked_after_ancestry
  - blocked_after_complete_validation_before_publication
```

The fault seam is private and test-only. The public resolver signature remains
exactly `(canonical_record, record_bound_boundary)`. At every point, an
injected fault must leave the exact input bytes/hash and its scheduler result
unchanged, publish no candidate, append no canonical ledger entry, and retain
no global or reusable provisional state.

## Required witness matrix

```yaml
A_exact_genesis:
  proves:
    - exact new payload identity
    - exact inherited topology projection
    - one singular subject occupancy
    - one planned transition definition
    - one available subject-transition reservation

B_reverse_oriented_start:
  proves:
    - transition order site_0002 -> site_0001 is preserved
    - only a copied pair is normalized for route matching
    - lexical route storage is not direction authority
    - accepted start atomically publishes Rtransit

C_in_transition_record:
  proves:
    - subject has one exact in-transition relation
    - subject is not settled at either endpoint
    - active commitment owns its exact reservation
    - completion exists only after start commits

D_record_relative_completion:
  proves:
    - completion is rediscovered from Rtransit
    - start publishes Rtransit only and terminates before rediscovery
    - completion uses no retained R0 boundary or itinerary
    - unresolved_work is the sole candidate-work discovery source
    - canonical completion does not read local interpolation or navigation
    - Rfinal settles the subject at the destination and releases resources

E_blocked_control:
  proves:
    - same transition definition and resolver path
    - byte-identical transition-definition hash across open and blocked inputs
    - route access is the ordinary causal differentiator
    - blocked start commits failed with reason failed_gate without changing occupancy
    - no resource or completion-work residue

F_execution_policy_neutrality:
  proves:
    - dense inspection and boundary jump match at every canonical checkpoint
    - local representation of the interval has no completion authority

G_stale_and_crossing_capabilities:
  proves:
    - R0 start boundary is stale after Rtransit
    - Rtransit completion boundary cannot resolve against R0 or Rfinal
    - open and blocked record capabilities cannot cross

H_replay_and_source_audit:
  proves:
    - every canonical branch replays byte-identically
    - one declared canonical resolver path owns start, failure, and completion
    - representation and policy data cannot reach canonical gates or mutation

I_non_authoritative_schedule_copies:
  proves:
    - R0 completion-time definition cannot create a completion boundary
    - historical ledger created_work cannot resurrect consumed work
    - unpublished candidate state cannot be queried
    - retained start context and local cache cannot authorize completion
```

## Adversarial requirements

The frozen implementation must make each case mechanically falsifiable.

### Canonical identity and schema

Reject before mutation:

1. missing, additional, duplicate, or noncanonical top-level fields;
2. missing or duplicate exact occupant, site, route, transition, reservation, or
   work identities;
3. occupant/site/route/transition/resource/work type substitution;
4. occupancy referencing an unknown site or transition;
5. a second authoritative occupancy index or location field;
6. malformed tagged-union keys, including `at_site` with a transition ID or
   `in_transition` with a site ID;
7. identical origin and destination;
8. noncanonical stored endpoint order or malformed unordered relation; and
9. source/destination pair that does not normalize to the route endpoints.

### Authority and ordering

Reject before mutation:

10. start or completion boundary bound to the wrong record;
11. retained start boundary used after Rtransit commits;
12. fabricated completion boundary before completion work exists;
13. completion work precomputed into R0;
14. crossing open/blocked boundaries or work definitions;
15. route endpoint storage order used to reverse transition intent;
16. resolution policy, local trace, container iteration, scenario ID, seed, or
    expected outcome selecting a result; and
17. conceptual label, Actor ID, transform, nav result, level, streaming cell,
    coordinate, local progress, or physical-arrival flag supplied as authority.

### Lifecycle and atomicity

Reject or fail closed as specified:

18. start when the subject is not settled at the declared origin;
19. start when the subject-transition reservation is not available;
20. successful start without both in-transition occupancy and exact reservation;
21. completion without active commitment, matching in-transition occupancy,
    matching reservation, or owned resource;
22. blocked access followed by occupancy or reservation mutation;
23. start that mutates site identity, route identity, endpoints, endpoint
    semantics, or route access;
24. completion that consults navigation/progress or mutates topology;
25. any partial successor escaping after a fault at a provisional mutation
    point;
26. terminal success retaining the reservation or owned resource;
27. failed start acquiring a resource or leaving completion work;
28. successor self-hash or competing canonical transaction-header authority;
    and
29. local interpolation or representation data serialized into canonical
    history.
30. commitment owner, occupancy subject, or reservation occupant mismatch;
31. commitment time, work time, boundary time, or successor clock mismatch;
32. any lifecycle-matrix combination not listed as legal;
33. hidden root generator, variant flag, or seed interpretation selecting open
    versus blocked access;
34. primary Rtransit or Rfinal topology drift from the exact available root;
    and
35. any additional, missing, or differently shaped dense-inspection trace
    record acquiring canonical influence.
36. any resolver, query, cache, or detached projection converting
    `in_transition` or `commitment.route_id` into site occupancy, route
    occupancy, geometry, progress, or arrival authority;
37. completion authority derived from R0's commitment time declaration;
38. completion authority derived or resurrected from historical ledger
    `created_work`;
39. scheduler discovery against private, unpublished candidate Rtransit;
40. a start resolver returning or retaining a completion boundary, itinerary,
    or reusable completion object; and
41. resolution policy or local cache authorizing completion without a fresh
    query of published Rtransit `unresolved_work`.

Cases 18 and 19 are structural record rejections under the exhaustive
lifecycle matrix; they are not additional ordinary failure branches. Case 22
is the one demonstrated ordinary gate failure. Cases 20, 21, and 23–35 are
structural, capability, private-construction, or source-audit failures as their
wording requires; none may publish a canonical successor.

Blocked route access is an ordinary failed gate, not a structural rejection.
The implementation must test that distinction explicitly.

## Source audit

The source audit is a hard acceptance gate, not documentary evidence. It must
establish:

1. one exact payload validator owns both open and blocked records;
2. one boundary discovery path is record-relative;
3. one canonical resolver path handles start, ordinary failure, and completion;
4. completion work can only be constructed by accepted start resolution;
5. only the canonical occupancy tagged union owns the current canonical spatial relation;
6. route endpoint normalization operates on a copy and never rewrites ordered
   transition intent;
7. resolution-local traces are never resolver inputs;
8. no Unreal, Actor, navigation, transform, coordinate, progress, collision,
   level, streaming, or conceptual-map identity dataflows into canonical gates,
   scheduling, resources, mutation, provenance, or ancestry;
9. no policy-specific or blocked-control-specific resolver exists;
10. resource acquisition and release are canonical and terminally closed;
11. successor identity is self-hash-safe; and
12. no production topology, movement, travel, or pathfinding abstraction is
    introduced under the fixture;
13. scheduler candidate discovery dataflows only from the queried record's
    `future_causal_state.unresolved_work`;
14. start resolution publishes only complete Rtransit and cannot call or
    return scheduler discovery before that publication context ends;
15. detached projections and `route_id` cannot manufacture site, route,
    geometric, progress, or arrival authority; and
16. fixture-genesis reservation data cannot reach current resource gates or
    allocation state.

Output coincidence is insufficient if this structural isolation fails.

## Replay and checkpoint oracle

Within each witness, replay from the same exact canonical input and execution
policy must be byte-identical.

Across dense-inspection and boundary-jump histories, require:

```yaml
must_match:
  R0: byte_identical
  Rtransit: byte_identical
  Rfinal: byte_identical
  canonical_hashes: identical
  ledger_entries: byte_identical
  ancestry: byte_identical
  resource_states_and_dispositions: byte_identical
  future_schedule_after_each_checkpoint: byte_identical
  next_boundary_after_R0: identical_start_bound_to_H0
  next_boundary_after_Rtransit: identical_completion_bound_to_Htransit
  next_boundary_after_Rfinal: identical_none

may_differ:
  resolution_local_inspection_trace: yes
```

The blocked control replays byte-identically from its exact blocked R0 and
produces one exact failed successor. Its scheduler oracle must likewise match
start bound to `H0_blocked` at the root and `none` after `Rblocked`.

## Exact evidence and release artifact DAG

The implementation must emit exactly these deterministic artifact members:

```yaml
artifact_names:
  - canonical_occupancy_transition_R0.json
  - canonical_occupancy_transition_R0_blocked.json
  - canonical_occupancy_transition_start_boundary_H0.json
  - canonical_occupancy_transition_start_boundary_H0_blocked.json
  - canonical_occupancy_transition_Rtransit.json
  - canonical_occupancy_transition_completion_boundary_Htransit.json
  - canonical_occupancy_transition_Rfinal.json
  - canonical_occupancy_transition_Rblocked.json
  - canonical_occupancy_transition_dense_inspection_run.json
  - canonical_occupancy_transition_boundary_jump_run.json
  - canonical_occupancy_transition_blocked_control_run.json
  - canonical_occupancy_transition_checkpoint_oracle.json
  - canonical_occupancy_transition_topology_projection_oracle.json
  - canonical_occupancy_transition_transition_definition_oracle.json
  - canonical_occupancy_transition_runtime_fail_closed.json
  - canonical_occupancy_transition_fault_atomicity.json
  - canonical_occupancy_transition_replay_oracle.json
  - canonical_occupancy_transition_source_audit.json
  - canonical_occupancy_transition_proof_run.json
```

Their role DAG is exact:

```text
sealed Phase-1 canonical_topology_R0 spatial projection
        ├─ detached byte-identity oracle → exact available R0
        └─ same IDs/endpoints + declared access-only difference → exact blocked R0

R0 → Bstart(H0) → Rtransit → Bcomplete(Htransit) → Rfinal
R0_blocked → Bstart(H0_blocked) → Rblocked

dense + jump + blocked control
        ↓
checkpoint / topology / transition-definition oracles
        ↓
runtime rejection + private fault atomicity + replay + source audit
        ↓
proof run + evidence document
        ↓
self-excluding exact-member SHA-256 manifest
        ↓
release verifier regenerates and validates every artifact
```

The Phase-1 predecessor input is bound to exact sealed artifact:

```yaml
path: proof_kernel/CanonicalSpatialTopologyIdentityProofRecords/canonical_topology_R0.json
sha256: 5e57c04875cfaead69f4cd6aaffeee2f788a2c1f5a820a56fb7083f8f7e861ed
```

The complete self-excluding release member set is exactly:

```yaml
source_and_governing_members:
  - README.md
  - Resolution Semantics Law - v0.1.1.md
  - Causal-LOD Equivalence Proof Evidence - v0.1.0.md
  - Record-Relative Chronological Resolution Proof Evidence - v0.1.0.md
  - Canonical Spatial Topology Identity Proof Evidence - v0.1.0.md
  - proof_kernel/CanonicalSpatialTopologyIdentityProofRecords/canonical_topology_R0.json
  - Canonical Occupancy Transition Proof - Draft.md
  - Canonical Occupancy Transition Proof Evidence - v0.1.0.md
  - Co-op Open-City FPS Simulation - v0.7 Working Continuation.md
  - THE_CITY Development Capacity and Progress Note - v0.1.11.md
  - THE_CITY Current Proof State and Repo-Agent Instruction - v0.1.0.md
  - proof_kernel/canonical_occupancy_transition.py
  - proof_kernel/test_canonical_occupancy_transition.py
  - proof_kernel/verify_canonical_occupancy_transition_release.py

deterministic_artifact_members:
  - the exact 19 artifact_names listed above, each under
    proof_kernel/CanonicalOccupancyTransitionProofRecords/
```

The release manifest path is
`Canonical Occupancy Transition Proof - v0.1.0 SHA256SUMS.txt` and it must
exclude itself. Hashes are written only after every exact member is final.
The verifier must reject missing, additional, reordered, duplicated, absolute,
parent-traversing, or checksum-mismatched members and recompute every semantic
oracle rather than trusting checked-in pass booleans. Artifact filenames,
diagnostic labels, and test-only fault IDs are evidence plumbing; they never
enter canonical records or affect resolver selection.

## Exclusions

This proof does not authorize or prove:

- physical movement, animation, navigation, or route traversal;
- distance, speed, travel duration derivation, cost, or time estimation;
- continuous coordinates, interpolation progress, current segment, or last
  valid physical position;
- route entry/exit, capacity, leases, traffic, collision, or congestion;
- mid-transition route closure, cancellation, interruption, rerouting, return,
  recovery, or failure after accepted start;
- multiple subjects, routes, transitions, occupancy contention, or site
  exclusivity;
- external evidence, Q/BQ, player/crew input, same-clock work, randomness, or
  agent planning;
- Unreal materialization of occupancy, player embodiment, split players,
  simultaneous physical domains, or networking;
- World Partition, streaming, save/load, rollback, production topology,
  production Bridge semantics, city graph, population, or scale; or
- Phase 3 or any later thesis-program scope.

The exact proof-fixture completion boundary does not establish a generalized
travel-time law.

## Acceptance statement

If sealed evidence passes every gate, the bounded claim becomes:

> **One canonically identified subject can leave one settled canonical site,
> enter one exact resource-owning canonical transition whose eligibility is
> constrained by an explicitly referenced available canonical route relation,
> remain in that transition across an
> interval whose local inspection is causally irrelevant, and settle at the
> other endpoint only when a later record-relative canonical completion
> boundary resolves.**

And, separately:

> **A structurally valid transition with blocked route access terminates by an
> ordinary canonical failed gate without changing occupancy or acquiring
> transition reservation.**

And, as the chronology boundary:

> **A transition may create future completion eligibility, but completion
> authority exists only after the in-transition successor is published as
> canonical truth and a new record-bound boundary is independently discovered
> from that successor's unresolved work.**

This is not evidence that a physical Actor traversed a road.

## Frozen contract

Freeze review accepted this exact contract on 2026-08-27. The frozen
requirements are:

```yaml
freeze_requirements:
  proof_question: exact
  frozen_identity: 0.7.0-draft.65
  exact_payload_schema: exhaustive
  exact_ID_value_spaces: exhaustive_and_type_disjoint
  phase_1_topology_projection_oracle: exact_and_detached
  singular_occupancy_tagged_union: exact
  in_transition_ontology_and_detached_projection: exact
  route_vs_transition_ordering: exact
  R0_and_blocked_R0: exact
  start_and_completion_boundaries: exact
  unresolved_work_as_sole_scheduler_discovery_source: exact
  start_publication_before_completion_rediscovery: exact
  Rtransit_Rfinal_Rblocked: exact
  reservation_and_terminal_dispositions: exact
  ordinary_failure_vs_structural_rejection: exact
  ledger_and_ancestry: exact_and_self_hash_safe
  local_policy_neutrality: exact
  failure_atomicity: exact
  diagnostic_precedence_and_fault_injection_points: exact
  adversarial_matrix: exact
  source_audit: hard_gate
  replay_and_checkpoint_oracle: exact
  artifact_roles_hashes_and_release_DAG: exact
  exclusions: closed
```

The freeze changes no demonstrated capacity. Evidence remains unsealed until
the exact implementation DAG, witnesses, source audit, and release verifier
pass.

## Bounded implementation authority

Implementation is authorized only for:

```yaml
authorized:
  - exact CanonicalOccupancyTransitionPayload.v1 validation
  - canonical serialization and canonical-envelope hashing
  - exact R0, R0_blocked, Rtransit, Rfinal, and Rblocked records
  - record-bound start and completion boundary discovery
  - one canonical start/blocked/completion resolution path
  - publication of Rtransit before completion rediscovery
  - canonical subject-transition reservation ownership and disposition
  - dense-inspection and boundary-jump witnesses
  - blocked-access control
  - declared structural rejection and fault-injection witnesses
  - byte-identical replay and checkpoint oracle
  - hard source audit
  - evidence artifacts, self-excluding manifest, and release verifier

not_authorized:
  - Unreal or occupancy materialization
  - physical movement, traversal, navigation, or interpolation
  - derived travel time, distance, speed, progress, or route occupancy
  - route capacity, leases, traffic, collision, or congestion
  - multiple subjects, routes, transitions, or contention
  - external input, randomness, same-clock work, or agent planning
  - networking, World Partition, streaming, save/load, or rollback
  - generalized resolver, topology, reservation, or movement abstractions
  - Phase 3, simultaneous physical domains, or adjacent spatial architecture
```

The governing authority state after freeze is:

```yaml
implementation: bounded_canonical_only
unreal_changes: prohibited
capacity_change: none
README_capacity_promotion: prohibited
phase_3_selection: prohibited
evidence_status: unsealed
```
