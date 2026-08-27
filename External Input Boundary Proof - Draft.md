# External Input Boundary Proof

**Version:** 0.1.0
**Status:** Frozen. Canonical-only implementation is authorized within this exact boundary.
**Parent law:** [Resolution Semantics Law — v0.1.1](Resolution%20Semantics%20Law%20-%20v0.1.1.md)
**Predecessors:** [Causal-LOD Equivalence Proof — v0.1.0](Causal-LOD%20Equivalence%20Proof%20Evidence%20-%20v0.1.0.md); [Record-Relative Chronological Resolution Proof — v0.1.0](Record-Relative%20Chronological%20Resolution%20Proof%20Evidence%20-%20v0.1.0.md); [Crew Arrival Into Live Commitment Proof — v0.1.0](Crew%20Arrival%20Into%20Live%20Commitment%20Proof%20Evidence%20-%20v0.1.0.md)
**Parent continuation:** [Co-op Open-City FPS Simulation — v0.7 Working Continuation](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)
**Simulation version:** `0.7.0-draft.42` — fixed for this proof.

## Question

> **Can an evidenced player-originated consequence enter an interval that a
> boundary-jump policy would otherwise skip, become its own canonical boundary,
> and alter only the future eligibility of later autonomous work?**

The required shape is:

```text
R0, 14:29
  next autonomous boundary = 14:31

external physical evidence occurs at 14:30
  ↓
canonical external-input boundary at 14:30
  ↓
Rinput
  ↓
rediscover autonomous work from Rinput
  ↓
14:31 autonomous boundary revalidates changed state
  ↓
Rfinal
```

The 14:29/14:30/14:31 labels are illustrative. The exact fixture uses the
neutral time tokens `t0/00`, `t0/30`, and `t1/00`.

This proof does not re-prove Unreal physical resolution or evidence integrity.
Those boundaries are already separately demonstrated. It treats one exact,
sealed physical-evidence envelope as an external input and proves the missing
canonical temporal law: an earlier admitted input stops boundary jumping,
commits through canonical authority, and changes only later work that lawfully
depends on its resulting fact.

## Governing laws

### External evidence, admission, and execution boundary are distinct

An external evidence envelope is not authoritative merely because a runtime
observed it. Before canonical acceptance it remains an immutable input outside
the city record. Its occurrence time is an execution constraint, not a city
fact. This proof freezes three separate authority objects:

```text
Q
  external evidence envelope
  non-authoritative
        ↓
admit_external_input_candidate(R0, Q)
  side-effect-free admission validation
        ↓
BQ
  R0-bound external execution capability
        ↓
resolve_execution_boundary(R0, BQ, Q)
  canonical transaction
        ↓
Rinput
```

`admit_external_input_candidate` either returns a record-bound `BQ` or a
diagnostic rejection. It cannot mutate the canonical envelope, its ledger,
the schedule, or the replay-local cursor.

A malformed Q that fails this validation **has not crossed the canonical
admission boundary**. It is not a canonical mutation attempt under the
governing provenance law. Its rejection is diagnostic only, leaves `R0`
byte-identical, and is an isolated terminal API witness: the test ends without
advancing a cursor or continuing normal execution. This proof deliberately
does not define malformed-input consumption, retry, or continuation semantics.

Only a valid `BQ` may reach `resolve_execution_boundary`. Its transaction at
`t0/30` atomically advances canonical time to `t0/30`, applies the permitted
mutation, and appends causal provenance. There is no clock-only scheduler
advance before it. The BQ transaction itself is the first authoritative event
after `R0`.

### Boundary jump may skip only intervals with no admitted input

`next_consequential_boundary(record)` remains the record-relative query for
autonomous commitments. It does not inspect future player choices.

The input-aware execution coordinator has one additional, explicit input
source:

```text
next_execution_boundary(record, ordered_external_inputs, input_cursor)
  = earliest lawful boundary among:
      1. the next autonomous canonical boundary from record, and
      2. BQ, constructed only by successfully admitting the next externally
         supplied evidence input available after record.clock
```

The input cursor belongs to the ordered external input sequence, not the
canonical envelope. It supplies only externally available Q candidates for
admission; it does not precompute autonomous outcomes, cache a due set, or
alter the city before canonical admission.

