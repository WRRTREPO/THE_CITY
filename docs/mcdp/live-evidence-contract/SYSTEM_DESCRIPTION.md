# System description

Two original Unreal processes stay alive. Each domain proposes its evidence from its own physical resource Actor. Python resolves the fixed QA/QB batch once. Both original domains then display the owner from the same committed R1 bytes.

Python owns canonical city truth. Unreal owns proposals and representation. The world probe reads every world context and loaded Actor slot on the game thread. It receives no expected owner, head or generation. The verifier derives success from raw rows and independently decoded records. Extra Actors, stale generations, wrong worlds and mixed heads reject.

MCDP has proved the offline implementation contract. Live acquisition remains ahead. The full 43-field contract is preserved in CONTRACT_LAWS.md. No law is reduced to this description.

The exact contract projection follows. Historical review labels remain unchanged.

```json
{
  "schema": "city.mcdp.documentation.v1",
  "document": "SYSTEM_DESCRIPTION.md",
  "contract_sha256": "b862ceba039b1f2f418b01fe32221f14f095ce4894d163077b4eaa31dd0a8755",
  "projection": {
    "identity": {
      "proof": "Live Cross-Domain Evidence Round-Trip Proof",
      "version": "0.1.0-draft.3",
      "phase": 5,
      "status": "specification_review",
      "implementation_authorized": false,
      "evidence_sealed": false
    },
    "scope": {
      "domains": [
        "domain_A",
        "domain_B"
      ],
      "candidate_inputs": [
        "QA",
        "QB"
      ],
      "resource": "shared_slot_01",
      "canonical_records": [
        "R0",
        "R1"
      ],
      "canonical_boundaries": 1,
      "fixed_candidate_set": true,
      "original_processes_required": true,
      "canonical_source": "proof_kernel/concurrent_external_evidence_arbitration.py",
      "canonical_order": [
        "occurrence_time",
        "external_phase",
        "canonical_external_priority",
        "input_id"
      ],
      "canonical_mutation_owner": "python_resolver",
      "unreal_authority": "proposal_and_representation_only",
      "predecessor_bytes_mutable": false
    },
    "runtime": {
      "project": "CityMaterializationProof/CityMaterializationProof.uproject",
      "engine": "/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor",
      "integration": "additive_runtime_plugin",
      "plugin": "CityMaterializationProof/Plugins/CityLiveEvidenceProof",
      "game_mode": "/Script/CityLiveEvidenceProof.CityLiveEvidenceGameMode",
      "map": "/Engine/Maps/Entry",
      "transport": "parent_child_pipes",
      "canonical_state_to_child": "immutable_committed_record_bytes_plus_projection_on_stdin",
      "timeout_seconds": 60,
      "timeout_effect": "terminal_witness_failure_without_membership_change",
      "output_root": "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords"
    },
    "world_oracle": {
      "selected_world": "Exactly one non-preview game UWorld with WorldType=Game and package /Engine/Maps/Entry; reject missing/second game world or actual GetAuthGameMode class unequal to /Script/CityLiveEvidenceProof.CityLiveEvidenceGameMode. Retain every GEngine world context, not just selected context.",
      "enumeration": "On the game thread, traverse every loaded level Actor array in every world context, including pending-destruction Actors. Flatten level paths sorted lexically, then native array index. visited_slots must be 0..actor_array_size-1 exactly; null_slots records null entries. actors contains one row for every non-null entry, sorted by actor_path, with no duplicates. actor_array_size sums all loaded level arrays. Fail if context/level/array changes during traversal; never return partial success.",
      "actor_identity": "actor_path is UObject GetPathName(); actor_id is world_path + | + actor_path. class_path is actual GetClass()->GetPathName(). Never infer generation/role from actor ID.",
      "relevant_predicate": "Any Actor whose class derives from /Script/CityLiveEvidenceProof.CityLiveEvidenceActor OR whose role slot is head_anchor/resource_state OR whose class belongs to /Script/CityMaterializationProof is relevant. The old module may be loaded; none of its Actors may exist. No relevant Actor may exist in another world. Include pending-kill Actors until removed from arrays.",
      "raw_slots": "Read role, domain, generation, record_raw_sha256 and allocation_owner from each actual Actor. Non-proof Actors have role/domain/record/generation null. Resource Actor doubles as the domain-local interaction surface; no third proof Actor. Head anchor owner is null. Resource owner is derived from its own physical slot.",
      "derive": "Verifier derives counts and sorted IDs by filtering raw rows. Success requires exactly one live head_anchor and one live resource_state, same domain, record and generation as independently decoded canonical bytes. R0 resource owner=null; R1 resource owner=domain_A. Both anchor and resource bind the same raw record; anchor owner remains null. Any extra, pending, wrong-world, old-generation or mismatched row rejects. Summaries must equal derived values; heterogeneous head/generation yields null summaries and never success.",
      "startup": "At ready and before materialization: zero relevant Actors, zero Pawns, exactly one /Script/Engine.PlayerController with null Pawn, every Actor AutoReceiveInput=Disabled(0). GameMode explicitly sets DefaultPawnClass and SpectatorClass null and suppresses pawn spawning; no proof callback from controller/input/tick except the declared stdin dispatch. Check the actual world, not config intentions.",
      "negative_cases": [
        "mixed_head_resource_generation",
        "wrong_world",
        "omitted_actor_row",
        "duplicate_slot",
        "missing_slot",
        "extra_old_actor",
        "pending_kill_actor",
        "wrong_resource_owner",
        "unexpected_pawn",
        "wrong_game_mode"
      ],
      "probe_independence": "Probe entry receives no projection/receipt/expected owner/head/generation. It reads UWorld and raw Actors only. Wrapper binding comes from routing after enumeration; a failure selector cannot change probe output."
    },
    "record_delivery": {
      "channel": "materialize_input on original stdin; no child-side file lookup, embedded R0 copy, or peer input",
      "R0": "Before materialize_0001, bind succeeds. Parent sends exact pinned stored R0 UTF-8 plus exact stored_receipt_bytes(launch_receipt(R0)) and the R0 projection. Child strictly parses both; verifies raw bytes, canonical digest, exact fixture schema/value identities and all launch receipt fields with the same acceptance semantics as validate_launch_artifact. It computes both digests from received bytes, never echoes supplied digests. Only then create Actors and issue old acceptance receipt. Emission reads this accepted R0 and physical Actor; no Q template supplied by parent.",
      "R1": "After the parent publishes the one resolver result, materialize_0002 carries those exact committed R1 bytes plus matching R1 projection and launch_receipt_raw_utf8=null. Child validates strict serialization, exact pinned R1 identity, parent/source ancestry, generation=1, owner=domain_A and original binding. validate_launch_artifact is R0-only and is NOT called or claimed for R1. Issue only the new r1_receipt after publication. Child does not resolve or mutate canonical data.",
      "ordering": "materialize_0001 may occur once before emit; materialize_0002 once after L3. Failed authentication precedes Actor destruction. Successful R1 authentication disables proposal capability permanently. Harness will not send R1 before successful resolver publication.",
      "negative_bytes": "Offline verifier adversaries remove R0 LF, add second LF, replace one byte, alter only launch receipt raw hash, change only projection owner, send R1 with an R0 launch receipt, and send a provisional working-state object. All reject before accepted materialization. These are byte-contract tests, not live runs."
    }
  },
  "live_acceptance_verified": false,
  "game_implementation_authorized": false,
  "game_sealed": false,
  "trusted_ci": false
}
```
