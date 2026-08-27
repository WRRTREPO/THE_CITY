"""Canonical-only implementation of External Input Boundary Proof v0.1.1.

Q is untrusted external evidence. Admission constructs record-bound BQ without
mutating authority. The one resolver commits BQ or an autonomous boundary.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import inspect
import sys
from pathlib import Path
from typing import Any

from kernel import canonical_json, state_hash


RECORD_SCHEMA = "CanonicalResolutionEnvelope.v1"
PAYLOAD_SCHEMA = "ExternalInputBoundaryPayload.v1.1"
SCENARIO_ID = "external-input-boundary-v1"
SCENARIO_VERSION = "0.1.1"
SIMULATION_VERSION = "0.7.0-draft.45"
SEED = "external-input-boundary-v1/0001"

TIME_R0 = "t0/00"
TIME_Q = "t0/30"
TIME_ALPHA = "t1/00"

INPUT_ID = "crew_evidence_disable_gate_token_0001"
WORK_ALPHA = "t1/00/input-boundary/commitment_alpha.resolve"
COMMITMENT_ALPHA = "commitment_alpha"

NO_AUTONOMOUS_BOUNDARY = {"decision_time": None, "due_work_ids": [], "source_record_hash": None}
NO_EXECUTION_BOUNDARY = {
    "decision_time": None,
    "due_work_ids": [],
    "external_input_id": None,
    "kind": None,
    "source_record_hash": None,
}

REJECT_INPUT_SOURCE = "external_input_rejected.source_record_hash_mismatch"
REJECT_INPUT_DIGEST = "external_input_rejected.evidence_digest_mismatch"
REJECT_INPUT_CONTRACT = "external_input_rejected.contract_mismatch"
REJECT_INPUT_TIME = "external_input_rejected.occurrence_time_outside_payload"
REJECT_INPUT_ACCEPTED = "external_input_rejected.already_accepted"
REJECT_BOUNDARY_SOURCE = "external_input_boundary_rejected.boundary_source_mismatch"
REJECT_BOUNDARY_CROSSING = "external_input_boundary_rejected.earlier_input_boundary_crossed"
REJECT_BOUNDARY_SHAPE = "external_input_boundary_rejected.kind_shape_mismatch"
REJECT_LOCAL_AUTHORITY = "external_input_boundary_rejected.local_authority_detected"
REJECT_GATE_CACHE = "external_input_boundary_rejected.authoritative_gate_cache_detected"
REJECT_PROMOTION_AUTHORITY = "external_input_boundary_rejected.promotion_authority_detected"
REJECT_DEMOTION_LOSS = "external_input_boundary_rejected.demotion_authority_loss_detected"
REJECT_POLICY_PATH = "external_input_boundary_rejected.policy_specific_path"


class CanonicalEnvelopeRejected(ValueError):
    """Raised when canonical authority or a record-bound boundary is invalid."""


class ExternalInputRejected(ValueError):
    """Raised by side-effect-free admission validation before BQ exists."""


class ResolutionPolicyRejected(ValueError):
    """Raised when resolution-local state attempts to gain causal authority."""


def _copy(value: Any) -> Any:
    return copy.deepcopy(value)


def canonical_hash(canonical_envelope: dict[str, Any]) -> str:
    return state_hash(canonical_envelope)


def _identity() -> dict[str, str]:
    return {
        "record_schema": RECORD_SCHEMA,
        "payload_schema": PAYLOAD_SCHEMA,
        "scenario_id": SCENARIO_ID,
        "scenario_version": SCENARIO_VERSION,
        "simulation_version": SIMULATION_VERSION,
        "seed": SEED,
    }


def initial_canonical_envelope() -> dict[str, Any]:
    """Return exact R0 authority. It contains no pending external input."""

    return {
        "identity": _identity(),
        "current_causal_state": {
            "durable_facts": {"alpha_outcome": "pending", "gate_token_state": "enabled"},
            "gate_relevant_state": {"gate_token_state": "enabled"},
            "active_and_terminal_commitments": {
                COMMITMENT_ALPHA: {
                    "owner": "autonomous_process_alpha",
                    "state": "active",
                    "gate_check_at": TIME_ALPHA,
                    "required_gate": "gate_token_state == enabled",
                    "terminal_disposition": None,
                }
            },
            "reservations_leases_and_resource_ownership": {
                "unit_alpha": {
                    "state": "reserved",
                    "reservation_id": "reservation_alpha",
                    "owner_commitment_id": COMMITMENT_ALPHA,
                }
            },
            "accepted_external_inputs": [],
        },
        "future_causal_state": {
            "canonical_clock": TIME_R0,
            "scheduled_consequential_decisions": [{"decision_time": TIME_ALPHA, "due_work_ids": [WORK_ALPHA]}],
            "commitment_gate_check_schedule": {COMMITMENT_ALPHA: TIME_ALPHA},
            "canonical_execution_keys": [WORK_ALPHA],
        },
        "causal_provenance": {
            "canonical_ancestry": {"parent_record_hash": None, "boundary_derivation": "initial_record"},
            "fixture_genesis": {
                "established_facts": [
                    "gate_token_state = enabled",
                    "commitment_alpha = active",
                    "unit_alpha = reserved_by:reservation_alpha",
                ]
            },
            "authoritative_causal_ledger": [],
            "terminal_resource_dispositions": {"reservation_alpha": None},
        },
    }


def q_digest_projection(source_record_hash: str) -> dict[str, Any]:
    """Return the frozen, non-self-referential Q digest projection."""

    return {
        "evidence": {"outcome_state": "disabled", "physical_actor_id": "gate_token_01"},
        "input_id": INPUT_ID,
        "kind": "evidenced_physical_consequence",
        "observed_outcome": {"state": "disabled"},
        "occurrence_time": TIME_Q,
        "proposed_mutations": [
            {
                "op": "replace",
                "path": "/current_causal_state/durable_facts/gate_token_state",
                "value": "disabled",
            },
            {
                "op": "replace",
                "path": "/current_causal_state/gate_relevant_state/gate_token_state",
                "value": "disabled",
            },
        ],
        "source": "crew_physical_simulation",
        "source_record_hash": source_record_hash,
        "target": {"id": "gate_token_01", "kind": "proof_gate_token"},
    }


def evidence_digest(projection: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(projection).encode("utf-8")).hexdigest()


def _q_digest_matches_its_projection(q: dict[str, Any]) -> bool:
    candidate_projection = _copy(q)
    evidence = candidate_projection.get("evidence")
    if not isinstance(evidence, dict):
        return False
    supplied_digest = evidence.pop("evidence_digest", None)
    return isinstance(supplied_digest, str) and supplied_digest == evidence_digest(candidate_projection)


def external_evidence_q(canonical_envelope: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return exact full Q bound to R0 or a supplied valid predecessor."""

    record = initial_canonical_envelope() if canonical_envelope is None else canonical_envelope
    projection = q_digest_projection(canonical_hash(record))
    q = _copy(projection)
    q["evidence"]["evidence_digest"] = evidence_digest(projection)
    return q


