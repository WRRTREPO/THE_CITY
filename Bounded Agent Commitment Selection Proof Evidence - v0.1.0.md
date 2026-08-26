# Bounded Agent Commitment Selection Proof Evidence — v0.1.0

**Status:** Passed and sealed
**Date:** 2026-08-26
**Specification:** [Bounded Agent Commitment Selection Proof — v0.1.0](Bounded%20Agent%20Commitment%20Selection%20Proof%20-%20Draft.md)
**Implementation scope:** Canonical-only; one agent, two fixture-local action definitions, one selection transaction, and active commitment creation only.

## Claim proved

> **An agent may select one feasible action from a bounded perception, then propose a commitment that the canonical transaction layer alone may create.**

The selector is pure. It receives a declared projection, evaluates ordinary gates and scores, and emits a proposal. It neither receives the complete city record nor mutates a resource, commitment, or ledger.

```text
authoritative record
        ↓
audited perception projection
        ↓
candidate gates + explicit score
        ↓
deterministic selected action
        ↓
agent proposal
        ↓
canonical revalidation
        ↓
one active commitment with owned reservations
```

## Frozen action identity

| Action definition | SHA-256 |
| --- | --- |
| `secure_remote_capacity` | `3fa8a9353eac6c088df8e4a1c06b7ff88bb6341b3d6631f0f82b6a6a9dd14ea1` |
| `stabilize_local_capacity` | `425c750c831ede4b22f3a94ca66401ca8906a0c587420981eb200c8d95362eb6` |

Both hashes are identical in every witness. The canonical transaction rejects a proposal if its record action definitions diverge from the frozen identity, even where a substituted definition would otherwise produce a valid selection.

## Witnesses

| Witness | R0 SHA-256 | Final SHA-256 | Result |
| --- | --- | --- | --- |
| Primary | `36296c9ee08f56cf1b6644cd803223e2b35f0d7c82154be967213de47729a30b` | `40c1412d97ae473e146da5f9dcb2149c9501e65b7a1d728ae5e99c0ce66c4391` | Remote score 5 exceeds local score 4; proposal is canonically accepted; remote commitment owns transport plus route capacity. |
| Feasibility | `b0ad1988352f524d598bee2489a57c69a87a3f1736ff49b190a034368534b0e9` | `43e6a46051ba1ab24b12335d0cce1c0927dfa0e536f0723676e2201adec2ce85` | Only `A_to_B.open` is false; remote action fails its ordinary route gate; unchanged local action is selected. |
| Hidden H alpha | `36296c9ee08f56cf1b6644cd803223e2b35f0d7c82154be967213de47729a30b` | `40c1412d97ae473e146da5f9dcb2149c9501e65b7a1d728ae5e99c0ce66c4391` | Baseline excluded-fact state. |
| Hidden H beta | `f8c7b7eaf505ce8c1be7bc55eefb99cdf8ba59f23bf36a8fb8303154ef5c09e8` | `9eef30858c56652e6eb1fc54e0b52daeea38b91cfd8e6013c15aa80d80afd42d` | Only H changes. Perception, candidates, score, selected action, and semantic commitment intent remain identical. |
| Tie | `5a02c40b7952007e2bc744cf017f5632cc8597d81ef531e14112023a661bd751` | `b00bfbbb80f2bbfd4aa2dbaba0a99a3577b56e952092778db44be3c494c8b0cd` | Both actions score 4. Stable ascending action-ID order selects `secure_remote_capacity`. |

## Boundaries demonstrated

The perception projection exposes route openness/capacity, declared resource availability, local capacity, declared opportunity values, action-definition hashes, and the agent's commitment availability. `hidden_fact_H` is not projected or readable by the selector.

Changing H changes complete-record source and final hashes as required by canonical binding. The hidden-fact witness therefore compares semantic selection fields. After removing H itself, its two final records are byte-identical.

Canonical revalidation validates source binding, actor/policy identity, frozen definitions and hashes, exact perception, exact candidate evaluation, exact proposed commitment, and every selected action gate before reserving anything. A redirected proposal is rejected with no resource acquisition and no commitment creation.

The proof stops at active commitment creation. A successful proposal creates one named active commitment that owns its reservations; it does not claim to prove later execution or terminal disposal.

## Verification

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/thecity_pycache \
python3 -m unittest -v \
  test_kernel.py test_roundtrip.py test_contention.py \
  test_unreal_authority_boundary.py test_deployment_opportunity.py \
  test_live_commitment.py test_shared_state_interference.py \
  test_bounded_agent_selection.py
79 tests — OK
```

The self-excluding release manifest regenerates and verifies each primary, feasibility, hidden-H, and tie artifact from the frozen resolver:

```sh
cd "/Users/boandersson/Desktop/Games/THE_CITY"
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/thecity_pycache \
  python3 proof_kernel/verify_bounded_agent_selection_release.py verify
```

## Boundary

This establishes one bounded perception-to-commitment proposal path. It does not authorize multiple agents, agent-to-agent strategy, stale beliefs, learning, a generalized planner, Unreal, physical evidence, economy, city content, scale, split crews, multiplayer, networking, rollback, repair, or a successor scope.
