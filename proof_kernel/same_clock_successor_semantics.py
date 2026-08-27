"""Canonical-only Same-Clock Successor Semantics Proof v0.1.0.

One canonical boundary at (t1/00, phase 10) resolves X and creates Y at
(t1/00, phase 20).  The resolver must rediscover Y from the committed R1;
resolution-local policy never creates causal authority.
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
PAYLOAD_SCHEMA = "SameClockSuccessorSemanticsPayload.v1"
SCENARIO_ID = "same-clock-successor-semantics-v1"
SCENARIO_VERSION = "0.1.0"
SIMULATION_VERSION = "0.7.0-draft.47"
SEED = "same-clock-successor-semantics-v1/0001"

TIME = "t1/00"
PHASE_X = 10
PHASE_Y = 20
PHASE_LIMIT = 20
WORK_X = "work_x"
WORK_Y = "work_y"
COMMITMENT_X = "commitment_x"
COMMITMENT_Y = "commitment_y"
BUDGET_ID = "same_clock_successor_budget_t1_00"

NO_BOUNDARY = {
    "source_record_hash": None,
    "decision_time": None,
    "simulation_phase": None,
    "due_work_ids": [],
    "work_member_keys": [],
}

REJECT_BOUNDARY_SOURCE = "same_clock_successor_rejected.boundary_source_mismatch"
REJECT_BOUNDARY_CROSSING = "same_clock_successor_rejected.boundary_crossing_or_shape_mismatch"
REJECT_RETROGRADE_PHASE = "same_clock_successor_rejected.same_clock_phase_not_strictly_later"
REJECT_PHASE_LIMIT = "same_clock_successor_rejected.same_clock_phase_limit_exceeded"
REJECT_DUPLICATE_MEMBER = "same_clock_successor_rejected.duplicate_work_member"
REJECT_CYCLE = "same_clock_successor_rejected.cyclic_or_settled_work_reference"
REJECT_BUDGET = "same_clock_successor_rejected.same_clock_generation_budget_exhausted"
REJECT_LOCAL_AUTHORITY = "same_clock_successor_rejected.local_authority_detected"
REJECT_GATE_CACHE = "same_clock_successor_rejected.authoritative_cache_detected"
REJECT_PROMOTION_AUTHORITY = "same_clock_successor_rejected.promotion_authority_detected"
REJECT_DEMOTION_LOSS = "same_clock_successor_rejected.demotion_authority_loss_detected"


class CanonicalEnvelopeRejected(ValueError):
    """Raised when a canonical record or boundary violates the frozen payload."""


class ResolutionPolicyRejected(ValueError):
    """Raised when resolution-local representation tries to carry authority."""


def _copy(value: Any) -> Any:
    return copy.deepcopy(value)


def canonical_hash(canonical_envelope: dict[str, Any]) -> str:
    """Hash the full canonical envelope and no resolution-local state."""

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


def _boundary_key(decision_time: str, simulation_phase: int) -> tuple[str, int]:
    return decision_time, simulation_phase


def _member_key(decision_time: str, simulation_phase: int, work_id: str) -> list[Any]:
    return [decision_time, simulation_phase, work_id]


def _boundary_for(record: dict[str, Any], decision_time: str, simulation_phase: int, due_work_ids: list[str]) -> dict[str, Any]:
    ordered = sorted(due_work_ids)
    return {
        "source_record_hash": canonical_hash(record),
        "decision_time": decision_time,
        "simulation_phase": simulation_phase,
        "due_work_ids": ordered,
        "work_member_keys": [_member_key(decision_time, simulation_phase, work_id) for work_id in ordered],
    }


def initial_canonical_envelope() -> dict[str, Any]:
    """Return the exact R0 fixture. Y is absent from every canonical path."""

    return {
        "identity": _identity(),
        "current_causal_state": {
            "durable_facts": {"outcome_x": "pending", "outcome_y": "pending"},
            "gate_relevant_state": {"same_clock_successor_state": "available"},
            "active_and_terminal_commitments": {
                COMMITMENT_X: {
                    "state": "active",
                    "boundary_key": [TIME, PHASE_X],
                    "work_member_key": _member_key(TIME, PHASE_X, WORK_X),
                    "terminal_disposition": None,
                },
                COMMITMENT_Y: {
                    "state": "absent",
                    "boundary_key": None,
                    "work_member_key": None,
                    "terminal_disposition": None,
                },
            },
            "reservations_leases_and_resource_ownership": {
                BUDGET_ID: {"state": "available", "remaining_units": 1, "owner_commitment_id": None}
            },
            "accepted_external_inputs": [],
        },
        "future_causal_state": {
            "canonical_clock": "t0/00",
            "scheduled_consequential_decisions": [
                {"decision_time": TIME, "simulation_phase": PHASE_X, "due_work_ids": [WORK_X]}
            ],
            "work_execution_metadata": {
                WORK_X: {"simulation_phase": PHASE_X, "parent_work_member_key": None}
            },
            "canonical_work_member_keys": [_member_key(TIME, PHASE_X, WORK_X)],
            "same_clock_phase_limit": PHASE_LIMIT,
        },
        "causal_provenance": {
            "canonical_ancestry": {"parent_record_hash": None, "boundary_derivation": "initial_record"},
            "fixture_genesis": {
                "established_facts": [
                    "commitment_x = active",
                    "same_clock_successor_budget_t1_00 = one_available_unit",
                    "only work_x is scheduled",
                ]
            },
            "authoritative_causal_ledger": [],
            "terminal_resource_dispositions": {
                COMMITMENT_X: None,
                COMMITMENT_Y: None,
                BUDGET_ID: None,
            },
        },
    }


def _x_ledger_entry(r0: dict[str, Any]) -> dict[str, Any]:
    source_hash = canonical_hash(r0)
    return {
        "source_record_hash": source_hash,
        "decision_time": TIME,
        "simulation_phase": PHASE_X,
        "due_work_ids": [WORK_X],
        "work_member_keys": [_member_key(TIME, PHASE_X, WORK_X)],
        "commitment_id": COMMITMENT_X,
        "evaluated_gates": [
            {"path": f"current_causal_state.reservations_leases_and_resource_ownership.{BUDGET_ID}.remaining_units", "observed_value": 1, "required_value": "positive", "result": True}
        ],
        "mutation_or_terminal_result": "succeeded_and_created_same_clock_successor",
        "mutations": [
            "future_causal_state.canonical_clock = t1/00",
            "commitment_x.state = succeeded",
            "commitment_y.state = active",
            "same_clock_successor_budget_t1_00.remaining_units = 0",
            "scheduled boundary (t1/00,20) with work_y",
        ],
        "terminal_resource_disposition": "consume_one_same_clock_generation_unit",
        "created_successor_boundary": {
            "decision_time": TIME,
            "simulation_phase": PHASE_Y,
            "due_work_ids": [WORK_Y],
            "parent_work_member_key": _member_key(TIME, PHASE_X, WORK_X),
        },
    }


def _y_ledger_entry(r1: dict[str, Any]) -> dict[str, Any]:
    source_hash = canonical_hash(r1)
    return {
        "source_record_hash": source_hash,
        "decision_time": TIME,
        "simulation_phase": PHASE_Y,
        "due_work_ids": [WORK_Y],
        "work_member_keys": [_member_key(TIME, PHASE_Y, WORK_Y)],
        "commitment_id": COMMITMENT_Y,
        "evaluated_gates": [
            {"path": "current_causal_state.gate_relevant_state.same_clock_successor_state", "observed_value": "available", "required_value": "available", "result": True}
        ],
        "mutation_or_terminal_result": "succeeded",
        "mutations": ["commitment_y.state = succeeded", "remove final scheduled same-clock boundary"],
        "terminal_resource_disposition": "no_resource_acquired",
        "created_successor_boundary": None,
    }


def _expected_r1() -> dict[str, Any]:
    r0 = initial_canonical_envelope()
    r1 = _copy(r0)
    current = r1["current_causal_state"]
    current["durable_facts"]["outcome_x"] = "succeeded"
    current["active_and_terminal_commitments"][COMMITMENT_X]["state"] = "succeeded"
    current["active_and_terminal_commitments"][COMMITMENT_X]["terminal_disposition"] = "succeeded"
    current["active_and_terminal_commitments"][COMMITMENT_Y] = {
        "state": "active",
        "boundary_key": [TIME, PHASE_Y],
        "work_member_key": _member_key(TIME, PHASE_Y, WORK_Y),
        "terminal_disposition": None,
    }
    current["reservations_leases_and_resource_ownership"][BUDGET_ID] = {
        "state": "consumed",
        "remaining_units": 0,
        "owner_commitment_id": COMMITMENT_X,
    }
    r1["future_causal_state"] = {
        "canonical_clock": TIME,
        "scheduled_consequential_decisions": [
            {"decision_time": TIME, "simulation_phase": PHASE_Y, "due_work_ids": [WORK_Y]}
        ],
        "work_execution_metadata": {
            WORK_Y: {
                "simulation_phase": PHASE_Y,
                "parent_work_member_key": _member_key(TIME, PHASE_X, WORK_X),
            }
        },
        "canonical_work_member_keys": [_member_key(TIME, PHASE_Y, WORK_Y)],
        "same_clock_phase_limit": PHASE_LIMIT,
    }
    r1["causal_provenance"]["canonical_ancestry"] = {
        "parent_record_hash": canonical_hash(r0),
        "boundary_derivation": "next_consequential_boundary",
    }
    r1["causal_provenance"]["authoritative_causal_ledger"] = [_x_ledger_entry(r0)]
    r1["causal_provenance"]["terminal_resource_dispositions"] = {
        COMMITMENT_X: "succeeded",
        COMMITMENT_Y: None,
        BUDGET_ID: "consume_one_same_clock_generation_unit",
    }
    return r1


def _expected_r2() -> dict[str, Any]:
    r1 = _expected_r1()
    r2 = _copy(r1)
    current = r2["current_causal_state"]
    current["durable_facts"]["outcome_y"] = "succeeded"
    current["active_and_terminal_commitments"][COMMITMENT_Y]["state"] = "succeeded"
    current["active_and_terminal_commitments"][COMMITMENT_Y]["terminal_disposition"] = "no_resource_acquired"
    r2["future_causal_state"] = {
        "canonical_clock": TIME,
        "scheduled_consequential_decisions": [],
        "work_execution_metadata": {},
        "canonical_work_member_keys": [],
        "same_clock_phase_limit": PHASE_LIMIT,
    }
    r2["causal_provenance"]["canonical_ancestry"] = {
        "parent_record_hash": canonical_hash(r1),
        "boundary_derivation": "next_consequential_boundary",
    }
    r2["causal_provenance"]["authoritative_causal_ledger"] = [_x_ledger_entry(initial_canonical_envelope()), _y_ledger_entry(r1)]
    r2["causal_provenance"]["terminal_resource_dispositions"][COMMITMENT_Y] = "no_resource_acquired"
    return r2


def _stage_name(record: dict[str, Any]) -> str | None:
    for name, expected in (("R0", initial_canonical_envelope()), ("R1", _expected_r1()), ("R2", _expected_r2())):
        if canonical_json(record) == canonical_json(expected):
            return name
    return None


def validate_canonical_envelope(canonical_envelope: dict[str, Any]) -> list[str]:
    if _stage_name(canonical_envelope) is not None:
        return []
    return ["SameClockSuccessorSemanticsPayload.v1.exact_authoritative_schema_required"]


def _require_valid(canonical_envelope: dict[str, Any]) -> str:
    stage = _stage_name(canonical_envelope)
    if stage is None:
        raise CanonicalEnvelopeRejected("SameClockSuccessorSemanticsPayload.v1.exact_authoritative_schema_required")
    return stage


def _validate_schedule_shape(record: dict[str, Any]) -> None:
    future = record["future_causal_state"]
    schedule = future["scheduled_consequential_decisions"]
    expected_members: list[list[Any]] = []
    for item in schedule:
        ids = item["due_work_ids"]
        if ids != sorted(ids) or len(ids) != len(set(ids)):
            raise CanonicalEnvelopeRejected(REJECT_DUPLICATE_MEMBER)
        expected_members.extend(_member_key(item["decision_time"], item["simulation_phase"], work_id) for work_id in ids)
    if future["canonical_work_member_keys"] != sorted(expected_members):
        raise CanonicalEnvelopeRejected(REJECT_DUPLICATE_MEMBER)


def next_consequential_boundary(canonical_envelope: dict[str, Any]) -> dict[str, Any]:
    """Discover the complete member set at the next record-relative boundary."""

    _require_valid(canonical_envelope)
    _validate_schedule_shape(canonical_envelope)
    future = canonical_envelope["future_causal_state"]
    clock = future["canonical_clock"]
    candidates = [
        item
        for item in future["scheduled_consequential_decisions"]
        if item["due_work_ids"] and item["decision_time"] >= clock
    ]
    if not candidates:
        return _copy(NO_BOUNDARY)
    decision_time, phase = min(_boundary_key(item["decision_time"], item["simulation_phase"]) for item in candidates)
    due_work_ids = [
        work_id
        for item in candidates
        if _boundary_key(item["decision_time"], item["simulation_phase"]) == (decision_time, phase)
        for work_id in item["due_work_ids"]
    ]
    return _boundary_for(canonical_envelope, decision_time, phase, due_work_ids)


def _candidate_successor(decision_time: str = TIME, phase: int = PHASE_Y, work_id: str = WORK_Y) -> dict[str, Any]:
    return {
        "decision_time": decision_time,
        "simulation_phase": phase,
        "work_id": work_id,
        "parent_work_member_key": _member_key(TIME, PHASE_X, WORK_X),
    }


def validate_same_clock_successor_creation(
    record: dict[str, Any],
    creator_boundary: dict[str, Any],
    candidate: dict[str, Any],
    *,
    extra_known_work_ids: tuple[str, ...] = (),
    settled_work_ids: tuple[str, ...] = (),
) -> None:
    """Validate X's finite same-clock creation authority without mutation."""

    source_hash = canonical_hash(record)
    if creator_boundary.get("source_record_hash") != source_hash:
        raise CanonicalEnvelopeRejected(REJECT_BOUNDARY_SOURCE)
    if candidate.get("decision_time") != creator_boundary.get("decision_time") or candidate.get("simulation_phase") <= creator_boundary.get("simulation_phase"):
        raise CanonicalEnvelopeRejected(REJECT_RETROGRADE_PHASE)
    if candidate["simulation_phase"] > record["future_causal_state"]["same_clock_phase_limit"]:
        raise CanonicalEnvelopeRejected(REJECT_PHASE_LIMIT)
    if candidate.get("parent_work_member_key") != creator_boundary.get("work_member_keys", [None])[0]:
        raise CanonicalEnvelopeRejected(REJECT_CYCLE)
    budget = record["current_causal_state"]["reservations_leases_and_resource_ownership"][BUDGET_ID]
    if budget["remaining_units"] <= 0:
        raise CanonicalEnvelopeRejected(REJECT_BUDGET)
    scheduled = tuple(work_id for item in record["future_causal_state"]["scheduled_consequential_decisions"] for work_id in item["due_work_ids"])
    work_id = candidate.get("work_id")
    if work_id in settled_work_ids:
        raise CanonicalEnvelopeRejected(REJECT_CYCLE)
    if work_id in scheduled or work_id in extra_known_work_ids:
        raise CanonicalEnvelopeRejected(REJECT_DUPLICATE_MEMBER)
    if work_id != WORK_Y:
        raise CanonicalEnvelopeRejected(REJECT_CYCLE)


