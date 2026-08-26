"""Create and verify the self-excluding release manifest for contention v0.1.0."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from contention import CASE_DESTRUCTION_FIRST, CASE_ENTRY_FIRST, write_case_artifacts


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROOF_RECORDS = PROJECT_ROOT / "CityMaterializationProof" / "Content" / "ProofRecords"
MANIFEST = PROJECT_ROOT / "Bridge Access Traversal Contention Proof - v0.1.1 SHA256SUMS.txt"

SOURCE_PATHS = (
    "Bridge Access Traversal Contention Proof - Draft.md",
    "Bridge Access Traversal Contention Proof Evidence - v0.1.0.md",
    "Bridge Access Traversal Contention Proof Evidence - v0.1.1.md",
    "Co-op Open-City FPS Simulation - v0.7 Working Continuation.md",
    "proof_kernel/contention.py",
    "proof_kernel/test_contention.py",
    "proof_kernel/roundtrip.py",
    "proof_kernel/test_roundtrip.py",
    "proof_kernel/test_kernel.py",
    "proof_kernel/test_unreal_authority_boundary.py",
    "proof_kernel/verify_contention_release.py",
    "CityMaterializationProof/Source/CityMaterializationProof/BridgeAccessPoint.h",
    "CityMaterializationProof/Source/CityMaterializationProof/BridgeAccessPoint.cpp",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationActor.h",
    "CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationActor.cpp",
    "CityMaterializationProof/README.md",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_paths() -> tuple[str, ...]:
    generated = tuple(
        f"CityMaterializationProof/Content/ProofRecords/{case}_{kind}.json"
        for case in (CASE_DESTRUCTION_FIRST, CASE_ENTRY_FIRST)
        for kind in ("R0", "intermediate", "final", "ledger", "run")
    )
    return generated + ("CityMaterializationProof/Content/ProofRecords/physical_destroy_E_AB_contention_0001.json",)


def release_paths() -> tuple[str, ...]:
    return tuple(sorted(SOURCE_PATHS + _artifact_paths()))


def write_release() -> None:
    """Regenerate canonical inputs, then create a manifest which never hashes itself."""

    physical_path = PROOF_RECORDS / "physical_destroy_E_AB_contention_0001.json"
    if not physical_path.is_file():
        raise FileNotFoundError("the release requires the captured Unreal physical proposal")
    physical_proposal = json.loads(physical_path.read_text(encoding="utf-8"))
    for case in (CASE_DESTRUCTION_FIRST, CASE_ENTRY_FIRST):
        write_case_artifacts(case, PROOF_RECORDS, physical_proposal)

    if MANIFEST.relative_to(PROJECT_ROOT).as_posix() in release_paths():
        raise AssertionError("release manifest must not contain its own identity")
    lines = []
    for relative in release_paths():
        path = PROJECT_ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        lines.append(f"{_sha256(path)}  {relative}")
    MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8")


def verify_release() -> tuple[int, int]:
    """Verify every named member and reject a self-referential or drifting manifest."""

    manifest_relative = MANIFEST.relative_to(PROJECT_ROOT).as_posix()
    lines = [line for line in MANIFEST.read_text(encoding="utf-8").splitlines() if line]
    parsed: list[tuple[str, str]] = []
    for line in lines:
        digest, separator, relative = line.partition("  ")
        if not separator or len(digest) != 64 or not relative:
            raise ValueError(f"invalid manifest line: {line!r}")
        if relative == manifest_relative:
            raise ValueError("release manifest must not contain its own hash")
        if Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise ValueError(f"manifest path escapes project: {relative}")
        parsed.append((digest, relative))
    expected_paths = release_paths()
    actual_paths = tuple(relative for _, relative in parsed)
    if actual_paths != expected_paths:
        raise ValueError("manifest members do not match the frozen release set")
    for expected_digest, relative in parsed:
        actual_digest = _sha256(PROJECT_ROOT / relative)
        if actual_digest != expected_digest:
            raise ValueError(f"checksum mismatch: {relative}")
    return len(parsed), len(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("write", "verify"))
    args = parser.parse_args()
    if args.command == "write":
        write_release()
    checked, lines = verify_release()
    print(f"verified {checked}/{lines} release artifacts; manifest excludes itself")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
