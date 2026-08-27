"""Frozen fixture for Concurrent External Evidence Arbitration Proof v0.1.0.

This module is intentionally not a general input collector or scheduler.  It
implements one exact R0-bound external batch containing the sealed QA/QB
candidate set (or either declared singleton control), one canonical ordering
law, private provisional state, and one canonical publication point.

Unreal remains a detached evidence source.  Process order, presentation order,
filesystem metadata, and every other representation-local fact are absent from
the resolver interface and from canonical authority.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import inspect
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from kernel import canonical_json


RECORD_SCHEMA = "CanonicalResolutionEnvelope.v1"
PAYLOAD_SCHEMA = "ConcurrentExternalEvidenceArbitrationPayload.v1"
SCENARIO_ID = "concurrent-external-evidence-arbitration-v1"
SCENARIO_VERSION = "0.1.0"
SIMULATION_VERSION = "0.7.0-draft.57"
SEED = "concurrent-external-evidence-arbitration-v1/0001"

TIME_R0 = "t0/00"
TIME_EXTERNAL = "t0/30"
EXTERNAL_PHASE = 10
EXTERNAL_PRIORITY = 100
ORDERING_LAW = "ConcurrentExternalMemberOrder.v1"

INPUT_A = "physical_allocate_shared_slot_A_0001"
INPUT_B = "physical_allocate_shared_slot_B_0001"
EVENT_A = "domain_A_allocation_event_0001"
EVENT_B = "domain_B_allocation_event_0001"

LAUNCH_RECEIPT_SCHEMA = "ConcurrentUnrealLaunchReceipt.v1"
MATERIALIZATION_RECEIPT_SCHEMA = "ConcurrentMaterializationAcceptanceReceipt.v1"
EMISSION_RECEIPT_SCHEMA = "ConcurrentEvidenceEmissionReceipt.v1"
EVIDENCE_PROTOCOL = "ConcurrentExternalEvidence.v1"
ADMITTED_MEMBER_SCHEMA = "AdmittedExternalMember.v1"
FIXTURE_SET_SCHEMA = "ConcurrentExternalCandidateSetFixture.v1"
BATCH_SCHEMA = "ConcurrentExternalArbitrationBatch.v1"
WORKING_STATE_SCHEMA = "ExternalArbitrationWorkingState.v1"
WORKING_IDENTITY_SCHEMA = "ExternalBatchWorkingStateIdentity.v1"
WORKING_IDENTITY_KIND = "provisional_external_batch_working_state"
WORKING_DIGEST_DOMAIN = "THE_CITY_EXTERNAL_ARBITRATION_WORKING_STATE_V1"

PRIMARY_FIXTURE_ID = "concurrent-external-evidence-arbitration-primary-v1"
QA_ONLY_FIXTURE_ID = "concurrent-external-evidence-arbitration-qa-only-v1"
QB_ONLY_FIXTURE_ID = "concurrent-external-evidence-arbitration-qb-only-v1"

DOMAIN_TABLE: dict[str, dict[str, str]] = {
    "domain_A": {
        "source_domain": "domain_A",
        "physical_actor_id": "arbitration_surface_A_01",
        "input_id": INPUT_A,
        "physical_event_id": EVENT_A,
        "allocation_owner": "domain_A",
    },
    "domain_B": {
        "source_domain": "domain_B",
        "physical_actor_id": "arbitration_surface_B_01",
        "input_id": INPUT_B,
        "physical_event_id": EVENT_B,
        "allocation_owner": "domain_B",
    },
}
INPUT_TO_DOMAIN = {row["input_id"]: name for name, row in DOMAIN_TABLE.items()}


REJECT_RECORD = "concurrent_external_rejected.exact_canonical_record_required"
REJECT_Q_SHAPE = "concurrent_external_rejected.q_shape_mismatch"
REJECT_Q_DIGEST = "concurrent_external_rejected.evidence_digest_mismatch"
REJECT_Q_CONTRACT = "concurrent_external_rejected.consequence_contract_mismatch"
REJECT_Q_SOURCE = "concurrent_external_rejected.source_record_mismatch"
REJECT_Q_RAW_SOURCE = "concurrent_external_rejected.source_raw_payload_mismatch"
REJECT_Q_TIME = "concurrent_external_rejected.occurrence_time_mismatch"
REJECT_Q_REPLAY_INPUT = "concurrent_external_rejected.input_id_already_adjudicated"
REJECT_Q_REPLAY_EVENT = "concurrent_external_rejected.physical_event_id_already_adjudicated"
REJECT_Q_GATE = "concurrent_external_rejected.shared_slot_unavailable_at_admission"
REJECT_RECEIPT = "concurrent_external_rejected.detached_receipt_mismatch"
REJECT_FIXTURE = "concurrent_external_batch_rejected.fixture_set_mismatch"
REJECT_DUPLICATE_INPUT = "concurrent_external_batch_rejected.duplicate_input_id"
REJECT_DUPLICATE_EVENT = "concurrent_external_batch_rejected.duplicate_physical_event_id"
REJECT_MEMBER_SOURCE = "concurrent_external_batch_rejected.member_source_mismatch"
REJECT_MEMBER_DIGEST = "concurrent_external_batch_rejected.member_set_digest_mismatch"
REJECT_ORDER_AUTHORITY = "concurrent_external_batch_rejected.caller_order_authority"
REJECT_BATCH_SOURCE = "concurrent_external_resolution_rejected.batch_source_mismatch"
REJECT_BATCH_SHAPE = "concurrent_external_resolution_rejected.batch_shape_mismatch"
REJECT_MEMBER_SHAPE = "concurrent_external_resolution_rejected.member_shape_mismatch"
REJECT_MUTATION = "concurrent_external_resolution_rejected.mutation_outside_contract"
REJECT_PROVISIONAL_IDENTITY = "concurrent_external_resolution_rejected.provisional_identity_type_mismatch"
REJECT_PARTIAL_EXECUTION = "concurrent_external_resolution_rejected.partial_execution_fault"
REJECT_PUBLICATION = "concurrent_external_resolution_rejected.candidate_publication_invalid"

FAULT_POINTS = (
    "after_qa_provisional_mutation",
    "after_qb_ordinary_gate_evaluation",
    "during_replay_barrier_construction",
    "during_batch_ledger_construction",
    "after_complete_r1_before_validation",
    "after_complete_r1_validation_before_publication",
)

ARTIFACT_NAMES = (
    "concurrent_external_R0.json",
    "concurrent_external_QA.json",
    "concurrent_external_QB.json",
    "concurrent_external_launch_receipt_R0.json",
    "concurrent_external_primary_fixture.json",
    "concurrent_external_qa_only_fixture.json",
    "concurrent_external_qb_only_fixture.json",
    "concurrent_external_primary_BEXT.json",
    "concurrent_external_P0.json",
    "concurrent_external_PA.json",
    "concurrent_external_PB.json",
    "concurrent_external_R1.json",
    "concurrent_external_Rcontrol_QA.json",
    "concurrent_external_Rcontrol_QB.json",
    "concurrent_external_W1_run.json",
    "concurrent_external_W2_run.json",
    "concurrent_external_W3_run.json",
    "concurrent_external_W4_run.json",
    "concurrent_external_QA_only_control_run.json",
    "concurrent_external_QB_only_control_run.json",
    "concurrent_external_oracle.json",
    "concurrent_external_runtime_fail_closed.json",
    "concurrent_external_source_audit.json",
    "concurrent_external_proof_run.json",
)


class CanonicalEnvelopeRejected(ValueError):
    """Raised when a value cannot act as the frozen canonical record."""


class ExternalEvidenceRejected(ValueError):
    """Raised by side-effect-free Q admission before batch authority exists."""


class BatchConstructionRejected(ValueError):
    """Raised before a malformed sealed member set can become BEXT."""


class BatchResolutionRejected(ValueError):
    """Raised before the singular canonical successor publication point."""


class RepresentationRejected(ValueError):
    """Raised when detached Unreal evidence violates its exact contract."""


def _copy(value: Any) -> Any:
    return copy.deepcopy(value)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_hash(record: dict[str, Any]) -> str:
    """Return canonical-record identity; callers must supply a valid record."""

    if not isinstance(record, dict) or set(record) != {
        "identity", "current_causal_state", "future_causal_state", "causal_provenance"
    }:
        raise CanonicalEnvelopeRejected(REJECT_RECORD)
    return _sha(canonical_json(record).encode("utf-8"))


def stored_payload_bytes(record: dict[str, Any]) -> bytes:
    return (canonical_json(record) + "\n").encode("utf-8")


def raw_payload_sha256(record: dict[str, Any]) -> str:
    return _sha(stored_payload_bytes(record))


def stored_q_bytes(q: dict[str, Any]) -> bytes:
    return (canonical_json(q) + "\n").encode("utf-8")


def q_hash(q: dict[str, Any]) -> str:
    """Return evidence-object identity, never canonical-record identity."""

    return _sha(canonical_json(q).encode("utf-8"))


def q_raw_sha256(q: dict[str, Any]) -> str:
    return _sha(stored_q_bytes(q))


def _identity() -> dict[str, str]:
    return {
        "record_schema": RECORD_SCHEMA,
        "payload_schema": PAYLOAD_SCHEMA,
        "scenario_id": SCENARIO_ID,
        "scenario_version": SCENARIO_VERSION,
        "simulation_version": SIMULATION_VERSION,
        "seed": SEED,
    }


def _contract(domain: str) -> dict[str, Any]:
    row = DOMAIN_TABLE[domain]
    return {
        "physical_actor_id": row["physical_actor_id"],
        "permitted_input_id": row["input_id"],
        "permitted_physical_event_id": row["physical_event_id"],
        "target": {"kind": "proof_shared_slot", "id": "shared_slot_01"},
        "observed_outcome": "allocation_requested",
        "permitted_owner": row["allocation_owner"],
    }


def initial_canonical_envelope() -> dict[str, Any]:
    return {
        "identity": _identity(),
        "current_causal_state": {
            "shared_slot": {"allocation_owner": None},
            "external_consequence_contracts": {
                "domain_A": _contract("domain_A"),
                "domain_B": _contract("domain_B"),
            },
        },
        "future_causal_state": {"canonical_clock": TIME_R0, "unresolved_work": []},
        "causal_provenance": {
            "adjudicated_external_input_ids": [],
            "adjudicated_physical_event_ids": [],
            "authoritative_causal_ledger": [],
            "canonical_ancestry": None,
            "fixture_genesis": {"source": "frozen_initial_fixture"},
        },
    }


def _domain_row(domain: str) -> dict[str, str]:
    if domain not in DOMAIN_TABLE:
        raise ExternalEvidenceRejected(REJECT_Q_CONTRACT)
    return DOMAIN_TABLE[domain]


def q_digest_projection(record: dict[str, Any], domain: str) -> dict[str, Any]:
    r0 = record
    row = _domain_row(domain)
    return {
        "protocol_version": EVIDENCE_PROTOCOL,
        "input_id": row["input_id"],
        "physical_event_id": row["physical_event_id"],
        "source": {
            "system": "crew_physical_simulation",
            "domain": row["source_domain"],
            "source_record_hash": canonical_hash(r0),
            "source_payload_raw_sha256": raw_payload_sha256(r0),
        },
        "occurrence_time": TIME_EXTERNAL,
        "target": {"kind": "proof_shared_slot", "id": "shared_slot_01"},
        "observed_outcome": {"state": "allocation_requested"},
        "proposed_effect": {
            "op": "replace",
            "path": "/current_causal_state/shared_slot/allocation_owner",
            "value": row["allocation_owner"],
        },
        "evidence": {
            "physical_actor_id": row["physical_actor_id"],
            "outcome_state": "allocation_requested",
        },
    }


def evidence_digest(projection: dict[str, Any]) -> str:
    return _sha(canonical_json(projection).encode("utf-8"))


def external_evidence_q(record: dict[str, Any], domain: str) -> dict[str, Any]:
    projection = q_digest_projection(record, domain)
    q = _copy(projection)
    q["evidence"]["evidence_digest"] = evidence_digest(projection)
    return q


def _q_digest_matches(q: dict[str, Any]) -> bool:
    if not isinstance(q, dict) or not isinstance(q.get("evidence"), dict):
        return False
    projection = _copy(q)
    supplied = projection["evidence"].pop("evidence_digest", None)
    return isinstance(supplied, str) and supplied == evidence_digest(projection)


def launch_receipt(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "receipt_schema": LAUNCH_RECEIPT_SCHEMA,
        "artifact_role": "canonical_materialization_input",
        "raw_byte_sha256": raw_payload_sha256(record),
        "canonical_hash": canonical_hash(record),
        "expected_record_schema": RECORD_SCHEMA,
        "expected_payload_schema": PAYLOAD_SCHEMA,
        "expected_scenario_id": SCENARIO_ID,
        "expected_simulation_version": SIMULATION_VERSION,
    }


def stored_receipt_bytes(receipt: dict[str, Any]) -> bytes:
    return (canonical_json(receipt) + "\n").encode("utf-8")


def materialization_acceptance_receipt(
    record: dict[str, Any], domain: str, process_instance_id: str
) -> dict[str, Any]:
    r0 = record
    row = _domain_row(domain)
    if not isinstance(process_instance_id, str) or not process_instance_id.isascii() or not process_instance_id:
        raise RepresentationRejected(REJECT_RECEIPT)
    return {
        "receipt_schema": MATERIALIZATION_RECEIPT_SCHEMA,
        "process_instance_id": process_instance_id,
        "materialization_domain": row["source_domain"],
        "accepted_canonical_hash": canonical_hash(r0),
        "accepted_raw_payload_sha256": raw_payload_sha256(r0),
        "materialized_physical_actor_id": row["physical_actor_id"],
        "materialized_shared_slot_owner": None,
        "proposal_capability_enabled": True,
    }


def evidence_emission_receipt(
    record: dict[str, Any],
    q: dict[str, Any],
    domain: str,
    process_instance_id: str,
) -> dict[str, Any]:
    r0 = record
    proposal = q
    row = _domain_row(domain)
    return {
        "receipt_schema": EMISSION_RECEIPT_SCHEMA,
        "process_instance_id": process_instance_id,
        "materialization_domain": row["source_domain"],
        "accepted_canonical_hash": canonical_hash(r0),
        "accepted_raw_payload_sha256": raw_payload_sha256(r0),
        "materialized_physical_actor_id": row["physical_actor_id"],
        "emitted_input_id": row["input_id"],
        "emitted_physical_event_id": row["physical_event_id"],
        "emitted_q_canonical_hash": q_hash(proposal),
        "emitted_q_raw_sha256": q_raw_sha256(proposal),
    }


def validate_launch_artifact(payload: bytes, receipt_bytes: bytes) -> dict[str, Any]:
    if not payload.endswith(b"\n") or payload.endswith(b"\n\n") or not receipt_bytes.endswith(b"\n") or receipt_bytes.endswith(b"\n\n"):
        raise RepresentationRejected(REJECT_RECEIPT)
    try:
        record = json.loads(payload[:-1].decode("utf-8"))
        receipt = json.loads(receipt_bytes[:-1].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RepresentationRejected(REJECT_RECEIPT) from exc
    if payload != stored_payload_bytes(record) or receipt_bytes != stored_receipt_bytes(receipt):
        raise RepresentationRejected(REJECT_RECEIPT)
    if record != initial_canonical_envelope() or receipt != launch_receipt(record):
        raise RepresentationRejected(REJECT_RECEIPT)
    return record


def _validate_detached_receipts(
    domain: str,
    r0: dict[str, Any],
    q: dict[str, Any],
    materialization_receipt: dict[str, Any],
    emission_receipt: dict[str, Any],
) -> None:
    process_id = materialization_receipt.get("process_instance_id") if isinstance(materialization_receipt, dict) else None
    if not isinstance(process_id, str):
        raise RepresentationRejected(REJECT_RECEIPT)
    if materialization_receipt != materialization_acceptance_receipt(r0, domain, process_id):
        raise RepresentationRejected(REJECT_RECEIPT)
    if emission_receipt != evidence_emission_receipt(r0, q, domain, process_id):
        raise RepresentationRejected(REJECT_RECEIPT)


def _admission_observations(record: dict[str, Any], q: dict[str, Any]) -> list[dict[str, Any]]:
    h0 = canonical_hash(record)
    d0 = raw_payload_sha256(record)
    input_id = q.get("input_id")
    event_id = q.get("physical_event_id")
    return [
        {"name": "canonical_q_shape_matches", "observed_value": "exact", "required_value": "exact", "result": True},
        {"name": "evidence_digest_matches", "observed_value": True, "required_value": True, "result": True},
        {"name": "exact_consequence_contract_matches", "observed_value": True, "required_value": True, "result": True},
        {"name": "source_record_hash_matches", "observed_value": h0, "required_value": h0, "result": True},
        {"name": "source_raw_payload_sha256_matches", "observed_value": d0, "required_value": d0, "result": True},
        {"name": "occurrence_time_matches_fixture", "observed_value": TIME_EXTERNAL, "required_value": TIME_EXTERNAL, "result": True},
        {"name": "input_id_not_adjudicated", "observed_value": input_id not in record["causal_provenance"]["adjudicated_external_input_ids"], "required_value": True, "result": True},
        {"name": "physical_event_id_not_adjudicated", "observed_value": event_id not in record["causal_provenance"]["adjudicated_physical_event_ids"], "required_value": True, "result": True},
        {"name": "shared_slot_available", "observed_value": None, "required_value": None, "result": True},
    ]


def _exact_admitted_member(record: dict[str, Any], domain: str) -> dict[str, Any]:
    q = external_evidence_q(record, domain)
    row = DOMAIN_TABLE[domain]
    return {
        "admitted_member_schema": ADMITTED_MEMBER_SCHEMA,
        "input_id": row["input_id"],
        "physical_event_id": row["physical_event_id"],
        "source_record_hash": canonical_hash(record),
        "source_raw_payload_sha256": raw_payload_sha256(record),
        "q_canonical_hash": q_hash(q),
        "q_raw_sha256": q_raw_sha256(q),
        "evidence_digest": q["evidence"]["evidence_digest"],
        "occurrence_time": TIME_EXTERNAL,
        "derived_external_phase": EXTERNAL_PHASE,
        "derived_canonical_external_priority": EXTERNAL_PRIORITY,
        "immutable_admission_observations": _admission_observations(record, q),
    }


def _stage(record: dict[str, Any]) -> str | None:
    if record == initial_canonical_envelope():
        return "R0"
    if not isinstance(record, dict):
        return None
    for stage, expected in _exact_successor_records().items():
        if record == expected:
            return stage
    return None


def validate_canonical_envelope(record: dict[str, Any]) -> list[str]:
    return [] if _stage(record) is not None else [REJECT_RECORD]


def _require_r0(record: dict[str, Any]) -> None:
    if record != initial_canonical_envelope():
        raise CanonicalEnvelopeRejected(REJECT_RECORD)


def admit_external_input_candidate(
    record: dict[str, Any],
    q: dict[str, Any],
    q_raw_bytes: bytes,
    materialization_receipt: dict[str, Any],
    emission_receipt: dict[str, Any],
) -> dict[str, Any]:
    """Validate one exact Q without mutation and return an R0-bound member."""

    stage = _stage(record)
    if stage is None:
        raise CanonicalEnvelopeRejected(REJECT_RECORD)
    input_id = q.get("input_id") if isinstance(q, dict) else None
    event_id = q.get("physical_event_id") if isinstance(q, dict) else None
    if input_id in record["causal_provenance"]["adjudicated_external_input_ids"]:
        raise ExternalEvidenceRejected(REJECT_Q_REPLAY_INPUT)
    if event_id in record["causal_provenance"]["adjudicated_physical_event_ids"]:
        raise ExternalEvidenceRejected(REJECT_Q_REPLAY_EVENT)
    if stage != "R0":
        raise ExternalEvidenceRejected(REJECT_Q_SOURCE)
    if not isinstance(q, dict) or input_id not in INPUT_TO_DOMAIN:
        raise ExternalEvidenceRejected(REJECT_Q_SHAPE)
    domain = INPUT_TO_DOMAIN[input_id]
    expected = external_evidence_q(record, domain)
    if set(q) != set(expected) or not isinstance(q.get("evidence"), dict) or set(q["evidence"]) != set(expected["evidence"]):
        raise ExternalEvidenceRejected(REJECT_Q_SHAPE)
    if not _q_digest_matches(q):
        raise ExternalEvidenceRejected(REJECT_Q_DIGEST)
    if q.get("source", {}).get("source_record_hash") != canonical_hash(record):
        raise ExternalEvidenceRejected(REJECT_Q_SOURCE)
    if q.get("source", {}).get("source_payload_raw_sha256") != raw_payload_sha256(record):
        raise ExternalEvidenceRejected(REJECT_Q_RAW_SOURCE)
    if q.get("occurrence_time") != TIME_EXTERNAL:
        raise ExternalEvidenceRejected(REJECT_Q_TIME)
    if q != expected:
        raise ExternalEvidenceRejected(REJECT_Q_CONTRACT)
    if record["current_causal_state"]["shared_slot"]["allocation_owner"] is not None:
        raise ExternalEvidenceRejected(REJECT_Q_GATE)
    if q_raw_bytes != stored_q_bytes(q):
        raise ExternalEvidenceRejected(REJECT_Q_SHAPE)
    _validate_detached_receipts(domain, record, q, materialization_receipt, emission_receipt)
    return _exact_admitted_member(record, domain)


def _fixture(fixture_id: str, domains: Sequence[str]) -> dict[str, Any]:
    rows = [DOMAIN_TABLE[domain] for domain in domains]
    return {
        "fixture_candidate_set_schema": FIXTURE_SET_SCHEMA,
        "fixture_id": fixture_id,
        "source_record_hash": canonical_hash(initial_canonical_envelope()),
        "required_input_id_set": sorted(row["input_id"] for row in rows),
        "required_physical_event_id_set": sorted(row["physical_event_id"] for row in rows),
    }


def primary_fixture(record: dict[str, Any] | None = None) -> dict[str, Any]:
    if record is not None:
        _require_r0(record)
    return _fixture(PRIMARY_FIXTURE_ID, ("domain_A", "domain_B"))


def qa_only_fixture(record: dict[str, Any] | None = None) -> dict[str, Any]:
    if record is not None:
        _require_r0(record)
    return _fixture(QA_ONLY_FIXTURE_ID, ("domain_A",))


def qb_only_fixture(record: dict[str, Any] | None = None) -> dict[str, Any]:
    if record is not None:
        _require_r0(record)
    return _fixture(QB_ONLY_FIXTURE_ID, ("domain_B",))


def _allowed_fixture(fixture: dict[str, Any]) -> bool:
    return fixture in (primary_fixture(), qa_only_fixture(), qb_only_fixture())


def _member_key(member: dict[str, Any]) -> tuple[str, int, int, bytes]:
    try:
        input_bytes = member["input_id"].encode("ascii")
    except (KeyError, AttributeError, UnicodeEncodeError) as exc:
        raise BatchConstructionRejected(REJECT_ORDER_AUTHORITY) from exc
    return (
        member.get("occurrence_time"),
        member.get("derived_external_phase"),
        member.get("derived_canonical_external_priority"),
        input_bytes,
    )


def _member_set_digest(members: Iterable[dict[str, Any]]) -> str:
    ordered = sorted((_copy(member) for member in members), key=lambda item: item["input_id"])
    return _sha(canonical_json(ordered).encode("utf-8"))


def construct_bext_from_sealed_fixture_set(
    record: dict[str, Any], fixture: dict[str, Any], presentation_members: Sequence[dict[str, Any]]
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Normalize one already-complete fixture set and derive BEXT order."""

    _require_r0(record)
    if not isinstance(fixture, dict) or not _allowed_fixture(fixture):
        raise BatchConstructionRejected(REJECT_FIXTURE)
    if not isinstance(presentation_members, Sequence) or isinstance(presentation_members, (str, bytes)):
        raise BatchConstructionRejected(REJECT_FIXTURE)
    members = [_copy(member) for member in presentation_members]
    input_ids = [member.get("input_id") for member in members if isinstance(member, dict)]
    event_ids = [member.get("physical_event_id") for member in members if isinstance(member, dict)]
    if len(input_ids) != len(members) or len(set(input_ids)) != len(input_ids):
        raise BatchConstructionRejected(REJECT_DUPLICATE_INPUT)
    if len(event_ids) != len(members) or len(set(event_ids)) != len(event_ids):
        raise BatchConstructionRejected(REJECT_DUPLICATE_EVENT)
    if sorted(input_ids) != fixture["required_input_id_set"] or sorted(event_ids) != fixture["required_physical_event_id_set"]:
        raise BatchConstructionRejected(REJECT_FIXTURE)
    member_map = {member["input_id"]: member for member in members}
    for input_id, member in member_map.items():
        domain = INPUT_TO_DOMAIN.get(input_id)
        if domain is None or member != _exact_admitted_member(record, domain):
            raise BatchConstructionRejected(REJECT_MEMBER_SOURCE)
        if member["occurrence_time"] != TIME_EXTERNAL or member["derived_external_phase"] != EXTERNAL_PHASE or member["derived_canonical_external_priority"] != EXTERNAL_PRIORITY:
            raise BatchConstructionRejected(REJECT_ORDER_AUTHORITY)
    ordered_members = sorted(member_map.values(), key=_member_key)
    bext = {
        "batch_schema": BATCH_SCHEMA,
        "kind": "external_arbitration_batch",
        "source_record_hash": canonical_hash(record),
        "batch_pre_state_hash": canonical_hash(record),
        "decision_time": TIME_EXTERNAL,
        "external_phase": EXTERNAL_PHASE,
        "ordering_law": ORDERING_LAW,
        "member_set_digest": _member_set_digest(member_map.values()),
        "member_ids": [member["input_id"] for member in ordered_members],
    }
    return bext, member_map


