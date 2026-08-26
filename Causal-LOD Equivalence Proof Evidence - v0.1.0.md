# Causal-LOD Equivalence Proof Evidence

**Version:** 0.1.0
**Status:** Passed and sealed
**Frozen specification:** [Causal-LOD Equivalence Proof — v0.1.0](Causal-LOD%20Equivalence%20Proof%20-%20Draft.md)
**Parent law:** [Resolution Semantics Law — v0.1.1](Resolution%20Semantics%20Law%20-%20v0.1.1.md)
**Predecessor:** [Resolution Semantics Substrate Proof — v0.1.0](Resolution%20Semantics%20Substrate%20Proof%20Evidence%20-%20v0.1.0.md)
**Simulation version:** `0.7.0-draft.34`
**Scope:** Canonical-only resolution equivalence; no Unreal or city-content fixture.

## Claim

> Changing execution granularity between consequential boundaries does not change authoritative causal history.

The proof runs one exact `CausalLodEquivalencePayload.v1` from byte-identical
R0 under four different local execution histories. Every witness reaches the
same R1 through the same `resolve_next_due` transaction.

## Common authority transaction

```text
R0
  canonical_clock = t0/00
  active commitment_alpha
  reservation_alpha owns unit_alpha
  next boundary = t1/00
        │
        ▼
one resolve_next_due(R0, t1/00) transaction
  parent_record_hash = hash(R0)
  transaction_pre_state_hash = hash(R0)
  canonical_clock = t1/00
  gate passes
  commitment succeeds
  unit_alpha releases
  one authoritative ledger entry
  future schedule = empty
        │
        ▼
R1
```

No authoritative scheduler-clock-advance record, parent, ledger entry, or
alternate pre-state exists between R0 and the t1/00 transaction.

## Witnesses

| Witness | Local execution history | Canonical result |
| --- | --- | --- |
| Dense throughout | Samples at `t0/15`, `t0/30`, and `t0/45`. | R1 |
| Boundary jump throughout | No intermediate sample. | R1 |
| Boundary jump → promote → dense | No initial sample, promoted local cache, then dense samples. | R1 |
| Dense → demote → jump → promote → dense | One dense sample, discard local state, jump, regenerate local cache, final dense sample. | R1 |

All four results are byte-identical in canonical envelope, canonical hash,
terminal commitment state, unit-alpha disposition, authoritative ledger, R0
parent/pre-state hashes, future schedule, and `next_consequential_boundary = none`.
Only local samples, local cache, diagnostics, and the resolution trace differ.

## Runtime rejection and equivalence oracle

Malformed local runtime behavior fails closed without canonical mutation:

```text
local canonical-clock mutation       → rejected
cached authoritative gate result     → rejected
promotion carries authority          → rejected
demotion loses resolver input        → rejected
boundary jump skips due work         → rejected
```

Cross-witness disagreement is instead an `equivalence_failure`. Candidate
outputs remain as inspectable non-authoritative artifacts; the proof harness
does not rewrite or roll them back.

## Source audit

The source audit verifies the structural requirement beyond output coincidence:

- exactly one resolver: `resolve_next_due(canonical_envelope, canonical_boundary)`;
- resolver code reads no policy, local state, trace, or runtime envelope;
- dense inspection and boundary jump do not invoke the resolver, override its boundary, or evaluate authoritative gates;
- promotion/demotion do not write canonical paths;
- no random module, Unreal path, city-content fixture, planner, or external input exists.

## Verification

The full repository regression passes **104/104** tests. The Causal-LOD proof
adds 13 tests covering exact payload identity, R0-only transaction ancestry,
local-state isolation, all four witness policies, terminal resource behavior,
runtime rejection, oracle failure preservation, replay, and source audit.

The self-excluding release manifest is [Causal-LOD Equivalence Proof — v0.1.0 SHA256SUMS](Causal-LOD%20Equivalence%20Proof%20-%20v0.1.0%20SHA256SUMS.txt). It seals ten source/governing members and nine deterministic witness/audit artifacts.

Run from the project root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s proof_kernel -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 proof_kernel/verify_causal_lod_equivalence_release.py verify
```

## Boundary

This proves one neutral canonical fixture under two materially different
execution granularities. It does not prove Unreal materialization at changing
fidelity, stochastic equivalence, external inputs during skipped intervals,
multiple live commitments, planner behavior, city content, city scale,
multiplayer, save/load, rollback, or production streaming.

Any successor proof must be selected separately. This result does not authorize
generalizing from the one fixture to production Causal LOD.
