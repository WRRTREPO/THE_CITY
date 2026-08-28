# Simultaneous Physical Domains Proof

**Version:** 0.1.0-draft.1
**Status:** Freeze review; not frozen; implementation prohibited
**Selected:** 2026-08-28
**Advanced to freeze review:** 2026-08-28
**Parent continuation:** [Co-op Open-City FPS Simulation — v0.7 Working Continuation](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)
**Latest sealed predecessor:** [Canonical Occupancy Transition Proof — v0.1.0](Canonical%20Occupancy%20Transition%20Proof%20Evidence%20-%20v0.1.0.md)
**Canonical source payload:** `CanonicalSpatialTopologyIdentityPayload.v1` / `0.7.0-draft.61`, reused byte-for-byte
**Candidate proof-harness identity:** `SimultaneousPhysicalDomainsProof.v1` / `0.7.0-draft.69` — not frozen

## Question

> **Can two process-isolated Unreal representation domains remain
> simultaneously alive against one canonical head, survive an independently
> committed canonical H0→H1 transition without participating in that
> transaction, and independently rebind to H1 while any domain still
> representing H0 is mechanically classified as stale and incapable of
> current-head canonical authority?**

The bounded primary chain is:

```text
exact sealed Phase-1 R0 / H0
        ↓
launch isolated Unreal domain A
  site projection: topology_site_0001
  route projection: topology_route_0001 / available
        ↓
launch isolated Unreal domain B
  site projection: topology_site_0002
  route projection: topology_route_0001 / available
        ↓
A and B simultaneously alive and synchronized to H0
        ↓
canonical machine independently resolves the sealed H0-bound boundary
        ↓
exact sealed Phase-1 R1 / H1
  topology_route_0001.access_state: available → blocked
        ↓
A and B remain alive and head_unconfirmed until detached observation proves H1
        ↓
exact H1 observation publishes and independently reverifies
        ↓
A and B are mechanically stale against current head H1
        ↓
independent receipt-verified refreshes in either A/B order
        ↓
A and B remain alive and synchronized to H1
```

This proof does not introduce new canonical state, a new canonical payload, a
new canonical mutation, or another canonical resolver. It composes the exact
sealed Phase-1 H0/H1 transition with a new physical-lifecycle question.

## Selection and authority state

```yaml
selection:
  phase: 3
  proof: Simultaneous Physical Domains Proof
  version: 0.1.0-draft.1
  status: freeze_review
  implementation_authority: none
  unreal_source_change_authority: none
  capacity_advancement: none
  freeze_status: not_frozen
```

Opening this draft selects one risk for review. It does not authorize Python,
Unreal, adapter, harness, test, evidence, artifact, release-manifest, README
capacity, or production-architecture implementation.

## Governing predecessor boundary

### Exercised predecessor evidence

The candidate directly composes these exact sealed records:

1. [Canonical Spatial Topology Identity Proof — v0.1.0](Canonical%20Spatial%20Topology%20Identity%20Proof%20Evidence%20-%20v0.1.0.md), for the exact two-site/one-route R0/H0 and R1/H1 payloads, the one access-only canonical mutation, detached mapping identity, raw-byte and canonical-hash verification, and representation/canonical identity separation.
2. [Integrated Unreal Promotion-Unload-Repromotion Proof — v0.1.0](Integrated%20Unreal%20Promotion-Unload-Repromotion%20Proof%20Evidence%20-%20v0.1.0.md), only for receipt-verified Unreal materialization, process-root isolation, and canonical/operational identity separation.
3. [Record-Relative Chronological Resolution Proof — v0.1.0](Record-Relative%20Chronological%20Resolution%20Proof%20Evidence%20-%20v0.1.0.md), for current-record-bound boundary authority and post-commit invalidation.
4. [Resolution Semantics Law — v0.1.1](Resolution%20Semantics%20Law%20-%20v0.1.1.md), for canonical-envelope ownership, hash boundaries, and disposable representation state.

### Preserved but not exercised

These sealed records constrain the proof without adding their fixture behavior:

1. [Canonical Occupancy Transition Proof — v0.1.0](Canonical%20Occupancy%20Transition%20Proof%20Evidence%20-%20v0.1.0.md). A domain scope is not subject occupancy, `in_transition`, route occupancy, arrival, or another canonical location field. No occupancy is materialized.
2. [Concurrent External Evidence Arbitration Proof — v0.1.0](Concurrent%20External%20Evidence%20Arbitration%20Proof%20Evidence%20-%20v0.1.0.md). Physical-domain identity, process order, filesystem order, and presentation order remain non-authoritative. QA, QB, BEXT, admission, and arbitration are not exercised.

### Phase-1 physical lifecycle is not inherited

Phase 1 established this physical lifecycle:

```text
materialize R0 in source process
→ destroy source representation
→ commit H0-to-H1 canonical transition
→ materialize R1 in fresh isolated return process
```

Phase 3 deliberately does not inherit that lifecycle. Its novelty requires:

```text
materialize R0 in process A
materialize R0 in process B
→ prove A and B alive concurrently
→ commit H0-to-H1 while neither process participates
→ prove the same A and B process instances remain alive
→ independently rebind those live instances to R1
```

Destroying or replacing either source process before H1, or satisfying the
primary witness with fresh return processes, fails this proof.

## Exact scope

```yaml
proof_scope:
  canonical_payload_schemas: 1 existing exact schema
  new_canonical_fields: 0
  canonical_records: 2 exact sealed artifacts
  canonical_mutations: 1 exact sealed access-only transition
  canonical_sites: 2
  canonical_routes: 1
  physical_domains: 2
  unreal_processes: 2 simultaneously alive
  detached_domain_projections: 4
  primary_refresh_orders: 2
  asymmetric_refresh_failures: 2 symmetric branches
  current_head_observation_failures: 1 exact injected branch
  stale_local_state_perturbation_pairs: 1 exact pair
  uninterrupted_liveness_intervals: 2 domains across 1 canonical commit
  external_inputs: none
  occupancy_materializations: none
  authoritative_random_draws: none
  implementation_authority: none
```

`physical_domain` means one proof-local Unreal process, one disjoint process
root, one operational process identity, one exact detached projection role,
and one local head-state machine. It is not a player, crew, host, peer,
streaming cell, level instance, network node, canonical subject, or canonical
site.

## Exact canonical source and mutation boundary

The proof must reuse these exact sealed artifacts without modification:

```yaml
canonical_R0:
  path: proof_kernel/CanonicalSpatialTopologyIdentityProofRecords/canonical_topology_R0.json
  raw_sha256: 5e57c04875cfaead69f4cd6aaffeee2f788a2c1f5a820a56fb7083f8f7e861ed
  payload_schema: CanonicalSpatialTopologyIdentityPayload.v1
  simulation_version: 0.7.0-draft.61

canonical_R1:
  path: proof_kernel/CanonicalSpatialTopologyIdentityProofRecords/canonical_topology_R1.json
  raw_sha256: 7ac7ece5c142ac4dee83abc6e83f7845d85dfc7f055ca6d678b7f04bdf1d795a
  payload_schema: CanonicalSpatialTopologyIdentityPayload.v1
  simulation_version: 0.7.0-draft.61
```

