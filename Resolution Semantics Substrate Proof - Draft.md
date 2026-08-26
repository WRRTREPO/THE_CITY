# Resolution Semantics Substrate Proof

**Version:** 0.1.0-draft.0
**Status:** Specification review only. No implementation or successor scope is authorized.
**Parent law:** [Resolution Semantics Law — v0.1.1](Resolution%20Semantics%20Law%20-%20v0.1.1.md)
**Parent continuation:** [Co-op Open-City FPS Simulation — v0.7 Working Continuation](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)
**Simulation version candidate:** 0.7.0-draft.31 — not fixed until this specification freezes.

## Claim

Prove the smallest executable substrate required before Causal-LOD Equivalence may be selected:

> **Given one canonical envelope with one exact payload schema, boundary discovery and resolution transitions preserve all authoritative state required for future causal decisions.**

This is not a city scenario. It is a neutral authority-and-representation proof.

## Frozen candidate boundary

~~~yaml
scope:
  payload_schema: one exact neutral fixture schema
  canonical_scheduler_query: one
  promotion_transform: one
  demotion_transform: one
  transition_witnesses:
    - boundary_identity
    - promotion_neutrality
    - demotion_neutrality
    - demotion_promotion_round_trip
  adversarial_disposition_classes: three

prohibited:
  implementation: true
  unreal: true
  city_content: true
  randomness: true
  causal_lod_high_coarse_scenario: true
  planner_generalization: true
  map_scale: true
  multiplayer_or_networking: true
~~~

All nouns below are structural fixture labels. They do not define production agents, sites, resources, content, or city ontology.

## Exact record identity

~~~yaml
record_schema: CanonicalResolutionEnvelope.v1
payload_schema: ResolutionSemanticsSubstratePayload.v1
scenario_id: resolution-semantics-substrate-v1
scenario_version: 0.1.0
simulation_version: 0.7.0-draft.31
seed: resolution-semantics-substrate-v1/0001
canonical_json:
  sort_keys: true
  separators: [",", ":"]
  ensure_ascii: true
canonical_hash: sha256(canonical_json(canonical_envelope))
~~~

The payload schema is exact. Unknown, missing, redirected, or incompatible authoritative payload fields must be rejected. Resolution-local fields are not payload fields and must never appear inside canonical_envelope.

## Exact authoritative payload schema

The candidate R0 is one complete canonical envelope. Every listed path is required; no other authoritative path is permitted by ResolutionSemanticsSubstratePayload.v1.

~~~yaml
canonical_envelope:
  identity:
    record_schema: CanonicalResolutionEnvelope.v1
    payload_schema: ResolutionSemanticsSubstratePayload.v1
    scenario_id: resolution-semantics-substrate-v1
    scenario_version: 0.1.0
    simulation_version: 0.7.0-draft.31
    seed: resolution-semantics-substrate-v1/0001

  current_causal_state:
    durable_facts:
      substrate_marker: stable
    active_commitments:
      commitment_alpha:
        owner: process_alpha
        state: active
        gate_check_at: t1/00
        required_gate: substrate_marker == stable
        reservation_id: reservation_alpha
        terminal_disposition: release_unit_alpha_on_failed_or_cancelled
    resource_ownership:
      unit_alpha:
        state: reserved
        reservation_id: reservation_alpha
        owner_commitment_id: commitment_alpha
    gate_relevant_state:
      substrate_marker: stable
    accepted_external_inputs: []

  future_causal_state:
    canonical_clock: t0/00
    scheduled_consequential_decisions:
      - decision_time: t1/00
        due_work_ids:
          - t1/00/substrate/commitment_alpha.gate_check
    commitment_gate_check_schedule:
      commitment_alpha: t1/00
    canonical_execution_keys:
      - t1/00/substrate/commitment_alpha.gate_check

  causal_provenance:
    canonical_ancestry:
      parent_record_hash: null
      boundary_derivation: initial_record
    fixture_genesis:
      established_facts:
        - active_commitments.commitment_alpha = active
        - resource_ownership.unit_alpha = reserved_by:reservation_alpha
      resources:
        - unit_alpha starts reserved by reservation_alpha
      terminal_resource_disposition: release_unit_alpha_on_failed_or_cancelled
    authoritative_causal_ledger: []
    terminal_resource_dispositions:
      reservation_alpha: release_unit_alpha_on_failed_or_cancelled
