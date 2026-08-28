# Simultaneous Physical Domains Proof

**Version:** 0.1.0
**Status:** Frozen specification; exact bounded Phase-3 implementation, evidence, and release verification authorized; evidence unsealed
**Selected:** 2026-08-28
**Advanced to freeze review:** 2026-08-28
**Frozen:** 2026-08-28
**Parent continuation:** [Co-op Open-City FPS Simulation — v0.7 Working Continuation](Co-op%20Open-City%20FPS%20Simulation%20-%20v0.7%20Working%20Continuation.md)
**Latest sealed predecessor:** [Canonical Occupancy Transition Proof — v0.1.0](Canonical%20Occupancy%20Transition%20Proof%20Evidence%20-%20v0.1.0.md)
**Canonical source payload:** `CanonicalSpatialTopologyIdentityPayload.v1` / `0.7.0-draft.61`, reused byte-for-byte
**Frozen proof-harness identity:** `SimultaneousPhysicalDomainsProof.v1` / `0.7.0-draft.72`

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
  version: 0.1.0
  status: frozen_specification
  implementation_authority: bounded_phase_3_proof_only
  unreal_source_change_authority: exact_frozen_phase_3_paths_only
  capacity_advancement: none
  freeze_status: frozen
  evidence_status: unsealed
```

This reviewed freeze authorizes only the exact bounded Phase-3 proof,
Unreal-adapter, harness, test, evidence, artifact, and release-verification
surface declared below. It authorizes no capacity advancement, production
architecture, or adjacent scope.

## Governing predecessor boundary

### Exercised predecessor evidence

The frozen proof directly composes these exact sealed records:

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
  guard_open_canonical_controls: 1 exact branch
  stale_local_state_perturbation_pairs: 1 exact pair
  independent_live_UE_observations_per_primary_order: 4
  release_artifact_members: 44 exact files
  release_manifest_members: 110 exact files_excluding_manifest
  uninterrupted_liveness_intervals: 2 domains across 1 canonical commit
  external_inputs: none
  occupancy_materializations: none
  authoritative_random_draws: none
  implementation_authority: bounded_phase_3_proof_only
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

The authorized implementation proof must reproduce R1 byte-for-byte
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

Before the H0-to-H1 resolver is invoked, the harness protocol must close one
global **physical-current-head guard**. The guard is head-qualified physical
protocol state, not a boolean authority register. Its exact states are:

```yaml
physical_current_head_guard:
  open_for_H0:
    accepted_physical_head: H0
    current_head_representation_claim_acceptance: H0_only
    refresh_eligibility: false
  closed_for_H0_to_H1:
    accepted_physical_head: none
    current_head_representation_claim_acceptance: false
    refresh_eligibility: false
  open_for_H1:
    accepted_physical_head: H1
    current_head_representation_claim_acceptance: H1_only
    refresh_eligibility: stale_H0_to_exact_H1_only
  failed_closed:
    accepted_physical_head: none
    current_head_representation_claim_acceptance: false
    refresh_eligibility: false
    reopening: prohibited_in_this_proof
```

The guard governs only:

- acceptance of a physical materialization as a current-head claim;
- harness acceptance of Unreal materialization and physical-observation
  receipts; and
- harness eligibility to stage and invoke a domain refresh.

The guard is incapable of gating canonical execution. It is not an input,
parameter, precondition, capability, lock, branch, or failure mode of the
sealed Phase-1 boundary discovery, resolver, transaction, commit, serializer,
ledger, ancestry, or hash path. The canonical path receives only the exact
sealed R0/H0 and its exact H0-bound boundary. It neither reads nor can discover
the guard, head-observation file, domain state, receipt state, or refresh
eligibility. Physical evidence, canonical scheduling from a domain, and
canonical mutation from a domain remain unconditionally absent or prohibited;
the guard does not turn those paths on or off.

The initial synchronized H0 dispositions require `open_for_H0`. The normal
transition changes the guard atomically from `open_for_H0` to
`closed_for_H0_to_H1` before canonical invocation. While it is closed, no
physical receipt is accepted as current and no refresh command is sent. Both
domains may continue only quarantined nonconsequential local execution under
the physical head-state law.

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

The file is harness-private and lies outside both physical-domain roots. Its
path, bytes, digest, existence, absence, validity, publication result, and any
derived boolean or head-state classification must never enter Unreal through a
file, directory, command line, environment variable, inherited descriptor,
standard-input command, operation receipt, projection, process binding, or
shared memory. A missing, malformed, mismatched, partially written, stale-H0,
or unverifiable observation does not mean H0 remains current. It means
current-head observation is unproven to the harness.

Only after the independent reread proves exact H1 may the harness perform one
ordered, indivisible physical-protocol transition:

1. classify every still-H0 affected domain as `stale(H0/H1)`;
2. change the guard from `closed_for_H0_to_H1` to `open_for_H1` only after all
   those stale classifications are durably recorded;
3. open refresh eligibility for stale-H0 to exact-H1 bundles only;
4. stage a role-specific bundle and send the already frozen refresh command;
   and
5. evaluate later Unreal receipts and independent physical observations
   against H1 at the harness boundary.

This is the only normal guard reopening in the proof. `open_for_H1` cannot
accept H0 as current, cannot authorize another canonical transition, and does
not reopen evidence, scheduling, mutation, or truth publication. A fault before
the complete H1 reread/reverification and both stale classifications leaves the
guard `failed_closed` for that witness; no partial reopening is legal.

The Unreal refresh adapter does not perform any head-observation check. It
verifies only its declared visible command/bundle inputs and its exact process
binding, then publishes a disposable representation of the supplied record.
The adapter may report which canonical hash it represents; it may not report
that the hash is current. Only the harness compares that represented hash with
its private verified head. The operational observation never opens evidence,
scheduling, or mutation in this proof. Those paths remain absent or prohibited
even for a harness-classified synchronized domain.

### Guard-open canonical control

The required guard-order adversary deliberately leaves the physical-current-
head guard `open_for_H0` and invokes the exact sealed Phase-1 boundary and
resolver. The canonical resolver must still produce and durably commit
byte-identical R1/H1 without reading the guard. Immediately after the harness
independently verifies that committed output, it must atomically change the
guard to `failed_closed` and classify both affected domains
`protocol_invalid(accepted H0, committed H1, guard_open_at_commit)`.

`protocol_invalid` is the exact terminal physical disposition for this
negative control. Local execution is halted; diagnostics and termination are
the only permitted process actions; current-head representation claims,
receipt acceptance, refresh, evidence, scheduling, mutation, and truth
publication are disabled. The control may not publish the normal operational
head observation, reopen the guard, refresh either domain, or convert either
domain to `stale` or `synchronized`. The Phase-3 harness witness fails, while
the canonical transaction remains byte-identical, durable, neither rejected
nor rolled back. This control proves guard order protects physical acceptance
only and cannot select canonical execution.

### Injected post-commit observation failure

The required fault is injected after the canonical resolver has produced and
durably verified exact R1/H1 but before the candidate operational observation
is published:

```text
global physical-current-head guard changes to closed_for_H0_to_H1
→ A and B become head_unconfirmed while remaining alive
→ exact canonical H0-to-H1 transaction commits
→ exact R1/H1 is durable canonical truth
→ injected fault prevents current_head_observation.json publication
→ prior H0 observation is not accepted as current
→ global physical-current-head guard changes to failed_closed
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
  - w8_guard_open_control

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
unreal_engine_build_identity: exact_UE_5_8_build_identity
entry_map_package_identity: exact_Engine_Maps_Entry_identity
project_realpath: exact_absolute_path
project_raw_sha256: lowercase_sha256
project_config_and_module_inventory_raw_sha256: lowercase_sha256
process_root_realpath: exact_absolute_path
launch_argv_raw_sha256: lowercase_sha256_of_exact_ordered_argv
launch_environment_audit_raw_sha256: lowercase_sha256_of_redacted_complete_audit
launch_cwd_realpath: exact_repository_root_realpath
inherited_descriptor_map_raw_sha256: lowercase_sha256
control_pipe_id: exact_harness_operational_id
structured_output_pipe_id: exact_harness_operational_id
diagnostic_pipe_id: exact_harness_operational_id
```

`harness_launch_id` is constructed only by concatenating the exact stored
`witness_id`, the exact domain role, and `launch_0001` with `/` separators. It
is operational evidence, not a generalized identifier grammar.

The macOS process-start pair must come from `proc_pidinfo` /
`PROC_PIDTBSDINFO` for the launched PID. The harness computes
`operational_process_instance_id` as lowercase SHA-256 over canonical JSON of
the complete binding.

The binding is delivered without a hidden launch channel. The harness creates
the two anonymous pipes, launches the direct child with macOS
`POSIX_SPAWN_START_SUSPENDED`, obtains and verifies its PID/process-start pair,
registers the exit watch, constructs the complete binding, and writes exactly
one canonical-JSON binding command plus LF to the original stdin pipe before
resuming the child:

```yaml
command_schema: SimultaneousPhysicalDomainBindInvocation.v1
proof_scenario: simultaneous-physical-domains-v1
operation: bind_process_once
operational_process_instance_id: lowercase_sha256_of_complete_binding
process_binding: exact complete SimultaneousPhysicalDomainProcessBinding.v1 object
```

The Unreal process must consume this as its first input, verify the observable
PID, executable, engine build/entry map, project, module/config inventory, root,
argv digest, cwd, role, and standard-input/output/diagnostic descriptors, store the binding immutably,
and echo its identity/digest in every accepted
materialization, refresh, physical observation, and lifecycle result. The
harness separately verifies that the descriptors are the original binding's
pipe endpoints. A second binding command or resume before the complete command
is buffered fails launch. The binding contains no canonical head, head
observation, physical guard, refresh eligibility, or expected access state. It
is detached operational evidence and never enters canonical state.

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

1. `L0`: both H0 representation receipts and independent live `available`
   observations accepted, before physical guard closure;
2. `L1`: physical guard closed, immediately before canonical boundary
   invocation;
3. `L2`: exact R1/H1 committed, before operational head publication;
4. `L3`: exact H1 observation published, before either refresh invocation;
5. `L4A`: first domain H1 receipt plus independent live `blocked` observation
   accepted, second domain still stale;
6. `L4B`: both domains' H1 receipts plus independent live `blocked`
   observations accepted.

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
expected_source_represented_hash: none_for_launch | H0
expected_target_represented_hash: H0 | H1
canonical_payload_raw_sha256: exact R0 or R1 raw digest
expected_canonical_hash: H0 | H1
projection_raw_sha256: exact detached projection digest
expected_projection_id: exact legal matrix value
```

