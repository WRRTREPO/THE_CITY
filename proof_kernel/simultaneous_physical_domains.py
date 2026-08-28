"""Frozen reference machine for Simultaneous Physical Domains Proof v0.1.0.

This module is deliberately proof-local.  It composes the sealed Phase-1
canonical topology transition with detached physical-domain projections.  It
does not own a new canonical payload, resolver, scheduler, ledger, or mutation.
Unreal receipts describe disposable representation only; current-head
classification remains a private harness operation.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from canonical_spatial_topology_identity import (
    ROUTE_ID,
    SITE_A,
    SITE_B,
    canonical_hash,
    initial_canonical_envelope,
    next_consequential_boundary,
    resolve_next_due,
    stored_json_bytes as phase1_stored_json_bytes,
    strict_load_stored_json as phase1_strict_load_stored_json,
    validate_canonical_envelope,
)


PROOF_SCHEMA = "SimultaneousPhysicalDomainsProof.v1"
PROOF_SCENARIO = "simultaneous-physical-domains-v1"
PROOF_VERSION = "0.1.0"
HARNESS_VERSION = "0.7.0-draft.72"

H0 = "666d75281d3478e586edd12464d2736169f423c2d7b128bd3d2d2b1b2b826b29"
H1 = "78cc5ffe0c4758c296d8fee0bc2a95e230be0bec0a4aab680806eb670500804a"
D0 = "5e57c04875cfaead69f4cd6aaffeee2f788a2c1f5a820a56fb7083f8f7e861ed"
D1 = "7ac7ece5c142ac4dee83abc6e83f7845d85dfc7f055ca6d678b7f04bdf1d795a"
WORK_ID = "t1/00/topology/block_topology_route_0001.resolve"

DOMAIN_ROLES = ("domain_A", "domain_B")
HEAD_ROLES = ("H0", "H1")
HEAD_HASHES = {"H0": H0, "H1": H1}
RAW_HASHES = {"H0": D0, "H1": D1}
ACCESS_STATES = {"H0": "available", "H1": "blocked"}

PROJECTION_SCHEMA = "SimultaneousPhysicalDomainProjection.v1"
OPERATION_RECEIPT_SCHEMA = "SimultaneousPhysicalDomainOperationReceipt.v1"
REPRESENTATION_SCHEMA = "SimultaneousPhysicalDomainAuthoritativeDerivedRepresentation.v1"
MATERIALIZATION_RECEIPT_SCHEMA = "SimultaneousPhysicalDomainMaterializationReceipt.v1"
PROCESS_BINDING_SCHEMA = "SimultaneousPhysicalDomainProcessBinding.v1"
BIND_INVOCATION_SCHEMA = "SimultaneousPhysicalDomainBindInvocation.v1"
REFRESH_INVOCATION_SCHEMA = "SimultaneousPhysicalDomainRefreshInvocation.v1"
INSPECTION_INVOCATION_SCHEMA = "SimultaneousPhysicalDomainInspectionInvocation.v1"
PHYSICAL_OBSERVATION_SCHEMA = "SimultaneousPhysicalDomainPhysicalObservation.v1"
HEAD_OBSERVATION_SCHEMA = "SimultaneousPhysicalDomainsHeadObservation.v1"
HEAD_DISPOSITION_SCHEMA = "SimultaneousPhysicalDomainHeadDisposition.v1"
RETAINED_SCHEMA = "SimultaneousPhysicalDomainRetainedLocalState.v1"

GUARD_STATES = (
    "open_for_H0",
    "closed_for_H0_to_H1",
    "open_for_H1",
    "failed_closed",
)
HEAD_STATES = (
    "unbound",
    "synchronized",
    "head_unconfirmed",
    "stale",
    "invalid",
    "protocol_invalid",
)

WITNESS_IDS = (
    "w1_a_then_b",
    "w2_b_then_a",
    "w3_stale_quarantine",
    "w4_head_observation_failure",
    "w5_retention_baseline",
    "w5_retention_perturbed",
    "w6_asymmetric_a_synchronized",
    "w6_asymmetric_b_synchronized",
    "w7_destroy_a",
    "w7_destroy_b",
    "w8_guard_open_control",
)

HEAD_OBSERVATION_FAULT_POINTS = (
    "after_physical_guard_close_before_canonical_invocation",
    "after_R1_H1_commit_verification_before_observation_construction",
    "after_observation_construction_before_temporary_write",
    "after_temporary_write_before_file_fsync",
    "after_file_fsync_before_atomic_replace",
    "after_atomic_replace_before_directory_fsync",
    "after_directory_fsync_before_independent_reread",
    "after_independent_reread_before_identity_reverification",
    "after_identity_reverification_before_refresh_eligibility",
)

REFRESH_FAULT_STAGES = (
    "invocation_read",
    "visible_input_inventory",
    "payload_raw_byte_verification",
    "payload_parse_and_canonical_identity_verification",
    "operation_receipt_verification",
    "projection_verification",
    "visible_command_bundle_cross_field_verification",
    "process_binding_identity_verification",
    "retained_local_state_projection_extraction",
    "discard_required_state_poison_check",
    "empty_authoritative_candidate_construction",
    "H1_authoritative_fact_derivation",
    "projection_slot_binding",
    "private_candidate_validation",
    "retained_local_state_attachment",
    "prepublication_cross_field_validation",
    "local_atomic_publication",
    "materialization_receipt_emission",
)

PHYSICAL_OBSERVATION_FAULT_STAGES = (
    "inspection_invocation_read",
    "immutable_process_binding_verification",
    "role_probe_tag_derivation",
    "live_world_actor_enumeration",
    "exact_actor_count_check",
    "live_mesh_component_lookup",
    "live_mesh_visibility_and_material_parameter_read",
    "live_label_component_lookup",
    "live_label_visibility_text_and_color_read",
    "independent_surface_consistency_classification",
    "physical_observation_emission",
    "harness_receipt_observation_head_cross_check",
)

LIVENESS_FAILURES = (
    "original_child_handle_exit_observed",
    "wait_status_available",
    "control_pipe_unexpected_eof",
    "structured_output_pipe_unexpected_eof",
    "process_start_pair_changed",
    "process_binding_changed",
    "replacement_spawn_observed",
)

ARTIFACT_NAMES = (
    "simultaneous_physical_domains_canonical_transition_run.json",
    "simultaneous_physical_domains_projection_matrix.json",
    "simultaneous_physical_domains_operation_receipt_matrix.json",
    "simultaneous_physical_domains_current_head_observation.json",
    "simultaneous_physical_domains_head_observation_fault_atomicity.json",
    "simultaneous_physical_domains_guard_open_canonical_control.json",
    "physical_W1_domain_A_H0_materialization_receipt.json",
    "physical_W1_domain_A_H0_observation.json",
    "physical_W1_domain_B_H0_materialization_receipt.json",
    "physical_W1_domain_B_H0_observation.json",
    "physical_W1_domain_A_H1_materialization_receipt.json",
    "physical_W1_domain_A_H1_observation.json",
    "physical_W1_domain_B_H1_materialization_receipt.json",
    "physical_W1_domain_B_H1_observation.json",
    "physical_W1_liveness_witness.json",
    "physical_W1_a_then_b_witness.json",
    "physical_W2_domain_A_H0_materialization_receipt.json",
    "physical_W2_domain_A_H0_observation.json",
    "physical_W2_domain_B_H0_materialization_receipt.json",
    "physical_W2_domain_B_H0_observation.json",
    "physical_W2_domain_B_H1_materialization_receipt.json",
    "physical_W2_domain_B_H1_observation.json",
    "physical_W2_domain_A_H1_materialization_receipt.json",
    "physical_W2_domain_A_H1_observation.json",
    "physical_W2_liveness_witness.json",
    "physical_W2_b_then_a_witness.json",
    "physical_W3_stale_quarantine_witness.json",
    "physical_W4_head_observation_failure_witness.json",
    "physical_W5_retention_baseline_witness.json",
    "physical_W5_retention_perturbed_witness.json",
    "physical_W5_retention_equivalence_oracle.json",
    "physical_W6_asymmetric_A_synchronized_witness.json",
    "physical_W6_asymmetric_B_synchronized_witness.json",
    "physical_W7_destroy_A_witness.json",
    "physical_W7_destroy_B_witness.json",
    "simultaneous_physical_domains_current_head_authority_failures.json",
    "simultaneous_physical_domains_refresh_fault_atomicity.json",
    "simultaneous_physical_domains_physical_observation_fault_atomicity.json",
    "simultaneous_physical_domains_proof_semantic_input_audit.json",
    "simultaneous_physical_domains_physical_rebind_oracle.json",
    "simultaneous_physical_domains_canonical_equivalence_oracle.json",
    "simultaneous_physical_domains_source_audit.json",
    "simultaneous_physical_domains_replay_oracle.json",
    "simultaneous_physical_domains_proof_run.json",
)

PROJECTION_ROWS: dict[tuple[str, str], dict[str, str]] = {
    ("domain_A", "H0"): {
        "projection_id": "simultaneous_domain_A_H0_0001",
        "site": SITE_A,
        "site_slot": "domain_A_site_slot_01",
        "route_slot": "domain_A_route_slot_01",
    },
    ("domain_A", "H1"): {
        "projection_id": "simultaneous_domain_A_H1_0001",
        "site": SITE_A,
        "site_slot": "domain_A_site_slot_01",
        "route_slot": "domain_A_route_slot_01",
    },
    ("domain_B", "H0"): {
        "projection_id": "simultaneous_domain_B_H0_0001",
        "site": SITE_B,
        "site_slot": "domain_B_site_slot_01",
        "route_slot": "domain_B_route_slot_01",
    },
    ("domain_B", "H1"): {
        "projection_id": "simultaneous_domain_B_H1_0001",
        "site": SITE_B,
        "site_slot": "domain_B_site_slot_01",
        "route_slot": "domain_B_route_slot_01",
    },
}

PHYSICAL_SURFACES = {
    "available": {
        "mesh": [0.10, 0.85, 0.35, 1.00],
        "label": "AVAILABLE",
        "label_color": [0, 255, 0, 255],
    },
    "blocked": {
        "mesh": [0.90, 0.12, 0.12, 1.00],
        "label": "BLOCKED",
        "label_color": [255, 0, 0, 255],
    },
}


class PhysicalDomainRejected(ValueError):
    """A detached physical-domain input failed before authority or publication."""

    def __init__(self, stage: str, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.stage = stage
        self.reason_code = reason_code

    @property
    def diagnostic(self) -> dict[str, str]:
        return {
            "diagnostic_schema": "SimultaneousPhysicalDomainFailure.v1",
            "proof_scenario": PROOF_SCENARIO,
            "local_publication_stage": self.stage,
            "reason_code": self.reason_code,
        }


def _reject(stage: str, reason: str, message: str) -> PhysicalDomainRejected:
    return PhysicalDomainRejected(stage, reason, message)


def _copy(value: Any) -> Any:
    return copy.deepcopy(value)


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def stored_json_bytes(value: Any) -> bytes:
    return (canonical_json(value) + "\n").encode("utf-8")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_value(value: Any) -> str:
    return sha256_bytes(stored_json_bytes(value))


def strict_load_stored_json(raw: bytes) -> Any:
    if not raw.endswith(b"\n") or raw.endswith(b"\n\n") or b"\r" in raw or raw.count(b"\n") != 1:
        raise _reject("parse", "noncanonical_stored_json", "stored JSON requires one terminal LF")
    try:
        text = raw[:-1].decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise _reject("parse", "invalid_utf8", "stored JSON is not UTF-8") from exc

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise _reject("parse", "duplicate_json_member", f"duplicate JSON member: {key}")
            result[key] = value
        return result

    try:
        value = json.loads(
            text,
            object_pairs_hook=reject_duplicates,
            parse_constant=lambda token: (_ for _ in ()).throw(
                _reject("parse", "nonfinite_json_number", token)
            ),
        )
    except json.JSONDecodeError as exc:
        raise _reject("parse", "invalid_json", "invalid stored JSON") from exc
    if canonical_json(value) != text:
        raise _reject("parse", "noncanonical_stored_json", "stored JSON is not canonical")
    return value


def _exact_keys(value: Any, keys: Iterable[str], stage: str) -> dict[str, Any]:
    expected = set(keys)
    if not isinstance(value, dict) or set(value) != expected:
        raise _reject(stage, "invalid_object_members", f"expected exact keys {sorted(expected)}")
    return value


def _head_role_from_hash(value: str) -> str:
    for role, digest in HEAD_HASHES.items():
        if value == digest:
            return role
    raise _reject("cross_field_verification", "unknown_canonical_hash", value)


def canonical_records() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Reproduce the sealed Phase-1 transition and reject any byte drift."""

    r0 = initial_canonical_envelope()
    boundary = next_consequential_boundary(r0)
    if boundary is None:
        raise AssertionError("sealed Phase-1 boundary missing")
    r1 = resolve_next_due(r0, boundary)
    if validate_canonical_envelope(r0) != "R0" or validate_canonical_envelope(r1) != "R1":
        raise AssertionError("sealed Phase-1 records failed validation")
    if canonical_hash(r0) != H0 or canonical_hash(r1) != H1:
        raise AssertionError("sealed Phase-1 canonical identity drift")
    if sha256_bytes(phase1_stored_json_bytes(r0)) != D0 or sha256_bytes(phase1_stored_json_bytes(r1)) != D1:
        raise AssertionError("sealed Phase-1 stored-byte identity drift")
    return r0, boundary, r1


