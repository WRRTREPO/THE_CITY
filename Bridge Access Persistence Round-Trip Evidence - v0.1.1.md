# Bridge Access Persistence Round-Trip Evidence — v0.1.1

**Status:** Passed  
**Date:** 2026-08-26  
**Specification:** [Bridge Access Persistence Round-Trip Proof — v0.1.1](Bridge%20Access%20Persistence%20Round-Trip%20Proof%20-%20Draft.md)  
**Prior record:** [v0.1.0](Bridge%20Access%20Persistence%20Round-Trip%20Evidence%20-%20v0.1.0.md), retained as the original execution witness.

## Claim proved

One physically resolved crew consequence crossed into authoritative city truth without granting Unreal authority to mutate that truth:

```text
Unreal seed scene
  → crew presses E at bridge access
  → local destruction + immutable proposal
  → canonical validation and atomic commit
  → canonical record R1
  → first Unreal process destroyed
  → fresh Unreal process receives R1 only
  → destroyed, impassable bridge reappears
```

This revision seals the final rebuilt source set, including the corrected local prompt cleanup and ASCII-only materialization labels. It changes no causal behavior, proposal, canonical record, or acceptance result from v0.1.0.

## Authority inputs and outputs

| Artifact | Identity | Meaning |
| --- | --- | --- |
| Frozen parent | `0b27ed07131ab5889d820476ef7d665c1f5c046872ea895b93b764801e7c7206` | No-fire Ash Crossing counterfactual. |
| Round-trip seed `R0` | `a049c8cde65f14dd6f485353d224acafa1c3cc16a30ab0ce0d758076eb6ed69b` | E_AB open/capacity 1/access intact; fire 4; police at C; Docklands contested. |
| Unreal proposal `P` | file SHA-256 `766843195d083690ead53b44ac5467dad19e9ea95b067a222a0e3c7934c46a6b` | Crew physical evidence for `bridge_access_point_E_AB_01` destruction. |
| Canonical committed record `R1` | `a3557899d69f2ace213e5f4b05138877ef12c86d27c29712a007cdc5e8ebbeac` | E_AB closed/capacity 0/access destroyed; all unrelated facts preserved. |

`R1` contains only the permitted persistent change:

```yaml
bridge_open: false
bridge_capacity: 0
bridge_access_point_state: destroyed
fire_intensity: 4
police_location: C
docklands_owner: contested
```

## Final runtime sequence

1. The Python canonical layer generated `R0` from the frozen no-fire parent.
2. A fresh UE 5.8 process loaded `R0`. The crew pawn entered the physical bridge-access space and pressed `E`.
3. Unreal resolved only the local physical consequence: it replaced the intact access with local destroyed geometry and emitted `physical_destroy_E_AB_0001.json`. It did not write a city record or ledger.
4. `roundtrip.py` received `R0` and `P`, evaluated all seven side-effect-free gates as true, then atomically committed `R1`. Its accepted ledger entry contains the crew, physical actor, evidence digest, pre-state hash, post-state hash, all gate results, and the exact three mutation paths.
5. The original UE process was terminated. A fresh UE 5.8 process then received **only** `R1`.
6. The fresh process logged materialization of `a355…beac`; first-person inspection showed `ACCESS DESTROYED - BRIDGE CLOSED` and `ACCESS DESTROYED - ROUTE CLOSED`, a blocking destroyed access barrier, no active fire, police present at C, and contested Docklands.
7. The original proposal was submitted again against `R1`. All validation gates ran. `source_record_hash_matches_pre_state`, `proposal_id_unseen`, and `target_current_state_eligible` were false; the canonical record did not change.
8. The accepted transaction was replayed from the same `R0` and actual Unreal proposal `P`. It produced byte-identical `R1` and an equivalent accepted ledger entry.

## Reproducible artifacts

