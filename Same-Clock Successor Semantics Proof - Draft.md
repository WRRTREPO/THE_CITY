# Same-Clock Successor Semantics Proof

**Version:** 0.1.0
**Status:** Frozen. Canonical-only implementation is authorized within this exact boundary.
**Parent laws:** [Resolution Semantics Law — v0.1.1](Resolution%20Semantics%20Law%20-%20v0.1.1.md); [Record-Relative Chronological Resolution Proof — v0.1.0](Record-Relative%20Chronological%20Resolution%20Proof%20-%20Draft.md); [External Input Boundary Proof — v0.1.1](External%20Input%20Boundary%20Proof%20-%20v0.1.1.md)
**Parent continuation:** [Co-op Open-City FPS Simulation — v0.7 Working Continuation](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)
**Simulation version:** `SameClockSuccessorSemanticsPayload.v1` / `0.7.0-draft.47`

**Authority posture:** This freeze authorizes only the bounded canonical
implementation stated below. The sealed External Input release remains its own
historical package; no adjacent city scope is implied.

## Question

> **May one canonical boundary lawfully create unresolved successor work at the
> same canonical decision time, and if so, how does the city order, rediscover,
> bound, and prove that work without retaining an authoritative itinerary?**

The current sealed scheduler law already discovers unresolved work where:

```text
decision_time >= canonical_clock
```

The previous chronological fixture deliberately rejected same-clock successor
creation. That was correct for its fixed payload, but it leaves this real
scheduler question unresolved:

```text
X resolves at t1/00, phase 10
        ↓
X lawfully creates Y at t1/00, phase 20
        ↓
R1 still has canonical_clock = t1/00
        ↓
what may next_consequential_boundary(R1) lawfully return?
```

This proof selects one answer for one neutral bounded fixture. It does not
generalize same-time external-input arbitration, agent behavior, city content,
or production scheduling.

## Proposed law

> **Same-clock successor work is lawful only when its canonical boundary key
> is strictly later than the boundary that created it, its authoritative
> same-clock budget remains positive, and it is rediscovered from the committed
> successor record.**

The scheduler never continues an in-memory batch merely because it remembers
that X created Y. It must follow the ordinary record-relative cycle:

```text
R0
  ↓ discover BX bound to hash(R0)
resolve X
  ↓ commit R1 @ t1/00
discard BX and every prior scheduling view
  ↓ discover BY bound to hash(R1)
resolve Y
  ↓ commit R2 @ t1/00
rediscover from R2
  ↓ none
```

The clock remains at `t1/00` during both transactions. Phase-boundary
progression, not an invented clock tick, establishes lawful order.

## Exact proof boundary

```yaml
authorized_for_implementation:
  - one exact new payload schema
  - one canonical scheduler query with phase-aware boundaries and ordered work
    members
  - one X boundary that creates one same-clock Y successor
  - one finite authoritative same-clock budget
  - one R0/R1/R2 checkpoint chain
  - dense, boundary-jump, and two mixed local-policy witnesses
  - record-bound stale/crossing/retrograde/duplicate/cycle rejection
  - replay, source audit, evidence, and self-excluding release manifest

not_authorized:
  - same-time external-input arbitration
  - external input transport or cursor changes
  - Unreal, streaming, or helicopter observation
  - routes, factions, agents, planners, or city-content fixtures
  - randomness
  - multiple independent same-clock creators
  - unbounded successor generation
  - networking, rollback, save/load, map scale, or production scheduling
```

`X`, `Y`, phase labels, and the budget are proof fixtures, not city ontology.
They do not create a general `SameClockSuccessorSystem`, a content pipeline, or
a production action vocabulary.

## Exact identity boundary

This frozen proof creates—not reuses—one exact authoritative payload:

```yaml
record_schema: CanonicalResolutionEnvelope.v1
payload_schema: SameClockSuccessorSemanticsPayload.v1
scenario_id: same-clock-successor-semantics-v1
scenario_version: 0.1.0
simulation_version: 0.7.0-draft.47
seed: same-clock-successor-semantics-v1/0001
```

Identity lives only in `canonical_envelope.identity` and is included in
`canonical_hash`. Unknown, missing, redirected, or incompatible authoritative
fields must reject. The implementation, artifacts, replay inputs, evidence,
and release manifest must use this exact simulation identity.

## Canonical boundary and member ordering law

Every scheduled work item belongs to one canonical boundary and has one
canonical member identity:

```yaml
canonical_boundary_key:
  decision_time: exact canonical time token
  simulation_phase: bounded non-negative integer

canonical_work_member_key:
  decision_time: exact canonical time token
  simulation_phase: bounded non-negative integer
  work_id: exact stable identifier
```

The scheduler orders **boundaries** lexicographically by
`(decision_time, simulation_phase)`. It selects the minimum unresolved
boundary, then returns that boundary's complete due-work set ordered by
`work_id`. The matching complete ordered `canonical_work_member_key` set is
provenance for those members; it does not create extra transaction boundaries.

