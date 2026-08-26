# Crew Deployment Opportunity-Cost Proof

**Version:** 0.1.0
**Status:** Frozen implementation specification. Only this proof is authorized.
**Simulation version:** 0.7.0-draft.16
**Parent:** [Co-op Open-City FPS Simulation — v0.7 Working Continuation](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)

## Claim

Prove the first player-facing city law:

> **One aircraft-bound crew can spend its exclusive physical opportunity in one materialized domain while active-world time continues everywhere else.**

Deployment grants evidence-generation opportunity only. It never grants a runtime direct authority to commit city state, pause unattended processes, or veto remote commitments.

## Fixed scope

```yaml
crew_deployment_model:
  crew_id: crew_01_to_04
  players: 1..4
  aircraft_id: aircraft_01
  active_deployment_commitments_per_crew: 1
  split_fireteams: prohibited

control:
  intelligence_variance: excluded
  initial_record: identical_R0
  seed: identical
  autonomous_schedule: identical
```

`A` is the hub. `B` holds the existing fire and Ash Bridge approach. `C` holds the existing gang seizure. `D` is a neutral airborne holding domain, not a new site simulation.

## Deployment authority

The hub emits a player command, not a city mutation:

```text
player selects B | C | D
  → crew_deployment_request
  → canonical validation
  → reserve crew + aircraft
  → commit deployment
  → takeoff; active-world clock begins
```

Required deployment gates:

```yaml
crew_available: true
aircraft_available: true
crew_has_no_active_deployment: true
destination_is_valid: true
deployment_origin_is_hub: true
```

Acceptance atomically creates:

```yaml
deployment:
  commitment_id: crew_deployment_<B|C|D>_t0
  destination: B | C | D
  state: active
  start_time: t0/00
  interaction_domain_available_at: t0/05

resources:
  crew_01_to_04: reserved
  aircraft_01: reserved

world:
  active_world: true
```

A second deployment request while this commitment is active must evaluate every gate, reject on exclusivity, create no second domain, and append only rejected ledger provenance.

## Time and authority schedule

```text
t0/00  deployment transaction commits; takeoff begins active-world time
t0/05  exactly the selected interaction domain may generate crew physical evidence
t0/10  fire spread decision
t0/20  police E_AB admission decision
t0/25  C disruption interaction window (C branch)
t1/15  police exits E_AB at B, if admitted
t1/20  police E_BC admission, if at B
t2/15  police reaches C, if admitted
t2/40  gang seizure completion decision
```

Scheduler boundary construction must retain the immediate parent record hash, a named `scheduler_clock_advance` derivation, and the hash of the derived transaction pre-state. It changes only `clock` before that boundary's transaction executes.

## Exact local evidence contracts

### B — fire containment

At `t0/05`, a materialized `fire_control_valve_B_01` may emit only:

```yaml
proposal_id: physical_contain_fire_B_deployment_0001
target:
  kind: fire_control
  id: fire_control_valve_B_01
  area: B
observed_outcome: {state: contained, event_sequence: 1}
proposed_mutations:
  - B.fire_containment = true
```

The canonical proposal gate additionally requires the active deployment domain to equal `B` and the clock to be at or after `t0/05`. At `t0/10`, fire spread requires `B.fire_containment == false`. Therefore accepted containment prevents spread; it does not undo spread after the fact.

### C — seizure disruption

At `t0/25`, a materialized `gang_signal_relay_C_01` may emit only:

```yaml
proposal_id: physical_disrupt_seizure_C_deployment_0001
target:
  kind: gang_signal_relay
  id: gang_signal_relay_C_01
  area: C
observed_outcome: {state: disabled, event_sequence: 1}
proposed_mutations:
  - C.crew_disruption = true
```

The canonical proposal gate additionally requires the active deployment domain to equal `C` and the clock to be at or after `t0/05`. At `t2/40`, gang seizure completion requires both `C.crew_disruption == false` and no police at C.

Remote city state may change only through autonomous canonical commitments or canonical propagation from these accepted local consequences.

## Branches

All branches begin from byte-identical R0. They differ only in accepted deployment destination and crew physical input sequence.

```text
B: contain fire before t0/10
   → E_AB remains open → police reaches C → gang seizure fails → C contested

C: disrupt seizure before t2/40
   → fire closes E_AB → police fails → disruption gate fails seizure → C contested

D: no B/C physical evidence
   → fire closes E_AB → police fails → gang seizure succeeds → C gang
```

## Acceptance

- deployment request is a canonical transaction, not runtime authority;
- exactly one materialized crew interaction domain exists;
- second deployment rejection proves exclusivity;
- B and C evidence is physically emitted by Unreal and canonically accepted only in its matching active domain;
- no crew evidence can originate remotely or during D;
- all autonomous fire, police, and gang effects resolve from the same canonical city record;
- each branch replays byte-identically, and all scheduler transitions retain parent provenance;
- a fresh Unreal process materializes each final B/C/D record alone, without branch knowledge; and
- Unreal writes proposals only, never records, deployment commitments, or ledgers.

## Boundary

No split fireteams, intelligence uncertainty, repair, new factions, additional sites, multiplayer arbitration, or generalized physical-action framework are authorized. This proof defines two exact evidence contracts only.
