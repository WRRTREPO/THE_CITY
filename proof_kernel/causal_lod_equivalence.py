"""Canonical-only Causal-LOD equivalence proof.

The module has one resolver.  Dense inspection and boundary jump affect only
resolution-local representation before that resolver is called at the same
canonical boundary.
"""

from __future__ import annotations

import argparse
import copy
import inspect
import sys
from pathlib import Path
from typing import Any

from kernel import canonical_json, state_hash


RECORD_SCHEMA = "CanonicalResolutionEnvelope.v1"
PAYLOAD_SCHEMA = "CausalLodEquivalencePayload.v1"
SCENARIO_ID = "causal-lod-equivalence-v1"
SCENARIO_VERSION = "0.1.0"
SIMULATION_VERSION = "0.7.0-draft.34"
SEED = "causal-lod-equivalence-v1/0001"

COMMITMENT_ID = "commitment_alpha"
RESERVATION_ID = "reservation_alpha"
DECISION_TIME = "t1/00"
DUE_WORK_ID = "t1/00/equivalence/commitment_alpha.resolve"
NO_BOUNDARY = {"decision_time": None, "due_work_ids": []}

REJECT_POLICY_AUTHORITY = "resolution_policy_rejected.authoritative_mutation_detected"
REJECT_GATE_CACHE = "resolution_policy_rejected.authoritative_gate_cache_detected"
REJECT_PROMOTION_AUTHORITY = "resolution_policy_rejected.promotion_authority_detected"
REJECT_DEMOTION_LOSS = "resolution_policy_rejected.demotion_authority_loss_detected"
REJECT_BOUNDARY_SKIP = "resolution_policy_rejected.boundary_skip_detected"


class CanonicalEnvelopeRejected(ValueError):
    """Raised when canonical state does not satisfy this exact payload schema."""


class ResolutionPolicyRejected(ValueError):
    """Raised when local runtime state tries to carry canonical authority."""


def _copy(value: Any) -> Any:
    return copy.deepcopy(value)


def canonical_hash(canonical_envelope: dict[str, Any]) -> str:
    """The singular authority hash covers only the canonical envelope."""

    return state_hash(canonical_envelope)


def initial_canonical_envelope() -> dict[str, Any]:
    """Return the exact neutral R0 fixture."""

    return {
        "identity": {
            "record_schema": RECORD_SCHEMA,
            "payload_schema": PAYLOAD_SCHEMA,
            "scenario_id": SCENARIO_ID,
            "scenario_version": SCENARIO_VERSION,
            "simulation_version": SIMULATION_VERSION,
            "seed": SEED,
        },
        "current_causal_state": {
            "durable_facts": {"substrate_marker": "stable", "commitment_alpha_outcome": "pending"},
            "gate_relevant_state": {"substrate_marker": "stable"},
            "active_commitments": {
                COMMITMENT_ID: {
                    "owner": "process_alpha",
                    "state": "active",
                    "gate_check_at": DECISION_TIME,
                    "required_gate": "substrate_marker == stable",
                    "reservation_id": RESERVATION_ID,
                    "terminal_disposition": "release_unit_alpha_on_success",
                }
            },
            "resource_ownership": {
                "unit_alpha": {
                    "state": "reserved",
                    "reservation_id": RESERVATION_ID,
                    "owner_commitment_id": COMMITMENT_ID,
                }
            },
            "accepted_external_inputs": [],
        },
        "future_causal_state": {
            "canonical_clock": "t0/00",
            "scheduled_consequential_decisions": [
                {"decision_time": DECISION_TIME, "due_work_ids": [DUE_WORK_ID]}
            ],
            "commitment_gate_check_schedule": {COMMITMENT_ID: DECISION_TIME},
            "canonical_execution_keys": [DUE_WORK_ID],
        },
        "causal_provenance": {
            "canonical_ancestry": {"parent_record_hash": None, "boundary_derivation": "initial_record"},
            "fixture_genesis": {
                "established_facts": [
                    "active_commitments.commitment_alpha = active",
                    "resource_ownership.unit_alpha = reserved_by:reservation_alpha",
                ],
                "resources": ["unit_alpha starts reserved by reservation_alpha"],
            },
            "authoritative_causal_ledger": [],
            "terminal_resource_dispositions": {RESERVATION_ID: "release_unit_alpha_on_success"},
        },
    }


