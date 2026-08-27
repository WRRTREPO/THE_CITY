"""Acquire the frozen two-domain Unreal evidence-arbitration witnesses.

This is an operational witness harness, not a live input collector.  The
sealed ``ConcurrentExternalCandidateSetFixture.v1`` object defines candidate
set completeness.  Process readiness, physical interaction order, file
arrival, and presentation order remain non-authoritative evidence traces.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import subprocess
import time
from pathlib import Path
from typing import Any

from concurrent_external_evidence_arbitration import (
    DOMAIN_TABLE,
    INPUT_A,
    INPUT_B,
    admit_external_input_candidate,
    canonical_hash,
    construct_bext_from_sealed_fixture_set,
    evidence_emission_receipt,
    external_evidence_q,
    initial_canonical_envelope,
    launch_receipt,
    materialization_acceptance_receipt,
    primary_fixture,
    raw_payload_sha256,
    resolve_external_batch,
    run_witness,
    stored_payload_bytes,
    stored_q_bytes,
    stored_receipt_bytes,
    validate_launch_artifact,
)
from kernel import canonical_json


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "CityMaterializationProof" / "CityMaterializationProof.uproject"
EDITOR = Path("/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor")
PAYLOAD_NAME = "canonical_payload_R0.json"
LAUNCH_RECEIPT_NAME = "launch_receipt_R0.json"
MATERIALIZATION_MARKER = "CONCURRENT_MATERIALIZATION_RECEIPT:"
WITNESS_MATRIX = {
    "W1": (("domain_A", "domain_B"), ("domain_A", "domain_B")),
    "W2": (("domain_B", "domain_A"), ("domain_A", "domain_B")),
    "W3": (("domain_A", "domain_B"), ("domain_B", "domain_A")),
    "W4": (("domain_B", "domain_A"), ("domain_B", "domain_A")),
}


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def _domain_paths(root: Path, domain: str) -> dict[str, Path]:
    base = root / domain
    return {
        "base": base,
        "input": base / "input",
        "output": base / "output",
        "process": base / "process",
        "user": base / "user",
        "temp": base / "temp",
    }


def _process_id(witness: str, domain: str) -> str:
    return f"{witness.lower()}_{domain}_process_01"


def _log_path(root: Path, witness: str, domain: str) -> Path:
    return _domain_paths(root, domain)["process"] / f"{_process_id(witness, domain)}.log"


def _q_path(root: Path, domain: str) -> Path:
    input_id = DOMAIN_TABLE[domain]["input_id"]
    return _domain_paths(root, domain)["output"] / f"{input_id}.json"


def _emission_receipt_path(root: Path, domain: str) -> Path:
    input_id = DOMAIN_TABLE[domain]["input_id"]
    return _domain_paths(root, domain)["output"] / f"{input_id}.emission_receipt.json"


def _launch_command(root: Path, witness: str, domain: str) -> list[str]:
    paths = _domain_paths(root, domain)
    x = "30" if domain == "domain_A" else "990"
    return [
        str(EDITOR),
        str(PROJECT),
        "-game",
        "-Multiprocess",
        "-NoSplash",
        "-Windowed",
        "-ResX=900",
        "-ResY=650",
        f"-WinX={x}",
        "-WinY=60",
        f"-UserDir={paths['user']}",
        f"-ConcurrentEvidencePayload={paths['input'] / PAYLOAD_NAME}",
        f"-ConcurrentEvidenceLaunchReceipt={paths['input'] / LAUNCH_RECEIPT_NAME}",
        f"-ConcurrentEvidenceOutput={paths['output']}",
        "-ConcurrentEvidenceInteractionOpportunity=t0/30",
        f"-ConcurrentEvidenceProcessInstanceId={_process_id(witness, domain)}",
        f"-ConcurrentEvidenceDomain={domain}",
        f"-abslog={_log_path(root, witness, domain)}",
    ]


def _launch_environment(root: Path, domain: str) -> dict[str, str]:
    """Return the exact noncanonical process environment used for launch.

    Keeping construction here lets the input audit inspect the same mapping
    passed to ``Popen`` without exporting environment values into evidence.
    """

    environment = dict(os.environ)
    environment["TMPDIR"] = str(_domain_paths(root, domain)["temp"])
    return environment


def _input_audit(root: Path, witness: str, domain: str) -> dict[str, Any]:
    paths = _domain_paths(root, domain)
    command = _launch_command(root, witness, domain)
    environment = _launch_environment(root, domain)
    other = "domain_B" if domain == "domain_A" else "domain_A"
    command_text = "\n".join(command)
    environment_text = "\n".join(str(value) for value in environment.values())
    other_base = str(_domain_paths(root, other)["base"])
    other_in_arguments = other_base in command_text
    other_in_environment = other_base in environment_text
    own_writable_roots = {
        str(paths[name]) for name in ("output", "process", "user", "temp")
    }
    other_paths = _domain_paths(root, other)
    other_writable_roots = {
        str(other_paths[name]) for name in ("output", "process", "user", "temp")
    }
    return {
        "materialization_domain": domain,
        "process_instance_id": _process_id(witness, domain),
        "proof_input_files": [
            {"name": PAYLOAD_NAME, "raw_byte_sha256": _sha(paths["input"] / PAYLOAD_NAME)},
            {"name": LAUNCH_RECEIPT_NAME, "raw_byte_sha256": _sha(paths["input"] / LAUNCH_RECEIPT_NAME)},
        ],
        "execution_context": {
            "interaction_opportunity": "t0/30",
            "materialization_domain": domain,
        },
        "other_domain_paths_visible": other_in_arguments or other_in_environment,
        "other_domain_paths_in_launch_arguments": other_in_arguments,
        "other_domain_paths_in_launch_environment": other_in_environment,
        "launch_environment_values_exported": False,
        "shared_writable_proof_state": False,
        "shared_writable_proof_path_configured": not own_writable_roots.isdisjoint(other_writable_roots),
        "authority_bearing_selectors_present": any(
            token in command_text for token in (
                "ConcurrentEvidencePriority=", "ConcurrentEvidenceExternalPhase=",
                "ConcurrentEvidenceMemberOrder=", "ConcurrentEvidenceWinner=",
            )
        ),
        "runtime_root_isolated": len(own_writable_roots) == 4 and own_writable_roots.isdisjoint(other_writable_roots),
    }


def prepare(root: Path, witness: str) -> dict[str, Any]:
    if witness not in WITNESS_MATRIX:
        raise ValueError("witness must be W1, W2, W3, or W4")
    if root.exists() and any(root.iterdir()):
        raise ValueError("runtime root must be new or empty")
    root.mkdir(parents=True, exist_ok=True)
    r0 = initial_canonical_envelope()
    for domain in ("domain_A", "domain_B"):
        paths = _domain_paths(root, domain)
        for name in ("input", "output", "process", "user", "temp"):
            paths[name].mkdir(parents=True, exist_ok=False)
        (paths["input"] / PAYLOAD_NAME).write_bytes(stored_payload_bytes(r0))
        (paths["input"] / LAUNCH_RECEIPT_NAME).write_bytes(stored_receipt_bytes(launch_receipt(r0)))
        validate_launch_artifact(
            (paths["input"] / PAYLOAD_NAME).read_bytes(),
            (paths["input"] / LAUNCH_RECEIPT_NAME).read_bytes(),
        )
    audits = {domain: _input_audit(root, witness, domain) for domain in ("domain_A", "domain_B")}
    if not all(
        not audit["other_domain_paths_visible"]
        and not audit["other_domain_paths_in_launch_arguments"]
        and not audit["other_domain_paths_in_launch_environment"]
        and audit["launch_environment_values_exported"] is False
        and not audit["authority_bearing_selectors_present"]
        and not audit["shared_writable_proof_state"]
        and not audit["shared_writable_proof_path_configured"]
        and audit["runtime_root_isolated"]
        for audit in audits.values()
    ):
        raise ValueError("domain isolation or ordering-selector audit failed")
    prepared = {
        "witness": witness,
        "canonical_R0_hash": canonical_hash(r0),
        "raw_R0_sha256": raw_payload_sha256(r0),
        "sealed_physical_emission_order": list(WITNESS_MATRIX[witness][0]),
        "sealed_harness_presentation_order": list(WITNESS_MATRIX[witness][1]),
        "candidate_set_completeness_source": "ConcurrentExternalCandidateSetFixture.v1",
        "input_audits": audits,
    }
    _write_json(root / "state" / "prepared.json", prepared)
    return prepared


def launch_pair(root: Path) -> dict[str, Any]:
    prepared = _read_json(root / "state" / "prepared.json")
    witness = prepared["witness"]
    pids: dict[str, int] = {}
    commands: dict[str, list[str]] = {}
    for domain in ("domain_A", "domain_B"):
        paths = _domain_paths(root, domain)
        command = _launch_command(root, witness, domain)
        environment = _launch_environment(root, domain)
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        pids[domain] = process.pid
        commands[domain] = command
    state = {"witness": witness, "pids": pids, "commands": commands}
    _write_json(root / "state" / "processes.json", state)
    return state


def _is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def _receipt_from_log(path: Path) -> dict[str, Any]:
    receipts: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="strict").splitlines():
        if MATERIALIZATION_MARKER in line:
            _, _, raw = line.partition(MATERIALIZATION_MARKER)
            receipts.append(json.loads(raw))
    if len(receipts) != 1:
        raise ValueError(f"expected exactly one materialization receipt in {path.name}")
    return receipts[0]


def record_overlap(root: Path, wait_seconds: int = 120) -> dict[str, Any]:
    prepared = _read_json(root / "state" / "prepared.json")
    process_state = _read_json(root / "state" / "processes.json")
    witness = prepared["witness"]
    deadline = time.monotonic() + wait_seconds
    while True:
        logs_ready = all(_log_path(root, witness, domain).is_file() and MATERIALIZATION_MARKER in _log_path(root, witness, domain).read_text(encoding="utf-8", errors="ignore") for domain in ("domain_A", "domain_B"))
        pids_alive = all(_is_alive(process_state["pids"][domain]) for domain in ("domain_A", "domain_B"))
        if logs_ready and pids_alive:
            break
        if time.monotonic() >= deadline:
            raise ValueError("operational witness acquisition did not reach the two-process overlap barrier")
        time.sleep(0.25)
    r0 = initial_canonical_envelope()
    receipts: dict[str, dict[str, Any]] = {}
    for domain in ("domain_A", "domain_B"):
        receipt = _receipt_from_log(_log_path(root, witness, domain))
        expected = materialization_acceptance_receipt(r0, domain, _process_id(witness, domain))
        if receipt != expected:
            raise ValueError(f"{domain} materialization receipt mismatch")
        if any(_domain_paths(root, domain)["output"].iterdir()):
            raise ValueError("physical interaction occurred before overlap barrier")
        receipts[domain] = receipt
        _write_json(root / "state" / f"{domain}_materialization_receipt.json", receipt)
    overlap = {
        "witness": witness,
        "both_alive_before_first_interaction": True,
        "materialization_receipts_complete_before_first_interaction": True,
        "physical_emission_order": [DOMAIN_TABLE[domain]["input_id"] for domain in WITNESS_MATRIX[witness][0]],
        "harness_presentation_order": [DOMAIN_TABLE[domain]["input_id"] for domain in WITNESS_MATRIX[witness][1]],
        "process_instance_ids": {
            domain: _process_id(witness, domain) for domain in ("domain_A", "domain_B")
        },
        "source_process_pids": process_state["pids"],
    }
    _write_json(root / "state" / "overlap_witness.json", overlap)
    return overlap


def capture_domain_output(root: Path, domain: str) -> dict[str, Any]:
    if domain not in DOMAIN_TABLE:
        raise ValueError("unknown domain")
    prepared = _read_json(root / "state" / "prepared.json")
    witness = prepared["witness"]
    if not (root / "state" / "overlap_witness.json").is_file():
        raise ValueError("overlap barrier must be witnessed before interaction")
    q_path = _q_path(root, domain)
    emission_path = _emission_receipt_path(root, domain)
    expected_names = tuple(sorted((q_path.name, emission_path.name)))
    actual_names = tuple(sorted(path.name for path in _domain_paths(root, domain)["output"].iterdir()))
    if actual_names != expected_names:
        raise ValueError(f"{domain} output must contain exactly Q and its emission receipt")
    r0 = initial_canonical_envelope()
    expected_q = external_evidence_q(r0, domain)
    q_bytes = q_path.read_bytes()
    q = _read_json(q_path)
    if q_bytes != stored_q_bytes(expected_q) or q != expected_q:
        raise ValueError(f"{domain} did not emit exact frozen Q")
    emission = _read_json(emission_path)
    expected_emission = evidence_emission_receipt(
        r0, q, domain, _process_id(witness, domain)
    )
    if emission != expected_emission:
        raise ValueError(f"{domain} emission receipt mismatch")
    interactions_path = root / "state" / "physical_interactions.json"
    trace = _read_json(interactions_path) if interactions_path.is_file() else {"order": []}
    if domain in trace["order"]:
        raise ValueError("duplicate physical interaction capture")
    trace["order"].append(domain)
    _write_json(interactions_path, trace)
    audit = {
        "materialization_domain": domain,
        "allowed_files": [
            {"name": q_path.name, "raw_byte_sha256": _sha(q_path)},
            {"name": emission_path.name, "raw_byte_sha256": _sha(emission_path)},
        ],
        "other_domain_paths_visible": False,
        "shared_writable_proof_state": False,
    }
    _write_json(root / "state" / f"{domain}_output_audit.json", audit)
    return {"Q": q, "emission_receipt": emission, "output_audit": audit, "physical_interaction_order": trace["order"]}


def terminate_pair(root: Path) -> dict[str, Any]:
    if not (root / "state" / "physical_interactions.json").is_file():
        raise ValueError("both physical outputs must be captured before termination")
    trace = _read_json(root / "state" / "physical_interactions.json")
    if set(trace.get("order", [])) != {"domain_A", "domain_B"} or len(trace["order"]) != 2:
        raise ValueError("both physical interactions are required")
    state = _read_json(root / "state" / "processes.json")
    for pid in state["pids"].values():
        if _is_alive(pid):
            os.killpg(pid, signal.SIGTERM)
    deadline = time.monotonic() + 30
    while any(_is_alive(pid) for pid in state["pids"].values()):
        if time.monotonic() >= deadline:
            raise ValueError("source processes did not terminate")
        time.sleep(0.1)
    witness = {
        "witness": state["witness"],
        "before": "construct_BEXT_from_sealed_fixture_set",
        "process_state": {"domain_A": "terminated", "domain_B": "terminated"},
        "proof_outputs_closed": True,
    }
    _write_json(root / "state" / "termination_witness.json", witness)
    return witness


def export_witness(root: Path, destination: Path) -> dict[str, Any]:
    prepared = _read_json(root / "state" / "prepared.json")
    witness = prepared["witness"]
    if not (root / "state" / "termination_witness.json").is_file():
        raise ValueError("source termination witness required before candidate-set validation")
    actual_physical_order = _read_json(root / "state" / "physical_interactions.json")["order"]
    expected_physical, presentation = WITNESS_MATRIX[witness]
    if tuple(actual_physical_order) != expected_physical:
        raise ValueError("captured physical order does not match the selected witness")
    r0 = initial_canonical_envelope()
    q_by_domain: dict[str, dict[str, Any]] = {}
    member_by_domain: dict[str, dict[str, Any]] = {}
    for domain in ("domain_A", "domain_B"):
        q_path = _q_path(root, domain)
        q = _read_json(q_path)
        materialization = _read_json(root / "state" / f"{domain}_materialization_receipt.json")
        emission = _read_json(_emission_receipt_path(root, domain))
        member_by_domain[domain] = admit_external_input_candidate(
            r0, q, q_path.read_bytes(), materialization, emission
        )
        q_by_domain[domain] = q
    fixture = primary_fixture()
    bext, member_map = construct_bext_from_sealed_fixture_set(
        r0, fixture, [member_by_domain[domain] for domain in presentation]
    )
    r1 = resolve_external_batch(r0, bext, member_map)
    canonical_reference = run_witness(witness)
    if canonical_json(r1) != canonical_json(canonical_reference["canonical_checkpoints"]["R1"]):
        raise ValueError("physical evidence path diverged from frozen canonical witness")
    destination.mkdir(parents=True, exist_ok=True)
    exported: list[str] = []
    for domain in ("domain_A", "domain_B"):
        suffix = "A" if domain == "domain_A" else "B"
        sources = {
            f"physical_{witness}_domain_{suffix}_Q.json": _q_path(root, domain),
            f"physical_{witness}_domain_{suffix}_materialization_receipt.json": root / "state" / f"{domain}_materialization_receipt.json",
            f"physical_{witness}_domain_{suffix}_emission_receipt.json": _emission_receipt_path(root, domain),
            f"physical_{witness}_domain_{suffix}_process.log": _log_path(root, witness, domain),
            f"physical_{witness}_domain_{suffix}_input_audit.json": root / "state" / "prepared.json",
            f"physical_{witness}_domain_{suffix}_output_audit.json": root / "state" / f"{domain}_output_audit.json",
        }
        for name, source in sources.items():
            target = destination / name
            if target.exists():
                raise ValueError(f"export target already exists: {name}")
            if name.endswith("input_audit.json"):
                _write_json(target, prepared["input_audits"][domain])
            else:
                shutil.copyfile(source, target)
            exported.append(name)
    shared = {
        f"physical_{witness}_overlap_witness.json": root / "state" / "overlap_witness.json",
        f"physical_{witness}_termination_witness.json": root / "state" / "termination_witness.json",
    }
    for name, source in shared.items():
        shutil.copyfile(source, destination / name)
        exported.append(name)
    lifecycle = {
        "witness": witness,
        "source_record_hash": canonical_hash(r0),
        "source_raw_payload_sha256": raw_payload_sha256(r0),
        "physical_input_ids": [DOMAIN_TABLE[domain]["input_id"] for domain in actual_physical_order],
        "harness_presentation_order": [DOMAIN_TABLE[domain]["input_id"] for domain in presentation],
        "canonical_member_order": bext["member_ids"],
        "both_sources_isolated": True,
        "one_atomic_successor": True,
        "canonical_successor_hash": canonical_hash(r1),
    }
    lifecycle_name = f"physical_{witness}_lifecycle_witness.json"
    _write_json(destination / lifecycle_name, lifecycle)
    return lifecycle


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("prepare", "launch-pair", "record-overlap", "capture-domain", "terminate-pair", "export-witness", "launch-command"),
    )
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--witness", choices=tuple(WITNESS_MATRIX))
    parser.add_argument("--domain", choices=("domain_A", "domain_B"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "prepare":
        if args.witness is None:
            parser.error("prepare requires --witness")
        result = prepare(args.runtime_root, args.witness)
    elif args.command == "launch-pair":
        result = launch_pair(args.runtime_root)
    elif args.command == "record-overlap":
        result = record_overlap(args.runtime_root)
    elif args.command == "capture-domain":
        if args.domain is None:
            parser.error("capture-domain requires --domain")
        result = capture_domain_output(args.runtime_root, args.domain)
    elif args.command == "terminate-pair":
        result = terminate_pair(args.runtime_root)
    elif args.command == "export-witness":
        if args.output is None:
            parser.error("export-witness requires --output")
        result = export_witness(args.runtime_root, args.output)
    else:
        if args.domain is None:
            parser.error("launch-command requires --domain")
        prepared = _read_json(args.runtime_root / "state" / "prepared.json")
        result = {"command": _launch_command(args.runtime_root, prepared["witness"], args.domain)}
    print(canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
