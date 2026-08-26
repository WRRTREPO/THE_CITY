"""Regression tests for the frozen bounded-agent commitment-selection proof."""

from __future__ import annotations

import copy
import inspect
import unittest

from kernel import canonical_json
from bounded_agent_selection import (
    AGENT_ID,
    LOCAL_ACTION,
    REMOTE_ACTION,
    ACTION_DEFINITIONS,
    action_definition_hashes,
    apply_selection_proposal,
    feasibility_counterfactual_run,
    hidden_a_run,
    hidden_b_run,
    initial_record,
    make_selection_proposal,
    primary_run,
    project_perception,
    record_hash,
    run_fixture,
    select_action,
    semantic_selection,
    tie_run,
)


def gate_map(entry: dict) -> dict[str, bool]:
    return {gate["name"]: gate["passed"] for gate in entry["gates"]}


class BoundedAgentCommitmentSelectionTests(unittest.TestCase):
    def test_primary_selects_remote_from_declared_perception_then_canonically_creates_it(self) -> None:
        run = primary_run()
        r0 = run["r0"]
        proposal = run["proposal"]
        entry = run["ledger"][0]
        final = run["final_record"]
        self.assertEqual(proposal["selection"]["selected_action_id"], REMOTE_ACTION)
        self.assertEqual(proposal["selection"]["selected_score"], 5)
        self.assertEqual(r0["commitments"], {})
        self.assertEqual(final["commitments"][f"{AGENT_ID}.{REMOTE_ACTION}.commitment.t0_00"]["state"], "active")
        self.assertEqual(final["agents"][AGENT_ID]["available_transport"], 0)
        self.assertEqual(final["graph"]["A_to_B"]["capacity"], 0)
        self.assertEqual(final["resources"]["transport_unit_01"], f"reserved_by:{AGENT_ID}.{REMOTE_ACTION}.commitment.t0_00")
        self.assertEqual(entry["result"], "accepted")
        self.assertTrue(all(gate_map(entry).values()))

    def test_selection_is_pure_and_does_not_create_city_state(self) -> None:
        r0 = initial_record()
        before = copy.deepcopy(r0)
        proposal = make_selection_proposal(r0)
        self.assertEqual(r0, before)
        self.assertEqual(proposal["proposed_commitment"]["state"], "proposed")
        self.assertEqual(r0["agents"][AGENT_ID]["active_commitment_id"], None)

    def test_route_counterfactual_changes_only_normal_feasibility_then_selects_local(self) -> None:
        primary = primary_run()
        counterfactual = feasibility_counterfactual_run()
        primary_r0 = copy.deepcopy(primary["r0"])
        counter_r0 = copy.deepcopy(counterfactual["r0"])
        primary_r0["graph"]["A_to_B"]["open"] = False
        self.assertEqual(primary_r0, counter_r0)
        selection = counterfactual["proposal"]["selection"]
        remote = next(item for item in selection["candidates"] if item["action_id"] == REMOTE_ACTION)
        self.assertFalse(remote["feasible"])
        self.assertFalse(dict((gate["name"], gate["passed"]) for gate in remote["gates"])["A_to_B.open"])
        self.assertEqual(selection["selected_action_id"], LOCAL_ACTION)
        final = counterfactual["final_record"]
        self.assertIn(f"{AGENT_ID}.{LOCAL_ACTION}.commitment.t0_00", final["commitments"])
        self.assertEqual(final["resources"]["local_work_unit_01"], f"reserved_by:{AGENT_ID}.{LOCAL_ACTION}.commitment.t0_00")

    def test_hidden_fact_is_excluded_from_perception_and_selection_semantics(self) -> None:
        alpha = hidden_a_run()
        beta = hidden_b_run()
        self.assertNotIn("hidden_fact_H", alpha["proposal"]["selection"]["perception"])
        self.assertEqual(semantic_selection(alpha), semantic_selection(beta))
        alpha_final = copy.deepcopy(alpha["final_record"])
        beta_final = copy.deepcopy(beta["final_record"])
        alpha_final.pop("hidden_fact_H")
        beta_final.pop("hidden_fact_H")
        self.assertEqual(alpha_final, beta_final)
        self.assertNotEqual(record_hash(alpha["r0"]), record_hash(beta["r0"]))
        self.assertNotEqual(alpha["proposal"]["source_record_hash"], beta["proposal"]["source_record_hash"])

    def test_equal_score_tie_uses_stable_action_identifier(self) -> None:
        run = tie_run()
        selection = run["proposal"]["selection"]
        scores = {candidate["action_id"]: candidate["score"] for candidate in selection["candidates"]}
        self.assertEqual(scores, {REMOTE_ACTION: 4, LOCAL_ACTION: 4})
        self.assertEqual(selection["selected_action_id"], REMOTE_ACTION)
        self.assertEqual(selection["tie_break"], "stable ascending action_id after descending score")

    def test_perception_projection_has_only_declared_fields(self) -> None:
        perception = project_perception(initial_record())
        self.assertEqual(set(perception), {"agent", "graph", "resources", "local_capacity_available", "opportunity_values", "action_definition_hashes"})
        self.assertEqual(set(perception["graph"]), {"A_to_B"})
        self.assertNotIn("hidden_fact_H", canonical_json(perception))
        source = inspect.getsource(project_perception) + inspect.getsource(select_action)
        self.assertNotIn("hidden_fact_H", source)
        self.assertNotIn("commitments", inspect.getsource(select_action))

    def test_action_definition_identity_is_fixed_and_revalidated(self) -> None:
        r0 = initial_record()
        proposal = make_selection_proposal(r0)
        r0["action_definitions"][REMOTE_ACTION]["risk_cost"] = 0
        result, entry = apply_selection_proposal(r0, proposal)
        gates = gate_map(entry)
        self.assertFalse(gates["action_definitions_exact"])
        self.assertFalse(gates["stored_action_definition_hashes_match_definitions"])
        self.assertTrue(gates["action_definition_hashes_exact"])
        self.assertEqual(entry["result"], "rejected")
        self.assertEqual(result["commitments"], {})
        self.assertEqual(r0["action_definition_hashes"], action_definition_hashes())
        self.assertEqual(ACTION_DEFINITIONS[REMOTE_ACTION]["risk_cost"], 1)

    def test_proposal_revalidation_rejects_redirect_without_reserving_resource(self) -> None:
        r0 = initial_record()
        proposal = make_selection_proposal(r0)
        proposal["proposed_commitment"]["action_id"] = LOCAL_ACTION
        result, entry = apply_selection_proposal(r0, proposal)
        gates = gate_map(entry)
        self.assertFalse(gates["proposed_commitment_exact"])
        self.assertTrue(gates["source_record_hash_matches_batch_pre_state"])
        self.assertEqual(entry["result"], "rejected")
        self.assertEqual(result["commitments"], {})
        self.assertEqual(result["resources"]["transport_unit_01"], "available")
        self.assertEqual(result["resources"]["local_work_unit_01"], "available")
        self.assertEqual(entry["resources"], ["no resource acquired", "no commitment created"])

    def test_ledger_carries_perception_candidates_score_and_canonical_boundary(self) -> None:
        run = primary_run()
        transaction = run["transactions"][0]
        entry = run["ledger"][0]
        self.assertEqual(transaction["header"]["parent_record_hash"], record_hash(run["r0"]))
        self.assertEqual(transaction["header"]["transaction_pre_state_hash"], record_hash(run["r0"]))
        self.assertEqual(entry["observed_inputs"], run["proposal"]["selection"]["perception"])
        self.assertEqual(entry["candidate_actions"], run["proposal"]["selection"]["candidates"])
        self.assertEqual(entry["selected_action_id"], REMOTE_ACTION)
        self.assertEqual(entry["selected_score"], 5)
        self.assertEqual(entry["resources"][-1], "active commitment owns reservations")

    def test_replay_is_byte_identical_for_all_frozen_witness_inputs(self) -> None:
        fixtures = (
            {},
            {"route_open": False},
            {"hidden_fact_H": "H_alpha"},
            {"hidden_fact_H": "H_beta"},
            {"remote_opportunity_value": 7},
        )
        for fixture in fixtures:
            self.assertEqual(canonical_json(run_fixture(**fixture)), canonical_json(run_fixture(**fixture)))

    def test_final_records_carry_no_branch_or_front_selector(self) -> None:
        for run in (primary_run(), feasibility_counterfactual_run(), hidden_a_run(), hidden_b_run(), tie_run()):
            final = run["final_record"]
            serialized = canonical_json(final)
            self.assertNotIn("branch", final)
            self.assertNotIn("front", serialized)
            self.assertNotIn("mission_variant", serialized)
            self.assertNotIn("arrival_stage", serialized)


if __name__ == "__main__":
    unittest.main(verbosity=2)
