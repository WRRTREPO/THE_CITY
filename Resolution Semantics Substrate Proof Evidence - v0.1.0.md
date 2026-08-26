# Resolution Semantics Substrate Proof Evidence

**Version:** 0.1.0
**Status:** Passed and sealed
**Frozen specification:** [Resolution Semantics Substrate Proof — v0.1.0](Resolution%20Semantics%20Substrate%20Proof%20-%20Draft.md)
**Parent law:** [Resolution Semantics Law — v0.1.1](Resolution%20Semantics%20Law%20-%20v0.1.1.md)
**Simulation version:** `0.7.0-draft.30`
**Scope:** Canonical-only authority substrate. No commitment gate executes.

## Claim

> Given one canonical envelope with one exact payload schema, boundary discovery and resolution transitions preserve all authoritative state required for future causal decisions.

This is the predecessor proof for Causal-LOD Equivalence. It does not prove variable-resolution execution.

## Implemented authority boundary

```text
canonical_envelope
  ├── identity
  ├── current_causal_state
  ├── future_causal_state
  └── causal_provenance
          │
          │ canonical_hash covers this envelope only
          ▼
runtime_envelope
  ├── byte-identical canonical_envelope
  └── resolution_local_state
          │
          ├── cache
          ├── samples
          └── diagnostics
```

`ResolutionSemanticsSubstratePayload.v1` is validated as an exact schema. Unknown, missing, redirected, and incompatible authoritative paths are rejected. The canonical identity exists only inside the hashed envelope; there is no second operational identity wrapper.

## Witnesses

| Witness | Result |
| --- | --- |
| Boundary identity | R0, minimal, promoted, and demoted runtime envelopes all return `t1/00` and exactly `t1/00/substrate/commitment_alpha.gate_check`. |
| Promotion neutrality | Promotion derives only a cache, sample, and diagnostic. The authoritative projection and canonical hash remain byte-identical to R0. |
| Demotion neutrality | Demotion drops all local representation while preserving the active commitment, reservation, future schedule, terminal disposition, genesis provenance, and empty authoritative ledger. |
| Round-trip neutrality | `R0 → promote → demote → promote` regenerates the local cache from canonical truth; it does not preserve cache state as hidden authority. |

## Adversarial dispositions

All malformed inputs fail closed outside the canonical envelope and causal ledger.

```text
promotion adds durable authority
→ resolution_transition_rejected.authoritative_mutation_detected

demotion removes authoritative ownership, scheduling, ancestry, or disposition
→ resolution_transition_rejected.authoritative_loss_detected

local policy proposes a different boundary or due set
→ resolution_transition_rejected.boundary_mismatch
```

No rejection appends to the authoritative causal ledger or creates future schedule state.

## Determinism and source audit

The full regression suite passes **91/91** checks. The substrate adds 12 checks covering exact payload validation, redundant scheduling/provenance agreement, the four required witnesses, all three fail-closed classes, replay, and source authority separation.

The source audit establishes that:

- there is one scheduler query, `next_consequential_boundary(canonical_envelope)`;
- the scheduler receives only canonical state and does not read resolution-local state or a resolution trace;
- promotion/demotion do not mutate canonical paths, commitments, reservations, or the authoritative ledger;
- local policy cannot override canonical boundary discovery;
- no expected-result shortcut, authoritative randomness, high/coarse execution mode, Unreal path, city-content fixture, or planner behavior exists in this proof.

## Release verification

The self-excluding release manifest is [Resolution Semantics Substrate Proof — v0.1.0 SHA256SUMS](Resolution%20Semantics%20Substrate%20Proof%20-%20v0.1.0%20SHA256SUMS.txt). It seals the frozen law/specification, implementation, regression suite, verifier, governing record, README, and the five deterministic artifacts:

- `resolution_substrate_R0.json`
- `resolution_substrate_run.json`
- `resolution_substrate_witnesses.json`
- `resolution_substrate_adversarial.json`
- `resolution_substrate_source_audit.json`

Run from the project root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s proof_kernel -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 proof_kernel/verify_resolution_semantics_substrate_release.py verify
```

## Boundary

This proof does not implement or prove high/coarse execution policy, Causal-LOD equivalence, stochastic behavior, a canonical commitment resolution, Unreal materialization, city content, planning, networking, multiplayer, map scale, or production streaming.

The next valid working unit, if explicitly selected, is a new Causal-LOD Equivalence specification. It must use this substrate rather than introduce alternate causal semantics inside a fixture.
