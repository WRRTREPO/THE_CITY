# THE_CITY — Multi-Presence Canonical Simulation

## Target capacity

THE_CITY must ultimately support **one authoritative persistent simulation with 1–4 independently located physical participants**.

Participants may:

- remain together;
- divide into groups;
- operate individually;
- converge;
- separate again; and
- generate consequential physical evidence concurrently from different materialized regions.

The simulation does not divide when participants divide.

```text
Physical Domain A ─┐
Physical Domain B ─┤
Physical Domain C ─┼──→ ONE CANONICAL CITY
Physical Domain D ─┘
                         ↓
                  ONE ORDERED HISTORY
```

The fundamental invariant is:

> **Multiple physical presences. One canonical authority.**

## Do not inherit the single-crew proof constraint

The existing Crew Deployment Opportunity-Cost proof deliberately restricts the fixture to:

```yaml
crew: one
simultaneous_deployments: one
simultaneous_physical_evidence_domains: one
split_fireteams: prohibited
```

That constraint isolated and proved exclusive opportunity cost. It is not authority to impose the same topology on THE_CITY generally.

Current capacity explicitly records multiple active crews, split fireteams, simultaneous crew bubbles, and 1–4 network arbitration as **not yet proven**.

The required successor architecture therefore expands physical presence without weakening canonical authority.

## Required machine

Conceptually:

```text
                    CANONICAL CITY
                         │
              authoritative chronology
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
     Domain A         Domain B       Domain C ...
          │              │              │
     physical         physical       physical
     simulation       simulation     simulation
          │              │              │
          ▼              ▼              ▼
      evidence         evidence       evidence
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                CANONICAL ADMISSION
                         │
                         ▼
                ORDERED RESOLUTION
                         │
                         ▼
                NEW CANONICAL CITY
```

No materialized domain becomes strategic authority.

No participant directly writes canonical state.

No local simulation owns canonical chronology.

## Physical presence is independent

Each active participant requires an independently tracked physical presence.

At minimum, the eventual model must be capable of representing:

```yaml
participant:
  identity: stable
  physical_location: independent
  materialization_domain: independent
  observation_domain: independent
  physical_action_stream: independent
  consequential_evidence_stream: independent
```

This does **not** imply that these fields belong in this exact form in the canonical schema.

The point is the ownership boundary:

> Participant A's physical location must not constrain Participant B to the same materialization domain merely because both belong to the same session or group.

The physical topology may therefore become:

```text
4

4

3 + 1

2 + 2

2 + 1 + 1

1 + 1 + 1 + 1
```

without creating separate city histories.

## One canonical chronology

Independent physical domains can produce consequential evidence at different times.

Conceptually:

```text
t0/20  participant C evidence
t0/24  autonomous boundary
t0/27  participant A evidence
t0/31  participant D evidence
t0/35  autonomous boundary
```

These cannot become four partially authoritative histories reconciled later.

They must become one canonical chronology.

The existing Record-Relative Chronological Resolution proof establishes the prerequisite law that, after each committed boundary, future consequential work is rediscovered from the resulting canonical successor rather than from a retained itinerary.

Therefore the required shape remains:

```text
R0
 ↓
resolve earliest lawful boundary
 ↓
R1
 ↓
rediscover from R1
 ↓
resolve earliest lawful boundary
 ↓
R2
 ↓
rediscover from R2
 ↓
...
```

Adding more physical evidence sources must not weaken this law.

## External physical evidence

A physical outcome is not canonical truth.

The existing physical round-trip proves the boundary:

```text
physical consequence
→ immutable evidence
→ canonical validation
→ canonical mutation
→ new authoritative record
```



The External Input Boundary specification extends the temporal requirement:

```text
canonical record
    │
    ├── future autonomous boundary
    │
    └── earlier valid external evidence arrives
              ↓
       external-input boundary
              ↓
       canonical successor
              ↓
       rediscover autonomous work
              ↓
       ordinary revalidation
```



Multi-presence THE_CITY therefore needs to generalize from:

```text
one external evidence source
```

toward:

```text
N independently located evidence sources
```

while preserving exactly one admission and resolution authority.

## Shared-state interference is expected

Independent participants do not require explicit relationships to affect one another.

The existing Shared-State Commitment Interference proof establishes the useful underlying law:

> independently defined commitments can interfere solely because they read and write shared authoritative state.

The same architectural property is required for independently located physical participants.

Desired:

```text
Participant A
→ valid physical consequence
→ canonical fact S changes

Participant B
→ later action/commitment
→ ordinary gate reads S
→ eligibility differs
```

Undesired:

```text
if participant_A_did_X:
    modify_participant_B_encounter()
```

Cross-domain effects should emerge through canonical state wherever possible, not through pair-specific participant callbacks.

## Materialization domains are projections

Multiple simultaneous materializations must remain projections of one canonical city.

Conceptually:

```text
                     CANONICAL Rn
                    /     |      \
                   /      |       \
                  ▼       ▼        ▼
             Domain A  Domain B  Domain C
```

Each may contain different high-resolution physical state because each represents different geography.

But none may contradict canonical facts relevant to its region.

The existing Unreal materialization proof establishes this authority direction for bounded records: authoritative state is supplied to the physical representation; the physical representation does not reroll strategic truth.

Multiple domains do not change that law.

## Local state remains local

