# Record-Relative Chronological Resolution Proof

**Version:** 0.1.0-draft.1
**Status:** Under specification review. Implementation is not authorized.
**Parent law:** [Resolution Semantics Law — v0.1.1](Resolution%20Semantics%20Law%20-%20v0.1.1.md)
**Predecessors:** [Resolution Semantics Substrate Proof — v0.1.0](Resolution%20Semantics%20Substrate%20Proof%20Evidence%20-%20v0.1.0.md); [Causal-LOD Equivalence Proof — v0.1.0](Causal-LOD%20Equivalence%20Proof%20Evidence%20-%20v0.1.0.md)
**Parent continuation:** [Co-op Open-City FPS Simulation — v0.7 Working Continuation](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)
**Candidate simulation version:** `0.7.0-draft.39` — fixed if this proof freezes.

## Claim

Prove record-relative chronological resolution under variable non-authoritative
execution granularity:

> **Resolution policy may skip empty intervals, but after every committed boundary it must discover the next consequential boundary from the newly committed canonical record.**

The proof combines two already separate results without expanding either one:

```text
shared-state interference
        +
resolution-policy equivalence between empty boundaries
        ↓
record-relative chronological equivalence
```

It is canonical-only. It introduces no city, faction, route, vehicle, crew,
FPS, Unreal, planner, external-input, or stochastic system.

## Required identity boundary

Neither predecessor payload may be reused. This proof introduces new
authoritative execution semantics: three ordered transactions, per-checkpoint
ancestry, and a future schedule that survives more than one resolver call.

```yaml
record_schema: CanonicalResolutionEnvelope.v1
payload_schema: RecordRelativeChronologicalResolutionPayload.v1
scenario_id: record-relative-chronological-resolution-v1
scenario_version: 0.1.0
simulation_version: 0.7.0-draft.39
seed: record-relative-chronological-resolution-v1/0001
```

The identity lives only at `canonical_envelope.identity` and is included in
`canonical_hash`. The implementation must reject unknown, missing, redirected,
or incompatible authoritative fields. Any later field or semantic change
requires a new payload schema and simulation identity.

## One neutral canonical machine

The fixture contains three independently defined commitments and one shared
authoritative capacity fact. X and Y do not reference one another. Their only
relationship is ordinary access to the same fact.

```text
X due at t1/00
  → acquires the one shared slot

Y due at t1/30
  → ordinarily requires that slot
  → fails its ordinary gate after X's committed allocation

Z due at t2/00
  → independent of the shared slot
  → resolves normally
```

`scheduled_consequential_decisions` is authoritative future state. It is not a
precomputed execution itinerary: it records that future work exists, but it
does not authorize any process to retain a selected next boundary, due set,
gate result, working state, or outcome after a canonical commit.

### Exact payload schema

`RecordRelativeChronologicalResolutionPayload.v1` permits only the following
authoritative fields and values. All maps use lexicographically ascending keys;
all lists use their declared canonical order.

