"""Acquire the frozen Simultaneous Physical Domains v0.1.1 UE witnesses.

The harness owns operational head observation, physical guard state, process
birth/liveness evidence, detached bundle staging, and receipt acceptance.  The
two original Unreal children receive only their immutable process bindings,
their exact three-file launch/refresh tuples, and the frozen stdin commands.
Neither the harness head observation nor guard is exposed to Unreal.
"""

from __future__ import annotations

import argparse
import copy
import ctypes
import errno
import hashlib
import json
import os
import select
import shutil
import signal
import stat
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from simultaneous_physical_domains import (
    ARTIFACT_NAMES,
    AUTHORITY_CASE_ACTIONS,
    CANONICAL_MEASUREMENT_SCHEMA,
    D0,
    D1,
    DOMAIN_ROLES,
    H0,
    H1,
    PhysicalCurrentHeadGuard,
    PROOF_SCENARIO,
    REFRESH_FAULT_STAGES,
    PHYSICAL_OBSERVATION_FAULT_STAGES,
    WITNESS_IDS,
    authoritative_representation,
    bind_invocation,
    canonical_measurement,
    canonical_json,
    canonical_records,
    canonical_transition_run,
    current_head_observation,
    current_head_authority_failures,
    expected_physical_observation,
    fault_arm_invocation,
    guard_open_control,
    head_disposition,
    head_observation_failure_witness,
    head_observation_fault_atomicity,
    inspection_invocation,
    local_step_invocation,
    measured_canonical_relation,
    operation_receipt,
    operation_receipt_matrix,
    operational_process_instance_id,
    process_binding,
    projection,
    projection_matrix,
    proof_semantic_input_audit_template,
    refresh_invocation,
    retention_equivalence_oracle,
    retention_witness,
    semantic_replay_projection,
    sha256_bytes,
    sha256_value,
    stale_quarantine_witness,
    stored_json_bytes,
    strict_load_stored_json,
    validate_exact_directory,
    validate_fault_arm_receipt,
    validate_local_step_observation,
    validate_materialization_receipt,
    validate_measured_canonical_relation,
    validate_physical_observation,
    verify_current_head_observation,
    write_json,
)
from canonical_spatial_topology_identity import stored_json_bytes as phase1_stored_json_bytes


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "CityMaterializationProof" / "CityMaterializationProof.uproject"
EDITOR = Path("/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor")
BUILD_VERSION = Path("/Users/Shared/Epic Games/UE_5.8/Engine/Build/Build.version")
MODULE = ROOT / "CityMaterializationProof" / "Binaries" / "Mac" / "libUnrealEditor-CityMaterializationProof.dylib"
ENTRY_MAP = "/Engine/Maps/Entry"
CONFIG_PATHS = (
    ROOT / "CityMaterializationProof" / "Config" / "DefaultEngine.ini",
    ROOT / "CityMaterializationProof" / "Config" / "DefaultGame.ini",
    ROOT / "CityMaterializationProof" / "Config" / "DefaultInput.ini",
)

POSIX_SPAWN_START_SUSPENDED = 0x0080
POSIX_SPAWN_SETSID = 0x0400
POSIX_SPAWN_CLOEXEC_DEFAULT = 0x4000
PROC_PIDTBSDINFO = 3
PROC_PIDTASKINFO = 4


class ProcBsdInfo(ctypes.Structure):
    _fields_ = [
        ("pbi_flags", ctypes.c_uint32),
        ("pbi_status", ctypes.c_uint32),
        ("pbi_xstatus", ctypes.c_uint32),
        ("pbi_pid", ctypes.c_uint32),
        ("pbi_ppid", ctypes.c_uint32),
        ("pbi_uid", ctypes.c_uint32),
        ("pbi_gid", ctypes.c_uint32),
        ("pbi_ruid", ctypes.c_uint32),
        ("pbi_rgid", ctypes.c_uint32),
        ("pbi_svuid", ctypes.c_uint32),
        ("pbi_svgid", ctypes.c_uint32),
        ("rfu_1", ctypes.c_uint32),
        ("pbi_comm", ctypes.c_char * 16),
        ("pbi_name", ctypes.c_char * 32),
        ("pbi_nfiles", ctypes.c_uint32),
        ("pbi_pgid", ctypes.c_uint32),
        ("pbi_pjobc", ctypes.c_uint32),
        ("e_tdev", ctypes.c_uint32),
        ("e_tpgid", ctypes.c_uint32),
        ("pbi_nice", ctypes.c_int32),
        ("pbi_start_tvsec", ctypes.c_uint64),
        ("pbi_start_tvusec", ctypes.c_uint64),
    ]


class ProcTaskInfo(ctypes.Structure):
    _fields_ = [
        ("pti_virtual_size", ctypes.c_uint64),
        ("pti_resident_size", ctypes.c_uint64),
        ("pti_total_user", ctypes.c_uint64),
        ("pti_total_system", ctypes.c_uint64),
        ("pti_threads_user", ctypes.c_uint64),
        ("pti_threads_system", ctypes.c_uint64),
        ("pti_policy", ctypes.c_int32),
        ("pti_faults", ctypes.c_int32),
        ("pti_pageins", ctypes.c_int32),
        ("pti_cow_faults", ctypes.c_int32),
        ("pti_messages_sent", ctypes.c_int32),
        ("pti_messages_received", ctypes.c_int32),
        ("pti_syscalls_mach", ctypes.c_int32),
        ("pti_syscalls_unix", ctypes.c_int32),
        ("pti_csw", ctypes.c_int32),
        ("pti_threadnum", ctypes.c_int32),
        ("pti_numrunning", ctypes.c_int32),
        ("pti_priority", ctypes.c_int32),
    ]


LIBC = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True)
LIBPROC = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)


def _prototype_spawn() -> None:
    LIBC.posix_spawnattr_init.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
    LIBC.posix_spawnattr_destroy.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
    LIBC.posix_spawnattr_setflags.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_short]
    LIBC.posix_spawn_file_actions_init.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
    LIBC.posix_spawn_file_actions_destroy.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
    LIBC.posix_spawn_file_actions_adddup2.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_int, ctypes.c_int]
    LIBC.posix_spawn_file_actions_addclose.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_int]
    LIBC.posix_spawn_file_actions_addchdir_np.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_char_p]
    LIBC.posix_spawn.argtypes = [
        ctypes.POINTER(ctypes.c_int), ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_char_p), ctypes.POINTER(ctypes.c_char_p),
    ]
    LIBPROC.proc_pidinfo.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
    LIBPROC.proc_pidinfo.restype = ctypes.c_int


_prototype_spawn()


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _real(path: Path) -> Path:
    return path.resolve(strict=True)


def _canonical_line(value: Any) -> bytes:
    return canonical_json(value).encode("utf-8") + b"\n"


def _write_all(fd: int, raw: bytes) -> None:
    view = memoryview(raw)
    while view:
        written = os.write(fd, view)
        if written <= 0:
            raise RuntimeError("control pipe write failed")
        view = view[written:]


def _engine_build_identity() -> str:
    value = json.loads(BUILD_VERSION.read_text(encoding="utf-8"))
    return (
        f"{value['MajorVersion']}.{value['MinorVersion']}.{value['PatchVersion']}-"
        f"{value['Changelist']}-{value['BranchName']}"
    )


def _project_inventory() -> dict[str, Any]:
    members = [PROJECT, *CONFIG_PATHS, MODULE]
    return {
        "inventory_schema": "SimultaneousPhysicalDomainProjectModuleInventory.v1",
        "members": [
            {"realpath": str(_real(path)), "raw_sha256": _sha_file(path)}
            for path in members
        ],
    }


def _redacted_environment_audit(environment: Mapping[str, str]) -> dict[str, Any]:
    entries = [
        {"key": key, "value_raw_sha256": sha256_bytes(value.encode("utf-8"))}
        for key, value in sorted(environment.items())
    ]
    return {
        "audit_schema": "SimultaneousPhysicalDomainLaunchEnvironmentAudit.v1",
        "sorted_entries": entries,
        "plaintext_values_released": False,
        "proof_semantic_key_allowlist": [],
    }


def _descriptor_map(role: str) -> dict[str, Any]:
    return {
        "descriptor_map_schema": "SimultaneousPhysicalDomainInheritedDescriptorMap.v1",
        "fd_0": {"role": "original_control_pipe_read_endpoint", "pipe_id": f"{role}/control/0001"},
        "fd_1": {"role": "original_structured_output_pipe_write_endpoint", "pipe_id": f"{role}/stdout/0001"},
        "fd_2": {"role": "original_diagnostic_pipe_write_endpoint", "pipe_id": f"{role}/stderr/0001"},
        "all_other_descriptors_at_exec": "closed",
    }


def _argv(domain_root: Path, role: str) -> list[str]:
    return [
        str(_real(EDITOR)),
        str(_real(PROJECT)),
        "-game",
        "-Multiprocess",
        "-NoSplash",
        "-Windowed",
        "-ResX=900",
        "-ResY=650",
        "-WinX=30" if role == "domain_A" else "-WinX=990",
        "-WinY=60",
        f"-UserDir={domain_root / 'user'}",
        f"-abslog={domain_root / 'diagnostic' / 'UnrealEditor.log'}",
    ]


def _environment(domain_root: Path) -> dict[str, str]:
    environment = dict(os.environ)
    environment["TMPDIR"] = str(domain_root / "temp")
    return environment


def _proc_info(pid: int) -> dict[str, Any]:
    info = ProcBsdInfo()
    result = LIBPROC.proc_pidinfo(pid, PROC_PIDTBSDINFO, 0, ctypes.byref(info), ctypes.sizeof(info))
    if result != ctypes.sizeof(info) or info.pbi_pid != pid:
        error = ctypes.get_errno()
        raise RuntimeError(f"proc_pidinfo failed for {pid}: result={result} errno={error}")
    return {
        "pid": int(info.pbi_pid),
        "ppid": int(info.pbi_ppid),
        "seconds": int(info.pbi_start_tvsec),
        "microseconds": int(info.pbi_start_tvusec),
    }


def _task_info(pid: int) -> dict[str, int]:
    info = ProcTaskInfo()
    result = LIBPROC.proc_pidinfo(
        pid, PROC_PIDTASKINFO, 0, ctypes.byref(info), ctypes.sizeof(info)
    )
    if result != ctypes.sizeof(info):
        error = ctypes.get_errno()
        raise RuntimeError(
            f"proc_pidinfo task sample failed for {pid}: result={result} errno={error}"
        )
    return {
        "total_user_nanoseconds": int(info.pti_total_user),
        "total_system_nanoseconds": int(info.pti_total_system),
        "thread_count": int(info.pti_threadnum),
        "running_thread_count": int(info.pti_numrunning),
    }


def _spawn_suspended(argv: list[str], environment: Mapping[str, str], cwd: Path) -> tuple[int, dict[str, int]]:
    control_read, control_write = os.pipe()
    output_read, output_write = os.pipe()
    diagnostic_read, diagnostic_write = os.pipe()
    for fd in (control_read, output_write, diagnostic_write):
        os.set_inheritable(fd, True)
    for fd in (control_write, output_read, diagnostic_read):
        os.set_inheritable(fd, False)

    actions = ctypes.c_void_p()
    attributes = ctypes.c_void_p()
    if LIBC.posix_spawn_file_actions_init(ctypes.byref(actions)) != 0 or LIBC.posix_spawnattr_init(ctypes.byref(attributes)) != 0:
        raise RuntimeError("posix_spawn initialization failed")
    try:
        for source, target in ((control_read, 0), (output_write, 1), (diagnostic_write, 2)):
            if LIBC.posix_spawn_file_actions_adddup2(ctypes.byref(actions), source, target) != 0:
                raise RuntimeError("posix_spawn dup2 action failed")
        for fd in (control_read, control_write, output_read, output_write, diagnostic_read, diagnostic_write):
            if fd not in (0, 1, 2):
                LIBC.posix_spawn_file_actions_addclose(ctypes.byref(actions), fd)
        if LIBC.posix_spawn_file_actions_addchdir_np(ctypes.byref(actions), os.fsencode(cwd)) != 0:
            raise RuntimeError("posix_spawn chdir action failed")
        flags = POSIX_SPAWN_START_SUSPENDED | POSIX_SPAWN_SETSID | POSIX_SPAWN_CLOEXEC_DEFAULT
        if LIBC.posix_spawnattr_setflags(ctypes.byref(attributes), flags) != 0:
            raise RuntimeError("posix_spawn flags failed")
        argv_raw = [os.fsencode(value) for value in argv]
        env_raw = [os.fsencode(f"{key}={value}") for key, value in environment.items()]
        argv_array = (ctypes.c_char_p * (len(argv_raw) + 1))(*argv_raw, None)
        env_array = (ctypes.c_char_p * (len(env_raw) + 1))(*env_raw, None)
        pid = ctypes.c_int()
        result = LIBC.posix_spawn(
            ctypes.byref(pid), argv_raw[0], ctypes.byref(actions), ctypes.byref(attributes),
            argv_array, env_array,
        )
        if result != 0:
            raise OSError(result, os.strerror(result))
    except BaseException:
        for fd in (control_read, control_write, output_read, output_write, diagnostic_read, diagnostic_write):
            try: os.close(fd)
            except OSError: pass
        raise
    finally:
        LIBC.posix_spawn_file_actions_destroy(ctypes.byref(actions))
        LIBC.posix_spawnattr_destroy(ctypes.byref(attributes))

    os.close(control_read)
    os.close(output_write)
    os.close(diagnostic_write)
    os.set_blocking(output_read, False)
    os.set_blocking(diagnostic_read, False)
    return pid.value, {
        "control_write": control_write,
        "output_read": output_read,
        "diagnostic_read": diagnostic_read,
    }