For this exact fixture, the one valid input has occurrence time `t0/30`, which
is strictly between `R0.clock = t0/00` and the next autonomous boundary at
`t1/00`. A boundary-jump policy must therefore select that input boundary. It
must reject an attempt to resolve the `t1/00` autonomous boundary first.

The production question of how wall-clock/active-world progress exposes an
input opportunity is deliberately outside this proof. Here the ordered input
sequence is a sealed replay input, just as earlier proofs use sealed evidence
proposals. The law demonstrated is narrower: once a valid Q is available to
the canonical coordinator, no resolution policy may jump beyond its BQ.

### Player input changes future eligibility, never settled history

The external input may mutate only its declared current target fact. It may not
directly terminalize, cancel, reschedule, or rewrite the autonomous commitment.
The later autonomous boundary independently revalidates its normal gate against
the input successor record.

```text
accepted input at t0/30
  → gate_token_state = disabled

autonomous commitment at t1/00
  → requires gate_token_state = enabled
  → fails its ordinary gate
```

There is no rule equivalent to `if player_input then fail commitment`. The
relationship is only the ordinary gate read. An input occurring after the
autonomous result, same-time ordering, repair, reversal, or historical
reopening are excluded.

### One canonical resolver, no policy authority

There is exactly one canonical resolver:

```text
resolve_execution_boundary(canonical_envelope, execution_boundary, Q | null)
```

It accepts either a record-bound autonomous boundary with null external input,
or a `BQ` paired with its exact Q. It validates the selected boundary against
the exact record, then atomically advances time, applies the boundary's
permitted canonical work, updates schedule state, appends the authoritative
ledger entry, and returns one successor envelope. It never receives a malformed
external envelope; malformed-Q validation ends before resolver admission.

The two exact boundary schemas are a tagged union, not one ambiguous shape:

```yaml
external_input_boundary:
  source_record_hash: hash(the exact canonical envelope queried)
  kind: external_input
  decision_time: t0/30
  external_input_id: crew_evidence_disable_gate_token_0001
  due_work_ids: []

autonomous_boundary:
  source_record_hash: hash(the exact canonical envelope queried)
  kind: autonomous_consequence
  decision_time: t1/00
  external_input_id: null
  due_work_ids:
    - t1/00/input-boundary/commitment_alpha.resolve
```

`resolve_execution_boundary(record, boundary, Q | null)` requires exact source
record hash, exact kind-specific shape, and exact equality with the current
lawful next execution boundary before any gate evaluation or mutation.

Dense inspection, boundary jump, promotion, demotion, local traces, and the
input cursor may not mutate canonical state, evaluate a gate for resolver use,
append a ledger entry, choose a different resolver, or retain authority across
a committed successor.

## Required identity boundary

No earlier payload schema may be reused. This proof adds one new authoritative
semantic: external-input admission as a canonical boundary before scheduled
autonomous work.

The current sealed scheduler proofs do not implement this semantic; they
explicitly exclude external input. `next_execution_boundary` is therefore new
canonical architecture to be implemented and tested under this freeze, not a
policy wrapper that may be inserted to make this proof pass.

```yaml
record_schema: CanonicalResolutionEnvelope.v1
payload_schema: ExternalInputBoundaryPayload.v1
scenario_id: external-input-boundary-v1
scenario_version: 0.1.0
simulation_version: 0.7.0-draft.42
seed: external-input-boundary-v1/0001
```

The identity lives only in `canonical_envelope.identity` and is included in the
canonical hash. The payload validator, artifacts, replay inputs, and release
manifest must use these exact values. Unknown, missing, redirected, or
incompatible authoritative fields reject.

## Frozen canonical representation

Every canonical envelope, execution-boundary capability, Q digest projection,
and evidence artifact in this proof uses this exact canonical JSON law:

```text
canonical_json(value)
  = UTF-8 encoding of JSON with:
      object keys sorted lexicographically by Unicode code point;
      compact separators `,` and `:` only;
      `ensure_ascii = true`;
      no duplicate object keys;
      no NaN, Infinity, or -Infinity;
      arrays preserved exactly in their declared order; and
      a single terminal LF only for stored text artifacts, never in hashed JSON.

canonical_hash(envelope)
  = lowercase hexadecimal SHA-256(canonical_json(envelope))
```

