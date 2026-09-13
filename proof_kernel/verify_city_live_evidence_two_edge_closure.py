#!/usr/bin/env python3
"""Independently recompute CITY's two-edge closure record."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


AUTHORITY = {"may_open_acquisition": False, "may_open_release": False, "may_seal_phase_5": False}
FAILURE = "lcer.two_edge_closure_invalid"


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def reject() -> None:
    raise ValueError(FAILURE)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(FAILURE) from error
    if not isinstance(value, dict):
        reject()
    return value


def file_digest(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        reject()
    return digest(path.read_bytes())


def sealed_environment(keys: Any, owned: Path) -> dict[str, str]:
    base = {"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C", "PYTHONDONTWRITEBYTECODE": "1",
            "HOME": "/var/empty", "TMPDIR": str(owned / "tmp"),
            "PYTHONPYCACHEPREFIX": str(owned / "pycache")}
    if (not isinstance(keys, list) or sorted(keys) != sorted(set(keys))
            or any(not isinstance(key, str) or key not in base for key in keys)):
        reject()
    return {key: base[key] for key in keys}


def expected_record(root: Path, output: Path) -> dict[str, Any]:
    contract_path = root / "proof_kernel/city_live_evidence_two_edge_closure_contract.json"
    contract = read_json(contract_path)
    contract_unsigned = {key: value for key, value in contract.items() if key != "record_sha256"}
    source_path = root / "proof_kernel/city_live_evidence_source_audit_contract.json"
    source = read_json(source_path)
    required = {"schema", "source_audit_contract_sha256", "source_file_count", "source_file_manifest_sha256",
                "edges", "build_environment_keys", "closure_environment_keys", "negative_controls", "authority",
                "record_sha256"}
    if (set(contract) != required or contract.get("schema") != "city.live_evidence_two_edge_closure_contract.v1"
            or contract.get("authority") != AUTHORITY
            or contract.get("record_sha256") != digest(canonical(contract_unsigned))
            or contract.get("source_audit_contract_sha256") != file_digest(source_path)):
        reject()
    primary = source.get("primary_sources")
    transitive = source.get("transitive_local_imports", {}).get("sources")
    sites = source.get("exact_effect_call_sites")
    if not isinstance(primary, list) or not isinstance(transitive, list) or not isinstance(sites, list):
        reject()
    files = [*primary, *transitive]
    if (len(files) != 13 or contract.get("source_file_count") != len(files)
            or contract.get("source_file_manifest_sha256") != digest(canonical(files))):
        reject()
    for row in files:
        if not isinstance(row, dict) or set(row) != {"path", "sha256", "kind"}:
            reject()
        path = Path(row["path"])
        if path.is_absolute() or ".." in path.parts or file_digest(root / path) != row["sha256"]:
            reject()
    edges = contract.get("edges")
    if not isinstance(edges, list) or len(edges) != 2:
        reject()
    for edge in edges:
        if (not isinstance(edge, dict) or set(edge) != {"family", "path", "line", "callable", "token", "consequence"}
                or edge.get("family") not in {"function_to_consequence", "external_input_to_callable"}
                or not isinstance(edge.get("line"), int) or edge["line"] <= 0
                or not all(isinstance(edge.get(key), str) and edge[key] for key in ("path", "callable", "token", "consequence"))
                or {"path": edge["path"], "function": edge["callable"], "callee": edge["token"],
                    "line": edge["line"], "consequence": edge["consequence"]} not in sites):
            reject()
    if {(edge["family"], edge["consequence"]) for edge in edges} != {("function_to_consequence", "build_execution"), ("external_input_to_callable", "test_control")}:
        reject()
    build = sealed_environment(contract.get("build_environment_keys"), output)
    closure = sealed_environment(contract.get("closure_environment_keys"), output)
    record = {"schema": "city.live_evidence_two_edge_closure_record.v1", "status": "pass",
              "verdict": "raw_evidence_valid_incomplete", "closure_contract_sha256": file_digest(contract_path),
              "source_audit_contract_sha256": file_digest(source_path), "source_files": files, "edges": edges,
              "build_environment": {"keys": sorted(build), "sha256": digest(canonical(build))},
              "closure_environment": {"keys": sorted(closure), "sha256": digest(canonical(closure))},
              "authority": AUTHORITY,
              "retained_denials": ["lcer.acquisition_implementation_incomplete", "lcer.release_semantics_not_implemented"]}
    record["record_sha256"] = digest(canonical(record))
    return record


def verify(root: Path, record_path: Path) -> dict[str, Any]:
    root, record_path = root.resolve(), record_path.resolve()
    if record_path.is_relative_to(root):
        reject()
    actual = read_json(record_path)
    if actual != expected_record(root, record_path.parent):
        reject()
    return {"status": "pass", "verdict": actual["verdict"], "record_sha256": actual["record_sha256"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--record", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(verify(Path(args.root), Path(args.record)), sort_keys=True)); return 0
    except (OSError, ValueError, TypeError, KeyError):
        print(json.dumps({"status": "fail", "failure_codes": [FAILURE]}, sort_keys=True)); return 2


if __name__ == "__main__":
    raise SystemExit(main())
