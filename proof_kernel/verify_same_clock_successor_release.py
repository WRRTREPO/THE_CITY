"""Release verifier for Same-Clock Successor Semantics Proof v0.1.0."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from kernel import canonical_json
from same_clock_successor_semantics import (
    BUDGET_ID,
    COMMITMENT_X,
    COMMITMENT_Y,
    NO_BOUNDARY,
    REJECT_BOUNDARY_CROSSING,
    REJECT_BOUNDARY_SOURCE,
    REJECT_BUDGET,
    REJECT_CYCLE,
    REJECT_DEMOTION_LOSS,
    REJECT_DUPLICATE_MEMBER,
    REJECT_GATE_CACHE,
    REJECT_LOCAL_AUTHORITY,
    REJECT_PHASE_LIMIT,
    REJECT_PROMOTION_AUTHORITY,
    REJECT_RETROGRADE_PHASE,
    TIME,
    all_witness_runs,
    canonical_hash,
    equivalence_oracle,
    initial_canonical_envelope,
    proof_run,
    runtime_fail_closed_results,
    source_audit,
    write_artifacts,
)


ROOT = Path(__file__).resolve().parents[1]
RECORDS = Path(__file__).resolve().parent / "SameClockSuccessorSemanticsProofRecords"
MANIFEST = ROOT / "Same-Clock Successor Semantics Proof - v0.1.0 SHA256SUMS.txt"

SOURCE_PATHS = (
    "README.md",
    "Resolution Semantics Law - v0.1.1.md",
    "Causal-LOD Equivalence Proof Evidence - v0.1.0.md",
    "Record-Relative Chronological Resolution Proof Evidence - v0.1.0.md",
    "External Input Boundary Proof Evidence - v0.1.1.md",
    "Same-Clock Successor Semantics Proof - Draft.md",
    "Same-Clock Successor Semantics Proof Evidence - v0.1.0.md",
    "Co-op Open-City FPS Simulation - v0.7 Working Continuation.md",
    "THE_CITY Development Capacity and Progress Note - v0.1.7.md",
    "proof_kernel/kernel.py",
    "proof_kernel/same_clock_successor_semantics.py",
    "proof_kernel/test_same_clock_successor_semantics.py",
    "proof_kernel/verify_same_clock_successor_release.py",
)


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_paths() -> tuple[str, ...]:
    names = (
        "same_clock_successor_R0.json",
        "same_clock_successor_R1.json",
        "same_clock_successor_R2.json",
        "same_clock_successor_dense_throughout_run.json",
        "same_clock_successor_boundary_jump_throughout_run.json",
        "same_clock_successor_dense_demote_boundary_jump_run.json",
        "same_clock_successor_boundary_jump_promote_dense_run.json",
        "same_clock_successor_oracle.json",
        "same_clock_successor_runtime_fail_closed.json",
        "same_clock_successor_source_audit.json",
        "same_clock_successor_proof_run.json",
    )
    return tuple(f"proof_kernel/SameClockSuccessorSemanticsProofRecords/{name}" for name in names)


def release_paths() -> tuple[str, ...]:
    return tuple(sorted(SOURCE_PATHS + _artifact_paths()))


def _load(name: str) -> Any:
    return json.loads((RECORDS / name).read_text(encoding="utf-8"))


def _verify_artifacts() -> None:
    expected_r0 = initial_canonical_envelope()
    expected_proof = proof_run()
    expected_runs = all_witness_runs()
    reference = expected_runs["dense_throughout"]

    expected_records = {"R0": expected_proof["r0"], "R1": expected_proof["r1"], "R2": expected_proof["r2"]}
    for label, expected in expected_records.items():
        actual = _load(f"same_clock_successor_{label}.json")
        if canonical_json(actual) != canonical_json(expected):
            raise ValueError(f"{label} cannot be regenerated from the frozen resolver")

    for name, expected in expected_runs.items():
        actual = _load(f"same_clock_successor_{name}_run.json")
        if canonical_json(actual) != canonical_json(expected):
            raise ValueError(f"{name} cannot be regenerated from the frozen policy sequence")
        for label in ("R0", "R1", "R2"):
            if canonical_json(actual["checkpoints"][label]) != canonical_json(reference["checkpoints"][label]):
                raise ValueError(f"{name} {label} differs from the dense checkpoint")

    if _load("same_clock_successor_oracle.json") != expected_proof["equivalence_oracle"]:
        raise ValueError("checkpoint equivalence oracle drift")
    if _load("same_clock_successor_runtime_fail_closed.json") != expected_proof["runtime_fail_closed"]:
        raise ValueError("runtime fail-closed artifact drift")
    if _load("same_clock_successor_source_audit.json") != expected_proof["source_audit"]:
        raise ValueError("source audit artifact drift")
    if canonical_json(_load("same_clock_successor_proof_run.json")) != canonical_json(expected_proof):
        raise ValueError("proof-run artifact drift")

    oracle = equivalence_oracle(expected_runs)
    if oracle != {"result": "accepted", "reference_witness": "dense_throughout", "failures": []}:
        raise ValueError("witnesses do not prove checkpoint equivalence")
    if expected_runs["dense_throughout"]["diagnostic_resolution_trace"] == expected_runs["boundary_jump_throughout"]["diagnostic_resolution_trace"]:
        raise ValueError("local execution histories are not materially different")

    r0 = expected_r0
    r1 = reference["checkpoints"]["R1"]["canonical_envelope"]
    r2 = reference["checkpoints"]["R2"]["canonical_envelope"]
    bx = reference["checkpoints"]["R0"]["next_consequential_boundary"]
    by = reference["checkpoints"]["R1"]["next_consequential_boundary"]
    if (bx["decision_time"], bx["simulation_phase"], bx["due_work_ids"]) != (TIME, 10, ["work_x"]):
        raise ValueError("X boundary identity drift")
    if (by["decision_time"], by["simulation_phase"], by["due_work_ids"]) != (TIME, 20, ["work_y"]):
        raise ValueError("Y was not rediscovered at the later same-clock phase")
    if by["source_record_hash"] != canonical_hash(r1):
        raise ValueError("Y boundary is not bound to R1")
    if r1["future_causal_state"]["canonical_clock"] != TIME or r2["future_causal_state"]["canonical_clock"] != TIME:
        raise ValueError("same-clock transitions introduced an unauthorized clock advance")
    if r1["current_causal_state"]["reservations_leases_and_resource_ownership"][BUDGET_ID]["remaining_units"] != 0:
        raise ValueError("X did not consume finite same-clock authority")
    if r1["current_causal_state"]["active_and_terminal_commitments"][COMMITMENT_Y]["state"] != "active":
        raise ValueError("X did not create an active Y commitment")
    if r2["current_causal_state"]["active_and_terminal_commitments"][COMMITMENT_Y]["state"] != "succeeded":
        raise ValueError("Y did not resolve from R1")
    if r2["future_causal_state"]["scheduled_consequential_decisions"] or r2["future_causal_state"]["canonical_work_member_keys"]:
        raise ValueError("R2 retained same-clock future work")
    if reference["checkpoints"]["R2"]["next_consequential_boundary"] != NO_BOUNDARY:
        raise ValueError("scheduler did not return none after Y")
    for parent, successor in ((r0, r1), (r1, r2)):
        parent_hash = canonical_hash(parent)
        if successor["causal_provenance"]["canonical_ancestry"]["parent_record_hash"] != parent_hash:
            raise ValueError("successor ancestry is not record-relative")
        if successor["causal_provenance"]["authoritative_causal_ledger"][-1]["source_record_hash"] != parent_hash:
            raise ValueError("ledger source is not record-relative")

    failures = runtime_fail_closed_results()
    expected_dispositions = {
        "retrograde_or_equal_phase": REJECT_RETROGRADE_PHASE,
        "phase_limit_exceeded": REJECT_PHASE_LIMIT,
        "duplicate_work_member": REJECT_DUPLICATE_MEMBER,
        "cyclic_or_settled_work": REJECT_CYCLE,
        "generation_budget_exhausted": REJECT_BUDGET,
        "stale_BX_against_R1": REJECT_BOUNDARY_SOURCE,
        "fabricated_BY_against_R0": REJECT_BOUNDARY_CROSSING,
        "crossing_boundary_against_R1": REJECT_BOUNDARY_CROSSING,
        "local_clock_authority": REJECT_LOCAL_AUTHORITY,
        "cached_authoritative_gate": REJECT_GATE_CACHE,
        "promotion_authority": REJECT_PROMOTION_AUTHORITY,
        "demotion_authority_loss": REJECT_DEMOTION_LOSS,
    }
    if {name: result["disposition"] for name, result in failures.items()} != expected_dispositions:
        raise ValueError("runtime rejection disposition drift")
    if any(result["canonical_mutation_committed"] or result["authoritative_causal_ledger_appended"] or result["future_schedule_created"] for result in failures.values()):
        raise ValueError("rejected attempt leaked into canonical authority")

    audit = source_audit()
    if not (
        audit["resolver_functions"] == ["resolve_next_due"]
        and audit["resolver_signature"] == ["canonical_envelope", "canonical_boundary"]
        and audit["scheduler_signature"] == ["canonical_envelope"]
        and audit["boundary_schema"] == ["source_record_hash", "decision_time", "simulation_phase", "due_work_ids", "work_member_keys"]
        and audit["scheduler_selects_boundary_not_member"]
        and audit["scheduler_returns_complete_due_set"]
        and not audit["work_id_creates_transaction_boundaries"]
        and not audit["resolver_reads_policy_local_state_or_trace"]
        and not audit["policy_calls_resolver"]
        and not audit["policy_evaluates_authoritative_gate"]
        and not audit["policy_can_override_boundary"]
        and not audit["policy_writes_canonical_paths"]
        and audit["scheduler_requeries_after_each_commit"]
        and audit["same_clock_budget_authoritative"]
        and not audit["random_module_imported"]
        and not audit["unreal_or_city_content_present"]
        and not audit["self_referential_successor_hash_present"]
        and audit["payload_schema_exact"]
    ):
        raise ValueError("source audit does not prove frozen authority boundaries")


def write_release() -> None:
    write_artifacts(RECORDS)
    _verify_artifacts()
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
