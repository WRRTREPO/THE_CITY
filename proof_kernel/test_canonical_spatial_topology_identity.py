from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from canonical_spatial_topology_identity import (
    ANCESTRY_SCHEMA,
    BOUNDARY_SCHEMA,
    CANONICAL_PAYLOAD_FILENAME,
    ENDPOINTS,
    ENDPOINT_SEMANTICS,
    FAILURE_SCHEMA,
    FROZEN_ADVERSARIAL_MATRIX,
    FROZEN_REPRESENTATION_DIAGNOSTICS,
    INVENTORY_SCHEMA,
    LAUNCH_RECEIPT_FILENAME,
    LEDGER_SCHEMA,
    MATERIALIZATION_MAP_FILENAME,
    MATERIALIZATION_RECEIPT_SCHEMA,
    NO_BOUNDARY,
    PAYLOAD_SCHEMA,
    PROCESS_ID,
    QUERY_SCHEMA,
    RECORD_SCHEMA,
    ROUTE_ID,
    R0_MAPPING_ID,
    R1_MAPPING_ID,
    SCENARIO_ID,
    SIMULATION_VERSION,
    SITE_A,
    SITE_B,
    SITE_IDS,
    WORK_ID,
    CanonicalTopologyRejected,
    RepresentationRejected,
    canonical_hash,
    canonical_source_audit,
    complete_termination_witness,
    conceptual_assignment,
    conceptual_label_neutrality_witness,
    evaluate_route_access,
    initial_canonical_envelope,
    isolation_witness,
    launch_receipt,
    materialization_failure,
    materialization_map,
    next_consequential_boundary,
    open_termination_observation,
    proof_input_inventory,
    proof_run,
    raw_stored_sha256,
    replay_witness,
    resolve_next_due,
    reverse_order_oracle,
    runtime_fail_closed_results,
    stored_json_bytes,
    strict_load_stored_json,
    validate_canonical_envelope,
    validate_isolation_witness,
    validate_materialization_bundle,
    validate_materialization_receipt,
    validate_proof_input_inventory,
    validate_termination_witness,
)
from kernel import canonical_json


class CanonicalSpatialTopologyIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.r0 = initial_canonical_envelope()
        self.boundary = next_consequential_boundary(self.r0)
        assert self.boundary is not None
        self.r1 = resolve_next_due(self.r0, self.boundary)

    def test_01_exact_identity_and_fixture_topology(self) -> None:
        self.assertEqual(validate_canonical_envelope(self.r0), "R0")
        self.assertEqual(self.r0["identity"]["record_schema"], RECORD_SCHEMA)
        self.assertEqual(self.r0["identity"]["payload_schema"], PAYLOAD_SCHEMA)
        self.assertEqual(self.r0["identity"]["scenario_id"], SCENARIO_ID)
        self.assertEqual(self.r0["identity"]["simulation_version"], SIMULATION_VERSION)
        topology = self.r0["current_causal_state"]["spatial_topology"]
        self.assertEqual(tuple(topology["sites"]), SITE_IDS)
        self.assertEqual(tuple(topology["routes"]), (ROUTE_ID,))
        self.assertEqual(topology["routes"][ROUTE_ID]["endpoint_site_ids"], ENDPOINTS)
        self.assertEqual(topology["routes"][ROUTE_ID]["endpoint_semantics"], ENDPOINT_SEMANTICS)

    def test_02_strict_stored_serialization_and_duplicate_rejection(self) -> None:
        self.assertEqual(strict_load_stored_json(stored_json_bytes(self.r0)), self.r0)
        with self.assertRaises(ValueError):
            strict_load_stored_json(b'{"identity":{},"identity":{}}\n')
        with self.assertRaises(ValueError):
            strict_load_stored_json(stored_json_bytes(self.r0) + b"\n")
        self.assertEqual(stored_json_bytes(self.r0), canonical_json(self.r0).encode() + b"\n")
        with self.assertRaises(ValueError):
            stored_json_bytes({"not_finite": float("nan")})

    def test_03_record_bound_boundary_and_singular_resolution(self) -> None:
        self.assertEqual(self.boundary["boundary_schema"], BOUNDARY_SCHEMA)
        self.assertEqual(self.boundary["source_record_hash"], canonical_hash(self.r0))
        self.assertEqual(self.boundary["due_work_ids"], [WORK_ID])
        stale = copy.deepcopy(self.boundary)
        stale["source_record_hash"] = canonical_hash(self.r1)
        with self.assertRaises(CanonicalTopologyRejected):
            resolve_next_due(self.r0, stale)
        self.assertIs(next_consequential_boundary(self.r1), NO_BOUNDARY)

    def test_04_r1_has_exact_six_replacements(self) -> None:
        self.assertEqual(validate_canonical_envelope(self.r1), "R1")
        changed = []
        if self.r0["current_causal_state"]["spatial_topology"]["routes"][ROUTE_ID]["access_state"] != self.r1["current_causal_state"]["spatial_topology"]["routes"][ROUTE_ID]["access_state"]:
            changed.append("access")
        if self.r0["current_causal_state"]["fixture_processes"][PROCESS_ID]["state"] != self.r1["current_causal_state"]["fixture_processes"][PROCESS_ID]["state"]:
            changed.append("process")
        if self.r0["future_causal_state"]["canonical_clock"] != self.r1["future_causal_state"]["canonical_clock"]:
            changed.append("clock")
        if self.r0["future_causal_state"]["unresolved_work"] != self.r1["future_causal_state"]["unresolved_work"]:
            changed.append("work")
        if self.r0["causal_provenance"]["authoritative_causal_ledger"] != self.r1["causal_provenance"]["authoritative_causal_ledger"]:
            changed.append("ledger")
        if self.r0["causal_provenance"]["canonical_ancestry"] != self.r1["causal_provenance"]["canonical_ancestry"]:
            changed.append("ancestry")
        self.assertEqual(changed, ["access", "process", "clock", "work", "ledger", "ancestry"])
        self.assertEqual(self.r0["identity"], self.r1["identity"])
        self.assertEqual(self.r0["causal_provenance"]["fixture_genesis"], self.r1["causal_provenance"]["fixture_genesis"])
        self.assertEqual(self.r0["current_causal_state"]["spatial_topology"]["sites"], self.r1["current_causal_state"]["spatial_topology"]["sites"])

    def test_05_provenance_is_h0_bound_and_self_hash_safe(self) -> None:
        h0 = canonical_hash(self.r0)
        h1 = canonical_hash(self.r1)
        ancestry = self.r1["causal_provenance"]["canonical_ancestry"]
        ledger = self.r1["causal_provenance"]["authoritative_causal_ledger"][0]
        self.assertEqual(ancestry["ancestry_schema"], ANCESTRY_SCHEMA)
        self.assertEqual(ancestry["parent_record_hash"], h0)
        self.assertEqual(ledger["ledger_schema"], LEDGER_SCHEMA)
        self.assertEqual(ledger["canonical_pre_state_hash"], h0)
        self.assertNotIn(h1, canonical_json(self.r1))
        self.assertNotIn("canonical_post_state_hash", ledger)

    def test_06_forward_and_reverse_requests_are_semantically_equivalent(self) -> None:
        for record, expected_eligible in ((self.r0, True), (self.r1, False)):
            oracle = reverse_order_oracle(record)
            self.assertTrue(oracle["semantic_results_equal_after_received_order_removed"])
            self.assertTrue(oracle["access_state_evaluated"])
            self.assertEqual(oracle["forward"]["eligible"], expected_eligible)
            self.assertEqual(oracle["reverse"]["eligible"], expected_eligible)
            self.assertEqual(oracle["forward"]["normalized_endpoint_site_ids"], ENDPOINTS)
            self.assertEqual(oracle["reverse"]["normalized_endpoint_site_ids"], ENDPOINTS)

    def test_07_query_failure_precedence_and_no_access_evaluation(self) -> None:
        cases = (
            ("bad", ENDPOINTS, "invalid_route_id"),
            ("bad", "also-bad", "invalid_route_id"),
            (ROUTE_ID, "bad", "endpoint_array_required"),
            (ROUTE_ID, [SITE_A], "endpoint_count_not_two"),
            (ROUTE_ID, [SITE_A, SITE_B, "bad"], "endpoint_count_not_two"),
            (ROUTE_ID, [SITE_A, "bad"], "invalid_endpoint_site_id"),
            (ROUTE_ID, ["bad", "bad"], "invalid_endpoint_site_id"),
            (ROUTE_ID, [SITE_A, SITE_A], "duplicate_endpoint_site_id"),
        )
        for route, endpoints, reason in cases:
            result = evaluate_route_access(self.r0, route, endpoints)
            self.assertEqual(set(result), {"result_schema", "source_record_hash", "evaluation_status", "reason_code", "eligible", "access_state_evaluated"})
            self.assertEqual(result["result_schema"], QUERY_SCHEMA)
            self.assertEqual(result["reason_code"], reason)
            self.assertIsNone(result["eligible"])
            self.assertFalse(result["access_state_evaluated"])

    def test_08_canonical_validation_precedes_query(self) -> None:
        invalid = copy.deepcopy(self.r0)
        invalid["current_causal_state"]["spatial_topology"]["sites"]["extra"] = None
        with self.assertRaises(CanonicalTopologyRejected):
            evaluate_route_access(invalid, ROUTE_ID, ENDPOINTS)

    def test_09_conceptual_label_rename_is_neutral(self) -> None:
        witness = conceptual_label_neutrality_witness()
        self.assertNotEqual(conceptual_assignment(False), conceptual_assignment(True))
        self.assertNotEqual(witness["A0"], witness["A1"])
        self.assertEqual(witness["AP0"], witness["AP1"])
        self.assertTrue(witness["PB0_equals_PB1"])
        self.assertEqual(witness["baseline_canonical_hash"], canonical_hash(self.r0))
        self.assertEqual(witness["renamed_canonical_hash"], canonical_hash(self.r0))

    def test_10_exact_endpoint_free_materialization_maps(self) -> None:
        map0 = materialization_map(self.r0)
        map1 = materialization_map(self.r1)
        self.assertEqual(map0["mapping_id"], R0_MAPPING_ID)
        self.assertEqual(map1["mapping_id"], R1_MAPPING_ID)
        self.assertEqual(set(map0), {"mapping_schema", "mapping_id", "source_canonical_hash", "sites", "routes"})
        self.assertNotIn("endpoint", canonical_json(map0))
        self.assertEqual(map0["sites"], map1["sites"])
        self.assertEqual(map0["routes"], map1["routes"])

    def test_11_detached_bundle_validates_raw_and_canonical_identity(self) -> None:
        for record in (self.r0, self.r1):
            mapping = materialization_map(record)
            receipt = launch_receipt(record, mapping)
            accepted_record, accepted_map = validate_materialization_bundle(
                stored_json_bytes(record), stored_json_bytes(mapping), stored_json_bytes(receipt)
            )
            self.assertEqual(accepted_record, record)
            self.assertEqual(accepted_map, mapping)
        with self.assertRaises(RepresentationRejected):
            validate_materialization_bundle(
                stored_json_bytes(self.r0), stored_json_bytes(materialization_map(self.r1)), stored_json_bytes(launch_receipt(self.r1))
            )

    def test_12_proof_input_inventory_is_exact_and_role_bound(self) -> None:
        for role, record in (("R0_source", self.r0), ("R1_return", self.r1)):
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                mapping = materialization_map(record)
                (root / CANONICAL_PAYLOAD_FILENAME).write_bytes(stored_json_bytes(record))
                (root / MATERIALIZATION_MAP_FILENAME).write_bytes(stored_json_bytes(mapping))
                (root / LAUNCH_RECEIPT_FILENAME).write_bytes(stored_json_bytes(launch_receipt(record, mapping)))
                inventory = proof_input_inventory(root, role)
                self.assertEqual(inventory["inventory_schema"], INVENTORY_SCHEMA)
                self.assertEqual([entry["filename"] for entry in inventory["files"]], [CANONICAL_PAYLOAD_FILENAME, LAUNCH_RECEIPT_FILENAME, MATERIALIZATION_MAP_FILENAME])
                self.assertEqual(inventory["unexpected_files"], [])

    def test_13_materialization_receipt_is_observation_not_authority(self) -> None:
        for record, process_id in ((self.r0, "P0"), (self.r1, "P1")):
            mapping = materialization_map(record)
            receipt = {
                "accepted_canonical_hash": canonical_hash(record),
                "accepted_canonical_payload_raw_sha256": raw_stored_sha256(record),
                "accepted_mapping_id": mapping["mapping_id"],
                "accepted_materialization_map_raw_sha256": raw_stored_sha256(mapping),
                "materialized_access_state": record["current_causal_state"]["spatial_topology"]["routes"][ROUTE_ID]["access_state"],
                "materialized_canonical_route_id": ROUTE_ID,
                "materialized_canonical_site_ids": list(SITE_IDS),
                "materialized_endpoint_site_ids": ENDPOINTS,
                "operational_actor_instance_ids": {"representation_site_slot_01": "site_a", "representation_site_slot_02": "site_b", "representation_route_slot_01": "route"},
                "operational_process_instance_id": process_id,
                "receipt_schema": MATERIALIZATION_RECEIPT_SCHEMA,
            }
            validate_materialization_receipt(record, mapping, receipt)
            self.assertNotIn(process_id, canonical_json(record))

    def test_14_lifecycle_witnesses_are_exact_and_isolated(self) -> None:
        h0, h1 = canonical_hash(self.r0), canonical_hash(self.r1)
        opened = open_termination_observation("P0", h0, process_alive=False)
        termination = complete_termination_witness(opened, h1)
        validate_termination_witness(termination, "P0", h0, h1)
        with self.assertRaises(RepresentationRejected):
            open_termination_observation("P0", h0, process_alive=True)
        with tempfile.TemporaryDirectory() as left, tempfile.TemporaryDirectory() as right:
            left_root = Path(left); right_root = Path(right)
            isolation = isolation_witness("P0", "P1", left_root, right_root, left_root / "cache", right_root / "cache")
            validate_isolation_witness(isolation)
            self.assertEqual(isolation["truth_bearing_command_line_values"], [])

    def test_15_materialization_failure_dispositions_are_detached(self) -> None:
        failure = materialization_failure("raw_hash", "artifact_raw_hash_mismatch")
        self.assertEqual(failure["diagnostic_schema"], FAILURE_SCHEMA)
        self.assertFalse(failure["materialization_started"])
        self.assertFalse(failure["canonical_write_attempted"])
        with self.assertRaises(RepresentationRejected):
            materialization_failure("raw_hash", "invalid_launch_receipt")

    def test_16_all_28_adversarial_families_fail_closed(self) -> None:
        results = runtime_fail_closed_results()
        observed = {name: (result["disposition"], tuple(result["variants"])) for name, result in results.items()}
        self.assertEqual(observed, FROZEN_ADVERSARIAL_MATRIX)
        observed_diagnostics = {
            family: {
                variant: (result["detached_diagnostic"]["stage"], result["detached_diagnostic"]["reason_code"])
                for variant, result in results[family]["variants"].items()
                if "detached_diagnostic" in result
            }
            for family in FROZEN_REPRESENTATION_DIAGNOSTICS
        }
        self.assertEqual(observed_diagnostics, FROZEN_REPRESENTATION_DIAGNOSTICS)
        diagnostics = [
            variant["detached_diagnostic"]
            for family in results.values()
            for variant in family["variants"].values()
            if "detached_diagnostic" in variant
        ]
        self.assertTrue(diagnostics)
        self.assertTrue(all(set(diagnostic) == {"canonical_write_attempted", "diagnostic_schema", "materialization_started", "reason_code", "stage"} for diagnostic in diagnostics))

    def test_17_replay_is_byte_identical(self) -> None:
        replay = replay_witness()
        self.assertEqual(replay["result"], "accepted")
        self.assertTrue(replay["R0_byte_identical"])
        self.assertTrue(replay["R1_byte_identical"])

    def test_18_source_audit_and_proof_run(self) -> None:
        self.assertTrue(all(canonical_source_audit().values()))
        run = proof_run()
        self.assertEqual(run["R0_hash"], canonical_hash(self.r0))
        self.assertEqual(run["R1_hash"], canonical_hash(self.r1))
        self.assertEqual(run["R0_raw_sha256"], raw_stored_sha256(self.r0))
        self.assertEqual(run["R1_raw_sha256"], raw_stored_sha256(self.r1))


if __name__ == "__main__":
    unittest.main()
