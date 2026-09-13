#!/usr/bin/env python3
"""Independent validator for a CITY raw source-effect audit candidate."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def reject() -> None:
    raise ValueError("lcer.source_audit_record_invalid")


def validate(candidate_path: Path, contract_path: Path) -> dict[str, Any]:
    try:
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        contract_raw = contract_path.read_bytes()
        contract = json.loads(contract_raw)
    except (OSError, ValueError) as error:
        raise ValueError("lcer.source_audit_record_invalid") from error
    if not isinstance(candidate, dict) or not isinstance(contract, dict):
        reject()
    required = {"schema", "adapter_id", "claim_level", "source_identity", "contract_sha256", "files", "nodes", "edges", "transitive_local_imports", "scope_status", "source_audit_complete", "adversary_results", "summary", "authority", "result_sha256"}
    if set(candidate) != required or candidate["schema"] != "city.source_effect_audit.v1" or candidate["adapter_id"] != "city-live-evidence" or candidate["claim_level"] != "raw_evidence_only":
        reject()
    unsigned = dict(candidate); supplied = unsigned.pop("result_sha256")
    if not isinstance(supplied, str) or supplied != digest(canonical(unsigned)):
        reject()
    if candidate["contract_sha256"] != digest(contract_raw):
        reject()
    expected = contract.get("primary_sources")
    files = candidate["files"]
    if not isinstance(expected, list) or not isinstance(files, list) or [row.get("path") for row in files] != [row.get("path") for row in expected]:
        reject()
    if any(row.get("sha256") != wanted.get("sha256") for row, wanted in zip(files, expected)):
        reject()
    edges = candidate["edges"]
    if not isinstance(edges, list) or any(not isinstance(row, dict) or row.get("classification") not in {"allowed", "denied", "unclassified"} for row in edges):
        reject()
    unclassified = [row for row in edges if row["classification"] == "unclassified"]
    adversaries = candidate["adversary_results"]
    expected_adversaries = contract.get("forbidden_source_adversaries")
    if not isinstance(adversaries, list) or [row.get("adversary_id") for row in adversaries] != expected_adversaries or any(row.get("status") != "rejected" or not isinstance(row.get("offending_edge"), dict) or row["offending_edge"].get("classification") != "denied" or row["offending_edge"].get("reason_code") != row.get("failure_code") for row in adversaries):
        reject()
    if candidate["scope_status"] != "partial" or candidate["source_audit_complete"] is not False:
        reject()
    authority = candidate["authority"]
    if authority != {"may_open_acquisition": False, "may_open_release": False, "may_seal_phase_5": False}:
        reject()
    if candidate["summary"].get("unclassified_count") != len(unclassified):
        reject()
    # A candidate with incomplete closure is valid raw evidence, never a passed audit.
    return {"schema": "city.source_effect_audit_validation.v1", "status": "pass", "verdict": "raw_evidence_valid_incomplete", "failure_codes": ["lcer.required_edge_unclassified"] if unclassified else ["lcer.scope_incomplete"], "unclassified_count": len(unclassified), "claim_level": "raw_evidence_only"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate CITY raw source-effect candidate")
    parser.add_argument("--candidate", required=True); parser.add_argument("--contract", required=True); parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(validate(Path(args.candidate), Path(args.contract)), sort_keys=True))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(json.dumps({"status": "fail", "failure_codes": [str(error)], "claim_level": "raw_evidence_only"}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
