# Concurrent External Evidence Arbitration Proof

**Version:** 0.1.0-draft.0
**Status:** Candidate specification under review. Implementation is not authorized.
**Selected:** 2026-08-27
**Parent continuation:** [Co-op Open-City FPS Simulation — v0.7 Working Continuation](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)
**Sealed predecessors:** [External Input Boundary Proof — v0.1.1](External%20Input%20Boundary%20Proof%20Evidence%20-%20v0.1.1.md); [Shared-State Commitment Interference Proof — v0.1.0](Shared-State%20Commitment%20Interference%20Proof%20Evidence%20-%20v0.1.0.md); [Record-Relative Chronological Resolution Proof — v0.1.0](Record-Relative%20Chronological%20Resolution%20Proof%20Evidence%20-%20v0.1.0.md); [Integrated Unreal Promotion-Unload-Repromotion Proof — v0.1.0](Integrated%20Unreal%20Promotion-Unload-Repromotion%20Proof%20Evidence%20-%20v0.1.0.md)
**Candidate simulation identity:** `0.7.0-draft.56`; not frozen.

## Question

> **Can two independently evidenced external inputs, both validly bound to the
> same canonical R0, be admitted side-effect-free into one canonical external
> arbitration batch whose frozen ordering and working-state revalidation
> produce one deterministic successor history independent of physical,
> filesystem, or closed-set harness-presentation order?**

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

## Candidate proof boundary

```yaml
next_working_unit:
  name: Concurrent External Evidence Arbitration Proof
  version: 0.1.0-draft.0
  status: specification_only

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
> directory enumeration, closed-set harness presentation, OS timestamps, and
> thread scheduling have no canonical ordering authority.**

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

Neither member creates a canonical successor. `HWA`, the state after QA and
before QB, is provisional batch state only. It is not R1, is never exposed as
city truth, cannot be materialized, and cannot authorize later work.

QB is not re-admitted against R1. No R1 exists until the complete batch closes.

## Candidate identity

The following identity is proposed for freeze review:

```yaml
record_schema: CanonicalResolutionEnvelope.v1
payload_schema: ConcurrentExternalEvidenceArbitrationPayload.v1
scenario_id: concurrent-external-evidence-arbitration-v1
scenario_version: 0.1.0
simulation_version: 0.7.0-draft.56
seed: concurrent-external-evidence-arbitration-v1/0001
```

The exact payload schema, Q schemas, batch capability, ledger object, receipts,
and canonical serialization must be frozen before implementation. A new
authoritative field after freeze requires a new payload schema and simulation
identity.

The predecessor canonical-JSON law remains the candidate serializer: sorted
object keys, compact separators, `ensure_ascii = true`, no duplicate keys or
non-finite numbers, declared array order preserved, and lowercase SHA-256.
Stored artifacts have one terminal LF; hashed JSON values do not.

No canonical record or ledger entry may contain its own successor hash.

## Minimal authoritative fixture

R0 contains no autonomous commitment or future consequential schedule. It
contains only the identity above, one available shared slot, the two exact
permitted external-consequence contracts, replay protection state, and genesis
provenance.

```yaml
current_causal_state:
  shared_slot:
    allocation_owner: null
  external_consequence_contracts:
    domain_A:
      physical_actor_id: arbitration_surface_A_01
      permitted_input_id: physical_allocate_shared_slot_A_0001
      permitted_owner: domain_A
    domain_B:
      physical_actor_id: arbitration_surface_B_01
      permitted_input_id: physical_allocate_shared_slot_B_0001
      permitted_owner: domain_B
future_causal_state:
  canonical_clock: t0/00
  unresolved_work: []

causal_provenance:
  accepted_external_inputs: []
  adjudicated_physical_event_ids: []
  authoritative_causal_ledger: []
  canonical_ancestry: null
  fixture_genesis:
    source: frozen_initial_fixture
