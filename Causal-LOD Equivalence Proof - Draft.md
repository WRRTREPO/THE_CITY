# Causal-LOD Equivalence Proof

**Version:** 0.1.0-draft.0
**Status:** Open for specification review. No implementation is authorized.
**Parent law:** [Resolution Semantics Law — v0.1.1](Resolution%20Semantics%20Law%20-%20v0.1.1.md)
**Predecessor:** [Resolution Semantics Substrate Proof — v0.1.0](Resolution%20Semantics%20Substrate%20Proof%20Evidence%20-%20v0.1.0.md)
**Parent continuation:** [Co-op Open-City FPS Simulation — v0.7 Working Continuation](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)
**Candidate simulation version:** `0.7.0-draft.34` — exact identity to be retained if this specification freezes.

## Claim

Prove the first actual Causal-LOD property:

> **Changing execution granularity between consequential boundaries does not change authoritative causal history.**

This is canonical-only. It proves neither FPS fidelity nor production streaming.

## Required identity boundary

`ResolutionSemanticsSubstratePayload.v1` remains a sealed predecessor fixture.
It cannot be reused: it stops at R0 boundary discovery and produces no later
canonical record.

The candidate proof must introduce a new exact identity:

```yaml
record_schema: CanonicalResolutionEnvelope.v1
payload_schema: CausalLodEquivalencePayload.v1
scenario_id: causal-lod-equivalence-v1
scenario_version: 0.1.0
simulation_version: 0.7.0-draft.34
seed: causal-lod-equivalence-v1/0001
```

The identity belongs only inside `canonical_envelope.identity` and is included
in `canonical_hash`. Unknown, missing, redirected, or incompatible
authoritative fields reject. New execution semantics therefore cannot hide
under `ResolutionSemanticsSubstratePayload.v1`.

## One neutral canonical machine

The candidate fixture has no city, faction, NPC, route, FPS, or planner noun.
It contains exactly one active commitment, one reservation, one stable gate,
one canonical boundary, and one terminal disposition.

### Candidate R0

```yaml
current_causal_state:
  durable_facts:
    substrate_marker: stable
    commitment_alpha_outcome: pending
  gate_relevant_state:
    substrate_marker: stable
  active_commitments:
    commitment_alpha:
      owner: process_alpha
      state: active
      gate_check_at: t1/00
      required_gate: substrate_marker == stable
      reservation_id: reservation_alpha
      terminal_disposition: release_unit_alpha_on_success
  resource_ownership:
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
        - t1/00/equivalence/commitment_alpha.resolve
  commitment_gate_check_schedule:
    commitment_alpha: t1/00
  canonical_execution_keys:
    - t1/00/equivalence/commitment_alpha.resolve

causal_provenance:
  canonical_ancestry:
    parent_record_hash: null
    boundary_derivation: initial_record
  fixture_genesis:
    established_facts:
      - active_commitments.commitment_alpha = active
      - resource_ownership.unit_alpha = reserved_by:reservation_alpha
  authoritative_causal_ledger: []
  terminal_resource_dispositions:
    reservation_alpha: release_unit_alpha_on_success
```

### One resolver and exact R1 shape

There is one canonical operation, not a dense resolver and a boundary-jump
resolver:

```text
resolve_next_due(canonical_envelope, canonical_boundary)
```

It must reject any supplied boundary that differs from
`next_consequential_boundary(canonical_envelope)`. It receives no resolution
policy, local sample, cache, diagnostic, or trace.

At the common `t1/00` boundary, it alone:

```text
revalidates substrate_marker == stable
→ commitment_alpha.state = succeeded
→ commitment_alpha_outcome = succeeded
→ releases unit_alpha
→ records release_unit_alpha_on_success
→ advances canonical_clock to t1/00 inside this transaction
→ appends one authoritative causal-ledger entry
→ removes the resolved due work and leaves no future consequential boundary
```

Candidate R1 therefore has one terminal commitment, an available `unit_alpha`,
the stated terminal disposition, one ledger entry whose transaction pre-state
is R0, and an empty future schedule/execution-key set. No policy may change
this result or add a separate authoritative event before `t1/00`.

## Resolution policies

The policies are execution strategies, not alternate world laws.

