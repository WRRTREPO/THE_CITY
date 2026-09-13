#!/usr/bin/env python3
"""Run Harbinger against CITY's frozen Phase 5 source manifest.

This bridge is host-specific.  It prepares a fresh packet outside CITY, binds
the packet to the frozen CITY source contract, and returns raw evidence only.
Harbinger's candidate remains incomplete until its own graph is complete; this
bridge cannot open CITY acquisition, release, or Phase 5 authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any


SCHEMA = "city.harbinger_source_effect_bridge.v1"


class BridgeError(ValueError):
    pass


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_bytes(canonical(value) + b"\n")


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise BridgeError("lcer.harbinger_bridge_record_invalid") from error
    if not isinstance(value, dict):
        raise BridgeError("lcer.harbinger_bridge_record_invalid")
    return value


def source_identity(root: Path) -> dict[str, str]:
    result = subprocess.run(["/usr/bin/git", "rev-parse", "HEAD", "HEAD^{tree}"], cwd=root,
                            env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"}, capture_output=True, text=True, check=False)
    if result.returncode != 0 or len(result.stdout.splitlines()) != 2:
        raise BridgeError("lcer.harbinger_bridge_record_invalid")
    commit, tree = result.stdout.splitlines()
    if not all(len(value) == 40 and all(char in "0123456789abcdef" for char in value) for value in (commit, tree)):
        raise BridgeError("lcer.harbinger_bridge_record_invalid")
    return {"commit": commit, "tree": tree}


def frozen_sources(root: Path, contract: dict[str, Any]) -> list[dict[str, str]]:
    primary, closure = contract.get("primary_sources"), contract.get("transitive_local_imports")
    if not isinstance(primary, list) or not isinstance(closure, dict) or not isinstance(closure.get("sources"), list):
        raise BridgeError("lcer.harbinger_bridge_record_invalid")
    sources = [*primary, *closure["sources"]]
    if len(sources) != 13:
        raise BridgeError("lcer.harbinger_bridge_record_invalid")
    result: list[dict[str, str]] = []
    for item in sources:
        if not isinstance(item, dict) or set(item) != {"path", "sha256", "kind"}:
            raise BridgeError("lcer.harbinger_bridge_record_invalid")
        path = Path(item["path"])
        if path.is_absolute() or ".." in path.parts:
            raise BridgeError("lcer.harbinger_bridge_record_invalid")
        source = root / path
        if source.is_symlink() or not source.is_file() or digest(source.read_bytes()) != item["sha256"]:
            raise BridgeError("lcer.source_audit_record_changed")
        result.append({"path": item["path"], "kind": item["kind"], "included_by": "city_frozen_phase_5_contract"})
    return result


def run_harbinger(cli: Path, *arguments: str, expected: int = 0) -> dict[str, Any]:
    result = subprocess.run([str(cli), *arguments, "--json"], cwd=cli.parent,
                            env={"PATH": "/usr/bin:/bin", "LC_ALL": "C", "PYTHONDONTWRITEBYTECODE": "1"},
                            capture_output=True, text=True, check=False)
    try:
        value = json.loads(result.stdout)
    except ValueError as error:
        raise BridgeError("lcer.harbinger_bridge_execution_invalid") from error
    if result.returncode != expected or not isinstance(value, dict):
        raise BridgeError("lcer.harbinger_bridge_execution_invalid")
    return value


def clean_output(root: Path, city_root: Path) -> None:
    if not root.is_absolute() or root == city_root or root.is_relative_to(city_root) or root.exists():
        raise BridgeError("lcer.harbinger_bridge_output_invalid")
    root.parent.mkdir(parents=True, exist_ok=True)
    if root.parent.is_symlink() or any(parent.is_symlink() for parent in root.parents):
        raise BridgeError("lcer.harbinger_bridge_output_invalid")
    root.mkdir(mode=0o700)


def audit(city_root: Path, harbinger_root: Path, output: Path) -> dict[str, Any]:
    city_root = city_root.resolve(); harbinger_root = harbinger_root.resolve(); output = output.resolve()
    cli = harbinger_root / "harbinger"
    contract_path = city_root / "proof_kernel/city_live_evidence_source_audit_contract.json"
    adapter_path = city_root / "proof_kernel/run_harbinger_city_source_effect_audit.py"
    if not cli.is_file() or cli.is_symlink() or not contract_path.is_file() or adapter_path.is_symlink():
        raise BridgeError("lcer.harbinger_bridge_record_invalid")
    contract_raw = contract_path.read_bytes(); contract = read_json(contract_path)
    if contract.get("schema") != "city.live_evidence_source_audit_contract.v1":
        raise BridgeError("lcer.harbinger_bridge_record_invalid")
    sources = frozen_sources(city_root, contract)
    clean_output(output, city_root)
    packet = output / "packet"; packet.mkdir(mode=0o700)
    scope = {"schema": "harbinger.scope.v2", "source_root": str(city_root), "files": sources}
    scope_path = packet / "scope.json"; write_json(scope_path, scope)
    snapshot_path = packet / "source-snapshot.json"
    run_harbinger(cli, "snapshot", "create", "--scope", str(scope_path), "--output", str(snapshot_path))
    policy = {"schema": "harbinger.inventory_policy.v2", "allowed_external_inputs": [], "allowed_consequences": [], "external_models": []}
    policy_path = packet / "inventory-policy.json"; write_json(policy_path, policy)
    copied_adapter = packet / "city_harbinger_adapter.py"; shutil.copyfile(adapter_path, copied_adapter)
    copied_contract = packet / "city-frozen-contract.json"; copied_contract.write_bytes(contract_raw)
    task_contract = {"schema": "city.harbinger_task_contract.v1", "city_contract_sha256": digest(contract_raw),
                     "primary_source_baseline_identity": contract["primary_source_baseline_identity"]}
    task_contract_path = packet / "task-contract.json"; write_json(task_contract_path, task_contract)
    runner = packet / "runner.sh"; runner.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8"); runner.chmod(0o700)
    def ref(path: Path) -> dict[str, str]:
        return {"path": path.name, "sha256": digest(path.read_bytes())}
    task = {
        "schema": "harbinger.task_manifest.v2", "task_id": "city/phase-5-source-effect",
        "target": {"repo": "CITY", "root": "."}, "source_snapshot": ref(snapshot_path),
        "adapter": {"id": "city-live-evidence", **ref(copied_adapter)}, "contract": ref(task_contract_path),
        "immutable_inputs": [
            {"role": "city_frozen_contract", **ref(copied_contract)},
            {"role": "source_scope", **ref(scope_path)}, {"role": "policy", **ref(policy_path)},
            {"role": "runner", **ref(runner)},
        ],
        "commands": [{"id": "observe-host-adapter", "argv": ["./runner.sh"], "depends_on": []}],
        "receipt_root": "runs/city-phase-5", "budgets": {"task_seconds": 30, "output_bytes": 1048576},
    }
    task_path = packet / "task.json"; write_json(task_path, task)
    preflight = run_harbinger(cli, "task", "preflight", "--manifest", str(task_path), "--output", str(packet / "preflight"))
    inventory = run_harbinger(cli, "inventory", "--snapshot", str(snapshot_path), "--policy", str(policy_path), "--output", str(packet / "inventory"))
    graph = Path(inventory["graph"])
    audit_contract = {"schema": "harbinger.adapter_contract.v2", "adapter_id": "city-live-evidence", "scope_closure": "partial",
                      "raw_graph": {"path": "inventory/source-effect-graph.json", "sha256": digest(graph.read_bytes())}}
    audit_contract_path = packet / "harbinger-adapter-contract.json"; write_json(audit_contract_path, audit_contract)
    candidate = run_harbinger(cli, "audit", "--adapter", "city-live-evidence", "--contract", str(audit_contract_path),
                              "--task-receipt", str(preflight["receipt"]), "--output", str(packet / "audit"), expected=1)
    receipt = Path(candidate["receipt"])
    run_harbinger(cli, "receipt", "validate", "--receipt", str(receipt))
    record = {"schema": SCHEMA, "status": "pass", "verdict": "raw_evidence_valid_incomplete",
              "claim_level": "raw_evidence_only", "city_source_identity": source_identity(city_root),
              "city_frozen_contract_sha256": digest(contract_raw), "harbinger_source_snapshot_sha256": digest(snapshot_path.read_bytes()),
              "harbinger_graph_sha256": digest(graph.read_bytes()), "harbinger_candidate_sha256": digest(Path(candidate["candidate"]).read_bytes()),
              "harbinger_receipt_sha256": digest(receipt.read_bytes()), "summary": inventory["summary"],
              "failure_codes": candidate["failure_codes"],
              "authority": {"may_open_acquisition": False, "may_open_release": False, "may_seal_phase_5": False}}
    record["record_sha256"] = digest(canonical(record))
    record_path = output / "city-harbinger-source-effect-record.json"; write_json(record_path, record)
    return {"status": "pass", "record": str(record_path), "summary": record["summary"],
            "failure_codes": record["failure_codes"], "claim_level": "raw_evidence_only"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Harbinger against CITY's frozen Phase 5 source scope")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--harbinger-root", default=None)
    parser.add_argument("--output", required=True); parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        city_root = Path(args.root).resolve()
        harbinger_root = Path(args.harbinger_root).resolve() if args.harbinger_root else city_root.parent / "Harbinger"
        print(json.dumps(audit(city_root, harbinger_root, Path(args.output)), sort_keys=True))
        return 0
    except (BridgeError, OSError, KeyError, TypeError) as error:
        print(json.dumps({"status": "fail", "failure_codes": [str(error)], "claim_level": "raw_evidence_only"}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