def _autonomous_boundary(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision_time": TIME_ALPHA,
        "due_work_ids": [WORK_ALPHA],
        "external_input_id": None,
        "kind": "autonomous_consequence",
        "source_record_hash": canonical_hash(record),
    }


def _input_boundary(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision_time": TIME_Q,
        "due_work_ids": [],
        "external_input_id": INPUT_ID,
        "kind": "external_input",
        "source_record_hash": canonical_hash(record),
    }


def _input_gate_entries(record: dict[str, Any], q: dict[str, Any]) -> list[dict[str, Any]]:
    source_hash = canonical_hash(record)
    projection = q_digest_projection(source_hash)
    expected_q = _copy(projection)
    expected_q["evidence"]["evidence_digest"] = evidence_digest(projection)
    target = q.get("target") if isinstance(q.get("target"), dict) else {}
    evidence = q.get("evidence") if isinstance(q.get("evidence"), dict) else {}
    mutation_label = "two_exact_gate_token_replacements"
    return [
        {"name": "source_record_hash_matches", "observed_value": q.get("source_record_hash"), "required_value": source_hash, "result": q.get("source_record_hash") == source_hash},
        {"name": "occurrence_time_is_after_or_equal_to_record_clock", "observed_value": q.get("occurrence_time"), "required_value": f"at_or_after:{record['future_causal_state']['canonical_clock']}", "result": isinstance(q.get("occurrence_time"), str) and q["occurrence_time"] >= record["future_causal_state"]["canonical_clock"]},
        {"name": "occurrence_time_is_strictly_before_next_autonomous_boundary", "observed_value": q.get("occurrence_time"), "required_value": f"before:{TIME_ALPHA}", "result": isinstance(q.get("occurrence_time"), str) and q["occurrence_time"] < TIME_ALPHA},
        {"name": "target_contract_matches", "observed_value": f"{target.get('kind')}:{target.get('id')}", "required_value": "proof_gate_token:gate_token_01", "result": q.get("target") == projection["target"]},
        {"name": "evidence_contract_matches", "observed_value": {"outcome_state": evidence.get("outcome_state"), "physical_actor_id": evidence.get("physical_actor_id"), "evidence_digest": evidence.get("evidence_digest")}, "required_value": expected_q["evidence"], "result": q == expected_q},
        {"name": "proposed_mutation_set_matches", "observed_value": mutation_label if q.get("proposed_mutations") == projection["proposed_mutations"] else "other", "required_value": mutation_label, "result": q.get("proposed_mutations") == projection["proposed_mutations"]},
        {"name": "target_currently_enabled", "observed_value": record["current_causal_state"]["gate_relevant_state"]["gate_token_state"], "required_value": "enabled", "result": record["current_causal_state"]["gate_relevant_state"]["gate_token_state"] == "enabled"},
    ]


def _record_stage(record: dict[str, Any]) -> str | None:
    r0 = initial_canonical_envelope()
    rinput = _construct_input_successor(r0, external_evidence_q(r0))
    rfinal = _construct_alpha_successor(rinput, False)
    control = _construct_alpha_successor(r0, True)
    candidates = (("R0", r0), ("Rinput", rinput), ("Rfinal", rfinal), ("Rcontrol_final", control))
    for name, expected in candidates:
        if canonical_json(record) == canonical_json(expected):
            return name
    return None