Unknown, missing, duplicate, redirected, empty, or type-incompatible members
reject. Raw bytes are verified before parse. Parsed identities, schema,
scenario, domain role, expected process identity, source represented hash,
target represented hash, projection, and payload must agree with one another
before a candidate physical update is built. Separately, before staging any
refresh bundle, the harness must compare that exact tuple with its private
verified H1 and stale-domain classification. That harness comparison is not an
Unreal-visible input and is not repeated by the adapter.

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

As a harness-only protocol step, after exact H1 head observation is proven and
the target domain is classified `stale(H0/H1)`, the harness writes exactly one
canonical-JSON object followed by one LF to that domain's original
standard-input pipe:

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
refresh command, extra JSON value on one line, unknown command, wrong role,
wrong refresh ID, wrong target head relative to the visible bundle, command
delivered on a different pipe, or any alternative visible-input member fails
before private candidate construction. The two separately declared physical-
inspection commands are not refresh invocations and are routed only to the
independent probe. Delivery of the refresh command before the harness has
privately verified H1 is not an adapter-detectable condition: it is a harness-
protocol failure, the physical guard changes to `failed_closed`, and no
resulting receipt or representation is accepted as current. If no local
publication occurred, the affected domain remains `head_unconfirmed`; if local
publication occurred or cannot be excluded, it becomes `invalid`. Neither
state may refresh again in that witness.

No command-line refresh, file watcher, directory polling, signal, FIFO, Unix
socket, loopback socket, network socket, shared directory, environment-variable
refresh, or runtime-selected alternative is permitted. The standard-input
line is an operational invocation only; the exact R1 bytes and detached
projection/receipt bundle are the complete refresh data.

The refresh adapter emits exactly one structured materialization result on its
original standard-output pipe. The independent physical observer later emits a
separate structured observation on the same output pipe. Console logs,
filesystem timestamps, process timing, and either structured object standing
alone are not proof of a successful current-head rebind.

This mechanism is bounded local harness control. It is not live input
collection, player input, packet/transport ordering law, networking, or
canonical transport.

### Exact proof-semantic input closure

This contract does not claim that an Unreal process sees no operating system,
engine, executable, project, environment, or runtime context. **Proof-semantic
input** means any byte, value, state, or dependency permitted to select a proof
branch, validate an input, construct or modify authoritative-derived
representation facts, publish local representation state, construct a receipt,
classify the physical observation, or affect the Phase-3 pass/fail result.

The exact proof-semantic closure is:

```yaml
proof_semantic_inputs:
  immutable_process_binding:
    - exact SimultaneousPhysicalDomainProcessBinding.v1 bytes
  adapter_launch_tuple:
    - exact R0 bytes
    - exact role/H0 projection
    - exact role/H0 operation receipt
  stdin_commands_in_exact_order:
    - exact bind_process_once invocation carrying the process binding
    - exact launch_physical_0001 inspection invocation
    - exact h0_to_h1_refresh_0001 refresh invocation
    - exact refresh_physical_0001 inspection invocation
  adapter_refresh_tuple:
    - exact R1 bytes
    - exact role/H1 projection
    - exact role/H1 operation receipt
  probe_live_state:
    - exact role-derived live Actor count
    - exact live route mesh visibility and color parameter
    - exact live access-label visibility, text, and color
  executable_and_project_dependencies:
    - exact UnrealEditor executable realpath and raw SHA-256
    - exact Unreal Engine 5.8 build identity
    - exact CityMaterializationProof.uproject realpath and raw SHA-256
    - exact DefaultEngine.ini, DefaultGame.ini, and DefaultInput.ini raw SHA-256
    - exact Engine/Maps/Entry package identity selected by DefaultEngine.ini
    - exact loaded CityMaterializationProof module realpath and raw SHA-256
    - exact release-manifest hashes of all declared Unreal source/project members
  semantic_environment_keys: []
  semantic_command_line_selectors: []
  semantic_inherited_descriptors:
    - fd_0_original_control_pipe_read_endpoint
    - fd_1_original_structured_output_pipe_write_endpoint
  prohibited_hidden_semantic_inputs:
    - current_head_observation_path_or_bytes
    - physical_current_head_guard_state
    - harness_head_state_classification
    - harness_refresh_eligibility
    - expected_physical_access_result
    - other_domain_root_or_state
    - project_Content_ProofRecords
    - filesystem_timestamp_or_directory_order
    - console_log_or_diagnostic_stream
    - environment_or_argv_proof_selector
    - inherited_or_runtime_opened_alternate_command_channel
    - shared_memory_or_shared_mutable_object
```

The launch tuple is staged before spawn under exactly
`DOMAIN_ROOT/launch_input/launch_0001/` as the role-specific equivalents of
`canonical_topology_R0.json`, `simultaneous_domain_ROLE_H0_projection.json`,
and `simultaneous_domain_ROLE_H0_operation_receipt.json`. It has the same exact
three-regular-file, no-link, raw-hash, opened-descriptor, and read-only rules as
the refresh tuple. The immutable binding gives the adapter the exact domain
root only after the suspended child has been bound. No Phase-3 fixture path or
expected result appears in launch arguments or environment.

The complete launch-surface audit is exact:

```yaml
launch_surface_audit:
  argv_in_order:
    - exact UnrealEditor executable realpath
    - exact CityMaterializationProof.uproject realpath
    - -game
    - -Multiprocess
    - -NoSplash
    - -Windowed
    - -ResX=900
    - -ResY=650
    - -WinX=30 for A | -WinX=990 for B
    - -WinY=60
    - -UserDir=exact role-isolated user root
    - -abslog=exact role-isolated diagnostic path
  argv_audit:
    exact_order_and_values_recorded: true
    proof_semantic_selector_allowlist: []
    other_domain_path_present: false
    head_observation_or_guard_value_present: false
  environment:
    construction: complete inherited environment plus role-isolated TMPDIR override
    evidence_form: sorted keys plus per-value SHA-256 and whole-map SHA-256
    plaintext_values_released: false
    proof_semantic_key_allowlist: []
    adapter_or_probe_environment_reads: prohibited
    other_domain_path_present: false
    head_observation_or_guard_value_present: false
  cwd:
    value: exact repository root realpath
    adapter_or_probe_cwd_branching: prohibited
  inherited_descriptors:
    fd_0: original control pipe read endpoint
    fd_1: original structured-output pipe write endpoint
    fd_2: role-isolated diagnostic pipe write endpoint
    all_other_descriptors_at_exec: closed
    fd_2_proof_semantic_input: false
  executable_project_and_runtime:
    executable_project_config_module_hashes: recorded_and_binding_verified
    unreal_engine_build_and_entry_map_identity: recorded_and_binding_verified
    engine_and_system_loaded_image_inventory: realpath_UUID_and_raw_hash_recorded
    initial_world_actor_class_inventory_before_first_materialization: recorded
    non_Phase3_world_actor_reads_for_proof_semantics: prohibited
    project_Content_ProofRecords_reads: prohibited
    alternate_fixture_or_command_file_reads: prohibited
    dynamic_loader_and_engine_internal_descriptors: platform_context_only
    application_level_reads_from_runtime_descriptors: prohibited
```

The environment, diagnostic descriptor, engine state, dynamic-loader state,
system libraries, and engine-opened descriptors remain process-visible platform
context. They are not asserted absent. Their audited identities are provenance,
not proof selectors. Static call-graph/file-open/environment-read audit plus the
runtime inventories must prove that no adapter, command router, representation
Actor, or physical probe reads them as Phase-3 data or branches on them to
produce a proof result. A different inventory is a replay-environment mismatch,
not a source of alternate truth.

The adapter consumes only the immutable binding, its exact launch or refresh
tuple, and the refresh command. The independent probe consumes only the
immutable binding, the two inspection commands, and the declared live Actor
component surfaces. Neither component may read a harness control-root path.
Any value outside the exact proof-semantic closure that reaches proof branch
selection, authoritative-derived construction, publication, receipt,
observation classification, or acceptance fails the witness.

## Exact physical-domain head-state machine

The harness owns the comparison between each domain's accepted head and the
current canonical head. The domain reports its accepted source hash; it does
not declare which canonical record is current.

Every state and diagnostic classification below is harness-owned. Unreal may
report only represented-record and local-publication facts; it neither receives
nor emits `synchronized`, `head_unconfirmed`, or `stale`.

The only admitted head states are:

```yaml
unbound:
  accepted_head: null
  local_execution: prohibited

synchronized:
  accepted_head: current_canonical_head
  local_nonconsequential_execution: permitted
  current_head_materialization_claim: permitted_as_harness_accepted_representation_only
  claim_preconditions:
    - represented_hash_equals_privately_verified_head
    - exact_matching_head_guard_is_open
    - representation_receipt_and_independent_live_observation_are_accepted
  claim_authority: disposable_representation_correspondence_only
  canonical_evidence: prohibited_in_this_proof
  canonical_scheduling: prohibited
  canonical_mutation: prohibited
  canonical_truth_publication: prohibited

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

protocol_invalid:
  accepted_head: H0
  committed_head: H1
  reason: guard_open_at_commit
  local_nonconsequential_execution: halted
  diagnostics_and_termination_only: permitted
  refresh_attempt: prohibited
  current_head_materialization_claim: prohibited
  canonical_evidence: prohibited
  canonical_scheduling: prohibited
  canonical_mutation: prohibited
  canonical_truth_publication: prohibited
  terminal: true
```

The exact state transitions are:

```text
unbound
  -- valid launch receipt + independent live available observation against H0
     + guard open_for_H0 --> synchronized(H0)

synchronized(H0)
  -- guard open_for_H0 changes to closed_for_H0_to_H1 before commit --> head_unconfirmed(accepted H0)

head_unconfirmed(accepted H0)
  -- exact H1 commits but observation is not yet proven --> head_unconfirmed(accepted H0)

head_unconfirmed(accepted H0)
  -- exact H1 observation atomically publishes and reverifies,
     both affected domains classify stale, then guard opens_for_H1 --> stale(accepted H0, current H1)

head_unconfirmed
  -- observation missing/malformed/mismatched or publication fails --> head_unconfirmed

stale(H0/H1)
  -- valid complete atomic refresh + independent live blocked observation
     + harness acceptance against private H1 --> synchronized(H1)

stale(H0/H1)
  -- refresh bundle rejected before local publication --> stale(H0/H1)

synchronized, head_unconfirmed, or stale
  -- detected partial publication / accepted-state corruption --> invalid

synchronized(H0) with guard open_for_H0
  -- exact H1 commits before required guard closure --> protocol_invalid(accepted H0, committed H1, guard_open_at_commit)

protocol_invalid
  -- proof-local recovery or refresh --> no transition

invalid
  -- proof-local recovery --> no transition
```

In the normal protocol there is no state in which a process remains
`synchronized(H0)` while the H0-to-H1 transaction or its observation is
unresolved. The guard first makes the domain `head_unconfirmed`; only exact H1
observation plus atomic stale classification and `open_for_H1` transition may
make it refresh-eligible. In the guard-open negative control, committed H1
forces the explicit terminal `protocol_invalid` disposition instead. None of
these physical classifications modifies R0, R1, or canonical history.

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

Before sending the refresh command, the harness alone must prove exact H1,
classify the domain stale, open refresh eligibility, stage the exact bundle,
and reverify the original process binding. None of those private head or guard
facts is sent into Unreal.

The adapter must then:

```text
verify complete H1 payload/receipt/projection tuple
→ verify exact process-binding identity visible to this original process
→ extract only the exact allowed retained-local-state projection
→ construct authoritative-derived H1 representation from empty private state
  using exact H1 + exact domain/H1 projection only
→ attach the detached retained-local-state projection without feeding it into
  authoritative-derived construction
→ validate complete candidate projection
→ publish represented_head = H1 and the visible H1 projection together
→ emit one representation receipt that makes no current-head claim
```

Before the final local publication point, the old H0 representation remains
represented and visible only under harness quarantine. A rejection before
publication leaves the process representing H0 and publishes no H1
materialization receipt; the harness classification remains `stale(H0/H1)`.

If a fault makes it impossible to establish that represented-head identity and
visible authoritative-derived representation changed together, the process is
classified `invalid` by the harness, local execution halts, and no current-head
receipt is accepted. The adapter may not report represented H1 while showing
H0-derived access state, or show H1-derived access state while reporting
represented H0. Even a structurally valid H1 receipt remains insufficient
until the independent live-UE physical observer passes and the harness accepts
both objects against its private H1.

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

## Materialization and harness head-disposition receipts

