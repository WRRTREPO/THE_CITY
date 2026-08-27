# Integrated Unreal Promotion-Unload-Repromotion Proof

**Version:** 0.1.0-draft.2\
**Status:** Specification review only. Implementation is not authorized.\
**Parent law:** [Resolution Semantics Law — v0.1.1](Resolution%20Semantics%20Law%20-%20v0.1.1.md)\
**Sealed predecessors:** [Causal-LOD Equivalence Proof — v0.1.0](Causal-LOD%20Equivalence%20Proof%20Evidence%20-%20v0.1.0.md); [Record-Relative Chronological Resolution Proof — v0.1.0](Record-Relative%20Chronological%20Resolution%20Proof%20Evidence%20-%20v0.1.0.md); [External Input Boundary Proof — v0.1.1](External%20Input%20Boundary%20Proof%20Evidence%20-%20v0.1.1.md); [Unreal Materialization Proof — v0.1.0](Unreal%20Materialization%20Proof%20Evidence%20-%20v0.1.0.md); [Bridge Access Persistence Round-Trip Evidence — v0.1.1](Bridge%20Access%20Persistence%20Round-Trip%20Evidence%20-%20v0.1.1.md)\
**Related sealed scheduler hardening:** [Same-Clock Successor Semantics Proof — v0.1.0](Same-Clock%20Successor%20Semantics%20Proof%20Evidence%20-%20v0.1.0.md), not exercised by this fixture.\
**Parent continuation:** [Co-op Open-City FPS Simulation — v0.7 Working Continuation](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)\
**Candidate simulation identity:** `0.7.0-draft.51` — exact identity and serialization remain freeze gates.

## Question

> **Can a sealed canonical record be promoted into a fresh Unreal physical
> representation, produce an evidenced external input, survive destruction of
> that representation, continue under boundary-jump canonical execution, and
> reconstruct the later truth in a second fresh Unreal process?**

This is neither a player-movement proof nor a streaming proof. It integrates
only the already-sealed authority boundaries.

```text
R0 @ t0/00
  ↓ representation-promotion request only
fresh UE process #1 accepts and materializes R0
  ↓ physical action emits Q @ t0/30
canonical admission and BQ transaction
  ↓
Rinput
  ↓ destroy UE process #1
boundary-jump canonical execution
  ↓ alpha revalidates at t1/00
Rfinal
  ↓ fresh UE process #2 materializes Rfinal only
```

The proposition is:

> **Throwing away local physical representation must not throw away, delay, or
> reinterpret canonical causality.**

## Scope

After a later freeze, this proof may implement only:

- one exact canonical payload;
- one active autonomous commitment, `alpha`;
- one interaction surface which may emit one exact Q;
- one input transaction at `t0/30` and one autonomous transaction at `t1/00`;
- one fresh UE source process, termination witness, and fresh return process;
- isolated source-input, source-output, and return-input proof domains;
- a dense canonical reference, an integrated boundary-jump witness, and a
  Q-absent control; and
- tests, source audit, build, evidence, replay, and a self-excluding manifest.

It does not authorize player movement, helicopter travel, proximity
thresholds, World Partition, asynchronous streaming, level instances,
same-clock work, multiple inputs or commitments, randomness, networking,
save/load, city geography, planner work, population, or scale.

`alpha`, `gate_token`, and the interaction surface are fixture nouns, not
city ontology or production primitives.

## Three independent machines

```text
CANONICAL EXECUTION
  dense inspection | boundary jump

REPRESENTATION LIFECYCLE
  unloaded | promoted UE process | destroyed

AUTHORITY
  canonical record and transaction layer only
```

A promotion request derives local representation from a sealed record. It may
not alter the canonical clock, gate state, commitment state, schedule,
resources, ledger, canonical policy, or canonical hash. Promotion does not
mean dense canonical execution.

Unreal may materialize state and emit Q. It may not select an autonomous
boundary, resolve `alpha`, commit a record, write a causal ledger, or choose a
canonical policy.

## Candidate identity and canonical payload

The frozen version must make these exact:

```yaml
record_schema: CanonicalResolutionEnvelope.v1
payload_schema: IntegratedUnrealPromotionUnloadRepromotionPayload.v1
scenario_id: integrated-unreal-promotion-unload-repromotion-v1
scenario_version: 0.1.0
simulation_version: 0.7.0-draft.51
seed: integrated-unreal-promotion-unload-repromotion-v1/0001
```

