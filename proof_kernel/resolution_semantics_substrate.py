"""Canonical-only implementation of the frozen resolution-semantics substrate.

This module deliberately stops at scheduler-boundary discovery.  It supplies
one exact authoritative envelope and pure representation transitions; it does
not execute a commitment, model a city, or introduce variable resolution.
"""

from __future__ import annotations

import argparse
import copy
import inspect
import json
from pathlib import Path
from typing import Any

from kernel import canonical_json, state_hash


RECORD_SCHEMA = "CanonicalResolutionEnvelope.v1"
PAYLOAD_SCHEMA = "ResolutionSemanticsSubstratePayload.v1"
SCENARIO_ID = "resolution-semantics-substrate-v1"
SCENARIO_VERSION = "0.1.0"
SIMULATION_VERSION = "0.7.0-draft.30"
SEED = "resolution-semantics-substrate-v1/0001"

DECISION_TIME = "t1/00"
DUE_WORK_ID = "t1/00/substrate/commitment_alpha.gate_check"
COMMITMENT_ID = "commitment_alpha"
RESERVATION_ID = "reservation_alpha"

REJECTION_AUTHORITATIVE_MUTATION = "resolution_transition_rejected.authoritative_mutation_detected"
REJECTION_AUTHORITATIVE_LOSS = "resolution_transition_rejected.authoritative_loss_detected"
REJECTION_BOUNDARY_MISMATCH = "resolution_transition_rejected.boundary_mismatch"


class CanonicalEnvelopeRejected(ValueError):
    """Raised when an envelope violates the exact frozen payload contract."""


def _copy(value: Any) -> Any:
    return copy.deepcopy(value)


def initial_canonical_envelope() -> dict[str, Any]:
    """Return the one complete, neutral R0 canonical envelope."""

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
            "durable_facts": {"substrate_marker": "stable"},
            "active_commitments": {
                COMMITMENT_ID: {
                    "owner": "process_alpha",
                    "state": "active",
                    "gate_check_at": DECISION_TIME,
                    "required_gate": "substrate_marker == stable",
                    "reservation_id": RESERVATION_ID,
                    "terminal_disposition": "release_unit_alpha_on_failed_or_cancelled",
                }
            },
            "resource_ownership": {
                "unit_alpha": {
                    "state": "reserved",
                    "reservation_id": RESERVATION_ID,
                    "owner_commitment_id": COMMITMENT_ID,
                }
            },
            "gate_relevant_state": {"substrate_marker": "stable"},
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
                "terminal_resource_disposition": "release_unit_alpha_on_failed_or_cancelled",
            },
            "authoritative_causal_ledger": [],
            "terminal_resource_dispositions": {
                RESERVATION_ID: "release_unit_alpha_on_failed_or_cancelled"
            },
        },
    }


def canonical_hash(canonical_envelope: dict[str, Any]) -> str:
    """Hash only the singular authoritative envelope, never runtime local state."""

    return state_hash(canonical_envelope)


def _shape_errors(actual: Any, expected: Any, path: str = "canonical_envelope") -> list[str]:
    """Return unknown/missing/type errors without conflating them with value laws."""

    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [f"{path}.type"]
        errors: list[str] = []
        actual_keys = set(actual)
        expected_keys = set(expected)
        for key in sorted(expected_keys - actual_keys):
            errors.append(f"{path}.{key}.missing")
        for key in sorted(actual_keys - expected_keys):
            errors.append(f"{path}.{key}.unknown")
        for key in sorted(actual_keys & expected_keys):
            errors.extend(_shape_errors(actual[key], expected[key], f"{path}.{key}"))
        return errors
    if isinstance(expected, list):
        if not isinstance(actual, list):
            return [f"{path}.type"]
        errors = []
        if len(actual) != len(expected):
            errors.append(f"{path}.length")
        for index, value in enumerate(actual[: len(expected)]):
            errors.extend(_shape_errors(value, expected[index], f"{path}[{index}]"))
        return errors
    if type(actual) is not type(expected):
        return [f"{path}.type"]
    return []