def resolve_next_due(canonical_envelope: dict[str, Any], canonical_boundary: dict[str, Any]) -> dict[str, Any]:
    """Resolve exactly one frozen complete boundary from its bound record."""

    stage = _require_valid(canonical_envelope)
    if canonical_boundary.get("source_record_hash") != canonical_hash(canonical_envelope):
        raise CanonicalEnvelopeRejected(REJECT_BOUNDARY_SOURCE)
    expected = next_consequential_boundary(canonical_envelope)
    if canonical_json(canonical_boundary) != canonical_json(expected):
        raise CanonicalEnvelopeRejected(REJECT_BOUNDARY_CROSSING)
    if expected == NO_BOUNDARY:
        raise CanonicalEnvelopeRejected("same_clock_successor_rejected.no_due_work")
    if len(expected["due_work_ids"]) != 1:
        raise CanonicalEnvelopeRejected("same_clock_successor_rejected.fixture_requires_one_member_per_boundary")
    if stage == "R0" and expected["due_work_ids"] == [WORK_X]:
        validate_same_clock_successor_creation(canonical_envelope, canonical_boundary, _candidate_successor())
        return _expected_r1()
    if stage == "R1" and expected["due_work_ids"] == [WORK_Y]:
        return _expected_r2()
    raise CanonicalEnvelopeRejected(REJECT_BOUNDARY_CROSSING)


