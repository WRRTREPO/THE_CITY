# Resolution Semantics Law

**Version:** 0.1.0
**Status:** Frozen. No implementation, scenario, or successor scope is authorized.
**Simulation version:** 0.7.0-draft.29 — fixed for the first resolution-semantics substrate proof.
**Parent:** [Co-op Open-City FPS Simulation — v0.7 Working Continuation](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)

## Why this law is required

The city contract promises causal LOD: changing computational fidelity must not change city truth. The sealed proofs establish deterministic transactions, commitments, materialization, physical evidence, shared-state composition, and bounded agent selection. They do **not** yet provide a canonical notion of execution resolution.

Current proof resolvers execute fixed fixture timelines. They do not yet expose one scheduler that can discover its next consequential boundary, vary non-authoritative work between those boundaries, or preserve a declared authoritative projection through promotion and demotion.

This document defines that missing substrate. It is deliberately not the later high-versus-coarse equivalence proof.

## Proposed law

> **Resolution may alter how much non-authoritative work is represented or executed between consequential boundaries. It may not alter the authoritative state required to determine any future consequential boundary.**

Resolution is a performance and representation policy. It is never a source of causal authority.

```text
CANONICAL ENVELOPE
  authoritative state + causal ledger
        │
        ├── scheduler discovers next consequential boundary
        ├── canonical rules resolve due work
        └── transaction changes authoritative truth
        │
        ▼
RUNTIME ENVELOPE
  canonical envelope + resolution-local state + resolution trace
        │
        ├── promote: derive local representation
        └── demote: discard or replace local representation
```

The canonical envelope is the city. The runtime envelope is an execution view of that city.

## Scope and exclusions

```yaml
scope:
  canonical_scheduler: one future substrate
  authoritative_projection: one future schema
  resolution_local_state_class: one
  promotion_transform: one law
  demotion_transform: one law
  randomness: none

prohibited:
  implementation: true
  new_scenario: true
  causal_lod_equivalence_execution: true
  unreal: true
  new_city_behavior: true
  planner_generalization: true
  map_or_population_scale: true
  multiplayer_or_networking: true
```

The terms in this document describe required architecture. They do not claim that the existing fixture resolvers already implement it.

## 1. Two state classes

### Canonical envelope

The canonical envelope is the only source of authoritative city truth. Its serialized form is the input to replay, persistence, canonical validation, and future materialization.

Its authoritative projection must contain, at minimum:

```yaml
authoritative_projection:
  identity:
    - record_schema
    - scenario_or_world_identity
    - simulation_version
    - deterministic_seed

  current_causal_state:
    - canonical_clock
    - durable_city_facts
    - active_and_terminal_commitments
    - commitment_owners_and_lifecycle_state
    - reservations_leases_and_resource_ownership
    - gate_relevant_and_derived_state
    - accepted_external_inputs_and_their_identities

  future_causal_state:
    - scheduled_consequential_decisions
    - commitment_gate_check_schedule
    - canonical_execution_keys_needed_for_future_ordering

  causal_provenance:
    - authoritative_causal_ledger
    - canonical_ancestry_and_transaction_hash_references
    - terminal_resource_dispositions
```

The first substrate uses this fixed identity and top-level envelope shape:

```yaml
record_schema: CanonicalResolutionEnvelope.v1
law_id: resolution-semantics-law-v1
law_version: 0.1.0
simulation_version: 0.7.0-draft.29

canonical_envelope:
  identity: {}
  current_causal_state: {}
  future_causal_state: {}
  causal_provenance: {}
```

A field belongs in one of these declared envelope sections whenever changing or losing it could change a future canonical decision, its ordering, its eligibility, or the explanation of a durable mutation. Implementations may add named fields within these sections, but may not add a new top-level authoritative section or omit a required category without a new versioned law.

`canonical_hash` is `sha256(canonical_json(canonical_envelope))`. It is not a hash of runtime caches, diagnostics, materialization detail, or any other resolution-local representation.

### Resolution-local state

Resolution-local state may exist only inside a runtime envelope. It may include:

```yaml
resolution_local_state:
  - discardable_cache
  - intermediate_samples
  - visualization_or_materialization_detail
  - performance_diagnostics
  - local_execution_bookkeeping_that_cannot_affect_canonical_resolution
```

It is explicitly forbidden from containing the sole copy of a fact required by future scheduling, a commitment gate, resource ownership, reservation/lease, canonical ordering, mutation provenance, or random outcome.

```text
runtime_state = canonical_envelope + resolution_local_state

authoritative_projection(runtime_state)
  = canonical_envelope
```

The scheduler and canonical resolver may read only the canonical envelope. Resolution-local state is not a fallback data source.

## 2. Consequential-boundary discovery

The scheduler owns canonical time and decides when canonical work is due. It must expose one deterministic operation in substance:

```text
next_consequential_boundary(canonical_envelope)
  → none
  | {
      decision_time,
      due_work_ids: [canonical_execution_key ascending]
    }
```

The result is derived only from authoritative state. It must identify the earliest future boundary at which canonical work can evaluate a gate, consume or release a resource, change a commitment lifecycle, apply a derived effect, or append an authoritative causal-ledger entry.

At that boundary, the inherited transaction law remains unchanged:

```text
immutable boundary snapshot
→ proposals from due work
→ canonical ordering
→ sequential working-state revalidation
→ commit or failed disposition
→ derived state and future scheduling
```

A resolution policy may choose whether to create local samples or caches while time lies strictly between two consequential boundaries. It may not:

```text
skip a due consequential boundary
cross it without canonical resolution
reorder due work
invent a new due commitment
delay a recorded boundary because the area is coarse
```