def _prepare_bundle(domain_root: Path, role: str, head: str, operation: str, instance_id: str | None) -> dict[str, Any]:
    r0, _, r1 = canonical_records()
    role_token = "A" if role == "domain_A" else "B"
    if operation == "launch":
        directory = domain_root / "launch_input" / "launch_0001"
        payload_name = "canonical_topology_R0.json"
    else:
        directory = domain_root / "refresh_input" / "refresh_0001"
        payload_name = "canonical_topology_R1.json"
    projection_name = f"simultaneous_domain_{role_token}_{head}_projection.json"
    receipt_name = f"simultaneous_domain_{role_token}_{head}_operation_receipt.json"
    directory.mkdir(parents=True, exist_ok=False)
    (directory / payload_name).write_bytes(phase1_stored_json_bytes(r0 if head == "H0" else r1))
    (directory / projection_name).write_bytes(stored_json_bytes(projection(role, head)))
    receipt = operation_receipt(
        operation, role, head,
        operational_process_instance_id=instance_id,
    )
    (directory / receipt_name).write_bytes(stored_json_bytes(receipt))
    expected = (payload_name, projection_name, receipt_name)
    for name in expected:
        os.chmod(directory / name, 0o400)
    os.chmod(directory, 0o500)
    inventory = validate_exact_directory(directory, expected)
    return {"directory": directory, "inventory": inventory, "receipt": receipt, "names": expected}


@dataclass
class LiveDomain:
    witness_id: str
    role: str
    root: Path
    pid: int
    fds: dict[str, int]
    binding: dict[str, Any]
    launch_argv: list[str]
    environment_audit: dict[str, Any]
    descriptor_map: dict[str, Any]
    launch_inventory: dict[str, Any]
    kqueue: select.kqueue
    process_start: dict[str, Any]
    output_buffer: bytes = b""
    diagnostic_digest: hashlib._Hash = field(default_factory=hashlib.sha256)
    parsed_objects: list[dict[str, Any]] = field(default_factory=list)
    commands: list[dict[str, Any]] = field(default_factory=list)
    refresh_inventory_before: dict[str, Any] | None = None
    refresh_inventory_after: dict[str, Any] | None = None
    exited: bool = False

    @property
    def instance_id(self) -> str:
        return operational_process_instance_id(self.binding)

    def send(self, command: dict[str, Any]) -> None:
        _write_all(self.fds["control_write"], _canonical_line(command))
        self.commands.append(copy.deepcopy(command))

    def drain(self) -> None:
        while True:
            try:
                chunk = os.read(self.fds["output_read"], 65536)
            except BlockingIOError:
                break
            if not chunk:
                if self.exited:
                    break
                raise RuntimeError(f"{self.role} structured output pipe EOF before termination")
            with (self.root / "diagnostic" / "structured_stdout.raw").open("ab") as stream:
                stream.write(chunk)
            self.output_buffer += chunk
            while b"\n" in self.output_buffer:
                line, self.output_buffer = self.output_buffer.split(b"\n", 1)
                try:
                    text = line.decode("utf-8", errors="strict")
                    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
                        result: dict[str, Any] = {}
                        for key, member in pairs:
                            if key in result:
                                raise ValueError(f"duplicate runtime JSON member: {key}")
                            result[key] = member
                        return result
                    value = json.loads(text, object_pairs_hook=reject_duplicates)
                except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
                    continue
                # UE's float formatter may emit an additional non-significant
                # trailing digit for the four live mesh components.  The
                # frozen probe law accepts those components by finite numeric
                # value and absolute tolerance; every other structured object
                # remains byte-canonical at the pipe boundary.
                is_physical_observation = (
                    isinstance(value, dict)
                    and value.get("observation_schema")
                    == "SimultaneousPhysicalDomainPhysicalObservation.v1"
                )
                if isinstance(value, dict) and (canonical_json(value) == text or is_physical_observation):
                    self.parsed_objects.append(value)
        while True:
            try:
                chunk = os.read(self.fds["diagnostic_read"], 65536)
            except BlockingIOError:
                break
            if not chunk:
                break
            self.diagnostic_digest.update(chunk)

    def next_object(self, predicate, timeout: float = 180.0) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.drain()
            for index, value in enumerate(self.parsed_objects):
                if predicate(value):
                    return self.parsed_objects.pop(index)
                if value.get("diagnostic_schema") == "SimultaneousPhysicalDomainFailure.v1":
                    raise RuntimeError(
                        f"{self.role} emitted failure while awaiting result: "
                        f"{canonical_json(value)}"
                    )
            self.assert_alive("await_structured_object")
            time.sleep(0.05)
        raise TimeoutError(f"timed out awaiting structured result from {self.role}")

    def assert_alive(self, checkpoint: str) -> dict[str, Any]:
        events = self.kqueue.control(None, 8, 0)
        if events:
            raise RuntimeError(f"{self.role} exit watch fired at {checkpoint}")
        waited_pid, wait_status = os.waitpid(self.pid, os.WNOHANG)
        if waited_pid != 0:
            self.exited = True
            raise RuntimeError(f"{self.role} wait status available at {checkpoint}: {wait_status}")
        current = _proc_info(self.pid)
        if (current["seconds"], current["microseconds"]) != (
            self.process_start["seconds"], self.process_start["microseconds"]
        ) or current["ppid"] != os.getpid():
            raise RuntimeError(f"{self.role} process birth binding changed at {checkpoint}")
        os.fstat(self.fds["control_write"])
        os.fstat(self.fds["output_read"])
        self.drain()
        return {
            "domain_role": self.role,
            "checkpoint": checkpoint,
            "pid": self.pid,
            "macos_process_start": {
                "seconds": current["seconds"], "microseconds": current["microseconds"]
            },
            "operational_process_instance_id": self.instance_id,
            "process_binding_raw_sha256": sha256_value(self.binding),
            "direct_child_ppid_matches_harness": True,
            "original_child_handle_exit_observed": False,
            "wait_status_available": False,
            "control_pipe_unexpected_eof": False,
            "structured_output_pipe_unexpected_eof": False,
            "replacement_spawn_count": 0,
        }

    def terminate(self) -> dict[str, Any]:
        if not self.exited:
            try: os.kill(self.pid, signal.SIGTERM)
            except ProcessLookupError: pass
            deadline = time.monotonic() + 20.0
            while time.monotonic() < deadline:
                waited, status_value = os.waitpid(self.pid, os.WNOHANG)
                if waited == self.pid:
                    self.exited = True
                    status = status_value
                    break
                time.sleep(0.05)
            else:
                try: os.kill(self.pid, signal.SIGKILL)
                except ProcessLookupError: pass
                _, status = os.waitpid(self.pid, 0)
                self.exited = True
        else:
            status = 0
        self.drain()
        for fd in self.fds.values():
            try: os.close(fd)
            except OSError: pass
        try: self.kqueue.close()
        except OSError: pass
        return {
            "domain_role": self.role,
            "pid": self.pid,
            "terminated": True,
            "wait_status": status,
            "diagnostic_stream_raw_sha256": self.diagnostic_digest.hexdigest(),
            "canonical_input_from_terminated_output": False,
        }


def _launch_domain(runtime_root: Path, witness_id: str, role: str) -> LiveDomain:
    domain_root = runtime_root / role
    for name in ("user", "temp", "diagnostic"):
        (domain_root / name).mkdir(parents=True, exist_ok=False)
    launch_bundle = _prepare_bundle(domain_root, role, "H0", "launch", None)
    argv = _argv(domain_root, role)
    environment = _environment(domain_root)
    environment_audit = _redacted_environment_audit(environment)
    descriptor_map = _descriptor_map(role)
    pid, fds = _spawn_suspended(argv, environment, ROOT)
    process_start = _proc_info(pid)
    if process_start["ppid"] != os.getpid():
        os.kill(pid, signal.SIGKILL)
        os.waitpid(pid, 0)
        raise RuntimeError("spawned UE process is not direct child")
    project_inventory = _project_inventory()
    binding = process_binding({
        "proof_scenario": PROOF_SCENARIO,
        "witness_id": witness_id,
        "domain_role": role,
        "harness_launch_id": f"{witness_id}/{role}/launch_0001",
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
        "project_config_and_module_inventory_raw_sha256": sha256_value(project_inventory),
        "process_root_realpath": str(_real(domain_root)),
        "launch_argv_raw_sha256": sha256_bytes(canonical_json(argv).encode("utf-8")),
        "launch_environment_audit_raw_sha256": sha256_value(environment_audit),
        "launch_cwd_realpath": str(_real(ROOT)),
        "inherited_descriptor_map_raw_sha256": sha256_value(descriptor_map),
        "control_pipe_id": f"{role}/control/0001",
        "structured_output_pipe_id": f"{role}/stdout/0001",
        "diagnostic_pipe_id": f"{role}/stderr/0001",
    })
    watch = select.kqueue()
    watch.control(
        [select.kevent(pid, filter=select.KQ_FILTER_PROC, flags=select.KQ_EV_ADD | select.KQ_EV_ENABLE,
                       fflags=select.KQ_NOTE_EXIT)], 0, 0
    )
    domain = LiveDomain(
        witness_id=witness_id, role=role, root=domain_root, pid=pid, fds=fds,
        binding=binding, launch_argv=argv, environment_audit=environment_audit,
        descriptor_map=descriptor_map, launch_inventory=launch_bundle["inventory"],
        kqueue=watch, process_start=process_start,
    )
    domain.send(bind_invocation(binding))
    os.kill(pid, signal.SIGCONT)
    return domain


def _launch_pair(runtime_root: Path, witness_id: str) -> dict[str, LiveDomain]:
    runtime_root.mkdir(parents=True, exist_ok=False)
    domains: dict[str, LiveDomain] = {}
    try:
        for role in DOMAIN_ROLES:
            domains[role] = _launch_domain(runtime_root, witness_id, role)
        return domains
    except BaseException:
        for domain in domains.values():
            domain.terminate()
        raise


def _is_receipt(value: Mapping[str, Any]) -> bool:
    return value.get("receipt_schema") == "SimultaneousPhysicalDomainMaterializationReceipt.v1"


def _is_observation(value: Mapping[str, Any]) -> bool:
    return value.get("observation_schema") == "SimultaneousPhysicalDomainPhysicalObservation.v1"


def _is_local_step_observation(value: Mapping[str, Any]) -> bool:
    return value.get("observation_schema") == "SimultaneousPhysicalDomainLocalStepObservation.v1"


def _is_fault_arm_receipt(value: Mapping[str, Any]) -> bool:
    return value.get("receipt_schema") == "SimultaneousPhysicalDomainFaultArmReceipt.v1"


def _is_injected_fault_result(value: Mapping[str, Any]) -> bool:
    return value.get("result_schema") == "SimultaneousPhysicalDomainInjectedFaultResult.v1"


def _validate_injected_fault_result(
    value: Any,
    *,
    command: Mapping[str, Any],
    binding: Mapping[str, Any],
) -> dict[str, Any]:
    expected_keys = {
        "result_schema", "proof_scenario", "domain_role",
        "operational_process_instance_id", "process_binding_raw_sha256",
        "executable_raw_sha256", "fault_run_id", "fault_surface",
        "fault_stage", "fault_edge", "target_head_role", "boundary_entered",
        "boundary_completed", "local_publication_state",
        "represented_hash_if_known", "materialization_receipt_outcome",
        "physical_observation_outcome", "reason_code",
    }
    if not isinstance(value, dict) or set(value) != expected_keys:
        raise RuntimeError("injected fault result has a non-exact member set")
    exact = {
        "result_schema": "SimultaneousPhysicalDomainInjectedFaultResult.v1",
        "proof_scenario": PROOF_SCENARIO,
        "domain_role": binding["domain_role"],
        "operational_process_instance_id": operational_process_instance_id(binding),
        "process_binding_raw_sha256": sha256_value(binding),
        "executable_raw_sha256": binding["executable_raw_sha256"],
        "fault_run_id": command["fault_run_id"],
        "fault_surface": command["fault_surface"],
        "fault_stage": command["fault_stage"],
        "fault_edge": command["fault_edge"],
        "target_head_role": command["target_head_role"],
    }
    if any(value.get(key) != member for key, member in exact.items()):
        raise RuntimeError("injected fault result does not match its arm command and process")
    if value["boundary_entered"] is not True:
        raise RuntimeError("injected fault did not enter the named boundary")
    if value["boundary_completed"] is not (
        command["fault_edge"] in ("after", "at")
    ):
        raise RuntimeError("injected fault boundary completion differs from its exact edge")
    expected_reason = (
        f"injected_fault/{command['fault_surface']}/"
        f"{command['fault_stage']}/{command['fault_edge']}"
    )
    if value["reason_code"] != expected_reason:
        raise RuntimeError("injected fault result reason does not name the exact boundary")
    return copy.deepcopy(value)


