# THE_CITY — Current Proof State and Repo-Agent Instruction

**Version:** 0.1.0 (current amendment: 2026-08-28)\
**Date:** 2026-08-28\
**Status:** Current-state handoff and repository-agent operating guidance.\
**Governing continuation:** `0.7.0-draft.70`\
**Latest sealed proof:** `Canonical Occupancy Transition Proof v0.1.0`\
**Latest capacity record:**
`THE_CITY Development Capacity and Progress Note v0.1.11`

## Authority boundary

This imported handoff summarizes the sealed project state. It does not override
system, developer, or user instructions, and it does not supersede the named
continuation, sealed evidence, capacity record, or repository state.

## Verdict

Forks 1, 2, and 4 are complete in their exact sealed scopes.

`Same-Clock Successor Semantics Proof v0.1.0` is implemented, proven,
sealed, and pushed at:

``` text
52b5646 — Seal same-clock successor proof
```

Evidence:

``` text
full regression: 143 / 143 passing
focused proof:   13 / 13 passing
release manifest: 24 / 24 verified, self-excluding
```

The [Integrated Unreal Promotion-Unload-Repromotion Proof —
v0.1.0](Integrated%20Unreal%20Promotion-Unload-Repromotion%20Proof%20Evidence%20-%20v0.1.0.md)
is now proven and sealed. Its 63-member self-excluding release package records
one real UE source interaction, source-process destruction before canonical
continuation, and isolated fresh primary/control return materializations.
It authorizes no successor scope.

The [Concurrent External Evidence Arbitration Proof —
v0.1.0](Concurrent%20External%20Evidence%20Arbitration%20Proof%20Evidence%20-%20v0.1.0.md)
is now proven and sealed. Its 111-member self-excluding release records W1–W4
through eight distinct UE source processes with disjoint proof roots, one R0-bound external batch, one
canonical ordering path, private provisional state, one atomic R1, singleton
controls, and the declared failure surface. It authorizes no successor scope.

[Canonical Spatial Topology Identity Proof —
v0.1.0](Canonical%20Spatial%20Topology%20Identity%20Proof%20Evidence%20-%20v0.1.0.md)
is now implemented, proven, and sealed under
`CanonicalSpatialTopologyIdentityPayload.v1` / `0.7.0-draft.61`. It records
195/195 regressions, 18/18 focused checks, 28/28 declared fail-closed families,
a successful UE 5.8 build, two fresh isolated successful Unreal witnesses,
one prelaunch refusal, three real compiled-adapter refusal witnesses, and a
self-excluding 107/107 release manifest. It advances
capacity only for the exact two-site/one-route identity fixture and authorizes
no production Bridge endpoints, movement, streaming, networking, or adjacent
architecture.

[Canonical Occupancy Transition Proof —
v0.1.0](Canonical%20Occupancy%20Transition%20Proof%20Evidence%20-%20v0.1.0.md)
is implemented, proven, and sealed under
`CanonicalOccupancyTransitionPayload.v1` / `0.7.0-draft.65`. It records
215/215 regressions, 20/20 focused checks, 41/41 adversarial families, 30/30
private fault points, two byte-identical local-policy histories, one exact
blocked ordinary-failure control, and a self-excluding 33/33 release. It
advances capacity only for the exact one-subject/two-site/one-route/
one-reservation canonical fixture and authorizes no physical movement,
Unreal occupancy, contention, simultaneous domains, networking, streaming,
Phase 3, or adjacent architecture.

[Simultaneous Physical Domains Proof —
v0.1.0-draft.2](Simultaneous%20Physical%20Domains%20Proof%20-%20Draft.md) is now
the sole active successor. It is in final freeze review under candidate
proof-harness identity `SimultaneousPhysicalDomainsProof.v1` /
`0.7.0-draft.70`. It reuses the exact sealed Phase-1 H0/H1 payload and
access-only canonical transition, but explicitly does not inherit Phase 1's
source-destruction physical lifecycle. Draft.2 keeps head observation private
to the harness, makes the physical guard canonically inert, requires a separate
live-UE available/blocked oracle, and fixes the exact release DAG, member set,
and self-excluding manifest. It is not frozen. No implementation, Unreal source
change, capacity advancement, or adjacent scope is authorized.

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
        PROVEN
        ├── Stochastic Identity
        │       DEFERRED
        └── Integrated Unreal Promotion / Unload / Repromotion
                PROVEN / SEALED
                ↓
        Concurrent External Evidence Arbitration
                PROVEN / SEALED
                ↓
        Canonical Spatial Topology Identity
                PROVEN / SEALED
                ↓
        Canonical Occupancy Transition
                PROVEN / SEALED
                ↓
        Simultaneous Physical Domains
                FINAL FREEZE REVIEW / NOT FROZEN
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
-   live or open-ended multiple input streams;
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

