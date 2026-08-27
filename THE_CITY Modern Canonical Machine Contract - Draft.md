# THE_CITY Modern Canonical Machine Contract

**Version:** 0.1.0-draft.0
**Status:** doctrine extraction / specification review only
**Implementation authority from this document:** none
**Successor-proof authority:** none
**City-scope expansion authority:** none

## Status and purpose

This draft extracts general authority architecture already demonstrated by
THE_CITY's sealed proof records. It is neither a new proof nor permission to
generalize a proof fixture.

It changes no sealed claim, capacity claim, code authority, release identity,
or frozen proof specification. Any rule not supported by the sources below
must be marked **candidate doctrine** and cannot become governing law merely
by appearing here.

The currently frozen [Integrated Unreal Promotion-Unload-Repromotion Proof —
v0.1.0](Integrated%20Unreal%20Promotion-Unload-Repromotion%20Proof%20-%20Draft.md)
remains the sole implementation target. Its implementation is unsealed. This
parallel documentation review neither suspends nor alters that authority.

## Source authority

### Normative machine-law sources

The following repository records support governing statements in this draft:

- [Persistent City Simulation — Initial Systems Note](Persistent%20City%20Simulation%20-%20Initial%20Systems%20Note.md), the frozen v0.6 foundational player/world contract;
- [Resolution Semantics Law — v0.1.1](Resolution%20Semantics%20Law%20-%20v0.1.1.md);
- [Resolution Semantics Substrate Proof Evidence — v0.1.0](Resolution%20Semantics%20Substrate%20Proof%20Evidence%20-%20v0.1.0.md);
- [Causal-LOD Equivalence Proof Evidence — v0.1.0](Causal-LOD%20Equivalence%20Proof%20Evidence%20-%20v0.1.0.md);
- [Record-Relative Chronological Resolution Proof Evidence — v0.1.0](Record-Relative%20Chronological%20Resolution%20Proof%20Evidence%20-%20v0.1.0.md);
- [External Input Boundary Proof Evidence — v0.1.1](External%20Input%20Boundary%20Proof%20Evidence%20-%20v0.1.1.md);
- [Same-Clock Successor Semantics Proof Evidence — v0.1.0](Same-Clock%20Successor%20Semantics%20Proof%20Evidence%20-%20v0.1.0.md);
- [Unreal Materialization Proof Evidence — v0.1.0](Unreal%20Materialization%20Proof%20Evidence%20-%20v0.1.0.md);
- [Bridge Access Persistence Round-Trip Evidence — v0.1.1](Bridge%20Access%20Persistence%20Round-Trip%20Evidence%20-%20v0.1.1.md); and
- [Crew Arrival Into Live Commitment Proof Evidence — v0.1.0](Crew%20Arrival%20Into%20Live%20Commitment%20Proof%20Evidence%20-%20v0.1.0.md).

### Current-scope and spatial-framing sources

[Co-op Open-City FPS Simulation — v0.7 Working Continuation](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)
and [THE_CITY Current Proof State and Repo-Agent Instruction — v0.1.0](THE_CITY%20Current%20Proof%20State%20and%20Repo-Agent%20Instruction%20-%20v0.1.0.md)
govern the present scope, sealed/unsealed status, and implementation authority.
They do not independently prove a machine law.

[THE_CITY Conceptual City Topology and Developer Framing v0.2.0](THE_CITY_Conceptual_City_Topology_Developer_Framing_v0.2.0.md)
supplies the current **candidate doctrine** for spatial identity separation.
It does not establish a production topology, streaming implementation, or
canonical spatial schema.

`Modern-canonical-machine-v1.0.txt` is not present in this repository and is
not cited by this draft. Historical drafts are provenance only; they cannot
override sealed evidence, the frozen foundational contract, or current scope.

## Governing machine law

> **Authority lives in the current canonical record. Everything else is a
> capability, proposal, representation, cache, policy, observation, or piece
> of evidence whose authority expires or must be revalidated against that
> record.**

```text
CURRENT CANONICAL RECORD
        ↓
RECORD-BOUND BOUNDARY DISCOVERY / ADMISSION
        ↓
ONE DECLARED CANONICAL RESOLUTION PATH
        ↓
ATOMIC SUCCESSOR RECORD
        ↓
PREDECESSOR AUTHORITY INVALIDATED
        ↓
REDISCOVER FROM SUCCESSOR
```

