# Bridge Access Persistence Round-Trip Evidence — v0.1.0

**Status:** Passed  
**Date:** 2026-08-26  
**Specification:** [Bridge Access Persistence Round-Trip Proof — v0.1.1](Bridge%20Access%20Persistence%20Round-Trip%20Proof%20-%20Draft.md)

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

## Runtime sequence

1. The Python canonical layer generated the `R0` fixture.
2. A fresh UE 5.8 process loaded `R0`. The local log recorded materialization of `a049…ed69b`.
3. The crew pawn occupied the local bridge-access space and pressed `E`. Unreal showed the local destroyed barrier and wrote `physical_destroy_E_AB_0001.json`; it logged `Physical bridge-access destruction detected; proposal written.`
4. `roundtrip.py` received `R0` and `P`, evaluated all seven side-effect-free gates as true, then atomically committed `R1`. The causal ledger records the crew, physical actor, evidence digest, pre-state hash, post-state hash, gate results, and exact three mutation paths.
5. The original UE process was terminated.
6. A fresh UE 5.8 process loaded only the canonical `R1` file. Its log recorded materialization of `a355…beac`. Native first-person inspection showed a blocking destroyed access barrier, no active fire, police present at C, and contested Docklands.
7. The original proposal was submitted once more against `R1`. Validation evaluated every gate and rejected it. `source_record_hash_matches_pre_state`, `proposal_id_unseen`, and `target_current_state_eligible` were false; no canonical fact changed.

The serialized committed and duplicate-output records are byte-identical:

```text
5f7bd26344c9bac7bc553c63cc74ba970dff5b99fcee46816fdb64508c4bca81
```

The accepted transaction replay from the same `R0` and actual Unreal proposal `P` produced the same committed record and an equivalent accepted ledger entry.

## Automated checks

```text
PYTHONDONTWRITEBYTECODE=1 python3 test_kernel.py
8 tests — OK

PYTHONDONTWRITEBYTECODE=1 python3 test_roundtrip.py
5 tests — OK

PYTHONDONTWRITEBYTECODE=1 python3 test_unreal_authority_boundary.py
2 tests — OK
```

The Unreal target also compiled successfully with UE 5.8, Mac Development.

## Authority audit

`BridgeAccessPoint.cpp` may serialize only `physical_destroy_E_AB_0001.json` into the ignored local `RuntimeExchange/` directory. It does not name or write a committed record, duplicate record, causal ledger, or canonical transaction. `CityMaterializationActor.cpp` reads a selected record but does not serialize one.

The two authority-audit tests enforce those source boundaries. The canonical Python module alone performs validation, mutation, canonical hashing, and causal-ledger append.

## Source identity

```text
d387563044886606282111b3d6f8838629a2562f0741332dedbfb555a9264f3b  proof_kernel/roundtrip.py
56e7ad9fc6adf294a5b3b0af5c29ee20a5eb763b2307b7ffa55ebbf3b570697b  proof_kernel/test_roundtrip.py
148017fcf0033a82b000941b394aed4b8c5d29989c84e3f37a38c02de26e5c01  proof_kernel/test_unreal_authority_boundary.py
26d6542d1e7ed22602e57487bc9da6fe11bf25024d3c56586f832b999cc6d03e  CityMaterializationProof/Source/CityMaterializationProof/BridgeAccessPoint.cpp
86b488dbe7e207cf73fc8255b584869cfe5981b5fc9857ae501749d997629d5f  CityMaterializationProof/Source/CityMaterializationProof/BridgeAccessPoint.h
24d3dae1805371d59e49c1761a4a05f37de00088718229cd3c29341a23cb8493  CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationActor.cpp
e03332b6034f8f8c29a77a2aa3b4fc9d3dcac9e2c18aad2eb85059a0874fdaf3  CityMaterializationProof/Source/CityMaterializationProof/CityProofCharacter.cpp
4762e33eb394ec89c00e9747220904d86d10e9ac319c88a0cba92fa3136f1541  CityMaterializationProof/Content/ProofRecords/BridgeAccessRoundTripSeed.json
```

## Boundary

This proves one physical-to-canonical-to-physical consequence. It does not prove multiplayer arbitration, trusted network transport, rollback, general save/load, repair, damage gradation, or expanded city simulation.
