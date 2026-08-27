"""Regression tests for the frozen record-relative chronological-resolution proof."""

from __future__ import annotations

import copy
import unittest

from kernel import canonical_json
from record_relative_chronological_resolution import (
    COMMITMENT_X,
    COMMITMENT_Y,
    COMMITMENT_Z,
    NO_BOUNDARY,
    PAYLOAD_SCHEMA,
    REJECT_BOUNDARY_CROSSING,
    REJECT_BOUNDARY_SOURCE,
    REJECT_DEMOTION_LOSS,
    REJECT_GATE_CACHE,
    REJECT_LOCAL_AUTHORITY,
    REJECT_PROMOTION_AUTHORITY,
    REJECT_SAME_CLOCK_SUCCESSOR,
    REJECT_STALE_BOUNDARY,
    CanonicalEnvelopeRejected,
    all_witness_runs,
    authoritative_projection,
    boundary_jump,
    canonical_hash,
    definition_independence_audit,
    demote,
    dense_inspection,
    dense_demote_boundary_jump_promote_dense_run,
    dense_throughout_run,
    equivalence_oracle,
    initial_canonical_envelope,
    minimal_runtime,
    next_consequential_boundary,
    promote,
    resolve_next_due,
    runtime_fail_closed_results,
    source_audit,
    validate_canonical_envelope,
)


