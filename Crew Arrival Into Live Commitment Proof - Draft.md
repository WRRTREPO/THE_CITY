# Crew Arrival Into Live Commitment Proof

**Version:** 0.1.0-draft.3
**Status:** Candidate freeze under review. Implementation is not authorized.
**Simulation version:** 0.7.0-draft.20 — fixed for this proof.
**Parent:** [Co-op Open-City FPS Simulation — v0.7 Working Continuation](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)

## Claim

Prove continuity of causality through player arrival:

> **Crew arrival does not create, select, restart, suspend, or advance a causal process. It grants physical access to the current authoritative state and allows new evidence to enter that process.**

The crew must be able to land inside a gang claim already underway, change one current causal input through physical play, and let the same canonical claim commitment resolve from the resulting record.

## Fixture-only vocabulary law

> **Scenario nouns are proof fixtures, not generalized city ontology.**

`survey`, `marshal`, `ingress`, `perimeter`, `relay`, `claim`, gang control,
and their particular gates establish only this demonstrated causal shape. They
do not become mandatory primitives for other agents, commitments, city
processes, or production content.

The reusable machine law is only:

```text
completed actions → durable facts → active future commitment
→ physical evidence opportunity → canonical revalidation → durable history
```

No production abstraction may be named after this fixture. In particular, this
proof does not authorize `GangClaimSystem`, `TerritoryRelayState`, a five-step
takeover pipeline, or an ownership-specific commitment framework.

## Proof topology

This proof retains one shared aircraft-bound crew and one canonical city. It adds no scale, split deployment, intelligence uncertainty, network authority, repair, or generalized action framework.

```text
HUB A
  │ canonical deployment; active-world time begins at takeoff
  │
  └──── crew travels to C ────────────────────────────────┐
                                                            │
CANONICAL GANG CLAIM AT C                                  │
  survey                                                     │
  → marshal personnel                                       │
  → secure ingress                                          │
  → establish perimeter                                     │
  → activate relay                                          │
  → begin claim commitment ─── Rarrival ─── crew lands ─────┘
                               │
                               ├── no intervention → claim resolves
                               └── physical relay disable → claim revalidates
```

`C` remains Docklands Yard. `A` remains the crew hub. The gang claim is an agent/process goal using authored action primitives, not an arrival-specific mission sequence.

## Deployment, access, and arrival are distinct

This proof must not conflate a selected destination with physical capability. It
freezes three distinct concepts:

```text
deployment destination
  = the canonical crew commitment selected at takeoff: C
physical-access eligibility
  = deterministic eligibility for the crew runtime to originate evidence at C
strategic arrival mutation
  = none
```

```yaml
deployment:
  commitment_id: crew_deployment_C_live_001
  state: active
  destination: C
  physical_access_at: t0/27
```

```text
physical_access(C) :=
    deployment.state == active
    AND deployment.destination == C
    AND canonical_clock >= deployment.physical_access_at
```

Before `t0/27`, the deployment destination is C but `physical_access(C)` is
false, so the crew runtime has no evidence surface there. At or after `t0/27`,
physical access is true only because canonical time has reached the
precommitted travel boundary. No strategic fact, claim gate, threshold,
schedule, or commitment mutates merely because this predicate becomes true.

## Non-negotiable authority law

An authored action primitive is lawful:

```text
relay.active == true → materialize active relay representation
```

An arrival-specific event selector is forbidden:

```yaml
mission_variant: gang_takeover_stage_4
arrival_stage: 4
encounter_type: relay_defense
spawn_takeover_sequence: true
```

Unreal receives the authoritative arrival record, materializes its facts, and may emit physical evidence. It may not select a mission stage, run a strategic timer, resolve the claim, mutate ownership, alter a claim commitment, serialize a canonical record, or append a causal ledger entry.

## Frozen proof identity

No replay-significant identity remains contextual.

```yaml
scenario_id: crew-arrival-live-commitment-v1
scenario_version: 0.1.0
simulation_version: 0.7.0-draft.20
record_schema: CrewArrivalLiveCommitmentRecord.v1
seed: crew-arrival-live-commitment-v1/0001
```