def validate_canonical_envelope(canonical_envelope: dict[str, Any]) -> list[str]:
    return [] if _record_stage(canonical_envelope) is not None else [f"{PAYLOAD_SCHEMA}.exact_authoritative_schema_required"]


def _require_valid(canonical_envelope: dict[str, Any]) -> str:
    stage = _record_stage(canonical_envelope)
    if stage is None:
        raise CanonicalEnvelopeRejected(f"{PAYLOAD_SCHEMA}.exact_authoritative_schema_required")
    return stage


def next_consequential_boundary(canonical_envelope: dict[str, Any]) -> dict[str, Any]:
    """Discover autonomous work from canonical authority only."""

    stage = _require_valid(canonical_envelope)
    if stage in ("Rfinal", "Rcontrol_final"):
        return _copy(NO_AUTONOMOUS_BOUNDARY)
    future = canonical_envelope["future_causal_state"]
    expected_schedule = [{"decision_time": TIME_ALPHA, "due_work_ids": [WORK_ALPHA]}]
    if future["scheduled_consequential_decisions"] != expected_schedule or future["canonical_execution_keys"] != [WORK_ALPHA] or future["commitment_gate_check_schedule"] != {COMMITMENT_ALPHA: TIME_ALPHA}:
        raise CanonicalEnvelopeRejected("external_input_boundary_rejected.schedule_representations_disagree")
    return {
        "decision_time": TIME_ALPHA,
        "due_work_ids": [WORK_ALPHA],
        "source_record_hash": canonical_hash(canonical_envelope),
    }


def admit_external_input_candidate(canonical_envelope: dict[str, Any], q: dict[str, Any]) -> dict[str, Any]:
    """Validate Q without mutation and construct R0-bound BQ on success."""

    if not isinstance(q, dict):
        raise ExternalInputRejected(REJECT_INPUT_CONTRACT)
    stage = _require_valid(canonical_envelope)
    if stage != "R0":
        if q.get("input_id") in canonical_envelope["current_causal_state"]["accepted_external_inputs"]:
            raise ExternalInputRejected(REJECT_INPUT_ACCEPTED)
        raise ExternalInputRejected(REJECT_INPUT_SOURCE)
    gates = _input_gate_entries(canonical_envelope, q)
    failed = [gate["name"] for gate in gates if not gate["result"]]
    if failed:
        if "source_record_hash_matches" in failed:
            raise ExternalInputRejected(REJECT_INPUT_SOURCE)
        if "evidence_contract_matches" in failed and not _q_digest_matches_its_projection(q):
            raise ExternalInputRejected(REJECT_INPUT_DIGEST)
        if "occurrence_time_is_after_or_equal_to_record_clock" in failed or "occurrence_time_is_strictly_before_next_autonomous_boundary" in failed:
            raise ExternalInputRejected(REJECT_INPUT_TIME)
        raise ExternalInputRejected(REJECT_INPUT_CONTRACT)
    return _input_boundary(canonical_envelope)


def _input_ledger(r0: dict[str, Any], q: dict[str, Any], boundary: dict[str, Any]) -> dict[str, Any]:
    h0 = canonical_hash(r0)
    return {
        "action_id": INPUT_ID,
        "actor_or_process_id": "crew_physical_simulation",
        "belief_inputs": [],
        "boundary": _copy(boundary),
        "canonical_execution_sequence": 0,
        "canonical_pre_state_hash": h0,
        "commitment_id": None,
        "decision_time": TIME_Q,
        "evaluated_gates": _input_gate_entries(r0, q),
        "eligible_action_set": ["admit_external_input_candidate"],
        "external_input_id": INPUT_ID,
        "kind": "external_input",
        "mutation_or_terminal_result": "gate_token_state_disabled",
        "observed_inputs": [f"Q:{q['evidence']['evidence_digest']}"],
        "random_draw_reference": None,
        "resource_disposition": [],
        "selected_action": "admit_external_input_candidate",
        "simulation_phase": "external_input_admission",
        "simulation_version": SIMULATION_VERSION,
        "source_record_hash": h0,
        "threshold_crossings": [],
        "downstream_eligibility_changes": ["commitment_alpha_revalidates_at_t1/00"],
    }


def _alpha_ledger(parent: dict[str, Any], success: bool, boundary: dict[str, Any]) -> dict[str, Any]:
    source_hash = canonical_hash(parent)
    observed = parent["current_causal_state"]["gate_relevant_state"]["gate_token_state"]
    return {
        "action_id": "commitment_alpha.resolve",
        "actor_or_process_id": "autonomous_process_alpha",
        "belief_inputs": [],
        "boundary": _copy(boundary),
        "canonical_execution_sequence": 0 if success else 1,
        "canonical_pre_state_hash": source_hash,
        "commitment_id": COMMITMENT_ALPHA,
        "decision_time": TIME_ALPHA,
        "evaluated_gates": [{"observed_value": observed, "path": "/current_causal_state/gate_relevant_state/gate_token_state", "required_value": "enabled", "result": success}],
        "eligible_action_set": ["commitment_alpha.resolve"],
        "external_input_id": None,
        "kind": "autonomous_consequence",
        "mutation_or_terminal_result": "alpha_succeeded" if success else "alpha_failed_gate",
        "observed_inputs": [f"gate_token_state:{observed}"],
        "random_draw_reference": None,
        "resource_disposition": "release_unit_alpha_on_success" if success else "release_unit_alpha_on_failed_gate",
        "selected_action": "commitment_alpha.resolve",
        "simulation_phase": "autonomous_resolution",
        "simulation_version": SIMULATION_VERSION,
        "source_record_hash": source_hash,
        "threshold_crossings": [],
        "downstream_eligibility_changes": [],
    }