```

The two consequence contracts authorize different physical actors and
different allocation owners but read and write the same ordinary
`shared_slot`. Neither contract names the other domain, input, or outcome.

The final frozen specification must replace this semantic R0 with one exact,
exhaustive JSON record shape.

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
Q. The candidate receipt contract binds:

```yaml
receipt_schema: ConcurrentEvidenceEmissionReceipt.v1
process_instance_id: <domain-specific operational identity>
materialization_domain: domain_A | domain_B
accepted_canonical_hash: H0
accepted_raw_payload_sha256: D0
materialized_physical_actor_id: arbitration_surface_A_01 | arbitration_surface_B_01
emitted_input_id: physical_allocate_shared_slot_A_0001 | physical_allocate_shared_slot_B_0001
emitted_physical_event_id: domain_A_allocation_event_0001 | domain_B_allocation_event_0001
emitted_q_canonical_hash: <hash of exact Q JSON>
emitted_q_raw_sha256: <hash of exact stored Q bytes>
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
closed before side-effect-free candidate-set closure or canonical arbitration.
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
validate input identity not already accepted
validate physical_event_id not already adjudicated
observe ordinary R0 gate shared_slot.allocation_owner == null
        ↓
return admitted candidate or diagnostic rejection
```

Admission may not mutate R0, append canonical provenance, consume an input
cursor, reserve the shared slot, or decide member order. Malformed admission
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

## Closed candidate-set boundary

This proof does not define a network collection window or decide when future
inputs have finished arriving. After both already-captured Q artifacts exist,
the harness presents an unordered candidate multiset to a side-effect-free
closure operation:

```text
close_external_candidate_set(R0, {QA, QB})
        ↓
sealed admitted member set
        ↓
BEXT construction
```

Every W1–W4 witness closes the same complete multiset. Physical and harness
presentation traces may differ; the sealed set may not. Late arrival, packet
transport, collection-window policy, and dynamically joining members are not
claimed.

## BEXT: record-bound batch capability

Each successful admission returns an immutable member capability with this
candidate shape:

```yaml
admitted_member_schema: AdmittedExternalMember.v1
input_id: ...
physical_event_id: ...
source_record_hash: H0
source_raw_payload_sha256: D0
q_canonical_hash: <hash of complete Q JSON>
q_raw_sha256: <hash of exact stored Q bytes>
evidence_digest: ...
occurrence_time: t0/30
derived_external_phase: 10
derived_canonical_external_priority: 100
immutable_admission_observations: [...]
```

This is a side-effect-free record-bound capability, not canonical city state.
The resolver must re-verify every exact Q object and raw-byte identity against
its admitted-member capability, BEXT, H0, and D0 before any working mutation.

Successful batch construction returns one record-bound capability, proposed as:

```yaml
kind: external_arbitration_batch
source_record_hash: H0
batch_pre_state_hash: H0
decision_time: t0/30
external_phase: 10
ordering_law: ConcurrentExternalMemberOrder.v1
member_set_digest: <digest of canonical set projection>
member_ids:
  - physical_allocate_shared_slot_A_0001
  - physical_allocate_shared_slot_B_0001
```

`member_set_digest` is computed over the complete
`AdmittedExternalMember.v1` objects after sorting by `input_id`. It binds BEXT
to the exact Q objects, raw bytes, source identities, derived ordering values,
and closed member set without inheriting harness presentation order.

Duplicate input IDs, duplicate evidence identities, a member-set digest
mismatch, or any member not admitted against the exact BEXT source record
rejects batch construction without canonical mutation.

BEXT is invalid against every record except R0. It cannot be retained as
authority after R1 exists.

## Candidate canonical member-ordering law

The following `ConcurrentExternalMemberOrder.v1` key is proposed for freeze
review:

```text
external_member_key = (
  occurrence_time,
  external_phase,
  canonical_external_priority,
  input_id
)
```

The key components, types, and comparisons proposed for this fixture are:

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

The batch builder accepts candidate containers in any positional order, treats
that position as a non-authoritative presentation trace, canonicalizes the
closed set, and derives its complete member order. An explicit `member_order`,
priority, winner, or authority-bearing order argument/field supplied by a
caller rejects. W3 and W4 therefore lawfully reverse container presentation
while producing the same BEXT.

This key is new external-arbitration law. It is not inherited implicitly from
autonomous commitment ordering and remains an explicit freeze-review decision.

## Sequential revalidation inside one atomic transaction

The resolver receives only `(R0, BEXT, admitted_candidate_set)`. It may not
receive physical emission order, filesystem metadata, harness presentation
order, process IDs, UE frames, timestamps, or local traces.

It creates provisional working state from R0 and evaluates the complete
canonical member order:

```text
QA
  evidence_source_record_hash = H0
  working pre-state = HW0 derived from R0
  gate shared_slot.allocation_owner == null → true
  provisional mutation allocates domain_A
  result = succeeded