`H0` and `H1` retain their Phase-1 meaning: canonical-envelope hashes of the
complete exact R0 and R1 roots. `D0` and `D1` mean the displayed SHA-256 values
of the exact stored R0 and R1 bytes, including the required terminal LF. Raw
digests and canonical hashes are distinct and must not be substituted.

The canonical transition is exactly the sealed Phase-1 boundary and resolver:

```yaml
source_record: R0
source_record_hash: H0
work_id: t1/00/topology/block_topology_route_0001.resolve
decision_time: t1/00
simulation_phase: 10
canonical_mutation:
  op: replace
  path: /current_causal_state/spatial_topology/routes/topology_route_0001/access_state
  prior_value: available
  value: blocked
successor_record: R1
successor_record_hash: H1
```

The implementation proof, if later authorized, must reproduce R1 byte-for-byte
through the existing canonical resolver while both physical domains remain
alive. Neither domain process, projection, local state, refresh state, Actor,
receipt, timing, ordering, or diagnostic may enter boundary discovery, gate
evaluation, mutation, ledger construction, ancestry, or successor hashing.

The H0-to-H1 transaction does not wait for a domain acknowledgement. It does
not observe domain liveness. It does not publish a partial successor. H1 is
current canonical truth before any domain refresh begins.

## Canonical head and history law

> **A committed successor does not invalidate its predecessor as history. It
> invalidates predecessor-bound claims to current-head authority.**

After H1 commits:

- R0/H0 remains valid immutable canonical history and release evidence;
- H1 is the sole current canonical head;
- an H0 materialization may remain physically alive;
- an H0-bound boundary, refresh, cache, projection, receipt, or capability may
  not claim to represent H1 or authorize any current-head operation;
- a physical process cannot make H0 current by retaining, replaying, or
  rematerializing H0; and
- no physical-domain state may construct or publish another canonical
  successor.

## Current-head observation and failure atomicity

The proof harness uses one detached operational head observation only to
compare a domain's accepted record with the already committed canonical head.
The observation is not a second authority plane. It may mirror a canonical
commit; it may not select, create, delay, repair, roll back, or replace one.

Before the H0-to-H1 resolver is invoked, the harness must close one global
current-head guard. While that guard is closed:

- no domain materialization receipt is accepted as a current-head claim;
- no physical-domain evidence path is enabled;
- no physical-domain scheduling or mutation request is accepted;
- no refresh invocation is permitted; and
- both domains may continue only quarantined nonconsequential local execution.

The exact operational head-observation record is:

```yaml
observation_schema: SimultaneousPhysicalDomainsHeadObservation.v1
proof_scenario: simultaneous-physical-domains-v1
source: verified_canonical_commit_output
canonical_payload_path_role: canonical_topology_R1
canonical_payload_raw_sha256: D1
observed_canonical_hash: H1
observed_parent_canonical_hash: H0
observed_work_id: t1/00/topology/block_topology_route_0001.resolve
observed_decision_time: t1/00
observed_simulation_phase: 10
```

`D1` is the already bound raw digest of the exact sealed R1 artifact. The
observer must independently read the complete committed R1 bytes, validate the
exact Phase-1 payload, recompute D1 and H1, verify H0 ancestry and the exact
boundary identity, and only then construct this record. It may not derive H1
from a domain receipt, projection, cache, Actor, prior head-register value,
expected outcome, or harness branch.

The harness publishes the observation to its private control root as exactly
`current_head_observation.json` by:

```text
construct complete candidate bytes privately
→ write one sibling temporary file
→ fsync candidate file
→ atomically replace current_head_observation.json
→ fsync containing directory
→ independently reread and reverify exact observation bytes
```

The file is not visible to either physical-domain input root. A missing,
malformed, mismatched, partially written, stale-H0, or unverifiable observation
does not mean H0 remains current. It means current-head observation is
unproven.

Only after the independent reread proves exact H1 may the harness:

1. classify both still-H0 domains as `stale(H0/H1)`;
2. open refresh eligibility for exact H1 bundles; and
3. evaluate each domain's current-head claim against its own accepted head.

The operational observation never opens evidence, scheduling, or mutation in
this proof. Those paths remain absent or prohibited even for a synchronized
domain.

### Injected post-commit observation failure

The required fault is injected after the canonical resolver has produced and
durably verified exact R1/H1 but before the candidate operational observation
is published:

```text
global current-head guard closes
→ A and B become head_unconfirmed while remaining alive
→ exact canonical H0-to-H1 transaction commits
→ exact R1/H1 is durable canonical truth
→ injected fault prevents current_head_observation.json publication
→ prior H0 observation is not accepted as current
→ global current-head guard remains closed
→ A and B remain head_unconfirmed
→ refresh invocation is prohibited
→ current-head claims/evidence/scheduling/mutation are disabled
→ canonical H1 remains unchanged and sole authority
```

This witness terminates in the fail-closed state. It does not retry or repair
the observation and therefore does not establish retry, recovery, transport,
or operational high-availability semantics.

## Exact detached domain projections

Each physical domain receives the full exact canonical payload plus one
detached, non-authoritative projection map. The map permits representation of
one site and the shared route. It does not contain the route access value,
endpoint relation, topology definition, canonical clock, work, ledger, or
ancestry. Those facts must be read from the accepted canonical payload.

The candidate projection schema is:

```yaml
projection_schema: SimultaneousPhysicalDomainProjection.v1
projection_id: one exact value from the matrix below
proof_scenario: simultaneous-physical-domains-v1
domain_role: domain_A | domain_B
source_canonical_hash: H0 | H1
allowed_site_projection:
  canonical_site_id: topology_site_0001 | topology_site_0002
  representation_slot: domain_A_site_slot_01 | domain_B_site_slot_01
allowed_route_projection:
  canonical_route_id: topology_route_0001
  representation_slot: domain_A_route_slot_01 | domain_B_route_slot_01
```

The exact legal matrix is:

| Domain | Head | Projection ID | Site | Route |
|---|---|---|---|---|
| A | H0 | `simultaneous_domain_A_H0_0001` | `topology_site_0001` | `topology_route_0001` |
| A | H1 | `simultaneous_domain_A_H1_0001` | `topology_site_0001` | `topology_route_0001` |
| B | H0 | `simultaneous_domain_B_H0_0001` | `topology_site_0002` | `topology_route_0001` |
| B | H1 | `simultaneous_domain_B_H1_0001` | `topology_site_0002` | `topology_route_0001` |

Every cross-row combination rejects before physical materialization or
refresh. A projection may neither redirect a domain to the other site nor omit
`topology_route_0001`.

The adapter must validate that the projected site is one of the canonical
route's exact endpoint IDs. It must read the endpoint pair and `access_state`
from the canonical payload. It may not infer either from the projection, Actor
layout, transform, mesh, collision, route-slot name, or physical relation.

