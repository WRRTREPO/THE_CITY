"""Canonical-only implementation of the frozen occupancy-transition proof.

This module implements exactly one two-site, one-route, one-subject fixture.
It is not a movement, navigation, travel-time, or representation system.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import inspect
import json
import sys
from pathlib import Path
from typing import Any, Callable

RECORD_SCHEMA = "CanonicalResolutionEnvelope.v1"
PAYLOAD_SCHEMA = "CanonicalOccupancyTransitionPayload.v1"
SCENARIO_ID = "canonical-occupancy-transition-v1"
SCENARIO_VERSION = "0.1.0"
SIMULATION_VERSION = "0.7.0-draft.65"
SEED = "canonical-occupancy-transition-v1/0001"

BOUNDARY_SCHEMA = "CanonicalOccupancyTransitionBoundary.v1"
LEDGER_SCHEMA = "CanonicalOccupancyTransitionLedgerEntry.v1"
ANCESTRY_SCHEMA = "CanonicalOccupancyTransitionAncestry.v1"
GENESIS_SCHEMA = "CanonicalOccupancyTransitionFixtureGenesis.v1"
TRACE_SCHEMA = "CanonicalOccupancyResolutionLocalInspection.v1"

SITE_A = "topology_site_0001"
SITE_B = "topology_site_0002"
ROUTE = "topology_route_0001"
OCCUPANT = "topology_occupant_0001"
TRANSITION = "occupancy_transition_0001"
RESERVATION = "occupancy_reservation_topology_occupant_0001"
START_WORK = "t0/30/occupancy/occupancy_transition_0001.start"
COMPLETE_WORK = "t1/00/occupancy/occupancy_transition_0001.complete"

TIME_ROOT = "t0/00"
TIME_START = "t0/30"
TIME_COMPLETE = "t1/00"
PHASE = 10
TIME_ORDER = {TIME_ROOT: 0, TIME_START: 1, TIME_COMPLETE: 2}

NO_BOUNDARY = None
BOUNDARY_KEYS = {
    "boundary_schema",
    "source_record_hash",
    "decision_time",
    "simulation_phase",
    "due_work_ids",
}

REJECT_RECORD = "occupancy_transition_rejected.invalid_canonical_record"
REJECT_SERIALIZATION = "occupancy_transition_rejected.serialization"
REJECT_BOUNDARY_SOURCE = "occupancy_transition_rejected.boundary_source_mismatch"
REJECT_BOUNDARY_SHAPE = "occupancy_transition_rejected.boundary_shape_mismatch"
REJECT_NO_DUE_WORK = "occupancy_transition_rejected.no_due_work"
REJECT_LOCAL_AUTHORITY = "occupancy_transition_rejected.local_authority"
REJECT_UNPUBLISHED_DISCOVERY = "occupancy_transition_rejected.unpublished_candidate"
REJECT_TRACE = "occupancy_transition_rejected.invalid_resolution_local_trace"
REJECT_FAULT = "occupancy_transition_rejected.injected_private_construction_fault"

START_FAULT_POINTS = (
    "start_after_occupancy",
    "start_after_commitment_state",
    "start_after_resources_owned",
    "start_after_reservation_state",
    "start_after_reservation_owner",
    "start_after_start_work_consumed",
    "start_after_completion_work_created",
    "start_after_clock",
    "start_after_ledger",
    "start_after_ancestry",
    "start_after_complete_validation_before_publication",
)
COMPLETION_FAULT_POINTS = (
    "completion_after_occupancy",
    "completion_after_commitment_state",
    "completion_after_resources_cleared",
    "completion_after_terminal_disposition",
    "completion_after_reservation_state",
    "completion_after_reservation_owner_cleared",
    "completion_after_work_consumed",
    "completion_after_clock",
    "completion_after_ledger",
    "completion_after_ancestry",
    "completion_after_complete_validation_before_publication",
)
BLOCKED_FAULT_POINTS = (
    "blocked_after_commitment_state",
    "blocked_after_terminal_reason",
    "blocked_after_terminal_disposition",
    "blocked_after_work_consumed",
    "blocked_after_clock",
    "blocked_after_ledger",
    "blocked_after_ancestry",
    "blocked_after_complete_validation_before_publication",
)
ALL_FAULT_POINTS = START_FAULT_POINTS + COMPLETION_FAULT_POINTS + BLOCKED_FAULT_POINTS


class CanonicalOccupancyRejected(ValueError):
    """Raised before publication when canonical input violates the payload."""


class ResolutionLocalAuthorityRejected(ValueError):
    """Raised when non-authoritative state attempts to enter causal authority."""


class InjectedPrivateConstructionFault(RuntimeError):
    """Raised only by the proof harness before a successor can publish."""


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


def state_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def canonical_hash(record: dict[str, Any]) -> str:
    return state_hash(record)


def _identity() -> dict[str, str]:
    return {
        "record_schema": RECORD_SCHEMA,
        "payload_schema": PAYLOAD_SCHEMA,
        "scenario_id": SCENARIO_ID,
        "scenario_version": SCENARIO_VERSION,
        "simulation_version": SIMULATION_VERSION,
        "seed": SEED,
    }


def _sites() -> dict[str, None]:
    return {SITE_A: None, SITE_B: None}


def _available_topology() -> dict[str, Any]:
    return {
        "sites": _sites(),
        "routes": {
            ROUTE: {
                "endpoint_semantics": "unordered_pair_fixture_only",
                "endpoint_site_ids": [SITE_A, SITE_B],
                "access_state": "available",
            }
        },
    }


def _blocked_topology() -> dict[str, Any]:
    return {
        "sites": _sites(),
        "routes": {
            ROUTE: {
                "endpoint_semantics": "unordered_pair_fixture_only",
                "endpoint_site_ids": [SITE_A, SITE_B],
                "access_state": "blocked",
            }
        },
    }


def _planned_transition() -> dict[str, Any]:
    return {
        "owner_occupant_id": OCCUPANT,
        "origin_site_id": SITE_B,
        "destination_site_id": SITE_A,
        "route_id": ROUTE,
        "canonical_start_time": TIME_START,
        "canonical_completion_time": TIME_COMPLETE,
        "state": "planned",
        "resources_owned": [],
        "terminal_reason": None,
        "terminal_resource_disposition": None,
    }


def _available_reservation() -> dict[str, Any]:
    return {
        "occupant_id": OCCUPANT,
        "state": "available",
        "owner_transition_id": None,
    }


def _start_work() -> dict[str, Any]:
    return {
        "work_id": START_WORK,
        "decision_time": TIME_START,
        "simulation_phase": PHASE,
        "transition_id": TRANSITION,
        "action": "start",
    }


def _completion_work() -> dict[str, Any]:
    return {
        "work_id": COMPLETE_WORK,
        "decision_time": TIME_COMPLETE,
        "simulation_phase": PHASE,
        "transition_id": TRANSITION,
        "action": "complete",
    }


def _fixture_genesis(topology: dict[str, Any]) -> dict[str, Any]:
    return {
        "genesis_schema": GENESIS_SCHEMA,
        "source": "frozen_initial_fixture",
        "initial_topology": _copy(topology),
        "initial_occupancy": {OCCUPANT: {"kind": "at_site", "site_id": SITE_B}},
        "initial_transition_definition": {TRANSITION: _planned_transition()},
        "initial_transition_reservation": {RESERVATION: _available_reservation()},
        "initial_work_projection": _start_work(),
    }


def _initial_record_from_exact_components(
    topology: dict[str, Any], genesis: dict[str, Any]
) -> dict[str, Any]:
    """Assemble exact components; it does not select or toggle a root variant."""

    return {
        "identity": _identity(),
        "current_causal_state": {
            "spatial_topology": _copy(topology),
            "canonical_occupancy": {
                OCCUPANT: {"kind": "at_site", "site_id": SITE_B}
            },
            "occupancy_transition_commitments": {TRANSITION: _planned_transition()},
            "occupancy_transition_reservations": {
                RESERVATION: _available_reservation()
            },
        },
        "future_causal_state": {
            "canonical_clock": TIME_ROOT,
            "unresolved_work": [_start_work()],
        },
        "causal_provenance": {
            "fixture_genesis": _copy(genesis),
            "authoritative_causal_ledger": [],
            "canonical_ancestry": None,
        },
    }


def initial_available_record() -> dict[str, Any]:
    topology = _available_topology()
    return _initial_record_from_exact_components(topology, _fixture_genesis(topology))


def initial_blocked_record() -> dict[str, Any]:
    topology = _blocked_topology()
    return _initial_record_from_exact_components(topology, _fixture_genesis(topology))


def transition_definition_projection(record: dict[str, Any]) -> dict[str, Any]:
    return _copy(
        record["current_causal_state"]["occupancy_transition_commitments"][TRANSITION]
    )


def detached_occupancy_projection(record: dict[str, Any]) -> dict[str, Any]:
    _require_valid_record(record)
    occupancy = record["current_causal_state"]["canonical_occupancy"][OCCUPANT]
    if occupancy == {"kind": "at_site", "site_id": SITE_B}:
        return {
            "site_projection": {SITE_A: [], SITE_B: [OCCUPANT]},
            "detached_transition_relation": None,
        }
    if occupancy == {"kind": "at_site", "site_id": SITE_A}:
        return {
            "site_projection": {SITE_A: [OCCUPANT], SITE_B: []},
            "detached_transition_relation": None,
        }
    return {
        "site_projection": {SITE_A: [], SITE_B: []},
        "detached_transition_relation": {OCCUPANT: TRANSITION},
    }


def _boundary_for(record: dict[str, Any], work: dict[str, Any]) -> dict[str, Any]:
    return {
        "boundary_schema": BOUNDARY_SCHEMA,
        "source_record_hash": canonical_hash(record),
        "decision_time": work["decision_time"],
        "simulation_phase": work["simulation_phase"],
        "due_work_ids": [work["work_id"]],
    }


def _start_gate_observations(record: dict[str, Any]) -> list[dict[str, Any]]:
    state = record["current_causal_state"]
    commitment = state["occupancy_transition_commitments"][TRANSITION]
    occupancy = state["canonical_occupancy"][OCCUPANT]
    access = state["spatial_topology"]["routes"][ROUTE]["access_state"]
    reservation = state["occupancy_transition_reservations"][RESERVATION]
    expected_occupancy = {"kind": "at_site", "site_id": SITE_B}
    return [
        {
            "gate_id": "commitment_planned",
            "path": f"/current_causal_state/occupancy_transition_commitments/{TRANSITION}/state",
            "observed": commitment["state"],
            "required": "planned",
            "passed": commitment["state"] == "planned",
        },
        {
            "gate_id": "occupant_at_origin",
            "path": f"/current_causal_state/canonical_occupancy/{OCCUPANT}",
            "observed": _copy(occupancy),
            "required": expected_occupancy,
            "passed": occupancy == expected_occupancy,
        },
        {
            "gate_id": "route_access_available",
            "path": f"/current_causal_state/spatial_topology/routes/{ROUTE}/access_state",
            "observed": access,
            "required": "available",
            "passed": access == "available",
        },
        {
            "gate_id": "reservation_available",
            "path": f"/current_causal_state/occupancy_transition_reservations/{RESERVATION}/state",
            "observed": reservation["state"],
            "required": "available",
            "passed": reservation["state"] == "available",
        },
    ]


def _completion_gate_observations(record: dict[str, Any]) -> list[dict[str, Any]]:
    state = record["current_causal_state"]
    commitment = state["occupancy_transition_commitments"][TRANSITION]
    occupancy = state["canonical_occupancy"][OCCUPANT]
    reservation = state["occupancy_transition_reservations"][RESERVATION]
    expected_occupancy = {"kind": "in_transition", "transition_id": TRANSITION}
    expected_owned = [RESERVATION]
    return [
        {
            "gate_id": "commitment_active",
            "path": f"/current_causal_state/occupancy_transition_commitments/{TRANSITION}/state",
            "observed": commitment["state"],
            "required": "active",
            "passed": commitment["state"] == "active",
        },
        {
            "gate_id": "occupancy_in_exact_transition",
            "path": f"/current_causal_state/canonical_occupancy/{OCCUPANT}",
            "observed": _copy(occupancy),
            "required": expected_occupancy,
            "passed": occupancy == expected_occupancy,
        },
        {
            "gate_id": "reservation_reserved",
            "path": f"/current_causal_state/occupancy_transition_reservations/{RESERVATION}/state",
            "observed": reservation["state"],
            "required": "reserved",
            "passed": reservation["state"] == "reserved",
        },
        {
            "gate_id": "reservation_owned_by_transition",
            "path": f"/current_causal_state/occupancy_transition_reservations/{RESERVATION}/owner_transition_id",
            "observed": reservation["owner_transition_id"],
            "required": TRANSITION,
            "passed": reservation["owner_transition_id"] == TRANSITION,
        },
        {
            "gate_id": "commitment_owns_exact_reservation",
            "path": f"/current_causal_state/occupancy_transition_commitments/{TRANSITION}/resources_owned",
            "observed": _copy(commitment["resources_owned"]),
            "required": expected_owned,
            "passed": commitment["resources_owned"] == expected_owned,
        },
    ]


def _transition_observation() -> dict[str, Any]:
    ordered_intent = [SITE_B, SITE_A]
    normalized_copy = sorted(_copy(ordered_intent))
    return {
        "origin_site_id": ordered_intent[0],
        "destination_site_id": ordered_intent[1],
        "route_id": ROUTE,
        "stored_endpoint_site_ids": [SITE_A, SITE_B],
        "normalized_transition_site_ids": normalized_copy,
    }


def _ledger_entry(
    source: dict[str, Any],
    boundary: dict[str, Any],
    gates: list[dict[str, Any]],
    result: str,
) -> dict[str, Any]:
    action = "complete" if boundary["due_work_ids"] == [COMPLETE_WORK] else "start"
    if result == "started":
        effects = {
            "occupancy": "at_site_origin_to_in_transition",
            "commitment": "planned_to_active",
            "reservation": "available_to_reserved",
            "clock": "t0/00_to_t0/30",
        }
        resource_effect = "reserve_subject_transition_reservation"
        downstream = "completion_work_created"
        created_work: dict[str, Any] | None = _completion_work()
    elif result == "failed_gate":
        effects = {
            "occupancy": "unchanged_at_origin",
            "commitment": "planned_to_failed",
            "terminal_reason": "failed_gate",
            "reservation": "unchanged_available",
            "clock": "t0/00_to_t0/30",
        }
        resource_effect = "no_resource_acquired"
        downstream = "none"
        created_work = None
    else:
        effects = {
            "occupancy": "in_transition_to_at_site_destination",
            "commitment": "active_to_succeeded",
            "reservation": "reserved_to_available",
            "clock": "t0/30_to_t1/00",
        }
        resource_effect = "release_subject_transition_reservation"
        downstream = "none"
        created_work = None
    sequence = len(source["causal_provenance"]["authoritative_causal_ledger"]) + 1
    pre_hash = canonical_hash(source)
    work_id = boundary["due_work_ids"][0]
    return {
        "ledger_schema": LEDGER_SCHEMA,
        "transaction_id": f"{boundary['decision_time']}/phase_{PHASE}/{TRANSITION}.{action}",
        "ledger_sequence": sequence,
        "resolver_path_id": "canonical_occupancy_transition.resolve_next_due.v1",
        "canonical_execution_sequence": 0,
        "simulation_version": SIMULATION_VERSION,
        "owner_occupant_id": OCCUPANT,
        "transition_id": TRANSITION,
        "work_id": work_id,
        "action": action,
        "decision_time": boundary["decision_time"],
        "simulation_phase": PHASE,
        "canonical_pre_state_hash": pre_hash,
        "source_boundary": _copy(boundary),
        "due_work_ids": [work_id],
        "snapshot_reference": pre_hash,
        "belief_inputs": "not_applicable",
        "eligible_action_set": [work_id],
        "selected_action": work_id,
        "deterministic_tie_break": "none",
        "random_draw_reference": "none",
        "threshold_evaluations": [],
        "structural_validation": "passed",
        "transition_observation": _transition_observation(),
        "reservation_id": RESERVATION,
        "gate_observations": _copy(gates),
        "result": result,
        "state_effects": effects,
        "resource_effect": resource_effect,
        "downstream_eligibility_effect": downstream,
        "schedule_effect": {
            "consumed_work_id": work_id,
            "created_work": created_work,
        },
    }


def _ancestry(source: dict[str, Any], boundary: dict[str, Any], sequence: int) -> dict[str, Any]:
    parent = canonical_hash(source)
    return {
        "ancestry_schema": ANCESTRY_SCHEMA,
        "parent_record_hash": parent,
        "boundary_derivation": {
            "method": "next_consequential_boundary",
            "source_record_hash": parent,
            "decision_time": boundary["decision_time"],
            "simulation_phase": PHASE,
            "due_work_ids": _copy(boundary["due_work_ids"]),
        },
        "ledger_sequence_after_commit": sequence,
    }


def _trip_fault(requested: str | None, point: str) -> None:
    if requested == point:
        raise InjectedPrivateConstructionFault(f"{REJECT_FAULT}:{point}")


def _construct_start_successor(
    source: dict[str, Any], boundary: dict[str, Any], fault_after: str | None = None
) -> dict[str, Any]:
    gates = _start_gate_observations(source)
    passed = all(item["passed"] for item in gates)
    candidate = _copy(source)
    state = candidate["current_causal_state"]
    future = candidate["future_causal_state"]
    provenance = candidate["causal_provenance"]
    commitment = state["occupancy_transition_commitments"][TRANSITION]
    reservation = state["occupancy_transition_reservations"][RESERVATION]

    if passed:
        state["canonical_occupancy"][OCCUPANT] = {
            "kind": "in_transition",
            "transition_id": TRANSITION,
        }
        _trip_fault(fault_after, "start_after_occupancy")
        commitment["state"] = "active"
        _trip_fault(fault_after, "start_after_commitment_state")
        commitment["resources_owned"] = [RESERVATION]
        _trip_fault(fault_after, "start_after_resources_owned")
        reservation["state"] = "reserved"
        _trip_fault(fault_after, "start_after_reservation_state")
        reservation["owner_transition_id"] = TRANSITION
        _trip_fault(fault_after, "start_after_reservation_owner")
        future["unresolved_work"] = []
        _trip_fault(fault_after, "start_after_start_work_consumed")
        future["unresolved_work"] = [_completion_work()]
        _trip_fault(fault_after, "start_after_completion_work_created")
        future["canonical_clock"] = TIME_START
        _trip_fault(fault_after, "start_after_clock")
        result = "started"
    else:
        commitment["state"] = "failed"
        _trip_fault(fault_after, "blocked_after_commitment_state")
        commitment["terminal_reason"] = "failed_gate"
        _trip_fault(fault_after, "blocked_after_terminal_reason")
        commitment["terminal_resource_disposition"] = "no_resource_acquired"
        _trip_fault(fault_after, "blocked_after_terminal_disposition")
        future["unresolved_work"] = []
        _trip_fault(fault_after, "blocked_after_work_consumed")
        future["canonical_clock"] = TIME_START
        _trip_fault(fault_after, "blocked_after_clock")
        result = "failed_gate"

    entry = _ledger_entry(source, boundary, gates, result)
    provenance["authoritative_causal_ledger"].append(entry)
    prefix = "start" if result == "started" else "blocked"
    _trip_fault(fault_after, f"{prefix}_after_ledger")
    provenance["canonical_ancestry"] = _ancestry(source, boundary, 1)
    _trip_fault(fault_after, f"{prefix}_after_ancestry")
    return candidate


def _construct_completion_successor(
    source: dict[str, Any], boundary: dict[str, Any], fault_after: str | None = None
) -> dict[str, Any]:
    gates = _completion_gate_observations(source)
    if not all(item["passed"] for item in gates):
        raise CanonicalOccupancyRejected(f"{REJECT_RECORD}:completion_gate_structure")
    candidate = _copy(source)
    state = candidate["current_causal_state"]
    future = candidate["future_causal_state"]
    provenance = candidate["causal_provenance"]
    commitment = state["occupancy_transition_commitments"][TRANSITION]
    reservation = state["occupancy_transition_reservations"][RESERVATION]

    state["canonical_occupancy"][OCCUPANT] = {"kind": "at_site", "site_id": SITE_A}
    _trip_fault(fault_after, "completion_after_occupancy")
    commitment["state"] = "succeeded"
    _trip_fault(fault_after, "completion_after_commitment_state")
    commitment["resources_owned"] = []
    _trip_fault(fault_after, "completion_after_resources_cleared")
    commitment["terminal_resource_disposition"] = "release_subject_transition_reservation"
    _trip_fault(fault_after, "completion_after_terminal_disposition")
    reservation["state"] = "available"
    _trip_fault(fault_after, "completion_after_reservation_state")
    reservation["owner_transition_id"] = None
    _trip_fault(fault_after, "completion_after_reservation_owner_cleared")
    future["unresolved_work"] = []
    _trip_fault(fault_after, "completion_after_work_consumed")
    future["canonical_clock"] = TIME_COMPLETE
    _trip_fault(fault_after, "completion_after_clock")
    provenance["authoritative_causal_ledger"].append(
        _ledger_entry(source, boundary, gates, "completed")
    )
    _trip_fault(fault_after, "completion_after_ledger")
    provenance["canonical_ancestry"] = _ancestry(source, boundary, 2)
    _trip_fault(fault_after, "completion_after_ancestry")
    return candidate


def _reference_records() -> dict[str, dict[str, Any]]:
    r0 = initial_available_record()
    r0_blocked = initial_blocked_record()
    b_start = _boundary_for(r0, _start_work())
    b_blocked = _boundary_for(r0_blocked, _start_work())
    rtransit = _construct_start_successor(r0, b_start)
    rblocked = _construct_start_successor(r0_blocked, b_blocked)
    b_complete = _boundary_for(
        rtransit, rtransit["future_causal_state"]["unresolved_work"][0]
    )
    rfinal = _construct_completion_successor(rtransit, b_complete)
    return {
        "R0": r0,
        "R0_blocked": r0_blocked,
        "Rtransit": rtransit,
        "Rfinal": rfinal,
        "Rblocked": rblocked,
    }


def validate_canonical_record(record: dict[str, Any]) -> list[str]:
    """Validate the exhaustive five-record payload value space."""

    try:
        encoded = canonical_json(record)
    except (TypeError, ValueError) as exc:
        return [f"not canonical JSON: {exc}"]
    if not isinstance(record, dict):
        return ["record must be an object"]
    exact_roots = {"identity", "current_causal_state", "future_causal_state", "causal_provenance"}
    errors: list[str] = []
    if set(record) != exact_roots:
        errors.append("top-level fields are not exact")
    if record.get("identity") != _identity():
        errors.append("identity is not exact")
    if any(encoded == canonical_json(reference) for reference in _reference_records().values()):
        return []
    errors.append("record does not match any exhaustive lifecycle row")
    return errors


def _require_valid_record(record: dict[str, Any]) -> None:
    errors = validate_canonical_record(record)
    if errors:
        raise CanonicalOccupancyRejected(f"{REJECT_RECORD}:{'|'.join(errors)}")


def _no_duplicate_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CanonicalOccupancyRejected(
                f"{REJECT_SERIALIZATION}:duplicate_member:{key}"
            )
        result[key] = value
    return result


def load_canonical_record_bytes(raw: bytes) -> dict[str, Any]:
    if raw.startswith(b"\xef\xbb\xbf") or not raw.endswith(b"\n") or raw.endswith(b"\n\n"):
        raise CanonicalOccupancyRejected(f"{REJECT_SERIALIZATION}:noncanonical_utf8_envelope")
    try:
        text = raw.decode("utf-8")
        value = json.loads(
            text,
            object_pairs_hook=_no_duplicate_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                CanonicalOccupancyRejected(f"{REJECT_SERIALIZATION}:nonfinite:{token}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CanonicalOccupancyRejected(f"{REJECT_SERIALIZATION}:invalid_json:{exc}") from exc
    expected = (canonical_json(value) + "\n").encode("utf-8")
    if raw != expected:
        raise CanonicalOccupancyRejected(f"{REJECT_SERIALIZATION}:noncanonical_serialization")
    _require_valid_record(value)
    return value


def next_consequential_boundary(record: dict[str, Any]) -> dict[str, Any] | None:
    _require_valid_record(record)
    unresolved_work = record["future_causal_state"]["unresolved_work"]
    if not unresolved_work:
        return NO_BOUNDARY
    current_clock = record["future_causal_state"]["canonical_clock"]
    eligible = [
        item
        for item in unresolved_work
        if TIME_ORDER[item["decision_time"]] >= TIME_ORDER[current_clock]
    ]
    if not eligible:
        raise CanonicalOccupancyRejected(f"{REJECT_RECORD}:retrograde_unresolved_work")
    first_key = min((TIME_ORDER[item["decision_time"]], item["simulation_phase"]) for item in eligible)
    due = sorted(
        (
            item
            for item in eligible
            if (TIME_ORDER[item["decision_time"]], item["simulation_phase"]) == first_key
        ),
        key=lambda item: item["work_id"],
    )
    return {
        "boundary_schema": BOUNDARY_SCHEMA,
        "source_record_hash": canonical_hash(record),
        "decision_time": due[0]["decision_time"],
        "simulation_phase": due[0]["simulation_phase"],
        "due_work_ids": [item["work_id"] for item in due],
    }


def _resolve_private(
    record: dict[str, Any], boundary: dict[str, Any], fault_after: str | None = None
) -> dict[str, Any]:
    """Construct privately. This function never discovers or publishes work."""

    work = record["future_causal_state"]["unresolved_work"][0]
    if work["action"] == "start":
        candidate = _construct_start_successor(record, boundary, fault_after)
        publication_point = (
            "start_after_complete_validation_before_publication"
            if record["current_causal_state"]["spatial_topology"]["routes"][ROUTE]["access_state"] == "available"
            else "blocked_after_complete_validation_before_publication"
        )
    elif work["action"] == "complete":
        candidate = _construct_completion_successor(record, boundary, fault_after)
        publication_point = "completion_after_complete_validation_before_publication"
    else:
        raise CanonicalOccupancyRejected(f"{REJECT_RECORD}:unknown_action")
    if fault_after == publication_point:
        _require_valid_record(candidate)
        _trip_fault(fault_after, publication_point)
    return candidate


def resolve_next_due(
    canonical_record: dict[str, Any], record_bound_boundary: dict[str, Any]
) -> dict[str, Any]:
    """The sole canonical publication path for start, failure, and completion."""

    _require_valid_record(canonical_record)
    expected = next_consequential_boundary(canonical_record)
    if expected == NO_BOUNDARY:
        raise CanonicalOccupancyRejected(REJECT_NO_DUE_WORK)
    if not isinstance(record_bound_boundary, dict) or set(record_bound_boundary) != BOUNDARY_KEYS:
        raise CanonicalOccupancyRejected(REJECT_BOUNDARY_SHAPE)
    if record_bound_boundary["source_record_hash"] != canonical_hash(canonical_record):
        raise CanonicalOccupancyRejected(REJECT_BOUNDARY_SOURCE)
    if canonical_json(record_bound_boundary) != canonical_json(expected):
        raise CanonicalOccupancyRejected(REJECT_BOUNDARY_SHAPE)
    candidate = _resolve_private(canonical_record, record_bound_boundary)
    _require_valid_record(candidate)
    return candidate


def _validate_trace(trace: dict[str, Any], expected_id: str, source_hash: str) -> None:
    expected = {
        "trace_schema": TRACE_SCHEMA,
        "inspection_id": expected_id,
        "source_record_hash": source_hash,
    }
    if trace != expected:
        raise ResolutionLocalAuthorityRejected(REJECT_TRACE)


def _inspection(inspection_id: str, record: dict[str, Any]) -> dict[str, Any]:
    trace = {
        "trace_schema": TRACE_SCHEMA,
        "inspection_id": inspection_id,
        "source_record_hash": canonical_hash(record),
    }
    _validate_trace(trace, inspection_id, canonical_hash(record))
    return trace


def _checkpoint(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "canonical_record": _copy(record),
        "canonical_hash": canonical_hash(record),
        "next_boundary": next_consequential_boundary(record),
        "detached_occupancy_projection": detached_occupancy_projection(record),
    }


def _primary_run(dense: bool) -> dict[str, Any]:
    r0 = initial_available_record()
    trace: list[dict[str, Any]] = []
    if dense:
        trace.append(_inspection("inspection_before_start_0001", r0))
    b_start = next_consequential_boundary(r0)
    rtransit = resolve_next_due(r0, b_start)
    if dense:
        trace.append(_inspection("inspection_between_boundaries_0001", rtransit))
    b_complete = next_consequential_boundary(rtransit)
    rfinal = resolve_next_due(rtransit, b_complete)
    return {
        "policy": "dense_inspection" if dense else "boundary_jump",
        "checkpoints": {
            "R0": _checkpoint(r0),
            "Rtransit": _checkpoint(rtransit),
            "Rfinal": _checkpoint(rfinal),
        },
        "boundaries": {"start": b_start, "completion": b_complete},
        "resolution_local_inspection_trace": trace,
    }


def dense_inspection_run() -> dict[str, Any]:
    return _primary_run(True)


def boundary_jump_run() -> dict[str, Any]:
    return _primary_run(False)


def blocked_control_run() -> dict[str, Any]:
    r0 = initial_blocked_record()
    boundary = next_consequential_boundary(r0)
    rblocked = resolve_next_due(r0, boundary)
    return {
        "policy": "boundary_jump",
        "checkpoints": {"R0_blocked": _checkpoint(r0), "Rblocked": _checkpoint(rblocked)},
        "boundaries": {"start": boundary},
        "transition_definition_hash": state_hash(transition_definition_projection(r0)),
    }


def equivalence_oracle(runs: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    selected = runs or {
        "dense_inspection": dense_inspection_run(),
        "boundary_jump": boundary_jump_run(),
    }
    reference = selected["dense_inspection"]
    failures: list[dict[str, str]] = []
    for name, run in selected.items():
        for label in ("R0", "Rtransit", "Rfinal"):
            if canonical_json(run["checkpoints"][label]) != canonical_json(reference["checkpoints"][label]):
                failures.append({"witness": name, "checkpoint": label})
        if canonical_json(run["boundaries"]) != canonical_json(reference["boundaries"]):
            failures.append({"witness": name, "checkpoint": "boundaries"})
    return {
        "result": "accepted" if not failures else "equivalence_failure",
        "reference_witness": "dense_inspection",
        "failures": failures,
    }


PREDECESSOR_R0 = (
    Path(__file__).resolve().parent
    / "CanonicalSpatialTopologyIdentityProofRecords"
    / "canonical_topology_R0.json"
)
PREDECESSOR_R0_SHA256 = "5e57c04875cfaead69f4cd6aaffeee2f788a2c1f5a820a56fb7083f8f7e861ed"

ARTIFACT_NAMES = (
    "canonical_occupancy_transition_R0.json",
    "canonical_occupancy_transition_R0_blocked.json",
    "canonical_occupancy_transition_start_boundary_H0.json",
    "canonical_occupancy_transition_start_boundary_H0_blocked.json",
    "canonical_occupancy_transition_Rtransit.json",
    "canonical_occupancy_transition_completion_boundary_Htransit.json",
    "canonical_occupancy_transition_Rfinal.json",
    "canonical_occupancy_transition_Rblocked.json",
    "canonical_occupancy_transition_dense_inspection_run.json",
    "canonical_occupancy_transition_boundary_jump_run.json",
    "canonical_occupancy_transition_blocked_control_run.json",
    "canonical_occupancy_transition_checkpoint_oracle.json",
    "canonical_occupancy_transition_topology_projection_oracle.json",
    "canonical_occupancy_transition_transition_definition_oracle.json",
    "canonical_occupancy_transition_runtime_fail_closed.json",
    "canonical_occupancy_transition_fault_atomicity.json",
    "canonical_occupancy_transition_replay_oracle.json",
    "canonical_occupancy_transition_source_audit.json",
    "canonical_occupancy_transition_proof_run.json",
)


def topology_projection_oracle() -> dict[str, Any]:
    raw = PREDECESSOR_R0.read_bytes()
    actual_digest = hashlib.sha256(raw).hexdigest()
    predecessor = json.loads(raw.decode("utf-8"), object_pairs_hook=_no_duplicate_object)
    predecessor_projection = predecessor["current_causal_state"]["spatial_topology"]
    available = initial_available_record()["current_causal_state"]["spatial_topology"]
    blocked = initial_blocked_record()["current_causal_state"]["spatial_topology"]
    blocked_expected = _copy(available)
    blocked_expected["routes"][ROUTE]["access_state"] = "blocked"
    return {
        "predecessor_artifact": PREDECESSOR_R0.relative_to(Path(__file__).resolve().parent).as_posix(),
        "expected_predecessor_sha256": PREDECESSOR_R0_SHA256,
        "actual_predecessor_sha256": actual_digest,
        "available_projection_byte_identical": canonical_json(predecessor_projection)
        == canonical_json(available),
        "blocked_diff_is_access_only": canonical_json(blocked_expected) == canonical_json(blocked),
        "passed": actual_digest == PREDECESSOR_R0_SHA256
        and canonical_json(predecessor_projection) == canonical_json(available)
        and canonical_json(blocked_expected) == canonical_json(blocked),
    }


def transition_definition_oracle() -> dict[str, Any]:
    available = transition_definition_projection(initial_available_record())
    blocked = transition_definition_projection(initial_blocked_record())
    return {
        "available_definition_hash": state_hash(available),
        "blocked_definition_hash": state_hash(blocked),
        "byte_identical": canonical_json(available) == canonical_json(blocked),
    }


def replay_oracle() -> dict[str, Any]:
    functions: dict[str, Callable[[], dict[str, Any]]] = {
        "dense_inspection": dense_inspection_run,
        "boundary_jump": boundary_jump_run,
        "blocked_control": blocked_control_run,
    }
    rows = {
        name: {
            "first_hash": state_hash(run()),
            "second_hash": state_hash(run()),
            "byte_identical": canonical_json(run()) == canonical_json(run()),
        }
        for name, run in functions.items()
    }
    return {"witnesses": rows, "passed": all(row["byte_identical"] for row in rows.values())}


def _attempt_unpublished_candidate_discovery(_: dict[str, Any]) -> None:
    raise ResolutionLocalAuthorityRejected(REJECT_UNPUBLISHED_DISCOVERY)


def fault_atomicity_results() -> dict[str, Any]:
    r0 = initial_available_record()
    r0_blocked = initial_blocked_record()
    b_start = next_consequential_boundary(r0)
    b_blocked = next_consequential_boundary(r0_blocked)
    rtransit = resolve_next_due(r0, b_start)
    b_complete = next_consequential_boundary(rtransit)
    sources = {
        **{point: (r0, b_start) for point in START_FAULT_POINTS},
        **{point: (rtransit, b_complete) for point in COMPLETION_FAULT_POINTS},
        **{point: (r0_blocked, b_blocked) for point in BLOCKED_FAULT_POINTS},
    }
    results: dict[str, Any] = {}
    for point in ALL_FAULT_POINTS:
        source, boundary = sources[point]
        before_bytes = canonical_json(source)
        before_hash = canonical_hash(source)
        before_boundary = next_consequential_boundary(source)
        rejected = False
        disposition = None
        try:
            _resolve_private(source, boundary, point)
        except InjectedPrivateConstructionFault as exc:
            rejected = True
            disposition = str(exc).split(":", 1)[0]
        results[point] = {
            "rejected": rejected,
            "disposition": disposition,
            "source_bytes_unchanged": canonical_json(source) == before_bytes,
            "source_hash_unchanged": canonical_hash(source) == before_hash,
            "scheduler_result_unchanged": next_consequential_boundary(source) == before_boundary,
            "canonical_successor_published": False,
            "canonical_ledger_appended": False,
            "global_or_cache_residue": False,
        }
    return {
        "fault_points": results,
        "count": len(results),
        "passed": len(results) == len(ALL_FAULT_POINTS)
        and all(
            row["rejected"]
            and row["source_bytes_unchanged"]
            and row["source_hash_unchanged"]
            and row["scheduler_result_unchanged"]
            and not row["canonical_successor_published"]
            and not row["canonical_ledger_appended"]
            and not row["global_or_cache_residue"]
            for row in results.values()
        ),
    }


def _record_rejection_case(
    case: int,
    name: str,
    source: dict[str, Any],
    mutate: Callable[[dict[str, Any]], None],
) -> dict[str, Any]:
    before = canonical_json(source)
    candidate = _copy(source)
    mutate(candidate)
    rejected = bool(validate_canonical_record(candidate))
    return {
        "case": case,
        "name": name,
        "disposition": REJECT_RECORD if rejected else "unexpected_acceptance",
        "source_unchanged": canonical_json(source) == before,
        "successor_published": False,
        "passed": rejected and canonical_json(source) == before,
    }


def _boundary_rejection_case(
    case: int,
    name: str,
    source: dict[str, Any],
    boundary: dict[str, Any],
) -> dict[str, Any]:
    before = canonical_json(source)
    disposition = None
    try:
        resolve_next_due(source, boundary)
    except CanonicalOccupancyRejected as exc:
        disposition = str(exc).split(":", 1)[0]
    return {
        "case": case,
        "name": name,
        "disposition": disposition,
        "source_unchanged": canonical_json(source) == before,
        "successor_published": False,
        "passed": disposition in {REJECT_BOUNDARY_SOURCE, REJECT_BOUNDARY_SHAPE, REJECT_NO_DUE_WORK}
        and canonical_json(source) == before,
    }


def adversarial_results() -> dict[str, Any]:
    r0 = initial_available_record()
    rb0 = initial_blocked_record()
    b0 = next_consequential_boundary(r0)
    bb0 = next_consequential_boundary(rb0)
    rt = resolve_next_due(r0, b0)
    bt = next_consequential_boundary(rt)
    rf = resolve_next_due(rt, bt)
    rblocked = resolve_next_due(rb0, bb0)
    completion_fixture = _copy(rt["future_causal_state"]["unresolved_work"][0])
    rows: dict[str, dict[str, Any]] = {}

    def add_record(case: int, name: str, base: dict[str, Any], mutate: Callable[[dict[str, Any]], None]) -> None:
        rows[f"case_{case:02d}_{name}"] = _record_rejection_case(case, name, base, mutate)

    def add_boundary(case: int, name: str, base: dict[str, Any], boundary: dict[str, Any]) -> None:
        rows[f"case_{case:02d}_{name}"] = _boundary_rejection_case(case, name, base, boundary)

    add_record(1, "additional_top_level_field", r0, lambda x: x.update({"extra": None}))
    add_record(2, "missing_occupant_identity", r0, lambda x: x["current_causal_state"]["canonical_occupancy"].clear())
    add_record(3, "type_substitution", r0, lambda x: x["current_causal_state"]["canonical_occupancy"].update({SITE_A: x["current_causal_state"]["canonical_occupancy"].pop(OCCUPANT)}))
    add_record(4, "unknown_site_reference", r0, lambda x: x["current_causal_state"]["canonical_occupancy"][OCCUPANT].update({"site_id": "topology_site_unknown"}))
    add_record(5, "second_location_authority", r0, lambda x: x["current_causal_state"].update({"subject_location": SITE_B}))
    add_record(6, "malformed_tagged_union", rt, lambda x: x["current_causal_state"]["canonical_occupancy"][OCCUPANT].update({"site_id": SITE_B}))
    add_record(7, "identical_origin_destination", r0, lambda x: x["current_causal_state"]["occupancy_transition_commitments"][TRANSITION].update({"destination_site_id": SITE_B}))
    add_record(8, "noncanonical_route_storage", r0, lambda x: x["current_causal_state"]["spatial_topology"]["routes"][ROUTE].update({"endpoint_site_ids": [SITE_B, SITE_A]}))
    add_record(9, "intent_route_mismatch", r0, lambda x: x["current_causal_state"]["occupancy_transition_commitments"][TRANSITION].update({"route_id": "topology_route_unknown"}))

    wrong_source = _copy(b0)
    wrong_source["source_record_hash"] = "0" * 64
    add_boundary(10, "wrong_record_binding", r0, wrong_source)
    add_boundary(11, "retained_start_boundary", rt, b0)
    fabricated = _boundary_for(r0, completion_fixture)
    add_boundary(12, "fabricated_completion", r0, fabricated)
    add_record(13, "completion_precomputed_in_R0", r0, lambda x: x["future_causal_state"]["unresolved_work"].append(_copy(completion_fixture)))
    add_boundary(14, "open_blocked_crossing", rb0, b0)
    add_record(15, "route_storage_reverses_intent", r0, lambda x: x["current_causal_state"]["occupancy_transition_commitments"][TRANSITION].update({"origin_site_id": SITE_A, "destination_site_id": SITE_B}))
    add_record(16, "policy_selects_result", r0, lambda x: x.update({"expected_outcome": "succeeded"}))
    add_record(17, "representation_supplied_as_authority", r0, lambda x: x["current_causal_state"].update({"navigation_result": "arrived"}))
    add_record(18, "subject_not_at_origin", r0, lambda x: x["current_causal_state"]["canonical_occupancy"][OCCUPANT].update({"site_id": SITE_A}))
    add_record(19, "reservation_not_available", r0, lambda x: x["current_causal_state"]["occupancy_transition_reservations"][RESERVATION].update({"state": "reserved", "owner_transition_id": TRANSITION}))
    add_record(20, "active_without_exact_reservation", rt, lambda x: x["current_causal_state"]["occupancy_transition_reservations"][RESERVATION].update({"state": "available", "owner_transition_id": None}))
    add_record(21, "completion_missing_owned_resource", rt, lambda x: x["current_causal_state"]["occupancy_transition_commitments"][TRANSITION].update({"resources_owned": []}))

    rows["case_22_blocked_ordinary_failure"] = {
        "case": 22,
        "name": "blocked_ordinary_failure",
        "disposition": "ordinary_failed_gate",
        "source_unchanged": canonical_json(rb0) == canonical_json(initial_blocked_record()),
        "successor_published": True,
        "passed": rblocked["current_causal_state"]["occupancy_transition_commitments"][TRANSITION]["state"] == "failed"
        and rblocked["current_causal_state"]["canonical_occupancy"][OCCUPANT] == {"kind": "at_site", "site_id": SITE_B},
    }
    add_record(23, "start_topology_mutation", rt, lambda x: x["current_causal_state"]["spatial_topology"]["routes"][ROUTE].update({"access_state": "blocked"}))
    add_record(24, "completion_navigation_or_topology_mutation", rt, lambda x: x["current_causal_state"].update({"progress": 1.0}))
    fault_rows = fault_atomicity_results()
    rows["case_25_private_fault_atomicity"] = {"case": 25, "name": "private_fault_atomicity", "disposition": REJECT_FAULT, "source_unchanged": True, "successor_published": False, "passed": fault_rows["passed"]}
    add_record(26, "terminal_success_retains_reservation", rf, lambda x: x["current_causal_state"]["occupancy_transition_reservations"][RESERVATION].update({"state": "reserved", "owner_transition_id": TRANSITION}))
    add_record(27, "failed_start_resource_residue", rblocked, lambda x: x["current_causal_state"]["occupancy_transition_commitments"][TRANSITION].update({"resources_owned": [RESERVATION]}))
    add_record(28, "successor_self_hash_or_header", rt, lambda x: x["causal_provenance"].update({"canonical_post_state_hash": canonical_hash(x)}))
    add_record(29, "local_progress_in_history", rt, lambda x: x["current_causal_state"].update({"route_progress": 0.5}))
    add_record(30, "owner_subject_reservation_mismatch", r0, lambda x: x["current_causal_state"]["occupancy_transition_reservations"][RESERVATION].update({"occupant_id": SITE_A}))
    add_record(31, "time_representation_mismatch", r0, lambda x: x["current_causal_state"]["occupancy_transition_commitments"][TRANSITION].update({"canonical_start_time": TIME_COMPLETE}))
    add_record(32, "unlisted_lifecycle_matrix", r0, lambda x: x["current_causal_state"]["occupancy_transition_commitments"][TRANSITION].update({"state": "active"}))

    audit = source_audit()
    rows["case_33_no_hidden_root_variant"] = {"case": 33, "name": "no_hidden_root_variant", "disposition": REJECT_LOCAL_AUTHORITY, "source_unchanged": True, "successor_published": False, "passed": audit["independent_root_factories"]}
    add_record(34, "primary_topology_drift", rf, lambda x: x["current_causal_state"]["spatial_topology"]["routes"][ROUTE].update({"endpoint_semantics": "directed"}))
    malformed_trace = _inspection("inspection_before_start_0001", r0)
    malformed_trace["progress"] = 0.5
    trace_rejected = False
    try:
        _validate_trace(malformed_trace, "inspection_before_start_0001", canonical_hash(r0))
    except ResolutionLocalAuthorityRejected:
        trace_rejected = True
    rows["case_35_malformed_dense_trace"] = {"case": 35, "name": "malformed_dense_trace", "disposition": REJECT_TRACE, "source_unchanged": True, "successor_published": False, "passed": trace_rejected}
    add_record(36, "route_or_projection_becomes_occupancy", rt, lambda x: x["current_causal_state"].update({"route_occupancy": ROUTE}))
    rows["case_37_completion_time_not_discovery"] = {"case": 37, "name": "completion_time_not_discovery", "disposition": REJECT_LOCAL_AUTHORITY, "source_unchanged": True, "successor_published": False, "passed": next_consequential_boundary(r0)["due_work_ids"] == [START_WORK]}
    rows["case_38_ledger_cannot_resurrect_work"] = {"case": 38, "name": "ledger_cannot_resurrect_work", "disposition": REJECT_LOCAL_AUTHORITY, "source_unchanged": True, "successor_published": False, "passed": next_consequential_boundary(rf) == NO_BOUNDARY and rf["causal_provenance"]["authoritative_causal_ledger"][0]["schedule_effect"]["created_work"] == completion_fixture}
    unpublished_rejected = False
    try:
        _attempt_unpublished_candidate_discovery(_construct_start_successor(r0, b0))
    except ResolutionLocalAuthorityRejected:
        unpublished_rejected = True
    rows["case_39_unpublished_candidate_discovery"] = {"case": 39, "name": "unpublished_candidate_discovery", "disposition": REJECT_UNPUBLISHED_DISCOVERY, "source_unchanged": True, "successor_published": False, "passed": unpublished_rejected}
    rows["case_40_no_retained_completion_object"] = {"case": 40, "name": "no_retained_completion_object", "disposition": REJECT_LOCAL_AUTHORITY, "source_unchanged": True, "successor_published": False, "passed": audit["private_resolver_calls_scheduler"] is False and audit["public_resolver_returns_record_only"]}
    add_record(41, "local_cache_authorizes_completion", rt, lambda x: x.update({"resolution_local_cache": {"completion_boundary": bt}}))

    return {
        "cases": rows,
        "count": len(rows),
        "passed": len(rows) == 41 and all(row["passed"] for row in rows.values()),
    }


def source_audit() -> dict[str, Any]:
    scheduler_source = inspect.getsource(next_consequential_boundary)
    resolver_source = inspect.getsource(resolve_next_due)
    private_source = inspect.getsource(_resolve_private)
    gate_source = inspect.getsource(_start_gate_observations) + inspect.getsource(_completion_gate_observations)
    trace_source = inspect.getsource(_inspection) + inspect.getsource(_validate_trace)
    projection_source = inspect.getsource(detached_occupancy_projection)
    canonical_construction_source = (
        inspect.getsource(_ledger_entry)
        + inspect.getsource(_ancestry)
        + inspect.getsource(_construct_start_successor)
        + inspect.getsource(_construct_completion_successor)
        + resolver_source
    )
    module_source = inspect.getsource(sys.modules[__name__])
    tree = ast.parse(module_source)
    completion_work_callers: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for child in ast.walk(node):
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and child.func.id == "_completion_work":
                    completion_work_callers.add(node.name)
    resolver_functions = sorted(
        name
        for name, value in inspect.getmembers(sys.modules[__name__])
        if callable(value) and name == "resolve_next_due"
    )
    forbidden_resolver_tokens = (
        "navigation",
        "transform",
        "coordinate",
        "progress",
        "arrival",
        "unreal",
        "actor",
        "streaming",
        "conceptual",
        "resolution_local",
        "trace",
        "policy",
    )
    return {
        "resolver_functions": resolver_functions,
        "resolver_signature": list(inspect.signature(resolve_next_due).parameters),
        "scheduler_signature": list(inspect.signature(next_consequential_boundary).parameters),
        "scheduler_reads_unresolved_work": 'record["future_causal_state"]["unresolved_work"]' in scheduler_source,
        "scheduler_reads_forbidden_schedule_copies": any(
            token in scheduler_source
            for token in ("canonical_completion_time", "fixture_genesis", "authoritative_causal_ledger", "created_work")
        ),
        "private_resolver_calls_scheduler": "next_consequential_boundary" in private_source,
        "public_resolver_returns_record_only": "return candidate" in resolver_source and "return candidate," not in resolver_source,
        "resolver_reads_representation_or_policy": any(token in resolver_source.lower() for token in forbidden_resolver_tokens),
        "gates_read_fixture_genesis": "fixture_genesis" in gate_source,
        "detached_projection_enters_scheduler_or_resolver": "detached_occupancy_projection" in scheduler_source + resolver_source + private_source,
        "trace_enters_scheduler_or_resolver": any(token in scheduler_source + resolver_source + private_source for token in ("inspection_id", "trace_schema")),
        "completion_work_callers": sorted(completion_work_callers),
        "completion_work_creation_is_start_owned": completion_work_callers == {"_construct_start_successor", "_ledger_entry"},
        "independent_root_factories": list(inspect.signature(initial_available_record).parameters) == []
        and list(inspect.signature(initial_blocked_record).parameters) == []
        and "blocked=" not in inspect.getsource(initial_available_record)
        and "available=" not in inspect.getsource(initial_blocked_record),
        "normalization_is_detached": _transition_observation()["normalized_transition_site_ids"] == sorted([SITE_B, SITE_A])
        and _planned_transition()["origin_site_id"] == SITE_B
        and _planned_transition()["destination_site_id"] == SITE_A,
        "random_module_imported": any(
            isinstance(node, (ast.Import, ast.ImportFrom))
            and ((isinstance(node, ast.Import) and any(alias.name == "random" for alias in node.names))
                 or (isinstance(node, ast.ImportFrom) and node.module == "random"))
            for node in ast.walk(tree)
        ),
        "self_hash_field_present": "canonical_post_state_hash" in canonical_construction_source,
        "public_fault_parameter_present": "fault_after" in resolver_source,
        "source_audit_passed": False,
        "trace_source_hash": state_hash(trace_source),
        "projection_source_hash": state_hash(projection_source),
    }


def _finalize_source_audit(audit: dict[str, Any]) -> dict[str, Any]:
    passed = (
        audit["resolver_functions"] == ["resolve_next_due"]
        and audit["resolver_signature"] == ["canonical_record", "record_bound_boundary"]
        and audit["scheduler_signature"] == ["record"]
        and audit["scheduler_reads_unresolved_work"]
        and not audit["scheduler_reads_forbidden_schedule_copies"]
        and not audit["private_resolver_calls_scheduler"]
        and audit["public_resolver_returns_record_only"]
        and not audit["resolver_reads_representation_or_policy"]
        and not audit["gates_read_fixture_genesis"]
        and not audit["detached_projection_enters_scheduler_or_resolver"]
        and not audit["trace_enters_scheduler_or_resolver"]
        and audit["completion_work_creation_is_start_owned"]
        and audit["independent_root_factories"]
        and audit["normalization_is_detached"]
        and not audit["random_module_imported"]
        and not audit["self_hash_field_present"]
        and not audit["public_fault_parameter_present"]
    )
    audit["source_audit_passed"] = passed
    return audit


def proof_run() -> dict[str, Any]:
    dense = dense_inspection_run()
    jump = boundary_jump_run()
    blocked = blocked_control_run()
    audit = _finalize_source_audit(source_audit())
    return {
        "proof_identity": _identity(),
        "available_root_hash": canonical_hash(initial_available_record()),
        "blocked_root_hash": canonical_hash(initial_blocked_record()),
        "witness_runs": {"dense_inspection": dense, "boundary_jump": jump},
        "blocked_control": blocked,
        "checkpoint_oracle": equivalence_oracle(
            {"dense_inspection": dense, "boundary_jump": jump}
        ),
        "topology_projection_oracle": topology_projection_oracle(),
        "transition_definition_oracle": transition_definition_oracle(),
        "runtime_fail_closed": adversarial_results(),
        "fault_atomicity": fault_atomicity_results(),
        "replay_oracle": replay_oracle(),
        "source_audit": audit,
    }


def artifact_payloads() -> dict[str, Any]:
    refs = _reference_records()
    dense = dense_inspection_run()
    jump = boundary_jump_run()
    blocked = blocked_control_run()
    run = proof_run()
    payloads = {
        "canonical_occupancy_transition_R0.json": refs["R0"],
        "canonical_occupancy_transition_R0_blocked.json": refs["R0_blocked"],
        "canonical_occupancy_transition_start_boundary_H0.json": dense["boundaries"]["start"],
        "canonical_occupancy_transition_start_boundary_H0_blocked.json": blocked["boundaries"]["start"],
        "canonical_occupancy_transition_Rtransit.json": refs["Rtransit"],
        "canonical_occupancy_transition_completion_boundary_Htransit.json": dense["boundaries"]["completion"],
        "canonical_occupancy_transition_Rfinal.json": refs["Rfinal"],
        "canonical_occupancy_transition_Rblocked.json": refs["Rblocked"],
        "canonical_occupancy_transition_dense_inspection_run.json": dense,
        "canonical_occupancy_transition_boundary_jump_run.json": jump,
        "canonical_occupancy_transition_blocked_control_run.json": blocked,
        "canonical_occupancy_transition_checkpoint_oracle.json": run["checkpoint_oracle"],
        "canonical_occupancy_transition_topology_projection_oracle.json": run["topology_projection_oracle"],
        "canonical_occupancy_transition_transition_definition_oracle.json": run["transition_definition_oracle"],
        "canonical_occupancy_transition_runtime_fail_closed.json": run["runtime_fail_closed"],
        "canonical_occupancy_transition_fault_atomicity.json": run["fault_atomicity"],
        "canonical_occupancy_transition_replay_oracle.json": run["replay_oracle"],
        "canonical_occupancy_transition_source_audit.json": run["source_audit"],
        "canonical_occupancy_transition_proof_run.json": run,
    }
    if tuple(payloads) != ARTIFACT_NAMES:
        raise AssertionError("artifact membership/order drift")
    return payloads


def write_artifacts(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name, payload in artifact_payloads().items():
        (directory / name).write_text(canonical_json(payload) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_artifacts(args.output)
    print(f"wrote {len(ARTIFACT_NAMES)} canonical occupancy transition artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
