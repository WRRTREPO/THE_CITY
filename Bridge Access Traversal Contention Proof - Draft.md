# Bridge Access Traversal Contention Proof — Draft

**Version:** 0.1.0-draft.0  
**Status:** Prepared implementation specification. Not frozen; no implementation has begun.  
**Opened:** 2026-08-26  
**Parent continuation:** [Co-op Open-City FPS Simulation — v0.7 Working Continuation](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)

## Purpose

Prove the first live contention between the two already-proven halves of the city machine:

```text
crew physical consequence proposal
        ×
already-due canonical police edge-entry proposal
        ↓
one authoritative decision boundary
        ↓
deterministic, non-retroactive route history
```

This is not a new city system. It uses the existing `E_AB` bridge, `police_unit_01`, bridge-access destruction consequence, lease model, and Unreal proof project.

## Inherited law under test

The following laws are already established by the v0.7 continuation and frozen Ash Crossing kernel:

- one strategic decision boundary begins from one immutable authoritative snapshot;
- proposals are canonically ordered, then revalidated one at a time against a working record;
- a physical consequence is only a proposal until the canonical layer accepts it;
- `proposal.source_record_hash == transaction.pre_state_hash` is the optimistic-concurrency gate;
- edge gates are checked when entering an edge; later closure cannot retroactively invalidate a validly entered segment; and
- every terminal transition releases, consumes, transfers, or transforms its resources and records that disposition.

This proof must not revise those laws in code. It exists to exercise their interaction.

## Candidate route-admission clarification

The implementation must be capable of representing the following lawful transient state. This wording is a candidate clarification pending freeze:

> `route.open` and `route.capacity` govern new edge admission only. A valid existing edge lease is traversal authority for its already-entered segment and survives a later admission closure until scheduled exit or an explicitly defined traversal-invalidating event.

Consequently, this state is valid:

```yaml
E_AB:
  open: false
  capacity: 0
  leases:
    - police_dispatch_C_t0:E_AB
```

`len(leases) <= capacity` is therefore **not** a global route invariant. It applies only to a proposed new admission before that lease is created.

## Fixed scope and initial state

```text
scenario_id: ash-crossing-bridge-contention-v1
simulation_version: next continuation revision after freeze
strategic_decision_boundary: t0
route: E_AB
physical target: bridge_access_point_E_AB_01
```

Generate one canonical seed `R0` for both cases. Its relevant authoritative facts are:

```yaml
routes:
  E_AB:
    open: true
    capacity: 1
    bridge_access_point_state: intact
    leases: []
  E_BC:
    open: true
    capacity: 2
    leases: []

agents:
  police_unit_01:
    location: A
    availability: available
    units: 1

commitments: {}

areas:
  B:
    fire_intensity: 4
  C:
    police_present: 0
    owner: contested
```

No fire proposal is due in this proof. Fire intensity remains `4`; it is retained only to prove that bridge closure originated from the crew consequence, not the fire process.

## Shared decision boundary

The physical proposal and police entry proposal derive from the same immutable start snapshot:

```text
R0
 ↓
one atomic decision boundary at t0
 ↓
immutable transaction pre-state = R0
 ↓
physical proposal P: crew.destroy_E_AB, source_record_hash = hash(R0)
police proposal Q: police.enter_E_AB, observations/beliefs from R0
 ↓
canonical queue, sequential working-record revalidation
 ↓
one committed record for the selected case
```

The Unreal proposal does not select its own canonical order. It supplies physical evidence only. The test fixture supplies the named canonical queue position before the batch closes. Local Unreal clock time, process scheduling, and transport arrival time are evidence metadata only; none may determine strategic order.

Each case has its own fixed canonical input sequence. Replay means the same `R0`, proposal bytes, logical queue, simulation version, and rules reproduce its own byte-identical record and ledger.

## Proposals

### `P`: crew bridge-access destruction

`P` is emitted by the existing Unreal proof path after a crew pawn physically destroys `bridge_access_point_E_AB_01`.

It retains the established authority boundary:

```text
Unreal physical outcome
  → immutable evidenced proposal P
  → canonical validation
  → accept or reject
```

Required proposal facts:

