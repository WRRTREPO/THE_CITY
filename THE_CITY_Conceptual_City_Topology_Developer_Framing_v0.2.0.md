# THE_CITY --- Conceptual City Topology and Developer Framing

**Version:** 0.2.0\
**Status:** Developer framing for the current city image.\
**Supersedes:** v0.1.0.\
**Scope:** Conceptual spatial interpretation only. This document
establishes no production topology, canonical site schema, mission
structure, exact dimensions, streaming architecture, or new simulation
law.

## Purpose

The current city image establishes the first conceptual spatial frame
for THE_CITY.

It should be read as **conceptual spatial topology and causal
geography**: a bounded city containing named spatial anchors,
approximate relative placement, geographic features, and a crew origin
from which future causal relationships may be specified.

It must **not** be read as an authored mission map, a production graph,
or an implementation schema.

> **The drawing defines conceptual spatial topology and causal
> geography, not authored mission layout or prematurely fixed
> connectivity.**

## Authority classification

This document separates what the image actually establishes from design
intent and from work that remains unauthorized.

### Image authority

The image establishes:

-   named conceptual spatial anchors;
-   approximate relative placement of those anchors;
-   approximate geographic features and city boundary;
-   the Hub's conceptual location;
-   ocean/coastal space along the northern edge; and
-   the presence of a lake and ruin area as conceptual geographic
    features.

### Design intent

The intended use of this geography is:

-   geography should create causal pressure;
-   locations should not imply missions;
-   distance should be capable of producing deployment latency and
    opportunity cost;
-   meaningful connectivity may later become canonical causal topology;
-   geographic features may later become physical or causal constraints
    where explicitly specified; and
-   the city should remain coherent independently of authored mission
    content.

Design intent is not implementation authority.

### Not yet authorized

This image and framing do not authorize:

-   canonical site identities for every named anchor;
-   a production route or road ontology;
-   an exact canonical graph;
-   topology schema;
-   exact dimensions or travel costs;
-   district or simulation-area boundaries;
-   World Partition mapping;
-   streaming-cell mapping;
-   generalized city-scale promotion/demotion;
-   generalized city-scale Causal-LOD;
-   production population, traffic, economy, or content systems; or
-   mission, encounter, spawn, or scripted-event placement.

## Named conceptual spatial anchors

The drawing currently contains these named anchors:

-   **Power Plant** --- north-west waterfront.
-   **Block A** --- north / central-east.
-   **Block B** --- west-central.
-   **Bank** --- east side.
-   **Bridge** --- west-central / south of Block B.
-   **Park** --- central-east.
-   **Storage** --- south-west.
-   **Hub** --- south-central.
-   **Lake** --- south-central / east.
-   **Jail** --- southern edge.
-   **Ruin** --- south-east.

These names identify conceptual geography in the drawing.

They do not, by themselves, establish canonical entity identity,
persistence schema, state ownership, exact boundaries, simulation
fidelity, or production implementation.

## Governing spatial frame

Developers should read the image through four conceptual layers:

``` text
CITY SPACE
    │
    ├── named conceptual anchors
    │     Power Plant / Bank / Jail / Storage / ...
    │
    ├── candidate traversal structure
    │     streets / bridge / passages / connections
    │
    ├── geographic features and candidate constraints
    │     ocean / lake / ruin / coastline
    │
    └── crew origin
          Hub
```

These layers give the causal city machine geography to operate through.

They are not mission definitions and are not yet a production topology.

## Conceptual anchors are not missions

A named location must not be interpreted as a prescribed gameplay event.

For example:

``` text
BANK
```

does not mean:

``` text
BANK ROBBERY MISSION
```

The Bank is currently only a named conceptual spatial anchor.

If it later receives canonical identity, its gameplay meaning should
derive from canonical state, agents, processes, commitments, player
consequences, and materialization---not from the existence of the label
itself.

Non-normative examples of possible future conditions could include
occupation, damage, access change, public-service presence, or contest.
These examples are explanatory only. They do **not** define a Bank
schema or authorize those state fields.

The same rule applies to every other named anchor.

The simulation should determine what is happening at a place.

The map should not prescribe it.

## Geography and causal pressure

The corpus establishes that deployment and route conditions can create
opportunity cost in bounded proofs. The conceptual map gives future
production geography in which that principle may operate.