Not every physical detail belongs in the canonical city.

Each materialized region may contain large amounts of non-authoritative state:

```text
animation state
ragdoll state
temporary particles
exact incidental object placement
local AI representation
rendering state
audio state
navigation caches
physics intermediates
local prediction
diagnostics
```

Only consequential results cross the persistence boundary.

The Resolution Semantics Law already establishes the broader separation:

```text
canonical authority
≠
resolution-local representation
```



Multi-presence must preserve that distinction independently for every materialized region.

## Concurrent evidence is the hard boundary

The unresolved problem is not simply supporting four networked pawns.

The material problem is:

> **What happens when multiple physical domains produce valid consequential evidence close enough in canonical time to contend?**

Example:

```text
Canonical state R

Domain A emits QA
Domain B emits QB
Autonomous work X is also due

QA, QB and X may all touch shared state.
```

The system requires an unambiguous law determining:

```text
admission
ordering
source-record binding
revalidation
mutation
terminal disposition
successor ancestry
```

without allowing:

- arrival order from network transport to become hidden simulation law;
- thread scheduling to become canonical ordering;
- host process iteration order to become authority;
- two evidence inputs to commit against the same stale pre-state independently;
- one domain to overwrite another domain's committed consequence;
- rollback to silently rewrite already-authoritative history;
- local prediction to escape into canonical state; or
- a participant to gain authority by owning or hosting a physical domain.

This is the central future proof boundary.

## Source-record capabilities must expire

Existing record-relative proofs establish a useful rule:

> A capability bound to Rn loses authority once Rn has produced a canonical successor.

Therefore:

```text
QA bound to R0
→ commits
→ R1 exists

QB previously bound to R0
→ cannot simply commit against R0
```

QB must be handled under an explicitly defined future multiplayer/input law.

Possible behavior is intentionally **not specified here**.

It may require revalidation, rejection, rebinding, deterministic same-boundary ordering, or another explicitly proven mechanism.

Do not infer that policy from the current proofs.

## Networking must not become authority

Eventually the physical domains will be network distributed.

The authority hierarchy must remain:

```text
NETWORK TRANSPORT
      ↓
delivers observations/evidence

PHYSICAL SIMULATION
      ↓
produces candidate consequential evidence

CANONICAL ADMISSION
      ↓
validates authority to attempt mutation

CANONICAL RESOLVER
      ↓
owns ordering and mutation

CANONICAL RECORD
      ↓
owns truth
```

Not:

```text
host wins
```

or:

```text
first packet wins
```

or:

```text
client result becomes canonical because
that client simulated the physical event
```

Network transport is evidence transport, not simulation authority.

## Persistence does not change the rule

A persistent city increases the cost of getting this wrong.

A transient session can sometimes tolerate reconciliation artifacts.

THE_CITY cannot.

A bad authority decision can survive:

```text
current session
→ persistence
→ future materialization
→ later commitments
→ downstream consequences
→ subsequent sessions
```

The canonical mutation boundary therefore has to remain inspectable and deterministic enough that a persistent historical defect can be reconstructed.

The causal ledger is not optional debugging decoration.

It is part of the machine's ability to explain how the current city came to exist.

## Required eventual capacity

The intended capacity can be stated compactly:

```yaml
canonical_city:
  count: 1
  chronology: 1
  strategic_authority: exclusive

physical_presence:
  simultaneous_participants: 1..4
  locations: independent
  grouping: unrestricted_by_simulation
  convergence: supported
  separation: supported

materialization:
  simultaneous_domains: 1..4
  canonical_authority: none

physical_evidence:
  simultaneous_sources: 1..4
  direct_canonical_mutation: prohibited

canonical_input:
  validates: all_consequential_evidence
  orders: all_admitted_boundaries
  stale_authority: rejected_or_explicitly_resolved
  successor_ancestry: singular

autonomous_simulation:
  continues_during_physical_activity: true
  rediscovered_after_each_canonical_successor: true

history:
  authoritative_records: singular
  divergent_city_histories: prohibited
```

This is a **target capacity description**, not a claim that these capacities are currently proven.

## Current proven boundary

Today THE_CITY has separately established important prerequisites:

- deterministic canonical history;
- physical-to-canonical consequence crossing;
- canonical-to-physical rematerialization;
- temporal contention;
- independent commitment interference through shared state;
- record-relative chronological rediscovery;
- resolution-policy neutrality in bounded fixtures; and
- a frozen specification for one external input interrupting otherwise skippable autonomous time. 
It has **not** established:

```text
multiple simultaneous physical evidence domains
multiple independent participant input streams
same-time external-input ordering
network arbitration
rollback
host migration
multi-domain prediction/reconciliation
shared persistent ownership
```

Those remain unresolved.

## Programmer rule

Do not build THE_CITY around an assumption that all participants occupy one physical domain.

Also do not implement speculative multiplayer authority merely to remove that restriction.

Preserve the distinction:

```text
PRODUCT CAPACITY
1–4 independent physical presences
inside one persistent causal city

CURRENT PROOF CAPACITY
one physical evidence domain
plus bounded canonical input/resolution proofs

NEXT ARCHITECTURAL PROBLEM
prove multiple physical evidence sources
can enter one canonical chronology
without creating multiple authorities
```

The machine we are protecting is:

> **One city. One chronology. Multiple simultaneous physical presences.**