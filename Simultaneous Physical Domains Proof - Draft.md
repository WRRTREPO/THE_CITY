# Simultaneous Physical Domains Proof

**Version:** 0.1.0-draft.0
**Status:** Specification review only; implementation prohibited
**Selected:** 2026-08-28
**Parent continuation:** [Co-op Open-City FPS Simulation — v0.7 Working Continuation](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)
**Latest sealed predecessor:** [Canonical Occupancy Transition Proof — v0.1.0](Canonical%20Occupancy%20Transition%20Proof%20Evidence%20-%20v0.1.0.md)
**Canonical source payload:** `CanonicalSpatialTopologyIdentityPayload.v1` / `0.7.0-draft.61`, reused byte-for-byte
**Candidate proof-harness identity:** `SimultaneousPhysicalDomainsProof.v1` / `0.7.0-draft.68` — not frozen

## Question

> **Can two process-isolated Unreal representation domains remain
> simultaneously alive against one canonical head, survive an independently
> committed canonical H0→H1 transition without participating in that
> transaction, and independently rebind to H1 while any domain still
> representing H0 is mechanically classified as stale and incapable of
> current-head canonical authority?**

The bounded primary chain is:

```text
exact sealed Phase-1 R0 / H0
        ↓
launch isolated Unreal domain A
  site projection: topology_site_0001
  route projection: topology_route_0001 / available
        ↓
launch isolated Unreal domain B
  site projection: topology_site_0002
  route projection: topology_route_0001 / available
        ↓
A and B simultaneously alive and synchronized to H0
        ↓
canonical machine independently resolves the sealed H0-bound boundary
        ↓
exact sealed Phase-1 R1 / H1
  topology_route_0001.access_state: available → blocked
        ↓
A and B remain alive but are mechanically stale against current head H1
        ↓
independent receipt-verified refreshes in either A/B order
        ↓
A and B remain alive and synchronized to H1
```

This proof does not introduce new canonical state, a new canonical payload, a
new canonical mutation, or another canonical resolver. It composes the exact
sealed Phase-1 H0/H1 transition with a new physical-lifecycle question.

## Selection and authority state

```yaml
selection:
  phase: 3
  proof: Simultaneous Physical Domains Proof
  version: 0.1.0-draft.0
  status: specification_review_only
  implementation_authority: none
  unreal_source_change_authority: none
  capacity_advancement: none
  freeze_status: not_frozen
```

Opening this draft selects one risk for review. It does not authorize Python,
Unreal, adapter, harness, test, evidence, artifact, release-manifest, README
capacity, or production-architecture implementation.

## Governing predecessor boundary

### Exercised predecessor evidence

The candidate directly composes these exact sealed records:

1. [Canonical Spatial Topology Identity Proof — v0.1.0](Canonical%20Spatial%20Topology%20Identity%20Proof%20Evidence%20-%20v0.1.0.md), for the exact two-site/one-route R0/H0 and R1/H1 payloads, the one access-only canonical mutation, detached mapping identity, raw-byte and canonical-hash verification, and representation/canonical identity separation.
2. [Integrated Unreal Promotion-Unload-Repromotion Proof — v0.1.0](Integrated%20Unreal%20Promotion-Unload-Repromotion%20Proof%20Evidence%20-%20v0.1.0.md), only for receipt-verified Unreal materialization, process-root isolation, and canonical/operational identity separation.
3. [Record-Relative Chronological Resolution Proof — v0.1.0](Record-Relative%20Chronological%20Resolution%20Proof%20Evidence%20-%20v0.1.0.md), for current-record-bound boundary authority and post-commit invalidation.
4. [Resolution Semantics Law — v0.1.1](Resolution%20Semantics%20Law%20-%20v0.1.1.md), for canonical-envelope ownership, hash boundaries, and disposable representation state.

### Preserved but not exercised

These sealed records constrain the proof without adding their fixture behavior:

1. [Canonical Occupancy Transition Proof — v0.1.0](Canonical%20Occupancy%20Transition%20Proof%20Evidence%20-%20v0.1.0.md). A domain scope is not subject occupancy, `in_transition`, route occupancy, arrival, or another canonical location field. No occupancy is materialized.
2. [Concurrent External Evidence Arbitration Proof — v0.1.0](Concurrent%20External%20Evidence%20Arbitration%20Proof%20Evidence%20-%20v0.1.0.md). Physical-domain identity, process order, filesystem order, and presentation order remain non-authoritative. QA, QB, BEXT, admission, and arbitration are not exercised.

### Phase-1 physical lifecycle is not inherited

Phase 1 established this physical lifecycle:

```text
materialize R0 in source process
→ destroy source representation
→ commit H0-to-H1 canonical transition
→ materialize R1 in fresh isolated return process
```

Phase 3 deliberately does not inherit that lifecycle. Its novelty requires:

```text
materialize R0 in process A
materialize R0 in process B
→ prove A and B alive concurrently
→ commit H0-to-H1 while neither process participates
→ prove the same A and B process instances remain alive
→ independently rebind those live instances to R1
```

Destroying or replacing either source process before H1, or satisfying the
primary witness with fresh return processes, fails this proof.

## Exact scope

```yaml
proof_scope:
  canonical_payload_schemas: 1 existing exact schema
  new_canonical_fields: 0
  canonical_records: 2 exact sealed artifacts
  canonical_mutations: 1 exact sealed access-only transition
  canonical_sites: 2
  canonical_routes: 1
  physical_domains: 2
  unreal_processes: 2 simultaneously alive
  detached_domain_projections: 4
  primary_refresh_orders: 2
  asymmetric_refresh_failures: 2 symmetric branches
  external_inputs: none
  occupancy_materializations: none
  authoritative_random_draws: none
  implementation_authority: none
```

`physical_domain` means one proof-local Unreal process, one disjoint process
root, one operational process identity, one exact detached projection role,
and one local head-state machine. It is not a player, crew, host, peer,
streaming cell, level instance, network node, canonical subject, or canonical
site.

## Exact canonical source and mutation boundary

The proof must reuse these exact sealed artifacts without modification:

```yaml
canonical_R0:
  path: proof_kernel/CanonicalSpatialTopologyIdentityProofRecords/canonical_topology_R0.json
  raw_sha256: 5e57c04875cfaead69f4cd6aaffeee2f788a2c1f5a820a56fb7083f8f7e861ed
  payload_schema: CanonicalSpatialTopologyIdentityPayload.v1
  simulation_version: 0.7.0-draft.61

canonical_R1:
  path: proof_kernel/CanonicalSpatialTopologyIdentityProofRecords/canonical_topology_R1.json
  raw_sha256: 7ac7ece5c142ac4dee83abc6e83f7845d85dfc7f055ca6d678b7f04bdf1d795a
  payload_schema: CanonicalSpatialTopologyIdentityPayload.v1
  simulation_version: 0.7.0-draft.61
```

`H0` and `H1` retain their Phase-1 meaning: canonical-envelope hashes of the
complete exact R0 and R1 roots. The displayed SHA-256 values bind stored bytes,
including the required terminal LF; they are not substitutes for H0 or H1.

The canonical transition is exactly the sealed Phase-1 boundary and resolver:

```yaml
source_record: R0
source_record_hash: H0
work_id: t1/00/topology/block_topology_route_0001.resolve
decision_time: t1/00
simulation_phase: 10
canonical_mutation:
  op: replace
  path: /current_causal_state/spatial_topology/routes/topology_route_0001/access_state
  prior_value: available
  value: blocked
successor_record: R1
successor_record_hash: H1
```

The implementation proof, if later authorized, must reproduce R1 byte-for-byte
through the existing canonical resolver while both physical domains remain
alive. Neither domain process, projection, local state, refresh state, Actor,
receipt, timing, ordering, or diagnostic may enter boundary discovery, gate
evaluation, mutation, ledger construction, ancestry, or successor hashing.

The H0-to-H1 transaction does not wait for a domain acknowledgement. It does
not observe domain liveness. It does not publish a partial successor. H1 is
current canonical truth before any domain refresh begins.

## Canonical head and history law

> **A committed successor does not invalidate its predecessor as history. It
> invalidates predecessor-bound claims to current-head authority.**

After H1 commits:

- R0/H0 remains valid immutable canonical history and release evidence;
- H1 is the sole current canonical head;
- an H0 materialization may remain physically alive;
- an H0-bound boundary, refresh, cache, projection, receipt, or capability may
  not claim to represent H1 or authorize any current-head operation;
- a physical process cannot make H0 current by retaining, replaying, or
  rematerializing H0; and
- no physical-domain state may construct or publish another canonical
  successor.

The canonical-head register used by the proof harness is operational control
evidence. It points only to an already committed exact canonical hash. It does
not enter the canonical envelope, choose the H0-to-H1 outcome, or grant a
physical process canonical authority.

## Exact detached domain projections

Each physical domain receives the full exact canonical payload plus one
detached, non-authoritative projection map. The map permits representation of
one site and the shared route. It does not contain the route access value,
endpoint relation, topology definition, canonical clock, work, ledger, or
ancestry. Those facts must be read from the accepted canonical payload.

The candidate projection schema is:

```yaml
projection_schema: SimultaneousPhysicalDomainProjection.v1
projection_id: one exact value from the matrix below
proof_scenario: simultaneous-physical-domains-v1
domain_role: domain_A | domain_B
source_canonical_hash: H0 | H1
allowed_site_projection:
  canonical_site_id: topology_site_0001 | topology_site_0002
  representation_slot: domain_A_site_slot_01 | domain_B_site_slot_01
allowed_route_projection:
  canonical_route_id: topology_route_0001
  representation_slot: domain_A_route_slot_01 | domain_B_route_slot_01
```

The exact legal matrix is:

| Domain | Head | Projection ID | Site | Route |
|---|---|---|---|---|
| A | H0 | `simultaneous_domain_A_H0_0001` | `topology_site_0001` | `topology_route_0001` |
| A | H1 | `simultaneous_domain_A_H1_0001` | `topology_site_0001` | `topology_route_0001` |
| B | H0 | `simultaneous_domain_B_H0_0001` | `topology_site_0002` | `topology_route_0001` |
| B | H1 | `simultaneous_domain_B_H1_0001` | `topology_site_0002` | `topology_route_0001` |

Every cross-row combination rejects before physical materialization or
refresh. A projection may neither redirect a domain to the other site nor omit
`topology_route_0001`.

The adapter must validate that the projected site is one of the canonical
route's exact endpoint IDs. It must read the endpoint pair and `access_state`
from the canonical payload. It may not infer either from the projection, Actor
layout, transform, mesh, collision, route-slot name, or physical relation.

Both domains must visibly represent the canonical route-access fact:

```text
H0 → topology_route_0001.access_state = available
H1 → topology_route_0001.access_state = blocked
```

This is a local representation of one shared canonical fact. It is not route
occupancy, direction, geometry, traversal, navigation, streaming, or
cross-domain propagation.

## Process and root isolation

The two live domains must have:

```yaml
isolation:
  process_ids_distinct: true
  process_roots_distinct: true
  canonical_input_roots_distinct: true
  refresh_input_roots_distinct: true
  output_roots_distinct: true
  neither_root_contains_the_other: true
  shared_writable_exchange_root: none
  domain_to_domain_input_visibility: none
```

Both domains may receive byte-identical copies of the exact canonical R0 and
later R1 artifacts. Shared canonical bytes do not make their process roots or
operational identities shared. Neither domain may read the other domain's
projection, receipt, diagnostics, process state, local cache, refresh result,
or output.

The harness may observe both processes. One domain may not use the other's
liveness, refresh, failure, or destruction as a canonical or local truth
selector.

## Detached launch and refresh integrity

Before launch or refresh, the harness must inventory and hash every visible
proof input for that domain. Each accepted input tuple is exact:

```text
canonical payload bytes
+ exact domain/head projection bytes
+ detached domain-operation receipt
```

The candidate domain-operation receipt is:

```yaml
receipt_schema: SimultaneousPhysicalDomainOperationReceipt.v1
operation: launch | refresh
proof_scenario: simultaneous-physical-domains-v1
domain_role: domain_A | domain_B
expected_operational_process_instance_id: absent_for_launch | exact_existing_id_for_refresh
expected_source_head: none_for_launch | H0
expected_target_head: H0 | H1
canonical_payload_raw_sha256: exact R0 or R1 raw digest
expected_canonical_hash: H0 | H1
projection_raw_sha256: exact detached projection digest
expected_projection_id: exact legal matrix value
```