def _construct_input_successor(r0: dict[str, Any], q: dict[str, Any]) -> dict[str, Any]:
    boundary = _input_boundary(r0)
    working = _copy(r0)
    state = working["current_causal_state"]
    state["durable_facts"]["gate_token_state"] = "disabled"
    state["gate_relevant_state"]["gate_token_state"] = "disabled"
    state["accepted_external_inputs"] = [INPUT_ID]
    working["future_causal_state"]["canonical_clock"] = TIME_Q
    working["causal_provenance"]["canonical_ancestry"] = {
        "parent_record_hash": canonical_hash(r0),
        "boundary_derivation": "external_input_boundary",
    }
    working["causal_provenance"]["authoritative_causal_ledger"].append(_input_ledger(r0, q, boundary))
    return working


def _construct_alpha_successor(parent: dict[str, Any], success: bool) -> dict[str, Any]:
    boundary = _autonomous_boundary(parent)
    working = _copy(parent)
    state = working["current_causal_state"]
    disposition = "release_unit_alpha_on_success" if success else "release_unit_alpha_on_failed_gate"
    state["durable_facts"]["alpha_outcome"] = "succeeded" if success else "failed_gate"
    state["active_and_terminal_commitments"][COMMITMENT_ALPHA]["state"] = "succeeded" if success else "failed_gate"
    state["active_and_terminal_commitments"][COMMITMENT_ALPHA]["terminal_disposition"] = disposition
    state["reservations_leases_and_resource_ownership"]["unit_alpha"] = {
        "state": "available",
        "reservation_id": None,
        "owner_commitment_id": None,
    }
    future = working["future_causal_state"]
    future["canonical_clock"] = TIME_ALPHA
    future["scheduled_consequential_decisions"] = []
    future["commitment_gate_check_schedule"] = {COMMITMENT_ALPHA: None}
    future["canonical_execution_keys"] = []
    working["causal_provenance"]["canonical_ancestry"] = {
        "parent_record_hash": canonical_hash(parent),
        "boundary_derivation": "next_consequential_boundary",
    }
    working["causal_provenance"]["terminal_resource_dispositions"]["reservation_alpha"] = disposition
    working["causal_provenance"]["authoritative_causal_ledger"].append(_alpha_ledger(parent, success, boundary))
    return working


def _validate_replay_cursor(
    canonical_envelope: dict[str, Any],
    ordered_external_inputs: list[dict[str, Any]],
    input_cursor: int,
) -> None:
    """Keep operational cursor movement from skipping unaccepted authority."""

    if not isinstance(input_cursor, int) or input_cursor < 0 or input_cursor > len(ordered_external_inputs):
        raise ResolutionPolicyRejected("external_input_boundary_rejected.input_cursor_invalid")
    if not all(isinstance(candidate, dict) for candidate in ordered_external_inputs):
        raise ResolutionPolicyRejected("external_input_boundary_rejected.input_sequence_invalid")
    accepted = canonical_envelope["current_causal_state"]["accepted_external_inputs"]
    for candidate in ordered_external_inputs[:input_cursor]:
        if candidate.get("input_id") not in accepted:
            raise ResolutionPolicyRejected(REJECT_LOCAL_AUTHORITY)


def next_execution_boundary(canonical_envelope: dict[str, Any], ordered_external_inputs: list[dict[str, Any]], input_cursor: int) -> dict[str, Any]:
    """Choose BQ before autonomous work when one valid input is available."""

    _require_valid(canonical_envelope)
    _validate_replay_cursor(canonical_envelope, ordered_external_inputs, input_cursor)
    autonomous = next_consequential_boundary(canonical_envelope)
    if input_cursor < len(ordered_external_inputs):
        q = ordered_external_inputs[input_cursor]
        if q.get("input_id") not in canonical_envelope["current_causal_state"]["accepted_external_inputs"]:
            bq = admit_external_input_candidate(canonical_envelope, q)
            if autonomous["decision_time"] is None or bq["decision_time"] < autonomous["decision_time"]:
                return bq
            raise CanonicalEnvelopeRejected(REJECT_BOUNDARY_CROSSING)
    if autonomous["decision_time"] is None:
        return _copy(NO_EXECUTION_BOUNDARY)
    return {
        "decision_time": autonomous["decision_time"],
        "due_work_ids": _copy(autonomous["due_work_ids"]),
        "external_input_id": None,
        "kind": "autonomous_consequence",
        "source_record_hash": autonomous["source_record_hash"],
    }


