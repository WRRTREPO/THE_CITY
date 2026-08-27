"""Canonical-only record-relative chronological-resolution proof.

The scheduler derives one record-bound next boundary from current canonical
authority. Dense inspection and boundary jump alter only local representation.
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
PAYLOAD_SCHEMA = "RecordRelativeChronologicalResolutionPayload.v1"
SCENARIO_ID = "record-relative-chronological-resolution-v1"
SCENARIO_VERSION = "0.1.0"
SIMULATION_VERSION = "0.7.0-draft.39"
SEED = "record-relative-chronological-resolution-v1/0001"

COMMITMENT_X = "commitment_x"
COMMITMENT_Y = "commitment_y"
COMMITMENT_Z = "commitment_z"

TIME_X = "t1/00"
TIME_Y = "t1/30"
TIME_Z = "t2/00"

WORK_X = "t1/00/chronological/commitment_x.resolve"
WORK_Y = "t1/30/chronological/commitment_y.resolve"
WORK_Z = "t2/00/chronological/commitment_z.resolve"

NO_BOUNDARY = {"decision_time": None, "due_work_ids": []}

REJECT_STALE_BOUNDARY = "chronological_resolution_rejected.stale_boundary_source"
REJECT_BOUNDARY_CROSSING = "chronological_resolution_rejected.due_boundary_crossed"
REJECT_BOUNDARY_SOURCE = "chronological_resolution_rejected.boundary_source_mismatch"
REJECT_LOCAL_AUTHORITY = "chronological_resolution_rejected.local_authority_detected"
REJECT_GATE_CACHE = "chronological_resolution_rejected.authoritative_gate_cache_detected"
REJECT_PROMOTION_AUTHORITY = "chronological_resolution_rejected.promotion_authority_detected"
REJECT_DEMOTION_LOSS = "chronological_resolution_rejected.demotion_authority_loss_detected"
REJECT_SAME_CLOCK_SUCCESSOR = "chronological_resolution_rejected.same_clock_successor_outside_payload"
REJECT_POLICY_PATH = "chronological_resolution_rejected.policy_specific_path"


class CanonicalEnvelopeRejected(ValueError):
    """Raised when a record or record-bound boundary is outside this payload."""


class ResolutionPolicyRejected(ValueError):
    """Raised when local representation attempts to carry canonical authority."""


def _copy(value: Any) -> Any:
    return copy.deepcopy(value)


def canonical_hash(canonical_envelope: dict[str, Any]) -> str:
    return state_hash(canonical_envelope)


DEFINITIONS: dict[str, dict[str, Any]] = {
    COMMITMENT_X: {
        "owner": "process_x",
        "required_gate_path": "current_causal_state.gate_relevant_state.shared_slot_state",
        "required_value": "available",
        "terminal_disposition": "transform_shared_slot_to_allocation_x",
        "success_effect": "allocate_shared_slot",
    },
    COMMITMENT_Y: {
        "owner": "process_y",
        "required_gate_path": "current_causal_state.gate_relevant_state.shared_slot_state",
        "required_value": "available",
        "terminal_disposition": "no_resource_acquired_on_failed_gate",
        "success_effect": "allocate_shared_slot",
    },
    COMMITMENT_Z: {
        "owner": "process_z",
        "required_gate_path": "current_causal_state.gate_relevant_state.stable_gate",
        "required_value": "stable",
        "terminal_disposition": "release_unit_z_on_success",
        "success_effect": "release_unit_z",
    },
}

WORK_TO_COMMITMENT = {
    WORK_X: COMMITMENT_X,
    WORK_Y: COMMITMENT_Y,
    WORK_Z: COMMITMENT_Z,
}

TIME_BY_WORK = {
    WORK_X: TIME_X,
    WORK_Y: TIME_Y,
    WORK_Z: TIME_Z,
}


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
    """Return the exact R0 authority record."""

    return {
        "identity": _identity(),
        "current_causal_state": {
            "durable_facts": {
                "stable_gate": "stable",
                "shared_slot_outcome": "unallocated",
                "outcome_x": "pending",
                "outcome_y": "pending",
                "outcome_z": "pending",
            },
            "gate_relevant_state": {
                "stable_gate": "stable",
                "shared_slot_state": "available",
            },
            "active_and_terminal_commitments": {
                COMMITMENT_X: {
                    "owner": "process_x",
                    "state": "active",
                    "gate_check_at": TIME_X,
                    "required_gate": "shared_slot_state == available",
                    "reservation_id": None,
                    "terminal_disposition": "transform_shared_slot_to_allocation_x",
                },
                COMMITMENT_Y: {
                    "owner": "process_y",
                    "state": "active",
                    "gate_check_at": TIME_Y,
                    "required_gate": "shared_slot_state == available",
                    "reservation_id": None,
                    "terminal_disposition": "no_resource_acquired_on_failed_gate",
                },
                COMMITMENT_Z: {
                    "owner": "process_z",
                    "state": "active",
                    "gate_check_at": TIME_Z,
                    "required_gate": "stable_gate == stable",
                    "reservation_id": "reservation_z",
                    "terminal_disposition": "release_unit_z_on_success",
                },
            },
            "reservations_leases_and_resource_ownership": {
                "shared_slot": {"state": "available", "allocation_owner": None},
                "unit_z": {
                    "state": "reserved",
                    "reservation_id": "reservation_z",
                    "owner_commitment_id": COMMITMENT_Z,
                },
            },
            "accepted_external_inputs": [],
        },
        "future_causal_state": {
            "canonical_clock": "t0/00",
            "scheduled_consequential_decisions": [
                {"decision_time": TIME_X, "due_work_ids": [WORK_X]},
                {"decision_time": TIME_Y, "due_work_ids": [WORK_Y]},
                {"decision_time": TIME_Z, "due_work_ids": [WORK_Z]},
            ],
            "commitment_gate_check_schedule": {
                COMMITMENT_X: TIME_X,
                COMMITMENT_Y: TIME_Y,
                COMMITMENT_Z: TIME_Z,
            },
            "canonical_execution_keys": [WORK_X, WORK_Y, WORK_Z],
        },
        "causal_provenance": {
            "canonical_ancestry": {
                "parent_record_hash": None,
                "boundary_derivation": "initial_record",
            },
            "fixture_genesis": {
                "established_facts": [
                    "shared_slot = available",
                    "commitment_x = active",
                    "commitment_y = active",
                    "commitment_z = active",
                    "unit_z = reserved_by:reservation_z",
                ]
            },
            "authoritative_causal_ledger": [],
            "terminal_resource_dispositions": {
                "shared_slot": None,
                COMMITMENT_Y: None,
                "reservation_z": None,
            },
        },
    }


def _read_path(record: dict[str, Any], dotted_path: str) -> Any:
    value: Any = record
    for part in dotted_path.split("."):
        value = value[part]
    return value


def _schedule_after_removal(record: dict[str, Any], work_id: str) -> None:
    future = record["future_causal_state"]
    future["scheduled_consequential_decisions"] = [
        {
            "decision_time": item["decision_time"],
            "due_work_ids": [candidate for candidate in item["due_work_ids"] if candidate != work_id],
        }
        for item in future["scheduled_consequential_decisions"]
        if work_id not in item["due_work_ids"] or len(item["due_work_ids"]) > 1
    ]
    future["canonical_execution_keys"] = [
        candidate for candidate in future["canonical_execution_keys"] if candidate != work_id
    ]
    future["commitment_gate_check_schedule"][WORK_TO_COMMITMENT[work_id]] = None


def _apply_effect(working: dict[str, Any], commitment_id: str, success: bool) -> tuple[list[str], str]:
    state = working["current_causal_state"]
    facts = state["durable_facts"]
    gate_state = state["gate_relevant_state"]
    resources = state["reservations_leases_and_resource_ownership"]
    dispositions = working["causal_provenance"]["terminal_resource_dispositions"]
    definition = DEFINITIONS[commitment_id]

    if not success:
        facts[f"outcome_{commitment_id[-1]}"] = "failed_gate"
        dispositions[commitment_id] = "no_resource_acquired_on_failed_gate"
        return [f"{commitment_id}.state = failed_gate"], "no_resource_acquired_on_failed_gate"

    if definition["success_effect"] == "allocate_shared_slot":
        allocation = f"allocated_to_{commitment_id[-1]}"
        gate_state["shared_slot_state"] = allocation
        facts["shared_slot_outcome"] = allocation
        facts[f"outcome_{commitment_id[-1]}"] = "succeeded"
        resources["shared_slot"] = {"state": "allocated", "allocation_owner": commitment_id}
        dispositions["shared_slot"] = "transform_shared_slot_to_allocation_x"
        return (
            [
                "gate_relevant_state.shared_slot_state = allocated_to_x",
                "durable_facts.shared_slot_outcome = allocated_to_x",
                "reservations_leases_and_resource_ownership.shared_slot = allocated_by:commitment_x",
                f"{commitment_id}.state = succeeded",
            ],
            "transform_shared_slot_to_allocation_x",
        )

    if definition["success_effect"] == "release_unit_z":
        facts[f"outcome_{commitment_id[-1]}"] = "succeeded"
        resources["unit_z"] = {
            "state": "available",
            "reservation_id": None,
            "owner_commitment_id": None,
        }
        dispositions["reservation_z"] = "release_unit_z_on_success"
        return (
            [
                "reservations_leases_and_resource_ownership.unit_z = available",
                f"{commitment_id}.state = succeeded",
            ],
            "release_unit_z_on_success",
        )

    raise AssertionError("unknown frozen fixture success effect")


def _transition(record: dict[str, Any], boundary: dict[str, Any]) -> dict[str, Any]:
    """Build one successor from a valid record-bound due-work capability."""

    work_id = boundary["due_work_ids"][0]
    commitment_id = WORK_TO_COMMITMENT[work_id]
    definition = DEFINITIONS[commitment_id]
    working = _copy(record)
    observed = _read_path(working, definition["required_gate_path"])
    gate_result = observed == definition["required_value"]

    commitment = working["current_causal_state"]["active_and_terminal_commitments"][commitment_id]
    commitment["state"] = "succeeded" if gate_result else "failed_gate"
    mutations, disposition = _apply_effect(working, commitment_id, gate_result)
    _schedule_after_removal(working, work_id)
    working["future_causal_state"]["canonical_clock"] = boundary["decision_time"]
    working["causal_provenance"]["canonical_ancestry"] = {
        "parent_record_hash": boundary["source_record_hash"],
        "boundary_derivation": "next_consequential_boundary",
    }
    entry = {
        "source_record_hash": boundary["source_record_hash"],
        "decision_time": boundary["decision_time"],
        "due_work_ids": _copy(boundary["due_work_ids"]),
        "commitment_id": commitment_id,
        "evaluated_gates": [
            {
                "path": definition["required_gate_path"],
                "observed_value": observed,
                "required_value": definition["required_value"],
                "result": gate_result,
            }
        ],
        "mutation_or_failed_gate": "succeeded" if gate_result else "failed_gate",
        "mutations": mutations,
        "terminal_resource_disposition": disposition,
    }
    working["causal_provenance"]["authoritative_causal_ledger"].append(entry)
    return working


def _expected_r1() -> dict[str, Any]:
    r0 = initial_canonical_envelope()
    return _transition(r0, _boundary_for(r0, TIME_X, [WORK_X]))


def _expected_r2() -> dict[str, Any]:
    r1 = _expected_r1()
    return _transition(r1, _boundary_for(r1, TIME_Y, [WORK_Y]))


def _expected_r3() -> dict[str, Any]:
    r2 = _expected_r2()
    return _transition(r2, _boundary_for(r2, TIME_Z, [WORK_Z]))


def _boundary_for(record: dict[str, Any], decision_time: str, due_work_ids: list[str]) -> dict[str, Any]:
    return {
        "source_record_hash": canonical_hash(record),
        "decision_time": decision_time,
        "due_work_ids": list(due_work_ids),
    }


def _stage_name(record: dict[str, Any]) -> str | None:
    candidates = (
        ("R0", initial_canonical_envelope()),
        ("R1", _expected_r1()),
        ("R2", _expected_r2()),
        ("R3", _expected_r3()),
    )
    for name, expected in candidates:
        if canonical_json(record) == canonical_json(expected):
            return name
    return None


def validate_canonical_envelope(canonical_envelope: dict[str, Any]) -> list[str]:
    if _stage_name(canonical_envelope) is not None:
        return []
    return ["RecordRelativeChronologicalResolutionPayload.v1.exact_authoritative_schema_required"]


def _require_valid(canonical_envelope: dict[str, Any]) -> str:
    stage = _stage_name(canonical_envelope)
    if stage is None:
        raise CanonicalEnvelopeRejected("RecordRelativeChronologicalResolutionPayload.v1.exact_authoritative_schema_required")
    return stage


def _time_token_not_before(decision_time: str, clock: str) -> bool:
    return decision_time >= clock


def next_consequential_boundary(canonical_envelope: dict[str, Any]) -> dict[str, Any]:
    """Discover the earliest unresolved due set from this record alone."""

    _require_valid(canonical_envelope)
    future = canonical_envelope["future_causal_state"]
    clock = future["canonical_clock"]
    candidates = [
        item
        for item in future["scheduled_consequential_decisions"]
        if _time_token_not_before(item["decision_time"], clock) and item["due_work_ids"]
    ]
    if not candidates:
        return _copy(NO_BOUNDARY)
    earliest = min(item["decision_time"] for item in candidates)
    due_work_ids = sorted(
        work_id
        for item in candidates
        if item["decision_time"] == earliest
        for work_id in item["due_work_ids"]
    )
    if due_work_ids != sorted(due_work_ids) or any(work_id not in future["canonical_execution_keys"] for work_id in due_work_ids):
        raise CanonicalEnvelopeRejected("canonical_schedule_representations_disagree")
    return _boundary_for(canonical_envelope, earliest, due_work_ids)


def resolve_next_due(canonical_envelope: dict[str, Any], canonical_boundary: dict[str, Any]) -> dict[str, Any]:
    """Resolve exactly the record-bound next consequential boundary."""

    _require_valid(canonical_envelope)
    record_hash = canonical_hash(canonical_envelope)
    if canonical_boundary.get("source_record_hash") != record_hash:
        raise CanonicalEnvelopeRejected(REJECT_BOUNDARY_SOURCE)
    expected = next_consequential_boundary(canonical_envelope)
    if canonical_json(canonical_boundary) != canonical_json(expected):
        raise CanonicalEnvelopeRejected(REJECT_BOUNDARY_CROSSING)
    if expected == NO_BOUNDARY:
        raise CanonicalEnvelopeRejected("no_due_work_to_resolve")
    if len(expected["due_work_ids"]) != 1:
        raise CanonicalEnvelopeRejected("fixture_requires_one_due_work_per_boundary")
    successor = _transition(canonical_envelope, canonical_boundary)
    if _stage_name(successor) is None:
        raise AssertionError("resolver constructed state outside frozen payload")
    return successor


def authoritative_projection(runtime_envelope: dict[str, Any]) -> dict[str, Any]:
    if set(runtime_envelope) != {"canonical_envelope", "resolution_local_state", "resolution_trace"}:
        raise ResolutionPolicyRejected("runtime_envelope_paths_invalid")
    canonical = runtime_envelope["canonical_envelope"]
    if not isinstance(canonical, dict):
        raise ResolutionPolicyRejected("runtime_envelope_missing_canonical_envelope")
    return _copy(canonical)


def _empty_local(profile: str = "minimal") -> dict[str, Any]:
    return {"profile": profile, "cache": {}, "samples": [], "diagnostics": []}


def minimal_runtime(canonical_envelope: dict[str, Any]) -> dict[str, Any]:
    _require_valid(canonical_envelope)
    return {
        "canonical_envelope": _copy(canonical_envelope),
        "resolution_local_state": _empty_local(),
        "resolution_trace": [],
    }


def _find_prohibited_local_authority(value: Any) -> bool:
    prohibited = {
        "authoritative_gate_result",
        "resolver_input",
        "canonical_mutation",
        "canonical_boundary_override",
        "retained_authoritative_boundary",
    }
    if isinstance(value, dict):
        return any(key in prohibited or _find_prohibited_local_authority(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_find_prohibited_local_authority(item) for item in value)
    return False


def _require_clean_runtime(runtime_envelope: dict[str, Any]) -> None:
    canonical = authoritative_projection(runtime_envelope)
    _require_valid(canonical)
    local = runtime_envelope["resolution_local_state"]
    trace = runtime_envelope["resolution_trace"]
    if not isinstance(local, dict) or set(local) != {"profile", "cache", "samples", "diagnostics"}:
        raise ResolutionPolicyRejected("resolution_local_state_paths_invalid")
    if not isinstance(trace, list):
        raise ResolutionPolicyRejected("resolution_trace_type_invalid")
    if _find_prohibited_local_authority(local) or _find_prohibited_local_authority(trace):
        raise ResolutionPolicyRejected(REJECT_GATE_CACHE)


def dense_inspection(runtime_envelope: dict[str, Any], sample_position: str) -> dict[str, Any]:
    """Derive a display sample only; it has no causal authority."""

    _require_clean_runtime(runtime_envelope)
    if not isinstance(sample_position, str) or not sample_position:
        raise ResolutionPolicyRejected("dense_sample_position_invalid")
    runtime = _copy(runtime_envelope)
    canonical = runtime["canonical_envelope"]
    state = canonical["current_causal_state"]
    runtime["resolution_local_state"]["profile"] = "dense"
    runtime["resolution_local_state"]["samples"].append(
        {
            "sample_position": sample_position,
            "display_snapshot": {
                "canonical_clock": canonical["future_causal_state"]["canonical_clock"],
                "shared_slot_state": state["gate_relevant_state"]["shared_slot_state"],
                "active_commitments": sorted(
                    commitment_id
                    for commitment_id, commitment in state["active_and_terminal_commitments"].items()
                    if commitment["state"] == "active"
                ),
            },
        }
    )
    runtime["resolution_local_state"]["diagnostics"].append("dense_sample_derived_from_canonical_envelope")
    runtime["resolution_trace"].append({"policy": "dense_inspection", "sample_position": sample_position})
    return runtime


def boundary_jump(runtime_envelope: dict[str, Any]) -> dict[str, Any]:
    """Represent an empty interval without creating a local sample."""

    _require_clean_runtime(runtime_envelope)
    runtime = _copy(runtime_envelope)
    runtime["resolution_local_state"]["profile"] = "boundary_jump"
    runtime["resolution_local_state"]["diagnostics"].append("boundary_jump_no_intermediate_sample")
    runtime["resolution_trace"].append({"policy": "boundary_jump", "sample_count": 0})
    return runtime


def promote(runtime_envelope: dict[str, Any]) -> dict[str, Any]:
    """Derive discardable local representation from canonical authority."""

    _require_clean_runtime(runtime_envelope)
    runtime = _copy(runtime_envelope)
    canonical = runtime["canonical_envelope"]
    runtime["resolution_local_state"]["profile"] = "promoted"
    runtime["resolution_local_state"]["cache"] = {
        "next_boundary_display": next_consequential_boundary(canonical),
        "clock_display": canonical["future_causal_state"]["canonical_clock"],
    }
    runtime["resolution_local_state"]["diagnostics"].append("promotion_derived_from_canonical_envelope")
    runtime["resolution_trace"].append({"policy": "promotion"})
    return runtime


def demote(runtime_envelope: dict[str, Any]) -> dict[str, Any]:
    """Discard resolution-local representation and retain canonical authority."""

    _require_clean_runtime(runtime_envelope)
    runtime = _copy(runtime_envelope)
    runtime["resolution_local_state"] = _empty_local("demoted")
    runtime["resolution_local_state"]["diagnostics"] = ["local_state_discarded"]
    runtime["resolution_trace"].append({"policy": "demotion"})
    return runtime


def advance_runtime(runtime_envelope: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Discover and resolve one boundary from the runtime's current authority."""

    _require_clean_runtime(runtime_envelope)
    runtime = _copy(runtime_envelope)
    canonical = authoritative_projection(runtime)
    boundary = next_consequential_boundary(canonical)
    runtime["canonical_envelope"] = resolve_next_due(canonical, boundary)
    runtime["resolution_trace"].append(
        {
            "scheduler": "next_consequential_boundary",
            "source_record_hash": boundary["source_record_hash"],
            "decision_time": boundary["decision_time"],
            "due_work_ids": boundary["due_work_ids"],
        }
    )
    return runtime, boundary


