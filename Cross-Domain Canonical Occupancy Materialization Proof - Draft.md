# Cross-Domain Canonical Occupancy Materialization Proof

**Version:** 0.1.0-draft.0\
**Status:** Specification review only; implementation prohibited\
**Selected:** 2026-08-29\
**Parent continuation:** [Co-op Open-City FPS Simulation — v0.7 Working Continuation](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)\
**Latest sealed predecessor:** [Simultaneous Physical Domains Proof — v0.1.1](Simultaneous%20Physical%20Domains%20Proof%20Evidence%20-%20v0.1.1.md)\
**Canonical source payload:** `CanonicalOccupancyTransitionPayload.v1` / `0.7.0-draft.65`, exact sealed R0 → Rtransit → Rfinal chain\
**Physical-lifecycle source:** `SimultaneousPhysicalDomainsProof.v1.1` / `0.7.0-draft.77`, exact sealed two-process law\
**Candidate proof-harness identity:** `CrossDomainCanonicalOccupancyMaterializationProof.v1` / `0.7.0-draft.79` — not frozen

## Question

> **Can the exact sealed Phase-2 R0 → Rtransit → Rfinal occupancy chain be
> represented across the two simultaneously live Phase-3 Unreal domains, while
> the canonical record remains the sole authority for occupancy and
> completion?**

The bounded primary chain is:

```text
exact sealed Phase-2 R0 / H0_occ
  topology_occupant_0001 = at_site(topology_site_0002)
        ↓
launch original Unreal domain A / topology_site_0001
launch original Unreal domain B / topology_site_0002
        ↓
both processes simultaneously alive and synchronized to H0_occ
  A: positive head anchor + zero subject Actors
  B: positive head anchor + exactly one subject Actor
        ↓
canonical machine independently discovers and resolves exact Bstart(H0_occ)
        ↓
exact sealed Phase-2 Rtransit / Htransit_occ
  topology_occupant_0001 = in_transition(occupancy_transition_0001)
        ↓
both original processes remain alive, become head-unconfirmed, then stale
        ↓
independent receipt-verified refreshes in a frozen A/B order
  A: positive Htransit anchor + zero subject Actors
  B: positive Htransit anchor + zero subject Actors
        ↓
canonical machine independently rediscovers and resolves exact
Bcomplete(Htransit_occ) from Rtransit.unresolved_work only
        ↓
exact sealed Phase-2 Rfinal / Hfinal_occ
  topology_occupant_0001 = at_site(topology_site_0001)
        ↓
both original processes remain alive, become head-unconfirmed, then stale
        ↓
independent receipt-verified refreshes in a frozen A/B order
  A: positive Hfinal anchor + exactly one subject Actor
  B: positive Hfinal anchor + zero subject Actors
        ↓
both original processes remain alive and synchronized to Hfinal_occ
```

This proof composes two sealed laws without changing either. Phase 2 remains
the sole owner of canonical occupancy, transition start, completion discovery,
reservation disposition, ledger, ancestry, and successor publication. Phase 3
supplies only the exact two-original-process liveness, isolation, refresh,
staleness, fail-closed publication, provenance, and independent-live-probe
discipline.

The proof does not establish traversal. At `Rtransit`, the subject is
canonically in transition and is represented at neither endpoint. No route
Actor, coordinate, interpolation, progress, speed, distance, arrival trigger,
or navigation path may stand in for that canonical fact.

## Selection and authority state

```yaml
selection:
  phase: 4
  proof: Cross-Domain Canonical Occupancy Materialization Proof
  version: 0.1.0-draft.0
  status: specification_review_only
  candidate_proof_harness_identity: CrossDomainCanonicalOccupancyMaterializationProof.v1
  candidate_simulation_identity: 0.7.0-draft.79
  implementation_authority: none
  unreal_source_change_authority: none
  evidence_authority: none
  release_authority: none
  capacity_advancement: none
  freeze_status: not_frozen
```

Opening this draft selects one composition risk for review. It authorizes
governing specification work only. It does not authorize Python, Unreal,
adapter, router, Actor, harness, test, evidence, artifact, manifest, capacity,
production-architecture, or adjacent successor implementation.

## Governing predecessor boundary

### Exercised predecessor evidence

The candidate directly composes these exact sealed records:

1. [Canonical Occupancy Transition Proof — v0.1.0](Canonical%20Occupancy%20Transition%20Proof%20Evidence%20-%20v0.1.0.md), for the exact canonical R0, Rtransit, and Rfinal records; record-bound start and completion; singular occupancy; reservation closure; byte-identical replay; and the law that completion is rediscovered only from published Rtransit unresolved work.
2. [Simultaneous Physical Domains Proof — v0.1.1](Simultaneous%20Physical%20Domains%20Proof%20Evidence%20-%20v0.1.1.md), for two original process-isolated Unreal domains remaining alive across an independent canonical commit; immutable process binding; head-unconfirmed/stale/synchronized/invalid/protocol-invalid dispositions; atomic local refresh; independent live-world observation; process-input closure; and canonically inert physical guards.
3. [Canonical Spatial Topology Identity Proof — v0.1.0](Canonical%20Spatial%20Topology%20Identity%20Proof%20Evidence%20-%20v0.1.0.md), only for exact site/route identity and representation/canonical separation already embedded in the Phase-2 records.
4. [Integrated Unreal Promotion-Unload-Repromotion Proof — v0.1.0](Integrated%20Unreal%20Promotion-Unload-Repromotion%20Proof%20Evidence%20-%20v0.1.0.md), only for raw-byte-bound materialization input, detached receipts, and canonical/operational identity separation.
5. [Resolution Semantics Law — v0.1.1](Resolution%20Semantics%20Law%20-%20v0.1.1.md), for canonical-envelope ownership, hash boundaries, record-relative authority, and disposable representation state.

