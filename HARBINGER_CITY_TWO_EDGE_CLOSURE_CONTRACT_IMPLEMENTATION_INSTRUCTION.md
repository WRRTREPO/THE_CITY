# CITY × Harbinger — Two-Edge Closure Contract

## Objective

Close the two remaining Harbinger policy edges with executable CITY law.

```text
1. AcquisitionWorkspace.build_candidate → subprocess.run
2. ClosureExecutionContext.acquire → os.environ
```

Both are real boundaries. Neither is a category-level provenance read. Do not
map either edge until this contract, its independent verifier, and its negative
controls pass.

This work changes no Phase 5 authority.

```yaml
may_open_acquisition: false
may_open_release: false
may_seal_phase_5: false
```

Keep these denials:

```text
lcer.acquisition_implementation_incomplete
lcer.release_semantics_not_implemented
```

Do not launch Unreal or run an actual build as part of this slice.

## Fixed Baseline

Start from a clean CITY worktree at or after commit `32c30a6`. Read and verify:

```text
proof_kernel/city_live_evidence_source_audit_contract.json
proof_kernel/city_harbinger_policy_contract.json
proof_kernel/live_cross_domain_evidence_round_trip_harness.py
proof_kernel/test_live_cross_domain_evidence_round_trip.py
proof_kernel/verify_live_cross_domain_evidence_round_trip_release.py
```

The 13-file frozen source manifest remains the source boundary. If this work
changes either scoped Python source file, update its declared hash only as part
of the same reviewed contract transaction. Do not accept stale source hashes.

Harbinger remains raw evidence. Its bridge and policy adapter must keep the
record verdict `raw_evidence_valid_incomplete` until their own closure rules
are satisfied.

## Deliverables

Add a CITY-owned closure contract, a constructor, an independent verifier, and
focused tests. Names may vary only if their purpose stays separate from
Harbinger's generic core.

```text
proof_kernel/city_live_evidence_two_edge_closure_contract.json
proof_kernel/city_live_evidence_two_edge_closure.py
proof_kernel/verify_city_live_evidence_two_edge_closure.py
proof_kernel/test_city_live_evidence_two_edge_closure.py
```

The contract must bind:

```text
schema
CITY source-audit-contract SHA-256
all 13 source-file hashes
exact edge identity: family, path, line, callable, token
sealed build invocation relation
sealed closure-command environment relation
negative-control set
authority: all false
record SHA-256
```

The independent verifier must not import the constructor or reuse its decision
function.

## Edge 1 — Live Build Launch

The target is this exact call site:

```text
family: function_to_consequence
path: proof_kernel/live_cross_domain_evidence_round_trip_harness.py
line: 210
callable: proof_kernel.live_cross_domain_evidence_round_trip_harness.py.AcquisitionWorkspace.build_candidate
token: subprocess.run
```

The closure is a controlled build invocation. It is not proof that a build
passed or that Unreal may run.

Before `subprocess.run`, the implementation must derive and bind all of these:

```text
the sealed constitutional build argv
the exact CITY working directory
an explicit total process environment
the current Python runtime identity
the 13-file CITY source snapshot
the core dependency identities from core_health
a fresh exclusive output root and build-log path
the full-source-audit record and its fourteen adversary outcomes
```

Rules:

1. The command must use an argv list. No shell. No inherited PATH lookup.
2. The command must receive `env=`. It may not inherit the parent environment.
3. Every environment key must come from the closure contract. A needed but
   undeclared key rejects with `lcer.build_environment_unsealed` before spawn.
4. The environment record may store declared names and a canonical digest. It
   must not write secret values into evidence.
5. The log path must be new, inside the owned output root, opened exclusively,
   and fsynced after the command returns.
6. The attempted-build latch remains before the external call. An interruption
   consumes the workspace.
7. The full source-effect auditor and all fourteen frozen adversaries must
   pass before this boundary can execute outside an intercepted test.
8. A passing intercepted test proves only the boundary relation. It does not
   open acquisition.