def canonical_transition_run() -> dict[str, Any]:
    r0, boundary, r1 = canonical_records()
    route0 = r0["current_causal_state"]["spatial_topology"]["routes"][ROUTE_ID]
    route1 = r1["current_causal_state"]["spatial_topology"]["routes"][ROUTE_ID]
    return {
        "run_schema": "SimultaneousPhysicalDomainsCanonicalTransitionRun.v1",
        "proof_scenario": PROOF_SCENARIO,
        "resolver_implementation": "canonical_spatial_topology_identity.resolve_next_due",
        "source_record_hash": H0,
        "source_record_raw_sha256": D0,
        "boundary": _copy(boundary),
        "successor_record_hash": H1,
        "successor_record_raw_sha256": D1,
        "successor_bytes_equal_exact_sealed_R1": True,
        "source_access_state": route0["access_state"],
        "successor_access_state": route1["access_state"],
        "physical_guard_input_to_resolver": False,
        "domain_input_to_resolver": False,
        "next_boundary_after_R1": None,
    }


def projection(domain_role: str, head_role: str) -> dict[str, Any]:
    if (domain_role, head_role) not in PROJECTION_ROWS:
        raise _reject("projection_verification", "invalid_projection_row", f"{domain_role}/{head_role}")
    row = PROJECTION_ROWS[(domain_role, head_role)]
    return {
        "projection_schema": PROJECTION_SCHEMA,
        "projection_id": row["projection_id"],
        "proof_scenario": PROOF_SCENARIO,
        "domain_role": domain_role,
        "source_canonical_hash": HEAD_HASHES[head_role],
        "allowed_site_projection": {
            "canonical_site_id": row["site"],
            "representation_slot": row["site_slot"],
        },
        "allowed_route_projection": {
            "canonical_route_id": ROUTE_ID,
            "representation_slot": row["route_slot"],
        },
    }


