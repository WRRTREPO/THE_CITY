import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from proof_kernel.city_harbinger_policy_adapter import canonical, digest


ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "proof_kernel/run_harbinger_city_source_effect_audit.py"
ADAPTER = ROOT / "proof_kernel/city_harbinger_policy_adapter.py"
VERIFY = ROOT / "proof_kernel/verify_city_harbinger_policy_adapter.py"


class CityHarbingerPolicyAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(dir="/private/tmp")
        cls.work = Path(cls.temporary.name)
        cls.bridge_root = cls.work / "fresh-bridge"
        cls.policy_root = cls.work / "policy-record"
        cls.run_cli(BRIDGE, "--root", str(ROOT), "--harbinger-root", str(ROOT.parent / "Harbinger"), "--output", str(cls.bridge_root))
        cls.bridge_record = cls.bridge_root / "city-harbinger-source-effect-record.json"
        cls.raw = json.loads(cls.bridge_record.read_text(encoding="utf-8"))
        cls.adapter_result = cls.run_cli(ADAPTER, "--root", str(ROOT), "--bridge-record", str(cls.bridge_record), "--output", str(cls.policy_root))
        cls.record = cls.policy_root / "city-harbinger-policy-record.json"

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    @staticmethod
    def run_cli(script: Path, *arguments: str, expected: int = 0) -> dict:
        result = subprocess.run([sys.executable, "-B", str(script), *arguments, "--json"], cwd=ROOT, capture_output=True, text=True, check=False)
        if not result.stdout:
            raise AssertionError(f"{script.name}: no JSON output: {result.stderr}")
        value = json.loads(result.stdout)
        if result.returncode != expected:
            raise AssertionError(f"{script.name}: {result.returncode}: {value}")
        return value

    def verify(self, record: Path, *, root: Path = ROOT, expected: int = 0) -> dict:
        return self.run_cli(VERIFY, "--root", str(root), "--record", str(record), "--bridge-record", str(self.bridge_record), expected=expected)

    def copied_record(self) -> Path:
        target = Path(tempfile.mkdtemp(dir=self.work)) / "copy"
        shutil.copytree(self.policy_root, target)
        return target / self.record.name

    @staticmethod
    def rewrite_record(path: Path, mutate) -> None:
        value = json.loads(path.read_text(encoding="utf-8"))
        mutate(value)
        value["record_sha256"] = digest(canonical({key: item for key, item in value.items() if key != "record_sha256"}))
        path.write_bytes(canonical(value) + b"\n")

    def test_fresh_valid_bridge_is_raw_valid_and_incomplete(self):
        self.assertEqual(self.raw["verdict"], "raw_evidence_valid_incomplete")
        self.assertEqual(self.raw["summary"]["edge_count"], 45)
        self.assertEqual(self.adapter_result["mapped_edge_count"], 4)
        self.assertEqual(self.adapter_result["unclassified_edge_count"], 41)
        self.assertEqual(self.verify(self.record)["verdict"], "raw_evidence_valid_incomplete")

    def test_source_byte_change_rejects_before_mapping(self):
        with tempfile.TemporaryDirectory(dir=self.work) as temporary:
            copied_root = Path(temporary)
            contract = json.loads((ROOT / "proof_kernel/city_live_evidence_source_audit_contract.json").read_text(encoding="utf-8"))
            for source in [*contract["primary_sources"], *contract["transitive_local_imports"]["sources"]]:
                target = copied_root / source["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / source["path"], target)
            shutil.copy2(ROOT / "proof_kernel/city_live_evidence_source_audit_contract.json", copied_root / "proof_kernel/city_live_evidence_source_audit_contract.json")
            shutil.copy2(ROOT / "proof_kernel/city_harbinger_policy_contract.json", copied_root / "proof_kernel/city_harbinger_policy_contract.json")
            changed = copied_root / contract["primary_sources"][0]["path"]
            changed.write_bytes(changed.read_bytes() + b"\n# changed\n")
            self.assertEqual(self.verify(self.record, root=copied_root, expected=2)["failure_codes"], ["lcer.harbinger_policy_record_invalid"])

    def test_digest_substitutions_reject(self):
        for field in ("harbinger_graph_sha256", "harbinger_snapshot_sha256", "harbinger_receipt_sha256", "harbinger_core_sha256"):
            with self.subTest(field=field):
                record = self.copied_record()
                self.rewrite_record(record, lambda value, field=field: value.__setitem__(field, "0" * 64))
                self.assertEqual(self.verify(record, expected=2)["status"], "fail")

    def test_allowed_edge_line_move_rejects(self):
        record = self.copied_record()
        self.rewrite_record(record, lambda value: next(row for row in value["edge_decisions"] if row["classification"] == "allowed").__setitem__("source_line", 1))
        self.assertEqual(self.verify(record, expected=2)["status"], "fail")

    def test_unmapped_edge_cannot_be_allowed(self):
        record = self.copied_record()
        self.rewrite_record(record, lambda value: next(row for row in value["edge_decisions"] if row["classification"] == "unclassified").__setitem__("classification", "allowed"))
        self.assertEqual(self.verify(record, expected=2)["status"], "fail")

    def test_live_emit_and_dynamic_resolve_cannot_be_diagnostic(self):
        for token in ("self._emit", "<dynamic>.resolve"):
            with self.subTest(token=token):
                record = self.copied_record()
                def mutate(value, token=token):
                    row = next(row for row in value["edge_decisions"] if row["classification"] == "unclassified")
                    row["harbinger_token"] = token
                    row["classification"] = "allowed"
                    row["city_classification"] = "diagnostic"
                self.rewrite_record(record, mutate)
                self.assertEqual(self.verify(record, expected=2)["status"], "fail")

    def test_authority_escalation_and_missing_edge_reject(self):
        record = self.copied_record()
        self.rewrite_record(record, lambda value: value["authority"].__setitem__("may_open_release", True))
        self.assertEqual(self.verify(record, expected=2)["status"], "fail")
        record = self.copied_record()
        self.rewrite_record(record, lambda value: value["edge_decisions"].pop())
        self.assertEqual(self.verify(record, expected=2)["status"], "fail")


if __name__ == "__main__":
    unittest.main()
