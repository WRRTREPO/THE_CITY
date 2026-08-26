# Three-Area Causal Proof Kernel — Draft

**Version:** 0.1.0  
**Status:** Frozen implementation specification; not implemented.  
**Opened:** 2026-08-26  
**Frozen:** 2026-08-26  
**Parent track:** [Co-op Open-City FPS Simulation — v0.7 Working Continuation](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)

## Purpose

Prove the smallest useful instance of the persistent causal city before map-scale work. The kernel must demonstrate that a fire, public-service response, two factions, a shared route, and an occupied crew can produce a deterministic, inspectable, non-scripted city outcome.

This document specifies the test case. It does not establish new city law and it does not authorize implementation beyond this kernel.

## Changelog

### 0.1.0 — 2026-08-26

- Defined scheduled police traversal, edge-capacity leases, route-gate timing, and exact failure locations.
- Scoped rival defense to the named gang-seizure commitment and defined its expiry.
- Defined terminal resource disposition for police traversal, gang seizure, and rival defense commitments.
- Froze the corrected scenario as the implementation specification.

### 0.1.0-draft.1 — 2026-08-26

- Defined the scheduled police-arrival action required by the no-fire counterfactual.
- Added changelog discipline to the standalone kernel specification.

### 0.1.0-draft.0 — 2026-08-26

- Specified the initial three-area, two-faction, police, fire, and crew-commitment proof kernel.

## Fixed simulation identity

```text
scenario_id: ash-crossing-v1
simulation_version: 0.7.0-draft.4
seed: ash-crossing-v1/0001
strategic_decision_interval: 1 active-world minute
crew_commitment_window: t0 through t2
```

The scenario uses the deterministic transaction and provenance law defined in the v0.7 continuation. All identifiers and canonical ordering values below are fixed for this proof.

## Canonical area graph

```text
Area A: Inland Hub
    │  E_AB — Ash Bridge — travel: 1 minute
    ▼
Area B: Bridgehead
    │  E_BC — East Road — travel: 1 minute
    ▼
Area C: Docklands Yard
```

| ID | Type | Initial state | Strategic role |
| --- | --- | --- | --- |
| `A` | area | Police unit available; crew begins a bank-containment commitment here. | Source of the only public-service response. |
| `B` | area | Fire intensity `4`; fuel `1`; bridge is initially open. | Shared route gate and fire location. |
| `C` | area | Gang control `62`; rival control `38`; police presence `0`; owner `contested`. | Faction contest and materialization target. |
| `E_AB` | route | `A ↔ B`; travel `1`; capacity `1`; gate `bridge_open = true`; unavailable when fire intensity reaches `5`. | Required first leg of the police route. |
| `E_BC` | route | `B ↔ C`; travel `1`; capacity `2`; gate `east_road_open = true`. | Required second leg of the police route. |

`C` changes owner to `gang` only when all of these are true in the threshold phase:

```text
gang_control >= 70
police_present_C == 0
```

Control is conserved between the two factions: a change to gang control is an equal inverse change to rival control.

## Agents, process, and crew commitment

| ID | Type and location | Objective | Initial resources / state |
| --- | --- | --- | --- |
| `gang_docklands` | faction agent at `C` | Gain ownership of `C`. | personnel `6`; equipment `1`; local intelligence `1`; supply `1`; control `62`. |
| `rival_docklands` | faction agent at `C` | Prevent gang ownership of `C`. | personnel `4`; supply `1`; control `38`. |
| `police_unit_01` | public-service agent at `A` | Reach `C` and contain the faction contest. | units `1`; route knowledge `E_AB → E_BC`; response priority `high`. |
| `fire_bridgehead` | fire process at `B` | Spread while fuel remains. | intensity `4`; fuel `1`; next decision `t0`. |
| `crew_01_to_04` | player crew at `A` | Complete the bank-containment commitment. | unavailable for movement or intervention in `C` from `t0` through `t2`. |

The crew commitment is a real input sequence: at `t0`, the crew accepts `bank_containment`; it remains at `A` and takes no action that affects `B` or `C` through `t2`.

## Commitment lifecycle and traversal semantics

Every time-bearing action in this kernel is a commitment with an identifier, owner, state, resource lease, gate-check schedule, and terminal resource disposition:

```text
planned → active → succeeded | failed | cancelled
```

`police_unit_01.dispatch_to_C` creates a scheduled traversal commitment:

```yaml
id: police_dispatch_C_t0
route: [E_AB, E_BC]
departure: t0
arrival: t2
unit_reserved: true
current_progress:
  t0/20: enter E_AB from A
  t1/15: arrive B; release E_AB capacity lease
  t1/20: enter E_BC from B
  t2/15: arrive C; release E_BC capacity lease
```

