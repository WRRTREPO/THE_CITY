"""Create and verify the self-excluding chronological-resolution release."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from kernel import canonical_json
from record_relative_chronological_resolution import (
    COMMITMENT_Y,
    NO_BOUNDARY,
    REJECT_BOUNDARY_CROSSING,
    REJECT_BOUNDARY_SOURCE,
    REJECT_DEMOTION_LOSS,
    REJECT_GATE_CACHE,
    REJECT_LOCAL_AUTHORITY,
    REJECT_PROMOTION_AUTHORITY,
    REJECT_SAME_CLOCK_SUCCESSOR,
    REJECT_STALE_BOUNDARY,
    all_witness_runs,
    canonical_hash,
    definition_independence_audit,
    equivalence_oracle,
    initial_canonical_envelope,
    next_consequential_boundary,
    proof_run,
    runtime_fail_closed_results,
    source_audit,
    write_artifacts,
)


ROOT = Path(__file__).resolve().parents[1]
RECORDS = Path(__file__).resolve().parent / "RecordRelativeChronologicalResolutionProofRecords"
MANIFEST = ROOT / "Record-Relative Chronological Resolution Proof - v0.1.0 SHA256SUMS.txt"

SOURCE_PATHS = (
    "README.md",
    "Resolution Semantics Law - v0.1.1.md",
    "Causal-LOD Equivalence Proof Evidence - v0.1.0.md",
    "Record-Relative Chronological Resolution Proof - Draft.md",
    "Record-Relative Chronological Resolution Proof Evidence - v0.1.0.md",
    "Co-op Open-City FPS Simulation - v0.7 Working Continuation.md",
    "THE_CITY Development Capacity and Progress Note - v0.1.5.md",
    "proof_kernel/kernel.py",
    "proof_kernel/record_relative_chronological_resolution.py",
    "proof_kernel/test_record_relative_chronological_resolution.py",
    "proof_kernel/verify_record_relative_chronological_resolution_release.py",
)


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_paths() -> tuple[str, ...]:
    names = (
        "chronological_resolution_R0.json",
        "chronological_resolution_dense_throughout_run.json",
        "chronological_resolution_boundary_jump_throughout_run.json",
        "chronological_resolution_dense_demote_boundary_jump_promote_dense_run.json",
        "chronological_resolution_boundary_jump_promote_dense_demote_boundary_jump_run.json",
        "chronological_resolution_oracle.json",
        "chronological_resolution_runtime_fail_closed.json",
        "chronological_resolution_definition_independence.json",
        "chronological_resolution_source_audit.json",
        "chronological_resolution_proof_run.json",
    )
    return tuple(f"proof_kernel/RecordRelativeChronologicalResolutionProofRecords/{name}" for name in names)


def release_paths() -> tuple[str, ...]:
    return tuple(sorted(SOURCE_PATHS + _artifact_paths()))


def _load(name: str) -> Any:
    return json.loads((RECORDS / name).read_text(encoding="utf-8"))


def _verify_artifacts() -> None:
    expected_r0 = initial_canonical_envelope()
    expected_runs = all_witness_runs()
    expected_proof = proof_run()

    if canonical_json(_load("chronological_resolution_R0.json")) != canonical_json(expected_r0):
        raise ValueError("R0 cannot be regenerated from the exact payload schema")
    for name, expected in expected_runs.items():
        actual = _load(f"chronological_resolution_{name}_run.json")
        if canonical_json(actual) != canonical_json(expected):
            raise ValueError(f"{name} cannot be regenerated from the frozen resolver and policy sequence")
    if _load("chronological_resolution_oracle.json") != expected_proof["equivalence_oracle"]:
        raise ValueError("checkpoint equivalence oracle artifact drift")
    if _load("chronological_resolution_runtime_fail_closed.json") != expected_proof["runtime_fail_closed"]:
        raise ValueError("runtime rejection artifact drift")
    if _load("chronological_resolution_definition_independence.json") != expected_proof["definition_independence_audit"]:
        raise ValueError("definition-independence audit artifact drift")
    if _load("chronological_resolution_source_audit.json") != expected_proof["source_audit"]:
        raise ValueError("source audit artifact drift")
    if canonical_json(_load("chronological_resolution_proof_run.json")) != canonical_json(expected_proof):
        raise ValueError("proof-run artifact drift")

    oracle = equivalence_oracle(expected_runs)
    if oracle["result"] != "accepted" or oracle["failures"]:
        raise ValueError("witnesses do not prove checkpoint equivalence")
    reference = expected_runs["dense_throughout"]
    for name, run in expected_runs.items():
        for label in ("R0", "R1", "R2", "R3"):
            if canonical_json(run["checkpoints"][label]) != canonical_json(reference["checkpoints"][label]):
                raise ValueError(f"{name} {label} differs from dense reference")
        if run["final_canonical_hash"] != reference["final_canonical_hash"]:
            raise ValueError(f"{name} final canonical hash differs")
    if expected_runs["dense_throughout"]["diagnostic_resolution_trace"] == expected_runs["boundary_jump_throughout"]["diagnostic_resolution_trace"]:
        raise ValueError("policies do not demonstrate different local execution histories")

    r0 = expected_r0
    r1 = reference["checkpoints"]["R1"]["canonical_envelope"]
    r2 = reference["checkpoints"]["R2"]["canonical_envelope"]
    r3 = reference["checkpoints"]["R3"]["canonical_envelope"]
    for parent, successor in ((r0, r1), (r1, r2), (r2, r3)):
        entry = successor["causal_provenance"]["authoritative_causal_ledger"][-1]
        parent_hash = canonical_hash(parent)
        if entry["source_record_hash"] != parent_hash:
            raise ValueError("ledger boundary source is not record-relative")
        if successor["causal_provenance"]["canonical_ancestry"]["parent_record_hash"] != parent_hash:
            raise ValueError("successor ancestry is not record-relative")
    y = r2["causal_provenance"]["authoritative_causal_ledger"][-1]
    if y["commitment_id"] != COMMITMENT_Y or y["source_record_hash"] != canonical_hash(r1):
        raise ValueError("Y is not derived from R1")
    if y["evaluated_gates"] != [{
        "path": "current_causal_state.gate_relevant_state.shared_slot_state",
        "observed_value": "allocated_to_x",
        "required_value": "available",
        "result": False,
    }]:
        raise ValueError("Y did not record its exact R1 gate observation")
    if next_consequential_boundary(r3) != NO_BOUNDARY:
        raise ValueError("Z did not leave an empty future schedule")

    failures = runtime_fail_closed_results()
    expected_dispositions = {
        "stale_R0_boundary_against_R1": REJECT_STALE_BOUNDARY,
        "cross_Y_boundary_from_R1": REJECT_BOUNDARY_CROSSING,
        "source_hash_mismatch": REJECT_BOUNDARY_SOURCE,
        "dense_mutates_canonical_clock": REJECT_LOCAL_AUTHORITY,
        "sample_caches_authoritative_gate": REJECT_GATE_CACHE,
        "promotion_carries_authority": REJECT_PROMOTION_AUTHORITY,
        "demotion_loses_authority": REJECT_DEMOTION_LOSS,
        "same_clock_successor_outside_payload": REJECT_SAME_CLOCK_SUCCESSOR,
    }
    if {name: result["disposition"] for name, result in failures.items()} != expected_dispositions:
        raise ValueError("runtime fail-closed disposition drift")
    if any(result["authoritative_causal_ledger_appended"] or result["future_schedule_created"] for result in failures.values()):
        raise ValueError("rejection leaked into canonical authority")

    independence = definition_independence_audit()
    audit = source_audit()
    if not (
        independence["passed"]
        and not independence["foreign_references"]
        and audit["resolver_functions"] == ["resolve_next_due"]
        and audit["resolver_signature"] == ["canonical_envelope", "canonical_boundary"]
        and audit["scheduler_signature"] == ["canonical_envelope"]
        and not audit["scheduler_reads_policy_local_state_or_trace"]
        and not audit["resolver_reads_policy_local_state_or_trace"]
        and audit["boundary_requires_source_record_hash"]
        and audit["scheduler_uses_at_or_after_clock"]
        and not audit["policy_calls_resolver"]
        and not audit["policy_evaluates_authoritative_gate"]
        and not audit["transitions_write_canonical_paths"]
        and audit["definition_independence"]["passed"]
        and not audit["random_module_imported"]
        and not audit["unreal_or_city_content_present"]
        and audit["payload_schema_exact"]
    ):
        raise ValueError("source audit does not prove record-relative scheduler isolation")


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
        count = len(release_paths())
    else:
        count, _ = verify_release()
    print(f"verified {count}/{count} release artifacts; manifest excludes itself")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
