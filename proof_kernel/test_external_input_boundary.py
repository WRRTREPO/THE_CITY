"""Regression tests for External Input Boundary Proof v0.1.1."""

from __future__ import annotations

import copy
import unittest

from kernel import canonical_json
from external_input_boundary import (
    COMMITMENT_ALPHA,
    INPUT_ID,
    NO_AUTONOMOUS_BOUNDARY,
    NO_EXECUTION_BOUNDARY,
    PAYLOAD_SCHEMA,
    REJECT_BOUNDARY_CROSSING,
    REJECT_BOUNDARY_SOURCE,
    REJECT_DEMOTION_LOSS,
    REJECT_GATE_CACHE,
    REJECT_INPUT_ACCEPTED,
    REJECT_INPUT_CONTRACT,
    REJECT_INPUT_DIGEST,
    REJECT_INPUT_SOURCE,
    REJECT_INPUT_TIME,
    REJECT_LOCAL_AUTHORITY,
    REJECT_PROMOTION_AUTHORITY,
    CanonicalEnvelopeRejected,
    ExternalInputRejected,
    ResolutionPolicyRejected,
    advance_runtime,
    admit_external_input_candidate,
    all_witness_runs,
    authoritative_projection,
    boundary_jump,
    canonical_hash,
    cursor_reset_witness,
    demote,
    dense_inspection,
    dense_throughout_run,
    equivalence_oracle,
    external_evidence_q,
    initial_canonical_envelope,
    minimal_runtime,
    next_consequential_boundary,
    next_execution_boundary,
    promote,
    q_absent_control_run,
    resolve_execution_boundary,
    runtime_fail_closed_results,
    source_audit,
    validate_canonical_envelope,
)