~~~

### Field contract

| Payload path | Type / accepted value | Authority role |
| --- | --- | --- |
| durable_facts.substrate_marker | exact string stable | Current durable and gate-relevant fact. |
| active_commitments.commitment_alpha | exact active commitment object above | Owns one future gate check and one reservation. |
| resource_ownership.unit_alpha | exact reserved-ownership object above | Proves reservation is persistent, not local cache. |
| future_causal_state.canonical_clock | exact time token t0/00 | Scheduler starting point. |
| scheduled_consequential_decisions | one exact schedule item | Sole source of next boundary and due set. |
| commitment_gate_check_schedule | exact map | Redundant authoritative scheduling witness; must agree with the schedule item. |
| canonical_execution_keys | one ascending key | Canonical ordering source for the due set. |
| causal_provenance | exact initial-record ancestry, fixture-genesis declaration, and empty causal ledger | Explains the existing reservation without pretending seed construction was a transaction. |
| terminal_resource_dispositions.reservation_alpha | exact disposition string | Required future lifecycle fact. |

The duplicated scheduling fields are intentional. The scheduler must validate their agreement rather than infer a missing schedule from resolution-local state.

R0 is a declared genesis record, not the result of a transaction inside this
proof. Its fixture_genesis object therefore records the exact facts already
present in R0. The authoritative causal ledger is intentionally empty: no
canonical action occurs inside this proof, so this fixture does not pretend that
seed construction was a transaction. No later transaction is in scope here.

## Canonical scheduler query

The one required scheduler operation is:

~~~text
next_consequential_boundary(canonical_envelope)
  → {
      decision_time: "t1/00",
      due_work_ids: [
        "t1/00/substrate/commitment_alpha.gate_check"
      ]
    }
~~~

It derives this answer only from the authoritative payload. Before returning it, the scheduler must reject the envelope if:

~~~text
active commitment gate_check_at disagrees with schedule
schedule due_work_ids disagree with canonical_execution_keys
reservation ownership disagrees with commitment reservation_id
durable_facts.substrate_marker disagrees with gate_relevant_state.substrate_marker
required gate references an absent or invalid gate-relevant fact
genesis provenance does not exactly explain the active reservation
~~~

This proof stops at boundary discovery. It does not generate a proposal, evaluate the future gate, resolve commitment_alpha, or change unit_alpha.

## Runtime envelope and exact transforms

A runtime envelope contains the canonical envelope plus optional local state:

~~~yaml
runtime_envelope:
  canonical_envelope: <byte-identical copy of R0 canonical_envelope>
  resolution_local_state:
    profile: minimal | promoted | demoted
    cache: {}
    samples: []
    diagnostics: []
~~~

### Promotion

~~~text
promote(R0)
  → runtime_envelope:
      canonical_envelope: byte-identical R0 canonical_envelope
      resolution_local_state:
        profile: promoted
        cache:
          commitment_alpha:
            next_gate_display: t1/00
            reservation_display: reservation_alpha
        samples:
          - t0/00
        diagnostics:
          - promotion_derived_from_canonical_envelope
~~~

The cache, sample, and diagnostic are derived copies only. The scheduler and any canonical resolver are forbidden to read them.

### Demotion

~~~text
demote(runtime_envelope)
  → runtime_envelope:
      canonical_envelope: byte-identical input canonical_envelope
      resolution_local_state:
        profile: demoted
        cache: {}
        samples: []
        diagnostics:
          - local_state_discarded
~~~

Demotion may discard every local field. It may not discard, alter, move, regenerate, or infer an authoritative payload field.

## Required witnesses

### A. Boundary identity

~~~text
R0
→ next_consequential_boundary(R0)
→ { t1/00, [t1/00/substrate/commitment_alpha.gate_check] }
~~~

Repeat the query against the canonical envelope contained in minimal, promoted, and demoted runtime envelopes. Every result must be byte-identical.

### B. Promotion neutrality

~~~text
R0
→ promote
→ promoted runtime envelope

