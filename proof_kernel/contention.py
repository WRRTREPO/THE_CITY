"""Canonical resolver for the frozen E_AB bridge traversal contention proof.

This module is intentionally small.  It proves only that a physical bridge
destruction proposal and an already-due police edge-entry proposal can share
one deterministic canonical batch without transferring authority to Unreal.
"""

from __future__ import annotations

import argparse
import copy
import json
from collections import OrderedDict
from pathlib import Path
from typing import Any, Iterable

from kernel import canonical_json, state_hash
from roundtrip import (
    PROTOCOL_VERSION,
    PhysicalProposalContract,
    evidence_digest,
    physical_authorization_gates,
)


SCENARIO_ID = "ash-crossing-bridge-contention-v1"
SCENARIO_VERSION = "0.1.0"
SIMULATION_VERSION = "0.7.0-draft.13"
RECORD_SCHEMA = "BridgeAccessTraversalContentionRecord.v1"

CASE_DESTRUCTION_FIRST = "destruction_first"
CASE_ENTRY_FIRST = "entry_first"
PHYSICAL_PROPOSAL_ID = "physical_destroy_E_AB_contention_0001"
POLICE_PROPOSAL_ID = "police_dispatch_C_t0.enter_E_AB"
POLICE_COMMITMENT_ID = "police_dispatch_C_t0"
LEASE_ID = f"{POLICE_COMMITMENT_ID}:E_AB"

PHYSICAL_CONTRACT = PhysicalProposalContract(
    proposal_id=PHYSICAL_PROPOSAL_ID,
    simulation_version=SIMULATION_VERSION,
    runtime_instance_id="contention_proof_runtime_01",
    instigator={"kind": "crew", "id": "crew_01_to_04"},
    target={
        "kind": "bridge_access_point",
        "id": "bridge_access_point_E_AB_01",
        "route": "E_AB",
    },
    observed_outcome={"state": "destroyed", "event_sequence": 1},
    allowed_mutations=[
        "E_AB.open = false",
        "E_AB.capacity = 0",
        "E_AB.bridge_access_point.state = destroyed",
    ],
)


def _copy(value: Any) -> Any:
    return copy.deepcopy(value)


def _ordered_gates(scope: str, values: OrderedDict[str, bool] | dict[str, bool]) -> list[dict[str, Any]]:
    return [
        {
            "scope": scope,
            "name": name,
            "value": bool(passed),
            "passed": bool(passed),
            "result": "pass" if passed else "fail",
        }
        for name, passed in values.items()
    ]


def _first_failed(gates: Iterable[dict[str, Any]]) -> str | None:
    for gate in gates:
        if not gate["passed"]:
            return str(gate["name"])
    return None


def initial_record() -> dict[str, Any]:
    """The one R0 used by both canonical-ordering fixtures."""

    return {
        "record_schema": RECORD_SCHEMA,
        "record_name": "Ash Crossing bridge traversal contention",
        "scenario_id": SCENARIO_ID,
        "scenario_version": SCENARIO_VERSION,
        "simulation_version": SIMULATION_VERSION,
        "clock": "t0",
        "routes": {
            "E_AB": {
                "open": True,
                "capacity": 1,
                "bridge_access_point_state": "intact",
                "leases": [],
            },
            "E_BC": {"open": True, "capacity": 2, "leases": []},
        },
        "agents": {
            "police_unit_01": {
                "location": "A",
                "availability": "available",
                "units": 1,
                "dispatch_to_C": None,
            }
        },
        "commitments": {},
        "areas": {
            "B": {"fire_intensity": 4},
            "C": {
                "police_present": 0,
                "owner": "contested",
                "gang_control": 62,
                "rival_control": 38,
            },
        },
        "proposal_terminal_dispositions": {},
    }


def record_hash(record: dict[str, Any]) -> str:
    return state_hash(record)


def serializable_record(record: dict[str, Any]) -> dict[str, Any]:
    result = _copy(record)
    result["canonical_sha256"] = record_hash(record)
    return result


