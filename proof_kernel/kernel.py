"""Deterministic reference implementation of the frozen Ash Crossing proof kernel.

This is proof code for the v0.1.0 scenario, not an Unreal integration.
"""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Callable


SCENARIO_ID = "ash-crossing-v1"
SCENARIO_VERSION = "0.1.0"
SIMULATION_VERSION = "0.7.0-draft.4"
SEED = "ash-crossing-v1/0001"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def state_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def tie_break(sequence: str) -> str:
    return hashlib.sha256(f"{SEED}|{sequence}".encode("utf-8")).hexdigest()[:16]


def initial_world() -> dict[str, Any]:
    return {
        "clock": "t0",
        "areas": {
            "A": {"name": "Inland Hub"},
            "B": {"name": "Bridgehead", "fire_intensity": 4, "fuel": 1},
            "C": {
                "name": "Docklands Yard",
                "gang_control": 62,
                "rival_control": 38,
                "police_present": 0,
                "owner": "contested",
            },
        },
        "routes": {
            "E_AB": {
                "open": True,
                "capacity": 1,
                "leases": [],
                "travel_minutes": 1,
            },
            "E_BC": {
                "open": True,
                "capacity": 2,
                "leases": [],
                "travel_minutes": 1,
            },
        },
        "agents": {
            "gang_docklands": {
                "location": "C",
                "personnel_available": 6,
                "personnel_reserved": 0,
                "equipment": 1,
                "local_intelligence": 1,
                "supply": 1,
            },
            "rival_docklands": {
                "location": "C",
                "personnel_available": 4,
                "personnel_reserved": 0,
                "supply": 1,
            },
            "police_unit_01": {
                "location": "A",
                "availability": "available",
                "units": 1,
            },
        },
        "crew": {
            "location": "A",
            "commitment": "bank_containment",
            "active_from": "t0",
            "active_until": "t2",
            "available_for_C": False,
        },
        "commitments": {},
        "fronts": {},
    }


