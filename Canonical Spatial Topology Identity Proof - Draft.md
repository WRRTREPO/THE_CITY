# Canonical Spatial Topology Identity Proof

**Version:** 0.1.0-draft.0\
**Status:** specification review only; implementation is not authorized\
**Selected:** 2026-08-27\
**Parent continuation:** [Co-op Open-City FPS Simulation — v0.7 Working Continuation](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)\
**Conceptual source:** [THE_CITY Conceptual City Topology and Developer Framing v0.3.0](THE_CITY_Conceptual_City_Topology_Developer_Framing_v0.3.0.md)\
**Latest sealed predecessor:** [Concurrent External Evidence Arbitration Proof — v0.1.0](Concurrent%20External%20Evidence%20Arbitration%20Proof%20Evidence%20-%20v0.1.0.md)\
**Candidate simulation identity:** `0.7.0-draft.60` — not frozen

## Question

> **Can one explicitly specified proof-local two-site/one-route topology own
> consequential spatial identity independently of conceptual labels and
> physical representation identity, preserve its endpoint relation through one
> canonical access mutation, and reconstruct that relation in a fresh Unreal
> process?**

This is the first proof aimed specifically at the design-time boundary:

```text
CONCEPTUAL GEOGRAPHIC REFERENCE
        ↓ explicit reviewed assignment
CANONICAL SPATIAL TOPOLOGY
        ↓ non-authoritative materialization mapping
PHYSICAL REPRESENTATION
```

It is **not** the first repository fixture to contain areas or routes. The
three-area kernel already contains fixture-local `A`, `B`, `C`, `E_AB`, and
`E_BC` causal facts and route behavior. This proof asks a narrower question
that those records do not answer: whether conceptual references, canonical
site/route identities, and Unreal representation identities are mechanically
separate and connected only by explicit mappings.

## Governing predecessor boundary

This candidate composes, but does not reopen, the following sealed records:

- [Proof Kernel Implementation Evidence — v0.1.1](Proof%20Kernel%20Implementation%20Evidence%20-%20v0.1.1.md), for fixture-local canonical areas, routes, eligibility, and replay;
- [Unreal Materialization Proof Evidence — v0.1.0](Unreal%20Materialization%20Proof%20Evidence%20-%20v0.1.0.md), for read-only sealed-record materialization;
- [Bridge Access Persistence Round-Trip Evidence — v0.1.1](Bridge%20Access%20Persistence%20Round-Trip%20Evidence%20-%20v0.1.1.md), for access-state mutation and fresh rematerialization;
- [Integrated Unreal Promotion-Unload-Repromotion Proof Evidence — v0.1.0](Integrated%20Unreal%20Promotion-Unload-Repromotion%20Proof%20Evidence%20-%20v0.1.0.md), for fresh-process receipt verification, destruction, isolation, and return materialization;
- [Record-Relative Chronological Resolution Proof Evidence — v0.1.0](Record-Relative%20Chronological%20Resolution%20Proof%20Evidence%20-%20v0.1.0.md), for source-record-bound boundary authority and post-commit invalidation;
- [Same-Clock Successor Semantics Proof Evidence — v0.1.0](Same-Clock%20Successor%20Semantics%20Proof%20Evidence%20-%20v0.1.0.md), for the phase-aware canonical boundary/member distinction; and
- [Resolution Semantics Law — v0.1.1](Resolution%20Semantics%20Law%20-%20v0.1.1.md), for the canonical envelope, payload-schema, hashing, and representation-authority boundary.

The unproven seam is explicit endpoint referential integrity and the identity
mapping across conceptual, canonical, and representation layers. Existing
`E_AB` names and hardcoded Unreal geometry do not prove that seam.

The imported v0.3.0 conceptual source has exact SHA-256
`1466cf486eb8be952b2927d83ad8f5bd3938a98fe48f163856d10b152159955d`.
That digest proves which framing bytes were reviewed; it grants no runtime or
canonical authority.

## Authority state

This draft opens specification review only.

```yaml
proof:
  name: Canonical Spatial Topology Identity Proof
  version: 0.1.0-draft.0
  payload_schema_candidate: CanonicalSpatialTopologyIdentityPayload.v1
  simulation_identity_candidate: 0.7.0-draft.60

authority:
  specification_review: authorized
  implementation: prohibited
  unreal_source_changes: prohibited
  capacity_advancement: prohibited
  successor_scope: prohibited
```

