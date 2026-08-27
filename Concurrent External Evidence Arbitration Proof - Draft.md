# Concurrent External Evidence Arbitration Proof

**Version:** 0.1.0
**Status:** Frozen specification. Implementation is authorized only for the bounded DAG and acceptance gates in this record; evidence is not yet sealed.
**Selected:** 2026-08-27
**Parent continuation:** [Co-op Open-City FPS Simulation — v0.7 Working Continuation](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)
**Sealed predecessors:** [External Input Boundary Proof — v0.1.1](External%20Input%20Boundary%20Proof%20Evidence%20-%20v0.1.1.md); [Shared-State Commitment Interference Proof — v0.1.0](Shared-State%20Commitment%20Interference%20Proof%20Evidence%20-%20v0.1.0.md); [Record-Relative Chronological Resolution Proof — v0.1.0](Record-Relative%20Chronological%20Resolution%20Proof%20Evidence%20-%20v0.1.0.md); [Integrated Unreal Promotion-Unload-Repromotion Proof — v0.1.0](Integrated%20Unreal%20Promotion-Unload-Repromotion%20Proof%20Evidence%20-%20v0.1.0.md)
**Frozen simulation identity:** `0.7.0-draft.57`.

## Question

> **Can two independently evidenced external inputs, both validly bound to the
> same canonical R0, be admitted side-effect-free into one canonical external
> arbitration batch whose frozen ordering and working-state revalidation
> produce one deterministic successor history independent of physical,
> filesystem, or sealed-fixture harness-presentation order?**

This proof extends exactly one dimension of the sealed machine:

```text
one R0-bound physical Q
        ↓
two independently generated R0-bound physical Q members
        ↓
one R0-authorized canonical external batch
        ↓
one atomic canonical successor
```

It does not introduce retry, re-admission, networking, split crews, movement,
streaming, or two sequential external transactions.

## Frozen proof boundary

```yaml
next_working_unit:
  name: Concurrent External Evidence Arbitration Proof
  version: 0.1.0
  status: frozen_implementation_authorized

scope:
  canonical_source_records: 1
  canonical_inputs_in_primary: 2
  unreal_source_domains: 2
  canonical_external_batches: 1
  canonical_successors_per_execution: 1
  autonomous_commitments: 0
  shared_authoritative_facts: 1
  randomness: prohibited
  networking: prohibited
  retry_or_readmission: prohibited
  movement: prohibited
  streaming: prohibited
  same_clock_successor_creation: prohibited
  split_player_topology: prohibited
```

`domain_A`, `domain_B`, `QA`, `QB`, and `shared_slot` are neutral proof
fixtures. They are not production player, crew, resource, network, or city
ontology.

## New simulator law

> **Multiple external evidence candidates may share one immutable source-record
> authority and one atomic canonical batch. Their evidence authority remains
> bound to the batch pre-state; their mutation eligibility is revalidated in
> canonical member order against the evolving provisional working state.**

The corresponding prohibition is:

> **Physical emission order, UE process scheduling, filesystem creation order,
> directory enumeration, sealed-fixture harness presentation, OS timestamps, and
> thread scheduling have no canonical ordering authority.**

This law begins only after one exact fixture candidate set has been supplied.
It proves no input-discovery, collection-window, transport-completeness,
timeout, or live-arrival law.

## One batch, not sequential external transactions

The primary machine is:

```text
R0 / H0

QA ─┐
    ├─ side-effect-free admission against immutable R0
QB ─┘
        ↓
BEXT
  source_record_hash = H0
  batch_pre_state_hash = H0
  admitted member set = {QA, QB}
  member order = derived canonically
        ↓
QA revalidates against working R0
  shared-slot gate passes
  provisional mutation allocates A
        ↓
QB remains an R0-authorized BEXT member
  revalidates against provisional A allocation
  unchanged ordinary shared-slot gate fails
  no resource acquired
        ↓
close one atomic batch
        ↓
R1 / singular parent H0 / one batch ledger entry
```

Neither member creates a canonical successor. `PA`, the identity of the
provisional state after QA and before QB, is batch-local provenance only. It is
not R1, is never exposed as city truth, cannot be materialized, and cannot
authorize later work.

QB is not re-admitted against R1. No R1 exists until the complete batch closes.

## Frozen identity

The following identity is frozen:

```yaml
record_schema: CanonicalResolutionEnvelope.v1
payload_schema: ConcurrentExternalEvidenceArbitrationPayload.v1
scenario_id: concurrent-external-evidence-arbitration-v1
scenario_version: 0.1.0
simulation_version: 0.7.0-draft.57
seed: concurrent-external-evidence-arbitration-v1/0001
```

The exact payload, Q, batch-capability, ledger, receipt, and serialization
contracts are frozen below. A new authoritative field requires a new payload
schema and simulation identity.

The predecessor canonical-JSON law remains the frozen serializer: sorted
object keys, compact separators, `ensure_ascii = true`, no duplicate keys or
non-finite numbers, declared array order preserved, and lowercase SHA-256.
Stored artifacts have one terminal LF; hashed JSON values do not.

No canonical record or ledger entry may contain its own successor hash.

## Exact frozen serialization contract

The following definitions are normative. Later abbreviated YAML fragments are
readability projections of these definitions and grant no additional field.

### Fixed domain table and derived identities

```yaml
domain_A:
  source_domain: domain_A
  physical_actor_id: arbitration_surface_A_01
  input_id: physical_allocate_shared_slot_A_0001
  physical_event_id: domain_A_allocation_event_0001
  allocation_owner: domain_A

domain_B:
  source_domain: domain_B
  physical_actor_id: arbitration_surface_B_01
  input_id: physical_allocate_shared_slot_B_0001
  physical_event_id: domain_B_allocation_event_0001
  allocation_owner: domain_B
```

For a complete canonical envelope `R`:

