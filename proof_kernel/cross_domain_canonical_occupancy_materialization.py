#!/usr/bin/env python3
"""Frozen Phase-4 cross-domain canonical occupancy proof kernel.

The canonical scheduler and resolver remain owned by
``canonical_occupancy_transition``.  This module validates their exact sealed
records and constructs only disposable, process-bound representation evidence.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import stat
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from canonical_occupancy_transition import (
    canonical_hash as phase2_canonical_hash,
    load_canonical_record_bytes,
    next_consequential_boundary,
    resolve_next_due,
    validate_canonical_record,
)


ROOT = Path(__file__).resolve().parent.parent
RECORDS = ROOT / "proof_kernel" / "CanonicalOccupancyTransitionProofRecords"

PROOF_SCHEMA = "CrossDomainCanonicalOccupancyMaterializationProof.v1"
PROOF_SCENARIO = "cross-domain-canonical-occupancy-materialization-v1"
PROOF_VERSION = "0.1.0"
SIMULATION_IDENTITY = "0.7.0-draft.80"

R0_ROLE = "R0"
RTRANSIT_ROLE = "Rtransit"
RFINAL_ROLE = "Rfinal"
RECORD_ROLES = (R0_ROLE, RTRANSIT_ROLE, RFINAL_ROLE)
DOMAIN_ROLES = ("domain_A", "domain_B")

H0 = "b31e7ad0993e288ba80f50fb1960da5c67bad9bcc7cc39bf0ec0ebeeaad57dc8"
HTRANSIT = "2640fe567b343e2229f875c9cf2d081f41aaaec2a3834e81e2efb3f9caa5da19"
HFINAL = "3a00d32115af74950923ac3362a8459d0e08043d45abbe91bcc573e27103db34"
D0 = "59ce47bc4d6c63cbda4a740fec8d25e497ca8ed74052b16b5358745be115c2dc"
DTRANSIT = "215e3383bff21a9fe01dbb240035a0fa5dd774c703417486846e027a0615a12f"
DFINAL = "0b4d9d97eb166b3aae6480c5581654c39b367c3a5fab47a02daec50b1e88a181"

HEAD_HASHES = {R0_ROLE: H0, RTRANSIT_ROLE: HTRANSIT, RFINAL_ROLE: HFINAL}
RAW_HASHES = {R0_ROLE: D0, RTRANSIT_ROLE: DTRANSIT, RFINAL_ROLE: DFINAL}
RECORD_FILENAMES = {
    R0_ROLE: "canonical_occupancy_transition_R0.json",
    RTRANSIT_ROLE: "canonical_occupancy_transition_Rtransit.json",
    RFINAL_ROLE: "canonical_occupancy_transition_Rfinal.json",
}
BOUNDARY_FILENAMES = {
    "start": "canonical_occupancy_transition_start_boundary_H0.json",
    "completion": "canonical_occupancy_transition_completion_boundary_Htransit.json",
}

SITE_A = "topology_site_0001"
SITE_B = "topology_site_0002"
ROUTE = "topology_route_0001"
OCCUPANT = "topology_occupant_0001"
TRANSITION = "occupancy_transition_0001"
RESERVATION = "occupancy_reservation_topology_occupant_0001"

PROJECTION_SCHEMA = "CrossDomainCanonicalOccupancyProjection.v1"
EXPECTED_SCHEMA = "CrossDomainOccupancyExpectedRepresentation.v1"
PROCESS_BINDING_SCHEMA = "CrossDomainOccupancyProcessBinding.v1"
BIND_INVOCATION_SCHEMA = "CrossDomainOccupancyBindInvocation.v1"
LAUNCH_PLAN_SCHEMA = "CrossDomainOccupancyLaunchPlan.v1"
OPERATION_INVOCATION_SCHEMA = "CrossDomainOccupancyOperationInvocation.v1"
MATERIALIZE_INVOCATION_SCHEMA = "CrossDomainOccupancyMaterializeInvocation.v1"
INSPECTION_INVOCATION_SCHEMA = "CrossDomainOccupancyInspectionInvocation.v1"
FAULT_ARM_INVOCATION_SCHEMA = "CrossDomainOccupancyProcessFaultArmInvocation.v1"
FAULT_ARM_RECEIPT_SCHEMA = "CrossDomainOccupancyProcessFaultArmReceipt.v1"
HARNESS_FAULT_PLAN_SCHEMA = "CrossDomainOccupancyHarnessFaultPlan.v1"
HARNESS_FAULT_ARM_RECEIPT_SCHEMA = "CrossDomainOccupancyHarnessFaultArmReceipt.v1"
LIVENESS_PLAN_SCHEMA = "CrossDomainOccupancyLivenessAdversaryPlan.v1"
LIVENESS_INVOCATION_SCHEMA = "CrossDomainOccupancyLivenessAdversaryInvocation.v1"
LIVENESS_ARM_RECEIPT_SCHEMA = "CrossDomainOccupancyLivenessAdversaryArmReceipt.v1"
LIVENESS_OBSERVATION_SCHEMA = "CrossDomainOccupancyLivenessObservation.v1"
LIVENESS_REPORT_SCHEMA = "CrossDomainOccupancyLivenessAdversarialReport.v1"
ANCHOR_SCHEMA = "CrossDomainOccupancyHeadAnchor.v1"
SUBJECT_SCHEMA = "CrossDomainOccupancySubjectRepresentation.v1"
LIVE_OBSERVATION_SCHEMA = "CrossDomainOccupancyLiveObservation.v1"
HEAD_OBSERVATION_SCHEMA = "CrossDomainOccupancyCanonicalHeadObservation.v1"
MATERIALIZATION_RECEIPT_SCHEMA = "CrossDomainOccupancyMaterializationReceipt.v1"
DISPOSITION_SCHEMA = "CrossDomainOccupancyHeadDisposition.v1"
RUNTIME_TRACE_SCHEMA = "CrossDomainOccupancyRuntimeTraceEvent.v1"
HARNESS_TRACE_SCHEMA = "CrossDomainOccupancyHarnessTraceEvent.v1"

PROJECTION_ROWS: dict[tuple[str, str], dict[str, str]] = {
    ("domain_A", R0_ROLE): {
        "projection_id": "cross_domain_A_R0_0001",
        "site": SITE_A,
        "site_slot": "domain_A_site_slot_01",
        "subject_slot": "domain_A_subject_slot_01",
        "raw_sha256": "c175ee92a3c69adbbeebaeecdabb54e462bbea1aa99f43117c5205757bcc9624",
    },
    ("domain_B", R0_ROLE): {
        "projection_id": "cross_domain_B_R0_0001",
        "site": SITE_B,
        "site_slot": "domain_B_site_slot_01",
        "subject_slot": "domain_B_subject_slot_01",
        "raw_sha256": "4d8da172945e1ff97433fe6230290f448d8731ac0dd5d3cef421e806b43531cb",
    },
    ("domain_A", RTRANSIT_ROLE): {
        "projection_id": "cross_domain_A_Rtransit_0001",
        "site": SITE_A,
        "site_slot": "domain_A_site_slot_01",
        "subject_slot": "domain_A_subject_slot_01",
        "raw_sha256": "1f57d0fc964956275008fffeb82adbb365f7c3343cce76d90e5cbd53262d68e6",
    },
    ("domain_B", RTRANSIT_ROLE): {
        "projection_id": "cross_domain_B_Rtransit_0001",
        "site": SITE_B,
        "site_slot": "domain_B_site_slot_01",
        "subject_slot": "domain_B_subject_slot_01",
        "raw_sha256": "1e72049befcbd9d1af6babaf855440c14101faa2d4aa5b97d13b9ae859d8d5dc",
    },
    ("domain_A", RFINAL_ROLE): {
        "projection_id": "cross_domain_A_Rfinal_0001",
        "site": SITE_A,
        "site_slot": "domain_A_site_slot_01",
        "subject_slot": "domain_A_subject_slot_01",
        "raw_sha256": "723d9e539f3e0cebdab418dfacb25f8f2d6bbc0acd42c85a5330dca322a5e6c8",
    },
    ("domain_B", RFINAL_ROLE): {
        "projection_id": "cross_domain_B_Rfinal_0001",
        "site": SITE_B,
        "site_slot": "domain_B_site_slot_01",
        "subject_slot": "domain_B_subject_slot_01",
        "raw_sha256": "1552fb88285ffe670f1866ac324ef4b61c51d4ec2c4977df84e23b97e8eb85b9",
    },
}

OPERATION_ROWS: dict[tuple[str, str], dict[str, Any]] = {}
for _role in DOMAIN_ROLES:
    OPERATION_ROWS[(_role, "launch_0001")] = {
        "operation": "materialize_initial",
        "source_role": None,
        "target_role": R0_ROLE,
        "bundle_root": "launch_input/launch_0001",
        "payload_file": "canonical_occupancy_R0.json",
        "projection_file": f"cross_domain_{'A' if _role == 'domain_A' else 'B'}_R0_projection.json",
        "invocation_file": f"cross_domain_{'A' if _role == 'domain_A' else 'B'}_launch_R0_invocation.json",
        "generation": "publication_0001",
    }
    OPERATION_ROWS[(_role, "refresh_0001")] = {
        "operation": "refresh_once",
        "source_role": R0_ROLE,
        "target_role": RTRANSIT_ROLE,
        "bundle_root": "refresh_input/refresh_0001",
        "payload_file": "canonical_occupancy_Rtransit.json",
        "projection_file": f"cross_domain_{'A' if _role == 'domain_A' else 'B'}_Rtransit_projection.json",
        "invocation_file": f"cross_domain_{'A' if _role == 'domain_A' else 'B'}_refresh_Rtransit_invocation.json",
        "generation": "publication_0002",
    }
    OPERATION_ROWS[(_role, "refresh_0002")] = {
        "operation": "refresh_once",
        "source_role": RTRANSIT_ROLE,
        "target_role": RFINAL_ROLE,
        "bundle_root": "refresh_input/refresh_0002",
        "payload_file": "canonical_occupancy_Rfinal.json",
        "projection_file": f"cross_domain_{'A' if _role == 'domain_A' else 'B'}_Rfinal_projection.json",
        "invocation_file": f"cross_domain_{'A' if _role == 'domain_A' else 'B'}_refresh_Rfinal_invocation.json",
        "generation": "publication_0003",
    }

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

WITNESS_IDS = (
    "w1_A_B__A_B", "w2_B_A__B_A", "w3_A_B__B_A", "w4_B_A__A_B",
    "c1_canonical_completion_independence", "c2_positive_Rtransit_absence",
    "c3_receipt_only_rejection", "c4a_start_guard_open",
    "c4b_completion_guard_open", "c5_process_replacement",
    "af_Rtransit_A_success_B_failure", "af_Rtransit_B_success_A_failure",
    "af_Rfinal_A_success_B_failure", "af_Rfinal_B_success_A_failure",
    "fault_head_publication", "fault_materialization", "fault_live_observation",
    "authority_adversary", "process_binding_adversary", "liveness_adversary",
    "replay_repeat",
)

GUARD_STATES = (
    "open_for_R0", "closed_for_R0_to_Rtransit", "open_for_Rtransit",
    "closed_for_Rtransit_to_Rfinal", "closed_for_c1_Rtransit_to_Rfinal",
    "open_for_Rfinal", "failed_closed",
)

MATERIALIZATION_STAGES = tuple(
    f"M{i:02d}_{name}" for i, name in enumerate((
        "receive_and_parse_command", "resolve_role_private_bundle_root",
        "inventory_exact_three_file_directory", "open_and_pre_stat_payload",
        "read_and_post_stat_payload", "authenticate_and_validate_payload",
        "open_and_pre_stat_projection", "read_and_post_stat_projection",
        "authenticate_and_validate_projection", "open_and_pre_stat_invocation",
        "read_and_post_stat_invocation", "validate_operation_tuple_and_process_binding",
        "derive_local_subject_disposition", "construct_private_anchor_values",
        "construct_private_subject_values", "validate_candidate_coherence_and_cardinality",
        "begin_publication_linearization_interval",
        "destroy_and_verify_predecessor_generation_absent",
        "spawn_configure_and_finish_target_subject_set",
        "spawn_configure_and_finish_target_anchor",
        "enumerate_and_validate_adapter_visible_generation",
        "emit_materialization_receipt", "router_forward_receipt",
    ), 1)
)

LIVE_OBSERVATION_STAGES = tuple(
    f"O{i:02d}_{name}" for i, name in enumerate((
        "receive_and_parse_inspection_command", "verify_original_process_binding",
        "select_exact_process_bound_game_world", "enumerate_all_loaded_level_actor_slots",
        "classify_all_phase4_relevant_actor_rows",
        "inventory_all_pawn_controller_and_input_rows",
        "sort_and_cross_check_counts_with_lists", "construct_closed_live_observation",
        "emit_live_observation", "router_forward_live_observation",
        "harness_derive_independent_expected_representation",
        "harness_compare_expectation_receipt_observation_head_binding_guard",
    ), 1)
)

HEAD_PUBLICATION_STAGES = (
    "open_source", "pre_stat_source", "read_source_once", "post_stat_source",
    "authenticate_record", "construct_private_observation",
    "write_and_fsync_candidate", "atomic_publish", "reopen_and_reverify",
)

PRIMARY_REFRESH_ORDERS = {
    "W1": (("domain_A", "domain_B"), ("domain_A", "domain_B")),
    "W2": (("domain_B", "domain_A"), ("domain_B", "domain_A")),
    "W3": (("domain_A", "domain_B"), ("domain_B", "domain_A")),
    "W4": (("domain_B", "domain_A"), ("domain_A", "domain_B")),
}

ARTIFACT_NAMES = (
    "cross_domain_occupancy_canonical_chain.json",
    "cross_domain_occupancy_projection_matrix.json",
    "cross_domain_occupancy_operation_tuple_matrix.json",
    "cross_domain_occupancy_guard_and_head_observation_matrix.json",
    *tuple(
        name
        for witness, suffix in (("W1", "A_B__A_B"), ("W2", "B_A__B_A"),
                                ("W3", "A_B__B_A"), ("W4", "B_A__A_B"))
        for name in (
            *tuple(
                f"physical_{witness}_domain_{role}_{head}_{kind}.json"
                for head in ("R0", "Rtransit", "Rfinal")
                for role in ("A", "B")
                for kind in ("materialization_receipt", "live_observation")
            ),
            f"physical_{witness}_liveness_witness.json",
            f"physical_{witness}_{suffix}_witness.json",
        )
    ),
    "control_C1_canonical_completion_independence.json",
    "control_C2_positive_Rtransit_absence.json",
    "control_C3_receipt_only_rejection.json",
    "control_C4a_start_guard_open.json",
    "control_C4b_completion_guard_open.json",
    "control_C5_process_replacement.json",
    "failure_AF01_Rtransit_A_success_B_failure.json",
    "failure_AF02_Rtransit_B_success_A_failure.json",
    "failure_AF03_Rfinal_A_success_B_failure.json",
    "failure_AF04_Rfinal_B_success_A_failure.json",
    "cross_domain_occupancy_process_binding_adversaries.json",
    "cross_domain_occupancy_authority_adversaries.json",
    "cross_domain_occupancy_head_publication_fault_atomicity.json",
    "cross_domain_occupancy_materialization_fault_atomicity.json",
    "cross_domain_occupancy_live_observation_fault_atomicity.json",
    "cross_domain_occupancy_liveness_adversaries.json",
    "cross_domain_occupancy_proof_semantic_input_audit.json",
    "cross_domain_occupancy_canonical_equivalence_oracle.json",
    "cross_domain_occupancy_source_audit.json",
    "cross_domain_occupancy_replay_oracle.json",
    "cross_domain_occupancy_process_occurrence_registry.json",
    "cross_domain_occupancy_proof_run.json",
)


class CrossDomainOccupancyRejected(ValueError):
    """Exact fail-closed rejection with stage and reason identity."""

    def __init__(self, stage: str, reason: str, message: str = "") -> None:
        self.stage = stage
        self.reason = reason
        super().__init__(f"{stage}: {reason}: {message}")


def _reject(stage: str, reason: str, message: str = "") -> CrossDomainOccupancyRejected:
    return CrossDomainOccupancyRejected(stage, reason, message)


def _copy(value: Any) -> Any:
    return copy.deepcopy(value)


def canonical_json(value: Any) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    )


def canonical_json_bytes(value: Any) -> bytes:
    return canonical_json(value).encode("utf-8")


def stored_json_bytes(value: Any) -> bytes:
    return canonical_json_bytes(value) + b"\n"


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_value(value: Any) -> str:
    return sha256_bytes(stored_json_bytes(value))


def is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def strict_load_stored_json(raw: bytes) -> Any:
    if raw.startswith(b"\xef\xbb\xbf") or not raw.endswith(b"\n") or raw.endswith(b"\n\n"):
        raise _reject("parse", "noncanonical_stored_json", "one LF and no BOM required")
    if b"\r" in raw or raw.count(b"\n") != 1:
        raise _reject("parse", "noncanonical_stored_json", "embedded newline")
    try:
        text = raw[:-1].decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise _reject("parse", "invalid_utf8", str(exc)) from exc

    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in values:
            if key in result:
                raise _reject("parse", "duplicate_json_member", key)
            result[key] = value
        return result

    def reject_float(token: str) -> Any:
        raise _reject("parse", "noninteger_json_number", token)

    try:
        value = json.loads(
            text, object_pairs_hook=pairs, parse_float=reject_float,
            parse_constant=reject_float,
        )
    except json.JSONDecodeError as exc:
        raise _reject("parse", "invalid_json", str(exc)) from exc
    if canonical_json(value) != text:
        raise _reject("parse", "noncanonical_stored_json", "round trip differs")
    return value


def _exact_keys(value: Any, expected: Iterable[str], stage: str) -> dict[str, Any]:
    keys = tuple(expected)
    if not isinstance(value, dict) or set(value) != set(keys):
        raise _reject(stage, "invalid_object_members", f"expected {sorted(keys)!r}")
    return value


def canonical_records() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    raw: dict[str, bytes] = {
        role: (RECORDS / RECORD_FILENAMES[role]).read_bytes() for role in RECORD_ROLES
    }
    records = {role: load_canonical_record_bytes(raw[role]) for role in RECORD_ROLES}
    for role in RECORD_ROLES:
        if sha256_bytes(raw[role]) != RAW_HASHES[role]:
            raise AssertionError(f"sealed {role} raw identity drift")
        if phase2_canonical_hash(records[role]) != HEAD_HASHES[role]:
            raise AssertionError(f"sealed {role} canonical identity drift")
        if validate_canonical_record(records[role]):
            raise AssertionError(f"sealed {role} validation drift")

    start = next_consequential_boundary(records[R0_ROLE])
    if start is None or resolve_next_due(records[R0_ROLE], start) != records[RTRANSIT_ROLE]:
        raise AssertionError("sealed Phase-2 start resolver drift")
    completion = next_consequential_boundary(records[RTRANSIT_ROLE])
    if completion is None or resolve_next_due(records[RTRANSIT_ROLE], completion) != records[RFINAL_ROLE]:
        raise AssertionError("sealed Phase-2 completion resolver drift")
    if next_consequential_boundary(records[RFINAL_ROLE]) is not None:
        raise AssertionError("sealed Phase-2 final schedule drift")

    stored_start = strict_load_stored_json((RECORDS / BOUNDARY_FILENAMES["start"]).read_bytes())
    stored_completion = strict_load_stored_json((RECORDS / BOUNDARY_FILENAMES["completion"]).read_bytes())
    if start != stored_start or completion != stored_completion:
        raise AssertionError("sealed Phase-2 boundary drift")
    return (
        _copy(records[R0_ROLE]), _copy(start), _copy(records[RTRANSIT_ROLE]),
        _copy(completion), _copy(records[RFINAL_ROLE]),
    )


def canonical_measurement(record: Mapping[str, Any]) -> dict[str, Any]:
    value = _copy(dict(record))
    errors = validate_canonical_record(value)
    if errors:
        raise _reject("canonical_measurement", "invalid_canonical_record", str(errors))
    provenance = value["causal_provenance"]
    current = value["current_causal_state"]
    future = value["future_causal_state"]
    return {
        "measurement_schema": "CrossDomainOccupancyCanonicalMeasurement.v1",
        "record_raw_sha256": sha256_bytes(stored_json_bytes(value)),
        "record_canonical_hash": phase2_canonical_hash(value),
        "authoritative_ledger": _copy(provenance["authoritative_causal_ledger"]),
        "canonical_ancestry": _copy(provenance["canonical_ancestry"]),
        "reservation_state": _copy(current["occupancy_transition_reservations"][RESERVATION]),
        "transition_state": _copy(current["occupancy_transition_commitments"][TRANSITION]),
        "canonical_occupancy": _copy(current["canonical_occupancy"][OCCUPANT]),
        "unresolved_work": _copy(future["unresolved_work"]),
        "canonical_clock": future["canonical_clock"],
    }


def canonical_chain() -> dict[str, Any]:
    r0, start, rtransit, completion, rfinal = canonical_records()
    return {
        "chain_schema": "CrossDomainOccupancyCanonicalChain.v1",
        "proof_scenario": PROOF_SCENARIO,
        "phase_2_scheduler": "canonical_occupancy_transition.next_consequential_boundary",
        "phase_2_resolver": "canonical_occupancy_transition.resolve_next_due",
        "physical_input_to_scheduler_or_resolver": False,
        "records": {
            R0_ROLE: canonical_measurement(r0),
            RTRANSIT_ROLE: canonical_measurement(rtransit),
            RFINAL_ROLE: canonical_measurement(rfinal),
        },
        "start_boundary": start,
        "completion_boundary": completion,
        "rtransit_bytes_equal_sealed": stored_json_bytes(rtransit) == (RECORDS / RECORD_FILENAMES[RTRANSIT_ROLE]).read_bytes(),
        "rfinal_bytes_equal_sealed": stored_json_bytes(rfinal) == (RECORDS / RECORD_FILENAMES[RFINAL_ROLE]).read_bytes(),
        "completion_rediscovered_from_rtransit": True,
    }


def projection(domain_role: str, record_role: str) -> dict[str, Any]:
    try:
        row = PROJECTION_ROWS[(domain_role, record_role)]
    except KeyError as exc:
        raise _reject("projection_validation", "projection_row_mismatch", f"{domain_role}/{record_role}") from exc
    return {
        "allowed_site_projection": {
            "canonical_site_id": row["site"],
            "representation_slot": row["site_slot"],
        },
        "allowed_subject_projection": {
            "canonical_occupant_id": OCCUPANT,
            "representation_slot": row["subject_slot"],
        },
        "domain_role": domain_role,
        "projection_id": row["projection_id"],
        "projection_schema": PROJECTION_SCHEMA,
        "proof_scenario": PROOF_SCENARIO,
        "source_canonical_hash": HEAD_HASHES[record_role],
    }


def validate_projection(value: Any, domain_role: str, record_role: str) -> dict[str, Any]:
    expected = projection(domain_role, record_role)
    if value != expected:
        raise _reject("M09_authenticate_and_validate_projection", "projection_row_mismatch")
    raw = stored_json_bytes(value)
    if sha256_bytes(raw) != PROJECTION_ROWS[(domain_role, record_role)]["raw_sha256"]:
        raise _reject("M09_authenticate_and_validate_projection", "projection_raw_sha256_not_frozen")
    return _copy(expected)


def projection_matrix() -> dict[str, Any]:
    return {
        "matrix_schema": "CrossDomainOccupancyProjectionMatrix.v1",
        "proof_scenario": PROOF_SCENARIO,
        "rows": [projection(role, record) for record in RECORD_ROLES for role in DOMAIN_ROLES],
        "row_raw_sha256": [PROJECTION_ROWS[(role, record)]["raw_sha256"] for record in RECORD_ROLES for role in DOMAIN_ROLES],
        "occupancy_answer_present_in_projection": False,
    }


def record_role_from_hash(value: str) -> str:
    for role, digest in HEAD_HASHES.items():
        if value == digest:
            return role
    raise _reject("canonical_identity", "unknown_canonical_hash", value)


def operation_invocation(domain_role: str, operation_id: str, operational_id: str) -> dict[str, Any]:
    if not is_sha256(operational_id):
        raise _reject("operation_tuple", "process_identity_invalid")
    try:
        row = OPERATION_ROWS[(domain_role, operation_id)]
    except KeyError as exc:
        raise _reject("operation_tuple", "operation_tuple_mismatch") from exc
    source_role = row["source_role"]
    target_role = row["target_role"]
    p = projection(domain_role, target_role)
    return {
        "domain_role": domain_role,
        "operation": row["operation"],
        "operation_id": operation_id,
        "operational_process_instance_id": operational_id,
        "proof_scenario": PROOF_SCENARIO,
        "publication_generation": row["generation"],
        "source_canonical_hash": None if source_role is None else HEAD_HASHES[source_role],
        "target_canonical_hash": HEAD_HASHES[target_role],
        "target_canonical_payload_raw_sha256": RAW_HASHES[target_role],
        "target_projection_id": p["projection_id"],
        "target_projection_raw_sha256": sha256_value(p),
        "invocation_schema": OPERATION_INVOCATION_SCHEMA,
    }


def operation_tuple_matrix() -> dict[str, Any]:
    placeholder = "0" * 64
    rows = []
    for operation_id in ("launch_0001", "refresh_0001", "refresh_0002"):
        for role in DOMAIN_ROLES:
            row = _copy(OPERATION_ROWS[(role, operation_id)])
            row["domain_role"] = role
            row["operation_invocation"] = operation_invocation(role, operation_id, placeholder)
            rows.append(row)
    return {
        "matrix_schema": "CrossDomainOccupancyOperationTupleMatrix.v1",
        "proof_scenario": PROOF_SCENARIO,
        "rows": rows,
    }


def payload_from_raw(raw: bytes, expected_role: str) -> dict[str, Any]:
    if sha256_bytes(raw) != RAW_HASHES[expected_role]:
        raise _reject("M06_authenticate_and_validate_payload", "sealed_payload_identity_mismatch")
    try:
        value = load_canonical_record_bytes(raw)
    except ValueError as exc:
        raise _reject("M06_authenticate_and_validate_payload", "canonical_shape_mismatch", str(exc)) from exc
    if validate_canonical_record(value) or phase2_canonical_hash(value) != HEAD_HASHES[expected_role]:
        raise _reject("M06_authenticate_and_validate_payload", "canonical_identity_mismatch")
    return value


def derive_occupancy(payload: Mapping[str, Any], projected_site: str) -> tuple[str, str, str]:
    occupancy_map = payload["current_causal_state"]["canonical_occupancy"]
    if set(occupancy_map) != {OCCUPANT}:
        raise _reject("M13_derive_local_subject_disposition", "occupancy_identity_mismatch")
    occupancy = occupancy_map[OCCUPANT]
    if occupancy.get("kind") == "at_site" and set(occupancy) == {"kind", "site_id"}:
        reference = occupancy["site_id"]
        if reference not in (SITE_A, SITE_B):
            raise _reject("M13_derive_local_subject_disposition", "occupancy_identity_mismatch")
        disposition = "present_at_local_site" if reference == projected_site else "remote_at_other_site"
        return "at_site", reference, disposition
    if occupancy.get("kind") == "in_transition" and set(occupancy) == {"kind", "transition_id"}:
        if occupancy["transition_id"] != TRANSITION:
            raise _reject("M13_derive_local_subject_disposition", "occupancy_identity_mismatch")
        return "in_transition", TRANSITION, "in_transition_out_of_domain"
    raise _reject("M13_derive_local_subject_disposition", "occupancy_identity_mismatch")


def expected_representation(payload_raw: bytes, projection_raw: bytes) -> dict[str, Any]:
    payload_digest = sha256_bytes(payload_raw)
    try:
        record_role = next(role for role, digest in RAW_HASHES.items() if digest == payload_digest)
    except StopIteration as exc:
        raise _reject("O11_harness_derive_independent_expected_representation", "sealed_payload_identity_mismatch") from exc
    payload = payload_from_raw(payload_raw, record_role)
    p = strict_load_stored_json(projection_raw)
    domain_role = str(p.get("domain_role", "")) if isinstance(p, dict) else ""
    validate_projection(p, domain_role, record_role)
    row = PROJECTION_ROWS[(domain_role, record_role)]
    kind, reference, disposition = derive_occupancy(payload, row["site"])
    subject_count = 1 if disposition == "present_at_local_site" else 0
    return {
        "canonical_hash": HEAD_HASHES[record_role],
        "canonical_occupancy_kind": kind,
        "canonical_occupancy_reference": reference,
        "canonical_occupant_id": OCCUPANT,
        "canonical_payload_raw_sha256": payload_digest,
        "domain_role": domain_role,
        "expectation_source": "independently_authenticated_payload_and_projection_only",
        "expected_anchor_actor_count": 1,
        "expected_auto_receive_input_actor_count": 0,
        "expected_controller_count": 1,
        "expected_local_subject_disposition": disposition,
        "expected_pawn_count": 0,
        "expected_phase_4_actor_input_binding_count": 0,
        "expected_proof_relevant_actor_count": 1 + subject_count,
        "expected_route_actor_count": 0,
        "expected_subject_actor_count": subject_count,
        "expected_unexpected_proof_tagged_actor_count": 0,
        "expected_schema": EXPECTED_SCHEMA,
        "projected_canonical_site_id": row["site"],
        "projected_site_representation_slot": row["site_slot"],
        "projected_subject_representation_slot": row["subject_slot"],
        "projection_id": row["projection_id"],
        "projection_raw_sha256": sha256_bytes(projection_raw),
        "proof_scenario": PROOF_SCENARIO,
    }


def process_binding(instance: Mapping[str, Any]) -> dict[str, Any]:
    required_without_schema = tuple(field for field in PROCESS_BINDING_FIELDS if field != "binding_schema")
    _exact_keys(instance, required_without_schema, "process_binding_identity_verification")
    value = {"binding_schema": PROCESS_BINDING_SCHEMA, **_copy(dict(instance))}
    if value["proof_scenario"] != PROOF_SCENARIO or value["witness_id"] not in WITNESS_IDS:
        raise _reject("process_binding_identity_verification", "binding_identity_mismatch")
    if value["domain_role"] not in DOMAIN_ROLES:
        raise _reject("process_binding_identity_verification", "domain_binding_mismatch")
    if value["harness_launch_id"] != f"{value['witness_id']}/{value['domain_role']}/launch_0001":
        raise _reject("process_binding_identity_verification", "binding_launch_mismatch")
    if type(value["pid"]) is not int or value["pid"] <= 0:
        raise _reject("process_binding_identity_verification", "binding_pid_invalid")
    start = value["macos_process_start"]
    if (
        not isinstance(start, dict) or set(start) != {"seconds", "microseconds"}
        or type(start["seconds"]) is not int or start["seconds"] < 0
        or type(start["microseconds"]) is not int or not 0 <= start["microseconds"] <= 999999
    ):
        raise _reject("process_binding_identity_verification", "binding_process_start_invalid")
    if value["entry_map_package_identity"] != "/Engine/Maps/Entry":
        raise _reject("process_binding_identity_verification", "entry_map_mismatch")
    for field in (
        "executable_raw_sha256", "project_raw_sha256",
        "project_config_and_module_inventory_raw_sha256", "launch_argv_raw_sha256",
        "launch_environment_audit_raw_sha256", "inherited_descriptor_map_raw_sha256",
    ):
        if not is_sha256(value[field]):
            raise _reject("process_binding_identity_verification", "binding_digest_invalid", field)
    for field in ("executable_realpath", "project_realpath", "process_root_realpath", "launch_cwd_realpath"):
        if not isinstance(value[field], str) or not value[field].startswith("/") or "/../" in value[field]:
            raise _reject("process_binding_identity_verification", "binding_path_invalid", field)
    return value


def operational_process_instance_id(binding: Mapping[str, Any]) -> str:
    _exact_keys(binding, PROCESS_BINDING_FIELDS, "process_binding_identity_verification")
    return sha256_bytes(canonical_json_bytes(dict(binding)))


def process_binding_raw_sha256(binding: Mapping[str, Any]) -> str:
    _exact_keys(binding, PROCESS_BINDING_FIELDS, "process_binding_identity_verification")
    return sha256_value(dict(binding))


def bind_invocation(binding: Mapping[str, Any]) -> dict[str, Any]:
    value = _copy(dict(binding))
    return {
        "bind_invocation_schema": BIND_INVOCATION_SCHEMA,
        "command_sequence": 0,
        "operational_process_instance_id": operational_process_instance_id(value),
        "process_binding": value,
        "process_binding_raw_sha256": process_binding_raw_sha256(value),
        "proof_scenario": PROOF_SCENARIO,
    }


def launch_plan(
    witness_id: str, domain_role: str, process_root: str,
    control_pipe_id: str, output_pipe_id: str, diagnostic_pipe_id: str,
) -> dict[str, Any]:
    if witness_id not in WITNESS_IDS or domain_role not in DOMAIN_ROLES:
        raise _reject("launch_plan", "launch_identity_invalid")
    return {
        "control_pipe_id": control_pipe_id,
        "diagnostic_pipe_id": diagnostic_pipe_id,
        "domain_role": domain_role,
        "harness_launch_id": f"{witness_id}/{domain_role}/launch_0001",
        "launch_plan_schema": LAUNCH_PLAN_SCHEMA,
        "process_root_realpath": process_root,
        "proof_scenario": PROOF_SCENARIO,
        "structured_output_pipe_id": output_pipe_id,
        "witness_id": witness_id,
    }


def materialize_invocation(command_sequence: int, operation_id: str) -> dict[str, Any]:
    if type(command_sequence) is not int or command_sequence <= 0:
        raise _reject("M01_receive_and_parse_command", "command_sequence_invalid")
    row = next((row for (role, op), row in OPERATION_ROWS.items() if op == operation_id), None)
    if row is None:
        raise _reject("M01_receive_and_parse_command", "operation_tuple_mismatch")
    return {
        "command_sequence": command_sequence,
        "materialize_invocation_schema": MATERIALIZE_INVOCATION_SCHEMA,
        "operation": row["operation"],
        "operation_id": operation_id,
        "proof_scenario": PROOF_SCENARIO,
        "relative_bundle_root": row["bundle_root"],
    }


INSPECTION_IDS = tuple(f"inspection_{i:04d}" for i in range(1, 10)) + (
    "inspection_c1_terminal_0001", "inspection_c2_rejection_0001",
    "inspection_c3_rejection_0001",
)


def inspection_invocation(command_sequence: int, inspection_id: str) -> dict[str, Any]:
    if type(command_sequence) is not int or command_sequence <= 0 or inspection_id not in INSPECTION_IDS:
        raise _reject("O01_receive_and_parse_inspection_command", "inspection_command_invalid")
    return {
        "command_sequence": command_sequence,
        "inspection_id": inspection_id,
        "inspection_invocation_schema": INSPECTION_INVOCATION_SCHEMA,
        "operation": "inspect_published_occupancy_once",
        "proof_scenario": PROOF_SCENARIO,
    }


def bundle_file_names(domain_role: str, operation_id: str) -> tuple[str, str, str]:
    try:
        row = OPERATION_ROWS[(domain_role, operation_id)]
    except KeyError as exc:
        raise _reject("M03_inventory_exact_three_file_directory", "operation_tuple_mismatch") from exc
    return row["payload_file"], row["projection_file"], row["invocation_file"]


def validate_exact_directory(root: Path, expected_names: Sequence[str]) -> dict[str, Any]:
    if not root.is_dir() or root.is_symlink():
        raise _reject("M03_inventory_exact_three_file_directory", "invalid_directory")
    if sorted(p.name for p in root.iterdir()) != sorted(expected_names):
        raise _reject("M03_inventory_exact_three_file_directory", "directory_member_mismatch")
    root_real = root.resolve(strict=True)
    seen: set[tuple[int, int]] = set()
    rows = []
    for name in expected_names:
        path = root / name
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or path.is_symlink() or info.st_nlink != 1:
            raise _reject("M03_inventory_exact_three_file_directory", "nonregular_or_linked_input", name)
        real = path.resolve(strict=True)
        try:
            real.relative_to(root_real)
        except ValueError as exc:
            raise _reject("M03_inventory_exact_three_file_directory", "input_realpath_escape", name) from exc
        inode = (info.st_dev, info.st_ino)
        if inode in seen:
            raise _reject("M03_inventory_exact_three_file_directory", "hardlink_duplicate", name)
        seen.add(inode)
        raw = path.read_bytes()
        rows.append({
            "device": info.st_dev, "filename": name, "inode": info.st_ino,
            "link_count": info.st_nlink, "raw_sha256": sha256_bytes(raw),
            "realpath": str(real), "size": len(raw),
        })
    return {
        "directory_realpath": str(root_real),
        "files": rows,
        "inventory_schema": "CrossDomainOccupancyInputInventory.v1",
        "unexpected_members": [],
    }


def validate_visible_tuple(
    payload_raw: bytes, projection_raw: bytes, invocation_raw: bytes, *,
    domain_role: str, operation_id: str, operational_id: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str]:
    try:
        row = OPERATION_ROWS[(domain_role, operation_id)]
    except KeyError as exc:
        raise _reject("M12_validate_operation_tuple_and_process_binding", "operation_tuple_mismatch") from exc
    target_role = row["target_role"]
    payload = payload_from_raw(payload_raw, target_role)
    if sha256_bytes(projection_raw) != PROJECTION_ROWS[(domain_role, target_role)]["raw_sha256"]:
        raise _reject("M09_authenticate_and_validate_projection", "projection_raw_sha256_not_frozen")
    p = strict_load_stored_json(projection_raw)
    validate_projection(p, domain_role, target_role)
    invocation = strict_load_stored_json(invocation_raw)
    expected = operation_invocation(domain_role, operation_id, operational_id)
    if invocation != expected:
        raise _reject("M12_validate_operation_tuple_and_process_binding", "operation_tuple_mismatch")
    return payload, p, invocation, target_role


def anchor_values(
    expected: Mapping[str, Any], binding: Mapping[str, Any], generation: str,
) -> dict[str, Any]:
    return {
        "accepted_canonical_hash": expected["canonical_hash"],
        "accepted_canonical_payload_raw_sha256": expected["canonical_payload_raw_sha256"],
        "accepted_projection_id": expected["projection_id"],
        "accepted_projection_raw_sha256": expected["projection_raw_sha256"],
        "anchor_schema": ANCHOR_SCHEMA,
        "canonical_occupancy_kind": expected["canonical_occupancy_kind"],
        "canonical_occupancy_reference": expected["canonical_occupancy_reference"],
        "canonical_occupant_id": OCCUPANT,
        "domain_role": expected["domain_role"],
        "local_subject_disposition": expected["expected_local_subject_disposition"],
        "operational_process_instance_id": operational_process_instance_id(binding),
        "process_binding_raw_sha256": process_binding_raw_sha256(binding),
        "projected_canonical_site_id": expected["projected_canonical_site_id"],
        "projected_site_representation_slot": expected["projected_site_representation_slot"],
        "projected_subject_representation_slot": expected["projected_subject_representation_slot"],
        "proof_scenario": PROOF_SCENARIO,
        "publication_generation": generation,
        "representation_publication_state": "locally_published_unverified",
    }


def subject_values(
    expected: Mapping[str, Any], binding: Mapping[str, Any], generation: str,
) -> dict[str, Any] | None:
    if expected["expected_local_subject_disposition"] != "present_at_local_site":
        return None
    return {
        "accepted_canonical_hash": expected["canonical_hash"],
        "accepted_canonical_payload_raw_sha256": expected["canonical_payload_raw_sha256"],
        "accepted_projection_id": expected["projection_id"],
        "accepted_projection_raw_sha256": expected["projection_raw_sha256"],
        "canonical_occupant_id": OCCUPANT,
        "domain_role": expected["domain_role"],
        "operational_process_instance_id": operational_process_instance_id(binding),
        "process_binding_raw_sha256": process_binding_raw_sha256(binding),
        "proof_scenario": PROOF_SCENARIO,
        "publication_generation": generation,
        "representation_publication_state": "locally_published_unverified",
        "represented_site_id": expected["projected_canonical_site_id"],
        "subject_representation_slot": expected["projected_subject_representation_slot"],
        "subject_schema": SUBJECT_SCHEMA,
    }


def expected_actor_rows(
    expected: Mapping[str, Any], binding: Mapping[str, Any], generation: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    anchor = anchor_values(expected, binding, generation)
    subject = subject_values(expected, binding, generation)
    return [anchor], [] if subject is None else [subject]


def materialization_receipt(
    *, operation_id: str, command_raw_sha256: str, operation_invocation_raw_sha256: str,
    expected: Mapping[str, Any], binding: Mapping[str, Any], generation: str,
    anchor_rows: Sequence[Mapping[str, Any]], subject_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    row = OPERATION_ROWS[(expected["domain_role"], operation_id)]
    if not is_sha256(command_raw_sha256) or not is_sha256(operation_invocation_raw_sha256):
        raise _reject("M22_emit_materialization_receipt", "receipt_digest_invalid")
    if len(anchor_rows) != 1 or len(subject_rows) != expected["expected_subject_actor_count"]:
        raise _reject("M16_validate_candidate_coherence_and_cardinality", "candidate_cardinality_mismatch")
    return {
        "accepted_canonical_hash": expected["canonical_hash"],
        "accepted_canonical_payload_raw_sha256": expected["canonical_payload_raw_sha256"],
        "accepted_projection_id": expected["projection_id"],
        "accepted_projection_raw_sha256": expected["projection_raw_sha256"],
        "canonical_occupancy_kind": expected["canonical_occupancy_kind"],
        "canonical_occupancy_reference": expected["canonical_occupancy_reference"],
        "canonical_occupant_id": OCCUPANT,
        "derived_local_subject_disposition": expected["expected_local_subject_disposition"],
        "domain_role": expected["domain_role"],
        "materialize_command_raw_sha256": command_raw_sha256,
        "operation": row["operation"],
        "operation_id": operation_id,
        "operation_invocation_raw_sha256": operation_invocation_raw_sha256,
        "operational_process_instance_id": operational_process_instance_id(binding),
        "process_binding_raw_sha256": process_binding_raw_sha256(binding),
        "projected_canonical_site_id": expected["projected_canonical_site_id"],
        "projected_site_representation_slot": expected["projected_site_representation_slot"],
        "projected_subject_representation_slot": expected["projected_subject_representation_slot"],
        "proof_scenario": PROOF_SCENARIO,
        "publication_generation": generation,
        "published_anchor_actor_count": len(anchor_rows),
        "published_anchor_actor_rows": _copy(list(anchor_rows)),
        "published_subject_actor_count": len(subject_rows),
        "published_subject_actor_rows": _copy(list(subject_rows)),
        "receipt_authority": "representation_only",
        "receipt_schema": MATERIALIZATION_RECEIPT_SCHEMA,
        "representation_publication_state": "locally_published_unverified",
    }


def validate_materialization_receipt(
    value: Any, expected: Mapping[str, Any], binding: Mapping[str, Any], operation_id: str,
) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("receipt_schema") != MATERIALIZATION_RECEIPT_SCHEMA:
        raise _reject("M22_emit_materialization_receipt", "receipt_schema_mismatch")
    if value.get("receipt_authority") != "representation_only" or "synchronized" in canonical_json(value):
        raise _reject("M22_emit_materialization_receipt", "receipt_authority_escalation")
    for field, expected_value in (
        ("domain_role", expected["domain_role"]),
        ("operation_id", operation_id),
        ("accepted_canonical_hash", expected["canonical_hash"]),
        ("accepted_canonical_payload_raw_sha256", expected["canonical_payload_raw_sha256"]),
        ("accepted_projection_id", expected["projection_id"]),
        ("accepted_projection_raw_sha256", expected["projection_raw_sha256"]),
        ("operational_process_instance_id", operational_process_instance_id(binding)),
        ("process_binding_raw_sha256", process_binding_raw_sha256(binding)),
        ("derived_local_subject_disposition", expected["expected_local_subject_disposition"]),
    ):
        if value.get(field) != expected_value:
            raise _reject("M22_emit_materialization_receipt", "receipt_field_mismatch", field)
    if value.get("published_anchor_actor_count") != len(value.get("published_anchor_actor_rows", [])):
        raise _reject("M22_emit_materialization_receipt", "receipt_count_mismatch")
    if value.get("published_subject_actor_count") != len(value.get("published_subject_actor_rows", [])):
        raise _reject("M22_emit_materialization_receipt", "receipt_count_mismatch")
    if value["published_anchor_actor_count"] != 1 or value["published_subject_actor_count"] != expected["expected_subject_actor_count"]:
        raise _reject("M22_emit_materialization_receipt", "receipt_cardinality_mismatch")
    return _copy(value)


class PhysicalCurrentHeadGuard:
    """Harness-only seven-state state machine with an absorbing failure."""

    def __init__(self) -> None:
        self.state = "open_for_R0"
        self.history = [self.state]

    def transition(self, target: str, trigger: str) -> str:
        if self.state == "failed_closed":
            raise _reject("guard_transition", "failed_closed_absorbing")
        if target == "failed_closed":
            self.state = target
            self.history.append(target)
            return target
        legal = {
            ("open_for_R0", "closed_for_R0_to_Rtransit"): "before_exact_start_resolution",
            ("closed_for_R0_to_Rtransit", "open_for_Rtransit"): "verified_Rtransit_and_both_stale_R0",
            ("open_for_Rtransit", "closed_for_Rtransit_to_Rfinal"): "both_synchronized_Rtransit_before_completion",
            ("open_for_Rtransit", "closed_for_c1_Rtransit_to_Rfinal"): "c1_verified_Rtransit_both_stale_no_refresh",
            ("closed_for_Rtransit_to_Rfinal", "open_for_Rfinal"): "verified_Rfinal_and_both_stale_Rtransit",
        }
        if legal.get((self.state, target)) != trigger:
            raise _reject("guard_transition", "illegal_guard_transition", f"{self.state}->{target}")
        self.state = target
        self.history.append(target)
        return target


PERMISSION_ROWS = {
    "unbound / binding_not_accepted": (False, False, False, False, True, True, False),
    "synchronized(R0) / exact_current_representation": (True, False, True, True, True, True, False),
    "head_unconfirmed(R0) / successor_observation_unpublished": (False, False, True, True, True, True, False),
    "stale(R0/Rtransit) / immediate_successor_verified": (False, True, True, True, True, True, True),
    "synchronized(Rtransit) / exact_current_representation": (True, False, True, True, True, True, False),
    "head_unconfirmed(Rtransit) / successor_observation_unpublished": (False, False, True, True, True, True, False),
    "stale(Rtransit/Rfinal) / immediate_successor_verified": (False, True, True, True, True, True, True),
    "synchronized(Rfinal) / exact_current_representation": (True, False, True, True, True, True, False),
    "stale(R0/Rfinal) / multigeneration_control_terminal": (False, False, True, False, True, True, False),
    "invalid / local_publication_unprovable": (False, False, False, False, True, True, False),
    "protocol_invalid / physical_protocol_violation": (False, False, False, False, True, True, False),
}


def head_disposition(
    *, context: str, domain_role: str, binding: Mapping[str, Any], guard_state: str,
    represented_hash: str | None, observed_head: str | None,
    expected: Mapping[str, Any] | None = None, receipt: Mapping[str, Any] | None = None,
    observation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if context not in PERMISSION_ROWS or guard_state not in GUARD_STATES:
        raise _reject("head_disposition", "disposition_context_invalid")
    state_reason = context.split(" / ", 1)
    head_state = state_reason[0].split("(", 1)[0]
    reason = state_reason[1]
    relation = {
        "unbound": "none", "synchronized": "current", "head_unconfirmed": "successor_unpublished",
        "invalid": "untrusted", "protocol_invalid": "untrusted",
    }.get(head_state)
    if head_state == "stale":
        relation = "two_generation_stale" if "R0/Rfinal" in context else "one_generation_stale"
    claim, refresh, inspect, step, diagnostics, terminate, publish = PERMISSION_ROWS[context]
    local = None if expected is None else expected["expected_local_subject_disposition"]
    return {
        "anchor_verified": claim,
        "canonical_completion_enabled": False,
        "canonical_evidence_enabled": False,
        "canonical_mutation_enabled": False,
        "canonical_scheduling_enabled": False,
        "canonical_truth_publication_enabled": False,
        "current_head_representation_claim_enabled": claim,
        "diagnostics_enabled": diagnostics,
        "disposition_schema": DISPOSITION_SCHEMA,
        "domain_role": domain_role,
        "expected_representation_raw_sha256": None if expected is None else sha256_value(dict(expected)),
        "harness_observed_current_canonical_hash": observed_head,
        "head_relation": relation,
        "head_state": head_state,
        "inspection_enabled": inspect,
        "live_observation_raw_sha256": None if observation is None else sha256_value(dict(observation)),
        "local_nonconsequential_step_enabled": step,
        "local_publication_enabled": publish,
        "local_subject_disposition": local,
        "materialization_receipt_raw_sha256": None if receipt is None else sha256_value(dict(receipt)),
        "operational_process_instance_id": operational_process_instance_id(binding),
        "peer_interaction_enabled": False,
        "physical_current_head_guard_state": guard_state,
        "process_binding_raw_sha256": process_binding_raw_sha256(binding),
        "proof_scenario": PROOF_SCENARIO,
        "reason_code": reason,
        "refresh_enabled": refresh,
        "represented_canonical_hash": represented_hash,
        "subject_census_verified": claim,
        "termination_enabled": terminate,
    }


def compare_expectation_receipt_observation(
    expected: Mapping[str, Any], receipt: Mapping[str, Any], observation: Mapping[str, Any],
    binding: Mapping[str, Any], operation_id: str,
) -> None:
    validate_materialization_receipt(receipt, expected, binding, operation_id)
    if observation.get("observation_schema") != LIVE_OBSERVATION_SCHEMA:
        raise _reject("O12_harness_compare_expectation_receipt_observation_head_binding_guard", "observation_schema_mismatch")
    count_fields = (
        ("anchor_actor_count", "expected_anchor_actor_count"),
        ("subject_actor_count", "expected_subject_actor_count"),
        ("proof_relevant_actor_count", "expected_proof_relevant_actor_count"),
        ("route_actor_count", "expected_route_actor_count"),
        ("unexpected_proof_tagged_actor_count", "expected_unexpected_proof_tagged_actor_count"),
        ("pawn_count", "expected_pawn_count"),
        ("controller_count", "expected_controller_count"),
        ("auto_receive_input_actor_count", "expected_auto_receive_input_actor_count"),
        ("phase_4_actor_input_binding_count", "expected_phase_4_actor_input_binding_count"),
    )
    for observed, expected_field in count_fields:
        if observation.get(observed) != expected[expected_field]:
            reason = "live_count_mismatch"
            if observed == "anchor_actor_count":
                reason = "positive_anchor_missing" if observation.get(observed) == 0 else "duplicate_generation_object"
            elif observed == "subject_actor_count":
                actual = observation.get(observed)
                required = expected[expected_field]
                if required == 1 and actual == 0:
                    reason = "missing_local_subject"
                elif required == 0 and actual and expected["canonical_occupancy_kind"] == "in_transition":
                    reason = "subject_forbidden_in_transition"
                elif required == 0 and actual:
                    reason = "unexpected_local_subject"
                elif actual and actual > 1:
                    reason = "duplicate_generation_object"
            raise _reject("O12_harness_compare_expectation_receipt_observation_head_binding_guard", reason, observed)
    if observation.get("operational_process_instance_id") != operational_process_instance_id(binding):
        raise _reject("O12_harness_compare_expectation_receipt_observation_head_binding_guard", "live_binding_mismatch")
    if observation.get("observed_publication_generation") != receipt["publication_generation"]:
        raise _reject("O12_harness_compare_expectation_receipt_observation_head_binding_guard", "live_generation_mismatch")
    if observation.get("observation_source") != "exhaustive_live_ue_world_census":
        raise _reject("O12_harness_compare_expectation_receipt_observation_head_binding_guard", "oracle_not_independent")
    anchor_rows = observation.get("anchor_actor_rows")
    subject_rows = observation.get("subject_actor_rows")
    if not isinstance(anchor_rows, list) or not isinstance(subject_rows, list):
        raise _reject("O12_harness_compare_expectation_receipt_observation_head_binding_guard", "live_actor_rows_missing")
    if anchor_rows != receipt.get("published_anchor_actor_rows") or subject_rows != receipt.get("published_subject_actor_rows"):
        raise _reject("O12_harness_compare_expectation_receipt_observation_head_binding_guard", "receipt_live_actor_rows_mismatch")
    expected_anchor = anchor_values(expected, binding, receipt["publication_generation"])
    expected_subject = subject_values(expected, binding, receipt["publication_generation"])
    for row in anchor_rows:
        if any(row.get(field) != value for field, value in expected_anchor.items()):
            raise _reject("O12_harness_compare_expectation_receipt_observation_head_binding_guard", "live_field_mismatch")
    if expected_subject is None and subject_rows:
        raise _reject("O12_harness_compare_expectation_receipt_observation_head_binding_guard", "unexpected_local_subject")
    for row in subject_rows:
        if expected_subject is None or any(row.get(field) != value for field, value in expected_subject.items()):
            raise _reject("O12_harness_compare_expectation_receipt_observation_head_binding_guard", "live_field_mismatch")
    actor_paths = [row.get("actor_path") for row in anchor_rows + subject_rows]
    if None in actor_paths or len(actor_paths) != len(set(actor_paths)):
        raise _reject("O12_harness_compare_expectation_receipt_observation_head_binding_guard", "duplicate_generation_object")
    if observation.get("proof_relevant_actor_rows") != sorted(
        anchor_rows + subject_rows, key=lambda row: row.get("actor_path", "")
    ):
        raise _reject("O12_harness_compare_expectation_receipt_observation_head_binding_guard", "proof_relevant_actor_union_mismatch")


def validate_head_disposition(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("disposition_schema") != DISPOSITION_SCHEMA:
        raise _reject("head_disposition", "disposition_schema_mismatch")
    context = next(
        (
            candidate for candidate in PERMISSION_ROWS
            if candidate.split(" / ", 1)[1] == value.get("reason_code")
            and candidate.split("(", 1)[0] == value.get("head_state")
        ),
        None,
    )
    if context is None:
        raise _reject("head_disposition", "disposition_context_invalid")
    expected_permissions = PERMISSION_ROWS[context]
    fields = (
        "current_head_representation_claim_enabled", "refresh_enabled", "inspection_enabled",
        "local_nonconsequential_step_enabled", "diagnostics_enabled", "termination_enabled",
        "local_publication_enabled",
    )
    if tuple(value.get(field) for field in fields) != expected_permissions:
        raise _reject("head_disposition", "permission_matrix_mismatch")
    for field in (
        "canonical_completion_enabled", "canonical_evidence_enabled", "canonical_mutation_enabled",
        "canonical_scheduling_enabled", "canonical_truth_publication_enabled", "peer_interaction_enabled",
    ):
        if value.get(field) is not False:
            raise _reject("head_disposition", "authority_claim_prohibited", field)
    return _copy(value)


def guard_and_head_observation_matrix() -> dict[str, Any]:
    return {
        "matrix_schema": "CrossDomainOccupancyGuardAndHeadObservationMatrix.v1",
        "proof_scenario": PROOF_SCENARIO,
        "guard_states": list(GUARD_STATES),
        "legal_transitions": [
            ["open_for_R0", "closed_for_R0_to_Rtransit"],
            ["closed_for_R0_to_Rtransit", "open_for_Rtransit"],
            ["open_for_Rtransit", "closed_for_Rtransit_to_Rfinal"],
            ["open_for_Rtransit", "closed_for_c1_Rtransit_to_Rfinal"],
            ["closed_for_Rtransit_to_Rfinal", "open_for_Rfinal"],
            ["any_nonfailed", "failed_closed"],
        ],
        "head_observations": [
            {"observation_sequence": "head_observation_0001", "source_record_role": RTRANSIT_ROLE,
             "source_record_raw_sha256": DTRANSIT, "observed_canonical_hash": HTRANSIT,
             "observed_parent_canonical_hash": H0, "observed_ledger_entry_count": 1,
             "observed_unresolved_work_count": 1},
            {"observation_sequence": "head_observation_0002", "source_record_role": RFINAL_ROLE,
             "source_record_raw_sha256": DFINAL, "observed_canonical_hash": HFINAL,
             "observed_parent_canonical_hash": HTRANSIT, "observed_ledger_entry_count": 2,
             "observed_unresolved_work_count": 0},
        ],
        "permission_rows": [
            {"context": key, "permissions": list(value)} for key, value in PERMISSION_ROWS.items()
        ],
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(stored_json_bytes(value))


def artifact_role_set_valid(directory: Path) -> bool:
    return (
        directory.is_dir() and not directory.is_symlink()
        and tuple(sorted(p.name for p in directory.iterdir())) == tuple(sorted(ARTIFACT_NAMES))
        and all(p.is_file() and not p.is_symlink() for p in directory.iterdir())
    )


def semantic_replay_projection(value: Any) -> Any:
    operational = {
        "pid", "observed_pid", "macos_process_start", "observed_macos_process_start",
        "operational_process_instance_id", "process_binding_raw_sha256",
        "process_root_realpath", "world_instance_identity", "actor_path",
        "source_record_device", "source_record_inode", "harness_run_id",
        "launch_plan_raw_sha256", "command_raw_sha256", "materialize_command_raw_sha256",
        "operation_invocation_raw_sha256", "materialization_receipt_raw_sha256",
        "live_observation_raw_sha256",
    }
    if isinstance(value, dict):
        return {key: "<operational>" if key in operational else semantic_replay_projection(item)
                for key, item in value.items()}
    if isinstance(value, list):
        return [semantic_replay_projection(item) for item in value]
    return _copy(value)


if len(ARTIFACT_NAMES) != 82 or len(set(ARTIFACT_NAMES)) != 82:
    raise AssertionError("frozen artifact list must contain 82 unique names")


__all__ = [name for name in globals() if not name.startswith("_")]
