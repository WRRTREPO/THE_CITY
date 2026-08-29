# Cross-Domain Canonical Occupancy Materialization Proof

**Version:** 0.1.0\
**Status:** Frozen specification; exact bounded Phase-4 implementation, evidence, and release verification authorized; evidence unsealed\
**Selected:** 2026-08-29\
**Advanced to final freeze review:** 2026-08-29\
**Frozen:** 2026-08-29\
**Parent continuation:** [Co-op Open-City FPS Simulation — v0.7 Working Continuation](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)\
**Latest sealed predecessor:** [Simultaneous Physical Domains Proof — v0.1.1](Simultaneous%20Physical%20Domains%20Proof%20Evidence%20-%20v0.1.1.md)\
**Canonical source payload:** `CanonicalOccupancyTransitionPayload.v1` / `0.7.0-draft.65`, exact sealed R0 → Rtransit → Rfinal chain\
**Physical-lifecycle source:** `SimultaneousPhysicalDomainsProof.v1.1` / `0.7.0-draft.77`, exact sealed two-process law\
**Frozen proof-harness identity:** `CrossDomainCanonicalOccupancyMaterializationProof.v1` / `0.7.0-draft.80`

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
  version: 0.1.0
  status: frozen_specification
  frozen_proof_harness_identity: CrossDomainCanonicalOccupancyMaterializationProof.v1
  simulation_identity: 0.7.0-draft.80
  accepted_candidate_commit: fd2d62f404936eb961d7d1571204f1a352439bd7
  accepted_candidate_tree: b8b7bd6259d72c685ac5dee3c1488b19025b0fb3
  implementation_authority: bounded_phase_4_proof_only
  unreal_source_change_authority: exact_frozen_phase_4_paths_only
  evidence_authority: exact_frozen_phase_4_evidence_only
  release_authority: exact_frozen_phase_4_release_only
  capacity_advancement: none
  freeze_status: frozen
  evidence_status: unsealed
```

This reviewed forward freeze binds the exact accepted candidate commit
`fd2d62f404936eb961d7d1571204f1a352439bd7`, tree
`b8b7bd6259d72c685ac5dee3c1488b19025b0fb3`. It authorizes only the exact
bounded Phase-4 Python, Unreal, adapter, router, Actor, harness, test, evidence,
artifact, manifest, and release-verification surface declared below. It does
not authorize capacity advancement, production architecture, Phase 5, or any
adjacent successor scope.

Independent final freeze review of the first corrective candidate at commit
`299aa865c5757fb63aeef27a9c4eb48554dcea6f`, tree
`666bf7c70f04a4b1294c08aa5e003b97ff5fd836`, returned
`STOP_WITH_FINDINGS`. The corrected draft.1 revision closed that residual
ledger with one exact detached-JSON byte law, distinct logical and stored
process-binding orders, six exact liveness-adversary rows, four exact
malformed-projection rows, and success/fault/liveness-mode-complete harness
traces. Independent final freeze review then returned `ACCEPT_FOR_FREEZE` for
the exact candidate commit and tree bound above.

## Governing predecessor boundary

The imported predecessor identities are normative:

```yaml
phase_2_canonical_occupancy_transition:
  payload_schema: CanonicalOccupancyTransitionPayload.v1
  simulation_identity: 0.7.0-draft.65
  seal_commit: 638e1accc2076814b1f05458b2a55ecaa0a16232
  release_manifest_members: 33

phase_3_simultaneous_physical_domains:
  proof_harness_identity: SimultaneousPhysicalDomainsProof.v1.1
  simulation_identity: 0.7.0-draft.77
  accepted_candidate_commit: 4e14b39a01ba712bfe559d004b0383fc7d9db7d6
  accepted_candidate_tree: 9cd3d8568959cb6b3cfd5e9f06383a7efea6dd78
  forward_seal_commit: f72d6fbb87bcc5a047db0ab12f7447614ebee1fc
  forward_seal_tree: 5916ade67e25bf004d12df74b980fde4ec39bfaa
  release_manifest_members: 111
```

Phase 4 reuses the exact Phase-2 scheduler/resolver entry points and the
Phase-3 process-birth, pipe-continuity, harness-private head observation,
guard, stale quarantine, independent live-probe, proof-semantic-input, and
source-audit laws. It versions every Phase-4 schema, command, Actor, projection,
and output named below. “The same two original processes” means the same A/B
process instances from R0 through Rfinal inside each new Phase-4 witness; it
does not mean the historical Phase-3 process births or Actors are reused.

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
projection, input, or Actor schema. Every reused mechanism is named, versioned,
and rebound below to this exact three-head occupancy contract; no unnamed or
implicitly inherited mechanism is legal.

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
  implementation_authority: bounded_phase_4_proof_only
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

## Exact detached JSON byte identity

Unless a more specific rule below narrows a value enum, every detached Phase-4
JSON object uses this one stored-byte law. The law covers projections, process
bindings, bind/launch/materialize/inspect/fault/liveness invocations and
receipts, launch plans and surfaces, independent expected representations,
canonical-head observations, live observations, materialization receipts,
head dispositions, runtime events, harness events, occurrence-registry rows,
and their aggregate JSON artifacts. Unreal Actor field schemas are live fields,
not competing standalone serializations; when copied into a detached row they
obey this law.

```yaml
detached_json_byte_identity: CrossDomainOccupancyDetachedJsonBytes.v1
encoding: UTF-8 without BOM
object_member_order: recursively ascending raw UTF-8 key bytes
array_member_order: exact schema- or table-declared semantic order
member_set: exact closed schema; no omitted additional or duplicate member
numbers: base-10 JSON integers only; no float NaN or infinity
booleans_and_null: lowercase JSON true false null
string_escaping: shortest valid JSON escape form with non-ASCII emitted as UTF-8
separators: comma and colon only; no insignificant whitespace
stored_terminator: exactly one LF byte
raw_sha256: lowercase SHA-256 over the complete stored bytes including LF
trace_stream: canonical event objects concatenated by trace_sequence, one LF-terminated object per event
```

Every `*_raw_sha256` field whose referent is a Phase-4 detached JSON object uses
that exact stored-byte identity. Digests whose referent is an imported sealed
canonical payload, executable, project, translation unit, input member, or
other non-detached source instead hash the complete exact source bytes under
their separately declared source law. In particular,
`expected_representation_raw_sha256`, `live_observation_raw_sha256`, and
`materialization_receipt_raw_sha256` hash their complete closed objects plus
the one terminal LF; none may hash an in-memory structure, a subset, a pretty
rendering, or bytes without the terminator. The sole additional binding
identity is `operational_process_instance_id`, defined below over the same
canonical binding JSON bytes before the stored LF. Every trace event has its
own raw identity under this law, and the trace artifact identity covers the
exact ordered concatenation.

## Exact domain projection and occupancy derivation

Each domain receives the full exact canonical payload plus one detached
domain/head projection. The projection admits a site representation slot and a
subject representation slot, but it contains no occupancy kind, occupied site,
transition ID, expected subject presence, expected Actor count, completion
state, or expected live-observation result.

The frozen-candidate projection schema is a closed seven-member canonical JSON
object. Member order is raw UTF-8 lexicographic order at every object level;
serialization uses UTF-8, no insignificant whitespace, and one terminal LF:

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

The H aliases are normative and singular:

```yaml
H0_occ: b31e7ad0993e288ba80f50fb1960da5c67bad9bcc7cc39bf0ec0ebeeaad57dc8
Htransit_occ: 2640fe567b343e2229f875c9cf2d081f41aaaec2a3834e81e2efb3f9caa5da19
Hfinal_occ: 3a00d32115af74950923ac3362a8459d0e08043d45abbe91bcc573e27103db34
```

The exact legal matrix is closed:

| Domain | Canonical head | Projection ID | Site ID | Site slot | Subject slot | Projection raw SHA-256 |
|---|---|---|---|---|---|---|
| A | H0_occ | `cross_domain_A_R0_0001` | `topology_site_0001` | `domain_A_site_slot_01` | `domain_A_subject_slot_01` | `c175ee92a3c69adbbeebaeecdabb54e462bbea1aa99f43117c5205757bcc9624` |
| B | H0_occ | `cross_domain_B_R0_0001` | `topology_site_0002` | `domain_B_site_slot_01` | `domain_B_subject_slot_01` | `4d8da172945e1ff97433fe6230290f448d8731ac0dd5d3cef421e806b43531cb` |
| A | Htransit_occ | `cross_domain_A_Rtransit_0001` | `topology_site_0001` | `domain_A_site_slot_01` | `domain_A_subject_slot_01` | `1f57d0fc964956275008fffeb82adbb365f7c3343cce76d90e5cbd53262d68e6` |
| B | Htransit_occ | `cross_domain_B_Rtransit_0001` | `topology_site_0002` | `domain_B_site_slot_01` | `domain_B_subject_slot_01` | `1e72049befcbd9d1af6babaf855440c14101faa2d4aa5b97d13b9ae859d8d5dc` |
| A | Hfinal_occ | `cross_domain_A_Rfinal_0001` | `topology_site_0001` | `domain_A_site_slot_01` | `domain_A_subject_slot_01` | `723d9e539f3e0cebdab418dfacb25f8f2d6bbc0acd42c85a5330dca322a5e6c8` |
| B | Hfinal_occ | `cross_domain_B_Rfinal_0001` | `topology_site_0002` | `domain_B_site_slot_01` | `domain_B_subject_slot_01` | `1552fb88285ffe670f1866ac324ef4b61c51d4ec2c4977df84e23b97e8eb85b9` |

The exact canonical JSON bytes before the terminal LF are:

```json
{"allowed_site_projection":{"canonical_site_id":"topology_site_0001","representation_slot":"domain_A_site_slot_01"},"allowed_subject_projection":{"canonical_occupant_id":"topology_occupant_0001","representation_slot":"domain_A_subject_slot_01"},"domain_role":"domain_A","projection_id":"cross_domain_A_R0_0001","projection_schema":"CrossDomainCanonicalOccupancyProjection.v1","proof_scenario":"cross-domain-canonical-occupancy-materialization-v1","source_canonical_hash":"b31e7ad0993e288ba80f50fb1960da5c67bad9bcc7cc39bf0ec0ebeeaad57dc8"}
{"allowed_site_projection":{"canonical_site_id":"topology_site_0002","representation_slot":"domain_B_site_slot_01"},"allowed_subject_projection":{"canonical_occupant_id":"topology_occupant_0001","representation_slot":"domain_B_subject_slot_01"},"domain_role":"domain_B","projection_id":"cross_domain_B_R0_0001","projection_schema":"CrossDomainCanonicalOccupancyProjection.v1","proof_scenario":"cross-domain-canonical-occupancy-materialization-v1","source_canonical_hash":"b31e7ad0993e288ba80f50fb1960da5c67bad9bcc7cc39bf0ec0ebeeaad57dc8"}
{"allowed_site_projection":{"canonical_site_id":"topology_site_0001","representation_slot":"domain_A_site_slot_01"},"allowed_subject_projection":{"canonical_occupant_id":"topology_occupant_0001","representation_slot":"domain_A_subject_slot_01"},"domain_role":"domain_A","projection_id":"cross_domain_A_Rtransit_0001","projection_schema":"CrossDomainCanonicalOccupancyProjection.v1","proof_scenario":"cross-domain-canonical-occupancy-materialization-v1","source_canonical_hash":"2640fe567b343e2229f875c9cf2d081f41aaaec2a3834e81e2efb3f9caa5da19"}
{"allowed_site_projection":{"canonical_site_id":"topology_site_0002","representation_slot":"domain_B_site_slot_01"},"allowed_subject_projection":{"canonical_occupant_id":"topology_occupant_0001","representation_slot":"domain_B_subject_slot_01"},"domain_role":"domain_B","projection_id":"cross_domain_B_Rtransit_0001","projection_schema":"CrossDomainCanonicalOccupancyProjection.v1","proof_scenario":"cross-domain-canonical-occupancy-materialization-v1","source_canonical_hash":"2640fe567b343e2229f875c9cf2d081f41aaaec2a3834e81e2efb3f9caa5da19"}
{"allowed_site_projection":{"canonical_site_id":"topology_site_0001","representation_slot":"domain_A_site_slot_01"},"allowed_subject_projection":{"canonical_occupant_id":"topology_occupant_0001","representation_slot":"domain_A_subject_slot_01"},"domain_role":"domain_A","projection_id":"cross_domain_A_Rfinal_0001","projection_schema":"CrossDomainCanonicalOccupancyProjection.v1","proof_scenario":"cross-domain-canonical-occupancy-materialization-v1","source_canonical_hash":"3a00d32115af74950923ac3362a8459d0e08043d45abbe91bcc573e27103db34"}
{"allowed_site_projection":{"canonical_site_id":"topology_site_0002","representation_slot":"domain_B_site_slot_01"},"allowed_subject_projection":{"canonical_occupant_id":"topology_occupant_0001","representation_slot":"domain_B_subject_slot_01"},"domain_role":"domain_B","projection_id":"cross_domain_B_Rfinal_0001","projection_schema":"CrossDomainCanonicalOccupancyProjection.v1","proof_scenario":"cross-domain-canonical-occupancy-materialization-v1","source_canonical_hash":"3a00d32115af74950923ac3362a8459d0e08043d45abbe91bcc573e27103db34"}
```

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

The head anchor is exactly one live
`ACrossDomainOccupancyHeadAnchorActor`. Its role tag is
`cross_domain_occupancy/domain_A/head_anchor` or
`cross_domain_occupancy/domain_B/head_anchor`. Its closed ordered field schema
is:

```yaml
anchor_schema: CrossDomainOccupancyHeadAnchor.v1
proof_scenario: cross-domain-canonical-occupancy-materialization-v1
domain_role: domain_A | domain_B
operational_process_instance_id: exact_immutable_binding
process_binding_raw_sha256: exact binding digest
accepted_canonical_payload_raw_sha256: exact R0 | Rtransit | Rfinal raw digest
accepted_canonical_hash: H0_occ | Htransit_occ | Hfinal_occ
accepted_projection_raw_sha256: exact detached projection digest
accepted_projection_id: exact six-row value
projected_canonical_site_id: topology_site_0001 | topology_site_0002
projected_site_representation_slot: domain_A_site_slot_01 | domain_B_site_slot_01
projected_subject_representation_slot: domain_A_subject_slot_01 | domain_B_subject_slot_01
canonical_occupant_id: topology_occupant_0001
canonical_occupancy_kind: at_site | in_transition
canonical_occupancy_reference: topology_site_0001 | topology_site_0002 | occupancy_transition_0001
local_subject_disposition: present_at_local_site | remote_at_other_site | in_transition_out_of_domain
publication_generation: publication_0001 | publication_0002 | publication_0003
representation_publication_state: locally_published_unverified
```

The anchor is disposable representation state. It does not create a canonical
head, choose a disposition, complete a transition, authorize evidence, or
substitute for the canonical payload. Its identity changes at every accepted
generation. `locally_published_unverified` is not a head disposition and does
not permit a current-head claim.

When the exact disposition is `present_at_local_site`, the generation contains
exactly one `ACrossDomainOccupancySubjectActor` with the role tag
`cross_domain_occupancy/domain_A/domain_A_subject_slot_01` or
`cross_domain_occupancy/domain_B/domain_B_subject_slot_01` and this closed
ordered field schema:

```yaml
subject_schema: CrossDomainOccupancySubjectRepresentation.v1
proof_scenario: cross-domain-canonical-occupancy-materialization-v1
domain_role: domain_A | domain_B
operational_process_instance_id: exact_immutable_binding
process_binding_raw_sha256: exact binding digest
canonical_occupant_id: topology_occupant_0001
represented_site_id: exact projected canonical site
subject_representation_slot: exact role-specific subject slot
accepted_canonical_payload_raw_sha256: exact R0 or Rfinal raw digest
accepted_canonical_hash: H0_occ | Hfinal_occ
accepted_projection_raw_sha256: exact detached projection digest
accepted_projection_id: exact matching row
publication_generation: exact matching anchor generation
representation_publication_state: locally_published_unverified
```

Rtransit permits no subject Actor or route Actor. The head anchor is the exact
site/head representation surface; the site slot is therefore exercised. Phase
4 does not reuse or publish the Phase-3 route Actor and establishes symbolic
local-site correspondence only, not a transform-to-site or placement law.

### Independent expected representation

The harness derives one
`CrossDomainOccupancyExpectedRepresentation.v1` before it reads any adapter
receipt or live observation. Its only semantic inputs are independently opened
and authenticated exact canonical payload bytes plus exact projection bytes.
The constructor accepts only the three sealed raw-digest/canonical-hash pairs
and six exact projection byte strings above. A recomputed digest over altered
bytes is not in that allowlist and rejects.

```yaml
expected_schema: CrossDomainOccupancyExpectedRepresentation.v1
proof_scenario: cross-domain-canonical-occupancy-materialization-v1
domain_role: domain_A | domain_B
canonical_payload_raw_sha256: exact sealed raw digest
canonical_hash: H0_occ | Htransit_occ | Hfinal_occ
projection_raw_sha256: exact frozen projection digest
projection_id: exact six-row value
projected_canonical_site_id: exact role site
projected_site_representation_slot: exact role site slot
projected_subject_representation_slot: exact role subject slot
canonical_occupant_id: topology_occupant_0001
canonical_occupancy_kind: at_site | in_transition
canonical_occupancy_reference: exact site or transition ID
expected_local_subject_disposition: present_at_local_site | remote_at_other_site | in_transition_out_of_domain
expected_anchor_actor_count: 1
expected_subject_actor_count: 0 | 1
expected_proof_relevant_actor_count: 1 | 2
expected_route_actor_count: 0
expected_unexpected_proof_tagged_actor_count: 0
expected_pawn_count: 0
expected_controller_count: 1
expected_auto_receive_input_actor_count: 0
expected_phase_4_actor_input_binding_count: 0
expectation_source: independently_authenticated_payload_and_projection_only
```

After complete structural validation, output fields map exactly as follows:

| Output | Sole source |
|---|---|
| canonical payload raw digest and canonical hash | independently authenticated payload bytes |
| projection raw digest and ID | independently authenticated projection bytes |
| domain role, projected site, site slot, subject slot | exact projection row |
| occupant ID | `/current_causal_state/canonical_occupancy` sole member key |
| occupancy kind/reference | that member's closed tagged-union value |
| local disposition | equality of `at_site.site_id` to projected site, or exact `in_transition` kind |
| expected anchor count | constant `1` |
| expected subject count | `1` iff local disposition is `present_at_local_site`; otherwise `0` |
| expected proof-relevant Actor count | expected anchor count plus expected subject count |
| expected route and unexpected proof-tagged Actor counts | constant `0` |
| expected Pawn, auto-input, and Phase-4 input-binding counts | constant `0` |
| expected controller count | constant `1`, the inert unpossessed engine-base controller |

No ledger, ancestry, unresolved work, commitment state, reservation, receipt,
guard, live object, prior generation, cache, transform, route, process label,
or expected-result input may select an output. A function-scoped source audit
must prove that constructor signature and every reachable read.

### Exact independent live-world census

One non-UObject `FCrossDomainOccupancyLiveWorldProbe`, created before the first
materialization and retained by the non-Actor command router in the original
process, receives only the exact immutable process binding plus an inspection
command whose sequence label cannot select an expected head or count. The
probe is not spawned into the world and cannot become a census row. It has no
adapter, candidate, expected-representation, payload, projection, receipt,
guard, or harness-result pointer.

The probe inspects the one process-bound `/Engine/Maps/Entry` game world. It
walks every non-null Actor slot in every loaded `ULevel::Actors` array,
including objects marked hidden, beginning-destroy, or pending-kill, and sorts
rows by exact UObject path encoded as UTF-8. It inventories every Actor whose
class is either Phase-4 class, whose tag begins `cross_domain_occupancy/`, or
whose reflected proof field names a Phase-4 schema. It separately inventories
all `APawn`, all `AController`, every Actor with non-disabled
`AutoReceiveInput`, and every Actor/component input binding or delegate that
can reach a Phase-4 handler. The exact stdin router is inventoried separately
as a permitted non-Actor command surface. Null level slots are counted separately. Nothing may be omitted by
expected class, expected tag, visibility, registration, generation, or
lifecycle state.

The exact closed observation schema is:

```yaml
observation_schema: CrossDomainOccupancyLiveObservation.v1
proof_scenario: cross-domain-canonical-occupancy-materialization-v1
domain_role: domain_A | domain_B
operational_process_instance_id: exact observed process binding
process_binding_raw_sha256: exact observed binding digest
inspection_id: inspection_0001 | inspection_0002 | inspection_0003 | inspection_0004 | inspection_0005 | inspection_0006 | inspection_0007 | inspection_0008 | inspection_0009 | inspection_c1_terminal_0001 | inspection_c2_rejection_0001 | inspection_c3_rejection_0001
observed_publication_generation: publication_0001 | publication_0002 | publication_0003 | null
world_package_name: /Engine/Maps/Entry
world_instance_identity: exact process-local observed identity
world_type: Game
loaded_level_count: exact nonnegative integer
level_actor_slot_count: exact nonnegative integer
null_level_actor_slot_count: exact nonnegative integer
proof_relevant_actor_count: exact nonnegative integer
proof_relevant_actor_rows: exhaustive sorted closed rows
anchor_actor_count: exact nonnegative integer
anchor_actor_rows: exhaustive sorted CrossDomainOccupancyHeadAnchor.v1 live-field rows
subject_actor_count: exact nonnegative integer
subject_actor_rows: exhaustive sorted CrossDomainOccupancySubjectRepresentation.v1 live-field rows
route_actor_count: exact nonnegative integer
route_actor_rows: exhaustive sorted class/path/tag rows
unexpected_proof_tagged_actor_count: exact nonnegative integer
unexpected_proof_tagged_actor_rows: exhaustive sorted rows
pawn_count: exact nonnegative integer
pawn_rows: exhaustive sorted class/path/possession rows
controller_count: exact nonnegative integer
controller_rows: exhaustive sorted class/path/pawn/input-enabled rows
auto_receive_input_actor_count: exact nonnegative integer
auto_receive_input_actor_rows: exhaustive sorted rows
phase_4_actor_input_binding_count: exact nonnegative integer
phase_4_actor_input_binding_rows: exhaustive sorted owner/delegate/input-source rows
observation_source: exhaustive_live_ue_world_census
```

Every count must equal its exact list length. Each Actor row records exact class,
path, tags, hidden/registration/lifecycle state, publication generation, and all
live reflected proof fields. Duplicates are recorded as counts greater than one,
never made unrepresentable by a `0 | 1` schema. Any wrong-world, orphaned,
untagged Phase-4 class, malformed tag, wrong generation, route Actor,
destroying, pending-kill, unexpected proof-tagged, Pawn, non-disabled
auto-input, or Phase-4 command-bound row is invalid.

The sole controller row must be exact class `/Script/Engine.PlayerController`,
Pawn null, possession absent, and Phase-4 handler reachability false. A missing,
additional, subclassed, possessed, or Phase-4-reachable controller row is
invalid. Any Pawn, non-disabled auto-input Actor, or Phase-4 command-bound row
is invalid.

At an accepted census, `proof_relevant_actor_count` equals
`anchor_actor_count + subject_actor_count`; the route and unexpected-tagged
lists are empty, so no other Phase-4 Actor class or tag exists in the world.

The harness compares the independently derived expectation separately with the
adapter receipt and the live observation; receipt/live agreement without
expectation agreement rejects. For `present_at_local_site`, exactly one anchor
and one exact subject Actor agree on every identity and generation field. For
either lawful absence disposition, the exact anchor exists and the exhaustive
subject Actor census is zero. A zero count without the exact anchor is invalid.
Only after expected representation, receipt, live census, private head
observation, process binding, and matching open guard all agree may the harness
write a `synchronized` disposition.

## Subject representation law

A subject representation Actor is permitted only for
`present_at_local_site`. It is a read-only expression of one accepted canonical
fact. It owns no occupancy, completion, transition, reservation, scheduling,
evidence, or mutation authority.

The Actor contains exactly the closed
`CrossDomainOccupancySubjectRepresentation.v1` fields above plus its disposable
UObject path, exact class, exact role tag, hidden/registration/lifecycle facts,
and no other reflected Phase-4 member.

It may not contain or derive:

- an authoritative transform-to-site rule;
- route progress, arrival, distance, speed, interpolation, or navigation state;
- a completion timer, callback, trigger, overlap, animation event, or collision
  event with canonical effect;
- a retained canonical boundary or scheduler capability;
- another domain's state, liveness, subject Actor, or projection;
- a local substitute for the canonical occupancy tagged union; or
- a canonical write, ledger, ancestry, reservation, or successor path.

The proof requires and accepts zero Pawn, zero possession, zero non-disabled
`AutoReceiveInput`, and zero Actor/delegate/input binding that can reach a
Phase-4 handler. Each `-game` process contains exactly one unpossessed inert
engine-base `/Script/Engine.PlayerController`, matching the established
Phase-3 bootstrap: its Pawn is null, it cannot call the Phase-4 router, adapter,
or probe, and no controller/player/input value may enter proof semantics. No
other `AController` is legal. The Phase-4 `CityProofGameMode.cpp` branch sets
`DefaultPawnClass`, `SpectatorClass`, and `HUDClass` to null, sets both
controller classes to `APlayerController`, starts players as spectators, and
returns before every Pawn creation, possession, view-target, or input-binding
path. Engine/platform input objects, if present behind the inert controller,
are inventoried as nonsemantic context and must expose no Phase-4 handler edge.

## Exact process identity and lifetime

Phase 4 versions the Phase-3 birth law as the exact ordered 22-member logical
validation schema
`CrossDomainOccupancyProcessBinding.v1` object:

```yaml
binding_schema: CrossDomainOccupancyProcessBinding.v1
proof_scenario: cross-domain-canonical-occupancy-materialization-v1
witness_id: exact closed enum below
domain_role: domain_A | domain_B
harness_launch_id: witness_id/domain_role/launch_0001
pid: positive integer
macos_process_start:
  seconds: nonnegative integer
  microseconds: integer 0 through 999999