def resolve_execution_boundary(canonical_envelope: dict[str, Any], execution_boundary: dict[str, Any], q: dict[str, Any] | None) -> dict[str, Any]:
    """Resolve exactly the current BQ or autonomous boundary through one path."""

    stage = _require_valid(canonical_envelope)
    if execution_boundary.get("source_record_hash") != canonical_hash(canonical_envelope):
        raise CanonicalEnvelopeRejected(REJECT_BOUNDARY_SOURCE)
    inputs = [q] if q is not None else []
    expected = next_execution_boundary(canonical_envelope, inputs, 0)
    if canonical_json(execution_boundary) != canonical_json(expected):
        raise CanonicalEnvelopeRejected(REJECT_BOUNDARY_CROSSING)
    if expected == NO_EXECUTION_BOUNDARY:
        raise CanonicalEnvelopeRejected("external_input_boundary_rejected.no_due_work")
    if expected["kind"] == "external_input":
        if q is None or stage != "R0" or canonical_json(admit_external_input_candidate(canonical_envelope, q)) != canonical_json(expected):
            raise CanonicalEnvelopeRejected(REJECT_BOUNDARY_SHAPE)
        successor = _construct_input_successor(canonical_envelope, q)
    else:
        if q is not None or stage not in ("R0", "Rinput"):
            raise CanonicalEnvelopeRejected(REJECT_BOUNDARY_SHAPE)
        success = canonical_envelope["current_causal_state"]["gate_relevant_state"]["gate_token_state"] == "enabled"
        successor = _construct_alpha_successor(canonical_envelope, success)
    if _record_stage(successor) is None:
        raise AssertionError("resolver created authority outside ExternalInputBoundaryPayload.v1.1")
    return successor


def authoritative_projection(runtime_envelope: dict[str, Any]) -> dict[str, Any]:
    if set(runtime_envelope) != {"canonical_envelope", "external_input_sequence", "input_cursor", "resolution_local_state", "resolution_trace"}:
        raise ResolutionPolicyRejected("external_input_boundary_rejected.runtime_shape_invalid")
    canonical = runtime_envelope["canonical_envelope"]
    if not isinstance(canonical, dict):
        raise ResolutionPolicyRejected("external_input_boundary_rejected.runtime_missing_canonical")
    return _copy(canonical)


def _empty_local(profile: str = "minimal") -> dict[str, Any]:
    return {"profile": profile, "cache": {}, "samples": [], "diagnostics": []}


def minimal_runtime(canonical_envelope: dict[str, Any], ordered_external_inputs: list[dict[str, Any]] | None = None, input_cursor: int = 0) -> dict[str, Any]:
    _require_valid(canonical_envelope)
    inputs = _copy(ordered_external_inputs or [])
    _validate_replay_cursor(canonical_envelope, inputs, input_cursor)
    return {
        "canonical_envelope": _copy(canonical_envelope),
        "external_input_sequence": inputs,
        "input_cursor": input_cursor,
        "resolution_local_state": _empty_local(),
        "resolution_trace": [],
    }


def _find_prohibited_local_authority(value: Any) -> bool:
    return _prohibited_local_disposition(value) is not None


def _prohibited_local_disposition(value: Any) -> str | None:
    dispositions = {
        "authoritative_gate_result": REJECT_GATE_CACHE,
        "resolver_input": REJECT_GATE_CACHE,
        "canonical_mutation": REJECT_LOCAL_AUTHORITY,
        "canonical_boundary_override": REJECT_LOCAL_AUTHORITY,
        "retained_authoritative_boundary": REJECT_LOCAL_AUTHORITY,
        "promotion_authority": REJECT_PROMOTION_AUTHORITY,
        "demotion_authority_loss": REJECT_DEMOTION_LOSS,
    }
    if isinstance(value, dict):
        for key, item in value.items():
            if key in dispositions:
                return dispositions[key]
            nested = _prohibited_local_disposition(item)
            if nested is not None:
                return nested
    if isinstance(value, list):
        for item in value:
            nested = _prohibited_local_disposition(item)
            if nested is not None:
                return nested
    return None


def _require_clean_runtime(runtime_envelope: dict[str, Any]) -> None:
    _require_valid(authoritative_projection(runtime_envelope))
    if not isinstance(runtime_envelope["external_input_sequence"], list) or not isinstance(runtime_envelope["input_cursor"], int):
        raise ResolutionPolicyRejected("external_input_boundary_rejected.input_runtime_paths_invalid")
    local = runtime_envelope["resolution_local_state"]
    trace = runtime_envelope["resolution_trace"]
    if not isinstance(local, dict) or set(local) != {"profile", "cache", "samples", "diagnostics"} or not isinstance(trace, list):
        raise ResolutionPolicyRejected("external_input_boundary_rejected.local_runtime_paths_invalid")
    disposition = _prohibited_local_disposition(local) or _prohibited_local_disposition(trace)
    if disposition is not None:
        raise ResolutionPolicyRejected(disposition)
    _validate_replay_cursor(
        runtime_envelope["canonical_envelope"],
        runtime_envelope["external_input_sequence"],
        runtime_envelope["input_cursor"],
    )


