"""Canonical proof of bounded agent perception, selection, and commitment proposal.

The fixture is intentionally not a planner.  It demonstrates only one pure
selection policy over a declared perception projection, followed by canonical
proposal revalidation and one active commitment reservation.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, Iterable

from kernel import canonical_json, state_hash


SCENARIO_ID = "bounded-agent-commitment-selection-v1"
SCENARIO_VERSION = "0.1.0"
SIMULATION_VERSION = "0.7.0-draft.25"
POLICY_VERSION = "bounded-agent-selection-policy-v1"
RECORD_SCHEMA = "BoundedAgentCommitmentSelectionRecord.v1"
SEED = "bounded-agent-commitment-selection-v1/0001"
DECISION_BOUNDARY = "t0/00"

AGENT_ID = "agent_P"
REMOTE_ACTION = "secure_remote_capacity"
LOCAL_ACTION = "stabilize_local_capacity"
ACTIONS = (REMOTE_ACTION, LOCAL_ACTION)


def _copy(value: Any) -> Any:
    return copy.deepcopy(value)


def record_hash(record: dict[str, Any]) -> str:
    return state_hash(record)


def serializable_record(record: dict[str, Any]) -> dict[str, Any]:
    serialized = _copy(record)
    serialized["canonical_sha256"] = record_hash(record)
    return serialized


ACTION_DEFINITIONS: dict[str, dict[str, Any]] = {
    REMOTE_ACTION: {
        "id": REMOTE_ACTION,
        "requires": ["A_to_B.open", "A_to_B.capacity >= 1", "agent_P.available_transport >= 1"],
        "reserves": ["transport_unit_01", "A_to_B.capacity_unit_01"],
        "risk_cost": 1,
        "travel_cost": 2,
        "value_key": "remote_opportunity_value",
    },
    LOCAL_ACTION: {
        "id": LOCAL_ACTION,
        "requires": ["local_capacity_available", "local_work_unit_01.available"],
        "reserves": ["local_work_unit_01"],
        "risk_cost": 1,
        "travel_cost": 0,
        "value_key": "local_opportunity_value",
    },
}


def action_definition_hashes(definitions: dict[str, dict[str, Any]] | None = None) -> dict[str, str]:
    source = ACTION_DEFINITIONS if definitions is None else definitions
    return {action_id: state_hash(source[action_id]) for action_id in sorted(source)}


def initial_record(
    *,
    route_open: bool = True,
    hidden_fact_H: str = "H_alpha",
    remote_opportunity_value: int = 8,
) -> dict[str, Any]:
    return {
        "record_schema": RECORD_SCHEMA,
        "record_name": "Bounded agent selection seed",
        "scenario_id": SCENARIO_ID,
        "scenario_version": SCENARIO_VERSION,
        "simulation_version": SIMULATION_VERSION,
        "policy_version": POLICY_VERSION,
        "seed": SEED,
        "clock": DECISION_BOUNDARY,
        "agents": {
            AGENT_ID: {
                "location": "A",
                "available_transport": 1,
                "active_commitment_id": None,
                "goal": "preserve_operational_capacity",
            }
        },
        "graph": {
            "A_to_B": {
                "open": route_open,
                "capacity": 1,
                "leases": [],
            }
        },
        "resources": {
            "transport_unit_01": "available",
            "local_work_unit_01": "available",
        },
        "local_capacity_available": True,
        "opportunity_values": {
            "remote_opportunity_value": remote_opportunity_value,
            "local_opportunity_value": 5,
        },
        "hidden_fact_H": hidden_fact_H,
        "action_definitions": _copy(ACTION_DEFINITIONS),
        "action_definition_hashes": action_definition_hashes(),
        "commitments": {},
        "proposal_terminal_dispositions": {},
    }


def project_perception(record: dict[str, Any]) -> dict[str, Any]:
    """Return the complete, audited projection available to the selector."""

    agent = record["agents"][AGENT_ID]
    route = record["graph"]["A_to_B"]
    return {
        "agent": {
            "id": AGENT_ID,
            "available_transport": agent["available_transport"],
            "has_active_commitment": agent["active_commitment_id"] is not None,
        },
        "graph": {"A_to_B": {"open": route["open"], "capacity": route["capacity"]}},
        "resources": {
            "transport_unit_01": record["resources"]["transport_unit_01"],
            "local_work_unit_01": record["resources"]["local_work_unit_01"],
        },
        "local_capacity_available": record["local_capacity_available"],
        "opportunity_values": _copy(record["opportunity_values"]),
        "action_definition_hashes": _copy(record["action_definition_hashes"]),
    }


def _action_gates(perception: dict[str, Any], action_id: str) -> list[tuple[str, bool]]:
    if action_id == REMOTE_ACTION:
        return [
            ("A_to_B.open", perception["graph"]["A_to_B"]["open"]),
            ("A_to_B.capacity >= 1", perception["graph"]["A_to_B"]["capacity"] >= 1),
            ("agent_P.available_transport >= 1", perception["agent"]["available_transport"] >= 1),
            ("transport_unit_01.available", perception["resources"]["transport_unit_01"] == "available"),
            ("agent_P.has_no_active_commitment", not perception["agent"]["has_active_commitment"]),
        ]
    if action_id == LOCAL_ACTION:
        return [
            ("local_capacity_available", perception["local_capacity_available"]),
            ("local_work_unit_01.available", perception["resources"]["local_work_unit_01"] == "available"),
            ("agent_P.has_no_active_commitment", not perception["agent"]["has_active_commitment"]),
        ]
    raise ValueError(f"unknown action {action_id!r}")


def select_action(perception: dict[str, Any], definitions: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Pure deterministic selection.  It receives no authoritative record."""

    candidates: list[dict[str, Any]] = []
    for action_id in sorted(definitions):
        definition = definitions[action_id]
        gates = _action_gates(perception, action_id)
        goal_value = perception["opportunity_values"][definition["value_key"]]
        score = goal_value - definition["risk_cost"] - definition["travel_cost"]
        candidates.append(
            {
                "action_id": action_id,
                "definition_hash": state_hash(definition),
                "gates": [{"name": name, "passed": passed} for name, passed in gates],
                "feasible": all(passed for _, passed in gates),
                "goal_value": goal_value,
                "risk_cost": definition["risk_cost"],
                "travel_cost": definition["travel_cost"],
                "score": score,
            }
        )
    feasible = [candidate for candidate in candidates if candidate["feasible"]]
    selected = min(feasible, key=lambda candidate: (-candidate["score"], candidate["action_id"])) if feasible else None
    return {
        "policy_version": POLICY_VERSION,
        "perception": _copy(perception),
        "perception_hash": state_hash(perception),
        "candidates": candidates,
        "selected_action_id": selected["action_id"] if selected else None,
        "selected_score": selected["score"] if selected else None,
        "tie_break": "stable ascending action_id after descending score",
    }