```text
canonical_hash(R) = lowercase_sha256(UTF-8(canonical_json(R)))
stored_payload(R) = UTF-8(canonical_json(R) + "\n")
raw_payload_sha256(R) = lowercase_sha256(stored_payload(R))

H0 = canonical_hash(R0)
D0 = raw_payload_sha256(R0)
HQ(X) = lowercase_sha256(UTF-8(canonical_json(Q(X))))
stored_Q(X) = UTF-8(canonical_json(Q(X)) + "\n")
DQ(X) = lowercase_sha256(stored_Q(X))
```

`HQ(X)` is evidence-object identity only. It is never a canonical-record hash
and rejects in every canonical record-identity field.

### Exact R0

```yaml
identity:
  record_schema: CanonicalResolutionEnvelope.v1
  payload_schema: ConcurrentExternalEvidenceArbitrationPayload.v1
  scenario_id: concurrent-external-evidence-arbitration-v1
  scenario_version: 0.1.0
  simulation_version: 0.7.0-draft.57
  seed: concurrent-external-evidence-arbitration-v1/0001
current_causal_state:
  shared_slot:
    allocation_owner: null
  external_consequence_contracts:
    domain_A:
      physical_actor_id: arbitration_surface_A_01
      permitted_input_id: physical_allocate_shared_slot_A_0001
      permitted_physical_event_id: domain_A_allocation_event_0001
      target: {kind: proof_shared_slot, id: shared_slot_01}
      observed_outcome: allocation_requested
      permitted_owner: domain_A
    domain_B:
      physical_actor_id: arbitration_surface_B_01
      permitted_input_id: physical_allocate_shared_slot_B_0001
      permitted_physical_event_id: domain_B_allocation_event_0001
      target: {kind: proof_shared_slot, id: shared_slot_01}
      observed_outcome: allocation_requested
      permitted_owner: domain_B
future_causal_state:
  canonical_clock: t0/00
  unresolved_work: []
causal_provenance:
  adjudicated_external_input_ids: []
  adjudicated_physical_event_ids: []
  authoritative_causal_ledger: []
  canonical_ancestry: null
  fixture_genesis:
    source: frozen_initial_fixture
```

No other R0 field is permitted.

### Exact Q(X)

For `X` equal to one row of the fixed domain table, Q is exactly:

```yaml
protocol_version: ConcurrentExternalEvidence.v1
input_id: X.input_id
physical_event_id: X.physical_event_id
source:
  system: crew_physical_simulation
  domain: X.source_domain
  source_record_hash: H0
  source_payload_raw_sha256: D0
occurrence_time: t0/30
target: {kind: proof_shared_slot, id: shared_slot_01}
observed_outcome: {state: allocation_requested}
proposed_effect:
  op: replace
  path: /current_causal_state/shared_slot/allocation_owner
  value: X.allocation_owner
evidence:
  physical_actor_id: X.physical_actor_id
  outcome_state: allocation_requested
  evidence_digest: evidence_digest(X)
```

`evidence_digest(X)` is lowercase SHA-256 of canonical JSON for this complete Q
with only `evidence.evidence_digest` omitted. No additional or missing Q field
is permitted.

### Exact detached Unreal contracts

Each source launch receives exact stored R0 plus:

```yaml
receipt_schema: ConcurrentUnrealLaunchReceipt.v1
artifact_role: canonical_materialization_input
raw_byte_sha256: D0
canonical_hash: H0
expected_record_schema: CanonicalResolutionEnvelope.v1
expected_payload_schema: ConcurrentExternalEvidenceArbitrationPayload.v1
expected_scenario_id: concurrent-external-evidence-arbitration-v1
expected_simulation_version: 0.7.0-draft.57
```

After verification and materialization, source X emits exactly one acceptance
receipt:

```yaml
receipt_schema: ConcurrentMaterializationAcceptanceReceipt.v1
process_instance_id: operational_process_instance_id
materialization_domain: X.source_domain
accepted_canonical_hash: H0
accepted_raw_payload_sha256: D0
materialized_physical_actor_id: X.physical_actor_id
materialized_shared_slot_owner: null
proposal_capability_enabled: true
```

After physical interaction, source X emits Q(X) and exactly one:

```yaml
receipt_schema: ConcurrentEvidenceEmissionReceipt.v1
process_instance_id: same_operational_process_instance_id
materialization_domain: X.source_domain
accepted_canonical_hash: H0
accepted_raw_payload_sha256: D0
materialized_physical_actor_id: X.physical_actor_id
emitted_input_id: X.input_id
emitted_physical_event_id: X.physical_event_id
emitted_q_canonical_hash: HQ(X)
emitted_q_raw_sha256: DQ(X)
```

The operational process string is noncanonical, unique per launched process,
and excluded from Q, BEXT, R1, and every canonical ordering input.

### Exact admitted member and sealed fixture contracts

An admitted member for X is exactly:

```yaml
admitted_member_schema: AdmittedExternalMember.v1
input_id: X.input_id
physical_event_id: X.physical_event_id
source_record_hash: H0
source_raw_payload_sha256: D0
q_canonical_hash: HQ(X)
q_raw_sha256: DQ(X)
evidence_digest: evidence_digest(X)
occurrence_time: t0/30
derived_external_phase: 10
derived_canonical_external_priority: 100
immutable_admission_observations:
  - {name: canonical_q_shape_matches, observed_value: exact, required_value: exact, result: true}
  - {name: evidence_digest_matches, observed_value: true, required_value: true, result: true}
  - {name: exact_consequence_contract_matches, observed_value: true, required_value: true, result: true}
  - {name: source_record_hash_matches, observed_value: H0, required_value: H0, result: true}
  - {name: source_raw_payload_sha256_matches, observed_value: D0, required_value: D0, result: true}
  - {name: occurrence_time_matches_fixture, observed_value: t0/30, required_value: t0/30, result: true}
  - {name: input_id_not_adjudicated, observed_value: true, required_value: true, result: true}
  - {name: physical_event_id_not_adjudicated, observed_value: true, required_value: true, result: true}
  - {name: shared_slot_available, observed_value: null, required_value: null, result: true}
```