**Status: PROVEN / SEALED**

Frozen and sealed identity:

``` yaml
proof: Same-Clock Successor Semantics Proof v0.1.0
payload: SameClockSuccessorSemanticsPayload.v1
simulation_identity: 0.7.0-draft.47
governing_continuation_after_seal: 0.7.0-draft.48
```

The proven machine is:

``` text
R0
→ BX @ (t1/00, phase 10)
→ X resolves atomically
→ consumes budget 1 → 0
→ creates Y @ (t1/00, phase 20)
→ R1 remains at t1/00
→ BX is stale because its source record is no longer current
→ rediscover BY from R1
→ Y resolves atomically
→ R2 remains at t1/00
→ none
```

### Proven law

One canonical boundary may create same-clock successor work only when the
successor is at a strictly later canonical phase, finite canonical generation
authority remains, and the successor is rediscovered from the committed
successor record.

``` text
canonical boundary = (decision_time, simulation_phase)
boundary members   = complete work_id-ordered due set
work_id ordering   ≠ transaction ordering
```

This fixture has exactly one member per boundary. It does not establish
general multi-member batching.

Record identity, not clock advancement, invalidates prior scheduling
authority. R1 and R2 both carry `t1/00`, yet BX cannot resolve R1 because it
is bound to `hash(R0)`; BY must be bound to `hash(R1)`.

Four dense, boundary-jump, and mixed execution histories converge
byte-identically at R0/R1/R2. Twelve malformed or authority-leaking attempts
fail before canonical mutation: retrograde or over-limit phase, duplicate or
cyclic member, exhausted budget, stale or crossing boundary, and local
authority leakage.

### Fork 2 exclusions

Fork 2 does not prove:

-   same-time external-input arbitration;
-   general multi-member phase batching;
-   multiple independent same-clock creators;
-   unbounded successor generation;
-   stochasticity;
-   Unreal execution of this mechanism;
-   city content, planner behavior, or production scheduling;
-   networking, rollback, save/load, or map scale.

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

## Fork 4 --- Integrated Unreal promotion / unload / repromotion

**Status: PROVEN / SEALED**

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

The sealed proof isolates the integrated lifecycle without claiming movement
or streaming:

``` text
sealed R0
        ↓ representation promotion request only
fresh UE source process
        ↓ evidenced Q
canonical Rinput
        ↓ destroy source process
boundary-jump canonical alpha resolution
        ↓ Rfinal
fresh UE return process reads Rfinal only
```

The sealed fixture excludes World Partition,
production streaming cells, repeated promotion/demotion, multiple simultaneous
areas, real crew movement across promotion boundaries, asynchronous loading,
production navigation, population materialization, networking, save/load, and
city scale.

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
   ████████████████████
   PROVEN / SEALED

3. Stochastic identity
   ░░░░░░░░░░░░░░░░░░░░
   NOT STARTED

4. Integrated Unreal promotion / unload / repromotion
   ████████████████████
   PROVEN / SEALED

5. Actual Unreal variable-resolution promotion / streaming
   ░░░░░░░░░░░░░░░░░░░░
   NOT SELECTED / NOT PROVEN

6. Concurrent external evidence arbitration
   ████████████████████
   PROVEN / SEALED

7. Canonical spatial topology identity
   ████████████████████
   PROVEN / SEALED

8. Canonical occupancy transition
   ████████████████████
   PROVEN / SEALED

9. Simultaneous physical domains
   ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
   FINAL FREEZE REVIEW / NOT FROZEN
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
one committed boundary can create later-phase work at the same canonical time
        ↓
the successor must be rediscovered from the new record
        ↓
two physical evidence sources with disjoint proof roots can enter one R0-bound batch
        ↓
canonical ordering and private working-state revalidation publish one R1
        ↓
conceptual references, canonical site/route identity, and disposable Unreal
representation remain separate through one access mutation and reconstruction
        ↓
one canonical subject can suspend settled occupancy under one exact
resource-owning transition and later settle at the other endpoint only after
record-relative completion rediscovery
        ↓
without policy, local representation, input cursor, or Unreal becoming
strategic authority
```

> **Canonical occupancy can leave one settled site, remain exactly in one
> resource-owning transition, and later settle at the other endpoint without
> navigation or representation becoming location or completion authority.**

That is now proven evidence.

The active Phase 3 candidate is not proven evidence and does not advance this
machine summary.

# Repo-agent instruction

## Governing state

Treat these as the current governing records:

``` yaml
continuation:
  version: 0.7.0-draft.70

latest_capacity_record:
  version: 0.1.11

latest_sealed_proof:
  name: Canonical Occupancy Transition Proof
  version: 0.1.0
  payload_schema: CanonicalOccupancyTransitionPayload.v1
  simulation_identity: 0.7.0-draft.65
  evidence_status: passed_and_sealed