```yaml
canonical_envelope:
  identity:
    record_schema: CanonicalResolutionEnvelope.v1
    payload_schema: RecordRelativeChronologicalResolutionPayload.v1
    scenario_id: record-relative-chronological-resolution-v1
    scenario_version: 0.1.0
    simulation_version: 0.7.0-draft.39
    seed: record-relative-chronological-resolution-v1/0001

  current_causal_state:
    durable_facts:
      stable_gate: stable
      shared_slot_outcome: unallocated | allocated_to_x
      outcome_x: pending | succeeded
      outcome_y: pending | failed_gate
      outcome_z: pending | succeeded

    gate_relevant_state:
      stable_gate: stable
      shared_slot_state: available | allocated_to_x

    active_and_terminal_commitments:
      commitment_x:
        owner: process_x
        state: active | succeeded
        gate_check_at: t1/00
        required_gate: shared_slot_state == available
        reservation_id: null
        terminal_disposition: transform_shared_slot_to_allocation_x
      commitment_y:
        owner: process_y
        state: active | failed_gate
        gate_check_at: t1/30
        required_gate: shared_slot_state == available
        reservation_id: null
        terminal_disposition: no_resource_acquired_on_failed_gate
      commitment_z:
        owner: process_z
        state: active | succeeded
        gate_check_at: t2/00
        required_gate: stable_gate == stable
        reservation_id: reservation_z
        terminal_disposition: release_unit_z_on_success

    reservations_leases_and_resource_ownership:
      shared_slot:
        state: available | allocated
        allocation_owner: null | commitment_x
      unit_z:
        state: reserved | available
        reservation_id: reservation_z | null
        owner_commitment_id: commitment_z | null
    accepted_external_inputs: []

  future_causal_state:
    canonical_clock: t0/00 | t1/00 | t1/30 | t2/00
    scheduled_consequential_decisions:
      - decision_time: t1/00 | t1/30 | t2/00
        due_work_ids:
          - <the one exact canonical execution key due at that time>
    commitment_gate_check_schedule:
      commitment_x: t1/00 | null
      commitment_y: t1/30 | null
      commitment_z: t2/00 | null
    canonical_execution_keys:
      - t1/00/chronological/commitment_x.resolve
      - t1/30/chronological/commitment_y.resolve
      - t2/00/chronological/commitment_z.resolve

  causal_provenance:
    canonical_ancestry:
      parent_record_hash: null | <canonical hash>
      boundary_derivation: initial_record | next_consequential_boundary
    fixture_genesis:
      established_facts:
        - shared_slot = available
        - commitment_x = active
        - commitment_y = active
        - commitment_z = active
        - unit_z = reserved_by:reservation_z
    authoritative_causal_ledger:
      - source_record_hash: <hash of the exact record resolved>
        decision_time: t1/00 | t1/30 | t2/00
        due_work_ids: [<one exact due key at this boundary>]
        commitment_id: commitment_x | commitment_y | commitment_z
        evaluated_gates: []
        mutation_or_failed_gate: <exact terminal result>
        terminal_resource_disposition: <exact disposition>
    terminal_resource_dispositions:
      shared_slot: transform_shared_slot_to_allocation_x | null
      commitment_y: no_resource_acquired_on_failed_gate | null
      reservation_z: release_unit_z_on_success | null
```

The exact initial R0 uses the `pending`, `active`, `available`, and `reserved`
values shown above; its clock is `t0/00`; its three schedule representations
contain X, Y, and Z at their stated times. Its causal ledger is empty and its
ancestry is `initial_record`. `fixture_genesis` explains initial facts without
manufacturing a transaction. Each successor appends exactly one ledger entry in
the declared ordered shape; the exact gate list and terminal result are frozen
per X, Y, and Z in the implementation specification.

The implementation specification must replace the compact list notation above
with the exact canonical JSON shape, absence rules, null placement, canonical
ordering, and rejecting validator. It may not add another authoritative field
under this identity.

## Canonical scheduler and transaction law

There is exactly one scheduler query:

```text
next_consequential_boundary(canonical_envelope)
  → none
  | { decision_time, due_work_ids: [canonical execution key ascending] }
```

It validates that all three authoritative schedule representations agree,
selects the earliest unresolved decision time not earlier than the current
canonical clock, and returns the complete due set at that time. It receives no
resolution policy, local sample, cache, trace, or prior query result.

Resolved work is removed by canonical execution identity, not merely because
its decision time equals the current clock. Therefore a lawful future payload
may create new unresolved work at the current clock and the next query can
still discover it. This proof's exact payload permits no new commitment or
schedule creation: an attempted same-clock successor is rejected by the
payload validator. The scheduler rule nevertheless remains `>=`, rather than
`>`, so this fixture cannot accidentally establish work loss as city law.

There is exactly one resolver:

```text
resolve_next_due(canonical_envelope, canonical_boundary)
```

