"""Regenerate and verify Canonical Spatial Topology Identity v0.1.0.

Canonical artifacts are regenerated from the frozen reference implementation.
Real UE logs and receipts are imported physical evidence and are only
validated here; this verifier never manufactures them.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from pathlib import Path
from typing import Any

from canonical_spatial_topology_identity import (
    ARTIFACT_NAMES,
    CANONICAL_PAYLOAD_FILENAME,
    FROZEN_ADVERSARIAL_MATRIX,
    FROZEN_REPRESENTATION_DIAGNOSTICS,
    LAUNCH_RECEIPT_FILENAME,
    MATERIALIZATION_MAP_FILENAME,
    SITE_IDS,
    canonical_hash,
    initial_canonical_envelope,
    launch_receipt,
    materialization_map,
    next_consequential_boundary,
    proof_run,
    raw_stored_sha256,
    resolve_next_due,
    runtime_fail_closed_results,
    stored_json_bytes,
    strict_load_stored_json,
    validate_isolation_witness,
    validate_materialization_receipt,
    validate_termination_witness,
    write_artifacts,
)


ROOT = Path(__file__).resolve().parents[1]
RECORDS = Path(__file__).with_name("CanonicalSpatialTopologyIdentityProofRecords")
EVIDENCE = ROOT / "Canonical Spatial Topology Identity Proof Evidence - v0.1.0.md"
MANIFEST = ROOT / "Canonical Spatial Topology Identity Proof - v0.1.0 SHA256SUMS.txt"
SOURCE_PROCESS_ID = "topology_source_process_01"
RETURN_PROCESS_ID = "topology_return_process_01"
RECEIPT_MARKER = "CANONICAL_TOPOLOGY_MATERIALIZATION_RECEIPT:"
FAILURE_MARKER = "CANONICAL_TOPOLOGY_MATERIALIZATION_FAILURE:"
OPERATIONAL_FAILURE_MARKER = "CANONICAL_TOPOLOGY_OPERATIONAL_MATERIALIZATION_FAILURE:"
UE_BUILD_VERSION = "++UE5+Release-5.8-CL-55116800"
UE_ENGINE_VERSION = "5.8.0-55116800+++UE5+Release-5.8"
UE_RELEASE_VERSION = "5.8.0"
DDC_GRAPH = "(ProjectPak,InstalledProjectPak,EnginePak=InstalledEnginePak,EnterprisePak,Local=InstalledLocal)"

NEGATIVE_PHYSICAL_CASES: dict[str, tuple[str, str]] = {
    "additional_directory": ("input_inventory", "unexpected_input_file"),
    "noncanonical_launch_receipt": ("launch_receipt", "invalid_launch_receipt"),
    "altered_materialization_map": ("raw_hash", "artifact_raw_hash_mismatch"),
    "cross_row_r0_payload_r1_map_receipt": ("raw_hash", "artifact_raw_hash_mismatch"),
}


def _negative_physical_artifacts() -> tuple[str, ...]:
    members = ["physical_negative_materialization_witness.json"]
    for case_id in NEGATIVE_PHYSICAL_CASES:
        prefix = f"physical_negative_{case_id}"
        members.extend((f"{prefix}_diagnostic.json", f"{prefix}_input_inventory.json"))
        if case_id == "additional_directory":
            members.append(f"{prefix}_prelaunch_rejection_audit.json")
        else:
            members.extend((
                f"{prefix}_launch_audit.json",
                f"{prefix}_process.log",
                f"{prefix}_process_audit.json",
            ))
    return tuple(members)

PHYSICAL_ARTIFACTS = (
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
) + _negative_physical_artifacts()

SOURCE_PATHS = (
    "README.md",
    "Canonical Spatial Topology Identity Proof - Draft.md",
    "Canonical Spatial Topology Identity Proof Evidence - v0.1.0.md",
    "Canonical Spatial Topology Identity Proof - v0.1.0 SHA256SUMS.txt",  # removed by release_paths
    "Co-op Open-City FPS Simulation - v0.7 Working Continuation.md",
    "THE_CITY Current Proof State and Repo-Agent Instruction - v0.1.0.md",
    "THE_CITY Development Capacity and Progress Note - v0.1.10.md",
    "THE_CITY Modern Canonical Machine Contract - Draft.md",
    "THE_CITY_Conceptual_City_Topology_Developer_Framing_v0.3.0.md",
    "Concurrent External Evidence Arbitration Proof - Draft.md",
    "Concurrent External Evidence Arbitration Proof Evidence - v0.1.0.md",
    "Concurrent External Evidence Arbitration Proof - v0.1.0 SHA256SUMS.txt",
    "Proof Kernel Implementation Evidence - v0.1.1.md",
    "Unreal Materialization Proof Evidence - v0.1.0.md",
    "Bridge Access Persistence Round-Trip Evidence - v0.1.1.md",
    "Integrated Unreal Promotion-Unload-Repromotion Proof Evidence - v0.1.0.md",
    "Record-Relative Chronological Resolution Proof Evidence - v0.1.0.md",
    "Same-Clock Successor Semantics Proof Evidence - v0.1.0.md",
    "Resolution Semantics Law - v0.1.1.md",
    "proof_kernel/kernel.py",
    "proof_kernel/canonical_spatial_topology_identity.py",
    "proof_kernel/canonical_spatial_topology_identity_harness.py",
    "proof_kernel/test_canonical_spatial_topology_identity.py",
    "proof_kernel/verify_canonical_spatial_topology_identity_release.py",
    "CityMaterializationProof/CityMaterializationProof.uproject",
    "CityMaterializationProof/README.md",
)

UE_BUILD_PATHS = tuple(sorted(
    path.relative_to(ROOT).as_posix()
    for directory in (ROOT / "CityMaterializationProof/Config", ROOT / "CityMaterializationProof/Source")
    for path in directory.rglob("*")
    if path.is_file() and path.suffix in {".ini", ".cs", ".h", ".cpp"}
))


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load(name: str) -> Any:
    return strict_load_stored_json((RECORDS / name).read_bytes())


def _receipt_from_log(name: str) -> dict[str, Any]:
    log = (RECORDS / name).read_text(encoding="utf-8", errors="strict")
    if FAILURE_MARKER in log or OPERATIONAL_FAILURE_MARKER in log:
        raise ValueError(f"positive UE log contains a materialization failure: {name}")
    receipts = [line.partition(RECEIPT_MARKER)[2] for line in log.splitlines() if RECEIPT_MARKER in line]
    if len(receipts) != 1:
        raise ValueError(f"UE log must contain exactly one topology receipt: {name}")
    value = strict_load_stored_json((receipts[0] + "\n").encode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"UE receipt is not an object: {name}")
    return value


def _expected_embedded_artifact_identities() -> dict[str, str]:
    """Return the exact identities the compiled adapter is allowed to pin.

    H0/H1 are semantic canonical-record identities.  D/M/L are exact stored
    byte identities for the payload, materialization map, and launch receipt.
    Keeping those classes explicit prevents a matching constant *name* from
    passing the source audit while its sealed value has drifted.
    """

    r0 = _load("canonical_topology_R0.json")
    r1 = _load("canonical_topology_R1.json")
    return {
        "H0": canonical_hash(r0),
        "H1": canonical_hash(r1),
        "D0": _sha(RECORDS / "canonical_topology_R0.json"),
        "D1": _sha(RECORDS / "canonical_topology_R1.json"),
        "M0": _sha(RECORDS / "canonical_topology_materialization_map_R0.json"),
        "M1": _sha(RECORDS / "canonical_topology_materialization_map_R1.json"),
        "L0": _sha(RECORDS / "canonical_topology_launch_receipt_R0.json"),
        "L1": _sha(RECORDS / "canonical_topology_launch_receipt_R1.json"),
    }


def _embedded_artifact_identities(adapter: str) -> dict[str, str]:
    matches = re.findall(
        r'constexpr\s+TCHAR\s+(H[01]|D[01]|M[01]|L[01])\[\]\s*=\s*TEXT\("([0-9a-f]{64})"\);',
        adapter,
    )
    observed = dict(matches)
    if len(matches) != 8 or len(observed) != 8:
        return {}
    return observed


def _assert_isolated_cache_log(name: str, launch_audit: dict[str, Any]) -> None:
    log = (RECORDS / name).read_text(encoding="utf-8", errors="strict")
    expected_local = (Path(launch_audit["cache_root"]).resolve() / "DerivedDataCache").as_posix()
    writable_lines = [line for line in log.splitlines() if "Using data cache path" in line and "Writable" in line]
    if len(writable_lines) != 1 or expected_local not in writable_lines[0]:
        raise ValueError(f"UE log does not prove exact process-local writable DDC: {name}")
    forbidden = (
        "/Library/Application Support/Epic/UnrealEngine/Common/DerivedDataCache",
        "/Library/Application Support/Epic/UnrealEngine/Common/Zen/Data",
        "ZenLocal: Using ZenServer",
        "Local ZenServer AutoLaunch",
        "Unreal Trace Server launched successfully",
    )
    if any(marker in log for marker in forbidden):
        raise ValueError(f"UE log exposes shared writable cache/Zen state: {name}")
    if (
        launch_audit["ddc_graph"] != DDC_GRAPH
        or launch_audit["effective_writable_cache_paths"] != [expected_local]
        or launch_audit["shared_zen_service_used"] is not False
        or launch_audit["shared_trace_server_used"] is not False
    ):
        raise ValueError(f"launch cache audit contradicts UE log: {name}")


def _assert_unreal_58_log(name: str) -> None:
    """Bind every launched witness to the exact reviewed UE 5.8 build."""

    log = (RECORDS / name).read_text(encoding="utf-8", errors="strict")
    required_once = (
        f'Metadata set : buildversion="{UE_BUILD_VERSION}"',
        f'Metadata set : engineversion="{UE_ENGINE_VERSION}"',
        f'Metadata set : enginereleaseversion="{UE_RELEASE_VERSION}"',
        f"LogInit: Build: {UE_BUILD_VERSION}",
        f"LogInit: Engine Version: {UE_ENGINE_VERSION}",
        "LogInit: Branch Name: ++UE5+Release-5.8",
    )
    if any(log.count(marker) != 1 for marker in required_once):
        raise ValueError(f"UE 5.8 build identity is missing, duplicated, or contradictory: {name}")
    module_loads = re.findall(
        r"LogModuleManager: InternalLoadLibrary: 'CityMaterializationProof' \('[^'\r\n]*/CityMaterializationProof/Binaries/Mac/libUnrealEditor-CityMaterializationProof\.dylib'\)",
        log,
    )
    if len(module_loads) != 1:
        raise ValueError(f"current CityMaterializationProof editor module load is not singularly witnessed: {name}")


LAUNCH_AUDIT_KEYS = {
    "cache_root", "cache_seed_clone_contains_symlinks", "cache_seed_clone_non_authoritative",
    "cache_seed_clone_realpaths_contained", "cache_seed_source_root_referenced_by_launch",
    "ddc_graph", "effective_writable_cache_paths", "input_root", "prelaunch_isolation_scope",
    "prelaunch_isolation_validated", "predecessor_path_absent_from_command",
    "predecessor_path_absent_from_environment", "predecessor_process_group_terminated_before_launch",
    "predecessor_process_root_absent_before_launch", "process_instance_id", "process_root",
    "shared_trace_server_used", "shared_zen_service_used", "temp_root", "truth_bearing_command_line_values", "user_root",
}


def _is_strict_child(child: Path, parent: Path) -> bool:
    child, parent = child.resolve(), parent.resolve()
    return child != parent and child.is_relative_to(parent)


def _validate_launch_audit(
    audit: dict[str, Any],
    *,
    process_id: str | None = None,
    predecessor_required: bool,
    expected_scope: str,
) -> None:
    if set(audit) != LAUNCH_AUDIT_KEYS:
        raise ValueError("launch isolation audit shape drift")
    if not isinstance(audit["process_instance_id"], str) or not audit["process_instance_id"]:
        raise ValueError("launch process identity is missing")
    if process_id is not None and audit["process_instance_id"] != process_id:
        raise ValueError("launch process identity drift")
    if audit["truth_bearing_command_line_values"] != []:
        raise ValueError("truth-bearing selector reached UE")
    if (
        audit["ddc_graph"] != DDC_GRAPH
        or audit["cache_seed_clone_non_authoritative"] is not True
        or audit["cache_seed_source_root_referenced_by_launch"] is not False
        or audit["cache_seed_clone_contains_symlinks"] is not False
        or audit["cache_seed_clone_realpaths_contained"] is not True
        or audit["prelaunch_isolation_validated"] is not True
        or audit["prelaunch_isolation_scope"] != expected_scope
        or audit["shared_trace_server_used"] is not False
    ):
        raise ValueError("process-local cache/prelaunch isolation classification drift")
    process_root = Path(audit["process_root"])
    child_keys = ("input_root", "user_root", "temp_root", "cache_root")
    child_roots = [Path(audit[key]) for key in child_keys]
    if not all(path.is_absolute() and _is_strict_child(path, process_root) for path in child_roots):
        raise ValueError("launch-owned roots are not strictly contained by the process root")
    expected_children = {
        "input_root": process_root.resolve() / "input",
        "user_root": process_root.resolve() / "user",
        "temp_root": process_root.resolve() / "temp",
        "cache_root": process_root.resolve() / "cache",
    }
    if any(Path(audit[key]).resolve() != expected_children[key] for key in child_keys):
        raise ValueError("launch-owned root layout drift")
    predecessor_fields = (
        "predecessor_process_group_terminated_before_launch",
        "predecessor_process_root_absent_before_launch",
        "predecessor_path_absent_from_command",
        "predecessor_path_absent_from_environment",
    )
    if predecessor_required:
        if not all(audit[key] is True for key in predecessor_fields):
            raise ValueError("return launch did not prove predecessor isolation before process start")
    elif not all(audit[key] is None for key in predecessor_fields):
        raise ValueError("source/negative launch claims a nonexistent predecessor transition")


def _validate_launch_set_disjoint(audits: list[dict[str, Any]]) -> None:
    if len({audit["process_instance_id"] for audit in audits}) != len(audits):
        raise ValueError("UE launch process identities are not unique")
    for index, left in enumerate(audits):
        left_roots = [Path(left[key]).resolve() for key in ("process_root", "input_root", "user_root", "temp_root", "cache_root")]
        for right in audits[index + 1:]:
            right_roots = [Path(right[key]).resolve() for key in ("process_root", "input_root", "user_root", "temp_root", "cache_root")]
            for left_root in left_roots:
                for right_root in right_roots:
                    if (
                        left_root == right_root
                        or left_root.is_relative_to(right_root)
                        or right_root.is_relative_to(left_root)
                    ):
                        raise ValueError("UE process proof roots overlap across launches")


def _validate_negative_materialization_witnesses() -> list[dict[str, Any]]:
    r0 = _load("canonical_topology_R0.json")
    r1 = _load("canonical_topology_R1.json")
    map0, map1 = materialization_map(r0), materialization_map(r1)
    receipt0, receipt1 = launch_receipt(r0, map0), launch_receipt(r1, map1)
    noncanonical_receipt0 = (json.dumps(receipt0, sort_keys=False, indent=2, ensure_ascii=True) + "\n").encode("utf-8")
    altered_map0 = dict(map0)
    altered_map0["mapping_id"] = "topology_materialization_map_altered"

    def file_member(filename: str, raw: bytes) -> dict[str, Any]:
        return {
            "filename": filename,
            "member_type": "regular_file",
            "raw_sha256": hashlib.sha256(raw).hexdigest(),
        }

    common_d0 = file_member(CANONICAL_PAYLOAD_FILENAME, stored_json_bytes(r0))
    expected_inventory_members = {
        "additional_directory": sorted((
            common_d0,
            file_member(LAUNCH_RECEIPT_FILENAME, stored_json_bytes(receipt0)),
            file_member(MATERIALIZATION_MAP_FILENAME, stored_json_bytes(map0)),
            {"filename": "unexpected_directory", "member_type": "directory", "raw_sha256": None},
        ), key=lambda item: item["filename"]),
        "noncanonical_launch_receipt": sorted((
            common_d0,
            file_member(LAUNCH_RECEIPT_FILENAME, noncanonical_receipt0),
            file_member(MATERIALIZATION_MAP_FILENAME, stored_json_bytes(map0)),
        ), key=lambda item: item["filename"]),
        "altered_materialization_map": sorted((
            common_d0,
            file_member(LAUNCH_RECEIPT_FILENAME, stored_json_bytes(receipt0)),
            file_member(MATERIALIZATION_MAP_FILENAME, stored_json_bytes(altered_map0)),
        ), key=lambda item: item["filename"]),
        "cross_row_r0_payload_r1_map_receipt": sorted((
            common_d0,
            file_member(LAUNCH_RECEIPT_FILENAME, stored_json_bytes(receipt1)),
            file_member(MATERIALIZATION_MAP_FILENAME, stored_json_bytes(map1)),
        ), key=lambda item: item["filename"]),
    }

    aggregate = _load("physical_negative_materialization_witness.json")
    aggregate_keys = {
        "cases", "compiled_adapter_refusal_process_count", "prelaunch_rejection_count",
        "successful_materialization_process_count", "witness_schema",
    }
    if (
        set(aggregate) != aggregate_keys
        or aggregate["witness_schema"] != "CanonicalTopologyPhysicalNegativeMaterializationWitness.v1"
        or aggregate["successful_materialization_process_count"] != 2
        or aggregate["compiled_adapter_refusal_process_count"] != 3
        or aggregate["prelaunch_rejection_count"] != 1
    ):
        raise ValueError("negative physical aggregate shape drift")
    cases = aggregate["cases"]
    if not isinstance(cases, list) or [case.get("case_id") for case in cases if isinstance(case, dict)] != list(NEGATIVE_PHYSICAL_CASES):
        raise ValueError("negative physical case order/membership drift")
    case_keys = {
        "canonical_resolution_invoked", "canonical_write_attempted", "case_id", "diagnostic_artifact",
        "expected_reason_code", "expected_stage", "input_inventory_artifact", "launch_audit_artifact",
        "frozen_failure_marker_count", "materialization_receipt_count", "materialization_started", "mode",
        "operational_failure_count", "prelaunch_rejection_audit_artifact", "private_cache_audit_passed",
        "process_audit_artifact", "process_group_alive_after_termination", "process_launched",
        "process_log_artifact",
    }
    observed_negative_process_ids: set[str] = set()
    negative_launch_audits: list[dict[str, Any]] = []
    expected_negative_process_ids = {
        "noncanonical_launch_receipt": "topology_negative_process_02",
        "altered_materialization_map": "topology_negative_process_03",
        "cross_row_r0_payload_r1_map_receipt": "topology_negative_process_04",
    }
    for case in cases:
        if set(case) != case_keys:
            raise ValueError("negative physical aggregate case shape drift")
        case_id = case["case_id"]
        stage, reason = NEGATIVE_PHYSICAL_CASES[case_id]
        prefix = f"physical_negative_{case_id}"
        diagnostic_name = f"{prefix}_diagnostic.json"
        inventory_name = f"{prefix}_input_inventory.json"
        if (
            case["diagnostic_artifact"] != diagnostic_name
            or case["input_inventory_artifact"] != inventory_name
            or case["expected_stage"] != stage
            or case["expected_reason_code"] != reason
            or case["materialization_receipt_count"] != 0
            or case["operational_failure_count"] != 0
            or case["canonical_resolution_invoked"] is not False
            or case["canonical_write_attempted"] is not False
            or case["materialization_started"] is not False
        ):
            raise ValueError(f"negative physical disposition drift: {case_id}")

        diagnostic = _load(diagnostic_name)
        expected_diagnostic = {
            "canonical_write_attempted": False,
            "diagnostic_schema": "CanonicalTopologyMaterializationFailure.v1",
            "materialization_started": False,
            "reason_code": reason,
            "stage": stage,
        }
        if diagnostic != expected_diagnostic:
            raise ValueError(f"negative physical diagnostic drift: {case_id}")

        inventory = _load(inventory_name)
        if set(inventory) != {"case_id", "input_role", "inventory_schema", "members"}:
            raise ValueError(f"negative physical input inventory shape drift: {case_id}")
        if (
            inventory["case_id"] != case_id
            or inventory["input_role"] != "negative_materialization"
            or inventory["inventory_schema"] != "CanonicalTopologyPhysicalNegativeInputInventory.v1"
            or not isinstance(inventory["members"], list)
        ):
            raise ValueError(f"negative physical input inventory identity drift: {case_id}")
        members = inventory["members"]
        names = [member.get("filename") for member in members if isinstance(member, dict)]
        if names != sorted(names) or len(names) != len(set(names)) or len(names) != len(members):
            raise ValueError(f"negative physical input inventory ordering drift: {case_id}")
        for member in members:
            if set(member) != {"filename", "member_type", "raw_sha256"} or member["member_type"] not in {"regular_file", "directory"}:
                raise ValueError(f"negative physical input member shape drift: {case_id}")
            digest = member["raw_sha256"]
            if member["member_type"] == "directory":
                if digest is not None:
                    raise ValueError(f"directory member has a raw digest: {case_id}")
            elif not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                raise ValueError(f"regular input member has an invalid digest: {case_id}")
        regular_names = {member["filename"] for member in members if member["member_type"] == "regular_file"}
        if regular_names != {CANONICAL_PAYLOAD_FILENAME, MATERIALIZATION_MAP_FILENAME, LAUNCH_RECEIPT_FILENAME}:
            raise ValueError(f"negative physical regular proof-input membership drift: {case_id}")
        if members != expected_inventory_members[case_id]:
            raise ValueError(f"negative physical proof-input bytes drift: {case_id}")

        if case_id == "additional_directory":
            prelaunch_name = f"{prefix}_prelaunch_rejection_audit.json"
            if (
                len(members) != 4
                or sum(member["member_type"] == "directory" for member in members) != 1
                or case["mode"] != "prelaunch_rejection"
                or case["process_launched"] is not False
                or case["frozen_failure_marker_count"] != 0
                or case["launch_audit_artifact"] is not None
                or case["process_log_artifact"] is not None
                or case["process_audit_artifact"] is not None
                or case["prelaunch_rejection_audit_artifact"] != prelaunch_name
                or case["private_cache_audit_passed"] is not None
                or case["process_group_alive_after_termination"] is not None
            ):
                raise ValueError("additional-directory prelaunch rejection boundary drift")
            prelaunch = _load(prelaunch_name)
            expected_prelaunch = {
                "audit_schema": "CanonicalTopologyPhysicalNegativePrelaunchRejectionAudit.v1",
                "canonical_resolution_invoked": False,
                "canonical_write_attempted": False,
                "case_id": case_id,
                "process_launched": False,
                "reason_code": reason,
                "rejection_stage": stage,
            }
            if prelaunch != expected_prelaunch:
                raise ValueError("additional-directory prelaunch audit drift")
            continue

        launch_name = f"{prefix}_launch_audit.json"
        log_name = f"{prefix}_process.log"
        process_audit_name = f"{prefix}_process_audit.json"
        if (
            len(members) != 3
            or any(member["member_type"] != "regular_file" for member in members)
            or case["mode"] != "compiled_adapter_refusal"
            or case["process_launched"] is not True
            or case["frozen_failure_marker_count"] != 1
            or case["launch_audit_artifact"] != launch_name
            or case["process_log_artifact"] != log_name
            or case["process_audit_artifact"] != process_audit_name
            or case["prelaunch_rejection_audit_artifact"] is not None
            or case["private_cache_audit_passed"] is not True
            or case["process_group_alive_after_termination"] is not False
        ):
            raise ValueError(f"compiled-adapter refusal boundary drift: {case_id}")
        log = (RECORDS / log_name).read_text(encoding="utf-8", errors="strict")
        failure_values = [line.partition(FAILURE_MARKER)[2] for line in log.splitlines() if FAILURE_MARKER in line]
        if len(failure_values) != 1 or strict_load_stored_json((failure_values[0] + "\n").encode("utf-8")) != diagnostic:
            raise ValueError(f"negative UE log does not bind exactly one frozen diagnostic: {case_id}")
        if RECEIPT_MARKER in log or OPERATIONAL_FAILURE_MARKER in log:
            raise ValueError(f"negative UE log acquired materialization/operational authority: {case_id}")
        launch_audit = _load(launch_name)
        _validate_launch_audit(
            launch_audit,
            process_id=expected_negative_process_ids[case_id],
            predecessor_required=False,
            expected_scope="negative_no_predecessor",
        )
        observed_negative_process_ids.add(launch_audit["process_instance_id"])
        negative_launch_audits.append(launch_audit)
        _assert_unreal_58_log(log_name)
        _assert_isolated_cache_log(log_name, launch_audit)
        process_audit = _load(process_audit_name)
        expected_process_audit = {
            "audit_schema": "CanonicalTopologyPhysicalNegativeProcessAudit.v1",
            "canonical_resolution_invoked": False,
            "canonical_write_attempted": False,
            "case_id": case_id,
            "diagnostic_observed_before_termination": True,
            "operational_process_instance_id": launch_audit["process_instance_id"],
            "process_group_alive_after_termination": False,
            "process_launched": True,
            "process_leader_terminated": True,
        }
        if process_audit != expected_process_audit:
            raise ValueError(f"negative physical process audit drift: {case_id}")
    if (
        observed_negative_process_ids != set(expected_negative_process_ids.values())
        or observed_negative_process_ids & {SOURCE_PROCESS_ID, RETURN_PROCESS_ID}
    ):
        raise ValueError("negative UE process identity set drift")
    return negative_launch_audits


def verify_canonical() -> None:
    expected_names = tuple(sorted(ARTIFACT_NAMES + PHYSICAL_ARTIFACTS))
    actual_names = tuple(sorted(path.name for path in RECORDS.iterdir() if path.is_file()))
    if actual_names != expected_names:
        raise ValueError("topology proof record membership drift")
    with tempfile.TemporaryDirectory() as temporary:
        regenerated = Path(temporary)
        write_artifacts(regenerated)
        for name in ARTIFACT_NAMES:
            if (RECORDS / name).read_bytes() != (regenerated / name).read_bytes():
                raise ValueError(f"canonical topology artifact cannot regenerate: {name}")
    run = proof_run()
    if _load("canonical_topology_R0.json") != run["R0"] or _load("canonical_topology_R1.json") != run["R1"]:
        raise ValueError("canonical checkpoint drift")
    failures = runtime_fail_closed_results()
    if _load("canonical_topology_runtime_fail_closed.json") != failures:
        raise ValueError("28-family rejection artifact drift")
    if len(failures) != 28:
        raise ValueError("frozen adversarial family count changed")
    observed_matrix = {
        family: (result["disposition"], tuple(result["variants"]))
        for family, result in failures.items()
    }
    if observed_matrix != FROZEN_ADVERSARIAL_MATRIX:
        raise ValueError("frozen adversarial family/variant/disposition matrix changed")
    if any(
        set(failures[family]) != {"disposition", "variant_count", "variants"}
        or failures[family]["variant_count"] != len(variants)
        or len(failures[family]["variants"]) != len(variants)
        for family, (_, variants) in FROZEN_ADVERSARIAL_MATRIX.items()
    ):
        raise ValueError("frozen adversarial variant-count contract changed")
    observed_diagnostics = {
        family: {
            variant: (result["detached_diagnostic"]["stage"], result["detached_diagnostic"]["reason_code"])
            for variant, result in failures[family]["variants"].items()
            if "detached_diagnostic" in result
        }
        for family in FROZEN_REPRESENTATION_DIAGNOSTICS
    }
    if observed_diagnostics != FROZEN_REPRESENTATION_DIAGNOSTICS:
        raise ValueError("frozen representation diagnostic precedence changed")
    if run["replay"]["result"] != "accepted" or not all(run["source_audit"].values()):
        raise ValueError("canonical replay/source audit failed")
    if _sha(ROOT / "THE_CITY_Conceptual_City_Topology_Developer_Framing_v0.3.0.md") != "1466cf486eb8be952b2927d83ad8f5bd3938a98fe48f163856d10b152159955d":
        raise ValueError("reviewed conceptual framing bytes drift")


def _expected_inventory(role: str, record: dict[str, Any]) -> dict[str, Any]:
    mapping = materialization_map(record)
    receipt = launch_receipt(record, mapping)
    return {
        "files": [
            {"filename": CANONICAL_PAYLOAD_FILENAME, "raw_sha256": raw_stored_sha256(record)},
            {"filename": LAUNCH_RECEIPT_FILENAME, "raw_sha256": raw_stored_sha256(receipt)},
            {"filename": MATERIALIZATION_MAP_FILENAME, "raw_sha256": raw_stored_sha256(mapping)},
        ],
        "input_role": role,
        "inventory_schema": "CanonicalTopologyProofInputInventory.v1",
        "unexpected_files": [],
    }


def verify_physical_witnesses() -> None:
    r0 = initial_canonical_envelope()
    boundary = next_consequential_boundary(r0)
    if boundary is None:
        raise ValueError("R0 boundary missing")
    r1 = resolve_next_due(r0, boundary)
    h0, h1 = canonical_hash(r0), canonical_hash(r1)
    source_receipt = _load("physical_R0_source_materialization_receipt.json")
    return_receipt = _load("physical_R1_return_materialization_receipt.json")
    if source_receipt != _receipt_from_log("physical_R0_source_process.log"):
        raise ValueError("source receipt/log mismatch")
    if return_receipt != _receipt_from_log("physical_R1_return_process.log"):
        raise ValueError("return receipt/log mismatch")
    validate_materialization_receipt(r0, materialization_map(r0), source_receipt)
    validate_materialization_receipt(r1, materialization_map(r1), return_receipt)
    if _load("physical_R0_source_input_inventory.json") != _expected_inventory("R0_source", r0):
        raise ValueError("source inventory drift")
    if _load("physical_R1_return_input_inventory.json") != _expected_inventory("R1_return", r1):
        raise ValueError("return inventory drift")
    termination = _load("physical_R0_source_termination_witness.json")
    validate_termination_witness(termination, SOURCE_PROCESS_ID, h0, h1)
    isolation = _load("physical_fresh_process_isolation_witness.json")
    validate_isolation_witness(isolation)
    if isolation["source_process_instance_id"] != SOURCE_PROCESS_ID or isolation["return_process_instance_id"] != RETURN_PROCESS_ID:
        raise ValueError("isolation process identity drift")
    source_launch = _load("physical_R0_source_launch_audit.json")
    return_launch = _load("physical_R1_return_launch_audit.json")
    _validate_launch_audit(
        source_launch,
        process_id=SOURCE_PROCESS_ID,
        predecessor_required=False,
        expected_scope="source_no_predecessor",
    )
    _validate_launch_audit(
        return_launch,
        process_id=RETURN_PROCESS_ID,
        predecessor_required=True,
        expected_scope="return_after_source_destruction",
    )
    if (
        source_receipt["operational_process_instance_id"] != source_launch["process_instance_id"]
        or return_receipt["operational_process_instance_id"] != return_launch["process_instance_id"]
    ):
        raise ValueError("materialization receipt/launch process identity mismatch")
    if (
        source_receipt["operational_process_instance_id"] != isolation["source_process_instance_id"]
        or return_receipt["operational_process_instance_id"] != isolation["return_process_instance_id"]
        or termination["operational_process_instance_id"] != source_receipt["operational_process_instance_id"]
    ):
        raise ValueError("receipt/termination/isolation lifecycle identity mismatch")
    _validate_launch_set_disjoint([source_launch, return_launch])
    _assert_unreal_58_log("physical_R0_source_process.log")
    _assert_unreal_58_log("physical_R1_return_process.log")
    _assert_isolated_cache_log("physical_R0_source_process.log", source_launch)
    _assert_isolated_cache_log("physical_R1_return_process.log", return_launch)
    source_actors = source_receipt["operational_actor_instance_ids"]
    return_actors = return_receipt["operational_actor_instance_ids"]
    if source_receipt["operational_process_instance_id"] == return_receipt["operational_process_instance_id"]:
        raise ValueError("P0/P1 are not distinct")
    if any(
        (source_receipt["operational_process_instance_id"], source_actors[role]) ==
        (return_receipt["operational_process_instance_id"], return_actors[role])
        for role in source_actors
    ):
        raise ValueError("representation identity survived process destruction")
    lifecycle = _load("physical_canonical_topology_lifecycle_witness.json")
    expected_lifecycle = {
        "canonical_hashes": {"R0": h0, "R1": h1},
        "canonical_resolution_after_source_destruction": True,
        "endpoint_relation_preserved": True,
        "fresh_process_actor_pairs_differ_by_role": True,
        "process_ids_distinct": True,
        "return_access_state": "blocked",
        "return_received_R1_only": True,
        "source_access_state": "available",
        "source_process_root_destroyed": True,
    }
    if lifecycle != expected_lifecycle:
        raise ValueError("physical lifecycle oracle drift")
    negative_launches = _validate_negative_materialization_witnesses()
    _validate_launch_set_disjoint([source_launch, return_launch, *negative_launches])


def unreal_source_audit() -> dict[str, bool]:
    adapter = (ROOT / "CityMaterializationProof/Source/CityMaterializationProof/CanonicalSpatialTopologyProofAdapter.cpp").read_text(encoding="utf-8")
    header = (ROOT / "CityMaterializationProof/Source/CityMaterializationProof/CanonicalSpatialTopologyProofAdapter.h").read_text(encoding="utf-8")
    representation = (ROOT / "CityMaterializationProof/Source/CityMaterializationProof/CanonicalTopologyRepresentationActor.cpp").read_text(encoding="utf-8")
    game_mode = (ROOT / "CityMaterializationProof/Source/CityMaterializationProof/CityProofGameMode.cpp").read_text(encoding="utf-8")
    harness = (ROOT / "proof_kernel/canonical_spatial_topology_identity_harness.py").read_text(encoding="utf-8")
    def ordered(text: str, *tokens: str) -> bool:
        positions = [text.find(token) for token in tokens]
        return all(position >= 0 for position in positions) and positions == sorted(positions)

    negative_start = harness.find("def _acquire_negative_witnesses(")
    negative_end = harness.find("def _acquire_staged(", negative_start)
    negative_harness = harness[negative_start:negative_end] if -1 < negative_start < negative_end else ""
    endpoint_extract = adapter.find("TryGetArrayField(TEXT(\"endpoint_site_ids\"), EndpointValues)")
    endpoint_record_write = adapter.find("OutRecord.EndpointSiteId0 = EndpointSiteId0")
    endpoint_map_read = adapter.find("ExactString(*MapSites, *EndpointSiteId0")
    endpoint_projection = adapter.find("AddLocalLabel(FVector(-320.0f, 180.0f, 260.0f), Record.EndpointSiteId0")
    endpoint_receipt = adapter.find("materialized_endpoint_site_ids")
    return {
        "adapter_routes_any_topology_selector_fail_closed": "CommandLine.Contains(TEXT(\"CanonicalTopologyProof\"))" in game_mode,
        "adapter_uses_spectator_before_initial_pawn_spawn": game_mode.find("DefaultPawnClass = CommandLine.Contains(TEXT(\"CanonicalTopologyProof\"))") < game_mode.find("void ACityProofGameMode::BeginPlay()") and "ASpectatorPawn::StaticClass()" in game_mode,
        "adapter_inventories_exact_three_inputs": all(name in adapter for name in (CANONICAL_PAYLOAD_FILENAME, MATERIALIZATION_MAP_FILENAME, LAUNCH_RECEIPT_FILENAME)),
        "adapter_inventory_rejects_added_directories": "FindFiles(Entries" in adapter and "true, true" in adapter,
        "adapter_scans_duplicate_members_before_object_construction": adapter.find("HasDuplicateObjectMember(Canonical)") < adapter.find("FJsonSerializer::Deserialize"),
        "adapter_hashes_payload_and_map_before_parsing": ordered(
            adapter,
            "const FString RawPayloadHash",
            "const FString RawMapHash",
            "ParseObjectAfterDuplicateScan(PayloadCanonical",
        ),
        "adapter_pins_exact_h_d_m_l_sealed_identities": _embedded_artifact_identities(adapter) == _expected_embedded_artifact_identities(),
        "adapter_uses_pinned_identities_in_one_branch_validation_path": all(token in adapter for token in (
            "RawReceiptHash == L0", "RawReceiptHash == L1",
            "bReceiptR0 ? D0 : D1", "bReceiptR0 ? M0 : M1",
            "bReceiptR0 && CanonicalHash == H0", "bReceiptR1 && CanonicalHash == H1",
        )),
        "adapter_validates_full_receipt_before_artifact_load": adapter.find("NonEmptyString(Receipt") < adapter.find("TArray<uint8> PayloadBytes"),
        "adapter_endpoints_dataflow_from_payload_to_map_projection_and_receipt": (
            all(token in header + adapter for token in (
                "CanonicalRouteId", "EndpointSiteId0", "EndpointSiteId1",
                "OutRecord.CanonicalRouteId = RouteId", "OutRecord.EndpointSiteId0 = EndpointSiteId0",
                "OutRecord.EndpointSiteId1 = EndpointSiteId1", "*Record.CanonicalRouteId",
                "*Record.EndpointSiteId0", "*Record.EndpointSiteId1",
            ))
            and -1 < endpoint_extract < endpoint_record_write
            and -1 < endpoint_map_read < endpoint_record_write
            and endpoint_record_write < endpoint_projection < endpoint_receipt
        ),
        "adapter_has_no_q_or_canonical_resolution_path": all(token not in adapter + header for token in ("ExternalEvidence", "ProposalCapability", "resolve_next_due", "next_consequential_boundary", "authoritative_causal_ledger", "canonical_ancestry")),
        "adapter_rejects_truth_bearing_branch_selectors": all(token in adapter for token in ("CanonicalTopologyProofBranch=", "CanonicalTopologyProofAccess=", "CanonicalTopologyProofEndpoint=", "CanonicalTopologyProofMappingId=", "CityProof=")),
        "representation_is_noncolliding_and_nonnavigating": "SetCollisionEnabled(ECollisionEnabled::NoCollision)" in representation and "SetCanEverAffectNavigation(false)" in representation,
        "exact_three_representation_actors_spawned": adapter.count("SpawnActor<ACanonicalTopologyRepresentationActor>") == 3,
        "representation_spawns_are_deferred_and_staged": adapter.count("bDeferConstruction = true") == 3 and adapter.count("FinishSpawning") == 3 and adapter.count("SetActorHiddenInGame(true)") == 3,
        "source_root_destroyed_before_boundary_discovery": ordered(
            harness, "shutil.rmtree(original_source_root)", "boundary = next_consequential_boundary(r0)",
        ),
        "return_root_created_only_after_r1": ordered(
            harness, "r1 = resolve_next_due", '_prepare_process_root(runtime_root, "return"',
        ),
        "termination_observation_opens_before_resolution": ordered(
            harness, "termination_observation = open_termination_observation", "boundary = next_consequential_boundary(r0)",
        ),
        "cache_isolation_is_observed_for_positive_processes": all(token in harness for token in (
            '_complete_cache_audit(source_configuration["audit"]',
            '_complete_cache_audit(return_configuration["audit"]',
        )) and ordered(harness, '_complete_cache_audit(return_configuration["audit"]', "isolated = isolation_witness("),
        "private_cache_clone_is_mechanically_contained": (
            "if member.is_symlink():" in harness
            and "private process tree member escapes its root" in harness
            and ordered(harness, 'subprocess.run(["/bin/cp", "-cR"', "_assert_no_symlink_escape(local_ddc)")
        ),
        "global_cache_seed_is_absent_from_process_launch_contract": all(token in harness for token in (
            "if any(seed_path in value for value in command)",
            "any(seed_path in value for value in environment.values())",
            '"cache_seed_source_root_referenced_by_launch": False',
        )),
        "positive_unreal_processes_have_finally_cleanup": all(token in harness for token in (
            "finally:\n        _terminate(source_process)", "finally:\n        _terminate(return_process)",
        )),
        "return_prelaunch_isolation_precedes_process_start": ordered(
            harness, "_validate_return_prelaunch(\n        return_configuration,", "return_process = _start_process(return_configuration)",
        ),
        "source_process_group_death_precedes_boundary_discovery": ordered(
            harness, "if _process_group_alive(source_process.pid)", "boundary = next_consequential_boundary(r0)",
        ),
        "evidence_publication_is_single_and_failure_atomic": (
            "if evidence_output.exists():" in harness
            and "observed_artifacts != EXPECTED_EVIDENCE_FILENAMES" in harness
            and "os.replace(staging, evidence_output)" in harness
            and "failed acquisition escaped a published evidence directory" in harness
        ),
        "harness_collects_real_negative_ue_witnesses": (
            all(case_id in harness for case_id in NEGATIVE_PHYSICAL_CASES)
            and "for index, (case_id, expected_stage, expected_reason) in enumerate(NEGATIVE_CASES" in negative_harness
            and FAILURE_MARKER in harness
            and 'if case_id == "additional_directory":' in negative_harness
            and '"process_launched": False' in negative_harness
            and "process = _start_process(configuration)" in negative_harness
            and all(token not in negative_harness for token in ("next_consequential_boundary", "resolve_next_due"))
        ),
        "harness_has_no_q_path": all(token not in harness for token in ("external_evidence_q", "admit_external_input", "proposal_capability")),
    }


def release_paths() -> tuple[str, ...]:
    own = MANIFEST.relative_to(ROOT).as_posix()
    sources = tuple(path for path in SOURCE_PATHS + UE_BUILD_PATHS if path != own)
    records = tuple(f"proof_kernel/CanonicalSpatialTopologyIdentityProofRecords/{name}" for name in ARTIFACT_NAMES + PHYSICAL_ARTIFACTS)
    return tuple(sorted(sources + records))


def write_release() -> int:
    write_artifacts(RECORDS)
    verify_canonical()
    verify_physical_witnesses()
    if not all(unreal_source_audit().values()):
        raise ValueError(f"UE authority source audit failed: {unreal_source_audit()}")
    own = MANIFEST.relative_to(ROOT).as_posix()
    if own in release_paths():
        raise AssertionError("manifest cannot contain itself")
    for path in release_paths():
        if not (ROOT / path).is_file():
            raise ValueError(f"release member is missing: {path}")
    MANIFEST.write_text("\n".join(f"{_sha(ROOT / path)}  {path}" for path in release_paths()) + "\n", encoding="utf-8")
    return len(release_paths())


def verify_release() -> int:
    own = MANIFEST.relative_to(ROOT).as_posix()
    members: list[tuple[str, str]] = []
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        digest, separator, path = line.partition("  ")
        if not separator or len(digest) != 64 or not path or path == own or Path(path).is_absolute() or ".." in Path(path).parts:
            raise ValueError(f"invalid manifest member: {line!r}")
        members.append((digest, path))
    if tuple(path for _, path in members) != release_paths():
        raise ValueError("manifest membership drift")
    for digest, path in members:
        if _sha(ROOT / path) != digest:
            raise ValueError(f"checksum mismatch: {path}")
    verify_canonical()
    verify_physical_witnesses()
    if not all(unreal_source_audit().values()):
        raise ValueError("UE source authority audit failed")
    return len(members)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("write-canonical", "canonical", "write-release", "verify"))
    args = parser.parse_args()
    if args.command == "write-canonical":
        write_artifacts(RECORDS)
        verify_canonical()
        print("verified canonical topology artifacts; physical UE evidence remains required")
        return 0
    if args.command == "canonical":
        verify_canonical()
        verify_physical_witnesses()
        if not all(unreal_source_audit().values()):
            raise SystemExit(f"UE source audit failed: {unreal_source_audit()}")
        print("verified canonical topology and imported physical UE artifacts; release remains unsealed")
        return 0
    if args.command == "write-release":
        if not EVIDENCE.is_file():
            raise SystemExit("release evidence document is required before writing manifest")
        count = write_release()
    else:
        if not EVIDENCE.is_file() or not MANIFEST.is_file():
            raise SystemExit("release verification unavailable: evidence is not sealed")
        count = verify_release()
    print(f"verified {count}/{count} release artifacts; manifest excludes itself")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
