"""Create and verify the self-excluding External Input Boundary v0.1.1 release."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from kernel import canonical_json
from external_input_boundary import (
    COMMITMENT_ALPHA,
    INPUT_ID,
    NO_AUTONOMOUS_BOUNDARY,
    NO_EXECUTION_BOUNDARY,
    PAYLOAD_SCHEMA,
    REJECT_BOUNDARY_CROSSING,
    REJECT_BOUNDARY_SOURCE,
    REJECT_DEMOTION_LOSS,
    REJECT_GATE_CACHE,
    REJECT_INPUT_CONTRACT,
    REJECT_INPUT_DIGEST,
    REJECT_INPUT_SOURCE,
    REJECT_INPUT_TIME,
    REJECT_LOCAL_AUTHORITY,
    REJECT_PROMOTION_AUTHORITY,
    all_witness_runs,
    canonical_hash,
    cursor_reset_witness,
    equivalence_oracle,
    external_evidence_q,
    initial_canonical_envelope,
    next_consequential_boundary,
    next_execution_boundary,
    proof_run,
    q_absent_control_run,
    runtime_fail_closed_results,
    source_audit,
    write_artifacts,
)


ROOT = Path(__file__).resolve().parents[1]
RECORDS = Path(__file__).resolve().parent / "ExternalInputBoundaryProofRecords"
MANIFEST = ROOT / "External Input Boundary Proof - v0.1.1 SHA256SUMS.txt"

SOURCE_PATHS = (
    "README.md",
    "Resolution Semantics Law - v0.1.1.md",
    "Causal-LOD Equivalence Proof Evidence - v0.1.0.md",
    "Record-Relative Chronological Resolution Proof Evidence - v0.1.0.md",
    "External Input Boundary Proof - Draft.md",
    "External Input Boundary Proof - v0.1.1.md",
    "External Input Boundary Proof Evidence - v0.1.1.md",
    "Co-op Open-City FPS Simulation - v0.7 Working Continuation.md",
    "THE_CITY Development Capacity and Progress Note - v0.1.6.md",
    "proof_kernel/kernel.py",
    "proof_kernel/external_input_boundary.py",
    "proof_kernel/test_external_input_boundary.py",
    "proof_kernel/verify_external_input_boundary_release.py",
)


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_paths() -> tuple[str, ...]:
    names = (
        "external_input_R0.json",
        "external_input_Q.json",
        "external_input_dense_throughout_run.json",
        "external_input_boundary_jump_throughout_run.json",
        "external_input_dense_demote_boundary_jump_run.json",
        "external_input_boundary_jump_promote_dense_run.json",
        "external_input_q_absent_control.json",
        "external_input_cursor_reset.json",
        "external_input_runtime_fail_closed.json",
        "external_input_oracle.json",
        "external_input_source_audit.json",
        "external_input_proof_run.json",
    )
    return tuple(f"proof_kernel/ExternalInputBoundaryProofRecords/{name}" for name in names)


def release_paths() -> tuple[str, ...]:
    return tuple(sorted(SOURCE_PATHS + _artifact_paths()))


def _load(name: str) -> Any:
    return json.loads((RECORDS / name).read_text(encoding="utf-8"))


def _verify_artifacts() -> None:
    r0 = initial_canonical_envelope()
    q = external_evidence_q(r0)
    runs = all_witness_runs()
    expected_proof = proof_run()
    control = q_absent_control_run()
    cursor_reset = cursor_reset_witness()

    if _load("external_input_R0.json") != r0:
        raise ValueError("R0 cannot be regenerated from ExternalInputBoundaryPayload.v1.1")
    if _load("external_input_Q.json") != q:
        raise ValueError("Q cannot be regenerated using the frozen non-self-referential digest projection")
    for name, expected in runs.items():
        if _load(f"external_input_{name}_run.json") != expected:
            raise ValueError(f"{name} cannot be regenerated from the frozen coordinator and resolver")
    for artifact, expected in (
        ("external_input_q_absent_control.json", control),
        ("external_input_cursor_reset.json", cursor_reset),
        ("external_input_runtime_fail_closed.json", expected_proof["runtime_fail_closed"]),
        ("external_input_oracle.json", expected_proof["equivalence_oracle"]),
        ("external_input_source_audit.json", expected_proof["source_audit"]),
        ("external_input_proof_run.json", expected_proof),
    ):
        if _load(artifact) != expected:
            raise ValueError(f"artifact drift: {artifact}")

    oracle = equivalence_oracle(runs)
    if oracle != {"result": "accepted", "reference_witness": "dense_throughout", "failures": []}:
        raise ValueError("four execution policies do not prove external-input checkpoint equivalence")
    reference = runs["dense_throughout"]
    for name, run in runs.items():
        for label in ("R0", "Rinput", "Rfinal"):
            if canonical_json(run["checkpoints"][label]) != canonical_json(reference["checkpoints"][label]):
                raise ValueError(f"{name} diverges from dense reference at {label}")
    if reference["diagnostic_resolution_trace"] == runs["boundary_jump_throughout"]["diagnostic_resolution_trace"]:
        raise ValueError("dense and boundary-jump witnesses do not differ locally")

    rinput = reference["checkpoints"]["Rinput"]["canonical_envelope"]
    rfinal = reference["checkpoints"]["Rfinal"]["canonical_envelope"]
    h0, hi, hf, hc = canonical_hash(r0), canonical_hash(rinput), canonical_hash(rfinal), canonical_hash(control["control_final"])
    q_entry = rinput["causal_provenance"]["authoritative_causal_ledger"][-1]
    alpha_entry = rfinal["causal_provenance"]["authoritative_causal_ledger"][-1]
    control_entry = control["control_final"]["causal_provenance"]["authoritative_causal_ledger"][-1]
    if rinput["causal_provenance"]["canonical_ancestry"]["parent_record_hash"] != h0 or q_entry["canonical_pre_state_hash"] != h0:
        raise ValueError("Rinput does not witness R0 ancestry/pre-state")
    if rfinal["causal_provenance"]["canonical_ancestry"]["parent_record_hash"] != hi or alpha_entry["canonical_pre_state_hash"] != hi:
        raise ValueError("Rfinal does not witness Rinput ancestry/pre-state")
    if control["control_final"]["causal_provenance"]["canonical_ancestry"]["parent_record_hash"] != h0 or control_entry["canonical_pre_state_hash"] != h0:
        raise ValueError("control final does not witness R0 ancestry/pre-state")
    if not all(len(value) == 64 for value in (h0, hi, hf, hc)):
        raise ValueError("external successor hashes are not complete SHA-256 identities")
    if "canonical_post_state_hash" in canonical_json({"Rinput": rinput, "Rfinal": rfinal, "Rcontrol_final": control["control_final"]}):
        raise ValueError("canonical record stores a forbidden self-referential post-state hash")

    if next_consequential_boundary(r0)["decision_time"] != "t1/00":
        raise ValueError("R0 autonomous scheduler drift")
    if next_execution_boundary(r0, [q], 0)["decision_time"] != "t0/30":
        raise ValueError("coordinator did not intercept Q before alpha")
    if next_consequential_boundary(rinput)["decision_time"] != "t1/00" or next_execution_boundary(rinput, [q], 1)["decision_time"] != "t1/00":
        raise ValueError("Rinput did not rediscover alpha")
    if next_consequential_boundary(rfinal) != NO_AUTONOMOUS_BOUNDARY or next_execution_boundary(rfinal, [q], 1) != NO_EXECUTION_BOUNDARY:
        raise ValueError("Rfinal did not empty autonomous and coordinator boundaries")
    if rinput["current_causal_state"]["accepted_external_inputs"] != [INPUT_ID]:
        raise ValueError("accepted external input identity was not made canonical")
    if alpha_entry["evaluated_gates"] != [{"observed_value": "disabled", "path": "/current_causal_state/gate_relevant_state/gate_token_state", "required_value": "enabled", "result": False}]:
        raise ValueError("alpha did not revalidate Rinput's canonical gate fact")
    if rfinal["current_causal_state"]["active_and_terminal_commitments"][COMMITMENT_ALPHA]["state"] != "failed_gate":
        raise ValueError("accepted Q directly changed alpha or alpha did not fail its ordinary gate")
    if control["control_final"]["current_causal_state"]["durable_facts"]["alpha_outcome"] != "succeeded":
        raise ValueError("Q-absent control did not preserve ordinary alpha success")

    expected_failures = {
        "source_hash_mismatch": REJECT_INPUT_SOURCE,
        "digest_covered_field_changed_without_recompute": REJECT_INPUT_DIGEST,
        "redirected_contract_with_recomputed_digest": REJECT_INPUT_CONTRACT,
        "late_or_equal_time_input": REJECT_INPUT_TIME,
        "autonomous_boundary_crosses_available_Q": REJECT_BOUNDARY_CROSSING,
        "stale_BQ_against_Rinput": REJECT_BOUNDARY_SOURCE,
        "cursor_skips_unaccepted_Q": REJECT_LOCAL_AUTHORITY,
        "local_sample_caches_authoritative_gate": REJECT_GATE_CACHE,
        "local_policy_requests_canonical_mutation": REJECT_LOCAL_AUTHORITY,
        "promotion_carries_authority": REJECT_PROMOTION_AUTHORITY,
        "demotion_loses_authority": REJECT_DEMOTION_LOSS,
    }
    failures = runtime_fail_closed_results()
    if {name: entry["disposition"] for name, entry in failures.items()} != expected_failures:
        raise ValueError("runtime rejection disposition drift")
    if any(not entry["canonical_unchanged"] or entry["cursor_advanced"] or not entry["test_terminal"] for entry in failures.values()):
        raise ValueError("rejected input or runtime attack leaked into canonical authority")

    audit = source_audit()
    if not (
        audit["passed"]
        and audit["admission_functions"] == ["admit_external_input_candidate"]
        and audit["resolver_functions"] == ["resolve_execution_boundary"]
        and audit["scheduler_functions"] == ["next_consequential_boundary"]
        and audit["coordinator_functions"] == ["next_execution_boundary"]
        and audit["resolver_signature"] == ["canonical_envelope", "execution_boundary", "q"]
        and audit["admission_is_side_effect_free"]
        and audit["boundary_requires_source_record_hash"]
        and not audit["policy_calls_resolver"]
        and not audit["policy_evaluates_authoritative_gate"]
        and not audit["random_module_imported"]
        and not audit["unreal_or_city_content_present"]
        and not audit["canonical_post_state_hash_present"]
        and not audit["input_shortcut_present"]
    ):
        raise ValueError("source audit does not prove canonical external-input authority isolation")


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
    _verify_artifacts()
    return len(members), len(members)


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