The primary `ConcurrentExternalCandidateSetFixture.v1` is the exact two-member
object already shown below. QA-only and QB-only controls use the same schema,
their own fixed fixture IDs ending `-qa-only-v1` / `-qb-only-v1`, and the
corresponding one-element input/event sets. No fixture array position is an
ordering input.

### Exact BEXT

For the primary admitted-member map, BEXT is exactly:

```yaml
batch_schema: ConcurrentExternalArbitrationBatch.v1
kind: external_arbitration_batch
source_record_hash: H0
batch_pre_state_hash: H0
decision_time: t0/30
external_phase: 10
ordering_law: ConcurrentExternalMemberOrder.v1
member_set_digest: member_set_digest
member_ids:
  - physical_allocate_shared_slot_A_0001
  - physical_allocate_shared_slot_B_0001
```

`member_set_digest` is lowercase SHA-256 of canonical JSON for the complete
`AdmittedExternalMember.v1` objects sorted by `input_id`. Singleton BEXTs use
the same schema with the corresponding one-element `member_ids` array and
digest. No caller-supplied order field is permitted.

### Exact provisional identities

For each working point, the projection is exactly:

```yaml
batch_working_state_schema: ExternalArbitrationWorkingState.v1
batch_pre_state_hash: H0
provisional_current_causal_state: derived_complete_current_state
provisional_future_causal_state: byte_identical_R0_future_state
```

`P0` uses owner `null`; `PA` uses owner `domain_A`; singleton `PB` uses owner
`domain_B`. The only identity representation is the tagged
`ExternalBatchWorkingStateIdentity.v1` object defined below. The two angle-
bracket clauses above are exact derivation rules, not extensible fields.

### Exact R1 and controls

Primary R1 is the complete R0 envelope with only these exact changes:

```yaml
current_causal_state.shared_slot.allocation_owner: domain_A
future_causal_state.canonical_clock: t0/30
causal_provenance.adjudicated_external_input_ids:
  - physical_allocate_shared_slot_A_0001
  - physical_allocate_shared_slot_B_0001
causal_provenance.adjudicated_physical_event_ids:
  - domain_A_allocation_event_0001
  - domain_B_allocation_event_0001
causal_provenance.canonical_ancestry:
  parent_record_hash: H0
  boundary_derivation: external_arbitration_batch
causal_provenance.authoritative_causal_ledger:
  - kind: external_arbitration_batch
    simulation_version: 0.7.0-draft.57
    decision_time: t0/30
    external_phase: 10
    batch_pre_state_hash: H0
    boundary: primary_BEXT
    members: [QA_member_result, QB_member_result]
```

The exact member-result schema is the exhaustive field list defined under
“One canonical successor and one ledger representation.” QA instantiates it
with sequence `0`, P0→PA, gate observation `null == null` true, its one
authorized proposed effect, provisional outcome
`mutation_applied_to_working_state`, adjudication `mutation_committed`, both
replay identities `adjudicated_by_atomic_batch`, and resource disposition
`shared_slot_allocated_to_domain_A`. QB instantiates it with sequence `1`,
PA→PA, gate observation `domain_A == null` false, its one authorized proposed
effect, provisional outcome `ordinary_gate_failed`, adjudication `failed_gate`,
both replay identities `adjudicated_by_atomic_batch`, and resource disposition
`no_resource_acquired`.

QA-only and QB-only successors use the same envelope and ledger schemas, the
corresponding singleton fixture/BEXT/member result, owner `domain_A` or
`domain_B`, and only that input/event identity in the adjudication arrays.
They introduce no alternate resolver or field.

## Minimal authoritative fixture

R0 is exactly the envelope under “Exact R0.” It contains no autonomous
commitment or future consequential schedule. Its two consequence contracts
authorize different physical actors and allocation owners but read and write
the same ordinary `shared_slot`. Neither contract names the other domain,
input, or outcome.

## Two isolated Unreal evidence domains

Each witness uses two fresh UE 5.8 processes with physically separate proof
domains:

```text
domain_A_input/       domain_B_input/
domain_A_output/      domain_B_output/
domain_A_process.log  domain_B_process.log
```

Each process receives the same exact R0 payload bytes and detached receipt. A
separate non-authoritative process context selects which fixture surface to
materialize:

```yaml
domain_A_context:
  materialization_domain: domain_A
  interaction_opportunity: t0/30

domain_B_context:
  materialization_domain: domain_B
  interaction_opportunity: t0/30
```

The context may select representation and the permitted physical actor. It may
not select canonical order, priority, winner, mutation, or disposition. UE
does not derive canonical time; `t0/30` is a sealed fixture opportunity later
validated by canonical admission.

Each domain must emit a detached materialization receipt after independently
verifying the raw R0 bytes and materializing its own interaction surface. The
receipt is operational evidence only.

Each domain must also emit one detached evidence-emission receipt beside its
Q. The frozen receipt contract binds:

```yaml
receipt_schema: ConcurrentEvidenceEmissionReceipt.v1
process_instance_id: operational_process_instance_id
materialization_domain: domain_A | domain_B
accepted_canonical_hash: H0
accepted_raw_payload_sha256: D0
materialized_physical_actor_id: arbitration_surface_A_01 | arbitration_surface_B_01
emitted_input_id: physical_allocate_shared_slot_A_0001 | physical_allocate_shared_slot_B_0001
emitted_physical_event_id: domain_A_allocation_event_0001 | domain_B_allocation_event_0001
emitted_q_canonical_hash: HQ(X)
emitted_q_raw_sha256: DQ(X)
```

The harness and canonical admission cross-check the materialization receipt,
emission receipt, exact Q bytes, domain contract, H0, and D0. The source audit
must prove each domain's proposal capability is constructed only for its own
preauthorized actor, input ID, event ID, and consequence contract. Merely
seeing both contracts in R0 grants neither process authority to emit the
other's Q.

Both source acceptance receipts and both materialization audits must exist
before either physical interaction is permitted. This overlap barrier proves
that both source PIDs are alive concurrently. Operational witness control
then permits A-first or B-first interaction without turning that order into
canonical time or priority.

