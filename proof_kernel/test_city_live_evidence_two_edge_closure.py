import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from proof_kernel.city_live_evidence_two_edge_closure import construct, environment

ROOT = Path(__file__).resolve().parents[1]
VERIFY = ROOT / "proof_kernel/verify_city_live_evidence_two_edge_closure.py"


class TwoEdgeClosureTests(unittest.TestCase):
    def test_constructs_raw_incomplete_record_and_independently_verifies(self):
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            output = Path(temporary) / "closure"
            result = construct(ROOT, output)
            self.assertEqual(result["status"], "pass")
            record = Path(result["record"])
            checked = subprocess.run([sys.executable, "-B", str(VERIFY), "--root", str(ROOT), "--record", str(record), "--json"], cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
            self.assertEqual(json.loads(checked.stdout)["verdict"], "raw_evidence_valid_incomplete")

    def test_parent_environment_cannot_change_sealed_mapping(self):
        first = environment(["PATH", "LANG", "LC_ALL"], Path("/private/tmp/case"))
        self.assertEqual(first, environment(["PATH", "LANG", "LC_ALL"], Path("/private/tmp/case")))

    def test_undeclared_environment_and_tampered_record_fail(self):
        with self.assertRaisesRegex(ValueError, "lcer.build_environment_unsealed"):
            environment(["PATH", "UNDECLARED"], Path("/private/tmp/case"))
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            output = Path(temporary) / "closure"; record = Path(construct(ROOT, output)["record"])
            value = json.loads(record.read_text()); value["authority"]["may_open_release"] = True
            record.write_text(json.dumps(value), encoding="utf-8")
            checked = subprocess.run([sys.executable, "-B", str(VERIFY), "--root", str(ROOT), "--record", str(record), "--json"], cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(checked.returncode, 2)


if __name__ == "__main__":
    unittest.main()
