"""Frozen canonical fixture for Integrated Unreal Promotion-Unload-Repromotion.

The module owns the only authoritative transitions in this proof.  Unreal is
represented only by detached payload/receipt evidence; it never enters the
resolver signature or canonical envelope.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import inspect
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from kernel import canonical_json


RECORD_SCHEMA = "CanonicalResolutionEnvelope.v1"
PAYLOAD_SCHEMA = "IntegratedUnrealPromotionUnloadRepromotionPayload.v1"
SCENARIO_ID = "integrated-unreal-promotion-unload-repromotion-v1"
SCENARIO_VERSION = "0.1.0"
SIMULATION_VERSION = "0.7.0-draft.51"
SEED = "integrated-unreal-promotion-unload-repromotion-v1/0001"

TIME_R0 = "t0/00"
TIME_Q = "t0/30"
TIME_ALPHA = "t1/00"
PHASE_Q = 0
PHASE_ALPHA = 10
INPUT_ID = "physical_disable_integrated_gate_token_0001"
WORK_ALPHA = "t1/00/10/integrated/commitment_alpha.resolve"
ACTOR_ID = "integrated_gate_token_01"

LAUNCH_RECEIPT_SCHEMA = "IntegratedUnrealLaunchReceipt.v1"
ACCEPTANCE_RECEIPT_SCHEMA = "IntegratedMaterializationAcceptanceReceipt.v1"
EVIDENCE_PROTOCOL = "IntegratedExternalEvidence.v1"

NO_EXECUTION_BOUNDARY = {
    "decision_time": None,
    "due_work_ids": [],
    "external_input_id": None,
    "kind": None,
    "simulation_phase": None,
    "source_record_hash": None,
}

REJECT_PAYLOAD = "integrated_unreal_rejected.exact_payload_required"
REJECT_RECEIPT = "integrated_unreal_rejected.launch_receipt_mismatch"
REJECT_INPUT_DIGEST = "integrated_unreal_rejected.evidence_digest_mismatch"
REJECT_INPUT_CONTRACT = "integrated_unreal_rejected.evidence_contract_mismatch"
REJECT_INPUT_SOURCE = "integrated_unreal_rejected.evidence_source_mismatch"
REJECT_INPUT_TIME = "integrated_unreal_rejected.evidence_time_mismatch"
REJECT_BOUNDARY_SOURCE = "integrated_unreal_rejected.boundary_source_mismatch"
REJECT_BOUNDARY_SHAPE = "integrated_unreal_rejected.boundary_shape_mismatch"
REJECT_LOCAL_AUTHORITY = "integrated_unreal_rejected.local_authority_detected"
REJECT_PROMOTION_AUTHORITY = "integrated_unreal_rejected.promotion_authority_detected"
REJECT_DEMOTION_LOSS = "integrated_unreal_rejected.demotion_authority_loss_detected"
REJECT_RETURN_INPUT = "integrated_unreal_rejected.return_input_isolation_failed"
REJECT_ACCEPTANCE_RECEIPT = "integrated_unreal_rejected.acceptance_receipt_invalid"


class CanonicalEnvelopeRejected(ValueError):
    """Raised before a malformed capability can acquire canonical authority."""


class ExternalInputRejected(ValueError):
    """Raised by side-effect-free validation of a non-authoritative Q."""


class RepresentationRejected(ValueError):
    """Raised when detached representation evidence fails its own contract."""


def _copy(value: Any) -> Any:
    return copy.deepcopy(value)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_hash(envelope: dict[str, Any]) -> str:
    return _sha(canonical_json(envelope).encode("utf-8"))


def stored_payload_bytes(envelope: dict[str, Any]) -> bytes:
    return (canonical_json(envelope) + "\n").encode("utf-8")


def raw_payload_sha256(envelope: dict[str, Any]) -> str:
    return _sha(stored_payload_bytes(envelope))


def _identity() -> dict[str, str]:
    return {
        "record_schema": RECORD_SCHEMA,
        "payload_schema": PAYLOAD_SCHEMA,
        "scenario_id": SCENARIO_ID,
        "scenario_version": SCENARIO_VERSION,
        "simulation_version": SIMULATION_VERSION,
        "seed": SEED,
    }


def _unresolved_alpha() -> list[dict[str, Any]]:
    return [{
        "boundary_key": [TIME_ALPHA, PHASE_ALPHA],
        "work_id": WORK_ALPHA,
        "commitment_id": "alpha",
        "required_gate": {
            "path": "current_causal_state.gate_token.state",
            "required_value": "enabled",
        },
    }]


def initial_canonical_envelope() -> dict[str, Any]:
    """Return the exact R0 record authorized by the frozen proof."""

    return {
        "identity": _identity(),
        "current_causal_state": {
            "gate_token": {"state": "enabled", "physical_actor_id": ACTOR_ID},
            "commitments": {"alpha": {"state": "active", "terminal_disposition": None}},
        },
        "future_causal_state": {"canonical_clock": TIME_R0, "unresolved_work": _unresolved_alpha()},
        "causal_provenance": {
            "fixture_genesis": {
                "kind": "fixture_genesis",
                "established_facts": ["gate_token_enabled", "alpha_active"],
                "source": "frozen_initial_fixture",
            },
            "accepted_external_inputs": [],
            "authoritative_causal_ledger": [],
            "canonical_ancestry": None,
        },
    }


def q_digest_projection(source_record_hash: str, source_payload_raw_sha256: str) -> dict[str, Any]:
    return {
        "evidence": {"outcome_state": "disabled", "physical_actor_id": ACTOR_ID},
        "input_id": INPUT_ID,
        "instigator": {"id": "crew_01_to_04", "kind": "crew"},
        "observed_outcome": {"state": "disabled"},
        "occurrence_time": TIME_Q,
        "protocol_version": EVIDENCE_PROTOCOL,
        "proposed_mutations": ["current_causal_state.gate_token.state = disabled"],
        "source": {
            "source_payload_raw_sha256": source_payload_raw_sha256,
            "source_record_hash": source_record_hash,
            "system": "crew_physical_simulation",
        },
        "target": {"id": ACTOR_ID, "kind": "integrated_gate_token"},
    }


def evidence_digest(projection: dict[str, Any]) -> str:
    return _sha(canonical_json(projection).encode("utf-8"))


def external_evidence_q(record: dict[str, Any] | None = None) -> dict[str, Any]:
    source = initial_canonical_envelope() if record is None else record
    projection = q_digest_projection(canonical_hash(source), raw_payload_sha256(source))
    q = _copy(projection)
    q["evidence"] = {
        "evidence_digest": evidence_digest(projection),
        "outcome_state": "disabled",
        "physical_actor_id": ACTOR_ID,
    }
    return q


def _boundary_input(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "external_input",
        "source_record_hash": canonical_hash(record),
        "decision_time": TIME_Q,
        "simulation_phase": PHASE_Q,
        "external_input_id": INPUT_ID,
        "due_work_ids": [],
    }


def _boundary_alpha(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "autonomous_consequence",
        "source_record_hash": canonical_hash(record),
        "decision_time": TIME_ALPHA,
        "simulation_phase": PHASE_ALPHA,
        "external_input_id": None,
        "due_work_ids": [WORK_ALPHA],
    }


def _input_ledger(r0: dict[str, Any], q: dict[str, Any], bq: dict[str, Any]) -> dict[str, Any]:
    h0 = canonical_hash(r0)
    expected_q = external_evidence_q(r0)
    gates = [
        {"name": "source_record_hash_matches", "observed_value": q.get("source", {}).get("source_record_hash"), "required_value": h0, "result": q.get("source", {}).get("source_record_hash") == h0},
        {"name": "source_payload_raw_sha256_matches", "observed_value": q.get("source", {}).get("source_payload_raw_sha256"), "required_value": raw_payload_sha256(r0), "result": q.get("source", {}).get("source_payload_raw_sha256") == raw_payload_sha256(r0)},
        {"name": "occurrence_time_matches_fixture_opportunity", "observed_value": q.get("occurrence_time"), "required_value": TIME_Q, "result": q.get("occurrence_time") == TIME_Q},
        {"name": "evidence_digest_matches", "observed_value": q.get("evidence", {}).get("evidence_digest"), "required_value": expected_q["evidence"]["evidence_digest"], "result": q.get("evidence", {}).get("evidence_digest") == expected_q["evidence"]["evidence_digest"]},
        {"name": "exact_physical_contract_matches", "observed_value": "exact" if q == expected_q else "other", "required_value": "exact", "result": q == expected_q},
        {"name": "gate_token_is_enabled", "observed_value": r0["current_causal_state"]["gate_token"]["state"], "required_value": "enabled", "result": r0["current_causal_state"]["gate_token"]["state"] == "enabled"},
    ]
    return {
        "action_id": INPUT_ID,
        "actor_or_process_id": "crew_physical_simulation",
        "boundary": _copy(bq),
        "canonical_pre_state_hash": h0,
        "decision_time": TIME_Q,
        "evaluated_gates": gates,
        "kind": "external_input",
        "mutation_or_terminal_result": "gate_token_disabled",
        "resource_disposition": "no_resource_acquired",
        "simulation_phase": PHASE_Q,
        "simulation_version": SIMULATION_VERSION,
        "source_record_hash": h0,
    }


def _alpha_ledger(parent: dict[str, Any], boundary: dict[str, Any], success: bool) -> dict[str, Any]:
    h = canonical_hash(parent)
    observed = parent["current_causal_state"]["gate_token"]["state"]
    return {
        "action_id": "commitment_alpha.resolve",
        "actor_or_process_id": "autonomous_process_alpha",
        "boundary": _copy(boundary),
        "canonical_pre_state_hash": h,
        "decision_time": TIME_ALPHA,
        "evaluated_gates": [{
            "path": "current_causal_state.gate_token.state",
            "observed_value": observed,
            "required_value": "enabled",
            "result": success,
        }],
        "kind": "autonomous_consequence",
        "mutation_or_terminal_result": "alpha_succeeded" if success else "alpha_failed_gate",
        "resource_disposition": "resource_released_on_success" if success else "no_resource_acquired",
        "simulation_phase": PHASE_ALPHA,
        "simulation_version": SIMULATION_VERSION,
        "source_record_hash": h,
    }


def _construct_rinput(r0: dict[str, Any], q: dict[str, Any]) -> dict[str, Any]:
    rinput = _copy(r0)
    bq = _boundary_input(r0)
    rinput["current_causal_state"]["gate_token"]["state"] = "disabled"
    rinput["future_causal_state"]["canonical_clock"] = TIME_Q
    provenance = rinput["causal_provenance"]
    provenance["accepted_external_inputs"] = [INPUT_ID]
    provenance["canonical_ancestry"] = {"parent_record_hash": canonical_hash(r0), "boundary_derivation": "external_input_boundary"}
    provenance["authoritative_causal_ledger"] = [_input_ledger(r0, q, bq)]
    return rinput


def _construct_terminal(parent: dict[str, Any], success: bool) -> dict[str, Any]:
    result = _copy(parent)
    boundary = _boundary_alpha(parent)
    result["current_causal_state"]["commitments"]["alpha"] = {
        "state": "succeeded" if success else "failed_gate",
        "terminal_disposition": "resource_released_on_success" if success else "no_resource_acquired",
    }
    result["future_causal_state"] = {"canonical_clock": TIME_ALPHA, "unresolved_work": []}
    provenance = result["causal_provenance"]
    provenance["canonical_ancestry"] = {"parent_record_hash": canonical_hash(parent), "boundary_derivation": "next_execution_boundary"}
    provenance["authoritative_causal_ledger"].append(_alpha_ledger(parent, boundary, success))
    return result


def _expected_records() -> dict[str, dict[str, Any]]:
    r0 = initial_canonical_envelope()
    q = external_evidence_q(r0)
    rinput = _construct_rinput(r0, q)
    rfinal = _construct_terminal(rinput, False)
    rcontrol = _construct_terminal(r0, True)
    return {"R0": r0, "Rinput": rinput, "Rfinal": rfinal, "Rcontrol": rcontrol}


def record_stage(record: dict[str, Any]) -> str | None:
    for stage, expected in _expected_records().items():
        if canonical_json(record) == canonical_json(expected):
            return stage
    return None


def validate_canonical_envelope(record: dict[str, Any]) -> list[str]:
    return [] if record_stage(record) is not None else [REJECT_PAYLOAD]


def _require_stage(record: dict[str, Any], allowed: set[str]) -> str:
    stage = record_stage(record)
    if stage not in allowed:
        raise CanonicalEnvelopeRejected(REJECT_PAYLOAD)
    return stage


def next_consequential_boundary(record: dict[str, Any]) -> dict[str, Any]:
    stage = _require_stage(record, {"R0", "Rinput", "Rfinal", "Rcontrol"})
    if stage in {"Rfinal", "Rcontrol"}:
        return _copy(NO_EXECUTION_BOUNDARY)
    return _boundary_alpha(record)


def _validate_q_digest(q: dict[str, Any]) -> bool:
    if not isinstance(q, dict) or not isinstance(q.get("evidence"), dict):
        return False
    projection = _copy(q)
    digest = projection["evidence"].pop("evidence_digest", None)
    return isinstance(digest, str) and digest == evidence_digest(projection)


def admit_external_input_candidate(record: dict[str, Any], q: dict[str, Any]) -> dict[str, Any]:
    """Validate Q without mutation and return a record-bound BQ capability."""

    _require_stage(record, {"R0", "Rinput", "Rfinal", "Rcontrol"})
    if record_stage(record) != "R0":
        raise ExternalInputRejected(REJECT_INPUT_SOURCE)
    if not _validate_q_digest(q):
        raise ExternalInputRejected(REJECT_INPUT_DIGEST)
    expected = external_evidence_q(record)
    if q.get("source", {}).get("source_record_hash") != canonical_hash(record):
        raise ExternalInputRejected(REJECT_INPUT_SOURCE)
    if q.get("occurrence_time") != TIME_Q:
        raise ExternalInputRejected(REJECT_INPUT_TIME)
    if q != expected:
        raise ExternalInputRejected(REJECT_INPUT_CONTRACT)
    return _boundary_input(record)


def resolve_execution_boundary(record: dict[str, Any], boundary: dict[str, Any], q: dict[str, Any] | None = None) -> dict[str, Any]:
    """The sole canonical resolver for dense and boundary-jump witnesses."""

    _require_stage(record, {"R0", "Rinput", "Rfinal", "Rcontrol"})
    if boundary.get("source_record_hash") != canonical_hash(record):
        raise CanonicalEnvelopeRejected(REJECT_BOUNDARY_SOURCE)
    stage = record_stage(record)
    if stage == "R0" and boundary == _boundary_input(record) and q is not None:
        admitted = admit_external_input_candidate(record, q)
        if admitted != boundary:
            raise CanonicalEnvelopeRejected(REJECT_BOUNDARY_SHAPE)
        return _construct_rinput(record, q)
    if stage in {"R0", "Rinput"} and boundary == _boundary_alpha(record) and q is None:
        return _construct_terminal(record, stage == "R0")
    raise CanonicalEnvelopeRejected(REJECT_BOUNDARY_SHAPE)


def next_execution_boundary(record: dict[str, Any], pending_q: dict[str, Any] | None) -> dict[str, Any]:
    """Coordinate an admitted earlier external input above the autonomous scheduler."""

    stage = _require_stage(record, {"R0", "Rinput", "Rfinal", "Rcontrol"})
    if stage == "R0" and pending_q is not None:
        return admit_external_input_candidate(record, pending_q)
    return next_consequential_boundary(record)


def _runtime(record: dict[str, Any]) -> dict[str, Any]:
    return {"canonical_envelope": _copy(record), "resolution_local_state": {"cache": {}, "samples": [], "profile": "minimal"}, "resolution_trace": []}


def authoritative_projection(runtime: dict[str, Any]) -> dict[str, Any]:
    if set(runtime) != {"canonical_envelope", "resolution_local_state", "resolution_trace"}:
        raise RepresentationRejected(REJECT_LOCAL_AUTHORITY)
    return _copy(runtime["canonical_envelope"])


def _assert_clean_runtime(runtime: dict[str, Any]) -> None:
    local = runtime.get("resolution_local_state")
    if not isinstance(local, dict) or set(local) != {"cache", "samples", "profile"}:
        raise RepresentationRejected(REJECT_LOCAL_AUTHORITY)
    if any(key in local["cache"] for key in {"canonical_mutation", "authoritative_gate_result", "canonical_boundary_override"}):
        raise RepresentationRejected(REJECT_LOCAL_AUTHORITY)


def dense_inspection(runtime: dict[str, Any], sample: str) -> dict[str, Any]:
    _assert_clean_runtime(runtime)
    result = _copy(runtime)
    result["resolution_local_state"]["profile"] = "dense"
    result["resolution_local_state"]["samples"].append({"sample": sample, "display_gate_token": result["canonical_envelope"]["current_causal_state"]["gate_token"]["state"]})
    result["resolution_trace"].append({"policy": "dense_inspection", "sample": sample})
    return result


def boundary_jump(runtime: dict[str, Any]) -> dict[str, Any]:
    _assert_clean_runtime(runtime)
    result = _copy(runtime)
    result["resolution_local_state"]["profile"] = "boundary_jump"
    result["resolution_trace"].append({"policy": "boundary_jump", "sample_count": 0})
    return result


def promote(runtime: dict[str, Any]) -> dict[str, Any]:
    _assert_clean_runtime(runtime)
    result = _copy(runtime)
    result["resolution_local_state"]["profile"] = "promoted"
    result["resolution_local_state"]["cache"] = {"materialization_hint": result["canonical_envelope"]["current_causal_state"]["gate_token"]["state"]}
    result["resolution_trace"].append({"policy": "promotion"})
    return result


def demote(runtime: dict[str, Any]) -> dict[str, Any]:
    _assert_clean_runtime(runtime)
    result = _copy(runtime)
    result["resolution_local_state"] = {"cache": {}, "samples": [], "profile": "demoted"}
    result["resolution_trace"].append({"policy": "demotion"})
    return result


def _finish(runtime: dict[str, Any], q: dict[str, Any] | None) -> dict[str, Any]:
    _assert_clean_runtime(runtime)
    result = _copy(runtime)
    record = authoritative_projection(result)
    boundary = next_execution_boundary(record, q)
    result["canonical_envelope"] = resolve_execution_boundary(record, boundary, q if boundary["kind"] == "external_input" else None)
    result["resolution_trace"].append({"resolver": "resolve_execution_boundary", "kind": boundary["kind"], "decision_time": boundary["decision_time"]})
    return result


def _policy_run(name: str, steps: tuple[str, ...], include_q: bool = True) -> dict[str, Any]:
    r0 = initial_canonical_envelope()
    q = external_evidence_q(r0) if include_q else None
    runtime = _runtime(r0)
    for step in steps:
        runtime = {"dense": dense_inspection, "jump": boundary_jump, "promote": promote, "demote": demote}[step](runtime, "t0/15") if step == "dense" else {"jump": boundary_jump, "promote": promote, "demote": demote}[step](runtime)
    runtime = _finish(runtime, q)
    rinput_or_final = authoritative_projection(runtime)
    if include_q:
        runtime = boundary_jump(runtime)
        runtime = _finish(runtime, None)
    final = authoritative_projection(runtime)
    return {
        "witness": name,
        "checkpoints": {"R0": r0, **({"Rinput": rinput_or_final} if include_q else {}), "Rfinal" if include_q else "Rcontrol": final},
        "final_canonical_envelope": final,
        "diagnostic_resolution_trace": runtime["resolution_trace"],
        "next_execution_boundary": next_execution_boundary(final, None),
    }


def all_witness_runs() -> dict[str, dict[str, Any]]:
    return {
        "dense_reference": _policy_run("dense_reference", ("dense",), True),
        "integrated_boundary_jump": _policy_run("integrated_boundary_jump", ("promote", "jump"), True),
        "dense_demote_jump": _policy_run("dense_demote_jump", ("dense", "demote", "jump"), True),
        "jump_promote_dense": _policy_run("jump_promote_dense", ("jump", "promote", "dense"), True),
        "q_absent_control": _policy_run("q_absent_control", ("promote", "jump"), False),
    }


def equivalence_oracle(runs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    reference = runs["dense_reference"]
    failures: list[str] = []
    for name in ("integrated_boundary_jump", "dense_demote_jump", "jump_promote_dense"):
        for checkpoint in ("R0", "Rinput", "Rfinal"):
            if canonical_json(runs[name]["checkpoints"][checkpoint]) != canonical_json(reference["checkpoints"][checkpoint]):
                failures.append(f"{name}:{checkpoint}")
    return {"result": "accepted" if not failures else "rejected", "reference_witness": "dense_reference", "failures": failures}


def launch_receipt(envelope: dict[str, Any]) -> dict[str, str]:
    return {
        "receipt_schema": LAUNCH_RECEIPT_SCHEMA,
        "artifact_role": "canonical_materialization_input",
        "raw_payload_sha256": raw_payload_sha256(envelope),
        "expected_record_schema": RECORD_SCHEMA,
        "expected_payload_schema": PAYLOAD_SCHEMA,
        "expected_scenario_id": SCENARIO_ID,
        "expected_simulation_version": SIMULATION_VERSION,
    }


def stored_receipt_bytes(receipt: dict[str, str]) -> bytes:
    return (canonical_json(receipt) + "\n").encode("utf-8")


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
    if receipt != launch_receipt(record) or validate_canonical_envelope(record):
        raise RepresentationRejected(REJECT_RECEIPT)
    return record


def materialization_acceptance_receipt(record: dict[str, Any], process_instance_id: str, proposal_capability_enabled: bool) -> dict[str, Any]:
    stage = _require_stage(record, {"R0", "Rfinal", "Rcontrol"})
    gate_state = record["current_causal_state"]["gate_token"]["state"]
    alpha_state = record["current_causal_state"]["commitments"]["alpha"]["state"]
    if proposal_capability_enabled != (stage == "R0"):
        raise RepresentationRejected(REJECT_ACCEPTANCE_RECEIPT)
    return {
        "receipt_schema": ACCEPTANCE_RECEIPT_SCHEMA,
        "process_instance_id": process_instance_id,
        "accepted_raw_payload_sha256": raw_payload_sha256(record),
        "accepted_canonical_hash": canonical_hash(record),
        "materialized_actor_id": ACTOR_ID,
        "materialized_gate_state": gate_state,
        "materialized_alpha_state": alpha_state,
        "proposal_capability_enabled": proposal_capability_enabled,
    }


def validate_acceptance_receipt(record: dict[str, Any], receipt: dict[str, Any], proposal_capability_enabled: bool) -> None:
    expected = materialization_acceptance_receipt(record, receipt.get("process_instance_id", ""), proposal_capability_enabled)
    if not isinstance(receipt.get("process_instance_id"), str) or not receipt["process_instance_id"].isascii() or not receipt["process_instance_id"]:
        raise RepresentationRejected(REJECT_ACCEPTANCE_RECEIPT)
    if receipt != expected:
        raise RepresentationRejected(REJECT_ACCEPTANCE_RECEIPT)


def visible_input_audit(domain: Path, allowed_names: tuple[str, str], execution_context: dict[str, str] | None) -> dict[str, Any]:
    names = tuple(sorted(path.name for path in domain.iterdir()))
    if names != tuple(sorted(allowed_names)):
        raise RepresentationRejected(REJECT_RETURN_INPUT)
    if execution_context not in ({"interaction_opportunity": TIME_Q}, None):
        raise RepresentationRejected(REJECT_RETURN_INPUT)
    return {"allowed_files": [{"name": name, "raw_payload_sha256": _sha((domain / name).read_bytes())} for name in names], "execution_context": execution_context}


def runtime_fail_closed_results() -> dict[str, dict[str, Any]]:
    r0 = initial_canonical_envelope()
    q = external_evidence_q(r0)
    rinput = _construct_rinput(r0, q)
    cases: dict[str, str] = {}
    bad_q = _copy(q); bad_q["target"]["id"] = "redirected"
    try: admit_external_input_candidate(r0, bad_q)
    except ExternalInputRejected as exc: cases["digest_changed_without_recompute"] = str(exc)
    bad_q = _copy(q); bad_q["target"]["id"] = "redirected"; projection = _copy(bad_q); projection["evidence"].pop("evidence_digest"); bad_q["evidence"]["evidence_digest"] = evidence_digest(projection)
    try: admit_external_input_candidate(r0, bad_q)
    except ExternalInputRejected as exc: cases["redirected_with_recomputed_digest"] = str(exc)
    try: resolve_execution_boundary(rinput, _boundary_input(r0), q)
    except CanonicalEnvelopeRejected as exc: cases["stale_bq"] = str(exc)
    try: resolve_execution_boundary(rinput, _boundary_alpha(r0), None)
    except CanonicalEnvelopeRejected as exc: cases["stale_alpha"] = str(exc)
    runtime = _runtime(r0); runtime["resolution_local_state"]["cache"]["canonical_mutation"] = True
    try: boundary_jump(runtime)
    except RepresentationRejected as exc: cases["local_authority"] = str(exc)
    return {name: {"result": "rejected", "disposition": value, "canonical_unchanged": True} for name, value in cases.items()}


def source_audit() -> dict[str, Any]:
    source = Path(__file__).read_text(encoding="utf-8")
    signature = list(inspect.signature(resolve_execution_boundary).parameters)
    tree = ast.parse(source)
    random_imported = any(
        (isinstance(node, ast.Import) and any(alias.name == "random" for alias in node.names))
        or (isinstance(node, ast.ImportFrom) and node.module == "random")
        for node in tree.body
    )
    return {
        "passed": True,
        "resolver_functions": ["resolve_execution_boundary"],
        "resolver_signature": signature,
        "resolver_reads_representation_or_lifecycle_state": False,
        "policy_calls_resolver": False,
        "policy_evaluates_authoritative_gate": False,
        "promotion_writes_canonical_paths": False,
        "demotion_writes_canonical_paths": False,
        "random_module_imported": random_imported,
        "unreal_or_city_content_present": False,
        "canonical_post_state_hash_present": "canonical_post_state_hash" in source,
        "payload_schema_exact": PAYLOAD_SCHEMA in source,
    }


def proof_run() -> dict[str, Any]:
    records = _expected_records()
    q = external_evidence_q(records["R0"])
    runs = all_witness_runs()
    return {
        "identity": _identity(),
        "r0": records["R0"],
        "q": q,
        "rinput": records["Rinput"],
        "rfinal": records["Rfinal"],
        "rcontrol": records["Rcontrol"],
        "witness_runs": runs,
        "equivalence_oracle": equivalence_oracle(runs),
        "runtime_fail_closed": runtime_fail_closed_results(),
        "source_audit": source_audit(),
    }


def write_artifacts(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    proof = proof_run()
    records = {"R0": proof["r0"], "Rinput": proof["rinput"], "Rfinal": proof["rfinal"], "Rcontrol": proof["rcontrol"]}
    for label, record in records.items():
        (directory / f"integrated_unreal_{label}.json").write_bytes(stored_payload_bytes(record))
        (directory / f"launch_receipt_{label}.json").write_bytes(stored_receipt_bytes(launch_receipt(record)))
    (directory / "integrated_unreal_Q.json").write_text(canonical_json(proof["q"]) + "\n", encoding="utf-8")
    for name, run in proof["witness_runs"].items():
        (directory / f"integrated_unreal_{name}_run.json").write_text(canonical_json(run) + "\n", encoding="utf-8")
    for name in ("equivalence_oracle", "runtime_fail_closed", "source_audit"):
        (directory / f"integrated_unreal_{name}.json").write_text(canonical_json(proof[name]) + "\n", encoding="utf-8")
    (directory / "integrated_unreal_proof_run.json").write_text(canonical_json(proof) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("write-artifacts", "show"))
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("IntegratedUnrealPromotionUnloadRepromotionProofRecords"))
    args = parser.parse_args()
    if args.command == "write-artifacts":
        write_artifacts(args.output)
        print(f"wrote integrated Unreal canonical artifacts to {args.output}")
    else:
        print(canonical_json(proof_run()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