No domain may read or write the other's input directory, output directory,
receipt, process log, Q, or process context. Neither may see BEXT, canonical
member order, working state, winner identity, R1, or a branch selector. A
visible-input and writable-output audit is required for each process.

The frozen launch contract must give each UE process a distinct writable
runtime root for proof inputs/outputs, `Saved`, config, session, log, and temp
state. Shared engine/project assets may be mounted read-only; shared caches may
not carry proof truth and must be excluded or mounted read-only. The evidence
may claim only paths proven absent from process arguments, environment,
visible-input inventories, and runtime-consumption audit; it may not infer OS
inaccessibility from directory naming alone.

Both source processes must be terminated and their proof-output artifacts
closed before sealed-fixture candidate-set validation or canonical arbitration.
No live UE process participates in BEXT construction or resolution.

## QA and QB evidence contracts

Both Q envelopes are non-authoritative and independently valid against R0.
Their exact frozen schemas will inherit the sealed distinction between digest
integrity and exact consequence authorization.

Their semantic contracts are:

```yaml
QA:
  input_id: physical_allocate_shared_slot_A_0001
  physical_event_id: domain_A_allocation_event_0001
  source_domain: domain_A
  source_record_hash: H0
  source_raw_payload_sha256: D0
  occurrence_time: t0/30
  physical_actor_id: arbitration_surface_A_01
  observed_outcome: allocation_requested
  proposed_effect:
    shared_slot.allocation_owner: domain_A

QB:
  input_id: physical_allocate_shared_slot_B_0001
  physical_event_id: domain_B_allocation_event_0001
  source_domain: domain_B
  source_record_hash: H0
  source_raw_payload_sha256: D0
  occurrence_time: t0/30
  physical_actor_id: arbitration_surface_B_01
  observed_outcome: allocation_requested
  proposed_effect:
    shared_slot.allocation_owner: domain_B
```

Each digest is computed over an exact non-self-referential projection with the
digest field absent. Recomputed integrity cannot authorize a redirected actor,
target, owner, source domain, outcome, or mutation set.

Neither Q may carry `external_phase`, canonical priority, member position,
winner identity, or any other canonical ordering instruction.

`D0` is the detached raw-byte SHA-256 of the exact stored R0 payload, inherited
from the sealed Unreal lifecycle boundary. Admission binds both H0 and D0.
`physical_event_id` is distinct from `input_id`; both are digest-covered and
preauthorized per domain. This lets the rejection suite distinguish duplicate
input identity from replay of the same physical event under another input ID.
Domain A cannot emit QB, and domain B cannot emit QA, merely by recomputing a
digest.

## Side-effect-free admission

Admission evaluates each Q independently against the exact immutable R0:

```text
validate envelope shape and canonical serialization
validate evidence digest
validate exact source-domain / actor / target / outcome / mutation contract
validate source_record_hash == H0
validate source_raw_payload_sha256 == D0
validate occurrence_time under the supplied fixture opportunity
validate input identity not already adjudicated
validate physical_event_id not already adjudicated
observe ordinary R0 gate shared_slot.allocation_owner == null
        ↓
return admitted candidate or diagnostic rejection
```

Admission may not mutate R0, append canonical provenance, reserve the shared
slot, or decide member order. Malformed admission
witnesses terminate at this boundary; they do not introduce retry or
continuation semantics.

“Valid against R0” therefore means both contract-valid and presently eligible:
each member observes the slot owner as `null` during side-effect-free
admission. That observation grants no reservation and is not cached as
execution authority. The same ordinary gate is evaluated again against the
provisional working state when the batch executes.

The primary witness requires both exact candidates to pass admission. The
QA-only and QB-only controls construct lawful one-member batches from their
single admitted candidates.

Malformed-one witnesses are terminal admission tests: the malformed candidate
gets no membership, R0 remains byte-identical, and the valid peer is not
continued into a singleton batch in that witness. General member filtering,
continuation, retry, and partial-set execution remain outside scope.

The following terms are distinct and normative:

```text
admitted
  = passed side-effect-free validation and received an R0-bound member
    capability; no canonical mutation or replay disposition yet exists

adjudicated
  = represented in the singular successfully published R1 after all BEXT
    members were provisionally evaluated; only then do the input and
    physical-event identities enter canonical replay protection

mutation_committed
  = the admitted member's ordinary gate passed and its permitted mutation
    entered the singular published atomic successor

failed_gate
  = the admitted member's ordinary working-state gate failed; no mutation or
    resource was acquired, but successful batch publication still adjudicated
    the member
```

`failed_gate` is neither pre-admission evidence rejection nor a structural
batch failure. The specification does not call QB an accepted consequence.
It records that QB was admitted, adjudicated, and terminally resolved through
its unchanged ordinary gate.

## Sealed fixture candidate-set input

Candidate-set completeness is a sealed proof-fixture input, not an observed or
inferred runtime condition. The primary fixture supplies this exact object:

```yaml
fixture_candidate_set_schema: ConcurrentExternalCandidateSetFixture.v1
fixture_id: concurrent-external-evidence-arbitration-primary-v1
source_record_hash: H0
required_input_id_set:
  - physical_allocate_shared_slot_A_0001
  - physical_allocate_shared_slot_B_0001
required_physical_event_id_set:
  - domain_A_allocation_event_0001
  - domain_B_allocation_event_0001
```

The arrays are canonical sorted encodings of mathematical sets. Their stored
position cannot become member execution order. The fixture object is a frozen
test input outside canonical city state and outside UE. It declares what the
bounded witness must already contain; it does not tell a runtime when to
stop listening for inputs.

After both already-captured Q artifacts exist and both have independently
passed admission, the harness supplies a duplicate-preserving,
non-authoritative presentation sequence and the sealed fixture object to:

```text
construct_BEXT_from_sealed_fixture_set(
  R0,
  ConcurrentExternalCandidateSetFixture.v1,
  [admitted_QA, admitted_QB]  # presentation sequence; reversible in W3/W4
)
        ↓
reject duplicate input_id or physical_event_id before normalization
        ↓
normalize to input_id-keyed map
        ↓
validate exact set equality and source binding
        ↓
BEXT construction
```