def make_physical_proposal(source_record_hash: str) -> dict[str, Any]:
    digest = evidence_digest(
        source_record_hash=source_record_hash,
        instigator_id=PHYSICAL_CONTRACT.instigator["id"],
        physical_actor_id=PHYSICAL_CONTRACT.target["id"],
        state=PHYSICAL_CONTRACT.observed_outcome["state"],
        event_sequence=PHYSICAL_CONTRACT.observed_outcome["event_sequence"],
    )
    return {
        "proposal_id": PHYSICAL_CONTRACT.proposal_id,
        "protocol_version": PROTOCOL_VERSION,
        "source": {
            "system": "crew_physical_simulation",
            "runtime_instance_id": PHYSICAL_CONTRACT.runtime_instance_id,
            "source_record_hash": source_record_hash,
            "source_simulation_version": SIMULATION_VERSION,
        },
        "instigator": _copy(PHYSICAL_CONTRACT.instigator),
        "target": _copy(PHYSICAL_CONTRACT.target),
        "observed_outcome": _copy(PHYSICAL_CONTRACT.observed_outcome),
        "evidence": {
            "physical_actor_id": PHYSICAL_CONTRACT.target["id"],
            "destruction_state": "destroyed",
            "evidence_digest": digest,
        },
        "proposed_mutations": _copy(PHYSICAL_CONTRACT.allowed_mutations),
    }


def make_police_entry_proposal(source_record_hash: str) -> dict[str, Any]:
    return {
        "proposal_id": POLICE_PROPOSAL_ID,
        "owner": "police_unit_01",
        "commitment": POLICE_COMMITMENT_ID,
        "source_snapshot_hash": source_record_hash,
        "route": "E_AB",
    }


def _entry(
    *,
    decision_time: str,
    actor: str,
    proposal_id: str,
    execution_key: str,
    batch_pre_state_hash: str,
    source_record_hash: str | None,
    working_pre_state_hash: str,
    working_post_state_hash: str,
    gates: list[dict[str, Any]],
    result: str,
    mutations: list[str],
    resources: list[str],
    observed_inputs: dict[str, Any],
    believed_inputs: dict[str, Any],
) -> dict[str, Any]:
    """A complete, inspectable causal-ledger entry."""

    return {
        "scenario_id": SCENARIO_ID,
        "scenario_version": SCENARIO_VERSION,
        "simulation_version": SIMULATION_VERSION,
        "decision_time": decision_time,
        "actor": actor,
        "proposal_id": proposal_id,
        "canonical_execution_key": execution_key,
        "batch_pre_state_hash": batch_pre_state_hash,
        "source_record_hash": source_record_hash,
        "working_pre_state_hash": working_pre_state_hash,
        "working_post_state_hash": working_post_state_hash,
        "observed_inputs": _copy(observed_inputs),
        "believed_inputs": _copy(believed_inputs),
        "gates": _copy(gates),
        "result": result,
        "mutations": mutations,
        "resources": resources,
    }


def _physical_working_gates(record: dict[str, Any]) -> OrderedDict[str, bool]:
    route = record["routes"]["E_AB"]
    return OrderedDict(
        [
            (
                "E_AB.bridge_access_intact",
                route["bridge_access_point_state"] == "intact",
            ),
            ("E_AB.open", route["open"] is True),
        ]
    )


def _police_batch_gates(proposal: dict[str, Any], batch_pre_state_hash: str) -> OrderedDict[str, bool]:
    return OrderedDict(
        [
            ("proposal_identity_exact", proposal.get("proposal_id") == POLICE_PROPOSAL_ID),
            (
                "source_snapshot_hash_matches_batch_pre_state",
                proposal.get("source_snapshot_hash") == batch_pre_state_hash,
            ),
            ("owner_and_commitment_exact", proposal.get("owner") == "police_unit_01" and proposal.get("commitment") == POLICE_COMMITMENT_ID),
            ("route_exact", proposal.get("route") == "E_AB"),
        ]
    )


def _police_working_gates(record: dict[str, Any]) -> OrderedDict[str, bool]:
    police = record["agents"]["police_unit_01"]
    route = record["routes"]["E_AB"]
    return OrderedDict(
        [
            ("police.availability", police["availability"] == "available"),
            ("E_AB.open", route["open"] is True),
            ("E_AB.new_admission_capacity", len(route["leases"]) < route["capacity"]),
        ]
    )