### Preserved but not exercised

These sealed records constrain the candidate without adding their behavior:

1. Concurrent External Evidence Arbitration remains sealed and unexercised. No QA, QB, BEXT, admission, collection, retry, transport, or arbitration is present.
2. Phase-2 blocked access remains sealed predecessor evidence but is not a fourth materialized primary head. This candidate asks only about the exact successful R0 → Rtransit → Rfinal chain.
3. Same-clock successors, stochastic identity, agent selection, multiple commitments, and generalized scheduling remain outside the proof.

### Neither predecessor lifecycle is silently generalized

Phase 2 proved no Unreal lifecycle. Phase 3 proved one canonical H0-to-H1
access mutation across two live processes, but it did not materialize canonical
occupancy and did not cross two consecutive canonical commits.

Phase 4 therefore introduces exactly these new proof obligations:

```text
one exact Phase-2 payload schema in Unreal
+ one canonical subject disposition derived in each domain
+ two consecutive canonically independent commits
+ two local stale/refresh cycles in the same original A/B processes
+ a positive proof of lawful zero-subject materialization at Rtransit
```

It does not inherit permission to generalize Phase 3's guard, process,
projection, input, or Actor schema. Any reused mechanism must be named,
versioned, and rebound to this exact three-head occupancy contract before
freeze.

## Exact scope

```yaml
proof_scope:
  canonical_payload_schemas: 1 existing exact schema
  new_canonical_fields: 0
  canonical_records: 3 exact sealed artifacts
  canonical_mutations: 2 exact sealed Phase-2 resolutions
  canonical_subjects: 1
  canonical_sites: 2
  canonical_routes: 1
  canonical_transition_commitments: 1
  canonical_reservations: 1
  physical_domains: 2
  original_unreal_processes_per_primary_witness: 2
  process_replacements: 0
  detached_domain_head_projections: 6 exact rows
  positive_head_anchors_per_primary_witness: 6
  local_subject_actors_across_the_three_synchronized_checkpoints: 2 total
  canonical_completion_inputs_from_unreal: 0
  external_inputs: 0
  player_pawns_or_possessions: 0
  authoritative_random_draws: 0
  capacity_advancement: none
  implementation_authority: none
```

`physical_domain` retains the exact Phase-3 meaning: one proof-local Unreal
process, one disjoint process root, one immutable process-birth binding, one
exact domain role, one original control/output pipe set, and one local
representation state. It is not a player, crew, network peer, canonical
subject, streaming cell, level instance, host, ownership grant, or canonical
site.

The sole canonical subject is `topology_occupant_0001`. A physical domain does
not own that subject. Domain role decides only which canonical site may be
locally represented; it never decides occupancy.

## Exact canonical source artifacts

The candidate must reuse these exact sealed Phase-2 artifacts without
modification:

```yaml
canonical_R0:
  path: proof_kernel/CanonicalOccupancyTransitionProofRecords/canonical_occupancy_transition_R0.json
  raw_sha256: 59ce47bc4d6c63cbda4a740fec8d25e497ca8ed74052b16b5358745be115c2dc
  canonical_hash: b31e7ad0993e288ba80f50fb1960da5c67bad9bcc7cc39bf0ec0ebeeaad57dc8
  occupancy: at_site(topology_site_0002)

canonical_Rtransit:
  path: proof_kernel/CanonicalOccupancyTransitionProofRecords/canonical_occupancy_transition_Rtransit.json
  raw_sha256: 215e3383bff21a9fe01dbb240035a0fa5dd774c703417486846e027a0615a12f
  canonical_hash: 2640fe567b343e2229f875c9cf2d081f41aaaec2a3834e81e2efb3f9caa5da19
  occupancy: in_transition(occupancy_transition_0001)

canonical_Rfinal:
  path: proof_kernel/CanonicalOccupancyTransitionProofRecords/canonical_occupancy_transition_Rfinal.json
  raw_sha256: 0b4d9d97eb166b3aae6480c5581654c39b367c3a5fab47a02daec50b1e88a181
  canonical_hash: 3a00d32115af74950923ac3362a8459d0e08043d45abbe91bcc573e27103db34
  occupancy: at_site(topology_site_0001)

identity:
  record_schema: CanonicalResolutionEnvelope.v1
  payload_schema: CanonicalOccupancyTransitionPayload.v1
  scenario_id: canonical-occupancy-transition-v1
  scenario_version: 0.1.0
  simulation_version: 0.7.0-draft.65
```

The displayed raw SHA-256 values bind stored bytes, including the terminal LF.
They are not canonical record hashes. The canonical hashes are recomputed from
the exact envelope projection defined by the sealed Phase-2 implementation;
neither digest may substitute for the other.

## Exact canonical transition boundary

The proof must call the sealed Phase-2 scheduler and resolver without adding a
physical-domain parameter, callback, guard, acknowledgement, observation, or
expected result.

```yaml
start_boundary:
  schema: CanonicalOccupancyTransitionBoundary.v1
  source_record_hash: b31e7ad0993e288ba80f50fb1960da5c67bad9bcc7cc39bf0ec0ebeeaad57dc8
  decision_time: t0/30
  simulation_phase: 10
  due_work_ids:
    - t0/30/occupancy/occupancy_transition_0001.start

completion_boundary:
  schema: CanonicalOccupancyTransitionBoundary.v1
  source_record_hash: 2640fe567b343e2229f875c9cf2d081f41aaaec2a3834e81e2efb3f9caa5da19
  decision_time: t1/00
  simulation_phase: 10
  due_work_ids:
    - t1/00/occupancy/occupancy_transition_0001.complete
```