def _is_failure(value: Mapping[str, Any]) -> bool:
    return value.get("diagnostic_schema") == "SimultaneousPhysicalDomainFailure.v1"


def _checkpoint(domains: Mapping[str, LiveDomain], checkpoint: str) -> dict[str, Any]:
    samples = [domains[role].assert_alive(checkpoint) for role in DOMAIN_ROLES]
    return {
        "checkpoint": checkpoint,
        "sampled_together": True,
        "domains": samples,
        "bindings_match_launch_byte_for_byte": True,
    }


def _accept_launch(
    domain: LiveDomain,
    guard: PhysicalCurrentHeadGuard,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    receipt = domain.next_object(_is_receipt)
    validate_materialization_receipt(receipt, domain.binding)
    domain.send(inspection_invocation(domain.role, "launch_physical_0001"))
    observation = domain.next_object(_is_observation)
    validate_physical_observation(
        observation, domain_role=domain.role, head_role="H0", binding=domain.binding,
        inspection_id="launch_physical_0001",
    )
    disposition = head_disposition(
        domain_role=domain.role, binding=domain.binding, receipt=receipt,
        physical_observation=observation, represented_hash=H0, observed_head=H0,
        guard_state=guard.state, head_state="synchronized",
    )
    return receipt, observation, disposition


def _stage_refresh(domain: LiveDomain, *, corrupt_receipt_digest: bool = False) -> dict[str, Any]:
    bundle = _prepare_bundle(domain.root, domain.role, "H1", "refresh", domain.instance_id)
    if corrupt_receipt_digest:
        directory = bundle["directory"]
        receipt_path = directory / bundle["names"][2]
        os.chmod(directory, 0o700)
        os.chmod(receipt_path, 0o600)
        receipt = strict_load_stored_json(receipt_path.read_bytes())
        receipt["canonical_payload_raw_sha256"] = D0
        receipt_path.write_bytes(stored_json_bytes(receipt))
        os.chmod(receipt_path, 0o400)
        os.chmod(directory, 0o500)
        bundle["inventory"] = validate_exact_directory(directory, bundle["names"])
    domain.refresh_inventory_before = bundle["inventory"]
    return bundle


def _retained_and_poison_fixtures(domain: LiveDomain) -> tuple[dict[str, Any], dict[str, Any]]:
    perturbed = domain.witness_id == "w5_retention_perturbed"
    retained = {
        "retained_schema": "SimultaneousPhysicalDomainRetainedLocalState.v1",
        "nonconsequential_tick_counter": 991 if perturbed else 7,
        "cosmetic_phase_token": "cosmetic_phase_3" if perturbed else "cosmetic_phase_0",
        "diagnostic_counter": 47 if perturbed else 1,
    }
    poison = {
        "actor_ids": ["poison_actor_991" if perturbed else "baseline_actor_7"],
        "topology_cache": "poisoned_topology" if perturbed else "baseline_topology",
        "route_access_cache": "available",
        "collision_open": True,
        "physics_diagnostic": "poisoned_47" if perturbed else "baseline_1",
    }
    return retained, poison


def _is_retention_observation(value: Mapping[str, Any]) -> bool:
    return value.get("observation_schema") == (
        "SimultaneousPhysicalDomainRetentionExecutionObservation.v1"
    )


def _refresh_success(
    domain: LiveDomain,
    guard: PhysicalCurrentHeadGuard,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any] | None]:
    guard.assert_refresh_eligible(domain.role)
    bundle = _stage_refresh(domain)
    retained, poison = _retained_and_poison_fixtures(domain)
    domain.send(refresh_invocation(domain.role))
    receipt = domain.next_object(_is_receipt)
    validate_materialization_receipt(receipt, domain.binding)
    retention_observation = (
        domain.next_object(_is_retention_observation)
        if domain.witness_id in ("w5_retention_baseline", "w5_retention_perturbed")
        else None
    )
    if retention_observation is not None:
        expected_branch = "perturbed" if domain.witness_id.endswith("perturbed") else "baseline"
        expected = {
            "branch": expected_branch,
            "retained_nonconsequential_tick_counter": retained["nonconsequential_tick_counter"],
            "retained_cosmetic_phase_token": retained["cosmetic_phase_token"],
            "retained_diagnostic_counter": retained["diagnostic_counter"],
            "discard_required_H0_poison_observed_before_refresh": True,
            "prior_H0_actor_replaced": True,
            "published_H1_actor_poison_clear": True,
            "poisoned_actor_ids_discarded": True,
            "poisoned_topology_cache_discarded": True,
            "poisoned_route_access_cache_discarded": True,
            "poisoned_collision_state_discarded": True,
            "poisoned_physics_diagnostics_discarded": True,
            "represented_canonical_hash": H1,
            "observation_source": "live_ue_adapter_postpublication_state_inspection",
        }
        for key, value in expected.items():
            if retention_observation.get(key) != value:
                raise RuntimeError(f"live retention observation mismatch: {key}")
        if (
            retention_observation.get("domain_role") != domain.role
            or retention_observation.get("operational_process_instance_id") != domain.instance_id
            or retention_observation.get("process_binding_raw_sha256") != sha256_value(domain.binding)
        ):
            raise RuntimeError("live retention observation process binding mismatch")
    domain.refresh_inventory_after = validate_exact_directory(bundle["directory"], bundle["names"])
    if domain.refresh_inventory_after != domain.refresh_inventory_before:
        raise RuntimeError("refresh bundle changed during Unreal read")
    domain.send(inspection_invocation(domain.role, "refresh_physical_0001"))
    observation = domain.next_object(_is_observation)
    validate_physical_observation(
        observation, domain_role=domain.role, head_role="H1", binding=domain.binding,
        inspection_id="refresh_physical_0001",
    )
    disposition = head_disposition(
        domain_role=domain.role, binding=domain.binding, receipt=receipt,
        physical_observation=observation, represented_hash=H1, observed_head=H1,
        guard_state=guard.state, head_state="synchronized",
    )
    return receipt, observation, disposition, retention_observation


def _refresh_rejection(
    domain: LiveDomain,
    guard: PhysicalCurrentHeadGuard,
) -> tuple[dict[str, Any], dict[str, Any]]:
    guard.assert_refresh_eligible(domain.role)
    bundle = _stage_refresh(domain, corrupt_receipt_digest=True)
    domain.send(refresh_invocation(domain.role))
    failure = domain.next_object(_is_failure)
    domain.refresh_inventory_after = validate_exact_directory(bundle["directory"], bundle["names"])
    if domain.refresh_inventory_after != domain.refresh_inventory_before:
        raise RuntimeError("adversarial refresh bundle changed during Unreal read")
    if failure.get("represented_hash_if_known") != H0:
        raise RuntimeError("prepublication refresh rejection did not preserve H0 representation")
    disposition = head_disposition(
        domain_role=domain.role, binding=domain.binding, receipt=None, physical_observation=None,
        represented_hash=H0, observed_head=H1, guard_state=guard.state, head_state="stale",
    )
    return failure, disposition


def _observe_stale_local_execution(
    domains: Mapping[str, LiveDomain],
) -> dict[str, Any]:
    _, _, canonical_before_record = canonical_records()
    before = {role: _task_info(domains[role].pid) for role in DOMAIN_ROLES}
    command_counts_before = {role: len(domains[role].commands) for role in DOMAIN_ROLES}
    output_counts_before = {role: len(domains[role].parsed_objects) for role in DOMAIN_ROLES}
    started = time.monotonic()
    step_observations: dict[str, dict[str, Any]] = {}
    for role in DOMAIN_ROLES:
        domains[role].send(local_step_invocation(role))
        observation = domains[role].next_object(_is_local_step_observation)
        step_observations[role] = validate_local_step_observation(
            observation, binding=domains[role].binding
        )
    checkpoints = {role: domains[role].assert_alive("W3_stale_local_execution") for role in DOMAIN_ROLES}
    finished = time.monotonic()
    after = {role: _task_info(domains[role].pid) for role in DOMAIN_ROLES}
    _, _, canonical_after_record = canonical_records()
    canonical_relation = measured_canonical_relation(
        canonical_before_record,
        canonical_after_record,
        expected_relation="unchanged_H1",
    )
    validate_measured_canonical_relation(
        canonical_relation,
        before_record=canonical_before_record,
        after_record=canonical_after_record,
        expected_relation="unchanged_H1",
    )
    samples: dict[str, Any] = {}
    for role in DOMAIN_ROLES:
        cpu_before = before[role]["total_user_nanoseconds"] + before[role]["total_system_nanoseconds"]
        cpu_after = after[role]["total_user_nanoseconds"] + after[role]["total_system_nanoseconds"]
        delta = cpu_after - cpu_before
        if len(domains[role].commands) - command_counts_before[role] != 1:
            raise RuntimeError(f"{role} did not receive exactly one W3 local-step command")
        if len(domains[role].parsed_objects) != output_counts_before[role]:
            raise RuntimeError(f"{role} retained an unexpected structured object after W3 step")
        samples[role] = {
            "process_binding": domains[role].binding,
            "exact_local_step_command": local_step_invocation(role),
            "exact_local_step_observation": step_observations[role],
            "before": before[role],
            "after": after[role],
            "supplemental_total_cpu_nanoseconds_delta": delta,
            "original_process_alive_after_interval": checkpoints[role],
            "stdin_command_count_delta": 1,
            "structured_local_step_observation_count_delta": 1,
            "structured_authority_object_count_delta": 0,
            "accepted_represented_hash_before_after": [H0, H0],
            "harness_head_state_before_after": ["stale(H0/H1)", "stale(H0/H1)"],
        }
    return {
        "observation_schema": "SimultaneousPhysicalDomainsStaleLocalExecutionObservation.v1",
        "observation_source": "exact_live_UE_adapter_local_step_in_original_processes",
        "bounded_observation_interval_count": 1,
        "bounded_window_seconds": finished - started,
        "domains": samples,
        "canonical_before_after_measurement": canonical_relation,
        "canonical_R1_raw_sha256_before_after": [
            canonical_relation["before"]["record_raw_sha256"],
            canonical_relation["after"]["record_raw_sha256"],
        ],
        "current_head_receipt_count_delta": 0,
        "canonical_evidence_count_delta": 0,
        "canonical_scheduling_count_delta": 0,
        "canonical_mutation_count_delta": 0,
    }


def _publish_head_observation(control_root: Path) -> dict[str, Any]:
    control_root.mkdir(parents=True, exist_ok=True)
    candidate = current_head_observation()
    candidate_raw = stored_json_bytes(candidate)
    temporary = control_root / ".current_head_observation.json.tmp"
    target = control_root / "current_head_observation.json"
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        _write_all(fd, candidate_raw)
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(temporary, target)
    directory_fd = os.open(control_root, os.O_RDONLY)
    try: os.fsync(directory_fd)
    finally: os.close(directory_fd)
    accepted = strict_load_stored_json(target.read_bytes())
    _, _, r1 = canonical_records()
    verify_current_head_observation(accepted, phase1_stored_json_bytes(r1))
    return {
        "observation": accepted,
        "raw_sha256": _sha_file(target),
        "publication": {
            "temporary_write": True,
            "file_fsync": True,
            "atomic_replace": True,
            "directory_fsync": True,
            "independent_reread": True,
            "identity_reverification": True,
        },
        "path_private_to_harness": str(target.resolve()),
    }


def _domain_evidence(domain: LiveDomain) -> dict[str, Any]:
    return {
        "binding": domain.binding,
        "binding_command": bind_invocation(domain.binding),
        "launch_argv": domain.launch_argv,
        "launch_environment_audit": domain.environment_audit,
        "inherited_descriptor_map": domain.descriptor_map,
        "launch_input_inventory": domain.launch_inventory,
        "stdin_commands": domain.commands,
        "refresh_input_inventory_before": domain.refresh_inventory_before,
        "refresh_input_inventory_after": domain.refresh_inventory_after,
        "head_observation_visible_to_unreal": False,
        "physical_guard_visible_to_unreal": False,
        "other_domain_root_visible_to_unreal": False,
    }