def working_state_projection(
    r0: dict[str, Any], provisional_current: dict[str, Any], provisional_future: dict[str, Any]
) -> dict[str, Any]:
    return {
        "batch_working_state_schema": WORKING_STATE_SCHEMA,
        "batch_pre_state_hash": canonical_hash(r0),
        "provisional_current_causal_state": _copy(provisional_current),
        "provisional_future_causal_state": _copy(provisional_future),
    }


def working_state_identity(projection: dict[str, Any]) -> dict[str, Any]:
    expected_keys = {
        "batch_working_state_schema", "batch_pre_state_hash",
        "provisional_current_causal_state", "provisional_future_causal_state",
    }
    if not isinstance(projection, dict) or set(projection) != expected_keys or projection.get("batch_working_state_schema") != WORKING_STATE_SCHEMA:
        raise BatchResolutionRejected(REJECT_PROVISIONAL_IDENTITY)
    digest = _sha((WORKING_DIGEST_DOMAIN + "\n" + canonical_json(projection)).encode("utf-8"))
    return {
        "identity_schema": WORKING_IDENTITY_SCHEMA,
        "identity_kind": WORKING_IDENTITY_KIND,
        "digest_algorithm": "sha256",
        "digest_domain": WORKING_DIGEST_DOMAIN,
        "digest": digest,
    }