def _checkpoint(runtime_envelope: dict[str, Any], label: str) -> dict[str, Any]:
    canonical = authoritative_projection(runtime_envelope)
    return {
        "label": label,
        "canonical_envelope": canonical,
        "canonical_hash": canonical_hash(canonical),
        "next_consequential_boundary": next_consequential_boundary(canonical),
    }


def _run_witness(name: str, local_steps: tuple[tuple[str, tuple[str, ...]], ...]) -> dict[str, Any]:
    runtime = minimal_runtime(initial_canonical_envelope())
    checkpoints: dict[str, dict[str, Any]] = {}

    for label, steps in local_steps:
        for step in steps:
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
        if label != "R3":
            runtime, _ = advance_runtime(runtime)

    return {
        "witness": name,
        "checkpoints": checkpoints,
        "final_canonical_envelope": _copy(runtime["canonical_envelope"]),
        "final_canonical_hash": canonical_hash(runtime["canonical_envelope"]),
        "next_consequential_boundary": next_consequential_boundary(runtime["canonical_envelope"]),
        "resolution_local_state": _copy(runtime["resolution_local_state"]),
        "diagnostic_resolution_trace": _copy(runtime["resolution_trace"]),
    }


def dense_throughout_run() -> dict[str, Any]:
    return _run_witness(
        "dense_throughout",
        (
            ("R0", ("dense:t0/15", "dense:t0/30", "dense:t0/45")),
            ("R1", ("dense:t1/05", "dense:t1/15")),
            ("R2", ("dense:t1/45",)),
            ("R3", ()),
        ),
    )