Rtransit must be byte-identical to the sealed artifact after the accepted start.
Rfinal must be byte-identical to the sealed artifact after completion freshly
rediscovered from Rtransit's `future_causal_state.unresolved_work`. A retained
R0 schedule copy, physical Actor disappearance, destination Actor creation,
refresh receipt, local clock, transform, collision, animation completion, or
domain acknowledgement may not construct, select, accelerate, delay, or satisfy
completion.

The canonical transaction does not wait for either domain. It does not observe
whether either process is alive, synchronized, stale, invalid, destroyed, or
refreshed. Physical failure may close the proof protocol; it may not roll back,
rewrite, delay, or create Rtransit or Rfinal.

## Exact domain projection and occupancy derivation

Each domain receives the full exact canonical payload plus one detached
domain/head projection. The projection admits a site representation slot and a
subject representation slot, but it contains no occupancy kind, occupied site,
transition ID, expected subject presence, expected Actor count, completion
state, or expected live-observation result.

The candidate projection schema is:

```yaml
projection_schema: CrossDomainCanonicalOccupancyProjection.v1
projection_id: one exact value from the six-row matrix
proof_scenario: cross-domain-canonical-occupancy-materialization-v1
domain_role: domain_A | domain_B
source_canonical_hash: H0_occ | Htransit_occ | Hfinal_occ
allowed_site_projection:
  canonical_site_id: topology_site_0001 | topology_site_0002
  representation_slot: domain_A_site_slot_01 | domain_B_site_slot_01
allowed_subject_projection:
  canonical_occupant_id: topology_occupant_0001
  representation_slot: domain_A_subject_slot_01 | domain_B_subject_slot_01
```

The exact legal matrix proposed for freeze is:

| Domain | Canonical head | Projection ID | Allowed site | Subject slot |
|---|---|---|---|---|
| A | H0_occ | `cross_domain_A_R0_0001` | `topology_site_0001` | `domain_A_subject_slot_01` |
| B | H0_occ | `cross_domain_B_R0_0001` | `topology_site_0002` | `domain_B_subject_slot_01` |
| A | Htransit_occ | `cross_domain_A_Rtransit_0001` | `topology_site_0001` | `domain_A_subject_slot_01` |
| B | Htransit_occ | `cross_domain_B_Rtransit_0001` | `topology_site_0002` | `domain_B_subject_slot_01` |
| A | Hfinal_occ | `cross_domain_A_Rfinal_0001` | `topology_site_0001` | `domain_A_subject_slot_01` |
| B | Hfinal_occ | `cross_domain_B_Rfinal_0001` | `topology_site_0002` | `domain_B_subject_slot_01` |

Every cross-row, redirected, omitted, additional, duplicated, or unknown member
rejects before materialization. The adapter must derive occupancy disposition
only from the validated canonical payload and compare an `at_site.site_id` only
with the exact projection site ID. The projection cannot announce the answer.

The exhaustive canonical-to-local disposition table is:

| Canonical record | Domain A | Domain B | Total live subject Actors |
|---|---|---|---:|
| R0 / `at_site(topology_site_0002)` | `remote_at_other_site` | `present_at_local_site` | 1 |
| Rtransit / `in_transition(occupancy_transition_0001)` | `in_transition_out_of_domain` | `in_transition_out_of_domain` | 0 |
| Rfinal / `at_site(topology_site_0001)` | `present_at_local_site` | `remote_at_other_site` | 1 |

No other disposition is lawful. `remote_at_other_site` does not reveal an
unprojected site's local representation. It states only that this domain must
not publish the subject Actor. `in_transition_out_of_domain` states that the
canonical occupant is in the exact transition and may not be represented at
either endpoint. It does not create route occupancy or a third place.

## Positive representation of lawful absence

Actor absence alone is not proof. A missing subject Actor could mean a lawful
remote or in-transition disposition, but it could also mean failed launch,
failed refresh, partial publication, wrong world, wrong head, wrong projection,
or an inspection that never ran.

Every synchronized domain therefore requires two independent facts:

1. one positively observed representation-head anchor bound to the accepted
   canonical bytes, canonical hash, domain role, projection, and derived local
   occupancy disposition; and
2. an independent live-world census of subject representation Actors.

The candidate anchor schema is:

```yaml
anchor_schema: CrossDomainOccupancyHeadAnchor.v1
proof_scenario: cross-domain-canonical-occupancy-materialization-v1
domain_role: domain_A | domain_B
operational_process_instance_id: exact_immutable_binding
accepted_canonical_payload_raw_sha256: exact R0 | Rtransit | Rfinal raw digest
accepted_canonical_hash: H0_occ | Htransit_occ | Hfinal_occ
accepted_projection_raw_sha256: exact detached projection digest
accepted_projection_id: exact six-row value
canonical_occupant_id: topology_occupant_0001
canonical_occupancy_kind: at_site | in_transition
canonical_occupancy_reference: topology_site_0001 | topology_site_0002 | occupancy_transition_0001
local_subject_disposition: present_at_local_site | remote_at_other_site | in_transition_out_of_domain
head_state_at_publication: synchronized
```

The anchor is disposable representation state. It does not create a canonical
head, choose a disposition, complete a transition, authorize evidence, or
substitute for the canonical payload. Its identity may change at every refresh.

The exact live-world observation schema must be frozen before implementation.
At minimum it must bind:

```yaml
observation_schema: CrossDomainOccupancyLiveObservation.v1
operational_process_instance_id: exact observed process binding
domain_role: independently derived from the real process root
observed_anchor_count: 1
observed_anchor_identity: exact live Actor/component identity
observed_anchor_fields: independently read live values
observed_subject_actor_count: 0 | 1
observed_subject_actor_identities: exhaustive sorted list
observed_subject_occupant_ids: exhaustive sorted list
observed_subject_site_ids: exhaustive sorted list
player_pawn_count: 0
possessed_controller_count: 0
phase_4_actor_input_path_count: 0
```

