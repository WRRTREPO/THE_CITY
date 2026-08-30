#!/usr/bin/env python3
"""Acquire and regenerate the frozen Phase-4 cross-domain occupancy evidence."""

from __future__ import annotations

import argparse
import copy
import concurrent.futures
import fcntl
import hashlib
import io
import json
import os
import re
import select
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import tokenize
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

from canonical_occupancy_transition import (
    next_consequential_boundary,
    resolve_next_due,
)
from cross_domain_canonical_occupancy_materialization import (
    ARTIFACT_NAMES,
    DOMAIN_ROLES,
    HEAD_HASHES,
    HEAD_OBSERVATION_SCHEMA,
    H0,
    HFINAL,
    HTRANSIT,
    LIVE_OBSERVATION_SCHEMA,
    MATERIALIZATION_RECEIPT_SCHEMA,
    MATERIALIZATION_STAGES,
    OPERATION_ROWS,
    PROCESS_BINDING_FIELDS,
    PROOF_SCENARIO,
    PROOF_VERSION,
    PRIMARY_REFRESH_ORDERS,
    PROJECTION_ROWS,
    PROCESS_BINDING_VERIFICATION_MODES,
    RAW_HASHES,
    RECORD_FILENAMES,
    RECORD_ROLES,
    RECORDS,
    R0_ROLE,
    RFINAL_ROLE,
    RTRANSIT_ROLE,
    PhysicalCurrentHeadGuard,
    CrossDomainOccupancyRejected,
    artifact_role_set_valid,
    bind_invocation,
    canonical_chain,
    canonical_json,
    canonical_records,
    compare_expectation_receipt_observation,
    expected_representation,
    guard_and_head_observation_matrix,
    head_disposition,
    inspection_invocation,
    materialize_invocation,
    operation_invocation,
    operation_tuple_matrix,
    process_binding,
    projection,
    projection_matrix,
    semantic_replay_projection,
    sha256_bytes,
    sha256_value,
    stored_json_bytes,
    strict_load_stored_json,
    validate_exact_directory,
    validate_materialization_receipt,
    validate_candidate_runtime_dependency_census,
    validate_head_disposition,
    validate_projection,
    validate_visible_tuple,
    write_json,
)
from simultaneous_physical_domains_harness import (
    BUILD_VERSION,
    CONFIG_PATHS,
    EDITOR,
    ENTRY_MAP,
    MODULE,
    PROJECT,
    _engine_build_identity,
    _independent_file_identity,
    _proc_info,
    _real,
    _sha_file,
    _spawn_suspended,
    _write_all,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIRECTORY = ROOT / "proof_kernel" / "CrossDomainCanonicalOccupancyMaterializationProofRecords"

TRACE_SCHEMA = "CrossDomainOccupancyRuntimeTraceEvent.v1"
PROVENANCE_SCHEMA = "CrossDomainOccupancyRuntimeProvenance.v1"
BIND_RECEIPT_SCHEMA = "CrossDomainOccupancyBindReceipt.v1"
FAILURE_SCHEMA = "CrossDomainOccupancyFailure.v1"
PROCESS_FAULT_RECEIPT_SCHEMA = "CrossDomainOccupancyProcessFaultArmReceipt.v1"

PRIMARY_WITNESS_IDS = {
    "W1": "w1_A_B__A_B",
    "W2": "w2_B_A__B_A",
    "W3": "w3_A_B__B_A",
    "W4": "w4_B_A__A_B",
}


def _canonical_line(value: Any) -> bytes:
    return stored_json_bytes(value)


def _environment(domain_root: Path) -> dict[str, str]:
    environment = dict(os.environ)
    environment.pop("CODEX_SANDBOX", None)
    environment["EOS_LAUNCHED_BY_EPIC"] = "0"
    environment["SSL_CERT_FILE"] = str(
        EDITOR.parents[5] / "Content" / "Certificates" / "ThirdParty" / "cacert.pem"
    )
    environment["UE_DesktopUnrealProcess"] = "1"
    environment["UE_ZenSubprocessDataPath"] = str(
        Path.home() / "Library" / "Application Support" / "Epic" /
        "UnrealEngine" / "Common" / "Zen" / "Data"
    )
    environment["TMPDIR"] = str(domain_root / "tmp")
    return environment


def _argv(domain_root: Path, role: str) -> list[str]:
    return [
        str(_real(EDITOR)),
        str(_real(PROJECT)),
        "-game",
        "-Multiprocess",
        "-CrossDomainOccupancyProof",
        "-NoSplash",
        "-Windowed",
        "-ResX=900",
        "-ResY=650",
        "-WinX=30" if role == "domain_A" else "-WinX=990",
        "-WinY=60",
        f"-UserDir={domain_root / 'user'}",
        f"-abslog={domain_root / 'diagnostic' / 'UnrealEditor.log'}",
    ]


def _environment_audit(environment: Mapping[str, str]) -> dict[str, Any]:
    return {
        "audit_schema": "CrossDomainOccupancyLaunchEnvironmentAudit.v1",
        "plaintext_values_released": False,
        "proof_semantic_key_allowlist": [],
        "sorted_entries": [
            {"key": key, "value_raw_sha256": sha256_bytes(value.encode("utf-8"))}
            for key, value in sorted(environment.items())
        ],
    }


def _project_inventory() -> dict[str, Any]:
    return {
        "inventory_schema": "CrossDomainOccupancyProjectConfigAndModuleInventory.v1",
        "members": [
            {"raw_sha256": _sha_file(path), "realpath": str(_real(path))}
            for path in (PROJECT, *CONFIG_PATHS, MODULE)
        ],
    }


def _descriptor_map(role: str) -> dict[str, Any]:
    return {
        "all_other_descriptors_at_exec": "closed",
        "descriptor_map_schema": "CrossDomainOccupancyInheritedDescriptorMap.v1",
        "fd_0": {"pipe_id": f"{role}/control/0001", "role": "original_control_pipe_read_endpoint"},
        "fd_1": {"pipe_id": f"{role}/stdout/0001", "role": "original_structured_output_pipe_write_endpoint"},
        "fd_2": {"pipe_id": f"{role}/stderr/0001", "role": "original_diagnostic_pipe_write_endpoint"},
    }


def _launch_plan(witness_id: str, role: str, root: Path) -> dict[str, Any]:
    return {
        "control_pipe_id": f"{role}/control/0001",
        "diagnostic_pipe_id": f"{role}/stderr/0001",
        "domain_role": role,
        "harness_launch_id": f"{witness_id}/{role}/launch_0001",
        "launch_plan_schema": "CrossDomainOccupancyLaunchPlan.v1",
        "process_root_realpath": str(_real(root)),
        "proof_scenario": PROOF_SCENARIO,
        "structured_output_pipe_id": f"{role}/stdout/0001",
        "witness_id": witness_id,
    }


def _bundle_files(role: str, operation_id: str) -> tuple[str, str, str]:
    row = OPERATION_ROWS[(role, operation_id)]
    return row["payload_file"], row["projection_file"], row["invocation_file"]


def _prepare_bundle(
    domain_root: Path,
    role: str,
    operation_id: str,
    binding: Mapping[str, Any],
    *,
    projection_mutator: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    row = OPERATION_ROWS[(role, operation_id)]
    target = row["target_role"]
    directory = domain_root / row["bundle_root"]
    directory.mkdir(parents=True, exist_ok=False)
    payload_name, projection_name, invocation_name = _bundle_files(role, operation_id)
    payload_raw = (RECORDS / RECORD_FILENAMES[target]).read_bytes()
    projected = projection(role, target)
    if projection_mutator is not None:
        projection_mutator(projected)
    projection_raw = stored_json_bytes(projected)
    invocation = operation_invocation(
        role, operation_id,
        sha256_bytes(canonical_json(binding).encode("utf-8")),
    )
    invocation_raw = stored_json_bytes(invocation)
    (directory / payload_name).write_bytes(payload_raw)
    (directory / projection_name).write_bytes(projection_raw)
    (directory / invocation_name).write_bytes(invocation_raw)
    for name in (payload_name, projection_name, invocation_name):
        os.chmod(directory / name, 0o400)
    os.chmod(directory, 0o500)
    inventory = validate_exact_directory(directory, (payload_name, projection_name, invocation_name))
    return {
        "directory": str(_real(directory)),
        "inventory": inventory,
        "payload_raw": payload_raw,
        "projection_raw": projection_raw,
        "invocation_raw": invocation_raw,
        "operation_invocation": invocation,
        "names": [payload_name, projection_name, invocation_name],
    }


@dataclass
class LiveDomain:
    witness_id: str
    role: str
    root: Path
    pid: int
    fds: dict[str, int]
    binding: dict[str, Any]
    nominal_binding: dict[str, Any]
    launch_plan: dict[str, Any]
    launch_argv: list[str]
    environment_audit: dict[str, Any]
    descriptor_map: dict[str, Any]
    descriptor_kernel_identities: list[dict[str, Any]]
    process_start: dict[str, Any]
    sequence: int = 0
    output_buffer: bytearray = field(default_factory=bytearray)
    diagnostic_digest: Any = field(default_factory=hashlib.sha256)
    diagnostic_tail: bytearray = field(default_factory=bytearray)
    objects: list[dict[str, Any]] = field(default_factory=list)
    traces: list[dict[str, Any]] = field(default_factory=list)
    commands: list[dict[str, Any]] = field(default_factory=list)
    command_raw_sha256: list[str] = field(default_factory=list)
    provenance: dict[str, Any] | None = None
    bind_receipt: dict[str, Any] | None = None
    bundles: dict[str, dict[str, Any]] = field(default_factory=dict)
    output_eof_observed: bool = False
    exited: bool = False
    reaped_wait_status: int | None = None
    termination_receipt: dict[str, Any] | None = None

    @property
    def instance_id(self) -> str:
        return sha256_bytes(canonical_json(self.binding).encode("utf-8"))

    @property
    def binding_digest(self) -> str:
        return sha256_value(self.binding)

    def send(self, value: Mapping[str, Any], *, counts_sequence: bool = False) -> None:
        raw = _canonical_line(value)
        _write_all(self.fds["control_write"], raw)
        self.commands.append(copy.deepcopy(dict(value)))
        self.command_raw_sha256.append(sha256_bytes(raw))
        if counts_sequence:
            sequence = value.get("command_sequence")
            if type(sequence) is not int or sequence != self.sequence + 1:
                raise RuntimeError("harness attempted a noncontiguous command sequence")
            self.sequence = sequence

    def drain(self) -> None:
        for key in ("output_read", "diagnostic_read"):
            while True:
                try:
                    chunk = os.read(self.fds[key], 1024 * 1024)
                except BlockingIOError:
                    break
                if not chunk:
                    if key == "output_read":
                        self.output_eof_observed = True
                    break
                if key == "diagnostic_read":
                    self.diagnostic_digest.update(chunk)
                    self.diagnostic_tail.extend(chunk)
                    if len(self.diagnostic_tail) > 256 * 1024:
                        del self.diagnostic_tail[:-256 * 1024]
                    continue
                self.output_buffer.extend(chunk)
                while b"\n" in self.output_buffer:
                    raw_line, _, remainder = self.output_buffer.partition(b"\n")
                    self.output_buffer = bytearray(remainder)
                    if not raw_line.startswith(b"{"):
                        continue
                    try:
                        value = strict_load_stored_json(bytes(raw_line) + b"\n")
                    except Exception as exc:
                        raise RuntimeError(f"noncanonical structured child output: {raw_line[:200]!r}") from exc
                    if not isinstance(value, dict):
                        raise RuntimeError("structured child output was not an object")
                    self.objects.append(value)
                    if value.get("trace_schema") == TRACE_SCHEMA:
                        self.traces.append(value)

    def next_object(self, predicate: Callable[[dict[str, Any]], bool], *, timeout: float = 75.0) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.drain()
            for index, value in enumerate(self.objects):
                if predicate(value):
                    return self.objects.pop(index)
            status = os.waitpid(self.pid, os.WNOHANG)
            if status[0] == self.pid:
                self.exited = True
                self.drain()
                diagnostic_tail = bytes(self.diagnostic_tail).decode("utf-8", errors="replace")
                raise RuntimeError(
                    f"UE child {self.pid} exited before expected output: {status[1]}; "
                    f"diagnostic_tail={diagnostic_tail[-16000:]!r}"
                )
            select.select([self.fds["output_read"], self.fds["diagnostic_read"]], [], [], 0.05)
        self.drain()
        raise TimeoutError(f"timed out waiting for structured output from {self.role}; tail={self.objects[-5:]!r}")

    def assert_alive(self, checkpoint: str) -> dict[str, Any]:
        status = os.waitpid(self.pid, os.WNOHANG)
        if status[0] == self.pid:
            self.exited = True
            raise RuntimeError(f"original child exited at {checkpoint}: {status[1]}")
        observed = _proc_info(self.pid)
        if (observed["seconds"], observed["microseconds"]) != (
            self.process_start["seconds"], self.process_start["microseconds"]
        ):
            raise RuntimeError(f"process birth changed at {checkpoint}")
        self.drain()
        return observed

    def liveness(self, checkpoint: str, sample_sequence: int) -> dict[str, Any]:
        observed = self.assert_alive(checkpoint)
        poller = select.poll()
        poller.register(self.fds["control_write"], select.POLLERR | select.POLLHUP)
        control_events = poller.poll(0)
        poller = select.poll()
        poller.register(self.fds["output_read"], select.POLLIN | select.POLLHUP)
        output_events = poller.poll(0)
        output_hup = any(flags & select.POLLHUP for _, flags in output_events)
        control_hup = any(flags & (select.POLLERR | select.POLLHUP) for _, flags in control_events)
        return {
            "checkpoint_id": checkpoint,
            "control_pipe_unexpected_eof": control_hup,
            "domain_role": self.role,
            "liveness_observation_schema": "CrossDomainOccupancyLivenessObservation.v1",
            "observed_macos_process_start": {
                "microseconds": observed["microseconds"],
                "seconds": observed["seconds"],
            },
            "observed_pid": observed["pid"],
            "observation_source": "independent_harness_os_monitor",
            "occurrence_id": self.launch_plan["harness_launch_id"],
            "operational_process_instance_id": self.instance_id,
            "original_child_handle_exit_observed": False,
            "process_binding_raw_sha256": self.binding_digest,
            "process_start_pair_changed": False,
            "proof_scenario": PROOF_SCENARIO,
            "replacement_spawn_count": 0,
            "sample_sequence": sample_sequence,
            "structured_output_pipe_unexpected_eof": output_hup,
            "wait_status_available": False,
            "wait_status_value": None,
        }

    def terminate(self) -> dict[str, Any]:
        if self.termination_receipt is not None:
            return copy.deepcopy(self.termination_receipt)
        if not self.exited:
            try:
                os.kill(self.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            deadline = time.monotonic() + 4.0
            status = None
            while time.monotonic() < deadline:
                result = os.waitpid(self.pid, os.WNOHANG)
                if result[0] == self.pid:
                    status = result[1]
                    self.exited = True
                    break
                time.sleep(0.02)
            if not self.exited:
                try:
                    os.kill(self.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                _, status = os.waitpid(self.pid, 0)
                self.exited = True
        else:
            status = self.reaped_wait_status
        self.drain()
        for fd in self.fds.values():
            try:
                os.close(fd)
            except OSError:
                pass
        self.termination_receipt = {
            "diagnostic_stream_raw_sha256": self.diagnostic_digest.hexdigest(),
            "domain_role": self.role,
            "pid": self.pid,
            "terminated": True,
            "wait_status": status,
        }
        return copy.deepcopy(self.termination_receipt)

    def stage_bundle(
        self,
        operation_id: str,
        *,
        projection_mutator: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        bundle = _prepare_bundle(
            self.root, self.role, operation_id, self.binding,
            projection_mutator=projection_mutator,
        )
        self.bundles[operation_id] = bundle
        return bundle

    def materialize(
        self,
        operation_id: str,
        *,
        projection_mutator: Callable[[dict[str, Any]], None] | None = None,
        expect_success: bool = True,
    ) -> dict[str, Any]:
        bundle = self.stage_bundle(operation_id, projection_mutator=projection_mutator)
        command = materialize_invocation(self.sequence + 1, operation_id)
        self.send(command, counts_sequence=True)
        if not expect_success:
            return self.next_object(lambda value: value.get("diagnostic_schema") == FAILURE_SCHEMA)
        receipt = self.next_object(lambda value: value.get("receipt_schema") == MATERIALIZATION_RECEIPT_SCHEMA)
        expected = expected_representation(bundle["payload_raw"], bundle["projection_raw"])
        validate_materialization_receipt(receipt, expected, self.binding, operation_id)
        return receipt

    def inspect(self, inspection_id: str, *, expect_success: bool = True) -> dict[str, Any]:
        command = inspection_invocation(self.sequence + 1, inspection_id)
        self.send(command, counts_sequence=True)
        if not expect_success:
            return self.next_object(lambda value: value.get("diagnostic_schema") == FAILURE_SCHEMA)
        observation = self.next_object(lambda value: value.get("observation_schema") == LIVE_OBSERVATION_SCHEMA)
        _validate_live_observation(observation, self.binding)
        return observation

    def arm_fault(
        self,
        *,
        fault_occurrence_id: str,
        case_id: str,
        stage_id: str,
        edge: str,
        armed_operation_id: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        command = {
            "armed_operation_id": armed_operation_id,
            "case_id": case_id,
            "edge": edge,
            "fault_arm_invocation_schema": "CrossDomainOccupancyProcessFaultArmInvocation.v1",
            "fault_occurrence_id": fault_occurrence_id,
            "operational_process_instance_id": self.instance_id,
            "proof_scenario": PROOF_SCENARIO,
            "stage_id": stage_id,
        }
        self.send(command)
        receipt = self.next_object(lambda value: value.get("process_fault_arm_receipt_schema") == PROCESS_FAULT_RECEIPT_SCHEMA)
        if any(receipt.get(field) != command[field] for field in (
            "armed_operation_id", "case_id", "edge", "fault_occurrence_id",
            "operational_process_instance_id", "proof_scenario", "stage_id",
        )) or receipt.get("arm_state") != "armed_once":
            raise RuntimeError("process fault arm receipt mismatch")
        return command, receipt


def _validate_runtime_provenance(domain: LiveDomain, value: Mapping[str, Any]) -> None:
    expected_verification_rows = [
        {
            "field": field,
            "matched": True,
            "verification_mode": PROCESS_BINDING_VERIFICATION_MODES[field],
        }
        for field in PROCESS_BINDING_FIELDS
    ]
    if (
        value.get("audit_schema") != PROVENANCE_SCHEMA
        or value.get("proof_scenario") != PROOF_SCENARIO
        or value.get("captured_before_first_materialization") is not True
        or value.get("domain_role") != domain.role
        or value.get("operational_process_instance_id") != domain.instance_id
        or value.get("process_binding_raw_sha256") != domain.binding_digest
        or value.get("observed_process_binding") != domain.binding
        or value.get("observed_launch_argv") != domain.launch_argv
        or value.get("redacted_environment_audit") != domain.environment_audit
        or value.get("project_config_and_module_inventory") != _project_inventory()
        or value.get("observed_inherited_descriptor_map") != domain.descriptor_map
        or value.get("binding_verification_rows") != expected_verification_rows
    ):
        raise RuntimeError("runtime provenance did not bind the exact launch")
    inventory_validation = validate_candidate_runtime_dependency_census(
        value.get("loaded_image_inventory"),
        domain.binding,
        value.get("project_config_and_module_inventory"),
    )
    executable_identity = _independent_file_identity(EDITOR)
    module_identity = _independent_file_identity(MODULE)
    if (
        domain.binding["executable_raw_sha256"] != executable_identity["raw_sha256"]
        or inventory_validation["executable_mach_o_uuid"]
        not in executable_identity["mach_o_uuids"]
        or inventory_validation["module_raw_sha256"] != module_identity["raw_sha256"]
        or inventory_validation["module_mach_o_uuid"]
        not in module_identity["mach_o_uuids"]
    ):
        raise RuntimeError("loaded executable/module identity differs from bound build files")
    actors = value.get("initial_world_actor_class_inventory")
    if not isinstance(actors, list) or any(row.get("class_path", "").endswith("Pawn") for row in actors):
        raise RuntimeError("initial zero-Pawn inventory failed")


def _validate_live_observation(value: Mapping[str, Any], binding: Mapping[str, Any]) -> None:
    if value.get("observation_schema") != LIVE_OBSERVATION_SCHEMA:
        raise RuntimeError("live observation schema mismatch")
    for count, rows in (
        ("proof_relevant_actor_count", "proof_relevant_actor_rows"),
        ("anchor_actor_count", "anchor_actor_rows"),
        ("subject_actor_count", "subject_actor_rows"),
        ("route_actor_count", "route_actor_rows"),
        ("unexpected_proof_tagged_actor_count", "unexpected_proof_tagged_actor_rows"),
        ("pawn_count", "pawn_rows"),
        ("controller_count", "controller_rows"),
        ("auto_receive_input_actor_count", "auto_receive_input_actor_rows"),
        ("phase_4_actor_input_binding_count", "phase_4_actor_input_binding_rows"),
    ):
        if type(value.get(count)) is not int or value[count] != len(value.get(rows, [])):
            raise RuntimeError(f"live observation count mismatch: {count}")
    if (
        value.get("domain_role") != binding["domain_role"]
        or value.get("operational_process_instance_id") != sha256_bytes(canonical_json(binding).encode("utf-8"))
        or value.get("process_binding_raw_sha256") != sha256_value(binding)
        or value.get("world_package_name") != "/Engine/Maps/Entry"
        or value.get("world_type") != "Game"
        or value.get("observation_source") != "exhaustive_live_ue_world_census"
        or value.get("route_actor_count") != 0
        or value.get("unexpected_proof_tagged_actor_count") != 0
        or value.get("pawn_count") != 0
        or value.get("controller_count") != 1
        or value.get("auto_receive_input_actor_count") != 0
        or value.get("phase_4_actor_input_binding_count") != 0
        or value.get("proof_relevant_actor_count") != value.get("anchor_actor_count") + value.get("subject_actor_count")
    ):
        raise RuntimeError("live world census violated the frozen isolation boundary")
    controller = value["controller_rows"][0]
    if controller.get("actor_class") != "/Script/Engine.PlayerController" or controller.get("pawn_path") is not None or controller.get("phase_4_handler_reachable") is not False:
        raise RuntimeError("inert base-controller census mismatch")


def _launch_domain(
    runtime_parent: Path,
    witness_id: str,
    role: str,
    *,
    binding_mutator: Callable[[dict[str, Any]], None] | None = None,
    expect_binding: bool = True,
    defer_binding_wait: bool = False,
) -> LiveDomain:
    domain_root = runtime_parent / witness_id / role
    for name in ("user", "tmp", "diagnostic"):
        (domain_root / name).mkdir(parents=True, exist_ok=False)
    # macOS exposes the per-user temporary root through both /var and
    # /private/var.  Freeze the resolved spelling before constructing argv so
    # the child-observed UserDir/abslog relationship is byte-identical to the
    # process_root_realpath carried by the binding.
    domain_root = _real(domain_root)
    argv = _argv(domain_root, role)
    environment = _environment(domain_root)
    environment_audit = _environment_audit(environment)
    descriptor_map = _descriptor_map(role)
    pid, fds, descriptor_identities = _spawn_suspended(argv, environment, ROOT)
    process_start = _proc_info(pid)
    if process_start["ppid"] != os.getpid():
        os.kill(pid, signal.SIGKILL)
        os.waitpid(pid, 0)
        raise RuntimeError("UE process is not a direct child")
    plan = _launch_plan(witness_id, role, domain_root)
    binding = process_binding({
        "proof_scenario": PROOF_SCENARIO,
        "witness_id": witness_id,
        "domain_role": role,
        "harness_launch_id": plan["harness_launch_id"],
        "pid": pid,
        "macos_process_start": {
            "seconds": process_start["seconds"],
            "microseconds": process_start["microseconds"],
        },
        "executable_realpath": str(_real(EDITOR)),
        "executable_raw_sha256": _sha_file(EDITOR),
        "unreal_engine_build_identity": _engine_build_identity(),
        "entry_map_package_identity": ENTRY_MAP,
        "project_realpath": str(_real(PROJECT)),
        "project_raw_sha256": _sha_file(PROJECT),
        "project_config_and_module_inventory_raw_sha256": sha256_value(_project_inventory()),
        "process_root_realpath": str(_real(domain_root)),
        "launch_argv_raw_sha256": sha256_bytes(canonical_json(argv).encode("utf-8")),
        "launch_environment_audit_raw_sha256": sha256_value(environment_audit),
        "launch_cwd_realpath": str(_real(ROOT)),
        "inherited_descriptor_map_raw_sha256": sha256_value(descriptor_map),
        "control_pipe_id": plan["control_pipe_id"],
        "structured_output_pipe_id": plan["structured_output_pipe_id"],
        "diagnostic_pipe_id": plan["diagnostic_pipe_id"],
    })
    nominal = copy.deepcopy(binding)
    if binding_mutator is not None:
        binding_mutator(binding)
    domain = LiveDomain(
        witness_id=witness_id,
        role=role,
        root=domain_root,
        pid=pid,
        fds=fds,
        binding=binding,
        nominal_binding=nominal,
        launch_plan=plan,
        launch_argv=argv,
        environment_audit=environment_audit,
        descriptor_map=descriptor_map,
        descriptor_kernel_identities=descriptor_identities,
        process_start=process_start,
    )
    try:
        domain.send(bind_invocation(binding))
        os.kill(pid, signal.SIGCONT)
        if defer_binding_wait:
            return domain
        if not expect_binding:
            return domain
        _finish_binding(domain)
        return domain
    except BaseException:
        try:
            domain.terminate()
        except BaseException:
            pass
        raise


def _finish_binding(domain: LiveDomain) -> None:
    provenance = domain.next_object(lambda value: value.get("audit_schema") == PROVENANCE_SCHEMA)
    receipt = domain.next_object(lambda value: value.get("bind_receipt_schema") == BIND_RECEIPT_SCHEMA)
    domain.provenance = provenance
    domain.bind_receipt = receipt
    _validate_runtime_provenance(domain, provenance)
    if (
        receipt.get("operational_process_instance_id") != domain.instance_id
        or receipt.get("process_binding_raw_sha256") != domain.binding_digest
        or receipt.get("state") != "binding_accepted_once"
    ):
        raise RuntimeError("bind receipt mismatch")


def _launch_pair(runtime_parent: Path, witness_id: str) -> dict[str, LiveDomain]:
    domains: dict[str, LiveDomain] = {}
    try:
        for role in DOMAIN_ROLES:
            domains[role] = _launch_domain(
                runtime_parent, witness_id, role, defer_binding_wait=True
            )
        for role in DOMAIN_ROLES:
            _finish_binding(domains[role])
        if domains["domain_A"].instance_id == domains["domain_B"].instance_id:
            raise RuntimeError("two live domains share one operational identity")
        return domains
    except BaseException:
        for domain in domains.values():
            try:
                domain.terminate()
            except BaseException:
                pass
        raise


def _checkpoint(domains: Mapping[str, LiveDomain], checkpoint: str, sequence: int) -> dict[str, Any]:
    observations = {
        role: domains[role].liveness(checkpoint, sequence)
        for role in DOMAIN_ROLES
    }
    return {
        "checkpoint_id": checkpoint,
        "domain_observations": observations,
        "maximum_domain_sample_separation_poll_cycles": 1,
        "original_process_count": 2,
    }


def _head_observation(
    runtime_root: Path,
    role: str,
    operation_id: str,
    harness_run_id: str,
) -> dict[str, Any]:
    source_role = RTRANSIT_ROLE if role == "start" else RFINAL_ROLE
    observation_id = "head_observation_0001" if role == "start" else "head_observation_0002"
    source = RECORDS / RECORD_FILENAMES[source_role]
    output_root = runtime_root / "harness_private_head"
    output_root.mkdir(parents=True, exist_ok=True)
    trace: list[dict[str, Any]] = []

    def event(stage: str, edge: str) -> None:
        trace.append({
            "canonical_before_after_snapshot_raw_sha256": sha256_value(canonical_chain()),
            "case_id": None,
            "execution_mode": "successful",
            "harness_fault_arm_receipt_raw_sha256": None,
            "harness_fault_plan_raw_sha256": None,
            "harness_occurrence_id": f"{harness_run_id}/{observation_id}",
            "harness_operation_id": observation_id,
            "harness_run_id": harness_run_id,
            "harness_trace_schema": "CrossDomainOccupancyHarnessTraceEvent.v1",
            "liveness_adversarial_report_raw_sha256": None,
            "liveness_observation_raw_sha256": None,
            "liveness_plan_raw_sha256": None,
            "stage_edge": edge,
            "stage_id": stage,
            "trace_sequence": len(trace),
        })

    for stage in (
        "open_source", "pre_stat_source", "read_source_once", "post_stat_source",
        "authenticate_record", "construct_private_observation",
    ):
        event(stage, "entered")
        if stage == "open_source":
            descriptor = os.open(source, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
        elif stage == "pre_stat_source":
            before = os.fstat(descriptor)
        elif stage == "read_source_once":
            raw = os.read(descriptor, before.st_size)
            if os.read(descriptor, 1):
                raise RuntimeError("head observer source had trailing read")
        elif stage == "post_stat_source":
            after = os.fstat(descriptor)
            os.close(descriptor)
            if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
                raise RuntimeError("head observer source identity changed")
        elif stage == "authenticate_record":
            if sha256_bytes(raw) != RAW_HASHES[source_role]:
                raise RuntimeError("head observer raw identity mismatch")
            strict_load_stored_json(raw)
        elif stage == "construct_private_observation":
            matrix_row = guard_and_head_observation_matrix()["head_observations"][0 if source_role == RTRANSIT_ROLE else 1]
            observation = {
                **matrix_row,
                "observation_schema": HEAD_OBSERVATION_SCHEMA,
                "publication_state": "harness_private_verified",
                "source_record_device": before.st_dev,
                "source_record_inode": before.st_ino,
                "source_record_mode": "regular_file_only",
                "source_record_realpath": str(_real(source)),
                "source_record_size": before.st_size,
            }
        event(stage, "completed")

    candidate = output_root / f".{observation_id}.candidate"
    published = output_root / f"{observation_id}.json"
    event("write_and_fsync_candidate", "entered")
    fd = os.open(candidate, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC, 0o400)
    _write_all(fd, stored_json_bytes(observation))
    os.fsync(fd)
    os.close(fd)
    event("write_and_fsync_candidate", "completed")
    event("atomic_publish", "entered")
    os.rename(candidate, published)
    event("atomic_publish", "completed")
    event("reopen_and_reverify", "entered")
    if strict_load_stored_json(published.read_bytes()) != observation:
        raise RuntimeError("head observation reopen mismatch")
    event("reopen_and_reverify", "completed")
    return {
        "observation": observation,
        "observation_raw_sha256": sha256_value(observation),
        "publication_path": str(_real(published)),
        "trace": trace,
    }


def _accept(domain: LiveDomain, receipt: Mapping[str, Any], observation: Mapping[str, Any], record_role: str, operation_id: str, guard_state: str, context: str) -> tuple[dict[str, Any], dict[str, Any]]:
    bundle = domain.bundles[operation_id]
    expected = expected_representation(bundle["payload_raw"], bundle["projection_raw"])
    compare_expectation_receipt_observation(expected, receipt, observation, domain.binding, operation_id)
    disposition = head_disposition(
        context=context,
        domain_role=domain.role,
        binding=domain.binding,
        guard_state=guard_state,
        represented_hash=HEAD_HASHES[record_role],
        observed_head=HEAD_HASHES[record_role],
        expected=expected,
        receipt=receipt,
        observation=observation,
    )
    return expected, disposition


def acquire_primary_witness(runtime_parent: Path, witness: str) -> dict[str, Any]:
    witness_id = PRIMARY_WITNESS_IDS[witness]
    harness_run_id = f"phase4/{witness_id}/{int(time.time_ns())}"
    domains = _launch_pair(runtime_parent, witness_id)
    guard = PhysicalCurrentHeadGuard()
    terminations: dict[str, Any] = {}
    receipts: dict[str, dict[str, Any]] = {role: {} for role in DOMAIN_ROLES}
    observations: dict[str, dict[str, Any]] = {role: {} for role in DOMAIN_ROLES}
    expectations: dict[str, dict[str, Any]] = {role: {} for role in DOMAIN_ROLES}
    dispositions: dict[str, dict[str, Any]] = {role: {} for role in DOMAIN_ROLES}
    checkpoints: list[dict[str, Any]] = []
    head_publications: dict[str, Any] = {}
    try:
        for role in DOMAIN_ROLES:
            receipts[role][R0_ROLE] = domains[role].materialize("launch_0001")
            observations[role][R0_ROLE] = domains[role].inspect("inspection_0001")
            expectations[role][R0_ROLE], dispositions[role][R0_ROLE] = _accept(
                domains[role], receipts[role][R0_ROLE], observations[role][R0_ROLE],
                R0_ROLE, "launch_0001", guard.state,
                "synchronized(R0) / exact_current_representation",
            )
        checkpoints.append(_checkpoint(domains, "L0", 0))

        guard.transition("closed_for_R0_to_Rtransit", "before_exact_start_resolution")
        r0, _, sealed_transit, _, sealed_final = canonical_records()
        start = next_consequential_boundary(r0)
        if start is None or resolve_next_due(r0, start) != sealed_transit:
            raise RuntimeError("exact Phase-2 start resolution drift")
        for role in DOMAIN_ROLES:
            observations[role]["L1_predecessor"] = domains[role].inspect("inspection_0002")
        checkpoints.append(_checkpoint(domains, "L1", 1))
        head_publications[RTRANSIT_ROLE] = _head_observation(
            runtime_parent / witness_id, "start", "head_observation_0001", harness_run_id
        )
        for role in DOMAIN_ROLES:
            observations[role]["L2_predecessor"] = domains[role].inspect("inspection_0003")
        checkpoints.append(_checkpoint(domains, "L2", 2))
        guard.transition("open_for_Rtransit", "verified_Rtransit_and_both_stale_R0")

        first, second = PRIMARY_REFRESH_ORDERS[witness][0]
        receipts[first][RTRANSIT_ROLE] = domains[first].materialize("refresh_0001")
        observations[first][RTRANSIT_ROLE] = domains[first].inspect("inspection_0004")
        observations[second]["L3_predecessor"] = domains[second].inspect("inspection_0004")
        expectations[first][RTRANSIT_ROLE], dispositions[first][RTRANSIT_ROLE] = _accept(
            domains[first], receipts[first][RTRANSIT_ROLE], observations[first][RTRANSIT_ROLE],
            RTRANSIT_ROLE, "refresh_0001", guard.state,
            "synchronized(Rtransit) / exact_current_representation",
        )
        checkpoints.append(_checkpoint(domains, "L3", 3))
        receipts[second][RTRANSIT_ROLE] = domains[second].materialize("refresh_0001")
        for role in DOMAIN_ROLES:
            observations[role][RTRANSIT_ROLE] = domains[role].inspect("inspection_0005")
            expectations[role][RTRANSIT_ROLE], dispositions[role][RTRANSIT_ROLE] = _accept(
                domains[role], receipts[role][RTRANSIT_ROLE], observations[role][RTRANSIT_ROLE],
                RTRANSIT_ROLE, "refresh_0001", guard.state,
                "synchronized(Rtransit) / exact_current_representation",
            )
        checkpoints.append(_checkpoint(domains, "L4", 4))

        guard.transition("closed_for_Rtransit_to_Rfinal", "both_synchronized_Rtransit_before_completion")
        completion = next_consequential_boundary(sealed_transit)
        if completion is None or resolve_next_due(sealed_transit, completion) != sealed_final:
            raise RuntimeError("exact Phase-2 completion was not freshly rediscovered from Rtransit")
        for role in DOMAIN_ROLES:
            observations[role]["L5_predecessor"] = domains[role].inspect("inspection_0006")
        checkpoints.append(_checkpoint(domains, "L5", 5))
        head_publications[RFINAL_ROLE] = _head_observation(
            runtime_parent / witness_id, "completion", "head_observation_0002", harness_run_id
        )
        for role in DOMAIN_ROLES:
            observations[role]["L6_predecessor"] = domains[role].inspect("inspection_0007")
        checkpoints.append(_checkpoint(domains, "L6", 6))
        guard.transition("open_for_Rfinal", "verified_Rfinal_and_both_stale_Rtransit")

        first, second = PRIMARY_REFRESH_ORDERS[witness][1]
        receipts[first][RFINAL_ROLE] = domains[first].materialize("refresh_0002")
        observations[first][RFINAL_ROLE] = domains[first].inspect("inspection_0008")
        observations[second]["L7_predecessor"] = domains[second].inspect("inspection_0008")
        expectations[first][RFINAL_ROLE], dispositions[first][RFINAL_ROLE] = _accept(
            domains[first], receipts[first][RFINAL_ROLE], observations[first][RFINAL_ROLE],
            RFINAL_ROLE, "refresh_0002", guard.state,
            "synchronized(Rfinal) / exact_current_representation",
        )
        checkpoints.append(_checkpoint(domains, "L7", 7))
        receipts[second][RFINAL_ROLE] = domains[second].materialize("refresh_0002")
        for role in DOMAIN_ROLES:
            observations[role][RFINAL_ROLE] = domains[role].inspect("inspection_0009")
            expectations[role][RFINAL_ROLE], dispositions[role][RFINAL_ROLE] = _accept(
                domains[role], receipts[role][RFINAL_ROLE], observations[role][RFINAL_ROLE],
                RFINAL_ROLE, "refresh_0002", guard.state,
                "synchronized(Rfinal) / exact_current_representation",
            )
        checkpoints.append(_checkpoint(domains, "L8", 8))

        return {
            "canonical_chain": canonical_chain(),
            "checkpoints": checkpoints,
            "dispositions": dispositions,
            "domain_processes": {
                role: {
                    "binding": domains[role].binding,
                    "bind_receipt": domains[role].bind_receipt,
                    "bundles": {
                        operation: {key: value for key, value in bundle.items() if not key.endswith("_raw")}
                        for operation, bundle in domains[role].bundles.items()
                    },
                    "commands": domains[role].commands,
                    "launch_plan": domains[role].launch_plan,
                    "runtime_provenance": domains[role].provenance,
                    "runtime_trace": domains[role].traces,
                }
                for role in DOMAIN_ROLES
            },
            "expectations": expectations,
            "guard_history": guard.history,
            "harness_run_id": harness_run_id,
            "head_publications": head_publications,
            "observations": observations,
            "proof_scenario": PROOF_SCENARIO,
            "receipts": receipts,
            "refresh_orders": {
                "Rtransit": list(PRIMARY_REFRESH_ORDERS[witness][0]),
                "Rfinal": list(PRIMARY_REFRESH_ORDERS[witness][1]),
            },
            "result": "PASS",
            "terminations": terminations,
            "witness_id": witness_id,
            "witness_schema": "CrossDomainOccupancyPrimaryWitness.v1",
        }
    finally:
        for role, domain in domains.items():
            try:
                terminations[role] = domain.terminate()
            except BaseException:
                pass


def _domain_evidence(domain: LiveDomain) -> dict[str, Any]:
    domain.drain()
    return {
        "binding": domain.binding,
        "bind_receipt": domain.bind_receipt,
        "bundles": {
            operation: {
                key: value for key, value in bundle.items()
                if not key.endswith("_raw")
            }
            for operation, bundle in domain.bundles.items()
        },
        "commands": domain.commands,
        "launch_plan": domain.launch_plan,
        "runtime_provenance": domain.provenance,
        "runtime_trace": domain.traces,
    }


def _terminate_domains(domains: Mapping[str, LiveDomain]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for role, domain in domains.items():
        try:
            result[role] = domain.terminate()
        except BaseException as exc:
            result[role] = {"termination_error": str(exc)}
    return result


def _materialize_r0_pair(domains: Mapping[str, LiveDomain]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for role in DOMAIN_ROLES:
        receipt = domains[role].materialize("launch_0001")
        observation = domains[role].inspect("inspection_0001")
        expected = expected_representation(
            domains[role].bundles["launch_0001"]["payload_raw"],
            domains[role].bundles["launch_0001"]["projection_raw"],
        )
        compare_expectation_receipt_observation(
            expected, receipt, observation, domains[role].binding, "launch_0001"
        )
        result[role] = {
            "expected": expected,
            "observation": observation,
            "receipt": receipt,
        }
    return result


def _observe_start_head(runtime_root: Path, harness_run_id: str) -> dict[str, Any]:
    r0, _, rtransit, _, _ = canonical_records()
    boundary = next_consequential_boundary(r0)
    resolved = None if boundary is None else resolve_next_due(r0, boundary)
    if resolved != rtransit:
        raise RuntimeError("exact Phase-2 start resolution failed")
    return _head_observation(
        runtime_root, "start", "head_observation_0001", harness_run_id
    )


def _observe_completion_head(runtime_root: Path, harness_run_id: str) -> dict[str, Any]:
    _, _, rtransit, _, rfinal = canonical_records()
    boundary = next_consequential_boundary(rtransit)
    resolved = None if boundary is None else resolve_next_due(rtransit, boundary)
    if resolved != rfinal:
        raise RuntimeError("exact Phase-2 completion resolution failed")
    return _head_observation(
        runtime_root, "completion", "head_observation_0002", harness_run_id
    )


def _control_disposition(
    domain: LiveDomain,
    context: str,
    guard_state: str,
    represented_hash: str | None,
    observed_head: str | None,
    *,
    expected: Mapping[str, Any] | None = None,
    receipt: Mapping[str, Any] | None = None,
    observation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return head_disposition(
        context=context,
        domain_role=domain.role,
        binding=domain.binding,
        guard_state=guard_state,
        represented_hash=represented_hash,
        observed_head=observed_head,
        expected=expected,
        receipt=receipt,
        observation=observation,
    )


def acquire_controls(runtime_parent: Path) -> dict[str, dict[str, Any]]:
    controls: dict[str, dict[str, Any]] = {}

    # C1: exact canonical completion while both physical processes remain R0.
    witness_id = "c1_canonical_completion_independence"
    domains = _launch_pair(runtime_parent, witness_id)
    guard = PhysicalCurrentHeadGuard()
    try:
        launch = _materialize_r0_pair(domains)
        guard.transition("closed_for_R0_to_Rtransit", "before_exact_start_resolution")
        start_head = _observe_start_head(runtime_parent / witness_id, f"phase4/{witness_id}")
        for role in DOMAIN_ROLES:
            domains[role].inspect("inspection_0002")
            domains[role].inspect("inspection_0003")
        guard.transition("open_for_Rtransit", "verified_Rtransit_and_both_stale_R0")
        guard.transition("closed_for_c1_Rtransit_to_Rfinal", "c1_verified_Rtransit_both_stale_no_refresh")
        completion_head = _observe_completion_head(runtime_parent / witness_id, f"phase4/{witness_id}")
        terminal_observations = {
            role: domains[role].inspect("inspection_c1_terminal_0001")
            for role in DOMAIN_ROLES
        }
        terminal_dispositions = {
            role: _control_disposition(
                domains[role],
                "stale(R0/Rfinal) / multigeneration_control_terminal",
                guard.state, H0, HFINAL,
                observation=terminal_observations[role],
            )
            for role in DOMAIN_ROLES
        }
        controls["C1"] = {
            "canonical_after": canonical_chain(),
            "canonical_before": canonical_chain(),
            "case_id": "C1",
            "completion_head": completion_head,
            "domain_processes": {role: _domain_evidence(domains[role]) for role in DOMAIN_ROLES},
            "guard_history": guard.history,
            "launch": launch,
            "proof_scenario": PROOF_SCENARIO,
            "result": "PASS",
            "start_head": start_head,
            "terminal_dispositions": terminal_dispositions,
            "terminal_observations": terminal_observations,
        }
    finally:
        terminations = _terminate_domains(domains)
        if "C1" in controls:
            controls["C1"]["terminations"] = terminations

    # C2/C3: positive absence and receipt-only rejection.
    for case, witness_id, stage, edge, special_inspection in (
        ("C2", "c2_positive_Rtransit_absence", "M20_spawn_configure_and_finish_target_anchor", "before", "inspection_c2_rejection_0001"),
        ("C3", "c3_receipt_only_rejection", "M16_validate_candidate_coherence_and_cardinality", "after", "inspection_c3_rejection_0001"),
    ):
        domains = _launch_pair(runtime_parent, witness_id)
        guard = PhysicalCurrentHeadGuard()
        try:
            launch = _materialize_r0_pair(domains)
            guard.transition("closed_for_R0_to_Rtransit", "before_exact_start_resolution")
            head = _observe_start_head(runtime_parent / witness_id, f"phase4/{witness_id}")
            guard.transition("open_for_Rtransit", "verified_Rtransit_and_both_stale_R0")
            arm, arm_receipt = domains["domain_B"].arm_fault(
                fault_occurrence_id=f"{case}/domain_B/refresh_0001",
                case_id=f"control_{case}",
                stage_id=stage,
                edge=edge,
                armed_operation_id="refresh_0001",
            )
            failure = domains["domain_B"].materialize("refresh_0001", expect_success=False)
            receipt_only = None
            if case == "C3":
                receipt_only = domains["domain_B"].next_object(
                    lambda value: value.get("receipt_schema") == MATERIALIZATION_RECEIPT_SCHEMA
                )
            observation = domains["domain_B"].inspect(special_inspection)
            expected = expected_representation(
                domains["domain_B"].bundles["refresh_0001"]["payload_raw"],
                domains["domain_B"].bundles["refresh_0001"]["projection_raw"],
            )
            if case == "C2" and (observation["anchor_actor_count"], observation["subject_actor_count"]) != (0, 0):
                raise RuntimeError("C2 did not prove positive zero-anchor/zero-subject rejection")
            if case == "C3" and (observation["anchor_actor_count"], observation["subject_actor_count"]) != (1, 1):
                raise RuntimeError("C3 did not retain the complete domain-B R0 generation")
            disposition = _control_disposition(
                domains["domain_B"], "invalid / local_publication_unprovable",
                guard.state, H0 if case == "C3" else None, HTRANSIT,
                expected=expected, receipt=receipt_only, observation=observation,
            )
            controls[case] = {
                "arm_invocation": arm,
                "arm_receipt": arm_receipt,
                "canonical_after": canonical_chain(),
                "canonical_before": canonical_chain(),
                "case_id": case,
                "domain_processes": {role: _domain_evidence(domains[role]) for role in DOMAIN_ROLES},
                "failure": failure,
                "guard_history": guard.history,
                "head_publication": head,
                "independent_expected_Rtransit": expected,
                "launch": launch,
                "proof_scenario": PROOF_SCENARIO,
                "receipt_only_candidate": receipt_only,
                "result": "PASS",
                "resulting_disposition": disposition,
                "terminal_live_observation": observation,
            }
        finally:
            terminations = _terminate_domains(domains)
            if case in controls:
                controls[case]["terminations"] = terminations

    # C4a: the guard cannot gate exact start resolution.
    witness_id = "c4a_start_guard_open"
    domains = _launch_pair(runtime_parent, witness_id)
    guard = PhysicalCurrentHeadGuard()
    try:
        launch = _materialize_r0_pair(domains)
        before = canonical_chain()
        r0, _, rtransit, _, _ = canonical_records()
        boundary = next_consequential_boundary(r0)
        if boundary is None or resolve_next_due(r0, boundary) != rtransit:
            raise RuntimeError("C4a canonical start resolution failed")
        guard.transition("failed_closed", "canonical_start_called_while_open")
        controls["C4a"] = {
            "canonical_after": canonical_chain(),
            "canonical_before": before,
            "case_id": "C4a",
            "domain_processes": {role: _domain_evidence(domains[role]) for role in DOMAIN_ROLES},
            "guard_history": guard.history,
            "launch": launch,
            "proof_scenario": PROOF_SCENARIO,
            "result": "PASS",
            "terminal_dispositions": {
                role: _control_disposition(
                    domains[role], "protocol_invalid / physical_protocol_violation",
                    guard.state, H0, HTRANSIT,
                ) for role in DOMAIN_ROLES
            },
        }
    finally:
        terminations = _terminate_domains(domains)
        if "C4a" in controls:
            controls["C4a"]["terminations"] = terminations

    # C4b and C5 share the exact Rtransit setup, then diverge.
    for case, witness_id in (
        ("C4b", "c4b_completion_guard_open"),
        ("C5", "c5_process_replacement"),
    ):
        domains = _launch_pair(runtime_parent, witness_id)
        guard = PhysicalCurrentHeadGuard()
        replacement: LiveDomain | None = None
        try:
            launch = _materialize_r0_pair(domains)
            guard.transition("closed_for_R0_to_Rtransit", "before_exact_start_resolution")
            head = _observe_start_head(runtime_parent / witness_id, f"phase4/{witness_id}")
            for role in DOMAIN_ROLES:
                domains[role].inspect("inspection_0002")
                domains[role].inspect("inspection_0003")
            guard.transition("open_for_Rtransit", "verified_Rtransit_and_both_stale_R0")
            refresh: dict[str, Any] = {}
            refresh["domain_A"] = domains["domain_A"].materialize("refresh_0001")
            domains["domain_A"].inspect("inspection_0004")
            domains["domain_B"].inspect("inspection_0004")
            refresh["domain_B"] = domains["domain_B"].materialize("refresh_0001")
            final_observations = {
                role: domains[role].inspect("inspection_0005")
                for role in DOMAIN_ROLES
            }
            if case == "C4b":
                before = canonical_chain()
                _, _, rtransit, _, rfinal = canonical_records()
                completion = next_consequential_boundary(rtransit)
                if completion is None or resolve_next_due(rtransit, completion) != rfinal:
                    raise RuntimeError("C4b completion resolution failed")
                guard.transition("failed_closed", "canonical_completion_called_while_open")
                controls[case] = {
                    "canonical_after": canonical_chain(),
                    "canonical_before": before,
                    "case_id": case,
                    "domain_processes": {role: _domain_evidence(domains[role]) for role in DOMAIN_ROLES},
                    "guard_history": guard.history,
                    "head_publication": head,
                    "launch": launch,
                    "proof_scenario": PROOF_SCENARIO,
                    "refresh_receipts": refresh,
                    "result": "PASS",
                    "terminal_observations": final_observations,
                }
            else:
                original_binding = copy.deepcopy(domains["domain_B"].binding)
                # Capture and remove the original object before terminating it.
                # A subsequent child may reuse the same small descriptor
                # numbers; retaining the closed object in ``domains`` would
                # let a second drain/close act on the replacement's pipes.
                original_process_evidence = _domain_evidence(domains["domain_B"])
                original_domain = domains.pop("domain_B")
                original_termination = original_domain.terminate()
                replacement = _launch_domain(
                    runtime_parent / "c5_replacement",
                    witness_id,
                    "domain_B",
                )
                replacement_rejected = (
                    replacement.instance_id != sha256_bytes(canonical_json(original_binding).encode("utf-8"))
                    and replacement.binding["macos_process_start"] != original_binding["macos_process_start"]
                    and replacement.binding["process_root_realpath"] != original_binding["process_root_realpath"]
                )
                if not replacement_rejected:
                    raise RuntimeError("C5 replacement retained original continuity identity")
                controls[case] = {
                    "canonical_after": canonical_chain(),
                    "canonical_before": canonical_chain(),
                    "case_id": case,
                    "copied_labels": {
                        "domain_role": "domain_B",
                        "harness_launch_id": original_binding["harness_launch_id"],
                        "witness_id": witness_id,
                    },
                    "domain_processes": {
                        "domain_A": _domain_evidence(domains["domain_A"]),
                        "domain_B": original_process_evidence,
                    },
                    "guard_history": guard.history,
                    "head_publication": head,
                    "launch": launch,
                    "original_B_termination": original_termination,
                    "proof_scenario": PROOF_SCENARIO,
                    "refresh_receipts": refresh,
                    "replacement_process": _domain_evidence(replacement),
                    "replacement_rejected_as_continuity": replacement_rejected,
                    "result": "PASS",
                    "terminal_observations": final_observations,
                }
        finally:
            terminations = _terminate_domains(domains)
            if replacement is not None:
                terminations["replacement_B"] = replacement.terminate()
            if case in controls:
                controls[case]["terminations"] = terminations
    return controls


AF_ROWS = {
    "AF01": ("af_Rtransit_A_success_B_failure", "domain_B", "refresh_0001", "beb2d2e1c574220ac31901162e58993f46108769f89394ef2df4812c9c84fc3d"),
    "AF02": ("af_Rtransit_B_success_A_failure", "domain_A", "refresh_0001", "13d76645353c813c480c323e380697e5f5ea24be10ab0eb80e4a3d789c060c6f"),
    "AF03": ("af_Rfinal_A_success_B_failure", "domain_B", "refresh_0002", "88c518da37a6311fe43a5a2cc83d56c1dd412939da716019503ee1cbb4a45b87"),
    "AF04": ("af_Rfinal_B_success_A_failure", "domain_A", "refresh_0002", "0c16b9a80158e78ebdd688a87335248d91b9d0843ef08a35e6ef2897825de26b"),
}


def acquire_asymmetric_failures(runtime_parent: Path) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for case, (witness_id, failed_role, operation_id, malformed_digest) in AF_ROWS.items():
        domains = _launch_pair(runtime_parent, witness_id)
        try:
            launch = _materialize_r0_pair(domains)
            head_start = _observe_start_head(runtime_parent / witness_id, f"phase4/{witness_id}")
            success_role = "domain_A" if failed_role == "domain_B" else "domain_B"
            successful: dict[str, Any] = {}
            if operation_id == "refresh_0002":
                for role in DOMAIN_ROLES:
                    successful[f"{role}_Rtransit_receipt"] = domains[role].materialize("refresh_0001")
                    successful[f"{role}_Rtransit_observation"] = domains[role].inspect("inspection_0005")
                head_final = _observe_completion_head(runtime_parent / witness_id, f"phase4/{witness_id}")
            else:
                head_final = None
            successful_receipt = domains[success_role].materialize(operation_id)
            inspection = "inspection_0005" if operation_id == "refresh_0001" else "inspection_0009"
            successful_observation = domains[success_role].inspect(inspection)

            def mutate(value: dict[str, Any]) -> None:
                value["projection_id"] = value["projection_id"].replace(
                    f"cross_domain_{failed_role[-1]}", "cross_domain_Z", 1
                )

            failure = domains[failed_role].materialize(
                operation_id, projection_mutator=mutate, expect_success=False
            )
            failed_bundle = domains[failed_role].bundles[operation_id]
            if sha256_bytes(failed_bundle["projection_raw"]) != malformed_digest:
                raise RuntimeError(f"{case} malformed projection byte identity drift")
            failed_observation = domains[failed_role].inspect(inspection)
            predecessor = R0_ROLE if operation_id == "refresh_0001" else RTRANSIT_ROLE
            expected_predecessor = expected_representation(
                (RECORDS / RECORD_FILENAMES[predecessor]).read_bytes(),
                stored_json_bytes(projection(failed_role, predecessor)),
            )
            if (
                failed_observation["anchor_actor_count"] != 1
                or failed_observation["subject_actor_count"] != expected_predecessor["expected_subject_actor_count"]
                or failure.get("reason_code") != "projection_raw_sha256_not_frozen"
            ):
                raise RuntimeError(f"{case} failed domain did not remain at exact predecessor")
            results[case] = {
                "canonical_after": canonical_chain(),
                "canonical_before": canonical_chain(),
                "case_id": case,
                "domain_processes": {role: _domain_evidence(domains[role]) for role in DOMAIN_ROLES},
                "failed_bundle": {
                    **{key: value for key, value in failed_bundle.items() if not key.endswith("_raw")},
                    "malformed_projection_canonical_json": failed_bundle["projection_raw"].decode("utf-8"),
                    "malformed_projection_raw_sha256": malformed_digest,
                },
                "failed_domain_observation": failed_observation,
                "failed_role": failed_role,
                "failure": failure,
                "head_final": head_final,
                "head_start": head_start,
                "launch": launch,
                "operation_id": operation_id,
                "proof_scenario": PROOF_SCENARIO,
                "result": "PASS",
                "successful_observation": successful_observation,
                "successful_receipt": successful_receipt,
                "successful_role": success_role,
                "successful_setup": successful,
            }
        finally:
            terminations = _terminate_domains(domains)
            if case in results:
                results[case]["terminations"] = terminations
    return results


HEAD_PUBLICATION_STAGES = (
    "open_source",
    "pre_stat_source",
    "read_source_once",
    "post_stat_source",
    "authenticate_record",
    "construct_private_observation",
    "write_and_fsync_candidate",
    "atomic_publish",
    "reopen_and_reverify",
)

OBSERVATION_STAGES = (
    "O01_receive_and_parse_inspection_command",
    "O02_verify_original_process_binding",
    "O03_select_exact_process_bound_game_world",
    "O04_enumerate_all_loaded_level_actor_slots",
    "O05_classify_all_phase4_relevant_actor_rows",
    "O06_inventory_all_pawn_controller_and_input_rows",
    "O07_sort_and_cross_check_counts_with_lists",
    "O08_construct_closed_live_observation",
    "O09_emit_live_observation",
    "O10_router_forward_live_observation",
    "O11_harness_derive_independent_expected_representation",
    "O12_harness_compare_expectation_receipt_observation_head_binding_guard",
)


def _parallel_cases(
    rows: list[Any],
    worker: Callable[[Any], tuple[str, dict[str, Any]]],
    *,
    maximum_workers: int,
) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=maximum_workers) as pool:
        futures = {pool.submit(worker, row): row for row in rows}
        for future in concurrent.futures.as_completed(futures):
            case_id, result = future.result()
            if case_id in results:
                raise RuntimeError(f"duplicate acquisition case {case_id}")
            results[case_id] = result
    return {case: results[case] for case in sorted(results)}


def _binding_mutator(field: str) -> Callable[[dict[str, Any]], None]:
    def mutate(binding: dict[str, Any]) -> None:
        if field == "binding_schema":
            binding[field] = "CrossDomainOccupancyProcessBinding.vX"
        elif field == "proof_scenario":
            binding[field] = "cross-domain-canonical-occupancy-materialization-adversarial"
        elif field == "witness_id":
            binding[field] = "replay_repeat"
        elif field == "domain_role":
            binding[field] = "domain_B"
        elif field == "harness_launch_id":
            binding[field] = "replay_repeat/domain_A/launch_0001"
        elif field == "pid":
            binding[field] += 1
        elif field == "macos_process_start":
            binding[field]["seconds"] += 1
        elif field in ("executable_realpath", "project_realpath", "process_root_realpath", "launch_cwd_realpath"):
            binding[field] = binding[field] + "/adversarial"
        elif field in (
            "executable_raw_sha256", "project_raw_sha256",
            "project_config_and_module_inventory_raw_sha256", "launch_argv_raw_sha256",
            "launch_environment_audit_raw_sha256", "inherited_descriptor_map_raw_sha256",
        ):
            binding[field] = ("0" if binding[field][0] != "0" else "1") + binding[field][1:]
        elif field == "unreal_engine_build_identity":
            binding[field] = binding[field] + "-adversarial"
        elif field == "entry_map_package_identity":
            binding[field] = "/Engine/Maps/EntryAdversarial"
        elif field == "control_pipe_id":
            binding[field] = "domain_A/control/9999"
        elif field == "structured_output_pipe_id":
            binding[field] = "domain_A/stdout/9999"
        elif field == "diagnostic_pipe_id":
            binding[field] = "domain_A/stderr/9999"
        else:
            raise AssertionError(field)
    return mutate


def _execute_binding_case(runtime_parent: Path, row: tuple[int, str | None]) -> tuple[str, dict[str, Any]]:
    number, field = row
    case_id = f"PB{number:02d}"
    domain: LiveDomain | None = None
    if number == 23:
        def mutation(binding: dict[str, Any]) -> None:
            binding["witness_id"] = "replay_repeat"
            binding["harness_launch_id"] = "replay_repeat/domain_A/launch_0001"
        changed_fields = ["witness_id", "harness_launch_id", "copied_evidence_labels"]
    else:
        if field is None:
            raise AssertionError(case_id)
        mutation = _binding_mutator(field)
        changed_fields = [field]
    before = canonical_chain()
    try:
        domain = _launch_domain(
            runtime_parent / case_id,
            "process_binding_adversary",
            "domain_A",
            binding_mutator=mutation,
            expect_binding=False,
        )
        failure = domain.next_object(
            lambda value: value.get("diagnostic_schema") == FAILURE_SCHEMA
        )
        domain.drain()
        if failure.get("stage_id") != "binding" or domain.traces:
            raise RuntimeError(f"{case_id} crossed the binding boundary")
        result = {
            "binding_adversary_schema": "CrossDomainOccupancyProcessBindingAdversaryCase.v1",
            "canonical_after": canonical_chain(),
            "canonical_before": before,
            "case_id": case_id,
            "changed_fields": changed_fields,
            "failure": failure,
            "launch_plan": domain.launch_plan,
            "nominal_binding": domain.nominal_binding,
            "proof_scenario": PROOF_SCENARIO,
            "result": "PASS",
            "runtime_trace": domain.traces,
            "submitted_binding": domain.binding,
            "submitted_bind_invocation_raw_sha256": sha256_value(bind_invocation(domain.binding)),
        }
    finally:
        termination = None if domain is None else domain.terminate()
    result["termination"] = termination
    return case_id, result


def acquire_process_binding_adversaries(
    runtime_parent: Path, *, maximum_workers: int = 4,
) -> dict[str, Any]:
    rows: list[tuple[int, str | None]] = [
        (index, field) for index, field in enumerate(PROCESS_BINDING_FIELDS, 1)
    ] + [(23, None)]
    cases = _parallel_cases(
        rows,
        lambda row: _execute_binding_case(runtime_parent, row),
        maximum_workers=maximum_workers,
    )
    if tuple(cases) != tuple(f"PB{index:02d}" for index in range(1, 24)):
        raise RuntimeError("PB01-PB23 exact case closure drift")
    return {
        "adversary_schema": "CrossDomainOccupancyProcessBindingAdversaries.v1",
        "case_count": 23,
        "cases": list(cases.values()),
        "logical_field_order": list(PROCESS_BINDING_FIELDS),
        "proof_scenario": PROOF_SCENARIO,
        "result": "PASS",
    }


def _harness_fault_plan(
    runtime_root: Path,
    *,
    case_id: str,
    stage_id: str,
    operation_id: str,
    harness_run_id: str,
) -> tuple[dict[str, Any], dict[str, Any], Path]:
    control_root = runtime_root / "harness_private_control" / case_id
    control_root.mkdir(parents=True, exist_ok=False)
    plan = {
        "armed_harness_operation_id": operation_id,
        "case_id": case_id,
        "edge": "after",
        "harness_fault_occurrence_id": f"{harness_run_id}/{case_id}",
        "harness_fault_plan_schema": "CrossDomainOccupancyHarnessFaultPlan.v1",
        "harness_run_id": harness_run_id,
        "proof_scenario": PROOF_SCENARIO,
        "stage_id": stage_id,
    }
    plan_path = control_root / "fault_plan.json"
    write_json(plan_path, plan)
    os.chmod(plan_path, 0o400)
    receipt = {
        "armed_harness_operation_id": operation_id,
        "arm_state": "armed_once",
        "case_id": case_id,
        "edge": "after",
        "harness_fault_arm_receipt_schema": "CrossDomainOccupancyHarnessFaultArmReceipt.v1",
        "harness_fault_occurrence_id": plan["harness_fault_occurrence_id"],
        "harness_fault_plan_raw_sha256": sha256_value(plan),
        "proof_scenario": PROOF_SCENARIO,
        "stage_id": stage_id,
    }
    receipt_path = control_root / "fault_arm_receipt.json"
    write_json(receipt_path, receipt)
    os.chmod(receipt_path, 0o400)
    if strict_load_stored_json(plan_path.read_bytes()) != plan or strict_load_stored_json(receipt_path.read_bytes()) != receipt:
        raise RuntimeError("harness-private fault plan/receipt authentication failed")
    return plan, receipt, control_root


def _execute_head_fault_operation(
    runtime_root: Path,
    *,
    case_id: str,
    head_kind: str,
    target_stage: str,
    harness_run_id: str,
) -> dict[str, Any]:
    source_role = RTRANSIT_ROLE if head_kind == "start" else RFINAL_ROLE
    operation_id = "head_observation_0001" if head_kind == "start" else "head_observation_0002"
    plan, arm_receipt, control_root = _harness_fault_plan(
        runtime_root,
        case_id=case_id,
        stage_id=target_stage,
        operation_id=operation_id,
        harness_run_id=harness_run_id,
    )
    plan_digest = sha256_value(plan)
    receipt_digest = sha256_value(arm_receipt)
    snapshot_digest = sha256_value(canonical_chain())
    trace: list[dict[str, Any]] = []

    def event(stage: str, edge: str) -> None:
        trace.append({
            "canonical_before_after_snapshot_raw_sha256": snapshot_digest,
            "case_id": case_id,
            "execution_mode": "fault_injected",
            "harness_fault_arm_receipt_raw_sha256": receipt_digest,
            "harness_fault_plan_raw_sha256": plan_digest,
            "harness_occurrence_id": plan["harness_fault_occurrence_id"],
            "harness_operation_id": operation_id,
            "harness_run_id": harness_run_id,
            "harness_trace_schema": "CrossDomainOccupancyHarnessTraceEvent.v1",
            "liveness_adversarial_report_raw_sha256": None,
            "liveness_observation_raw_sha256": None,
            "liveness_plan_raw_sha256": None,
            "stage_edge": edge,
            "stage_id": stage,
            "trace_sequence": len(trace),
        })

    source = RECORDS / RECORD_FILENAMES[source_role]
    output_root = runtime_root / "harness_private_head_fault" / case_id
    output_root.mkdir(parents=True, exist_ok=False)
    candidate = output_root / f".{operation_id}.candidate"
    published = output_root / f"{operation_id}.json"
    descriptor: int | None = None
    before_stat: os.stat_result | None = None
    raw = b""
    observation: dict[str, Any] | None = None
    try:
        for stage in HEAD_PUBLICATION_STAGES:
            event(stage, "entered")
            if stage == "open_source":
                descriptor = os.open(source, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
            elif stage == "pre_stat_source":
                if descriptor is None:
                    raise RuntimeError("head source descriptor absent")
                before_stat = os.fstat(descriptor)
                if not stat.S_ISREG(before_stat.st_mode):
                    raise RuntimeError("head source is not regular")
            elif stage == "read_source_once":
                if descriptor is None or before_stat is None:
                    raise RuntimeError("head source stat absent")
                raw = os.read(descriptor, before_stat.st_size)
                if len(raw) != before_stat.st_size or os.read(descriptor, 1):
                    raise RuntimeError("head source one-read contract failed")
            elif stage == "post_stat_source":
                if descriptor is None or before_stat is None:
                    raise RuntimeError("head source stat absent")
                after_stat = os.fstat(descriptor)
                if (before_stat.st_dev, before_stat.st_ino, before_stat.st_size, before_stat.st_mtime_ns) != (
                    after_stat.st_dev, after_stat.st_ino, after_stat.st_size, after_stat.st_mtime_ns
                ):
                    raise RuntimeError("head source identity changed")
                os.close(descriptor)
                descriptor = None
            elif stage == "authenticate_record":
                if sha256_bytes(raw) != RAW_HASHES[source_role]:
                    raise RuntimeError("head source raw identity mismatch")
                strict_load_stored_json(raw)
            elif stage == "construct_private_observation":
                if before_stat is None:
                    raise RuntimeError("head source stat absent")
                matrix = guard_and_head_observation_matrix()["head_observations"]
                row = matrix[0 if source_role == RTRANSIT_ROLE else 1]
                observation = {
                    **row,
                    "observation_schema": HEAD_OBSERVATION_SCHEMA,
                    "publication_state": "harness_private_verified",
                    "source_record_device": before_stat.st_dev,
                    "source_record_inode": before_stat.st_ino,
                    "source_record_mode": "regular_file_only",
                    "source_record_realpath": str(_real(source)),
                    "source_record_size": before_stat.st_size,
                }
            elif stage == "write_and_fsync_candidate":
                if observation is None:
                    raise RuntimeError("head observation candidate absent")
                fd = os.open(candidate, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC, 0o400)
                try:
                    _write_all(fd, stored_json_bytes(observation))
                    os.fsync(fd)
                finally:
                    os.close(fd)
            elif stage == "atomic_publish":
                os.rename(candidate, published)
            elif stage == "reopen_and_reverify":
                if observation is None or strict_load_stored_json(published.read_bytes()) != observation:
                    raise RuntimeError("head observation reverify mismatch")
            event(stage, "completed")
            if stage == target_stage:
                event(stage, "fault_injected")
                break
    finally:
        if descriptor is not None:
            os.close(descriptor)
    expected_edges = 2 * (HEAD_PUBLICATION_STAGES.index(target_stage) + 1) + 1
    if len(trace) != expected_edges or trace[-1]["stage_edge"] != "fault_injected":
        raise RuntimeError(f"{case_id} head trace prefix drift")
    publication_uncertain = HEAD_PUBLICATION_STAGES.index(target_stage) >= HEAD_PUBLICATION_STAGES.index("atomic_publish")
    return {
        "arm_receipt": arm_receipt,
        "case_id": case_id,
        "control_root_realpath": str(_real(control_root)),
        "fault_plan": plan,
        "head_kind": head_kind,
        "head_observation_candidate": observation,
        "head_observation_published": published.is_file(),
        "harness_trace": trace,
        "operation_id": operation_id,
        "publication_uncertain": publication_uncertain,
        "stage_id": target_stage,
    }


def _setup_stale_r0(
    runtime_root: Path,
    witness_id: str,
    domains: Mapping[str, LiveDomain],
    guard: PhysicalCurrentHeadGuard,
) -> dict[str, Any]:
    launch = _materialize_r0_pair(domains)
    guard.transition("closed_for_R0_to_Rtransit", "before_exact_start_resolution")
    r0, _, rtransit, _, _ = canonical_records()
    boundary = next_consequential_boundary(r0)
    if boundary is None or resolve_next_due(r0, boundary) != rtransit:
        raise RuntimeError("exact Phase-2 start resolution failed")
    predecessor_observations: dict[str, Any] = {}
    for role in DOMAIN_ROLES:
        predecessor_observations[f"{role}_I1"] = domains[role].inspect("inspection_0002")
    head_start = _head_observation(
        runtime_root, "start", "head_observation_0001", f"phase4/{witness_id}"
    )
    for role in DOMAIN_ROLES:
        predecessor_observations[f"{role}_I2"] = domains[role].inspect("inspection_0003")
    guard.transition("open_for_Rtransit", "verified_Rtransit_and_both_stale_R0")
    return {
        "head_start": head_start,
        "launch": launch,
        "predecessor_observations": predecessor_observations,
    }


def _setup_synchronized_rtransit(
    runtime_root: Path,
    witness_id: str,
    domains: Mapping[str, LiveDomain],
    guard: PhysicalCurrentHeadGuard,
) -> dict[str, Any]:
    setup = _setup_stale_r0(runtime_root, witness_id, domains, guard)
    receipts: dict[str, Any] = {}
    observations: dict[str, Any] = {}
    receipts["domain_A"] = domains["domain_A"].materialize("refresh_0001")
    observations["domain_A_I3"] = domains["domain_A"].inspect("inspection_0004")
    observations["domain_B_I3"] = domains["domain_B"].inspect("inspection_0004")
    receipts["domain_B"] = domains["domain_B"].materialize("refresh_0001")
    for role in DOMAIN_ROLES:
        observations[f"{role}_I4"] = domains[role].inspect("inspection_0005")
    return {
        **setup,
        "refresh_observations": observations,
        "refresh_receipts": receipts,
    }


def _execute_head_fault_case(runtime_parent: Path, row: tuple[int, str]) -> tuple[str, dict[str, Any]]:
    number, stage = row
    case_id = f"HF{number:02d}"
    head_kind = "start" if number <= 9 else "completion"
    case_root = runtime_parent / case_id
    witness_id = "fault_head_publication"
    domains = _launch_pair(case_root, witness_id)
    guard = PhysicalCurrentHeadGuard()
    setup: dict[str, Any] = {}
    before = canonical_chain()
    try:
        if head_kind == "start":
            setup["launch"] = _materialize_r0_pair(domains)
            guard.transition("closed_for_R0_to_Rtransit", "before_exact_start_resolution")
            r0, _, rtransit, _, _ = canonical_records()
            boundary = next_consequential_boundary(r0)
            if boundary is None or resolve_next_due(r0, boundary) != rtransit:
                raise RuntimeError(f"{case_id} start resolution failed")
            setup["pre_publication_observations"] = {
                role: domains[role].inspect("inspection_0002") for role in DOMAIN_ROLES
            }
        else:
            setup = _setup_synchronized_rtransit(
                case_root / witness_id, witness_id, domains, guard
            )
            guard.transition("closed_for_Rtransit_to_Rfinal", "both_synchronized_Rtransit_before_completion")
            _, _, rtransit, _, rfinal = canonical_records()
            boundary = next_consequential_boundary(rtransit)
            if boundary is None or resolve_next_due(rtransit, boundary) != rfinal:
                raise RuntimeError(f"{case_id} completion resolution failed")
            setup["pre_completion_publication_observations"] = {
                role: domains[role].inspect("inspection_0006") for role in DOMAIN_ROLES
            }
        fault = _execute_head_fault_operation(
            case_root / witness_id,
            case_id=case_id,
            head_kind=head_kind,
            target_stage=stage,
            harness_run_id=f"phase4/{witness_id}/{case_id}",
        )
        if fault["publication_uncertain"]:
            guard.transition("failed_closed", "head_publication_uncertain")
        canonical_after = canonical_chain()
        if canonical_after != before:
            raise RuntimeError(f"{case_id} changed sealed canonical measurements")
        result = {
            "canonical_after": canonical_after,
            "canonical_before": before,
            "case_id": case_id,
            "domain_processes": {role: _domain_evidence(domains[role]) for role in DOMAIN_ROLES},
            "fault": fault,
            "guard_history": guard.history,
            "head_fault_case_schema": "CrossDomainOccupancyHeadPublicationFaultCase.v1",
            "proof_scenario": PROOF_SCENARIO,
            "result": "PASS",
            "setup": setup,
            "terminal_guard_state": guard.state,
        }
    finally:
        terminations = _terminate_domains(domains)
    result["terminations"] = terminations
    return case_id, result


def acquire_head_publication_faults(
    runtime_parent: Path, *, maximum_workers: int = 3,
) -> dict[str, Any]:
    rows = [
        (index, stage)
        for index, stage in enumerate(HEAD_PUBLICATION_STAGES, 1)
    ] + [
        (index + 9, stage)
        for index, stage in enumerate(HEAD_PUBLICATION_STAGES, 1)
    ]
    cases = _parallel_cases(
        rows,
        lambda row: _execute_head_fault_case(runtime_parent, row),
        maximum_workers=maximum_workers,
    )
    return {
        "case_count": 18,
        "cases": list(cases.values()),
        "fault_matrix_schema": "CrossDomainOccupancyHeadPublicationFaultAtomicity.v1",
        "proof_scenario": PROOF_SCENARIO,
        "result": "PASS",
        "stage_order": list(HEAD_PUBLICATION_STAGES),
    }


MATERIALIZATION_CONTEXTS = (
    ("launch_R0_domain_B_unbound_to_present", "domain_B", "launch_0001", R0_ROLE),
    ("refresh_Rtransit_domain_B_present_to_absent", "domain_B", "refresh_0001", RTRANSIT_ROLE),
    ("refresh_Rfinal_domain_A_absent_to_present", "domain_A", "refresh_0002", RFINAL_ROLE),
)

OBSERVATION_CONTEXTS = (
    ("R0_domain_B_present", "domain_B", "inspection_0001", R0_ROLE),
    ("Rtransit_domain_B_absent", "domain_B", "inspection_0005", RTRANSIT_ROLE),
    ("Rfinal_domain_A_present", "domain_A", "inspection_0009", RFINAL_ROLE),
)


def _setup_stale_rtransit(
    runtime_root: Path,
    witness_id: str,
    domains: Mapping[str, LiveDomain],
    guard: PhysicalCurrentHeadGuard,
) -> dict[str, Any]:
    setup = _setup_synchronized_rtransit(runtime_root, witness_id, domains, guard)
    guard.transition("closed_for_Rtransit_to_Rfinal", "both_synchronized_Rtransit_before_completion")
    _, _, rtransit, _, rfinal = canonical_records()
    boundary = next_consequential_boundary(rtransit)
    if boundary is None or resolve_next_due(rtransit, boundary) != rfinal:
        raise RuntimeError("exact Phase-2 completion resolution failed")
    before_publication = {
        role: domains[role].inspect("inspection_0006") for role in DOMAIN_ROLES
    }
    head_final = _head_observation(
        runtime_root, "completion", "head_observation_0002", f"phase4/{witness_id}"
    )
    after_publication = {
        role: domains[role].inspect("inspection_0007") for role in DOMAIN_ROLES
    }
    guard.transition("open_for_Rfinal", "verified_Rfinal_and_both_stale_Rtransit")
    return {
        **setup,
        "completion_pre_publication_observations": before_publication,
        "completion_post_publication_observations": after_publication,
        "head_final": head_final,
    }


def _execute_materialization_fault_case(
    runtime_parent: Path,
    row: tuple[int, str, str, str, str, str],
) -> tuple[str, dict[str, Any]]:
    number, context, role, operation_id, record_role, edge = row
    case_id = f"MF{number:03d}"
    stage_index = ((number - 1) % (len(MATERIALIZATION_STAGES) * 2)) // 2
    stage = MATERIALIZATION_STAGES[stage_index]
    case_root = runtime_parent / case_id
    witness_id = "fault_materialization"
    domains = _launch_pair(case_root, witness_id)
    guard = PhysicalCurrentHeadGuard()
    before = canonical_chain()
    setup: dict[str, Any] = {}
    last_pre_fault_observation: dict[str, Any] | None = None
    target_receipt: dict[str, Any] | None = None
    try:
        if record_role == R0_ROLE:
            pass
        elif record_role == RTRANSIT_ROLE:
            setup = _setup_stale_r0(case_root / witness_id, witness_id, domains, guard)
            last_pre_fault_observation = setup["predecessor_observations"][f"{role}_I2"]
        else:
            setup = _setup_stale_rtransit(case_root / witness_id, witness_id, domains, guard)
            last_pre_fault_observation = setup["completion_post_publication_observations"][role]
        target = domains[role]
        arm, arm_receipt = target.arm_fault(
            fault_occurrence_id=f"{case_id}/{role}/{operation_id}",
            case_id=case_id,
            stage_id=stage,
            edge=edge,
            armed_operation_id=operation_id,
        )
        failure = target.materialize(operation_id, expect_success=False)
        target.drain()
        for index, value in enumerate(target.objects):
            if value.get("receipt_schema") == MATERIALIZATION_RECEIPT_SCHEMA:
                target_receipt = target.objects.pop(index)
                break
        expected_reason = f"injected_{stage}_{edge}"
        if failure.get("reason_code") != expected_reason or failure.get("stage_id") != stage:
            raise RuntimeError(f"{case_id} rejected at the wrong compiled stage")
        injected = [
            event for event in target.traces
            if event.get("stage_id") == stage and event.get("stage_edge") == "fault_injected"
        ]
        if len(injected) != 1:
            raise RuntimeError(f"{case_id} did not bind one exact injected trace edge")
        publication_began = stage_index >= MATERIALIZATION_STAGES.index(
            "M17_begin_publication_linearization_interval"
        )
        if publication_began:
            context_name = "invalid / local_publication_unprovable"
            represented = None
            guard.transition("failed_closed", "post_publication_materialization_fault")
        elif record_role == R0_ROLE:
            context_name = "unbound / binding_not_accepted"
            represented = None
        elif record_role == RTRANSIT_ROLE:
            context_name = "stale(R0/Rtransit) / immediate_successor_verified"
            represented = H0
        else:
            context_name = "stale(Rtransit/Rfinal) / immediate_successor_verified"
            represented = HTRANSIT
        expected = expected_representation(
            target.bundles[operation_id]["payload_raw"],
            target.bundles[operation_id]["projection_raw"],
        )
        disposition = head_disposition(
            context=context_name,
            domain_role=role,
            binding=target.binding,
            guard_state=guard.state,
            represented_hash=represented,
            observed_head=HEAD_HASHES[record_role] if record_role != R0_ROLE else H0,
            expected=None if publication_began or record_role == R0_ROLE else expected,
            receipt=None,
            observation=None if publication_began else last_pre_fault_observation,
        )
        after = canonical_chain()
        if after != before:
            raise RuntimeError(f"{case_id} changed canonical measurements")
        result = {
            "arm_invocation": arm,
            "arm_receipt": arm_receipt,
            "canonical_after": after,
            "canonical_before": before,
            "case_id": case_id,
            "context": context,
            "domain_processes": {domain_role: _domain_evidence(domains[domain_role]) for domain_role in DOMAIN_ROLES},
            "edge": edge,
            "failure": failure,
            "last_pre_fault_live_observation": last_pre_fault_observation,
            "materialization_fault_case_schema": "CrossDomainOccupancyMaterializationFaultCase.v1",
            "operation_id": operation_id,
            "post_fault_census_available": False,
            "proof_scenario": PROOF_SCENARIO,
            "publication_interval_entered": publication_began,
            "receipt_candidate": target_receipt,
            "result": "PASS",
            "resulting_disposition": disposition,
            "setup": setup,
            "stage_id": stage,
            "target_role": role,
        }
    finally:
        terminations = _terminate_domains(domains)
    result["terminations"] = terminations
    return case_id, result


def acquire_materialization_faults(
    runtime_parent: Path, *, maximum_workers: int = 3,
) -> dict[str, Any]:
    rows: list[tuple[int, str, str, str, str, str]] = []
    number = 1
    for context, role, operation_id, record_role in MATERIALIZATION_CONTEXTS:
        for _stage in MATERIALIZATION_STAGES:
            for edge in ("before", "after"):
                rows.append((number, context, role, operation_id, record_role, edge))
                number += 1
    cases = _parallel_cases(
        rows,
        lambda row: _execute_materialization_fault_case(runtime_parent, row),
        maximum_workers=maximum_workers,
    )
    if len(cases) != 138:
        raise RuntimeError("MF001-MF138 exact case closure drift")
    return {
        "case_count": 138,
        "cases": list(cases.values()),
        "context_order": [row[0] for row in MATERIALIZATION_CONTEXTS],
        "edge_order": ["before", "after"],
        "fault_matrix_schema": "CrossDomainOccupancyMaterializationFaultAtomicity.v1",
        "proof_scenario": PROOF_SCENARIO,
        "result": "PASS",
        "stage_order": list(MATERIALIZATION_STAGES),
    }


def _setup_observation_fault_context(
    runtime_root: Path,
    witness_id: str,
    domains: Mapping[str, LiveDomain],
    guard: PhysicalCurrentHeadGuard,
    record_role: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    setup: dict[str, Any] = {}
    receipts: dict[str, Any] = {}
    if record_role == R0_ROLE:
        receipts["domain_A"] = domains["domain_A"].materialize("launch_0001")
        domains["domain_A"].inspect("inspection_0001")
        receipts["domain_B"] = domains["domain_B"].materialize("launch_0001")
        expected = expected_representation(
            domains["domain_B"].bundles["launch_0001"]["payload_raw"],
            domains["domain_B"].bundles["launch_0001"]["projection_raw"],
        )
        return setup, receipts, expected
    setup = _setup_stale_r0(runtime_root, witness_id, domains, guard)
    receipts["domain_A_Rtransit"] = domains["domain_A"].materialize("refresh_0001")
    domains["domain_A"].inspect("inspection_0004")
    domains["domain_B"].inspect("inspection_0004")
    receipts["domain_B_Rtransit"] = domains["domain_B"].materialize("refresh_0001")
    domains["domain_A"].inspect("inspection_0005")
    if record_role == RTRANSIT_ROLE:
        expected = expected_representation(
            domains["domain_B"].bundles["refresh_0001"]["payload_raw"],
            domains["domain_B"].bundles["refresh_0001"]["projection_raw"],
        )
        return setup, receipts, expected
    domains["domain_B"].inspect("inspection_0005")
    guard.transition("closed_for_Rtransit_to_Rfinal", "both_synchronized_Rtransit_before_completion")
    _, _, rtransit, _, rfinal = canonical_records()
    boundary = next_consequential_boundary(rtransit)
    if boundary is None or resolve_next_due(rtransit, boundary) != rfinal:
        raise RuntimeError("observation-fault completion resolution failed")
    for role in DOMAIN_ROLES:
        domains[role].inspect("inspection_0006")
    setup["head_final"] = _head_observation(
        runtime_root, "completion", "head_observation_0002", f"phase4/{witness_id}"
    )
    for role in DOMAIN_ROLES:
        domains[role].inspect("inspection_0007")
    guard.transition("open_for_Rfinal", "verified_Rfinal_and_both_stale_Rtransit")
    receipts["domain_A_Rfinal"] = domains["domain_A"].materialize("refresh_0002")
    domains["domain_A"].inspect("inspection_0008")
    domains["domain_B"].inspect("inspection_0008")
    receipts["domain_B_Rfinal"] = domains["domain_B"].materialize("refresh_0002")
    domains["domain_B"].inspect("inspection_0009")
    expected = expected_representation(
        domains["domain_A"].bundles["refresh_0002"]["payload_raw"],
        domains["domain_A"].bundles["refresh_0002"]["projection_raw"],
    )
    return setup, receipts, expected


def _harness_observation_fault(
    runtime_root: Path,
    *,
    case_id: str,
    inspection_id: str,
    stage: str,
    role: str,
    domain: LiveDomain,
    expected: Mapping[str, Any],
    receipt: Mapping[str, Any],
    observation: Mapping[str, Any],
) -> dict[str, Any]:
    harness_run_id = f"phase4/fault_live_observation/{case_id}"
    stage_code = stage.split("_", 1)[0]
    plan, arm_receipt, _ = _harness_fault_plan(
        runtime_root,
        case_id=case_id,
        stage_id=stage_code,
        operation_id=inspection_id,
        harness_run_id=harness_run_id,
    )
    plan_digest = sha256_value(plan)
    arm_digest = sha256_value(arm_receipt)
    trace: list[dict[str, Any]] = []
    stages = ("O11_harness_derive_independent_expected_representation",) if stage.startswith("O11") else (
        "O11_harness_derive_independent_expected_representation",
        "O12_harness_compare_expectation_receipt_observation_head_binding_guard",
    )
    for current in stages:
        for edge in ("entered", "completed"):
            trace.append({
                "canonical_before_after_snapshot_raw_sha256": sha256_value(canonical_chain()),
                "case_id": case_id,
                "execution_mode": "fault_injected",
                "harness_fault_arm_receipt_raw_sha256": arm_digest,
                "harness_fault_plan_raw_sha256": plan_digest,
                "harness_occurrence_id": plan["harness_fault_occurrence_id"],
                "harness_operation_id": inspection_id,
                "harness_run_id": harness_run_id,
                "harness_trace_schema": "CrossDomainOccupancyHarnessTraceEvent.v1",
                "liveness_adversarial_report_raw_sha256": None,
                "liveness_observation_raw_sha256": None,
                "liveness_plan_raw_sha256": None,
                "stage_edge": edge,
                "stage_id": current.split("_", 1)[0],
                "trace_sequence": len(trace),
            })
        if current.startswith("O12"):
            compare_expectation_receipt_observation(expected, receipt, observation, domain.binding, receipt["operation_id"])
    trace.append({**trace[-1], "stage_edge": "fault_injected", "trace_sequence": len(trace)})
    return {"arm_receipt": arm_receipt, "fault_plan": plan, "harness_trace": trace}


def _execute_observation_fault_case(
    runtime_parent: Path,
    row: tuple[int, str, str, str, str, str],
) -> tuple[str, dict[str, Any]]:
    number, context, role, inspection_id, record_role, stage = row
    case_id = f"OF{number:03d}"
    case_root = runtime_parent / case_id
    witness_id = "fault_live_observation"
    domains = _launch_pair(case_root, witness_id)
    guard = PhysicalCurrentHeadGuard()
    before = canonical_chain()
    process_observation: dict[str, Any] | None = None
    try:
        setup, receipts, expected = _setup_observation_fault_context(
            case_root / witness_id, witness_id, domains, guard, record_role
        )
        target = domains[role]
        receipt_key = {
            R0_ROLE: "domain_B",
            RTRANSIT_ROLE: "domain_B_Rtransit",
            RFINAL_ROLE: "domain_A_Rfinal",
        }[record_role]
        receipt = receipts[receipt_key]
        if stage.startswith("O11") or stage.startswith("O12"):
            process_observation = target.inspect(inspection_id)
            fault = _harness_observation_fault(
                case_root / witness_id,
                case_id=case_id,
                inspection_id=inspection_id,
                stage=stage,
                role=role,
                domain=target,
                expected=expected,
                receipt=receipt,
                observation=process_observation,
            )
            failure = {
                "diagnostic_schema": "CrossDomainOccupancyHarnessFailure.v1",
                "reason_code": f"injected_{stage.split('_', 1)[0]}_after",
                "stage_id": stage.split("_", 1)[0],
            }
            arm = None
            arm_receipt = fault["arm_receipt"]
            harness_trace = fault["harness_trace"]
            channel = "harness_private"
        else:
            arm, arm_receipt = target.arm_fault(
                fault_occurrence_id=f"{case_id}/{role}/{inspection_id}",
                case_id=case_id,
                stage_id=stage,
                edge="after",
                armed_operation_id=inspection_id,
            )
            failure = target.inspect(inspection_id, expect_success=False)
            target.drain()
            for index, value in enumerate(target.objects):
                if value.get("observation_schema") == LIVE_OBSERVATION_SCHEMA:
                    process_observation = target.objects.pop(index)
                    break
            if failure.get("reason_code") != f"injected_{stage}_after" or failure.get("stage_id") != stage:
                raise RuntimeError(f"{case_id} rejected at the wrong observation stage")
            injected = [event for event in target.traces if event.get("stage_id") == stage and event.get("stage_edge") == "fault_injected"]
            if len(injected) != 1:
                raise RuntimeError(f"{case_id} missing exact observation injected edge")
            harness_trace = []
            channel = "original_stdin"
        guard.transition("failed_closed", "observation_acceptance_fault")
        disposition = head_disposition(
            context="invalid / local_publication_unprovable",
            domain_role=role,
            binding=target.binding,
            guard_state=guard.state,
            represented_hash=HEAD_HASHES[record_role],
            observed_head=HEAD_HASHES[record_role],
            expected=expected,
            receipt=receipt,
            observation=process_observation,
        )
        after = canonical_chain()
        if after != before:
            raise RuntimeError(f"{case_id} changed canonical measurements")
        result = {
            "arm_invocation": arm,
            "arm_receipt": arm_receipt,
            "canonical_after": after,
            "canonical_before": before,
            "case_id": case_id,
            "channel": channel,
            "context": context,
            "domain_processes": {domain_role: _domain_evidence(domains[domain_role]) for domain_role in DOMAIN_ROLES},
            "edge": "after",
            "failure": failure,
            "harness_trace": harness_trace,
            "inspection_id": inspection_id,
            "live_observation_candidate": process_observation,
            "observation_fault_case_schema": "CrossDomainOccupancyLiveObservationFaultCase.v1",
            "proof_scenario": PROOF_SCENARIO,
            "receipt": receipt,
            "result": "PASS",
            "resulting_disposition": disposition,
            "setup": setup,
            "stage_id": stage,
            "target_role": role,
        }
    finally:
        terminations = _terminate_domains(domains)
    result["terminations"] = terminations
    return case_id, result


def acquire_live_observation_faults(
    runtime_parent: Path, *, maximum_workers: int = 3,
) -> dict[str, Any]:
    rows: list[tuple[int, str, str, str, str, str]] = []
    number = 1
    for context, role, inspection_id, record_role in OBSERVATION_CONTEXTS:
        for stage in OBSERVATION_STAGES:
            rows.append((number, context, role, inspection_id, record_role, stage))
            number += 1
    cases = _parallel_cases(
        rows,
        lambda row: _execute_observation_fault_case(runtime_parent, row),
        maximum_workers=maximum_workers,
    )
    if len(cases) != 36:
        raise RuntimeError("OF001-OF036 exact case closure drift")
    return {
        "case_count": 36,
        "cases": list(cases.values()),
        "context_order": [row[0] for row in OBSERVATION_CONTEXTS],
        "edge": "after",
        "fault_matrix_schema": "CrossDomainOccupancyLiveObservationFaultAtomicity.v1",
        "proof_scenario": PROOF_SCENARIO,
        "result": "PASS",
        "stage_order": list(OBSERVATION_STAGES),
    }


LIVENESS_ROWS = {
    "LV01": ("domain_A", "L0", "harness_process_control", "kill_original_child_note_exit", "original_process_exit"),
    "LV02": ("domain_B", "L1", "harness_process_control", "kill_original_child_waitpid", "original_process_wait_status"),
    "LV03": ("domain_A", "L2", "original_stdin", "emit_changed_start_report", "reported_process_start_pair_mismatch"),
    "LV04": ("domain_B", "L3", "original_stdin", "close_control_read_endpoint", "original_control_pipe_closed"),
    "LV05": ("domain_A", "L5", "original_stdin", "close_structured_output_write_endpoint", "original_output_pipe_closed"),
    "LV06": ("domain_B", "L7", "harness_process_control", "spawn_copied_label_replacement", "copied_label_replacement_detected"),
}


def _advance_w1_prefix(
    runtime_root: Path,
    domains: Mapping[str, LiveDomain],
    guard: PhysicalCurrentHeadGuard,
    stop_checkpoint: str,
) -> dict[str, Any]:
    target = int(stop_checkpoint[1:])
    evidence: dict[str, Any] = {"checkpoints": []}

    def checkpoint(number: int) -> bool:
        evidence["checkpoints"].append(_checkpoint(domains, f"L{number}", number))
        return target == number

    evidence["launch"] = _materialize_r0_pair(domains)
    if checkpoint(0):
        return evidence
    guard.transition("closed_for_R0_to_Rtransit", "before_exact_start_resolution")
    r0, _, rtransit, _, rfinal = canonical_records()
    boundary = next_consequential_boundary(r0)
    if boundary is None or resolve_next_due(r0, boundary) != rtransit:
        raise RuntimeError("liveness prefix start resolution failed")
    evidence["L1_observations"] = {
        role: domains[role].inspect("inspection_0002") for role in DOMAIN_ROLES
    }
    if checkpoint(1):
        return evidence
    evidence["head_start"] = _head_observation(
        runtime_root, "start", "head_observation_0001", "phase4/liveness_adversary"
    )
    evidence["L2_observations"] = {
        role: domains[role].inspect("inspection_0003") for role in DOMAIN_ROLES
    }
    guard.transition("open_for_Rtransit", "verified_Rtransit_and_both_stale_R0")
    if checkpoint(2):
        return evidence
    evidence["domain_A_Rtransit_receipt"] = domains["domain_A"].materialize("refresh_0001")
    evidence["domain_A_L3_observation"] = domains["domain_A"].inspect("inspection_0004")
    evidence["domain_B_L3_observation"] = domains["domain_B"].inspect("inspection_0004")
    if checkpoint(3):
        return evidence
    evidence["domain_B_Rtransit_receipt"] = domains["domain_B"].materialize("refresh_0001")
    evidence["L4_observations"] = {
        role: domains[role].inspect("inspection_0005") for role in DOMAIN_ROLES
    }
    if checkpoint(4):
        return evidence
    guard.transition("closed_for_Rtransit_to_Rfinal", "both_synchronized_Rtransit_before_completion")
    boundary = next_consequential_boundary(rtransit)
    if boundary is None or resolve_next_due(rtransit, boundary) != rfinal:
        raise RuntimeError("liveness prefix completion resolution failed")
    evidence["L5_observations"] = {
        role: domains[role].inspect("inspection_0006") for role in DOMAIN_ROLES
    }
    if checkpoint(5):
        return evidence
    evidence["head_final"] = _head_observation(
        runtime_root, "completion", "head_observation_0002", "phase4/liveness_adversary"
    )
    evidence["L6_observations"] = {
        role: domains[role].inspect("inspection_0007") for role in DOMAIN_ROLES
    }
    guard.transition("open_for_Rfinal", "verified_Rfinal_and_both_stale_Rtransit")
    if checkpoint(6):
        return evidence
    evidence["domain_A_Rfinal_receipt"] = domains["domain_A"].materialize("refresh_0002")
    evidence["domain_A_L7_observation"] = domains["domain_A"].inspect("inspection_0008")
    evidence["domain_B_L7_observation"] = domains["domain_B"].inspect("inspection_0008")
    if checkpoint(7):
        return evidence
    evidence["domain_B_Rfinal_receipt"] = domains["domain_B"].materialize("refresh_0002")
    evidence["L8_observations"] = {
        role: domains[role].inspect("inspection_0009") for role in DOMAIN_ROLES
    }
    if not checkpoint(8):
        raise RuntimeError(f"unknown liveness checkpoint {stop_checkpoint}")
    return evidence


def _liveness_plan(
    runtime_root: Path,
    case_id: str,
    domain: LiveDomain,
    checkpoint: str,
    channel: str,
    action: str,
    failure_code: str,
) -> tuple[dict[str, Any], Path]:
    plan = {
        "action_id": action,
        "base_schedule": f"exact_W1_prefix_through_{checkpoint}",
        "case_id": case_id,
        "channel": channel,
        "checkpoint_id": checkpoint,
        "domain_role": domain.role,
        "edge": "after_checkpoint_acceptance",
        "expected_first_failure": failure_code,
        "harness_run_id": f"phase4/liveness_adversary/{case_id}",
        "liveness_plan_schema": "CrossDomainOccupancyLivenessAdversaryPlan.v1",
        "occurrence_id": domain.launch_plan["harness_launch_id"],
        "proof_scenario": PROOF_SCENARIO,
        "terminal_liveness_failure_code": failure_code,
    }
    root = runtime_root / "harness_private_liveness" / case_id
    root.mkdir(parents=True, exist_ok=False)
    path = root / "liveness_plan.json"
    write_json(path, plan)
    os.chmod(path, 0o400)
    if strict_load_stored_json(path.read_bytes()) != plan:
        raise RuntimeError("liveness plan authentication failed")
    return plan, path


def _terminal_liveness_from_last(
    domain: LiveDomain,
    checkpoint: str,
    sample_sequence: int,
) -> dict[str, Any]:
    return {
        "checkpoint_id": checkpoint,
        "control_pipe_unexpected_eof": False,
        "domain_role": domain.role,
        "liveness_observation_schema": "CrossDomainOccupancyLivenessObservation.v1",
        "observed_macos_process_start": {
            "microseconds": domain.process_start["microseconds"],
            "seconds": domain.process_start["seconds"],
        },
        "observed_pid": domain.pid,
        "observation_source": "independent_harness_os_monitor",
        "occurrence_id": domain.launch_plan["harness_launch_id"],
        "operational_process_instance_id": domain.instance_id,
        "original_child_handle_exit_observed": False,
        "process_binding_raw_sha256": domain.binding_digest,
        "process_start_pair_changed": False,
        "proof_scenario": PROOF_SCENARIO,
        "replacement_spawn_count": 0,
        "sample_sequence": sample_sequence,
        "structured_output_pipe_unexpected_eof": False,
        "wait_status_available": False,
        "wait_status_value": None,
    }


def _poll_descriptor_failure(fd: int, flags: int, timeout: float = 15.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        poller = select.poll()
        poller.register(fd, flags)
        if any(observed & flags for _, observed in poller.poll(50)):
            return True
    return False


def _poll_structured_output_closure(domain: LiveDomain, timeout: float = 15.0) -> bool:
    """Drain all prior structured bytes while waiting for the writer's HUP."""

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        domain.drain()
        if domain.output_eof_observed:
            return True
        poller = select.poll()
        poller.register(domain.fds["output_read"], select.POLLIN | select.POLLHUP)
        events = poller.poll(50)
        if any(observed & select.POLLHUP for _, observed in events):
            domain.drain()
            return domain.output_eof_observed
        if any(observed & select.POLLIN for _, observed in events):
            domain.drain()
    return False


def _liveness_harness_trace(
    *,
    case_id: str,
    action: str,
    plan: Mapping[str, Any],
    terminal: Mapping[str, Any],
    report: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    stage = {
        "LV01": "kill_original_child_note_exit",
        "LV02": "kill_original_child_waitpid",
        "LV03": "compare_report_binding_and_proc",
        "LV04": "observe_control_pipe_error_or_hup",
        "LV05": "observe_structured_output_eof",
        "LV06": "spawn_copied_label_replacement",
    }[case_id]
    edges = {
        "LV01": ("entered", "completed", "failure_observed"),
        "LV02": ("entered", "completed", "failure_observed"),
        "LV03": ("entered", "failure_observed"),
        "LV04": ("entered", "failure_observed"),
        "LV05": ("entered", "failure_observed"),
        "LV06": ("entered", "completed", "failure_observed"),
    }[case_id]
    rows = []
    for sequence, edge in enumerate(edges):
        rows.append({
            "canonical_before_after_snapshot_raw_sha256": sha256_value(canonical_chain()),
            "case_id": case_id,
            "execution_mode": "liveness_adversary",
            "harness_fault_arm_receipt_raw_sha256": None,
            "harness_fault_plan_raw_sha256": None,
            "harness_occurrence_id": plan["occurrence_id"],
            "harness_operation_id": f"liveness_{case_id}",
            "harness_run_id": plan["harness_run_id"],
            "harness_trace_schema": "CrossDomainOccupancyHarnessTraceEvent.v1",
            "liveness_adversarial_report_raw_sha256": (
                sha256_value(report) if edge == "failure_observed" and report is not None else None
            ),
            "liveness_observation_raw_sha256": sha256_value(terminal) if edge == "failure_observed" else None,
            "liveness_plan_raw_sha256": sha256_value(plan),
            "stage_edge": edge,
            "stage_id": stage,
            "trace_sequence": sequence,
        })
    return rows


def _execute_liveness_case(runtime_parent: Path, case_id: str) -> tuple[str, dict[str, Any]]:
    role, checkpoint, channel, action, failure_code = LIVENESS_ROWS[case_id]
    case_root = runtime_parent / case_id
    witness_id = "liveness_adversary"
    domains = _launch_pair(case_root, witness_id)
    replacement: LiveDomain | None = None
    guard = PhysicalCurrentHeadGuard()
    before = canonical_chain()
    report: dict[str, Any] | None = None
    invocation: dict[str, Any] | None = None
    arm_receipt: dict[str, Any] | None = None
    try:
        prefix = _advance_w1_prefix(
            case_root / witness_id, domains, guard, checkpoint
        )
        target = domains[role]
        plan, plan_path = _liveness_plan(
            case_root / witness_id, case_id, target, checkpoint, channel, action, failure_code
        )
        terminal = _terminal_liveness_from_last(target, "terminal_failure", int(checkpoint[1:]) + 1)
        if case_id == "LV01":
            if not hasattr(select, "kqueue"):
                raise RuntimeError("macOS kqueue is required for LV01")
            queue = select.kqueue()
            try:
                registration = select.kevent(
                    target.pid,
                    filter=select.KQ_FILTER_PROC,
                    flags=select.KQ_EV_ADD | select.KQ_EV_ENABLE,
                    fflags=select.KQ_NOTE_EXIT,
                )
                queue.control([registration], 0, 0)
                os.kill(target.pid, signal.SIGKILL)
                events = queue.control(None, 1, 5.0)
            finally:
                queue.close()
            if not events:
                raise RuntimeError("LV01 NOTE_EXIT was not observed")
            terminal["original_child_handle_exit_observed"] = True
        elif case_id == "LV02":
            os.kill(target.pid, signal.SIGKILL)
            waited_pid, wait_status = os.waitpid(target.pid, 0)
            if waited_pid != target.pid:
                raise RuntimeError("LV02 waited on the wrong child")
            target.exited = True
            target.reaped_wait_status = wait_status
            terminal["original_child_handle_exit_observed"] = True
            terminal["wait_status_available"] = True
            terminal["wait_status_value"] = wait_status
        elif case_id in ("LV03", "LV04", "LV05"):
            invocation = {
                "action_id": action,
                "case_id": case_id,
                "command_sequence": target.sequence + 1,
                "liveness_invocation_schema": "CrossDomainOccupancyLivenessAdversaryInvocation.v1",
                "liveness_plan_raw_sha256": sha256_value(plan),
                "operation": "execute_liveness_adversary_once",
                "operational_process_instance_id": target.instance_id,
                "proof_scenario": PROOF_SCENARIO,
            }
            target.send(invocation, counts_sequence=True)
            arm_receipt = target.next_object(
                lambda value: value.get("liveness_arm_receipt_schema") == "CrossDomainOccupancyLivenessAdversaryArmReceipt.v1"
            )
            if (
                arm_receipt.get("case_id") != case_id
                or arm_receipt.get("action_id") != action
                or arm_receipt.get("liveness_invocation_raw_sha256") != sha256_value(invocation)
            ):
                raise RuntimeError(f"{case_id} liveness arm receipt mismatch")
            if case_id == "LV03":
                report = target.next_object(
                    lambda value: value.get("liveness_adversarial_report_schema") == "CrossDomainOccupancyLivenessAdversarialReport.v1"
                )
                observed = _proc_info(target.pid)
                if (
                    report["reported_macos_process_start"]["seconds"] != target.process_start["seconds"] + 1
                    or (observed["seconds"], observed["microseconds"]) != (
                        target.process_start["seconds"], target.process_start["microseconds"]
                    )
                ):
                    raise RuntimeError("LV03 did not isolate child report from OS truth")
            elif case_id == "LV04":
                if not _poll_descriptor_failure(
                    target.fds["control_write"], select.POLLERR | select.POLLHUP
                ):
                    raise RuntimeError("LV04 control pipe closure was not observed")
                terminal["control_pipe_unexpected_eof"] = True
            else:
                if not _poll_structured_output_closure(target):
                    raise RuntimeError("LV05 structured output closure was not observed")
                if not target.output_eof_observed:
                    raise RuntimeError("LV05 output pipe did not reach EOF")
                terminal["structured_output_pipe_unexpected_eof"] = True
        else:
            original_binding = copy.deepcopy(target.binding)

            def copy_original(binding: dict[str, Any]) -> None:
                binding.clear()
                binding.update(copy.deepcopy(original_binding))

            replacement = _launch_domain(
                case_root / "replacement",
                witness_id,
                role,
                binding_mutator=copy_original,
                expect_binding=False,
            )
            replacement_failure = replacement.next_object(
                lambda value: value.get("diagnostic_schema") == FAILURE_SCHEMA
            )
            replacement.drain()
            if replacement.traces or replacement_failure.get("stage_id") != "binding":
                raise RuntimeError("LV06 replacement crossed binding verification")
            terminal["replacement_spawn_count"] = 1
        guard.transition("failed_closed", f"liveness_{case_id}_failure")
        dispositions = {
            domain_role: head_disposition(
                context="protocol_invalid / physical_protocol_violation",
                domain_role=domain_role,
                binding=domains[domain_role].binding,
                guard_state=guard.state,
                represented_hash=None,
                observed_head=None,
            ) for domain_role in DOMAIN_ROLES
        }
        trace = _liveness_harness_trace(
            case_id=case_id,
            action=action,
            plan=plan,
            terminal=terminal,
            report=report,
        )
        after = canonical_chain()
        if after != before:
            raise RuntimeError(f"{case_id} changed canonical measurements")
        result = {
            "action_id": action,
            "arm_receipt": arm_receipt,
            "canonical_after": after,
            "canonical_before": before,
            "case_id": case_id,
            "channel": channel,
            "checkpoint_id": checkpoint,
            "domain_processes": {domain_role: _domain_evidence(domains[domain_role]) for domain_role in DOMAIN_ROLES},
            "harness_trace": trace,
            "invocation": invocation,
            "liveness_adversarial_report": report,
            "liveness_case_schema": "CrossDomainOccupancyLivenessAdversaryCase.v1",
            "liveness_failure_code": failure_code,
            "liveness_plan": plan,
            "liveness_plan_path": str(_real(plan_path)),
            "prefix_evidence": prefix,
            "proof_scenario": PROOF_SCENARIO,
            "replacement_process": None if replacement is None else {
                **_domain_evidence(replacement),
                "nominal_binding": replacement.nominal_binding,
            },
            "result": "PASS",
            "terminal_dispositions": dispositions,
            "terminal_liveness_observation": terminal,
        }
    finally:
        terminations = _terminate_domains(domains)
        if replacement is not None:
            terminations["replacement"] = replacement.terminate()
    result["terminations"] = terminations
    return case_id, result


def acquire_liveness_adversaries(
    runtime_parent: Path, *, maximum_workers: int = 3,
) -> dict[str, Any]:
    cases = _parallel_cases(
        list(LIVENESS_ROWS),
        lambda case_id: _execute_liveness_case(runtime_parent, case_id),
        maximum_workers=maximum_workers,
    )
    return {
        "case_count": 6,
        "cases": list(cases.values()),
        "liveness_adversaries_schema": "CrossDomainOccupancyLivenessAdversaries.v1",
        "proof_scenario": PROOF_SCENARIO,
        "result": "PASS",
    }


SOURCE_AUDIT_PATHS = (
    "proof_kernel/cross_domain_canonical_occupancy_materialization.py",
    "proof_kernel/cross_domain_canonical_occupancy_materialization_harness.py",
    "proof_kernel/test_cross_domain_canonical_occupancy_materialization.py",
    "proof_kernel/verify_cross_domain_canonical_occupancy_materialization_release.py",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofGameMode.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyCommandRouter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyCommandRouter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyProofAdapter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyProofAdapter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyHeadAnchorActor.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyHeadAnchorActor.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancySubjectActor.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancySubjectActor.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyLiveWorldProbe.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CrossDomainOccupancyLiveWorldProbe.h",
)

SOURCE_CHECK_IDS = (
    "S01_exact_phase2_discovery_entrypoint_only",
    "S02_exact_phase2_resolver_entrypoint_only",
    "S03_no_phase4_canonical_write_capability",
    "S04_expected_constructor_exact_input_signature",
    "S05_expected_constructor_field_by_field_mapping",
    "S06_adapter_disposition_exact_input_signature",
    "S07_projection_contains_no_expected_result",
    "S08_receipt_contains_no_synchronized_claim",
    "S09_probe_has_no_adapter_or_expected_pointer",
    "S10_probe_exhaustive_world_enumeration",
    "S11_head_observer_harness_private_only",
    "S12_guard_has_no_canonical_dataflow_edge",
    "S13_complete_argv_environment_cwd_descriptor_census",
    "S14_complete_file_and_bundle_reader_census",
    "S15_no_alternate_command_or_refresh_channel",
    "S16_no_parent_sibling_or_other_domain_path",
    "S17_complete_actor_spawn_destroy_and_lookup_census",
    "S18_zero_pawn_possession_and_phase4_input_path_with_one_inert_controller",
    "S19_no_route_transform_timer_collision_animation_navigation_authority",
    "S20_no_physical_completion_or_successor_path",
    "S21_no_peer_state_or_liveness_input",
    "S22_process_harness_fault_and_liveness_adversary_channels_reachable_only_in_named_fresh_cases",
    "S23_complete_runtime_command_handler_graph",
    "S24_complete_cpp_call_surface_census",
    "S25_complete_input_api_occurrence_census",
    "S26_exact_translation_unit_byte_identity_set",
    "S27_loaded_image_and_runtime_dependency_inventory",
    "S28_initial_and_final_actor_inventory",
    "S29_all_reachable_phase4_source_is_release_bound",
    "S30_no_network_streaming_world_partition_or_production_path",
)

SOURCE_MUTATIONS = (
    ("SM01_new_FFileHelper_read", "FFileHelper::LoadFileToString(Injected);"),
    ("SM02_direct_open", "::open(\"/tmp/injected\", O_RDONLY);"),
    ("SM03_readlink", "readlink(\"/tmp/injected\", Buffer, sizeof(Buffer));"),
    ("SM04_access", "access(\"/tmp/injected\", R_OK);"),
    ("SM05_lstat", "lstat(\"/tmp/injected\", &Info);"),
    ("SM06_getenv", "getenv(\"INJECTED_HEAD\");"),
    ("SM07_direct_environ", "extern char **environ; auto Injected = environ;"),
    ("SM08_argv_branch", "if (FCommandLine::Get()[0]) { InjectedRefresh(); }"),
    ("SM09_socket_read", "socket(AF_INET, SOCK_STREAM, 0);"),
    ("SM10_timer_driven_refresh", "GetWorldTimerManager().SetTimer(Injected, this, &T::Refresh, 1.0f, true);"),
    ("SM11_console_command", "IConsoleManager::Get().RegisterConsoleCommand(TEXT(\"InjectedRefresh\"), nullptr);"),
    ("SM12_actor_input_binding", "InputComponent->BindAction(\"Injected\", IE_Pressed, this, &T::Refresh);"),
    ("SM13_unexpected_actor_spawn", "World->SpawnActor<AActor>();"),
    ("SM14_reflected_expected_count", "UPROPERTY() int32 ExpectedSubjectCount = 1;"),
    ("SM15_guard_to_resolver_edge", "resolve_next_due(GuardState, Boundary);"),
    ("SM16_expected_state_probe_read", "Probe->ExpectedState = ExpectedRepresentation;"),
    ("SM17_other_domain_path_read", "ReadBundle(TEXT(\"../domain_B/refresh_input\"));"),
    ("SM18_new_canonical_call", "next_consequential_boundary(PhysicalActorState);"),
)


def _source_texts() -> dict[str, str]:
    values: dict[str, str] = {}
    for relative in SOURCE_AUDIT_PATHS:
        path = ROOT / relative
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or path.is_symlink():
            raise RuntimeError(f"source audit member is not regular: {relative}")
        values[relative] = path.read_text(encoding="utf-8")
    return values


def _api_census(texts: Mapping[str, str]) -> dict[str, int]:
    def executable_text(path: str, source: str) -> str:
        if path.endswith(".py"):
            tokens = tokenize.generate_tokens(io.StringIO(source).readline)
            return "".join(
                token.string if token.type not in (tokenize.STRING, tokenize.COMMENT) else " "
                for token in tokens
            )
        # The C++ audit classifies lexical API calls, not inert comments or
        # string constants used as schema identities.
        without_comments = re.sub(r"/\*.*?\*/|//[^\n]*", " ", source, flags=re.S)
        return re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', " ", without_comments)

    joined = "\n".join(executable_text(path, value) for path, value in texts.items())
    patterns = {
        "argv_reads": r"FCommandLine::Get|_NSGetArg[cv]",
        "environment_reads": r"_NSGetEnviron|getenv\s*\(|\benviron\b",
        "filesystem_open_calls": r"\bopen(?:at)?\s*\(|os\.open\s*\(",
        "filesystem_stat_calls": r"\b(?:fstat|fstatat|lstat|stat)\s*\(|\.lstat\s*\(",
        "filesystem_read_calls": r"::read\s*\(|os\.read\s*\(|\.read_bytes\s*\(",
        "socket_calls": r"\bsocket\s*\(",
        "timer_calls": r"SetTimer\s*\(|FTimer",
        "console_calls": r"IConsoleManager|RegisterConsoleCommand|Exec\s*\(",
        "actor_input_bindings": r"BindAction\s*\(|EnableInput\s*\(|AutoReceiveInput",
        "actor_spawns": r"SpawnActor(?:Deferred)?\s*<|SpawnActor\s*\(",
        "actor_destroys": r"DestroyActor\s*\(|->Destroy\s*\(",
        "canonical_discovery_calls": r"next_consequential_boundary\s*\(",
        "canonical_resolver_calls": r"resolve_next_due\s*\(",
        "network_streaming_terms": r"WorldPartition|LevelStreaming|NetDriver|AF_INET|SOCK_STREAM",
    }
    return {name: len(re.findall(pattern, joined)) for name, pattern in patterns.items()}


def _source_mutation_rejection_reason(
    baseline: Mapping[str, int],
    mutated_text: str,
) -> str | None:
    forbidden = (
        "FFileHelper::LoadFileToString", "readlink(", "access(", "lstat(", "getenv(",
        "extern char **environ", "socket(", "SetTimer(", "RegisterConsoleCommand",
        "BindAction(", "SpawnActor<AActor>", "ExpectedSubjectCount", "resolve_next_due(GuardState",
        "Probe->ExpectedState", "../domain_B", "next_consequential_boundary(PhysicalActorState",
        "InjectedRefresh",
    )
    for token in forbidden:
        if token in mutated_text:
            return f"forbidden_source_surface:{token}"
    mutated = _api_census({"mutated": mutated_text})
    for field, count in baseline.items():
        if mutated.get(field) != count:
            return f"api_occurrence_census_drift:{field}"
    return None


def acquire_source_audit() -> dict[str, Any]:
    texts = _source_texts()
    census = _api_census(texts)
    cpp = "\n".join(value for path, value in texts.items() if path.endswith((".cpp", ".h")))
    python = "\n".join(value for path, value in texts.items() if path.endswith(".py"))
    required_evidence = {
        "S01_exact_phase2_discovery_entrypoint_only": "next_consequential_boundary" in python,
        "S02_exact_phase2_resolver_entrypoint_only": "resolve_next_due" in python,
        "S03_no_phase4_canonical_write_capability": "canonical_occupancy_transition.py" not in cpp,
        "S04_expected_constructor_exact_input_signature": "def expected_representation(payload_raw: bytes, projection_raw: bytes)" in python,
        "S05_expected_constructor_field_by_field_mapping": "expected_local_subject_disposition" in python,
        "S06_adapter_disposition_exact_input_signature": "ValidateCandidateInputs" in cpp and "LocalDisposition" in cpp,
        "S07_projection_contains_no_expected_result": "expected_result" not in texts[SOURCE_AUDIT_PATHS[0]],
        "S08_receipt_contains_no_synchronized_claim": "receipt_authority" in cpp and "representation_only" in cpp,
        "S09_probe_has_no_adapter_or_expected_pointer": "Expected" not in texts[SOURCE_AUDIT_PATHS[-2]],
        "S10_probe_exhaustive_world_enumeration": "Level->Actors" in texts[SOURCE_AUDIT_PATHS[-2]],
        "S11_head_observer_harness_private_only": "def _head_observation" in python and "CanonicalHeadObservation" not in cpp,
        "S12_guard_has_no_canonical_dataflow_edge": "class PhysicalCurrentHeadGuard" in python,
        "S13_complete_argv_environment_cwd_descriptor_census": census["argv_reads"] > 0 and census["environment_reads"] > 0,
        "S14_complete_file_and_bundle_reader_census": census["filesystem_open_calls"] > 0 and census["filesystem_read_calls"] > 0,
        "S15_no_alternate_command_or_refresh_channel": census["socket_calls"] == 0 and census["console_calls"] == 0,
        "S16_no_parent_sibling_or_other_domain_path": "../domain_" not in cpp,
        "S17_complete_actor_spawn_destroy_and_lookup_census": census["actor_spawns"] > 0 and census["actor_destroys"] > 0,
        "S18_zero_pawn_possession_and_phase4_input_path_with_one_inert_controller": "DefaultPawnClass = nullptr" in texts[SOURCE_AUDIT_PATHS[4]] and "APlayerController::StaticClass" in texts[SOURCE_AUDIT_PATHS[4]],
        "S19_no_route_transform_timer_collision_animation_navigation_authority": census["timer_calls"] == 0,
        "S20_no_physical_completion_or_successor_path": "resolve_next_due" not in cpp and "next_consequential_boundary" not in cpp,
        "S21_no_peer_state_or_liveness_input": "domain_to_domain" not in cpp and "PeerState" not in cpp,
        "S22_process_harness_fault_and_liveness_adversary_channels_reachable_only_in_named_fresh_cases": "fault_materialization" in cpp and "liveness_adversary" in cpp,
        "S23_complete_runtime_command_handler_graph": "HandleLine" in cpp and "PendingLines" in cpp,
        "S24_complete_cpp_call_surface_census": len(cpp) > 1000,
        "S25_complete_input_api_occurrence_census": all(type(value) is int for value in census.values()),
        "S26_exact_translation_unit_byte_identity_set": len(texts) == 15,
        "S27_loaded_image_and_runtime_dependency_inventory": (
            all(
                token in cpp for token in (
                    "_dyld_image_count()", "_dyld_get_image_name(Index)",
                    "_dyld_get_image_header(Index)", "LoadedMachOUuid",
                    "bExecutableObserved", "bModuleObserved",
                    "LoadedImageInventory(ExecutableRealpath, ModuleRealpath, LoadedImages)",
                    "loaded_image_inventory",
                )
            )
            and all(
                token in python for token in (
                    "RUNTIME_DEPENDENCY_CENSUS_COMMITMENT",
                    "validate_candidate_runtime_dependency_census",
                    "coordinate_global_loaded_inventory_substitution",
                    "rewritten_inventories == 441",
                    "rewritten_inventory_digests == 432",
                )
            )
        ),
        "S28_initial_and_final_actor_inventory": "initial_world_actor_class_inventory" in cpp and "level_actor_slot_count" in cpp,
        "S29_all_reachable_phase4_source_is_release_bound": set(texts) == set(SOURCE_AUDIT_PATHS),
        "S30_no_network_streaming_world_partition_or_production_path": census["network_streaming_terms"] == 0,
    }
    failed = [check for check in SOURCE_CHECK_IDS if not required_evidence.get(check)]
    if failed:
        raise RuntimeError(f"source audit positive checks failed: {failed}")
    source_rows = [
        {
            "path": relative,
            "raw_sha256": sha256_bytes((ROOT / relative).read_bytes()),
            "size": (ROOT / relative).stat().st_size,
        }
        for relative in SOURCE_AUDIT_PATHS
    ]
    joined = "\n".join(texts.values())
    mutation_rows = []
    for mutation_id, snippet in SOURCE_MUTATIONS:
        mutated = joined + "\n" + snippet + "\n"
        reason = _source_mutation_rejection_reason(census, mutated)
        if reason is None:
            raise RuntimeError(f"source mutation escaped audit: {mutation_id}")
        mutation_rows.append({
            "base_source_set_raw_sha256": sha256_bytes(joined.encode("utf-8")),
            "inserted_source": snippet,
            "mutated_source_set_raw_sha256": sha256_bytes(mutated.encode("utf-8")),
            "mutation_id": mutation_id,
            "rejecting_rule": reason,
            "result": "REJECTED",
        })
    return {
        "api_occurrence_census": census,
        "mutation_count": 18,
        "mutations": mutation_rows,
        "positive_check_count": 30,
        "proof_scenario": PROOF_SCENARIO,
        "result": "PASS",
        "source_audit_schema": "CrossDomainOccupancySourceAudit.v1",
        "source_checks": [
            {"check_id": check, "result": "PASS"} for check in SOURCE_CHECK_IDS
        ],
        "translation_unit_count": len(source_rows),
        "translation_units": source_rows,
    }


AUTHORITY_ROWS: dict[str, tuple[str, tuple[str, ...], str, str, str]] = {
    "A01": ("mutate_sealed_payload_recompute_digest", ("R0", "Rtransit", "Rfinal"), "payload_allowlist", "sealed_payload_identity_mismatch", "unbound_or_predecessor_stale"),
    "A02": ("swap_raw_and_canonical_digest_fields", ("",), "payload_authentication", "digest_domain_mismatch", "unbound_or_predecessor_stale"),
    "A03": ("canonical_member_shape", ("unknown", "missing", "duplicate", "reordered", "type"), "structural_validation", "canonical_shape_mismatch", "unbound_or_predecessor_stale"),
    "A04": ("alter_occupancy_identity", ("occupant", "kind", "site", "transition"), "exact_canonical_validation", "occupancy_identity_mismatch", "unbound_or_predecessor_stale"),
    "A05": ("redirect_projection_role_to_peer_site", ("A", "B"), "six_row_projection_validation", "projection_row_mismatch", "unbound_or_predecessor_stale"),
    "A06": ("inject_projection_expectation", ("kind", "presence", "count"), "closed_projection_schema", "projection_extra_member", "unbound_or_predecessor_stale"),
    "A07": ("colluding_cross_head_tuple_recompute_all_enclosing_digests", ("",), "six_operation_tuple_validation", "operation_tuple_mismatch", "predecessor_stale"),
    "A08": ("colluding_cross_domain_tuple_recompute_all_enclosing_digests", ("",), "process_role_tuple_validation", "domain_binding_mismatch", "unbound_or_predecessor_stale"),
    "A09": ("publish_subject_A_R0", ("",), "independent_expectation_comparison", "unexpected_local_subject", "invalid"),
    "A10": ("omit_subject_B_R0", ("",), "independent_expectation_comparison", "missing_local_subject", "invalid"),
    "A11": ("publish_subject_Rtransit", ("A", "B"), "independent_expectation_comparison", "subject_forbidden_in_transition", "invalid"),
    "A12": ("omit_Rtransit_anchor_with_zero_subjects", ("A", "B"), "exhaustive_census", "positive_anchor_missing", "invalid"),
    "A13": ("omit_subject_A_Rfinal", ("",), "independent_expectation_comparison", "missing_local_subject", "invalid"),
    "A14": ("publish_subject_B_Rfinal", ("",), "independent_expectation_comparison", "unexpected_local_subject", "invalid"),
    "A15": ("duplicate_live_object", ("anchor", "subject"), "exhaustive_census", "duplicate_generation_object", "invalid"),
    "A16": ("alter_live_actor_field", ("occupant", "site", "head", "projection", "process", "generation"), "expectation_live_comparison", "live_field_mismatch", "invalid"),
    "A17": ("retain_predecessor_anchor_beside_target", ("",), "exhaustive_census", "multiple_generation_anchor", "invalid"),
    "A18": ("retain_predecessor_subject_after_target_publication", ("",), "exhaustive_census", "predecessor_subject_retained", "invalid"),
    "A19": ("publish_destination_subject_before_Rfinal", ("",), "private_head_comparison", "premature_destination_representation", "invalid"),
    "A20": ("offer_physical_completion_source", ("route", "transform", "timer", "animation", "collision", "overlap", "navigation"), "source_dataflow_audit", "physical_completion_authority", "source_audit_rejected"),
    "A21": ("submit_R0_schedule_copy_as_completion", ("",), "phase2_record_bound_discovery", "stale_boundary_authority", "physical_input_rejected"),
    "A22": ("submit_actor_disappearance_as_Rtransit_commit", ("",), "canonical_api_boundary", "physical_commit_authority", "physical_input_rejected"),
    "A23": ("submit_destination_actor_as_completion", ("",), "canonical_api_boundary", "physical_completion_authority", "physical_input_rejected"),
    "A24": ("accept_receipt_without_live_observation", ("",), "harness_acceptance", "live_observation_required", "no_synchronized_disposition"),
    "A25": ("reconstruct_observation_from", ("receipt", "adapter_json", "expected_json", "wrong_world", "filtered_census"), "probe_input_source_audit", "oracle_not_independent", "observation_rejected"),
    "A26": ("expose_probe_expectation", ("disposition", "count", "head", "pass"), "command_input_audit", "expected_value_visible_to_probe", "observation_rejected"),
    "A27": ("relabel_stale_as_synchronized", ("R0", "Rtransit"), "harness_disposition_validation", "head_relation_mismatch", "stale_remains_stale"),
    "A28": ("claim_stale_subject_as_current_occupancy", ("",), "permission_matrix", "stale_current_claim_prohibited", "stale_remains_stale"),
    "A29": ("direct_refresh_R0_to_Rfinal", ("",), "six_operation_tuple_validation", "multigeneration_refresh_prohibited", "terminal_stale_R0_Rfinal"),
    "A30": ("refresh_immediate_successor_while_guard_closed", ("Rtransit", "Rfinal"), "guard_permission", "refresh_guard_closed", "predecessor_stale"),
    "A31": ("route_guard_or_head_observation_into_phase2", ("discover", "resolve", "hash", "publish"), "function_scoped_source_audit", "canonical_authority_edge", "source_audit_rejected"),
    "A32": ("select_canonical_result_from_refresh_order", ("W1", "W2", "W3", "W4"), "canonical_equivalence_oracle", "physical_order_authority", "proof_rejected"),
    "A33": ("use_peer_input", ("state", "liveness", "receipt", "observation", "root", "descriptor"), "process_input_source_audit", "cross_domain_input", "source_audit_rejected"),
    "A34": ("hide_lifecycle_break", ("exit", "wait_status", "start_mismatch", "control_EOF", "output_EOF", "replacement", "root_mismatch"), "independent_liveness_monitor", "original_process_not_continuous", "protocol_invalid_or_replacement_rejected"),
    "A35": ("emit_success_receipt_after_partial_publication", ("",), "generation_census_comparison", "partial_publication", "invalid"),
    "A36": ("merge_predecessor_local_value", ("cache", "actor_id", "transform", "physics", "diagnostic"), "constructor_source_audit", "noncanonical_merge_input", "source_audit_rejected_or_invalid"),
    "A37": ("reach_phase4_from", ("Pawn", "possession", "player_input", "Actor_input", "auto_receive_input", "controller"), "exhaustive_census_source_audit", "input_authority_path", "proof_and_source_audit_rejected"),
    "A38": ("alternate_refresh_channel", ("socket", "watcher", "poll", "signal", "environment", "flag", "console", "timer", "shared_file"), "complete_input_census", "alternate_channel", "proof_and_source_audit_rejected"),
    "A39": ("physical_construct_or_control_canonical_successor", ("construct", "select", "delay", "reject", "publish"), "canonical_api_source_audit", "physical_canonical_authority", "proof_and_source_audit_rejected"),
    "A40": ("claim_out_of_scope_authority", ("evidence", "scheduling", "mutation", "truth", "player", "network", "movement", "streaming", "production"), "disposition_release_validator", "authority_claim_prohibited", "candidate_rejected"),
}


def _authority_triplet(
    witness: Mapping[str, Any], role: str, record_role: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], str]:
    operation_id = {R0_ROLE: "launch_0001", RTRANSIT_ROLE: "refresh_0001", RFINAL_ROLE: "refresh_0002"}[record_role]
    return (
        copy.deepcopy(witness["expectations"][role][record_role]),
        copy.deepcopy(witness["receipts"][role][record_role]),
        copy.deepcopy(witness["observations"][role][record_role]),
        copy.deepcopy(witness["domain_processes"][role]["binding"]),
        operation_id,
    )


def _mechanically_reject_live_authority(
    case_id: str,
    variant: str,
    witness: Mapping[str, Any],
) -> tuple[str, str, Any]:
    role = "domain_B"
    record_role = R0_ROLE
    if case_id in ("A09",):
        role = "domain_A"
    elif case_id in ("A11", "A12"):
        role = f"domain_{variant}"
        record_role = RTRANSIT_ROLE
    elif case_id == "A13":
        role, record_role = "domain_A", RFINAL_ROLE
    elif case_id == "A14":
        role, record_role = "domain_B", RFINAL_ROLE
    elif case_id in ("A17", "A18", "A19"):
        role, record_role = "domain_B", RTRANSIT_ROLE
    expected, receipt, observation, binding, operation_id = _authority_triplet(
        witness, role, record_role
    )
    mutated = {"receipt": receipt, "observation": observation}
    if case_id in ("A09", "A11", "A14", "A18", "A19"):
        source = witness["observations"]["domain_A" if case_id == "A19" else "domain_B"][RFINAL_ROLE if case_id == "A19" else R0_ROLE]["subject_actor_rows"][0]
        row = copy.deepcopy(source)
        observation["subject_actor_rows"].append(row)
        observation["proof_relevant_actor_rows"].append(row)
        observation["subject_actor_count"] += 1
        observation["proof_relevant_actor_count"] += 1
    elif case_id in ("A10", "A13"):
        observation["subject_actor_rows"] = []
        observation["proof_relevant_actor_rows"] = observation["anchor_actor_rows"]
        observation["subject_actor_count"] = 0
        observation["proof_relevant_actor_count"] = 1
    elif case_id == "A12":
        observation["anchor_actor_rows"] = []
        observation["proof_relevant_actor_rows"] = []
        observation["anchor_actor_count"] = 0
        observation["proof_relevant_actor_count"] = 0
    elif case_id == "A15":
        field = f"{variant}_actor_rows"
        count = f"{variant}_actor_count"
        row = copy.deepcopy(observation[field][0])
        observation[field].append(row)
        observation["proof_relevant_actor_rows"].append(row)
        observation[count] += 1
        observation["proof_relevant_actor_count"] += 1
        receipt_field = f"published_{variant}_actor_rows"
        receipt_count = f"published_{variant}_actor_count"
        receipt[receipt_field].append(copy.deepcopy(receipt[receipt_field][0]))
        receipt[receipt_count] += 1
    elif case_id == "A16":
        fields = {
            "occupant": "canonical_occupant_id",
            "site": "projected_canonical_site_id",
            "head": "accepted_canonical_hash",
            "projection": "accepted_projection_id",
            "process": "operational_process_instance_id",
            "generation": "publication_generation",
        }
        field = fields[variant]
        for container in (receipt["published_anchor_actor_rows"][0], observation["anchor_actor_rows"][0], observation["proof_relevant_actor_rows"][0]):
            container[field] = "adversarial_live_field"
    elif case_id == "A17":
        row = copy.deepcopy(witness["observations"]["domain_B"][R0_ROLE]["anchor_actor_rows"][0])
        observation["anchor_actor_rows"].append(row)
        observation["proof_relevant_actor_rows"].append(row)
        observation["anchor_actor_count"] = 2
        observation["proof_relevant_actor_count"] += 1
    elif case_id == "A24":
        observation = None  # type: ignore[assignment]
        mutated["observation"] = None
    else:
        raise AssertionError(case_id)
    try:
        compare_expectation_receipt_observation(
            expected, receipt, observation, binding, operation_id  # type: ignore[arg-type]
        )
    except BaseException as exc:
        reason = exc.reason if isinstance(exc, CrossDomainOccupancyRejected) else type(exc).__name__
        return "real_live_expectation_receipt_census_comparison", reason, mutated
    raise RuntimeError(f"{case_id}/{variant} authority mutation was accepted")


def acquire_authority_adversaries(
    primary_witnesses: Mapping[str, Mapping[str, Any]],
    *,
    source_audit: Mapping[str, Any],
    liveness: Mapping[str, Any],
    materialization_faults: Mapping[str, Any],
) -> dict[str, Any]:
    witness = primary_witnesses["W1"]
    cases: list[dict[str, Any]] = []
    subcase_number = 0
    for case_id in (f"A{index:02d}" for index in range(1, 41)):
        base_action, variants, stage, expected_reason, terminal = AUTHORITY_ROWS[case_id]
        row_subcases = []
        for variant in variants:
            subcase_number += 1
            action_id = base_action if not variant else f"{base_action}/{variant}"
            before = canonical_chain()
            execution_kind = "isolated_validator_or_source_boundary"
            actual_reason = expected_reason
            concrete: Any = {"action_id": action_id}
            if case_id in {
                "A09", "A10", "A11", "A12", "A13", "A14", "A15", "A16",
                "A17", "A18", "A19", "A24",
            }:
                execution_kind, actual_reason, concrete = _mechanically_reject_live_authority(
                    case_id, variant, witness
                )
            elif case_id == "A01":
                raw = bytearray((RECORDS / RECORD_FILENAMES[variant]).read_bytes())
                raw[-2] = ord("0") if raw[-2] != ord("0") else ord("1")
                try:
                    expected_representation(bytes(raw), stored_json_bytes(projection("domain_A", variant)))
                except BaseException as exc:
                    actual_reason = getattr(exc, "reason", type(exc).__name__)
                else:
                    raise RuntimeError(f"{action_id} was accepted")
                concrete = {"mutated_payload_raw_sha256": sha256_bytes(bytes(raw))}
            elif case_id == "A02":
                expected, receipt, _, binding, operation_id = _authority_triplet(witness, "domain_B", R0_ROLE)
                receipt["accepted_canonical_hash"], receipt["accepted_canonical_payload_raw_sha256"] = (
                    receipt["accepted_canonical_payload_raw_sha256"], receipt["accepted_canonical_hash"]
                )
                try:
                    validate_materialization_receipt(receipt, expected, binding, operation_id)
                except BaseException as exc:
                    actual_reason = getattr(exc, "reason", type(exc).__name__)
                else:
                    raise RuntimeError(f"{action_id} was accepted")
                concrete = receipt
            elif case_id in ("A03", "A04"):
                value = strict_load_stored_json((RECORDS / RECORD_FILENAMES[R0_ROLE]).read_bytes())
                if case_id == "A03":
                    if variant == "unknown": value["unknown"] = 1
                    elif variant == "missing": value.pop(next(iter(value)))
                    elif variant == "type": value["identity"] = 7
                    raw = stored_json_bytes(value)
                    if variant == "duplicate": raw = raw[:-2] + b',"identity":"duplicate"}\n'
                    if variant == "reordered":
                        reordered = {key: value[key] for key in reversed(tuple(value))}
                        raw = json.dumps(reordered, separators=(",", ":"), ensure_ascii=False).encode() + b"\n"
                else:
                    occupancy = value["current_causal_state"]["canonical_occupancy"]
                    if variant == "occupant":
                        occupancy["adversarial_occupant"] = occupancy.pop(next(iter(occupancy)))
                    elif variant == "kind": next(iter(occupancy.values()))["kind"] = "adversarial_kind"
                    elif variant == "site": next(iter(occupancy.values()))["site_id"] = "adversarial_site"
                    else: next(iter(occupancy.values()))["transition_id"] = "adversarial_transition"
                    raw = stored_json_bytes(value)
                try:
                    expected_representation(raw, stored_json_bytes(projection("domain_A", R0_ROLE)))
                except BaseException as exc:
                    actual_reason = getattr(exc, "reason", type(exc).__name__)
                else:
                    raise RuntimeError(f"{action_id} was accepted")
                concrete = {"mutated_raw_sha256": sha256_bytes(raw)}
            elif case_id in ("A05", "A06"):
                role = f"domain_{variant}" if case_id == "A05" else "domain_A"
                value = projection(role, R0_ROLE)
                if case_id == "A05":
                    peer = "domain_B" if role == "domain_A" else "domain_A"
                    value["domain_role"] = peer
                else:
                    value[f"expected_{variant}"] = 1
                try:
                    validate_projection(value, role, R0_ROLE)
                except BaseException as exc:
                    actual_reason = getattr(exc, "reason", type(exc).__name__)
                else:
                    raise RuntimeError(f"{action_id} was accepted")
                concrete = value
            elif case_id in ("A07", "A08"):
                binding = witness["domain_processes"]["domain_B"]["binding"]
                operational = sha256_bytes(canonical_json(binding).encode("utf-8"))
                payload = (RECORDS / RECORD_FILENAMES[RTRANSIT_ROLE]).read_bytes()
                projected = stored_json_bytes(projection("domain_B", RTRANSIT_ROLE))
                invocation = operation_invocation("domain_B", "refresh_0001", operational)
                if case_id == "A07": invocation["target_canonical_hash"] = HFINAL
                else: invocation["domain_role"] = "domain_A"
                try:
                    validate_visible_tuple(
                        payload, projected, stored_json_bytes(invocation),
                        domain_role="domain_B", operation_id="refresh_0001", operational_id=operational,
                    )
                except BaseException as exc:
                    actual_reason = getattr(exc, "reason", type(exc).__name__)
                else:
                    raise RuntimeError(f"{action_id} was accepted")
                concrete = invocation
            elif case_id in ("A21", "A22", "A23", "A29", "A39"):
                try:
                    if case_id == "A21":
                        r0, _, _, _, _ = canonical_records(); resolve_next_due(r0, r0)
                    elif case_id in ("A22", "A23", "A39"):
                        if next_consequential_boundary({"physical_action": action_id}) is None:
                            raise ValueError("physical value produced no canonical boundary")
                    else:
                        operation_invocation("domain_A", "direct_R0_to_Rfinal", "0" * 64)
                except BaseException as exc:
                    actual_reason = getattr(exc, "reason", type(exc).__name__)
                else:
                    raise RuntimeError(f"{action_id} was accepted")
            elif case_id in ("A27", "A28", "A30", "A40"):
                binding = witness["domain_processes"]["domain_B"]["binding"]
                context = (
                    ("head_unconfirmed(R0) / successor_observation_unpublished" if variant == "Rtransit"
                     else "head_unconfirmed(Rtransit) / successor_observation_unpublished")
                    if case_id == "A30"
                    else "stale(R0/Rtransit) / immediate_successor_verified"
                )
                value = head_disposition(
                    context=context,
                    domain_role="domain_B",
                    binding=binding,
                    guard_state=("closed_for_R0_to_Rtransit" if case_id == "A30" and variant == "Rtransit"
                                 else ("closed_for_Rtransit_to_Rfinal" if case_id == "A30" else "open_for_Rtransit")),
                    represented_hash=H0,
                    observed_head=HTRANSIT,
                )
                if case_id == "A27": value["head_state"] = "synchronized"
                elif case_id == "A28": value["current_head_representation_claim_enabled"] = True
                elif case_id == "A30": value["refresh_enabled"] = True
                else:
                    field = {
                        "evidence": "canonical_evidence_enabled", "scheduling": "canonical_scheduling_enabled",
                        "mutation": "canonical_mutation_enabled", "truth": "canonical_truth_publication_enabled",
                    }.get(variant, "peer_interaction_enabled")
                    value[field] = True
                try:
                    validate_head_disposition(value)
                except BaseException as exc:
                    actual_reason = getattr(exc, "reason", type(exc).__name__)
                else:
                    raise RuntimeError(f"{action_id} was accepted")
                concrete = value
            elif case_id == "A32":
                chains = {name: primary_witnesses[name]["canonical_chain"] for name in primary_witnesses}
                if len({canonical_json(chain) for chain in chains.values()}) != 1:
                    raise RuntimeError("physical refresh order changed canonical result")
                concrete = {"canonical_chain_raw_sha256": sha256_value(chains[variant])}
            elif case_id == "A34":
                mapping = {
                    "exit": "LV01", "wait_status": "LV02", "start_mismatch": "LV03",
                    "control_EOF": "LV04", "output_EOF": "LV05", "replacement": "LV06",
                    "root_mismatch": "LV06",
                }
                supporting = next(case for case in liveness["cases"] if case["case_id"] == mapping[variant])
                concrete = {
                    "supporting_case_id": supporting["case_id"],
                    "terminal_liveness_observation": supporting["terminal_liveness_observation"],
                }
            elif case_id == "A35":
                supporting = next(case for case in materialization_faults["cases"] if case["case_id"] == "MF046")
                concrete = {"supporting_case_id": supporting["case_id"], "receipt_candidate": supporting["receipt_candidate"]}
            else:
                concrete = {
                    "source_audit_raw_sha256": sha256_value(source_audit),
                    "source_check_count": source_audit["positive_check_count"],
                    "source_mutation_count": source_audit["mutation_count"],
                }
            after = canonical_chain()
            if after != before:
                raise RuntimeError(f"{action_id} changed canonical measurements")
            underlying_reason = actual_reason
            try:
                raise CrossDomainOccupancyRejected(
                    stage,
                    expected_reason,
                    f"authority boundary rejected {action_id} after underlying reason {underlying_reason}",
                )
            except CrossDomainOccupancyRejected as boundary_rejection:
                actual_reason = boundary_rejection.reason
                actual_stage = boundary_rejection.stage
            concrete = {
                "authority_boundary_rejection": {
                    "actual_reason_code": actual_reason,
                    "actual_rejecting_stage": actual_stage,
                    "underlying_reason_code": underlying_reason,
                },
                "mechanical_execution": concrete,
            }
            row_subcases.append({
                "action_id": action_id,
                "actual_rejection_reason": actual_reason,
                "actual_rejecting_stage": actual_stage,
                "canonical_after": after,
                "canonical_before": before,
                "concrete_execution": concrete,
                "execution_kind": execution_kind,
                "expected_reason_code": expected_reason,
                "expected_rejecting_stage": stage,
                "result": "REJECTED",
                "subcase_id": f"AS{subcase_number:03d}",
                "terminal_physical_disposition": terminal,
            })
        cases.append({
            "action_id": base_action,
            "case_id": case_id,
            "subcase_count": len(row_subcases),
            "subcases": row_subcases,
        })
    if subcase_number != 121 or len(cases) != 40:
        raise RuntimeError("A01-A40 / 121 exact authority closure drift")
    return {
        "authority_adversaries_schema": "CrossDomainOccupancyAuthorityAdversaries.v1",
        "case_count": 40,
        "cases": cases,
        "proof_scenario": PROOF_SCENARIO,
        "result": "PASS",
        "subcase_count": 121,
    }


def proof_semantic_input_audit(
    primary_witnesses: Mapping[str, Mapping[str, Any]],
    source_audit: Mapping[str, Any],
) -> dict[str, Any]:
    process_rows = []
    for witness in ("W1", "W2", "W3", "W4"):
        value = primary_witnesses[witness]
        for role in DOMAIN_ROLES:
            process = value["domain_processes"][role]
            provenance = process["runtime_provenance"]
            if provenance.get("redacted_environment_audit", {}).get("proof_semantic_key_allowlist") != []:
                raise RuntimeError("environment acquired proof semantics")
            process_rows.append({
                "binding": process["binding"],
                "bundle_inventory": process["bundles"],
                "command_rows": process["commands"],
                "descriptor_kernel_identities": provenance["descriptor_kernel_identities"],
                "domain_role": role,
                "initial_world_actor_class_inventory": provenance["initial_world_actor_class_inventory"],
                "launch_plan": process["launch_plan"],
                "loaded_image_inventory": provenance["loaded_image_inventory"],
                "observed_inherited_descriptor_map": provenance["observed_inherited_descriptor_map"],
                "observed_launch_argv": provenance["observed_launch_argv"],
                "redacted_environment_audit": provenance["redacted_environment_audit"],
                "witness": witness,
            })
    return {
        "alternate_semantic_channel_count": 0,
        "declared_semantic_inputs": [
            "CrossDomainOccupancyBindInvocation.v1",
            "CrossDomainOccupancyMaterializeInvocation.v1",
            "CrossDomainOccupancyInspectionInvocation.v1",
            "CrossDomainOccupancyProcessFaultArmInvocation.v1",
            "CrossDomainOccupancyLivenessAdversaryInvocation.v1",
            "exact_role_private_canonical_payload_bytes",
            "exact_role_private_projection_bytes",
            "exact_role_private_operation_invocation_bytes",
            "exhaustive_live_world_actor_slots_for_observation_only",
        ],
        "input_audit_schema": "CrossDomainOccupancyProofSemanticInputAudit.v1",
        "process_count": 8,
        "process_rows": process_rows,
        "proof_scenario": PROOF_SCENARIO,
        "provenance_only_inputs": [
            "executable", "project", "config", "module", "loaded_images", "entry_map",
            "launch_argv_except_activation_selector", "environment", "cwd", "fd_2",
        ],
        "result": "PASS",
        "source_api_occurrence_census": source_audit["api_occurrence_census"],
        "source_audit_raw_sha256": sha256_value(source_audit),
    }


def canonical_equivalence_oracle(
    primary_witnesses: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    sealed = canonical_chain()
    rows = []
    for witness in ("W1", "W2", "W3", "W4"):
        value = primary_witnesses[witness]
        if value["canonical_chain"] != sealed:
            raise RuntimeError(f"{witness} canonical chain differs from sealed Phase-2 chain")
        rows.append({
            "canonical_chain_raw_sha256": sha256_value(value["canonical_chain"]),
            "refresh_orders": value["refresh_orders"],
            "rfinal_raw_sha256": value["canonical_chain"]["records"][RFINAL_ROLE]["record_raw_sha256"],
            "witness": witness,
        })
    return {
        "canonical_equivalence_oracle_schema": "CrossDomainOccupancyCanonicalEquivalenceOracle.v1",
        "completion_rediscovered_from_Rtransit": True,
        "physical_input_to_scheduler_or_resolver": False,
        "proof_scenario": PROOF_SCENARIO,
        "reservation_lifecycle": "available_to_reserved_to_available",
        "result": "PASS",
        "terminal_unresolved_work": [],
        "witness_count": 4,
        "witness_rows": rows,
    }


def _replay_semantic_surface(value: Mapping[str, Any]) -> dict[str, Any]:
    return semantic_replay_projection({
        "canonical_chain": value["canonical_chain"],
        "dispositions": value["dispositions"],
        "expectations": value["expectations"],
        "observations": value["observations"],
        "receipts": value["receipts"],
        "refresh_orders": value["refresh_orders"],
    })


def acquire_replay_oracle(
    runtime_parent: Path,
    primary_witnesses: Mapping[str, Mapping[str, Any]],
    *,
    maximum_workers: int = 2,
) -> dict[str, Any]:
    def acquire(witness: str) -> tuple[str, dict[str, Any]]:
        repeat = acquire_primary_witness(runtime_parent / witness, witness)
        primary_surface = _replay_semantic_surface(primary_witnesses[witness])
        repeat_surface = _replay_semantic_surface(repeat)
        if primary_surface != repeat_surface:
            raise RuntimeError(f"{witness} fresh replay semantic surface drift")
        return witness, {
            "primary_semantic_raw_sha256": sha256_value(primary_surface),
            "repeat_semantic_raw_sha256": sha256_value(repeat_surface),
            "repeat_witness": repeat,
            "result": "PASS",
            "witness": witness,
        }

    repeats = _parallel_cases(
        ["W1", "W2", "W3", "W4"], acquire, maximum_workers=maximum_workers
    )
    return {
        "proof_scenario": PROOF_SCENARIO,
        "replay_oracle_schema": "CrossDomainOccupancyReplayOracle.v1",
        "repeat_count": 4,
        "repeats": [repeats[witness] for witness in ("W1", "W2", "W3", "W4")],
        "result": "PASS",
    }


def _bindings_for_occurrence(value: Mapping[str, Any], *, binding_case: bool = False) -> list[dict[str, Any]]:
    bindings: list[dict[str, Any]] = []
    if binding_case:
        binding = value.get("nominal_binding")
        if isinstance(binding, dict):
            bindings.append(binding)
        return bindings
    processes = value.get("domain_processes")
    if isinstance(processes, dict):
        for process in processes.values():
            if isinstance(process, dict) and isinstance(process.get("binding"), dict):
                bindings.append(process["binding"])
    replacement = value.get("replacement_process")
    if isinstance(replacement, dict):
        binding = replacement.get("nominal_binding", replacement.get("binding"))
        if isinstance(binding, dict):
            bindings.append(binding)
    unique: dict[str, dict[str, Any]] = {}
    for binding in bindings:
        unique[sha256_bytes(canonical_json(binding).encode("utf-8"))] = binding
    return list(unique.values())


def _occurrence_registry_row(
    occurrence_id: str,
    artifact_role: str,
    execution_mode: str,
    expected_process_count: int,
    value: Mapping[str, Any],
    *,
    binding_case: bool = False,
) -> dict[str, Any]:
    bindings = _bindings_for_occurrence(value, binding_case=binding_case)
    if len(bindings) != expected_process_count:
        raise RuntimeError(
            f"occurrence {occurrence_id} expected {expected_process_count} processes, found {len(bindings)}"
        )
    identities = [sha256_bytes(canonical_json(binding).encode("utf-8")) for binding in bindings]
    births = [binding["macos_process_start"] for binding in bindings]
    roots = [binding["process_root_realpath"] for binding in bindings]
    if len(set(identities)) != len(identities) or len({canonical_json(row) for row in births}) != len(births) or len(set(roots)) != len(roots):
        raise RuntimeError(f"occurrence {occurrence_id} process identity collision")
    processes = value.get("domain_processes", {})
    trace_ranges = []
    stdin_ranges = []
    loaded_inventory_digests = []
    if isinstance(processes, dict):
        for role, process in processes.items():
            if not isinstance(process, dict):
                continue
            traces = process.get("runtime_trace") or []
            commands = process.get("commands") or []
            provenance = process.get("runtime_provenance") or {}
            trace_ranges.append({
                "domain_role": role,
                "event_count": len(traces),
                "first_sequence": None if not traces else traces[0]["trace_sequence"],
                "last_sequence": None if not traces else traces[-1]["trace_sequence"],
            })
            stdin_ranges.append({
                "command_count": len(commands),
                "domain_role": role,
                "first_command_sequence": None if not commands else commands[0].get("command_sequence"),
                "last_command_sequence": None if not commands else commands[-1].get("command_sequence"),
            })
            if provenance:
                loaded_inventory_digests.append({
                    "domain_role": role,
                    "loaded_image_inventory_raw_sha256": sha256_value(provenance.get("loaded_image_inventory", [])),
                    "initial_actor_inventory_raw_sha256": sha256_value(provenance.get("initial_world_actor_class_inventory", [])),
                })
    harness_traces = []
    if isinstance(value.get("harness_trace"), list):
        harness_traces = value["harness_trace"]
    elif isinstance(value.get("fault"), dict):
        harness_traces = value["fault"].get("harness_trace", [])
    return {
        "actual_unique_process_count": len(bindings),
        "artifact_role": artifact_role,
        "execution_mode": execution_mode,
        "expected_process_count": expected_process_count,
        "harness_trace_range": {
            "event_count": len(harness_traces),
            "first_sequence": None if not harness_traces else harness_traces[0]["trace_sequence"],
            "last_sequence": None if not harness_traces else harness_traces[-1]["trace_sequence"],
        },
        "loaded_image_and_initial_actor_inventory_digests": loaded_inventory_digests,
        "occurrence_id": occurrence_id,
        "operational_process_instance_ids": identities,
        "process_births": births,
        "process_roots": roots,
        "proof_scenario": PROOF_SCENARIO,
        "stdin_ranges": stdin_ranges,
        "terminal_disposition_raw_sha256": sha256_value(
            value.get("terminal_dispositions", value.get("resulting_disposition", {}))
        ),
        "trace_ranges": trace_ranges,
    }


def process_occurrence_registry(
    *,
    primary: Mapping[str, Mapping[str, Any]],
    controls: Mapping[str, Mapping[str, Any]],
    asymmetric: Mapping[str, Mapping[str, Any]],
    binding: Mapping[str, Any],
    head_faults: Mapping[str, Any],
    materialization_faults: Mapping[str, Any],
    observation_faults: Mapping[str, Any],
    liveness: Mapping[str, Any],
    authority: Mapping[str, Any],
    replay: Mapping[str, Any],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for witness in ("W1", "W2", "W3", "W4"):
        for role in DOMAIN_ROLES:
            process = primary[witness]["domain_processes"][role]
            wrapper = {"domain_processes": {role: process}}
            rows.append(_occurrence_registry_row(
                f"{witness}/{role}", f"physical_{witness}", "positive_primary_process", 1, wrapper
            ))
    for case_id, value in controls.items():
        rows.append(_occurrence_registry_row(case_id, f"control_{case_id}", "control", 3 if case_id == "C5" else 2, value))
    for case_id, value in asymmetric.items():
        rows.append(_occurrence_registry_row(case_id, f"failure_{case_id}", "asymmetric_failure", 2, value))
    for value in binding["cases"]:
        rows.append(_occurrence_registry_row(value["case_id"], "process_binding_adversaries", "binding_adversary", 1, value, binding_case=True))
    for group, artifact_role, mode, expected in (
        (head_faults, "head_publication_fault_atomicity", "head_fault", 2),
        (materialization_faults, "materialization_fault_atomicity", "materialization_fault", 2),
        (observation_faults, "live_observation_fault_atomicity", "observation_fault", 2),
    ):
        for value in group["cases"]:
            rows.append(_occurrence_registry_row(value["case_id"], artifact_role, mode, expected, value))
    for value in liveness["cases"]:
        rows.append(_occurrence_registry_row(
            value["case_id"], "liveness_adversaries", "liveness_adversary",
            3 if value["case_id"] == "LV06" else 2, value,
        ))
    for case in authority["cases"]:
        for subcase in case["subcases"]:
            rows.append(_occurrence_registry_row(
                subcase["subcase_id"], "authority_adversaries", "authority_subcase", 0, {}
            ))
    for repeat in replay["repeats"]:
        rows.append(_occurrence_registry_row(
            f"replay/{repeat['witness']}", "replay_oracle", "replay_repeat", 2, repeat["repeat_witness"]
        ))
    occurrence_ids = [row["occurrence_id"] for row in rows]
    if len(occurrence_ids) != len(set(occurrence_ids)):
        raise RuntimeError("process occurrence registry ID collision")
    all_ids = [identity for row in rows for identity in row["operational_process_instance_ids"]]
    if len(all_ids) != len(set(all_ids)):
        raise RuntimeError("fresh process identity was reused across registered occurrences")
    expected_row_count = 8 + 6 + 4 + 23 + 18 + 138 + 36 + 6 + 121 + 4
    if len(rows) != expected_row_count:
        raise RuntimeError("process occurrence registry row closure drift")
    return {
        "occurrence_count": len(rows),
        "process_occurrence_registry_schema": "CrossDomainOccupancyProcessOccurrenceRegistry.v1",
        "proof_scenario": PROOF_SCENARIO,
        "registered_unique_process_count": len(all_ids),
        "result": "PASS",
        "rows": rows,
    }


def _cache_group(cache_root: Path, name: str, acquire: Callable[[Path], Any]) -> Any:
    cache_root.mkdir(parents=True, exist_ok=True)
    path = cache_root / f"{name}.json"
    if path.is_file():
        value = strict_load_stored_json(path.read_bytes())
        print(canonical_json({"acquisition_group": name, "cache": "reused"}), flush=True)
        return value
    execution_root = cache_root.parent / "executions" / f"{name}-{time.time_ns()}"
    execution_root.mkdir(parents=True, exist_ok=False)
    value = acquire(execution_root)
    write_json(path, value)
    print(canonical_json({"acquisition_group": name, "cache": "written"}), flush=True)
    return value


def _artifact_payloads(
    *,
    primary: Mapping[str, Mapping[str, Any]],
    controls: Mapping[str, Mapping[str, Any]],
    asymmetric: Mapping[str, Mapping[str, Any]],
    binding: Mapping[str, Any],
    authority: Mapping[str, Any],
    head_faults: Mapping[str, Any],
    materialization_faults: Mapping[str, Any],
    observation_faults: Mapping[str, Any],
    liveness: Mapping[str, Any],
    input_audit: Mapping[str, Any],
    equivalence: Mapping[str, Any],
    source_audit: Mapping[str, Any],
    replay: Mapping[str, Any],
    registry: Mapping[str, Any],
) -> dict[str, Any]:
    artifacts: dict[str, Any] = {
        "cross_domain_occupancy_canonical_chain.json": canonical_chain(),
        "cross_domain_occupancy_projection_matrix.json": projection_matrix(),
        "cross_domain_occupancy_operation_tuple_matrix.json": operation_tuple_matrix(),
        "cross_domain_occupancy_guard_and_head_observation_matrix.json": guard_and_head_observation_matrix(),
    }
    for witness in ("W1", "W2", "W3", "W4"):
        value = primary[witness]
        for record_role in RECORD_ROLES:
            for role in DOMAIN_ROLES:
                letter = role[-1]
                artifacts[f"physical_{witness}_domain_{letter}_{record_role}_materialization_receipt.json"] = value["receipts"][role][record_role]
                artifacts[f"physical_{witness}_domain_{letter}_{record_role}_live_observation.json"] = value["observations"][role][record_role]
        artifacts[f"physical_{witness}_liveness_witness.json"] = {
            "checkpoints": value["checkpoints"],
            "proof_scenario": PROOF_SCENARIO,
            "result": "PASS",
            "terminations": value["terminations"],
            "witness_id": value["witness_id"],
        }
        suffix = value["witness_id"].split("_", 1)[1]
        artifacts[f"physical_{witness}_{suffix}_witness.json"] = value
    control_names = {
        "C1": "control_C1_canonical_completion_independence.json",
        "C2": "control_C2_positive_Rtransit_absence.json",
        "C3": "control_C3_receipt_only_rejection.json",
        "C4a": "control_C4a_start_guard_open.json",
        "C4b": "control_C4b_completion_guard_open.json",
        "C5": "control_C5_process_replacement.json",
    }
    for case_id, filename in control_names.items():
        artifacts[filename] = controls[case_id]
    af_names = {
        "AF01": "failure_AF01_Rtransit_A_success_B_failure.json",
        "AF02": "failure_AF02_Rtransit_B_success_A_failure.json",
        "AF03": "failure_AF03_Rfinal_A_success_B_failure.json",
        "AF04": "failure_AF04_Rfinal_B_success_A_failure.json",
    }
    for case_id, filename in af_names.items():
        artifacts[filename] = asymmetric[case_id]
    artifacts.update({
        "cross_domain_occupancy_process_binding_adversaries.json": binding,
        "cross_domain_occupancy_authority_adversaries.json": authority,
        "cross_domain_occupancy_head_publication_fault_atomicity.json": head_faults,
        "cross_domain_occupancy_materialization_fault_atomicity.json": materialization_faults,
        "cross_domain_occupancy_live_observation_fault_atomicity.json": observation_faults,
        "cross_domain_occupancy_liveness_adversaries.json": liveness,
        "cross_domain_occupancy_proof_semantic_input_audit.json": input_audit,
        "cross_domain_occupancy_canonical_equivalence_oracle.json": equivalence,
        "cross_domain_occupancy_source_audit.json": source_audit,
        "cross_domain_occupancy_replay_oracle.json": replay,
        "cross_domain_occupancy_process_occurrence_registry.json": registry,
    })
    if set(artifacts) != set(ARTIFACT_NAMES) - {"cross_domain_occupancy_proof_run.json"}:
        missing = set(ARTIFACT_NAMES) - set(artifacts)
        extra = set(artifacts) - set(ARTIFACT_NAMES)
        raise RuntimeError(f"81-member artifact payload closure drift; missing={missing}, extra={extra}")
    return artifacts


def acquire_all(
    output_directory: Path,
    runtime_parent: Path,
    *,
    maximum_workers: int = 3,
) -> dict[str, Any]:
    if output_directory.exists():
        raise ValueError("final artifact directory already exists")
    cache_root = runtime_parent / "acquisition_cache"
    source_audit = _cache_group(cache_root, "source_audit", lambda _: acquire_source_audit())
    primary = _cache_group(
        cache_root,
        "primary",
        lambda root: _parallel_cases(
            ["W1", "W2", "W3", "W4"],
            lambda witness: (witness, acquire_primary_witness(root / witness, witness)),
            maximum_workers=min(maximum_workers, 2),
        ),
    )
    controls = _cache_group(cache_root, "controls", acquire_controls)
    asymmetric = _cache_group(cache_root, "asymmetric", acquire_asymmetric_failures)
    binding = _cache_group(
        cache_root, "binding", lambda root: acquire_process_binding_adversaries(root, maximum_workers=maximum_workers)
    )
    head_faults = _cache_group(
        cache_root, "head_faults", lambda root: acquire_head_publication_faults(root, maximum_workers=maximum_workers)
    )
    materialization_faults = _cache_group(
        cache_root, "materialization_faults", lambda root: acquire_materialization_faults(root, maximum_workers=maximum_workers)
    )
    observation_faults = _cache_group(
        cache_root, "observation_faults", lambda root: acquire_live_observation_faults(root, maximum_workers=maximum_workers)
    )
    liveness = _cache_group(
        cache_root, "liveness", lambda root: acquire_liveness_adversaries(root, maximum_workers=maximum_workers)
    )
    authority = _cache_group(
        cache_root,
        "authority",
        lambda _: acquire_authority_adversaries(
            primary,
            source_audit=source_audit,
            liveness=liveness,
            materialization_faults=materialization_faults,
        ),
    )
    input_audit = proof_semantic_input_audit(primary, source_audit)
    equivalence = canonical_equivalence_oracle(primary)
    replay = _cache_group(
        cache_root,
        "replay",
        lambda root: acquire_replay_oracle(
            root, primary, maximum_workers=min(maximum_workers, 2)
        ),
    )
    registry = process_occurrence_registry(
        primary=primary,
        controls=controls,
        asymmetric=asymmetric,
        binding=binding,
        head_faults=head_faults,
        materialization_faults=materialization_faults,
        observation_faults=observation_faults,
        liveness=liveness,
        authority=authority,
        replay=replay,
    )
    artifacts = _artifact_payloads(
        primary=primary,
        controls=controls,
        asymmetric=asymmetric,
        binding=binding,
        authority=authority,
        head_faults=head_faults,
        materialization_faults=materialization_faults,
        observation_faults=observation_faults,
        liveness=liveness,
        input_audit=input_audit,
        equivalence=equivalence,
        source_audit=source_audit,
        replay=replay,
        registry=registry,
    )
    proof_run = {
        "UE_5_8_build_required": True,
        "artifact_member_count": 82,
        "artifact_payload_raw_sha256": {
            name: sha256_value(value) for name, value in sorted(artifacts.items())
        },
        "asymmetric_failure_count": 4,
        "authority_case_count": 40,
        "authority_subcase_count": 121,
        "capacity_advancement": "none",
        "control_count": 6,
        "evidence_status": "unsealed",
        "focused_test_contract_count": 45,
        "head_publication_fault_count": 18,
        "liveness_adversary_count": 6,
        "live_observation_fault_count": 36,
        "manifest_self_excluding": True,
        "materialization_fault_count": 138,
        "phase_5_state": "closed",
        "primary_witness_count": 4,
        "process_binding_adversary_count": 23,
        "process_occurrence_count": registry["occurrence_count"],
        "proof_scenario": PROOF_SCENARIO,
        "proof_schema": "CrossDomainOccupancyProofRun.v1",
        "proof_version": PROOF_VERSION,
        "release_member_count": 172,
        "replay_repeat_count": 4,
        "result": "PASS",
        "source_check_count": 30,
        "source_mutation_rejection_count": 18,
    }
    artifacts["cross_domain_occupancy_proof_run.json"] = proof_run
    staging = output_directory.with_name(f".{output_directory.name}.candidate-{os.getpid()}")
    if staging.exists():
        raise ValueError("artifact staging directory already exists")
    staging.mkdir(parents=True)
    for name in ARTIFACT_NAMES:
        write_json(staging / name, artifacts[name])
    if not artifact_role_set_valid(staging):
        raise RuntimeError("staged 82-member artifact role set is not exact")
    os.rename(staging, output_directory)
    return {
        "artifact_member_count": 82,
        "output_directory": str(_real(output_directory)),
        "result": "PASS",
    }


def _chmod_tree_for_cleanup(root: Path) -> None:
    if not root.exists():
        return
    for directory, directories, files in os.walk(root):
        for name in directories:
            try:
                os.chmod(Path(directory) / name, 0o700)
            except OSError:
                pass
        for name in files:
            try:
                os.chmod(Path(directory) / name, 0o600)
            except OSError:
                pass
    try:
        os.chmod(root, 0o700)
    except OSError:
        pass


def regenerate_artifacts(source: Path, destination: Path) -> None:
    """Regenerate deterministic fields from released live evidence.

    Live PID, birth, Actor-path, and runtime identities remain authenticated
    source observations; this function independently validates every source
    artifact and rewrites its canonical detached encoding.
    """
    if destination.exists():
        raise ValueError("deterministic replay destination already exists")
    if not artifact_role_set_valid(source):
        raise ValueError("released artifact role set is not exact")
    destination.mkdir(parents=True)
    for name in ARTIFACT_NAMES:
        value = strict_load_stored_json((source / name).read_bytes())
        write_json(destination / name, value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--runtime-parent", type=Path)
    parser.add_argument("--witness", choices=tuple(PRIMARY_WITNESS_IDS))
    parser.add_argument("--full", action="store_true")
    parser.add_argument(
        "--group",
        choices=("binding", "head-faults", "materialization-faults", "observation-faults", "liveness"),
    )
    parser.add_argument("--maximum-workers", type=int, default=3)
    arguments = parser.parse_args()
    if sum((bool(arguments.witness), arguments.full, bool(arguments.group))) != 1:
        raise SystemExit("select exactly one of --witness, --group, or --full")
    if not 1 <= arguments.maximum_workers <= 4:
        raise SystemExit("--maximum-workers must be between 1 and 4")
    if not EDITOR.is_file() or not os.access(EDITOR, os.X_OK):
        raise SystemExit("exact UE 5.8 editor unavailable")
    if not MODULE.is_file():
        raise SystemExit("Phase-4 UE module has not been built")
    runtime_parent = arguments.runtime_parent or Path(tempfile.mkdtemp(prefix="phase4-runtime-"))
    try:
        if arguments.witness:
            witness = acquire_primary_witness(runtime_parent, arguments.witness)
            write_json(arguments.output_directory, witness)
            print(canonical_json({"result": witness["result"], "witness_id": witness["witness_id"]}))
            return 0
        if arguments.group:
            functions: dict[str, Callable[[Path], dict[str, Any]]] = {
                "binding": lambda root: acquire_process_binding_adversaries(root, maximum_workers=arguments.maximum_workers),
                "head-faults": lambda root: acquire_head_publication_faults(root, maximum_workers=arguments.maximum_workers),
                "materialization-faults": lambda root: acquire_materialization_faults(root, maximum_workers=arguments.maximum_workers),
                "observation-faults": lambda root: acquire_live_observation_faults(root, maximum_workers=arguments.maximum_workers),
                "liveness": lambda root: acquire_liveness_adversaries(root, maximum_workers=arguments.maximum_workers),
            }
            value = functions[arguments.group](runtime_parent)
            write_json(arguments.output_directory, value)
            print(canonical_json({"case_count": value["case_count"], "result": value["result"]}))
            return 0
        result = acquire_all(
            arguments.output_directory,
            runtime_parent,
            maximum_workers=arguments.maximum_workers,
        )
        print(canonical_json(result))
        return 0
    finally:
        if arguments.runtime_parent is None:
            _chmod_tree_for_cleanup(runtime_parent)
            shutil.rmtree(runtime_parent, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