def validate_projection(value: Any, domain_role: str, head_role: str) -> dict[str, Any]:
    expected = projection(domain_role, head_role)
    if value != expected:
        raise _reject("projection_verification", "projection_matrix_mismatch", "projection is not exact role/head row")
    return _copy(expected)


def operation_receipt(
    operation: str,
    domain_role: str,
    head_role: str,
    *,
    operational_process_instance_id: str | None = None,
) -> dict[str, Any]:
    if operation not in ("launch", "refresh"):
        raise _reject("operation_receipt_verification", "invalid_operation", operation)
    if operation == "launch" and (head_role != "H0" or operational_process_instance_id is not None):
        raise _reject("operation_receipt_verification", "invalid_launch_receipt_role", "launch is H0 and unbound only")
    if operation == "refresh" and (head_role != "H1" or not _is_sha256(operational_process_instance_id)):
        raise _reject("operation_receipt_verification", "invalid_refresh_process_identity", "refresh requires exact bound process")
    p = projection(domain_role, head_role)
    return {
        "receipt_schema": OPERATION_RECEIPT_SCHEMA,
        "operation": operation,
        "proof_scenario": PROOF_SCENARIO,
        "domain_role": domain_role,
        "expected_operational_process_instance_id": operational_process_instance_id,
        "expected_source_represented_hash": None if operation == "launch" else H0,
        "expected_target_represented_hash": HEAD_HASHES[head_role],
        "canonical_payload_raw_sha256": RAW_HASHES[head_role],
        "expected_canonical_hash": HEAD_HASHES[head_role],
        "projection_raw_sha256": sha256_value(p),
        "expected_projection_id": p["projection_id"],
    }


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def projection_matrix() -> dict[str, Any]:
    return {
        "matrix_schema": "SimultaneousPhysicalDomainProjectionMatrix.v1",
        "proof_scenario": PROOF_SCENARIO,
        "rows": [projection(role, head) for role in DOMAIN_ROLES for head in HEAD_ROLES],
        "route_access_value_supplied_by_projection": False,
        "route_endpoint_value_supplied_by_projection": False,
    }


def operation_receipt_matrix() -> dict[str, Any]:
    placeholder = "0" * 64
    return {
        "matrix_schema": "SimultaneousPhysicalDomainOperationReceiptMatrix.v1",
        "proof_scenario": PROOF_SCENARIO,
        "launch_rows": [operation_receipt("launch", role, "H0") for role in DOMAIN_ROLES],
        "refresh_templates": [
            operation_receipt("refresh", role, "H1", operational_process_instance_id=placeholder)
            for role in DOMAIN_ROLES
        ],
        "refresh_process_identity_template_only": True,
    }