It rejects a supplied boundary unless it exactly equals
`next_consequential_boundary(canonical_envelope)`. It resolves only that one
complete due set, atomically advances the canonical clock to its decision time,
applies the defined gate/disposition, removes only the resolved work from every
authoritative schedule representation, appends one causal-ledger entry, and
returns the next canonical record.

No resolver accepts a list of future boundaries. No policy owns scheduler
state.

Every discovered boundary is a record-bound capability:

```yaml
canonical_boundary:
  source_record_hash: hash(the exact canonical envelope queried)
  decision_time: <one canonical time token>
  due_work_ids:
    - <complete canonical due set, execution-key ascending>
```

`resolve_next_due(record, boundary)` requires
`boundary.source_record_hash == hash(record)` before any gate evaluation or
mutation. Retaining an old boundary object is harmless: after a commit, its
source hash cannot authorize a resolver call against the successor record.

### Required chronological chain

```text
R0, clock t0/00
  → next_consequential_boundary(R0)
  → { hash(R0), t1/00, [t1/00/chronological/commitment_x.resolve] }
  → resolve_next_due(R0, boundary)
  → R1

any retained R0 scheduling product is non-authoritative and cannot resolve R1

R1, clock t1/00
  → next_consequential_boundary(R1)
  → { hash(R1), t1/30, [t1/30/chronological/commitment_y.resolve] }
  → resolve_next_due(R1, boundary)
  → R2

any retained R1 scheduling product is non-authoritative and cannot resolve R2

R2, clock t1/30
  → next_consequential_boundary(R2)
  → { hash(R2), t2/00, [t2/00/chronological/commitment_z.resolve] }
  → resolve_next_due(R2, boundary)
  → R3

R3, clock t2/00
  → next_consequential_boundary(R3)
  → none
```

At `t1/00`, X revalidates `shared_slot_state == available`, succeeds, and
transforms the slot into a durable allocation owned by X. R1 preserves the
scheduled Y and Z work, but no R0-derived scheduler product has authority over
R1.

At `t1/30`, Y is discovered from R1 and revalidates the ordinary same gate
against R1. It fails because `shared_slot_state == allocated_to_x`. It acquires
no resource and records `no_resource_acquired_on_failed_gate`. Its
authoritative ledger entry must contain:

```yaml
source_record_hash: hash(R1)
evaluated_gate:
  path: current_causal_state.gate_relevant_state.shared_slot_state
  observed_value: allocated_to_x
  required_value: available
  result: false
```

At `t2/00`, Z is discovered from R2, revalidates only `stable_gate == stable`,
succeeds, releases `unit_z`, and records `release_unit_z_on_success`.
Z explicitly witnesses that Y's ordinary failed boundary produces R2 and that
chronological discovery continues; commitment failure must not terminate
scheduler operation.

For every `resolve_next_due(Rn, Bn)`, the exact pre-state is established only
by `Bn.source_record_hash == hash(Rn)`. There is no separately serialized
`transaction_parent_record_hash`, `transaction_pre_state_hash`, or
transaction-header object.

The successor record has one canonical ancestry representation:

```yaml
Rn_plus_1.causal_provenance.canonical_ancestry:
  parent_record_hash: hash(Rn)
  boundary_derivation: next_consequential_boundary
```

The authoritative ledger embeds the transaction witness rather than referring
to a separate header. Its entry records the boundary's `source_record_hash`,
`decision_time`, complete `due_work_ids`, gate observations, mutation or
failure, and terminal disposition. The ledger source hash is the exercised
boundary capability, not a second parent-ancestry field. It must equal the
successor's sole `canonical_ancestry.parent_record_hash`.

An implementation may not insert an authoritative intermediate clock-advance
record or a separate scheduler ledger entry before any of these three
transactions.

## Execution-resolution policies

Both policies use the exact same scheduler query and resolver. They differ only
in non-authoritative inspection between canonical boundaries.