def _commitment_id(action_id: str) -> str:
    return f"{AGENT_ID}.{action_id}.commitment.t0_00"


def make_selection_proposal(record: dict[str, Any]) -> dict[str, Any]:
    perception = project_perception(record)
    selection = select_action(perception, record["action_definitions"])
    action_id = selection["selected_action_id"]
    if action_id is None:
        commitment = None
    else:
        commitment = {
            "id": _commitment_id(action_id),
            "action_id": action_id,
            "state": "proposed",
            "reservations": _copy(record["action_definitions"][action_id]["reserves"]),
        }
    return {
        "proposal_id": f"{AGENT_ID}.selection_proposal.t0_00",
        "source_record_hash": record_hash(record),
        "actor": AGENT_ID,
        "policy_version": POLICY_VERSION,
        "selection": selection,
        "proposed_commitment": commitment,
    }


def _gate_entries(values: Iterable[tuple[str, bool]]) -> list[dict[str, Any]]:
    return [
        {"scope": "canonical_revalidation", "name": name, "value": value, "passed": value, "result": "pass" if value else "fail"}
        for name, value in values
    ]


def _revalidation_gates(record: dict[str, Any], proposal: dict[str, Any], expected: dict[str, Any]) -> list[dict[str, Any]]:
    action_id = expected["selected_action_id"]
    proposal_commitment = proposal.get("proposed_commitment")
    action_gates = _action_gates(project_perception(record), action_id) if action_id else []
    expected_commitment = (
        {
            "id": _commitment_id(action_id),
            "action_id": action_id,
            "state": "proposed",
            "reservations": _copy(record["action_definitions"][action_id]["reserves"]),
        }
        if action_id
        else None
    )
    return _gate_entries(
        [
            ("proposal_id_exact", proposal.get("proposal_id") == f"{AGENT_ID}.selection_proposal.t0_00"),
            ("source_record_hash_matches_batch_pre_state", proposal.get("source_record_hash") == record_hash(record)),
            ("actor_exact", proposal.get("actor") == AGENT_ID),
            ("policy_version_exact", proposal.get("policy_version") == POLICY_VERSION),
            ("action_definitions_exact", record["action_definitions"] == ACTION_DEFINITIONS),
            ("stored_action_definition_hashes_match_definitions", record["action_definition_hashes"] == action_definition_hashes(record["action_definitions"])),
            ("action_definition_hashes_exact", record["action_definition_hashes"] == action_definition_hashes()),
            ("perception_exact", proposal.get("selection", {}).get("perception") == project_perception(record)),
            ("perception_hash_exact", proposal.get("selection", {}).get("perception_hash") == state_hash(project_perception(record))),
            ("candidate_evaluation_exact", proposal.get("selection") == expected),
            ("proposed_commitment_exact", proposal_commitment == expected_commitment),
        ]
        + action_gates
    )


