"""Regression tests for Same-Clock Successor Semantics Proof v0.1.0."""

from __future__ import annotations

import copy
import unittest

from kernel import canonical_json
from same_clock_successor_semantics import (
    BUDGET_ID,
    COMMITMENT_X,
    COMMITMENT_Y,
    NO_BOUNDARY,
    PAYLOAD_SCHEMA,
    PHASE_LIMIT,
    PHASE_X,
    PHASE_Y,
    REJECT_BOUNDARY_CROSSING,
    REJECT_BOUNDARY_SOURCE,
    REJECT_BUDGET,
    REJECT_CYCLE,
    REJECT_DEMOTION_LOSS,
    REJECT_DUPLICATE_MEMBER,
    REJECT_GATE_CACHE,
    REJECT_LOCAL_AUTHORITY,
    REJECT_PHASE_LIMIT,
    REJECT_PROMOTION_AUTHORITY,
    REJECT_RETROGRADE_PHASE,
    TIME,
    WORK_X,
    WORK_Y,
    CanonicalEnvelopeRejected,
    all_witness_runs,
    authoritative_projection,
    boundary_jump,
    boundary_jump_promote_dense_run,
    boundary_jump_throughout_run,
    canonical_hash,
    demote,
    dense_demote_boundary_jump_run,
    dense_inspection,
    dense_throughout_run,
    equivalence_oracle,
    initial_canonical_envelope,
    minimal_runtime,
    next_consequential_boundary,
    proof_run,
    promote,
    resolve_next_due,
    runtime_fail_closed_results,
    source_audit,
    validate_canonical_envelope,
)


