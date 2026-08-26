"""Canonical resolver for the frozen crew-arrival live-commitment proof.

The fixture is deliberately narrow.  Its gang/relay nouns are not city
ontology: they demonstrate only that a completed causal history can remain
live through crew arrival, accept physical evidence, and resolve under one
canonical authority.
"""

from __future__ import annotations

import argparse
import copy
import json
from collections import OrderedDict
from pathlib import Path
from typing import Any, Callable, Iterable

from kernel import canonical_json, state_hash
from roundtrip import PROTOCOL_VERSION, evidence_digest


SCENARIO_ID = "crew-arrival-live-commitment-v1"
SCENARIO_VERSION = "0.1.0"
SIMULATION_VERSION = "0.7.0-draft.21"
RECORD_SCHEMA = "CrewArrivalLiveCommitmentRecord.v1"
SEED = "crew-arrival-live-commitment-v1/0001"

CREW_ID = "crew_01_to_04"
AIRCRAFT_ID = "aircraft_01"
RUNTIME_INSTANCE_ID = "live_commitment_runtime_01"
CLAIM_ID = "gang_claim_C_001"

BRANCH_CONTROL = "control"
BRANCH_EARLY = "early"
BRANCH_LATE = "late"
BRANCHES = (BRANCH_CONTROL, BRANCH_EARLY, BRANCH_LATE)

EARLY_PROPOSAL_ID = "physical_disable_claim_relay_C_live_0001"
LATE_PROPOSAL_ID = "physical_disable_claim_relay_C_live_0002"

TIME_INDEX = {
    "t0/00": 0,
    "t0/04": 4,
    "t0/08": 8,
    "t0/12": 12,
    "t0/16": 16,
    "t0/20": 20,
    "t0/21": 21,
    "t0/27": 27,
    "t0/40": 40,
}

PHYSICAL_CONTRACTS: dict[str, dict[str, Any]] = {
    "active": {
        "proposal_id": EARLY_PROPOSAL_ID,
        "claim_state": "active",
        "event_sequence": 1,
        "target": {"kind": "claim_relay", "id": "gang_claim_relay_C_01", "area": "C"},
        "outcome": {"state": "disabled", "event_sequence": 1},
        "mutations": ["C.relay.active = false"],
    },
    "succeeded": {
        "proposal_id": LATE_PROPOSAL_ID,
        "claim_state": "succeeded",
        "event_sequence": 2,
        "target": {"kind": "claim_relay", "id": "gang_claim_relay_C_01", "area": "C"},
        "outcome": {"state": "disabled", "event_sequence": 2},
        "mutations": ["C.relay.active = false"],
    },
}


def _copy(value: Any) -> Any:
    return copy.deepcopy(value)


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _ordered_gates(scope: str, values: OrderedDict[str, bool]) -> list[dict[str, Any]]:
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


def _at_or_after(current: str, earliest: str) -> bool:
    return TIME_INDEX.get(current, -1) >= TIME_INDEX.get(earliest, 10**9)


def record_hash(record: dict[str, Any]) -> str:
    return state_hash(record)


def serializable_record(record: dict[str, Any]) -> dict[str, Any]:
    serialized = _copy(record)
    serialized["canonical_sha256"] = record_hash(record)
    return serialized


def initial_record() -> dict[str, Any]:
    """Return the single R0 from which every branch derives."""

    return {
        "record_schema": RECORD_SCHEMA,
        "record_name": "Docklands Yard — live commitment seed",
        "scenario_id": SCENARIO_ID,
        "scenario_version": SCENARIO_VERSION,
        "simulation_version": SIMULATION_VERSION,
        "seed": SEED,
        "clock": "t0/00",
        "world": {"active_world": False},
        "resources": {
            CREW_ID: "available",
            AIRCRAFT_ID: "available",
            "gang_personnel_available": 6,
            "gang_claim_supply_available": 1,
        },
        "deployment": None,
        "areas": {
            "C": {
                "gang_intelligence": False,
                "gang_personnel_present": 0,
                "gang_presence": 0,
                "ingress_secured": False,
                "perimeter_established": False,
                "relay": {"active": False},
                "rival_resistance": 36,
                "owner": "contested",
                "gang_control": 64,
                "rival_control": 36,
            }
        },
        "commitments": {},
        "completed_history": [],
        "proposal_terminal_dispositions": {},
    }