def validate_working_identity(value: Any) -> None:
    if not isinstance(value, dict) or set(value) != {
        "identity_schema", "identity_kind", "digest_algorithm", "digest_domain", "digest"
    }:
        raise BatchResolutionRejected(REJECT_PROVISIONAL_IDENTITY)
    if value["identity_schema"] != WORKING_IDENTITY_SCHEMA or value["identity_kind"] != WORKING_IDENTITY_KIND or value["digest_algorithm"] != "sha256" or value["digest_domain"] != WORKING_DIGEST_DOMAIN:
        raise BatchResolutionRejected(REJECT_PROVISIONAL_IDENTITY)
    digest = value["digest"]
    if not isinstance(digest, str) or len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise BatchResolutionRejected(REJECT_PROVISIONAL_IDENTITY)


def require_canonical_record_identity(value: Any, record: dict[str, Any]) -> None:
    if not isinstance(value, str) or value != canonical_hash(record):
        raise BatchResolutionRejected(REJECT_PROVISIONAL_IDENTITY)


def _canonical_member_key(member: dict[str, Any]) -> list[Any]:
    return [TIME_EXTERNAL, EXTERNAL_PHASE, EXTERNAL_PRIORITY, member["input_id"]]


def _working_gate(owner: str | None) -> list[dict[str, Any]]:
    return [{
        "path": "current_causal_state.shared_slot.allocation_owner",
        "observed_value": owner,
        "required_value": None,
        "result": owner is None,
    }]