Every successful Unreal launch or refresh emits one detached representation
receipt:

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
receipt_authority: representation_only
```

The digest is computed over the exact canonical JSON object defined above,
and every repeated materialization field in the receipt must equal that
object. A digest or repeated-field mismatch rejects the receipt.

The receipt asserts only that this process represents the accepted payload. It
contains no `current_head`, `observed_current_head`, `head_state`, guard,
observation, refresh-eligibility, canonical evidence, scheduling, or mutation
field. Receipt emission cannot classify the process as synchronized.

The A process ID must remain identical across its H0 launch and H1 refresh.
The B process ID must remain identical across its H0 launch and H1 refresh.
A and B process IDs must differ. Every receipt's process-binding digest must
match the uninterrupted-liveness witness for that exact original child.
Actor IDs, transforms, object paths, and local physics state may differ and
remain detached.

The harness emits a separate detached disposition after applying its private
head observation and, for a purported synchronized materialization, the
independent physical-rebind oracle:

```yaml
disposition_schema: SimultaneousPhysicalDomainHeadDisposition.v1
proof_scenario: simultaneous-physical-domains-v1
domain_role: domain_A | domain_B
operational_process_instance_id: OperationalInstanceId.v1
process_binding_raw_sha256: exact binding digest for this process instance
representation_receipt_raw_sha256: lowercase_sha256 | null
physical_observation_raw_sha256: lowercase_sha256 | null
represented_canonical_hash: H0 | H1 | null
harness_observed_current_canonical_hash: H0 | H1 | null
physical_current_head_guard_state: open_for_H0 | closed_for_H0_to_H1 | open_for_H1 | failed_closed
head_state: head_unconfirmed | stale | synchronized | invalid | protocol_invalid
refresh_enabled: true_iff_stale_H0_against_verified_H1_and_guard_open_for_H1 | false
current_head_claim_enabled: true_iff_synchronized_to_guard_matching_privately_verified_head | false
current_head_claim_scope: disposable_representation_correspondence_only | none
canonical_evidence_enabled: false
canonical_scheduling_enabled: false
canonical_mutation_enabled: false
```

The exact permission matrix is:

| Head state | Required guard | Current-head representation claim | Refresh | Local execution |
| --- | --- | --- | --- | --- |
| `synchronized(H0)` | `open_for_H0` | enabled, representation-only | disabled | nonconsequential permitted |
| `head_unconfirmed(H0)` | `closed_for_H0_to_H1` or `failed_closed` | disabled | disabled | quarantined nonconsequential permitted |
| `stale(H0/H1)` | `open_for_H1` | disabled | exact H1 once | quarantined nonconsequential permitted |
| `synchronized(H1)` | `open_for_H1` | enabled, representation-only | disabled | nonconsequential permitted |
| `invalid` | any matching recorded state | disabled | disabled | halted; diagnostics/termination only |
| `protocol_invalid(H0/H1)` | `failed_closed` | disabled | disabled | halted; diagnostics/termination only |

For a synchronized result, both receipt digests are required, the represented
and privately verified harness head must be identical, the guard must be open
for that exact head, and the physical observation must match the expected live
H0 or H1 representation law. `current_head_claim_enabled: true` means only that
the harness accepts this disposable representation as corresponding to its
privately verified current head. It grants no canonical evidence, scheduling,
mutation, truth publication, strategic authority, or right to select another
head. The disposition is written only under the harness evidence root and is
never provided to Unreal. It is operational evidence, never canonical truth.

An Unreal process may emit a local failure diagnostic, but it may contain only
its process binding, represented hash if known, local publication stage, and
reason code. It may not name `synchronized`, `stale`, `head_unconfirmed`, or a
current canonical head.

## Independent live-UE physical rebind oracle

Correct canonical JSON and a correct materialization receipt are necessary but
insufficient. In each original Unreal process, a proof-local observer distinct
from the refresh adapter must inspect the actually published live route
representation at H0 and again after H1 refresh.

### Exact physical representation signal

The one projected route Actor carries one noncanonical probe tag fixed only by
domain role and route slot:

```yaml
domain_A: simultaneous_physical_domain/domain_A/domain_A_route_slot_01
domain_B: simultaneous_physical_domain/domain_B/domain_B_route_slot_01
```

Exactly one live `ASimultaneousPhysicalDomainRepresentationActor` with that
tag must exist in the process world. Its route mesh and access label must be
registered, visible, and not hidden. The exact access-state surfaces are:

```yaml
available:
  route_mesh_color_parameter_rgba: [0.10, 0.85, 0.35, 1.00]
  access_label_text: AVAILABLE
  access_label_color_rgba8: [0, 255, 0, 255]

blocked:
  route_mesh_color_parameter_rgba: [0.90, 0.12, 0.12, 1.00]
  access_label_text: BLOCKED
  access_label_color_rgba8: [255, 0, 0, 255]
```

The mesh color and label must independently map to the same result. Missing,
duplicate, hidden, unregistered, invisible, non-finite, out-of-tolerance, or
cross-state surfaces produce `inconsistent`. Float color components use exact
binary values written by the proof adapter and are accepted only within an
absolute per-component tolerance of `0.000001`; the label values are exact.
These colors and labels are disposable representation facts, not canonical
topology or gameplay behavior.

### Independent observer path

One `ASimultaneousPhysicalRebindProbe`, created at initial process launch and
kept alive in the original process, consumes an exact inspection command on the
original stdin command stream:

```yaml
command_schema: SimultaneousPhysicalDomainInspectionInvocation.v1
proof_scenario: simultaneous-physical-domains-v1
domain_role: domain_A | domain_B
operation: inspect_published_route_once
inspection_id: launch_physical_0001 | refresh_physical_0001
```

The command contains no expected canonical hash, access state, color, label,
Actor identifier, receipt digest, projection value, or pass condition.
`inspection_id` labels the capture only and may not select the expected result.
The probe derives its role and exact probe tag only from the process binding,
enumerates the live UE world, and reads the matching Actor's live mesh material
parameter plus live text component state.

The probe must not receive or read the canonical payload, detached projection,
operation receipt, authoritative-derived representation JSON, materialization
receipt, refresh adapter candidate, retained local state, harness head
observation, or guard state. It shares no parsed-record object, candidate
object, receipt builder, or access-state variable with the adapter. Source
audit must establish this negative dataflow mechanically.

The exact observer result is:

```yaml
observation_schema: SimultaneousPhysicalDomainPhysicalObservation.v1
proof_scenario: simultaneous-physical-domains-v1
domain_role: domain_A | domain_B
operational_process_instance_id: OperationalInstanceId.v1
process_binding_raw_sha256: exact binding digest for this process instance
inspection_id: launch_physical_0001 | refresh_physical_0001
probe_tag: exact role-specific value
matching_live_actor_count: 1
actor_class: ASimultaneousPhysicalDomainRepresentationActor
actor_hidden_in_game: false
route_mesh_registered: true
route_mesh_visible: true
observed_route_mesh_color_parameter_rgba: exact four-number array
access_label_registered: true
access_label_visible: true
observed_access_label_text: AVAILABLE | BLOCKED
observed_access_label_color_rgba8: exact four-integer array
observed_physical_access_state: available | blocked | inconsistent
observation_source: live_ue_world_actor_component_inspection
```

The harness sends `launch_physical_0001` only after the H0 representation
receipt and requires `available` before accepting the initial synchronized-H0
disposition. It sends `refresh_physical_0001` only after the H1 representation
receipt and requires `blocked` before accepting a synchronized-H1 disposition.
The original process binding must match both observations. The harness compares
the live observation with its expected H0/H1 law without feeding that
expectation into the probe.

A missing or inconsistent observation, a receipt/observation disagreement, or
an H1 receipt paired with a live `available` surface fails the physical rebind
oracle. If this occurs after local H1 publication, the harness classifies the
domain `invalid`, halts its local execution, accepts no synchronized
disposition, and leaves canonical H1 unchanged.

## Required positive witnesses

### W1 — A then B refresh

```text
launch A from exact H0 + A/H0 projection
launch B from exact H0 + B/H0 projection
invoke each independent physical probe after its H0 representation receipt
observe actual live route state = available in original A and original B
prove L0: both original process bindings concurrently alive and harness-accepted synchronized to H0
close global physical-current-head guard
prove L1: both original process bindings still alive and head_unconfirmed
commit exact H0-to-H1 canonical transition independently
prove L2: both original process bindings alive before head publication
publish and independently reverify exact H1 operational observation
atomically classify both H0 domains stale and change guard to open_for_H1
prove L3: both original process bindings alive, stale against H1, and exact-H1 refresh-eligible
stage exact A/H1 three-file bundle and invoke refresh once on A's original stdin pipe
refresh A atomically to H1
invoke A's independent physical probe and observe actual live route state = blocked
prove L4A: original A harness-accepted synchronized / original B stale and both alive
stage exact B/H1 three-file bundle and invoke refresh once on B's original stdin pipe
refresh B atomically to H1
invoke B's independent physical probe and observe actual live route state = blocked
prove L4B: original A and B harness-accepted synchronized to H1 and both alive
```

### W2 — B then A refresh

Repeat W1 from fresh isolated proof roots and process instances, reversing only
the physical refresh order. The canonical R0, boundary, R1, ledger, ancestry,
and hashes must be byte-identical to W1. Both processes must satisfy the same
continuous birth-binding and pipe-continuity law. Each original process must
independently observe live `available` at H0 and live `blocked` after its H1
refresh; neither receipt nor authoritative-derived JSON can satisfy that
oracle.

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
bindings alive, both domains `head_unconfirmed`, the global physical guard
`failed_closed`,
refresh prohibited, all current-head claims/evidence/scheduling/mutation
disabled, and canonical H1 byte-identical to the primary witness.

### W5 — retained-local-state perturbation

Run the exact baseline/perturbed pair defined by the retention law. Require
byte-identical H1 authoritative-derived representation projections despite the
declared retained-scalar differences and poisoned discard-required H0 Actor,
cache, collision, and physics state. The independent live-UE oracle must also
observe `blocked` in both runs without consuming either projection object.

### W8 — guard-open protocol-invalid control

From fresh roots, accept both original processes as `synchronized(H0)` while
the guard is `open_for_H0`, deliberately omit the required closure, and invoke
the exact sealed canonical boundary/resolver. Require byte-identical committed
R1/H1, unchanged canonical ledger/ancestry, the guard's atomic transition to
`failed_closed`, and terminal `protocol_invalid(H0/H1)` dispositions for both
still-live processes. Neither process may be refreshed or accepted as current;
only diagnostics and termination may follow. The canonical call must have no
guard parameter, read, dependency, or rejection branch.

## Required asymmetric witness

The primary asymmetric failure is exact:

```text
H1 commits
→ exact H1 operational observation publishes and reverifies
→ both domains classify stale and the guard changes to open_for_H1
→ both original process bindings remain continuously alive
→ A's original stdin pipe receives its sole exact refresh invocation
→ A refresh reads the exact valid A/H1 three-file tuple and succeeds
→ A's independent physical probe observes the live route as blocked
→ B's original stdin pipe receives its sole exact refresh invocation
→ B refresh reads a B/H1 operation receipt whose payload raw digest does
  not match the supplied exact R1 bytes
