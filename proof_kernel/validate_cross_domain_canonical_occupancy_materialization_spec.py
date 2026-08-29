#!/usr/bin/env python3
"""Validate the Phase-4 corrective specification's frozen-candidate structure.

This is review-time document QA. It does not import or execute a Phase-4 proof
implementation, create evidence, or belong to the prospective release. The
``--self-test`` mode mutates only in-memory document copies.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections.abc import Callable
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "Cross-Domain Canonical Occupancy Materialization Proof - Draft.md"
THIS_VALIDATOR = (
    "proof_kernel/validate_cross_domain_canonical_occupancy_materialization_spec.py"
)
MANIFEST = (
    "Cross-Domain Canonical Occupancy Materialization Proof - v0.1.0 SHA256SUMS.txt"
)

EXPECTED_COMPLETE_SPEC_SHA256 = (
    "ec06d6ed4b0fa9b4bd5eb9f2c2fd09048218ef20bc54dac9d7567d116359a3f3"
)
EXPECTED_ARTIFACT_LIST_SHA256 = (
    "93d3e024361f94c613aae4a8467b12a6463fbc69d46397908158f6c7dc50c7ef"
)
EXPECTED_NON_ARTIFACT_LIST_SHA256 = (
    "7f27873096458befcd72e6a3ca6c1c590d0f2c9ff387d692c85d7245fd8780fb"
)
EXPECTED_PROJECTION_JSON_LINES_SHA256 = (
    "0b957c6929bfbe4d7266337ee3a9685c394675f81696caa36cc4afbfcab1bde2"
)
EXPECTED_PERMISSION_TABLE_SHA256 = (
    "c3a4f475fd0d9fd069d21b311ee8fe058af1a492656041a7165bd54a96165c1f"
)
EXPECTED_OPERATION_TABLE_SHA256 = (
    "96995d7a24eb608452e76decabec58bd53673b1f528a786480feba06721b5752"
)
EXPECTED_AUTHORITY_TABLE_SHA256 = (
    "f06dd89bb16146903df872a7fd1a37e4069037d97664ddb52a81e69c5f8e2a92"
)
EXPECTED_HF_TABLE_SHA256 = "99497255063f5bb0ec1d065ed069a8bf61f12ad5a43bd691f9e6d2379c8e3292"
EXPECTED_OF_TABLE_SHA256 = "6b2250eb2d73af26b1e7d2ec1b565313f7c8ab39a6ec2577335ef7b05dea2dde"
EXPECTED_COMMAND_PROFILE_TABLE_SHA256 = "91a2e5721a3ce256c72fcfdee4f15a8a36d536a5c82c2c78798d2745ffb7c92d"
EXPECTED_WITNESS_PROFILE_TABLE_SHA256 = "893d4a54700d9f359da98688749df0abaf8907f7ceb124f072ebe2991fa938a5"
EXPECTED_CONTROL_COMMAND_TABLE_SHA256 = "f5970326a5c54063839dc8a44d77f1fa4fc2167e970bbaf26e58648c01cc2053"
EXPECTED_CONTROL_FAULT_TABLE_SHA256 = "9ca195145d3fd11e63804fe5a07ee41fb8d3563a779c7ebe2a8968a8b3883175"
EXPECTED_PRIMARY_WITNESS_TABLE_SHA256 = "da6fdb30f4dda490ee57187ba7915969689fd0504053af7fd705056b4a20d0e3"
EXPECTED_LIVENESS_TABLE_SHA256 = "885cab4cfcb30b8bfc892ab98f2ec217a7c891d48c47a746265c72dc330120db"
EXPECTED_GUARD_TRANSITION_TABLE_SHA256 = "e05722c8a19fc29d95b201ca862af4f91df6ef7e5e7af39b62c9d4e9434cd02d"
EXPECTED_CONTAINING_BLOCK_SHA256 = {
    "binding_schema: CrossDomainOccupancyProcessBinding.v1": "6a6821e9127cc91f93ac5466466645dcf6812fe369f1d47db99cad0925a98830",
    "bind_invocation_schema: CrossDomainOccupancyBindInvocation.v1": "df80b1e19cebd2a4cbab4e9854fee5a743b330c277e852b497c8081327ca2b7a",
    "launch_plan_schema: CrossDomainOccupancyLaunchPlan.v1": "761fdf1a5466e3b9f3f41c86ed887fe52de826d5f1feecd0efed144863482a0b",
    "expected_schema: CrossDomainOccupancyExpectedRepresentation.v1": "44f0c74e7c45e0a9924eb6c8b457e4343459b456b49df071f44c0016be61fdcd",
    "anchor_schema: CrossDomainOccupancyHeadAnchor.v1": "cc4c5ddb224e78211ebb0810b8c7c35088f86b3c0dad309029c110626f29284b",
    "subject_schema: CrossDomainOccupancySubjectRepresentation.v1": "6f3b62fa3a23b2f790615a0f7c98d23b868ef3854993f68a479e2744d5932805",
    "observation_schema: CrossDomainOccupancyLiveObservation.v1": "3203df4061f2fd3888495458d9455a45595c56af178ed6f97f4e4f2ce18770b9",
    "observation_schema: CrossDomainOccupancyCanonicalHeadObservation.v1": "5a642c161fd795a1d0d3f410f4ea18e50c5dc375e8af28037fa3a8a4b4a474ce",
    "disposition_schema: CrossDomainOccupancyHeadDisposition.v1": "960d6ae3ebe5906b650c980d1b85cf425d7eeae486ae0a304d25f0de1c50b53d",
    "invocation_schema: CrossDomainOccupancyOperationInvocation.v1": "4be6a0fea80f9d4fa9caeb7dab3badaba18f57702985e250e9869ab913ec0ce7",
    "materialize_invocation_schema: CrossDomainOccupancyMaterializeInvocation.v1": "02df652c23e0db3bb1299cead2b4dac4a52d7fc4f33698b30a276d1f69c1f1b1",
    "inspection_invocation_schema: CrossDomainOccupancyInspectionInvocation.v1": "cb79d16a517a405b4f30dd806f70400d2a33f2929dcd80feeeeebc6b3529b7c5",
    "fault_arm_invocation_schema: CrossDomainOccupancyProcessFaultArmInvocation.v1": "d6722f1c0e2b4ed699603ba221c0370745eaca1970e0f553d114a2cdfe66c8f4",
    "process_fault_arm_receipt_schema: CrossDomainOccupancyProcessFaultArmReceipt.v1": "0f73ee040fccc0bb96bcf5ad640d2345d578d19e1ce729b24a27a90d0ad01f13",
    "harness_fault_plan_schema: CrossDomainOccupancyHarnessFaultPlan.v1": "710355e5d1b61920773912b55d1e526c428b906c70b441cdf745118e41e85ae4",
    "harness_fault_arm_receipt_schema: CrossDomainOccupancyHarnessFaultArmReceipt.v1": "51b035c36cb8fa3fc239ca8e7756549c911eca3aeb88b6458ba06f9818c0a6fa",
    "launch_surface_schema: CrossDomainOccupancyLaunchSurface.v1": "8efd0b8627143cc62fec5a824efea4b0b38088d99b81084acb55e9adea2e94fc",
    "receipt_schema: CrossDomainOccupancyMaterializationReceipt.v1": "0b8eca7d1017c2a3969e469a37d33f2255ec34fbc3b971023b827c84e563b230",
    "trace_schema: CrossDomainOccupancyRuntimeTraceEvent.v1": "fcce47c95976f70b5c9aca7b988b25fb665bf4949d6be949087747239180230d",
    "harness_trace_schema: CrossDomainOccupancyHarnessTraceEvent.v1": "891f3ff8fb88ee55edae24390fcd8a57c0f4890b12d397f9074a8f75a5a7857f",
    "frozen_implementation_authority:": "ca09447f94bece75ee64659cef08a4ae6c2fddf2cc972a34f1fd652b1f2c7175",
}
EXPECTED_AFTER_BLOCK_SHA256 = {
    "Field verification modes are exact:": "f11369b43dbeff5f6f8d05ed98d74b580cb8df943ce5cb6ce3aa47e425b49600",
    "The exact states are:": "50f70dbf66c78dc32fc9ab11ec52b743c3b4c33243909119602aec74776ebed9",
}

EXPECTED_VERSION_HEADER = "**Version:** 0.1.0-draft.1\\"
EXPECTED_STATUS_HEADER = (
    "**Status:** Corrective final freeze-review candidate; implementation prohibited\\"
)
EXPECTED_IDENTITY = (
    "**Candidate proof-harness identity:** "
    "`CrossDomainCanonicalOccupancyMaterializationProof.v1` / "
    "`0.7.0-draft.80` — not frozen"
)

EXPECTED_CANONICAL_RAW = {
    "proof_kernel/CanonicalOccupancyTransitionProofRecords/"
    "canonical_occupancy_transition_R0.json": (
        "59ce47bc4d6c63cbda4a740fec8d25e497ca8ed74052b16b5358745be115c2dc"
    ),
    "proof_kernel/CanonicalOccupancyTransitionProofRecords/"
    "canonical_occupancy_transition_Rtransit.json": (
        "215e3383bff21a9fe01dbb240035a0fa5dd774c703417486846e027a0615a12f"
    ),
    "proof_kernel/CanonicalOccupancyTransitionProofRecords/"
    "canonical_occupancy_transition_Rfinal.json": (
        "0b4d9d97eb166b3aae6480c5581654c39b367c3a5fab47a02daec50b1e88a181"
    ),
}
EXPECTED_PROJECTION_IDS = (
    "cross_domain_A_R0_0001",
    "cross_domain_B_R0_0001",
    "cross_domain_A_Rtransit_0001",
    "cross_domain_B_Rtransit_0001",
    "cross_domain_A_Rfinal_0001",
    "cross_domain_B_Rfinal_0001",
)
EXPECTED_PROJECTION_DIGESTS = (
    "c175ee92a3c69adbbeebaeecdabb54e462bbea1aa99f43117c5205757bcc9624",
    "4d8da172945e1ff97433fe6230290f448d8731ac0dd5d3cef421e806b43531cb",
    "1f57d0fc964956275008fffeb82adbb365f7c3343cce76d90e5cbd53262d68e6",
    "1e72049befcbd9d1af6babaf855440c14101faa2d4aa5b97d13b9ae859d8d5dc",
    "723d9e539f3e0cebdab418dfacb25f8f2d6bbc0acd42c85a5330dca322a5e6c8",
    "1552fb88285ffe670f1866ac324ef4b61c51d4ec2c4977df84e23b97e8eb85b9",
)

EXPECTED_BINDING_FIELDS = (
    "binding_schema",
    "proof_scenario",
    "witness_id",
    "domain_role",
    "harness_launch_id",
    "pid",
    "macos_process_start",
    "executable_realpath",
    "executable_raw_sha256",
    "unreal_engine_build_identity",
    "entry_map_package_identity",
    "project_realpath",
    "project_raw_sha256",
    "project_config_and_module_inventory_raw_sha256",
    "process_root_realpath",
    "launch_argv_raw_sha256",
    "launch_environment_audit_raw_sha256",
    "launch_cwd_realpath",
    "inherited_descriptor_map_raw_sha256",
    "control_pipe_id",
    "structured_output_pipe_id",
    "diagnostic_pipe_id",
)
EXPECTED_WITNESS_IDS = (
    "w1_A_B__A_B",
    "w2_B_A__B_A",
    "w3_A_B__B_A",
    "w4_B_A__A_B",
    "c1_canonical_completion_independence",
    "c2_positive_Rtransit_absence",
    "c3_receipt_only_rejection",
    "c4a_start_guard_open",
    "c4b_completion_guard_open",
    "c5_process_replacement",
    "af_Rtransit_A_success_B_failure",
    "af_Rtransit_B_success_A_failure",
    "af_Rfinal_A_success_B_failure",
    "af_Rfinal_B_success_A_failure",
    "fault_head_publication",
    "fault_materialization",
    "fault_live_observation",
    "authority_adversary",
    "process_binding_adversary",
    "liveness_adversary",
    "replay_repeat",
)
EXPECTED_GUARD_STATES = (
    "open_for_R0",
    "closed_for_R0_to_Rtransit",
    "open_for_Rtransit",
    "closed_for_Rtransit_to_Rfinal",
    "closed_for_c1_Rtransit_to_Rfinal",
    "open_for_Rfinal",
    "failed_closed",
)

EXPECTED_SCHEMA_FIELDS = {
    "expected_schema: CrossDomainOccupancyExpectedRepresentation.v1": (
        "expected_schema", "proof_scenario", "domain_role",
        "canonical_payload_raw_sha256", "canonical_hash",
        "projection_raw_sha256", "projection_id", "projected_canonical_site_id",
        "projected_site_representation_slot", "projected_subject_representation_slot",
        "canonical_occupant_id",
        "canonical_occupancy_kind", "canonical_occupancy_reference",
        "expected_local_subject_disposition", "expected_anchor_actor_count",
        "expected_subject_actor_count", "expected_proof_relevant_actor_count",
        "expected_route_actor_count", "expected_unexpected_proof_tagged_actor_count",
        "expected_pawn_count", "expected_controller_count",
        "expected_auto_receive_input_actor_count",
        "expected_phase_4_actor_input_binding_count", "expectation_source",
    ),
    "anchor_schema: CrossDomainOccupancyHeadAnchor.v1": (
        "anchor_schema", "proof_scenario", "domain_role",
        "operational_process_instance_id", "process_binding_raw_sha256",
        "accepted_canonical_payload_raw_sha256", "accepted_canonical_hash",
        "accepted_projection_raw_sha256", "accepted_projection_id",
        "projected_canonical_site_id", "projected_site_representation_slot",
        "projected_subject_representation_slot",
        "canonical_occupant_id", "canonical_occupancy_kind",
        "canonical_occupancy_reference", "local_subject_disposition",
        "publication_generation", "representation_publication_state",
    ),
    "subject_schema: CrossDomainOccupancySubjectRepresentation.v1": (
        "subject_schema", "proof_scenario", "domain_role",
        "operational_process_instance_id", "process_binding_raw_sha256",
        "canonical_occupant_id", "represented_site_id",
        "subject_representation_slot", "accepted_canonical_payload_raw_sha256",
        "accepted_canonical_hash", "accepted_projection_raw_sha256",
        "accepted_projection_id", "publication_generation",
        "representation_publication_state",
    ),
    "observation_schema: CrossDomainOccupancyLiveObservation.v1": (
        "observation_schema", "proof_scenario", "domain_role",
        "operational_process_instance_id", "process_binding_raw_sha256",
        "inspection_id", "observed_publication_generation", "world_package_name",
        "world_instance_identity", "world_type", "loaded_level_count",
        "level_actor_slot_count", "null_level_actor_slot_count",
        "proof_relevant_actor_count", "proof_relevant_actor_rows",
        "anchor_actor_count", "anchor_actor_rows", "subject_actor_count",
        "subject_actor_rows", "route_actor_count", "route_actor_rows",
        "unexpected_proof_tagged_actor_count", "unexpected_proof_tagged_actor_rows",
        "pawn_count", "pawn_rows", "controller_count", "controller_rows",
        "auto_receive_input_actor_count", "auto_receive_input_actor_rows",
        "phase_4_actor_input_binding_count", "phase_4_actor_input_binding_rows",
        "observation_source",
    ),
    "receipt_schema: CrossDomainOccupancyMaterializationReceipt.v1": (
        "receipt_schema", "proof_scenario", "operation_id", "operation",
        "materialize_command_raw_sha256", "operation_invocation_raw_sha256",
        "domain_role", "operational_process_instance_id",
        "process_binding_raw_sha256", "accepted_canonical_payload_raw_sha256",
        "accepted_canonical_hash", "accepted_projection_raw_sha256",
        "accepted_projection_id", "projected_canonical_site_id",
        "projected_site_representation_slot", "projected_subject_representation_slot",
        "canonical_occupant_id",
        "canonical_occupancy_kind", "canonical_occupancy_reference",
        "derived_local_subject_disposition", "publication_generation",
        "published_anchor_actor_count", "published_anchor_actor_rows",
        "published_subject_actor_count", "published_subject_actor_rows",
        "representation_publication_state", "receipt_authority",
    ),
    "disposition_schema: CrossDomainOccupancyHeadDisposition.v1": (
        "disposition_schema", "proof_scenario", "domain_role",
        "operational_process_instance_id", "process_binding_raw_sha256",
        "expected_representation_raw_sha256", "materialization_receipt_raw_sha256",
        "live_observation_raw_sha256", "represented_canonical_hash",
        "harness_observed_current_canonical_hash",
        "physical_current_head_guard_state", "head_state", "head_relation",
        "local_subject_disposition", "anchor_verified", "subject_census_verified",
        "current_head_representation_claim_enabled", "refresh_enabled",
        "inspection_enabled", "local_nonconsequential_step_enabled",
        "diagnostics_enabled", "termination_enabled", "local_publication_enabled",
        "peer_interaction_enabled", "canonical_evidence_enabled",
        "canonical_scheduling_enabled", "canonical_mutation_enabled",
        "canonical_completion_enabled", "canonical_truth_publication_enabled",
        "reason_code",
    ),
}

EXPECTED_MATERIALIZATION_STAGES = (
    "M01_receive_and_parse_command",
    "M02_resolve_role_private_bundle_root",
    "M03_inventory_exact_three_file_directory",
    "M04_open_and_pre_stat_payload",
    "M05_read_and_post_stat_payload",
    "M06_authenticate_and_validate_payload",
    "M07_open_and_pre_stat_projection",
    "M08_read_and_post_stat_projection",
    "M09_authenticate_and_validate_projection",
    "M10_open_and_pre_stat_invocation",
    "M11_read_and_post_stat_invocation",
    "M12_validate_operation_tuple_and_process_binding",
    "M13_derive_local_subject_disposition",
    "M14_construct_private_anchor_values",
    "M15_construct_private_subject_values",
    "M16_validate_candidate_coherence_and_cardinality",
    "M17_begin_publication_linearization_interval",
    "M18_destroy_and_verify_predecessor_generation_absent",
    "M19_spawn_configure_and_finish_target_subject_set",
    "M20_spawn_configure_and_finish_target_anchor",
    "M21_enumerate_and_validate_adapter_visible_generation",
    "M22_emit_materialization_receipt",
    "M23_router_forward_receipt",
)
EXPECTED_OBSERVATION_STAGES = (
    "O01_receive_and_parse_inspection_command",
    "O02_verify_original_process_binding",
    "O03_select_exact_process_bound_game_world",
    "O04_enumerate_all_loaded_level_actor_slots",
    "O05_classify_all_phase4_relevant_actor_rows",
    "O06_inventory_all_pawn_controller_and_input_rows",
    "O07_sort_and_cross_check_counts_with_lists",
    "O08_construct_closed_live_observation",
    "O09_emit_live_observation",
    "O10_router_forward_live_observation",
    "O11_harness_derive_independent_expected_representation",
    "O12_harness_compare_expectation_receipt_observation_head_binding_guard",
)
EXPECTED_SOURCE_CHECKS = (
    "S01_exact_phase2_discovery_entrypoint_only",
    "S02_exact_phase2_resolver_entrypoint_only",
    "S03_no_phase4_canonical_write_capability",
    "S04_expected_constructor_exact_input_signature",
    "S05_expected_constructor_field_by_field_mapping",
    "S06_adapter_disposition_exact_input_signature",
    "S07_projection_contains_no_expected_result",
    "S08_receipt_contains_no_synchronized_claim",
    "S09_probe_has_no_adapter_or_expected_pointer",
    "S10_probe_exhaustive_world_enumeration",
    "S11_head_observer_harness_private_only",
    "S12_guard_has_no_canonical_dataflow_edge",
    "S13_complete_argv_environment_cwd_descriptor_census",
    "S14_complete_file_and_bundle_reader_census",
    "S15_no_alternate_command_or_refresh_channel",
    "S16_no_parent_sibling_or_other_domain_path",
    "S17_complete_actor_spawn_destroy_and_lookup_census",
    "S18_zero_pawn_possession_and_phase4_input_path_with_one_inert_controller",
    "S19_no_route_transform_timer_collision_animation_navigation_authority",
    "S20_no_physical_completion_or_successor_path",
    "S21_no_peer_state_or_liveness_input",
    "S22_process_and_harness_fault_channels_reachable_only_in_named_fresh_cases",
    "S23_complete_runtime_command_handler_graph",
    "S24_complete_cpp_call_surface_census",
    "S25_complete_input_api_occurrence_census",
    "S26_exact_translation_unit_byte_identity_set",
    "S27_loaded_image_and_runtime_dependency_inventory",
    "S28_initial_and_final_actor_inventory",
    "S29_all_reachable_phase4_source_is_release_bound",
    "S30_no_network_streaming_world_partition_or_production_path",
)
EXPECTED_AUTHORITY_CASES = tuple(f"A{i:02d}" for i in range(1, 41))
EXPECTED_UNREAL_PATHS = (
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyCommandRouter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyCommandRouter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyProofAdapter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyProofAdapter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyHeadAnchorActor.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyHeadAnchorActor.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancySubjectActor.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancySubjectActor.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyLiveWorldProbe.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyLiveWorldProbe.h",
)
EXPECTED_MUTABLE_NON_ARTIFACT_PATHS = (
    "README.md",
    "Cross-Domain Canonical Occupancy Materialization Proof Evidence - v0.1.0.md",
    "Co-op Open-City FPS Simulation - v0.7 Working Continuation.md",
    "THE_CITY Developer Snapshot - v0.1.0.md",
    "THE_CITY Current Proof State and Repo-Agent Instruction - v0.1.0.md",
    "proof_kernel/cross_domain_canonical_occupancy_materialization.py",
    "proof_kernel/cross_domain_canonical_occupancy_materialization_harness.py",
    "proof_kernel/test_cross_domain_canonical_occupancy_materialization.py",
    "proof_kernel/verify_cross_domain_canonical_occupancy_materialization_release.py",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofGameMode.cpp",
    *EXPECTED_UNREAL_PATHS,
)


class ValidationError(RuntimeError):
    """Raised when a specification invariant is not exact."""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def ordered_list_sha256(values: list[str]) -> str:
    data = json.dumps(values, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(data)


def fenced_block_after(text: str, marker: str, language: str = "yaml") -> str:
    offset = text.find(marker)
    if offset < 0:
        raise ValidationError(f"missing marker: {marker}")
    fence = f"```{language}\n"
    start = text.find(fence, offset)
    if start < 0:
        raise ValidationError(f"missing {language} fence after: {marker}")
    start += len(fence)
    end = text.find("\n```", start)
    if end < 0:
        raise ValidationError(f"unterminated {language} fence after: {marker}")
    return text[start:end]


def fenced_block_containing(text: str, marker: str, language: str = "yaml") -> str:
    offset = text.find(marker)
    if offset < 0:
        raise ValidationError(f"missing marker: {marker}")
    fence = f"```{language}\n"
    fence_start = text.rfind(fence, 0, offset + 1)
    if fence_start < 0:
        raise ValidationError(f"missing containing {language} fence: {marker}")
    start = fence_start + len(fence)
    end = text.find("\n```", offset)
    if end < 0:
        raise ValidationError(f"unterminated containing {language} fence: {marker}")
    require(start <= offset <= end, f"marker is not inside {language} fence: {marker}")
    return text[start:end]


def section_between(text: str, start_marker: str, end_marker: str) -> str:
    start = text.find(start_marker)
    if start < 0:
        raise ValidationError(f"missing section: {start_marker}")
    end = text.find(end_marker, start + len(start_marker))
    if end < 0:
        raise ValidationError(f"missing section end: {end_marker}")
    return text[start:end]


def top_level_keys(block: str) -> list[str]:
    return [
        match.group(1)
        for match in re.finditer(r"^([A-Za-z][A-Za-z0-9_]*):", block, re.MULTILINE)
    ]


def list_members(block: str) -> list[str]:
    return [
        match.group(1)
        for match in re.finditer(r"^  - (.+)$", block, re.MULTILINE)
    ]


def table_lines(section: str, header_prefix: str) -> list[str]:
    lines = section.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.startswith(header_prefix))
    except StopIteration as exc:
        raise ValidationError(f"missing table header: {header_prefix}") from exc
    result: list[str] = []
    for line in lines[start:]:
        if not line.startswith("|"):
            if result:
                break
            continue
        result.append(line)
    return result


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def check_unique_exact(values: list[str], count: int, subject: str) -> None:
    require(len(values) == count, f"{subject} count {len(values)} != {count}")
    require(len(set(values)) == count, f"{subject} contains duplicates")


def validate_text(text: str, *, enforce_complete_hash: bool) -> list[str]:
    checks: list[str] = []

    require(text.startswith("# Cross-Domain Canonical Occupancy Materialization Proof\n"), "title")
    require(EXPECTED_VERSION_HEADER in text, "version header")
    require(EXPECTED_STATUS_HEADER in text, "status header")
    require(EXPECTED_IDENTITY in text, "candidate identity")
    checks.append("headers_and_authority")

    if enforce_complete_hash:
        require(sha256_text(text) == EXPECTED_COMPLETE_SPEC_SHA256, "complete spec digest")
    for marker, expected_digest in EXPECTED_CONTAINING_BLOCK_SHA256.items():
        require(
            sha256_text(fenced_block_containing(text, marker)) == expected_digest,
            f"exact containing block {marker}",
        )
    for marker, expected_digest in EXPECTED_AFTER_BLOCK_SHA256.items():
        require(
            sha256_text(fenced_block_after(text, marker)) == expected_digest,
            f"exact following block {marker}",
        )
    checks.append("complete_document_identity")

    for identity in (
        "638e1accc2076814b1f05458b2a55ecaa0a16232",
        "4e14b39a01ba712bfe559d004b0383fc7d9db7d6",
        "f72d6fbb87bcc5a047db0ab12f7447614ebee1fc",
    ):
        require(identity in text, f"missing predecessor identity {identity}")

    for path, expected in EXPECTED_CANONICAL_RAW.items():
        require(expected in text, f"missing canonical digest {expected}")
        if enforce_complete_hash:
            require(sha256_bytes((ROOT / path).read_bytes()) == expected, f"artifact digest {path}")
    checks.append("predecessor_and_canonical_bindings")

    projection_section = section_between(
        text, "The exact legal matrix is closed:", "Every cross-row"
    )
    projection_table = table_lines(projection_section, "| Domain |")
    require(len(projection_table) == 8, "projection table must have header/separator/six rows")
    for index, (projection_id, digest) in enumerate(
        zip(EXPECTED_PROJECTION_IDS, EXPECTED_PROJECTION_DIGESTS), start=2
    ):
        require(projection_id in projection_table[index], f"projection order {projection_id}")
        require(digest in projection_table[index], f"projection digest {projection_id}")
    json_block = fenced_block_after(text, "The exact canonical JSON bytes", "json")
    json_lines = json_block.splitlines()
    require(len(json_lines) == 6, "projection JSON line count")
    for line, projection_id, digest in zip(
        json_lines, EXPECTED_PROJECTION_IDS, EXPECTED_PROJECTION_DIGESTS
    ):
        require(json.loads(line)["projection_id"] == projection_id, "projection JSON order")
        require(sha256_text(line + "\n") == digest, f"projection JSON digest {projection_id}")
    require(sha256_text(json_block) == EXPECTED_PROJECTION_JSON_LINES_SHA256, "projection block digest")
    checks.append("six_projection_rows")

    binding_block = fenced_block_after(text, "exact ordered 22-member")
    require(tuple(top_level_keys(binding_block)) == EXPECTED_BINDING_FIELDS, "binding field order")
    witness_block = fenced_block_after(text, "The exact witness-ID enum is:")
    witness_ids = list_members(witness_block)
    require(tuple(witness_ids) == EXPECTED_WITNESS_IDS, "witness ID enum")
    require("PB01` through `PB22" in text and "`PB23`" in text, "binding adversaries")
    require(
        "bind_invocation_schema: CrossDomainOccupancyBindInvocation.v1" in text,
        "closed bind invocation",
    )
    liveness_section = section_between(
        text, "The required liveness checkpoints are:", "## Exact physical current-head guard"
    )
    liveness_table = table_lines(liveness_section, "| Checkpoint |")
    require(len(liveness_table) == 11, "nine liveness checkpoints")
    require(
        sha256_text("\n".join(liveness_table)) == EXPECTED_LIVENESS_TABLE_SHA256,
        "liveness table digest",
    )
    checks.append("process_binding_and_adversaries")

    for marker, expected_fields in EXPECTED_SCHEMA_FIELDS.items():
        block = fenced_block_containing(text, marker)
        require(tuple(top_level_keys(block)) == expected_fields, f"schema fields {marker}")
    require("head_state_at_publication: synchronized" not in text, "premature anchor synchronization")
    require("head_state_at_receipt: synchronized" not in text, "premature receipt synchronization")
    require(text.count("representation_publication_state: locally_published_unverified") >= 2,
            "unverified local publication state")
    checks.append("closed_representation_schemas")

    observation_section = section_between(
        text, "### Exact independent live-world census", "## Subject representation law"
    )
    for required in (
        "every non-null Actor slot", "proof_relevant_actor_rows",
        "route_actor_rows", "pawn_rows", "controller_rows",
        "phase_4_actor_input_binding_rows", "wrong-world", "receipt/live agreement without",
        "FCrossDomainOccupancyLiveWorldProbe", "not spawned into the world",
    ):
        require(required in observation_section, f"live census closure {required}")
    checks.append("independent_expectation_and_live_census")

    guard_block = fenced_block_after(text, "The exact states are:")
    require(tuple(top_level_keys(guard_block)) == EXPECTED_GUARD_STATES, "guard states")
    guard_section = section_between(
        text, "## Exact physical current-head guard", "## Exact physical head dispositions"
    )
    guard_table = table_lines(guard_section, "| From |")
    require(len(guard_table) == 8, "guard legal transition table")
    require(
        sha256_text("\n".join(guard_table)) == EXPECTED_GUARD_TRANSITION_TABLE_SHA256,
        "guard transition table digest",
    )
    require("`failed_closed` is absorbing" in guard_section, "absorbing guard")
    require(
        "`closed_for_c1_Rtransit_to_Rfinal` has no normal-success outgoing transition"
        in guard_section,
        "C1 terminal guard",
    )
    hf_table = table_lines(guard_section, "| Case | Head operation |")
    require(len(hf_table) == 20, "head fault table must have 18 rows")
    require(
        sha256_text("\n".join(hf_table)) == EXPECTED_HF_TABLE_SHA256,
        "head fault table digest",
    )
    checks.append("head_observation_and_guard")

    disposition_section = section_between(
        text, "## Exact physical head dispositions", "## Detached launch and refresh input closure"
    )
    permission_table = table_lines(disposition_section, "| Context / reason code |")
    require(len(permission_table) == 13, "permission table must have 11 contexts")
    require(sha256_text("\n".join(permission_table)) == EXPECTED_PERMISSION_TABLE_SHA256,
            "permission table digest")
    require("canonical_completion_enabled: false" in disposition_section, "completion permission false")
    checks.append("dispositions_and_permissions")

    operation_section = section_between(
        text, "## Detached launch and refresh input closure", "## Atomic local publication law"
    )
    operation_table = table_lines(operation_section, "| Role | Operation |")
    require(len(operation_table) == 8, "operation table must have six rows")
    require(sha256_text("\n".join(operation_table)) == EXPECTED_OPERATION_TABLE_SHA256,
            "operation table digest")
    for required in (
        "-CrossDomainOccupancyProof", "openat(O_RDONLY|O_CLOEXEC|O_NOFOLLOW)",
        "CrossDomainOccupancyProcessFaultArmInvocation.v1", "Direct R0 → Rfinal",
        "materialize_invocation_schema: CrossDomainOccupancyMaterializeInvocation.v1",
        "inspection_invocation_schema: CrossDomainOccupancyInspectionInvocation.v1",
        "fault_arm_invocation_schema: CrossDomainOccupancyProcessFaultArmInvocation.v1",
        "harness_fault_plan_schema: CrossDomainOccupancyHarnessFaultPlan.v1",
        "launch_surface_schema: CrossDomainOccupancyLaunchSurface.v1",
        "operation_invocation_raw_sha256",
        "cross-products reject", "no alternate reader", "other-domain path",
    ):
        require(required in operation_section, f"operation/input closure {required}")
    profile_table = table_lines(operation_section, "| Profile |")
    witness_profile_table = table_lines(operation_section, "| Witness | Domain A profile |")
    require(len(profile_table) == 6, "four command profiles")
    require(len(witness_profile_table) == 6, "four witness profile rows")
    require(
        sha256_text("\n".join(profile_table)) == EXPECTED_COMMAND_PROFILE_TABLE_SHA256,
        "command profile table digest",
    )
    require(
        sha256_text("\n".join(witness_profile_table)) == EXPECTED_WITNESS_PROFILE_TABLE_SHA256,
        "witness profile table digest",
    )
    require(
        re.search(r"measured raw\s+SHA-256", operation_section) is not None,
        "measured stdin digest",
    )
    checks.append("operation_tuples_and_input_closure")

    publication_section = section_between(
        text, "## Atomic local publication law", "## Materialization receipt boundary"
    )
    require("begin_publication" in publication_section, "publication start")
    require(
        re.search(r"harness\s+acceptance disposition", publication_section) is not None,
        "claim linearization",
    )
    require("rollback or retry in that process is prohibited" in publication_section,
            "post-publication terminal law")
    checks.append("publication_linearization")

    witness_section = section_between(text, "## Required primary witnesses", "## Required controls")
    primary_witness_table = table_lines(witness_section, "| Witness | R0")
    require(len(primary_witness_table) == 6, "primary witness table")
    require(
        sha256_text("\n".join(primary_witness_table)) == EXPECTED_PRIMARY_WITNESS_TABLE_SHA256,
        "primary witness table digest",
    )
    for witness in ("| W1 |", "| W2 |", "| W3 |", "| W4 |"):
        require(witness in witness_section, f"witness {witness}")
    control_section = section_between(text, "## Required controls", "## Asymmetric failure obligations")
    control_command_table = table_lines(control_section, "| Control / role |")
    control_fault_table = table_lines(control_section, "| Case | Role | Armed operation |")
    require(len(control_command_table) == 12, "control command rows")
    require(len(control_fault_table) == 4, "control fault rows")
    require(
        sha256_text("\n".join(control_command_table)) == EXPECTED_CONTROL_COMMAND_TABLE_SHA256,
        "control command table digest",
    )
    require(
        sha256_text("\n".join(control_fault_table)) == EXPECTED_CONTROL_FAULT_TABLE_SHA256,
        "control fault table digest",
    )
    for control in ("### C1", "### C2", "### C3", "### C4a", "### C4b", "### C5"):
        require(control in control_section, f"control {control}")
    asym_section = section_between(
        text, "## Asymmetric failure obligations", "## Current-head and occupancy authority adversaries"
    )
    for case in ("AF01", "AF02", "AF03", "AF04"):
        require(case in asym_section, f"asymmetric case {case}")
    checks.append("witness_control_failure_matrix")

    authority_section = section_between(
        text, "## Current-head and occupancy authority adversaries", "## Failure atomicity"
    )
    authority_table = table_lines(authority_section, "| Case |")
    authority_cases = tuple(re.findall(r"^\| (A\d{2}) \|", "\n".join(authority_table), re.MULTILINE))
    require(authority_cases == EXPECTED_AUTHORITY_CASES, "authority case order")
    require("121 executed subcases" in text, "authority subcase count")
    require(sha256_text("\n".join(authority_table)) == EXPECTED_AUTHORITY_TABLE_SHA256,
            "authority table digest")
    checks.append("authority_adversary_table")

    fault_section = section_between(text, "## Failure atomicity", "## Canonical equivalence and replay")
    materialization_block = fenced_block_after(fault_section, "The 23 ordered materialization stages")
    materialization_stages = tuple(list_members(materialization_block))
    require(materialization_stages == EXPECTED_MATERIALIZATION_STAGES, "materialization stages")
    observation_block = fenced_block_after(fault_section, "The 12 ordered live observation")
    observation_stages = tuple(list_members(observation_block))
    require(observation_stages == EXPECTED_OBSERVATION_STAGES, "observation stages")
    of_table = table_lines(fault_section, "| Case | Context / inspection |")
    require(len(of_table) == 38, "observation fault table must have 36 rows")
    require(
        sha256_text("\n".join(of_table)) == EXPECTED_OF_TABLE_SHA256,
        "observation fault table digest",
    )
    for count in ("MF001`–`MF138", "OF001`–`OF036", "HF01`–`HF18",
                  "PB01`–`PB23"):
        require(count in fault_section, f"fault count {count}")
    checks.append("fault_matrices")

    provenance_section = section_between(
        text, "## Provenance and source/dataflow audit",
        "## Exact implementation, evidence, and release boundary proposed for freeze",
    )
    source_block = fenced_block_after(provenance_section, "exactly these 30 positive checks")
    source_checks = tuple(list_members(source_block))
    require(source_checks == EXPECTED_SOURCE_CHECKS, "source checks")
    require("Exactly 18 source mutations" in provenance_section, "source mutation count")
    require("CrossDomainOccupancyProcessOccurrenceRegistry.v1" in provenance_section,
            "process registry")
    checks.append("provenance_and_source_audit")

    artifact_block = fenced_block_after(text, "these 82 regular non-link files")
    artifacts = list_members(artifact_block)
    check_unique_exact(artifacts, 82, "artifact list")
    require(ordered_list_sha256(artifacts) == EXPECTED_ARTIFACT_LIST_SHA256,
            "artifact list digest")
    checks.append("artifact_set")

    release_block = fenced_block_after(text, "these exact 90 paths")
    group_markers = (
        "governing_and_predecessor_members:", "sealed_canonical_input_members:",
        "python_source_members:", "unreal_project_members:",
    )
    groups: list[list[str]] = []
    for index, marker in enumerate(group_markers):
        start = release_block.find(marker)
        require(start >= 0, f"release group {marker}")
        end = (
            release_block.find(group_markers[index + 1], start)
            if index + 1 < len(group_markers)
            else len(release_block)
        )
        groups.append(list_members(release_block[start:end]))
    require(tuple(map(len, groups)) == (20, 5, 13, 52), "release group counts")
    non_artifacts = [item for group in groups for item in group]
    check_unique_exact(non_artifacts, 90, "non-artifact list")
    require(not set(non_artifacts).intersection(artifacts), "artifact/non-artifact overlap")
    require(ordered_list_sha256(non_artifacts) == EXPECTED_NON_ARTIFACT_LIST_SHA256,
            "non-artifact list digest")
    require(THIS_VALIDATOR not in non_artifacts, "validator included in release")
    require(MANIFEST not in non_artifacts, "manifest included in itself")
    checks.append("release_member_set")

    implementation_block = fenced_block_containing(text, "frozen_implementation_authority:")
    python_members = re.findall(
        r"^    - (.+)$",
        section_between(implementation_block, "  new_python_paths:", "  new_unreal_paths:"),
        re.MULTILINE,
    )
    require(
        tuple(python_members)
        == (
            "proof_kernel/cross_domain_canonical_occupancy_materialization.py",
            "proof_kernel/cross_domain_canonical_occupancy_materialization_harness.py",
            "proof_kernel/test_cross_domain_canonical_occupancy_materialization.py",
            "proof_kernel/verify_cross_domain_canonical_occupancy_materialization_release.py",
        ),
        "four exact new Python paths",
    )
    unreal_members = re.findall(
        r"^    - (.+)$",
        section_between(
            implementation_block,
            "  new_unreal_paths:",
            "  bounded_existing_source_change:",
        ),
        re.MULTILINE,
    )
    require(tuple(unreal_members) == EXPECTED_UNREAL_PATHS, "ten exact new Unreal paths")
    mutable_members = re.findall(
        r"^    - (.+)$",
        section_between(
            implementation_block,
            "  new_or_changed_non_artifact_members:",
            "  new_or_changed_non_artifact_member_count:",
        ),
        re.MULTILINE,
    )
    require(
        tuple(mutable_members) == EXPECTED_MUTABLE_NON_ARTIFACT_PATHS,
        "twenty exact new or changed non-artifact paths",
    )
    require(set(mutable_members).issubset(non_artifacts), "mutable path outside release set")
    require(len(set(non_artifacts).difference(mutable_members)) == 70,
            "unchanged non-artifact set count")
    for exact_authority in (
        "new_or_changed_non_artifact_member_count: 20",
        "unchanged_non_artifact_member_count: 70",
        "frozen_specification_change: prohibited",
        "excluded_operational_record_path: handover.md",
        "excluded_operational_record_authority: informational_handover_updates_only",
    ):
        require(exact_authority in implementation_block, f"implementation authority {exact_authority}")
    require("artifact_member_count: 82" in implementation_block, "artifact authority count")
    require("manifest_member_count_excluding_manifest: 172" in implementation_block,
            "manifest authority count")
    require("capacity_advancement: none" in implementation_block, "capacity authority")
    checks.append("bounded_implementation_authority")

    for required in (
        "focused suite contains exactly 45", "215/215", "33/33", "111/111",
        "30/30 source checks", "18/18 source mutations", "exact 82/172",
        "30 exact in-memory verifier mutations",
    ):
        require(required in text, f"verification contract {required}")
    checks.append("verification_contract")

    forbidden = re.compile(
        r"\bat (?:least|minimum)\b|\bmust choose\b|future_release_contract|"
        r"exact_and_exhaustive|exact_ordered_set|"
        r"implementation_authority:\s*(?:unbounded|unrestricted)|"
        r"head_state_at_(?:publication|receipt): synchronized",
        re.IGNORECASE,
    )
    require(not forbidden.search(text), "unfinished or excessive authority term")
    current = fenced_block_after(text, "## Current decision record")
    for required in (
        "working_unit: Cross-Domain Canonical Occupancy Materialization Proof v0.1.0-draft.1",
        "candidate_simulation_identity: 0.7.0-draft.80",
        "specification_status: final_freeze_review_candidate",
        "freeze_status: not_frozen", "implementation_authority: none",
        "canonical_capacity_change: none",
    ):
        require(required in current, f"current decision {required}")
    require(text.rstrip().endswith(
        "the complete contract and explicitly grants bounded implementation authority."
    ), "terminal authority boundary")
    checks.append("terminal_scope_and_decision")

    require(len(checks) == 20, f"internal check count {len(checks)}")
    return checks


def replace_once(value: str, old: str, new: str) -> str:
    if value.count(old) != 1:
        raise AssertionError(f"self-test target count for {old!r}: {value.count(old)}")
    return value.replace(old, new, 1)


def remove_first_list_member_after(value: str, marker: str) -> str:
    start = value.index(marker)
    match = re.search(r"^  - .+\n", value[start:], re.MULTILINE)
    if not match:
        raise AssertionError(f"list member after {marker}")
    absolute_start = start + match.start()
    absolute_end = start + match.end()
    return value[:absolute_start] + value[absolute_end:]


def duplicate_first_list_member_after(value: str, marker: str) -> str:
    start = value.index(marker)
    match = re.search(r"^  - .+\n", value[start:], re.MULTILINE)
    if not match:
        raise AssertionError(f"list member after {marker}")
    line = match.group(0)
    absolute_end = start + match.end()
    return value[:absolute_end] + line + value[absolute_end:]


def run_self_test(text: str) -> list[str]:
    mutations: list[tuple[str, Callable[[str], str]]] = [
        (
            "version_change",
            lambda s: replace_once(
                s, EXPECTED_VERSION_HEADER, "**Version:** 0.1.0-draft.2\\"
            ),
        ),
        ("authority_grant", lambda s: replace_once(s, EXPECTED_STATUS_HEADER,
             "**Status:** Frozen; implementation authorized\\")),
        ("canonical_digest", lambda s: replace_once(s, EXPECTED_CANONICAL_RAW[next(iter(EXPECTED_CANONICAL_RAW))], "0" * 64)),
        ("projection_missing", lambda s: replace_once(s, json.dumps(json.loads(fenced_block_after(s, "The exact canonical JSON bytes", "json").splitlines()[0]), separators=(",", ":")) + "\n", "")),
        (
            "projection_reordered",
            lambda s: replace_once(
                s,
                "| A | H0_occ | `cross_domain_A_R0_0001` |",
                "| A | H0_occ | `cross_domain_Z_R0_0001` |",
            ),
        ),
        ("binding_field_missing", lambda s: replace_once(s, "diagnostic_pipe_id: exact original stderr-pipe harness identity\n", "")),
        ("binding_field_reordered", lambda s: replace_once(s, "binding_schema: CrossDomainOccupancyProcessBinding.v1\nproof_scenario:", "proof_scenario:")),
        ("witness_duplicate", lambda s: duplicate_first_list_member_after(s, "CrossDomainOccupancyWitnessId.v1:")),
        (
            "premature_sync",
            lambda s: replace_once(
                s,
                "publication_generation: publication_0001 | publication_0002 | publication_0003\n"
                "representation_publication_state: locally_published_unverified",
                "publication_generation: publication_0001 | publication_0002 | publication_0003\n"
                "head_state_at_publication: synchronized",
            ),
        ),
        ("expected_schema_missing", lambda s: replace_once(s, "expected_schema: CrossDomainOccupancyExpectedRepresentation.v1", "expected_schema: Missing.v1")),
        (
            "expected_anchor_value_changed",
            lambda s: replace_once(s, "expected_anchor_actor_count: 1", "expected_anchor_actor_count: 0"),
        ),
        (
            "observation_world_filter_removed",
            lambda s: replace_once(s, "wrong-world", "same-world"),
        ),
        ("world_type_changed", lambda s: replace_once(s, "world_type: Game", "world_type: Editor")),
        (
            "receipt_authority_escalated",
            lambda s: replace_once(
                s,
                "receipt_authority: representation_only",
                "receipt_authority: canonical_truth",
            ),
        ),
        (
            "direct_catchup_tuple",
            lambda s: replace_once(
                s,
                "| A | `refresh_once` | Rtransit → Rfinal |",
                "| A | `refresh_once` | R0 → Rfinal |",
            ),
        ),
        ("alternate_channel", lambda s: replace_once(s, "no alternate reader", "one alternate reader")),
        ("guard_state_missing", lambda s: replace_once(s, "failed_closed:\n", "failed_state:\n")),
        (
            "guard_target_redirected",
            lambda s: replace_once(s, "refresh_target: Hfinal_occ", "refresh_target: H0_occ"),
        ),
        ("binding_pid_negative", lambda s: replace_once(s, "pid: positive integer", "pid: negative integer")),
        ("permission_flip", lambda s: replace_once(s, "| `invalid / local_publication_unprovable` | no |", "| `invalid / local_publication_unprovable` | yes |")),
        ("control_missing", lambda s: replace_once(s, "### C4b — completion guard-open canonical control", "### merged guard-open control")),
        ("authority_row_missing", lambda s: replace_once(s, "| A40 |", "| Z40 |")),
        ("fault_stage_missing", lambda s: replace_once(s, "  - M23_router_forward_receipt\n", "")),
        (
            "fault_stage_authority_renamed",
            lambda s: replace_once(
                s,
                "M18_destroy_and_verify_predecessor_generation_absent",
                "M18_publish_canonical_successor",
            ),
        ),
        (
            "source_check_authority_renamed",
            lambda s: replace_once(
                s,
                "S03_no_phase4_canonical_write_capability",
                "S03_grant_phase4_canonical_write_capability",
            ),
        ),
        ("artifact_missing", lambda s: remove_first_list_member_after(s, "artifact_names:")),
        ("artifact_duplicate", lambda s: duplicate_first_list_member_after(s, "artifact_names:")),
        ("member_missing", lambda s: remove_first_list_member_after(s, "governing_and_predecessor_members:")),
        ("validator_self_include", lambda s: replace_once(s, "  - proof_kernel/kernel.py\n", f"  - {THIS_VALIDATOR}\n  - proof_kernel/kernel.py\n")),
        (
            "manifest_self_include",
            lambda s: replace_once(
                s,
                "governing_and_predecessor_members:\n  - README.md\n",
                f"governing_and_predecessor_members:\n  - {MANIFEST}\n  - README.md\n",
            ),
        ),
        (
            "unreal_authority_path_redirected",
            lambda s: replace_once(
                s,
                "    - CityMaterializationProof/Source/CityMaterializationProof/"
                "CrossDomainOccupancyLiveWorldProbe.cpp\n"
                "    - CityMaterializationProof/Source/CityMaterializationProof/"
                "CrossDomainOccupancyLiveWorldProbe.h\n"
                "  bounded_existing_source_change:\n",
                "    - CityMaterializationProof/Source/CityMaterializationProof/"
                "CrossDomainCanonicalAuthority.cpp\n"
                "    - CityMaterializationProof/Source/CityMaterializationProof/"
                "CrossDomainOccupancyLiveWorldProbe.h\n"
                "  bounded_existing_source_change:\n",
            ),
        ),
        ("terminal_override", lambda s: s + "\nimplementation_authority: unrestricted\n"),
    ]
    rejected: list[str] = []
    for name, mutate in mutations:
        candidate = mutate(text)
        if candidate == text:
            raise AssertionError(f"mutation {name} changed nothing")
        try:
            validate_text(candidate, enforce_complete_hash=False)
        except ValidationError:
            rejected.append(name)
        else:
            raise AssertionError(f"mutation survived: {name}")
    if len(rejected) != 32:
        raise AssertionError(f"self-test count {len(rejected)} != 32")
    return rejected


def main(argv: list[str]) -> int:
    if argv not in ([], ["--self-test"]):
        print("usage: validate_cross_domain_canonical_occupancy_materialization_spec.py [--self-test]", file=sys.stderr)
        return 2
    text = SPEC.read_text(encoding="utf-8")
    try:
        checks = validate_text(text, enforce_complete_hash=True)
        if argv == ["--self-test"]:
            rejected = run_self_test(text)
            print(
                f"validated {len(checks)}/20 specification checks; "
                f"rejected {len(rejected)}/32 in-memory mutations"
            )
        else:
            print(f"validated {len(checks)}/20 specification checks")
    except (ValidationError, AssertionError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
