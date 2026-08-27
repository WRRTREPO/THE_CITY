# THE_CITY --- Current Proof State and Repo-Agent Instruction

**Version:** 0.1.0\
**Date:** 2026-08-26\
**Status:** Current-state handoff and repository-agent operating guidance.\
**Governing continuation:** `0.7.0-draft.46`\
**Latest sealed proof:** `External Input Boundary Proof v0.1.1`\
**Latest capacity record:**
`THE_CITY Development Capacity and Progress Note v0.1.6`

## Authority boundary

This imported handoff summarizes the sealed project state. It does not override
system, developer, or user instructions, and it does not supersede the named
continuation, sealed evidence, capacity record, or repository state.

## Verdict

Fork 1 is complete.

`External Input Boundary Proof v0.1.1` is implemented, proven, sealed,
and pushed at:

``` text
634c0d7 — Seal external input boundary proof
```

Evidence:

``` text
full regression: 130 / 130 passing
focused proof:   13 / 13 passing
release manifest: 25 / 25 verified, self-excluding
```

No successor city scope is authorized by the seal.

## Current proof progression

``` text
Resolution Semantics Substrate
        PROVEN
        ↓
Causal-LOD Equivalence
        PROVEN
        ↓
Record-Relative Chronological Resolution
        PROVEN
        ↓
External Input During Skipped Time
        PROVEN
        ↓
Same-Clock Successor Semantics
        NOT PROVEN
        ↓
Stochastic Identity
        NOT STARTED
        ↓
Actual Unreal Variable-Resolution Promotion / Streaming
        NOT PROVEN
```

Record-relative chronological resolution remains an essential
intermediate proof. It established that after every committed
consequential boundary, the next boundary is rediscovered from the new
canonical record. No authoritative future itinerary is retained.

## Fork 1 --- External input during skipped time

**Status: PROVEN / SEALED**

Frozen and sealed identity:

``` yaml
proof: External Input Boundary Proof v0.1.1
payload: ExternalInputBoundaryPayload.v1.1
simulation_identity: 0.7.0-draft.45
governing_continuation_after_seal: 0.7.0-draft.46
```

The proven machine is:

``` text
R0
│
├── autonomous alpha is due later
│
└── player-originated evidence Q occurs first
        ↓
side-effect-free admission validation
        ↓
R0-bound BQ execution capability
        ↓
canonical input transaction
        ↓
Rinput
        ↓
rediscover autonomous work from Rinput
        ↓
alpha reads changed canonical state
        ↓
ordinary gate revalidation
        ↓
Rfinal
```

### Proven law

A valid player-originated evidence input can interrupt an interval that
boundary-jump execution would otherwise skip.

Q may change a canonical fact. Q may not directly choose, cancel,
terminalize, reschedule, or manufacture the outcome of later autonomous
work.

``` text
Q
→ changes canonical fact
→ Rinput

alpha
→ unchanged autonomous definition
→ later reads Rinput
→ ordinary gate passes or fails
```

No lawful shortcut exists equivalent to:

``` text
if Q:
    fail alpha
```

Four materially different local execution histories converge
byte-identically at `R0`, `Rinput`, and `Rfinal`. Only resolution-local
samples, cache, and diagnostics may differ.

The coordinator/scheduler distinction is proven:

``` text
R0:
    next_consequential_boundary = alpha @ t1/00
    next_execution_boundary     = BQ @ t0/30

Rinput:
    next_consequential_boundary = alpha @ t1/00
    next_execution_boundary     = alpha @ t1/00

Rfinal:
    next_consequential_boundary = none
    next_execution_boundary     = none
```

The autonomous scheduler does not know about Q. The input-aware
coordinator intercepts the earlier lawful input, commits it canonically,
then autonomous work is rediscovered from the successor.

### Self-hash correction

The original `v0.1.0` specification contained a self-referential
successor-hash defect. `v0.1.1` corrected it without introducing a
second authority projection.

``` text
KEEP:
    canonical_pre_state_hash
    successor canonical_ancestry.parent_record_hash

DO NOT STORE:
    canonical_post_state_hash inside the successor record
```

Successor hashes are computed only after complete successor construction
and verified externally.

``` text
R0
→ transaction records H0 as pre-state
→ construct complete Rinput
→ compute HI externally

Rinput
→ transaction records HI as pre-state
→ construct complete Rfinal
→ compute HF externally
```

No canonical record stores its own hash.

### Fork 1 exclusions

Fork 1 does not prove:

-   live input transport;
-   wall-clock / active-world synchronization;
-   same-time input versus autonomous ordering;
-   late evidence;
-   malformed-input retry or consumption semantics;
-   multiple input streams;
-   multiple autonomous commitments under input pressure;
-   randomness;
-   Unreal execution of this exact temporal mechanism;
-   production-scale Causal-LOD;
-   networking;
-   rollback;
-   save/load;
-   map scale; or
-   production streaming.

## Fork 2 --- Same-clock successor semantics

**Status: NOT PROVEN / NEXT CLEAN SCHEDULER RISK**

The existing scheduler permits unresolved work where:

``` text
decision_time >= canonical_clock
```

But the chronological proof deliberately prohibited creation of new
same-clock successor work. External Input Boundary also excludes
same-time input/autonomous arbitration.

The unresolved case is:

``` text
X resolves at t1/00
        ↓
X lawfully creates Y
with decision_time = t1/00
        ↓
???
```

A possible future law might be:

``` text
same decision_time
+ later lawful phase / canonical execution key
→ Y remains immediately due
```

That is not current law.

A future proof must decide and mechanically prove:

-   whether same-clock successor creation is legal;
-   what ordering domain owns it;
-   whether a successor may execute at the same canonical decision time;
-   what prevents infinite same-clock work generation;
-   how phase/key monotonicity is enforced;
-   how already-settled work is excluded after rediscovery;
-   whether same-clock work interacts with external-input arbitration;
    and
-   fail-closed behavior for cyclic, duplicate, stale, crossing, or
    retrograde work.

No implementation is authorized until this proof is explicitly selected,
reviewed, and frozen.

## Fork 3 --- Stochastic identity

**Status: NOT STARTED / DELIBERATELY DEFERRED**

Authoritative randomness remains excluded.

There is no proven:

``` text
canonical random stream
random draw identity
commitment-addressed draw
event-addressed draw
stochastic replay identity
resolution-independent random consumption law
```

Do not introduce randomness merely to create apparent unpredictability.

Select this fork only when a concrete city requirement needs uncertainty
that cannot be represented correctly through deterministic hidden state,
bounded perception, competing commitments, or external input.

Until then:

> **Authoritative randomness remains prohibited.**

## Fork 4 --- Actual Unreal promotion / streaming under variable resolution

**Status: PREREQUISITES PROVEN / INTEGRATED PROOF NOT STARTED**

Already proven separately:

1.  sealed canonical records can materialize as distinct walkable UE 5.8
    worlds without reroll;
2.  Unreal physical outcomes can emit evidence that only the canonical
    layer may commit;
3.  fresh Unreal processes can rematerialize committed durable state;
4.  promotion/demotion can preserve canonical authority;
5.  dense, boundary-jump, and mixed resolution policies can converge in
    the neutral Causal-LOD fixture;
6.  player-originated evidence can interrupt skipped causal time without
    granting local authority.

Still unproven is the integrated production-shaped loop:

``` text
distant canonical area
        ↓
coarse / boundary-jump execution
        ↓
crew approaches
        ↓
Unreal representation streams / materializes
        ↓
simulation representation promotes
        ↓
player observes / interacts
        ↓
durable physical consequence emits evidence
        ↓
canonical transaction
        ↓
crew leaves
        ↓
representation demotes / unloads
        ↓
canonical simulation continues
        ↓
later re-promotion preserves history
```

This is not yet proven under World Partition, production streaming
cells, repeated promotion/demotion, multiple simultaneous areas, real
crew movement across promotion boundaries, asynchronous loading,
production navigation, population materialization, networking,
save/load, or city scale.

Preserve the identity law:

``` text
canonical spatial identity
        ≠
Unreal Actor identity
        ≠
Level Instance identity
        ≠
World Partition cell identity
        ≠
streaming identity
```

## Current fork status

``` text
1. External input during skipped time
   ████████████████████
   PROVEN / SEALED

2. Same-clock successor semantics
   ░░░░░░░░░░░░░░░░░░░░
   NOT PROVEN

3. Stochastic identity
   ░░░░░░░░░░░░░░░░░░░░
   NOT STARTED

4. Actual Unreal variable-resolution promotion / streaming
   ███████░░░░░░░░░░░░░
   PREREQUISITES PROVEN
   INTEGRATED PROOF NOT STARTED
```

The bars are illustrative. The textual statuses are authoritative.

## What the machine now proves

``` text
canonical authority survives promotion/demotion
        ↓
different local resolution policies can converge
        ↓
future boundaries are rediscovered from each committed record
        ↓
player-originated evidence can interrupt skipped causal time
        ↓
the resulting canonical fact can alter later autonomous eligibility
        ↓
without policy, local representation, input cursor, or Unreal becoming
strategic authority
```