```text
4762e33eb394ec89c00e9747220904d86d10e9ac319c88a0cba92fa3136f1541  RuntimeExchange/roundtrip_seed.json
766843195d083690ead53b44ac5467dad19e9ea95b067a222a0e3c7934c46a6b  RuntimeExchange/physical_destroy_E_AB_0001.json
5f7bd26344c9bac7bc553c63cc74ba970dff5b99fcee46816fdb64508c4bca81  RuntimeExchange/committed_record.json
edb99738bb07912567300bb6c3a4924085057a7089fd5c18a405619a18a11253  RuntimeExchange/causal_ledger.json
5f7bd26344c9bac7bc553c63cc74ba970dff5b99fcee46816fdb64508c4bca81  RuntimeExchange/duplicate_record.json
9ead26fefa90ecfda85af34f1d3d9fecc27b7903176315851a18da3c3d16a0ba  RuntimeExchange/duplicate_causal_ledger.json
5f7bd26344c9bac7bc553c63cc74ba970dff5b99fcee46816fdb64508c4bca81  RuntimeExchange/replay_committed_record.json
edb99738bb07912567300bb6c3a4924085057a7089fd5c18a405619a18a11253  RuntimeExchange/replay_causal_ledger.json
```

The committed, duplicate-output, and replay-output records are byte-identical. The duplicate ledger is deliberately different: it is an append-only rejected transaction record with all gates recorded.

## Automated verification

```text
PYTHONDONTWRITEBYTECODE=1 python3 proof_kernel/test_kernel.py
8 tests — OK

PYTHONDONTWRITEBYTECODE=1 python3 proof_kernel/test_roundtrip.py
5 tests — OK

PYTHONDONTWRITEBYTECODE=1 python3 proof_kernel/test_unreal_authority_boundary.py
2 tests — OK
```

The final Unreal target also compiled successfully with UE 5.8, Mac Development. The final fresh materialization was visually inspected after the build.

## Authority audit

`BridgeAccessPoint.cpp` may serialize only `physical_destroy_E_AB_0001.json` into ignored local `RuntimeExchange/`. It does not name or write a committed record, duplicate record, causal ledger, or canonical transaction. `CityMaterializationActor.cpp` reads a selected record but never serializes one.

The two authority-audit tests enforce those source boundaries. The canonical Python module alone performs validation, mutation, canonical hashing, and causal-ledger append.

## Final source identity

```text
d387563044886606282111b3d6f8838629a2562f0741332dedbfb555a9264f3b  proof_kernel/roundtrip.py
56e7ad9fc6adf294a5b3b0af5c29ee20a5eb763b2307b7ffa55ebbf3b570697b  proof_kernel/test_roundtrip.py
148017fcf0033a82b000941b394aed4b8c5d29989c84e3f37a38c02de26e5c01  proof_kernel/test_unreal_authority_boundary.py
2ad11728e4f876227b1a3ed70f7f6cc022e1e933aa3b175e72a33ebaa920710c  CityMaterializationProof/Source/CityMaterializationProof/BridgeAccessPoint.h
ecafaa9149dcf34bcfdacbea7c3e932afa3ed3d4b44268c54a14f6340292dd6e  CityMaterializationProof/Source/CityMaterializationProof/BridgeAccessPoint.cpp
78ee18b5048b6933ddaabd35882be216e8308ab84a90e05546ab7096cc74425e  CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationActor.cpp
e03332b6034f8f8c29a77a2aa3b4fc9d3dcac9e2c18aad2eb85059a0874fdaf3  CityMaterializationProof/Source/CityMaterializationProof/CityProofCharacter.cpp
4762e33eb394ec89c00e9747220904d86d10e9ac319c88a0cba92fa3136f1541  CityMaterializationProof/Content/ProofRecords/BridgeAccessRoundTripSeed.json
```

## Boundary

This proves one physical-to-canonical-to-physical consequence. It does not prove multiplayer arbitration, trusted network transport, rollback, general save/load, repair, damage gradation, or expanded city simulation.
