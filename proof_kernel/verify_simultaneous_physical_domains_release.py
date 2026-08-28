"""Write and verify the frozen self-excluding Phase-3 release manifest."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping

from simultaneous_physical_domains import (
    ARTIFACT_NAMES,
    D0,
    D1,
    DOMAIN_ROLES,
    H0,
    H1,
    HEAD_OBSERVATION_FAULT_POINTS,
    PHYSICAL_OBSERVATION_FAULT_STAGES,
    REFRESH_FAULT_STAGES,
    WITNESS_IDS,
    artifact_role_set_valid,
    canonical_json,
    canonical_transition_run,
    current_head_authority_failures,
    current_head_observation,
    guard_open_control,
    head_observation_failure_witness,
    head_observation_fault_atomicity,
    operation_receipt_matrix,
    physical_observation_fault_atomicity,
    projection_matrix,
    refresh_fault_atomicity,
    retention_equivalence_oracle,
    retention_witness,
    sha256_value,
    stale_quarantine_witness,
    stored_json_bytes,
    strict_load_stored_json,
    validate_materialization_receipt,
    validate_physical_observation,
    write_json,
)
from simultaneous_physical_domains_harness import _source_audit


ROOT = Path(__file__).resolve().parents[1]
RECORDS = Path(__file__).resolve().parent / "SimultaneousPhysicalDomainsProofRecords"
MANIFEST = ROOT / "Simultaneous Physical Domains Proof - v0.1.0 SHA256SUMS.txt"
EVIDENCE = ROOT / "Simultaneous Physical Domains Proof Evidence - v0.1.0.md"

GOVERNING_AND_PREDECESSOR_MEMBERS = (
    "README.md",
    "Resolution Semantics Law - v0.1.1.md",
    "Record-Relative Chronological Resolution Proof Evidence - v0.1.0.md",
    "Integrated Unreal Promotion-Unload-Repromotion Proof Evidence - v0.1.0.md",
    "Concurrent External Evidence Arbitration Proof Evidence - v0.1.0.md",
    "Canonical Spatial Topology Identity Proof - Draft.md",
    "Canonical Spatial Topology Identity Proof Evidence - v0.1.0.md",
    "Canonical Spatial Topology Identity Proof - v0.1.0 SHA256SUMS.txt",
    "Canonical Occupancy Transition Proof Evidence - v0.1.0.md",
    "Simultaneous Physical Domains Proof - Draft.md",
    "Simultaneous Physical Domains Proof Evidence - v0.1.0.md",
    "Co-op Open-City FPS Simulation - v0.7 Working Continuation.md",
    "THE_CITY Development Capacity and Progress Note - v0.1.11.md",
    "THE_CITY Developer Snapshot - v0.1.0.md",
    "THE_CITY Current Proof State and Repo-Agent Instruction - v0.1.0.md",
)

SEALED_CANONICAL_INPUT_MEMBERS = (
    "proof_kernel/CanonicalSpatialTopologyIdentityProofRecords/canonical_topology_R0.json",
    "proof_kernel/CanonicalSpatialTopologyIdentityProofRecords/canonical_topology_boundary_H0.json",
    "proof_kernel/CanonicalSpatialTopologyIdentityProofRecords/canonical_topology_R1.json",
)

PYTHON_SOURCE_MEMBERS = (
    "proof_kernel/kernel.py",
    "proof_kernel/canonical_spatial_topology_identity.py",
    "proof_kernel/simultaneous_physical_domains.py",
    "proof_kernel/simultaneous_physical_domains_harness.py",
    "proof_kernel/test_simultaneous_physical_domains.py",
    "proof_kernel/verify_simultaneous_physical_domains_release.py",
)

UNREAL_PROJECT_MEMBERS = (
    "CityMaterializationProof/CityMaterializationProof.uproject",
    "CityMaterializationProof/Config/DefaultEngine.ini",
    "CityMaterializationProof/Config/DefaultGame.ini",
    "CityMaterializationProof/Config/DefaultInput.ini",
    "CityMaterializationProof/README.md",
    "CityMaterializationProof/Source/CityMaterializationProof.Target.cs",
    "CityMaterializationProof/Source/CityMaterializationProofEditor.Target.cs",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationProof.Build.cs",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationProof.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationProof.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofGameMode.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofGameMode.h",
    "CityMaterializationProof/Source/CityMaterializationProof/BridgeAccessPoint.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/BridgeAccessPoint.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CanonicalSpatialTopologyProofAdapter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CanonicalSpatialTopologyProofAdapter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CanonicalTopologyRepresentationActor.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CanonicalTopologyRepresentationActor.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationActor.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationActor.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofCharacter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofCharacter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/ConcurrentEvidenceSurface.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/ConcurrentEvidenceSurface.h",
    "CityMaterializationProof/Source/CityMaterializationProof/ConcurrentExternalEvidenceProofAdapter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/ConcurrentExternalEvidenceProofAdapter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CrewOperationPoint.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CrewOperationPoint.h",
    "CityMaterializationProof/Source/CityMaterializationProof/IntegratedGateTokenPoint.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/IntegratedGateTokenPoint.h",
    "CityMaterializationProof/Source/CityMaterializationProof/IntegratedUnrealProofAdapter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/IntegratedUnrealProofAdapter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/LiveCommitmentRelayPoint.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/LiveCommitmentRelayPoint.h",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainCommandRouter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainCommandRouter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainProofAdapter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainProofAdapter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainRepresentationActor.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainRepresentationActor.h",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalRebindProbe.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalRebindProbe.h",
)

NON_ARTIFACT_MEMBERS = (
    GOVERNING_AND_PREDECESSOR_MEMBERS
    + SEALED_CANONICAL_INPUT_MEMBERS
    + PYTHON_SOURCE_MEMBERS
    + UNREAL_PROJECT_MEMBERS
)


def artifact_paths() -> tuple[str, ...]:
    return tuple(
        f"proof_kernel/SimultaneousPhysicalDomainsProofRecords/{name}"
        for name in ARTIFACT_NAMES
    )


def release_paths() -> tuple[str, ...]:
    paths = NON_ARTIFACT_MEMBERS + artifact_paths()
    if len(NON_ARTIFACT_MEMBERS) != 66 or len(paths) != 110 or len(set(paths)) != 110:
        raise AssertionError("frozen 44 + 66 = 110 member contract drift")
    return tuple(sorted(paths, key=lambda value: value.encode("utf-8")))


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _strict_member(path: Path) -> None:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"release member is not one regular non-symlink file: {path}")
    try:
        path.resolve(strict=True).relative_to(ROOT.resolve(strict=True))
    except ValueError as exc:
        raise ValueError(f"release member realpath escapes repository: {path}") from exc


def _load(name: str) -> dict[str, Any]:
    path = RECORDS / name
    raw = path.read_bytes()
    value = strict_load_stored_json(raw)
    if not isinstance(value, dict):
        raise ValueError(f"artifact is not an object: {name}")
    return value


def _expect_equal(name: str, expected: Mapping[str, Any]) -> None:
    actual = _load(name)
    if stored_json_bytes(actual) != stored_json_bytes(dict(expected)):
        raise ValueError(f"deterministic artifact regeneration mismatch: {name}")


def _verify_primary(order: str) -> dict[str, Any]:
    prefix = "physical_W1" if order == "W1" else "physical_W2"
    witness_name = f"{prefix}_{'a_then_b' if order == 'W1' else 'b_then_a'}_witness.json"
    witness = _load(witness_name)
    expected_witness_id = "w1_a_then_b" if order == "W1" else "w2_b_then_a"
    if witness.get("witness_id") != expected_witness_id or witness.get("launch_count") != 2 or witness.get("replacement_spawn_count") != 0:
        raise ValueError(f"{order} launch/binding witness drift")
    expected_order = ("domain_A", "domain_B") if order == "W1" else ("domain_B", "domain_A")
    command_order = [
        role for role in expected_order
        if witness["domains"][role]["stdin_commands"][2]["operation"] == "refresh_once"
    ]
    if tuple(command_order) != expected_order:
        raise ValueError(f"{order} refresh command order drift")
    for role in DOMAIN_ROLES:
        binding = witness["domains"][role]["binding"]
        h0_receipt = _load(f"{prefix}_{role}_H0_materialization_receipt.json")
        h0_observation = _load(f"{prefix}_{role}_H0_observation.json")
        h1_receipt = _load(f"{prefix}_{role}_H1_materialization_receipt.json")
        h1_observation = _load(f"{prefix}_{role}_H1_observation.json")
        validate_materialization_receipt(h0_receipt, binding)
        validate_materialization_receipt(h1_receipt, binding)
        validate_physical_observation(
            h0_observation, domain_role=role, head_role="H0", binding=binding,
            inspection_id="launch_physical_0001",
        )
        validate_physical_observation(
            h1_observation, domain_role=role, head_role="H1", binding=binding,
            inspection_id="refresh_physical_0001",
        )
        if h0_receipt != witness["launch_receipts"][role] or h1_receipt != witness["refresh_receipts"][role]:
            raise ValueError(f"{order}/{role} detached receipt does not match witness embedding")
        if h0_observation != witness["launch_observations"][role] or h1_observation != witness["refresh_observations"][role]:
            raise ValueError(f"{order}/{role} detached physical observation does not match witness")
        commands = witness["domains"][role]["stdin_commands"]
        if [command["operation"] for command in commands] != [
            "bind_process_once", "inspect_published_route_once", "refresh_once", "inspect_published_route_once"
        ]:
            raise ValueError(f"{order}/{role} command sequence drift")
        if witness["domains"][role]["head_observation_visible_to_unreal"] or witness["domains"][role]["physical_guard_visible_to_unreal"]:
            raise ValueError(f"{order}/{role} hidden harness input reached Unreal")
        if witness["domains"][role]["refresh_input_inventory_before"] != witness["domains"][role]["refresh_input_inventory_after"]:
            raise ValueError(f"{order}/{role} refresh input changed during read")
    liveness = _load(f"{prefix}_liveness_witness.json")
    if (
        liveness.get("required_checkpoints") != ["L0", "L1", "L2", "L3", "L4A", "L4B"]
        or liveness.get("observed_checkpoints") != ["L0", "L1", "L2", "L3", "L4A", "L4B"]
        or not liveness.get("pids_distinct")
        or not liveness.get("process_start_pairs_distinct")
        or not liveness.get("same_original_binding_at_all_checkpoints")
        or liveness.get("launch_count") != 2
        or liveness.get("replacement_spawn_count") != 0
        or not liveness.get("uninterrupted_simultaneous_liveness_proven")
    ):
        raise ValueError(f"{order} uninterrupted simultaneous liveness failed")
    return witness


def _verify_other_witnesses() -> None:
    w3 = _load("physical_W3_stale_quarantine_witness.json")
    if not all((
        w3["canonical_R1_raw_sha256_before"] == D1,
        w3["canonical_R1_raw_sha256_after"] == D1,
        w3["current_head_receipts_emitted"] == 0,
        w3["physical_witness"].get("refresh_invocations", 0) == 0,
    )):
        raise ValueError("W3 stale quarantine drift")
    w4 = _load("physical_W4_head_observation_failure_witness.json")
    physical_w4 = w4["physical_witness"]
    if (
        w4["injected_fault_point"] != "after_R1_H1_commit_verification_before_observation_construction"
        or w4["guard_terminal_state"] != "failed_closed"
        or physical_w4["head_observation_published"]
        or physical_w4["refresh_invocations"] != 0
        or set(physical_w4["terminal_states"].values()) != {"head_unconfirmed"}
    ):
        raise ValueError("W4 head-observation failure did not fail closed")
    baseline = _load("physical_W5_retention_baseline_witness.json")
    perturbed = _load("physical_W5_retention_perturbed_witness.json")
    oracle = _load("physical_W5_retention_equivalence_oracle.json")
    if (
        baseline["retained_local_state"] == perturbed["retained_local_state"]
        or not oracle["authoritative_derived_H1_byte_identical"]
        or not oracle["poison_discarded"]
    ):
        raise ValueError("W5 retained-local-state perturbation selected H1 truth")
    for name, success_role, stale_role in (
        ("physical_W6_asymmetric_A_synchronized_witness.json", "domain_A", "domain_B"),
        ("physical_W6_asymmetric_B_synchronized_witness.json", "domain_B", "domain_A"),
    ):
        witness = _load(name)
        if (
            witness["refresh_dispositions"][success_role]["head_state"] != "synchronized"
            or witness["refresh_dispositions"][stale_role]["head_state"] != "stale"
            or witness["refresh_failures"][stale_role]["represented_hash_if_known"] != H0
            or witness["refresh_dispositions"][stale_role]["current_head_claim_enabled"]
            or not witness["canonical_R1_byte_identical"]
        ):
            raise ValueError(f"asymmetric refresh atomicity failed: {name}")
    for name, destroyed, remaining in (
        ("physical_W7_destroy_A_witness.json", "domain_A", "domain_B"),
        ("physical_W7_destroy_B_witness.json", "domain_B", "domain_A"),
    ):
        witness = _load(name)
        post = next(item for item in witness["checkpoints"] if item["checkpoint"] == "post_destruction")
        if (
            destroyed not in witness["terminations"]
            or post["remaining_domain"]["domain_role"] != remaining
            or post["remaining_domain_head_state"] != "synchronized(H1)"
            or not post["canonical_H1_unchanged"]
        ):
            raise ValueError(f"destruction isolation failed: {name}")


def _verify_oracles(w1: Mapping[str, Any], w2: Mapping[str, Any]) -> None:
    _expect_equal("simultaneous_physical_domains_canonical_transition_run.json", canonical_transition_run())
    _expect_equal("simultaneous_physical_domains_projection_matrix.json", projection_matrix())
    _expect_equal("simultaneous_physical_domains_operation_receipt_matrix.json", operation_receipt_matrix())
    _expect_equal("simultaneous_physical_domains_current_head_observation.json", current_head_observation())
    _expect_equal("simultaneous_physical_domains_head_observation_fault_atomicity.json", head_observation_fault_atomicity())
    guard = _load("simultaneous_physical_domains_guard_open_canonical_control.json")
    expected_guard = guard_open_control()
    for key, value in expected_guard.items():
        if guard.get(key) != value:
            raise ValueError(f"guard-open control deterministic field drift: {key}")
    if (
        guard["physical_witness"]["guard_transitions"] != ["open_for_H0", "failed_closed"]
        or set(guard["physical_witness"]["terminal_dispositions"].values()) != {"protocol_invalid(H0/H1)"}
        or guard["physical_witness"]["refresh_invocations"] != 0
    ):
        raise ValueError("guard-open live canonical control drift")
    authority = _load("simultaneous_physical_domains_current_head_authority_failures.json")
    if authority != current_head_authority_failures() or authority["case_count"] != 37:
        raise ValueError("37 current-head authority rejection cases drift")
    refresh_faults = _load("simultaneous_physical_domains_refresh_fault_atomicity.json")
    if refresh_faults != refresh_fault_atomicity() or refresh_faults["fault_stages"] != list(REFRESH_FAULT_STAGES):
        raise ValueError("exact refresh pre/post fault surface drift")
    physical_faults = _load("simultaneous_physical_domains_physical_observation_fault_atomicity.json")
    if physical_faults != physical_observation_fault_atomicity() or physical_faults["fault_stages"] != list(PHYSICAL_OBSERVATION_FAULT_STAGES):
        raise ValueError("exact physical observation fault surface drift")
    head_faults = _load("simultaneous_physical_domains_head_observation_fault_atomicity.json")
    if head_faults["fault_points"] != list(HEAD_OBSERVATION_FAULT_POINTS):
        raise ValueError("exact head observation fault surface drift")
    input_audit = _load("simultaneous_physical_domains_proof_semantic_input_audit.json")
    if not all((
        input_audit["proof_semantic_closure_complete"],
        input_audit["all_launches_exact_surface"],
        input_audit["all_refreshes_original_stdin_pipe_only"],
        not input_audit["head_observation_visible_to_unreal"],
        not input_audit["physical_guard_visible_to_unreal"],
        input_audit["semantic_environment_keys"] == [],
        input_audit["semantic_command_line_selectors"] == [],
        input_audit["alternate_refresh_channels"] == [],
    )):
        raise ValueError("proof-semantic input closure failed")
    rebind = _load("simultaneous_physical_domains_physical_rebind_oracle.json")
    if not all((
        rebind["receipt_independent_probe"],
        rebind["available_in_both_original_processes_at_H0"],
        rebind["blocked_in_both_original_processes_at_H1"],
        rebind["same_process_binding_before_after"],
    )):
        raise ValueError("independent live UE rebind oracle failed")
    canonical_equivalence = _load("simultaneous_physical_domains_canonical_equivalence_oracle.json")
    if not canonical_equivalence["all_branches_equal"] or canonical_equivalence["canonical_R1_raw_sha256"] != D1:
        raise ValueError("canonical equivalence oracle failed")
    source = _load("simultaneous_physical_domains_source_audit.json")
    rerun_source = _source_audit()
    if source != rerun_source or not source["all_checks_passed"]:
        raise ValueError("source/dataflow audit failed or cannot be reproduced")
    replay = _load("simultaneous_physical_domains_replay_oracle.json")
    if not replay["canonical_artifacts_byte_identical"] or not replay["W1_W2_semantic_primary_relations_equal"]:
        raise ValueError("semantic replay oracle failed")
    proof_run = _load("simultaneous_physical_domains_proof_run.json")
    if (
        proof_run["result"] != "PASS"
        or proof_run["witness_ids"] != list(WITNESS_IDS)
        or proof_run["witness_count"] != 11
        or proof_run["artifact_member_count"] != 44
        or proof_run["evidence_status"] != "unsealed"
        or proof_run["capacity_advancement"] != "none"
    ):
        raise ValueError("top-level proof run drift")


def _isolated_role_regeneration() -> None:
    """Regenerate all 44 roles without pretending operational IDs repeat."""

    with tempfile.TemporaryDirectory(prefix="spd-release-replay-") as temporary:
        regenerated = Path(temporary) / "SimultaneousPhysicalDomainsProofRecords"
        regenerated.mkdir()
        deterministic = {
            ARTIFACT_NAMES[0]: canonical_transition_run(),
            ARTIFACT_NAMES[1]: projection_matrix(),
            ARTIFACT_NAMES[2]: operation_receipt_matrix(),
            ARTIFACT_NAMES[3]: current_head_observation(),
            ARTIFACT_NAMES[4]: head_observation_fault_atomicity(),
            ARTIFACT_NAMES[35]: current_head_authority_failures(),
            ARTIFACT_NAMES[36]: refresh_fault_atomicity(),
            ARTIFACT_NAMES[37]: physical_observation_fault_atomicity(),
        }
        for name in ARTIFACT_NAMES:
            payload = deterministic.get(name, _load(name))
            write_json(regenerated / name, payload)
        if not artifact_role_set_valid(regenerated):
            raise ValueError("isolated 44-role regeneration member set failed")
        for name, expected in deterministic.items():
            if (regenerated / name).read_bytes() != stored_json_bytes(expected):
                raise ValueError(f"isolated deterministic regeneration mismatch: {name}")


def _run_focused_tests() -> None:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPYCACHEPREFIX"] = "/private/tmp/thecity_pycache"
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "test_simultaneous_physical_domains.py"],
        cwd=ROOT / "proof_kernel", env=environment, capture_output=True, text=True,
    )
    if result.returncode != 0 or "Ran 33 tests" not in result.stderr or "OK" not in result.stderr:
        raise ValueError(f"focused Phase-3 tests failed:\n{result.stdout}\n{result.stderr}")


def verify_artifacts() -> None:
    if not artifact_role_set_valid(RECORDS):
        raise ValueError("artifact directory is not exact 44-member regular-file set")
    for name in ARTIFACT_NAMES:
        _strict_member(RECORDS / name)
        _load(name)
    w1 = _verify_primary("W1")
    w2 = _verify_primary("W2")
    _verify_other_witnesses()
    _verify_oracles(w1, w2)
    _isolated_role_regeneration()
    _run_focused_tests()


def write_release() -> int:
    if not EVIDENCE.is_file():
        raise FileNotFoundError("exact evidence document is required before manifest creation")
    verify_artifacts()
    own = MANIFEST.relative_to(ROOT).as_posix()
    if own in release_paths():
        raise AssertionError("manifest self-inclusion")
    for relative in release_paths():
        _strict_member(ROOT / relative)
    MANIFEST.write_text(
        "".join(f"{_sha(ROOT / relative)}  {relative}\n" for relative in release_paths()),
        encoding="utf-8",
    )
    return len(release_paths())


def verify_release() -> int:
    _strict_member(MANIFEST)
    raw = MANIFEST.read_bytes()
    if not raw.endswith(b"\n") or b"\r" in raw:
        raise ValueError("manifest line ending drift")
    parsed: list[tuple[str, str]] = []
    seen: set[str] = set()
    own = MANIFEST.relative_to(ROOT).as_posix()
    for raw_line in raw.decode("utf-8", errors="strict").splitlines():
        digest, separator, relative = raw_line.partition("  ")
        candidate = Path(relative)
        if (
            separator != "  " or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
            or not relative or relative in seen or relative == own
            or candidate.is_absolute() or ".." in candidate.parts
        ):
            raise ValueError(f"invalid manifest member: {raw_line!r}")
        seen.add(relative)
        parsed.append((digest, relative))
    if tuple(relative for _, relative in parsed) != release_paths():
        raise ValueError("manifest exact member order/set drift")
    for digest, relative in parsed:
        path = ROOT / relative
        _strict_member(path)
        if _sha(path) != digest:
            raise ValueError(f"manifest checksum mismatch: {relative}")
    verify_artifacts()
    return len(parsed)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("artifacts", "write-release", "verify"))
    arguments = parser.parse_args()
    if arguments.command == "artifacts":
        verify_artifacts()
        print("verified exact 44/44 Phase-3 artifacts; evidence remains unsealed")
        return 0
    if arguments.command == "write-release":
        count = write_release()
    else:
        if not EVIDENCE.is_file() or not MANIFEST.is_file():
            raise SystemExit("release verification unavailable: evidence document or manifest missing")
        count = verify_release()
    print(f"verified {count}/{count} release members; manifest excludes itself; evidence remains unsealed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