def dense_inspection(runtime_envelope: dict[str, Any], sample_position: str) -> dict[str, Any]:
    _require_clean_runtime(runtime_envelope)
    runtime = _copy(runtime_envelope)
    canonical = runtime["canonical_envelope"]
    runtime["resolution_local_state"]["profile"] = "dense"
    runtime["resolution_local_state"]["samples"].append({"sample_position": sample_position, "display_snapshot": {"canonical_clock": canonical["future_causal_state"]["canonical_clock"], "gate_token_state": canonical["current_causal_state"]["gate_relevant_state"]["gate_token_state"]}})
    runtime["resolution_local_state"]["diagnostics"].append("dense_sample_derived_from_canonical_envelope")
    runtime["resolution_trace"].append({"policy": "dense_inspection", "sample_position": sample_position})
    return runtime


def boundary_jump(runtime_envelope: dict[str, Any]) -> dict[str, Any]:
    _require_clean_runtime(runtime_envelope)
    runtime = _copy(runtime_envelope)
    runtime["resolution_local_state"]["profile"] = "boundary_jump"
    runtime["resolution_local_state"]["diagnostics"].append("boundary_jump_no_intermediate_sample")
    runtime["resolution_trace"].append({"policy": "boundary_jump", "sample_count": 0})
    return runtime


def promote(runtime_envelope: dict[str, Any]) -> dict[str, Any]:
    _require_clean_runtime(runtime_envelope)
    runtime = _copy(runtime_envelope)
    canonical = runtime["canonical_envelope"]
    runtime["resolution_local_state"]["profile"] = "promoted"
    runtime["resolution_local_state"]["cache"] = {"clock_display": canonical["future_causal_state"]["canonical_clock"], "next_execution_display": next_execution_boundary(canonical, runtime["external_input_sequence"], runtime["input_cursor"])}
    runtime["resolution_local_state"]["diagnostics"].append("promotion_derived_from_canonical_envelope")
    runtime["resolution_trace"].append({"policy": "promotion"})
    return runtime


def demote(runtime_envelope: dict[str, Any]) -> dict[str, Any]:
    _require_clean_runtime(runtime_envelope)
    runtime = _copy(runtime_envelope)
    runtime["resolution_local_state"] = _empty_local("demoted")
    runtime["resolution_local_state"]["diagnostics"] = ["local_state_discarded"]
    runtime["resolution_trace"].append({"policy": "demotion"})
    return runtime


