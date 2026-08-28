"""Focused tests for Canonical Occupancy Transition Proof v0.1.0."""

from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from canonical_occupancy_transition import (
    ALL_FAULT_POINTS,
    ARTIFACT_NAMES,
    COMPLETE_WORK,
    NO_BOUNDARY,
    OCCUPANT,
    PAYLOAD_SCHEMA,
    REJECT_BOUNDARY_SHAPE,
    REJECT_BOUNDARY_SOURCE,
    REJECT_NO_DUE_WORK,
    RESERVATION,
    ROUTE,
    SIMULATION_VERSION,
    SITE_A,
    SITE_B,
    START_WORK,
    TRANSITION,
    CanonicalOccupancyRejected,
    adversarial_results,
    artifact_payloads,
    blocked_control_run,
    boundary_jump_run,
    canonical_hash,
    canonical_json,
    dense_inspection_run,
    detached_occupancy_projection,
    equivalence_oracle,
    fault_atomicity_results,
    initial_available_record,
    initial_blocked_record,
    load_canonical_record_bytes,
    next_consequential_boundary,
    replay_oracle,
    resolve_next_due,
    source_audit,
    topology_projection_oracle,
    transition_definition_oracle,
    transition_definition_projection,
    validate_canonical_record,
    write_artifacts,
    _finalize_source_audit,
)


