# City Materialization Proof

Unreal Engine 5.8 C++ proof that frozen Ash Crossing authoritative records cross into a real, walkable first-person scene without being contradicted or rerolled.

The project reads a selected record and materializes only its permitted facts. The baseline records are under `Content/ProofRecords/`:

- `Primary`: the fire closes Ash Bridge; police remain at A; Docklands is under gang control.
- `Counterfactual`: Ash Bridge is open; police reach Docklands; ownership remains contested.

No strategic simulation runs in Unreal. The Python kernel remains the causal authority. This project proves only the FPS/materialization boundary.

The player begins on a collision floor at the proof map's `Z = 0` elevation. It is deliberate proof geometry, not a simulated city fact.

## Build

```sh
"/Users/Shared/Epic Games/UE_5.8/Engine/Build/BatchFiles/Mac/Build.sh" \
  CityMaterializationProofEditor Mac Development \
  -project="/Users/boandersson/Desktop/Games/THE_CITY/CityMaterializationProof/CityMaterializationProof.uproject"
```

## Run

```sh
"/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor" \
  "/Users/boandersson/Desktop/Games/THE_CITY/CityMaterializationProof/CityMaterializationProof.uproject" \
  -game -CityProof=Primary
```

Replace `Primary` with `Counterfactual` to load the no-fire record. Use WASD and mouse to move through the first-person proof scene.

## Acceptance

The primary scene may not show an open bridge, police at Docklands, or rival ownership. The counterfactual scene may not show the closed bridge, gang control, or absent police. The scene surface exposes the loaded record name and canonical hash prefix for review.

The recorded verification is in [Unreal Materialization Proof Evidence — v0.1.0](../Unreal%20Materialization%20Proof%20Evidence%20-%20v0.1.0.md).

## Bridge-access persistence round trip

The Unreal scene can emit a **proposal**, never city state. Generate the canonical seed record first:

```sh
cd "/Users/boandersson/Desktop/Games/THE_CITY/proof_kernel"
PYTHONDONTWRITEBYTECODE=1 python3 roundtrip.py write-seed \
  --output ../CityMaterializationProof/Content/ProofRecords/BridgeAccessRoundTripSeed.json
```

Run that seed in Unreal, then press `E` while near the cyan bridge-access console. This changes the disposable local FPS scene and writes only `RuntimeExchange/physical_destroy_E_AB_0001.json`.

```sh
"/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor" \
  "/Users/boandersson/Desktop/Games/THE_CITY/CityMaterializationProof/CityMaterializationProof.uproject" \
  -game \
  -CityProofRecord="/Users/boandersson/Desktop/Games/THE_CITY/CityMaterializationProof/Content/ProofRecords/BridgeAccessRoundTripSeed.json" \
  -CityProofExchange="/Users/boandersson/Desktop/Games/THE_CITY/CityMaterializationProof/RuntimeExchange"
```

Only the Python canonical transaction layer may accept that proposal:

```sh
cd "/Users/boandersson/Desktop/Games/THE_CITY/proof_kernel"
PYTHONDONTWRITEBYTECODE=1 python3 roundtrip.py apply \
  --record ../CityMaterializationProof/Content/ProofRecords/BridgeAccessRoundTripSeed.json \
  --proposal ../CityMaterializationProof/RuntimeExchange/physical_destroy_E_AB_0001.json \
  --output ../CityMaterializationProof/RuntimeExchange/committed_record.json \
  --ledger ../CityMaterializationProof/RuntimeExchange/causal_ledger.json
```

Terminate the first Unreal process. Start a fresh process with `-CityProofRecord` set to `RuntimeExchange/committed_record.json`. It must rematerialize a destroyed, impassable bridge access point without showing an active fire.

The complete passing record is [Bridge Access Persistence Round-Trip Evidence — v0.1.0](../Bridge%20Access%20Persistence%20Round-Trip%20Evidence%20-%20v0.1.0.md).