The canonical serializer and canonical-envelope hash law are inherited from
the Resolution Semantics Law. A successor record contains no self-referential
post-state hash.

For this draft, `H0`, `Hinput`, and `Hfinal` mean the canonical-envelope hashes
of R0, Rinput, and Rfinal. `D0`, `Dinput`, and `Dfinal` mean the SHA-256 hashes
of their exact raw UTF-8 payload artifacts. The two identities are related by
the detached receipt but are not interchangeable.

R0 contains exactly the authority needed for the one interval:

```yaml
canonical_envelope:
  identity: <exact identity above>
  current_causal_state:
    gate_token:
      state: enabled
      physical_actor_id: integrated_gate_token_01
    commitments:
      alpha:
        state: active
        terminal_disposition: null
  future_causal_state:
    canonical_clock: t0/00
    unresolved_work:
      - boundary_key: [t1/00, 10]
        work_id: t1/00/10/integrated/commitment_alpha.resolve
        commitment_id: alpha
        required_gate:
          path: current_causal_state.gate_token.state
          required_value: enabled
  causal_provenance:
    fixture_genesis: <exact frozen witness>
    accepted_external_inputs: []
    authoritative_causal_ledger: []
    canonical_ancestry: null
```

The later exact schema may add no authority beyond state, admission, ancestry,
terminal disposition, provenance, and scheduling needed by this proof. Any
additional authoritative field requires a new payload schema and identity.

## Detached materialization receipt

The proof input filesystem and process execution context are different classes
of input. Neither may be inferred from the other.

```yaml
ue_source_process:
  proof_input_files:
    - canonical_payload_R0.json
    - launch_receipt_R0.json
  non_authoritative_execution_context:
    interaction_opportunity: t0/30

ue_return_process:
  proof_input_files:
    - canonical_payload_Rfinal.json
    - launch_receipt_Rfinal.json
  non_authoritative_execution_context: none
```

The source opportunity is a harness-supplied fixture token, not a proof-input
file and not canonical state. The return process receives no equivalent
context. The visible-input audit inventories both filesystem inputs and
execution-context values before each process starts.

The detached receipt is operational integrity evidence, not city state:

```yaml
receipt_schema: IntegratedUnrealLaunchReceipt.v1
artifact_role: canonical_materialization_input
raw_payload_sha256: <SHA-256 of exact UTF-8 payload bytes>
expected_record_schema: CanonicalResolutionEnvelope.v1
expected_payload_schema: IntegratedUnrealPromotionUnloadRepromotionPayload.v1
expected_scenario_id: integrated-unreal-promotion-unload-repromotion-v1
expected_simulation_version: 0.7.0-draft.51
```

UE computes SHA-256 over the raw UTF-8 payload bytes before parsing. It refuses
materialization and exposes no proposal capability if receipt, bytes, schema,
scenario, or identity disagree. The frozen version must define receipt JSON,
UTF-8, field-presence, null, and hash-hex rules exactly.

### Process-domain isolation

The harness creates three physically distinct proof domains:

```text
source_input/
  canonical_payload_R0.json
  launch_receipt_R0.json

source_output/
  Q only

return_input/
  canonical_payload_Rfinal.json
  launch_receipt_Rfinal.json
```

Fresh UE process #1 may read `source_input/` and write its one Q to
`source_output/`. It may not read `return_input/`. Fresh UE process #2 may
read `return_input/` only; it has no access to `source_input/` or
`source_output/` and no writeable proof-exchange directory. The harness must
also assert that UE #2 receives no predecessor-path, Q-path, branch-selector,
save, configuration, session, cache, or inherited command-line input capable
of carrying fixture truth.

Before UE #2 launches, the harness records a complete allowed-file list and
raw-byte hashes for `return_input/` and rejects every extra visible proof
input. Process death alone is not accepted as filesystem isolation evidence.

### Materialization acceptance receipt

After receipt validation, parse, and physical materialization, each UE process
emits one detached `IntegratedMaterializationAcceptanceReceipt.v1` on a
structured process-output channel captured by the harness. It is operational
evidence, not canonical state and not a file in any proof-input domain.

The source receipt records:

```yaml
process_instance_id: <operational only>
accepted_raw_payload_sha256: D0
accepted_canonical_hash: H0
materialized_actor_id: integrated_gate_token_01
materialized_gate_state: enabled
materialized_alpha_state: active
proposal_capability_enabled: true
```

The return receipt records:

```yaml
process_instance_id: <operational only>
accepted_raw_payload_sha256: Dfinal
accepted_canonical_hash: Hfinal
materialized_actor_id: integrated_gate_token_01
materialized_gate_state: disabled
materialized_alpha_state: failed_gate
proposal_capability_enabled: false
```

The control's return receipt must instead report its own Rcontrol hash,
`enabled`, `succeeded`, and `proposal_capability_enabled: false`. A missing,
contradictory, or duplicate acceptance receipt fails the proof witness.

## Promotion, materialization, and Q

The harness may issue a non-authoritative promotion request against H0:

```yaml
promotion_request:
  source_canonical_hash: H0
  representation: unreal_fresh_process
  materialization_domain: integrated_fixture_surface
```

Fresh UE process #1 receives R0, its matching receipt, and only the
non-authoritative fixture-local interaction-opportunity context described
below. It must visibly materialize `gate_token = enabled` and `alpha = active,
due t1/00`.

The harness supplies `t0/30` to UE #1 as a sealed fixture-local interaction
opportunity through non-authoritative execution context. UE does not derive
canonical time, active-world time, or occurrence-time authority. It proves
only that physical interaction occurred under that supplied opportunity.

At that supplied opportunity, activation of `integrated_gate_token_01` may
change only disposable local representation and emit one Q:

```yaml
input_id: physical_disable_integrated_gate_token_0001
protocol_version: IntegratedExternalEvidence.v1
source:
  system: crew_physical_simulation
  source_record_hash: H0
  source_payload_raw_sha256: D0
occurrence_time: t0/30
instigator:
  kind: crew
  id: crew_01_to_04
target:
  kind: integrated_gate_token
  id: integrated_gate_token_01
observed_outcome:
  state: disabled
evidence:
  physical_actor_id: integrated_gate_token_01
  outcome_state: disabled
  evidence_digest: <exact digest projection hash>
proposed_mutations:
  - current_causal_state.gate_token.state = disabled
```

The digest projection explicitly omits `evidence_digest`; exact canonical JSON
is a freeze gate. Q is evidence, never a transaction or city mutation.

## Canonical continuation after unload

The authority chain follows the sealed External Input Boundary law:

```text
Q
  ↓ side-effect-free admission against R0
BQ bound to H0 @ t0/30
  ↓ canonical transaction
Rinput
```

Admission checks Q identity, source canonical hash, source raw-payload hash,
occurrence time, digest, actor, target, observed outcome, declared mutation,
and R0 target eligibility. The source raw-payload hash must match the receipt
that UE #1 independently accepted for R0. All side-effect-free gates are
evaluated before a decision. Malformed Q remains diagnostic only and gains no
BQ authority.

The BQ transaction produces Rinput atomically:

```yaml
canonical_clock: t0/30
gate_token.state: disabled
alpha.state: active
accepted_external_inputs:
  - physical_disable_integrated_gate_token_0001
future_causal_state.unresolved_work:
  - alpha @ [t1/00, 10]
causal_ledger:
  - accepted external input at t0/30
canonical_ancestry.parent_record_hash: H0
```

Q cannot cancel, terminalize, reschedule, or directly fail alpha. It changes
only alpha's later ordinary gate input.

After Rinput is durable, the proof terminates UE process #1 and records an
operational termination witness. The harness then proves the source domains
are inaccessible to the later canonical/return stages under the isolated
domain law above. This proves sequencing; process existence is never a
canonical gate.

Only then may the harness call `next_execution_boundary(Rinput)`. It must
rediscover the Rinput-bound alpha capability:

```yaml
kind: autonomous_consequence
source_record_hash: Hinput
decision_time: t1/00
simulation_phase: 10
due_work_ids:
  - t1/00/10/integrated/commitment_alpha.resolve
```

Resolving it yields Rfinal:

```yaml
canonical_clock: t1/00
gate_token.state: disabled
alpha:
  state: failed_gate
  terminal_disposition: no_resource_acquired
future_causal_state.unresolved_work: []
causal_ledger:
  - accepted input at t0/30
  - alpha ordinary gate failure at t1/00
canonical_ancestry.parent_record_hash: Hinput
```

The alpha ledger must identify the actual Rinput gate observation:

```yaml
path: current_causal_state.gate_token.state
observed_value: disabled
required_value: enabled
result: false
```

An R0-bound autonomous capability retained after Rinput must fail as stale.

## Return materialization

