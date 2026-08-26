"""Create and verify the self-excluding Causal-LOD equivalence release."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from causal_lod_equivalence import (
    NO_BOUNDARY,
    REJECT_BOUNDARY_SKIP,
    REJECT_DEMOTION_LOSS,
    REJECT_GATE_CACHE,
    REJECT_POLICY_AUTHORITY,
    REJECT_PROMOTION_AUTHORITY,
    all_witness_runs,
    canonical_hash,
    equivalence_oracle,
    initial_canonical_envelope,
    proof_run,
    runtime_fail_closed_results,
    source_audit,
    write_artifacts,
)
from kernel import canonical_json


ROOT = Path(__file__).resolve().parents[1]
RECORDS = Path(__file__).resolve().parent / "CausalLodEquivalenceProofRecords"
MANIFEST = ROOT / "Causal-LOD Equivalence Proof - v0.1.0 SHA256SUMS.txt"

SOURCE_PATHS = (
    "README.md",
    "Resolution Semantics Law - v0.1.1.md",
    "Resolution Semantics Substrate Proof Evidence - v0.1.0.md",
    "Causal-LOD Equivalence Proof - Draft.md",
    "Causal-LOD Equivalence Proof Evidence - v0.1.0.md",
    "Co-op Open-City FPS Simulation - v0.7 Working Continuation.md",
    "proof_kernel/kernel.py",
    "proof_kernel/causal_lod_equivalence.py",
    "proof_kernel/test_causal_lod_equivalence.py",
    "proof_kernel/verify_causal_lod_equivalence_release.py",
)


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_paths() -> tuple[str, ...]:
    names = (
        "causal_lod_equivalence_R0.json",
        "causal_lod_equivalence_dense_throughout_run.json",
        "causal_lod_equivalence_boundary_jump_throughout_run.json",
        "causal_lod_equivalence_boundary_jump_promote_dense_run.json",
        "causal_lod_equivalence_dense_demote_boundary_jump_promote_dense_run.json",
        "causal_lod_equivalence_oracle.json",
        "causal_lod_equivalence_runtime_fail_closed.json",
        "causal_lod_equivalence_source_audit.json",
        "causal_lod_equivalence_proof_run.json",
    )
    return tuple(f"proof_kernel/CausalLodEquivalenceProofRecords/{name}" for name in names)


def release_paths() -> tuple[str, ...]:
    return tuple(sorted(SOURCE_PATHS + _artifact_paths()))


def _load(name: str) -> Any:
    return json.loads((RECORDS / name).read_text(encoding="utf-8"))


def _verify_artifacts() -> None:
    expected_r0 = initial_canonical_envelope()
    expected_runs = all_witness_runs()
    expected_proof = proof_run()
    if canonical_json(_load("causal_lod_equivalence_R0.json")) != canonical_json(expected_r0):
        raise ValueError("R0 cannot be regenerated from the exact payload schema")
    for name, expected in expected_runs.items():
        actual = _load(f"causal_lod_equivalence_{name}_run.json")
        if canonical_json(actual) != canonical_json(expected):
            raise ValueError(f"{name} cannot be regenerated from the frozen resolver and policy sequence")
    if _load("causal_lod_equivalence_oracle.json") != expected_proof["equivalence_oracle"]:
        raise ValueError("equivalence oracle artifact drift")
    if _load("causal_lod_equivalence_runtime_fail_closed.json") != expected_proof["runtime_fail_closed"]:
        raise ValueError("runtime rejection artifact drift")
    if _load("causal_lod_equivalence_source_audit.json") != expected_proof["source_audit"]:
        raise ValueError("source audit artifact drift")
    if canonical_json(_load("causal_lod_equivalence_proof_run.json")) != canonical_json(expected_proof):
        raise ValueError("proof run artifact drift")

    runs = expected_runs
    oracle = equivalence_oracle(runs)
    if oracle["result"] != "accepted" or oracle["failures"]:
        raise ValueError("witnesses do not prove canonical equivalence")
    r0_hash = canonical_hash(expected_r0)
    reference = runs["dense_throughout"]
    for name, run in runs.items():
        if canonical_json(run["final_canonical_envelope"]) != canonical_json(reference["final_canonical_envelope"]):
            raise ValueError(f"{name} final canonical envelope differs")
        header = run["transaction"]["header"]
        if header["parent_record_hash"] != r0_hash or header["transaction_pre_state_hash"] != r0_hash:
            raise ValueError(f"{name} does not use R0 as exact transaction pre-state")
        if run["next_consequential_boundary"] != NO_BOUNDARY:
            raise ValueError(f"{name} leaves future consequential work")
    if runs["dense_throughout"]["diagnostic_resolution_trace"] == runs["boundary_jump_throughout"]["diagnostic_resolution_trace"]:
        raise ValueError("policies do not demonstrate materially different local execution traces")

    failures = runtime_fail_closed_results()
    expected_dispositions = {
        "dense_mutates_canonical_clock": REJECT_POLICY_AUTHORITY,
        "sample_caches_authoritative_gate": REJECT_GATE_CACHE,
        "promotion_carries_authority": REJECT_PROMOTION_AUTHORITY,
        "demotion_loses_authority": REJECT_DEMOTION_LOSS,
        "boundary_jump_skips_due_work": REJECT_BOUNDARY_SKIP,
    }
    if {name: result["disposition"] for name, result in failures.items()} != expected_dispositions:
        raise ValueError("runtime fail-closed disposition drift")
    if any(result["authoritative_causal_ledger_appended"] or result["future_schedule_created"] for result in failures.values()):
        raise ValueError("runtime rejection leaked into canonical authority")

    audit = source_audit()
    if not (
        audit["resolver_functions"] == ["resolve_next_due"]
        and audit["resolver_signature"] == ["canonical_envelope", "canonical_boundary"]
        and not audit["resolver_reads_policy_local_state_or_trace"]
        and not audit["policy_calls_resolver"]
        and not audit["policy_can_override_boundary"]
        and not audit["policy_evaluates_authoritative_gate"]
        and not audit["transitions_write_canonical_paths"]
        and not audit["random_module_imported"]
        and not audit["unreal_or_city_content_present"]
        and audit["payload_schema_exact"]
    ):
        raise ValueError("source audit does not prove policy/resolver isolation")


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