def deterministic_scheduler_advance(parent_record: dict[str, Any], decision_boundary: str) -> dict[str, Any]:
    """Make a scheduler-owned boundary record by changing only its clock."""

    if decision_boundary not in TIME_INDEX:
        raise ValueError(f"unknown decision boundary {decision_boundary!r}")
    child = _copy(parent_record)
    child["clock"] = decision_boundary
    return child


def _scheduler_header(parent_record: dict[str, Any], decision_boundary: str, input_sequence_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    pre_state = deterministic_scheduler_advance(parent_record, decision_boundary)
    return pre_state, {
        "decision_boundary": decision_boundary,
        "parent_record_hash": record_hash(parent_record),
        "boundary_derivation": "scheduler_clock_advance",
        "transaction_pre_state_hash": record_hash(pre_state),
        "input_sequence_id": input_sequence_id,
    }


def _physical_header(record: dict[str, Any], input_sequence_id: str) -> dict[str, Any]:
    """A physical proposal is a new transaction, not a scheduler clock change."""

    current_hash = record_hash(record)
    return {
        "decision_boundary": record["clock"],
        "parent_record_hash": current_hash,
        "boundary_derivation": "physical_evidence_transaction",
        "transaction_pre_state_hash": current_hash,
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


def _append_transaction(run: dict[str, Any], header: dict[str, Any], entry: dict[str, Any]) -> None:
    run["transactions"].append({"header": _copy(header), "ledger": [_copy(entry)]})
    run["ledger"].append(_copy(entry))


def _canonical_action(
    record: dict[str, Any],
    *,
    time: str,
    actor: str,
    proposal_id: str,
    execution_key: str,
    gates: OrderedDict[str, bool],
    effect: Callable[[dict[str, Any]], list[str]],
    observed: dict[str, Any],
    resources: list[str],
    input_sequence_id: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    pre, header = _scheduler_header(record, time, input_sequence_id)
    working = _copy(pre)
    evaluated = _ordered_gates("working_revalidation", gates)
    working_pre_hash = record_hash(working)
    if all(gate["passed"] for gate in evaluated):
        mutations = effect(working)
        result = "accepted"
        terminal_resources = resources
    else:
        mutations = []
        result = "failed_gate"
        terminal_resources = ["no resource acquired"]
    working_post_hash = record_hash(working)
    entry = _ledger_entry(
        decision_time=time,
        actor=actor,
        proposal_id=proposal_id,
        execution_key=execution_key,
        batch_pre_state_hash=header["transaction_pre_state_hash"],
        source_record_hash=None,
        working_pre_state_hash=working_pre_hash,
        working_post_state_hash=working_post_hash,
        gates=evaluated,
        result=result,
        mutations=mutations,
        resources=terminal_resources,
        observed_inputs=observed,
        believed_inputs=observed,
    )
    header["proposal_ids"] = [proposal_id]
    header["canonical_queue"] = [execution_key]
    return working, entry, header


def _history_effect(history_id: str, mutation: Callable[[dict[str, Any]], list[str]]) -> Callable[[dict[str, Any]], list[str]]:
    def effect(working: dict[str, Any]) -> list[str]:
        mutations = mutation(working)
        working["completed_history"].append(history_id)
        return mutations + [f"completed_history += {history_id}"]

    return effect


def resolve_deployment(record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """The proof's crew reaches C only through a canonical commitment."""

    pre = _copy(record)
    batch_hash = record_hash(pre)
    working = _copy(pre)
    gates = _ordered_gates(
        "batch_binding",
        OrderedDict(
            [
                ("crew_available", pre["resources"][CREW_ID] == "available"),
                ("aircraft_available", pre["resources"][AIRCRAFT_ID] == "available"),
                ("no_active_deployment", pre["deployment"] is None),
            ]
        ),
    )
    if all(gate["passed"] for gate in gates):
        working["resources"][CREW_ID] = "reserved"
        working["resources"][AIRCRAFT_ID] = "reserved"
        working["world"]["active_world"] = True
        working["deployment"] = {
            "commitment_id": "crew_deployment_C_live_001",
            "crew_id": CREW_ID,
            "aircraft_id": AIRCRAFT_ID,
            "origin": "A",
            "destination": "C",
            "state": "active",
            "start_time": "t0/00",
            "physical_access_at": "t0/27",
        }
        result = "accepted"
        mutations = [
            f"resources.{CREW_ID} = reserved",
            f"resources.{AIRCRAFT_ID} = reserved",
            "world.active_world = true",
            "deployment = crew_deployment_C_live_001",
        ]
        resources = [f"reserve {CREW_ID}", f"reserve {AIRCRAFT_ID}"]
    else:
        result = "rejected"
        mutations = []
        resources = ["no resource acquired"]
    post_hash = record_hash(working)
    entry = _ledger_entry(
        decision_time="t0/00",
        actor="canonical_transaction_layer",
        proposal_id="crew_deployment_C_live_001",
        execution_key="t0/00/A/canonical.crew_deployment_request",
        batch_pre_state_hash=batch_hash,
        source_record_hash=batch_hash,
        working_pre_state_hash=batch_hash,
        working_post_state_hash=post_hash,
        gates=gates,
        result=result,
        mutations=mutations,
        resources=resources,
        observed_inputs={"crew": CREW_ID, "aircraft": AIRCRAFT_ID, "destination": "C"},
        believed_inputs={"deployment": pre["deployment"], "source_record_hash": batch_hash},
    )
    header = {
        "decision_boundary": "t0/00",
        "parent_record_hash": batch_hash,
        "boundary_derivation": "initial_record",
        "transaction_pre_state_hash": batch_hash,
        "input_sequence_id": "crew_deployment_C_live_001",
        "proposal_ids": ["crew_deployment_C_live_001"],
        "canonical_queue": ["t0/00/A/canonical.crew_deployment_request"],
    }
    return working, entry, header


def resolve_survey(record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    return _canonical_action(
        record,
        time="t0/04",
        actor="gang_docklands",
        proposal_id="gang_survey_C_001",
        execution_key="t0/04/C/gang_docklands.survey_C",
        gates=OrderedDict([("C.gang_intelligence == false", record["areas"]["C"]["gang_intelligence"] is False)]),
        effect=_history_effect("survey_C", lambda working: _set_value(working["areas"]["C"], "gang_intelligence", True, "C.gang_intelligence = true")),
        observed={"C.gang_intelligence": record["areas"]["C"]["gang_intelligence"]},
        resources=["consume gang survey effort = 1"],
        input_sequence_id="prehistory_survey",
    )


def _set_value(scope: dict[str, Any], key: str, value: Any, mutation: str) -> list[str]:
    scope[key] = value
    return [mutation]


def resolve_marshal(record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    def effect(working: dict[str, Any]) -> list[str]:
        working["resources"]["gang_personnel_available"] -= 6
        working["areas"]["C"]["gang_personnel_present"] = 6
        working["completed_history"].append("marshal_C")
        return ["gang_personnel_available -= 6", "C.gang_personnel_present = 6", "completed_history += marshal_C"]

    return _canonical_action(
        record,
        time="t0/08",
        actor="gang_docklands",
        proposal_id="gang_marshal_C_001",
        execution_key="t0/08/C/gang_docklands.marshal_C",
        gates=OrderedDict([("C.gang_intelligence", record["areas"]["C"]["gang_intelligence"] is True), ("gang.personnel_available >= 6", record["resources"]["gang_personnel_available"] >= 6)]),
        effect=effect,
        observed={"C.gang_intelligence": record["areas"]["C"]["gang_intelligence"], "gang_personnel_available": record["resources"]["gang_personnel_available"]},
        resources=["transfer 6 gang personnel to C"],
        input_sequence_id="prehistory_marshal",
    )


def resolve_ingress(record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    return _canonical_action(
        record,
        time="t0/12",
        actor="gang_docklands",
        proposal_id="gang_secure_ingress_C_001",
        execution_key="t0/12/C/gang_docklands.secure_ingress_C",
        gates=OrderedDict([("C.gang_personnel_present >= 6", record["areas"]["C"]["gang_personnel_present"] >= 6), ("C.ingress_secured == false", record["areas"]["C"]["ingress_secured"] is False)]),
        effect=_history_effect("secure_ingress_C", lambda working: _set_value(working["areas"]["C"], "ingress_secured", True, "C.ingress_secured = true")),
        observed={"C.gang_personnel_present": record["areas"]["C"]["gang_personnel_present"], "C.ingress_secured": record["areas"]["C"]["ingress_secured"]},
        resources=["consume gang ingress effort = 1"],
        input_sequence_id="prehistory_ingress",
    )


def resolve_perimeter(record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    return _canonical_action(
        record,
        time="t0/16",
        actor="gang_docklands",
        proposal_id="gang_establish_perimeter_C_001",
        execution_key="t0/16/C/gang_docklands.establish_perimeter_C",
        gates=OrderedDict([("C.ingress_secured", record["areas"]["C"]["ingress_secured"] is True), ("C.perimeter_established == false", record["areas"]["C"]["perimeter_established"] is False)]),
        effect=_history_effect("establish_perimeter_C", lambda working: _set_value(working["areas"]["C"], "perimeter_established", True, "C.perimeter_established = true")),
        observed={"C.ingress_secured": record["areas"]["C"]["ingress_secured"], "C.perimeter_established": record["areas"]["C"]["perimeter_established"]},
        resources=["consume gang perimeter effort = 1"],
        input_sequence_id="prehistory_perimeter",
    )


def resolve_relay_activation(record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    def mutation(working: dict[str, Any]) -> list[str]:
        working["areas"]["C"]["relay"]["active"] = True
        return ["C.relay.active = true"]

    return _canonical_action(
        record,
        time="t0/20",
        actor="gang_docklands",
        proposal_id="gang_activate_relay_C_001",
        execution_key="t0/20/C/gang_docklands.activate_relay_C",
        gates=OrderedDict([("C.perimeter_established", record["areas"]["C"]["perimeter_established"] is True), ("C.relay.active == false", record["areas"]["C"]["relay"]["active"] is False)]),
        effect=_history_effect("activate_relay_C", mutation),
        observed={"C.perimeter_established": record["areas"]["C"]["perimeter_established"], "C.relay.active": record["areas"]["C"]["relay"]["active"]},
        resources=["consume gang relay activation effort = 1"],
        input_sequence_id="prehistory_relay",
    )


def resolve_claim_start(record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    def effect(working: dict[str, Any]) -> list[str]:
        working["resources"]["gang_claim_supply_available"] -= 1
        working["commitments"][CLAIM_ID] = {
            "state": "active",
            "owner": "gang_docklands",
            "start_time": "t0/21",
            "resolution_time": "t0/40",
            "reserved_personnel": 6,
            "reserved_supply": 1,
            "terminal_resource_disposition": None,
        }
        return ["gang_claim_supply_available -= 1", f"commitments.{CLAIM_ID} = active"]

    area = record["areas"]["C"]
    return _canonical_action(
        record,
        time="t0/21",
        actor="gang_docklands",
        proposal_id=CLAIM_ID + ".begin",
        execution_key="t0/21/C/gang_docklands.begin_claim_C",
        gates=OrderedDict([("C.relay.active", area["relay"]["active"] is True), ("C.perimeter_established", area["perimeter_established"] is True), ("C.ingress_secured", area["ingress_secured"] is True), ("C.gang_personnel_present >= 6", area["gang_personnel_present"] >= 6), ("gang.claim_supply_available >= 1", record["resources"]["gang_claim_supply_available"] >= 1), ("claim.absent", CLAIM_ID not in record["commitments"])]),
        effect=effect,
        observed={"C.relay.active": area["relay"]["active"], "C.perimeter_established": area["perimeter_established"], "C.ingress_secured": area["ingress_secured"], "C.gang_personnel_present": area["gang_personnel_present"], "gang_claim_supply_available": record["resources"]["gang_claim_supply_available"]},
        resources=["reserve 6 C gang personnel", "reserve 1 gang claim supply"],
        input_sequence_id="claim_begin",
    )


def physical_access(record: dict[str, Any]) -> bool:
    deployment = _as_dict(record.get("deployment"))
    return (
        record.get("world", {}).get("active_world") is True
        and deployment.get("state") == "active"
        and deployment.get("destination") == "C"
        and _at_or_after(str(record.get("clock")), str(deployment.get("physical_access_at")))
    )


def prepare_arrival_record() -> dict[str, Any]:
    """Return Rarrival, whose only difference from t0/21 is its clock."""

    record = initial_record()
    record, _, _ = resolve_deployment(record)
    for resolver in (resolve_survey, resolve_marshal, resolve_ingress, resolve_perimeter, resolve_relay_activation, resolve_claim_start):
        record, _, _ = resolver(record)
    arrival, _ = _scheduler_header(record, "t0/27", "arrival_scheduler_derivation")
    return arrival


def make_physical_proposal(claim_state: str, source_record_hash: str) -> dict[str, Any]:
    contract = PHYSICAL_CONTRACTS[claim_state]
    digest = evidence_digest(
        source_record_hash=source_record_hash,
        instigator_id=CREW_ID,
        physical_actor_id=contract["target"]["id"],
        state=contract["outcome"]["state"],
        event_sequence=contract["event_sequence"],
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
        "observed_outcome": _copy(contract["outcome"]),
        "evidence": {
            "physical_actor_id": contract["target"]["id"],
            "outcome_state": contract["outcome"]["state"],
            "evidence_digest": digest,
        },
        "proposed_mutations": _copy(contract["mutations"]),
    }


def _contract_for_proposal(proposal: dict[str, Any]) -> dict[str, Any] | None:
    proposal_id = proposal.get("proposal_id")
    return next((contract for contract in PHYSICAL_CONTRACTS.values() if contract["proposal_id"] == proposal_id), None)


def _physical_gates(record: dict[str, Any], proposal: dict[str, Any], batch_hash: str) -> list[dict[str, Any]]:
    contract = _contract_for_proposal(proposal)
    source = _as_dict(proposal.get("source"))
    instigator = _as_dict(proposal.get("instigator"))
    target = _as_dict(proposal.get("target"))
    observed = _as_dict(proposal.get("observed_outcome"))
    evidence = _as_dict(proposal.get("evidence"))
    expected_digest = evidence_digest(
        source_record_hash=str(source.get("source_record_hash", "")),
        instigator_id=str(instigator.get("id", "")),
        physical_actor_id=str(evidence.get("physical_actor_id", "")),
        state=str(observed.get("state", "")),
        event_sequence=observed.get("event_sequence") if isinstance(observed.get("event_sequence"), int) else -1,
    )
    exact_top_level = {"proposal_id", "protocol_version", "source", "instigator", "target", "observed_outcome", "evidence", "proposed_mutations"}
    static = OrderedDict(
        [
            ("schema_protocol_compatible", set(proposal) == exact_top_level and proposal.get("protocol_version") == PROTOCOL_VERSION and set(source) == {"system", "runtime_instance_id", "source_record_hash", "source_simulation_version"} and source.get("source_simulation_version") == SIMULATION_VERSION),
            ("source_identity_exact", source.get("system") == "crew_physical_simulation" and source.get("runtime_instance_id") == RUNTIME_INSTANCE_ID),
            ("source_record_hash_matches_batch_pre_state", source.get("source_record_hash") == batch_hash),
            ("proposal_id_unseen", contract is not None and proposal.get("proposal_id") not in record["proposal_terminal_dispositions"]),
            ("instigator_exact", instigator == {"kind": "crew", "id": CREW_ID}),
            ("target_exact", contract is not None and target == contract["target"]),
            ("observed_outcome_exact", contract is not None and observed == contract["outcome"]),
            ("evidence_exact_and_digest_valid", contract is not None and set(evidence) == {"physical_actor_id", "outcome_state", "evidence_digest"} and evidence.get("physical_actor_id") == contract["target"]["id"] and evidence.get("outcome_state") == contract["outcome"]["state"] and evidence.get("evidence_digest") == expected_digest),
            ("allowed_effect_set_exact", contract is not None and proposal.get("proposed_mutations") == contract["mutations"]),
        ]
    )
    claim = _as_dict(record["commitments"].get(CLAIM_ID))
    area = record["areas"]["C"]
    working = OrderedDict(
        [
            ("physical_access_C", physical_access(record)),
            ("claim_state_matches_contract", contract is not None and claim.get("state") == contract["claim_state"]),
            ("relay_active", area["relay"]["active"] is True),
            ("post_claim_owner_is_gang", contract is None or contract["claim_state"] != "succeeded" or area["owner"] == "gang"),
        ]
    )
    return _ordered_gates("batch_binding", static) + _ordered_gates("working_revalidation", working)


def apply_physical_proposal(record: dict[str, Any], proposal: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Validate every physical-evidence gate before an atomic city mutation."""

    pre = _copy(record)
    batch_hash = record_hash(pre)
    header = _physical_header(pre, "physical_relay_evidence")
    working = _copy(pre)
    gates = _physical_gates(pre, proposal, batch_hash)
    contract = _contract_for_proposal(proposal)
    if all(gate["passed"] for gate in gates) and contract is not None:
        working["areas"]["C"]["relay"]["active"] = False
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
        execution_key=f"{pre['clock']}/C/canonical.apply_physical_relay_proposal",
        batch_pre_state_hash=batch_hash,
        source_record_hash=_as_dict(proposal.get("source")).get("source_record_hash"),
        working_pre_state_hash=batch_hash,
        working_post_state_hash=post_hash,
        gates=gates,
        result=result,
        mutations=mutations,
        resources=[],
        observed_inputs={"physical_actor_id": _as_dict(proposal.get("evidence")).get("physical_actor_id"), "outcome_state": _as_dict(proposal.get("evidence")).get("outcome_state"), "claim_state": _as_dict(pre["commitments"].get(CLAIM_ID)).get("state")},
        believed_inputs={"source_record_hash": _as_dict(proposal.get("source")).get("source_record_hash"), "target": proposal.get("target"), "outcome": proposal.get("observed_outcome")},
    )
    header["proposal_ids"] = [proposal.get("proposal_id")]
    header["canonical_queue"] = [entry["canonical_execution_key"]]
    return working, entry, header


def resolve_claim(record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Resolve the same active claim after or without crew evidence."""

    def effect(working: dict[str, Any]) -> list[str]:
        area = working["areas"]["C"]
        claim = working["commitments"][CLAIM_ID]
        if area["relay"]["active"]:
            area["owner"] = "gang"
            area["gang_control"] = 72
            area["rival_control"] = 28
            area["gang_presence"] = claim["reserved_personnel"]
            claim["state"] = "succeeded"
            claim["terminal_resource_disposition"] = {
                "personnel": "transfer 6 reserved personnel to C.gang_presence",
                "supply": "consume 1 reserved claim supply",
            }
            return ["C.owner = gang", "C.gang_control = 72", "C.rival_control = 28", "C.gang_presence = 6", f"commitments.{CLAIM_ID} = succeeded", "consume 1 reserved claim supply"]
        working["resources"]["gang_personnel_available"] += claim["reserved_personnel"]
        working["resources"]["gang_claim_supply_available"] += claim["reserved_supply"]
        area["gang_personnel_present"] = 0
        claim["state"] = "failed"
        claim["terminal_resource_disposition"] = {
            "personnel": "release 6 reserved personnel to gang_personnel_available",
            "supply": "release 1 reserved claim supply to gang_claim_supply_available",
        }
        return ["gang_personnel_available += 6", "gang_claim_supply_available += 1", "C.gang_personnel_present = 0", f"commitments.{CLAIM_ID} = failed"]

    area = record["areas"]["C"]
    claim = _as_dict(record["commitments"].get(CLAIM_ID))
    gates = OrderedDict(
        [
            ("claim.active", claim.get("state") == "active"),
            ("C.relay.active", area["relay"]["active"] is True),
            ("C.perimeter_established", area["perimeter_established"] is True),
            ("C.ingress_secured", area["ingress_secured"] is True),
            ("claim.reserved_personnel >= 6", claim.get("reserved_personnel", 0) >= 6),
            ("C.rival_resistance <= 36", area["rival_resistance"] <= 36),
            ("C.owner == contested", area["owner"] == "contested"),
        ]
    )
    # Claim failure must release resources even when the relay gate fails.  It
    # is a terminal resolution, not a rejected action.
    pre, header = _scheduler_header(record, "t0/40", "claim_resolution")
    working = _copy(pre)
    evaluated = _ordered_gates("working_revalidation", gates)
    working_pre_hash = record_hash(working)
    if all(gate["passed"] for gate in evaluated):
        mutations = effect(working)
        result = "accepted"
        resources = ["transfer 6 reserved personnel to C.gang_presence", "consume 1 reserved claim supply"]
    else:
        active_claim = working["commitments"][CLAIM_ID]
        working["resources"]["gang_personnel_available"] += active_claim["reserved_personnel"]
        working["resources"]["gang_claim_supply_available"] += active_claim["reserved_supply"]
        working["areas"]["C"]["gang_personnel_present"] = 0
        active_claim["state"] = "failed"
        active_claim["terminal_resource_disposition"] = {
            "personnel": "release 6 reserved personnel to gang_personnel_available",
            "supply": "release 1 reserved claim supply to gang_claim_supply_available",
        }
        mutations = ["gang_personnel_available += 6", "gang_claim_supply_available += 1", "C.gang_personnel_present = 0", f"commitments.{CLAIM_ID} = failed"]
        result = "failed_gate"
        resources = ["release 6 reserved personnel", "release 1 reserved claim supply"]
    working_post_hash = record_hash(working)
    entry = _ledger_entry(
        decision_time="t0/40",
        actor="gang_docklands",
        proposal_id=CLAIM_ID + ".complete",
        execution_key="t0/40/C/gang_docklands.complete_claim_C",
        batch_pre_state_hash=header["transaction_pre_state_hash"],
        source_record_hash=None,
        working_pre_state_hash=working_pre_hash,
        working_post_state_hash=working_post_hash,
        gates=evaluated,
        result=result,
        mutations=mutations,
        resources=resources,
        observed_inputs={"C.relay.active": area["relay"]["active"], "C.perimeter_established": area["perimeter_established"], "C.ingress_secured": area["ingress_secured"], "claim.reserved_personnel": claim.get("reserved_personnel"), "C.owner": area["owner"]},
        believed_inputs={"claim": claim, "area_C": area},
    )
    header["proposal_ids"] = [entry["proposal_id"]]
    header["canonical_queue"] = [entry["canonical_execution_key"]]
    return working, entry, header


def _pre_arrival_run() -> tuple[dict[str, Any], dict[str, Any]]:
    r0 = initial_record()
    run: dict[str, Any] = {
        "scenario_id": SCENARIO_ID,
        "scenario_version": SCENARIO_VERSION,
        "simulation_version": SIMULATION_VERSION,
        "r0": _copy(r0),
        "transactions": [],
        "ledger": [],
    }
    record, entry, header = resolve_deployment(r0)
    _append_transaction(run, header, entry)
    for resolver in (resolve_survey, resolve_marshal, resolve_ingress, resolve_perimeter, resolve_relay_activation, resolve_claim_start):
        record, entry, header = resolver(record)
        _append_transaction(run, header, entry)
    arrival, arrival_header = _scheduler_header(record, "t0/27", "arrival_scheduler_derivation")
    arrival_entry = _ledger_entry(
        decision_time="t0/27",
        actor="canonical_scheduler",
        proposal_id="scheduler.arrival_access_C",
        execution_key="t0/27/C/canonical_scheduler.arrival_access",
        batch_pre_state_hash=arrival_header["transaction_pre_state_hash"],
        source_record_hash=None,
        working_pre_state_hash=arrival_header["transaction_pre_state_hash"],
        working_post_state_hash=arrival_header["transaction_pre_state_hash"],
        gates=_ordered_gates("derived_eligibility", OrderedDict([("physical_access_C", physical_access(arrival))])),
        result="derived",
        mutations=["clock = t0/27"],
        resources=["no resource acquired"],
        observed_inputs={"deployment.destination": arrival["deployment"]["destination"], "deployment.physical_access_at": arrival["deployment"]["physical_access_at"], "clock": arrival["clock"]},
        believed_inputs={"physical_access_C": physical_access(arrival)},
    )
    arrival_header["proposal_ids"] = [arrival_entry["proposal_id"]]
    arrival_header["canonical_queue"] = [arrival_entry["canonical_execution_key"]]
    _append_transaction(run, arrival_header, arrival_entry)
    run["arrival_record"] = _copy(arrival)
    return run, arrival


def prepare_post_claim_record() -> dict[str, Any]:
    run = run_branch(BRANCH_CONTROL)
    return _copy(run["final_record"])


def run_branch(branch: str, physical_proposal: dict[str, Any] | None = None) -> dict[str, Any]:
    """Resolve a full A/B/C proof branch from byte-identical R0."""

    if branch not in BRANCHES:
        raise ValueError(f"unknown branch {branch!r}")
    run, record = _pre_arrival_run()
    run["branch_label"] = branch  # run artifact metadata only; never serialized into city state.
    if branch == BRANCH_EARLY:
        proposal = _copy(physical_proposal or make_physical_proposal("active", record_hash(record)))
        record, entry, header = apply_physical_proposal(record, proposal)
        _append_transaction(run, header, entry)
    record, entry, header = resolve_claim(record)
    _append_transaction(run, header, entry)
    if branch == BRANCH_LATE:
        proposal = _copy(physical_proposal or make_physical_proposal("succeeded", record_hash(record)))
        record, entry, header = apply_physical_proposal(record, proposal)
        _append_transaction(run, header, entry)
    run["final_record"] = _copy(record)
    run["final_record_hash"] = record_hash(record)
    return run


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def write_pre_records(output_directory: Path) -> dict[str, Path]:
    output_directory.mkdir(parents=True, exist_ok=True)
    arrival = prepare_arrival_record()
    post_claim = prepare_post_claim_record()
    paths = {
        "arrival": output_directory / "live_commitment_Rarrival.json",
        "post_claim": output_directory / "live_commitment_post_claim_pre.json",
    }
    _write_json(paths["arrival"], serializable_record(arrival))
    _write_json(paths["post_claim"], serializable_record(post_claim))
    return paths


def write_branch_artifacts(branch: str, output_directory: Path, physical_proposal: dict[str, Any] | None = None) -> dict[str, Path]:
    output_directory.mkdir(parents=True, exist_ok=True)
    run = run_branch(branch, physical_proposal)
    paths = {
        "run": output_directory / f"live_commitment_{branch}_run.json",
        "r0": output_directory / f"live_commitment_{branch}_R0.json",
        "final": output_directory / f"live_commitment_{branch}_final.json",
        "ledger": output_directory / f"live_commitment_{branch}_ledger.json",
    }
    _write_json(paths["run"], run)
    _write_json(paths["r0"], serializable_record(run["r0"]))
    _write_json(paths["final"], serializable_record(run["final_record"]))
    _write_json(paths["ledger"], run["ledger"])
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    command = parser.add_subparsers(dest="command", required=True)
    pre = command.add_parser("write-pre-records")
    pre.add_argument("--output-directory", type=Path, required=True)
    branch = command.add_parser("write-branch")
    branch.add_argument("branch", choices=BRANCHES)
    branch.add_argument("--output-directory", type=Path, required=True)
    branch.add_argument("--physical-proposal", type=Path)
    arguments = parser.parse_args()
    if arguments.command == "write-pre-records":
        paths = write_pre_records(arguments.output_directory)
    else:
        proposal = None if arguments.physical_proposal is None else json.loads(arguments.physical_proposal.read_text(encoding="utf-8"))
        paths = write_branch_artifacts(arguments.branch, arguments.output_directory, proposal)
    print(canonical_json({name: str(path) for name, path in paths.items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
