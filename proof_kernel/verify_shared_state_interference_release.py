"""Create and verify the self-excluding shared-state interference release."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from kernel import canonical_json
from shared_state_interference import (
    COMMITMENT_X,
    COMMITMENT_Y,
    counterfactual_run,
    definition_hashes,
    permutation_run,
    primary_run,
    record_hash,
    write_run_artifacts,
)


ROOT = Path(__file__).resolve().parents[1]
RECORDS = Path(__file__).resolve().parent / "SharedStateInterferenceProofRecords"
MANIFEST = ROOT / "Shared-State Commitment Interference Proof - v0.1.0 SHA256SUMS.txt"

SOURCE_PATHS = (
    "Shared-State Commitment Interference Proof - Draft.md",
    "Shared-State Commitment Interference Proof Evidence - v0.1.0.md",
    "Co-op Open-City FPS Simulation - v0.7 Working Continuation.md",
    "proof_kernel/kernel.py",
    "proof_kernel/shared_state_interference.py",
    "proof_kernel/test_shared_state_interference.py",
    "proof_kernel/verify_shared_state_interference_release.py",
)


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_paths() -> tuple[str, ...]:
    return tuple(
        f"proof_kernel/SharedStateInterferenceProofRecords/shared_state_{name}_{kind}.json"
        for name in ("primary", "counterfactual", "permutation")
        for kind in ("R0", "final", "ledger", "run")
    )


def release_paths() -> tuple[str, ...]:
    return tuple(sorted(SOURCE_PATHS + _artifact_paths()))


def _load_record(name: str) -> dict[str, Any]:
    record = json.loads((RECORDS / name).read_text(encoding="utf-8"))
    supplied = record.pop("canonical_sha256", None)
    if supplied != record_hash(record):
        raise ValueError(f"canonical hash mismatch: {name}")
    return record


def _expected(name: str) -> dict[str, Any]:
    return {
        "primary": primary_run,
        "counterfactual": counterfactual_run,
        "permutation": permutation_run,
    }[name]()


def _verify_run(name: str) -> None:
    expected = _expected(name)
    actual = json.loads((RECORDS / f"shared_state_{name}_run.json").read_text(encoding="utf-8"))
    if canonical_json(actual) != canonical_json(expected):
        raise ValueError(f"{name} run cannot be regenerated from frozen resolver")
    if _load_record(f"shared_state_{name}_R0.json") != expected["r0"]:
        raise ValueError(f"{name} R0 drift")
    if _load_record(f"shared_state_{name}_final.json") != expected["final_record"]:
        raise ValueError(f"{name} final record drift")
    ledger = json.loads((RECORDS / f"shared_state_{name}_ledger.json").read_text(encoding="utf-8"))
    if ledger != expected["ledger"]:
        raise ValueError(f"{name} ledger drift")
    if expected["definition_audit"]["definition_hashes"] != definition_hashes():
        raise ValueError(f"{name} definition hash drift")


def _verify_outcomes() -> None:
    primary = _load_record("shared_state_primary_final.json")
    counterfactual = _load_record("shared_state_counterfactual_final.json")
    permutation = _load_record("shared_state_permutation_final.json")
    if not (
        primary["commitments"][COMMITMENT_X]["state"] == "succeeded"
        and primary["commitments"][COMMITMENT_Y]["state"] == "failed"
        and primary["shared_state"]["durable_allocations"][0]["committed_by"] == COMMITMENT_X
    ):
        raise ValueError("primary does not prove X-first shared-state interference")
    if not (
        counterfactual["commitments"][COMMITMENT_X]["state"] == "not_scheduled"
        and counterfactual["commitments"][COMMITMENT_Y]["state"] == "succeeded"
        and counterfactual["shared_state"]["durable_allocations"][0]["committed_by"] == COMMITMENT_Y
    ):
        raise ValueError("counterfactual does not prove Y success when X is absent")
    if not (
        permutation["commitments"][COMMITMENT_X]["state"] == "failed"
        and permutation["commitments"][COMMITMENT_Y]["state"] == "succeeded"
        and permutation["shared_state"]["durable_allocations"][0]["committed_by"] == COMMITMENT_Y
    ):
        raise ValueError("permutation does not prove order-driven shared-state contention")
    if not (
        primary["definition_hashes"] == counterfactual["definition_hashes"] == permutation["definition_hashes"] == definition_hashes()
    ):
        raise ValueError("definition hashes drift between fixtures")


def write_release() -> None:
    for name, run in (("primary", primary_run()), ("counterfactual", counterfactual_run()), ("permutation", permutation_run())):
        write_run_artifacts(name, run, RECORDS)
    for name in ("primary", "counterfactual", "permutation"):
        _verify_run(name)
    _verify_outcomes()
    own = MANIFEST.relative_to(ROOT).as_posix()
    if own in release_paths():
        raise AssertionError("manifest cannot contain itself")
    MANIFEST.write_text("\n".join(f"{_sha(ROOT / path)}  {path}" for path in release_paths()) + "\n", encoding="utf-8")


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
    for name in ("primary", "counterfactual", "permutation"):
        _verify_run(name)
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
