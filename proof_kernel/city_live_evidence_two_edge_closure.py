#!/usr/bin/env python3
"""Construct a fail-closed record for CITY's two controlled development edges."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any

AUTHORITY = {"may_open_acquisition": False, "may_open_release": False, "may_seal_phase_5": False}
class ClosureError(ValueError): pass
def canonical(value: Any) -> bytes: return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
def digest(raw: bytes) -> str: return hashlib.sha256(raw).hexdigest()
def load(path: Path) -> dict[str, Any]:
    try: value = json.loads(path.read_text())
    except (OSError, ValueError) as error: raise ClosureError("lcer.two_edge_closure_invalid") from error
    if not isinstance(value, dict): raise ClosureError("lcer.two_edge_closure_invalid")
    return value
def contract(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    closure = load(root / "proof_kernel/city_live_evidence_two_edge_closure_contract.json")
    unsigned = {k:v for k,v in closure.items() if k != "record_sha256"}
    source = root / "proof_kernel/city_live_evidence_source_audit_contract.json"
    if (closure.get("schema") != "city.live_evidence_two_edge_closure_contract.v1" or closure.get("authority") != AUTHORITY
            or closure.get("record_sha256") != digest(canonical(unsigned)) or digest(source.read_bytes()) != closure.get("source_audit_contract_sha256")):
        raise ClosureError("lcer.two_edge_closure_invalid")
    audit = load(source); files = [*audit.get("primary_sources", []), *audit.get("transitive_local_imports", {}).get("sources", [])]
    if (len(files) != closure.get("source_file_count") or digest(canonical(files)) != closure.get("source_file_manifest_sha256")
            or any(not (root / row["path"]).is_file() or digest((root / row["path"]).read_bytes()) != row["sha256"] for row in files)):
        raise ClosureError("lcer.two_edge_closure_invalid")
    return closure, audit
def environment(keys: list[str], owned: Path) -> dict[str, str]:
    base = {"PATH":"/usr/bin:/bin", "LANG":"C", "LC_ALL":"C", "PYTHONDONTWRITEBYTECODE":"1", "HOME":"/var/empty", "TMPDIR":str(owned / "tmp"), "PYTHONPYCACHEPREFIX":str(owned / "pycache")}
    if sorted(keys) != sorted(set(keys)) or any(key not in base for key in keys): raise ClosureError("lcer.build_environment_unsealed")
    return {key: base[key] for key in keys}
def construct(root: Path, output: Path) -> dict[str, Any]:
    root = root.resolve(); output = output.resolve(); closure, audit_contract = contract(root)
    if not output.is_absolute() or output.exists() or output.is_relative_to(root): raise ClosureError("lcer.two_edge_closure_invalid")
    files = [*audit_contract["primary_sources"], *audit_contract["transitive_local_imports"]["sources"]]
    build_env, closure_env = environment(closure["build_environment_keys"], output), environment(closure["closure_environment_keys"], output)
    references = audit_contract["exact_effect_call_sites"]
    if any({"path":row["path"],"function":row["callable"],"callee":row["token"],"line":row["line"],"consequence":row["consequence"]} not in references for row in closure["edges"]): raise ClosureError("lcer.two_edge_closure_invalid")
    record = {"schema":"city.live_evidence_two_edge_closure_record.v1","status":"pass","verdict":"raw_evidence_valid_incomplete","closure_contract_sha256":digest((root / "proof_kernel/city_live_evidence_two_edge_closure_contract.json").read_bytes()),"source_audit_contract_sha256":closure["source_audit_contract_sha256"],"source_files":files,"edges":closure["edges"],"build_environment":{"keys":sorted(build_env),"sha256":digest(canonical(build_env))},"closure_environment":{"keys":sorted(closure_env),"sha256":digest(canonical(closure_env))},"authority":AUTHORITY,"retained_denials":["lcer.acquisition_implementation_incomplete","lcer.release_semantics_not_implemented"]}
    record["record_sha256"] = digest(canonical(record)); output.mkdir(mode=0o700); (output / "two-edge-closure-record.json").write_bytes(canonical(record)+b"\n")
    return {"status":"pass","record":str(output / "two-edge-closure-record.json"),"verdict":record["verdict"]}
def main(argv=None):
    parser=argparse.ArgumentParser(); parser.add_argument("--root",default=str(Path(__file__).resolve().parents[1])); parser.add_argument("--output",required=True); parser.add_argument("--json",action="store_true"); args=parser.parse_args(argv)
    try: print(json.dumps(construct(Path(args.root),Path(args.output)),sort_keys=True)); return 0
    except (ClosureError,OSError,KeyError,TypeError) as error: print(json.dumps({"status":"fail","failure_codes":[str(error)]},sort_keys=True)); return 2
if __name__ == "__main__": raise SystemExit(main())