Every W1–W4 witness uses the same sealed fixture object and exact admitted
set. Physical and harness presentation traces may differ; fixture
membership may not. The QA-only and QB-only controls use separately sealed
singleton fixture objects. Missing, extra, or substituted members invalidate
that witness before BEXT construction. Late arrival, packet transport,
collection-window policy, timeout, dynamically joining members, and the means
by which production code would determine completeness are not claimed.

## BEXT: record-bound batch capability

Each successful admission returns the immutable member capability frozen in
the exact contract above. This field projection uses `X` from the domain table:

```yaml
admitted_member_schema: AdmittedExternalMember.v1
input_id: X.input_id
physical_event_id: X.physical_event_id
source_record_hash: H0
source_raw_payload_sha256: D0
q_canonical_hash: HQ(X)
q_raw_sha256: DQ(X)
evidence_digest: evidence_digest(X)
occurrence_time: t0/30
derived_external_phase: 10
derived_canonical_external_priority: 100
immutable_admission_observations: exact_nine_entry_admission_list
```

This is a side-effect-free record-bound capability, not canonical city state.
The resolver must re-verify every exact Q object and raw-byte identity against
its admitted-member capability, BEXT, H0, and D0 before any working mutation.

Successful batch construction returns one frozen record-bound capability:

```yaml
kind: external_arbitration_batch
source_record_hash: H0
batch_pre_state_hash: H0
decision_time: t0/30
external_phase: 10
ordering_law: ConcurrentExternalMemberOrder.v1
member_set_digest: member_set_digest
member_ids:
  - physical_allocate_shared_slot_A_0001
  - physical_allocate_shared_slot_B_0001
```

`member_set_digest` is computed over the complete
`AdmittedExternalMember.v1` objects after sorting by `input_id`. It binds BEXT
to the exact Q objects, raw bytes, source identities, derived ordering values,
and sealed fixture member set without inheriting harness presentation order.

Duplicate input IDs, duplicate physical-event IDs, a member-set digest
mismatch, or any member not admitted against the exact BEXT source record
rejects batch construction without canonical mutation.

BEXT is invalid against every record except R0. It cannot be retained as
authority after R1 exists.

The fixture and caller never supply `member_ids` in execution order. Batch
preconstruction rejects duplicate input or event identities before any map
conversion can overwrite them. Batch construction then receives a member map
keyed by `input_id`, validates exact set equality against the sealed fixture,
derives the canonical key for every map value, and generates BEXT's ordered
`member_ids` vector internally. The resolver receives only
`(R0, BEXT, admitted_member_map)` and looks up members by the already-derived
BEXT vector. It must not enumerate the map to derive order and must assert the
map key set equals BEXT before its first lookup. It receives no
caller-positioned member container.

## Frozen canonical member-ordering law

The following `ConcurrentExternalMemberOrder.v1` key is frozen:

```text
external_member_key = (
  occurrence_time,
  external_phase,
  canonical_external_priority,
  input_id
)
```

The key components, types, and comparisons frozen for this fixture are:

```yaml
occurrence_time:
  type: fixture_literal_time_token
  comparison: exact_equality_then_no_further_time_order_needed
  value: t0/30
external_phase:
  type: unsigned_integer
  comparison: numeric_ascending
  value: 10
canonical_external_priority:
  type: unsigned_integer
  comparison: numeric_ascending
  value: 100
input_id:
  type: fixture_ascii_identifier
  comparison: bytewise_ascii_ascending
```

Those first three values are identical for QA and QB. `external_phase` and
`canonical_external_priority` are derived by the canonical admission contract;
they are absent from Q and cannot be supplied by UE or the harness. The final
tie-break is ASCII lexicographic `input_id`, so QA precedes QB.

The equal fixture priority proves stable arbitration without selecting a
production precedence policy among future input classes. Such a policy remains
outside this proof.

The preconstruction harness accepts candidate containers in any positional
order, treats that position as a non-authoritative trace, and normalizes them
into the exact member map before BEXT construction. An explicit
`member_order`, priority, winner, or authority-bearing order argument/field
supplied by a caller rejects. W3 and W4 therefore lawfully reverse presentation
while producing the same member map and BEXT. Any occurrence time, phase, or
priority that differs from the exact frozen fixture constants also rejects.

This key is new external-arbitration law. It is not inherited implicitly from
autonomous commitment ordering and is frozen only for this fixture.

## Sequential revalidation inside one atomic transaction

The resolver receives only `(R0, BEXT, admitted_member_map)`. It may not
receive physical emission order, filesystem metadata, harness presentation
order, process IDs, UE frames, timestamps, or local traces.

It creates provisional working state from R0 and evaluates the complete
canonical member order:

```text
QA
  evidence_source_record_hash = H0
  working pre-state identity = P0 derived from R0
  gate shared_slot.allocation_owner == null → true
  provisional mutation allocates domain_A
  provisional_evaluation_outcome = mutation_applied_to_working_state

QB
  evidence_source_record_hash = H0
  working pre-state identity = PA
  gate shared_slot.allocation_owner == null → false
  no mutation
  provisional_evaluation_outcome = ordinary_gate_failed
  resource disposition = no resource acquired
```

An ordinary failed gate is a valid provisional member result and does not roll
back a previous lawful working-state mutation. A structural resolver failure,
schema violation, undeclared mutation, exception, or attempt to escape a
partial successor aborts
the entire batch: no R1, canonical ledger entry, ancestry, adjudicated-input
identity, or partial city mutation may escape.

## Self-hash-safe, type-disjoint working-state identity

The batch must distinguish canonical authority from provisional working-state
identity. One domain-separated working-hash scheme is used for every member:

```yaml
batch_authority:
  batch_pre_state_hash: H0

member_QA:
  evidence_source_record_hash: H0
  working_pre_state_identity: P0
  working_post_state_identity: PA

member_QB:
  evidence_source_record_hash: H0
  working_pre_state_identity: PA
  working_post_state_identity: PA
```

