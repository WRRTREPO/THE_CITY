# Bridge Access Traversal Contention Proof Evidence — v0.1.0

**Status:** Passed
**Date:** 2026-08-26
**Specification:** [Bridge Access Traversal Contention Proof — v0.1.0](Bridge%20Access%20Traversal%20Contention%20Proof%20-%20Draft.md)
**Parent continuation:** [v0.7.0-draft.14](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)

## Claim proved

One Unreal-originated physical consequence and one already-due canonical traversal entry can contend within one deterministic city decision boundary without either Unreal authority leakage or retroactive route history.

```text
R0
 └─ captured Unreal crew proposal P ─┐
                                    ├─ t0 canonical batch ── Case 1 or Case 2
R0 ─ police E_AB entry proposal Q ──┘
                                              │
                              Case 2 only: distinct t1/15 exit transaction
                                              │
                                     fresh Unreal materialization
```

The canonical kernel owns validation, ordering, revalidation, mutation, and ledger entries. Unreal owns physical detection, evidence production, and read-only materialization only.

## Authority inputs

The captured UE proposal is preserved at:

`CityMaterializationProof/Content/ProofRecords/physical_destroy_E_AB_contention_0001.json`

It is byte-for-byte valid under the frozen proposal contract and binds to the shared canonical R0. Its identity is:

```text
proposal_id: physical_destroy_E_AB_contention_0001
runtime_instance_id: contention_proof_runtime_01
source_record_hash: 65d928d8c981542065e59f4d9ecf0b126637ce0497f9ee51f1476d62d25549bd
source_simulation_version: 0.7.0-draft.13
```

The canonical resolver reuses that captured proposal for both fixture orderings. It does not substitute a hand-authored proposal during release artifact generation.

## Canonical outcomes

| Record | Canonical state hash | Result |
| --- | --- | --- |
| Shared R0 | `65d928d8c981542065e59f4d9ecf0b126637ce0497f9ee51f1476d62d25549bd` | E_AB open/capacity 1/access intact; police A and available; fire 4; Docklands contested. |
| Case 1 final | `9ae316b61e0bf1a747a2e7060b99a20ca166cdffbd71107adddfbb0d3af7c647` | P destroys the access first; Q fails `E_AB.open`; police stays A and no lease exists. |
| Case 2 intermediate | `a2cdbae6cc4fdc7ead07008f665d2f4de5e28eab08c3ee085794d26695d0ef76` | Q enters first; P closes admission; the valid E_AB lease remains while police traverses. |
| Case 2 final | `062777b73824134391159bcce9ecffeaae930729c3cddae832e0e49d418ab4b3` | A separate `t1/15` transaction releases the E_AB lease; police is at B, reserved, with E_BC unevaluated. |

Both final records preserve fire intensity `4` and contested Docklands. The only changed authority is bridge access plus the police/traversal state causally required by the selected ordering.

## Acceptance results

- **Complete proposal authorization:** 11 contention tests reject wrong target route/id, actor, outcome, missing/extra/reordered mutation effects, and an internally consistent but unauthorized proposal. A valid evidence digest alone never authorizes mutation.
- **Hash roles:** Case 2 proves P's source hash matches immutable `batch_pre_state_hash = hash(R0)` while differing from its later sequential `working_pre_state_hash`; P still revalidates and commits correctly.
- **Route history:** the Case 2 intermediate record explicitly carries `open: false`, `capacity: 0`, and the existing `police_dispatch_C_t0:E_AB` lease. The later closure blocks new admission without cancelling the entered segment.
- **Temporal provenance:** `t1/15` has its own batch header and pre-state hash. It does not inherit the t0 batch hash or decision time.
- **Authority audit:** Unreal writes only the physical proposal. Static tests reject canonical-record and ledger writes from Unreal source; the materializer reads records but never serializes them.
- **Replay:** each fixed ordering produces byte-identical canonical run artifacts and ledger output.

## Automated verification

```text
PYTHONDONTWRITEBYTECODE=1 python3 proof_kernel/test_contention.py
11 tests — OK

PYTHONDONTWRITEBYTECODE=1 python3 proof_kernel/test_kernel.py
8 tests — OK

PYTHONDONTWRITEBYTECODE=1 python3 proof_kernel/test_roundtrip.py
5 tests — OK

PYTHONDONTWRITEBYTECODE=1 python3 proof_kernel/test_unreal_authority_boundary.py
2 tests — OK
```

All **26 tests** passed after the final implementation. UE 5.8 compiled `CityMaterializationProofEditor Mac Development` successfully.

## Runtime verification

1. A fresh UE process loaded the shared R0 record. Pressing `E` at the physical bridge-access console generated `physical_destroy_E_AB_contention_0001.json` only. The parsed file exactly matched the frozen P contract.
2. The captured P was supplied to the canonical resolver for both orderings. The resolver produced the sealed Case 1, Case 2 intermediate, and Case 2 final records above.
3. The R0 process was terminated. A fresh UE process loaded Case 2 final only and visibly materialized a destroyed, impassable bridge with `POLICE AT B - RESERVED`.
4. That process was terminated. Another fresh UE process loaded Case 1 final only and visibly materialized the same destroyed bridge with the police consequence retained at A.

The local Unreal log records both final record hashes. No final scene depended on object state retained from the R0 process.

## Release integrity

Run:

```sh
cd "/Users/boandersson/Desktop/Games/THE_CITY"
PYTHONDONTWRITEBYTECODE=1 python3 proof_kernel/verify_contention_release.py verify
```

The verifier checks the sealed member set and every SHA-256 recorded in [the release manifest](Bridge%20Access%20Traversal%20Contention%20Proof%20-%20v0.1.0%20SHA256SUMS.txt). The manifest deliberately excludes its own hash, preventing the self-reference defect found in the rejected external candidate.

## Boundary

This proves one contention law, not a general multiplayer ordering policy, network trust model, rollback system, repair system, new damage type, E_BC traversal, or city expansion. The next proof requires a separately frozen scope decision.