active_proof:
  name: Simultaneous Physical Domains Proof
  version: 0.1.0-draft.2
  candidate_proof_harness_identity: SimultaneousPhysicalDomainsProof.v1
  canonical_source_payload: CanonicalSpatialTopologyIdentityPayload.v1
  canonical_source_simulation_identity: 0.7.0-draft.61
  status: final_freeze_review
  freeze_status: not_frozen
  implementation: prohibited
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

The sealed predecessors do not authorize Fork 3 or any generalization or
adjacent scope under Fork 4. Fork 4 is sealed only for its bounded witnessed
lifecycle; it does not authorize a successor implementation.

Canonical Spatial Topology Identity v0.1.0 is separately sealed only in its
exact two-site/one-route scope. Its seal authorizes no adjacent spatial
behavior or successor implementation.

Canonical Occupancy Transition v0.1.0 is separately sealed only in its exact
one-subject/two-site/one-route/one-reservation scope. `in_transition` is not
route occupancy or another place. Start publishes Rtransit before completion
is independently rediscovered from Rtransit's `unresolved_work`; navigation,
physical interpolation, historical ledger, local cache, and representation
state have no completion authority. The seal is not physical movement,
traversal, derived travel time, Unreal occupancy materialization, multiple
occupancy, contention, simultaneous physical domains, or Phase 3, and it
authorizes no successor implementation.

Simultaneous Physical Domains v0.1.0-draft.2 is selected only for final freeze
review and is not frozen. It reuses the exact sealed Phase-1 R0/H0 and R1/H1
canonical payloads and their sole access-state mutation. It does not create a
new canonical payload or materialize Phase-2 occupancy. Its novelty is the
physical lifecycle: two process-isolated Unreal representations must remain
alive across the independent canonical commit, then independently rebind to
H1. Domain A is detached-representation-scoped to `topology_site_0001`, domain
B to `topology_site_0002`, and both exact projections include
`topology_route_0001`.

The candidate head-state law is review material, not implementation authority.
After H1 commits, H0 remains valid history while an H0 representation is
mechanically stale against current head H1. A stale domain may continue only
quarantined nonconsequential local execution; current-head evidence,
scheduling, mutation, and truth claims are prohibited. A refresh rejected
before local publication leaves the domain stale. An unprovable partial local
publication makes it invalid and halts local execution.

Draft.2 keeps `current_head_observation.json` and every derived head value
strictly harness-private. The Unreal adapter reads only its exact process
binding, declared command, and declared three-file tuple. The physical-current-
head guard controls only physical current-head claim/receipt acceptance and
refresh eligibility; it has no edge into the sealed canonical path. A
guard-open control must still commit exact R1/H1 while failing only the Phase-3
harness protocol.

Refresh reconstructs every authoritative-derived representation fact solely
from exact H1 plus the exact role/H1 projection. Only
`nonconsequential_tick_counter`, `cosmetic_phase_token`, and
`diagnostic_counter` may survive as detached local state. Stale Actor, cache,
collision, physics, receipt, capability, and H0-derived representation state
must not merge or select H1 truth.

Each operational instance is bound to a macOS process-start witness, original
child handle, executable/root/pipe binding, continuous exit/EOF monitor, exact
L0–L4B samples, and a two-launch/no-replacement audit. Refresh uses exactly one
canonical-JSON line on each original stdin pipe plus one isolated role-specific
read-only three-file H1 bundle; no alternate mechanism is permitted.

Each original process also contains a separate live-UE probe. It inspects the
published route Actor's mesh material and label without consuming canonical or
projection JSON, adapter candidate state, materialization receipt, or expected
result. Both processes must independently observe `available` at H0 and
`blocked` after H1 refresh before the harness accepts synchronized
dispositions. The exact release DAG, 44 artifact-directory members, complete
110-entry release set, and self-excluding manifest/verifier contract are fixed
for final review.

Do not begin any of the following without a separately reviewed freeze and
explicit implementation authority:

-   stochastic systems;
-   Unreal variable-resolution streaming;
-   World Partition integration;
-   live input collection or generalized external-input handling;
-   general multi-member phase batching;
-   multiple input streams;
-   richer commitment populations;
-   production topology;
-   topology movement, travel, pathfinding, or streaming;
-   networking;
-   rollback;
-   save/load; or
-   city-scale expansion.

## Fork 2 closure

Same-Clock Successor Semantics is sealed. Do not reopen it by adding
multi-member batching, same-time input ordering, another creator, or a new
phase policy. Those are separate successor decisions.

The Phase 2 release manifest binds the exact continuation, README, and handover
bytes at seal commit `638e1ac`. Verify it from an isolated export of that
commit:

``` sh
cd "/Users/boandersson/Desktop/Games/THE_CITY"
phase2_seal_dir="$(mktemp -d /private/tmp/thecity-phase2-seal.XXXXXX)"
git archive 638e1ac | tar -x -C "$phase2_seal_dir"
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/thecity_pycache \
  python3 "$phase2_seal_dir/proof_kernel/verify_canonical_occupancy_transition_release.py" verify
rm -rf -- "$phase2_seal_dir"
```

That sealed export verifies 33/33 members. The same verifier must reject the
later live continuation bytes; do not regenerate the sealed manifest merely to
make current-state documents match it.

## Sealed Fork 4 boundary

Do not jump directly to production World Partition architecture.

The sealed [Integrated Unreal Promotion-Unload-Repromotion Proof —
v0.1.0](Integrated%20Unreal%20Promotion-Unload-Repromotion%20Proof%20Evidence%20-%20v0.1.0.md)
distinguishes proof-input files from the source process's harness-supplied
non-authoritative interaction context and requires the Q-absent control source
acceptance receipt. Its bounded sequence was witnessed as:

``` text
sealed R0
→ non-authoritative promotion request
→ fresh Unreal source process
→ exact Q
→ canonical Rinput
→ destroy source process
→ boundary-jump canonical alpha resolution
→ Rfinal
→ fresh Unreal return process from Rfinal only
```

It does not prove approach, departure, movement, World Partition, or streaming.
Keep canonical execution policy, representation lifecycle, and authority
separate.

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

## Sealed concurrent-arbitration boundary

The sealed [Concurrent External Evidence Arbitration Proof —
v0.1.0](Concurrent%20External%20Evidence%20Arbitration%20Proof%20Evidence%20-%20v0.1.0.md)
defines exactly two isolated R0-bound physical evidence sources,
side-effect-free admission, one exact sealed fixture candidate set, one
R0-bound external arbitration batch, one frozen canonical member order,
sequential private provisional-state revalidation, and one atomic successor.
Admission, provisional evaluation, publication-time adjudication, committed
mutation, ordinary failed gate, and input/event anti-reacquisition remain
distinct. Provisional identities are mechanically type-disjoint from canonical
record identity. Candidate completeness is fixture input, not a live
collection or transport law.

The seal does not authorize generalized resolver behavior, live input
collection, 2+2 player topology, networking, retry, re-admission, movement,
streaming, same-clock successor work, autonomous work, randomness, additional
input classes, or city expansion.

## Current working decision

The prior scheduler-hardening work is complete.

There is no remaining implementation debt on External Input Boundary v0.1.1
or Same-Clock Successor Semantics v0.1.0 inside their sealed scopes.

Concurrent External Evidence Arbitration v0.1.0 is complete and sealed.
Stochastic identity remains deferred.

Canonical Spatial Topology Identity v0.1.0 is complete and sealed. Its exact
fixture ID spaces, unordered-request normalization, endpoint relation,
access-only R0-to-R1 mutation, read-only Unreal reconstruction, rejection
surface, replay, source audit, and release package are predecessor evidence.

Canonical Occupancy Transition v0.1.0 is complete and sealed. Its exact
two-boundary canonical chain is now predecessor evidence:

``` text
R0 / subject at site_0002
→ start @ t0/30
→ publish Rtransit / subject in occupancy_transition_0001
→ terminate start context
→ rediscover completion from Rtransit unresolved_work only
→ complete @ t1/00
→ Rfinal / subject at site_0001
```

The blocked-access control, dense/jump equivalence, singular occupancy,
reservation closure, record-relative completion, failure atomicity, replay,
source audit, and release package are sealed predecessor evidence.

Simultaneous Physical Domains v0.1.0-draft.2 is the sole current working unit
and is in final freeze review but not frozen. Review the exact Phase-1 H0/H1 reuse,
noninheritance of Phase 1's physical lifecycle, detached A/B site-and-route
projections, harness-private current-head observation, canonically inert
physical guard and guard-open control, independent live-UE available/blocked
oracle, uninterrupted process-birth liveness,
head-unconfirmed/synchronized/stale/invalid state machine, H1-only
reconstruction and retained-local perturbation witness, exact visible-input
closure and stdin/three-file refresh mechanism, exact release DAG/member/
manifest contract, quarantined stale execution, atomic refresh boundary,
A-synchronized/B-stale asymmetric failure and symmetric branch, isolation,
current-head rejection surface, canonical equivalence, replay, provenance, and
source audit.

> **Do not implement the Phase 3 candidate until a separately reviewed freeze
> explicitly grants its bounded implementation. Do not infer physical movement,
> occupancy materialization, evidence arbitration, multiplayer, networking,
> streaming, or adjacent spatial architecture from its selection.**