class RecordRelativeChronologicalResolutionTests(unittest.TestCase):
    def _chain(self) -> tuple[dict, dict, dict, dict]:
        r0 = initial_canonical_envelope()
        r1 = resolve_next_due(r0, next_consequential_boundary(r0))
        r2 = resolve_next_due(r1, next_consequential_boundary(r1))
        r3 = resolve_next_due(r2, next_consequential_boundary(r2))
        return r0, r1, r2, r3

    def test_exact_new_payload_identity_and_r0_schema(self) -> None:
        r0 = initial_canonical_envelope()
        self.assertEqual(r0["identity"]["payload_schema"], PAYLOAD_SCHEMA)
        self.assertEqual(r0["identity"]["simulation_version"], "0.7.0-draft.39")
        self.assertEqual(validate_canonical_envelope(r0), [])
        invalid = copy.deepcopy(r0)
        invalid["current_causal_state"]["durable_facts"]["unfrozen"] = True
        self.assertNotEqual(validate_canonical_envelope(invalid), [])

    def test_every_discovered_boundary_is_bound_to_its_exact_source_record(self) -> None:
        r0, r1, r2, r3 = self._chain()
        expected = (
            (r0, "t1/00", "t1/00/chronological/commitment_x.resolve"),
            (r1, "t1/30", "t1/30/chronological/commitment_y.resolve"),
            (r2, "t2/00", "t2/00/chronological/commitment_z.resolve"),
        )
        for record, decision_time, work_id in expected:
            boundary = next_consequential_boundary(record)
            self.assertEqual(boundary["source_record_hash"], canonical_hash(record))
            self.assertEqual(boundary["decision_time"], decision_time)
            self.assertEqual(boundary["due_work_ids"], [work_id])
        self.assertEqual(next_consequential_boundary(r3), NO_BOUNDARY)

    def test_successor_ancestry_is_singular_and_matches_the_boundary_witness(self) -> None:
        r0, r1, r2, r3 = self._chain()
        for parent, successor in ((r0, r1), (r1, r2), (r2, r3)):
            entry = successor["causal_provenance"]["authoritative_causal_ledger"][-1]
            self.assertEqual(
                successor["causal_provenance"]["canonical_ancestry"],
                {
                    "parent_record_hash": canonical_hash(parent),
                    "boundary_derivation": "next_consequential_boundary",
                },
            )
            self.assertEqual(entry["source_record_hash"], canonical_hash(parent))
            self.assertNotIn("transaction_parent_record_hash", entry)
            self.assertNotIn("transaction_pre_state_hash", entry)

    def test_x_mutates_shared_state_then_y_revalidates_r1_and_fails(self) -> None:
        r0, r1, r2, _ = self._chain()
        self.assertEqual(r1["current_causal_state"]["durable_facts"]["outcome_x"], "succeeded")
        self.assertEqual(r1["current_causal_state"]["gate_relevant_state"]["shared_slot_state"], "allocated_to_x")
        y = r2["causal_provenance"]["authoritative_causal_ledger"][-1]
        self.assertEqual(y["commitment_id"], COMMITMENT_Y)
        self.assertEqual(y["source_record_hash"], canonical_hash(r1))
        self.assertEqual(
            y["evaluated_gates"],
            [
                {
                    "path": "current_causal_state.gate_relevant_state.shared_slot_state",
                    "observed_value": "allocated_to_x",
                    "required_value": "available",
                    "result": False,
                }
            ],
        )
        self.assertEqual(y["mutation_or_failed_gate"], "failed_gate")
        self.assertEqual(r2["current_causal_state"]["active_and_terminal_commitments"][COMMITMENT_Y]["state"], "failed_gate")
        self.assertEqual(r2["causal_provenance"]["terminal_resource_dispositions"][COMMITMENT_Y], "no_resource_acquired_on_failed_gate")
        self.assertNotEqual(canonical_hash(r0), canonical_hash(r1))

    def test_y_failure_commits_r2_and_z_remains_discoverable_then_succeeds(self) -> None:
        _, r1, r2, r3 = self._chain()
        z_boundary = next_consequential_boundary(r2)
        self.assertEqual(z_boundary["due_work_ids"], ["t2/00/chronological/commitment_z.resolve"])
        self.assertEqual(z_boundary["source_record_hash"], canonical_hash(r2))
        self.assertEqual(r3["current_causal_state"]["active_and_terminal_commitments"][COMMITMENT_Z]["state"], "succeeded")
        self.assertEqual(r3["current_causal_state"]["durable_facts"]["outcome_z"], "succeeded")
        self.assertEqual(
            r3["current_causal_state"]["reservations_leases_and_resource_ownership"]["unit_z"],
            {"state": "available", "reservation_id": None, "owner_commitment_id": None},
        )
        self.assertEqual(r3["causal_provenance"]["terminal_resource_dispositions"]["reservation_z"], "release_unit_z_on_success")
        self.assertEqual(next_consequential_boundary(r3), NO_BOUNDARY)
        self.assertNotEqual(canonical_hash(r1), canonical_hash(r2))

    def test_stale_and_crossing_boundaries_fail_without_mutating_r1(self) -> None:
        r0 = initial_canonical_envelope()
        b0 = next_consequential_boundary(r0)
        r1 = resolve_next_due(r0, b0)
        before = copy.deepcopy(r1)
        with self.assertRaisesRegex(CanonicalEnvelopeRejected, REJECT_BOUNDARY_SOURCE):
            resolve_next_due(r1, b0)
        self.assertEqual(r1, before)

        crossing = {
            "source_record_hash": canonical_hash(r1),
            "decision_time": "t2/00",
            "due_work_ids": ["t2/00/chronological/commitment_z.resolve"],
        }
        with self.assertRaisesRegex(CanonicalEnvelopeRejected, REJECT_BOUNDARY_CROSSING):
            resolve_next_due(r1, crossing)
        self.assertEqual(r1, before)

    def test_same_clock_successor_is_rejected_by_this_exact_payload(self) -> None:
        r0, r1, _, _ = self._chain()
        candidate = copy.deepcopy(r1)
        candidate["future_causal_state"]["scheduled_consequential_decisions"].append(
            {"decision_time": "t1/00", "due_work_ids": ["t1/00/chronological/same_clock.resolve"]}
        )
        self.assertNotEqual(validate_canonical_envelope(candidate), [])
        self.assertEqual(r0["future_causal_state"]["canonical_clock"], "t0/00")

    def test_dense_boundary_jump_promotion_and_demotion_are_resolution_local(self) -> None:
        r0 = initial_canonical_envelope()
        dense = dense_inspection(minimal_runtime(r0), "t0/15")
        jumped = boundary_jump(minimal_runtime(r0))
        promoted = promote(dense)
        demoted = demote(promoted)
        for runtime in (dense, jumped, promoted, demoted):
            self.assertEqual(canonical_json(authoritative_projection(runtime)), canonical_json(r0))
        self.assertEqual(dense["canonical_envelope"]["future_causal_state"]["canonical_clock"], "t0/00")
        self.assertEqual(jumped["resolution_local_state"]["samples"], [])
        self.assertEqual(demoted["resolution_local_state"]["cache"], {})

    def test_all_four_policy_histories_match_every_authoritative_checkpoint(self) -> None:
        runs = all_witness_runs()
        oracle = equivalence_oracle(runs)
        self.assertEqual(oracle, {"result": "accepted", "reference_witness": "dense_throughout", "failures": []})
        reference = runs["dense_throughout"]
        for run in runs.values():
            for label in ("R0", "R1", "R2", "R3"):
                self.assertEqual(
                    canonical_json(run["checkpoints"][label]),
                    canonical_json(reference["checkpoints"][label]),
                )
            self.assertEqual(
                canonical_json(run["final_canonical_envelope"]),
                canonical_json(reference["final_canonical_envelope"]),
            )
        self.assertNotEqual(
            runs["dense_throughout"]["diagnostic_resolution_trace"],
            runs["boundary_jump_throughout"]["diagnostic_resolution_trace"],
        )

    def test_each_policy_replays_byte_identically(self) -> None:
        for run in (
            dense_throughout_run,
            dense_demote_boundary_jump_promote_dense_run,
        ):
            self.assertEqual(canonical_json(run()), canonical_json(run()))

    def test_runtime_fail_closed_dispositions_are_exact_and_noncausal(self) -> None:
        results = runtime_fail_closed_results()
        expected = {
            "stale_R0_boundary_against_R1": REJECT_STALE_BOUNDARY,
            "cross_Y_boundary_from_R1": REJECT_BOUNDARY_CROSSING,
            "source_hash_mismatch": REJECT_BOUNDARY_SOURCE,
            "dense_mutates_canonical_clock": REJECT_LOCAL_AUTHORITY,
            "sample_caches_authoritative_gate": REJECT_GATE_CACHE,
            "promotion_carries_authority": REJECT_PROMOTION_AUTHORITY,
            "demotion_loses_authority": REJECT_DEMOTION_LOSS,
            "same_clock_successor_outside_payload": REJECT_SAME_CLOCK_SUCCESSOR,
        }
        self.assertEqual({name: result["disposition"] for name, result in results.items()}, expected)
        for result in results.values():
            self.assertFalse(result["authoritative_causal_ledger_appended"])
            self.assertFalse(result["future_schedule_created"])

    def test_equivalence_failure_preserves_divergent_candidate_artifacts(self) -> None:
        runs = all_witness_runs()
        candidate = copy.deepcopy(runs)
        candidate["boundary_jump_throughout"]["checkpoints"]["R2"]["canonical_envelope"]["current_causal_state"]["durable_facts"]["outcome_y"] = "pending"
        result = equivalence_oracle(candidate)
        self.assertEqual(result["result"], "equivalence_failure")
        self.assertTrue(result["failures"])
        self.assertEqual(
            runs["boundary_jump_throughout"]["checkpoints"]["R2"]["canonical_envelope"]["current_causal_state"]["durable_facts"]["outcome_y"],
            "failed_gate",
        )

    def test_source_audit_proves_scheduler_and_policy_isolation(self) -> None:
        audit = source_audit()
        self.assertEqual(audit["resolver_functions"], ["resolve_next_due"])
        self.assertEqual(audit["resolver_signature"], ["canonical_envelope", "canonical_boundary"])
        self.assertEqual(audit["scheduler_signature"], ["canonical_envelope"])
        self.assertFalse(audit["scheduler_reads_policy_local_state_or_trace"])
        self.assertFalse(audit["resolver_reads_policy_local_state_or_trace"])
        self.assertTrue(audit["boundary_requires_source_record_hash"])
        self.assertTrue(audit["scheduler_uses_at_or_after_clock"])
        self.assertFalse(audit["policy_calls_resolver"])
        self.assertFalse(audit["policy_evaluates_authoritative_gate"])
        self.assertFalse(audit["transitions_write_canonical_paths"])
        self.assertTrue(audit["definition_independence"]["passed"])
        self.assertEqual(audit["definition_independence"]["foreign_references"], [])
        self.assertFalse(audit["random_module_imported"])
        self.assertFalse(audit["unreal_or_city_content_present"])
        self.assertTrue(audit["payload_schema_exact"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