For a given simulation identity and canonical boundary, resolution policy may
not select an alternate causal semantics path. A physical or operational
system may provide evidence, but it cannot replace the canonical transition.

## Canonical record contract

The current canonical record owns strategic truth. Where applicable, its exact
payload owns current causal facts; active and terminal commitments; causally
relevant resource ownership and reservations; unresolved future work; accepted
external-input identities; canonical ancestry; and authoritative provenance.

`CanonicalResolutionEnvelope` is the fixed authority container. A separately
versioned payload schema is the exhaustive authoritative field contract for a
particular implementation identity. Both identities participate in canonical
serialization and hashing.

No implementation may silently add an authoritative field under an unchanged
payload-schema identity. A changed authority container, hash boundary,
scheduler-discovery law, or promotion/demotion discard law requires a new
container-schema and law version.

## Record-relative authority

Every execution capability binds to the exact canonical record from which it
was discovered or admitted. A successor commit invalidates predecessor-bound
capabilities even when its canonical clock has not advanced.

After every committed consequential boundary, prior scheduling views have no
authority, the next boundary is discovered from the successor record, and no
precomputed authoritative itinerary survives the commit.

> **Record identity, not clock advancement, determines continuation
> authority.**

## Canonical boundary and member contract

An autonomous canonical boundary has a `decision_time` and, where phase
semantics apply, a `simulation_phase`. Boundary members form the complete
canonical due set for that boundary and use stable `work_id` ordering for
member identity and provenance.

`work_id` ordering does not independently create a transaction boundary. This
contract does not claim a generalized multi-member batching policy beyond the
sealed boundary/member law.

Same-clock successor work is lawful only under the demonstrated constraints:

- its canonical phase is strictly later than its creator's phase;
- it consumes finite canonical generation authority;
- it is absent from the predecessor schedule and rediscovered from the
  committed successor record; and
- its causal parentage is explicit without converting member order into hidden
  transaction order.

## Canonical resolver contract

For each simulation identity and canonical boundary, one declared canonical
resolution path owns source-record binding validation, gate/resource
revalidation against current canonical state, deterministic contention/order
where defined, atomic mutation, terminal resource disposition,
causal-provenance append, and successor construction.

Canonical decisions may not depend on a resolution-local cache, diagnostic
trace, representation-lifecycle state, Unreal state, branch selector, cached
authoritative gate result, or policy-selected alternate resolver path.

## Resolution-policy contract

Resolution policy may alter how much non-authoritative work is represented or
executed between consequential boundaries. It may not change the authoritative
state required to determine any future consequential boundary.

```yaml
resolution_policy:
  may_change:
    - local samples
    - cache
    - diagnostics
    - resolution-local representation detail
  may_not_change:
    - canonical facts
    - commitments
    - resource authority
    - future consequential work
    - boundary identity
    - causal ledger
    - ancestry
```

Within sealed resolution semantics, promotion and demotion are non-causal
resolution-local transitions. They may create or discard only disposable local
state; they may not manufacture or discard authority. This is not a claim that
production Unreal streaming, proximity promotion, or city-scale physical
representation has been proven.

## External-input contract

```text
external evidence
    non-authoritative
        ↓
side-effect-free admission
        ↓
record-bound execution capability
        ↓
canonical transaction
```

Observation alone does not create city truth. Admission is side-effect-free.
An admitted capability binds to its exact source record, and the resulting
canonical transaction may change only its declared canonical facts.

An input cannot directly choose a later autonomous terminal result. Later
autonomous work must be rediscovered from the successor record and revalidate
its ordinary gates there.

This contract does not generalize same-time input arbitration, late input,
retry or consumption semantics, multiple streams, trusted network transport,
rollback, or reconciliation.

## Historical finality contract

The sealed Crew Arrival proof establishes this narrow law:

> **Admitted evidence may change current facts and future eligibility, but
> cannot reopen a completed canonical disposition unless a separately
> specified canonical rule authorizes a new transition.**