All identifiers and values in this fixture are ASCII. Every canonical envelope
has exactly these four top-level keys and no others:

```text
causal_provenance
current_causal_state
future_causal_state
identity
```

The nested objects and lists shown below are exhaustive. Omitted keys are
absent, not implicitly null. A key shown with `null` must be present with JSON
`null`. The payload validator rejects all additional keys, missing keys, enum
changes, reordering of declared lists, and value changes outside an authorized
transaction result.

Let `H0 = canonical_hash(R0)`, `HI = canonical_hash(Rinput)`,
`HF = canonical_hash(Rfinal)`, and `HC = canonical_hash(Rcontrol_final)`.
These symbols are not placeholders: they are the exact values produced by the
fixed serializer over the exact records in this specification.

### Exact Q, digest projection, and BQ

Q's digest projection is this exact JSON value, before canonical serialization:

```json
{
  "evidence": {
    "outcome_state": "disabled",
    "physical_actor_id": "gate_token_01"
  },
  "input_id": "crew_evidence_disable_gate_token_0001",
  "kind": "evidenced_physical_consequence",
  "observed_outcome": {
    "state": "disabled"
  },
  "occurrence_time": "t0/30",
  "proposed_mutations": [
    {
      "op": "replace",
      "path": "/current_causal_state/durable_facts/gate_token_state",
      "value": "disabled"
    },
    {
      "op": "replace",
      "path": "/current_causal_state/gate_relevant_state/gate_token_state",
      "value": "disabled"
    }
  ],
  "source": "crew_physical_simulation",
  "source_record_hash": "H0",
  "target": {
    "id": "gate_token_01",
    "kind": "proof_gate_token"
  }
}
```

`D0 = lowercase hexadecimal SHA-256(canonical_json(Q_digest_projection))`.
In the literal JSON above, the string `"H0"` denotes the actual canonical
hash value `H0`, not those two characters. The full exact Q is the same object
with one additional key in its `evidence` object:

```json
"evidence_digest": "D0"
```

Here `"D0"` likewise denotes the actual resulting lowercase digest. This is
non-self-referential because `evidence_digest` is absent from the digest
projection. Its presence and exact value are required in full Q.

Successful side-effect-free admission of Q against R0 returns exactly:

```json
{
  "decision_time": "t0/30",
  "due_work_ids": [],
  "external_input_id": "crew_evidence_disable_gate_token_0001",
  "kind": "external_input",
  "source_record_hash": "H0"
}
```

This object is `BQ`. It is invalid against any record whose hash is not H0.
The Rinput autonomous boundary is exactly:

```json
{
  "decision_time": "t1/00",
  "due_work_ids": [
    "t1/00/input-boundary/commitment_alpha.resolve"
  ],
  "external_input_id": null,
  "kind": "autonomous_consequence",
  "source_record_hash": "HI"
}
```

### Exact successor records

Every record has the exact R0 object shape defined below. Only these declared
values differ between stages:

| Authoritative path | R0 | Rinput | Rfinal | Q-absent control final |
| --- | --- | --- | --- | --- |
| `canonical_clock` | `t0/00` | `t0/30` | `t1/00` | `t1/00` |
| `gate_token_state` in both state paths | `enabled` | `disabled` | `disabled` | `enabled` |
| `alpha_outcome` | `pending` | `pending` | `failed_gate` | `succeeded` |
| `commitment_alpha.state` | `active` | `active` | `failed_gate` | `succeeded` |
| `commitment_alpha.terminal_disposition` | `null` | `null` | `release_unit_alpha_on_failed_gate` | `release_unit_alpha_on_success` |
| `unit_alpha` | reserved by `reservation_alpha` | unchanged | available; reservation/owner null | available; reservation/owner null |
| `accepted_external_inputs` | `[]` | `["crew_evidence_disable_gate_token_0001"]` | unchanged | `[]` |
| autonomous schedule / gate schedule / execution keys | alpha at `t1/00` | unchanged | all empty / null / empty | all empty / null / empty |
| ancestry parent / derivation | `null` / `initial_record` | H0 / `external_input_boundary` | HI / `next_consequential_boundary` | H0 / `next_consequential_boundary` |
| authoritative ledger | `[]` | `[LQ]` | `[LQ, LAlphaFailed]` | `[LAlphaSucceeded]` |
| `terminal_resource_dispositions.reservation_alpha` | `null` | `null` | `release_unit_alpha_on_failed_gate` | `release_unit_alpha_on_success` |

