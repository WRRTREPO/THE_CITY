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
    validate_acceptance_receipt,
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
RECEIPT_MARKER = "INTEGRATED_MATERIALIZATION_RECEIPT:"


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
        "process_output": root / "process_output",
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
    # Process output is operational capture space, not a proof-input or
    # proof-exchange domain. UE writes structured receipts here; the harness
    # later validates and copies only the receipt into evidence.
    paths["process_output"].mkdir()
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


def source_launch_command(root: Path, control: bool = False) -> list[str]:
    paths = _runtime_paths(root)
    process_id = "control_source_process_01" if control else "source_process_01"
    return [
        str(EDITOR), str(PROJECT), "-game",
        f"-IntegratedProofPayload={paths['source_input'] / SOURCE_PAYLOAD}",
        f"-IntegratedProofLaunchReceipt={paths['source_input'] / SOURCE_RECEIPT}",
        f"-IntegratedProofOutput={paths['source_output']}",
        f"-IntegratedProofInteractionOpportunity={TIME_Q}",
        f"-IntegratedProofProcessInstanceId={process_id}",
        f"-abslog={paths['process_output'] / f'{process_id}.log'}",
    ]


def return_launch_command(root: Path, control: bool = False) -> list[str]:
    paths = _runtime_paths(root)
    payload = "canonical_payload_Rcontrol.json" if control else RETURN_PAYLOAD
    receipt = "launch_receipt_Rcontrol.json" if control else RETURN_RECEIPT
    process_id = "control_return_process_01" if control else "return_process_01"
    return [
        str(EDITOR), str(PROJECT), "-game",
        f"-IntegratedProofPayload={paths['return_input'] / payload}",
        f"-IntegratedProofLaunchReceipt={paths['return_input'] / receipt}",
        f"-IntegratedProofProcessInstanceId={process_id}",
        f"-abslog={paths['process_output'] / f'{process_id}.log'}",
    ]


def _source_record_for_receipt(root: Path) -> dict[str, Any]:
    paths = _runtime_paths(root)
    return validate_launch_artifact((paths["source_input"] / SOURCE_PAYLOAD).read_bytes(), (paths["source_input"] / SOURCE_RECEIPT).read_bytes())


def _return_record_for_receipt(root: Path, control: bool) -> dict[str, Any]:
    paths = _runtime_paths(root)
    payload = "canonical_payload_Rcontrol.json" if control else RETURN_PAYLOAD
    receipt = "launch_receipt_Rcontrol.json" if control else RETURN_RECEIPT
    return validate_launch_artifact((paths["return_input"] / payload).read_bytes(), (paths["return_input"] / receipt).read_bytes())