def _r0_ledger_entry(r0: dict[str, Any]) -> dict[str, Any]:
    r0_hash = canonical_hash(r0)
    return {
        "decision_time": DECISION_TIME,
        "canonical_execution_key": DUE_WORK_ID,
        "actor": "process_alpha",
        "commitment_id": COMMITMENT_ID,
        "action_id": "resolve",
        "parent_record_hash": r0_hash,
        "transaction_pre_state_hash": r0_hash,
        "observed_inputs": {"substrate_marker": "stable"},
        "believed_inputs": {"substrate_marker": "stable"},
        "gates": [{"name": "substrate_marker == stable", "value": "stable", "passed": True}],
        "result": "accepted",
        "mutations": [
            "future_causal_state.canonical_clock = t1/00",
            "active_commitments.commitment_alpha.state = succeeded",
            "durable_facts.commitment_alpha_outcome = succeeded",
            "resource_ownership.unit_alpha = available",
            "future_causal_state.scheduled_consequential_decisions = []",
        ],
        "resources": ["release unit_alpha", "terminal disposition: release_unit_alpha_on_success"],
        "terminal_disposition": "release_unit_alpha_on_success",
    }


def _expected_r1(r0: dict[str, Any]) -> dict[str, Any]:
    """Build the only lawful R1 from byte-identical R0 authority."""

    r1 = _copy(r0)
    r1["current_causal_state"]["durable_facts"]["commitment_alpha_outcome"] = "succeeded"
    r1["current_causal_state"]["active_commitments"][COMMITMENT_ID]["state"] = "succeeded"
    r1["current_causal_state"]["resource_ownership"]["unit_alpha"] = {
        "state": "available",
        "reservation_id": None,
        "owner_commitment_id": None,
    }
    r1["future_causal_state"] = {
        "canonical_clock": DECISION_TIME,
        "scheduled_consequential_decisions": [],
        "commitment_gate_check_schedule": {},
        "canonical_execution_keys": [],
    }
    r1["causal_provenance"]["canonical_ancestry"] = {
        "parent_record_hash": canonical_hash(r0),
        "boundary_derivation": "next_consequential_boundary",
    }
    r1["causal_provenance"]["authoritative_causal_ledger"] = [_r0_ledger_entry(r0)]
    return r1


def validate_r0(canonical_envelope: dict[str, Any]) -> list[str]:
    """R0 is an exact payload, not an extensible object."""

    expected = initial_canonical_envelope()
    if canonical_json(canonical_envelope) == canonical_json(expected):
        return []
    return ["CausalLodEquivalencePayload.v1.R0_exact"]


def validate_r1(canonical_envelope: dict[str, Any]) -> list[str]:
    """R1 is the exact result of the one t1/00 resolver transaction."""

    expected = _expected_r1(initial_canonical_envelope())
    if canonical_json(canonical_envelope) == canonical_json(expected):
        return []
    return ["CausalLodEquivalencePayload.v1.R1_exact"]


def validate_canonical_envelope(canonical_envelope: dict[str, Any]) -> list[str]:
    errors = validate_r0(canonical_envelope)
    if not errors:
        return []
    errors = validate_r1(canonical_envelope)
    if not errors:
        return []
    return ["CausalLodEquivalencePayload.v1.exact_authoritative_schema_required"]


def _require_r0(canonical_envelope: dict[str, Any]) -> None:
    errors = validate_r0(canonical_envelope)
    if errors:
        raise CanonicalEnvelopeRejected(",".join(errors))


def next_consequential_boundary(canonical_envelope: dict[str, Any]) -> dict[str, Any]:
    """Discover due canonical work from the envelope alone."""

    if not validate_r0(canonical_envelope):
        return {"decision_time": DECISION_TIME, "due_work_ids": [DUE_WORK_ID]}
    if not validate_r1(canonical_envelope):
        return _copy(NO_BOUNDARY)
    raise CanonicalEnvelopeRejected("CausalLodEquivalencePayload.v1.exact_authoritative_schema_required")