The conceptual framing is non-authoritative developer material. This draft is
not a frozen canonical schema. Neither document can change city truth merely
by naming a place or drawing a connection.

## Exact proof boundary

```yaml
fixture:
  conceptual_endpoint_references: 2
  conceptual_relationship_references: 1
  canonical_sites: 2
  canonical_routes: 1
  route_endpoint_count: 2
  consequential_route_facts: 1
  canonical_access_mutations: 1
  fresh_unreal_materializations: 2

included:
  - explicit_conceptual_to_canonical_assignment
  - stable_canonical_site_identity
  - stable_canonical_route_identity
  - exact_route_endpoint_references
  - one_ordinary_route_access_gate
  - one_access_only_canonical_mutation
  - canonical_ancestry_and_replay
  - representation_identity_independence
  - representation_destruction_and_fresh_rematerialization

excluded:
  - travel_time
  - movement
  - traversal
  - pathfinding
  - navigation_authority
  - coordinates
  - distance
  - directionality_generalization
  - route_capacity_generalization
  - route_leases
  - dynamic_topology_creation_or_deletion
  - topology_repair
  - endpoint_mutation
  - adjacency_inference
  - transitive_spatial_queries
  - topology_search
  - physical_interaction_or_Q
  - geometry_authoring_authority
  - generalized_site_or_route_ontology
  - production_route_direction_law
  - city_graph_generalization
  - player_or_crew_split
  - multiple_concurrent_or_evidence_producing_physical_domains
  - world_partition
  - streaming
  - level_instances
  - networking
  - population
  - traffic
  - stochasticity
```

`Bridge` is a motivating conceptual geographic anchor and candidate topology
from the developer framing. The framing does not name or resolve its endpoints.
The exact proof relationship is therefore invented for the fixture, along with
two neutral design references, `proof_endpoint_reference_0001` and
`proof_endpoint_reference_0002`; neither is asserted to be an anchor or
production endpoint on the conceptual map. The fixture's opaque canonical
identities are `topology_site_0001`, `topology_site_0002`, and
`topology_route_0001`. It does not fix the final Bridge's endpoints, edge count,
direction, capacity, travel cost, physical shape, or streaming representation.

`site` is a fixture-local topology-node type. This proof does not replace the
existing canonical area concept, define area/site containment, or establish a
general production site ontology.

## Spatial authority law

> **Conceptual reference, canonical topology identity, and physical
> representation identity are distinct identity classes. Only an exact
> versioned canonical topology specification may establish authoritative site
> and route identity.**

```text
conceptual_endpoint_reference
    ≠ canonical_site_id

conceptual_relationship_reference
    ≠ canonical_route_id

canonical_site_id / canonical_route_id
    ≠ Unreal Actor name, label, path, GUID, or object identity
    ≠ navigation polygon, link, or path identity
    ≠ level, Level Instance, World Partition cell, or streaming identity
    ≠ render or collision component identity
```

The conceptual assignment explains how this proof's neutral design references
designate the canonical fixture; `Bridge` is motivation only. The assignment
does not become runtime authority. The canonical record contains its own
complete site identities, route identity, endpoint relation, and access fact.
Unreal receives those facts; it does not infer or create them.

## Candidate identity and schema boundary

Freeze review must decide the following exact candidate identity or supersede
it explicitly:

```yaml
record_schema: CanonicalResolutionEnvelope.v1
payload_schema: CanonicalSpatialTopologyIdentityPayload.v1
scenario_id: canonical-spatial-topology-identity-v1
scenario_version: 0.1.0
simulation_version: 0.7.0-draft.60
seed: canonical-spatial-topology-identity-v1/0001
```

All identity fields belong inside the canonical envelope and therefore inside
its canonical hash. A new authoritative topology field requires a new payload
schema and simulation identity.

The predecessor canonical-JSON law remains mandatory: sorted object keys,
compact separators, `ensure_ascii = true`, no non-finite numbers, declared
array order preserved, UTF-8 encoding, lowercase SHA-256, and one terminal LF
only in stored artifacts. Raw JSON ingestion must detect and reject duplicate
object-member names before constructing an in-memory object; an ordinary parser
whose last duplicate silently wins is non-conformant.

