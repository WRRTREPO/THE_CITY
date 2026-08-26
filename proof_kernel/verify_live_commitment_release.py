"""Create and verify the self-excluding live-commitment proof release."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from kernel import canonical_json
from live_commitment import (
    BRANCH_CONTROL, BRANCH_EARLY, BRANCH_LATE, CLAIM_ID,
    make_physical_proposal, prepare_arrival_record, prepare_post_claim_record,
    record_hash, run_branch, serializable_record, write_branch_artifacts,
    write_pre_records,
)

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "CityMaterializationProof" / "Content" / "ProofRecords"
MANIFEST = ROOT / "Crew Arrival Into Live Commitment Proof - v0.1.0 SHA256SUMS.txt"

SOURCE_PATHS = (
    "Crew Arrival Into Live Commitment Proof - Draft.md",
    "Crew Arrival Into Live Commitment Proof Evidence - v0.1.0.md",
    "Co-op Open-City FPS Simulation - v0.7 Working Continuation.md",
    "proof_kernel/kernel.py", "proof_kernel/roundtrip.py", "proof_kernel/live_commitment.py",
    "proof_kernel/test_live_commitment.py", "proof_kernel/test_unreal_authority_boundary.py",
    "proof_kernel/verify_live_commitment_release.py",
    "CityMaterializationProof/Source/CityMaterializationProof/LiveCommitmentRelayPoint.h",
    "CityMaterializationProof/Source/CityMaterializationProof/LiveCommitmentRelayPoint.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationActor.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationActor.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CityProofCharacter.cpp",
    "CityMaterializationProof/README.md",
)

def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()

def _artifacts() -> tuple[str, ...]:
    records = [
        "CityMaterializationProof/Content/ProofRecords/live_commitment_Rarrival.json",
        "CityMaterializationProof/Content/ProofRecords/live_commitment_post_claim_pre.json",
        "CityMaterializationProof/Content/ProofRecords/physical_disable_claim_relay_C_live_0001.json",
        "CityMaterializationProof/Content/ProofRecords/physical_disable_claim_relay_C_live_0002.json",
    ]
    records.extend(
        f"CityMaterializationProof/Content/ProofRecords/live_commitment_{branch}_{kind}.json"
        for branch in (BRANCH_CONTROL, BRANCH_EARLY, BRANCH_LATE)
        for kind in ("R0", "final", "ledger", "run")
    )
    return tuple(records)

def release_paths() -> tuple[str, ...]:
    return tuple(sorted(SOURCE_PATHS + _artifacts()))

def _load_record(name: str) -> dict[str, Any]:
    value = json.loads((RECORDS / name).read_text(encoding="utf-8"))
    supplied = value.pop("canonical_sha256", None)
    if supplied != record_hash(value):
        raise ValueError(f"invalid canonical hash: {name}")
    return value

def _proposal(name: str, state: str, record: dict[str, Any]) -> dict[str, Any]:
    captured = json.loads((RECORDS / name).read_text(encoding="utf-8"))
    expected = make_physical_proposal(state, record_hash(record))
    if captured != expected:
        raise ValueError(f"captured proposal is not exact Unreal evidence: {name}")
    return captured

def _verify_branch(branch: str, proposal: dict[str, Any] | None) -> None:
    expected = run_branch(branch, proposal)
    actual = json.loads((RECORDS / f"live_commitment_{branch}_run.json").read_text(encoding="utf-8"))
    if canonical_json(actual) != canonical_json(expected):
        raise ValueError(f"{branch} run is not reproducible")
    if _load_record(f"live_commitment_{branch}_R0.json") != expected["r0"]:
        raise ValueError(f"{branch} R0 drift")
    if _load_record(f"live_commitment_{branch}_final.json") != expected["final_record"]:
        raise ValueError(f"{branch} final drift")
    ledger = json.loads((RECORDS / f"live_commitment_{branch}_ledger.json").read_text(encoding="utf-8"))
    if ledger != expected["ledger"]:
        raise ValueError(f"{branch} ledger drift")
    for prior, later in zip(actual["transactions"], actual["transactions"][1:]):
        if later["header"]["parent_record_hash"] != prior["ledger"][0]["working_post_state_hash"]:
            raise ValueError(f"{branch} transaction ancestry is discontinuous")

def _verify_outcomes() -> None:
    control = _load_record("live_commitment_control_final.json")
    early = _load_record("live_commitment_early_final.json")
    late = _load_record("live_commitment_late_final.json")
    if not (control["areas"]["C"]["owner"] == "gang" and control["areas"]["C"]["relay"]["active"] and control["commitments"][CLAIM_ID]["state"] == "succeeded"):
        raise ValueError("control branch is not canonical claim success")
    if not (early["areas"]["C"]["owner"] == "contested" and not early["areas"]["C"]["relay"]["active"] and early["commitments"][CLAIM_ID]["state"] == "failed"):
        raise ValueError("early branch is not pre-boundary claim prevention")
    if not (late["areas"]["C"]["owner"] == "gang" and not late["areas"]["C"]["relay"]["active"] and late["commitments"][CLAIM_ID]["state"] == "succeeded" and (late["areas"]["C"]["gang_control"], late["areas"]["C"]["rival_control"]) == (72, 28)):
        raise ValueError("late branch reopened settled ownership or failed relay mutation")

def write_release() -> None:
    write_pre_records(RECORDS)
    arrival = _load_record("live_commitment_Rarrival.json")
    settled = _load_record("live_commitment_post_claim_pre.json")
    early = _proposal("physical_disable_claim_relay_C_live_0001.json", "active", arrival)
    late = _proposal("physical_disable_claim_relay_C_live_0002.json", "succeeded", settled)
    write_branch_artifacts(BRANCH_CONTROL, RECORDS)
    write_branch_artifacts(BRANCH_EARLY, RECORDS, early)
    write_branch_artifacts(BRANCH_LATE, RECORDS, late)
    _verify_branch(BRANCH_CONTROL, None)
    _verify_branch(BRANCH_EARLY, early)
    _verify_branch(BRANCH_LATE, late)
    _verify_outcomes()
    own = MANIFEST.relative_to(ROOT).as_posix()
    if own in release_paths():
        raise AssertionError("manifest cannot contain itself")
    MANIFEST.write_text("\n".join(f"{_sha(ROOT / path)}  {path}" for path in release_paths()) + "\n", encoding="utf-8")

def verify_release() -> tuple[int, int]:
    own = MANIFEST.relative_to(ROOT).as_posix()
    parsed = []
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        digest, sep, path = line.partition("  ")
        if not sep or len(digest) != 64 or not path or path == own or Path(path).is_absolute() or ".." in Path(path).parts:
            raise ValueError(f"invalid manifest entry: {line!r}")
        parsed.append((digest, path))
    if tuple(path for _, path in parsed) != release_paths():
        raise ValueError("manifest membership drift")
    for digest, path in parsed:
        if _sha(ROOT / path) != digest:
            raise ValueError(f"checksum mismatch: {path}")
    arrival = _load_record("live_commitment_Rarrival.json")
    settled = _load_record("live_commitment_post_claim_pre.json")
    _verify_branch(BRANCH_CONTROL, None)
    _verify_branch(BRANCH_EARLY, _proposal("physical_disable_claim_relay_C_live_0001.json", "active", arrival))
    _verify_branch(BRANCH_LATE, _proposal("physical_disable_claim_relay_C_live_0002.json", "succeeded", settled))
    _verify_outcomes()
    return len(parsed), len(parsed)

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("write", "verify"))
    args = parser.parse_args()
    if args.command == "write":
        write_release()
    checked, total = verify_release()
    print(f"verified {checked}/{total} release artifacts; manifest excludes itself")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