The independent probe must have no adapter pointer and may consume neither the
materialization receipt, authoritative-derived JSON under test, expected
disposition, expected Actor count, nor harness pass/fail result. It must inspect
the live published world objects directly and report the complete relevant
Actor/component census.

For `present_at_local_site`, the anchor and one exact subject Actor must agree on
occupant ID, site ID, accepted head, projection, and process binding. For either
lawful absence disposition, the positive anchor must exist and the complete
subject Actor census must be zero. A zero count without the exact anchor is
invalid evidence.

## Subject representation law

A subject representation Actor is permitted only for
`present_at_local_site`. It is a read-only expression of one accepted canonical
fact. It owns no occupancy, completion, transition, reservation, scheduling,
evidence, or mutation authority.

The Actor may contain only the frozen representation members needed to prove:

```yaml
canonical_occupant_id: topology_occupant_0001
represented_site_id: exact local projected site
accepted_canonical_hash: exact synchronized head
accepted_projection_id: exact synchronized projection
operational_process_instance_id: exact immutable binding
representation_actor_identity: disposable local identity
```

It may not contain or derive:

- an authoritative transform-to-site rule;
- route progress, arrival, distance, speed, interpolation, or navigation state;
- a completion timer, callback, trigger, overlap, animation event, or collision
  event with canonical effect;
- a retained canonical boundary or scheduler capability;
- another domain's state, liveness, subject Actor, or projection;
- a local substitute for the canonical occupancy tagged union; or
- a canonical write, ledger, ancestry, reservation, or successor path.

The proof requires no Pawn, player controller ownership, possession, input
component, auto-receive input, player identity, or crew identity. An inert
engine-base controller may exist only if the freeze records and source audit
prove that it cannot reach any Phase-4 Actor or command path.

## Exact process identity and lifetime

The two primary processes must reuse or version the sealed Phase-3 immutable
22-member process-binding contract. Before freeze, the draft must state the
exact binding schema, member order, verification mode, and child-visible versus
independent observation for every member. No process identity may come only
from a declared command value.

For each primary witness:

```yaml
domain_A:
  one_process_birth: true
  original_child_handle_retained: true
  original_stdin_stdout_stderr_bindings_retained: true
  process_root_immutable: true
  alive_from_L0_through_L8: true

domain_B:
  one_process_birth: true
  original_child_handle_retained: true
  original_stdin_stdout_stderr_bindings_retained: true
  process_root_immutable: true
  alive_from_L0_through_L8: true

cross_domain:
  process_ids_distinct: true
  process_birth_tuples_distinct: true
  process_roots_disjoint: true
  proof_input_roots_disjoint: true
  output_roots_disjoint: true
  shared_writable_exchange_root: none
  domain_to_domain_input_visibility: none
```

The required liveness checkpoints are:

| Checkpoint | Canonical head | Required joint A/B state |
|---|---|---|
| L0 | R0 | A and B synchronized to R0 |
| L1 | Rtransit committed, observation unpublished | A and B head-unconfirmed at R0 |
| L2 | Rtransit observed, guard closed | A and B stale at R0 |
| L3 | Rtransit | the witness's first-refreshed role synchronized to Rtransit; its peer stale at R0 |
| L4 | Rtransit | A and B synchronized to Rtransit |
| L5 | Rfinal committed, observation unpublished | A and B head-unconfirmed at Rtransit |
| L6 | Rfinal observed, guard closed | A and B stale at Rtransit |
| L7 | Rfinal | the witness's first-refreshed role synchronized to Rfinal; its peer stale at Rtransit |
| L8 | Rfinal | A and B synchronized to Rfinal |

Every checkpoint must bind both original process-birth identities, open child
handles, non-EOF control/output pipes, and one independent liveness observation.
A fresh process, restarted editor, replaced child, reattached pipe, or copied
receipt cannot satisfy continuity.

## Exact physical current-head guard

The Phase-4 guard is operational protocol state only. It may control acceptance
of a physical current-head representation claim and refresh eligibility. It may
not enter Phase-2 boundary discovery, gate evaluation, resolver execution,
record construction, ledger, ancestry, canonical hashing, or publication.

The candidate exact states are:

```yaml
open_for_R0:
  accepted_physical_head: H0_occ
  refresh_target: none

closed_for_R0_to_Rtransit:
  accepted_physical_head: none
  refresh_target: none

open_for_Rtransit:
  accepted_physical_head: Htransit_occ
  refresh_target: Htransit_occ

closed_for_Rtransit_to_Rfinal:
  accepted_physical_head: none
  refresh_target: none

open_for_Rfinal:
  accepted_physical_head: Hfinal_occ
  refresh_target: Hfinal_occ

failed_closed:
  accepted_physical_head: none
  refresh_target: none
```

The normal transition order is exact:

```text
open_for_R0
→ close before invoking sealed Phase-2 start resolution
→ exact Rtransit commits regardless of guard state
→ independently observe and reverify exact Rtransit
→ classify every R0 domain stale
→ open_for_Rtransit
→ refresh both domains to Rtransit
→ close before invoking sealed Phase-2 completion resolution
→ exact Rfinal commits regardless of guard state
→ independently observe and reverify exact Rfinal
→ classify every Rtransit domain stale
→ open_for_Rfinal
→ refresh both domains to Rfinal
```