→ B rejects before private candidate construction or local publication
→ H1 remains sole canonical authority
→ A is harness-accepted synchronized(H1)
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
19. exact canonical boundary invocation while the physical-current-head guard
    is open producing any result other than byte-identical committed R1 plus a
    failed Phase-3 harness-protocol witness, `failed_closed` guard, and terminal
    `protocol_invalid(H0/H1)` dispositions;
20. missing, stale-H0, malformed, mismatched, or unverified operational head
    observation reopening current-head or refresh eligibility after H1;
21. publication failure after H1 followed by any domain state other than
    `head_unconfirmed`, any guard state other than `failed_closed`, or any
    enabled current-head path;
22. harness delivery of a refresh invocation while current-head observation is
    unproven followed by acceptance of any resulting receipt as current;
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
    FIFO, socket, shared directory, alternate pipe, or second refresh
    invocation;
28. refresh bundle with any missing, additional, redirected, non-regular,
    cross-domain, mutable, or wrong-role visible input reaching candidate
    construction;
29. any path, bytes, digest, existence flag, validity flag, or classification
    derived from `current_head_observation.json` reaching Unreal;
30. guard or head-observation state read by the sealed Phase-1 scheduler,
    resolver, transaction, serializer, ledger, ancestry, or hash path;
31. structurally correct H1 JSON and representation receipt accepted as a
    successful rebind without an independent live `blocked` observation;
32. the physical probe deriving its result from canonical/projection JSON,
    adapter candidate state, materialization receipt, expected outcome, or a
    shared access-state variable instead of live Actor components;
33. H1 receipt paired with missing, duplicate, hidden, invisible,
    unregistered, `available`, or inconsistent live route surfaces; and
34. an inspection command containing an expected hash, access state, color,
    label, Actor identity, receipt digest, or pass condition;
35. a synchronized disposition with its guard closed, failed, or open for a
    different head, or with either receipt/oracle prerequisite absent;
36. a non-synchronized disposition enabling a current-head representation
    claim, or any disposition treating that claim as canonical authority; and
37. argv, environment, cwd, inherited descriptor, executable/project input,
    engine/system dependency, project content, or runtime-opened channel outside
    the declared proof-semantic closure affecting Phase-3 semantics or result.

No case may create or alter a canonical mutation. Case 19 must still commit the
exact sealed R1/H1 and fails only the Phase-3 physical harness protocol; the
canonical result is not rejected or rolled back, both affected domains are
terminal `protocol_invalid`, and the guard is `failed_closed`. All other
adversaries leave
canonical history unchanged beyond any already committed exact H1. Cases
involving a malformed physical refresh leave the domain stale if no local
publication occurred and make it invalid if atomic publication or the
independent physical oracle can no longer be proven.

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
  - after_physical_guard_close_before_canonical_invocation
  - after_R1_H1_commit_verification_before_observation_construction
  - after_observation_construction_before_temporary_write
  - after_temporary_write_before_file_fsync
  - after_file_fsync_before_atomic_replace
  - after_atomic_replace_before_directory_fsync
  - after_directory_fsync_before_independent_reread
  - after_independent_reread_before_identity_reverification
  - after_identity_reverification_before_refresh_eligibility
```

At every point the global physical-current-head guard remains
`closed_for_H0_to_H1` until exact H1 has been independently reread and
reverified, every affected H0 domain has been classified stale, and the one
atomic transition to `open_for_H1` completes. A candidate or even atomically
replaced observation file is not sufficient by its mere existence. Any missing
completion witness changes the guard to terminal `failed_closed`, leaves all
affected domains `head_unconfirmed`, and disables current-head claim/receipt
acceptance and refresh. Evidence, scheduling, and mutation paths remain
independently prohibited. None of these fault points may block, alter, or roll
back the sealed canonical transaction; even the pre-invocation injected branch
must continue through the exact canonical call independently of physical
protocol failure.

The required injected witness uses
`after_R1_H1_commit_verification_before_observation_construction`. H1 is already
durable canonical truth; the operational observation is absent and cannot
substitute H0 or an expected H1. No observer fault mutates either canonical
record.

### Physical refresh fault surface

The exact refresh stages frozen for mandatory pre/post fault injection during the later authorized implementation/evidence phase are:

```yaml
refresh_fault_stages:
  - invocation_read
  - visible_input_inventory
  - payload_raw_byte_verification
  - payload_parse_and_canonical_identity_verification
  - operation_receipt_verification
  - projection_verification
  - visible_command_bundle_cross_field_verification
  - process_binding_identity_verification
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

### Independent physical-observation fault surface

The exact post-publication observer stages are:

```yaml
physical_observation_fault_stages:
  - inspection_invocation_read
  - immutable_process_binding_verification
  - role_probe_tag_derivation
  - live_world_actor_enumeration
  - exact_actor_count_check
  - live_mesh_component_lookup
  - live_mesh_visibility_and_material_parameter_read
  - live_label_component_lookup
  - live_label_visibility_text_and_color_read
  - independent_surface_consistency_classification
  - physical_observation_emission
  - harness_receipt_observation_head_cross_check
```

The probe receives no expected state at any stage. A fault or mismatch at H0
prevents initial synchronized acceptance and the primary witness does not
advance. A fault or mismatch after local H1 publication makes the domain
invalid and halted; no synchronized-H1 disposition is accepted. Neither case
changes canonical bytes or grants the representation authority.

### Liveness failure surface

Continuous child-handle, process-start, and pipe monitoring runs independently
of refresh. An exit, wait status, unexpected EOF, binding change, or replacement
spawn at any point from L0 through L4B fails uninterrupted liveness. If H1 is
already committed, H1 remains sole authority and the affected domain cannot
publish a current-head claim. No restart may repair that witness.

No head observer, physical observer, refresh, retention, or liveness fault
changes canonical H1 or the other domain's already valid detached state.

## Provenance and replay

Detached proof evidence must record:

- exact sealed R0/R1 paths, raw hashes, and canonical hashes;
- the exact H0-bound canonical boundary and byte-identical R1 reproduction;
- process-root inventories and realpaths;
- process-birth bindings, continuous child-handle/pipe monitors, exact L0–L4B
  samples, and two-launch/no-replacement audits;
- global physical-current-head guard transitions, the guard-open canonical
  control, exact operational head-observation bytes, publication/reread
  witnesses, and the injected post-commit publication failure;
- per-domain launch and refresh input inventories;
- the exact proof-semantic input closure, complete launch-surface audits,
  executable/project/runtime dependency identities, all
  binding/inspection/refresh standard-input bytes, and original pipe bindings;
- per-domain projection and operation-receipt hashes;
- successful materialization receipts;
- independent live-UE H0 `available` and H1 `blocked` observations, including
  raw mesh and label surfaces and receipt-independent oracle results;
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
5. domain head state, operational observation, physical guard, process
   identity, liveness, refresh state, Actor state, cache, collision, physics,
   retained scalars, and diagnostics do not dataflow into canonical execution;