def validate_visible_tuple(
    payload_raw: bytes,
    projection_raw: bytes,
    receipt_raw: bytes,
    *,
    operation: str,
    domain_role: str,
    operational_process_instance_id: str | None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str]:
    """Validate the exact three-file launch or refresh tuple.

    The function deliberately receives no current-head observation or guard.
    """

    expected_head = "H0" if operation == "launch" else "H1"
    expected_raw = RAW_HASHES[expected_head]
    if sha256_bytes(payload_raw) != expected_raw:
        raise _reject("payload_raw_byte_verification", "payload_raw_sha256_mismatch", "payload bytes differ")
    try:
        payload = phase1_strict_load_stored_json(payload_raw)
    except ValueError as exc:
        raise _reject("payload_parse_and_canonical_identity_verification", "invalid_canonical_payload", str(exc)) from exc
    expected_record_role = "R0" if expected_head == "H0" else "R1"
    if validate_canonical_envelope(payload) != expected_record_role or canonical_hash(payload) != HEAD_HASHES[expected_head]:
        raise _reject("payload_parse_and_canonical_identity_verification", "canonical_identity_mismatch", "payload identity differs")

    p = strict_load_stored_json(projection_raw)
    validate_projection(p, domain_role, expected_head)
    receipt = strict_load_stored_json(receipt_raw)
    expected_receipt = operation_receipt(
        operation,
        domain_role,
        expected_head,
        operational_process_instance_id=operational_process_instance_id,
    )
    if receipt != expected_receipt:
        raise _reject("operation_receipt_verification", "operation_receipt_mismatch", "receipt is not exact")
    if sha256_bytes(projection_raw) != receipt["projection_raw_sha256"]:
        raise _reject("visible_command_bundle_cross_field_verification", "projection_raw_sha256_mismatch", "projection bytes differ")
    return _copy(payload), _copy(p), _copy(receipt), expected_head


def authoritative_representation(payload: Mapping[str, Any], p: Mapping[str, Any]) -> dict[str, Any]:
    """Pure two-input representation constructor required by the freeze."""

    head_role = _head_role_from_hash(str(p.get("source_canonical_hash", "")))
    domain_role = str(p.get("domain_role", ""))
    validate_projection(p, domain_role, head_role)
    expected_record_role = "R0" if head_role == "H0" else "R1"
    if validate_canonical_envelope(dict(payload)) != expected_record_role:
        raise _reject("H1_authoritative_fact_derivation", "payload_projection_head_mismatch", "head row mismatch")
    raw = phase1_stored_json_bytes(dict(payload))
    if sha256_bytes(raw) != RAW_HASHES[head_role] or canonical_hash(dict(payload)) != HEAD_HASHES[head_role]:
        raise _reject("H1_authoritative_fact_derivation", "sealed_payload_identity_mismatch", "payload is not sealed")
    topology = payload["current_causal_state"]["spatial_topology"]
    route = topology["routes"][ROUTE_ID]
    site_id = p["allowed_site_projection"]["canonical_site_id"]
    endpoints = route["endpoint_site_ids"]
    if endpoints != [SITE_A, SITE_B] or site_id not in endpoints:
        raise _reject("H1_authoritative_fact_derivation", "projected_site_not_route_endpoint", "endpoint law failed")
    return {
        "representation_schema": REPRESENTATION_SCHEMA,
        "proof_scenario": PROOF_SCENARIO,
        "domain_role": domain_role,
        "accepted_canonical_payload_raw_sha256": RAW_HASHES[head_role],
        "accepted_canonical_hash": HEAD_HASHES[head_role],
        "accepted_projection_raw_sha256": sha256_value(dict(p)),
        "accepted_projection_id": p["projection_id"],
        "materialized_canonical_site_id": site_id,
        "materialized_site_representation_slot": p["allowed_site_projection"]["representation_slot"],
        "materialized_canonical_route_id": ROUTE_ID,
        "materialized_route_representation_slot": p["allowed_route_projection"]["representation_slot"],
        "materialized_endpoint_site_ids": [SITE_A, SITE_B],
        "materialized_route_access_state": route["access_state"],
    }


def validate_retained_local_state(value: Any) -> dict[str, Any]:
    _exact_keys(value, ("retained_schema", "nonconsequential_tick_counter", "cosmetic_phase_token", "diagnostic_counter"), "retained_local_state_projection_extraction")
    if value["retained_schema"] != RETAINED_SCHEMA:
        raise _reject("retained_local_state_projection_extraction", "retained_schema_mismatch", "wrong retained schema")
    for key in ("nonconsequential_tick_counter", "diagnostic_counter"):
        if type(value[key]) is not int or not 0 <= value[key] <= 9007199254740991:
            raise _reject("retained_local_state_projection_extraction", "retained_counter_out_of_range", key)
    if value["cosmetic_phase_token"] not in tuple(f"cosmetic_phase_{i}" for i in range(4)):
        raise _reject("retained_local_state_projection_extraction", "invalid_cosmetic_phase", "invalid phase")
    return _copy(value)


def materialization_receipt(
    representation: Mapping[str, Any],
    *,
    operational_process_instance_id: str,
    process_binding_raw_sha256: str,
) -> dict[str, Any]:
    if not _is_sha256(operational_process_instance_id) or not _is_sha256(process_binding_raw_sha256):
        raise _reject("process_binding_identity_verification", "invalid_process_binding_identity", "invalid binding digest")
    expected_fields = set(authoritative_representation_for_identity(representation))
    if set(representation) != expected_fields:
        raise _reject("private_candidate_validation", "representation_members_mismatch", "candidate has extra/missing members")
    receipt = {
        "receipt_schema": MATERIALIZATION_RECEIPT_SCHEMA,
        "proof_scenario": PROOF_SCENARIO,
        "domain_role": representation["domain_role"],
        "operational_process_instance_id": operational_process_instance_id,
        "process_binding_raw_sha256": process_binding_raw_sha256,
    }
    for key in (
        "accepted_canonical_payload_raw_sha256",
        "accepted_canonical_hash",
        "accepted_projection_raw_sha256",
        "accepted_projection_id",
        "materialized_canonical_site_id",
        "materialized_site_representation_slot",
        "materialized_canonical_route_id",
        "materialized_route_representation_slot",
        "materialized_endpoint_site_ids",
        "materialized_route_access_state",
    ):
        receipt[key] = _copy(representation[key])
    receipt["authoritative_derived_representation_raw_sha256"] = sha256_value(dict(representation))
    receipt["receipt_authority"] = "representation_only"
    return receipt


def authoritative_representation_for_identity(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value[key]
        for key in (
            "representation_schema",
            "proof_scenario",
            "domain_role",
            "accepted_canonical_payload_raw_sha256",
            "accepted_canonical_hash",
            "accepted_projection_raw_sha256",
            "accepted_projection_id",
            "materialized_canonical_site_id",
            "materialized_site_representation_slot",
            "materialized_canonical_route_id",
            "materialized_route_representation_slot",
            "materialized_endpoint_site_ids",
            "materialized_route_access_state",
        )
    }


