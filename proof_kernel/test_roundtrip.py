import copy
import unittest

from roundtrip import (
    ALLOWED_MUTATIONS,
    PARENT_COUNTERFACTUAL_HASH,
    apply_proposal,
    make_proposal,
    record_hash,
    seed_record,
    serializable_record,
    validation_gates,
)


class BridgeAccessRoundTripTests(unittest.TestCase):
    def setUp(self) -> None:
        self.seed = seed_record()
        self.seed_hash = record_hash(self.seed)
        self.proposal = make_proposal(self.seed_hash)

    def test_seed_preserves_the_no_fire_counterfactual(self) -> None:
        self.assertEqual(self.seed["parent_causal_record_hash"], PARENT_COUNTERFACTUAL_HASH)
        self.assertTrue(self.seed["bridge_open"])
        self.assertEqual(self.seed["bridge_capacity"], 1)
        self.assertEqual(self.seed["bridge_access_point_state"], "intact")
        self.assertEqual(self.seed["fire_intensity"], 4)
        self.assertEqual(self.seed["police_location"], "C")
        self.assertEqual(self.seed["docklands_owner"], "contested")
        self.assertEqual(serializable_record(self.seed)["canonical_sha256"], self.seed_hash)

    def test_accepted_proposal_changes_only_the_scoped_facts(self) -> None:
        committed, ledger = apply_proposal(self.seed, self.proposal)
        entry = ledger[-1]
        self.assertEqual(entry["result"], "accepted")
        self.assertTrue(all(entry["gate_results"].values()))
        self.assertEqual(entry["committed_mutations"], ALLOWED_MUTATIONS)
        self.assertFalse(committed["bridge_open"])
        self.assertEqual(committed["bridge_capacity"], 0)
        self.assertEqual(committed["bridge_access_point_state"], "destroyed")
        self.assertEqual(committed["fire_intensity"], 4)
        self.assertEqual(committed["police_location"], "C")
        self.assertEqual(committed["docklands_owner"], "contested")
        self.assertEqual(committed["proposal_terminal_dispositions"][self.proposal["proposal_id"]], "accepted")

    def test_duplicate_is_rejected_with_all_gate_results_and_no_record_mutation(self) -> None:
        committed, accepted_ledger = apply_proposal(self.seed, self.proposal)
        committed_hash = record_hash(committed)
        duplicate, ledger = apply_proposal(committed, self.proposal, accepted_ledger)
        entry = ledger[-1]
        self.assertEqual(record_hash(duplicate), committed_hash)
        self.assertEqual(entry["result"], "rejected")
        self.assertFalse(entry["gate_results"]["source_record_hash_matches_pre_state"])
        self.assertFalse(entry["gate_results"]["proposal_id_unseen"])
        self.assertEqual(entry["committed_mutations"], [])
        self.assertEqual(entry["post_state_hash"], committed_hash)

    def test_all_validation_gates_are_evaluated_without_short_circuiting(self) -> None:
        malformed = copy.deepcopy(self.proposal)
        malformed["source"]["source_record_hash"] = "stale"
        malformed["proposed_mutations"] = []
        gates = validation_gates(self.seed, malformed)
        self.assertEqual(
            list(gates),
            [
                "schema_protocol_compatible",
                "source_record_hash_matches_pre_state",
                "proposal_id_unseen",
                "target_identity_and_route_match",
                "target_current_state_eligible",
                "evidence_matches_observed_outcome",
                "allowed_effect_set_exact",
            ],
        )
        self.assertFalse(gates["source_record_hash_matches_pre_state"])
        self.assertFalse(gates["evidence_matches_observed_outcome"])
        self.assertFalse(gates["allowed_effect_set_exact"])

    def test_same_record_and_proposal_are_byte_equivalent(self) -> None:
        first_record, first_ledger = apply_proposal(self.seed, self.proposal)
        second_record, second_ledger = apply_proposal(self.seed, self.proposal)
        self.assertEqual(record_hash(first_record), record_hash(second_record))
        self.assertEqual(first_ledger, second_ledger)


if __name__ == "__main__":
    unittest.main(verbosity=2)
