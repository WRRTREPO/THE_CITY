"""Regression and authority tests for the frozen live-commitment proof."""

from __future__ import annotations

import copy
import unittest

from kernel import canonical_json
from live_commitment import (
    BRANCH_CONTROL,
    BRANCH_EARLY,
    BRANCH_LATE,
    CLAIM_ID,
    EARLY_PROPOSAL_ID,
    LATE_PROPOSAL_ID,
    PHYSICAL_CONTRACTS,
    apply_physical_proposal,
    deterministic_scheduler_advance,
    initial_record,
    make_physical_proposal,
    physical_access,
    prepare_arrival_record,
    prepare_post_claim_record,
    record_hash,
    run_branch,
)
from roundtrip import evidence_digest


def entry_for(run: dict, proposal_id: str) -> dict:
    return next(entry for entry in run["ledger"] if entry["proposal_id"] == proposal_id)


def gate_map(entry: dict) -> dict[str, bool]:
    return {gate["name"]: gate["passed"] for gate in entry["gates"]}


class CrewArrivalLiveCommitmentTests(unittest.TestCase):
    def test_all_branches_begin_from_one_byte_identical_r0(self) -> None:
        runs = [run_branch(branch) for branch in (BRANCH_CONTROL, BRANCH_EARLY, BRANCH_LATE)]
        self.assertEqual({record_hash(run["r0"]) for run in runs}, {record_hash(initial_record())})
        self.assertEqual({run["r0"]["seed"] for run in runs}, {"crew-arrival-live-commitment-v1/0001"})

    def test_canonical_prehistory_creates_durable_facts_and_one_active_claim(self) -> None:
        arrival = prepare_arrival_record()
        area = arrival["areas"]["C"]
        claim = arrival["commitments"][CLAIM_ID]
        self.assertEqual(arrival["completed_history"], ["survey_C", "marshal_C", "secure_ingress_C", "establish_perimeter_C", "activate_relay_C"])
        self.assertTrue(area["gang_intelligence"])
        self.assertEqual(area["gang_personnel_present"], 6)
        self.assertTrue(area["ingress_secured"])
        self.assertTrue(area["perimeter_established"])
        self.assertTrue(area["relay"]["active"])
        self.assertEqual(claim["state"], "active")
        self.assertEqual(claim["resolution_time"], "t0/40")
        self.assertEqual((claim["reserved_personnel"], claim["reserved_supply"]), (6, 1))

    def test_arrival_is_clock_only_and_physical_access_is_derived(self) -> None:
        arrival = prepare_arrival_record()
        before = copy.deepcopy(arrival)
        before["clock"] = "t0/21"
        self.assertTrue(physical_access(arrival))
        self.assertFalse(physical_access(before))
        unchanged_before = copy.deepcopy(before)
        unchanged_arrival = copy.deepcopy(arrival)
        unchanged_before.pop("clock")
        unchanged_arrival.pop("clock")
        self.assertEqual(unchanged_before, unchanged_arrival)
        self.assertEqual(arrival["deployment"]["destination"], "C")
        self.assertEqual(arrival["deployment"]["physical_access_at"], "t0/27")

    def test_control_emits_no_physical_proposal_and_claim_resolves_canonically(self) -> None:
        run = run_branch(BRANCH_CONTROL)
        final = run["final_record"]
        proposal_ids = {entry["proposal_id"] for entry in run["ledger"]}
        self.assertNotIn(EARLY_PROPOSAL_ID, proposal_ids)
        self.assertNotIn(LATE_PROPOSAL_ID, proposal_ids)
        claim = entry_for(run, CLAIM_ID + ".complete")
        self.assertEqual(claim["result"], "accepted")
        self.assertTrue(all(gate_map(claim).values()))
        self.assertEqual(final["areas"]["C"]["owner"], "gang")
        self.assertEqual((final["areas"]["C"]["gang_control"], final["areas"]["C"]["rival_control"]), (72, 28))
        self.assertEqual(final["commitments"][CLAIM_ID]["state"], "succeeded")

    def test_early_unreal_evidence_is_bound_to_rarrival_and_prevents_future_claim(self) -> None:
        arrival = prepare_arrival_record()
        proposal = make_physical_proposal("active", record_hash(arrival))
        run = run_branch(BRANCH_EARLY, proposal)
        physical = entry_for(run, EARLY_PROPOSAL_ID)
        claim = entry_for(run, CLAIM_ID + ".complete")
        final = run["final_record"]
        self.assertEqual(physical["source_record_hash"], record_hash(arrival))
        self.assertEqual(physical["batch_pre_state_hash"], record_hash(arrival))
        self.assertEqual(physical["result"], "accepted")
        self.assertTrue(all(gate_map(physical).values()))
        self.assertEqual(claim["result"], "failed_gate")
        self.assertFalse(gate_map(claim)["C.relay.active"])
        self.assertEqual(final["areas"]["C"]["owner"], "contested")
        self.assertFalse(final["areas"]["C"]["relay"]["active"])

    def test_failed_claim_releases_every_reservation(self) -> None:
        final = run_branch(BRANCH_EARLY)["final_record"]
        claim = final["commitments"][CLAIM_ID]
        self.assertEqual(claim["state"], "failed")
        self.assertEqual(final["resources"]["gang_personnel_available"], 6)
        self.assertEqual(final["resources"]["gang_claim_supply_available"], 1)
        self.assertEqual(final["areas"]["C"]["gang_personnel_present"], 0)
        self.assertEqual(claim["terminal_resource_disposition"]["personnel"], "release 6 reserved personnel to gang_personnel_available")

    def test_late_evidence_is_emitted_from_a_fresh_settled_record_without_reopening_history(self) -> None:
        post_claim = prepare_post_claim_record()
        proposal = make_physical_proposal("succeeded", record_hash(post_claim))
        run = run_branch(BRANCH_LATE, proposal)
        physical = entry_for(run, LATE_PROPOSAL_ID)
        final = run["final_record"]
        self.assertEqual(post_claim["commitments"][CLAIM_ID]["state"], "succeeded")
        self.assertEqual(post_claim["areas"]["C"]["owner"], "gang")
        self.assertEqual(physical["source_record_hash"], record_hash(post_claim))
        self.assertEqual(physical["result"], "accepted")
        self.assertTrue(all(gate_map(physical).values()))
        self.assertFalse(final["areas"]["C"]["relay"]["active"])
        self.assertEqual(final["areas"]["C"]["owner"], "gang")
        self.assertEqual((final["areas"]["C"]["gang_control"], final["areas"]["C"]["rival_control"]), (72, 28))
        self.assertEqual(final["commitments"][CLAIM_ID]["state"], "succeeded")

    def test_pre_and_post_evidence_use_the_same_validator_and_differ_by_authoritative_state(self) -> None:
        arrival = prepare_arrival_record()
        post_claim = prepare_post_claim_record()
        _, early_entry, _ = apply_physical_proposal(arrival, make_physical_proposal("active", record_hash(arrival)))
        _, late_entry, _ = apply_physical_proposal(post_claim, make_physical_proposal("succeeded", record_hash(post_claim)))
        self.assertEqual(early_entry["canonical_execution_key"].split("/")[-1], late_entry["canonical_execution_key"].split("/")[-1])
        self.assertEqual([gate["name"] for gate in early_entry["gates"]], [gate["name"] for gate in late_entry["gates"]])
        self.assertNotEqual(early_entry["observed_inputs"]["claim_state"], late_entry["observed_inputs"]["claim_state"])

    def test_physical_evidence_before_access_rejects_without_city_mutation(self) -> None:
        arrival = prepare_arrival_record()
        before = copy.deepcopy(arrival)
        before["clock"] = "t0/21"
        proposal = make_physical_proposal("active", record_hash(before))
        result, entry, _ = apply_physical_proposal(before, proposal)
        self.assertEqual(entry["result"], "rejected")
        self.assertFalse(gate_map(entry)["physical_access_C"])
        self.assertEqual(result, before)

    def test_stale_source_and_duplicate_are_rejected_with_all_gates_recorded(self) -> None:
        arrival = prepare_arrival_record()
        proposal = make_physical_proposal("active", record_hash(arrival))
        accepted, _, _ = apply_physical_proposal(arrival, proposal)
        duplicate, duplicate_entry, _ = apply_physical_proposal(accepted, proposal)
        gates = gate_map(duplicate_entry)
        self.assertEqual(duplicate_entry["result"], "rejected")
        self.assertFalse(gates["source_record_hash_matches_batch_pre_state"])
        self.assertFalse(gates["proposal_id_unseen"])
        self.assertEqual(duplicate, accepted)

    def test_recomputed_digest_does_not_authorize_wrong_target_or_mutation(self) -> None:
        arrival = prepare_arrival_record()
        proposal = make_physical_proposal("active", record_hash(arrival))
        proposal["target"]["id"] = "wrong_relay"
        proposal["proposed_mutations"].append("C.owner = gang")
        evidence = proposal["evidence"]
        evidence["evidence_digest"] = evidence_digest(
            source_record_hash=proposal["source"]["source_record_hash"],
            instigator_id=proposal["instigator"]["id"],
            physical_actor_id=evidence["physical_actor_id"],
            state=proposal["observed_outcome"]["state"],
            event_sequence=proposal["observed_outcome"]["event_sequence"],
        )
        result, entry, _ = apply_physical_proposal(arrival, proposal)
        gates = gate_map(entry)
        self.assertTrue(gates["evidence_exact_and_digest_valid"])
        self.assertFalse(gates["target_exact"])
        self.assertFalse(gates["allowed_effect_set_exact"])
        self.assertEqual(entry["result"], "rejected")
        self.assertEqual(result, arrival)

    def test_scheduler_ancestry_is_continuous_and_clock_only(self) -> None:
        run = run_branch(BRANCH_EARLY)
        for prior, later in zip(run["transactions"], run["transactions"][1:]):
            header = later["header"]
            if header["boundary_derivation"] == "scheduler_clock_advance":
                self.assertEqual(header["parent_record_hash"], prior["ledger"][0]["working_post_state_hash"])
        parent = initial_record()
        child = deterministic_scheduler_advance(parent, "t0/04")
        unclocked_parent = copy.deepcopy(parent)
        unclocked_child = copy.deepcopy(child)
        unclocked_parent.pop("clock")
        unclocked_child.pop("clock")
        self.assertEqual(unclocked_parent, unclocked_child)

    def test_runs_replay_byte_identically(self) -> None:
        for branch in (BRANCH_CONTROL, BRANCH_EARLY, BRANCH_LATE):
            self.assertEqual(canonical_json(run_branch(branch)), canonical_json(run_branch(branch)))

    def test_final_city_records_carry_no_branch_or_mission_variant(self) -> None:
        for branch in (BRANCH_CONTROL, BRANCH_EARLY, BRANCH_LATE):
            final = run_branch(branch)["final_record"]
            serialized = canonical_json(final)
            self.assertNotIn("branch", final)
            self.assertNotIn("mission_variant", serialized)
            self.assertNotIn("arrival_stage", serialized)

    def test_contracts_are_fixture_local_and_exact(self) -> None:
        self.assertEqual(PHYSICAL_CONTRACTS["active"]["proposal_id"], EARLY_PROPOSAL_ID)
        self.assertEqual(PHYSICAL_CONTRACTS["succeeded"]["proposal_id"], LATE_PROPOSAL_ID)
        self.assertEqual(PHYSICAL_CONTRACTS["active"]["mutations"], ["C.relay.active = false"])
        self.assertEqual(PHYSICAL_CONTRACTS["succeeded"]["mutations"], ["C.relay.active = false"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
