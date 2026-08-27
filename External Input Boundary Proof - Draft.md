# External Input Boundary Proof

**Version:** 0.1.0-draft.1
**Status:** Specification review only. Implementation is not authorized.
**Parent law:** [Resolution Semantics Law — v0.1.1](Resolution%20Semantics%20Law%20-%20v0.1.1.md)
**Predecessors:** [Causal-LOD Equivalence Proof — v0.1.0](Causal-LOD%20Equivalence%20Proof%20Evidence%20-%20v0.1.0.md); [Record-Relative Chronological Resolution Proof — v0.1.0](Record-Relative%20Chronological%20Resolution%20Proof%20Evidence%20-%20v0.1.0.md); [Crew Arrival Into Live Commitment Proof — v0.1.0](Crew%20Arrival%20Into%20Live%20Commitment%20Proof%20Evidence%20-%20v0.1.0.md)
**Parent continuation:** [Co-op Open-City FPS Simulation — v0.7 Working Continuation](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)
**Candidate simulation version:** `0.7.0-draft.42` — fixed only when this specification freezes.

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
canonical architecture to be specified and tested after freeze, not a policy
wrapper that may be inserted to make this proof pass.

```yaml
record_schema: CanonicalResolutionEnvelope.v1
payload_schema: ExternalInputBoundaryPayload.v1
scenario_id: external-input-boundary-v1
scenario_version: 0.1.0
simulation_version: 0.7.0-draft.42
seed: external-input-boundary-v1/0001
```

The identity lives only in `canonical_envelope.identity` and is included in the
canonical hash. The frozen specification must replace this candidate identity
with the exact same values in its payload validator, artifacts, replay inputs,
and release manifest. Unknown, missing, redirected, or incompatible
authoritative fields reject.

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
        terminal_disposition: release_unit_alpha_on_success | release_unit_alpha_on_failed_gate
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

The input sequence in the primary witnesses contains exactly one immutable
input. Its complete canonical JSON shape, evidence digest algorithm, absence
rules, and canonical ordering must freeze before implementation.

```yaml
input_id: crew_evidence_disable_gate_token_0001
kind: evidenced_physical_consequence
source: crew_physical_simulation
source_record_hash: hash(R0)
occurrence_time: t0/30
target:
  kind: proof_gate_token
  id: gate_token_01
observed_outcome:
  state: disabled
evidence:
  physical_actor_id: gate_token_01
  outcome_state: disabled
  evidence_digest: <digest of Q digest projection>
proposed_mutations:
  - current_causal_state.durable_facts.gate_token_state = disabled
  - current_causal_state.gate_relevant_state.gate_token_state = disabled
```

Q's evidence digest is non-self-referential:

```text
evidence_digest = SHA256(canonical_json({
  input_id,
  kind,
  source,
  source_record_hash,
  occurrence_time,
  target,
  observed_outcome,
  evidence.physical_actor_id,
  evidence.outcome_state,
  proposed_mutations
}))
```

The projection omits `evidence.evidence_digest` itself. The frozen proof must
define the exact JSON object, key ordering, UTF-8 encoding, and SHA-256 hex
form before implementation. Any changed digest-covered field without a
recomputed digest rejects for integrity failure. A changed field with a
recomputed valid digest still rejects if it violates Q's exact target, actor,
outcome, or mutation contract.

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
  → resolve_execution_boundary(Rinput, autonomous-boundary)
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

This scope does not authorize implementation yet. It introduces no Unreal
execution, live network input transport, wall-clock synchronization, helicopter
observation, city fixture, route, faction, agent, randomness, same-time input
ordering, late input after settlement, repair/reversal, additional commitment
composition, multiple input streams, multiplayer arbitration, rollback,
save/load, map scale, or production streaming.

## Freeze gate

Before implementation, freeze:

1. the exact simulation identity, JSON payload schema, null/absence rules, and canonical serialization;
2. the exact Q digest projection, envelope contract, side-effect-free admission API, BQ tagged-union schema, and input cursor semantics;
3. the exact canonical execution-boundary selection law, Q-versus-autonomous tie prohibition, and malformed-Q terminal-test disposition;
4. exact Rinput/Rfinal/control record shapes, terminal dispositions, and allowed counterfactual differences;
5. the four policy sequences, cursor-reset witness, runtime rejections, equivalence oracle, replay condition, and source audit; and
6. an explicit continuation revision authorizing only the bounded canonical implementation.

No broader city or FPS scope follows from this specification.