def capture_acceptance_receipt(root: Path, stage: str, control: bool = False) -> dict[str, Any]:
    """Capture exactly one UE receipt from its process-specific output log.

    The log is an operational output channel created by ``-abslog``. It is
    neither a UE proof input nor a proof exchange directory. This function is
    intentionally strict: a missing, malformed, contradictory, or duplicate
    receipt fails the witness before it can be retained as evidence.
    """

    if stage not in {"source", "return"}:
        raise ValueError("receipt stage must be source or return")
    paths = _runtime_paths(root)
    if stage == "source":
        record = _source_record_for_receipt(root)
        process_id = "control_source_process_01" if control else "source_process_01"
        proposal_capability_enabled = True
    else:
        record = _return_record_for_receipt(root, control)
        process_id = "control_return_process_01" if control else "return_process_01"
        proposal_capability_enabled = False
    output_log = paths["process_output"] / f"{process_id}.log"
    if not output_log.is_file():
        raise ValueError("UE process output log is unavailable")
    receipts: list[dict[str, Any]] = []
    for line in output_log.read_text(encoding="utf-8", errors="strict").splitlines():
        if RECEIPT_MARKER not in line:
            continue
        _, _, raw = line.partition(RECEIPT_MARKER)
        try:
            receipt = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("UE emitted malformed materialization receipt") from exc
        if not isinstance(receipt, dict):
            raise ValueError("UE materialization receipt is not an object")
        receipts.append(receipt)
    if len(receipts) != 1:
        raise ValueError("UE process must emit exactly one materialization receipt")
    receipt = receipts[0]
    if receipt.get("process_instance_id") != process_id:
        raise ValueError("UE materialization receipt process identity mismatch")
    validate_acceptance_receipt(record, receipt, proposal_capability_enabled)
    name = f"{'control_' if control else 'primary_'}{stage}_acceptance_receipt.json"
    _write_json(paths["evidence"] / name, receipt)
    return receipt


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
    if any(paths["source_output"].iterdir()):
        raise ValueError("Q-absent control source output must be empty before continuation")
    _write_json(paths["state"] / "control_source_output_audit.json", {"allowed_files": []})
    rcontrol = resolve_execution_boundary(r0, next_execution_boundary(r0, None))
    _write_json(paths["evidence"] / "Rcontrol.json", rcontrol)
    if paths["return_input"].exists():
        raise ValueError("control return input must not exist before control continuation")
    shutil.rmtree(paths["source_input"])
    shutil.rmtree(paths["source_output"])
    _write_pair(paths["return_input"], "canonical_payload_Rcontrol.json", "launch_receipt_Rcontrol.json", rcontrol)
    audit = visible_input_audit(paths["return_input"], ("canonical_payload_Rcontrol.json", "launch_receipt_Rcontrol.json"), None)
    _write_json(paths["state"] / "control_return_input_audit.json", audit)
    return {"rcontrol": rcontrol, "return_input_audit": audit}