Route gates are checked only when the unit is about to enter an edge. Once the unit has validly entered an edge, a later closure cannot retroactively invalidate that traversal segment. A failure before entering `E_AB` leaves the unit at `A`; a failure to enter `E_BC` leaves it at `B`. On any traversal failure, the current edge lease is released and the unit becomes available at its exact last valid location.

The proof uses edge-capacity leases rather than an abstract whole-route reservation. `E_AB` is leased only from `t0/20` to `t1/15`; `E_BC` is leased only from `t1/20` to `t2/15`.

## Feasible actions and economy of action

### `fire_bridgehead.spread`

```text
phase: 10_environment
duration: immediate
gates: fuel >= 1 and intensity == 4
cost: fuel -1
effects:
  intensity +1
  E_AB.bridge_open = false
  E_AB.capacity = 0
```

### `police_unit_01.dispatch_to_C`

```text
phase: 20_service_response
duration: 2 minutes (E_AB + E_BC)
gates at start:
  units >= 1
  E_AB.bridge_open == true
  E_AB.capacity >= 1
cost: reserve 1 police unit; acquire E_AB capacity lease
effects on success:
  create police_dispatch_C_t0 traversal commitment
  enter E_AB at t0/20
effects on failure:
  retain unit at A; record failed start gate or unavailable E_AB capacity
```

### `police_unit_01.arrive_at_C`

```text
phase: 20_service_response
duration: immediate at t2/15 after E_BC traversal
gates:
  police_dispatch_C_t0 is active
  police_dispatch_C_t0.current_segment == E_BC
  E_BC traversal progress is complete
effects on success:
  police_unit_01.location = C
  police_present_C = 1
  release E_BC capacity lease
  complete police_dispatch_C_t0
  transform reserved police unit into deployed police presence at C
effects on failure:
  release current edge capacity lease; retain the unit at its last valid location; record the failed route gate
```

### `rival_docklands.defend_C`

```text
phase: 30_faction_action
action priority: 10
duration: through the terminal state of gang_docklands.seize_C_t0
gates: personnel >= 3 and supply >= 1
cost: reserve 3 personnel; supply -1
effects:
  create defense_against_seize_C_t0
  target: gang_docklands.seize_C_t0
  magnitude: 2
  expiry: target succeeds, fails, or is cancelled
terminal disposition:
  remove defense_against_seize_C_t0
  release 3 rival personnel at C
```

The defense commitment targets the canonical gang action identity selected from the shared `t0` snapshot. If `gang_docklands.seize_C_t0` does not become active in phase `30`, the defense commitment fails at `t0/90`, removes itself, and releases its personnel. It never becomes a generic persistent area modifier.

### `gang_docklands.begin_seize_C`

```text
phase: 30_faction_action
action priority: 20
duration: 2 minutes
gates at start:
  personnel >= 5
  equipment >= 1
  local_intelligence >= 1
  gang_control_C >= 60
cost: commit 5 personnel; supply -1
effects on success:
  create gang_docklands.seize_C_t0 commitment
  schedule gang_docklands.complete_seize_C at t2
terminal disposition:
  on success, failure, or cancellation: release 5 gang personnel at C
  supply remains consumed and is not refunded
```

### `gang_docklands.complete_seize_C`

```text
phase: 40_faction_resolution
duration: immediate
gates at completion:
  gang_docklands.seize_C_t0 is active
  police_present_C == 0
effect:
  control transfer = 14 - defense_against_seize_C_t0.magnitude
  gang_control_C += control transfer
  rival_control_C -= control transfer
terminal disposition:
  mark gang_docklands.seize_C_t0 succeeded or failed
  apply its terminal resource disposition
  expire defense_against_seize_C_t0 and apply its terminal resource disposition
```

With the specified commitment-scoped defense magnitude `2`, a valid gang completion transfers `12` control: gang control becomes `74` and rival control becomes `26`. No generic area-level `defense_pressure` persists after the gang commitment terminates.

On a failed gang completion, no control transfers. The gang seizure becomes `failed`, both the gang and rival personnel leases are released, the defense commitment expires, and the gang's consumed supply remains consumed.

### Derived threshold evaluation

```text
phase: 90_derived_state
if gang_control_C >= 70 and police_present_C == 0:
  C.owner = gang
  expose player-readable gang-control front at C
```

The front is emitted only here, after the underlying commitments and threshold have changed authoritative facts.

## Canonical ordering at `t0`

All agents and processes decide from the same immutable `t0` snapshot, where `E_AB.bridge_open == true`.

