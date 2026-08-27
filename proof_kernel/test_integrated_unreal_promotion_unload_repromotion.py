"""Focused conformance checks for Integrated Unreal Promotion-Unload-Repromotion."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from kernel import canonical_json
from integrated_unreal_promotion_unload_repromotion import (
    ACTOR_ID,
    INPUT_ID,
    NO_EXECUTION_BOUNDARY,
    PHASE_ALPHA,
    REJECT_ACCEPTANCE_RECEIPT,
    REJECT_BOUNDARY_SOURCE,
    REJECT_INPUT_CONTRACT,
    REJECT_INPUT_DIGEST,
    REJECT_LOCAL_AUTHORITY,
    REJECT_RECEIPT,
    REJECT_RETURN_INPUT,
    CanonicalEnvelopeRejected,
    ExternalInputRejected,
    RepresentationRejected,
    admit_external_input_candidate,
    all_witness_runs,
    authoritative_projection,
    boundary_jump,
    canonical_hash,
    demote,
    dense_inspection,
    equivalence_oracle,
    external_evidence_q,
    initial_canonical_envelope,
    launch_receipt,
    materialization_acceptance_receipt,
    next_consequential_boundary,
    next_execution_boundary,
    promote,
    raw_payload_sha256,
    resolve_execution_boundary,
    runtime_fail_closed_results,
    source_audit,
    stored_payload_bytes,
    stored_receipt_bytes,
    validate_acceptance_receipt,
    validate_canonical_envelope,
    validate_launch_artifact,
    visible_input_audit,
    write_artifacts,
)
from integrated_unreal_lifecycle_harness import (
    Q_FILENAME,
    accept_q_and_prepare_return,
    capture_acceptance_receipt,
    export_witness_artifacts,
    prepare,
    record_source_termination,
    resolve_after_unload,
    resolve_control_after_unload,
    return_launch_command,
    source_launch_command,
)
from verify_integrated_unreal_promotion_unload_repromotion_release import canonical_source_audit


class IntegratedUnrealPromotionUnloadRepromotionTests(unittest.TestCase):
    def _primary(self) -> tuple[dict, dict, dict, dict]:
        r0 = initial_canonical_envelope()
        q = external_evidence_q(r0)
        bq = admit_external_input_candidate(r0, q)
        rinput = resolve_execution_boundary(r0, bq, q)
        alpha = next_execution_boundary(rinput, None)
        rfinal = resolve_execution_boundary(rinput, alpha)
        return r0, q, rinput, rfinal

    def test_exact_identity_and_all_four_records_validate(self) -> None:
        r0, _, rinput, rfinal = self._primary()
        control = resolve_execution_boundary(r0, next_consequential_boundary(r0))
        for record in (r0, rinput, rfinal, control):
            self.assertEqual(validate_canonical_envelope(record), [])
            self.assertNotIn("canonical_post_state_hash", canonical_json(record))
        self.assertEqual(r0["identity"]["simulation_version"], "0.7.0-draft.51")

    def test_payload_and_receipt_byte_identity_are_separate_and_exact(self) -> None:
        r0 = initial_canonical_envelope()
        payload = stored_payload_bytes(r0)
        receipt = stored_receipt_bytes(launch_receipt(r0))
        self.assertEqual(validate_launch_artifact(payload, receipt), r0)
        self.assertEqual(raw_payload_sha256(r0), launch_receipt(r0)["raw_payload_sha256"])
        altered = payload.replace(b"enabled", b"disabled", 1)
        with self.assertRaisesRegex(RepresentationRejected, REJECT_RECEIPT):
            validate_launch_artifact(altered, receipt)

    def test_q_is_exact_evidence_not_an_authoritative_command(self) -> None:
        r0 = initial_canonical_envelope()
        q = external_evidence_q(r0)
        self.assertEqual(q["input_id"], INPUT_ID)
        self.assertEqual(q["target"]["id"], ACTOR_ID)
        self.assertEqual(q["proposed_mutations"], ["current_causal_state.gate_token.state = disabled"])
        bq = admit_external_input_candidate(r0, q)
        self.assertEqual(bq["kind"], "external_input")
        self.assertEqual(bq["source_record_hash"], canonical_hash(r0))
        self.assertEqual(bq["simulation_phase"], 0)

    def test_digest_and_contract_rejections_are_distinct(self) -> None:
        r0 = initial_canonical_envelope()
        q = external_evidence_q(r0)
        altered = copy.deepcopy(q)
        altered["target"]["id"] = "redirected"
        with self.assertRaisesRegex(ExternalInputRejected, REJECT_INPUT_DIGEST):
            admit_external_input_candidate(r0, altered)
        redirected = copy.deepcopy(altered)
        from integrated_unreal_promotion_unload_repromotion import evidence_digest
        projection = copy.deepcopy(redirected)
        projection["evidence"].pop("evidence_digest")
        redirected["evidence"]["evidence_digest"] = evidence_digest(projection)
        with self.assertRaisesRegex(ExternalInputRejected, REJECT_INPUT_CONTRACT):
            admit_external_input_candidate(r0, redirected)

    def test_q_then_destruction_then_record_relative_alpha(self) -> None:
        r0, q, rinput, rfinal = self._primary()
        self.assertEqual(rinput["future_causal_state"]["canonical_clock"], "t0/30")
        self.assertEqual(rinput["current_causal_state"]["gate_token"]["state"], "disabled")
        self.assertEqual(rinput["current_causal_state"]["commitments"]["alpha"]["state"], "active")
        self.assertEqual(rinput["causal_provenance"]["accepted_external_inputs"], [INPUT_ID])
        alpha = next_execution_boundary(rinput, None)
        self.assertEqual(alpha["source_record_hash"], canonical_hash(rinput))
        self.assertEqual(alpha["simulation_phase"], PHASE_ALPHA)
        self.assertEqual(rfinal["current_causal_state"]["commitments"]["alpha"]["state"], "failed_gate")
        self.assertEqual(rfinal["current_causal_state"]["commitments"]["alpha"]["terminal_disposition"], "no_resource_acquired")
        self.assertEqual(rfinal["causal_provenance"]["authoritative_causal_ledger"][-1]["evaluated_gates"][0]["observed_value"], "disabled")
        self.assertEqual(next_execution_boundary(rfinal, None), NO_EXECUTION_BOUNDARY)
        self.assertNotEqual(canonical_hash(r0), canonical_hash(rinput))

    def test_r0_bound_capabilities_are_stale_after_rinput(self) -> None:
        r0, q, rinput, _ = self._primary()
        with self.assertRaisesRegex(CanonicalEnvelopeRejected, REJECT_BOUNDARY_SOURCE):
            resolve_execution_boundary(rinput, admit_external_input_candidate(r0, q), q)
        with self.assertRaisesRegex(CanonicalEnvelopeRejected, REJECT_BOUNDARY_SOURCE):
            resolve_execution_boundary(rinput, next_consequential_boundary(r0))

    def test_control_is_the_same_lifecycle_without_q(self) -> None:
        r0 = initial_canonical_envelope()
        control = resolve_execution_boundary(r0, next_execution_boundary(r0, None))
        self.assertEqual(control["current_causal_state"]["gate_token"]["state"], "enabled")
        self.assertEqual(control["current_causal_state"]["commitments"]["alpha"]["state"], "succeeded")
        self.assertEqual(control["causal_provenance"]["authoritative_causal_ledger"][-1]["evaluated_gates"][0]["observed_value"], "enabled")

    def test_materialization_acceptance_receipts_are_record_derived(self) -> None:
        r0, _, _, rfinal = self._primary()
        source = materialization_acceptance_receipt(r0, "source_process_01", True)
        returned = materialization_acceptance_receipt(rfinal, "return_process_01", False)
        validate_acceptance_receipt(r0, source, True)
        validate_acceptance_receipt(rfinal, returned, False)
        invalid = copy.deepcopy(returned)
        invalid["materialized_gate_state"] = "enabled"
        with self.assertRaisesRegex(RepresentationRejected, REJECT_ACCEPTANCE_RECEIPT):
            validate_acceptance_receipt(rfinal, invalid, False)

    def test_promotion_and_demotion_preserve_authority(self) -> None:
        r0 = initial_canonical_envelope()
        runtime = {"canonical_envelope": r0, "resolution_local_state": {"cache": {}, "samples": [], "profile": "minimal"}, "resolution_trace": []}
        dense = dense_inspection(runtime, "t0/15")
        promoted = promote(dense)
        demoted = demote(promoted)
        jumped = boundary_jump(demoted)
        for candidate in (dense, promoted, demoted, jumped):
            self.assertEqual(canonical_json(authoritative_projection(candidate)), canonical_json(r0))
        runtime["resolution_local_state"]["cache"]["canonical_mutation"] = True
        with self.assertRaisesRegex(RepresentationRejected, REJECT_LOCAL_AUTHORITY):
            boundary_jump(runtime)

    def test_return_input_isolation_requires_exactly_two_files_and_no_context(self) -> None:
        r0, _, _, rfinal = self._primary()
        with tempfile.TemporaryDirectory() as raw:
            domain = Path(raw)
            (domain / "canonical_payload_Rfinal.json").write_bytes(stored_payload_bytes(rfinal))
            (domain / "launch_receipt_Rfinal.json").write_bytes(stored_receipt_bytes(launch_receipt(rfinal)))
            audit = visible_input_audit(domain, ("canonical_payload_Rfinal.json", "launch_receipt_Rfinal.json"), None)
            self.assertEqual(len(audit["allowed_files"]), 2)
            (domain / "Q.json").write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(RepresentationRejected, REJECT_RETURN_INPUT):
                visible_input_audit(domain, ("canonical_payload_Rfinal.json", "launch_receipt_Rfinal.json"), None)

    def test_all_resolution_witnesses_match_at_shared_checkpoints(self) -> None:
        runs = all_witness_runs()
        self.assertEqual(equivalence_oracle(runs), {"result": "accepted", "reference_witness": "dense_reference", "failures": []})
        reference = runs["dense_reference"]
        for name in ("integrated_boundary_jump", "dense_demote_jump", "jump_promote_dense"):
            for checkpoint in ("R0", "Rinput", "Rfinal"):
                self.assertEqual(canonical_json(runs[name]["checkpoints"][checkpoint]), canonical_json(reference["checkpoints"][checkpoint]))
        self.assertNotEqual(reference["diagnostic_resolution_trace"], runs["integrated_boundary_jump"]["diagnostic_resolution_trace"])

    def test_runtime_rejections_are_pre_mutation(self) -> None:
        failures = runtime_fail_closed_results()
        self.assertEqual(set(failures), {"digest_changed_without_recompute", "redirected_with_recomputed_digest", "stale_bq", "stale_alpha", "local_authority"})
        self.assertTrue(all(value["canonical_unchanged"] for value in failures.values()))

    def test_artifact_regeneration_and_source_audit(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw)
            write_artifacts(output)
            self.assertTrue((output / "integrated_unreal_R0.json").is_file())
            self.assertTrue((output / "launch_receipt_Rfinal.json").is_file())
            self.assertTrue((output / "integrated_unreal_integrated_boundary_jump_run.json").is_file())
        audit = source_audit()
        self.assertTrue(audit["passed"])
        self.assertEqual(audit["resolver_functions"], ["resolve_execution_boundary"])
        self.assertFalse(audit["resolver_reads_representation_or_lifecycle_state"])
        self.assertFalse(audit["random_module_imported"])
        self.assertTrue(all(canonical_source_audit().values()))

    def test_lifecycle_harness_removes_source_domains_before_return(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "primary"
            prepare(root)
            self.assertIn("-IntegratedProofInteractionOpportunity=t0/30", source_launch_command(root))
            r0 = initial_canonical_envelope()
            (root / "source_output" / Q_FILENAME).write_text(canonical_json(external_evidence_q(r0)) + "\n", encoding="utf-8")
            accepted = accept_q_and_prepare_return(root)
            self.assertEqual(accepted["rinput"]["current_causal_state"]["gate_token"]["state"], "disabled")
            record_source_termination(root, 999999)
            continued = resolve_after_unload(root)
            self.assertEqual(continued["rfinal"]["current_causal_state"]["commitments"]["alpha"]["state"], "failed_gate")
            self.assertFalse((root / "source_input").exists())
            self.assertFalse((root / "source_output").exists())
            self.assertEqual(len(continued["return_input_audit"]["allowed_files"]), 2)
            command = return_launch_command(root)
            self.assertFalse(any("IntegratedProofOutput=" in value or "InteractionOpportunity=" in value for value in command))

    def test_control_harness_uses_the_same_destroy_then_return_order(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "control"
            prepare(root)
            self.assertIn("-IntegratedProofProcessInstanceId=control_source_process_01", source_launch_command(root, True))
            record_source_termination(root, 999999)
            control = resolve_control_after_unload(root)
            self.assertEqual(control["rcontrol"]["current_causal_state"]["commitments"]["alpha"]["state"], "succeeded")
            self.assertFalse((root / "source_input").exists())
            self.assertFalse((root / "source_output").exists())
            self.assertTrue(any("Rcontrol" in value for value in return_launch_command(root, True)))

    def test_control_harness_rejects_any_source_q_before_continuation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "control_with_stray_q"
            prepare(root)
            (root / "source_output" / Q_FILENAME).write_text(canonical_json(external_evidence_q(initial_canonical_envelope())) + "\n", encoding="utf-8")
            record_source_termination(root, 999999)
            with self.assertRaisesRegex(ValueError, "Q-absent control source output must be empty"):
                resolve_control_after_unload(root)

    def test_harness_captures_one_valid_structured_source_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "receipt_capture"
            prepare(root)
            r0 = initial_canonical_envelope()
            receipt = materialization_acceptance_receipt(r0, "source_process_01", True)
            (root / "process_output" / "source_process_01.log").write_text(
                "ordinary UE output\nINTEGRATED_MATERIALIZATION_RECEIPT:" + canonical_json(receipt) + "\n",
                encoding="utf-8",
            )
            self.assertEqual(capture_acceptance_receipt(root, "source"), receipt)
            self.assertEqual(
                json.loads((root / "evidence" / "primary_source_acceptance_receipt.json").read_text(encoding="utf-8")),
                receipt,
            )

    def test_export_requires_two_complete_clean_lifecycle_witnesses(self) -> None:
        def write_receipt_log(root: Path, process_id: str, record: dict, proposal_capability_enabled: bool) -> None:
            receipt = materialization_acceptance_receipt(record, process_id, proposal_capability_enabled)
            (root / "process_output" / f"{process_id}.log").write_text(
                "INTEGRATED_MATERIALIZATION_RECEIPT:" + canonical_json(receipt) + "\n",
                encoding="utf-8",
            )

        with tempfile.TemporaryDirectory() as raw:
            primary = Path(raw) / "primary"
            control = Path(raw) / "control"
            output = Path(raw) / "export"
            r0 = initial_canonical_envelope()

            prepare(primary)
            write_receipt_log(primary, "source_process_01", r0, True)
            capture_acceptance_receipt(primary, "source")
            (primary / "source_output" / Q_FILENAME).write_text(canonical_json(external_evidence_q(r0)) + "\n", encoding="utf-8")
            accept_q_and_prepare_return(primary)
            record_source_termination(primary, 999999)
            continued = resolve_after_unload(primary)
            write_receipt_log(primary, "return_process_01", continued["rfinal"], False)
            capture_acceptance_receipt(primary, "return")

            prepare(control)
            write_receipt_log(control, "control_source_process_01", r0, True)
            capture_acceptance_receipt(control, "source", control=True)
            record_source_termination(control, 999999)
            controlled = resolve_control_after_unload(control)
            write_receipt_log(control, "control_return_process_01", controlled["rcontrol"], False)
            capture_acceptance_receipt(control, "return", control=True)

            summary = export_witness_artifacts(primary, control, output)
            self.assertTrue(summary["primary"]["source_domains_removed_before_rediscovery"])
            self.assertTrue(summary["control"]["source_output_empty_before_continuation"])
            self.assertTrue((output / "physical_primary_Q.json").is_file())
            self.assertTrue((output / "physical_control_Rcontrol.json").is_file())


if __name__ == "__main__":
    unittest.main()