Unknown, missing, duplicate, redirected, empty, or type-incompatible members
reject. Raw bytes are verified before parse. Parsed identities, schema,
scenario, domain role, expected process identity, source head, target head,
projection, and current harness head must agree before a candidate physical
update is built.

The refresh mechanism is one bounded, local, harness-controlled proof channel.
It is not networking, live input collection, packet-order law, a player input
path, or canonical transport. The freeze must choose one exact invocation and
visible-input mechanism before implementation; no alternative channel may be
selected at runtime.

## Exact physical-domain head-state machine

The harness owns the comparison between each domain's accepted head and the
current canonical head. The domain reports its accepted source hash; it does
not declare which canonical record is current.

The only admitted head states are:

```yaml
unbound:
  accepted_head: null
  local_execution: prohibited

synchronized:
  accepted_head: current_canonical_head
  local_nonconsequential_execution: permitted
  current_head_materialization_claim: permitted
  canonical_evidence: prohibited_in_this_proof
  canonical_scheduling: prohibited
  canonical_mutation: prohibited

stale:
  accepted_head: historical_head
  current_canonical_head: different_committed_successor
  local_nonconsequential_execution: permitted_under_quarantine
  diagnostics: permitted_and_must_be_marked_stale
  refresh_attempt: permitted
  current_head_materialization_claim: prohibited
  canonical_evidence: prohibited
  canonical_scheduling: prohibited
  canonical_mutation: prohibited
  canonical_truth_publication: prohibited

invalid:
  accepted_head: untrusted_or_partially_applied
  local_nonconsequential_execution: halted
  diagnostics_and_termination_only: permitted
  refresh_attempt: prohibited
  current_head_materialization_claim: prohibited
  canonical_evidence: prohibited
  canonical_scheduling: prohibited
  canonical_mutation: prohibited
  canonical_truth_publication: prohibited
```

The exact state transitions are:

```text
unbound
  -- valid launch against current H0 --> synchronized(H0)

synchronized(H0)
  -- independent canonical commit H1 --> stale(accepted H0, current H1)

stale(H0/H1)
  -- valid complete atomic refresh --> synchronized(H1)

stale(H0/H1)
  -- refresh bundle rejected before local publication --> stale(H0/H1)

synchronized or stale
  -- detected partial publication / accepted-state corruption --> invalid

invalid
  -- proof-local recovery --> no transition
```

There is no state in which a process remains `synchronized(H0)` after H1 is
the current canonical head. The transition to `stale` is an operational
classification caused by comparing immutable accepted-head identity to the
committed current-head identity; it does not modify R0, R1, or canonical
history.

### Stale local execution law

A stale H0 representation may continue only disposable, nonconsequential
local execution under quarantine. Examples include local rendering, animation,
collision, physics settling, camera motion, or diagnostic counters that do not
leave the process as a current-head claim.

It may not:

- emit evidence accepted as current-head evidence;
- request, retain, or invoke a canonical scheduling capability;
- call a canonical mutation or resolver path;
- label its represented access fact as current;
- publish a materialization-acceptance receipt for H1;
- overwrite or repair H1 from retained H0 state;
- cause another domain to refresh, fail, or change; or
- preserve H0 as a competing current city.

The proof does not claim that stale local physics is meaningful gameplay. It
proves only that such disposable execution cannot acquire strategic authority.

## Atomic physical refresh law

Physical refresh is not a canonical transaction. It nevertheless must be
fail-closed about claims of synchronized representation.

The adapter must:

```text
verify complete H1 payload/receipt/projection tuple
→ verify current canonical head is H1
→ verify exact existing domain process identity
→ construct candidate H1 representation state privately
→ validate complete candidate projection
→ publish accepted_head = H1 and the visible H1 projection together
```

Before the final local publication point, the old H0 representation remains
stale and visible only under quarantine. A rejection before publication leaves
the process exactly `stale(H0/H1)` and publishes no H1 acceptance receipt.