`work_id` is therefore a stable within-boundary ordering key only. It cannot
repair a non-monotonic phase relation or silently turn each member into a
separate canonical transaction.

For a same-clock successor:

```text
successor.decision_time == creator.decision_time == canonical_clock
successor.simulation_phase > creator.simulation_phase
successor.boundary_key > creator.boundary_key
successor.parent_work_member_key == creator.work_member_key
```

For this fixture only:

```yaml
same_clock_phase_limit: 20
same_clock_generation_budget:
  t1/00: 1

X:
  boundary_key: [t1/00, 10]
  work_member_key: [t1/00, 10, work_x]
  may_create: Y

Y:
  boundary_key: [t1/00, 20]
  work_member_key: [t1/00, 20, work_y]
  may_create_same_clock_successor: false
```

The budget is authoritative future-causal state. X consumes the one budget
unit while creating Y. Y has no remaining same-clock creation authority. This
gives the demonstrated chain a finite, inspectable termination argument:

```text
same-clock budget starts at 1
X creates Y
→ budget becomes 0
Y resolves
→ no same-clock work remains or can lawfully be created
```

This does not choose a production budget size or production phase range. It
proves only that same-clock creation needs a finite canonical monotonicity law,
rather than relying on wall time, policy iterations, or caller discipline.

## Neutral payload fixture

The exact initial authoritative record will contain:

```yaml
current_causal_state:
  durable_facts:
    outcome_x: pending
    outcome_y: pending
  active_and_terminal_commitments:
    commitment_x:
      state: active
      boundary_key: [t1/00, 10]
      work_member_key: [t1/00, 10, work_x]
      terminal_disposition: null
    commitment_y:
      state: absent
      boundary_key: null
      work_member_key: null
      terminal_disposition: null
  reservations_leases_and_resource_ownership:
    successor_budget_t1_00:
      state: available
      remaining_units: 1
      owner_commitment_id: null

future_causal_state:
  canonical_clock: t0/00
  scheduled_consequential_decisions:
    - decision_time: t1/00
      simulation_phase: 10
      due_work_ids: [work_x]
  work_execution_metadata:
    work_x:
      simulation_phase: 10
      parent_work_member_key: null
  canonical_work_member_keys:
    - [t1/00, 10, work_x]
  same_clock_phase_limit: 20
```

`work_y` is absent from every R0 canonical field. It is not a hidden second
member of an R0 due set, a precomputed itinerary entry, or a local cache
prediction.

`scheduled_consequential_decisions` represents boundaries, not individual
members. Its `due_work_ids` is the complete, canonically `work_id`-ordered set
for its exact `(decision_time, simulation_phase)` pair. The execution metadata
and `canonical_work_member_keys` must agree with that complete set; they may
not split members into extra boundaries.

### R0 → R1: X creates Y

`next_consequential_boundary(R0)` returns exactly `BX`:

```yaml
source_record_hash: hash(R0)
decision_time: t1/00
simulation_phase: 10
due_work_ids: [work_x]
work_member_keys:
  - [t1/00, 10, work_x]
```

Resolving BX atomically:

```text
advances canonical_clock to t1/00
terminalizes X as succeeded
consumes the one same-clock successor budget
creates active commitment Y
creates work_y at [t1/00, 20, work_y]
records work_y.parent_work_member_key = [t1/00, 10, work_x]
replaces the resolved X schedule with the complete Y boundary
  {decision_time: t1/00, simulation_phase: 20, due_work_ids: [work_y]}
appends one canonical X ledger entry
commits R1
```

R1's canonical ancestry parent and X ledger boundary source must both equal
`hash(R0)`. The complete hash of R1 is computed only after construction; no
record or ledger stores a self-referential successor/post-state hash.

### R1 → R2: rediscovered Y resolves

`next_consequential_boundary(R1)` must query R1, not a retained BX or an R0
itinerary. It returns exactly `BY`:

```yaml
source_record_hash: hash(R1)
decision_time: t1/00
simulation_phase: 20
due_work_ids: [work_y]
work_member_keys:
  - [t1/00, 20, work_y]
```

Resolving BY atomically terminalizes Y as succeeded, leaves the same-clock
budget at zero, removes every work item, appends Y provenance bound to
`hash(R1)`, and commits R2. R2 remains at `t1/00` and has:

```yaml
next_consequential_boundary: none
active_same_clock_work: none
same_clock_budget_remaining: 0
```

Y's success is intentionally neutral. It proves the successor was not merely
created then discarded, and that completing one boundary at a strategic time
does not make a lawful later-phase boundary at that same time invisible.

## Scheduler contract

The scheduler must derive each boundary from current canonical authority only:

```text
next_consequential_boundary(record)
  → validate complete schedule, execution metadata, and budget representation
  → select earliest unresolved canonical boundary key where
        decision_time >= record.canonical_clock
  → return every unresolved due-work member at that exact
        (decision_time, simulation_phase) boundary, ordered by work_id
  → include the matching complete ordered work_member_keys list
  → bind result.source_record_hash = hash(record)
```