QB
  evidence_source_record_hash = H0
  working pre-state = HWA
  gate shared_slot.allocation_owner == null → false
  no mutation
  result = failed_gate
  resource disposition = no resource acquired
```

An ordinary failed gate is a valid member result and does not roll back a
previous successful member. A structural resolver failure, schema violation,
undeclared mutation, exception, or attempt to escape a partial successor aborts
the entire batch: no R1, canonical ledger entry, ancestry, accepted-input
identity, or partial city mutation may escape.

## Self-hash-safe working-state identity

The batch must distinguish canonical authority from provisional working-state
identity. One domain-separated working-hash scheme is used for every member:

```yaml
batch_authority:
  batch_pre_state_hash: H0

member_QA:
  evidence_source_record_hash: H0
  working_pre_state_hash: HW0
  working_pre_state_identity_kind: external_batch_working_state_hash
  working_post_state_hash: HWA
  working_post_state_identity_kind: external_batch_working_state_hash

member_QB:
  evidence_source_record_hash: H0
  working_pre_state_hash: HWA
  working_pre_state_identity_kind: external_batch_working_state_hash
  working_post_state_hash: HWA
  working_post_state_identity_kind: external_batch_working_state_hash
```

`H0` is the canonical hash of R0. `HW0` and `HWA` are not canonical record
hashes. They are domain-separated digests of the exact mutation-state
projection below, evaluated before and after QA respectively. The
projection deliberately excludes admission/replay identities, provenance,
member results, and failure dispositions; those are written only when the
atomic batch closes. Consequently a failed member that performs no mutation
leaves this working-state identity unchanged.

```yaml
batch_working_state_schema: ExternalArbitrationWorkingState.v1
batch_pre_state_hash: H0
provisional_current_causal_state: <complete current state at this working point>
provisional_future_causal_state: <complete unchanged future state>
```

```text
HW0 = working_state_hash(projection of R0 before QA)
HWA = working_state_hash(projection after QA allocation)

working_state_hash(projection) = lowercase hexadecimal SHA-256(
  UTF-8("THE_CITY_EXTERNAL_ARBITRATION_WORKING_STATE_V1\n")
  + canonical_json(projection)
)
```

The projection excludes its own digest, final ledger state, and successor ancestry.
It has no materialization or scheduler authority. The final frozen draft must
replace the placeholders above with exact exhaustive objects.

## One canonical successor and one ledger representation

After every admitted member has produced a lawful result, the resolver creates
one complete R1 atomically:

```yaml
R1:
  canonical_clock: t0/30
  shared_slot:
    allocation_owner: domain_A
  accepted_external_inputs:
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
Both member IDs enter `accepted_external_inputs`, and both event IDs enter
`adjudicated_physical_event_ids`, only at batch closure because both were
admitted and adjudicated even though only QA mutates the shared slot. These are
the canonical replay barriers that prevent losing QB—or the same physical
event wrapped in a different input ID—from reacquiring authority.

Each member result records:

```yaml
input_id: ...
source_domain: ...
canonical_member_sequence: 0 | 1
evidence_digest: ...
evidence_source_record_hash: H0
evidence_source_raw_payload_sha256: D0
canonical_member_key: [...]
immutable_admission_observations: [...]
working_pre_state_hash: ...
working_pre_state_identity_kind: ...
working_post_state_hash: ...
working_post_state_identity_kind: ...
working_state_gate_observations: [...]
authorized_mutations: [...]
mutation_or_terminal_result: ...
resource_disposition: ...
```

The complete R1 is hashed externally only after construction. No R1 field or
ledger member stores R1's own hash.

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
admitted candidate set
member-set digest
BEXT
canonical member order
member gate observations
HW0 / HWA
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
- Q bound to a different source record; and
- Q identity already present in R0 replay-protection state.

