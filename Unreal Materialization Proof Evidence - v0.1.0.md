# Unreal Materialization Proof Evidence — v0.1.0

**Status:** Passed  
**Date:** 2026-08-26  
**Scope:** Record-to-FPS materialization only. This is not a new city-law record and does not add strategic simulation to Unreal.

## Claim under test

The same frozen Ash Crossing authoritative records accepted by the Python causal kernel can be loaded into a real, walkable Unreal first-person scene without contradiction or reroll.

Unreal receives a selected sealed record. It validates that record, materializes only its permitted physical facts, and has no authority to run fronts, make strategic decisions, or mutate the causal record.

## Authority inputs

| Run | Canonical record hash | Required material facts |
| --- | --- | --- |
| Primary | `d08e69d6b5fde3b27d10fb45f3bfd6143d856750c2dfd91f7b5851674fbeed76` | fire intensity 5; Ash Bridge closed; police at A; Docklands gang-controlled, 74 / 26 |
| Counterfactual | `0b27ed07131ab5889d820476ef7d665c1f5c046872ea895b93b764801e7c7206` | fire intensity 4; Ash Bridge open; police present at C; Docklands contested, 62 / 38 |

Those record hashes come from [Proof Kernel Implementation Evidence — v0.1.1](Proof%20Kernel%20Implementation%20Evidence%20-%20v0.1.1.md). The two records used by Unreal are under `CityMaterializationProof/Content/ProofRecords/`.

## Materialization boundary

```text
sealed authoritative record
        ↓
Unreal record validation
        ↓
walkable FPS scene
        ↓
physical expression only

no FPS outcome returns to city state in this proof
```

The project rejects a gang-controlled record with police present at Docklands, and rejects an open bridge with fire intensity of five or greater. It does not try to infer or repair a contradictory city state.

## Source identity

```text
d4cf6ee332faf8705cd3eab6a3a9a2a110e5a41daa1c361e95a0181012aea7ac  CityMaterializationProof.uproject
eeeb3a785dba6140f247a928b4de7f43b5541698e71db22d1a5eb575274edb9c  Source/CityMaterializationProof/CityMaterializationActor.cpp
359860424eff81f46fa669577faf40b46865ec91596e3ccffd12b77b094a47ff  Source/CityMaterializationProof/CityProofGameMode.cpp
bd63d7fe2b9bcf6d16cd72d1a25997f3057061dc32dc1ec06a083699f3f726e0  Source/CityMaterializationProof/CityProofCharacter.cpp
```

## Verification

1. The causal source remained green:

   ```text
   PYTHONDONTWRITEBYTECODE=1 python3 test_kernel.py
   Ran 8 tests in 0.008s — OK
   ```

2. The Unreal target compiled successfully with UE 5.8, Mac Development:

   ```text
   CityMaterializationProofEditor Mac Development
   Result: Succeeded
   ```

3. The primary runtime launched with `-game -CityProof=Primary`. Its local Unreal log recorded:

   ```text
   Materialized authoritative record Primary — Fire closes Ash Bridge
   (d08e69d6b5fde3b27d10fb45f3bfd6143d856750c2dfd91f7b5851674fbeed76)
   ```

   Native first-person inspection showed the player standing on the proof floor, an active fire closing Ash Bridge, and gang-control geometry in Docklands.

4. The counterfactual runtime launched with `-game -CityProof=Counterfactual`. Its local Unreal log recorded:

   ```text
   Materialized authoritative record Counterfactual — No fire
   (0b27ed07131ab5889d820476ef7d665c1f5c046872ea895b93b764801e7c7206)
   ```

   Native first-person inspection showed the same grounded proof space with Ash Bridge open, police present, and Docklands contested. It did not show the primary path's fire closure or gang-control geometry.

The runtime logs are local diagnostic evidence under `~/Library/Logs/CityMaterializationProof/`; source hashes and the canonical record hashes above make the record independently repeatable.

## Corrective record

The first visual run exposed two presentation defects: the pawn lacked an explicitly collision-profiled proof floor, and labels faced away from the crew's approach. Neither was accepted as evidence. The final source adds a blocking floor at map `Z = 0`, spawns the player onto it, sets the controller's view target explicitly, and orients labels toward the initial approach. The final build and both final runs are the evidence recorded here.

## Result

**Pass.** The two authoritative records produce distinct, coherent, playable first-person embodiments. Unreal does not reroll either result. The proof does not yet establish the reverse player-to-city persistence boundary, production-scale streaming, or a full city simulation.
