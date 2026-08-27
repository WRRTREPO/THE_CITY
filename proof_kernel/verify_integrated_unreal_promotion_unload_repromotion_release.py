"""Create and verify the Integrated Unreal lifecycle proof release.

The canonical fixture is regenerated from the frozen resolver. Physical UE
witnesses are strictly imported by the lifecycle harness and can only be
validated here; this verifier never manufactures an Unreal receipt or Q.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from integrated_unreal_promotion_unload_repromotion import (
    ACTOR_ID,
    NO_EXECUTION_BOUNDARY,
    all_witness_runs,
    canonical_hash,
    equivalence_oracle,
    external_evidence_q,
    initial_canonical_envelope,
    materialization_acceptance_receipt,
    proof_run,
    raw_payload_sha256,
    runtime_fail_closed_results,
    source_audit,
    stored_payload_bytes,
    validate_acceptance_receipt,
    validate_launch_artifact,
    write_artifacts,
)
from kernel import canonical_json


ROOT = Path(__file__).resolve().parents[1]
RECORDS = Path(__file__).with_name("IntegratedUnrealPromotionUnloadRepromotionProofRecords")
EVIDENCE = ROOT / "Integrated Unreal Promotion-Unload-Repromotion Proof Evidence - v0.1.0.md"
MANIFEST = ROOT / "Integrated Unreal Promotion-Unload-Repromotion Proof - v0.1.0 SHA256SUMS.txt"

CANONICAL_ARTIFACTS = (
    "integrated_unreal_Q.json",
    "integrated_unreal_R0.json",
    "integrated_unreal_Rcontrol.json",
    "integrated_unreal_Rfinal.json",
    "integrated_unreal_Rinput.json",
    "integrated_unreal_dense_demote_jump_run.json",
    "integrated_unreal_dense_reference_run.json",
    "integrated_unreal_equivalence_oracle.json",
    "integrated_unreal_integrated_boundary_jump_run.json",
    "integrated_unreal_jump_promote_dense_run.json",
    "integrated_unreal_proof_run.json",
    "integrated_unreal_q_absent_control_run.json",
    "integrated_unreal_runtime_fail_closed.json",
    "integrated_unreal_source_audit.json",
    "launch_receipt_R0.json",
    "launch_receipt_Rcontrol.json",
    "launch_receipt_Rfinal.json",
    "launch_receipt_Rinput.json",
)

PHYSICAL_ARTIFACTS = (
    "physical_control_Rcontrol.json",
    "physical_control_launch_receipt_Rcontrol.json",
    "physical_control_preparation.json",
    "physical_control_return_acceptance_receipt.json",
    "physical_control_return_input_audit.json",
    "physical_control_return_process.log",
    "physical_control_source_acceptance_receipt.json",
    "physical_control_source_output_audit.json",
    "physical_control_source_process.log",
    "physical_control_source_termination_witness.json",
    "physical_integrated_unreal_lifecycle_witness.json",
    "physical_primary_Q.json",
    "physical_primary_Rfinal.json",
    "physical_primary_Rinput.json",
    "physical_primary_input_committed.json",
    "physical_primary_preparation.json",
    "physical_primary_return_acceptance_receipt.json",
    "physical_primary_return_input_audit.json",
    "physical_primary_return_process.log",
    "physical_primary_source_acceptance_receipt.json",
    "physical_primary_source_process.log",
    "physical_primary_source_termination_witness.json",
)

EXPORTED_PHYSICAL_ARTIFACTS = (
    "physical_primary_source_acceptance_receipt.json",
    "physical_primary_return_acceptance_receipt.json",
    "physical_primary_Q.json",
    "physical_primary_Rinput.json",
    "physical_primary_Rfinal.json",
    "physical_primary_preparation.json",
    "physical_primary_input_committed.json",
    "physical_primary_source_termination_witness.json",
    "physical_primary_return_input_audit.json",
    "physical_primary_source_process.log",
    "physical_primary_return_process.log",
    "physical_control_source_acceptance_receipt.json",
    "physical_control_return_acceptance_receipt.json",
    "physical_control_Rcontrol.json",
    "physical_control_launch_receipt_Rcontrol.json",
    "physical_control_preparation.json",
    "physical_control_source_output_audit.json",
    "physical_control_source_termination_witness.json",
    "physical_control_return_input_audit.json",
    "physical_control_source_process.log",
    "physical_control_return_process.log",
)

SOURCE_PATHS = (
    "README.md",
    "Integrated Unreal Promotion-Unload-Repromotion Proof - Draft.md",
    "Integrated Unreal Promotion-Unload-Repromotion Proof Evidence - v0.1.0.md",
    "Co-op Open-City FPS Simulation - v0.7 Working Continuation.md",
    "THE_CITY Current Proof State and Repo-Agent Instruction - v0.1.0.md",
    "THE_CITY Development Capacity and Progress Note - v0.1.8.md",
    "proof_kernel/kernel.py",
    "proof_kernel/integrated_unreal_promotion_unload_repromotion.py",
    "proof_kernel/integrated_unreal_lifecycle_harness.py",
    "proof_kernel/test_integrated_unreal_promotion_unload_repromotion.py",
    "proof_kernel/verify_integrated_unreal_promotion_unload_repromotion_release.py",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationProof.Build.cs",
    "CityMaterializationProof/CityMaterializationProof.uproject",
    "CityMaterializationProof/Config/DefaultEngine.ini",
    "CityMaterializationProof/Config/DefaultInput.ini",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofCharacter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofCharacter.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofGameMode.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofGameMode.h",
    "CityMaterializationProof/Source/CityMaterializationProof/IntegratedGateTokenPoint.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/IntegratedGateTokenPoint.h",
    "CityMaterializationProof/Source/CityMaterializationProof/IntegratedUnrealProofAdapter.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/IntegratedUnrealProofAdapter.h",
)


def _load(name: str) -> Any:
    return json.loads((RECORDS / name).read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _receipt_from_log(name: str) -> dict[str, Any]:
    marker = "INTEGRATED_MATERIALIZATION_RECEIPT:"
    receipts: list[dict[str, Any]] = []
    for line in (RECORDS / name).read_text(encoding="utf-8").splitlines():
        if marker in line:
            _, _, raw = line.partition(marker)
            receipts.append(json.loads(raw))
    if len(receipts) != 1:
        raise ValueError(f"process log must contain one structured receipt: {name}")
    return receipts[0]


def _expected_input_audit(
    visible_payload_name: str,
    payload_artifact_name: str,
    receipt_name: str,
    context: dict[str, str] | None,
    visible_receipt_name: str | None = None,
) -> dict[str, Any]:
    return {
        "allowed_files": [
            {"name": visible_payload_name, "raw_payload_sha256": _sha(RECORDS / payload_artifact_name)},
            {"name": visible_receipt_name or receipt_name, "raw_payload_sha256": _sha(RECORDS / receipt_name)},
        ],
        "execution_context": context,
    }


def _require_termination(name: str, expected_before: str) -> None:
    witness = _load(name)
    if set(witness) != {"before", "process_state", "source_process_pid"} or witness["before"] != expected_before or witness["process_state"] != "terminated" or not isinstance(witness["source_process_pid"], int) or witness["source_process_pid"] <= 0:
        raise ValueError(f"invalid termination witness: {name}")


def canonical_source_audit() -> dict[str, Any]:
    """Audit the new source paths, not legacy materialization fixtures."""

    adapter = (ROOT / "CityMaterializationProof/Source/CityMaterializationProof/IntegratedUnrealProofAdapter.cpp").read_text(encoding="utf-8")
    gate = (ROOT / "CityMaterializationProof/Source/CityMaterializationProof/IntegratedGateTokenPoint.cpp").read_text(encoding="utf-8")
    game_mode = (ROOT / "CityMaterializationProof/Source/CityMaterializationProof/CityProofGameMode.cpp").read_text(encoding="utf-8")
    return {
        "adapter_validates_raw_sha256_before_parse": "Sha256Hex(PayloadBytes.GetData(), PayloadBytes.Num())" in adapter,
        "adapter_emits_detached_acceptance_receipt": "INTEGRATED_MATERIALIZATION_RECEIPT:" in adapter,
        "adapter_has_no_canonical_resolver": "resolve_execution_boundary" not in adapter,
        "adapter_has_no_canonical_ledger_write": "authoritative_causal_ledger" not in adapter,
        "adapter_has_no_policy_selection": "next_execution_boundary" not in adapter,
        "gate_writes_only_q": "physical_disable_integrated_gate_token_0001.json" in gate and "committed_record" not in gate and "causal_ledger" not in gate,
        "gate_emits_exact_fixture_actor": ACTOR_ID in gate,
        "gate_q_uses_canonical_key_order": gate.find("\\\"proposed_mutations\\\"") < gate.find("\\\"protocol_version\\\""),
        "integrated_mode_bypasses_legacy_materializer": "AIntegratedUnrealProofAdapter" in game_mode and "IntegratedProofPayload=" in game_mode,
        "source_and_return_context_are_distinct": "IntegratedProofInteractionOpportunity=" in adapter and "bReturnRecord" in adapter,
    }


def verify_canonical() -> None:
    expected = proof_run()
    if canonical_json(_load("integrated_unreal_R0.json")) != canonical_json(expected["r0"]):
        raise ValueError("R0 cannot be regenerated from the frozen fixture")
    for label, expected_record in (("Rinput", expected["rinput"]), ("Rfinal", expected["rfinal"]), ("Rcontrol", expected["rcontrol"])):
        if canonical_json(_load(f"integrated_unreal_{label}.json")) != canonical_json(expected_record):
            raise ValueError(f"{label} cannot be regenerated from the frozen resolver")
    if canonical_json(_load("integrated_unreal_Q.json")) != canonical_json(expected["q"]):
        raise ValueError("frozen Q artifact drift")
    for name, run in expected["witness_runs"].items():
        if canonical_json(_load(f"integrated_unreal_{name}_run.json")) != canonical_json(run):
            raise ValueError(f"{name} run drift")
    if _load("integrated_unreal_equivalence_oracle.json") != expected["equivalence_oracle"]:
        raise ValueError("equivalence oracle drift")
    if _load("integrated_unreal_runtime_fail_closed.json") != expected["runtime_fail_closed"]:
        raise ValueError("runtime fail-closed artifact drift")
    if _load("integrated_unreal_source_audit.json") != expected["source_audit"]:
        raise ValueError("canonical source audit artifact drift")
    if canonical_json(_load("integrated_unreal_proof_run.json")) != canonical_json(expected):
        raise ValueError("canonical proof-run artifact drift")
    if equivalence_oracle(all_witness_runs()) != {"result": "accepted", "reference_witness": "dense_reference", "failures": []}:
        raise ValueError("dense and boundary-jump witnesses diverge")
    if expected["rfinal"]["causal_provenance"]["canonical_ancestry"]["parent_record_hash"] != canonical_hash(expected["rinput"]):
        raise ValueError("Rfinal ancestry is not Rinput-relative")
    if expected["rfinal"]["causal_provenance"]["authoritative_causal_ledger"][-1]["evaluated_gates"][0]["observed_value"] != "disabled":
        raise ValueError("alpha did not read Rinput gate state")
    if all_witness_runs()["dense_reference"]["next_execution_boundary"] != NO_EXECUTION_BOUNDARY:
        raise ValueError("Rfinal retains executable work")
    expected_failures = {
        "digest_changed_without_recompute",
        "redirected_with_recomputed_digest",
        "stale_bq",
        "stale_alpha",
        "local_authority",
    }
    if set(runtime_fail_closed_results()) != expected_failures:
        raise ValueError("runtime rejection surface drift")
    if not all(canonical_source_audit().values()):
        raise ValueError("UE authority source audit failed")


def verify_physical_witnesses() -> None:
    """Validate imported UE outputs against frozen record and receipt laws."""

    expected = proof_run()
    r0, q, rinput, rfinal, rcontrol = (expected[key] for key in ("r0", "q", "rinput", "rfinal", "rcontrol"))
    physical_q = (RECORDS / "physical_primary_Q.json").read_bytes()
    if physical_q != (canonical_json(q) + "\n").encode("utf-8"):
        raise ValueError("physical UE Q is not the exact frozen evidence envelope")
    for name, record in (
        ("physical_primary_Rinput.json", rinput),
        ("physical_primary_Rfinal.json", rfinal),
        ("physical_control_Rcontrol.json", rcontrol),
    ):
        if (RECORDS / name).read_bytes() != stored_payload_bytes(record):
            raise ValueError(f"physical checkpoint drift: {name}")
    if validate_launch_artifact(
        (RECORDS / "physical_control_Rcontrol.json").read_bytes(),
        (RECORDS / "physical_control_launch_receipt_Rcontrol.json").read_bytes(),
    ) != rcontrol:
        raise ValueError("control return launch artifact is not exact")

    receipts = {
        "physical_primary_source_acceptance_receipt.json": (r0, True, "source_process_01", "physical_primary_source_process.log"),
        "physical_primary_return_acceptance_receipt.json": (rfinal, False, "return_process_01", "physical_primary_return_process.log"),
        "physical_control_source_acceptance_receipt.json": (r0, True, "control_source_process_01", "physical_control_source_process.log"),
        "physical_control_return_acceptance_receipt.json": (rcontrol, False, "control_return_process_01", "physical_control_return_process.log"),
    }
    for artifact, (record, capability, process_id, log_name) in receipts.items():
        receipt = _load(artifact)
        validate_acceptance_receipt(record, receipt, capability)
        if receipt["process_instance_id"] != process_id or _receipt_from_log(log_name) != receipt:
            raise ValueError(f"receipt/log mismatch: {artifact}")
    if "Integrated physical gate disable; Q written." not in (RECORDS / "physical_primary_source_process.log").read_text(encoding="utf-8"):
        raise ValueError("primary source log does not witness physical Q emission")
    if "Integrated physical gate disable; Q written." in (RECORDS / "physical_control_source_process.log").read_text(encoding="utf-8"):
        raise ValueError("Q-absent control source emitted Q")

    if _load("physical_primary_preparation.json") != {
        "source_canonical_hash": canonical_hash(r0),
        "source_raw_payload_sha256": raw_payload_sha256(r0),
        "source_visible_input_audit": _expected_input_audit("canonical_payload_R0.json", "integrated_unreal_R0.json", "launch_receipt_R0.json", {"interaction_opportunity": "t0/30"}),
        "source_process_context": {"interaction_opportunity": "t0/30"},
    }:
        raise ValueError("primary source input/context audit drift")
    if _load("physical_control_preparation.json") != _load("physical_primary_preparation.json"):
        raise ValueError("control did not start from the same audited R0 input")
    bq = {
        "kind": "external_input",
        "source_record_hash": canonical_hash(r0),
        "decision_time": "t0/30",
        "simulation_phase": 0,
        "external_input_id": "physical_disable_integrated_gate_token_0001",
        "due_work_ids": [],
    }
    if _load("physical_primary_input_committed.json") != {
        "rinput_hash": canonical_hash(rinput),
        "bq": bq,
        "source_process_must_be_terminated_before": "next_execution_boundary(Rinput)",
    }:
        raise ValueError("primary input-commit witness drift")
    _require_termination("physical_primary_source_termination_witness.json", "next_execution_boundary(Rinput)")
    _require_termination("physical_control_source_termination_witness.json", "next_execution_boundary(Rinput)")
    if _load("physical_primary_return_input_audit.json") != _expected_input_audit("canonical_payload_Rfinal.json", "physical_primary_Rfinal.json", "launch_receipt_Rfinal.json", None):
        raise ValueError("primary return input audit drift")
    if _load("physical_control_return_input_audit.json") != _expected_input_audit("canonical_payload_Rcontrol.json", "physical_control_Rcontrol.json", "physical_control_launch_receipt_Rcontrol.json", None, "launch_receipt_Rcontrol.json"):
        raise ValueError("control return input audit drift")
    if _load("physical_control_source_output_audit.json") != {"allowed_files": []}:
        raise ValueError("control source output was not empty")
    summary = _load("physical_integrated_unreal_lifecycle_witness.json")
    if summary != {
        "primary": {"canonical_hashes": {"R0": canonical_hash(r0), "Rinput": canonical_hash(rinput), "Rfinal": canonical_hash(rfinal)}, "source_domains_removed_before_rediscovery": True},
        "control": {"canonical_hashes": {"R0": canonical_hash(r0), "Rcontrol": canonical_hash(rcontrol)}, "source_output_empty_before_continuation": True, "source_domains_removed_before_resolution": True},
        "artifact_names": list(EXPORTED_PHYSICAL_ARTIFACTS),
    }:
        raise ValueError("physical lifecycle summary drift")


def release_paths() -> tuple[str, ...]:
    records = tuple(f"proof_kernel/IntegratedUnrealPromotionUnloadRepromotionProofRecords/{name}" for name in CANONICAL_ARTIFACTS + PHYSICAL_ARTIFACTS)
    return tuple(sorted(SOURCE_PATHS + records))


def write_release() -> int:
    write_artifacts(RECORDS)
    verify_canonical()
    verify_physical_witnesses()
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
    for digest, relative_path in members:
        if _sha(ROOT / relative_path) != digest:
            raise ValueError(f"checksum mismatch: {relative_path}")
    verify_canonical()
    verify_physical_witnesses()
    return len(members)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("write-canonical", "canonical", "write-release", "verify"))
    args = parser.parse_args()
    if args.command == "write-canonical":
        write_artifacts(RECORDS)
        verify_canonical()
        print("verified canonical fixture artifacts; physical UE lifecycle evidence remains required")
        return 0
    verify_canonical()
    if args.command == "canonical":
        print("verified canonical fixture artifacts; physical UE lifecycle evidence remains required")
        return 0
    if args.command == "write-release":
        if not EVIDENCE.is_file():
            raise SystemExit("release evidence document is required before writing the manifest")
        count = write_release()
    else:
        if not EVIDENCE.is_file() or not MANIFEST.is_file():
            raise SystemExit("release verification unavailable: physical UE lifecycle evidence has not been sealed")
        count = verify_release()
    print(f"verified {count}/{count} release artifacts; manifest excludes itself")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
