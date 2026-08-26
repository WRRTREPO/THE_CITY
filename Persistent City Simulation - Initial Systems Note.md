# Co-op Open-City FPS Simulation Contract — Draft

**Version:** 0.6.0  
**Status:** Foundational player-experience and world-behavior contract. This is not yet a technical implementation specification.  
**Last updated:** 2026-08-26

## Versioning

This contract follows Semantic Versioning (`MAJOR.MINOR.PATCH`). Before version 1.0.0, a minor version records a meaningful expansion or change to the player or world-behavior contract; a patch records clarification that does not change the intended contract. Version 1.0.0 marks a contract ready to govern implementation.

## Changelog

### 0.6.0 — 2026-08-26

- Corrected the distant-simulation language: it evaluates scheduled agent and process commitments; event fronts remain downstream player-readable projections.
- Defined the first required proof kernel: three areas, two factions, police, one fire, and one crew commitment.
- Added determinism, inspectability, emergence, and materialization acceptance criteria for that kernel.

### 0.5.0 — 2026-08-26

- Recast the simulation as a bounded, first-principles causal game rather than a collection of independently authored front timelines.
- Defined the city graph, agents and processes, action economy, gates, thresholds, and bounded strategic choice as the sources of city change.
- Redefined event fronts as player-readable projections of real agent or process commitments.
- Replaced independent front-tempo authoring with scenario-based calibration of action costs, durations, gates, and thresholds.

### 0.4.0 — 2026-08-26

- Replaced the vague causal-density calibration gate with concrete front-tempo contracts that name a player commitment, a front, and an allowed stage transition.
- Clarified that clock ratio follows authored front tempos and player commitments; there is no universal quota of “unattended city history.”

### 0.3.0 — 2026-08-26

- Established causal density as the next mandatory calibration gate: define how much unattended city history may occur during a normal deployment before selecting a real-time-to-active-world-time ratio.
- Deferred further city-system design that depends on time scale until this calibration is resolved.

### 0.2.1 — 2026-08-26

- Clarified that all event fronts are processes within one shared causal machine: each resolution reads and writes the same authoritative city record, so fronts can causally interfere.
- Identified active-world time scale as the next calibration gate because it determines travel pressure, front cadence, crisis density, intelligence staleness, and opportunity cost.

### 0.2.0 — 2026-08-26

- Distinguished authoritative city facts from the crew's intelligence, which may be partial or stale.
- Established geography and aircraft travel as decision latency: distant situations continue to evolve during deployment.
- Established that concurrent event fronts affect shared city conditions rather than operate as isolated missions.
- Clarified the causal-persistence boundary for individual people: generated population becomes persistent only through significance.

### 0.1.0 — 2026-08-26

- Established the initial 1–4 player co-op, open-city FPS simulation contract.
- Defined the persistent hub, 10 × 10 km city scope, and deployment premise.
- Established the active-world clock: the city advances while one or more players are deployed and freezes when none are deployed.
- Defined event fronts as the off-screen engine for consequential city change.
- Defined district, block/site, and crew-bubble ownership of strategic, tactical, and immediate physical consequence.
- Defined promotion before observation, compression of durable results on departure, and the prohibition on rerolling settled outcomes on arrival.
- Added causal LOD: simulation resolution can vary while authoritative city consequences remain persistent.

## Purpose

Define the initial operating model for a 10 × 10 km 3D city that supports a crew of one to four players in first-person play. The crew deploys by aircraft from a persistent hub somewhere within the city and can visit any point on the map.

The city must feel ongoing: conditions and conflicts outside the crew's current operation can change while the players are active. It must not require the entire city to run at full simulation fidelity.

## Player contract

The game promises the following:

- A crew can deploy from its persistent hub to any point in the city.
- The city advances whenever at least one player is deployed, including events that the crew does not witness.
- Players make consequential choices by deciding what to answer, delay, or abandon. An unattended threat may become a settled change in the city.
- When the crew reaches a place, its local state is a playable first-person situation, not merely a strategic report or a retroactive result screen.
- A location never changes its already-settled outcome merely because players have arrived to observe it.
- When nobody is deployed, the city preserves its state and does not advance through real-world time.