def _copy_exact(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise ValueError(f"required witness artifact is unavailable: {source.name}")
    if destination.exists():
        raise ValueError(f"witness destination already exists: {destination.name}")
    shutil.copyfile(source, destination)


def export_witness_artifacts(primary_root: Path, control_root: Path, destination: Path) -> dict[str, Any]:
    """Validate and export the two clean UE lifecycle witnesses.

    This command is deliberately downstream of physical witnessing. It never
    launches UE, creates Q, or manufactures a receipt; it accepts only the
    captured artifacts emitted by the already-completed runtime domains.
    """

    primary = _runtime_paths(primary_root)
    control = _runtime_paths(control_root)
    destination.mkdir(parents=True, exist_ok=True)

    r0 = initial_canonical_envelope()
    q = external_evidence_q(r0)
    bq = admit_external_input_candidate(r0, q)
    expected_rinput = resolve_execution_boundary(r0, bq, q)
    expected_rfinal = resolve_execution_boundary(expected_rinput, next_execution_boundary(expected_rinput, None))
    expected_rcontrol = resolve_execution_boundary(r0, next_execution_boundary(r0, None))

    primary_source_receipt = _read_json(primary["evidence"] / "primary_source_acceptance_receipt.json")
    primary_return_receipt = _read_json(primary["evidence"] / "primary_return_acceptance_receipt.json")
    control_source_receipt = _read_json(control["evidence"] / "control_source_acceptance_receipt.json")
    control_return_receipt = _read_json(control["evidence"] / "control_return_acceptance_receipt.json")
    validate_acceptance_receipt(r0, primary_source_receipt, True)
    validate_acceptance_receipt(expected_rfinal, primary_return_receipt, False)
    validate_acceptance_receipt(r0, control_source_receipt, True)
    validate_acceptance_receipt(expected_rcontrol, control_return_receipt, False)

    if _read_json(primary["evidence"] / "captured_Q.json") != q:
        raise ValueError("primary UE output is not the exact frozen Q")
    if _read_json(primary["evidence"] / "Rinput.json") != expected_rinput:
        raise ValueError("primary Rinput differs from the canonical resolver")
    if _read_json(primary["evidence"] / "Rfinal.json") != expected_rfinal:
        raise ValueError("primary Rfinal differs from record-relative resolution")
    control_return_record = _return_record_for_receipt(control_root, True)
    if control_return_record != expected_rcontrol:
        raise ValueError("control Rcontrol differs from the canonical resolver")
    if primary["source_input"].exists() or primary["source_output"].exists():
        raise ValueError("primary source domains remained accessible after unload")
    if control["source_input"].exists() or control["source_output"].exists():
        raise ValueError("control source domains remained accessible after unload")
    if _read_json(control["state"] / "control_source_output_audit.json") != {"allowed_files": []}:
        raise ValueError("control source output was not proven empty")

    artifacts = {
        "physical_primary_source_acceptance_receipt.json": primary["evidence"] / "primary_source_acceptance_receipt.json",
        "physical_primary_return_acceptance_receipt.json": primary["evidence"] / "primary_return_acceptance_receipt.json",
        "physical_primary_Q.json": primary["evidence"] / "captured_Q.json",
        "physical_primary_Rinput.json": primary["evidence"] / "Rinput.json",
        "physical_primary_Rfinal.json": primary["evidence"] / "Rfinal.json",
        "physical_primary_preparation.json": primary["state"] / "prepared.json",
        "physical_primary_input_committed.json": primary["state"] / "input_committed.json",
        "physical_primary_source_termination_witness.json": primary["state"] / "source_termination_witness.json",
        "physical_primary_return_input_audit.json": primary["state"] / "return_input_audit.json",
        "physical_primary_source_process.log": primary["process_output"] / "source_process_01.log",
        "physical_primary_return_process.log": primary["process_output"] / "return_process_01.log",
        "physical_control_source_acceptance_receipt.json": control["evidence"] / "control_source_acceptance_receipt.json",
        "physical_control_return_acceptance_receipt.json": control["evidence"] / "control_return_acceptance_receipt.json",
        "physical_control_Rcontrol.json": control["return_input"] / "canonical_payload_Rcontrol.json",
        "physical_control_launch_receipt_Rcontrol.json": control["return_input"] / "launch_receipt_Rcontrol.json",
        "physical_control_preparation.json": control["state"] / "prepared.json",
        "physical_control_source_output_audit.json": control["state"] / "control_source_output_audit.json",
        "physical_control_source_termination_witness.json": control["state"] / "source_termination_witness.json",
        "physical_control_return_input_audit.json": control["state"] / "control_return_input_audit.json",
        "physical_control_source_process.log": control["process_output"] / "control_source_process_01.log",
        "physical_control_return_process.log": control["process_output"] / "control_return_process_01.log",
    }
    for name, source in artifacts.items():
        _copy_exact(source, destination / name)
    summary = {
        "primary": {
            "canonical_hashes": {"R0": canonical_hash(r0), "Rinput": canonical_hash(expected_rinput), "Rfinal": canonical_hash(expected_rfinal)},
            "source_domains_removed_before_rediscovery": True,
        },
        "control": {
            "canonical_hashes": {"R0": canonical_hash(r0), "Rcontrol": canonical_hash(expected_rcontrol)},
            "source_output_empty_before_continuation": True,
            "source_domains_removed_before_resolution": True,
        },
        "artifact_names": list(artifacts),
    }
    _write_json(destination / "physical_integrated_unreal_lifecycle_witness.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "source-command", "capture-receipt", "accept-q", "record-source-termination", "resolve-after-unload", "resolve-control-after-unload", "return-command", "export-witness"))
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--control-runtime-root", type=Path)
    parser.add_argument("--evidence-output", type=Path)
    parser.add_argument("--pid", type=int)
    parser.add_argument("--control", action="store_true")
    parser.add_argument("--stage", choices=("source", "return"))
    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare(args.runtime_root)
    elif args.command == "source-command":
        result = {"command": source_launch_command(args.runtime_root, args.control)}
    elif args.command == "capture-receipt":
        if args.stage is None:
            parser.error("capture-receipt requires --stage")
        result = capture_acceptance_receipt(args.runtime_root, args.stage, args.control)
    elif args.command == "export-witness":
        if args.control_runtime_root is None or args.evidence_output is None:
            parser.error("export-witness requires --control-runtime-root and --evidence-output")
        result = export_witness_artifacts(args.runtime_root, args.control_runtime_root, args.evidence_output)
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
