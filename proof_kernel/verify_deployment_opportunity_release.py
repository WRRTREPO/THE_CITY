"""Create and verify the self-excluding release for deployment opportunity v0.1.0."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from deployment_opportunity import (
    DEPLOY_B,
    DEPLOY_C,
    DEPLOY_D,
    PHYSICAL_CONTRACTS,
    make_physical_proposal,
    record_hash,
    run_branch,
    serializable_record,
    write_branch_artifacts,
    write_interaction_records,
)
from kernel import canonical_json


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROOF_RECORDS = PROJECT_ROOT / "CityMaterializationProof" / "Content" / "ProofRecords"
MANIFEST = PROJECT_ROOT / "Crew Deployment Opportunity-Cost Proof - v0.1.0 SHA256SUMS.txt"

SOURCE_PATHS = (
    ".gitignore",
    "Crew Deployment Opportunity-Cost Proof - Draft.md",
    "Crew Deployment Opportunity-Cost Proof Evidence - v0.1.0.md",
    "Co-op Open-City FPS Simulation - v0.7 Working Continuation.md",
    "proof_kernel/deployment_opportunity.py",
    "proof_kernel/test_deployment_opportunity.py",
    "proof_kernel/test_kernel.py",
    "proof_kernel/test_roundtrip.py",
    "proof_kernel/test_contention.py",
    "proof_kernel/test_unreal_authority_boundary.py",
    "proof_kernel/verify_deployment_opportunity_release.py",
    "CityMaterializationProof/Source/CityMaterializationProof/CrewOperationPoint.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CrewOperationPoint.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationActor.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationActor.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofCharacter.cpp",
    "CityMaterializationProof/README.md",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_paths() -> tuple[str, ...]:
    paths = [
        "CityMaterializationProof/Content/ProofRecords/deployment_B_interaction_pre.json",
        "CityMaterializationProof/Content/ProofRecords/deployment_C_interaction_pre.json",
        "CityMaterializationProof/Content/ProofRecords/physical_contain_fire_B_deployment_0001.json",
        "CityMaterializationProof/Content/ProofRecords/physical_disrupt_seizure_C_deployment_0001.json",
    ]
    paths.extend(
        f"CityMaterializationProof/Content/ProofRecords/deployment_{destination}_{kind}.json"
        for destination in (DEPLOY_B, DEPLOY_C, DEPLOY_D)
        for kind in ("R0", "final", "ledger", "run")
    )
    return tuple(paths)


def release_paths() -> tuple[str, ...]:
    return tuple(sorted(SOURCE_PATHS + _artifact_paths()))


def _load_serialized_record(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    supplied_hash = value.pop("canonical_sha256", None)
    if supplied_hash != record_hash(value):
        raise ValueError(f"{path} has an invalid canonical_sha256")
    return value


def _captured_proposal(destination: str) -> dict[str, Any]:
    contract = PHYSICAL_CONTRACTS[destination]
    filename = "physical_contain_fire_B_deployment_0001.json" if destination == DEPLOY_B else "physical_disrupt_seizure_C_deployment_0001.json"
    proposal = json.loads((PROOF_RECORDS / filename).read_text(encoding="utf-8"))
    pre_filename = f"deployment_{destination}_interaction_pre.json"
    pre = _load_serialized_record(PROOF_RECORDS / pre_filename)
    expected = make_physical_proposal(destination, record_hash(pre))
    if proposal != expected:
        raise ValueError(f"captured {contract['proposal_id']} is not the exact frozen Unreal evidence contract")
    return proposal


def _verify_branch_artifacts(destination: str, proposal: dict[str, Any] | None) -> None:
    expected = run_branch(destination, proposal)
    run_path = PROOF_RECORDS / f"deployment_{destination}_run.json"
    actual_run = json.loads(run_path.read_text(encoding="utf-8"))
    if canonical_json(actual_run) != canonical_json(expected):
        raise ValueError(f"{destination} run artifact is not reproducible from the sealed source and proposal")
    r0 = _load_serialized_record(PROOF_RECORDS / f"deployment_{destination}_R0.json")
    final = _load_serialized_record(PROOF_RECORDS / f"deployment_{destination}_final.json")
    ledger = json.loads((PROOF_RECORDS / f"deployment_{destination}_ledger.json").read_text(encoding="utf-8"))
    if r0 != expected["r0"] or final != expected["final_record"] or ledger != expected["ledger"]:
        raise ValueError(f"{destination} split artifacts drift from its sealed run")
    if record_hash(r0) != record_hash(expected["r0"]):
        raise ValueError(f"{destination} has the wrong R0")
    transactions = actual_run["transactions"]
    if transactions[0]["header"]["parent_record_hash"] != record_hash(r0):
        raise ValueError(f"{destination} deployment does not name R0 as its parent")
    for prior, later in zip(transactions, transactions[1:]):
        if later["header"]["parent_record_hash"] != prior["ledger"][0]["working_post_state_hash"]:
            raise ValueError(f"{destination} scheduler ancestry is discontinuous")
        if later["header"]["boundary_derivation"] != "scheduler_clock_advance":
            raise ValueError(f"{destination} later transaction lacks scheduler derivation")


def _verify_branch_outcomes() -> None:
    b = _load_serialized_record(PROOF_RECORDS / "deployment_B_final.json")
    c = _load_serialized_record(PROOF_RECORDS / "deployment_C_final.json")
    d = _load_serialized_record(PROOF_RECORDS / "deployment_D_final.json")
    if not (b["areas"]["B"]["fire_containment"] and b["routes"]["E_AB"]["open"] and b["agents"]["police_unit_01"]["location"] == "C" and b["areas"]["C"]["owner"] == "contested"):
        raise ValueError("B branch does not prove fire answer → police response → contested C")
    if not (c["areas"]["C"]["crew_disruption"] and c["areas"]["B"]["fire_intensity"] == 5 and not c["routes"]["E_AB"]["open"] and c["areas"]["C"]["owner"] == "contested"):
        raise ValueError("C branch does not prove remote fire history plus local seizure disruption")
    if not (d["deployment"]["interaction_domain"] == "D" and d["world"]["active_world"] and d["areas"]["B"]["fire_intensity"] == 5 and d["areas"]["C"]["owner"] == "gang" and d["areas"]["C"]["gang_control"] == 74):
        raise ValueError("D branch does not prove unattended city progression")


def write_release() -> None:
    """Regenerate records from captured UE proposals, then make a self-excluding manifest."""

    write_interaction_records(PROOF_RECORDS)
    b_proposal = _captured_proposal(DEPLOY_B)
    c_proposal = _captured_proposal(DEPLOY_C)
    write_branch_artifacts(DEPLOY_B, PROOF_RECORDS, b_proposal)
    write_branch_artifacts(DEPLOY_C, PROOF_RECORDS, c_proposal)
    write_branch_artifacts(DEPLOY_D, PROOF_RECORDS)
    _verify_branch_artifacts(DEPLOY_B, b_proposal)
    _verify_branch_artifacts(DEPLOY_C, c_proposal)
    _verify_branch_artifacts(DEPLOY_D, None)
    _verify_branch_outcomes()
    manifest_relative = MANIFEST.relative_to(PROJECT_ROOT).as_posix()
    if manifest_relative in release_paths():
        raise AssertionError("release manifest must not contain its own identity")
    MANIFEST.write_text(
        "\n".join(f"{_sha256(PROJECT_ROOT / relative)}  {relative}" for relative in release_paths()) + "\n",
        encoding="utf-8",
    )


def verify_release() -> tuple[int, int]:
    """Verify exact members, hashes, captured evidence, replay, and branch facts."""

    manifest_relative = MANIFEST.relative_to(PROJECT_ROOT).as_posix()
    parsed: list[tuple[str, str]] = []
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        digest, separator, relative = line.partition("  ")
        if not separator or len(digest) != 64 or not relative:
            raise ValueError(f"invalid manifest line: {line!r}")
        if relative == manifest_relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise ValueError(f"invalid manifest member: {relative}")
        parsed.append((digest, relative))
    if tuple(relative for _, relative in parsed) != release_paths():
        raise ValueError("manifest members do not match the frozen release set")
    for expected_digest, relative in parsed:
        if _sha256(PROJECT_ROOT / relative) != expected_digest:
            raise ValueError(f"checksum mismatch: {relative}")
    b_proposal = _captured_proposal(DEPLOY_B)
    c_proposal = _captured_proposal(DEPLOY_C)
    _verify_branch_artifacts(DEPLOY_B, b_proposal)
    _verify_branch_artifacts(DEPLOY_C, c_proposal)
    _verify_branch_artifacts(DEPLOY_D, None)
    _verify_branch_outcomes()
    return len(parsed), len(parsed)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("write", "verify"))
    arguments = parser.parse_args()
    if arguments.command == "write":
        write_release()
    checked, total = verify_release()
    print(f"verified {checked}/{total} release artifacts; manifest excludes itself")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