6. the physical-current-head guard has no parameter, read, call, import,
   callback, capability, lock, branch, exception, or data dependency in the
   sealed Phase-1 boundary discovery/resolver/commit path, and the guard-open
   control still commits byte-identical R1/H1;
7. the operational head observer reads only complete committed canonical bytes
   and cannot write, select, repair, delay, or roll back canonical head;
8. the head-observation file/control root and every value derived from it are
   absent from Unreal arguments, environment, inherited descriptors, roots,
   files, commands, process bindings, projections, receipts, shared objects,
   and adapter/probe dataflow;
9. static call-graph/dataflow audit plus runtime input inventory proves the
   refresh adapter reads only its exact stored process binding, refresh command,
   and three visible bundle files; it performs no head-observation check;
10. the launch audit records exact ordered argv, redacted complete environment,
    cwd, inherited descriptor map, executable/project/config/module hashes, and
    engine/system loaded-image inventory for each process, with no other-domain,
    head-observation, guard, expected-result, or proof-selector value;
11. the command router's one-time binding verification is the only application
    environment/argv/cwd/descriptor inspection; after binding, the adapter and
    probe have no environment read, command-line selector, cwd branch, project
    Content/ProofRecords read, alternate file-open, dynamic library lookup, or
    alternate descriptor read capable of affecting proof semantics;
12. every file-open and input read reachable from the Phase-3 adapter, router,
    representation Actor, or probe is in the exact proof-semantic closure, and
    runtime file/descriptor tracing agrees with that static allowlist;
13. head-unconfirmed and stale local execution have no outward current-head
   evidence, scheduling, mutation, or truth-publication path;
14. the authoritative-derived H1 representation constructor has exactly two
    inputs: exact H1 and the exact role/H1 projection;
15. only the exact three-field retained-local-state projection may cross
    refresh, and it cannot reach the authoritative-derived constructor;
16. stale Actor, cache, collision, physics, receipt, capability, and H0-derived
    representation state is discarded before H1 publication;
17. refresh is private until one complete local publication point;
18. the only refresh invocation is one exact line on each original stdin pipe,
    and each fixed role-specific visible-input directory has exactly three
    regular read-only members;
19. the representation receipt carries no current-head or harness-head field,
    and only the harness emits the detached head disposition;
20. the independent physical probe reads only the immutable process binding,
    inspection command, and live UE world Actor/components, with no adapter
    record/candidate/receipt pointer, canonical/projection input, shared access
    variable, or expected-state input;
21. both original processes produce receipt-independent live `available` H0
    and live `blocked` H1 observations before synchronized dispositions;
22. original child handles, macOS process-start pairs, birth bindings, and pipe
    endpoints remain continuous from L0 through L4B with no replacement spawn;
23. one domain cannot read or select from the other's proof root or local state;
24. process, local-state perturbation, and refresh order cannot select canonical
    or materialized access truth; and
25. synchronized representation-claim permission is true only for an exact
    matching open guard plus accepted receipt and independent live observation;
    it never enables canonical evidence, scheduling, mutation, truth, or head
    selection; and
26. no occupancy, movement, networking, streaming, World Partition, player,
    or production abstraction is introduced under the proof fixture.

## Exact release artifact DAG and self-excluding manifest

This frozen specification fixes the implementation, evidence, and later
release boundary. The names below are exact contract members; authority extends
only to the mutable paths and bounded existing-source branch declared below.

The review-time document validator is exactly
`proof_kernel/validate_simultaneous_physical_domains_spec.py`. It checks this
specification's state/disposition alignment, guard laws, proof-semantic input closure,
44 artifact names, and 110 unique self-excluding manifest members. It is
specification QA only: it does not import or execute a Phase-3 runtime, produce
proof evidence, or belong to the 44-member
artifact directory, 110-member release manifest, or release DAG. The authorized
prospective release verifier is the frozen
`proof_kernel/verify_simultaneous_physical_domains_release.py` member.

Its default mode validates the active document. Its `--self-test` mode operates
only on in-memory copies of the same document and must prove that missing,
extra, duplicate, reordered, contradictory, granted, altered, and self-included
contract mutations are rejected without writing a file.

### Exact evidence artifact members

The authorized implementation must populate exactly one directory:

`proof_kernel/SimultaneousPhysicalDomainsProofRecords/`

That directory must contain exactly these 44 regular files and no others:

```yaml
artifact_names:
  - simultaneous_physical_domains_canonical_transition_run.json
  - simultaneous_physical_domains_projection_matrix.json
  - simultaneous_physical_domains_operation_receipt_matrix.json
  - simultaneous_physical_domains_current_head_observation.json
  - simultaneous_physical_domains_head_observation_fault_atomicity.json
  - simultaneous_physical_domains_guard_open_canonical_control.json
  - physical_W1_domain_A_H0_materialization_receipt.json
  - physical_W1_domain_A_H0_observation.json
  - physical_W1_domain_B_H0_materialization_receipt.json
  - physical_W1_domain_B_H0_observation.json
  - physical_W1_domain_A_H1_materialization_receipt.json
  - physical_W1_domain_A_H1_observation.json
  - physical_W1_domain_B_H1_materialization_receipt.json
  - physical_W1_domain_B_H1_observation.json
  - physical_W1_liveness_witness.json
  - physical_W1_a_then_b_witness.json
  - physical_W2_domain_A_H0_materialization_receipt.json
  - physical_W2_domain_A_H0_observation.json
  - physical_W2_domain_B_H0_materialization_receipt.json
  - physical_W2_domain_B_H0_observation.json
  - physical_W2_domain_B_H1_materialization_receipt.json
  - physical_W2_domain_B_H1_observation.json
  - physical_W2_domain_A_H1_materialization_receipt.json
  - physical_W2_domain_A_H1_observation.json
  - physical_W2_liveness_witness.json
  - physical_W2_b_then_a_witness.json
  - physical_W3_stale_quarantine_witness.json
  - physical_W4_head_observation_failure_witness.json
  - physical_W5_retention_baseline_witness.json
  - physical_W5_retention_perturbed_witness.json
  - physical_W5_retention_equivalence_oracle.json
  - physical_W6_asymmetric_A_synchronized_witness.json
  - physical_W6_asymmetric_B_synchronized_witness.json
  - physical_W7_destroy_A_witness.json
  - physical_W7_destroy_B_witness.json
  - simultaneous_physical_domains_current_head_authority_failures.json
  - simultaneous_physical_domains_refresh_fault_atomicity.json
  - simultaneous_physical_domains_physical_observation_fault_atomicity.json
  - simultaneous_physical_domains_proof_semantic_input_audit.json
  - simultaneous_physical_domains_physical_rebind_oracle.json
  - simultaneous_physical_domains_canonical_equivalence_oracle.json
  - simultaneous_physical_domains_source_audit.json
  - simultaneous_physical_domains_replay_oracle.json
  - simultaneous_physical_domains_proof_run.json
```

Per-domain input inventories, binding commands, inspection commands, refresh
commands, process-birth samples, pipe continuity, disposition receipts, fault
results, and source-audit facts must be embedded under their exact witness or
oracle member above. No additional log, screenshot, receipt, cache dump,
temporary file, or optional evidence member may be added to the release
directory. Runtime scratch output remains outside it and is not release
evidence.

### Exact role DAG

```text
sealed Phase-1 R0/H0 + exact H0-bound boundary
        ↓
existing sealed Phase-1 resolver only
        ↓
byte-identical R1/H1 + canonical-transition artifact

exact A/B projection + operation-receipt matrices
        ↓
two suspended direct-child launches + exact binding commands
        ↓
H0 representation receipts + independent live available observations
        ↓
L0 → open_for_H0 changes to closed_for_H0_to_H1 → L1
        ├─ canonical path: exact resolver commit, guard unreadable → L2
        └─ guard-open control: exact resolver still commits R1
             → failed_closed + terminal protocol_invalid dispositions
        ↓
harness-private H1 observation / publication fault branch
        ↓
atomic stale classifications + open_for_H1
        ↓
exact isolated H1 bundles + sole refresh commands
        ↓
W1 A→B and W2 B→A representation receipts
        ↓
independent live blocked observations in the same original processes
        ↓
L4A / L4B synchronized dispositions
        ↓
stale, retention, asymmetric, destruction, authority, and fault witnesses
        ↓
physical-rebind + canonical-equivalence + source-audit + replay oracles
        ↓
proof run + evidence document
        ↓
self-excluding exact-member SHA-256 manifest
        ↓
release verifier checks the exact set, hashes, DAG relations, and all semantics
```

