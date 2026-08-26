# Bridge Access Traversal Contention Proof Evidence — v0.1.1

**Status:** Passed — provenance correction
**Date:** 2026-08-26
**Specification:** [Bridge Access Traversal Contention Proof — v0.1.0](Bridge%20Access%20Traversal%20Contention%20Proof%20-%20Draft.md)
**Supersedes:** [v0.1.0 evidence](Bridge%20Access%20Traversal%20Contention%20Proof%20Evidence%20-%20v0.1.0.md) as the final release record; the original witness remains unchanged.

## Scope of this revision

This revision repairs only cross-transaction temporal provenance. It does not alter contention ordering, route-admission law, proposal authority, canonical city facts, Unreal materialization source, or the final Case 1 / Case 2 authoritative records.

```text
t0 intermediate record
      │ hash retained as parent_record_hash
      ▼
scheduler_clock_advance("t1/15")
      │ changes clock only
      ▼
Rexit_pre
      │ hash retained as transaction_pre_state_hash
      ▼
t1/15 exit transaction
```

## Corrected provenance law

The `t1/15` batch header now contains:

```yaml
parent_record_hash: hash(t0_intermediate)
boundary_derivation: scheduler_clock_advance
transaction_pre_state_hash: hash(Rexit_pre)
```

The deterministic scheduler derivation is exact:

```text
Rexit_pre = copy(t0_intermediate) + clock := t1/15
```

No actor proposal or strategic decision is introduced by this boundary construction. The `t1/15` exit remains a separate canonical transaction, and its working revalidation begins only after the explicitly derived `Rexit_pre` exists.

The failed Case 1 police admission now records `no resource acquired`; it no longer claims release of a unit that was never reserved.

## Acceptance results

- The Case 2 `t1/15` header's `parent_record_hash` equals the canonical hash of the exact t0 intermediate record.
- Reapplying `deterministic_scheduler_advance(parent, "t1/15")` reproduces the serialized `Rexit_pre` byte-for-byte and differs from its parent only in `clock`.
- `hash(Rexit_pre)` equals the t1 batch's immutable transaction pre-state hash.
- Resolving the same t1 transaction from the same parent and boundary produces byte-identical transaction output and final record.
- The existing Case 1 and Case 2 contention outcomes remain unchanged: police stays at A when destruction wins admission; an entered lease survives later closure and police exits at B when entry wins.

## Verification

```text
PYTHONDONTWRITEBYTECODE=1 python3 proof_kernel/test_contention.py
13 tests — OK

PYTHONDONTWRITEBYTECODE=1 python3 proof_kernel/test_kernel.py
8 tests — OK

PYTHONDONTWRITEBYTECODE=1 python3 proof_kernel/test_roundtrip.py
5 tests — OK

PYTHONDONTWRITEBYTECODE=1 python3 proof_kernel/test_unreal_authority_boundary.py
2 tests — OK
```

All **28 tests** pass. No Unreal C++ source or final materialization record changed in this provenance-only revision; therefore the prior UE 5.8 build and fresh-process materialization evidence remains applicable without reinterpretation.

Verify the new sealed package with:

```sh
cd "/Users/boandersson/Desktop/Games/THE_CITY"
PYTHONDONTWRITEBYTECODE=1 python3 proof_kernel/verify_contention_release.py verify
```

The new manifest is [Bridge Access Traversal Contention Proof — v0.1.1 SHA256SUMS](Bridge%20Access%20Traversal%20Contention%20Proof%20-%20v0.1.1%20SHA256SUMS.txt). It excludes its own identity and preserves the v0.1.0 manifest as the historical identity of commit `ddf7719`.

## Boundary

This correction closes temporal ancestry for the demonstrated t0 → t1/15 transition only. It authorizes no successor city scope, multiplayer policy, rollback law, route behavior, or additional simulation system.
