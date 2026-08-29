"""Write and verify the frozen self-excluding Phase-3 release manifest."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping

from simultaneous_physical_domains import (
    ARTIFACT_NAMES,
    AUTHORITY_CASE_ACTIONS,
    D0,
    D1,
    DOMAIN_ROLES,
    H0,
    H1,
    HEAD_OBSERVATION_FAULT_POINTS,
    PHYSICAL_OBSERVATION_FAULT_STAGES,
    REFRESH_FAULT_STAGES,
    WITNESS_IDS,
    artifact_role_set_valid,
    bind_invocation,
    canonical_records,
    canonical_json,
    canonical_transition_run,
    current_head_authority_failures,
    current_head_observation,
    fault_arm_invocation,
    guard_open_control,
    head_observation_failure_witness,
    head_observation_fault_atomicity,
    inspection_invocation,
    operation_receipt_matrix,
    operational_process_instance_id,
    process_binding,
    projection_matrix,
    refresh_invocation,
    retention_equivalence_oracle,
    retention_witness,
    sha256_value,
    stale_quarantine_witness,
    stored_json_bytes,
    strict_load_stored_json,
    validate_materialization_receipt,
    validate_fault_arm_receipt,
    validate_local_step_observation,
    validate_measured_canonical_relation,
    validate_physical_observation,
    write_json,
)
from simultaneous_physical_domains_harness import (
    BINDING_VERIFICATION_MODES,
    LIVE_WORLD_READ_STAGES,
    PHYSICAL_FAULT_LIVE_WORLD_PREFIX_COUNTS,
    _source_audit,
)


ROOT = Path(__file__).resolve().parents[1]
RECORDS = Path(__file__).resolve().parent / "SimultaneousPhysicalDomainsProofRecords"
MANIFEST = ROOT / "Simultaneous Physical Domains Proof - v0.1.1 SHA256SUMS.txt"
EVIDENCE = ROOT / "Simultaneous Physical Domains Proof Evidence - v0.1.1.md"

GOVERNING_AND_PREDECESSOR_MEMBERS = (
    "README.md",
    "Resolution Semantics Law - v0.1.1.md",
    "Record-Relative Chronological Resolution Proof Evidence - v0.1.0.md",
    "Integrated Unreal Promotion-Unload-Repromotion Proof Evidence - v0.1.0.md",
    "Concurrent External Evidence Arbitration Proof Evidence - v0.1.0.md",
    "Canonical Spatial Topology Identity Proof - Draft.md",
    "Canonical Spatial Topology Identity Proof Evidence - v0.1.0.md",
    "Canonical Spatial Topology Identity Proof - v0.1.0 SHA256SUMS.txt",
    "Canonical Occupancy Transition Proof Evidence - v0.1.0.md",
    "Simultaneous Physical Domains Proof - Draft.md",
    "Simultaneous Physical Domains Proof - v0.1.1.md",
    "Simultaneous Physical Domains Proof Evidence - v0.1.1.md",
    "Co-op Open-City FPS Simulation - v0.7 Working Continuation.md",
    "THE_CITY Development Capacity and Progress Note - v0.1.11.md",
    "THE_CITY Developer Snapshot - v0.1.0.md",
    "THE_CITY Current Proof State and Repo-Agent Instruction - v0.1.0.md",
)

SEALED_CANONICAL_INPUT_MEMBERS = (
    "proof_kernel/CanonicalSpatialTopologyIdentityProofRecords/canonical_topology_R0.json",
    "proof_kernel/CanonicalSpatialTopologyIdentityProofRecords/canonical_topology_boundary_H0.json",
    "proof_kernel/CanonicalSpatialTopologyIdentityProofRecords/canonical_topology_R1.json",
)

PYTHON_SOURCE_MEMBERS = (
    "proof_kernel/kernel.py",
    "proof_kernel/canonical_spatial_topology_identity.py",
    "proof_kernel/simultaneous_physical_domains.py",
    "proof_kernel/simultaneous_physical_domains_harness.py",
    "proof_kernel/test_simultaneous_physical_domains.py",
    "proof_kernel/verify_simultaneous_physical_domains_release.py",
)

UNREAL_PROJECT_MEMBERS = (
    "CityMaterializationProof/CityMaterializationProof.uproject",
    "CityMaterializationProof/Config/DefaultEngine.ini",
    "CityMaterializationProof/Config/DefaultGame.ini",
    "CityMaterializationProof/Config/DefaultInput.ini",
    "CityMaterializationProof/README.md",
    "CityMaterializationProof/Source/CityMaterializationProof.Target.cs",
    "CityMaterializationProof/Source/CityMaterializationProofEditor.Target.cs",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationProof.Build.cs",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationProof.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationProof.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofGameMode.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofGameMode.h",
    "CityMaterializationProof/Source/CityMaterializationProof/BridgeAccessPoint.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/BridgeAccessPoint.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CanonicalSpatialTopologyProofAdapter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CanonicalSpatialTopologyProofAdapter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CanonicalTopologyRepresentationActor.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CanonicalTopologyRepresentationActor.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationActor.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationActor.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofCharacter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofCharacter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/ConcurrentEvidenceSurface.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/ConcurrentEvidenceSurface.h",
    "CityMaterializationProof/Source/CityMaterializationProof/ConcurrentExternalEvidenceProofAdapter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/ConcurrentExternalEvidenceProofAdapter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CrewOperationPoint.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CrewOperationPoint.h",
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
)

NON_ARTIFACT_MEMBERS = (
    GOVERNING_AND_PREDECESSOR_MEMBERS
    + SEALED_CANONICAL_INPUT_MEMBERS
    + PYTHON_SOURCE_MEMBERS
    + UNREAL_PROJECT_MEMBERS
)

PROCESS_BINDING_FIELDS = (
    "binding_schema", "proof_scenario", "witness_id", "domain_role",
    "harness_launch_id", "pid", "macos_process_start", "executable_realpath",
    "executable_raw_sha256", "unreal_engine_build_identity",
    "entry_map_package_identity", "project_realpath", "project_raw_sha256",
    "project_config_and_module_inventory_raw_sha256", "process_root_realpath",
    "launch_argv_raw_sha256", "launch_environment_audit_raw_sha256",
    "launch_cwd_realpath", "inherited_descriptor_map_raw_sha256",
    "control_pipe_id", "structured_output_pipe_id", "diagnostic_pipe_id",
)

_RUNTIME_INPUT_AUDIT_CACHE: dict[str, Any] | None = None


AUTHORITY_EXECUTION_EXPECTATIONS = (
    ("validate_materialization_receipt", "materialization_receipt_emission", "representation_digest_mismatch"),
    ("validate_projection", "projection_verification", "projection_matrix_mismatch"),
    ("head_disposition", "disposition", "synchronized_head_mismatch"),
    ("require_physical_capability", "current_head_authority_guard", "canonical_scheduling_disabled"),
    ("require_physical_capability", "current_head_authority_guard", "canonical_mutation_disabled"),
    ("head_disposition", "disposition", "synchronized_head_mismatch"),
    ("validate_physical_observation", "live_mesh_visibility_and_material_parameter_read", "live_mesh_surface_mismatch"),
    ("authoritative_representation", "sealed_canonical_payload_validation", "CanonicalTopologyRejected"),
    ("authoritative_representation", "sealed_canonical_payload_validation", "CanonicalTopologyRejected"),
    ("validate_physical_observation", "immutable_process_binding_verification", "physical_observation_binding_mismatch"),
    (
        "canonical_transition_run_signature_and_two_normal_order_replays",
        "canonical_transition_run_signature_and_two_normal_order_replays",
        "undeclared_order_argument_rejected_by_signature",
    ),
    ("validate_projection/two_redirected_fields", "validate_projection/two_redirected_fields", "live_or_bound_adversary_rejected"),
    ("validate_projection", "projection_verification", "projection_matrix_mismatch"),
    ("validate_projection", "projection_verification", "projection_matrix_mismatch"),
    ("validate_materialization_receipt", "process_binding_identity_verification", "receipt_binding_mismatch"),
    ("compiled_refresh_fault/local_atomic_publication/after", "compiled_refresh_fault/local_atomic_publication/after", "live_or_bound_adversary_rejected"),
    (
        "live_W6_refresh_failure_plus_live_W7_destruction_then_sealed_resolver_signature",
        "live_W6_refresh_failure_plus_live_W7_destruction_then_sealed_resolver_signature",
        "undeclared_canonical_input_rejected_by_signature",
    ),
    ("canonical_records_signature", "canonical_records_signature", "undeclared_canonical_input_rejected_by_signature"),
    (
        "guard_open_control_and_live_W8_exact_canonical_commit",
        "phase3_physical_harness_protocol_after_exact_canonical_commit",
        "guard_open_commit_terminal_protocol_invalid",
    ),
    ("verify_current_head_observation", "head_observation", "head_observation_mismatch"),
    ("PhysicalCurrentHeadGuard", "physical_guard_transition", "refresh_before_durable_stale_open"),
    ("PhysicalCurrentHeadGuard.assert_refresh_eligible", "PhysicalCurrentHeadGuard.assert_refresh_eligible", "live_or_bound_adversary_rejected"),
    ("validate_physical_observation", "live_world_actor_enumeration", "nonlive_observation_source"),
    ("validate_projection", "projection_verification", "projection_matrix_mismatch"),
    ("two_live_W5_adapter_refreshes_and_H1_projection_comparison", "two_live_W5_adapter_refreshes_and_H1_projection_comparison", "live_or_bound_adversary_rejected"),
    ("validate_materialization_receipt", "process_binding_identity_verification", "receipt_binding_mismatch"),
    ("two_fresh_live_router_processes", "two_fresh_live_router_processes", "live_or_bound_adversary_rejected"),
    ("live_W6_corrupt_receipt_bundle_to_UE_adapter", "live_W6_corrupt_receipt_bundle_to_UE_adapter", "live_or_bound_adversary_rejected"),
    ("ASimultaneousPhysicalDomainCommandRouter::HandleLine", "ASimultaneousPhysicalDomainCommandRouter::HandleLine", "live_or_bound_adversary_rejected"),
    (
        "canonical_records_and_canonical_transition_run_signatures",
        "canonical_records_and_canonical_transition_run_signatures",
        "guard_and_head_arguments_rejected_by_signature",
    ),
    ("head_disposition", "disposition", "synchronized_prerequisite_missing"),
    ("validate_physical_observation", "live_world_actor_enumeration", "nonlive_observation_source"),
    (
        "live_W1_probe_observation_mutation_rejections_and_24_live_probe_faults",
        "live_W1_probe_observation_mutation_rejections_and_24_live_probe_faults",
        "live_or_bound_adversary_rejected",
    ),
    ("ASimultaneousPhysicalDomainCommandRouter::HandleLine", "ASimultaneousPhysicalDomainCommandRouter::HandleLine", "live_or_bound_adversary_rejected"),
    ("head_disposition", "disposition", "synchronized_prerequisite_missing"),
    ("require_physical_capability", "current_head_authority_guard", "current_head_materialization_claim_disabled"),
    ("ASimultaneousPhysicalDomainCommandRouter::HandleLine", "ASimultaneousPhysicalDomainCommandRouter::HandleLine", "live_or_bound_adversary_rejected"),
)


AUTHORITY_DESCRIPTION_INPUTS = {
    1: "H0 receipt claims H1 with H0 bytes",
    2: "H0 projection claims H1",
    3: "H0 cache publishes current receipt",
    4: "H0 scheduler capability against H1",
    5: "H0 mutation capability against H1",
    6: "stale diagnostic relabeled synchronized",
    7: "stale available route claimed current",
    8: "local state rewrites canonical route",
    9: "local state constructs competing successor",
    10: "other-domain state used as head oracle",
    13: "shared route omitted",
    14: "projection supplies route access",
    15: "replacement process claims original binding",
    20: "bad head observation reopens eligibility",
    21: "publication failure does not fail closed",
    23: "observation derived from domain",
    24: "retained scalar selects H1 fact",
    26: "PID reuse accepted as liveness",
    31: "receipt-only rebind accepted",
    32: "probe derives result from adapter data",
    35: "synchronized disposition lacks prerequisites",
    36: "non-synchronized claim enabled",
}


AUTHORITY_CASE_12_REDIRECTED_INPUTS = [
    {
        "actual_validation_path": "validate_projection",
        "canonical_H1_unchanged": True,
        "canonical_authority_acquired": False,
        "case_id": 11,
        "description": "physical order selects canonical outcome",
        "reason_code": "projection_matrix_mismatch",
        "rejected": True,
        "rejection_stage": "projection_verification",
    },
    {
        "actual_validation_path": "validate_projection",
        "canonical_H1_unchanged": True,
        "canonical_authority_acquired": False,
        "case_id": 12,
        "description": "projection site or route redirected",
        "reason_code": "projection_matrix_mismatch",
        "rejected": True,
        "rejection_stage": "projection_verification",
    },
]


def artifact_paths() -> tuple[str, ...]:
    return tuple(
        f"proof_kernel/SimultaneousPhysicalDomainsProofRecords/{name}"
        for name in ARTIFACT_NAMES
    )


def release_paths() -> tuple[str, ...]:
    paths = NON_ARTIFACT_MEMBERS + artifact_paths()
    if len(NON_ARTIFACT_MEMBERS) != 67 or len(paths) != 111 or len(set(paths)) != 111:
        raise AssertionError("frozen 44 + 67 = 111 member contract drift")
    return tuple(sorted(paths, key=lambda value: value.encode("utf-8")))


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _strict_member(path: Path) -> None:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"release member is not one regular non-symlink file: {path}")
    try:
        path.resolve(strict=True).relative_to(ROOT.resolve(strict=True))
    except ValueError as exc:
        raise ValueError(f"release member realpath escapes repository: {path}") from exc


def _load(name: str) -> dict[str, Any]:
    path = RECORDS / name
    raw = path.read_bytes()
    value = strict_load_stored_json(raw)
    if not isinstance(value, dict):
        raise ValueError(f"artifact is not an object: {name}")
    return value


def _runtime_input_audit() -> dict[str, Any]:
    global _RUNTIME_INPUT_AUDIT_CACHE
    if _RUNTIME_INPUT_AUDIT_CACHE is None:
        _RUNTIME_INPUT_AUDIT_CACHE = _load(
            "simultaneous_physical_domains_proof_semantic_input_audit.json"
        )
    return _RUNTIME_INPUT_AUDIT_CACHE


def _expect_equal(name: str, expected: Mapping[str, Any]) -> None:
    actual = _load(name)
    if stored_json_bytes(actual) != stored_json_bytes(dict(expected)):
        raise ValueError(f"deterministic artifact regeneration mismatch: {name}")


def _verify_primary(order: str) -> dict[str, Any]:
    prefix = "physical_W1" if order == "W1" else "physical_W2"
    witness_name = f"{prefix}_{'a_then_b' if order == 'W1' else 'b_then_a'}_witness.json"
    witness = _load(witness_name)
    expected_witness_id = "w1_a_then_b" if order == "W1" else "w2_b_then_a"
    if witness.get("witness_id") != expected_witness_id or witness.get("launch_count") != 2 or witness.get("replacement_spawn_count") != 0:
        raise ValueError(f"{order} launch/binding witness drift")
    expected_order = ("domain_A", "domain_B") if order == "W1" else ("domain_B", "domain_A")
    command_order = [
        role for role in expected_order
        if witness["domains"][role]["stdin_commands"][2]["operation"] == "refresh_once"
    ]
    if tuple(command_order) != expected_order:
        raise ValueError(f"{order} refresh command order drift")
    for role in DOMAIN_ROLES:
        binding = witness["domains"][role]["binding"]
        h0_receipt = _load(f"{prefix}_{role}_H0_materialization_receipt.json")
        h0_observation = _load(f"{prefix}_{role}_H0_observation.json")
        h1_receipt = _load(f"{prefix}_{role}_H1_materialization_receipt.json")
        h1_observation = _load(f"{prefix}_{role}_H1_observation.json")
        validate_materialization_receipt(h0_receipt, binding)
        validate_materialization_receipt(h1_receipt, binding)
        validate_physical_observation(
            h0_observation, domain_role=role, head_role="H0", binding=binding,
            inspection_id="launch_physical_0001",
        )
        validate_physical_observation(
            h1_observation, domain_role=role, head_role="H1", binding=binding,
            inspection_id="refresh_physical_0001",
        )
        if h0_receipt != witness["launch_receipts"][role] or h1_receipt != witness["refresh_receipts"][role]:
            raise ValueError(f"{order}/{role} detached receipt does not match witness embedding")
        if h0_observation != witness["launch_observations"][role] or h1_observation != witness["refresh_observations"][role]:
            raise ValueError(f"{order}/{role} detached physical observation does not match witness")
        commands = witness["domains"][role]["stdin_commands"]
        if [command["operation"] for command in commands] != [
            "bind_process_once", "inspect_published_route_once", "refresh_once", "inspect_published_route_once"
        ]:
            raise ValueError(f"{order}/{role} command sequence drift")
        if witness["domains"][role]["head_observation_visible_to_unreal"] or witness["domains"][role]["physical_guard_visible_to_unreal"]:
            raise ValueError(f"{order}/{role} hidden harness input reached Unreal")
        if witness["domains"][role]["refresh_input_inventory_before"] != witness["domains"][role]["refresh_input_inventory_after"]:
            raise ValueError(f"{order}/{role} refresh input changed during read")
    liveness = _load(f"{prefix}_liveness_witness.json")
    if (
        liveness.get("required_checkpoints") != ["L0", "L1", "L2", "L3", "L4A", "L4B"]
        or liveness.get("observed_checkpoints") != ["L0", "L1", "L2", "L3", "L4A", "L4B"]
        or not liveness.get("pids_distinct")
        or not liveness.get("process_start_pairs_distinct")
        or not liveness.get("same_original_binding_at_all_checkpoints")
        or liveness.get("launch_count") != 2
        or liveness.get("replacement_spawn_count") != 0
        or not liveness.get("uninterrupted_simultaneous_liveness_proven")
    ):
        raise ValueError(f"{order} uninterrupted simultaneous liveness failed")
    return witness


def _verify_canonical_relation(value: Any, expected_relation: str) -> None:
    r0, _, r1 = canonical_records()
    before_record = r0 if expected_relation in ("unchanged_H0", "exact_H0_to_H1") else r1
    after_record = r1 if expected_relation in ("unchanged_H1", "exact_H0_to_H1") else r0
    validate_measured_canonical_relation(
        value,
        before_record=before_record,
        after_record=after_record,
        expected_relation=expected_relation,
    )


def _verify_w3_payload(w3: Mapping[str, Any]) -> None:
    samples = w3.get("observed_domain_samples")
    if not isinstance(samples, dict) or set(samples) != set(DOMAIN_ROLES):
        raise ValueError("W3 exact domain sample set drift")
    for role in DOMAIN_ROLES:
        sample = samples[role]
        binding = sample.get("process_binding")
        observation = sample.get("exact_local_step_observation")
        if not isinstance(binding, dict) or not isinstance(observation, dict):
            raise ValueError("W3 lacks a process-bound exact local-step observation")
        validate_local_step_observation(observation, binding=binding)
        if (
            sample.get("exact_local_step_command", {}).get("operation")
            != "execute_nonconsequential_step_once"
            or sample.get("stdin_command_count_delta") != 1
            or sample.get("structured_local_step_observation_count_delta") != 1
            or sample.get("structured_authority_object_count_delta") != 0
            or sample.get("accepted_represented_hash_before_after") != [H0, H0]
        ):
            raise ValueError("W3 exact local-step execution law drift")
    _verify_canonical_relation(w3.get("canonical_before_after_measurement"), "unchanged_H1")
    if not all((
        w3.get("canonical_R1_raw_sha256_before_after") == [D1, D1],
        w3.get("current_head_receipt_count_delta") == 0,
        w3.get("canonical_evidence_count_delta") == 0,
        w3.get("canonical_scheduling_count_delta") == 0,
        w3.get("canonical_mutation_count_delta") == 0,
        w3.get("observed_live_UE_execution_in_both_original_processes") is True,
        w3.get("cpu_evidence_role") == "supplemental_only",
    )):
        raise ValueError("W3 stale quarantine drift")


def _verify_fault_result(
    result: Mapping[str, Any],
    command: Mapping[str, Any],
    binding: Mapping[str, Any],
) -> None:
    required = {
        "result_schema", "proof_scenario", "domain_role",
        "operational_process_instance_id", "process_binding_raw_sha256",
        "executable_raw_sha256", "fault_run_id", "fault_surface",
        "fault_stage", "fault_edge", "target_head_role", "boundary_entered",
        "boundary_completed", "local_publication_state", "represented_hash_if_known",
        "materialization_receipt_outcome", "physical_observation_outcome", "reason_code",
    }
    if set(result) != required:
        raise ValueError("live fault result exact member set drift")
    if (
        result.get("result_schema") != "SimultaneousPhysicalDomainInjectedFaultResult.v1"
        or result.get("fault_run_id") != command.get("fault_run_id")
        or result.get("fault_surface") != command.get("fault_surface")
        or result.get("fault_stage") != command.get("fault_stage")
        or result.get("fault_edge") != command.get("fault_edge")
        or result.get("target_head_role") != command.get("target_head_role")
        or result.get("domain_role") != binding.get("domain_role")
        or result.get("executable_raw_sha256") != binding.get("executable_raw_sha256")
        or result.get("process_binding_raw_sha256") != sha256_value(dict(binding))
        or result.get("boundary_entered") is not True
        or result.get("boundary_completed") is not (command.get("fault_edge") in ("after", "at"))
        or result.get("reason_code") != (
            f"injected_fault/{command.get('fault_surface')}/"
            f"{command.get('fault_stage')}/{command.get('fault_edge')}"
        )
    ):
        raise ValueError("live fault result is not bound to its command/process/boundary")


def _is_sha256_text(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _validated_process_binding(
    value: Any,
    *,
    expected_role: str,
    expected_witness_id: str,
) -> tuple[dict[str, Any], str, str, tuple[int, int, int]]:
    if not isinstance(value, dict):
        raise ValueError("process binding evidence is absent")
    raw = dict(value)
    if raw.pop("binding_schema", None) != "SimultaneousPhysicalDomainProcessBinding.v1":
        raise ValueError("process binding schema drift")
    validated = process_binding(raw)
    if (
        validated != value
        or value.get("domain_role") != expected_role
        or value.get("witness_id") != expected_witness_id
    ):
        raise ValueError("process binding identity/role/witness drift")
    instance_id = operational_process_instance_id(value)
    binding_digest = sha256_value(value)
    start = value["macos_process_start"]
    birth = (value["pid"], start["seconds"], start["microseconds"])
    return validated, instance_id, binding_digest, birth


def _path_is_within(child: Any, parent: Any) -> bool:
    if not isinstance(child, str) or not isinstance(parent, str):
        return False
    try:
        return os.path.commonpath((child, parent)) == os.path.normpath(parent)
    except ValueError:
        return False


def _verify_compact_runtime_provenance(
    evidence: Mapping[str, Any],
    *,
    binding: Mapping[str, Any],
    instance_id: str,
    binding_digest: str,
    input_audit: Mapping[str, Any],
) -> None:
    compact = evidence.get("runtime_provenance")
    compact_required = {
        "evidence_schema", "child_report_without_loaded_image_identities",
        "loaded_image_inventory_reference",
        "reconstructed_child_report_raw_sha256",
    }
    if not isinstance(compact, dict) or set(compact) != compact_required:
        raise ValueError("compact runtime provenance exact member set drift")
    reference = compact.get("loaded_image_inventory_reference")
    if not isinstance(reference, dict) or set(reference) != {
        "catalog_owner_artifact", "catalog_raw_sha256", "loaded_image_count",
    }:
        raise ValueError("loaded-image catalog reference drift")
    catalog = input_audit.get("runtime_loaded_image_inventory_catalog")
    catalog_digest = reference.get("catalog_raw_sha256")
    if (
        compact.get("evidence_schema")
        != "SimultaneousPhysicalDomainCompactRuntimeProvenance.v1"
        or reference.get("catalog_owner_artifact")
        != "simultaneous_physical_domains_proof_semantic_input_audit.json"
        or not isinstance(catalog, dict)
        or not _is_sha256_text(catalog_digest)
        or catalog_digest not in catalog
    ):
        raise ValueError("loaded-image catalog reference is not resolvable")
    loaded_images = catalog[catalog_digest]
    if (
        not isinstance(loaded_images, list)
        or reference.get("loaded_image_count") != len(loaded_images)
        or sha256_value(loaded_images) != catalog_digest
    ):
        raise ValueError("loaded-image catalog reference digest/count mismatch")
    child_without_images = compact.get("child_report_without_loaded_image_identities")
    if not isinstance(child_without_images, dict):
        raise ValueError("compact runtime provenance child report is absent")
    report = copy.deepcopy(child_without_images)
    report["loaded_image_identities"] = copy.deepcopy(loaded_images)
    if (
        not _is_sha256_text(compact.get("reconstructed_child_report_raw_sha256"))
        or sha256_value(report)
        != compact.get("reconstructed_child_report_raw_sha256")
    ):
        raise ValueError("compact runtime provenance reconstruction digest mismatch")

    report_required = {
        "audit_schema", "binding_verification_rows",
        "captured_before_first_materialization", "descriptor_kernel_identities",
        "domain_role", "entry_map_file_identity",
        "initial_world_actor_class_inventory", "loaded_image_identities",
        "observed_inherited_descriptor_map", "observed_launch_argv",
        "observed_process_binding", "operational_process_instance_id",
        "process_binding_raw_sha256", "project_config_and_module_inventory",
        "proof_scenario", "redacted_environment_audit",
    }
    expected_rows = [
        {
            "field": field_name,
            "verification_mode": BINDING_VERIFICATION_MODES.get(
                field_name, "independent_process_observation"
            ),
            "matched": True,
        }
        for field_name in PROCESS_BINDING_FIELDS
    ]
    if (
        set(report) != report_required
        or report.get("audit_schema")
        != "SimultaneousPhysicalDomainRuntimeProvenance.v1"
        or report.get("proof_scenario") != binding["proof_scenario"]
        or report.get("captured_before_first_materialization") is not True
        or report.get("domain_role") != binding["domain_role"]
        or report.get("operational_process_instance_id") != instance_id
        or report.get("process_binding_raw_sha256") != binding_digest
        or report.get("observed_process_binding") != binding
        or report.get("binding_verification_rows") != expected_rows
        or report.get("observed_launch_argv") != evidence.get("launch_argv")
        or report.get("redacted_environment_audit")
        != evidence.get("launch_environment_audit")
        or report.get("observed_inherited_descriptor_map")
        != evidence.get("inherited_descriptor_map")
        or report.get("descriptor_kernel_identities")
        != evidence.get("spawn_descriptor_kernel_identities")
    ):
        raise ValueError("runtime provenance is not exact and process-bound")

    descriptor_rows = report["descriptor_kernel_identities"]
    expected_descriptor_modes = {
        0: "read_only", 1: "write_only", 2: "write_only",
    }
    if not isinstance(descriptor_rows, list) or len(descriptor_rows) != 3:
        raise ValueError("runtime descriptor kernel identity set drift")
    for row, expected_fd in zip(descriptor_rows, (0, 1, 2)):
        if (
            not isinstance(row, dict)
            or set(row) != {"access_mode", "device", "fd", "file_type", "inode"}
            or row.get("fd") != expected_fd
            or row.get("file_type") != "fifo"
            or row.get("access_mode") != expected_descriptor_modes[expected_fd]
            or not isinstance(row.get("device"), str)
            or not isinstance(row.get("inode"), str)
        ):
            raise ValueError("runtime descriptor kernel identity row drift")

    project_inventory = report.get("project_config_and_module_inventory")
    project_members = (
        project_inventory.get("members")
        if isinstance(project_inventory, dict) else None
    )
    if (
        not isinstance(project_inventory, dict)
        or set(project_inventory) != {"inventory_schema", "members"}
        or project_inventory.get("inventory_schema")
        != "SimultaneousPhysicalDomainProjectModuleInventory.v1"
        or not isinstance(project_members, list)
        or len(project_members) != 5
        or any(
            not isinstance(row, dict)
            or set(row) != {"raw_sha256", "realpath"}
            or not isinstance(row.get("realpath"), str)
            or not _is_sha256_text(row.get("raw_sha256"))
            for row in project_members
        )
        or sha256_value(project_inventory)
        != binding["project_config_and_module_inventory_raw_sha256"]
        or binding["project_realpath"]
        not in {row["realpath"] for row in project_members}
        or not any(
            row["realpath"].endswith(
                "/Binaries/Mac/libUnrealEditor-CityMaterializationProof.dylib"
            )
            for row in project_members
        )
    ):
        raise ValueError("runtime project/config/module inventory drift")

    entry_map = report.get("entry_map_file_identity")
    if (
        not isinstance(entry_map, dict)
        or set(entry_map) != {"package_identity", "raw_sha256", "realpath"}
        or entry_map.get("package_identity") != binding["entry_map_package_identity"]
        or not isinstance(entry_map.get("realpath"), str)
        or not entry_map["realpath"].endswith("/Content/Maps/Entry.umap")
        or not _is_sha256_text(entry_map.get("raw_sha256"))
    ):
        raise ValueError("runtime entry-map file identity drift")

    actor_rows = report.get("initial_world_actor_class_inventory")
    if not isinstance(actor_rows, list) or not actor_rows:
        raise ValueError("runtime initial actor inventory is absent")
    actor_classes = []
    for row in actor_rows:
        if (
            not isinstance(row, dict)
            or set(row) != {"actor_count", "class_path"}
            or type(row.get("actor_count")) is not int
            or row["actor_count"] <= 0
            or not isinstance(row.get("class_path"), str)
        ):
            raise ValueError("runtime initial actor inventory row drift")
        actor_classes.append(row["class_path"])
    prohibited = {
        "/Script/CityMaterializationProof.SimultaneousPhysicalDomainProofAdapter",
        "/Script/CityMaterializationProof.SimultaneousPhysicalDomainRepresentationActor",
        "/Script/CityMaterializationProof.SimultaneousPhysicalRebindProbe",
    }
    if (
        actor_classes != sorted(actor_classes, key=str.casefold)
        or len(actor_classes) != len(set(actor_classes))
        or "/Script/CityMaterializationProof.CityProofGameMode" not in actor_classes
        or "/Script/CityMaterializationProof.SimultaneousPhysicalDomainCommandRouter"
        not in actor_classes
        or any(name in prohibited or name.endswith("Pawn") for name in actor_classes)
    ):
        raise ValueError("runtime initial actor inventory is not pre-materialization")

    file_catalog = input_audit.get("runtime_loaded_image_file_catalog")
    if not isinstance(file_catalog, list):
        raise ValueError("runtime loaded-image file catalog is absent")
    file_by_path = {
        row.get("realpath"): row for row in file_catalog if isinstance(row, dict)
    }
    filesystem_catalog = []
    seen_images: set[tuple[str, str]] = set()
    filesystem_count = shared_cache_count = 0
    executable_seen = module_seen = False
    for row in loaded_images:
        if not isinstance(row, dict) or set(row) != {
            "filesystem_regular_file", "mach_o_uuid", "path_resolution",
            "realpath", "reported_path",
        }:
            raise ValueError("runtime loaded-image identity row drift")
        realpath = row.get("realpath")
        uuid = row.get("mach_o_uuid")
        image_key = (realpath, uuid)
        if (
            not isinstance(realpath, str) or not realpath.startswith("/")
            or not isinstance(row.get("reported_path"), str)
            or not isinstance(uuid, str) or len(uuid) != 36
            or uuid != uuid.lower()
            or tuple(index for index, char in enumerate(uuid) if char == "-")
            != (8, 13, 18, 23)
            or any(char not in "0123456789abcdef-" for char in uuid)
            or image_key in seen_images
        ):
            raise ValueError("runtime loaded-image path/UUID identity drift")
        seen_images.add(image_key)
        if row.get("filesystem_regular_file") is True:
            identity = file_by_path.get(realpath)
            if (
                row.get("path_resolution") != "filesystem_realpath"
                or not isinstance(identity, dict)
                or uuid not in identity.get("mach_o_uuids", [])
            ):
                raise ValueError("runtime filesystem image lacks catalog identity")
            filesystem_catalog.append(copy.deepcopy(identity))
            filesystem_count += 1
        elif row.get("filesystem_regular_file") is False:
            if row.get("path_resolution") != "dyld_shared_cache_logical_path":
                raise ValueError("runtime shared-cache image classification drift")
            shared_cache_count += 1
        else:
            raise ValueError("runtime image filesystem classification is not boolean")
        executable_seen |= realpath == binding["executable_realpath"]
        module_seen |= realpath.endswith(
            "/Binaries/Mac/libUnrealEditor-CityMaterializationProof.dylib"
        )
    if not executable_seen or not module_seen or not filesystem_count or not shared_cache_count:
        raise ValueError("runtime loaded-image inventory omits a required backing class")
    filesystem_catalog.sort(key=lambda row: row["realpath"])

    shared_cache = input_audit.get("dyld_shared_cache_inventory")
    validation = evidence.get("runtime_provenance_validation")
    expected_validation = {
        "validation_schema": "SimultaneousPhysicalDomainRuntimeProvenanceValidation.v1",
        "binding_field_count": len(PROCESS_BINDING_FIELDS),
        "all_binding_fields_exactly_matched": True,
        "compiled_constant_binding_field_count": 2,
        "child_visible_launch_identity_field_count": 6,
        "independent_process_observation_field_count": 14,
        "descriptor_kernel_identities_match_spawn_endpoints": True,
        "entry_map_file_independently_rehashed": True,
        "initial_actor_inventory_raw_sha256": sha256_value(actor_rows),
        "pre_materialization_phase3_actor_count": 0,
        "loaded_image_count": len(loaded_images),
        "filesystem_loaded_image_count": filesystem_count,
        "dyld_shared_cache_loaded_image_count": shared_cache_count,
        "loaded_image_inventory_raw_sha256": sha256_value(loaded_images),
        "filesystem_loaded_image_catalog_raw_sha256": sha256_value(
            filesystem_catalog
        ),
        "dyld_shared_cache_inventory_raw_sha256": (
            shared_cache.get("inventory_raw_sha256")
            if isinstance(shared_cache, dict) else None
        ),
        "runtime_provenance_raw_sha256": sha256_value(report),
        "proof_semantic_input": False,
    }
    if validation != expected_validation:
        raise ValueError("runtime provenance validation is not independently reproducible")


def _verify_runtime_input_trace(
    evidence: Mapping[str, Any],
    *,
    binding: Mapping[str, Any],
    instance_id: str,
    binding_digest: str,
) -> None:
    rows = evidence.get("runtime_input_trace")
    commands = evidence.get("stdin_commands")
    required = {
        "domain_role", "input_class", "metadata", "observed_raw_sha256",
        "operation", "operational_process_instance_id",
        "process_binding_raw_sha256", "proof_scenario", "sequence",
        "source_identity", "trace_schema",
    }
    if not isinstance(rows, list) or not rows or not isinstance(commands, list):
        raise ValueError("runtime input trace is absent")
    for index, row in enumerate(rows, start=1):
        if (
            not isinstance(row, dict) or set(row) != required
            or row.get("trace_schema")
            != "SimultaneousPhysicalDomainRuntimeInputTraceEvent.v1"
            or row.get("proof_scenario") != binding["proof_scenario"]
            or row.get("domain_role") != binding["domain_role"]
            or row.get("operational_process_instance_id") != instance_id
            or row.get("process_binding_raw_sha256") != binding_digest
            or row.get("sequence") != index
            or not _is_sha256_text(row.get("observed_raw_sha256"))
            or not isinstance(row.get("metadata"), dict)
        ):
            raise ValueError("runtime input trace sequence/process binding drift")
    command_rows = [row for row in rows if row["input_class"] == "stdin_command"]
    if len(command_rows) != len(commands):
        raise ValueError("runtime input trace omits a stdin command")
    for command, row in zip(commands, command_rows):
        expected_hash = hashlib.sha256(
            (canonical_json(command) + "\n").encode("utf-8")
        ).hexdigest()
        if (
            row["operation"] != "canonical_line_read"
            or row["source_identity"] != "fd:0"
            or row["observed_raw_sha256"] != expected_hash
            or row["metadata"] != {
                "command_schema": command["command_schema"],
                "descriptor": "fd_0_original_control_pipe_read_endpoint",
            }
        ):
            raise ValueError("runtime stdin trace is not bound to exact command bytes")

    allowed_pairs = {
        ("stdin_command", "canonical_line_read"),
        ("bundle_directory", "exact_member_inventory"),
        ("bundle_file", "opened_descriptor_raw_read"),
        ("engine_asset_package", "LoadObject_dependency"),
        ("live_world_state", "independent_probe_read"),
    }
    directory_count = file_count = engine_asset_count = live_world_count = 0
    process_root = binding["process_root_realpath"]
    for row in rows:
        pair = (row["input_class"], row["operation"])
        if pair not in allowed_pairs:
            raise ValueError("runtime input trace contains an undeclared operation")
        metadata = row["metadata"]
        if row["input_class"] == "bundle_directory":
            names = metadata.get("sorted_member_names")
            if (
                not _path_is_within(row["source_identity"], process_root)
                or not isinstance(names, list) or names != sorted(names)
                or row["observed_raw_sha256"]
                != hashlib.sha256(canonical_json(names).encode("utf-8")).hexdigest()
            ):
                raise ValueError("runtime bundle-directory trace drift")
            directory_count += 1
        elif row["input_class"] == "bundle_file":
            if (
                not _path_is_within(row["source_identity"], process_root)
                or metadata.get("descriptor_access") != "read_only_no_follow"
                or not isinstance(metadata.get("device"), str)
                or not isinstance(metadata.get("inode"), str)
                or type(metadata.get("size")) is not int
                or metadata["size"] <= 0
            ):
                raise ValueError("runtime opened bundle-file trace drift")
            file_count += 1
        elif row["input_class"] == "engine_asset_package":
            if (
                metadata.get("package_identity") not in (
                    "/Engine/BasicShapes/Cube",
                    "/Engine/BasicShapes/BasicShapeMaterial",
                )
                or not isinstance(row["source_identity"], str)
                or not row["source_identity"].startswith("/")
            ):
                raise ValueError("runtime engine asset trace drift")
            engine_asset_count += 1
        elif row["input_class"] == "live_world_state":
            stage = metadata.get("read_stage")
            if (
                row["source_identity"] != stage
                or stage not in (
                    "player_and_input_inventory",
                    "representation_actor_enumeration",
                    "mesh_label_component_state",
                )
                or not isinstance(metadata.get("inspection_id"), str)
            ):
                raise ValueError("runtime live-world trace drift")
            live_world_count += 1
    expected_live_world: list[tuple[str, str]] = []
    valid_inspection_count = 0
    full_inspection_count = 0
    fault_prefix_inspection_count = 0
    armed_physical_stage: str | None = None
    for command in commands:
        if (
            command.get("operation") == "arm_exact_fault_once"
            and command.get("fault_surface") == "physical_observation"
            and command.get("fault_stage")
            in PHYSICAL_FAULT_LIVE_WORLD_PREFIX_COUNTS
        ):
            armed_physical_stage = command["fault_stage"]
            continue
        if command.get("operation") != "inspect_published_route_once":
            continue
        inspection_id = command.get("inspection_id")
        try:
            exact_inspection = inspection_invocation(
                binding["domain_role"], inspection_id
            )
        except Exception:
            continue
        if command != exact_inspection:
            continue
        valid_inspection_count += 1
        stage_count = len(LIVE_WORLD_READ_STAGES)
        if armed_physical_stage is not None:
            stage_count = PHYSICAL_FAULT_LIVE_WORLD_PREFIX_COUNTS[
                armed_physical_stage
            ]
            fault_prefix_inspection_count += 1
            armed_physical_stage = None
        else:
            full_inspection_count += 1
        expected_live_world.extend(
            (inspection_id, stage) for stage in LIVE_WORLD_READ_STAGES[:stage_count]
        )
    observed_live_world = [
        (row["metadata"]["inspection_id"], row["metadata"]["read_stage"])
        for row in rows if row["input_class"] == "live_world_state"
    ]
    if (
        directory_count < 1 or file_count < 3 or engine_asset_count < 2
        or observed_live_world != expected_live_world
    ):
        raise ValueError("runtime trace omits a required launch input class")
    expected_validation = {
        "validation_schema": "SimultaneousPhysicalDomainRuntimeInputTraceValidation.v1",
        "event_count": len(rows),
        "last_sequence": rows[-1]["sequence"],
        "stdin_command_event_count": len(command_rows),
        "bundle_directory_event_count": directory_count,
        "bundle_file_event_count": file_count,
        "engine_asset_event_count": engine_asset_count,
        "live_world_event_count": live_world_count,
        "valid_inspection_command_count": valid_inspection_count,
        "full_three_stage_inspection_count": full_inspection_count,
        "fault_prefix_inspection_count": fault_prefix_inspection_count,
        "exact_live_world_stage_sequences_matched": True,
        "all_events_contiguous_and_process_bound": True,
        "all_stdin_commands_byte_bound": True,
        "alternate_runtime_input_path_observed": False,
        "runtime_input_trace_raw_sha256": sha256_value(rows),
    }
    if evidence.get("runtime_input_trace_validation") != expected_validation:
        raise ValueError("runtime input trace validation is not independently reproducible")


def _verify_domain_evidence(
    value: Any,
    *,
    expected_role: str,
    expected_witness_id: str,
    input_audit: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], str, str, tuple[int, int, int]]:
    required = {
        "binding", "binding_command", "head_observation_visible_to_unreal",
        "inherited_descriptor_map", "launch_argv", "launch_environment_audit",
        "launch_input_inventory", "other_domain_root_visible_to_unreal",
        "physical_guard_visible_to_unreal", "refresh_input_inventory_after",
        "refresh_input_inventory_before", "runtime_input_trace",
        "runtime_input_trace_validation", "runtime_provenance",
        "runtime_provenance_validation", "spawn_descriptor_kernel_identities",
        "stdin_commands",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError("runtime domain evidence exact member set drift")
    binding, instance_id, binding_digest, birth = _validated_process_binding(
        value["binding"],
        expected_role=expected_role,
        expected_witness_id=expected_witness_id,
    )
    if (
        value.get("binding_command") != bind_invocation(binding)
        or hashlib.sha256(canonical_json(value.get("launch_argv")).encode("utf-8")).hexdigest()
        != binding.get("launch_argv_raw_sha256")
        or sha256_value(value.get("launch_environment_audit"))
        != binding.get("launch_environment_audit_raw_sha256")
        or sha256_value(value.get("inherited_descriptor_map"))
        != binding.get("inherited_descriptor_map_raw_sha256")
        or value.get("head_observation_visible_to_unreal") is not False
        or value.get("physical_guard_visible_to_unreal") is not False
        or value.get("other_domain_root_visible_to_unreal") is not False
        or not isinstance(value.get("stdin_commands"), list)
    ):
        raise ValueError("runtime domain evidence is not bound to its process/input closure")
    audit = _runtime_input_audit() if input_audit is None else input_audit
    _verify_compact_runtime_provenance(
        value,
        binding=binding,
        instance_id=instance_id,
        binding_digest=binding_digest,
        input_audit=audit,
    )
    _verify_runtime_input_trace(
        value,
        binding=binding,
        instance_id=instance_id,
        binding_digest=binding_digest,
    )
    return binding, instance_id, binding_digest, birth


def _verify_liveness_sample(
    value: Any,
    *,
    expected_role: str,
    expected_checkpoint: str | None,
    binding: Mapping[str, Any] | None = None,
    instance_id: str | None = None,
) -> tuple[str, str, tuple[int, int, int]]:
    required = {
        "checkpoint", "control_pipe_unexpected_eof", "direct_child_ppid_matches_harness",
        "domain_role", "macos_process_start", "operational_process_instance_id",
        "original_child_handle_exit_observed", "pid", "process_binding_raw_sha256",
        "replacement_spawn_count", "structured_output_pipe_unexpected_eof",
        "wait_status_available",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError("process liveness evidence exact member set drift")
    start = value.get("macos_process_start")
    if (
        value.get("domain_role") != expected_role
        or (expected_checkpoint is not None and value.get("checkpoint") != expected_checkpoint)
        or not isinstance(value.get("checkpoint"), str)
        or not value.get("checkpoint")
        or type(value.get("pid")) is not int
        or value["pid"] <= 0
        or not isinstance(start, dict)
        or set(start) != {"seconds", "microseconds"}
        or type(start.get("seconds")) is not int
        or type(start.get("microseconds")) is not int
        or start["seconds"] < 0
        or not 0 <= start["microseconds"] <= 999999
        or not _is_sha256_text(value.get("operational_process_instance_id"))
        or not _is_sha256_text(value.get("process_binding_raw_sha256"))
        or value.get("direct_child_ppid_matches_harness") is not True
        or value.get("original_child_handle_exit_observed") is not False
        or value.get("control_pipe_unexpected_eof") is not False
        or value.get("structured_output_pipe_unexpected_eof") is not False
        or value.get("replacement_spawn_count") != 0
        or value.get("wait_status_available") is not False
    ):
        raise ValueError("process liveness evidence is not a live original process")
    if binding is not None:
        expected_instance = operational_process_instance_id(binding)
        if (
            value["pid"] != binding.get("pid")
            or start != binding.get("macos_process_start")
            or value["operational_process_instance_id"] != expected_instance
            or value["process_binding_raw_sha256"] != sha256_value(binding)
            or (instance_id is not None and instance_id != expected_instance)
        ):
            raise ValueError("process liveness evidence does not bind the declared process")
    birth = (value["pid"], start["seconds"], start["microseconds"])
    return (
        value["operational_process_instance_id"],
        value["process_binding_raw_sha256"],
        birth,
    )


def _verify_fault_case_binding(
    case: Mapping[str, Any],
    *,
    surface: str,
    stage: str,
    edge: str,
    head_role: str,
    result_key: str,
    owner_key: str,
    expected_owner: str,
) -> dict[str, Any]:
    command = case.get("fault_arm_command")
    receipt = case.get("fault_arm_receipt")
    result = case.get(result_key)
    expected_command = fault_arm_invocation(
        surface=surface,
        stage=stage,
        edge=edge,
        head_role=head_role,
    )
    expected_run_id = expected_command["fault_run_id"]
    expected_case_schema = (
        "SimultaneousPhysicalDomainsLiveRefreshFaultCase.v1"
        if surface == "refresh"
        else "SimultaneousPhysicalDomainsLivePhysicalObservationFaultCase.v1"
    )
    expected_input_origin = (
        "fresh_original_UE_process_exact_H1_bundle_and_stdin_fault_arm"
        if surface == "refresh"
        else "fresh_original_UE_process_live_representation_and_exact_stdin_fault_arm"
    )
    if (
        not isinstance(command, dict)
        or command != expected_command
        or case.get("proof_scenario") != "simultaneous-physical-domains-v1.1"
        or case.get("case_schema") != expected_case_schema
        or case.get("input_origin") != expected_input_origin
        or case.get("fault_stage") != stage
        or case.get("fault_edge") != edge
        or case.get("fault_run_id") != expected_run_id
        or (surface == "physical_observation" and case.get("head_role") != head_role)
        or case.get(owner_key) != expected_owner
    ):
        raise ValueError("fault row label/owner is not bound to its exact command")

    target_evidence = case.get("target_domain_evidence")
    peer_evidence = case.get("peer_domain_evidence")
    target_binding, target_id, target_digest, target_birth = _verify_domain_evidence(
        target_evidence,
        expected_role="domain_A",
        expected_witness_id=("f_refresh_fault" if surface == "refresh" else "f_physical_observation_fault"),
    )
    peer_binding, peer_id, peer_digest, peer_birth = _verify_domain_evidence(
        peer_evidence,
        expected_role="domain_B",
        expected_witness_id=("f_refresh_fault" if surface == "refresh" else "f_physical_observation_fault"),
    )
    if (
        case.get("target_process_binding") != target_binding
        or case.get("target_executable_raw_sha256") != target_binding.get("executable_raw_sha256")
    ):
        raise ValueError("fault target row does not embed its exact process binding")

    target_commands = target_evidence["stdin_commands"]
    peer_commands = peer_evidence["stdin_commands"]
    expected_target_operations = (
        ["bind_process_once", "inspect_published_route_once", "arm_exact_fault_once", "refresh_once"]
        if surface == "refresh"
        else (
            ["bind_process_once", "arm_exact_fault_once", "inspect_published_route_once"]
            if head_role == "H0"
            else [
                "bind_process_once", "inspect_published_route_once", "refresh_once",
                "arm_exact_fault_once", "inspect_published_route_once",
            ]
        )
    )
    if (
        [member.get("operation") for member in target_commands] != expected_target_operations
        or target_commands.count(command) != 1
        or target_commands[0] != bind_invocation(target_binding)
        or [member.get("operation") for member in peer_commands]
        != ["bind_process_once", "inspect_published_route_once"]
        or peer_commands[0] != bind_invocation(peer_binding)
        or any(member.get("operation") == "arm_exact_fault_once" for member in peer_commands)
    ):
        raise ValueError("fault command is not bound to the exact target/peer stdin histories")

    if not isinstance(receipt, dict) or not isinstance(result, dict):
        raise ValueError("fault receipt/result evidence is absent")
    validate_fault_arm_receipt(receipt, command=command, binding=target_binding)
    _verify_fault_result(result, command, target_binding)
    peer_checkpoint = (
        f"refresh_fault/{stage}/{edge}/peer_alive"
        if surface == "refresh"
        else f"physical_observation_fault/{head_role}/{stage}/peer_alive"
    )
    _verify_liveness_sample(
        case.get("peer_original_process_alive"),
        expected_role="domain_B",
        expected_checkpoint=peer_checkpoint,
        binding=peer_binding,
        instance_id=peer_id,
    )
    return {
        "target_id": target_id,
        "target_digest": target_digest,
        "target_birth": target_birth,
        "peer_id": peer_id,
        "peer_digest": peer_digest,
        "peer_birth": peer_birth,
        "result_digest": sha256_value(result),
        "target_evidence_digest": sha256_value(target_evidence),
        "peer_evidence_digest": sha256_value(peer_evidence),
    }


def _verify_fresh_fault_matrix(rows: list[Mapping[str, Any]], *, label: str) -> None:
    count = len(rows)
    for key in (
        "target_id", "target_digest", "target_birth", "peer_id", "peer_digest",
        "peer_birth", "result_digest", "target_evidence_digest", "peer_evidence_digest",
    ):
        if len({row[key] for row in rows}) != count:
            raise ValueError(f"{label} reused matrix evidence: {key}")
    if (
        not {row["target_id"] for row in rows}.isdisjoint(row["peer_id"] for row in rows)
        or not {row["target_digest"] for row in rows}.isdisjoint(row["peer_digest"] for row in rows)
        or len({row["target_birth"] for row in rows} | {row["peer_birth"] for row in rows}) != count * 2
    ):
        raise ValueError(f"{label} target/peer process identity was reused")


def _verify_refresh_fault_payload(value: Mapping[str, Any]) -> None:
    if set(value) != {
        "all_fail_closed_without_canonical_effect", "all_faults_executed",
        "case_count", "cases", "execution_surface", "fault_edges", "fault_stages",
        "oracle_schema", "proof_scenario",
    }:
        raise ValueError("refresh fault matrix exact member set drift")
    cases = value.get("cases")
    expected_pairs = [(stage, edge) for stage in REFRESH_FAULT_STAGES for edge in ("before", "after")]
    actual_pairs = [(case.get("fault_stage"), case.get("fault_edge")) for case in cases or []]
    if (
        value.get("oracle_schema") != "SimultaneousPhysicalDomainsRefreshFaultAtomicity.v1"
        or value.get("proof_scenario") != "simultaneous-physical-domains-v1.1"
        or value.get("fault_stages") != list(REFRESH_FAULT_STAGES)
        or value.get("fault_edges") != ["before", "after"]
        or value.get("case_count") != 36
        or value.get("execution_surface") != "36_fresh_compiled_UE_adapter_or_router_boundaries"
        or actual_pairs != expected_pairs
        or value.get("all_faults_executed") is not True
        or value.get("all_fail_closed_without_canonical_effect") is not True
    ):
        raise ValueError("exact live refresh fault matrix drift")
    required_case_members = {
        "canonical_H1_unchanged", "canonical_before_after_measurement",
        "canonical_transition", "case_schema", "compiled_boundary_owner",
        "compiled_boundary_result", "emitted_materialization_receipt_not_accepted",
        "fault_arm_command", "fault_arm_receipt", "fault_edge", "fault_run_id",
        "fault_stage", "guard_machine", "head_publication", "input_origin",
        "launch_acceptance", "peer_domain_evidence", "peer_original_process_alive",
        "proof_scenario", "resulting_disposition", "retry_permitted",
        "target_domain_evidence", "target_executable_raw_sha256",
        "target_process_binding",
    }
    verified_rows: list[Mapping[str, Any]] = []
    for case in cases:
        if set(case) != required_case_members:
            raise ValueError("refresh fault row exact member set drift")
        binding = case.get("target_process_binding")
        command = case.get("fault_arm_command")
        arm_receipt = case.get("fault_arm_receipt")
        result = case.get("compiled_boundary_result")
        if not all(isinstance(member, dict) for member in (binding, command, arm_receipt, result)):
            raise ValueError("Python-only refresh fault row lacks compiled UE binding evidence")
        owner = (
            "ASimultaneousPhysicalDomainCommandRouter"
            if case["fault_stage"] in ("invocation_read", "materialization_receipt_emission")
            else "ASimultaneousPhysicalDomainProofAdapter"
        )
        verified_rows.append(_verify_fault_case_binding(
            case,
            surface="refresh",
            stage=case["fault_stage"],
            edge=case["fault_edge"],
            head_role="H1",
            result_key="compiled_boundary_result",
            owner_key="compiled_boundary_owner",
            expected_owner=owner,
        ))
        _verify_canonical_relation(case.get("canonical_before_after_measurement"), "unchanged_H1")
        if case.get("canonical_H1_unchanged") is not True:
            raise ValueError("refresh fault hard-coded/false canonical relation")
    _verify_fresh_fault_matrix(verified_rows, label="refresh fault")


def _verify_physical_fault_payload(value: Mapping[str, Any]) -> None:
    if set(value) != {
        "all_fail_closed_without_canonical_effect", "all_faults_executed", "cases",
        "execution_surface", "fault_stages", "head_role_case_count", "head_roles",
        "oracle_schema", "proof_scenario",
    }:
        raise ValueError("physical-observation fault matrix exact member set drift")
    cases = value.get("cases")
    expected_pairs = [(stage, head) for stage in PHYSICAL_OBSERVATION_FAULT_STAGES for head in ("H0", "H1")]
    actual_pairs = [(case.get("fault_stage"), case.get("head_role")) for case in cases or []]
    if (
        value.get("oracle_schema") != "SimultaneousPhysicalDomainsPhysicalObservationFaultAtomicity.v1"
        or value.get("proof_scenario") != "simultaneous-physical-domains-v1.1"
        or value.get("fault_stages") != list(PHYSICAL_OBSERVATION_FAULT_STAGES)
        or value.get("head_roles") != ["H0", "H1"]
        or value.get("head_role_case_count") != 24
        or value.get("execution_surface")
        != "24_fresh_live_UE_probe_router_or_exact_harness_crosscheck_boundaries"
        or actual_pairs != expected_pairs
        or value.get("all_faults_executed") is not True
        or value.get("all_fail_closed_without_canonical_effect") is not True
    ):
        raise ValueError("exact live physical-observation fault matrix drift")
    required_case_members = {
        "accepted_physical_observation", "boundary_result",
        "canonical_before_after_measurement", "canonical_transition", "canonical_unchanged",
        "case_schema", "compiled_or_harness_boundary_owner", "fault_arm_command",
        "fault_arm_receipt", "fault_edge", "fault_run_id", "fault_stage",
        "guard_machine", "head_publication", "head_role", "input_origin",
        "live_observation_emitted_but_not_accepted", "peer_domain_evidence",
        "peer_launch_acceptance", "peer_original_process_alive", "proof_scenario",
        "resulting_disposition", "target_domain_evidence", "target_executable_raw_sha256",
        "target_materialization_receipt", "target_process_binding",
    }
    verified_rows: list[Mapping[str, Any]] = []
    for case in cases:
        if set(case) != required_case_members:
            raise ValueError("physical-observation fault row exact member set drift")
        binding = case.get("target_process_binding")
        command = case.get("fault_arm_command")
        arm_receipt = case.get("fault_arm_receipt")
        result = case.get("boundary_result")
        if not all(isinstance(member, dict) for member in (binding, command, arm_receipt, result)):
            raise ValueError("Python-only observation fault row lacks original UE binding evidence")
        if case["fault_stage"] in ("inspection_invocation_read", "physical_observation_emission"):
            owner = "ASimultaneousPhysicalDomainCommandRouter"
        elif case["fault_stage"] == "harness_receipt_observation_head_cross_check":
            owner = "python_harness_receipt_observation_head_cross_check"
        else:
            owner = "ASimultaneousPhysicalRebindProbe"
        verified_rows.append(_verify_fault_case_binding(
            case,
            surface="physical_observation",
            stage=case["fault_stage"],
            edge="at",
            head_role=case["head_role"],
            result_key="boundary_result",
            owner_key="compiled_or_harness_boundary_owner",
            expected_owner=owner,
        ))
        _verify_canonical_relation(
            case.get("canonical_before_after_measurement"),
            "unchanged_H0" if case["head_role"] == "H0" else "unchanged_H1",
        )
        if case.get("accepted_physical_observation") is not None:
            raise ValueError("faulted physical observation was accepted")
    _verify_fresh_fault_matrix(verified_rows, label="physical-observation fault")


def _verify_live_authority_attack(
    value: Any,
    *,
    attack: str,
) -> dict[str, Any]:
    required = {
        "actual_command", "actual_validation_path", "attack",
        "canonical_before_after_measurement", "canonical_transition",
        "canonical_unchanged", "live_stdin_command_count_delta",
        "peer_alive_after_rejection", "peer_domain_evidence", "rejection",
        "target_alive_after_rejection", "target_domain_evidence",
        "target_executable_raw_sha256", "target_process_binding",
    }
    if not isinstance(value, dict) or set(value) != required or value.get("attack") != attack:
        raise ValueError(f"authority live attack exact member/identity drift: {attack}")

    expected_command: dict[str, Any]
    if attack == "inspection_expected_outcome":
        expected_command = inspection_invocation("domain_A", "launch_physical_0001")
        expected_command["expected_access_state"] = "available"
    elif attack == "undeclared_semantic_input":
        expected_command = {
            "command_schema": "UndeclaredPhase3SemanticInput.v1",
            "proof_scenario": "simultaneous-physical-domains-v1.1",
            "domain_role": "domain_A",
            "environment_selector": "undeclared",
            "alternate_channel": "stdin_attempt",
        }
    else:
        expected_command = refresh_invocation("domain_A")
        if attack == "alternate_refresh":
            expected_command["alternate_channel"] = "directory_poll"
        elif attack == "refresh_head_field":
            expected_command["current_head_observation"] = current_head_observation()
        elif attack not in ("refresh_before_head_observation", "second_refresh"):
            raise ValueError(f"unknown authority live attack contract: {attack}")

    expectations = {
        "refresh_before_head_observation": (
            "PhysicalCurrentHeadGuard.assert_refresh_eligible", 1,
            "HarnessPhysicalCurrentHeadGuardRejection.v1", "physical_guard_transition",
            "refresh_before_durable_stale_open", "unchanged_H1", None,
        ),
        "alternate_refresh": (
            "ASimultaneousPhysicalDomainCommandRouter::HandleLine", 2,
            "SimultaneousPhysicalDomainFailure.v1", "invocation_read",
            "invalid_duplicate_or_out_of_order_refresh", "unchanged_H1", H0,
        ),
        "second_refresh": (
            "ASimultaneousPhysicalDomainCommandRouter::HandleLine", 3,
            "SimultaneousPhysicalDomainFailure.v1", "invocation_read",
            "invalid_duplicate_or_out_of_order_refresh", "unchanged_H1", H1,
        ),
        "refresh_head_field": (
            "ASimultaneousPhysicalDomainCommandRouter::HandleLine", 2,
            "SimultaneousPhysicalDomainFailure.v1", "invocation_read",
            "invalid_duplicate_or_out_of_order_refresh", "unchanged_H1", H0,
        ),
        "inspection_expected_outcome": (
            "ASimultaneousPhysicalDomainCommandRouter::HandleLine", 1,
            "SimultaneousPhysicalDomainFailure.v1", "inspection_invocation_read",
            "invalid_inspection_command", "unchanged_H0", H0,
        ),
        "undeclared_semantic_input": (
            "ASimultaneousPhysicalDomainCommandRouter::HandleLine", 1,
            "SimultaneousPhysicalDomainFailure.v1", "invocation_read",
            "unknown_command_schema", "unchanged_H0", H0,
        ),
    }
    path, command_delta, schema, stage, reason, relation, represented_hash = expectations[attack]
    if (
        value.get("actual_command") != expected_command
        or value.get("actual_validation_path") != path
        or value.get("live_stdin_command_count_delta") != command_delta
        or value.get("canonical_unchanged") is not True
    ):
        raise ValueError(f"authority live command/path/count drift: {attack}")
    _verify_canonical_relation(value.get("canonical_before_after_measurement"), relation)
    expected_transition = canonical_transition_run() if relation == "unchanged_H1" else None
    if value.get("canonical_transition") != expected_transition:
        raise ValueError(f"authority live transition binding drift: {attack}")

    binding, target_id, target_digest, target_birth = _verify_domain_evidence(
        value.get("target_domain_evidence"),
        expected_role="domain_A",
        expected_witness_id="f_refresh_fault",
    )
    peer_binding, peer_id, peer_digest, peer_birth = _verify_domain_evidence(
        value.get("peer_domain_evidence"),
        expected_role="domain_B",
        expected_witness_id="f_refresh_fault",
    )
    if (
        value.get("target_process_binding") != binding
        or value.get("target_executable_raw_sha256")
        != binding.get("executable_raw_sha256")
    ):
        raise ValueError(f"authority live executable binding drift: {attack}")
    _verify_liveness_sample(
        value.get("target_alive_after_rejection"),
        expected_role="domain_A",
        expected_checkpoint=None,
        binding=binding,
        instance_id=target_id,
    )
    _verify_liveness_sample(
        value.get("peer_alive_after_rejection"),
        expected_role="domain_B",
        expected_checkpoint=None,
        binding=peer_binding,
        instance_id=peer_id,
    )
    if target_id == peer_id or target_digest == peer_digest or target_birth == peer_birth:
        raise ValueError(f"authority live target/peer identity collision: {attack}")

    rejection = value.get("rejection")
    if not isinstance(rejection, dict) or rejection.get("diagnostic_schema") != schema:
        raise ValueError(f"authority live rejection schema drift: {attack}")
    if (
        rejection.get("proof_scenario") != "simultaneous-physical-domains-v1.1"
        or rejection.get("domain_role") != "domain_A"
        or rejection.get("local_publication_stage") != stage
        or rejection.get("reason_code") != reason
    ):
        raise ValueError(f"authority live rejection path/reason drift: {attack}")
    if schema == "HarnessPhysicalCurrentHeadGuardRejection.v1":
        if (
            set(rejection) != {
                "diagnostic_schema", "proof_scenario", "domain_role",
                "local_publication_stage", "reason_code", "refresh_command_delivered_to_unreal",
            }
            or rejection.get("refresh_command_delivered_to_unreal") is not False
        ):
            raise ValueError(f"authority harness rejection structure drift: {attack}")
    elif (
        set(rejection) != {
            "diagnostic_schema", "proof_scenario", "domain_role", "operational_process_instance_id",
            "process_binding_raw_sha256", "represented_hash_if_known",
            "local_publication_stage", "reason_code",
        }
        or rejection.get("operational_process_instance_id") != target_id
        or rejection.get("process_binding_raw_sha256") != target_digest
        or rejection.get("represented_hash_if_known") != represented_hash
    ):
        raise ValueError(f"authority UE rejection process/state binding drift: {attack}")
    return {
        "target_id": target_id,
        "target_digest": target_digest,
        "target_birth": target_birth,
        "peer_id": peer_id,
        "peer_digest": peer_digest,
        "peer_birth": peer_birth,
        "execution_digest": sha256_value(value),
    }


def _require_signature_rejection(call: Any, *, label: str) -> None:
    try:
        call()
    except TypeError:
        return
    raise ValueError(f"authority signature unexpectedly accepted: {label}")


def _verify_authority_concrete_execution(
    case: Mapping[str, Any],
    *,
    live_executions: list[dict[str, Any]],
) -> None:
    case_id = case["case_id"]
    concrete = case.get("concrete_input_and_bound_execution")
    if case_id in AUTHORITY_DESCRIPTION_INPUTS:
        baseline = {
            member["case_id"]: member
            for member in current_head_authority_failures()["cases"]
        }[case_id]
        if (
            concrete != AUTHORITY_DESCRIPTION_INPUTS[case_id]
            or baseline.get("description") != concrete
            or baseline.get("actual_validation_path") != case.get("actual_validation_path")
            or baseline.get("rejection_stage") != case.get("rejection_stage")
            or baseline.get("reason_code") != case.get("reason_code")
            or baseline.get("rejected") is not True
            or baseline.get("canonical_authority_acquired") is not False
        ):
            raise ValueError(f"authority deterministic concrete input drift: {case_id}")
        return
    if case_id == 11:
        if concrete != {"physical_refresh_order": ["domain_B", "domain_A"]}:
            raise ValueError("authority case 11 concrete order drift")
        _require_signature_rejection(
            lambda: canonical_transition_run(physical_refresh_order=["domain_B", "domain_A"]),  # type: ignore[call-arg]
            label="case_11_physical_refresh_order",
        )
        if stored_json_bytes(canonical_transition_run()) != stored_json_bytes(canonical_transition_run()):
            raise ValueError("authority case 11 normal canonical replay drift")
    elif case_id == 12:
        if concrete != AUTHORITY_CASE_12_REDIRECTED_INPUTS:
            raise ValueError("authority case 12 redirected-field executions drift")
    elif case_id == 16:
        refresh = _load("simultaneous_physical_domains_refresh_fault_atomicity.json")
        expected = next(
            row for row in refresh["cases"]
            if row["fault_stage"] == "local_atomic_publication" and row["fault_edge"] == "after"
        )
        if concrete != expected:
            raise ValueError("authority case 16 is not bound to the exact compiled refresh fault")
    elif case_id == 17:
        expected = {
            "W6_A": _load("physical_W6_asymmetric_A_synchronized_witness.json"),
            "W6_B": _load("physical_W6_asymmetric_B_synchronized_witness.json"),
            "W7_A": _load("physical_W7_destroy_A_witness.json"),
            "W7_B": _load("physical_W7_destroy_B_witness.json"),
            "attempted_H1_change": "canonical_records(domain_destruction_or_refresh_failure=...) rejected",
        }
        if concrete != expected:
            raise ValueError("authority case 17 live destruction/refresh evidence drift")
        _require_signature_rejection(
            lambda: canonical_records(domain_destruction_or_refresh_failure=concrete),  # type: ignore[call-arg]
            label="case_17_domain_destruction_or_refresh_failure",
        )
    elif case_id == 18:
        if concrete != {"local_state": {"route_access_cache": "available"}}:
            raise ValueError("authority case 18 local-state input drift")
        _require_signature_rejection(
            lambda: canonical_records(local_state=concrete),  # type: ignore[call-arg]
            label="case_18_local_state",
        )
    elif case_id == 19:
        guard = _load("simultaneous_physical_domains_guard_open_canonical_control.json")
        expected = {
            "canonical_control": {key: value for key, value in guard.items() if key != "physical_witness"},
            "live_physical_control": guard["physical_witness"],
        }
        if concrete != expected:
            raise ValueError("authority case 19 canonical/live guard control drift")
    elif case_id == 22:
        live_executions.append(_verify_live_authority_attack(
            concrete, attack="refresh_before_head_observation",
        ))
    elif case_id == 25:
        expected = {
            "baseline": _load("physical_W5_retention_baseline_witness.json")["physical_witness"],
            "perturbed": _load("physical_W5_retention_perturbed_witness.json")["physical_witness"],
        }
        if concrete != expected:
            raise ValueError("authority case 25 live retention evidence drift")
    elif case_id == 27:
        if not isinstance(concrete, dict) or set(concrete) != {"alternate_refresh", "second_refresh"}:
            raise ValueError("authority case 27 exact two-command evidence drift")
        live_executions.append(_verify_live_authority_attack(
            concrete["alternate_refresh"], attack="alternate_refresh",
        ))
        live_executions.append(_verify_live_authority_attack(
            concrete["second_refresh"], attack="second_refresh",
        ))
    elif case_id == 28:
        expected = {
            "A_failure": _load("physical_W6_asymmetric_B_synchronized_witness.json")["refresh_failures"]["domain_A"],
            "B_failure": _load("physical_W6_asymmetric_A_synchronized_witness.json")["refresh_failures"]["domain_B"],
        }
        if concrete != expected:
            raise ValueError("authority case 28 corrupt-bundle live failures drift")
    elif case_id == 29:
        live_executions.append(_verify_live_authority_attack(
            concrete, attack="refresh_head_field",
        ))
    elif case_id == 30:
        expected = {
            "physical_guard": "open_for_H1",
            "current_head_observation": current_head_observation(),
        }
        if concrete != expected:
            raise ValueError("authority case 30 guard/head input drift")
        _require_signature_rejection(
            lambda: canonical_transition_run(
                physical_guard="open_for_H1", current_head=current_head_observation(),  # type: ignore[call-arg]
            ),
            label="case_30_guard_and_head",
        )
    elif case_id == 33:
        w1 = _load("physical_W1_a_then_b_witness.json")
        expected = {
            "live_H0": w1["launch_observations"]["domain_A"],
            "live_H1": w1["refresh_observations"]["domain_A"],
            "live_fault_case_count": 24,
        }
        if concrete != expected:
            raise ValueError("authority case 33 live probe/fault evidence drift")
    elif case_id == 34:
        live_executions.append(_verify_live_authority_attack(
            concrete, attack="inspection_expected_outcome",
        ))
    elif case_id == 37:
        live_executions.append(_verify_live_authority_attack(
            concrete, attack="undeclared_semantic_input",
        ))
    else:
        raise ValueError(f"authority concrete execution contract missing: {case_id}")


def _verify_authority_payload(value: Mapping[str, Any]) -> None:
    if set(value) != {
        "all_canonical_measurements_recomputed", "all_real_validation_paths_executed",
        "all_rejected_or_protocol_invalid_as_frozen", "authority_case_actions",
        "case_count", "cases", "fresh_live_command_attack_count",
        "oracle_schema", "proof_scenario",
    }:
        raise ValueError("authority oracle exact member set drift")
    exact_table = {
        str(index): action for index, action in enumerate(AUTHORITY_CASE_ACTIONS, start=1)
    }
    cases = value.get("cases")
    if (
        len(AUTHORITY_EXECUTION_EXPECTATIONS) != 37
        or value.get("oracle_schema")
        != "SimultaneousPhysicalDomainsCurrentHeadAuthorityFailures.v1.1"
        or value.get("proof_scenario") != "simultaneous-physical-domains-v1.1"
        or value.get("authority_case_actions") != exact_table
        or value.get("case_count") != 37
        or value.get("fresh_live_command_attack_count") != 6
        or [case.get("case_id") for case in cases or []] != list(range(1, 38))
        or [case.get("action_id") for case in cases or []] != list(AUTHORITY_CASE_ACTIONS)
        or value.get("all_real_validation_paths_executed") is not True
        or value.get("all_rejected_or_protocol_invalid_as_frozen") is not True
        or value.get("all_canonical_measurements_recomputed") is not True
    ):
        raise ValueError("37-row authority case/action table drift")
    live_executions: list[dict[str, Any]] = []
    required_case_members = {
        "action_id", "actual_validation_path", "canonical_H1_unchanged",
        "canonical_authority_acquired", "canonical_before_after_measurement", "case_id",
        "concrete_input_and_bound_execution", "exact_H0_to_H1_committed", "reason_code",
        "rejected_or_protocol_invalid_as_frozen", "rejection_stage",
    }
    for case in cases:
        if set(case) != required_case_members:
            raise ValueError("authority case exact member set drift")
        case_id = case["case_id"]
        expected_path, expected_stage, expected_reason = AUTHORITY_EXECUTION_EXPECTATIONS[case_id - 1]
        expected_relation = "exact_H0_to_H1" if case_id == 19 else "unchanged_H1"
        _verify_canonical_relation(case.get("canonical_before_after_measurement"), expected_relation)
        if (
            case.get("actual_validation_path") != expected_path
            or case.get("rejection_stage") != expected_stage
            or case.get("reason_code") != expected_reason
            or "concrete_input_and_bound_execution" not in case
            or case.get("canonical_authority_acquired") is not False
            or case.get("rejected_or_protocol_invalid_as_frozen") is not True
        ):
            raise ValueError(f"authority case execution evidence drift: {case_id}")
        _verify_authority_concrete_execution(case, live_executions=live_executions)
        if case_id == 19:
            concrete = case["concrete_input_and_bound_execution"]
            control = concrete["canonical_control"]
            physical = concrete["live_physical_control"]
            if (
                case.get("canonical_H1_unchanged") is not False
                or case.get("exact_H0_to_H1_committed") is not True
                or control.get("canonical_R1_byte_identical") is not True
                or control.get("guard_after_commit_verification") != "failed_closed"
                or set(physical.get("terminal_dispositions", {}).values())
                != {"protocol_invalid(H0/H1)"}
            ):
                raise ValueError("authority case 19 exact canonical commit/protocol failure drift")
        elif case.get("canonical_H1_unchanged") is not True:
            raise ValueError(f"authority case {case_id} unchanged summary not derived")
    if len(live_executions) != 6:
        raise ValueError("authority live execution count drift")
    for key in (
        "target_id", "target_digest", "target_birth", "peer_id", "peer_digest",
        "peer_birth", "execution_digest",
    ):
        if len({execution[key] for execution in live_executions}) != len(live_executions):
            raise ValueError(f"authority live execution reused evidence: {key}")
    if (
        not {execution["target_id"] for execution in live_executions}.isdisjoint(
            execution["peer_id"] for execution in live_executions
        )
        or not {execution["target_digest"] for execution in live_executions}.isdisjoint(
            execution["peer_digest"] for execution in live_executions
        )
        or len(
            {execution["target_birth"] for execution in live_executions}
            | {execution["peer_birth"] for execution in live_executions}
        ) != len(live_executions) * 2
    ):
        raise ValueError("authority live target/peer process identities collide")


def _verify_other_witnesses() -> None:
    w3 = _load("physical_W3_stale_quarantine_witness.json")
    _verify_w3_payload(w3)
    w4 = _load("physical_W4_head_observation_failure_witness.json")
    physical_w4 = w4["physical_witness"]
    if (
        w4["injected_fault_point"] != "after_R1_H1_commit_verification_before_observation_construction"
        or w4["guard_terminal_state"] != "failed_closed"
        or physical_w4["head_observation_published"]
        or physical_w4["refresh_invocations"] != 0
        or set(physical_w4["terminal_states"].values()) != {"head_unconfirmed"}
    ):
        raise ValueError("W4 head-observation failure did not fail closed")
    baseline = _load("physical_W5_retention_baseline_witness.json")
    perturbed = _load("physical_W5_retention_perturbed_witness.json")
    oracle = _load("physical_W5_retention_equivalence_oracle.json")
    if (
        baseline["observed_retained_local_state_by_domain"]
        == perturbed["observed_retained_local_state_by_domain"]
        or not all(oracle["authoritative_derived_H1_byte_identical_by_role"].values())
        or not oracle["poison_observed_and_discarded_in_both_branches"]
        or not baseline["all_discard_required_H0_poison_observed_then_discarded"]
        or not perturbed["all_discard_required_H0_poison_observed_then_discarded"]
    ):
        raise ValueError("W5 retained-local-state perturbation selected H1 truth")
    for branch in (baseline, perturbed):
        for role in DOMAIN_ROLES:
            retention = branch["live_retention_execution_observations"][role]
            physical = branch["independent_live_H1_physical_observations"][role]
            if (
                retention["observation_source"] != "live_ue_adapter_postpublication_state_inspection"
                or not retention["discard_required_H0_poison_observed_before_refresh"]
                or not retention["prior_H0_actor_replaced"]
                or not retention["published_H1_actor_poison_clear"]
                or physical["observed_physical_access_state"] != "blocked"
                or physical["observation_source"] != "live_ue_world_actor_component_inspection"
            ):
                raise ValueError(f"W5 live execution evidence failed: {branch['branch']}/{role}")
    for name, success_role, stale_role in (
        ("physical_W6_asymmetric_A_synchronized_witness.json", "domain_A", "domain_B"),
        ("physical_W6_asymmetric_B_synchronized_witness.json", "domain_B", "domain_A"),
    ):
        witness = _load(name)
        if (
            witness["refresh_dispositions"][success_role]["head_state"] != "synchronized"
            or witness["refresh_dispositions"][stale_role]["head_state"] != "stale"
            or witness["refresh_failures"][stale_role]["represented_hash_if_known"] != H0
            or witness["refresh_dispositions"][stale_role]["current_head_claim_enabled"]
            or not witness["canonical_R1_byte_identical"]
        ):
            raise ValueError(f"asymmetric refresh atomicity failed: {name}")
    for name, destroyed, remaining in (
        ("physical_W7_destroy_A_witness.json", "domain_A", "domain_B"),
        ("physical_W7_destroy_B_witness.json", "domain_B", "domain_A"),
    ):
        witness = _load(name)
        post = next(item for item in witness["checkpoints"] if item["checkpoint"] == "post_destruction")
        if (
            destroyed not in witness["terminations"]
            or post["remaining_domain"]["domain_role"] != remaining
            or post["remaining_domain_head_state"] != "synchronized(H1)"
            or not post["canonical_H1_unchanged"]
        ):
            raise ValueError(f"destruction isolation failed: {name}")


def _binding_field_expected_reason(field_name: str) -> str:
    if field_name in ("binding_schema", "proof_scenario"):
        return "binding_structure_mismatch"
    if field_name in ("witness_id", "domain_role", "harness_launch_id"):
        return "binding_fixed_identity_or_cross_field_mismatch"
    return f"binding_field_mismatch/{field_name}"


def _verify_binding_field_adversaries(value: Any) -> None:
    if not isinstance(value, dict) or set(value) != {
        "all_coordinated_relabels_rejected",
        "all_fields_mutated_exactly_once", "all_rejected_before_materialization",
        "cases", "field_count", "field_order", "fresh_live_unreal_process_count",
        "matrix_schema", "proof_scenario", "coordinated_relabel_case_count",
        "coordinated_relabel_cases",
    }:
        raise ValueError("binding-field adversary matrix exact member set drift")
    cases = value.get("cases")
    if (
        value.get("matrix_schema")
        != "SimultaneousPhysicalDomainBindingFieldAdversaryMatrix.v1"
        or value.get("proof_scenario") != "simultaneous-physical-domains-v1.1"
        or value.get("field_order") != list(PROCESS_BINDING_FIELDS)
        or value.get("field_count") != len(PROCESS_BINDING_FIELDS)
        or value.get("fresh_live_unreal_process_count")
        != len(PROCESS_BINDING_FIELDS) + 1
        or value.get("all_fields_mutated_exactly_once") is not True
        or value.get("all_rejected_before_materialization") is not True
        or not isinstance(cases, list)
        or len(cases) != len(PROCESS_BINDING_FIELDS)
        or value.get("coordinated_relabel_case_count") != 1
        or value.get("all_coordinated_relabels_rejected") is not True
    ):
        raise ValueError("binding-field adversary matrix summary drift")
    expected_case_members = {
        "adversarial_bind_command", "adversarial_process_binding", "case_id",
        "case_schema", "changed_top_level_fields", "expected_reason_code",
        "mutated_field", "nominal_process_binding", "observed_failure",
        "operational_process_instance_id_recomputed",
        "rejected_before_materialization", "rejected_before_runtime_provenance",
        "runtime_trace_event_count", "termination",
    }
    failure_members = {
        "diagnostic_schema", "domain_role", "local_publication_stage",
        "operational_process_instance_id", "process_binding_raw_sha256",
        "proof_scenario", "reason_code", "represented_hash_if_known",
    }
    termination_members = {
        "canonical_input_from_terminated_output", "diagnostic_stream_raw_sha256",
        "domain_role", "pid", "terminated", "wait_status",
    }
    births = set()
    for index, (field_name, case) in enumerate(
        zip(PROCESS_BINDING_FIELDS, cases), start=1
    ):
        if not isinstance(case, dict) or set(case) != expected_case_members:
            raise ValueError("binding-field adversary case exact member set drift")
        nominal = case.get("nominal_process_binding")
        adversarial = case.get("adversarial_process_binding")
        if not isinstance(nominal, dict) or not isinstance(adversarial, dict):
            raise ValueError("binding-field adversary lacks two bindings")
        _validated_process_binding(
            nominal, expected_role="domain_A", expected_witness_id="w1_a_then_b"
        )
        changed = [
            name for name in PROCESS_BINDING_FIELDS
            if nominal.get(name) != adversarial.get(name)
        ]
        expected_reason = _binding_field_expected_reason(field_name)
        failure = case.get("observed_failure")
        termination = case.get("termination")
        birth = (
            nominal["pid"], nominal["macos_process_start"]["seconds"],
            nominal["macos_process_start"]["microseconds"],
        )
        if (
            set(nominal) != set(PROCESS_BINDING_FIELDS)
            or set(adversarial) != set(PROCESS_BINDING_FIELDS)
            or case.get("case_schema")
            != "SimultaneousPhysicalDomainBindingFieldAdversary.v1"
            or case.get("case_id") != f"binding_field_{index:02d}_{field_name}"
            or case.get("mutated_field") != field_name
            or case.get("changed_top_level_fields") != [field_name]
            or changed != [field_name]
            or case.get("adversarial_bind_command") != bind_invocation(adversarial)
            or case.get("operational_process_instance_id_recomputed") is not True
            or case.get("expected_reason_code") != expected_reason
            or case.get("rejected_before_runtime_provenance") is not True
            or case.get("rejected_before_materialization") is not True
            or case.get("runtime_trace_event_count") != 0
            or birth in births
        ):
            raise ValueError(f"binding-field adversary drift: {field_name}")
        births.add(birth)
        if (
            not isinstance(failure, dict) or set(failure) != failure_members
            or failure.get("diagnostic_schema")
            != "SimultaneousPhysicalDomainFailure.v1"
            or failure.get("proof_scenario") != "simultaneous-physical-domains-v1.1"
            or failure.get("domain_role") != "unbound"
            or failure.get("local_publication_stage")
            != "process_binding_identity_verification"
            or failure.get("reason_code") != expected_reason
            or failure.get("operational_process_instance_id") != ""
            or failure.get("process_binding_raw_sha256") != ""
            or failure.get("represented_hash_if_known") != ""
        ):
            raise ValueError(f"binding-field rejection evidence drift: {field_name}")
        if (
            not isinstance(termination, dict)
            or set(termination) != termination_members
            or termination.get("domain_role") != "domain_A"
            or termination.get("pid") != nominal["pid"]
            or termination.get("terminated") is not True
            or type(termination.get("wait_status")) is not int
            or not _is_sha256_text(termination.get("diagnostic_stream_raw_sha256"))
            or termination.get("canonical_input_from_terminated_output") is not False
        ):
            raise ValueError(f"binding-field termination evidence drift: {field_name}")

    coordinated = value.get("coordinated_relabel_cases")
    coordinated_members = {
        "adversarial_bind_command", "adversarial_process_binding", "case_id",
        "case_schema", "expected_reason_code", "mutated_fields",
        "nominal_process_binding", "observed_failure",
        "operational_process_instance_id_recomputed",
        "rejected_before_materialization", "rejected_before_runtime_provenance",
        "runtime_trace_event_count", "termination",
    }
    if not isinstance(coordinated, list) or len(coordinated) != 1:
        raise ValueError("coordinated binding adversary is absent")
    case = coordinated[0]
    if not isinstance(case, dict) or set(case) != coordinated_members:
        raise ValueError("coordinated binding adversary exact member set drift")
    nominal = case.get("nominal_process_binding")
    adversarial = case.get("adversarial_process_binding")
    if not isinstance(nominal, dict) or not isinstance(adversarial, dict):
        raise ValueError("coordinated binding adversary lacks exact bindings")
    _validated_process_binding(
        nominal, expected_role="domain_A", expected_witness_id="w1_a_then_b"
    )
    changed = [
        name for name in PROCESS_BINDING_FIELDS
        if nominal.get(name) != adversarial.get(name)
    ]
    failure = case.get("observed_failure")
    termination = case.get("termination")
    birth = (
        nominal["pid"], nominal["macos_process_start"]["seconds"],
        nominal["macos_process_start"]["microseconds"],
    )
    if (
        case.get("case_schema")
        != "SimultaneousPhysicalDomainCoordinatedBindingAdversary.v1"
        or case.get("case_id")
        != "coordinated_witness_and_harness_launch_relabel"
        or case.get("mutated_fields") != ["witness_id", "harness_launch_id"]
        or changed != ["witness_id", "harness_launch_id"]
        or adversarial.get("witness_id") != "w2_b_then_a"
        or adversarial.get("harness_launch_id")
        != "w2_b_then_a/domain_A/launch_0001"
        or case.get("adversarial_bind_command") != bind_invocation(adversarial)
        or case.get("operational_process_instance_id_recomputed") is not True
        or case.get("expected_reason_code") != "binding_field_mismatch/witness_id"
        or case.get("rejected_before_runtime_provenance") is not True
        or case.get("rejected_before_materialization") is not True
        or case.get("runtime_trace_event_count") != 0
        or birth in births
    ):
        raise ValueError("coordinated witness/launch relabel adversary drift")
    if (
        not isinstance(failure, dict) or set(failure) != failure_members
        or failure.get("diagnostic_schema")
        != "SimultaneousPhysicalDomainFailure.v1"
        or failure.get("proof_scenario") != "simultaneous-physical-domains-v1.1"
        or failure.get("domain_role") != "unbound"
        or failure.get("local_publication_stage")
        != "process_binding_identity_verification"
        or failure.get("reason_code") != "binding_field_mismatch/witness_id"
        or failure.get("operational_process_instance_id") != ""
        or failure.get("process_binding_raw_sha256") != ""
        or failure.get("represented_hash_if_known") != ""
    ):
        raise ValueError("coordinated binding rejection evidence drift")
    if (
        not isinstance(termination, dict) or set(termination) != termination_members
        or termination.get("domain_role") != "domain_A"
        or termination.get("pid") != nominal["pid"]
        or termination.get("terminated") is not True
        or type(termination.get("wait_status")) is not int
        or not _is_sha256_text(termination.get("diagnostic_stream_raw_sha256"))
        or termination.get("canonical_input_from_terminated_output") is not False
    ):
        raise ValueError("coordinated binding termination evidence drift")


def _verify_runtime_input_audit_contract(value: Any) -> None:
    required = {
        "all_launches_exact_surface", "all_refreshes_original_stdin_pipe_only",
        "alternate_refresh_channels", "audit_schema", "binding_field_adversaries",
        "dyld_shared_cache_inventory", "expected_physical_result_visible_to_probe",
        "fault_process_audits", "head_observation_visible_to_unreal",
        "other_domain_state_visible_to_unreal", "physical_guard_visible_to_unreal",
        "project_Content_ProofRecords_reads", "proof_scenario",
        "proof_semantic_closure_complete", "runtime_loaded_image_file_catalog",
        "runtime_loaded_image_file_catalog_entry_count",
        "runtime_loaded_image_file_catalog_raw_sha256",
        "runtime_loaded_image_inventory_catalog",
        "runtime_loaded_image_inventory_catalog_entry_count",
        "runtime_process_provenance_registry", "runtime_valid_process_expected_count",
        "runtime_valid_process_observed_count", "semantic_command_line_selectors",
        "semantic_environment_keys", "semantic_inherited_descriptors",
        "source_audit_adversary_count", "source_audit_check_count",
        "source_audit_raw_sha256", "witness_domain_audits",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError("proof-semantic input audit exact member set drift")
    if (
        value.get("audit_schema")
        != "SimultaneousPhysicalDomainsProofSemanticInputAudit.v1"
        or value.get("proof_scenario") != "simultaneous-physical-domains-v1.1"
        or value.get("semantic_environment_keys") != []
        or value.get("semantic_command_line_selectors") != []
        or value.get("semantic_inherited_descriptors") != [
            "fd_0_original_control_pipe_read_endpoint",
            "fd_1_original_structured_output_pipe_write_endpoint",
        ]
        or value.get("head_observation_visible_to_unreal") is not False
        or value.get("physical_guard_visible_to_unreal") is not False
        or value.get("other_domain_state_visible_to_unreal") is not False
        or value.get("expected_physical_result_visible_to_probe") is not False
        or value.get("alternate_refresh_channels") != []
        or value.get("project_Content_ProofRecords_reads") != []
        or value.get("proof_semantic_closure_complete") is not True
        or value.get("all_launches_exact_surface") is not True
        or value.get("all_refreshes_original_stdin_pipe_only") is not True
        or value.get("runtime_valid_process_expected_count") != 154
        or value.get("runtime_valid_process_observed_count") != 154
        or value.get("source_audit_check_count") != 38
        or value.get("source_audit_adversary_count") != 12
        or not _is_sha256_text(value.get("source_audit_raw_sha256"))
        or value.get("fault_process_audits") != {
            "refresh_case_count": 36,
            "physical_observation_case_count": 24,
            "fault_arm_channel": "original_process_stdin_exact_declared_command_only",
        }
    ):
        raise ValueError("proof-semantic input audit closure summary drift")
    source_audit = _load("simultaneous_physical_domains_source_audit.json")
    if (
        value.get("source_audit_raw_sha256") != sha256_value(source_audit)
        or source_audit.get("all_checks_passed") is not True
        or source_audit.get("check_count") != 38
        or source_audit.get("source_audit_adversaries", {}).get("case_count") != 12
        or source_audit.get("input_api_occurrence_count") != 69
        or source_audit.get("complete_phase3_input_api_census", {}).get(
            "exact_allowlist_match"
        ) is not True
        or source_audit.get("source_audit_adversaries", {}).get("all_rejected")
        is not True
    ):
        raise ValueError("proof-semantic input audit source binding drift")
    _verify_binding_field_adversaries(value.get("binding_field_adversaries"))

    inventory_catalog = value.get("runtime_loaded_image_inventory_catalog")
    if (
        not isinstance(inventory_catalog, dict) or not inventory_catalog
        or value.get("runtime_loaded_image_inventory_catalog_entry_count")
        != len(inventory_catalog)
    ):
        raise ValueError("loaded-image inventory catalog summary drift")
    for digest, rows in inventory_catalog.items():
        if (
            not _is_sha256_text(digest) or not isinstance(rows, list) or not rows
            or sha256_value(rows) != digest
        ):
            raise ValueError("loaded-image inventory catalog digest drift")

    file_catalog = value.get("runtime_loaded_image_file_catalog")
    if (
        not isinstance(file_catalog, list) or not file_catalog
        or value.get("runtime_loaded_image_file_catalog_entry_count")
        != len(file_catalog)
        or value.get("runtime_loaded_image_file_catalog_raw_sha256")
        != sha256_value(file_catalog)
    ):
        raise ValueError("loaded-image file catalog summary drift")
    file_paths = []
    for row in file_catalog:
        if (
            not isinstance(row, dict)
            or set(row) != {
                "device", "inode", "mach_o_uuids", "raw_sha256", "realpath",
                "size",
            }
            or not isinstance(row.get("realpath"), str)
            or not row["realpath"].startswith("/")
            or not isinstance(row.get("device"), str)
            or not isinstance(row.get("inode"), str)
            or type(row.get("size")) is not int or row["size"] <= 0
            or not _is_sha256_text(row.get("raw_sha256"))
            or not isinstance(row.get("mach_o_uuids"), list)
            or not row["mach_o_uuids"]
            or any(
                not isinstance(uuid, str) or len(uuid) != 36 or uuid != uuid.lower()
                for uuid in row["mach_o_uuids"]
            )
        ):
            raise ValueError("loaded-image file catalog identity drift")
        file_paths.append(row["realpath"])
    if file_paths != sorted(file_paths) or len(file_paths) != len(set(file_paths)):
        raise ValueError("loaded-image file catalog order/uniqueness drift")
    referenced_files = {
        row["realpath"]
        for rows in inventory_catalog.values()
        for row in rows
        if isinstance(row, dict) and row.get("filesystem_regular_file") is True
    }
    if referenced_files != set(file_paths):
        raise ValueError("loaded-image file catalog does not equal inventory union")

    shared_cache = value.get("dyld_shared_cache_inventory")
    members = shared_cache.get("members") if isinstance(shared_cache, dict) else None
    if (
        not isinstance(shared_cache, dict)
        or set(shared_cache) != {
            "inventory_raw_sha256", "inventory_schema", "members",
        }
        or shared_cache.get("inventory_schema")
        != "SimultaneousPhysicalDomainDyldSharedCacheInventory.v1"
        or not isinstance(members, list) or len(members) != 4
        or any(
            not isinstance(row, dict)
            or set(row) != {"raw_sha256", "realpath", "size"}
            or not isinstance(row.get("realpath"), str)
            or type(row.get("size")) is not int or row["size"] <= 0
            or not _is_sha256_text(row.get("raw_sha256"))
            for row in members
        )
        or shared_cache.get("inventory_raw_sha256")
        != sha256_value({
            "inventory_schema": shared_cache.get("inventory_schema"),
            "members": members,
        })
    ):
        raise ValueError("dyld shared-cache backing inventory drift")

    registry = value.get("runtime_process_provenance_registry")
    registry_members = {
        "all_stdin_commands_byte_bound", "alternate_runtime_input_path_observed",
        "binding_field_count", "closure_verified", "domain_role",
        "filesystem_loaded_image_catalog_raw_sha256",
        "loaded_image_inventory_raw_sha256", "operational_process_instance_id",
        "process_binding_raw_sha256", "runtime_input_trace_raw_sha256",
        "runtime_provenance_raw_sha256", "runtime_trace_event_count",
        "stdin_command_event_count", "witness_id",
    }
    if not isinstance(registry, list) or len(registry) != 154:
        raise ValueError("runtime process provenance registry count drift")
    ids = []
    for row in registry:
        if (
            not isinstance(row, dict) or set(row) != registry_members
            or row.get("witness_id") not in WITNESS_IDS
            or row.get("domain_role") not in DOMAIN_ROLES
            or not _is_sha256_text(row.get("operational_process_instance_id"))
            or not _is_sha256_text(row.get("process_binding_raw_sha256"))
            or not _is_sha256_text(row.get("runtime_provenance_raw_sha256"))
            or not _is_sha256_text(row.get("runtime_input_trace_raw_sha256"))
            or not _is_sha256_text(row.get("loaded_image_inventory_raw_sha256"))
            or not _is_sha256_text(
                row.get("filesystem_loaded_image_catalog_raw_sha256")
            )
            or type(row.get("runtime_trace_event_count")) is not int
            or row["runtime_trace_event_count"] <= 0
            or type(row.get("stdin_command_event_count")) is not int
            or row["stdin_command_event_count"] <= 0
            or row.get("binding_field_count") != len(PROCESS_BINDING_FIELDS)
            or row.get("closure_verified") is not True
            or row.get("all_stdin_commands_byte_bound") is not True
            or row.get("alternate_runtime_input_path_observed") is not False
            or row.get("loaded_image_inventory_raw_sha256") not in inventory_catalog
        ):
            raise ValueError("runtime process provenance registry row drift")
        ids.append(row["operational_process_instance_id"])
    if ids != sorted(ids) or len(ids) != len(set(ids)):
        raise ValueError("runtime process provenance registry order/uniqueness drift")

    primary_ids = [name for name in WITNESS_IDS if not name.startswith("f_")]
    witness_audits = value.get("witness_domain_audits")
    if (
        not isinstance(witness_audits, dict)
        or set(witness_audits) != set(primary_ids)
        or any(
            not isinstance(witness_audits[name], dict)
            or set(witness_audits[name]) != set(DOMAIN_ROLES)
            for name in primary_ids
        )
    ):
        raise ValueError("primary witness domain-audit index drift")


def _verify_runtime_evidence_population(input_audit: Mapping[str, Any]) -> None:
    evidence_rows: list[dict[str, Any]] = []

    def visit(value: Any) -> None:
        if (
            isinstance(value, dict)
            and isinstance(value.get("runtime_provenance"), dict)
            and value["runtime_provenance"].get("evidence_schema")
            == "SimultaneousPhysicalDomainCompactRuntimeProvenance.v1"
        ):
            evidence_rows.append(value)
            return
        if isinstance(value, dict):
            for member in value.values():
                visit(member)
        elif isinstance(value, list):
            for member in value:
                visit(member)

    input_name = "simultaneous_physical_domains_proof_semantic_input_audit.json"
    for name in ARTIFACT_NAMES:
        if name != input_name:
            visit(_load(name))
    if len(evidence_rows) != 170:
        raise ValueError(
            f"runtime evidence occurrence count drift: {len(evidence_rows)} != 170"
        )

    derived_registry = []
    evidence_by_primary: dict[tuple[str, str], Mapping[str, Any]] = {}
    unique_evidence: dict[str, Mapping[str, Any]] = {}
    births: dict[tuple[int, int, int], str] = {}
    referenced_catalogs = set()
    for evidence in evidence_rows:
        declared = evidence.get("binding")
        if not isinstance(declared, dict):
            raise ValueError("runtime evidence lacks a declared binding")
        binding, instance_id, binding_digest, birth = _verify_domain_evidence(
            evidence,
            expected_role=declared.get("domain_role"),
            expected_witness_id=declared.get("witness_id"),
            input_audit=input_audit,
        )
        if instance_id in unique_evidence:
            if unique_evidence[instance_id] != evidence:
                raise ValueError(
                    "re-embedded runtime process evidence is not byte-identical"
                )
            if births.get(birth) != instance_id:
                raise ValueError("re-embedded runtime evidence birth tuple drift")
            continue
        if birth in births:
            raise ValueError("runtime evidence reuses a process birth tuple")
        unique_evidence[instance_id] = evidence
        births[birth] = instance_id
        provenance_validation = evidence["runtime_provenance_validation"]
        trace_validation = evidence["runtime_input_trace_validation"]
        derived_registry.append({
            "witness_id": binding["witness_id"],
            "domain_role": binding["domain_role"],
            "operational_process_instance_id": instance_id,
            "process_binding_raw_sha256": binding_digest,
            "runtime_provenance_raw_sha256": provenance_validation[
                "runtime_provenance_raw_sha256"
            ],
            "runtime_input_trace_raw_sha256": trace_validation[
                "runtime_input_trace_raw_sha256"
            ],
            "runtime_trace_event_count": trace_validation["event_count"],
            "stdin_command_event_count": trace_validation[
                "stdin_command_event_count"
            ],
            "all_stdin_commands_byte_bound": trace_validation[
                "all_stdin_commands_byte_bound"
            ],
            "alternate_runtime_input_path_observed": trace_validation[
                "alternate_runtime_input_path_observed"
            ],
            "loaded_image_inventory_raw_sha256": provenance_validation[
                "loaded_image_inventory_raw_sha256"
            ],
            "filesystem_loaded_image_catalog_raw_sha256": provenance_validation[
                "filesystem_loaded_image_catalog_raw_sha256"
            ],
            "binding_field_count": provenance_validation["binding_field_count"],
            "closure_verified": True,
        })
        referenced_catalogs.add(
            provenance_validation["loaded_image_inventory_raw_sha256"]
        )
        if not binding["witness_id"].startswith("f_"):
            key = (binding["witness_id"], binding["domain_role"])
            if key in evidence_by_primary:
                raise ValueError("primary witness runtime evidence is duplicated")
            evidence_by_primary[key] = evidence
    if len(unique_evidence) != 154 or len(births) != 154:
        raise ValueError("runtime unique process evidence population drift")
    derived_registry.sort(key=lambda row: row["operational_process_instance_id"])
    if derived_registry != input_audit["runtime_process_provenance_registry"]:
        raise ValueError("runtime process provenance registry is not artifact-derived")
    if referenced_catalogs != set(
        input_audit["runtime_loaded_image_inventory_catalog"]
    ):
        raise ValueError("runtime loaded-image inventory catalog has an unbound entry")
    witness_audits = input_audit["witness_domain_audits"]
    for witness_id, roles in witness_audits.items():
        for role, evidence in roles.items():
            if evidence != evidence_by_primary.get((witness_id, role)):
                raise ValueError("primary witness domain audit differs from released evidence")

    source = _load("simultaneous_physical_domains_source_audit.json")
    if (
        input_audit.get("source_audit_raw_sha256") != sha256_value(source)
        or input_audit.get("source_audit_check_count") != source.get("check_count")
        or input_audit.get("source_audit_adversary_count")
        != source.get("source_audit_adversaries", {}).get("case_count")
    ):
        raise ValueError("runtime input audit is not bound to the source audit")


def _verify_oracles(w1: Mapping[str, Any], w2: Mapping[str, Any]) -> None:
    _expect_equal("simultaneous_physical_domains_canonical_transition_run.json", canonical_transition_run())
    _expect_equal("simultaneous_physical_domains_projection_matrix.json", projection_matrix())
    _expect_equal("simultaneous_physical_domains_operation_receipt_matrix.json", operation_receipt_matrix())
    _expect_equal("simultaneous_physical_domains_current_head_observation.json", current_head_observation())
    _expect_equal("simultaneous_physical_domains_head_observation_fault_atomicity.json", head_observation_fault_atomicity())
    guard = _load("simultaneous_physical_domains_guard_open_canonical_control.json")
    expected_guard = guard_open_control()
    for key, value in expected_guard.items():
        if guard.get(key) != value:
            raise ValueError(f"guard-open control deterministic field drift: {key}")
    if (
        guard["physical_witness"]["guard_machine"]["state"] != "failed_closed"
        or set(guard["physical_witness"]["terminal_dispositions"].values()) != {"protocol_invalid(H0/H1)"}
        or guard["physical_witness"]["refresh_invocations"] != 0
    ):
        raise ValueError("guard-open live canonical control drift")
    authority = _load("simultaneous_physical_domains_current_head_authority_failures.json")
    _verify_authority_payload(authority)
    refresh_faults = _load("simultaneous_physical_domains_refresh_fault_atomicity.json")
    _verify_refresh_fault_payload(refresh_faults)
    physical_faults = _load("simultaneous_physical_domains_physical_observation_fault_atomicity.json")
    _verify_physical_fault_payload(physical_faults)
    head_faults = _load("simultaneous_physical_domains_head_observation_fault_atomicity.json")
    if head_faults["fault_points"] != list(HEAD_OBSERVATION_FAULT_POINTS):
        raise ValueError("exact head observation fault surface drift")
    if (
        len(head_faults["cases"]) != 9
        or not head_faults["all_faults_executed"]
        or not head_faults["all_fail_closed_without_canonical_effect"]
        or len(head_faults["guard_illegal_transition_cases"]) != 8
        or not all(case["rejected"] for case in head_faults["guard_illegal_transition_cases"])
    ):
        raise ValueError("head/guard executable failure surface drift")
    input_audit = _load("simultaneous_physical_domains_proof_semantic_input_audit.json")
    _verify_runtime_input_audit_contract(input_audit)
    _verify_runtime_evidence_population(input_audit)
    rebind = _load("simultaneous_physical_domains_physical_rebind_oracle.json")
    if not all((
        rebind["receipt_independent_probe"],
        rebind["available_in_both_original_processes_at_H0"],
        rebind["blocked_in_both_original_processes_at_H1"],
        rebind["same_process_binding_before_after"],
    )):
        raise ValueError("independent live UE rebind oracle failed")
    canonical_equivalence = _load("simultaneous_physical_domains_canonical_equivalence_oracle.json")
    if not canonical_equivalence["all_branches_equal"] or canonical_equivalence["canonical_R1_raw_sha256"] != D1:
        raise ValueError("canonical equivalence oracle failed")
    source = _load("simultaneous_physical_domains_source_audit.json")
    rerun_source = _source_audit()
    if source != rerun_source or not source["all_checks_passed"]:
        raise ValueError("source/dataflow audit failed or cannot be reproduced")
    replay = _load("simultaneous_physical_domains_replay_oracle.json")
    if not replay["canonical_artifacts_byte_identical"] or not replay["W1_W2_semantic_primary_relations_equal"]:
        raise ValueError("semantic replay oracle failed")
    proof_run = _load("simultaneous_physical_domains_proof_run.json")
    if (
        proof_run["result"] != "PASS"
        or proof_run["witness_ids"] != list(WITNESS_IDS)
        or proof_run["primary_witness_count"] != 11
        or proof_run["refresh_fault_case_count"] != 36
        or proof_run["physical_observation_fault_case_count"] != 24
        or proof_run["artifact_member_count"] != 44
        or proof_run["proof_version"] != "0.1.1"
        or proof_run["harness_version"] != "0.7.0-draft.77"
        or proof_run["evidence_status"] != "unsealed"
        or proof_run["capacity_advancement"] != "none"
    ):
        raise ValueError("top-level proof run drift")


def _isolated_role_regeneration() -> None:
    """Regenerate all 44 roles without pretending operational IDs repeat."""

    with tempfile.TemporaryDirectory(prefix="spd-release-replay-") as temporary:
        regenerated = Path(temporary) / "SimultaneousPhysicalDomainsProofRecords"
        regenerated.mkdir()
        deterministic = {
            ARTIFACT_NAMES[0]: canonical_transition_run(),
            ARTIFACT_NAMES[1]: projection_matrix(),
            ARTIFACT_NAMES[2]: operation_receipt_matrix(),
            ARTIFACT_NAMES[3]: current_head_observation(),
            ARTIFACT_NAMES[4]: head_observation_fault_atomicity(),
        }
        for name in ARTIFACT_NAMES:
            payload = deterministic.get(name, _load(name))
            write_json(regenerated / name, payload)
        if not artifact_role_set_valid(regenerated):
            raise ValueError("isolated 44-role regeneration member set failed")
        for name, expected in deterministic.items():
            if (regenerated / name).read_bytes() != stored_json_bytes(expected):
                raise ValueError(f"isolated deterministic regeneration mismatch: {name}")


def _run_verifier_negative_tests() -> int:
    rejected = 0

    def reject(label: str, payload: Mapping[str, Any], verifier: Any) -> None:
        nonlocal rejected
        try:
            verifier(payload)
        except (ValueError, KeyError, TypeError, AssertionError):
            rejected += 1
        else:
            raise ValueError(f"negative verifier accepted adversary: {label}")

    def rebind_target(
        case: dict[str, Any],
        binding: Mapping[str, Any],
        *,
        result_key: str,
        evidence: Mapping[str, Any] | None = None,
    ) -> None:
        if evidence is not None:
            case["target_domain_evidence"] = copy.deepcopy(evidence)
        target = case["target_domain_evidence"]
        target["binding"] = copy.deepcopy(binding)
        target["binding_command"] = bind_invocation(binding)
        target["stdin_commands"][0] = bind_invocation(binding)
        for index, command in enumerate(target["stdin_commands"]):
            if command.get("operation") == "arm_exact_fault_once":
                target["stdin_commands"][index] = copy.deepcopy(case["fault_arm_command"])
        instance_id = operational_process_instance_id(binding)
        binding_digest = sha256_value(binding)
        case["target_process_binding"] = copy.deepcopy(binding)
        case["target_executable_raw_sha256"] = binding["executable_raw_sha256"]
        for member in (case["fault_arm_receipt"], case[result_key]):
            member["operational_process_instance_id"] = instance_id
            member["process_binding_raw_sha256"] = binding_digest
            member["executable_raw_sha256"] = binding["executable_raw_sha256"]

    def rebind_peer_birth(case: dict[str, Any], source_birth: Mapping[str, Any]) -> None:
        peer = case["peer_domain_evidence"]
        binding = copy.deepcopy(peer["binding"])
        binding["pid"] = source_birth["pid"]
        binding["macos_process_start"] = copy.deepcopy(source_birth["macos_process_start"])
        peer["binding"] = binding
        peer["binding_command"] = bind_invocation(binding)
        peer["stdin_commands"][0] = bind_invocation(binding)
        alive = case["peer_original_process_alive"]
        alive["pid"] = binding["pid"]
        alive["macos_process_start"] = copy.deepcopy(binding["macos_process_start"])
        alive["operational_process_instance_id"] = operational_process_instance_id(binding)
        alive["process_binding_raw_sha256"] = sha256_value(binding)

    cpu_only_w3 = copy.deepcopy(_load("physical_W3_stale_quarantine_witness.json"))
    for sample in cpu_only_w3["observed_domain_samples"].values():
        sample.pop("exact_local_step_command", None)
        sample.pop("exact_local_step_observation", None)
        sample["supplemental_total_cpu_nanoseconds_delta"] = 1
    reject("cpu_only_W3", cpu_only_w3, _verify_w3_payload)

    python_only_faults = copy.deepcopy(
        _load("simultaneous_physical_domains_refresh_fault_atomicity.json")
    )
    python_only_faults["execution_surface"] = "python_validator_replay_only"
    python_only_faults["cases"][0].pop("target_process_binding", None)
    python_only_faults["cases"][0].pop("fault_arm_receipt", None)
    python_only_faults["cases"][0].pop("compiled_boundary_result", None)
    reject("python_only_refresh_matrix", python_only_faults, _verify_refresh_fault_payload)

    swapped_authority = copy.deepcopy(
        _load("simultaneous_physical_domains_current_head_authority_failures.json")
    )
    swapped_authority["cases"][10]["action_id"], swapped_authority["cases"][16]["action_id"] = (
        swapped_authority["cases"][16]["action_id"],
        swapped_authority["cases"][10]["action_id"],
    )
    reject("swapped_authority_action_labels", swapped_authority, _verify_authority_payload)

    hard_coded_unchanged = copy.deepcopy(
        _load("simultaneous_physical_domains_refresh_fault_atomicity.json")
    )
    relation = hard_coded_unchanged["cases"][0]["canonical_before_after_measurement"]
    relation["after"]["authoritative_ledger_entry_count"] += 1
    relation["relation_verified"] = True
    hard_coded_unchanged["cases"][0]["canonical_H1_unchanged"] = True
    reject("hard_coded_unchanged_history", hard_coded_unchanged, _verify_refresh_fault_payload)

    refresh_source = _load("simultaneous_physical_domains_refresh_fault_atomicity.json")
    for label, field, replacement in (
        ("refresh_command_stage_mismatch", "fault_stage", "projection_verification"),
        ("refresh_command_edge_mismatch", "fault_edge", "after"),
        ("refresh_command_head_mismatch", "target_head_role", "H0"),
        ("refresh_command_run_id_mismatch", "fault_run_id", "refresh/H1/wrong/before/domain_A"),
    ):
        payload = copy.deepcopy(refresh_source)
        payload["cases"][0]["fault_arm_command"][field] = replacement
        reject(label, payload, _verify_refresh_fault_payload)
    payload = copy.deepcopy(refresh_source)
    payload["cases"][0]["compiled_boundary_result"] = copy.deepcopy(
        payload["cases"][2]["compiled_boundary_result"]
    )
    reject("refresh_reused_bound_result", payload, _verify_refresh_fault_payload)
    payload = copy.deepcopy(refresh_source)
    source_case, target_case = payload["cases"][0], payload["cases"][2]
    rebind_target(
        target_case,
        source_case["target_process_binding"],
        result_key="compiled_boundary_result",
        evidence=source_case["target_domain_evidence"],
    )
    reject("refresh_reused_target_process", payload, _verify_refresh_fault_payload)
    payload = copy.deepcopy(refresh_source)
    source_case, target_case = payload["cases"][0], payload["cases"][2]
    binding = copy.deepcopy(target_case["target_process_binding"])
    binding["pid"] = source_case["target_process_binding"]["pid"]
    binding["macos_process_start"] = copy.deepcopy(
        source_case["target_process_binding"]["macos_process_start"]
    )
    rebind_target(target_case, binding, result_key="compiled_boundary_result")
    reject("refresh_reused_target_birth_tuple", payload, _verify_refresh_fault_payload)
    payload = copy.deepcopy(refresh_source)
    payload["cases"][0].pop("peer_domain_evidence")
    reject("refresh_missing_peer_evidence", payload, _verify_refresh_fault_payload)
    payload = copy.deepcopy(refresh_source)
    payload["cases"][0]["peer_original_process_alive"]["original_child_handle_exit_observed"] = True
    reject("refresh_dead_peer", payload, _verify_refresh_fault_payload)
    payload = copy.deepcopy(refresh_source)
    payload["cases"][2]["peer_domain_evidence"] = copy.deepcopy(payload["cases"][0]["peer_domain_evidence"])
    payload["cases"][2]["peer_original_process_alive"] = copy.deepcopy(payload["cases"][0]["peer_original_process_alive"])
    reject("refresh_reused_peer_process", payload, _verify_refresh_fault_payload)
    payload = copy.deepcopy(refresh_source)
    rebind_peer_birth(payload["cases"][2], payload["cases"][0]["peer_domain_evidence"]["binding"])
    reject("refresh_reused_peer_birth_tuple", payload, _verify_refresh_fault_payload)

    physical_source = _load("simultaneous_physical_domains_physical_observation_fault_atomicity.json")
    for label, field, replacement in (
        ("observation_command_stage_mismatch", "fault_stage", "immutable_process_binding_verification"),
        ("observation_command_edge_mismatch", "fault_edge", "before"),
        ("observation_command_head_mismatch", "target_head_role", "H1"),
        ("observation_command_run_id_mismatch", "fault_run_id", "physical_observation/H0/wrong/at/domain_A"),
    ):
        payload = copy.deepcopy(physical_source)
        payload["cases"][0]["fault_arm_command"][field] = replacement
        reject(label, payload, _verify_physical_fault_payload)
    payload = copy.deepcopy(physical_source)
    payload["cases"][0]["boundary_result"] = copy.deepcopy(payload["cases"][2]["boundary_result"])
    reject("observation_reused_bound_result", payload, _verify_physical_fault_payload)
    payload = copy.deepcopy(physical_source)
    source_case, target_case = payload["cases"][0], payload["cases"][2]
    rebind_target(
        target_case,
        source_case["target_process_binding"],
        result_key="boundary_result",
        evidence=source_case["target_domain_evidence"],
    )
    reject("observation_reused_target_process", payload, _verify_physical_fault_payload)
    payload = copy.deepcopy(physical_source)
    source_case, target_case = payload["cases"][0], payload["cases"][2]
    binding = copy.deepcopy(target_case["target_process_binding"])
    binding["pid"] = source_case["target_process_binding"]["pid"]
    binding["macos_process_start"] = copy.deepcopy(
        source_case["target_process_binding"]["macos_process_start"]
    )
    rebind_target(target_case, binding, result_key="boundary_result")
    reject("observation_reused_target_birth_tuple", payload, _verify_physical_fault_payload)
    payload = copy.deepcopy(physical_source)
    payload["cases"][0].pop("peer_domain_evidence")
    reject("observation_missing_peer_evidence", payload, _verify_physical_fault_payload)
    payload = copy.deepcopy(physical_source)
    payload["cases"][0]["peer_original_process_alive"]["control_pipe_unexpected_eof"] = True
    reject("observation_dead_peer", payload, _verify_physical_fault_payload)
    payload = copy.deepcopy(physical_source)
    payload["cases"][2]["peer_domain_evidence"] = copy.deepcopy(payload["cases"][0]["peer_domain_evidence"])
    payload["cases"][2]["peer_original_process_alive"] = copy.deepcopy(payload["cases"][0]["peer_original_process_alive"])
    reject("observation_reused_peer_process", payload, _verify_physical_fault_payload)

    authority_source = _load("simultaneous_physical_domains_current_head_authority_failures.json")
    for label, field in (
        ("swapped_authority_execution_paths", "actual_validation_path"),
        ("swapped_authority_rejection_stages", "rejection_stage"),
        ("swapped_authority_reasons", "reason_code"),
        ("swapped_authority_concrete_inputs", "concrete_input_and_bound_execution"),
    ):
        payload = copy.deepcopy(authority_source)
        payload["cases"][10][field], payload["cases"][16][field] = (
            payload["cases"][16][field], payload["cases"][10][field]
        )
        reject(label, payload, _verify_authority_payload)
    for label, field, replacement in (
        ("arbitrary_authority_execution_path", "actual_validation_path", "nonempty_arbitrary_path"),
        ("arbitrary_authority_rejection_stage", "rejection_stage", "nonempty_arbitrary_stage"),
        ("arbitrary_authority_reason", "reason_code", "nonempty_arbitrary_reason"),
        ("arbitrary_authority_concrete_input", "concrete_input_and_bound_execution", {"asserted": True}),
    ):
        payload = copy.deepcopy(authority_source)
        payload["cases"][10][field] = replacement
        reject(label, payload, _verify_authority_payload)

    domain_source = refresh_source["cases"][0]["target_domain_evidence"]
    domain_verifier = lambda evidence: _verify_domain_evidence(
        evidence,
        expected_role="domain_A",
        expected_witness_id="f_refresh_fault",
        input_audit=_runtime_input_audit(),
    )
    payload = copy.deepcopy(domain_source)
    payload["runtime_provenance"][
        "child_report_without_loaded_image_identities"
    ]["captured_before_first_materialization"] = False
    reject("runtime_provenance_report_tamper", payload, domain_verifier)
    payload = copy.deepcopy(domain_source)
    payload["runtime_input_trace"][0]["observed_raw_sha256"] = "0" * 64
    reject("runtime_input_trace_tamper", payload, domain_verifier)
    successful_trace = copy.deepcopy(
        _load("physical_W1_a_then_b_witness.json")["domains"]["domain_A"]
    )
    successful_trace["runtime_input_trace"] = [
        row for row in successful_trace["runtime_input_trace"]
        if not (
            row["input_class"] == "live_world_state"
            and row["metadata"].get("inspection_id")
            == "refresh_physical_0001"
        )
    ]
    for sequence, row in enumerate(
        successful_trace["runtime_input_trace"], start=1
    ):
        row["sequence"] = sequence
    trace_validation = successful_trace["runtime_input_trace_validation"]
    trace_validation["event_count"] = len(successful_trace["runtime_input_trace"])
    trace_validation["last_sequence"] = len(successful_trace["runtime_input_trace"])
    trace_validation["live_world_event_count"] -= 3
    trace_validation["full_three_stage_inspection_count"] -= 1
    trace_validation["runtime_input_trace_raw_sha256"] = sha256_value(
        successful_trace["runtime_input_trace"]
    )
    reject(
        "successful_refresh_live_world_trace_deleted_and_summary_recomputed",
        successful_trace,
        lambda evidence: _verify_domain_evidence(
            evidence,
            expected_role="domain_A",
            expected_witness_id="w1_a_then_b",
            input_audit=_runtime_input_audit(),
        ),
    )
    payload = copy.deepcopy(_runtime_input_audit())
    catalog_digest = domain_source["runtime_provenance"][
        "loaded_image_inventory_reference"
    ]["catalog_raw_sha256"]
    payload["runtime_loaded_image_inventory_catalog"].pop(catalog_digest)
    reject(
        "runtime_loaded_image_catalog_missing",
        payload,
        lambda audit: _verify_domain_evidence(
            domain_source,
            expected_role="domain_A",
            expected_witness_id="f_refresh_fault",
            input_audit=audit,
        ),
    )
    payload = copy.deepcopy(_runtime_input_audit())
    payload["runtime_process_provenance_registry"].pop()
    reject("runtime_process_registry_missing", payload, _verify_runtime_input_audit_contract)
    payload = copy.deepcopy(_runtime_input_audit())
    payload["binding_field_adversaries"]["cases"].pop()
    reject("binding_field_adversary_missing", payload, _verify_runtime_input_audit_contract)
    payload = copy.deepcopy(_runtime_input_audit())
    payload["binding_field_adversaries"]["cases"][0][
        "rejected_before_materialization"
    ] = False
    reject("binding_field_adversary_accepted", payload, _verify_runtime_input_audit_contract)
    payload = copy.deepcopy(_runtime_input_audit())
    payload["source_audit_raw_sha256"] = "0" * 64
    reject("source_audit_digest_tamper", payload, _verify_runtime_input_audit_contract)

    if rejected != 41:
        raise ValueError(f"negative verifier rejection count drift: {rejected}")
    return rejected


def _run_focused_tests() -> None:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPYCACHEPREFIX"] = "/private/tmp/thecity_pycache"
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "test_simultaneous_physical_domains.py"],
        cwd=ROOT / "proof_kernel", env=environment, capture_output=True, text=True,
    )
    if result.returncode != 0 or "Ran 40 tests" not in result.stderr or "OK" not in result.stderr:
        raise ValueError(f"focused Phase-3 tests failed:\n{result.stdout}\n{result.stderr}")


def verify_artifacts() -> None:
    global _RUNTIME_INPUT_AUDIT_CACHE
    if not artifact_role_set_valid(RECORDS):
        raise ValueError("artifact directory is not exact 44-member regular-file set")
    for name in ARTIFACT_NAMES:
        _strict_member(RECORDS / name)
        _load(name)
    _RUNTIME_INPUT_AUDIT_CACHE = _load(
        "simultaneous_physical_domains_proof_semantic_input_audit.json"
    )
    _verify_runtime_input_audit_contract(_RUNTIME_INPUT_AUDIT_CACHE)
    w1 = _verify_primary("W1")
    w2 = _verify_primary("W2")
    _verify_other_witnesses()
    _verify_oracles(w1, w2)
    _isolated_role_regeneration()
    _run_verifier_negative_tests()
    _run_focused_tests()


def write_release() -> int:
    if not EVIDENCE.is_file():
        raise FileNotFoundError("exact evidence document is required before manifest creation")
    verify_artifacts()
    own = MANIFEST.relative_to(ROOT).as_posix()
    if own in release_paths():
        raise AssertionError("manifest self-inclusion")
    for relative in release_paths():
        _strict_member(ROOT / relative)
    MANIFEST.write_text(
        "".join(f"{_sha(ROOT / relative)}  {relative}\n" for relative in release_paths()),
        encoding="utf-8",
    )
    return len(release_paths())


def verify_release() -> int:
    _strict_member(MANIFEST)
    raw = MANIFEST.read_bytes()
    if not raw.endswith(b"\n") or b"\r" in raw:
        raise ValueError("manifest line ending drift")
    parsed: list[tuple[str, str]] = []
    seen: set[str] = set()
    own = MANIFEST.relative_to(ROOT).as_posix()
    for raw_line in raw.decode("utf-8", errors="strict").splitlines():
        digest, separator, relative = raw_line.partition("  ")
        candidate = Path(relative)
        if (
            separator != "  " or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
            or not relative or relative in seen or relative == own
            or candidate.is_absolute() or ".." in candidate.parts
        ):
            raise ValueError(f"invalid manifest member: {raw_line!r}")
        seen.add(relative)
        parsed.append((digest, relative))
    if tuple(relative for _, relative in parsed) != release_paths():
        raise ValueError("manifest exact member order/set drift")
    for digest, relative in parsed:
        path = ROOT / relative
        _strict_member(path)
        if _sha(path) != digest:
            raise ValueError(f"manifest checksum mismatch: {relative}")
    verify_artifacts()
    return len(parsed)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("artifacts", "write-release", "verify"))
    arguments = parser.parse_args()
    if arguments.command == "artifacts":
        verify_artifacts()
        print("verified exact 44/44 Phase-3 artifacts; verifier adversaries 41/41 rejected; evidence remains unsealed")
        return 0
    if arguments.command == "write-release":
        count = write_release()
    else:
        if not EVIDENCE.is_file() or not MANIFEST.is_file():
            raise SystemExit("release verification unavailable: evidence document or manifest missing")
        count = verify_release()
    print(f"verified {count}/{count} release members; verifier adversaries 41/41 rejected; manifest excludes itself; evidence remains unsealed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
