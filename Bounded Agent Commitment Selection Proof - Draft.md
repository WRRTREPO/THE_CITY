# Bounded Agent Commitment Selection Proof

**Version:** 0.1.0-draft.0
**Status:** Candidate scope under review. Implementation is not authorized.
**Candidate simulation version:** 0.7.0-draft.25
**Parent:** [Co-op Open-City FPS Simulation — v0.7 Working Continuation](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)

## Why this is next

The sealed interference proof establishes that independently defined
commitments compose once they exist. The remaining missing primitive is how an
agent lawfully creates a commitment in the first place.

The next proof must establish:

> **An agent may select one feasible action from a bounded perception, then propose a commitment that the canonical transaction layer alone may create.**

This begins proving the first-principles loop rather than adding city content:

```text
authoritative state
        ↓
bounded agent perception
        ↓
feasible actions + ordinary gates + explicit costs
        ↓
deterministic selection
        ↓
commitment proposal
        ↓
canonical revalidation and commitment creation
```

## Candidate fixture

All nouns are proof fixtures. They do not create production city ontology,
utility systems, or action classes.

```yaml
agent:
  id: agent_P
  location: A
  available_transport: 1
  goal: preserve_operational_capacity

areas_and_graph:
  A_to_B:
    open: true
    capacity: 1
    travel_cost: 2

actions:
  secure_remote_capacity:
    requires:
      - A_to_B.open
      - A_to_B.capacity >= 1
      - agent_P.available_transport >= 1
    cost: reserve one transport unit
    goal_value: 8
    risk_cost: 1
    travel_cost: 2

  stabilize_local_capacity:
    requires:
      - local_capacity_available
    cost: reserve one local work unit
    goal_value: 5
    risk_cost: 1
    travel_cost: 0
```

The candidate score law is explicit and deterministic:

```text
score = goal_value - risk_cost - travel_cost
select highest-scoring feasible action
tie → stable action identifier ordering
```

The fixture exists only to prove bounded perception, feasibility, cost, and
selection. It is not a production utility function or a claim about what real
agents value.

## Perception boundary

The selector does not receive the whole city record. It receives one declared
projection:

```yaml
agent_P_perception:
  visible:
    - A_to_B.open
    - A_to_B.capacity
    - agent_P.available_transport
    - local_capacity_available
    - declared action values and costs
  excluded:
    - unrelated distant city facts
    - other agents' private state
    - hidden fixture fact H
```

The initial proof uses current observations only. It does **not** introduce
stale beliefs, misinformation, memory, or a production intelligence model.

## Candidate runs

### Primary — remote action selected

```text
route open; transport available; local capacity available
        ↓
remote score = 8 - 1 - 2 = 5
local score = 5 - 1 - 0 = 4
        ↓
agent_P selects secure_remote_capacity
        ↓
canonical transaction revalidates its ordinary gates
        ↓
remote commitment is created and transport is reserved
```

### Feasibility counterfactual — route changes

```text
change only A_to_B.open = false
        ↓
remote action becomes infeasible through its normal route gate
        ↓
unchanged local action is selected
        ↓
canonical transaction creates the local commitment
```

### Perception exclusion witness

```text
change only hidden fixture fact H
        ↓
agent_P perception is byte-identical
        ↓
candidate set, scores, selected action, proposal, and committed result
remain byte-identical
```

### Deterministic tie witness

Adjust fixture values so two feasible actions have equal score. Stable action
identifier ordering must select one deterministically. This is a fixture input,
not a production priority policy.

## Required authority boundaries

```text
agent selector owns:
  perception projection
  feasible-action enumeration
  score calculation
  selected commitment proposal

canonical transaction layer owns:
  immutable decision snapshot
  sequential revalidation
  resource reservation
  commitment creation or rejection
  causal ledger

forbidden:
  direct city mutation during selection
  direct resource reservation during selection
  direct commitment creation during selection
  front/stage/mission selector
```

## Acceptance gates before freeze

1. Agent perception is a declared projection and is mechanically auditable against the authoritative record.
2. The selector cannot read excluded hidden fact H or undeclared city state.
3. Primary selects the higher-scoring feasible remote action and proposes—rather than directly creates—the commitment.
4. The canonical transaction layer revalidates all ordinary gates and performs the only commitment/resource mutation.
5. Route-closed counterfactual changes only route availability; the unchanged local action is selected through ordinary feasibility.
6. Hidden-fact witness produces byte-identical perception, selection, proposal, ledger, and record.
7. Tie witness uses stable deterministic ordering; no container order, wall-clock timing, or action-name special case decides it.
8. Every selected or rejected action records perception, candidate set, feasibility gates, score, tie break, proposal, revalidation, and resource disposition.
9. Same record, seed, policy version, and input sequence replay byte-identically.
10. Source audit shows no mission/front selector, direct mutation in the selector, undeclared read path, or fixture-branch result field.

## Explicit boundary

This candidate does not authorize implementation, Unreal, physical evidence,
multiple agents, agent-to-agent strategy, stale intelligence, generalized
planning, learning, economy, map scale, split crews, multiplayer, networking,
rollback, repair, or city-content expansion.

## Changelog

### 0.1.0-draft.0 — 2026-08-26

- Opened the candidate bounded-agent commitment-selection proof after the sealed shared-state composition proof.
- Kept the unit canonical-only: one agent, two fixture actions, a declared perception projection, one feasibility counterfactual, one hidden-fact exclusion witness, and one deterministic tie witness.
- Implementation remains prohibited pending review and freeze.