The policy therefore cannot change `next_consequential_boundary` for a given canonical envelope. The returned `due_work_ids` are the complete canonical due set for that decision time, before proposal generation or working-state revalidation.

## 3. Promotion and demotion

### Promotion

Promotion increases local representation or computation detail from canonical truth.

```text
promote(canonical_envelope, local_policy)
  → runtime_envelope
```

It may derive caches, samples, materialization inputs, or other resolution-local state. It may not create, delete, reinterpret, reschedule, or mutate an authoritative fact.

Required invariant:

```text
authoritative_projection(promote(A, policy)) == A
```

Promotion itself produces no canonical mutation and no causal-ledger entry.

### Demotion

Demotion reduces local representation or discards resolution-local work.

```text
demote(runtime_envelope, local_policy)
  → runtime_envelope_or_canonical_envelope
```

It may discard or replace only resolution-local state. It may not discard, compress away, alter, or relocate any authoritative field.

Required invariant:

```text
authoritative_projection(demote(A + L, policy)) == A
```

Promotion and demotion are not strategic decisions and are not causal events. They require no actor, commitment, resource disposition, or causal-ledger entry. If either operation requires one, it is attempting to change city truth and must instead submit an ordinary canonical transaction.

## 4. Ledger boundary

The causal ledger records authoritative causal boundaries only: canonical attempts, gate evaluations, accepted or failed dispositions, durable mutations, resource transitions, derived effects, and future scheduling.

It does not record the frequency with which a runtime sampled, cached, rendered, promoted, or demoted non-authoritative detail.

```yaml
authoritative_causal_ledger:
  included:
    - consequential_transaction_boundaries
    - canonical_ordering_and_revalidation
    - gate_results
    - resource_and_commitment_lifecycle
    - durable_mutations_and_ancestry
    - future_consequential_schedule_changes

resolution_trace:
  excluded_from_canonical_hash_and_causal_ledger:
    - local_samples
    - cache_population_or_eviction
    - diagnostics
    - promotion_and_demotion_events
    - materialization_only_detail
```

`resolution_trace` is optional diagnostic data. It may differ across policies, must not be treated as city history, and must not be read by canonical scheduling or resolution.

This is a deliberate correction to the existing fixture shape, where a single ledger structure currently records every demonstrated resolver action. The future substrate must make the authority of each entry explicit rather than infer it from execution frequency.

## 5. Randomness: explicitly absent

The first resolution-semantics substrate carries no authoritative stochastic draws:

```yaml
randomness:
  authoritative_random_draws: none
  random_state_in_authoritative_projection: none
  resolution_local_randomness_may_affect_canonical_truth: false
```

The existing fixture tie-break is deterministic ordering, not a random draw. This document does not introduce identity-addressed randomness, a global draw stream, per-commitment random state, or a future random-equivalence claim.

When a later city rule genuinely needs stochastic causal resolution, a separate law must define how a consequential draw is identified and persisted before it may participate in resolution equivalence.

## 6. Resolution-policy authority boundary

One canonical rule implementation resolves commitments, gates, resources, terminal dispositions, derived state, and ledger entries. Resolution policy may control only resolution-local representation between canonical boundaries.

The following are forbidden:

```text
high_resolution_resolver()
coarse_resolution_resolver()
if coarse: apply_expected_result()
coarse-only gate, mutation, commitment outcome, or resource disposition
promotion-created commitment, lease, scheduled decision, or provenance
demotion-discarded gate fact, schedule, reservation, or ledger ancestry
resolution trace used as canonical input
```

If a proposed optimization requires any of these, it is a new city law and must be separately specified, reviewed, and proven.

## 7. Future predecessor acceptance gate

The canonical-envelope identity, hash boundary, scheduler result shape, ledger boundary, and no-randomness rule are frozen. A later, separately authorized substrate proof must establish only:

```text
A
→ demote
→ authoritative_projection unchanged

A
→ promote
→ authoritative_projection unchanged

A
→ next_consequential_boundary
→ same answer under every permitted resolution policy
```

It must not yet claim full high-versus-coarse causal equivalence, introduce a new city fixture, use Unreal, or broaden city behavior. Causal-LOD Equivalence becomes selectable only after this substrate is sealed.

## DAG plan

```text
review authoritative-envelope + scheduler law
        │
        ▼
freeze exact schema and simulation identity
        │
        ▼
separate authorization for substrate implementation
        │
        ├───────────────┐
        ▼               ▼
scheduler boundary    promotion/demotion invariants
discovery proof        + ledger-boundary proof
        │               │
        └───────┬───────┘
                ▼
resolution-semantics evidence seal
                │
                ▼
Causal-LOD Equivalence may be selected
```

## Explicit boundary

This law authorizes no code, test fixture, record migration, simulator refactor, Unreal work, random system, city content, planner extension, map scale, multiplayer, networking, rollback, or production streaming work.

## Changelog

### 0.1.0 — 2026-08-26

- Froze `CanonicalResolutionEnvelope.v1`, `resolution-semantics-law-v1`, and simulation version `0.7.0-draft.29`.
- Fixed `canonical_hash` as the SHA-256 of canonical JSON for the canonical envelope alone; fixed the next-boundary result as one decision time plus a complete ascending canonical due-work set.
- Froze authoritative-only ledger semantics and the absence of authoritative random draws. Implementation remains separately unauthorized.

### 0.1.0-draft.0 — 2026-08-26

- Opened the Resolution Semantics Law after repository audit found that current causal LOD is record-to-FPS materialization, not variable-granularity canonical simulation.
- Defined the proposed canonical-envelope, resolution-local-state, consequential-boundary, promotion/demotion, authoritative-ledger, and no-randomness laws.
- Kept Causal-LOD Equivalence, all implementation, and all new scenarios out of scope pending review and freeze.