executable_realpath: exact absolute realpath
executable_raw_sha256: lowercase SHA-256
unreal_engine_build_identity: exact UE 5.8 build identity
entry_map_package_identity: /Engine/Maps/Entry
project_realpath: exact absolute realpath
project_raw_sha256: lowercase SHA-256
project_config_and_module_inventory_raw_sha256: lowercase SHA-256
process_root_realpath: exact absolute realpath
launch_argv_raw_sha256: lowercase SHA-256 of exact ordered argv
launch_environment_audit_raw_sha256: lowercase SHA-256 of redacted complete audit
launch_cwd_realpath: exact repository root realpath
inherited_descriptor_map_raw_sha256: lowercase SHA-256
control_pipe_id: exact original stdin-pipe harness identity
structured_output_pipe_id: exact original stdout-pipe harness identity
diagnostic_pipe_id: exact original stderr-pipe harness identity
```

The displayed order is the exact logical validation enumeration, including
`binding_schema` as logical field 1 and `diagnostic_pipe_id` as logical field
22. It is not the stored JSON member order. Under the detached-byte law, the
exact stored top-level order is:

```yaml
binding_canonical_top_level_member_order:
  - binding_schema
  - control_pipe_id
  - diagnostic_pipe_id
  - domain_role
  - entry_map_package_identity
  - executable_raw_sha256
  - executable_realpath
  - harness_launch_id
  - inherited_descriptor_map_raw_sha256
  - launch_argv_raw_sha256
  - launch_cwd_realpath
  - launch_environment_audit_raw_sha256
  - macos_process_start
  - pid
  - process_root_realpath
  - project_config_and_module_inventory_raw_sha256
  - project_raw_sha256
  - project_realpath
  - proof_scenario
  - structured_output_pipe_id
  - unreal_engine_build_identity
  - witness_id
```

The nested birth tuple is stored in this exact order:

```yaml
macos_process_start_canonical_member_order:
  - microseconds
  - seconds
```

`operational_process_instance_id` is the lowercase SHA-256 of the complete
canonical binding JSON bytes before the stored LF;
`process_binding_raw_sha256` hashes those same bytes plus exactly one LF.
Neither ID is caller-selected. No implementation may serialize the logical
validation enumeration as stored member order.

The bind command is one closed object; it carries no second identity surface:

```yaml
bind_invocation_schema: CrossDomainOccupancyBindInvocation.v1
proof_scenario: cross-domain-canonical-occupancy-materialization-v1
command_sequence: 0
process_binding: exact complete CrossDomainOccupancyProcessBinding.v1 object
operational_process_instance_id: exact independently derived binding identity
process_binding_raw_sha256: exact stored binding digest
```

It uses the same canonical JSON rule and is written as those bytes plus one LF.
The child reserializes `process_binding`, independently derives both identities,
and accepts the command only when the echoed scalar identities, all 22 fields,
and its direct observations agree.

The exact witness-ID enum is:

```yaml
CrossDomainOccupancyWitnessId.v1:
  - w1_A_B__A_B
  - w2_B_A__B_A
  - w3_A_B__B_A
  - w4_B_A__A_B
  - c1_canonical_completion_independence
  - c2_positive_Rtransit_absence
  - c3_receipt_only_rejection
  - c4a_start_guard_open
  - c4b_completion_guard_open
  - c5_process_replacement
  - af_Rtransit_A_success_B_failure
  - af_Rtransit_B_success_A_failure
  - af_Rfinal_A_success_B_failure
  - af_Rfinal_B_success_A_failure
  - fault_head_publication
  - fault_materialization
  - fault_live_observation
  - authority_adversary
  - process_binding_adversary
  - liveness_adversary
  - replay_repeat
```

Field verification modes are exact:

```yaml
compiled_constant_identity:
  - binding_schema
  - proof_scenario
harness_frozen_launch_plan_identity:
  - witness_id
  - domain_role
  - harness_launch_id
harness_created_and_independently_reobserved_identity:
  - control_pipe_id
  - structured_output_pipe_id
  - diagnostic_pipe_id
  - process_root_realpath
independent_process_observation:
  - pid
  - macos_process_start
  - executable_realpath
  - executable_raw_sha256
  - unreal_engine_build_identity
  - entry_map_package_identity
  - project_realpath
  - project_raw_sha256
  - project_config_and_module_inventory_raw_sha256
  - launch_argv_raw_sha256
  - launch_environment_audit_raw_sha256
  - launch_cwd_realpath
  - inherited_descriptor_map_raw_sha256
```

Before spawn, the harness creates one immutable
`CrossDomainOccupancyLaunchPlan.v1` row from the frozen witness/control matrix,
domain role, `launch_0001`, a newly created role-private process root, and the
three dedicated pipe kernel endpoints. No child, stored receipt, or later
evidence label supplies that row. The harness reobserves root and endpoint
identities after spawn and requires the binding to equal the registered plan.
The plan selects only proof occurrence and local projection role; it has no
canonical head, occupancy answer, expected count, result, or canonical-call
field.

```yaml
launch_plan_schema: CrossDomainOccupancyLaunchPlan.v1
proof_scenario: cross-domain-canonical-occupancy-materialization-v1
witness_id: exact closed witness ID
domain_role: domain_A | domain_B
harness_launch_id: witness_id/domain_role/launch_0001
process_root_realpath: exact newly created role-private root
control_pipe_id: exact newly created stdin-pipe identity
structured_output_pipe_id: exact newly created stdout-pipe identity
diagnostic_pipe_id: exact newly created stderr-pipe identity
```

The canonical launch-plan bytes and raw SHA-256 are retained in the occurrence
registry before spawn. The binding repeats these seven planned identity fields
exactly; it does not receive or trust a caller-supplied launch-plan digest.

The harness launches each direct child with macOS
`POSIX_SPAWN_START_SUSPENDED`, independently obtains the PID/start pair through
`proc_pidinfo` / `PROC_PIDTBSDINFO`, registers the exit watch, constructs the
complete binding, and writes exactly one canonical-JSON
`CrossDomainOccupancyBindInvocation.v1` plus LF to the original stdin pipe
before resuming the child. A second bind, incomplete bind, resume-before-bind,
declared-only identity, or mismatch rejects before materialization.

The child validates the compiled constants, launch-ID construction, role/root
relationship, and every locally observable process/root/descriptor field. The
harness separately validates the complete object against its immutable launch
plan and independent OS observations before it accepts any echoed binding ID.
Neither side can replace an unverified copied label with authority.

Every accepted output echoes both binding identities. The complete process
population must have unique operational IDs, birth tuples, launch IDs, roots,
and pipe kernel identities. The source/dataflow audit must prove that
`witness_id`, launch ID, PID, process-start value, paths, digests, environment,
argv, and pipe IDs can identify evidence but cannot select occupancy,
generation contents, expected counts, canonical execution, or pass/fail.

The executable adversary suite mutates each of the 22 fields individually in
cases `PB01` through `PB22`, preserving all other stored fields and recomputing
caller-controlled enclosing digests. Each fresh process rejects before
materialization. `PB23` coherently relabels witness ID, harness launch ID, and
all copied evidence labels while retaining the independently observed process
birth/root/pipe facts; it also rejects before materialization with no trace
past binding verification.

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

From first binding through L8, the harness continuously retains the original
direct-child handles and exact pipe endpoints and records:

```yaml
continuous_monitor:
  original_child_handle_exit_observed: false
  wait_status_available: false
  control_pipe_unexpected_eof: false
  structured_output_pipe_unexpected_eof: false
  process_start_pair_changed: false
  replacement_spawn_count: 0