Fresh UE process #2 receives only the two allowed `return_input/` files:
Rfinal and its matching receipt. It receives no R0, Q, BQ, source exchange
directory, cache, prior UE save, prior actor state, or branch selector. After
receipt verification and acceptance-receipt emission, it must visibly
materialize:

```yaml
gate_token: disabled
alpha:
  state: failed_gate
```

The return scene may derive only from Rfinal. It must not use the fact that a
crew action occurred as a presentation selector.

## Witnesses and oracle

| Witness | Execution / lifecycle | Required result |
| --- | --- | --- |
| Dense reference | Dense canonical execution receives the exact captured Q as ordered external input; no UE state participates in resolution. | R0 → Rinput → Rfinal. |
| Integrated primary | Boundary jump; promotion; fresh UE #1 emits Q; Q commits; UE #1 terminates; alpha is rediscovered; fresh UE #2 reads Rfinal only. | R0 → Rinput → Rfinal plus lifecycle witnesses. |
| Q-absent control | Fresh control UE source process accepts/materializes R0 and emits its source acceptance receipt; no interaction and no Q; source process terminates; boundary jump resolves alpha; fresh control return process receives Rcontrol only. | R0 → Rcontrol, token enabled / alpha succeeded, under the same isolation lifecycle. |

Dense reference and integrated primary require byte-identical canonical
authority at each shared checkpoint:

```yaml
must_match:
  R0.canonical_envelope: byte_identical
  R0.canonical_hash: identical
  Rinput.canonical_envelope: byte_identical
  Rinput.canonical_hash: identical
  Rfinal.canonical_envelope: byte_identical
  Rfinal.canonical_hash: identical
  accepted_input_identity: identical
  alpha_terminal_disposition: identical
  authoritative_ledger: byte_identical
  successor_ancestry: byte_identical
  future_schedule: byte_identical
  next_execution_boundary_after_Rfinal: identical_none
```

The control changes only because Q is absent. Its unchanged alpha definition
must read `enabled` and succeed through its ordinary gate.

## Required failure and source-audit witnesses

The frozen specification must require at least:

1. receipt raw-byte mismatch, schema mismatch, scenario mismatch, or identity
   mismatch → UE refusal and no Q;
2. changed digest-covered Q field with an old digest → diagnostic rejection;
3. redirected Q with a recomputed digest → contract rejection;
4. Q against another record or after Rinput → no BQ authority;
5. R0-bound alpha after Rinput → stale-boundary rejection;
6. promotion or demotion changing canonical authority → rejection;
7. local trace, receipt, UE state, or lifecycle state dataflow into canonical
   gate evaluation, mutation, disposition, schedule, or ledger → audit failure;
8. UE code path writing canonical records/ledgers, resolving alpha, or
   selecting canonical policy → audit failure; and
9. return UE process receiving predecessor, Q, exchange, cache, or branch
   input → harness failure before materialization; and
10. missing, contradictory, or duplicate materialization acceptance receipt →
    witness failure.

The audit must show one canonical resolver serves dense and boundary-jump
witnesses. It receives only canonical record-bound capabilities and admitted
Q, never representation or lifecycle state.

## Freeze gate

Do not freeze until the proof fixes exact payload, Q, BQ, receipt, ledger, and
artifact serializations; canonical and raw-byte hash projections; exact
R0/Rinput/Rfinal/Rcontrol records; the process-termination and isolated-return
witnesses; source audit; release-manifest membership; and the exact simulation
identity.

After freeze, implementation may add only this neutral canonical fixture, a
receipt-verifying UE adapter, an exact proposal emitter, listed tests, evidence,
and a self-excluding release manifest. It may not add travel, streaming, World
Partition, same-clock behavior, or adjacent city systems.

## Decision record

- Draft.2 separates proof-input filesystem files from non-authoritative
  execution context and requires the control source process to emit the same
  source materialization-acceptance receipt as the primary source process.
- Draft.1 added mechanical process-domain isolation, detached UE acceptance
  receipts, harness-supplied interaction opportunity semantics, and the full
  source/destroy/return lifecycle for the Q-absent control.
- This draft selects no World Partition or production streaming architecture.
- Same-clock successor semantics is a sealed predecessor, not an exercised
  fixture behavior.
- Promotion is a non-authoritative representation request, not a proximity or
  mission-selection law.
- No code, Unreal source, payload artifact, README, capacity claim, or sealed
  release package changes under this draft.
