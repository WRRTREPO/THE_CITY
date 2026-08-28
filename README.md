# THE_CITY

THE_CITY is a proof-driven architecture for a 1–4 player co-op open-city FPS
whose persistent causal city, rather than its local encounters, is the
strategic authority.

> **The city holds facts; the crew's presence renders those facts into detail.**

**Current sealed proof record:** [Canonical Occupancy Transition Proof — v0.1.0](Canonical%20Occupancy%20Transition%20Proof%20Evidence%20-%20v0.1.0.md).
The governing continuation is [v0.7.0-draft.73](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md).
[Simultaneous Physical Domains Proof v0.1.0](Simultaneous%20Physical%20Domains%20Proof%20-%20Draft.md)
is frozen under `SimultaneousPhysicalDomainsProof.v1` / `0.7.0-draft.72`. It
reuses the exact sealed Phase-1 H0/H1 canonical transition while requiring two
process-isolated Unreal representations to remain alive across the commit and
obey one fail-closed harness-private current-head observer and
head-unconfirmed/synchronized/stale/invalid/protocol-invalid physical-head law.
The head-qualified physical guard cannot gate canonical execution; its
guard-open control ends failed-closed after canonical H1 still commits. Refresh
rebuilds canonical-derived representation facts only from exact H1 plus the exact projection, while a
separate live-UE probe must observe `available` at H0 and `blocked` after H1.
The exact process-liveness, proof-semantic-input, release-DAG, member-set, and
manifest contracts are frozen and pass the exact structural document validator
plus its 25 adversarial self-tests. Implementation authority is limited to the
exact named Phase-3 paths and bounded dispatch branch. Evidence remains
unsealed, no Phase-3 runtime behavior is yet proven, and Development Capacity
v0.1.11 is unchanged.
The [Resolution Semantics Law v0.1.1](Resolution%20Semantics%20Law%20-%20v0.1.1.md)
and its implemented [substrate proof v0.1.0](Resolution%20Semantics%20Substrate%20Proof%20-%20Draft.md)
are sealed. Causal-LOD Equivalence, record-relative chronological resolution,
external-input interception, and same-clock successor semantics are proven
only in their stated neutral canonical fixtures. Concurrent external evidence
arbitration is proven only for one sealed two-member R0-bound batch. Canonical
spatial topology identity is proven only for one exact two-site/one-unordered-route
fixture with one access mutation and two fresh read-only UE materializations.

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
| [Resolution Semantics Substrate](Resolution%20Semantics%20Substrate%20Proof%20Evidence%20-%20v0.1.0.md) | Exact canonical-envelope authority, next-boundary discovery, and promotion/demotion preserve causal truth before Causal-LOD Equivalence is attempted. |
| [Causal-LOD Equivalence](Causal-LOD%20Equivalence%20Proof%20Evidence%20-%20v0.1.0.md) | Dense inspection, boundary jump, and mixed local-policy execution reach byte-identical canonical history through one resolver. |
| [Record-Relative Chronological Resolution](Record-Relative%20Chronological%20Resolution%20Proof%20Evidence%20-%20v0.1.0.md) | After every committed boundary, the next due work is rediscovered from that successor record; dense and boundary-jump policies match at R0/R1/R2/R3. |
| [External Input Boundary](External%20Input%20Boundary%20Proof%20Evidence%20-%20v0.1.1.md) | Valid external evidence can become an earlier canonical boundary inside a skipped interval; the later autonomous commitment revalidates its ordinary gate from the input successor record. |
| [Same-Clock Successor Semantics](Same-Clock%20Successor%20Semantics%20Proof%20Evidence%20-%20v0.1.0.md) | One boundary can create one later-phase successor at the same canonical time under finite canonical authority; the successor is rediscovered from its committed parent record. |
| [Integrated Unreal Promotion-Unload-Repromotion](Integrated%20Unreal%20Promotion-Unload-Repromotion%20Proof%20Evidence%20-%20v0.1.0.md) | A real UE source interaction emits exact Q; its source process is destroyed before canonical continuation; an isolated fresh UE process materializes the evolved final record only. |
| [Concurrent External Evidence Arbitration](Concurrent%20External%20Evidence%20Arbitration%20Proof%20Evidence%20-%20v0.1.0.md) | Two UE domains with disjoint proof roots physically emit distinct evidence against the same R0; one canonical batch orders, revalidates, and publishes one atomic R1 independent of physical or presentation order. |
| [Canonical Spatial Topology Identity](Canonical%20Spatial%20Topology%20Identity%20Proof%20Evidence%20-%20v0.1.0.md) | Two exact canonical sites and one unordered canonical route retain their endpoint identity through one access mutation, total source-representation destruction, and isolated fresh UE reconstruction; labels and Actor identity remain non-authoritative. |
| [Canonical Occupancy Transition](Canonical%20Occupancy%20Transition%20Proof%20Evidence%20-%20v0.1.0.md) | One exact subject leaves settled site B, enters one resource-owning canonical transition, and settles at site A only after a fresh Rtransit-bound completion; blocked access fails ordinarily without occupancy or reservation residue. |

