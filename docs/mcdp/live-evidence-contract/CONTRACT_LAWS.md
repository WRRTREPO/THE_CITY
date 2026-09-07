# Frozen contract laws

These are the exact frozen contract bytes. All 43 fields remain binding. Human summaries in this document set do not replace any term. Historical review labels remain historical; PHASE_5_FREEZE.json records the later accepted freeze.

```json
{
  "schema": "city.live_cross_domain_evidence_spec.v1",
  "identity": {
    "proof": "Live Cross-Domain Evidence Round-Trip Proof",
    "version": "0.1.0-draft.3",
    "phase": 5,
    "status": "specification_review",
    "implementation_authorized": false,
    "evidence_sealed": false
  },
  "predecessors": {
    "Concurrent External Evidence Arbitration Proof - Draft.md": "d00a867aae53cd8f58817532bdd85d9eb2e3c5686c04f881015dc9720e6f9ecd",
    "Concurrent External Evidence Arbitration Proof Evidence - v0.1.0.md": "72f1e2db17500cd75b422904195fbdbd2cda375b3cab0a73dbfdbf4ca06fc2f5",
    "Cross-Domain Canonical Occupancy Materialization Proof - Draft.md": "47889ac299cf2cfbea143a6a529b1253826e74ae9ddc83f0b25903117ff9406d",
    "Cross-Domain Canonical Occupancy Materialization Proof Evidence - v0.1.0.md": "4a8146b507f5d8542abd742ee3b6da93d0368af4f98f5f8837f1d923c8598026",
    "proof_kernel/concurrent_external_evidence_arbitration.py": "c2f8c3543a1ef954ec57f5d3dbc28df9260310241c5f590747032dcf555e0690"
  },
  "canonical_records": {
    "proof_kernel/ConcurrentExternalEvidenceArbitrationProofRecords/concurrent_external_QA.json": "57e3a15fbe844e232ab738a6b44828e3a9b74d31095bdf2f327f4159fe164ad4",
    "proof_kernel/ConcurrentExternalEvidenceArbitrationProofRecords/concurrent_external_QB.json": "ddc12eba2d928961502a22d6095d9317b436ff0d648574cb08edb49254351650",
    "proof_kernel/ConcurrentExternalEvidenceArbitrationProofRecords/concurrent_external_R0.json": "8cea1aa6ae3ab2d7a25b6b660c91c26d26a1340ab4f2b67e134f7b7feb12cb12",
    "proof_kernel/ConcurrentExternalEvidenceArbitrationProofRecords/concurrent_external_R1.json": "8e2862666a75833c8cff5c1faf9b783fb1d694de9df94fb5a4663fef599ea63c"
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
  "witnesses": [
    {
      "id": "W1",
      "emission": [
        "domain_A",
        "domain_B"
      ],
      "presentation": [
        "domain_A",
        "domain_B"
      ],
      "refresh": [
        "domain_A",
        "domain_B"
      ]
    },
    {
      "id": "W2",
      "emission": [
        "domain_A",
        "domain_B"
      ],
      "presentation": [
        "domain_A",
        "domain_B"
      ],
      "refresh": [
        "domain_B",
        "domain_A"
      ]
    },
    {
      "id": "W3",
      "emission": [
        "domain_A",
        "domain_B"
      ],
      "presentation": [
        "domain_B",
        "domain_A"
      ],
      "refresh": [
        "domain_A",
        "domain_B"
      ]
    },
    {
      "id": "W4",
      "emission": [
        "domain_A",
        "domain_B"
      ],
      "presentation": [
        "domain_B",
        "domain_A"
      ],
      "refresh": [
        "domain_B",
        "domain_A"
      ]
    },
    {
      "id": "W5",
      "emission": [
        "domain_B",
        "domain_A"
      ],
      "presentation": [
        "domain_A",
        "domain_B"
      ],
      "refresh": [
        "domain_A",
        "domain_B"
      ]
    },
    {
      "id": "W6",
      "emission": [
        "domain_B",
        "domain_A"
      ],
      "presentation": [
        "domain_A",
        "domain_B"
      ],
      "refresh": [
        "domain_B",
        "domain_A"
      ]
    },
    {
      "id": "W7",
      "emission": [
        "domain_B",
        "domain_A"
      ],
      "presentation": [
        "domain_B",
        "domain_A"
      ],
      "refresh": [
        "domain_A",
        "domain_B"
      ]
    },
    {
      "id": "W8",
      "emission": [
        "domain_B",
        "domain_A"
      ],
      "presentation": [
        "domain_B",
        "domain_A"
      ],
      "refresh": [
        "domain_B",
        "domain_A"
      ]
    }
  ],
  "checkpoints": [
    {
      "id": "L0",
      "canonical": "R0",
      "domain_A": "current_R0",
      "domain_B": "current_R0"
    },
    {
      "id": "L1",
      "canonical": "R0",
      "domain_A": "emitted_QA",
      "domain_B": "emitted_QB"
    },
    {
      "id": "L2",
      "canonical": "R0",
      "domain_A": "batch_admitted",
      "domain_B": "batch_admitted"
    },
    {
      "id": "L3",
      "canonical": "R1",
      "domain_A": "stale_R0",
      "domain_B": "stale_R0"
    },
    {
      "id": "L4",
      "canonical": "R1",
      "domain_A": "refresh_order_dependent",
      "domain_B": "refresh_order_dependent"
    },
    {
      "id": "L5",
      "canonical": "R1",
      "domain_A": "current_R1",
      "domain_B": "current_R1"
    }
  ],
  "failure_cases": [
    {
      "id": "F01",
      "trigger": "missing_Q",
      "boundary": "before_commit",
      "failure_code": "LCER_INPUT_SET_INVALID",
      "canonical_remains": "R0",
      "affected_representation": "unavailable",
      "runs": [
        "F01"
      ]
    },
    {
      "id": "F02",
      "trigger": "malformed_Q",
      "boundary": "before_commit",
      "failure_code": "LCER_EVIDENCE_INVALID",
      "canonical_remains": "R0",
      "affected_representation": "unavailable",
      "runs": [
        "F02"
      ]
    },
    {
      "id": "F03",
      "trigger": "redirected_Q",
      "boundary": "before_commit",
      "failure_code": "LCER_EVIDENCE_INVALID",
      "canonical_remains": "R0",
      "affected_representation": "unavailable",
      "runs": [
        "F03"
      ]
    },
    {
      "id": "F04",
      "trigger": "duplicate_input_or_event",
      "boundary": "before_commit",
      "failure_code": "LCER_INPUT_SET_INVALID",
      "canonical_remains": "R0",
      "affected_representation": "unavailable",
      "runs": [
        "F04a",
        "F04b"
      ]
    },
    {
      "id": "F05",
      "trigger": "stale_source_record",
      "boundary": "before_commit",
      "failure_code": "LCER_STALE_EVIDENCE",
      "canonical_remains": "R0",
      "affected_representation": "unavailable",
      "runs": [
        "F05"
      ]
    },
    {
      "id": "F06",
      "trigger": "incompatible_consequence",
      "boundary": "before_commit",
      "failure_code": "LCER_EVIDENCE_INVALID",
      "canonical_remains": "R0",
      "affected_representation": "unavailable",
      "runs": [
        "F06"
      ]
    },
    {
      "id": "F07",
      "trigger": "process_replacement_before_commit",
      "boundary": "before_commit",
      "failure_code": "LCER_PROCESS_INVALID",
      "canonical_remains": "R0",
      "affected_representation": "unavailable",
      "runs": [
        "F07"
      ]
    },
    {
      "id": "F08",
      "trigger": "source_exit_before_complete_set",
      "boundary": "before_commit",
      "failure_code": "LCER_PROCESS_INVALID",
      "canonical_remains": "R0",
      "affected_representation": "unavailable",
      "runs": [
        "F08"
      ]
    },
    {
      "id": "F09",
      "trigger": "provisional_state_as_projection",
      "boundary": "before_commit",
      "failure_code": "LCER_PROJECTION_INVALID",
      "canonical_remains": "R0",
      "affected_representation": "unavailable",
      "runs": [
        "F09"
      ]
    },
    {
      "id": "F10",
      "trigger": "replay_after_commit",
      "boundary": "after_commit",
      "failure_code": "LCER_STALE_EVIDENCE",
      "canonical_remains": "R1",
      "affected_representation": "unchanged",
      "runs": [
        "F10a",
        "F10b"
      ]
    },
    {
      "id": "F11",
      "trigger": "domain_A_exit_after_commit",
      "boundary": "after_commit",
      "failure_code": "LCER_PROCESS_INVALID",
      "canonical_remains": "R1",
      "affected_representation": "unavailable",
      "runs": [
        "F11"
      ]
    },
    {
      "id": "F12",
      "trigger": "domain_B_exit_after_commit",
      "boundary": "after_commit",
      "failure_code": "LCER_PROCESS_INVALID",
      "canonical_remains": "R1",
      "affected_representation": "unavailable",
      "runs": [
        "F12"
      ]
    },
    {
      "id": "F13",
      "trigger": "domain_A_partial_refresh",
      "boundary": "after_commit",
      "failure_code": "LCER_REFRESH_INVALID",
      "canonical_remains": "R1",
      "affected_representation": "unavailable_partial_R1_without_anchor",
      "runs": [
        "F13"
      ]
    },
    {
      "id": "F14",
      "trigger": "domain_B_partial_refresh",
      "boundary": "after_commit",
      "failure_code": "LCER_REFRESH_INVALID",
      "canonical_remains": "R1",
      "affected_representation": "unavailable_partial_R1_without_anchor",
      "runs": [
        "F14"
      ]
    },
    {
      "id": "F15",
      "trigger": "valid_receipt_wrong_live_owner",
      "boundary": "after_commit",
      "failure_code": "LCER_OBSERVATION_INVALID",
      "canonical_remains": "R1",
      "affected_representation": "stale",
      "runs": [
        "F15"
      ]
    },
    {
      "id": "F16",
      "trigger": "duplicate_or_old_generation_actor",
      "boundary": "after_commit",
      "failure_code": "LCER_OBSERVATION_INVALID",
      "canonical_remains": "R1",
      "affected_representation": "stale",
      "runs": [
        "F16a",
        "F16b"
      ]
    },
    {
      "id": "F17",
      "trigger": "stale_projection_after_commit",
      "boundary": "after_commit",
      "failure_code": "LCER_PROJECTION_INVALID",
      "canonical_remains": "R1",
      "affected_representation": "stale",
      "runs": [
        "F17"
      ]
    },
    {
      "id": "F18",
      "trigger": "altered_refresh_binding",
      "boundary": "after_commit",
      "failure_code": "LCER_PROCESS_INVALID",
      "canonical_remains": "R1",
      "affected_representation": "stale",
      "runs": [
        "F18"
      ]
    }
  ],
  "canonical_faults": [
    "after_qa_provisional_mutation",
    "after_qb_ordinary_gate_evaluation",
    "during_replay_barrier_construction",
    "during_batch_ledger_construction",
    "after_complete_r1_before_validation",
    "after_complete_r1_validation_before_publication"
  ],
  "process_binding_fields": [
    "witness_id",
    "domain",
    "launch_id",
    "pid",
    "macos_birth_tuple",
    "executable_realpath",
    "executable_sha256",
    "project_realpath",
    "project_sha256",
    "module_inventory_sha256",
    "argv_sha256",
    "environment_sha256",
    "descriptor_map_sha256",
    "process_root_realpath",
    "cwd_sha256",
    "startup_sha256",
    "input_inventory_sha256"
  ],
  "observation_fields": [
    "schema",
    "witness_id",
    "domain",
    "launch_id",
    "operation_id",
    "binding_sha256",
    "worlds",
    "selected_world_path",
    "anchor_count",
    "resource_actor_count",
    "all_proof_actor_ids",
    "record_sha256",
    "generation",
    "allocation_owner"
  ],
  "evidence_fields": [
    "schema",
    "witness_id",
    "domain",
    "launch_id",
    "operation_id",
    "binding_sha256",
    "q_raw_sha256",
    "q_canonical_hash",
    "physical_event_id",
    "source_record_hash",
    "interaction_counter"
  ],
  "output_fields": [
    "schema",
    "proof",
    "version",
    "witness_id",
    "status",
    "failure_codes",
    "process_bindings",
    "liveness_checkpoints",
    "canonical_artifacts",
    "captured_evidence",
    "materialization_receipts",
    "live_observations",
    "head_dispositions",
    "command_trace",
    "artifact_sha256",
    "claims"
  ],
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
  "planned_commands": {
    "acquire": [
      "python3",
      "-B",
      "proof_kernel/live_cross_domain_evidence_round_trip_harness.py",
      "acquire",
      "--runtime-parent",
      "{absolute_unique_temp_root}",
      "--output",
      "{fresh_output_root}"
    ],
    "verify": [
      "python3",
      "-B",
      "proof_kernel/verify_live_cross_domain_evidence_round_trip_release.py",
      "verify",
      "--artifacts",
      "{artifact_root}"
    ],
    "test": [
      "python3",
      "-B",
      "-m",
      "unittest",
      "discover",
      "-s",
      "proof_kernel",
      "-p",
      "test_live_cross_domain_evidence_round_trip.py"
    ]
  },
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
  "cost": {
    "successful_builds_per_candidate": 1,
    "primary_pair_runs": 8,
    "primary_process_launches": 16,
    "failure_pair_runs": 21,
    "canonical_fault_pair_runs": 6,
    "total_pair_runs_per_acquisition": 35,
    "total_original_process_launches": 70,
    "replacement_process_launches": 1,
    "runtime_seconds_per_case_limit": 900,
    "total_wall_time_estimate": "unmeasured",
    "artifact_policy": "fresh_successor_artifacts_only",
    "artifact_files": 219,
    "release_members_excluding_manifest": 289
  },
  "review_gate": {
    "document_validator_proves": "structural_specification_consistency_only",
    "independent_review": "pending",
    "freeze": "pending",
    "mcdp_session": "mcdp-city-live-evidence-spec",
    "phoenix_handoff": "not_created",
    "runtime_proof": "not_run"
  },
  "wire_schemas": {
    "process_binding": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "witness_id",
        "domain",
        "launch_id",
        "pid",
        "macos_birth_tuple",
        "executable_realpath",
        "executable_sha256",
        "project_realpath",
        "project_sha256",
        "module_inventory_sha256",
        "argv_sha256",
        "environment_sha256",
        "descriptor_map_sha256",
        "process_root_realpath",
        "cwd_sha256",
        "startup_sha256",
        "input_inventory_sha256"
      ],
      "properties": {
        "witness_id": {
          "type": "string",
          "minLength": 1
        },
        "domain": {
          "enum": [
            "domain_A",
            "domain_B"
          ]
        },
        "launch_id": {
          "type": "string",
          "minLength": 1
        },
        "pid": {
          "type": "integer",
          "minimum": 0
        },
        "macos_birth_tuple": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "seconds",
            "microseconds"
          ],
          "properties": {
            "seconds": {
              "type": "integer",
              "minimum": 0
            },
            "microseconds": {
              "type": "integer",
              "minimum": 0,
              "maximum": 999999
            }
          }
        },
        "executable_realpath": {
          "type": "string",
          "minLength": 1
        },
        "executable_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "project_realpath": {
          "type": "string",
          "minLength": 1
        },
        "project_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "module_inventory_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "argv_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "environment_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "descriptor_map_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "process_root_realpath": {
          "type": "string",
          "minLength": 1
        },
        "cwd_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "startup_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "input_inventory_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        }
      }
    },
    "projection": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "schema",
        "witness_id",
        "domain",
        "launch_id",
        "operation_id",
        "binding_sha256",
        "record_role",
        "record_raw_sha256",
        "record_canonical_hash",
        "generation",
        "allocation_owner"
      ],
      "properties": {
        "schema": {
          "const": "city.live_evidence_projection.v1"
        },
        "witness_id": {
          "type": "string",
          "minLength": 1
        },
        "domain": {
          "enum": [
            "domain_A",
            "domain_B"
          ]
        },
        "launch_id": {
          "type": "string",
          "minLength": 1
        },
        "operation_id": {
          "type": "string",
          "minLength": 1
        },
        "binding_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "record_role": {
          "enum": [
            "R0",
            "R1"
          ]
        },
        "record_raw_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "record_canonical_hash": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "generation": {
          "enum": [
            0,
            1
          ]
        },
        "allocation_owner": {
          "enum": [
            null,
            "domain_A"
          ]
        }
      }
    },
    "command": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "schema",
        "witness_id",
        "domain",
        "launch_id",
        "operation_id",
        "binding_sha256",
        "command",
        "payload"
      ],
      "properties": {
        "schema": {
          "const": "city.live_evidence_command.v1"
        },
        "witness_id": {
          "type": "string",
          "minLength": 1
        },
        "domain": {
          "enum": [
            "domain_A",
            "domain_B"
          ]
        },
        "launch_id": {
          "type": "string",
          "minLength": 1
        },
        "operation_id": {
          "type": "string",
          "minLength": 1
        },
        "binding_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "command": {
          "enum": [
            "bind",
            "materialize",
            "emit",
            "inspect",
            "arm_fault",
            "shutdown"
          ]
        },
        "payload": {
          "oneOf": [
            {
              "type": "null"
            },
            {
              "$ref": "#/$defs/process_binding"
            },
            {
              "$ref": "#/$defs/materialize_input"
            },
            {
              "$ref": "#/$defs/fault_arm"
            }
          ]
        }
      }
    },
    "live_observation": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "schema",
        "witness_id",
        "domain",
        "launch_id",
        "operation_id",
        "binding_sha256",
        "worlds",
        "selected_world_path",
        "anchor_count",
        "resource_actor_count",
        "all_proof_actor_ids",
        "record_sha256",
        "generation",
        "allocation_owner"
      ],
      "properties": {
        "schema": {
          "const": "city.live_evidence_observation.v1"
        },
        "witness_id": {
          "type": "string",
          "minLength": 1
        },
        "domain": {
          "enum": [
            "domain_A",
            "domain_B"
          ]
        },
        "launch_id": {
          "type": "string",
          "minLength": 1
        },
        "operation_id": {
          "type": "string",
          "minLength": 1
        },
        "binding_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "worlds": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/world_row"
          }
        },
        "selected_world_path": {
          "type": "string",
          "minLength": 1
        },
        "anchor_count": {
          "type": "integer",
          "minimum": 0
        },
        "resource_actor_count": {
          "type": "integer",
          "minimum": 0
        },
        "all_proof_actor_ids": {
          "type": "array",
          "items": {
            "type": "string",
            "minLength": 1
          }
        },
        "record_sha256": {
          "oneOf": [
            {
              "type": "null"
            },
            {
              "type": "string",
              "pattern": "^[0-9a-f]{64}$"
            }
          ]
        },
        "generation": {
          "oneOf": [
            {
              "type": "null"
            },
            {
              "type": "integer",
              "minimum": 0
            }
          ]
        },
        "allocation_owner": {
          "enum": [
            null,
            "domain_A",
            "domain_B"
          ]
        }
      }
    },
    "emission_wrapper": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "schema",
        "witness_id",
        "domain",
        "launch_id",
        "operation_id",
        "binding_sha256",
        "q_raw_sha256",
        "q_canonical_hash",
        "physical_event_id",
        "source_record_hash",
        "interaction_counter"
      ],
      "properties": {
        "schema": {
          "const": "city.live_evidence_emission.v1"
        },
        "witness_id": {
          "type": "string",
          "minLength": 1
        },
        "domain": {
          "enum": [
            "domain_A",
            "domain_B"
          ]
        },
        "launch_id": {
          "type": "string",
          "minLength": 1
        },
        "operation_id": {
          "type": "string",
          "minLength": 1
        },
        "binding_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "q_raw_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "q_canonical_hash": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "physical_event_id": {
          "type": "string",
          "minLength": 1
        },
        "source_record_hash": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "interaction_counter": {
          "type": "integer",
          "minimum": 0
        }
      }
    },
    "materialize_input": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "projection",
        "record_raw_utf8",
        "launch_receipt_raw_utf8"
      ],
      "properties": {
        "projection": {
          "$ref": "#/$defs/projection"
        },
        "record_raw_utf8": {
          "type": "string",
          "minLength": 1
        },
        "launch_receipt_raw_utf8": {
          "oneOf": [
            {
              "type": "null"
            },
            {
              "type": "string",
              "minLength": 1
            }
          ]
        }
      }
    },
    "error": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "code",
        "underlying_code",
        "stage"
      ],
      "properties": {
        "code": {
          "type": "string",
          "minLength": 1
        },
        "underlying_code": {
          "type": "string",
          "minLength": 1
        },
        "stage": {
          "type": "string",
          "minLength": 1
        }
      }
    },
    "artifact_hash": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "path",
        "sha256",
        "size_bytes"
      ],
      "properties": {
        "path": {
          "type": "string",
          "minLength": 1
        },
        "sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "size_bytes": {
          "type": "integer",
          "minimum": 0
        }
      }
    },
    "file_identity": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "realpath",
        "sha256",
        "size_bytes"
      ],
      "properties": {
        "realpath": {
          "type": "string",
          "minLength": 1
        },
        "sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "size_bytes": {
          "type": "integer",
          "minimum": 0
        }
      }
    },
    "image_identity": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "realpath",
        "sha256",
        "macho_uuid",
        "architecture",
        "source"
      ],
      "properties": {
        "realpath": {
          "type": "string",
          "minLength": 1
        },
        "sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "macho_uuid": {
          "type": "string",
          "minLength": 1
        },
        "architecture": {
          "type": "string",
          "minLength": 1
        },
        "source": {
          "enum": [
            "dyld",
            "dyld_shared_cache"
          ]
        }
      }
    },
    "descriptor": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "pid",
        "fd",
        "kind",
        "kernel_id",
        "peer_kernel_id",
        "access",
        "path"
      ],
      "properties": {
        "pid": {
          "type": "integer",
          "minimum": 0
        },
        "fd": {
          "type": "integer",
          "minimum": 0
        },
        "kind": {
          "enum": [
            "pipe",
            "vnode",
            "socket",
            "kqueue",
            "other"
          ]
        },
        "kernel_id": {
          "type": "string",
          "minLength": 1
        },
        "peer_kernel_id": {
          "oneOf": [
            {
              "type": "null"
            },
            {
              "type": "string",
              "minLength": 1
            }
          ]
        },
        "access": {
          "enum": [
            "read",
            "write",
            "read_write"
          ]
        },
        "path": {
          "oneOf": [
            {
              "type": "null"
            },
            {
              "type": "string",
              "minLength": 1
            }
          ]
        }
      }
    },
    "environment": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "HOME",
        "TMPDIR",
        "USER",
        "LOGNAME",
        "PATH",
        "LANG",
        "LC_ALL"
      ],
      "properties": {
        "HOME": {
          "type": "string"
        },
        "TMPDIR": {
          "type": "string"
        },
        "USER": {
          "type": "string"
        },
        "LOGNAME": {
          "type": "string"
        },
        "PATH": {
          "type": "string"
        },
        "LANG": {
          "type": "string"
        },
        "LC_ALL": {
          "type": "string"
        }
      }
    },
    "actor_row": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "actor_id",
        "actor_path",
        "class_path",
        "world_path",
        "role",
        "domain",
        "record_raw_sha256",
        "generation",
        "allocation_owner",
        "pending_kill",
        "auto_receive_input"
      ],
      "properties": {
        "actor_id": {
          "type": "string",
          "minLength": 1
        },
        "actor_path": {
          "type": "string",
          "minLength": 1
        },
        "class_path": {
          "type": "string",
          "minLength": 1
        },
        "world_path": {
          "type": "string",
          "minLength": 1
        },
        "role": {
          "oneOf": [
            {
              "type": "null"
            },
            {
              "enum": [
                "head_anchor",
                "resource_state"
              ]
            }
          ]
        },
        "domain": {
          "oneOf": [
            {
              "type": "null"
            },
            {
              "enum": [
                "domain_A",
                "domain_B"
              ]
            }
          ]
        },
        "record_raw_sha256": {
          "oneOf": [
            {
              "type": "null"
            },
            {
              "type": "string",
              "pattern": "^[0-9a-f]{64}$"
            }
          ]
        },
        "generation": {
          "oneOf": [
            {
              "type": "null"
            },
            {
              "type": "integer",
              "minimum": 0
            }
          ]
        },
        "allocation_owner": {
          "enum": [
            null,
            "domain_A",
            "domain_B"
          ]
        },
        "pending_kill": {
          "type": "boolean"
        },
        "auto_receive_input": {
          "type": "integer",
          "minimum": 0
        }
      }
    },
    "world_row": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "world_path",
        "world_type",
        "game_mode_class",
        "actor_array_size",
        "visited_slots",
        "null_slots",
        "actors"
      ],
      "properties": {
        "world_path": {
          "type": "string",
          "minLength": 1
        },
        "world_type": {
          "type": "string",
          "minLength": 1
        },
        "game_mode_class": {
          "oneOf": [
            {
              "type": "null"
            },
            {
              "type": "string",
              "minLength": 1
            }
          ]
        },
        "actor_array_size": {
          "type": "integer",
          "minimum": 0
        },
        "visited_slots": {
          "type": "array",
          "items": {
            "type": "integer",
            "minimum": 0
          }
        },
        "null_slots": {
          "type": "array",
          "items": {
            "type": "integer",
            "minimum": 0
          }
        },
        "actors": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/actor_row"
          }
        }
      }
    },
    "controller_row": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "actor_path",
        "class_path",
        "pawn_path"
      ],
      "properties": {
        "actor_path": {
          "type": "string",
          "minLength": 1
        },
        "class_path": {
          "type": "string",
          "minLength": 1
        },
        "pawn_path": {
          "oneOf": [
            {
              "type": "null"
            },
            {
              "type": "string",
              "minLength": 1
            }
          ]
        }
      }
    },
    "startup": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "schema",
        "witness_id",
        "domain",
        "launch_id",
        "pid",
        "cwd_realpath",
        "worlds",
        "controllers",
        "loaded_images",
        "enabled_plugins",
        "config_files",
        "proof_module"
      ],
      "properties": {
        "schema": {
          "const": "city.live_evidence_startup.v1"
        },
        "witness_id": {
          "type": "string",
          "minLength": 1
        },
        "domain": {
          "enum": [
            "domain_A",
            "domain_B"
          ]
        },
        "launch_id": {
          "type": "string",
          "minLength": 1
        },
        "pid": {
          "type": "integer",
          "minimum": 0
        },
        "cwd_realpath": {
          "type": "string",
          "minLength": 1
        },
        "worlds": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/world_row"
          }
        },
        "controllers": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/controller_row"
          }
        },
        "loaded_images": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/image_identity"
          }
        },
        "enabled_plugins": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/file_identity"
          }
        },
        "config_files": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/file_identity"
          }
        },
        "proof_module": {
          "$ref": "#/$defs/image_identity"
        }
      }
    },
    "process_observation": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "pid",
        "ppid",
        "macos_birth_tuple",
        "cwd_realpath",
        "executable",
        "argv",
        "environment",
        "descriptors",
        "open_files",
        "loaded_images",
        "startup"
      ],
      "properties": {
        "pid": {
          "type": "integer",
          "minimum": 0
        },
        "ppid": {
          "type": "integer",
          "minimum": 0
        },
        "macos_birth_tuple": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "seconds",
            "microseconds"
          ],
          "properties": {
            "seconds": {
              "type": "integer",
              "minimum": 0
            },
            "microseconds": {
              "type": "integer",
              "minimum": 0,
              "maximum": 999999
            }
          }
        },
        "cwd_realpath": {
          "type": "string",
          "minLength": 1
        },
        "executable": {
          "$ref": "#/$defs/file_identity"
        },
        "argv": {
          "type": "array",
          "items": {
            "type": "string",
            "minLength": 1
          }
        },
        "environment": {
          "$ref": "#/$defs/environment"
        },
        "descriptors": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/descriptor"
          }
        },
        "open_files": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/file_identity"
          }
        },
        "loaded_images": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/image_identity"
          }
        },
        "startup": {
          "$ref": "#/$defs/startup"
        }
      }
    },
    "r1_receipt": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "schema",
        "witness_id",
        "domain",
        "launch_id",
        "operation_id",
        "binding_sha256",
        "record_raw_sha256",
        "record_canonical_hash",
        "generation",
        "allocation_owner",
        "anchor_actor_id",
        "resource_actor_id",
        "proposal_capability_enabled"
      ],
      "properties": {
        "schema": {
          "const": "city.live_evidence_representation_receipt.v1"
        },
        "witness_id": {
          "type": "string",
          "minLength": 1
        },
        "domain": {
          "enum": [
            "domain_A",
            "domain_B"
          ]
        },
        "launch_id": {
          "type": "string",
          "minLength": 1
        },
        "operation_id": {
          "type": "string",
          "minLength": 1
        },
        "binding_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "record_raw_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "record_canonical_hash": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "generation": {
          "const": 1
        },
        "allocation_owner": {
          "const": "domain_A"
        },
        "anchor_actor_id": {
          "type": "string",
          "minLength": 1
        },
        "resource_actor_id": {
          "type": "string",
          "minLength": 1
        },
        "proposal_capability_enabled": {
          "const": false
        }
      }
    },
    "materialization_result": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "r0_acceptance_raw_utf8",
        "r1_representation"
      ],
      "properties": {
        "r0_acceptance_raw_utf8": {
          "oneOf": [
            {
              "type": "null"
            },
            {
              "type": "string",
              "minLength": 1
            }
          ]
        },
        "r1_representation": {
          "oneOf": [
            {
              "type": "null"
            },
            {
              "$ref": "#/$defs/r1_receipt"
            }
          ]
        }
      }
    },
    "physical_event": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "schema",
        "witness_id",
        "domain",
        "launch_id",
        "operation_id",
        "binding_sha256",
        "actor_id",
        "physical_event_id",
        "interaction_counter",
        "accepted_record_raw_sha256",
        "q_raw_sha256",
        "q_canonical_hash"
      ],
      "properties": {
        "schema": {
          "const": "city.live_evidence_physical_event.v1"
        },
        "witness_id": {
          "type": "string",
          "minLength": 1
        },
        "domain": {
          "enum": [
            "domain_A",
            "domain_B"
          ]
        },
        "launch_id": {
          "type": "string",
          "minLength": 1
        },
        "operation_id": {
          "type": "string",
          "minLength": 1
        },
        "binding_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "actor_id": {
          "type": "string",
          "minLength": 1
        },
        "physical_event_id": {
          "type": "string",
          "minLength": 1
        },
        "interaction_counter": {
          "const": 1
        },
        "accepted_record_raw_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "q_raw_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "q_canonical_hash": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        }
      }
    },
    "emission_result": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "q_raw_utf8",
        "acceptance_receipt_raw_utf8",
        "emission_receipt_raw_utf8",
        "wrapper",
        "physical_event"
      ],
      "properties": {
        "q_raw_utf8": {
          "type": "string",
          "minLength": 1
        },
        "acceptance_receipt_raw_utf8": {
          "type": "string",
          "minLength": 1
        },
        "emission_receipt_raw_utf8": {
          "type": "string",
          "minLength": 1
        },
        "wrapper": {
          "$ref": "#/$defs/emission_wrapper"
        },
        "physical_event": {
          "$ref": "#/$defs/physical_event"
        }
      }
    },
    "fault_arm": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "failure_case",
        "stage",
        "operation_id"
      ],
      "properties": {
        "failure_case": {
          "enum": [
            "F13",
            "F14",
            "F15",
            "F16a",
            "F16b"
          ]
        },
        "stage": {
          "enum": [
            "after_resource_before_anchor",
            "after_receipt_before_observation"
          ]
        },
        "operation_id": {
          "const": "materialize_0002"
        }
      }
    },
    "fault_ack": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "schema",
        "witness_id",
        "domain",
        "launch_id",
        "operation_id",
        "binding_sha256",
        "failure_case",
        "stage",
        "armed_for"
      ],
      "properties": {
        "schema": {
          "const": "city.live_evidence_fault_ack.v1"
        },
        "witness_id": {
          "type": "string",
          "minLength": 1
        },
        "domain": {
          "enum": [
            "domain_A",
            "domain_B"
          ]
        },
        "launch_id": {
          "type": "string",
          "minLength": 1
        },
        "operation_id": {
          "type": "string",
          "minLength": 1
        },
        "binding_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "failure_case": {
          "type": "string",
          "minLength": 1
        },
        "stage": {
          "type": "string",
          "minLength": 1
        },
        "armed_for": {
          "const": "materialize_0002"
        }
      }
    },
    "bind_ack": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "schema",
        "witness_id",
        "domain",
        "launch_id",
        "operation_id",
        "binding_sha256",
        "startup_sha256"
      ],
      "properties": {
        "schema": {
          "const": "city.live_evidence_bind_ack.v1"
        },
        "witness_id": {
          "type": "string",
          "minLength": 1
        },
        "domain": {
          "enum": [
            "domain_A",
            "domain_B"
          ]
        },
        "launch_id": {
          "type": "string",
          "minLength": 1
        },
        "operation_id": {
          "type": "string",
          "minLength": 1
        },
        "binding_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "startup_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        }
      }
    },
    "shutdown_ack": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "schema",
        "witness_id",
        "domain",
        "launch_id",
        "operation_id",
        "binding_sha256",
        "accepted"
      ],
      "properties": {
        "schema": {
          "const": "city.live_evidence_shutdown_ack.v1"
        },
        "witness_id": {
          "type": "string",
          "minLength": 1
        },
        "domain": {
          "enum": [
            "domain_A",
            "domain_B"
          ]
        },
        "launch_id": {
          "type": "string",
          "minLength": 1
        },
        "operation_id": {
          "type": "string",
          "minLength": 1
        },
        "binding_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "accepted": {
          "const": true
        }
      }
    },
    "response": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "schema",
        "witness_id",
        "domain",
        "launch_id",
        "operation_id",
        "binding_sha256",
        "command",
        "status",
        "error",
        "payload"
      ],
      "properties": {
        "schema": {
          "const": "city.live_evidence_response.v1"
        },
        "witness_id": {
          "type": "string",
          "minLength": 1
        },
        "domain": {
          "enum": [
            "domain_A",
            "domain_B"
          ]
        },
        "launch_id": {
          "type": "string",
          "minLength": 1
        },
        "operation_id": {
          "type": "string",
          "minLength": 1
        },
        "binding_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "command": {
          "enum": [
            "bind",
            "materialize",
            "emit",
            "inspect",
            "arm_fault",
            "shutdown"
          ]
        },
        "status": {
          "enum": [
            "ok",
            "error"
          ]
        },
        "error": {
          "oneOf": [
            {
              "type": "null"
            },
            {
              "$ref": "#/$defs/error"
            }
          ]
        },
        "payload": {
          "oneOf": [
            {
              "type": "null"
            },
            {
              "$ref": "#/$defs/bind_ack"
            },
            {
              "$ref": "#/$defs/materialization_result"
            },
            {
              "$ref": "#/$defs/emission_result"
            },
            {
              "$ref": "#/$defs/live_observation"
            },
            {
              "$ref": "#/$defs/fault_ack"
            },
            {
              "$ref": "#/$defs/shutdown_ack"
            }
          ]
        }
      }
    },
    "liveness": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "checkpoint",
        "domain",
        "launch_id",
        "poll_returncode",
        "observed_process",
        "pipe_endpoints",
        "pipe_holders"
      ],
      "properties": {
        "checkpoint": {
          "enum": [
            "startup",
            "L0",
            "L1",
            "L2",
            "before_resolve",
            "after_resolve",
            "L3",
            "L4",
            "L5",
            "terminal",
            "cleanup"
          ]
        },
        "domain": {
          "enum": [
            "domain_A",
            "domain_B"
          ]
        },
        "launch_id": {
          "type": "string",
          "minLength": 1
        },
        "poll_returncode": {
          "oneOf": [
            {
              "type": "null"
            },
            {
              "type": "integer"
            }
          ]
        },
        "observed_process": {
          "oneOf": [
            {
              "type": "null"
            },
            {
              "$ref": "#/$defs/process_observation"
            }
          ]
        },
        "pipe_endpoints": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/descriptor"
          }
        },
        "pipe_holders": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/descriptor"
          }
        }
      }
    },
    "head_event": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "edge",
        "canonical_role",
        "canonical_raw_utf8",
        "domain",
        "disposition",
        "observation_sha256"
      ],
      "properties": {
        "edge": {
          "enum": [
            "initialize",
            "invalidate_claims",
            "publish",
            "classify",
            "terminal"
          ]
        },
        "canonical_role": {
          "enum": [
            "R0",
            "R1"
          ]
        },
        "canonical_raw_utf8": {
          "type": "string",
          "minLength": 1
        },
        "domain": {
          "oneOf": [
            {
              "type": "null"
            },
            {
              "enum": [
                "domain_A",
                "domain_B"
              ]
            }
          ]
        },
        "disposition": {
          "enum": [
            "current",
            "stale",
            "unavailable",
            "unclaimed"
          ]
        },
        "observation_sha256": {
          "oneOf": [
            {
              "type": "null"
            },
            {
              "type": "string",
              "pattern": "^[0-9a-f]{64}$"
            }
          ]
        }
      }
    },
    "canonical_call": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "function",
        "record_before_raw_utf8",
        "return_raw_utf8",
        "exception_code",
        "record_after_raw_utf8",
        "published_record_raw_utf8",
        "fault_point",
        "arguments"
      ],
      "properties": {
        "function": {
          "enum": [
            "admit_external_input_candidate",
            "construct_bext_from_sealed_fixture_set",
            "resolve_external_batch"
          ]
        },
        "record_before_raw_utf8": {
          "type": "string",
          "minLength": 1
        },
        "return_raw_utf8": {
          "oneOf": [
            {
              "type": "null"
            },
            {
              "type": "string",
              "minLength": 1
            }
          ]
        },
        "exception_code": {
          "oneOf": [
            {
              "type": "null"
            },
            {
              "type": "string",
              "minLength": 1
            }
          ]
        },
        "record_after_raw_utf8": {
          "type": "string",
          "minLength": 1
        },
        "published_record_raw_utf8": {
          "oneOf": [
            {
              "type": "null"
            },
            {
              "type": "string",
              "minLength": 1
            }
          ]
        },
        "fault_point": {
          "oneOf": [
            {
              "type": "null"
            },
            {
              "type": "string",
              "minLength": 1
            }
          ]
        },
        "arguments": {
          "oneOf": [
            {
              "$ref": "#/$defs/admission_arguments"
            },
            {
              "$ref": "#/$defs/construction_arguments"
            },
            {
              "$ref": "#/$defs/resolution_arguments"
            }
          ]
        }
      }
    },
    "fault_event": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "failure_case",
        "executor",
        "stage",
        "action",
        "consumed",
        "underlying_code",
        "before",
        "after"
      ],
      "properties": {
        "failure_case": {
          "type": "string",
          "minLength": 1
        },
        "executor": {
          "enum": [
            "harness",
            "unreal"
          ]
        },
        "stage": {
          "type": "string",
          "minLength": 1
        },
        "action": {
          "type": "string",
          "minLength": 1
        },
        "consumed": {
          "type": "boolean"
        },
        "underlying_code": {
          "oneOf": [
            {
              "type": "null"
            },
            {
              "type": "string",
              "minLength": 1
            }
          ]
        },
        "before": {
          "oneOf": [
            {
              "$ref": "#/$defs/fault_bytes_state"
            },
            {
              "$ref": "#/$defs/fault_world_state"
            },
            {
              "$ref": "#/$defs/fault_process_state"
            }
          ]
        },
        "after": {
          "oneOf": [
            {
              "$ref": "#/$defs/fault_bytes_state"
            },
            {
              "$ref": "#/$defs/fault_world_state"
            },
            {
              "$ref": "#/$defs/fault_process_state"
            }
          ]
        }
      }
    },
    "wire_event": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "direction",
        "raw_line_utf8",
        "stream_byte_offset",
        "parsed_schema"
      ],
      "properties": {
        "direction": {
          "enum": [
            "stdin",
            "stdout"
          ]
        },
        "raw_line_utf8": {
          "type": "string",
          "minLength": 1
        },
        "stream_byte_offset": {
          "type": "integer",
          "minimum": 0
        },
        "parsed_schema": {
          "enum": [
            "command",
            "response",
            "startup",
            "physical_event",
            "fault_event"
          ]
        }
      }
    },
    "trace_event": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "sequence",
        "event_id",
        "operation_id",
        "domain",
        "monotonic_ns",
        "payload",
        "previous_event_sha256"
      ],
      "properties": {
        "sequence": {
          "type": "integer",
          "minimum": 0
        },
        "event_id": {
          "enum": [
            "process_observation",
            "wire_event",
            "liveness",
            "head_event",
            "canonical_call",
            "fault_event"
          ]
        },
        "operation_id": {
          "oneOf": [
            {
              "type": "null"
            },
            {
              "type": "string",
              "minLength": 1
            }
          ]
        },
        "domain": {
          "oneOf": [
            {
              "type": "null"
            },
            {
              "enum": [
                "domain_A",
                "domain_B"
              ]
            }
          ]
        },
        "monotonic_ns": {
          "type": "integer",
          "minimum": 0
        },
        "payload": {
          "oneOf": [
            {
              "$ref": "#/$defs/process_observation"
            },
            {
              "$ref": "#/$defs/wire_event"
            },
            {
              "$ref": "#/$defs/liveness"
            },
            {
              "$ref": "#/$defs/head_event"
            },
            {
              "$ref": "#/$defs/canonical_call"
            },
            {
              "$ref": "#/$defs/fault_event"
            }
          ]
        },
        "previous_event_sha256": {
          "oneOf": [
            {
              "type": "null"
            },
            {
              "type": "string",
              "pattern": "^[0-9a-f]{64}$"
            }
          ]
        }
      }
    },
    "capture_slot": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "domain",
        "emission"
      ],
      "properties": {
        "domain": {
          "enum": [
            "domain_A",
            "domain_B"
          ]
        },
        "emission": {
          "oneOf": [
            {
              "type": "null"
            },
            {
              "$ref": "#/$defs/emission_result"
            }
          ]
        }
      }
    },
    "claims": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "synchronized_representation",
        "canonical_commit",
        "production_ready",
        "trusted_ci",
        "game_sealed"
      ],
      "properties": {
        "synchronized_representation": {
          "type": "boolean"
        },
        "canonical_commit": {
          "type": "boolean"
        },
        "production_ready": {
          "const": false
        },
        "trusted_ci": {
          "const": false
        },
        "game_sealed": {
          "const": false
        }
      }
    },
    "case_record": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "schema",
        "proof",
        "version",
        "witness_id",
        "status",
        "failure_codes",
        "process_bindings",
        "liveness_checkpoints",
        "canonical_artifacts",
        "captured_evidence",
        "materialization_receipts",
        "live_observations",
        "head_dispositions",
        "command_trace",
        "artifact_sha256",
        "claims"
      ],
      "properties": {
        "schema": {
          "const": "city.live_evidence_case.v1"
        },
        "proof": {
          "const": "Live Cross-Domain Evidence Round-Trip Proof"
        },
        "version": {
          "const": "0.1.0"
        },
        "witness_id": {
          "type": "string",
          "minLength": 1
        },
        "status": {
          "enum": [
            "accepted",
            "expected_failure",
            "acquisition_failure"
          ]
        },
        "failure_codes": {
          "type": "array",
          "items": {
            "type": "string",
            "minLength": 1
          }
        },
        "process_bindings": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/process_binding"
          }
        },
        "liveness_checkpoints": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/liveness"
          }
        },
        "canonical_artifacts": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "initial_raw_utf8",
            "published_raw_utf8",
            "terminal_raw_utf8"
          ],
          "properties": {
            "initial_raw_utf8": {
              "type": "string",
              "minLength": 1
            },
            "published_raw_utf8": {
              "oneOf": [
                {
                  "type": "null"
                },
                {
                  "type": "string",
                  "minLength": 1
                }
              ]
            },
            "terminal_raw_utf8": {
              "type": "string",
              "minLength": 1
            }
          }
        },
        "captured_evidence": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/capture_slot"
          }
        },
        "materialization_receipts": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/materialization_result"
          }
        },
        "live_observations": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/live_observation"
          }
        },
        "head_dispositions": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/head_event"
          }
        },
        "command_trace": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/trace_event"
          }
        },
        "artifact_sha256": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/artifact_hash"
          }
        },
        "claims": {
          "$ref": "#/$defs/claims"
        }
      }
    },
    "source_edge": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "path",
        "function",
        "input",
        "callee",
        "consequence"
      ],
      "properties": {
        "path": {
          "type": "string",
          "minLength": 1
        },
        "function": {
          "type": "string",
          "minLength": 1
        },
        "input": {
          "enum": [
            "canonical",
            "binding",
            "command",
            "world",
            "platform"
          ]
        },
        "callee": {
          "type": "string",
          "minLength": 1
        },
        "consequence": {
          "enum": [
            "canonical",
            "representation",
            "observation",
            "provenance",
            "fault"
          ]
        }
      }
    },
    "source_audit": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "files",
        "edges",
        "rejected_mutations",
        "argv",
        "returncode"
      ],
      "properties": {
        "files": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/artifact_hash"
          }
        },
        "edges": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/source_edge"
          }
        },
        "rejected_mutations": {
          "type": "array",
          "items": {
            "type": "string",
            "minLength": 1
          }
        },
        "argv": {
          "type": "array",
          "items": {
            "type": "string",
            "minLength": 1
          }
        },
        "returncode": {
          "type": "integer"
        }
      }
    },
    "external_inputs": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "engine_root",
        "engine_build_version",
        "compiler",
        "sdk",
        "python",
        "build_inputs",
        "engine_configs",
        "engine_plugins",
        "loaded_images",
        "dyld_cache"
      ],
      "properties": {
        "engine_root": {
          "type": "string",
          "minLength": 1
        },
        "engine_build_version": {
          "$ref": "#/$defs/file_identity"
        },
        "compiler": {
          "$ref": "#/$defs/file_identity"
        },
        "sdk": {
          "$ref": "#/$defs/file_identity"
        },
        "python": {
          "$ref": "#/$defs/file_identity"
        },
        "build_inputs": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/file_identity"
          }
        },
        "engine_configs": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/file_identity"
          }
        },
        "engine_plugins": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/file_identity"
          }
        },
        "loaded_images": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/image_identity"
          }
        },
        "dyld_cache": {
          "$ref": "#/$defs/file_identity"
        }
      }
    },
    "build_record": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "schema",
        "argv",
        "cwd",
        "source_commit",
        "source_tree",
        "returncode",
        "started_at",
        "finished_at",
        "log",
        "editor",
        "project",
        "modules",
        "external_inputs",
        "source_audit"
      ],
      "properties": {
        "schema": {
          "const": "city.live_evidence_build.v1"
        },
        "argv": {
          "type": "array",
          "items": {
            "type": "string",
            "minLength": 1
          }
        },
        "cwd": {
          "type": "string",
          "minLength": 1
        },
        "source_commit": {
          "type": "string",
          "minLength": 1
        },
        "source_tree": {
          "type": "string",
          "minLength": 1
        },
        "returncode": {
          "type": "integer"
        },
        "started_at": {
          "type": "string",
          "minLength": 1
        },
        "finished_at": {
          "type": "string",
          "minLength": 1
        },
        "log": {
          "$ref": "#/$defs/artifact_hash"
        },
        "editor": {
          "$ref": "#/$defs/file_identity"
        },
        "project": {
          "$ref": "#/$defs/file_identity"
        },
        "modules": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/image_identity"
          }
        },
        "external_inputs": {
          "$ref": "#/$defs/external_inputs"
        },
        "source_audit": {
          "$ref": "#/$defs/source_audit"
        }
      }
    },
    "case_index": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "witness_id",
        "record_path",
        "record_sha256"
      ],
      "properties": {
        "witness_id": {
          "type": "string",
          "minLength": 1
        },
        "record_path": {
          "type": "string",
          "minLength": 1
        },
        "record_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        }
      }
    },
    "acquisition_record": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "schema",
        "source_commit",
        "source_tree",
        "build_sha256",
        "cases",
        "artifact_members",
        "artifact_hashes",
        "status",
        "claims"
      ],
      "properties": {
        "schema": {
          "const": "city.live_evidence_acquisition.v1"
        },
        "source_commit": {
          "type": "string",
          "minLength": 1
        },
        "source_tree": {
          "type": "string",
          "minLength": 1
        },
        "build_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "cases": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/case_index"
          }
        },
        "artifact_members": {
          "type": "array",
          "items": {
            "type": "string",
            "minLength": 1
          }
        },
        "artifact_hashes": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/artifact_hash"
          }
        },
        "status": {
          "enum": [
            "complete",
            "failed"
          ]
        },
        "claims": {
          "$ref": "#/$defs/claims"
        }
      }
    },
    "admission_arguments": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "schema",
        "record_raw_utf8",
        "q_object_raw_utf8",
        "q_raw_base64",
        "materialization_receipt_raw_utf8",
        "emission_receipt_raw_utf8"
      ],
      "properties": {
        "schema": {
          "const": "city.live_evidence_admission_arguments.v1"
        },
        "record_raw_utf8": {
          "type": "string",
          "minLength": 1
        },
        "q_object_raw_utf8": {
          "type": "string",
          "minLength": 1
        },
        "q_raw_base64": {
          "type": "string"
        },
        "materialization_receipt_raw_utf8": {
          "type": "string",
          "minLength": 1
        },
        "emission_receipt_raw_utf8": {
          "type": "string",
          "minLength": 1
        }
      }
    },
    "construction_arguments": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "schema",
        "record_raw_utf8",
        "fixture_raw_utf8",
        "presentation_members_raw_utf8"
      ],
      "properties": {
        "schema": {
          "const": "city.live_evidence_construction_arguments.v1"
        },
        "record_raw_utf8": {
          "type": "string",
          "minLength": 1
        },
        "fixture_raw_utf8": {
          "type": "string",
          "minLength": 1
        },
        "presentation_members_raw_utf8": {
          "type": "array",
          "items": {
            "type": "string",
            "minLength": 1
          }
        }
      }
    },
    "member_entry": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "input_id",
        "member_raw_utf8"
      ],
      "properties": {
        "input_id": {
          "type": "string",
          "minLength": 1
        },
        "member_raw_utf8": {
          "type": "string",
          "minLength": 1
        }
      }
    },
    "resolution_arguments": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "schema",
        "record_raw_utf8",
        "bext_raw_utf8",
        "admitted_members",
        "fault_point"
      ],
      "properties": {
        "schema": {
          "const": "city.live_evidence_resolution_arguments.v1"
        },
        "record_raw_utf8": {
          "type": "string",
          "minLength": 1
        },
        "bext_raw_utf8": {
          "type": "string",
          "minLength": 1
        },
        "admitted_members": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/member_entry"
          }
        },
        "fault_point": {
          "oneOf": [
            {
              "type": "null"
            },
            {
              "enum": [
                "after_qa_provisional_mutation",
                "after_qb_ordinary_gate_evaluation",
                "during_replay_barrier_construction",
                "during_batch_ledger_construction",
                "after_complete_r1_before_validation",
                "after_complete_r1_validation_before_publication"
              ]
            }
          ]
        }
      }
    },
    "construction_return": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "bext_raw_utf8",
        "admitted_members"
      ],
      "properties": {
        "bext_raw_utf8": {
          "type": "string",
          "minLength": 1
        },
        "admitted_members": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/member_entry"
          }
        }
      }
    },
    "fault_bytes_state": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "kind",
        "semantic_type",
        "raw_base64"
      ],
      "properties": {
        "kind": {
          "const": "bytes"
        },
        "semantic_type": {
          "enum": [
            "q_raw",
            "admission_arguments",
            "construction_arguments",
            "materialize_command"
          ]
        },
        "raw_base64": {
          "type": "string"
        }
      }
    },
    "fault_world_state": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "kind",
        "observation"
      ],
      "properties": {
        "kind": {
          "const": "world"
        },
        "observation": {
          "$ref": "#/$defs/live_observation"
        }
      }
    },
    "fault_process_state": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "kind",
        "sample"
      ],
      "properties": {
        "kind": {
          "const": "process"
        },
        "sample": {
          "$ref": "#/$defs/liveness"
        }
      }
    }
  },
  "command_contract": {
    "bind": "first command only; binding payload; verifies exact parent-observed identity",
    "materialize": "materialize_input, with exact raw-R0 authentication or distinct committed-R1 validation in record_delivery",
    "emit": "null payload; exactly once at accepted R0; actual Actor interaction",
    "inspect": "null payload; independent world enumeration",
    "arm_fault": "Only F13,F14,F15,F16a,F16b, with exact stage/operation; one successful arm and one consumed event; harness-owned cases never arm a child",
    "shutdown": "null payload; terminal; no restart",
    "unknown_or_duplicate": "reject before side effects",
    "operation_ids": "bind_0001,materialize_0001,emit_0001,inspect_L0,inspect_L1,inspect_L2,inspect_L3,materialize_0002,inspect_L4,inspect_L5,inspect_terminal,arm_fault_0001,shutdown_0001; each once per domain. Terminal census is evidence capture only; no retry/repair."
  },
  "launch_argv": [
    "{engine}",
    "{absolute_city_project}",
    "/Engine/Maps/Entry?game=/Script/CityLiveEvidenceProof.CityLiveEvidenceGameMode",
    "-game",
    "-unattended",
    "-nosplash",
    "-NoSound",
    "-log",
    "-LCERDomain={domain}",
    "-LCERWitness={witness_id}",
    "-LCERLaunch={launch_id}",
    "-LCERRoot={absolute_domain_root}",
    "-UserDir={absolute_domain_root}/user"
  ],
  "launch_environment": {
    "HOME": "{absolute_domain_root}/home",
    "TMPDIR": "{absolute_domain_root}/tmp",
    "USER": "{observed_operator_user}",
    "LOGNAME": "{observed_operator_user}",
    "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
    "LANG": "C",
    "LC_ALL": "C"
  },
  "descriptor_contract": {
    "stdin": 0,
    "stdout": 1,
    "stderr": 2,
    "inherited_proof_descriptors": [
      0,
      1,
      2
    ],
    "transport": "canonical JSON lines on stdin/stdout; UE log lines on stdout retained and parsed separately; stderr captured verbatim",
    "extra_descriptor_rule": "close all nonstandard inherited descriptors; audit before acceptance; refuse child helpers retaining proof pipes"
  },
  "build_argv": [
    "/Users/Shared/Epic Games/UE_5.8/Engine/Build/BatchFiles/Mac/Build.sh",
    "CityMaterializationProofEditor",
    "Mac",
    "Development",
    "-Project={absolute_city_project}",
    "-DisableUnity",
    "-WaitMutex"
  ],
  "plugin_contract": {
    "name": "CityLiveEvidenceProof",
    "module_type": "Runtime",
    "loading_phase": "Default",
    "enabled_by_default": true,
    "can_contain_content": false,
    "game_mode_selection": "explicit launch map URL only",
    "existing_source_edits": false,
    "extra_plugins": "only observed engine defaults and this declared plugin; record full loaded module identity; no undeclared proof-semantic input"
  },
  "artifact_relative_paths": [
    "acquisition.json",
    "build.json",
    "build.log",
    "canonical/R0.json",
    "canonical/R1.json",
    "canonical/QA.json",
    "canonical/QB.json",
    "W1/record.json",
    "W1/harness.jsonl",
    "W1/domain_A.stdout.log",
    "W1/domain_A.stderr.log",
    "W1/domain_B.stdout.log",
    "W1/domain_B.stderr.log",
    "W2/record.json",
    "W2/harness.jsonl",
    "W2/domain_A.stdout.log",
    "W2/domain_A.stderr.log",
    "W2/domain_B.stdout.log",
    "W2/domain_B.stderr.log",
    "W3/record.json",
    "W3/harness.jsonl",
    "W3/domain_A.stdout.log",
    "W3/domain_A.stderr.log",
    "W3/domain_B.stdout.log",
    "W3/domain_B.stderr.log",
    "W4/record.json",
    "W4/harness.jsonl",
    "W4/domain_A.stdout.log",
    "W4/domain_A.stderr.log",
    "W4/domain_B.stdout.log",
    "W4/domain_B.stderr.log",
    "W5/record.json",
    "W5/harness.jsonl",
    "W5/domain_A.stdout.log",
    "W5/domain_A.stderr.log",
    "W5/domain_B.stdout.log",
    "W5/domain_B.stderr.log",
    "W6/record.json",
    "W6/harness.jsonl",
    "W6/domain_A.stdout.log",
    "W6/domain_A.stderr.log",
    "W6/domain_B.stdout.log",
    "W6/domain_B.stderr.log",
    "W7/record.json",
    "W7/harness.jsonl",
    "W7/domain_A.stdout.log",
    "W7/domain_A.stderr.log",
    "W7/domain_B.stdout.log",
    "W7/domain_B.stderr.log",
    "W8/record.json",
    "W8/harness.jsonl",
    "W8/domain_A.stdout.log",
    "W8/domain_A.stderr.log",
    "W8/domain_B.stdout.log",
    "W8/domain_B.stderr.log",
    "F01/record.json",
    "F01/harness.jsonl",
    "F01/domain_A.stdout.log",
    "F01/domain_A.stderr.log",
    "F01/domain_B.stdout.log",
    "F01/domain_B.stderr.log",
    "F02/record.json",
    "F02/harness.jsonl",
    "F02/domain_A.stdout.log",
    "F02/domain_A.stderr.log",
    "F02/domain_B.stdout.log",
    "F02/domain_B.stderr.log",
    "F03/record.json",
    "F03/harness.jsonl",
    "F03/domain_A.stdout.log",
    "F03/domain_A.stderr.log",
    "F03/domain_B.stdout.log",
    "F03/domain_B.stderr.log",
    "F04a/record.json",
    "F04a/harness.jsonl",
    "F04a/domain_A.stdout.log",
    "F04a/domain_A.stderr.log",
    "F04a/domain_B.stdout.log",
    "F04a/domain_B.stderr.log",
    "F04b/record.json",
    "F04b/harness.jsonl",
    "F04b/domain_A.stdout.log",
    "F04b/domain_A.stderr.log",
    "F04b/domain_B.stdout.log",
    "F04b/domain_B.stderr.log",
    "F05/record.json",
    "F05/harness.jsonl",
    "F05/domain_A.stdout.log",
    "F05/domain_A.stderr.log",
    "F05/domain_B.stdout.log",
    "F05/domain_B.stderr.log",
    "F06/record.json",
    "F06/harness.jsonl",
    "F06/domain_A.stdout.log",
    "F06/domain_A.stderr.log",
    "F06/domain_B.stdout.log",
    "F06/domain_B.stderr.log",
    "F07/record.json",
    "F07/harness.jsonl",
    "F07/domain_A.stdout.log",
    "F07/domain_A.stderr.log",
    "F07/domain_B.stdout.log",
    "F07/domain_B.stderr.log",
    "F08/record.json",
    "F08/harness.jsonl",
    "F08/domain_A.stdout.log",
    "F08/domain_A.stderr.log",
    "F08/domain_B.stdout.log",
    "F08/domain_B.stderr.log",
    "F09/record.json",
    "F09/harness.jsonl",
    "F09/domain_A.stdout.log",
    "F09/domain_A.stderr.log",
    "F09/domain_B.stdout.log",
    "F09/domain_B.stderr.log",
    "F10a/record.json",
    "F10a/harness.jsonl",
    "F10a/domain_A.stdout.log",
    "F10a/domain_A.stderr.log",
    "F10a/domain_B.stdout.log",
    "F10a/domain_B.stderr.log",
    "F10b/record.json",
    "F10b/harness.jsonl",
    "F10b/domain_A.stdout.log",
    "F10b/domain_A.stderr.log",
    "F10b/domain_B.stdout.log",
    "F10b/domain_B.stderr.log",
    "F11/record.json",
    "F11/harness.jsonl",
    "F11/domain_A.stdout.log",
    "F11/domain_A.stderr.log",
    "F11/domain_B.stdout.log",
    "F11/domain_B.stderr.log",
    "F12/record.json",
    "F12/harness.jsonl",
    "F12/domain_A.stdout.log",
    "F12/domain_A.stderr.log",
    "F12/domain_B.stdout.log",
    "F12/domain_B.stderr.log",
    "F13/record.json",
    "F13/harness.jsonl",
    "F13/domain_A.stdout.log",
    "F13/domain_A.stderr.log",
    "F13/domain_B.stdout.log",
    "F13/domain_B.stderr.log",
    "F14/record.json",
    "F14/harness.jsonl",
    "F14/domain_A.stdout.log",
    "F14/domain_A.stderr.log",
    "F14/domain_B.stdout.log",
    "F14/domain_B.stderr.log",
    "F15/record.json",
    "F15/harness.jsonl",
    "F15/domain_A.stdout.log",
    "F15/domain_A.stderr.log",
    "F15/domain_B.stdout.log",
    "F15/domain_B.stderr.log",
    "F16a/record.json",
    "F16a/harness.jsonl",
    "F16a/domain_A.stdout.log",
    "F16a/domain_A.stderr.log",
    "F16a/domain_B.stdout.log",
    "F16a/domain_B.stderr.log",
    "F16b/record.json",
    "F16b/harness.jsonl",
    "F16b/domain_A.stdout.log",
    "F16b/domain_A.stderr.log",
    "F16b/domain_B.stdout.log",
    "F16b/domain_B.stderr.log",
    "F17/record.json",
    "F17/harness.jsonl",
    "F17/domain_A.stdout.log",
    "F17/domain_A.stderr.log",
    "F17/domain_B.stdout.log",
    "F17/domain_B.stderr.log",
    "F18/record.json",
    "F18/harness.jsonl",
    "F18/domain_A.stdout.log",
    "F18/domain_A.stderr.log",
    "F18/domain_B.stdout.log",
    "F18/domain_B.stderr.log",
    "C01/record.json",
    "C01/harness.jsonl",
    "C01/domain_A.stdout.log",
    "C01/domain_A.stderr.log",
    "C01/domain_B.stdout.log",
    "C01/domain_B.stderr.log",
    "C02/record.json",
    "C02/harness.jsonl",
    "C02/domain_A.stdout.log",
    "C02/domain_A.stderr.log",
    "C02/domain_B.stdout.log",
    "C02/domain_B.stderr.log",
    "C03/record.json",
    "C03/harness.jsonl",
    "C03/domain_A.stdout.log",
    "C03/domain_A.stderr.log",
    "C03/domain_B.stdout.log",
    "C03/domain_B.stderr.log",
    "C04/record.json",
    "C04/harness.jsonl",
    "C04/domain_A.stdout.log",
    "C04/domain_A.stderr.log",
    "C04/domain_B.stdout.log",
    "C04/domain_B.stderr.log",
    "C05/record.json",
    "C05/harness.jsonl",
    "C05/domain_A.stdout.log",
    "C05/domain_A.stderr.log",
    "C05/domain_B.stdout.log",
    "C05/domain_B.stderr.log",
    "C06/record.json",
    "C06/harness.jsonl",
    "C06/domain_A.stdout.log",
    "C06/domain_A.stderr.log",
    "C06/domain_B.stdout.log",
    "C06/domain_B.stderr.log",
    "F07/replacement.stdout.log",
    "F07/replacement.stderr.log"
  ],
  "artifact_record_contract": {
    "record.json": "case_record schema; hash exactly this case harness.jsonl and original four streams, plus replacement streams only for F07. Repeated parsed records must match raw trace/stream bytes.",
    "harness.jsonl": "trace_event schema for every line; original raw wire bytes retained as wire_event; command trace in record is byte-equivalent parsed ordered trace.",
    "stdout_stderr": "verbatim named process bytes; protocol lines must validate and reconcile with trace. Replacement streams never stand in for original A.",
    "acquisition.json": "acquisition_record schema; artifact_members is full exact path list. artifact_hashes covers every artifact except acquisition.json itself. cases has exactly the enumerated IDs and corresponding record path/hash.",
    "build.json": "build_record schema; hashes only build.log and source/external input bytes, never acquisition or case records. Compile success does not imply runtime.",
    "canonical_files": "exact four pinned stored predecessor bytes; presence of canonical/R1.json is an expected reference, NOT publication evidence; actual publication is recorded in case/trace."
  },
  "release_members": [
    "CityMaterializationProof/CityMaterializationProof.uproject",
    "CityMaterializationProof/Config/DefaultEngine.ini",
    "CityMaterializationProof/Config/DefaultGame.ini",
    "CityMaterializationProof/Config/DefaultInput.ini",
    "CityMaterializationProof/Plugins/CityLiveEvidenceProof/CityLiveEvidenceProof.uplugin",
    "CityMaterializationProof/Plugins/CityLiveEvidenceProof/Source/CityLiveEvidenceProof/CityLiveEvidenceProof.Build.cs",
    "CityMaterializationProof/Plugins/CityLiveEvidenceProof/Source/CityLiveEvidenceProof/Private/CityLiveEvidenceActors.cpp",
    "CityMaterializationProof/Plugins/CityLiveEvidenceProof/Source/CityLiveEvidenceProof/Private/CityLiveEvidenceGameMode.cpp",
    "CityMaterializationProof/Plugins/CityLiveEvidenceProof/Source/CityLiveEvidenceProof/Private/CityLiveEvidenceProofModule.cpp",
    "CityMaterializationProof/Plugins/CityLiveEvidenceProof/Source/CityLiveEvidenceProof/Public/CityLiveEvidenceActors.h",
    "CityMaterializationProof/Plugins/CityLiveEvidenceProof/Source/CityLiveEvidenceProof/Public/CityLiveEvidenceGameMode.h",
    "CityMaterializationProof/Source/CityMaterializationProof.Target.cs",
    "CityMaterializationProof/Source/CityMaterializationProof/BridgeAccessPoint.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/BridgeAccessPoint.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CanonicalSpatialTopologyProofAdapter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CanonicalSpatialTopologyProofAdapter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CanonicalTopologyRepresentationActor.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CanonicalTopologyRepresentationActor.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationActor.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationActor.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationProof.Build.cs",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationProof.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationProof.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofCharacter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofCharacter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofGameMode.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofGameMode.h",
    "CityMaterializationProof/Source/CityMaterializationProof/ConcurrentEvidenceSurface.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/ConcurrentEvidenceSurface.h",
    "CityMaterializationProof/Source/CityMaterializationProof/ConcurrentExternalEvidenceProofAdapter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/ConcurrentExternalEvidenceProofAdapter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CrewOperationPoint.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CrewOperationPoint.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyCommandRouter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyCommandRouter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyHeadAnchorActor.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyHeadAnchorActor.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyLiveWorldProbe.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyLiveWorldProbe.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyProofAdapter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyProofAdapter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancySubjectActor.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancySubjectActor.h",
    "CityMaterializationProof/Source/CityMaterializationProof/IntegratedGateTokenPoint.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/IntegratedGateTokenPoint.h",
    "CityMaterializationProof/Source/CityMaterializationProof/IntegratedUnrealProofAdapter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/IntegratedUnrealProofAdapter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/LiveCommitmentRelayPoint.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/LiveCommitmentRelayPoint.h",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainCommandRouter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainCommandRouter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainProofAdapter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainProofAdapter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainRepresentationActor.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainRepresentationActor.h",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalRebindProbe.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalRebindProbe.h",
    "CityMaterializationProof/Source/CityMaterializationProofEditor.Target.cs",
    "Concurrent External Evidence Arbitration Proof - Draft.md",
    "Concurrent External Evidence Arbitration Proof Evidence - v0.1.0.md",
    "Cross-Domain Canonical Occupancy Materialization Proof - Draft.md",
    "Cross-Domain Canonical Occupancy Materialization Proof Evidence - v0.1.0.md",
    "Live Cross-Domain Evidence Round-Trip Proof - Draft.md",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C01/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C01/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C01/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C01/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C01/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C01/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C02/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C02/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C02/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C02/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C02/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C02/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C03/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C03/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C03/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C03/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C03/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C03/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C04/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C04/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C04/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C04/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C04/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C04/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C05/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C05/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C05/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C05/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C05/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C05/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C06/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C06/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C06/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C06/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C06/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/C06/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F01/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F01/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F01/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F01/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F01/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F01/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F02/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F02/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F02/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F02/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F02/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F02/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F03/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F03/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F03/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F03/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F03/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F03/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F04a/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F04a/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F04a/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F04a/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F04a/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F04a/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F04b/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F04b/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F04b/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F04b/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F04b/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F04b/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F05/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F05/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F05/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F05/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F05/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F05/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F06/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F06/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F06/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F06/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F06/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F06/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F07/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F07/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F07/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F07/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F07/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F07/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F07/replacement.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F07/replacement.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F08/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F08/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F08/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F08/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F08/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F08/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F09/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F09/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F09/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F09/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F09/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F09/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F10a/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F10a/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F10a/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F10a/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F10a/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F10a/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F10b/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F10b/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F10b/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F10b/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F10b/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F10b/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F11/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F11/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F11/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F11/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F11/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F11/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F12/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F12/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F12/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F12/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F12/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F12/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F13/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F13/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F13/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F13/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F13/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F13/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F14/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F14/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F14/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F14/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F14/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F14/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F15/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F15/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F15/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F15/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F15/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F15/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F16a/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F16a/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F16a/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F16a/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F16a/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F16a/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F16b/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F16b/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F16b/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F16b/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F16b/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F16b/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F17/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F17/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F17/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F17/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F17/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F17/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F18/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F18/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F18/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F18/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F18/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/F18/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W1/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W1/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W1/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W1/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W1/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W1/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W2/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W2/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W2/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W2/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W2/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W2/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W3/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W3/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W3/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W3/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W3/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W3/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W4/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W4/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W4/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W4/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W4/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W4/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W5/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W5/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W5/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W5/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W5/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W5/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W6/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W6/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W6/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W6/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W6/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W6/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W7/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W7/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W7/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W7/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W7/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W7/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W8/domain_A.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W8/domain_A.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W8/domain_B.stderr.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W8/domain_B.stdout.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W8/harness.jsonl",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/W8/record.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/acquisition.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/build.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/build.log",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/canonical/QA.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/canonical/QB.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/canonical/R0.json",
    "proof_kernel/LiveCrossDomainEvidenceRoundTripProofRecords/canonical/R1.json",
    "proof_kernel/concurrent_external_evidence_arbitration.py",
    "proof_kernel/kernel.py",
    "proof_kernel/live_cross_domain_evidence_round_trip.py",
    "proof_kernel/live_cross_domain_evidence_round_trip_contract.json",
    "proof_kernel/live_cross_domain_evidence_round_trip_harness.py",
    "proof_kernel/test_live_cross_domain_evidence_round_trip.py",
    "proof_kernel/verify_live_cross_domain_evidence_round_trip_release.py"
  ],
  "release_manifest": "Live Cross-Domain Evidence Round-Trip Proof - v0.1.0 SHA256SUMS.txt",
  "schema_contract": {
    "dialect": "https://json-schema.org/draft/2020-12/schema",
    "bundle": "Place wire_schemas at $defs. Resolve only local #/$defs/name references. No external schema resolution.",
    "lexical": "Reject duplicate keys recursively, nonfinite numbers, invalid UTF-8, trailing data, unknown/missing fields. New stored JSON and each JSONL line use sorted ASCII compact JSON plus exactly one LF. No alternative whitespace. Raw embedded strings preserve the embedded trailing LF.",
    "legacy_raw": "R0/R1/Q/launch and acceptance/emission raw strings are parsed strictly, reserialized with the unchanged predecessor serializer, and compared with pinned canonical data and unchanged predecessor receipt constructors. process_instance_id is exactly launch_id. These strings cannot contain unconstrained JSON.",
    "response_match": {
      "bind": "bind_ack",
      "materialize": "materialization_result",
      "emit": "emission_result",
      "inspect": "live_observation",
      "arm_fault": "fault_ack",
      "shutdown": "shutdown_ack"
    },
    "relations": [
      "Exactly one response for each dispatched command, with byte-equal witness/domain/launch/operation/binding fields and command name. Error status requires error object and null payload; ok requires null error and exactly the mapped payload schema. No success plus error form.",
      "bind command payload is process_binding; materialize is materialize_input; arm_fault is fault_arm; emit/inspect/shutdown payload is null. Reject mismatches before any side effect.",
      "R0 materialization_result has exact predecessor acceptance raw string and null r1_representation. R1 has null r0_acceptance and its new r1_receipt; never alter or repurpose the old null-owner receipt.",
      "Trace event_id selects exactly the matching payload schema. sequence starts at 0, increases by one; previous_event_sha256 is null only for sequence 0, otherwise SHA256 of the exact prior stored line including LF. monotonic_ns never decreases.",
      "wire_event offsets identify the exact raw line in retained stdin trace or named original stdout stream. Every declared child protocol line must occur once in trace; unexplained protocol output, duplicate responses and unmatched operation IDs reject. Ordinary UE log text is retained but never parsed as proof.",
      "For each capture_slot there is exactly one domain. A null emission is permitted only in an expected failure before that domain emitted or in acquisition_failure. Complete successful and post-emission failure cases retain both actual captures unchanged. Mutated admission copies live only in fault/canonical-call traces.",
      "Every repeated liveness/observation/receipt/head field in case_record must equal the corresponding parsed raw trace/response. Convenience counts, status and claims are recomputed and compared; they never supply the verifier oracle.",
      "All raw SHA256 fields hash UTF-8 stored bytes including LF, except files and streams hash exact file bytes. Object identity digests (binding, argv, environment, descriptor map, inventories, startup, observation) hash their new stored canonical JSON including LF. Canonical record/Q hashes retain the predecessor law.",
      "An acquisition failure is not an expected failure and cannot satisfy any row. Missing process data due to death uses null observed_process with real poll_returncode and pipe-holder observations. Fabricated birth tuples or empty success objects reject."
    ]
  },
  "record_delivery": {
    "channel": "materialize_input on original stdin; no child-side file lookup, embedded R0 copy, or peer input",
    "R0": "Before materialize_0001, bind succeeds. Parent sends exact pinned stored R0 UTF-8 plus exact stored_receipt_bytes(launch_receipt(R0)) and the R0 projection. Child strictly parses both; verifies raw bytes, canonical digest, exact fixture schema/value identities and all launch receipt fields with the same acceptance semantics as validate_launch_artifact. It computes both digests from received bytes, never echoes supplied digests. Only then create Actors and issue old acceptance receipt. Emission reads this accepted R0 and physical Actor; no Q template supplied by parent.",
    "R1": "After the parent publishes the one resolver result, materialize_0002 carries those exact committed R1 bytes plus matching R1 projection and launch_receipt_raw_utf8=null. Child validates strict serialization, exact pinned R1 identity, parent/source ancestry, generation=1, owner=domain_A and original binding. validate_launch_artifact is R0-only and is NOT called or claimed for R1. Issue only the new r1_receipt after publication. Child does not resolve or mutate canonical data.",
    "ordering": "materialize_0001 may occur once before emit; materialize_0002 once after L3. Failed authentication precedes Actor destruction. Successful R1 authentication disables proposal capability permanently. Harness will not send R1 before successful resolver publication.",
    "negative_bytes": "Offline verifier adversaries remove R0 LF, add second LF, replace one byte, alter only launch receipt raw hash, change only projection owner, send R1 with an R0 launch receipt, and send a provisional working-state object. All reject before accepted materialization. These are byte-contract tests, not live runs."
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
  "failure_programs": [
    {
      "id": "F01",
      "prefix": "P0",
      "executor": "harness",
      "domain": "domain_B",
      "stage": "before_complete_set",
      "action": "Emit only QA; admit QA; call construct_bext_from_sealed_fixture_set(R0,primary_fixture(),[member_A]). No timer chooses membership.",
      "underlying_code": "concurrent_external_batch_rejected.fixture_set_mismatch",
      "terminal_physical": "Both remain exact R0; all current claims disabled.",
      "invocation": "construct with singleton admitted member list"
    },
    {
      "id": "F02",
      "prefix": "P1",
      "executor": "harness",
      "domain": "domain_A",
      "stage": "before_admission",
      "action": "Make a retained copy of captured QA raw bytes and remove its final LF only; parse unchanged object; pass changed raw bytes to admission with original receipts.",
      "underlying_code": "concurrent_external_rejected.q_shape_mismatch",
      "terminal_physical": "Both remain exact R0.",
      "invocation": "admit(R0, QA_object, QA_raw_without_LF, original receipts)"
    },
    {
      "id": "F03",
      "prefix": "P1",
      "executor": "harness",
      "domain": "domain_A",
      "stage": "before_admission",
      "action": "Copy QA; replace /target/id with shared_slot_02; recompute evidence_digest after removing only /evidence/evidence_digest; serialize with original law.",
      "underlying_code": "concurrent_external_rejected.consequence_contract_mismatch",
      "terminal_physical": "Both remain exact R0.",
      "invocation": "admit changed QA and changed stored bytes with original receipts"
    },
    {
      "id": "F04a",
      "prefix": "P1",
      "executor": "harness",
      "domain": "domain_A",
      "stage": "before_batch",
      "action": "Admit both exact captures. Construct with [member_A,member_A].",
      "underlying_code": "concurrent_external_batch_rejected.duplicate_input_id",
      "terminal_physical": "Both remain exact R0.",
      "invocation": "construct(R0,primary_fixture(),[member_A,member_A])"
    },
    {
      "id": "F04b",
      "prefix": "P1",
      "executor": "harness",
      "domain": "domain_B",
      "stage": "before_batch",
      "action": "Admit both exact captures. Copy member_B, keep its distinct input_id, replace only physical_event_id with member_A physical_event_id.",
      "underlying_code": "concurrent_external_batch_rejected.duplicate_physical_event_id",
      "terminal_physical": "Both remain exact R0.",
      "invocation": "construct(R0,primary_fixture(),[member_A,changed_member_B])"
    },
    {
      "id": "F05",
      "prefix": "P1",
      "executor": "harness",
      "domain": "domain_A",
      "stage": "before_admission",
      "action": "Copy QA; set /source/source_record_hash to pinned R1 canonical hash; recompute evidence_digest by unchanged law.",
      "underlying_code": "concurrent_external_rejected.source_record_mismatch",
      "terminal_physical": "Both remain exact R0.",
      "invocation": "admit changed QA and changed stored bytes with original receipts"
    },
    {
      "id": "F06",
      "prefix": "P1",
      "executor": "harness",
      "domain": "domain_A",
      "stage": "before_admission",
      "action": "Copy QA; replace /proposed_effect/path with /current_causal_state/forbidden_owner; recompute evidence_digest.",
      "underlying_code": "concurrent_external_rejected.consequence_contract_mismatch",
      "terminal_physical": "Both remain exact R0.",
      "invocation": "admit changed QA and changed stored bytes with original receipts"
    },
    {
      "id": "F07",
      "prefix": "P2",
      "executor": "harness",
      "domain": "domain_A",
      "stage": "before_resolve",
      "action": "Terminate original A and wait for exit. Launch one replacement executable with fresh root/pipes/launch ID, same domain/witness. Attempt original identity comparison using copied original bind record. Actual PID/birth/root/pipe identities come from parent observations; none are copied.",
      "underlying_code": "lcer.original_process_identity_mismatch",
      "terminal_physical": "A unavailable; B remains R0. Replacement never acquires representation.",
      "invocation": "parent original_identity_guard before any resolve call"
    },
    {
      "id": "F08",
      "prefix": "P0",
      "executor": "harness",
      "domain": "domain_B",
      "stage": "before_complete_set",
      "action": "Emit QA, terminate B and wait for exit before requesting QB. Parent samples original process, detects poll returncode.",
      "underlying_code": "lcer.original_process_exited",
      "terminal_physical": "B unavailable; A remains R0.",
      "invocation": "parent liveness guard before peer emission"
    },
    {
      "id": "F09",
      "prefix": "P0",
      "executor": "harness",
      "domain": "domain_A",
      "stage": "before_emission",
      "action": "Create working_state_projection(R0,R0.current_causal_state,R0.future_causal_state); send its stored JSON as record_raw_utf8 in materialize_0002 with an otherwise R1-shaped projection. This is an invalid refresh attempt before commit, not a resolver output.",
      "underlying_code": "lcer.committed_record_required",
      "terminal_physical": "Both remain exact R0; authentication rejects before destruction.",
      "invocation": "child materialize_0002 validation; terminal after error"
    },
    {
      "id": "F10a",
      "prefix": "P3",
      "executor": "harness",
      "domain": "domain_A",
      "stage": "after_commit",
      "action": "Attempt admission of captured QA against current R1 with original receipts.",
      "underlying_code": "concurrent_external_rejected.input_id_already_adjudicated",
      "terminal_physical": "Both stale exact R0; no refresh.",
      "invocation": "admit(R1,QA,QA_raw,original receipts)"
    },
    {
      "id": "F10b",
      "prefix": "P3",
      "executor": "harness",
      "domain": "domain_A",
      "stage": "after_commit",
      "action": "Copy QA; replace only input_id with replay_probe_new_input; retain original adjudicated physical_event_id. Replay check precedes shape/digest checks.",
      "underlying_code": "concurrent_external_rejected.physical_event_id_already_adjudicated",
      "terminal_physical": "Both stale exact R0; no refresh.",
      "invocation": "admit(R1,changed_QA,changed stored bytes,original receipts)"
    },
    {
      "id": "F11",
      "prefix": "P3",
      "executor": "harness",
      "domain": "domain_A",
      "stage": "before_refresh",
      "action": "Terminate original A and wait for exit; sample liveness before any refresh.",
      "underlying_code": "lcer.original_process_exited",
      "terminal_physical": "A unavailable; B stale R0.",
      "invocation": "parent liveness guard"
    },
    {
      "id": "F12",
      "prefix": "P3",
      "executor": "harness",
      "domain": "domain_B",
      "stage": "before_refresh",
      "action": "Terminate original B and wait for exit; sample liveness before any refresh.",
      "underlying_code": "lcer.original_process_exited",
      "terminal_physical": "B unavailable; A stale R0.",
      "invocation": "parent liveness guard"
    },
    {
      "id": "F13",
      "prefix": "P3",
      "executor": "unreal",
      "domain": "domain_A",
      "stage": "after_resource_before_anchor",
      "action": "Refresh A first. After successful R1 authentication, disable claim, destroy old Actors and wait for their absence; spawn R1 resource with domain_A owner. Consume fault before spawning anchor. Leave the one new resource in the world; do not restore R0.",
      "underlying_code": "lcer.injected_partial_publication",
      "terminal_physical": "A unavailable: zero anchors, one R1 resource. B stale R0.",
      "invocation": "arm_fault_0001 then materialize_0002 on A; error then terminal census"
    },
    {
      "id": "F14",
      "prefix": "P3",
      "executor": "unreal",
      "domain": "domain_B",
      "stage": "after_resource_before_anchor",
      "action": "Refresh B first. After successful R1 authentication, disable claim, destroy old Actors and wait for absence; spawn R1 resource. Consume fault before anchor. Leave the new resource; do not restore R0.",
      "underlying_code": "lcer.injected_partial_publication",
      "terminal_physical": "B unavailable: zero anchors, one R1 resource. A stale R0.",
      "invocation": "arm_fault_0001 then materialize_0002 on B; error then terminal census"
    },
    {
      "id": "F15",
      "prefix": "P3",
      "executor": "unreal",
      "domain": "domain_A",
      "stage": "after_receipt_before_observation",
      "action": "Refresh A first completely and construct a truthful R1 receipt. Consume hook after receipt construction but before response. Set only live resource allocation_owner to domain_B; emit the previously constructed receipt unaltered.",
      "underlying_code": "lcer.live_owner_mismatch",
      "terminal_physical": "A unclaimed: one R1 anchor and resource, wrong owner domain_B. B stale R0.",
      "invocation": "arm_fault_0001; materialize_0002 A; inspect_L4 both; parent oracle rejects"
    },
    {
      "id": "F16a",
      "prefix": "P3",
      "executor": "unreal",
      "domain": "domain_A",
      "stage": "after_receipt_before_observation",
      "action": "Refresh A first completely. Spawn one extra resource_state Actor with a new UObject path, same R1 record/generation/domain/owner. Keep original pair.",
      "underlying_code": "lcer.live_actor_cardinality_mismatch",
      "terminal_physical": "A unclaimed: one R1 anchor and two R1 resources. B stale R0.",
      "invocation": "arm_fault_0001; materialize_0002 A; inspect_L4 both; parent oracle rejects"
    },
    {
      "id": "F16b",
      "prefix": "P3",
      "executor": "unreal",
      "domain": "domain_A",
      "stage": "after_receipt_before_observation",
      "action": "Refresh A first completely. Spawn one extra resource_state Actor with a new UObject path, R0 record, generation 0 and null owner. Keep R1 pair.",
      "underlying_code": "lcer.live_generation_mismatch",
      "terminal_physical": "A unclaimed: R1 pair plus one R0 resource. B stale R0.",
      "invocation": "arm_fault_0001; materialize_0002 A; inspect_L4 both; parent oracle rejects"
    },
    {
      "id": "F17",
      "prefix": "P3",
      "executor": "harness",
      "domain": "domain_A",
      "stage": "before_refresh",
      "action": "Send exact R0 bytes with its R0 projection and launch receipt as materialize_0002. Child phase rule requires generation 1 after the initial materialization/emission.",
      "underlying_code": "lcer.immediate_successor_required",
      "terminal_physical": "Both stale R0; no Actor destruction.",
      "invocation": "materialize_0002 A with stale R0 input"
    },
    {
      "id": "F18",
      "prefix": "P3",
      "executor": "harness",
      "domain": "domain_A",
      "stage": "before_refresh",
      "action": "Create normal R1 materialize command then replace only outer binding_sha256 with 64 zero digits. Retain original command and altered wire bytes.",
      "underlying_code": "lcer.binding_mismatch",
      "terminal_physical": "Both stale R0; no Actor destruction.",
      "invocation": "materialize_0002 A with altered outer binding"
    }
  ],
  "failure_execution_law": {
    "schedule": "Expand each prefix recursively, then perform exact action/invocation. Do not execute the default next prefix. All F03/F05/F06 mutated copies recompute only the unchanged evidence digest; original physical captures/receipts remain untouched in emission slots. Save exact mutated call arguments and before/after bytes.",
    "normalization": "Map each run to its original F-family failure_code. A run accepts expected_failure only if the actual exception/independent-oracle code equals its underlying_code and all canonical/physical assertions pass. A matching LCER summary alone cannot pass.",
    "canonical_assertions": "Before-commit runs: zero resolver publications; initial and terminal stored bytes equal pinned R0; canonical-call record before/after identical. Post-commit runs: exactly one successful resolver call/publish edge, published and terminal bytes equal pinned R1, no second resolver call. All underlying rejection calls must actually execute.",
    "physical_assertions": "Compare terminal raw Actor rows and process observations to terminal_physical. All affected current/synchronized claims disabled. Surviving peer state is independently censused; death requires observed exit, never a null placeholder alone.",
    "one_shot": "Unreal accepts exactly its declared child-owned arm and matching stage/operation. Ack is emitted before materialize. Hook records before/after world census and consumed=true once. An unused arm, repeated arm, wrong stage/domain/run, synthetic error without physical action, missing consumed event or modified probe output fails acquisition.",
    "oracle_precedence": "Binding before command semantics; exact committed raw identity before lifecycle sequence before destruction. At observation: wrong world first, mixed generation next, cardinality next, record/domain next, owner last. This makes F16b report generation mismatch even though cardinality also differs.",
    "canonical_fault_programs": "C01-C06 each expand P2, sample before_resolve, call unchanged resolve_external_batch with its corresponding existing fault_point, retain the exact full hook-specific exception from canonical_fault_codes, sample after_resolve, terminal census and cleanup. No install/publish edge; R0 exact; no published replay barrier. Hook order follows canonical_faults. No child arm command."
  },
  "unchanged_dependencies": {
    "CityMaterializationProof/CityMaterializationProof.uproject": "d4cf6ee332faf8705cd3eab6a3a9a2a110e5a41daa1c361e95a0181012aea7ac",
    "CityMaterializationProof/Config/DefaultEngine.ini": "68c6a6c0dd9362574b2b5ecb36e3b63dedc8cc53c5a962382c56736d10121aa7",
    "CityMaterializationProof/Config/DefaultGame.ini": "4e585b50ed08182eab92acaf5ce5baf6138713a161adf90bd83850003ec22033",
    "CityMaterializationProof/Config/DefaultInput.ini": "1896fc5dc59d5eb78f504ae7619fd2eb393a551b6ffcced7ab4d560c3d686bfa",
    "CityMaterializationProof/Source/CityMaterializationProof.Target.cs": "9c243b7ad29c5d3b4c3b3ba645cbf14e135c5c77c70a7f8b55d057ab8a26ac52",
    "CityMaterializationProof/Source/CityMaterializationProof/BridgeAccessPoint.cpp": "1ab40256bf8bcbfd8464d1a7cdce5511ec97bd60fe6a496927f2de76bafcbee9",
    "CityMaterializationProof/Source/CityMaterializationProof/BridgeAccessPoint.h": "823da75aad621604cdb1b36d8668b09a37cca0bcc385e174d6d2ece3fe1051d3",
    "CityMaterializationProof/Source/CityMaterializationProof/CanonicalSpatialTopologyProofAdapter.cpp": "7a068b41508e33de510f7301f8a9ee1248c6d09abd789e9a38cb86b354725d78",
    "CityMaterializationProof/Source/CityMaterializationProof/CanonicalSpatialTopologyProofAdapter.h": "5d652be69ed6dfb05f7ec1c7857950694207db623b6e20bd2bf9f597ae04c641",
    "CityMaterializationProof/Source/CityMaterializationProof/CanonicalTopologyRepresentationActor.cpp": "32649c131810bae93c44fc54884a70ef37f7963579cb8027b9e70375cde4b4f3",
    "CityMaterializationProof/Source/CityMaterializationProof/CanonicalTopologyRepresentationActor.h": "23dca5db8484a83ba33165ae594f37d7192ba2bbb1935f28b027dfaeb6266e55",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationActor.cpp": "892f3afd4dcda04465b024d56dd922e9f9f6b7ab35660a0f967ce5875cb04bf5",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationActor.h": "748d797af131a01833a3c00cdb405d4f97618cd8c97f0e9d1a8ea33b0a06ead9",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationProof.Build.cs": "a3de5b70766741ea0b325cc0a847261c995b03f428f327564c171eacc82b15ed",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationProof.cpp": "a12a6f19764d880bd60bc340fb363bb4f9be7d753c639bde640bf8d9d0a0e372",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationProof.h": "972f8f69b8fbb624b8f90ae64cc8a282d2e4d38e0915279c0dcbc7ddd73851e8",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofCharacter.cpp": "4527faf98ddb8667888f4911c2a57aa1953f7ed66ad55968fe27dba3b1ad1358",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofCharacter.h": "888dfa7fee0e7a66a96076a1dc3e37215f5d8bb0213f31771f593a5ad508c7c0",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofGameMode.cpp": "8b4699e9310d6e270319d5f136006073a20f0aa2033ea06c1680f23cdb40cfda",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofGameMode.h": "d4fc425030762ffa37ca8e333cb306f99fd02a74f73f50690ae3937e9c6a55b4",
    "CityMaterializationProof/Source/CityMaterializationProof/ConcurrentEvidenceSurface.cpp": "153b1cb3814169d2bed70e3ff3f6191681f11e05e95687c84c37834a40c3dd8b",
    "CityMaterializationProof/Source/CityMaterializationProof/ConcurrentEvidenceSurface.h": "ea7d47bc09798c7ce002ca3b99c040cb347d049f4de64ff201e4c54ef02091a8",
    "CityMaterializationProof/Source/CityMaterializationProof/ConcurrentExternalEvidenceProofAdapter.cpp": "6ef847283216bf35551fce978f367279627d68c7d845f60aa0c0683481ba8a2a",
    "CityMaterializationProof/Source/CityMaterializationProof/ConcurrentExternalEvidenceProofAdapter.h": "e54390475860331c014da1862bccc1b3aea0e5f3fa35824c4719a64d04f782d9",
    "CityMaterializationProof/Source/CityMaterializationProof/CrewOperationPoint.cpp": "26eaf43fed3a77b68adf6f3133fe448a6ce6d91a4c21859ac19c8b2af9b2be94",
    "CityMaterializationProof/Source/CityMaterializationProof/CrewOperationPoint.h": "75ab04322e72b2bf5c0c996e4f26d5832d570ede4495c88a2095898cb28064be",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyCommandRouter.cpp": "8ec98fd1dcce271cc21ddd7c3915d8adf9a3d1e9d042a3e4245b0056d03a49c3",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyCommandRouter.h": "912b7d3f97620048de430e2c567de429672ef73d348b8324121de9180523af77",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyHeadAnchorActor.cpp": "1aecb398e9d3e7a702b37c6d82e63301f9c01911e497f10fe309651f6ea008c8",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyHeadAnchorActor.h": "2caa0d3e6407db59074682b8d4c9953498a2dd4ae6c0ca864a16c9c90201c07b",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyLiveWorldProbe.cpp": "220fad9ddb0da4027d8ebde1574fd2a490e1fb03f2a4d60c1b43d0ea0d73a14d",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyLiveWorldProbe.h": "9e55d89dc07b8976ecf007448bd2e7c88c17c8f8e416041c0e080dfbfc4f5c47",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyProofAdapter.cpp": "e5dd786de3ed3aac06507fff5eaeb499128a0753c72dc5675b35bd881a54e1e0",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyProofAdapter.h": "ddaf662c2ee716d55e36d80c121a42d63890d2056a0f2fad0fcff20008004e56",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancySubjectActor.cpp": "b71086185b037e52f7317d474a07cf6c918dbcf095878dbcd07eb18a29cee83d",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancySubjectActor.h": "9ad4c484838ec03744609b5885dde51bb48416a932188d7b904b104c598e2221",
    "CityMaterializationProof/Source/CityMaterializationProof/IntegratedGateTokenPoint.cpp": "4af4db5d9d38beee9429ce3a9dc426e2e441c9e007bcc39969fba2e3df229f4d",
    "CityMaterializationProof/Source/CityMaterializationProof/IntegratedGateTokenPoint.h": "406663682c6b750d44a7125cb3f68a97adbbfcca22a467c6254b5cd69f0661b1",
    "CityMaterializationProof/Source/CityMaterializationProof/IntegratedUnrealProofAdapter.cpp": "9de1d33c226c58ad3238cfbe93aa6e7719f51211cc845490327df48fc3cee9f6",
    "CityMaterializationProof/Source/CityMaterializationProof/IntegratedUnrealProofAdapter.h": "fd81e9f59dde36d7a564159140d3001b6cc4151211678608e57502749f260430",
    "CityMaterializationProof/Source/CityMaterializationProof/LiveCommitmentRelayPoint.cpp": "549bd615b0e0811e15839762095bcd2ff288097d8c8116a42917174c3e5d2784",
    "CityMaterializationProof/Source/CityMaterializationProof/LiveCommitmentRelayPoint.h": "b2dbb806487dd608008089b87f4019d6aa2cf4511d9fda6eb7bec0d4454d8ac5",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainCommandRouter.cpp": "7072a6c6d26676a1b13285aded72b8db68f394e4a581c63324f292fae0693811",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainCommandRouter.h": "afddb2cbceece7d18217f384965f2e1f9805aaf06eac9e942d08e5931a8dbfb1",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainProofAdapter.cpp": "3063ae41be306201377fb6c905bd250ad73bb6842c4d05c6c057c60f019c9905",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainProofAdapter.h": "ede78ca44e573e11821afb80dc6ed1b4ac0eec51300574133f5ebf51681e6931",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainRepresentationActor.cpp": "a07fc0b553c2b99d4845efc86bf778379f90816f29ae72e1251b1de6ac5f367a",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainRepresentationActor.h": "f0f9a8845439675f35a710054a62c2f4a411fbfc28507ee0af8f82f2c3908799",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalRebindProbe.cpp": "f2360cc84101dcfdcd40e81fd74b8caf2acdff2a2a226b6fdc38fcfa823ee3f1",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalRebindProbe.h": "b0c690d06a2380d44f20b8ae64e3707d1427af518640e43d39435b8717eca77c",
    "CityMaterializationProof/Source/CityMaterializationProofEditor.Target.cs": "b35c28f8c5a455e281f075990eda62f95d2e78dc5514ee9c52a9626d6d5f6578",
    "proof_kernel/kernel.py": "3ae9b961d7302aa999e59c2dd87e26f0e6eb55f105f30decb3132a6d0f32e2c3"
  },
  "dependency_contract": {
    "python": "Before importing, verifier verifies exact release bytes for new Python files, arbitration.py and kernel.py. Only these local modules plus Python stdlib are allowed. Record Python executable/version identity. Run with isolated import path restricted to verified proof_kernel and stdlib; reject local shadow modules.",
    "project": "unchanged_dependencies enumerates the project descriptor, all original target/module source and Config files used by UBT or runtime. Verify before build, launch, and release verification. Any added project source/config or enabled local plugin besides planned_source_paths rejects. No historical file is edited.",
    "external": "build_record.external_inputs binds all UBT build action prerequisites, toolchain/SDK identities, engine Build.version, engine config hierarchy and enabled engine plugin descriptors, loaded images and dyld shared-cache identity. The independent verifier requires complete inventories and exact equality across startup/process checkpoints and the build identities for binary/config inputs. SDK identity hashes SDKSettings.json; compiler hashes clang executable; dyld cache is pinned by its file hash and UUID inventory.",
    "acquisition": "Collect build prerequisites from the executed UBT action graph and loaded images from dyld enumeration plus vmmap/lsof parent observations. Resolve real paths, reject symlinks in project/release, hash external targets after realpath resolution. Record architecture and Mach-O UUID; dyld-cache images bind cache bytes and UUID. Generated UBT paths are external build artifacts, never extra project source authority.",
    "document_checker": "validate_live_cross_domain_evidence_round_trip_spec.py is a non-release review tool. It and CITY native/selection dependencies are deliberately outside the future game release. The future release verifier consumes only the contract/spec and complete declared executable closure.",
    "no_source_bootstrap": "A release verifier may not import unverified adjacent Python or use candidate success flags. First authenticate closed member set, then import the authenticated predecessor and independently derive raw expected records/admission/resolution."
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
  },
  "artifact_hash_graph": {
    "case_ids": [
      "W1",
      "W2",
      "W3",
      "W4",
      "W5",
      "W6",
      "W7",
      "W8",
      "F01",
      "F02",
      "F03",
      "F04a",
      "F04b",
      "F05",
      "F06",
      "F07",
      "F08",
      "F09",
      "F10a",
      "F10b",
      "F11",
      "F12",
      "F13",
      "F14",
      "F15",
      "F16a",
      "F16b",
      "F17",
      "F18",
      "C01",
      "C02",
      "C03",
      "C04",
      "C05",
      "C06"
    ],
    "construction_order": [
      "canonical reference files and build.log",
      "build.json",
      "each case raw process streams and harness.jsonl closed after cleanup",
      "each case record.json",
      "acquisition.json",
      "self-excluding release manifest"
    ],
    "case_record_targets": {
      "W1": [
        "W1/harness.jsonl",
        "W1/domain_A.stdout.log",
        "W1/domain_A.stderr.log",
        "W1/domain_B.stdout.log",
        "W1/domain_B.stderr.log"
      ],
      "W2": [
        "W2/harness.jsonl",
        "W2/domain_A.stdout.log",
        "W2/domain_A.stderr.log",
        "W2/domain_B.stdout.log",
        "W2/domain_B.stderr.log"
      ],
      "W3": [
        "W3/harness.jsonl",
        "W3/domain_A.stdout.log",
        "W3/domain_A.stderr.log",
        "W3/domain_B.stdout.log",
        "W3/domain_B.stderr.log"
      ],
      "W4": [
        "W4/harness.jsonl",
        "W4/domain_A.stdout.log",
        "W4/domain_A.stderr.log",
        "W4/domain_B.stdout.log",
        "W4/domain_B.stderr.log"
      ],
      "W5": [
        "W5/harness.jsonl",
        "W5/domain_A.stdout.log",
        "W5/domain_A.stderr.log",
        "W5/domain_B.stdout.log",
        "W5/domain_B.stderr.log"
      ],
      "W6": [
        "W6/harness.jsonl",
        "W6/domain_A.stdout.log",
        "W6/domain_A.stderr.log",
        "W6/domain_B.stdout.log",
        "W6/domain_B.stderr.log"
      ],
      "W7": [
        "W7/harness.jsonl",
        "W7/domain_A.stdout.log",
        "W7/domain_A.stderr.log",
        "W7/domain_B.stdout.log",
        "W7/domain_B.stderr.log"
      ],
      "W8": [
        "W8/harness.jsonl",
        "W8/domain_A.stdout.log",
        "W8/domain_A.stderr.log",
        "W8/domain_B.stdout.log",
        "W8/domain_B.stderr.log"
      ],
      "F01": [
        "F01/harness.jsonl",
        "F01/domain_A.stdout.log",
        "F01/domain_A.stderr.log",
        "F01/domain_B.stdout.log",
        "F01/domain_B.stderr.log"
      ],
      "F02": [
        "F02/harness.jsonl",
        "F02/domain_A.stdout.log",
        "F02/domain_A.stderr.log",
        "F02/domain_B.stdout.log",
        "F02/domain_B.stderr.log"
      ],
      "F03": [
        "F03/harness.jsonl",
        "F03/domain_A.stdout.log",
        "F03/domain_A.stderr.log",
        "F03/domain_B.stdout.log",
        "F03/domain_B.stderr.log"
      ],
      "F04a": [
        "F04a/harness.jsonl",
        "F04a/domain_A.stdout.log",
        "F04a/domain_A.stderr.log",
        "F04a/domain_B.stdout.log",
        "F04a/domain_B.stderr.log"
      ],
      "F04b": [
        "F04b/harness.jsonl",
        "F04b/domain_A.stdout.log",
        "F04b/domain_A.stderr.log",
        "F04b/domain_B.stdout.log",
        "F04b/domain_B.stderr.log"
      ],
      "F05": [
        "F05/harness.jsonl",
        "F05/domain_A.stdout.log",
        "F05/domain_A.stderr.log",
        "F05/domain_B.stdout.log",
        "F05/domain_B.stderr.log"
      ],
      "F06": [
        "F06/harness.jsonl",
        "F06/domain_A.stdout.log",
        "F06/domain_A.stderr.log",
        "F06/domain_B.stdout.log",
        "F06/domain_B.stderr.log"
      ],
      "F07": [
        "F07/harness.jsonl",
        "F07/domain_A.stdout.log",
        "F07/domain_A.stderr.log",
        "F07/domain_B.stdout.log",
        "F07/domain_B.stderr.log",
        "F07/replacement.stdout.log",
        "F07/replacement.stderr.log"
      ],
      "F08": [
        "F08/harness.jsonl",
        "F08/domain_A.stdout.log",
        "F08/domain_A.stderr.log",
        "F08/domain_B.stdout.log",
        "F08/domain_B.stderr.log"
      ],
      "F09": [
        "F09/harness.jsonl",
        "F09/domain_A.stdout.log",
        "F09/domain_A.stderr.log",
        "F09/domain_B.stdout.log",
        "F09/domain_B.stderr.log"
      ],
      "F10a": [
        "F10a/harness.jsonl",
        "F10a/domain_A.stdout.log",
        "F10a/domain_A.stderr.log",
        "F10a/domain_B.stdout.log",
        "F10a/domain_B.stderr.log"
      ],
      "F10b": [
        "F10b/harness.jsonl",
        "F10b/domain_A.stdout.log",
        "F10b/domain_A.stderr.log",
        "F10b/domain_B.stdout.log",
        "F10b/domain_B.stderr.log"
      ],
      "F11": [
        "F11/harness.jsonl",
        "F11/domain_A.stdout.log",
        "F11/domain_A.stderr.log",
        "F11/domain_B.stdout.log",
        "F11/domain_B.stderr.log"
      ],
      "F12": [
        "F12/harness.jsonl",
        "F12/domain_A.stdout.log",
        "F12/domain_A.stderr.log",
        "F12/domain_B.stdout.log",
        "F12/domain_B.stderr.log"
      ],
      "F13": [
        "F13/harness.jsonl",
        "F13/domain_A.stdout.log",
        "F13/domain_A.stderr.log",
        "F13/domain_B.stdout.log",
        "F13/domain_B.stderr.log"
      ],
      "F14": [
        "F14/harness.jsonl",
        "F14/domain_A.stdout.log",
        "F14/domain_A.stderr.log",
        "F14/domain_B.stdout.log",
        "F14/domain_B.stderr.log"
      ],
      "F15": [
        "F15/harness.jsonl",
        "F15/domain_A.stdout.log",
        "F15/domain_A.stderr.log",
        "F15/domain_B.stdout.log",
        "F15/domain_B.stderr.log"
      ],
      "F16a": [
        "F16a/harness.jsonl",
        "F16a/domain_A.stdout.log",
        "F16a/domain_A.stderr.log",
        "F16a/domain_B.stdout.log",
        "F16a/domain_B.stderr.log"
      ],
      "F16b": [
        "F16b/harness.jsonl",
        "F16b/domain_A.stdout.log",
        "F16b/domain_A.stderr.log",
        "F16b/domain_B.stdout.log",
        "F16b/domain_B.stderr.log"
      ],
      "F17": [
        "F17/harness.jsonl",
        "F17/domain_A.stdout.log",
        "F17/domain_A.stderr.log",
        "F17/domain_B.stdout.log",
        "F17/domain_B.stderr.log"
      ],
      "F18": [
        "F18/harness.jsonl",
        "F18/domain_A.stdout.log",
        "F18/domain_A.stderr.log",
        "F18/domain_B.stdout.log",
        "F18/domain_B.stderr.log"
      ],
      "C01": [
        "C01/harness.jsonl",
        "C01/domain_A.stdout.log",
        "C01/domain_A.stderr.log",
        "C01/domain_B.stdout.log",
        "C01/domain_B.stderr.log"
      ],
      "C02": [
        "C02/harness.jsonl",
        "C02/domain_A.stdout.log",
        "C02/domain_A.stderr.log",
        "C02/domain_B.stdout.log",
        "C02/domain_B.stderr.log"
      ],
      "C03": [
        "C03/harness.jsonl",
        "C03/domain_A.stdout.log",
        "C03/domain_A.stderr.log",
        "C03/domain_B.stdout.log",
        "C03/domain_B.stderr.log"
      ],
      "C04": [
        "C04/harness.jsonl",
        "C04/domain_A.stdout.log",
        "C04/domain_A.stderr.log",
        "C04/domain_B.stdout.log",
        "C04/domain_B.stderr.log"
      ],
      "C05": [
        "C05/harness.jsonl",
        "C05/domain_A.stdout.log",
        "C05/domain_A.stderr.log",
        "C05/domain_B.stdout.log",
        "C05/domain_B.stderr.log"
      ],
      "C06": [
        "C06/harness.jsonl",
        "C06/domain_A.stdout.log",
        "C06/domain_A.stderr.log",
        "C06/domain_B.stdout.log",
        "C06/domain_B.stderr.log"
      ]
    },
    "acquisition_targets": [
      "build.json",
      "build.log",
      "canonical/R0.json",
      "canonical/R1.json",
      "canonical/QA.json",
      "canonical/QB.json",
      "W1/record.json",
      "W1/harness.jsonl",
      "W1/domain_A.stdout.log",
      "W1/domain_A.stderr.log",
      "W1/domain_B.stdout.log",
      "W1/domain_B.stderr.log",
      "W2/record.json",
      "W2/harness.jsonl",
      "W2/domain_A.stdout.log",
      "W2/domain_A.stderr.log",
      "W2/domain_B.stdout.log",
      "W2/domain_B.stderr.log",
      "W3/record.json",
      "W3/harness.jsonl",
      "W3/domain_A.stdout.log",
      "W3/domain_A.stderr.log",
      "W3/domain_B.stdout.log",
      "W3/domain_B.stderr.log",
      "W4/record.json",
      "W4/harness.jsonl",
      "W4/domain_A.stdout.log",
      "W4/domain_A.stderr.log",
      "W4/domain_B.stdout.log",
      "W4/domain_B.stderr.log",
      "W5/record.json",
      "W5/harness.jsonl",
      "W5/domain_A.stdout.log",
      "W5/domain_A.stderr.log",
      "W5/domain_B.stdout.log",
      "W5/domain_B.stderr.log",
      "W6/record.json",
      "W6/harness.jsonl",
      "W6/domain_A.stdout.log",
      "W6/domain_A.stderr.log",
      "W6/domain_B.stdout.log",
      "W6/domain_B.stderr.log",
      "W7/record.json",
      "W7/harness.jsonl",
      "W7/domain_A.stdout.log",
      "W7/domain_A.stderr.log",
      "W7/domain_B.stdout.log",
      "W7/domain_B.stderr.log",
      "W8/record.json",
      "W8/harness.jsonl",
      "W8/domain_A.stdout.log",
      "W8/domain_A.stderr.log",
      "W8/domain_B.stdout.log",
      "W8/domain_B.stderr.log",
      "F01/record.json",
      "F01/harness.jsonl",
      "F01/domain_A.stdout.log",
      "F01/domain_A.stderr.log",
      "F01/domain_B.stdout.log",
      "F01/domain_B.stderr.log",
      "F02/record.json",
      "F02/harness.jsonl",
      "F02/domain_A.stdout.log",
      "F02/domain_A.stderr.log",
      "F02/domain_B.stdout.log",
      "F02/domain_B.stderr.log",
      "F03/record.json",
      "F03/harness.jsonl",
      "F03/domain_A.stdout.log",
      "F03/domain_A.stderr.log",
      "F03/domain_B.stdout.log",
      "F03/domain_B.stderr.log",
      "F04a/record.json",
      "F04a/harness.jsonl",
      "F04a/domain_A.stdout.log",
      "F04a/domain_A.stderr.log",
      "F04a/domain_B.stdout.log",
      "F04a/domain_B.stderr.log",
      "F04b/record.json",
      "F04b/harness.jsonl",
      "F04b/domain_A.stdout.log",
      "F04b/domain_A.stderr.log",
      "F04b/domain_B.stdout.log",
      "F04b/domain_B.stderr.log",
      "F05/record.json",
      "F05/harness.jsonl",
      "F05/domain_A.stdout.log",
      "F05/domain_A.stderr.log",
      "F05/domain_B.stdout.log",
      "F05/domain_B.stderr.log",
      "F06/record.json",
      "F06/harness.jsonl",
      "F06/domain_A.stdout.log",
      "F06/domain_A.stderr.log",
      "F06/domain_B.stdout.log",
      "F06/domain_B.stderr.log",
      "F07/record.json",
      "F07/harness.jsonl",
      "F07/domain_A.stdout.log",
      "F07/domain_A.stderr.log",
      "F07/domain_B.stdout.log",
      "F07/domain_B.stderr.log",
      "F08/record.json",
      "F08/harness.jsonl",
      "F08/domain_A.stdout.log",
      "F08/domain_A.stderr.log",
      "F08/domain_B.stdout.log",
      "F08/domain_B.stderr.log",
      "F09/record.json",
      "F09/harness.jsonl",
      "F09/domain_A.stdout.log",
      "F09/domain_A.stderr.log",
      "F09/domain_B.stdout.log",
      "F09/domain_B.stderr.log",
      "F10a/record.json",
      "F10a/harness.jsonl",
      "F10a/domain_A.stdout.log",
      "F10a/domain_A.stderr.log",
      "F10a/domain_B.stdout.log",
      "F10a/domain_B.stderr.log",
      "F10b/record.json",
      "F10b/harness.jsonl",
      "F10b/domain_A.stdout.log",
      "F10b/domain_A.stderr.log",
      "F10b/domain_B.stdout.log",
      "F10b/domain_B.stderr.log",
      "F11/record.json",
      "F11/harness.jsonl",
      "F11/domain_A.stdout.log",
      "F11/domain_A.stderr.log",
      "F11/domain_B.stdout.log",
      "F11/domain_B.stderr.log",
      "F12/record.json",
      "F12/harness.jsonl",
      "F12/domain_A.stdout.log",
      "F12/domain_A.stderr.log",
      "F12/domain_B.stdout.log",
      "F12/domain_B.stderr.log",
      "F13/record.json",
      "F13/harness.jsonl",
      "F13/domain_A.stdout.log",
      "F13/domain_A.stderr.log",
      "F13/domain_B.stdout.log",
      "F13/domain_B.stderr.log",
      "F14/record.json",
      "F14/harness.jsonl",
      "F14/domain_A.stdout.log",
      "F14/domain_A.stderr.log",
      "F14/domain_B.stdout.log",
      "F14/domain_B.stderr.log",
      "F15/record.json",
      "F15/harness.jsonl",
      "F15/domain_A.stdout.log",
      "F15/domain_A.stderr.log",
      "F15/domain_B.stdout.log",
      "F15/domain_B.stderr.log",
      "F16a/record.json",
      "F16a/harness.jsonl",
      "F16a/domain_A.stdout.log",
      "F16a/domain_A.stderr.log",
      "F16a/domain_B.stdout.log",
      "F16a/domain_B.stderr.log",
      "F16b/record.json",
      "F16b/harness.jsonl",
      "F16b/domain_A.stdout.log",
      "F16b/domain_A.stderr.log",
      "F16b/domain_B.stdout.log",
      "F16b/domain_B.stderr.log",
      "F17/record.json",
      "F17/harness.jsonl",
      "F17/domain_A.stdout.log",
      "F17/domain_A.stderr.log",
      "F17/domain_B.stdout.log",
      "F17/domain_B.stderr.log",
      "F18/record.json",
      "F18/harness.jsonl",
      "F18/domain_A.stdout.log",
      "F18/domain_A.stderr.log",
      "F18/domain_B.stdout.log",
      "F18/domain_B.stderr.log",
      "C01/record.json",
      "C01/harness.jsonl",
      "C01/domain_A.stdout.log",
      "C01/domain_A.stderr.log",
      "C01/domain_B.stdout.log",
      "C01/domain_B.stderr.log",
      "C02/record.json",
      "C02/harness.jsonl",
      "C02/domain_A.stdout.log",
      "C02/domain_A.stderr.log",
      "C02/domain_B.stdout.log",
      "C02/domain_B.stderr.log",
      "C03/record.json",
      "C03/harness.jsonl",
      "C03/domain_A.stdout.log",
      "C03/domain_A.stderr.log",
      "C03/domain_B.stdout.log",
      "C03/domain_B.stderr.log",
      "C04/record.json",
      "C04/harness.jsonl",
      "C04/domain_A.stdout.log",
      "C04/domain_A.stderr.log",
      "C04/domain_B.stdout.log",
      "C04/domain_B.stderr.log",
      "C05/record.json",
      "C05/harness.jsonl",
      "C05/domain_A.stdout.log",
      "C05/domain_A.stderr.log",
      "C05/domain_B.stdout.log",
      "C05/domain_B.stderr.log",
      "C06/record.json",
      "C06/harness.jsonl",
      "C06/domain_A.stdout.log",
      "C06/domain_A.stderr.log",
      "C06/domain_B.stdout.log",
      "C06/domain_B.stderr.log",
      "F07/replacement.stdout.log",
      "F07/replacement.stderr.log"
    ],
    "manifest_targets": "Exactly release_members; exclude release_manifest itself. The outer manifest hashes acquisition.json.",
    "membership_vs_hash": "artifact_members lists acquisition.json without an internal self digest. No case record hashes itself, acquisition or another case. Event chain hashes only previous complete lines; no forward reference. No semantic-hash projection is substituted for a raw file hash.",
    "verification": "Compare index member sets to these exact sets, resolve safe relative paths, check each raw size/hash. Reject self-edge, missing edge, extra edge, duplicate path or cycle before opening executable source."
  },
  "verifier_negative_cases": {
    "schema": "For every wire_schemas object, valid example plus root missing key, root extra key, wrong type, duplicate key; recursively mutate one nested required object per reference edge. Parse strings strictly before validating legacy content. Reject with lcer.schema_invalid. These are offline schema checks.",
    "semantic": [
      "response_wrong_command",
      "response_wrong_operation",
      "response_ok_with_error",
      "R0_receipt_used_for_R1",
      "missing_physical_event",
      "raw_line_offset_mismatch",
      "trace_gap",
      "trace_wrong_previous_hash",
      "changed_R0_byte",
      "changed_R0_launch_receipt",
      "changed_binding_field",
      "replaced_process_birth",
      "mixed_actor_generation",
      "omitted_actor_row",
      "unknown_config_input",
      "missing_kernel",
      "unlisted_import",
      "acquisition_self_hash",
      "case_self_hash",
      "manifest_missing_member"
    ],
    "execution": "Future verifier unittest suite starts from one valid retained release copied outside CITY, applies each named alteration independently, invokes verify argv and requires nonzero exit with exact lcer.schema_invalid for malformed schema or lcer.release_evidence_invalid for semantic discrepancy. It must reject from raw relationships, never fixture case-name matching. No Unreal launches."
  },
  "call_trace_contract": {
    "dispatch": {
      "admit_external_input_candidate": "admission_arguments",
      "construct_bext_from_sealed_fixture_set": "construction_arguments",
      "resolve_external_batch": "resolution_arguments"
    },
    "encoding": "arguments is a typed object, never an opaque JSON argument string. function must select exactly its mapped schema. Every *_raw_utf8 argument is strict stored predecessor JSON with one LF; duplicate keys, nonfinite numbers and unknown fields reject before replay. q_raw_base64 and fault raw_base64 use canonical RFC4648 base64 with padding, no whitespace, round-trip encode equality; they preserve any malformed original bytes without pretending those bytes passed JSON parsing.",
    "admission_call": "Decode record_raw_utf8, q_object_raw_utf8, materialization_receipt_raw_utf8 and emission_receipt_raw_utf8 strictly. Decode q_raw_base64 to actual bytes. Call admit_external_input_candidate(record,q_object,q_bytes,materialization_receipt,emission_receipt) in that exact positional order; no keyword arguments. q_object is stored independently of q_bytes so F02 can supply a valid object with missing-LF raw bytes.",
    "construction_call": "Decode record_raw_utf8 and fixture_raw_utf8 strictly. Decode each presentation_members_raw_utf8 item strictly, preserving array order. Call construct_bext_from_sealed_fixture_set(record,fixture,presentation_members) with those three positional arguments and no kwargs.",
    "resolution_call": "Decode record_raw_utf8,bext_raw_utf8 and each member_raw_utf8 strictly. admitted_members is lexically sorted by input_id with no duplicates. Construct only that input_id-to-member map. Call resolve_external_batch(record,bext,map,fault_point=arguments.fault_point), exactly three positional arguments and one keyword. canonical_call.fault_point must equal this value; it is null for other functions.",
    "nested_records": "record is exact pinned R0/R1. Original Q/receipts are exact captured predecessor values and constructor shapes. Fixture is exactly primary_fixture(R0). Admitted members must equal results independently derived from actual captured admission calls. BEXT/map must equal the independently repeated constructor result. No extra fields are allowed in these predecessor objects. The only deviations are the exact mutations named in failure_programs, applied to retained originals and compared field-for-field before replay. F10b explicitly changes input_id without repairing the old digest; replay must still reject at the event barrier. No unlisted member, field, mutation or argument encoding is legal.",
    "returns": "On exception, return_raw_utf8 and published_record_raw_utf8 are null and exception_code is the actual full code. On success exception_code is null. Admission return_raw_utf8 is the strict stored JSON of the exact returned member. Construction return_raw_utf8 decodes as the closed construction_return schema with exact returned BEXT/member map encoded by the same nested law. Resolver return_raw_utf8 is the exact returned R1 stored bytes; published bytes equal it only at the declared publication edge. Verifier repeats the actual call and compares each return or full exception code; recorded summary is not the oracle.",
    "fault_bytes": "For q_raw, base64 decodes the actual before/after proposed admission Q bytes; before must equal captured raw bytes and after must be exactly the declared mutation. The parsed q object stays separately in admission_arguments. For admission_arguments/construction_arguments/materialize_command, base64 decodes canonical JSON of the mapped closed schema (materialize_command uses command with command=materialize); reject unknown fields. Compare before/after recursively against the exact row action. Malformed bytes may occur only where the row explicitly changes raw bytes.",
    "fault_states": "Both states are mandatory. Child-owned hooks use fault_world_state with real probe results immediately around the action; never expected projection data. Process replacement/exit uses fault_process_state with actual liveness samples before/after. Harness Q/member/command mutation uses fault_bytes_state of the declared semantic type. Missing-input F01 uses construction_arguments with before and after both containing [actually admitted member_A]; its action is the actual incomplete-set invocation, not removal of an unobserved QB. F08 is process, F09/F17/F18 materialize_command, F04a/b construction_arguments, F02/F03/F05/F06/F10a/b admission_arguments. For F10a, before and after arguments are equal; the action is replay invocation against committed R1. F10b before uses captured QA and after the declared changed input_id. Consumed=true requires actual action/invocation and the exact row code.",
    "negative_cases": [
      "wrong_argument_schema_for_function",
      "unlisted_argument_field",
      "changed_positional_reconstruction",
      "kwargs_on_admission",
      "duplicate_member_key",
      "malformed_base64",
      "unlisted_nested_Q_field",
      "unlisted_member_mutation",
      "missing_fault_before",
      "wrong_fault_state_kind",
      "unsuffixed_canonical_fault_code"
    ]
  },
  "canonical_fault_codes": {
    "after_qa_provisional_mutation": "concurrent_external_resolution_rejected.partial_execution_fault.after_qa_provisional_mutation",
    "after_qb_ordinary_gate_evaluation": "concurrent_external_resolution_rejected.partial_execution_fault.after_qb_ordinary_gate_evaluation",
    "during_replay_barrier_construction": "concurrent_external_resolution_rejected.partial_execution_fault.during_replay_barrier_construction",
    "during_batch_ledger_construction": "concurrent_external_resolution_rejected.partial_execution_fault.during_batch_ledger_construction",
    "after_complete_r1_before_validation": "concurrent_external_resolution_rejected.partial_execution_fault.after_complete_r1_before_validation",
    "after_complete_r1_validation_before_publication": "concurrent_external_resolution_rejected.partial_execution_fault.after_complete_r1_validation_before_publication"
  }
}
```