Both domains must visibly represent the canonical route-access fact:

```text
H0 → topology_route_0001.access_state = available
H1 → topology_route_0001.access_state = blocked
```

This is a local representation of one shared canonical fact. It is not route
occupancy, direction, geometry, traversal, navigation, streaming, or
cross-domain propagation.

## Process and root isolation

The two live domains must have:

```yaml
isolation:
  process_ids_distinct: true
  process_roots_distinct: true
  canonical_input_roots_distinct: true
  refresh_input_roots_distinct: true
  output_roots_distinct: true
  neither_root_contains_the_other: true
  shared_writable_exchange_root: none
  domain_to_domain_input_visibility: none
```

Both domains may receive byte-identical copies of the exact canonical R0 and
later R1 artifacts. Shared canonical bytes do not make their process roots or
operational identities shared. Neither domain may read the other domain's
projection, receipt, diagnostics, process state, local cache, refresh result,
or output.

The harness may observe both processes. One domain may not use the other's
liveness, refresh, failure, or destruction as a canonical or local truth
selector.

## Uninterrupted simultaneous-liveness law

Equal process labels or PIDs before and after H1 are insufficient. The harness
must bind each `operational_process_instance_id` to one exact OS process-birth
witness and continuously observe the original child handle across the complete
canonical transaction interval.

The candidate birth binding is:

```yaml
SimultaneousPhysicalDomainsWitnessId.v1:
  - w1_a_then_b
  - w2_b_then_a
  - w3_stale_quarantine
  - w4_head_observation_failure
  - w5_retention_baseline
  - w5_retention_perturbed
  - w6_asymmetric_a_synchronized
  - w6_asymmetric_b_synchronized
  - w7_destroy_a
  - w7_destroy_b

binding_schema: SimultaneousPhysicalDomainProcessBinding.v1
proof_scenario: simultaneous-physical-domains-v1
witness_id: SimultaneousPhysicalDomainsWitnessId.v1
domain_role: domain_A | domain_B
harness_launch_id: witness_id/domain_A/launch_0001 | witness_id/domain_B/launch_0001
pid: positive_integer
macos_process_start:
  seconds: nonnegative_integer
  microseconds: integer_0_through_999999
executable_realpath: exact_absolute_path
executable_raw_sha256: lowercase_sha256
process_root_realpath: exact_absolute_path
control_pipe_id: exact_harness_operational_id
structured_output_pipe_id: exact_harness_operational_id
```

`harness_launch_id` is constructed only by concatenating the exact stored
`witness_id`, the exact domain role, and `launch_0001` with `/` separators. It
is operational evidence, not a generalized identifier grammar.

The macOS process-start pair must come from `proc_pidinfo` /
`PROC_PIDTBSDINFO` for the launched PID. The harness computes
`operational_process_instance_id` as lowercase SHA-256 over canonical JSON of
the complete binding. The process receives that identity at launch and echoes
it in every accepted materialization, state, refresh, and lifecycle receipt.
The binding is detached operational evidence and never enters canonical state.

The harness must retain the original direct child handle plus the original
anonymous control and structured-output pipe endpoints. From the first H0
acceptance through the final H1 refresh receipt it must continuously monitor:

```yaml
continuous_monitor:
  original_child_handle_exit_observed: false
  wait_status_available: false
  control_pipe_unexpected_eof: false
  structured_output_pipe_unexpected_eof: false
  replacement_spawn_count: 0
```

For each direct child, the harness must register a macOS `kqueue`
`EVFILT_PROC` watch with `NOTE_EXIT` before accepting that child's H0
materialization receipt. The registered PID, the `proc_pidinfo` process-start
pair, the direct-child relationship, and both original pipe endpoints must
match the stored binding. At every L checkpoint and before accepting every
domain receipt, the harness drains the original process watch, performs
`waitpid(original_pid, WNOHANG)`, reverifies the process-start pair, and checks
both pipe endpoints. Any `NOTE_EXIT`, nonzero or indeterminate `waitpid`
result, failed process-start reverification, or unexpected pipe EOF proves that
the original instance did not remain continuously alive. A later PID lookup or
new watch cannot repair that witness.

At each exact checkpoint below, one combined witness must sample both domains
and require their complete process-birth bindings to match their launch
bindings byte-for-byte:

1. `L0`: both H0 materialization receipts accepted, before head guard closure;
2. `L1`: head guard closed, immediately before canonical boundary invocation;
3. `L2`: exact R1/H1 committed, before operational head publication;
4. `L3`: exact H1 observation published, before either refresh invocation;
5. `L4A`: first domain refresh accepted, second domain still stale;
6. `L4B`: both domain refreshes accepted.

The harness launch audit must record exactly two Unreal process launches for a
primary witness: A once and B once. A process exit, non-null wait status, pipe
EOF, changed PID/start pair, changed binding, third launch, or replacement
process fails the simultaneous-liveness witness. A later process with a reused
PID cannot satisfy the original process-start pair, child handle, and pipe
continuity.

If liveness fails after H1 commits, H1 remains canonical truth and the affected
domain cannot publish a current-head claim. The failed witness may not
substitute a new process and continue as if uninterrupted liveness were proven.

## Detached launch and refresh integrity

Before launch or refresh, the harness must inventory and hash every visible
proof input for that domain. Each accepted input tuple is exact:

```text
canonical payload bytes
+ exact domain/head projection bytes
+ detached domain-operation receipt
```

The candidate domain-operation receipt is:

```yaml
receipt_schema: SimultaneousPhysicalDomainOperationReceipt.v1
operation: launch | refresh
proof_scenario: simultaneous-physical-domains-v1
domain_role: domain_A | domain_B
expected_operational_process_instance_id: absent_for_launch | exact_existing_id_for_refresh
expected_source_head: none_for_launch | H0
expected_target_head: H0 | H1
canonical_payload_raw_sha256: exact R0 or R1 raw digest
expected_canonical_hash: H0 | H1
projection_raw_sha256: exact detached projection digest
expected_projection_id: exact legal matrix value
```

Unknown, missing, duplicate, redirected, empty, or type-incompatible members
reject. Raw bytes are verified before parse. Parsed identities, schema,
scenario, domain role, expected process identity, source head, target head,
projection, and current harness head must agree before a candidate physical
update is built.

### Exact refresh invocation and visible-input mechanism

Each domain process receives one private anonymous unidirectional control pipe
as its standard-input stream at initial launch. The harness retains the sole
write endpoint. Each process also receives one private anonymous structured
standard-output pipe for receipts. These exact pipe endpoints remain open and
bound to the original process for the uninterrupted-liveness interval.

The refresh payload is supplied only through the domain's already isolated
proof root. Before invoking refresh, the harness creates exactly this read-only
directory:

```text
DOMAIN_ROOT/
  refresh_input/
    refresh_0001/
      canonical_topology_R1.json
      simultaneous_domain_A_H1_projection.json
      simultaneous_domain_A_H1_operation_receipt.json
```

or, for B:

```text
DOMAIN_ROOT/
  refresh_input/
    refresh_0001/
      canonical_topology_R1.json
      simultaneous_domain_B_H1_projection.json
      simultaneous_domain_B_H1_operation_receipt.json
```

The directory contains exactly three regular files, no symlink, subdirectory,
device, socket, FIFO, alias, hard-link duplicate, or additional member. Its
realpath lies strictly inside that domain's root. The canonical file is an
exact byte copy of sealed R1/D1. The projection and operation receipt are the
exact role/H1 row. The harness inventories realpaths, file types, sizes, and
raw SHA-256 values after staging and before invocation, then makes the bundle
read-only with file mode `0400` and directory mode `0500`. The adapter opens
each expected file once with `O_RDONLY | O_NOFOLLOW`, verifies the opened file
descriptor with `fstat`, and hashes the bytes read from that descriptor rather
than reopening by pathname. The harness retains the pre-invocation inventory
and repeats the complete inventory after the structured refresh result; any
change rejects the result. Neither domain can see the other domain's bundle.

After exact H1 head observation is proven and the target domain is classified
`stale(H0/H1)`, the harness writes exactly one canonical-JSON object followed
by one LF to that domain's original standard-input pipe:

```yaml
command_schema: SimultaneousPhysicalDomainRefreshInvocation.v1
proof_scenario: simultaneous-physical-domains-v1
domain_role: domain_A | domain_B
operation: refresh_once
refresh_id: h0_to_h1_refresh_0001
target_canonical_hash: H1
```

The serialized object has exactly those six keys. `domain_role` is the only
role-specific value. The command contains no absolute path, caller-selected
filename, branch selector, expected outcome, retry count, transport token, or
local-state merge instruction. The adapter resolves only the fixed
role-specific `refresh_input/refresh_0001` directory and the three exact
filenames shown above.

Each process accepts exactly one refresh invocation in this proof. A second
line, extra JSON value, unknown command, wrong role, wrong refresh ID, wrong
target head, command before verified H1 observation, command delivered on a
different pipe, or any alternative visible-input member fails before private
candidate construction.

No command-line refresh, file watcher, directory polling, signal, FIFO, Unix
socket, loopback socket, network socket, shared directory, environment-variable
refresh, or runtime-selected alternative is permitted. The standard-input
line is an operational invocation only; the exact R1 bytes and detached
projection/receipt bundle are the complete refresh data.

The process emits exactly one structured refresh result on its original
standard-output pipe. Console logs, rendered state, filesystem timestamps, and
process timing are not refresh receipts.

This mechanism is bounded local harness control. It is not live input
collection, player input, packet/transport ordering law, networking, or
canonical transport.

## Exact physical-domain head-state machine

The harness owns the comparison between each domain's accepted head and the
current canonical head. The domain reports its accepted source hash; it does
not declare which canonical record is current.

The only admitted head states are:

```yaml
unbound:
  accepted_head: null
  local_execution: prohibited

synchronized:
  accepted_head: current_canonical_head
  local_nonconsequential_execution: permitted
  current_head_materialization_claim: permitted
  canonical_evidence: prohibited_in_this_proof
  canonical_scheduling: prohibited
  canonical_mutation: prohibited

head_unconfirmed:
  accepted_head: H0 | H1
  observed_current_head: unproven
  local_nonconsequential_execution: permitted_under_quarantine
  diagnostics: permitted_and_must_be_marked_head_unconfirmed
  refresh_attempt: prohibited
  current_head_materialization_claim: prohibited
  canonical_evidence: prohibited
  canonical_scheduling: prohibited
  canonical_mutation: prohibited
  canonical_truth_publication: prohibited

stale:
  accepted_head: historical_head
  current_canonical_head: different_committed_successor
  local_nonconsequential_execution: permitted_under_quarantine
  diagnostics: permitted_and_must_be_marked_stale
  refresh_attempt: permitted
  current_head_materialization_claim: prohibited
  canonical_evidence: prohibited
  canonical_scheduling: prohibited
  canonical_mutation: prohibited
  canonical_truth_publication: prohibited

invalid:
  accepted_head: untrusted_or_partially_applied
  local_nonconsequential_execution: halted
  diagnostics_and_termination_only: permitted
  refresh_attempt: prohibited
  current_head_materialization_claim: prohibited
  canonical_evidence: prohibited
  canonical_scheduling: prohibited
  canonical_mutation: prohibited
  canonical_truth_publication: prohibited
```

The exact state transitions are:

```text
unbound
  -- valid launch against current H0 --> synchronized(H0)

synchronized(H0)
  -- global current-head guard closes before commit --> head_unconfirmed(accepted H0)

head_unconfirmed(accepted H0)
  -- exact H1 commits but observation is not yet proven --> head_unconfirmed(accepted H0)

head_unconfirmed(accepted H0)
  -- exact H1 observation atomically publishes and reverifies --> stale(accepted H0, current H1)

head_unconfirmed
  -- observation missing/malformed/mismatched or publication fails --> head_unconfirmed

stale(H0/H1)
  -- valid complete atomic refresh --> synchronized(H1)

stale(H0/H1)
  -- refresh bundle rejected before local publication --> stale(H0/H1)

synchronized, head_unconfirmed, or stale
  -- detected partial publication / accepted-state corruption --> invalid

invalid
  -- proof-local recovery --> no transition
```

There is no state in which a process remains `synchronized(H0)` while the
H0-to-H1 transaction or its observation is unresolved. The guard first makes
the domain `head_unconfirmed`; only exact H1 observation may classify it
`stale(H0/H1)`. Neither classification modifies R0, R1, or canonical history.

### Stale local execution law

A stale H0 representation may continue only disposable, nonconsequential
local execution under quarantine. Examples include local rendering, animation,
collision, physics settling, camera motion, or diagnostic counters that do not
leave the process as a current-head claim.

It may not:

- emit evidence accepted as current-head evidence;
- request, retain, or invoke a canonical scheduling capability;
- call a canonical mutation or resolver path;
- label its represented access fact as current;
- publish a materialization-acceptance receipt for H1;
- overwrite or repair H1 from retained H0 state;
- cause another domain to refresh, fail, or change; or
- preserve H0 as a competing current city.

The proof does not claim that stale local physics is meaningful gameplay. It
proves only that such disposable execution cannot acquire strategic authority.

## Atomic physical refresh law

Physical refresh is not a canonical transaction. It nevertheless must be
fail-closed about claims of synchronized representation.

The adapter must:

```text
verify complete H1 payload/receipt/projection tuple
→ verify exact H1 operational head observation is published and reverified
→ verify exact existing process-birth binding and uninterrupted liveness
→ extract only the exact allowed retained-local-state projection
→ construct authoritative-derived H1 representation from empty private state
  using exact H1 + exact domain/H1 projection only
→ attach the detached retained-local-state projection without feeding it into
  authoritative-derived construction
→ validate complete candidate projection
→ publish accepted_head = H1 and the visible H1 projection together
```

