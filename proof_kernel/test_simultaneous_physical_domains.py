from __future__ import annotations

import copy
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

from simultaneous_physical_domains import (
    ACCESS_STATES,
    ARTIFACT_NAMES,
    D0,
    D1,
    DOMAIN_ROLES,
    GUARD_STATES,
    H0,
    H1,
    HEAD_OBSERVATION_FAULT_POINTS,
    PHYSICAL_OBSERVATION_FAULT_STAGES,
    PROJECTION_ROWS,
    REFRESH_FAULT_STAGES,
    RETAINED_SCHEMA,
    PhysicalDomainRejected,
    artifact_role_set_valid,
    authoritative_representation,
    bind_invocation,
    canonical_json,
    canonical_records,
    canonical_transition_run,
    current_head_authority_failures,
    current_head_observation,
    expected_physical_observation,
    guard_open_control,
    head_disposition,
    head_observation_failure_witness,
    head_observation_fault_atomicity,
    inspection_invocation,
    materialization_receipt,
    operation_receipt,
    operation_receipt_matrix,
    operational_process_instance_id,
    physical_observation_fault_atomicity,
    probe_tag,
    process_binding,
    projection,
    projection_matrix,
    proof_semantic_input_audit_template,
    refresh_fault_atomicity,
    refresh_invocation,
    retention_equivalence_oracle,
    retention_witness,
    semantic_replay_projection,
    sha256_bytes,
    sha256_value,
    stale_quarantine_witness,
    stored_json_bytes,
    strict_load_stored_json,
    validate_exact_directory,
    validate_materialization_receipt,
    validate_physical_observation,
    validate_projection,
    validate_retained_local_state,
    validate_visible_tuple,
    verify_current_head_observation,
)
from canonical_spatial_topology_identity import stored_json_bytes as phase1_bytes


class SimultaneousPhysicalDomainsTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.r0, self.boundary, self.r1 = canonical_records()
        self.binding_a = self._binding("domain_A")
        self.binding_b = self._binding("domain_B", pid=4243)

    @staticmethod
    def _binding(role: str, *, pid: int = 4242) -> dict:
        witness = "w1_a_then_b"
        return process_binding({
            "proof_scenario": "simultaneous-physical-domains-v1",
            "witness_id": witness,
            "domain_role": role,
            "harness_launch_id": f"{witness}/{role}/launch_0001",
            "pid": pid,
            "macos_process_start": {"seconds": 100, "microseconds": pid},
            "executable_realpath": "/exact/UnrealEditor",
            "executable_raw_sha256": "1" * 64,
            "unreal_engine_build_identity": "5.8.0-test",
            "entry_map_package_identity": "/Engine/Maps/Entry",
            "project_realpath": "/exact/CityMaterializationProof.uproject",
            "project_raw_sha256": "2" * 64,
            "project_config_and_module_inventory_raw_sha256": "3" * 64,
            "process_root_realpath": f"/private/exact/{role}",
            "launch_argv_raw_sha256": "4" * 64,
            "launch_environment_audit_raw_sha256": "5" * 64,
            "launch_cwd_realpath": "/exact/repository",
            "inherited_descriptor_map_raw_sha256": "6" * 64,
            "control_pipe_id": f"{role}/control/0001",
            "structured_output_pipe_id": f"{role}/stdout/0001",
            "diagnostic_pipe_id": f"{role}/stderr/0001",
        })

    def _bundle(self, role: str, head: str, operation: str, binding: dict | None = None):
        payload = self.r0 if head == "H0" else self.r1
        p = projection(role, head)
        identity = operational_process_instance_id(binding) if binding is not None else None
        receipt = operation_receipt(operation, role, head, operational_process_instance_id=identity)
        return phase1_bytes(payload), stored_json_bytes(p), stored_json_bytes(receipt)

    def test_01_exact_sealed_phase1_transition_reused(self) -> None:
        self.assertEqual(sha256_bytes(phase1_bytes(self.r0)), D0)
        self.assertEqual(sha256_bytes(phase1_bytes(self.r1)), D1)
        self.assertEqual(canonical_transition_run()["source_record_hash"], H0)
        self.assertEqual(canonical_transition_run()["successor_record_hash"], H1)
        self.assertFalse(canonical_transition_run()["physical_guard_input_to_resolver"])

    def test_02_strict_json_duplicate_and_noncanonical_rejection(self) -> None:
        value = {"a": 1, "b": [2]}
        self.assertEqual(strict_load_stored_json(stored_json_bytes(value)), value)
        with self.assertRaises(PhysicalDomainRejected):
            strict_load_stored_json(b'{"a":1,"a":2}\n')
        with self.assertRaises(PhysicalDomainRejected):
            strict_load_stored_json(b'{"b":2,"a":1}\n')

    def test_03_projection_matrix_is_exact_four_rows(self) -> None:
        matrix = projection_matrix()
        self.assertEqual(len(matrix["rows"]), 4)
        self.assertEqual({(row["domain_role"], row["source_canonical_hash"]) for row in matrix["rows"]}, {
            ("domain_A", H0), ("domain_A", H1), ("domain_B", H0), ("domain_B", H1)
        })
        for row in matrix["rows"]:
            self.assertEqual(row["allowed_route_projection"]["canonical_route_id"], "topology_route_0001")
            self.assertNotIn("access", canonical_json(row))

    def test_04_cross_row_projection_rejects(self) -> None:
        with self.assertRaises(PhysicalDomainRejected):
            validate_projection(projection("domain_A", "H0"), "domain_B", "H0")
        altered = projection("domain_A", "H1")
        altered["allowed_route_projection"]["canonical_route_id"] = "wrong"
        with self.assertRaises(PhysicalDomainRejected):
            validate_projection(altered, "domain_A", "H1")

    def test_05_operation_receipts_bind_exact_tuple(self) -> None:
        matrix = operation_receipt_matrix()
        self.assertEqual(len(matrix["launch_rows"]), 2)
        self.assertEqual(len(matrix["refresh_templates"]), 2)
        with self.assertRaises(PhysicalDomainRejected):
            operation_receipt("launch", "domain_A", "H1")
        with self.assertRaises(PhysicalDomainRejected):
            operation_receipt("refresh", "domain_A", "H1", operational_process_instance_id=None)

    def test_06_exact_launch_visible_tuple_validates(self) -> None:
        raw = self._bundle("domain_A", "H0", "launch")
        payload, p, receipt, head = validate_visible_tuple(
            *raw, operation="launch", domain_role="domain_A", operational_process_instance_id=None
        )
        self.assertEqual(head, "H0")
        self.assertEqual(payload, self.r0)
        self.assertEqual(p, projection("domain_A", "H0"))
        self.assertEqual(receipt["expected_target_represented_hash"], H0)

    def test_07_exact_refresh_visible_tuple_validates(self) -> None:
        instance = operational_process_instance_id(self.binding_a)
        raw = self._bundle("domain_A", "H1", "refresh", self.binding_a)
        _, _, receipt, head = validate_visible_tuple(
            *raw, operation="refresh", domain_role="domain_A", operational_process_instance_id=instance
        )
        self.assertEqual(head, "H1")
        self.assertEqual(receipt["expected_source_represented_hash"], H0)

    def test_08_refresh_payload_digest_mismatch_rejects_before_parse(self) -> None:
        payload, p, receipt = self._bundle("domain_A", "H1", "refresh", self.binding_a)
        malformed = payload.replace(b'"blocked"', b'"available"')
        with self.assertRaises(PhysicalDomainRejected) as caught:
            validate_visible_tuple(
                malformed, p, receipt, operation="refresh", domain_role="domain_A",
                operational_process_instance_id=operational_process_instance_id(self.binding_a),
            )
        self.assertEqual(caught.exception.stage, "payload_raw_byte_verification")

    def test_09_operation_receipt_payload_digest_mismatch_rejects(self) -> None:
        payload, p, receipt_raw = self._bundle("domain_B", "H1", "refresh", self.binding_b)
        receipt = strict_load_stored_json(receipt_raw)
        receipt["canonical_payload_raw_sha256"] = D0
        with self.assertRaises(PhysicalDomainRejected) as caught:
            validate_visible_tuple(
                payload, p, stored_json_bytes(receipt), operation="refresh", domain_role="domain_B",
                operational_process_instance_id=operational_process_instance_id(self.binding_b),
            )
        self.assertEqual(caught.exception.stage, "operation_receipt_verification")

    def test_10_authoritative_projection_rederives_access_and_endpoints(self) -> None:
        for role in DOMAIN_ROLES:
            h0 = authoritative_representation(self.r0, projection(role, "H0"))
            h1 = authoritative_representation(self.r1, projection(role, "H1"))
            self.assertEqual(h0["materialized_route_access_state"], "available")
            self.assertEqual(h1["materialized_route_access_state"], "blocked")
            self.assertEqual(h1["materialized_endpoint_site_ids"], ["topology_site_0001", "topology_site_0002"])

    def test_11_authoritative_constructor_has_exact_two_semantic_inputs(self) -> None:
        h1a = authoritative_representation(self.r1, projection("domain_A", "H1"))
        h1b = authoritative_representation(self.r1, projection("domain_B", "H1"))
        self.assertEqual(set(h1a), set(h1b))
        self.assertNotIn("retained", canonical_json(h1a))
        self.assertNotIn("actor", canonical_json(h1a).lower())
        self.assertNotIn("current_head", canonical_json(h1a))

    def test_12_retained_state_exact_and_bounded(self) -> None:
        baseline = retention_witness(perturbed=False)["retained_local_state"]
        self.assertEqual(validate_retained_local_state(baseline), baseline)
        invalid = copy.deepcopy(baseline)
        invalid["canonical_hash"] = H0
        with self.assertRaises(PhysicalDomainRejected):
            validate_retained_local_state(invalid)
        invalid = copy.deepcopy(baseline)
        invalid["nonconsequential_tick_counter"] = -1
        with self.assertRaises(PhysicalDomainRejected):
            validate_retained_local_state(invalid)

    def test_13_retention_perturbation_cannot_select_H1_projection(self) -> None:
        oracle = retention_equivalence_oracle()
        self.assertTrue(oracle["retained_local_state_differs"])
        self.assertTrue(oracle["authoritative_derived_H1_byte_identical"])
        self.assertTrue(oracle["poison_discarded"])

    def test_14_process_binding_and_instance_identity_are_exact(self) -> None:
        self.assertEqual(len(operational_process_instance_id(self.binding_a)), 64)
        invocation = bind_invocation(self.binding_a)
        self.assertEqual(invocation["process_binding"], self.binding_a)
        self.assertEqual(invocation["operational_process_instance_id"], operational_process_instance_id(self.binding_a))
        altered = copy.deepcopy(self.binding_a)
        altered["harness_launch_id"] = "wrong"
        without_schema = {key: value for key, value in altered.items() if key != "binding_schema"}
        with self.assertRaises(PhysicalDomainRejected):
            process_binding(without_schema)

    def test_15_materialization_receipt_is_representation_only(self) -> None:
        representation = authoritative_representation(self.r0, projection("domain_A", "H0"))
        receipt = materialization_receipt(
            representation,
            operational_process_instance_id=operational_process_instance_id(self.binding_a),
            process_binding_raw_sha256=sha256_value(self.binding_a),
        )
        validate_materialization_receipt(receipt, self.binding_a)
        self.assertEqual(receipt["receipt_authority"], "representation_only")
        for forbidden in ("current_head", "head_state", "guard", "scheduling", "mutation"):
            self.assertNotIn(forbidden, canonical_json(receipt))

    def test_16_receipt_repeated_field_or_digest_mismatch_rejects(self) -> None:
        representation = authoritative_representation(self.r1, projection("domain_A", "H1"))
        receipt = materialization_receipt(
            representation,
            operational_process_instance_id=operational_process_instance_id(self.binding_a),
            process_binding_raw_sha256=sha256_value(self.binding_a),
        )
        receipt["materialized_route_access_state"] = "available"
        with self.assertRaises(PhysicalDomainRejected):
            validate_materialization_receipt(receipt, self.binding_a)

    def test_17_inspection_command_contains_no_expected_result(self) -> None:
        invocation = inspection_invocation("domain_A", "launch_physical_0001")
        self.assertEqual(set(invocation), {"command_schema", "proof_scenario", "domain_role", "operation", "inspection_id"})
        serialized = canonical_json(invocation)
        for forbidden in (H0, H1, "available", "blocked", "color", "label", "receipt"):
            self.assertNotIn(forbidden, serialized)

    def test_18_refresh_invocation_is_exact_and_head_observation_free(self) -> None:
        invocation = refresh_invocation("domain_B")
        self.assertEqual(set(invocation), {"command_schema", "proof_scenario", "domain_role", "operation", "refresh_id", "target_canonical_hash"})
        self.assertNotIn("guard", canonical_json(invocation))
        self.assertNotIn("observation", canonical_json(invocation))
        self.assertNotIn("path", canonical_json(invocation))

    def test_19_independent_physical_surfaces_are_exact(self) -> None:
        for role, binding in (("domain_A", self.binding_a), ("domain_B", self.binding_b)):
            for head, inspection in (("H0", "launch_physical_0001"), ("H1", "refresh_physical_0001")):
                observation = expected_physical_observation(
                    role, head,
                    operational_process_instance_id=operational_process_instance_id(binding),
                    process_binding_raw_sha256=sha256_value(binding),
                    inspection_id=inspection,
                )
                validate_physical_observation(
                    observation, domain_role=role, head_role=head, binding=binding, inspection_id=inspection
                )
                self.assertEqual(observation["observed_physical_access_state"], ACCESS_STATES[head])

    def test_20_available_receipt_with_blocked_oracle_disagrees(self) -> None:
        observation = expected_physical_observation(
            "domain_A", "H0",
            operational_process_instance_id=operational_process_instance_id(self.binding_a),
            process_binding_raw_sha256=sha256_value(self.binding_a),
            inspection_id="launch_physical_0001",
        )
        observation["observed_access_label_text"] = "BLOCKED"
        with self.assertRaises(PhysicalDomainRejected):
            validate_physical_observation(
                observation, domain_role="domain_A", head_role="H0", binding=self.binding_a,
                inspection_id="launch_physical_0001",
            )

    def test_21_current_head_observer_is_exact_committed_R1_only(self) -> None:
        observation = current_head_observation()
        self.assertEqual(verify_current_head_observation(observation, phase1_bytes(self.r1)), observation)
        with self.assertRaises(PhysicalDomainRejected):
            verify_current_head_observation(observation, phase1_bytes(self.r0))

    def test_22_synchronized_disposition_requires_receipt_oracle_and_guard(self) -> None:
        representation = authoritative_representation(self.r0, projection("domain_A", "H0"))
        receipt = materialization_receipt(
            representation,
            operational_process_instance_id=operational_process_instance_id(self.binding_a),
            process_binding_raw_sha256=sha256_value(self.binding_a),
        )
        observation = expected_physical_observation(
            "domain_A", "H0",
            operational_process_instance_id=operational_process_instance_id(self.binding_a),
            process_binding_raw_sha256=sha256_value(self.binding_a),
            inspection_id="launch_physical_0001",
        )
        disposition = head_disposition(
            domain_role="domain_A", binding=self.binding_a, receipt=receipt,
            physical_observation=observation, represented_hash=H0, observed_head=H0,
            guard_state="open_for_H0", head_state="synchronized",
        )
        self.assertTrue(disposition["current_head_claim_enabled"])
        self.assertFalse(disposition["canonical_evidence_enabled"])
        with self.assertRaises(PhysicalDomainRejected):
            head_disposition(
                domain_role="domain_A", binding=self.binding_a, receipt=receipt,
                physical_observation=None, represented_hash=H0, observed_head=H0,
                guard_state="open_for_H0", head_state="synchronized",
            )

    def test_23_stale_disposition_is_only_exact_refresh_eligible_state(self) -> None:
        stale = head_disposition(
            domain_role="domain_A", binding=self.binding_a, receipt=None, physical_observation=None,
            represented_hash=H0, observed_head=H1, guard_state="open_for_H1", head_state="stale",
        )
        self.assertTrue(stale["refresh_enabled"])
        self.assertFalse(stale["current_head_claim_enabled"])
        unconfirmed = head_disposition(
            domain_role="domain_A", binding=self.binding_a, receipt=None, physical_observation=None,
            represented_hash=H0, observed_head=None, guard_state="failed_closed", head_state="head_unconfirmed",
        )
        self.assertFalse(unconfirmed["refresh_enabled"])

    def test_24_guard_open_control_commits_exact_R1_and_fails_physical_protocol(self) -> None:
        witness = guard_open_control()
        self.assertTrue(witness["canonical_R1_byte_identical"])
        self.assertEqual(witness["guard_after_commit_verification"], "failed_closed")
        self.assertEqual(witness["domain_A_terminal_head_state"], "protocol_invalid")
        self.assertFalse(witness["phase_3_harness_protocol_passed"])

    def test_25_head_observation_fault_matrix_is_exact_nine_and_fail_closed(self) -> None:
        oracle = head_observation_fault_atomicity()
        self.assertEqual(tuple(oracle["fault_points"]), HEAD_OBSERVATION_FAULT_POINTS)
        self.assertEqual(len(oracle["cases"]), 9)
        self.assertTrue(all(case["guard_terminal_state"] == "failed_closed" for case in oracle["cases"]))
        self.assertTrue(all(case["canonical_H1"] == H1 for case in oracle["cases"]))

    def test_26_refresh_fault_matrix_has_exact_pre_post_surface(self) -> None:
        oracle = refresh_fault_atomicity()
        self.assertEqual(tuple(oracle["fault_stages"]), REFRESH_FAULT_STAGES)
        self.assertEqual(len(oracle["cases"]), 2 * len(REFRESH_FAULT_STAGES))
        self.assertTrue(all(not case["H1_materialization_receipt_accepted"] for case in oracle["cases"]))
        self.assertTrue(all(case["canonical_H1_unchanged"] for case in oracle["cases"]))

    def test_27_physical_observation_fault_matrix_is_exact(self) -> None:
        oracle = physical_observation_fault_atomicity()
        self.assertEqual(tuple(oracle["fault_stages"]), PHYSICAL_OBSERVATION_FAULT_STAGES)
        self.assertEqual(len(oracle["cases"]), len(PHYSICAL_OBSERVATION_FAULT_STAGES))
        self.assertTrue(all(case["H1_result"] == "invalid_and_halted" for case in oracle["cases"]))

    def test_28_stale_and_head_failure_witnesses_keep_H1(self) -> None:
        stale = stale_quarantine_witness()
        failure = head_observation_failure_witness()
        self.assertEqual(stale["canonical_R1_raw_sha256_before"], stale["canonical_R1_raw_sha256_after"])
        self.assertEqual(failure["canonical_R1_raw_sha256"], D1)
        self.assertEqual(failure["refresh_invocations"], 0)

    def test_29_all_37_current_head_authority_cases_reject(self) -> None:
        oracle = current_head_authority_failures()
        self.assertEqual(oracle["case_count"], 37)
        self.assertEqual([case["case_id"] for case in oracle["cases"]], list(range(1, 38)))
        self.assertTrue(all(case["rejected"] and not case["canonical_authority_acquired"] for case in oracle["cases"]))

    def test_30_exact_directory_inventory_rejects_links_extras_and_hardlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            names = ("a.json", "b.json", "c.json")
            for name in names:
                (root / name).write_bytes(b"{}\n")
            inventory = validate_exact_directory(root, names)
            self.assertEqual([item["filename"] for item in inventory["files"]], list(names))
            (root / "extra").write_bytes(b"x")
            with self.assertRaises(PhysicalDomainRejected):
                validate_exact_directory(root, names)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            names = ("a.json", "b.json", "c.json")
            (root / "a.json").write_bytes(b"{}\n")
            (root / "b.json").symlink_to(root / "a.json")
            (root / "c.json").write_bytes(b"{}\n")
            with self.assertRaises(PhysicalDomainRejected):
                validate_exact_directory(root, names)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            names = ("a.json", "b.json", "c.json")
            (root / "a.json").write_bytes(b"{}\n")
            os.link(root / "a.json", root / "b.json")
            (root / "c.json").write_bytes(b"{}\n")
            with self.assertRaises(PhysicalDomainRejected):
                validate_exact_directory(root, names)

    def test_31_proof_semantic_closure_has_no_hidden_head_input(self) -> None:
        audit = proof_semantic_input_audit_template()
        self.assertEqual(audit["semantic_environment_keys"], [])
        self.assertEqual(audit["semantic_command_line_selectors"], [])
        self.assertFalse(audit["head_observation_visible_to_unreal"])
        self.assertFalse(audit["physical_guard_visible_to_unreal"])
        self.assertEqual(audit["alternate_refresh_channels"], [])

    def test_32_exact_artifact_member_set_is_44_unique(self) -> None:
        self.assertEqual(len(ARTIFACT_NAMES), 44)
        self.assertEqual(len(set(ARTIFACT_NAMES)), 44)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ARTIFACT_NAMES:
                (root / name).write_bytes(b"{}\n")
            self.assertTrue(artifact_role_set_valid(root))
            (root / "extra.json").write_bytes(b"{}\n")
            self.assertFalse(artifact_role_set_valid(root))

    def test_33_semantic_replay_removes_only_operational_identity(self) -> None:
        left = {"canonical": H1, "pid": 1, "nested": {"process_start": {"seconds": 1}}}
        right = {"canonical": H1, "pid": 2, "nested": {"process_start": {"seconds": 2}}}
        self.assertEqual(semantic_replay_projection(left), semantic_replay_projection(right))
        right["canonical"] = H0
        self.assertNotEqual(semantic_replay_projection(left), semantic_replay_projection(right))


if __name__ == "__main__":
    unittest.main()
