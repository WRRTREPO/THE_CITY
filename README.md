# THE_CITY

THE_CITY is a proof-driven architecture for a 1–4 player co-op open-city FPS
whose persistent causal city, rather than its local encounters, is the
strategic authority.

> **The city holds facts; the crew's presence renders those facts into detail.**

**Current sealed proof record:** `a15c3a5`. The governing continuation is
[v0.7.0-draft.32](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md).
The [Resolution Semantics Law v0.1.1](Resolution%20Semantics%20Law%20-%20v0.1.1.md)
and its [substrate proof v0.1.0](Resolution%20Semantics%20Substrate%20Proof%20-%20Draft.md)
are frozen. No implementation or successor scope is authorized.

## The machine

```text
AUTHORITATIVE CITY RECORD
        │
        ├── agents perceive bounded state
        ├── choose feasible actions
        ├── propose commitments
        └── canonical transactions revalidate and mutate truth
        │
        ▼
LOCAL FPS MATERIALIZATION
        │
        └── physical player outcome produces evidence only
        │
        ▼
CANONICAL VALIDATION + LEDGER
        │
        ▼
NEW AUTHORITATIVE CITY RECORD
        │
        ▼
FRESH MATERIALIZATION
```

The Python canonical layer owns strategic time, state, commitment creation,
ordering, validation, durable mutations, and causal provenance. Unreal owns
local first-person materialization and may emit exact physical-evidence
proposals. Unreal cannot write city truth or causal-ledger entries.

## What is proven

| Proof | Established boundary |
| --- | --- |
| [Three-Area Causal Proof Kernel](Three-Area%20Causal%20Proof%20Kernel%20-%20Draft.md) | Fire, routes, police, factions, resources, commitments, gates, and thresholds produce one deterministic causal history. |
| [Unreal Materialization](Unreal%20Materialization%20Proof%20Evidence%20-%20v0.1.0.md) | Sealed authoritative records become distinct walkable UE 5.8 worlds without rerolling. |
| [Bridge Access Persistence Round Trip](Bridge%20Access%20Persistence%20Round-Trip%20Evidence%20-%20v0.1.1.md) | Physical consequence → evidence → canonical mutation → fresh FPS rematerialization. |
| [Bridge Traversal Contention](Bridge%20Access%20Traversal%20Contention%20Proof%20Evidence%20-%20v0.1.1.md) | Canonical order controls contention; an entered route segment survives later admission closure. |
| [Crew Deployment Opportunity Cost](Crew%20Deployment%20Opportunity-Cost%20Proof%20Evidence%20-%20v0.1.0.md) | One shared crew has one active physical-evidence domain while unattended city causality continues. |
| [Crew Arrival into Live Commitment](Crew%20Arrival%20Into%20Live%20Commitment%20Proof%20Evidence%20-%20v0.1.0.md) | A crew enters an already-live commitment, changes a future gate, and cannot reopen settled history. |
| [Shared-State Commitment Interference](Shared-State%20Commitment%20Interference%20Proof%20Evidence%20-%20v0.1.0.md) | Independently defined commitments interfere through ordinary shared-state revalidation, not authored coupling. |
| [Bounded Agent Commitment Selection](Bounded%20Agent%20Commitment%20Selection%20Proof%20Evidence%20-%20v0.1.0.md) | A pure agent selector chooses from bounded perception and submits a proposal; canonical authority alone creates the active reservation. |

The current capacity record is [THE_CITY Development Capacity and Progress Note — v0.1.2](THE_CITY%20Development%20Capacity%20and%20Progress%20Note%20-%20v0.1.2.md).

## Verification

Run the complete Python regression record:

```sh
cd "/Users/boandersson/Desktop/Games/THE_CITY/proof_kernel"
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/thecity_pycache \
  python3 -m unittest -v \
  test_kernel.py test_roundtrip.py test_contention.py \
  test_unreal_authority_boundary.py test_deployment_opportunity.py \
  test_live_commitment.py test_shared_state_interference.py \
  test_bounded_agent_selection.py
```

Verify the latest sealed release package:

```sh
cd "/Users/boandersson/Desktop/Games/THE_CITY"
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/thecity_pycache \
  python3 proof_kernel/verify_bounded_agent_selection_release.py verify
```

The `CityMaterializationProof/README.md` remains the focused UE 5.8
materialization and physical-evidence guide. It is intentionally not the
project-wide architecture record.

## Not yet proven

This is not a production-scale city simulation. The record does not yet prove:

- map-scale streaming, population, performance, or long-horizon stability;
- multiple crews, split fireteams, networking, rollback, save/load, or host migration;
- stale intelligence, agent memory, learning, generalized planning, or multi-agent strategy;
- economy, civilians, traffic, repair, damage gradation, or production content density;
- that the demonstrated opportunity pressure remains readable and fun at scale.

Each future capability requires a separately selected, frozen, and verified
proof. The sealed kernel is evidence of an authority architecture, not
permission to infer production readiness.