The intended relationship is:

``` text
distance
+ meaningful topology
+ route condition
+ deployment origin
+ current canonical state
─────────────────────────
→ potential decision latency
```

This is a design relationship, not yet a calibrated production formula.

Exact travel times, route costs, aircraft behavior, and city-scale
timing remain unspecified.

The important constraint is that geography may participate in causality
without becoming a mission selector.

## Physical network versus canonical causal graph

Do not equate visible roads or physical adjacency with canonical
simulation topology.

``` text
PHYSICAL ROAD / STREET NETWORK
              ≠
CANONICAL CAUSAL GRAPH
```

A production city may contain thousands of physical streets, passages,
doors, paths, or navigation connections without requiring every one of
them to exist as an authoritative canonical edge.

A connection requires canonical representation only when its state is
explicitly determined to matter to consequential city resolution---for
example, where access, capacity, travel, resource flow, or another
causal eligibility condition depends on it.

The existing proof corpus establishes route gates, capacities, leases,
and traversal semantics only inside its bounded fixtures. Those proofs
do not automatically generalize every production road into a canonical
route object.

## The Bridge

The Bridge shown in the image is a conceptual geographic anchor and an
obvious candidate for consequential topology.

That does not yet establish:

-   its exact endpoints;
-   whether it is one canonical edge or several;
-   its travel cost;
-   its capacity;
-   its failure states;
-   its relationship to aircraft or pedestrian traversal;
-   whether surrounding roads are canonical;
-   or whether its visual geometry maps directly to any canonical
    identity.

Those decisions require an explicit topology specification.

## The Hub

The Hub is shown away from the apparent geometric center of the
conceptual city.

If that relationship is retained, it can naturally produce asymmetric
deployment latency and opportunity cost.

The corpus already establishes the bounded principle that a shared crew
can spend its physical opportunity in one domain while unattended city
causality continues elsewhere. The image provides a conceptual geography
in which that pressure may eventually be expressed at larger scale.

The Hub should therefore be understood as the conceptual crew origin,
not as a mission-selection abstraction.

Future implementation should make questions such as these legible where
the underlying systems actually support them:

``` text
Where is the situation?
How far away is it?
What meaningful routes are available?
How long will deployment consume?
What may happen elsewhere during that commitment?
What are we choosing not to answer?
```

The image does not yet supply the numerical answers.

## Geographic features

The ocean, lake, coastline, ruin, and similar large features are
conceptually present.

Their simulation meaning remains unresolved.

``` text
KNOWN FROM IMAGE
    feature exists conceptually
    approximate relationship to other anchors

UNKNOWN UNTIL SPECIFIED
    whether it constrains traversal
    how it constrains traversal
    whether the constraint is canonical
    whether aircraft are affected
    whether canonical routes cross it
    whether it changes materialization or simulation fidelity
```

Do not promote visual geography into causal law without an explicit
contract.

## Identity separation invariant

Canonical spatial identity must never be inferred from Unreal
representation.

``` text
conceptual geographic feature
        ↓ explicit specification / mapping
canonical spatial identity
        ↓ materialization adapter
Unreal representation
```

The following identities are **not implicitly equivalent**:

``` text
conceptual map identity
canonical area/site/route identity
Unreal Actor identity
Level Instance identity
World Partition cell identity
streaming identity
navigation identity
render identity
```

They may later be related through explicit adapters or mapping
contracts.

None may silently define another.

This protects the existing authority boundary: the canonical city owns
strategic truth; Unreal materializes and evidences local physical
consequence.

## Relationship to the canonical city

The existing THE_CITY law remains unchanged:

> **The city holds facts; the crew's presence renders those facts into
> detail.**

The conceptual map provides candidate places, separation, and
relationships through which those facts may eventually operate.

Where explicit canonical topology has been defined, the relationship is:

``` text
canonical city state
        ↓
explicit canonical spatial identity/topology
        ↓
materialization mapping
        ↓
local Unreal representation
        ↓
playable physical situation
```

Arrival does not create or reroll canonical history.

Materialization expresses the current authoritative situation at the
relevant geography.

## Causal-LOD boundary

Do **not** interpret this drawing or this document as evidence that
production city-scale Causal-LOD has been proven.

The current corpus proves Causal-LOD Equivalence only inside its sealed
neutral fixture: different non-authoritative execution granularities
converge on the same canonical result under that proof's exact
conditions.

