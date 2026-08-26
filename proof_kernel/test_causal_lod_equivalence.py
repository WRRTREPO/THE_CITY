"""Regression tests for the frozen canonical-only Causal-LOD equivalence proof."""

from __future__ import annotations

import copy
import unittest

from kernel import canonical_json
from causal_lod_equivalence import (
    COMMITMENT_ID,
    DECISION_TIME,
    DUE_WORK_ID,
    NO_BOUNDARY,
    PAYLOAD_SCHEMA,
    REJECT_BOUNDARY_SKIP,
    REJECT_DEMOTION_LOSS,
    REJECT_GATE_CACHE,
    REJECT_POLICY_AUTHORITY,
    REJECT_PROMOTION_AUTHORITY,
    CanonicalEnvelopeRejected,
    all_witness_runs,
    assess_boundary_jump,
    assess_demotion_transition,
    assess_dense_transition,
    assess_promotion_transition,
    authoritative_projection,
    boundary_jump,
    boundary_jump_promote_dense_run,
    boundary_jump_throughout_run,
    canonical_hash,
    demote,
    dense_demote_boundary_jump_promote_dense_run,
    dense_inspection,
    dense_throughout_run,
    equivalence_oracle,
    finish_at_next_boundary,
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


R0_BOUNDARY = {"decision_time": DECISION_TIME, "due_work_ids": [DUE_WORK_ID]}


class CausalLodEquivalenceTests(unittest.TestCase):
    def test_r0_identity_is_new_exact_payload_schema(self) -> None:
        r0 = initial_canonical_envelope()
        self.assertEqual(r0["identity"]["payload_schema"], PAYLOAD_SCHEMA)
        self.assertEqual(r0["identity"]["simulation_version"], "0.7.0-draft.34")
        self.assertEqual(validate_canonical_envelope(r0), [])
        self.assertEqual(next_consequential_boundary(r0), R0_BOUNDARY)
        invalid = copy.deepcopy(r0)
        invalid["current_causal_state"]["durable_facts"]["unfrozen"] = True
        self.assertNotEqual(validate_canonical_envelope(invalid), [])

    def test_one_resolver_uses_r0_as_the_only_transaction_pre_state(self) -> None:
        r0 = initial_canonical_envelope()
        r1 = resolve_next_due(r0, R0_BOUNDARY)
        r0_hash = canonical_hash(r0)
        entry = r1["causal_provenance"]["authoritative_causal_ledger"][0]
        self.assertEqual(entry["parent_record_hash"], r0_hash)
        self.assertEqual(entry["transaction_pre_state_hash"], r0_hash)
        self.assertEqual(r1["causal_provenance"]["canonical_ancestry"]["parent_record_hash"], r0_hash)
        self.assertEqual(r1["future_causal_state"]["canonical_clock"], DECISION_TIME)
        self.assertEqual(len(r1["causal_provenance"]["authoritative_causal_ledger"]), 1)
        self.assertEqual(next_consequential_boundary(r1), NO_BOUNDARY)

    def test_resolver_rejects_an_alternate_boundary_before_canonical_mutation(self) -> None:
        r0 = initial_canonical_envelope()
        before = copy.deepcopy(r0)
        with self.assertRaises(CanonicalEnvelopeRejected):
            resolve_next_due(r0, NO_BOUNDARY)
        self.assertEqual(r0, before)

    def test_dense_samples_are_local_and_do_not_advance_canonical_clock(self) -> None:
        r0 = initial_canonical_envelope()
        runtime = dense_inspection(minimal_runtime(r0), "t0/15")
        self.assertEqual(canonical_json(authoritative_projection(runtime)), canonical_json(r0))
        self.assertEqual(runtime["canonical_envelope"]["future_causal_state"]["canonical_clock"], "t0/00")
        sample = runtime["resolution_local_state"]["samples"][0]
        self.assertEqual(sample["sample_position"], "t0/15")
        self.assertNotIn("authoritative_gate_result", canonical_json(sample))
        self.assertEqual(assess_dense_transition(r0, runtime)["result"], "accepted")

    def test_boundary_jump_has_no_intermediate_sample_or_canonical_effect(self) -> None:
        r0 = initial_canonical_envelope()
        runtime = boundary_jump(minimal_runtime(r0))
        self.assertEqual(canonical_json(authoritative_projection(runtime)), canonical_json(r0))
        self.assertEqual(runtime["resolution_local_state"]["samples"], [])
        self.assertEqual(runtime["resolution_local_state"]["profile"], "boundary_jump")
        self.assertEqual(assess_boundary_jump(r0, R0_BOUNDARY)["result"], "accepted")

    def test_promotion_and_demotion_are_non_causal_transitions(self) -> None:
        r0 = initial_canonical_envelope()
        promoted = promote(minimal_runtime(r0))
        self.assertEqual(canonical_json(authoritative_projection(promoted)), canonical_json(r0))
        self.assertIn(COMMITMENT_ID, promoted["resolution_local_state"]["cache"])
        self.assertEqual(assess_promotion_transition(r0, promoted)["result"], "accepted")
        demoted = demote(promoted)
        self.assertEqual(canonical_json(authoritative_projection(demoted)), canonical_json(r0))
        self.assertEqual(demoted["resolution_local_state"]["cache"], {})
        self.assertEqual(assess_demotion_transition(r0, demoted)["result"], "accepted")

    def test_all_four_witnesses_converge_on_byte_identical_authority(self) -> None:
        runs = all_witness_runs()
        oracle = equivalence_oracle(runs)
        self.assertEqual(oracle, {"result": "accepted", "reference_witness": "dense_throughout", "failures": []})
        reference = runs["dense_throughout"]
        r0_hash = canonical_hash(initial_canonical_envelope())
        for run in runs.values():
            self.assertEqual(canonical_json(run["final_canonical_envelope"]), canonical_json(reference["final_canonical_envelope"]))
            self.assertEqual(run["final_canonical_hash"], reference["final_canonical_hash"])
            self.assertEqual(run["transaction"]["header"]["parent_record_hash"], r0_hash)
            self.assertEqual(run["transaction"]["header"]["transaction_pre_state_hash"], r0_hash)
            self.assertEqual(run["next_consequential_boundary"], NO_BOUNDARY)

    def test_terminal_commitment_resource_ledger_and_schedule_are_exact(self) -> None:
        final = dense_throughout_run()["final_canonical_envelope"]
        self.assertEqual(final["current_causal_state"]["active_commitments"][COMMITMENT_ID]["state"], "succeeded")
        self.assertEqual(final["current_causal_state"]["durable_facts"]["commitment_alpha_outcome"], "succeeded")
        self.assertEqual(
            final["current_causal_state"]["resource_ownership"]["unit_alpha"],
            {"state": "available", "reservation_id": None, "owner_commitment_id": None},
        )
        self.assertEqual(final["future_causal_state"]["scheduled_consequential_decisions"], [])
        entry = final["causal_provenance"]["authoritative_causal_ledger"][0]
        self.assertEqual(entry["terminal_disposition"], "release_unit_alpha_on_success")

    def test_resolution_local_traces_may_differ_without_affecting_authority(self) -> None:
        dense = dense_throughout_run()
        jump = boundary_jump_throughout_run()
        mixed = boundary_jump_promote_dense_run()
        self.assertNotEqual(dense["diagnostic_resolution_trace"], jump["diagnostic_resolution_trace"])
        self.assertNotEqual(jump["resolution_local_state"], mixed["resolution_local_state"])
        self.assertEqual(dense["final_canonical_hash"], jump["final_canonical_hash"])

    def test_each_policy_sequence_replays_byte_identically(self) -> None:
        for run in (
            dense_throughout_run,
            boundary_jump_throughout_run,
            boundary_jump_promote_dense_run,
            dense_demote_boundary_jump_promote_dense_run,
        ):
            self.assertEqual(canonical_json(run()), canonical_json(run()))
        self.assertEqual(canonical_json(proof_run()), canonical_json(proof_run()))

    def test_runtime_fail_closed_cases_leave_no_canonical_side_effect(self) -> None:
        results = runtime_fail_closed_results()
        self.assertEqual(results["dense_mutates_canonical_clock"]["disposition"], REJECT_POLICY_AUTHORITY)
        self.assertEqual(results["sample_caches_authoritative_gate"]["disposition"], REJECT_GATE_CACHE)
        self.assertEqual(results["promotion_carries_authority"]["disposition"], REJECT_PROMOTION_AUTHORITY)
        self.assertEqual(results["demotion_loses_authority"]["disposition"], REJECT_DEMOTION_LOSS)
        self.assertEqual(results["boundary_jump_skips_due_work"]["disposition"], REJECT_BOUNDARY_SKIP)
        for result in results.values():
            self.assertFalse(result["authoritative_causal_ledger_appended"])
            self.assertFalse(result["future_schedule_created"])

    def test_equivalence_failure_preserves_divergent_candidate_artifacts_for_inspection(self) -> None:
        runs = all_witness_runs()
        candidate = copy.deepcopy(runs)
        candidate["boundary_jump_throughout"]["final_canonical_envelope"]["current_causal_state"]["resource_ownership"]["unit_alpha"]["state"] = "reserved"
        result = equivalence_oracle(candidate)
        self.assertEqual(result["result"], "equivalence_failure")
        self.assertTrue(any(item["failure"] == "final_canonical_envelope_differs" for item in result["failures"]))
        self.assertEqual(runs["boundary_jump_throughout"]["final_canonical_envelope"]["current_causal_state"]["resource_ownership"]["unit_alpha"]["state"], "available")

    def test_source_audit_proves_one_resolver_and_no_local_policy_dataflow(self) -> None:
        audit = source_audit()
        self.assertEqual(audit["resolver_functions"], ["resolve_next_due"])
        self.assertEqual(audit["resolver_signature"], ["canonical_envelope", "canonical_boundary"])
        self.assertFalse(audit["resolver_reads_policy_local_state_or_trace"])
        self.assertFalse(audit["policy_calls_resolver"])
        self.assertFalse(audit["policy_can_override_boundary"])
        self.assertFalse(audit["policy_evaluates_authoritative_gate"])
        self.assertFalse(audit["transitions_write_canonical_paths"])
        self.assertFalse(audit["random_module_imported"])
        self.assertFalse(audit["unreal_or_city_content_present"])
        self.assertTrue(audit["payload_schema_exact"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