No node outside this DAG is part of the proof. In particular, the private head
observation has no edge into Unreal, and the physical guard has no edge into
the canonical path.

### Exact source and governing member set

The manifest member set is the union of the exact 44 artifact paths above and
the following exact relative paths: 110 manifest entries total, excluding the
manifest itself.

```yaml
governing_and_predecessor_members:
  - README.md
  - Resolution Semantics Law - v0.1.1.md
  - Record-Relative Chronological Resolution Proof Evidence - v0.1.0.md
  - Integrated Unreal Promotion-Unload-Repromotion Proof Evidence - v0.1.0.md
  - Concurrent External Evidence Arbitration Proof Evidence - v0.1.0.md
  - Canonical Spatial Topology Identity Proof - Draft.md
  - Canonical Spatial Topology Identity Proof Evidence - v0.1.0.md
  - Canonical Spatial Topology Identity Proof - v0.1.0 SHA256SUMS.txt
  - Canonical Occupancy Transition Proof Evidence - v0.1.0.md
  - Simultaneous Physical Domains Proof - Draft.md
  - Simultaneous Physical Domains Proof Evidence - v0.1.0.md
  - Co-op Open-City FPS Simulation - v0.7 Working Continuation.md
  - THE_CITY Development Capacity and Progress Note - v0.1.11.md
  - THE_CITY Developer Snapshot - v0.1.0.md
  - THE_CITY Current Proof State and Repo-Agent Instruction - v0.1.0.md

sealed_canonical_input_members:
  - proof_kernel/CanonicalSpatialTopologyIdentityProofRecords/canonical_topology_R0.json
  - proof_kernel/CanonicalSpatialTopologyIdentityProofRecords/canonical_topology_boundary_H0.json
  - proof_kernel/CanonicalSpatialTopologyIdentityProofRecords/canonical_topology_R1.json

python_source_members:
  - proof_kernel/kernel.py
  - proof_kernel/canonical_spatial_topology_identity.py
  - proof_kernel/simultaneous_physical_domains.py
  - proof_kernel/simultaneous_physical_domains_harness.py
  - proof_kernel/test_simultaneous_physical_domains.py
  - proof_kernel/verify_simultaneous_physical_domains_release.py

unreal_project_members:
  - CityMaterializationProof/CityMaterializationProof.uproject
  - CityMaterializationProof/Config/DefaultEngine.ini
  - CityMaterializationProof/Config/DefaultGame.ini
  - CityMaterializationProof/Config/DefaultInput.ini
  - CityMaterializationProof/README.md
  - CityMaterializationProof/Source/CityMaterializationProof.Target.cs
  - CityMaterializationProof/Source/CityMaterializationProofEditor.Target.cs
  - CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationProof.Build.cs
  - CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationProof.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationProof.h
  - CityMaterializationProof/Source/CityMaterializationProof/CityProofGameMode.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/CityProofGameMode.h
  - CityMaterializationProof/Source/CityMaterializationProof/BridgeAccessPoint.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/BridgeAccessPoint.h
  - CityMaterializationProof/Source/CityMaterializationProof/CanonicalSpatialTopologyProofAdapter.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/CanonicalSpatialTopologyProofAdapter.h
  - CityMaterializationProof/Source/CityMaterializationProof/CanonicalTopologyRepresentationActor.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/CanonicalTopologyRepresentationActor.h
  - CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationActor.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/CityMaterializationActor.h
  - CityMaterializationProof/Source/CityMaterializationProof/CityProofCharacter.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/CityProofCharacter.h
  - CityMaterializationProof/Source/CityMaterializationProof/ConcurrentEvidenceSurface.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/ConcurrentEvidenceSurface.h
  - CityMaterializationProof/Source/CityMaterializationProof/ConcurrentExternalEvidenceProofAdapter.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/ConcurrentExternalEvidenceProofAdapter.h
  - CityMaterializationProof/Source/CityMaterializationProof/CrewOperationPoint.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/CrewOperationPoint.h
  - CityMaterializationProof/Source/CityMaterializationProof/IntegratedGateTokenPoint.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/IntegratedGateTokenPoint.h
  - CityMaterializationProof/Source/CityMaterializationProof/IntegratedUnrealProofAdapter.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/IntegratedUnrealProofAdapter.h
  - CityMaterializationProof/Source/CityMaterializationProof/LiveCommitmentRelayPoint.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/LiveCommitmentRelayPoint.h
  - CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainCommandRouter.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainCommandRouter.h
  - CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainProofAdapter.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainProofAdapter.h
  - CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainRepresentationActor.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainRepresentationActor.h
  - CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalRebindProbe.cpp
  - CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalRebindProbe.h
```

The exact bounded implementation surface is:

```yaml
frozen_implementation_authority:
  new_python_paths:
    - proof_kernel/simultaneous_physical_domains.py
    - proof_kernel/simultaneous_physical_domains_harness.py
    - proof_kernel/test_simultaneous_physical_domains.py
    - proof_kernel/verify_simultaneous_physical_domains_release.py
  new_unreal_paths:
    - CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainCommandRouter.cpp
    - CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainCommandRouter.h
    - CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainProofAdapter.cpp
    - CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainProofAdapter.h
    - CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainRepresentationActor.cpp
    - CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalDomainRepresentationActor.h
    - CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalRebindProbe.cpp
    - CityMaterializationProof/Source/CityMaterializationProof/SimultaneousPhysicalRebindProbe.h
  bounded_existing_source_change:
    path: CityMaterializationProof/Source/CityMaterializationProof/CityProofGameMode.cpp
    scope: phase_3_dispatch_branch_only
  evidence_path: Simultaneous Physical Domains Proof Evidence - v0.1.0.md
  artifact_directory: proof_kernel/SimultaneousPhysicalDomainsProofRecords/
  artifact_member_count: 44
  manifest_path: Simultaneous Physical Domains Proof - v0.1.0 SHA256SUMS.txt
  manifest_member_count_excluding_manifest: 110
  governing_document_changes: implementation_evidence_and_seal_records_only
  all_other_existing_source_project_config_paths: hash_bound_unchanged
  capacity_advancement: none
```

Only those four new Python paths, eight new `SimultaneousPhysical*` Unreal
paths, the bounded Phase-3 dispatch branch in `CityProofGameMode.cpp`, the one
evidence document, exact 44-member artifact directory, and self-excluding
manifest are authorized. Every other existing source/project/config member
above is a hash-bound dependency and must remain unchanged. Governing documents
may change only to record implementation, evidence, and seal; any capacity
decision requires separate review. The non-release document validator is
frozen QA code and is not implementation authority. Any other created or
modified source path requires a return to specification review and a revised
exact member set.

### Self-excluding manifest contract

The eventual manifest path is exactly:

`Simultaneous Physical Domains Proof - v0.1.0 SHA256SUMS.txt`

It must exclude itself. Its 110 member lines must be the complete union above,
sorted by raw UTF-8 relative-path bytes, each encoded exactly as lowercase
64-hex SHA-256, two ASCII spaces, the repository-relative path, and LF. Every
member must be one regular non-symlink file whose realpath remains beneath the
repository root. Hashes are written only after every member is final.

The release verifier carries the same frozen ordered path list in source and
must reject a missing, additional, duplicated, reordered, absolute,
parent-traversing, non-regular, symlinked, unreadable, or checksum-mismatched
member. It must also reject any additional member in the exact artifact
directory, regenerate the 44 artifact roles in an isolated temporary root,
recompute canonical artifacts byte-for-byte, validate operational artifacts by
their frozen semantic relations, rerun the complete proof tests, and reperform
the source/dataflow audits rather than trust checked-in pass booleans. Manifest
verification is an exit gate only; it grants no successor or production
authority.

The manifest proves the exact release commit, not every later working-tree
amendment. After a seal, any continuation, README, snapshot, or handover change
must not rewrite the historical manifest. Historical verification must export
or check out the recorded seal commit into an isolated root and run that
commit's verifier there. A live-tree mismatch caused solely by later governing-
document advancement is not proof failure; substituting current files into the
sealed member set or regenerating the historical manifest is forbidden.

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