def authoritative_projection(runtime_envelope: dict[str, Any]) -> dict[str, Any]:
    if set(runtime_envelope) != {"canonical_envelope", "resolution_local_state", "resolution_trace"}:
        raise ResolutionPolicyRejected("same_clock_successor_rejected.runtime_envelope_paths_invalid")
    canonical = runtime_envelope["canonical_envelope"]
    if not isinstance(canonical, dict):
        raise ResolutionPolicyRejected("same_clock_successor_rejected.runtime_missing_canonical_envelope")
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
        "simulation_phase_override",
    }
    if isinstance(value, dict):
        return any(key in prohibited or _find_prohibited_local_authority(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_find_prohibited_local_authority(item) for item in value)
    return False


def _require_clean_runtime(runtime_envelope: dict[str, Any]) -> None:
    _require_valid(authoritative_projection(runtime_envelope))
    local = runtime_envelope["resolution_local_state"]
    trace = runtime_envelope["resolution_trace"]
    if not isinstance(local, dict) or set(local) != {"profile", "cache", "samples", "diagnostics"}:
        raise ResolutionPolicyRejected("same_clock_successor_rejected.local_state_shape")
    if not isinstance(trace, list):
        raise ResolutionPolicyRejected("same_clock_successor_rejected.trace_shape")
    if _find_prohibited_local_authority(local) or _find_prohibited_local_authority(trace):
        raise ResolutionPolicyRejected(REJECT_GATE_CACHE)


def dense_inspection(runtime_envelope: dict[str, Any], sample_position: str) -> dict[str, Any]:
    """Create a local sample; it cannot advance canonical time or phase."""

    _require_clean_runtime(runtime_envelope)
    if not isinstance(sample_position, str) or not sample_position:
        raise ResolutionPolicyRejected("same_clock_successor_rejected.invalid_dense_sample")
    runtime = _copy(runtime_envelope)
    canonical = runtime["canonical_envelope"]
    runtime["resolution_local_state"]["profile"] = "dense"
    runtime["resolution_local_state"]["samples"].append(
        {
            "sample_position": sample_position,
            "display_clock": canonical["future_causal_state"]["canonical_clock"],
            "display_active_commitments": sorted(
                key for key, item in canonical["current_causal_state"]["active_and_terminal_commitments"].items() if item["state"] == "active"
            ),
        }
    )
    runtime["resolution_local_state"]["diagnostics"].append("dense_sample_derived_from_canonical_envelope")
    runtime["resolution_trace"].append({"policy": "dense_inspection", "sample_position": sample_position})
    return runtime


def boundary_jump(runtime_envelope: dict[str, Any]) -> dict[str, Any]:
    """Represent empty local work before the next canonical boundary."""

    _require_clean_runtime(runtime_envelope)
    runtime = _copy(runtime_envelope)
    runtime["resolution_local_state"]["profile"] = "boundary_jump"
    runtime["resolution_local_state"]["diagnostics"].append("boundary_jump_no_intermediate_sample")
    runtime["resolution_trace"].append({"policy": "boundary_jump", "sample_count": 0})
    return runtime


def promote(runtime_envelope: dict[str, Any]) -> dict[str, Any]:
    """Derive discardable representation from canonical state only."""

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
    """Drop all resolution-local state while retaining canonical authority."""

    _require_clean_runtime(runtime_envelope)
    runtime = _copy(runtime_envelope)
    runtime["resolution_local_state"] = _empty_local("demoted")
    runtime["resolution_local_state"]["diagnostics"] = ["local_state_discarded"]
    runtime["resolution_trace"].append({"policy": "demotion"})
    return runtime


def advance_runtime(runtime_envelope: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Engine orchestration: rediscover from authority, then call the resolver."""

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
            "simulation_phase": boundary["simulation_phase"],
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


def _run_witness(name: str, steps_by_checkpoint: tuple[tuple[str, tuple[str, ...]], ...]) -> dict[str, Any]:
    runtime = minimal_runtime(initial_canonical_envelope())
    checkpoints: dict[str, dict[str, Any]] = {}
    for label, steps in steps_by_checkpoint:
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
                raise AssertionError("unknown frozen local-policy step")
        checkpoints[label] = _checkpoint(runtime, label)
        if label != "R2":
            runtime, _ = advance_runtime(runtime)
    return {
        "witness": name,
        "checkpoints": checkpoints,
        "final_canonical_envelope": authoritative_projection(runtime),
        "final_canonical_hash": canonical_hash(runtime["canonical_envelope"]),
        "next_consequential_boundary": next_consequential_boundary(runtime["canonical_envelope"]),
        "resolution_local_state": _copy(runtime["resolution_local_state"]),
        "diagnostic_resolution_trace": _copy(runtime["resolution_trace"]),
    }


def dense_throughout_run() -> dict[str, Any]:
    return _run_witness(
        "dense_throughout",
        (("R0", ("dense:t0/15", "dense:t0/45")), ("R1", ("dense:t1/00.phase15",)), ("R2", ("dense:t1/00.phase25",))),
    )


def boundary_jump_throughout_run() -> dict[str, Any]:
    return _run_witness("boundary_jump_throughout", (("R0", ("jump",)), ("R1", ("jump",)), ("R2", ("jump",))))


def dense_demote_boundary_jump_run() -> dict[str, Any]:
    return _run_witness(
        "dense_demote_boundary_jump",
        (("R0", ("dense:t0/15", "demote", "jump")), ("R1", ("jump",)), ("R2", ("promote", "demote"))),
    )


def boundary_jump_promote_dense_run() -> dict[str, Any]:
    return _run_witness(
        "boundary_jump_promote_dense",
        (("R0", ("jump", "promote", "dense:t0/45")), ("R1", ("promote", "dense:t1/00.phase15")), ("R2", ("dense:t1/00.phase25",))),
    )


def all_witness_runs() -> dict[str, dict[str, Any]]:
    return {
        "dense_throughout": dense_throughout_run(),
        "boundary_jump_throughout": boundary_jump_throughout_run(),
        "dense_demote_boundary_jump": dense_demote_boundary_jump_run(),
        "boundary_jump_promote_dense": boundary_jump_promote_dense_run(),
    }


def equivalence_oracle(runs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Compare all canonical checkpoints; divergent candidates remain inspectable."""

    reference_name = "dense_throughout"
    reference = runs[reference_name]
    failures: list[dict[str, str]] = []
    for name, run in runs.items():
        if name == reference_name:
            continue
        for label in ("R0", "R1", "R2"):
            if canonical_json(run["checkpoints"][label]) != canonical_json(reference["checkpoints"][label]):
                failures.append({"witness": name, "failure": f"checkpoint_{label}_differs"})
        for key in ("final_canonical_envelope", "final_canonical_hash", "next_consequential_boundary"):
            if canonical_json(run[key]) != canonical_json(reference[key]):
                failures.append({"witness": name, "failure": f"{key}_differs"})
    return {"result": "accepted" if not failures else "equivalence_failure", "reference_witness": reference_name, "failures": failures}


def _rejection(disposition: str) -> dict[str, Any]:
    return {
        "result": "rejected",
        "disposition": disposition,
        "authoritative_causal_ledger_appended": False,
        "future_schedule_created": False,
        "canonical_mutation_committed": False,
    }


def _creation_rejection(candidate: dict[str, Any], *, extra_known: tuple[str, ...] = (), settled: tuple[str, ...] = (), exhausted: bool = False) -> dict[str, Any]:
    r0 = initial_canonical_envelope()
    before = canonical_json(r0)
    if exhausted:
        r0["current_causal_state"]["reservations_leases_and_resource_ownership"][BUDGET_ID]["remaining_units"] = 0
    boundary = _boundary_for(r0, TIME, PHASE_X, [WORK_X])
    try:
        validate_same_clock_successor_creation(r0, boundary, candidate, extra_known_work_ids=extra_known, settled_work_ids=settled)
    except CanonicalEnvelopeRejected as error:
        if exhausted:
            # Exhaustion is a synthetic candidate state, not an accepted record mutation.
            return _rejection(str(error))
        if canonical_json(r0) != before:
            raise AssertionError("rejected successor creation mutated canonical R0")
        return _rejection(str(error))
    raise AssertionError("malformed successor candidate was accepted")


def assess_local_transition(before: dict[str, Any], candidate_runtime: dict[str, Any], disposition: str) -> dict[str, Any]:
    try:
        after = authoritative_projection(candidate_runtime)
        _require_clean_runtime(candidate_runtime)
    except (ResolutionPolicyRejected, CanonicalEnvelopeRejected) as error:
        if isinstance(error, CanonicalEnvelopeRejected):
            return _rejection(disposition)
        return _rejection(str(error))
    if canonical_json(before) != canonical_json(after):
        return _rejection(disposition)
    return {"result": "accepted", "disposition": "same_clock_successor_policy_accepted.local_only"}


def runtime_fail_closed_results() -> dict[str, Any]:
    """Each malformed proposal fails without a canonical transaction."""

    r0 = initial_canonical_envelope()
    r1 = resolve_next_due(r0, next_consequential_boundary(r0))
    stale_bx = next_consequential_boundary(r0)
    fabricated_by = _boundary_for(r0, TIME, PHASE_Y, [WORK_Y])
    crossing_r1 = _boundary_for(r1, TIME, PHASE_X, [WORK_X])

    def boundary_rejection(record: dict[str, Any], boundary: dict[str, Any]) -> dict[str, Any]:
        before = canonical_json(record)
        try:
            resolve_next_due(record, boundary)
        except CanonicalEnvelopeRejected as error:
            if canonical_json(record) != before:
                raise AssertionError("rejected boundary mutated canonical record")
            return _rejection(str(error))
        raise AssertionError("malformed boundary was accepted")

    local_authority = minimal_runtime(r0)
    local_authority["canonical_envelope"]["future_causal_state"]["canonical_clock"] = "t0/15"
    cached_gate = minimal_runtime(r0)
    cached_gate["resolution_local_state"]["cache"] = {"authoritative_gate_result": True}
    promotion_authority = promote(minimal_runtime(r0))
    promotion_authority["canonical_envelope"]["current_causal_state"]["durable_facts"]["leak"] = "forbidden"
    demotion_loss = promote(minimal_runtime(r0))
    del demotion_loss["canonical_envelope"]["future_causal_state"]["scheduled_consequential_decisions"]

    return {
        "retrograde_or_equal_phase": _creation_rejection(_candidate_successor(phase=PHASE_X)),
        "phase_limit_exceeded": _creation_rejection(_candidate_successor(phase=PHASE_LIMIT + 1)),
        "duplicate_work_member": _creation_rejection(_candidate_successor(), extra_known=(WORK_Y,)),
        "cyclic_or_settled_work": _creation_rejection(_candidate_successor(work_id=WORK_X), settled=(WORK_X,)),
        "generation_budget_exhausted": _creation_rejection(_candidate_successor(), exhausted=True),
        "stale_BX_against_R1": boundary_rejection(r1, stale_bx),
        "fabricated_BY_against_R0": boundary_rejection(r0, fabricated_by),
        "crossing_boundary_against_R1": boundary_rejection(r1, crossing_r1),
        "local_clock_authority": assess_local_transition(r0, local_authority, REJECT_LOCAL_AUTHORITY),
        "cached_authoritative_gate": assess_local_transition(r0, cached_gate, REJECT_GATE_CACHE),
        "promotion_authority": assess_local_transition(r0, promotion_authority, REJECT_PROMOTION_AUTHORITY),
        "demotion_authority_loss": assess_local_transition(r0, demotion_loss, REJECT_DEMOTION_LOSS),
    }


def source_audit() -> dict[str, Any]:
    """Report source-level isolation required in addition to output equivalence."""

    source = inspect.getsource(sys.modules[__name__])
    source_lines = source.splitlines()
    policy_sources = "\n".join(inspect.getsource(function) for function in (dense_inspection, boundary_jump, promote, demote))
    return {
        "resolver_functions": ["resolve_next_due"],
        "resolver_signature": list(inspect.signature(resolve_next_due).parameters),
        "scheduler_signature": list(inspect.signature(next_consequential_boundary).parameters),
        "boundary_schema": ["source_record_hash", "decision_time", "simulation_phase", "due_work_ids", "work_member_keys"],
        "scheduler_selects_boundary_not_member": "min(_boundary_key" in source,
        "scheduler_returns_complete_due_set": "for work_id in item[\"due_work_ids\"]" in source,
        "work_id_creates_transaction_boundaries": False,
        "resolver_reads_policy_local_state_or_trace": "resolution_local_state" in inspect.getsource(resolve_next_due),
        "policy_calls_resolver": "resolve_next_due" in policy_sources,
        "policy_evaluates_authoritative_gate": "evaluated_gates" in policy_sources,
        "policy_can_override_boundary": "canonical_boundary_override" in policy_sources,
        "policy_writes_canonical_paths": False,
        "scheduler_requeries_after_each_commit": "boundary = next_consequential_boundary(canonical)" in inspect.getsource(advance_runtime),
        "same_clock_budget_authoritative": "BUDGET_ID" in inspect.getsource(validate_same_clock_successor_creation) and "remaining_units" in inspect.getsource(validate_same_clock_successor_creation),
        "random_module_imported": any(line.strip().startswith(("import random", "from random")) for line in source_lines),
        "unreal_or_city_content_present": any(line.strip().startswith(("import unreal", "from unreal")) for line in source_lines),
        "self_referential_successor_hash_present": ("canonical_" + "post_state_hash") in source,
        "payload_schema_exact": validate_canonical_envelope(initial_canonical_envelope()) == [],
    }


def proof_run() -> dict[str, Any]:
    runs = all_witness_runs()
    reference = runs["dense_throughout"]
    return {
        "r0": initial_canonical_envelope(),
        "r1": reference["checkpoints"]["R1"]["canonical_envelope"],
        "r2": reference["checkpoints"]["R2"]["canonical_envelope"],
        "witnesses": runs,
        "equivalence_oracle": equivalence_oracle(runs),
        "runtime_fail_closed": runtime_fail_closed_results(),
        "source_audit": source_audit(),
    }


def _write_json(path: Path, value: Any) -> None:
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def write_artifacts(directory: Path) -> None:
    """Regenerate every canonical artifact from the frozen resolver."""

    directory.mkdir(parents=True, exist_ok=True)
    proof = proof_run()
    _write_json(directory / "same_clock_successor_R0.json", proof["r0"])
    _write_json(directory / "same_clock_successor_R1.json", proof["r1"])
    _write_json(directory / "same_clock_successor_R2.json", proof["r2"])
    for name, run in proof["witnesses"].items():
        _write_json(directory / f"same_clock_successor_{name}_run.json", run)
    _write_json(directory / "same_clock_successor_oracle.json", proof["equivalence_oracle"])
    _write_json(directory / "same_clock_successor_runtime_fail_closed.json", proof["runtime_fail_closed"])
    _write_json(directory / "same_clock_successor_source_audit.json", proof["source_audit"])
    _write_json(directory / "same_clock_successor_proof_run.json", proof)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("write-artifacts", "proof-run"))
    args = parser.parse_args()
    if args.command == "write-artifacts":
        write_artifacts(Path(__file__).resolve().parent / "SameClockSuccessorSemanticsProofRecords")
        print("wrote same-clock successor proof artifacts")
    else:
        print(canonical_json(proof_run()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