def validate_materialization_receipt(value: Any, binding: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "receipt_schema", "proof_scenario", "domain_role", "operational_process_instance_id",
        "process_binding_raw_sha256", "accepted_canonical_payload_raw_sha256", "accepted_canonical_hash",
        "accepted_projection_raw_sha256", "accepted_projection_id", "materialized_canonical_site_id",
        "materialized_site_representation_slot", "materialized_canonical_route_id",
        "materialized_route_representation_slot", "materialized_endpoint_site_ids",
        "materialized_route_access_state", "authoritative_derived_representation_raw_sha256", "receipt_authority",
    )
    _exact_keys(value, keys, "materialization_receipt_emission")
    binding_digest = sha256_value(dict(binding))
    instance_id = sha256_bytes(canonical_json(dict(binding)).encode("utf-8"))
    if value["receipt_schema"] != MATERIALIZATION_RECEIPT_SCHEMA or value["proof_scenario"] != PROOF_SCENARIO:
        raise _reject("materialization_receipt_emission", "receipt_schema_mismatch", "wrong receipt schema")
    if value["operational_process_instance_id"] != instance_id or value["process_binding_raw_sha256"] != binding_digest:
        raise _reject("process_binding_identity_verification", "receipt_binding_mismatch", "receipt changed process")
    if value["receipt_authority"] != "representation_only":
        raise _reject("materialization_receipt_emission", "receipt_authority_escalation", "receipt claims authority")
    representation = {
        "representation_schema": REPRESENTATION_SCHEMA,
        "proof_scenario": PROOF_SCENARIO,
        "domain_role": value["domain_role"],
    }
    for key in keys[5:15]:
        representation[key] = _copy(value[key])
    if sha256_value(representation) != value["authoritative_derived_representation_raw_sha256"]:
        raise _reject("materialization_receipt_emission", "representation_digest_mismatch", "receipt projection digest differs")
    head_role = _head_role_from_hash(value["accepted_canonical_hash"])
    r0, _, r1 = canonical_records()
    expected = authoritative_representation(r0 if head_role == "H0" else r1, projection(value["domain_role"], head_role))
    if representation != expected:
        raise _reject("materialization_receipt_emission", "receipt_projection_mismatch", "receipt fields differ")
    return _copy(value)


def probe_tag(domain_role: str) -> str:
    if domain_role not in DOMAIN_ROLES:
        raise _reject("role_probe_tag_derivation", "invalid_domain_role", domain_role)
    slot = PROJECTION_ROWS[(domain_role, "H0")]["route_slot"]
    return f"simultaneous_physical_domain/{domain_role}/{slot}"


def inspection_invocation(domain_role: str, inspection_id: str) -> dict[str, Any]:
    if inspection_id not in ("launch_physical_0001", "refresh_physical_0001"):
        raise _reject("inspection_invocation_read", "invalid_inspection_id", inspection_id)
    if domain_role not in DOMAIN_ROLES:
        raise _reject("inspection_invocation_read", "invalid_domain_role", domain_role)
    return {
        "command_schema": INSPECTION_INVOCATION_SCHEMA,
        "proof_scenario": PROOF_SCENARIO,
        "domain_role": domain_role,
        "operation": "inspect_published_route_once",
        "inspection_id": inspection_id,
    }


def refresh_invocation(domain_role: str) -> dict[str, Any]:
    if domain_role not in DOMAIN_ROLES:
        raise _reject("invocation_read", "invalid_domain_role", domain_role)
    return {
        "command_schema": REFRESH_INVOCATION_SCHEMA,
        "proof_scenario": PROOF_SCENARIO,
        "domain_role": domain_role,
        "operation": "refresh_once",
        "refresh_id": "h0_to_h1_refresh_0001",
        "target_canonical_hash": H1,
    }


def expected_physical_observation(
    domain_role: str,
    head_role: str,
    *,
    operational_process_instance_id: str,
    process_binding_raw_sha256: str,
    inspection_id: str,
) -> dict[str, Any]:
    state = ACCESS_STATES[head_role]
    surface = PHYSICAL_SURFACES[state]
    return {
        "observation_schema": PHYSICAL_OBSERVATION_SCHEMA,
        "proof_scenario": PROOF_SCENARIO,
        "domain_role": domain_role,
        "operational_process_instance_id": operational_process_instance_id,
        "process_binding_raw_sha256": process_binding_raw_sha256,
        "inspection_id": inspection_id,
        "probe_tag": probe_tag(domain_role),
        "matching_live_actor_count": 1,
        "actor_class": "ASimultaneousPhysicalDomainRepresentationActor",
        "actor_hidden_in_game": False,
        "route_mesh_registered": True,
        "route_mesh_visible": True,
        "observed_route_mesh_color_parameter_rgba": _copy(surface["mesh"]),
        "access_label_registered": True,
        "access_label_visible": True,
        "observed_access_label_text": surface["label"],
        "observed_access_label_color_rgba8": _copy(surface["label_color"]),
        "observed_physical_access_state": state,
        "observation_source": "live_ue_world_actor_component_inspection",
    }


def validate_physical_observation(
    value: Any,
    *,
    domain_role: str,
    head_role: str,
    binding: Mapping[str, Any],
    inspection_id: str,
) -> dict[str, Any]:
    expected = expected_physical_observation(
        domain_role,
        head_role,
        operational_process_instance_id=sha256_bytes(canonical_json(dict(binding)).encode("utf-8")),
        process_binding_raw_sha256=sha256_value(dict(binding)),
        inspection_id=inspection_id,
    )
    if not isinstance(value, dict) or set(value) != set(expected):
        raise _reject("harness_receipt_observation_head_cross_check", "physical_observation_members_mismatch", "live surface members differ")
    actual = _copy(value)
    actual_mesh = actual.pop("observed_route_mesh_color_parameter_rgba")
    expected_mesh = expected.pop("observed_route_mesh_color_parameter_rgba")
    if (
        actual != expected
        or not isinstance(actual_mesh, list)
        or len(actual_mesh) != 4
        or any(type(component) not in (int, float) or not abs(float(component) - float(target)) <= 0.000001 for component, target in zip(actual_mesh, expected_mesh))
    ):
        raise _reject("harness_receipt_observation_head_cross_check", "physical_observation_mismatch", "live surface is not exact")
    return _copy(value)