authoritative_projection(promoted_runtime)
== byte-identical R0 canonical_envelope
~~~

The canonical hash, full authoritative payload, and scheduler query result must remain identical.

### C. Demotion neutrality

~~~text
promoted runtime envelope
→ demote
→ demoted runtime envelope

authoritative_projection(demoted_runtime)
== byte-identical R0 canonical_envelope
~~~

The local cache must be absent after demotion while the active commitment, reservation, schedule, terminal disposition, and ledger ancestry remain intact.

### D. Round-trip neutrality

~~~text
R0
→ promote
→ demote
→ promote

authoritative_projection(final_runtime)
== byte-identical R0 canonical_envelope
~~~

The final promoted cache may be regenerated from R0, but it may not be preserved as hidden authority from the first promotion.

## Adversarial disposition tests

Each malformed transform or query must fail closed with an inspectable non-causal test disposition. It must not mutate R0, append to the authoritative causal ledger, or create a new future schedule.

| Failure class | Malformed witness | Required result |
| --- | --- | --- |
| Promotion creates authority | Promotion adds durable_facts.illegal_marker or changes commitment_alpha | Reject: resolution_transition_rejected.authoritative_mutation_detected. |
| Demotion drops authority | Demotion removes resource_ownership.unit_alpha, the schedule item, ledger ancestry, or terminal disposition | Reject: resolution_transition_rejected.authoritative_loss_detected. |
| Policy changes boundary | A local policy proposes t2/00, omits the due key, or adds a due key | Reject: resolution_transition_rejected.boundary_mismatch. |

These dispositions belong to the proof harness or resolution trace, never to the canonical envelope or authoritative causal ledger.

## Source audit requirements

The future implementation must mechanically establish:

1. There is one scheduler query implementation; it receives only a canonical envelope.
2. Promotion and demotion cannot write canonical-envelope paths.
3. The scheduler and canonical resolver cannot read resolution_local_state or the resolution trace.
4. No policy branch can alter the decision time or due-work set.
5. No transform contains an expected-result shortcut or produces a commitment/resource/ledger mutation.
6. Every payload path is validated against ResolutionSemanticsSubstratePayload.v1.

## Acceptance gates before freeze

1. The payload schema is exact, neutral, and contains no city-content noun.
2. R0 includes current durable/gate-relevant state, one active future commitment, one reservation with terminal disposition, one complete future due set, and provenance explaining the reservation.
3. The scheduler query has exactly one accepted result.
4. Minimal, promoted, and demoted runtime envelopes return the identical boundary result.
5. Promotion, demotion, and the promote→demote→promote round trip preserve byte-identical authoritative projection and canonical hash.
6. Local data differs only outside canonical truth and cannot be consumed by scheduling or resolution.
7. Each adversarial failure class rejects without canonical mutation, causal-ledger append, schedule change, or resource change.
8. Identical inputs reproduce byte-equivalent runtime transforms, query results, proof-harness dispositions, and artifacts.
9. The source audit proves one canonical scheduler and zero resolution-policy authority over city facts.
10. No high/coarse execution scenario, Unreal, randomness, city content, planner behavior, or expanded city scope exists in the implementation.

## DAG plan

~~~text
review exact payload + transform contract
        │
        ▼
freeze substrate proof specification
        │
        ▼
separate authorization for canonical-only implementation
        │
        ├───────────────┐
        ▼               ▼
schema + scheduler      promote/demote transitions
validation              + adversarial dispositions
        │               │
        └───────┬───────┘
                ▼
witness replay + source audit
                │
                ▼
release artifacts + evidence seal
                │
                ▼
Causal-LOD Equivalence may be selected
~~~

## Explicit boundary

This candidate authorizes no code, test fixture, record migration, simulator refactor, Unreal work, random system, city content, planner extension, map scale, multiplayer, networking, rollback, or production streaming work.

## Changelog

### 0.1.0-draft.0 — 2026-08-26

- Opened the canonical-only Resolution Semantics Substrate Proof specification.
- Defined one exact neutral payload schema, one scheduler query, one promotion transform, one demotion transform, four neutrality witnesses, and three adversarial failure dispositions.
- Kept all implementation and full Causal-LOD Equivalence outside the scope pending review and freeze.
