"""Regression and adversarial tests for the frozen bridge-contention proof."""

from __future__ import annotations

import copy
import unittest

from kernel import canonical_json
from contention import (
    CASE_DESTRUCTION_FIRST,
    CASE_ENTRY_FIRST,
    LEASE_ID,
    PHYSICAL_CONTRACT,
    PHYSICAL_PROPOSAL_ID,
    POLICE_COMMITMENT_ID,
    deterministic_scheduler_advance,
    initial_record,
    make_physical_proposal,
    record_hash,
    run_case,
)
from roundtrip import evidence_digest


def physical_entry(result: dict) -> dict:
    return next(entry for entry in result["ledger"] if entry["proposal_id"] == PHYSICAL_PROPOSAL_ID)


def police_entry(result: dict) -> dict:
    return next(entry for entry in result["ledger"] if entry["proposal_id"].endswith("enter_E_AB"))


def gate_map(entry: dict) -> dict[str, bool]:
    return {gate["name"]: gate["passed"] for gate in entry["gates"]}


def refresh_digest(proposal: dict) -> None:
    source = proposal["source"]
    instigator = proposal["instigator"]
    evidence = proposal["evidence"]
    observed = proposal["observed_outcome"]
    evidence["evidence_digest"] = evidence_digest(
        source_record_hash=source["source_record_hash"],
        instigator_id=instigator["id"],
        physical_actor_id=evidence["physical_actor_id"],
        state=observed["state"],
        event_sequence=observed["event_sequence"],
    )


class BridgeContentionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.r0_hash = record_hash(initial_record())

    def test_case_1_destruction_prevents_new_entry(self) -> None:
        result = run_case(CASE_DESTRUCTION_FIRST)
        final = result["final_record"]
        route = final["routes"]["E_AB"]
        police = final["agents"]["police_unit_01"]
        self.assertEqual(route, {"open": False, "capacity": 0, "bridge_access_point_state": "destroyed", "leases": []})
        self.assertEqual(police["location"], "A")
        self.assertEqual(police["availability"], "available")
        self.assertEqual(police["dispatch_to_C"], {"result": "failed_gate", "failed_gate": "E_AB.open"})
        self.assertNotIn(POLICE_COMMITMENT_ID, final["commitments"])
        failed_entry = police_entry(result)
        self.assertEqual(failed_entry["result"], "failed_gate")
        self.assertEqual(failed_entry["resources"], ["no resource acquired"])

    def test_case_2_closed_route_honours_existing_lease_before_exit(self) -> None:
        result = run_case(CASE_ENTRY_FIRST)
        intermediate = result["intermediate_record"]
        route = intermediate["routes"]["E_AB"]
        police = intermediate["agents"]["police_unit_01"]
        commitment = intermediate["commitments"][POLICE_COMMITMENT_ID]
        self.assertFalse(route["open"])
        self.assertEqual(route["capacity"], 0)
        self.assertEqual(route["leases"], [LEASE_ID])
        self.assertEqual(police["location"], "A")
        self.assertEqual(police["availability"], "reserved")
        self.assertEqual(commitment["current_segment"], "E_AB")
        self.assertEqual(commitment["last_valid_location"], "A")

    def test_case_2_exit_is_a_new_t1_transaction_and_releases_lease(self) -> None:
        result = run_case(CASE_ENTRY_FIRST)
        exit_transaction = result["exit_transaction"]
        exit_entry = result["ledger"][-1]
        final = result["final_record"]
        self.assertEqual(exit_entry["decision_time"], "t1/15")
        self.assertEqual(exit_entry["batch_pre_state_hash"], exit_transaction["batch_pre_state_hash"])
        self.assertEqual(exit_transaction["batch_header"]["decision_boundary"], "t1/15")
        self.assertEqual(exit_transaction["batch_header"]["parent_record_hash"], record_hash(result["intermediate_record"]))
        self.assertEqual(exit_transaction["batch_header"]["boundary_derivation"], "scheduler_clock_advance")
        self.assertEqual(exit_transaction["batch_header"]["transaction_pre_state_hash"], exit_transaction["batch_pre_state_hash"])
        self.assertNotEqual(exit_entry["batch_pre_state_hash"], result["batch_pre_state_hash"])
        self.assertEqual(exit_entry["working_pre_state_hash"], exit_transaction["batch_pre_state_hash"])
        self.assertIsNone(exit_entry["source_record_hash"])
        self.assertEqual(final["agents"]["police_unit_01"]["location"], "B")
        self.assertEqual(final["routes"]["E_AB"]["leases"], [])
        self.assertIsNone(final["commitments"][POLICE_COMMITMENT_ID]["current_segment"])
        self.assertEqual(final["commitments"][POLICE_COMMITMENT_ID]["last_valid_location"], "B")

    def test_t1_pre_state_is_explicit_scheduler_derivation_of_the_t0_parent(self) -> None:
        result = run_case(CASE_ENTRY_FIRST)
        exit_transaction = result["exit_transaction"]
        parent = result["intermediate_record"]
        expected = deterministic_scheduler_advance(parent, "t1/15")
        self.assertEqual(exit_transaction["parent_record_hash"], record_hash(parent))
        self.assertEqual(exit_transaction["exit_pre_record"], expected)
        self.assertEqual(record_hash(expected), exit_transaction["batch_pre_state_hash"])
        parent_without_clock = copy.deepcopy(parent)
        exit_without_clock = copy.deepcopy(exit_transaction["exit_pre_record"])
        parent_without_clock.pop("clock")
        exit_without_clock.pop("clock")
        self.assertEqual(parent_without_clock, exit_without_clock)

    def test_t1_transaction_replays_from_the_same_parent_and_boundary_byte_identically(self) -> None:
        first_parent = run_case(CASE_ENTRY_FIRST)["intermediate_record"]
        second_parent = run_case(CASE_ENTRY_FIRST)["intermediate_record"]
        from contention import resolve_t1_exit

        self.assertEqual(canonical_json(resolve_t1_exit(first_parent)), canonical_json(resolve_t1_exit(second_parent)))

    def test_case_2_physical_source_is_bound_to_batch_not_working_pre_state(self) -> None:
        result = run_case(CASE_ENTRY_FIRST)
        entry = physical_entry(result)
        self.assertEqual(entry["source_record_hash"], result["batch_pre_state_hash"])
        self.assertNotEqual(entry["source_record_hash"], entry["working_pre_state_hash"])
        self.assertEqual(entry["result"], "accepted")
        self.assertTrue(gate_map(entry)["source_record_hash_matches_batch_pre_state"])

    def test_ebc_is_untouched_until_its_later_entry_boundary(self) -> None:
        result = run_case(CASE_ENTRY_FIRST)
        final = result["final_record"]
        self.assertEqual(final["routes"]["E_BC"], {"open": True, "capacity": 2, "leases": []})
        self.assertEqual(final["commitments"][POLICE_COMMITMENT_ID]["next_gate"], "E_BC at t1/20")

    def test_replay_is_byte_identical_for_each_fixture_ordering(self) -> None:
        for case in (CASE_DESTRUCTION_FIRST, CASE_ENTRY_FIRST):
            self.assertEqual(canonical_json(run_case(case)), canonical_json(run_case(case)))

    def test_ledger_records_scoped_gates_and_explains_execution_order(self) -> None:
        result = run_case(CASE_ENTRY_FIRST)
        physical = physical_entry(result)
        police = police_entry(result)
        self.assertEqual(result["queue"], [
            "t0/20/E_AB/police_unit_01.enter_E_AB",
            "t0/25/E_AB/crew_01_to_04.destroy_E_AB",
        ])
        self.assertEqual(police["canonical_execution_key"], result["queue"][0])
        self.assertEqual(physical["canonical_execution_key"], result["queue"][1])
        self.assertEqual(result["t0_batch"]["header"]["decision_boundary"], "t0")
        self.assertEqual(result["t0_batch"]["header"]["transaction_pre_state_hash"], result["batch_pre_state_hash"])
        self.assertEqual(result["t0_batch"]["header"]["proposal_ids"], [PHYSICAL_PROPOSAL_ID, "police_dispatch_C_t0.enter_E_AB"])
        self.assertEqual({gate["scope"] for gate in physical["gates"]}, {"batch_binding", "working_revalidation"})
        self.assertEqual({gate["scope"] for gate in police["gates"]}, {"batch_binding", "working_revalidation"})
        self.assertTrue(all({"value", "result", "passed"}.issubset(gate) for gate in physical["gates"]))
        self.assertEqual(physical["observed_inputs"]["crew"], {"kind": "crew", "id": "crew_01_to_04"})
        self.assertTrue(physical["observed_inputs"]["evidence_digest"].startswith("md5:"))

    def test_adversarial_authority_contracts_reject_without_mutating_bridge(self) -> None:
        mutations = {
            "wrong_target_route": lambda p: p["target"].update({"route": "E_BC"}),
            "wrong_target_id": lambda p: p["target"].update({"id": "bridge_access_point_E_AB_99"}),
            "wrong_actor_id": lambda p: p["evidence"].update({"physical_actor_id": "bridge_access_point_E_AB_99"}),
            "wrong_outcome": lambda p: p["observed_outcome"].update({"state": "damaged"}),
            "missing_required_mutation": lambda p: p.update({"proposed_mutations": p["proposed_mutations"][:-1]}),
            "extra_mutation": lambda p: p.update({"proposed_mutations": p["proposed_mutations"] + ["E_BC.open = false"]}),
            "reordered_mutation": lambda p: p.update({"proposed_mutations": list(reversed(p["proposed_mutations"]))}),
            "extra_authority_field": lambda p: p.update({"authority_override": "E_BC"}),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                proposal = make_physical_proposal(self.r0_hash)
                mutate(proposal)
                refresh_digest(proposal)
                result = run_case(CASE_DESTRUCTION_FIRST, proposal)
                entry = physical_entry(result)
                self.assertEqual(entry["result"], "rejected")
                self.assertFalse(all(gate_map(entry).values()))
                self.assertTrue(result["final_record"]["routes"]["E_AB"]["open"])
                self.assertEqual(result["final_record"]["routes"]["E_AB"]["bridge_access_point_state"], "intact")

    def test_digest_integrity_does_not_authorize_redirected_target(self) -> None:
        proposal = make_physical_proposal(self.r0_hash)
        proposal["target"] = {"kind": "bridge_access_point", "id": "bridge_access_point_E_AB_01", "route": "E_BC"}
        refresh_digest(proposal)
        result = run_case(CASE_DESTRUCTION_FIRST, proposal)
        entry = physical_entry(result)
        gates = gate_map(entry)
        self.assertTrue(gates["evidence_matches_observed_outcome"])
        self.assertFalse(gates["target_identity_and_route_match"])
        self.assertEqual(entry["result"], "rejected")

    def test_authorization_rejection_evaluates_all_nonmutating_gates(self) -> None:
        proposal = make_physical_proposal(self.r0_hash)
        proposal["target"]["route"] = "E_BC"
        proposal["proposed_mutations"].append("E_BC.open = false")
        refresh_digest(proposal)
        entry = physical_entry(run_case(CASE_DESTRUCTION_FIRST, proposal))
        gates = gate_map(entry)
        self.assertFalse(gates["target_identity_and_route_match"])
        self.assertFalse(gates["allowed_effect_set_exact"])
        self.assertTrue(gates["E_AB.bridge_access_intact"])
        self.assertTrue(gates["E_AB.open"])

    def test_exact_frozen_physical_contract_is_accepted(self) -> None:
        proposal = make_physical_proposal(self.r0_hash)
        self.assertEqual(proposal["proposal_id"], PHYSICAL_CONTRACT.proposal_id)
        self.assertEqual(proposal["proposed_mutations"], PHYSICAL_CONTRACT.allowed_mutations)
        self.assertEqual(physical_entry(run_case(CASE_DESTRUCTION_FIRST, proposal))["result"], "accepted")


if __name__ == "__main__":
    unittest.main(verbosity=2)