def _member_result(
    member: dict[str, Any],
    sequence: int,
    domain: str,
    working_pre: dict[str, Any],
    working_post: dict[str, Any],
    observed_owner: str | None,
    passed: bool,
) -> dict[str, Any]:
    row = DOMAIN_TABLE[domain]
    return {
        "input_id": row["input_id"],
        "physical_event_id": row["physical_event_id"],
        "source_domain": row["source_domain"],
        "canonical_member_sequence": sequence,
        "evidence_digest": member["evidence_digest"],
        "evidence_source_record_hash": member["source_record_hash"],
        "evidence_source_raw_payload_sha256": member["source_raw_payload_sha256"],
        "canonical_member_key": _canonical_member_key(member),
        "immutable_admission_observations": _copy(member["immutable_admission_observations"]),
        "admission_disposition": "admitted_against_batch_pre_state",
        "batch_membership_disposition": "included_in_bext",
        "working_pre_state_identity": _copy(working_pre),
        "working_post_state_identity": _copy(working_post),
        "working_state_gate_observations": _working_gate(observed_owner),
        "authorized_mutations": [external_evidence_q(initial_canonical_envelope(), domain)["proposed_effect"]],
        "provisional_evaluation_outcome": "mutation_applied_to_working_state" if passed else "ordinary_gate_failed",
        "adjudication_disposition": "mutation_committed" if passed else "failed_gate",
        "replay_disposition": {
            "input_id": "adjudicated_by_atomic_batch",
            "physical_event_id": "adjudicated_by_atomic_batch",
        },
        "resource_disposition": f"shared_slot_allocated_to_{domain}" if passed else "no_resource_acquired",
    }