The game does not promise that every citizen, vehicle, or room exists at full fidelity at all times. It promises that the city state the players can encounter is coherent, consequential, and faithful to the active-world simulation.

## Core principle

**The city holds facts; the crew's presence renders those facts into detail.**

The authoritative city state is a persistent record of districts, events, infrastructure, factions, and lasting player consequences. A local, high-fidelity scene is a materialization of that record when players can observe or affect it.

Materialization may generate non-causal local detail—such as an exact civilian position, a roadblock layout, or ambient activity—but it must never contradict settled causal facts. The city record establishes what happened and what is true; the local scene expresses it in playable form.

The authoritative record is not the same as the crew's knowledge. Hub intelligence, reports, and field observation are player-facing views of the city that may be incomplete or stale. They must not alter the underlying facts merely by being revealed.

## First-principles city model

No city fact changes merely because a front increments. Every durable change must have an inspectable causal path:

```text
agent or process
  → feasible action
  → action cost and graph path
  → gates satisfied
  → threshold crossed
  → authoritative city fact changes
```

The simulation is a bounded causal game. It represents only the agents, resources, areas, and actions needed to explain consequential city change; it does not attempt to model every person or object continuously.

| Primitive | Contract |
| --- | --- |
| Areas | Districts, blocks, and sites are stateful nodes. They hold control, access, capacity, resources, damage, risk, and other local facts. |
| Graphs | Typed edges connect areas for movement, logistics, information, and influence. Each edge has travel cost, capacity, risk, and an availability state. |
| Agents and processes | Factions, named people, crews, services, and non-human processes such as fire are active only at the fidelity their consequences require. Each has a location or reach, capabilities, resources, commitments, and a state. |
| Action economy | Actions consume time and scarce inputs—people, equipment, supplies, money, influence, access, or attention—and produce changes, transfers, or new commitments. |
| Gates and thresholds | Gates are preconditions for an action; thresholds are state boundaries that change what becomes possible or true. A closed bridge is a gate. Gaining enough local control to seize a site is a threshold. |
| Beliefs and strategy | Each agent acts on incomplete information and a bounded local objective, such as survival, control, wealth, legitimacy, or service restoration. It chooses from feasible actions, not from omniscient global optimization. |

The game's strategic interaction comes from agents competing or cooperating through the same scarce areas, routes, resources, and thresholds. This uses game-theoretic pressure without requiring a city-wide Nash-equilibrium solver: agents make bounded decisions from their own beliefs and incentives, then live with the shared consequences.

### Strategic simulation step

At each scheduled strategic decision point, the off-screen simulation:

1. Applies ongoing flows and previously committed actions along the city graph.
2. Updates area state, gates, and thresholds.
3. Lets eligible agents or processes select feasible next actions from their current beliefs, goals, and resources.
4. Starts, advances, stalls, or ends those actions.
5. Writes the resulting durable facts to the authoritative city record.

The crew bubble executes the same causal logic at much finer physical resolution. It does not become a separate, inconsistent simulation.

## Active-world time

The city uses an active-world clock, never wall-clock time.

- If at least one player is deployed in the city, the active-world clock advances.
- If no player is deployed in the city, the city freezes at its exact current state.
- Returning players resume the saved state exactly. The city does not catch up the real time spent with no players present.
- Every timed city system uses active-world minutes: events, fires, traffic conditions, faction operations, injuries, weather fronts, supply routes, and mission deadlines.

The world does **not** pause around the crew. If the crew becomes occupied with a bank robbery, a gang operation on the other side of the city can progress and resolve during those same active-world minutes.

## Scenario calibration — next design gate

Do not author arbitrary front jumps or a universal quota of unattended history. Calibrate the simulation with named scenarios that specify a concrete city state, a crew commitment, the relevant agents and processes, and the intended consequences.