`H0` is the canonical hash of R0. `P0` and `PA` are indivisible tagged objects,
not strings and not canonical record hashes:

```yaml
identity_schema: ExternalBatchWorkingStateIdentity.v1
identity_kind: provisional_external_batch_working_state
digest_algorithm: sha256
digest_domain: THE_CITY_EXTERNAL_ARBITRATION_WORKING_STATE_V1
digest: working_projection_digest
```

They are domain-separated identities of the exact mutation-state projection
below, evaluated before and after QA respectively. The projection deliberately
excludes admission/anti-reacquisition identities, provenance, member results,
and failure dispositions; those are written only when the atomic batch closes.
Consequently a failed member that performs no mutation leaves the provisional
working-state identity unchanged.

```yaml
batch_working_state_schema: ExternalArbitrationWorkingState.v1
batch_pre_state_hash: H0
provisional_current_causal_state: derived_complete_current_state
provisional_future_causal_state: byte_identical_R0_future_state
```

```text
P0 = working_state_identity(projection of R0 before QA)
PA = working_state_identity(projection after QA allocation)

working_state_identity(projection) = ExternalBatchWorkingStateIdentity.v1 {
  digest = lowercase hexadecimal SHA-256(
    UTF-8("THE_CITY_EXTERNAL_ARBITRATION_WORKING_STATE_V1\n")
    + canonical_json(projection)
  )
}
```

The projection excludes its own digest, final ledger state, and successor ancestry.
It has no materialization or scheduler authority. The tagged object is the
only lawful representation of a provisional identity. A bare canonical hash
cannot satisfy a working-identity field. The tagged object—or its extracted
digest—must reject wherever a canonical `source_record_hash`,
`batch_pre_state_hash`, ancestry parent, scheduler/admission capability,
materialization input, or successor identity is required. Those canonical
references must independently equal the recomputed hash of an actual complete
canonical record. Storing a tagged working identity inside the final canonical
ledger records provisional provenance; it does not promote the provisional
state to canonical authority. The exact frozen derivation above is exhaustive.

## One canonical successor and one ledger representation

After every admitted member has produced a lawful provisional evaluation
outcome, the resolver constructs one complete candidate R1 inside its private
transaction buffer:

```yaml
R1:
  canonical_clock: t0/30
  shared_slot:
    allocation_owner: domain_A
  adjudicated_external_input_ids:
    - physical_allocate_shared_slot_A_0001
    - physical_allocate_shared_slot_B_0001
  adjudicated_physical_event_ids:
    - domain_A_allocation_event_0001
    - domain_B_allocation_event_0001
  canonical_ancestry:
    parent_record_hash: H0
    boundary_derivation: external_arbitration_batch
  authoritative_causal_ledger:
    - kind: external_arbitration_batch
      batch_pre_state_hash: H0
      boundary: BEXT
      members: [QA_result, QB_result]
```

The batch has one canonical ledger entry containing an ordered member list. A
member is not a hidden sub-transaction and has no separate successor ancestry.
Both member IDs enter `adjudicated_external_input_ids`, and both event IDs enter
`adjudicated_physical_event_ids`, only at singular batch publication. That
publication makes both members adjudicated even though only QA's mutation
commits. These are the canonical replay barriers that prevent failed-gate
QB—or the same physical event wrapped
in a different input ID—from reacquiring authority. If the batch structurally
aborts, neither member becomes adjudicated and neither replay barrier may
escape.

Both canonical replay-protection arrays are ordered by canonical member
sequence. Presentation-sequence order, fixture-array position, and map
iteration order cannot affect their serialized order.

Each member result uses the exhaustive schema and exact QA/QB instantiations
frozen above:

```yaml
input_id: X.input_id
physical_event_id: X.physical_event_id
source_domain: X.source_domain
canonical_member_sequence: 0 | 1
evidence_digest: evidence_digest(X)
evidence_source_record_hash: H0
evidence_source_raw_payload_sha256: D0
canonical_member_key: [t0/30, 10, 100, X.input_id]
immutable_admission_observations: exact_nine_entry_admission_list
admission_disposition: admitted_against_batch_pre_state
batch_membership_disposition: included_in_bext
working_pre_state_identity: ExternalBatchWorkingStateIdentity.v1
working_post_state_identity: ExternalBatchWorkingStateIdentity.v1
working_state_gate_observations: exact_X_gate_observation
authorized_mutations: [Q(X).proposed_effect]
provisional_evaluation_outcome: mutation_applied_to_working_state | ordinary_gate_failed
adjudication_disposition: mutation_committed | failed_gate
replay_disposition:
  input_id: adjudicated_by_atomic_batch
  physical_event_id: adjudicated_by_atomic_batch
resource_disposition: shared_slot_allocated_to_domain_A | shared_slot_allocated_to_domain_B | no_resource_acquired
```

The exact primary gate observations are:

```yaml
QA:
  - path: current_causal_state.shared_slot.allocation_owner
    observed_value: null
    required_value: null
    result: true
QB:
  - path: current_causal_state.shared_slot.allocation_owner
    observed_value: domain_A
    required_value: null
    result: false
```

The QB-only control observes `null`, requires `null`, returns `true`, and uses
`shared_slot_allocated_to_domain_B`. The QA-only control uses the exact QA
observation and `shared_slot_allocated_to_domain_A`.

The prospective member ledger can contain these values in the private candidate
R1 buffer, but `adjudication_disposition` and `replay_disposition` acquire
canonical meaning only at singular R1 publication. `replay_disposition`
describes the canonical anti-reacquisition result of successful batch closure.
It does not define transport consumption, retry, re-admission,
or malformed-input continuation. A later admission attempt carrying either
adjudicated input ID or either adjudicated physical-event ID rejects before a
new batch capability is constructed.

The complete R1 is hashed externally only after construction. No R1 field or
ledger member stores R1's own hash.

## Atomic closure and publication

Every provisional mutation, member observation, member disposition, replay
barrier, ledger object, ancestry field, and candidate R1 remains inside one
transaction-local buffer until closure. There is one publication point:

```text
all BEXT members provisionally evaluated in canonical order
        ↓
complete ledger + replay barriers + ancestry assembled
        ↓
complete candidate R1 schema and contract validated
        ↓
exactly one canonical R1 returned/written/published
        ↓
member adjudication dispositions and replay barriers become canonical
```

Before that final step, no QA success artifact, QB failed-gate artifact,
resource disposition, replay-barrier update, member ledger fragment,
provisional-state object, provisional identity, successor ancestry, candidate
R1, or canonical hash may escape through a canonical API or canonical output
path. Fault diagnostics may survive only in a separately named
non-authoritative test-evidence domain and must be rejected by every canonical,
deterministic-regeneration, scheduling, admission, and materialization
interface.

Atomicity here means one in-process canonical publication boundary. It does not
claim durable-storage crash consistency. An ordinary `failed_gate` member is a
lawful adjudication result inside a successfully published batch; it is not a
partial transaction failure.

A structural abort after either gate evaluation means no member was
canonically adjudicated, no working-state mutation became canonical, and no
input or physical-event replay barrier became canonical.

## Required physical and presentation witnesses

All four primary witnesses start from byte-identical R0 and use byte-identical
QA and QB evidence envelopes:

| Witness | Operational physical emission | Harness presentation |
| --- | --- | --- |
| W1 | QA then QB | QA then QB |
| W2 | QB then QA | QA then QB |
| W3 | QA then QB | QB then QA |
| W4 | QB then QA | QB then QA |

Physical emission order and presentation order are non-authoritative witness
traces. Every run must produce byte-identical:

```text
R0
sealed fixture set + normalized admitted-member map
member-set digest
BEXT
canonical member order
member gate observations
P0 / PA
R1
authoritative batch ledger
successor ancestry
terminal resource dispositions
```

Process IDs, physical timing traces, directory paths, and presentation traces
may differ and remain outside canonical authority. No return UE process is
required; fresh repromotion is already sealed by the predecessor and is not
another variable in this arbitration proof.

## Required counterfactuals

```text
QA only
→ ordinary shared-slot gate passes
→ domain_A receives the slot

QB only
→ ordinary shared-slot gate passes
→ domain_B receives the slot

QA + QB
→ frozen canonical key orders QA before QB
→ QA passes and provisionally allocates the slot
→ QB reads the changed ordinary slot fact and fails
```

The definitions and Q bytes used in the primary are identical to their
single-member controls. No conflict callback, peer reference, winner rule, or
`if QA then fail QB` branch is permitted.

## Required failure witnesses

### Pre-admission diagnostic rejection

- malformed Q;
- digest-covered field changed without digest recomputation;
- redirected actor, target, source domain, owner, outcome, or mutation with a
  recomputed valid digest;
- Q bound to a different source record.

Each test terminates at side-effect-free admission. R0, ledger, schedule, and
future eligibility remain byte-identical.

Separate isolated anti-reacquisition probes use completed R1 as the current
record and present an already-adjudicated input/event identity. Admission must
report the exact `input_id already adjudicated` and/or `physical_event_id
already adjudicated` gate observation and construct no member capability.
A stale source binding or other failing gate may also be reported, but cannot
substitute for the replay-protection observation. Each probe ends immediately
with R1 byte-identical; it defines no retry, re-admission, continuation,
or transport-consumption behavior.

### Batch-construction rejection

- duplicate input ID;
- duplicate physical-event identity under a different input ID;
- member-set digest mismatch;
- member not admitted against R0;
- harness-supplied member order treated as authority; and
- UE-supplied external phase, priority, or winner field.

No BEXT or canonical mutation may escape.

### Atomic resolver rejection

- BEXT source hash differs from R0;
- BEXT candidate set differs from its bound set digest;
- primary witness member map differs from its sealed fixture set;
- member mutation exceeds its admitted consequence contract;
- filesystem timestamp, process schedule, or presentation order reaches
  canonical ordering;
- a member attempts to create its own canonical successor or ancestry;
- any provisional working state is exposed as a canonical record;
- a tagged provisional identity or its extracted digest is supplied as a
  canonical source, parent, ancestry, scheduler, admission, materialization, or
  successor identity;
- a bare canonical hash is supplied where a tagged provisional identity is
  required;
- a partial member-execution exception occurs; and
- promotion, materialization, or UE code reaches canonical ordering, mutation,
  disposition, ledger, or policy selection.

A structural failure aborts the in-process transaction with no returned or
written R1. Durable storage crash consistency is not claimed because general
save/persistence is prohibited. QA's lawful provisional mutation followed by
QB's ordinary failed gate is not a structural failure; singular publication
makes QA `mutation_committed`, QB `failed_gate`, and closes the specified
atomic R1.

The atomicity harness must inject deterministic faults at each of these exact
points and prove R0 remains byte-identical with no R1 or canonical artifact:

```text
after QA provisional mutation
after QB ordinary gate evaluation
during replay-barrier construction
during batch-ledger construction
after complete provisional R1 construction but before validation
after complete R1 validation but before its singular return/write
```

The order-isolation harness must also poison file mtimes, reverse directory
enumeration, reverse candidate-container order, and vary process/presentation
traces while holding the sealed fixture and admitted-member map constant. BEXT,
canonical order, provisional identities, and R1 must remain byte-identical.
Source audit must trace actual resolver dataflow; string search alone is
insufficient.

## Source and authority audit

The proof fails even if outputs coincide when source inspection finds:

```text
two canonical external resolvers
policy-specific or witness-specific result branches
UE-selected order or priority
harness list order reaching the resolver
fixture set array position reaching canonical member order
filesystem metadata reaching the resolver
runtime timeout, polling completion, directory quietness, or live arrival
deciding fixture completeness
cross-domain readable or writable proof state
QA naming QB or QB naming QA
pair-specific conflict handling
member-owned canonical commit or ancestry
partial-success record publication
provisional identity accepted by a canonical identity interface
```