```yaml
proposal_id: physical_destroy_E_AB_contention_0001
source:
  system: crew_physical_simulation
  source_record_hash: hash(R0)
instigator:
  kind: crew
  id: crew_01_to_04
target:
  kind: bridge_access_point
  id: bridge_access_point_E_AB_01
  route: E_AB
observed_outcome:
  state: destroyed
evidence:
  physical_actor_id: bridge_access_point_E_AB_01
  destruction_state: destroyed
  evidence_digest: deterministic_from_proposal_fields
proposed_mutations:
  - E_AB.open = false
  - E_AB.capacity = 0
  - E_AB.bridge_access_point.state = destroyed
```

`P` must not require spare route admission capacity. It may validly destroy an occupied bridge. Its canonical gates still require the target to be intact and the route to be open in the working record.

### `Q`: police entry into `E_AB`

`Q` is the existing first-segment traversal action, narrowed to entry only:

```yaml
proposal_id: police_dispatch_C_t0.enter_E_AB
owner: police_unit_01
commitment: police_dispatch_C_t0
source_snapshot_hash: hash(R0)
gates_at_commit:
  police availability: available
  E_AB.open: true
  E_AB new-admission capacity: len(E_AB.leases) < E_AB.capacity
effects_on_success:
  police availability: reserved
  E_AB lease: police_dispatch_C_t0:E_AB
  commitment state: active
  current_segment: E_AB
  last_valid_location: A
effects_on_failure:
  police location: A
  police availability: available
  dispatch result: failed_gate
  E_AB leases: []
```

`Q` observes `R0`; its listed gates are always re-evaluated against the working record when its canonical turn arrives.

## Case 1 — destruction first

The test fixture gives `P` its canonical queue position before `Q`:

```text
t0/15/E_AB/crew_01_to_04.destroy_E_AB
t0/20/E_AB/police_unit_01.enter_E_AB
```

Expected sequence:

```text
P validates against R0 and commits bridge destruction
    ↓
working E_AB: open false, capacity 0, access destroyed, leases []
    ↓
Q revalidates
    ↓
E_AB.open gate fails
    ↓
Q fails; police remains A and available
```

Required canonical result:

```yaml
E_AB:
  open: false
  capacity: 0
  bridge_access_point_state: destroyed
  leases: []
police_unit_01:
  location: A
  availability: available
  dispatch_to_C:
    result: failed_gate
    failed_gate: E_AB.open
commitments:
  police_dispatch_C_t0: absent
```

## Case 2 — entry first

The test fixture gives `Q` its canonical queue position before `P`:

```text
t0/20/E_AB/police_unit_01.enter_E_AB
t0/25/E_AB/crew_01_to_04.destroy_E_AB
```

Expected sequence:

```text
Q validates against R0 and commits entry
    ↓
E_AB lease acquired; police traversal is active on E_AB
    ↓
P revalidates against the working record and commits destruction
    ↓
new admission closes, existing E_AB traversal remains lawful
```

The proof must preserve the following serialized or inspectable intermediate state **after the batch and before scheduled exit**:

```yaml
E_AB:
  open: false
  capacity: 0
  bridge_access_point_state: destroyed
  leases:
    - police_dispatch_C_t0:E_AB
police_unit_01:
  location: A
  availability: reserved
commitments:
  police_dispatch_C_t0:
    state: active
    current_segment: E_AB
    last_valid_location: A
```

At the already-defined scheduled `t1/15` exit boundary:

```text
police exits E_AB at B
  → releases E_AB lease
  → retains the active traversal commitment and reserved unit
  → records B as exact last valid location
```

Required post-exit state:

```yaml
E_AB:
  open: false
  capacity: 0
  bridge_access_point_state: destroyed
  leases: []
police_unit_01:
  location: B
  availability: reserved
commitments:
  police_dispatch_C_t0:
    state: active
    current_segment: null
    last_valid_location: B
    next_gate: E_BC at t1/20
```

The proof ends at `t1/15`. It must not enter, reject, reserve, or otherwise evaluate `E_BC`; that is a later entry boundary and outside this proof.

## Canonical validation, mutation, and ledger

The transaction layer must create a batch header recording:

```yaml
decision_boundary: t0
transaction_pre_state_hash: hash(R0)
input_sequence_id: case_1_destruction_first | case_2_entry_first
proposal_ids:
  - physical_destroy_E_AB_contention_0001
  - police_dispatch_C_t0.enter_E_AB
```

Each proposal ledger entry must retain the inherited provenance fields and additionally make the race inspectable:

- immutable `R0` snapshot hash and working pre-/post-state hashes;
- canonical execution sequence and fixture-supplied queue position;
- proposal observations and beliefs from `R0`;
- all gates evaluated at its working-record turn;
- route lease acquisition, absence, or release;
- physical evidence digest and crew provenance for `P`; and
- downstream traversal eligibility changes.

The intermediate Case 2 record is proof evidence, not a separate player-visible strategic decision. It may be serialized as a test artifact solely to prove the lawful closed-route-plus-lease state.

## Fresh materialization

For each final case record, destroy the preceding Unreal process and start a fresh process from that final canonical record only.

Both fresh scenes must show a destroyed, impassable bridge access point and no fire. They must differ only in their authoritative police consequence:

```text
Case 1: police remains at A after failed E_AB admission.
Case 2: police has reached B after completing the valid E_AB segment.
```

Unreal may not infer, repair, or commit either result. It only expresses the selected authoritative record.

## Acceptance matrix

| Test | Required proof |
| --- | --- |
| Shared snapshot | `P` and `Q` both bind to `hash(R0)`; one batch owns their resolution. |
| Destruction-first | `P` commits, `Q` fails `E_AB.open`, police remains at A, and no lease exists. |
| Entry-first intermediate | `Q` acquires the sole E_AB lease; `P` closes new admission while that lease remains valid. |
| Entry-first exit | At `t1/15`, police reaches B and releases exactly the E_AB lease. |
| Future admission | A new E_AB admission after destruction fails; no stale or phantom lease exists. |
| E_BC isolation | No E_BC gate, lease, or police arrival at C is evaluated before `t1/20`. |
| Mutation isolation | Only bridge-access facts plus mandatory police/traversal facts caused by the ordered proposals change. Fire remains 4; Docklands remains contested. |
| Replay | Each fixed case input reproduces byte-identical final record, intermediate artifact where applicable, and ledger. |
| Ledger reconstruction | The batch header and entries establish why `P` or `Q` won without inference from final state. |
| Fresh materialization | A fresh Unreal process independently renders each final authoritative record with no hidden prior process state. |
| Authority audit | Unreal writes only `P`; it cannot write batch, intermediate, final record, or ledger. |

## Intended implementation surface after freeze

Implementation should remain narrow:

```text
proof_kernel/
  contention.py                 # new batch fixture and canonical resolver
  test_contention.py            # acceptance matrix
  kernel.py                     # reuse traversal conventions; no regression
  roundtrip.py                  # reuse proposal validation only if behavior remains pinned

CityMaterializationProof/
  existing bridge access actor  # emits P only
  selected-record materializer  # reads Case 1 / Case 2 records only
```

The existing eight kernel tests, five round-trip tests, and two Unreal authority-boundary tests remain required regressions. No code, record, or Unreal source is modified by this draft.

## Explicitly out of scope

- real network arrival, multiplayer arbitration, rollback, or client trust;
- bridge repair, damage gradation, fire behavior, or new physical consequence types;
- E_BC traversal, police arrival at C, factions, fronts, economy, or additional areas;
- general save/load beyond canonical test artifacts; and
- map-scale streaming or city expansion.

## Freeze boundary

Freeze this draft only if the candidate route-admission clarification, exact case records, queue positions, intermediate evidence, and acceptance matrix are accepted. Then implement exactly this proof and nothing adjacent.

## Changelog

### 0.1.0-draft.0 — 2026-08-26

- Prepared the minimal contention proof between an Unreal-originated bridge-destruction proposal and an already-due canonical police E_AB entry.
- Defined separate destruction-first and entry-first cases from one immutable R0, including the lawful closed-route-plus-existing-lease intermediate state.
- Prohibited Unreal wall-clock or transport arrival from determining canonical order.