Opening for a new head before exact canonical observation and all required
stale classifications is a protocol failure. Leaving the guard open for the
source head during either canonical invocation must not prevent the exact
canonical commit; it must instead end the physical protocol `failed_closed`
and classify affected physical dispositions `protocol_invalid`.

## Exact physical head dispositions

The candidate admits only:

```yaml
unbound:
  accepted_head: null
  local_execution: prohibited

synchronized:
  accepted_head: exact_current_canonical_head
  exact_anchor_and_live_observation: required
  local_nonconsequential_execution: permitted
  current_head_representation_claim: permitted
  canonical_evidence: prohibited
  canonical_scheduling: prohibited
  canonical_mutation: prohibited

head_unconfirmed:
  accepted_head: prior_head
  committed_successor: exists_but_operational_observation_not_yet_proven
  local_nonconsequential_execution: prohibited
  refresh: prohibited
  current_head_representation_claim: prohibited

stale:
  accepted_head: exact_historical_head
  current_canonical_head: different_exact_committed_successor
  local_nonconsequential_execution: permitted_under_quarantine
  refresh_to_immediate_successor: permitted_when_guard_open
  current_head_representation_claim: prohibited
  canonical_evidence: prohibited
  canonical_scheduling: prohibited
  canonical_mutation: prohibited
  canonical_truth_publication: prohibited

invalid:
  accepted_head: untrusted_or_partially_published
  local_execution: halted
  refresh: prohibited
  diagnostics_and_termination_only: permitted

protocol_invalid:
  accepted_head: exact_historical_head
  cause: physical_protocol_violated_after_exact_canonical_commit
  local_execution: halted
  refresh: prohibited
  diagnostics_and_termination_only: permitted
```

There is no state in which a domain remains synchronized to a predecessor after
a different committed head is independently observed. A stale R0 subject Actor
may remain visibly present in domain B only as quarantined historical local
state until a valid Rtransit refresh atomically removes it. It may never be
accepted as a current occupancy claim after Rtransit commits.

Direct R0-to-Rfinal physical catch-up is excluded from this candidate. The
positive proof requires both domains synchronized to Rtransit before the normal
completion cycle. A separate canonical-independence control may allow Rfinal to
commit while one or both domains remain stale at R0, but those domains remain
stale or terminate; they may not skip the immediate-successor refresh contract.

## Detached launch and refresh input closure

Every accepted launch or refresh input is exactly:

```text
exact canonical payload bytes
+ exact domain/head projection bytes
+ exact detached operation receipt bytes
```

No expected disposition, expected subject count, expected anchor fields,
expected live observation, current-head result, other-domain state, canonical
before/after summary, or pass/fail value may be visible to the Unreal process
or independent probe.

The operation receipt candidate is:

```yaml
receipt_schema: CrossDomainOccupancyOperationReceipt.v1
operation: launch | refresh
proof_scenario: cross-domain-canonical-occupancy-materialization-v1
domain_role: domain_A | domain_B
expected_operational_process_instance_id: absent_for_launch | exact_existing_binding_for_refresh
expected_source_head: none_for_launch | H0_occ | Htransit_occ
expected_target_head: H0_occ | Htransit_occ | Hfinal_occ
canonical_payload_raw_sha256: exact target-record raw digest
expected_canonical_hash: exact target canonical hash
projection_raw_sha256: exact detached projection digest
expected_projection_id: exact six-row value
```

The harness must inventory and hash the complete process-visible launch and
refresh surfaces: argv, environment, cwd, inherited descriptors, executable,
project, config/module inputs, runtime dependencies, original control channel,
and exact isolated bundle directory. The freeze must choose one exact refresh
invocation and prohibit all alternates, including flags, environment changes,
watchers, polling, signals, sockets, shared files, console commands, timers,
Actor input, player input, or domain-to-domain messages.

## Atomic local publication law

Physical materialization is not a canonical transaction. It must nevertheless
be atomic about any claim of synchronized representation.

For each launch or refresh, the adapter must perform this order:

```text
read and hash the complete exact three-file bundle
→ validate exact canonical payload bytes and canonical hash
→ validate exact projection bytes and legal matrix row
→ validate exact operation receipt and immutable process binding
→ derive occupancy disposition from canonical payload + local site only
→ privately construct candidate head anchor
→ privately construct the exhaustive candidate subject Actor set
→ validate anchor/Actor coherence and zero-or-one Actor cardinality
→ publish accepted head, anchor, and subject Actor set atomically
→ emit detached materialization receipt
→ obtain independent live-world observation
→ accept synchronized state only if receipt and live observation agree
```

Before publication, the prior representation remains historical local state.
A rejection before publication leaves the domain stale at the prior accepted
head and emits no target-head receipt. If the system cannot prove that the
anchor, subject Actor set, and accepted-head identity changed together, the
domain becomes invalid and local execution halts.

The R0-to-Rtransit refresh has an exact destructive obligation: domain B's
prior R0 subject Actor must be gone when the Rtransit anchor becomes visible.
The Rtransit-to-Rfinal refresh has an exact asymmetric publication obligation:
domain A publishes one Rfinal subject Actor with its Rfinal anchor, while domain
B publishes an Rfinal anchor with no subject Actor. A retained predecessor
anchor or subject Actor, premature destination Actor, duplicate subject Actor,
or target anchor paired with a predecessor Actor set is partial publication.

No local publication failure may alter canonical record bytes, canonical head,
ledger, ancestry, unresolved work, transition commitment, reservation, or the
ability of the sealed canonical resolver to produce its exact successor.

## Materialization receipt boundary

Every successful launch or refresh emits one detached receipt with at least:

```yaml
receipt_schema: CrossDomainOccupancyMaterializationReceipt.v1
proof_scenario: cross-domain-canonical-occupancy-materialization-v1
operation: launch | refresh
domain_role: domain_A | domain_B
operational_process_instance_id: exact immutable binding
accepted_canonical_payload_raw_sha256: exact record digest
accepted_canonical_hash: exact canonical head
accepted_projection_raw_sha256: exact projection digest
accepted_projection_id: exact legal row
canonical_occupant_id: topology_occupant_0001
canonical_occupancy_kind: at_site | in_transition
canonical_occupancy_reference: exact site or transition ID
derived_local_subject_disposition: exact table value
published_anchor_identity: disposable local identity
published_subject_actor_count: 0 | 1
published_subject_actor_identities: exhaustive sorted list
head_state_at_receipt: synchronized
```

The receipt is necessary and insufficient. It proves what the adapter reports
publishing. Only agreement with the separate independent live-world
observation permits the harness to accept a current-head representation claim.
Neither document is canonical truth.

## Required primary witnesses

The freeze must choose an exact finite refresh-order matrix. The proposed
matrix covers both orders at both canonical transitions so no process role or
first-refresh role can become hidden authority:

| Witness | R0 → Rtransit refresh order | Rtransit → Rfinal refresh order |
|---|---|---|
| W1 | A then B | A then B |
| W2 | B then A | B then A |
| W3 | A then B | B then A |
| W4 | B then A | A then B |

Every witness begins from fresh isolated roots and two fresh original process
bindings. Every witness must prove:

1. exact R0 launch dispositions: A absent, B present;
2. uninterrupted A/B liveness through L0–L8;
3. exact byte-identical sealed start resolution and Rtransit;
4. exact head-unconfirmed then stale classification after Rtransit;
5. exact Rtransit positive anchors and zero subject Actors after both refreshes;
6. exact byte-identical sealed completion rediscovery and Rfinal;
7. exact head-unconfirmed then stale classification after Rfinal;
8. exact Rfinal dispositions: A present, B absent;
9. exact receipt/live-observation agreement at every synchronized checkpoint;
10. canonical record, ledger, ancestry, schedule, reservation, and replay
    equality across all four physical refresh schedules.

At L3 and L7, one domain is synchronized to the new head while its peer remains
stale at the immediate predecessor. The synchronized domain cannot authorize,
repair, refresh, inspect, or terminate its peer. The stale peer cannot delay or
invalidate the synchronized domain's lawful representation.

## Required controls

### C1 — canonical completion ignores physical synchronization

From fresh R0-synchronized processes, commit exact Rtransit, leave both domains
stale at R0, then invoke the exact sealed completion discovery and resolver
against Rtransit. Exact Rfinal must still commit byte-for-byte. Both physical
domains remain stale or terminate; direct R0-to-Rfinal refresh is not accepted.

This control proves canonical independence. It is not a successful final
materialization witness and does not weaken the primary immediate-successor
refresh law.

### C2 — lawful Rtransit absence is positive

From a valid Rtransit refresh candidate, independently remove or corrupt the
head anchor while leaving the subject Actor census at zero. The result must be
invalid, never synchronized. A zero-subject world cannot pass merely because
zero is the expected count.

### C3 — receipt-only publication is insufficient

Provide an internally valid materialization receipt while the independent live
world retains the predecessor anchor or subject Actor set. The harness must
reject the current-head claim and classify the domain invalid.

### C4 — guard-open canonical controls

Repeat each exact Phase-2 canonical resolution while the physical guard remains
open for the predecessor. The sealed canonical successor must still commit
byte-for-byte. The physical protocol then becomes failed-closed and affected
domains become protocol-invalid. This proves the guard cannot gate canonical
execution at either boundary.

### C5 — process replacement is not continuity

Terminate one original domain and launch a fresh process with copied payload,
projection, receipt, root contents, and declared binding fields. The new
process must be rejected as a replacement and cannot satisfy any L0–L8
checkpoint.

## Asymmetric failure obligations

The freeze must bind symmetric failures at both refresh cycles:

```yaml
Rtransit_refresh_failures:
  - A succeeds; B rejects before publication and remains stale at R0
  - B succeeds; A rejects before publication and remains stale at R0

Rfinal_refresh_failures:
  - A succeeds; B rejects before publication and remains stale at Rtransit
  - B succeeds; A rejects before publication and remains stale at Rtransit
```

Each failure uses a fresh process-bound live adapter path. The failure input,
rejection stage, disposition, prior anchor/Actor identity, target-head receipt
absence, peer liveness, peer representation, and canonical before/after state
must be recorded. A symmetric label swap is not sufficient evidence.

An asymmetric failure may not cause the successful peer to roll back, cause the
failed domain to publish a partial target state, or change canonical history.
Neither domain may observe the other's failure as an input.

## Current-head and occupancy authority adversaries

The reviewed freeze must enumerate an exact case-ID/action/disposition table.
At minimum it must reject:

1. R0, Rtransit, or Rfinal raw bytes whose digest is recomputed after mutation;
2. a canonical hash substituted for a raw digest or the reverse;
3. an unknown, missing, duplicate, reordered, or type-incompatible canonical member;
4. an altered occupant ID, occupancy kind, site ID, or transition ID;
5. a projection that redirects A or B to the other site;
6. a projection that supplies occupancy kind, expected presence, or expected count;
7. a cross-head projection/receipt/payload tuple;
8. a cross-domain projection/receipt/process-binding tuple;
9. a subject Actor in domain A at R0;
10. no subject Actor in domain B at synchronized R0;
11. any subject Actor in either synchronized Rtransit domain;
12. no positive Rtransit head anchor despite a zero-subject census;
13. no subject Actor in domain A at synchronized Rfinal;
14. any subject Actor in domain B at synchronized Rfinal;
15. duplicate subject Actors or duplicate head anchors;
16. a wrong occupant, wrong site, wrong head, or wrong process binding on an Actor;
17. a predecessor anchor retained beside a target anchor;
18. a predecessor subject Actor retained after target-head publication;
19. a destination Actor published before canonical Rfinal commits;
20. a route Actor, transform, timer, animation, collision, overlap, or navigation
    event presented as transition or completion authority;
