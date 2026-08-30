# Cross-Domain Canonical Occupancy Materialization Proof Evidence

**Version:** 0.1.0
**Date:** 2026-08-29
**Status:** Passed release candidate; independent implementation review pending.
**Specification:** [Cross-Domain Canonical Occupancy Materialization Proof v0.1.0](Cross-Domain%20Canonical%20Occupancy%20Materialization%20Proof%20-%20Draft.md)
**Frozen specification SHA-256:** `47889ac299cf2cfbea143a6a529b1253826e74ae9ddc83f0b25903117ff9406d`
**Proof harness identity:** `CrossDomainCanonicalOccupancyMaterializationProof.v1` / `0.7.0-draft.80`

## Claim tested

> Can the exact sealed Phase-2 `R0 → Rtransit → Rfinal` canonical occupancy
> chain be represented across the same two original, simultaneously live
> Phase-3 Unreal domains while canonical records remain the sole authority for
> occupancy, transition, chronology, and completion?

The bounded candidate passes this claim. Four refresh-order witnesses used two
original direct-child UE 5.8 processes each. Both processes remained bound to
their exact PID, macOS birth tuple, executable, process root, argv,
environment audit, descriptor map, project identity, and launch plan across
two independently committed canonical successors and two physical refresh
cycles. Neither Unreal process received a canonical completion source or a
canonical mutation path.

This record does not seal itself. The generated proof-run artifact retains
`evidence_status: unsealed`; the exact implementation/release commit must be
submitted to independent review before any later forward seal decision.

## Canonical authority and exact chain

The candidate imports the five exact sealed Phase-2 records and boundaries.
It invokes only the sealed Phase-2 scheduler and resolver. Physical state,
refresh order, Actor presence, receipts, observations, guards, and
dispositions are never inputs to either canonical function.

```yaml
R0:
  record_canonical_hash: b31e7ad0993e288ba80f50fb1960da5c67bad9bcc7cc39bf0ec0ebeeaad57dc8
  record_raw_sha256: 59ce47bc4d6c63cbda4a740fec8d25e497ca8ed74052b16b5358745be115c2dc
  occupancy: topology_occupant_0001 at topology_site_0002
  reservation: available
Rtransit:
  record_canonical_hash: 2640fe567b343e2229f875c9cf2d081f41aaaec2a3834e81e2efb3f9caa5da19
  record_raw_sha256: 215e3383bff21a9fe01dbb240035a0fa5dd774c703417486846e027a0615a12f
  occupancy: topology_occupant_0001 in occupancy_transition_0001
  reservation: reserved by occupancy_transition_0001
Rfinal:
  record_canonical_hash: 3a00d32115af74950923ac3362a8459d0e08043d45abbe91bcc573e27103db34
  record_raw_sha256: 0b4d9d97eb166b3aae6480c5581654c39b367c3a5fab47a02daec50b1e88a181
  occupancy: topology_occupant_0001 at topology_site_0001
  reservation: available
completion_rediscovered_from_Rtransit: true
physical_input_to_scheduler_or_resolver: false
```

All W1–W4 canonical objects are byte-identical despite distinct physical
refresh orders:

```text
W1: Rtransit A→B; Rfinal A→B
W2: Rtransit B→A; Rfinal B→A
W3: Rtransit A→B; Rfinal B→A
W4: Rtransit B→A; Rfinal A→B
```

## Live Unreal materialization

Each accepted generation is established through four separate surfaces:

1. an expectation independently derived from exact canonical payload bytes and
   one of six detached byte-bound projections;
2. an Unreal materialization receipt bound to the exact operation tuple and
   immutable 22-field process binding;
3. an independent exhaustive live-world Actor census that consumes neither
   the receipt nor the expected JSON; and
4. a harness-private canonical-head observation and fail-closed disposition.

The positive live census is exact:

| Canonical role | Domain A | Domain B |
| --- | --- | --- |
| `R0` | one anchor, zero subjects | one anchor, one subject |
| `Rtransit` | one anchor, zero subjects | one anchor, zero subjects |
| `Rfinal` | one anchor, one subject | one anchor, zero subjects |

The `Rtransit` row is positive zero-subject evidence from both complete live
censuses. It is not inferred from an empty query, a receipt, a transform, route
presence, or elapsed time. The subject is represented at neither endpoint
while canonical occupancy is `in_transition`.

Every successful refresh publishes one complete target generation before the
predecessor generation is removed, verifies the exact live census, and then
permits a synchronized representation-only disposition. No partial generation
may claim current-head representation.

