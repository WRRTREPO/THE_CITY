# Shared-State Commitment Interference Proof

**Version:** 0.1.0
**Status:** Frozen. Implementation is authorized only within this proof.
**Simulation version:** 0.7.0-draft.23 — fixed for this proof.
**Parent:** [Co-op Open-City FPS Simulation — v0.7 Working Continuation](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)

## Claim

Prove the smallest general composition law of the city simulator:

> **Independently defined commitments may interfere solely because they read and write the same authoritative state.**

The canonical transaction layer must not know an X/Y relationship. It may only
apply normal canonical ordering and sequential working-state revalidation.

## Frozen proof boundary

```yaml
scenario_id: shared-state-commitment-interference-v1
scenario_version: 0.1.0
simulation_version: 0.7.0-draft.23
record_schema: SharedStateCommitmentInterferenceRecord.v1
seed: shared-state-commitment-interference-v1/0001

scope:
  execution: canonical_only
  shared_facts: one fixture-local capacity pool S
  commitment_definitions: two
  decision_boundaries: one
  unreal: prohibited
  planner_generalization: prohibited
  city_expansion: prohibited
```

`S`, `X`, and `Y` are fixture labels, not production city ontology. The proof
does not authorize a capacity subsystem, commitment library, action planner, or
pair-interaction framework beyond this record.

## The only shared state

```yaml
S:
  total_units: 1
  available_units: 1
  durable_allocations: []
```

`S.available_units` is the sole shared fact capable of causing interference.
Each successful commitment transforms one available unit into its own durable
allocation. The unit remains allocated after that commitment's terminal
success; this is an explicit resource transformation, not an unclosed lease.

## Independent definitions

The definitions exist identically in every run, including the counterfactual.
The counterfactual removes only the scheduled presence of X.

```yaml
commitment_X:
  id: commitment_X
  actor: process_X
  action: allocate_one_unit
  reads:
    - S.available_units
  writes:
    - S.available_units
    - S.durable_allocations.commitment_X
  gate: S.available_units >= 1
  terminal_success:
    - transform one available S unit into allocation committed_by_X
  terminal_failure:
    - no resource acquired

commitment_Y:
  id: commitment_Y
  actor: process_Y
  action: allocate_one_unit
  reads:
    - S.available_units
  writes:
    - S.available_units
    - S.durable_allocations.commitment_Y
  gate: S.available_units >= 1
  terminal_success:
    - transform one available S unit into allocation committed_by_Y
  terminal_failure:
    - no resource acquired
```

The action identifiers may be the same because each definition owns only its
own commitment identity and permitted allocation path. Their shared gate is
ordinary resource admission, not a relationship declaration.

## Prohibitions

The following are forbidden in definitions, resolver code, ledger derivation,
and fixture setup:

```text
X references Y
Y references X
if X succeeded: fail Y
if Y succeeded: fail X
callback(X → Y)
pair-specific interaction rule
fixture branch selector in a canonical record
```

The source audit must prove that X and Y share only the declared `S` paths.
They may not carry a foreign commitment ID, actor ID, action result, or special
case for their counterpart.

## One canonical decision boundary

All active commitments derive observations and beliefs from one immutable R0
snapshot. The fixture supplies an ordinary canonical queue ordering as input;
it is not a production precedence policy.

```text
R0
  S.available_units = 1
  X due
  Y due
        ↓
immutable batch snapshot = R0
        ↓
canonical queue / sequential working revalidation
        ↓
R1
```

For each proposal the ledger records both `batch_pre_state_hash` and
`working_pre_state_hash`. The former binds both commitments to R0; the latter
shows why a later commitment may become ineligible after an earlier valid
commit.

## Required executions

### Primary — X first

```text
R0: S available = 1; X due; Y due
canonical queue: X, Y

X revalidates → S gate passes → transforms unit into X allocation
Y revalidates → S gate fails → terminal failure / no resource acquired

R1: S available = 0; allocation = X; X succeeded; Y failed
```

### Counterfactual — X absent

```text
same R0 definition set
same Y definition, gate, seed, rule version, and queue position
only X scheduled presence is removed

Y revalidates → S gate passes → transforms unit into Y allocation

R1: S available = 0; allocation = Y; Y succeeded
```

### Permutation witness — Y first

```text
same R0; X and Y due
same definition hashes
only canonical fixture queue reverses: Y, X

Y revalidates → S gate passes → transforms unit into Y allocation
X revalidates → S gate fails → terminal failure / no resource acquired

R1: S available = 0; allocation = Y; Y succeeded; X failed
```

This witness proves the primary result is not hidden X-priority semantics.
The fixture order is an explicit input to the canonical queue, not law derived
from the names X or Y.

## Acceptance gates

1. X and Y definitions hash identically across primary, counterfactual, and permutation runs.
2. Counterfactual removes only X scheduling/presence; it does not alter Y's definition, gate, state, seed, rule version, or source.
3. Both active commitments observe the same immutable R0 batch snapshot.
4. Each commitment reads only its own definition plus the declared ordinary `S` gate and writes only its permitted `S` allocation.
5. Primary X-first result is X success / Y `S.available_units` failure.
6. Counterfactual result is Y success with no X allocation.
7. Permutation result is Y success / X `S.available_units` failure.
8. Every success transforms exactly one capacity unit into a durable allocation; every failure records no resource acquired. No reservation or capacity leak remains.
9. The ledger reconstructs ordering, common batch snapshot, working-state revalidation, gate values, mutations, and terminal resource disposition without final-state inference.
10. Identical inputs reproduce byte-equivalent records, ledgers, definition hashes, and artifacts.
11. Source and definition audits prove zero cross-commitment references or pair-specific interaction rules.
12. No final canonical record contains a branch selector, counterpart reference, callback result, or special-case interaction fact.

## DAG plan

```text
freeze independent-definition contract
        │
        ├──────────────┐
        ▼              ▼
canonical resolver    definition/source audit
        │              │
        └──────┬───────┘
               ▼
primary / counterfactual / permutation runs
               │
               ▼
replay + lifecycle + provenance verification
               │
               ▼
release artifacts + self-excluding manifest
               │
               ▼
evidence seal
```

## Explicit boundary

This proof does not authorize Unreal work, physical evidence, new city content,
general planning, additional agents, economy, map scale, split crews,
multiplayer, networking, rollback, repair, or a generalized resource system.

## Changelog

### 0.1.0 — 2026-08-26

- Froze the canonical-only shared-state commitment interference proof.
- Required primary, X-absent counterfactual, and reversed-order permutation evidence with identical isolated definition hashes.
- Prohibited cross-commitment references, callbacks, pair rules, and canonical branch selectors.