def apply_selection_proposal(record: dict[str, Any], proposal: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Canonically revalidate and create one active commitment, or reject."""

    batch_pre_state_hash = record_hash(record)
    expected = select_action(project_perception(record), record["action_definitions"])
    gates = _revalidation_gates(record, proposal, expected)
    working = _copy(record)
    working_pre_state_hash = record_hash(working)
    action_id = expected["selected_action_id"]
    if action_id is not None and all(gate["passed"] for gate in gates):
        commitment_id = _commitment_id(action_id)
        commitment = {
            "id": commitment_id,
            "action_id": action_id,
            "owner": AGENT_ID,
            "state": "active",
            "start_time": DECISION_BOUNDARY,
            "reservations": _copy(record["action_definitions"][action_id]["reserves"]),
        }
        working["commitments"][commitment_id] = commitment
        working["agents"][AGENT_ID]["active_commitment_id"] = commitment_id
        if action_id == REMOTE_ACTION:
            working["agents"][AGENT_ID]["available_transport"] = 0
            working["resources"]["transport_unit_01"] = f"reserved_by:{commitment_id}"
            working["graph"]["A_to_B"]["capacity"] = 0
            working["graph"]["A_to_B"]["leases"].append(commitment_id)
            mutations = [
                f"commitments.{commitment_id} = active",
                "agent_P.available_transport = 0",
                f"transport_unit_01 = reserved_by:{commitment_id}",
                "A_to_B.capacity = 0",
                f"A_to_B.leases += {commitment_id}",
            ]
        else:
            working["resources"]["local_work_unit_01"] = f"reserved_by:{commitment_id}"
            working["local_capacity_available"] = False
            mutations = [
                f"commitments.{commitment_id} = active",
                f"local_work_unit_01 = reserved_by:{commitment_id}",
                "local_capacity_available = false",
            ]
        working["proposal_terminal_dispositions"][proposal["proposal_id"]] = "accepted: active commitment owns explicit reservations"
        result = "accepted"
        resources = [f"reserve {item}" for item in commitment["reservations"]] + ["active commitment owns reservations"]
    else:
        working["proposal_terminal_dispositions"][proposal["proposal_id"]] = "rejected: no resource acquired; no commitment created"
        mutations = []
        result = "rejected"
        resources = ["no resource acquired", "no commitment created"]
    working_post_state_hash = record_hash(working)
    entry = {
        "scenario_id": SCENARIO_ID,
        "scenario_version": SCENARIO_VERSION,
        "simulation_version": SIMULATION_VERSION,
        "policy_version": POLICY_VERSION,
        "decision_time": DECISION_BOUNDARY,
        "actor": AGENT_ID,
        "proposal_id": proposal.get("proposal_id"),
        "canonical_execution_key": f"{DECISION_BOUNDARY}/selection/{AGENT_ID}",
        "batch_pre_state_hash": batch_pre_state_hash,
        "source_record_hash": proposal.get("source_record_hash"),
        "working_pre_state_hash": working_pre_state_hash,
        "working_post_state_hash": working_post_state_hash,
        "observed_inputs": _copy(proposal.get("selection", {}).get("perception", {})),
        "believed_inputs": _copy(proposal.get("selection", {}).get("perception", {})),
        "candidate_actions": _copy(proposal.get("selection", {}).get("candidates", [])),
        "selected_action_id": action_id,
        "selected_score": expected["selected_score"],
        "tie_break": expected["tie_break"],
        "gates": gates,
        "result": result,
        "mutations": mutations,
        "resources": resources,
    }
    return working, entry


def run_fixture(
    *,
    route_open: bool = True,
    hidden_fact_H: str = "H_alpha",
    remote_opportunity_value: int = 8,
) -> dict[str, Any]:
    r0 = initial_record(
        route_open=route_open,
        hidden_fact_H=hidden_fact_H,
        remote_opportunity_value=remote_opportunity_value,
    )
    proposal = make_selection_proposal(r0)
    final, entry = apply_selection_proposal(r0, proposal)
    return {
        "r0": r0,
        "proposal": proposal,
        "transactions": [
            {
                "header": {
                    "decision_boundary": DECISION_BOUNDARY,
                    "parent_record_hash": record_hash(r0),
                    "boundary_derivation": "agent_selection_canonical_transaction",
                    "transaction_pre_state_hash": record_hash(r0),
                },
                "ledger": [entry],
            }
        ],
        "ledger": [entry],
        "final_record": final,
    }


def primary_run() -> dict[str, Any]:
    return run_fixture()


def feasibility_counterfactual_run() -> dict[str, Any]:
    return run_fixture(route_open=False)


def hidden_a_run() -> dict[str, Any]:
    return run_fixture(hidden_fact_H="H_alpha")


def hidden_b_run() -> dict[str, Any]:
    return run_fixture(hidden_fact_H="H_beta")


def tie_run() -> dict[str, Any]:
    return run_fixture(remote_opportunity_value=7)


def semantic_selection(run: dict[str, Any]) -> dict[str, Any]:
    """Decision content excluding required full-record hash references."""

    proposal = run["proposal"]
    entry = run["ledger"][0]
    return {
        "perception": proposal["selection"]["perception"],
        "candidates": proposal["selection"]["candidates"],
        "selected_action_id": proposal["selection"]["selected_action_id"],
        "selected_score": proposal["selection"]["selected_score"],
        "proposed_commitment": proposal["proposed_commitment"],
        "ledger_selected_action_id": entry["selected_action_id"],
        "ledger_selected_score": entry["selected_score"],
        "ledger_mutations": entry["mutations"],
    }


def _write_json(path: Path, value: Any) -> None:
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def write_run_artifacts(name: str, run: dict[str, Any], directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    _write_json(directory / f"bounded_selection_{name}_R0.json", serializable_record(run["r0"]))
    _write_json(directory / f"bounded_selection_{name}_proposal.json", run["proposal"])
    _write_json(directory / f"bounded_selection_{name}_final.json", serializable_record(run["final_record"]))
    _write_json(directory / f"bounded_selection_{name}_ledger.json", run["ledger"])
    _write_json(directory / f"bounded_selection_{name}_run.json", run)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for name, run in (
        ("primary", primary_run()),
        ("feasibility", feasibility_counterfactual_run()),
        ("hidden_a", hidden_a_run()),
        ("hidden_b", hidden_b_run()),
        ("tie", tie_run()),
    ):
        write_run_artifacts(name, run, args.output)
    print(f"wrote bounded-agent selection artifacts to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
