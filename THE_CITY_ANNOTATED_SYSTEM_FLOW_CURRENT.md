# THE_CITY — Annotated System Flow

Version: `0.2.0`
Updated: 2026-09-13
Status: current architecture map. It records sealed proof, landed implementation, and open work separately.

## Read this first

THE_CITY has one canonical causal world. Python records own truth. Unreal represents local physical state and may propose evidence. Unreal never settles canonical facts.

Phase 3 and Phase 4 are sealed historical proofs. Phase 5 is a frozen specification. Its implementation pipeline landed at commit `44090c6`, but it has not acquired live Unreal evidence or a new seal.

```text
SEALED HISTORY                    CURRENT ENGINEERING                  PRODUCT TARGET
Phase 3: two live domains         Phase 5: pipeline landed             Four players in several places
Phase 4: occupancy materialized   Live acquisition still closed         One city. No history merge.
```

## One canonical city

```text
                                  THE_CITY
                       ONE CANONICAL CAUSAL WORLD

┌───────────────────────────────────────────────────────────────────────┐
│  1. CANONICAL RECORD Rn / Hn                                           │
│                                                                       │
│  Owns: facts, topology, occupancy, commitments, reservations,        │
│  resources, future work, chronology, ancestry, and provenance.       │
│                                                                       │
│  Does not own: Unreal Actors, transforms, animation, streaming cells,│
│  process identity, or presentation order.                             │
└───────────────────────────────┬───────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────┐
│  2. RECORD-BOUND DISCOVERY                                             │
│                                                                       │
│  Ask Rn: "What work is lawful now?"                                   │
│                                                                       │
│  The answer belongs to Rn only. A committed successor kills old        │
│  discovery authority. There is no authoritative future itinerary.      │
└───────────────────────────────┬───────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────┐
│  3. PROPOSALS AND PHYSICAL EVIDENCE                                   │
│                                                                       │
│  AI uses bounded perception and proposes a commitment.                 │
│  Players act in a local FPS world and may produce physical evidence.   │
│                                                                       │
│  Neither path writes city truth directly.                              │
└───────────────────────────────┬───────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────┐
│  4. CANONICAL ADMISSION                                                │
│                                                                       │
│  Check source-record identity, resources, gates, topology,            │
│  reservations, chronology, duplicates, and stale authority.           │
│                                                                       │
│  Bad input becomes an ordinary failure or diagnostic.                  │
│  Good input enters the declared canonical resolution path.             │
└───────────────────────────────┬───────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────┐
│  5. PRIVATE RESOLUTION                                                 │
│                                                                       │
│  Candidates can be ordered and revalidated against private working     │
│  state. Process order, file order, Unreal order, and presentation      │
│  order never become city law.                                           │
└───────────────────────────────┬───────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────┐
│  6. ATOMIC COMMIT: Rn ─────────────► Rn+1                              │
│                                                                       │
│  The successor publishes facts, resource dispositions, commitments,    │
│  future work, provenance, and ancestry together.                       │
│                                                                       │
│  No partial strategic successor escapes.                               │
└───────────────────────────────┬───────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────┐
│  7. REDISCOVER FROM Rn+1                                               │
│                                                                       │
│  Future work is discovered again from the new record. Shared facts     │
│  change. Later actions revalidate. The lawful future can change.       │
└───────────────────────────────────────────────────────────────────────┘
```

## Physical materialization

```text
                         CURRENT CANONICAL HEAD Hn
                                      │
                    exact projection and local binding
                         ┌────────────┴────────────┐
                         ▼                         ▼
                ┌─────────────────┐       ┌─────────────────┐
                │ Physical domain │       │ Physical domain │
                │ A               │       │ B               │
                │ Unreal process  │       │ Unreal process  │
                │ local Actors    │       │ local Actors    │
                │ local physics   │       │ local physics   │
                └────────┬────────┘       └────────┬────────┘
                         │                         │
                         └──── proposes evidence ──┘
                                      │
                                      ▼
                             canonical admission
                                      │
                                      ▼
                                    Rn+1
```

Domains A and B are not two cities. They are disposable local views of one city record.

A physical world can be stale after `Hn → Hn+1`. It may render, animate, settle local physics, and run diagnostics. It cannot claim that its old head is current, schedule canonical work, or mutate city truth. It must be rebound from the new canonical record before it can again produce current-head evidence.

## Sealed Phase-3 example

This is historical proof, not a current Phase-5 claim.

```text
H0
 │
 ├── Domain A alive at H0 ── route observed AVAILABLE
 └── Domain B alive at H0 ── route observed AVAILABLE
 │
 ├── canonical resolver commits H0 → H1 independently
 │
 ├── A and B remain alive but stale at H0
 │
 ├── each domain independently refreshes from exact H1
 │
 └── each independent live-world probe observes BLOCKED
     │
     └── synchronized(H1)
```

If one refresh fails, canonical truth is still `H1`. The failed domain is physically alive but quarantined as stale. There is never an `H1 for A` and an `H0 for B` in canonical truth.