```text
Initial city state: <areas, routes, resources, agent beliefs, gates, thresholds>
Crew commitment: <for example, flight or bank robbery>
Unattended agents/processes: <their feasible actions and costs>
Expected result: <which valid actions complete, which gates or thresholds change, and which durable facts result>
```

For example, while the crew handles a bank robbery, a gang can only displace a rival patrol if it has the required people, access route, local intelligence, and enough time to pay the action's cost. It may seize territory only if that action's additional gates and control threshold are also satisfied. The result follows from the city machine; it is not an arbitrary stage allowance.

Build a small reference set of such scenarios before fixing clock ratio. Use them to tune action costs, durations, resource rates, gate requirements, and threshold values. Aircraft travel, front cadence, information staleness, and active-world time scale are outputs of that model and its tested player pressure.

### First required proof kernel

Before expanding to the full city, prove the model in one deliberately small scenario:

- Three connected areas, with at least one shared route or gate whose state can change.
- Two factions with competing objectives and constrained resources.
- A police or public-service agent whose response depends on the graph and current access.
- One fire process that can alter area and route state.
- One named crew commitment that occupies player attention while the rest of the scenario advances.

The scenario is successful only if the same seeded starting state produces the same causal record, a later inspection can explain each durable change through its agent/process and valid action chain, and the resulting player-visible front is a truthful projection of those facts. It must be possible—but not directly scripted—for the fire to alter access, alter a response, shift a faction contest, and change a district or site condition. When the crew arrives, the materialized FPS scene must express that recorded result.

If this kernel cannot produce a consequential, inspectable outcome without a direct `front.stage++` rule, expanding the map will not solve the problem.

## Persistent hub and deployment

The hub is a fixed, persistent location within the city. It is the crew's operational base and should hold the durable state that belongs to the crew rather than to a particular field operation:

- aircraft, deployment and extraction;
- preparation, intelligence, equipment, upgrades, and crew history;
- the city situation as currently known to the crew; and
- consequences returned from prior operations.

The hub should make distance, travel, and deployment choice legible without making any map location unreachable. The crew's selection of one operation is also a decision not to address other active situations.

Distance is decision latency. Aircraft travel consumes active-world time, so a situation 9 km away is not strategically equivalent to one 800 m away: distant fronts continue to advance during the journey. The hub must communicate enough intelligence for the crew to understand that trade-off without converting the city into a static mission menu.

## City simulation hierarchy

| Scale | Persistent state | Simulation while the city is active |
| --- | --- | --- |
| City | time, weather, economy, major infrastructure, city-wide faction posture | consequential city-wide changes |
| District | control, threat, population and traffic pressure, active incidents, resource flow | low-cost event-front resolution |
| Block / site | damage, named locations, local objectives, important witnesses, tactical consequences | scene materialization when relevant |
| Crew bubble | exact player actions and immediate world state | full AI, combat, traffic, physics, interiors, and interaction |

Districts are the primary unit of strategic consequence. Blocks and sites are the primary unit of tactical consequence. Individual citizens persist only when the game has made them significant.

## Causal identity

Most population can remain procedural and non-persistent. An individual crosses into the authoritative city record only when the game makes that person causally significant: for example, as a witness, hostage, informant, victim, rescued civilian, named enemy, or persistent relationship. This permits population scale without requiring every generated citizen to become permanent history.

## Event fronts

An event front is a player-readable projection of an ongoing agent or process commitment. It makes an operation, crisis, or opportunity legible without becoming an independent script. Its stages describe real actions, gates, and thresholds in the authoritative city record. Multiple fronts can coexist and affect the same shared city conditions—such as police pressure, road access, district mood, resources, and faction strength—rather than behaving as isolated missions.

Every front reads from and writes to the same authoritative city record. A resolved fire can alter road access for a supply convoy; a police response can weaken a gang operation; a player intervention can change the conditions used by later fronts. The city is one shared causal machine, not many independent mission scripts running in parallel.

Example: a gang expansion front in Docklands.

1. Scout target blocks.
2. Pressure local businesses.
3. Drive out rival patrols.
4. Seize turf.
5. Consolidate control.