def resolve_next_due(canonical_envelope: dict[str, Any], canonical_boundary: dict[str, Any]) -> dict[str, Any]:
    """Atomically advance R0 to R1 at the one canonical t1/00 boundary."""

    _require_r0(canonical_envelope)
    expected_boundary = next_consequential_boundary(canonical_envelope)
    if canonical_json(canonical_boundary) != canonical_json(expected_boundary):
        raise CanonicalEnvelopeRejected("canonical_boundary_mismatch")
    r1 = _expected_r1(canonical_envelope)
    if validate_r1(r1):
        raise AssertionError("resolver failed to construct the frozen R1 payload")
    return r1


def authoritative_projection(runtime_envelope: dict[str, Any]) -> dict[str, Any]:
    if set(runtime_envelope) != {"canonical_envelope", "resolution_local_state", "resolution_trace"}:
        raise ResolutionPolicyRejected("runtime_envelope_paths_invalid")
    envelope = runtime_envelope.get("canonical_envelope")
    if not isinstance(envelope, dict):
        raise ResolutionPolicyRejected("runtime_envelope_missing_canonical_envelope")
    return _copy(envelope)


def _empty_local(profile: str = "minimal") -> dict[str, Any]:
    return {"profile": profile, "cache": {}, "samples": [], "diagnostics": []}


def minimal_runtime(canonical_envelope: dict[str, Any]) -> dict[str, Any]:
    _require_r0(canonical_envelope)
    return {
        "canonical_envelope": _copy(canonical_envelope),
        "resolution_local_state": _empty_local(),
        "resolution_trace": [],
    }