```text
DENSE INSPECTION
  derive non-authoritative local samples at t0/15, t0/30, and t0/45
  then call the shared resolver once at t1/00

BOUNDARY JUMP
  derive no intermediate sample
  call the same shared resolver once at t1/00
```

A dense sample may copy displayable canonical facts into a local trace. It may
not evaluate and cache an authoritative gate result, mutate the canonical
clock, reserve/release a resource, append the causal ledger, create future
work, or provide input to the resolver.

The sample offsets are resolution-local trace positions. They are not
authoritative clock advances. The canonical clock changes only inside the
common `t1/00` transaction.

## Promotion and demotion

Promotion and demotion use the inherited non-causal law under
`CausalLodEquivalencePayload.v1`:

```text
promotion
  → derive local cache / samples / diagnostics from canonical state
  → canonical envelope unchanged

demotion
  → discard local cache / samples / diagnostics
  → canonical envelope unchanged
```

Neither transform can carry a local sample into the authoritative envelope or
remove state needed by `resolve_next_due`.

## Required witnesses

All witnesses begin from byte-identical R0 with the same identity, seed, rule
set, empty external-input sequence, and canonical due boundary.

```text
A. DENSE THROUGHOUT
R0 → dense samples → shared t1/00 resolver → R1

B. BOUNDARY JUMP THROUGHOUT
R0 → shared t1/00 resolver → R1

C. BOUNDARY JUMP → PROMOTE → DENSE
R0 → no local sample → promote → dense samples → shared t1/00 resolver → R1

D. DENSE → DEMOTE → BOUNDARY JUMP → PROMOTE → DENSE
R0 → dense sample → demote → no local sample → promote → dense sample
   → shared t1/00 resolver → R1
```

The policy changes in C and D occur only in resolution-local runtime state.
They do not create an authoritative transition, delay the t1/00 due work, or
change the resolver input.

## Equivalence oracle

Every witness must end with byte-identical canonical authority:

```yaml
must_match:
  canonical_envelope: byte_identical
  canonical_hash: identical
  commitment_terminal_state: identical
  reservation_disposition: identical
  authoritative_ledger: byte_identical
  future_schedule: byte_identical
  next_consequential_boundary: { decision_time: null, due_work_ids: [] }

may_differ:
  resolution_local_state: yes
  diagnostic_resolution_trace: yes
```

The ledger records the one authoritative `t1/00` transaction only. It must not
record dense inspection as causal history. Each witness must also replay
byte-identically within its own policy sequence.

## Required fail-closed cases

The future implementation must reject, without canonical mutation, ledger
append, resource change, or future-schedule creation:

1. dense inspection mutates canonical clock before `t1/00`;
2. a local sample caches an authoritative gate result for later resolver use;
3. promotion carries local sample data into canonical authority;
4. demotion removes any resolver-required fact, reservation, disposition, or due work;
5. boundary jump omits or crosses authoritative due work;
6. either policy selects a distinct resolver path or policy-specific outcome;
7. terminal resource disposition, ledger ancestry, transaction pre-state, or future schedule differs across witnesses.

## Required source audit

The source audit must prove:

- exactly one `resolve_next_due` implementation;
- the resolver receives canonical envelope plus canonical boundary only;
- dense/boundary-jump policy controls local sampling only;
- policy/local-state/trace values cannot reach canonical gate evaluation, mutation, ledger, scheduling, or disposition code;
- promotion/demotion cannot write canonical paths;
- no expected-result shortcut, policy-specific terminal outcome, random draw, Unreal path, city-content fixture, planner, or external input exists.

## Explicit boundary

This draft authorizes no implementation, Unreal work, physical materialization,
city content, additional commitment composition, planning, stochastic system,
external input, networking, multiplayer, rollback, save/load, map scale, or
production streaming work.

The specification must freeze its exact payload fields, final R1 record,
canonical serializer, source-audit test plan, release artifacts, and
simulation identity before canonical-only implementation is authorized.

## Changelog

### 0.1.0-draft.0 — 2026-08-26

- Opened the first Causal-LOD Equivalence proof as a canonical-only specification.
- Proposed one new payload schema, one resolver, dense-inspection and boundary-jump policies, four policy-transition witnesses, byte-identical authority oracle, and fail-closed policy-leak tests.
- No implementation or successor city scope is authorized.