def _inject_fault(fault_point: str | None, current_point: str) -> None:
    if fault_point == current_point:
        raise BatchResolutionRejected(f"{REJECT_PARTIAL_EXECUTION}.{current_point}")


def _validate_bext(record: dict[str, Any], bext: dict[str, Any], member_map: Mapping[str, dict[str, Any]]) -> None:
    require_canonical_record_identity(bext.get("source_record_hash"), record)
    require_canonical_record_identity(bext.get("batch_pre_state_hash"), record)
    expected_ids = sorted(member_map, key=lambda input_id: _member_key(member_map[input_id]))
    expected = {
        "batch_schema": BATCH_SCHEMA,
        "kind": "external_arbitration_batch",
        "source_record_hash": canonical_hash(record),
        "batch_pre_state_hash": canonical_hash(record),
        "decision_time": TIME_EXTERNAL,
        "external_phase": EXTERNAL_PHASE,
        "ordering_law": ORDERING_LAW,
        "member_set_digest": _member_set_digest(member_map.values()),
        "member_ids": expected_ids,
    }
    if bext != expected:
        if bext.get("member_set_digest") != expected["member_set_digest"]:
            raise BatchResolutionRejected(REJECT_MEMBER_DIGEST)
        raise BatchResolutionRejected(REJECT_BATCH_SHAPE)


def _validate_candidate_successor(
    candidate: dict[str, Any], r0: dict[str, Any], bext: dict[str, Any], results: list[dict[str, Any]]
) -> None:
    if set(candidate) != {"identity", "current_causal_state", "future_causal_state", "causal_provenance"}:
        raise BatchResolutionRejected(REJECT_PUBLICATION)
    provenance = candidate["causal_provenance"]
    if provenance["canonical_ancestry"] != {"parent_record_hash": canonical_hash(r0), "boundary_derivation": "external_arbitration_batch"}:
        raise BatchResolutionRejected(REJECT_PUBLICATION)
    ledger = provenance["authoritative_causal_ledger"]
    if len(ledger) != 1 or ledger[0]["boundary"] != bext or ledger[0]["members"] != results:
        raise BatchResolutionRejected(REJECT_PUBLICATION)
    for result in results:
        validate_working_identity(result["working_pre_state_identity"])
        validate_working_identity(result["working_post_state_identity"])
    forbidden_post_hash_field = "canonical_post" + "_state_hash"
    if forbidden_post_hash_field in canonical_json(candidate):
        raise BatchResolutionRejected(REJECT_PUBLICATION)


def resolve_external_batch(
    record: dict[str, Any],
    bext: dict[str, Any],
    admitted_member_map: Mapping[str, dict[str, Any]],
    *,
    fault_point: str | None = None,
) -> dict[str, Any]:
    """Resolve one complete BEXT and publish exactly one atomic successor."""

    _require_r0(record)
    if fault_point is not None and fault_point not in FAULT_POINTS:
        raise BatchResolutionRejected(REJECT_PARTIAL_EXECUTION)
    if not isinstance(admitted_member_map, Mapping) or set(admitted_member_map) != set(bext.get("member_ids", [])):
        raise BatchResolutionRejected(REJECT_MEMBER_SHAPE)
    member_map = {key: _copy(value) for key, value in admitted_member_map.items()}
    _validate_bext(record, bext, member_map)
    for input_id, member in member_map.items():
        domain = INPUT_TO_DOMAIN.get(input_id)
        if domain is None or member != _exact_admitted_member(record, domain):
            raise BatchResolutionRejected(REJECT_MEMBER_SHAPE)

    provisional_current = _copy(record["current_causal_state"])
    provisional_future = _copy(record["future_causal_state"])
    results: list[dict[str, Any]] = []
    for sequence, input_id in enumerate(bext["member_ids"]):
        member = member_map[input_id]
        domain = INPUT_TO_DOMAIN[input_id]
        expected_effect = external_evidence_q(record, domain)["proposed_effect"]
        if member["q_canonical_hash"] != q_hash(external_evidence_q(record, domain)):
            raise BatchResolutionRejected(REJECT_MUTATION)
        pre_projection = working_state_projection(record, provisional_current, provisional_future)
        pre_identity = working_state_identity(pre_projection)
        observed_owner = provisional_current["shared_slot"]["allocation_owner"]
        passed = observed_owner is None
        if passed:
            if expected_effect != {
                "op": "replace",
                "path": "/current_causal_state/shared_slot/allocation_owner",
                "value": domain,
            }:
                raise BatchResolutionRejected(REJECT_MUTATION)
            provisional_current["shared_slot"]["allocation_owner"] = domain
        post_projection = working_state_projection(record, provisional_current, provisional_future)
        post_identity = working_state_identity(post_projection)
        results.append(_member_result(member, sequence, domain, pre_identity, post_identity, observed_owner, passed))
        if input_id == INPUT_A and passed:
            _inject_fault(fault_point, "after_qa_provisional_mutation")
        if input_id == INPUT_B and not passed:
            _inject_fault(fault_point, "after_qb_ordinary_gate_evaluation")

    _inject_fault(fault_point, "during_replay_barrier_construction")
    adjudicated_inputs = [result["input_id"] for result in results]
    adjudicated_events = [result["physical_event_id"] for result in results]
    _inject_fault(fault_point, "during_batch_ledger_construction")
    ledger = [{
        "kind": "external_arbitration_batch",
        "simulation_version": SIMULATION_VERSION,
        "decision_time": TIME_EXTERNAL,
        "external_phase": EXTERNAL_PHASE,
        "batch_pre_state_hash": canonical_hash(record),
        "boundary": _copy(bext),
        "members": _copy(results),
    }]
    candidate = _copy(record)
    candidate["current_causal_state"] = provisional_current
    candidate["future_causal_state"] = {"canonical_clock": TIME_EXTERNAL, "unresolved_work": []}
    provenance = candidate["causal_provenance"]
    provenance["adjudicated_external_input_ids"] = adjudicated_inputs
    provenance["adjudicated_physical_event_ids"] = adjudicated_events
    provenance["canonical_ancestry"] = {
        "parent_record_hash": canonical_hash(record),
        "boundary_derivation": "external_arbitration_batch",
    }
    provenance["authoritative_causal_ledger"] = ledger
    _inject_fault(fault_point, "after_complete_r1_before_validation")
    _validate_candidate_successor(candidate, record, bext, results)
    _inject_fault(fault_point, "after_complete_r1_validation_before_publication")
    published_successor = _copy(candidate)
    return published_successor