def _at(value: Any, *path: Any) -> Any:
    current = value
    for part in path:
        if isinstance(part, int):
            if not isinstance(current, list) or part >= len(current):
                return None
        elif not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def validate_canonical_envelope(canonical_envelope: dict[str, Any]) -> list[str]:
    """Validate every permitted authoritative path and its required agreement."""

    expected = initial_canonical_envelope()
    errors = _shape_errors(canonical_envelope, expected)
    if errors:
        return sorted(set(errors))

    current = canonical_envelope["current_causal_state"]
    future = canonical_envelope["future_causal_state"]
    provenance = canonical_envelope["causal_provenance"]
    commitment = current["active_commitments"][COMMITMENT_ID]
    schedule_item = future["scheduled_consequential_decisions"][0]
    reservation = current["resource_ownership"]["unit_alpha"]
    genesis = provenance["fixture_genesis"]

    exact_groups = {
        "identity_exact": canonical_envelope["identity"] == expected["identity"],
        "durable_facts_exact": current["durable_facts"] == expected["current_causal_state"]["durable_facts"],
        "active_commitment_exact": commitment == expected["current_causal_state"]["active_commitments"][COMMITMENT_ID],
        "resource_ownership_exact": reservation == expected["current_causal_state"]["resource_ownership"]["unit_alpha"],
        "gate_relevant_state_exact": current["gate_relevant_state"] == expected["current_causal_state"]["gate_relevant_state"],
        "accepted_external_inputs_exact": current["accepted_external_inputs"] == [],
        "canonical_clock_exact": future["canonical_clock"] == "t0/00",
        "schedule_item_exact": schedule_item == expected["future_causal_state"]["scheduled_consequential_decisions"][0],
        "commitment_schedule_exact": future["commitment_gate_check_schedule"] == expected["future_causal_state"]["commitment_gate_check_schedule"],
        "execution_keys_exact": future["canonical_execution_keys"] == [DUE_WORK_ID],
        "canonical_ancestry_exact": provenance["canonical_ancestry"] == expected["causal_provenance"]["canonical_ancestry"],
        "fixture_genesis_exact": genesis == expected["causal_provenance"]["fixture_genesis"],
        "causal_ledger_empty": provenance["authoritative_causal_ledger"] == [],
        "terminal_dispositions_exact": provenance["terminal_resource_dispositions"] == expected["causal_provenance"]["terminal_resource_dispositions"],
    }
    errors.extend(name for name, passed in exact_groups.items() if not passed)

    relationship_checks = {
        "commitment_schedule_agreement": commitment["gate_check_at"] == schedule_item["decision_time"] == future["commitment_gate_check_schedule"][COMMITMENT_ID],
        "schedule_execution_keys_agreement": schedule_item["due_work_ids"] == future["canonical_execution_keys"] == [DUE_WORK_ID],
        "reservation_ownership_agreement": commitment["reservation_id"] == reservation["reservation_id"] == RESERVATION_ID
        and reservation["owner_commitment_id"] == COMMITMENT_ID,
        "durable_gate_marker_agreement": current["durable_facts"]["substrate_marker"] == current["gate_relevant_state"]["substrate_marker"],
        "required_gate_references_valid_fact": commitment["required_gate"] == "substrate_marker == stable"
        and current["gate_relevant_state"].get("substrate_marker") == "stable",
        "fixture_genesis_explains_reservation": genesis["established_facts"]
        == [
            "active_commitments.commitment_alpha = active",
            "resource_ownership.unit_alpha = reserved_by:reservation_alpha",
        ]
        and genesis["resources"] == ["unit_alpha starts reserved by reservation_alpha"]
        and genesis["terminal_resource_disposition"] == commitment["terminal_disposition"]
        == provenance["terminal_resource_dispositions"][RESERVATION_ID],
    }
    errors.extend(name for name, passed in relationship_checks.items() if not passed)
    return sorted(set(errors))