## Frozen acceptance contract

Freeze review accepted the following exact contract:

```yaml
freeze_acceptance:
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
  proof_semantic_input_closure: exact_and_head_observation_free
  argv_environment_cwd_descriptor_audit: exact
  executable_project_and_runtime_dependency_audit: exact
  unreal_head_observation_dependency: prohibited
  current_head_observer_schema: exact
  physical_current_head_guard_scope: claims_receipt_acceptance_and_refresh_only
  physical_guard_dataflow_into_canonical_execution: prohibited
  guard_open_canonical_control: exact_R1_commit_failed_closed_and_terminal_protocol_invalid
  normal_guard_reopening: only_after_exact_H1_reverification_and_all_stale_classifications
  current_head_guard_and_publication_order: exact_physical_protocol
  current_head_observation_failure_atomicity: exact_nine_fault_points
  post_commit_prepublication_failure_witness: exact
  physical_head_state_machine: exhaustive
  synchronized_claim_disposition_alignment: exact_representation_only
  head_unconfirmed_state: exact
  stale_local_execution_law: exact
  invalid_state_and_halt_law: exact
  authoritative_derived_reconstruction_inputs: exact_H1_plus_projection_only
  retained_local_state_schema: exact_three_fields
  actor_cache_collision_physics_retention: prohibited
  retention_perturbation_witness: exact
  physical_refresh_publication_boundary: exact
  independent_live_UE_physical_rebind_oracle: exact
  H0_physical_observation: available_in_both_original_processes
  H1_physical_observation: blocked_in_both_original_processes
  physical_probe_receipt_and_JSON_independence: source_audited
  asymmetric_witnesses: exact_and_symmetric
  current_head_authority_failures: exhaustive
  failure_atomicity: fault_points_frozen
  domain_isolation: exact
  canonical_equivalence: exact
  provenance_and_replay: exact
  source_audit: exact
  release_artifact_DAG: exact
  release_artifact_directory_members: exact_44
  release_source_and_governing_members: exhaustive
  release_manifest: exact_self_excluding_and_mechanically_verified
  review_time_document_validator: structurally_exact_passing_and_non_release
  review_time_validator_self_tests: exact_adversarial_mutations_all_rejected
  post_seal_verification: exact_recorded_seal_commit_export
  exclusions: exact
```

Freeze review accepted the exact non-release document validator, including its
structural authority blocks, guard/state/disposition structures, permission
matrix, proof-semantic closure, launch surface, lifecycle wording, artifact
set, manifest member set, and adversarial in-memory rejection tests. The frozen
contract retains draft.3's physical guard, claim, input-closure, live-UE oracle,
and exact 44/110 release boundary without claiming runtime evidence.

The authorized implementation must fail review for any hidden head-observation
input, canonical dependency on the physical guard, receipt-only physical
acceptance, non-independent probe, optional release member, alternate
projection or refresh channel, ambiguous head-unconfirmed/stale/invalid/
protocol-invalid disposition, misaligned synchronized claim permission, hidden
proof-semantic process input, retained authoritative-derived H0 state,
replaceable process identity, or unspecified local publication boundary.

## Frozen acceptance statement

If the authorized implementation passes every required gate, it may establish
only:

> **Two process-isolated Unreal representation domains can remain
> simultaneously alive while one exact canonical topology record advances
> independently from H0 to H1. Each live process can rebind through an exact
> detached projection to the same H1, while any process still representing H0
> is mechanically stale, may continue only quarantined nonconsequential local
> execution, and cannot exercise current-head evidence, scheduling, mutation,
> or truth authority. Failure to prove operational observation of committed H1
> closes every physical current-head path rather than creating another head;
> that observation never enters Unreal; the physical guard cannot affect the
> canonical transaction; refresh reconstructs every authoritative-derived fact
> solely from H1 plus the exact projection; independent live-UE component
> inspection observes available at H0 and blocked after H1 in both original
> processes; and uninterrupted process-birth evidence proves neither physical
> domain exited or was replaced across the commit.**

It may not establish multiplayer, networking, occupancy materialization,
movement, streaming, or production physical-domain architecture.

## Specification and draft review history

### 0.1.0 — 2026-08-28

- Accepted the corrected refresh-fault lifecycle wording and the validator's
  rejection of old or equivalent pre-freeze runtime obligations.
- Froze `Simultaneous Physical Domains Proof v0.1.0` under
  `SimultaneousPhysicalDomainsProof.v1` / `0.7.0-draft.72`.
- Authorized only the exact four Python paths, eight Unreal paths, bounded
  `CityProofGameMode.cpp` dispatch branch, evidence path, 44-member artifact
  directory, and self-excluding 110-member manifest declared above.
- Kept evidence unsealed, capacity at v0.1.11, and every production or adjacent
  scope unauthorized.

### 0.1.0-draft.4 — 2026-08-28

- Replaced presence-only document checks with exact structural authority-block
  parsing and exact ordered block/list identities for the head-state table,
  four-state guard, disposition, permission matrix, proof-semantic closure,
  launch surface, 44 artifacts, and 66 non-artifact manifest members.
- Added `--self-test` in-memory adversaries for missing, extra, duplicate, or
  reordered guard/authority/input/list structure, contradictory or granted
  implementation authority, a falsely frozen Phase-3 state, altered permission
  rows, validator/manifest self-inclusion, and pre-freeze runtime-obligation
  wording.
- Bound mandatory refresh fault injection to the later authorized
  implementation/evidence phase.
- Named the review-time document validator as the sole pre-freeze QA-code
  exception while keeping every Phase-3 runtime, Unreal, proof, test, evidence,
  artifact, and release implementation prohibited.
- Kept final freeze review open, the proof unfrozen, capacity unchanged, and
  implementation authority `none`.

### 0.1.0-draft.3 — 2026-08-28

- Defined `open_for_H0`, `closed_for_H0_to_H1`, `open_for_H1`, and
  `failed_closed` guard states, the exact normal H1 reopening point, and a
  terminal `protocol_invalid` disposition for the guard-open control while the
  canonical resolver still commits byte-identical R1/H1.
- Aligned synchronized current-head representation-claim permission across the
  head state, guard, disposition schema, permission matrix, witnesses, and
  rejection cases without granting canonical authority.
- Replaced the impossible all-process-context assertion with an exact
  proof-semantic input closure and complete audits of argv, environment, cwd,
  descriptors, executable/project/module inputs, bundle files, and runtime
  dependencies.
- Added the non-release specification validator for the state/disposition law,
  prohibited hidden inputs, 44 exact artifacts, and 110 unique self-excluding
  manifest members.
- Kept final freeze review open, the proof unfrozen, and implementation
  authority `none`.

### 0.1.0-draft.2 — 2026-08-28

- Removed all private head-observation inputs and checks from the Unreal
  adapter/probe boundary and declared a narrower adapter/probe input contract;
  draft.3 corrects its overbroad process-visibility wording.
- Restricted the physical-current-head guard to physical claim/receipt
  acceptance and refresh eligibility, with an exact guard-open control proving
  the sealed Phase-1 resolver still commits byte-identical R1/H1.
- Added exact independent live-UE mesh/label observations of `available` at H0
  and `blocked` after H1 refresh in each original process, plus failure
  atomicity and source-audit independence from receipt/JSON paths.
- Fixed the exact release DAG, 44-member artifact directory, complete
  source/governing member set, and self-excluding manifest/verifier contract.
- Advanced to final freeze review without freezing the proof or granting code,
  Unreal, capacity, or successor authority.

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
working_unit: Simultaneous Physical Domains Proof v0.1.0 bounded implementation
successor_selected: true
specification_status: frozen
freeze_status: frozen
implementation_authority: bounded_phase_3_proof_only
canonical_capacity_change: none
evidence_status: unsealed
latest_sealed_capacity: THE_CITY Development Capacity and Progress Note v0.1.11
```

The specification is frozen. Implementation authority is limited to the exact
Phase-3 proof paths and bounded dispatch branch declared by this contract. It
permits the named proof implementation, Unreal adapter, harness, tests,
evidence, artifacts, and release verification only. It grants no capacity
advancement, production architecture, or adjacent spatial scope.