class SameClockSuccessorSemanticsTests(unittest.TestCase):
    def _chain(self) -> tuple[dict, dict, dict]:
        r0 = initial_canonical_envelope()
        r1 = resolve_next_due(r0, next_consequential_boundary(r0))
        r2 = resolve_next_due(r1, next_consequential_boundary(r1))
        return r0, r1, r2

    def test_exact_payload_identity_and_r0_validation(self) -> None:
        r0 = initial_canonical_envelope()
        self.assertEqual(r0["identity"]["payload_schema"], PAYLOAD_SCHEMA)
        self.assertEqual(r0["identity"]["simulation_version"], "0.7.0-draft.47")
        self.assertEqual(validate_canonical_envelope(r0), [])
        self.assertEqual(r0["current_causal_state"]["active_and_terminal_commitments"][COMMITMENT_Y]["state"], "absent")
        self.assertNotIn(WORK_Y, canonical_json(r0))
        invalid = copy.deepcopy(r0)
        invalid["current_causal_state"]["durable_facts"]["unfrozen"] = True
        self.assertNotEqual(validate_canonical_envelope(invalid), [])

    def test_scheduler_returns_one_phase_boundary_with_complete_ordered_members(self) -> None:
        r0 = initial_canonical_envelope()
        bx = next_consequential_boundary(r0)
        self.assertEqual(bx["source_record_hash"], canonical_hash(r0))
        self.assertEqual((bx["decision_time"], bx["simulation_phase"]), (TIME, PHASE_X))
        self.assertEqual(bx["due_work_ids"], [WORK_X])
        self.assertEqual(bx["work_member_keys"], [[TIME, PHASE_X, WORK_X]])
        self.assertEqual(bx["due_work_ids"], sorted(bx["due_work_ids"]))

    def test_x_creates_later_same_clock_boundary_and_consumes_budget(self) -> None:
        r0 = initial_canonical_envelope()
        r1 = resolve_next_due(r0, next_consequential_boundary(r0))
        self.assertEqual(r1["future_causal_state"]["canonical_clock"], TIME)
        self.assertEqual(r1["current_causal_state"]["durable_facts"]["outcome_x"], "succeeded")
        self.assertEqual(r1["current_causal_state"]["active_and_terminal_commitments"][COMMITMENT_Y]["state"], "active")
        self.assertEqual(
            r1["current_causal_state"]["reservations_leases_and_resource_ownership"][BUDGET_ID],
            {"state": "consumed", "remaining_units": 0, "owner_commitment_id": COMMITMENT_X},
        )
        self.assertEqual(
            r1["future_causal_state"]["scheduled_consequential_decisions"],
            [{"decision_time": TIME, "simulation_phase": PHASE_Y, "due_work_ids": [WORK_Y]}],
        )
        entry = r1["causal_provenance"]["authoritative_causal_ledger"][-1]
        self.assertEqual(entry["source_record_hash"], canonical_hash(r0))
        self.assertEqual(entry["created_successor_boundary"]["parent_work_member_key"], [TIME, PHASE_X, WORK_X])

    def test_r1_rediscovery_invalidates_bx_even_without_clock_advance(self) -> None:
        r0 = initial_canonical_envelope()
        bx = next_consequential_boundary(r0)
        r1 = resolve_next_due(r0, bx)
        by = next_consequential_boundary(r1)
        self.assertEqual(r1["future_causal_state"]["canonical_clock"], TIME)
        self.assertEqual((by["decision_time"], by["simulation_phase"]), (TIME, PHASE_Y))
        self.assertEqual(by["source_record_hash"], canonical_hash(r1))
        with self.assertRaisesRegex(CanonicalEnvelopeRejected, REJECT_BOUNDARY_SOURCE):
            resolve_next_due(r1, bx)

    def test_y_resolves_at_later_phase_then_the_scheduler_returns_none(self) -> None:
        _, r1, r2 = self._chain()
        self.assertEqual(r2["future_causal_state"]["canonical_clock"], TIME)
        self.assertEqual(r2["current_causal_state"]["durable_facts"]["outcome_y"], "succeeded")
        self.assertEqual(r2["current_causal_state"]["active_and_terminal_commitments"][COMMITMENT_Y]["state"], "succeeded")
        self.assertEqual(r2["future_causal_state"]["scheduled_consequential_decisions"], [])
        self.assertEqual(r2["future_causal_state"]["canonical_work_member_keys"], [])
        self.assertEqual(next_consequential_boundary(r2), NO_BOUNDARY)
        y_entry = r2["causal_provenance"]["authoritative_causal_ledger"][-1]
        self.assertEqual(y_entry["source_record_hash"], canonical_hash(r1))
        self.assertEqual(y_entry["simulation_phase"], PHASE_Y)

    def test_successor_ancestry_and_ledger_pre_state_are_record_relative(self) -> None:
        r0, r1, r2 = self._chain()
        for parent, successor in ((r0, r1), (r1, r2)):
            parent_hash = canonical_hash(parent)
            self.assertEqual(successor["causal_provenance"]["canonical_ancestry"], {"parent_record_hash": parent_hash, "boundary_derivation": "next_consequential_boundary"})
            self.assertEqual(successor["causal_provenance"]["authoritative_causal_ledger"][-1]["source_record_hash"], parent_hash)
            self.assertNotIn("canonical_post_state_hash", canonical_json(successor))

    def test_four_resolution_policies_match_every_canonical_checkpoint(self) -> None:
        runs = all_witness_runs()
        self.assertEqual(equivalence_oracle(runs), {"result": "accepted", "reference_witness": "dense_throughout", "failures": []})
        reference = runs["dense_throughout"]
        for run in runs.values():
            for label in ("R0", "R1", "R2"):
                self.assertEqual(canonical_json(run["checkpoints"][label]), canonical_json(reference["checkpoints"][label]))
            self.assertEqual(run["final_canonical_hash"], reference["final_canonical_hash"])

    def test_resolution_local_histories_differ_without_changing_authority(self) -> None:
        dense = dense_throughout_run()
        jump = boundary_jump_throughout_run()
        mixed = boundary_jump_promote_dense_run()
        self.assertNotEqual(dense["diagnostic_resolution_trace"], jump["diagnostic_resolution_trace"])
        self.assertNotEqual(jump["resolution_local_state"], mixed["resolution_local_state"])
        self.assertEqual(dense["final_canonical_hash"], jump["final_canonical_hash"])

    def test_each_witness_and_the_complete_proof_replay_byte_identically(self) -> None:
        for run in (dense_throughout_run, boundary_jump_throughout_run, dense_demote_boundary_jump_run, boundary_jump_promote_dense_run):
            self.assertEqual(canonical_json(run()), canonical_json(run()))
        self.assertEqual(canonical_json(proof_run()), canonical_json(proof_run()))

    def test_promotion_and_demotion_keep_authority_exactly_unchanged(self) -> None:
        r0 = initial_canonical_envelope()
        promoted = promote(minimal_runtime(r0))
        self.assertEqual(canonical_json(authoritative_projection(promoted)), canonical_json(r0))
        self.assertIn("next_boundary_display", promoted["resolution_local_state"]["cache"])
        demoted = demote(promoted)
        self.assertEqual(canonical_json(authoritative_projection(demoted)), canonical_json(r0))
        jumped = boundary_jump(demoted)
        self.assertEqual(canonical_json(authoritative_projection(jumped)), canonical_json(r0))
        sampled = dense_inspection(jumped, "t0/15")
        self.assertEqual(canonical_json(authoritative_projection(sampled)), canonical_json(r0))

    def test_all_malformed_boundaries_and_local_authority_attempts_fail_closed(self) -> None:
        results = runtime_fail_closed_results()
        expected = {
            "retrograde_or_equal_phase": REJECT_RETROGRADE_PHASE,
            "phase_limit_exceeded": REJECT_PHASE_LIMIT,
            "duplicate_work_member": REJECT_DUPLICATE_MEMBER,
            "cyclic_or_settled_work": REJECT_CYCLE,
            "generation_budget_exhausted": REJECT_BUDGET,
            "stale_BX_against_R1": REJECT_BOUNDARY_SOURCE,
            "fabricated_BY_against_R0": REJECT_BOUNDARY_CROSSING,
            "crossing_boundary_against_R1": REJECT_BOUNDARY_CROSSING,
            "local_clock_authority": REJECT_LOCAL_AUTHORITY,
            "cached_authoritative_gate": REJECT_GATE_CACHE,
            "promotion_authority": REJECT_PROMOTION_AUTHORITY,
            "demotion_authority_loss": REJECT_DEMOTION_LOSS,
        }
        self.assertEqual({name: value["disposition"] for name, value in results.items()}, expected)
        for result in results.values():
            self.assertFalse(result["authoritative_causal_ledger_appended"])
            self.assertFalse(result["future_schedule_created"])
            self.assertFalse(result["canonical_mutation_committed"])

    def test_equivalence_oracle_preserves_divergent_candidate_artifacts(self) -> None:
        runs = all_witness_runs()
        candidate = copy.deepcopy(runs)
        candidate["boundary_jump_throughout"]["checkpoints"]["R1"]["canonical_envelope"]["future_causal_state"]["canonical_clock"] = "t1/01"
        result = equivalence_oracle(candidate)
        self.assertEqual(result["result"], "equivalence_failure")
        self.assertTrue(any(item["failure"] == "checkpoint_R1_differs" for item in result["failures"]))
        self.assertEqual(runs["boundary_jump_throughout"]["checkpoints"]["R1"]["canonical_envelope"]["future_causal_state"]["canonical_clock"], TIME)

    def test_source_audit_proves_policy_isolation_and_boundary_member_distinction(self) -> None:
        audit = source_audit()
        self.assertEqual(audit["resolver_functions"], ["resolve_next_due"])
        self.assertEqual(audit["scheduler_signature"], ["canonical_envelope"])
        self.assertTrue(audit["scheduler_selects_boundary_not_member"])
        self.assertTrue(audit["scheduler_returns_complete_due_set"])
        self.assertFalse(audit["work_id_creates_transaction_boundaries"])
        self.assertFalse(audit["resolver_reads_policy_local_state_or_trace"])
        self.assertFalse(audit["policy_calls_resolver"])
        self.assertFalse(audit["policy_evaluates_authoritative_gate"])
        self.assertFalse(audit["policy_can_override_boundary"])
        self.assertFalse(audit["policy_writes_canonical_paths"])
        self.assertTrue(audit["scheduler_requeries_after_each_commit"])
        self.assertTrue(audit["same_clock_budget_authoritative"])
        self.assertFalse(audit["random_module_imported"])
        self.assertFalse(audit["unreal_or_city_content_present"])
        self.assertFalse(audit["self_referential_successor_hash_present"])
        self.assertTrue(audit["payload_schema_exact"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