The resulting capture must bind argv, cwd, environment digest, source snapshot,
runtime identity, dependency identities, audit identity, timestamps, exit code,
and log identity. Any later inventory must recompute and compare those fields.

## Edge 2 — Closure-Command Environment

The target is this exact call site:

```text
family: external_input_to_callable
path: proof_kernel/test_live_cross_domain_evidence_round_trip.py
line: 14508
callable: proof_kernel.test_live_cross_domain_evidence_round_trip.py.ClosureExecutionContext.acquire
token: os.environ
```

`ClosureExecutionContext.acquire` is development-evidence code. It must not
copy the agent's environment into a closure case.

Replace `dict(os.environ)` with a total environment derived from the closure
contract. The derived mapping must contain only the keys needed by the frozen
acquisition command. It must set deterministic paths under that case's owned
directory. It must reject an unknown required variable before it creates a
runtime or output directory.

The command-start record binds the environment digest, its approved key set,
argv, cwd, and the closure context digest. It does not expose values that the
record does not need to prove.

The command capture must receive exactly that mapping. A changed parent
environment must produce the same derived mapping and the same digest.

## CITY Source-Audit and Harbinger Rules

After the two closures exist:

1. Add exact CITY source-audit call-site entries for both edge shapes. The
   entries must carry path, function, callee, line, and consequence.
2. Add explicit closure kinds. Use `build_execution` for the controlled build
   boundary and `test_control` for the sealed closure-command environment.
   Do not call the build edge `provenance`.
3. Extend the source-audit validator so it accepts those kinds only at the
   declared exact sites.
4. Add matching Harbinger policy entries with all five edge coordinates and a
   reference object that equals the CITY source-audit call-site entry.
5. Keep any edge without that exact object as `unclassified` with
   `lcer.harbinger_edge_unmapped`.
6. Keep `self._emit`, dynamic resolve, canonical admission, and release
   semantics under their present laws. This contract grants none of them.

## Mandatory Tests

Every case must run from argv and write a machine-readable result outside CITY.

```text
sealed build relation with intercepted subprocess       -> contract passes
build argv changed                                      -> reject before spawn
build cwd changed                                       -> reject before spawn
undeclared build environment key                        -> reject before spawn
parent environment changed                              -> derived build environment unchanged
output root reused or build log pre-exists              -> reject before spawn
source snapshot or core dependency changed              -> reject before spawn
incomplete source audit                                 -> existing acquisition denial; no spawn
one frozen adversary failure                            -> reject before spawn
interrupted subprocess                                  -> workspace consumed; no retry
closure parent environment changed                      -> derived closure environment unchanged
closure environment digest or approved key set changed  -> reject
closure command receives any undeclared key             -> reject
either Harbinger edge moved by path, line, callable,
family, or token                                        -> reject
either CITY call-site reference changed                 -> reject
either edge absent from policy                          -> unclassified, never dropped
any authority flag true                                 -> reject
```

Keep the existing negative test that the normal acquisition path rejects before
any compiler call. Add no test that turns a mocked compiler into acquisition
acceptance.

## Required Evidence

Use a fresh external output root for every full run.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  proof_kernel.test_city_live_evidence_two_edge_closure
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  proof_kernel.test_city_harbinger_policy_adapter
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  proof_kernel.test_city_live_evidence_source_audit
python3 -B proof_kernel/run_harbinger_city_source_effect_audit.py \
  --root "$PWD" --harbinger-root ../Harbinger \
  --output /private/tmp/city-harbinger-two-edge-closure --json
git diff --check
```

After commit, repeat the complete suite at that exact HEAD. Refresh and
validate CITY through ControlTower against the committed SHA.

## Stop Condition

Stop when the closure contract, constructor, independent verifier, and negative
controls pass at an exact committed HEAD.

That result may map the two exact edges as controlled development evidence. It
does not make Harbinger's generic graph complete. It does not remove the
acquisition or release denials. It does not authorize Phase 5 execution or a
Phase 5 seal.
