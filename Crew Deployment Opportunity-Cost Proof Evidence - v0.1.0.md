# Crew Deployment Opportunity-Cost Proof Evidence — v0.1.0

**Status:** Passed
**Date:** 2026-08-26
**Specification:** [Crew Deployment Opportunity-Cost Proof — v0.1.0](Crew%20Deployment%20Opportunity-Cost%20Proof%20-%20Draft.md)
**Implementation scope:** One crew, one aircraft, one deployment commitment, and the frozen B/C/D choice branches only.

## Claim proved

```text
canonical crew deployment
        ↓
one materialized physical-evidence domain
        ↓
active-world time continues elsewhere
        ↓
same canonical city machine
        ↓
different durable history
        ↓
fresh Unreal materialization from final record alone
```

The proof establishes that deciding where the crew becomes physically capable
is itself a consequential city action. The crew receives no remote veto or
pause authority over unattended fire, police, or gang commitments.

## Canonical records

| Record | Canonical SHA-256 | Meaning |
| --- | --- | --- |
| B interaction pre-state | `f22ab50d5edfc4796d3c50d26f778b35b33e8739dcd62bbec146e094fecd9743` | Crew deployed to B; fire-control evidence domain available at `t0/05`. |
| C interaction pre-state | `683645537eb859dd0edf0993b3f7926e8556d59a7d40bf1e6ba243edee6b7866` | Crew deployed to C; fire already closed E_AB and police admission has failed. |
| B final | `c5fdb16685a628bfc1de59280b340b60f0bf546a54b1d136e8b0add517f4b5bb` | Fire contained, E_AB open, police at C, Docklands contested. |
| C final | `a3c76c840870bd2cfd32fdaeb5d4f8fca08bc24a68e6aed358dced1c78c9e340` | Fire closes E_AB, police remains A, crew disruption prevents seizure, Docklands contested. |
| D final | `e1c4a3e8d4131f04e00f3671caee9017ac387ffb6997e86f35429f2c79371958` | Crew is deployed in the neutral holding domain while fire closes E_AB and Docklands becomes gang-controlled, 74 / 26. |

All three branches begin from byte-identical R0 with the same seed, rules, and
autonomous schedule. Only the accepted deployment destination and allowed
physical input sequence differ.

## Canonical deployment and exclusivity

The B, C, and D requests each begin as a crew hub command. The canonical
transaction layer validates source binding, crew availability, aircraft
availability, no active deployment, a valid destination, and hub origin before
atomically reserving `crew_01_to_04` and `aircraft_01`, creating one active
deployment commitment, and setting `world.active_world = true` at `t0/00`.

A second canonical deployment request at `t0/01` evaluates every gate. It is
rejected because the crew and aircraft are reserved and an active deployment
already exists. It creates no second interaction domain and acquires no
resource.

## Physical evidence boundary

Fresh UE 5.8 first-person processes loaded the two sealed pre-interaction
records. The crew pawn pressed `E` at the selected cyan operation surface:

```text
B process
  → fire_control_valve_B_01
  → physical_contain_fire_B_deployment_0001.json

C process
  → gang_signal_relay_C_01
  → physical_disrupt_seizure_C_deployment_0001.json
```

The Unreal actors emitted only their exact evidence contracts. Each proposal
contains its source-record hash, crew identity, exact target, physical outcome,
and allowed one-fact mutation. The Python canonical resolver verified those
contracts before it changed `B.fire_containment` or `C.crew_disruption`.

Unreal does not write canonical records, deployment commitments,
`proposal_terminal_dispositions`, or causal-ledger entries. The source audit
tests enforce that boundary.

## Resulting city histories

```text
DEPLOY B
  physical containment before t0/10
  → fire spread gate fails
  → E_AB remains open
  → police reaches C
  → gang completion gate fails
  → C remains contested

DEPLOY C
  fire proceeds remotely at t0/10
  → E_AB closes
  → police admission fails
  → physical disruption before t2/40
  → gang completion gate fails
  → C remains contested

DEPLOY D
  no B/C physical evidence
  → fire closes E_AB
  → police admission fails
  → gang completion succeeds
  → C becomes gang-controlled
```

No branch contains a fixture-only `branch` fact. The final canonical record,
including its deployment fact and durable city state, is sufficient to express
the scene.

## Cross-transaction provenance and replay

Every later boundary is explicitly constructed as:

```text
parent canonical record
  → scheduler_clock_advance
  → transaction pre-state (clock only changed)
  → due canonical action
```

Each run records parent and transaction-pre-state hashes. The release verifier
checks that each scheduler header parent equals the preceding transaction's
working post-state hash, regenerates all B/C/D artifacts from sealed source and
captured Unreal evidence, and compares the complete runs byte-for-byte.

## Verification

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v \
  test_kernel.py test_roundtrip.py test_contention.py \
  test_unreal_authority_boundary.py test_deployment_opportunity.py
41 tests — OK

UE 5.8: CityMaterializationProofEditor Mac Development
Result: Succeeded
```

After the proposal-emitting processes were terminated, three fresh UE 5.8
processes received only `deployment_B_final.json`, `deployment_C_final.json`,
and `deployment_D_final.json`. First-person inspection confirmed the three
distinct states: open route/police response after B containment; fire closure
plus disruption after C; and fire closure plus gang control after D. The proof
floor remained a collision surface at `Z = 0` in every run.

Verify the sealed package with:

```sh
cd "/Users/boandersson/Desktop/Games/THE_CITY"
PYTHONDONTWRITEBYTECODE=1 python3 proof_kernel/verify_deployment_opportunity_release.py verify
```

The release manifest excludes its own checksum identity.

## Boundary

This proves exclusive crew opportunity cost only. It does not authorize split
fireteams, intelligence uncertainty, additional city sites or factions,
multiplayer arbitration, networking, rollback, repair, or a generalized
physical-action framework.