## Causal scenario

### Canonical pre-arrival history

The gang's objective is to claim control of C. Each completed action is a canonical action with gates, costs, terminal resource disposition, provenance, and a durable result. A player is already deployed with destination C and travelling; no crew physical evidence is available until derived physical access becomes true at arrival.

```text
t0/00  crew deployment to C commits; active-world time begins
t0/04  gang survey_C succeeds       → C.gang_intelligence = true
t0/08  gang marshal_C succeeds      → C.gang_personnel_present = 6
t0/12  gang secure_ingress succeeds → C.ingress_secured = true
t0/16  gang establish_perimeter     → C.perimeter_established = true
t0/20  gang activate_relay          → C.relay.active = true
t0/21  gang_claim_C_001 begins; personnel and supply are reserved
t0/27  Rarrival; crew may physically interact at C
t0/40  gang_claim_C_001 completion revalidates canonically
```

The first five actions are complete history, not a single persistent `stage` field. Their durable results remain in C. Their terminal resource effects are recorded before the next action becomes eligible.

### Arrival record

`Rarrival` is not an arrival transaction. It is the first scheduler-derived
record for which `physical_access(C)` is true, constructed from the exact
t0/21 parent record:

```text
Rarrival = copy(t0/21 claim-start record) + clock := t0/27
```

It has a parent hash, `scheduler_clock_advance` derivation, and transaction-pre-state hash. It changes no fact except `clock`.

The existing canonical deployment commitment selects C, but derived physical
access is false before `t0/27`. Arrival itself produces no strategic mutation,
does not alter C, and does not create, replan, pause, extend, or advance
`gang_claim_C_001`.

The record must contain at least:

```yaml
area: C
deployment:
  commitment_id: crew_deployment_C_live_001
  state: active
  destination: C
  physical_access_at: t0/27
gang:
  intelligence: true
  personnel_present: 6
  personnel_available: 0
perimeter:
  established: true
ingress:
  secured: true
relay:
  active: true
claim:
  commitment_id: gang_claim_C_001
  state: active
  resolution_time: t0/40
  reserved_personnel: 6
  reserved_supply: 1
  completion_gates:
    - C.relay.active == true
    - C.perimeter_established == true
    - C.ingress_secured == true
    - claim.reserved_personnel >= 6
    - C.rival_resistance <= 36
control:
  owner: contested
  gang: 64
  rival: 36
completed_history:
  - survey_C
  - marshal_C
  - secure_ingress_C
  - establish_perimeter_C
  - activate_relay_C
```

`physical_access(C)` is derived from these canonical deployment fields and the
record clock; it is not a separately serialized arrival fact. Thus the
arrival record remains a clock-only scheduler derivation while still proving
that the crew could not lawfully originate evidence at C before the
precommitted travel boundary.

The materializer may derive physical relay, perimeter, gang presence, ingress state, and visible pressure from those facts. It may not consume a stage or variant instruction.

## Claim resource lifecycle

At `t0/21`, `gang_claim_C_001` reserves exactly six present gang personnel and one claim supply.

```text
claim succeeds
  → personnel transfer to persistent C.gang_presence = 6
  → supply is consumed
  → commitment terminal = succeeded

claim fails
  → personnel release to gang.personnel_available = 6
  → supply releases to gang.supply_available = 1
  → commitment terminal = failed
```

Perimeter, ingress, and relay are durable results of earlier completed actions. They are not claim reservations. A failed claim does not rewrite their already-settled history.

## Physical relay evidence

While C is the active materialized crew domain, the local `gang_claim_relay_C_01` may physically produce a relay-disable proposal. It must be exact, evidenced, source-record-bound, and canonically validated.

```yaml
proposal_id: physical_disable_claim_relay_C_live_0001
target:
  kind: claim_relay
  id: gang_claim_relay_C_01
  area: C
observed_outcome: {state: disabled, event_sequence: 1}
proposed_mutations:
  - C.relay.active = false
```

The proposal gate requires all of the following:

```yaml
source_record_hash: transaction_pre_state_hash
crew_deployment: active
deployment_destination: C
physical_access_C: true
clock: at_or_after_t0_27
claim_id: gang_claim_C_001
claim_state: active
relay_active: true
```

Unreal may emit this proposal but cannot apply it. The canonical transaction layer evaluates every side-effect-free authority gate, then atomically accepts or rejects it and appends the causal ledger entry.

## Canonical resolution and race law

The claim has one canonical resolution boundary: `t0/40`. It is never an Unreal timer.

```text
claim completion gates
  C.relay.active == true
  C.perimeter_established == true
  C.ingress_secured == true
  claim.reserved_personnel >= 6
  C.rival_resistance <= 36
```

The visible countdown, if materialized, is a projection of `resolution_time: t0/40`; it has no strategic authority.

The proof freezes two ordered outcomes.

### Intervention wins the future

```text
Rarrival
  → crew disables relay
  → proposal commits at t0/30
  → C.relay.active = false
  → scheduler reaches t0/40
  → claim completion revalidates and fails relay gate
  → C remains contested (64 / 36)
  → claim releases all reservations
```

### Claim wins before later evidence

```text
Rarrival
  → no pre-t0/40 proposal
  → claim completion commits at t0/40
  → C.owner = gang; control = 72 / 28
  → claim reservations transfer/consume terminally
  → fresh post-claim physical relay evidence commits
  → C.relay.active = false
  → C.owner remains gang; control remains 72 / 28
```

The post-claim witness is intentionally stronger than stale-evidence rejection.
It proves that a cause required for a past result need not remain true forever
for that past result to stay historically true:

```text
relay.active was required for claim success at t0/40
≠
relay.active is required forever for gang ownership to remain history
```

The exact post-claim physical occurrence is fixture-local:

```yaml
proposal_id: physical_disable_claim_relay_C_live_0002
target:
  kind: claim_relay
  id: gang_claim_relay_C_01
  area: C
observed_outcome: {state: disabled, event_sequence: 2}
proposed_mutations:
  - C.relay.active = false
```

It originates only from a **fresh Unreal process** receiving the t0/40
gang-owned canonical record. Its canonical validation requires a fresh source
record hash, active deployment with destination C, derived
`physical_access(C) == true`, `C.owner == gang`, terminal claim state
`succeeded`, and `C.relay.active == true`. It may change the current relay fact
but has no authority path that can reopen, reverse, or re-evaluate the completed
claim.

The governing law is:

> **Physical evidence changes future canonical eligibility only if its mutation commits before the dependent commitment crosses its canonical revalidation boundary.**

## Required branch records

All branch runs share byte-identical R0, seed, rule version, pre-arrival gang actions, crew deployment, and Rarrival. They differ only in physical input timing after arrival.

```text
Rarrival control
  → no intervention
  → t0/40 claim succeeds
  → gang-owned C

Rarrival early intervention
  → relay-disable evidence accepted at t0/30
  → t0/40 claim fails
  → contested C

Rarrival late evidence
  → t0/40 claim succeeds
  → fresh post-claim relay evidence commits
  → relay becomes inactive; gang ownership remains historical fact
```

The proof variable is the timing of valid physical evidence relative to the
claim's canonical revalidation boundary, not arrival timing by itself. Branch C
does not claim that arriving after settlement creates a distinct history. It
materializes a fresh already-settled canonical record, then proves that a new
physical occurrence may change current relay state without reopening the
already-resolved ownership history.

The resulting conclusion is exactly:

> **No intervention before settlement permits the claim to resolve; valid physical evidence before settlement can prevent the claim; valid physical evidence after settlement can change current relay state without reopening already-resolved ownership history.**

## Acceptance gates