The candidate payload admits exactly:

```yaml
canonical_envelope:
  identity:
    record_schema: CanonicalResolutionEnvelope.v1
    payload_schema: CanonicalSpatialTopologyIdentityPayload.v1
    scenario_id: canonical-spatial-topology-identity-v1
    scenario_version: 0.1.0
    simulation_version: 0.7.0-draft.60
    seed: canonical-spatial-topology-identity-v1/0001

  current_causal_state:
    spatial_topology:
      sites:
        topology_site_0001: null
        topology_site_0002: null
      routes:
        topology_route_0001:
          endpoint_semantics: unordered_pair_fixture_only
          endpoint_site_ids:
            - topology_site_0001
            - topology_site_0002
          access_state: available | blocked
    fixture_processes:
      topology_access_closure_01:
        state: active | succeeded
        resources_owned: []

  future_causal_state:
    canonical_clock: t0/00 | t1/00
    unresolved_work:
      - work_id: t1/00/topology/block_topology_route_0001.resolve
        decision_time: t1/00
        simulation_phase: 10
        process_id: topology_access_closure_01
        target:
          kind: canonical_route
          route_id: topology_route_0001
          endpoint_site_ids:
            - topology_site_0001
            - topology_site_0002
        gates:
          - path: /current_causal_state/spatial_topology/routes/topology_route_0001/endpoint_site_ids
            required_value:
              - topology_site_0001
              - topology_site_0002
          - path: /current_causal_state/spatial_topology/routes/topology_route_0001/access_state
            required_value: available
        permitted_topology_mutation:
          op: replace
          path: /current_causal_state/spatial_topology/routes/topology_route_0001/access_state
          value: blocked
        terminal_state: succeeded
        terminal_resource_disposition: no_resources_owned

  causal_provenance:
    authoritative_causal_ledger: <exact frozen ledger>
    canonical_ancestry: <null or exact predecessor relation>
    fixture_genesis: <exact immutable genesis retained in R0 and R1>
```

R0 contains exactly the displayed work member, `canonical_clock = t0/00`,
`access_state = available`, and process `state = active`. R1 contains
`canonical_clock = t1/00`, `access_state = blocked`, process `state =
succeeded`, and `unresolved_work = []`. The array-shaped work definition above
is therefore an R0-only schema branch, not permission for additional work.

No conceptual label, Unreal identity, navigation identity, coordinate,
distance, capacity, travel, level, cell, or streaming field is admitted.

## Canonical topology invariants

The candidate schema must fail closed unless all of these are true:

1. `sites` contains exactly the two canonical object keys shown above, with
   null values and canonical JSON key ordering.
2. Each canonical site identity is unique and conforms to the frozen opaque-ID
   grammar.
3. `routes` contains exactly one object key with canonical ID
   `topology_route_0001`.
4. `endpoint_site_ids` contains exactly two distinct existing canonical site
   identities in canonical lexical order.
5. `endpoint_semantics` is exactly `unordered_pair_fixture_only`.
6. `access_state` is exactly `available` or `blocked`.
7. Endpoint identity and endpoint semantics are immutable after genesis in
   this proof.
8. The only authorized topology mutation is
   `topology_route_0001.access_state: available → blocked`.

`CanonicalSiteId.v1` admits exactly `topology_site_0001` and
`topology_site_0002`. `CanonicalRouteId.v1` admits exactly
`topology_route_0001`. These value spaces are type-disjoint and exhaustive for
the fixture. No resolver, gate, serializer, or adapter may parse a route ID to
infer either endpoint or parse any site/route token to recover conceptual
meaning.

Lexical endpoint ordering is serialization law, not travel direction and not a
pathfinding rule. `unordered_pair_fixture_only` is a proof-local endpoint
semantic, not a production directionality decision. This proof does not
generalize directed edges, parallel routes, hyperedges, or route networks.

## Explicit conceptual assignment

The proof uses one detached design-time assignment artifact. Stable proof
reference IDs and mutable human display labels are separate fields:

```yaml
assignment_schema: ConceptualToCanonicalTopologyAssignment.v1
assignment_id: canonical-spatial-topology-identity-fixture-0001
conceptual_references:
  endpoints:
    - reference_id: proof_endpoint_reference_0001
      display_label: Proof Endpoint One
      canonical_target_id: topology_site_0001
    - reference_id: proof_endpoint_reference_0002
      display_label: Proof Endpoint Two
      canonical_target_id: topology_site_0002
  relationships:
    - reference_id: proof_relationship_reference_0001
      display_label: Conceptual Crossing Fixture
      canonical_target_id: topology_route_0001
      endpoint_reference_ids:
        - proof_endpoint_reference_0001
        - proof_endpoint_reference_0002
```

This artifact is inspectable specification provenance, not canonical runtime
state. R0 is frozen fixture genesis; it is never imported, generated, repaired,
or mutated from this artifact at runtime. The artifact may designate the
already reviewed canonical definition; it may not write a record, answer a
route gate, or supply a canonical ID after R0 exists.

Canonical `fixture_genesis` must not contain the assignment bytes, assignment
digest, conceptual reference IDs, or display labels. Detached evidence may hash
and compare both declared assignment projections, but those evidence hashes do
not participate in H0. Otherwise a label rename would silently change canonical
identity and the neutrality witness would be invalid.

The proof must include a label-neutrality witness:

```text
conceptual references:
  Proof Endpoint One / Proof Endpoint Two / Conceptual Crossing Fixture

same stable proof reference IDs, renamed display labels:
  West Reference / East Reference / Crossing Reference

same explicit canonical assignment target
        ↓
byte-identical canonical R0
```

This is deliberately not a generalized topology importer. The candidate
implementation, if later authorized, compares two detached display-label
projections to the already frozen R0. The assignment has no canonical write
path.

## Canonical route-access gate

One pure ordinary query demonstrates that the canonical route fact is causal:

```text
evaluate_route_access(
  record,
  requested_route_id,
  requested_endpoint_site_ids
)
```

Candidate result:

```yaml
source_record_hash: canonical_hash(record)
evaluation_status: evaluated
requested_route_id: topology_route_0001
requested_endpoint_site_ids: [topology_site_0001, topology_site_0002]
evaluated_gates:
  - gate: route_exists
    result: true
  - gate: requested_endpoint_pair_is_canonical
    result: true
  - gate: requested_endpoint_pair_matches_stored_route
    observed_value: [topology_site_0001, topology_site_0002]
    result: true
  - gate: route_access_state
    observed_value: available | blocked
    required_value: available
    result: true | false
eligible: true | false
```

Invalid request shape:

```yaml
source_record_hash: canonical_hash(record)
evaluation_status: invalid_request
reason: <exact frozen validation reason>
eligible: null
access_state_evaluated: false
```

The query must resolve `requested_route_id` only against the canonical route
table and must compare the exact canonical ordered endpoint pair stored in the
record. It may not accept a conceptual label, Actor identity, navigation link,
level path, cell ID, mesh name, or adapter role as a substitute. Request syntax
and canonical identity validate before eligibility. A wrong, redirected,
reversed, missing, additional, or representation-derived endpoint pair returns
`invalid_request` with `eligible = null`; it does not imply blocked or
directional access. Only the exact canonical ordered pair may reach the stored
endpoint and access-state gates.

```text
R0.topology_route_0001.access_state = available
→ eligible = true

R1.topology_route_0001.access_state = blocked
→ eligible = false
```

The query result is a detached, non-authoritative deterministic evaluation
witness. It cannot be replayed as a boundary, capability, or mutation proposal.
The query does not authorize movement, reserve capacity, acquire a lease, or
create a traversal commitment.

## One canonical mutation

The proposed canonical fixture contains the complete ordinary scheduled proof
process definition inside authoritative R0. Boundary discovery returns exactly:

```yaml
boundary_schema: CanonicalSpatialTopologyBoundary.v1
source_record_hash: H0
decision_time: t1/00
simulation_phase: 10
due_work_ids:
  - t1/00/topology/block_topology_route_0001.resolve
```

The boundary owns no hidden target or command; the complete target, gate,
permitted topology mutation, terminal process state, and resource disposition
come from the R0 work definition shown above. The process is neutral proof
vocabulary, not a production road, damage, bridge, agent, or planner system.