def _apply_physical_destruction(record: dict[str, Any]) -> None:
    route = record["routes"]["E_AB"]
    route["open"] = False
    route["capacity"] = 0
    route["bridge_access_point_state"] = "destroyed"


def _apply_police_entry(record: dict[str, Any]) -> None:
    police = record["agents"]["police_unit_01"]
    route = record["routes"]["E_AB"]
    police["availability"] = "reserved"
    route["leases"].append(LEASE_ID)
    record["commitments"][POLICE_COMMITMENT_ID] = {
        "state": "active",
        "route": ["E_AB", "E_BC"],
        "current_segment": "E_AB",
        "last_valid_location": "A",
        "next_gate": "E_BC at t1/20",
    }


def _apply_police_entry_failure(record: dict[str, Any], failed_gate: str) -> None:
    police = record["agents"]["police_unit_01"]
    police["location"] = "A"
    police["availability"] = "available"
    police["dispatch_to_C"] = {"result": "failed_gate", "failed_gate": failed_gate}


def resolve_t0_batch(
    case: str,
    physical_proposal: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve P and Q from one immutable R0 in a fixture-supplied order."""

    if case not in {CASE_DESTRUCTION_FIRST, CASE_ENTRY_FIRST}:
        raise ValueError(f"unknown case {case!r}")
    r0 = initial_record()
    batch_pre_state_hash = record_hash(r0)
    physical = _copy(physical_proposal or make_physical_proposal(batch_pre_state_hash))
    police = make_police_entry_proposal(batch_pre_state_hash)
    queued = (
        [("t0/15/E_AB/crew_01_to_04.destroy_E_AB", "physical", physical), ("t0/20/E_AB/police_unit_01.enter_E_AB", "police", police)]
        if case == CASE_DESTRUCTION_FIRST
        else [("t0/20/E_AB/police_unit_01.enter_E_AB", "police", police), ("t0/25/E_AB/crew_01_to_04.destroy_E_AB", "physical", physical)]
    )
    working = _copy(r0)
    ledger: list[dict[str, Any]] = []
    batch_header = {
        "decision_boundary": "t0",
        "transaction_pre_state_hash": batch_pre_state_hash,
        "input_sequence_id": "case_1_destruction_first" if case == CASE_DESTRUCTION_FIRST else "case_2_entry_first",
        "proposal_ids": [PHYSICAL_PROPOSAL_ID, POLICE_PROPOSAL_ID],
        "canonical_queue": [item[0] for item in queued],
    }

    for execution_key, kind, proposal in queued:
        working_pre_state_hash = record_hash(working)
        if kind == "physical":
            batch = physical_authorization_gates(
                proposal,
                contract=PHYSICAL_CONTRACT,
                batch_pre_state_hash=batch_pre_state_hash,
                proposal_terminal_dispositions=r0["proposal_terminal_dispositions"],
            )
            gates = _ordered_gates("batch_binding", batch)
            gates += _ordered_gates("working_revalidation", _physical_working_gates(working))
            accepted = all(gate["passed"] for gate in gates)
            if accepted:
                _apply_physical_destruction(working)
                result = "accepted"
                mutations = _copy(PHYSICAL_CONTRACT.allowed_mutations)
            else:
                result = "rejected"
                mutations = []
            working_post_state_hash = record_hash(working)
            ledger.append(
                _entry(
                    decision_time="t0",
                    actor="crew_physical_simulation",
                    proposal_id=str(proposal.get("proposal_id")),
                    execution_key=execution_key,
                    batch_pre_state_hash=batch_pre_state_hash,
                    source_record_hash=proposal.get("source", {}).get("source_record_hash"),
                    working_pre_state_hash=working_pre_state_hash,
                    working_post_state_hash=working_post_state_hash,
                    gates=gates,
                    result=result,
                    mutations=mutations,
                    resources=[],
                    observed_inputs={
                        "crew": proposal.get("instigator"),
                        "physical_actor_id": proposal.get("evidence", {}).get("physical_actor_id"),
                        "destruction_state": proposal.get("evidence", {}).get("destruction_state"),
                        "evidence_digest": proposal.get("evidence", {}).get("evidence_digest"),
                    },
                    believed_inputs={
                        "source_record_hash": proposal.get("source", {}).get("source_record_hash"),
                        "target": proposal.get("target"),
                        "outcome": proposal.get("observed_outcome"),
                    },
                )
            )
        else:
            batch = _police_batch_gates(proposal, batch_pre_state_hash)
            gates = _ordered_gates("batch_binding", batch)
            gates += _ordered_gates("working_revalidation", _police_working_gates(working))
            accepted = all(gate["passed"] for gate in gates)
            if accepted:
                _apply_police_entry(working)
                result = "accepted"
                mutations = [
                    "police_unit_01.availability = reserved",
                    f"E_AB.lease += {LEASE_ID}",
                    f"commitments.{POLICE_COMMITMENT_ID} = active",
                ]
                resources = [f"acquire {LEASE_ID}", "reserve police_unit_01"]
            else:
                failed_gate = _first_failed(gates) or "unknown"
                _apply_police_entry_failure(working, failed_gate)
                result = "failed_gate"
                mutations = [f"police_unit_01.dispatch_to_C.failed_gate = {failed_gate}"]
                resources = ["release police_unit_01"]
            working_post_state_hash = record_hash(working)
            ledger.append(
                _entry(
                    decision_time="t0",
                    actor="police_unit_01",
                    proposal_id=POLICE_PROPOSAL_ID,
                    execution_key=execution_key,
                    batch_pre_state_hash=batch_pre_state_hash,
                    source_record_hash=proposal["source_snapshot_hash"],
                    working_pre_state_hash=working_pre_state_hash,
                    working_post_state_hash=working_post_state_hash,
                    gates=gates,
                    result=result,
                    mutations=mutations,
                    resources=resources,
                    observed_inputs={"police.availability": "available", "E_AB.open": True},
                    believed_inputs={"source_snapshot_hash": proposal["source_snapshot_hash"]},
                )
            )

    return {
        "r0": r0,
        "batch_pre_state_hash": batch_pre_state_hash,
        "physical_proposal": physical,
        "police_proposal": police,
        "queue": [item[0] for item in queued],
        "batch_header": batch_header,
        "intermediate_record": working,
        "intermediate_record_hash": record_hash(working),
        "ledger": ledger,
    }


def resolve_t1_exit(intermediate_record: dict[str, Any]) -> dict[str, Any]:
    """Complete only E_AB in its own t1/15 transaction boundary."""

    exit_pre = _copy(intermediate_record)
    exit_pre["clock"] = "t1/15"
    batch_pre_state_hash = record_hash(exit_pre)
    working = _copy(exit_pre)
    police = working["agents"]["police_unit_01"]
    route = working["routes"]["E_AB"]
    commitment = working["commitments"].get(POLICE_COMMITMENT_ID, {})
    gates = _ordered_gates(
        "working_revalidation",
        OrderedDict(
            [
                ("commitment.active", commitment.get("state") == "active"),
                ("commitment.current_segment", commitment.get("current_segment") == "E_AB"),
                ("E_AB.lease_held", LEASE_ID in route["leases"]),
                ("police.availability", police["availability"] == "reserved"),
            ]
        ),
    )
    working_pre_state_hash = record_hash(working)
    if all(gate["passed"] for gate in gates):
        route["leases"].remove(LEASE_ID)
        police["location"] = "B"
        commitment["current_segment"] = None
        commitment["last_valid_location"] = "B"
        result = "accepted"
        mutations = [
            f"E_AB.lease -= {LEASE_ID}",
            "police_unit_01.location = B",
            f"commitments.{POLICE_COMMITMENT_ID}.current_segment = null",
            f"commitments.{POLICE_COMMITMENT_ID}.last_valid_location = B",
        ]
        resources = [f"release {LEASE_ID}"]
    else:
        result = "failed_gate"
        mutations = []
        resources = []
    working_post_state_hash = record_hash(working)
    batch_header = {
        "decision_boundary": "t1/15",
        "transaction_pre_state_hash": batch_pre_state_hash,
        "input_sequence_id": "case_2_entry_first_exit_E_AB",
        "proposal_ids": [f"{POLICE_COMMITMENT_ID}.exit_E_AB"],
        "canonical_queue": ["t1/15/E_AB/police_unit_01.exit_E_AB"],
    }
    ledger = _entry(
        decision_time="t1/15",
        actor="police_unit_01",
        proposal_id=f"{POLICE_COMMITMENT_ID}.exit_E_AB",
        execution_key="t1/15/E_AB/police_unit_01.exit_E_AB",
        batch_pre_state_hash=batch_pre_state_hash,
        source_record_hash=None,
        working_pre_state_hash=working_pre_state_hash,
        working_post_state_hash=working_post_state_hash,
        gates=gates,
        result=result,
        mutations=mutations,
        resources=resources,
        observed_inputs={"E_AB.lease": LEASE_ID, "E_AB.open": route["open"]},
        believed_inputs={"entered_segment_authority": LEASE_ID},
    )
    return {
        "batch_pre_state_hash": batch_pre_state_hash,
        "batch_header": batch_header,
        "exit_pre_record": exit_pre,
        "record": working,
        "record_hash": working_post_state_hash,
        "ledger": ledger,
    }


def run_case(case: str, physical_proposal: dict[str, Any] | None = None) -> dict[str, Any]:
    t0 = resolve_t0_batch(case, physical_proposal)
    exit_result = None
    final_record = t0["intermediate_record"]
    final_ledger = _copy(t0["ledger"])
    if case == CASE_ENTRY_FIRST and t0["ledger"][0 if t0["ledger"][0]["actor"] == "police_unit_01" else 1]["result"] == "accepted":
        exit_result = resolve_t1_exit(final_record)
        final_record = exit_result["record"]
        final_ledger.append(exit_result["ledger"])
    return {
        "scenario_id": SCENARIO_ID,
        "scenario_version": SCENARIO_VERSION,
        "simulation_version": SIMULATION_VERSION,
        "case": case,
        "r0": t0["r0"],
        "batch_pre_state_hash": t0["batch_pre_state_hash"],
        "queue": t0["queue"],
        "t0_batch": {"header": t0["batch_header"], "ledger": _copy(t0["ledger"])},
        "physical_proposal": t0["physical_proposal"],
        "police_proposal": t0["police_proposal"],
        "intermediate_record": t0["intermediate_record"],
        "intermediate_record_hash": t0["intermediate_record_hash"],
        "exit_transaction": exit_result,
        "final_record": final_record,
        "final_record_hash": record_hash(final_record),
        "ledger": final_ledger,
    }


def _write_json(path: Path, value: Any) -> None:
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def write_case_artifacts(
    case: str,
    output_directory: Path,
    physical_proposal: dict[str, Any] | None = None,
) -> dict[str, Path]:
    """Write sealed canonical artifacts; the caller owns evidence and manifesting."""

    output_directory.mkdir(parents=True, exist_ok=True)
    result = run_case(case, physical_proposal)
    paths = {
        "full": output_directory / f"{case}_run.json",
        "r0": output_directory / f"{case}_R0.json",
        "intermediate": output_directory / f"{case}_intermediate.json",
        "final": output_directory / f"{case}_final.json",
        "ledger": output_directory / f"{case}_ledger.json",
    }
    _write_json(paths["full"], result)
    _write_json(paths["r0"], serializable_record(result["r0"]))
    _write_json(paths["intermediate"], serializable_record(result["intermediate_record"]))
    _write_json(paths["final"], serializable_record(result["final_record"]))
    _write_json(paths["ledger"], result["ledger"])
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=[CASE_DESTRUCTION_FIRST, CASE_ENTRY_FIRST])
    parser.add_argument("output_directory", type=Path)
    arguments = parser.parse_args()
    paths = write_case_artifacts(arguments.case, arguments.output_directory)
    print(canonical_json({name: str(path) for name, path in paths.items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
