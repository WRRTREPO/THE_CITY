"""Create and verify the self-excluding occupancy-transition release."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from canonical_occupancy_transition import (
    ALL_FAULT_POINTS,
    ARTIFACT_NAMES,
    NO_BOUNDARY,
    OCCUPANT,
    RESERVATION,
    SITE_A,
    SITE_B,
    TRANSITION,
    artifact_payloads,
    canonical_hash,
    canonical_json,
    next_consequential_boundary,
    proof_run,
    transition_definition_projection,
    write_artifacts,
)


ROOT = Path(__file__).resolve().parents[1]
RECORDS = Path(__file__).resolve().parent / "CanonicalOccupancyTransitionProofRecords"
MANIFEST = ROOT / "Canonical Occupancy Transition Proof - v0.1.0 SHA256SUMS.txt"

SOURCE_PATHS = (
    "README.md",
    "Resolution Semantics Law - v0.1.1.md",
    "Causal-LOD Equivalence Proof Evidence - v0.1.0.md",
    "Record-Relative Chronological Resolution Proof Evidence - v0.1.0.md",
    "Canonical Spatial Topology Identity Proof Evidence - v0.1.0.md",
    "proof_kernel/CanonicalSpatialTopologyIdentityProofRecords/canonical_topology_R0.json",
    "Canonical Occupancy Transition Proof - Draft.md",
    "Canonical Occupancy Transition Proof Evidence - v0.1.0.md",
    "Co-op Open-City FPS Simulation - v0.7 Working Continuation.md",
    "THE_CITY Development Capacity and Progress Note - v0.1.11.md",
    "THE_CITY Current Proof State and Repo-Agent Instruction - v0.1.0.md",
    "proof_kernel/canonical_occupancy_transition.py",
    "proof_kernel/test_canonical_occupancy_transition.py",
    "proof_kernel/verify_canonical_occupancy_transition_release.py",
)


def _artifact_paths() -> tuple[str, ...]:
    return tuple(
        f"proof_kernel/CanonicalOccupancyTransitionProofRecords/{name}"
        for name in ARTIFACT_NAMES
    )


def release_paths() -> tuple[str, ...]:
    return tuple(sorted(SOURCE_PATHS + _artifact_paths()))


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _strict_load(path: Path) -> Any:
    raw = path.read_bytes()
    if not raw.endswith(b"\n") or raw.endswith(b"\n\n") or raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError(f"noncanonical artifact envelope: {path.name}")
    value = json.loads(raw.decode("utf-8"))
    if raw != (canonical_json(value) + "\n").encode("utf-8"):
        raise ValueError(f"noncanonical artifact serialization: {path.name}")
    return value


def _verify_artifacts() -> None:
    expected = artifact_payloads()
    actual_names = tuple(sorted(path.name for path in RECORDS.iterdir() if path.is_file()))
    if actual_names != tuple(sorted(ARTIFACT_NAMES)):
        raise ValueError("artifact directory membership drift")
    for name, payload in expected.items():
        actual = _strict_load(RECORDS / name)
        if canonical_json(actual) != canonical_json(payload):
            raise ValueError(f"artifact cannot be regenerated: {name}")

    run = proof_run()
    if run["checkpoint_oracle"] != {
        "result": "accepted",
        "reference_witness": "dense_inspection",
        "failures": [],
    }:
        raise ValueError("checkpoint equivalence failed")
    if not run["topology_projection_oracle"]["passed"]:
        raise ValueError("sealed Phase-1 topology projection is not bound")
    if not run["transition_definition_oracle"]["byte_identical"]:
        raise ValueError("open/blocked transition definitions differ")
    if run["runtime_fail_closed"]["count"] != 41 or not run["runtime_fail_closed"]["passed"]:
        raise ValueError("41-family rejection surface failed")
    if run["fault_atomicity"]["count"] != len(ALL_FAULT_POINTS) or not run["fault_atomicity"]["passed"]:
        raise ValueError("private fault atomicity failed")
    if not run["replay_oracle"]["passed"]:
        raise ValueError("replay oracle failed")
    if not run["source_audit"]["source_audit_passed"]:
        raise ValueError("source authority audit failed")

    dense = run["witness_runs"]["dense_inspection"]
    jump = run["witness_runs"]["boundary_jump"]
    for label in ("R0", "Rtransit", "Rfinal"):
        if canonical_json(dense["checkpoints"][label]) != canonical_json(jump["checkpoints"][label]):
            raise ValueError(f"policy checkpoint differs: {label}")
    r0 = dense["checkpoints"]["R0"]["canonical_record"]
    rtransit = dense["checkpoints"]["Rtransit"]["canonical_record"]
    rfinal = dense["checkpoints"]["Rfinal"]["canonical_record"]
    if rtransit["causal_provenance"]["canonical_ancestry"]["parent_record_hash"] != canonical_hash(r0):
        raise ValueError("Rtransit ancestry is not R0-bound")
    if rfinal["causal_provenance"]["canonical_ancestry"]["parent_record_hash"] != canonical_hash(rtransit):
        raise ValueError("Rfinal ancestry is not Rtransit-bound")
    if rtransit["current_causal_state"]["canonical_occupancy"][OCCUPANT] != {
        "kind": "in_transition",
        "transition_id": TRANSITION,
    }:
        raise ValueError("Rtransit occupancy is not exact")
    if rfinal["current_causal_state"]["canonical_occupancy"][OCCUPANT] != {
        "kind": "at_site",
        "site_id": SITE_A,
    }:
        raise ValueError("Rfinal did not settle at destination")
    if rfinal["current_causal_state"]["occupancy_transition_reservations"][RESERVATION]["state"] != "available":
        raise ValueError("terminal reservation was not released")
    if next_consequential_boundary(rfinal) != NO_BOUNDARY:
        raise ValueError("Rfinal retained future work")

    blocked = run["blocked_control"]["checkpoints"]["Rblocked"]["canonical_record"]
    blocked_commitment = blocked["current_causal_state"]["occupancy_transition_commitments"][TRANSITION]
    if (
        blocked["current_causal_state"]["canonical_occupancy"][OCCUPANT]
        != {"kind": "at_site", "site_id": SITE_B}
        or blocked_commitment["state"] != "failed"
        or blocked_commitment["terminal_reason"] != "failed_gate"
        or blocked_commitment["terminal_resource_disposition"] != "no_resource_acquired"
    ):
        raise ValueError("blocked ordinary-failure control drift")
    if canonical_json(transition_definition_projection(r0)) != canonical_json(
        transition_definition_projection(
            run["blocked_control"]["checkpoints"]["R0_blocked"]["canonical_record"]
        )
    ):
        raise ValueError("blocked control changed transition definition")


def write_release() -> None:
    write_artifacts(RECORDS)
    _verify_artifacts()
    own = MANIFEST.relative_to(ROOT).as_posix()
    if own in release_paths():
        raise AssertionError("manifest cannot contain itself")
    missing = [path for path in release_paths() if not (ROOT / path).is_file()]
    if missing:
        raise FileNotFoundError(f"missing release members: {missing}")
    MANIFEST.write_text(
        "\n".join(f"{_sha(ROOT / path)}  {path}" for path in release_paths()) + "\n",
        encoding="utf-8",
    )


def verify_release() -> tuple[int, int]:
    own = MANIFEST.relative_to(ROOT).as_posix()
    parsed: list[tuple[str, str]] = []
    seen: set[str] = set()
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        digest, separator, path = line.partition("  ")
        candidate = Path(path)
        if (
            not separator
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
            or not path
            or path in seen
            or path == own
            or candidate.is_absolute()
            or ".." in candidate.parts
        ):
            raise ValueError(f"invalid manifest member: {line!r}")
        seen.add(path)
        parsed.append((digest, path))
    if tuple(path for _, path in parsed) != release_paths():
        raise ValueError("manifest membership/order drift")
    for digest, path in parsed:
        if _sha(ROOT / path) != digest:
            raise ValueError(f"checksum mismatch: {path}")
    _verify_artifacts()
    return len(parsed), len(release_paths())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("write-release", "verify"))
    args = parser.parse_args()
    if args.command == "write-release":
        write_release()
        count = len(release_paths())
    else:
        count, expected = verify_release()
        if count != expected:
            raise ValueError("release member count mismatch")
    print(f"verified {count}/{count} release artifacts; manifest excludes itself")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
