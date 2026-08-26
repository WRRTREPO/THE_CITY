"""Regression tests for the frozen shared-state commitment interference proof."""

from __future__ import annotations

import inspect
import unittest

from kernel import canonical_json
from shared_state_interference import (
    COMMITMENT_X,
    COMMITMENT_Y,
    DEFINITIONS,
    _commit_one,
    counterfactual_run,
    definition_independence_audit,
    definition_hashes,
    initial_record,
    permutation_run,
    primary_run,
    record_hash,
    run_fixture,
)


def entry_for(run: dict, commitment_id: str) -> dict:
    return next(entry for entry in run["ledger"] if entry["commitment_id"] == commitment_id)


def gate_map(entry: dict) -> dict[str, bool]:
    return {gate["name"]: gate["passed"] for gate in entry["gates"]}


class SharedStateCommitmentInterferenceTests(unittest.TestCase):
    def test_definition_audit_proves_no_cross_commitment_reference(self) -> None:
        audit = definition_independence_audit()
        self.assertTrue(audit["passed"])
        self.assertEqual(audit["foreign_references"], [])
        self.assertEqual(audit["undeclared_shared_paths"], [])
        self.assertEqual(DEFINITIONS[COMMITMENT_X]["reads"], ["S.available_units"])
        self.assertEqual(DEFINITIONS[COMMITMENT_Y]["reads"], ["S.available_units"])
        self.assertNotIn(COMMITMENT_Y, canonical_json(DEFINITIONS[COMMITMENT_X]))
        self.assertNotIn(COMMITMENT_X, canonical_json(DEFINITIONS[COMMITMENT_Y]))

    def test_definition_hashes_are_identical_across_every_execution(self) -> None:
        expected = definition_hashes()
        for run in (primary_run(), counterfactual_run(), permutation_run()):
            self.assertEqual(run["r0"]["definition_hashes"], expected)
            self.assertEqual(run["definition_audit"]["definition_hashes"], expected)

    def test_counterfactual_removes_only_x_scheduling_presence(self) -> None:
        primary = primary_run()["r0"]
        counterfactual = counterfactual_run()["r0"]
        self.assertEqual(primary["commitment_definitions"], counterfactual["commitment_definitions"])
        self.assertEqual(primary["definition_hashes"], counterfactual["definition_hashes"])
        self.assertEqual(primary["shared_state"], counterfactual["shared_state"])
        self.assertEqual(primary["commitments"][COMMITMENT_Y], counterfactual["commitments"][COMMITMENT_Y])
        self.assertEqual(primary["scheduled_commitment_ids"], [COMMITMENT_X, COMMITMENT_Y])
        self.assertEqual(counterfactual["scheduled_commitment_ids"], [COMMITMENT_Y])
        self.assertEqual(primary["commitments"][COMMITMENT_X]["state"], "due")
        self.assertEqual(counterfactual["commitments"][COMMITMENT_X]["state"], "not_scheduled")

    def test_primary_x_first_transforms_s_and_y_fails_normal_gate(self) -> None:
        run = primary_run()
        x = entry_for(run, COMMITMENT_X)
        y = entry_for(run, COMMITMENT_Y)
        final = run["final_record"]
        self.assertEqual(x["batch_pre_state_hash"], record_hash(run["r0"]))
        self.assertEqual(y["batch_pre_state_hash"], record_hash(run["r0"]))
        self.assertEqual(x["result"], "accepted")
        self.assertEqual(y["result"], "failed_gate")
        self.assertFalse(gate_map(y)["S.available_units >= 1"])
        self.assertNotEqual(y["working_pre_state_hash"], y["batch_pre_state_hash"])
        self.assertEqual(final["shared_state"]["available_units"], 0)
        self.assertEqual(final["shared_state"]["durable_allocations"], [{"allocation_id": "S.allocation.commitment_X", "committed_by": COMMITMENT_X, "units": 1}])
        self.assertEqual(final["commitments"][COMMITMENT_X]["state"], "succeeded")
        self.assertEqual(final["commitments"][COMMITMENT_Y]["state"], "failed")

    def test_x_absent_counterfactual_leaves_y_definition_and_gate_unchanged(self) -> None:
        primary_y = entry_for(primary_run(), COMMITMENT_Y)
        counterfactual = counterfactual_run()
        y = entry_for(counterfactual, COMMITMENT_Y)
        final = counterfactual["final_record"]
        self.assertEqual(primary_y["action_id"], y["action_id"])
        self.assertEqual(primary_y["definition_hash"], y["definition_hash"])
        self.assertEqual([gate["name"] for gate in primary_y["gates"]], [gate["name"] for gate in y["gates"]])
        self.assertEqual(y["result"], "accepted")
        self.assertTrue(gate_map(y)["S.available_units >= 1"])
        self.assertEqual(final["shared_state"]["durable_allocations"][0]["committed_by"], COMMITMENT_Y)
        self.assertEqual(final["commitments"][COMMITMENT_Y]["state"], "succeeded")
        self.assertEqual(final["commitments"][COMMITMENT_X]["state"], "not_scheduled")

    def test_reversed_fixture_queue_proves_no_hidden_x_priority(self) -> None:
        run = permutation_run()
        y = entry_for(run, COMMITMENT_Y)
        x = entry_for(run, COMMITMENT_X)
        self.assertEqual(run["transactions"][0]["header"]["canonical_queue"], [COMMITMENT_Y, COMMITMENT_X])
        self.assertTrue(run["transactions"][0]["header"]["fixture_queue_is_not_production_precedence"])
        self.assertEqual(y["result"], "accepted")
        self.assertEqual(x["result"], "failed_gate")
        self.assertFalse(gate_map(x)["S.available_units >= 1"])
        self.assertEqual(run["final_record"]["shared_state"]["durable_allocations"][0]["committed_by"], COMMITMENT_Y)

    def test_terminal_resource_dispositions_are_closed_without_leak(self) -> None:
        for run in (primary_run(), counterfactual_run(), permutation_run()):
            final = run["final_record"]
            successful = [cid for cid, item in final["commitments"].items() if item["state"] == "succeeded"]
            failed = [cid for cid, item in final["commitments"].items() if item["state"] == "failed"]
            self.assertEqual(len(final["shared_state"]["durable_allocations"]), len(successful))
            self.assertEqual(final["shared_state"]["available_units"], 1 - len(successful))
            for commitment_id in successful:
                self.assertEqual(final["terminal_resource_dispositions"][commitment_id], "transform one available S unit into durable allocation")
            for commitment_id in failed:
                self.assertEqual(final["terminal_resource_dispositions"][commitment_id], "no resource acquired")

    def test_replay_is_byte_identical_for_every_fixture_input(self) -> None:
        fixtures = (
            {"scheduled_commitment_ids": (COMMITMENT_X, COMMITMENT_Y), "canonical_queue": (COMMITMENT_X, COMMITMENT_Y)},
            {"scheduled_commitment_ids": (COMMITMENT_Y,), "canonical_queue": (COMMITMENT_Y,)},
            {"scheduled_commitment_ids": (COMMITMENT_X, COMMITMENT_Y), "canonical_queue": (COMMITMENT_Y, COMMITMENT_X)},
        )
        for fixture in fixtures:
            self.assertEqual(canonical_json(run_fixture(**fixture)), canonical_json(run_fixture(**fixture)))

    def test_ledger_reconstructs_common_snapshot_and_sequential_revalidation(self) -> None:
        run = primary_run()
        transaction = run["transactions"][0]
        self.assertEqual(transaction["header"]["transaction_pre_state_hash"], record_hash(run["r0"]))
        self.assertEqual(transaction["header"]["parent_record_hash"], record_hash(run["r0"]))
        x, y = transaction["ledger"]
        self.assertEqual(x["working_post_state_hash"], y["working_pre_state_hash"])
        self.assertEqual(x["batch_pre_state_hash"], y["batch_pre_state_hash"])
        self.assertEqual(y["resources"], ["no resource acquired"])

    def test_final_records_carry_no_branch_or_pair_specific_state(self) -> None:
        for run in (primary_run(), counterfactual_run(), permutation_run()):
            final = run["final_record"]
            serialized = canonical_json(final)
            self.assertNotIn("branch", final)
            self.assertNotIn("counterpart", serialized)
            self.assertNotIn("callback", serialized)
            self.assertNotIn("pair_specific", serialized)

    def test_resolver_is_generic_over_scheduled_ids_and_queue(self) -> None:
        source = inspect.getsource(run_fixture) + inspect.getsource(_commit_one)
        self.assertNotIn("primary", source)
        self.assertNotIn("counterfactual", source)
        self.assertNotIn("permutation", source)
        self.assertNotIn(COMMITMENT_X, source)
        self.assertNotIn(COMMITMENT_Y, source)
        self.assertEqual(initial_record()["shared_state"]["available_units"], 1)

if __name__ == "__main__":
    unittest.main(verbosity=2)