A completed disposition remains completed. Later lawful evidence may change a
current fact, affect future eligibility, or create new lawful history, but it
may not silently rewrite that disposition. This is not a universal prohibition
on future post-settlement transitions; each requires its own explicit canonical
rule and proof.

## Representation and identity contract

Unreal or another physical representation may validate and materialize sealed
canonical truth, resolve local physical detail, and emit evidence of
consequential physical outcomes. It may not advance canonical strategic time,
choose canonical execution policy, discover autonomous work, resolve canonical
commitments, write canonical records, write the authoritative ledger, or
become canonical identity.

### Candidate doctrine — spatial identity mapping

The following spatial identity boundary is carried forward from current
developer framing. It is candidate doctrine pending explicit adoption; it does
not claim a sealed production-topology proof.

Canonical spatial identity is never inferred from a representation. The
following identities are not implicitly equivalent:

```text
conceptual map identity
canonical area / site / route identity
Unreal Actor identity
Level Instance identity
World Partition cell identity
streaming identity
navigation identity
render identity
```

They require explicit mapping contracts where a relation is needed. This does
not select a production topology, World Partition arrangement, or streaming
architecture.

The Integrated Unreal Promotion-Unload-Repromotion proof is frozen and
implemented but unsealed. Its lifecycle integration claim is not a proven rule
of this contract until its physical-action evidence and release sealing pass.

## Provenance and successor identity

Every committed consequence requires inspectable causal provenance sufficient
to identify its source/pre-state authority, gates, resource disposition, and
result. Successor identity is computed only after the complete successor record
exists.

Canonical records and ledger entries may not contain self-referential
successor hashes. Canonical pre-state references and successor ancestry are
recorded canonically; successor identity is established by hashing the complete
successor record externally.

Observation and materialization cannot reroll completed history. Current facts
change only through new lawful canonical transitions.

## Failure atomicity

The demonstrated failure classes fail closed before unauthorized canonical
mutation:

```text
invalid source binding
invalid schema
invalid boundary
stale capability
crossing capability
authority leakage
illegal promotion/demotion mutation
invalid external evidence or admission
retrograde same-clock successor
same-clock generation-budget exhaustion
────────────────────────────────────────
→ no unauthorized canonical mutation
```

Some classes were demonstrated only in bounded fixtures. This contract does
not claim their full production generalization without an explicit successor
proof.

## Randomness boundary

```yaml
authoritative_randomness:
  status: prohibited
  until: separately specified, proven, and explicitly adopted
```

This contract introduces no random-stream identity, stochastic draw, or
random-consumption semantics.

## Explicit non-claims

This contract neither proves nor authorizes production city scale, World
Partition or production streaming, repeated city-scale promotion/demotion,
multiple crew bubbles, networking or host migration, rollback or generalized
save/load, stochastic identity, generalized planning, population/traffic/
economy, production topology, exact travel/proximity laws, performance,
long-horizon stability, fun, balance, pacing, player readability, or completion
and sealing of the Integrated Unreal lifecycle proof.

## Contract evolution

```text
sealed predecessor contract
→ explicit falsifiable proof question
→ frozen bounded proof
→ implementation
→ evidence / seal
→ doctrine extraction review
→ versioned contract amendment
```

A successful fixture does not automatically amend this contract. Human review
must explicitly adopt any extracted general law in a versioned amendment.
Historical contract versions remain immutable.

## Draft.0 review gate

This draft is ready for review only when:

1. every governing statement traces to repository-present sealed evidence or a frozen foundational contract;
2. no unavailable source is cited;
3. fixture nouns are absent from doctrine;
4. historical finality uses the narrow Crew Arrival law;
5. no unsealed Integrated Unreal result is promoted to proven doctrine;
6. no stochastic, production-topology, or streaming law is invented;
7. `CanonicalResolutionEnvelope` and exact payload-schema authority remain distinct;
8. record-relative rediscovery and predecessor-capability invalidation are explicit;
9. external evidence, admission, and canonical transaction remain distinct;
10. resolution policy and representation remain non-authoritative;
11. provenance and successor identity remain self-hash-safe; and
12. the spatial identity mapping remains marked candidate doctrine pending explicit adoption; and
13. this document grants no implementation, successor-proof, or city-expansion scope.