```text
DENSE INSPECTION
  derives local diagnostic samples inside an empty interval
  then asks next_consequential_boundary(current committed record)

BOUNDARY JUMP
  derives no intermediate local sample
  then asks next_consequential_boundary(current committed record)
```

A local sample may copy displayable canonical facts into a local trace. It may
not evaluate or cache a gate result for later resolver use; mutate canonical
clock, resource, commitment, schedule, or ledger state; create an input; or
provide data to the scheduler or resolver.

Promotion derives only disposable local cache/samples/diagnostics from the
current canonical envelope. Demotion discards only those local values. Neither
can affect the canonical envelope, its hash, the next boundary, or resolver
input.

## Required witnesses

Every witness begins from byte-identical R0, has the same identity/seed/rules,
and receives no external inputs. Each witness must derive and record the next
boundary only immediately before its corresponding resolver call. A retained
prior boundary may remain in local memory, but its source-record hash must make
it incapable of authorizing resolution against a successor record.

```text
A. DENSE THROUGHOUT
R0 → dense samples → discover X → resolve R1
R1 → dense samples → discover Y → resolve R2
R2 → dense samples → discover Z → resolve R3

B. BOUNDARY JUMP THROUGHOUT
R0 → discover X → resolve R1
R1 → discover Y → resolve R2
R2 → discover Z → resolve R3

C. DENSE → DEMOTE → BOUNDARY JUMP → PROMOTE → DENSE
R0 → dense samples → demote → discover X → resolve R1
R1 → boundary jump → discover Y → resolve R2
R2 → promote → dense samples → discover Z → resolve R3

D. BOUNDARY JUMP → PROMOTE → DENSE → DEMOTE → BOUNDARY JUMP
R0 → discover X → resolve R1
R1 → promote → dense samples → discover Y → resolve R2
R2 → demote → discover Z → resolve R3
```

The displayed local operations are not canonical transitions and do not imply
an authoritative time advance. The only canonical clock changes occur inside
the X, Y, and Z resolver transactions.

## Checkpoint equivalence oracle

Final convergence is insufficient. Every witness must be byte-identical at
every committed checkpoint:

```yaml
must_match_at_R0:
  canonical_envelope: byte_identical
  canonical_hash: identical
  next_boundary:
    source_record_hash: hash_of_R0
    decision_time: t1/00
    due_work_ids: [t1/00/chronological/commitment_x.resolve]

must_match_at_R1:
  canonical_envelope: byte_identical
  canonical_hash: identical
  successor_ancestry_parent: hash_of_R0
  exercised_boundary_source: hash_of_R0
  authoritative_ledger: one_identical_X_entry
  terminal_dispositions: shared_slot_transformed
  future_schedule: Y_then_Z_only
  next_boundary:
    source_record_hash: hash_of_R1
    decision_time: t1/30
    due_work_ids: [t1/30/chronological/commitment_y.resolve]

must_match_at_R2:
  canonical_envelope: byte_identical
  canonical_hash: identical
  successor_ancestry_parent: hash_of_R1
  exercised_boundary_source: hash_of_R1
  authoritative_ledger: identical_X_then_Y_entries
  terminal_dispositions: X_transformed_and_Y_no_resource_acquired
  future_schedule: Z_only
  next_boundary:
    source_record_hash: hash_of_R2
    decision_time: t2/00
    due_work_ids: [t2/00/chronological/commitment_z.resolve]

must_match_at_R3:
  canonical_envelope: byte_identical
  canonical_hash: identical
  successor_ancestry_parent: hash_of_R2
  exercised_boundary_source: hash_of_R2
  authoritative_ledger: identical_X_Y_Z_entries
  terminal_dispositions: X_transform_Y_no_resource_Z_release
  future_schedule: empty
  next_boundary: none

may_differ:
  resolution_local_state: yes
  diagnostic_resolution_trace: yes
```

Within each policy, replay must be byte-identical in all canonical checkpoints
and its own local trace. Across policies, only local state and diagnostic trace
may differ.

## Runtime fail-closed cases