@dataclass
class Kernel:
    include_fire: bool
    world: dict[str, Any] = field(default_factory=initial_world)
    ledger: list[dict[str, Any]] = field(default_factory=list)
    snapshots: dict[str, str] = field(default_factory=dict)
    snapshot_states: dict[str, dict[str, Any]] = field(default_factory=dict)

    def snapshot(self, time: str) -> str:
        self.world["clock"] = time
        self.snapshot_states[time] = copy.deepcopy(self.world)
        reference = state_hash(self.world)
        self.snapshots[time] = reference
        return reference

    def _append(
        self,
        *,
        time: str,
        phase: int,
        sequence: str,
        actor: str,
        commitment: str | None,
        action: str,
        observed: dict[str, Any],
        eligible_actions: list[str],
        gates: dict[str, bool],
        resources: dict[str, Any],
        effect: Callable[[], dict[str, Any]] | None,
        downstream: list[str],
        believed_inputs: dict[str, Any] | None = None,
        on_failure: Callable[[], dict[str, Any]] | None = None,
    ) -> bool:
        before = state_hash(self.world)
        passed = all(gates.values())
        mutation = effect() if passed and effect else (on_failure() if not passed and on_failure else {})
        after = state_hash(self.world)
        result = "committed" if passed else "failed_gate"
        self.ledger.append(
            {
                "decision_time": time,
                "simulation_phase": phase,
                "canonical_execution_sequence": sequence,
                "simulation_version": SIMULATION_VERSION,
                "actor_or_process": actor,
                "commitment_id": commitment,
                "action_id": action,
                "snapshot_reference": self.snapshots[time],
                "observed_inputs": observed,
                "believed_inputs": copy.deepcopy(observed if believed_inputs is None else believed_inputs),
                "eligible_actions": eligible_actions,
                "selected_action": action,
                "deterministic_tie_break": tie_break(sequence),
                "random_draw_reference": "none",
                "resources": resources,
                "gates": gates,
                "result": result,
                "mutation": mutation,
                "pre_state_hash": before,
                "post_state_hash": after,
                "downstream_eligibility_changes": downstream,
            }
        )
        return passed

    def fire_spread(self) -> None:
        def effect() -> dict[str, Any]:
            bridgehead = self.world["areas"]["B"]
            bridgehead["fuel"] -= 1
            bridgehead["fire_intensity"] += 1
            route = self.world["routes"]["E_AB"]
            route["open"] = False
            route["capacity"] = 0
            return {"B.fire_intensity": 5, "E_AB.open": False, "E_AB.capacity": 0}

        self._append(
            time="t0",
            phase=10,
            sequence="t0/10/B/fire_bridgehead.spread",
            actor="fire_bridgehead",
            commitment=None,
            action="fire_bridgehead.spread",
            observed={"intensity": 4, "fuel": 1},
            eligible_actions=["fire_bridgehead.spread"],
            gates={"fuel >= 1": True, "intensity == 4": True},
            resources={"fuel": {"consumed": 1}},
            effect=effect,
            downstream=["E_AB.entry_gate_changed"],
        )

    def test_close_e_bc_at_t1(self) -> None:
        """Test-only route mutation used to prove mid-route failure cleanup."""

        route = self.world["routes"]["E_BC"]

        def effect() -> dict[str, Any]:
            route["open"] = False
            route["capacity"] = 0
            return {"E_BC.open": False, "E_BC.capacity": 0}

        self._append(
            time="t1",
            phase=10,
            sequence="t1/10/B/test_harness.close_E_BC",
            actor="test_harness",
            commitment=None,
            action="test_harness.close_E_BC",
            observed={"E_BC.open": self.snapshot_states["t1"]["routes"]["E_BC"]["open"]},
            eligible_actions=["test_harness.close_E_BC"],
            gates={"test hook enabled": True},
            resources={},
            effect=effect,
            downstream=["police_dispatch_C_t0.entry_gate:E_BC"],
        )

    def police_dispatch(self) -> None:
        police = self.world["agents"]["police_unit_01"]
        start_snapshot = self.snapshot_states["t0"]
        observed = {
            "E_AB.open": start_snapshot["routes"]["E_AB"]["open"],
            "E_AB.capacity": start_snapshot["routes"]["E_AB"]["capacity"],
            "police_availability": start_snapshot["agents"]["police_unit_01"]["availability"],
        }
        route_ab = self.world["routes"]["E_AB"]
        gates = {
            "police unit available": police["availability"] == "available",
            "E_AB.open": route_ab["open"],
            "E_AB.capacity >= 1": len(route_ab["leases"]) < route_ab["capacity"],
        }

        def effect() -> dict[str, Any]:
            police["availability"] = "reserved"
            route_ab["leases"].append("police_dispatch_C_t0:E_AB")
            self.world["commitments"]["police_dispatch_C_t0"] = {
                "owner": "police_unit_01",
                "state": "active",
                "route": ["E_AB", "E_BC"],
                "departure": "t0",
                "arrival": "t2",
                "current_segment": "E_AB",
                "last_valid_location": "A",
                "unit_reserved": True,
            }
            return {
                "commitment": "police_dispatch_C_t0 active",
                "E_AB.capacity_lease": "police_dispatch_C_t0:E_AB",
            }

        def failure_effect() -> dict[str, Any]:
            failed_gate = next(gate for gate, passed in gates.items() if not passed)
            police["dispatch_to_C"] = {"result": "failed_gate", "failed_gate": failed_gate}
            police["availability"] = "available"
            return {"police.dispatch_to_C": "failed_gate", "failed_gate": failed_gate}

        self._append(
            time="t0",
            phase=20,
            sequence="t0/20/A/police_unit_01.dispatch_to_C",
            actor="police_unit_01",
            commitment="police_dispatch_C_t0",
            action="police_unit_01.dispatch_to_C",
            observed=observed,
            eligible_actions=["police_unit_01.dispatch_to_C"],
            gates=gates,
            resources={"police_unit": {"reserved_on_success": 1}, "E_AB": {"lease_on_success": 1}},
            effect=effect,
            downstream=["police_dispatch_C_t0.progress:t1/15"],
            on_failure=failure_effect,
        )

    def rival_defend(self) -> None:
        rival = self.world["agents"]["rival_docklands"]
        gates = {
            "personnel >= 3": rival["personnel_available"] >= 3,
            "supply >= 1": rival["supply"] >= 1,
        }

        def effect() -> dict[str, Any]:
            rival["personnel_available"] -= 3
            rival["personnel_reserved"] += 3
            rival["supply"] -= 1
            self.world["commitments"]["defense_against_seize_C_t0"] = {
                "owner": "rival_docklands",
                "state": "active",
                "target": "gang_docklands.seize_C_t0",
                "magnitude": 2,
                "expires_with_target": True,
            }
            return {"defense_against_seize_C_t0": "active", "magnitude": 2}

        self._append(
            time="t0",
            phase=30,
            sequence="t0/30/C/rival_docklands.defend_C",
            actor="rival_docklands",
            commitment="defense_against_seize_C_t0",
            action="rival_docklands.defend_C",
            observed={"rival_personnel": 4, "rival_supply": 1, "target_action": "gang_docklands.seize_C_t0"},
            eligible_actions=["rival_docklands.defend_C"],
            gates=gates,
            resources={"personnel": {"reserved": 3}, "supply": {"consumed": 1}},
            effect=effect,
            downstream=["gang_docklands.complete_seize_C defense modifier"],
        )

    def gang_begin_seize(self) -> None:
        gang = self.world["agents"]["gang_docklands"]
        control = self.world["areas"]["C"]["gang_control"]
        gates = {
            "personnel >= 5": gang["personnel_available"] >= 5,
            "equipment >= 1": gang["equipment"] >= 1,
            "local_intelligence >= 1": gang["local_intelligence"] >= 1,
            "gang_control >= 60": control >= 60,
            "supply >= 1": gang["supply"] >= 1,
        }

        def effect() -> dict[str, Any]:
            gang["personnel_available"] -= 5
            gang["personnel_reserved"] += 5
            gang["supply"] -= 1
            self.world["commitments"]["gang_docklands.seize_C_t0"] = {
                "owner": "gang_docklands",
                "state": "active",
                "completion": "t2",
                "personnel_reserved": 5,
                "supply_consumed": 1,
            }
            return {"gang_docklands.seize_C_t0": "active", "completion": "t2"}

        self._append(
            time="t0",
            phase=30,
            sequence="t0/30/C/gang_docklands.begin_seize_C",
            actor="gang_docklands",
            commitment="gang_docklands.seize_C_t0",
            action="gang_docklands.begin_seize_C",
            observed={"gang_control": 62, "personnel": 6, "equipment": 1, "intel": 1},
            eligible_actions=["gang_docklands.begin_seize_C"],
            gates=gates,
            resources={"personnel": {"reserved": 5}, "supply": {"consumed": 1}},
            effect=effect,
            downstream=["gang_docklands.complete_seize_C:t2"],
        )

    def derived_state(self, time: str) -> None:
        docklands = self.world["areas"]["C"]
        gates = {
            "gang_control >= 70": docklands["gang_control"] >= 70,
            "police_present_C == 0": docklands["police_present"] == 0,
        }

        def effect() -> dict[str, Any]:
            docklands["owner"] = "gang"
            self.world["fronts"]["gang_control_C"] = "gang_controls_docklands_yard"
            return {"C.owner": "gang", "fronts.gang_control_C": "exposed"}

        self._append(
            time=time,
            phase=90,
            sequence=f"{time}/90/C/derived_state",
            actor="derived_state",
            commitment=None,
            action="derived_state.evaluate_C_owner",
            observed={"gang_control": docklands["gang_control"], "police_present": docklands["police_present"]},
            eligible_actions=["derived_state.evaluate_C_owner"],
            gates=gates,
            resources={},
            effect=effect,
            downstream=["front:gang_control_C"] if all(gates.values()) else [],
        )

    def police_progress_t1(self) -> None:
        commitment = self.world["commitments"].get("police_dispatch_C_t0")
        if not commitment or commitment["state"] != "active":
            return
        route_ab = self.world["routes"]["E_AB"]
        police = self.world["agents"]["police_unit_01"]

        def exit_effect() -> dict[str, Any]:
            route_ab["leases"].remove("police_dispatch_C_t0:E_AB")
            police["location"] = "B"
            commitment["last_valid_location"] = "B"
            commitment["current_segment"] = None
            return {"police.location": "B", "E_AB.capacity_lease": "released"}

        self._append(
            time="t1",
            phase=15,
            sequence="t1/15/B/police_unit_01.exit_E_AB",
            actor="police_unit_01",
            commitment="police_dispatch_C_t0",
            action="police_unit_01.exit_E_AB",
            observed={"current_segment": "E_AB", "last_valid_location": "A"},
            eligible_actions=["police_unit_01.exit_E_AB"],
            gates={"traversal active": commitment["state"] == "active", "current_segment == E_AB": commitment["current_segment"] == "E_AB"},
            resources={"E_AB": {"lease_released": 1}},
            effect=exit_effect,
            downstream=["police_dispatch_C_t0.enter_E_BC:t1/20"],
        )

        route_bc = self.world["routes"]["E_BC"]
        t1_snapshot = self.snapshot_states["t1"]
        gates = {
            "traversal active": commitment["state"] == "active",
            "E_BC.open": route_bc["open"],
            "E_BC.capacity >= 1": len(route_bc["leases"]) < route_bc["capacity"],
        }

        def enter_effect() -> dict[str, Any]:
            route_bc["leases"].append("police_dispatch_C_t0:E_BC")
            commitment["current_segment"] = "E_BC"
            return {"E_BC.capacity_lease": "police_dispatch_C_t0:E_BC"}

        def enter_failure_effect() -> dict[str, Any]:
            lease = "police_dispatch_C_t0:E_BC"
            if lease in route_bc["leases"]:
                route_bc["leases"].remove(lease)
            commitment["state"] = "failed"
            commitment["current_segment"] = None
            commitment["last_valid_location"] = "B"
            commitment["terminal_disposition"] = "unit_released_at_B_after_E_BC_entry_failure"
            police["location"] = "B"
            police["availability"] = "available"
            return {
                "police_dispatch_C_t0": "failed",
                "police.location": "B",
                "police.availability": "available",
                "E_BC.capacity_lease": "released_if_held",
            }

        self._append(
            time="t1",
            phase=20,
            sequence="t1/20/B/police_unit_01.enter_E_BC",
            actor="police_unit_01",
            commitment="police_dispatch_C_t0",
            action="police_unit_01.enter_E_BC",
            observed={
                "police_location": t1_snapshot["agents"]["police_unit_01"]["location"],
                "E_BC.open": t1_snapshot["routes"]["E_BC"]["open"],
            },
            eligible_actions=["police_unit_01.enter_E_BC"],
            gates=gates,
            resources={"E_BC": {"lease_on_success": 1}},
            effect=enter_effect,
            downstream=["police_unit_01.arrive_at_C:t2/15"],
            on_failure=enter_failure_effect,
        )

    def police_arrive_t2(self) -> None:
        commitment = self.world["commitments"].get("police_dispatch_C_t0")
        if not commitment or commitment["state"] != "active":
            return
        route_bc = self.world["routes"]["E_BC"]
        police = self.world["agents"]["police_unit_01"]
        gates = {
            "traversal active": commitment["state"] == "active",
            "current_segment == E_BC": commitment["current_segment"] == "E_BC",
        }

        def effect() -> dict[str, Any]:
            route_bc["leases"].remove("police_dispatch_C_t0:E_BC")
            police["location"] = "C"
            police["availability"] = "deployed"
            commitment["state"] = "succeeded"
            commitment["terminal_disposition"] = "unit_transformed_to_deployed_police_presence_C"
            self.world["areas"]["C"]["police_present"] = 1
            return {"police.location": "C", "police_present_C": 1, "E_BC.capacity_lease": "released"}

        self._append(
            time="t2",
            phase=15,
            sequence="t2/15/C/police_unit_01.arrive_at_C",
            actor="police_unit_01",
            commitment="police_dispatch_C_t0",
            action="police_unit_01.arrive_at_C",
            observed={"current_segment": commitment["current_segment"], "police_location": police["location"]},
            eligible_actions=["police_unit_01.arrive_at_C"],
            gates=gates,
            resources={"E_BC": {"lease_released": 1}, "police_unit": {"transformed": "deployed_C"}},
            effect=effect,
            downstream=["gang_docklands.complete_seize_C gate:police_present_C"],
        )

    def gang_complete_seize(self) -> None:
        gang_commitment = self.world["commitments"]["gang_docklands.seize_C_t0"]
        defense = self.world["commitments"]["defense_against_seize_C_t0"]
        gang = self.world["agents"]["gang_docklands"]
        rival = self.world["agents"]["rival_docklands"]
        docklands = self.world["areas"]["C"]
        t2_snapshot = self.snapshot_states["t2"]
        gates = {
            "gang seizure active": gang_commitment["state"] == "active",
            "police_present_C == 0": docklands["police_present"] == 0,
        }

        def cleanup(outcome: str) -> None:
            gang["personnel_available"] += gang["personnel_reserved"]
            gang["personnel_reserved"] = 0
            rival["personnel_available"] += rival["personnel_reserved"]
            rival["personnel_reserved"] = 0
            gang_commitment["state"] = outcome
            gang_commitment["terminal_disposition"] = "personnel_released_supply_consumed"
            defense["state"] = "expired"
            defense["terminal_disposition"] = "rival_personnel_released"

        def effect() -> dict[str, Any]:
            transfer = 14 - defense["magnitude"]
            docklands["gang_control"] += transfer
            docklands["rival_control"] -= transfer
            cleanup("succeeded")
            return {"control_transfer": transfer, "gang_commitment": "succeeded", "defense": "expired"}

        before = state_hash(self.world)
        passed = all(gates.values())
        mutation = effect() if passed else {}
        if not passed:
            cleanup("failed")
            mutation = {"control_transfer": 0, "gang_commitment": "failed", "defense": "expired"}
        after = state_hash(self.world)
        sequence = "t2/40/C/gang_docklands.complete_seize_C"
        self.ledger.append(
            {
                "decision_time": "t2",
                "simulation_phase": 40,
                "canonical_execution_sequence": sequence,
                "simulation_version": SIMULATION_VERSION,
                "actor_or_process": "gang_docklands",
                "commitment_id": "gang_docklands.seize_C_t0",
                "action_id": "gang_docklands.complete_seize_C",
                "snapshot_reference": self.snapshots["t2"],
                "observed_inputs": {
                    "police_present_C": t2_snapshot["areas"]["C"]["police_present"],
                    "defense_magnitude": t2_snapshot["commitments"]["defense_against_seize_C_t0"]["magnitude"],
                },
                "believed_inputs": {
                    "police_present_C": t2_snapshot["areas"]["C"]["police_present"],
                    "defense_magnitude": t2_snapshot["commitments"]["defense_against_seize_C_t0"]["magnitude"],
                },
                "eligible_actions": ["gang_docklands.complete_seize_C"],
                "selected_action": "gang_docklands.complete_seize_C",
                "deterministic_tie_break": tie_break(sequence),
                "random_draw_reference": "none",
                "resources": {
                    "gang_personnel": {"released": 5},
                    "gang_supply": {"consumed_not_refunded": 1},
                    "rival_personnel": {"released": 3},
                },
                "gates": gates,
                "result": "committed" if passed else "failed_gate",
                "mutation": mutation,
                "pre_state_hash": before,
                "post_state_hash": after,
                "downstream_eligibility_changes": ["derived_state.evaluate_C_owner"],
            }
        )

    def materialize(self) -> dict[str, Any]:
        bridgehead = self.world["areas"]["B"]
        docklands = self.world["areas"]["C"]
        return {
            "B": {
                "ash_bridge_passable": self.world["routes"]["E_AB"]["open"],
                "fire_intensity": bridgehead["fire_intensity"],
                "police_route_displayed_open": self.world["routes"]["E_AB"]["open"],
            },
            "C": {
                "owner": docklands["owner"],
                "police_present": docklands["police_present"],
                "gang_occupation": docklands["owner"] == "gang",
                "rival_displaced": docklands["owner"] == "gang",
            },
        }


