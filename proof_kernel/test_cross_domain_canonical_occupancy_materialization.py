from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from cross_domain_canonical_occupancy_materialization import (
    ARTIFACT_NAMES,
    D0,
    DFINAL,
    DOMAIN_ROLES,
    DTRANSIT,
    GUARD_STATES,
    H0,
    HFINAL,
    HTRANSIT,
    OPERATION_ROWS,
    PERMISSION_ROWS,
    PRIMARY_REFRESH_ORDERS,
    PROCESS_BINDING_FIELDS,
    PROJECTION_ROWS,
    PROOF_SCENARIO,
    RECORD_FILENAMES,
    RECORD_ROLES,
    RECORDS,
    CrossDomainOccupancyRejected,
    PhysicalCurrentHeadGuard,
    artifact_role_set_valid,
    bind_invocation,
    canonical_chain,
    canonical_json,
    expected_actor_rows,
    expected_representation,
    guard_and_head_observation_matrix,
    head_disposition,
    materialization_receipt,
    operation_invocation,
    operation_tuple_matrix,
    operational_process_instance_id,
    process_binding,
    process_binding_raw_sha256,
    projection,
    projection_matrix,
    semantic_replay_projection,
    sha256_bytes,
    sha256_value,
    stored_json_bytes,
    strict_load_stored_json,
    validate_materialization_receipt,
    validate_projection,
)