The future implementation must reject each malformed attempt without mutation
of the record it attempted to resolve, without a ledger append, resource
change, or schedule change:

1. a caller resolves Y against R1 using a boundary whose source record is R0;
2. a caller resolves Z from R1, crossing the due Y boundary;
3. a caller supplies a boundary whose source-record hash differs from the record passed to the resolver;
4. dense inspection mutates canonical clock, gate state, resource state, commitment state, schedule, or ledger;
5. a local sample caches Y's gate result or next boundary for scheduler/resolver use;
6. promotion writes local state into canonical authority or demotion removes scheduler/resolver-required authority;
7. an attempted same-clock successor, new commitment, or new schedule entry is introduced under this exact payload schema;
8. a policy selects a distinct resolver path, a precomputed boundary itinerary, a policy-specific outcome, an external input, or a random draw.

These are runtime authority violations. Their diagnostics are not canonical city
history.

## Equivalence-oracle failures

The following are post-run proof failures. Candidate artifacts remain available
for inspection; they are not retroactively rewritten or rolled back.

```yaml
equivalence_failure:
  - R0_R1_R2_or_R3_canonical_envelope_differs
  - R0_R1_R2_or_R3_canonical_hash_differs
  - per_checkpoint_next_boundary_differs
  - successor_ancestry_or_boundary_source_hash_differs
  - authoritative_ledger_or_ancestry_differs
  - commitment_terminal_state_or_resource_disposition_differs
  - future_schedule_differs
  - policy_local_state_reaches_canonical_authority
```

## Required source audit

The source audit must prove:

- exactly one `next_consequential_boundary` implementation and one `resolve_next_due` implementation exist;
- each resolver call accepts only a boundary whose `source_record_hash` equals the canonical record passed to that call;
- no `precomputed_boundary_itinerary`, retained due set, cached schedule view, or policy-owned scheduler state can acquire authority across a committed record transition;
- the scheduler selects unresolved work at `decision_time >= canonical_clock` and resolved execution identities cannot reappear;
- policy/local sample/cache/trace values cannot dataflow into canonical gate evaluation, mutation, ledger, scheduling, resource disposition, or resolver selection;
- X and Y definitions contain no reference, callback, pair-specific rule, or special priority relationship to one another;
- promotion/demotion cannot write canonical paths or discard authority needed at R1/R2/R3;
- no random draw, external input, Unreal path, city-content fixture, planner, or alternate resolver exists.

## Explicit boundary

This draft authorizes no implementation. If frozen, a separate authorization
would be required for exactly one canonical-only implementation: payload
validator, canonical serializer/hash, one scheduler query, one resolver, two
local policies, four witnesses, checkpoint oracle, runtime rejection checks,
replay/source audit, evidence, and a self-excluding manifest.

It does not authorize Unreal, FPS/materialization work, helicopter observation,
city-content fixture, routes, factions, agents, planners, external input,
randomness, additional commitment composition, networking, multiplayer,
rollback, save/load, map scale, production streaming, or city expansion.

## Changelog

### 0.1.0-draft.1 — 2026-08-26

- Bound each discovered boundary to the hash of its queried canonical record; stale boundaries now lose authority even if retained in local memory.
- Corrected scheduler discovery to select unresolved work at or after the canonical clock, while this exact payload rejects same-clock successor creation.
- Defined one successor ancestry representation, embedded boundary witness information in the authoritative ledger, and required an exact R1-relative Y gate observation.
- Made Z's role explicit: Y failure commits R2 and chronological discovery must continue to Z.
- No implementation or successor city scope is authorized.

### 0.1.0-draft.0 — 2026-08-26

- Opened a canonical-only specification for record-relative chronological resolution.
- Proposed one new payload schema, neutral X/Y/Z fixture, one record-relative scheduler query, one resolver, four local-policy witnesses, checkpoint-by-checkpoint equivalence, runtime rejection, and source-audit requirements.
- No implementation or successor city scope is authorized.
