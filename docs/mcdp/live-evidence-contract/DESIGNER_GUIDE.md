# Designer guide

Keep the two domains, two candidates, one shared resource and one canonical boundary fixed. Design the additive plugin around the frozen operation schedule. Keep proposal intake, canonical resolution and local representation separate.

Implement only the eleven planned source paths. Do not rewrite old game source or predecessor records. Preserve complete raw world enumeration, original-process identity, dispatch ordering, immutable record delivery and the independent verifier. CONTRACT_LAWS.md retains every schema, algorithm, failure condition and ownership rule.

P8 supplies an offline frozen obligation-plan compiler. It authenticates the source before every compile and detaches returned plans. It covers all 35 case plans and the frozen artifact obligations. Its output does not prove a physical Unreal run.

New scenarios, retries, re-admission, recovery, networking and production scale are outside this candidate. A successor requires an explicit version and a newly sealed contract.

The exact contract projection follows. Historical review labels remain unchanged.

```json
{
  "schema": "city.mcdp.documentation.v1",
  "document": "DESIGNER_GUIDE.md",
  "contract_sha256": "b862ceba039b1f2f418b01fe32221f14f095ce4894d163077b4eaa31dd0a8755",
  "projection": {
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
    "exclusions": [
      "networking",
      "open_ended_live_collection",
      "autonomous_batch_members",
      "additional_input_classes",
      "physical_movement",
      "multiple_subjects",
      "streaming",
      "randomness",
      "retry",
      "re_admission",
      "recovery",
      "production_scale",
      "trusted_ci"
    ],
    "planned_source_paths": [
      "proof_kernel/live_cross_domain_evidence_round_trip.py",
      "proof_kernel/live_cross_domain_evidence_round_trip_harness.py",
      "proof_kernel/verify_live_cross_domain_evidence_round_trip_release.py",
      "proof_kernel/test_live_cross_domain_evidence_round_trip.py",
      "CityMaterializationProof/Plugins/CityLiveEvidenceProof/CityLiveEvidenceProof.uplugin",
      "CityMaterializationProof/Plugins/CityLiveEvidenceProof/Source/CityLiveEvidenceProof/CityLiveEvidenceProof.Build.cs",
      "CityMaterializationProof/Plugins/CityLiveEvidenceProof/Source/CityLiveEvidenceProof/Private/CityLiveEvidenceProofModule.cpp",
      "CityMaterializationProof/Plugins/CityLiveEvidenceProof/Source/CityLiveEvidenceProof/Public/CityLiveEvidenceGameMode.h",
      "CityMaterializationProof/Plugins/CityLiveEvidenceProof/Source/CityLiveEvidenceProof/Private/CityLiveEvidenceGameMode.cpp",
      "CityMaterializationProof/Plugins/CityLiveEvidenceProof/Source/CityLiveEvidenceProof/Public/CityLiveEvidenceActors.h",
      "CityMaterializationProof/Plugins/CityLiveEvidenceProof/Source/CityLiveEvidenceProof/Private/CityLiveEvidenceActors.cpp"
    ],
    "operation_schedule": {
      "prefixes": {
        "P0": [
          "launch A",
          "launch B",
          "ready A",
          "ready B",
          "observe and bind A",
          "observe and bind B",
          "materialize_0001 A",
          "materialize_0001 B",
          "inspect_L0 A",
          "inspect_L0 B",
          "liveness L0"
        ],
        "P1": [
          "P0",
          "emit_0001 A",
          "emit_0001 B",
          "inspect_L1 A",
          "inspect_L1 B",
          "liveness L1"
        ],
        "P2": [
          "P1",
          "admit QA on R0",
          "admit QB on R0",
          "construct primary fixture batch",
          "inspect_L2 A",
          "inspect_L2 B",
          "liveness L2"
        ],
        "P3": [
          "P2",
          "invalidate both current claims",
          "liveness before_resolve",
          "resolve once and publish exact R1",
          "liveness after_resolve",
          "classify both stale",
          "inspect_L3 A",
          "inspect_L3 B",
          "liveness L3"
        ],
        "P4": [
          "P3",
          "materialize_0002 first refresh domain",
          "inspect_L4 A",
          "inspect_L4 B",
          "liveness L4"
        ],
        "P5": [
          "P4",
          "materialize_0002 second refresh domain",
          "inspect_L5 A",
          "inspect_L5 B",
          "liveness L5"
        ]
      },
      "witness_variations": "W1-W8 substitute only the listed emission order, presentation order at admission/construction, and refresh order. Wait for both physical event and response before emitting the peer; serialized parent requests establish cross-process order without comparing child clocks. F/C cases use A then B unless explicitly stated.",
      "terminal": "After each expected failure take inspect_terminal once in each surviving original domain and terminal liveness. Faulted child still answers this read-only census. No further materialize/emit/resolve. Then shutdown live originals, poll until exits, kill only task-owned children on timeout, drain streams and record cleanup liveness. F07 replacement receives no bind/materialize after detection.",
      "publish_edge": "resolve call logs immutable before/input bytes. A successful return is validated and installed as parent head exactly once before after_resolve sample. Physical failure cannot roll this back. C fault throws before install; no returned successor is fabricated."
    },
    "process_input_contract": {
      "cwd": "Exact realpath of /Users/boandersson/Projects/CITY for parent build and each child. No branching on cwd.",
      "identity_acquisition": "Parent collects PID/PPID/birth tuple via proc_pidinfo, executable via proc_pidpath, cwd/vnode identities via proc_pidinfo, fd kernel records via PROC_PIDLISTFDS/PROC_PIDFDINFO and lsof, and loaded images from child dyld list cross-checked against parent vmmap/lsof. Retain raw normalized process_observation records before bind and in every liveness sample. Never fill parent observations from a previous receipt.",
      "handshake": "Child emits startup once after GameMode/world creation and before receiving bind. Parent independently checks input inventories and initial world contract, computes binding and sends bind_0001. Child compares its actual startup/body identities to parent binding, replies bind_ack with startup_sha256. No Actors/materialization/emit before successful bind. Explicit actual GameMode mismatch rejects; URL fallback is never accepted.",
      "descriptors": "At exec inherit only original stdin-read, stdout-write and stderr-write pipes. Record parent and child endpoint kernel IDs, peer IDs, access and holder PID/fd tuples. Dynamic engine descriptors are inventoried but never read by proof code. Match proof endpoints at every liveness sample. Extra holder (including helper process) of any proof pipe causes terminal acquisition failure. Close/drain task pipes, terminate only task-owned descendants by observed PID/birth; never kill unrelated Trace/Zen service. No helper startup retry inside a case.",
      "config": "Pin all project Config bytes from unchanged_dependencies. Fresh domain home/user/tmp contain no prior Saved/Config. Engine config/plugin inputs belong to build_record.external_inputs and must match every run. Proof code must not consult GConfig, environment, file paths, engine settings, controller/input, arbitrary reflection or time for Q/projection/admission/owner/fault choice. Map/GameMode startup settings are checked as actual world facts. Unresolved or unexplained semantic config reads reject.",
      "inventory_acceptance": "Inventory equality alone is not semantic acceptance. Each input has the classification below and a source-audit edge; any platform-to-proof-decision edge rejects even when all hashes match. Compiled images can be acquired later, but acceptance procedure cannot change after freeze.",
      "classifications": {
        "canonical_bytes": "exact representation input only; canonical computation Python-owned",
        "stdin": "binding and declared command grammar only",
        "argv": "domain/witness/launch/root and fixed activation only; no canonical or owner selection",
        "environment_cwd": "provenance only",
        "config_engine_plugins_images": "compiled code/platform identity and startup only",
        "world_slots": "physical emission and independent observation only",
        "stderr_clock_pid": "provenance/liveness only; no canonical consequence"
      },
      "source_audit": "Before acquisition, independently enumerate all functions/methods in the four new Python and seven plugin files plus transitive local imports. Record every external-input-to-function and function-to-consequence edge as source_edge. Trace call sites through helper functions; reject dynamic import/eval/exec and unclassified C++ reflection/delegates. Canonical resolve/admit calls only in parent harness and independent verifier; Unreal has no canonical mutation edge. Probe cannot read expected projection or receipts. Only command dispatch may call Actor interaction; only the five declared arm hooks may mutate fault state. Canonical module/kernel bytes remain exact.",
      "source_negative_cases": [
        "GConfig_owner_read",
        "getenv_Q_choice",
        "argv_canonical_order",
        "clock_member_order",
        "PID_owner_choice",
        "peer_root_read",
        "canonical_output_write_from_child",
        "probe_reads_receipt",
        "probe_reads_projection",
        "echoed_Q_without_actor",
        "unlisted_local_import",
        "controller_calls_emit",
        "fault_bypasses_stage",
        "helper_holds_proof_pipe"
      ],
      "source_negative_execution": "Future unittest module creates one temporary source mutation for each named forbidden edge; runs the same independent audit and asserts lcer.source_input_forbidden plus the exact offending source/function/input edge. Helper case uses an offline pipe-holder fixture and asserts lcer.proof_pipe_extra_holder, not a claimed Unreal run. Positives audit actual candidate source with zero unclassified edges. Save argv, raw edges and rejected mutation IDs in build.source_audit. No arbitrary success flag can substitute."
    }
  },
  "live_acceptance_verified": false,
  "game_implementation_authorized": false,
  "game_sealed": false,
  "trusted_ci": false
}
```
