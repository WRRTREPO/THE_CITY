# Shared-State Commitment Interference Proof Evidence — v0.1.0

**Status:** Passed and sealed
**Date:** 2026-08-26
**Specification:** [Shared-State Commitment Interference Proof — v0.1.0](Shared-State%20Commitment%20Interference%20Proof%20-%20Draft.md)
**Implementation scope:** Canonical-only; two fixture-local commitment definitions and one shared capacity fact only.

## Claim proved

> **Independently defined commitments may interfere solely because they read and write the same authoritative state.**

The resolver contains no X→Y callback, foreign commitment reference, pair rule,
or outcome branch selector. It receives due commitment identities and an
explicit fixture queue, then applies ordinary working-state revalidation.

```text
immutable R0 batch snapshot
        ↓
first valid commitment transforms S
        ↓
later valid commitment revalidates against working state
        ↓
ordinary S gate passes or fails
        ↓
durable allocation and terminal disposition
```

## Isolated definition identity

Both definitions are present and byte-identical in primary, counterfactual,
and permutation records.

| Definition | SHA-256 |
| --- | --- |
| `commitment_X` | `08b0338b9897c691bac309bb11017e921ea6517577837ae4fed9496bae7f831d` |
| `commitment_Y` | `bf7e83f57dfb35d9b3ef9c228a52422732e517a8db720a33683bf1f485d019ce` |

Each definition reads the ordinary `S.available_units >= 1` gate and writes
only `S.available_units` plus its own allocation path. The definition audit
finds zero foreign commitment/actor references and zero non-`S` state paths.

## Three canonical witnesses

| Fixture | R0 SHA-256 | Final SHA-256 | Result |
| --- | --- | --- | --- |
| Primary, queue X → Y | `37bc69d1b09b54d6cc184b119efae9a9665270cad49623b6ee3fc981b9b63416` | `a912f032beccb925be0fbf1155b4547612a0fd12b49da1942ad9c06a91cbe0ae` | X transforms the only S unit; Y revalidates and fails its ordinary S gate. |
| Counterfactual, X absent | `46f8b8e2799bed035a37f2f879fc28cdff55f449c9cf01f722dc4160c27b5284` | `9d56f6e12da69abbfa1604061ba7fd9a25ec2bc690c293db7b4a0b2f7df293af` | Only X scheduling/presence is removed; unchanged Y succeeds and receives the unit. |
| Permutation, queue Y → X | `37bc69d1b09b54d6cc184b119efae9a9665270cad49623b6ee3fc981b9b63416` | `5c09897de6f114fcfac24a38a5495548fa2181d5f1a3f2bbf2b86170e852a342` | Y transforms the unit; X revalidates and fails the same ordinary S gate. |

Primary and permutation share byte-identical R0. Their different final records
therefore witness canonical ordering over the same state, not hidden X-priority
semantics. The counterfactual preserves R0’s definitions, shared state, seed,
rules, and Y instance unchanged; only X's scheduled presence is removed.

## Lifecycle and provenance

Every successful commitment transforms exactly one available S unit into a
durable allocation. Every failed commitment records `no resource acquired`.
There are no open leases, capacity leaks, or implicit cleanup paths.

Each ledger entry carries the common `batch_pre_state_hash`, its own
`working_pre_state_hash`, gate values, definition hash, mutations, and terminal
resource disposition. In the primary case, Y retains the R0 batch reference but
has a different working pre-state after X has committed; that record directly
explains Y’s failure without inferring a relationship from the final state.

## Verification

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/thecity_pycache \
python3 -m unittest -v \
  test_kernel.py test_roundtrip.py test_contention.py \
  test_unreal_authority_boundary.py test_deployment_opportunity.py \
  test_live_commitment.py test_shared_state_interference.py
68 tests — OK
```

The release verifier regenerates all three runs from the frozen resolver and
verifies source, test, record, ledger, and run artifact hashes through its
self-excluding manifest:

```sh
cd "/Users/boandersson/Desktop/Games/THE_CITY"
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/thecity_pycache \
  python3 proof_kernel/verify_shared_state_interference_release.py verify
```

## Boundary

This proves composition through one shared authoritative fact. It does not
authorize Unreal, physical evidence, generalized commitment definitions,
planner behavior, new city content, resource systems, scale, split crews,
multiplayer, networking, rollback, repair, or a successor proof scope.