Before the final local publication point, the old H0 representation remains
stale and visible only under quarantine. A rejection before publication leaves
the process exactly `stale(H0/H1)` and publishes no H1 acceptance receipt.

If a fault makes it impossible to establish that accepted-head identity and
visible authoritative-derived representation changed together, the process is
classified `invalid`, local execution halts, and no synchronized receipt is
accepted. The adapter may not claim H1 while showing H0-derived access state,
or show H1-derived access state while claiming H0.

No local refresh failure may roll back, rewrite, delay, or create canonical H1.

## Refresh reconstruction and retention law

Refresh is not a fieldwise merge between H0 representation state and H1. The
authoritative-derived representation projection is a pure reconstruction:

```text
authoritative_derived_H1_representation
  = materialize(exact sealed R1 bytes, exact role/H1 detached projection)
```

Its input set contains exactly those two values. No H0 payload, H0 projection,
Actor, component, cache, collision, physics, prior receipt, local trace,
retained scalar, expected outcome, or current visible state is an input.

### Facts that must be rederived

Every fact whose meaning expresses canonical or projection identity must be
discarded and rederived solely from exact H1 plus the exact detached
projection. This includes:

- accepted canonical raw digest and canonical hash;
- accepted projection digest and projection ID;
- `domain_role` and its exact site/route projection row;
- `topology_site_0001` or `topology_site_0002` identity;
- `topology_route_0001` identity;
- the route's exact endpoint pair and proof that the projected site is one
  endpoint;
- `topology_route_0001.access_state = blocked`;
- representation-slot bindings for the projected site and route;
- every rendered, visible, collision, gate, or interaction-enabled state whose
  meaning expresses route access; and
- the synchronized H1 materialization receipt projection.

The detached projection supplies only the permitted site ID, route ID, and
representation slots. It does not supply endpoints or access state. Exact H1
supplies canonical identity, relation, and truth.

### Exact authoritative-derived representation projection

The authoritative-derived representation projection is exactly one canonical
JSON object with these fields and no others:

```yaml
representation_schema: SimultaneousPhysicalDomainAuthoritativeDerivedRepresentation.v1
proof_scenario: simultaneous-physical-domains-v1
domain_role: domain_A | domain_B
accepted_canonical_payload_raw_sha256: D0 | D1
accepted_canonical_hash: H0 | H1
accepted_projection_raw_sha256: exact detached projection digest
accepted_projection_id: exact legal matrix value
materialized_canonical_site_id: topology_site_0001 | topology_site_0002
materialized_site_representation_slot: domain_A_site_slot_01 | domain_B_site_slot_01
materialized_canonical_route_id: topology_route_0001
materialized_route_representation_slot: domain_A_route_slot_01 | domain_B_route_slot_01
materialized_endpoint_site_ids:
  - topology_site_0001
  - topology_site_0002
materialized_route_access_state: available | blocked
```

All values are cross-field constrained by the exact domain/head projection
matrix and sealed canonical payload: H0 requires D0 and `available`; H1
requires D1 and `blocked`; A requires the A site and slots; B requires the B
site and slots. The endpoint array remains in the exact sealed canonical
storage order. The canonical JSON bytes of this complete object are the
authoritative-derived comparison surface. Actor IDs, UObject paths,
transforms, physics diagnostics, retained-local-state values, process identity,
and receipt metadata are outside it and cannot select any field within it.

### Exact retainable local state

Only this detached local structure may survive from stale H0 representation
state into the synchronized H1 process:

```yaml
retained_schema: SimultaneousPhysicalDomainRetainedLocalState.v1
nonconsequential_tick_counter: integer_0_through_9007199254740991
cosmetic_phase_token: cosmetic_phase_0 | cosmetic_phase_1 | cosmetic_phase_2 | cosmetic_phase_3
diagnostic_counter: integer_0_through_9007199254740991
```

These three values remain outside the materialization receipt's
authoritative-derived projection. They may be copied byte-for-byte only after
the H1 representation has been constructed and validated without them. They
may not select a branch, projection, Actor, component, site, route, endpoint,
access value, collision state, gate state, capability, or receipt disposition.

The operational process-birth binding also remains the same, but it is
lifecycle evidence rather than mergeable local representation state.

### State that must not survive or merge

No Actor, Actor identifier, UObject/object path, component, topology lookup
cache, accepted-head cache, payload cache, projection cache, route-access
cache, collision state, physics body/state, transform, visual access state,
interaction gate, H0 receipt, H0 capability, or H0-derived representation fact
may be retained into the published H1 authoritative-derived projection.

The proof adapter may destroy and reconstruct projected Actors and components
inside the still-running process. Same-process liveness does not require Actor
identity continuity. If an implementation reuses allocated storage, source
audit and fault witnesses must prove that every listed semantic field is reset
and rederived before publication; object reuse itself grants no retention law.

There is no conflict-resolution rule, H0/H1 preference flag, last-writer-wins
merge, local override, patch operation, or repair path. A stale local value
that disagrees with H1 is discarded, never adjudicated against H1.

### Retention perturbation witness

Two fresh isolated witness runs must use byte-identical canonical R0/H0,
boundary, R1/H1, and role/H1 projections while deliberately differing in stale
local state before refresh:

```yaml
retention_baseline:
  nonconsequential_tick_counter: 7
  cosmetic_phase_token: cosmetic_phase_0
  diagnostic_counter: 1

retention_perturbed:
  nonconsequential_tick_counter: 991
  cosmetic_phase_token: cosmetic_phase_3
  diagnostic_counter: 47
```

The perturbed branch must also poison discard-required H0 local state with
different Actor IDs, topology-cache values, route-access cache `available`,
collision-open state, and physics diagnostics before refresh. Those values are
test-only disposable local state and may not alter canonical bytes.

After exact H1 refresh, require:

```yaml
must_match_byte_identically:
  accepted_R1_raw_digest: D1
  accepted_canonical_hash: H1
  accepted_projection_identity: exact role/H1 row
  materialized_canonical_site_id: exact role site
  materialized_canonical_route_id: topology_route_0001
  materialized_endpoint_site_ids:
    - topology_site_0001
    - topology_site_0002
  materialized_route_access_state: blocked
  authoritative_derived_representation_projection: exact

may_differ_exactly_as_declared:
  retained_local_state: baseline | perturbed

must_not_survive:
  poisoned_actor_ids: true
  poisoned_topology_cache: true
  poisoned_route_access_cache: true
  poisoned_collision_state: true
  poisoned_physics_diagnostics: true
```

The equivalence oracle compares the canonical JSON bytes of the extracted
authoritative-derived representation projection, not process IDs or the
detached retained-local-state block.

## Materialization and head-state receipts

Every successful launch or refresh emits one detached receipt:

```yaml
receipt_schema: SimultaneousPhysicalDomainMaterializationReceipt.v1
proof_scenario: simultaneous-physical-domains-v1
domain_role: domain_A | domain_B
operational_process_instance_id: OperationalInstanceId.v1
process_binding_raw_sha256: exact binding digest for this process instance
accepted_canonical_payload_raw_sha256: exact R0 or R1 raw digest
accepted_canonical_hash: H0 | H1
accepted_projection_raw_sha256: exact projection digest
accepted_projection_id: exact legal matrix value
materialized_canonical_site_id: topology_site_0001 | topology_site_0002
materialized_site_representation_slot: domain_A_site_slot_01 | domain_B_site_slot_01
materialized_canonical_route_id: topology_route_0001
materialized_route_representation_slot: domain_A_route_slot_01 | domain_B_route_slot_01
materialized_endpoint_site_ids:
  - topology_site_0001
  - topology_site_0002
materialized_route_access_state: available | blocked
authoritative_derived_representation_raw_sha256: lowercase_sha256
head_state_at_receipt: synchronized
```

The digest is computed over the exact canonical JSON object defined above,
and every repeated materialization field in the receipt must equal that
object. A digest or repeated-field mismatch rejects the receipt.

The A process ID must remain identical across its H0 launch and H1 refresh.
The B process ID must remain identical across its H0 launch and H1 refresh.
A and B process IDs must differ. Every receipt's process-binding digest must
match the uninterrupted-liveness witness for that exact original child.
Actor IDs, transforms, object paths, and local physics state may differ and
remain detached.

A head-unconfirmed, stale, or invalid process may emit only a diagnostic state
receipt:

```yaml
receipt_schema: SimultaneousPhysicalDomainStateDiagnostic.v1
domain_role: domain_A | domain_B
operational_process_instance_id: OperationalInstanceId.v1
process_binding_raw_sha256: exact binding digest for this process instance
accepted_canonical_hash: H0 | H1 | null
observed_current_canonical_hash: H1 | null
head_state: head_unconfirmed | stale | invalid
refresh_enabled: false | true_only_when_stale_against_verified_H1
current_head_claim_enabled: false
canonical_evidence_enabled: false
canonical_scheduling_enabled: false
canonical_mutation_enabled: false
```

This receipt is operational evidence, never canonical truth.

## Required positive witnesses

### W1 — A then B refresh

```text
launch A from exact H0 + A/H0 projection
launch B from exact H0 + B/H0 projection
prove L0: both original process bindings concurrently alive and synchronized to H0
close global current-head guard
prove L1: both original process bindings still alive and head_unconfirmed
commit exact H0-to-H1 canonical transition independently
prove L2: both original process bindings alive before head publication
publish and independently reverify exact H1 operational observation
prove L3: both original process bindings alive and stale against H1
stage exact A/H1 three-file bundle and invoke refresh once on A's original stdin pipe
refresh A atomically to H1
prove L4A: original A synchronized / original B stale and both alive
stage exact B/H1 three-file bundle and invoke refresh once on B's original stdin pipe
refresh B atomically to H1
prove L4B: original A and B synchronized to H1 and both alive
```

### W2 — B then A refresh

Repeat W1 from fresh isolated proof roots and process instances, reversing only
the physical refresh order. The canonical R0, boundary, R1, ledger, ancestry,
and hashes must be byte-identical to W1. Both processes must satisfy the same
continuous birth-binding and pipe-continuity law.

### W3 — stale local execution quarantine

After H1 commits, exact H1 observation is proven, and before refresh, both
stale domains execute one exact bounded local nonconsequential step. The local
diagnostic may differ, but:

- no canonical bytes change;
- no current-head receipt is emitted;
- no evidence, scheduling, mutation, or truth-claim path is enabled;
- the accepted head remains H0; and
- the mechanically observed head state remains `stale(H0/H1)`.

### W4 — post-commit current-head observation failure

Inject the exact failure defined under current-head observation after H1 is
durable and before operational head publication. Require both original process
bindings alive, both domains `head_unconfirmed`, the global guard closed,
refresh prohibited, all current-head claims/evidence/scheduling/mutation
disabled, and canonical H1 byte-identical to the primary witness.

### W5 — retained-local-state perturbation

Run the exact baseline/perturbed pair defined by the retention law. Require
byte-identical H1 authoritative-derived representation projections despite the
declared retained-scalar differences and poisoned discard-required H0 Actor,
cache, collision, and physics state.

## Required asymmetric witness

The primary asymmetric failure is exact:

```text
H1 commits
→ exact H1 operational observation publishes and reverifies
→ both original process bindings remain continuously alive
→ A's original stdin pipe receives its sole exact invocation
→ A refresh reads the exact valid A/H1 three-file tuple and succeeds
→ B's original stdin pipe receives its sole exact invocation
→ B refresh reads a B/H1 operation receipt whose payload raw digest does
  not match the supplied exact R1 bytes
→ B rejects before private candidate construction or local publication
→ H1 remains sole canonical authority
→ A is synchronized(H1)
→ B remains stale(accepted H0, current H1)
→ B may continue only quarantined local nonconsequential execution
→ every H0-bound current-head capability/cache/truth claim from B fails
```

The mismatch is a harness-supplied adversarial proof input. It is not a
network, packet, retry, or live-input behavior. A symmetric branch must repeat
the witness with B successful and A stale.

## Current-head authority failures

H0 remains valid history. These failures apply only when an H0-bound object
attempts to act as current-head authority after H1 commits.

The frozen review must require at least:

1. H0-bound refresh receipt claiming target H1 with H0 bytes;
2. H0-bound projection claiming H1 as `source_canonical_hash`;
3. H0 cache or Actor state attempting to publish a current-head
   materialization receipt after H1;
4. H0-bound boundary or scheduler capability presented against current H1;
5. H0-bound mutation or resolver request presented against current H1;
6. stale domain diagnostic relabeled as synchronized;
7. stale domain route access `available` presented as current after H1;
8. domain-local state attempting to rewrite canonical route access;
9. domain-local state attempting to construct a competing successor or ledger;
10. one domain's accepted-head or refresh state used as the other domain's
    current-head oracle;
11. physical or refresh order used to select canonical outcome;
12. projection site or route redirection;
13. projection omission of `topology_route_0001`;
14. route access value supplied by the projection instead of the canonical
    payload;
15. process identity replacement presented as live-instance refresh;
16. successful receipt after partial local publication;
17. domain destruction or refresh failure changing H1; and
18. local execution trace, cache, Actor state, transform, physics, or
    diagnostic reaching canonical scheduling, gates, mutation, ledger,
    ancestry, or hashing;
19. canonical boundary invocation while the global current-head guard is open;
20. missing, stale-H0, malformed, mismatched, or unverified operational head
    observation reopening current-head or refresh eligibility after H1;
21. publication failure after H1 followed by any domain state other than
    `head_unconfirmed` or any enabled current-head path;
22. refresh invocation while current-head observation is unproven;
23. operational head observation constructed from domain, projection, cache,
    expected outcome, or prior-register state instead of exact committed R1;
24. any allowed retained-local scalar selecting or modifying an
    authoritative-derived H1 representation fact;
25. stale H0 Actor, cache, collision, physics, or receipt state surviving into
    or selecting the published H1 authoritative-derived projection;