1. Every pre-arrival action is canonically committed before Rarrival, including terminal resource disposition and provenance.
2. Rarrival is a scheduler-only derivation of its immediate parent and changes only `clock`.
3. Deployment destination, derived physical-access eligibility, and strategic arrival mutation are distinct: destination is C; access becomes true only when the canonical clock reaches `physical_access_at`; arrival performs no strategic city, claim, gate, threshold, or schedule mutation.
4. Rarrival contains durable facts plus `gang_claim_C_001` as one active canonical commitment.
5. Unreal materializes Rarrival from facts and commitment data only; no stage/variant/arrival selector exists on the demonstrated path.
6. The claim remains canonical while its physical context is materialized; Unreal owns neither its timer nor its resolution.
7. Branch A materializes `Rarrival`, emits no Unreal proposal, and reaches gang ownership only through the canonical t0/40 claim resolution.
8. The physical relay outcome crosses only as evidenced proposal → canonical validation → atomic mutation → causal ledger.
9. In Branch B, physically evidenced relay disable commits before t0/40, changes the claim gate, and produces the exact failed terminal disposition.
10. In Branch C, the claim is already canonical history before Unreal starts; fresh post-boundary relay evidence may change `C.relay.active`, but cannot retroactively change completed gang ownership or control facts.
11. The same proposal validator and canonical commit path handle Branches B and C. Their different consequences arise only from authoritative pre-state and canonical timing, never branch-specific resolver logic.
12. Every success/failure terminal transition releases, consumes, transfers, or transforms every claim reservation.
13. Replay from Rarrival plus the same ordered physical input is byte-identical for all branch records and ledgers.
14. Every final Unreal process receives only its canonical final record. No branch reads prior Unreal-process memory, transient state, or branch-local hidden state.
15. Source audit proves no Unreal path selects a stage/mission variant, resolves `gang_claim_C_001`, mutates ownership/commitments, serializes canonical records, or writes the causal ledger.

## DAG plan

```text
freeze reviewed specification
        │
        ├──────────────┐
        ▼              ▼
canonical prehistory   materialization contract / source audit
+ Rarrival             │
        │              │
        └──────┬───────┘
               ▼
     early / control / late canonical branches
               │
               ▼
        Unreal Rarrival proposal capture
               │
               ▼
  fresh terminal materialization + replay + release manifest
               │
               ▼
            evidence seal
```

## Explicit boundary

This draft does not authorize implementation, additional city scale, split crews, intelligence variance, autonomous general planning, civilian simulation, new factions, multiplayer, networking, rollback, repair, or generalized player action semantics.

## Changelog

### 0.1.0-draft.3 — 2026-08-26

- Advanced the fixed proof simulation identity to `0.7.0-draft.20` and corrected the branch interpretation: evidence timing relative to canonical claim settlement—not arrival timing alone—distinguishes pre- and post-boundary consequences.
- Required an explicit no-proposal control branch, one shared B/C validator and commit path, and final-process isolation from prior Unreal state.

### 0.1.0-draft.2 — 2026-08-26

- Advanced the fixed proof simulation identity to `0.7.0-draft.19` with this reviewed arrival-eligibility correction.
- Separated deployment destination from physical-access eligibility. `physical_access(C)` is a deterministic predicate of an active deployment, destination, and the canonical clock; `Rarrival` remains clock-only and introduces no strategic arrival mutation.
- Replaced the ambiguous `crew_domain` evidence gate with deployment destination plus derived physical-access eligibility, including the fresh post-claim witness.
- Replaced the stale DAG opening with the actual remaining action: freeze the reviewed specification.

### 0.1.0-draft.1 — 2026-08-26

- Marked all gang, relay, perimeter, ingress, and ownership language fixture-only; the reusable machine is completed history, durable facts, live commitment, evidence, and canonical resolution.
- Fixed simulation identity as `0.7.0-draft.18` and selected the stronger fresh post-claim relay witness: the relay may later become inactive while already-committed gang ownership remains historical fact.
- Kept implementation prohibited pending final freeze review.

### 0.1.0-draft.0 — 2026-08-26

- Drafted the live-commitment arrival proof: completed gang history, durable relay/perimeter facts, a distinct active gang claim, Rarrival state-derived materialization, exact pre-boundary intervention, and no-retroactivity requirements.
- Kept the physical boundary narrow: one crew, one domain, and one relay causal input.
- Left exact simulation identity and late-evidence variant open for review; implementation remains prohibited.
