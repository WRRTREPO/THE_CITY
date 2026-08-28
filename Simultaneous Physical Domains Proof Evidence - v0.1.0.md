# Simultaneous Physical Domains Proof Evidence

**Version:** 0.1.0
**Date:** 2026-08-28
**Status:** Implementation evidence passed; evidence unsealed pending independent review
**Specification:** [Simultaneous Physical Domains Proof v0.1.0](Simultaneous%20Physical%20Domains%20Proof%20-%20Draft.md)
**Proof harness identity:** `SimultaneousPhysicalDomainsProof.v1` / `0.7.0-draft.72`
**Evidence continuation:** `0.7.0-draft.75`

## Claim tested

> Can two process-isolated Unreal representation domains remain simultaneously
> alive against one canonical head, survive an independently committed
> canonical H0-to-H1 transition without participating in that transaction, and
> independently rebind to H1 while any domain still representing H0 is
> mechanically classified as stale and incapable of current-head canonical
> authority?

The bounded implementation passes this claim. This document records a release
candidate for separate evidence review. It does not seal the result.

## Exact canonical reuse

The harness imports the sealed Phase-1 validator and resolver. It recomputes the
same record-bound H0 transition and commits byte-identical H1 without accepting
domain state, the physical guard, or the private operational head observer as
canonical inputs.

```yaml
H0_record_hash: 666d75281d3478e586edd12464d2736169f423c2d7b128bd3d2d2b1b2b826b29
R0_raw_sha256: 5e57c04875cfaead69f4cd6aaffeee2f788a2c1f5a820a56fb7083f8f7e861ed
H0_route_access: available
H1_record_hash: 78cc5ffe0c4758c296d8fee0bc2a95e230be0bec0a4aab680806eb670500804a
R1_raw_sha256: 7ac7ece5c142ac4dee83abc6e83f7845d85dfc7f055ca6d678b7f04bdf1d795a
H1_route_access: blocked
canonical_transition_branches_byte_identical: true
```

The guard-open W8 control leaves the guard at `open_for_H0`, invokes that same
resolver, obtains the same R1/H1, and then ends the physical protocol in
`failed_closed` with both H0 domains `protocol_invalid`. Canonical execution
does not read or reject on the guard.

## Live Unreal evidence

The proof used compiled UE 5.8 code and two distinct, suspended direct-child
Unreal processes per physical witness. Each child was bound once to its exact
PID and macOS process-birth tuple before release. The same original binding,
child handle, stdin/stdout pipes, and process instance remained present at all
required checkpoints from L0 through L4B; no replacement process was spawned.

The two principal witnesses reverse only refresh order:

```text
W1: launch A+B at H0 → commit H1 → refresh A → refresh B
W2: launch A+B at H0 → commit H1 → refresh B → refresh A
```

In both orders, an independent probe inside each original Unreal process
inspected the live published representation. The probe has no adapter pointer
and consumes neither the materialization receipt nor the authoritative-derived
JSON under test.

```yaml
domain_A_H0_live_observation: available
domain_B_H0_live_observation: available
domain_A_H1_live_observation: blocked
domain_B_H1_live_observation: blocked
same_original_process_binding_before_after: true
receipt_independent_probe: true
```

The adapter derives site identity, route identity, endpoints, and
`topology_route_0001.access_state` only from the exact payload and exact
detached projection. The receipt asserts disposable representation
correspondence only. It grants no current-head or canonical authority.

## Witnesses and failure atomicity

All 11 frozen live-process witnesses were acquired:

- W1 and W2: both refresh orders with uninterrupted simultaneous liveness;
- W3: stale H0 quarantine with no current-head receipt;
- W4: injected failure after canonical H1 commit verification and before
  operational observation construction, failing both domains closed;
- W5 baseline and perturbation: distinct allowed stale local state produces
  byte-identical H1 authoritative-derived representation facts;
- W6 A-succeeds/B-fails and B-succeeds/A-fails asymmetric refreshes;
- W7 destruction of A and destruction of B without changing H1 or the remaining
  synchronized domain; and
- W8 guard-open canonical control.

The deterministic fault and rejection surfaces pass:

```yaml
head_observation_fault_points: 9/9 fail_closed
refresh_fault_stages: 18/18 fail_closed
physical_observation_fault_stages: 12/12 fail_closed
current_head_authority_cases: 37/37 rejected
canonical_R1_rollback_or_rewrite: none
partial_current_head_authority: none
```

An H0 representation may retain only the three frozen detached local scalar
values and may continue only nonconsequential local physical execution. While
stale, it cannot claim or accept current-head evidence, schedule canonical
work, mutate truth, refresh from an undeclared channel, or publish a successor.

## Proof-semantic closure and source audit

The launch audit records exact argv, hashed environment entries, launch cwd,
fd 0/1/2 bindings, executable/project/module identities, engine identity, and
the three-file launch bundle. Refresh accepts only the original stdin pipe and
one exact three-file H1 bundle. The evidence records:

```yaml
proof_semantic_closure_complete: true
all_launches_exact_surface: true
all_refreshes_original_stdin_pipe_only: true
head_observation_visible_to_unreal: false
physical_guard_visible_to_unreal: false
other_domain_state_visible_to_unreal: false
expected_physical_result_visible_to_probe: false
```

The independently rerun source/dataflow audit passes. It confirms that the
sealed Phase-1 resolver remains the sole canonical mutation owner, that no
head-observation or guard input reaches Unreal, that the live probe is separated
from the adapter/receipt path, and that no Phase-3 source implements occupancy,
movement, navigation, networking, streaming, or successor publication.

## Determinism, replay, build, and release

```yaml
phase_3_focused_tests: 33/33
predecessor_regressions: 215/215
specification_validator: 10/10
specification_validator_adversaries: 29/29
ue_version: 5.8.0-55116800-++UE5+Release-5.8
ue_editor_build: succeeded_with_DisableUnity
live_witnesses: 11/11
artifact_roles: 44/44
release_manifest_members_excluding_manifest: 110/110
manifest_self_excluding: true
canonical_replay: byte_identical
W1_W2_semantic_replay: equal
evidence_status: unsealed
capacity_advancement: none
```

The UE build command was:

```sh
'/Users/Shared/Epic Games/UE_5.8/Engine/Build/BatchFiles/Mac/Build.sh' \
  CityMaterializationProofEditor Mac Development \
  '/Users/boandersson/Desktop/Games/THE_CITY/CityMaterializationProof/CityMaterializationProof.uproject' \
  -WaitMutex -DisableUnity
```

The exact release directory contains 44 regular, non-symlink members and no
others. The self-excluding manifest contains the frozen 66 non-artifact members
plus those 44 artifacts, sorted by raw UTF-8 relative-path bytes. The release
verifier rehashes every member, reconstructs deterministic artifacts, validates
operational witness relations, reruns all 33 focused tests, and reperforms the
source/dataflow audit.

Run it from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/thecity_pycache \
  python3 proof_kernel/verify_simultaneous_physical_domains_release.py verify
```

## Proven candidate boundary

The evidence candidate establishes only two process-isolated Unreal
representations of one exact sealed Phase-1 topology transition, with one
domain projection per canonical site and the shared route included in both.
It establishes that disposable live representation can survive a canonical
head change without retaining lawful H0-bound current-head authority.

It does not establish canonical occupancy materialization, Q/BQ/BEXT, live
external input, physical movement, navigation, networking, rollback, host
migration, World Partition, streaming, split players, arbitrary domain counts,
1-to-4-player topology, cross-domain causal propagation, production
architecture, Phase 4, or any capacity increase. No successor scope follows
until this evidence is independently reviewed and sealed.