No other authoritative value may differ. `Rfinal` and the control final carry
no remaining scheduled work. `next_consequential_boundary` and
`next_execution_boundary` both return `none` for each.

The exact ledger entry shapes are:

```json
{
  "action_id": "crew_evidence_disable_gate_token_0001",
  "actor_or_process_id": "crew_physical_simulation",
  "belief_inputs": [],
  "boundary": {
    "decision_time": "t0/30",
    "due_work_ids": [],
    "external_input_id": "crew_evidence_disable_gate_token_0001",
    "kind": "external_input",
    "source_record_hash": "H0"
  },
  "canonical_execution_sequence": 0,
  "canonical_post_state_hash": "HI",
  "canonical_pre_state_hash": "H0",
  "commitment_id": null,
  "decision_time": "t0/30",
  "evaluated_gates": [
    {"name":"source_record_hash_matches","observed_value":"H0","required_value":"H0","result":true},
    {"name":"occurrence_time_is_after_or_equal_to_record_clock","observed_value":"t0/30","required_value":"at_or_after:t0/00","result":true},
    {"name":"occurrence_time_is_strictly_before_next_autonomous_boundary","observed_value":"t0/30","required_value":"before:t1/00","result":true},
    {"name":"target_contract_matches","observed_value":"proof_gate_token:gate_token_01","required_value":"proof_gate_token:gate_token_01","result":true},
    {"name":"evidence_contract_matches","observed_value":"D0","required_value":"D0","result":true},
    {"name":"proposed_mutation_set_matches","observed_value":"two_exact_gate_token_replacements","required_value":"two_exact_gate_token_replacements","result":true},
    {"name":"target_currently_enabled","observed_value":"enabled","required_value":"enabled","result":true}
  ],
  "eligible_action_set": ["admit_external_input_candidate"],
  "external_input_id": "crew_evidence_disable_gate_token_0001",
  "kind": "external_input",
  "mutation_or_terminal_result": "gate_token_state_disabled",
  "observed_inputs": ["Q:D0"],
  "random_draw_reference": null,
  "resource_disposition": [],
  "selected_action": "admit_external_input_candidate",
  "simulation_phase": "external_input_admission",
  "simulation_version": "0.7.0-draft.42",
  "source_record_hash": "H0",
  "threshold_crossings": [],
  "downstream_eligibility_changes": ["commitment_alpha_revalidates_at_t1/00"]
}
```

`LAlphaFailed` is exactly:

```json
{
  "boundary": {
    "decision_time": "t1/00",
    "due_work_ids": ["t1/00/input-boundary/commitment_alpha.resolve"],
    "external_input_id": null,
    "kind": "autonomous_consequence",
    "source_record_hash": "HI"
  },
  "action_id": "commitment_alpha.resolve",
  "actor_or_process_id": "autonomous_process_alpha",
  "belief_inputs": [],
  "canonical_execution_sequence": 1,
  "canonical_post_state_hash": "HF",
  "canonical_pre_state_hash": "HI",
  "commitment_id": "commitment_alpha",
  "decision_time": "t1/00",
  "evaluated_gates": [
    {"observed_value":"disabled","path":"/current_causal_state/gate_relevant_state/gate_token_state","required_value":"enabled","result":false}
  ],
  "eligible_action_set": ["commitment_alpha.resolve"],
  "external_input_id": null,
  "kind": "autonomous_consequence",
  "mutation_or_terminal_result": "alpha_failed_gate",
  "observed_inputs": ["gate_token_state:disabled"],
  "random_draw_reference": null,
  "resource_disposition": "release_unit_alpha_on_failed_gate",
  "selected_action": "commitment_alpha.resolve",
  "simulation_phase": "autonomous_resolution",
  "simulation_version": "0.7.0-draft.42",
  "source_record_hash": "HI",
  "threshold_crossings": [],
  "downstream_eligibility_changes": []
}
```

`LAlphaSucceeded` is exactly the same object with these substitutions only:

```text
boundary.source_record_hash = H0
canonical_execution_sequence = 0
canonical_post_state_hash = HC
canonical_pre_state_hash = H0
evaluated_gates[0].observed_value = enabled
evaluated_gates[0].result = true
mutation_or_terminal_result = alpha_succeeded
observed_inputs = ["gate_token_state:enabled"]
resource_disposition = release_unit_alpha_on_success
source_record_hash = H0
```

The implementation must encode the alpha gate witness as this exact JSON
object. It must not replace it with a cached boolean or an implicit result.

## Neutral exact fixture

All nouns below are proof fixtures, not city ontology. `gate_token`,
`commitment_alpha`, and `crew_evidence_disable_gate_token_0001` do not define
production action primitives, mission forms, or player-content vocabulary.

### Authoritative R0

```yaml
canonical_envelope:
  identity:
    record_schema: CanonicalResolutionEnvelope.v1
    payload_schema: ExternalInputBoundaryPayload.v1
    scenario_id: external-input-boundary-v1
    scenario_version: 0.1.0
    simulation_version: 0.7.0-draft.42
    seed: external-input-boundary-v1/0001

  current_causal_state:
    durable_facts:
      gate_token_state: enabled
      alpha_outcome: pending
    gate_relevant_state:
      gate_token_state: enabled
    active_and_terminal_commitments:
      commitment_alpha:
        owner: autonomous_process_alpha
        state: active
        gate_check_at: t1/00
        required_gate: gate_token_state == enabled
        terminal_disposition: null
    reservations_leases_and_resource_ownership:
      unit_alpha:
        state: reserved
        reservation_id: reservation_alpha
        owner_commitment_id: commitment_alpha
    accepted_external_inputs: []

  future_causal_state:
    canonical_clock: t0/00
    scheduled_consequential_decisions:
      - decision_time: t1/00
        due_work_ids:
          - t1/00/input-boundary/commitment_alpha.resolve
    commitment_gate_check_schedule:
      commitment_alpha: t1/00
    canonical_execution_keys:
      - t1/00/input-boundary/commitment_alpha.resolve

  causal_provenance:
    canonical_ancestry:
      parent_record_hash: null
      boundary_derivation: initial_record
    fixture_genesis:
      established_facts:
        - gate_token_state = enabled
        - commitment_alpha = active
        - unit_alpha = reserved_by:reservation_alpha
    authoritative_causal_ledger: []
    terminal_resource_dispositions:
      reservation_alpha: null
```

`R0` contains no pending external input. The player consequence is not inserted
into authoritative future schedule state simply because a replay fixture knows
it will later be supplied.

### Sealed external evidence input Q

