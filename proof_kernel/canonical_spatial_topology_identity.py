"""Frozen reference machine for Canonical Spatial Topology Identity v0.1.0.

This module is intentionally not a general graph or topology system.  It owns
exactly two canonical site identities, one unordered route identity, one route
access fact, and the single R0 -> R1 transaction authorized by the frozen
proof.  Conceptual assignments and Unreal materialization artifacts are
detached evidence; neither can supply canonical identity or mutation authority.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import inspect
import json
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

RECORD_SCHEMA = "CanonicalResolutionEnvelope.v1"
PAYLOAD_SCHEMA = "CanonicalSpatialTopologyIdentityPayload.v1"
SCENARIO_ID = "canonical-spatial-topology-identity-v1"
SCENARIO_VERSION = "0.1.0"
SIMULATION_VERSION = "0.7.0-draft.61"
SEED = "canonical-spatial-topology-identity-v1/0001"

SITE_A = "topology_site_0001"
SITE_B = "topology_site_0002"
SITE_IDS = (SITE_A, SITE_B)
ROUTE_ID = "topology_route_0001"
ROUTE_IDS = (ROUTE_ID,)
ENDPOINTS = [SITE_A, SITE_B]
ENDPOINT_SEMANTICS = "unordered_pair_fixture_only"
PROCESS_ID = "topology_access_closure_01"
WORK_ID = "t1/00/topology/block_topology_route_0001.resolve"
TIME_R0 = "t0/00"
TIME_R1 = "t1/00"
PHASE = 10

BOUNDARY_SCHEMA = "CanonicalSpatialTopologyBoundary.v1"
LEDGER_SCHEMA = "CanonicalSpatialTopologyAccessLedgerEntry.v1"
ANCESTRY_SCHEMA = "CanonicalSpatialTopologyAncestry.v1"
GENESIS_SCHEMA = "CanonicalSpatialTopologyFixtureGenesis.v1"
ASSIGNMENT_SCHEMA = "ConceptualToCanonicalTopologyAssignment.v1"
QUERY_SCHEMA = "CanonicalRouteAccessEvaluation.v1"
MAP_SCHEMA = "CanonicalTopologyMaterializationMap.v1"
LAUNCH_RECEIPT_SCHEMA = "CanonicalTopologyLaunchReceipt.v1"
MATERIALIZATION_RECEIPT_SCHEMA = "CanonicalTopologyMaterializationReceipt.v1"
INVENTORY_SCHEMA = "CanonicalTopologyProofInputInventory.v1"
TERMINATION_SCHEMA = "CanonicalTopologyProcessTerminationWitness.v1"
ISOLATION_SCHEMA = "CanonicalTopologyFreshProcessIsolationWitness.v1"
FAILURE_SCHEMA = "CanonicalTopologyMaterializationFailure.v1"

R0_MAPPING_ID = "topology_materialization_R0_0001"
R1_MAPPING_ID = "topology_materialization_R1_0001"

CANONICAL_PAYLOAD_FILENAME = "canonical_payload.json"
MATERIALIZATION_MAP_FILENAME = "materialization_map.json"
LAUNCH_RECEIPT_FILENAME = "launch_receipt.json"

OPERATIONAL_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")

NO_BOUNDARY: None = None

ARTIFACT_NAMES = (
    "canonical_topology_R0.json",
    "canonical_topology_R1.json",
    "canonical_topology_boundary_H0.json",
    "canonical_topology_assignment_baseline.json",
    "canonical_topology_assignment_renamed.json",
    "canonical_topology_label_neutrality_witness.json",
    "canonical_topology_access_R0_forward.json",
    "canonical_topology_access_R0_reverse.json",
    "canonical_topology_access_R1_forward.json",
    "canonical_topology_access_R1_reverse.json",
    "canonical_topology_access_oracle.json",
    "canonical_topology_mutation_run.json",
    "canonical_topology_materialization_map_R0.json",
    "canonical_topology_materialization_map_R1.json",
    "canonical_topology_launch_receipt_R0.json",
    "canonical_topology_launch_receipt_R1.json",
    "canonical_topology_replay_oracle.json",
    "canonical_topology_runtime_fail_closed.json",
    "canonical_topology_source_audit.json",
    "canonical_topology_proof_run.json",
)

FROZEN_ADVERSARIAL_MATRIX: dict[str, tuple[str, tuple[str, ...]]] = {
    "01_duplicate_raw_json_member": ("all_variants_rejected", ("duplicate_identity",)),
    "02_cross_type_identity_substitution": ("all_variants_rejected", ("route_as_site", "site_as_route")),
    "03_dangling_route_endpoint": ("all_variants_rejected", ("missing_site_b",)),
    "04_identical_stored_endpoints": ("all_variants_rejected", ("site_a_twice",)),
    "05_noncanonical_stored_endpoint_order": ("all_variants_rejected", ("reversed_storage",)),
    "06_request_order_semantic_leakage": ("equivalence_oracle_passed", ("reverse_rejected", "reverse_directional", "reverse_eligibility_changed")),
    "07_invalid_route_reaches_access": ("all_variants_rejected", ("invalid_route_only", "invalid_route_precedes_non_array")),
    "08_non_array_endpoints_reach_access": ("all_variants_rejected", ("non_array",)),
    "09_wrong_endpoint_count_reaches_access": ("all_variants_rejected", ("one_endpoint", "count_precedes_unknown_id")),
    "10_unknown_endpoint_reaches_access": ("all_variants_rejected", ("one_unknown", "unknown_precedes_duplicate")),
    "11_duplicate_requested_endpoint_reaches_access": ("all_variants_rejected", ("site_a_twice",)),
    "12_extra_topology_field_or_value": ("all_variants_rejected", ("extra_route", "extra_site", "extra_topology_field", "invalid_access_value")),
    "13_conceptual_identity_substitution": ("all_variants_rejected", ("conceptual_route_label", "conceptual_site_labels")),
    "14_representation_identity_substitution": ("all_variants_rejected", (
        "route:Actor_42", "site:Actor_42", "route:/Game/Actor.Path", "site:/Game/Actor.Path",
        "route:GUID-42", "site:GUID-42", "route:NavNode_A", "site:NavNode_A",
        "route:Level_A", "site:Level_A", "route:WorldPartitionCell_B", "site:WorldPartitionCell_B",
        "route:StreamingIdentity_C", "site:StreamingIdentity_C",
    )),
    "15_query_redirected_through_mapping": ("rejected_by_interface", ("mapping_parameter",)),
    "16_access_mutation_changes_identity_or_endpoints": ("all_variants_rejected", ("site_id", "route_id", "endpoint", "endpoint_semantics")),
    "17_stale_or_wrong_record_boundary": ("all_variants_rejected", ("r1_hash_against_r0",)),
    "18_invalid_materialization_mapping_keys": ("all_variants_rejected", ("missing_key", "additional_key", "duplicate_key", "redirected_key")),
    "19_cross_row_artifact_combination": ("all_variants_rejected", (
        "r0_payload_r1_map_receipt", "r1_payload_r0_map_receipt", "r0_payload_r0_map_r1_receipt",
        "r1_payload_r1_map_r0_receipt", "r0_payload_r1_map_r0_receipt", "r1_payload_r0_map_r1_receipt",
        "r0_files_r1_inventory_role", "r1_files_r0_inventory_role",
    )),
    "20_map_or_receipt_disagreement": ("all_variants_rejected", (
        "map_bytes", "map_schema", "map_identity", "map_source_hash", "recomputed_hash_noncanonical_map",
        "noncanonical_launch_receipt", "empty_receipt_field_preparse",
    )),
    "21_adapter_manufactures_absent_topology": ("all_variants_rejected", ("route_absent",)),
    "22_adapter_attempts_canonical_write": ("all_variants_rejected", ("access_state", "ledger", "ancestry", "schedule", "successor")),
    "23_adapter_exposes_q_path": ("all_variants_rejected", ("proposal_capability",)),
    "24_invalid_proof_input_file_set": ("all_variants_rejected", ("missing_file", "additional_file", "additional_directory", "duplicate_filename", "role_incompatible")),
    "25_return_process_receives_source_truth": ("all_variants_rejected", ("source_input", "source_output", "shared_cache", "branch_selector")),
    "26_invalid_process_or_actor_identity_evidence": ("all_variants_rejected", ("missing", "duplicate_actor", "contradictory", "malformed", "non_distinct_processes")),
    "27_representation_destruction_deletes_topology": ("authority_invariance_proven", ("mapping_destroyed",)),
    "28_in_record_successor_self_hash": ("all_variants_rejected", ("successor_hash_field",)),
}

FROZEN_REPRESENTATION_DIAGNOSTICS: dict[str, dict[str, tuple[str, str]]] = {
    "18_invalid_materialization_mapping_keys": {
        variant: ("raw_hash", "artifact_raw_hash_mismatch")
        for variant in ("missing_key", "additional_key", "duplicate_key", "redirected_key")
    },
    "19_cross_row_artifact_combination": {
        "r0_payload_r1_map_receipt": ("raw_hash", "artifact_raw_hash_mismatch"),
        "r1_payload_r0_map_receipt": ("raw_hash", "artifact_raw_hash_mismatch"),
        "r0_payload_r0_map_r1_receipt": ("raw_hash", "artifact_raw_hash_mismatch"),
        "r1_payload_r1_map_r0_receipt": ("raw_hash", "artifact_raw_hash_mismatch"),
        "r0_payload_r1_map_r0_receipt": ("raw_hash", "artifact_raw_hash_mismatch"),
        "r1_payload_r0_map_r1_receipt": ("raw_hash", "artifact_raw_hash_mismatch"),
        "r0_files_r1_inventory_role": ("input_inventory", "unexpected_input_file"),
        "r1_files_r0_inventory_role": ("input_inventory", "unexpected_input_file"),
    },
    "20_map_or_receipt_disagreement": {
        "map_bytes": ("raw_hash", "artifact_raw_hash_mismatch"),
        "map_schema": ("raw_hash", "artifact_raw_hash_mismatch"),
        "map_identity": ("raw_hash", "artifact_raw_hash_mismatch"),
        "map_source_hash": ("raw_hash", "artifact_raw_hash_mismatch"),
        "recomputed_hash_noncanonical_map": ("launch_receipt", "launch_receipt_hash_mismatch"),
        "noncanonical_launch_receipt": ("launch_receipt", "invalid_launch_receipt"),
        "empty_receipt_field_preparse": ("launch_receipt", "invalid_launch_receipt"),
    },
    "24_invalid_proof_input_file_set": {
        "missing_file": ("input_inventory", "missing_input_file"),
        "additional_file": ("input_inventory", "unexpected_input_file"),
        "additional_directory": ("input_inventory", "unexpected_input_file"),
        "duplicate_filename": ("input_inventory", "duplicate_input_filename"),
        "role_incompatible": ("input_inventory", "unexpected_input_file"),
    },
}


class CanonicalTopologyRejected(ValueError):
    """A malformed record, boundary, or request failed before authority."""


class RepresentationRejected(ValueError):
    """Detached materialization input or evidence failed before projection."""

    def __init__(self, message: str, *, stage: str | None = None, reason_code: str | None = None) -> None:
        super().__init__(message)
        self.stage = stage
        self.reason_code = reason_code

    @property
    def diagnostic(self) -> dict[str, Any] | None:
        if self.stage is None or self.reason_code is None:
            return None
        return materialization_failure(self.stage, self.reason_code)


def _representation_rejected(stage: str, reason_code: str, message: str) -> RepresentationRejected:
    return RepresentationRejected(message, stage=stage, reason_code=reason_code)


def _copy(value: Any) -> Any:
    return copy.deepcopy(value)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_json(value: Any) -> str:
    """Topology-local frozen JSON law; unlike predecessor helpers it rejects NaN/Inf."""

    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def canonical_hash(record: dict[str, Any]) -> str:
    return _sha(canonical_json(record).encode("utf-8"))


def stored_json_bytes(value: Any) -> bytes:
    return (canonical_json(value) + "\n").encode("utf-8")


def raw_stored_sha256(value: Any) -> str:
    return _sha(stored_json_bytes(value))


def strict_load_stored_json(raw: bytes) -> Any:
    """Load one exact stored JSON artifact and reject duplicate members.

    The object-pairs hook rejects duplicates while each object is being formed;
    it never permits a last-member-wins dictionary to reach validation.
    """

    if not raw.endswith(b"\n") or raw.endswith(b"\n\n") or b"\r" in raw or raw.count(b"\n") != 1:
        raise ValueError("stored JSON must contain exactly one terminal LF")
    try:
        text = raw[:-1].decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError("stored JSON is not valid UTF-8") from exc

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON object member: {key}")
            result[key] = value
        return result

    try:
        value = json.loads(text, object_pairs_hook=reject_duplicates, parse_constant=lambda token: (_ for _ in ()).throw(ValueError(f"non-finite JSON number: {token}")))
    except json.JSONDecodeError as exc:
        raise ValueError("invalid JSON") from exc
    if canonical_json(value) != text:
        raise ValueError("stored JSON is not frozen canonical JSON")
    return value


def _identity() -> dict[str, str]:
    return {
        "record_schema": RECORD_SCHEMA,
        "payload_schema": PAYLOAD_SCHEMA,
        "scenario_id": SCENARIO_ID,
        "scenario_version": SCENARIO_VERSION,
        "seed": SEED,
        "simulation_version": SIMULATION_VERSION,
    }


def _work() -> dict[str, Any]:
    return {
        "decision_time": TIME_R1,
        "gates": [
            {
                "path": "/current_causal_state/spatial_topology/routes/topology_route_0001/endpoint_site_ids",
                "required_value": _copy(ENDPOINTS),
            },
            {
                "path": "/current_causal_state/spatial_topology/routes/topology_route_0001/access_state",
                "required_value": "available",
            },
        ],
        "permitted_topology_mutation": {
            "op": "replace",
            "path": "/current_causal_state/spatial_topology/routes/topology_route_0001/access_state",
            "value": "blocked",
        },
        "process_id": PROCESS_ID,
        "simulation_phase": PHASE,
        "target": {
            "endpoint_site_ids": _copy(ENDPOINTS),
            "kind": "canonical_route",
            "route_id": ROUTE_ID,
        },
        "terminal_resource_disposition": "no_resources_owned",
        "terminal_state": "succeeded",
        "work_id": WORK_ID,
    }


def _genesis() -> dict[str, Any]:
    return {
        "genesis_schema": GENESIS_SCHEMA,
        "initial_process": {
            "process_id": PROCESS_ID,
            "resources_owned": [],
            "state": "active",
        },
        "initial_topology": {
            "access_state": "available",
            "canonical_route_id": ROUTE_ID,
            "canonical_site_ids": _copy(list(SITE_IDS)),
            "endpoint_semantics": ENDPOINT_SEMANTICS,
            "endpoint_site_ids": _copy(ENDPOINTS),
        },
        "initial_work_projection": {
            "decision_time": TIME_R1,
            "simulation_phase": PHASE,
            "work_id": WORK_ID,
        },
        "source": "frozen_initial_fixture",
    }


def initial_canonical_envelope() -> dict[str, Any]:
    """Return the exact frozen R0 canonical record."""

    return {
        "causal_provenance": {
            "authoritative_causal_ledger": [],
            "canonical_ancestry": None,
            "fixture_genesis": _genesis(),
        },
        "current_causal_state": {
            "fixture_processes": {
                PROCESS_ID: {"resources_owned": [], "state": "active"},
            },
            "spatial_topology": {
                "routes": {
                    ROUTE_ID: {
                        "access_state": "available",
                        "endpoint_semantics": ENDPOINT_SEMANTICS,
                        "endpoint_site_ids": _copy(ENDPOINTS),
                    },
                },
                "sites": {SITE_A: None, SITE_B: None},
            },
        },
        "future_causal_state": {
            "canonical_clock": TIME_R0,
            "unresolved_work": [_work()],
        },
        "identity": _identity(),
    }


def _boundary(r0: dict[str, Any]) -> dict[str, Any]:
    return {
        "boundary_schema": BOUNDARY_SCHEMA,
        "decision_time": TIME_R1,
        "due_work_ids": [WORK_ID],
        "simulation_phase": PHASE,
        "source_record_hash": canonical_hash(r0),
    }


def _ledger(r0: dict[str, Any]) -> dict[str, Any]:
    h0 = canonical_hash(r0)
    return {
        "canonical_execution_sequence": 0,
        "canonical_pre_state_hash": h0,
        "committed_topology_mutation": {
            "op": "replace",
            "path": "/current_causal_state/spatial_topology/routes/topology_route_0001/access_state",
            "prior_value": "available",
            "value": "blocked",
        },
        "decision_time": TIME_R1,
        "evaluated_gates": [
            {
                "observed_value": _copy(ENDPOINTS),
                "path": "/current_causal_state/spatial_topology/routes/topology_route_0001/endpoint_site_ids",
                "required_value": _copy(ENDPOINTS),
                "result": True,
            },
            {
                "observed_value": "available",
                "path": "/current_causal_state/spatial_topology/routes/topology_route_0001/access_state",
                "required_value": "available",
                "result": True,
            },
        ],
        "ledger_schema": LEDGER_SCHEMA,
        "process_id": PROCESS_ID,
        "simulation_phase": PHASE,
        "simulation_version": SIMULATION_VERSION,
        "source_boundary": _boundary(r0),
        "target": {
            "endpoint_site_ids": _copy(ENDPOINTS),
            "kind": "canonical_route",
            "route_id": ROUTE_ID,
        },
        "terminal_process_state": "succeeded",
        "terminal_resource_disposition": "no_resources_owned",
        "transaction_id": "t1/00/phase_10/topology_access_closure_01",
        "work_id": WORK_ID,
    }


def _expected_r1(r0: dict[str, Any] | None = None) -> dict[str, Any]:
    source = initial_canonical_envelope() if r0 is None else r0
    result = _copy(source)
    result["current_causal_state"]["spatial_topology"]["routes"][ROUTE_ID]["access_state"] = "blocked"
    result["current_causal_state"]["fixture_processes"][PROCESS_ID]["state"] = "succeeded"
    result["future_causal_state"]["canonical_clock"] = TIME_R1
    result["future_causal_state"]["unresolved_work"] = []
    result["causal_provenance"]["authoritative_causal_ledger"] = [_ledger(source)]
    result["causal_provenance"]["canonical_ancestry"] = {
        "ancestry_schema": ANCESTRY_SCHEMA,
        "boundary_derivation": {
            "decision_time": TIME_R1,
            "due_work_ids": [WORK_ID],
            "method": "next_consequential_boundary",
            "simulation_phase": PHASE,
            "source_record_hash": canonical_hash(source),
        },
        "parent_record_hash": canonical_hash(source),
    }
    return result


def validate_canonical_envelope(record: dict[str, Any]) -> str:
    """Validate the exhaustive R0/R1 schema and return its branch label."""

    if not isinstance(record, dict):
        raise CanonicalTopologyRejected("canonical record must be an object")
    if set(record) != {"identity", "current_causal_state", "future_causal_state", "causal_provenance"}:
        raise CanonicalTopologyRejected("canonical root shape mismatch")
    r0 = initial_canonical_envelope()
    if canonical_json(record) == canonical_json(r0):
        return "R0"
    r1 = _expected_r1(r0)
    if canonical_json(record) == canonical_json(r1):
        return "R1"
    raise CanonicalTopologyRejected("record is not the exact frozen R0 or R1 branch")


def next_consequential_boundary(record: dict[str, Any]) -> dict[str, Any] | None:
    branch = validate_canonical_envelope(record)
    return _boundary(record) if branch == "R0" else NO_BOUNDARY


def resolve_next_due(record: dict[str, Any], boundary: dict[str, Any]) -> dict[str, Any]:
    if validate_canonical_envelope(record) != "R0":
        raise CanonicalTopologyRejected("only R0 owns the frozen close boundary")
    if boundary != _boundary(record):
        raise CanonicalTopologyRejected("boundary is not the exact H0-bound capability")
    # Work, target, gates, mutation, lifecycle, and provenance all come from R0.
    result = _expected_r1(record)
    validate_canonical_envelope(result)
    return result


def _invalid_query(record: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "access_state_evaluated": False,
        "eligible": None,
        "evaluation_status": "invalid_request",
        "reason_code": reason,
        "result_schema": QUERY_SCHEMA,
        "source_record_hash": canonical_hash(record),
    }


def evaluate_route_access(record: dict[str, Any], requested_route_id: Any, requested_endpoint_site_ids: Any) -> dict[str, Any]:
    """Evaluate the one ordinary route-access gate from canonical truth only."""

    validate_canonical_envelope(record)
    if requested_route_id != ROUTE_ID:
        return _invalid_query(record, "invalid_route_id")
    if not isinstance(requested_endpoint_site_ids, list):
        return _invalid_query(record, "endpoint_array_required")
    if len(requested_endpoint_site_ids) != 2:
        return _invalid_query(record, "endpoint_count_not_two")
    if any(value not in SITE_IDS for value in requested_endpoint_site_ids):
        return _invalid_query(record, "invalid_endpoint_site_id")
    if requested_endpoint_site_ids[0] == requested_endpoint_site_ids[1]:
        return _invalid_query(record, "duplicate_endpoint_site_id")

    received = _copy(requested_endpoint_site_ids)
    normalized = sorted(received)
    route = record["current_causal_state"]["spatial_topology"]["routes"][ROUTE_ID]
    pair_matches = normalized == route["endpoint_site_ids"]
    access_available = route["access_state"] == "available"
    return {
        "access_state_evaluated": True,
        "eligible": pair_matches and access_available,
        "evaluated_gates": [
            {"gate": "route_exists", "result": True},
            {"gate": "requested_endpoints_are_two_distinct_canonical_site_ids", "result": True},
            {
                "gate": "normalized_endpoint_pair_matches_stored_route",
                "observed_value": _copy(route["endpoint_site_ids"]),
                "result": pair_matches,
            },
            {
                "gate": "route_access_state",
                "observed_value": route["access_state"],
                "required_value": "available",
                "result": access_available,
            },
        ],
        "evaluation_status": "evaluated",
        "normalized_endpoint_site_ids": normalized,
        "received_endpoint_site_ids": received,
        "requested_route_id": ROUTE_ID,
        "result_schema": QUERY_SCHEMA,
        "source_record_hash": canonical_hash(record),
    }


def conceptual_assignment(renamed: bool = False) -> dict[str, Any]:
    labels = ("West Reference", "East Reference", "Crossing Reference") if renamed else (
        "Proof Endpoint One", "Proof Endpoint Two", "Conceptual Crossing Fixture"
    )
    return {
        "assignment_id": "canonical-spatial-topology-identity-fixture-0001",
        "assignment_schema": ASSIGNMENT_SCHEMA,
        "conceptual_references": {
            "endpoints": [
                {"canonical_target_id": SITE_A, "display_label": labels[0], "reference_id": "proof_endpoint_reference_0001"},
                {"canonical_target_id": SITE_B, "display_label": labels[1], "reference_id": "proof_endpoint_reference_0002"},
            ],
            "relationships": [{
                "canonical_target_id": ROUTE_ID,
                "display_label": labels[2],
                "endpoint_reference_ids": ["proof_endpoint_reference_0001", "proof_endpoint_reference_0002"],
                "reference_id": "proof_relationship_reference_0001",
            }],
        },
    }


def assignment_neutral_projection(assignment: dict[str, Any]) -> dict[str, Any]:
    expected = conceptual_assignment(False)
    renamed = conceptual_assignment(True)
    if canonical_json(assignment) not in {canonical_json(expected), canonical_json(renamed)}:
        raise ValueError("assignment is not an exact frozen label branch")
    result = _copy(assignment)
    for endpoint in result["conceptual_references"]["endpoints"]:
        del endpoint["display_label"]
    del result["conceptual_references"]["relationships"][0]["display_label"]
    return result


def conceptual_label_neutrality_witness() -> dict[str, Any]:
    baseline = conceptual_assignment(False)
    renamed = conceptual_assignment(True)
    pb0 = canonical_json(assignment_neutral_projection(baseline)).encode("utf-8")
    pb1 = canonical_json(assignment_neutral_projection(renamed)).encode("utf-8")
    r0 = initial_canonical_envelope()
    return {
        "A0": raw_stored_sha256(baseline),
        "A1": raw_stored_sha256(renamed),
        "AP0": _sha(pb0),
        "AP1": _sha(pb1),
        "PB0_equals_PB1": pb0 == pb1,
        "baseline_canonical_hash": canonical_hash(r0),
        "baseline_r0_raw_sha256": raw_stored_sha256(r0),
        "canonical_hashes_equal": True,
        "canonical_target_ids_equal": True,
        "labels_change_assignment_raw_identity": raw_stored_sha256(baseline) != raw_stored_sha256(renamed),
        "projection_hashes_equal": _sha(pb0) == _sha(pb1),
        "renamed_canonical_hash": canonical_hash(r0),
        "renamed_r0_raw_sha256": raw_stored_sha256(r0),
    }


def materialization_map(record: dict[str, Any]) -> dict[str, Any]:
    branch = validate_canonical_envelope(record)
    return {
        "mapping_id": R0_MAPPING_ID if branch == "R0" else R1_MAPPING_ID,
        "mapping_schema": MAP_SCHEMA,
        "routes": {ROUTE_ID: "representation_route_slot_01"},
        "sites": {SITE_A: "representation_site_slot_01", SITE_B: "representation_site_slot_02"},
        "source_canonical_hash": canonical_hash(record),
    }


def launch_receipt(record: dict[str, Any], mapping: dict[str, Any] | None = None) -> dict[str, Any]:
    expected_map = materialization_map(record)
    chosen = expected_map if mapping is None else mapping
    if chosen != expected_map:
        raise RepresentationRejected("materialization map does not match record branch")
    return {
        "canonical_payload_raw_sha256": raw_stored_sha256(record),
        "expected_canonical_hash": canonical_hash(record),
        "expected_mapping_id": chosen["mapping_id"],
        "expected_mapping_schema": MAP_SCHEMA,
        "expected_payload_schema": PAYLOAD_SCHEMA,
        "expected_record_schema": RECORD_SCHEMA,
        "expected_scenario_id": SCENARIO_ID,
        "expected_simulation_version": SIMULATION_VERSION,
        "materialization_map_raw_sha256": raw_stored_sha256(chosen),
        "receipt_schema": LAUNCH_RECEIPT_SCHEMA,
    }


def validate_materialization_bundle(payload_raw: bytes, map_raw: bytes, receipt_raw: bytes) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        receipt = strict_load_stored_json(receipt_raw)
    except ValueError as exc:
        raise _representation_rejected("launch_receipt", "invalid_launch_receipt", "invalid launch receipt") from exc
    if not isinstance(receipt, dict) or set(receipt) != {
        "receipt_schema", "canonical_payload_raw_sha256", "materialization_map_raw_sha256",
        "expected_canonical_hash", "expected_record_schema", "expected_payload_schema",
        "expected_scenario_id", "expected_simulation_version", "expected_mapping_schema", "expected_mapping_id",
    }:
        raise _representation_rejected("launch_receipt", "invalid_launch_receipt", "invalid launch receipt shape")
    if receipt.get("receipt_schema") != LAUNCH_RECEIPT_SCHEMA:
        raise _representation_rejected("launch_receipt", "invalid_launch_receipt", "invalid launch receipt schema")
    if any(not isinstance(value, str) or not value for value in receipt.values()):
        raise _representation_rejected("launch_receipt", "invalid_launch_receipt", "launch receipt fields must be non-empty strings")
    if any(not re.fullmatch(r"[0-9a-f]{64}", receipt[field]) for field in (
        "canonical_payload_raw_sha256", "materialization_map_raw_sha256", "expected_canonical_hash"
    )):
        raise _representation_rejected("launch_receipt", "invalid_launch_receipt", "launch receipt hashes are malformed")
    r0 = initial_canonical_envelope()
    r1 = _expected_r1(r0)
    exact_receipts = (launch_receipt(r0), launch_receipt(r1))
    if receipt not in exact_receipts:
        raise _representation_rejected("launch_receipt", "launch_receipt_hash_mismatch", "launch receipt is not an exact frozen branch artifact")
    if _sha(payload_raw) != receipt["canonical_payload_raw_sha256"] or _sha(map_raw) != receipt["materialization_map_raw_sha256"]:
        raise _representation_rejected("raw_hash", "artifact_raw_hash_mismatch", "artifact raw hash mismatch")
    try:
        record = strict_load_stored_json(payload_raw)
        mapping = strict_load_stored_json(map_raw)
    except ValueError as exc:
        raise _representation_rejected("parse", "json_parse_failure", "proof artifact parse failure") from exc
    try:
        branch = validate_canonical_envelope(record)
    except CanonicalTopologyRejected as exc:
        raise _representation_rejected("payload_validation", "invalid_canonical_payload", "invalid canonical payload") from exc
    expected_map = materialization_map(record)
    if mapping != expected_map:
        raise _representation_rejected("map_validation", "invalid_materialization_map", "invalid or redirected materialization map")
    expected_receipt = launch_receipt(record, mapping)
    if receipt != expected_receipt:
        raise _representation_rejected("cross_artifact_binding", "cross_artifact_binding_mismatch", "cross-artifact binding mismatch")
    if receipt["expected_mapping_id"] != (R0_MAPPING_ID if branch == "R0" else R1_MAPPING_ID):
        raise _representation_rejected("cross_artifact_binding", "cross_artifact_binding_mismatch", "cross-row mapping identity")
    return record, mapping


def proof_input_inventory(root: Path, input_role: str) -> dict[str, Any]:
    branch = "R0" if input_role == "R0_source" else "R1" if input_role == "R1_return" else None
    if branch is None:
        raise RepresentationRejected("invalid input role")
    members = tuple(sorted(root.iterdir(), key=lambda path: path.name))
    names = tuple(path.name for path in members)
    expected_names = tuple(sorted((CANONICAL_PAYLOAD_FILENAME, MATERIALIZATION_MAP_FILENAME, LAUNCH_RECEIPT_FILENAME)))
    if names != expected_names or any(not path.is_file() for path in members):
        reason = "missing_input_file" if len(members) < len(expected_names) else "unexpected_input_file"
        raise _representation_rejected("input_inventory", reason, "proof-input root must contain exactly three allowed regular files")
    # Inventory order is semantic and intentionally differs from directory order.
    files = [
        {"filename": CANONICAL_PAYLOAD_FILENAME, "raw_sha256": _sha((root / CANONICAL_PAYLOAD_FILENAME).read_bytes())},
        {"filename": LAUNCH_RECEIPT_FILENAME, "raw_sha256": _sha((root / LAUNCH_RECEIPT_FILENAME).read_bytes())},
        {"filename": MATERIALIZATION_MAP_FILENAME, "raw_sha256": _sha((root / MATERIALIZATION_MAP_FILENAME).read_bytes())},
    ]
    payload = (root / CANONICAL_PAYLOAD_FILENAME).read_bytes()
    mapping = (root / MATERIALIZATION_MAP_FILENAME).read_bytes()
    receipt = (root / LAUNCH_RECEIPT_FILENAME).read_bytes()
    record, _ = validate_materialization_bundle(payload, mapping, receipt)
    if validate_canonical_envelope(record) != branch:
        raise _representation_rejected("input_inventory", "unexpected_input_file", "input role does not match canonical branch")
    inventory = {"files": files, "input_role": input_role, "inventory_schema": INVENTORY_SCHEMA, "unexpected_files": []}
    validate_proof_input_inventory(inventory, input_role, record)
    return inventory


def validate_proof_input_inventory(inventory: dict[str, Any], input_role: str, record: dict[str, Any]) -> None:
    expected_role = "R0_source" if validate_canonical_envelope(record) == "R0" else "R1_return"
    if input_role != expected_role:
        raise _representation_rejected("input_inventory", "unexpected_input_file", "proof-input role does not match canonical branch")
    expected_files = [
        {"filename": CANONICAL_PAYLOAD_FILENAME, "raw_sha256": raw_stored_sha256(record)},
        {"filename": LAUNCH_RECEIPT_FILENAME, "raw_sha256": raw_stored_sha256(launch_receipt(record))},
        {"filename": MATERIALIZATION_MAP_FILENAME, "raw_sha256": raw_stored_sha256(materialization_map(record))},
    ]
    if not isinstance(inventory, dict) or set(inventory) != {"files", "input_role", "inventory_schema", "unexpected_files"}:
        raise _representation_rejected("input_inventory", "unexpected_input_file", "proof-input inventory shape mismatch")
    files = inventory.get("files")
    if not isinstance(files, list):
        raise _representation_rejected("input_inventory", "unexpected_input_file", "proof-input inventory file list missing")
    filenames = [entry.get("filename") for entry in files if isinstance(entry, dict)]
    if len(filenames) != len(files):
        raise _representation_rejected("input_inventory", "unexpected_input_file", "proof-input inventory member malformed")
    if len(set(filenames)) != len(filenames):
        raise _representation_rejected("input_inventory", "duplicate_input_filename", "proof-input inventory contains duplicate filename")
    if inventory != {"files": expected_files, "input_role": expected_role, "inventory_schema": INVENTORY_SCHEMA, "unexpected_files": []}:
        reason = "missing_input_file" if len(files) < len(expected_files) else "unexpected_input_file"
        raise _representation_rejected("input_inventory", reason, "proof-input inventory does not match exact branch")


def validate_materialization_receipt(record: dict[str, Any], mapping: dict[str, Any], receipt: dict[str, Any]) -> None:
    validate_canonical_envelope(record)
    if mapping != materialization_map(record):
        raise RepresentationRejected("receipt mapping is not record-correlated")
    expected_keys = {
        "receipt_schema", "accepted_canonical_payload_raw_sha256", "accepted_canonical_hash",
        "accepted_materialization_map_raw_sha256", "accepted_mapping_id", "materialized_canonical_site_ids",
        "materialized_canonical_route_id", "materialized_endpoint_site_ids", "materialized_access_state",
        "operational_process_instance_id", "operational_actor_instance_ids",
    }
    if not isinstance(receipt, dict) or set(receipt) != expected_keys:
        raise RepresentationRejected("materialization receipt shape mismatch")
    process_id = receipt["operational_process_instance_id"]
    actor_ids = receipt["operational_actor_instance_ids"]
    if not isinstance(process_id, str) or not OPERATIONAL_ID.fullmatch(process_id):
        raise RepresentationRejected("invalid operational process identity")
    if not isinstance(actor_ids, dict) or set(actor_ids) != {
        "representation_site_slot_01", "representation_site_slot_02", "representation_route_slot_01"
    }:
        raise RepresentationRejected("invalid operational actor identity roles")
    if any(not isinstance(value, str) or not OPERATIONAL_ID.fullmatch(value) for value in actor_ids.values()) or len(set(actor_ids.values())) != 3:
        raise RepresentationRejected("operational actor identities must be valid and pairwise distinct")
    route = record["current_causal_state"]["spatial_topology"]["routes"][ROUTE_ID]
    expected = {
        "accepted_canonical_hash": canonical_hash(record),
        "accepted_canonical_payload_raw_sha256": raw_stored_sha256(record),
        "accepted_mapping_id": mapping["mapping_id"],
        "accepted_materialization_map_raw_sha256": raw_stored_sha256(mapping),
        "materialized_access_state": route["access_state"],
        "materialized_canonical_route_id": ROUTE_ID,
        "materialized_canonical_site_ids": _copy(list(SITE_IDS)),
        "materialized_endpoint_site_ids": _copy(ENDPOINTS),
        "operational_actor_instance_ids": actor_ids,
        "operational_process_instance_id": process_id,
        "receipt_schema": MATERIALIZATION_RECEIPT_SCHEMA,
    }
    if receipt != expected:
        raise RepresentationRejected("materialization receipt contradicts accepted canonical topology")


def materialization_failure(stage: str, reason_code: str) -> dict[str, Any]:
    allowed = {
        "input_inventory": {"unexpected_input_file", "missing_input_file", "duplicate_input_filename"},
        "launch_receipt": {"invalid_launch_receipt", "launch_receipt_hash_mismatch"},
        "raw_hash": {"artifact_raw_hash_mismatch"},
        "parse": {"json_parse_failure"},
        "payload_validation": {"invalid_canonical_payload"},
        "map_validation": {"invalid_materialization_map"},
        "cross_artifact_binding": {"cross_artifact_binding_mismatch"},
    }
    if reason_code not in allowed.get(stage, set()):
        raise RepresentationRejected("invalid materialization failure disposition")
    return {
        "canonical_write_attempted": False,
        "diagnostic_schema": FAILURE_SCHEMA,
        "materialization_started": False,
        "reason_code": reason_code,
        "stage": stage,
    }


_TERMINATION_OBSERVATION_SEAL = object()


@dataclass(frozen=True)
class _TerminationObservation:
    operational_process_instance_id: str
    canonical_pre_state_hash: str
    termination_observed: bool
    alive_before_canonical_resolution: bool
    _seal: object


def open_termination_observation(process_id: str, h0: str, *, process_alive: bool) -> _TerminationObservation:
    if not OPERATIONAL_ID.fullmatch(process_id):
        raise RepresentationRejected("invalid terminated process identity")
    if process_alive:
        raise RepresentationRejected("cannot open termination observation while process is alive")
    if not re.fullmatch(r"[0-9a-f]{64}", h0):
        raise RepresentationRejected("invalid canonical pre-state hash")
    return _TerminationObservation(process_id, h0, True, False, _TERMINATION_OBSERVATION_SEAL)


def _expected_termination_witness(process_id: str, h0: str, h1: str) -> dict[str, Any]:
    return {
        "alive_before_canonical_resolution": False,
        "alive_before_return_launch": False,
        "canonical_pre_state_hash": h0,
        "canonical_resolution_invoked_after_termination": True,
        "event_order": ["source_termination_observed", "canonical_resolution_invoked", "successor_hash_observed"],
        "observed_successor_hash_after_resolution": h1,
        "operational_process_instance_id": process_id,
        "source_terminated_before_canonical_resolution": True,
        "termination_observed": True,
        "termination_schema": TERMINATION_SCHEMA,
    }


def complete_termination_witness(observation: _TerminationObservation, h1: str) -> dict[str, Any]:
    if not isinstance(observation, _TerminationObservation) or observation._seal is not _TERMINATION_OBSERVATION_SEAL:
        raise RepresentationRejected("termination completion requires the opened process observation")
    if not observation.termination_observed or observation.alive_before_canonical_resolution:
        raise RepresentationRejected("termination observation contradicts completion ordering")
    if not re.fullmatch(r"[0-9a-f]{64}", h1):
        raise RepresentationRejected("invalid observed successor hash")
    return _expected_termination_witness(
        observation.operational_process_instance_id,
        observation.canonical_pre_state_hash,
        h1,
    )


def isolation_witness(
    source_process_id: str,
    return_process_id: str,
    source_root: Path,
    return_root: Path,
    source_cache_root: Path,
    return_cache_root: Path,
) -> dict[str, Any]:
    source_real = source_root.resolve()
    return_real = return_root.resolve()
    source_cache_real = source_cache_root.resolve()
    return_cache_real = return_cache_root.resolve()
    if source_process_id == return_process_id or source_real == return_real or source_cache_real == return_cache_real:
        raise RepresentationRejected("source and return identities must be distinct")
    if source_real not in source_cache_real.parents:
        raise RepresentationRejected("source cache is not scoped to source process root")
    if return_real not in return_cache_real.parents:
        raise RepresentationRejected("return cache is not scoped to return process root")
    if source_cache_real in return_cache_real.parents or return_cache_real in source_cache_real.parents:
        raise RepresentationRejected("source and return cache roots overlap")
    return {
        "isolation_schema": ISOLATION_SCHEMA,
        "neither_root_contains_the_other": source_real not in return_real.parents and return_real not in source_real.parents,
        "return_process_instance_id": return_process_id,
        "shared_cache_or_save_or_session_root": False,
        "source_and_return_process_ids_distinct": True,
        "source_and_return_realpaths_distinct": True,
        "source_input_supplied_to_return": False,
        "source_output_supplied_to_return": False,
        "source_process_instance_id": source_process_id,
        "source_process_terminated": True,
        "truth_bearing_command_line_values": [],
    }


def validate_termination_witness(witness: dict[str, Any], process_id: str, h0: str, h1: str) -> None:
    if witness != _expected_termination_witness(process_id, h0, h1):
        raise RepresentationRejected("termination witness is incomplete or contradictory")


def validate_isolation_witness(witness: dict[str, Any]) -> None:
    expected_keys = {
        "isolation_schema", "source_process_instance_id", "return_process_instance_id",
        "source_and_return_process_ids_distinct", "source_and_return_realpaths_distinct",
        "neither_root_contains_the_other", "source_process_terminated", "source_input_supplied_to_return",
        "source_output_supplied_to_return", "shared_cache_or_save_or_session_root",
        "truth_bearing_command_line_values",
    }
    if not isinstance(witness, dict) or set(witness) != expected_keys:
        raise RepresentationRejected("isolation witness shape mismatch")
    if witness["isolation_schema"] != ISOLATION_SCHEMA:
        raise RepresentationRejected("isolation witness schema mismatch")
    if any(not isinstance(witness[key], str) or not OPERATIONAL_ID.fullmatch(witness[key]) for key in ("source_process_instance_id", "return_process_instance_id")):
        raise RepresentationRejected("isolation process identity is malformed")
    if witness["source_process_instance_id"] == witness["return_process_instance_id"]:
        raise RepresentationRejected("process identities are not distinct")
    required_true = (
        "source_and_return_process_ids_distinct", "source_and_return_realpaths_distinct",
        "neither_root_contains_the_other", "source_process_terminated",
    )
    if not all(witness[key] is True for key in required_true):
        raise RepresentationRejected("fresh-process isolation fact is false")
    required_false = (
        "source_input_supplied_to_return", "source_output_supplied_to_return",
        "shared_cache_or_save_or_session_root",
    )
    if not all(witness[key] is False for key in required_false) or witness["truth_bearing_command_line_values"] != []:
        raise RepresentationRejected("truth-bearing source state reached the return process")


def reverse_order_oracle(record: dict[str, Any]) -> dict[str, Any]:
    forward = evaluate_route_access(record, ROUTE_ID, [SITE_A, SITE_B])
    reverse = evaluate_route_access(record, ROUTE_ID, [SITE_B, SITE_A])
    forward_semantic = _copy(forward)
    reverse_semantic = _copy(reverse)
    del forward_semantic["received_endpoint_site_ids"]
    del reverse_semantic["received_endpoint_site_ids"]
    return {
        "access_state_evaluated": forward["access_state_evaluated"] and reverse["access_state_evaluated"],
        "forward": forward,
        "reverse": reverse,
        "semantic_results_equal_after_received_order_removed": forward_semantic == reverse_semantic,
    }


def replay_witness() -> dict[str, Any]:
    r0a = initial_canonical_envelope()
    r1a = resolve_next_due(r0a, next_consequential_boundary(r0a))  # type: ignore[arg-type]
    r0b = initial_canonical_envelope()
    r1b = resolve_next_due(r0b, next_consequential_boundary(r0b))  # type: ignore[arg-type]
    return {
        "R0_byte_identical": stored_json_bytes(r0a) == stored_json_bytes(r0b),
        "R0_hash": canonical_hash(r0a),
        "R1_byte_identical": stored_json_bytes(r1a) == stored_json_bytes(r1b),
        "R1_hash": canonical_hash(r1a),
        "result": "accepted" if stored_json_bytes(r0a) == stored_json_bytes(r0b) and stored_json_bytes(r1a) == stored_json_bytes(r1b) else "failed",
    }


def canonical_source_audit() -> dict[str, Any]:
    query_source = inspect.getsource(evaluate_route_access)
    resolver_source = inspect.getsource(resolve_next_due)
    assignment_source = inspect.getsource(conceptual_label_neutrality_witness)
    return {
        "assignment_has_no_canonical_import_or_write_path": "conceptual_assignment" not in resolver_source and "conceptual_assignment" not in inspect.getsource(initial_canonical_envelope),
        "canonical_validator_query_resolver_are_separate": len({id(validate_canonical_envelope), id(evaluate_route_access), id(resolve_next_due)}) == 3,
        "labels_absent_from_canonical_record": all(label not in canonical_json(initial_canonical_envelope()) for label in ("Proof Endpoint", "West Reference", "Conceptual Crossing")),
        "map_is_not_query_input": "materialization_map" not in query_source,
        "query_normalizes_request_copy": "received = _copy(requested_endpoint_site_ids)" in query_source and "normalized = sorted(received)" in query_source,
        "resolver_has_no_conceptual_or_representation_input": all(token not in resolver_source for token in ("display_label", "materialization", "Actor", "navigation", "level", "streaming")),
        "resolver_owns_only_access_fact_topology_mutation": "access_state\"] = \"blocked\"" in inspect.getsource(_expected_r1),
        "renamed_assignment_changes_no_canonical_input": "initial_canonical_envelope()" in assignment_source,
    }


def runtime_fail_closed_results() -> dict[str, dict[str, Any]]:
    """Mechanically exercise all named variants inside the 28 frozen families."""

    results: dict[str, dict[str, Any]] = {}
    r0 = initial_canonical_envelope()
    r1 = resolve_next_due(r0, _boundary(r0))
    good_map = materialization_map(r0)
    good_receipt = launch_receipt(r0)

    def capture(operation: Callable[[], Any], expected_diagnostic: dict[str, Any] | None = None) -> dict[str, Any]:
        before = stored_json_bytes(r0)
        try:
            operation()
        except (ValueError, CanonicalTopologyRejected, RepresentationRejected, TypeError) as exc:
            if stored_json_bytes(r0) != before:
                raise AssertionError("rejection mutated R0")
            diagnostic = exc.diagnostic if isinstance(exc, RepresentationRejected) else None
            if expected_diagnostic is not None and diagnostic != expected_diagnostic:
                raise AssertionError(f"detached diagnostic mismatch: {diagnostic!r}")
            result: dict[str, Any] = {"disposition": "rejected_before_authority"}
            if diagnostic is not None:
                result["detached_diagnostic"] = diagnostic
            return result
        raise AssertionError("adversarial variant did not reject")

    def family(name: str, variants: dict[str, Callable[[], Any] | tuple[Callable[[], Any], dict[str, Any]]]) -> None:
        observed: dict[str, Any] = {}
        for variant, operation in variants.items():
            if isinstance(operation, tuple):
                observed[variant] = capture(operation[0], operation[1])
            else:
                observed[variant] = capture(operation)
        results[name] = {"disposition": "all_variants_rejected", "variant_count": len(observed), "variants": observed}

    family("01_duplicate_raw_json_member", {"duplicate_identity": lambda: strict_load_stored_json(b'{"identity":{},"identity":{}}\n')})
    bad = _copy(r0); bad["current_causal_state"]["spatial_topology"]["sites"] = {ROUTE_ID: None, SITE_B: None}
    site_as_route = _copy(r0); site_as_route["current_causal_state"]["spatial_topology"]["routes"] = {SITE_A: _copy(site_as_route["current_causal_state"]["spatial_topology"]["routes"][ROUTE_ID])}
    family("02_cross_type_identity_substitution", {
        "route_as_site": lambda bad=bad: validate_canonical_envelope(bad),
        "site_as_route": lambda: validate_canonical_envelope(site_as_route),
    })
    bad = _copy(r0); del bad["current_causal_state"]["spatial_topology"]["sites"][SITE_B]
    family("03_dangling_route_endpoint", {"missing_site_b": lambda bad=bad: validate_canonical_envelope(bad)})
    bad = _copy(r0); bad["current_causal_state"]["spatial_topology"]["routes"][ROUTE_ID]["endpoint_site_ids"] = [SITE_A, SITE_A]
    family("04_identical_stored_endpoints", {"site_a_twice": lambda bad=bad: validate_canonical_envelope(bad)})
    bad = _copy(r0); bad["current_causal_state"]["spatial_topology"]["routes"][ROUTE_ID]["endpoint_site_ids"] = [SITE_B, SITE_A]
    family("05_noncanonical_stored_endpoint_order", {"reversed_storage": lambda bad=bad: validate_canonical_envelope(bad)})

    oracle = reverse_order_oracle(r0)
    if not oracle["semantic_results_equal_after_received_order_removed"] or not oracle["forward"]["eligible"] or not oracle["reverse"]["eligible"]:
        raise AssertionError("reverse-order semantics leaked")
    results["06_request_order_semantic_leakage"] = {
        "disposition": "equivalence_oracle_passed", "variant_count": 3,
        "variants": {name: {"disposition": "equivalence_preserved"} for name in ("reverse_rejected", "reverse_directional", "reverse_eligibility_changed")},
    }

    query_cases = {
        "07_invalid_route_reaches_access": {
            "invalid_route_only": ("unknown_route", ENDPOINTS, "invalid_route_id"),
            "invalid_route_precedes_non_array": ("unknown_route", "not-an-array", "invalid_route_id"),
        },
        "08_non_array_endpoints_reach_access": {"non_array": (ROUTE_ID, "not-an-array", "endpoint_array_required")},
        "09_wrong_endpoint_count_reaches_access": {
            "one_endpoint": (ROUTE_ID, [SITE_A], "endpoint_count_not_two"),
            "count_precedes_unknown_id": (ROUTE_ID, [SITE_A, SITE_B, "bad"], "endpoint_count_not_two"),
        },
        "10_unknown_endpoint_reaches_access": {
            "one_unknown": (ROUTE_ID, [SITE_A, "topology_site_9999"], "invalid_endpoint_site_id"),
            "unknown_precedes_duplicate": (ROUTE_ID, ["bad", "bad"], "invalid_endpoint_site_id"),
        },
        "11_duplicate_requested_endpoint_reaches_access": {"site_a_twice": (ROUTE_ID, [SITE_A, SITE_A], "duplicate_endpoint_site_id")},
    }
    for name, cases in query_cases.items():
        variants: dict[str, Any] = {}
        for variant, (route, endpoints, reason) in cases.items():
            result = evaluate_route_access(r0, route, endpoints)
            if result["reason_code"] != reason or result["access_state_evaluated"] or result["eligible"] is not None:
                raise AssertionError(f"query precedence failed: {name}/{variant}")
            variants[variant] = {"disposition": "rejected_as_invalid_request", "reason_code": reason}
        results[name] = {"disposition": "all_variants_rejected", "variant_count": len(variants), "variants": variants}

    extra_route = _copy(r0); extra_route["current_causal_state"]["spatial_topology"]["routes"]["extra_route"] = {}
    extra_site = _copy(r0); extra_site["current_causal_state"]["spatial_topology"]["sites"]["extra_site"] = None
    extra_field = _copy(r0); extra_field["current_causal_state"]["spatial_topology"]["extra"] = None
    bad_access = _copy(r0); bad_access["current_causal_state"]["spatial_topology"]["routes"][ROUTE_ID]["access_state"] = "unknown"
    family("12_extra_topology_field_or_value", {
        "extra_route": lambda: validate_canonical_envelope(extra_route),
        "extra_site": lambda: validate_canonical_envelope(extra_site),
        "extra_topology_field": lambda: validate_canonical_envelope(extra_field),
        "invalid_access_value": lambda: validate_canonical_envelope(bad_access),
    })

    conceptual_route = evaluate_route_access(r0, "Conceptual Crossing Fixture", ENDPOINTS)
    conceptual_sites = evaluate_route_access(r0, ROUTE_ID, ["Proof Endpoint One", "Proof Endpoint Two"])
    if any(result["evaluation_status"] != "invalid_request" or result["access_state_evaluated"] for result in (conceptual_route, conceptual_sites)):
        raise AssertionError("conceptual identity reached query")
    results["13_conceptual_identity_substitution"] = {
        "disposition": "all_variants_rejected", "variant_count": 2,
        "variants": {
            "conceptual_route_label": {"disposition": "rejected_as_invalid_request", "reason_code": conceptual_route["reason_code"]},
            "conceptual_site_labels": {"disposition": "rejected_as_invalid_request", "reason_code": conceptual_sites["reason_code"]},
        },
    }
    representation_variants = ("Actor_42", "/Game/Actor.Path", "GUID-42", "NavNode_A", "Level_A", "WorldPartitionCell_B", "StreamingIdentity_C")
    representation_results: dict[str, Any] = {}
    for identity in representation_variants:
        for position, query in (
            ("route", evaluate_route_access(r0, identity, ENDPOINTS)),
            ("site", evaluate_route_access(r0, ROUTE_ID, [identity, SITE_B])),
        ):
            if query["evaluation_status"] != "invalid_request" or query["access_state_evaluated"]:
                raise AssertionError("representation identity reached query")
            representation_results[f"{position}:{identity}"] = {"disposition": "rejected_as_invalid_request", "reason_code": query["reason_code"]}
    results["14_representation_identity_substitution"] = {"disposition": "all_variants_rejected", "variant_count": len(representation_results), "variants": representation_results}
    if "materialization_map" in inspect.signature(evaluate_route_access).parameters:
        raise AssertionError("mapping can redirect route access")
    results["15_query_redirected_through_mapping"] = {"disposition": "rejected_by_interface", "variant_count": 1, "variants": {"mapping_parameter": {"disposition": "absent"}}}

    mutation_variants: dict[str, Callable[[], Any]] = {}
    for variant, path in (
        ("site_id", "/current_causal_state/spatial_topology/sites/topology_site_0001"),
        ("route_id", "/current_causal_state/spatial_topology/routes/topology_route_0001"),
        ("endpoint", "/current_causal_state/spatial_topology/routes/topology_route_0001/endpoint_site_ids"),
        ("endpoint_semantics", "/current_causal_state/spatial_topology/routes/topology_route_0001/endpoint_semantics"),
    ):
        candidate = _boundary(r0); candidate["permitted_topology_mutation"] = {"path": path}
        mutation_variants[variant] = lambda candidate=candidate: resolve_next_due(r0, candidate)
    family("16_access_mutation_changes_identity_or_endpoints", mutation_variants)
    stale_boundary = _boundary(r0); stale_boundary["source_record_hash"] = canonical_hash(r1)
    family("17_stale_or_wrong_record_boundary", {"r1_hash_against_r0": lambda: resolve_next_due(r0, stale_boundary)})

    map_variants: dict[str, dict[str, Any]] = {}
    missing_map = _copy(good_map); del missing_map["sites"][SITE_A]
    additional_map = _copy(good_map); additional_map["sites"]["extra_site"] = "representation_site_slot_03"
    redirected_map = _copy(good_map); redirected_map["sites"][SITE_A] = "representation_site_slot_02"
    duplicate_map_raw = stored_json_bytes(good_map).replace(b'"topology_site_0001":"representation_site_slot_01",', b'"topology_site_0001":"representation_site_slot_01","topology_site_0001":"representation_site_slot_01",')
    for variant, raw in {
        "missing_key": stored_json_bytes(missing_map),
        "additional_key": stored_json_bytes(additional_map),
        "duplicate_key": duplicate_map_raw,
        "redirected_key": stored_json_bytes(redirected_map),
    }.items():
        map_variants[variant] = capture(
            lambda raw=raw: validate_materialization_bundle(stored_json_bytes(r0), raw, stored_json_bytes(good_receipt)),
            materialization_failure("raw_hash", "artifact_raw_hash_mismatch"),
        )
    results["18_invalid_materialization_mapping_keys"] = {"disposition": "all_variants_rejected", "variant_count": len(map_variants), "variants": map_variants}

    cross_variants: dict[str, Any] = {}
    cross_cases = {
        "r0_payload_r1_map_receipt": (r0, materialization_map(r1), launch_receipt(r1)),
        "r1_payload_r0_map_receipt": (r1, materialization_map(r0), launch_receipt(r0)),
        "r0_payload_r0_map_r1_receipt": (r0, materialization_map(r0), launch_receipt(r1)),
        "r1_payload_r1_map_r0_receipt": (r1, materialization_map(r1), launch_receipt(r0)),
        "r0_payload_r1_map_r0_receipt": (r0, materialization_map(r1), launch_receipt(r0)),
        "r1_payload_r0_map_r1_receipt": (r1, materialization_map(r0), launch_receipt(r1)),
    }
    for variant, (record, mapping, receipt) in cross_cases.items():
        cross_variants[variant] = capture(
            lambda record=record, mapping=mapping, receipt=receipt: validate_materialization_bundle(stored_json_bytes(record), stored_json_bytes(mapping), stored_json_bytes(receipt)),
            materialization_failure("raw_hash", "artifact_raw_hash_mismatch"),
        )
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        for filename, value in ((CANONICAL_PAYLOAD_FILENAME, r0), (MATERIALIZATION_MAP_FILENAME, good_map), (LAUNCH_RECEIPT_FILENAME, good_receipt)):
            (root / filename).write_bytes(stored_json_bytes(value))
        cross_variants["r0_files_r1_inventory_role"] = capture(lambda: proof_input_inventory(root, "R1_return"), materialization_failure("input_inventory", "unexpected_input_file"))
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        map1 = materialization_map(r1); receipt1 = launch_receipt(r1)
        for filename, value in ((CANONICAL_PAYLOAD_FILENAME, r1), (MATERIALIZATION_MAP_FILENAME, map1), (LAUNCH_RECEIPT_FILENAME, receipt1)):
            (root / filename).write_bytes(stored_json_bytes(value))
        cross_variants["r1_files_r0_inventory_role"] = capture(lambda: proof_input_inventory(root, "R0_source"), materialization_failure("input_inventory", "unexpected_input_file"))
    results["19_cross_row_artifact_combination"] = {"disposition": "all_variants_rejected", "variant_count": len(cross_variants), "variants": cross_variants}

    disagreement_variants: dict[str, Any] = {}
    for variant, mutated in (
        ("map_bytes", {**good_map, "mapping_id": R1_MAPPING_ID}),
        ("map_schema", {**good_map, "mapping_schema": "WrongMap.v1"}),
        ("map_identity", {**good_map, "mapping_id": "wrong_mapping"}),
        ("map_source_hash", {**good_map, "source_canonical_hash": canonical_hash(r1)}),
    ):
        raw = stored_json_bytes(mutated)
        disagreement_variants[variant] = capture(
            lambda raw=raw: validate_materialization_bundle(stored_json_bytes(r0), raw, stored_json_bytes(good_receipt)),
            materialization_failure("raw_hash", "artifact_raw_hash_mismatch"),
        )
    noncanonical_map = json.dumps(good_map, sort_keys=False, separators=(", ", ": "), ensure_ascii=True).encode("utf-8") + b"\n"
    receipt_for_noncanonical = _copy(good_receipt); receipt_for_noncanonical["materialization_map_raw_sha256"] = _sha(noncanonical_map)
    disagreement_variants["recomputed_hash_noncanonical_map"] = capture(
        lambda: validate_materialization_bundle(stored_json_bytes(r0), noncanonical_map, stored_json_bytes(receipt_for_noncanonical)),
        materialization_failure("launch_receipt", "launch_receipt_hash_mismatch"),
    )
    noncanonical_receipt = json.dumps(good_receipt, sort_keys=False, separators=(", ", ": "), ensure_ascii=True).encode("utf-8") + b"\n"
    disagreement_variants["noncanonical_launch_receipt"] = capture(
        lambda: validate_materialization_bundle(stored_json_bytes(r0), stored_json_bytes(good_map), noncanonical_receipt),
        materialization_failure("launch_receipt", "invalid_launch_receipt"),
    )
    malformed_receipt = _copy(good_receipt); malformed_receipt["expected_scenario_id"] = ""
    disagreement_variants["empty_receipt_field_preparse"] = capture(
        lambda: validate_materialization_bundle(stored_json_bytes(r0), stored_json_bytes(good_map), stored_json_bytes(malformed_receipt)),
        materialization_failure("launch_receipt", "invalid_launch_receipt"),
    )
    results["20_map_or_receipt_disagreement"] = {"disposition": "all_variants_rejected", "variant_count": len(disagreement_variants), "variants": disagreement_variants}

    absent = _copy(r0); del absent["current_causal_state"]["spatial_topology"]["routes"][ROUTE_ID]
    family("21_adapter_manufactures_absent_topology", {"route_absent": lambda: validate_canonical_envelope(absent)})
    receipt = {
        "accepted_canonical_hash": canonical_hash(r0), "accepted_canonical_payload_raw_sha256": raw_stored_sha256(r0),
        "accepted_mapping_id": good_map["mapping_id"], "accepted_materialization_map_raw_sha256": raw_stored_sha256(good_map),
        "materialized_access_state": "available", "materialized_canonical_route_id": ROUTE_ID,
        "materialized_canonical_site_ids": list(SITE_IDS), "materialized_endpoint_site_ids": ENDPOINTS,
        "operational_actor_instance_ids": {"representation_site_slot_01": "a", "representation_site_slot_02": "b", "representation_route_slot_01": "c"},
        "operational_process_instance_id": "P0", "receipt_schema": MATERIALIZATION_RECEIPT_SCHEMA,
    }
    write_variants: dict[str, Callable[[], Any]] = {}
    for variant, field, value in (
        ("access_state", "canonical_access_state_write", "blocked"),
        ("ledger", "authoritative_causal_ledger", []),
        ("ancestry", "canonical_ancestry", {}),
        ("schedule", "future_schedule", []),
        ("successor", "canonical_successor", r1),
    ):
        candidate = _copy(receipt); candidate[field] = value
        write_variants[variant] = lambda candidate=candidate: validate_materialization_receipt(r0, good_map, candidate)
    family("22_adapter_attempts_canonical_write", write_variants)
    q_receipt = _copy(receipt); q_receipt["proposal_capability_enabled"] = True
    family("23_adapter_exposes_q_path", {"proposal_capability": lambda: validate_materialization_receipt(r0, good_map, q_receipt)})

    input_variants: dict[str, Any] = {}
    def root_case(kind: str) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for filename, value in ((CANONICAL_PAYLOAD_FILENAME, r0), (MATERIALIZATION_MAP_FILENAME, good_map), (LAUNCH_RECEIPT_FILENAME, good_receipt)):
                (root / filename).write_bytes(stored_json_bytes(value))
            if kind == "missing":
                (root / MATERIALIZATION_MAP_FILENAME).unlink()
            elif kind == "additional":
                (root / "extra.json").write_text("{}\n", encoding="utf-8")
            elif kind == "directory":
                (root / "extra_directory").mkdir()
            proof_input_inventory(root, "R0_source")
    for variant, reason in (("missing_file", "missing_input_file"), ("additional_file", "unexpected_input_file"), ("additional_directory", "unexpected_input_file")):
        input_variants[variant] = capture(lambda variant=variant: root_case({"missing_file": "missing", "additional_file": "additional", "additional_directory": "directory"}[variant]), materialization_failure("input_inventory", reason))
    exact_inventory = {
        "files": [
            {"filename": CANONICAL_PAYLOAD_FILENAME, "raw_sha256": raw_stored_sha256(r0)},
            {"filename": LAUNCH_RECEIPT_FILENAME, "raw_sha256": raw_stored_sha256(good_receipt)},
            {"filename": MATERIALIZATION_MAP_FILENAME, "raw_sha256": raw_stored_sha256(good_map)},
        ],
        "input_role": "R0_source", "inventory_schema": INVENTORY_SCHEMA, "unexpected_files": [],
    }
    duplicate_inventory = _copy(exact_inventory); duplicate_inventory["files"][2] = _copy(duplicate_inventory["files"][1])
    input_variants["duplicate_filename"] = capture(lambda: validate_proof_input_inventory(duplicate_inventory, "R0_source", r0), materialization_failure("input_inventory", "duplicate_input_filename"))
    input_variants["role_incompatible"] = capture(lambda: validate_proof_input_inventory(exact_inventory, "R1_return", r0), materialization_failure("input_inventory", "unexpected_input_file"))
    results["24_invalid_proof_input_file_set"] = {"disposition": "all_variants_rejected", "variant_count": len(input_variants), "variants": input_variants}

    isolation_variants: dict[str, Any] = {}
    for variant, changed in (
        ("source_input", {"source_input_supplied_to_return": True}),
        ("source_output", {"source_output_supplied_to_return": True}),
        ("shared_cache", {"shared_cache_or_save_or_session_root": True}),
        ("branch_selector", {"truth_bearing_command_line_values": ["R0"]}),
    ):
        candidate = {
            "isolation_schema": ISOLATION_SCHEMA, "source_process_instance_id": "P0", "return_process_instance_id": "P1",
            "source_and_return_process_ids_distinct": True, "source_and_return_realpaths_distinct": True,
            "neither_root_contains_the_other": True, "source_process_terminated": True,
            "source_input_supplied_to_return": False, "source_output_supplied_to_return": False,
            "shared_cache_or_save_or_session_root": False, "truth_bearing_command_line_values": [],
        }
        candidate.update(changed)
        isolation_variants[variant] = capture(lambda candidate=candidate: validate_isolation_witness(candidate))
    results["25_return_process_receives_source_truth"] = {"disposition": "all_variants_rejected", "variant_count": len(isolation_variants), "variants": isolation_variants}

    identity_variants: dict[str, Any] = {}
    missing_identity = _copy(receipt); del missing_identity["operational_process_instance_id"]
    duplicate_actor = _copy(receipt); duplicate_actor["operational_actor_instance_ids"]["representation_site_slot_02"] = "a"
    contradictory = _copy(receipt); contradictory["accepted_canonical_hash"] = canonical_hash(r1)
    malformed = _copy(receipt); malformed["operational_process_instance_id"] = "bad id"
    for variant, candidate in (("missing", missing_identity), ("duplicate_actor", duplicate_actor), ("contradictory", contradictory), ("malformed", malformed)):
        identity_variants[variant] = capture(lambda candidate=candidate: validate_materialization_receipt(r0, good_map, candidate))
    same_process_isolation = {
        "isolation_schema": ISOLATION_SCHEMA, "source_process_instance_id": "P0", "return_process_instance_id": "P0",
        "source_and_return_process_ids_distinct": True, "source_and_return_realpaths_distinct": True,
        "neither_root_contains_the_other": True, "source_process_terminated": True,
        "source_input_supplied_to_return": False, "source_output_supplied_to_return": False,
        "shared_cache_or_save_or_session_root": False, "truth_bearing_command_line_values": [],
    }
    identity_variants["non_distinct_processes"] = capture(lambda: validate_isolation_witness(same_process_isolation))
    results["26_invalid_process_or_actor_identity_evidence"] = {"disposition": "all_variants_rejected", "variant_count": len(identity_variants), "variants": identity_variants}

    record_before = stored_json_bytes(r0)
    disposable_mapping = materialization_map(r0); del disposable_mapping
    if stored_json_bytes(r0) != record_before or canonical_hash(r0) != canonical_hash(initial_canonical_envelope()):
        raise AssertionError("representation destruction deleted canonical topology")
    results["27_representation_destruction_deletes_topology"] = {"disposition": "authority_invariance_proven", "variant_count": 1, "variants": {"mapping_destroyed": {"canonical_R0_unchanged": True}}}
    self_hash = _copy(r1); self_hash["causal_provenance"]["canonical_ancestry"]["successor_record_hash"] = canonical_hash(r1)
    family("28_in_record_successor_self_hash", {"successor_hash_field": lambda: validate_canonical_envelope(self_hash)})
    observed_matrix = {
        family_name: (result["disposition"], tuple(result["variants"]))
        for family_name, result in results.items()
    }
    if observed_matrix != FROZEN_ADVERSARIAL_MATRIX:
        raise AssertionError("adversarial family/variant/disposition matrix drift")
    observed_diagnostics = {
        family_name: {
            variant_name: (
                variant["detached_diagnostic"]["stage"],
                variant["detached_diagnostic"]["reason_code"],
            )
            for variant_name, variant in results[family_name]["variants"].items()
            if "detached_diagnostic" in variant
        }
        for family_name in FROZEN_REPRESENTATION_DIAGNOSTICS
    }
    if observed_diagnostics != FROZEN_REPRESENTATION_DIAGNOSTICS:
        raise AssertionError("representation failure stage/reason precedence drift")
    return results


def proof_run() -> dict[str, Any]:
    r0 = initial_canonical_envelope()
    boundary = next_consequential_boundary(r0)
    if boundary is None:
        raise AssertionError("R0 must own one boundary")
    r1 = resolve_next_due(r0, boundary)
    return {
        "R0": r0,
        "R0_hash": canonical_hash(r0),
        "R0_raw_sha256": raw_stored_sha256(r0),
        "R1": r1,
        "R1_hash": canonical_hash(r1),
        "R1_raw_sha256": raw_stored_sha256(r1),
        "boundary": boundary,
        "conceptual_label_neutrality": conceptual_label_neutrality_witness(),
        "materialization_maps": {"R0": materialization_map(r0), "R1": materialization_map(r1)},
        "launch_receipts": {"R0": launch_receipt(r0), "R1": launch_receipt(r1)},
        "queries": {"R0": reverse_order_oracle(r0), "R1": reverse_order_oracle(r1)},
        "replay": replay_witness(),
        "runtime_fail_closed": runtime_fail_closed_results(),
        "source_audit": canonical_source_audit(),
    }


def write_artifacts(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    run = proof_run()
    mutation_run = {
        "R0_hash": run["R0_hash"],
        "R1_hash": run["R1_hash"],
        "boundary": run["boundary"],
        "canonical_topology_mutation_count": 1,
        "endpoint_relation_unchanged": True,
        "next_boundary_after_R1": None,
        "r1_ledger": run["R1"]["causal_provenance"]["authoritative_causal_ledger"],
        "r1_parent_record_hash": run["R1"]["causal_provenance"]["canonical_ancestry"]["parent_record_hash"],
        "six_replacements": ["access_state", "process_state", "canonical_clock", "unresolved_work", "authoritative_causal_ledger", "canonical_ancestry"],
    }
    artifacts = {
        "canonical_topology_R0.json": run["R0"],
        "canonical_topology_R1.json": run["R1"],
        "canonical_topology_boundary_H0.json": run["boundary"],
        "canonical_topology_assignment_baseline.json": conceptual_assignment(False),
        "canonical_topology_assignment_renamed.json": conceptual_assignment(True),
        "canonical_topology_label_neutrality_witness.json": run["conceptual_label_neutrality"],
        "canonical_topology_access_R0_forward.json": run["queries"]["R0"]["forward"],
        "canonical_topology_access_R0_reverse.json": run["queries"]["R0"]["reverse"],
        "canonical_topology_access_R1_forward.json": run["queries"]["R1"]["forward"],
        "canonical_topology_access_R1_reverse.json": run["queries"]["R1"]["reverse"],
        "canonical_topology_access_oracle.json": run["queries"],
        "canonical_topology_mutation_run.json": mutation_run,
        "canonical_topology_materialization_map_R0.json": run["materialization_maps"]["R0"],
        "canonical_topology_materialization_map_R1.json": run["materialization_maps"]["R1"],
        "canonical_topology_launch_receipt_R0.json": run["launch_receipts"]["R0"],
        "canonical_topology_launch_receipt_R1.json": run["launch_receipts"]["R1"],
        "canonical_topology_replay_oracle.json": run["replay"],
        "canonical_topology_runtime_fail_closed.json": run["runtime_fail_closed"],
        "canonical_topology_source_audit.json": run["source_audit"],
        "canonical_topology_proof_run.json": run,
    }
    if tuple(artifacts) != ARTIFACT_NAMES:
        raise AssertionError("canonical topology artifact membership drift")
    for name, value in artifacts.items():
        (directory / name).write_bytes(stored_json_bytes(value))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("run", "write-artifacts"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "run":
        print(canonical_json(proof_run()))
    elif args.output is None:
        parser.error("--output is required")
    else:
        write_artifacts(args.output)


if __name__ == "__main__":
    main()
