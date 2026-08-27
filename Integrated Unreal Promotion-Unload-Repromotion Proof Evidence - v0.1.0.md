# Integrated Unreal Promotion-Unload-Repromotion Proof Evidence

**Version:** 0.1.0
**Status:** Passed and sealed.
**Specification:** [Integrated Unreal Promotion-Unload-Repromotion Proof — v0.1.0](Integrated%20Unreal%20Promotion-Unload-Repromotion%20Proof%20-%20Draft.md)
**Simulation identity:** `0.7.0-draft.51`
**Scope:** One neutral canonical fixture, two fresh Unreal source/return
lifecycle witnesses, and no travel, World Partition, streaming, same-clock
work, map scale, or production behavior.

## Verdict

> **A canonical record can be materialized into a fresh Unreal world, receive
> one real physical consequence as non-authoritative evidence, lose that world
> entirely, continue canonically at boundary-jump resolution, and later
> reconstruct the evolved truth in a second isolated Unreal world.**

The proof does not retain first-process memory, actors, source inputs, Q, or a
branch selector for the returning world.

```text
R0
→ fresh UE source / enabled gate / alpha active
→ physical E interaction emits exact Q
→ canonical BQ admission
→ Rinput
→ source UE terminated and source domains removed
→ rediscover alpha from Rinput
→ Rfinal / disabled gate / alpha failed_gate
→ fresh isolated UE return
```

The Q-absent control uses the same source-destroy-return lifecycle. It starts
from the same R0, proves its source Q directory empty before continuation, and
returns `enabled / succeeded` from Rcontrol.

## Physical Unreal witnesses

All four acceptance receipts were emitted by UE on distinct process-specific
output channels, captured by the harness, and validated against the exact
canonical record and detached raw-byte launch receipt each process received.

| Witness | UE input | Observed materialization | Proposal capability |
| --- | --- | --- | --- |
| Primary source | R0 | `gate = enabled`, `alpha = active` | enabled |
| Primary return | Rfinal only | `gate = disabled`, `alpha = failed_gate` | disabled |
| Control source | R0 | `gate = enabled`, `alpha = active` | enabled |
| Control return | Rcontrol only | `gate = enabled`, `alpha = succeeded` | disabled |

The primary source gate was physically activated through the Unreal first-person
interaction. UE wrote exactly one Q; the harness byte-compared it to the frozen
external-evidence envelope before constructing BQ. The primary return and the
control return were each visually confirmed in fresh Unreal processes.

The primary source process was terminated after Rinput committed and before
`next_execution_boundary(Rinput)`. Alpha was then rediscovered from Rinput and
read the ordinary gate fact `disabled`, producing `failed_gate` at `t1/00`.

The final Q-absent control was terminated immediately after its source receipt.
Its audited source-output directory was empty before canonical continuation.
Alpha then read `enabled` and succeeded normally. Earlier exploratory control
runs that emitted Q were rejected by the harness and are not release evidence.

## Canonical and isolation results

```text
H0       075540149809018481221e1f524c48ce6c6b6a5ce38caede59949b799251d909
Hinput   0ec4683e11ab178c0914899de63cb0ac281dd425c24317c0a5e065692d385128
Hfinal   0a5bb79da303d2cb7d6d71bbd3bc2d305866420eeeb9c2e342d73766d313fb26
Hcontrol 130df39433d81aac4e8a46c1f8280f230ae76b28f7f1c9a124a67194c0f50e4c
```

The primary lifecycle establishes:

```text
R0
→ Q / BQ @ t0/30
→ Rinput
→ source process termination
→ record-relative alpha boundary @ t1/00
→ Rfinal
```

The alpha ledger in Rfinal records the actual ordinary read:

```yaml
path: current_causal_state.gate_token.state
observed_value: disabled
required_value: enabled
result: false
```

The primary and control return-input audits each enumerate exactly their two
allowed files and raw-byte hashes. They receive no source path, Q path,
cache, save, session, or truth-bearing execution context. The harness removes
source input/output domains before canonical continuation and requires a
dedicated empty-source-output audit for the no-Q control.

## Regression and source audit

* Full Python regression: **161/161** checks passed.
* Focused integrated lifecycle suite: **18/18** checks passed.
* UE 5.8 `CityMaterializationProofEditor` build: **passed**.
* Canonical dense, boundary-jump, and mixed-policy references remain
  byte-identical at R0/Rinput/Rfinal.
* Source audit confirms UE validates raw payload bytes before parsing, emits
  detached receipts and Q only, and has no canonical resolver, ledger writer,
  scheduler, or policy-selection path.

The release verifier regenerates canonical fixture artifacts and rejects a
missing, malformed, duplicate, contradictory, or record-incompatible UE
receipt; an altered Q; a mismatched checkpoint; a non-empty control Q output;
or an isolation/termination audit mismatch.

## Release package

The self-excluding manifest binds the frozen specification, evidence,
continuation, capacity record, exact canonical fixture, UE source, lifecycle
harness, tests, verifier, four structured UE process-output logs, four parsed
acceptance receipts, Q, checkpoints, termination witnesses, and input-isolation
audits, plus the current repository-agent handoff. It verifies **63/63**
release artifacts and excludes its own digest.

```sh
cd "/Users/boandersson/Desktop/Games/THE_CITY"
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/private/tmp/thecity_pycache \
  python3 proof_kernel/verify_integrated_unreal_promotion_unload_repromotion_release.py verify
```

## Boundary

This proves one fresh promotion → physical evidence → unload → canonical
continuation → fresh repromotion cycle. It does not prove World Partition,
continuous travel, proximity promotion, asynchronous streaming, repeated
cycles, multiple promoted areas, same-clock input arbitration, live transport,
randomness, network authority, rollback, save/load, population, city scale, or
production performance.
