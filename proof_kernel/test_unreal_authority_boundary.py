import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
UNREAL_SOURCE = PROJECT_ROOT / "CityMaterializationProof" / "Source" / "CityMaterializationProof"


class UnrealAuthorityBoundaryTests(unittest.TestCase):
    def test_bridge_access_actor_writes_only_a_physical_proposal(self) -> None:
        source = (UNREAL_SOURCE / "BridgeAccessPoint.cpp").read_text(encoding="utf-8")
        self.assertIn("physical_destroy_E_AB_0001.json", source)
        self.assertIn("physical_destroy_E_AB_contention_0001.json", source)
        self.assertIn("contention_proof_runtime_01", source)
        self.assertIn("E_AB.open = false", source)
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
        self.assertIn("BridgeAccessTraversalContentionRecord.v1", source)
        self.assertIn("CrewDeploymentOpportunityRecord.v1", source)
        self.assertIn("CrewArrivalLiveCommitmentRecord.v1", source)
        self.assertIn("SpawnCrewOperationPoint", source)
        self.assertIn("SpawnLiveCommitmentRelayPoint", source)
        self.assertNotIn("SaveStringToFile", source)
        self.assertNotIn("FJsonSerializer::Serialize", source)

    def test_deployment_operation_actor_emits_only_exact_physical_proposals(self) -> None:
        source = (UNREAL_SOURCE / "CrewOperationPoint.cpp").read_text(encoding="utf-8")
        self.assertIn("physical_contain_fire_B_deployment_0001.json", source)
        self.assertIn("physical_disrupt_seizure_C_deployment_0001.json", source)
        self.assertIn("fire_control_valve_B_01", source)
        self.assertIn("gang_signal_relay_C_01", source)
        self.assertIn("B.fire_containment = true", source)
        self.assertIn("C.crew_disruption = true", source)
        self.assertIn("deployment_opportunity_runtime_01", source)
        self.assertIn("SaveStringToFile", source)
        for forbidden_canonical_output in (
            "committed_record.json",
            "causal_ledger.json",
            "proposal_terminal_dispositions",
            "canonical.apply_physical_proposal",
            "crew_deployment_request",
        ):
            self.assertNotIn(forbidden_canonical_output, source)

    def test_live_relay_actor_emits_only_fixture_exact_evidence(self) -> None:
        source = (UNREAL_SOURCE / "LiveCommitmentRelayPoint.cpp").read_text(encoding="utf-8")
        self.assertIn("physical_disable_claim_relay_C_live_0001.json", source)
        self.assertIn("physical_disable_claim_relay_C_live_0002.json", source)
        self.assertIn("gang_claim_relay_C_01", source)
        self.assertIn("C.relay.active = false", source)
        self.assertIn("live_commitment_runtime_01", source)
        self.assertIn("SaveStringToFile", source)
        for forbidden_canonical_output in (
            "committed_record.json",
            "causal_ledger.json",
            "proposal_terminal_dispositions",
            "canonical.apply_physical_relay_proposal",
            "gang_claim_C_001.complete",
            "C.owner = gang",
            "mission_variant",
            "arrival_stage",
        ):
            self.assertNotIn(forbidden_canonical_output, source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