It does not yet prove generalized equivalence for:

-   external inputs during skipped intervals;
-   multiple independently scheduled active commitments;
-   stochastic draws;
-   actual FPS/materialization fidelity changes;
-   repeated city-scale promotion and demotion;
-   production streaming;
-   population-scale simulation; or
-   long-horizon city execution.

The map provides no additional authority in those areas.

## What developers must not infer

The current image does **not** establish:

-   exact city dimensions;
-   exact block dimensions;
-   exact road geometry;
-   exact graph connectivity;
-   exact travel times;
-   exact aircraft flight paths;
-   canonical identity for every label;
-   canonical identity for every street;
-   district ownership;
-   simulation-area boundaries;
-   streaming-cell boundaries;
-   World Partition configuration;
-   population density;
-   traffic topology;
-   interiors;
-   encounter locations;
-   spawn locations;
-   mission locations;
-   scripted events;
-   traversal permissions;
-   which unlabeled regions contain gameplay;
-   whether visual adjacency implies graph adjacency;
-   whether the apparent macro-grid is a production grid; or
-   whether any visual object maps one-to-one to a canonical object.

Do not manufacture precision from the sketch.

## Developer rule

Preserve this distinction:

``` text
IMAGE PROVIDES
    conceptual geography
    named spatial anchors
    approximate relative placement
    geographic features
    conceptual crew origin
    candidate traversal relationships

DESIGN INTENT PROVIDES
    geography should create causal pressure
    locations should remain independent of missions
    meaningful distance should matter
    consequential connectivity may become canonical topology

IMAGE DOES NOT PROVIDE
    canonical site schema
    exact graph edges
    production route ontology
    missions
    encounters
    scripted front progression
    production streaming topology
    exact metrics
    generalized Causal-LOD
    unstated simulation rules
```

When exact connectivity, dimensions, travel costs, graph edges,
canonical identities, districts, or streaming boundaries become
necessary, they require their own explicit specification and proof
boundary.

## Architectural consequence

The image is useful because it gives the causal machine **somewhere to
happen** without deciding **what must happen there**.

The intended machine remains:

``` text
conceptual geography
        ↓
explicit canonical topology where causally required
        +
canonical state
        +
agents / processes / commitments
        +
shared consequential constraints
        +
crew intervention
        ↓
persistent causal history
        ↓
local physical materialization
```

Not:

``` text
map label
        ↓
authored mission
        ↓
scripted outcome
```

And not:

``` text
visible road
        ↓
automatic canonical edge
```

And not:

``` text
Unreal object / World Partition cell
        ↓
automatic canonical identity
```

## Acceptance gate

This framing is preserved only if a developer **cannot** use this
document as authority to:

1.  create production canonical nodes merely because an image label
    exists;
2.  turn every visible road or adjacency into a canonical edge;
3.  bind canonical identity to Unreal Actor, Level Instance, World
    Partition, navigation, rendering, or streaming identity;
4.  infer exact connectivity, dimensions, travel costs, or topology;
5.  infer production state schemas from explanatory examples;
6.  claim generalized or city-scale Causal-LOD;
7.  create mission or encounter triggers from named geography; or
8.  infer simulation behavior from visual features without an explicit
    causal contract.

The framing succeeds when developers can instead use the image for
exactly this:

> **The geography provides places, separation, and potential
> constraints. Canonical causality determines what those places mean
> over time.**

## Changelog

### 0.2.0 --- 2026-08-26

-   Separated image authority, design intent, and unauthorized
    implementation scope.
-   Replaced premature `persistent sites` language with
    `named conceptual spatial anchors`.
-   Distinguished physical road/street networks from the canonical
    causal graph.
-   Added the canonical/Unreal/World Partition identity-separation
    invariant.
-   Recast the Hub's off-center placement as an observed relationship
    whose causal use depends on retention and later specification.
-   Marked location-state examples as non-normative rather than implied
    production schemas.
-   Reclassified ocean, lake, ruin, and similar features as conceptual
    geography with unresolved causal semantics.
-   Added an explicit prohibition on treating the image as evidence for
    generalized city-scale Causal-LOD.
-   Strengthened the acceptance gate against accidental
    production-topology, mission-map, and representation-authority
    inference.