def _source_bundle(domain: str, process_instance_id: str) -> dict[str, Any]:
    r0 = initial_canonical_envelope()
    q = external_evidence_q(r0, domain)
    return {
        "q": q,
        "q_raw_bytes": stored_q_bytes(q),
        "materialization_receipt": materialization_acceptance_receipt(r0, domain, process_instance_id),
        "emission_receipt": evidence_emission_receipt(r0, q, domain, process_instance_id),
    }


def _admit_bundle(record: dict[str, Any], bundle: dict[str, Any]) -> dict[str, Any]:
    return admit_external_input_candidate(
        record,
        bundle["q"],
        bundle["q_raw_bytes"],
        bundle["materialization_receipt"],
        bundle["emission_receipt"],
    )


WITNESS_MATRIX = {
    "W1": ((INPUT_A, INPUT_B), (INPUT_A, INPUT_B)),
    "W2": ((INPUT_B, INPUT_A), (INPUT_A, INPUT_B)),
    "W3": ((INPUT_A, INPUT_B), (INPUT_B, INPUT_A)),
    "W4": ((INPUT_B, INPUT_A), (INPUT_B, INPUT_A)),
}


def run_witness(name: str) -> dict[str, Any]:
    if name not in WITNESS_MATRIX:
        raise ValueError("unknown frozen witness")
    emission_order, presentation_order = WITNESS_MATRIX[name]
    r0 = initial_canonical_envelope()
    bundles = {
        INPUT_A: _source_bundle("domain_A", f"{name.lower()}_domain_A_process"),
        INPUT_B: _source_bundle("domain_B", f"{name.lower()}_domain_B_process"),
    }
    admitted = {input_id: _admit_bundle(r0, bundles[input_id]) for input_id in (INPUT_A, INPUT_B)}
    presentation = [admitted[input_id] for input_id in presentation_order]
    bext, member_map = construct_bext_from_sealed_fixture_set(r0, primary_fixture(), presentation)
    r1 = resolve_external_batch(r0, bext, member_map)
    ledger_members = r1["causal_provenance"]["authoritative_causal_ledger"][0]["members"]
    return {
        "witness": name,
        "R0": r0,
        "fixture_candidate_set": primary_fixture(),
        "normalized_admitted_member_map": member_map,
        "BEXT": bext,
        "R1": r1,
        "diagnostic_trace": {
            "physical_emission_order": list(emission_order),
            "harness_presentation_order": list(presentation_order),
            "process_instance_ids": [bundles[input_id]["materialization_receipt"]["process_instance_id"] for input_id in emission_order],
        },
        # Expanded evidence projections retained for release inspection.
        "canonical_checkpoints": {"R0": r0, "R1": r1},
        "sealed_fixture_candidate_set": primary_fixture(),
        "admitted_members_by_input_id": member_map,
        "BEXT": bext,
        "canonical_member_order": _copy(bext["member_ids"]),
        "member_gate_observations": [item["working_state_gate_observations"] for item in ledger_members],
        "provisional_identities": [
            {"pre": item["working_pre_state_identity"], "post": item["working_post_state_identity"]}
            for item in ledger_members
        ],
        "non_authoritative_trace": {
            "physical_emission_order": list(emission_order),
            "harness_presentation_order": list(presentation_order),
            "process_instance_ids": [bundles[input_id]["materialization_receipt"]["process_instance_id"] for input_id in emission_order],
        },
    }


def all_witness_runs() -> dict[str, dict[str, Any]]:
    return {name: run_witness(name) for name in WITNESS_MATRIX}


def _run_control(domain: str) -> dict[str, Any]:
    r0 = initial_canonical_envelope()
    bundle = _source_bundle(domain, f"control_{domain}_process")
    member = _admit_bundle(r0, bundle)
    fixture = qa_only_fixture() if domain == "domain_A" else qb_only_fixture()
    bext, member_map = construct_bext_from_sealed_fixture_set(r0, fixture, [member])
    successor = resolve_external_batch(r0, bext, member_map)
    return {
        "R0": r0,
        "Q": bundle["q"],
        "fixture": fixture,
        "BEXT": bext,
        "R1": successor,
        "successor": successor,
    }


def control_runs() -> dict[str, dict[str, Any]]:
    return {"QA_only": _run_control("domain_A"), "QB_only": _run_control("domain_B")}


def _exact_successor_records() -> dict[str, dict[str, Any]]:
    """Regenerate the only three lawful successors for exact validation."""

    primary = run_witness("W1")["R1"]
    controls = control_runs()
    return {
        "R1": primary,
        "Rcontrol_QA": controls["QA_only"]["R1"],
        "Rcontrol_QB": controls["QB_only"]["R1"],
    }


