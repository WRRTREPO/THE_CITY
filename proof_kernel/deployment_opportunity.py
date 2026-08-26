"""Canonical resolver for the frozen crew deployment opportunity-cost proof.

The proof intentionally has one crew, one aircraft and one evidence-producing
domain.  It demonstrates that a destination choice consumes active-world time
without granting the Unreal runtime any authority to alter city truth.
"""

from __future__ import annotations

import argparse
import copy
import json
from collections import OrderedDict
from pathlib import Path
from typing import Any, Iterable

from kernel import canonical_json, state_hash
from roundtrip import PROTOCOL_VERSION, evidence_digest


SCENARIO_ID = "crew-deployment-opportunity-cost-v1"
SCENARIO_VERSION = "0.1.0"
SIMULATION_VERSION = "0.7.0-draft.16"
RECORD_SCHEMA = "CrewDeploymentOpportunityRecord.v1"
SEED = "crew-deployment-opportunity-cost-v1/0001"

CREW_ID = "crew_01_to_04"
AIRCRAFT_ID = "aircraft_01"
RUNTIME_INSTANCE_ID = "deployment_opportunity_runtime_01"

DEPLOY_B = "B"
DEPLOY_C = "C"
DEPLOY_D = "D"
DESTINATIONS = (DEPLOY_B, DEPLOY_C, DEPLOY_D)

FIRE_PROPOSAL_ID = "physical_contain_fire_B_deployment_0001"
DISRUPTION_PROPOSAL_ID = "physical_disrupt_seizure_C_deployment_0001"

PHYSICAL_CONTRACTS: dict[str, dict[str, Any]] = {
    DEPLOY_B: {
        "proposal_id": FIRE_PROPOSAL_ID,
        "target": {"kind": "fire_control", "id": "fire_control_valve_B_01", "area": "B"},
        "outcome": {"state": "contained", "event_sequence": 1},
        "mutations": ["B.fire_containment = true"],
    },
    DEPLOY_C: {
        "proposal_id": DISRUPTION_PROPOSAL_ID,
        "target": {"kind": "gang_signal_relay", "id": "gang_signal_relay_C_01", "area": "C"},
        "outcome": {"state": "disabled", "event_sequence": 1},
        "mutations": ["C.crew_disruption = true"],
    },
}

TIME_INDEX = {
    "t0/00": 0,
    "t0/01": 1,
    "t0/05": 5,
    "t0/10": 10,
    "t0/20": 20,
    "t0/25": 25,
    "t1/15": 75,
    "t1/20": 80,
    "t2/15": 135,
    "t2/40": 160,
}


def _copy(value: Any) -> Any:
    return copy.deepcopy(value)


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _ordered_gates(scope: str, values: OrderedDict[str, bool] | dict[str, bool]) -> list[dict[str, Any]]:
    return [
        {
            "scope": scope,
            "name": name,
            "value": bool(value),
            "passed": bool(value),
            "result": "pass" if value else "fail",
        }
        for name, value in values.items()
    ]


def _first_failed(gates: Iterable[dict[str, Any]]) -> str | None:
    return next((str(gate["name"]) for gate in gates if not gate["passed"]), None)


def _at_or_after(current: str, earliest: str) -> bool:
    return TIME_INDEX.get(current, -1) >= TIME_INDEX[earliest]


def initial_record() -> dict[str, Any]:
    """The identical R0 for all three crew-choice branches."""

    return {
        "record_schema": RECORD_SCHEMA,
        "record_name": "Ash Crossing — deployment opportunity seed",
        "scenario_id": SCENARIO_ID,
        "scenario_version": SCENARIO_VERSION,
        "simulation_version": SIMULATION_VERSION,
        "seed": SEED,
        "clock": "t0/00",
        "world": {"active_world": False},
        "resources": {CREW_ID: "available", AIRCRAFT_ID: "available"},
        "deployment": None,
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
            "B": {"fire_intensity": 4, "fire_containment": False},
            "C": {
                "police_present": 0,
                "owner": "contested",
                "gang_control": 62,
                "rival_control": 38,
                "crew_disruption": False,
            },
        },
        "proposal_terminal_dispositions": {},
    }