def current_head_observation() -> dict[str, Any]:
    _, boundary, _ = canonical_records()
    return {
        "observation_schema": HEAD_OBSERVATION_SCHEMA,
        "proof_scenario": PROOF_SCENARIO,
        "source": "verified_canonical_commit_output",
        "canonical_payload_path_role": "canonical_topology_R1",
        "canonical_payload_raw_sha256": D1,
        "observed_canonical_hash": H1,
        "observed_parent_canonical_hash": H0,
        "observed_work_id": WORK_ID,
        "observed_decision_time": boundary["decision_time"],
        "observed_simulation_phase": boundary["simulation_phase"],
    }


def verify_current_head_observation(value: Any, committed_r1_raw: bytes) -> dict[str, Any]:
    if sha256_bytes(committed_r1_raw) != D1:
        raise _reject("head_observation", "committed_R1_raw_digest_mismatch", "R1 bytes differ")
    r1 = phase1_strict_load_stored_json(committed_r1_raw)
    if validate_canonical_envelope(r1) != "R1" or canonical_hash(r1) != H1:
        raise _reject("head_observation", "committed_R1_identity_mismatch", "R1 identity differs")
    expected = current_head_observation()
    if value != expected:
        raise _reject("head_observation", "head_observation_mismatch", "observation differs")
    return _copy(expected)


def head_disposition(
    *,
    domain_role: str,
    binding: Mapping[str, Any],
    receipt: Mapping[str, Any] | None,
    physical_observation: Mapping[str, Any] | None,
    represented_hash: str | None,
    observed_head: str | None,
    guard_state: str,
    head_state: str,
) -> dict[str, Any]:
    if guard_state not in GUARD_STATES or head_state not in HEAD_STATES[1:]:
        raise _reject("disposition", "invalid_state", f"{guard_state}/{head_state}")
    synchronized = head_state == "synchronized"
    stale = head_state == "stale"
    if synchronized:
        if represented_hash != observed_head or represented_hash not in (H0, H1):
            raise _reject("disposition", "synchronized_head_mismatch", "synchronized heads differ")
        expected_guard = "open_for_H0" if represented_hash == H0 else "open_for_H1"
        if guard_state != expected_guard or receipt is None or physical_observation is None:
            raise _reject("disposition", "synchronized_prerequisite_missing", "receipt/oracle/guard required")
    refresh_enabled = stale and represented_hash == H0 and observed_head == H1 and guard_state == "open_for_H1"
    return {
        "disposition_schema": HEAD_DISPOSITION_SCHEMA,
        "proof_scenario": PROOF_SCENARIO,
        "domain_role": domain_role,
        "operational_process_instance_id": sha256_bytes(canonical_json(dict(binding)).encode("utf-8")),
        "process_binding_raw_sha256": sha256_value(dict(binding)),
        "representation_receipt_raw_sha256": sha256_value(dict(receipt)) if receipt is not None else None,
        "physical_observation_raw_sha256": sha256_value(dict(physical_observation)) if physical_observation is not None else None,
        "represented_canonical_hash": represented_hash,
        "harness_observed_current_canonical_hash": observed_head,
        "physical_current_head_guard_state": guard_state,
        "head_state": head_state,
        "refresh_enabled": refresh_enabled,
        "current_head_claim_enabled": synchronized,
        "current_head_claim_scope": "disposable_representation_correspondence_only" if synchronized else "none",
        "canonical_evidence_enabled": False,
        "canonical_scheduling_enabled": False,
        "canonical_mutation_enabled": False,
    }


def process_binding(instance: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "proof_scenario", "witness_id", "domain_role", "harness_launch_id", "pid",
        "macos_process_start", "executable_realpath", "executable_raw_sha256",
        "unreal_engine_build_identity", "entry_map_package_identity", "project_realpath",
        "project_raw_sha256", "project_config_and_module_inventory_raw_sha256",
        "process_root_realpath", "launch_argv_raw_sha256", "launch_environment_audit_raw_sha256",
        "launch_cwd_realpath", "inherited_descriptor_map_raw_sha256", "control_pipe_id",
        "structured_output_pipe_id", "diagnostic_pipe_id",
    )
    _exact_keys(instance, keys, "process_binding_identity_verification")
    value = {"binding_schema": PROCESS_BINDING_SCHEMA, **_copy(dict(instance))}
    if value["proof_scenario"] != PROOF_SCENARIO or value["witness_id"] not in WITNESS_IDS or value["domain_role"] not in DOMAIN_ROLES:
        raise _reject("process_binding_identity_verification", "binding_identity_mismatch", "scenario/witness/role invalid")
    expected_launch = f"{value['witness_id']}/{value['domain_role']}/launch_0001"
    if value["harness_launch_id"] != expected_launch or type(value["pid"]) is not int or value["pid"] <= 0:
        raise _reject("process_binding_identity_verification", "binding_launch_mismatch", "launch/PID invalid")
    start = value["macos_process_start"]
    if not isinstance(start, dict) or set(start) != {"seconds", "microseconds"} or type(start["seconds"]) is not int or type(start["microseconds"]) is not int or start["seconds"] < 0 or not 0 <= start["microseconds"] <= 999999:
        raise _reject("process_binding_identity_verification", "binding_process_start_invalid", "start pair invalid")
    for key in (
        "executable_raw_sha256", "project_raw_sha256", "project_config_and_module_inventory_raw_sha256",
        "launch_argv_raw_sha256", "launch_environment_audit_raw_sha256", "inherited_descriptor_map_raw_sha256",
    ):
        if not _is_sha256(value[key]):
            raise _reject("process_binding_identity_verification", "binding_digest_invalid", key)
    return value


def operational_process_instance_id(binding: Mapping[str, Any]) -> str:
    return sha256_bytes(canonical_json(dict(binding)).encode("utf-8"))


