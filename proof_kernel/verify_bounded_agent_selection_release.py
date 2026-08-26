"""Create and verify the self-excluding bounded-agent selection release."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from bounded_agent_selection import (
    AGENT_ID,
    LOCAL_ACTION,
    REMOTE_ACTION,
    action_definition_hashes,
    feasibility_counterfactual_run,
    hidden_a_run,
    hidden_b_run,
    primary_run,
    record_hash,
    semantic_selection,
    tie_run,
    write_run_artifacts,
)
from kernel import canonical_json


ROOT = Path(__file__).resolve().parents[1]
RECORDS = Path(__file__).resolve().parent / "BoundedAgentSelectionProofRecords"
MANIFEST = ROOT / "Bounded Agent Commitment Selection Proof - v0.1.0 SHA256SUMS.txt"

SOURCE_PATHS = (
    "Bounded Agent Commitment Selection Proof - Draft.md",
    "Bounded Agent Commitment Selection Proof Evidence - v0.1.0.md",
    "Co-op Open-City FPS Simulation - v0.7 Working Continuation.md",
    "proof_kernel/kernel.py",
    "proof_kernel/bounded_agent_selection.py",
    "proof_kernel/test_bounded_agent_selection.py",
    "proof_kernel/verify_bounded_agent_selection_release.py",
)


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_paths() -> tuple[str, ...]:
    return tuple(
        f"proof_kernel/BoundedAgentSelectionProofRecords/bounded_selection_{name}_{kind}.json"
        for name in ("primary", "feasibility", "hidden_a", "hidden_b", "tie")
        for kind in ("R0", "proposal", "final", "ledger", "run")
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
        "feasibility": feasibility_counterfactual_run,
        "hidden_a": hidden_a_run,
        "hidden_b": hidden_b_run,
        "tie": tie_run,
    }[name]()


def _verify_run(name: str) -> None:
    expected = _expected(name)
    actual = json.loads((RECORDS / f"bounded_selection_{name}_run.json").read_text(encoding="utf-8"))
    if canonical_json(actual) != canonical_json(expected):
        raise ValueError(f"{name} run cannot be regenerated from the frozen resolver")
    if _load_record(f"bounded_selection_{name}_R0.json") != expected["r0"]:
        raise ValueError(f"{name} R0 drift")
    if _load_record(f"bounded_selection_{name}_final.json") != expected["final_record"]:
        raise ValueError(f"{name} final drift")
    proposal = json.loads((RECORDS / f"bounded_selection_{name}_proposal.json").read_text(encoding="utf-8"))
    if proposal != expected["proposal"]:
        raise ValueError(f"{name} proposal drift")
    ledger = json.loads((RECORDS / f"bounded_selection_{name}_ledger.json").read_text(encoding="utf-8"))
    if ledger != expected["ledger"]:
        raise ValueError(f"{name} ledger drift")


def _verify_outcomes() -> None:
    primary = _expected("primary")
    feasibility = _expected("feasibility")
    hidden_a = _expected("hidden_a")
    hidden_b = _expected("hidden_b")
    tie = _expected("tie")
    remote_commitment = f"{AGENT_ID}.{REMOTE_ACTION}.commitment.t0_00"
    local_commitment = f"{AGENT_ID}.{LOCAL_ACTION}.commitment.t0_00"
    if not (
        primary["proposal"]["selection"]["selected_action_id"] == REMOTE_ACTION
        and remote_commitment in primary["final_record"]["commitments"]
        and primary["final_record"]["graph"]["A_to_B"]["capacity"] == 0
    ):
        raise ValueError("primary does not prove remote selection and canonical commitment creation")
    if not (
        feasibility["proposal"]["selection"]["selected_action_id"] == LOCAL_ACTION
        and local_commitment in feasibility["final_record"]["commitments"]
        and feasibility["final_record"]["graph"]["A_to_B"]["open"] is False
    ):
        raise ValueError("feasibility counterfactual does not prove local selection")
    if semantic_selection(hidden_a) != semantic_selection(hidden_b):
        raise ValueError("hidden-fact witness changes selection semantics")
    normalized_a = copy.deepcopy(hidden_a["final_record"])
    normalized_b = copy.deepcopy(hidden_b["final_record"])
    normalized_a.pop("hidden_fact_H")
    normalized_b.pop("hidden_fact_H")
    if normalized_a != normalized_b:
        raise ValueError("hidden-fact witness changes more than H")
    if not (
        tie["proposal"]["selection"]["selected_action_id"] == REMOTE_ACTION
        and tie["proposal"]["selection"]["selected_score"] == 4
    ):
        raise ValueError("tie witness does not use stable action-id selection")
    hashes = action_definition_hashes()
    if any(run["r0"]["action_definition_hashes"] != hashes for run in (primary, feasibility, hidden_a, hidden_b, tie)):
        raise ValueError("action definition hashes drift between witnesses")


def write_release() -> None:
    for name, run in (
        ("primary", primary_run()),
        ("feasibility", feasibility_counterfactual_run()),
        ("hidden_a", hidden_a_run()),
        ("hidden_b", hidden_b_run()),
        ("tie", tie_run()),
    ):
        write_run_artifacts(name, run, RECORDS)
    for name in ("primary", "feasibility", "hidden_a", "hidden_b", "tie"):
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
    for name in ("primary", "feasibility", "hidden_a", "hidden_b", "tie"):
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