If a fault makes it impossible to establish that accepted-head identity and
visible authoritative-derived representation changed together, the process is
classified `invalid`, local execution halts, and no synchronized receipt is
accepted. The adapter may not claim H1 while showing H0-derived access state,
or show H1-derived access state while claiming H0.

No local refresh failure may roll back, rewrite, delay, or create canonical H1.

## Materialization and head-state receipts

Every successful launch or refresh emits one detached receipt:

```yaml
receipt_schema: SimultaneousPhysicalDomainMaterializationReceipt.v1
proof_scenario: simultaneous-physical-domains-v1
domain_role: domain_A | domain_B
operational_process_instance_id: OperationalInstanceId.v1
accepted_canonical_payload_raw_sha256: exact R0 or R1 raw digest
accepted_canonical_hash: H0 | H1
accepted_projection_raw_sha256: exact projection digest
accepted_projection_id: exact legal matrix value
materialized_canonical_site_id: topology_site_0001 | topology_site_0002
materialized_canonical_route_id: topology_route_0001
materialized_route_access_state: available | blocked
head_state_at_receipt: synchronized
```

The A process ID must remain identical across its H0 launch and H1 refresh.
The B process ID must remain identical across its H0 launch and H1 refresh.
A and B process IDs must differ. Actor IDs, transforms, object paths, and local
physics state may differ and remain detached.

A stale or invalid process may emit only a diagnostic state receipt:

```yaml
receipt_schema: SimultaneousPhysicalDomainStateDiagnostic.v1
domain_role: domain_A | domain_B
operational_process_instance_id: OperationalInstanceId.v1
accepted_canonical_hash: H0 | H1 | null
observed_current_canonical_hash: H1
head_state: stale | invalid
current_head_claim_enabled: false
canonical_evidence_enabled: false
canonical_scheduling_enabled: false
canonical_mutation_enabled: false
```

This receipt is operational evidence, never canonical truth.

## Required positive witnesses

### W1 — A then B refresh

```text
launch A from exact H0 + A/H0 projection
launch B from exact H0 + B/H0 projection
prove both processes concurrently alive and synchronized to H0
commit exact H0-to-H1 canonical transition independently
prove both original process IDs still alive and stale against H1
refresh A atomically to H1
prove A synchronized / B stale
refresh B atomically to H1
prove A and B synchronized to H1
```

### W2 — B then A refresh

Repeat W1 from fresh isolated proof roots and process instances, reversing only
the physical refresh order. The canonical R0, boundary, R1, ledger, ancestry,
and hashes must be byte-identical to W1.

### W3 — stale local execution quarantine

After H1 commits and before refresh, both domains execute one exact bounded
local nonconsequential step. The local diagnostic may differ, but:

- no canonical bytes change;
- no current-head receipt is emitted;
- no evidence, scheduling, mutation, or truth-claim path is enabled;
- the accepted head remains H0; and
- the mechanically observed head state remains `stale(H0/H1)`.

## Required asymmetric witness

The primary asymmetric failure is exact:

```text
H1 commits
→ A refresh receives the exact valid A/H1 tuple and succeeds
→ B refresh receives a B/H1 operation receipt whose payload raw digest does
  not match the supplied exact R1 bytes
→ B rejects before private candidate construction or local publication
→ H1 remains sole canonical authority
→ A is synchronized(H1)
→ B remains stale(accepted H0, current H1)
→ B may continue only quarantined local nonconsequential execution
→ every H0-bound current-head capability/cache/truth claim from B fails
```

The mismatch is a harness-supplied adversarial proof input. It is not a
network, packet, retry, or live-input behavior. A symmetric branch must repeat
the witness with B successful and A stale.

## Current-head authority failures

H0 remains valid history. These failures apply only when an H0-bound object
attempts to act as current-head authority after H1 commits.

The frozen review must require at least:

1. H0-bound refresh receipt claiming target H1 with H0 bytes;
2. H0-bound projection claiming H1 as `source_canonical_hash`;
3. H0 cache or Actor state attempting to publish a current-head
   materialization receipt after H1;