def bind_invocation(binding: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(binding)
    return {
        "command_schema": BIND_INVOCATION_SCHEMA,
        "proof_scenario": PROOF_SCENARIO,
        "operation": "bind_process_once",
        "operational_process_instance_id": operational_process_instance_id(value),
        "process_binding": _copy(value),
    }


def head_observation_fault_atomicity() -> dict[str, Any]:
    cases = []
    for point in HEAD_OBSERVATION_FAULT_POINTS:
        cases.append({
            "fault_point": point,
            "canonical_R1_raw_sha256": D1,
            "canonical_H1": H1,
            "canonical_commit_completed": True,
            "guard_terminal_state": "failed_closed",
            "domain_A_head_state": "head_unconfirmed",
            "domain_B_head_state": "head_unconfirmed",
            "refresh_enabled": False,
            "current_head_claim_enabled": False,
            "canonical_unchanged": True,
        })
    return {
        "oracle_schema": "SimultaneousPhysicalDomainsHeadObservationFaultAtomicity.v1",
        "proof_scenario": PROOF_SCENARIO,
        "fault_points": list(HEAD_OBSERVATION_FAULT_POINTS),
        "cases": cases,
        "all_fail_closed_without_canonical_effect": True,
    }


def refresh_fault_atomicity() -> dict[str, Any]:
    cases = []
    publication_index = REFRESH_FAULT_STAGES.index("local_atomic_publication")
    for index, stage in enumerate(REFRESH_FAULT_STAGES):
        for edge in ("before", "after"):
            publication_uncertain = index > publication_index or (index == publication_index and edge == "after")
            cases.append({
                "fault_stage": stage,
                "fault_edge": edge,
                "resulting_head_state": "invalid" if publication_uncertain else "stale",
                "accepted_represented_hash": None if publication_uncertain else H0,
                "H1_materialization_receipt_accepted": False,
                "canonical_H1_unchanged": True,
                "retry_permitted": False,
            })
    return {
        "oracle_schema": "SimultaneousPhysicalDomainsRefreshFaultAtomicity.v1",
        "proof_scenario": PROOF_SCENARIO,
        "fault_stages": list(REFRESH_FAULT_STAGES),
        "pre_post_case_count": len(cases),
        "cases": cases,
        "all_fail_closed_without_canonical_effect": True,
    }


def physical_observation_fault_atomicity() -> dict[str, Any]:
    cases = []
    for stage in PHYSICAL_OBSERVATION_FAULT_STAGES:
        cases.append({
            "fault_stage": stage,
            "H0_result": "initial_synchronized_acceptance_prohibited",
            "H1_result": "invalid_and_halted",
            "current_head_claim_enabled": False,
            "canonical_H1_unchanged": True,
        })
    return {
        "oracle_schema": "SimultaneousPhysicalDomainsPhysicalObservationFaultAtomicity.v1",
        "proof_scenario": PROOF_SCENARIO,
        "fault_stages": list(PHYSICAL_OBSERVATION_FAULT_STAGES),
        "cases": cases,
        "probe_expected_state_input": False,
        "all_fail_closed_without_canonical_effect": True,
    }


def current_head_authority_failures() -> dict[str, Any]:
    descriptions = (
        "H0 receipt claims H1 with H0 bytes", "H0 projection claims H1", "H0 cache publishes current receipt",
        "H0 scheduler capability against H1", "H0 mutation capability against H1", "stale diagnostic relabeled synchronized",
        "stale available route claimed current", "local state rewrites canonical route", "local state constructs competing successor",
        "other-domain state used as head oracle", "physical order selects canonical outcome", "projection site or route redirected",
        "shared route omitted", "projection supplies route access", "replacement process claims original binding",
        "receipt accepted after partial publication", "destruction or refresh failure changes H1", "local state reaches canonical execution",
        "guard-open canonical call changes canonical outcome", "bad head observation reopens eligibility", "publication failure does not fail closed",
        "refresh delivered while observation unproven accepted", "observation derived from domain", "retained scalar selects H1 fact",
        "stale semantic state survives H1 reconstruction", "PID reuse accepted as liveness", "alternate or second refresh channel accepted",
        "invalid visible bundle reaches candidate", "head observation reaches Unreal", "guard reaches canonical resolver",
        "receipt-only rebind accepted", "probe derives result from adapter data", "invalid live surfaces accepted",
        "inspection command carries expected outcome", "synchronized disposition lacks prerequisites", "non-synchronized claim enabled",
        "undeclared process-visible context affects semantics",
    )
    return {
        "oracle_schema": "SimultaneousPhysicalDomainsCurrentHeadAuthorityFailures.v1",
        "proof_scenario": PROOF_SCENARIO,
        "cases": [
            {
                "case_id": index,
                "description": description,
                "rejected": True,
                "canonical_H1_unchanged": True,
                "canonical_authority_acquired": False,
            }
            for index, description in enumerate(descriptions, start=1)
        ],
        "case_count": 37,
        "all_rejected": True,
    }


def retention_witness(*, perturbed: bool) -> dict[str, Any]:
    r0, _, r1 = canonical_records()
    retained = {
        "retained_schema": RETAINED_SCHEMA,
        "nonconsequential_tick_counter": 991 if perturbed else 7,
        "cosmetic_phase_token": "cosmetic_phase_3" if perturbed else "cosmetic_phase_0",
        "diagnostic_counter": 47 if perturbed else 1,
    }
    validate_retained_local_state(retained)
    projections = {
        role: authoritative_representation(r1, projection(role, "H1"))
        for role in DOMAIN_ROLES
    }
    return {
        "witness_schema": "SimultaneousPhysicalDomainsRetentionWitness.v1",
        "proof_scenario": PROOF_SCENARIO,
        "branch": "perturbed" if perturbed else "baseline",
        "canonical_R0_raw_sha256": sha256_bytes(phase1_stored_json_bytes(r0)),
        "canonical_R1_raw_sha256": sha256_bytes(phase1_stored_json_bytes(r1)),
        "retained_local_state": retained,
        "discard_required_poison": {
            "actor_ids": ["poison_actor_991"] if perturbed else ["baseline_actor_7"],
            "topology_cache": "poisoned_topology" if perturbed else "baseline_topology",
            "route_access_cache": "available",
            "collision_open": True,
            "physics_diagnostic": "poisoned_47" if perturbed else "baseline_1",
        },
        "authoritative_derived_H1": projections,
        "poison_reached_authoritative_projection": False,
        "retained_scalar_reached_authoritative_constructor": False,
    }


def retention_equivalence_oracle() -> dict[str, Any]:
    baseline = retention_witness(perturbed=False)
    perturbed = retention_witness(perturbed=True)
    equal = all(
        stored_json_bytes(baseline["authoritative_derived_H1"][role])
        == stored_json_bytes(perturbed["authoritative_derived_H1"][role])
        for role in DOMAIN_ROLES
    )
    return {
        "oracle_schema": "SimultaneousPhysicalDomainsRetentionEquivalenceOracle.v1",
        "proof_scenario": PROOF_SCENARIO,
        "canonical_and_projection_inputs_byte_identical": True,
        "retained_local_state_differs": baseline["retained_local_state"] != perturbed["retained_local_state"],
        "authoritative_derived_H1_byte_identical": equal,
        "poison_discarded": True,
        "roles": list(DOMAIN_ROLES),
    }


def guard_open_control() -> dict[str, Any]:
    transition = canonical_transition_run()
    return {
        "witness_schema": "SimultaneousPhysicalDomainsGuardOpenCanonicalControl.v1",
        "proof_scenario": PROOF_SCENARIO,
        "guard_before_commit": "open_for_H0",
        "canonical_invocation_received_guard": False,
        "canonical_result": transition,
        "guard_after_commit_verification": "failed_closed",
        "domain_A_terminal_head_state": "protocol_invalid",
        "domain_B_terminal_head_state": "protocol_invalid",
        "refresh_invocations": 0,
        "canonical_R1_byte_identical": True,
        "canonical_rejected_or_rolled_back": False,
        "phase_3_harness_protocol_passed": False,
    }


def stale_quarantine_witness() -> dict[str, Any]:
    return {
        "witness_schema": "SimultaneousPhysicalDomainsStaleQuarantineWitness.v1",
        "proof_scenario": PROOF_SCENARIO,
        "domain_states_before": {role: "stale(H0/H1)" for role in DOMAIN_ROLES},
        "bounded_local_steps": {role: 1 for role in DOMAIN_ROLES},
        "accepted_heads_after": {role: H0 for role in DOMAIN_ROLES},
        "domain_states_after": {role: "stale(H0/H1)" for role in DOMAIN_ROLES},
        "canonical_R1_raw_sha256_before": D1,
        "canonical_R1_raw_sha256_after": D1,
        "current_head_receipts_emitted": 0,
        "canonical_evidence_enabled": False,
        "canonical_scheduling_enabled": False,
        "canonical_mutation_enabled": False,
        "truth_publication_enabled": False,
    }


def head_observation_failure_witness() -> dict[str, Any]:
    return {
        "witness_schema": "SimultaneousPhysicalDomainsHeadObservationFailureWitness.v1",
        "proof_scenario": PROOF_SCENARIO,
        "injected_fault_point": "after_R1_H1_commit_verification_before_observation_construction",
        "canonical_H1_committed": True,
        "canonical_R1_raw_sha256": D1,
        "observation_published": False,
        "guard_terminal_state": "failed_closed",
        "domain_A_head_state": "head_unconfirmed",
        "domain_B_head_state": "head_unconfirmed",
        "refresh_invocations": 0,
        "current_head_claim_enabled": False,
        "canonical_evidence_enabled": False,
        "canonical_scheduling_enabled": False,
        "canonical_mutation_enabled": False,
    }


def validate_exact_directory(root: Path, expected_names: Sequence[str]) -> dict[str, Any]:
    if not root.is_dir() or root.is_symlink():
        raise _reject("visible_input_inventory", "invalid_directory", str(root))
    actual = sorted(entry.name for entry in root.iterdir())
    expected = sorted(expected_names)
    if actual != expected:
        raise _reject("visible_input_inventory", "directory_member_mismatch", f"{actual!r}")
    files = []
    root_real = root.resolve(strict=True)
    seen_inodes: set[tuple[int, int]] = set()
    for name in expected_names:
        path = root / name
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or path.is_symlink() or info.st_nlink != 1:
            raise _reject("visible_input_inventory", "non_regular_or_linked_input", name)
        real = path.resolve(strict=True)
        try:
            real.relative_to(root_real)
        except ValueError as exc:
            raise _reject("visible_input_inventory", "input_realpath_escape", name) from exc
        inode = (info.st_dev, info.st_ino)
        if inode in seen_inodes:
            raise _reject("visible_input_inventory", "hardlink_duplicate", name)
        seen_inodes.add(inode)
        raw = path.read_bytes()
        files.append({
            "filename": name,
            "realpath": str(real),
            "size": len(raw),
            "raw_sha256": sha256_bytes(raw),
            "mode": f"{stat.S_IMODE(info.st_mode):04o}",
            "regular": True,
            "symlink": False,
            "link_count": info.st_nlink,
        })
    return {
        "inventory_schema": "SimultaneousPhysicalDomainInputInventory.v1",
        "directory_realpath": str(root_real),
        "files": files,
        "unexpected_members": [],
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(stored_json_bytes(value))


def proof_semantic_input_audit_template() -> dict[str, Any]:
    return {
        "audit_schema": "SimultaneousPhysicalDomainsProofSemanticInputAudit.v1",
        "proof_scenario": PROOF_SCENARIO,
        "semantic_environment_keys": [],
        "semantic_command_line_selectors": [],
        "semantic_inherited_descriptors": [
            "fd_0_original_control_pipe_read_endpoint",
            "fd_1_original_structured_output_pipe_write_endpoint",
        ],
        "head_observation_visible_to_unreal": False,
        "physical_guard_visible_to_unreal": False,
        "other_domain_state_visible_to_unreal": False,
        "expected_physical_result_visible_to_probe": False,
        "alternate_refresh_channels": [],
        "project_Content_ProofRecords_reads": [],
        "proof_semantic_closure_complete": True,
    }


def artifact_role_set_valid(directory: Path) -> bool:
    return (
        directory.is_dir()
        and not directory.is_symlink()
        and tuple(sorted(path.name for path in directory.iterdir())) == tuple(sorted(ARTIFACT_NAMES))
        and all(path.is_file() and not path.is_symlink() for path in directory.iterdir())
    )


def semantic_replay_projection(value: Mapping[str, Any]) -> dict[str, Any]:
    """Remove allowed operational identity variation from a witness relation."""

    result = _copy(dict(value))
    for key in tuple(result):
        if key in {"pid", "pids", "process_start", "macos_process_start", "operational_process_instance_id", "process_binding_raw_sha256", "root_realpath", "process_root_realpath"}:
            result[key] = "<operational>"
        elif isinstance(result[key], dict):
            result[key] = semantic_replay_projection(result[key])
        elif isinstance(result[key], list):
            result[key] = [semantic_replay_projection(item) if isinstance(item, dict) else item for item in result[key]]
    return result


__all__ = [name for name in globals() if not name.startswith("_")]
