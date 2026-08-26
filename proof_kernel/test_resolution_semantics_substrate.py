"""Regression tests for the frozen canonical-only resolution substrate proof."""

from __future__ import annotations

import copy
import inspect
import unittest

from kernel import canonical_json
from resolution_semantics_substrate import (
    COMMITMENT_ID,
    DECISION_TIME,
    DUE_WORK_ID,
    PAYLOAD_SCHEMA,
    REJECTION_AUTHORITATIVE_LOSS,
    REJECTION_AUTHORITATIVE_MUTATION,
    REJECTION_BOUNDARY_MISMATCH,
    CanonicalEnvelopeRejected,
    assess_boundary_policy,
    assess_demotion_transition,
    assess_promotion_transition,
    authoritative_projection,
    canonical_hash,
    demote,
    initial_canonical_envelope,
    minimal_runtime,
    next_consequential_boundary,
    proof_run,
    promote,
    source_audit,
    validate_canonical_envelope,
)


EXPECTED_BOUNDARY = {"decision_time": DECISION_TIME, "due_work_ids": [DUE_WORK_ID]}


class ResolutionSemanticsSubstrateTests(unittest.TestCase):
    def test_exact_singular_canonical_envelope_is_valid_and_hashed(self) -> None:
        r0 = initial_canonical_envelope()
        self.assertEqual(set(r0), {"identity", "current_causal_state", "future_causal_state", "causal_provenance"})
        self.assertNotIn("canonical_envelope", r0)
        self.assertEqual(r0["identity"]["payload_schema"], PAYLOAD_SCHEMA)
        self.assertEqual(validate_canonical_envelope(r0), [])
        self.assertEqual(canonical_hash(r0), canonical_hash(copy.deepcopy(r0)))

    def test_exact_payload_rejects_unknown_missing_and_incompatible_authoritative_paths(self) -> None:
        unknown = initial_canonical_envelope()
        unknown["current_causal_state"]["durable_facts"]["illegal_marker"] = "unexpected"
        self.assertIn("canonical_envelope.current_causal_state.durable_facts.illegal_marker.unknown", validate_canonical_envelope(unknown))

        missing = initial_canonical_envelope()
        del missing["causal_provenance"]["fixture_genesis"]
        self.assertIn("canonical_envelope.causal_provenance.fixture_genesis.missing", validate_canonical_envelope(missing))

        incompatible = initial_canonical_envelope()
        incompatible["future_causal_state"]["canonical_clock"] = 0
        self.assertIn("canonical_envelope.future_causal_state.canonical_clock.type", validate_canonical_envelope(incompatible))

    def test_scheduler_rejects_every_redundant_authoritative_disagreement(self) -> None:
        fixtures: list[tuple[str, tuple[object, ...], object]] = [
            ("commitment_schedule", ("current_causal_state", "active_commitments", COMMITMENT_ID, "gate_check_at"), "t9/00"),
            ("execution_keys", ("future_causal_state", "canonical_execution_keys"), ["t1/00/substrate/wrong"]),
            ("reservation", ("current_causal_state", "resource_ownership", "unit_alpha", "reservation_id"), "wrong_reservation"),
            ("marker", ("current_causal_state", "gate_relevant_state", "substrate_marker"), "unstable"),
            ("required_gate", ("current_causal_state", "active_commitments", COMMITMENT_ID, "required_gate"), "absent_fact == stable"),
            ("genesis", ("causal_provenance", "fixture_genesis", "resources"), ["unit_alpha has no explanation"]),
        ]
        for name, path, replacement in fixtures:
            with self.subTest(name=name):
                r0 = initial_canonical_envelope()
                target = r0
                for part in path[:-1]:
                    target = target[part]  # type: ignore[index]
                target[path[-1]] = replacement  # type: ignore[index]
                with self.assertRaises(CanonicalEnvelopeRejected):
                    next_consequential_boundary(r0)

    def test_boundary_identity_is_identical_across_minimal_promoted_and_demoted_runtime(self) -> None:
        r0 = initial_canonical_envelope()
        minimal = minimal_runtime(r0)
        promoted = promote(r0)
        demoted = demote(promoted)
        self.assertEqual(next_consequential_boundary(r0), EXPECTED_BOUNDARY)
        for runtime in (minimal, promoted, demoted):
            self.assertEqual(next_consequential_boundary(authoritative_projection(runtime)), EXPECTED_BOUNDARY)
        with self.assertRaises(CanonicalEnvelopeRejected):
            next_consequential_boundary(promoted)  # type: ignore[arg-type]

    def test_promotion_preserves_authoritative_projection_hash_and_derives_only_local_state(self) -> None:
        r0 = initial_canonical_envelope()
        before = copy.deepcopy(r0)
        promoted = promote(r0)
        self.assertEqual(r0, before)
        self.assertEqual(canonical_json(authoritative_projection(promoted)), canonical_json(r0))
        self.assertEqual(canonical_hash(authoritative_projection(promoted)), canonical_hash(r0))
        self.assertEqual(
            promoted["resolution_local_state"],
            {
                "profile": "promoted",
                "cache": {COMMITMENT_ID: {"next_gate_display": DECISION_TIME, "reservation_display": "reservation_alpha"}},
                "samples": ["t0/00"],
                "diagnostics": ["promotion_derived_from_canonical_envelope"],
            },
        )
        self.assertEqual(assess_promotion_transition(r0, promoted)["result"], "accepted")

    def test_demotion_preserves_authority_and_discards_local_cache(self) -> None:
        r0 = initial_canonical_envelope()
        demoted = demote(promote(r0))
        self.assertEqual(canonical_json(authoritative_projection(demoted)), canonical_json(r0))
        self.assertEqual(canonical_hash(authoritative_projection(demoted)), canonical_hash(r0))
        self.assertEqual(
            demoted["resolution_local_state"],
            {"profile": "demoted", "cache": {}, "samples": [], "diagnostics": ["local_state_discarded"]},
        )
        self.assertEqual(assess_demotion_transition(r0, demoted)["result"], "accepted")

    def test_promote_demote_promote_regenerates_local_cache_without_hidden_authority(self) -> None:
        r0 = initial_canonical_envelope()
        first = promote(r0)
        first["resolution_local_state"]["cache"][COMMITMENT_ID]["next_gate_display"] = "corrupted_local_value"
        demoted = demote(first)
        second = promote(authoritative_projection(demoted))
        self.assertEqual(canonical_json(authoritative_projection(second)), canonical_json(r0))
        self.assertEqual(second["resolution_local_state"]["cache"][COMMITMENT_ID]["next_gate_display"], DECISION_TIME)

    def test_promotion_authority_creation_rejects_without_canonical_side_effect(self) -> None:
        r0 = initial_canonical_envelope()
        before = copy.deepcopy(r0)
        malformed = promote(r0)
        malformed["canonical_envelope"]["current_causal_state"]["durable_facts"]["illegal_marker"] = "created"
        result = assess_promotion_transition(r0, malformed)
        self.assertEqual(result["disposition"], REJECTION_AUTHORITATIVE_MUTATION)
        self.assertFalse(result["authoritative_causal_ledger_appended"])
        self.assertFalse(result["future_schedule_created"])
        self.assertEqual(r0, before)

    def test_demotion_authority_loss_rejects_for_every_frozen_loss_class(self) -> None:
        paths = (
            ("current_causal_state", "resource_ownership", "unit_alpha"),
            ("future_causal_state", "scheduled_consequential_decisions"),
            ("causal_provenance", "canonical_ancestry"),
            ("causal_provenance", "terminal_resource_dispositions", "reservation_alpha"),
        )
        r0 = initial_canonical_envelope()
        for path in paths:
            with self.subTest(path=path):
                malformed = promote(r0)
                target = malformed["canonical_envelope"]
                for part in path[:-1]:
                    target = target[part]
                del target[path[-1]]
                result = assess_demotion_transition(r0, malformed)
                self.assertEqual(result["disposition"], REJECTION_AUTHORITATIVE_LOSS)
                self.assertFalse(result["authoritative_causal_ledger_appended"])
                self.assertFalse(result["future_schedule_created"])

    def test_local_policy_boundary_override_rejects_without_canonical_side_effect(self) -> None:
        r0 = initial_canonical_envelope()
        proposals = (
            {"decision_time": "t2/00", "due_work_ids": [DUE_WORK_ID]},
            {"decision_time": DECISION_TIME, "due_work_ids": []},
            {"decision_time": DECISION_TIME, "due_work_ids": [DUE_WORK_ID, "t1/00/substrate/extra"]},
        )
        for proposal in proposals:
            result = assess_boundary_policy(r0, proposal)
            self.assertEqual(result["disposition"], REJECTION_BOUNDARY_MISMATCH)
            self.assertFalse(result["authoritative_causal_ledger_appended"])
            self.assertFalse(result["future_schedule_created"])

    def test_each_proof_run_replays_byte_identically(self) -> None:
        self.assertEqual(canonical_json(proof_run()), canonical_json(proof_run()))

    def test_source_audit_keeps_canonical_and_resolution_local_authority_separate(self) -> None:
        audit = source_audit()
        self.assertEqual(audit["scheduler_functions"], ["next_consequential_boundary"])
        self.assertEqual(audit["scheduler_parameter"], "canonical_envelope")
        self.assertFalse(audit["scheduler_reads_resolution_local_state"])
        self.assertFalse(audit["transforms_write_canonical_paths"])
        self.assertFalse(audit["scheduler_or_resolver_reads_resolution_trace"])
        self.assertFalse(audit["policy_can_override_boundary"])
        self.assertFalse(audit["expected_result_shortcut_present"])
        self.assertFalse(audit["transform_mutates_commitment_resource_or_ledger"])
        self.assertTrue(audit["payload_validation_uses_exact_schema"])
        self.assertEqual(audit["authoritative_randomness"], "none")
        self.assertFalse(audit["random_module_imported"])
        self.assertFalse(audit["resolution_execution_modes_implemented"])
        source = inspect.getsource(next_consequential_boundary)
        self.assertNotIn("resolution_local_state", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