4. H0-bound boundary or scheduler capability presented against current H1;
5. H0-bound mutation or resolver request presented against current H1;
6. stale domain diagnostic relabeled as synchronized;
7. stale domain route access `available` presented as current after H1;
8. domain-local state attempting to rewrite canonical route access;
9. domain-local state attempting to construct a competing successor or ledger;
10. one domain's accepted-head or refresh state used as the other domain's
    current-head oracle;
11. physical or refresh order used to select canonical outcome;
12. projection site or route redirection;
13. projection omission of `topology_route_0001`;
14. route access value supplied by the projection instead of the canonical
    payload;
15. process identity replacement presented as live-instance refresh;
16. successful receipt after partial local publication;
17. domain destruction or refresh failure changing H1; and
18. local execution trace, cache, Actor state, transform, physics, or
    diagnostic reaching canonical scheduling, gates, mutation, ledger,
    ancestry, or hashing.

Every case fails before canonical mutation. Cases involving a malformed
physical refresh leave the domain stale if no local publication occurred and
make it invalid if atomic publication can no longer be proven.

## Destruction and isolation controls

After both domains synchronize to H1, the proof must independently terminate A
and B in symmetric controls. Each control requires:

```yaml
canonical_H1_unchanged: true
remaining_domain_head_state_unchanged: synchronized
terminated_domain_output_used_as_canonical_input: false
new_canonical_work_created: false
canonical_ledger_changed: false
canonical_ancestry_changed: false
```

This proves only that destruction of one disposable representation does not
change canonical truth. It does not prove failover, host migration, reconnect,
network resilience, save/load, or production lifecycle recovery.

## Canonical equivalence and operational variation

Across W1, W2, asymmetric A-success, asymmetric B-success, and destruction
controls, require:

```yaml
must_match:
  canonical_R0_bytes: exact sealed artifact
  canonical_H0: exact sealed identity
  canonical_boundary: byte_identical
  canonical_R1_bytes: exact sealed artifact
  canonical_H1: exact sealed identity
  authoritative_ledger: byte_identical
  canonical_ancestry: byte_identical
  future_schedule: byte_identical
  next_boundary_after_R1: identical_none

may_differ:
  operational_process_ids: yes
  process_start_order: yes
  physical_refresh_order: yes
  domain_local_nonconsequential_state: yes
  stale_diagnostics: yes
  process_termination_order: yes
```

No allowed operational difference may enter a canonical artifact or select a
canonical result.

## Failure atomicity

The proof must freeze fault points for:

- payload-byte verification;
- receipt parsing and identity verification;
- projection parsing and identity verification;
- current-head comparison;
- process-identity comparison;
- private candidate construction;
- candidate projection validation;
- pre-publication invariant validation;
- local publication of accepted head and visible access state; and
- materialization-receipt emission.

Before local publication, a fault leaves the domain stale and H0-derived local
state unchanged. At or after an unprovable partial publication, the domain is
invalid and halted. No fault changes canonical H1 or the other domain.

The eventual frozen implementation must mechanically prove the complete fault
matrix. This draft does not set a fault-point count.

## Provenance and replay

Detached proof evidence must record:

- exact sealed R0/R1 paths, raw hashes, and canonical hashes;
- the exact H0-bound canonical boundary and byte-identical R1 reproduction;
- process-root inventories and realpaths;
- process-start and simultaneous-liveness witnesses;
- per-domain launch and refresh input inventories;
- per-domain projection and operation-receipt hashes;
- successful materialization receipts;
- stale and invalid diagnostics;
- refresh-order and asymmetric-failure timelines;
- domain destruction witnesses;
- current-head authority rejection results;
- source-audit results; and
- deterministic artifact replay.

The canonical artifacts must reproduce byte-identically. Detached operational
identities may differ between independent runs but must satisfy the declared
within-run relations. The replay oracle must compare semantic operational
relations rather than require process IDs to repeat.

## Source audit

The eventual source audit must establish:

1. no new canonical payload, field, serializer, mutation, resolver, ledger, or
   scheduler implementation exists for this proof;
2. the canonical transition calls the existing Phase-1 resolver and compares
   its output byte-for-byte with the sealed R1 artifact;
3. neither Unreal domain can write canonical records, ledger entries, ancestry,
   work, boundaries, or current-head identity;