def record_hash(record: dict[str, Any]) -> str:
    return state_hash(record)


def serializable_record(record: dict[str, Any]) -> dict[str, Any]:
    serialized = _copy(record)
    serialized["canonical_sha256"] = record_hash(record)
    return serialized


def deterministic_scheduler_advance(parent_record: dict[str, Any], decision_boundary: str) -> dict[str, Any]:
    """Construct a later transaction pre-state by changing *only* its clock."""

    if decision_boundary not in TIME_INDEX:
        raise ValueError(f"unknown decision boundary {decision_boundary!r}")
    advanced = _copy(parent_record)
    advanced["clock"] = decision_boundary
    return advanced


def _scheduler_header(parent_record: dict[str, Any], decision_boundary: str, input_sequence_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    pre_state = deterministic_scheduler_advance(parent_record, decision_boundary)
    return pre_state, {
        "decision_boundary": decision_boundary,
        "parent_record_hash": record_hash(parent_record),
        "boundary_derivation": "scheduler_clock_advance",
        "transaction_pre_state_hash": record_hash(pre_state),
        "input_sequence_id": input_sequence_id,
    }


def _ledger_entry(
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
        "mutations": _copy(mutations),
        "resources": _copy(resources),
    }


def make_deployment_request(destination: str, source_record_hash: str) -> dict[str, Any]:
    return {
        "request_id": f"crew_deployment_{destination}_t0",
        "source": {"system": "crew_hub_command", "source_record_hash": source_record_hash},
        "crew_id": CREW_ID,
        "aircraft_id": AIRCRAFT_ID,
        "origin": "A",
        "destination": destination,
    }


def _deployment_gates(record: dict[str, Any], request: dict[str, Any], batch_pre_state_hash: str) -> OrderedDict[str, bool]:
    resources = record["resources"]
    return OrderedDict(
        [
            ("request_schema_exact", set(request) == {"request_id", "source", "crew_id", "aircraft_id", "origin", "destination"}),
            ("source_record_hash_matches_batch_pre_state", _as_dict(request.get("source")).get("source_record_hash") == batch_pre_state_hash),
            ("crew_available", request.get("crew_id") == CREW_ID and resources[CREW_ID] == "available"),
            ("aircraft_available", request.get("aircraft_id") == AIRCRAFT_ID and resources[AIRCRAFT_ID] == "available"),
            ("crew_has_no_active_deployment", record["deployment"] is None),
            ("destination_is_valid", request.get("destination") in DESTINATIONS),
            ("deployment_origin_is_hub", request.get("origin") == "A"),
        ]
    )


def accept_deployment(record: dict[str, Any], request: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Accept or reject one hub deployment request as a canonical transaction."""

    pre = _copy(record)
    batch_pre_state_hash = record_hash(pre)
    working = _copy(pre)
    gates = _ordered_gates("batch_binding", _deployment_gates(pre, request, batch_pre_state_hash))
    accepted = all(gate["passed"] for gate in gates)
    if accepted:
        destination = str(request["destination"])
        working["resources"][CREW_ID] = "reserved"
        working["resources"][AIRCRAFT_ID] = "reserved"
        working["world"]["active_world"] = True
        working["deployment"] = {
            "commitment_id": str(request["request_id"]),
            "crew_id": CREW_ID,
            "aircraft_id": AIRCRAFT_ID,
            "origin": "A",
            "destination": destination,
            "state": "active",
            "start_time": "t0/00",
            "interaction_domain": destination,
            "interaction_domain_available_at": "t0/05",
        }
        result = "accepted"
        mutations = [
            f"resources.{CREW_ID} = reserved",
            f"resources.{AIRCRAFT_ID} = reserved",
            "world.active_world = true",
            f"deployment = crew_deployment_{destination}_t0",
        ]
        resources = [f"reserve {CREW_ID}", f"reserve {AIRCRAFT_ID}"]
    else:
        result = "rejected"
        mutations = []
        resources = ["no resource acquired"]
    post_hash = record_hash(working)
    entry = _ledger_entry(
        decision_time=pre["clock"],
        actor="canonical_transaction_layer",
        proposal_id=str(request.get("request_id")),
        execution_key=f"{pre['clock']}/A/canonical.crew_deployment_request",
        batch_pre_state_hash=batch_pre_state_hash,
        source_record_hash=_as_dict(request.get("source")).get("source_record_hash"),
        working_pre_state_hash=batch_pre_state_hash,
        working_post_state_hash=post_hash,
        gates=gates,
        result=result,
        mutations=mutations,
        resources=resources,
        observed_inputs={"crew": CREW_ID, "aircraft": AIRCRAFT_ID, "origin": request.get("origin"), "destination": request.get("destination")},
        believed_inputs={"source_record_hash": _as_dict(request.get("source")).get("source_record_hash"), "deployment": pre["deployment"]},
    )
    return working, entry


def make_physical_proposal(domain: str, source_record_hash: str) -> dict[str, Any]:
    contract = PHYSICAL_CONTRACTS[domain]
    outcome = contract["outcome"]
    digest = evidence_digest(
        source_record_hash=source_record_hash,
        instigator_id=CREW_ID,
        physical_actor_id=contract["target"]["id"],
        state=outcome["state"],
        event_sequence=outcome["event_sequence"],
    )
    return {
        "proposal_id": contract["proposal_id"],
        "protocol_version": PROTOCOL_VERSION,
        "source": {
            "system": "crew_physical_simulation",
            "runtime_instance_id": RUNTIME_INSTANCE_ID,
            "source_record_hash": source_record_hash,
            "source_simulation_version": SIMULATION_VERSION,
        },
        "instigator": {"kind": "crew", "id": CREW_ID},
        "target": _copy(contract["target"]),
        "observed_outcome": _copy(outcome),
        "evidence": {
            "physical_actor_id": contract["target"]["id"],
            "outcome_state": outcome["state"],
            "evidence_digest": digest,
        },
        "proposed_mutations": _copy(contract["mutations"]),
    }


def _physical_gates(record: dict[str, Any], proposal: dict[str, Any], domain: str, batch_pre_state_hash: str) -> list[dict[str, Any]]:
    contract = PHYSICAL_CONTRACTS[domain]
    source = _as_dict(proposal.get("source"))
    evidence = _as_dict(proposal.get("evidence"))
    observed = _as_dict(proposal.get("observed_outcome"))
    deployment = record["deployment"]
    expected_digest = evidence_digest(
        source_record_hash=str(source.get("source_record_hash", "")),
        instigator_id=str(_as_dict(proposal.get("instigator")).get("id", "")),
        physical_actor_id=str(evidence.get("physical_actor_id", "")),
        state=str(observed.get("state", "")),
        event_sequence=observed.get("event_sequence") if isinstance(observed.get("event_sequence"), int) else -1,
    )
    exact_top_level = {"proposal_id", "protocol_version", "source", "instigator", "target", "observed_outcome", "evidence", "proposed_mutations"}
    static = OrderedDict(
        [
            ("schema_protocol_compatible", set(proposal) == exact_top_level and proposal.get("protocol_version") == PROTOCOL_VERSION and set(source) == {"system", "runtime_instance_id", "source_record_hash", "source_simulation_version"} and source.get("source_simulation_version") == SIMULATION_VERSION),
            ("source_identity_exact", source.get("system") == "crew_physical_simulation" and source.get("runtime_instance_id") == RUNTIME_INSTANCE_ID),
            ("source_record_hash_matches_batch_pre_state", source.get("source_record_hash") == batch_pre_state_hash),
            ("proposal_id_unseen", proposal.get("proposal_id") == contract["proposal_id"] and contract["proposal_id"] not in record["proposal_terminal_dispositions"]),
            ("instigator_exact", _as_dict(proposal.get("instigator")) == {"kind": "crew", "id": CREW_ID}),
            ("target_exact", _as_dict(proposal.get("target")) == contract["target"]),
            ("observed_outcome_exact", observed == contract["outcome"]),
            ("evidence_exact_and_digest_valid", set(evidence) == {"physical_actor_id", "outcome_state", "evidence_digest"} and evidence.get("physical_actor_id") == contract["target"]["id"] and evidence.get("outcome_state") == contract["outcome"]["state"] and evidence.get("evidence_digest") == expected_digest),
            ("allowed_effect_set_exact", proposal.get("proposed_mutations") == contract["mutations"]),
        ]
    )
    working = OrderedDict(
        [
            ("world.active_world", record["world"]["active_world"] is True),
            ("deployment.active", deployment is not None and deployment.get("state") == "active"),
            ("deployment.domain_matches_evidence", deployment is not None and deployment.get("interaction_domain") == domain),
            ("interaction_domain_available", deployment is not None and _at_or_after(record["clock"], str(deployment.get("interaction_domain_available_at")))),
        ]
    )
    return _ordered_gates("batch_binding", static) + _ordered_gates("working_revalidation", working)


def apply_physical_proposal(record: dict[str, Any], proposal: dict[str, Any], domain: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate all physical gates then atomically accept or reject one exact local fact."""

    pre = _copy(record)
    batch_pre_state_hash = record_hash(pre)
    working = _copy(pre)
    gates = _physical_gates(pre, proposal, domain, batch_pre_state_hash)
    accepted = all(gate["passed"] for gate in gates)
    contract = PHYSICAL_CONTRACTS[domain]
    if accepted:
        if domain == DEPLOY_B:
            working["areas"]["B"]["fire_containment"] = True
        else:
            working["areas"]["C"]["crew_disruption"] = True
        working["proposal_terminal_dispositions"][contract["proposal_id"]] = "accepted"
        result = "accepted"
        mutations = _copy(contract["mutations"])
    else:
        result = "rejected"
        mutations = []
    post_hash = record_hash(working)
    entry = _ledger_entry(
        decision_time=pre["clock"],
        actor="canonical_transaction_layer",
        proposal_id=str(proposal.get("proposal_id")),
        execution_key=f"{pre['clock']}/{domain}/canonical.apply_physical_proposal",
        batch_pre_state_hash=batch_pre_state_hash,
        source_record_hash=_as_dict(proposal.get("source")).get("source_record_hash"),
        working_pre_state_hash=batch_pre_state_hash,
        working_post_state_hash=post_hash,
        gates=gates,
        result=result,
        mutations=mutations,
        resources=[],
        observed_inputs={"physical_actor_id": _as_dict(proposal.get("evidence")).get("physical_actor_id"), "outcome_state": _as_dict(proposal.get("evidence")).get("outcome_state"), "deployment_domain": None if pre["deployment"] is None else pre["deployment"].get("interaction_domain")},
        believed_inputs={"source_record_hash": _as_dict(proposal.get("source")).get("source_record_hash"), "target": proposal.get("target"), "outcome": proposal.get("observed_outcome")},
    )
    return working, entry


def _autonomous_transaction(record: dict[str, Any], *, time: str, actor: str, proposal_id: str, execution_key: str, gates: OrderedDict[str, bool], effect: Any, observed: dict[str, Any], resources: list[str], input_sequence_id: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    pre, header = _scheduler_header(record, time, input_sequence_id)
    working = _copy(pre)
    evaluated = _ordered_gates("working_revalidation", gates)
    working_pre = record_hash(working)
    if all(gate["passed"] for gate in evaluated):
        mutations = effect(working)
        result = "accepted"
    else:
        mutations = []
        result = "failed_gate"
    working_post = record_hash(working)
    entry = _ledger_entry(
        decision_time=time,
        actor=actor,
        proposal_id=proposal_id,
        execution_key=execution_key,
        batch_pre_state_hash=header["transaction_pre_state_hash"],
        source_record_hash=None,
        working_pre_state_hash=working_pre,
        working_post_state_hash=working_post,
        gates=evaluated,
        result=result,
        mutations=mutations,
        resources=resources if result == "accepted" else ["no resource acquired"],
        observed_inputs=observed,
        believed_inputs=_copy(observed),
    )
    header["proposal_ids"] = [proposal_id]
    header["canonical_queue"] = [execution_key]
    return working, entry, header


def resolve_fire_spread(record: dict[str, Any], input_sequence_id: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    def effect(working: dict[str, Any]) -> list[str]:
        working["areas"]["B"]["fire_intensity"] = 5
        working["routes"]["E_AB"]["open"] = False
        working["routes"]["E_AB"]["capacity"] = 0
        return ["B.fire_intensity = 5", "E_AB.open = false", "E_AB.capacity = 0"]

    return _autonomous_transaction(
        record,
        time="t0/10",
        actor="fire_bridgehead",
        proposal_id="fire_bridgehead.spread",
        execution_key="t0/10/B/fire_bridgehead.spread",
        gates=OrderedDict([("B.fire_intensity == 4", record["areas"]["B"]["fire_intensity"] == 4), ("B.fire_containment == false", record["areas"]["B"]["fire_containment"] is False)]),
        effect=effect,
        observed={"B.fire_intensity": record["areas"]["B"]["fire_intensity"], "B.fire_containment": record["areas"]["B"]["fire_containment"]},
        resources=["consume B.fire fuel = 1"],
        input_sequence_id=input_sequence_id,
    )


def resolve_police_entry_ab(record: dict[str, Any], input_sequence_id: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    def effect(working: dict[str, Any]) -> list[str]:
        police = working["agents"]["police_unit_01"]
        route = working["routes"]["E_AB"]
        police["availability"] = "reserved"
        lease = "police_dispatch_C_t0:E_AB"
        route["leases"].append(lease)
        working["commitments"]["police_dispatch_C_t0"] = {"state": "active", "route": ["E_AB", "E_BC"], "current_segment": "E_AB", "last_valid_location": "A", "next_gate": "E_BC at t1/20"}
        return ["police_unit_01.availability = reserved", f"E_AB.lease += {lease}", "commitments.police_dispatch_C_t0 = active"]

    police = record["agents"]["police_unit_01"]
    route = record["routes"]["E_AB"]
    next_record, entry, header = _autonomous_transaction(
        record,
        time="t0/20",
        actor="police_unit_01",
        proposal_id="police_dispatch_C_t0.enter_E_AB",
        execution_key="t0/20/E_AB/police_unit_01.enter_E_AB",
        gates=OrderedDict([("police.availability", police["availability"] == "available"), ("E_AB.open", route["open"] is True), ("E_AB.new_admission_capacity", len(route["leases"]) < route["capacity"])]),
        effect=effect,
        observed={"police.availability": police["availability"], "E_AB.open": route["open"], "E_AB.capacity": route["capacity"]},
        resources=["reserve police_unit_01", "acquire police_dispatch_C_t0:E_AB"],
        input_sequence_id=input_sequence_id,
    )
    if entry["result"] == "failed_gate":
        failed_gate = _first_failed(entry["gates"]) or "unknown"
        next_record["agents"]["police_unit_01"]["dispatch_to_C"] = {"result": "failed_gate", "failed_gate": failed_gate}
        entry["mutations"] = [f"police_unit_01.dispatch_to_C.failed_gate = {failed_gate}"]
        entry["resources"] = ["no resource acquired"]
        entry["working_post_state_hash"] = record_hash(next_record)
    return next_record, entry, header


def resolve_police_exit_ab(record: dict[str, Any], input_sequence_id: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    lease = "police_dispatch_C_t0:E_AB"
    def effect(working: dict[str, Any]) -> list[str]:
        working["routes"]["E_AB"]["leases"].remove(lease)
        police = working["agents"]["police_unit_01"]
        police["location"] = "B"
        commitment = working["commitments"]["police_dispatch_C_t0"]
        commitment["current_segment"] = None
        commitment["last_valid_location"] = "B"
        return [f"E_AB.lease -= {lease}", "police_unit_01.location = B", "commitments.police_dispatch_C_t0.last_valid_location = B"]

    commitment = record["commitments"].get("police_dispatch_C_t0", {})
    route = record["routes"]["E_AB"]
    police = record["agents"]["police_unit_01"]
    return _autonomous_transaction(record, time="t1/15", actor="police_unit_01", proposal_id="police_dispatch_C_t0.exit_E_AB", execution_key="t1/15/E_AB/police_unit_01.exit_E_AB", gates=OrderedDict([("commitment.active", commitment.get("state") == "active"), ("commitment.current_segment", commitment.get("current_segment") == "E_AB"), ("E_AB.lease_held", lease in route["leases"]), ("police.availability", police["availability"] == "reserved")]), effect=effect, observed={"E_AB.lease": lease, "E_AB.open": route["open"]}, resources=[f"release {lease}"], input_sequence_id=input_sequence_id)


def resolve_police_entry_bc(record: dict[str, Any], input_sequence_id: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    lease = "police_dispatch_C_t0:E_BC"
    def effect(working: dict[str, Any]) -> list[str]:
        working["routes"]["E_BC"]["leases"].append(lease)
        commitment = working["commitments"]["police_dispatch_C_t0"]
        commitment["current_segment"] = "E_BC"
        return [f"E_BC.lease += {lease}", "commitments.police_dispatch_C_t0.current_segment = E_BC"]

    commitment = record["commitments"].get("police_dispatch_C_t0", {})
    route = record["routes"]["E_BC"]
    police = record["agents"]["police_unit_01"]
    return _autonomous_transaction(record, time="t1/20", actor="police_unit_01", proposal_id="police_dispatch_C_t0.enter_E_BC", execution_key="t1/20/E_BC/police_unit_01.enter_E_BC", gates=OrderedDict([("commitment.active", commitment.get("state") == "active"), ("police.at_B", police["location"] == "B"), ("E_BC.open", route["open"] is True), ("E_BC.new_admission_capacity", len(route["leases"]) < route["capacity"])]), effect=effect, observed={"police.location": police["location"], "E_BC.open": route["open"]}, resources=[f"acquire {lease}"], input_sequence_id=input_sequence_id)


def resolve_police_arrival_c(record: dict[str, Any], input_sequence_id: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    lease = "police_dispatch_C_t0:E_BC"
    def effect(working: dict[str, Any]) -> list[str]:
        working["routes"]["E_BC"]["leases"].remove(lease)
        police = working["agents"]["police_unit_01"]
        police["location"] = "C"
        police["availability"] = "deployed"
        working["areas"]["C"]["police_present"] = 1
        commitment = working["commitments"]["police_dispatch_C_t0"]
        commitment["state"] = "success"
        commitment["current_segment"] = None
        commitment["last_valid_location"] = "C"
        return [f"E_BC.lease -= {lease}", "police_unit_01.location = C", "C.police_present = 1", "commitments.police_dispatch_C_t0 = success"]

    commitment = record["commitments"].get("police_dispatch_C_t0", {})
    route = record["routes"]["E_BC"]
    return _autonomous_transaction(record, time="t2/15", actor="police_unit_01", proposal_id="police_dispatch_C_t0.exit_E_BC", execution_key="t2/15/E_BC/police_unit_01.exit_E_BC", gates=OrderedDict([("commitment.active", commitment.get("state") == "active"), ("commitment.current_segment", commitment.get("current_segment") == "E_BC"), ("E_BC.lease_held", lease in route["leases"])]), effect=effect, observed={"E_BC.lease": lease}, resources=[f"release {lease}"], input_sequence_id=input_sequence_id)


def resolve_gang_seizure(record: dict[str, Any], input_sequence_id: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    def effect(working: dict[str, Any]) -> list[str]:
        area = working["areas"]["C"]
        area["owner"] = "gang"
        area["gang_control"] = 74
        area["rival_control"] = 26
        return ["C.owner = gang", "C.gang_control = 74", "C.rival_control = 26"]

    area = record["areas"]["C"]
    return _autonomous_transaction(record, time="t2/40", actor="gang_docklands", proposal_id="gang_docklands.seize_C.complete", execution_key="t2/40/C/gang_docklands.seize_C.complete", gates=OrderedDict([("C.crew_disruption == false", area["crew_disruption"] is False), ("C.police_present == 0", area["police_present"] == 0), ("C.owner == contested", area["owner"] == "contested")]), effect=effect, observed={"C.crew_disruption": area["crew_disruption"], "C.police_present": area["police_present"], "C.owner": area["owner"]}, resources=["consume gang supply = 1", "transfer gang control threshold"], input_sequence_id=input_sequence_id)


def prepare_interaction_record(destination: str) -> dict[str, Any]:
    """Return the exact canonical record given to a fresh Unreal interaction process."""

    if destination not in (DEPLOY_B, DEPLOY_C):
        raise ValueError("only B and C have physical interaction records")
    r0 = initial_record()
    deployed, _ = accept_deployment(r0, make_deployment_request(destination, record_hash(r0)))
    if destination == DEPLOY_B:
        pre, _ = _scheduler_header(deployed, "t0/05", "prepare_B_interaction")
        return pre
    after_fire, _, _ = resolve_fire_spread(deployed, "prepare_C_fire")
    after_police, _, _ = resolve_police_entry_ab(after_fire, "prepare_C_police")
    pre, _ = _scheduler_header(after_police, "t0/25", "prepare_C_interaction")
    return pre


def _append_transaction(run: dict[str, Any], header: dict[str, Any], entry: dict[str, Any]) -> None:
    run["transactions"].append({"header": _copy(header), "ledger": [_copy(entry)]})
    run["ledger"].append(_copy(entry))


def run_branch(destination: str, physical_proposal: dict[str, Any] | None = None) -> dict[str, Any]:
    """Resolve a single B/C/D branch from one byte-identical R0."""

    if destination not in DESTINATIONS:
        raise ValueError(f"unknown destination {destination!r}")
    r0 = initial_record()
    run: dict[str, Any] = {
        "scenario_id": SCENARIO_ID,
        "scenario_version": SCENARIO_VERSION,
        "simulation_version": SIMULATION_VERSION,
        "r0": _copy(r0),
        "deployment_destination": destination,
        "transactions": [],
        "ledger": [],
    }
    deployment_request = make_deployment_request(destination, record_hash(r0))
    record, deployment_entry = accept_deployment(r0, deployment_request)
    deployment_header = {"decision_boundary": "t0/00", "parent_record_hash": record_hash(r0), "boundary_derivation": "initial_record", "transaction_pre_state_hash": record_hash(r0), "input_sequence_id": f"deploy_{destination}", "proposal_ids": [deployment_request["request_id"]], "canonical_queue": ["t0/00/A/canonical.crew_deployment_request"]}
    _append_transaction(run, deployment_header, deployment_entry)

    if destination == DEPLOY_B:
        interaction_pre, interaction_header = _scheduler_header(record, "t0/05", "deploy_B_physical_input")
        proposal = _copy(physical_proposal or make_physical_proposal(DEPLOY_B, record_hash(interaction_pre)))
        record, physical_entry = apply_physical_proposal(interaction_pre, proposal, DEPLOY_B)
        interaction_header["proposal_ids"] = [proposal.get("proposal_id")]
        interaction_header["canonical_queue"] = ["t0/05/B/canonical.apply_physical_proposal"]
        _append_transaction(run, interaction_header, physical_entry)
    record, fire_entry, fire_header = resolve_fire_spread(record, f"deploy_{destination}_fire")
    _append_transaction(run, fire_header, fire_entry)
    record, police_ab_entry, police_ab_header = resolve_police_entry_ab(record, f"deploy_{destination}_police_E_AB")
    _append_transaction(run, police_ab_header, police_ab_entry)

    if destination == DEPLOY_C:
        interaction_pre, interaction_header = _scheduler_header(record, "t0/25", "deploy_C_physical_input")
        proposal = _copy(physical_proposal or make_physical_proposal(DEPLOY_C, record_hash(interaction_pre)))
        record, physical_entry = apply_physical_proposal(interaction_pre, proposal, DEPLOY_C)
        interaction_header["proposal_ids"] = [proposal.get("proposal_id")]
        interaction_header["canonical_queue"] = ["t0/25/C/canonical.apply_physical_proposal"]
        _append_transaction(run, interaction_header, physical_entry)

    if record["commitments"].get("police_dispatch_C_t0", {}).get("state") == "active":
        record, exit_ab_entry, exit_ab_header = resolve_police_exit_ab(record, f"deploy_{destination}_police_exit_E_AB")
        _append_transaction(run, exit_ab_header, exit_ab_entry)
        record, entry_bc_entry, entry_bc_header = resolve_police_entry_bc(record, f"deploy_{destination}_police_enter_E_BC")
        _append_transaction(run, entry_bc_header, entry_bc_entry)
        record, arrival_c_entry, arrival_c_header = resolve_police_arrival_c(record, f"deploy_{destination}_police_exit_E_BC")
        _append_transaction(run, arrival_c_header, arrival_c_entry)

    record, gang_entry, gang_header = resolve_gang_seizure(record, f"deploy_{destination}_gang")
    _append_transaction(run, gang_header, gang_entry)
    run["final_record"] = _copy(record)
    run["final_record_hash"] = record_hash(record)
    return run


def run_exclusivity_rejection(destination: str = DEPLOY_B) -> dict[str, Any]:
    """Test-only witness that a live crew cannot create a second interaction domain."""

    r0 = initial_record()
    deployed, first_entry = accept_deployment(r0, make_deployment_request(destination, record_hash(r0)))
    later, header = _scheduler_header(deployed, "t0/01", "second_deployment_rejection")
    rejected, second_entry = accept_deployment(later, make_deployment_request(DEPLOY_C, record_hash(later)))
    return {"first_record": deployed, "first_ledger": first_entry, "second_pre_record": later, "second_header": header, "record": rejected, "second_ledger": second_entry}


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def write_interaction_records(output_directory: Path) -> dict[str, Path]:
    output_directory.mkdir(parents=True, exist_ok=True)
    paths = {
        DEPLOY_B: output_directory / "deployment_B_interaction_pre.json",
        DEPLOY_C: output_directory / "deployment_C_interaction_pre.json",
    }
    for destination, path in paths.items():
        _write_json(path, serializable_record(prepare_interaction_record(destination)))
    return paths


def write_branch_artifacts(destination: str, output_directory: Path, physical_proposal: dict[str, Any] | None = None) -> dict[str, Path]:
    output_directory.mkdir(parents=True, exist_ok=True)
    run = run_branch(destination, physical_proposal)
    paths = {
        "run": output_directory / f"deployment_{destination}_run.json",
        "r0": output_directory / f"deployment_{destination}_R0.json",
        "final": output_directory / f"deployment_{destination}_final.json",
        "ledger": output_directory / f"deployment_{destination}_ledger.json",
    }
    _write_json(paths["run"], run)
    _write_json(paths["r0"], serializable_record(run["r0"]))
    _write_json(paths["final"], serializable_record(run["final_record"]))
    _write_json(paths["ledger"], run["ledger"])
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    command = parser.add_subparsers(dest="command", required=True)
    interaction = command.add_parser("write-interaction-records")
    interaction.add_argument("--output-directory", type=Path, required=True)
    branch = command.add_parser("write-branch")
    branch.add_argument("destination", choices=DESTINATIONS)
    branch.add_argument("--output-directory", type=Path, required=True)
    branch.add_argument("--physical-proposal", type=Path)
    arguments = parser.parse_args()
    if arguments.command == "write-interaction-records":
        paths = write_interaction_records(arguments.output_directory)
    else:
        proposal = None if arguments.physical_proposal is None else json.loads(arguments.physical_proposal.read_text(encoding="utf-8"))
        paths = write_branch_artifacts(arguments.destination, arguments.output_directory, proposal)
    print(canonical_json({name: str(path) for name, path in paths.items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