```

A checkpoint or terminal liveness sample is one closed detached object:

```yaml
liveness_observation_schema: CrossDomainOccupancyLivenessObservation.v1
proof_scenario: cross-domain-canonical-occupancy-materialization-v1
occurrence_id: exact registered occurrence
checkpoint_id: L0 | L1 | L2 | L3 | L4 | L5 | L6 | L7 | L8 | terminal_failure
domain_role: domain_A | domain_B
operational_process_instance_id: exact original binding identity
process_binding_raw_sha256: exact original binding digest
sample_sequence: contiguous nonnegative integer per domain occurrence
observed_pid: exact independently observed integer
observed_macos_process_start:
  seconds: exact independently observed nonnegative integer
  microseconds: exact independently observed integer 0 through 999999
original_child_handle_exit_observed: true | false
wait_status_available: true | false
wait_status_value: exact integer | null iff unavailable
control_pipe_unexpected_eof: true | false
structured_output_pipe_unexpected_eof: true | false
process_start_pair_changed: true | false
replacement_spawn_count: exact nonnegative integer
observation_source: independent_harness_os_monitor
```

Only `independent_harness_os_monitor` may satisfy a checkpoint. The harness
constructs it from the retained direct-child handle, fresh `proc_pidinfo`,
nonblocking `waitpid`, registered kqueue/poll state, pipe kernel endpoints, and
its private spawn registry. `process_start_pair_changed` therefore means only
that the fresh OS-observed PID/start pair differs from the immutable accepted
binding; it never summarizes a child claim. A receipt, copied binding, or peer
value cannot satisfy liveness.

LV03 alone emits one separately typed child-authored report:

```yaml
liveness_adversarial_report_schema: CrossDomainOccupancyLivenessAdversarialReport.v1
proof_scenario: cross-domain-canonical-occupancy-materialization-v1
occurrence_id: exact fresh LV03 occurrence
case_id: LV03
checkpoint_id: L2
domain_role: domain_A
command_sequence: 5
action_id: emit_changed_start_report
operational_process_instance_id: exact original binding identity
process_binding_raw_sha256: exact original binding digest
report_sequence: 0
reported_pid: exact immutable binding PID
reported_macos_process_start:
  seconds: exact immutable binding seconds plus 1
  microseconds: exact immutable binding microseconds
report_source: adversarial_child_report
```

This report is adversarial input, not a liveness observation. It cannot satisfy
a checkpoint or populate an `independent_harness_os_monitor` field. The harness
retains its exact bytes and separately samples the real PID/start pair before
classifying the explicit report-to-binding-and-OS mismatch.

A registered macOS `kqueue` `EVFILT_PROC` / `NOTE_EXIT` watch, nonblocking
`waitpid`, pipe EOF watches, and fresh `proc_pidinfo` samples provide the
independent observations. Liveness adversaries use one harness-private plan;
only LV03–LV05 also send one process-side failure-only invocation on the
original stdin pipe. Neither channel can produce a passing checkpoint.

```yaml
liveness_plan_schema: CrossDomainOccupancyLivenessAdversaryPlan.v1
proof_scenario: cross-domain-canonical-occupancy-materialization-v1
occurrence_id: exact fresh registered liveness occurrence
case_id: LV01 | LV02 | LV03 | LV04 | LV05 | LV06
base_schedule: exact W1 canonical and command prefix through named checkpoint
domain_role: exact table role
checkpoint_id: exact table checkpoint
edge: after_checkpoint_acceptance
channel: harness_process_control | original_stdin
action_id: kill_original_child_note_exit | kill_original_child_waitpid | emit_changed_start_report | close_control_read_endpoint | close_structured_output_write_endpoint | spawn_copied_label_replacement
expected_first_failure: exact table monitor predicate
terminal_liveness_failure_code: original_process_exit | original_process_wait_status | reported_process_start_pair_mismatch | original_control_pipe_closed | original_output_pipe_closed | copied_label_replacement_detected
harness_run_id: exact current harness run
```

```yaml
liveness_invocation_schema: CrossDomainOccupancyLivenessAdversaryInvocation.v1
proof_scenario: cross-domain-canonical-occupancy-materialization-v1
command_sequence: exact table sequence
operation: execute_liveness_adversary_once
case_id: LV03 | LV04 | LV05
action_id: emit_changed_start_report | close_control_read_endpoint | close_structured_output_write_endpoint
operational_process_instance_id: exact original bound process
liveness_plan_raw_sha256: exact authenticated private-plan digest
```

```yaml
liveness_arm_receipt_schema: CrossDomainOccupancyLivenessAdversaryArmReceipt.v1
proof_scenario: cross-domain-canonical-occupancy-materialization-v1
case_id: exact LV03 | LV04 | LV05
action_id: exact matching action
operational_process_instance_id: exact original bound process
liveness_invocation_raw_sha256: exact measured stdin-line digest
arm_state: armed_once_before_action
```

The six-case matrix is exact. Every case uses a fresh pair and the exact W1
prefix; “after” means after both domains' checkpoint rows are accepted and
before any next normal action. `SIGKILL` is sent only to the exact retained
direct-child PID. For LV01 the kqueue event is consumed before `waitpid`; for
LV02 the terminal `waitpid` status is consumed before the queued kqueue event.
At the first required failure, the sole global guard transitions to absorbing
`failed_closed` and both original domains receive terminal
`protocol_invalid / physical_protocol_violation` dispositions. Any row's
preserved synchronized, head-unconfirmed, or stale wording describes only its
last Actor generation and live census before that terminal disposition; it is
not a surviving current-head claim.

| Case | Role | Checkpoint / edge | Channel and exact action | Required first failing observation | Exact terminal trace and disposition |
|---|---|---|---|---|---|
| LV01 | A | L0 / after | `kill_original_child_note_exit`: harness `kill(original_A_pid, SIGKILL)` | `original_child_handle_exit_observed=true` from `NOTE_EXIT` | accepted traces end at L0; both originals terminal protocol-invalid; `liveness_failure_code=original_process_exit`; B's last physical generation/census remains R0; canonical R0 unchanged; terminate pair |
| LV02 | B | L1 / after | `kill_original_child_waitpid`: harness `kill(original_B_pid, SIGKILL)` | `wait_status_available=true` with exact non-null status | accepted traces end at L1; both originals terminal protocol-invalid; `liveness_failure_code=original_process_wait_status`; A's last physical generation/census remains head-unconfirmed R0; exact Rtransit unchanged; terminate pair |
| LV03 | A | L2 / after | `emit_changed_start_report`: stdin sequence 5; arm receipt, then emit the exact closed LV03 adversarial-report row whose reported start seconds equal immutable binding seconds plus 1 | reported start pair differs from both immutable binding and fresh `proc_pidinfo`; the independent terminal sample retains `process_start_pair_changed=false` | process trace appends entered then completed `liveness_LV03_emit_changed_start_report` events and binds the report identity; both originals terminal protocol-invalid; `liveness_failure_code=reported_process_start_pair_mismatch`; B's last physical generation/census remains stale R0; exact Rtransit unchanged; terminate pair |
| LV04 | B | L3 / after | `close_control_read_endpoint`: stdin sequence 6; arm receipt, emit the entered action event, then close original fd 0 read endpoint and emit the completed action event on fd 1 | harness poll of retained control write endpoint reports `POLLERR` or `POLLHUP`; `control_pipe_unexpected_eof=true` | process trace ends with entered then completed `liveness_LV04_close_control_read_endpoint` events; both originals terminal protocol-invalid; `liveness_failure_code=original_control_pipe_closed`; A's last physical generation/census remains Rtransit; exact Rtransit unchanged; terminate pair |
| LV05 | A | L5 / after | `close_structured_output_write_endpoint`: stdin sequence 9; arm receipt, flush prior output, emit the entered action event, flush it, then close original fd 1 write endpoint | harness read/kqueue on retained structured-output endpoint reports EOF; `structured_output_pipe_unexpected_eof=true` | process trace ends with the entered `liveness_LV05_close_structured_output_write_endpoint` event and no completed event; both originals terminal protocol-invalid; `liveness_failure_code=original_output_pipe_closed`; B's last physical generation/census remains head-unconfirmed Rtransit; exact Rfinal unchanged; terminate pair |
| LV06 | B | L7 / after | `spawn_copied_label_replacement`: harness launches one fresh third child from a new disjoint root with copied B labels while original B remains alive | private spawn registry records `replacement_spawn_count=1`; new PID/start/binding cannot equal original | replacement is `unbound / binding_not_accepted` with zero process trace; both originals terminal protocol-invalid; `liveness_failure_code=copied_label_replacement_detected`; last physical generations remain B/Rtransit and A/Rfinal; exact Rfinal unchanged; terminate all three |

The liveness plan and any process invocation/receipt obey the detached-byte
law. LV03–LV05 commands are accepted only for witness ID
`liveness_adversary`, their exact case/role/checkpoint/sequence rows, and one
unused arm; all cross-products reject. Their process trace has the successful
checkpoint prefix, the exact named liveness action edge, and no later normal
command. LV01, LV02, and LV06 retain exact harness action/OS-call evidence and
have no invented process command. No case changes canonical bytes or the
peer's last valid detached physical state.

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

Each checkpoint also carries one exact ordered runtime-trace sample for each
domain. L0, L4, and L8 include receipt plus independent live census. L1 and L5
prove the predecessor anchor/subject generation remains present and no target
generation exists before head publication. L2 and L6 repeat that census after
the independently observed successor and stale classification. L3 and L7 bind
both domains in one harness sampling interval: the refreshed role has the exact
target anchor/Actor set and the peer retains the exact quarantined predecessor
generation, with no premature peer target object. The maximum separation
between the two process samples is one completed harness polling cycle; both
original child handles and pipe monitors must remain live before and after the
pair. Receipt-only intermediate state is insufficient.

## Exact physical current-head guard

The harness-private current-head observer publishes exactly two successor
observations. It opens the committed successor file independently with
`openat(O_RDONLY|O_CLOEXEC|O_NOFOLLOW)`, verifies regular-file identity before
and after one read, authenticates the exact raw digest and canonical hash, and
derives parent/sequence from the canonical record itself. It consumes no Unreal,
receipt, guard, expected materialization, or other-domain value.

```yaml
observation_schema: CrossDomainOccupancyCanonicalHeadObservation.v1
observation_sequence: head_observation_0001 | head_observation_0002
source_record_role: Rtransit | Rfinal
source_record_realpath: exact isolated canonical-output path
source_record_device: independently observed integer
source_record_inode: independently observed integer
source_record_mode: regular_file_only
source_record_size: exact independently observed integer
source_record_raw_sha256: exact sealed raw digest
observed_canonical_hash: Htransit_occ | Hfinal_occ
observed_parent_canonical_hash: H0_occ | Htransit_occ
observed_ledger_entry_count: 1 | 2
observed_unresolved_work_count: 1 | 0
publication_state: harness_private_verified
```

The only legal rows are
`head_observation_0001/Rtransit/Htransit_occ/H0_occ/1/1` and
`head_observation_0002/Rfinal/Hfinal_occ/Htransit_occ/2/0`, with the exact raw
digests declared above. The harness constructs a private candidate, validates
all fields, writes one detached observation artifact through a new regular
temporary file, `fsync`s it, atomically renames it to the harness-private
published path, reopens and reverifies it, and only then changes stale
classification or performs a legal guard transition. For C1's Rfinal
observation, the stale classification advances to the exact terminal
R0/Rfinal relation while `closed_for_c1_Rtransit_to_Rfinal` remains closed.
Unreal cannot name, enumerate, inherit, open, or receive that path or any
derived field.

The exact nine publication stages are `open_source`, `pre_stat_source`,
`read_source_once`, `post_stat_source`, `authenticate_record`,
`construct_private_observation`, `write_and_fsync_candidate`,
`atomic_publish`, and `reopen_and_reverify`. The harness-private fault mapping
is exact; every row injects after the named stage and before the next normal
action or acceptance:

| Case | Head operation | Stage | Edge |
|---|---|---|---|
| HF01 | `head_observation_0001` | `open_source` | after |
| HF02 | `head_observation_0001` | `pre_stat_source` | after |
| HF03 | `head_observation_0001` | `read_source_once` | after |
| HF04 | `head_observation_0001` | `post_stat_source` | after |
| HF05 | `head_observation_0001` | `authenticate_record` | after |
| HF06 | `head_observation_0001` | `construct_private_observation` | after |
| HF07 | `head_observation_0001` | `write_and_fsync_candidate` | after |
| HF08 | `head_observation_0001` | `atomic_publish` | after |
| HF09 | `head_observation_0001` | `reopen_and_reverify` | after |
| HF10 | `head_observation_0002` | `open_source` | after |
| HF11 | `head_observation_0002` | `pre_stat_source` | after |
| HF12 | `head_observation_0002` | `read_source_once` | after |
| HF13 | `head_observation_0002` | `post_stat_source` | after |
| HF14 | `head_observation_0002` | `authenticate_record` | after |
| HF15 | `head_observation_0002` | `construct_private_observation` | after |
| HF16 | `head_observation_0002` | `write_and_fsync_candidate` | after |
| HF17 | `head_observation_0002` | `atomic_publish` | after |
| HF18 | `head_observation_0002` | `reopen_and_reverify` | after |

HF uses only the harness-private plan/receipt channel defined below; no HF arm
is written to an Unreal process. Before atomic publication the old
guard/dispositions remain; uncertainty at or after publication forces
`failed_closed` and `protocol_invalid` physical state. Exact Phase-2 canonical
records remain unchanged in every case.

The Phase-4 guard is operational protocol state only. It may control acceptance
of a physical current-head representation claim and refresh eligibility. It may
not enter Phase-2 boundary discovery, gate evaluation, resolver execution,
record construction, ledger, ancestry, canonical hashing, or publication.

The exact states are:

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

closed_for_c1_Rtransit_to_Rfinal:
  accepted_physical_head: none
  refresh_target: none

open_for_Rfinal:
  accepted_physical_head: Hfinal_occ
  refresh_target: Hfinal_occ

failed_closed:
  accepted_physical_head: none
  refresh_target: none
```

For W1–W4 and every other successful normal-path occurrence, the transition
order is exact:

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

C1 is the sole exception to the normal completion-close precondition. After
exact Rtransit observation, both original domains must be classified
`stale(R0/Rtransit)`, no Rtransit refresh command may have been sent or
accepted, and the registered occurrence must be exactly
`c1_canonical_completion_independence`. Only then does the harness transition
`open_for_Rtransit` → `closed_for_c1_Rtransit_to_Rfinal` immediately before
invoking exact completion. That state never opens for Rfinal. After exact
Rfinal observation, the same two domains receive the terminal
`stale(R0/Rfinal) / multigeneration_control_terminal` disposition, perform one
final census, and terminate. This close cannot be used by W1–W4, C4b, or any
other occurrence.

Opening for a new head before exact canonical observation and all required
stale classifications is a protocol failure. Leaving the guard open for the
source head during either canonical invocation must not prevent the exact
canonical commit; it must instead end the physical protocol `failed_closed`
and classify affected physical dispositions `protocol_invalid`.

The guard is one harness-global, non-file, non-environment, non-Unreal state
machine. Its only writer is the exact harness transition function. Legal
transitions are closed:

| From | To | Sole trigger and precondition |
|---|---|---|
| `open_for_R0` | `closed_for_R0_to_Rtransit` | before invoking the exact start resolver |
| `closed_for_R0_to_Rtransit` | `open_for_Rtransit` | verified Rtransit observation plus atomic stale-R0 classification for A and B |
| `open_for_Rtransit` | `closed_for_Rtransit_to_Rfinal` | after both domains synchronize to Rtransit and before invoking exact completion |
| `open_for_Rtransit` | `closed_for_c1_Rtransit_to_Rfinal` | C1 only: verified Rtransit observation, both original domains stale at R0, no Rtransit refresh sent or accepted, immediately before exact completion |
| `closed_for_Rtransit_to_Rfinal` | `open_for_Rfinal` | verified Rfinal observation plus atomic stale-Rtransit classification for A and B |
| any state except `failed_closed` | `failed_closed` | one recorded protocol violation or post-publication uncertainty |

`failed_closed` is absorbing.
`closed_for_c1_Rtransit_to_Rfinal` has no normal-success outgoing transition;
it permits only the C1 Rfinal observation, terminal disposition/census,
diagnostics, and termination sequence above. Its sole outgoing failure edge is
to `failed_closed` after a recorded protocol violation or post-publication
uncertainty. Repeated transition requests, skipped states, reverse transitions,
opening from only one stale classification, opening from an unverified
observation, and all other ordered pairs reject. Guard state is never
serialized into a canonical call, and static plus runtime dataflow audit must
prove no edge to Phase-2 discovery, resolution, record construction, ledger,
ancestry, hashing, or publication.