There must be one declared canonical external-batch resolution path for this
simulation identity and boundary.

## Contract-level red-team gates

The specification is not freeze-worthy unless each of these attacks has one
unambiguous disposition at the contract level:

| Attack surface | Required contract result |
| --- | --- |
| Atomicity | Every member effect and disposition remains provisional until one validated R1 publication point; structural failure publishes no canonical fragment or replay barrier. |
| Replay identity | Admission, adjudication, mutation result, and replay protection are separate; both successfully adjudicated member/event identities become barriers only when the batch closes, including a lawful `failed_gate` member. |
| Hidden ordering authority | Fixture array position, candidate container order, emission order, mtimes, enumeration, process timing, and caller fields cannot reach the resolver; BEXT alone generates its member vector from the frozen key. |
| Provisional-state authority leakage | `ExternalBatchWorkingStateIdentity.v1` is a type-disjoint tagged object and rejects in every canonical-record identity position; its ledger presence is provenance, not capability. |
| Accidental live-transport semantics | Exact candidate-set membership is supplied by `ConcurrentExternalCandidateSetFixture.v1`; no timeout, listener, polling state, packet arrival, or runtime closure decision is specified or demonstrated. |

The red-team oracle must additionally verify that changing any prohibited input
cannot alter BEXT or R1, and that attempting to route any such input into a
canonical interface fails at its declared pre-publication boundary. Passing
output coincidence without the required dataflow isolation is insufficient.

## Acceptance gates

The proof froze only after the exact identity, payload, R0, R1, QA, QB, digest
projections, receipt schemas, BEXT schema, ordering key, working-state
projection, member provenance, serialization, and failure dispositions became
exhaustive in this record.

Implementation may later pass only if:

1. two fresh isolated Unreal domains independently verify and materialize the
   same R0 and physically emit exact QA and QB;
2. each Q is admitted side-effect-free against immutable R0 with integrity and
   consequence authorization validated separately;
3. one R0-bound BEXT binds the exact admitted member set;
4. canonical member order is independent of every physical and presentation
   permutation in W1–W4;
5. QA passes the ordinary shared-slot gate and changes P0 to PA provisionally;
6. QB remains R0-authorized inside BEXT, reads PA, fails the unchanged ordinary
   gate, and acquires no resource;
7. exactly one atomic R1 with singular H0 ancestry and one ordered batch ledger
   entry is emitted;
8. QA-only and QB-only controls each succeed with identical member definitions;
9. duplicate, stale, redirected, caller-ordered, local-authority, and partial
   execution attempts fail at their declared boundary;
10. each witness regenerates byte-identical canonical
    artifacts; and
11. source audit proves zero cross-domain, arrival-order, pair-specific, or
    member-owned canonical authority.

## DAG plan

```text
freeze identity + exact record/Q/BEXT schemas
        │
        ├───────────────┬──────────────────┐
        ▼               ▼                  ▼
canonical batch      two isolated UE    source/authority
resolver             evidence domains   audit
        │               │                  │
        └───────────────┴──────────┬───────┘
                                   ▼
                         W1–W4 + controls
                                   │
                                   ▼
          fresh regeneration + atomicity + provenance oracle
                                   │
                                   ▼
                    evidence + self-excluding manifest
```

## Explicit non-claims

This proof does not prove or authorize:

- split crews, player identities, or 2+2 topology;
- networking, sockets, packet order, latency, trust, or host arbitration;
- player movement, travel, proximity, World Partition, or streaming;
- multiple promoted return worlds or shared save ownership;
- retry, re-admission, malformed-input continuation, or late evidence;
- autonomous work in the same batch;
- same-clock successor creation;
- more than two evidence inputs or more than one shared fact;
- randomness;
- generalized external priority policy;
- production-scale concurrency, persistence, or city simulation.

No successor gameplay or city scope follows from this proof.

## Changelog

### 0.1.0 — 2026-08-27

- Froze `ConcurrentExternalEvidenceArbitrationPayload.v1` under simulation
  identity `0.7.0-draft.57` after the draft.1 contract-level red-team passed.
- Froze exact R0, Q, receipt, admitted-member, sealed-fixture, BEXT,
  provisional-identity, R1, control, serialization, ordering, publication, and
  failure contracts.
- Authorized only the exact two-source, one-R0, one-sealed-fixture,
  one-external-batch implementation DAG, W1–W4, singleton controls, declared
  failure suite, source audit, evidence, and self-excluding release manifest.
- Kept live collection, networking, 2+2 topology, movement, streaming,
  autonomous members, retry, randomness, additional input classes, generalized
  arbitration, and all adjacent architecture closed.

### 0.1.0-draft.1 — 2026-08-27

- Distinguished side-effect-free admission, provisional member evaluation,
  singular-publication adjudication, committed mutation, ordinary
  `failed_gate`, and input/event anti-reacquisition dispositions.
- Replaced canonical-looking provisional hashes with the type-disjoint
  `ExternalBatchWorkingStateIdentity.v1` object and required rejection of both
  that object and its extracted digest from every canonical identity interface.
- Classified candidate-set completeness as exact sealed fixture input, moved
  duplicate rejection ahead of map normalization, and prohibited any inference
  of live collection, timeout, polling, or transport semantics.
- Froze one transaction-local publication point, eliminated hidden positional
  ordering paths, and recorded a contract-level red-team pass over atomicity,
  anti-reacquisition identity, ordering authority, provisional-state leakage,
  and live-transport ambiguity.
- Advanced only to freeze review. Authorized no resolver, Unreal, transport,
  2+2 topology, or adjacent implementation work.

### 0.1.0-draft.0 — 2026-08-27

- Opened a specification-only proof for two independently materialized R0-bound
  evidence sources entering one atomic canonical external batch.
- Proposed explicit external-member ordering, self-hash-safe provisional
  working-state identity, W1–W4 order-independence witnesses, QA/QB controls,
  batch-level atomicity, and two-domain Unreal isolation.
- Authorized no implementation or adjacent 2+2, network, movement, streaming,
  retry, random, or city-scale work.
