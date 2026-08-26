import unittest

from kernel import Kernel, run_scenario


class AshCrossingKernelTests(unittest.TestCase):
    def test_primary_run_indirectly_changes_ownership(self) -> None:
        result = run_scenario(include_fire=True)["payload"]
        world = result["world"]
        self.assertFalse(world["routes"]["E_AB"]["open"])
        self.assertEqual(world["agents"]["police_unit_01"]["location"], "A")
        self.assertEqual(world["agents"]["police_unit_01"]["availability"], "available")
        self.assertEqual(world["agents"]["police_unit_01"]["dispatch_to_C"], {"result": "failed_gate", "failed_gate": "E_AB.open"})
        self.assertEqual(world["areas"]["C"]["gang_control"], 74)
        self.assertEqual(world["areas"]["C"]["rival_control"], 26)
        self.assertEqual(world["areas"]["C"]["owner"], "gang")
        self.assertEqual(world["fronts"]["gang_control_C"], "gang_controls_docklands_yard")
        self.assertEqual(world["agents"]["gang_docklands"]["personnel_reserved"], 0)
        self.assertEqual(world["agents"]["rival_docklands"]["personnel_reserved"], 0)
        self.assertEqual(world["commitments"]["gang_docklands.seize_C_t0"]["state"], "succeeded")
        self.assertEqual(world["commitments"]["defense_against_seize_C_t0"]["state"], "expired")

    def test_removing_only_fire_reverses_ownership_result(self) -> None:
        result = run_scenario(include_fire=False)["payload"]
        world = result["world"]
        self.assertTrue(world["routes"]["E_AB"]["open"])
        self.assertEqual(world["agents"]["police_unit_01"]["location"], "C")
        self.assertEqual(world["agents"]["police_unit_01"]["availability"], "deployed")
        self.assertEqual(world["areas"]["C"]["police_present"], 1)
        self.assertEqual(world["areas"]["C"]["owner"], "contested")
        self.assertNotIn("gang_control_C", world["fronts"])
        self.assertEqual(world["commitments"]["gang_docklands.seize_C_t0"]["state"], "failed")

    def test_replays_are_byte_equivalent(self) -> None:
        first = run_scenario(include_fire=True)
        second = run_scenario(include_fire=True)
        self.assertEqual(first["canonical_json"], second["canonical_json"])
        self.assertEqual(first["sha256"], second["sha256"])

    def test_counterfactual_traversal_order_and_terminal_cleanup(self) -> None:
        result = run_scenario(include_fire=False)["payload"]
        world = result["world"]
        sequence = [entry["canonical_execution_sequence"] for entry in result["ledger"]]
        self.assertLess(sequence.index("t1/15/B/police_unit_01.exit_E_AB"), sequence.index("t1/20/B/police_unit_01.enter_E_BC"))
        self.assertLess(sequence.index("t1/20/B/police_unit_01.enter_E_BC"), sequence.index("t2/15/C/police_unit_01.arrive_at_C"))
        self.assertLess(sequence.index("t2/15/C/police_unit_01.arrive_at_C"), sequence.index("t2/40/C/gang_docklands.complete_seize_C"))
        self.assertEqual(world["routes"]["E_AB"]["leases"], [])
        self.assertEqual(world["routes"]["E_BC"]["leases"], [])
        self.assertEqual(world["agents"]["gang_docklands"]["personnel_reserved"], 0)
        self.assertEqual(world["agents"]["rival_docklands"]["personnel_reserved"], 0)
        self.assertEqual(world["commitments"]["police_dispatch_C_t0"]["state"], "succeeded")
        self.assertEqual(world["commitments"]["police_dispatch_C_t0"]["terminal_disposition"], "unit_transformed_to_deployed_police_presence_C")

    def test_future_edge_state_does_not_block_dispatch_start(self) -> None:
        kernel = Kernel(include_fire=False)
        kernel.world["routes"]["E_BC"]["open"] = False
        kernel.snapshot("t0")
        kernel.police_dispatch()
        self.assertIn("police_dispatch_C_t0", kernel.world["commitments"])
        self.assertEqual(kernel.world["commitments"]["police_dispatch_C_t0"]["state"], "active")
        dispatch = kernel.ledger[-1]
        self.assertNotIn("E_BC.open", dispatch["gates"])

    def test_mid_route_e_bc_closure_terminates_and_releases_police(self) -> None:
        result = run_scenario(include_fire=False, close_e_bc_at_t1=True)["payload"]
        world = result["world"]
        police = world["agents"]["police_unit_01"]
        commitment = world["commitments"]["police_dispatch_C_t0"]
        self.assertEqual(police["location"], "B")
        self.assertEqual(police["availability"], "available")
        self.assertEqual(commitment["state"], "failed")
        self.assertEqual(commitment["last_valid_location"], "B")
        self.assertEqual(world["routes"]["E_AB"]["leases"], [])
        self.assertEqual(world["routes"]["E_BC"]["leases"], [])
        enter = next(entry for entry in result["ledger"] if entry["action_id"] == "police_unit_01.enter_E_BC")
        self.assertEqual(enter["result"], "failed_gate")
        self.assertEqual(enter["mutation"]["police_dispatch_C_t0"], "failed")
        self.assertFalse(any(entry["action_id"] == "police_unit_01.arrive_at_C" for entry in result["ledger"]))

    def test_ledger_contains_required_provenance(self) -> None:
        result = run_scenario(include_fire=True)["payload"]
        required = {
            "decision_time",
            "simulation_phase",
            "canonical_execution_sequence",
            "simulation_version",
            "actor_or_process",
            "snapshot_reference",
            "observed_inputs",
            "believed_inputs",
            "eligible_actions",
            "selected_action",
            "resources",
            "gates",
            "result",
            "pre_state_hash",
            "post_state_hash",
            "downstream_eligibility_changes",
        }
        self.assertTrue(result["ledger"])
        for entry in result["ledger"]:
            self.assertTrue(required.issubset(entry))
        dispatch = next(entry for entry in result["ledger"] if entry["action_id"] == "police_unit_01.dispatch_to_C")
        self.assertEqual(dispatch["result"], "failed_gate")
        self.assertFalse(dispatch["gates"]["E_AB.open"])

    def test_materialization_does_not_contradict_authoritative_record(self) -> None:
        primary = run_scenario(include_fire=True)["payload"]["materialization"]
        self.assertFalse(primary["B"]["ash_bridge_passable"])
        self.assertFalse(primary["B"]["police_route_displayed_open"])
        self.assertEqual(primary["C"]["owner"], "gang")
        self.assertTrue(primary["C"]["gang_occupation"])
        self.assertFalse(primary["C"]["police_present"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