Phase 3 sealed this exact two-domain, access-only fixture. It did not prove general multiplayer, continuous travel, world partition, or a production city.

## Current Phase-5 implementation boundary

```text
Frozen Phase-5 specification
           │
           ▼
Landed implementation pipeline at 44090c6
           │
           ├── source identity and import preflight
           ├── parent-owned acquisition workspace
           ├── bounded Unreal evidence plugin
           ├── independent record and native-image verification
           └── adversarial test and component-reader surfaces
           │
           ▼
      FULL SOURCE-EFFECT AUDIT                 OPEN
           │
           ▼
      LIVE TWO-DOMAIN ACQUISITION              CLOSED
           │
           ▼
      INDEPENDENT RELEASE ACCEPTANCE           CLOSED
           │
           ▼
      NEW EVIDENCE SEAL                        NOT EARNED
```

The code gives the frozen specification a concrete implementation surface. It does not prove a fresh Unreal run.

The fresh current-source reader run passed `22/22` component readers. That is development evidence. It does not complete the full source-effect audit.

## What is sealed

| Boundary | Status | Exact scope |
| --- | --- | --- |
| Canonical causal history | Sealed | Deterministic canonical records, chronology, provenance, and atomic successors in declared fixtures. |
| Record-relative chronology | Sealed | The current record discovers the next lawful boundary. |
| Physical evidence admission | Sealed in declared proofs | Local Unreal outcomes can become bounded evidence after canonical validation. |
| Simultaneous physical domains | Sealed as Phase 3 | Two original Unreal processes survive one exact `H0 → H1` access transition and independently rebind. |
| Cross-domain occupancy materialization | Sealed as Phase 4 | One exact `R0 → Rtransit → Rfinal` occupancy chain across two original live Unreal domains. |

The current capacity record remains `v0.1.11`. Sealed history grants no automatic production scope.

## What is implemented but unsealed

| Surface | Current state |
| --- | --- |
| Phase-5 frozen contract | Fixed at draft `0.1.0-draft.3`. |
| Python harness and independent verifier | Landed at `44090c6`. |
| `CityLiveEvidenceProof` Unreal plugin | Landed with GameMode and Actor code for local evidence behavior. |
| Source identity and component analysis | Executed as development evidence. |
| Live acquisition, source-effect closure, release acceptance | Still denied by explicit fail-closed guards. |

The Phase-5 freeze record remains authoritative for specification status: specification frozen, evidence unsealed, capacity unchanged. A code commit does not alter that record or create a seal.

## Known open gates

| Gate | Current result | Required before it can open |
| --- | --- | --- |
| Full source-effect audit | `145103` graph entries remain unclassified | Audit all four new Python files, seven plugin files, and transitive local imports. Produce every required source edge and reject all fourteen frozen source adversaries. |
| Acquisition | `lcer.acquisition_implementation_incomplete` | Authenticate the complete source audit from disk before build or launch. |
| Release | `lcer.release_semantics_not_implemented` | Supply complete source audit plus actual build, live execution, and release evidence. |
| Stored release replay | `CITY_VERIFIER_TIMEOUT` after 300 seconds | Give the sealed replay an appropriate controlled budget and capture its terminal receipt. |
| Trusted CI | Unproved | Run the accepted workload through a host-owned trusted execution boundary. |

Do not delete or weaken these guards. Replace each one with the proof it demands.

## Four-player product interpretation

```text
                           ONE CITY RECORD R42
                                      │
                    ┌─────────────────┴─────────────────┐
                    ▼                                   ▼
             Player domain A                      Player domain B
                 P1 + P2                              P3 + P4
               Gang nest                              Bank
                    │                                   │
                    └──── local action and evidence ───┘
                                      │
                                      ▼
                             canonical admission
                                      │
                                      ▼
                                ONE SUCCESSOR R43
                                      │
                    ┌─────────────────┴─────────────────┐
                    ▼                                   ▼
             gang view rebinds                    bank view rebinds
```

This is the intended product machine. It is not proven capacity.

If players later reunite, there is nothing to merge. They never left one city history.

## Short form

```text
THE CITY OWNS TRUTH
        ↓
AGENTS AND PLAYERS PROPOSE ACTION OR EVIDENCE
        ↓
THE CURRENT RECORD VALIDATES IT
        ↓
ONE ATOMIC SUCCESSOR COMMITS
        ↓
OLD CURRENT-HEAD AUTHORITY DIES
        ↓
PHYSICAL WORLDS REBIND TO THE SAME NEW TRUTH
        ↓
DIFFERENT PLACES. ONE CITY.
```

## Authority sources

- `handover.md` — current repository routing.
- `PHASE_5_SELECTION.json` and `PHASE_5_FREEZE.json` — frozen Phase-5 specification status.
- `Simultaneous Physical Domains Proof - v0.1.1.md` — sealed Phase-3 boundary.
- `Cross-Domain Canonical Occupancy Materialization Proof Evidence - v0.1.0.md` — sealed Phase-4 boundary.
- `LIVE_EVIDENCE_PIPELINE_IMPLEMENTATION_README.md` — landed Phase-5 implementation and its open failures.