21. R0 schedule state presented as completion work after Rtransit;
22. Actor disappearance presented as proof that Rtransit committed;
23. destination Actor creation presented as proof that completion committed;
24. a materialization receipt accepted without the independent live observation;
25. a live observation reconstructed from receipt or authoritative-derived JSON;
26. an expected disposition or expected Actor count visible to the probe;
27. a stale R0 or Rtransit representation relabeled synchronized;
28. a stale subject Actor presented as current occupancy;
29. direct R0-to-Rfinal refresh presented as an allowed catch-up;
30. an immediate-successor refresh attempted while the guard is closed;
31. a guard or head observation reaching the Phase-2 scheduler or resolver;
32. physical refresh order changing canonical bytes, ledger, ancestry, or schedule;
33. one domain's state, liveness, receipt, or observation used as the other's input;
34. process exit, EOF, replacement, birth-tuple mismatch, or root mismatch hidden by copied output;
35. a successful receipt after unprovable partial anchor/Actor publication;
36. local cache, Actor identity, transform, physics, or diagnostics merged into
    authoritative-derived target representation;
37. Pawn, possession, player input, Actor input, or auto-receive input reaching
    a Phase-4 path;
38. socket, watcher, polling, signal, environment, flag, console, timer, or
    shared-file refresh outside the sole frozen channel;
39. any physical domain constructing, selecting, delaying, rejecting, or
    publishing a canonical successor; and
40. any accepted evidence, scheduling, mutation, truth, player, network,
    movement, streaming, or production-authority claim.

Every applicable row must mechanically measure the exact canonical record,
ledger, ancestry, reservation, and unresolved-work state before and after the
adversary. A hard-coded `canonical_unchanged: true` summary is not evidence.

## Failure atomicity

Before freeze, every private construction and publication boundary must receive
an exact fault point. Required fault classes include:

- payload read/hash/parse and canonical validation;
- projection read/hash/parse and legal-row validation;
- operation receipt read/hash/parse and process-binding validation;
- occupancy derivation and exhaustive-disposition validation;
- candidate anchor construction;
- candidate subject Actor construction or destruction;
- candidate anchor/Actor coherence validation;
- old-representation quarantine;
- target anchor publication;
- target subject Actor-set publication;
- accepted-head publication;
- materialization receipt emission;
- independent live-anchor inspection;
- independent subject Actor census; and
- final synchronized-claim acceptance.

Each fault must execute at the real compiled adapter, router, live-probe, or
harness boundary selected by the freeze. Python-only replay of a live fault is
insufficient. Rejection before publication leaves the exact predecessor state
stale; uncertainty after any publication begins produces invalid state and
halts local execution.

## Canonical equivalence and replay

For every positive witness, control, and applicable failure case, the verifier
must independently recompute:

```yaml
R0_bytes_and_hash: exact sealed identity
start_boundary: exact H0_occ-bound identity
Rtransit_bytes_and_hash: exact sealed identity
Rtransit_ledger_and_ancestry: exact sealed identity
completion_boundary: freshly rediscovered exact Htransit_occ-bound identity
Rfinal_bytes_and_hash: exact sealed identity
Rfinal_ledger_and_ancestry: exact sealed identity
reservation_lifecycle: available_to_reserved_to_available
terminal_unresolved_work: empty
```

W1–W4 must be byte-identical in every canonical object despite their different
physical refresh orders. Repeating any witness from fresh roots and processes
must reproduce all deterministic canonical, projection, receipt, disposition,
and oracle artifacts byte-for-byte except the exact declared live process and
disposable Actor identity fields.

## Provenance and source/dataflow audit

The freeze must require surviving provenance for every launch, refresh,
observation, fault, and process identity. The release may not accept a compact
summary that cannot reconstruct each process-bound occurrence.

The source/dataflow audit must prove at least:

- the sealed Phase-2 scheduler/resolver remains the sole canonical mutation owner;
- Phase-4 code receives no canonical write or completion capability;
- occupancy disposition derives only from exact payload plus local site projection;
- the projection cannot announce expected occupancy or presence;
- the independent probe cannot read adapter state, receipt state, expected
  state, or harness pass/fail state;
- no Actor, transform, route, timer, collision, animation, or navigation value
  reaches canonical discovery, gates, resolution, or hashing;
- no other-domain value reaches a domain's construction or observation path;
- no alternate process input or refresh reader exists;
- every compiled source input read and call surface is exhaustively inventoried;
- exact source bytes are bound for every future authorized translation unit;
- no Pawn, controller, possession, player-input, network, movement, streaming,
  World Partition, or production path is introduced; and
- the source audit itself has mutation tests for new input, authority, oracle,
  identity, and call-surface paths.

## Evidence and release requirements before freeze

No evidence or release package is authorized now. Before a later freeze may
grant implementation, the specification must fix:

```yaml
future_release_contract:
  implementation_paths: exact_and_exhaustive
  unreal_paths: exact_and_exhaustive
  bounded_existing_source_changes: exact_and_exhaustive
  deterministic_artifact_roles: exact_ordered_set
  live_operational_artifact_roles: exact_ordered_set
  adversary_artifact_roles: exact_ordered_set
  governing_and_predecessor_members: exact_ordered_set
  source_and_project_members: exact_ordered_set
  manifest_member_count_excluding_manifest: exact
  artifact_directory_member_count: exact
  manifest: self_excluding_sorted_sha256
  review_time_document_validator: exact_non_release_QA
  post_seal_verification: exact_recorded_seal_commit_export
```