## Exact physical head dispositions

Only the harness emits a head disposition, after independent expectation,
receipt, live census, private head, process binding, and guard checks. The
closed ordered schema is:

```yaml
disposition_schema: CrossDomainOccupancyHeadDisposition.v1
proof_scenario: cross-domain-canonical-occupancy-materialization-v1
domain_role: domain_A | domain_B
operational_process_instance_id: exact original binding identity
process_binding_raw_sha256: exact original binding digest
expected_representation_raw_sha256: independent expectation digest | null
materialization_receipt_raw_sha256: representation receipt digest | null
live_observation_raw_sha256: exhaustive census digest | null
represented_canonical_hash: H0_occ | Htransit_occ | Hfinal_occ | null
harness_observed_current_canonical_hash: H0_occ | Htransit_occ | Hfinal_occ | null
physical_current_head_guard_state: exact seven-state value
head_state: unbound | synchronized | head_unconfirmed | stale | invalid | protocol_invalid
head_relation: none | current | successor_unpublished | one_generation_stale | two_generation_stale | untrusted
local_subject_disposition: present_at_local_site | remote_at_other_site | in_transition_out_of_domain | null
anchor_verified: true | false
subject_census_verified: true | false
current_head_representation_claim_enabled: true | false
refresh_enabled: true | false
inspection_enabled: true | false
local_nonconsequential_step_enabled: true | false
diagnostics_enabled: true | false
termination_enabled: true | false
local_publication_enabled: true | false
peer_interaction_enabled: false
canonical_evidence_enabled: false
canonical_scheduling_enabled: false
canonical_mutation_enabled: false
canonical_completion_enabled: false
canonical_truth_publication_enabled: false
reason_code: exact table-bound value
```

Every permission is closed by this exact context table. “Quarantined step” is
one exact compiled local counter increment that reads/writes only the three
Phase-3-approved detached scalar fields; it cannot call an adapter, probe,
router, Actor, canonical function, filesystem reader, or other process.

| Context / reason code | Claim | Refresh | Inspect | Quarantined step | Diagnostics | Terminate | Local publication | Peer interaction |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `unbound / binding_not_accepted` | no | no | no | no | yes | yes | no | no |
| `synchronized(R0) / exact_current_representation` | yes | no | yes | yes | yes | yes | no | no |
| `head_unconfirmed(R0) / successor_observation_unpublished` | no | no | yes | yes | yes | yes | no | no |
| `stale(R0/Rtransit) / immediate_successor_verified` | no | yes, Rtransit once | yes | yes | yes | yes | yes, Rtransit candidate only | no |
| `synchronized(Rtransit) / exact_current_representation` | yes | no | yes | yes | yes | yes | no | no |
| `head_unconfirmed(Rtransit) / successor_observation_unpublished` | no | no | yes | yes | yes | yes | no | no |
| `stale(Rtransit/Rfinal) / immediate_successor_verified` | no | yes, Rfinal once | yes | yes | yes | yes | yes, Rfinal candidate only | no |
| `synchronized(Rfinal) / exact_current_representation` | yes | no | yes | yes | yes | yes | no | no |
| `stale(R0/Rfinal) / multigeneration_control_terminal` | no | no | yes | no | yes | yes | no | no |
| `invalid / local_publication_unprovable` | no | no | no | no | yes | yes | no | no |
| `protocol_invalid / physical_protocol_violation` | no | no | no | no | yes | yes | no | no |

In all eleven rows, canonical evidence, scheduling, mutation, completion,
truth publication, and peer interaction are prohibited. `synchronized` exists
only in this harness disposition; no Unreal field or receipt may use it.

There is no state in which a domain remains synchronized to a predecessor after
a different committed head is independently observed. A stale R0 subject Actor
may remain visibly present in domain B only as quarantined historical local
state until a valid Rtransit refresh atomically removes it. It may never be
accepted as a current occupancy claim after Rtransit commits.

Direct R0-to-Rfinal physical catch-up is excluded from this candidate. The
positive proof requires both domains synchronized to Rtransit before the normal
completion cycle. A separate canonical-independence control may allow Rfinal to
commit while both domains remain stale at R0; each receives the exact terminal
`stale(R0/Rfinal) / multigeneration_control_terminal` disposition and may only
be inspected, diagnosed, or terminated. It may not skip the immediate-successor
refresh contract.

## Detached launch and refresh input closure

Every materialization operation consumes one exact, read-only, role-private
three-file bundle:

```text
exact canonical payload bytes
+ exact domain/head projection bytes
+ exact detached operation invocation bytes
```

No expected disposition, expected subject count, expected anchor fields,
expected live observation, current-head result, other-domain state, canonical
before/after summary, or pass/fail value may be visible to the Unreal process
or independent probe.

The exact invocation schema is:

```yaml
invocation_schema: CrossDomainOccupancyOperationInvocation.v1
proof_scenario: cross-domain-canonical-occupancy-materialization-v1
operation_id: launch_0001 | refresh_0001 | refresh_0002
operation: materialize_initial | refresh_once
domain_role: domain_A | domain_B
operational_process_instance_id: exact bound original process
source_canonical_hash: null | H0_occ | Htransit_occ
target_canonical_payload_raw_sha256: exact target raw digest
target_canonical_hash: H0_occ | Htransit_occ | Hfinal_occ
target_projection_raw_sha256: exact matching projection digest
target_projection_id: exact matching projection ID
publication_generation: publication_0001 | publication_0002 | publication_0003
```

Each operation-invocation file is canonical JSON under the same UTF-8,
recursively lexicographic, compact-member rule and ends in exactly one LF. Its
`operation_invocation_raw_sha256` is the lowercase SHA-256 of those stored
bytes. The harness constructs the file only after accepting the process binding,
writes it once into the role-private bundle, retains its device/inode/size/raw-
digest witness, and records that identity in the runtime trace. The adapter
hashes the one-read bytes before decoding, rejects a noncanonical round trip or
trailing bytes, and binds the raw digest into its materialization receipt. No
caller-supplied digest can substitute for the measured file digest.

There are exactly six legal tuples; unions outside these rows are invalid:

| Role | Operation | Source → target | Bundle root | Payload file | Projection file | Invocation file | Generation |
|---|---|---|---|---|---|---|---|
| A | `materialize_initial` | null → R0 | `launch_input/launch_0001/` | `canonical_occupancy_R0.json` | `cross_domain_A_R0_projection.json` | `cross_domain_A_launch_R0_invocation.json` | `publication_0001` |
| B | `materialize_initial` | null → R0 | `launch_input/launch_0001/` | `canonical_occupancy_R0.json` | `cross_domain_B_R0_projection.json` | `cross_domain_B_launch_R0_invocation.json` | `publication_0001` |
| A | `refresh_once` | R0 → Rtransit | `refresh_input/refresh_0001/` | `canonical_occupancy_Rtransit.json` | `cross_domain_A_Rtransit_projection.json` | `cross_domain_A_refresh_Rtransit_invocation.json` | `publication_0002` |
| B | `refresh_once` | R0 → Rtransit | `refresh_input/refresh_0001/` | `canonical_occupancy_Rtransit.json` | `cross_domain_B_Rtransit_projection.json` | `cross_domain_B_refresh_Rtransit_invocation.json` | `publication_0002` |
| A | `refresh_once` | Rtransit → Rfinal | `refresh_input/refresh_0002/` | `canonical_occupancy_Rfinal.json` | `cross_domain_A_Rfinal_projection.json` | `cross_domain_A_refresh_Rfinal_invocation.json` | `publication_0003` |
| B | `refresh_once` | Rtransit → Rfinal | `refresh_input/refresh_0002/` | `canonical_occupancy_Rfinal.json` | `cross_domain_B_Rfinal_projection.json` | `cross_domain_B_refresh_Rfinal_invocation.json` | `publication_0003` |

The invocation authenticates a requested operation but is never the authority
for payload or projection acceptance. The adapter independently hashes the two
data files and requires their exact frozen byte identities before comparing the
invocation. Direct R0 → Rfinal, repeated generation, cross-role, cross-head,
wrong-operation, or unknown tuples reject before private construction.

The non-truth-bearing launch selector is exactly
`-CrossDomainOccupancyProof`. The bounded Phase-4 branch in
`CityProofGameMode.cpp` uses it only to create the
`CrossDomainOccupancyCommandRouter`, suppress every Pawn/possession path, and
retain only the one inert engine-base controller required by the established
`-game` bootstrap.
It contains no role, head, occupancy, witness, expected result, or fault value.
Without that one selector, the Phase-4 router is unreachable; no existing
Phase-3 selector or router may accept Phase-4 commands.

The complete launch surface is value-bound, not merely digest-recorded:

```yaml
launch_surface_schema: CrossDomainOccupancyLaunchSurface.v1
argv_in_order:
  - exact UnrealEditor executable realpath
  - exact CityMaterializationProof.uproject realpath
  - -game
  - -Multiprocess
  - -CrossDomainOccupancyProof
  - -NoSplash
  - -Windowed
  - -ResX=900
  - -ResY=650
  - -WinX=30 for A | -WinX=990 for B
  - -WinY=60
  - -UserDir=exact role-private process_root/user
  - -abslog=exact role-private process_root/diagnostic/UnrealEditor.log
argv_semantic_selector_allowlist:
  - -CrossDomainOccupancyProof: router_activation_and_inert_bootstrap_only
argv_forbidden_values:
  - witness role head occupancy generation expected result fault other-domain path
environment:
  construction: complete inherited environment with TMPDIR replaced by exact role-private process_root/tmp
  audit_form: sorted complete key list plus per-value raw SHA-256 and whole-map raw SHA-256
  plaintext_values_released: false
  semantic_key_allowlist: []
  adapter_router_probe_reads_after_binding: prohibited
  forbidden_values: other-domain root head observation guard expected result fault selector
cwd:
  value: exact repository root realpath
  semantic_branching: prohibited
inherited_descriptors_at_exec:
  fd_0: original control pipe read endpoint
  fd_1: original structured-output pipe write endpoint
  fd_2: role-private diagnostic pipe write endpoint
  all_other_application_descriptors: closed
  fd_2_proof_semantic_input: false
runtime_input_classification:
  executable_project_config_module: provenance_and_compiled_code_identity_only
  engine_system_loaded_images_and_dynamic_descriptors: inventoried_platform_context_only
  argv_selector: router_activation_and_inert_bootstrap_only
  environment_cwd_and_fd_2: provenance_only
  fd_0_binding_commands_and_role_private_bundle_bytes: declared_phase4_inputs_only
  live_world_actor_slots: independent_observation_only
initial_world_contract:
  pawn_count: 0
  controller_count: 1
  controller_class: /Script/Engine.PlayerController
  controller_pawn: null
  phase_4_handler_edges_from_controller_or_input: 0
  non_disabled_auto_receive_input_actor_count: 0
```

The harness records the exact resolved argv values, redacted complete
environment audit, cwd, descriptor kernel map, loaded-image inventory, and
initial Actor inventory before the first materialization. The binding hashes
those exact records. Any missing, added, reordered, redirected, or
role-inconsistent argv member; environment construction other than the one
declared replacement; additional application descriptor; unexpected initial
Pawn/controller; or platform-context value reaching a Phase-4 decision rejects
the occurrence. The selector activates code only; it cannot choose any
representation field or result.

After the binding command, normal primary-witness traffic uses these neutral
command tokens. `I0` through `I8` are nine fresh censuses, one at each L0–L8
checkpoint; the token carries no expected head, count, or disposition.

```yaml
normal_command_tokens:
  M0: materialize_initial/launch_0001
  I0: inspect_published_occupancy_once/inspection_0001
  I1: inspect_published_occupancy_once/inspection_0002
  I2: inspect_published_occupancy_once/inspection_0003
  RT: refresh_once/refresh_0001
  I3: inspect_published_occupancy_once/inspection_0004
  I4: inspect_published_occupancy_once/inspection_0005
  I5: inspect_published_occupancy_once/inspection_0006
  I6: inspect_published_occupancy_once/inspection_0007
  RF: refresh_once/refresh_0002
  I7: inspect_published_occupancy_once/inspection_0008
  I8: inspect_published_occupancy_once/inspection_0009
```

The four exact per-process profiles, after bind sequence 0, are:

| Profile | Exact command tokens at sequences 1 through 12 |
|---|---|
| `first_then_first` | M0, I0, I1, I2, RT, I3, I4, I5, I6, RF, I7, I8 |
| `second_then_second` | M0, I0, I1, I2, I3, RT, I4, I5, I6, I7, RF, I8 |
| `first_then_second` | M0, I0, I1, I2, RT, I3, I4, I5, I6, I7, RF, I8 |
| `second_then_first` | M0, I0, I1, I2, I3, RT, I4, I5, I6, RF, I7, I8 |

| Witness | Domain A profile | Domain B profile |
|---|---|---|
| W1 | `first_then_first` | `second_then_second` |
| W2 | `second_then_second` | `first_then_first` |
| W3 | `first_then_second` | `second_then_first` |
| W4 | `second_then_first` | `first_then_second` |

At I1/L1 and I5/L5, both processes census the predecessor generation after
the canonical successor commits but before private head publication. At I2/L2
and I6/L6 they repeat that census after private head publication and stale
classification. At I3/L3 and I7/L7, the first-refreshed process is inspected
after its refresh while the second process is inspected before its refresh;
the harness pairs those two fresh observations within one polling cycle. I4/L4
and I8/L8 occur in both processes only after both corresponding refreshes.

The two normal stdin schemas are closed and canonicalized by the same JSON
rule:

```yaml
materialize_invocation_schema: CrossDomainOccupancyMaterializeInvocation.v1
proof_scenario: cross-domain-canonical-occupancy-materialization-v1
command_sequence: exact profile/control/fault/asymmetric-failure-bound integer 1 through 12
operation_id: launch_0001 | refresh_0001 | refresh_0002
operation: materialize_initial | refresh_once
relative_bundle_root: exact table row, without dot, slash prefix, or traversal
```

```yaml
inspection_invocation_schema: CrossDomainOccupancyInspectionInvocation.v1
proof_scenario: cross-domain-canonical-occupancy-materialization-v1
command_sequence: exact profile/control/fault/asymmetric-failure-bound positive integer
operation: inspect_published_occupancy_once
inspection_id: inspection_0001 | inspection_0002 | inspection_0003 | inspection_0004 | inspection_0005 | inspection_0006 | inspection_0007 | inspection_0008 | inspection_0009 | inspection_c1_terminal_0001 | inspection_c2_rejection_0001 | inspection_c3_rejection_0001
```

The profiles close every positive cross-product: M0 is always sequence 1, RT
is sequence 5 or 6 according to first/second refresh role, RF is sequence 10 or
11, I0/I1/I2/I4/I5/I6/I8 are sequences 2/3/4/7/8/9/12, and I3/I7 are sequence
5 or 6 / 10 or 11 according to whether that process is still stale or already
refreshed. The W table chooses the only legal profile per process. The exact
control, fault, asymmetric-failure, and liveness-adversary sequences below are
separate closed rows. All other
cross-products reject. The process records the measured raw SHA-256 of every
accepted stdin line in its trace before dispatch.

Each materialize command names only its operation ID and exact relative bundle
root. Each inspection command names only its sequence ID. No command contains a
head, disposition, count, Actor identity, expected value, receipt digest,
canonical result, or pass/fail state. Commands are accepted once, in order, on
the original pipe. Missing, duplicate, reordered, alternate-schema, trailing-
member, console, flag, environment, signal, socket, timer, watcher, polling,
Actor-input, player-input, or shared-file invocation rejects.

Fresh processes designated by `fault_materialization`,
`fault_live_observation`, `c2_positive_Rtransit_absence`, or
`c3_receipt_only_rejection` may receive one additional exact process-side arm
immediately before the named operation or inspection. It can name only an M01–
M23 adapter/router stage or O01–O10 process-side probe/router stage. It cannot
name HF or harness O11/O12. It contains no expected result and is acknowledged
by one process-bound receipt before the compiled stage executes.

```yaml
fault_arm_invocation_schema: CrossDomainOccupancyProcessFaultArmInvocation.v1
proof_scenario: cross-domain-canonical-occupancy-materialization-v1
fault_occurrence_id: exact fresh registered occurrence
case_id: exact matrix case ID
stage_id: exact M01-M23 | O01-O10 process-side stage for that case
edge: before | after
armed_operation_id: exact next operation or inspection ID
operational_process_instance_id: exact original bound process
```