For this fixture there is exactly one due work item at each returned boundary.
The return shape is nevertheless a complete ordered set. A future proof may
exercise multiple members within one boundary; this proof does not grant that
behavior or permit implementations to change the boundary law for it.

The resolver accepts only a boundary whose source hash, boundary key, complete
ordered due-work set, and matching member-key list exactly match the current
query result. A boundary becomes stale as soon as its source record has a
successor, even when successor and parent share one clock token.

```text
BX.source_record_hash = hash(R0)
R1 is committed at the same t1/00
BX cannot resolve R1
BY.source_record_hash = hash(R1)
```

## Required witnesses

All primary witnesses start from byte-identical R0 and have no external input:

```text
A. dense throughout
   R0 → local samples → X → R1 → local samples → Y → R2

B. boundary jump throughout
   R0 → X → R1 → Y → R2

C. dense → demote → boundary jump
   R0 → local samples → demote → X → R1 → Y → R2

D. boundary jump → promote → dense
   R0 → X → promote → local samples → Y → R2
```

At each of R0, R1, and R2, A–D must be byte-identical in:

```yaml
canonical_envelope: exact
canonical_hash: exact
canonical_clock: t0/00 | t1/00 | t1/00
canonical_ancestry_parent: exact
authoritative_ledger: exact
commitment_terminal_states: exact
same_clock_budget: exact
future_schedule: exact
next_consequential_boundary: exact
```

Only resolution-local samples, cache, and diagnostics may differ. Each policy
must replay byte-identically under the existing repository replay contract.

## Required failure witnesses

Each malformed boundary or creation attempt rejects before any canonical
mutation, ledger append, clock advance, budget consumption, or schedule change:

1. same-clock successor phase equals or precedes X phase;
2. same-clock successor phase exceeds the frozen phase limit;
3. duplicate `work_y`, duplicate canonical work-member key, or noncanonical
   due-work ordering;
4. cyclic generation that attempts `Y → X` or any already-settled work ID;
5. creation when the authoritative same-clock budget is exhausted;
6. retained BX attempts resolution against R1;
7. fabricated BY attempts resolution against R0;
8. crossing boundary attempts to skip the lawful R1 Y key;
9. a policy/cache/trace supplies a phase, gate result, budget, schedule, or
   resolver result; and
10. promotion or demotion creates, destroys, redirects, or retains
    authoritative same-clock state.

Cross-policy checkpoint divergence is not a transactional rejection. It is an
equivalence-oracle failure and must preserve all candidate artifacts for
inspection.

## Source-audit acceptance gate

The source audit must mechanically establish:

1. exactly one canonical `next_consequential_boundary` implementation;
2. exactly one canonical resolver for X and Y;
3. boundaries carry source record hash, phase-aware boundary keys, and
   complete ordered work-member sets;
4. phase/key/budget validation precedes any canonical mutation;
5. no precomputed multi-boundary itinerary or retained prior boundary has
   authority after a successor commits;
6. local policy/cache/trace/promotion/demotion cannot write canonical phase,
   budget, schedule, key, gate, ledger, disposition, or resolver choice;
7. X may create only the declared same-clock successor; Y cannot create one;
8. no randomness, external inputs, Unreal, city nouns, planner, or additional
   commitment exists; and
9. no canonical ledger or record stores a self-referential successor hash.

## Acceptance question

This proof may seal only when its implementation evidence can answer yes to:

```text
same R0
+ same canonical X boundary
+ one lawful same-clock successor creation
+ different non-authoritative resolution policies
────────────────────────────────────────────────────────
same R1 and R2 authoritative causal history

and

R1 at the same canonical clock
→ rediscover BY from R1 only
→ resolve Y once, later in canonical phase order
→ terminate with no same-clock work remaining
```

## Explicit exclusions

This frozen authorization does not choose same-time external-input arbitration,
general multi-work phase batching, production phase limits, production
budgeting, stochastic draws, city content, Unreal, streaming, networking,
rollback, save/load, map scale, or production-scale execution.

## Freeze record

This v0.1.0 freeze authorizes exactly: one
`SameClockSuccessorSemanticsPayload.v1` validator and serializer; one canonical
boundary-discovery query; one resolver for the neutral X-to-Y chain; the four
declared resolution-policy witnesses; the listed malformed-boundary and local
authority rejections; deterministic replay; source audit; evidence artifacts;
and a self-excluding release manifest. It authorizes no additional fixture,
same-time arbitration policy, or city behavior.

## Changelog

### v0.1.0 — 2026-08-26

- Froze the neutral same-clock successor proof under
  `SameClockSuccessorSemanticsPayload.v1` and simulation version
  `0.7.0-draft.47`.
- Authorized only the bounded canonical implementation and evidence scope.

### v0.1.0-draft.1 — 2026-08-26

- Distinguished canonical boundaries `(decision_time, simulation_phase)` from
  complete `work_id`-ordered boundary-member sets.

### v0.1.0-draft.0 — 2026-08-26

- Opened the same-clock successor specification for review.
