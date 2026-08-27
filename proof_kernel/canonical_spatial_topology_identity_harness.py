"""Acquire the two fresh UE witnesses for the frozen topology proof.

The harness owns representation lifecycle only.  It creates one R0 proof root,
validates the UE receipt, destroys that entire process/root, performs the sole
canonical R0 -> R1 resolution, and only then creates an isolated R1 proof root.
It never manufactures a UE receipt and exposes no Q/evidence path.
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

from canonical_spatial_topology_identity import (
    CANONICAL_PAYLOAD_FILENAME,
    LAUNCH_RECEIPT_FILENAME,
    MATERIALIZATION_MAP_FILENAME,
    RepresentationRejected,
    canonical_hash,
    complete_termination_witness,
    initial_canonical_envelope,
    isolation_witness,
    launch_receipt,
    materialization_failure,
    materialization_map,
    next_consequential_boundary,
    open_termination_observation,
    proof_input_inventory,
    resolve_next_due,
    stored_json_bytes,
    strict_load_stored_json,
    validate_isolation_witness,
    validate_materialization_receipt,
    validate_termination_witness,
)


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "CityMaterializationProof" / "CityMaterializationProof.uproject"
EDITOR = Path("/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor")
RECEIPT_MARKER = "CANONICAL_TOPOLOGY_MATERIALIZATION_RECEIPT:"
FAILURE_MARKER = "CANONICAL_TOPOLOGY_MATERIALIZATION_FAILURE:"
OPERATIONAL_FAILURE_MARKER = "CANONICAL_TOPOLOGY_OPERATIONAL_MATERIALIZATION_FAILURE:"
SOURCE_PROCESS_ID = "topology_source_process_01"
RETURN_PROCESS_ID = "topology_return_process_01"
NON_AUTHORITATIVE_DDC_SEED = Path("/Users/boandersson/Library/Application Support/Epic/UnrealEngine/Common/DerivedDataCache")
DDC_GRAPH = "(ProjectPak,InstalledProjectPak,EnginePak=InstalledEnginePak,EnterprisePak,Local=InstalledLocal)"
NEGATIVE_WITNESS_SCHEMA = "CanonicalTopologyPhysicalNegativeMaterializationWitness.v1"
NEGATIVE_INVENTORY_SCHEMA = "CanonicalTopologyPhysicalNegativeInputInventory.v1"
NEGATIVE_PROCESS_AUDIT_SCHEMA = "CanonicalTopologyPhysicalNegativeProcessAudit.v1"
NEGATIVE_PRELAUNCH_AUDIT_SCHEMA = "CanonicalTopologyPhysicalNegativePrelaunchRejectionAudit.v1"

NEGATIVE_CASES: tuple[tuple[str, str, str], ...] = (
    ("additional_directory", "input_inventory", "unexpected_input_file"),
    ("noncanonical_launch_receipt", "launch_receipt", "invalid_launch_receipt"),
    ("altered_materialization_map", "raw_hash", "artifact_raw_hash_mismatch"),
    ("cross_row_r0_payload_r1_map_receipt", "raw_hash", "artifact_raw_hash_mismatch"),
)

POSITIVE_EVIDENCE_FILENAMES = frozenset({
    "physical_R0_source_input_inventory.json",
    "physical_R0_source_launch_audit.json",
    "physical_R0_source_materialization_receipt.json",
    "physical_R0_source_process.log",
    "physical_R0_source_termination_witness.json",
    "physical_R1_return_input_inventory.json",
    "physical_R1_return_launch_audit.json",
    "physical_R1_return_materialization_receipt.json",
    "physical_R1_return_process.log",
    "physical_canonical_topology_lifecycle_witness.json",
    "physical_fresh_process_isolation_witness.json",
})


def _expected_evidence_filenames() -> frozenset[str]:
    names = set(POSITIVE_EVIDENCE_FILENAMES)
    names.add("physical_negative_materialization_witness.json")
    for case_id, _, _ in NEGATIVE_CASES:
        prefix = f"physical_negative_{case_id}"
        names.update({f"{prefix}_diagnostic.json", f"{prefix}_input_inventory.json"})
        if case_id == "additional_directory":
            names.add(f"{prefix}_prelaunch_rejection_audit.json")
        else:
            names.update({
                f"{prefix}_launch_audit.json",
                f"{prefix}_process.log",
                f"{prefix}_process_audit.json",
            })
    return frozenset(names)


EXPECTED_EVIDENCE_FILENAMES = _expected_evidence_filenames()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(stored_json_bytes(value))


def _paths(root: Path, role: str) -> dict[str, Path]:
    process_root = root / role
    return {
        "process_root": process_root,
        "input": process_root / "input",
        "process": process_root / "process",
        "user": process_root / "user",
        "temp": process_root / "temp",
        "cache": process_root / "cache",
    }


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _assert_no_symlink_escape(root: Path) -> None:
    """A private cache clone may contain neither symlinks nor escaped realpaths."""

    canonical_root = root.resolve(strict=True)
    for directory, directory_names, filenames in os.walk(root, followlinks=False):
        directory_path = Path(directory)
        for name in (*directory_names, *filenames):
            member = directory_path / name
            if member.is_symlink():
                raise ValueError(f"private process tree contains a symlink: {member}")
            if not _is_within(member.resolve(strict=True), canonical_root):
                raise ValueError(f"private process tree member escapes its root: {member}")


def _prepare_process_root(root: Path, role: str, record: dict[str, Any], inventory_role: str) -> dict[str, Any]:
    paths = _paths(root, role)
    if paths["process_root"].exists():
        raise ValueError(f"process root already exists: {paths['process_root']}")
    for key in ("input", "process", "user", "temp", "cache"):
        paths[key].mkdir(parents=True, exist_ok=False)
    if not NON_AUTHORITATIVE_DDC_SEED.is_dir():
        raise ValueError("non-authoritative DDC seed is unavailable")
    if NON_AUTHORITATIVE_DDC_SEED.is_symlink():
        raise ValueError("non-authoritative DDC seed root may not be a symlink")
    local_ddc = paths["cache"] / "DerivedDataCache"
    subprocess.run(["/bin/cp", "-cR", str(NON_AUTHORITATIVE_DDC_SEED), str(local_ddc)], check=True)
    _assert_no_symlink_escape(local_ddc)
    mapping = materialization_map(record)
    _write_json(paths["input"] / CANONICAL_PAYLOAD_FILENAME, record)
    _write_json(paths["input"] / MATERIALIZATION_MAP_FILENAME, mapping)
    _write_json(paths["input"] / LAUNCH_RECEIPT_FILENAME, launch_receipt(record, mapping))
    return proof_input_inventory(paths["input"], inventory_role)


def _launch_configuration(
    root: Path,
    role: str,
    process_id: str,
    *,
    prelaunch_scope: str,
) -> dict[str, Any]:
    """Construct and audit a launch without starting a process."""

    paths = _paths(root, role)
    if not paths["process_root"].is_dir() or not paths["input"].is_dir():
        raise ValueError("process root must be prepared before launch configuration")
    _assert_no_symlink_escape(paths["input"])
    _assert_no_symlink_escape(paths["cache"] / "DerivedDataCache")
    log_path = paths["process"] / "UnrealEditor.log"
    command = [
        str(EDITOR),
        str(PROJECT),
        "-game",
        "-windowed",
        "-ResX=1024",
        "-ResY=640",
        "-NoSound",
        f"-CanonicalTopologyProofInputRoot={paths['input']}",
        f"-CanonicalTopologyProofProcessInstanceId={process_id}",
        f"-UserDir={paths['user']}",
        f"-DDC={DDC_GRAPH}",
        f"-LocalDataCachePath={paths['cache'] / 'DerivedDataCache'}",
        "-SharedDataCachePath=None",
        f"-ZenDataPath={paths['cache'] / 'Zen' / 'Data'}",
        "-notraceserver",
        f"-abslog={log_path}",
    ]
    environment = os.environ.copy()
    environment.update({
        "TMPDIR": str(paths["temp"]),
        "XDG_CACHE_HOME": str(paths["cache"]),
    })
    seed_path = str(NON_AUTHORITATIVE_DDC_SEED.resolve())
    if any(seed_path in value for value in command) or any(seed_path in value for value in environment.values()):
        raise ValueError("global DDC seed root leaked into the UE launch contract")
    audit = {
        "input_root": str(paths["input"].resolve()),
        "process_instance_id": process_id,
        "process_root": str(paths["process_root"].resolve()),
        "truth_bearing_command_line_values": [],
        "user_root": str(paths["user"].resolve()),
        "temp_root": str(paths["temp"].resolve()),
        "cache_root": str(paths["cache"].resolve()),
        "ddc_graph": DDC_GRAPH,
        "cache_seed_clone_non_authoritative": True,
        "cache_seed_source_root_referenced_by_launch": False,
        "cache_seed_clone_contains_symlinks": False,
        "cache_seed_clone_realpaths_contained": True,
        "effective_writable_cache_paths": [],
        "shared_zen_service_used": None,
        "shared_trace_server_used": None,
        "prelaunch_isolation_scope": prelaunch_scope,
        "prelaunch_isolation_validated": prelaunch_scope != "return_after_source_destruction",
        "predecessor_process_group_terminated_before_launch": None,
        "predecessor_process_root_absent_before_launch": None,
        "predecessor_path_absent_from_command": None,
        "predecessor_path_absent_from_environment": None,
    }
    return {
        "audit": audit,
        "command": command,
        "environment": environment,
        "log_path": log_path,
        "paths": paths,
    }


def _process_group_alive(process_group_id: int) -> bool:
    try:
        os.killpg(process_group_id, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _validate_return_prelaunch(
    configuration: dict[str, Any],
    *,
    predecessor_process_group_id: int,
    predecessor_process_root: Path,
) -> None:
    """Prove predecessor isolation before the return Popen is permitted."""

    if _process_group_alive(predecessor_process_group_id):
        raise ValueError("source UE process group survives before return launch")
    if predecessor_process_root.exists():
        raise ValueError("source process root survives before return launch")
    predecessor_text = str(predecessor_process_root.resolve(strict=False))
    command_absent = all(predecessor_text not in value for value in configuration["command"])
    environment_absent = all(predecessor_text not in value for value in configuration["environment"].values())
    if not command_absent or not environment_absent:
        raise ValueError("return launch retains a predecessor path")
    return_root = configuration["paths"]["process_root"]
    if _is_within(return_root, predecessor_process_root) or _is_within(predecessor_process_root, return_root):
        raise ValueError("source and return process roots overlap")
    audit = configuration["audit"]
    if audit["prelaunch_isolation_scope"] != "return_after_source_destruction":
        raise ValueError("return launch has the wrong prelaunch isolation scope")
    audit.update({
        "prelaunch_isolation_validated": True,
        "predecessor_process_group_terminated_before_launch": True,
        "predecessor_process_root_absent_before_launch": True,
        "predecessor_path_absent_from_command": True,
        "predecessor_path_absent_from_environment": True,
    })


def _start_process(configuration: dict[str, Any]) -> subprocess.Popen[bytes]:
    if configuration["audit"]["prelaunch_isolation_validated"] is not True:
        raise ValueError("UE launch attempted before prelaunch isolation validation")
    return subprocess.Popen(
        configuration["command"],
        env=configuration["environment"],
        start_new_session=True,
    )


def _complete_cache_audit(audit: dict[str, Any], log: str) -> None:
    cache_root = Path(audit["cache_root"]).resolve()
    expected_local = (cache_root / "DerivedDataCache").as_posix()
    global_writable_markers = (
        "/Library/Application Support/Epic/UnrealEngine/Common/DerivedDataCache",
        "/Library/Application Support/Epic/UnrealEngine/Common/Zen/Data",
    )
    writable_lines = [line for line in log.splitlines() if "Using data cache path" in line and "Writable" in line]
    if len(writable_lines) != 1 or expected_local not in writable_lines[0]:
        raise ValueError("UE did not use the exact process-local writable DDC path")
    if any(marker in line for marker in global_writable_markers for line in log.splitlines()):
        raise ValueError("UE touched a global writable DDC or Zen data root")
    if "ZenLocal: Using ZenServer" in log or "Local ZenServer AutoLaunch" in log:
        raise ValueError("UE used a shared/local Zen service instead of the isolated filesystem DDC")
    if "Unreal Trace Server launched successfully" in log:
        raise ValueError("UE launched a shared trace server inside an isolated proof process")
    audit["effective_writable_cache_paths"] = [expected_local]
    audit["shared_zen_service_used"] = False
    audit["shared_trace_server_used"] = False


def _wait_for_receipt(process: subprocess.Popen[bytes], log_path: Path, timeout_seconds: float) -> tuple[dict[str, Any], str]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if log_path.is_file():
            log = log_path.read_text(encoding="utf-8", errors="strict")
            failures = [line.partition(FAILURE_MARKER)[2] for line in log.splitlines() if FAILURE_MARKER in line]
            if failures:
                raise ValueError(f"UE refused topology materialization: {failures[-1]}")
            operational_failures = [line.partition(OPERATIONAL_FAILURE_MARKER)[2] for line in log.splitlines() if OPERATIONAL_FAILURE_MARKER in line]
            if operational_failures:
                raise ValueError(f"UE representation staging failed: {operational_failures[-1]}")
            receipts = [line.partition(RECEIPT_MARKER)[2] for line in log.splitlines() if RECEIPT_MARKER in line]
            if receipts:
                if len(receipts) != 1:
                    raise ValueError("UE must emit exactly one topology materialization receipt")
                receipt = strict_load_stored_json((receipts[0] + "\n").encode("utf-8"))
                if not isinstance(receipt, dict):
                    raise ValueError("UE receipt is not an object")
                return receipt, log
        if process.poll() is not None:
            raise ValueError(f"UE process exited before receipt with status {process.returncode}")
        time.sleep(0.25)
    raise TimeoutError("timed out waiting for UE topology receipt")


def _wait_for_process_group_death(process_group_id: int, timeout_seconds: float) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if not _process_group_alive(process_group_id):
            return True
        time.sleep(0.1)
    return not _process_group_alive(process_group_id)


def _terminate(process: subprocess.Popen[bytes]) -> None:
    """Terminate the full session process group and prove that it is gone."""

    process_group_id = process.pid
    if _process_group_alive(process_group_id):
        os.killpg(process_group_id, signal.SIGTERM)
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        pass
    if not _wait_for_process_group_death(process_group_id, 10.0):
        if _process_group_alive(process_group_id):
            os.killpg(process_group_id, signal.SIGKILL)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        if not _wait_for_process_group_death(process_group_id, 5.0):
            raise ValueError("UE process group remains alive after SIGKILL")
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired as exc:
        raise ValueError("UE process leader remains waitable after process-group death") from exc
    if _process_group_alive(process_group_id):
        raise ValueError("UE process group remains alive after termination")


def _copy_evidence(evidence: Path, name: str, value: Any) -> None:
    _write_json(evidence / name, value)


def _negative_input_inventory(input_root: Path, case_id: str) -> dict[str, Any]:
    _assert_no_symlink_escape(input_root)
    members: list[dict[str, Any]] = []
    for member in sorted(input_root.iterdir(), key=lambda path: path.name):
        if member.is_file():
            member_type = "regular_file"
            raw_sha256: str | None = hashlib.sha256(member.read_bytes()).hexdigest()
        elif member.is_dir():
            member_type = "directory"
            raw_sha256 = None
        else:
            raise ValueError("negative proof-input member has an unsupported type")
        members.append({
            "filename": member.name,
            "member_type": member_type,
            "raw_sha256": raw_sha256,
        })
    return {
        "case_id": case_id,
        "input_role": "negative_materialization",
        "inventory_schema": NEGATIVE_INVENTORY_SCHEMA,
        "members": members,
    }


def _prepare_negative_case(
    runtime_root: Path,
    case_id: str,
    r0: dict[str, Any],
    r1: dict[str, Any],
) -> dict[str, Any]:
    role = f"negative_{case_id}"
    _prepare_process_root(runtime_root, role, r0, "R0_source")
    paths = _paths(runtime_root, role)
    input_root = paths["input"]
    if case_id == "additional_directory":
        (input_root / "unexpected_directory").mkdir()
    elif case_id == "noncanonical_launch_receipt":
        receipt = launch_receipt(r0, materialization_map(r0))
        noncanonical = (json.dumps(receipt, sort_keys=False, indent=2, ensure_ascii=True) + "\n").encode("utf-8")
        (input_root / LAUNCH_RECEIPT_FILENAME).write_bytes(noncanonical)
    elif case_id == "altered_materialization_map":
        mapping = materialization_map(r0)
        mapping["mapping_id"] = "topology_materialization_map_altered"
        _write_json(input_root / MATERIALIZATION_MAP_FILENAME, mapping)
    elif case_id == "cross_row_r0_payload_r1_map_receipt":
        mapping = materialization_map(r1)
        _write_json(input_root / MATERIALIZATION_MAP_FILENAME, mapping)
        _write_json(input_root / LAUNCH_RECEIPT_FILENAME, launch_receipt(r1, mapping))
    else:
        raise ValueError(f"unsupported negative physical case: {case_id}")
    return {
        "inventory": _negative_input_inventory(input_root, case_id),
        "paths": paths,
        "role": role,
    }


def _parse_marker_payload(payload: str) -> dict[str, Any]:
    parsed = strict_load_stored_json((payload + "\n").encode("utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("UE marker payload is not an object")
    return parsed


def _negative_log_observation(
    log: str,
    expected_stage: str,
    expected_reason: str,
) -> tuple[dict[str, Any], dict[str, int | bool]]:
    failures = [
        _parse_marker_payload(line.partition(FAILURE_MARKER)[2])
        for line in log.splitlines()
        if FAILURE_MARKER in line
    ]
    receipt_count = sum(RECEIPT_MARKER in line for line in log.splitlines())
    operational_failure_count = sum(OPERATIONAL_FAILURE_MARKER in line for line in log.splitlines())
    if len(failures) != 1:
        raise ValueError("negative UE witness must emit exactly one frozen failure marker")
    expected = materialization_failure(expected_stage, expected_reason)
    if failures[0] != expected:
        raise ValueError("negative UE diagnostic does not match its frozen earliest disposition")
    if receipt_count != 0 or operational_failure_count != 0:
        raise ValueError("negative UE witness emitted a receipt or operational failure")
    return failures[0], {
        "exactly_one_failure_marker": True,
        "materialization_receipt_count": receipt_count,
        "operational_failure_count": operational_failure_count,
    }


def _wait_for_failure(
    process: subprocess.Popen[bytes],
    log_path: Path,
    expected_stage: str,
    expected_reason: str,
    timeout_seconds: float,
) -> tuple[dict[str, Any], str]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if log_path.is_file():
            log = log_path.read_text(encoding="utf-8", errors="strict")
            if FAILURE_MARKER in log:
                diagnostic, _ = _negative_log_observation(log, expected_stage, expected_reason)
                return diagnostic, log
            if RECEIPT_MARKER in log or OPERATIONAL_FAILURE_MARKER in log:
                raise ValueError("negative UE witness crossed an unauthorized outcome path")
        if process.poll() is not None:
            raise ValueError(f"negative UE process exited before diagnostic with status {process.returncode}")
        time.sleep(0.25)
    raise TimeoutError("timed out waiting for UE topology failure diagnostic")


def _acquire_negative_witnesses(
    runtime_root: Path,
    evidence: Path,
    r0: dict[str, Any],
    r1: dict[str, Any],
    timeout_seconds: float,
) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    for index, (case_id, expected_stage, expected_reason) in enumerate(NEGATIVE_CASES, start=1):
        prepared = _prepare_negative_case(runtime_root, case_id, r0, r1)
        prefix = f"physical_negative_{case_id}"
        diagnostic_name = f"{prefix}_diagnostic.json"
        inventory_name = f"{prefix}_input_inventory.json"
        _copy_evidence(evidence, inventory_name, prepared["inventory"])

        if case_id == "additional_directory":
            try:
                proof_input_inventory(prepared["paths"]["input"], "R0_source")
            except RepresentationRejected as exc:
                diagnostic = exc.diagnostic
            else:
                raise ValueError("additional-directory prelaunch gate failed open")
            expected = materialization_failure(expected_stage, expected_reason)
            if diagnostic != expected:
                raise ValueError("prelaunch rejection does not match the frozen diagnostic")
            prelaunch_name = f"{prefix}_prelaunch_rejection_audit.json"
            prelaunch = {
                "audit_schema": NEGATIVE_PRELAUNCH_AUDIT_SCHEMA,
                "canonical_resolution_invoked": False,
                "canonical_write_attempted": False,
                "case_id": case_id,
                "process_launched": False,
                "reason_code": expected_reason,
                "rejection_stage": expected_stage,
            }
            _copy_evidence(evidence, diagnostic_name, diagnostic)
            _copy_evidence(evidence, prelaunch_name, prelaunch)
            cases.append({
                "canonical_resolution_invoked": False,
                "canonical_write_attempted": diagnostic["canonical_write_attempted"],
                "case_id": case_id,
                "diagnostic_artifact": diagnostic_name,
                "expected_reason_code": expected_reason,
                "expected_stage": expected_stage,
                "frozen_failure_marker_count": 0,
                "input_inventory_artifact": inventory_name,
                "launch_audit_artifact": None,
                "materialization_receipt_count": 0,
                "materialization_started": diagnostic["materialization_started"],
                "mode": "prelaunch_rejection",
                "operational_failure_count": 0,
                "prelaunch_rejection_audit_artifact": prelaunch_name,
                "private_cache_audit_passed": None,
                "process_audit_artifact": None,
                "process_group_alive_after_termination": None,
                "process_launched": False,
                "process_log_artifact": None,
            })
            continue

        process_id = f"topology_negative_process_{index:02d}"
        configuration = _launch_configuration(
            runtime_root,
            prepared["role"],
            process_id,
            prelaunch_scope="negative_no_predecessor",
        )
        process = _start_process(configuration)
        diagnostic_observed = False
        try:
            _, _ = _wait_for_failure(
                process,
                configuration["log_path"],
                expected_stage,
                expected_reason,
                timeout_seconds,
            )
            diagnostic_observed = True
        finally:
            _terminate(process)
        if _process_group_alive(process.pid):
            raise ValueError("negative UE process group survived termination")
        log = configuration["log_path"].read_text(encoding="utf-8", errors="strict")
        diagnostic, observation = _negative_log_observation(log, expected_stage, expected_reason)
        _complete_cache_audit(configuration["audit"], log)
        process_audit = {
            "audit_schema": NEGATIVE_PROCESS_AUDIT_SCHEMA,
            "canonical_resolution_invoked": False,
            "canonical_write_attempted": False,
            "case_id": case_id,
            "diagnostic_observed_before_termination": diagnostic_observed,
            "operational_process_instance_id": process_id,
            "process_group_alive_after_termination": False,
            "process_launched": True,
            "process_leader_terminated": process.poll() is not None,
        }
        launch_name = f"{prefix}_launch_audit.json"
        log_name = f"{prefix}_process.log"
        process_audit_name = f"{prefix}_process_audit.json"
        _copy_evidence(evidence, diagnostic_name, diagnostic)
        _copy_evidence(evidence, launch_name, configuration["audit"])
        (evidence / log_name).write_text(log, encoding="utf-8")
        _copy_evidence(evidence, process_audit_name, process_audit)
        cases.append({
            "canonical_resolution_invoked": False,
            "canonical_write_attempted": diagnostic["canonical_write_attempted"],
            "case_id": case_id,
            "diagnostic_artifact": diagnostic_name,
            "expected_reason_code": expected_reason,
            "expected_stage": expected_stage,
            "frozen_failure_marker_count": 1 if observation["exactly_one_failure_marker"] else 0,
            "input_inventory_artifact": inventory_name,
            "launch_audit_artifact": launch_name,
            "materialization_receipt_count": observation["materialization_receipt_count"],
            "materialization_started": diagnostic["materialization_started"],
            "mode": "compiled_adapter_refusal",
            "operational_failure_count": observation["operational_failure_count"],
            "prelaunch_rejection_audit_artifact": None,
            "private_cache_audit_passed": True,
            "process_audit_artifact": process_audit_name,
            "process_group_alive_after_termination": process_audit["process_group_alive_after_termination"],
            "process_launched": True,
            "process_log_artifact": log_name,
        })
    witness = {
        "cases": cases,
        "compiled_adapter_refusal_process_count": 3,
        "prelaunch_rejection_count": 1,
        "successful_materialization_process_count": 2,
        "witness_schema": NEGATIVE_WITNESS_SCHEMA,
    }
    _copy_evidence(evidence, "physical_negative_materialization_witness.json", witness)
    return witness


def _acquire_staged(runtime_root: Path, evidence_output: Path, timeout_seconds: float) -> dict[str, Any]:
    if runtime_root.exists() and any(runtime_root.iterdir()):
        raise ValueError("runtime root must be new or empty")
    runtime_root.mkdir(parents=True, exist_ok=True)
    evidence_output.mkdir(parents=True, exist_ok=True)

    r0 = initial_canonical_envelope()
    h0 = canonical_hash(r0)
    source_inventory = _prepare_process_root(runtime_root, "source", r0, "R0_source")
    source_paths = _paths(runtime_root, "source")
    source_configuration = _launch_configuration(
        runtime_root,
        "source",
        SOURCE_PROCESS_ID,
        prelaunch_scope="source_no_predecessor",
    )
    source_process = _start_process(source_configuration)
    source_log_path = source_configuration["log_path"]
    try:
        source_receipt, _ = _wait_for_receipt(source_process, source_log_path, timeout_seconds)
        validate_materialization_receipt(r0, materialization_map(r0), source_receipt)
        if source_receipt["operational_process_instance_id"] != SOURCE_PROCESS_ID:
            raise ValueError("source materialization receipt has the wrong operational process identity")
        if source_process.poll() is not None:
            raise ValueError("source UE process must be alive when its receipt is accepted")
    finally:
        _terminate(source_process)
    if _process_group_alive(source_process.pid):
        raise ValueError("source UE process group survived termination")
    termination_observation = open_termination_observation(
        SOURCE_PROCESS_ID,
        h0,
        process_alive=False,
    )
    source_log = source_log_path.read_text(encoding="utf-8", errors="strict")
    _complete_cache_audit(source_configuration["audit"], source_log)

    # Preserve only detached evidence before deleting the complete source root.
    _copy_evidence(evidence_output, "physical_R0_source_input_inventory.json", source_inventory)
    _copy_evidence(evidence_output, "physical_R0_source_materialization_receipt.json", source_receipt)
    (evidence_output / "physical_R0_source_process.log").write_text(source_log, encoding="utf-8")
    _copy_evidence(evidence_output, "physical_R0_source_launch_audit.json", source_configuration["audit"])
    original_source_root = source_paths["process_root"]
    shutil.rmtree(original_source_root)
    if original_source_root.exists():
        raise ValueError("source process root survived destruction")

    # Canonical discovery/resolution happens only after source process/root death.
    boundary = next_consequential_boundary(r0)
    if boundary is None:
        raise ValueError("R0 did not rediscover its exact canonical boundary")
    r1 = resolve_next_due(r0, boundary)
    h1 = canonical_hash(r1)
    terminated = complete_termination_witness(termination_observation, h1)
    validate_termination_witness(terminated, SOURCE_PROCESS_ID, h0, h1)
    _copy_evidence(evidence_output, "physical_R0_source_termination_witness.json", terminated)

    return_inventory = _prepare_process_root(runtime_root, "return", r1, "R1_return")
    return_paths = _paths(runtime_root, "return")
    return_configuration = _launch_configuration(
        runtime_root,
        "return",
        RETURN_PROCESS_ID,
        prelaunch_scope="return_after_source_destruction",
    )
    _validate_return_prelaunch(
        return_configuration,
        predecessor_process_group_id=source_process.pid,
        predecessor_process_root=original_source_root,
    )
    return_process = _start_process(return_configuration)
    return_log_path = return_configuration["log_path"]
    try:
        return_receipt, _ = _wait_for_receipt(return_process, return_log_path, timeout_seconds)
        validate_materialization_receipt(r1, materialization_map(r1), return_receipt)
        if return_receipt["operational_process_instance_id"] != RETURN_PROCESS_ID:
            raise ValueError("return materialization receipt has the wrong operational process identity")
    finally:
        _terminate(return_process)
    if _process_group_alive(return_process.pid):
        raise ValueError("return UE process group survived termination")
    return_log = return_log_path.read_text(encoding="utf-8", errors="strict")
    _complete_cache_audit(return_configuration["audit"], return_log)

    isolated = isolation_witness(
        SOURCE_PROCESS_ID,
        RETURN_PROCESS_ID,
        original_source_root,
        return_paths["process_root"],
        Path(source_configuration["audit"]["cache_root"]),
        Path(return_configuration["audit"]["cache_root"]),
    )
    validate_isolation_witness(isolated)
    _copy_evidence(evidence_output, "physical_fresh_process_isolation_witness.json", isolated)

    _copy_evidence(evidence_output, "physical_R1_return_input_inventory.json", return_inventory)
    _copy_evidence(evidence_output, "physical_R1_return_materialization_receipt.json", return_receipt)
    (evidence_output / "physical_R1_return_process.log").write_text(return_log, encoding="utf-8")
    _copy_evidence(evidence_output, "physical_R1_return_launch_audit.json", return_configuration["audit"])

    source_actors = source_receipt["operational_actor_instance_ids"]
    return_actors = return_receipt["operational_actor_instance_ids"]
    role_pairs_differ = all(
        (source_receipt["operational_process_instance_id"], source_actors[role]) !=
        (return_receipt["operational_process_instance_id"], return_actors[role])
        for role in source_actors
    )
    lifecycle = {
        "canonical_hashes": {"R0": h0, "R1": h1},
        "canonical_resolution_after_source_destruction": True,
        "endpoint_relation_preserved": source_receipt["materialized_endpoint_site_ids"] == return_receipt["materialized_endpoint_site_ids"],
        "fresh_process_actor_pairs_differ_by_role": role_pairs_differ,
        "process_ids_distinct": source_receipt["operational_process_instance_id"] != return_receipt["operational_process_instance_id"],
        "return_access_state": return_receipt["materialized_access_state"],
        "return_received_R1_only": True,
        "source_access_state": source_receipt["materialized_access_state"],
        "source_process_root_destroyed": True,
    }
    if not all((
        lifecycle["canonical_resolution_after_source_destruction"],
        lifecycle["endpoint_relation_preserved"],
        lifecycle["fresh_process_actor_pairs_differ_by_role"],
        lifecycle["process_ids_distinct"],
        lifecycle["return_received_R1_only"],
        lifecycle["source_process_root_destroyed"],
        lifecycle["source_access_state"] == "available",
        lifecycle["return_access_state"] == "blocked",
    )):
        raise ValueError("fresh Unreal lifecycle oracle failed")
    _copy_evidence(evidence_output, "physical_canonical_topology_lifecycle_witness.json", lifecycle)
    _acquire_negative_witnesses(runtime_root, evidence_output, r0, r1, timeout_seconds)
    observed_artifacts = frozenset(path.name for path in evidence_output.iterdir() if path.is_file())
    if observed_artifacts != EXPECTED_EVIDENCE_FILENAMES or any(not path.is_file() for path in evidence_output.iterdir()):
        raise ValueError("staged topology physical evidence artifact membership drift")
    return lifecycle


def acquire(runtime_root: Path, evidence_output: Path, timeout_seconds: float = 120.0) -> dict[str, Any]:
    """Acquire into private staging and publish exactly once after all witnesses pass."""

    if evidence_output.exists():
        raise ValueError("final evidence output must not exist")
    if runtime_root.is_symlink():
        raise ValueError("runtime root may not be a symlink")
    if _is_within(evidence_output, runtime_root) or _is_within(runtime_root, evidence_output):
        raise ValueError("runtime and final evidence roots must be disjoint")
    if runtime_root.exists() and any(runtime_root.iterdir()):
        raise ValueError("runtime root must be new or empty")
    evidence_output.parent.mkdir(parents=True, exist_ok=True)
    staging = evidence_output.parent / f".{evidence_output.name}.staging-{os.getpid()}-{time.monotonic_ns()}"
    if staging.exists():
        raise ValueError("private evidence staging path unexpectedly exists")
    try:
        result = _acquire_staged(runtime_root, staging, timeout_seconds)
        if evidence_output.exists():
            raise ValueError("final evidence output appeared before publication")
        os.replace(staging, evidence_output)
        return result
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging)
        if evidence_output.exists():
            raise RuntimeError("failed acquisition escaped a published evidence directory")
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("acquire",))
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--evidence-output", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=float, default=120.0)
    args = parser.parse_args()
    if args.command == "acquire":
        print(json.dumps(acquire(args.runtime_root, args.evidence_output, args.timeout_seconds), sort_keys=True))


if __name__ == "__main__":
    main()