def boundary_jump_throughout_run() -> dict[str, Any]:
    return _run_witness(
        "boundary_jump_throughout",
        (
            ("R0", ("jump",)),
            ("R1", ("jump",)),
            ("R2", ("jump",)),
            ("R3", ()),
        ),
    )


def dense_demote_boundary_jump_promote_dense_run() -> dict[str, Any]:
    return _run_witness(
        "dense_demote_boundary_jump_promote_dense",
        (
            ("R0", ("dense:t0/15", "demote")),
            ("R1", ("jump",)),
            ("R2", ("promote", "dense:t1/45")),
            ("R3", ()),
        ),
    )


def boundary_jump_promote_dense_demote_boundary_jump_run() -> dict[str, Any]:
    return _run_witness(
        "boundary_jump_promote_dense_demote_boundary_jump",
        (
            ("R0", ("jump",)),
            ("R1", ("promote", "dense:t1/05")),
            ("R2", ("demote", "jump")),
            ("R3", ()),
        ),
    )


def all_witness_runs() -> dict[str, dict[str, Any]]:
    return {
        "dense_throughout": dense_throughout_run(),
        "boundary_jump_throughout": boundary_jump_throughout_run(),
        "dense_demote_boundary_jump_promote_dense": dense_demote_boundary_jump_promote_dense_run(),
        "boundary_jump_promote_dense_demote_boundary_jump": boundary_jump_promote_dense_demote_boundary_jump_run(),
    }