def _require_valid(canonical_envelope: dict[str, Any]) -> None:
    errors = validate_canonical_envelope(canonical_envelope)
    if errors:
        raise CanonicalEnvelopeRejected("canonical_envelope_rejected." + ",".join(errors))


def next_consequential_boundary(canonical_envelope: dict[str, Any]) -> dict[str, Any]:
    """Return the complete next authoritative decision boundary from canonical state."""

    _require_valid(canonical_envelope)
    schedule_item = canonical_envelope["future_causal_state"]["scheduled_consequential_decisions"][0]
    return {"decision_time": schedule_item["decision_time"], "due_work_ids": _copy(schedule_item["due_work_ids"])}


def authoritative_projection(runtime_envelope: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of runtime authority; resolution-local data is deliberately excluded."""

    if set(runtime_envelope) != {"canonical_envelope", "resolution_local_state"}:
        raise ValueError("runtime_envelope_exact_paths_required")
    envelope = runtime_envelope.get("canonical_envelope")
    if not isinstance(envelope, dict):
        raise ValueError("runtime_envelope_missing_canonical_envelope")
    return _copy(envelope)


def _runtime(canonical_envelope: dict[str, Any], local_state: dict[str, Any]) -> dict[str, Any]:
    return {
        "canonical_envelope": _copy(canonical_envelope),
        "resolution_local_state": _copy(local_state),
    }


def minimal_runtime(canonical_envelope: dict[str, Any]) -> dict[str, Any]:
    _require_valid(canonical_envelope)
    return _runtime(canonical_envelope, {"profile": "minimal", "cache": {}, "samples": [], "diagnostics": []})


def promote(canonical_envelope: dict[str, Any]) -> dict[str, Any]:
    """Derive promoted local detail without changing authority."""

    _require_valid(canonical_envelope)
    commitment = canonical_envelope["current_causal_state"]["active_commitments"][COMMITMENT_ID]
    return _runtime(
        canonical_envelope,
        {
            "profile": "promoted",
            "cache": {
                COMMITMENT_ID: {
                    "next_gate_display": commitment["gate_check_at"],
                    "reservation_display": commitment["reservation_id"],
                }
            },
            "samples": [canonical_envelope["future_causal_state"]["canonical_clock"]],
            "diagnostics": ["promotion_derived_from_canonical_envelope"],
        },
    )


def demote(runtime_envelope: dict[str, Any]) -> dict[str, Any]:
    """Discard all local representation while preserving byte-identical authority."""

    canonical_envelope = authoritative_projection(runtime_envelope)
    _require_valid(canonical_envelope)
    return _runtime(
        canonical_envelope,
        {"profile": "demoted", "cache": {}, "samples": [], "diagnostics": ["local_state_discarded"]},
    )


def _transition_rejection(before: dict[str, Any], candidate: dict[str, Any], disposition: str) -> dict[str, Any]:
    """Report a non-causal failed transition without repairing or mutating either input."""

    try:
        after = authoritative_projection(candidate)
    except ValueError:
        after = None
    return {
        "result": "rejected",
        "disposition": disposition,
        "canonical_hash_before": canonical_hash(before),
        "canonical_hash_after": canonical_hash(after) if isinstance(after, dict) else None,
        "authoritative_causal_ledger_appended": False,
        "future_schedule_created": False,
    }


def assess_promotion_transition(before: dict[str, Any], candidate_runtime: dict[str, Any]) -> dict[str, Any]:
    """Fail closed when a proposed promotion creates or changes authority."""

    if canonical_json(authoritative_projection(candidate_runtime)) != canonical_json(before):
        return _transition_rejection(before, candidate_runtime, REJECTION_AUTHORITATIVE_MUTATION)
    try:
        _require_valid(authoritative_projection(candidate_runtime))
    except CanonicalEnvelopeRejected:
        return _transition_rejection(before, candidate_runtime, REJECTION_AUTHORITATIVE_MUTATION)
    return {"result": "accepted", "disposition": "resolution_transition_accepted.promotion_neutral"}


def assess_demotion_transition(before: dict[str, Any], candidate_runtime: dict[str, Any]) -> dict[str, Any]:
    """Fail closed when a proposed demotion loses or changes authority."""

    try:
        after = authoritative_projection(candidate_runtime)
    except ValueError:
        return _transition_rejection(before, candidate_runtime, REJECTION_AUTHORITATIVE_LOSS)
    if canonical_json(after) != canonical_json(before):
        return _transition_rejection(before, candidate_runtime, REJECTION_AUTHORITATIVE_LOSS)
    try:
        _require_valid(after)
    except CanonicalEnvelopeRejected:
        return _transition_rejection(before, candidate_runtime, REJECTION_AUTHORITATIVE_LOSS)
    return {"result": "accepted", "disposition": "resolution_transition_accepted.demotion_neutral"}


def assess_boundary_policy(canonical_envelope: dict[str, Any], proposed_boundary: dict[str, Any]) -> dict[str, Any]:
    """Reject any resolution-local attempt to replace canonical boundary discovery."""

    expected = next_consequential_boundary(canonical_envelope)
    if canonical_json(proposed_boundary) != canonical_json(expected):
        return {
            "result": "rejected",
            "disposition": REJECTION_BOUNDARY_MISMATCH,
            "canonical_hash": canonical_hash(canonical_envelope),
            "expected_boundary": expected,
            "proposed_boundary": _copy(proposed_boundary),
            "authoritative_causal_ledger_appended": False,
            "future_schedule_created": False,
        }
    return {"result": "accepted", "disposition": "resolution_transition_accepted.boundary_identity"}


def source_audit() -> dict[str, Any]:
    """Mechanically report the narrow source properties frozen for this substrate."""

    scheduler_source = inspect.getsource(next_consequential_boundary)
    transform_source = inspect.getsource(promote) + inspect.getsource(demote)
    machine_source = (
        inspect.getsource(initial_canonical_envelope)
        + inspect.getsource(validate_canonical_envelope)
        + scheduler_source
        + transform_source
    )
    forbidden_canonical_write_tokens = (
        '["canonical_envelope"] =',
        '["identity"] =',
        '["current_causal_state"] =',
        '["future_causal_state"] =',
        '["causal_provenance"] =',
    )
    return {
        "scheduler_functions": ["next_consequential_boundary"],
        "scheduler_parameter": "canonical_envelope",
        "scheduler_reads_resolution_local_state": "resolution_local_state" in scheduler_source,
        "transforms_write_canonical_paths": any(token in transform_source for token in forbidden_canonical_write_tokens),
        "scheduler_or_resolver_reads_resolution_trace": "resolution_trace" in scheduler_source,
        "policy_can_override_boundary": "proposed_boundary" in scheduler_source,
        "expected_result_shortcut_present": "apply_expected_result" in transform_source,
        "transform_mutates_commitment_resource_or_ledger": any(
            token in transform_source
            for token in ('["active_commitments"] =', '["resource_ownership"] =', '["authoritative_causal_ledger"] =')
        ),
        "payload_validation_uses_exact_schema": "initial_canonical_envelope()" in inspect.getsource(validate_canonical_envelope)
        and "PAYLOAD_SCHEMA" in inspect.getsource(initial_canonical_envelope),
        "authoritative_randomness": "none",
        "random_module_imported": "import random" in machine_source or "from random" in machine_source,
        "resolution_execution_modes_implemented": any(
            token in machine_source
            for token in ("high_resolution", "coarse_resolution", "resolution_policy")
        ),
    }


def proof_run() -> dict[str, Any]:
    """Execute the four neutrality witnesses and three fail-closed dispositions."""

    r0 = initial_canonical_envelope()
    minimal = minimal_runtime(r0)
    promoted = promote(r0)
    demoted = demote(promoted)
    re_promoted = promote(authoritative_projection(demoted))
    boundary = next_consequential_boundary(r0)

    malicious_promotion = promote(r0)
    malicious_promotion["canonical_envelope"]["current_causal_state"]["durable_facts"]["illegal_marker"] = "created"
    malicious_demotion = promote(r0)
    del malicious_demotion["canonical_envelope"]["current_causal_state"]["resource_ownership"]["unit_alpha"]
    altered_boundaries = {
        "changed_time": {"decision_time": "t2/00", "due_work_ids": [DUE_WORK_ID]},
        "omitted_due_work": {"decision_time": DECISION_TIME, "due_work_ids": []},
        "added_due_work": {"decision_time": DECISION_TIME, "due_work_ids": [DUE_WORK_ID, "t1/00/substrate/extra"]},
    }

    return {
        "proof_identity": {
            "payload_schema": PAYLOAD_SCHEMA,
            "scenario_id": SCENARIO_ID,
            "scenario_version": SCENARIO_VERSION,
            "simulation_version": SIMULATION_VERSION,
        },
        "r0_canonical_hash": canonical_hash(r0),
        "witnesses": {
            "boundary_identity": {
                "r0": boundary,
                "minimal": next_consequential_boundary(authoritative_projection(minimal)),
                "promoted": next_consequential_boundary(authoritative_projection(promoted)),
                "demoted": next_consequential_boundary(authoritative_projection(demoted)),
            },
            "promotion_neutrality": {
                "canonical_hash_before": canonical_hash(r0),
                "canonical_hash_after": canonical_hash(authoritative_projection(promoted)),
                "projection_byte_identical": canonical_json(r0) == canonical_json(authoritative_projection(promoted)),
                "assessment": assess_promotion_transition(r0, promoted),
            },
            "demotion_neutrality": {
                "canonical_hash_before": canonical_hash(r0),
                "canonical_hash_after": canonical_hash(authoritative_projection(demoted)),
                "projection_byte_identical": canonical_json(r0) == canonical_json(authoritative_projection(demoted)),
                "local_cache": demoted["resolution_local_state"]["cache"],
                "assessment": assess_demotion_transition(r0, demoted),
            },
            "demotion_promotion_round_trip": {
                "canonical_hash_before": canonical_hash(r0),
                "canonical_hash_after": canonical_hash(authoritative_projection(re_promoted)),
                "projection_byte_identical": canonical_json(r0) == canonical_json(authoritative_projection(re_promoted)),
                "final_promoted_cache": _copy(re_promoted["resolution_local_state"]["cache"]),
            },
        },
        "adversarial_dispositions": {
            "promotion_creates_authority": assess_promotion_transition(r0, malicious_promotion),
            "demotion_drops_authority": assess_demotion_transition(r0, malicious_demotion),
            "policy_changes_boundary": {
                name: assess_boundary_policy(r0, candidate) for name, candidate in altered_boundaries.items()
            },
        },
        "source_audit": source_audit(),
    }


def _write_json(path: Path, value: Any) -> None:
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def write_artifacts(directory: Path) -> None:
    """Write deterministic, inspectable proof artifacts without an authority wrapper."""

    directory.mkdir(parents=True, exist_ok=True)
    run = proof_run()
    _write_json(directory / "resolution_substrate_R0.json", initial_canonical_envelope())
    _write_json(directory / "resolution_substrate_run.json", run)
    _write_json(directory / "resolution_substrate_witnesses.json", run["witnesses"])
    _write_json(directory / "resolution_substrate_adversarial.json", run["adversarial_dispositions"])
    _write_json(directory / "resolution_substrate_source_audit.json", run["source_audit"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_artifacts(args.output)
    print(f"wrote resolution-semantics substrate artifacts to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