The eventual verifier must regenerate deterministic artifacts in isolation,
semantically validate live artifacts, rerun focused and predecessor tests,
reperform source/dataflow audits, reject verifier-specific in-memory
adversaries, enforce exact directory membership, and verify the manifest
without treating pass booleans as proof.

## Explicit exclusions

This candidate does not authorize or prove:

- physical traversal, movement, interpolation, animation, coordinates,
  distance, speed, progress, navigation, pathfinding, or arrival detection;
- route occupancy, route capacity, leases, traffic, collision, congestion,
  interruption, rerouting, or mid-transition topology mutation;
- more than one canonical subject, multiple simultaneous transitions,
  contention, split crews, 2+2 player topology, or player identity;
- Pawn embodiment, possession, input, weapons, gameplay, or local action;
- live external input, QA/QB/BEXT, evidence admission, arbitration, retry,
  re-admission, transport, networking, replication, rollback, reconciliation,
  host migration, save/load, or shared ownership;
- direct multi-generation physical catch-up, dynamic process creation,
  arbitrary domain counts, reconnect, recovery, or lifecycle management;
- World Partition, streaming, levels, Level Instances, cells, proximity
  promotion, production materialization, city scale, or performance;
- a new canonical payload, field, scheduler, resolver, topology, occupancy,
  transition, reservation, or completion law;
- stochastic identity, generalized planning, production architecture, Phase 5,
  Phase 6, or any capacity advancement; or
- successor implementation of any kind.

## Freeze-review gates

This draft may freeze only after independent review establishes:

```yaml
freeze_review:
  proof_question: exact
  phase_2_R0_Rtransit_Rfinal_artifacts: exact_and_byte_bound
  phase_2_scheduler_and_resolver_reuse: exact
  completion_rediscovery_from_Rtransit_only: exact
  phase_3_two_original_process_law: exact
  predecessor_noninheritance_and_new_obligations: explicit
  physical_domain_definition: exact
  process_binding_fields_and_verification_modes: exact
  L0_through_L8_liveness_matrix: exact
  six_projection_rows: exhaustive
  canonical_to_local_disposition_table: exhaustive
  positive_head_anchor_schema: exact
  independent_live_world_oracle: exact_and_non_self_validating
  lawful_zero_subject_Rtransit_proof: positive_and_exact
  subject_actor_schema_and_cardinality: exact
  physical_guard_states_and_transitions: exhaustive
  physical_dispositions_and_permissions: exhaustive
  immediate_successor_refresh_only: exact
  launch_and_refresh_input_inventory: exhaustive
  sole_refresh_channel: exact
  atomic_anchor_actor_head_publication: exact
  W1_through_W4_refresh_order_matrix: exact
  controls_C1_through_C5: exact
  asymmetric_failures_at_both_cycles: exact_and_symmetric
  authority_case_table: exact_and_exhaustive
  fault_points: exact_and_executed_at_real_boundaries
  canonical_before_after_measurement: exact
  canonical_equivalence_and_replay: exact
  process_provenance_and_runtime_trace: exact
  source_dataflow_and_input_closure: exact
  release_DAG_and_member_sets: exact
  review_time_validator_and_adversaries: exact
  exclusions: exact
```

The draft must not freeze with an ambiguous absence oracle, optional anchor,
receipt-only acceptance, incomplete Actor census, unspecified partial-
publication disposition, unbound refresh channel, generalized head/guard
abstraction, direct catch-up ambiguity, or any route from physical state to
canonical completion.

## Candidate acceptance statement

If a later frozen implementation passes every required gate, it may establish
only:

> **The exact sealed Phase-2 R0 → Rtransit → Rfinal occupancy chain can be
> represented across the same two original, simultaneously live Phase-3 Unreal
> domains. At each accepted head, an exact positive head anchor and independent
> live-world census prove that the sole canonical subject is represented only
> at its canonical endpoint, at neither endpoint while canonically in
> transition, and only at the destination after canonical completion. The
> sealed Phase-2 record remains the sole authority for occupancy, transition,
> completion, reservation, ledger, ancestry, and successor publication; stale
> or failed physical representation cannot alter that authority.**

It may not establish physical traversal, multiple subjects, players,
networking, streaming, arbitrary domains, production materialization, or any
capacity increase.

## Specification review history

### 0.1.0-draft.0 — 2026-08-29

- Selected the exact Phase-4 composition question for specification review
  only.
- Bound the candidate to the sealed Phase-2 R0/Rtransit/Rfinal bytes and the
  sealed Phase-3 two-original-process lifecycle without changing either.
- Proposed the six-row domain/head projection matrix, exhaustive local
  disposition table, positive head-anchor plus independent live-census oracle,
  two stale/refresh cycles, four refresh-order witnesses, canonical-
  independence controls, asymmetric failures, and exact authority exclusions.
- Kept implementation prohibited, capacity at v0.1.11, and every Phase-5,
  multiplayer, movement, network, streaming, and production scope closed.

## Current decision record

```yaml
working_unit: Cross-Domain Canonical Occupancy Materialization Proof v0.1.0-draft.0
phase: 4
successor_selected: true
specification_status: specification_review_only
freeze_status: not_frozen
implementation_authority: none
unreal_source_change_authority: none
evidence_status: not_created
canonical_capacity_change: none
latest_sealed_capacity: THE_CITY Development Capacity and Progress Note v0.1.11
```

No code may be written for this proof until a separately reviewed freeze fixes
the complete contract and explicitly grants bounded implementation authority.