The current capacity record is [THE_CITY Development Capacity and Progress Note — v0.1.11](THE_CITY%20Development%20Capacity%20and%20Progress%20Note%20-%20v0.1.11.md).

## Verification

Validate the frozen Phase-3 specification contract without executing a Phase-3
runtime:

```sh
cd "/Users/boandersson/Desktop/Games/THE_CITY"
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/thecity_pycache \
  python3 proof_kernel/validate_simultaneous_physical_domains_spec.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/thecity_pycache \
  python3 proof_kernel/validate_simultaneous_physical_domains_spec.py --self-test
```

Run the complete Python regression record:

```sh
cd "/Users/boandersson/Desktop/Games/THE_CITY/proof_kernel"
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/thecity_pycache \
  python3 -m unittest -v \
  test_kernel.py test_roundtrip.py test_contention.py \
  test_unreal_authority_boundary.py test_deployment_opportunity.py \
  test_live_commitment.py test_shared_state_interference.py \
  test_bounded_agent_selection.py test_resolution_semantics_substrate.py \
  test_causal_lod_equivalence.py test_record_relative_chronological_resolution.py \
  test_external_input_boundary.py test_same_clock_successor_semantics.py \
  test_integrated_unreal_promotion_unload_repromotion.py \
  test_concurrent_external_evidence_arbitration.py \
  test_canonical_spatial_topology_identity.py \
  test_canonical_occupancy_transition.py
```

The Phase 2 manifest binds the exact continuation, README, and handover bytes at
seal commit `638e1ac`. After a successor continuation opens, verify that sealed
package from an isolated export of its commit:

```sh
cd "/Users/boandersson/Desktop/Games/THE_CITY"
phase2_seal_dir="$(mktemp -d /private/tmp/thecity-phase2-seal.XXXXXX)"
git archive 638e1ac | tar -x -C "$phase2_seal_dir"
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/thecity_pycache \
  python3 "$phase2_seal_dir/proof_kernel/verify_canonical_occupancy_transition_release.py" verify
rm -rf -- "$phase2_seal_dir"
```

This verifies **33/33** sealed members. Running that verifier against a later
working continuation must fail on the changed current-state documents; do not
rewrite the sealed manifest to conceal that version boundary.

The `CityMaterializationProof/README.md` remains the focused UE 5.8
materialization and physical-evidence guide. It is intentionally not the
project-wide architecture record.

## Not yet proven

This is not a production-scale city simulation. The record does not yet prove:

- map-scale streaming, population, performance, or long-horizon stability;
- multiple crews, split fireteams, live input collection, networking,
  rollback, save/load, or host migration;
- stale intelligence, agent memory, learning, generalized planning, or multi-agent strategy;
- economy, civilians, traffic, repair, damage gradation, or production content density;
- physical or generalized multi-subject occupancy/movement, directionality,
  distance, derived travel time, pathfinding, production Bridge topology,
  proven simultaneous live-domain rebinding, or a generalized city graph;
- that the demonstrated opportunity pressure remains readable and fun at scale.

Each future capability requires a separately selected, frozen, and verified
proof. The sealed kernel is evidence of an authority architecture, not
permission to infer production readiness.