“One access-only canonical mutation” means exactly one topology-fact mutation.
The same atomic transaction necessarily advances the canonical clock, consumes
the due-work member, terminalizes the fixture process with
`no_resources_owned`, appends provenance, and establishes successor ancestry.
Those lifecycle changes may not be hidden or omitted, and no other spatial fact
may change.

The intended canonical chain is:

```text
R0 / H0
  sites = topology_site_0001, topology_site_0002
  topology_route_0001 endpoints =
    [topology_site_0001, topology_site_0002]
  topology_route_0001 access = available
  close work due at t1/00
        ↓
discover one H0-bound boundary
        ↓
resolve through the declared canonical path
        ↓
R1 / H1
  parent = H0
  sites byte-identical
  route identity + endpoints byte-identical
  fixture genesis byte-identical
  topology_route_0001 access = blocked
  closure process = succeeded / no resources owned
  no future work
```

The complete R0 is the transaction pre-state. Successor identity `H1` is
computed externally only after complete R1 construction. No canonical ledger
entry may contain its own record's hash.

The authoritative ledger must record the H0-bound boundary, the exact route
identity and endpoint observation, the `available` gate result, the access-only
mutation, and the canonical pre-state hash. It must not record conceptual or
representation identity as causal input.

## Representation mapping boundary

Unreal receives a detached, non-authoritative mapping whose only function is
to project canonical identities into one proof surface:

```yaml
mapping_schema: CanonicalTopologyMaterializationMap.v1
mapping_id: topology_materialization_R0_0001 | topology_materialization_R1_0001
source_canonical_hash: H0 | H1
sites:
  topology_site_0001: representation_site_slot_01
  topology_site_0002: representation_site_slot_02
routes:
  topology_route_0001: representation_route_slot_01
```

The mapping must use canonical IDs as keys. It cannot add, delete, rename,
redirect, or synthesize canonical topology. Representation roles, Actor names,
object paths, instance GUIDs, transforms, meshes, materials, collision, and
process IDs remain non-authoritative.

The mapping deliberately contains no endpoint relation. The adapter must read
`endpoint_site_ids` exclusively from the canonical record and then resolve the
named canonical sites through the detached site-slot map. The route slot cannot
become a competing topology source.

Fixed local transforms may be used only to make the proof visible and
inspectable. Collision, traversal, and walkability are not proof oracles. Local
placement establishes no canonical coordinates, distance, direction, travel
cost, or navigation relation.

### Exact proof-input classes

Each UE process receives one isolated proof-input root containing exactly:

```text
canonical_payload.json
materialization_map.json
launch_receipt.json
```

It receives no truth-bearing process context. Before launch, the harness must
inventory the visible root, reject an additional or missing file, and record
the exact filename/raw-SHA-256 set.

The R0 and R1 proof roots must be physically disjoint. Before UE #2 launches,
the harness must prove that UE #1's root, process state, output, caches, saves,
session data, and command-line truth are inaccessible to it.

The detached launch receipt must bind both artifacts before either is parsed:

```yaml
receipt_schema: CanonicalTopologyLaunchReceipt.v1
canonical_payload_raw_sha256: <exact stored R0 or R1 byte hash>
materialization_map_raw_sha256: <exact stored map byte hash>
expected_canonical_hash: H0 | H1
expected_record_schema: CanonicalResolutionEnvelope.v1
expected_payload_schema: CanonicalSpatialTopologyIdentityPayload.v1
expected_scenario_id: canonical-spatial-topology-identity-v1
expected_simulation_version: 0.7.0-draft.60
expected_mapping_schema: CanonicalTopologyMaterializationMap.v1
expected_mapping_id: <exact R0 or R1 map identity>
```

UE independently verifies both raw hashes before parsing. It then parses both
artifacts, validates every expected schema/scenario/mapping identity, computes
the canonical payload hash, and requires:

```text
computed_canonical_hash(payload)
    = launch_receipt.expected_canonical_hash
    = materialization_map.source_canonical_hash
```

Only after those checks may materialization begin. A mismatch at any stage
refuses materialization and emits only a detached diagnostic failure.

The detached materialization receipt must bind:

```yaml
receipt_schema: CanonicalTopologyMaterializationReceipt.v1
accepted_canonical_payload_raw_sha256: <verified input hash>
accepted_canonical_hash: H0 | H1
accepted_materialization_map_raw_sha256: <verified map hash>
accepted_mapping_id: <verified map identity>
materialized_canonical_site_ids:
  - topology_site_0001
  - topology_site_0002
materialized_canonical_route_id: topology_route_0001
materialized_endpoint_site_ids:
  - topology_site_0001
  - topology_site_0002
materialized_access_state: available | blocked
operational_process_instance_id: <non-authoritative>
operational_actor_instance_ids: <non-authoritative exact set>
```

The endpoint receipt field is an observation of the accepted canonical record,
not a second endpoint source.

## Fresh Unreal lifecycle witnesses

If implementation is later authorized, the proof must use real fresh UE 5.8
processes and detached raw-byte receipts.

### Open-state source witness

```text
fresh UE process #1
  receives exact stored R0 + detached receipt + R0 mapping
        ↓
  verifies raw bytes and canonical identity before materialization
        ↓
  materializes exactly:
    topology_site_0001
    topology_site_0002
    topology_route_0001 connecting those canonical endpoints
    access = available
        ↓
  emits detached materialization receipt
        ↓
  process is terminated
```

The acceptance receipt must bind the accepted canonical hash, canonical site
IDs, canonical route ID, endpoint relation, access fact, and operational
process/Actor instance observations without converting those operational
identities into authority.

### Canonical-only transition

```text
UE process #1 terminated
        ↓
canonical resolver consumes the H0-bound close boundary
        ↓
R1 commits independently of Unreal
```

The physical representation is not required to remain loaded for topology or
access authority to persist.

### Closed-state return witness

```text
fresh isolated UE process #2
  receives exact stored R1 + detached receipt + R1 mapping only
        ↓
  cannot see R0, process #1, its Actors, caches, saves, or session state
        ↓
  materializes exactly:
    topology_site_0001
    topology_site_0002
    topology_route_0001 connecting those same canonical endpoints
    access = blocked
        ↓
  emits detached materialization receipt
```

The second process must reconstruct the canonical endpoint relation from R1
through the sealed non-authoritative adapter rather than reuse Actor, level,
navigation, or process-local identity from the first process. The record owns
the relation; the adapter owns only its local physical placement.

The R0 and R1 receipts must record distinct process-local Actor instance
identities while binding the same canonical site IDs, route ID, and endpoint
pair. This does not authorize arbitrary art replacement or production
streaming. It tests only that representation destruction/recreation does not
replace canonical topology identity.

## Required witness matrix

```yaml
A_exact_topology:
  proves:
    - exact canonical site and route identities
    - exact endpoint integrity
    - deterministic serialization and hash

B_conceptual_label_neutrality:
  proves:
    - renamed conceptual display labels produce byte-identical canonical R0
    - conceptual labels are absent from runtime authority

C_available_access:
  source: R0
  expected: topology_route_0001 eligible

D_access_mutation:
  source: R0
  expected:
    - one atomic R1
    - endpoint relation unchanged
    - access_state blocked
    - complete provenance

E_blocked_access:
  source: R1
  expected: topology_route_0001 ineligible

F_available_materialization:
  source: R0_only
  process: fresh_UE_1

G_representation_destruction:
  expected: no topology authority lost or transferred

H_blocked_rematerialization:
  source: R1_only
  process: fresh_UE_2
  expected:
    - same canonical site IDs, route ID, and endpoint pair as fresh_UE_1
    - distinct process-local Actor instance identities
```

Within each canonical execution, replay must be byte-identical. Detached
representation receipts may differ only in declared operational fields; no
operational identity may enter R0, R1, their hashes, or canonical provenance.

## Fail-closed adversarial surface

Freeze review must retain at least these failures:

1. duplicate canonical site identity;
2. duplicate raw JSON object-member name before object construction;
3. cross-type site/route identity substitution;
4. route endpoint missing from the canonical site table;
5. identical route endpoints;
6. non-canonical endpoint ordering;
7. requested endpoint pair that does not exactly match the stored route being
   classified as ordinary ineligibility instead of `invalid_request`;
8. extra route, site, topology field, or access value;
9. conceptual label supplied where a canonical site/route ID is required;
10. Unreal Actor name, path, GUID, navigation ID, level identity, cell identity,
   or streaming identity supplied as canonical identity;
