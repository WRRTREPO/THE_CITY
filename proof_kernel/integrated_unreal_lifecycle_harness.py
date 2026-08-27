"""Operational harness for the frozen integrated Unreal lifecycle witness.

This script is deliberately not a simulator. It prepares isolated process
domains, validates the exact UE-emitted Q, records the source termination
boundary, and prepares a return process that receives only Rfinal/Rcontrol and
its detached launch receipt.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path
from typing import Any

from integrated_unreal_promotion_unload_repromotion import (
    ACTOR_ID,
    INPUT_ID,
    TIME_Q,
    admit_external_input_candidate,
    canonical_hash,
    external_evidence_q,
    initial_canonical_envelope,
    launch_receipt,
    next_execution_boundary,
    raw_payload_sha256,
    resolve_execution_boundary,
    stored_payload_bytes,
    stored_receipt_bytes,
    validate_launch_artifact,
    visible_input_audit,
)
from kernel import canonical_json


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "CityMaterializationProof" / "CityMaterializationProof.uproject"
EDITOR = Path("/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor")
SOURCE_PAYLOAD = "canonical_payload_R0.json"
SOURCE_RECEIPT = "launch_receipt_R0.json"
RETURN_PAYLOAD = "canonical_payload_Rfinal.json"
RETURN_RECEIPT = "launch_receipt_Rfinal.json"
Q_FILENAME = "physical_disable_integrated_gate_token_0001.json"


def _write_pair(directory: Path, payload_name: str, receipt_name: str, record: dict[str, Any]) -> None:
    directory.mkdir(parents=True, exist_ok=False)
    (directory / payload_name).write_bytes(stored_payload_bytes(record))
    (directory / receipt_name).write_bytes(stored_receipt_bytes(launch_receipt(record)))
    validate_launch_artifact((directory / payload_name).read_bytes(), (directory / receipt_name).read_bytes())


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def _runtime_paths(root: Path) -> dict[str, Path]:
    return {
        "source_input": root / "source_input",
        "source_output": root / "source_output",
        "return_input": root / "return_input",
        "evidence": root / "evidence",
        "state": root / "state",
    }


def prepare(root: Path) -> dict[str, Any]:
    if root.exists() and any(root.iterdir()):
        raise ValueError("runtime root must be new or empty")
    root.mkdir(parents=True, exist_ok=True)
    paths = _runtime_paths(root)
    r0 = initial_canonical_envelope()
    _write_pair(paths["source_input"], SOURCE_PAYLOAD, SOURCE_RECEIPT, r0)
    paths["source_output"].mkdir()
    paths["evidence"].mkdir()
    paths["state"].mkdir()
    source_audit = visible_input_audit(paths["source_input"], (SOURCE_PAYLOAD, SOURCE_RECEIPT), {"interaction_opportunity": TIME_Q})
    _write_json(paths["state"] / "prepared.json", {
        "source_canonical_hash": canonical_hash(r0),
        "source_raw_payload_sha256": raw_payload_sha256(r0),
        "source_visible_input_audit": source_audit,
        "source_process_context": {"interaction_opportunity": TIME_Q},
    })
    return source_audit


def source_launch_command(root: Path) -> list[str]:
    paths = _runtime_paths(root)
    return [
        str(EDITOR), str(PROJECT), "-game",
        f"-IntegratedProofPayload={paths['source_input'] / SOURCE_PAYLOAD}",
        f"-IntegratedProofLaunchReceipt={paths['source_input'] / SOURCE_RECEIPT}",
        f"-IntegratedProofOutput={paths['source_output']}",
        f"-IntegratedProofInteractionOpportunity={TIME_Q}",
        "-IntegratedProofProcessInstanceId=source_process_01",
    ]


def return_launch_command(root: Path, control: bool = False) -> list[str]:
    paths = _runtime_paths(root)
    payload = "canonical_payload_Rcontrol.json" if control else RETURN_PAYLOAD
    receipt = "launch_receipt_Rcontrol.json" if control else RETURN_RECEIPT
    return [
        str(EDITOR), str(PROJECT), "-game",
        f"-IntegratedProofPayload={paths['return_input'] / payload}",
        f"-IntegratedProofLaunchReceipt={paths['return_input'] / receipt}",
        "-IntegratedProofProcessInstanceId=return_process_01" if not control else "-IntegratedProofProcessInstanceId=control_return_process_01",
    ]


def accept_q_and_prepare_return(root: Path) -> dict[str, Any]:
    paths = _runtime_paths(root)
    q_path = paths["source_output"] / Q_FILENAME
    if tuple(sorted(path.name for path in paths["source_output"].iterdir())) != (Q_FILENAME,):
        raise ValueError("source output must contain exactly one Q")
    q_bytes = q_path.read_bytes()
    q = _read_json(q_path)
    r0 = validate_launch_artifact((paths["source_input"] / SOURCE_PAYLOAD).read_bytes(), (paths["source_input"] / SOURCE_RECEIPT).read_bytes())
    expected_q = external_evidence_q(r0)
    if q_bytes != (canonical_json(expected_q) + "\n").encode("utf-8") or q != expected_q:
        raise ValueError("UE Q is not the exact frozen external evidence envelope")
    bq = admit_external_input_candidate(r0, q)
    rinput = resolve_execution_boundary(r0, bq, q)
    _write_json(paths["evidence"] / "captured_Q.json", q)
    _write_json(paths["evidence"] / "Rinput.json", rinput)
    _write_json(paths["state"] / "input_committed.json", {
        "rinput_hash": canonical_hash(rinput),
        "bq": bq,
        "source_process_must_be_terminated_before": "next_execution_boundary(Rinput)",
    })
    return {"rinput": rinput, "bq": bq}


def record_source_termination(root: Path, pid: int) -> dict[str, Any]:
    # The caller must terminate UE #1 first; this witness rejects a live PID.
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        pass
    else:
        raise ValueError("source UE process is still alive")
    paths = _runtime_paths(root)
    witness = {"source_process_pid": pid, "process_state": "terminated", "before": "next_execution_boundary(Rinput)"}
    _write_json(paths["state"] / "source_termination_witness.json", witness)
    return witness


def resolve_after_unload(root: Path) -> dict[str, Any]:
    paths = _runtime_paths(root)
    if not (paths["state"] / "source_termination_witness.json").is_file():
        raise ValueError("source termination witness is required before canonical continuation")
    rinput = _read_json(paths["evidence"] / "Rinput.json")
    alpha = next_execution_boundary(rinput, None)
    rfinal = resolve_execution_boundary(rinput, alpha)
    _write_json(paths["evidence"] / "Rfinal.json", rfinal)
    # Source input/output are temporary representation domains. Once Q has
    # become canonical evidence, the return stage retains none of their files.
    shutil.rmtree(paths["source_input"])
    shutil.rmtree(paths["source_output"])
    _write_pair(paths["return_input"], RETURN_PAYLOAD, RETURN_RECEIPT, rfinal)
    return_audit = visible_input_audit(paths["return_input"], (RETURN_PAYLOAD, RETURN_RECEIPT), None)
    _write_json(paths["state"] / "return_input_audit.json", return_audit)
    return {"alpha_boundary": alpha, "rfinal": rfinal, "return_input_audit": return_audit}


def resolve_control_after_unload(root: Path) -> dict[str, Any]:
    paths = _runtime_paths(root)
    r0 = initial_canonical_envelope()
    if not (paths["state"] / "source_termination_witness.json").is_file():
        raise ValueError("control source termination witness is required before canonical continuation")
    rcontrol = resolve_execution_boundary(r0, next_execution_boundary(r0, None))
    if paths["return_input"].exists():
        raise ValueError("control return input must not exist before control continuation")
    shutil.rmtree(paths["source_input"])
    shutil.rmtree(paths["source_output"])
    _write_pair(paths["return_input"], "canonical_payload_Rcontrol.json", "launch_receipt_Rcontrol.json", rcontrol)
    audit = visible_input_audit(paths["return_input"], ("canonical_payload_Rcontrol.json", "launch_receipt_Rcontrol.json"), None)
    _write_json(paths["state"] / "control_return_input_audit.json", audit)
    return {"rcontrol": rcontrol, "return_input_audit": audit}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "source-command", "accept-q", "record-source-termination", "resolve-after-unload", "resolve-control-after-unload", "return-command"))
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--pid", type=int)
    parser.add_argument("--control", action="store_true")
    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare(args.runtime_root)
    elif args.command == "source-command":
        result = {"command": source_launch_command(args.runtime_root)}
    elif args.command == "accept-q":
        result = accept_q_and_prepare_return(args.runtime_root)
    elif args.command == "record-source-termination":
        if args.pid is None:
            parser.error("--pid is required")
        result = record_source_termination(args.runtime_root, args.pid)
    elif args.command == "resolve-after-unload":
        result = resolve_after_unload(args.runtime_root)
    elif args.command == "return-command":
        result = {"command": return_launch_command(args.runtime_root, args.control)}
    else:
        result = resolve_control_after_unload(args.runtime_root)
    print(canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
