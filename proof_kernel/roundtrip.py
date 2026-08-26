"""Canonical bridge-access persistence transaction for the frozen round-trip proof.

Unreal may create the proposal this module receives. Only this module accepts or
rejects it and produces the next authoritative record.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from kernel import canonical_json, state_hash


PROTOCOL_VERSION = "PhysicalConsequenceProposal.v1"
SIMULATION_VERSION = "0.7.0-draft.9"
PARENT_COUNTERFACTUAL_HASH = "0b27ed07131ab5889d820476ef7d665c1f5c046872ea895b93b764801e7c7206"
PROPOSAL_ID = "physical_destroy_E_AB_0001"
TARGET_ID = "bridge_access_point_E_AB_01"
ALLOWED_MUTATIONS = [
    "E_AB.bridge_open = false",
    "E_AB.capacity = 0",
    "E_AB.bridge_access_point.state = destroyed",
]


@dataclass(frozen=True)
class PhysicalProposalContract:
    """Exact authority-bearing shape for one physical consequence kind.

    This is deliberately narrower than evidence integrity.  A valid digest only
    proves that a proposal's fields agree with one another; this contract proves
    those fields authorize the canonical mutation being considered.
    """

    proposal_id: str
    simulation_version: str
    runtime_instance_id: str
    instigator: dict[str, str]
    target: dict[str, str]
    observed_outcome: dict[str, Any]
    allowed_mutations: list[str]


def physical_authorization_gates(
    proposal: dict[str, Any],
    *,
    contract: PhysicalProposalContract,
    batch_pre_state_hash: str,
    proposal_terminal_dispositions: Mapping[str, str] | None = None,
) -> OrderedDict[str, bool]:
    """Validate authority-bearing physical proposal fields without mutation.

    The source hash is intentionally compared to the immutable *batch* state,
    never to a later sequential working state.  Callers add their own dynamic
    working-record revalidation gates after this immutable binding check.
    """

    source = _as_dict(proposal.get("source"))
    instigator = _as_dict(proposal.get("instigator"))
    target = _as_dict(proposal.get("target"))
    observed = _as_dict(proposal.get("observed_outcome"))
    evidence = _as_dict(proposal.get("evidence"))
    terminal = proposal_terminal_dispositions or {}
    event_sequence = observed.get("event_sequence")
    expected_digest = evidence_digest(
        source_record_hash=str(source.get("source_record_hash", "")),
        instigator_id=str(instigator.get("id", "")),
        physical_actor_id=str(evidence.get("physical_actor_id", "")),
        state=str(observed.get("state", "")),
        event_sequence=event_sequence if isinstance(event_sequence, int) else -1,
    )

    exact_top_level = {
        "proposal_id",
        "protocol_version",
        "source",
        "instigator",
        "target",
        "observed_outcome",
        "evidence",
        "proposed_mutations",
    }
    exact_source = {
        "system",
        "runtime_instance_id",
        "source_record_hash",
        "source_simulation_version",
    }
    exact_evidence = {"physical_actor_id", "destruction_state", "evidence_digest"}

    return OrderedDict(
        [
            (
                "schema_protocol_compatible",
                set(proposal) == exact_top_level
                and proposal.get("protocol_version") == PROTOCOL_VERSION
                and set(source) == exact_source
                and source.get("source_simulation_version") == contract.simulation_version,
            ),
            (
                "source_identity_exact",
                source.get("system") == "crew_physical_simulation"
                and source.get("runtime_instance_id") == contract.runtime_instance_id,
            ),
            (
                "source_record_hash_matches_batch_pre_state",
                source.get("source_record_hash") == batch_pre_state_hash,
            ),
            (
                "proposal_id_unseen",
                proposal.get("proposal_id") == contract.proposal_id
                and contract.proposal_id not in terminal,
            ),
            ("instigator_exact", instigator == contract.instigator),
            ("target_identity_and_route_match", target == contract.target),
            ("observed_outcome_exact", observed == contract.observed_outcome),
            (
                "evidence_matches_observed_outcome",
                set(evidence) == exact_evidence
                and evidence.get("physical_actor_id") == contract.target["id"]
                and evidence.get("destruction_state") == contract.observed_outcome["state"]
                and evidence.get("evidence_digest") == expected_digest,
            ),
            ("allowed_effect_set_exact", proposal.get("proposed_mutations") == contract.allowed_mutations),
        ]
    )


def seed_record() -> dict[str, Any]:
    """The normalized record supplied to the first Unreal process."""

    return {
        "record_schema": "BridgeAccessRoundTripRecord.v1",
        "record_name": "Round trip seed — E_AB intact",
        "parent_causal_record_hash": PARENT_COUNTERFACTUAL_HASH,
        "simulation_version": SIMULATION_VERSION,
        "bridge_open": True,
        "bridge_capacity": 1,
        "bridge_access_point_state": "intact",
        "fire_intensity": 4,
        "police_location": "C",
        "police_availability": "deployed",
        "police_present_C": 1,
        "docklands_owner": "contested",
        "gang_control": 62,
        "rival_control": 38,
        "proposal_terminal_dispositions": {},
    }


def record_hash(record: dict[str, Any]) -> str:
    return state_hash(record)


def serializable_record(record: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(record)
    result["canonical_sha256"] = record_hash(record)
    return result


def load_serialized_record(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    supplied_hash = value.pop("canonical_sha256", None)
    if supplied_hash != record_hash(value):
        raise ValueError(f"{path} does not carry the canonical hash of its record content")
    return value


def evidence_digest(*, source_record_hash: str, instigator_id: str, physical_actor_id: str, state: str, event_sequence: int) -> str:
    material = "|".join(
        [source_record_hash, instigator_id, physical_actor_id, state, str(event_sequence)]
    )
    return "md5:" + hashlib.md5(material.encode("ascii")).hexdigest()


def make_proposal(source_record_hash: str) -> dict[str, Any]:
    digest = evidence_digest(
        source_record_hash=source_record_hash,
        instigator_id="crew_01_to_04",
        physical_actor_id=TARGET_ID,
        state="destroyed",
        event_sequence=1,
    )
    return {
        "proposal_id": PROPOSAL_ID,
        "protocol_version": PROTOCOL_VERSION,
        "source": {
            "system": "crew_physical_simulation",
            "runtime_instance_id": "proof_runtime_01",
            "source_record_hash": source_record_hash,
            "source_simulation_version": SIMULATION_VERSION,
        },
        "instigator": {"kind": "crew", "id": "crew_01_to_04"},
        "target": {"kind": "bridge_access_point", "id": TARGET_ID, "route": "E_AB"},
        "observed_outcome": {"state": "destroyed", "event_sequence": 1},
        "evidence": {
            "physical_actor_id": TARGET_ID,
            "destruction_state": "destroyed",
            "evidence_digest": digest,
        },
        "proposed_mutations": ALLOWED_MUTATIONS,
    }


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def validation_gates(record: dict[str, Any], proposal: dict[str, Any]) -> OrderedDict[str, bool]:
    """Evaluate all side-effect-free gates against one immutable pre-state."""

    source = _as_dict(proposal.get("source"))
    instigator = _as_dict(proposal.get("instigator"))
    target = _as_dict(proposal.get("target"))
    observed = _as_dict(proposal.get("observed_outcome"))
    evidence = _as_dict(proposal.get("evidence"))
    proposal_id = proposal.get("proposal_id")
    event_sequence = observed.get("event_sequence")
    expected_digest = evidence_digest(
        source_record_hash=str(source.get("source_record_hash", "")),
        instigator_id=str(instigator.get("id", "")),
        physical_actor_id=str(evidence.get("physical_actor_id", "")),
        state=str(observed.get("state", "")),
        event_sequence=event_sequence if isinstance(event_sequence, int) else -1,
    )

    return OrderedDict(
        [
            (
                "schema_protocol_compatible",
                proposal.get("protocol_version") == PROTOCOL_VERSION
                and source.get("source_simulation_version") == SIMULATION_VERSION,
            ),
            (
                "source_record_hash_matches_pre_state",
                source.get("source_record_hash") == record_hash(record),
            ),
            (
                "proposal_id_unseen",
                isinstance(proposal_id, str)
                and proposal_id not in record.get("proposal_terminal_dispositions", {}),
            ),
            (
                "target_identity_and_route_match",
                target
                == {"kind": "bridge_access_point", "id": TARGET_ID, "route": "E_AB"},
            ),
            (
                "target_current_state_eligible",
                record.get("bridge_access_point_state") == "intact"
                and record.get("bridge_open") is True
                and record.get("bridge_capacity") >= 1,
            ),
            (
                "evidence_matches_observed_outcome",
                evidence.get("physical_actor_id") == TARGET_ID
                and evidence.get("destruction_state") == "destroyed"
                and observed == {"state": "destroyed", "event_sequence": 1}
                and evidence.get("evidence_digest") == expected_digest,
            ),
            ("allowed_effect_set_exact", proposal.get("proposed_mutations") == ALLOWED_MUTATIONS),
        ]
    )


def apply_proposal(
    record: dict[str, Any], proposal: dict[str, Any], ledger: list[dict[str, Any]] | None = None
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Validate a proposal without short-circuiting, then atomically commit or reject."""

    ledger = [] if ledger is None else copy.deepcopy(ledger)
    pre_state = copy.deepcopy(record)
    pre_hash = record_hash(pre_state)
    gates = validation_gates(pre_state, proposal)
    accepted = all(gates.values())
    next_record = copy.deepcopy(pre_state)
    proposal_id = proposal.get("proposal_id")
    source = _as_dict(proposal.get("source"))
    evidence = _as_dict(proposal.get("evidence"))

    if accepted:
        next_record["bridge_open"] = False
        next_record["bridge_capacity"] = 0
        next_record["bridge_access_point_state"] = "destroyed"
        next_record["record_name"] = "Round trip committed — bridge access destroyed"
        next_record.setdefault("proposal_terminal_dispositions", {})[proposal_id] = "accepted"

    post_hash = record_hash(next_record)
    ledger.append(
        {
            "decision_boundary": "t3/50/E_AB/physical_persistence",
            "canonical_execution_sequence": "t3/50/E_AB/canonical.apply_physical_proposal",
            "simulation_version": SIMULATION_VERSION,
            "proposal_protocol_version": proposal.get("protocol_version"),
            "actor_or_process": "canonical_transaction_layer",
            "action_id": proposal_id,
            "source_record_hash": source.get("source_record_hash"),
            "transaction_pre_state_hash": pre_hash,
            "evidence_digest": evidence.get("evidence_digest"),
            "physical_actor_id": evidence.get("physical_actor_id"),
            "instigator": copy.deepcopy(_as_dict(proposal.get("instigator"))),
            "observed_physical_outcome": copy.deepcopy(_as_dict(proposal.get("observed_outcome"))),
            "gate_results": dict(gates),
            "result": "accepted" if accepted else "rejected",
            "terminal_disposition": "accepted" if accepted else "rejected",
            "committed_mutations": copy.deepcopy(ALLOWED_MUTATIONS if accepted else []),
            "pre_state_hash": pre_hash,
            "post_state_hash": post_hash,
        }
    )
    return next_record, ledger


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    command = parser.add_subparsers(dest="command", required=True)
    seed_command = command.add_parser("write-seed")
    seed_command.add_argument("--output", type=Path, required=True)
    proposal_command = command.add_parser("write-proof-proposal")
    proposal_command.add_argument("--record", type=Path, required=True)
    proposal_command.add_argument("--output", type=Path, required=True)
    apply_command = command.add_parser("apply")
    apply_command.add_argument("--record", type=Path, required=True)
    apply_command.add_argument("--proposal", type=Path, required=True)
    apply_command.add_argument("--output", type=Path, required=True)
    apply_command.add_argument("--ledger", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "write-seed":
        _write_json(args.output, serializable_record(seed_record()))
        return
    if args.command == "write-proof-proposal":
        _write_json(args.output, make_proposal(record_hash(load_serialized_record(args.record))))
        return

    current_record = load_serialized_record(args.record)
    proposal = json.loads(args.proposal.read_text(encoding="utf-8"))
    prior_ledger = json.loads(args.ledger.read_text(encoding="utf-8")) if args.ledger.exists() else []
    next_record, next_ledger = apply_proposal(current_record, proposal, prior_ledger)
    _write_json(args.output, serializable_record(next_record))
    _write_json(args.ledger, next_ledger)


if __name__ == "__main__":
    main()