4. projection data cannot supply route access, endpoint identity, canonical
   topology, canonical clock, or work;
5. domain head state, process identity, liveness, refresh state, Actor state,
   cache, physics, and diagnostics do not dataflow into canonical execution;
6. the current-head guard compares exact canonical hashes and never repairs,
   promotes, or rewrites an H0-bound claim;
7. stale local execution has no outward current-head evidence, scheduling,
   mutation, or truth-publication path;
8. refresh is private until one complete local publication point;
9. one domain cannot read or select from the other's proof root or local state;
10. process and refresh order cannot select canonical or materialized access
    truth; and
11. no occupancy, movement, networking, streaming, World Partition, player,
    or production abstraction is introduced under the proof fixture.

## Explicit exclusions

This proof does not authorize or prove:

- canonical subject or occupancy materialization;
- physical movement, traversal, navigation, interpolation, coordinates,
  distance, speed, travel time, arrival, route progress, or route occupancy;
- Q, BQ, QA, QB, BEXT, external admission, external arbitration, or any
  additional physical-evidence type;
- live external-input collection, candidate-set completeness, packet order,
  transport order, retry, re-admission, or open-ended input streams;
- player embodiment, split players, two-player gameplay, 1–4 player topology,
  split crews, or player-to-domain ownership;
- networking, replication, reconciliation, rollback, host migration, save/load,
  disconnect, reconnect, or shared multi-owner persistence;
- World Partition, streaming, streaming bubbles, levels, Level Instances,
  cells, proximity promotion, or production materialization architecture;
- cross-domain causal propagation, domain-to-domain messaging, shared local
  physics, or one domain updating the other;
- arbitrary domain counts, dynamic domain creation, production lifecycle
  management, city population, city scale, or performance;
- new canonical topology, access semantics, occupancy, contention, movement,
  scheduler, resolver, or canonical payload behavior;
- randomness, stochastic identity, generalized planning, or Phase 4–6; or
- production architecture of any kind.

## Review gates before freeze

This draft may freeze only after review establishes:

```yaml
freeze_review:
  proof_question: exact
  canonical_R0_R1_artifacts: exact_and_byte_bound
  phase_1_physical_lifecycle_noninheritance: explicit
  canonical_transaction_independence: exact
  physical_domain_definition: exact
  simultaneous_liveness_witness: exact
  domain_A_and_B_projections: exhaustive
  shared_route_projection: required_in_both_domains
  launch_and_refresh_input_inventory: exhaustive
  operation_receipts: exhaustive
  physical_head_state_machine: exhaustive
  stale_local_execution_law: exact
  invalid_state_and_halt_law: exact
  physical_refresh_publication_boundary: exact
  asymmetric_witnesses: exact_and_symmetric
  current_head_authority_failures: exhaustive
  failure_atomicity: fault_points_frozen
  domain_isolation: exact
  canonical_equivalence: exact
  provenance_and_replay: exact
  source_audit: exact
  release_manifest: self_excluding_and_mechanically_verified
  exclusions: exact
```

The draft must not freeze with an unresolved refresh transport, optional
projection member, ambiguous stale/invalid disposition, or unspecified local
publication boundary.

## Candidate acceptance statement

If a later frozen implementation passes every required gate, it may establish
only:

> **Two process-isolated Unreal representation domains can remain
> simultaneously alive while one exact canonical topology record advances
> independently from H0 to H1. Each live process can rebind through an exact
> detached projection to the same H1, while any process still representing H0
> is mechanically stale, may continue only quarantined nonconsequential local
> execution, and cannot exercise current-head evidence, scheduling, mutation,
> or truth authority.**

It may not establish multiplayer, networking, occupancy materialization,
movement, streaming, or production physical-domain architecture.

## Current decision record

```yaml
working_unit: Simultaneous Physical Domains Proof v0.1.0-draft.0
successor_selected: true
specification_status: review_only
freeze_status: not_frozen
implementation_authority: none
canonical_capacity_change: none
latest_sealed_capacity: THE_CITY Development Capacity and Progress Note v0.1.11
```

No code may be written for this proof until a separately reviewed freeze fixes
the complete contract and explicitly grants bounded implementation authority.
