"""Create and verify Concurrent External Evidence Arbitration v0.1.0.

Canonical artifacts are regenerated from the frozen implementation. Physical
Unreal artifacts are imported evidence: this verifier may validate them but
must never create, repair, or infer them.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from kernel import canonical_json
from concurrent_external_evidence_arbitration import (
    ARTIFACT_NAMES,
    DOMAIN_TABLE,
    INPUT_A,
    INPUT_B,
    all_witness_runs,
    canonical_hash,
    construct_bext_from_sealed_fixture_set,
    control_runs,
    equivalence_oracle,
    evidence_emission_receipt,
    external_evidence_q,
    fail_closed_results,
    initial_canonical_envelope,
    launch_receipt,
    materialization_acceptance_receipt,
    primary_fixture,
    proof_run,
    q_hash,
    q_raw_sha256,
    raw_payload_sha256,
    self_check,
    source_audit,
    stored_payload_bytes,
    stored_q_bytes,
    write_artifacts,
)


ROOT = Path(__file__).resolve().parents[1]
RECORDS = Path(__file__).with_name("ConcurrentExternalEvidenceArbitrationProofRecords")
EVIDENCE = ROOT / "Concurrent External Evidence Arbitration Proof Evidence - v0.1.0.md"
MANIFEST = ROOT / "Concurrent External Evidence Arbitration Proof - v0.1.0 SHA256SUMS.txt"

SOURCE_PATHS = (
    "README.md",
    "Concurrent External Evidence Arbitration Proof - Draft.md",
    "Concurrent External Evidence Arbitration Proof Evidence - v0.1.0.md",
    "Co-op Open-City FPS Simulation - v0.7 Working Continuation.md",
    "THE_CITY Current Proof State and Repo-Agent Instruction - v0.1.0.md",
    "THE_CITY Development Capacity and Progress Note - v0.1.9.md",
    "External Input Boundary Proof Evidence - v0.1.1.md",
    "Shared-State Commitment Interference Proof Evidence - v0.1.0.md",
    "Record-Relative Chronological Resolution Proof Evidence - v0.1.0.md",
    "Integrated Unreal Promotion-Unload-Repromotion Proof Evidence - v0.1.0.md",
    "proof_kernel/kernel.py",
    "proof_kernel/concurrent_external_evidence_arbitration.py",
    "proof_kernel/concurrent_external_evidence_arbitration_harness.py",
    "proof_kernel/test_concurrent_external_evidence_arbitration.py",
    "proof_kernel/verify_concurrent_external_evidence_arbitration_release.py",
    "CityMaterializationProof/CityMaterializationProof.uproject",
    "CityMaterializationProof/Config/DefaultEngine.ini",
    "CityMaterializationProof/Config/DefaultInput.ini",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationProof.Build.cs",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofCharacter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofCharacter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofGameMode.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofGameMode.h",
    "CityMaterializationProof/Source/CityMaterializationProof/ConcurrentEvidenceSurface.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/ConcurrentEvidenceSurface.h",
    "CityMaterializationProof/Source/CityMaterializationProof/ConcurrentExternalEvidenceProofAdapter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/ConcurrentExternalEvidenceProofAdapter.h",
)


def _physical_names() -> tuple[str, ...]:
    names: list[str] = []
    for witness in ("W1", "W2", "W3", "W4"):
        prefix = f"physical_{witness}"
        for domain in ("domain_A", "domain_B"):
            names.extend(
                (
                    f"{prefix}_{domain}_Q.json",
                    f"{prefix}_{domain}_materialization_receipt.json",
                    f"{prefix}_{domain}_emission_receipt.json",
                    f"{prefix}_{domain}_process.log",
                    f"{prefix}_{domain}_input_audit.json",
                    f"{prefix}_{domain}_output_audit.json",
                )
            )
        names.extend((f"{prefix}_overlap_witness.json", f"{prefix}_termination_witness.json", f"{prefix}_lifecycle_witness.json"))
    return tuple(names)


PHYSICAL_ARTIFACTS = _physical_names()


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load(name: str) -> Any:
    return json.loads((RECORDS / name).read_text(encoding="utf-8"))


def _materialization_receipt_from_log(name: str) -> dict[str, Any]:
    marker = "CONCURRENT_MATERIALIZATION_RECEIPT:"
    receipts: list[dict[str, Any]] = []
    for line in (RECORDS / name).read_text(encoding="utf-8").splitlines():
        if marker in line:
            receipts.append(json.loads(line.partition(marker)[2]))
    if len(receipts) != 1:
        raise ValueError(f"UE log must contain one materialization receipt: {name}")
    return receipts[0]


def _physical_interaction_timestamp_from_log(name: str, domain: str) -> tuple[int, ...]:
    pattern = re.compile(
        rf"\[(\d{{4}})\.(\d{{2}})\.(\d{{2}})-(\d{{2}})\.(\d{{2}})\.(\d{{2}}):(\d{{3}})\]"
        rf".*Concurrent physical evidence emitted for {re.escape(domain)}\."
    )
    matches = [
        tuple(int(part) for part in match.groups())
        for match in pattern.finditer((RECORDS / name).read_text(encoding="utf-8"))
    ]
    if len(matches) != 1:
        raise ValueError(f"UE log must contain one timestamped physical interaction: {name}")
    return matches[0]


def _expected_canonical_artifacts() -> dict[str, Any]:
    proof = proof_run()
    runs = proof["witness_runs"]
    controls = proof["controls"]
    primary_members = runs["W1"]["canonical_checkpoints"]["R1"]["causal_provenance"]["authoritative_causal_ledger"][0]["members"]
    qa_control_member = controls["QA_only"]["successor"]["causal_provenance"]["authoritative_causal_ledger"][0]["members"][0]
    qb_control_member = controls["QB_only"]["successor"]["causal_provenance"]["authoritative_causal_ledger"][0]["members"][0]
    return {
        "concurrent_external_R0.json": proof["R0"],
        "concurrent_external_QA.json": proof["QA"],
        "concurrent_external_QB.json": proof["QB"],
        "concurrent_external_launch_receipt_R0.json": launch_receipt(proof["R0"]),
        "concurrent_external_primary_fixture.json": primary_fixture(),
        "concurrent_external_qa_only_fixture.json": controls["QA_only"]["fixture"],
        "concurrent_external_qb_only_fixture.json": controls["QB_only"]["fixture"],
        "concurrent_external_primary_BEXT.json": proof["primary_BEXT"],
        "concurrent_external_P0.json": primary_members[0]["working_pre_state_identity"],
        "concurrent_external_PA.json": primary_members[0]["working_post_state_identity"],
        "concurrent_external_PB.json": qb_control_member["working_post_state_identity"],
        "concurrent_external_R1.json": proof["R1"],
        "concurrent_external_Rcontrol_QA.json": controls["QA_only"]["successor"],
        "concurrent_external_Rcontrol_QB.json": controls["QB_only"]["successor"],
        "concurrent_external_W1_run.json": runs["W1"],
        "concurrent_external_W2_run.json": runs["W2"],
        "concurrent_external_W3_run.json": runs["W3"],
        "concurrent_external_W4_run.json": runs["W4"],
        "concurrent_external_QA_only_control_run.json": controls["QA_only"],
        "concurrent_external_QB_only_control_run.json": controls["QB_only"],
        "concurrent_external_oracle.json": proof["equivalence_oracle"],
        "concurrent_external_runtime_fail_closed.json": proof["fail_closed"],
        "concurrent_external_source_audit.json": proof["source_audit"],
        "concurrent_external_proof_run.json": proof,
    }


def verify_canonical() -> None:
    expected = _expected_canonical_artifacts()
    if tuple(expected) != ARTIFACT_NAMES:
        raise ValueError("canonical artifact membership differs from frozen release contract")
    for name, value in expected.items():
        if canonical_json(_load(name)) != canonical_json(value):
            raise ValueError(f"canonical artifact cannot be regenerated: {name}")

    check = self_check()
    if check["result"] != "passed" or check["witnesses"] != 4 or check["controls"] != 2:
        raise ValueError("canonical self-check did not establish frozen witness matrix")
    runs = all_witness_runs()
    if equivalence_oracle(runs)["result"] != "accepted":
        raise ValueError("W1-W4 canonical equivalence failed")
    reference = runs["W1"]
    for name, run in runs.items():
        for key in (
            "canonical_checkpoints", "sealed_fixture_candidate_set", "admitted_members_by_input_id",
            "BEXT", "canonical_member_order", "member_gate_observations", "provisional_identities",
        ):
            if canonical_json(run[key]) != canonical_json(reference[key]):
                raise ValueError(f"{name} authoritative checkpoint differs: {key}")

    r0 = initial_canonical_envelope()
    r1 = reference["canonical_checkpoints"]["R1"]
    if r1["causal_provenance"]["canonical_ancestry"] != {
        "parent_record_hash": canonical_hash(r0), "boundary_derivation": "external_arbitration_batch"
    }:
        raise ValueError("R1 does not have singular H0 ancestry")
    ledger = r1["causal_provenance"]["authoritative_causal_ledger"]
    if len(ledger) != 1 or len(ledger[0]["members"]) != 2:
        raise ValueError("batch did not publish exactly one ordered ledger entry")
    qa_result, qb_result = ledger[0]["members"]
    if qa_result["adjudication_disposition"] != "mutation_committed" or qb_result["adjudication_disposition"] != "failed_gate":
        raise ValueError("member adjudication disposition drift")
    if qb_result["resource_disposition"] != "no_resource_acquired" or qb_result["working_pre_state_identity"] != qb_result["working_post_state_identity"]:
        raise ValueError("failed-gate member changed working authority or acquired a resource")
    for identity in (qa_result["working_pre_state_identity"], qa_result["working_post_state_identity"]):
        if not isinstance(identity, dict) or identity.get("identity_kind") != "provisional_external_batch_working_state":
            raise ValueError("provisional identity is not mechanically type-disjoint")
    failures = fail_closed_results()
    if not failures or not all(
        result["canonical_unchanged"]
        and not result["canonical_successor_published"]
        and not result["canonical_replay_barrier_published"]
        for result in failures.values()
    ):
        raise ValueError("a rejected attempt leaked canonical authority")
    required_faults = {
        "fault_after_qa_provisional_mutation", "fault_after_qb_ordinary_gate_evaluation",
        "fault_during_replay_barrier_construction", "fault_during_batch_ledger_construction",
        "fault_after_complete_r1_before_validation", "fault_after_complete_r1_validation_before_publication",
    }
    if not required_faults.issubset(failures):
        raise ValueError("six-point atomicity witness surface is incomplete")
    audit = source_audit()
    if not audit["passed"]:
        raise ValueError("canonical source audit failed")


def _expected_input_audit(domain: str, process_id: str) -> dict[str, Any]:
    return {
        "materialization_domain": domain,
        "process_instance_id": process_id,
        "proof_input_files": [
            {"name": "canonical_payload_R0.json", "raw_byte_sha256": raw_payload_sha256(initial_canonical_envelope())},
            {"name": "launch_receipt_R0.json", "raw_byte_sha256": _sha(RECORDS / "concurrent_external_launch_receipt_R0.json")},
        ],
        "execution_context": {"interaction_opportunity": "t0/30", "materialization_domain": domain},
        "other_domain_paths_visible": False,
        "other_domain_paths_in_launch_arguments": False,
        "other_domain_paths_in_launch_environment": False,
        "launch_environment_values_exported": False,
        "shared_writable_proof_state": False,
        "shared_writable_proof_path_configured": False,
        "authority_bearing_selectors_present": False,
        "runtime_root_isolated": True,
    }


def _expected_output_audit(domain: str, q_name: str, receipt_name: str) -> dict[str, Any]:
    return {
        "materialization_domain": domain,
        "allowed_files": [
            {"name": DOMAIN_TABLE[domain]["input_id"] + ".json", "raw_byte_sha256": _sha(RECORDS / q_name)},
            {"name": DOMAIN_TABLE[domain]["input_id"] + ".emission_receipt.json", "raw_byte_sha256": _sha(RECORDS / receipt_name)},
        ],
        "other_domain_paths_visible": False,
        "shared_writable_proof_state": False,
    }


def verify_physical_witnesses() -> None:
    r0 = initial_canonical_envelope()
    expected_q = {"domain_A": external_evidence_q(r0, "domain_A"), "domain_B": external_evidence_q(r0, "domain_B")}
    matrix = {
        "W1": ([INPUT_A, INPUT_B], [INPUT_A, INPUT_B]),
        "W2": ([INPUT_B, INPUT_A], [INPUT_A, INPUT_B]),
        "W3": ([INPUT_A, INPUT_B], [INPUT_B, INPUT_A]),
        "W4": ([INPUT_B, INPUT_A], [INPUT_B, INPUT_A]),
    }
    process_ids: set[str] = set()
    pids: set[int] = set()
    for witness, (emission_order, presentation_order) in matrix.items():
        prefix = f"physical_{witness}"
        physical_log_times: dict[str, tuple[int, ...]] = {}
        for domain in ("domain_A", "domain_B"):
            q_name = f"{prefix}_{domain}_Q.json"
            if (RECORDS / q_name).read_bytes() != stored_q_bytes(expected_q[domain]):
                raise ValueError(f"physical Q is not exact frozen evidence: {q_name}")
            materialization_name = f"{prefix}_{domain}_materialization_receipt.json"
            emission_name = f"{prefix}_{domain}_emission_receipt.json"
            log_name = f"{prefix}_{domain}_process.log"
            materialization = _load(materialization_name)
            process_id = materialization.get("process_instance_id")
            if not isinstance(process_id, str) or not process_id or process_id in process_ids:
                raise ValueError("physical process identities must be nonempty and unique")
            process_ids.add(process_id)
            if materialization != materialization_acceptance_receipt(r0, domain, process_id):
                raise ValueError(f"materialization receipt drift: {materialization_name}")
            if _materialization_receipt_from_log(log_name) != materialization:
                raise ValueError(f"materialization receipt/log mismatch: {log_name}")
            emission = _load(emission_name)
            if emission != evidence_emission_receipt(r0, expected_q[domain], domain, process_id):
                raise ValueError(f"emission receipt drift: {emission_name}")
            log = (RECORDS / log_name).read_text(encoding="utf-8")
            if f"Concurrent physical evidence emitted for {domain}." not in log:
                raise ValueError(f"UE log does not witness real physical interaction: {log_name}")
            physical_log_times[domain] = _physical_interaction_timestamp_from_log(log_name, domain)
            if _load(f"{prefix}_{domain}_input_audit.json") != _expected_input_audit(domain, process_id):
                raise ValueError(f"input isolation audit drift: {witness}/{domain}")
            if _load(f"{prefix}_{domain}_output_audit.json") != _expected_output_audit(domain, q_name, emission_name):
                raise ValueError(f"output isolation audit drift: {witness}/{domain}")

        if len(set(physical_log_times.values())) != 2:
            raise ValueError(f"physical interaction timestamps must be distinct: {witness}")
        observed_physical_order = [
            DOMAIN_TABLE[domain]["input_id"]
            for domain in sorted(physical_log_times, key=physical_log_times.__getitem__)
        ]
        if observed_physical_order != emission_order:
            raise ValueError(f"UE log timestamps contradict physical emission order: {witness}")

        overlap = _load(f"{prefix}_overlap_witness.json")
        if (
            overlap.get("witness") != witness
            or overlap.get("both_alive_before_first_interaction") is not True
            or overlap.get("materialization_receipts_complete_before_first_interaction") is not True
            or overlap.get("physical_emission_order") != emission_order
            or overlap.get("harness_presentation_order") != presentation_order
            or set(overlap.get("process_instance_ids", {})) != {"domain_A", "domain_B"}
            or set(overlap.get("source_process_pids", {})) != {"domain_A", "domain_B"}
        ):
            raise ValueError(f"invalid process overlap/order witness: {witness}")
        for process_id in overlap["process_instance_ids"].values():
            if process_id not in process_ids:
                raise ValueError(f"overlap witness references an unknown process: {witness}")
        for pid in overlap["source_process_pids"].values():
            if not isinstance(pid, int) or pid <= 0 or pid in pids:
                raise ValueError("physical PIDs must be positive and unique")
            pids.add(pid)
        termination = _load(f"{prefix}_termination_witness.json")
        if termination != {
            "witness": witness,
            "before": "construct_BEXT_from_sealed_fixture_set",
            "process_state": {"domain_A": "terminated", "domain_B": "terminated"},
            "proof_outputs_closed": True,
        }:
            raise ValueError(f"source processes were not closed before arbitration: {witness}")
        lifecycle = _load(f"{prefix}_lifecycle_witness.json")
        if lifecycle != {
            "witness": witness,
            "source_record_hash": canonical_hash(r0),
            "source_raw_payload_sha256": raw_payload_sha256(r0),
            "physical_input_ids": emission_order,
            "harness_presentation_order": presentation_order,
            "canonical_member_order": [INPUT_A, INPUT_B],
            "both_sources_isolated": True,
            "one_atomic_successor": True,
            "canonical_successor_hash": canonical_hash(all_witness_runs()[witness]["canonical_checkpoints"]["R1"]),
        }:
            raise ValueError(f"physical lifecycle summary drift: {witness}")


def canonical_source_audit() -> dict[str, bool]:
    adapter = (ROOT / "CityMaterializationProof/Source/CityMaterializationProof/ConcurrentExternalEvidenceProofAdapter.cpp").read_text(encoding="utf-8")
    surface = (ROOT / "CityMaterializationProof/Source/CityMaterializationProof/ConcurrentEvidenceSurface.cpp").read_text(encoding="utf-8")
    game_mode = (ROOT / "CityMaterializationProof/Source/CityMaterializationProof/CityProofGameMode.cpp").read_text(encoding="utf-8")
    character = (ROOT / "CityMaterializationProof/Source/CityMaterializationProof/CityProofCharacter.cpp").read_text(encoding="utf-8")
    harness = (ROOT / "proof_kernel/concurrent_external_evidence_arbitration_harness.py").read_text(encoding="utf-8")
    verifier = Path(__file__).read_text(encoding="utf-8")
    return {
        "adapter_validates_exact_raw_payload": "LoadExactStoredJson" in adapter and "payload is not the exact frozen concurrent R0" in adapter,
        "adapter_rejects_authority_selectors": all(token in adapter for token in ("ConcurrentEvidencePriority=", "ConcurrentEvidenceMemberOrder=", "ConcurrentEvidenceWinner=")),
        "adapter_emits_materialization_receipt_only": "CONCURRENT_MATERIALIZATION_RECEIPT:" in adapter and "resolve_external_batch" not in adapter,
        "surface_emits_exact_q_and_detached_receipt": "ConcurrentExternalEvidence.v1" in surface and "ConcurrentEvidenceEmissionReceipt.v1" in surface,
        "surface_cannot_write_canonical_record": "authoritative_causal_ledger" not in surface and "canonical_ancestry" not in surface,
        "surface_has_no_order_or_winner": all(token not in surface for token in ("member_order", "canonical_external_priority", "winner")),
        "game_mode_selects_representation_not_result": "AConcurrentExternalEvidenceProofAdapter" in game_mode and "ConcurrentEvidencePayload=" in game_mode,
        "character_routes_physical_interaction_only": "AConcurrentEvidenceSurface" in character and "TryAllocateByCrew" in character,
        "launch_environment_shared_by_audit_and_process": harness.count("environment = _launch_environment(root, domain)") == 2,
        "peer_paths_audited_in_arguments_and_environment": all(
            token in harness for token in (
                "other_domain_paths_in_launch_arguments",
                "other_domain_paths_in_launch_environment",
                "launch_environment_values_exported",
            )
        ),
        "physical_order_rederived_from_ue_log_time": all(
            token in verifier for token in (
                "_physical_interaction_timestamp_from_log",
                "UE log timestamps contradict physical emission order",
            )
        ),
    }


def release_paths() -> tuple[str, ...]:
    records = tuple(f"proof_kernel/ConcurrentExternalEvidenceArbitrationProofRecords/{name}" for name in ARTIFACT_NAMES + PHYSICAL_ARTIFACTS)
    return tuple(sorted(SOURCE_PATHS + records))


def write_release() -> int:
    write_artifacts(RECORDS)
    verify_canonical()
    verify_physical_witnesses()
    if not all(canonical_source_audit().values()):
        raise ValueError("Unreal source authority audit failed")
    own = MANIFEST.relative_to(ROOT).as_posix()
    if own in release_paths():
        raise AssertionError("manifest cannot contain itself")
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
    if not all(canonical_source_audit().values()):
        raise ValueError("Unreal source authority audit failed")
    return len(members)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("write-canonical", "canonical", "write-release", "verify"))
    args = parser.parse_args()
    if args.command == "write-canonical":
        write_artifacts(RECORDS)
        verify_canonical()
        print("verified canonical arbitration artifacts; physical UE evidence remains required")
        return 0
    if args.command == "canonical":
        verify_canonical()
        print("verified canonical arbitration artifacts; physical UE evidence remains required")
        return 0
    if args.command == "write-release":
        if not EVIDENCE.is_file():
            raise SystemExit("release evidence document is required before writing the manifest")
        count = write_release()
    else:
        if not EVIDENCE.is_file() or not MANIFEST.is_file():
            raise SystemExit("release verification unavailable: physical UE evidence has not been sealed")
        count = verify_release()
    print(f"verified {count}/{count} release artifacts; manifest excludes itself")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