The primary ordered replay input sequence is exactly `[Q]`, where Q, D0, and
BQ are the frozen JSON values defined in [Frozen canonical
representation](#frozen-canonical-representation). No alternate Q field,
absence rule, digest form, mutation operation, or list ordering is lawful.

Changing a digest-covered Q field without recomputing D0 rejects for integrity
failure. Changing a field and recomputing a valid digest still rejects if it
violates Q's exact target, actor, outcome, or mutation contract.

Q's persistence gates are exact and side-effect-free:

```yaml
source_record_hash_matches: true
occurrence_time_is_after_or_equal_to_record_clock: true
occurrence_time_is_strictly_before_next_autonomous_boundary: true
target_contract_matches: true
evidence_contract_matches: true
proposed_mutation_set_matches: true
target_currently_enabled: true
```

All admission gates are side-effect-free. On success their exact results are
copied into the BQ transaction's authoritative ledger entry before commit. The
primary path accepts Q. Invalid, stale, redirected, late/equal-time, or
mutation-expanded Q variants reject before BQ construction or any canonical
mutation.

### Required autonomous revalidation

After `resolve_execution_boundary(R0, BQ, Q)` succeeds, the replay-local input
cursor advances and Q's identity is appended to `accepted_external_inputs`
inside the envelope. The canonical successor is `Rinput`:

```text
R0 at t0/00
  → admit_external_input_candidate(R0, Q)
  → BQ selected at t0/30
  → resolve_execution_boundary(R0, BQ, Q)
  → Rinput at t0/30
```

`Rinput` preserves the still-active `commitment_alpha`, its reservation, and
its t1/00 scheduled decision. It changes only canonical clock, Q's exact
declared token facts, accepted-input history, canonical ancestry, and the one
input ledger entry.

Successor ancestry is singular and canonical:

```yaml
Rinput.causal_provenance.canonical_ancestry:
  parent_record_hash: hash(R0)
  boundary_derivation: external_input_boundary

Rfinal.causal_provenance.canonical_ancestry:
  parent_record_hash: hash(Rinput)
  boundary_derivation: next_consequential_boundary
```

Each appended ledger entry embeds its execution-boundary witness, including
the exact `source_record_hash`, kind, decision time, Q identity or alpha due
work ID, evaluated gates, mutation/terminal result, and resource disposition.
There is no second canonical transaction-header representation.

If a replay-local cursor is reset after `Rinput`, Q cannot reacquire authority:
the coordinator derives `accepted_external_inputs` from canonical state and
will not admit a Q whose input ID is already accepted. It skips Q operationally
and returns alpha's Rinput-bound autonomous boundary. The cursor therefore
chooses only where to resume reading the immutable replay sequence; canonical
accepted-input identity decides whether an input can still acquire authority.

The old R0 autonomous-boundary object and old BQ object are stale
against `Rinput` because both carry `source_record_hash = hash(R0)`.

```text
Rinput
  → next_consequential_boundary(Rinput)
  → t1/00 commitment_alpha.resolve
  → resolve_execution_boundary(Rinput, autonomous-boundary, null)
  → Rfinal
```

At t1/00 the resolver reads:

```yaml
path: current_causal_state.gate_relevant_state.gate_token_state
observed_value: disabled
required_value: enabled
result: false
```

It fails `commitment_alpha` through its ordinary gate, releases
`reservation_alpha` as `release_unit_alpha_on_failed_gate`, removes the due
work from every authoritative schedule representation, appends one autonomous
ledger entry, and returns `Rfinal` with no next autonomous boundary.

The Q-absent control removes only Q from the ordered external input sequence.
It retains byte-identical R0, identity, commitment definition, autonomous
schedule, and resolver. The t1/00 commitment then reads `enabled`, succeeds,
and releases `reservation_alpha` as `release_unit_alpha_on_success`.

## Required witnesses

The primary equivalence witnesses all begin with byte-identical R0 and the
same ordered external input sequence `[Q]`.

```text
A. dense input-aware throughout
   R0 → local samples → Q at t0/30 → local samples → alpha at t1/00 → Rfinal

B. boundary jump input-aware throughout
   R0 → Q at t0/30 → alpha at t1/00 → Rfinal

C. dense → demote → boundary jump
   R0 → local samples → demote → Q → alpha → Rfinal

D. boundary jump → promote → dense
   R0 → Q → promote → local samples → alpha → Rfinal
```

The policies may differ only in resolution-local samples, traces, and derived
representation/cache state. They must each ask
`next_execution_boundary(current_record, ordered_inputs, input_cursor)` again
after every canonical successor. No witness may retain an old canonical
boundary, precompute a two-step itinerary, or decide Q's accepted outcome.

The counterfactual control is not part of cross-policy byte equivalence because
it intentionally removes Q. It proves causal relevance:

```text
same R0 + no Q
  → alpha succeeds

same R0 + Q before t1/00
  → Q disables token
  → alpha fails ordinary gate
```

## Required canonical comparisons

Across A–D, the following must be byte-identical at every checkpoint:

```yaml
R0:
  canonical_envelope
  canonical_hash
  next_consequential_boundary: alpha at t1/00
  next_execution_boundary: BQ at t0/30

Rinput:
  canonical_envelope
  canonical_hash
  Q ledger provenance
  source/parent ancestry
  next_consequential_boundary: alpha at t1/00
  next_execution_boundary: alpha at t1/00

Rfinal:
  canonical_envelope
  canonical_hash
  alpha gate witness
  terminal resource disposition
  authoritative ledger
  future schedule
  next_consequential_boundary: none
  next_execution_boundary: none
```

Only resolution-local state and diagnostic execution traces may differ.

The Q-absent control must differ only through normal causal consequences of
the missing external input: accepted-input history, gate-token facts, alpha
gate result, terminal disposition, ledger, and resulting records.

## Required failures

### Runtime rejection, no canonical mutation

Each malformed-Q witness is an isolated terminal API test:

```text
R0 + malformed Q
  → admit_external_input_candidate(R0, malformed Q)
  → diagnostic rejection
  → assert R0 byte-identical
  → test ends
```

No malformed-Q witness advances, consumes, retries, or otherwise mutates the
replay-local cursor. The implementation must reject and retain diagnostic
evidence outside canonical truth when any of these attempts occurs:

1. boundary jump resolves autonomous t1/00 work while earlier valid Q at t0/30 is available;
2. Q source record hash differs from the exact current record;
3. a digest-covered Q field changes without recomputing the evidence digest;
4. Q is redirected to another target, actor, outcome, or mutation set despite a recomputed valid digest;
5. Q's occurrence time is at or after the t1/00 autonomous boundary under this exact payload;
6. a local sample, trace, promotion, demotion, or input cursor creates or loses canonical authority;
7. a policy supplies a cached autonomous gate result, an alternate resolver, or an input outcome shortcut; or
8. a retained R0 boundary attempts to resolve Rinput.

### Equivalence-oracle failure, preserve candidates

The proof must preserve candidate artifacts for inspection rather than describe
cross-witness divergence as a transactional rejection. It fails if A–D differ
in any required canonical checkpoint, ancestry/source hash, accepted input,
ledger, gate observation, terminal disposition, schedule, or next boundary.

## Source-audit acceptance gate

The source audit must mechanically establish:

1. exactly one side-effect-free `admit_external_input_candidate` path constructs BQ from valid Q;
2. exactly one `resolve_execution_boundary` path resolves both BQ and alpha;
3. exactly one `next_consequential_boundary` path discovers autonomous work;
4. every selected execution boundary carries the exact source record hash and tagged-union shape;
5. the input-aware coordinator chooses BQ before later autonomous work but cannot mutate canonical state;
6. no policy/local cache/trace/input cursor dataflows into canonical gate evaluation, mutation, ledger, schedule, disposition, BQ construction, or resolver selection;
7. there is no precomputed boundary itinerary, input-result shortcut, `if Q then fail alpha`, or branch selector in canonical state;
8. cursor reset cannot reacquire Q authority once canonical accepted-input identity contains Q;
9. the autonomous alpha definition is byte-identical with and without Q; and
10. no randomness, Unreal path, city-content primitive, planner, or additional commitment exists.

## Acceptance

This proof passes only if it establishes:

```text
same R0
+ same autonomous commitment
+ same canonical resolver
+ same valid external evidence Q before the autonomous boundary
+ materially different local execution policies
──────────────────────────────────────────────────────────────────
same Rinput and Rfinal authoritative history

and

same R0 without Q
──────────────────────────────────────────────────────────────────
ordinary autonomous success through the unchanged alpha definition
```

The demonstrated law is:

> **Players may interrupt an empty interval by supplying valid evidenced input;
> they may change only future canonical eligibility, never rewrite a boundary
> that has already committed.**

## Explicit exclusions

The authorized implementation introduces no Unreal execution, live network
input transport, wall-clock synchronization, helicopter observation, city
fixture, route, faction, agent, randomness, same-time input ordering, late
input after settlement, repair/reversal, additional commitment composition,
multiple input streams, multiplayer arbitration, rollback, save/load, map
scale, or production streaming.

## Implementation acceptance boundary

Implementation may contain only:

1. the exact `ExternalInputBoundaryPayload.v1` validator and fixed serializer/hash;
2. side-effect-free Q admission validation, digest/contract rejections, and BQ construction;
3. one input-aware execution coordinator, one canonical resolver, and the unchanged autonomous boundary query;
4. exact R0/Rinput/Rfinal/control records, ledger entries, terminal dispositions, and tagged boundaries;
5. dense, boundary-jump, and two mixed witnesses; Q-absent control; cursor-reset witness; malformed-Q terminal tests; boundary-crossing/stale-capability tests; replay; checkpoint oracle; and source audit;
6. proof artifacts, evidence, and a self-excluding release manifest.

The implementation may not add production input continuation, Unreal,
wall-clock synchronization, city content, input ties, late evidence,
randomness, additional commitments, networking, rollback, save/load, scale, or
streaming.

No broader city or FPS scope follows from this specification.