At each decision point, the participating agent or process evaluates feasible actions from its beliefs, goals, resources, graph access, and current gates. It then commits, advances, stalls, branches, or resolves accordingly. The front display changes only when those underlying facts change. Distant causal state advances at scheduled strategic decision points, not through a continuous full-fidelity simulation.

If a front reaches a consequence stage without intervention, its district record changes. A takeover might increase gang control, weaken a rival, alter business behavior, and redirect local traffic. Players later flying to the district find a detailed local scene that reflects those settled facts. Observation never rerolls a settled outcome. Players can still respond afterward, but doing so begins a new intervention or counter-operation; it does not revise the city's established history.

## Simulation fidelity and off-screen advancement

The city clock remains one shared clock while players are active. Simulation resolution changes with observation and potential interaction.

| Relation to crew | Resolution method |
| --- | --- |
| Current operation | Continuous, high-frequency simulation. |
| Approaching or nearby area | Low-frequency updates; promote to detailed simulation before observation or interaction is possible. |
| Distant but relevant district | Evaluate scheduled agent and process commitments at their strategic decision points, often several minutes apart. |
| Distant routine system | Jump directly to its next consequential decision point rather than simulate individual actors. |

Off-screen systems should be event-driven, not frame-driven. A gang commitment does not need every gang member simulated every second. It can move from `pressuring businesses at 14:10` to `rival patrol displaced at 14:20` after valid actions resolve against its stored inputs, graph access, gates, and thresholds. The player-facing gang front then reflects that result.

This preserves an ongoing city while keeping distant simulation inexpensive and understandable.

### Causal LOD

This is more than conventional visual level of detail. It is **causal LOD**: computational resolution can decrease with distance from the crew, while the authority and persistence of consequences do not. Graphics, individual AI, physics, and exact scene detail may be simplified or absent until needed; the city facts and the rules that advance them remain authoritative.

## Materialization and handoff

**Promote a location before players can meaningfully observe or affect it.**

As the crew flies toward a destination, the approaching district and its likely operation area are brought from coarse state into finer simulation ahead of the aircraft. The resolved city record becomes a concrete scene: road closures, local AI, fire locations, businesses, enemies, witnesses, traffic, and opportunities. The materialization process may choose the unimportant physical particulars, but it cannot change the causal outcome that the city record has already settled.

The city must never reveal an outcome and then revise it because players arrived. The materialized scene is a faithful local expression of the authoritative state at the time the crew could affect it.

When players leave an area, compress meaningful results back into the persistent record: damage, casualties where relevant, seized resources, changed faction strength, altered access routes, completed or worsened fronts, and persistent site changes.

## World lifecycle

```text
Dormant
  No players deployed in the city.
  The saved city state is authoritative and does not advance.

Active
  At least one player is deployed.
  The active-world clock advances; local and off-screen simulation resolve at their appropriate resolutions.

Transition
  Deployment, landing, extraction, or final departure.
  Promote approaching locations before observation; commit durable consequences before dormancy.
```

## Design consequences

- The crew cannot solve every crisis. Attending one event may allow another to resolve.
- Distance and aircraft deployment matter because they determine when an area becomes observable and intervenable.
- A city-wide simulation remains tractable because it stores meaningful state and scheduled decisions, not a frame-by-frame model of every NPC.
- Persistence is legible: later scenes make visible the consequences of what the crew chose to address, ignore, or cause.
- City pressures are not disposable missions. Ignored fronts can become geography, faction control, infrastructure damage, economic conditions, or later operations.

## Questions to settle next

1. Prove the first required kernel—three areas, two factions, police, one fire, and one crew commitment—before expanding the reference scenario set or choosing active-world time scale.
2. Does deployment from the hub count as active city time from takeoff, or only after entering the field operation?
3. Which consequences are permanent, which decay, and which can be reversed?
4. How many simultaneous event fronts should be visible to the crew at one time?
5. What information about distant fronts is available at the hub versus discovered only in the field?