class CanonicalOccupancyTransitionTests(unittest.TestCase):
    def _primary(self) -> tuple[dict, dict, dict, dict, dict]:
        r0 = initial_available_record()
        b0 = next_consequential_boundary(r0)
        self.assertIsNotNone(b0)
        rtransit = resolve_next_due(r0, b0)
        bt = next_consequential_boundary(rtransit)
        self.assertIsNotNone(bt)
        rfinal = resolve_next_due(rtransit, bt)
        return r0, b0, rtransit, bt, rfinal

    def test_01_exact_identity_and_independent_roots(self) -> None:
        available = initial_available_record()
        blocked = initial_blocked_record()
        for record in (available, blocked):
            self.assertEqual(record["identity"]["payload_schema"], PAYLOAD_SCHEMA)
            self.assertEqual(record["identity"]["simulation_version"], SIMULATION_VERSION)
            self.assertEqual(validate_canonical_record(record), [])
        self.assertNotEqual(canonical_hash(available), canonical_hash(blocked))
        self.assertEqual(
            canonical_json(transition_definition_projection(available)),
            canonical_json(transition_definition_projection(blocked)),
        )
        self.assertEqual(
            available["current_causal_state"]["spatial_topology"]["routes"][ROUTE]["access_state"],
            "available",
        )
        self.assertEqual(
            blocked["current_causal_state"]["spatial_topology"]["routes"][ROUTE]["access_state"],
            "blocked",
        )

    def test_02_strict_stored_json_and_duplicate_rejection(self) -> None:
        record = initial_available_record()
        raw = (canonical_json(record) + "\n").encode("utf-8")
        self.assertEqual(load_canonical_record_bytes(raw), record)
        for malformed in (
            raw[:-1],
            b"\xef\xbb\xbf" + raw,
            raw + b"\n",
            b'{"identity":{},"identity":{}}\n',
            b'{"value":NaN}\n',
        ):
            with self.assertRaises(CanonicalOccupancyRejected):
                load_canonical_record_bytes(malformed)

    def test_03_phase_1_topology_projection_is_exact_and_hash_bound(self) -> None:
        oracle = topology_projection_oracle()
        self.assertTrue(oracle["passed"])
        self.assertTrue(oracle["available_projection_byte_identical"])
        self.assertTrue(oracle["blocked_diff_is_access_only"])

    def test_04_singular_occupancy_and_exhaustive_lifecycle_rows(self) -> None:
        refs = artifact_payloads()
        names = (
            "canonical_occupancy_transition_R0.json",
            "canonical_occupancy_transition_R0_blocked.json",
            "canonical_occupancy_transition_Rtransit.json",
            "canonical_occupancy_transition_Rfinal.json",
            "canonical_occupancy_transition_Rblocked.json",
        )
        for name in names:
            self.assertEqual(validate_canonical_record(refs[name]), [])
            self.assertEqual(set(refs[name]["current_causal_state"]["canonical_occupancy"]), {OCCUPANT})
            self.assertNotIn("subject_location", refs[name]["current_causal_state"])
            self.assertNotIn("site_occupants", refs[name]["current_causal_state"])
        invalid = copy.deepcopy(refs[names[0]])
        invalid["current_causal_state"]["canonical_occupancy"][OCCUPANT]["transition_id"] = TRANSITION
        self.assertTrue(validate_canonical_record(invalid))

    def test_05_scheduler_discovers_only_record_bound_unresolved_work(self) -> None:
        r0, b0, rt, bt, rf = self._primary()
        self.assertEqual(b0["source_record_hash"], canonical_hash(r0))
        self.assertEqual(b0["due_work_ids"], [START_WORK])
        self.assertEqual(bt["source_record_hash"], canonical_hash(rt))
        self.assertEqual(bt["due_work_ids"], [COMPLETE_WORK])
        self.assertEqual(next_consequential_boundary(rf), NO_BOUNDARY)

    def test_06_reverse_oriented_intent_normalizes_copy_only(self) -> None:
        r0 = initial_available_record()
        commitment = r0["current_causal_state"]["occupancy_transition_commitments"][TRANSITION]
        self.assertEqual([commitment["origin_site_id"], commitment["destination_site_id"]], [SITE_B, SITE_A])
        rtransit = resolve_next_due(r0, next_consequential_boundary(r0))
        entry = rtransit["causal_provenance"]["authoritative_causal_ledger"][0]
        self.assertEqual(entry["transition_observation"]["normalized_transition_site_ids"], [SITE_A, SITE_B])
        self.assertEqual(entry["transition_observation"]["origin_site_id"], SITE_B)
        self.assertEqual(entry["transition_observation"]["destination_site_id"], SITE_A)

    def test_07_accepted_start_is_atomic_and_owns_exact_reservation(self) -> None:
        r0, b0, rt, _, _ = self._primary()
        state = rt["current_causal_state"]
        self.assertEqual(state["canonical_occupancy"][OCCUPANT], {"kind": "in_transition", "transition_id": TRANSITION})
        self.assertEqual(state["occupancy_transition_commitments"][TRANSITION]["resources_owned"], [RESERVATION])
        self.assertEqual(state["occupancy_transition_reservations"][RESERVATION], {"occupant_id": OCCUPANT, "state": "reserved", "owner_transition_id": TRANSITION})
        self.assertEqual(rt["future_causal_state"]["unresolved_work"][0]["work_id"], COMPLETE_WORK)
        entry = rt["causal_provenance"]["authoritative_causal_ledger"][0]
        self.assertEqual(entry["result"], "started")
        self.assertEqual(entry["canonical_pre_state_hash"], canonical_hash(r0))
        self.assertEqual(entry["source_boundary"], b0)
        self.assertNotIn("canonical_post_state_hash", canonical_json(rt))

    def test_08_completion_is_absent_until_published_transition_record(self) -> None:
        r0, _, rt, bt, _ = self._primary()
        self.assertNotIn(COMPLETE_WORK, next_consequential_boundary(r0)["due_work_ids"])
        self.assertEqual(bt["source_record_hash"], canonical_hash(rt))
        self.assertNotEqual(bt["source_record_hash"], canonical_hash(r0))
        stale = copy.deepcopy(bt)
        stale["source_record_hash"] = canonical_hash(r0)
        with self.assertRaisesRegex(CanonicalOccupancyRejected, REJECT_BOUNDARY_SOURCE):
            resolve_next_due(rt, stale)

    def test_09_completion_settles_destination_and_releases_resource(self) -> None:
        _, _, rt, bt, rf = self._primary()
        state = rf["current_causal_state"]
        self.assertEqual(state["canonical_occupancy"][OCCUPANT], {"kind": "at_site", "site_id": SITE_A})
        commitment = state["occupancy_transition_commitments"][TRANSITION]
        self.assertEqual(commitment["state"], "succeeded")
        self.assertEqual(commitment["resources_owned"], [])
        self.assertEqual(commitment["terminal_resource_disposition"], "release_subject_transition_reservation")
        self.assertEqual(state["occupancy_transition_reservations"][RESERVATION], {"occupant_id": OCCUPANT, "state": "available", "owner_transition_id": None})
        self.assertEqual(rf["causal_provenance"]["canonical_ancestry"]["parent_record_hash"], canonical_hash(rt))
        self.assertEqual(rf["causal_provenance"]["authoritative_causal_ledger"][-1]["source_boundary"], bt)

    def test_10_blocked_access_is_ordinary_failed_gate(self) -> None:
        run = blocked_control_run()
        root = run["checkpoints"]["R0_blocked"]["canonical_record"]
        blocked = run["checkpoints"]["Rblocked"]["canonical_record"]
        state = blocked["current_causal_state"]
        self.assertEqual(state["canonical_occupancy"][OCCUPANT], {"kind": "at_site", "site_id": SITE_B})
        commitment = state["occupancy_transition_commitments"][TRANSITION]
        self.assertEqual((commitment["state"], commitment["terminal_reason"], commitment["terminal_resource_disposition"]), ("failed", "failed_gate", "no_resource_acquired"))
        self.assertEqual(state["occupancy_transition_reservations"][RESERVATION]["state"], "available")
        self.assertEqual(next_consequential_boundary(blocked), NO_BOUNDARY)
        gates = blocked["causal_provenance"]["authoritative_causal_ledger"][0]["gate_observations"]
        self.assertEqual([gate["passed"] for gate in gates], [True, True, False, True])
        self.assertEqual(blocked["causal_provenance"]["canonical_ancestry"]["parent_record_hash"], canonical_hash(root))

    def test_11_stale_crossing_and_malformed_boundaries_reject(self) -> None:
        r0, b0, rt, bt, rf = self._primary()
        with self.assertRaisesRegex(CanonicalOccupancyRejected, REJECT_BOUNDARY_SOURCE):
            resolve_next_due(rt, b0)
        with self.assertRaisesRegex(CanonicalOccupancyRejected, REJECT_BOUNDARY_SHAPE):
            resolve_next_due(rt, {"source_record_hash": canonical_hash(rt)})
        with self.assertRaisesRegex(CanonicalOccupancyRejected, REJECT_BOUNDARY_SHAPE):
            resolve_next_due(rt, None)  # type: ignore[arg-type]
        with self.assertRaisesRegex(CanonicalOccupancyRejected, REJECT_NO_DUE_WORK):
            resolve_next_due(rf, bt)
        blocked_boundary = next_consequential_boundary(initial_blocked_record())
        with self.assertRaisesRegex(CanonicalOccupancyRejected, REJECT_BOUNDARY_SOURCE):
            resolve_next_due(r0, blocked_boundary)

    def test_12_schedule_copies_cannot_create_or_resurrect_work(self) -> None:
        r0, _, rt, _, rf = self._primary()
        self.assertEqual(next_consequential_boundary(r0)["due_work_ids"], [START_WORK])
        self.assertEqual(next_consequential_boundary(rt)["due_work_ids"], [COMPLETE_WORK])
        self.assertEqual(next_consequential_boundary(rf), NO_BOUNDARY)
        self.assertEqual(rf["causal_provenance"]["authoritative_causal_ledger"][0]["schedule_effect"]["created_work"]["work_id"], COMPLETE_WORK)

    def test_13_detached_projection_never_creates_route_occupancy(self) -> None:
        r0, _, rt, _, rf = self._primary()
        self.assertEqual(detached_occupancy_projection(r0)["site_projection"], {SITE_A: [], SITE_B: [OCCUPANT]})
        self.assertEqual(detached_occupancy_projection(rt), {"site_projection": {SITE_A: [], SITE_B: []}, "detached_transition_relation": {OCCUPANT: TRANSITION}})
        self.assertEqual(detached_occupancy_projection(rf)["site_projection"], {SITE_A: [OCCUPANT], SITE_B: []})
        self.assertNotIn("route_occupancy", canonical_json(rt))
        self.assertNotIn("site_projection", canonical_json(rt))

    def test_14_every_exact_private_fault_point_is_atomic(self) -> None:
        result = fault_atomicity_results()
        self.assertEqual(result["count"], len(ALL_FAULT_POINTS))
        self.assertTrue(result["passed"])
        for point, row in result["fault_points"].items():
            self.assertIn(point, ALL_FAULT_POINTS)
            self.assertTrue(row["source_bytes_unchanged"])
            self.assertTrue(row["scheduler_result_unchanged"])
            self.assertFalse(row["canonical_successor_published"])

    def test_15_dense_and_jump_match_every_canonical_checkpoint(self) -> None:
        runs = {"dense_inspection": dense_inspection_run(), "boundary_jump": boundary_jump_run()}
        self.assertEqual(equivalence_oracle(runs), {"result": "accepted", "reference_witness": "dense_inspection", "failures": []})
        for label in ("R0", "Rtransit", "Rfinal"):
            self.assertEqual(canonical_json(runs["dense_inspection"]["checkpoints"][label]), canonical_json(runs["boundary_jump"]["checkpoints"][label]))
        self.assertEqual(runs["boundary_jump"]["resolution_local_inspection_trace"], [])

    def test_16_dense_trace_shape_is_exact_and_non_authoritative(self) -> None:
        dense = dense_inspection_run()
        trace = dense["resolution_local_inspection_trace"]
        self.assertEqual(len(trace), 2)
        self.assertEqual([row["inspection_id"] for row in trace], ["inspection_before_start_0001", "inspection_between_boundaries_0001"])
        for row in trace:
            self.assertEqual(set(row), {"trace_schema", "inspection_id", "source_record_hash"})
        self.assertNotEqual(trace, boundary_jump_run()["resolution_local_inspection_trace"])

    def test_17_all_41_adversarial_families_are_mechanical(self) -> None:
        result = adversarial_results()
        self.assertEqual(result["count"], 41)
        self.assertTrue(result["passed"])
        self.assertEqual({row["case"] for row in result["cases"].values()}, set(range(1, 42)))

    def test_18_each_history_replays_byte_identically(self) -> None:
        result = replay_oracle()
        self.assertTrue(result["passed"])
        for row in result["witnesses"].values():
            self.assertEqual(row["first_hash"], row["second_hash"])

    def test_19_source_audit_is_a_hard_gate(self) -> None:
        audit = _finalize_source_audit(source_audit())
        self.assertTrue(audit["source_audit_passed"])
        self.assertEqual(audit["resolver_functions"], ["resolve_next_due"])
        self.assertEqual(audit["completion_work_callers"], ["_construct_start_successor", "_ledger_entry"])
        self.assertFalse(audit["private_resolver_calls_scheduler"])
        self.assertFalse(audit["public_fault_parameter_present"])
        self.assertFalse(audit["random_module_imported"])

    def test_20_artifact_membership_and_generation_are_exact(self) -> None:
        payloads = artifact_payloads()
        self.assertEqual(tuple(payloads), ARTIFACT_NAMES)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_artifacts(root)
            self.assertEqual(tuple(sorted(path.name for path in root.iterdir())), tuple(sorted(ARTIFACT_NAMES)))
            for name, expected in payloads.items():
                actual = (root / name).read_text(encoding="utf-8")
                self.assertEqual(actual, canonical_json(expected) + "\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