class ExternalInputBoundaryTests(unittest.TestCase):
    def _primary_chain(self) -> tuple[dict, dict, dict, dict]:
        r0 = initial_canonical_envelope()
        q = external_evidence_q(r0)
        bq = admit_external_input_candidate(r0, q)
        rinput = resolve_execution_boundary(r0, bq, q)
        alpha = next_execution_boundary(rinput, [q], 1)
        rfinal = resolve_execution_boundary(rinput, alpha, None)
        return r0, q, rinput, rfinal

    def test_exact_corrected_identity_and_no_in_record_post_hashes(self) -> None:
        r0, _, rinput, rfinal = self._primary_chain()
        self.assertEqual(r0["identity"]["payload_schema"], PAYLOAD_SCHEMA)
        self.assertEqual(r0["identity"]["simulation_version"], "0.7.0-draft.45")
        self.assertEqual(validate_canonical_envelope(r0), [])
        self.assertEqual(validate_canonical_envelope(rinput), [])
        self.assertEqual(validate_canonical_envelope(rfinal), [])
        for record in (rinput, rfinal):
            self.assertNotIn("canonical_post_state_hash", canonical_json(record))
        invalid = copy.deepcopy(r0)
        invalid["current_causal_state"]["durable_facts"]["unfrozen"] = True
        self.assertNotEqual(validate_canonical_envelope(invalid), [])

    def test_admission_is_side_effect_free_and_constructs_r0_bound_bq(self) -> None:
        r0 = initial_canonical_envelope()
        before = canonical_json(r0)
        q = external_evidence_q(r0)
        bq = admit_external_input_candidate(r0, q)
        self.assertEqual(canonical_json(r0), before)
        self.assertEqual(
            bq,
            {
                "decision_time": "t0/30",
                "due_work_ids": [],
                "external_input_id": INPUT_ID,
                "kind": "external_input",
                "source_record_hash": canonical_hash(r0),
            },
        )

    def test_integrity_and_contract_rejections_are_distinct_and_terminal(self) -> None:
        r0 = initial_canonical_envelope()
        q = external_evidence_q(r0)
        tampered = copy.deepcopy(q)
        tampered["target"]["id"] = "redirected"
        with self.assertRaisesRegex(ExternalInputRejected, REJECT_INPUT_DIGEST):
            admit_external_input_candidate(r0, tampered)

        redirected = copy.deepcopy(tampered)
        projection = copy.deepcopy(redirected)
        projection["evidence"].pop("evidence_digest")
        from external_input_boundary import evidence_digest

        redirected["evidence"]["evidence_digest"] = evidence_digest(projection)
        with self.assertRaisesRegex(ExternalInputRejected, REJECT_INPUT_CONTRACT):
            admit_external_input_candidate(r0, redirected)
        unknown = copy.deepcopy(q)
        unknown["unfrozen"] = True
        unknown_projection = copy.deepcopy(unknown)
        unknown_projection["evidence"].pop("evidence_digest")
        unknown["evidence"]["evidence_digest"] = evidence_digest(unknown_projection)
        with self.assertRaisesRegex(ExternalInputRejected, REJECT_INPUT_CONTRACT):
            admit_external_input_candidate(r0, unknown)
        missing_target = copy.deepcopy(q)
        missing_target.pop("target")
        missing_projection = copy.deepcopy(missing_target)
        missing_projection["evidence"].pop("evidence_digest")
        missing_target["evidence"]["evidence_digest"] = evidence_digest(missing_projection)
        with self.assertRaisesRegex(ExternalInputRejected, REJECT_INPUT_CONTRACT):
            admit_external_input_candidate(r0, missing_target)
        self.assertEqual(r0["current_causal_state"]["accepted_external_inputs"], [])
        self.assertEqual(r0["causal_provenance"]["authoritative_causal_ledger"], [])

    def test_coordinator_intercepts_accepted_input_before_autonomous_boundary(self) -> None:
        r0 = initial_canonical_envelope()
        q = external_evidence_q(r0)
        autonomous = next_consequential_boundary(r0)
        execution = next_execution_boundary(r0, [q], 0)
        self.assertEqual(autonomous["decision_time"], "t1/00")
        self.assertEqual(execution["kind"], "external_input")
        self.assertEqual(execution["decision_time"], "t0/30")
        auto_boundary = {
            "decision_time": "t1/00",
            "due_work_ids": ["t1/00/input-boundary/commitment_alpha.resolve"],
            "external_input_id": None,
            "kind": "autonomous_consequence",
            "source_record_hash": canonical_hash(r0),
        }
        with self.assertRaisesRegex(CanonicalEnvelopeRejected, REJECT_BOUNDARY_CROSSING):
            resolve_execution_boundary(r0, auto_boundary, q)

    def test_q_commits_only_declared_fact_then_alpha_revalidates_rinput(self) -> None:
        r0, q, rinput, rfinal = self._primary_chain()
        h0 = canonical_hash(r0)
        hi = canonical_hash(rinput)
        hf = canonical_hash(rfinal)
        self.assertEqual(rinput["causal_provenance"]["canonical_ancestry"]["parent_record_hash"], h0)
        q_entry = rinput["causal_provenance"]["authoritative_causal_ledger"][-1]
        self.assertEqual(q_entry["canonical_pre_state_hash"], h0)
        self.assertNotIn("canonical_post_state_hash", q_entry)
        self.assertEqual(rinput["current_causal_state"]["gate_relevant_state"]["gate_token_state"], "disabled")
        self.assertEqual(rinput["current_causal_state"]["accepted_external_inputs"], [INPUT_ID])
        self.assertEqual(next_consequential_boundary(rinput)["source_record_hash"], hi)
        self.assertEqual(next_execution_boundary(rinput, [q], 1)["kind"], "autonomous_consequence")

        self.assertEqual(rfinal["causal_provenance"]["canonical_ancestry"]["parent_record_hash"], hi)
        alpha_entry = rfinal["causal_provenance"]["authoritative_causal_ledger"][-1]
        self.assertEqual(alpha_entry["canonical_pre_state_hash"], hi)
        self.assertNotIn("canonical_post_state_hash", alpha_entry)
        self.assertEqual(alpha_entry["evaluated_gates"][0]["observed_value"], "disabled")
        self.assertFalse(alpha_entry["evaluated_gates"][0]["result"])
        self.assertEqual(rfinal["current_causal_state"]["durable_facts"]["alpha_outcome"], "failed_gate")
        self.assertEqual(rfinal["current_causal_state"]["reservations_leases_and_resource_ownership"]["unit_alpha"]["state"], "available")
        self.assertEqual(next_consequential_boundary(rfinal), NO_AUTONOMOUS_BOUNDARY)
        self.assertEqual(next_execution_boundary(rfinal, [q], 1), NO_EXECUTION_BOUNDARY)
        self.assertEqual(canonical_hash(rfinal), hf)

    def test_q_absent_control_preserves_alpha_definition_and_succeeds(self) -> None:
        primary_r0, _, _, _ = self._primary_chain()
        control = q_absent_control_run()
        final = control["control_final"]
        self.assertEqual(canonical_json(control["R0"]["canonical_envelope"]), canonical_json(primary_r0))
        self.assertEqual(control["boundary"]["kind"], "autonomous_consequence")
        self.assertEqual(final["current_causal_state"]["durable_facts"]["alpha_outcome"], "succeeded")
        self.assertEqual(
            final["current_causal_state"]["active_and_terminal_commitments"][COMMITMENT_ALPHA]["terminal_disposition"],
            "release_unit_alpha_on_success",
        )
        self.assertEqual(control["next_execution_boundary"], NO_EXECUTION_BOUNDARY)

    def test_cursor_reset_cannot_readmit_an_already_accepted_q(self) -> None:
        witness = cursor_reset_witness()
        self.assertEqual(witness["accepted_external_inputs"], [INPUT_ID])
        self.assertEqual(witness["next_execution_boundary"]["kind"], "autonomous_consequence")
        r0, q, rinput, _ = self._primary_chain()
        with self.assertRaisesRegex(ExternalInputRejected, REJECT_INPUT_ACCEPTED):
            admit_external_input_candidate(rinput, q)
        self.assertNotEqual(witness["Rinput_hash"], canonical_hash(r0))

    def test_all_four_policies_match_at_every_authoritative_checkpoint(self) -> None:
        runs = all_witness_runs()
        self.assertEqual(equivalence_oracle(runs), {"result": "accepted", "reference_witness": "dense_throughout", "failures": []})
        reference = runs["dense_throughout"]
        for run in runs.values():
            for checkpoint in ("R0", "Rinput", "Rfinal"):
                self.assertEqual(canonical_json(run["checkpoints"][checkpoint]), canonical_json(reference["checkpoints"][checkpoint]))
        self.assertNotEqual(reference["diagnostic_resolution_trace"], runs["boundary_jump_throughout"]["diagnostic_resolution_trace"])

    def test_promotion_demotion_and_dense_samples_are_resolution_local(self) -> None:
        r0 = initial_canonical_envelope()
        runtime = minimal_runtime(r0, [external_evidence_q(r0)])
        dense = dense_inspection(runtime, "t0/10")
        promoted = promote(dense)
        demoted = demote(promoted)
        jumped = boundary_jump(runtime)
        for candidate in (dense, promoted, demoted, jumped):
            self.assertEqual(canonical_json(authoritative_projection(candidate)), canonical_json(r0))
        self.assertEqual(demoted["resolution_local_state"]["cache"], {})

    def test_runtime_fail_closed_dispositions_do_not_append_canonical_history(self) -> None:
        results = runtime_fail_closed_results()
        expected = {
            "source_hash_mismatch": REJECT_INPUT_SOURCE,
            "digest_covered_field_changed_without_recompute": REJECT_INPUT_DIGEST,
            "redirected_contract_with_recomputed_digest": REJECT_INPUT_CONTRACT,
            "late_or_equal_time_input": REJECT_INPUT_TIME,
            "autonomous_boundary_crosses_available_Q": REJECT_BOUNDARY_CROSSING,
            "stale_BQ_against_Rinput": REJECT_BOUNDARY_SOURCE,
            "cursor_skips_unaccepted_Q": REJECT_LOCAL_AUTHORITY,
            "local_sample_caches_authoritative_gate": REJECT_GATE_CACHE,
            "local_policy_requests_canonical_mutation": REJECT_LOCAL_AUTHORITY,
            "promotion_carries_authority": REJECT_PROMOTION_AUTHORITY,
            "demotion_loses_authority": REJECT_DEMOTION_LOSS,
        }
        self.assertEqual({name: value["disposition"] for name, value in results.items()}, expected)
        for result in results.values():
            self.assertTrue(result["canonical_unchanged"])
            self.assertFalse(result["cursor_advanced"])
            self.assertTrue(result["test_terminal"])

    def test_stale_bq_is_bound_to_r0_not_rinput(self) -> None:
        r0, q, rinput, _ = self._primary_chain()
        bq = admit_external_input_candidate(r0, q)
        before = canonical_json(rinput)
        with self.assertRaisesRegex(CanonicalEnvelopeRejected, REJECT_BOUNDARY_SOURCE):
            resolve_execution_boundary(rinput, bq, q)
        self.assertEqual(canonical_json(rinput), before)

    def test_each_policy_replays_byte_identically_and_source_audit_is_clean(self) -> None:
        self.assertEqual(canonical_json(dense_throughout_run()), canonical_json(dense_throughout_run()))
        audit = source_audit()
        self.assertTrue(audit["passed"])
        self.assertEqual(audit["resolver_functions"], ["resolve_execution_boundary"])
        self.assertEqual(audit["resolver_signature"], ["canonical_envelope", "execution_boundary", "q"])
        self.assertFalse(audit["policy_calls_resolver"])
        self.assertFalse(audit["policy_evaluates_authoritative_gate"])
        self.assertFalse(audit["random_module_imported"])
        self.assertFalse(audit["unreal_or_city_content_present"])
        self.assertFalse(audit["canonical_post_state_hash_present"])
        self.assertFalse(audit["input_shortcut_present"])

    def test_runtime_local_authority_is_rejected(self) -> None:
        runtime = minimal_runtime(initial_canonical_envelope())
        runtime["resolution_local_state"]["cache"]["authoritative_gate_result"] = True
        with self.assertRaises(ResolutionPolicyRejected):
            boundary_jump(runtime)


if __name__ == "__main__":
    unittest.main()
