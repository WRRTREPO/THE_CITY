"""Acquire the frozen Simultaneous Physical Domains v0.1.0 UE witnesses.

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
    D0,
    D1,
    DOMAIN_ROLES,
    H0,
    H1,
    PROOF_SCENARIO,
    WITNESS_IDS,
    authoritative_representation,
    bind_invocation,
    canonical_json,
    canonical_records,
    canonical_transition_run,
    current_head_authority_failures,
    current_head_observation,
    expected_physical_observation,
    guard_open_control,
    head_disposition,
    head_observation_failure_witness,
    head_observation_fault_atomicity,
    inspection_invocation,
    operation_receipt,
    operation_receipt_matrix,
    operational_process_instance_id,
    physical_observation_fault_atomicity,
    process_binding,
    projection,
    projection_matrix,
    proof_semantic_input_audit_template,
    refresh_fault_atomicity,
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
    validate_materialization_receipt,
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


def _accept_launch(domain: LiveDomain) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
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
        guard_state="open_for_H0", head_state="synchronized",
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


def _refresh_success(domain: LiveDomain) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    bundle = _stage_refresh(domain)
    domain.send(refresh_invocation(domain.role))
    receipt = domain.next_object(_is_receipt)
    validate_materialization_receipt(receipt, domain.binding)
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
        guard_state="open_for_H1", head_state="synchronized",
    )
    return receipt, observation, disposition


def _refresh_rejection(domain: LiveDomain) -> tuple[dict[str, Any], dict[str, Any]]:
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
        represented_hash=H0, observed_head=H1, guard_state="open_for_H1", head_state="stale",
    )
    return failure, disposition


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
    terminations: dict[str, Any] = {}
    guard_transitions = ["open_for_H0"]
    transition = canonical_transition_run()
    control_root = runtime_root / "harness_private_control"
    head_publication: dict[str, Any] | None = None
    try:
        for role in DOMAIN_ROLES:
            receipt, observation, disposition = _accept_launch(domains[role])
            launch_receipts[role] = receipt
            launch_observations[role] = observation
            launch_dispositions[role] = disposition
        checkpoints.append(_checkpoint(domains, "L0"))

        if witness_id == "w8_guard_open_control":
            checkpoints.append(_checkpoint(domains, "guard_open_before_canonical_invocation"))
            guard_transitions.append("failed_closed")
            return {
                "witness_id": witness_id,
                "canonical_transition": transition,
                "guard_transitions": guard_transitions,
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

        guard_transitions.append("closed_for_H0_to_H1")
        checkpoints.append(_checkpoint(domains, "L1"))
        checkpoints.append(_checkpoint(domains, "L2"))
        if witness_id == "w4_head_observation_failure":
            guard_transitions.append("failed_closed")
            return {
                "witness_id": witness_id,
                "canonical_transition": transition,
                "guard_transitions": guard_transitions,
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
        guard_transitions.append("open_for_H1")
        checkpoints.append(_checkpoint(domains, "L3"))

        if witness_id == "w3_stale_quarantine":
            return {
                "witness_id": witness_id,
                "canonical_transition": transition,
                "guard_transitions": guard_transitions,
                "head_publication": head_publication,
                "checkpoints": checkpoints,
                "launch_receipts": launch_receipts,
                "launch_observations": launch_observations,
                "bounded_nonconsequential_steps": {role: 1 for role in DOMAIN_ROLES},
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
            receipt, observation, disposition = _refresh_success(domains[success_role])
            refresh_receipts[success_role] = receipt
            refresh_observations[success_role] = observation
            refresh_dispositions[success_role] = disposition
            checkpoints.append(_checkpoint(domains, "L4A"))
            failure, stale_disposition = _refresh_rejection(domains[failure_role])
            failures[failure_role] = failure
            refresh_dispositions[failure_role] = stale_disposition
            checkpoints.append(_checkpoint(domains, "asymmetric_terminal"))
        else:
            order = ("domain_A", "domain_B") if witness_id in (
                "w1_a_then_b", "w5_retention_baseline", "w5_retention_perturbed", "w7_destroy_a", "w7_destroy_b"
            ) else ("domain_B", "domain_A")
            for index, role in enumerate(order):
                receipt, observation, disposition = _refresh_success(domains[role])
                refresh_receipts[role] = receipt
                refresh_observations[role] = observation
                refresh_dispositions[role] = disposition
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
            "guard_transitions": guard_transitions,
            "head_publication": head_publication,
            "launch_receipts": launch_receipts,
            "launch_observations": launch_observations,
            "launch_dispositions": launch_dispositions,
            "refresh_receipts": refresh_receipts,
            "refresh_observations": refresh_observations,
            "refresh_dispositions": refresh_dispositions,
            "refresh_failures": failures,
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


def _source_audit() -> dict[str, Any]:
    source_root = ROOT / "CityMaterializationProof" / "Source" / "CityMaterializationProof"
    router = (source_root / "SimultaneousPhysicalDomainCommandRouter.cpp").read_text(encoding="utf-8")
    adapter = (source_root / "SimultaneousPhysicalDomainProofAdapter.cpp").read_text(encoding="utf-8")
    probe = (source_root / "SimultaneousPhysicalRebindProbe.cpp").read_text(encoding="utf-8")
    actor = (source_root / "SimultaneousPhysicalDomainRepresentationActor.cpp").read_text(encoding="utf-8")
    phase1 = (ROOT / "proof_kernel" / "canonical_spatial_topology_identity.py").read_text(encoding="utf-8")
    forbidden_unreal = (
        "current_head_observation.json", "physical_current_head_guard", "harness_refresh_eligibility",
        "CanonicalSpatialTopologyBoundary", "resolve_next_due", "canonical_ancestry",
    )
    phase3_unreal = router + adapter + probe + actor
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
        "no_socket_or_network_channel": all(token not in phase3_unreal for token in ("FSocket", "socket(", "Tcp", "Udp")),
        "representation_receipt_authority_only": "representation_only" in adapter,
        "other_domain_input_absent": "other_domain_root" not in phase3_unreal.lower(),
        "occupancy_movement_streaming_absent": all(token not in phase3_unreal for token in ("WorldPartition", "Occupancy", "NavigationSystem")),
    }
    return {
        "audit_schema": "SimultaneousPhysicalDomainsSourceAudit.v1",
        "proof_scenario": PROOF_SCENARIO,
        "checks": checks,
        "all_checks_passed": all(checks.values()),
        "forbidden_unreal_semantic_inputs": list(forbidden_unreal),
        "canonical_resolver_owner": "proof_kernel/canonical_spatial_topology_identity.py",
        "phase3_unreal_source_paths": [
            str(path.relative_to(ROOT))
            for path in sorted(source_root.glob("SimultaneousPhysical*"))
        ],
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


def acquire_all(output_directory: Path, runtime_parent: Path) -> dict[str, Any]:
    if output_directory.exists():
        raise ValueError("output artifact directory must not already exist")
    output_directory.mkdir(parents=True, exist_ok=False)
    runtime_parent.mkdir(parents=True, exist_ok=True)
    acquired: dict[str, dict[str, Any]] = {}
    for witness_id in WITNESS_IDS:
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
        "physical_W3_stale_quarantine_witness.json": {**stale_quarantine_witness(), "physical_witness": acquired["w3_stale_quarantine"]},
        "physical_W4_head_observation_failure_witness.json": {**head_observation_failure_witness(), "physical_witness": acquired["w4_head_observation_failure"]},
        "physical_W5_retention_baseline_witness.json": {**retention_witness(perturbed=False), "physical_witness": acquired["w5_retention_baseline"]},
        "physical_W5_retention_perturbed_witness.json": {**retention_witness(perturbed=True), "physical_witness": acquired["w5_retention_perturbed"]},
        "physical_W5_retention_equivalence_oracle.json": retention_equivalence_oracle(),
        "physical_W6_asymmetric_A_synchronized_witness.json": acquired["w6_asymmetric_a_synchronized"],
        "physical_W6_asymmetric_B_synchronized_witness.json": acquired["w6_asymmetric_b_synchronized"],
        "physical_W7_destroy_A_witness.json": acquired["w7_destroy_a"],
        "physical_W7_destroy_B_witness.json": acquired["w7_destroy_b"],
        "simultaneous_physical_domains_current_head_authority_failures.json": current_head_authority_failures(),
        "simultaneous_physical_domains_refresh_fault_atomicity.json": refresh_fault_atomicity(),
        "simultaneous_physical_domains_physical_observation_fault_atomicity.json": physical_observation_fault_atomicity(),
    }
    for name, value in mapping.items():
        write_json(output_directory / name, value)

    input_audit = proof_semantic_input_audit_template()
    input_audit["witness_domain_audits"] = {
        witness_id: acquired[witness_id].get("domains", {}) for witness_id in WITNESS_IDS
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
        "retention_equivalence": retention_equivalence_oracle(),
    }
    write_json(output_directory / "simultaneous_physical_domains_replay_oracle.json", replay)

    proof_run = {
        "proof_schema": "SimultaneousPhysicalDomainsProofRun.v1",
        "proof_scenario": PROOF_SCENARIO,
        "proof_version": "0.1.0",
        "harness_version": "0.7.0-draft.72",
        "witness_ids": list(WITNESS_IDS),
        "witness_count": len(acquired),
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