```yaml
process_fault_arm_receipt_schema: CrossDomainOccupancyProcessFaultArmReceipt.v1
proof_scenario: cross-domain-canonical-occupancy-materialization-v1
fault_occurrence_id: exact matching occurrence
case_id: exact matching case
stage_id: exact matching process-side stage
edge: exact matching edge
armed_operation_id: exact matching next operation or inspection ID
operational_process_instance_id: exact original bound process
arm_state: armed_once
```

HF01–HF18 and the O11/O12 portions of OF execute only through a separate
harness-private channel. Before the named harness stage, the harness creates
and authenticates one closed plan and receipt beneath its private control root;
neither object, path, digest, stage, or result enters Unreal.

```yaml
harness_fault_plan_schema: CrossDomainOccupancyHarnessFaultPlan.v1
proof_scenario: cross-domain-canonical-occupancy-materialization-v1
harness_fault_occurrence_id: exact fresh harness occurrence
case_id: exact HF | OF harness-side case
stage_id: exact head-publication stage | O11 | O12
edge: exact case-table edge
armed_harness_operation_id: head_observation_0001 | head_observation_0002 | exact inspection occurrence
harness_run_id: exact current harness run
```

```yaml
harness_fault_arm_receipt_schema: CrossDomainOccupancyHarnessFaultArmReceipt.v1
proof_scenario: cross-domain-canonical-occupancy-materialization-v1
harness_fault_occurrence_id: exact matching harness occurrence
harness_fault_plan_raw_sha256: exact authenticated plan digest
case_id: exact matching case
stage_id: exact matching harness stage
edge: exact matching edge
armed_harness_operation_id: exact matching operation
arm_state: armed_once
```

Both fault channels are one-shot and case-table-bound. The distinct liveness
channel admits only the exact LV03–LV05 invocation/receipt rows declared in the
lifetime section; LV01, LV02, and LV06 have no stdin command. A second or
unused arm, cross-channel stage, unexpected operation, altered plan, or
environment, argv, file, console, signal, timer, debugger, or witness-ID
selector rejects.

Every bundle directory is beneath its role-private process root, contains
exactly the three regular files and no link, has a distinct device/inode for
each member, `st_nlink == 1`, and is opened once through a retained directory
descriptor with `openat(O_RDONLY|O_CLOEXEC|O_NOFOLLOW)`. Pre/post `fstat`
identity, size, and one-read EOF are exact. Parent traversal, absolute member
paths, aliases, symlinks, hardlinks, sibling enumeration, root containment,
other-domain descriptors, and shared writable ancestors reject.

The proof-semantic input audit freezes the complete process-visible surface:
ordered argv, redacted complete environment, cwd, inherited descriptors,
executable, project, config/module inventory, loaded images/runtime
dependencies, map, binding command, ordered normal/fault/liveness-adversary
commands, and exact bundle opens. Foundational UE/platform inputs are
inventoried and hash-bound;
only the one activation selector, binding, exact commands, canonical bytes,
projection bytes, and enumerated live Actor slots may reach their declared
Phase-4 roles. All other fields may identify evidence only. The audit
must prove no alternate reader, hidden selector, other-domain path, repository
ProofRecords path, parent enumeration, or ambient state reaches the proof.

## Atomic local publication law

Physical materialization is not a canonical transaction. It must nevertheless
have one exact atomic acceptance boundary. UE destruction and spawning are
separate world mutations; the proof does not falsely claim those mutations are
simultaneous.

For each launch or refresh, the adapter must perform this order:

```text
open once and hash the complete exact three-file bundle
→ validate exact canonical payload bytes and canonical hash
→ validate exact projection bytes and legal matrix row
→ validate exact operation invocation and immutable process binding
→ derive occupancy disposition from canonical payload + local site only
→ privately construct closed anchor/subject value objects with no world visibility
→ validate candidate coherence and exact target cardinality
→ begin publication on the game thread; current-head claim remains disabled
→ quarantine and destroy every predecessor generation object; verify absence
→ spawn/configure/finish the target subject Actor when required
→ spawn/configure/finish the target head anchor last as generation commit marker
→ enumerate and validate the adapter-visible target generation
→ emit detached materialization receipt
→ obtain independent live-world observation
→ derive independent expectation from separately authenticated input bytes
→ harness compares expectation independently with receipt and live census
→ harness verifies private head, original binding, and matching open guard
→ emit one synchronized disposition as the atomic acceptance point
```

Before `begin_publication`, the prior representation remains exact quarantined
historical local state. A normal rejection there leaves the domain stale at the
prior head and emits no target receipt. The sole exception is the exact
`control_C3` adversary: after M16 it deliberately emits one non-authoritative,
structurally valid-looking receipt from the authenticated private candidate
values without entering M17 or mutating the world. That receipt must be
rejected and creates no success path. `begin_publication` occurs immediately
before the first predecessor destruction or target spawn. From that point
until the harness disposition, current-head claim permission remains false. Any fault,
uncertain destruction, duplicate, partial spawn, mismatched generation,
observation disagreement, or missing output after that point produces terminal
`invalid`; rollback or retry in that process is prohibited. The harness
acceptance disposition—not object visibility or receipt emission—is the sole
linearization point for a representation-correspondence claim.

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

Every locally completed launch or refresh emits one detached receipt with this
exact closed ordered schema:

```yaml
receipt_schema: CrossDomainOccupancyMaterializationReceipt.v1
proof_scenario: cross-domain-canonical-occupancy-materialization-v1
operation_id: launch_0001 | refresh_0001 | refresh_0002
operation: materialize_initial | refresh_once
materialize_command_raw_sha256: exact measured stdin-line digest
operation_invocation_raw_sha256: exact measured invocation-file digest
domain_role: domain_A | domain_B
operational_process_instance_id: exact immutable binding
process_binding_raw_sha256: exact binding digest
accepted_canonical_payload_raw_sha256: exact record digest
accepted_canonical_hash: exact canonical head
accepted_projection_raw_sha256: exact projection digest
accepted_projection_id: exact legal row
projected_canonical_site_id: exact role site
projected_site_representation_slot: exact role site slot
projected_subject_representation_slot: exact role subject slot
canonical_occupant_id: topology_occupant_0001
canonical_occupancy_kind: at_site | in_transition
canonical_occupancy_reference: exact site or transition ID
derived_local_subject_disposition: exact table value
publication_generation: publication_0001 | publication_0002 | publication_0003
published_anchor_actor_count: exact nonnegative integer
published_anchor_actor_rows: exhaustive sorted adapter-visible rows
published_subject_actor_count: exact nonnegative integer
published_subject_actor_rows: exhaustive sorted adapter-visible rows
representation_publication_state: locally_published_unverified
receipt_authority: representation_only
```

Counts must equal list lengths. A positive receipt requires exactly one anchor
and the expected zero or one subject row, but the receipt is necessary and
insufficient. It reports what the adapter believes it published and never says
`synchronized`, `current_head`, `stale`, `guard`, or `pass`. Only the later
harness disposition may accept a current-head claim after separate expectation
and census comparisons. None of these documents is canonical truth.

## Required primary witnesses

The exact finite refresh-order matrix covers both orders at both canonical transitions so no process role or
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

Control stdin schedules are closed separately from W1–W4. `FA(case)` is the
one process-side arm immediately before its target command; canonical calls and
harness-private head operations never travel on stdin.

| Control / role | Exact stdin tokens after bind |
|---|---|
| C1 / A and B | M0, I0, I1, I2, inspection_c1_terminal_0001 |
| C2 / A | M0, I0 |
| C2 / B | M0, I0, FA(control_C2), RT, inspection_c2_rejection_0001 |
| C3 / A | M0, I0 |
| C3 / B | M0, I0, FA(control_C3), RT, inspection_c3_rejection_0001 |
| C4a / A and B | M0, I0 |
| C4b / A | M0, I0, I1, I2, RT, I3, I4 |
| C4b / B | M0, I0, I1, I2, I3, RT, I4 |
| C5 / A | M0, I0, I1, I2, RT, I3, I4 |
| C5 / original B | M0, I0, I1, I2, I3, RT, I4, then terminate |

The three special inspection IDs are legal only in the named control and at
the final displayed position. Their command sequence is their 1-based position
after bind. The C1 terminal inspection occurs only after exact Rfinal head
observation and the multigeneration stale disposition. C2/C3 rejection
inspections occur only after their target command fails.

| Case | Role | Armed operation | Compiled stage | Edge | Exact injected action |
|---|---|---|---|---|---|
| `control_C2` | B | `refresh_0001` | `M20_spawn_configure_and_finish_target_anchor` | before | abort before target anchor spawn after predecessor destruction and zero-subject M19 |
| `control_C3` | B | `refresh_0001` | `M16_validate_candidate_coherence_and_cardinality` | after | adapter emits one structurally valid-looking target receipt from authenticated private candidate values without entering M17 or mutating the R0 world |

### C1 — canonical completion ignores physical synchronization

From fresh R0-synchronized processes, commit and independently observe exact
Rtransit, classify both domains `stale(R0/Rtransit)`, and send no Rtransit
refresh. Immediately before exact completion, perform the sole legal C1 close
to terminal guard state `closed_for_c1_Rtransit_to_Rfinal`; then invoke the
exact sealed completion discovery and resolver against Rtransit. Exact Rfinal
must still commit byte-for-byte. The C1 guard never opens for Rfinal. Both
physical domains receive exact
`stale(R0/Rfinal) / multigeneration_control_terminal` dispositions, remain
alive for one final census, and are then terminated by the harness. Direct
R0-to-Rfinal refresh is never sent or accepted.

This control proves canonical independence. It is not a successful final
materialization witness and does not weaken the primary immediate-successor
refresh law.

### C2 — lawful Rtransit absence is positive

In a fresh `c2_positive_Rtransit_absence` process pair, arm exact
`control_C2` on domain B's Rtransit publication using the row above. The
adapter removes the R0 subject through M18, completes the exact zero-subject set
through M19, and fails before M20 can spawn the target anchor. The independent
read-only probe performs its
normal exhaustive census and reports zero anchor plus zero subject Actors. The
harness must emit `invalid / local_publication_unprovable`, never synchronized.
A zero-subject world cannot pass merely because zero is expected. The probe
does not mutate the world.

### C3 — receipt-only publication is insufficient

In a fresh `c3_receipt_only_rejection` pair, arm exact `control_C3` for domain
B's Rtransit operation using the row above. After M02–M16 authenticate the
three-file bundle, derive the target disposition, and validate the private
candidate, the exact after-M16 adapter fault emits a structurally valid-looking
target receipt whose claimed published rows are filled from those authenticated
private candidate values. It does not enter M17, destroy or spawn an Actor, or
read an expected representation; the live world retains the complete R0
generation. Its process trace ends at the injected after-M16 edge. The
independent probe records the R0 anchor and subject. The separately derived
expectation is Rtransit. The harness rejects the expectation/receipt agreement
because neither receipt/live nor expectation/live agrees, and emits
`invalid / local_publication_unprovable`. No general receipt fabrication path
exists outside this one-shot fault-arm case.

### C4a — start guard-open canonical control

From a fresh exact R0-synchronized pair, deliberately omit the legal close and
invoke exact Phase-2 start while the guard remains `open_for_R0`. Exact
Rtransit must still commit byte-for-byte. The physical protocol then becomes
`failed_closed`; both domains receive
`protocol_invalid / physical_protocol_violation` and halt.

### C4b — completion guard-open canonical control

From a separate fresh pair, complete the normal R0 → Rtransit materialization
and deliberately omit the second legal close. Invoke exact Phase-2 completion
while the guard remains `open_for_Rtransit`. Exact Rfinal must still commit
byte-for-byte. The guard becomes `failed_closed`; both domains receive the
same terminal protocol-invalid disposition. C4a and C4b each bind complete
canonical before/after snapshots and prove the guard cannot gate either
canonical resolution.

### C5 — process replacement is not continuity

Terminate original domain B after L4 and launch a fresh direct child with copied
payload, projection, receipt, root contents, and declared labels. Independently
observe its honest new PID/start pair, root, descriptors, executable, and
process population. Even when all caller-controlled labels are rewritten
consistently, its newly computed operational ID differs and it must be rejected
as a replacement before binding to the original witness. It cannot satisfy any
L0–L8 checkpoint or emit an accepted materialization.

Each control has one exact case ID, fresh roots/processes, complete command and
fault-arm provenance, exact expected output/reason code, and full canonical
record/ledger/ancestry/reservation/unresolved-work snapshots before and after.
A boolean unchanged summary is never sufficient.

## Asymmetric failure obligations

AF01–AF04 use four separate closed stdin schedules. `TOKEN@n` means the exact
normal token schema already declared above with process-local
`command_sequence: n`; `valid` selects the exact frozen three-file row, while
`AFxx-malformed` uses that same legal relative bundle root and exact legal
operation-invocation bytes but places the case's fresh malformed projection
bytes in the not-yet-consumed projection member before process launch. I4 is
`inspection_0005`; I8 is `inspection_0009`. A pre-publication M09 rejection
consumes that one refresh attempt but leaves the predecessor stale, the
original pipe usable for the one displayed census, and no retry enabled.

| Case | Exact domain-A stdin after bind | Exact domain-B stdin after bind | Exact harness/canonical ordering |
|---|---|---|---|
| AF01 | M0@1, I0@2, RT-valid@3, I4@4 | M0@1, I0@2, RT-AF01-malformed@3, I4@4 | accept both I0 at R0; exact start/head/stale/open; accept A RT then A I4 at Rtransit; reject B RT at M09; accept B I4 at stale R0; terminate pair |
| AF02 | M0@1, I0@2, RT-AF02-malformed@3, I4@4 | M0@1, I0@2, RT-valid@3, I4@4 | accept both I0 at R0; exact start/head/stale/open; accept B RT then B I4 at Rtransit; reject A RT at M09; accept A I4 at stale R0; terminate pair |
| AF03 | M0@1, I0@2, RT-valid@3, I4@4, RF-valid@5, I8@6 | M0@1, I0@2, RT-valid@3, I4@4, RF-AF03-malformed@5, I8@6 | accept both I0 at R0; exact start/head/stale/open; accept A RT/I4 then B RT/I4; exact completion/head/stale/open; accept A RF then A I8 at Rfinal; reject B RF at M09; accept B I8 at stale Rtransit; terminate pair |
| AF04 | M0@1, I0@2, RT-valid@3, I4@4, RF-AF04-malformed@5, I8@6 | M0@1, I0@2, RT-valid@3, I4@4, RF-valid@5, I8@6 | accept both I0 at R0; exact start/head/stale/open; accept A RT/I4 then B RT/I4; exact completion/head/stale/open; accept B RF then B I8 at Rfinal; reject A RF at M09; accept A I8 at stale Rtransit; terminate pair |

No AF schedule is a W1–W4 profile, control schedule, or configurable fault row.
Every different token, sequence, role, order, bundle-root, projection member,
inspection ID, retry, or cross-product rejects.

Each failed refresh consumes an exact same-length malformed projection. Its
bytes equal the frozen target projection bytes except for the sole
`projection_id` substitution shown below; every other byte and the one terminal
LF remain exact. The operation invocation remains the exact legal role/head row
and therefore still names the original frozen projection digest. The adapter
completes M01–M08, enters
`M09_authenticate_and_validate_projection`, measures the displayed unrecognized
raw digest, and rejects there with
`projection_raw_sha256_not_frozen`. M09 does not complete; M10–M23 do not run;
no target receipt or target-generation object exists.

The exact asymmetric failure matrix is:

| Case | Exact setup and successful refresh | Failed role / operation | Sole projection-ID substitution | Malformed projection raw SHA-256 | Exact failed trace / physical outcome |
|---|---|---|---|---|---|
| AF01 | fresh R0 pair; exact Rtransit commit/head; A exact `refresh_0001` succeeds | B / `refresh_0001` | `cross_domain_B_Rtransit_0001` → `cross_domain_Z_Rtransit_0001` | `beb2d2e1c574220ac31901162e58993f46108769f89394ef2df4812c9c84fc3d` | B refresh trace has M01–M08 completed, M09 entered/rejected and no M09 completion; B I4 then confirms stale R0; A synchronized Rtransit; exact Rtransit unchanged |
| AF02 | fresh R0 pair; exact Rtransit commit/head; B exact `refresh_0001` succeeds | A / `refresh_0001` | `cross_domain_A_Rtransit_0001` → `cross_domain_Z_Rtransit_0001` | `13d76645353c813c480c323e380697e5f5ea24be10ab0eb80e4a3d789c060c6f` | A refresh trace has M01–M08 completed, M09 entered/rejected and no M09 completion; A I4 then confirms stale R0; B synchronized Rtransit; exact Rtransit unchanged |
| AF03 | fresh pair synchronized Rtransit by exact A-then-B setup; exact Rfinal commit/head; A exact `refresh_0002` succeeds | B / `refresh_0002` | `cross_domain_B_Rfinal_0001` → `cross_domain_Z_Rfinal_0001` | `88c518da37a6311fe43a5a2cc83d56c1dd412939da716019503ee1cbb4a45b87` | B refresh trace has M01–M08 completed, M09 entered/rejected and no M09 completion; B I8 then confirms stale Rtransit; A synchronized Rfinal; exact Rfinal unchanged |
| AF04 | fresh pair synchronized Rtransit by exact A-then-B setup; exact Rfinal commit/head; B exact `refresh_0002` succeeds | A / `refresh_0002` | `cross_domain_A_Rfinal_0001` → `cross_domain_Z_Rfinal_0001` | `0c16b9a80158e78ebdd688a87335248d91b9d0843ef08a35e6ef2897825de26b` | A refresh trace has M01–M08 completed, M09 entered/rejected and no M09 completion; A I8 then confirms stale Rtransit; B synchronized Rfinal; exact Rfinal unchanged |

