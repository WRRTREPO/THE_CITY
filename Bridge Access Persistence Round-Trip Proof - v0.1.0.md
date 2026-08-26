# Bridge Access Persistence Round-Trip Proof

**Version:** 0.1.0  
**Status:** Frozen implementation specification. Not implemented.  
**Opened:** 2026-08-26  
**Parent continuation:** [Co-op Open-City FPS Simulation — v0.7 Working Continuation](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)  
**Prior authority proof:** [Unreal Materialization Proof Evidence — v0.1.0](Unreal%20Materialization%20Proof%20Evidence%20-%20v0.1.0.md)

## Purpose

Prove one complete, reversible-direction authority crossing without granting Unreal city-state authority:

```text
sealed authoritative record
        ↓
materialize into Unreal FPS
        ↓
crew physically destroys one bridge access point
        ↓
Unreal emits evidence and a consequence proposal
        ↓
canonical transaction layer validates and commits
        ↓
new canonical record and causal-ledger entry
        ↓
destroy the Unreal embodiment
        ↓
fresh Unreal process materializes only from the new record
        ↓
bridge remains closed
```

The proof is passed only when the final closure is recreated from canonical city truth after the original Unreal scene no longer exists. A destroyed mesh surviving in memory is not evidence of persistence.

## Scope

Exactly one physical consequence is in scope:

```text
target: bridge_access_point_E_AB_01
owner: route E_AB (Ash Bridge, A ↔ B)
physical outcome: destroyed
durable route result:
  E_AB.bridge_open = false
  E_AB.capacity = 0
  E_AB.bridge_access_point.state = destroyed
```

No fire intensity, faction control, police location, crew commitment, economy, civilian, traffic, or new graph behavior is introduced. The bridge access point is a persistent site of the already-proven `E_AB` route, not a new city system.

## Seed and resulting truth

The proof starts from the frozen no-fire counterfactual causal result:

```text
parent causal record hash
= 0b27ed07131ab5889d820476ef7d665c1f5c046872ea895b93b764801e7c7206

E_AB.bridge_open = true
E_AB.capacity = 1
E_AB.bridge_access_point.state = intact
bridgehead.fire_intensity = 4
C.owner = contested
police_present_C = 1
```

The source record above remains immutable. The round-trip fixture normalizes its explicit access-point state to `intact` and records the parent hash. Its own canonical fixture hash is an implementation-evidence artifact, not a revision of the frozen counterfactual hash.

After an accepted proposal, the new canonical record must contain:

```yaml
E_AB:
  bridge_open: false
  capacity: 0
  bridge_access_point:
    state: destroyed

bridgehead:
  fire_intensity: 4
```

The closure is therefore a destroyed-access consequence, not a fire consequence. Fresh materialization must show a physically impassable destroyed access point and must not fabricate an active fire to explain it.

## Authority split

```text
Unreal FPS
  owns physical resolution, observation, evidence production,
  and a non-authoritative consequence proposal.

Canonical transaction layer
  owns persistence eligibility, current-record revalidation,
  idempotency, authoritative mutation, canonical serialization,
  and the causal ledger.
```

This is forbidden:

```cpp
CityRecord.E_AB.Open = false;
```

The Unreal process may not write a canonical record, calculate a canonical record hash, commit a ledger entry, or decide that its local physical outcome is durable.

## Physical proposal contract

After physical destruction is detected, Unreal emits an immutable `PhysicalConsequenceProposal.v1` to the canonical transaction boundary. For this proof it must contain at least:

```yaml
proposal_id: physical_destroy_E_AB_0001
protocol_version: PhysicalConsequenceProposal.v1
source:
  system: crew_physical_simulation
  runtime_instance_id: proof_runtime_01
  source_record_hash: <round-trip seed canonical hash>
  source_simulation_version: <frozen proof version>
instigator:
  kind: crew
  id: crew_01_to_04
target:
  kind: bridge_access_point
  id: bridge_access_point_E_AB_01
  route: E_AB
observed_outcome:
  state: destroyed
  event_sequence: 1
evidence:
  physical_actor_id: bridge_access_point_E_AB_01
  destruction_state: destroyed
  evidence_digest: <canonical digest of the proof evidence>
proposed_mutations:
  - E_AB.bridge_open = false
  - E_AB.capacity = 0
  - E_AB.bridge_access_point.state = destroyed
```

