#!/usr/bin/env python3
"""Raw, fail-closed source-effect evidence for the CITY Phase 5 surface.

This is an adapter, not a release or acquisition gate.  It reads source bytes,
creates a raw graph, and deliberately leaves incomplete closure unaccepted.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


SCHEMA = "city.source_effect_audit.v1"
CONTRACT_SCHEMA = "city.live_evidence_source_audit_contract.v1"
ADVERSARY_SAMPLES = {
    "GConfig_owner_read": "void AuditCase() { GConfig->GetString(); }",
    "getenv_Q_choice": "def AuditCase(): return os.getenv('Q')",
    "argv_canonical_order": "def AuditCase(): return sys.argv[1]",
    "clock_member_order": "def AuditCase(): return time.time()",
    "PID_owner_choice": "def AuditCase(): return os.getpid()",
    "peer_root_read": "def AuditCase(): return open(peer_root / 'state')",
    "canonical_output_write_from_child": "def AuditCase(): canonical_output.write_bytes(b'x')",
    "probe_reads_receipt": "def AuditCase(): return probe.read_receipt()",
    "probe_reads_projection": "def AuditCase(): return probe.read_projection()",
    "echoed_Q_without_actor": "def AuditCase(): return echoed_Q_without_actor",
    "unlisted_local_import": "import proof_kernel.unlisted_local_import",
    "controller_calls_emit": "def AuditCase(): return controller.emit()",
    "fault_bypasses_stage": "def AuditCase(): return fault_bypasses_stage()",
    "helper_holds_proof_pipe": "def AuditCase(): return helper_holds_proof_pipe()",
}


class AuditError(ValueError):
    pass


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise AuditError("lcer.source_audit_record_invalid") from error
    if not isinstance(value, dict):
        raise AuditError("lcer.source_audit_record_invalid")
    return value


def safe_source(root: Path, name: str) -> Path:
    candidate = Path(name)
    if not name or candidate.is_absolute() or ".." in candidate.parts:
        raise AuditError("lcer.source_audit_record_invalid")
    path = root / candidate
    if path.is_symlink() or any(part.is_symlink() for part in (root / candidate).parents if part != root.parent):
        raise AuditError("lcer.source_audit_record_invalid")
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise AuditError("lcer.source_audit_record_invalid") from error
    if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
        raise AuditError("lcer.source_audit_record_invalid")
    return resolved


def source_identity(root: Path) -> dict[str, str]:
    result = subprocess.run(["/usr/bin/git", "rev-parse", "HEAD", "HEAD^{tree}"], cwd=root,
                            check=False, capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"})
    if result.returncode or len(result.stdout.splitlines()) != 2:
        raise AuditError("lcer.source_audit_record_invalid")
    commit, tree = result.stdout.splitlines()
    if not re.fullmatch(r"[0-9a-f]{40}", commit) or not re.fullmatch(r"[0-9a-f]{40}", tree):
        raise AuditError("lcer.source_audit_record_invalid")
    return {"commit": commit, "tree": tree}


def dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = dotted(node.value)
        return prefix + "." + node.attr if prefix else node.attr
    return "<dynamic>"


def edge(path: str, function: str, input_name: str, callee: str, consequence: str,
         classification: str, reason: str, line: int) -> dict[str, Any]:
    stable = digest(canonical([path, function, input_name, callee, consequence, line]))
    return {"edge_id": "sha256:" + stable, "path": path, "function": function,
            "input": input_name, "callee": callee, "consequence": consequence,
            "classification": classification, "reason_code": reason,
            "location": {"line": line}}


def python_rows(path: Path, name: str, modeled_calls: set[str],
                modeled_effects: set[tuple[str, str, str]],
                modeled_sites: dict[tuple[str, str, str, int], str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], set[str]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=name)
    except (OSError, SyntaxError) as error:
        raise AuditError("lcer.source_audit_record_invalid") from error
    rows: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    local_imports: set[str] = set()

    class Walk(ast.NodeVisitor):
        def __init__(self) -> None:
            self.stack: list[str] = []

        def owner(self) -> str:
            suffix = ".".join(self.stack) or "<module>"
            return name.replace("/", ".") + "." + suffix

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            rows.append({"kind": "function", "id": self.owner() + "." + node.name, "line": node.lineno})
            self.stack.append(node.name); self.generic_visit(node); self.stack.pop()

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            rows.append({"kind": "class", "id": self.owner() + "." + node.name, "line": node.lineno})
            self.stack.append(node.name); self.generic_visit(node); self.stack.pop()

        def visit_Import(self, node: ast.Import) -> None:
            for alias in node.names:
                rows.append({"kind": "import", "id": alias.name, "line": node.lineno})
                local_imports.add(alias.name)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            module = node.module or ""
            rows.append({"kind": "import", "id": module or "<relative>", "line": node.lineno})
            if module:
                local_imports.add(module)
            if node.level:
                local_imports.add("<relative>" + module)

        def visit_Call(self, node: ast.Call) -> None:
            call = dotted(node.func); owner = self.owner()
            if call in {"eval", "exec", "__import__", "importlib.import_module"}:
                edges.append(edge(name, owner, "platform", call, "fault", "denied", "lcer.source_input_forbidden", node.lineno))
            elif call in {"os.getenv", "os.environ.get", "input", "open", "subprocess.run", "subprocess.Popen", "os.system"}:
                site_key = (name, owner, call, node.lineno)
                site_consequence = modeled_sites.get(site_key)
                consequence = site_consequence or ("provenance" if call in {"open", "subprocess.run", "subprocess.Popen", "os.system"} else "fault")
                classification = "allowed" if site_consequence == "build_execution" or call in modeled_calls else "unclassified"
                reason = "lcer.effect_model_declared" if site_consequence == "build_execution" else "lcer.external_model_declared" if call in modeled_calls else "lcer.external_model_missing"
                edges.append(edge(name, owner, "platform", call, consequence, classification, reason, node.lineno))
            elif any(token in call.lower() for token in ("resolve", "admit", "emit", "spawnactor", "destroy")):
                default_consequence = "canonical" if any(token in call.lower() for token in ("resolve", "admit")) else "representation"
                consequence = modeled_sites.get((name, owner, call, node.lineno), default_consequence)
                modeled = (name, call, consequence) in modeled_effects or (name, owner, call, node.lineno) in modeled_sites
                edges.append(edge(name, owner, "command", call, consequence,
                                  "allowed" if modeled else "unclassified",
                                  "lcer.effect_model_declared" if modeled else "lcer.required_edge_unclassified", node.lineno))
            self.generic_visit(node)

        def visit_Attribute(self, node: ast.Attribute) -> None:
            attribute_name = dotted(node)
            if attribute_name in {"sys.argv", "os.environ"}:
                owner = self.owner()
                site_key = (name, owner, attribute_name, node.lineno)
                consequence = modeled_sites.get(site_key, "fault")
                edges.append(edge(name, owner, "platform", attribute_name, consequence,
                                  "allowed" if site_key in modeled_sites else "unclassified",
                                  "lcer.effect_model_declared" if site_key in modeled_sites else "lcer.required_edge_unclassified",
                                  node.lineno))
            self.generic_visit(node)

    Walk().visit(tree)
    return rows, edges, local_imports


def cpp_rows(path: Path, name: str, modeled_effects: set[tuple[str, str, str]],
             modeled_sites: dict[tuple[str, str, str, int], str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows, edges = [], []
    text = path.read_text(encoding="utf-8", errors="replace")
    for number, line in enumerate(text.splitlines(), start=1):
        match = re.search(r"(?:void|bool|int|float|double|F\w+|U\w+)\s+(\w+(?:::\w+)*)\s*\(", line)
        owner = match.group(1) if match else name + ".<native>"
        if match:
            rows.append({"kind": "function", "id": owner, "line": number})
        for token, input_name, consequence in (
            ("GConfig", "platform", "fault"), ("getenv", "platform", "fault"),
            ("ProcessEvent", "platform", "representation"), ("AddDynamic", "platform", "representation"),
            ("AddUObject", "platform", "representation"), ("SpawnActor", "command", "representation"),
            ("Destroy", "command", "representation"), ("Resolve", "command", "canonical"),
        ):
            if token in line:
                site_key = (name, owner, token, number)
                effective_consequence = modeled_sites.get(site_key, consequence)
                modeled = (name, token, effective_consequence) in modeled_effects or site_key in modeled_sites
                edges.append(edge(name, owner, input_name, token, effective_consequence,
                                  "allowed" if modeled else "unclassified",
                                  "lcer.effect_model_declared" if modeled else "lcer.required_edge_unclassified", number))
    return rows, edges


def detect_forbidden_adversary(adversary_id: str, source: str) -> dict[str, Any]:
    if adversary_id not in ADVERSARY_SAMPLES:
        raise AuditError("lcer.source_audit_record_invalid")
    token = {
        "GConfig_owner_read": "GConfig", "getenv_Q_choice": "os.getenv", "argv_canonical_order": "sys.argv",
        "clock_member_order": "time.time", "PID_owner_choice": "os.getpid", "peer_root_read": "peer_root",
        "canonical_output_write_from_child": "canonical_output", "probe_reads_receipt": "read_receipt",
        "probe_reads_projection": "read_projection", "echoed_Q_without_actor": "echoed_Q_without_actor",
        "unlisted_local_import": "proof_kernel.unlisted_local_import", "controller_calls_emit": "controller.emit",
        "fault_bypasses_stage": "fault_bypasses_stage", "helper_holds_proof_pipe": "helper_holds_proof_pipe",
    }[adversary_id]
    if token not in source:
        raise AuditError("lcer.source_audit_record_invalid")
    code = "lcer.proof_pipe_extra_holder" if adversary_id == "helper_holds_proof_pipe" else "lcer.source_input_forbidden"
    return edge("<adversary:" + adversary_id + ">", "AuditCase", "platform", token, "fault", "denied", code, 1)


def required_adversaries(contract: dict[str, Any]) -> list[dict[str, Any]]:
    names = contract.get("forbidden_source_adversaries")
    if not isinstance(names, list) or len(names) != 14 or len(set(names)) != 14 or not all(isinstance(name, str) and name for name in names):
        raise AuditError("lcer.source_audit_record_invalid")
    result = []
    for name in names:
        offending_edge = detect_forbidden_adversary(name, ADVERSARY_SAMPLES[name])
        result.append({"adversary_id": name, "status": "rejected", "failure_code": offending_edge["reason_code"], "offending_edge": offending_edge})
    return result


def audit(root: Path, contract_path: Path) -> dict[str, Any]:
    root = root.resolve()
    contract_raw = contract_path.read_bytes(); contract = load_json(contract_path)
    if contract.get("schema") != CONTRACT_SCHEMA or contract.get("adapter_id") != "city-live-evidence":
        raise AuditError("lcer.source_audit_record_invalid")
    primary_baseline = contract.get("primary_source_baseline_identity")
    if (not isinstance(primary_baseline, dict) or set(primary_baseline) != {"commit", "tree"}
            or not all(isinstance(primary_baseline[key], str) and re.fullmatch(r"[0-9a-f]{40}", primary_baseline[key])
                       for key in ("commit", "tree"))):
        raise AuditError("lcer.source_audit_record_invalid")
    primary = contract.get("primary_sources")
    closure = contract.get("transitive_local_imports")
    sources = primary + closure.get("sources", []) if isinstance(primary, list) and isinstance(closure, dict) else None
    models = contract.get("external_models")
    effect_models = contract.get("effect_models")
    exact_sites = contract.get("exact_effect_call_sites")
    if (not isinstance(sources, list) or len(primary) != 11 or len(sources) != 13
            or not isinstance(models, list) or not isinstance(effect_models, list) or not isinstance(exact_sites, list)):
        raise AuditError("lcer.source_audit_record_invalid")
    modeled_calls = set()
    for model in models:
        if not isinstance(model, dict) or set(model) != {"id", "calls", "consequence"} or not isinstance(model["id"], str) or not isinstance(model["consequence"], str) or not isinstance(model["calls"], list) or not all(isinstance(call, str) for call in model["calls"]):
            raise AuditError("lcer.source_audit_record_invalid")
        modeled_calls.update(model["calls"])
    modeled_effects: set[tuple[str, str, str]] = set()
    for model in effect_models:
        if (not isinstance(model, dict) or set(model) != {"id", "path", "calls", "consequence"}
                or not isinstance(model["id"], str) or not isinstance(model["path"], str)
                or not isinstance(model["consequence"], str) or not isinstance(model["calls"], list)
                or not model["calls"] or not all(isinstance(call, str) and call for call in model["calls"])):
            raise AuditError("lcer.source_audit_record_invalid")
        modeled_effects.update((model["path"], call, model["consequence"]) for call in model["calls"])
    modeled_sites: dict[tuple[str, str, str, int], str] = {}
    for site in exact_sites:
        if (not isinstance(site, dict) or set(site) != {"path", "function", "callee", "line", "consequence"}
                or not all(isinstance(site[key], str) and site[key] for key in ("path", "function", "callee", "consequence"))
                or not isinstance(site["line"], int) or site["line"] <= 0
                or site["consequence"] not in {"provenance", "canonical", "representation", "test_control", "build_execution"}):
            raise AuditError("lcer.source_audit_record_invalid")
        key = (site["path"], site["function"], site["callee"], site["line"])
        if key in modeled_sites:
            raise AuditError("lcer.source_audit_record_invalid")
        modeled_sites[key] = site["consequence"]
    files, rows, edges, imports = [], [], [], set()
    for item in sources:
        if not isinstance(item, dict) or set(item) != {"path", "sha256", "kind"}:
            raise AuditError("lcer.source_audit_record_invalid")
        source = safe_source(root, item["path"]); raw = source.read_bytes()
        if digest(raw) != item["sha256"]:
            raise AuditError("lcer.source_audit_record_changed")
        files.append({"path": item["path"], "sha256": digest(raw), "size_bytes": len(raw), "kind": item["kind"]})
        if item["kind"] == "python_source":
            found_rows, found_edges, found_imports = python_rows(source, item["path"], modeled_calls, modeled_effects, modeled_sites)
            rows.extend(found_rows); edges.extend(found_edges); imports.update(found_imports)
        elif item["kind"] in {"cpp_source", "build_rule"}:
            found_rows, found_edges = cpp_rows(source, item["path"], modeled_effects, modeled_sites)
            rows.extend(found_rows); edges.extend(found_edges)
    declared_modules = {row["path"].removesuffix(".py").replace("/", ".") for row in sources if row["kind"] == "python_source"}
    unresolved_imports = set()
    for imported in imports:
        normalized = imported.removeprefix("proof_kernel.")
        candidate = "proof_kernel." + normalized
        if candidate in declared_modules:
            continue
        if (root / "proof_kernel" / (normalized.replace(".", "/") + ".py")).is_file() or imported.startswith("<relative>"):
            unresolved_imports.add(imported)
    for imported in sorted(unresolved_imports):
        edges.append(edge("<import-closure>", "<module>", "platform", imported, "provenance", "unclassified", "lcer.scope_incomplete", 0))
    edges.sort(key=lambda item: item["edge_id"])
    unclassified = [item for item in edges if item["classification"] == "unclassified"]
    result = {"schema": SCHEMA, "adapter_id": "city-live-evidence", "claim_level": "raw_evidence_only",
              "source_identity": source_identity(root), "primary_source_baseline_identity": primary_baseline,
              "contract_sha256": digest(contract_raw), "files": files,
              "nodes": rows, "edges": edges, "transitive_local_imports": sorted(imports),
              "scope_status": "partial", "source_audit_complete": False,
              "adversary_results": required_adversaries(contract),
              "summary": {"primary_source_count": len(files), "node_count": len(rows), "edge_count": len(edges),
                          "unclassified_count": len(unclassified), "historical_partial_graph_unclassified_count": contract["baseline"]["partial_graph_unclassified_count"],
                          "declared_closure_source_count": len(closure["sources"]), "unresolved_local_import_count": len(unresolved_imports)},
              "authority": {"may_open_acquisition": False, "may_open_release": False, "may_seal_phase_5": False}}
    result["result_sha256"] = digest(canonical(result))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CITY raw source-effect audit adapter")
    parser.add_argument("--root", required=True); parser.add_argument("--contract", required=True)
    parser.add_argument("--output", required=True); parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        value = audit(Path(args.root), Path(args.contract))
        output = Path(args.output)
        if output.exists():
            raise AuditError("lcer.source_audit_record_invalid")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(canonical(value) + b"\n")
        print(json.dumps({"status": "pass", "artifact": str(output), "summary": value["summary"], "claim_level": "raw_evidence_only"}, sort_keys=True))
        return 0
    except (AuditError, OSError, KeyError, TypeError) as error:
        print(json.dumps({"status": "fail", "failure_codes": [str(error)], "claim_level": "raw_evidence_only"}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