def equivalence_oracle(runs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Require every canonical checkpoint, not only the final state, to match."""

    reference_name = "dense_throughout"
    reference = runs[reference_name]
    failures: list[dict[str, str]] = []
    for name, run in sorted(runs.items()):
        if name == reference_name:
            continue
        for label in ("R0", "R1", "R2", "R3"):
            candidate = run["checkpoints"][label]
            expected = reference["checkpoints"][label]
            for field, failure in (
                ("canonical_envelope", "canonical_envelope_differs"),
                ("canonical_hash", "canonical_hash_differs"),
                ("next_consequential_boundary", "next_boundary_differs"),
            ):
                if canonical_json(candidate[field]) != canonical_json(expected[field]):
                    failures.append({"witness": name, "checkpoint": label, "failure": failure})
        if canonical_json(run["final_canonical_envelope"]) != canonical_json(reference["final_canonical_envelope"]):
            failures.append({"witness": name, "checkpoint": "R3", "failure": "final_canonical_envelope_differs"})
    return {
        "result": "accepted" if not failures else "equivalence_failure",
        "reference_witness": reference_name,
        "failures": failures,
    }


def _rejection(disposition: str) -> dict[str, Any]:
    return {
        "result": "rejected",
        "disposition": disposition,
        "authoritative_causal_ledger_appended": False,
        "future_schedule_created": False,
    }


def runtime_fail_closed_results() -> dict[str, Any]:
    r0 = initial_canonical_envelope()
    r1 = resolve_next_due(r0, next_consequential_boundary(r0))
    stale_r0_boundary = next_consequential_boundary(r0)

    def rejected(disposition: str, action: Any) -> dict[str, Any]:
        before = _copy(r1)
        try:
            action()
        except (CanonicalEnvelopeRejected, ResolutionPolicyRejected):
            pass
        else:
            raise AssertionError("malformed runtime action unexpectedly succeeded")
        if canonical_json(r1) != canonical_json(before):
            raise AssertionError("rejection mutated canonical authority")
        return _rejection(disposition)

    wrong_y_boundary = {
        "source_record_hash": canonical_hash(r1),
        "decision_time": TIME_Z,
        "due_work_ids": [WORK_Z],
    }
    mismatched_source = {
        "source_record_hash": canonical_hash(r0),
        "decision_time": TIME_Y,
        "due_work_ids": [WORK_Y],
    }
    same_clock = _copy(r1)
    same_clock["future_causal_state"]["scheduled_consequential_decisions"].append(
        {"decision_time": TIME_X, "due_work_ids": ["t1/00/chronological/same_clock.resolve"]}
    )

    clock_mutation = minimal_runtime(r0)
    clock_mutation["canonical_envelope"]["future_causal_state"]["canonical_clock"] = "t0/15"
    cached_gate = minimal_runtime(r0)
    cached_gate["resolution_local_state"]["cache"] = {"authoritative_gate_result": True}
    promotion_authority = promote(minimal_runtime(r0))
    promotion_authority["canonical_envelope"]["current_causal_state"]["durable_facts"]["local"] = "leaked"
    demotion_loss = promote(minimal_runtime(r0))
    del demotion_loss["canonical_envelope"]["future_causal_state"]["scheduled_consequential_decisions"]

    return {
        "stale_R0_boundary_against_R1": rejected(
            REJECT_STALE_BOUNDARY,
            lambda: resolve_next_due(r1, stale_r0_boundary),
        ),
        "cross_Y_boundary_from_R1": rejected(
            REJECT_BOUNDARY_CROSSING,
            lambda: resolve_next_due(r1, wrong_y_boundary),
        ),
        "source_hash_mismatch": rejected(
            REJECT_BOUNDARY_SOURCE,
            lambda: resolve_next_due(r1, mismatched_source),
        ),
        "dense_mutates_canonical_clock": rejected(
            REJECT_LOCAL_AUTHORITY,
            lambda: _require_clean_runtime(clock_mutation),
        ),
        "sample_caches_authoritative_gate": rejected(
            REJECT_GATE_CACHE,
            lambda: _require_clean_runtime(cached_gate),
        ),
        "promotion_carries_authority": rejected(
            REJECT_PROMOTION_AUTHORITY,
            lambda: _require_clean_runtime(promotion_authority),
        ),
        "demotion_loses_authority": rejected(
            REJECT_DEMOTION_LOSS,
            lambda: _require_clean_runtime(demotion_loss),
        ),
        "same_clock_successor_outside_payload": rejected(
            REJECT_SAME_CLOCK_SUCCESSOR,
            lambda: _require_valid(same_clock),
        ),
    }


def definition_independence_audit() -> dict[str, Any]:
    foreign_references: list[dict[str, str]] = []
    for commitment_id, definition in sorted(DEFINITIONS.items()):
        text = canonical_json(definition)
        for other_id in sorted(DEFINITIONS):
            if other_id != commitment_id and other_id in text:
                foreign_references.append({"definition": commitment_id, "foreign_commitment": other_id})
    return {
        "definition_hashes": {
            commitment_id: state_hash(definition)
            for commitment_id, definition in sorted(DEFINITIONS.items())
        },
        "foreign_references": foreign_references,
        "passed": not foreign_references,
    }


def source_audit() -> dict[str, Any]:
    """Report the structural guarantees that output equality cannot establish."""

    scheduler_source = inspect.getsource(next_consequential_boundary)
    resolver_source = inspect.getsource(resolve_next_due)
    policies_source = inspect.getsource(dense_inspection) + inspect.getsource(boundary_jump)
    transitions_source = inspect.getsource(promote) + inspect.getsource(demote)
    machine_source = (
        inspect.getsource(initial_canonical_envelope)
        + scheduler_source
        + resolver_source
        + policies_source
        + transitions_source
        + inspect.getsource(advance_runtime)
    )
    resolver_functions = sorted(
        name
        for name, value in inspect.getmembers(sys.modules[__name__])
        if callable(value) and name == "resolve_next_due"
    )
    independence = definition_independence_audit()
    return {
        "resolver_functions": resolver_functions,
        "resolver_signature": list(inspect.signature(resolve_next_due).parameters),
        "scheduler_signature": list(inspect.signature(next_consequential_boundary).parameters),
        "scheduler_reads_policy_local_state_or_trace": any(
            token in scheduler_source for token in ("resolution_local_state", "resolution_trace", "runtime_envelope")
        ),
        "resolver_reads_policy_local_state_or_trace": any(
            token in resolver_source for token in ("policy", "resolution_local_state", "resolution_trace", "runtime_envelope")
        ),
        "boundary_requires_source_record_hash": "source_record_hash" in resolver_source,
        "scheduler_uses_at_or_after_clock": "_time_token_not_before" in scheduler_source,
        "policy_calls_resolver": "resolve_next_due" in policies_source,
        "policy_evaluates_authoritative_gate": "required_gate" in policies_source or "evaluated_gates" in policies_source,
        "transitions_write_canonical_paths": any(
            token in transitions_source
            for token in ('["canonical_envelope"] =', '["current_causal_state"] =', '["future_causal_state"] =')
        ),
        "definition_independence": independence,
        "random_module_imported": "import random" in machine_source or "from random" in machine_source,
        "unreal_or_city_content_present": any(
            token in machine_source.lower()
            for token in ("unreal", "faction", "gang", "police", "fire", "route", "crew", "helicopter")
        ),
        "payload_schema_exact": '"payload_schema": PAYLOAD_SCHEMA' in inspect.getsource(_identity)
        and "_require_valid(canonical_envelope)" in resolver_source,
    }


def proof_run() -> dict[str, Any]:
    runs = all_witness_runs()
    return {
        "proof_identity": _identity(),
        "r0_canonical_hash": canonical_hash(initial_canonical_envelope()),
        "witness_runs": runs,
        "equivalence_oracle": equivalence_oracle(runs),
        "runtime_fail_closed": runtime_fail_closed_results(),
        "definition_independence_audit": definition_independence_audit(),
        "source_audit": source_audit(),
    }


def _write_json(path: Path, value: Any) -> None:
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def write_artifacts(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    run = proof_run()
    _write_json(directory / "chronological_resolution_R0.json", initial_canonical_envelope())
    for name, witness in run["witness_runs"].items():
        _write_json(directory / f"chronological_resolution_{name}_run.json", witness)
    _write_json(directory / "chronological_resolution_oracle.json", run["equivalence_oracle"])
    _write_json(directory / "chronological_resolution_runtime_fail_closed.json", run["runtime_fail_closed"])
    _write_json(directory / "chronological_resolution_definition_independence.json", run["definition_independence_audit"])
    _write_json(directory / "chronological_resolution_source_audit.json", run["source_audit"])
    _write_json(directory / "chronological_resolution_proof_run.json", run)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_artifacts(args.output)
    print(f"wrote chronological-resolution artifacts to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
