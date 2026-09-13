#!/usr/bin/env python3
"""Independent recomputation for CITY's Harbinger policy record."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


AUTHORITY = {"may_open_acquisition": False, "may_open_release": False, "may_seal_phase_5": False}


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def reject() -> None:
    raise ValueError("lcer.harbinger_policy_record_invalid")


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError("lcer.harbinger_policy_record_invalid") from error
    if not isinstance(value, dict): reject()
    return value


def file_digest(path: Path) -> str:
    if path.is_symlink() or not path.is_file(): reject()
    return digest(path.read_bytes())


def required_digest(value: Any) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value): reject()
    return value


def load_policy(root: Path) -> tuple[dict[str, Any], Path]:
    path = root / "proof_kernel/city_harbinger_policy_contract.json"; value = read_json(path)
    required = {"schema", "city_frozen_contract", "harbinger_core", "required_unmapped_edge", "allowed_exact_test_controls", "retained_city_adversary_limit", "authority"}
    if set(value) != required or value.get("schema") != "city.harbinger_policy_contract.v1" or value.get("authority") != AUTHORITY: reject()
    city, core = value["city_frozen_contract"], value["harbinger_core"]
    if (not isinstance(city, dict) or set(city) != {"path", "sha256"} or city["path"] != "proof_kernel/city_live_evidence_source_audit_contract.json"
            or not isinstance(core, dict) or set(core) != {"path", "sha256"} or not isinstance(value["allowed_exact_test_controls"], list)
            or value["required_unmapped_edge"] != {"classification": "unclassified", "reason_code": "lcer.harbinger_edge_unmapped"}): reject()
    if file_digest(root / city["path"]) != required_digest(city["sha256"]) or file_digest((root / core["path"]).resolve()) != required_digest(core["sha256"]): reject()
    return value, path


def verify_frozen_sources(root: Path) -> None:
    contract = read_json(root / "proof_kernel/city_live_evidence_source_audit_contract.json")
    primary, closure = contract.get("primary_sources"), contract.get("transitive_local_imports", {}).get("sources")
    if contract.get("schema") != "city.live_evidence_source_audit_contract.v1" or not isinstance(primary, list) or not isinstance(closure, list) or len(primary) + len(closure) != 13: reject()
    for source in [*primary, *closure]:
        if not isinstance(source, dict) or set(source) != {"path", "sha256", "kind"}: reject()
        path = Path(source["path"])
        if path.is_absolute() or ".." in path.parts or file_digest(root / path) != required_digest(source["sha256"]): reject()


def edge_shape(edge: dict[str, Any]) -> tuple[str, str, int, str, str]:
    location, origin, target = edge.get("location"), edge.get("from"), edge.get("to")
    if (not isinstance(location, dict) or not isinstance(origin, dict) or not isinstance(target, dict)
            or not isinstance(location.get("path"), str) or not isinstance(location.get("line"), int)
            or not isinstance(origin.get("id"), str) or not isinstance(target.get("id"), str)): reject()
    if edge.get("family") == "function_to_consequence": return "function_to_consequence", location["path"], location["line"], origin["id"], target["id"]
    if edge.get("family") == "external_input_to_callable": return "external_input_to_callable", location["path"], location["line"], target["id"], origin["id"]
    reject()


def expected_decision(edge: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    edge_id = edge.get("edge_id")
    if not isinstance(edge_id, str) or not edge_id.startswith("sha256:"): reject()
    family, path, line, callable_name, token = edge_shape(edge)
    base = {"edge_id": edge_id, "graph_family": family, "source_path": path, "source_line": line, "source_callable": callable_name, "harbinger_token": token}
    for permitted in policy["allowed_exact_test_controls"]:
        if not isinstance(permitted, dict): reject()
        if (family, path, line, callable_name, token) == (permitted.get("family"), permitted.get("path"), permitted.get("line"), permitted.get("callable"), permitted.get("token")):
            if token in {"self._emit", "<dynamic>.resolve"}: reject()
            return {**base, "classification": "allowed", "city_classification": "test_control", "city_reason_code": "lcer.exact_test_control", "city_contract_reference": permitted.get("reference")}
    return {**base, "classification": "unclassified", "city_classification": "unresolved", "city_reason_code": "lcer.harbinger_edge_unmapped", "city_contract_reference": None}


def load_bridge(bridge_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    bridge = read_json(bridge_path)
    if (bridge.get("schema") != "city.harbinger_source_effect_bridge.v1" or bridge.get("status") != "pass" or bridge.get("verdict") != "raw_evidence_valid_incomplete"
            or bridge.get("authority") != AUTHORITY or bridge.get("record_sha256") != digest(canonical({k: v for k, v in bridge.items() if k != "record_sha256"}))): reject()
    packet = bridge_path.parent / "packet"
    paths = {"snapshot": packet / "source-snapshot.json", "graph": packet / "inventory/source-effect-graph.json", "candidate": packet / "audit/audit-candidate.json", "receipt": packet / "audit/receipt.json"}
    fields = {"snapshot": "harbinger_source_snapshot_sha256", "graph": "harbinger_graph_sha256", "candidate": "harbinger_candidate_sha256", "receipt": "harbinger_receipt_sha256"}
    for name, path in paths.items():
        if file_digest(path) != required_digest(bridge.get(fields[name])): reject()
    snapshot, graph, candidate, receipt = (read_json(paths[name]) for name in ("snapshot", "graph", "candidate", "receipt"))
    if (snapshot.get("schema") != "harbinger.source_snapshot.v2" or graph.get("schema") != "harbinger.source_effect_graph.v2" or not isinstance(graph.get("edges"), list)
            or graph.get("source_snapshot_sha256") != bridge[fields["snapshot"]] or candidate.get("schema") != "harbinger.audit_candidate.v2"
            or candidate.get("raw_graph", {}).get("sha256") != bridge[fields["graph"]] or receipt.get("schema") != "harbinger.run_receipt.v2"
            or receipt.get("source_snapshot_sha256") != bridge[fields["snapshot"]]): reject()
    return bridge, graph


def expected_payload(root: Path, bridge_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    policy, policy_path = load_policy(root); verify_frozen_sources(root); bridge, graph = load_bridge(bridge_path)
    edges = sorted(graph["edges"], key=lambda row: row.get("edge_id", "")); decisions = [expected_decision(edge, policy) for edge in edges]
    if len({row["edge_id"] for row in decisions}) != len(edges): reject()
    frozen = root / policy["city_frozen_contract"]["path"]
    bound = {"schema": "city.harbinger_bound_policy_contract.v1", "city_policy_contract_sha256": file_digest(policy_path), "city_frozen_contract_sha256": file_digest(frozen), "harbinger_core_sha256": policy["harbinger_core"]["sha256"], "harbinger_source_snapshot_sha256": bridge["harbinger_source_snapshot_sha256"], "harbinger_graph_sha256": bridge["harbinger_graph_sha256"], "harbinger_candidate_sha256": bridge["harbinger_candidate_sha256"], "harbinger_receipt_sha256": bridge["harbinger_receipt_sha256"], "edge_decisions": decisions, "required_unmapped_edge": policy["required_unmapped_edge"], "authority": AUTHORITY}
    record = {"schema": "city.harbinger_policy_adapter.v1", "status": "pass", "verdict": "raw_evidence_valid_incomplete", "source_identity": bridge["city_source_identity"], "city_frozen_contract_sha256": file_digest(frozen), "harbinger_snapshot_sha256": bridge["harbinger_source_snapshot_sha256"], "harbinger_graph_sha256": bridge["harbinger_graph_sha256"], "harbinger_candidate_sha256": bridge["harbinger_candidate_sha256"], "harbinger_receipt_sha256": bridge["harbinger_receipt_sha256"], "harbinger_core_sha256": policy["harbinger_core"]["sha256"], "harbinger_bridge_record_path": str(bridge_path), "harbinger_bridge_record_sha256": file_digest(bridge_path), "city_policy_contract_sha256": file_digest(policy_path), "mapped_edge_count": sum(row["classification"] != "unclassified" for row in decisions), "unclassified_edge_count": sum(row["classification"] == "unclassified" for row in decisions), "edge_decisions": decisions, "retained_city_adversary_limit": policy["retained_city_adversary_limit"], "authority": AUTHORITY}
    record["record_sha256"] = digest(canonical(record)); return bound, record


def validate(record_path: Path, root: Path, bridge_path: Path | None = None) -> dict[str, Any]:
    actual = read_json(record_path.resolve()); declared = actual.get("harbinger_bridge_record_path")
    bridge = bridge_path.resolve() if bridge_path else Path(declared).resolve() if isinstance(declared, str) else None
    if bridge is None or str(bridge) != declared: reject()
    bound, expected = expected_payload(root.resolve(), bridge)
    if actual != expected or read_json(record_path.resolve().parent / "city-harbinger-bound-policy-contract.json") != bound: reject()
    return {"status": "pass", "verdict": actual["verdict"], "record_sha256": actual["record_sha256"], "mapped_edge_count": actual["mapped_edge_count"], "unclassified_edge_count": actual["unclassified_edge_count"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Independently verify a CITY Harbinger policy record")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1])); parser.add_argument("--record", required=True); parser.add_argument("--bridge-record"); parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(validate(Path(args.record), Path(args.root), Path(args.bridge_record) if args.bridge_record else None), sort_keys=True)); return 0
    except (ValueError, OSError, TypeError, KeyError) as error:
        print(json.dumps({"status": "fail", "failure_codes": [str(error)]}, sort_keys=True)); return 2


if __name__ == "__main__":
    raise SystemExit(main())