Each case uses a fresh process pair and a fresh malformed three-file bundle
created before the failed command; no accepted input file is mutated in place.
The artifact records the complete malformed bytes and measured digest, original
process bindings, exact command sequence, prior anchor/Actor rows, target-head
receipt absence, both live peer censuses, dispositions, and complete canonical
record/ledger/ancestry/reservation/unresolved-work snapshots before and after.
A symmetric label swap or a configurable failure stage is not sufficient
evidence.

An asymmetric failure may not cause the successful peer to roll back, cause the
failed domain to publish a partial target state, or change canonical history.
Neither domain may observe the other's failure as an input.

## Current-head and occupancy authority adversaries

The exact ordered authority table is closed. Variant braces are finite sets
executed as separately identified subcases inside the named row; every subcase
must appear in the row artifact.

| Case | Exact action ID | Expected rejecting stage / reason | Resulting physical disposition |
|---|---|---|---|
| A01 | `mutate_sealed_payload_recompute_digest/{R0,Rtransit,Rfinal}` | payload allowlist / `sealed_payload_identity_mismatch` | unbound on launch; predecessor stale on refresh |
| A02 | `swap_raw_and_canonical_digest_fields` | payload authentication / `digest_domain_mismatch` | unbound or predecessor stale |
| A03 | `canonical_member_shape/{unknown,missing,duplicate,reordered,type}` | structural validation / `canonical_shape_mismatch` | unbound or predecessor stale |
| A04 | `alter_occupancy_identity/{occupant,kind,site,transition}` | exact canonical validation / `occupancy_identity_mismatch` | unbound or predecessor stale |
| A05 | `redirect_projection_role_to_peer_site/{A,B}` | six-row projection validation / `projection_row_mismatch` | unbound or predecessor stale |
| A06 | `inject_projection_expectation/{kind,presence,count}` | closed projection schema / `projection_extra_member` | unbound or predecessor stale |
| A07 | `colluding_cross_head_tuple_recompute_all_enclosing_digests` | six-operation tuple validation / `operation_tuple_mismatch` | predecessor stale |
| A08 | `colluding_cross_domain_tuple_recompute_all_enclosing_digests` | process/role tuple validation / `domain_binding_mismatch` | unbound or predecessor stale |
| A09 | `publish_subject_A_R0` | independent expectation comparison / `unexpected_local_subject` | invalid |
| A10 | `omit_subject_B_R0` | independent expectation comparison / `missing_local_subject` | invalid |
| A11 | `publish_subject_Rtransit/{A,B}` | independent expectation comparison / `subject_forbidden_in_transition` | invalid |
| A12 | `omit_Rtransit_anchor_with_zero_subjects/{A,B}` | exhaustive census / `positive_anchor_missing` | invalid |
| A13 | `omit_subject_A_Rfinal` | independent expectation comparison / `missing_local_subject` | invalid |
| A14 | `publish_subject_B_Rfinal` | independent expectation comparison / `unexpected_local_subject` | invalid |
| A15 | `duplicate_live_object/{anchor,subject}` | exhaustive census / `duplicate_generation_object` | invalid |
| A16 | `alter_live_actor_field/{occupant,site,head,projection,process,generation}` | expectation/live comparison / `live_field_mismatch` | invalid |
| A17 | `retain_predecessor_anchor_beside_target` | exhaustive census / `multiple_generation_anchor` | invalid |
| A18 | `retain_predecessor_subject_after_target_publication` | exhaustive census / `predecessor_subject_retained` | invalid |
| A19 | `publish_destination_subject_before_Rfinal` | private head comparison / `premature_destination_representation` | invalid |
| A20 | `offer_physical_completion_source/{route,transform,timer,animation,collision,overlap,navigation}` | source/dataflow audit / `physical_completion_authority` | source audit rejected |
| A21 | `submit_R0_schedule_copy_as_completion` | Phase-2 record-bound discovery / `stale_boundary_authority` | physical input rejected; canonical unchanged |
| A22 | `submit_actor_disappearance_as_Rtransit_commit` | canonical API boundary / `physical_commit_authority` | physical input rejected; canonical unchanged |
| A23 | `submit_destination_actor_as_completion` | canonical API boundary / `physical_completion_authority` | physical input rejected; canonical unchanged |
| A24 | `accept_receipt_without_live_observation` | harness acceptance / `live_observation_required` | no synchronized disposition |
| A25 | `reconstruct_observation_from/{receipt,adapter_json,expected_json,wrong_world,filtered_census}` | probe input/source audit / `oracle_not_independent` | observation rejected; source audit rejected |
| A26 | `expose_probe_expectation/{disposition,count,head,pass}` | command/input audit / `expected_value_visible_to_probe` | observation rejected |
| A27 | `relabel_stale_as_synchronized/{R0,Rtransit}` | harness disposition validation / `head_relation_mismatch` | stale remains stale |
| A28 | `claim_stale_subject_as_current_occupancy` | permission matrix / `stale_current_claim_prohibited` | stale remains stale |
| A29 | `direct_refresh_R0_to_Rfinal` | six-operation tuple validation / `multigeneration_refresh_prohibited` | terminal stale R0/Rfinal |
| A30 | `refresh_immediate_successor_while_guard_closed/{Rtransit,Rfinal}` | guard permission / `refresh_guard_closed` | predecessor stale |
| A31 | `route_guard_or_head_observation_into_phase2/{discover,resolve,hash,publish}` | function-scoped source audit / `canonical_authority_edge` | source audit rejected; exact canonical successor still required in live control |
| A32 | `select_canonical_result_from_refresh_order/{W1,W2,W3,W4}` | canonical equivalence oracle / `physical_order_authority` | proof rejected |
| A33 | `use_peer_input/{state,liveness,receipt,observation,root,descriptor}` | process-input/source audit / `cross_domain_input` | source audit rejected |
| A34 | `hide_lifecycle_break/{exit,wait_status,start_mismatch,control_EOF,output_EOF,replacement,root_mismatch}` | independent liveness monitor / `original_process_not_continuous` | protocol-invalid or replacement rejected |
| A35 | `emit_success_receipt_after_partial_publication` | generation/census comparison / `partial_publication` | invalid |
| A36 | `merge_predecessor_local_value/{cache,actor_id,transform,physics,diagnostic}` | constructor/source audit / `noncanonical_merge_input` | source audit rejected or invalid |
| A37 | `reach_phase4_from/{Pawn,possession,player_input,Actor_input,auto_receive_input,controller}` | exhaustive census/source audit / `input_authority_path` | proof and source audit rejected |
| A38 | `alternate_refresh_channel/{socket,watcher,poll,signal,environment,flag,console,timer,shared_file}` | complete input census / `alternate_channel` | proof and source audit rejected |
| A39 | `physical_construct_or_control_canonical_successor/{construct,select,delay,reject,publish}` | canonical API/source audit / `physical_canonical_authority` | proof and source audit rejected |
| A40 | `claim_out_of_scope_authority/{evidence,scheduling,mutation,truth,player,network,movement,streaming,production}` | disposition/release validator / `authority_claim_prohibited` | candidate rejected |

Every applicable row must mechanically measure the exact canonical record,
ledger, ancestry, reservation, and unresolved-work state before and after the
adversary. Each row records exact input bytes, process binding, command/fault
arm, real stage reached, reason code, receipt/observation presence, final live
census, disposition, and canonical snapshots. A hard-coded
`canonical_unchanged: true` summary is not evidence.

## Failure atomicity

Fault injection is one-shot and reachable only through its exact channel.
M01–M23 and O01–O10 use the process-side stdin arm/receipt and bind case,
process, stage, edge, operation, role, and current generation. HF and O11–O12
use the harness-private plan/receipt and bind case, harness run, stage, edge,
and harness operation without exposing a value to Unreal. An unarmed branch,
wrong process or harness run, wrong channel, wrong stage, repeated arm, unused
arm, or extra injection API rejects.

Liveness adversaries are not a configurable fault-injection branch. They are
the separate exact LV01–LV06 table: LV03–LV05 alone use their process-side
liveness invocation and arm receipt, while LV01, LV02, and LV06 execute their
named harness process-control action with no Unreal command. A liveness plan,
invocation, receipt, role, checkpoint, edge, sequence, action, first failing
observation, or terminal disposition outside its one exact row rejects.

The 23 ordered materialization stages are:

```yaml
materialization_stages:
  - M01_receive_and_parse_command
  - M02_resolve_role_private_bundle_root
  - M03_inventory_exact_three_file_directory
  - M04_open_and_pre_stat_payload
  - M05_read_and_post_stat_payload
  - M06_authenticate_and_validate_payload
  - M07_open_and_pre_stat_projection
  - M08_read_and_post_stat_projection
  - M09_authenticate_and_validate_projection
  - M10_open_and_pre_stat_invocation
  - M11_read_and_post_stat_invocation
  - M12_validate_operation_tuple_and_process_binding
  - M13_derive_local_subject_disposition
  - M14_construct_private_anchor_values
  - M15_construct_private_subject_values
  - M16_validate_candidate_coherence_and_cardinality
  - M17_begin_publication_linearization_interval
  - M18_destroy_and_verify_predecessor_generation_absent
  - M19_spawn_configure_and_finish_target_subject_set
  - M20_spawn_configure_and_finish_target_anchor
  - M21_enumerate_and_validate_adapter_visible_generation
  - M22_emit_materialization_receipt
  - M23_router_forward_receipt
```

Cases `MF001`–`MF138` are the exact Cartesian product, ordered first by
context, then stage, then edge, of:

```yaml
materialization_contexts:
  - launch_R0_domain_B_unbound_to_present
  - refresh_Rtransit_domain_B_present_to_absent
  - refresh_Rfinal_domain_A_absent_to_present
fault_edges:
  - before
  - after
```

For an initial launch, any fault before M17 leaves the process `unbound`; for a
refresh it leaves the predecessor exact and stale. From M17 onward, any fault
or missing expected trace suffix produces `invalid`, no synchronized
disposition, exact final live census, and no retry. Each row executes in a
fresh real UE process pair and binds the exact successful trace prefix through
the armed edge.

The 12 ordered live observation/acceptance stages are:

```yaml
live_observation_stages:
  - O01_receive_and_parse_inspection_command
  - O02_verify_original_process_binding
  - O03_select_exact_process_bound_game_world
  - O04_enumerate_all_loaded_level_actor_slots
  - O05_classify_all_phase4_relevant_actor_rows
  - O06_inventory_all_pawn_controller_and_input_rows
  - O07_sort_and_cross_check_counts_with_lists
  - O08_construct_closed_live_observation
  - O09_emit_live_observation
  - O10_router_forward_live_observation
  - O11_harness_derive_independent_expected_representation
  - O12_harness_compare_expectation_receipt_observation_head_binding_guard
```

Cases `OF001`–`OF036` are exact. Every row injects after its named stage and
before the next normal action or harness disposition:

| Case | Context / inspection | Stage | Channel | Edge |
|---|---|---|---|---|
| OF001 | R0 / domain B / present / `inspection_0001` | O01 | process | after |
| OF002 | R0 / domain B / present / `inspection_0001` | O02 | process | after |
| OF003 | R0 / domain B / present / `inspection_0001` | O03 | process | after |
| OF004 | R0 / domain B / present / `inspection_0001` | O04 | process | after |
| OF005 | R0 / domain B / present / `inspection_0001` | O05 | process | after |
| OF006 | R0 / domain B / present / `inspection_0001` | O06 | process | after |
| OF007 | R0 / domain B / present / `inspection_0001` | O07 | process | after |
| OF008 | R0 / domain B / present / `inspection_0001` | O08 | process | after |
| OF009 | R0 / domain B / present / `inspection_0001` | O09 | process | after |
| OF010 | R0 / domain B / present / `inspection_0001` | O10 | process | after |
| OF011 | R0 / domain B / present / `inspection_0001` | O11 | harness | after |
| OF012 | R0 / domain B / present / `inspection_0001` | O12 | harness | after |
| OF013 | Rtransit / domain B / absent / `inspection_0005` | O01 | process | after |
| OF014 | Rtransit / domain B / absent / `inspection_0005` | O02 | process | after |
| OF015 | Rtransit / domain B / absent / `inspection_0005` | O03 | process | after |
| OF016 | Rtransit / domain B / absent / `inspection_0005` | O04 | process | after |
| OF017 | Rtransit / domain B / absent / `inspection_0005` | O05 | process | after |
| OF018 | Rtransit / domain B / absent / `inspection_0005` | O06 | process | after |
| OF019 | Rtransit / domain B / absent / `inspection_0005` | O07 | process | after |
| OF020 | Rtransit / domain B / absent / `inspection_0005` | O08 | process | after |
| OF021 | Rtransit / domain B / absent / `inspection_0005` | O09 | process | after |
| OF022 | Rtransit / domain B / absent / `inspection_0005` | O10 | process | after |
| OF023 | Rtransit / domain B / absent / `inspection_0005` | O11 | harness | after |
| OF024 | Rtransit / domain B / absent / `inspection_0005` | O12 | harness | after |
| OF025 | Rfinal / domain A / present / `inspection_0009` | O01 | process | after |
| OF026 | Rfinal / domain A / present / `inspection_0009` | O02 | process | after |
| OF027 | Rfinal / domain A / present / `inspection_0009` | O03 | process | after |
| OF028 | Rfinal / domain A / present / `inspection_0009` | O04 | process | after |
| OF029 | Rfinal / domain A / present / `inspection_0009` | O05 | process | after |
| OF030 | Rfinal / domain A / present / `inspection_0009` | O06 | process | after |
| OF031 | Rfinal / domain A / present / `inspection_0009` | O07 | process | after |
| OF032 | Rfinal / domain A / present / `inspection_0009` | O08 | process | after |
| OF033 | Rfinal / domain A / present / `inspection_0009` | O09 | process | after |
| OF034 | Rfinal / domain A / present / `inspection_0009` | O10 | process | after |
| OF035 | Rfinal / domain A / present / `inspection_0009` | O11 | harness | after |
| OF036 | Rfinal / domain A / present / `inspection_0009` | O12 | harness | after |

O01–O10 use the process-side arm/receipt on the original stdin pipe. O11–O12
use the harness-private plan/receipt and send no arm command to Unreal. Any
case after local publication yields `invalid`, no synchronized claim, exact
live census when observable, and unchanged canonical history.

Head publication cases `HF01`–`HF18`, binding cases `PB01`–`PB23`, and the six
liveness cases are exact as declared above. The 40 authority rows execute at
their named real adapter/router/probe/harness/canonical/source-audit boundary.
Python-only replay of a compiled/live case is insufficient. Every matrix stores
the exact channel and arm provenance, stage result, applicable process births,
process or harness trace prefix, receipt and observation presence, post-fault
census, disposition, and complete canonical before/after measurements.

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

Every launch, command, materialization, observation, disposition, liveness
sample, fault, and adversary survives as a registered occurrence. Unreal-side
work is process-bound; HF, O11/O12, and all liveness monitor/control actions are
harness-run-bound.
Compact summaries that cannot reconstruct every occurrence are rejected.

The exact runtime event schema is:

```yaml
trace_schema: CrossDomainOccupancyRuntimeTraceEvent.v1
trace_sequence: contiguous integer beginning at 0 per process
occurrence_id: exact witness/control/fault/adversary occurrence
operational_process_instance_id: exact original binding
process_binding_raw_sha256: exact binding digest
domain_role: domain_A | domain_B
command_sequence: exact nonnegative integer
command_schema: exact bind/materialize/inspect/fault/liveness-adversary schema
command_raw_sha256: exact measured canonical stdin-line digest
operation_id: bind_0001 | launch_0001 | refresh_0001 | refresh_0002 | inspection_0001 | inspection_0002 | inspection_0003 | inspection_0004 | inspection_0005 | inspection_0006 | inspection_0007 | inspection_0008 | inspection_0009 | inspection_c1_terminal_0001 | inspection_c2_rejection_0001 | inspection_c3_rejection_0001 | fault_case | liveness_LV03 | liveness_LV04 | liveness_LV05
stage_id: exact binding | M01-M23 | O01-O10 process stage | exact liveness_LV03-LV05 action
stage_edge: entered | completed | fault_injected
publication_generation: publication_0001 | publication_0002 | publication_0003 | null
represented_canonical_hash: exact accepted historical/local hash | null
input_member_device_inode_size_sha256: exact closed rows read at this stage
output_identity: exact receipt/observation/diagnostic identity | null
monotonic_process_local_counter: exact nonnegative integer
```

