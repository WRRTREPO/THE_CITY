# Same-Clock Successor Semantics Proof Evidence

**Version:** 0.1.0
**Status:** Passed and sealed.
**Specification:** [Same-Clock Successor Semantics Proof — v0.1.0](Same-Clock%20Successor%20Semantics%20Proof%20-%20Draft.md)
**Simulation identity:** `SameClockSuccessorSemanticsPayload.v1` / `0.7.0-draft.47`
**Governing continuation:** [Co-op Open-City FPS Simulation — v0.7 Working Continuation](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)

## Claim proven

> One canonical boundary may create a same-clock successor only at a strictly
> later canonical phase, under finite canonical generation authority, and that
> successor must be rediscovered from the committed successor record.

This is a canonical-only neutral fixture. It proves neither same-time external
input arbitration nor general multi-member batching.

## Frozen fixture and records

```text
R0  hash 6033dc73851f7f8616e24e1595b4523a75ffbfa856585d35e3cc2f6a01bf0043
    clock t0/00
    BX = (t1/00, phase 10, [work_x])

R1  hash c9543139d6553497a28bb03d6b805bd17166e5f5ef39ba5589968b49380e2d01
    clock t1/00
    X terminal = succeeded
    same-clock budget = consumed, 1 → 0
    Y newly active
    BY = (t1/00, phase 20, [work_y])
    BY.source_record_hash = hash(R1)

R2  hash 315be42f405ea4c5e1702a699347ff11ed747bb6f3b5cb1dba53e2ff1b9f09a4
    clock t1/00
    Y terminal = succeeded
    future schedule = []
    next_consequential_boundary = none
```

The clock does not advance between R1 and R2. The committed R1 nevertheless
invalidates BX because boundary authority is record-bound, not clock-bound.

## Boundary/member law witnessed

```text
canonical boundary = (decision_time, simulation_phase)
boundary members   = complete due-work set at that exact pair
member order       = stable work_id order
```

Each demonstrated boundary has one member, but the scheduler emits a complete
ordered member set and matching member keys. `work_id` never creates an
additional transaction boundary.

## Execution-policy witnesses

All four witnesses begin from byte-identical R0 and use one resolver:

```text
dense throughout
boundary jump throughout
dense → demote → boundary jump
boundary jump → promote → dense
```

They produce byte-identical canonical R0, R1, and R2 checkpoints, including
the canonical envelope/hash, ancestry, ledger, resource disposition, future
schedule, and next-boundary result. Their resolution-local samples and traces
differ as intended.

## Rejection witnesses

Twelve malformed or authority-leaking attempts fail before canonical mutation:

```text
retrograde/equal phase             phase-limit breach
duplicate member                   cycle/settled-work reference
exhausted generation budget        stale BX against R1
fabricated BY against R0           crossing boundary against R1
local clock authority              cached authoritative gate
promotion authority creation       demotion authority loss
```

Rejected attempts append no canonical ledger entry, create no future schedule,
and commit no canonical mutation.

## Source and replay audit

The source audit establishes:

- exactly one `resolve_next_due` resolver;
- scheduler boundary selection by `(decision_time, simulation_phase)`;
- full `work_id`-ordered due-member return, with member keys as provenance;
- no policy/local trace input to resolver or canonical gate evaluation;
- record-relative rediscovery after every committed boundary;
- finite canonical budget enforcement;
- no randomness, Unreal, city-content fixture, or self-referential successor
  hash.

The full regression command passed **143/143** checks. The focused
same-clock suite passed **13/13** checks. Every witness and the complete proof
run replay byte-identically.

## Release package

`proof_kernel/verify_same_clock_successor_release.py` regenerates all frozen
records, validates the checkpoints, rejection dispositions, and source audit,
then verifies the self-excluding release manifest.

The release package binds the exact specification, this evidence, governing
continuation, capacity record, README, implementation, focused tests, verifier,
and R0/R1/R2 plus witness/audit artifacts.

The self-excluding manifest verifies **24/24** release artifacts.

## Boundary retained

Not proven here: same-time external input arbitration, general multi-member
phase batching, stochasticity, Unreal/materialization transitions, city
content, planner behavior, networking, rollback, save/load, map scale, or
production scheduling.