> **Player action can enter skipped causal time without giving local
> resolution authority.**

That is now proven evidence.

# Repo-agent instruction

## Governing state

Treat these as the current governing records:

``` yaml
sealed_commit:
  id: 634c0d7
  message: Seal external input boundary proof

continuation:
  version: 0.7.0-draft.46

latest_capacity_record:
  version: 0.1.6

latest_sealed_proof:
  name: External Input Boundary Proof
  version: 0.1.1
```

Older continuation snapshots, README files, draft states, and superseded
proof versions are historical when they conflict with these records.

## Preserve sealed scope

The repository is a proof record, not permission to generalize
successful fixtures.

Do not silently modify sealed proof meaning.

If a defect is found:

``` text
preserve original
→ record defect
→ create versioned successor
→ review
→ freeze
→ implement
→ rerun proof
→ reseal
```

## No implicit successor work

Fork 1 being sealed does not authorize Forks 2--4.

Do not begin any of the following without explicit successor selection:

-   same-clock successor implementation;
-   stochastic systems;
-   Unreal variable-resolution streaming;
-   World Partition integration;
-   generalized external-input handling;
-   multiple input streams;
-   richer commitment populations;
-   production topology;
-   networking;
-   rollback;
-   save/load; or
-   city-scale expansion.

## If Fork 2 is selected

Open **Same-Clock Successor Semantics** as a specification only.

Do not write implementation before freeze.

Use the smallest neutral machine:

``` text
R0 @ t1/00
→ X resolves
→ R1 remains at t1/00
→ X has lawfully created Y due at t1/00
→ rediscover from R1
→ determine whether Y is immediately due
```

The proof must define and test:

``` yaml
same_clock_successor:
  legality:
    - may canonical resolution create unresolved work at canonical_clock?

  ordering:
    - exact phase/key relation required for a lawful successor
    - successor may not sort before the work that created it
    - retrograde ordering must fail closed

  rediscovery:
    - next boundary comes from the successor record
    - already-settled work cannot reacquire authority

  termination:
    - prevent infinite same-clock successor chains
    - require a mechanically provable monotonic progression law
    - fail closed when monotonic progress is impossible

  authority:
    - canonical state alone determines same-clock eligibility
    - policy/cache/trace cannot manufacture or retain work

  provenance:
    - every successor boundary is bound to the exact source record

  equivalence:
    - dense, boundary-jump, and mixed policies converge at every canonical checkpoint

  rejection:
    - stale boundary
    - crossing boundary
    - retrograde phase/key
    - duplicate successor
    - cyclic successor generation
    - local-policy scheduler override
```

Do not solve same-time external-input arbitration inside this proof
unless explicitly authorized.

## If Fork 4 is selected instead

Do not jump directly to production World Partition architecture.

Open a bounded integrated Unreal proof first:

``` text
canonical coarse state
→ approach
→ promotion
→ fresh Unreal materialization
→ one evidenced player consequence
→ canonical commit
→ departure
→ demotion / unload
→ continued canonical resolution
→ re-promotion
→ same durable consequence remains
```

Keep canonical spatial identity separate from Unreal/streaming
identities.

## Acceptance discipline for every successor proof

Before implementation, every proof must freeze:

``` yaml
proof_contract:
  question: one falsifiable question
  parent_laws: exact sealed predecessors
  authority_owner: exact canonical owner
  mutation_boundary: exact transaction boundary
  payload_schema: new fixed identity where semantics change
  canonical_state: exhaustive field contract
  non_authoritative_state: explicit disposable state
  scheduler_boundary: exact discovery semantics
  failure_atomicity: exact no-mutation rejection behavior
  provenance: exact inspectable causal evidence
  replay: deterministic reproduction requirement
  equivalence: required canonical checkpoints
  source_audit: forbidden authority paths
  exclusions: explicit non-claims
  release_manifest: self-excluding and mechanically verified
```

A passing fixture does not authorize generalization beyond its frozen
claim.

## Current next decision

The previous unfinished job is complete.

There is no remaining implementation debt on External Input Boundary
v0.1.1 inside its sealed scope.

The next legitimate decision is:

``` text
A. Same-Clock Successor Semantics
   recommended if continuing canonical scheduler hardening

or

B. First integrated Unreal variable-resolution promotion/streaming proof
   if the project now needs to cross from canonical proof machinery
   toward the actual FPS embodiment loop
```

Stochastic identity remains deferred until a concrete requirement makes
authoritative uncertainty necessary.

Until a successor is explicitly selected:

> **Hold the sealed state. Do not expand the machine.**