def run_scenario(include_fire: bool = True, close_e_bc_at_t1: bool = False) -> dict[str, Any]:
    kernel = Kernel(include_fire=include_fire)
    kernel.snapshot("t0")
    if include_fire:
        kernel.fire_spread()
    kernel.police_dispatch()
    kernel.rival_defend()
    kernel.gang_begin_seize()
    kernel.derived_state("t0")

    kernel.snapshot("t1")
    if close_e_bc_at_t1:
        kernel.test_close_e_bc_at_t1()
    kernel.police_progress_t1()

    kernel.snapshot("t2")
    kernel.police_arrive_t2()
    kernel.gang_complete_seize()
    kernel.derived_state("t2")

    payload = {
        "scenario_id": SCENARIO_ID,
        "scenario_version": SCENARIO_VERSION,
        "simulation_version": SIMULATION_VERSION,
        "seed": SEED,
        "input_sequence": [
            "t0:crew_01_to_04.accept(bank_containment)",
            f"t0:fire_spread={include_fire}",
            f"t1:test_close_E_BC={close_e_bc_at_t1}",
        ],
        "world": copy.deepcopy(kernel.world),
        "ledger": copy.deepcopy(kernel.ledger),
        "materialization": kernel.materialize(),
    }
    return {"payload": payload, "canonical_json": canonical_json(payload), "sha256": state_hash(payload)}
