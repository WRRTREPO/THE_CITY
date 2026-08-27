"""Focused conformance checks for Concurrent External Evidence Arbitration."""

from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from kernel import canonical_json
from concurrent_external_evidence_arbitration import (
    DOMAIN_TABLE,
    EVENT_A,
    EVENT_B,
    INPUT_A,
    INPUT_B,
    PAYLOAD_SCHEMA,
    SIMULATION_VERSION,
    BatchConstructionRejected,
    ExternalEvidenceRejected,
    admit_external_input_candidate,
    all_witness_runs,
    canonical_hash,
    construct_bext_from_sealed_fixture_set,
    control_runs,
    equivalence_oracle,
    evidence_emission_receipt,
    external_evidence_q,
    fail_closed_results,
    initial_canonical_envelope,
    launch_receipt,
    materialization_acceptance_receipt,
    primary_fixture,
    proof_run,
    qa_only_fixture,
    qb_only_fixture,
    q_hash,
    q_raw_sha256,
    raw_payload_sha256,
    resolve_external_batch,
    source_audit,
    stored_payload_bytes,
    stored_q_bytes,
    stored_receipt_bytes,
    validate_launch_artifact,
    working_state_identity,
    write_artifacts,
)


class ConcurrentExternalEvidenceArbitrationTests(unittest.TestCase):
    def _candidates(self):
        r0 = initial_canonical_envelope()
        qa = external_evidence_q(r0, "domain_A")
        qb = external_evidence_q(r0, "domain_B")
        receipt_a = materialization_acceptance_receipt(r0, "domain_A", "test_domain_A_process")
        receipt_b = materialization_acceptance_receipt(r0, "domain_B", "test_domain_B_process")
        admitted_a = admit_external_input_candidate(
            r0, qa, stored_q_bytes(qa), receipt_a,
            evidence_emission_receipt(r0, qa, "domain_A", "test_domain_A_process"),
        )
        admitted_b = admit_external_input_candidate(
            r0, qb, stored_q_bytes(qb), receipt_b,
            evidence_emission_receipt(r0, qb, "domain_B", "test_domain_B_process"),
        )
        return r0, qa, qb, admitted_a, admitted_b

    def _primary(self, presentation_order=("A", "B")):
        r0, qa, qb, admitted_a, admitted_b = self._candidates()
        members = [admitted_a, admitted_b] if presentation_order == ("A", "B") else [admitted_b, admitted_a]
        bext, member_map = construct_bext_from_sealed_fixture_set(r0, primary_fixture(), members)
        return r0, qa, qb, bext, member_map, resolve_external_batch(r0, bext, member_map)

    def test_exact_identity_r0_and_no_self_hash(self) -> None:
        r0 = initial_canonical_envelope()
        self.assertEqual(r0["identity"]["payload_schema"], PAYLOAD_SCHEMA)
        self.assertEqual(r0["identity"]["simulation_version"], SIMULATION_VERSION)
        self.assertEqual(SIMULATION_VERSION, "0.7.0-draft.57")
        self.assertIsNone(r0["current_causal_state"]["shared_slot"]["allocation_owner"])
        self.assertEqual(r0["future_causal_state"], {"canonical_clock": "t0/00", "unresolved_work": []})
        self.assertNotIn("canonical_post_state_hash", canonical_json(r0))

    def test_q_bytes_digests_and_contracts_are_exact_and_distinct(self) -> None:
        r0, qa, qb, _, _ = self._candidates()
        self.assertEqual(qa["input_id"], INPUT_A)
        self.assertEqual(qb["input_id"], INPUT_B)
        self.assertEqual(qa["physical_event_id"], EVENT_A)
        self.assertEqual(qb["physical_event_id"], EVENT_B)
        self.assertNotEqual(stored_q_bytes(qa), stored_q_bytes(qb))
        self.assertEqual(len(q_hash(qa)), 64)
        self.assertEqual(len(q_raw_sha256(qa)), 64)
        self.assertEqual(qa["source"]["source_record_hash"], canonical_hash(r0))
        self.assertEqual(qa["source"]["source_payload_raw_sha256"], raw_payload_sha256(r0))
        self.assertNotIn("external_phase", qa)
        self.assertNotIn("canonical_external_priority", qa)

    def test_detached_launch_and_ue_receipts_bind_exact_r0_and_q(self) -> None:
        r0, qa, qb, _, _ = self._candidates()
        payload = stored_payload_bytes(r0)
        self.assertEqual(validate_launch_artifact(payload, stored_receipt_bytes(launch_receipt(r0))), r0)
        for domain, q in (("domain_A", qa), ("domain_B", qb)):
            process_id = f"test_{domain}_process"
            accepted = materialization_acceptance_receipt(r0, domain, process_id)
            emitted = evidence_emission_receipt(r0, q, domain, process_id)
            self.assertEqual(accepted["accepted_canonical_hash"], canonical_hash(r0))
            self.assertEqual(emitted["accepted_canonical_hash"], canonical_hash(r0))
            self.assertEqual(emitted["emitted_q_canonical_hash"], q_hash(q))
            self.assertEqual(emitted["emitted_q_raw_sha256"], q_raw_sha256(q))

    def test_admission_is_independent_side_effect_free_and_observes_r0(self) -> None:
        r0, _, _, admitted_a, admitted_b = self._candidates()
        before = canonical_json(r0)
        for admitted in (admitted_a, admitted_b):
            self.assertEqual(admitted["source_record_hash"], canonical_hash(r0))
            self.assertEqual(len(admitted["immutable_admission_observations"]), 9)
            self.assertTrue(all(item["result"] for item in admitted["immutable_admission_observations"]))
            self.assertEqual(admitted["derived_external_phase"], 10)
            self.assertEqual(admitted["derived_canonical_external_priority"], 100)
        self.assertEqual(canonical_json(r0), before)
        self.assertEqual(r0["causal_provenance"]["adjudicated_external_input_ids"], [])

    def test_sealed_fixture_is_input_not_live_collection_state(self) -> None:
        r0, _, _, admitted_a, admitted_b = self._candidates()
        fixture = primary_fixture()
        self.assertEqual(fixture["required_input_id_set"], sorted((INPUT_A, INPUT_B)))
        self.assertNotIn("timeout", canonical_json(fixture))
        self.assertNotIn("poll", canonical_json(fixture))
        first, _ = construct_bext_from_sealed_fixture_set(r0, fixture, [admitted_a, admitted_b])
        reversed_bext, _ = construct_bext_from_sealed_fixture_set(r0, fixture, [admitted_b, admitted_a])
        self.assertEqual(first, reversed_bext)

    def test_bext_derives_one_canonical_order_independent_of_presentation(self) -> None:
        r0, _, _, bext, member_map, _ = self._primary(("A", "B"))
        _, _, _, reversed_bext, reversed_map, _ = self._primary(("B", "A"))
        self.assertEqual(bext, reversed_bext)
        self.assertEqual(member_map, reversed_map)
        self.assertEqual(bext["source_record_hash"], canonical_hash(r0))
        self.assertEqual(bext["batch_pre_state_hash"], canonical_hash(r0))
        self.assertEqual(bext["member_ids"], [INPUT_A, INPUT_B])

    def test_primary_is_one_atomic_successor_with_ordinary_failed_gate(self) -> None:
        r0, _, _, bext, _, r1 = self._primary()
        self.assertEqual(r1["current_causal_state"]["shared_slot"]["allocation_owner"], "domain_A")
        self.assertEqual(r1["future_causal_state"]["canonical_clock"], "t0/30")
        self.assertEqual(r1["causal_provenance"]["canonical_ancestry"]["parent_record_hash"], canonical_hash(r0))
        self.assertEqual(r1["causal_provenance"]["adjudicated_external_input_ids"], [INPUT_A, INPUT_B])
        self.assertEqual(r1["causal_provenance"]["adjudicated_physical_event_ids"], [EVENT_A, EVENT_B])
        ledger = r1["causal_provenance"]["authoritative_causal_ledger"]
        self.assertEqual(len(ledger), 1)
        self.assertEqual(ledger[0]["boundary"], bext)
        self.assertEqual([item["adjudication_disposition"] for item in ledger[0]["members"]], ["mutation_committed", "failed_gate"])
        self.assertEqual(ledger[0]["members"][1]["resource_disposition"], "no_resource_acquired")
        self.assertEqual(ledger[0]["members"][1]["working_state_gate_observations"][0]["observed_value"], "domain_A")
        self.assertNotIn("canonical_post_state_hash", canonical_json(r1))

    def test_provisional_identities_are_tagged_self_hash_safe_and_noncanonical(self) -> None:
        r0, _, _, _, _, r1 = self._primary()
        members = r1["causal_provenance"]["authoritative_causal_ledger"][0]["members"]
        p0 = members[0]["working_pre_state_identity"]
        pa = members[0]["working_post_state_identity"]
        self.assertEqual(members[1]["working_pre_state_identity"], pa)
        self.assertEqual(members[1]["working_post_state_identity"], pa)
        for identity in (p0, pa):
            self.assertEqual(identity["identity_schema"], "ExternalBatchWorkingStateIdentity.v1")
            self.assertEqual(identity["identity_kind"], "provisional_external_batch_working_state")
            self.assertEqual(len(identity["digest"]), 64)
            self.assertNotEqual(identity["digest"], canonical_hash(r0))
        projection = {
            "batch_working_state_schema": "ExternalArbitrationWorkingState.v1",
            "batch_pre_state_hash": canonical_hash(r0),
            "provisional_current_causal_state": r0["current_causal_state"],
            "provisional_future_causal_state": r0["future_causal_state"],
        }
        self.assertEqual(working_state_identity(projection), p0)

    def test_w1_w4_are_byte_identical_in_all_authoritative_objects(self) -> None:
        runs = all_witness_runs()
        self.assertEqual(set(runs), {"W1", "W2", "W3", "W4"})
        self.assertEqual(equivalence_oracle(runs)["result"], "accepted")
        reference = runs["W1"]
        for run in runs.values():
            for key in ("canonical_checkpoints", "sealed_fixture_candidate_set", "admitted_members_by_input_id", "BEXT"):
                self.assertEqual(canonical_json(run[key]), canonical_json(reference[key]))
        self.assertNotEqual(runs["W1"]["non_authoritative_trace"], runs["W4"]["non_authoritative_trace"])

    def test_singleton_controls_use_same_q_definitions_and_same_resolver(self) -> None:
        r0, qa, qb, admitted_a, admitted_b = self._candidates()
        controls = control_runs()
        self.assertEqual(set(controls), {"QA_only", "QB_only"})
        self.assertEqual(controls["QA_only"]["Q"], qa)
        self.assertEqual(controls["QB_only"]["Q"], qb)
        self.assertEqual(controls["QA_only"]["successor"]["current_causal_state"]["shared_slot"]["allocation_owner"], "domain_A")
        self.assertEqual(controls["QB_only"]["successor"]["current_causal_state"]["shared_slot"]["allocation_owner"], "domain_B")
        for fixture, admitted, owner in ((qa_only_fixture(), admitted_a, "domain_A"), (qb_only_fixture(), admitted_b, "domain_B")):
            bext, member_map = construct_bext_from_sealed_fixture_set(r0, fixture, [admitted])
            self.assertEqual(resolve_external_batch(r0, bext, member_map)["current_causal_state"]["shared_slot"]["allocation_owner"], owner)

    def test_digest_and_redirected_contract_failures_are_distinct_and_premutation(self) -> None:
        r0 = initial_canonical_envelope()
        qa = external_evidence_q(r0, "domain_A")
        altered = copy.deepcopy(qa)
        altered["target"]["id"] = "redirected"
        with self.assertRaises(ExternalEvidenceRejected):
            admit_external_input_candidate(r0, altered, stored_q_bytes(altered), {}, {})
        redirected = copy.deepcopy(qa)
        redirected["source"]["domain"] = "domain_B"
        from concurrent_external_evidence_arbitration import evidence_digest
        projection = copy.deepcopy(redirected)
        projection["evidence"].pop("evidence_digest")
        redirected["evidence"]["evidence_digest"] = evidence_digest(projection)
        with self.assertRaises(ExternalEvidenceRejected):
            admit_external_input_candidate(r0, redirected, stored_q_bytes(redirected), {}, {})
        self.assertEqual(canonical_json(r0), canonical_json(initial_canonical_envelope()))

    def test_duplicate_construction_rejects_before_map_overwrite(self) -> None:
        r0, _, _, admitted_a, admitted_b = self._candidates()
        duplicate = copy.deepcopy(admitted_b)
        duplicate["input_id"] = admitted_a["input_id"]
        with self.assertRaises(BatchConstructionRejected):
            construct_bext_from_sealed_fixture_set(r0, primary_fixture(), [admitted_a, duplicate])

    def test_all_declared_failures_and_six_fault_points_are_fail_closed(self) -> None:
        failures = fail_closed_results()
        required = {
            "malformed_q", "digest_changed_without_recompute", "redirected_with_recomputed_digest", "wrong_source_record",
            "input_id_already_adjudicated", "physical_event_id_already_adjudicated",
            "duplicate_input_id", "duplicate_physical_event_id", "member_set_digest_mismatch", "member_not_admitted",
            "harness_order_authority", "ue_priority_authority", "stale_bext_source", "member_map_set_mismatch",
            "mutation_outside_contract", "metadata_order_authority", "member_owned_successor", "provisional_state_exposure",
            "provisional_identity_as_canonical", "canonical_hash_as_working_identity", "local_authority_leak",
            "fault_after_QA_mutation", "fault_after_QB_gate", "fault_during_replay_barriers", "fault_during_batch_ledger",
            "fault_after_candidate_R1_before_validation", "fault_after_R1_validation_before_publication",
        }
        self.assertTrue(required.issubset(failures), required - set(failures))
        for name, result in failures.items():
            self.assertTrue(result["canonical_unchanged"], name)
            self.assertFalse(result["canonical_successor_published"], name)
            self.assertFalse(result["canonical_replay_barrier_published"], name)

    def test_order_poison_does_not_change_bext_or_r1(self) -> None:
        failures = fail_closed_results()
        for name in ("filesystem_mtime_poison", "directory_enumeration_reverse", "candidate_container_reverse", "process_trace_reverse"):
            self.assertIn(name, failures)
            self.assertTrue(failures[name]["canonical_unchanged"])

    def test_source_audit_proves_one_path_no_transport_and_no_provisional_authority(self) -> None:
        audit = source_audit()
        self.assertTrue(audit["passed"])
        self.assertEqual(audit["canonical_resolver_functions"], ["resolve_external_batch"])
        self.assertFalse(audit["resolver_prohibited_dataflow_names"])
        self.assertFalse(audit["resolver_receives_presentation_container"])
        self.assertFalse(audit["resolver_receives_unreal_or_process_state"])
        self.assertFalse(audit["live_transport_terms_in_resolver"])
        self.assertFalse(audit["random_module_imported"])
        self.assertTrue(audit["resolver_has_one_return_statement"])

    def test_deterministic_regeneration(self) -> None:
        self.assertEqual(canonical_json(proof_run()), canonical_json(proof_run()))
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw)
            write_artifacts(output)
            self.assertTrue((output / "concurrent_external_R0.json").is_file())
            self.assertTrue((output / "concurrent_external_W4_run.json").is_file())
            self.assertTrue((output / "concurrent_external_proof_run.json").is_file())


if __name__ == "__main__":
    unittest.main(verbosity=2)
