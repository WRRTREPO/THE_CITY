# Live Evidence Pipeline: Implementation Record

Commit: `44090c6d2f4332d5b6a303fcc3c7dce0ebde4127`  
Status: implementation landed. Live proof remains closed.

## What this proves

This commit proves that CITY now has a real, testable implementation surface for the frozen Live Cross-Domain Evidence Round-Trip specification.

It proves these development facts:

- The frozen contract can authenticate the planned Python and Unreal source set before work begins.
- The parent-owned harness can reserve isolated case roots, derive frozen build and launch arguments, bind artifacts, and reject bad sequence or identity state.
- The Unreal plugin has concrete GameMode and Actor code for bounded evidence proposal, staged fault handling, and local representation. It does not own canonical city truth.
- The independent verifier can parse and cross-check declared build, process, native-image, artifact, and release relations without importing unauthenticated candidate code.
- The complete Python suite previously passed against the exact source snapshot. A fresh ControlTower reader run passed all 22 current-source component readers. The reader receipt is at `../Synthesis/CITYPhoenixContinuation/pr2/candidate-v140/reader-batch-execution.json`.

This is development evidence. It is not a new CITY seal, a live-Unreal proof, production readiness, or trusted CI.

## What it spans

| Surface | Delivered work |
| --- | --- |
| Frozen inputs | Exact source identity checks, fixed policy parsing, restricted local imports, and source inventory preflight. |
| Parent harness | Workspace reservation, case lifecycle, build and launch argument derivation, artifact writing, and fail-closed sequencing. |
| Unreal module | `CityLiveEvidenceProof` plugin with GameMode and Actor implementations for bounded local evidence behavior. |
| Independent verification | Strict parsing and cross-checking of source, process, native Mach-O, build, artifact, binding, world, and release records. |
| Tests | Adversarial source, schema, identity, ownership, process, native-image, and release-record coverage. |
| ControlTower evidence | Fresh Control Plane Gate receipts and a clean 22-reader current-source run. |

## What it benefits

The pipeline gives CITY one place to build hard proof work without handing truth to Unreal.

- Canonical records stay in the Python authority layer.
- Unreal can represent and propose physical evidence. It cannot settle city facts.
- Build, launch, process, and artifact claims have identity checks around them.
- Bad input, wrong order, changed bytes, extra holders, and malformed records fail before they become a success claim.
- Future live acquisition has a bounded implementation path instead of a blank spot in the architecture.

## What still fails by design

The public acquisition and release paths remain closed. Those denials are correct.

| Boundary | Current result | Why it stays closed |
| --- | --- | --- |
| Full source-effect audit | Open | The current graph has `145103` unclassified entries. Component readers verify slices only. They do not prove every external input reaches an allowed consequence. |
| Acquisition | `lcer.acquisition_implementation_incomplete` | The harness refuses to build or launch until an independently executed full audit produces the required positive record and fourteen named adversary rejections. |
| Release | `lcer.release_semantics_not_implemented` | The independent verifier checks substantial relations, then refuses to call them a release until complete source audit and live execution evidence exist. |
| Live Unreal | Unacquired | No fresh two-domain Unreal execution, observed world census, or complete artifact package has been accepted. |
| Trusted CI | Unproved | Current evidence is local development evidence. No host-owned trusted execution boundary has certified it. |
| Stored release replay | Timed out | `./start.sh verify-release --json` reached its fixed 300-second limit and returned `CITY_VERIFIER_TIMEOUT`; it did not produce a semantic verifier failure. |

Do not remove these denials to make a green report. Replace them only with the missing executable proof.

## Infrastructure findings from the eight-day run

### ControlTower

The Control Plane Gate did its job. It kept CITY mounted, profile-aligned, protocol-aligned, and bound to the truth contract.

It did not prove the candidate itself. A permitted gate only proves the lane was legal to run. The candidate still needs its own fresh source snapshot, execution receipt, validator result, and post-commit replay.

The release wrapper has a 300-second ceiling. The sealed replay needs longer. The timeout is a useful failure signal, but it prevents a current full replay receipt.

### Agents

The work exposed a continuity problem. A later agent can inherit scripts and evidence but still miss the task-local prerequisites that make those scripts runnable.

Each bounded task needs a self-contained manifest. It must name immutable inputs, expected hashes, source snapshot, runner, receipt directory, and dependency order. A human summary is not enough.

### Runtime and scripts

The reader graph was sound. The task packaging was weak.

Several attempts failed before source evaluation because they lacked a source snapshot, native scalar records, a projection manifest, or a clean receipt directory. The final clean task fixed that shape and passed all 22 readers.

The required rule is simple: preflight the task surface before spawning any child. Reject stale or inherited `runs/` directories. Reject missing static prerequisites. Verify that every script resolves paths inside its own task root.

## Evidence and repeatable checks

```sh
cd /Users/boandersson/Projects/CITY
./start.sh --status --json
./start.sh --validate --json
```

Expected now:

- native status: `pass`
- native validation: `pass`
- source and live claims: false or unproved

The current-source reader proof is external to the CITY release surface:

```sh
python3 -B -c 'import json; p="/Users/boandersson/Projects/Synthesis/CITYPhoenixContinuation/pr2/candidate-v140/reader-batch-execution.json"; d=json.load(open(p)); assert len(d["completed"]) == 22 and not d["pending"] and not d["active"]; assert all(v["returncode"] == 0 for v in d["completed"].values()); print("22/22 readers passed")'
```

## Next implementation gate

Build the full source-effect auditor before touching the two explicit denials.

It must:

1. Enumerate every function and method in the four new Python files and seven plugin files, plus every allowed transitive local import.
2. Record every external-input-to-function and function-to-consequence edge.
3. Reject dynamic imports, `eval`, `exec`, unclassified C++ reflection, unclassified delegates, wrong canonical ownership, child reads of expected data, and forbidden Actor or fault mutation routes.
4. Reject all fourteen frozen source adversaries with the exact failure code and source edge.
5. Write a source-audit record that the harness and independent verifier can authenticate from disk.
6. Run the entire sealed case set on the exact committed HEAD. Then run the required independent post-commit validation.

The general ControlTower lesson is specified in [the evidence-task isolation proposal](../HoldingPAD/CITY_EIGHT_DAY_EVIDENCE_TASK_ISOLATION_SPEC.md).