11. access query redirected through a representation mapping;
12. access-only mutation attempting to change a site ID, route ID, endpoint, or
    endpoint semantics;
13. boundary bound to a record other than the current canonical source;
14. materialization mapping with missing, additional, duplicate, or redirected
    canonical keys;
15. map bytes, schema, identity, or source hash disagreeing with the detached
    launch receipt;
16. materializer attempting to create canonical topology absent from the
    record;
17. Unreal or adapter attempting to write canonical access state, ledger,
    ancestry, schedule, or successor identity;
18. adapter exposing a physical-evidence/Q proposal path;
19. fresh return process receiving R0, prior Actor/session/cache state, or a
    branch selector in addition to R1;
20. representation destruction treated as deletion of canonical topology; and
21. any in-record successor self-hash.

Each malformed canonical candidate rejects before mutation. Each invalid
materialization candidate refuses materialization and produces detached
diagnostic failure only. This adapter has no evidence/Q proposal path at all.
No rejected representation attempt becomes canonical history.

## Source audit

The proof cannot pass on output coincidence alone. A mechanical source audit
must establish:

```text
conceptual label / reference
    X cannot dataflow into canonical runtime identity lookup

Unreal / navigation / level / streaming identity
    X cannot dataflow into canonical topology, gate, mutation, ledger,
      ancestry, schedule, or hash construction

canonical access mutation
    X cannot change route identity, endpoints, or endpoint semantics

materialization adapter
    may read canonical topology
    may derive representation-local state
    may not manufacture or mutate canonical topology
```

The canonical topology validator, route-access gate, canonical mutation path,
serializer/hash, and representation adapter must remain separately
inspectable.

## Freeze gates

Before `v0.1.0` may freeze, review must fix:

1. the exact canonical identity and payload schema;
2. the exact opaque canonical-ID grammar and array-order law;
3. the exact R0 and R1 record shapes;
4. the exact genesis and conceptual-assignment provenance boundary;
5. the exact scheduled close-work and record-bound boundary schemas;
6. the exact route-access query and ledger schemas;
7. the exact detached launch, mapping, and materialization-receipt schemas;
8. the exact fresh-process isolation contract;
9. the complete witness and rejection matrix; and
10. the source-audit patterns and deterministic replay oracle.

Until those gates pass, no simulator or Unreal implementation may begin.

## Candidate implementation DAG — closed

The following DAG is a review target, not implementation authority:

```text
freeze reviewed v0.1.0 specification
        ↓
exact canonical validator / serializer / hash
        ↓
exact R0 + conceptual-label-neutrality witness
        ↓
ordinary access gate + one canonical access mutation
        ↓
fresh UE R0 materialization
        ↓
destroy representation
        ↓
fresh isolated UE R1 materialization
        ↓
replay / source audit / rejection suite
        ↓
evidence + self-excluding release manifest
```

No node may execute before explicit freeze and implementation authorization.

## Draft changelog

### 0.1.0-draft.0 — 2026-08-27

- Opened the first explicit representation-independent topology-identity and
  endpoint-referential-integrity proof for specification review only.
- Proposed two opaque canonical site IDs, one opaque route ID, one explicit
  fixture-only unordered endpoint pair, and one consequential access fact.
- Separated stable proof reference IDs from mutable conceptual display labels
  and kept the assignment artifact outside runtime authority.
- Proposed one complete scheduled access-only fixture process, an endpoint-aware
  non-authoritative eligibility witness, and fresh read-only UE materialization
  before and after representation destruction.
- Authorized no implementation, capacity advancement, production Bridge
  endpoints, movement, travel, pathfinding, World Partition, streaming,
  networking, generalized city graph, or adjacent scope.

## Acceptance claim

If the frozen implementation later passes, it may establish only:

> **One explicitly specified proof-local two-site/one-route topology owns
> stable canonical identity and one consequential access fact independently of
> conceptual labels and physical representation identity. Its exact endpoint
> relation survives canonical mutation, destruction of its representation, and
> fresh Unreal rematerialization from the canonical record through a
> non-authoritative adapter.**

It may not establish travel, movement, pathfinding, distance, capacity,
streaming, World Partition, a generalized city graph, split players,
networking, population, or production spatial architecture.
