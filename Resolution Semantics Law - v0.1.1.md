# Resolution Semantics Law

**Version:** 0.1.1
**Status:** Frozen. No implementation, scenario, or successor scope is authorized.
**Supersedes:** [Resolution Semantics Law — v0.1.0](Resolution%20Semantics%20Law%20-%20Draft.md), retained as the historical freeze record.
**Simulation version:** 0.7.0-draft.30 — fixed for the first resolution-semantics substrate proof.
**Parent:** [Co-op Open-City FPS Simulation — v0.7 Working Continuation](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)

## Governing law

The v0.1.0 Resolution Semantics Law remains in force except where this superseding clarification differs.

> **Resolution may alter how much non-authoritative work is represented or executed between consequential boundaries. It may not alter the authoritative state required to determine any future consequential boundary.**

The canonical envelope remains the city. Resolution-local state remains discardable representation, cache, sample, or diagnostic detail. Promotion and demotion remain non-causal transforms that cannot change the authoritative projection.

## The correction: container schema is not payload schema

`CanonicalResolutionEnvelope.v1` freezes the authority container, its hashing law, the scheduler interface, promotion/demotion invariants, causal-ledger boundary, and the absence of authoritative randomness. It does **not** enumerate every authoritative field required by every future concrete runtime.

Each concrete proof or runtime record must therefore declare one separate, versioned authoritative payload schema. That schema, not the generic container, defines the exact authoritative field set for that implementation identity.

```yaml
container_schema: CanonicalResolutionEnvelope.v1
law_id: resolution-semantics-law-v1
law_version: 0.1.1
simulation_version: 0.7.0-draft.30

concrete_record_identity:
  payload_schema: <fixed-and-versioned-schema-identity>

canonical_envelope:
  identity:
    payload_schema: <same-fixed-and-versioned-schema-identity>
  current_causal_state: {}
  future_causal_state: {}
  causal_provenance: {}
```

The payload-schema identity is authoritative: it is part of the canonical envelope and therefore part of `canonical_hash`.

## Payload-schema law

Before a concrete substrate implementation may begin, its payload schema must be frozen in the implementation specification. It must enumerate, exactly:

```yaml
authoritative_payload_schema_must_define:
  - every permitted authoritative field path
  - each field's type, valid values, and absence/default rule
  - the canonical encoding and ordering of each collection
  - the field's role in current causal state, future causal state, or provenance
  - every field needed for future scheduling, gates, ordering, resources,
    commitments, terminal disposition, or ledger reconstruction
  - rejection behavior for unknown, missing, redirected, or incompatible fields
```

No implementation may introduce an additional authoritative field under an unchanged payload-schema identity. Adding, removing, renaming, retyping, or changing the causal meaning of an authoritative field requires:

```text
new payload-schema identity
→ explicit compatibility/migration decision
→ new frozen simulation identity
→ new proof or implementation scope
```

`CanonicalResolutionEnvelope.v1` may remain stable across payload schemas only while its container semantics remain unchanged. Any change to where authority lives, how it is hashed, how the scheduler discovers due work, or what promotion/demotion may discard requires a new container-schema version and a new law version.

## Canonical envelope and hash boundary

The container taxonomy is fixed:

```yaml
canonical_envelope:
  identity:
    - record_schema
    - scenario_or_world_identity
    - simulation_version
    - deterministic_seed
    - payload_schema

  current_causal_state:
    - durable_city_facts
    - active_and_terminal_commitments
    - commitment_owners_and_lifecycle_state
    - reservations_leases_and_resource_ownership
    - gate_relevant_and_derived_state
    - accepted_external_inputs_and_their_identities

  future_causal_state:
    - canonical_clock
    - scheduled_consequential_decisions
    - commitment_gate_check_schedule
    - canonical_execution_keys_needed_for_future_ordering

  causal_provenance:
    - authoritative_causal_ledger
    - canonical_ancestry_and_transaction_hash_references
    - terminal_resource_dispositions
```

`canonical_hash = sha256(canonical_json(canonical_envelope))`.

Runtime caches, materialization detail, local samples, diagnostics, and the optional resolution trace remain outside the envelope and cannot affect its hash, its scheduler result, or any canonical resolver decision.

## Unchanged scheduler, transition, ledger, and randomness law

The following v0.1.0 terms remain frozen without modification:

```text
next_consequential_boundary(A)
  → none
  | { decision_time, due_work_ids: [canonical_execution_key ascending] }

authoritative_projection(promote(A, policy)) == A
authoritative_projection(demote(A + L, policy)) == A
```

`due_work_ids` is the complete canonical due set before proposal generation or working-state revalidation. Resolution policy cannot skip, cross, reorder, invent, or delay a due consequential boundary.

The causal ledger records authoritative causal boundaries only. The optional resolution trace may differ by policy, lies outside the canonical hash, and is forbidden as canonical scheduler or resolver input.

Authoritative randomness remains explicitly absent. The first substrate may not introduce a random draw stream, identity-addressed draw, per-commitment random state, or resolution-local randomness capable of affecting city truth.

## Acceptance gate before substrate implementation

The next authorization may be requested only when a concrete substrate specification supplies one fixed `payload_schema` identity and the complete field contract required above. The source/test plan must then prove:

```text
same canonical envelope
→ same next consequential boundary and complete due-work set

promote(A)
→ canonical projection unchanged

demote(A + L)
→ canonical projection unchanged

demote → promote
→ canonical projection unchanged
```

It must not yet claim high-versus-coarse execution equivalence, add a city fixture, use Unreal, introduce randomness, or broaden city behavior.

## Explicit boundary

This correction authorizes no code, test fixture, record migration, simulator refactor, Unreal work, random system, city content, planner extension, map scale, multiplayer, networking, rollback, or production streaming work.

## Changelog

### 0.1.1 — 2026-08-26

- Superseded v0.1.0 without rewriting its frozen record.
- Clarified that `CanonicalResolutionEnvelope.v1` is a fixed authority container, not an indefinitely extensible authoritative payload schema.
- Required a separately versioned, exact payload schema for every concrete runtime or proof record, with schema identity included in the canonical hash.
