import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
UNREAL_SOURCE = PROJECT_ROOT / "CityMaterializationProof" / "Source" / "CityMaterializationProof"


class UnrealAuthorityBoundaryTests(unittest.TestCase):
    def test_bridge_access_actor_writes_only_a_physical_proposal(self) -> None:
        source = (UNREAL_SOURCE / "BridgeAccessPoint.cpp").read_text(encoding="utf-8")
        self.assertIn("physical_destroy_E_AB_0001.json", source)
        self.assertIn("SaveStringToFile", source)
        for forbidden_canonical_output in (
            "committed_record.json",
            "duplicate_record.json",
            "causal_ledger.json",
            "canonical.apply_physical_proposal",
            "proposal_terminal_dispositions",
        ):
            self.assertNotIn(forbidden_canonical_output, source)

    def test_materializer_reads_records_but_never_serializes_one(self) -> None:
        source = (UNREAL_SOURCE / "CityMaterializationActor.cpp").read_text(encoding="utf-8")
        self.assertIn("LoadAuthoritativeRecord", source)
        self.assertNotIn("SaveStringToFile", source)
        self.assertNotIn("FJsonSerializer::Serialize", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
