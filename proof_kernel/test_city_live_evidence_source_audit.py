import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from proof_kernel.city_live_evidence_source_audit import ADVERSARY_SAMPLES, AuditError, audit, canonical, detect_forbidden_adversary, digest
from proof_kernel.verify_city_live_evidence_source_audit import validate


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "proof_kernel" / "city_live_evidence_source_audit_contract.json"


class CityLiveEvidenceSourceAuditTests(unittest.TestCase):
    def test_current_source_emits_only_incomplete_raw_evidence(self):
        result = audit(ROOT, CONTRACT)
        self.assertEqual(result["schema"], "city.source_effect_audit.v1")
        self.assertEqual(result["claim_level"], "raw_evidence_only")
        self.assertEqual(result["scope_status"], "partial")
        self.assertFalse(result["source_audit_complete"])
        self.assertFalse(result["authority"]["may_open_acquisition"])
        self.assertEqual(len(result["adversary_results"]), 14)
        self.assertTrue(all(row["status"] == "rejected" for row in result["adversary_results"]))
        self.assertTrue(all(row["offending_edge"]["classification"] == "denied" for row in result["adversary_results"]))
        self.assertEqual(result["summary"]["historical_partial_graph_unclassified_count"], 145103)
        self.assertGreater(result["summary"]["unclassified_count"], 0)

    def test_source_byte_drift_is_rejected_before_any_candidate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
            for row in contract["primary_sources"]:
                source = ROOT / row["path"]
                target = root / row["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
            changed = root / contract["primary_sources"][0]["path"]
            changed.write_bytes(changed.read_bytes() + b"\n# audit drift\n")
            copied_contract = root / "contract.json"
            copied_contract.write_bytes(CONTRACT.read_bytes())
            with self.assertRaisesRegex(AuditError, "lcer.source_audit_record_changed"):
                audit(root, copied_contract)

    def test_independent_validator_rejects_authority_escalation(self):
        candidate = audit(ROOT, CONTRACT)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = root / "candidate.json"
            raw.write_bytes(canonical(candidate))
            result = validate(raw, CONTRACT)
            self.assertEqual(result["verdict"], "raw_evidence_valid_incomplete")
            candidate["authority"]["may_open_acquisition"] = True
            candidate["result_sha256"] = digest(canonical({key: value for key, value in candidate.items() if key != "result_sha256"}))
            raw.write_bytes(canonical(candidate))
            with self.assertRaisesRegex(ValueError, "lcer.source_audit_record_invalid"):
                validate(raw, CONTRACT)

    def test_every_frozen_adversary_requires_its_exact_mutation_fixture(self):
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(set(contract["forbidden_source_adversaries"]), set(ADVERSARY_SAMPLES))
        for adversary_id, source in ADVERSARY_SAMPLES.items():
            with self.subTest(adversary_id=adversary_id):
                found = detect_forbidden_adversary(adversary_id, source)
                self.assertEqual(found["classification"], "denied")
                with self.assertRaisesRegex(AuditError, "lcer.source_audit_record_invalid"):
                    detect_forbidden_adversary(adversary_id, "def AuditCase(): return None")


if __name__ == "__main__":
    unittest.main()