The selected proposals are committed in this canonical order:

| Sequence | Proposal | Expected commit result |
| --- | --- | --- |
| `t0/10/B/fire_bridgehead.spread` | Fire spreads. | Committed: intensity becomes `5`; `E_AB` closes. |
| `t0/20/A/police_unit_01.dispatch_to_C` | Police dispatches using the snapshot-observed route. | Revalidation fails because `E_AB.bridge_open == false`; failure is ledgered. |
| `t0/30/C/rival_docklands.defend_C` | Rival defends against the named gang seizure. | Committed: `defense_against_seize_C_t0` is active with magnitude `2`. |
| `t0/30/C/gang_docklands.begin_seize_C` | Gang begins the seizure. | Committed: completion scheduled for `t2`. |
| `t0/90/C/derived_state` | Threshold pass. | No ownership change yet; gang control remains `62`. |

At `t2`, the only relevant due faction resolution is `gang_docklands.complete_seize_C`:

| Sequence | Proposal | Expected commit result |
| --- | --- | --- |
| `t2/40/C/gang_docklands.complete_seize_C` | Gang completes the seizure. | Committed: police is absent; control transfers `12`; gang control becomes `74`; both gang seizure and rival defense commitments clean up their resource leases. |
| `t2/90/C/derived_state` | Control threshold evaluation. | Committed: `C.owner = gang`; player-readable front becomes eligible. |

## Expected authoritative result

At the end of `t2`, the canonical city record must contain at least:

```yaml
bridgehead:
  fire_intensity: 5
  bridge_open: false
  bridge_capacity: 0

police_unit_01:
  location: A
  availability: available
  dispatch_to_C:
    result: failed_gate
    failed_gate: E_AB.bridge_open

docklands_yard:
  gang_control: 74
  rival_control: 26
  police_present: 0
  owner: gang

commitments:
  gang_docklands.seize_C_t0: succeeded_and_cleaned_up
  defense_against_seize_C_t0: expired_and_cleaned_up

fronts:
  gang_control_C:
    visible_state: gang_controls_docklands_yard
```

This result must arise from the committed action chain. No direct front-stage mutation is permitted.

## Required counterfactual

Run the same canonical initial record and crew input, except remove the fire process's `spread` proposal at `t0`.

Expected divergence:

1. `E_AB` remains open.
2. `police_unit_01.dispatch_to_C` commits, enters `E_AB` at `t0/20`, arrives at `B` at `t1/15`, enters `E_BC` at `t1/20`, and arrives at `C` at `t2/15`.
3. `police_unit_01.arrive_at_C` commits at `t2/15`, releases its final edge lease, and transforms the reserved unit into `police_present_C = 1`.
4. `gang_docklands.complete_seize_C` fails its `police_present_C == 0` completion gate in phase `40_faction_resolution`.
5. `C.owner` remains `contested`; no gang-control front is exposed.

This counterfactual proves that the fire affects control only through authored graph, gate, resource, action, and threshold laws. There is no direct `fire → gang capture` rule.

## Replay, provenance, and inspection acceptance

For both the primary run and the counterfactual, prove:

```text
same canonical initial record
+ same seed and random-draw sequence
+ same ordered crew input sequence
+ same simulation version
────────────────────────────────────────────
= byte-equivalent canonical causal record
```

The causal ledger must include every listed proposal and every derived mutation, including the police dispatch failure, traversal segment entries and exits, capacity leases, commitment state changes, scoped-defense expiry, and all terminal resource dispositions. For each entry, inspection must recover the decision time, actor/process, snapshot and belief inputs, eligible actions, selected action, costs, gate values, result, pre-state and post-state references, threshold result, and downstream eligibility change.

## FPS materialization acceptance

After `t2`, send the crew from `A` to `C`. Before the crew can observe `B` or `C`, promote both areas from the canonical result.

The local first-person scene must express these facts:

- `B` contains the active fire consequence and an impassable Ash Bridge; it does not display an open police route.
- `C` contains gang control: visible occupation, changed access, absent police response, and rival displacement consistent with the record.
- The scene may choose incidental geometry, NPC positions, and ambient behavior, but it cannot materialize police control, an open bridge, or rival ownership.

On later compression, only new consequential player effects may modify the city record. The established `t2` result may be countered through new valid actions; it may not be rerolled or erased by arrival.

## Completion boundary

This scenario is frozen at `0.1.0` and ready to implement. Do not revise it or add map scale, extra factions, additional services, more hazards, or scripted front outcomes before its primary run, counterfactual, replay proof, causal ledger, and FPS materialization acceptance are complete.