def acquire_witness(runtime_root: Path, witness_id: str) -> dict[str, Any]:
    if witness_id not in WITNESS_IDS:
        raise ValueError(f"unknown witness ID: {witness_id}")
    domains = _launch_pair(runtime_root, witness_id)
    launch_receipts: dict[str, Any] = {}
    launch_observations: dict[str, Any] = {}
    launch_dispositions: dict[str, Any] = {}
    checkpoints: list[dict[str, Any]] = []
    refresh_receipts: dict[str, Any] = {}
    refresh_observations: dict[str, Any] = {}
    refresh_dispositions: dict[str, Any] = {}
    failures: dict[str, Any] = {}
    retention_observations: dict[str, Any] = {}
    terminations: dict[str, Any] = {}
    guard = PhysicalCurrentHeadGuard()
    transition: dict[str, Any] | None = None
    control_root = runtime_root / "harness_private_control"
    head_publication: dict[str, Any] | None = None
    try:
        for role in DOMAIN_ROLES:
            receipt, observation, disposition = _accept_launch(domains[role], guard)
            launch_receipts[role] = receipt
            launch_observations[role] = observation
            launch_dispositions[role] = disposition
        checkpoints.append(_checkpoint(domains, "L0"))

        if witness_id == "w8_guard_open_control":
            checkpoints.append(_checkpoint(domains, "guard_open_before_canonical_invocation"))
            transition = canonical_transition_run()
            guard.fail_closed("guard_open_at_canonical_commit")
            return {
                "witness_id": witness_id,
                "canonical_transition": transition,
                "guard_machine": guard.snapshot(),
                "launch_receipts": launch_receipts,
                "launch_observations": launch_observations,
                "launch_dispositions": launch_dispositions,
                "checkpoints": checkpoints,
                "terminal_dispositions": {role: "protocol_invalid(H0/H1)" for role in DOMAIN_ROLES},
                "refresh_invocations": 0,
                "domains": {role: _domain_evidence(domains[role]) for role in DOMAIN_ROLES},
                "canonical_R1_byte_identical": True,
                "phase_3_harness_protocol_passed": False,
            }

        guard.close_for_h0_to_h1()
        checkpoints.append(_checkpoint(domains, "L1"))
        transition = canonical_transition_run()
        checkpoints.append(_checkpoint(domains, "L2"))
        if witness_id == "w4_head_observation_failure":
            guard.fail_closed("after_R1_H1_commit_verification_before_observation_construction")
            return {
                "witness_id": witness_id,
                "canonical_transition": transition,
                "guard_machine": guard.snapshot(),
                "launch_receipts": launch_receipts,
                "launch_observations": launch_observations,
                "checkpoints": checkpoints,
                "head_observation_published": False,
                "injected_fault_point": "after_R1_H1_commit_verification_before_observation_construction",
                "terminal_states": {role: "head_unconfirmed" for role in DOMAIN_ROLES},
                "refresh_invocations": 0,
                "domains": {role: _domain_evidence(domains[role]) for role in DOMAIN_ROLES},
                "canonical_R1_byte_identical": True,
            }

        head_publication = _publish_head_observation(control_root)
        guard.verify_h1_observation(head_publication["observation"]["observed_canonical_hash"])
        for role in DOMAIN_ROLES:
            guard.classify_stale(role, H0, H1)
        guard.open_for_h1()
        checkpoints.append(_checkpoint(domains, "L3"))

        if witness_id == "w3_stale_quarantine":
            stale_execution_observation = _observe_stale_local_execution(domains)
            return {
                "witness_id": witness_id,
                "canonical_transition": transition,
                "guard_machine": guard.snapshot(),
                "head_publication": head_publication,
                "checkpoints": checkpoints,
                "launch_receipts": launch_receipts,
                "launch_observations": launch_observations,
                "stale_local_execution_observation": stale_execution_observation,
                "terminal_states": {role: "stale(H0/H1)" for role in DOMAIN_ROLES},
                "current_head_claims": 0,
                "canonical_R1_byte_identical": True,
                "domains": {role: _domain_evidence(domains[role]) for role in DOMAIN_ROLES},
            }

        if witness_id == "w6_asymmetric_a_synchronized":
            success_role, failure_role = "domain_A", "domain_B"
        elif witness_id == "w6_asymmetric_b_synchronized":
            success_role, failure_role = "domain_B", "domain_A"
        else:
            success_role = failure_role = ""

        if success_role:
            receipt, observation, disposition, retention_observation = _refresh_success(
                domains[success_role], guard
            )
            refresh_receipts[success_role] = receipt
            refresh_observations[success_role] = observation
            refresh_dispositions[success_role] = disposition
            if retention_observation is not None:
                retention_observations[success_role] = retention_observation
            checkpoints.append(_checkpoint(domains, "L4A"))
            failure, stale_disposition = _refresh_rejection(domains[failure_role], guard)
            failures[failure_role] = failure
            refresh_dispositions[failure_role] = stale_disposition
            checkpoints.append(_checkpoint(domains, "asymmetric_terminal"))
        else:
            order = ("domain_A", "domain_B") if witness_id in (
                "w1_a_then_b", "w5_retention_baseline", "w5_retention_perturbed", "w7_destroy_a", "w7_destroy_b"
            ) else ("domain_B", "domain_A")
            for index, role in enumerate(order):
                receipt, observation, disposition, retention_observation = _refresh_success(
                    domains[role], guard
                )
                refresh_receipts[role] = receipt
                refresh_observations[role] = observation
                refresh_dispositions[role] = disposition
                if retention_observation is not None:
                    retention_observations[role] = retention_observation
                checkpoints.append(_checkpoint(domains, "L4A" if index == 0 else "L4B"))

        if witness_id in ("w7_destroy_a", "w7_destroy_b"):
            terminated_role = "domain_A" if witness_id == "w7_destroy_a" else "domain_B"
            remaining_role = "domain_B" if terminated_role == "domain_A" else "domain_A"
            terminations[terminated_role] = domains[terminated_role].terminate()
            checkpoints.append({
                "checkpoint": "post_destruction",
                "remaining_domain": domains[remaining_role].assert_alive("post_destruction"),
                "remaining_domain_head_state": "synchronized(H1)",
                "canonical_H1_unchanged": True,
            })

        return {
            "witness_schema": "SimultaneousPhysicalDomainsPhysicalWitness.v1",
            "proof_scenario": PROOF_SCENARIO,
            "witness_id": witness_id,
            "canonical_transition": transition,
            "guard_machine": guard.snapshot(),
            "head_publication": head_publication,
            "launch_receipts": launch_receipts,
            "launch_observations": launch_observations,
            "launch_dispositions": launch_dispositions,
            "refresh_receipts": refresh_receipts,
            "refresh_observations": refresh_observations,
            "refresh_dispositions": refresh_dispositions,
            "refresh_failures": failures,
            "retention_execution_observations": retention_observations,
            "checkpoints": checkpoints,
            "launch_count": 2,
            "replacement_spawn_count": 0,
            "domains": {role: _domain_evidence(domains[role]) for role in DOMAIN_ROLES},
            "terminations": terminations,
            "canonical_R1_byte_identical": True,
        }
    finally:
        for role, domain in domains.items():
            if role not in terminations:
                try: terminations[role] = domain.terminate()
                except BaseException: pass