## Controls, adversaries, and atomicity

The complete frozen executable matrix passed:

```yaml
primary_refresh_order_witnesses: 4/4
canonical_independence_and_guard_controls: 6/6
asymmetric_peer_failures: 4/4
process_binding_adversaries: 23/23_rejected
authority_cases: 40/40
authority_subcases: 121/121_rejected
head_publication_faults: 18/18_fail_closed
materialization_faults: 138/138_fail_closed
live_observation_faults: 36/36_fail_closed
liveness_adversaries: 6/6_fail_closed
canonical_rollback_or_rewrite: none
```

The authority rows preserve both the underlying mechanical rejection and the
actual frozen authority-boundary stage/reason. Every subcase measures the
complete canonical chain before and after and rejects any physical attempt to
construct, select, delay, publish, or complete a canonical successor.

Materialization cases cover all 23 compiled M stages in all three frozen
contexts at both `before` and `after` edges. Observation cases cover all 12 O
stages in three contexts. Head-publication cases cover all nine harness stages
for both canonical boundaries. Liveness cases separately detect original-child
exit, wait status, reported birth mismatch, control-pipe closure,
structured-output EOF, and a copied-label replacement process.

## Provenance and closed occurrence registry

The release retains complete launch, command, bundle, runtime trace,
harness-trace, receipt, observation, census, disposition, termination, loaded
image, initial Actor-class, and source-audit evidence. The exact occurrence
registry independently reconstructs every process identity and rejects reuse
across occurrences.

```yaml
registered_occurrences: 364
registered_unique_unreal_processes: 457
primary_processes: 8
fresh_replay_processes: 8
alternate_proof_semantic_channels: 0
```

The function-scoped source/dataflow audit passes 30/30 checks and rejects all
18 declared source mutations. It binds the exact bytes of the four Python and
eleven relevant Unreal/GameMode translation units, inventories every admitted
input and publication surface, and confirms that physical values cannot reach
the Phase-2 scheduler, resolver, record construction, canonical hashing, or
successor publication paths.

## Verification, replay, build, and release

```yaml
focused_phase_4_contracts: 45/45
predecessor_regressions: 215/215
phase_2_isolated_seal_export: 33/33
phase_3_isolated_seal_export: 111/111
phase_3_verifier_adversaries: 41/41_rejected
specification_validator: 20/20
specification_validator_adversaries: 32/32_rejected
source_checks: 30/30
source_mutations: 18/18_rejected
fresh_replay_witnesses: 4/4
ue_version: 5.8.0-55116800+++UE5+Release-5.8
ue_editor_build: succeeded_with_DisableUnity_and_NoHotReloadFromIDE
artifact_roles: 82/82
release_members_excluding_manifest: 172/172
release_verifier_adversaries: 30/30_rejected
manifest_self_excluding: true
capacity_advancement: none
phase_5: closed
```

The UE build command was:

```sh
'/Users/Shared/Epic Games/UE_5.8/Engine/Build/BatchFiles/Mac/Build.sh' \
  CityMaterializationProofEditor Mac Development \
  '/Users/boandersson/Desktop/Games/THE_CITY/CityMaterializationProof/CityMaterializationProof.uproject' \
  -WaitMutex -DisableUnity -NoHotReloadFromIDE
```

The exact artifact directory contains 82 regular non-symlink JSON members and
no others. The verifier strictly reloads their canonical stored bytes,
recomputes the four global matrices, validates every live and deterministic
relation, reconstructs the 364-row occurrence registry, regenerates all 82
artifacts in isolation, reruns the 45 focused and 215 predecessor contracts,
reruns the source audit, and rejects 30 isolated in-memory verifier mutations.

After the self-excluding manifest exists, run the complete release gate from
the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/thecity_pycache \
  PYTHONPATH=proof_kernel \
  python3 proof_kernel/verify_cross_domain_canonical_occupancy_materialization_release.py verify
```

## Candidate boundary

This candidate proves only one subject, two canonical sites, one canonical
route, one transition, two original live domains, and two immediate-successor
refreshes. It does not prove physical traversal, route occupancy or capacity,
movement, interpolation, navigation, pathfinding, arrival detection, multiple
subjects, contention, player embodiment, multiplayer, networking, replication,
rollback, save/load, World Partition, streaming, reconnect, recovery,
production topology, performance, or city scale.

Development Capacity remains v0.1.11. Phase 5 remains closed. No push,
deployment, publication, or successor implementation is authorized by this
candidate record.
