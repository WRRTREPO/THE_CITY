#!/usr/bin/env python3
"""Interpret a hash-bound Harbinger raw graph under CITY's frozen policy."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA = "city.harbinger_policy_adapter.v1"
POLICY_SCHEMA = "city.harbinger_policy_contract.v1"
AUTHORITY = {"may_open_acquisition": False, "may_open_release": False, "may_seal_phase_5": False}


class PolicyError(ValueError):
    pass


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def file_digest(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise PolicyError("lcer.harbinger_policy_record_invalid")
    return digest(path.read_bytes())


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise PolicyError("lcer.harbinger_policy_record_invalid") from error
    if not isinstance(value, dict):
        raise PolicyError("lcer.harbinger_policy_record_invalid")
    return value


def write_json(path: Path, value: Any) -> None:
    path.write_bytes(canonical(value) + b"\n")


def require_digest(value: Any) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise PolicyError("lcer.harbinger_policy_record_invalid")
    return value


def load_policy(root: Path) -> tuple[dict[str, Any], Path]:
    path = root / "proof_kernel/city_harbinger_policy_contract.json"
    policy = read_json(path)
    if policy.get("schema") != POLICY_SCHEMA or policy.get("authority") != AUTHORITY:
        raise PolicyError("lcer.harbinger_policy_record_invalid")
    city = policy.get("city_frozen_contract")
    core = policy.get("harbinger_core")
    unmapped = policy.get("required_unmapped_edge")
    if (not isinstance(city, dict) or city.get("path") != "proof_kernel/city_live_evidence_source_audit_contract.json"
            or not isinstance(core, dict) or unmapped != {"classification": "unclassified", "reason_code": "lcer.harbinger_edge_unmapped"}
            or not isinstance(policy.get("allowed_exact_test_controls"), list)
            or not isinstance(policy.get("allowed_exact_provenance_reads"), list)
            or not isinstance(policy.get("allowed_exact_build_execution"), list)):
        raise PolicyError("lcer.harbinger_policy_record_invalid")
    require_digest(city.get("sha256")); require_digest(core.get("sha256"))
    return policy, path


def validate_frozen_sources(root: Path, policy: dict[str, Any]) -> tuple[dict[str, Any], Path]:
    source_path = root / policy["city_frozen_contract"]["path"]
    if file_digest(source_path) != policy["city_frozen_contract"]["sha256"]:
        raise PolicyError("lcer.harbinger_policy_record_invalid")
    contract = read_json(source_path)
    if contract.get("schema") != "city.live_evidence_source_audit_contract.v1":
        raise PolicyError("lcer.harbinger_policy_record_invalid")
    primary = contract.get("primary_sources")
    closure = contract.get("transitive_local_imports", {}).get("sources")
    if not isinstance(primary, list) or not isinstance(closure, list) or len(primary) + len(closure) != 13:
        raise PolicyError("lcer.harbinger_policy_record_invalid")
    for row in [*primary, *closure]:
        if not isinstance(row, dict) or set(row) != {"path", "sha256", "kind"}:
            raise PolicyError("lcer.harbinger_policy_record_invalid")
        relative = Path(row["path"])
        if relative.is_absolute() or ".." in relative.parts or file_digest(root / relative) != row["sha256"]:
            raise PolicyError("lcer.harbinger_policy_record_invalid")
    exact_sites = contract.get("exact_effect_call_sites")
    if not isinstance(exact_sites, list):
        raise PolicyError("lcer.harbinger_policy_record_invalid")
    for category, consequence in (("allowed_exact_provenance_reads", "provenance"),
                                  ("allowed_exact_build_execution", "build_execution")):
      for permitted in policy[category]:
        if (not isinstance(permitted, dict)
                or set(permitted) != {"family", "path", "line", "callable", "token", "reference"}
                or permitted.get("family") != "function_to_consequence"
                or not isinstance(permitted.get("line"), int)
                or not all(isinstance(permitted.get(key), str) and permitted[key]
                           for key in ("path", "callable", "token"))
                or not isinstance(permitted.get("reference"), dict)
                or permitted["reference"] != {"path": permitted["path"], "function": permitted["callable"],
                                                "callee": permitted["token"], "line": permitted["line"],
                                                "consequence": consequence}
                or permitted["reference"] not in exact_sites):
            raise PolicyError("lcer.harbinger_policy_record_invalid")
    return contract, source_path


def edge_shape(edge: dict[str, Any]) -> tuple[str, str, int, str, str]:
    location, origin, target = edge.get("location"), edge.get("from"), edge.get("to")
    if (not isinstance(location, dict) or not isinstance(origin, dict) or not isinstance(target, dict)
            or not isinstance(location.get("path"), str) or not isinstance(location.get("line"), int)
            or not isinstance(origin.get("id"), str) or not isinstance(target.get("id"), str)):
        raise PolicyError("lcer.harbinger_policy_record_invalid")
    family = edge.get("family")
    if family == "function_to_consequence":
        return family, location["path"], location["line"], origin["id"], target["id"]
    if family == "external_input_to_callable":
        return family, location["path"], location["line"], target["id"], origin["id"]
    raise PolicyError("lcer.harbinger_policy_record_invalid")


def decision_for(edge: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    edge_id = edge.get("edge_id")
    if not isinstance(edge_id, str) or not edge_id.startswith("sha256:"):
        raise PolicyError("lcer.harbinger_policy_record_invalid")
    family, path, line, callable_name, token = edge_shape(edge)
    base = {"edge_id": edge_id, "graph_family": family, "source_path": path, "source_line": line,
            "source_callable": callable_name, "harbinger_token": token}
    for permitted in policy["allowed_exact_test_controls"]:
        if not isinstance(permitted, dict):
            raise PolicyError("lcer.harbinger_policy_record_invalid")
        if (family == permitted.get("family") and path == permitted.get("path") and line == permitted.get("line")
                and callable_name == permitted.get("callable") and token == permitted.get("token")):
            return {**base, "classification": "allowed", "city_classification": "test_control",
                    "city_reason_code": "lcer.exact_test_control", "city_contract_reference": permitted.get("reference")}
    for permitted in policy["allowed_exact_provenance_reads"]:
        if not isinstance(permitted, dict):
            raise PolicyError("lcer.harbinger_policy_record_invalid")
        if (family == permitted.get("family") and path == permitted.get("path") and line == permitted.get("line")
                and callable_name == permitted.get("callable") and token == permitted.get("token")):
            return {**base, "classification": "allowed", "city_classification": "provenance",
                    "city_reason_code": "lcer.exact_provenance_read", "city_contract_reference": permitted.get("reference")}
    for permitted in policy["allowed_exact_build_execution"]:
        if not isinstance(permitted, dict):
            raise PolicyError("lcer.harbinger_policy_record_invalid")
        if (family == permitted.get("family") and path == permitted.get("path") and line == permitted.get("line")
                and callable_name == permitted.get("callable") and token == permitted.get("token")):
            return {**base, "classification": "allowed", "city_classification": "build_execution",
                    "city_reason_code": "lcer.exact_build_execution", "city_contract_reference": permitted.get("reference")}
    return {**base, "classification": "unclassified", "city_classification": "unresolved",
            "city_reason_code": "lcer.harbinger_edge_unmapped", "city_contract_reference": None}


def validate_decision(decision: dict[str, Any], edge: dict[str, Any], policy: dict[str, Any]) -> None:
    expected = decision_for(edge, policy)
    if decision != expected:
        raise PolicyError("lcer.harbinger_policy_record_invalid")
    if decision["classification"] not in {"allowed", "denied", "unclassified"}:
        raise PolicyError("lcer.harbinger_policy_record_invalid")
    token = decision["harbinger_token"]
    if decision["classification"] == "allowed" and (token in {"self._emit", "<dynamic>.resolve"} or "<dynamic>.resolve" in decision["source_callable"]):
        raise PolicyError("lcer.harbinger_policy_record_invalid")


def load_bridge_packet(root: Path, bridge_path: Path, policy: dict[str, Any]) -> dict[str, Any]:
    bridge = read_json(bridge_path)
    if bridge.get("schema") != "city.harbinger_source_effect_bridge.v1" or bridge.get("status") != "pass" or bridge.get("verdict") != "raw_evidence_valid_incomplete" or bridge.get("authority") != AUTHORITY:
        raise PolicyError("lcer.harbinger_policy_record_invalid")
    bridge_hash = bridge.get("record_sha256")
    if bridge_hash != digest(canonical({key: value for key, value in bridge.items() if key != "record_sha256"})):
        raise PolicyError("lcer.harbinger_policy_record_invalid")
    packet = bridge_path.parent / "packet"
    paths = {"snapshot": packet / "source-snapshot.json", "graph": packet / "inventory/source-effect-graph.json",
             "candidate": packet / "audit/audit-candidate.json", "receipt": packet / "audit/receipt.json"}
    fields = {"snapshot": "harbinger_source_snapshot_sha256", "graph": "harbinger_graph_sha256",
              "candidate": "harbinger_candidate_sha256", "receipt": "harbinger_receipt_sha256"}
    for name, path in paths.items():
        if file_digest(path) != require_digest(bridge.get(fields[name])):
            raise PolicyError("lcer.harbinger_policy_record_invalid")
    snapshot, graph, candidate, receipt = (read_json(paths[name]) for name in ("snapshot", "graph", "candidate", "receipt"))
    if (snapshot.get("schema") != "harbinger.source_snapshot.v2" or graph.get("schema") != "harbinger.source_effect_graph.v2"
            or graph.get("source_snapshot_sha256") != bridge[fields["snapshot"]] or not isinstance(graph.get("edges"), list)
            or candidate.get("schema") != "harbinger.audit_candidate.v2" or candidate.get("raw_graph", {}).get("sha256") != bridge[fields["graph"]]
            or receipt.get("schema") != "harbinger.run_receipt.v2" or receipt.get("source_snapshot_sha256") != bridge[fields["snapshot"]]):
        raise PolicyError("lcer.harbinger_policy_record_invalid")
    core = root.parent / "Harbinger/harbinger"
    if file_digest(core) != policy["harbinger_core"]["sha256"]:
        raise PolicyError("lcer.harbinger_policy_record_invalid")
    return {"bridge": bridge, "bridge_sha256": file_digest(bridge_path), "paths": paths, "graph": graph}


def record_payload(root: Path, bridge_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    policy, policy_path = load_policy(root)
    source_contract, _ = validate_frozen_sources(root, policy)
    packet = load_bridge_packet(root, bridge_path, policy)
    edges = packet["graph"]["edges"]
    decisions = [decision_for(edge, policy) for edge in sorted(edges, key=lambda row: row.get("edge_id", ""))]
    if len({row["edge_id"] for row in decisions}) != len(edges):
        raise PolicyError("lcer.harbinger_policy_record_invalid")
    for decision, edge in zip(decisions, sorted(edges, key=lambda row: row.get("edge_id", ""))):
        validate_decision(decision, edge, policy)
    bridge = packet["bridge"]
    bound = {"schema": "city.harbinger_bound_policy_contract.v1", "city_policy_contract_sha256": file_digest(policy_path),
             "city_frozen_contract_sha256": file_digest(root / policy["city_frozen_contract"]["path"]),
             "harbinger_core_sha256": policy["harbinger_core"]["sha256"], "harbinger_source_snapshot_sha256": bridge["harbinger_source_snapshot_sha256"],
             "harbinger_graph_sha256": bridge["harbinger_graph_sha256"], "harbinger_candidate_sha256": bridge["harbinger_candidate_sha256"],
             "harbinger_receipt_sha256": bridge["harbinger_receipt_sha256"], "edge_decisions": decisions,
             "required_unmapped_edge": policy["required_unmapped_edge"], "authority": AUTHORITY}
    record = {"schema": SCHEMA, "status": "pass", "verdict": "raw_evidence_valid_incomplete", "source_identity": bridge["city_source_identity"],
              "city_frozen_contract_sha256": file_digest(root / policy["city_frozen_contract"]["path"]), "harbinger_snapshot_sha256": bridge["harbinger_source_snapshot_sha256"],
              "harbinger_graph_sha256": bridge["harbinger_graph_sha256"], "harbinger_candidate_sha256": bridge["harbinger_candidate_sha256"],
              "harbinger_receipt_sha256": bridge["harbinger_receipt_sha256"], "harbinger_core_sha256": policy["harbinger_core"]["sha256"],
              "harbinger_bridge_record_path": str(bridge_path), "harbinger_bridge_record_sha256": packet["bridge_sha256"],
              "city_policy_contract_sha256": file_digest(policy_path),
              "mapped_edge_count": sum(row["classification"] != "unclassified" for row in decisions),
              "unclassified_edge_count": sum(row["classification"] == "unclassified" for row in decisions), "edge_decisions": decisions,
              "retained_city_adversary_limit": policy["retained_city_adversary_limit"], "authority": AUTHORITY}
    record["record_sha256"] = digest(canonical(record))
    return bound, record


def prepare_output(output: Path, root: Path) -> None:
    if not output.is_absolute() or output.exists() or output == root or output.is_relative_to(root):
        raise PolicyError("lcer.harbinger_policy_record_invalid")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir(mode=0o700)


def adapt(root: Path, bridge_path: Path, output: Path) -> dict[str, Any]:
    root = root.resolve(); bridge_path = bridge_path.resolve(); output = output.resolve()
    bound, record = record_payload(root, bridge_path)
    prepare_output(output, root)
    bound_path, record_path = output / "city-harbinger-bound-policy-contract.json", output / "city-harbinger-policy-record.json"
    write_json(bound_path, bound); write_json(record_path, record)
    return {"status": "pass", "verdict": record["verdict"], "record": str(record_path), "mapped_edge_count": record["mapped_edge_count"], "unclassified_edge_count": record["unclassified_edge_count"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply CITY policy to a Harbinger raw graph")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1])); parser.add_argument("--bridge-record", required=True)
    parser.add_argument("--output", required=True); parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(adapt(Path(args.root), Path(args.bridge_record), Path(args.output)), sort_keys=True)); return 0
    except (PolicyError, OSError, TypeError, KeyError) as error:
        print(json.dumps({"status": "fail", "failure_codes": [str(error)]}, sort_keys=True)); return 2


if __name__ == "__main__":
    raise SystemExit(main())