class CrossDomainCanonicalOccupancyMaterializationTests(unittest.TestCase):
    maxDiff = None

    @staticmethod
    def binding(role: str = "domain_A", *, witness: str = "w1_A_B__A_B", pid: int = 4201) -> dict:
        return process_binding({
            "proof_scenario": PROOF_SCENARIO,
            "witness_id": witness,
            "domain_role": role,
            "harness_launch_id": f"{witness}/{role}/launch_0001",
            "pid": pid,
            "macos_process_start": {"seconds": 1000, "microseconds": pid},
            "executable_realpath": "/exact/UnrealEditor",
            "executable_raw_sha256": "1" * 64,
            "unreal_engine_build_identity": "5.8.0-test",
            "entry_map_package_identity": "/Engine/Maps/Entry",
            "project_realpath": "/exact/CityMaterializationProof.uproject",
            "project_raw_sha256": "2" * 64,
            "project_config_and_module_inventory_raw_sha256": "3" * 64,
            "process_root_realpath": f"/private/exact/{witness}/{role}",
            "launch_argv_raw_sha256": "4" * 64,
            "launch_environment_audit_raw_sha256": "5" * 64,
            "launch_cwd_realpath": "/exact/repository",
            "inherited_descriptor_map_raw_sha256": "6" * 64,
            "control_pipe_id": f"{role}/control/0001",
            "structured_output_pipe_id": f"{role}/stdout/0001",
            "diagnostic_pipe_id": f"{role}/stderr/0001",
        })

    @staticmethod
    def expected(role: str, record: str) -> dict:
        return expected_representation(
            (RECORDS / RECORD_FILENAMES[record]).read_bytes(),
            stored_json_bytes(projection(role, record)),
        )

    # Three canonical artifact/hash contracts.
    def test_01_exact_sealed_phase2_chain(self) -> None:
        chain = canonical_chain()
        self.assertEqual([chain["records"][role]["record_canonical_hash"] for role in RECORD_ROLES], [H0, HTRANSIT, HFINAL])
        self.assertEqual([chain["records"][role]["record_raw_sha256"] for role in RECORD_ROLES], [D0, DTRANSIT, DFINAL])
        self.assertTrue(chain["completion_rediscovered_from_rtransit"])
        self.assertFalse(chain["physical_input_to_scheduler_or_resolver"])

    def test_02_detached_json_is_strict_and_lf_bound(self) -> None:
        value = {"a": 1, "b": [2, "three"]}
        self.assertEqual(strict_load_stored_json(stored_json_bytes(value)), value)
        for raw in (b'{"a":1,"a":2}\n', b'{"b":2,"a":1}\n', b'{"a":1}\r\n', b'{"a":1}'):
            with self.subTest(raw=raw), self.assertRaises(CrossDomainOccupancyRejected):
                strict_load_stored_json(raw)

    def test_03_exact_artifact_names_and_role_set(self) -> None:
        self.assertEqual(len(ARTIFACT_NAMES), 82)
        self.assertEqual(len(set(ARTIFACT_NAMES)), 82)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ARTIFACT_NAMES:
                (root / name).write_bytes(b"{}\n")
            self.assertTrue(artifact_role_set_valid(root))
            (root / "unexpected.json").write_bytes(b"{}\n")
            self.assertFalse(artifact_role_set_valid(root))

    # Six frozen projection-row contracts.
    def _assert_projection(self, role: str, record: str) -> None:
        value = projection(role, record)
        self.assertEqual(validate_projection(value, role, record), value)
        self.assertEqual(sha256_value(value), PROJECTION_ROWS[(role, record)]["raw_sha256"])
        altered = copy.deepcopy(value)
        altered["projection_id"] = altered["projection_id"].replace("domain_", "domain_Z_", 1)
        with self.assertRaises(CrossDomainOccupancyRejected):
            validate_projection(altered, role, record)

    def test_04_projection_A_R0(self) -> None: self._assert_projection("domain_A", "R0")
    def test_05_projection_B_R0(self) -> None: self._assert_projection("domain_B", "R0")
    def test_06_projection_A_Rtransit(self) -> None: self._assert_projection("domain_A", "Rtransit")
    def test_07_projection_B_Rtransit(self) -> None: self._assert_projection("domain_B", "Rtransit")
    def test_08_projection_A_Rfinal(self) -> None: self._assert_projection("domain_A", "Rfinal")
    def test_09_projection_B_Rfinal(self) -> None: self._assert_projection("domain_B", "Rfinal")

    # Six closed operation tuples.
    def _assert_operation(self, role: str, operation_id: str) -> None:
        identity = operational_process_instance_id(self.binding(role))
        value = operation_invocation(role, operation_id, identity)
        row = OPERATION_ROWS[(role, operation_id)]
        self.assertEqual(value["operation"], row["operation"])
        self.assertEqual(value["publication_generation"], row["generation"])
        self.assertEqual(value["operational_process_instance_id"], identity)

    def test_10_operation_A_launch(self) -> None: self._assert_operation("domain_A", "launch_0001")
    def test_11_operation_B_launch(self) -> None: self._assert_operation("domain_B", "launch_0001")
    def test_12_operation_A_Rtransit(self) -> None: self._assert_operation("domain_A", "refresh_0001")
    def test_13_operation_B_Rtransit(self) -> None: self._assert_operation("domain_B", "refresh_0001")
    def test_14_operation_A_Rfinal(self) -> None: self._assert_operation("domain_A", "refresh_0002")
    def test_15_operation_B_Rfinal(self) -> None: self._assert_operation("domain_B", "refresh_0002")

    # Three paired-head expected-representation contracts (six exact role rows).
    def _assert_expected_pair(self, record: str, dispositions: tuple[str, str], subjects: tuple[int, int]) -> None:
        values = tuple(self.expected(role, record) for role in DOMAIN_ROLES)
        self.assertEqual(tuple(value["expected_local_subject_disposition"] for value in values), dispositions)
        self.assertEqual(tuple(value["expected_subject_actor_count"] for value in values), subjects)
        self.assertTrue(all(value["expected_anchor_actor_count"] == 1 for value in values))
        self.assertTrue(all(value["expected_controller_count"] == 1 and value["expected_pawn_count"] == 0 for value in values))

    def test_16_expected_pair_R0(self) -> None:
        self._assert_expected_pair("R0", ("remote_at_other_site", "present_at_local_site"), (0, 1))

    def test_17_expected_pair_Rtransit(self) -> None:
        self._assert_expected_pair("Rtransit", ("in_transition_out_of_domain", "in_transition_out_of_domain"), (0, 0))

    def test_18_expected_pair_Rfinal(self) -> None:
        self._assert_expected_pair("Rfinal", ("present_at_local_site", "remote_at_other_site"), (1, 0))

    # Eleven exact permission contexts.
    def _assert_permission(self, context: str) -> None:
        binding = self.binding()
        disposition = head_disposition(
            context=context,
            domain_role="domain_A",
            binding=binding,
            guard_state="failed_closed" if context.startswith(("invalid", "protocol_invalid")) else "open_for_R0",
            represented_hash=H0,
            observed_head=H0,
        )
        expected = PERMISSION_ROWS[context]
        observed = tuple(disposition[field] for field in (
            "current_head_representation_claim_enabled", "refresh_enabled", "inspection_enabled",
            "local_nonconsequential_step_enabled", "diagnostics_enabled", "termination_enabled",
            "local_publication_enabled",
        ))
        self.assertEqual(observed, expected)
        for field in (
            "canonical_completion_enabled", "canonical_evidence_enabled", "canonical_mutation_enabled",
            "canonical_scheduling_enabled", "canonical_truth_publication_enabled", "peer_interaction_enabled",
        ):
            self.assertFalse(disposition[field])

    def test_19_permission_unbound(self) -> None: self._assert_permission("unbound / binding_not_accepted")
    def test_20_permission_sync_R0(self) -> None: self._assert_permission("synchronized(R0) / exact_current_representation")
    def test_21_permission_unconfirmed_R0(self) -> None: self._assert_permission("head_unconfirmed(R0) / successor_observation_unpublished")
    def test_22_permission_stale_R0_Rtransit(self) -> None: self._assert_permission("stale(R0/Rtransit) / immediate_successor_verified")
    def test_23_permission_sync_Rtransit(self) -> None: self._assert_permission("synchronized(Rtransit) / exact_current_representation")
    def test_24_permission_unconfirmed_Rtransit(self) -> None: self._assert_permission("head_unconfirmed(Rtransit) / successor_observation_unpublished")
    def test_25_permission_stale_Rtransit_Rfinal(self) -> None: self._assert_permission("stale(Rtransit/Rfinal) / immediate_successor_verified")
    def test_26_permission_sync_Rfinal(self) -> None: self._assert_permission("synchronized(Rfinal) / exact_current_representation")
    def test_27_permission_stale_R0_Rfinal(self) -> None: self._assert_permission("stale(R0/Rfinal) / multigeneration_control_terminal")
    def test_28_permission_invalid(self) -> None: self._assert_permission("invalid / local_publication_unprovable")
    def test_29_permission_protocol_invalid(self) -> None: self._assert_permission("protocol_invalid / physical_protocol_violation")

    # Six frozen controls.
    def test_30_control_C1_completion_independence(self) -> None:
        chain = canonical_chain()
        self.assertEqual(chain["records"]["Rfinal"]["record_canonical_hash"], HFINAL)
        self.assertFalse(chain["physical_input_to_scheduler_or_resolver"])

    def test_31_control_C2_positive_Rtransit_absence(self) -> None:
        for role in DOMAIN_ROLES:
            expected = self.expected(role, "Rtransit")
            self.assertEqual(expected["expected_anchor_actor_count"], 1)
            self.assertEqual(expected["expected_subject_actor_count"], 0)

    def test_32_control_C3_receipt_only_rejected(self) -> None:
        binding = self.binding()
        expected = self.expected("domain_A", "R0")
        anchors, subjects = expected_actor_rows(expected, binding, "publication_0001")
        receipt = materialization_receipt(
            operation_id="launch_0001", command_raw_sha256="7" * 64,
            operation_invocation_raw_sha256="8" * 64, expected=expected,
            binding=binding, generation="publication_0001", anchor_rows=anchors,
            subject_rows=subjects,
        )
        self.assertEqual(validate_materialization_receipt(receipt, expected, binding, "launch_0001"), receipt)
        self.assertEqual(receipt["representation_publication_state"], "locally_published_unverified")
        self.assertNotIn("synchronized", canonical_json(receipt))

    def test_33_control_C4a_start_guard_open(self) -> None:
        guard = PhysicalCurrentHeadGuard()
        guard.transition("failed_closed", "canonical_start_called_while_open")
        self.assertEqual(guard.state, "failed_closed")
        with self.assertRaises(CrossDomainOccupancyRejected):
            guard.transition("open_for_R0", "retry")

    def test_34_control_C4b_completion_guard_open(self) -> None:
        guard = PhysicalCurrentHeadGuard()
        guard.transition("closed_for_R0_to_Rtransit", "before_exact_start_resolution")
        guard.transition("open_for_Rtransit", "verified_Rtransit_and_both_stale_R0")
        guard.transition("failed_closed", "canonical_completion_called_while_open")
        self.assertEqual(guard.state, "failed_closed")

    def test_35_control_C5_process_replacement(self) -> None:
        original = self.binding(pid=4201)
        replacement = self.binding(pid=4202)
        self.assertNotEqual(operational_process_instance_id(original), operational_process_instance_id(replacement))
        self.assertNotEqual(process_binding_raw_sha256(original), process_binding_raw_sha256(replacement))

    # Four refresh-order witnesses.
    def test_36_witness_W1_order(self) -> None: self.assertEqual(PRIMARY_REFRESH_ORDERS["W1"], (("domain_A", "domain_B"), ("domain_A", "domain_B")))
    def test_37_witness_W2_order(self) -> None: self.assertEqual(PRIMARY_REFRESH_ORDERS["W2"], (("domain_B", "domain_A"), ("domain_B", "domain_A")))
    def test_38_witness_W3_order(self) -> None: self.assertEqual(PRIMARY_REFRESH_ORDERS["W3"], (("domain_A", "domain_B"), ("domain_B", "domain_A")))
    def test_39_witness_W4_order(self) -> None: self.assertEqual(PRIMARY_REFRESH_ORDERS["W4"], (("domain_B", "domain_A"), ("domain_A", "domain_B")))

    # Four asymmetric malformed-projection failures.
    def _assert_af(self, role: str, record: str) -> None:
        altered = projection(role, record)
        altered["projection_id"] = altered["projection_id"].replace(f"cross_domain_{role[-1]}", "cross_domain_Z")
        self.assertNotEqual(sha256_bytes(stored_json_bytes(altered)), PROJECTION_ROWS[(role, record)]["raw_sha256"])
        with self.assertRaises(CrossDomainOccupancyRejected) as caught:
            validate_projection(altered, role, record)
        self.assertEqual(caught.exception.stage, "M09_authenticate_and_validate_projection")

    def test_40_failure_AF01(self) -> None: self._assert_af("domain_B", "Rtransit")
    def test_41_failure_AF02(self) -> None: self._assert_af("domain_A", "Rtransit")
    def test_42_failure_AF03(self) -> None: self._assert_af("domain_B", "Rfinal")
    def test_43_failure_AF04(self) -> None: self._assert_af("domain_A", "Rfinal")

    def test_44_canonical_replay_projection(self) -> None:
        first = {"pid": 31, "canonical_hash": HFINAL, "nested": {"world_instance_identity": "one"}}
        second = {"pid": 79, "canonical_hash": HFINAL, "nested": {"world_instance_identity": "two"}}
        self.assertEqual(semantic_replay_projection(first), semantic_replay_projection(second))

    def test_45_release_set_closure(self) -> None:
        from verify_cross_domain_canonical_occupancy_materialization_release import NON_ARTIFACT_MEMBERS, release_paths

        self.assertEqual(len(NON_ARTIFACT_MEMBERS), 90)
        self.assertEqual(len(set(NON_ARTIFACT_MEMBERS)), 90)
        self.assertEqual(len(release_paths()), 172)
        self.assertEqual(tuple(sorted(release_paths(), key=lambda value: value.encode("utf-8"))), release_paths())
        self.assertEqual(len(PROCESS_BINDING_FIELDS), 22)
        self.assertEqual(len(GUARD_STATES), 7)
        self.assertEqual(len(projection_matrix()["rows"]), 6)
        self.assertEqual(len(operation_tuple_matrix()["rows"]), 6)
        self.assertEqual(len(guard_and_head_observation_matrix()["permission_rows"]), 11)


if __name__ == "__main__":
    unittest.main()