26. equal PID with a changed process-start pair, changed process binding,
    closed original pipe, observed child exit, or replacement spawn accepted as
    uninterrupted liveness;
27. refresh accepted through a command-line flag, watcher, poller, signal,
    FIFO, socket, shared directory, alternate pipe, or second invocation; and
28. refresh bundle with any missing, additional, redirected, non-regular,
    cross-domain, mutable, or wrong-role visible input reaching candidate
    construction.

Every case fails before canonical mutation. Cases involving a malformed
physical refresh leave the domain stale if no local publication occurred and
make it invalid if atomic publication can no longer be proven.

## Destruction and isolation controls

After both domains synchronize to H1, the proof must independently terminate A
and B in symmetric controls. Each control requires:

```yaml
canonical_H1_unchanged: true
remaining_domain_head_state_unchanged: synchronized
terminated_domain_output_used_as_canonical_input: false
new_canonical_work_created: false
canonical_ledger_changed: false
canonical_ancestry_changed: false
```

This proves only that destruction of one disposable representation does not
change canonical truth. It does not prove failover, host migration, reconnect,
network resilience, save/load, or production lifecycle recovery.

## Canonical equivalence and operational variation

Across W1, W2, asymmetric A-success, asymmetric B-success, and destruction
controls, require:

```yaml
must_match:
  canonical_R0_bytes: exact sealed artifact
  canonical_H0: exact sealed identity
  canonical_boundary: byte_identical
  canonical_R1_bytes: exact sealed artifact
  canonical_H1: exact sealed identity
  authoritative_ledger: byte_identical
  canonical_ancestry: byte_identical
  future_schedule: byte_identical
  next_boundary_after_R1: identical_none

may_differ:
  operational_process_ids: yes
  process_start_order: yes
  physical_refresh_order: yes
  domain_local_nonconsequential_state: yes
  stale_diagnostics: yes
  process_termination_order: yes
```

No allowed operational difference may enter a canonical artifact or select a
canonical result.

## Failure atomicity

### Current-head observation fault surface

The exact current-head observation publication fault points are:

```yaml
head_observation_fault_points:
  - after_global_guard_close_before_canonical_invocation
  - after_R1_H1_commit_verification_before_observation_construction
  - after_observation_construction_before_temporary_write
  - after_temporary_write_before_file_fsync
  - after_file_fsync_before_atomic_replace
  - after_atomic_replace_before_directory_fsync
  - after_directory_fsync_before_independent_reread
  - after_independent_reread_before_identity_reverification
  - after_identity_reverification_before_refresh_eligibility
```

At every point the global current-head guard remains closed until exact H1 has
been independently reread and reverified and refresh eligibility has been
explicitly opened. A candidate or even atomically replaced observation file is
not sufficient by its mere existence. Any missing completion witness leaves
all affected domains `head_unconfirmed` and disables current-head claims,
evidence, scheduling, mutation, and refresh.

The required injected witness uses
`after_R1_H1_commit_verification_before_observation_construction`. H1 is already
durable canonical truth; the operational observation is absent and cannot
substitute H0 or an expected H1. No observer fault mutates either canonical
record.

### Physical refresh fault surface

The exact refresh stages that require pre/post fault injection before freeze
are:

```yaml
refresh_fault_stages:
  - invocation_read
  - visible_input_inventory
  - payload_raw_byte_verification
  - payload_parse_and_canonical_identity_verification
  - operation_receipt_verification
  - projection_verification
  - verified_head_observation_check
  - process_birth_binding_and_liveness_check
  - retained_local_state_projection_extraction
  - discard_required_state_poison_check
  - empty_authoritative_candidate_construction
  - H1_authoritative_fact_derivation
  - projection_slot_binding
  - private_candidate_validation
  - retained_local_state_attachment
  - prepublication_cross_field_validation
  - local_atomic_publication
  - materialization_receipt_emission
```

Before local publication, a fault leaves the domain stale and its H0-derived
local state quarantined. No H1 materialization receipt is accepted. At or after
an unprovable partial local publication, the domain is invalid and halted.

A stale Actor/cache/collision/physics poison value appearing in the H1
authoritative candidate is a prepublication failure, not a merge conflict. An
allowed retained scalar reaching the authoritative derivation call is a source
audit and witness failure even if the resulting H1 fact happens to match.

### Liveness failure surface

Continuous child-handle, process-start, and pipe monitoring runs independently
of refresh. An exit, wait status, unexpected EOF, binding change, or replacement
spawn at any point from L0 through L4B fails uninterrupted liveness. If H1 is
already committed, H1 remains sole authority and the affected domain cannot
publish a current-head claim. No restart may repair that witness.

No observer, refresh, retention, or liveness fault changes canonical H1 or the
other domain's already valid detached state.

## Provenance and replay

Detached proof evidence must record:

- exact sealed R0/R1 paths, raw hashes, and canonical hashes;
- the exact H0-bound canonical boundary and byte-identical R1 reproduction;
- process-root inventories and realpaths;
- process-birth bindings, continuous child-handle/pipe monitors, exact L0–L4B
  samples, and two-launch/no-replacement audits;
- global current-head guard transitions, exact operational head-observation
  bytes, publication/reread witnesses, and the injected post-commit publication
  failure;
- per-domain launch and refresh input inventories;
- exact per-domain standard-input invocation bytes and original pipe bindings;
- per-domain projection and operation-receipt hashes;
- successful materialization receipts;
- head-unconfirmed, stale, and invalid diagnostics;
- refresh-order and asymmetric-failure timelines;
- retained-local-state baseline/perturbation values, discard-required poison
  inputs, and byte-identical authoritative-derived H1 projection oracles;
- domain destruction witnesses;
- current-head authority rejection results;
- source-audit results; and
- deterministic artifact replay.

The canonical artifacts must reproduce byte-identically. Detached operational
identities may differ between independent runs but must satisfy the declared
within-run relations. The replay oracle must compare semantic operational
relations rather than require process IDs to repeat.

## Source audit

The eventual source audit must establish:

1. no new canonical payload, field, serializer, mutation, resolver, ledger, or
   scheduler implementation exists for this proof;
2. the canonical transition calls the existing Phase-1 resolver and compares
   its output byte-for-byte with the sealed R1 artifact;
3. neither Unreal domain can write canonical records, ledger entries, ancestry,
   work, boundaries, or current-head identity;
4. projection data cannot supply route access, endpoint identity, canonical
   topology, canonical clock, or work;
5. domain head state, operational observation, process identity, liveness,
   refresh state, Actor state, cache, collision, physics, retained scalars, and
   diagnostics do not dataflow into canonical execution;
6. the global current-head guard closes before canonical invocation and cannot
   reopen from file existence, expected outcome, prior H0 observation, or any
   source other than independently reverified exact H1;
7. the operational head observer reads only complete committed canonical bytes
   and cannot write, select, repair, delay, or roll back canonical head;
8. head-unconfirmed and stale local execution have no outward current-head
   evidence, scheduling, mutation, or truth-publication path;
9. the authoritative-derived H1 representation constructor has exactly two
   inputs: exact H1 and the exact role/H1 projection;
