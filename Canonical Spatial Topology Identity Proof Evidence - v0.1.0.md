# Canonical Spatial Topology Identity Proof Evidence

**Version:** 0.1.0
**Date:** 2026-08-27
**Status:** Passed and sealed
**Specification:** [Canonical Spatial Topology Identity Proof v0.1.0](Canonical%20Spatial%20Topology%20Identity%20Proof%20-%20Draft.md)
**Payload:** `CanonicalSpatialTopologyIdentityPayload.v1`
**Simulation identity:** `0.7.0-draft.61`

## Result

The bounded Phase 1 spatial-identity claim passes.

```text
detached conceptual references
        ↓ reviewed assignment only
exact canonical site_A + site_B + route_AB
        ↓ read-only detached materialization map
fresh UE representation
```

Conceptual labels, canonical topology identity, and physical representation
identity remain mechanically distinct. The canonical record alone owns the
two site identities, the one route identity, its unordered endpoint relation,
and its access state.

## Canonical witnesses

The exact frozen checkpoints regenerate deterministically:

```yaml
R0:
  canonical_hash: 666d75281d3478e586edd12464d2736169f423c2d7b128bd3d2d2b1b2b826b29
  route: topology_route_0001
  endpoints: [topology_site_0001, topology_site_0002]
  endpoint_semantics: unordered_pair_fixture_only
  access_state: available

R1:
  canonical_hash: 78cc5ffe0c4758c296d8fee0bc2a95e230be0bec0a4aab680806eb670500804a
  parent_record_hash: 666d75281d3478e586edd12464d2736169f423c2d7b128bd3d2d2b1b2b826b29
  route: topology_route_0001
  endpoints: [topology_site_0001, topology_site_0002]
  endpoint_semantics: unordered_pair_fixture_only
  access_state: blocked
```

R1 differs from R0 in exactly the frozen six places: route access, fixture
process state, canonical clock, unresolved work, the one authoritative ledger
entry, and singular H0-bound ancestry. No canonical field stores H1.

Forward and reversed endpoint requests both normalize to the stored pair and
produce identical semantic evaluation:

```text
[site_0001, site_0002] ─┐
                        ├─ normalize → [site_0001, site_0002]
[site_0002, site_0001] ─┘

R0 → eligible = true
R1 → eligible = false
```

Renaming the three conceptual display labels changes the detached assignment
raw hash while leaving its label-neutral projection, canonical targets, R0
stored bytes, and H0 identical.

## Real UE 5.8 lifecycle

The source and return witnesses were acquired from two real, fresh UE 5.8
processes through physically disjoint proof roots.

```text
R0-only proof root
→ P0 verifies payload + map + detached receipt
→ materializes two sites, one route, access AVAILABLE
→ emits one detached materialization receipt
→ P0 terminates
→ complete source process root is destroyed

only then:

next_consequential_boundary(R0)
→ H0-bound canonical resolution
→ R1

then:

new disjoint R1-only proof root
→ P1 verifies payload + map + detached receipt
→ materializes the same canonical sites/route/endpoints, access BLOCKED
→ emits one detached materialization receipt
```

The process IDs differ. The three Actor IDs are pairwise distinct within each
process, and every `(process ID, Actor ID)` representation identity differs
between source and return. Endpoint identity remains unchanged because the
endpoint relation is reconstructed from the accepted canonical record, not
from Actor names or the detached map.

The return process receives no R0, prior Actor, source root, cache, save,
session state, Q, branch selector, or truth-bearing command-line context. The
adapter exposes no physical-evidence/Q proposal path.

Every launched proof process used the installed read-only engine cache plus a
process-private writable DDC clone. Source, return, and refusal-control cache
roots are mutually disjoint; no process used shared Zen storage or launched a
shared Unreal Trace Server.

The representation rejection boundary was also witnessed physically. One
additional-directory candidate was rejected by the production harness before
launch. Three further candidates were launched as direct compiled-adapter
conformance controls: a noncanonical receipt, an altered map, and an R0/R1
cross-row tuple. Each real UE refusal emitted exactly one frozen detached
diagnostic, no materialization receipt, no operational spawn failure, and no
canonical write. Each refusal process group was then proven dead. These
controls perform no canonical resolution and do not increase the successful
materialization count.

## Verification record

```yaml
full_python_regression: 195/195
focused_topology_suite: 18/18
declared_fail_closed_families: 28/28
ue_version: 5.8
ue_editor_build: succeeded
successful_fresh_ue_materializations: 2
compiled_adapter_refusal_processes: 3
prelaunch_rejections: 1
total_ue_processes: 5
canonical_replay: byte_identical
release_manifest: 107/107
manifest_self_excluding: true
```

The 28-family surface includes duplicate JSON members, identity type
substitution, dangling/duplicate/reversed stored endpoints, request-order
semantic leakage, invalid query shapes, conceptual/representation identity
substitution, stale boundary authority, redirected/cross-row materialization
inputs, adapter authority leakage, Q-path exposure, return contamination,
representation-destruction authority loss, and successor self-hash.

Every named variant is fixed by an independent exact matrix, including the
required detached diagnostic stage/reason precedence for representation
failures.

The source audit confirms separate canonical validation, request
normalization/query, mutation, serializer/hash, lifecycle harness, and Unreal
adapter paths. The adapter reads topology and derives local representation; it
cannot manufacture topology, mutate canonical access, write ledger/ancestry,
discover work, resolve a boundary, or emit evidence.

## Proven claim

> **One explicitly specified proof-local two-site/one-route topology can own
> consequential canonical spatial identity independently of conceptual labels
> and Unreal representation identity, preserve its endpoint relation through
> one access mutation, and reconstruct that relation in a fresh process after
> complete representation destruction.**

## Boundary

This evidence does not prove movement, occupancy transitions, directionality,
coordinates, distance, travel time, pathfinding, route capacity, graph search,
production Bridge endpoints, player subdivision, multiple physical domains,
World Partition, streaming, networking, population, or city scale.

No successor scope follows from this seal.
