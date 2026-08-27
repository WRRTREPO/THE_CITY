# Record-Relative Chronological Resolution Proof Evidence

**Version:** 0.1.0
**Status:** Passed and sealed.
**Specification:** [Record-Relative Chronological Resolution Proof — v0.1.0](Record-Relative%20Chronological%20Resolution%20Proof%20-%20Draft.md)
**Simulation version:** `0.7.0-draft.39`
**Parent continuation:** [Co-op Open-City FPS Simulation — v0.7 Working Continuation](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)

## Claim tested

> **Resolution policy may skip empty intervals, but after every committed
> boundary it must discover the next consequential boundary from the newly
> committed canonical record.**

The proof is canonical-only. It introduces no city-content, Unreal, external
input, randomness, planner, or production-streaming behavior.

## Sealed fixture

`RecordRelativeChronologicalResolutionPayload.v1` begins from one R0:

```text
t1/00  X resolves and allocates the shared slot
t1/30  Y is rediscovered from R1 and revalidates that slot
t2/00  Z is rediscovered from R2 and resolves independently
```

The final canonical sequence is:

```text
R0
→ boundary(source = hash(R0), t1/00, X)
→ R1

R1
→ boundary(source = hash(R1), t1/30, Y)
→ R2

R2
→ boundary(source = hash(R2), t2/00, Z)
→ R3

R3
→ none
```

No precomputed multi-boundary itinerary receives canonical authority.

## Results

The exact canonical resolver produced the required history:

```text
X succeeds
→ shared_slot_state = allocated_to_x
→ R1 commits

Y reads R1
→ observed shared_slot_state = allocated_to_x
→ required value = available
→ gate fails
→ no resource acquired
→ R2 commits

Z remains scheduled after Y fails
→ Z succeeds
→ reservation_z releases unit_z
→ R3 commits
→ no future boundary
```

Each successor carries exactly one canonical parent:

```text
R1.parent = hash(R0)
R2.parent = hash(R1)
R3.parent = hash(R2)
```

Each authoritative ledger entry embeds the boundary witness that authorized it.
Its `source_record_hash` equals the corresponding successor parent hash. There
is no second canonical transaction-header authority.

## Resolution witnesses

Four materially different local execution histories were regenerated from
byte-identical R0:

```text
A. dense throughout
B. boundary jump throughout
C. dense → demote → boundary jump → promote → dense
D. boundary jump → promote → dense → demote → boundary jump
```

All four match byte-for-byte at R0, R1, R2, and R3:

- canonical envelope and canonical hash;
- successor ancestry and boundary source;
- causal ledger and exact Y gate observation;
- terminal resource dispositions;
- future schedule; and
- next-consequential-boundary result.

Only resolution-local state and diagnostic traces differ.

## Rejection evidence

The runtime rejects, without canonical mutation, ledger append, or future-schedule
creation:

- an R0-bound boundary applied to R1;
- an R1 attempt to cross due Y and resolve Z;
- any boundary whose source hash differs from its supplied record;
- local clock/gate/cache authority;
- promotion authority creation or demotion authority loss; and
- same-clock successor creation under this exact fixed payload.

The generic scheduler relation remains unresolved-work
`decision_time >= canonical_clock`; this fixture simply rejects new schedule
creation so that same-clock successor behavior is not smuggled into its scope.

## Verification

- Complete Python regression suite: **117/117 passing**.
- Focused chronological-resolution suite: **13/13 passing**.
- Replaying each policy history regenerates byte-identical checkpoints and
  local trace for that policy.
- The source audit found exactly one `next_consequential_boundary` and one
  `resolve_next_due`; policies/local traces cannot reach canonical gate,
  mutation, ledger, schedule, disposition, or resolver-selection paths.
- X and Y definition hashes are isolated; neither definition contains a
  foreign commitment reference, callback, pair-specific rule, or priority.
- The self-excluding release manifest verifies the specification, evidence,
  continuation, capacity record, implementation, tests, verifier, and all
  regenerated proof artifacts.

Run the release verifier:

```sh
cd "/Users/boandersson/Desktop/Games/THE_CITY"
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/thecity_pycache \
  python3 proof_kernel/verify_record_relative_chronological_resolution_release.py verify
```

## Boundary

This proves one neutral three-boundary fixture only. It does not prove
same-clock successor creation, external inputs during skipped intervals,
stochasticity, larger commitment populations, city geography, FPS fidelity,
Unreal streaming, networking, rollback, save/load, or production-scale
Causal-LOD.

## Changelog

### 0.1.0 — 2026-08-26

- Sealed the canonical-only X/Y/Z chronological-resolution proof.
- Recorded record-bound boundary capability, R0/R1/R2/R3 checkpoint
  equivalence, exact R1-relative Y revalidation, continued Z discovery,
  runtime rejection, replay, source audit, and self-excluding manifest
  verification.
