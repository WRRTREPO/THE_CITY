"""Canonical-only resolver for the frozen shared-state interference proof.

The X/Y labels are fixture identifiers, not production roles.  The resolver
deliberately knows only generic definition data, a canonical queue, and the
shared state it revalidates.  No commitment definition can refer to the other.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, Iterable

from kernel import canonical_json, state_hash


SCENARIO_ID = "shared-state-commitment-interference-v1"
SCENARIO_VERSION = "0.1.0"
SIMULATION_VERSION = "0.7.0-draft.23"
RECORD_SCHEMA = "SharedStateCommitmentInterferenceRecord.v1"
SEED = "shared-state-commitment-interference-v1/0001"
DECISION_BOUNDARY = "t0/00"

COMMITMENT_X = "commitment_X"
COMMITMENT_Y = "commitment_Y"
COMMITMENTS = (COMMITMENT_X, COMMITMENT_Y)


def _copy(value: Any) -> Any:
    return copy.deepcopy(value)


def record_hash(record: dict[str, Any]) -> str:
    return state_hash(record)


def serializable_record(record: dict[str, Any]) -> dict[str, Any]:
    serialized = _copy(record)
    serialized["canonical_sha256"] = record_hash(record)
    return serialized


def _definition(commitment_id: str, actor: str) -> dict[str, Any]:
    return {
        "id": commitment_id,
        "actor": actor,
        "action": "allocate_one_unit",
        "reads": ["S.available_units"],
        "writes": ["S.available_units", f"S.durable_allocations.{commitment_id}"],
        "gate": "S.available_units >= 1",
        "terminal_success": f"transform one available S unit into allocation committed_by_{commitment_id}",
        "terminal_failure": "no resource acquired",
    }


DEFINITIONS = {
    COMMITMENT_X: _definition(COMMITMENT_X, "process_X"),
    COMMITMENT_Y: _definition(COMMITMENT_Y, "process_Y"),
}


def definition_hashes(definitions: dict[str, dict[str, Any]] | None = None) -> dict[str, str]:
    source = DEFINITIONS if definitions is None else definitions
    return {commitment_id: state_hash(source[commitment_id]) for commitment_id in sorted(source)}


def _strings(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, nested in value.items():
            yield str(key)
            yield from _strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _strings(nested)
    elif isinstance(value, str):
        yield value


def definition_independence_audit(definitions: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    """Verify definitions share declared S paths and no foreign identity."""

    source = DEFINITIONS if definitions is None else definitions
    foreign_references: list[dict[str, str]] = []
    undeclared_paths: list[dict[str, str]] = []
    known = {
        COMMITMENT_X: {"commitment_X", "process_X"},
        COMMITMENT_Y: {"commitment_Y", "process_Y"},
    }
    for commitment_id, definition in sorted(source.items()):
        for text in _strings(definition):
            for other_id, other_tokens in known.items():
                if other_id != commitment_id and text in other_tokens:
                    foreign_references.append({"definition": commitment_id, "foreign_token": text})
        for path in definition["reads"] + definition["writes"]:
            if not path.startswith("S."):
                undeclared_paths.append({"definition": commitment_id, "path": path})
    return {
        "definition_hashes": definition_hashes(source),
        "foreign_references": foreign_references,
        "undeclared_shared_paths": undeclared_paths,
        "passed": not foreign_references and not undeclared_paths,
    }


def initial_record(scheduled_commitment_ids: Iterable[str] = COMMITMENTS) -> dict[str, Any]:
    scheduled = tuple(scheduled_commitment_ids)
    if len(set(scheduled)) != len(scheduled) or any(item not in DEFINITIONS for item in scheduled):
        raise ValueError("scheduled commitments must be unique known definitions")
    return {
        "record_schema": RECORD_SCHEMA,
        "record_name": "Shared-state interference seed",
        "scenario_id": SCENARIO_ID,
        "scenario_version": SCENARIO_VERSION,
        "simulation_version": SIMULATION_VERSION,
        "seed": SEED,
        "clock": DECISION_BOUNDARY,
        "shared_state": {
            "total_units": 1,
            "available_units": 1,
            "durable_allocations": [],
        },
        "commitment_definitions": _copy(DEFINITIONS),
        "definition_hashes": definition_hashes(),
        "commitments": {
            commitment_id: {
                "definition_id": commitment_id,
                "state": "due" if commitment_id in scheduled else "not_scheduled",
            }
            for commitment_id in COMMITMENTS
        },
        "scheduled_commitment_ids": list(scheduled),
        "terminal_resource_dispositions": {},
    }


def _gate_entries(values: list[tuple[str, bool]]) -> list[dict[str, Any]]:
    return [
        {
            "scope": "working_revalidation",
            "name": name,
            "value": value,
            "passed": value,
            "result": "pass" if value else "fail",
        }
        for name, value in values
    ]


def _entry(
    *,
    commitment_id: str,
    definition: dict[str, Any],
    queue_index: int,
    batch_pre_state_hash: str,
    working_pre_state_hash: str,
    working_post_state_hash: str,
    gates: list[dict[str, Any]],
    result: str,
    mutations: list[str],
    resources: list[str],
    observed_inputs: dict[str, Any],
) -> dict[str, Any]:
    return {
        "scenario_id": SCENARIO_ID,
        "scenario_version": SCENARIO_VERSION,
        "simulation_version": SIMULATION_VERSION,
        "decision_time": DECISION_BOUNDARY,
        "actor": definition["actor"],
        "commitment_id": commitment_id,
        "action_id": definition["action"],
        "canonical_execution_key": f"{DECISION_BOUNDARY}/fixture_queue/{queue_index:02d}/{commitment_id}",
        "batch_pre_state_hash": batch_pre_state_hash,
        "source_record_hash": batch_pre_state_hash,
        "working_pre_state_hash": working_pre_state_hash,
        "working_post_state_hash": working_post_state_hash,
        "definition_hash": state_hash(definition),
        "observed_inputs": _copy(observed_inputs),
        "believed_inputs": _copy(observed_inputs),
        "gates": _copy(gates),
        "result": result,
        "mutations": _copy(mutations),
        "resources": _copy(resources),
        "terminal_resource_disposition": resources[-1],
    }


def _commit_one(
    working: dict[str, Any],
    *,
    commitment_id: str,
    queue_index: int,
    batch_pre_state_hash: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    definition = working["commitment_definitions"][commitment_id]
    current = working["commitments"][commitment_id]
    shared = working["shared_state"]
    observed = {
        "commitment_state": current["state"],
        "S.available_units": shared["available_units"],
        "definition_hash": state_hash(definition),
    }
    gates = _gate_entries(
        [
            ("commitment_is_due", current["state"] == "due"),
            ("definition_hash_matches_record", working["definition_hashes"][commitment_id] == state_hash(definition)),
            ("S.available_units >= 1", shared["available_units"] >= 1),
        ]
    )
    working_pre_state_hash = record_hash(working)
    if all(gate["passed"] for gate in gates):
        allocation = {
            "allocation_id": f"S.allocation.{commitment_id}",
            "committed_by": commitment_id,
            "units": 1,
        }
        shared["available_units"] -= 1
        shared["durable_allocations"].append(allocation)
        current["state"] = "succeeded"
        working["terminal_resource_dispositions"][commitment_id] = "transform one available S unit into durable allocation"
        mutations = [
            "S.available_units -= 1",
            f"S.durable_allocations += S.allocation.{commitment_id}",
            f"{commitment_id}.state = succeeded",
        ]
        resources = ["acquire 1 S unit", "transform one available S unit into durable allocation"]
        result = "accepted"
    else:
        current["state"] = "failed"
        working["terminal_resource_dispositions"][commitment_id] = "no resource acquired"
        mutations = [f"{commitment_id}.state = failed"]
        resources = ["no resource acquired"]
        result = "failed_gate"
    working_post_state_hash = record_hash(working)
    return working, _entry(
        commitment_id=commitment_id,
        definition=definition,
        queue_index=queue_index,
        batch_pre_state_hash=batch_pre_state_hash,
        working_pre_state_hash=working_pre_state_hash,
        working_post_state_hash=working_post_state_hash,
        gates=gates,
        result=result,
        mutations=mutations,
        resources=resources,
        observed_inputs=observed,
    )


def run_fixture(
    *,
    scheduled_commitment_ids: Iterable[str],
    canonical_queue: Iterable[str],
) -> dict[str, Any]:
    """Resolve generic due commitments using fixture-supplied queue input."""

    scheduled = tuple(scheduled_commitment_ids)
    queue = tuple(canonical_queue)
    if set(queue) != set(scheduled) or len(queue) != len(scheduled):
        raise ValueError("canonical queue must contain each scheduled commitment exactly once")
    r0 = initial_record(scheduled)
    audit = definition_independence_audit(r0["commitment_definitions"])
    if not audit["passed"]:
        raise ValueError("commitment definitions are not independent")
    batch_pre_state_hash = record_hash(r0)
    working = _copy(r0)
    ledger: list[dict[str, Any]] = []
    for queue_index, commitment_id in enumerate(queue, start=1):
        working, entry = _commit_one(
            working,
            commitment_id=commitment_id,
            queue_index=queue_index,
            batch_pre_state_hash=batch_pre_state_hash,
        )
        ledger.append(entry)
    transaction = {
        "header": {
            "decision_boundary": DECISION_BOUNDARY,
            "parent_record_hash": batch_pre_state_hash,
            "boundary_derivation": "canonical_shared_state_batch",
            "transaction_pre_state_hash": batch_pre_state_hash,
            "canonical_queue": list(queue),
            "fixture_queue_is_not_production_precedence": True,
        },
        "ledger": _copy(ledger),
    }
    return {
        "r0": r0,
        "definition_audit": audit,
        "transactions": [transaction],
        "ledger": ledger,
        "final_record": working,
    }


def primary_run() -> dict[str, Any]:
    return run_fixture(scheduled_commitment_ids=COMMITMENTS, canonical_queue=(COMMITMENT_X, COMMITMENT_Y))


def counterfactual_run() -> dict[str, Any]:
    return run_fixture(scheduled_commitment_ids=(COMMITMENT_Y,), canonical_queue=(COMMITMENT_Y,))


def permutation_run() -> dict[str, Any]:
    return run_fixture(scheduled_commitment_ids=COMMITMENTS, canonical_queue=(COMMITMENT_Y, COMMITMENT_X))


def _write_json(path: Path, value: Any) -> None:
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def write_run_artifacts(name: str, run: dict[str, Any], directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    _write_json(directory / f"shared_state_{name}_R0.json", serializable_record(run["r0"]))
    _write_json(directory / f"shared_state_{name}_final.json", serializable_record(run["final_record"]))
    _write_json(directory / f"shared_state_{name}_ledger.json", run["ledger"])
    _write_json(directory / f"shared_state_{name}_run.json", run)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for name, run in (
        ("primary", primary_run()),
        ("counterfactual", counterfactual_run()),
        ("permutation", permutation_run()),
    ):
        write_run_artifacts(name, run, args.output)
    print(f"wrote shared-state interference artifacts to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