def _find_prohibited_local_authority(value: Any) -> bool:
    forbidden_keys = {"authoritative_gate_result", "resolver_input", "canonical_mutation", "canonical_boundary_override"}
    if isinstance(value, dict):
        return any(key in forbidden_keys or _find_prohibited_local_authority(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_find_prohibited_local_authority(item) for item in value)
    return False


def _require_clean_runtime(runtime_envelope: dict[str, Any]) -> None:
    canonical_envelope = authoritative_projection(runtime_envelope)
    _require_r0(canonical_envelope)
    local = runtime_envelope.get("resolution_local_state")
    trace = runtime_envelope.get("resolution_trace")
    if not isinstance(local, dict) or set(local) != {"profile", "cache", "samples", "diagnostics"}:
        raise ResolutionPolicyRejected("resolution_local_state_paths_invalid")
    if not isinstance(trace, list):
        raise ResolutionPolicyRejected("resolution_trace_type_invalid")
    if _find_prohibited_local_authority(local) or _find_prohibited_local_authority(trace):
        raise ResolutionPolicyRejected(REJECT_GATE_CACHE)


def dense_inspection(runtime_envelope: dict[str, Any], sample_position: str) -> dict[str, Any]:
    """Derive one local display sample without evaluating a canonical gate."""

    _require_clean_runtime(runtime_envelope)
    if sample_position not in {"t0/15", "t0/30", "t0/45"}:
        raise ResolutionPolicyRejected("dense_sample_position_invalid")
    runtime = _copy(runtime_envelope)
    state = runtime["resolution_local_state"]
    source = runtime["canonical_envelope"]["current_causal_state"]
    state["profile"] = "dense"
    state["samples"].append(
        {
            "sample_position": sample_position,
            "display_snapshot": {
                "substrate_marker": source["durable_facts"]["substrate_marker"],
                "commitment_state": source["active_commitments"][COMMITMENT_ID]["state"],
            },
        }
    )
    state["diagnostics"].append("dense_sample_derived_from_canonical_envelope")
    runtime["resolution_trace"].append({"policy": "dense_inspection", "sample_position": sample_position})
    return runtime


def boundary_jump(runtime_envelope: dict[str, Any]) -> dict[str, Any]:
    """Record that no intermediate local sample is represented."""

    _require_clean_runtime(runtime_envelope)
    runtime = _copy(runtime_envelope)
    runtime["resolution_local_state"]["profile"] = "boundary_jump"
    runtime["resolution_local_state"]["diagnostics"].append("boundary_jump_no_intermediate_sample")
    runtime["resolution_trace"].append({"policy": "boundary_jump", "sample_count": 0})
    return runtime


def promote(runtime_envelope: dict[str, Any]) -> dict[str, Any]:
    """Increase local representation without changing canonical authority."""

    _require_clean_runtime(runtime_envelope)
    runtime = _copy(runtime_envelope)
    canonical_envelope = runtime["canonical_envelope"]
    runtime["resolution_local_state"]["profile"] = "promoted"
    runtime["resolution_local_state"]["cache"] = {
        COMMITMENT_ID: {
            "next_boundary_display": next_consequential_boundary(canonical_envelope),
            "reservation_display": canonical_envelope["current_causal_state"]["active_commitments"][COMMITMENT_ID]["reservation_id"],
        }
    }
    runtime["resolution_local_state"]["diagnostics"].append("promotion_derived_from_canonical_envelope")
    runtime["resolution_trace"].append({"policy": "promotion"})
    return runtime


def demote(runtime_envelope: dict[str, Any]) -> dict[str, Any]:
    """Discard all local representation while retaining canonical authority."""

    _require_clean_runtime(runtime_envelope)
    runtime = _copy(runtime_envelope)
    runtime["resolution_local_state"] = _empty_local("demoted")
    runtime["resolution_local_state"]["diagnostics"] = ["local_state_discarded"]
    runtime["resolution_trace"].append({"policy": "demotion"})
    return runtime


def finish_at_next_boundary(runtime_envelope: dict[str, Any]) -> dict[str, Any]:
    """Call the sole resolver using only the runtime's canonical projection."""

    _require_clean_runtime(runtime_envelope)
    runtime = _copy(runtime_envelope)
    canonical_envelope = authoritative_projection(runtime)
    boundary = next_consequential_boundary(canonical_envelope)
    runtime["canonical_envelope"] = resolve_next_due(canonical_envelope, boundary)
    runtime["resolution_trace"].append({"resolver": "resolve_next_due", "decision_time": DECISION_TIME})
    return runtime


def _rejection(disposition: str) -> dict[str, Any]:
    return {
        "result": "rejected",
        "disposition": disposition,
        "authoritative_causal_ledger_appended": False,
        "future_schedule_created": False,
    }


def assess_dense_transition(before: dict[str, Any], candidate_runtime: dict[str, Any]) -> dict[str, Any]:
    try:
        after = authoritative_projection(candidate_runtime)
    except ResolutionPolicyRejected:
        return _rejection(REJECT_POLICY_AUTHORITY)
    if canonical_json(before) != canonical_json(after):
        return _rejection(REJECT_POLICY_AUTHORITY)
    try:
        _require_clean_runtime(candidate_runtime)
    except ResolutionPolicyRejected as error:
        return _rejection(str(error))
    return {"result": "accepted", "disposition": "resolution_policy_accepted.dense_local_only"}


def assess_promotion_transition(before: dict[str, Any], candidate_runtime: dict[str, Any]) -> dict[str, Any]:
    try:
        after = authoritative_projection(candidate_runtime)
    except ResolutionPolicyRejected:
        return _rejection(REJECT_PROMOTION_AUTHORITY)
    if canonical_json(before) != canonical_json(after):
        return _rejection(REJECT_PROMOTION_AUTHORITY)
    return {"result": "accepted", "disposition": "resolution_policy_accepted.promotion_neutral"}


def assess_demotion_transition(before: dict[str, Any], candidate_runtime: dict[str, Any]) -> dict[str, Any]:
    try:
        after = authoritative_projection(candidate_runtime)
    except ResolutionPolicyRejected:
        return _rejection(REJECT_DEMOTION_LOSS)
    if canonical_json(before) != canonical_json(after):
        return _rejection(REJECT_DEMOTION_LOSS)
    return {"result": "accepted", "disposition": "resolution_policy_accepted.demotion_neutral"}


def assess_boundary_jump(canonical_envelope: dict[str, Any], proposed_boundary: dict[str, Any]) -> dict[str, Any]:
    expected = next_consequential_boundary(canonical_envelope)
    if canonical_json(proposed_boundary) != canonical_json(expected):
        return _rejection(REJECT_BOUNDARY_SKIP)
    return {"result": "accepted", "disposition": "resolution_policy_accepted.boundary_identity"}


def _run_result(runtime: dict[str, Any]) -> dict[str, Any]:
    r1 = authoritative_projection(runtime)
    entry = r1["causal_provenance"]["authoritative_causal_ledger"][0]
    return {
        "r0": initial_canonical_envelope(),
        "final_canonical_envelope": r1,
        "final_canonical_hash": canonical_hash(r1),
        "transaction": {
            "header": {
                "decision_time": DECISION_TIME,
                "parent_record_hash": entry["parent_record_hash"],
                "transaction_pre_state_hash": entry["transaction_pre_state_hash"],
                "boundary_derivation": "next_consequential_boundary",
            },
            "ledger": _copy(r1["causal_provenance"]["authoritative_causal_ledger"]),
        },
        "next_consequential_boundary": next_consequential_boundary(r1),
        "resolution_local_state": _copy(runtime["resolution_local_state"]),
        "diagnostic_resolution_trace": _copy(runtime["resolution_trace"]),
    }


def dense_throughout_run() -> dict[str, Any]:
    runtime = minimal_runtime(initial_canonical_envelope())
    for sample_position in ("t0/15", "t0/30", "t0/45"):
        runtime = dense_inspection(runtime, sample_position)
    return _run_result(finish_at_next_boundary(runtime))


def boundary_jump_throughout_run() -> dict[str, Any]:
    runtime = boundary_jump(minimal_runtime(initial_canonical_envelope()))
    return _run_result(finish_at_next_boundary(runtime))


def boundary_jump_promote_dense_run() -> dict[str, Any]:
    runtime = boundary_jump(minimal_runtime(initial_canonical_envelope()))
    runtime = promote(runtime)
    for sample_position in ("t0/30", "t0/45"):
        runtime = dense_inspection(runtime, sample_position)
    return _run_result(finish_at_next_boundary(runtime))


def dense_demote_boundary_jump_promote_dense_run() -> dict[str, Any]:
    runtime = dense_inspection(minimal_runtime(initial_canonical_envelope()), "t0/15")
    runtime = demote(runtime)
    runtime = boundary_jump(runtime)
    runtime = promote(runtime)
    runtime = dense_inspection(runtime, "t0/45")
    return _run_result(finish_at_next_boundary(runtime))


def all_witness_runs() -> dict[str, dict[str, Any]]:
    return {
        "dense_throughout": dense_throughout_run(),
        "boundary_jump_throughout": boundary_jump_throughout_run(),
        "boundary_jump_promote_dense": boundary_jump_promote_dense_run(),
        "dense_demote_boundary_jump_promote_dense": dense_demote_boundary_jump_promote_dense_run(),
    }


def equivalence_oracle(runs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Compare finished witness outputs without mutating or concealing them."""

    reference_name = "dense_throughout"
    reference = runs[reference_name]
    failures: list[dict[str, str]] = []
    comparisons = (
        ("final_canonical_envelope_differs", "final_canonical_envelope"),
        ("canonical_hash_differs", "final_canonical_hash"),
        ("authoritative_ledger_differs", "transaction"),
        ("next_consequential_boundary_differs", "next_consequential_boundary"),
    )
    for name, run in runs.items():
        if name == reference_name:
            continue
        for failure, key in comparisons:
            if canonical_json(run[key]) != canonical_json(reference[key]):
                failures.append({"witness": name, "failure": failure})
        header = run["transaction"]["header"]
        reference_header = reference["transaction"]["header"]
        for failure, key in (
            ("parent_record_hash_differs", "parent_record_hash"),
            ("transaction_pre_state_hash_differs", "transaction_pre_state_hash"),
        ):
            if header[key] != reference_header[key]:
                failures.append({"witness": name, "failure": failure})
        final = run["final_canonical_envelope"]
        reference_final = reference["final_canonical_envelope"]
        if final["current_causal_state"]["active_commitments"] != reference_final["current_causal_state"]["active_commitments"]:
            failures.append({"witness": name, "failure": "terminal_commitment_or_resource_disposition_differs"})
        if final["current_causal_state"]["resource_ownership"] != reference_final["current_causal_state"]["resource_ownership"]:
            failures.append({"witness": name, "failure": "terminal_commitment_or_resource_disposition_differs"})
        if final["future_causal_state"] != reference_final["future_causal_state"]:
            failures.append({"witness": name, "failure": "future_schedule_differs"})
    return {
        "result": "accepted" if not failures else "equivalence_failure",
        "reference_witness": reference_name,
        "failures": failures,
    }


def runtime_fail_closed_results() -> dict[str, Any]:
    r0 = initial_canonical_envelope()

    clock_mutation = minimal_runtime(r0)
    clock_mutation["canonical_envelope"]["future_causal_state"]["canonical_clock"] = "t0/15"

    cached_gate = minimal_runtime(r0)
    cached_gate["resolution_local_state"]["cache"] = {"authoritative_gate_result": True}

    promotion_authority = promote(minimal_runtime(r0))
    promotion_authority["canonical_envelope"]["current_causal_state"]["durable_facts"]["local_sample"] = "leaked"

    demotion_loss = promote(minimal_runtime(r0))
    del demotion_loss["canonical_envelope"]["future_causal_state"]["scheduled_consequential_decisions"]

    return {
        "dense_mutates_canonical_clock": assess_dense_transition(r0, clock_mutation),
        "sample_caches_authoritative_gate": assess_dense_transition(r0, cached_gate),
        "promotion_carries_authority": assess_promotion_transition(r0, promotion_authority),
        "demotion_loses_authority": assess_demotion_transition(r0, demotion_loss),
        "boundary_jump_skips_due_work": assess_boundary_jump(r0, _copy(NO_BOUNDARY)),
    }


def source_audit() -> dict[str, Any]:
    """Report the structural isolation that output equivalence alone cannot show."""

    resolver_source = inspect.getsource(resolve_next_due)
    policy_source = inspect.getsource(dense_inspection) + inspect.getsource(boundary_jump)
    transition_source = inspect.getsource(promote) + inspect.getsource(demote)
    machine_source = (
        inspect.getsource(initial_canonical_envelope)
        + resolver_source
        + policy_source
        + transition_source
        + inspect.getsource(finish_at_next_boundary)
    )
    resolver_functions = sorted(
        name for name, value in inspect.getmembers(sys.modules[__name__]) if callable(value) and name.startswith("resolve_")
    )
    return {
        "resolver_functions": resolver_functions,
        "resolver_signature": list(inspect.signature(resolve_next_due).parameters),
        "resolver_reads_policy_local_state_or_trace": any(
            token in resolver_source for token in ("policy", "resolution_local_state", "resolution_trace", "runtime_envelope")
        ),
        "policy_calls_resolver": "resolve_next_due" in policy_source,
        "policy_can_override_boundary": "canonical_boundary" in policy_source,
        "policy_evaluates_authoritative_gate": "required_gate" in policy_source or "passed" in policy_source,
        "transitions_write_canonical_paths": any(
            token in transition_source
            for token in ('["canonical_envelope"] =', '["current_causal_state"] =', '["future_causal_state"] =', '["causal_provenance"] =')
        ),
        "random_module_imported": "import random" in machine_source or "from random" in machine_source,
        "unreal_or_city_content_present": any(token in machine_source.lower() for token in ("unreal", "faction", "gang", "police", "fire")),
        "payload_schema_exact": "PAYLOAD_SCHEMA" in inspect.getsource(initial_canonical_envelope)
        and "_require_r0(canonical_envelope)" in inspect.getsource(resolve_next_due)
        and "validate_r0" in inspect.getsource(_require_r0),
    }


def proof_run() -> dict[str, Any]:
    runs = all_witness_runs()
    return {
        "proof_identity": {
            "record_schema": RECORD_SCHEMA,
            "payload_schema": PAYLOAD_SCHEMA,
            "scenario_id": SCENARIO_ID,
            "scenario_version": SCENARIO_VERSION,
            "simulation_version": SIMULATION_VERSION,
        },
        "r0_canonical_hash": canonical_hash(initial_canonical_envelope()),
        "witness_runs": runs,
        "equivalence_oracle": equivalence_oracle(runs),
        "runtime_fail_closed": runtime_fail_closed_results(),
        "source_audit": source_audit(),
    }


def _write_json(path: Path, value: Any) -> None:
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def write_artifacts(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    run = proof_run()
    _write_json(directory / "causal_lod_equivalence_R0.json", initial_canonical_envelope())
    for name, witness in run["witness_runs"].items():
        _write_json(directory / f"causal_lod_equivalence_{name}_run.json", witness)
    _write_json(directory / "causal_lod_equivalence_oracle.json", run["equivalence_oracle"])
    _write_json(directory / "causal_lod_equivalence_runtime_fail_closed.json", run["runtime_fail_closed"])
    _write_json(directory / "causal_lod_equivalence_source_audit.json", run["source_audit"])
    _write_json(directory / "causal_lod_equivalence_proof_run.json", run)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_artifacts(args.output)
    print(f"wrote Causal-LOD equivalence artifacts to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