Harness-private stages use a separate trace with no process-command fiction:

```yaml
harness_trace_schema: CrossDomainOccupancyHarnessTraceEvent.v1
trace_sequence: contiguous integer beginning at 0 per harness operation occurrence
harness_occurrence_id: exact witness control fault adversary or replay occurrence
harness_run_id: exact current harness run
execution_mode: successful | fault_injected | liveness_adversary
case_id: null for successful mode | exact HF01-HF18 or OF011-OF012 or OF023-OF024 or OF035-OF036 for fault mode | exact LV01-LV06 for liveness mode
harness_operation_id: head_observation_0001 | head_observation_0002 | inspection_0001 | inspection_0002 | inspection_0003 | inspection_0004 | inspection_0005 | inspection_0006 | inspection_0007 | inspection_0008 | inspection_0009 | inspection_c1_terminal_0001 | inspection_c2_rejection_0001 | inspection_c3_rejection_0001 | liveness_LV01 | liveness_LV02 | liveness_LV03 | liveness_LV04 | liveness_LV05 | liveness_LV06
stage_id: open_source | pre_stat_source | read_source_once | post_stat_source | authenticate_record | construct_private_observation | write_and_fsync_candidate | atomic_publish | reopen_and_reverify | O11 | O12 | kill_original_child_note_exit | kill_original_child_waitpid | compare_report_binding_and_proc | observe_control_pipe_error_or_hup | observe_structured_output_eof | spawn_copied_label_replacement
stage_edge: entered | completed | fault_injected | failure_observed
harness_fault_plan_raw_sha256: exact authenticated plan digest for fault mode | null otherwise
harness_fault_arm_receipt_raw_sha256: exact authenticated arm-receipt digest for fault mode | null otherwise
liveness_plan_raw_sha256: exact authenticated plan digest for liveness mode | null otherwise
liveness_observation_raw_sha256: exact terminal independent observation digest at liveness failure_observed edge | null otherwise
liveness_adversarial_report_raw_sha256: exact LV03 report digest at LV03 failure_observed edge | null otherwise
canonical_before_after_snapshot_raw_sha256: exact complete measurement digest
```

Successful materialization commands contain the 23 completed process events in
order. Successful inspections contain O01–O10 in the process trace followed by
O11–O12 in the paired `execution_mode: successful` harness trace; fault and
liveness digest fields are exactly null. Successful head observations likewise
use successful-mode harness traces across all nine completed publication
stages. Fault-mode traces require non-null matching fault-plan and arm-receipt
digests, null liveness digests, equal the exact successful prefix through the
armed edge, and contain no later success event.

Liveness-mode harness traces use this closed mapping:

| Case | Exact harness operation | Exact stage | Exact ordered edges |
|---|---|---|---|
| LV01 | `liveness_LV01` | `kill_original_child_note_exit` | entered, completed, failure_observed |
| LV02 | `liveness_LV02` | `kill_original_child_waitpid` | entered, completed, failure_observed |
| LV03 | `liveness_LV03` | `compare_report_binding_and_proc` | entered, failure_observed |
| LV04 | `liveness_LV04` | `observe_control_pipe_error_or_hup` | entered, failure_observed |
| LV05 | `liveness_LV05` | `observe_structured_output_eof` | entered, failure_observed |
| LV06 | `liveness_LV06` | `spawn_copied_label_replacement` | entered, completed, failure_observed |

Every liveness event binds the exact non-null liveness-plan digest and null
fault digests. Its sole terminal `failure_observed` event binds the exact
independent terminal liveness observation; LV03 alone also binds the non-null
adversarial-report digest, and every other event has that field null. The
mode/case/operation/stage/edge/nullability cross-product is closed: any missing,
additional, reordered, cross-mode, or mismatched value rejects.
Every stdin write/complete read, output write/complete read, and descriptor
identity is cross-bound to the process trace; every private
operation/plan/arm/acceptance step is cross-bound to the harness trace.

The process-occurrence registry is one closed
`CrossDomainOccupancyProcessOccurrenceRegistry.v1` object with a row for every
positive W1–W4 process, six control occurrences, four asymmetric failures, 18
head faults, 138 materialization faults, 36 observation faults, 23 binding
adversaries, six liveness adversaries, 121 authority subcases, and four replay
repeats. Each row binds occurrence ID, artifact role, execution mode, expected
process count, actual unique process IDs/births, trace range, stdin range,
output range, harness-trace range where applicable, executable identity,
loaded-image inventory, initial-Actor inventory, and terminal disposition.
Counts are the exact sums of this frozen
case matrix; no extra or missing occurrence, process reuse where freshness is
required, identity conflict, or unreferenced process is accepted.

The source audit has exactly these 30 positive checks:

```yaml
source_checks:
  - S01_exact_phase2_discovery_entrypoint_only
  - S02_exact_phase2_resolver_entrypoint_only
  - S03_no_phase4_canonical_write_capability
  - S04_expected_constructor_exact_input_signature
  - S05_expected_constructor_field_by_field_mapping
  - S06_adapter_disposition_exact_input_signature
  - S07_projection_contains_no_expected_result
  - S08_receipt_contains_no_synchronized_claim
  - S09_probe_has_no_adapter_or_expected_pointer
  - S10_probe_exhaustive_world_enumeration
  - S11_head_observer_harness_private_only
  - S12_guard_has_no_canonical_dataflow_edge
  - S13_complete_argv_environment_cwd_descriptor_census
  - S14_complete_file_and_bundle_reader_census
  - S15_no_alternate_command_or_refresh_channel
  - S16_no_parent_sibling_or_other_domain_path
  - S17_complete_actor_spawn_destroy_and_lookup_census
  - S18_zero_pawn_possession_and_phase4_input_path_with_one_inert_controller
  - S19_no_route_transform_timer_collision_animation_navigation_authority
  - S20_no_physical_completion_or_successor_path
  - S21_no_peer_state_or_liveness_input
  - S22_process_harness_fault_and_liveness_adversary_channels_reachable_only_in_named_fresh_cases
  - S23_complete_runtime_command_handler_graph
  - S24_complete_cpp_call_surface_census
  - S25_complete_input_api_occurrence_census
  - S26_exact_translation_unit_byte_identity_set
  - S27_loaded_image_and_runtime_dependency_inventory
  - S28_initial_and_final_actor_inventory
  - S29_all_reachable_phase4_source_is_release_bound
  - S30_no_network_streaming_world_partition_or_production_path
```

The audit scans every authorized translation unit and reachable call edge. It
records the exact count and classification of every argv/environment,
filesystem, descriptor, socket, process, time, console, Actor-input, Actor-
creation, reflection, and dynamic-load API occurrence; the verifier independently
rescans and requires byte-for-byte equality. It records exact raw SHA-256 for
every translation unit and rejects any compiled source absent from the release
set.

Exactly 18 source mutations must be rejected: new `FFileHelper` read, direct
`open`, `readlink`, `access`, `lstat`, `getenv`, direct `environ`, argv branch,
socket read, timer-driven refresh, console command, Actor input binding,
unexpected Actor spawn class, reflected expected-count field, guard-to-resolver
edge, expected-state probe read, other-domain path read, and new canonical call.
Each mutation operates on an isolated source copy, recomputes superficial
summaries, and must fail the independent rescan or dataflow check.

## Exact frozen implementation, evidence, and release boundary

The accepted freeze authorizes only the following bounded implementation,
evidence, artifact, and release-verification surface. It grants no authority
outside this complete boundary.

The non-release review-time validator is exactly
`proof_kernel/validate_cross_domain_canonical_occupancy_materialization_spec.py`.
It validates this document and mutates only in-memory copies under
`--self-test`. It does not import runtime code, create evidence, belong to the
artifact directory or manifest, or grant implementation authority.

### Exact 82-member artifact directory

The authorized artifact directory is exactly
`proof_kernel/CrossDomainCanonicalOccupancyMaterializationProofRecords/` and
contains these 82 regular non-link files and no others, in this order:

```yaml
artifact_names:
  - cross_domain_occupancy_canonical_chain.json
  - cross_domain_occupancy_projection_matrix.json
  - cross_domain_occupancy_operation_tuple_matrix.json
  - cross_domain_occupancy_guard_and_head_observation_matrix.json
  - physical_W1_domain_A_R0_materialization_receipt.json
  - physical_W1_domain_A_R0_live_observation.json
  - physical_W1_domain_B_R0_materialization_receipt.json
  - physical_W1_domain_B_R0_live_observation.json
  - physical_W1_domain_A_Rtransit_materialization_receipt.json
  - physical_W1_domain_A_Rtransit_live_observation.json
  - physical_W1_domain_B_Rtransit_materialization_receipt.json
  - physical_W1_domain_B_Rtransit_live_observation.json
  - physical_W1_domain_A_Rfinal_materialization_receipt.json
  - physical_W1_domain_A_Rfinal_live_observation.json
  - physical_W1_domain_B_Rfinal_materialization_receipt.json
  - physical_W1_domain_B_Rfinal_live_observation.json
  - physical_W1_liveness_witness.json
  - physical_W1_A_B__A_B_witness.json
  - physical_W2_domain_A_R0_materialization_receipt.json
  - physical_W2_domain_A_R0_live_observation.json
  - physical_W2_domain_B_R0_materialization_receipt.json
  - physical_W2_domain_B_R0_live_observation.json
  - physical_W2_domain_A_Rtransit_materialization_receipt.json
  - physical_W2_domain_A_Rtransit_live_observation.json
  - physical_W2_domain_B_Rtransit_materialization_receipt.json
  - physical_W2_domain_B_Rtransit_live_observation.json
  - physical_W2_domain_A_Rfinal_materialization_receipt.json
  - physical_W2_domain_A_Rfinal_live_observation.json
  - physical_W2_domain_B_Rfinal_materialization_receipt.json
  - physical_W2_domain_B_Rfinal_live_observation.json
  - physical_W2_liveness_witness.json
  - physical_W2_B_A__B_A_witness.json
  - physical_W3_domain_A_R0_materialization_receipt.json
  - physical_W3_domain_A_R0_live_observation.json
  - physical_W3_domain_B_R0_materialization_receipt.json
  - physical_W3_domain_B_R0_live_observation.json
  - physical_W3_domain_A_Rtransit_materialization_receipt.json
  - physical_W3_domain_A_Rtransit_live_observation.json
  - physical_W3_domain_B_Rtransit_materialization_receipt.json
  - physical_W3_domain_B_Rtransit_live_observation.json
  - physical_W3_domain_A_Rfinal_materialization_receipt.json
  - physical_W3_domain_A_Rfinal_live_observation.json
  - physical_W3_domain_B_Rfinal_materialization_receipt.json
  - physical_W3_domain_B_Rfinal_live_observation.json
  - physical_W3_liveness_witness.json
  - physical_W3_A_B__B_A_witness.json
  - physical_W4_domain_A_R0_materialization_receipt.json
  - physical_W4_domain_A_R0_live_observation.json
  - physical_W4_domain_B_R0_materialization_receipt.json
  - physical_W4_domain_B_R0_live_observation.json
  - physical_W4_domain_A_Rtransit_materialization_receipt.json
  - physical_W4_domain_A_Rtransit_live_observation.json
  - physical_W4_domain_B_Rtransit_materialization_receipt.json
  - physical_W4_domain_B_Rtransit_live_observation.json
  - physical_W4_domain_A_Rfinal_materialization_receipt.json
  - physical_W4_domain_A_Rfinal_live_observation.json
  - physical_W4_domain_B_Rfinal_materialization_receipt.json
  - physical_W4_domain_B_Rfinal_live_observation.json
  - physical_W4_liveness_witness.json
  - physical_W4_B_A__A_B_witness.json
  - control_C1_canonical_completion_independence.json
  - control_C2_positive_Rtransit_absence.json
  - control_C3_receipt_only_rejection.json
  - control_C4a_start_guard_open.json
  - control_C4b_completion_guard_open.json
  - control_C5_process_replacement.json
  - failure_AF01_Rtransit_A_success_B_failure.json
  - failure_AF02_Rtransit_B_success_A_failure.json
  - failure_AF03_Rfinal_A_success_B_failure.json
  - failure_AF04_Rfinal_B_success_A_failure.json
  - cross_domain_occupancy_process_binding_adversaries.json
  - cross_domain_occupancy_authority_adversaries.json
  - cross_domain_occupancy_head_publication_fault_atomicity.json
  - cross_domain_occupancy_materialization_fault_atomicity.json
  - cross_domain_occupancy_live_observation_fault_atomicity.json
  - cross_domain_occupancy_liveness_adversaries.json
  - cross_domain_occupancy_proof_semantic_input_audit.json
  - cross_domain_occupancy_canonical_equivalence_oracle.json
  - cross_domain_occupancy_source_audit.json
  - cross_domain_occupancy_replay_oracle.json
  - cross_domain_occupancy_process_occurrence_registry.json
  - cross_domain_occupancy_proof_run.json
```

The four global matrices bind exact canonical bytes, projection bytes, six
operation tuples, both head observations, and every legal/illegal guard edge.
Each W member embeds exact commands, generation identities, process bindings,
dispositions, checkpoint traces, and canonical measurements. Aggregated fault
and adversary artifacts retain every exact subcase row; no compact boolean
summary substitutes for occurrences.

### Exact release DAG

```text
five exact sealed Phase-2 record/boundary inputs
        ↓
exact Phase-2 scheduler/resolver: R0 → Rtransit → Rfinal
        ↓
six byte-bound projections + six closed operation tuples
        ↓
two suspended direct children + exact 22-field bindings
        ↓
R0 locally-published-unverified generations
        ↓
independent expectations + exhaustive live censuses + synchronized R0 dispositions
        ↓
close guard → exact start commit → private Rtransit head publication
        ↓
head-unconfirmed → stale R0 → open_for_Rtransit
        ↓
W1–W4 first refresh cycle + mixed L3 censuses + synchronized Rtransit
        ↓
close guard → freshly rediscovered exact completion → private Rfinal publication
        ↓
head-unconfirmed → stale Rtransit → open_for_Rfinal
        ↓
W1–W4 second refresh cycle + mixed L7 censuses + synchronized Rfinal
        ↓
C1, C2, C3, C4a, C4b, C5 + AF01–AF04
        ↓
PB01–PB23 + HF01–HF18 + MF001–MF138 + OF001–OF036
        ↓
six liveness cases + A01–A40 / 121 exact authority subcases
        ↓
input/source audit + canonical equivalence + replay + process registry
        ↓
proof run + evidence document
        ↓
self-excluding 172-member sorted SHA-256 manifest
        ↓
release verifier independently validates exact set, hashes, relations, and semantics
```

No node outside this DAG is proof evidence. Expected representation is derived
before receipt/observation comparison; the head observer remains harness-
private; the guard has no canonical edge; and no physical state can trigger
completion.

### Exact 90 non-artifact release members

The 172 manifest members are the 82 artifact paths plus these exact 90 paths:

```yaml
governing_and_predecessor_members:
  - README.md
  - Resolution Semantics Law - v0.1.1.md
  - Record-Relative Chronological Resolution Proof Evidence - v0.1.0.md
  - Integrated Unreal Promotion-Unload-Repromotion Proof Evidence - v0.1.0.md
  - Canonical Spatial Topology Identity Proof - Draft.md
  - Canonical Spatial Topology Identity Proof Evidence - v0.1.0.md
  - Canonical Spatial Topology Identity Proof - v0.1.0 SHA256SUMS.txt
  - Canonical Occupancy Transition Proof - Draft.md
  - Canonical Occupancy Transition Proof Evidence - v0.1.0.md
  - Canonical Occupancy Transition Proof - v0.1.0 SHA256SUMS.txt
  - Simultaneous Physical Domains Proof - Draft.md
  - Simultaneous Physical Domains Proof - v0.1.1.md
  - Simultaneous Physical Domains Proof Evidence - v0.1.1.md
  - Simultaneous Physical Domains Proof - v0.1.1 SHA256SUMS.txt
  - Cross-Domain Canonical Occupancy Materialization Proof - Draft.md
  - Cross-Domain Canonical Occupancy Materialization Proof Evidence - v0.1.0.md
  - Co-op Open-City FPS Simulation - v0.7 Working Continuation.md
  - THE_CITY Development Capacity and Progress Note - v0.1.11.md
  - THE_CITY Developer Snapshot - v0.1.0.md
  - THE_CITY Current Proof State and Repo-Agent Instruction - v0.1.0.md

sealed_canonical_input_members:
  - proof_kernel/CanonicalOccupancyTransitionProofRecords/canonical_occupancy_transition_R0.json
  - proof_kernel/CanonicalOccupancyTransitionProofRecords/canonical_occupancy_transition_start_boundary_H0.json
  - proof_kernel/CanonicalOccupancyTransitionProofRecords/canonical_occupancy_transition_Rtransit.json
  - proof_kernel/CanonicalOccupancyTransitionProofRecords/canonical_occupancy_transition_completion_boundary_Htransit.json
  - proof_kernel/CanonicalOccupancyTransitionProofRecords/canonical_occupancy_transition_Rfinal.json

python_source_members:
  - proof_kernel/kernel.py
  - proof_kernel/canonical_spatial_topology_identity.py
  - proof_kernel/canonical_occupancy_transition.py
  - proof_kernel/simultaneous_physical_domains.py
  - proof_kernel/simultaneous_physical_domains_harness.py
  - proof_kernel/test_canonical_occupancy_transition.py
  - proof_kernel/test_simultaneous_physical_domains.py
  - proof_kernel/verify_canonical_occupancy_transition_release.py
  - proof_kernel/verify_simultaneous_physical_domains_release.py
  - proof_kernel/cross_domain_canonical_occupancy_materialization.py
  - proof_kernel/cross_domain_canonical_occupancy_materialization_harness.py
  - proof_kernel/test_cross_domain_canonical_occupancy_materialization.py
  - proof_kernel/verify_cross_domain_canonical_occupancy_materialization_release.py

unreal_project_members:
  - CityMaterializationProof/CityMaterializationProof.uproject
  - CityMaterializationProof/Config/DefaultEngine.ini
  - CityMaterializationProof/Config/DefaultGame.ini
  - CityMaterializationProof/Config/DefaultInput.ini
  - CityMaterializationProof/README.md
  - CityMaterializationProof/Source/CityMaterializationProof.Target.cs
  - CityMaterializationProof/Source/CityMaterializationProofEditor.Target.cs
  - CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationProof.Build.cs
  - CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationProof.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationProof.h
  - CityMaterializationProof/Source/CityMaterializationProof/CityProofGameMode.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/CityProofGameMode.h
  - CityMaterializationProof/Source/CityMaterializationProof/BridgeAccessPoint.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/BridgeAccessPoint.h
  - CityMaterializationProof/Source/CityMaterializationProof/CanonicalSpatialTopologyProofAdapter.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/CanonicalSpatialTopologyProofAdapter.h
  - CityMaterializationProof/Source/CityMaterializationProof/CanonicalTopologyRepresentationActor.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/CanonicalTopologyRepresentationActor.h
  - CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationActor.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationActor.h
  - CityMaterializationProof/Source/CityMaterializationProof/CityProofCharacter.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/CityProofCharacter.h
  - CityMaterializationProof/Source/CityMaterializationProof/ConcurrentEvidenceSurface.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/ConcurrentEvidenceSurface.h
  - CityMaterializationProof/Source/CityMaterializationProof/ConcurrentExternalEvidenceProofAdapter.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/ConcurrentExternalEvidenceProofAdapter.h
  - CityMaterializationProof/Source/CityMaterializationProof/CrewOperationPoint.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/CrewOperationPoint.h
  - CityMaterializationProof/Source/CityMaterializationProof/IntegratedGateTokenPoint.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/IntegratedGateTokenPoint.h
  - CityMaterializationProof/Source/CityMaterializationProof/IntegratedUnrealProofAdapter.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/IntegratedUnrealProofAdapter.h
  - CityMaterializationProof/Source/CityMaterializationProof/LiveCommitmentRelayPoint.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/LiveCommitmentRelayPoint.h
  - CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainCommandRouter.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainCommandRouter.h
  - CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainProofAdapter.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainProofAdapter.h
  - CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainRepresentationActor.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainRepresentationActor.h
  - CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalRebindProbe.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalRebindProbe.h
  - CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyCommandRouter.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyCommandRouter.h
  - CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyProofAdapter.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyProofAdapter.h
  - CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyHeadAnchorActor.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyHeadAnchorActor.h
  - CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancySubjectActor.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancySubjectActor.h
  - CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyLiveWorldProbe.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyLiveWorldProbe.h
```

### Exact bounded implementation authority under this accepted freeze

```yaml
frozen_implementation_authority:
  new_python_paths:
    - proof_kernel/cross_domain_canonical_occupancy_materialization.py
    - proof_kernel/cross_domain_canonical_occupancy_materialization_harness.py
    - proof_kernel/test_cross_domain_canonical_occupancy_materialization.py
    - proof_kernel/verify_cross_domain_canonical_occupancy_materialization_release.py
  new_unreal_paths:
    - CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyCommandRouter.cpp
    - CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyCommandRouter.h
    - CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyProofAdapter.cpp
    - CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyProofAdapter.h
    - CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyHeadAnchorActor.cpp
    - CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyHeadAnchorActor.h
    - CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancySubjectActor.cpp
    - CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancySubjectActor.h
    - CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyLiveWorldProbe.cpp
    - CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyLiveWorldProbe.h
  bounded_existing_source_change:
    path: CityMaterializationProof/Source/CityMaterializationProof/CityProofGameMode.cpp
    scope: phase_4_cross_domain_occupancy_dispatch_zero_pawn_and_inert_controller_branch_only
  new_evidence_path: Cross-Domain Canonical Occupancy Materialization Proof Evidence - v0.1.0.md
  changed_governing_paths:
    - README.md
    - Co-op Open-City FPS Simulation - v0.7 Working Continuation.md
    - THE_CITY Developer Snapshot - v0.1.0.md
    - THE_CITY Current Proof State and Repo-Agent Instruction - v0.1.0.md
  new_or_changed_non_artifact_members:
    - README.md
    - Cross-Domain Canonical Occupancy Materialization Proof Evidence - v0.1.0.md
    - Co-op Open-City FPS Simulation - v0.7 Working Continuation.md
    - THE_CITY Developer Snapshot - v0.1.0.md
    - THE_CITY Current Proof State and Repo-Agent Instruction - v0.1.0.md
    - proof_kernel/cross_domain_canonical_occupancy_materialization.py
    - proof_kernel/cross_domain_canonical_occupancy_materialization_harness.py
    - proof_kernel/test_cross_domain_canonical_occupancy_materialization.py
    - proof_kernel/verify_cross_domain_canonical_occupancy_materialization_release.py
    - CityMaterializationProof/Source/CityMaterializationProof/CityProofGameMode.cpp
    - CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyCommandRouter.cpp
    - CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyCommandRouter.h
    - CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyProofAdapter.cpp
    - CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyProofAdapter.h
    - CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyHeadAnchorActor.cpp
    - CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyHeadAnchorActor.h
    - CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancySubjectActor.cpp
    - CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancySubjectActor.h
    - CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyLiveWorldProbe.cpp
    - CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyLiveWorldProbe.h
  new_or_changed_non_artifact_member_count: 20
  unchanged_non_artifact_member_definition: exact 90-member set minus exact 20-member list above
  unchanged_non_artifact_member_count: 70
  artifact_directory: proof_kernel/CrossDomainCanonicalOccupancyMaterializationProofRecords/
  artifact_member_count: 82
  manifest_path: Cross-Domain Canonical Occupancy Materialization Proof - v0.1.0 SHA256SUMS.txt
  manifest_member_count_excluding_manifest: 172
  frozen_specification_path: Cross-Domain Canonical Occupancy Materialization Proof - Draft.md
  frozen_specification_change: prohibited
  excluded_operational_record_path: handover.md
  excluded_operational_record_authority: informational_handover_updates_only
  capacity_advancement: none
```

Only those four new Python paths, ten new Unreal paths, bounded
`CityProofGameMode.cpp` branch, one evidence document, four exact governing
paths, exact 82-member artifact directory, and self-excluding manifest may
change under this accepted freeze. Those are exactly 20 of the 90
non-artifact members. The other exact 70 non-artifact members are the
set-theoretic difference against the complete ordered 90-member list above and
must remain byte-identical, including this frozen specification, the capacity
record, every predecessor record, and every other existing source/project/
config member. `handover.md` may receive informational excluded-record updates
only; it is not a release member or implementation surface. The validator is
non-release QA, not implementation.

The authorized focused suite contains exactly 45 test contracts: three canonical
artifact/hash contracts, six projection rows, six operation tuples, three
paired-head expected-representation contracts covering six exact role rows,
eleven permission contexts, six controls, four
refresh-order witnesses, four asymmetric failures, canonical replay, and
release-set closure. Implementation acceptance also requires 215/215 existing
canonical regressions, the exact Phase-2 33/33 seal export, exact Phase-3
111/111 seal export with 41/41 adversaries rejected, a UE 5.8 editor build, all
live matrices above, 30/30 source checks, 18/18 source mutations rejected, and
the exact 82/172 release boundary.

The manifest excludes itself. Its 172 lines are the complete union above,
sorted by raw UTF-8 relative-path bytes and encoded as lowercase 64-hex SHA-256,
two ASCII spaces, path, LF. Every member is one regular non-symlink file beneath
the repository realpath. The verifier must regenerate deterministic artifacts
in isolation, semantically validate every live occurrence, rerun all tests and
audits, reject 30 exact in-memory verifier mutations, enforce exact directory
and release membership, and verify every hash without trusting pass booleans.
After a later seal, verification must use an isolated export of the exact seal
commit; current governing documents may not be absorbed by rewriting a
historical manifest.

## Explicit exclusions

This frozen specification does not authorize or prove:

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
- implementation outside the exact frozen boundary.

## Frozen acceptance contract

Independent final freeze review accepted the exact candidate commit and tree
bound above and established:

```yaml
freeze_acceptance:
  proof_question: one exact Phase-2 chain / one subject / two original Phase-4 processes
  sealed_canonical_inputs: 5 exact regular files / 3 records / 2 boundaries
  phase_2_reuse: exact scheduler and resolver / fresh Rtransit completion discovery
  phase_3_reuse: exact sealed commit identities and rebound lifecycle mechanisms
  process_binding: 22 ordered fields / PB01-PB23 / closed witness enum
  liveness: L0-L8 / six exact lifecycle adversaries / mixed-state censuses
  projections: 6 exact canonical-JSON rows with raw SHA-256
  operation_tuples: 6 exact three-file bundles / no legal cross-products
  expectation_oracle: CrossDomainOccupancyExpectedRepresentation.v1 / independent inputs only
  anchor_schema: CrossDomainOccupancyHeadAnchor.v1 / locally_published_unverified
  subject_schema: CrossDomainOccupancySubjectRepresentation.v1 / symbolic local-site correspondence
  live_oracle: CrossDomainOccupancyLiveObservation.v1 / exhaustive world census
  guard: 7 states / 6 legal transition classes / C1 terminal close / failed_closed absorbing
  head_observation: 2 exact rows / HF01-HF18
  permissions: 11 exact context rows / every canonical permission false
  publication: 23 ordered stages / claim linearizes only at harness disposition
  witnesses: W1-W4 exact four-order matrix
  controls: C1 C2 C3 C4a C4b C5 / 6 exact artifacts
  asymmetric_failures: AF01-AF04
  authority_adversaries: A01-A40 / 121 executed subcases
  fault_matrices: PB23 + HF18 + MF138 + OF36 + 6 liveness cases
  canonical_measurement: complete record ledger ancestry reservation unresolved-work snapshots
  provenance: closed runtime trace and process-occurrence registry
  source_audit: S01-S30 / 18 source mutations rejected
  release: 82 artifacts + 90 non-artifact members = 172 self-excluding manifest members
  focused_tests: 45 exact contracts
  predecessor_regressions: 215
  validator: 20 default checks / 32 in-memory mutation rejections / outside release
  future_release_verifier: 30 in-memory mutation rejections / exact isolated regeneration
  exclusions: physical placement movement player network streaming production and capacity
```

The accepted freeze excludes an ambiguous absence oracle, optional anchor,
receipt-only acceptance, incomplete Actor census, unspecified partial-
publication disposition, unbound refresh channel, generalized head/guard
abstraction, direct catch-up ambiguity, and any route from physical state to
canonical completion.

## Frozen implementation acceptance statement

If the authorized implementation passes every required gate, it may establish
only:

> **The exact sealed Phase-2 R0 → Rtransit → Rfinal occupancy chain can be
> represented across the same two original, simultaneously live Phase-3 Unreal
> domains. At each accepted head, an exact positive head anchor and independent
> live-world census prove symbolic correspondence between the sole canonical
> subject and only the local projection of its canonical endpoint, no subject
> correspondence at either endpoint while canonically in transition, and only
> destination correspondence after canonical completion. No transform or
> physical-placement relation is claimed. The
> sealed Phase-2 record remains the sole authority for occupancy, transition,
> completion, reservation, ledger, ancestry, and successor publication; stale
> or failed physical representation cannot alter that authority.**

It may not establish physical traversal, multiple subjects, players,
networking, streaming, arbitrary domains, production materialization, or any
capacity increase.

## Specification review history

### 0.1.0 — 2026-08-29

- Independent final freeze review returned `ACCEPT_FOR_FREEZE` for exact
  candidate commit `fd2d62f404936eb961d7d1571204f1a352439bd7`, tree
  `b8b7bd6259d72c685ac5dee3c1488b19025b0fb3`.
- Froze `Cross-Domain Canonical Occupancy Materialization Proof v0.1.0` under
  `CrossDomainCanonicalOccupancyMaterializationProof.v1` /
  `0.7.0-draft.80`.
- Authorized only the exact four Python paths, ten Unreal paths, bounded
  `CityProofGameMode.cpp` branch, evidence path, four governing paths,
  82-member artifact directory, and self-excluding 172-member release declared
  above.
- Kept evidence unsealed, capacity at v0.1.11, Phase 5 closed, and every
  production or adjacent scope unauthorized.

### 0.1.0-draft.1 — 2026-08-29

- Closed the independent `STOP_WITH_FINDINGS` review of exact candidate commit
  `b31c2895aec82c9688f6525219598b9ac1a274cc` without granting implementation.
- Closed the later final freeze-review `STOP_WITH_FINDINGS` against commit
  `299aa865c5757fb63aeef27a9c4eb48554dcea6f`: froze detached JSON bytes and
  LF-inclusive raw digests, separated logical binding validation order from
  recursive stored-key order, made LV01–LV06 and AF01–AF04 field-exact, and
  made successful and injected harness traces schema-complete.
- Replaced premature Unreal `synchronized` claims with
  `locally_published_unverified`; only the later harness disposition may
  synchronize after independent expectation and exhaustive live census.
- Froze six projection byte identities, six legal operation tuples, the exact
  22-field binding, L0–L8 mixed-state census, two head observations, seven-state
  guard, eleven-row permission matrix, and realizable generation-acceptance
  linearization.
- Made C1–C5 executable, split C4a/C4b, froze AF01–AF04, A01–A40 with 121
  subcases, PB01–PB23, HF01–HF18, MF001–MF138, OF001–OF036, and six liveness
  adversaries.
- Froze 30 source checks, 18 source mutations, exact runtime/process
  provenance, four Python and ten Unreal implementation paths, 82 artifacts,
  90 other release members, and a self-excluding 172-member manifest.
- Advanced only to final freeze review under candidate simulation identity
  `0.7.0-draft.80`; capacity remains v0.1.11 and implementation remains
  prohibited.

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
working_unit: Cross-Domain Canonical Occupancy Materialization Proof v0.1.0 bounded implementation
phase: 4
successor_selected: true
simulation_identity: 0.7.0-draft.80
accepted_candidate_commit: fd2d62f404936eb961d7d1571204f1a352439bd7
accepted_candidate_tree: b8b7bd6259d72c685ac5dee3c1488b19025b0fb3
specification_status: frozen
freeze_status: frozen
implementation_authority: bounded_phase_4_proof_only
unreal_source_change_authority: exact_frozen_phase_4_paths_only
evidence_authority: exact_frozen_phase_4_evidence_only
release_authority: exact_frozen_phase_4_release_only
evidence_status: unsealed
canonical_capacity_change: none
latest_sealed_capacity: THE_CITY Development Capacity and Progress Note v0.1.11
phase_5: closed
```

The specification is frozen. Implementation authority is limited to the exact
Phase-4 paths and bounded `CityProofGameMode.cpp` branch declared by this
contract. It permits the named proof implementation, Unreal adapter, harness,
tests, evidence, artifacts, and release verification only. It grants no
capacity advancement, Phase 5, production architecture, or adjacent scope.