10. only the exact three-field retained-local-state projection may cross
    refresh, and it cannot reach the authoritative-derived constructor;
11. stale Actor, cache, collision, physics, receipt, capability, and H0-derived
    representation state is discarded before H1 publication;
12. refresh is private until one complete local publication point;
13. the only refresh invocation is one exact line on each original stdin pipe,
    and each fixed role-specific visible-input directory has exactly three
    regular read-only members;
14. original child handles, macOS process-start pairs, birth bindings, and pipe
    endpoints remain continuous from L0 through L4B with no replacement spawn;
15. one domain cannot read or select from the other's proof root or local state;
16. process, local-state perturbation, and refresh order cannot select canonical
    or materialized access truth; and
17. no occupancy, movement, networking, streaming, World Partition, player,
    or production abstraction is introduced under the proof fixture.

## Explicit exclusions

This proof does not authorize or prove:

- canonical subject or occupancy materialization;
- physical movement, traversal, navigation, interpolation, coordinates,
  distance, speed, travel time, arrival, route progress, or route occupancy;
- Q, BQ, QA, QB, BEXT, external admission, external arbitration, or any
  additional physical-evidence type;
- live external-input collection, candidate-set completeness, packet order,
  transport order, retry, re-admission, or open-ended input streams;
- distributed head consensus, head-register authority, observer recovery,
  refresh retry, reconnect, or durable local-state persistence;
- player embodiment, split players, two-player gameplay, 1–4 player topology,
  split crews, or player-to-domain ownership;
- networking, replication, reconciliation, rollback, host migration, save/load,
  disconnect, reconnect, or shared multi-owner persistence;
- World Partition, streaming, streaming bubbles, levels, Level Instances,
  cells, proximity promotion, or production materialization architecture;
- cross-domain causal propagation, domain-to-domain messaging, shared local
  physics, or one domain updating the other;
- arbitrary domain counts, dynamic domain creation, production lifecycle
  management, city population, city scale, or performance;
- new canonical topology, access semantics, occupancy, contention, movement,
  scheduler, resolver, or canonical payload behavior;
- randomness, stochastic identity, generalized planning, or Phase 4–6; or
- production architecture of any kind.

## Review gates before freeze

This draft may freeze only after review establishes:

```yaml
freeze_review:
  proof_question: exact
  canonical_R0_R1_artifacts: exact_and_byte_bound
  phase_1_physical_lifecycle_noninheritance: explicit
  canonical_transaction_independence: exact
  physical_domain_definition: exact
  process_birth_binding: exact
  uninterrupted_simultaneous_liveness_witness: exact_L0_through_L4B
  no_exit_restart_replacement_law: exact
  domain_A_and_B_projections: exhaustive
  shared_route_projection: required_in_both_domains
  launch_and_refresh_input_inventory: exhaustive
  operation_receipts: exhaustive
  refresh_invocation: exact_original_stdin_pipe_single_canonical_json_line
  refresh_visible_inputs: exact_role_specific_three_file_read_only_bundle
  alternate_refresh_mechanisms: prohibited
  current_head_observer_schema: exact
  current_head_guard_and_publication_order: exact
  current_head_observation_failure_atomicity: exact_nine_fault_points
  post_commit_prepublication_failure_witness: exact
  physical_head_state_machine: exhaustive
  head_unconfirmed_state: exact
  stale_local_execution_law: exact
  invalid_state_and_halt_law: exact
  authoritative_derived_reconstruction_inputs: exact_H1_plus_projection_only
  retained_local_state_schema: exact_three_fields
  actor_cache_collision_physics_retention: prohibited
  retention_perturbation_witness: exact
  physical_refresh_publication_boundary: exact
  asymmetric_witnesses: exact_and_symmetric
  current_head_authority_failures: exhaustive
  failure_atomicity: fault_points_frozen
  domain_isolation: exact
  canonical_equivalence: exact
  provenance_and_replay: exact
  source_audit: exact
  release_manifest: self_excluding_and_mechanically_verified
  exclusions: exact
```

Draft.1 resolves the prior refresh-transport dependency with the original
per-domain stdin pipe plus exact isolated three-file bundle. It also resolves
head-observation failure atomicity, retention/reconstruction semantics, and
uninterrupted process-liveness identity for freeze review.

Freeze review must still reject any optional projection member, alternate
refresh channel, incomplete head-observation gate, ambiguous
head-unconfirmed/stale/invalid disposition, retained authoritative-derived H0
state, replaceable process identity, or unspecified local publication
boundary. Passing review is not itself implementation authority.

## Candidate acceptance statement

If a later frozen implementation passes every required gate, it may establish
only:

> **Two process-isolated Unreal representation domains can remain
> simultaneously alive while one exact canonical topology record advances
> independently from H0 to H1. Each live process can rebind through an exact
> detached projection to the same H1, while any process still representing H0
> is mechanically stale, may continue only quarantined nonconsequential local
> execution, and cannot exercise current-head evidence, scheduling, mutation,
> or truth authority. Failure to prove operational observation of committed H1
> closes every current-head path rather than creating another head, refresh
> reconstructs every authoritative-derived fact solely from H1 plus the exact
> projection, and uninterrupted process-birth evidence proves neither physical
> domain exited or was replaced across the commit.**

It may not establish multiplayer, networking, occupancy materialization,
movement, streaming, or production physical-domain architecture.

## Draft review history

### 0.1.0-draft.1 — 2026-08-28

- Closed the global current-head guard before canonical invocation and required
  an exact independently reverified H1 observation before refresh eligibility.
- Added the exact injected post-commit/prepublication observer failure and the
  `head_unconfirmed` fail-closed state.
- Fixed the sole refresh mechanism as one canonical-JSON line on each original
  process stdin pipe plus one isolated role-specific three-file H1 bundle.
- Replaced refresh merge ambiguity with exact H1-plus-projection
  reconstruction, a three-field retained-local whitelist, mandatory discard of
  stale Actor/cache/collision/physics state, and a perturbation witness.
- Bound operational instance identity to macOS process-birth evidence, original
  child handles, continuous pipe monitoring, exact L0–L4B samples, and a
  two-launch/no-replacement audit.
- Kept the proof unimplemented, unfrozen, and non-capacity-bearing.

### 0.1.0-draft.0 — 2026-08-28

- Selected Phase 3 for specification review only.
- Opened the two-live-domain H0-to-H1 lifecycle, exact detached site/route
  projections, synchronized/stale/invalid head law, refresh-order witnesses,
  asymmetric refresh failure, and explicit non-scope.

## Current decision record

```yaml
working_unit: Simultaneous Physical Domains Proof v0.1.0-draft.1
successor_selected: true
specification_status: freeze_review
freeze_status: not_frozen
implementation_authority: none
canonical_capacity_change: none
latest_sealed_capacity: THE_CITY Development Capacity and Progress Note v0.1.11
```

No code may be written for this proof until a separately reviewed freeze fixes
the complete contract and explicitly grants bounded implementation authority.
