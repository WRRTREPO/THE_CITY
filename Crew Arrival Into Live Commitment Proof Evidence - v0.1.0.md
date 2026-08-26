# Crew Arrival Into Live Commitment Proof Evidence — v0.1.0

**Status:** Passed and sealed
**Date:** 2026-08-26
**Specification:** [Crew Arrival Into Live Commitment Proof — v0.1.0](Crew%20Arrival%20Into%20Live%20Commitment%20Proof%20-%20Draft.md)
**Implementation scope:** One shared crew, one materialized domain, one fixture-local live claim, and the frozen control/early/late branches only.

## Claim proved

```text
canonical completed history
        ↓
durable local facts + active future commitment
        ↓
fresh Unreal materialization of Rarrival
        ↓
optional physical relay evidence
        ↓
canonical revalidation at the claim boundary
        ↓
durable history
        ↓
fresh Unreal materialization of final truth alone
```

The proof establishes causal continuity through arrival. Crew arrival neither
creates, selects, restarts, suspends, nor advances `gang_claim_C_001`. It
derives physical-evidence eligibility from the active deployment, its selected
destination C, and canonical time reaching `t0/27`; it performs no strategic
arrival mutation.

The gang, relay, perimeter, ingress, claim, and ownership nouns are
fixture-only. The reusable result is: completed actions may leave durable
facts; a canonically owned commitment may remain live through materialization;
physical evidence may change a future gate; the canonical scheduler alone
settles the resulting history.

## Sealed canonical records

| Record | Canonical SHA-256 | Result |
| --- | --- | --- |
| Arrival `Rarrival` | `9e2226281c549f9cf98d4b59179f9473031a44b2966bbf17be85165360ac7ef1` | Relay active; perimeter and ingress established; claim active; physical access is derived at `t0/27`. |
| Control final | `9b7e6dcd5d8be788d6f9cfa3e137db42cbf74bb447d911f1d97b20d1fee2065a` | No proposal; claim succeeds; C is gang-owned and relay remains active. |
| Early final | `490448c5c078aee70935a80b899af59c312dcb1dd363922a8884586afc9b9fb8` | Relay evidence commits at `t0/27`; claim fails at `t0/40`; C remains contested and relay is inactive. |
| Late final | `c681a451c0fdaa9706a8e1eebb139809e0d629e39a969cd79b119ca0fc54622d` | Claim succeeds first; fresh later relay evidence changes only the current relay fact; C remains gang-owned at 72 / 28. |

## Canonical branch proof

All three branches begin from byte-identical R0, use the same seed, simulation
version, prehistory, deployment, and claim schedule. They differ only in the
permitted physical-input sequence after `Rarrival`.

```text
CONTROL
  Rarrival → no physical proposal → t0/40 canonical claim success

EARLY
  Rarrival → fresh Unreal P1 → canonical relay disable at t0/27
  → t0/40 claim gate fails → contested C

LATE
  t0/40 canonical claim success → fresh Unreal P2 from the settled record
  → canonical relay disable → gang ownership remains historical fact
```

The same physical relay-disable contract and canonical validator handle early
and late evidence. The different results arise from current authoritative
state and the claim's canonical revalidation boundary—not from branch-specific
Unreal logic or an arrival-specific encounter selector.

## Unreal authority and fresh-process witnesses

Fresh UE 5.8 first-person processes produced the two captured proposal files:

```text
Rarrival
  → physical_disable_claim_relay_C_live_0001.json

post-claim gang-owned record
  → physical_disable_claim_relay_C_live_0002.json
```

Unreal emitted evidence only. It did not serialize a canonical record, mutate
the active claim, resolve ownership, or append a ledger entry. The source audit
checks that boundary and rejects mission/stage/variant authority on the
demonstrated path.

After the proposal processes were terminated, three separate fresh UE 5.8
processes received only the final control, early, and late canonical records.
Direct first-person inspection observed, respectively: gang control with an
active relay; contested control with a canonically disabled relay; and gang
control with a canonically disabled relay. No final-process witness was given a
prior Unreal-process state, proposal, or branch instruction.

## Verification

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/thecity_pycache \
python3 -m unittest -v \
  test_kernel.py test_roundtrip.py test_contention.py \
  test_unreal_authority_boundary.py test_deployment_opportunity.py \
  test_live_commitment.py
57 tests — OK

UE 5.8: CityMaterializationProofEditor Mac Development
Result: Succeeded
```

The self-excluding release manifest verifies the frozen documents, source,
tests, captured Unreal evidence, and regenerated canonical branch artifacts:

```sh
cd "/Users/boandersson/Desktop/Games/THE_CITY"
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/thecity_pycache \
  python3 proof_kernel/verify_live_commitment_release.py verify
```

It excludes its own checksum identity and independently regenerates all three
branch artifacts from the captured Unreal proposals and frozen resolver.

## Boundary

This proof establishes one live commitment crossing arrival and one physical
input crossing its revalidation boundary. It does not authorize generalized
commitment types, broader city scale, split crews, intelligence uncertainty,
multiplayer arbitration, networking, rollback, repair, or generalized
physical-action semantics.