The proposal is evidence, not a mutation. A local visual effect may occur before acceptance, but it is disposable until the transaction layer commits it.

## Canonical transaction contract

The transaction layer receives the proposal at one named decision boundary. It first takes the current immutable authoritative record and then performs these gates in canonical order:

1. Validate proposal schema and protocol/simulation compatibility.
2. Verify that `source_record_hash` equals the current round-trip seed record hash.
3. Verify that `proposal_id` has not already received a terminal disposition.
4. Verify target identity and ownership: `bridge_access_point_E_AB_01` belongs to `E_AB`.
5. Verify current target state: access point is `intact`, `bridge_open == true`, and `capacity >= 1`.
6. Verify the proposal's allowed effect set exactly matches the scoped bridge-access destruction consequence.
7. Commit the three permitted mutations atomically, then derive the route's unavailability from the new facts.

No agent decision, front advancement, or unrelated derived effect executes at this transaction boundary. The proof isolates player-to-city persistence from strategic scheduling.

On acceptance, the ledger entry must include:

- decision boundary, canonical execution sequence, simulation and proposal-protocol versions;
- the source record hash, resulting canonical record hash, proposal id, evidence digest, and physical actor id;
- crew/player provenance and the observed physical outcome;
- all gate values and their pass/fail result;
- the exact allowed mutation paths, canonical pre-state and post-state references; and
- the terminal disposition `accepted`.

## Required rejection

Submit the exact accepted proposal a second time against the newly committed record.

It must be rejected before mutation because its source record hash is stale and its proposal id already has a terminal disposition. The canonical record hash must remain unchanged. The ledger must append an inspectable failed entry with:

```yaml
terminal_disposition: rejected
failed_gates:
  - source_record_hash_matches_current: false
  - proposal_id_unseen: false
committed_mutations: []
```

The rejection is part of the proof. It prevents duplicate physics events or late network-like delivery from becoming an unauthorized second city mutation.

## Compression and fresh rematerialization

After the accepted canonical record is serialized:

1. Destroy the first Unreal process and its entire local embodiment.
2. Start a fresh Unreal process with only the committed canonical record selected as its input.
3. Do not restore a prior level, actor instance, destruction flag, replay buffer, or Unreal save as proof state.
4. Materialize `E_AB` from the committed record.

The fresh scene must present a destroyed, impassable bridge access point; `E_AB` must be unavailable to traversal. It must preserve fire intensity `4` without visualizing a fire, and must retain the no-fire counterfactual's contested Docklands and police presence at `C`.

## Determinism and acceptance tests

| Test | Required result |
| --- | --- |
| Baseline materialization | The intact seed record materializes an open, traversable E_AB access point. |
| Physical proposal | Unreal emits exactly one immutable destruction proposal with the seed hash and crew provenance. |
| Accepted transaction | Canonical layer produces one new record hash and one accepted ledger entry; only the three allowed E_AB facts change. |
| Fresh rematerialization | A new Unreal process, supplied only the committed record, reconstructs the destroyed access point and closed route. |
| Duplicate/stale rejection | Replaying the accepted proposal changes no canonical fact and adds one rejected ledger entry. |
| Canonical replay | Same seed fixture, same proposal bytes, and same canonical version produce byte-identical committed record and ledger. |
| Authority audit | No Unreal source path writes canonical city state or emits a ledger commitment. |

## Explicitly out of scope

- multiplayer arbitration and client/server trust;
- rollback, late inputs, network retransmission beyond the one duplicate/stale rejection;
- save-system implementation beyond the canonical record fixture;
- bridge repair, reversible access, damage gradations, and any other route behavior;
- additional physical consequences or strategic city systems.

## Completion boundary

This specification is frozen at `0.1.0`. Implement exactly this one consequence and prove its accepted, rejected, compressed, and freshly rematerialized paths. Do not add city scale or adjacent gameplay systems until all acceptance tests pass.

## Changelog

### 0.1.0 — 2026-08-26

- Froze a one-consequence bridge-access destruction round trip from Unreal evidence proposal to canonical mutation and fresh FPS rematerialization.
- Defined strict ownership, transaction gates, provenance, idempotency rejection, and no-hidden-state acceptance.