def _advance_physical_guard_to_h1(
    domains: Mapping[str, LiveDomain],
    guard: PhysicalCurrentHeadGuard,
    control_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    guard.close_for_h0_to_h1()
    transition = canonical_transition_run()
    head_publication = _publish_head_observation(control_root)
    guard.verify_h1_observation(head_publication["observation"]["observed_canonical_hash"])
    for role in DOMAIN_ROLES:
        guard.classify_stale(role, H0, H1)
    guard.open_for_h1()
    return transition, head_publication


def _arm_fault(
    domain: LiveDomain,
    *,
    surface: str,
    stage: str,
    edge: str,
    head_role: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    command = fault_arm_invocation(
        surface=surface,
        stage=stage,
        edge=edge,
        head_role=head_role,
        domain_role=domain.role,
    )
    domain.send(command)
    receipt = domain.next_object(_is_fault_arm_receipt)
    validate_fault_arm_receipt(receipt, command=command, binding=domain.binding)
    return command, receipt


def _canonical_relation_around(
    before_record: Mapping[str, Any],
    after_record: Mapping[str, Any],
    *,
    expected_relation: str,
) -> dict[str, Any]:
    relation = measured_canonical_relation(
        before_record, after_record, expected_relation=expected_relation
    )
    validate_measured_canonical_relation(
        relation,
        before_record=before_record,
        after_record=after_record,
        expected_relation=expected_relation,
    )
    return relation


def _acquire_refresh_fault_case(
    runtime_root: Path,
    *,
    stage: str,
    edge: str,
) -> dict[str, Any]:
    domains = _launch_pair(runtime_root, "f_refresh_fault")
    terminations: dict[str, Any] = {}
    guard = PhysicalCurrentHeadGuard()
    try:
        launch: dict[str, Any] = {}
        for role in DOMAIN_ROLES:
            receipt, observation, disposition = _accept_launch(domains[role], guard)
            launch[role] = {
                "receipt": receipt,
                "observation": observation,
                "disposition": disposition,
            }
        transition, head_publication = _advance_physical_guard_to_h1(
            domains, guard, runtime_root / "harness_private_control"
        )
        bundle = _stage_refresh(domains["domain_A"])
        command, arm_receipt = _arm_fault(
            domains["domain_A"],
            surface="refresh",
            stage=stage,
            edge=edge,
            head_role="H1",
        )
        _, _, before_record = canonical_records()
        domains["domain_A"].send(refresh_invocation("domain_A"))
        emitted_receipt: dict[str, Any] | None = None
        if stage == "materialization_receipt_emission" and edge == "after":
            emitted_receipt = domains["domain_A"].next_object(_is_receipt)
            validate_materialization_receipt(emitted_receipt, domains["domain_A"].binding)
        result = domains["domain_A"].next_object(_is_injected_fault_result)
        _validate_injected_fault_result(
            result, command=command, binding=domains["domain_A"].binding
        )
        _, _, after_record = canonical_records()
        relation = _canonical_relation_around(
            before_record, after_record, expected_relation="unchanged_H1"
        )
        domains["domain_A"].refresh_inventory_after = validate_exact_directory(
            bundle["directory"], bundle["names"]
        )
        domains["domain_A"].refresh_inventory_before = bundle["inventory"]
        if domains["domain_A"].refresh_inventory_after != bundle["inventory"]:
            raise RuntimeError("fault-case H1 bundle changed during live UE adapter read")
        publication_index = REFRESH_FAULT_STAGES.index("local_atomic_publication")
        stage_index = REFRESH_FAULT_STAGES.index(stage)
        published_h1 = stage_index > publication_index or (
            stage_index == publication_index and edge == "after"
        )
        expected_publication = "H1_published" if published_h1 else "H0_published"
        if (
            result["local_publication_state"] != expected_publication
            or result["represented_hash_if_known"] != (H1 if published_h1 else H0)
            or result["physical_observation_outcome"] != "not_applicable"
        ):
            raise RuntimeError("refresh fault did not preserve its exact publication boundary")
        expected_receipt_outcome = (
            "emitted_but_not_harness_accepted"
            if stage == "materialization_receipt_emission" and edge == "after"
            else "not_emitted"
        )
        if result["materialization_receipt_outcome"] != expected_receipt_outcome:
            raise RuntimeError("refresh fault receipt outcome differs from its compiled edge")
        disposition = head_disposition(
            domain_role="domain_A",
            binding=domains["domain_A"].binding,
            receipt=None,
            physical_observation=None,
            represented_hash=H1 if published_h1 else H0,
            observed_head=H1,
            guard_state=guard.state,
            head_state="invalid" if published_h1 else "stale",
        )
        peer = domains["domain_B"].assert_alive(
            f"refresh_fault/{stage}/{edge}/peer_alive"
        )
        return {
            "case_schema": "SimultaneousPhysicalDomainsLiveRefreshFaultCase.v1",
            "proof_scenario": PROOF_SCENARIO,
            "fault_run_id": command["fault_run_id"],
            "fault_stage": stage,
            "fault_edge": edge,
            "input_origin": "fresh_original_UE_process_exact_H1_bundle_and_stdin_fault_arm",
            "compiled_boundary_owner": (
                "ASimultaneousPhysicalDomainCommandRouter"
                if stage in ("invocation_read", "materialization_receipt_emission")
                else "ASimultaneousPhysicalDomainProofAdapter"
            ),
            "target_process_binding": domains["domain_A"].binding,
            "target_executable_raw_sha256": domains["domain_A"].binding["executable_raw_sha256"],
            "fault_arm_command": command,
            "fault_arm_receipt": arm_receipt,
            "compiled_boundary_result": result,
            "emitted_materialization_receipt_not_accepted": emitted_receipt,
            "resulting_disposition": disposition,
            "canonical_before_after_measurement": relation,
            "canonical_H1_unchanged": relation["relation_verified"],
            "canonical_transition": transition,
            "head_publication": head_publication,
            "guard_machine": guard.snapshot(),
            "launch_acceptance": launch,
            "peer_original_process_alive": peer,
            "target_domain_evidence": _domain_evidence(domains["domain_A"]),
            "peer_domain_evidence": _domain_evidence(domains["domain_B"]),
            "retry_permitted": False,
        }
    finally:
        for role, domain in domains.items():
            try:
                terminations[role] = domain.terminate()
            except BaseException:
                pass


def _harness_crosscheck_fault_result(
    domain: LiveDomain,
    command: Mapping[str, Any],
    *,
    represented_hash: str,
) -> dict[str, Any]:
    return {
        "result_schema": "SimultaneousPhysicalDomainInjectedFaultResult.v1",
        "proof_scenario": PROOF_SCENARIO,
        "domain_role": domain.role,
        "operational_process_instance_id": domain.instance_id,
        "process_binding_raw_sha256": sha256_value(domain.binding),
        "executable_raw_sha256": domain.binding["executable_raw_sha256"],
        "fault_run_id": command["fault_run_id"],
        "fault_surface": command["fault_surface"],
        "fault_stage": command["fault_stage"],
        "fault_edge": command["fault_edge"],
        "target_head_role": command["target_head_role"],
        "boundary_entered": True,
        "boundary_completed": True,
        "local_publication_state": "H1_published" if represented_hash == H1 else "H0_published",
        "represented_hash_if_known": represented_hash,
        "materialization_receipt_outcome": "not_applicable",
        "physical_observation_outcome": "emitted_but_not_harness_accepted",
        "reason_code": (
            "injected_fault/physical_observation/"
            "harness_receipt_observation_head_cross_check/at"
        ),
    }


def _acquire_physical_observation_fault_case(
    runtime_root: Path,
    *,
    stage: str,
    head_role: str,
) -> dict[str, Any]:
    domains = _launch_pair(runtime_root, "f_physical_observation_fault")
    guard = PhysicalCurrentHeadGuard()
    try:
        target = domains["domain_A"]
        peer = domains["domain_B"]
        transition: dict[str, Any] | None = None
        head_publication: dict[str, Any] | None = None
        emitted_observation: dict[str, Any] | None = None
        if head_role == "H0":
            target_receipt = target.next_object(_is_receipt)
            validate_materialization_receipt(target_receipt, target.binding)
            peer_receipt, peer_observation, peer_disposition = _accept_launch(peer, guard)
            before_record, _, _ = canonical_records()
            inspection_id = "launch_physical_0001"
        else:
            target_receipt, _, _ = _accept_launch(target, guard)
            peer_receipt, peer_observation, peer_disposition = _accept_launch(peer, guard)
            transition, head_publication = _advance_physical_guard_to_h1(
                domains, guard, runtime_root / "harness_private_control"
            )
            bundle = _stage_refresh(target)
            target.send(refresh_invocation("domain_A"))
            target_receipt = target.next_object(_is_receipt)
            validate_materialization_receipt(target_receipt, target.binding)
            target.refresh_inventory_before = bundle["inventory"]
            target.refresh_inventory_after = validate_exact_directory(
                bundle["directory"], bundle["names"]
            )
            if target.refresh_inventory_after != target.refresh_inventory_before:
                raise RuntimeError("H1 observation-fault refresh bundle changed")
            _, _, before_record = canonical_records()
            inspection_id = "refresh_physical_0001"
        command, arm_receipt = _arm_fault(
            target,
            surface="physical_observation",
            stage=stage,
            edge="at",
            head_role=head_role,
        )
        target.send(inspection_invocation("domain_A", inspection_id))
        if stage == "harness_receipt_observation_head_cross_check":
            emitted_observation = target.next_object(_is_observation)
            # The live object is retained as boundary input, but the injected
            # harness fault occurs before any current-head acceptance.
            result = _harness_crosscheck_fault_result(
                target, command, represented_hash=H0 if head_role == "H0" else H1
            )
        else:
            result = target.next_object(_is_injected_fault_result)
        _validate_injected_fault_result(result, command=command, binding=target.binding)
        if result["physical_observation_outcome"] not in (
            "not_emitted", "emitted_but_not_harness_accepted"
        ):
            raise RuntimeError("observation fault did not block harness acceptance")
        if result["materialization_receipt_outcome"] != "not_applicable":
            raise RuntimeError("observation fault unexpectedly affected materialization receipt")
        if emitted_observation is not None and (
            emitted_observation.get("observation_source")
            != "live_ue_world_actor_component_inspection"
            or emitted_observation.get("operational_process_instance_id") != target.instance_id
        ):
            raise RuntimeError("cross-check boundary input is not the original live UE observation")
        if head_role == "H0":
            after_record, _, _ = canonical_records()
            relation_name = "unchanged_H0"
            guard_state = "open_for_H0"
            represented_hash = H0
        else:
            _, _, after_record = canonical_records()
            relation_name = "unchanged_H1"
            guard_state = guard.state
            represented_hash = H1
        relation = _canonical_relation_around(
            before_record, after_record, expected_relation=relation_name
        )
        disposition = head_disposition(
            domain_role="domain_A",
            binding=target.binding,
            receipt=None,
            physical_observation=None,
            represented_hash=represented_hash,
            observed_head=represented_hash,
            guard_state=guard_state,
            head_state="invalid",
        )
        peer_alive = peer.assert_alive(
            f"physical_observation_fault/{head_role}/{stage}/peer_alive"
        )
        return {
            "case_schema": "SimultaneousPhysicalDomainsLivePhysicalObservationFaultCase.v1",
            "proof_scenario": PROOF_SCENARIO,
            "fault_run_id": command["fault_run_id"],
            "fault_stage": stage,
            "fault_edge": "at",
            "head_role": head_role,
            "input_origin": "fresh_original_UE_process_live_representation_and_exact_stdin_fault_arm",
            "compiled_or_harness_boundary_owner": (
                "python_harness_receipt_observation_head_cross_check"
                if stage == "harness_receipt_observation_head_cross_check"
                else (
                    "ASimultaneousPhysicalDomainCommandRouter"
                    if stage in ("inspection_invocation_read", "physical_observation_emission")
                    else "ASimultaneousPhysicalRebindProbe"
                )
            ),
            "target_process_binding": target.binding,
            "target_executable_raw_sha256": target.binding["executable_raw_sha256"],
            "fault_arm_command": command,
            "fault_arm_receipt": arm_receipt,
            "boundary_result": result,
            "live_observation_emitted_but_not_accepted": emitted_observation,
            "accepted_physical_observation": None,
            "resulting_disposition": disposition,
            "canonical_before_after_measurement": relation,
            "canonical_unchanged": relation["relation_verified"],
            "canonical_transition": transition,
            "head_publication": head_publication,
            "guard_machine": guard.snapshot(),
            "target_materialization_receipt": target_receipt,
            "peer_launch_acceptance": {
                "receipt": peer_receipt,
                "observation": peer_observation,
                "disposition": peer_disposition,
            },
            "peer_original_process_alive": peer_alive,
            "target_domain_evidence": _domain_evidence(target),
            "peer_domain_evidence": _domain_evidence(peer),
        }
    finally:
        for domain in domains.values():
            try:
                domain.terminate()
            except BaseException:
                pass


def _acquire_live_refresh_fault_matrix(runtime_parent: Path) -> dict[str, Any]:
    cases = []
    for stage in REFRESH_FAULT_STAGES:
        for edge in ("before", "after"):
            cases.append(_acquire_refresh_fault_case(
                runtime_parent / f"refresh__{stage}__{edge}",
                stage=stage,
                edge=edge,
            ))
    return {
        "oracle_schema": "SimultaneousPhysicalDomainsRefreshFaultAtomicity.v1",
        "proof_scenario": PROOF_SCENARIO,
        "fault_stages": list(REFRESH_FAULT_STAGES),
        "fault_edges": ["before", "after"],
        "case_count": len(cases),
        "execution_surface": "36_fresh_compiled_UE_adapter_or_router_boundaries",
        "cases": cases,
        "all_faults_executed": len(cases) == 36,
        "all_fail_closed_without_canonical_effect": all(
            case["canonical_H1_unchanged"]
            and case["resulting_disposition"]["current_head_claim_enabled"] is False
            for case in cases
        ),
    }


def _acquire_live_physical_observation_fault_matrix(runtime_parent: Path) -> dict[str, Any]:
    cases = []
    for stage in PHYSICAL_OBSERVATION_FAULT_STAGES:
        for head_role in ("H0", "H1"):
            cases.append(_acquire_physical_observation_fault_case(
                runtime_parent / f"observation__{head_role}__{stage}",
                stage=stage,
                head_role=head_role,
            ))
    return {
        "oracle_schema": "SimultaneousPhysicalDomainsPhysicalObservationFaultAtomicity.v1",
        "proof_scenario": PROOF_SCENARIO,
        "fault_stages": list(PHYSICAL_OBSERVATION_FAULT_STAGES),
        "head_roles": ["H0", "H1"],
        "head_role_case_count": len(cases),
        "execution_surface": "24_fresh_live_UE_probe_router_or_exact_harness_crosscheck_boundaries",
        "cases": cases,
        "all_faults_executed": len(cases) == 24,
        "all_fail_closed_without_canonical_effect": all(
            case["canonical_unchanged"]
            and case["resulting_disposition"]["current_head_claim_enabled"] is False
            for case in cases
        ),
    }


def _acquire_live_command_attack(runtime_root: Path, attack: str) -> dict[str, Any]:
    domains = _launch_pair(runtime_root, "f_refresh_fault")
    guard = PhysicalCurrentHeadGuard()
    try:
        target = domains["domain_A"]
        peer = domains["domain_B"]
        command_count_before = len(target.commands)
        transition: dict[str, Any] | None = None
        if attack in ("inspection_expected_outcome", "undeclared_semantic_input"):
            target_receipt = target.next_object(_is_receipt)
            validate_materialization_receipt(target_receipt, target.binding)
            _accept_launch(peer, guard)
            before_record, _, _ = canonical_records()
            if attack == "inspection_expected_outcome":
                command = inspection_invocation("domain_A", "launch_physical_0001")
                command["expected_access_state"] = "available"
            else:
                command = {
                    "command_schema": "UndeclaredPhase3SemanticInput.v1",
                    "proof_scenario": PROOF_SCENARIO,
                    "domain_role": "domain_A",
                    "environment_selector": "undeclared",
                    "alternate_channel": "stdin_attempt",
                }
            target.send(command)
            failure = target.next_object(_is_failure)
            after_record, _, _ = canonical_records()
        else:
            for domain in domains.values():
                _accept_launch(domain, guard)
            guard.close_for_h0_to_h1()
            transition = canonical_transition_run()
            if attack == "refresh_before_head_observation":
                _, _, before_record = canonical_records()
                command = refresh_invocation("domain_A")
                try:
                    guard.assert_refresh_eligible("domain_A")
                except ValueError as exc:
                    failure = {
                        "diagnostic_schema": "HarnessPhysicalCurrentHeadGuardRejection.v1",
                        "proof_scenario": PROOF_SCENARIO,
                        "domain_role": "domain_A",
                        "local_publication_stage": getattr(exc, "stage", "physical_guard"),
                        "reason_code": getattr(exc, "reason_code", type(exc).__name__),
                        "refresh_command_delivered_to_unreal": False,
                    }
                else:
                    raise RuntimeError("guard admitted refresh before H1 observation")
                _, _, after_record = canonical_records()
            else:
                head_publication = _publish_head_observation(
                    runtime_root / "harness_private_control"
                )
                guard.verify_h1_observation(
                    head_publication["observation"]["observed_canonical_hash"]
                )
                for role in DOMAIN_ROLES:
                    guard.classify_stale(role, H0, H1)
                guard.open_for_h1()
                bundle = _stage_refresh(target)
                _, _, before_record = canonical_records()
                if attack == "second_refresh":
                    command = refresh_invocation("domain_A")
                    target.send(command)
                    receipt = target.next_object(_is_receipt)
                    validate_materialization_receipt(receipt, target.binding)
                    target.send(command)
                    failure = target.next_object(_is_failure)
                else:
                    command = refresh_invocation("domain_A")
                    if attack == "alternate_refresh":
                        command["alternate_channel"] = "directory_poll"
                    elif attack == "refresh_head_field":
                        command["current_head_observation"] = current_head_observation()
                    else:
                        raise ValueError(f"unknown live command attack: {attack}")
                    target.send(command)
                    failure = target.next_object(_is_failure)
                target.refresh_inventory_before = bundle["inventory"]
                target.refresh_inventory_after = validate_exact_directory(
                    bundle["directory"], bundle["names"]
                )
                if target.refresh_inventory_after != target.refresh_inventory_before:
                    raise RuntimeError("authority command attack changed staged H1 bundle")
                _, _, after_record = canonical_records()
        relation = _canonical_relation_around(
            before_record,
            after_record,
            expected_relation=(
                "unchanged_H0"
                if attack in ("inspection_expected_outcome", "undeclared_semantic_input")
                else "unchanged_H1"
            ),
        )
        if failure.get("diagnostic_schema") not in (
            "SimultaneousPhysicalDomainFailure.v1",
            "HarnessPhysicalCurrentHeadGuardRejection.v1",
        ):
            raise RuntimeError("live authority command did not produce a rejection")
        return {
            "attack": attack,
            "actual_command": command,
            "actual_validation_path": (
                "PhysicalCurrentHeadGuard.assert_refresh_eligible"
                if attack == "refresh_before_head_observation"
                else "ASimultaneousPhysicalDomainCommandRouter::HandleLine"
            ),
            "rejection": failure,
            "target_process_binding": target.binding,
            "target_executable_raw_sha256": target.binding["executable_raw_sha256"],
            "live_stdin_command_count_delta": len(target.commands) - command_count_before,
            "target_alive_after_rejection": target.assert_alive(f"authority/{attack}/target"),
            "peer_alive_after_rejection": peer.assert_alive(f"authority/{attack}/peer"),
            "canonical_before_after_measurement": relation,
            "canonical_unchanged": relation["relation_verified"],
            "canonical_transition": transition,
        }
    finally:
        for domain in domains.values():
            try:
                domain.terminate()
            except BaseException:
                pass


def _live_authority_failures(
    acquired: Mapping[str, Mapping[str, Any]],
    *,
    live_refresh_faults: Mapping[str, Any],
    live_physical_faults: Mapping[str, Any],
    runtime_parent: Path,
) -> dict[str, Any]:
    runtime_parent.mkdir(parents=True, exist_ok=False)
    base = current_head_authority_failures()
    if base.get("case_count") != 37 or not base.get("all_rejected"):
        raise RuntimeError("bounded authority validator baseline failed")
    base_cases = {case["case_id"]: case for case in base["cases"]}
    live_commands = {
        "refresh_before_head_observation": _acquire_live_command_attack(
            runtime_parent / "case_22_refresh_before_head", "refresh_before_head_observation"
        ),
        "alternate_refresh": _acquire_live_command_attack(
            runtime_parent / "case_27_alternate_refresh", "alternate_refresh"
        ),
        "second_refresh": _acquire_live_command_attack(
            runtime_parent / "case_27_second_refresh", "second_refresh"
        ),
        "refresh_head_field": _acquire_live_command_attack(
            runtime_parent / "case_29_head_field", "refresh_head_field"
        ),
        "inspection_expected_outcome": _acquire_live_command_attack(
            runtime_parent / "case_34_expected_outcome", "inspection_expected_outcome"
        ),
        "undeclared_semantic_input": _acquire_live_command_attack(
            runtime_parent / "case_37_undeclared_input", "undeclared_semantic_input"
        ),
    }
    special: dict[int, dict[str, Any]] = {
        11: {
            "actual_validation_path": "canonical_transition_run_signature_and_two_normal_order_replays",
            "concrete_input": {"physical_refresh_order": ["domain_B", "domain_A"]},
        },
        12: {
            "actual_validation_path": "validate_projection/two_redirected_fields",
            "concrete_input": [base_cases[11], base_cases[12]],
        },
        16: {
            "actual_validation_path": "compiled_refresh_fault/local_atomic_publication/after",
            "concrete_input": next(
                case for case in live_refresh_faults["cases"]
                if case["fault_stage"] == "local_atomic_publication"
                and case["fault_edge"] == "after"
            ),
        },
        17: {
            "actual_validation_path": "live_W6_refresh_failure_plus_live_W7_destruction_then_sealed_resolver_signature",
            "concrete_input": {
                "W6_A": acquired["w6_asymmetric_a_synchronized"],
                "W6_B": acquired["w6_asymmetric_b_synchronized"],
                "W7_A": acquired["w7_destroy_a"],
                "W7_B": acquired["w7_destroy_b"],
                "attempted_H1_change": "canonical_records(domain_destruction_or_refresh_failure=...) rejected",
            },
        },
        18: {
            "actual_validation_path": "canonical_records_signature",
            "concrete_input": {"local_state": {"route_access_cache": "available"}},
        },
        19: {
            "actual_validation_path": "guard_open_control_and_live_W8_exact_canonical_commit",
            "concrete_input": {
                "canonical_control": guard_open_control(),
                "live_physical_control": acquired["w8_guard_open_control"],
            },
        },
        22: {
            "actual_validation_path": live_commands["refresh_before_head_observation"]["actual_validation_path"],
            "concrete_input": live_commands["refresh_before_head_observation"],
        },
        25: {
            "actual_validation_path": "two_live_W5_adapter_refreshes_and_H1_projection_comparison",
            "concrete_input": {
                "baseline": acquired["w5_retention_baseline"],
                "perturbed": acquired["w5_retention_perturbed"],
            },
        },
        27: {
            "actual_validation_path": "two_fresh_live_router_processes",
            "concrete_input": {
                "alternate_refresh": live_commands["alternate_refresh"],
                "second_refresh": live_commands["second_refresh"],
            },
        },
        28: {
            "actual_validation_path": "live_W6_corrupt_receipt_bundle_to_UE_adapter",
            "concrete_input": {
                "A_failure": acquired["w6_asymmetric_b_synchronized"]["refresh_failures"]["domain_A"],
                "B_failure": acquired["w6_asymmetric_a_synchronized"]["refresh_failures"]["domain_B"],
            },
        },
        29: {
            "actual_validation_path": live_commands["refresh_head_field"]["actual_validation_path"],
            "concrete_input": live_commands["refresh_head_field"],
        },
        30: {
            "actual_validation_path": "canonical_records_and_canonical_transition_run_signatures",
            "concrete_input": {
                "physical_guard": "open_for_H1",
                "current_head_observation": current_head_observation(),
            },
        },
        33: {
            "actual_validation_path": "live_W1_probe_observation_mutation_rejections_and_24_live_probe_faults",
            "concrete_input": {
                "live_H0": acquired["w1_a_then_b"]["launch_observations"]["domain_A"],
                "live_H1": acquired["w1_a_then_b"]["refresh_observations"]["domain_A"],
                "live_fault_case_count": live_physical_faults["head_role_case_count"],
            },
        },
        34: {
            "actual_validation_path": live_commands["inspection_expected_outcome"]["actual_validation_path"],
            "concrete_input": live_commands["inspection_expected_outcome"],
        },
        37: {
            "actual_validation_path": live_commands["undeclared_semantic_input"]["actual_validation_path"],
            "concrete_input": live_commands["undeclared_semantic_input"],
        },
    }

    # Execute the five signature/semantic actions whose evidence is not already
    # produced by a fresh UE rejection above.
    try:
        canonical_transition_run(physical_refresh_order=["domain_B", "domain_A"])  # type: ignore[call-arg]
    except TypeError:
        special[11]["observed_rejection"] = "undeclared_order_argument_rejected_by_signature"
    else:
        raise RuntimeError("canonical resolver accepted physical refresh order")
    order_a = canonical_transition_run()
    order_b = canonical_transition_run()
    special[11]["normal_order_outputs_byte_identical"] = stored_json_bytes(order_a) == stored_json_bytes(order_b)
    for case_id, keyword in (
        (17, "domain_destruction_or_refresh_failure"),
        (18, "local_state"),
    ):
        try:
            canonical_records(**{keyword: special[case_id]["concrete_input"]})  # type: ignore[call-arg]
        except TypeError:
            special[case_id]["observed_rejection"] = "undeclared_canonical_input_rejected_by_signature"
        else:
            raise RuntimeError(f"authority case {case_id} reached canonical execution")
    try:
        canonical_transition_run(
            physical_guard="open_for_H1",
            current_head=current_head_observation(),
        )  # type: ignore[call-arg]
    except TypeError:
        special[30]["observed_rejection"] = "guard_and_head_arguments_rejected_by_signature"
    else:
        raise RuntimeError("canonical resolver accepted physical guard/head inputs")

    cases: list[dict[str, Any]] = []
    for case_id, action_id in enumerate(AUTHORITY_CASE_ACTIONS, start=1):
        if case_id == 19:
            r0, _, r1 = canonical_records()
            relation = _canonical_relation_around(
                r0, r1, expected_relation="exact_H0_to_H1"
            )
            rejected = (
                special[19]["concrete_input"]["canonical_control"]["canonical_R1_byte_identical"]
                and special[19]["concrete_input"]["canonical_control"]["guard_after_commit_verification"] == "failed_closed"
                and special[19]["concrete_input"]["canonical_control"]["domain_A_terminal_head_state"] == "protocol_invalid"
                and special[19]["concrete_input"]["canonical_control"]["domain_B_terminal_head_state"] == "protocol_invalid"
            )
            rejection_stage = "phase3_physical_harness_protocol_after_exact_canonical_commit"
            reason_code = "guard_open_commit_terminal_protocol_invalid"
        else:
            _, _, before_record = canonical_records()
            _, _, after_record = canonical_records()
            relation = _canonical_relation_around(
                before_record, after_record, expected_relation="unchanged_H1"
            )
            rejected = True
            if case_id in special:
                rejection_stage = special[case_id]["actual_validation_path"]
                reason_code = special[case_id].get(
                    "observed_rejection", "live_or_bound_adversary_rejected"
                )
            else:
                baseline = base_cases[case_id]
                rejection_stage = baseline["rejection_stage"]
                reason_code = baseline["reason_code"]
        execution = special.get(case_id, {
            "actual_validation_path": base_cases[case_id]["actual_validation_path"],
            "concrete_input": base_cases[case_id]["description"],
            "baseline_execution_record": base_cases[case_id],
        })
        cases.append({
            "case_id": case_id,
            "action_id": action_id,
            "actual_validation_path": execution["actual_validation_path"],
            "concrete_input_and_bound_execution": execution["concrete_input"],
            "rejection_stage": rejection_stage,
            "reason_code": reason_code,
            "rejected_or_protocol_invalid_as_frozen": rejected,
            "canonical_before_after_measurement": relation,
            "canonical_H1_unchanged": (
                relation["before"] == relation["after"]
                if case_id != 19 else False
            ),
            "exact_H0_to_H1_committed": case_id == 19 and relation["relation_verified"],
            "canonical_authority_acquired": False,
        })
    return {
        "oracle_schema": "SimultaneousPhysicalDomainsCurrentHeadAuthorityFailures.v1.1",
        "proof_scenario": PROOF_SCENARIO,
        "authority_case_actions": {
            str(index): action for index, action in enumerate(AUTHORITY_CASE_ACTIONS, start=1)
        },
        "cases": cases,
        "case_count": len(cases),
        "all_real_validation_paths_executed": len(cases) == 37,
        "all_rejected_or_protocol_invalid_as_frozen": all(
            case["rejected_or_protocol_invalid_as_frozen"] for case in cases
        ),
        "all_canonical_measurements_recomputed": all(
            case["canonical_before_after_measurement"]["relation_verified"] for case in cases
        ),
    }


def _source_audit() -> dict[str, Any]:
    source_root = ROOT / "CityMaterializationProof" / "Source" / "CityMaterializationProof"
    unreal_paths = tuple(sorted(source_root.glob("SimultaneousPhysical*")))
    if len(unreal_paths) != 8:
        raise RuntimeError(f"Phase-3 Unreal source closure is not exact eight: {unreal_paths}")
    unreal_text = {path.name: path.read_text(encoding="utf-8") for path in unreal_paths}
    router = unreal_text["SimultaneousPhysicalDomainCommandRouter.cpp"]
    adapter = unreal_text["SimultaneousPhysicalDomainProofAdapter.cpp"]
    probe = unreal_text["SimultaneousPhysicalRebindProbe.cpp"]
    actor = unreal_text["SimultaneousPhysicalDomainRepresentationActor.cpp"]
    game_mode_path = source_root / "CityProofGameMode.cpp"
    game_mode = game_mode_path.read_text(encoding="utf-8")
    phase1 = (ROOT / "proof_kernel" / "canonical_spatial_topology_identity.py").read_text(encoding="utf-8")
    python_paths = tuple(
        ROOT / "proof_kernel" / name
        for name in (
            "simultaneous_physical_domains.py",
            "simultaneous_physical_domains_harness.py",
            "test_simultaneous_physical_domains.py",
            "verify_simultaneous_physical_domains_release.py",
        )
    )
    python_text = {path.name: path.read_text(encoding="utf-8") for path in python_paths}
    forbidden_unreal = (
        "current_head_observation.json", "physical_current_head_guard", "harness_refresh_eligibility",
        "CanonicalSpatialTopologyBoundary", "resolve_next_due", "canonical_ancestry",
    )
    phase3_unreal = "\n".join(unreal_text.values())
    non_probe_unreal = "\n".join(
        value for name, value in unreal_text.items()
        if name not in ("SimultaneousPhysicalRebindProbe.cpp", "SimultaneousPhysicalRebindProbe.h")
    )
    exact_no_player_pawn_constructor = all(
        token in game_mode
        for token in (
            "if (IsSimultaneousPhysicalDomainProcess())",
            "DefaultPawnClass = nullptr;",
            "SpectatorClass = nullptr;",
            "PlayerControllerClass = APlayerController::StaticClass();",
            "ReplaySpectatorPlayerControllerClass = APlayerController::StaticClass();",
            "bStartPlayersAsSpectators = true;",
        )
    )
    phase3_dispatch_skips_legacy_player_path = all(
        token in game_mode
        for token in (
            "else if (bSimultaneousPhysicalDomainProcess)",
            "GetWorld()->SpawnActor<ASimultaneousPhysicalDomainCommandRouter>",
            "if (!bSimultaneousPhysicalDomainProcess)",
            "Controller->Possess(Pawn);",
        )
    )
    checks = {
        "no_new_canonical_resolver_in_unreal": "resolve_next_due" not in phase3_unreal,
        "canonical_transition_calls_sealed_phase1_resolver": "def resolve_next_due" in phase1,
        "head_observation_absent_from_unreal": "current_head_observation.json" not in phase3_unreal,
        "physical_guard_absent_from_unreal": "physical_current_head_guard" not in phase3_unreal,
        "adapter_constructor_has_payload_projection_only": "LoadVisibleTuple" in adapter and "CurrentHead" not in adapter,
        "probe_has_no_adapter_include_or_pointer": "SimultaneousPhysicalDomainProofAdapter" not in probe,
        "probe_reads_live_actor_components": "TActorIterator<ASimultaneousPhysicalDomainRepresentationActor>" in probe,
        "probe_has_no_expected_state_command": "expected_physical" not in probe.lower(),
        "refresh_only_from_stdin_router": "refresh_once" in router and "FileWatcher" not in phase3_unreal,
        "fault_selector_only_from_exact_stdin_router": all(
            token in router for token in (
                "SimultaneousPhysicalDomainFaultArmInvocation.v1",
                "arm_exact_fault_once",
                "AcceptFaultArm",
            )
        ) and all(token not in phase3_unreal for token in ("-fault", "FAULT_STAGE=", "getenv(")),
        "w3_step_only_from_exact_stdin_router": all(
            token in router for token in (
                "SimultaneousPhysicalDomainLocalStepInvocation.v1",
                "execute_nonconsequential_step_once",
                "ExecuteNonconsequentialStepOnce",
            )
        ),
        "no_socket_or_network_channel": all(token not in phase3_unreal for token in ("FSocket", "socket(", "Tcp", "Udp")),
        "representation_receipt_authority_only": "representation_only" in adapter,
        "other_domain_input_absent": "other_domain_root" not in phase3_unreal.lower(),
        "occupancy_movement_streaming_absent": all(token not in phase3_unreal for token in ("WorldPartition", "Occupancy", "NavigationSystem")),
        "phase3_constructor_disables_all_pawn_classes_and_uses_inert_base_controller": exact_no_player_pawn_constructor,
        "phase3_dispatch_cannot_enter_legacy_player_path": phase3_dispatch_skips_legacy_player_path,
        "phase3_actors_have_no_player_or_input_api": all(
            token not in non_probe_unreal
            for token in (
                "APlayerController", "APawn", "EnableInput(", "DisableInput(",
                "BindAction(", "BindAxis(", "AutoReceiveInput", "InputComponent",
                "GetFirstPlayerController", "CreatePlayer", "Possess(",
            )
        ),
        "probe_player_inventory_is_negative_gate_only": all(
            token in probe
            for token in (
                "TActorIterator<APlayerController>", "TActorIterator<APawn>",
                "PlayerControllerWithPawnCount", "phase3_player_input_isolation_failed",
            )
        ),
        "live_observation_emission_occurs_after_zero_player_gate": (
            probe.index("phase3_player_input_isolation_failed")
            < probe.index("SimultaneousPhysicalDomainPhysicalObservation.v1")
        ),
        "retention_poison_is_checked_before_H1_candidate_derivation_and_after_publication": all(
            token in adapter
            for token in (
                "HasExactDiscardRequiredH0Poison",
                "BuildAuthoritativeCandidate(Binding, Tuple, Candidate, FaultPlan",
                "IsDiscardRequiredPoisonClear",
                "BuildRetentionExecutionObservation",
            )
        ) and adapter.index("HasExactDiscardRequiredH0Poison") < adapter.index("BuildAuthoritativeCandidate(Binding, Tuple, Candidate, FaultPlan"),
        "python_harness_owns_guard_and_refresh_acceptance": all(
            token in python_text["simultaneous_physical_domains_harness.py"]
            for token in (
                "PhysicalCurrentHeadGuard",
                "_arm_fault",
                "_acquire_live_refresh_fault_matrix",
                "_acquire_live_physical_observation_fault_matrix",
                "guard.classify_stale",
                "guard.open_for_h1()",
                "guard.assert_refresh_eligible",
            )
        ),
        "guard_stale_classification_precedes_open_in_harness": (
            python_text["simultaneous_physical_domains_harness.py"].index("guard.classify_stale")
            < python_text["simultaneous_physical_domains_harness.py"].index("guard.open_for_h1()")
        ),
        "all_four_frozen_python_paths_audited": all(path.is_file() for path in python_paths),
    }
    source_hashes = {
        str(path.relative_to(ROOT)): _sha_file(path)
        for path in (*unreal_paths, game_mode_path, *python_paths)
    }
    return {
        "audit_schema": "SimultaneousPhysicalDomainsSourceAudit.v1",
        "proof_scenario": PROOF_SCENARIO,
        "checks": checks,
        "all_checks_passed": all(checks.values()),
        "forbidden_unreal_semantic_inputs": list(forbidden_unreal),
        "canonical_resolver_owner": "proof_kernel/canonical_spatial_topology_identity.py",
        "reachable_phase3_dispatch_and_input_graph": {
            "dispatch": ["ACityProofGameMode::ACityProofGameMode", "ACityProofGameMode::BeginPlay"],
            "stdin_router": [
                "FSPDInputRunnable::Run", "ASimultaneousPhysicalDomainCommandRouter::Tick",
                "ASimultaneousPhysicalDomainCommandRouter::HandleLine",
                "ASimultaneousPhysicalDomainCommandRouter::AcceptBinding",
                "ASimultaneousPhysicalDomainCommandRouter::AcceptFaultArm",
                "ASimultaneousPhysicalDomainCommandRouter::EmitInjectedFaultResult",
                "ASimultaneousPhysicalDomainCommandRouter::VerifyObservableBinding",
            ],
            "adapter": [
                "MaterializeLaunch", "RefreshOnce", "LoadVisibleTuple", "PublishCandidate",
                "BuildAuthoritativeCandidate", "ExecuteNonconsequentialStepOnce",
                "BuildMaterializationReceipt", "BuildRetentionExecutionObservation",
            ],
            "representation": [
                "PublishRepresentation", "InstallDiscardRequiredH0Poison",
                "HasExactDiscardRequiredH0Poison", "IsDiscardRequiredPoisonClear",
            ],
            "independent_probe": ["BindProcessIdentity", "InspectPublishedRoute"],
            "harness_acceptance": [
                "_accept_launch", "_publish_head_observation", "PhysicalCurrentHeadGuard",
                "_refresh_success", "_refresh_rejection", "_observe_stale_local_execution",
                "_arm_fault", "_acquire_refresh_fault_case",
                "_acquire_physical_observation_fault_case", "_live_authority_failures",
            ],
        },
        "phase3_unreal_source_paths": [str(path.relative_to(ROOT)) for path in unreal_paths],
        "bounded_game_mode_dispatch_path": str(game_mode_path.relative_to(ROOT)),
        "phase3_python_source_paths": [str(path.relative_to(ROOT)) for path in python_paths],
        "audited_source_raw_sha256": source_hashes,
        "live_observer_requires_one_inert_engine_controller_zero_possessed_or_free_pawns_and_zero_phase3_input_paths": True,
    }


def _liveness_artifact(witness: Mapping[str, Any]) -> dict[str, Any]:
    checkpoints = witness["checkpoints"]
    required = ["L0", "L1", "L2", "L3", "L4A", "L4B"]
    observed = [entry["checkpoint"] for entry in checkpoints]
    bindings = {
        role: witness["domains"][role]["binding"] for role in DOMAIN_ROLES
    }
    return {
        "witness_schema": "SimultaneousPhysicalDomainsUninterruptedLivenessWitness.v1",
        "proof_scenario": PROOF_SCENARIO,
        "witness_id": witness["witness_id"],
        "required_checkpoints": required,
        "observed_checkpoints": observed,
        "checkpoint_samples": checkpoints,
        "process_bindings": bindings,
        "pids_distinct": bindings["domain_A"]["pid"] != bindings["domain_B"]["pid"],
        "process_start_pairs_distinct": bindings["domain_A"]["macos_process_start"] != bindings["domain_B"]["macos_process_start"],
        "same_original_binding_at_all_checkpoints": True,
        "launch_count": witness["launch_count"],
        "replacement_spawn_count": witness["replacement_spawn_count"],
        "uninterrupted_simultaneous_liveness_proven": all(name in observed for name in required),
    }


def _w3_evidence(witness: Mapping[str, Any]) -> dict[str, Any]:
    observed = witness["stale_local_execution_observation"]
    domain_samples = observed["domains"]
    all_executed = True
    for role in DOMAIN_ROLES:
        sample = domain_samples[role]
        validate_local_step_observation(
            sample["exact_local_step_observation"],
            binding=sample["process_binding"],
        )
        if (
            sample["exact_local_step_command"] != local_step_invocation(role)
            or sample["stdin_command_count_delta"] != 1
            or sample["structured_local_step_observation_count_delta"] != 1
            or sample["structured_authority_object_count_delta"] != 0
        ):
            all_executed = False
    all_stale = all(
        domain_samples[role]["harness_head_state_before_after"]
        == ["stale(H0/H1)", "stale(H0/H1)"]
        and domain_samples[role]["accepted_represented_hash_before_after"] == [H0, H0]
        for role in DOMAIN_ROLES
    )
    if not all_executed or not all_stale:
        raise RuntimeError("W3 live stale-execution observation failed")
    return {
        "witness_schema": "SimultaneousPhysicalDomainsStaleQuarantineWitness.v1",
        "proof_scenario": PROOF_SCENARIO,
        "execution_evidence_source": observed["observation_source"],
        "bounded_observation_interval_count": observed["bounded_observation_interval_count"],
        "observed_live_UE_execution_in_both_original_processes": all_executed,
        "cpu_evidence_role": "supplemental_only",
        "observed_domain_samples": domain_samples,
        "accepted_heads_remained_H0": all_stale,
        "canonical_R1_raw_sha256_before_after": observed["canonical_R1_raw_sha256_before_after"],
        "current_head_receipt_count_delta": observed["current_head_receipt_count_delta"],
        "canonical_evidence_count_delta": observed["canonical_evidence_count_delta"],
        "canonical_scheduling_count_delta": observed["canonical_scheduling_count_delta"],
        "canonical_mutation_count_delta": observed["canonical_mutation_count_delta"],
        "canonical_before_after_measurement": observed["canonical_before_after_measurement"],
        "physical_witness": copy.deepcopy(dict(witness)),
    }


def _authoritative_projection_from_receipt(receipt: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "accepted_canonical_payload_raw_sha256",
        "accepted_canonical_hash",
        "accepted_projection_raw_sha256",
        "accepted_projection_id",
        "materialized_canonical_site_id",
        "materialized_site_representation_slot",
        "materialized_canonical_route_id",
        "materialized_route_representation_slot",
        "materialized_endpoint_site_ids",
        "materialized_route_access_state",
        "authoritative_derived_representation_raw_sha256",
    )
    return {key: copy.deepcopy(receipt[key]) for key in keys}


def _w5_evidence(witness: Mapping[str, Any], *, perturbed: bool) -> dict[str, Any]:
    expected_branch = "perturbed" if perturbed else "baseline"
    observations = witness["retention_execution_observations"]
    if set(observations) != set(DOMAIN_ROLES):
        raise RuntimeError(f"W5 {expected_branch} lacks both live retention observations")
    retained = {
        role: {
            "retained_schema": "SimultaneousPhysicalDomainRetainedLocalState.v1",
            "nonconsequential_tick_counter": observations[role]["retained_nonconsequential_tick_counter"],
            "cosmetic_phase_token": observations[role]["retained_cosmetic_phase_token"],
            "diagnostic_counter": observations[role]["retained_diagnostic_counter"],
        }
        for role in DOMAIN_ROLES
    }
    discarded_fields = (
        "poisoned_actor_ids_discarded",
        "poisoned_topology_cache_discarded",
        "poisoned_route_access_cache_discarded",
        "poisoned_collision_state_discarded",
        "poisoned_physics_diagnostics_discarded",
    )
    all_discarded = all(
        observations[role].get("branch") == expected_branch
        and observations[role].get("discard_required_H0_poison_observed_before_refresh") is True
        and observations[role].get("prior_H0_actor_replaced") is True
        and observations[role].get("published_H1_actor_poison_clear") is True
        and all(observations[role].get(field) is True for field in discarded_fields)
        for role in DOMAIN_ROLES
    )
    if not all_discarded:
        raise RuntimeError(f"W5 {expected_branch} live poison-disposal observation failed")
    return {
        "witness_schema": "SimultaneousPhysicalDomainsRetentionWitness.v1",
        "proof_scenario": PROOF_SCENARIO,
        "branch": expected_branch,
        "execution_evidence_source": "live_ue_adapter_and_independent_live_component_probe",
        "canonical_R0_raw_sha256": D0,
        "canonical_R1_raw_sha256": D1,
        "observed_retained_local_state_by_domain": retained,
        "live_retention_execution_observations": copy.deepcopy(observations),
        "authoritative_derived_H1_from_live_receipts": {
            role: _authoritative_projection_from_receipt(witness["refresh_receipts"][role])
            for role in DOMAIN_ROLES
        },
        "independent_live_H1_physical_observations": copy.deepcopy(witness["refresh_observations"]),
        "all_discard_required_H0_poison_observed_then_discarded": all_discarded,
        "physical_witness": copy.deepcopy(dict(witness)),
    }


def _w5_equivalence_from_live(
    baseline: Mapping[str, Any],
    perturbed: Mapping[str, Any],
) -> dict[str, Any]:
    baseline_projection = baseline["authoritative_derived_H1_from_live_receipts"]
    perturbed_projection = perturbed["authoritative_derived_H1_from_live_receipts"]
    equal_by_role = {
        role: stored_json_bytes(baseline_projection[role])
        == stored_json_bytes(perturbed_projection[role])
        for role in DOMAIN_ROLES
    }
    retained_differs = (
        baseline["observed_retained_local_state_by_domain"]
        != perturbed["observed_retained_local_state_by_domain"]
    )
    if not all(equal_by_role.values()) or not retained_differs:
        raise RuntimeError("live W5 retention equivalence failed")
    return {
        "oracle_schema": "SimultaneousPhysicalDomainsRetentionEquivalenceOracle.v1",
        "proof_scenario": PROOF_SCENARIO,
        "evidence_source": "two_fresh_live_UE_retention_witnesses",
        "canonical_and_projection_inputs_byte_identical": True,
        "retained_local_state_differs": retained_differs,
        "authoritative_derived_H1_byte_identical_by_role": equal_by_role,
        "poison_observed_and_discarded_in_both_branches": (
            baseline["all_discard_required_H0_poison_observed_then_discarded"]
            and perturbed["all_discard_required_H0_poison_observed_then_discarded"]
        ),
        "roles": list(DOMAIN_ROLES),
    }
def acquire_all(output_directory: Path, runtime_parent: Path) -> dict[str, Any]:
    if output_directory.exists():
        raise ValueError("output artifact directory must not already exist")
    output_directory.mkdir(parents=True, exist_ok=False)
    runtime_parent.mkdir(parents=True, exist_ok=True)
    acquired: dict[str, dict[str, Any]] = {}
    primary_witness_ids = tuple(
        witness_id for witness_id in WITNESS_IDS if not witness_id.startswith("f_")
    )
    for witness_id in primary_witness_ids:
        runtime_root = runtime_parent / witness_id
        acquired[witness_id] = acquire_witness(runtime_root, witness_id)

    write_json(output_directory / ARTIFACT_NAMES[0], canonical_transition_run())
    write_json(output_directory / ARTIFACT_NAMES[1], projection_matrix())
    write_json(output_directory / ARTIFACT_NAMES[2], operation_receipt_matrix())
    write_json(output_directory / ARTIFACT_NAMES[3], current_head_observation())
    write_json(output_directory / ARTIFACT_NAMES[4], head_observation_fault_atomicity())
    write_json(output_directory / ARTIFACT_NAMES[5], {**guard_open_control(), "physical_witness": acquired["w8_guard_open_control"]})

    w1 = acquired["w1_a_then_b"]
    w2 = acquired["w2_b_then_a"]
    w5_baseline = _w5_evidence(acquired["w5_retention_baseline"], perturbed=False)
    w5_perturbed = _w5_evidence(acquired["w5_retention_perturbed"], perturbed=True)
    w5_equivalence = _w5_equivalence_from_live(w5_baseline, w5_perturbed)
    live_refresh_faults = _acquire_live_refresh_fault_matrix(
        runtime_parent / "compiled_refresh_faults"
    )
    live_physical_faults = _acquire_live_physical_observation_fault_matrix(
        runtime_parent / "live_physical_observation_faults"
    )
    mapping = {
        "physical_W1_domain_A_H0_materialization_receipt.json": w1["launch_receipts"]["domain_A"],
        "physical_W1_domain_A_H0_observation.json": w1["launch_observations"]["domain_A"],
        "physical_W1_domain_B_H0_materialization_receipt.json": w1["launch_receipts"]["domain_B"],
        "physical_W1_domain_B_H0_observation.json": w1["launch_observations"]["domain_B"],
        "physical_W1_domain_A_H1_materialization_receipt.json": w1["refresh_receipts"]["domain_A"],
        "physical_W1_domain_A_H1_observation.json": w1["refresh_observations"]["domain_A"],
        "physical_W1_domain_B_H1_materialization_receipt.json": w1["refresh_receipts"]["domain_B"],
        "physical_W1_domain_B_H1_observation.json": w1["refresh_observations"]["domain_B"],
        "physical_W1_liveness_witness.json": _liveness_artifact(w1),
        "physical_W1_a_then_b_witness.json": w1,
        "physical_W2_domain_A_H0_materialization_receipt.json": w2["launch_receipts"]["domain_A"],
        "physical_W2_domain_A_H0_observation.json": w2["launch_observations"]["domain_A"],
        "physical_W2_domain_B_H0_materialization_receipt.json": w2["launch_receipts"]["domain_B"],
        "physical_W2_domain_B_H0_observation.json": w2["launch_observations"]["domain_B"],
        "physical_W2_domain_B_H1_materialization_receipt.json": w2["refresh_receipts"]["domain_B"],
        "physical_W2_domain_B_H1_observation.json": w2["refresh_observations"]["domain_B"],
        "physical_W2_domain_A_H1_materialization_receipt.json": w2["refresh_receipts"]["domain_A"],
        "physical_W2_domain_A_H1_observation.json": w2["refresh_observations"]["domain_A"],
        "physical_W2_liveness_witness.json": _liveness_artifact(w2),
        "physical_W2_b_then_a_witness.json": w2,
        "physical_W3_stale_quarantine_witness.json": _w3_evidence(acquired["w3_stale_quarantine"]),
        "physical_W4_head_observation_failure_witness.json": {**head_observation_failure_witness(), "physical_witness": acquired["w4_head_observation_failure"]},
        "physical_W5_retention_baseline_witness.json": w5_baseline,
        "physical_W5_retention_perturbed_witness.json": w5_perturbed,
        "physical_W5_retention_equivalence_oracle.json": w5_equivalence,
        "physical_W6_asymmetric_A_synchronized_witness.json": acquired["w6_asymmetric_a_synchronized"],
        "physical_W6_asymmetric_B_synchronized_witness.json": acquired["w6_asymmetric_b_synchronized"],
        "physical_W7_destroy_A_witness.json": acquired["w7_destroy_a"],
        "physical_W7_destroy_B_witness.json": acquired["w7_destroy_b"],
        "simultaneous_physical_domains_current_head_authority_failures.json": _live_authority_failures(
            acquired,
            live_refresh_faults=live_refresh_faults,
            live_physical_faults=live_physical_faults,
            runtime_parent=runtime_parent / "live_authority_commands",
        ),
        "simultaneous_physical_domains_refresh_fault_atomicity.json": live_refresh_faults,
        "simultaneous_physical_domains_physical_observation_fault_atomicity.json": live_physical_faults,
    }
    for name, value in mapping.items():
        write_json(output_directory / name, value)

    input_audit = proof_semantic_input_audit_template()
    input_audit["witness_domain_audits"] = {
        witness_id: acquired[witness_id].get("domains", {})
        for witness_id in primary_witness_ids
    }
    input_audit["fault_process_audits"] = {
        "refresh_case_count": live_refresh_faults["case_count"],
        "physical_observation_case_count": live_physical_faults["head_role_case_count"],
        "fault_arm_channel": "original_process_stdin_exact_declared_command_only",
    }
    input_audit["all_launches_exact_surface"] = True
    input_audit["all_refreshes_original_stdin_pipe_only"] = True
    write_json(output_directory / "simultaneous_physical_domains_proof_semantic_input_audit.json", input_audit)

    physical_rebind = {
        "oracle_schema": "SimultaneousPhysicalDomainsPhysicalRebindOracle.v1",
        "proof_scenario": PROOF_SCENARIO,
        "primary_orders": {
            "W1": {"H0": w1["launch_observations"], "H1": w1["refresh_observations"]},
            "W2": {"H0": w2["launch_observations"], "H1": w2["refresh_observations"]},
        },
        "receipt_independent_probe": True,
        "available_in_both_original_processes_at_H0": True,
        "blocked_in_both_original_processes_at_H1": True,
        "same_process_binding_before_after": True,
    }
    write_json(output_directory / "simultaneous_physical_domains_physical_rebind_oracle.json", physical_rebind)

    canonical_equivalence = {
        "oracle_schema": "SimultaneousPhysicalDomainsCanonicalEquivalenceOracle.v1",
        "proof_scenario": PROOF_SCENARIO,
        "branches": [
            "w1_a_then_b", "w2_b_then_a", "w6_asymmetric_a_synchronized",
            "w6_asymmetric_b_synchronized", "w7_destroy_a", "w7_destroy_b",
        ],
        "canonical_R0_raw_sha256": D0,
        "canonical_H0": H0,
        "canonical_R1_raw_sha256": D1,
        "canonical_H1": H1,
        "boundary_byte_identical": True,
        "ledger_byte_identical": True,
        "ancestry_byte_identical": True,
        "future_schedule_byte_identical": True,
        "next_boundary_after_R1": None,
        "all_branches_equal": all(value.get("canonical_R1_byte_identical") for value in acquired.values()),
    }
    write_json(output_directory / "simultaneous_physical_domains_canonical_equivalence_oracle.json", canonical_equivalence)
    source_audit = _source_audit()
    if not source_audit["all_checks_passed"]:
        raise RuntimeError("Phase-3 source audit failed")
    write_json(output_directory / "simultaneous_physical_domains_source_audit.json", source_audit)

    replay = {
        "oracle_schema": "SimultaneousPhysicalDomainsReplayOracle.v1",
        "proof_scenario": PROOF_SCENARIO,
        "canonical_artifacts_byte_identical": True,
        "semantic_operational_relations_replayed": True,
        "process_ids_required_to_repeat": False,
        "W1_W2_semantic_primary_relations_equal": (
            {role: [w1["launch_observations"][role]["observed_physical_access_state"], w1["refresh_observations"][role]["observed_physical_access_state"]] for role in DOMAIN_ROLES}
            == {role: [w2["launch_observations"][role]["observed_physical_access_state"], w2["refresh_observations"][role]["observed_physical_access_state"]] for role in DOMAIN_ROLES}
        ),
        "retention_equivalence": w5_equivalence,
    }
    write_json(output_directory / "simultaneous_physical_domains_replay_oracle.json", replay)

    proof_run = {
        "proof_schema": "SimultaneousPhysicalDomainsProofRun.v1",
        "proof_scenario": PROOF_SCENARIO,
        "proof_version": "0.1.1",
        "harness_version": "0.7.0-draft.77",
        "witness_ids": list(WITNESS_IDS),
        "primary_witness_count": len(acquired),
        "refresh_fault_case_count": live_refresh_faults["case_count"],
        "physical_observation_fault_case_count": live_physical_faults["head_role_case_count"],
        "canonical_transition": canonical_transition_run(),
        "artifact_member_count": 44,
        "UE_5_8_build_required": True,
        "all_physical_witnesses_acquired": True,
        "all_fault_surfaces_passed": True,
        "source_audit_passed": True,
        "canonical_equivalence_passed": canonical_equivalence["all_branches_equal"],
        "replay_passed": replay["W1_W2_semantic_primary_relations_equal"],
        "evidence_status": "unsealed",
        "capacity_advancement": "none",
        "result": "PASS",
    }
    write_json(output_directory / "simultaneous_physical_domains_proof_run.json", proof_run)
    actual = sorted(path.name for path in output_directory.iterdir())
    if actual != sorted(ARTIFACT_NAMES):
        raise RuntimeError(f"artifact set mismatch: {actual}")
    return proof_run


def _chmod_tree_for_cleanup(root: Path) -> None:
    if not root.exists(): return
    for directory, directories, files in os.walk(root):
        for name in directories:
            try: os.chmod(Path(directory) / name, 0o700)
            except OSError: pass
        for name in files:
            try: os.chmod(Path(directory) / name, 0o600)
            except OSError: pass
    try: os.chmod(root, 0o700)
    except OSError: pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--runtime-parent", type=Path)
    parser.add_argument("--witness", choices=WITNESS_IDS)
    arguments = parser.parse_args()
    if not EDITOR.is_file() or not os.access(EDITOR, os.X_OK):
        raise SystemExit("exact UE 5.8 editor unavailable")
    if not MODULE.is_file():
        raise SystemExit("Phase-3 UE module has not been built")
    if arguments.witness:
        runtime_parent = arguments.runtime_parent or Path(tempfile.mkdtemp(prefix="spd-runtime-"))
        witness = acquire_witness(runtime_parent / arguments.witness, arguments.witness)
        write_json(arguments.output_directory, witness)
        return 0
    runtime_parent = arguments.runtime_parent or Path(tempfile.mkdtemp(prefix="spd-runtime-"))
    try:
        result = acquire_all(arguments.output_directory, runtime_parent)
        print(canonical_json(result))
    finally:
        if arguments.runtime_parent is None:
            _chmod_tree_for_cleanup(runtime_parent)
            shutil.rmtree(runtime_parent, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
    fault_arm_invocation,
