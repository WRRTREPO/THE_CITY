# Operator guide

Work from `/Users/boandersson/Projects/CITY`. Inspect `./start.sh --status --json`, `./start.sh --validate --json` and `./start.sh verify-release --json`. These routes inspect the current governed repository and stored Phase 4 release.

Before game implementation, finish MCDP P16, use its exact emitted PhoenixRising mount command, and seal the clean implementation contract. Refresh the CITY mount after every commit. Keep the frozen draft and old evidence unchanged.

The planned acquisition command below is for Phoenix implementation. Supply a new absolute temporary runtime parent and a fresh output root. Run acquisition once per candidate. Then run the independent release verifier and the frozen test command. A timeout ends that witness. It does not change membership or authorize a retry.

Budget: one successful build. Thirty-five paired cases. Seventy original process launches and one replacement-process negative. Each IPC wait is capped at 60 seconds. Each live case is capped at 900 seconds. Total wall time remains unmeasured. Preserve partial failure evidence. Never relabel a failed run as success.

The commands below are planned. They are not claims of installed runtime capability.

The exact contract projection follows. Historical review labels remain unchanged.

```json
{
  "schema": "city.mcdp.documentation.v1",
  "document": "OPERATOR_GUIDE.md",
  "contract_sha256": "b862ceba039b1f2f418b01fe32221f14f095ce4894d163077b4eaa31dd0a8755",
  "projection": {
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
    "build_argv": [
      "/Users/Shared/Epic Games/UE_5.8/Engine/Build/BatchFiles/Mac/Build.sh",
      "CityMaterializationProofEditor",
      "Mac",
      "Development",
      "-Project={absolute_city_project}",
      "-DisableUnity",
      "-WaitMutex"
    ]
  },
  "live_acceptance_verified": false,
  "game_implementation_authorized": false,
  "game_sealed": false,
  "trusted_ci": false
}
```