Each test terminates at side-effect-free admission. R0, ledger, schedule,
cursor, and future eligibility remain byte-identical.

### Batch-construction rejection

- duplicate input ID;
- duplicate physical-event identity under a different input ID;
- replayed evidence whose input identity is already adjudicated;
- member-set digest mismatch;
- member not admitted against R0;
- harness-supplied member order treated as authority; and
- UE-supplied external phase, priority, or winner field.

No BEXT or canonical mutation may escape.

### Atomic resolver rejection

- BEXT source hash differs from R0;
- BEXT candidate set differs from its bound set digest;
- member mutation exceeds its admitted consequence contract;
- filesystem timestamp, process schedule, or presentation order reaches
  canonical ordering;
- a member attempts to create its own canonical successor or ancestry;
- any provisional working state is exposed as a canonical record;
- a partial member-execution exception occurs; and
- promotion, materialization, or UE code reaches canonical ordering, mutation,
  disposition, ledger, or policy selection.

A structural failure aborts the in-process transaction with no returned or
written R1. Durable storage crash consistency is not claimed because general
save/persistence is prohibited. QA success followed by QB's
ordinary failed gate is not a structural failure; it closes as the specified
atomic R1.

The atomicity harness must inject deterministic faults at each of these exact
points and prove R0 remains byte-identical with no R1 or canonical artifact:

```text
after QA provisional mutation
after QB ordinary gate evaluation
during batch-ledger construction
after complete provisional R1 construction but before return/write
```

The order-isolation harness must also poison file mtimes, reverse directory
enumeration, reverse candidate-container order, and vary process/presentation
traces while holding the closed admitted set constant. BEXT, canonical order,
working hashes, and R1 must remain byte-identical. Source audit must trace
actual resolver dataflow; string search alone is insufficient.

## Source and authority audit

The proof fails even if outputs coincide when source inspection finds:

```text
two canonical external resolvers
policy-specific or witness-specific result branches
UE-selected order or priority
harness list order reaching the resolver
filesystem metadata reaching the resolver
cross-domain readable or writable proof state
QA naming QB or QB naming QA
pair-specific conflict handling
member-owned canonical commit or ancestry
partial-success record publication
```

There must be one declared canonical external-batch resolution path for this
simulation identity and boundary.

## Acceptance gates

The proof may freeze only after the exact identity, payload, R0, R1, QA, QB,
digest projections, receipt schemas, BEXT schema, ordering key, working-state
projection, member provenance, serialization, and failure dispositions are
exhaustive.

Implementation may later pass only if:

1. two fresh isolated Unreal domains independently verify and materialize the
   same R0 and physically emit exact QA and QB;
2. each Q is admitted side-effect-free against immutable R0 with integrity and
   consequence authorization validated separately;
3. one R0-bound BEXT binds the exact admitted member set;
4. canonical member order is independent of every physical and presentation
   permutation in W1–W4;
5. QA passes the ordinary shared-slot gate and changes HW0 to HWA provisionally;
6. QB remains R0-authorized inside BEXT, reads HWA, fails the unchanged ordinary
   gate, and acquires no resource;
7. exactly one atomic R1 with singular H0 ancestry and one ordered batch ledger
   entry is emitted;
8. QA-only and QB-only controls each succeed with identical member definitions;
9. duplicate, stale, redirected, caller-ordered, local-authority, and partial
   execution attempts fail at their declared boundary;
10. each witness deterministically replays to byte-identical canonical
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
                  replay + atomicity + provenance oracle
                                   │
                                   ▼
                    evidence + self-excluding manifest
```

## Explicit non-claims

This candidate does not prove or authorize:

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

### 0.1.0-draft.0 — 2026-08-27

- Opened a specification-only proof for two independently materialized R0-bound
  evidence sources entering one atomic canonical external batch.
- Proposed explicit external-member ordering, self-hash-safe provisional
  working-state identity, W1–W4 order-independence witnesses, QA/QB controls,
  batch-level atomicity, and two-domain Unreal isolation.
- Authorized no implementation or adjacent 2+2, network, movement, streaming,
  retry, random, or city-scale work.
