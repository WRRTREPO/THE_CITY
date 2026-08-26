"""Regression and authority tests for the frozen crew-opportunity proof."""

from __future__ import annotations

import copy
import unittest

from kernel import canonical_json
from deployment_opportunity import (
    DEPLOY_B,
    DEPLOY_C,
    DEPLOY_D,
    DISRUPTION_PROPOSAL_ID,
    FIRE_PROPOSAL_ID,
    PHYSICAL_CONTRACTS,
    apply_physical_proposal,
    deterministic_scheduler_advance,
    initial_record,
    make_deployment_request,
    make_physical_proposal,
    prepare_interaction_record,
    record_hash,
    run_branch,
    run_exclusivity_rejection,
)
from roundtrip import evidence_digest


def entry_for(run: dict, proposal_id: str) -> dict:
    return next(entry for entry in run["ledger"] if entry["proposal_id"] == proposal_id)


def gate_map(entry: dict) -> dict[str, bool]:
    return {gate["name"]: gate["passed"] for gate in entry["gates"]}


class CrewDeploymentOpportunityTests(unittest.TestCase):
    def test_all_branches_share_the_same_r0(self) -> None:
        runs = [run_branch(destination) for destination in (DEPLOY_B, DEPLOY_C, DEPLOY_D)]
        self.assertEqual({record_hash(run["r0"]) for run in runs}, {record_hash(initial_record())})
        self.assertEqual({run["r0"]["seed"] for run in runs}, {"crew-deployment-opportunity-cost-v1/0001"})

    def test_deployment_is_a_canonical_reservation_that_starts_active_world_time(self) -> None:
        run = run_branch(DEPLOY_B)
        record = run["transactions"][0]["ledger"][0]
        final = run["final_record"]
        self.assertEqual(record["result"], "accepted")
        self.assertTrue(all(gate_map(record).values()))
        self.assertTrue(final["world"]["active_world"])
        self.assertEqual(final["resources"]["crew_01_to_04"], "reserved")
        self.assertEqual(final["resources"]["aircraft_01"], "reserved")
        self.assertEqual(final["deployment"]["interaction_domain"], "B")
        self.assertEqual(final["deployment"]["interaction_domain_available_at"], "t0/05")

    def test_second_deployment_rejects_with_all_exclusivity_gates_recorded(self) -> None:
        result = run_exclusivity_rejection()
        entry = result["second_ledger"]
        gates = gate_map(entry)
        self.assertEqual(entry["result"], "rejected")
        self.assertFalse(gates["crew_available"])
        self.assertFalse(gates["aircraft_available"])
        self.assertFalse(gates["crew_has_no_active_deployment"])
        self.assertTrue(gates["destination_is_valid"])
        self.assertEqual(result["record"]["deployment"]["destination"], "B")
        self.assertEqual(entry["resources"], ["no resource acquired"])

    def test_b_branch_contains_fire_through_a_matching_local_proposal(self) -> None:
        run = run_branch(DEPLOY_B)
        final = run["final_record"]
        proposal_entry = entry_for(run, FIRE_PROPOSAL_ID)
        fire_entry = entry_for(run, "fire_bridgehead.spread")
        self.assertEqual(proposal_entry["result"], "accepted")
        self.assertTrue(all(gate_map(proposal_entry).values()))
        self.assertEqual(fire_entry["result"], "failed_gate")
        self.assertTrue(final["areas"]["B"]["fire_containment"])
        self.assertEqual(final["areas"]["B"]["fire_intensity"], 4)
        self.assertTrue(final["routes"]["E_AB"]["open"])
        self.assertEqual(final["agents"]["police_unit_01"]["location"], "C")
        self.assertEqual(final["areas"]["C"]["owner"], "contested")
        self.assertEqual(entry_for(run, "gang_docklands.seize_C.complete")["result"], "failed_gate")

    def test_c_branch_disrupts_seizure_without_erasing_remote_fire_history(self) -> None:
        run = run_branch(DEPLOY_C)
        final = run["final_record"]
        self.assertEqual(entry_for(run, DISRUPTION_PROPOSAL_ID)["result"], "accepted")
        self.assertEqual(entry_for(run, "fire_bridgehead.spread")["result"], "accepted")
        self.assertEqual(entry_for(run, "police_dispatch_C_t0.enter_E_AB")["result"], "failed_gate")
        self.assertTrue(final["areas"]["C"]["crew_disruption"])
        self.assertEqual(final["areas"]["C"]["owner"], "contested")
        self.assertEqual(final["areas"]["B"]["fire_intensity"], 5)
        self.assertFalse(final["routes"]["E_AB"]["open"])
        self.assertEqual(final["agents"]["police_unit_01"]["location"], "A")

    def test_d_branch_keeps_crew_deployed_but_cannot_supply_remote_evidence(self) -> None:
        run = run_branch(DEPLOY_D)
        final = run["final_record"]
        proposal_ids = {entry["proposal_id"] for entry in run["ledger"]}
        self.assertTrue(final["world"]["active_world"])
        self.assertEqual(final["deployment"]["interaction_domain"], "D")
        self.assertNotIn(FIRE_PROPOSAL_ID, proposal_ids)
        self.assertNotIn(DISRUPTION_PROPOSAL_ID, proposal_ids)
        self.assertEqual(final["areas"]["B"]["fire_intensity"], 5)
        self.assertEqual(final["areas"]["C"]["owner"], "gang")
        self.assertEqual((final["areas"]["C"]["gang_control"], final["areas"]["C"]["rival_control"]), (74, 26))

    def test_b_and_c_proposals_are_bound_to_their_exact_interaction_pre_states(self) -> None:
        for domain in (DEPLOY_B, DEPLOY_C):
            pre = prepare_interaction_record(domain)
            proposal = make_physical_proposal(domain, record_hash(pre))
            self.assertEqual(proposal["source"]["source_record_hash"], record_hash(pre))
            self.assertEqual(proposal["target"], PHYSICAL_CONTRACTS[domain]["target"])
            self.assertEqual(proposal["proposed_mutations"], PHYSICAL_CONTRACTS[domain]["mutations"])

    def test_wrong_domain_is_rejected_even_when_digest_is_valid(self) -> None:
        c_pre = prepare_interaction_record(DEPLOY_C)
        b_proposal = make_physical_proposal(DEPLOY_B, record_hash(c_pre))
        _, entry = apply_physical_proposal(c_pre, b_proposal, DEPLOY_B)
        gates = gate_map(entry)
        self.assertEqual(entry["result"], "rejected")
        self.assertTrue(gates["source_record_hash_matches_batch_pre_state"])
        self.assertFalse(gates["deployment.domain_matches_evidence"])

    def test_physical_contract_rejects_recomputed_digest_with_unauthorized_mutation(self) -> None:
        pre = prepare_interaction_record(DEPLOY_B)
        proposal = make_physical_proposal(DEPLOY_B, record_hash(pre))
        proposal["proposed_mutations"].append("E_AB.open = false")
        evidence = proposal["evidence"]
        evidence["evidence_digest"] = evidence_digest(
            source_record_hash=proposal["source"]["source_record_hash"],
            instigator_id=proposal["instigator"]["id"],
            physical_actor_id=evidence["physical_actor_id"],
            state=proposal["observed_outcome"]["state"],
            event_sequence=proposal["observed_outcome"]["event_sequence"],
        )
        run = run_branch(DEPLOY_B, proposal)
        entry = entry_for(run, FIRE_PROPOSAL_ID)
        self.assertTrue(gate_map(entry)["evidence_exact_and_digest_valid"])
        self.assertFalse(gate_map(entry)["allowed_effect_set_exact"])
        self.assertEqual(entry["result"], "rejected")

    def test_scheduler_provenance_parents_every_later_boundary(self) -> None:
        run = run_branch(DEPLOY_B)
        for transaction in run["transactions"][1:]:
            header = transaction["header"]
            pre_hash = header["transaction_pre_state_hash"]
            self.assertEqual(header["boundary_derivation"], "scheduler_clock_advance")
            self.assertEqual(len(pre_hash), 64)
            self.assertEqual(len(header["parent_record_hash"]), 64)
        # The standalone construction law is exact and changes no fact besides clock.
        r0 = initial_record()
        advanced = deterministic_scheduler_advance(r0, "t0/05")
        unchanged_parent = copy.deepcopy(r0)
        unchanged_child = copy.deepcopy(advanced)
        unchanged_parent.pop("clock")
        unchanged_child.pop("clock")
        self.assertEqual(unchanged_parent, unchanged_child)

    def test_each_branch_replays_byte_identically(self) -> None:
        for destination in (DEPLOY_B, DEPLOY_C, DEPLOY_D):
            self.assertEqual(canonical_json(run_branch(destination)), canonical_json(run_branch(destination)))

    def test_final_records_need_no_fixture_branch_field(self) -> None:
        for destination in (DEPLOY_B, DEPLOY_C, DEPLOY_D):
            final = run_branch(destination)["final_record"]
            self.assertNotIn("branch", final)
            self.assertEqual(final["record_schema"], "CrewDeploymentOpportunityRecord.v1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