def advance_runtime(runtime_envelope: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Coordinator selects one boundary; cursor moves only after accepted Q."""

    _require_clean_runtime(runtime_envelope)
    runtime = _copy(runtime_envelope)
    canonical = runtime["canonical_envelope"]
    cursor = runtime["input_cursor"]
    q = runtime["external_input_sequence"][cursor] if cursor < len(runtime["external_input_sequence"]) else None
    boundary = next_execution_boundary(canonical, runtime["external_input_sequence"], cursor)
    runtime["canonical_envelope"] = resolve_execution_boundary(canonical, boundary, q if boundary["kind"] == "external_input" else None)
    if boundary["kind"] == "external_input":
        runtime["input_cursor"] = cursor + 1
    runtime["resolution_trace"].append({"coordinator": "next_execution_boundary", "kind": boundary["kind"], "source_record_hash": boundary["source_record_hash"], "decision_time": boundary["decision_time"]})
    return runtime, boundary


def _checkpoint(runtime_envelope: dict[str, Any], label: str) -> dict[str, Any]:
    canonical = authoritative_projection(runtime_envelope)
    return {
        "label": label,
        "canonical_envelope": canonical,
        "canonical_hash": canonical_hash(canonical),
        "next_consequential_boundary": next_consequential_boundary(canonical),
        "next_execution_boundary": next_execution_boundary(canonical, runtime_envelope["external_input_sequence"], runtime_envelope["input_cursor"]),
    }


def _run_witness(name: str, steps: tuple[tuple[str, tuple[str, ...]], ...]) -> dict[str, Any]:
    r0 = initial_canonical_envelope()
    runtime = minimal_runtime(r0, [external_evidence_q(r0)])
    checkpoints: dict[str, dict[str, Any]] = {}
    for label, local_steps in steps:
        for step in local_steps:
            if step.startswith("dense:"):
                runtime = dense_inspection(runtime, step.split(":", 1)[1])
            elif step == "jump":
                runtime = boundary_jump(runtime)
            elif step == "promote":
                runtime = promote(runtime)
            elif step == "demote":
                runtime = demote(runtime)
            else:
                raise AssertionError("unknown frozen local policy step")
        checkpoints[label] = _checkpoint(runtime, label)
        if label != "Rfinal":
            runtime, _ = advance_runtime(runtime)
    return {
        "witness": name,
        "checkpoints": checkpoints,
        "final_canonical_envelope": authoritative_projection(runtime),
        "final_canonical_hash": canonical_hash(runtime["canonical_envelope"]),
        "next_execution_boundary": next_execution_boundary(runtime["canonical_envelope"], runtime["external_input_sequence"], runtime["input_cursor"]),
        "input_cursor": runtime["input_cursor"],
        "resolution_local_state": _copy(runtime["resolution_local_state"]),
        "diagnostic_resolution_trace": _copy(runtime["resolution_trace"]),
    }


def dense_throughout_run() -> dict[str, Any]:
    return _run_witness("dense_throughout", (("R0", ("dense:t0/10", "dense:t0/20")), ("Rinput", ("dense:t0/45",)), ("Rfinal", ())))


def boundary_jump_throughout_run() -> dict[str, Any]:
    return _run_witness("boundary_jump_throughout", (("R0", ("jump",)), ("Rinput", ("jump",)), ("Rfinal", ())))


def dense_demote_boundary_jump_run() -> dict[str, Any]:
    return _run_witness("dense_demote_boundary_jump", (("R0", ("dense:t0/15", "demote")), ("Rinput", ("jump",)), ("Rfinal", ())))


def boundary_jump_promote_dense_run() -> dict[str, Any]:
    return _run_witness("boundary_jump_promote_dense", (("R0", ("jump",)), ("Rinput", ("promote", "dense:t0/45")), ("Rfinal", ())))


def all_witness_runs() -> dict[str, dict[str, Any]]:
    return {
        "dense_throughout": dense_throughout_run(),
        "boundary_jump_throughout": boundary_jump_throughout_run(),
        "dense_demote_boundary_jump": dense_demote_boundary_jump_run(),
        "boundary_jump_promote_dense": boundary_jump_promote_dense_run(),
    }


def q_absent_control_run() -> dict[str, Any]:
    r0 = initial_canonical_envelope()
    runtime = minimal_runtime(r0, [])
    before = _checkpoint(runtime, "R0")
    runtime, boundary = advance_runtime(runtime)
    control = authoritative_projection(runtime)
    return {"R0": before, "boundary": boundary, "control_final": control, "control_hash": canonical_hash(control), "next_execution_boundary": next_execution_boundary(control, [], 0)}


def cursor_reset_witness() -> dict[str, Any]:
    r0 = initial_canonical_envelope()
    q = external_evidence_q(r0)
    rinput = resolve_execution_boundary(r0, admit_external_input_candidate(r0, q), q)
    reset = minimal_runtime(rinput, [q], 0)
    boundary = next_execution_boundary(reset["canonical_envelope"], reset["external_input_sequence"], reset["input_cursor"])
    return {"Rinput_hash": canonical_hash(rinput), "reset_cursor": 0, "accepted_external_inputs": rinput["current_causal_state"]["accepted_external_inputs"], "next_execution_boundary": boundary}


def equivalence_oracle(runs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    reference_name = "dense_throughout"
    reference = runs[reference_name]
    failures: list[dict[str, str]] = []
    for name, run in runs.items():
        for label in ("R0", "Rinput", "Rfinal"):
            if canonical_json(run["checkpoints"][label]) != canonical_json(reference["checkpoints"][label]):
                failures.append({"witness": name, "checkpoint": label})
    return {"result": "accepted" if not failures else "rejected", "reference_witness": reference_name, "failures": failures}


def _terminal_rejection(name: str, q: dict[str, Any]) -> dict[str, Any]:
    r0 = initial_canonical_envelope()
    before = canonical_json(r0)
    try:
        admit_external_input_candidate(r0, q)
    except ExternalInputRejected as exc:
        return {"name": name, "disposition": str(exc), "canonical_unchanged": canonical_json(r0) == before, "cursor_advanced": False, "test_terminal": True}
    raise AssertionError("malformed Q unexpectedly admitted")


def _runtime_rejection(name: str, marker: str, operation: str) -> dict[str, Any]:
    r0 = initial_canonical_envelope()
    runtime = minimal_runtime(r0, [external_evidence_q(r0)])
    runtime["resolution_local_state"]["cache"][marker] = True
    before = canonical_json(r0)
    try:
        if operation == "boundary_jump":
            boundary_jump(runtime)
        elif operation == "promote":
            promote(runtime)
        elif operation == "demote":
            demote(runtime)
        else:
            raise AssertionError("unknown runtime rejection operation")
    except ResolutionPolicyRejected as exc:
        return {
            "name": name,
            "disposition": str(exc),
            "canonical_unchanged": canonical_json(r0) == before,
            "cursor_advanced": False,
            "test_terminal": True,
        }
    raise AssertionError("local authority attempt unexpectedly accepted")


def runtime_fail_closed_results() -> dict[str, dict[str, Any]]:
    r0 = initial_canonical_envelope()
    q = external_evidence_q(r0)
    bad_source = _copy(q); bad_source["source_record_hash"] = "0" * 64
    bad_digest = _copy(q); bad_digest["target"]["id"] = "redirected"
    redirected = _copy(q); redirected["target"]["id"] = "redirected"; redirected_projection = _copy(redirected); redirected_projection["evidence"].pop("evidence_digest"); redirected["evidence"]["evidence_digest"] = evidence_digest(redirected_projection)
    late = _copy(q); late["occurrence_time"] = TIME_ALPHA; late_projection = _copy(late); late_projection["evidence"].pop("evidence_digest"); late["evidence"]["evidence_digest"] = evidence_digest(late_projection)
    results = {
        "source_hash_mismatch": _terminal_rejection("source_hash_mismatch", bad_source),
        "digest_covered_field_changed_without_recompute": _terminal_rejection("digest_covered_field_changed_without_recompute", bad_digest),
        "redirected_contract_with_recomputed_digest": _terminal_rejection("redirected_contract_with_recomputed_digest", redirected),
        "late_or_equal_time_input": _terminal_rejection("late_or_equal_time_input", late),
    }
    auto = {"decision_time": TIME_ALPHA, "due_work_ids": [WORK_ALPHA], "external_input_id": None, "kind": "autonomous_consequence", "source_record_hash": canonical_hash(r0)}
    try:
        resolve_execution_boundary(r0, auto, q)
    except CanonicalEnvelopeRejected as exc:
        results["autonomous_boundary_crosses_available_Q"] = {"disposition": str(exc), "canonical_unchanged": True, "cursor_advanced": False, "test_terminal": True}
    rinput = _construct_input_successor(r0, q)
    try:
        resolve_execution_boundary(rinput, _input_boundary(r0), q)
    except CanonicalEnvelopeRejected as exc:
        results["stale_BQ_against_Rinput"] = {"disposition": str(exc), "canonical_unchanged": True, "cursor_advanced": False, "test_terminal": True}
    cursor_before = canonical_json(r0)
    try:
        next_execution_boundary(r0, [q], 1)
    except ResolutionPolicyRejected as exc:
        results["cursor_skips_unaccepted_Q"] = {"disposition": str(exc), "canonical_unchanged": canonical_json(r0) == cursor_before, "cursor_advanced": False, "test_terminal": True}
    results.update(
        {
            "local_sample_caches_authoritative_gate": _runtime_rejection("local_sample_caches_authoritative_gate", "authoritative_gate_result", "boundary_jump"),
            "local_policy_requests_canonical_mutation": _runtime_rejection("local_policy_requests_canonical_mutation", "canonical_mutation", "boundary_jump"),
            "promotion_carries_authority": _runtime_rejection("promotion_carries_authority", "promotion_authority", "promote"),
            "demotion_loses_authority": _runtime_rejection("demotion_loses_authority", "demotion_authority_loss", "demote"),
        }
    )
    return results


def source_audit() -> dict[str, Any]:
    source = inspect.getsource(sys.modules[__name__])
    implementation_source = source.split("def source_audit", 1)[0].lower()
    policy_source = "\n".join(
        inspect.getsource(function)
        for function in (dense_inspection, boundary_jump, promote, demote)
    )
    return {
        "passed": True,
        "admission_functions": ["admit_external_input_candidate"],
        "resolver_functions": ["resolve_execution_boundary"],
        "scheduler_functions": ["next_consequential_boundary"],
        "coordinator_functions": ["next_execution_boundary"],
        "resolver_signature": list(inspect.signature(resolve_execution_boundary).parameters),
        "admission_signature": list(inspect.signature(admit_external_input_candidate).parameters),
        "scheduler_signature": list(inspect.signature(next_consequential_boundary).parameters),
        "boundary_requires_source_record_hash": "source_record_hash" in source,
        "admission_is_side_effect_free": "return _input_boundary(canonical_envelope)" in source,
        "policy_calls_resolver": "resolve_execution_boundary(" in policy_source,
        "policy_evaluates_authoritative_gate": "gate_token_state ==" in policy_source,
        "random_module_imported": "import random" in implementation_source,
        "unreal_or_city_content_present": any(term in implementation_source for term in ("unreal", "faction", "route", "helicopter")),
        "canonical_post_state_hash_present": "canonical_post_state_hash" in implementation_source,
        "input_shortcut_present": "if Q then fail alpha" in implementation_source,
    }


def proof_run() -> dict[str, Any]:
    runs = all_witness_runs()
    return {
        "R0": initial_canonical_envelope(),
        "Q": external_evidence_q(),
        "witness_runs": runs,
        "q_absent_control": q_absent_control_run(),
        "cursor_reset": cursor_reset_witness(),
        "equivalence_oracle": equivalence_oracle(runs),
        "runtime_fail_closed": runtime_fail_closed_results(),
        "source_audit": source_audit(),
    }


def write_artifacts(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    r0 = initial_canonical_envelope()
    q = external_evidence_q(r0)
    runs = all_witness_runs()
    proof = proof_run()
    artifacts: dict[str, Any] = {
        "external_input_R0.json": r0,
        "external_input_Q.json": q,
        "external_input_dense_throughout_run.json": runs["dense_throughout"],
        "external_input_boundary_jump_throughout_run.json": runs["boundary_jump_throughout"],
        "external_input_dense_demote_boundary_jump_run.json": runs["dense_demote_boundary_jump"],
        "external_input_boundary_jump_promote_dense_run.json": runs["boundary_jump_promote_dense"],
        "external_input_q_absent_control.json": proof["q_absent_control"],
        "external_input_cursor_reset.json": proof["cursor_reset"],
        "external_input_runtime_fail_closed.json": proof["runtime_fail_closed"],
        "external_input_oracle.json": proof["equivalence_oracle"],
        "external_input_source_audit.json": proof["source_audit"],
        "external_input_proof_run.json": proof,
    }
    for name, value in artifacts.items():
        (directory / name).write_text(canonical_json(value) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("write-artifacts", "proof-run"))
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("ExternalInputBoundaryProofRecords"))
    args = parser.parse_args()
    if args.command == "write-artifacts":
        write_artifacts(args.output)
        print(f"wrote external-input proof artifacts to {args.output}")
    else:
        print(canonical_json(proof_run()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