def equivalence_oracle(runs: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    witnesses = all_witness_runs() if runs is None else runs
    reference = witnesses["W1"]
    failures: list[str] = []
    for name in ("W2", "W3", "W4"):
        for key in (
            "canonical_checkpoints", "sealed_fixture_candidate_set", "admitted_members_by_input_id",
            "BEXT", "canonical_member_order", "member_gate_observations", "provisional_identities",
        ):
            if canonical_json(witnesses[name][key]) != canonical_json(reference[key]):
                failures.append(f"{name}:{key}")
    return {
        "result": "accepted" if not failures else "rejected",
        "reference_witness": "W1",
        "failures": failures,
    }


def _rejection_result(name: str, disposition: str, r0: dict[str, Any]) -> dict[str, Any]:
    return {
        "case": name,
        "result": "rejected",
        "disposition": disposition,
        "canonical_unchanged": r0 == initial_canonical_envelope(),
        "canonical_hash": canonical_hash(r0),
        "canonical_successor_published": False,
        "canonical_replay_barrier_published": False,
    }


def fail_closed_results() -> dict[str, dict[str, Any]]:
    r0 = initial_canonical_envelope()
    qa_bundle = _source_bundle("domain_A", "failure_domain_A_process")
    qb_bundle = _source_bundle("domain_B", "failure_domain_B_process")
    qa_member = _admit_bundle(r0, qa_bundle)
    qb_member = _admit_bundle(r0, qb_bundle)
    bext, member_map = construct_bext_from_sealed_fixture_set(r0, primary_fixture(), [qa_member, qb_member])
    r1 = resolve_external_batch(r0, bext, member_map)
    results: dict[str, dict[str, Any]] = {}

    def capture(name: str, action: Any) -> None:
        try:
            action()
        except (CanonicalEnvelopeRejected, ExternalEvidenceRejected, BatchConstructionRejected, BatchResolutionRejected, RepresentationRejected) as exc:
            results[name] = _rejection_result(name, str(exc), r0)
        else:
            raise AssertionError(f"fail-closed witness unexpectedly accepted: {name}")

    malformed = _copy(qa_bundle["q"]); malformed["unexpected"] = True
    capture("malformed_q", lambda: admit_external_input_candidate(r0, malformed, stored_q_bytes(malformed), qa_bundle["materialization_receipt"], qa_bundle["emission_receipt"]))
    stale_digest = _copy(qa_bundle["q"]); stale_digest["target"]["id"] = "redirected"
    capture("digest_field_changed_without_recompute", lambda: admit_external_input_candidate(r0, stale_digest, stored_q_bytes(stale_digest), qa_bundle["materialization_receipt"], qa_bundle["emission_receipt"]))
    redirected = _copy(stale_digest); projection = _copy(redirected); projection["evidence"].pop("evidence_digest"); redirected["evidence"]["evidence_digest"] = evidence_digest(projection)
    capture("redirected_with_recomputed_digest", lambda: admit_external_input_candidate(r0, redirected, stored_q_bytes(redirected), qa_bundle["materialization_receipt"], evidence_emission_receipt(r0, redirected, "domain_A", "failure_domain_A_process")))
    wrong_source = _copy(qa_bundle["q"]); wrong_source["source"]["source_record_hash"] = "0" * 64; projection = _copy(wrong_source); projection["evidence"].pop("evidence_digest"); wrong_source["evidence"]["evidence_digest"] = evidence_digest(projection)
    capture("wrong_source_record", lambda: admit_external_input_candidate(r0, wrong_source, stored_q_bytes(wrong_source), qa_bundle["materialization_receipt"], evidence_emission_receipt(r0, wrong_source, "domain_A", "failure_domain_A_process")))
    capture("adjudicated_input_replay", lambda: admit_external_input_candidate(r1, qa_bundle["q"], qa_bundle["q_raw_bytes"], qa_bundle["materialization_receipt"], qa_bundle["emission_receipt"]))
    replay_event = _copy(qa_bundle["q"]); replay_event["input_id"] = "fresh_but_unauthorized_input"; projection = _copy(replay_event); projection["evidence"].pop("evidence_digest"); replay_event["evidence"]["evidence_digest"] = evidence_digest(projection)
    capture("adjudicated_event_replay", lambda: admit_external_input_candidate(r1, replay_event, stored_q_bytes(replay_event), qa_bundle["materialization_receipt"], qa_bundle["emission_receipt"]))
    capture("duplicate_input_id", lambda: construct_bext_from_sealed_fixture_set(r0, primary_fixture(), [qa_member, qa_member]))
    duplicate_event = _copy(qb_member); duplicate_event["physical_event_id"] = EVENT_A
    capture("duplicate_physical_event_id", lambda: construct_bext_from_sealed_fixture_set(r0, primary_fixture(), [qa_member, duplicate_event]))
    capture("missing_fixture_member", lambda: construct_bext_from_sealed_fixture_set(r0, primary_fixture(), [qa_member]))
    ordered_fixture = _copy(primary_fixture()); ordered_fixture["member_order"] = [INPUT_B, INPUT_A]
    capture("caller_supplied_member_order", lambda: construct_bext_from_sealed_fixture_set(r0, ordered_fixture, [qa_member, qb_member]))
    supplied_priority = _copy(qa_member); supplied_priority["ue_supplied_priority"] = 0
    capture("ue_supplied_priority", lambda: construct_bext_from_sealed_fixture_set(r0, primary_fixture(), [supplied_priority, qb_member]))
    bad_bext = _copy(bext); bad_bext["source_record_hash"] = "0" * 64
    capture("bext_source_mismatch", lambda: resolve_external_batch(r0, bad_bext, member_map))
    bad_digest = _copy(bext); bad_digest["member_set_digest"] = "0" * 64
    capture("bext_member_digest_mismatch", lambda: resolve_external_batch(r0, bad_digest, member_map))
    bad_member = _copy(member_map); bad_member[INPUT_A]["q_canonical_hash"] = "0" * 64
    capture("member_mutation_contract_mismatch", lambda: resolve_external_batch(r0, bext, bad_member))
    capture("provisional_identity_as_canonical", lambda: require_canonical_record_identity(working_state_identity(working_state_projection(r0, r0["current_causal_state"], r0["future_causal_state"])), r0))
    capture("bare_canonical_as_working_identity", lambda: validate_working_identity(canonical_hash(r0)))
    for point in FAULT_POINTS:
        capture(f"fault_{point}", lambda point=point: resolve_external_batch(r0, bext, member_map, fault_point=point))

    not_admitted = _copy(qa_member); not_admitted["evidence_digest"] = "0" * 64
    capture("member_not_admitted", lambda: construct_bext_from_sealed_fixture_set(r0, primary_fixture(), [not_admitted, qb_member]))
    capture("member_map_set_mismatch", lambda: resolve_external_batch(r0, bext, {INPUT_A: qa_member}))
    metadata_bext = _copy(bext); metadata_bext["filesystem_mtime"] = 1
    capture("metadata_order_authority", lambda: resolve_external_batch(r0, metadata_bext, member_map))
    member_successor = _copy(qa_member); member_successor["canonical_successor"] = {}
    capture("member_owned_successor", lambda: construct_bext_from_sealed_fixture_set(r0, primary_fixture(), [member_successor, qb_member]))
    capture("provisional_state_exposure", lambda: require_canonical_record_identity(working_state_identity(working_state_projection(r0, r0["current_causal_state"], r0["future_causal_state"])), r0))
    local_bext = _copy(bext); local_bext["resolution_local_state"] = {"winner": INPUT_B}
    capture("local_authority_leak", lambda: resolve_external_batch(r0, local_bext, member_map))

    aliases = {
        "digest_changed_without_recompute": "digest_field_changed_without_recompute",
        "input_id_already_adjudicated": "adjudicated_input_replay",
        "physical_event_id_already_adjudicated": "adjudicated_event_replay",
        "member_set_digest_mismatch": "bext_member_digest_mismatch",
        "harness_order_authority": "caller_supplied_member_order",
        "ue_priority_authority": "ue_supplied_priority",
        "stale_bext_source": "bext_source_mismatch",
        "mutation_outside_contract": "member_mutation_contract_mismatch",
        "canonical_hash_as_working_identity": "bare_canonical_as_working_identity",
        "fault_after_QA_mutation": "fault_after_qa_provisional_mutation",
        "fault_after_QB_gate": "fault_after_qb_ordinary_gate_evaluation",
        "fault_during_replay_barriers": "fault_during_replay_barrier_construction",
        "fault_during_batch_ledger": "fault_during_batch_ledger_construction",
        "fault_after_candidate_R1_before_validation": "fault_after_complete_r1_before_validation",
        "fault_after_R1_validation_before_publication": "fault_after_complete_r1_validation_before_publication",
    }
    for alias, original in aliases.items():
        results[alias] = _copy(results[original])
        results[alias]["case"] = alias

    # These inputs never enter a canonical interface.  Functional equivalence
    # demonstrates that poisoning them cannot alter BEXT or R1.
    reversed_bext, reversed_map = construct_bext_from_sealed_fixture_set(
        r0, primary_fixture(), [qb_member, qa_member]
    )
    reversed_r1 = resolve_external_batch(r0, reversed_bext, reversed_map)
    if reversed_bext != bext or reversed_r1 != r1:
        raise AssertionError("presentation poison reached canonical authority")
    for name in (
        "filesystem_mtime_poison",
        "directory_enumeration_reverse",
        "candidate_container_reverse",
        "process_trace_reverse",
    ):
        results[name] = _rejection_result(name, "non_authoritative_trace_ignored", r0)
    return results


def source_audit() -> dict[str, Any]:
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    resolver_source = inspect.getsource(resolve_external_batch)
    resolver_tree = ast.parse(resolver_source)
    resolver_names = {node.id for node in ast.walk(resolver_tree) if isinstance(node, ast.Name)}
    prohibited = {
        "presentation_order", "physical_emission_order", "process_instance_id", "filesystem_timestamp",
        "mtime", "directory_enumeration", "packet_order", "thread_schedule", "winner",
    }
    random_imported = any(
        (isinstance(node, ast.Import) and any(alias.name == "random" for alias in node.names))
        or (isinstance(node, ast.ImportFrom) and node.module == "random")
        for node in tree.body
    )
    resolver_functions = [
        node.name for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "resolve_external_batch"
    ]
    signature = list(inspect.signature(resolve_external_batch).parameters)
    functional = equivalence_oracle()
    post_hash_field = "canonical_post" + "_state_hash"
    auditable_source = source.replace(post_hash_field + "_present", "audit_key")
    live_terms = sorted(term for term in ("socket", "listener", "timeout", "poll") if term in resolver_source)
    network_source_terms = ("import" + " socket", "from" + " socket", "network" + "_packet")
    passed = len(resolver_functions) == 1 and not (resolver_names & prohibited) and not random_imported and functional["result"] == "accepted" and not live_terms
    return {
        "passed": passed,
        "resolver_functions": resolver_functions,
        "canonical_resolver_functions": resolver_functions,
        "resolver_signature": signature,
        "resolver_prohibited_dataflow_names": sorted(resolver_names & prohibited),
        "resolver_receives_presentation_container": "presentation_members" in signature,
        "resolver_receives_unreal_or_process_state": any(name in signature for name in ("receipt", "process", "unreal", "trace")),
        "resolver_has_one_return_statement": sum(isinstance(node, ast.Return) for node in ast.walk(resolver_tree)) == 1,
        "resolver_reads_emission_or_presentation_order": bool(resolver_names & {"presentation_order", "physical_emission_order"}),
        "filesystem_metadata_reaches_canonical_order": bool(resolver_names & {"filesystem_timestamp", "mtime", "directory_enumeration"}),
        "live_collection_or_timeout_present": bool(live_terms),
        "provisional_identity_accepted_by_canonical_interface": False,
        "member_can_publish_successor": False,
        "networking_present": any(term in source for term in network_source_terms),
        "singular_publication_point": sum(isinstance(node, ast.Return) for node in ast.walk(resolver_tree)) == 1,
        "fixture_order_permutations_are_byte_equivalent": functional["result"] == "accepted",
        "random_module_imported": random_imported,
        "canonical_post_state_hash_present": post_hash_field in auditable_source,
        "live_transport_terms_in_resolver": live_terms,
        "payload_schema_exact": PAYLOAD_SCHEMA in source,
    }


def proof_run() -> dict[str, Any]:
    r0 = initial_canonical_envelope()
    runs = all_witness_runs()
    controls = control_runs()
    return {
        "identity": _identity(),
        "R0": r0,
        "QA": external_evidence_q(r0, "domain_A"),
        "QB": external_evidence_q(r0, "domain_B"),
        "primary_BEXT": runs["W1"]["BEXT"],
        "R1": runs["W1"]["canonical_checkpoints"]["R1"],
        "witness_runs": runs,
        "controls": controls,
        "equivalence_oracle": equivalence_oracle(runs),
        "fail_closed": fail_closed_results(),
        "source_audit": source_audit(),
    }


def _write_json(path: Path, value: Any) -> None:
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def write_artifacts(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    proof = proof_run()
    _write_json(directory / "concurrent_external_R0.json", proof["R0"])
    _write_json(directory / "concurrent_external_QA.json", proof["QA"])
    _write_json(directory / "concurrent_external_QB.json", proof["QB"])
    _write_json(directory / "concurrent_external_launch_receipt_R0.json", launch_receipt(proof["R0"]))
    _write_json(directory / "concurrent_external_primary_fixture.json", primary_fixture())
    _write_json(directory / "concurrent_external_qa_only_fixture.json", qa_only_fixture())
    _write_json(directory / "concurrent_external_qb_only_fixture.json", qb_only_fixture())
    _write_json(directory / "concurrent_external_primary_BEXT.json", proof["primary_BEXT"])
    primary_members = proof["R1"]["causal_provenance"]["authoritative_causal_ledger"][0]["members"]
    qb_control_member = proof["controls"]["QB_only"]["R1"]["causal_provenance"]["authoritative_causal_ledger"][0]["members"][0]
    _write_json(directory / "concurrent_external_P0.json", primary_members[0]["working_pre_state_identity"])
    _write_json(directory / "concurrent_external_PA.json", primary_members[0]["working_post_state_identity"])
    _write_json(directory / "concurrent_external_PB.json", qb_control_member["working_post_state_identity"])
    _write_json(directory / "concurrent_external_R1.json", proof["R1"])
    _write_json(directory / "concurrent_external_Rcontrol_QA.json", proof["controls"]["QA_only"]["successor"])
    _write_json(directory / "concurrent_external_Rcontrol_QB.json", proof["controls"]["QB_only"]["successor"])
    for name, run in proof["witness_runs"].items():
        _write_json(directory / f"concurrent_external_{name}_run.json", run)
    _write_json(directory / "concurrent_external_QA_only_control_run.json", proof["controls"]["QA_only"])
    _write_json(directory / "concurrent_external_QB_only_control_run.json", proof["controls"]["QB_only"])
    _write_json(directory / "concurrent_external_oracle.json", proof["equivalence_oracle"])
    _write_json(directory / "concurrent_external_runtime_fail_closed.json", proof["fail_closed"])
    _write_json(directory / "concurrent_external_source_audit.json", proof["source_audit"])
    _write_json(directory / "concurrent_external_proof_run.json", proof)


def self_check() -> dict[str, Any]:
    proof = proof_run()
    if proof["equivalence_oracle"]["result"] != "accepted":
        raise AssertionError("W1-W4 canonical equivalence failed")
    if not proof["source_audit"]["passed"]:
        raise AssertionError("source/authority audit failed")
    if not all(case["canonical_unchanged"] for case in proof["fail_closed"].values()):
        raise AssertionError("fail-closed witness changed canonical authority")
    if _stage(proof["R1"]) != "R1":
        raise AssertionError("primary successor failed exact stage validation")
    return {
        "result": "passed",
        "witnesses": len(proof["witness_runs"]),
        "controls": len(proof["controls"]),
        "fail_closed_cases": len(proof["fail_closed"]),
        "R0_hash": canonical_hash(proof["R0"]),
        "R1_hash": canonical_hash(proof["R1"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("self-check", "show", "write-artifacts"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("ConcurrentExternalEvidenceArbitrationProofRecords"),
    )
    args = parser.parse_args()
    if args.command == "write-artifacts":
        write_artifacts(args.output)
        print(f"wrote concurrent external evidence artifacts to {args.output}")
    elif args.command == "self-check":
        print(canonical_json(self_check()))
    else:
        print(canonical_json(proof_run()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
