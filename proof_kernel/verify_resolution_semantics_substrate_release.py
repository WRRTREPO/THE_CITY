"""Create and verify the self-excluding resolution-semantics substrate release."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from kernel import canonical_json
from resolution_semantics_substrate import (
    DUE_WORK_ID,
    REJECTION_AUTHORITATIVE_LOSS,
    REJECTION_AUTHORITATIVE_MUTATION,
    REJECTION_BOUNDARY_MISMATCH,
    canonical_hash,
    initial_canonical_envelope,
    proof_run,
    write_artifacts,
)


ROOT = Path(__file__).resolve().parents[1]
RECORDS = Path(__file__).resolve().parent / "ResolutionSemanticsSubstrateProofRecords"
MANIFEST = ROOT / "Resolution Semantics Substrate Proof - v0.1.0 SHA256SUMS.txt"

SOURCE_PATHS = (
    "README.md",
    "Resolution Semantics Law - v0.1.1.md",
    "Resolution Semantics Substrate Proof - Draft.md",
    "Resolution Semantics Substrate Proof Evidence - v0.1.0.md",
    "Co-op Open-City FPS Simulation - v0.7 Working Continuation.md",
    "proof_kernel/kernel.py",
    "proof_kernel/resolution_semantics_substrate.py",
    "proof_kernel/test_resolution_semantics_substrate.py",
    "proof_kernel/verify_resolution_semantics_substrate_release.py",
)


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_paths() -> tuple[str, ...]:
    return tuple(
        f"proof_kernel/ResolutionSemanticsSubstrateProofRecords/{name}"
        for name in (
            "resolution_substrate_R0.json",
            "resolution_substrate_run.json",
            "resolution_substrate_witnesses.json",
            "resolution_substrate_adversarial.json",
            "resolution_substrate_source_audit.json",
        )
    )


def release_paths() -> tuple[str, ...]:
    return tuple(sorted(SOURCE_PATHS + _artifact_paths()))


def _load(name: str) -> Any:
    return json.loads((RECORDS / name).read_text(encoding="utf-8"))


def _verify_artifacts() -> None:
    expected_r0 = initial_canonical_envelope()
    expected_run = proof_run()
    r0 = _load("resolution_substrate_R0.json")
    run = _load("resolution_substrate_run.json")
    witnesses = _load("resolution_substrate_witnesses.json")
    adversarial = _load("resolution_substrate_adversarial.json")
    audit = _load("resolution_substrate_source_audit.json")

    if canonical_json(r0) != canonical_json(expected_r0):
        raise ValueError("R0 cannot be regenerated from the frozen payload schema")
    if canonical_json(run) != canonical_json(expected_run):
        raise ValueError("proof run cannot be regenerated from the frozen substrate")
    if witnesses != expected_run["witnesses"]:
        raise ValueError("neutrality witness drift")
    if adversarial != expected_run["adversarial_dispositions"]:
        raise ValueError("adversarial disposition drift")
    if audit != expected_run["source_audit"]:
        raise ValueError("source audit drift")

    expected_boundary = {"decision_time": "t1/00", "due_work_ids": [DUE_WORK_ID]}
    boundaries = witnesses["boundary_identity"]
    if any(boundary != expected_boundary for boundary in boundaries.values()):
        raise ValueError("resolution-local state changed canonical boundary discovery")
    for witness_name in ("promotion_neutrality", "demotion_neutrality", "demotion_promotion_round_trip"):
        witness = witnesses[witness_name]
        if not (witness["projection_byte_identical"] and witness["canonical_hash_before"] == witness["canonical_hash_after"]):
            raise ValueError(f"{witness_name} changed authoritative projection")
    if witnesses["demotion_neutrality"]["local_cache"] != {}:
        raise ValueError("demotion retained resolution-local cache")
    if witnesses["demotion_promotion_round_trip"]["final_promoted_cache"]["commitment_alpha"]["next_gate_display"] != "t1/00":
        raise ValueError("round-trip promotion did not derive the frozen local cache")

    if adversarial["promotion_creates_authority"]["disposition"] != REJECTION_AUTHORITATIVE_MUTATION:
        raise ValueError("promotion authority creation did not fail closed")
    if adversarial["demotion_drops_authority"]["disposition"] != REJECTION_AUTHORITATIVE_LOSS:
        raise ValueError("demotion authority loss did not fail closed")
    if any(result["disposition"] != REJECTION_BOUNDARY_MISMATCH for result in adversarial["policy_changes_boundary"].values()):
        raise ValueError("boundary override did not fail closed")
    if any(
        item["authoritative_causal_ledger_appended"] or item["future_schedule_created"]
        for item in (
            adversarial["promotion_creates_authority"],
            adversarial["demotion_drops_authority"],
            *adversarial["policy_changes_boundary"].values(),
        )
    ):
        raise ValueError("adversarial disposition leaked into canonical authority")
    if run["r0_canonical_hash"] != canonical_hash(expected_r0):
        raise ValueError("R0 canonical hash drift")


def write_release() -> None:
    write_artifacts(RECORDS)
    _verify_artifacts()
    own = MANIFEST.relative_to(ROOT).as_posix()
    if own in release_paths():
        raise AssertionError("manifest cannot contain itself")
    MANIFEST.write_text(
        "\n".join(f"{_sha(ROOT / path)}  {path}" for path in release_paths()) + "\n",
        encoding="utf-8",
    )


def verify_release() -> tuple[int, int]:
    own = MANIFEST.relative_to(ROOT).as_posix()
    parsed: list[tuple[str, str]] = []
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        digest, separator, path = line.partition("  ")
        if not separator or len(digest) != 64 or not path or path == own or Path(path).is_absolute() or ".." in Path(path).parts:
            raise ValueError(f"invalid manifest member: {line!r}")
        parsed.append((digest, path))
    if tuple(path for _, path in parsed) != release_paths():
        raise ValueError("manifest membership drift")
    for digest, path in parsed:
        if _sha(ROOT / path) != digest:
            raise ValueError(f"checksum mismatch: {path}")
    _verify_artifacts()
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
